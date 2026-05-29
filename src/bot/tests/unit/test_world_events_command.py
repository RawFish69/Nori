"""Tests for the `/worldevent` embed builder and reward filter."""

from __future__ import annotations

import json
from pathlib import Path

import hikari

from lib.commands.world_events import (
    _DEFAULT_PAGE_SIZE,
    _WORLD_BOSS_PREFIX,
    _filter_top_tier_rewards,
    _schedule_to_unix,
    build_world_events_embed,
    build_world_events_page_embed,
    sort_events,
)

WORLD_BOSS = "Prelude to Annihilation"

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "official_world_events.json"
)


def _embed_text(embed: hikari.Embed) -> str:
    parts: list[str] = []
    if embed.title:
        parts.append(embed.title)
    if embed.description:
        parts.append(embed.description)
    for field in embed.fields:
        parts.append(field.name)
        parts.append(field.value)
    return "\n".join(parts)


def _success_payload(events: list[dict]) -> dict:
    return {"ok": True, "data": events, "source": "official"}


def test_build_world_events_embed_with_scheduled():
    event = {
        "name": "Test Scheduled Event",
        "schedule": {"unixTimestamp": 1717000000},
        "requirements": [],
        "rewardPerLevel": [],
        "location": [],
    }
    text = _embed_text(build_world_events_embed(_success_payload([event])))
    assert "<t:1717000000:R>" in text
    assert "Next run:" in text


def test_build_world_events_embed_no_schedule():
    event = {
        "name": "Unscheduled Event",
        "schedule": None,
        "requirements": [],
        "rewardPerLevel": [],
        "location": [],
    }
    text = _embed_text(build_world_events_embed(_success_payload([event])))
    assert "Next run unknown" in text


def test_requirements_rendered():
    event = {
        "name": "Gated Event",
        "schedule": None,
        "requirements": [
            {"type": "COMBAT_LEVEL", "value": 50},
            {"type": "QUEST", "value": "Recover the Past"},
        ],
        "rewardPerLevel": [],
        "location": [],
    }
    text = _embed_text(build_world_events_embed(_success_payload([event])))
    assert "Combat Level: 50" in text
    assert "Quest: Recover the Past" in text


def test_rewards_filtered_to_top_tier():
    rewards = [
        {"name": "Stratiformis", "tier": "MYTHIC", "always": False},
        {"name": "Garnet", "tier": "FABLED", "always": False},
        {"name": "Iron Ingot", "tier": "COMMON", "always": False},
        {"name": "Gold Pouch", "tier": None, "always": True},
    ]
    filtered = _filter_top_tier_rewards(rewards)
    names = {entry["name"] for entry in filtered}
    assert names == {"Stratiformis", "Garnet", "Gold Pouch"}


def test_location_rendered():
    event = {
        "name": "Multi-spot Event",
        "schedule": None,
        "requirements": [],
        "rewardPerLevel": [],
        "location": [
            {"x": -442, "y": 56, "z": -1897},
            {"x": 100, "y": 70, "z": 200},
        ],
    }
    text = _embed_text(build_world_events_embed(_success_payload([event])))
    # Only the first coordinate is shown in the compact format
    assert "-442, 56, -1897" in text


def test_empty_payload():
    payload = {"ok": False, "error": "timeout", "detail": "request timed out: read timeout"}
    text = _embed_text(build_world_events_embed(payload))
    assert "World events temporarily unavailable" in text


def test_fixture_replay_does_not_crash():
    with FIXTURE_PATH.open(encoding="utf-8") as f:
        events = json.load(f)
    assert len(events) >= 5
    subset = events[:5]
    embed = build_world_events_embed(_success_payload(subset))
    assert len(embed.fields) >= len(subset)
    for field in embed.fields[: len(subset)]:
        assert field.value
        assert "Next run:" in field.value


