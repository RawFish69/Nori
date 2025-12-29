"""Wynncraft stats commands."""

import hikari
import lightbulb
from lib.utils import check_user_access
from lib.guild_utils import guild_stats
from lib.player_utils import player_stats
from lib.server_utils import get_server, get_uptime
from lib.config import user_lb_in_guild, lb_in_guild
from lib.views.leaderboard import GuildLeaderboardView


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
            web_page = f"[Full Guild Stats on Nori-Web](https://nori.fish/wynn/guild/)"
            guild_embed = hikari.Embed(title=f"Banner: Tier {banner_tier} {banner_structure}", description=web_page,
                                       color="#5EFB6E")
            guild_embed.set_footer(text=f"Nori Bot - Wynn Stats")
            user_lb_in_guild[user_id] = {
                'guild_prefix': guild_prefix,
                'category': None,
                'page': 0
            }

            if guild_prefix in lb_in_guild:
                view = GuildLeaderboardView(user_id)
                message = await ctx.edit_last_response(embed=guild_embed, content=f"```json\n{display}```", components=view)
                await view.start(message)
            else:
                await ctx.edit_last_response(embed=guild_embed, content=f"```json\n{display}```")

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
            playerStats = stats[0]
            online_status = stats[1]
            player_uuid = stats[2]
            embed_color = "#FF0000"
            if online_status is True:
                embed_color = "#5EFB6E"
            link = f"[All character stats on Nori-Web](https://nori.fish/wynn/player/?player={ctx.options.name})"
            player_embed = hikari.Embed(title=f"{ctx.options.name}", description=link, color=embed_color)
            player_embed.add_field(f"UUID: {player_uuid}", f"```json\n{playerStats}```")
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
        index = 0
        field_count = 0
        display_index = 1
        showed_servers = 20
        serverList = get_server()
        serverTime = get_uptime()
        response = ''
        web_page = f"[Uptime on Nori-Web](https://nori.fish/wynn/uptime/)"
        uptime_embed = hikari.Embed(title="Wynncraft World List",
                                    description=web_page,
                                    color="#C0FF88")
        header = '```json\n| #  | Server | Players  |  Uptime  |\n'
        header += "+----+--------+----------+----------+```"
        uptime_embed.add_field("Server uptime", header)
        valid_servers = set(serverList.keys()) & set(serverTime.keys())
        for server in sorted(valid_servers, key=lambda x: serverTime[x][0]):
            if index < showed_servers:
                world_ID = server
                player_count = serverList[world_ID]
                uptime_hours = serverTime[world_ID][0]
                uptime_minutes = serverTime[world_ID][1]
                response += f"| {display_index:2d} | {world_ID:6s} | {player_count:8d} | {uptime_hours:2d}h {uptime_minutes:2d}m |\n"
                index += 1
                display_index += 1
                if index % 5 == 0:
                    field_count += 1
                    uptime_embed.add_field(f"Servers {field_count * 5 - 4}-{field_count * 5}", f"```json\n{response}```")
                    response = ''
        if response:
            field_count += 1
            uptime_embed.add_field(f"Servers {field_count * 5 - 4}-{index}", f"```json\n{response}```")
        uptime_embed.set_footer("Nori Bot - Server Uptime")
        await ctx.respond(embed=uptime_embed)

    @bot.command()
    @lightbulb.command('soul', 'Soul point timer')
    @lightbulb.implements(lightbulb.SlashCommand)
    async def soul_point(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        from lib.server_utils import soul_timer
        timer = soul_timer()
        web_page = f"[Soul Point Timer on Nori-Web](https://nori.fish/wynn/uptime/)"
        soul_embed = hikari.Embed(title="Soul Point Timer",
                                  description=f"Latency is expected, use the time order as a reference.\n{web_page}", color="#A5F1FF")
        soul_embed.add_field("Timer:", f"{timer}")
        soul_embed.set_footer("Nori Bot - Soul Point Timer")
        await ctx.respond(embed=soul_embed)

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
        title_line = 'Wynncraft Raid Report [Global]\n'
        description_line = f"Select a leaderboard category"
        msg += '1. TNA - The Nameless Anomaly\n'
        msg += '2. TCC - The Canyon Colossus\n'
        msg += '3. NoL - Nexus of Light\n'
        msg += '4. NoG - Nest of the Grootslangs\n'
        msg += '5. All - Total Raid clears\n```'
        raid_embed = hikari.Embed(title=title_line, description=description_line, color="#93FEFD")
        raid_embed.add_field("Information:", f"{msg}")
        raid_embed.set_thumbnail("https://cdn.wynncraft.com/nextgen/wynncraft_icon.png")
        web_page = f"[Raid Leaderboards on Nori-Web](https://nori.fish/wynn/leaderboard/?type=raids&category=raids_total&page=1)"
        raid_embed.add_field("Leaderboard on Web Browser", f"{web_page}")
        raid_embed.set_footer("Nori Bot - Wynn Raid Report")
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

