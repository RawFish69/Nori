"""Recipe command group."""

import hikari
import lightbulb
import miru

from lib.build_recipe_utils import recipe_file_remove, recipe_file_search, recipe_file_updater
from lib.config import recipe_data
from lib.permissions import contributor_only
from lib.utils import check_user_access


def _chunk_results(items, size=10):
    return [items[index:index + size] for index in range(0, len(items), size)]


def _recipe_embed(page_results, tags, page, total_pages, recipes_found):
    tags_text = ", ".join(tags)
    page_line = f"Page **{page}** of **{total_pages}**"
    embed = hikari.Embed(
        title=f"Recipes with keyword: __{tags_text}__",
        description=f"**{recipes_found}** Results found\n{page_line}",
        color="#E4A3FC",
    )
    for index, recipe in enumerate(page_results, start=1):
        recipe_name = list(recipe.keys())[0]
        recipe_entry = recipe[recipe_name]
        recipe_tags = recipe_entry.get("tag", "")
        recipe_link = recipe_entry.get("link", "")
        for tag in tags:
            if tag and tag.lower() in recipe_tags.lower():
                recipe_tags = recipe_tags.replace(tag, f"__{tag}__")
        embed.add_field(
            f"{index}. **{recipe_name}**",
            f"{recipe_tags}\n[Click to view recipe]({recipe_link})",
        )
    web_page = "[Recipe Search on Nori-Web](https://nori.fish/wynn/recipe/)"
    embed.add_field(f"[{page}/{total_pages}]", web_page)
    embed.set_footer("Nori Bot - Wynn Recipes")
    return embed


class RecipeView(miru.View):
    def __init__(self, user_id: int, timeout: float = 60):
        super().__init__(timeout=timeout)
        self.user_id = user_id

    async def _edit_page(self, ctx: miru.Context, direction: int):
        state = recipe_data.get(self.user_id)
        if not state:
            await ctx.edit_response("Recipe search session expired.", components=[])
            self.stop()
            return

        total_pages = len(state["pages"])
        page = state["page"] + direction
        if page < 1:
            page = total_pages
        elif page > total_pages:
            page = 1
        state["page"] = page

        page_results = state["pages"][page - 1]
        embed = _recipe_embed(page_results, state["tags"], page, total_pages, state["count"])
        await ctx.edit_response(embed=embed)

    @miru.button(emoji="⬅", style=hikari.ButtonStyle.SECONDARY)
    async def button_previous(self, button: miru.Button, ctx: miru.Context):
        await self._edit_page(ctx, -1)

    @miru.button(emoji="➡", style=hikari.ButtonStyle.SECONDARY)
    async def button_next(self, button: miru.Button, ctx: miru.Context):
        await self._edit_page(ctx, 1)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as error:
            print(f"Failed to edit message on timeout: {error}")


def load_recipe_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load recipe commands."""

    @bot.command()
    @lightbulb.command("recipe", "Crafted recipes")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def recipe(ctx: lightbulb.Context):
        pass

    @recipe.child()
    @lightbulb.option("keyword_3", "3rd Keyword", required=False, default=None)
    @lightbulb.option("keyword_2", "2nd Keyword", required=False, default=None)
    @lightbulb.option("keyword_1", "1st Keyword", required=True)
    @lightbulb.command("search", "Look for specific recipe with key words")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def recipe_search(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)

        tag_2 = ctx.options.keyword_2
        tag_3 = ctx.options.keyword_3
        tags = [ctx.options.keyword_1]
        tags.append(tag_2) if tag_2 else None
        tags.append(tag_3) if tag_3 else None
        tags_text = ", ".join(tags)

        result = await recipe_file_search(tags)
        search_result = result["Result"]
        recipes_found = len(search_result)
        if not search_result:
            server_link = "https://discord.gg/tU7eaKAWb2"
            result_embed = hikari.Embed(
                title=f"No result found with tag: __{tags_text}__",
                color="#FF0000",
            )
            result_embed.add_field(
                "Can't find a specific type of recipe?",
                f"feel free to suggest or request it in the support server\n[Click to join]({server_link})",
            )
            await ctx.respond(embed=result_embed)
            return

        pages = _chunk_results(search_result, 10)
        user_id = ctx.user.id
        recipe_data[user_id] = {
            "page": 1,
            "pages": pages,
            "count": recipes_found,
            "tags": tags,
        }

        embed = _recipe_embed(pages[0], tags, 1, len(pages), recipes_found)
        if len(pages) > 1:
            view = RecipeView(user_id=user_id, timeout=60)
            message = await ctx.respond(embed=embed, components=view.build())
            message = await message
            await view.start(message)
            await view.wait()
        else:
            await ctx.respond(embed=embed)

    @recipe.child()
    @lightbulb.add_checks(contributor_only())
    @lightbulb.option("link", "WynnCrafter Link")
    @lightbulb.option("keywords", "Recipe Tags (keywords)")
    @lightbulb.option("recipe_type", "Recipe Item Type (Wand, Boots, Food, etc..)")
    @lightbulb.option("name", "Name of the Recipe")
    @lightbulb.command("submit", "Submit Recipe (Contributor Only)")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def recipe_submit(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        recipe_submission = {
            ctx.options.name: {
                "type": ctx.options.recipe_type,
                "link": ctx.options.link,
                "tag": ctx.options.keywords,
            }
        }
        await recipe_file_updater(recipe_submission)

        user = await bot.rest.fetch_user(ctx.user.id)
        username = user.username
        recipe_embed = hikari.Embed(
            title="Recipe Submission",
            description=f"Uploaded by {username}",
            color="#E4A3FC",
        )
        recipe_embed.add_field(
            f"Title: {ctx.options.name}",
            f"Keywords: {ctx.options.keywords}\n[{ctx.options.recipe_type} Recipe]({ctx.options.link})",
        )
        recipe_embed.set_footer("Nori Bot - Maintainer Tools")
        await ctx.respond(recipe_embed)

    @recipe.child()
    @lightbulb.add_checks(contributor_only())
    @lightbulb.option("name", "Name of the Recipe")
    @lightbulb.command("remove", "Remove Recipe (Contributor Only)")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def recipe_remove(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        remove_result = await recipe_file_remove(ctx.options.name)
        user = await bot.rest.fetch_user(ctx.user.id)
        username = user.username
        result = (
            f"Successfully removed {ctx.options.name} from db"
            if remove_result
            else f"Cannot find {ctx.options.name} in db, try another name?"
        )
        recipe_embed = hikari.Embed(
            title=f"Recipe deletion by {username}",
            description=result,
            color="#E4A3FC",
        )
        recipe_embed.set_footer("Nori Bot - Maintainer Tools")
        await ctx.respond(recipe_embed)

