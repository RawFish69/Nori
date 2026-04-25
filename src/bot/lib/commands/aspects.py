"""Aspect-related commands."""

import json
import time

import hikari
import lightbulb
import miru

from lib.config import DATA_PATH, aspect_user
from lib.utils import check_user_access

RAID_NAMES = ["TNA", "TCC", "NOL", "NOG", "TWP"]


def _bucket_has_tier_data(bucket) -> bool:
    """True when a raid bucket contains at least one non-empty tier list.

    An empty scaffold ``{"Mythic": [], "Fabled": [], ...}`` is truthy in
    Python, so ``not loot.get("NOG")`` would silently treat it as populated
    and skip the NOTG→NOG alias. We inspect the tier lists themselves.
    """
    if not isinstance(bucket, dict):
        return False
    return any(isinstance(v, list) and len(v) > 0 for v in bucket.values())


async def _load_aspect_lootpool():
    with open(DATA_PATH / "weekly_aspects.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    # Back-compat: legacy pool files (and the v2 pool API upstream) key the
    # grootslang raid as "NOTG" while our canonical short-code (RAID_NAMES
    # above) is "NOG". Fold the legacy entry into the canonical key so
    # displays keyed on "NOG" see the existing data. Uses a strong
    # bucket-has-tier-data check to also replace a truthy-but-empty NOG.
    if isinstance(data, dict):
        loot = data.get("Loot")
        if isinstance(loot, dict) and "NOTG" in loot:
            notg_bucket = loot.pop("NOTG")
            if not _bucket_has_tier_data(loot.get("NOG")):
                loot["NOG"] = notg_bucket if isinstance(notg_bucket, dict) else {}
    return data


class AspectLootView(miru.View):
    @miru.button(emoji=hikari.Emoji.parse("<a:aspect_assassin:1274305350102945814>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_mythic(self, button: miru.Button, ctx: miru.Context):
        user = await ctx.bot.rest.fetch_user(ctx.user.id)
        aspect_user[user.username] = "Mythic"
        print(f"[Lootpool] {aspect_user[user.username]} Aspects requested by {user.username}")
        await self.lootpool_display(ctx, aspect_user[user.username])

    @miru.button(emoji=hikari.Emoji.parse("<a:aspect_warrior:1274305374417063956>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_fabled(self, button: miru.Button, ctx: miru.Context):
        user = await ctx.bot.rest.fetch_user(ctx.user.id)
        aspect_user[user.username] = "Fabled"
        print(f"[Lootpool] {aspect_user[user.username]} Aspects requested by {user.username}")
        await self.lootpool_display(ctx, aspect_user[user.username])

    @miru.button(emoji=hikari.Emoji.parse("<a:aspect_shaman:1274305366011678793>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_legend(self, button: miru.Button, ctx: miru.Context):
        user = await ctx.bot.rest.fetch_user(ctx.user.id)
        aspect_user[user.username] = "Legendary"
        print(f"[Lootpool] {aspect_user[user.username]} Aspects requested by {user.username}")
        await self.lootpool_display(ctx, aspect_user[user.username])

    async def lootpool_display(self, ctx: miru.Context, loot_type: str):
        data = await _load_aspect_lootpool()
        aspects_all = data["Loot"]
        timestamp = data["Timestamp"]
        aspect_icons = data["Icon"]
        aspect_emojis = {
            "aspect_warrior.gif": "<a:aspect_warrior:1274305374417063956>",
            "aspect_mage.gif": "<a:aspect_mage:1274305357304565760>",
            "aspect_archer.gif": "<a:aspect_archer:1274305340959227971>",
            "aspect_assassin.gif": "<a:aspect_assassin:1274305350102945814>",
            "aspect_shaman.gif": "<a:aspect_shaman:1274305366011678793>",
        }
        static_emojis = {
            "static_warrior.png": "<:static_warrior:1274305305576079391>",
            "static_mage.png": "<:static_mage:1274305289491058743>",
            "static_archer.png": "<:static_archer:1274305243068497930>",
            "static_assassin.png": "<:static_assassin:1274305280351408238>",
            "static_shaman.png": "<:static_shaman:1274305297003057179>",
        }
        loot_aspects = {}
        next_update = timestamp + 604800
        user = await ctx.bot.rest.fetch_user(ctx.user.id)
        username = user.username
        aspect_user[username] = "Mythic"
        web_page = "### [Aspect Lootpool on Nori-Web](https://nori.fish/wynn/aspects) ###"
        time_line = f"Starting <t:{timestamp}:D>\nNext update: <t:{next_update}:R>\n"

        for raid in RAID_NAMES:
            aspects_in_pool = aspects_all.get(raid)
            if not aspects_in_pool:
                continue
            if loot_type == "Mythic":
                aspect_info = (
                    "\n".join(
                        [
                            f"- {aspect_emojis.get(aspect_icons.get(aspect_name, ''), '')}{aspect_name}"
                            for aspect_name in aspects_in_pool[loot_type]
                        ]
                    )
                    if aspects_in_pool[loot_type]
                    else "N/A"
                )
            else:
                aspect_info = (
                    "\n".join(
                        [
                            f"- {static_emojis.get(aspect_icons.get(aspect_name, ''), '')}{aspect_name}"
                            for aspect_name in aspects_in_pool[loot_type]
                        ]
                    )
                    if aspects_in_pool[loot_type]
                    else "N/A"
                )

            loot_aspects[raid] = aspect_info

        loot_embed = hikari.Embed(
            title="Weekly Aspect Rotation",
            description=f"{time_line}{web_page}",
            color="#c0aaff",
        )
        for raid, aspects in loot_aspects.items():
            loot_embed.add_field(f"{raid} {loot_type} Aspects", aspects)
        loot_embed.set_footer("Nori Bot - Aspect Lootpool")
        loot_embed.set_thumbnail("https://nori.fish/resources/aspect.gif")
        await ctx.edit_response(embed=loot_embed)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as error:
            print(f"Failed to edit message on timeout: {error}")


def load_aspect_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load aspect-related commands."""

    @bot.command()
    @lightbulb.command("aspect", "Aspect command group")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def aspect(ctx: lightbulb.Context):
        pass

    @aspect.child()
    @lightbulb.command("lootpool", "View weekly Aspect Lootpool")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def show_aspect_lootpool(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        data = await _load_aspect_lootpool()
        aspects_all = data["Loot"]
        timestamp = data["Timestamp"]
        aspect_icons = data["Icon"]
        aspect_emojis = {
            "aspect_warrior.gif": "<a:aspect_warrior:1274305374417063956>",
            "aspect_mage.gif": "<a:aspect_mage:1274305357304565760>",
            "aspect_archer.gif": "<a:aspect_archer:1274305340959227971>",
            "aspect_assassin.gif": "<a:aspect_assassin:1274305350102945814>",
            "aspect_shaman.gif": "<a:aspect_shaman:1274305366011678793>",
        }
        current_time = int(time.time())
        next_update = timestamp + 604800
        user = await bot.rest.fetch_user(ctx.user.id)
        username = user.username
        aspect_user[username] = "Mythic"
        web_page = "### [Aspect Lootpool on Nori-Web](https://nori.fish/wynn/aspects) ###"
        time_line = f"Starting <t:{timestamp}:D>\nNext update: <t:{next_update}:R>\n"
        loot_embed = hikari.Embed(
            title="Weekly Aspect Rotation",
            description=f"{time_line}{web_page}",
            color="#c0aaff",
        )

        if current_time >= next_update:
            update_msg = (
                "We are updating this week's new aspects.\n"
                "Aspect Lootpool is a community supported feature, be patient as our contributors gather the information.\n"
            )
            loot_embed.add_field("New Aspect Info", update_msg)
            web_info = (
                "Join our [support server](https://discord.com/invite/eDssA6Jbwd) to follow updates & patches for nori.\n"
                "The web version will update the same time as the bot, with much better display\n"
                "Try out other features on [Nori-Web](https://nori.fish/wynn/)\n"
                "Popular utility like **item analysis**, **item simulation**, **build/recpie search**, **leaderboards**, and more!"
            )
            loot_embed.add_field("Check Aspects in Web Browser", web_info)
            await ctx.respond(embed=loot_embed)
        else:
            for raid in RAID_NAMES:
                aspects_in_pool = aspects_all.get(raid)
                if not aspects_in_pool:
                    continue
                mythic_names = aspects_in_pool.get("Mythic") if isinstance(aspects_in_pool, dict) else None
                if mythic_names:
                    mythics_info = "\n".join(
                        f"- {aspect_emojis.get(aspect_icons.get(aspect_name, ''), '')}{aspect_name}"
                        for aspect_name in mythic_names
                    )
                else:
                    mythics_info = "N/A"
                loot_embed.add_field(f"{raid} Mythic Aspects", mythics_info)

            loot_embed.set_footer("Nori Bot - Aspect Lootpool")
            loot_embed.set_thumbnail("https://nori.fish/resources/aspect.gif")

            view = AspectLootView(timeout=120)
            message = await ctx.respond(embed=loot_embed, components=view.build())
            message = await message
            await view.start(message)
            await view.wait()

