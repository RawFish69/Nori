"""Interactive view for the `/worldevent` slash command."""

from __future__ import annotations

import math

import hikari
import miru

from lib.commands.world_events import (
    _DEFAULT_PAGE_SIZE,
    _DEFAULT_SORT,
    _VIEW_TIMEOUT_SECONDS,
    SORT_MODES,
    build_world_events_page_embed,
)


class WorldEventsView(miru.View):
    """Paginated view for `/worldevent`. Buttons advance through a pre-sorted list."""

    def __init__(
        self,
        payload: dict,
        sort: str,
        page_size: int = _DEFAULT_PAGE_SIZE,
        timeout: float = _VIEW_TIMEOUT_SECONDS,
    ):
        super().__init__(timeout=timeout)
        self._payload = payload
        self._sort = sort if sort in SORT_MODES else _DEFAULT_SORT
        self._page_size = page_size
        self._page = 0
        events = payload.get("data") or []
        self._total_pages = max(1, math.ceil(len(events) / page_size)) if events else 1
        self._sync_button_state()

    @property
    def sort(self) -> str:
        return self._sort

    @property
    def page_size(self) -> int:
        return self._page_size

    def _sync_button_state(self) -> None:
        # Children are in declaration order: prev, next.
        prev_btn, next_btn = self.children[0], self.children[1]
        prev_btn.disabled = self._page <= 0
        next_btn.disabled = self._page >= self._total_pages - 1

    async def _render(self, ctx: miru.ViewContext) -> None:
        self._sync_button_state()
        embed = build_world_events_page_embed(
            self._payload, page=self._page, page_size=self._page_size, sort=self._sort
        )
        await ctx.edit_response(embed=embed, components=self.build())

    @miru.button(label="« Prev", style=hikari.ButtonStyle.SECONDARY)
    async def prev_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self._page = max(0, self._page - 1)
        await self._render(ctx)

    @miru.button(label="Next »", style=hikari.ButtonStyle.SECONDARY)
    async def next_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self._page = min(self._total_pages - 1, self._page + 1)
        await self._render(ctx)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception:
            pass
