"""Startup and initialization for production."""

import json
import asyncio
import hikari
import lightbulb
from datetime import datetime, timezone, timedelta
from lib.config import DATA_PATH, BOT_PATH, LOG_PATH


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
        with open(DATA_PATH / "default_aspect_pool.json", "r") as file:
            config.aspect_pool_data = json.load(file)["Loot"]
    except Exception as e:
        print(f"Error loading default_aspect_pool.json: {e}")
        config.aspect_pool_data = {}
    
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
        with open(BOT_PATH / "items.json", "r") as file:
            config.item_map = json.load(file)
    except Exception as e:
        print(f"Error loading items.json: {e}")
        config.item_map = {}
    
    try:
        with open(BOT_PATH / "stat_mapping.json", "r") as file:
            config.stat_mapping = json.load(file)
    except Exception as e:
        print(f"Error loading stat_mapping.json: {e}")
        config.stat_mapping = {}
    
    try:
        import os
        lb_in_guild_path = os.getenv('LB_IN_GUILD_PATH', str(DATA_PATH / "leaderboard_in_guild.json"))
        with open(lb_in_guild_path, "r") as file:
            config.lb_in_guild = json.load(file)
    except Exception as e:
        print(f"Error loading leaderboard_in_guild.json: {e}")
        config.lb_in_guild = {}
    
    try:
        with open(BOT_PATH / "blocked_users.json", "r") as file:
            loaded_blocked = json.load(file)
            config.blocked_users.clear()
            config.blocked_users.extend(loaded_blocked)
    except Exception as e:
        print(f"Error loading blocked_users.json: {e}")
        config.blocked_users.clear()
    
    print("Data initial load complete.")
    
    # Send startup notification if channel ID is configured
    import os
    log_channel_id = os.getenv('LOG_CHANNEL_ID')
    if log_channel_id:
        try:
            CST = timezone(timedelta(hours=-5))
            time_now = datetime.now(CST)
            current_datetime = time_now.strftime("%Y-%m-%d %H:%M:%S")
            import time
            deploy_time = time.time()
            await bot.rest.create_message(
                channel=int(log_channel_id),
                content=f"Bot restarted at **{current_datetime}** CST\nAround <t:{int(deploy_time)}:R>"
            )
        except Exception as e:
            print(f"Error sending startup notification: {e}")
    
    # Start background tasks
    # asyncio.create_task(todo())
    # asyncio.create_task(task_repeated())

