"""
Project Name: Nori
Author: RawFish
Github: https://github.com/RawFish69
Description: Utility bot for Discord
"""
import logging
import time
import tracemalloc
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
import hikari
import lightbulb
import miru

from lib.config import (
    BOT_TOKEN, VERSION, MODE, ENGINE,
    BASE_PATH, DATA_PATH, BOT_PATH, LOG_PATH
)
from lib.data_manager import BotData, Database
from lib.wynn_api import Player, Guild, Items as WynnItems
from lib.utils import help, get_uptime
from lib.item_wrapper import Items as ItemWrapper
from lib.item_manager import ItemManager
from lib.price_estimator import PriceEstimator
from lib.item_utils import ItemUtils
from lib.item_weight import WeightManager
from lib.changelog_generate import ChangelogManager
from lib.guild_display import GuildManager
from lib.player_display import PlayerManager
from lib.commands.loader import load_all_commands
from lib.startup import load_startup_data
from lib.config import blocked_users

current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = LOG_PATH / f"nori_{current_datetime}.log"
logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

tracemalloc.start()

bot = lightbulb.BotApp(
    token=BOT_TOKEN,
    intents=hikari.Intents.ALL_UNPRIVILEGED
)
miru.install(bot)

bot_data = BotData()
database = Database()
wynn_player = Player()
wynn_guild = Guild()
wynn_items = WynnItems()

bot.managers = {
    "item_manager": ItemManager(),
    "item_utils": ItemUtils({}),
    "weight_manager": WeightManager(str(DATA_PATH / "mythic_weights.json")),
    "changelog_manager": ChangelogManager(
        item_changelog_dir=str(BOT_PATH / "changelog"),
        ingredient_changelog_dir=str(BOT_PATH / "changelog")
    ),
    "guild_manager": GuildManager(),
    "player_manager": PlayerManager(),
    "bot_data": bot_data,
    "database": database,
    "wynn_player": wynn_player,
    "wynn_guild": wynn_guild,
    "wynn_items": wynn_items
}

def setup_bot():
    load_all_commands(bot, blocked_users)
    return bot.managers

deploy_time = 0

@bot.listen(hikari.StartedEvent)
async def bot_start(event):
    global deploy_time
    deploy_time = time.time()
    CST = timezone(timedelta(hours=-5))
    time_now = datetime.now(CST)
    current_datetime = time_now.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"Nori Bot v{VERSION} started in {MODE} mode")
    print(f"Bot started at {current_datetime} CST")
    print(f"Using {ENGINE} language model")
    
    await load_startup_data(bot)


@bot.command()
@lightbulb.command("nori", "Nori bot information")
@lightbulb.implements(lightbulb.SlashCommand)
async def nori_cmd(ctx: lightbulb.Context):
    uptime_str = get_uptime(deploy_time)
    version_info = f"__{MODE}__ mode, **{ENGINE}** language model.\nUptime: {uptime_str}"
    
    nori_embed = hikari.Embed(
        title="Nori Bot",
        description=f"Nori is created and maintained by RawFish.\n{version_info}",
        color="#A6FFBD"
    )
    nori_embed.add_field("Version", VERSION)
    nori_embed.add_field("Status", "Online")
    nori_embed.set_footer("Nori Bot - Utility Bot for Discord")
    
    await ctx.respond(embed=nori_embed)


@bot.command()
@lightbulb.command("help", "Shows this bot's help menu.")
@lightbulb.implements(lightbulb.SlashCommand)
async def help_cmd(ctx: lightbulb.Context):
    user = await bot.rest.fetch_user(ctx.user.id)
    help_dict = help(0)
    help_embed = hikari.Embed(
        title="Help Menu",
        description=f"Requested by {user}",
        color="#A6FFBD"
    )
    for cmd in help_dict:
        help_embed.add_field(cmd, help_dict[cmd])
    help_embed.set_footer("Nori Bot - Help page")
    await ctx.respond(embed=help_embed)


def main():
    setup_bot()
    managers = bot.managers
    print("Managers initialized:")
    for name in managers.keys():
        print(f"  - {name}")
    
    print(f"\nStarting Nori Bot v{VERSION}...")
    bot.run()


if __name__ == "__main__":
    main()
