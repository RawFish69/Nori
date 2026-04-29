"""
Project Name: Nori
Author: RawFish
Github: https://github.com/RawFish69
Description: Utility bot for Discord
"""
import logging
import os
import time
import tracemalloc
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv
import hikari
import lightbulb
import miru

from lib.config import (
    BOT_TOKEN, VERSION, MODE,
    BASE_PATH, DATA_PATH, BOT_PATH, LOG_PATH, USER_IMG_PATH
)
from lib.data_manager import BotData, Database
from lib.wynn_api import Player, Guild, Items as WynnItems
from lib.item_wrapper import Items as ItemWrapper
from lib.item_manager import ItemManager
from lib.price_estimator import PriceEstimator
from lib.item_utils import ItemUtils
from lib.item_weight import WeightManager
from lib.changelog_generate import ChangelogManager
from lib.guild_display import GuildManager
from lib.player_display import PlayerManager
from lib.event_hooks import load_event_hooks
from lib.startup import load_startup_data
import lib.config as config
from lib.manager_registry import set_managers, get_managers

current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = LOG_PATH / f"nori_{current_datetime}.log"
logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

tracemalloc.start()


class NoriGatewayBot(hikari.GatewayBot):
    """GatewayBot with a small app-local data namespace."""


bot = NoriGatewayBot(token=BOT_TOKEN, intents=hikari.Intents.ALL_UNPRIVILEGED)
client = lightbulb.client_from_app(bot)
miru_client = miru.Client(bot)
bot.d = SimpleNamespace()
bot.d.miru = miru_client


@client.error_handler(priority=10)
async def on_command_error(exc: lightbulb.exceptions.ExecutionPipelineFailedException) -> bool:
    cause = exc.causes[0] if exc.causes else exc
    ctx = exc.context
    if isinstance(cause, lightbulb.prefab.NotOwner):
        await ctx.respond("You are not permitted to use this command.", flags=hikari.MessageFlag.EPHEMERAL)
        return True
    if isinstance(cause, lightbulb.prefab.MissingRequiredRoles):
        await ctx.respond("You need the required contributor role to use this command.", flags=hikari.MessageFlag.EPHEMERAL)
        return True
    await ctx.respond(f"An error occurred: {cause}", flags=hikari.MessageFlag.EPHEMERAL)
    return True

bot_data = BotData()
database = Database()
wynn_player = Player()
wynn_guild = Guild()
wynn_items = WynnItems()

set_managers({
    "item_manager": ItemManager(),
    "item_utils": ItemUtils({}),
    "weight_manager": WeightManager(str(DATA_PATH / "mythic_weights.json")),
    "price_estimator": PriceEstimator(output_path=USER_IMG_PATH / "pricecheck"),
    "changelog_manager": ChangelogManager(
        item_changelog_dir=str(BOT_PATH / "changelog" / "item_changelog"),
        ingredient_changelog_dir=str(BOT_PATH / "changelog" / "ingredient_changelog")
    ),
    "guild_manager": GuildManager(),
    "player_manager": PlayerManager(),
    "bot_data": bot_data,
    "database": database,
    "wynn_player": wynn_player,
    "wynn_guild": wynn_guild,
    "wynn_items": wynn_items
})

def setup_bot():
    try:
        # wynntilsresolver bootstraps data at import time using its own event
        # loop. Import it before Hikari starts the Discord loop.
        from lib.decoders import ItemDecoder  # noqa: F401
        print("Wynntils item decoder preloaded.")
    except Exception as error:
        print(f"Wynntils item decoder preload failed: {type(error).__name__}: {error}")
    load_event_hooks(bot)
    return get_managers()

deploy_time = 0


async def load_commands(event: hikari.StartingEvent) -> None:
    await client.load_extensions(
        "lib.commands.ping",
        "lib.commands.wynn_stats",
        "lib.commands.tower",
        "lib.commands.items",
        "lib.commands.ingredients",
        "lib.commands.aspects",
        "lib.commands.raid",
        "lib.commands.builds",
        "lib.commands.recipes",
        "lib.commands.utility",
        "lib.commands.portal",
        "lib.commands.games",
        "lib.commands.tasks",
        "lib.commands.social",
        "lib.commands.server",
        "lib.commands.math_tools",
        "lib.commands.help",
    )


bot.subscribe(hikari.StartingEvent, load_commands)
bot.subscribe(hikari.StartingEvent, client.start)
bot.subscribe(hikari.StoppingEvent, client.stop)

@bot.listen(hikari.InteractionCreateEvent)
async def on_interaction(event: hikari.InteractionCreateEvent) -> None:
    if isinstance(event.interaction, hikari.CommandInteraction):
        config.command_count += 1

@bot.listen(hikari.StartedEvent)
async def bot_start(event):
    global deploy_time
    deploy_time = time.time()
    config.deploy_time = deploy_time
    CST = timezone(timedelta(hours=-5))
    time_now = datetime.now(CST)
    current_datetime = time_now.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"Nori Bot v{VERSION} started in {MODE} mode")
    print(f"Bot started at {current_datetime} CST")
    
    await load_startup_data(bot)


def main():
    setup_bot()
    managers = get_managers()
    print("Managers initialized:")
    for name in managers.keys():
        print(f"  - {name}")
    
    print(f"\nStarting Nori Bot v{VERSION}...")
    logging.info("Starting Nori Bot process [pid:%s, ppid:%s]", os.getpid(), os.getppid())
    try:
        bot.run()
    except BaseException:
        logging.exception("Nori Bot process exited with an unhandled exception")
        raise
    finally:
        logging.info("Nori Bot process exiting [pid:%s]", os.getpid())


if __name__ == "__main__":
    main()
