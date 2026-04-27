"""Interactive views for raid lootpool commands."""

import time

import hikari
import miru

import lib.config as config
from lib.config import (
    ASPECT_TIERS,
    RAID_ITEM_TIERS,
    RAID_NAMES,
    RAID_WEB_URL,
    format_aspect_display,
    format_compacted_item_lines,
    format_ward_display,
)
from lib.raid_pool_utils import load_aspect_lootpool, load_weekly_raid_pool

SECONDS_PER_WEEK = 604800


class aspectView(miru.View):
    @miru.button(emoji=hikari.Emoji.parse("<a:aspect_assassin:1274305350102945814>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_mythic(self, button: miru.Button, ctx: miru.Context):
        await self.lootpool_display(ctx, "Mythic")

    @miru.button(emoji=hikari.Emoji.parse("<a:aspect_warrior:1274305374417063956>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_fabled(self, button: miru.Button, ctx: miru.Context):
        await self.lootpool_display(ctx, "Fabled")

    @miru.button(emoji=hikari.Emoji.parse("<a:aspect_shaman:1274305366011678793>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_legendary(self, button: miru.Button, ctx: miru.Context):
        await self.lootpool_display(ctx, "Legendary")

    async def lootpool_display(self, ctx: miru.Context, loot_type: str):
        if loot_type not in ASPECT_TIERS:
            loot_type = "Mythic"

        data = await load_aspect_lootpool()
        aspects_all = data.get("Loot", {})
        aspect_icons = data.get("Icon", {})
        timestamp = data.get("Timestamp", int(time.time()))
        next_update = timestamp + SECONDS_PER_WEEK

        user = await ctx.bot.rest.fetch_user(ctx.user.id)
        config.aspect_user[user.username] = loot_type

        description = (
            f"Starting <t:{timestamp}:D>\n"
            f"Next update: <t:{next_update}:R>\n"
            f"### [Raid Lootpool on Nori-Web]({RAID_WEB_URL}) ###"
        )
        loot_embed = hikari.Embed(title="Weekly Raid Aspect Rotation", description=description, color="#c0aaff")

        for raid in RAID_NAMES:
            aspects_in_pool = aspects_all.get(raid, {}) if isinstance(aspects_all, dict) else {}
            tier_aspects = aspects_in_pool.get(loot_type, []) if isinstance(aspects_in_pool, dict) else []
            use_static = loot_type != "Mythic"
            lines = [
                f"- {format_aspect_display(aspect_name, aspect_icons.get(aspect_name, ''), use_static=use_static)}"
                for aspect_name in tier_aspects
            ]
            loot_embed.add_field(f"{raid} {loot_type} Aspects", "\n".join(lines) if lines else "N/A")

        loot_embed.set_footer("Nori Bot - Raid Aspect Lootpool")
        loot_embed.set_thumbnail("https://nori.fish/resources/aspect.gif")
        await ctx.edit_response(embed=loot_embed)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as error:
            print(f"Failed to edit aspect view on timeout: {error}")


class raidItemView(miru.View):
    @miru.button(emoji=hikari.Emoji.parse("<:mythic:1185349344182935603>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_mythic(self, button: miru.Button, ctx: miru.Context):
        await self.lootpool_display(ctx, "Mythic")

    @miru.button(emoji=hikari.Emoji.parse("<:fabled:1185349372490285224>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_fabled(self, button: miru.Button, ctx: miru.Context):
        await self.lootpool_display(ctx, "Fabled")

    @miru.button(emoji=hikari.Emoji.parse("<:legendary:1185349392786534461>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_legendary(self, button: miru.Button, ctx: miru.Context):
        await self.lootpool_display(ctx, "Legendary")

    @miru.button(emoji=hikari.Emoji.parse("<:rare:1185349423279120514>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_rare(self, button: miru.Button, ctx: miru.Context):
        await self.lootpool_display(ctx, "Rare")

    @miru.button(emoji=hikari.Emoji.parse("<:unique:1185349447639646258>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_unique(self, button: miru.Button, ctx: miru.Context):
        await self.lootpool_display(ctx, "Unique")

    @miru.button(label="Misc", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_misc(self, button: miru.Button, ctx: miru.Context):
        await self.lootpool_display(ctx, "Misc")

    async def lootpool_display(self, ctx: miru.Context, loot_type: str):
        if loot_type not in RAID_ITEM_TIERS:
            loot_type = "Mythic"

        data = await load_weekly_raid_pool()
        raid_items_all = data.get("Loot", {})
        timestamp = data.get("Timestamp", int(time.time()))
        next_update = timestamp + SECONDS_PER_WEEK
        description = (
            f"Starting <t:{timestamp}:D>\n"
            f"Next update: <t:{next_update}:R>\n"
            f"### [Raid Lootpool on Nori-Web]({RAID_WEB_URL}) ###"
        )

        loot_embed = hikari.Embed(title="Weekly Raid Item Rotation", description=description, color="#c0aaff")
        for raid in RAID_NAMES:
            raid_data = raid_items_all.get(raid, {}) if isinstance(raid_items_all, dict) else {}
            tier_items = raid_data.get(loot_type, []) if isinstance(raid_data, dict) else []
            formatter = format_ward_display if loot_type == "Mythic" else None
            lines = format_compacted_item_lines(tier_items, formatter=formatter)
            loot_embed.add_field(f"{raid} {loot_type} Items", "\n".join(lines) if lines else "N/A")

        loot_embed.set_footer("Nori Bot - Raid Item Lootpool")
        loot_embed.set_thumbnail("https://static.wikia.nocookie.net/wynncraft_gamepedia_en/images/f/f0/LootrunUpdateIcon.png/revision/latest?cb=20230709013002")
        await ctx.edit_response(embed=loot_embed)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as error:
            print(f"Failed to edit raid item view on timeout: {error}")
