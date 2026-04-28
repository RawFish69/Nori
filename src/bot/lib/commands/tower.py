"""Tower calculation commands."""
import hikari
import lightbulb
from lib.tower_utils import hq_stats, tower_stats
from lib.views.guild import hqView, towerView
loader = lightbulb.Loader()

@loader.command
class GetHq(lightbulb.SlashCommand, name='hq', description='Calculate HQ Tower Stats'):
    links = lightbulb.integer('links', 'Links of the HQ', min_value=0, max_value=6)
    externals = lightbulb.integer('externals', 'Externals of the HQ', min_value=0, max_value=50)
    damage = lightbulb.integer('damage', 'Damage level, default = 11', default=11, min_value=0, max_value=11)
    attack = lightbulb.integer('attack', 'Attack speed level, default = 11', default=11, min_value=0, max_value=11)
    hp = lightbulb.integer('hp', 'Health level, default = 11', default=11, min_value=0, max_value=11)
    defense = lightbulb.integer('defense', 'Defense level, default = 11', default=11, min_value=0, max_value=11)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        links = self.links
        ext = self.externals
        damage = self.damage
        attack = self.attack
        hp = self.hp
        defense = self.defense
        display = hq_stats(links, ext, damage, attack, hp, defense)
        header = f'Links: {links}, Externals: {ext}, Upgrades: {damage}/{attack}/{hp}/{defense}'
        hq_embed = hikari.Embed(title=f'HQ Tower Stats', color='#6BFA44')
        hq_embed.add_field(header, f'```json\n{display}```')
        hq_embed.set_footer('Nori Bot - Guild War Tools')
        hq_view = hqView(timeout=120)
        message = await ctx.respond(embed=hq_embed, components=hq_view.build())
        message = await ctx.fetch_response(message)
        ctx.client.app.d.miru.start_view(hq_view, bind_to=message)
        await hq_view.wait()

@loader.command
class GetTower(lightbulb.SlashCommand, name='tower', description='Calculate Non-HQ Tower Stats'):
    links = lightbulb.integer('links', 'Links to the territory', min_value=0, max_value=6)
    damage = lightbulb.integer('damage', 'Damage level, default = 11', default=11, min_value=0, max_value=11)
    attack = lightbulb.integer('attack', 'Attack speed level, default = 11', default=11, min_value=0, max_value=11)
    hp = lightbulb.integer('hp', 'Health level, default = 11', default=11, min_value=0, max_value=11)
    defense = lightbulb.integer('defense', 'Defense level, default = 11', default=11, min_value=0, max_value=11)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        links = self.links
        damage = self.damage
        attack = self.attack
        hp = self.hp
        defense = self.defense
        display = tower_stats(links, damage, attack, hp, defense)
        header = f'Links: {links}, Upgrades: {damage}/{attack}/{hp}/{defense}'
        tower_embed = hikari.Embed(title=f'Tower Stats', color='#F5FA44')
        tower_embed.add_field(header, f'```json\n{display}```')
        tower_embed.set_footer('Nori Bot - Guild War Tools')
        tower_view = towerView(timeout=120)
        message = await ctx.respond(embed=tower_embed, components=tower_view.build())
        message = await ctx.fetch_response(message)
        ctx.client.app.d.miru.start_view(tower_view, bind_to=message)
        await tower_view.wait()
