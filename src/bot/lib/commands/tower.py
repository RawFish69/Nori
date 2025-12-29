"""Tower calculation commands."""

import hikari
import lightbulb
from lib.utils import check_user_access
from lib.tower_utils import hq_stats, tower_stats
from lib.views.guild import hqView, towerView


def load_tower_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load tower calculation commands."""
    
    @bot.command()
    @lightbulb.option('defense', 'Defense level, default = 11', type=int, default=11, min_value=0, max_value=11, required=False)
    @lightbulb.option('hp', 'Health level, default = 11', type=int, default=11, min_value=0, max_value=11, required=False)
    @lightbulb.option('attack', 'Attack speed level, default = 11', type=int, default=11, min_value=0, max_value=11, required=False)
    @lightbulb.option('damage', 'Damage level, default = 11', type=int, default=11, min_value=0, max_value=11, required=False)
    @lightbulb.option('externals', 'Externals of the HQ', type=int, min_value=0, max_value=50)
    @lightbulb.option('links', 'Links of the HQ', type=int, min_value=0, max_value=6)
    @lightbulb.command('hq', 'Calculate HQ Tower Stats')
    @lightbulb.implements(lightbulb.SlashCommand)
    async def get_hq(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        links = ctx.options.links
        ext = ctx.options.externals
        damage = ctx.options.damage
        attack = ctx.options.attack
        hp = ctx.options.hp
        defense = ctx.options.defense
        display = hq_stats(links, ext, damage, attack, hp, defense)
        header = f'Links: {links}, Externals: {ext}, Upgrades: {damage}/{attack}/{hp}/{defense}'
        hq_embed = hikari.Embed(title=f"HQ Tower Stats", color="#6BFA44")
        hq_embed.add_field(header, f"```json\n{display}```")
        hq_embed.set_footer("Nori Bot - Guild War Tools")
        hq_view = hqView(timeout=120)
        message = await ctx.respond(embed=hq_embed, components=hq_view.build())
        message = await message
        await hq_view.start(message)
        await hq_view.wait()

    @bot.command()
    @lightbulb.option('defense', 'Defense level, default = 11', type=int, default=11, min_value=0, max_value=11, required=False)
    @lightbulb.option('hp', 'Health level, default = 11', type=int, default=11, min_value=0, max_value=11, required=False)
    @lightbulb.option('attack', 'Attack speed level, default = 11', type=int, default=11, min_value=0, max_value=11, required=False)
    @lightbulb.option('damage', 'Damage level, default = 11', type=int, default=11, min_value=0, max_value=11, required=False)
    @lightbulb.option('links', 'Links to the territory', type=int, min_value=0, max_value=6)
    @lightbulb.command('tower', 'Calculate Non-HQ Tower Stats')
    @lightbulb.implements(lightbulb.SlashCommand)
    async def get_tower(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        links = ctx.options.links
        damage = ctx.options.damage
        attack = ctx.options.attack
        hp = ctx.options.hp
        defense = ctx.options.defense
        display = tower_stats(links, damage, attack, hp, defense)
        header = f'Links: {links}, Upgrades: {damage}/{attack}/{hp}/{defense}'
        tower_embed = hikari.Embed(title=f"Tower Stats", color="#F5FA44")
        tower_embed.add_field(header, f"```json\n{display}```")
        tower_embed.set_footer("Nori Bot - Guild War Tools")
        tower_view = towerView(timeout=120)
        message = await ctx.respond(embed=tower_embed, components=tower_view.build())
        message = await message
        await tower_view.start(message)
        await tower_view.wait()

