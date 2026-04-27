"""Admin and data maintenance command groups."""

import asyncio
import json
import os
import time
import tracemalloc
from datetime import datetime

import hikari
import lightbulb
import requests

import lib.config as config
from lib.config import (
    BOT_PATH,
    DATA_PATH,
    DATA_SCRIPTS_DATABASE_PATH,
    LOOTPOOL_REGIONS,
    RAID_NAMES,
    LOOT_TIERS,
    ASPECT_TIERS,
    WYNN_SOURCE_TOKEN,
)
from lib.utils import check_user_access, get_uptime
from lib.wynnsource_pool import (
    RARITY_LABELS_BY_TOKEN,
    clean_item_name,
    fetch_pool_legacy_with_failover,
    format_attempt_log,
    is_ward_item,
)
from lib.raid_pool_utils import (
    _normalize_gambit_loot_shape,
    current_gambit_refresh_interval,
    normalize_gambit_pool_cache,
    refresh_gambits,
)
from lib.raid_pool_utils import _normalize_raid_loot
from lib.manager_registry import get_managers
from lib.item_db_compat import items_response_to_dict, looks_like_item_database


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=3)


def _load_json(path, default=None):
    if default is None:
        default = {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def _normalize_item_payload(raw_items) -> dict:
    try:
        item_map, _ = items_response_to_dict(raw_items)
        if looks_like_item_database(item_map):
            return item_map
    except Exception as error:
        print(f"Item payload normalization failed: {type(error).__name__}: {error}")
    return {}


def _option_value(ctx: lightbulb.Context, name: str, default=None):
    """Read slash option values safely, including names that shadow option methods."""
    try:
        return ctx.options[name]
    except Exception:
        pass
    if isinstance(getattr(ctx, "raw_options", None), dict):
        value = ctx.raw_options.get(name)
        if value is not None:
            return value
    value = getattr(ctx.options, name, default)
    return value if not callable(value) else default


async def _fetch_api_usage_from_nori() -> dict:
    def request_usage():
        if not config.NORI_API_USAGE_TOKEN:
            raise RuntimeError("Missing NORI_API_USAGE_TOKEN or API_USAGE_TOKEN in environment")
        headers = {"X-Nori-Admin-Token": config.NORI_API_USAGE_TOKEN}
        response = requests.get(f"{config.NORI_API_BASE_URL}/api/usage", headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    import asyncio

    return await asyncio.to_thread(request_usage)



def _ensure_lootpool_cache():
    if not config.lootpool_data:
        data = _load_json(DATA_PATH / "lootpool_default.json", {"Loot": {}})
        config.lootpool_data = data.get("Loot", {})


def _ensure_aspect_cache():
    if not config.aspect_pool_data:
        data = _load_json(DATA_PATH / "default_aspect_pool.json", {"Loot": {}})
        config.aspect_pool_data = _normalize_raid_loot(data.get("Loot", {}), ASPECT_TIERS)


def _ensure_raid_item_cache():
    if not config.raid_item_pool_data:
        data = _load_json(config.RAID_ITEM_POOL_DEFAULT_FILE, {"Loot": {}})
        config.raid_item_pool_data = _normalize_raid_loot(data.get("Loot", {}), config.RAID_ITEM_TIERS)


def _trim_preview_text(text: str, limit: int = 900) -> str:
    if not isinstance(text, str):
        text = str(text)
    return text if len(text) <= limit else text[:limit - 3] + "..."


def _summarize_pool_tiers(bucket: dict, tiers: list[str], sample_size: int = 2) -> str:
    bucket = bucket if isinstance(bucket, dict) else {}
    lines = []
    for tier in tiers:
        entries = bucket.get(tier, [])
        entries = entries if isinstance(entries, list) else []
        count = len(entries)
        if count:
            sample = ", ".join(str(name) for name in entries[:sample_size])
            if count > sample_size:
                sample += ", ..."
            lines.append(f"{tier}: {count} ({sample})")
        else:
            lines.append(f"{tier}: 0")
    return _trim_preview_text("\n".join(lines), limit=900)


def _summarize_lootpool_region_preview(region_bucket: dict, sample_size: int = 2) -> str:
    region_bucket = region_bucket if isinstance(region_bucket, dict) else {}
    shiny_data = region_bucket.get("Shiny", {})
    shiny_data = shiny_data if isinstance(shiny_data, dict) else {}
    shiny_item = shiny_data.get("Item", "N/A")
    shiny_tracker = shiny_data.get("Tracker", "N/A")
    lines = [f"Shiny: {shiny_item} ({shiny_tracker} Tracker)"]
    lines.append(_summarize_pool_tiers(region_bucket, LOOT_TIERS, sample_size=sample_size))
    return _trim_preview_text("\n".join(lines), limit=900)


def _get_icon(item_name):
    special_items = {
        "Corkian Insulator": "insulator.png",
        "Corkian Simulator": "simulator.png",
        "Yellow Ward": "yellow_ward.png",
        "White Ward": "white_ward.png",
        "Red Ward": "red_ward.png",
        "Purple Ward": "purple_ward.png",
        "Pink Ward": "pink_ward.png",
        "Orange Ward": "orange_ward.png",
        "Green Ward": "green_ward.png",
        "Cyan Ward": "cyan_ward.png",
        "Blue Ward": "blue_ward.png",
        "Black Ward": "black_ward.png",
    }

    if item_name in config.item_processed:
        data = config.item_processed[item_name]
        icon_data = data.get("icon")
        if icon_data:
            if isinstance(icon_data, str):
                if icon_data.startswith("http"):
                    return icon_data
                icon_id = icon_data.replace(":", "_")
                return f"https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp"
            if isinstance(icon_data, dict):
                icon_format = icon_data.get("format")
                if icon_format == "legacy":
                    icon_value = icon_data.get("value")
                    if isinstance(icon_value, str):
                        icon_id = icon_value.replace(":", "_")
                        return f"https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp"
                elif icon_format == "attribute":
                    icon_id = icon_data.get("value", {}).get("name")
                    if icon_id:
                        return f"https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp"

        sub_type = data.get("subType")
        if sub_type in ("helmet", "chestplate", "leggings", "boots", "ring", "bracelet", "necklace"):
            return f"{sub_type}.png"
        return None

    return special_items.get(item_name)


async def _get_loot_from_source(pool: str, token: str) -> dict:
    if pool not in {"item", "aspect", "tome"}:
        raise ValueError(f"Unknown pool type: {pool}")

    result = await asyncio.to_thread(
        lambda: fetch_pool_legacy_with_failover(
            pool,
            token,
            primary_base_url=config.WCS_POOL_PRIMARY_BASE_URL,
            beta_base_url=config.WCS_POOL_BETA_BASE_URL,
            v1_base_url=config.WCS_POOL_V1_BASE_URL,
            timeout=config.WCS_POOL_TIMEOUT,
            allow_missing_regions=config.WCS_POOL_ALLOW_MISSING_REGIONS,
            enable_v1_fallback=config.WCS_POOL_ENABLE_V1_FALLBACK,
        )
    )

    if result.payload is None:
        return {
            "error": "All configured WynnSource pool sources were unusable.",
            "attempts": result.attempts,
        }

    return {
        "payload": result.payload,
        "source": result.source,
        "attempts": result.attempts,
    }


def _convert_lootpool_format(item_loot_data: dict) -> dict:
    loot = item_loot_data.get("data", {}).get("loot", {})
    weekly_loot = {}

    def normalize_lr_tier(raw_tier) -> str:
        if not isinstance(raw_tier, str):
            return "Misc"
        token = raw_tier.strip()
        if not token:
            return "Misc"
        for tier in LOOT_TIERS:
            if token.casefold() == tier.casefold():
                return tier
        normalized = token.upper()
        if normalized.startswith("RARITY_"):
            normalized = normalized[len("RARITY_"):]
        mapped = RARITY_LABELS_BY_TOKEN.get(normalized)
        return mapped if isinstance(mapped, str) and mapped in LOOT_TIERS else "Misc"

    for region, region_data in loot.items():
        out = {
            "Shiny": {"Item": "N/A", "Tracker": "N/A"},
            **{tier: [] for tier in LOOT_TIERS},
        }
        shiny_found = False
        rarity_map = {tier: [] for tier in LOOT_TIERS}

        for page_key in sorted(region_data.keys(), key=int):
            page = region_data[page_key]
            if not shiny_found and page.get("shiny"):
                out["Shiny"] = {
                    "Item": clean_item_name(page["shiny"].get("item", "")) or "N/A",
                    "Tracker": page["shiny"].get("tracker"),
                }
                shiny_found = True

            items = page.get("items", {})
            if not isinstance(items, dict):
                continue
            for raw_rarity, raw_entries in items.items():
                if not isinstance(raw_entries, list):
                    continue
                rarity = normalize_lr_tier(raw_rarity)
                for raw_name in raw_entries:
                    if not isinstance(raw_name, str):
                        continue
                    name = clean_item_name(raw_name)
                    if name:
                        rarity_map[rarity].append(name)

        mythic_items = list(rarity_map.get("Mythic", []))
        mythic_seen = set(mythic_items)
        for rarity in LOOT_TIERS:
            if rarity == "Mythic":
                continue
            filtered_items: list[str] = []
            for name in rarity_map[rarity]:
                if is_ward_item(name):
                    if name not in mythic_seen:
                        mythic_items.append(name)
                        mythic_seen.add(name)
                else:
                    filtered_items.append(name)
            rarity_map[rarity] = filtered_items
        rarity_map["Mythic"] = mythic_items
        shiny_item_name = out["Shiny"]["Item"]
        if shiny_found and shiny_item_name != "N/A" and shiny_item_name in rarity_map["Mythic"]:
            rarity_map["Mythic"].remove(shiny_item_name)

        for rarity in LOOT_TIERS:
            out[rarity] = rarity_map[rarity]
        weekly_loot[region] = out

    return {"Loot": weekly_loot}


def _convert_aspect_loot_format(raid_aspect_data: dict) -> dict:
    loot = raid_aspect_data.get("data", {}).get("loot", {})
    weekly_loot = {}

    for region, region_data in loot.items():
        out = {}
        rarity_map = {tier: [] for tier in ASPECT_TIERS}
        for page_key in sorted(region_data.keys(), key=int):
            page = region_data[page_key]
            items = page.get("items", {})
            for rarity in ASPECT_TIERS:
                if rarity in items:
                    for raw_name in items[rarity]:
                        if not isinstance(raw_name, str):
                            continue
                        name = clean_item_name(raw_name)
                        if name:
                            rarity_map[rarity].append(name)
        for rarity in ASPECT_TIERS:
            if rarity_map[rarity]:
                out[rarity] = rarity_map[rarity]
        weekly_loot[region] = out

    return {"Loot": weekly_loot}


async def _sync_item_lootpool():
    fetch_result = await _get_loot_from_source("item", WYNN_SOURCE_TOKEN)
    attempts = fetch_result.get("attempts", [])

    if "error" in fetch_result:
        defaults = _load_json(DATA_PATH / "lootpool_default.json", {"Loot": {}})
        config.lootpool_data = defaults.get("Loot", {})
        print(
            "Lootpool sync fallback to defaults. "
            f"{fetch_result['error']} Attempts: {format_attempt_log(attempts)}"
        )
        return {"regions": len(config.lootpool_data), "source": "defaults"}

    payload = fetch_result["payload"]
    config.lootpool_data = _convert_lootpool_format(payload)["Loot"]
    print(f"Lootpool sync source={fetch_result.get('source')} Attempts: {format_attempt_log(attempts)}")
    return {"regions": len(config.lootpool_data), "source": fetch_result.get("source", "unknown")}


async def _sync_aspect_lootpool():
    fetch_result = await _get_loot_from_source("aspect", WYNN_SOURCE_TOKEN)
    attempts = fetch_result.get("attempts", [])

    if "error" in fetch_result:
        defaults = _load_json(DATA_PATH / "default_aspect_pool.json", {"Loot": {}})
        config.aspect_pool_data = _normalize_raid_loot(defaults.get("Loot", {}), ASPECT_TIERS)
        print(
            "Aspect sync fallback to defaults. "
            f"{fetch_result['error']} Attempts: {format_attempt_log(attempts)}"
        )
        return {"raids": len(config.aspect_pool_data), "source": "defaults"}

    payload = fetch_result["payload"]
    config.aspect_pool_data = _normalize_raid_loot(_convert_aspect_loot_format(payload)["Loot"], ASPECT_TIERS)
    try:
        wards_by_region = await _extract_raid_wards_by_region()
    except Exception as error:
        wards_by_region = {}
        print(f"[Aspect sync] ward injection failed: {type(error).__name__}: {error}")

    for raid, wards in wards_by_region.items():
        if not wards:
            continue
        raid_bucket = config.aspect_pool_data.setdefault(raid, {})
        mythic_list = raid_bucket.setdefault("Mythic", [])
        if not isinstance(mythic_list, list):
            mythic_list = []
            raid_bucket["Mythic"] = mythic_list
        existing = set(mythic_list)
        for ward in wards:
            if ward not in existing:
                mythic_list.append(ward)
                existing.add(ward)
    print(f"Aspect sync source={fetch_result.get('source')} Attempts: {format_attempt_log(attempts)}")
    return {"raids": len(config.aspect_pool_data), "source": fetch_result.get("source", "unknown")}


async def _extract_raid_wards_by_region() -> dict:
    wards_by_region = {raid: [] for raid in RAID_NAMES}
    try:
        fetch_result = await _get_loot_from_source("tome", WYNN_SOURCE_TOKEN)
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
        wards_by_region[raid] = bucket
    return wards_by_region


async def _estimate_week_number():
    current_time = int(time.time())
    elapsed_time = current_time - config.FIRST_WEEK_TIMESTAMP
    elapsed_weeks = elapsed_time / config.SECONDS_PER_WEEK
    return int(elapsed_weeks) + 1


async def _aspect_week_number():
    current_time = int(time.time())
    elapsed_time = current_time - config.FIRST_WEEK_ASPECT_POOL
    elapsed_weeks = elapsed_time / config.SECONDS_PER_WEEK
    return int(elapsed_weeks) + 1


async def _create_weekly_lootpool():
    week = await _estimate_week_number()
    starting_time = (
        (week - 1) * config.SECONDS_PER_WEEK + config.FIRST_WEEK_TIMESTAMP + config.DST_OFFSET
    )
    normalized_loot = {}
    for region in LOOTPOOL_REGIONS:
        region_data = config.lootpool_data.get(region, {})
        normalized_loot[region] = {
            "Shiny": region_data.get("Shiny", {"Item": "N/A", "Tracker": "N/A"})
        }
        for tier in LOOT_TIERS:
            normalized_loot[region][tier] = region_data.get(tier, [])

    return {"Loot": normalized_loot, "Icon": config.lootpool_icon, "Timestamp": starting_time}


async def _create_weekly_aspects():
    week = await _aspect_week_number()
    starting_time = (
        (week - 1) * config.SECONDS_PER_WEEK + config.FIRST_WEEK_ASPECT_POOL + config.DST_OFFSET
    )
    aspect_pool = {
        "Loot": {
            raid: {tier: config.aspect_pool_data[raid].get(tier, []) for tier in ASPECT_TIERS}
            for raid in RAID_NAMES
            if raid in config.aspect_pool_data
        },
        "Icon": config.aspect_icon,
        "Timestamp": starting_time,
    }
    return aspect_pool


async def _update_lootpool(weekly_lootpool):
    _write_json(DATA_PATH / "weekly_lootpool.json", weekly_lootpool)
    print(f"Lootpool updated. Timestamp: {weekly_lootpool['Timestamp']}")


async def _update_aspect_pool(aspect_pool):
    _write_json(DATA_PATH / "weekly_aspects.json", aspect_pool)
    print(f"Aspect pool updated. Timestamp: {aspect_pool['Timestamp']}")


async def _history_log(weekly_lootpool, update: bool, date_string: str):
    if update is not True:
        return

    log_data = f"Week of {date_string}:\n"
    for region, pool in weekly_lootpool["Loot"].items():
        shiny = pool.get("Shiny", {})
        log_data += f"{region}:\nShiny {shiny.get('Item', 'N/A')}\n{shiny.get('Tracker', 'N/A')} Tracker\n"
        for mythic in pool.get("Mythic", []):
            log_data += f"- {mythic}\n"
    log_data += "\n"

    with open(DATA_PATH / "lootpool_history.log", "a", encoding="utf-8") as file:
        file.write(log_data)


async def _get_loot_history():
    config.lootpool_history = {}
    with open(DATA_PATH / "lootpool_history.log", "r", encoding="utf-8") as log:
        lines = log.read().split("\n")

    week_key = ""
    region_data = {}
    shiny_item = ""
    region = ""
    while lines:
        line = lines.pop(0).strip()
        if line.startswith("Week of"):
            if week_key:
                config.lootpool_history[week_key] = region_data
            week_key = line.split(" ")[-1][:-1]
            region_data = {}
            shiny_item = ""
        elif line:
            sublist = []
            if "Shiny" in line:
                shiny_item += f"{line}"
            elif "Tracker" in line:
                shiny_item += f" & {line}"
                region_data[region].append(shiny_item)
                shiny_item = ""
                while lines:
                    next_line = lines.pop(0).strip()
                    if next_line.startswith("- "):
                        sublist.append(next_line.split("- ")[1])
                    else:
                        if lines:
                            lines.insert(0, next_line)
                        break
                if sublist:
                    region_data[region].append(sublist)
            else:
                region = line.split(":")[0]
                region_data[region] = []

    if week_key and region_data:
        config.lootpool_history[week_key] = region_data
    return config.lootpool_history


async def _convert_lootpool_to_json():
    pool_data = await _get_loot_history()
    _write_json(DATA_PATH / "lootpool_history.json", pool_data)


async def _lootpool_post_process():
    if not config.item_processed:
        config.item_processed = _load_json(BOT_PATH / "items.json", {})

    all_icons = {}
    tiers = {"Mythic", "Fabled", "Legendary", "Rare", "Unique", "Misc"}
    for region_data in config.lootpool_data.values():
        shiny_name = region_data.get("Shiny", {}).get("Item")
        if shiny_name:
            all_icons[shiny_name] = _get_icon(shiny_name)
        for tier, items in region_data.items():
            if tier in tiers:
                for item_name in items:
                    all_icons.setdefault(item_name, None)
                    if not all_icons[item_name]:
                        all_icons[item_name] = _get_icon(item_name)
    empty_items = [item_name for item_name, icon in all_icons.items() if not icon]
    return {"icons": all_icons, "warning": empty_items}


async def _aspect_post_process():
    aspect_data = _load_json(BOT_PATH / "aspects.json", {})
    config.aspect_data = aspect_data
    available_icons = aspect_data.get("icons", {})
    all_icons = {}
    tiers = {"Mythic", "Fabled", "Legendary"}
    for raid_data in config.aspect_pool_data.values():
        for tier, aspects in raid_data.items():
            if tier in tiers:
                for aspect_name in aspects:
                    all_icons.setdefault(aspect_name, None)
                    if not all_icons[aspect_name]:
                        all_icons[aspect_name] = available_icons.get(aspect_name)
    empty_items = [item_name for item_name, icon in all_icons.items() if not icon]
    return {"icons": all_icons, "warning": empty_items}


def _maintainer_check():
    return lightbulb.has_roles(config.DATA_MANAGER_ROLE_ID) | lightbulb.owner_only


def load_admin_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load admin and data commands."""

    managers = get_managers()
    database = managers.get("database")
    item_manager = managers.get("item_manager")
    changelog_manager = managers.get("changelog_manager")

    @bot.command
    @lightbulb.command("manage", "Admin tools")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def manage(ctx: lightbulb.Context):
        pass

    @manage.child()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.option("user", "User ID", type=int)
    @lightbulb.command("block", "Block user access")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def manage_block_users(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        user_id = int(ctx.options.user)
        user_list = blocked_users if blocked_users is not None else config.blocked_users
        if user_id == int(ctx.user.id):
            await ctx.respond("You cannot block yourself.")
            return
        normalized_users = []
        for blocked_id in user_list:
            try:
                normalized_users.append(int(blocked_id))
            except (TypeError, ValueError):
                continue
        try:
            user = await bot.rest.fetch_user(user_id)
            if user_id in normalized_users:
                await ctx.respond(f"User `{user.username}` ({user_id}) is already blocked.")
                return
            normalized_users.append(user_id)
            user_list.clear()
            user_list.extend(normalized_users)
            if user_list is not config.blocked_users:
                config.blocked_users.clear()
                config.blocked_users.extend(normalized_users)
            _write_json(BOT_PATH / "blocked_users.json", normalized_users)
            await ctx.respond(f"User `{user.username}` ({user_id}) added to blocked list.")
        except Exception as error:
            await ctx.respond(f"Failed to fetch user ID: {user_id}")
            print(f"Failed to fetch user ID for block user: {error}")

    @manage.child()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.option("user", "User ID", type=int)
    @lightbulb.command("unblock", "Block user access")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def manage_unblock_users(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        user_id = int(ctx.options.user)
        user_list = blocked_users if blocked_users is not None else config.blocked_users
        normalized_users = []
        for blocked_id in user_list:
            try:
                normalized_users.append(int(blocked_id))
            except (TypeError, ValueError):
                continue
        try:
            user = await bot.rest.fetch_user(user_id)
            if user_id not in normalized_users:
                await ctx.respond(f"User `{user.username}` ({user_id}) is not blocked.")
                return
            normalized_users.remove(user_id)
            user_list.clear()
            user_list.extend(normalized_users)
            if user_list is not config.blocked_users:
                config.blocked_users.clear()
                config.blocked_users.extend(normalized_users)
            _write_json(BOT_PATH / "blocked_users.json", normalized_users)
            await ctx.respond(f"User `{user.username}` ({user_id}) removed from blocked list.")
        except Exception as error:
            await ctx.respond(f"Failed to fetch user ID: {user_id}")
            print(f"Failed to fetch user ID for unblock user: {error}")

    @bot.command
    @lightbulb.command("data", "Database tools")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def data(ctx: lightbulb.Context):
        pass

    @data.child()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.command("info", "Show info fetched from API list")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def data_dump(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        await ctx.respond("Scanning database, one moment...")
        current_time = int(time.time())
        display_text = "Database analysis completed\n"

        if database is None:
            await ctx.edit_last_response("Database manager is not available.")
            return

        if hasattr(database, "scan_db"):
            result = database.scan_db()
        else:
            result = database.scanDB()

        for key in result:
            display_text += f"`{result[key]}` {key}\n"
        display_text += f"<t:{current_time}>"
        await ctx.edit_last_response(display_text)

    @data.child()
    @lightbulb.option("export", "Export File to chat", choices=["Yes", "No"], default="No", required=False)
    @lightbulb.option(
        "file_type",
        "Updated from API sources",
        choices=["items", "itemLog", "ingredientLog"],
        required=True,
    )
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.command("update", "Update files")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def data_update_files(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)

        file_type = ctx.options.file_type
        export_file = ctx.options.export

        if file_type == "items":
            await ctx.respond("Updating Item Database...")
            try:
                if item_manager is None:
                    total_items = 0
                else:
                    total_items = item_manager.update_items(str(BOT_PATH / "items.json"))
                if total_items > 0:
                    if export_file == "Yes":
                        await ctx.edit_last_response(
                            content=f"Item data successfully updated, {total_items} items in total.\n`items.json` export complete.",
                            attachment=hikari.files.File(str(BOT_PATH / "items.json")),
                        )
                    else:
                        await ctx.edit_last_response(
                            f"Item data successfully updated, {total_items} items in total."
                        )
                else:
                    await ctx.edit_last_response("No change detected in item data.")
            except Exception as error:
                await ctx.edit_last_response("Failed to update item data")
                print(error)
            return

        if file_type == "itemLog":
            await ctx.respond("Updating Item Changelog...")
            try:
                check_items = _normalize_item_payload(_load_json(BOT_PATH / "items.json", {}))
                base_items = _normalize_item_payload(config.item_map) if config.item_map else check_items
                if changelog_manager is not None:
                    await changelog_manager.generate_item_changelog(base_items, check_items)
                config.item_map = check_items
                if export_file == "Yes":
                    await ctx.edit_last_response(
                        content="Item data successfully updated.\n`item_changelog.json` export complete.",
                        attachment=hikari.files.File(str(BOT_PATH / "changelog" / "item_changelog.json")),
                    )
                else:
                    await ctx.edit_last_response("Itemlog successfully updated.")
            except Exception as error:
                await ctx.edit_last_response("Failed to update item data")
                print(error)
            return

        if file_type == "ingredientLog":
            await ctx.respond("Updating Ingredient Changelog...")
            try:
                check_items = _normalize_item_payload(_load_json(BOT_PATH / "items.json", {}))
                base_items = _normalize_item_payload(config.item_map) if config.item_map else check_items
                if changelog_manager is not None:
                    await changelog_manager.generate_ingredient_changelog(base_items, check_items)
                config.item_map = check_items
                if export_file == "Yes":
                    await ctx.edit_last_response(
                        content="Ingredient data successfully updated.\n`ingredient_changelog` export complete.",
                        attachment=hikari.files.File(str(BOT_PATH / "changelog" / "ingredient_changelog.json")),
                    )
                else:
                    await ctx.edit_last_response("IngredientLog successfully updated.")
            except Exception as error:
                await ctx.edit_last_response("Failed to update item data")
                print(error)

    @data.child()
    @lightbulb.add_checks(_maintainer_check())
    @lightbulb.option("export", "Export File to chat", choices=["Yes", "No"], default="No", required=False)
    @lightbulb.option(
        "file_type",
        "Source File",
        choices=["items", "lootHistory", "lootpool", "aspects", "aspectpool", "gambitpool", "sales", "block"],
        required=True,
    )
    @lightbulb.command("reload", "Reload variables and properties from local files")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def reload(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        export_file = ctx.options.export
        file_type = ctx.options.file_type

        if file_type == "items":
            config.item_map = _normalize_item_payload(_load_json(BOT_PATH / "items.json", {}))
            target_path = BOT_PATH / "items.json"
            content = "Item map data reloaded."
            export_content = "Item data reloaded, export complete."
        elif file_type == "aspects":
            config.aspect_data = _load_json(BOT_PATH / "aspects.json", {})
            target_path = BOT_PATH / "aspects.json"
            content = "Aspect data reloaded."
            export_content = "Aspect data reloaded, export complete."
        elif file_type == "lootHistory":
            config.lootpool_history = _load_json(DATA_PATH / "lootpool_history.json", {})
            target_path = DATA_PATH / "lootpool_history.json"
            content = "Lootpool history data reloaded."
            export_content = "Lootpool History data reloaded, export complete."
        elif file_type == "lootpool":
            config.lootpool_data = _load_json(DATA_PATH / "weekly_lootpool.json", {"Loot": {}}).get("Loot", {})
            target_path = DATA_PATH / "weekly_lootpool.json"
            content = "Lootpool data reloaded."
            export_content = "Lootpool data reloaded, export complete."
        elif file_type == "aspectpool":
            aspect_payload = _load_json(config.WEEKLY_ASPECT_POOL_FILE, {"Loot": {}})
            config.aspect_pool_data = _normalize_raid_loot(aspect_payload.get("Loot", {}), ASPECT_TIERS)
            raid_payload = _load_json(config.WEEKLY_RAID_POOL_FILE, {})
            if isinstance(raid_payload, dict) and raid_payload:
                config.raid_item_pool_data = _normalize_raid_loot(raid_payload.get("Loot", {}), config.RAID_ITEM_TIERS)
                config.raid_item_icon = raid_payload.get("Icon", {}) if isinstance(raid_payload.get("Icon"), dict) else {}
                target_path = config.WEEKLY_RAID_POOL_FILE
            else:
                config.raid_item_pool_data = _normalize_raid_loot(aspect_payload.get("RaidItemLoot", {}), config.RAID_ITEM_TIERS)
                config.raid_item_icon = aspect_payload.get("RaidItemIcon", {}) if isinstance(aspect_payload.get("RaidItemIcon"), dict) else {}
                target_path = config.WEEKLY_ASPECT_POOL_FILE
            content = "Raid lootpool data reloaded."
            export_content = "Raid lootpool data reloaded, export complete."
        elif file_type == "gambitpool":
            cached = _load_json(config.GAMBIT_POOL_FILE, {})
            loot = cached.get("Loot", []) if isinstance(cached, dict) else []
            config.gambit_pool_data = _normalize_gambit_loot_shape(loot)
            normalize_gambit_pool_cache()
            target_path = config.GAMBIT_POOL_FILE
            content = "Gambit Pool data reloaded."
            export_content = "Gambit Pool data reloaded, export complete."
        elif file_type == "sales":
            config.sales_data = _load_json(DATA_PATH / "sales_data.json", {})
            target_path = DATA_PATH / "sales_data.json"
            content = "Sales data reloaded."
            export_content = "Sales data reloaded, export complete."
        else:
            user_list = []
            for blocked_id in _load_json(BOT_PATH / "blocked_users.json", []):
                try:
                    user_list.append(int(blocked_id))
                except (TypeError, ValueError):
                    continue
            config.blocked_users.clear()
            config.blocked_users.extend(user_list)
            if blocked_users is not None and blocked_users is not config.blocked_users:
                blocked_users.clear()
                blocked_users.extend(user_list)
            target_path = BOT_PATH / "blocked_users.json"
            content = "Blocked user reloaded."
            export_content = "Blocked user reloaded, export complete."

        if export_file == "Yes":
            await ctx.respond(
                content=export_content,
                attachment=hikari.files.File(str(target_path)),
                flags=hikari.MessageFlag.LOADING,
            )
        else:
            await ctx.respond(content)

    @data.child()
    @lightbulb.add_checks(_maintainer_check())
    @lightbulb.option("log", "Log generation", required=False, choices=["Yes", "No"], default="Yes")
    @lightbulb.option("items", "Comma-separated item names", required=False, default=None)
    @lightbulb.option("tracker", "Shiny tracker", required=False, default=None)
    @lightbulb.option("shiny", "Shiny mythic", required=False, default=None)
    @lightbulb.option("tier", "Item tier", choices=LOOT_TIERS, required=False)
    @lightbulb.option("area", "Lootrun camp area", choices=LOOTPOOL_REGIONS, required=False)
    @lightbulb.option("action", "Action by user", choices=["Entry", "Clear", "Preview", "Update", "Sync"], required=True)
    @lightbulb.command("loot", "Lootpool Maintenance")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def data_update_lootpool(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        _ensure_lootpool_cache()

        feedback = ""
        log_generation = ctx.options.log
        action = ctx.options.action

        if action == "Entry" and ctx.options.area in LOOTPOOL_REGIONS and ctx.options.tier in LOOT_TIERS:
            region = ctx.options.area
            tier = ctx.options.tier
            if ctx.options.shiny and ctx.options.tracker and tier == "Mythic":
                config.lootpool_data[region]["Shiny"]["Item"] = ctx.options.shiny
                config.lootpool_data[region]["Shiny"]["Tracker"] = ctx.options.tracker
                feedback += f"Shiny {ctx.options.shiny} + {ctx.options.tracker} Tracker\n"
            item_input = _option_value(ctx, "items")
            items = [item.strip() for item in item_input.split(",") if item.strip()] if isinstance(item_input, str) else []
            for item_name in items:
                if item_name not in config.lootpool_data[region][tier]:
                    config.lootpool_data[region][tier].append(item_name)
            feedback += f"{config.lootpool_data[region][tier]}"
            feedback_embed = hikari.Embed(
                title=f"{region} Lootpool Entry",
                description=f"Submitted by {ctx.user}",
                color="#83FFDB",
            )
            feedback_embed.add_field(f"{tier} Items", feedback if feedback else "No changes applied.")
            feedback_embed.set_footer("Nori Bot - Maintainer Tools")
            await ctx.respond(feedback_embed)
            return

        if action == "Clear" and ctx.options.area and ctx.options.tier:
            region = ctx.options.area
            tier = ctx.options.tier
            clear_count = len(config.lootpool_data[region][tier])
            config.lootpool_data[region][tier].clear()
            feedback_embed = hikari.Embed(
                title=f"Cleared {tier} items in {region} Lootpool",
                description=f"Requested by {ctx.user}",
                color="#83FFDB",
            )
            feedback_embed.add_field("Process Completed", f"Removed {clear_count} Items")
            feedback_embed.set_footer("Nori Bot - Maintainer Tools")
            await ctx.respond(feedback_embed)
            return

        if action == "Sync":
            try:
                sync_status = await _sync_item_lootpool()
                sync_embed = hikari.Embed(
                    title="Lootpool Sync Complete",
                    description="Lootpool data has been synchronized from Wynn Source API.",
                    color="#83FFDB",
                )
                sync_embed.set_footer("Nori Bot - Maintainer Tools")
                sync_embed.add_field("Result", f"Cached regions updated: {sync_status.get('regions', 0)}")
                sync_embed.add_field("Source", str(sync_status.get("source", "unknown")))
                sync_embed.add_field(
                    "Next",
                    "Preview pool with `/data loot Preview`, Run `/data loot Update` to generate lootpool data.",
                )
                await ctx.respond(embed=sync_embed)
            except Exception as error:
                error_embed = hikari.Embed(
                    title="Sync Error",
                    description=f"Failed to sync lootpool data: {error}",
                    color="#FF0000",
                )
                await ctx.respond(embed=error_embed)
            return

        if action == "Update":
            current_date = datetime.now().strftime("%Y-%m-%d")
            now_ts = int(time.time())
            week_number = await _estimate_week_number()
            notice_embed = hikari.Embed(
                title="Weekly Lootpool Maintenance",
                description=f"Week #{week_number} Date: {current_date}",
                color="#83FFDB",
            )
            await ctx.respond(embed=notice_embed)

            log_file = DATA_PATH / "lootpool_history.log"
            log_content = ""
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as log:
                    log_content = log.read()
            should_log = current_date not in log_content

            try:
                icon_data = await _lootpool_post_process()
                config.lootpool_icon = icon_data["icons"]
                warning_list = icon_data["warning"]
            except Exception as error:
                await ctx.respond(f"Error fetching icons for lootpool items: {error}")
                warning_list = []

            if warning_list:
                warning = ", ".join(warning_list)
                notice_embed.add_field("Status", f"Item icons generated complete.\nFailed to process: {warning}")

            try:
                weekly_lootpool = await _create_weekly_lootpool()
                await _update_lootpool(weekly_lootpool)
                report_line = f"Lootpool data generated at <t:{now_ts}:T>\nLog generation: False"
                if log_generation == "Yes":
                    await _history_log(weekly_lootpool, update=should_log, date_string=current_date)
                    await _convert_lootpool_to_json()
                    report_line = (
                        f"Data and log generated at <t:{now_ts}:T>\nLog generation: True (Default)"
                    )
                notice_embed.add_field(f"Update Confirmed by {ctx.user}", report_line)
                config.lootpool_data = _load_json(DATA_PATH / "lootpool_default.json", {"Loot": {}}).get("Loot", {})
                print("Lootpool update complete, cached data cleared.")
            except Exception as error:
                print(f"Lootpool update failed: {error}")
                notice_embed.add_field("Update Error", f"{type(error).__name__}: {error}")
                notice_embed.color = "#FF0000"

            notice_embed.set_footer("Nori Bot - Maintainer Tools")
            await ctx.edit_last_response(embed=notice_embed)
            return

        if action == "Preview":
            preview_embed = hikari.Embed(
                title="Lootpool Preview",
                description=f"Requested by {ctx.user}",
                color="#83FFDB",
            )
            for region in LOOTPOOL_REGIONS:
                region_preview = _summarize_lootpool_region_preview(config.lootpool_data.get(region, {}), sample_size=2)
                preview_embed.add_field(region, region_preview)
            preview_embed.add_field(
                "Preview Notes",
                "Tier counts and small samples shown. Icon validation is skipped for a faster preview.",
            )
            preview_embed.set_footer("Nori Bot - Maintainer Tools")
            await ctx.respond(preview_embed)

    @data.child()
    @lightbulb.add_checks(_maintainer_check())
    @lightbulb.option("aspects", "Comma-separated aspect names", required=False, default=None)
    @lightbulb.option("tier", "Aspect tier", choices=ASPECT_TIERS, required=False)
    @lightbulb.option("raid", "Raid Name", choices=RAID_NAMES, required=False)
    @lightbulb.option("action", "Action by user", choices=["Entry", "Clear", "Preview", "Update", "Sync"], required=True)
    @lightbulb.command("aspect", "Aspect pool Maintenance")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def data_update_aspects(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        _ensure_aspect_cache()
        _ensure_raid_item_cache()
        feedback = ""
        action = ctx.options.action

        if action == "Entry" and ctx.options.raid in RAID_NAMES and ctx.options.tier in ASPECT_TIERS:
            raid = ctx.options.raid
            aspects = [aspect.strip() for aspect in ctx.options.aspects.split(",") if aspect.strip()] if ctx.options.aspects else []
            for aspect_name in aspects:
                if aspect_name not in config.aspect_pool_data[raid][ctx.options.tier]:
                    config.aspect_pool_data[raid][ctx.options.tier].append(aspect_name)
            feedback += f"{config.aspect_pool_data[raid][ctx.options.tier]}"
            feedback_embed = hikari.Embed(
                title=f"{raid} Aspects Entry",
                description=f"Submitted by {ctx.user}",
                color="#c0aaff",
            )
            feedback_embed.add_field(f"{ctx.options.tier} Aspects", feedback)
            feedback_embed.set_footer("Nori Bot - Maintainer Tools")
            await ctx.respond(feedback_embed)
            return

        if action == "Clear" and ctx.options.raid and ctx.options.tier:
            raid = ctx.options.raid
            tier = ctx.options.tier
            clear_count = len(config.aspect_pool_data[raid][tier])
            config.aspect_pool_data[raid][tier].clear()
            feedback_embed = hikari.Embed(
                title=f"Cleared {tier} aspects in {raid} aspect pool",
                description=f"Requested by {ctx.user}",
                color="#c0aaff",
            )
            feedback_embed.add_field("Process Completed", f"Removed {clear_count} Aspects")
            feedback_embed.set_footer("Nori Bot - Maintainer Tools")
            await ctx.respond(feedback_embed)
            return

        if action == "Sync":
            try:
                sync_status = await _sync_aspect_lootpool()
                from lib.tasks.raid_pool import _sync_raid_item_lootpool
                raid_item_status = await _sync_raid_item_lootpool()
                sync_embed = hikari.Embed(
                    title="Aspect Sync Complete",
                    description="Raid aspect and raid item data have been synchronized from Wynn Source API.",
                    color="#c0aaff",
                )
                sync_embed.set_footer("Nori Bot - Maintainer Tools")
                sync_embed.add_field("Result", f"Cached raids updated: {sync_status.get('raids', 0)}")
                sync_embed.add_field("Raid Item Result", f"Cached raids updated: {raid_item_status.get('items', 0)}")
                sync_embed.add_field("Aspect Source", str(sync_status.get("source", "unknown")))
                sync_embed.add_field("Raid Item Source", str(raid_item_status.get("source", "unknown")))
                sync_embed.add_field(
                    "Next",
                    "Use Preview to verify inputs, then use Update to publish weekly raid data.",
                )
                await ctx.respond(embed=sync_embed)
            except Exception as error:
                error_embed = hikari.Embed(
                    title="Sync Error",
                    description=f"Failed to sync aspect data: {error}",
                    color="#FF0000",
                )
                await ctx.respond(embed=error_embed)
            return

        if action == "Update":
            from lib.tasks.raid_pool import _create_weekly_raid_pool, _raid_item_post_process, _update_weekly_raid_pool

            current_date = datetime.now().strftime("%Y-%m-%d")
            now_ts = int(time.time())
            week_number = await _aspect_week_number()
            notice_embed = hikari.Embed(
                title="Weekly Raid Maintenance",
                description=f"Week #{week_number} Date: {current_date}",
                color="#c0aaff",
            )
            await ctx.respond(embed=notice_embed)

            try:
                icon_data = await _aspect_post_process()
                config.aspect_icon = icon_data["icons"]
                aspect_warning_list = icon_data["warning"]
            except Exception as error:
                notice_embed.add_field("Icon Fetch Error", f"{type(error).__name__}: {error}")
                aspect_warning_list = []

            try:
                raid_item_icon_data = await _raid_item_post_process()
                config.raid_item_icon = raid_item_icon_data["icons"]
                raid_item_warning_list = raid_item_icon_data["warning"]
            except Exception as error:
                notice_embed.add_field("Raid Item Icon Fetch Error", f"{type(error).__name__}: {error}")
                raid_item_warning_list = []

            if aspect_warning_list:
                warning = ", ".join(aspect_warning_list)
                notice_embed.add_field("Aspect Icon Status", f"Failed to process: {warning}")
            if raid_item_warning_list:
                warning = ", ".join(raid_item_warning_list)
                notice_embed.add_field("Raid Item Icon Status", f"Failed to process: {warning}")

            weekly_aspects = await _create_weekly_aspects()
            await _update_aspect_pool(weekly_aspects)
            weekly_raid_pool = await _create_weekly_raid_pool(weekly_aspects)
            await _update_weekly_raid_pool(weekly_raid_pool)
            report_line = f"Aspect + raid pool data generated at <t:{now_ts}:T>"
            notice_embed.add_field(f"Update Confirmed by {ctx.user}", report_line)
            notice_embed.set_footer("Nori Bot - Maintainer Tools")
            await ctx.edit_last_response(embed=notice_embed)

            config.aspect_pool_data = _normalize_raid_loot(
                _load_json(config.ASPECT_POOL_DEFAULT_FILE, {"Loot": {}}).get("Loot", {}),
                ASPECT_TIERS,
            )
            config.raid_item_pool_data = _normalize_raid_loot(
                _load_json(config.RAID_ITEM_POOL_DEFAULT_FILE, {"Loot": {}}).get("Loot", {}),
                config.RAID_ITEM_TIERS,
            )
            print("Raid lootpool update complete, cached data cleared.")
            return

        if action == "Preview":
            preview_embed = hikari.Embed(
                title="Raid Lootpool Preview",
                description=f"Requested by {ctx.user}",
                color="#c0aaff",
            )
            for raid in RAID_NAMES:
                aspect_preview = _summarize_pool_tiers(config.aspect_pool_data.get(raid, {}), ASPECT_TIERS)
                item_preview = _summarize_pool_tiers(config.raid_item_pool_data.get(raid, {}), config.RAID_ITEM_TIERS)
                preview_embed.add_field(f"{raid} Aspect Loot", aspect_preview)
                preview_embed.add_field(f"{raid} Item Loot", item_preview)
            preview_embed.add_field(
                "Preview Notes",
                "Tier counts and small samples shown. Icon validation is skipped for a faster preview.",
            )
            preview_embed.set_footer("Nori Bot - Maintainer Tools")
            await ctx.respond(preview_embed)

    @data.child()
    @lightbulb.add_checks(_maintainer_check())
    @lightbulb.command("gambit", "Manually refresh gambit data from Wynn Source")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def data_refresh_gambits(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        await ctx.respond("Refreshing gambits from Wynn Source...", flags=hikari.MessageFlag.LOADING)
        result = await refresh_gambits()

        if "error" in result:
            error_embed = hikari.Embed(
                title="Gambit Refresh Failed",
                description="Could not refresh gambit data from Wynn Source API.",
                color="#FF0000",
            )
            error_embed.add_field("Error Detail", str(result["error"]))
            error_embed.set_footer("Nori Bot - Maintainer Tools")
            await ctx.edit_last_response(embed=error_embed, content="")
            return

        embed = hikari.Embed(
            title="Gambit Refresh Complete",
            description="Gambit pool pulled from WynnSource and written to disk.",
            color="#c0aaff",
        )
        embed.add_field("Gambits Updated", str(result.get("gambits", 0)))
        rotation_start = result.get("rotation_start")
        rotation_end = result.get("rotation_end")
        if rotation_start:
            embed.add_field("Rotation Start", f"<t:{rotation_start}:F>")
        if rotation_end:
            embed.add_field("Rotation End", f"<t:{rotation_end}:F>")
        next_interval = current_gambit_refresh_interval(now_ts=int(time.time()))
        embed.add_field("Next Auto-Refresh", f"In {max(1, next_interval // 60)} minutes")

        shared_lines = []
        for entry in config.gambit_pool_data[:5]:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name", "?")
            description = entry.get("description") or ""
            shared_lines.append(f"- **{name}**")
            if description:
                shared_lines.append(f"  {description}")
        if shared_lines:
            embed.add_field("Preview", "\n".join(shared_lines)[:1024])

        embed.set_footer("Nori Bot - Maintainer Tools")
        await ctx.edit_last_response(embed=embed, content="")

    @data.child()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.option("type", "Category of file", choices=["player", "other"])
    @lightbulb.command("progress", "Show current progress")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def data_current_progress(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        await ctx.respond("Loading database")

        if "player" in ctx.options.type:
            leaderboard_path = DATA_SCRIPTS_DATABASE_PATH / "player_leaderboard.json"
            if not leaderboard_path.exists():
                await ctx.edit_last_response("Required player leaderboard file is missing.")
                return
            with open(leaderboard_path, "r", encoding="utf-8") as file:
                leaderboard_meta = json.load(file)
                timestamp = leaderboard_meta.get("timestamp", int(time.time()))
                player_count = leaderboard_meta.get("player_count")

            if player_count is None:
                await ctx.edit_last_response(
                    "Player count unavailable until the next leaderboard rebuild\n"
                    f"Leaderboard data updated <t:{timestamp}:R>"
                )
            else:
                await ctx.edit_last_response(
                    f"Total of `{player_count}` players stored in local database\n"
                    f"Leaderboard data updated <t:{timestamp}:R>"
                )
        elif "item" in ctx.options.type:
            await ctx.edit_last_response("Work in progress")
        else:
            await ctx.edit_last_response("Invalid type")

    @data.child()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.option(
        "type",
        "Category of file",
        choices=["item", "itemChangelog", "ingredientLog", "build", "recipe", "uptime", "onlineRecord", "weight", "lootHistory", "sales", "mapping"],
    )
    @lightbulb.command("export", "Get files")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def data_get_file(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        await ctx.respond(f"File type: `{ctx.options.type}`")

        file_map = {
            "item": BOT_PATH / "items.json",
            "itemChangelog": BOT_PATH / "changelog" / "item_changelog.json",
            "ingredientLog": BOT_PATH / "changelog" / "ingredient_changelog.json",
            "build": DATA_PATH / "build_db.json",
            "recipe": DATA_PATH / "recipe_db.json",
            "uptime": DATA_SCRIPTS_DATABASE_PATH / "server_uptime.json",
            "onlineRecord": DATA_SCRIPTS_DATABASE_PATH / "online_activity.json",
            "weight": DATA_PATH / "mythic_weights.json",
            "lootHistory": DATA_PATH / "lootpool_history.json",
            "sales": DATA_PATH / "sales_data.json",
            "mapping": BOT_PATH / "stat_mapping.json",
        }
        target_file = file_map.get(ctx.options.type)
        if not target_file or not target_file.exists():
            await ctx.respond("Requested file is not available.")
            return
        await ctx.respond(attachment=hikari.files.File(str(target_file)))

    @data.child()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.command("api", "Show today's API endpoint usage (owner only)")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def data_api_usage(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        source_label = "Nori API"
        try:
            data = await _fetch_api_usage_from_nori()
        except Exception as error:
            await ctx.respond(f"Failed to fetch API usage: {error}")
            return

        date_str = data.get("date", "unknown")
        updated_at = data.get("updated_at")
        endpoints = data.get("endpoints", {})

        total = sum(v.get("count", 0) for v in endpoints.values())
        sorted_eps = sorted(endpoints.items(), key=lambda x: x[1].get("count", 0), reverse=True)
        active = [(k, v) for k, v in sorted_eps if v.get("count", 0) > 0]
        zero_count = sum(1 for _, v in sorted_eps if v.get("count", 0) == 0)

        ts = f"<t:{updated_at}:t>" if updated_at else "unknown"
        summary_lines = [
            f"Date: **{date_str}** | Updated: {ts}",
            f"Total requests today: **{total:,}**",
        ]
        if not active:
            summary_lines.append("No traffic recorded yet today.")
        if zero_count:
            summary_lines.append(f"**{zero_count}** endpoints with no traffic today")

        embed = hikari.Embed(
            title="API Usage Today",
            description="\n".join(summary_lines),
            color="#5078FF",
        )
        embed.add_field("Source", source_label, inline=True)

        # Show up to 20 active endpoints in fields (Discord limit: 25 fields)
        shown = active[:20]
        if shown:
            max_path_len = max(len(k) for k, _ in shown)
            lines = []
            for path, info in shown:
                count = info.get("count", 0)
                lines.append(f"`{path:<{max_path_len}}` {count:>6,}")
            # Split into chunks ≤1024 chars each (Discord field value limit)
            chunk, chunks = [], []
            for line in lines:
                if sum(len(l) + 1 for l in chunk) + len(line) > 1000:
                    chunks.append(chunk)
                    chunk = []
                chunk.append(line)
            if chunk:
                chunks.append(chunk)
            for i, chunk in enumerate(chunks):
                field_name = "Endpoints by Traffic" if i == 0 else "\u200b"
                embed.add_field(field_name, "\n".join(chunk))

        if len(active) > 20:
            embed.add_field("\u200b", f"... and {len(active) - 20} more active endpoints")

        embed.set_footer("Nori Bot - resets daily at midnight")
        await ctx.respond(embed=embed)

    @data.child()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.command("memory", "Generate memory usage report (RawFish only)")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def memory_report(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        if not tracemalloc.is_tracing():
            tracemalloc.start()

        def _format_size(size: float) -> str:
            for unit in ["B", "KiB", "MiB", "GiB"]:
                if size < 1024.0:
                    return f"{size:.2f} {unit}"
                size /= 1024.0
            return f"{size:.2f} GiB"

        await ctx.respond("Generating memory report...")

        current, peak = tracemalloc.get_traced_memory()
        rss_text = "Unavailable"
        try:
            import resource

            rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            rss_bytes = rss_kib * 1024 if os.name != "darwin" else rss_kib
            rss_text = _format_size(float(rss_bytes))
        except Exception:
            pass

        uptime = get_uptime(config.deploy_time)
        deploy_ts = int(config.deploy_time) if config.deploy_time else None
        uptime_text = uptime
        if deploy_ts:
            uptime_text += f"\nStarted <t:{deploy_ts}:R>"
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")
        function_stats = snapshot.statistics("traceback")

        now = datetime.now()
        date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        unix_time_str = str(int(now.timestamp()))
        report_lines = [
            "Memory Usage Report",
            f"Generated on: {date_time_str}",
            f"Unix Timestamp: {unix_time_str}",
            f"Uptime: {uptime}",
            f"Current RSS: {rss_text}",
            f"Python Allocated: {_format_size(float(current))}",
            f"Python Peak: {_format_size(float(peak))}",
            "",
            "Top Memory Consumers by Line of Code:",
        ]

        for index, stat in enumerate(top_stats[:10], start=1):
            size = _format_size(float(stat.size))
            location = "\n".join(stat.traceback.format())
            report_lines.append(f"{index}. {size}, {stat.count} objects, {location}")

        report_lines.append("\nTop Memory Consumers by Function Calls:")
        for index, stat in enumerate(function_stats[:10], start=1):
            size = _format_size(float(stat.size))
            function_name = stat.traceback[-1]
            report_lines.append(f"{index}. {size}, {stat.count} objects, {function_name}")

        report = "\n".join(report_lines)
        report_path = config.LOG_PATH / "memory_report.txt"
        summary = (
            "**Memory Usage**\n"
            f"Current RSS: `{rss_text}`\n"
            f"Python Allocated: `{_format_size(float(current))}`\n"
            f"Python Peak: `{_format_size(float(peak))}`\n"
            f"Uptime: `{uptime}`"
        )
        if deploy_ts:
            summary += f"\nStarted <t:{deploy_ts}:R>"
        try:
            with open(report_path, "w", encoding="utf-8") as file:
                file.write(report)
            await ctx.edit_last_response(
                content=f"{summary}\n\nReport generated.",
                attachment=hikari.files.File(str(report_path)),
            )
        except Exception as error:
            await ctx.edit_last_response(content=f"{summary}\n\nError generating memory report: {str(error)}")
