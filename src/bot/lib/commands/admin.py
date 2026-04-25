"""Admin and data maintenance command groups."""

import json
import time
import tracemalloc
from datetime import datetime

import hikari
import lightbulb

import lib.config as config
from lib.config import (
    BOT_PATH,
    DATA_PATH,
    LOG_PATH,
    DATA_SCRIPTS_DATABASE_PATH,
    LOOTPOOL_REGIONS,
    RAID_NAMES,
    LOOT_TIERS,
    ASPECT_TIERS,
    WYNN_SOURCE_TOKEN,
    SITE_DATA_PATH,
)
from lib.utils import check_user_access
from lib.wynnsource_pool import (
    clean_item_name,
    fetch_pool_legacy_with_failover,
    format_attempt_log,
    is_ward_item,
)
from lib.manager_registry import get_managers


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


def _ensure_lootpool_cache():
    if not config.lootpool_data:
        data = _load_json(DATA_PATH / "lootpool_default.json", {"Loot": {}})
        config.lootpool_data = data.get("Loot", {})


def _ensure_aspect_cache():
    if not config.aspect_pool_data:
        data = _load_json(DATA_PATH / "default_aspect_pool.json", {"Loot": {}})
        config.aspect_pool_data = data.get("Loot", {})


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

    result = fetch_pool_legacy_with_failover(
        pool,
        token,
        primary_base_url=config.WCS_POOL_PRIMARY_BASE_URL,
        beta_base_url=config.WCS_POOL_BETA_BASE_URL,
        v1_base_url=config.WCS_POOL_V1_BASE_URL,
        timeout=config.WCS_POOL_TIMEOUT,
        allow_missing_regions=config.WCS_POOL_ALLOW_MISSING_REGIONS,
        enable_v1_fallback=config.WCS_POOL_ENABLE_V1_FALLBACK,
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

    for region, region_data in loot.items():
        out = {
            "Shiny": {"Item": "N/A", "Tracker": "N/A"},
            "Mythic": [],
            "Fabled": [],
            "Legendary": [],
            "Rare": [],
            "Unique": [],
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
            for rarity in LOOT_TIERS:
                if rarity in items:
                    for raw_name in items[rarity]:
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
        config.aspect_pool_data = defaults.get("Loot", {})
        print(
            "Aspect sync fallback to defaults. "
            f"{fetch_result['error']} Attempts: {format_attempt_log(attempts)}"
        )
        return {"raids": len(config.aspect_pool_data), "source": "defaults"}

    payload = fetch_result["payload"]
    config.aspect_pool_data = _convert_aspect_loot_format(payload)["Loot"]
    print(f"Aspect sync source={fetch_result.get('source')} Attempts: {format_attempt_log(attempts)}")
    return {"raids": len(config.aspect_pool_data), "source": fetch_result.get("source", "unknown")}


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
    tiers = {"Mythic", "Fabled", "Legendary", "Rare", "Unique"}
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
        try:
            user = await bot.rest.fetch_user(user_id)
            user_list.append(user_id)
            _write_json(BOT_PATH / "blocked_users.json", user_list)
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
        try:
            user = await bot.rest.fetch_user(user_id)
            user_list.remove(user_id)
            _write_json(BOT_PATH / "blocked_users.json", user_list)
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
                check_items = _load_json(BOT_PATH / "items.json", {})
                base_items = config.item_map if config.item_map else check_items
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
                check_items = _load_json(BOT_PATH / "items.json", {})
                base_items = config.item_map if config.item_map else check_items
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
        choices=["items", "lootHistory", "lootpool", "aspects", "aspectpool", "sales", "block"],
        required=True,
    )
    @lightbulb.command("reload", "Reload variables and properties from local files")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def reload(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        export_file = ctx.options.export
        file_type = ctx.options.file_type

        if file_type == "items":
            config.item_map = _load_json(BOT_PATH / "items.json", {})
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
            config.aspect_pool_data = _load_json(DATA_PATH / "weekly_aspects.json", {"Loot": {}}).get("Loot", {})
            target_path = DATA_PATH / "weekly_aspects.json"
            content = "Aspect Lootpool data reloaded."
            export_content = "Aspect Lootpool data reloaded, export complete."
        elif file_type == "sales":
            config.sales_data = _load_json(DATA_PATH / "sales_data.json", {})
            target_path = DATA_PATH / "sales_data.json"
            content = "Sales data reloaded."
            export_content = "Sales data reloaded, export complete."
        else:
            user_list = _load_json(BOT_PATH / "blocked_users.json", [])
            config.blocked_users = user_list
            if blocked_users is not None:
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

        if action == "Entry" and ctx.options.area in LOOTPOOL_REGIONS:
            region = ctx.options.area
            if ctx.options.shiny and ctx.options.tracker and ctx.options.tier == "Mythic":
                config.lootpool_data[region]["Shiny"]["Item"] = ctx.options.shiny
                config.lootpool_data[region]["Shiny"]["Tracker"] = ctx.options.tracker
                feedback += f"Shiny {ctx.options.shiny} + {ctx.options.tracker} Tracker\n"
            items = [item.strip() for item in ctx.options.items.split(",") if item.strip()] if ctx.options.items else []
            for item_name in items:
                config.lootpool_data[region][ctx.options.tier].append(item_name)
            feedback += f"{config.lootpool_data[region][ctx.options.tier]}"
            feedback_embed = hikari.Embed(
                title=f"{region} Lootpool Entry",
                description=f"Submitted by {ctx.user}",
                color="#83FFDB",
            )
            feedback_embed.add_field(f"{ctx.options.tier} Items", feedback)
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
                preview_embed.add_field(region, config.lootpool_data[region])

            try:
                icon_data = await _lootpool_post_process()
                warning_list = icon_data["warning"]
            except Exception as error:
                await ctx.respond(f"Error fetching icons for lootpool items: {error}")
                warning_list = []

            if warning_list:
                warning = ", ".join(warning_list)
                preview_embed.add_field("Check Item Inputs", f"Failed to process: {warning}")
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
        feedback = ""
        action = ctx.options.action

        if action == "Entry" and ctx.options.raid in RAID_NAMES:
            raid = ctx.options.raid
            aspects = [aspect.strip() for aspect in ctx.options.aspects.split(",") if aspect.strip()] if ctx.options.aspects else []
            for aspect_name in aspects:
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
                sync_embed = hikari.Embed(
                    title="Aspect Sync Complete",
                    description="Aspect data has been synchronized from Wynn Source API.",
                    color="#c0aaff",
                )
                sync_embed.set_footer("Nori Bot - Maintainer Tools")
                sync_embed.add_field("Result", f"Cached raids updated: {sync_status.get('raids', 0)}")
                sync_embed.add_field("Source", str(sync_status.get("source", "unknown")))
                sync_embed.add_field(
                    "Next",
                    "Preview pool with `/data aspect Preview`, Run `/data aspect Update` to generate aspect pool data.",
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
            current_date = datetime.now().strftime("%Y-%m-%d")
            now_ts = int(time.time())
            week_number = await _aspect_week_number()
            notice_embed = hikari.Embed(
                title="Weekly Aspect Maintenance",
                description=f"Week #{week_number} Date: {current_date}",
                color="#c0aaff",
            )
            await ctx.respond(embed=notice_embed)

            try:
                icon_data = await _aspect_post_process()
                config.aspect_icon = icon_data["icons"]
                warning_list = icon_data["warning"]
            except Exception as error:
                await ctx.respond(f"Error fetching icon for aspects: {error}")
                warning_list = []

            if warning_list:
                warning = ", ".join(warning_list)
                notice_embed.add_field("Status", f"Aspect icons fetched complete.\nFailed to process: {warning}")

            weekly_aspects = await _create_weekly_aspects()
            await _update_aspect_pool(weekly_aspects)
            report_line = f"Aspect pool data generated at <t:{now_ts}:T>"
            notice_embed.add_field(f"Update Confirmed by {ctx.user}", report_line)
            notice_embed.set_footer("Nori Bot - Maintainer Tools")
            await ctx.edit_last_response(embed=notice_embed)

            config.aspect_pool_data = _load_json(DATA_PATH / "default_aspect_pool.json", {"Loot": {}}).get("Loot", {})
            print("Aspect lootpool update complete, cached data cleared.")
            return

        if action == "Preview":
            preview_embed = hikari.Embed(
                title="Aspects Lootpool Preview",
                description=f"Requested by {ctx.user}",
                color="#c0aaff",
            )
            for raid in RAID_NAMES:
                preview_embed.add_field(raid, config.aspect_pool_data[raid])

            try:
                icon_data = await _aspect_post_process()
                warning_list = icon_data["warning"]
            except Exception as error:
                await ctx.respond(f"Error fetching icon for aspects: {error}")
                warning_list = []

            if warning_list:
                warning = ", ".join(warning_list)
                preview_embed.add_field("Check Aspect Inputs", f"Failed to process: {warning}")
            preview_embed.set_footer("Nori Bot - Maintainer Tools")
            await ctx.respond(preview_embed)

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
        api_usage_path = SITE_DATA_PATH / "api_usage_today.json"
        try:
            with open(api_usage_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            await ctx.respond("No API usage data found yet. The file is created on the first request after deploy.")
            return
        except Exception as error:
            await ctx.respond(f"Failed to read API usage file: {error}")
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
            embed.add_field("\u200b", f"… and {len(active) - 20} more active endpoints")

        embed.set_footer("Nori Bot — resets daily at midnight")
        await ctx.respond(embed=embed)

    @data.child()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.command("memory", "Generate memory usage report (RawFish only)")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def memory_report(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        await ctx.respond("Generating memory report...")

        tracemalloc.start()
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")
        function_stats = snapshot.statistics("traceback")

        def _format_size(size):
            for unit in ["B", "KiB", "MiB", "GiB"]:
                if size < 1024.0:
                    return f"{size:.2f} {unit}"
                size /= 1024.0
            return f"{size:.2f} GiB"

        now = datetime.now()
        date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        unix_time_str = str(int(now.timestamp()))
        report_lines = [
            "Memory Usage Report",
            f"Generated on: {date_time_str}",
            f"Unix Timestamp: {unix_time_str}",
            "",
            "Top Memory Consumers by Line of Code:",
        ]

        for index, stat in enumerate(top_stats[:10], start=1):
            size = _format_size(stat.size)
            location = "\n".join(stat.traceback.format())
            report_lines.append(f"{index}. {size}, {stat.count} objects, {location}")

        report_lines.append("\nTop Memory Consumers by Function Calls:")
        for index, stat in enumerate(function_stats[:10], start=1):
            size = _format_size(stat.size)
            function_name = stat.traceback[-1]
            report_lines.append(f"{index}. {size}, {stat.count} objects, {function_name}")

        report = "\n".join(report_lines)
        report_path = LOG_PATH / "memory_report.txt"
        try:
            with open(report_path, "w", encoding="utf-8") as file:
                file.write(report)
            await ctx.edit_last_response(content="Report generated", attachment=hikari.files.File(str(report_path)))
        except Exception as error:
            await ctx.edit_last_response(content=f"Error generating memory report: {str(error)}")
