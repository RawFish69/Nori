"""Item-related views."""

import miru
import hikari
from lib.config import item_amp_data


class ampView(miru.View):
    """View for item amplifier/reroll interactions."""
    
    def __init__(self, timeout: float = 60.0):
        super().__init__(timeout=timeout)
    
    @miru.button(label="Reroll", style=hikari.ButtonStyle.PRIMARY)
    async def btn_reroll(self, button: miru.Button, ctx: miru.Context):
        user = await ctx.bot.rest.fetch_user(ctx.user.id)
        if user in item_amp_data:
            data = item_amp_data[user]
            data["rr"] += 1
            await ctx.edit_response("Rerolling...")
        else:
            await ctx.edit_response("No active item roll session.")
    
    @miru.button(label="Stop", style=hikari.ButtonStyle.DANGER)
    async def btn_stop(self, button: miru.Button, ctx: miru.Context):
        await ctx.edit_response("Rolling stopped.", components=[])
        self.stop()
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as e:
            print(f"Failed to edit message on timeout: {e}")


class lootView(miru.View):
    """View for lootpool selection."""
    
    def __init__(self, timeout: float = 120.0):
        super().__init__(timeout=timeout)
    
    @miru.button(label="Current Week", style=hikari.ButtonStyle.PRIMARY)
    async def btn_current(self, button: miru.Button, ctx: miru.Context):
        from lib.config import lootpool_data
        await ctx.edit_response(f"Current lootpool: {lootpool_data}")
    
    @miru.button(label="Stop", style=hikari.ButtonStyle.DANGER)
    async def btn_stop(self, button: miru.Button, ctx: miru.Context):
        await ctx.edit_response("Selection stopped.", components=[])
        self.stop()
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as e:
            print(f"Failed to edit message on timeout: {e}")

