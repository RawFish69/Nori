"""Ingredient-related commands."""

import json
import time
from datetime import datetime

import hikari
import lightbulb
import miru

from lib.config import (
    CHANGELOG_PATH,
    DATA_PATH,
    USER_IMG_PATH,
    VERSION,
    lootpool_user,
)
from lib.utils import check_user_access, ingredient_search

LOOTPOOL_REGIONS = ["SE", "Corkus", "Molten", "Sky", "Canyon", "FrumaEast", "FrumaWest"]
WARD_EMOJIS = {
    "Yellow Ward": "<:yellow_ward:1489621423113634022>",
    "White Ward": "<:white_ward:1489621422127976549>",
    "Red Ward": "<:red_ward:1489621420999704618>",
    "Purple Ward": "<:purple_ward:1489621420328747079>",
    "Pink Ward": "<:pink_ward:1489621419598938132>",
    "Orange Ward": "<:orange_ward:1489621418873196705>",
    "Green Ward": "<:green_ward:1489621418185588816>",
    "Cyan Ward": "<:cyan_ward:1489621417078296787>",
    "Blue Ward": "<:blue_ward:1489621416268791858>",
    "Black Ward": "<:black_ward:1489621415488520192>",
}


async def _get_lootpool():
    with open(DATA_PATH / "weekly_lootpool.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


async def _find_item_in_lootpool(item: str):
    with open(DATA_PATH / "lootpool_history.json", "r", encoding="utf-8") as file:
        pool_data = json.load(file)

    item_data = {}
    weekly_region = []
    item = item.lower()

    for week in pool_data:
        weekly_count = 0
        shiny_present = False
        shiny_region = None
        tracker = None
        weekly_pool = pool_data[week]

        for region in weekly_pool:
            pool_items = weekly_pool[region]
            if not pool_items:
                continue

            shiny = pool_items[0].lower() if len(pool_items) > 0 else ""
            mythic_list = pool_items[1] if len(pool_items) > 1 and isinstance(pool_items[1], list) else []
            mythic = [pool_item.lower() for pool_item in mythic_list]

            if item in shiny or item in mythic:
                weekly_count += 1
                weekly_region.append(region)
            if item in shiny:
                shiny_present = True
                shiny_region = region
                tracker = pool_items[0]

        item_data[week] = {
            "count": weekly_count,
            "shiny": shiny_present,
            "region": weekly_region,
            "shiny_region": shiny_region if shiny_present else None,
            "tracker": tracker if shiny_present else None,
        }
        weekly_region = []

    return item_data


async def _plot_calendar_heatmap(item_data, start_date="2023-07-01", item_name="Item", user_name=None):
    import matplotlib.colors as mcolors
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import seaborn as sns

    end_date = datetime.now().strftime("%Y-%m-%d")
    all_weeks = pd.date_range(start=start_date, end=end_date, freq="W-MON")
    heatmap_df = pd.DataFrame(all_weeks, columns=["week_start"])
    heatmap_df["count"] = 0
    heatmap_df["is_shiny"] = False

    for date_str, info in item_data.items():
        week_start = pd.to_datetime(date_str)
        mask = (heatmap_df["week_start"] <= week_start) & (
            week_start < heatmap_df["week_start"] + pd.Timedelta(weeks=1)
        )
        heatmap_df.loc[mask, "count"] = info.get("count", 0)
        heatmap_df.loc[mask, "is_shiny"] = info.get("is_shiny", False)

    heatmap_df["year"] = heatmap_df["week_start"].dt.year
    heatmap_df["quarter"] = heatmap_df["week_start"].dt.to_period("Q").dt.strftime("Q%q")
    heatmap_df["week"] = heatmap_df["week_start"].dt.isocalendar().week

    heatmap_pivot = heatmap_df.pivot_table(
        index="week",
        columns=["year", "quarter"],
        values="count",
        aggfunc="sum",
        fill_value=0,
    )

    colors = ["#e0f2e9", "#a5d6a7", "#66bb6a", "#388e3c", "#1b5e20"]
    cmap = mcolors.LinearSegmentedColormap.from_list("custom_cmap", colors)
    norm = plt.Normalize(heatmap_df["count"].min(), heatmap_df["count"].max())

    sns.heatmap(
        heatmap_pivot,
        cmap=cmap,
        linewidths=0.5,
        linecolor="lightgrey",
        annot=False,
        norm=norm,
        cbar_kws={"ticks": np.linspace(heatmap_df["count"].min(), heatmap_df["count"].max(), 3)},
        mask=heatmap_pivot == 0,
    )

    plt.title(f"Appearances of {item_name} in Lootpool [{end_date}]")
    plt.text(
        1.0,
        -0.15,
        f"Nori Bot v{VERSION} by RawFish",
        transform=plt.gca().transAxes,
        fontsize=10,
        ha="right",
        va="bottom",
        color="orange",
    )
    plt.xlabel("Year-Quarter")
    plt.ylabel("Week Number")
    plt.tight_layout()

    output_dir = USER_IMG_PATH / "loot_history"
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"lootHistory_{user_name}.png"
    plt.savefig(str(filename), bbox_inches="tight")
    plt.close()
    return int(time.time())


class IngredientLootView(miru.View):
    @miru.button(emoji=hikari.Emoji.parse("<:mythic:1185349344182935603>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_mythic(self, button: miru.Button, ctx: miru.Context):
        user = await ctx.bot.rest.fetch_user(ctx.user.id)
        lootpool_user[user.username] = "Mythic"
        print(f"[Lootpool] {lootpool_user[user.username]} Items requested by {user.username}")
        await self.lootpool_display(ctx, lootpool_user[user.username])

    @miru.button(emoji=hikari.Emoji.parse("<:fabled:1185349372490285224>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_fabled(self, button: miru.Button, ctx: miru.Context):
        user = await ctx.bot.rest.fetch_user(ctx.user.id)
        lootpool_user[user.username] = "Fabled"
        print(f"[Lootpool] {lootpool_user[user.username]} Items requested by {user.username}")
        await self.lootpool_display(ctx, lootpool_user[user.username])

    @miru.button(emoji=hikari.Emoji.parse("<:legendary:1185349392786534461>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_legend(self, button: miru.Button, ctx: miru.Context):
        user = await ctx.bot.rest.fetch_user(ctx.user.id)
        lootpool_user[user.username] = "Legendary"
        print(f"[Lootpool] {lootpool_user[user.username]} Items requested by {user.username}")
        await self.lootpool_display(ctx, lootpool_user[user.username])

    @miru.button(emoji=hikari.Emoji.parse("<:rare:1185349423279120514>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_rare(self, button: miru.Button, ctx: miru.Context):
        user = await ctx.bot.rest.fetch_user(ctx.user.id)
        lootpool_user[user.username] = "Rare"
        print(f"[Lootpool] {lootpool_user[user.username]} Items requested by {user.username}")
        await self.lootpool_display(ctx, lootpool_user[user.username])

    @miru.button(emoji=hikari.Emoji.parse("<:unique:1185349447639646258>"), style=hikari.ButtonStyle.SECONDARY)
    async def button_unique(self, button: miru.Button, ctx: miru.Context):
        user = await ctx.bot.rest.fetch_user(ctx.user.id)
        lootpool_user[user.username] = "Unique"
        print(f"[Lootpool] {lootpool_user[user.username]} Items requested by {user.username}")
        await self.lootpool_display(ctx, lootpool_user[user.username])

    async def lootpool_display(self, ctx: miru.Context, loot_type: str):
        data = await _get_lootpool()
        lootpool_all = data["Loot"]
        timestamp = data["Timestamp"]
        next_update = timestamp + 604800
        shiny_emoji = "<:shiny:1233489508956115116>"
        time_line = f"Starting <t:{timestamp}:D>\nNext update: <t:{next_update}:R>"
        loot_items = {}

        for pool in LOOTPOOL_REGIONS:
            pool_data = lootpool_all.get(pool)
            if not pool_data:
                continue

            items = (
                "\n".join(f"- {WARD_EMOJIS.get(item, '')}{item}" for item in pool_data[loot_type])
                if pool_data[loot_type]
                else "N/A"
            )
            if loot_type == "Mythic":
                shiny_info = (
                    f"- {shiny_emoji}Shiny **{pool_data['Shiny']['Item']}**\n"
                    f"Tracker: **{pool_data['Shiny']['Tracker']}**\n"
                )
                items = shiny_info + items
            loot_items[pool] = items

        loot_embed = hikari.Embed(title="Weekly Lootpool Rotation", description=time_line, color="#4FE5F9")
        for pool, items in loot_items.items():
            loot_embed.add_field(f"{pool} {loot_type}", items)
        loot_embed.set_footer("Nori Bot - Weekly Lootpool")
        loot_embed.set_thumbnail(
            "https://static.wikia.nocookie.net/wynncraft_gamepedia_en/images/f/f0/LootrunUpdateIcon.png/revision/latest?cb=20230709013002"
        )
        await ctx.edit_response(embed=loot_embed)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as error:
            print(f"Failed to edit message on timeout: {error}")


def load_ingredient_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load ingredient-related commands."""

    @bot.command()
    @lightbulb.command("ingredient", "Ingredients for wynn")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def ingredients(ctx: lightbulb.Context):
        pass

    @ingredients.child()
    @lightbulb.option("name", "Name of the ingredient")
    @lightbulb.command("search", "Ingredient search function")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def ingredient_process(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        input_name = ctx.options.name
        data = ingredient_search(input_name)
        try:
            skills = ", ".join(data["requirements"]["skills"])
            ing_icon = data["icon"]["value"]["name"] if "icon" in data else None
            icon_id = ing_icon.replace(":", "_") if ing_icon else None
            ids = data["identifications"] if "identifications" in data else None
            item_only = data["itemOnlyIDs"] if "itemOnlyIDs" in data else None
            consum_only = data["consumableOnlyIDs"] if "consumableOnlyIDs" in data else None
            modifier = data["ingredientPositionModifiers"] if "ingredientPositionModifiers" in data else None
            id_field = ""
            item_field = ""
            consum_field = ""
            modifier_field = ""
            ing_embed = hikari.Embed(
                title=data["internalName"],
                description=f"Level {data['requirements']['level']} Tier {data.get('tier', '').replace('TIER_', '')} Ingredient\nUsed in {skills}",
                color="#FFF977",
            )
            if ids:
                for stat in ids:
                    id_field += f"{stat}: **{ids[stat]['min']}** ~ **{ids[stat]['max']}**\n"
                ing_embed.add_field("Identifications", id_field)
            if item_only:
                for stat in item_only:
                    item_field += f"{stat}: {item_only[stat]}\n"
                ing_embed.add_field("Item-specific IDs", item_field)
            if consum_only:
                for stat in consum_only:
                    consum_field += f"{stat}: {consum_only[stat]}\n"
                ing_embed.add_field("Consumable-specific IDs", consum_field)
            if modifier:
                for stat in modifier:
                    modifier_field += f"{stat}: {modifier[stat]}\n"
                ing_embed.add_field("Modifiers", modifier_field)
            ing_embed.set_footer("Nori Bot - Wynn Ingredients")
            try:
                ing_embed.set_thumbnail(f"https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp")
            except Exception:
                pass
            await ctx.respond(embed=ing_embed)
        except Exception as error:
            print(error)
            await ctx.respond(f"No result found with `{input_name}`")

    @ingredients.child()
    @lightbulb.command("changelog", "Ingredient changelog based on API")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def ingredient_check_log(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        log_file = hikari.files.File(str(CHANGELOG_PATH / "ingredient_changelog.md"))
        await ctx.respond(log_file)

    @ingredients.child()
    @lightbulb.command("lootpool", "Weekly Lootpool Rotation")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def ingredient_lootpool(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        data = await _get_lootpool()
        lootpool_all = data["Loot"]
        timestamp = data["Timestamp"]
        current_time = int(time.time())
        next_update = timestamp + 604800
        shiny_emoji = "<:shiny:1233489508956115116>"
        user = await bot.rest.fetch_user(ctx.user.id)
        username = user.username
        lootpool_user[username] = "Mythic"
        time_line = f"Starting <t:{timestamp}:D>\nNext update: <t:{next_update}:R>\n"
        web_page = "### [Lootpool on Nori-Web](https://nori.fish/wynn/item/lootpool/) ###"
        loot_embed = hikari.Embed(
            title="Weekly Lootpool Rotation",
            description=f"{time_line}{web_page}",
            color="#4FE5F9",
        )

        if current_time >= next_update:
            update_msg = (
                "We are updating this week's new lootpool.\n"
                "Item lootpool is a community supported feature, be patient as our contributors check the information.\n"
            )
            loot_embed.add_field("New Lootpool Info", update_msg)
            web_info = (
                "Join our [support server](https://discord.com/invite/eDssA6Jbwd) to follow updates & patches for nori.\n"
                "The web version will update the same time as the bot, with much better display\n"
                "Try out other features on [Nori-Web](https://nori.fish/wynn/)\n"
                "Popular utility like **item analysis**, **item simulation**, **build/recpie search**, **leaderboards**, and more!"
            )
            loot_embed.add_field("Check Lootpool in Web Browser", web_info)
            await ctx.respond(embed=loot_embed)
        else:
            for pool in LOOTPOOL_REGIONS:
                pool_data = lootpool_all.get(pool)
                if not pool_data:
                    continue
                shiny_info = (
                    f"- {shiny_emoji}Shiny **{pool_data['Shiny']['Item']}**\n"
                    f"Tracker: **{pool_data['Shiny']['Tracker']}**"
                )
                mythics_info = "\n".join([f"- {WARD_EMOJIS.get(item, '')}{item}" for item in pool_data["Mythic"]])
                loot_embed.add_field(f"{pool} Mythic", f"{shiny_info}\n{mythics_info}")

            loot_embed.set_footer("Nori Bot - Weekly Lootpool")
            loot_embed.set_thumbnail(
                "https://static.wikia.nocookie.net/wynncraft_gamepedia_en/images/f/f0/LootrunUpdateIcon.png/revision/latest?cb=20230709013002"
            )

            view = IngredientLootView(timeout=120)
            message = await ctx.respond(embed=loot_embed, components=view.build())
            message = await message
            await view.start(message)
            await view.wait()

    @ingredients.child()
    @lightbulb.option("graph", "Heat map generation", default="Yes", choices=["Yes", "No"], required=False)
    @lightbulb.option("item", "Name of the item")
    @lightbulb.command("history", "Find item in the lootpool history")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def ingredient_history(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        user = await bot.rest.fetch_user(ctx.user.id)
        username = user.username
        msg_embed = hikari.Embed(
            title=f"Handling request from user {username}",
            description="Generating Heatmap...",
            color="#4FE5F9",
        )
        await ctx.respond(msg_embed)
        item_name = ctx.options.item
        try:
            item_data = await _find_item_in_lootpool(item_name)
            start_time = time.time()
            processing_time = None
            file_path = None
            if ctx.options.graph == "Yes":
                try:
                    end_time = await _plot_calendar_heatmap(item_data, "2023-07-01", item_name, username)
                    processing_time = round((end_time - start_time) * 1000, 2)
                    file_path = f"lootHistory_{username}.png"
                except Exception as error:
                    print(error)

            total = 0
            total_shiny = 0
            last_seen = ""
            last_region = ""
            last_seen_shiny = ""
            last_region_shiny = ""
            last_tracker = ""

            for week in item_data:
                data = item_data[week]
                if data["count"] > 0:
                    total += data["count"]
                    region = ", ".join(data["region"])
                    last_seen = week
                    last_region = region
                    if data["shiny"]:
                        total_shiny += 1
                        last_seen_shiny = week
                        last_region_shiny = data["shiny_region"]
                        last_tracker = data["tracker"]

            log_embed = hikari.Embed(
                title="Lootpool History Search [Beta]",
                description=(
                    f"{item_name} has been recorded {total} times in historical data.\n"
                    f"Its shiny variant was recorded {total_shiny} times."
                ),
                color="#4FE5F9",
            )
            log_embed.add_field("Last Seen", f"Week of **{last_seen}** in *{last_region}*")
            log_embed.add_field(
                "Shiny version last seen",
                f"Week of **{last_seen_shiny}** in *{last_region_shiny}*\n**{last_tracker}**",
            )
            log_embed.set_thumbnail(
                "https://static.wikia.nocookie.net/wynncraft_gamepedia_en/images/f/f0/LootrunUpdateIcon.png/revision/latest?cb=20230709013002"
            )
            if file_path:
                log_embed.add_field("Computation time", f"{processing_time} ms")
                map_generated = hikari.files.File(str(USER_IMG_PATH / "loot_history" / file_path))
                log_embed.set_image(map_generated)
            log_embed.set_footer("Nori Bot - Lootpool History")
        except Exception as error:
            print(error)
            log_embed = hikari.Embed(title=f"Error processing item {item_name}", color="#FF0000")
        await ctx.edit_last_response(embed=log_embed)

