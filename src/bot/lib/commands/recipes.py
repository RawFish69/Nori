"""Recipe command group."""
import hikari
import lightbulb
import miru
from lib.build_recipe_utils import recipe_file_remove, recipe_file_search, recipe_file_updater
from lib.config import recipe_data
from lib.permissions import contributor_only
loader = lightbulb.Loader()

def _chunk_results(items, size=10):
    return [items[index:index + size] for index in range(0, len(items), size)]

def _recipe_embed(page_results, tags, page, total_pages, recipes_found):
    tags_text = ', '.join(tags)
    page_line = f'Page **{page}** of **{total_pages}**'
    embed = hikari.Embed(title=f'Recipes with keyword: __{tags_text}__', description=f'**{recipes_found}** Results found\n{page_line}', color='#E4A3FC')
    for index, recipe in enumerate(page_results, start=1):
        recipe_name = list(recipe.keys())[0]
        recipe_entry = recipe[recipe_name]
        recipe_tags = str(recipe_entry.get('tag', '') or '')
        recipe_link = recipe_entry.get('link', '')
        for tag in tags:
            tag_text = str(tag or '')
            if tag_text and tag_text.lower() in recipe_tags.lower():
                recipe_tags = recipe_tags.replace(tag_text, f'__{tag_text}__')
        embed.add_field(f'{index}. **{recipe_name}**', f'{recipe_tags}\n[Click to view recipe]({recipe_link})')
    web_page = '[Recipe Search on Nori-Web](https://nori.fish/wynn/recipe/)'
    embed.add_field(f'[{page}/{total_pages}]', web_page)
    embed.set_footer('Nori Bot - Wynn Recipes')
    return embed

class RecipeView(miru.View):

    def __init__(self, user_id: int, timeout: float=60):
        super().__init__(timeout=timeout)
        self.user_id = user_id

    async def _edit_page(self, ctx: miru.ViewContext, direction: int):
        state = recipe_data.get(self.user_id)
        if not state:
            await ctx.edit_response('Recipe search session expired.', components=[])
            self.stop()
            return
        total_pages = len(state['pages'])
        page = state['page'] + direction
        if page < 1:
            page = total_pages
        elif page > total_pages:
            page = 1
        state['page'] = page
        page_results = state['pages'][page - 1]
        embed = _recipe_embed(page_results, state['tags'], page, total_pages, state['count'])
        await ctx.edit_response(embed=embed)

    @miru.button(emoji='⬅', style=hikari.ButtonStyle.SECONDARY)
    async def button_previous(self, ctx: miru.ViewContext, button: miru.Button):
        await self._edit_page(ctx, -1)

    @miru.button(emoji='➡', style=hikari.ButtonStyle.SECONDARY)
    async def button_next(self, ctx: miru.ViewContext, button: miru.Button):
        await self._edit_page(ctx, 1)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as error:
            print(f'Failed to edit message on timeout: {error}')
recipe = lightbulb.Group('recipe', 'Crafted recipes')

@recipe.register
class RecipeSearch(lightbulb.SlashCommand, name='search', description='Look for specific recipe with key words'):
    keyword_1 = lightbulb.string('keyword_1', '1st Keyword')
    keyword_2 = lightbulb.string('keyword_2', '2nd Keyword', default=None)
    keyword_3 = lightbulb.string('keyword_3', '3rd Keyword', default=None)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        tag_2 = self.keyword_2
        tag_3 = self.keyword_3
        tags = [self.keyword_1]
        tags.append(tag_2) if tag_2 else None
        tags.append(tag_3) if tag_3 else None
        tags_text = ', '.join(tags)
        result = await recipe_file_search(tags)
        search_result = result['Result']
        recipes_found = len(search_result)
        if not search_result:
            server_link = 'https://discord.gg/tU7eaKAWb2'
            result_embed = hikari.Embed(title=f'No result found with tag: __{tags_text}__', color='#FF0000')
            result_embed.add_field("Can't find a specific type of recipe?", f'feel free to suggest or request it in the support server\n[Click to join]({server_link})')
            await ctx.respond(embed=result_embed)
            return
        pages = _chunk_results(search_result, 10)
        user_id = ctx.user.id
        recipe_data[user_id] = {'page': 1, 'pages': pages, 'count': recipes_found, 'tags': tags}
        embed = _recipe_embed(pages[0], tags, 1, len(pages), recipes_found)
        if len(pages) > 1:
            view = RecipeView(user_id=user_id, timeout=60)
            message = await ctx.respond(embed=embed, components=view.build())
            message = await ctx.fetch_response(message)
            ctx.client.app.d.miru.start_view(view, bind_to=message)
            await view.wait()
        else:
            await ctx.respond(embed=embed)

@recipe.register
class RecipeSubmit(lightbulb.SlashCommand, name='submit', description='Submit Recipe (Contributor Only)', hooks=[contributor_only()]):
    name = lightbulb.string('name', 'Name of the Recipe')
    recipe_type = lightbulb.string('recipe_type', 'Recipe Item Type (Wand, Boots, Food, etc..)')
    keywords = lightbulb.string('keywords', 'Recipe Tags (keywords)')
    link = lightbulb.string('link', 'WynnCrafter Link')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        recipe_submission = {self.name: {'type': self.recipe_type, 'link': self.link, 'tag': self.keywords}}
        await recipe_file_updater(recipe_submission)
        user = await ctx.client.app.rest.fetch_user(ctx.user.id)
        username = user.username
        recipe_embed = hikari.Embed(title='Recipe Submission', description=f'Uploaded by {username}', color='#E4A3FC')
        recipe_embed.add_field(f'Title: {self.name}', f'Keywords: {self.keywords}\n[{self.recipe_type} Recipe]({self.link})')
        recipe_embed.set_footer('Nori Bot - Maintainer Tools')
        await ctx.respond(recipe_embed)

@recipe.register
class RecipeRemove(lightbulb.SlashCommand, name='remove', description='Remove Recipe (Contributor Only)', hooks=[contributor_only()]):
    name = lightbulb.string('name', 'Name of the Recipe')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        remove_result = await recipe_file_remove(self.name)
        user = await ctx.client.app.rest.fetch_user(ctx.user.id)
        username = user.username
        result = f'Successfully removed {self.name} from db' if remove_result else f'Cannot find {self.name} in db, try another name?'
        recipe_embed = hikari.Embed(title=f'Recipe deletion by {username}', description=result, color='#E4A3FC')
        recipe_embed.set_footer('Nori Bot - Maintainer Tools')
        await ctx.respond(recipe_embed)
loader.command(recipe)