def _embed_total_chars(embed: hikari.Embed) -> int:
    total = 0
    if embed.title:
        total += len(embed.title)
    if embed.description:
        total += len(embed.description)
    if embed.footer and embed.footer.text:
        total += len(embed.footer.text)
    for field in embed.fields:
        total += len(field.name) + len(field.value)
    return total


def test_embed_stays_under_discord_6000_char_limit():
    events = []
    for i in range(50):
        events.append(
            {
                "name": f"Event {i} with a moderately long display name",
                "schedule": None,
                "requirements": [{"type": "COMBAT_LEVEL", "value": 80}] * 4,
                "rewardPerLevel": {
                    "1": ["Various Items and Ingredients", "+Exclusive Item " + "x" * 80],
                    "13": ["+Infested Pit Key " + "y" * 80],
                },
                "location": [
                    {"event": {"x": -442 - i, "y": 56, "z": -1897 + i}},
                    {"event": {"x": 100 + i, "y": 70, "z": 200 - i}},
                ],
            }
        )
    embed = build_world_events_embed(_success_payload(events))
    assert _embed_total_chars(embed) <= 6000
    assert len(embed.fields) >= 1
    assert "of 50 world event" in embed.description


def test_schedule_to_unix_handles_all_shapes():
    from datetime import datetime, timezone

    expected_iso = int(datetime(2026, 5, 27, 13, 9, 0, tzinfo=timezone.utc).timestamp())
    assert _schedule_to_unix(None) is None
    assert _schedule_to_unix(1717000000) == 1717000000
    assert _schedule_to_unix(1717000000.5) == 1717000000
    assert _schedule_to_unix({"unixTimestamp": 1717000000}) == 1717000000
    assert _schedule_to_unix("2026-05-27T13:09:00+00:00") == expected_iso
    assert _schedule_to_unix("2026-05-27T13:09:00Z") == expected_iso
    assert _schedule_to_unix("garbage") is None


def test_sort_events_by_level_descending():
    events = [
        {"name": "A", "level": 30},
        {"name": "B", "level": 80},
        {"name": "C", "level": 55},
        {"name": "D"},  # missing level
    ]
    out = sort_events(events, "level")
    assert [e["name"] for e in out] == ["B", "C", "A", "D"]


def test_sort_events_by_time_puts_nulls_last():
    events = [
        {"name": "late", "schedule": "2026-05-27T13:30:00+00:00", "level": 50},
        {"name": "no_schedule_high_lvl", "schedule": None, "level": 90},
        {"name": "soon", "schedule": "2026-05-27T13:09:00+00:00", "level": 75},
        {"name": "no_schedule_low_lvl", "schedule": None, "level": 20},
    ]
    out = sort_events(events, "time")
    assert [e["name"] for e in out] == [
        "soon",
        "late",
        "no_schedule_high_lvl",
        "no_schedule_low_lvl",
    ]


def test_page_embed_slices_and_labels():
    events = [{"name": f"Event {i}", "level": i, "schedule": None} for i in range(20)]
    embed = build_world_events_page_embed(
        _success_payload(events), page=1, page_size=8, sort="level"
    )
    # Page 2 of 3 (zero-indexed page=1), 8 events shown.
    assert len(embed.fields) == 8
    assert "Page 2 of 3" in embed.description
    assert "events 9–16 of 20" in embed.description
    assert "level" in embed.description
    # Highest-level event (19) is on page 0, not here.
    field_names = {f.name for f in embed.fields}
    assert not any("Event 19" in n for n in field_names)
    assert any("Event 11" in n for n in field_names)


def test_page_embed_last_page_partial():
    events = [{"name": f"E{i}", "level": i, "schedule": None} for i in range(11)]
    embed = build_world_events_page_embed(
        _success_payload(events), page=1, page_size=8, sort="level"
    )
    assert len(embed.fields) == 3
    assert "events 9–11 of 11" in embed.description


def test_page_embed_clamps_out_of_range_page():
    events = [{"name": "x", "level": 10, "schedule": None}]
    embed = build_world_events_page_embed(
        _success_payload(events), page=999, page_size=8, sort="level"
    )
    assert len(embed.fields) == 1
    assert "Page 1 of 1" in embed.description


