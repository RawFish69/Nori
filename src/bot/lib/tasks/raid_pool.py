"""Weekly raid aspect and raid item pool refresh loop.

Refresh orchestration:

1. If ``config.LOOTPOOL_USE_OFFICIAL_PRIMARY`` is on, call the official
   ``/v3/map/loot-pools`` endpoint through :mod:`lib.wynn_map_api` and
   translate the raid half into the on-disk ``weekly_raid_pool.json`` shape
   via :func:`lib.lootpool_translate.translate_raid_pool`. Wards are then
   mirrored from ``Loot[raid]["Mythic"]`` into ``Aspects[raid]["Mythic"]``
   per the AGENT.md §7 ward-in-aspect-mythic contract.
2. If ``config.LOOTPOOL_ENRICH_WITH_WYNNSOURCE`` is also on, fetch the
   WynnSource aspect pool in the same cycle and merge any auxiliary
   metadata via :func:`_merge_raid_enrichment`. Both succeed -> ``source=hybrid``;
   official succeeds but enrichment fails -> ``source=official_only``.
3. If the official call fails, fall back to a hikari-free WynnSource-only
   path that calls ``fetch_pool_legacy_with_failover("aspect", ...)``
   directly and builds the canonical raid dict. Tagged
   ``source=wynnsource_fallback``.
4. If both paths fail in the same cycle, return an error dict tagged
   ``source=both`` and skip the on-disk write.

See ``AGENT/plans/V3_7_2_LOOTPOOL_MIGRATION.md`` sections 3 (architecture)
and 8 (logging contract) for the full contract.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import lib.config as config
from lib.lootpool_translate import (
    _empty_raid_aspects_block,
    _empty_raid_loot_block,
    translate_raid_pool,
)
from lib.raid_pool_utils import _normalize_raid_loot
from lib.wynn_map_api import fetch_loot_pools
from lib.wynnsource_pool import (
    clean_item_name,
    format_attempt_log,
    fetch_pool_legacy_with_failover,
    is_ward_item,
)


RARITY_LABELS_BY_TOKEN = {
    "MYTHIC": "Mythic",
    "FABLED": "Fabled",
    "LEGENDARY": "Legendary",
    "RARE": "Rare",
    "UNIQUE": "Unique",
}


def _normalize_raid_item_tier(raw_tier) -> str:
    if not isinstance(raw_tier, str) or not raw_tier.strip():
        return "Misc"
    token = raw_tier.strip()
    for tier in config.RAID_ITEM_TIERS:
        if token.casefold() == tier.casefold():
            return tier
    normalized = token.upper()
    if normalized.startswith("RARITY_"):
        normalized = normalized[len("RARITY_"):]
    mapped = RARITY_LABELS_BY_TOKEN.get(normalized)
    return mapped if mapped in config.RAID_ITEM_TIERS else "Misc"


def _convert_raid_item_loot_format(raid_item_data: dict) -> dict:
    loot = raid_item_data.get("data", {}).get("loot", {})
    weekly_items = {}
    for raid_name, raid_data in loot.items():
        rarity_map = {tier: [] for tier in config.RAID_ITEM_TIERS}
        if not isinstance(raid_data, dict):
            weekly_items[raid_name] = rarity_map
            continue
        for page_key in sorted(raid_data.keys(), key=lambda value: int(value) if str(value).isdigit() else 0):
            page = raid_data.get(page_key, {})
            items = page.get("items", {}) if isinstance(page, dict) else {}
            if not isinstance(items, dict):
                continue
            for raw_rarity, raw_entries in items.items():
                if not isinstance(raw_entries, list):
                    continue
                rarity = _normalize_raid_item_tier(raw_rarity)
                for raw_name in raw_entries:
                    if not isinstance(raw_name, str):
                        continue
                    name = clean_item_name(raw_name)
                    if name:
                        rarity_map[rarity].append(name)
        weekly_items[raid_name] = {tier: rarity_map[tier] for tier in config.RAID_ITEM_TIERS}
    return {"Loot": _normalize_raid_loot(weekly_items, config.RAID_ITEM_TIERS)}


async def _extract_raid_wards_by_region() -> dict:
    """Fetch raid item pool and extract weekly Ward drops for aspect display."""
    from lib.commands.admin import _get_loot_from_source

    wards_by_region = {raid: [] for raid in config.RAID_NAMES}
    try:
        fetch_result = await _get_loot_from_source("tome", config.WYNN_SOURCE_TOKEN)
    except Exception as error:
        print(f"[Aspect sync] tome pool fetch failed: {type(error).__name__}: {error}")
        return wards_by_region

    if "error" in fetch_result:
        print(
            "[Aspect sync] tome pool fetch unusable: "
            f"{format_attempt_log(fetch_result.get('attempts', []))}"
        )
        return wards_by_region

    loot = (fetch_result.get("payload", {}) or {}).get("data", {}).get("loot", {})
    if not isinstance(loot, dict):
        return wards_by_region

    for raid, region_data in loot.items():
        if not isinstance(region_data, dict):
            continue
        seen = set()
        bucket = []
        for page_key in sorted(region_data.keys(), key=lambda key: int(key) if str(key).isdigit() else 0):
            page = region_data.get(page_key, {})
            items = page.get("items", {}) if isinstance(page, dict) else {}
            mythic_list = items.get("Mythic", []) if isinstance(items, dict) else []
            if not isinstance(mythic_list, list):
                continue
            for name in mythic_list:
                if not isinstance(name, str) or not is_ward_item(name) or name in seen:
                    continue
                seen.add(name)
                bucket.append(name)
        # WCS keys Nest of the Grootslangs as NOTG; canonical short code is NOG.
        target = "NOG" if raid == "NOTG" else raid
        if target == "NOG" and wards_by_region.get("NOG"):
            existing = set(wards_by_region["NOG"])
            for ward in bucket:
                if ward not in existing:
                    wards_by_region["NOG"].append(ward)
                    existing.add(ward)
        else:
            wards_by_region[target] = bucket
    wards_by_region.pop("NOTG", None)
    return wards_by_region


async def _sync_raid_item_lootpool() -> dict:
    from lib.commands.admin import _get_loot_from_source

    fetch_result = await _get_loot_from_source("tome", config.WYNN_SOURCE_TOKEN)
    attempts = fetch_result.get("attempts", [])
    if "error" in fetch_result:
        defaults = {}
        try:
            with open(config.RAID_ITEM_POOL_DEFAULT_FILE, "r", encoding="utf-8") as file:
                defaults = json.load(file)
        except Exception:
            defaults = {"Loot": {}}
        config.raid_item_pool_data = _normalize_raid_loot(defaults.get("Loot", {}), config.RAID_ITEM_TIERS)
        print(
            "Raid item sync fallback to defaults. "
            f"{fetch_result['error']} Attempts: {format_attempt_log(attempts)}"
        )
        return {"items": len(config.raid_item_pool_data), "source": "defaults"}

    payload = fetch_result["payload"]
    config.raid_item_pool_data = _convert_raid_item_loot_format(payload)["Loot"]
    print(f"Raid item sync source={fetch_result.get('source')} Attempts: {format_attempt_log(attempts)}")
    return {"items": len(config.raid_item_pool_data), "source": fetch_result.get("source", "unknown")}


async def _raid_item_post_process() -> dict:
    from lib.commands.admin import _get_icon
    icon_map = {}
    for raid_data in config.raid_item_pool_data.values():
        if not isinstance(raid_data, dict):
            continue
        for items in raid_data.values():
            if not isinstance(items, list):
                continue
            for item_name in items:
                if item_name not in icon_map:
                    icon_map[item_name] = _get_icon(item_name)
    empty_items = [item_name for item_name, icon in icon_map.items() if not icon]
    return {"icons": icon_map, "warning": empty_items}


async def _create_weekly_raid_pool(aspect_pool: dict | None = None) -> dict:
    if not isinstance(aspect_pool, dict):
        from lib.commands.admin import _create_weekly_aspects
        aspect_pool = await _create_weekly_aspects()
    timestamp = aspect_pool.get("Timestamp", int(time.time()))
    if not isinstance(timestamp, int):
        timestamp = int(time.time())

    merged_icon = {}
    if isinstance(aspect_pool.get("Icon"), dict):
        merged_icon.update(aspect_pool.get("Icon", {}))
    if isinstance(config.raid_item_icon, dict):
        merged_icon.update(config.raid_item_icon)

    return {
        "Aspects": {
            raid: {
                tier: aspect_pool.get("Loot", {}).get(raid, {}).get(tier, [])
                for tier in config.ASPECT_TIERS
            }
            for raid in config.RAID_NAMES
        },
        "Loot": {
            raid: {
                tier: config.raid_item_pool_data.get(raid, {}).get(tier, [])
                for tier in config.RAID_ITEM_TIERS
            }
            for raid in config.RAID_NAMES
        },
        "Icon": merged_icon,
        "Timestamp": timestamp,
    }


async def _update_weekly_raid_pool(weekly_raid_pool: dict) -> None:
    with open(config.WEEKLY_RAID_POOL_FILE, "w", encoding="utf-8") as file:
        json.dump(weekly_raid_pool, file, indent=3)
    print(f"[Raid update] wrote {config.WEEKLY_RAID_POOL_FILE} timestamp={weekly_raid_pool['Timestamp']}")


def _all_raids_pool_filled(weekly_raid_pool: dict | None = None) -> bool:
    """Return True if every raid has at least a Mythic aspect and Mythic loot entry.

    If ``weekly_raid_pool`` is provided, the check runs directly off that dict
    (used by the new orchestration). Otherwise the legacy globals are consulted.
    """
    if isinstance(weekly_raid_pool, dict):
        aspects = weekly_raid_pool.get("Aspects", {})
        loot = weekly_raid_pool.get("Loot", {})
        for raid in config.RAID_NAMES:
            aspect_bucket = aspects.get(raid, {})
            if not isinstance(aspect_bucket, dict) or not aspect_bucket.get("Mythic"):
                return False
            item_bucket = loot.get(raid, {})
            if not isinstance(item_bucket, dict) or not item_bucket.get("Mythic"):
                return False
        return True

    for raid in config.RAID_NAMES:
        aspect_bucket = config.aspect_pool_data.get(raid, {})
        if not isinstance(aspect_bucket, dict) or not aspect_bucket.get("Mythic"):
            return False
        item_bucket = config.raid_item_pool_data.get(raid, {})
        if not isinstance(item_bucket, dict) or not item_bucket.get("Mythic"):
            return False
    return True


def _next_raid_pool_rotation_ts(now_ts: int | None = None) -> int:
    now_ts = now_ts if isinstance(now_ts, int) else int(time.time())
    elapsed = now_ts - (config.FIRST_WEEK_ASPECT_POOL + config.DST_OFFSET)
    weeks_elapsed = max(0, elapsed // config.SECONDS_PER_WEEK)
    return config.FIRST_WEEK_ASPECT_POOL + config.DST_OFFSET + (weeks_elapsed + 1) * config.SECONDS_PER_WEEK


def _compute_raid_pool_refresh_interval(all_filled: bool, now_ts: int | None = None) -> int:
    if not all_filled:
        return config.RAID_POOL_REFRESH_BURST_INTERVAL
    now_ts = now_ts if isinstance(now_ts, int) else int(time.time())
    next_rotation = _next_raid_pool_rotation_ts(now_ts)
    previous_rotation = next_rotation - config.SECONDS_PER_WEEK
    if now_ts - previous_rotation <= config.RAID_POOL_REFRESH_BURST_DURATION:
        return config.RAID_POOL_REFRESH_BURST_INTERVAL
    return config.RAID_POOL_REFRESH_BASE_INTERVAL


# ---------------------------------------------------------------------------
# Helpers for the new official-primary orchestration
# ---------------------------------------------------------------------------


def _mirror_wards_into_aspects(weekly_raid_pool: dict) -> None:
    """Ensure every ward in ``Loot[raid]["Mythic"]`` also appears in
    ``Aspects[raid]["Mythic"]``.

    Wards are surfaced from the official translator only under ``Loot``;
    nori AGENT.md §7 requires them in BOTH places. Mutates in place.
    """
    if not isinstance(weekly_raid_pool, dict):
        return
    aspects = weekly_raid_pool.get("Aspects")
    loot = weekly_raid_pool.get("Loot")
    if not isinstance(aspects, dict) or not isinstance(loot, dict):
        return

    for raid, loot_block in loot.items():
        if not isinstance(loot_block, dict):
            continue
        mythic_loot = loot_block.get("Mythic", [])
        if not isinstance(mythic_loot, list):
            continue
        wards = [name for name in mythic_loot if isinstance(name, str) and is_ward_item(name)]
        if not wards:
            continue
        aspect_block = aspects.setdefault(raid, _empty_raid_aspects_block())
        aspect_mythic = aspect_block.setdefault("Mythic", [])
        existing = set(aspect_mythic)
        for ward in wards:
            if ward not in existing:
                aspect_mythic.append(ward)
                existing.add(ward)


def _wynnsource_aspect_payload_to_blocks(payload: dict) -> tuple[dict, dict]:
    """Convert a WynnSource aspect-pool payload into nori ``Aspects`` + ``Loot``
    dicts keyed by canonical raid short code.

    The legacy aspect payload uses ``data.loot[raid][page].items[tier]`` where
    items at ``Mythic`` may contain a mix of true aspects and ward drops. We
    split them: wards go into ``Loot[raid]["Mythic"]``; non-wards become
    aspects under ``Aspects[raid][<tier>]``.

    Wards are mirrored into ``Aspects[raid]["Mythic"]`` by the caller via
    :func:`_mirror_wards_into_aspects`.
    """
    aspects: dict[str, dict[str, list[str]]] = {raid: _empty_raid_aspects_block() for raid in config.RAID_NAMES}
    loot: dict[str, dict[str, list[str]]] = {raid: _empty_raid_loot_block() for raid in config.RAID_NAMES}

    raw_loot = (payload or {}).get("data", {}).get("loot", {})
    if not isinstance(raw_loot, dict):
        return aspects, loot

    for raw_raid, raid_data in raw_loot.items():
        if not isinstance(raid_data, dict):
            continue
        # WCS keys Nest of the Grootslangs as NOTG; nori canonical is NOG.
        raid_code = "NOG" if raw_raid == "NOTG" else raw_raid

        aspect_block = aspects.setdefault(raid_code, _empty_raid_aspects_block())
        loot_block = loot.setdefault(raid_code, _empty_raid_loot_block())

        for page_key in sorted(raid_data.keys(), key=lambda value: int(value) if str(value).isdigit() else 0):
            page = raid_data.get(page_key, {})
            items = page.get("items", {}) if isinstance(page, dict) else {}
            if not isinstance(items, dict):
                continue
            for raw_rarity, raw_entries in items.items():
                if not isinstance(raw_entries, list):
                    continue
                rarity = _normalize_raid_item_tier(raw_rarity)
                aspect_tier = rarity if rarity in config.ASPECT_TIERS else None
                for raw_name in raw_entries:
                    if not isinstance(raw_name, str):
                        continue
                    name = clean_item_name(raw_name)
                    if not name:
                        continue
                    if is_ward_item(name):
                        if name not in loot_block.get("Mythic", []):
                            loot_block.setdefault("Mythic", []).append(name)
                        continue
                    if aspect_tier is not None:
                        bucket = aspect_block.setdefault(aspect_tier, [])
                        if name not in bucket:
                            bucket.append(name)
    return aspects, loot


def _merge_raid_enrichment(
    official_dict: dict[str, Any],
    wynnsource_blocks: dict[str, Any],
) -> dict[str, Any]:
    """Merge WynnSource raid enrichment into the official-sourced raid pool dict.

    Shape differs from Task 5's ``_merge_enrichment`` (raid pool has
    ``Aspects`` + ``Loot``, no Shiny tracker). Authoritative names from the
    official payload are preserved; enrichment only fills in names that the
    official side missed (rare in practice but cheap to support).

    Mutates and returns ``official_dict`` for convenience.
    """
    if not isinstance(official_dict, dict) or not isinstance(wynnsource_blocks, dict):
        return official_dict

    for section in ("Aspects", "Loot"):
        official_section = official_dict.get(section, {})
        wynn_section = wynnsource_blocks.get(section, {})
        for raid, wynn_block in wynn_section.items():
            official_block = official_section.setdefault(raid, {})
            for tier, wynn_entries in wynn_block.items():
                official_entries = official_block.setdefault(tier, [])
                existing = set(official_entries)
                for name in wynn_entries:
                    if name and name not in existing:
                        official_entries.append(name)
                        existing.add(name)
    return official_dict


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


async def _fetch_official_pool() -> dict:
    """Call the official ``/map/loot-pools`` endpoint off the event loop."""
    return await asyncio.to_thread(fetch_loot_pools)


async def _fetch_wynnsource_aspect_pool():
    """Call WynnSource's legacy failover chain for the aspect pool off-thread."""

    def _do_fetch():
        return fetch_pool_legacy_with_failover(
            "aspect",
            config.WYNN_SOURCE_TOKEN,
            primary_base_url=config.WCS_POOL_PRIMARY_BASE_URL,
            beta_base_url=config.WCS_POOL_BETA_BASE_URL,
            v1_base_url=config.WCS_POOL_V1_BASE_URL,
            timeout=config.WCS_POOL_TIMEOUT,
            allow_missing_regions=config.WCS_POOL_ALLOW_MISSING_REGIONS,
            enable_v1_fallback=config.WCS_POOL_ENABLE_V1_FALLBACK,
        )

    return await asyncio.to_thread(_do_fetch)


