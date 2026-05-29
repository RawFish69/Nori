"""Weekly item lootpool refresh loop.

Refresh orchestration (Task 5 of the v3.7.2 migration plan):

1. If ``config.LOOTPOOL_USE_OFFICIAL_PRIMARY`` is on, call the official
   ``/v3/map/loot-pools`` endpoint through :mod:`lib.wynn_map_api`. On
   success the official payload is translated into the on-disk
   ``weekly_lootpool.json`` shape via :mod:`lib.lootpool_translate`.
2. If ``config.LOOTPOOL_ENRICH_WITH_WYNNSOURCE`` is also on, fetch the
   WynnSource pool in the same cycle and merge its ``Shiny.Tracker``
   (and any page-split metadata) onto the official-sourced regions via
   :func:`_merge_enrichment`. Both succeed -> ``source=hybrid``; official
   succeeds but enrichment fails -> ``source=official_only``.
3. If the official call fails (timeout, 5xx, 429-after-retry, malformed
   payload), fall back to the legacy WynnSource-only flow already
   implemented in :mod:`lib.commands.admin`. Tagged ``source=wynnsource_fallback``.
4. If both paths fail in the same cycle, return an error dict tagged
   ``source=both`` and skip the on-disk write.

See ``AGENT/plans/V3_7_2_LOOTPOOL_MIGRATION.md`` sections 3 (architecture)
and 8 (logging contract) for the full contract.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any

import lib.config as config
from lib.lootpool_translate import translate_item_lootpool
from lib.wynn_map_api import fetch_loot_pools
from lib.wynnsource_pool import fetch_pool_legacy_with_failover


def _next_lootpool_rotation_ts(now_ts: int | None = None) -> int:
    now_ts = now_ts if isinstance(now_ts, int) else int(time.time())
    elapsed = now_ts - (config.FIRST_WEEK_TIMESTAMP + config.DST_OFFSET)
    weeks_elapsed = max(0, elapsed // config.SECONDS_PER_WEEK)
    return config.FIRST_WEEK_TIMESTAMP + config.DST_OFFSET + (weeks_elapsed + 1) * config.SECONDS_PER_WEEK


def _all_regions_lootpool_filled(weekly_lootpool: dict) -> bool:
    loot = weekly_lootpool.get("Loot", {})
    for region in config.LOOTPOOL_REGIONS:
        region_data = loot.get(region, {})
        shiny = region_data.get("Shiny", {})
        if not isinstance(shiny, dict) or shiny.get("Item", "N/A") == "N/A":
            return False
        if not region_data.get("Mythic", []):
            return False
    return True


def _compute_lootpool_refresh_interval(all_filled: bool, now_ts: int | None = None) -> int:
    now_ts = now_ts if isinstance(now_ts, int) else int(time.time())
    next_rotation = _next_lootpool_rotation_ts(now_ts)
    previous_rotation = next_rotation - config.SECONDS_PER_WEEK
    elapsed = now_ts - previous_rotation

    if not all_filled:
        if elapsed <= config.LOOTPOOL_REFRESH_HYPER_BURST_1_DURATION:
            return config.LOOTPOOL_REFRESH_HYPER_BURST_1_INTERVAL
        if elapsed <= config.LOOTPOOL_REFRESH_HYPER_BURST_DURATION:
            return config.LOOTPOOL_REFRESH_HYPER_BURST_2_INTERVAL
        return config.LOOTPOOL_REFRESH_BURST_INTERVAL

    if elapsed <= config.LOOTPOOL_REFRESH_BURST_DURATION:
        return config.LOOTPOOL_REFRESH_FILLED_BURST_INTERVAL
    return config.LOOTPOOL_REFRESH_BASE_INTERVAL


# ---------------------------------------------------------------------------
# Helpers for the new orchestration
# ---------------------------------------------------------------------------


def _wynnsource_legacy_to_region_blocks(payload: dict) -> dict[str, dict[str, Any]]:
    """Collapse a WynnSource legacy ``data.loot[region][page]`` payload into
    nori's per-region ``{Shiny, Mythic, Fabled, ...}`` shape.

    This is the same logic ``lib.commands.admin._convert_lootpool_format``
    applies, kept here in a hikari-free utility so the orchestration layer
    can read WynnSource output directly for enrichment without pulling the
    full discord command runtime into the import graph.
    """
    from lib.config import LOOT_TIERS
    from lib.wynnsource_pool import RARITY_LABELS_BY_TOKEN, clean_item_name, is_ward_item

    loot = (payload or {}).get("data", {}).get("loot", {})
    if not isinstance(loot, dict):
        return {}

    def _normalize_tier(raw_tier) -> str:
        if not isinstance(raw_tier, str):
            return "Misc"
        for tier in LOOT_TIERS:
            if raw_tier.casefold() == tier.casefold():
                return tier
        normalized = raw_tier.upper()
        if normalized.startswith("RARITY_"):
            normalized = normalized[len("RARITY_"):]
        mapped = RARITY_LABELS_BY_TOKEN.get(normalized)
        return mapped if isinstance(mapped, str) and mapped in LOOT_TIERS else "Misc"

    out_by_region: dict[str, dict[str, Any]] = {}
    for region, region_data in loot.items():
        if not isinstance(region_data, dict):
            continue
        block: dict[str, Any] = {
            "Shiny": {"Item": "N/A", "Tracker": None},
            **{tier: [] for tier in LOOT_TIERS},
        }
        shiny_found = False
        # Iterate pages in numeric order so the earliest shiny wins.
        page_keys = sorted(
            region_data.keys(),
            key=lambda k: int(k) if str(k).isdigit() else 0,
        )
        for page_key in page_keys:
            page = region_data.get(page_key, {})
            if not isinstance(page, dict):
                continue
            shiny = page.get("shiny")
            if not shiny_found and isinstance(shiny, dict):
                block["Shiny"] = {
                    "Item": clean_item_name(shiny.get("item", "")) or "N/A",
                    "Tracker": shiny.get("tracker"),
                }
                shiny_found = True
            items = page.get("items", {})
            if not isinstance(items, dict):
                continue
            for raw_rarity, raw_entries in items.items():
                if not isinstance(raw_entries, list):
                    continue
                tier = _normalize_tier(raw_rarity)
                for raw_name in raw_entries:
                    if not isinstance(raw_name, str):
                        continue
                    name = clean_item_name(raw_name)
                    if not name:
                        continue
                    if is_ward_item(name) and tier != "Mythic":
                        block["Mythic"].append(name)
                    else:
                        block.setdefault(tier, []).append(name)
        out_by_region[region] = block
    return out_by_region


def _merge_enrichment(
    official_dict: dict[str, Any],
    wynnsource_dict: dict[str, Any],
) -> dict[str, Any]:
    """Merge WynnSource enrichment (tracker + optional page split) into the
    official-sourced ``weekly_lootpool`` dict.

    Mutates and returns ``official_dict`` for convenience. Rules:

    - For each region that exists in both dicts, if WynnSource has a
      non-empty ``Shiny.Tracker`` whose ``Shiny.Item`` matches the
      official entry's ``Shiny.Item`` (case-sensitive), copy ``Tracker``
      into the official region block.
    - If WynnSource has a ``Pages`` (or ``pages``) key the official block
      lacks, attach it as ``Pages``. The on-disk single-page format is
      preserved; downstream embed renderers ignore the optional key.
    """
    if not isinstance(official_dict, dict) or not isinstance(wynnsource_dict, dict):
        return official_dict

    official_loot = official_dict.get("Loot")
    wynn_loot = wynnsource_dict.get("Loot")
    if not isinstance(official_loot, dict) or not isinstance(wynn_loot, dict):
        return official_dict

    for region, official_block in official_loot.items():
        if not isinstance(official_block, dict):
            continue
        wynn_block = wynn_loot.get(region)
        if not isinstance(wynn_block, dict):
            continue

        # ----- Tracker -----
        wynn_shiny = wynn_block.get("Shiny") if isinstance(wynn_block.get("Shiny"), dict) else {}
        wynn_tracker = wynn_shiny.get("Tracker")
        official_shiny = official_block.setdefault("Shiny", {"Item": "N/A", "Tracker": None})
        if wynn_tracker and wynn_tracker not in (None, "N/A"):
            wynn_item = wynn_shiny.get("Item")
            official_item = official_shiny.get("Item")
            # Names should agree; if WynnSource saw a different shiny we
            # still trust the official item and skip the tracker overlay.
            if not official_item or official_item == "N/A" or official_item == wynn_item:
                official_shiny["Tracker"] = wynn_tracker

        # ----- Page split (optional, preserve single-page on disk) -----
        for key in ("Pages", "pages"):
            if key in wynn_block and key not in official_block:
                official_block[key] = wynn_block[key]
                break

    return official_dict


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


async def _fetch_official_pool() -> dict:
    """Call the official /map/loot-pools endpoint off the event loop."""
    return await asyncio.to_thread(fetch_loot_pools)


async def _fetch_wynnsource_pool():
    """Call WynnSource's legacy failover chain off the event loop.

    Returns the raw :class:`PoolFetchResult`. Caller decides how to react to
    ``payload is None``.
    """

    def _do_fetch():
        return fetch_pool_legacy_with_failover(
            "item",
            config.WYNN_SOURCE_TOKEN,
            primary_base_url=config.WCS_POOL_PRIMARY_BASE_URL,
            beta_base_url=config.WCS_POOL_BETA_BASE_URL,
            v1_base_url=config.WCS_POOL_V1_BASE_URL,
            timeout=config.WCS_POOL_TIMEOUT,
            allow_missing_regions=config.WCS_POOL_ALLOW_MISSING_REGIONS,
            enable_v1_fallback=config.WCS_POOL_ENABLE_V1_FALLBACK,
        )

    return await asyncio.to_thread(_do_fetch)


async def _wynnsource_only_refresh() -> dict:
    """Legacy WynnSource-only refresh path.

    Calls ``fetch_pool_legacy_with_failover`` directly (the v2/beta/v1
    cascade) and assembles the on-disk ``weekly_lootpool`` dict using the
    same conversion logic the admin helpers use (kept hikari-free here so
    the orchestration layer is importable without hikari).

    If hikari is available, the admin helpers are reused for the icon
    post-process step; otherwise that step is skipped (icons stay at the
    last-known value). On-disk write goes through ``_post_official_write``
    which gracefully falls back to a direct JSON write.

    Returns either ``{ok, regions, all_filled, weekly_lootpool}`` on
    success or ``{"error": ..., "detail": ...}`` on failure.
    """
    try:
        wynn_result = await _fetch_wynnsource_pool()
    except Exception as exc:  # noqa: BLE001
        return {
            "error": "wynnsource_exception",
            "detail": f"{type(exc).__name__}: {exc}",
        }

    payload = getattr(wynn_result, "payload", None)
    if not isinstance(payload, dict):
        attempts = getattr(wynn_result, "attempts", None)
        return {
            "error": "wynnsource_unusable",
            "detail": f"all WynnSource attempts failed (attempts={attempts})",
        }

    region_blocks = _wynnsource_legacy_to_region_blocks(payload)
    if not region_blocks:
        return {
            "error": "wynnsource_payload_empty",
            "detail": "WynnSource returned no parseable regions",
        }

    # Ensure every nori region is present so downstream consumers don't
    # KeyError on missing entries. Mirrors `_create_weekly_lootpool` shape.
    normalized_loot: dict[str, Any] = {}
    for region in config.LOOTPOOL_REGIONS:
        block = region_blocks.get(region)
        if not isinstance(block, dict):
            from lib.lootpool_translate import _empty_region_block

            block = _empty_region_block()
        normalized_loot[region] = block
    # Carry through any extra regions WynnSource may have included so we
    # don't silently drop data.
    for region, block in region_blocks.items():
        if region not in normalized_loot:
            normalized_loot[region] = block

    weekly_lootpool: dict[str, Any] = {
        "Loot": normalized_loot,
        "Icon": config.lootpool_icon,
        "Timestamp": _next_lootpool_rotation_ts() - config.SECONDS_PER_WEEK,
    }

    # Persist + (optional) icon post-process.
    try:
        await _post_official_write(weekly_lootpool)
    except Exception as exc:  # noqa: BLE001
        print(
            f"[Lootpool refresh] on-disk write failed (fallback path): "
            f"{type(exc).__name__}: {exc}"
        )

    all_filled = _all_regions_lootpool_filled(weekly_lootpool)
    return {
        "ok": True,
        "regions": len(normalized_loot),
        "all_filled": all_filled,
        "weekly_lootpool": weekly_lootpool,
    }


def _failure_detail(result: Any) -> str:
    """Render an official-API failure dict as a compact one-line string."""
    if not isinstance(result, dict):
        return repr(result)
    error = result.get("error", "unknown")
    detail = result.get("detail")
    if detail:
        return f"{error} ({detail})"
    return str(error)


async def refresh_item_lootpool() -> dict:
    """Refresh the item lootpool using the official-primary orchestration.

    Returns a dict shaped as one of:

    - Success: ``{ok, source, regions, all_filled, weekly_lootpool}`` where
      ``source`` is ``official_only`` | ``hybrid`` | ``wynnsource_fallback``.
    - Failure: ``{error, source: "both", primary_error, fallback_error}``.

    See module docstring for the orchestration rules.
    """
    if not config.LOOTPOOL_USE_OFFICIAL_PRIMARY:
        # Kill-switch path: legacy behavior, tagged as fallback for log clarity.
        return await _legacy_refresh_with_tag(primary_error="primary_disabled")

    primary = await _fetch_official_pool()
    if not isinstance(primary, dict) or not primary.get("ok"):
        primary_error = _failure_detail(primary)
        return await _legacy_refresh_with_tag(primary_error=primary_error)

    # Official succeeded -> translate to on-disk shape.
    weekly_lootpool: dict[str, Any] = translate_item_lootpool(primary.get("data") or [])
    # Carry the icon cache forward; downstream renderers expect the key.
    weekly_lootpool.setdefault("Icon", config.lootpool_icon)

    source = "official_only"
    enrichment_error: str | None = None
    if config.LOOTPOOL_ENRICH_WITH_WYNNSOURCE:
        try:
            wynn_result = await _fetch_wynnsource_pool()
        except Exception as exc:  # noqa: BLE001 — enrichment is best-effort
            enrichment_error = f"{type(exc).__name__}: {exc}"
            print(
                f"[Lootpool refresh] enrichment failed (non-fatal): {enrichment_error}"
            )
        else:
            payload = getattr(wynn_result, "payload", None)
            if isinstance(payload, dict):
                wynn_blocks = _wynnsource_legacy_to_region_blocks(payload)
                if wynn_blocks:
                    _merge_enrichment(
                        weekly_lootpool,
                        {"Loot": wynn_blocks},
                    )
                    source = "hybrid"
                else:
                    enrichment_error = "wynnsource_payload_empty"
            else:
                attempts = getattr(wynn_result, "attempts", None)
                enrichment_error = f"wynnsource_unusable attempts={attempts}"

    # Update in-process state and write to disk via the existing admin helper.
    try:
        # Best-effort icon refresh + on-disk write via admin helpers.
        await _post_official_write(weekly_lootpool)
    except Exception as exc:  # noqa: BLE001 — disk write should not crash the loop
        print(
            f"[Lootpool refresh] on-disk write failed: {type(exc).__name__}: {exc}"
        )

    regions = len(weekly_lootpool.get("Loot", {}) or {})
    all_filled = _all_regions_lootpool_filled(weekly_lootpool)
    extras = f"enrichment_error={enrichment_error}" if enrichment_error else ""
    suffix = f" {extras}" if extras else ""
    print(
        f"[Lootpool refresh] ok source={source} regions={regions} filled={all_filled}{suffix}"
    )
    return {
        "ok": True,
        "source": source,
        "regions": regions,
        "all_filled": all_filled,
        "weekly_lootpool": weekly_lootpool,
    }


async def _legacy_refresh_with_tag(*, primary_error: str) -> dict:
    """Run the WynnSource-only path and tag the outcome.

    Used both when the official kill-switch is off and when the official
    primary call fails for the current cycle.
    """
    try:
        result = await _wynnsource_only_refresh()
    except Exception as exc:  # noqa: BLE001
        fallback_error = f"{type(exc).__name__}: {exc}"
        print(
            f"[Lootpool refresh] failed source=both primary_error={primary_error} "
            f"fallback_error={fallback_error}"
        )
        return {
            "error": "both_sources_failed",
            "source": "both",
            "primary_error": primary_error,
            "fallback_error": fallback_error,
        }

    if "error" in result:
        fallback_error = result.get("error")
        detail = result.get("detail")
        if detail:
            fallback_error = f"{fallback_error} ({detail})"
        print(
            f"[Lootpool refresh] failed source=both primary_error={primary_error} "
            f"fallback_error={fallback_error}"
        )
        return {
            "error": "both_sources_failed",
            "source": "both",
            "primary_error": primary_error,
            "fallback_error": fallback_error,
        }

    weekly = result.get("weekly_lootpool", {})
    regions = len(weekly.get("Loot", {}) or {}) if isinstance(weekly, dict) else 0
    all_filled = result.get("all_filled", False)
    print(
        f"[Lootpool refresh] ok source=wynnsource_fallback regions={regions} "
        f"filled={all_filled} primary_error={primary_error}"
    )
    return {
        "ok": True,
        "source": "wynnsource_fallback",
        "regions": result.get("regions", regions),
        "all_filled": all_filled,
        "weekly_lootpool": weekly,
        "primary_error": primary_error,
    }


async def _post_official_write(weekly_lootpool: dict) -> None:
    """Run the icon post-process + on-disk write that mirrors the legacy path.

    Imports are lazy so the module remains importable without hikari.
    """
    # Populate ``config.lootpool_data`` from the freshly-translated regions so
    # that the existing ``_lootpool_post_process`` (which expects that global)
    # can fetch icons. Skip if the admin helpers can't be imported (e.g. unit
    # tests without hikari).
    try:
        from lib.commands.admin import _lootpool_post_process, _update_lootpool
    except Exception:
        # Hikari-less test environment — fall back to writing JSON directly.
        await _write_lootpool_json_directly(weekly_lootpool)
        return

    config.lootpool_data = weekly_lootpool.get("Loot", {})
    try:
        icon_data = await _lootpool_post_process()
        config.lootpool_icon = icon_data["icons"]
        weekly_lootpool["Icon"] = config.lootpool_icon
    except Exception as error:
        print(f"[Lootpool refresh] icon fetch warning: {type(error).__name__}: {error}")

    await _update_lootpool(weekly_lootpool)


async def _write_lootpool_json_directly(weekly_lootpool: dict) -> None:
    """Hikari-free fallback that writes the same JSON as ``_update_lootpool``."""
    import json

    path = config.DATA_PATH / "weekly_lootpool.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(weekly_lootpool, fh, indent=3)
        print(f"Lootpool updated. Timestamp: {weekly_lootpool.get('Timestamp')}")
    except Exception as error:
        print(f"[Lootpool refresh] direct write failed: {type(error).__name__}: {error}")


async def _write_lootpool_log_if_filled(weekly_lootpool: dict):
    if not _all_regions_lootpool_filled(weekly_lootpool):
        return
    rotation_ts = weekly_lootpool.get("Timestamp")
    if not isinstance(rotation_ts, (int, float)):
        print("[Lootpool log] missing rotation timestamp, skipping write")
        return

    rotation_date = datetime.fromtimestamp(rotation_ts).strftime("%Y-%m-%d")
    log_path = config.DATA_PATH / "lootpool_history.log"
    try:
        existing = log_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        existing = ""

    marker = f"Week of {rotation_date}:"
    if marker in existing:
        print(f"[Lootpool log] rotation {rotation_date} already logged, skipping")
        return

    new_entry = f"{marker}\n"
    for region, pool in weekly_lootpool.get("Loot", {}).items():
        shiny = pool.get("Shiny", {})
        new_entry += f"{region}:\nShiny {shiny.get('Item', 'N/A')}\n{shiny.get('Tracker', 'N/A')} Tracker\n"
        for mythic in pool.get("Mythic", []):
            new_entry += f"- {mythic}\n"
    new_entry += "\n"
    log_path.write_text(existing + new_entry, encoding="utf-8")
    print(f"[Lootpool log] wrote entry for rotation {rotation_date}")
    try:
        from lib.commands.admin import _convert_lootpool_to_json
    except Exception:
        return
    await _convert_lootpool_to_json()


async def lootpool_refresh_task():
    """Auto-refresh item lootpool with burst/slow cadence."""
    print(
        f"[Lootpool refresh] task started, burst={config.LOOTPOOL_REFRESH_BURST_INTERVAL}s, "
        f"base={config.LOOTPOOL_REFRESH_BASE_INTERVAL}s"
    )
    log_written = False
    previous_filled = False
    while True:
        all_filled = False
        try:
            result = await refresh_item_lootpool()
            if "error" in result:
                print(f"[Lootpool refresh] failed: {result['error']}")
            else:
                all_filled = result.get("all_filled", False)
                if all_filled and not log_written:
                    weekly_lootpool = result.get("weekly_lootpool")
                    if weekly_lootpool:
                        await _write_lootpool_log_if_filled(weekly_lootpool)
                        log_written = True
                if previous_filled and not all_filled:
                    log_written = False
                    print("[Lootpool refresh] pools emptied (new rotation), log reset")
                previous_filled = all_filled
        except Exception as error:
            print(f"[Lootpool refresh] unexpected: {type(error).__name__}: {error}")

        interval = _compute_lootpool_refresh_interval(all_filled)
        print(f"[Lootpool refresh] sleeping {interval}s (filled={all_filled})")
        await asyncio.sleep(interval)
