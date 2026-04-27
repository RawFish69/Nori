"""Portal command for Nori web tools and apps."""

import hikari
import lightbulb

from lib.utils import check_user_access

UTILS_URL = "https://nori.fish/utils/"
DEMO_URL = "https://nori.fish/demo/"
ROBOTICS_URL = "https://nori.fish/robotics/"

APP_CATEGORIES = [
    (
        "Games & Simulators",
        [
            ("Space Orbs", DEMO_URL),
            ("FPV Drone Simulator", DEMO_URL),
            ("PID Controller Visualizer", DEMO_URL),
        ],
    ),
    (
        "Developer Tools",
        [
            ("System Analyzer", UTILS_URL),
            ("JSON Formatter", UTILS_URL),
            ("Timestamp Converter", UTILS_URL),
            ("Regex Tester", UTILS_URL),
        ],
    ),
    (
        "Media & Design",
        [
            ("3D Model Converter", UTILS_URL),
            ("Image Converter", UTILS_URL),
            ("QR Generator", UTILS_URL),
            ("Color Picker", UTILS_URL),
        ],
    ),
    (
        "Converters",
        [
            ("HTML Minifier", UTILS_URL),
            ("CSS Minifier", UTILS_URL),
            ("MP4 to GIF", UTILS_URL),
            ("Video Compressor", UTILS_URL),
        ],
    ),
    (
        "Web & Productivity",
        [
            ("Crypto Tracker", UTILS_URL),
            ("World Clock", UTILS_URL),
            ("YouTube Helper", UTILS_URL),
        ],
    ),
    (
        "Security & Encoding",
        [
            ("Password Generator", UTILS_URL),
            ("Hash & Encode", UTILS_URL),
            ("UUID Generator", UTILS_URL),
            ("URL Encoder", UTILS_URL),
        ],
    ),
    (
        "Text & Notes",
        [
            ("Quick Notes", UTILS_URL),
            ("Markdown Preview", UTILS_URL),
            ("Text Toolkit", UTILS_URL),
            ("Lorem Ipsum", UTILS_URL),
        ],
    ),
]


def _link_list(links: list[tuple[str, str]]) -> str:
    return "\n".join(f"[{label}]({url})" for label, url in links)


def _portal_embed() -> hikari.Embed:
    embed = hikari.Embed(
        title="Nori Web Portal",
        color="#FFFFFF",
    )

    embed.add_field("Apps", f"[nori.fish/demo]({DEMO_URL})", inline=True)
    embed.add_field("Robotics", f"[nori.fish/robotics]({ROBOTICS_URL})", inline=True)
    embed.add_field("Utilities", f"[nori.fish/utils]({UTILS_URL})", inline=True)

    for category, links in APP_CATEGORIES:
        embed.add_field(category, _link_list(links), inline=True)

    embed.set_footer("Nori Bot - Portal")
    return embed


def load_portal_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load Nori portal command."""

    @bot.command()
    @lightbulb.command("portal", "Browse Nori web apps, robotics, and utilities")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def portal(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        await ctx.respond(embed=_portal_embed())
