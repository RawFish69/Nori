"""Portal command for Nori web tools and apps."""

import hikari
import lightbulb

from lib.utils import check_user_access

UTILS_URL = "https://nori.fish/utils"
DEMO_URL = "https://nori.fish/demo/"
ROBOTICS_URL = "https://nori.fish/robotics/"

APP_CATEGORIES = [
    (
        "Games & Simulators",
        [
            ("Space Orbs", "https://game.nori.fish"),
            ("FPV Drone Simulator", "https://nori.fish/demo/fpv"),
            ("PID Controller Visualizer", "https://nori.fish/demo/pid"),
        ],
    ),
    (
        "Developer Tools",
        [
            ("System Analyzer", f"{UTILS_URL}#system-analyzer"),
            ("JSON Formatter", f"{UTILS_URL}#json-tool"),
            ("Timestamp Converter", f"{UTILS_URL}#timestamp"),
            ("Regex Tester", f"{UTILS_URL}#regex-tester"),
        ],
    ),
    (
        "Media & Design",
        [
            ("3D Model Converter", f"{UTILS_URL}#model-viewer"),
            ("Image Converter", f"{UTILS_URL}#image-converter"),
            ("QR Generator", f"{UTILS_URL}#qr-code"),
            ("Color Picker", f"{UTILS_URL}#color-picker"),
        ],
    ),
    (
        "Converters",
        [
            ("HTML Minifier", f"{UTILS_URL}#html-minifier"),
            ("CSS Minifier", f"{UTILS_URL}#css-minifier"),
            ("MP4 to GIF", f"{UTILS_URL}#mp4-to-gif"),
            ("Video Compressor", f"{UTILS_URL}#video-compressor"),
        ],
    ),
    (
        "Web & Productivity",
        [
            ("Crypto Tracker", f"{UTILS_URL}#crypto-tracker"),
            ("World Clock", f"{UTILS_URL}#world-clock"),
            ("YouTube Helper", f"{UTILS_URL}#youtube-helper"),
        ],
    ),
    (
        "Security & Encoding",
        [
            ("Password Generator", f"{UTILS_URL}#password-gen"),
            ("Hash & Encode", f"{UTILS_URL}#hash-tool"),
            ("UUID Generator", f"{UTILS_URL}#uuid-gen"),
            ("URL Encoder", f"{UTILS_URL}#url-encoder"),
        ],
    ),
    (
        "Text & Notes",
        [
            ("Quick Notes", f"{UTILS_URL}#notes"),
            ("Markdown Preview", f"{UTILS_URL}#markdown-preview"),
            ("Text Toolkit", f"{UTILS_URL}#text-toolkit"),
            ("Lorem Ipsum", f"{UTILS_URL}#lorem"),
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

    embed.add_field("Demos", f"[nori.fish/demo]({DEMO_URL})", inline=True)
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
