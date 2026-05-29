"""`/worldevent` slash command backed by official `/v3/map/world-events`."""

from __future__ import annotations

import asyncio
import math
import time
from datetime import datetime
from typing import Any

import hikari
import lightbulb

from lib import wynn_map_api
from lib.lightbulb_compat import lb_choices

loader = lightbulb.Loader()

_TOP_TIERS = frozenset({"MYTHIC", "FABLED", "LEGENDARY"})

_CACHE: dict[Any, dict] = {}
_CACHE_TTL_SECONDS = 60

# Discord caps embeds at 25 fields; one field per event.
_MAX_EVENTS_RENDERED = 24

# Discord caps the *total* embed payload (title + description + all field
# names + all field values + footer) at 6000 chars. Leave headroom for the
# title/description/footer plus the trailing "N more not shown" note.
_EMBED_TOTAL_CHAR_BUDGET = 5800

WORLD_EVENTS_WEB_URL = "https://nori.fish/wynn/events"

SORT_MODES = ("time", "level")
_DEFAULT_SORT = "level"
_DEFAULT_PAGE_SIZE = 8
_VIEW_TIMEOUT_SECONDS = 180

# World-boss events get a callout in the embed and pin to the front of the
# list when they have a known next-run timer. Keyed by `name` because the
# upstream `internalName` is an 8-char hash that means nothing to us.
WORLD_BOSS_EVENT_NAMES: frozenset[str] = frozenset({"Prelude to Annihilation"})
_WORLD_BOSS_PREFIX = "🌍 WORLD BOSS — "
_WORLD_BOSS_CALLOUT = "**🌍 WORLD BOSS**"


def _filter_top_tier_rewards(rewards: Any) -> list:
    """Pick top-tier / always-on rewards from an event's `rewardPerLevel`.

    Live payload is `dict[level_str, list[str]]` with no tier metadata, so
    every string surfaces (deduped, lowest level first). Synthetic spec
    shape `list[{name, tier, always}]` filters to MYTHIC/FABLED/LEGENDARY
    or `always=True`.
    """
    if isinstance(rewards, list):
        out: list[dict] = []
        seen: set[str] = set()
        for entry in rewards:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            tier = entry.get("tier")
            always = bool(entry.get("always"))
            tier_str = tier.upper() if isinstance(tier, str) else None
            if not (always or tier_str in _TOP_TIERS):
                continue
            key = str(name) if name is not None else repr(entry)
            if key in seen:
                continue
            seen.add(key)
            out.append(entry)
        return out

    if isinstance(rewards, dict):
        out_strs: list[str] = []
        seen_strs: set[str] = set()

        def _sort_key(k: Any) -> tuple[int, Any]:
            try:
                return (0, int(k))
            except (TypeError, ValueError):
                return (1, str(k))

        for level_key in sorted(rewards.keys(), key=_sort_key):
            level_rewards = rewards[level_key]
            if not isinstance(level_rewards, list):
                continue
            for item in level_rewards:
                if not isinstance(item, str) or item in seen_strs:
                    continue
                seen_strs.add(item)
                out_strs.append(item)
        return out_strs

    return []


def _format_schedule_field(schedule: Any) -> str:
    """Render `schedule` (ISO-8601 string, `{unixTimestamp: N}`, or None)."""
    if schedule is None:
        return "Next run unknown"

    if isinstance(schedule, dict):
        value = schedule.get("unixTimestamp")
        if isinstance(value, (int, float)):
            return f"<t:{int(value)}:R>"

    if isinstance(schedule, str):
        parsed = _parse_iso_to_unix(schedule)
        if parsed is not None:
            return f"<t:{parsed}:R>"

    return "Next run unknown"



def _parse_iso_to_unix(value: str) -> int | None:
    if not value:
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return int(dt.timestamp())


def _normalize_req_type(raw: Any) -> str:
    if not isinstance(raw, str):
        return "?"
    return raw.replace("_", " ").title()


def _format_requirements(requirements: Any) -> list[str]:
    if not isinstance(requirements, list):
        return []
    lines: list[str] = []
    for req in requirements:
        if not isinstance(req, dict):
            continue
        lines.append(f"{_normalize_req_type(req.get('type'))}: {req.get('value', '?')}")
    return lines


def _get_first_coord(locations: Any) -> dict | None:
    if not isinstance(locations, list):
        return None
    for loc in locations:
        if not isinstance(loc, dict):
            continue
        for key in ("event", "spawn", "reward"):
            v = loc.get(key)
            if isinstance(v, dict) and "x" in v:
                return v
        if "x" in loc:
            return loc
    return None


def _format_rewards_lines(filtered: list) -> list[str]:
    lines: list[str] = []
    for entry in filtered:
        if isinstance(entry, str):
            lines.append(entry)
        elif isinstance(entry, dict):
            name = entry.get("name", "?")
            tier = entry.get("tier")
            if isinstance(tier, str) and tier:
                lines.append(f"{name} ({tier})")
            elif entry.get("always"):
                lines.append(f"{name} (always)")
            else:
                lines.append(str(name))
    return lines


