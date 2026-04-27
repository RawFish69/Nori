"""Raid lootpool command group."""

import time

import hikari
import lightbulb

import lib.config as config
from lib.config import (
    RAID_ITEM_TIERS,
    RAID_NAMES,
    RAID_WEB_URL,
    format_aspect_display,
    format_compacted_item_lines,
    format_ward_display,
)
from lib.raid_pool_utils import (
    _normalize_gambit_loot_shape,
    load_aspect_lootpool,
    load_gambit_pool,
    load_weekly_raid_pool,
)
from lib.utils import check_user_access
from lib.views.raid import aspectView, raidItemView

SECONDS_PER_WEEK = 604800


def load_raid_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load raid lootpool commands."""

    @bot.command()
    @lightbulb.command("raid", "Raid lootpool command group")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def raid(ctx: lightbulb.Context):
        pass

    @raid.child()
    @lightbulb.command("gambit", "View daily raid gambits")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def show_raid_gambits(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        await ctx.respond("Loading daily gambits...", flags=hikari.MessageFlag.LOADING)
        data = await load_gambit_pool()
        if not data:
            await ctx.edit_last_response(
                content="Gambit data is not available yet - the background refresh has not produced a file yet. Please check back shortly."
            )
            return

        gambits_all = _normalize_gambit_loot_shape(data.get("Loot", []))
        rotation_start = data.get("RotationStart")
        rotation_end = data.get("RotationEnd")
        refreshed_at = data.get("RefreshedAt")
        current_time = int(time.time())

        time_lines = []
        if isinstance(rotation_start, int):
            time_lines.append(f"Rotation started: <t:{rotation_start}:R>")
        if isinstance(rotation_end, int):
            time_lines.append(f"Next reset: <t:{rotation_end}:R>")
        if isinstance(refreshed_at, int):
            time_lines.append(f"Last synced: <t:{refreshed_at}:R>")
        description = "\n".join(time_lines + [f"[Raid Gambits on Nori-Web]({RAID_WEB_URL})"])

        gambit_embed = hikari.Embed(
            title="Daily Raid Gambit Rotation",
            description=description,
            color="#c0aaff",
        )

        rotation_expired = isinstance(rotation_end, int) and current_time >= rotation_end
        if rotation_expired:
            gambit_embed.add_field(
                "Rotation Refreshing",
                "The current rotation window has ended. Awaiting the next data refresh.\n"
                "If entries still do not change, data may be outdated - please remind a maintainer to verify it.",
            )
        elif gambits_all:
            lines = []
            for entry in gambits_all:
                if not isinstance(entry, dict):
                    continue
                name = entry.get("name", "?")
                description_text = entry.get("description") or ""
                lines.append(f"- **{name}**")
                if description_text:
                    lines.append(f"  {description_text}")
            gambit_embed.add_field("Shared Gambits (All Raids)", "\n".join(lines)[:1024] if lines else "N/A")
        else:
            gambit_embed.add_field(
                "No Gambits Yet",
                "No gambit data has been reported for this rotation yet.",
            )

        gambit_embed.set_footer("Nori Bot - Raid Gambits")
        gambit_embed.set_thumbnail("https://nori.fish/resources/aspect.gif")
        await ctx.edit_last_response(embed=gambit_embed, content="")

    @raid.child()
    @lightbulb.command("aspect", "View weekly raid aspect lootpool")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def show_raid_aspect_lootpool(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        await ctx.respond("Loading weekly raid aspects...", flags=hikari.MessageFlag.LOADING)
        data = await load_aspect_lootpool()
        aspects_all = data.get("Loot", {})
        aspect_icons = data.get("Icon", {})
        timestamp = data.get("Timestamp", int(time.time()))
        current_time = int(time.time())
        next_update = timestamp + SECONDS_PER_WEEK
        config.aspect_user[ctx.user.username] = "Mythic"

        description = (
            f"Starting <t:{timestamp}:D>\n"
            f"Next update: <t:{next_update}:R>\n"
            f"### [Raid Lootpool on Nori-Web]({RAID_WEB_URL}) ###"
        )
        loot_embed = hikari.Embed(title="Weekly Raid Aspect Rotation", description=description, color="#c0aaff")

        if current_time >= next_update:
            loot_embed.add_field(
                "New Aspect Info",
                "We are updating this week's new aspects.\n"
                "Raid aspect lootpool is a community supported feature, be patient as our contributors gather the information.\n"
                "If the pool still looks unchanged after refresh time, it may be outdated - please remind a maintainer to verify it.",
            )
            loot_embed.add_field(
                "Check Raid Lootpool in Web Browser",
                "Join our [support server](https://discord.com/invite/eDssA6Jbwd) to follow updates & patches for nori.\n"
                "The web version will update the same time as the bot, with much better display\n"
                "Try out other features on [Nori-Web](https://nori.fish/wynn/)\n"
                "Popular utility like **item analysis**, **item simulation**, **build/recpie search**, **leaderboards**, and more!",
            )
            await ctx.edit_last_response(embed=loot_embed, content="")
            return

        for raid_name in RAID_NAMES:
            aspects_in_pool = aspects_all.get(raid_name, {}) if isinstance(aspects_all, dict) else {}
            mythic_names = aspects_in_pool.get("Mythic", []) if isinstance(aspects_in_pool, dict) else []
            lines = [
                f"- {format_aspect_display(aspect_name, aspect_icons.get(aspect_name, ''))}"
                for aspect_name in mythic_names
            ]
            loot_embed.add_field(f"{raid_name} Mythic Aspects", "\n".join(lines) if lines else "N/A")

        loot_embed.set_footer("Nori Bot - Raid Aspect Lootpool")
        loot_embed.set_thumbnail("https://nori.fish/resources/aspect.gif")
        view = aspectView(timeout=120)
        message = await ctx.edit_last_response(embed=loot_embed, content="", components=view.build())
        await view.start(message)
        await view.wait()

    @raid.child()
    @lightbulb.command("item", "View weekly raid item lootpool")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def show_raid_item_lootpool(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        await ctx.respond("Loading weekly raid items...", flags=hikari.MessageFlag.LOADING)
        data = await load_weekly_raid_pool()
        raid_items_all = data.get("Loot", {})
        timestamp = data.get("Timestamp", int(time.time()))
        next_update = timestamp + SECONDS_PER_WEEK
        current_time = int(time.time())

        description = (
            f"Starting <t:{timestamp}:D>\n"
            f"Next update: <t:{next_update}:R>\n"
            f"### [Raid Lootpool on Nori-Web]({RAID_WEB_URL}) ###"
        )
        loot_embed = hikari.Embed(title="Weekly Raid Item Rotation", description=description, color="#c0aaff")

        if current_time >= next_update:
            loot_embed.add_field(
                "New Raid Item Info",
                "We are updating this week's new raid item pool.\n"
                "Raid item lootpool is a community supported feature, be patient as our contributors gather the information.\n"
                "If the pool still looks unchanged after refresh time, it may be outdated - please remind a maintainer to verify it.",
            )
            await ctx.edit_last_response(embed=loot_embed, content="")
            return

        any_data = False
        for raid_name in RAID_NAMES:
            raid_data = raid_items_all.get(raid_name, {}) if isinstance(raid_items_all, dict) else {}
            mythic_items = raid_data.get("Mythic", []) if isinstance(raid_data, dict) else []
            lines = format_compacted_item_lines(mythic_items, formatter=format_ward_display) if mythic_items else ["N/A"]
            loot_embed.add_field(f"{raid_name} Mythic Items", "\n".join(lines))
            if isinstance(raid_data, dict) and any(
                isinstance(raid_data.get(tier), list) and raid_data.get(tier)
                for tier in RAID_ITEM_TIERS
            ):
                any_data = True

        if not any_data:
            loot_embed.add_field(
                "Raid Item Pool Not Ready",
                "No raid item pool has been published yet. Please check back shortly.",
            )
            await ctx.edit_last_response(embed=loot_embed, content="")
            return

        loot_embed.set_footer("Nori Bot - Raid Item Lootpool")
        loot_embed.set_thumbnail("https://static.wikia.nocookie.net/wynncraft_gamepedia_en/images/f/f0/LootrunUpdateIcon.png/revision/latest?cb=20230709013002")
        view = raidItemView(timeout=120)
        message = await ctx.edit_last_response(embed=loot_embed, content="", components=view.build())
        await view.start(message)
        await view.wait()
