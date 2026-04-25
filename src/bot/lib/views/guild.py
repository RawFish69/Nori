"""Guild and tower utility views for modular nori_bot."""

import hikari
import miru


class _BaseView(miru.View):
    """Shared base view with safe timeout handling."""

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if hasattr(self, "message") and self.message is not None:
                await self.message.edit(components=self.build())
        except Exception as error:
            print(f"view timeout update failed: {error}")


class gxpView(_BaseView):
    """Guild XP graph selector view."""

    def __init__(self, timeout: float = 120.0):
        super().__init__(timeout=timeout)

    @miru.button(label="Close", style=hikari.ButtonStyle.DANGER)
    async def btn_close(self, button: miru.Button, ctx: miru.Context):
        await ctx.edit_response("GXP menu closed.", components=[])
        self.stop()


class hqView(_BaseView):
    """HQ tower helper view."""

    def __init__(self, timeout: float = 120.0):
        super().__init__(timeout=timeout)

    @miru.button(label="Close", style=hikari.ButtonStyle.DANGER)
    async def btn_close(self, button: miru.Button, ctx: miru.Context):
        await ctx.edit_response("HQ menu closed.", components=[])
        self.stop()


class towerView(_BaseView):
    """Regular tower helper view."""

    def __init__(self, timeout: float = 120.0):
        super().__init__(timeout=timeout)

    @miru.button(label="Close", style=hikari.ButtonStyle.DANGER)
    async def btn_close(self, button: miru.Button, ctx: miru.Context):
        await ctx.edit_response("Tower menu closed.", components=[])
        self.stop()