def _truncate(text: str, limit: int = 1024) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _build_event_field_value(event: dict) -> str:
    parts: list[str] = []

    # Timer — one line
    schedule_str = _format_schedule_field(event.get("schedule"))
    if _is_world_boss(event):
        parts.append(f"🌍 **WORLD BOSS** · {schedule_str}")
    else:
        parts.append(f"Next run: {schedule_str}")

    # Requirements — one compact line
    req_lines = _format_requirements(event.get("requirements"))
    if req_lines:
        parts.append("Req: " + " · ".join(req_lines))

    # Rewards — up to 3, comma-separated on one line
    reward_lines = _format_rewards_lines(_filter_top_tier_rewards(event.get("rewardPerLevel")))
    if reward_lines:
        shown = reward_lines[:3]
        extra = len(reward_lines) - len(shown)
        rewards_str = ", ".join(shown)
        if extra:
            rewards_str += f" +{extra} more"
        parts.append(f"🎁 {rewards_str}")

    # Location — first coord only, compact
    coord = _get_first_coord(event.get("location"))
    if coord:
        parts.append(f"📍 {coord.get('x', '?')}, {coord.get('y', '?')}, {coord.get('z', '?')}")

    return _truncate("\n".join(parts))


def build_world_events_embed(payload: dict) -> hikari.Embed:
    """Build the embed shown by `/worldevent` from a `fetch_world_events` result."""
    if not payload.get("ok"):
        embed = hikari.Embed(
            title="World Events",
            description="World events temporarily unavailable",
            color="#c0aaff",
        )
        detail = payload.get("detail") or payload.get("error") or ""
        if detail:
            embed.add_field("Upstream error", _truncate(str(detail), 1024))
        embed.set_footer("Nori Bot - World Events")
        return embed

    events = payload.get("data") or []
    if not events:
        embed = hikari.Embed(
            title="World Events",
            description="No active world events right now.",
            color="#c0aaff",
        )
        embed.set_footer("Nori Bot - World Events")
        return embed

    title = "Wynncraft World Events"
    footer = "Nori Bot - World Events"
    # Reserve space for title + footer + a worst-case description.
    used = len(title) + len(footer) + 120
    candidates = events[:_MAX_EVENTS_RENDERED]
    rendered_fields: list[tuple[str, str]] = []
    for event in candidates:
        name = _format_event_field_name(event)
        value = _build_event_field_value(event) or "N/A"
        cost = len(name) + len(value)
        if used + cost > _EMBED_TOTAL_CHAR_BUDGET:
            break
        rendered_fields.append((name, value))
        used += cost

    skipped = len(events) - len(rendered_fields)
    description_parts = [f"Showing {len(rendered_fields)} of {len(events)} world event(s)."]
    if skipped > 0:
        description_parts.append(f"{skipped} additional event(s) not shown.")
    embed = hikari.Embed(
        title=title,
        description="\n".join(description_parts),
        color="#c0aaff",
    )
    for name, value in rendered_fields:
        embed.add_field(name, value)
    embed.set_footer(footer)
    return embed


def _is_world_boss(event: Any) -> bool:
    return isinstance(event, dict) and event.get("name") in WORLD_BOSS_EVENT_NAMES


def _format_event_field_name(event: dict) -> str:
    raw = str(event.get("name") or "Unknown event")
    label = f"{_WORLD_BOSS_PREFIX}{raw}" if _is_world_boss(event) else raw
    level = event.get("level")
    if isinstance(level, (int, float)):
        label = f"{label} · Lv {int(level)}"
    diff = event.get("difficulty")
    if isinstance(diff, str) and diff:
        label = f"{label} · {diff.title()}"
    return label[:256]


def _schedule_to_unix(schedule: Any) -> int | None:
    """Parse a schedule field (ISO-8601 string, dict, int, float, or None) to unix seconds."""
    if schedule is None:
        return None
    if isinstance(schedule, bool):
        return None
    if isinstance(schedule, (int, float)):
        return int(schedule)
    if isinstance(schedule, dict):
        value = schedule.get("unixTimestamp")
        if isinstance(value, (int, float)):
            return int(value)
    if isinstance(schedule, str):
        return _parse_iso_to_unix(schedule)
    return None


def _level_range_bucket(level: Any) -> int:
    """Map a level value to a sort bucket: 0 = 100+ (red), 1 = 60–99 (yellow), 2 = <60 (green)."""
    if not isinstance(level, (int, float)):
        return 2
    if level >= 100:
        return 0
    if level >= 60:
        return 1
    return 2