def _failure_detail(result: Any) -> str:
    """Render an official-API failure dict as a compact one-line string."""
    if not isinstance(result, dict):
        return repr(result)
    error = result.get("error", "unknown")
    detail = result.get("detail")
    if detail:
        return f"{error} ({detail})"
    return str(error)


async def _write_raid_pool_to_disk(weekly_raid_pool: dict) -> None:
    """Persist the raid pool dict to disk. Swallow IO errors with a log line."""
    try:
        await _update_weekly_raid_pool(weekly_raid_pool)
    except Exception as exc:  # noqa: BLE001
        print(
            f"[Raid pool refresh] on-disk write failed: {type(exc).__name__}: {exc}"
        )


async def _wynnsource_only_raid_refresh() -> dict:
    """Hikari-free WynnSource-only raid pool refresh.

    Calls ``fetch_pool_legacy_with_failover`` directly (so tests that mock the
    symbol imported into this module see the call) and assembles a canonical
    ``weekly_raid_pool`` dict. Returns either::

        {ok, regions, all_filled, weekly_raid_pool}

    on success or ``{"error": ..., "detail": ...}`` on failure.
    """
    try:
        wynn_result = await _fetch_wynnsource_aspect_pool()
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

    aspects, loot = _wynnsource_aspect_payload_to_blocks(payload)
    if not aspects and not loot:
        return {
            "error": "wynnsource_payload_empty",
            "detail": "WynnSource returned no parseable raids",
        }

    timestamp = _next_raid_pool_rotation_ts() - config.SECONDS_PER_WEEK
    weekly_raid_pool: dict[str, Any] = {
        "Aspects": aspects,
        "Loot": loot,
        "Icon": dict(config.aspect_icon) if isinstance(config.aspect_icon, dict) else {},
        "Timestamp": timestamp,
    }

    _mirror_wards_into_aspects(weekly_raid_pool)

    await _write_raid_pool_to_disk(weekly_raid_pool)

    all_filled = _all_raids_pool_filled(weekly_raid_pool)
    return {
        "ok": True,
        "regions": len(weekly_raid_pool.get("Aspects", {}) or {}),
        "all_filled": all_filled,
        "weekly_raid_pool": weekly_raid_pool,
    }


