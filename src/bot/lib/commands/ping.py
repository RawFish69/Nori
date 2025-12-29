"""Basic utility commands."""

import time
import hikari
import lightbulb


def load_ping_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load ping-related commands."""
    
    @bot.command()
    @lightbulb.command('ping', 'Checks the command response latency')
    @lightbulb.implements(lightbulb.SlashCommand)
    async def ping(ctx):
        from lib.utils import check_user_access
        await check_user_access(ctx, blocked_users)
        start_time = time.time()
        await ctx.respond("Calculating latency in real time...", flags=hikari.MessageFlag.LOADING)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        
        await ctx.edit_last_response(f"Command response latency: {latency:.2f} ms")

