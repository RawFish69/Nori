"""Utility command set."""
import asyncio
from pathlib import Path
import hikari
import lightbulb
import python_weather
from lib.config import BOT_PATH, DATA_SCRIPTS_GRAPHS_PATH
from lib.lightbulb_compat import lb_choices
loader = lightbulb.Loader()
ONLINE_GRAPH_FILES = {'24 hours': 'latest_activity.png', 'last 3 days': 'latest_3_day_activity.png', 'weekly': 'latest_weekly_activity.png', 'monthly': 'latest_monthly_activity.png', 'last 3 months': 'last_3_months_activity.png', 'last 6 months': 'last_6_months_activity.png', 'annual': 'annual_activity.png'}
ONLINE_GRAPH_TITLES = {'24 hours': 'Player activity from the past 24 hours', 'last 3 days': 'Player activity from the past 3 days', 'weekly': 'Player activity from the past 7 days', 'monthly': 'Player activity from the past 30 days', 'last 3 months': 'Player activity from the past 3 months', 'last 6 months': 'Player activity from the past 6 months', 'annual': 'Player activity from the past 12 months'}

@loader.command
class Pingme(lightbulb.SlashCommand, name='pingme', description='Pings a user after given time'):
    duration = lightbulb.integer('duration', 'Time in minutes', default=None)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        user = await ctx.client.app.rest.fetch_user(ctx.user.id)
        channel_id = ctx.channel_id
        duration_minutes = self.duration if self.duration else 30
        duration_seconds = duration_minutes * 60
        await ctx.respond(f'{user.mention}, I will ping you in {duration_minutes} minutes!')
        await asyncio.sleep(duration_seconds)
        ping_user = f'{user.mention}, {duration_minutes} minutes of time is up!.'
        await ctx.client.app.rest.create_message(channel=channel_id, content=ping_user, user_mentions=True)

@loader.command
class PlayerActivity(lightbulb.SlashCommand, name='online', description='Check player activity'):
    range = lightbulb.string('range', 'Time range', choices=lb_choices(['24 hours', 'last 3 days', 'weekly', 'monthly', 'last 3 months', 'last 6 months', 'annual']), default='24 hours')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        selected_range = self.range if self.range in ONLINE_GRAPH_FILES else '24 hours'
        graph_file = ONLINE_GRAPH_FILES[selected_range]
        title = ONLINE_GRAPH_TITLES[selected_range]
        graph_path = DATA_SCRIPTS_GRAPHS_PATH / graph_file
        if not graph_path.exists():
            await ctx.respond(f'Online activity graph is unavailable for `{selected_range}`.\nExpected file: `{graph_path}`')
            return
        img = hikari.files.File(str(graph_path))
        online_embed = hikari.Embed(title=title, description='Wynncraft online players visualization', color='#B2BAEC')
        online_embed.set_image(img)
        online_embed.set_footer('Nori Bot - Player Activity')
        await ctx.respond(embed=online_embed)

@loader.command
class CheckWeather(lightbulb.SlashCommand, name='weather', description='Checks the weather status of a city'):
    location = lightbulb.string('location', 'Name of the city')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        city = self.location
        try:
            async with python_weather.Client() as client:
                weather = await client.get(city)
        except Exception as error:
            await ctx.respond(f'Could not fetch weather for `{city}`: {error}')
            return
        hourly_lines = []
        forecasts = list(weather.daily_forecasts)
        if forecasts:
            hourly = list(forecasts[0].hourly_forecasts)
            pairs = []
            for section in hourly:
                pairs.append(f'[{section.time.hour:02d}:{section.time.minute:02d}] {section.description}')
            for index in range(0, len(pairs), 2):
                hourly_lines.append(' -> '.join(pairs[index:index + 2]))
        display_weather = f'```City/Area: {weather.location}\nRegion: {weather.region}, {weather.country}\nCurrent Temperature: {weather.temperature} C\nFeels like {weather.feels_like} C\n'
        if forecasts:
            display_weather += f'{forecasts[0].date} (Today):\n'
            display_weather += '\n'.join(hourly_lines) + '\n'
        display_weather += f'Wind Direction: {weather.wind_direction}, Wind Speed: {weather.wind_speed} km/h\nHumidity: {weather.humidity} %\n```'
        await ctx.respond(display_weather[:1990])