async def _legacy_refresh_with_tag(*, primary_error: str) -> dict:
    """Run the WynnSource-only path and tag the outcome.

    Used both when the official kill-switch is off and when the official
    primary call fails for the current cycle.
    """
    try:
        result = await _wynnsource_only_raid_refresh()
    except Exception as exc:  # noqa: BLE001
        fallback_error = f"{type(exc).__name__}: {exc}"
        print(
            f"[Raid pool refresh] failed source=both primary_error={primary_error} "
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
            f"[Raid pool refresh] failed source=both primary_error={primary_error} "
            f"fallback_error={fallback_error}"
        )
        return {
            "error": "both_sources_failed",
            "source": "both",
            "primary_error": primary_error,
            "fallback_error": fallback_error,
        }

    weekly = result.get("weekly_raid_pool", {})
    regions = len(weekly.get("Aspects", {}) or {}) if isinstance(weekly, dict) else 0
    all_filled = result.get("all_filled", False)
    print(
        f"[Raid pool refresh] ok source=wynnsource_fallback regions={regions} "
        f"filled={all_filled} primary_error={primary_error}"
    )
    return {
        "ok": True,
        "source": "wynnsource_fallback",
        "regions": result.get("regions", regions),
        "all_filled": all_filled,
        "weekly_raid_pool": weekly,
        "primary_error": primary_error,
    }


