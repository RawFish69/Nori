"""Wynncraft stats commands."""

import re

import hikari
import lightbulb
import miru
from lib.utils import check_user_access
from lib.guild_utils import guild_stats
from lib.player_utils import player_stats
from lib.server_utils import get_server, get_uptime
from lib.config import user_lb_in_guild
from lib.views.guild import GuildStatsView


def _code_block(text: str, limit: int = 3800) -> str:
    text = text or "N/A"
    if len(text) > limit:
        text = text[:limit - 40].rstrip() + "\n... truncated"
    return f"```json\n{text}```"


def _world_region(world_id: str) -> str:
    match = re.match(r"([A-Za-z]+)", str(world_id or ""))
    region = match.group(1).upper() if match else "OTHER"
    return region if region in {"NA", "EU", "AS"} else "OTHER"


def _world_sort_key(world_id: str):
    region_order = {"NA": 0, "EU": 1, "AS": 2, "OTHER": 3}
    region = _world_region(world_id)
    number_match = re.search(r"(\d+)", str(world_id or ""))
    number = int(number_match.group(1)) if number_match else 9999
    return region_order.get(region, 3), number, str(world_id)


def _uptime_chunks(rows: list[str], size: int = 12) -> list[list[str]]:
    return [rows[index:index + size] for index in range(0, len(rows), size)]


def _build_uptime_rows(server_list: dict, server_time: dict) -> dict[str, list[str]]:
    valid_servers = set(server_list.keys()) & set(server_time.keys())
    grouped = {"NA": [], "EU": [], "AS": []}
    for world_id in sorted(valid_servers, key=_world_sort_key):
        region = _world_region(world_id)
        if region not in grouped:
            continue
        players = server_list[world_id]
        player_count = len(players) if isinstance(players, list) else int(players or 0)
        uptime_display = str(server_time[world_id][0])
        if "." in uptime_display:
            uptime_display = uptime_display.split(".", 1)[0]
        grouped[region].append(
            f"| {world_id:5s} | {player_count:7d} | {uptime_display:>8s} |"
        )
    return grouped


def _build_uptime_embed(grouped: dict[str, list[str]], region: str = "NA") -> hikari.Embed:
    region = region if region in {"NA", "EU", "AS"} else "NA"
    web_page = f"[Uptime on Nori-Web](https://nori.fish/wynn/uptime/)"
    uptime_embed = hikari.Embed(
        title=f"Wynncraft {region} World List",
        description=web_page,
        color="#C0FF88",
    )
    rows = grouped.get(region, [])
    header = "| World | Players |  Uptime  |\n+-------+---------+----------+\n"
    if rows:
        for chunk_index, chunk in enumerate(_uptime_chunks(rows), start=1):
            field_name = f"{region} Worlds" if chunk_index == 1 else f"{region} Worlds ({chunk_index})"
            uptime_embed.add_field(field_name, f"```json\n{header}{chr(10).join(chunk)}```", inline=False)
    else:
        uptime_embed.add_field(f"{region} Worlds", "No online worlds found for this region.")
    counts = " | ".join(f"{name}: {len(grouped.get(name, []))}" for name in ["NA", "EU", "AS"])
    uptime_embed.add_field("Regions", counts, inline=False)
    uptime_embed.set_footer("Nori Bot - Server Uptime")
    return uptime_embed


