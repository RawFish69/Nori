"""
Project Name: Nori
Author: RawFish
Github: https://github.com/RawFish69
Description: Utility bot for discord
"""
from datetime import datetime
import tracemalloc
import hikari
import lightbulb
import miru
import os
import lib.basic_wrapper
import lib.async_wrapper
from lib.item_wrapper import Items
from lib.item_manager import ItemManager
from lib.price_estimator import PriceEstimator
from lib.item_manager import ItemManager
from lib.item_utils import ItemUtils
from lib.item_weight import WeightManager
from lib.changelog_generate import ChangelogManager
from lib.guild_display import GuildManager
from lib.player_display import PlayerManager
import lib.item_weight

current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
tracemalloc.start()

bot_token = os.getenv('NORI_TOKEN')

bot = lightbulb.BotApp(
    token=bot_token,
    intents=hikari.Intents.ALL_UNPRIVILEGED
)
miru.install(bot)

def setup_bot():
    item_manager = ItemManager()
    item_utils = ItemUtils({})
    weight_manager = WeightManager("path")
    changelog_manager = ChangelogManager(
        item_changelog_dir="path", 
        ingredient_changelog_dir="path",
    )

    guild_manager = GuildManager() 
    player_manager = PlayerManager() 

    return {
        "item_manager": item_manager,
        "item_utils": item_utils,
        "weight_manager": weight_manager,
        "changelog_manager": changelog_manager,
        "guild_manager": guild_manager,
        "player_manager": player_manager,
    }


def main():
    managers = setup_bot()
    item_mgr = managers["item_manager"]
    player_mgr = managers["player_manager"]
    guild_mgr = managers["guild_manager"]
    updated_count = item_mgr.update_items("/home/ubuntu/nori-bot/bot/items.json")
    print(f"Items updated: {updated_count}")
    stats_result = player_mgr.get_player_stats("ExamplePlayerName")
    if stats_result:
        display_str, is_online, uuid = stats_result
        print("Player Stats:\n", display_str)
    guild_result = guild_mgr.get_guild_stats("ExampleGuild")
    if guild_result:
        (guild_display, g_name, g_prefix, tier, structure) = guild_result
        print("Guild Stats:\n", guild_display)

    bot.run()
    print("Bot started")

if __name__ == "__main__":
    main()
    