async def refresh_raid_pools() -> dict:
    if not config.LOOTPOOL_USE_OFFICIAL_PRIMARY:
        # Kill-switch path: WynnSource-only, tagged as fallback for log clarity.
        return await _legacy_refresh_with_tag(primary_error="primary_disabled")

    primary = await _fetch_official_pool()
    if not isinstance(primary, dict) or not primary.get("ok"):
        primary_error = _failure_detail(primary)
        return await _legacy_refresh_with_tag(primary_error=primary_error)

    # Official succeeded -> translate to on-disk shape.
    weekly_raid_pool: dict[str, Any] = translate_raid_pool(primary.get("data") or [])
    _mirror_wards_into_aspects(weekly_raid_pool)
    # Carry the icon cache forward; downstream renderers expect the key.
    merged_icon: dict[str, Any] = {}
    if isinstance(config.aspect_icon, dict):
        merged_icon.update(config.aspect_icon)
    if isinstance(config.raid_item_icon, dict):
        merged_icon.update(config.raid_item_icon)
    if merged_icon:
        existing_icon = weekly_raid_pool.get("Icon")
        if isinstance(existing_icon, dict):
            merged_icon.update(existing_icon)
        weekly_raid_pool["Icon"] = merged_icon

    source = "official_only"
    enrichment_error: str | None = None
    if config.LOOTPOOL_ENRICH_WITH_WYNNSOURCE:
        try:
            wynn_result = await _fetch_wynnsource_aspect_pool()
        except Exception as exc:  # noqa: BLE001 — enrichment is best-effort
            enrichment_error = f"{type(exc).__name__}: {exc}"
            print(
                f"[Raid pool refresh] enrichment failed (non-fatal): {enrichment_error}"
            )
        else:
            payload = getattr(wynn_result, "payload", None)
            if isinstance(payload, dict):
                wynn_aspects, wynn_loot = _wynnsource_aspect_payload_to_blocks(payload)
                if wynn_aspects or wynn_loot:
                    _merge_raid_enrichment(
                        weekly_raid_pool,
                        {"Aspects": wynn_aspects, "Loot": wynn_loot},
                    )
                    # Re-mirror wards (enrichment may have added ward entries).
                    _mirror_wards_into_aspects(weekly_raid_pool)
                    source = "hybrid"
                else:
                    enrichment_error = "wynnsource_payload_empty"
            else:
                attempts = getattr(wynn_result, "attempts", None)
                enrichment_error = f"wynnsource_unusable attempts={attempts}"

    await _write_raid_pool_to_disk(weekly_raid_pool)

    regions = len(weekly_raid_pool.get("Aspects", {}) or {})
    all_filled = _all_raids_pool_filled(weekly_raid_pool)
    extras = f"enrichment_error={enrichment_error}" if enrichment_error else ""
    suffix = f" {extras}" if extras else ""
    print(
        f"[Raid pool refresh] ok source={source} regions={regions} filled={all_filled}{suffix}"
    )
    return {
        "ok": True,
        "source": source,
        "regions": regions,
        "all_filled": all_filled,
        "weekly_raid_pool": weekly_raid_pool,
    }


async def raid_pool_refresh_task():
    """Auto-refresh raid aspect + item pools."""
    print(
        f"[Raid pool refresh] task started, burst={config.RAID_POOL_REFRESH_BURST_INTERVAL}s "
        f"for {config.RAID_POOL_REFRESH_BURST_DURATION}s, base={config.RAID_POOL_REFRESH_BASE_INTERVAL}s"
    )
    while True:
        all_filled = False
        try:
            result = await refresh_raid_pools()
            if "error" in result:
                print(f"[Raid pool refresh] failed: {result['error']}")
            else:
                all_filled = result.get("all_filled", False)
        except Exception as error:
            print(f"[Raid pool refresh] unexpected: {type(error).__name__}: {error}")

        interval = _compute_raid_pool_refresh_interval(all_filled)
        print(f"[Raid pool refresh] sleeping {interval}s (filled={all_filled})")
        await asyncio.sleep(interval)
