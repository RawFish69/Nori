"""Menu views for the bot."""

import time
import miru
import hikari
from lib.config import deploy_time, mode, engine


class TheView(miru.View):
    """Main menu view."""
    
    @miru.button(label="Server", style=hikari.ButtonStyle.PRIMARY)
    async def btn_apply(self, button: miru.Button, ctx: miru.Context):
        server_link = "https://discord.gg/tU7eaKAWb2"
        await ctx.edit_response(f"Join my server if you have any questions or feedback:\n{server_link} ")

    @miru.button(label="Help", style=hikari.ButtonStyle.PRIMARY)
    async def btn_help(self, button: miru.Button, ctx: miru.Context):
        await ctx.edit_response("Do /help")

    @miru.button(label="Info", style=hikari.ButtonStyle.SUCCESS)
    async def button_info(self, button: miru.Button, ctx: miru.Context):
        current_time = time.time()
        up_time = int(current_time - deploy_time)
        minutes, seconds = divmod(up_time, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        time_display = f"**{days:2d}** d **{hours:2d}** h **{minutes:2d}** m **{seconds:2d}** s"
        version_info = f"__{mode}__ mode, **{engine}** language model. \nuptime: {time_display}"
        print(version_info)
        await ctx.edit_response(f"Nori is created and maintained by RawFish.\n{version_info}")

    @miru.button(label='Stop', style=hikari.ButtonStyle.DANGER, row=2)
    async def btn_stop(self, button: miru.button, ctx: miru.Context):
        await ctx.edit_response("Menu closed.", components=[])
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as e:
            print(f"Failed to edit message on timeout: {e}")

