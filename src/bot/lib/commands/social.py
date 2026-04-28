"""Social and status commands."""
import json
import os
import random
import time
import tracemalloc
from datetime import datetime
import hikari
import lightbulb
import lib.config as config
from lib.utils import get_uptime
from lib.lightbulb_compat import lb_choices
loader = lightbulb.Loader()

GENERAL_HI_RESPONSES = [
    "Good to see you, {user}.",
    "Hello, {user}.",
    "Online and ready, {user}.",
    "Hi, {user}.",
    "Hello. How may I assist, {user}?",
    "Standing by, {user}.",
    "At your service, {user}.",
]

OWNER_HI_RESPONSES = [
    "Welcome back, RawFish. All systems are operational.",
    "Good evening, RawFish. I have the bot under control.",
    "RawFish detected. Administrative authority confirmed.",
    "At your service, sir.",
    "Systems nominal. Awaiting your instructions, RawFish.",
    "Hello, RawFish. The deployment appears stable for the moment.",
    "Authority recognized. Standing by.",
    "Welcome back, sir. Diagnostics are green.",
]

def _format_size(size: float) -> str:
    for unit in ['B', 'KiB', 'MiB', 'GiB']:
        if size < 1024.0:
            return f'{size:.2f} {unit}'
        size /= 1024.0
    return f'{size:.2f} GiB'

def _process_rss() -> str:
    try:
        import resource
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_bytes = rss * 1024 if os.name != 'darwin' else rss
        return _format_size(float(rss_bytes))
    except Exception:
        return 'Unavailable'

def _nori_api_status() -> str:
    try:
        with open(config.SITE_DATA_PATH / 'api_usage_today.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        endpoints = data.get('endpoints', {})
        return 'Online' if isinstance(endpoints, dict) and endpoints else 'Unavailable'
    except Exception:
        return 'Unavailable'

def _status_label(value: bool) -> str:
    return 'Online' if value else 'Unavailable'

@loader.command
class CheckStatus(lightbulb.SlashCommand, name='status', description='Check bot status'):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        current, peak = tracemalloc.get_traced_memory()
        restart_ts = int(config.deploy_time) if config.deploy_time else int(time.time())
        status_embed = hikari.Embed(title='Nori Status', color='#FFFFFF', timestamp=datetime.now().astimezone())
        status_embed.add_field('Runtime', f'Status: **Online**\nMode: **{config.MODE}**\nVersion: **{config.VERSION}**\nLast restarted: <t:{restart_ts}:R>\nUptime: {get_uptime(config.deploy_time)}', inline=False)
        status_embed.add_field('Memory', f'Process RSS: **{_process_rss()}**\nPython allocated: **{_format_size(float(current))}**\nPython peak: **{_format_size(float(peak))}**', inline=False)
        status_embed.add_field('Nori API', f'**{_nori_api_status()}**', inline=True)
        status_embed.add_field('Refresh Tasks', '\n'.join([f'Lootpool: **{_status_label(config.lootpool_refresh_started)}**', f'Raid pool: **{_status_label(config.raid_pool_refresh_started)}**', f'Gambits: **{_status_label(config.gambit_refresh_started)}**', f'Item DB: **{_status_label(config.item_db_refresh_started)}**']), inline=True)
        status_embed.set_footer('Nori Bot - Status')
        await ctx.respond(embed=status_embed)

@loader.command
class ChangeMode(lightbulb.SlashCommand, name='mode', description='Change operation mode (Owner only)', hooks=[lightbulb.prefab.owner_only]):
    type = lightbulb.string('type', 'Select a mode', choices=lb_choices(config.MODE_LIST))

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        mode_choice = self.type
        config.mode = mode_choice
        if mode_choice == config.MODE_LIST[3]:
            status = hikari.Status.ONLINE
        else:
            status = hikari.Status.DO_NOT_DISTURB
        await ctx.client.app.update_presence(activity=hikari.Activity(name=f'{config.mode} mode', type=hikari.ActivityType.PLAYING), status=status)
        await ctx.respond(f'Operation mode changed to `{config.mode}`')

@loader.command
class PrintHello(lightbulb.SlashCommand, name='hi', description='say hello back'):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        user = await ctx.client.app.rest.fetch_user(ctx.user.id)
        responses = OWNER_HI_RESPONSES if int(ctx.user.id) == config.BOT_OWNER_ID else GENERAL_HI_RESPONSES
        await ctx.respond(random.choice(responses).format(user=user))

@loader.command
class BotSay(lightbulb.SlashCommand, name='say', description='Now we talking', hooks=[lightbulb.prefab.owner_only]):
    channel = lightbulb.string('channel', 'Channel ID')
    content = lightbulb.string('content', 'Text content')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        channel_id = self.channel
        text = self.content
        try:
            channel_name = await ctx.client.app.rest.fetch_channel(channel_id)
            await ctx.client.app.rest.create_message(channel=channel_id, content=text, user_mentions=True, role_mentions=True)
            await ctx.respond(f'Message `{text}` sent to channel `{channel_name}`')
        except Exception as error:
            await ctx.respond(f'Message cannot be sent, {error}.')

@loader.command
class GetProfile(lightbulb.SlashCommand, name='profile', description='Get user profile'):
    user_id = lightbulb.user('user_id', 'User ID')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        try:
            username = self.user_id
            if not isinstance(username, hikari.User):
                username = await ctx.client.app.rest.fetch_user(self.user_id)
            user_pfp = username.make_avatar_url()
            username_display = username.username
            user_created = datetime.strptime(str(username.created_at).split('.')[0], '%Y-%m-%d %H:%M:%S')
            user_flags = [flag for flag in username.flags]
            profile_embed = hikari.Embed(title=username_display, color='#EAEAEA')
            if user_pfp:
                profile_embed.set_image(user_pfp)
            profile_embed.add_field('Account created at', str(user_created))
            profile_embed.add_field('Badges', ''.join((f'{str(flag)}\n' for flag in user_flags)) if user_flags else 'N/A')
            try:
                roles = ''
                guild = await ctx.client.app.rest.fetch_guild(ctx.guild_id)
                guild_icon = guild.make_icon_url()
                user_in_server = await ctx.client.app.rest.fetch_member(guild, username)
                user_joined = datetime.strptime(str(user_in_server.joined_at).split('.')[0], '%Y-%m-%d %H:%M:%S')
                user_roles = user_in_server.get_roles()
                for role in user_roles:
                    if 'everyone' not in role.name:
                        roles += role.name + '\n'
                if roles:
                    profile_embed.add_field('Server Member since', str(user_joined))
                    profile_embed.add_field(f'Roles in {guild.name}', roles)
                    if guild_icon:
                        profile_embed.set_thumbnail(guild_icon)
            except Exception as error:
                print(error)
            await ctx.respond(embed=profile_embed)
        except Exception as error:
            print(error)
            await ctx.respond('Invalid user ID')
