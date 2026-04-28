"""Nori bot information and help commands."""

import hikari
import lightbulb

import lib.config as config
from lib.config import MODE, NORI_API_BASE_URL, VERSION
from lib.utils import check_user_access, get_uptime

HELP_SECTIONS = [
    (
        "Wynncraft Stats",
        [
            ("player", "Player stats"),
            ("guild", "Guild stats"),
            ("lb raid", "Raid leaderboard"),
            ("lb stat", "Stat leaderboard"),
            ("online", "Player activity"),
        ],
    ),
    (
        "Items",
        [
            ("item search", "Find item data"),
            ("item roll", "ID simulator"),
            ("item weigh", "Auto mythic weigh"),
            ("item evaluate", "Manual mythic weigh"),
            ("item lootpool", "Weekly lootpool"),
        ],
    ),
    (
        "Loot & Raids",
        [
            ("raid gambit", "Daily gambits"),
            ("raid aspect", "Weekly aspects"),
            ("raid item", "Weekly raid items"),
        ],
    ),
    (
        "Builds & Recipes",
        [
            ("build search", "Find builds"),
            ("build submit", "Submit build"),
            ("recipe search", "Find recipes"),
            ("recipe submit", "Submit recipe"),
            ("ingredient search", "Find ingredients"),
        ],
    ),
    (
        "Utilities",
        [
            ("portal", "Nori web apps"),
            ("gxp", "Guild XP graph"),
            ("hq", "HQ tower stats"),
            ("tower", "Tower stats"),
            ("pingme", "Reminder ping"),
            ("weather", "City weather"),
        ],
    ),
    (
        "Bot",
        [
            ("nori", "Bot info"),
            ("help", "Command menu"),
            ("status", "Runtime status"),
            ("profile", "User profile"),
            ("ping", "Latency check"),
        ],
    ),
]


def _command_list(commands: list[tuple[str, str]]) -> str:
    return "\n".join(f"`/{name}` - {summary}" for name, summary in commands)



def load_help_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load top-level `/nori` and `/help` commands."""

    @bot.command()
    @lightbulb.command("nori", "Nori bot information")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def nori_cmd(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        uptime_str = get_uptime(config.deploy_time)
        restart_ts = int(config.deploy_time)
        nori_embed = hikari.Embed(
            title="Multi-purpose Utility Bot",
            color="#FFFFFF",
        )
        nori_embed.add_field(
            "Status",
            f"**Online**\nMode: **{MODE}**\nLast restarted: <t:{restart_ts}:R>\nUptime: {uptime_str}",
            inline=False,
        )
        nori_embed.add_field(
            "Links",
            f"[Nori-Web]({NORI_API_BASE_URL})\n"
            "[Support server](https://discord.gg/tU7eaKAWb2)\n"
            "[Add Nori to your server](https://discord.com/application-directory/873677970928193568)\n"
            "[GitHub](https://github.com/RawFish69/Nori)",
            inline=False,
        )
        nori_embed.add_field("Version", VERSION, inline=True)
        nori_embed.add_field("Developer", "[RawFish](https://github.com/RawFish69)", inline=True)
        nori_embed.add_field("Maintainer", "[RawFish](https://github.com/RawFish69)", inline=True)
        try:
            nori_user = await bot.rest.fetch_user(873677970928193568)
            nori_embed.set_thumbnail(nori_user.make_avatar_url())
        except Exception:
            pass
        nori_embed.set_footer("Nori Bot - Wynncraft Utility Bot")
        await ctx.respond(embed=nori_embed)

    @bot.command()
    @lightbulb.command("help", "Shows this bot's help menu.")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def help_cmd(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        help_embed = hikari.Embed(
            title="Help Menu",
            color="#FFFFFF",
        )
        help_embed.add_field("Info", "`/nori`\nBot status and links", inline=True)
        help_embed.add_field("Portal", "`/portal`\nApps and utilities", inline=True)
        help_embed.add_field("Search", "Type `/` in Discord\nBrowse command list", inline=True)

        for section, commands in HELP_SECTIONS:
            help_embed.add_field(section, _command_list(commands), inline=True)

        help_embed.set_footer("Nori Bot - Help page")
        await ctx.respond(embed=help_embed)
