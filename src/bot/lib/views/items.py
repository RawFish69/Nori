"""Item-related interactive views."""

import json
import time

import hikari
import miru

import lib.config as config
from lib.config import (
    LOOTPOOL_REGIONS,
    LOOT_TIERS,
    RESOURCES_PATH,
    WEEKLY_LOOTPOOL_FILE,
    format_ward_display,
)

SHINY_EMOJI = "<:shiny:1233489508956115116>"


def _load_weekly_lootpool() -> dict:
    try:
        with open(WEEKLY_LOOTPOOL_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"Loot": config.lootpool_data, "Timestamp": int(time.time())}


def build_lootpool_embed(loot_type: str = "Mythic") -> hikari.Embed:
    """Build the weekly lootpool embed using the old bot.py layout."""
    if loot_type not in LOOT_TIERS:
        loot_type = "Mythic"

    data = _load_weekly_lootpool()
    lootpool_all = data.get("Loot", {})
    timestamp = data.get("Timestamp", int(time.time()))
    next_update = timestamp + config.SECONDS_PER_WEEK
    time_line = f"Starting <t:{timestamp}:D>\nNext update: <t:{next_update}:R>"
    loot_embed = hikari.Embed(
        title=f"Weekly Lootpool Rotation",
        description=time_line,
        color="#4FE5F9",
    )

    if int(time.time()) >= next_update:
        loot_embed.add_field(
            "New Lootpool Info",
            "**We are updating this week's new lootpool.**\n"
            "Contact [Support Server](https://discord.gg/tU7eaKAWb2) for any issue or follow nori updates",
        )
        return loot_embed

    for region in LOOTPOOL_REGIONS:
        pool_data = lootpool_all.get(region, {}) if isinstance(lootpool_all, dict) else {}
        tier_items = pool_data.get(loot_type, []) if isinstance(pool_data, dict) else []
        item_text = "".join(f"\n- {format_ward_display(item)}" for item in tier_items) if tier_items else "\nN/A"

        if loot_type == "Mythic":
            shiny = pool_data.get("Shiny", {}) if isinstance(pool_data, dict) else {}
            shiny_info = (
                f"- ✨Shiny **{shiny.get('Item', 'N/A')}**✨\n"
                f"Tracker: **{shiny.get('Tracker', 'N/A')}**"
            )
            item_text = shiny_info + item_text
        loot_embed.add_field(f"{region} Loot", item_text)

    loot_embed.set_footer("Nori Bot - Weekly Lootpool")
    loot_embed.set_thumbnail("https://static.wikia.nocookie.net/wynncraft_gamepedia_en/images/f/f0/LootrunUpdateIcon.png/revision/latest?cb=20230709013002")
    return loot_embed


class ampView(miru.View):
    """View for item amplifier/reroll interactions."""

    @miru.button(label="Refresh", style=hikari.ButtonStyle.SECONDARY)
    async def button_amp(self, ctx: miru.ViewContext, button: miru.Button):
        user = await ctx.client.app.rest.fetch_user(ctx.user.id)
        item_data = config.item_amp_data.get(user)
        if not item_data:
            await ctx.edit_response("No active item roll session.")
            return

        item_name = item_data["item"]
        item_data["rr"] += 1
        reroll_count = item_data["rr"]
        amp_tier = item_data["tier"]

        from lib.item_utils import ItemUtils
        item_utils = ItemUtils(config.item_map or {})

        amp_result = item_utils.item_amp(item_name, amp_tier)
        if not amp_result:
            await ctx.edit_response(f"Item {item_name} has no rerollable ID.")
            return
        display = amp_result[0]
        rr_display = amp_result[1]
        icon_id = amp_result[3] if len(amp_result) > 3 else None
        item_type = amp_result[4] if len(amp_result) > 4 else None

        item_embed = hikari.Embed(
            title="Item Identification Simulator",
            description='*"99% of gamblers quit before hitting it big"*',
            color="#00E7B6",
        )
        item_embed.add_field("Identifications", f"```json\n{rr_display}\nRerolled: [{reroll_count}]```")
        if amp_tier > 0:
            item_embed.add_field(f"Amplifier {amp_tier}", display)
        try:
            if item_type in ["helmet", "chestplate", "leggings", "boots"]:
                item_embed.set_thumbnail(hikari.files.File(str(RESOURCES_PATH / f"{item_type}.png")))
            elif icon_id:
                item_embed.set_thumbnail(f"https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp")
        except Exception as error:
            print(f"Item reroll thumbnail error: {error}")

        item_embed.set_footer("Nori Bot - Wynn Items")
        await ctx.edit_response(embed=item_embed)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as error:
            print(f"Failed to edit message on timeout: {error}")


class lootView(miru.View):
    """Tier selector for the weekly lootrun camp pool."""

    @miru.button(emoji=hikari.Emoji.parse("<:mythic:1185349344182935603>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_mythic(self, ctx: miru.ViewContext, button: miru.Button):
        await self.lootpool_display(ctx, "Mythic")

    @miru.button(emoji=hikari.Emoji.parse("<:fabled:1185349372490285224>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_fabled(self, ctx: miru.ViewContext, button: miru.Button):
        await self.lootpool_display(ctx, "Fabled")

    @miru.button(emoji=hikari.Emoji.parse("<:legendary:1185349392786534461>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_legendary(self, ctx: miru.ViewContext, button: miru.Button):
        await self.lootpool_display(ctx, "Legendary")

    @miru.button(emoji=hikari.Emoji.parse("<:rare:1185349423279120514>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_rare(self, ctx: miru.ViewContext, button: miru.Button):
        await self.lootpool_display(ctx, "Rare")

    @miru.button(emoji=hikari.Emoji.parse("<:unique:1185349447639646258>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_unique(self, ctx: miru.ViewContext, button: miru.Button):
        await self.lootpool_display(ctx, "Unique")

    @miru.button(label="Misc", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_misc(self, ctx: miru.ViewContext, button: miru.Button):
        await self.lootpool_display(ctx, "Misc")

    async def lootpool_display(self, ctx: miru.ViewContext, loot_type: str):
        if loot_type not in LOOT_TIERS:
            loot_type = "Mythic"

        user = await ctx.client.app.rest.fetch_user(ctx.user.id)
        config.lootpool_user[user.username] = loot_type
        print(f"[Lootpool] {loot_type} Items requested by {user.username}")

        await ctx.edit_response(embed=build_lootpool_embed(loot_type))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as error:
            print(f"Failed to edit message on timeout: {error}")