def sort_events(events: list, mode: str) -> list:
    """Sort events by level range then timer (default), or by timer alone.

    ``level`` mode (default): primary sort is level range high→low (100+, 60–99,
    <60). Within each range, scheduled events come first sorted by soonest timer;
    unscheduled events follow sorted by exact level descending.

    ``time`` mode: soonest scheduled first; unscheduled fall to the end broken
    by level descending.

    World bosses with a non-null schedule are pinned to the front after sorting,
    regardless of mode.
    """
    if mode == "time":
        def time_key(e: Any) -> tuple:
            ts = _schedule_to_unix(e.get("schedule") if isinstance(e, dict) else None)
            level = e.get("level") if isinstance(e, dict) else None
            level = int(level) if isinstance(level, (int, float)) else 0
            if ts is None:
                return (1, -level)
            return (0, ts)
        sorted_list = sorted(events, key=time_key)
    else:
        def _bucket(e: Any) -> int:
            return _level_range_bucket(e.get("level") if isinstance(e, dict) else None)

        def _lvl(e: Any) -> int:
            v = e.get("level") if isinstance(e, dict) else None
            return int(v) if isinstance(v, (int, float)) else 0

        with_timer = [e for e in events if _schedule_to_unix(
            e.get("schedule") if isinstance(e, dict) else None) is not None]
        no_timer = [e for e in events if _schedule_to_unix(
            e.get("schedule") if isinstance(e, dict) else None) is None]

        with_timer.sort(key=lambda e: (_bucket(e), _schedule_to_unix(
            e.get("schedule") if isinstance(e, dict) else None) or 0))
        no_timer.sort(key=lambda e: (_bucket(e), -_lvl(e)))

        sorted_list = with_timer + no_timer

    pinned: list = []
    rest: list = []
    for e in sorted_list:
        if _is_world_boss(e) and _schedule_to_unix(e.get("schedule")) is not None:
            pinned.append(e)
        else:
            rest.append(e)
    return pinned + rest


def build_world_events_page_embed(
    payload: dict,
    *,
    page: int,
    page_size: int,
    sort: str,
) -> hikari.Embed:
    """Build one page of the paginated `/worldevent` view.

    Falls back to :func:`build_world_events_embed` for error/empty payloads so
    those code paths stay in one place.
    """
    if not payload.get("ok") or not (payload.get("data") or []):
        return build_world_events_embed(payload)

    events = sort_events(payload["data"], sort)
    total = len(events)
    total_pages = max(1, math.ceil(total / page_size))
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    slice_ = events[start : start + page_size]

    sort_label = "time to next run" if sort == "time" else "level range (high → low), then timer"
    source = payload.get("source", "official")
    source_note = "\n⚠ Data from Wynncraft **beta** API" if source == "beta" else ""
    description = (
        f"Page {page + 1} of {total_pages} · "
        f"events {start + 1}–{start + len(slice_)} of {total} · "
        f"sorted by {sort_label}\n"
        f"[View all events on Nori-Web]({WORLD_EVENTS_WEB_URL})"
        f"{source_note}"
    )
    embed = hikari.Embed(
        title="Wynncraft World Events",
        description=description,
        color="#c0aaff",
    )
    for event in slice_:
        embed.add_field(
            _format_event_field_name(event),
            _build_event_field_value(event) or "N/A",
        )
    embed.set_footer(f"Nori Bot - World Events · sort: {sort}")
    return embed


def _cache_get_fresh() -> dict | None:
    entry = _CACHE.get(None)
    if entry is None or entry.get("expires_at", 0) <= time.time():
        return None
    return entry.get("data")


def _cache_put(payload: dict) -> None:
    _CACHE[None] = {"data": payload, "expires_at": time.time() + _CACHE_TTL_SECONDS}


@loader.command
class WorldEvent(
    lightbulb.SlashCommand,
    name="worldevent",
    description="Show upcoming Wynncraft world events",
):
    sort = lightbulb.string(
        "sort",
        "Order events by next-run time or by event level",
        choices=lb_choices(list(SORT_MODES)),
        default=_DEFAULT_SORT,
    )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.respond("Loading world events...", flags=hikari.MessageFlag.LOADING)
        cached = _cache_get_fresh()
        if cached is not None:
            payload = cached
        else:
            # Cache failures too — avoid retry-storming a degraded upstream.
            payload = await asyncio.to_thread(wynn_map_api.fetch_world_events)
            _cache_put(payload)

        sort_mode = self.sort if self.sort in SORT_MODES else _DEFAULT_SORT

        if not payload.get("ok") or not (payload.get("data") or []):
            embed = build_world_events_embed(payload)
            await ctx.edit_response(-1, embed=embed, content="")
            return

        # Lazy import keeps `lib/commands/world_events.py` miru-free for unit tests.
        from lib.views.world_events import WorldEventsView

        view = WorldEventsView(payload, sort=sort_mode)
        embed = build_world_events_page_embed(
            payload, page=0, page_size=view.page_size, sort=sort_mode
        )
        message = await ctx.edit_response(
            -1, embed=embed, content="", components=view.build()
        )
        ctx.client.app.d.miru.start_view(view, bind_to=message)
        await view.wait()
