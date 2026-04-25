"""Leaderboard-related views for modular nori_bot."""

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


class GuildLeaderboardView(_BaseView):
    """Guild leaderboard pager view."""

    def __init__(self, user_id: int | None = None, timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.user_id = user_id

    @miru.button(label="Close", style=hikari.ButtonStyle.DANGER)
    async def btn_close(self, button: miru.Button, ctx: miru.Context):
        await ctx.edit_response(components=[])
        self.stop()


class raidView(_BaseView):
    """Raid leaderboard selector view."""

    def __init__(self, timeout: float = 60.0):
        super().__init__(timeout=timeout)

    @miru.button(label="Close", style=hikari.ButtonStyle.DANGER)
    async def btn_close(self, button: miru.Button, ctx: miru.Context):
        await ctx.edit_response("Raid leaderboard menu closed.", components=[])
        self.stop()


class statView(_BaseView):
    """Stat leaderboard selector view."""

    def __init__(self, timeout: float = 60.0):
        super().__init__(timeout=timeout)

    @miru.button(label="Close", style=hikari.ButtonStyle.DANGER)
    async def btn_close(self, button: miru.Button, ctx: miru.Context):
        await ctx.edit_response("Stats leaderboard menu closed.", components=[])
        self.stop()


class prof_view(_BaseView):
    """Profession leaderboard selector view."""

    def __init__(self, timeout: float = 120.0):
        super().__init__(timeout=timeout)

    @miru.button(label="Close", style=hikari.ButtonStyle.DANGER)
    async def btn_close(self, button: miru.Button, ctx: miru.Context):
        await ctx.edit_response("Profession leaderboard menu closed.", components=[])
        self.stop()

