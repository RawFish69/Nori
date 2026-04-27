"""Deprecated aspect command aliases."""

import hikari
import lightbulb

from lib.utils import check_user_access


def load_aspect_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load deprecated aspect aliases that point users at `/raid`."""

    @bot.command()
    @lightbulb.command("aspect", "Deprecated raid alias")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def aspect(ctx: lightbulb.Context):
        pass

    @aspect.child()
    @lightbulb.command("lootpool", "Deprecated command alias")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def show_aspect_lootpool_deprecated(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        deprecation_msg = (
            "`/aspect lootpool` is deprecated.\n"
            "Use one of these commands instead:\n"
            "- `/raid aspect`\n"
            "- `/raid gambit`\n"
            "- `/raid item`"
        )
        await ctx.respond(deprecation_msg, flags=hikari.MessageFlag.EPHEMERAL)
