"""
Utility functions for Nori bot.
Helper functions that don't depend on bot instance.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from lib.config import DATA_PATH, BOT_PATH, VERSION
from lib.wynn_api import Player, Guild


async def check_user_access(ctx, blocked_users: list = None):
    """Check if user has access to bot commands."""
    if blocked_users is None:
        return
    
    user_id = ctx.user.id
    if user_id in blocked_users:
        import hikari
        import lightbulb
        from lib.config import bot
        user = await bot.rest.fetch_user(user_id)
        print(f"Blocked user {user.username} (ID: {user_id}) attempted to run a command.")
        await ctx.respond("Your account has been blocked from this bot.",
                                    flags=hikari.MessageFlag.EPHEMERAL)
        raise lightbulb.errors.CheckFailure(f"User {user.username} is blocked.")


def help(index):
    """Return help menu dictionary based on index."""
    help_menu = {
        "Nori command menu": "Currently using SlashCommands!",
        "Select a command group to view": "You can also type / in the chat and browse the command list",
        "For bot information": "Do /nori"
    }
    wynn_stats = {
        "player": "Display a player's in game statistics",
        "guild": "Display a guild's statistics",
        "lb raid": "Raid leaderboard of all players",
        "lb stat": "Stat leaderboard of all players",
        "lb profession": "Profession leaderboard of all players",
        "online": "Show online player activity (all players)"
    }
    wynn_utility = {
        "build search": "Search for class build with keyword",
        "recipe search": "Search for recipe with keyword",
        "ingredient search": "Search for ingredient with name",
        "uptime": "Online servers uptime",
        "soul": "Soul point regen timer",
        "forgery": "Forgery mythic odds",
        "gxp": "Guild xp requirement graph",
        "hq": "Calculate HQ guild tower stats",
        "tower": "Calculate regular guild tower stats",
        "lootpool": "Weekly lootpool for lootrun camps"
    }
    items = {
        "item search": "Search for an item with name",
        "item roll": "Identify or reroll an item",
        "item changelog": "Item changelog fetched from API",
        "item check": "View in game item stats by pasting the wynntils encoded item (F3 function)",
        "item weigh": "Directly weigh the mythic copied from wynntils F3 chat-item with (mythic only)",
        "item pricecheck": "Directly price-check the mythic copied from wynntils F3 chat-item (mythic only)",
        "item scale": "Weighing scale of a mythic item",
        "item evaluate": "Manual weighing of an item by inputting the wynntils % for each stat in order from the weighing scale.",
        "item pc": "Manual pricechecking of an item by inputting the wynntils % for each stat in order from the weighing scale.",
        "For manual input": "If an item has less than 7 stats on the scale, leave the rest blank.",
        "item lootpool": "Weekly Lootrun Camp Reward Pool",
        "item history": "Check specific item in lootpool history"
    }
    tools = {
        "ask": "Ask AI (gpt-turbo model)",
        "image": "Generate image with keyword",
        "math": "Mathematical tools",
        "status": "Bot current status",
        "profile": "Check user profile",
        "ping": "Check the latency of an url",
        "weather": "Check weather of a city/area",
        "flight": "Show all flights info",
        "pingme": "Ping an user after a set timer"
    }
    if index == 0:
        return help_menu
    elif index == 1:
        return wynn_stats
    elif index == 2:
        return wynn_utility
    elif index == 3:
        return items
    elif index == 4:
        return tools
    return help_menu


def get_uptime(deploy_time):
    """Calculate and format uptime."""
    current_time = time.time()
    up_time = int(current_time - deploy_time)
    minutes, seconds = divmod(up_time, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    time_display = f"**{days:2d}** d **{hours:2d}** h **{minutes:2d}** m **{seconds:2d}** s"
    return time_display


def format_xp(xp_value):
    """Format XP value for display with proper scaling."""
    if xp_value >= 1_000_000_000_000:
        return '{:.1f}T'.format(xp_value / 1_000_000_000_000)
    elif xp_value >= 1_000_000_000:
        return '{:.0f}B'.format(xp_value / 1_000_000_000)
    elif xp_value >= 1_000_000:
        return '{:.0f}M'.format(xp_value / 1_000_000)
    elif xp_value >= 1_000:
        return '{:.0f}K'.format(xp_value / 1_000)
    else:
        return str(xp_value)


async def build_file_search(keywords):
    """Search builds by keywords."""
    with open(DATA_PATH / "build_db.json", "r") as file:
        data = json.load(file)["Builds"]
    result = {"Result": []}
    keywords = [keyword.lower() for keyword in keywords]
    for build in data:
        tags = data[build]["tag"]
        if len(keywords) == 3:
            if keywords[0] in tags.lower() and keywords[1] in tags.lower() and keywords[2] in tags.lower():
                result["Result"].insert(0, {build: data[build]})
            elif keywords[0] in build.lower() and keywords[1] in build.lower() and keywords[2] in build.lower():
                result["Result"].insert(0, {build: data[build]})
        elif len(keywords) == 2:
            if keywords[0] in tags.lower() and keywords[1] in tags.lower():
                result["Result"].append({build: data[build]})
            elif keywords[0] in build.lower() and keywords[1] in build.lower():
                result["Result"].append({build: data[build]})
        else:
            for keyword in keywords:
                if keyword in build.lower() or keyword in tags.lower():
                    result["Result"].append({build: data[build]})
    return result


async def recipe_file_search(keywords):
    """Search recipes by keywords."""
    with open(DATA_PATH / "recipe_db.json", "r") as file:
        data = json.load(file)["Recipes"]
    result = {"Result": []}
    keywords = [keyword.lower() for keyword in keywords]
    for recipe in data:
        tags = data[recipe]["tag"]
        if len(keywords) == 3:
            if keywords[0] in tags.lower() and keywords[1] in tags.lower() and keywords[2] in tags.lower():
                result["Result"].insert(0, {recipe: data[recipe]})
            elif keywords[0] in recipe.lower() and keywords[1] in recipe.lower() and keywords[2] in recipe.lower():
                result["Result"].insert(0, {recipe: data[recipe]})
        elif len(keywords) == 2:
            if keywords[0] in tags.lower() and keywords[1] in tags.lower():
                result["Result"].append({recipe: data[recipe]})
            elif keywords[0] in recipe.lower() and keywords[1] in recipe.lower():
                result["Result"].append({recipe: data[recipe]})
        else:
            for keyword in keywords:
                if keyword in recipe.lower() or keyword in tags.lower():
                    result["Result"].append({recipe: data[recipe]})
    return result


def ingredient_search(name):
    """Search for ingredient by name."""
    with open(BOT_PATH / "items.json", "r") as file:
        full_list = json.load(file)
    result = {}
    for ing in full_list:
        if name.lower() == ing.lower():
            result = full_list[ing]
    return result

