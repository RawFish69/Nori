"""Raid aspect, raid item, and gambit pool helpers.

These are the reusable pieces behind the modular `/raid` commands. They are
ported from the working `bot.py` flows while keeping runtime state in
`lib.config`.
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

import lib.config as config
from lib.config import (
    ASPECT_TIERS,
    GAMBIT_POOL_FILE,
    GAMBIT_REFRESH_BASE_INTERVAL,
    GAMBIT_REFRESH_FAST_INTERVAL,
    GAMBIT_REFRESH_FAST_WINDOW_AFTER,
    GAMBIT_REFRESH_FAST_WINDOW_BEFORE,
    GAMBIT_REGIONS,
    GAMBIT_ROTATION_HOUR_ET,
    RAID_ITEM_TIERS,
    RAID_NAMES,
    WEEKLY_ASPECT_POOL_FILE,
    WEEKLY_RAID_POOL_FILE,
    WCS_POOL_BETA_BASE_URL,
    WCS_POOL_PRIMARY_BASE_URL,
    WCS_POOL_TIMEOUT,
    WYNN_SOURCE_TOKEN,
)
from lib.wynnsource_pool import format_attempt_log

V2_GAMBIT_BASE_PATH = "/api/v2/raid/gambit"
SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 604800


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
    # Aspects publish automatically (like item lootpools): the source of truth is
    # the auto-refreshed weekly_raid_pool.json, where aspect data lives under
    # "Aspects". The legacy manually-published weekly_aspects.json (aspect data
    # under "Loot") is kept only as a fallback when the raid pool has no aspects.
    raid_data = _load_json(WEEKLY_RAID_POOL_FILE, {})
    raid_data = raid_data if isinstance(raid_data, dict) else {}
    aspects_section = raid_data.get("Aspects")
    if isinstance(aspects_section, dict):
        source_aspects = aspects_section.get("Loot", aspects_section)
        if isinstance(source_aspects, dict) and source_aspects:
            icon = raid_data.get("Icon", {})
            timestamp = raid_data.get("Timestamp")
            return {
                "Loot": _normalize_raid_loot(source_aspects, ASPECT_TIERS),
                "Icon": icon if isinstance(icon, dict) else {},
                "Timestamp": timestamp if isinstance(timestamp, int) else int(time.time()),
            }

    # Legacy fallback: manually-published aspect file (aspect data under "Loot").
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


def _fetch_gambits_v2(token: str | None, base_url: str, timeout: int) -> dict:
    headers = {"Accept": "application/json"}
    if token:
        headers["X-API-KEY"] = token

    response = requests.get(f"{base_url}{V2_GAMBIT_BASE_PATH}", headers=headers, timeout=timeout)
    response.raise_for_status()
    payload = response.json() if response.content else {}
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    return data if isinstance(data, dict) else {}


def fetch_gambits_with_failover(
    token: str | None,
    primary_base_url: str,
    beta_base_url: str,
    timeout: int,
) -> dict:
    attempts: list[str] = []
    for source_key in ("v2_primary", "v2_beta"):
        try:
            base_url = primary_base_url if source_key == "v2_primary" else beta_base_url
            payload = _fetch_gambits_v2(token, base_url=base_url, timeout=timeout)
        except Exception as exc:
            attempts.append(f"{source_key}: request error ({type(exc).__name__}: {exc})")
            continue

        if payload:
            gambit_count = len(payload.get("gambits", [])) if isinstance(payload.get("gambits"), list) else 0
            attempts.append(f"{source_key}: ok (gambits={gambit_count})")
            return {"payload": payload, "source": source_key, "attempts": attempts}
        attempts.append(f"{source_key}: empty payload")

    return {"payload": None, "source": None, "attempts": attempts}


async def get_gambits_from_source(token: str | None) -> dict:
    result = await asyncio.to_thread(
        lambda: fetch_gambits_with_failover(
            token,
            primary_base_url=WCS_POOL_PRIMARY_BASE_URL,
            beta_base_url=WCS_POOL_BETA_BASE_URL,
            timeout=WCS_POOL_TIMEOUT,
        )
    )
    if result.get("payload") is None:
        return {
            "error": "All configured WynnSource gambit sources were unusable.",
            "attempts": result.get("attempts", []),
        }
    print(f"[GambitFetch] source={result.get('source')} attempts={format_attempt_log(result.get('attempts', []))}")
    return result


def _parse_rotation_ts(value) -> int | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        return int(datetime.fromisoformat(text).timestamp())
    except ValueError:
        pass
    try:
        if text.endswith("Z"):
            return int(datetime.fromisoformat(text[:-1] + "+00:00").timestamp())
    except ValueError:
        pass
    return None


def convert_gambit_format(raw_payload: dict) -> dict:
    source = raw_payload if isinstance(raw_payload, dict) else {}
    if "gambits" not in source and any(isinstance(source.get(raid), dict) for raid in GAMBIT_REGIONS):
        candidate = {}
        for raid in GAMBIT_REGIONS:
            raid_payload = source.get(raid)
            if not isinstance(raid_payload, dict):
                continue
            if not candidate:
                candidate = raid_payload
            if isinstance(raid_payload.get("gambits"), list) and raid_payload.get("gambits"):
                candidate = raid_payload
                break
        source = candidate if isinstance(candidate, dict) else {}

    entries: list = []
    raw_entries = source.get("gambits", [])
    if isinstance(raw_entries, list):
        for entry in raw_entries:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            description = entry.get("description")
            confidence = entry.get("confidence")
            try:
                confidence_value = float(confidence) if confidence is not None else None
            except (TypeError, ValueError):
                confidence_value = None
            entries.append({
                "name": name.strip(),
                "description": description.strip() if isinstance(description, str) else "",
                "confidence": confidence_value,
            })

    rotation_start = _parse_rotation_ts(source.get("rotation_start"))
    rotation_end = _parse_rotation_ts(source.get("rotation_end"))
    return {
        "Loot": entries,
        "Rotation": {"rotation_start": rotation_start, "rotation_end": rotation_end},
        "RotationStart": rotation_start,
        "RotationEnd": rotation_end,
    }


async def sync_gambits() -> dict:
    fetch_result = await get_gambits_from_source(WYNN_SOURCE_TOKEN)
    attempts = format_attempt_log(fetch_result.get("attempts", []))
    if "error" in fetch_result:
        print(f"[Gambit sync] unusable; keeping existing cache. Attempts: {attempts}")
        return {"error": fetch_result["error"], "attempts": attempts}

    converted = convert_gambit_format(fetch_result.get("payload", {}) or {})
    config.gambit_pool_data = converted.get("Loot", [])
    normalize_gambit_pool_cache()
    return converted


async def update_gambit_pool(gambit_pool: dict) -> None:
    with open(GAMBIT_POOL_FILE, "w", encoding="utf-8") as file:
        json.dump(gambit_pool, file, indent=3)
    print(f"[Gambit update] wrote {GAMBIT_POOL_FILE} timestamp={gambit_pool.get('Timestamp')}")


async def refresh_gambits() -> dict:
    converted = await sync_gambits()
    if "error" in converted:
        return converted

    now_ts = int(time.time())
    file_payload = {
        "Loot": converted.get("Loot", []),
        "Rotation": converted.get("Rotation", {}),
        "RotationStart": converted.get("RotationStart"),
        "RotationEnd": converted.get("RotationEnd"),
        "Timestamp": converted.get("RotationStart") or now_ts,
        "RefreshedAt": now_ts,
    }
    try:
        await update_gambit_pool(file_payload)
    except Exception as error:
        return {"error": f"write_failed: {type(error).__name__}: {error}"}

    return {
        "ok": True,
        "gambits": len(converted.get("Loot", [])) if isinstance(converted.get("Loot"), list) else 0,
        "rotation_start": converted.get("RotationStart"),
        "rotation_end": converted.get("RotationEnd"),
        "refreshed_at": now_ts,
    }


def _next_gambit_rotation_ts(now_ts: int | None = None) -> int:
    et = ZoneInfo("America/New_York")
    now = datetime.fromtimestamp(now_ts if isinstance(now_ts, int) else int(time.time()), tz=et)
    target = now.replace(hour=GAMBIT_ROTATION_HOUR_ET, minute=0, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    return int(target.timestamp())


def current_gambit_refresh_interval(now_ts: int | None = None, **_kwargs) -> int:
    now_ts = now_ts if isinstance(now_ts, int) else int(time.time())
    next_rotation = _next_gambit_rotation_ts(now_ts)
    previous_rotation = next_rotation - SECONDS_PER_DAY
    time_until_next = next_rotation - now_ts
    time_since_previous = now_ts - previous_rotation
    if time_until_next <= GAMBIT_REFRESH_FAST_WINDOW_BEFORE:
        return GAMBIT_REFRESH_FAST_INTERVAL
    if time_since_previous <= GAMBIT_REFRESH_FAST_WINDOW_AFTER:
        return GAMBIT_REFRESH_FAST_INTERVAL
    return GAMBIT_REFRESH_BASE_INTERVAL
