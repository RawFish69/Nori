"""Startup and initialization for production."""

import json
import asyncio
import lightbulb
from datetime import datetime, timezone, timedelta

from lib.config import (
    BOT_PATH,
    DATA_PATH,
    LOG_CHANNEL_ID,
)
from lib.leaderboard_cache import load_leaderboard_in_guild
from lib.item_db_compat import items_response_to_dict, looks_like_item_database
from lib.manager_registry import get_managers
from lib.raid_pool_utils import (
    _normalize_gambit_loot_shape,
    load_aspect_lootpool,
    load_gambit_pool,
    load_weekly_raid_pool,
)
from lib.tasks.gambit import gambit_refresh_task
from lib.tasks.item_db import item_db_refresh_task
from lib.tasks.lootpool import lootpool_refresh_task
from lib.tasks.raid_pool import raid_pool_refresh_task


def _load_item_map_from_disk():
    with open(BOT_PATH / "items.json", "r", encoding="utf-8") as file:
        loaded_items, summary = items_response_to_dict(json.load(file))
    if not looks_like_item_database(loaded_items):
        raise ValueError("items.json is not a valid item database")
    return loaded_items, summary


async def load_startup_data(bot: lightbulb.BotApp):
    """Load all data files on bot startup."""
    import lib.config as config
    
    try:
        with open(DATA_PATH / "lootpool_default.json", "r") as file:
            config.lootpool_data = json.load(file)["Loot"]
    except Exception as e:
        print(f"Error loading lootpool_default.json: {e}")
        config.lootpool_data = {}
    
    try:
        with open(DATA_PATH / "lootpool_history.json", "r") as file:
            config.lootpool_history = json.load(file)
    except Exception as e:
        print(f"Error loading lootpool_history.json: {e}")
        config.lootpool_history = {}
    
    try:
        aspect_pool = await load_aspect_lootpool()
        config.aspect_pool_data = aspect_pool.get("Loot", {})
        config.aspect_icon = aspect_pool.get("Icon", {})
    except Exception as e:
        print(f"Error loading weekly_aspects.json: {e}")
        config.aspect_pool_data = {}
        config.aspect_icon = {}

    try:
        raid_pool = await load_weekly_raid_pool()
        config.raid_item_pool_data = raid_pool.get("Loot", {})
        config.raid_item_icon = raid_pool.get("Icon", {})
    except Exception as e:
        print(f"Error loading weekly_raid_pool.json: {e}")
        config.raid_item_pool_data = {}
        config.raid_item_icon = {}

    try:
        gambit_pool = await load_gambit_pool()
        config.gambit_pool_data = _normalize_gambit_loot_shape(gambit_pool.get("Loot", []))
    except Exception as e:
        print(f"Error loading daily_gambits.json: {e}")
        config.gambit_pool_data = []
    
    try:
        with open(DATA_PATH / "sales_data.json", "r") as file:
            config.sales_data = json.load(file)
    except Exception as e:
        print(f"Error loading sales_data.json: {e}")
        config.sales_data = {}
    
    try:
        with open(BOT_PATH / "id_map.json", "r") as file:
            id_map = json.load(file)
    except Exception as e:
        print(f"Error loading id_map.json: {e}")
        id_map = {}
    
    try:
        with open(BOT_PATH / "shiny_stats.json", "r") as file:
            shiny_map = json.load(file)
    except Exception as e:
        print(f"Error loading shiny_stats.json: {e}")
        shiny_map = {}
    
    try:
        loaded_items, summary = _load_item_map_from_disk()
        config.item_map = loaded_items
        if summary is not None:
            print(
                f"Loaded v3.7 item list: {summary['total']} keys, "
                f"{len(summary['collisions'])} displayName collisions"
            )
    except Exception as e:
        print(f"Error loading items.json: {e}")
        config.item_map = {}
        item_manager = get_managers().get("item_manager")
        if item_manager is not None:
            try:
                updated_count = await asyncio.to_thread(item_manager.update_items, str(BOT_PATH / "items.json"))
                if updated_count > 0:
                    loaded_items, summary = _load_item_map_from_disk()
                    config.item_map = loaded_items
                    print(f"Recovered items.json during startup with {len(config.item_map)} items.")
                    if summary is not None:
                        print(
                            f"Recovered v3.7 item list: {summary['total']} keys, "
                            f"{len(summary['collisions'])} displayName collisions"
                        )
            except Exception as recover_error:
                print(f"Error recovering items.json: {recover_error}")
    
    try:
        with open(BOT_PATH / "stat_mapping.json", "r") as file:
            config.stat_mapping = json.load(file)
    except Exception as e:
        print(f"Error loading stat_mapping.json: {e}")
        config.stat_mapping = {}
    
    config.lb_in_guild = load_leaderboard_in_guild()
    
    try:
        with open(BOT_PATH / "blocked_users.json", "r") as file:
            loaded_blocked = json.load(file)
            loaded_blocked = [int(user_id) for user_id in loaded_blocked]
            config.blocked_users.clear()
            config.blocked_users.extend(loaded_blocked)
    except Exception as e:
        print(f"Error loading blocked_users.json: {e}")
        config.blocked_users.clear()
    
    print("Data initial load complete.")
    if not getattr(config, "gambit_refresh_started", False):
        config.gambit_refresh_started = True
        asyncio.create_task(gambit_refresh_task())
    if not getattr(config, "item_db_refresh_started", False):
        config.item_db_refresh_started = True
        asyncio.create_task(item_db_refresh_task(bot))
    if not getattr(config, "lootpool_refresh_started", False):
        config.lootpool_refresh_started = True
        asyncio.create_task(lootpool_refresh_task())
    if not getattr(config, "raid_pool_refresh_started", False):
        config.raid_pool_refresh_started = True
        asyncio.create_task(raid_pool_refresh_task())
    
    # Send startup notification if channel ID is configured
    if LOG_CHANNEL_ID:
        try:
            CST = timezone(timedelta(hours=-5))
            time_now = datetime.now(CST)
            current_datetime = time_now.strftime("%Y-%m-%d %H:%M:%S")
            import time
            deploy_time = time.time()
            await bot.rest.create_message(
                channel=int(LOG_CHANNEL_ID),
                content=f"Bot restarted at **{current_datetime}** CST\nAround <t:{int(deploy_time)}:R>"
            )
        except Exception as e:
            print(f"Error sending startup notification: {e}")
    
