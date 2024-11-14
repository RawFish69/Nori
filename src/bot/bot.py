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
import lib.item_weight

current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
tracemalloc.start()

bot_token = os.getenv('NORI_TOKEN')

bot = lightbulb.BotApp(
    token=bot_token,
    intents=hikari.Intents.ALL_UNPRIVILEGED
)
miru.install(bot)

bot.run()