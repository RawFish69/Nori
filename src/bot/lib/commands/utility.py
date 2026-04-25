"""Utility command set."""

import asyncio
from pathlib import Path

import hikari
import lightbulb

from lib.config import BOT_PATH, DATA_SCRIPTS_GRAPHS_PATH
from lib.utils import check_user_access
from lib.views.menu import TheView

ONLINE_GRAPH_FILES = {
    "24 hours": "latest_activity.png",
    "last 3 days": "latest_3_day_activity.png",
    "weekly": "latest_weekly_activity.png",
    "monthly": "latest_monthly_activity.png",
    "last 3 months": "last_3_months_activity.png",
    "last 6 months": "last_6_months_activity.png",
    "annual": "annual_activity.png",
}

ONLINE_GRAPH_TITLES = {
    "24 hours": "Player activity from the past 24 hours",
    "last 3 days": "Player activity from the past 3 days",
    "weekly": "Player activity from the past 7 days",
    "monthly": "Player activity from the past 30 days",
    "last 3 months": "Player activity from the past 3 months",
    "last 6 months": "Player activity from the past 6 months",
    "annual": "Player activity from the past 12 months",
}


def load_utility_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load utility commands."""

    @bot.command
    @lightbulb.option("duration", "Time in minutes", type=int, required=False)
    @lightbulb.command("pingme", "Pings a user after given time")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def pingme(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        user = await bot.rest.fetch_user(ctx.user.id)
        channel_id = ctx.channel_id
        duration_minutes = ctx.options.duration if ctx.options.duration else 30
        duration_seconds = duration_minutes * 60
        await ctx.respond(f"{user.mention}, I will ping you in {duration_minutes} minutes!")
        await asyncio.sleep(duration_seconds)
        ping_user = f"{user.mention}, {duration_minutes} minutes of time is up!."
        await bot.rest.create_message(channel=channel_id, content=ping_user, user_mentions=True)

    @bot.command()
    @lightbulb.command("menu", "Menu showing all the options")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def menu(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        view = TheView(timeout=60)
        user = await bot.rest.fetch_user(ctx.user.id)
        message = await ctx.respond(f"Menu requested by {user}", components=view.build())
        message = await message
        await view.start(message)
        await view.wait()

    @bot.command()
    @lightbulb.option("runs", "How many runs of 8/8 forgery", required=False, type=int, min_value=1, max_value=1000)
    @lightbulb.command("forgery", "Forgery mythic drop chance")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def forgery(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        graph_path = BOT_PATH / "forgery.png"
        if not graph_path.exists():
            await ctx.respond("Forgery graph file is missing. Expected `bot/forgery.png`.")
            return

        forgery_graph = hikari.files.File(str(graph_path))
        forgery_embed = hikari.Embed(title="Forgery mythic chance", color="#FFA9F3")
        if ctx.options.runs:
            total = ctx.options.runs
            chance_base = 1.5
            bonus = 1.01
            chance = chance_base
            expected = chance
            cumulative_expected = 0
            for runs in range(1, total + 1):
                chance = chance_base * (bonus ** runs)
                current_expected = 1 - (1 - (chance / runs) / 100) ** runs
                expected += current_expected
                cumulative_expected += expected
            display = "Mythic chance: {:.2f}%\nCumulative expected chance: {:.2f}%".format(chance, cumulative_expected)
            forgery_embed.add_field(f"At {total} Forgery runs", display)
        forgery_embed.set_image(forgery_graph)
        forgery_embed.set_footer("Nori Bot - Forgery")
        await ctx.respond(embed=forgery_embed)

    @bot.command()
    @lightbulb.option(
        "range",
        "Time range",
        choices=["24 hours", "last 3 days", "weekly", "monthly", "last 3 months", "last 6 months", "annual"],
        default="24 hours",
    )
    @lightbulb.command("online", "Check player activity")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def player_activity(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        selected_range = ctx.options.range if ctx.options.range in ONLINE_GRAPH_FILES else "24 hours"
        graph_file = ONLINE_GRAPH_FILES[selected_range]
        title = ONLINE_GRAPH_TITLES[selected_range]
        graph_path = DATA_SCRIPTS_GRAPHS_PATH / graph_file

        if not graph_path.exists():
            await ctx.respond(
                f"Online activity graph is unavailable for `{selected_range}`.\n"
                f"Expected file: `{graph_path}`"
            )
            return

        img = hikari.files.File(str(graph_path))
        online_embed = hikari.Embed(
            title=title,
            description="Wynncraft online players visualization",
            color="#B2BAEC",
        )
        online_embed.set_image(img)
        online_embed.set_footer("Nori Bot - Player Activity")
        await ctx.respond(embed=online_embed)

