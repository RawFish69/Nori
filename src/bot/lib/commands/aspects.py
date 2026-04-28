"""Deprecated aspect command aliases."""
import hikari
import lightbulb
loader = lightbulb.Loader()
aspect = lightbulb.Group('aspect', 'Deprecated raid alias')

@aspect.register
class ShowAspectLootpoolDeprecated(lightbulb.SlashCommand, name='lootpool', description='Deprecated command alias'):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        deprecation_msg = '`/aspect lootpool` is deprecated.\nUse one of these commands instead:\n- `/raid aspect`\n- `/raid gambit`\n- `/raid item`'
        await ctx.respond(deprecation_msg, flags=hikari.MessageFlag.EPHEMERAL)
loader.command(aspect)
