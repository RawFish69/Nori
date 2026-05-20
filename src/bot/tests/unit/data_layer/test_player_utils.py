from unittest.mock import MagicMock, patch

import pytest

from lib.player_utils import (
    RAID_DISPLAY_ORDER,
    _format_date,
    _format_number,
    _render_combined_raid_clears,
    _render_raid_stats_block,
    _short_raid_map,
    player_stats,
)


# ---------------------------------------------------------------------------
# _format_number
# ---------------------------------------------------------------------------

class TestFormatNumber:
    def test_formats_with_commas(self):
        assert _format_number(1000000) == "1,000,000"

    def test_zero(self):
        assert _format_number(0) == "0"

    def test_none_returns_zero(self):
        assert _format_number(None) == "0"

    def test_string_number(self):
        assert _format_number("5000") == "5,000"

    def test_invalid_returns_zero(self):
        assert _format_number("abc") == "0"


# ---------------------------------------------------------------------------
# _format_date
# ---------------------------------------------------------------------------

class TestFormatDate:
    def test_formats_iso_datetime(self):
        assert _format_date("2024-06-01T12:00:00.000Z") == "2024-06-01"

    def test_empty_string_returns_na(self):
        assert _format_date("") == "N/A"

    def test_none_returns_na(self):
        assert _format_date(None) == "N/A"

    def test_unparseable_string_returned_as_is(self):
        assert _format_date("not-a-date") == "not-a-date"


# ---------------------------------------------------------------------------
# _short_raid_map
# ---------------------------------------------------------------------------

class TestShortRaidMap:
    def test_maps_known_raid_names(self):
        raid_list = {
            "Nest of the Grootslangs": 5,
            "The Nameless Anomaly": 3,
        }
        result = _short_raid_map(raid_list)
        assert result["NOG"] == 5
        assert result["TNA"] == 3

    def test_unknown_name_passes_through(self):
        result = _short_raid_map({"CustomRaid": 2})
        assert result["CustomRaid"] == 2

    def test_empty_dict(self):
        assert _short_raid_map({}) == {}

    def test_none_input(self):
        assert _short_raid_map(None) == {}

    def test_accumulates_duplicate_short_names(self):
        # "Unknown" maps to "TWP", same as "The Wartorn Palace"
        result = _short_raid_map({"The Wartorn Palace": 3, "Unknown": 2})
        assert result["TWP"] == 5


# ---------------------------------------------------------------------------
# _render_raid_stats_block
# ---------------------------------------------------------------------------

class TestRenderRaidStatsBlock:
    def test_returns_placeholder_when_empty(self):
        assert "No raid stats" in _render_raid_stats_block(None)
        assert "No raid stats" in _render_raid_stats_block({})

    def test_renders_known_labels(self):
        stats = {"damageDealt": 1000000, "deaths": 5}
        result = _render_raid_stats_block(stats)
        assert "Damage Dealt" in result
        assert "Deaths" in result

    def test_missing_keys_show_zero(self):
        result = _render_raid_stats_block({"damageDealt": 0})
        assert "0" in result


# ---------------------------------------------------------------------------
# _render_combined_raid_clears
# ---------------------------------------------------------------------------

class TestRenderCombinedRaidClears:
    def test_output_is_code_block(self):
        raids = {"total": 10, "list": {}}
        result = _render_combined_raid_clears(raids, {})
        assert result.startswith("```")
        assert result.endswith("```")

    def test_contains_all_raid_names(self):
        raids = {
            "total": 42,
            "list": {
                "The Nameless Anomaly": 8,
                "The Canyon Colossus": 12,
                "Orphion's Nexus of Light": 7,
                "Nest of the Grootslangs": 10,
                "The Wartorn Palace": 5,
            }
        }
        result = _render_combined_raid_clears(raids, {})
        for short in RAID_DISPLAY_ORDER:
            assert short in result

    def test_shows_all_row(self):
        raids = {"total": 99, "list": {}}
        result = _render_combined_raid_clears(raids, {})
        assert "All" in result
        assert "99" in result

    def test_handles_none_inputs(self):
        result = _render_combined_raid_clears(None, None)
        assert "```" in result


# ---------------------------------------------------------------------------
# player_stats
# ---------------------------------------------------------------------------

class TestPlayerStats:
    def _make_player_data(self):
        return {
            "uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "username": "TestPlayer",
            "online": False,
            "server": None,
            "rank": "Player",
            "supportRank": None,
            "shortenedRank": None,
            "firstJoin": "2020-01-01T00:00:00.000Z",
            "lastJoin": "2024-06-01T12:00:00.000Z",
            "playtime": 1234,
            "guild": {"name": "TestGuild", "prefix": "TG", "rank": "Recruit"},
            "globalData": {
                "wars": 10,
                "mobsKilled": 500000,
                "chestsFound": 2000,
                "dungeons": {"total": 150, "list": {}},
                "raids": {"total": 42, "list": {}},
                "guildRaids": None,
                "completedQuests": 200,
                "pvp": {"kills": 10, "deaths": 5},
                "totalLevel": 1200,
                "worldEvents": 30,
                "raidStats": None,
            },
        }

    def test_returns_display_and_metadata(self, sample_player_data):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_player_data

        with patch("lib.wynn_api.requests.get", return_value=mock_resp):
            result = player_stats("TestPlayer")

        assert result is not None
        display, online_status, uuid = result
        assert online_status is False
        assert uuid == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        assert "profile" in display
        assert "raids" in display

    def test_returns_none_for_missing_player(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": "Player not found"}

        with patch("lib.wynn_api.requests.get", return_value=mock_resp):
            result = player_stats("NoSuchPlayer")

        assert result is None

    def test_rank_vip_displayed(self):
        data = self._make_player_data()
        data["supportRank"] = "vip"
        mock_resp = MagicMock()
        mock_resp.json.return_value = data

        with patch("lib.wynn_api.requests.get", return_value=mock_resp):
            display, _, _ = player_stats("TestPlayer")

        assert "VIP" in display["profile"]

    def test_online_player_shows_server(self):
        data = self._make_player_data()
        data["online"] = True
        data["server"] = "WC1"
        mock_resp = MagicMock()
        mock_resp.json.return_value = data

        with patch("lib.wynn_api.requests.get", return_value=mock_resp):
            display, online_status, _ = player_stats("TestPlayer")

        assert online_status is True
        assert "WC1" in display["profile"]

    def test_pvp_kd_calculated(self):
        data = self._make_player_data()
        data["globalData"]["pvp"] = {"kills": 10, "deaths": 5}
        mock_resp = MagicMock()
        mock_resp.json.return_value = data

        with patch("lib.wynn_api.requests.get", return_value=mock_resp):
            display, _, _ = player_stats("TestPlayer")

        assert "2.0" in display["gameplay"]

    def test_guild_displayed_when_present(self):
        data = self._make_player_data()
        mock_resp = MagicMock()
        mock_resp.json.return_value = data

        with patch("lib.wynn_api.requests.get", return_value=mock_resp):
            display, _, _ = player_stats("TestPlayer")

        assert "TestGuild" in display["profile"]
        assert "[TG]" in display["profile"]

    def test_no_guild_shows_na(self):
        data = self._make_player_data()
        data["guild"] = None
        mock_resp = MagicMock()
        mock_resp.json.return_value = data

        with patch("lib.wynn_api.requests.get", return_value=mock_resp):
            display, _, _ = player_stats("TestPlayer")

        assert "N/A" in display["profile"]
