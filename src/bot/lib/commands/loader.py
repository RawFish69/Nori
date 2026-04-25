"""Command loader for all bot commands."""

import lightbulb
from lib.commands.ping import load_ping_commands
from lib.commands.wynn_stats import load_wynn_stats_commands
from lib.commands.tower import load_tower_commands
from lib.commands.items import load_item_commands
from lib.commands.ingredients import load_ingredient_commands
from lib.commands.aspects import load_aspect_commands
from lib.commands.builds import load_build_commands
from lib.commands.recipes import load_recipe_commands
from lib.commands.utility import load_utility_commands
from lib.commands.games import load_game_commands
from lib.commands.tasks import load_task_commands
from lib.commands.social import load_social_commands
from lib.commands.server import load_server_commands
from lib.commands.owner_tools import load_owner_tools_commands
from lib.commands.admin import load_admin_commands
from lib.commands.ai_tools import load_ai_tools_commands
from lib.commands.math_tools import load_math_commands


def load_all_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load all bot commands."""
    load_ping_commands(bot, blocked_users)
    load_wynn_stats_commands(bot, blocked_users)
    load_tower_commands(bot, blocked_users)
    load_item_commands(bot, blocked_users)
    load_ingredient_commands(bot, blocked_users)
    load_aspect_commands(bot, blocked_users)
    load_build_commands(bot, blocked_users)
    load_recipe_commands(bot, blocked_users)
    load_utility_commands(bot, blocked_users)
    load_game_commands(bot, blocked_users)
    load_task_commands(bot, blocked_users)
    load_social_commands(bot, blocked_users)
    load_server_commands(bot, blocked_users)
    load_owner_tools_commands(bot, blocked_users)
    load_admin_commands(bot, blocked_users)
    load_ai_tools_commands(bot, blocked_users)
    load_math_commands(bot, blocked_users)

