"""
Project Name: Nori
Author: RawFish
Github: https://github.com/RawFish69
Description: Utility bot for Discord
"""

from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
import asyncio
import functools
import json
import logging
import os
import random
import time
from dotenv import load_dotenv
import hikari
import lightbulb
import miru
import numpy as np
import pandas as pd
import requests
import seaborn as sns
import sympy as sp
import tracemalloc
from PIL import (
    Image,
    ImageDraw,
    ImageFont
)
from matplotlib import (
    pyplot as plt,
    colors as mcolors
)
from scipy.interpolate import CubicSpline
from lib.item_wrapper import Items
from lib.item_manager import ItemManager
from lib.price_estimator import PriceEstimator
from lib.item_utils import ItemUtils
from lib.item_weight import WeightManager
from lib.changelog_generate import ChangelogManager
from lib.guild_display import GuildManager
from lib.player_display import PlayerManager
current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
tracemalloc.start()
bot_token = os.getenv('NORI_TOKEN')
bot = lightbulb.BotApp(
    token=bot_token,
    intents=hikari.Intents.ALL_UNPRIVILEGED
)
miru.install(bot)

def setup_bot():
    """
    Creates and configures all supporting manager objects needed by Nori.

    Returns:
        dict: A dictionary containing references to objects for item
              management, guild management, player management, etc.
    """
    item_manager = ItemManager()
    item_utils = ItemUtils({})
    weight_manager = WeightManager("path/to/weights")
    changelog_manager = ChangelogManager(
        item_changelog_dir="path/to/item_changelogs",
        ingredient_changelog_dir="path/to/ingredient_changelogs"
    )
    guild_manager = GuildManager()
    player_manager = PlayerManager()

    return {
        "item_manager": item_manager,
        "item_utils": item_utils,
        "weight_manager": weight_manager,
        "changelog_manager": changelog_manager,
        "guild_manager": guild_manager,
        "player_manager": player_manager
    }

# Below are the example structures for the various classes and components
# I left them as skeletons to show the intended structure and usage of each class


class BotData:
    """
    Manages item, build, and recipe data as well as user-specific states.

    This class is intended to handle caching or referencing user data across
    the bot. Typical usage might involve reading/storing user progress or
    preferences in various commands. Internal logic might include:
      - Merging user-submitted data with internal resources
      - Tracking temporary state (e.g. item roll attempts)
      - Providing an interface to store or retrieve data from a database
      - Managing user-specific settings or preferences
      - Handling user-specific cooldowns or rate limits
      - Storing or updating user-specific item or build data
      - Maintaining a cache of frequently accessed data
    """


class database:
    """
    Handles Wynncraft-related database operations and connections.

    Contains methods for querying or caching Wynncraft-related data, such as:
      - Player info
      - Guild info
      - Server or item metadata
      - Real-time or historical data for various Wynncraft aspects
      - Any other data that needs to be stored or retrieved
    The class may abstract away HTTP calls or local storage for improved modularity.
    """


class Player:
    """
    Provides Wynncraft player info retrieval and manipulation.

    Could contain methods to:
      - Fetch player's basic or full stats
      - Compute or parse the data to produce user-friendly output
      - Handle real-time or historical data for a player's activities

    Use player_display from lib for the actual implementation.
    """


class Guild:
    """
    Provides Wynncraft guild info, such as name, prefix, or member data, etc.

    Expected logic involves:
      - Fetching guild data from the Wynncraft API
      - Collating guild member info, ranks, and territories
      - Summarizing data in an easy-to-display format for Discord
    
    Use guild_display from lib for the actual implementation.
    """


class Items:
    """
    Manages Wynncraft item data and queries from Wynncraft's official or beta API.

    Potential logic includes:
      - Fetching all items or doing item search
      - Comparing older and newer data for changelog generation
      - Handling item-specific caching to reduce API usage
    
    Use item manager from lib for the actual implementation.
    """


class CustomTextSelect:
    """
    A skeleton for a custom text-select menu component in Discord.

    Typically used for letting users pick among text-based options. Logic might:
      - Define selectable text items
      - Bind a callback that processes the user choice
      - Update a message or embed upon selection
    
    This refers to the lightbulb SelectMenu component.
    """


class GraphButton:
    """
    A skeleton for a 'Graph' button component.

    Often used to display or toggle a graphical representation of data. Logic could:
      - Register a button click
      - Generate or retrieve a plot image
      - Edit an existing Discord message with the new graph
    """


class SplineButton:
    """
    A skeleton for a 'Spline' component.

    Intended usage might:
      - Show a mathematical spline function or curve data
      - Provide textual or image-based info upon button click
      - Let the user toggle advanced math outputs
    
    In the case of nori, it is used for pricecheck and math components.
    """


class RegressionButton:
    """
    A skeleton for a 'Regression' button component.

    Often used for toggling or displaying regression-based outputs. Logic could:
      - Calculate or store polynomial/logistic regression info
      - Show relevant numeric or graphical data
      - Manage repeated user queries for updated info

    In the case of nori, it is used for pricecheck and math components.
    """


