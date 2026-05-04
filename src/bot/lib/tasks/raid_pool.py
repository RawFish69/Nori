"""Weekly raid aspect and raid item pool refresh loop."""

import asyncio
import json
import time

import lib.config as config
from lib.commands.admin import (
    _aspect_post_process,
    _create_weekly_aspects,
    _get_loot_from_source,
    _sync_aspect_lootpool,
    _update_aspect_pool,
)
from lib.raid_pool_utils import _normalize_raid_loot
from lib.wynnsource_pool import clean_item_name, format_attempt_log, is_ward_item


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
    icon_map = {}
    for raid_data in config.raid_item_pool_data.values():
        if not isinstance(raid_data, dict):
            continue
        for items in raid_data.values():
            if not isinstance(items, list):
                continue
            for item_name in items:
                icon_map.setdefault(item_name, None)
                if item_name in config.WARD_ICON_FILES:
                    icon_map[item_name] = config.WARD_ICON_FILES[item_name]
                elif item_name in config.MISC_ITEM_ICON_FILES:
                    icon_map[item_name] = config.MISC_ITEM_ICON_FILES[item_name]
    empty_items = [item_name for item_name, icon in icon_map.items() if not icon]
    return {"icons": icon_map, "warning": empty_items}


async def _create_weekly_raid_pool(aspect_pool: dict | None = None) -> dict:
    if not isinstance(aspect_pool, dict):
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


def _all_raids_pool_filled() -> bool:
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


async def refresh_raid_pools() -> dict:
    try:
        synced_aspects = await _sync_aspect_lootpool()
    except Exception as error:
        print(f"[Raid refresh] aspect sync error: {type(error).__name__}: {error}")
        synced_aspects = {"raids": 0}

    try:
        synced_items = await _sync_raid_item_lootpool()
    except Exception as error:
        print(f"[Raid refresh] item sync error: {type(error).__name__}: {error}")
        synced_items = {"items": 0}

    if not synced_aspects.get("raids") and not synced_items.get("items"):
        return {"error": "both_syncs_empty"}

    try:
        icon_data = await _aspect_post_process()
        config.aspect_icon = icon_data["icons"]
    except Exception as error:
        print(f"[Raid refresh] aspect icon warning: {type(error).__name__}: {error}")

    try:
        item_icon_data = await _raid_item_post_process()
        config.raid_item_icon = item_icon_data["icons"]
    except Exception as error:
        print(f"[Raid refresh] item icon warning: {type(error).__name__}: {error}")

    weekly_aspects = await _create_weekly_aspects()
    await _update_aspect_pool(weekly_aspects)
    weekly_raid_pool = await _create_weekly_raid_pool(weekly_aspects)
    await _update_weekly_raid_pool(weekly_raid_pool)
    all_filled = _all_raids_pool_filled()
    return {
        "ok": True,
        "aspects": synced_aspects.get("raids", 0),
        "items": synced_items.get("items", 0),
        "all_filled": all_filled,
    }


async def raid_pool_refresh_task():
    """Auto-refresh raid aspect + item pools from WCS."""
    print(
        f"[Raid refresh] task started, burst={config.RAID_POOL_REFRESH_BURST_INTERVAL}s "
        f"for {config.RAID_POOL_REFRESH_BURST_DURATION}s, base={config.RAID_POOL_REFRESH_BASE_INTERVAL}s"
    )
    while True:
        all_filled = False
        try:
            result = await refresh_raid_pools()
            if "error" in result:
                print(f"[Raid refresh] failed: {result['error']}")
            else:
                all_filled = result.get("all_filled", False)
                print(f"[Raid refresh] ok aspects={result.get('aspects')} items={result.get('items')} filled={all_filled}")
        except Exception as error:
            print(f"[Raid refresh] unexpected: {type(error).__name__}: {error}")

        interval = _compute_raid_pool_refresh_interval(all_filled)
        print(f"[Raid refresh] sleeping {interval}s (filled={all_filled})")
        await asyncio.sleep(interval)
