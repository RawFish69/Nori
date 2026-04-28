"""Basic utility commands."""
import time
import hikari
import lightbulb
loader = lightbulb.Loader()

@loader.command
class Ping(lightbulb.SlashCommand, name='ping', description='Checks the command response latency'):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        start_time = time.time()
        await ctx.respond('Calculating latency in real time...', flags=hikari.MessageFlag.LOADING)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        await ctx.edit_response(-1, f'Command response latency: {latency:.2f} ms')
