"""Utility command set."""

import asyncio
from pathlib import Path

import hikari
import lightbulb
import python_weather

from lib.config import BOT_PATH, DATA_SCRIPTS_GRAPHS_PATH
from lib.utils import check_user_access

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

    @bot.command()
    @lightbulb.option("location", "Name of the city")
    @lightbulb.command("weather", "Checks the weather status of a city")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def check_weather(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        city = ctx.options.location
        try:
            async with python_weather.Client() as client:
                weather = await client.get(city)
        except Exception as error:
            await ctx.respond(f"Could not fetch weather for `{city}`: {error}")
            return

        hourly_lines = []
        forecasts = list(weather.forecasts)
        if forecasts:
            hourly = list(forecasts[0].hourly)
            pairs = []
            for section in hourly:
                pairs.append(f"[{section.time.hour}:{section.time.minute}{section.time.second}] {section.description}")
            for index in range(0, len(pairs), 2):
                hourly_lines.append(" -> ".join(pairs[index:index + 2]))

        display_weather = (
            f"```City/Area: {city}\n"
            f"Region: {weather.nearest_area.region}, {weather.nearest_area.country}\n"
            f"Current Temperature: {weather.current.temperature} C\n"
            f"Feels like {weather.current.feels_like} C\n"
        )
        if forecasts:
            display_weather += f"{forecasts[0].date} (Today):\n"
            display_weather += "\n".join(hourly_lines) + "\n"
        display_weather += (
            f"Wind Direction: {weather.current.wind_direction}, Wind Speed: {weather.current.wind_speed} mph\n"
            f"Humidity: {weather.current.humidity} %\n"
            "```"
        )
        await ctx.respond(display_weather[:1990])