class UptimeRegionView(miru.View):
    def __init__(self, grouped: dict[str, list[str]], timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.grouped = grouped

    @miru.button(label="NA", style=hikari.ButtonStyle.PRIMARY)
    async def button_na(self, button: miru.Button, ctx: miru.Context):
        await ctx.edit_response(embed=_build_uptime_embed(self.grouped, "NA"), components=self.build())

    @miru.button(label="EU", style=hikari.ButtonStyle.SECONDARY)
    async def button_eu(self, button: miru.Button, ctx: miru.Context):
        await ctx.edit_response(embed=_build_uptime_embed(self.grouped, "EU"), components=self.build())

    @miru.button(label="AS", style=hikari.ButtonStyle.SECONDARY)
    async def button_as(self, button: miru.Button, ctx: miru.Context):
        await ctx.edit_response(embed=_build_uptime_embed(self.grouped, "AS"), components=self.build())

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as error:
            print(f"uptime region view timeout update failed: {error}")


def load_wynn_stats_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load Wynncraft stats commands."""
    
    @bot.command()
    @lightbulb.option('name', 'Guild Prefix or Full Name')
    @lightbulb.command('guild', 'Search a Guild\'s Stats')
    @lightbulb.implements(lightbulb.SlashCommand)
    async def guild_cmd(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        user_id = ctx.user.id
        user_input = ctx.options.name
        default_embed = hikari.Embed(title=f"Loading guild stats for `{user_input}`...", color="#AEB1B1")
        await ctx.respond(embed=default_embed)

        try:
            guild_data = guild_stats(user_input)
            display = guild_data[0]
            guild_name = guild_data[1]
            guild_prefix = guild_data[2]
            banner_tier = guild_data[3]
            banner_structure = guild_data[4]
            online_display = guild_data[5]
            web_page = f"[Full Guild Stats on Nori-Web](https://nori.fish/wynn/guild/)"
            guild_embed = hikari.Embed(title=f"[{guild_prefix}] {guild_name}", description=web_page,
                                       color="#5EFB6E")
            guild_embed.set_footer(text=f"Nori Bot - Wynn Stats")
            guild_embed.add_field("Main Info", f"```json\n{display}```", inline=False)
            guild_embed.add_field("Banner", f"Tier {banner_tier} {banner_structure}", inline=False)
            online_embed = hikari.Embed(
                title=f"Online Members - [{guild_prefix}] {guild_name}",
                description=f"{web_page}\n{_code_block(online_display)}",
                color="#5EFB6E",
            )
            online_embed.add_field("Banner", f"Tier {banner_tier} {banner_structure}", inline=False)
            online_embed.set_footer(text="Nori Bot - Wynn Stats")
            user_lb_in_guild[user_id] = {
                'guild_prefix': guild_prefix,
                'category': None,
                'page': 0
            }

            view = GuildStatsView(guild_embed, online_embed)
            message = await ctx.edit_last_response(embed=guild_embed, content="", components=view.build())
            await view.start(message)

        except Exception as error:
            print(error)
            match_embed = hikari.Embed(title='Cannot find target guild', description='Please enter a valid name or prefix', color="#FF0000")
            await ctx.edit_last_response(embed=match_embed)

    @bot.command()
    @lightbulb.option('name', 'Player In Game Name')
    @lightbulb.command('player', 'Search a Player\'s Stats')
    @lightbulb.implements(lightbulb.SlashCommand)
    async def player_cmd(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        default_embed = hikari.Embed(title=f"Loading player stats for `{ctx.options.name}`...", color="#AEB1B1")
        await ctx.respond(embed=default_embed)
        try:
            from lib.player_utils import player_stats
            stats = player_stats(ctx.options.name)
            player_stats_display = stats[0]
            online_status = stats[1]
            player_uuid = stats[2]
            embed_color = "#FF0000"
            if online_status is True:
                embed_color = "#5EFB6E"
            link = f"[All character stats on Nori-Web](https://nori.fish/wynn/player/?player={ctx.options.name})"
            player_embed = hikari.Embed(title=f"{ctx.options.name}", description=link, color=embed_color)
            player_embed.add_field("Profile", player_stats_display["profile"], inline=False)
            player_embed.add_field("Progress", player_stats_display["progress"], inline=True)
            player_embed.add_field("Gameplay", player_stats_display["gameplay"], inline=True)
            player_embed.add_field("Raid Stats", player_stats_display["raid_stats"], inline=True)
            player_embed.add_field("Raid Clears", player_stats_display["raids"], inline=False)
            if player_stats_display.get("guild_history"):
                player_embed.add_field("Guild History", player_stats_display["guild_history"], inline=False)
            player_embed.add_field("UUID", f"`{player_uuid}`", inline=False)
            try:
                player_embed.set_thumbnail(f"https://visage.surgeplay.com/face/256/{player_uuid}")
            except Exception as error:
                print(f"player skin fetch error: {error}")
                pass
            player_embed.set_footer("Nori Bot - Wynn Stats")
            await ctx.edit_last_response(embed=player_embed)
        except Exception as error:
            print(error)
            line_b = f"Error occurred while searching for player `{ctx.options.name}`\n"
            line_b += f"Double check spelling, name search is case-sensitive\n"
            line_b += f"For any issue, contact the support server."
            match_embed = hikari.Embed(title="Player not found.", description=line_b, color="#AEB1B1")
            await ctx.edit_last_response(embed=match_embed)

    @bot.command()
    @lightbulb.command('uptime', 'List of Wynncraft servers')
    @lightbulb.implements(lightbulb.SlashCommand)
    async def server_list(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        await ctx.respond("Loading Wynncraft uptime...", flags=hikari.MessageFlag.LOADING)
        serverList = get_server()
        serverTime = get_uptime()
        grouped = _build_uptime_rows(serverList, serverTime)
        uptime_embed = _build_uptime_embed(grouped, "NA")
        view = UptimeRegionView(grouped)
        message = await ctx.edit_last_response(embed=uptime_embed, content="", components=view.build())
        await view.start(message)

    @bot.command()
    @lightbulb.option('level', "XP require for this level", required=False, type=int)
    @lightbulb.command('gxp', 'Guild XP related graphs')
    @lightbulb.implements(lightbulb.SlashCommand)
    async def gxp(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        from lib.views.guild import gxpView
        text = ""
        if ctx.options.level:
            level = ctx.options.level
            cumulative = 0
            total_xp = ""
            req = round(1.15 ** (int(level) - 1) * (20000 + 20000 / 0.15) - 20000 / 0.15)
            xp = ""
            if req >= 1_000_000_000_000:
                xp = '{:.1f}T'.format(req / 1_000_000_000_000)
            elif req >= 1_000_000_000:
                xp = '{:.0f}B'.format(req / 1_000_000_000)
            elif req >= 1_000_000:
                xp = '{:.0f}M'.format(req / 1_000_000)
            elif req >= 1_000:
                xp = '{:.0f}K'.format(req / 1_000)
            text += f"Required XP at Level `{level}`: `{xp}` or `{req}`\n"
            for lvl in range(1, level + 1):
                cumulative += round(1.15 ** (int(lvl) - 1) * (20000 + 20000 / 0.15) - 20000 / 0.15)
            if cumulative >= 1_000_000_000_000:
                total_xp = '{:.1f}T'.format(cumulative / 1_000_000_000_000)
            elif cumulative >= 1_000_000_000:
                total_xp = '{:.0f}B'.format(cumulative / 1_000_000_000)
            elif cumulative >= 1_000_000:
                total_xp = '{:.0f}M'.format(cumulative / 1_000_000)
            elif cumulative >= 1_000:
                total_xp = '{:.0f}K'.format(cumulative / 1_000)
            text += f"Cumulative [Level `1` - `{level}`]: `{total_xp}` or `{cumulative}` XP\n"
            text += "Please select the level range to see the plots."
        else:
            text += "Please select the level range to see the plots."
        gxp_view = gxpView(timeout=120)
        message = await ctx.respond(text, components=gxp_view.build())
        message = await message
        await gxp_view.start(message)
        await gxp_view.wait()

    @bot.command()
    @lightbulb.command('lb', 'Leaderboard')
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def leaderboard(ctx: lightbulb.Context):
        pass

    @leaderboard.child()
    @lightbulb.command('raid', 'View raid leaderboard')
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def lb_raid(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        from lib.config import lb_user_cache
        from lib.views.leaderboard import raidView
        user = await bot.rest.fetch_user(ctx.user.id)
        username = user.username
        lb_user_cache[username] = {"type": "", "page": 1}
        view = raidView(timeout=60)
        msg = '```json\n'
        title_line = 'Wynncraft Raid Leaderboard [Global]\n'
        description_line = "Per-raid clears or aggregate raid metrics"
        msg += 'Clears\n'
        msg += '  1. TNA - The Nameless Anomaly\n'
        msg += '  2. TCC - The Canyon Colossus\n'
        msg += '  3. NoL - Nexus of Light\n'
        msg += '  4. NoG - Nest of the Grootslangs\n'
        msg += '  5. TWP - The Wartorn Palace\n'
        msg += '  6. All - Total Raid clears\n'
        msg += 'Metrics (global aggregates)\n'
        msg += '  7. Damage Dealt\n'
        msg += '  8. Damage Taken\n'
        msg += '  9. Healing\n'
        msg += ' 10. Deaths\n'
        msg += ' 11. Buffs Taken\n'
        msg += ' 12. Gambits Used\n```'
        raid_embed = hikari.Embed(title=title_line, description=description_line, color="#93FEFD")
        raid_embed.add_field("Information:", f"{msg}")
        raid_embed.set_thumbnail("https://cdn.wynncraft.com/nextgen/wynncraft_icon.png")
        web_page = (
            "[Unified Raid Leaderboard on Nori-Web]"
            "(https://nori.fish/wynn/leaderboard/?type=raids&category=all&page=1)"
        )
        raid_embed.add_field("Leaderboard on Web Browser", f"{web_page}")
        raid_embed.set_footer("Nori Bot - Wynn Raid Leaderboard")
        message = await ctx.respond(embed=raid_embed, components=view.build())
        message = await message
        await view.start(message)
        await view.wait()

    @leaderboard.child()
    @lightbulb.command('stat', 'View stat leaderboard')
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def lb_stat(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        from lib.config import lb_user_cache
        from lib.views.leaderboard import statView
        user = await bot.rest.fetch_user(ctx.user.id)
        username = user.username
        lb_user_cache[username] = {"type": "", "page": 1}
        view = statView(timeout=60)
        msg = '```json\n'
        title_line = 'Wynncraft Leaderboard [Global]\n'
        description_line = f"Select a leaderboard category"
        msg += '1. Chest Opened\n'
        msg += '2. Mobs Killed\n'
        msg += '3. Wars Completed\n'
        msg += '4. Dungeon Clears\n'
        msg += '5. Playtime\n'
        msg += '6. PvP Kills\n'
        msg += '7. Quests Completed\n'
        msg += '8. Total Levels\n```'
        stat_embed = hikari.Embed(title=title_line, description=description_line, color="#93FEFD")
        stat_embed.add_field("Information:", f"{msg}")
        stat_embed.set_thumbnail("https://cdn.wynncraft.com/nextgen/wynncraft_icon.png")
        web_page = f"[Stats Leaderboards on Nori-Web](https://nori.fish/wynn/leaderboard/?type=stats&category=chests&page=1)"
        stat_embed.add_field("Leaderboard on Web Browser", f"{web_page}")
        stat_embed.set_footer("Nori Bot - Wynn Stats Leaderboard")
        message = await ctx.respond(embed=stat_embed, components=view.build())
        message = await message
        await view.start(message)
        await view.wait()

    @leaderboard.child()
    @lightbulb.command('profession', 'Profession Leaderboard')
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def prof_lb(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        from lib.views.leaderboard import prof_view
        display = prof_view(timeout=120)
        web_page = f"[Profession Leaderboards on Nori-Web](https://nori.fish/wynn/leaderboard/?type=professions&category=professionsGlobal&page=1)"
        message = await ctx.respond(f'{web_page}\nSelect a profession', components=display.build())
        message = await message
        await display.start(message)
        await display.wait()