def test_page_embed_falls_back_for_error_payload():
    payload = {"ok": False, "error": "timeout", "detail": "..."}
    embed = build_world_events_page_embed(payload, page=0, page_size=8, sort="time")
    text = _embed_text(embed)
    assert "World events temporarily unavailable" in text


def test_page_embed_stays_under_6000_chars():
    events = []
    for i in range(50):
        events.append(
            {
                "name": f"Event {i} with a moderately long display name",
                "schedule": None,
                "level": i,
                "requirements": [{"type": "COMBAT_LEVEL", "value": 80}] * 4,
                "rewardPerLevel": {
                    "1": ["Various Items and Ingredients", "+Exclusive Item " + "x" * 80],
                    "13": ["+Infested Pit Key " + "y" * 80],
                },
                "location": [
                    {"event": {"x": -442 - i, "y": 56, "z": -1897 + i}},
                    {"event": {"x": 100 + i, "y": 70, "z": 200 - i}},
                ],
            }
        )
    embed = build_world_events_page_embed(
        _success_payload(events), page=0, page_size=_DEFAULT_PAGE_SIZE, sort="level"
    )
    assert _embed_total_chars(embed) <= 6000
    assert len(embed.fields) == _DEFAULT_PAGE_SIZE


def test_scheduled_world_boss_pins_to_front_regardless_of_sort():
    boss = {"name": WORLD_BOSS, "schedule": "2026-05-27T16:08:00+00:00", "level": 105}
    early_lower = {"name": "Tiny", "schedule": "2026-05-27T15:00:00+00:00", "level": 3}
    no_schedule_high = {"name": "Bigger", "schedule": None, "level": 100}
    events = [no_schedule_high, early_lower, boss]
    # Sort by time: tiny is soonest, then boss, then no-schedule. With pinning, boss MUST be first.
    out_time = sort_events(events, "time")
    assert out_time[0]["name"] == WORLD_BOSS
    # Sort by level: bigger=100, boss=105, tiny=3. Without pinning, boss would be 0 anyway,
    # but with no-schedule events level=100 sometimes ties; pinning guarantees first slot.
    out_level = sort_events(events, "level")
    assert out_level[0]["name"] == WORLD_BOSS


def test_unscheduled_world_boss_does_not_pin():
    boss_unscheduled = {"name": WORLD_BOSS, "schedule": None, "level": 105}
    high = {"name": "Top", "schedule": "2026-05-27T15:00:00+00:00", "level": 50}
    events = [boss_unscheduled, high]
    out = sort_events(events, "time")
    # high has a schedule; boss does not. high comes first per time sort, boss falls to null bucket.
    assert out[0]["name"] == "Top"


def test_world_boss_field_name_and_value_have_callout():
    boss = {
        "name": WORLD_BOSS,
        "schedule": "2026-05-27T16:08:00+00:00",
        "level": 105,
        "requirements": [],
        "rewardPerLevel": {},
        "location": [],
    }
    embed = build_world_events_page_embed(
        _success_payload([boss]), page=0, page_size=8, sort="time"
    )
    assert len(embed.fields) == 1
    field = embed.fields[0]
    assert field.name.startswith(_WORLD_BOSS_PREFIX)
    assert WORLD_BOSS in field.name
    assert "Lv 105" in field.name
    assert "WORLD BOSS" in field.value
    # Schedule still rendered as Discord relative timestamp.
    assert "<t:" in field.value


def test_filter_dict_of_strings_dedupes_preserve_order():
    rewards = {
        "1": ["Various Items and Ingredients", "+Exclusive Item"],
        "13": ["+Infested Pit Key", "Various Items and Ingredients"],
    }
    assert _filter_top_tier_rewards(rewards) == [
        "Various Items and Ingredients",
        "+Exclusive Item",
        "+Infested Pit Key",
    ]
