"""Command loader for all bot commands."""

import lightbulb
from lib.commands.ping import load_ping_commands
from lib.commands.wynn_stats import load_wynn_stats_commands
from lib.commands.tower import load_tower_commands
from lib.commands.items import load_item_commands


def load_all_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load all bot commands."""
    load_ping_commands(bot, blocked_users)
    load_wynn_stats_commands(bot, blocked_users)
    load_tower_commands(bot, blocked_users)
    load_item_commands(bot, blocked_users)

