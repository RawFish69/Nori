"""Ingredient-related commands."""

import hikari
import lightbulb

from lib.config import (
    CHANGELOG_PATH,
)
from lib.utils import check_user_access, ingredient_search


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
