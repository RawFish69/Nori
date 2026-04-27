"""Weekly item lootpool refresh loop."""

import asyncio
import time
from datetime import datetime

import lib.config as config
from lib.commands.admin import (
    _convert_lootpool_to_json,
    _create_weekly_lootpool,
    _lootpool_post_process,
    _sync_item_lootpool,
    _update_lootpool,
)


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
    if not all_filled:
        return config.LOOTPOOL_REFRESH_BURST_INTERVAL
    now_ts = now_ts if isinstance(now_ts, int) else int(time.time())
    next_rotation = _next_lootpool_rotation_ts(now_ts)
    previous_rotation = next_rotation - config.SECONDS_PER_WEEK
    if now_ts - previous_rotation <= config.LOOTPOOL_REFRESH_BURST_DURATION:
        return config.LOOTPOOL_REFRESH_BURST_INTERVAL
    return config.LOOTPOOL_REFRESH_BASE_INTERVAL


async def refresh_item_lootpool() -> dict:
    synced = await _sync_item_lootpool()
    if not synced:
        return {"error": "sync_returned_empty"}

    try:
        icon_data = await _lootpool_post_process()
        config.lootpool_icon = icon_data["icons"]
    except Exception as error:
        print(f"[Lootpool refresh] icon fetch warning: {type(error).__name__}: {error}")

    weekly_lootpool = await _create_weekly_lootpool()
    await _update_lootpool(weekly_lootpool)
    all_filled = _all_regions_lootpool_filled(weekly_lootpool)
    return {"ok": True, "regions": synced.get("regions", 0), "all_filled": all_filled, "weekly_lootpool": weekly_lootpool}


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
    await _convert_lootpool_to_json()


async def lootpool_refresh_task():
    """Auto-refresh item lootpool from WCS with burst/slow cadence."""
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
                print(f"[Lootpool refresh] ok regions={result.get('regions')} filled={all_filled}")
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
