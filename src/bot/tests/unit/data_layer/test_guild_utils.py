from unittest.mock import MagicMock, patch

import pytest

from lib.guild_utils import guild_stats, xp_list


def _make_get_mock(data):
    m = MagicMock()
    m.json.return_value = data
    return m


# ---------------------------------------------------------------------------
# guild_stats
# ---------------------------------------------------------------------------

class TestGuildStats:
    def test_returns_tuple_for_valid_guild(self, sample_guild_data):
        with patch("lib.wynn_api.requests.get", return_value=_make_get_mock(sample_guild_data)):
            result = guild_stats("TG")
        assert result is not None
        display, name, prefix, banner_tier, banner_structure, online_display = result
        assert name == "TestGuild"
        assert prefix == "TG"
        assert banner_tier == 3
        assert banner_structure == "CROSS"

    def test_display_contains_guild_info(self, sample_guild_data):
        with patch("lib.wynn_api.requests.get", return_value=_make_get_mock(sample_guild_data)):
            result = guild_stats("TG")
        display = result[0]
        assert "TestGuild" in display
        assert "OwnerPlayer" in display
        assert "Level: 25" in display
        assert "War count: 100" in display
        assert "Territory count: 3" in display

    def test_online_players_shown(self, sample_guild_data):
        with patch("lib.wynn_api.requests.get", return_value=_make_get_mock(sample_guild_data)):
            result = guild_stats("TG")
        online_display = result[5]
        # RecruitA is online with server WC1
        assert "WC1" in online_display
        assert "RecruitA" in online_display

    def test_no_online_players_shows_placeholder(self, sample_guild_data):
        # Set all members offline
        for rank in ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]:
            for player in sample_guild_data["members"][rank].values():
                player["online"] = False
        with patch("lib.wynn_api.requests.get", return_value=_make_get_mock(sample_guild_data)):
            result = guild_stats("TG")
        assert "No online members." in result[5]

    def test_returns_none_when_guild_not_found(self):
        with patch("lib.wynn_api.requests.get", side_effect=Exception("not found")):
            result = guild_stats("NOTEXIST")
        assert result is None

    def test_returns_none_when_guild_data_is_none(self):
        with patch("lib.guild_utils.Guild") as MockGuild:
            MockGuild.return_value.get_guild_data.return_value = None
            result = guild_stats("TG")
        assert result is None

    def test_no_banner_returns_default_tier(self, sample_guild_data):
        sample_guild_data["banner"] = None
        with patch("lib.wynn_api.requests.get", return_value=_make_get_mock(sample_guild_data)):
            result = guild_stats("TG")
        assert result[3] == "0 tier"
        assert result[4] == "No structure"

    def test_banner_without_structure_returns_no_structure(self, sample_guild_data):
        sample_guild_data["banner"] = {"tier": 5}
        with patch("lib.wynn_api.requests.get", return_value=_make_get_mock(sample_guild_data)):
            result = guild_stats("TG")
        assert result[3] == 5
        assert result[4] == "No structure"

    def test_wars_none_shown_as_zero(self, sample_guild_data):
        sample_guild_data["wars"] = None
        with patch("lib.wynn_api.requests.get", return_value=_make_get_mock(sample_guild_data)):
            result = guild_stats("TG")
        assert "War count: 0" in result[0]


# ---------------------------------------------------------------------------
# xp_list
# ---------------------------------------------------------------------------

class TestXpList:
    def _contributions(self):
        return {
            "OwnerPlayer": 1000000,
            "RecruitA": 50000,
            "RecruitB": 30000,
        }

    def test_returns_formatted_string(self, sample_guild_data):
        with patch("lib.guild_utils.Guild") as MockGuild:
            MockGuild.return_value.get_guild_member_contribution.return_value = self._contributions()
            result = xp_list("TG")
        assert isinstance(result, str)
        assert "```" in result

    def test_members_sorted_by_contribution_descending(self, sample_guild_data):
        with patch("lib.guild_utils.Guild") as MockGuild:
            MockGuild.return_value.get_guild_member_contribution.return_value = self._contributions()
            result = xp_list("TG")
        # OwnerPlayer has most XP, should appear before others
        owner_pos = result.find("OwnerPlayer")
        recruit_pos = result.find("RecruitA")
        assert owner_pos < recruit_pos

    def test_contains_member_names(self):
        with patch("lib.guild_utils.Guild") as MockGuild:
            MockGuild.return_value.get_guild_member_contribution.return_value = self._contributions()
            result = xp_list("TG")
        assert "OwnerPlayer" in result
        assert "RecruitA" in result

    def test_shows_at_most_15_members(self):
        many = {f"Player{i:02d}": i * 1000 for i in range(20)}
        with patch("lib.guild_utils.Guild") as MockGuild:
            MockGuild.return_value.get_guild_member_contribution.return_value = many
            result = xp_list("TG")
        # Players 05-19 fill top 15; Player00 (lowest XP) should not appear
        assert "Player00" not in result