class GameView:
    """
    A skeleton for a Tic-Tac-Toe view with interactive Discord buttons.

    This class supports 3x3, 4x4, and 5x5 board sizes with potential internal logic:
      - Holds a simple board representation (e.g. 9, 16, or 25 spots)
      - Lets user click buttons to place 'X' or 'O'
      - Checks for winning conditions or a draw
      - Renders updated board state after each button press
      - Provides more complex AI or advanced strategy for larger boards
    
    Refer to 5x5_logic.py in lib for the actual implementation.
    """

class menuView:
    """
    A basic skeleton for a multi-button menu (e.g. main menu in Discord).

    Could hold logic to:
      - Provide a row of buttons for various actions
      - Navigate sub-menus or help pages
      - Perform quick utility tasks (ping, server info, etc.)
    
    This refers to the lightbulb UI components.
    """


class helpView:
    """
    A skeleton for a help menu with category buttons.

    Possibly used to:
      - Display different embed pages describing commands
      - Switch categories (Stats, Utility, Items, Tools)
      - Provide ephemeral or standard messages guiding the user
    """


class ampView:
    """
    A skeleton for an item amplifier or reroll interactive UI.

    Might involve:
      - Letting a user simulate item ID rolling
      - Updating real-time results with new stats or percentages
      - Tracking user attempts or gambler's fallacy disclaimers
    
    Calls BotData for item management and caching.
    """


class buildView:
    """
    A skeleton for a pagination view of build results.

    Typical usage:
      - Display a list of user or community-submitted builds
      - Let user move between multiple pages of results
      - Possibly handle sorting or filtering of builds in real time
    
    Calls BotData for build management and caching.
    """


class recipeView:
    """
    A skeleton for a pagination view of recipe results.

    Could:
      - List crafted recipes matching user search
      - Provide next/previous page button or text selection
      - Potentially integrate with Wynncraft's crafting simulators
    
    Calls BotData for recipe management and caching.
    """


class prof_view:
    """
    A skeleton for profession leaderboard text select.

    Typically used for:
      - Displaying multiple options for different gathering or crafting professions
      - Updating an embed or message based on user selection
      - Show top players in each profession
    
    Refer to the leaderboard component for fetch, process, and display.
    """


class lootView:
    """
    A skeleton for weekly lootpool rotation display.

    Might contain logic to:
      - Show different tiers of item drops for certain Wynncraft areas
      - Offer button-based selection to filter Mythic, Fabled, etc.
      - Retrieve or store rotation info for extended durations
    """


class aspectView:
    """
    A skeleton for weekly aspect rotation display.

    Similar to lootView but for aspects or custom rotating content. Logic might:
      - Let user pick which tier of aspects to view
      - Show advanced raids or endgame rotations
      - Link to a web-based resource for deeper data
    """


class raidView:
    """
    A skeleton for a raid leaderboard view.

    Potential usage:
      - Select which raid (TNA, TCC, NOL, etc.) to view
      - Move across multiple pages
      - Display player clear stats or ranks
    """


class GuildLeaderboardView:
    """
    A skeleton for a guild-specific leaderboard.

    Logic might revolve around:
      - Loading a single guild's stats
      - Displaying a variety of categories: xp, raids, dungeons
      - Handling pagination or select options
    """


class statView:
    """
    A skeleton for a stats leaderboard view.

    May handle:
      - Global Wynncraft stats like chests opened, mobs killed
      - Button-based interactions to choose next or previous pages
      - Potential ephemeral usage for minimal channel clutter
    """


class gxpView:
    """
    A skeleton for a guild xp or leveling command view.

    Used to:
      - Display leveling curve graphs (e.g. 1-50, 51-100, etc.)
      - Let user quickly switch among multiple relevant XP ranges
    """


class hqView:
    """
    A skeleton for HQ tower stats view.

    Could handle:
      - Show advanced war tower info
      - Render quick visual or textual references for guild defenders
      - Let user cycle between different stats like damage, DPS, EHP
    """


class towerView:
    """
    A skeleton for non-HQ tower stats view.

    Similar to hqView but for standard territories. Might:
      - Reflect changes in tower link count or defense levels
      - Provide a quick reference for upcoming war attempts
    """

def main():
    """
    Entry point for running the Nori bot. This function sets up resources,
    demonstrates example usage, and starts the bot loop.
    """
    managers = setup_bot()
    item_mgr = managers["item_manager"]
    player_mgr = managers["player_manager"]
    guild_mgr = managers["guild_manager"]

    updated_count = item_mgr.update_items("/home/ubuntu/nori-bot/bot/items.json")
    print(f"Items updated: {updated_count}")

    stats_result = player_mgr.get_player_stats("ExamplePlayerName")
    if stats_result:
        display_str, is_online, uuid = stats_result
        print("Player Stats:", display_str)

    guild_result = guild_mgr.get_guild_stats("ExampleGuild")
    if guild_result:
        guild_display, g_name, g_prefix, tier, structure = guild_result
        print("Guild Stats:", guild_display)

    bot.run()
    print("Bot started")


if __name__ == "__main__":
    main()
