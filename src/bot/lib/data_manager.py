"""
Data management classes for Nori bot.
Handles user state, caching, and database operations.
"""
import json
import requests
from pathlib import Path
from lib.config import (
    WYNN_AUTH_HEADER, DATA_PATH,
    item_amp_data, guild_prefix_data, build_data, 
    recipe_data, help_data
)


class BotData:
    """
    Manages item, build, and recipe data as well as user-specific states.
    
    This class handles caching or referencing user data across the bot.
    """
    
    def item_amp(self, user, item, rr, tier):
        """Store item amplifier data for a user."""
        temp_data = {
            "item": item,
            "rr": rr,
            "tier": tier,
        }
        item_amp_data[user] = temp_data
        return item_amp_data

    def guild_prefix(self, user, prefix):
        """Store guild prefix data for a user."""
        guild_prefix_data.update({user: prefix})
        return guild_prefix_data

    def build_list(self, user, page):
        """Update build list pagination for a user."""
        page_num = list(build_data[user].keys())[0]
        temp_data = build_data[user][page_num]
        build_data[user] = {page: temp_data}
        return build_data

    def recipe_list(self, user, page):
        """Update recipe list pagination for a user."""
        page_num = list(recipe_data[user].keys())[0]
        temp_data = recipe_data[user][page_num]
        recipe_data[user] = {page: temp_data}
        return recipe_data

    def help_list(self, user, page):
        """Update help menu page for a user."""
        help_data.update({user: page})
        return help_data


class Database:
    """
    Handles Wynncraft-related database operations and connections.
    """
    
    def __init__(self):
        self.API_list = {
            "guild": "https://api.wynncraft.com/v3/guild/list/guild",
            "item": "https://api.wynncraft.com/v3/item/database?fullResult"
        }

    def scan_db(self):
        """Scan and return database statistics."""
        db_result = {}
        guild_api = requests.get(self.API_list["guild"], headers=WYNN_AUTH_HEADER).json()
        db_result["guilds"] = len(guild_api)
        item_api = requests.get(self.API_list["item"], headers=WYNN_AUTH_HEADER).json()
        db_result["items"] = len(item_api)
        build_nori = json.load(open(DATA_PATH / "build_db.json", "r"))
        db_result["builds"] = len(build_nori["Builds"])
        recipe_nori = json.load(open(DATA_PATH / "recipe_db.json", "r"))
        db_result["recipes"] = len(recipe_nori["Recipes"])
        return db_result

