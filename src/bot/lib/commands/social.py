"""Social and status commands."""
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
    "Welcome back, {user}. All systems are operational.",
    "Good evening, {user}. I have the bot under control.",
    "{user} detected. Administrative authority confirmed.",
    "At your service, sir.",
    "Systems nominal. Awaiting your instructions, {user}.",
    "Hello, {user}. The deployment appears stable for the moment.",
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

async def _nori_api_ping() -> tuple[str, int, str]:
    """Live HTTP check. Returns (label, status_code, latency_str)."""
    import httpx
    url = f'{config.NORI_API_BASE_URL}/api/usage'
    headers = {'Authorization': config.NORI_API_USAGE_TOKEN} if config.NORI_API_USAGE_TOKEN else {}
    try:
        t0 = time.monotonic()
        async with httpx.AsyncClient(timeout=5.0) as http:
            resp = await http.get(url, headers=headers)
        latency = int((time.monotonic() - t0) * 1000)
        label = 'Online' if resp.status_code == 200 else 'Degraded'
        return label, resp.status_code, f'{latency}ms'
    except Exception:
        return 'Unavailable', 0, '—'

def _status_label(value: bool) -> str:
    return 'Online' if value else 'Unavailable'

def _pool_timing() -> dict:
    import json as _json
    out = {}
    for key, path in (
        ('lootpool', config.WEEKLY_LOOTPOOL_FILE),
        ('raid_pool', config.WEEKLY_RAID_POOL_FILE),
        ('gambit',   config.GAMBIT_POOL_FILE),
    ):
        try:
            with open(path, encoding='utf-8') as f:
                d = _json.load(f)
            last = d.get('RefreshedAt') or d.get('Timestamp')
            if key == 'gambit':
                nxt = d.get('RotationEnd')
            else:
                ts = d.get('Timestamp')
                nxt = (ts + config.SECONDS_PER_WEEK) if ts else None
            out[key] = (int(last) if last else None, int(nxt) if nxt else None)
        except Exception:
            out[key] = (None, None)
    return out

def _ts_fields(last: int | None, nxt: int | None, next_label: str = 'next') -> str:
    parts = []
    if last:
        parts.append(f'last <t:{last}:R>')
    if nxt:
        parts.append(f'{next_label} <t:{nxt}:R>')
    return ' · '.join(parts) if parts else ''

@loader.command
class CheckStatus(lightbulb.SlashCommand, name='status', description='Check bot status'):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        restart_ts = int(config.deploy_time) if config.deploy_time else int(time.time())
        is_owner = int(ctx.user.id) == config.BOT_OWNER_ID

        status_embed = hikari.Embed(title='Nori Status', color='#FFFFFF')
        status_embed.add_field(
            'Runtime',
            f'Status: **Online**\nMode: **{config.MODE}**\nVersion: **{config.VERSION}**\n'
            f'Last restarted: <t:{restart_ts}:R>\nUptime: {get_uptime(config.deploy_time)}',
            inline=False,
        )

        if is_owner:
            if not tracemalloc.is_tracing():
                tracemalloc.start()
            current, peak = tracemalloc.get_traced_memory()
            status_embed.add_field(
                'Memory',
                f'Process RSS: **{_process_rss()}**\n'
                f'Python allocated: **{_format_size(float(current))}**\n'
                f'Python peak: **{_format_size(float(peak))}**',
                inline=False,
            )

            api_label, api_code, api_latency = await _nori_api_ping()
            code_display = f' `{api_code}`' if api_code else ''
            try:
                bot = ctx.client.app
                shard_count = bot.shard_count
                guild_count = len(bot.cache.get_guilds_view()) if bot.cache else '—'
                gw_latency = f'{bot.heartbeat_latency * 1000:.0f}ms' if bot.heartbeat_latency else '—'
            except Exception:
                shard_count, guild_count, gw_latency = '—', '—', '—'
            status_embed.add_field(
                'Nori API',
                f'**{api_label}**{code_display} — {api_latency}',
                inline=True,
            )
            status_embed.add_field(
                'Bot Stats',
                f'Shards: **{shard_count}**\nGuilds: **{guild_count}**',
                inline=True,
            )
            status_embed.add_field(
                'Discord Health',
                f'Gateway: **{gw_latency}**',
                inline=True,
            )
            status_embed.add_field(
                'Session',
                f'Commands: **{config.command_count}**',
                inline=True,
            )
            timing = _pool_timing()
            lp_last, lp_nxt = timing.get('lootpool', (None, None))
            rp_last, rp_nxt = timing.get('raid_pool', (None, None))
            gb_last, gb_nxt = timing.get('gambit', (None, None))
            def _task_line(label: str, online: bool, last: int | None, nxt: int | None, next_label: str = 'next') -> str:
                ts = _ts_fields(last, nxt, next_label)
                return f'{label}: **{_status_label(online)}**' + (f' · {ts}' if ts else '')
            item_count = len(config.item_map) if config.item_map else 0
            item_db_ts = f' · last updated <t:{config.item_db_last_updated}:R>' if config.item_db_last_updated else ''
            status_embed.add_field(
                'Refresh Tasks',
                '\n'.join([
                    _task_line('Lootpool', config.lootpool_refresh_started, lp_last, lp_nxt),
                    _task_line('Raid pool', config.raid_pool_refresh_started, rp_last, rp_nxt),
                    _task_line('Gambits', config.gambit_refresh_started, gb_last, gb_nxt, 'expires'),
                    f'Item DB: **{_status_label(config.item_db_refresh_started)}** · **{item_count}** items{item_db_ts}',
                ]),
                inline=False,
            )
        else:
            api_label, _, api_latency = await _nori_api_ping()
            status_embed.add_field('Nori API', f'**{api_label}** — {api_latency}', inline=True)

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
