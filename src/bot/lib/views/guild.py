"""Guild XP and tower utility views."""

import hikari
import miru

from lib.config import BOT_PATH


class _BaseView(miru.View):
    async def _send_file(self, ctx: miru.ViewContext, filename: str):
        await ctx.edit_response(hikari.File(str(BOT_PATH / filename)))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as error:
            print(f"view timeout update failed: {error}")


class gxpView(_BaseView):
    """Guild XP graph selector view."""

    @miru.button(label="1-50", style=hikari.ButtonStyle.PRIMARY)
    async def btn_one(self, ctx: miru.ViewContext, button: miru.Button):
        await self._send_file(ctx, "xp_a.png")

    @miru.button(label="51-100", style=hikari.ButtonStyle.PRIMARY)
    async def btn_two(self, ctx: miru.ViewContext, button: miru.Button):
        await self._send_file(ctx, "xp_b.png")

    @miru.button(label="101-130", style=hikari.ButtonStyle.PRIMARY)
    async def btn_three(self, ctx: miru.ViewContext, button: miru.Button):
        await self._send_file(ctx, "xp_c.png")


class GuildStatsView(miru.View):
    """Toggle guild stats between main info and online members."""

    def __init__(self, main_embed: hikari.Embed, online_embed: hikari.Embed, timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.main_embed = main_embed
        self.online_embed = online_embed

    @miru.button(label="Main Info", style=hikari.ButtonStyle.PRIMARY)
    async def btn_main(self, ctx: miru.ViewContext, button: miru.Button):
        await ctx.edit_response(embed=self.main_embed, components=self.build())

    @miru.button(label="Online Members", style=hikari.ButtonStyle.SECONDARY)
    async def btn_online(self, ctx: miru.ViewContext, button: miru.Button):
        await ctx.edit_response(embed=self.online_embed, components=self.build())

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as error:
            print(f"guild stats view timeout update failed: {error}")


class hqView(_BaseView):
    """HQ tower helper view."""

    @miru.button(label="Visual", style=hikari.ButtonStyle.PRIMARY)
    async def btn_graph(self, ctx: miru.ViewContext, button: miru.Button):
        await self._send_file(ctx, "hq_tower_stats.png")

    @miru.button(label="Close", style=hikari.ButtonStyle.DANGER)
    async def btn_close(self, ctx: miru.ViewContext, button: miru.Button):
        await ctx.edit_response(components=[], attachments=[])
        self.stop()


class towerView(_BaseView):
    """Regular tower helper view."""

    @miru.button(label="Damage", style=hikari.ButtonStyle.PRIMARY)
    async def btn_dmg(self, ctx: miru.ViewContext, button: miru.Button):
        await self._send_file(ctx, "tower_damage.png")

    @miru.button(label="DPS", style=hikari.ButtonStyle.PRIMARY)
    async def btn_dps(self, ctx: miru.ViewContext, button: miru.Button):
        await self._send_file(ctx, "tower_dps.png")

    @miru.button(label="EHP", style=hikari.ButtonStyle.PRIMARY)
    async def btn_ehp(self, ctx: miru.ViewContext, button: miru.Button):
        await self._send_file(ctx, "tower_ehp.png")

    @miru.button(label="Close", style=hikari.ButtonStyle.DANGER)
    async def btn_close(self, ctx: miru.ViewContext, button: miru.Button):
        await ctx.edit_response(components=[], attachments=[])
        self.stop()
