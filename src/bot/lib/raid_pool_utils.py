"""Raid aspect, raid item, and gambit pool helpers.

Local-file loaders and tier normalization helpers used by the runtime views.
External pool sync has been removed from the open-source build; the bot now
reads weekly pool data from disk only.
"""

from __future__ import annotations

import json
import time

import lib.config as config
from lib.config import (
    ASPECT_TIERS,
    GAMBIT_POOL_FILE,
    GAMBIT_REGIONS,
    RAID_ITEM_TIERS,
    RAID_NAMES,
    WEEKLY_ASPECT_POOL_FILE,
    WEEKLY_RAID_POOL_FILE,
)


def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return default


def _bucket_has_tier_data(bucket) -> bool:
    if not isinstance(bucket, dict):
        return False
    return any(isinstance(value, list) and value for value in bucket.values())


def _alias_legacy_grootslang_key(loot: dict) -> dict:
    if not isinstance(loot, dict):
        return {}
    normalized = dict(loot)
    if "NOTG" in normalized:
        notg_bucket = normalized.pop("NOTG")
        if not _bucket_has_tier_data(normalized.get("NOG")):
            normalized["NOG"] = notg_bucket if isinstance(notg_bucket, dict) else {}
    return normalized


def _normalize_tier_bucket(bucket: dict, tiers: list[str]) -> dict:
    bucket = bucket if isinstance(bucket, dict) else {}
    return {
        tier: list(bucket.get(tier, [])) if isinstance(bucket.get(tier, []), list) else []
        for tier in tiers
    }


def normalize_raid_loot(source_loot: dict, tiers: list[str]) -> dict:
    source_loot = _alias_legacy_grootslang_key(source_loot if isinstance(source_loot, dict) else {})
    normalized = {
        raid_name: _normalize_tier_bucket(source_loot.get(raid_name, {}), tiers)
        for raid_name in RAID_NAMES
    }
    for raid_name, raid_bucket in source_loot.items():
        if raid_name in normalized or raid_name == "NOTG":
            continue
        normalized[raid_name] = _normalize_tier_bucket(raid_bucket, tiers)
    return normalized


_normalize_raid_loot = normalize_raid_loot


async def load_aspect_lootpool() -> dict:
    data = _load_json(WEEKLY_ASPECT_POOL_FILE, {})
    if not isinstance(data, dict):
        data = {}
    normalized = dict(data)
    normalized["Loot"] = _normalize_raid_loot(data.get("Loot", {}), ASPECT_TIERS)
    normalized["Icon"] = normalized.get("Icon", {}) if isinstance(normalized.get("Icon"), dict) else {}
    normalized["Timestamp"] = normalized.get("Timestamp") if isinstance(normalized.get("Timestamp"), int) else int(time.time())
    return normalized


async def load_weekly_raid_pool() -> dict:
    raid_data = _load_json(WEEKLY_RAID_POOL_FILE, {})
    raid_data = raid_data if isinstance(raid_data, dict) else {}

    fallback_aspects = await load_aspect_lootpool()
    timestamp = raid_data.get("Timestamp")
    if not isinstance(timestamp, int):
        timestamp = fallback_aspects.get("Timestamp")
    if not isinstance(timestamp, int):
        timestamp = int(time.time())

    aspects_section = raid_data.get("Aspects")
    if isinstance(aspects_section, dict):
        source_aspects = aspects_section.get("Loot", aspects_section)
    else:
        source_aspects = fallback_aspects.get("Loot", {})
    if not isinstance(source_aspects, dict) or not source_aspects:
        source_aspects = fallback_aspects.get("Loot", {})

    source_items = raid_data.get("Loot", {})
    if not isinstance(source_items, dict):
        source_items = raid_data.get("RaidItemLoot", {})
    if not isinstance(source_items, dict):
        source_items = {}
    if not source_items and isinstance(config.raid_item_pool_data, dict):
        source_items = config.raid_item_pool_data

    icon = raid_data.get("Icon", {})
    if not isinstance(icon, dict):
        icon = {}
    if not icon:
        icon.update(fallback_aspects.get("Icon", {}) if isinstance(fallback_aspects.get("Icon"), dict) else {})
        if isinstance(raid_data.get("RaidItemIcon"), dict):
            icon.update(raid_data.get("RaidItemIcon", {}))
        if isinstance(config.raid_item_icon, dict):
            icon.update(config.raid_item_icon)

    normalized = {
        "Loot": _normalize_raid_loot(source_items, RAID_ITEM_TIERS),
        "Aspects": _normalize_raid_loot(source_aspects, ASPECT_TIERS),
        "Icon": icon,
        "Timestamp": timestamp,
    }
    return normalized


async def load_gambit_pool() -> dict:
    data = _load_json(GAMBIT_POOL_FILE, {})
    return data if isinstance(data, dict) else {}


def _normalize_gambit_loot_shape(raw_loot) -> list:
    if isinstance(raw_loot, list):
        return raw_loot
    if isinstance(raw_loot, dict):
        for raid in GAMBIT_REGIONS:
            entries = raw_loot.get(raid)
            if isinstance(entries, list) and entries:
                return entries
        for entries in raw_loot.values():
            if isinstance(entries, list) and entries:
                return entries
    return []


def normalize_gambit_pool_cache() -> None:
    config.gambit_pool_data = _normalize_gambit_loot_shape(config.gambit_pool_data)
