"""Integration tests for player data fetching via the real Wynncraft API."""
import pytest

from lib.wynn_api import Player
from lib.player_utils import player_stats


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def player_main(test_ign):
    return Player().get_player_main(test_ign)


@pytest.fixture(scope="module")
def player_full(test_ign):
    return Player().get_player_full(test_ign)


# ---------------------------------------------------------------------------
# Player API shape
# ---------------------------------------------------------------------------

class TestPlayerApiShape:
    def test_has_uuid(self, player_main):
        assert "uuid" in player_main
        assert isinstance(player_main["uuid"], str)
        assert len(player_main["uuid"]) > 0

    def test_has_username(self, player_main, test_ign):
        assert player_main.get("username", "").lower() == test_ign.lower()

    def test_has_online_field(self, player_main):
        assert "online" in player_main
        assert isinstance(player_main["online"], bool)

    def test_has_global_data(self, player_main):
        gd = player_main.get("globalData")
        assert isinstance(gd, dict)

    def test_global_data_has_raids(self, player_main):
        raids = player_main["globalData"].get("raids")
        assert isinstance(raids, dict)
        assert "total" in raids
        assert isinstance(raids["total"], int)

    def test_global_data_has_mobs_killed(self, player_main):
        assert "mobsKilled" in player_main["globalData"]

    def test_global_data_has_dungeons(self, player_main):
        dungeons = player_main["globalData"].get("dungeons")
        assert isinstance(dungeons, dict)
        assert "total" in dungeons

    def test_player_full_has_characters(self, player_full):
        assert "characters" in player_full


# ---------------------------------------------------------------------------
# player_stats helper
# ---------------------------------------------------------------------------

class TestPlayerStatsHelper:
    def test_returns_tuple(self, test_ign):
        result = player_stats(test_ign)
        assert result is not None
        assert len(result) == 3

    def test_display_has_required_keys(self, test_ign):
        display, _, _ = player_stats(test_ign)
        for key in ("profile", "progress", "gameplay", "raids", "raid_stats"):
            assert key in display, f"Missing key: {key}"

    def test_profile_contains_rank(self, test_ign):
        display, _, _ = player_stats(test_ign)
        assert "Rank" in display["profile"]

    def test_uuid_is_string(self, test_ign):
        _, _, uuid = player_stats(test_ign)
        assert isinstance(uuid, str)
        assert len(uuid) > 0

    def test_online_is_bool(self, test_ign):
        _, online, _ = player_stats(test_ign)
        assert isinstance(online, bool)

    def test_raids_block_is_code_block(self, test_ign):
        display, _, _ = player_stats(test_ign)
        assert display["raids"].startswith("```")

    def test_nonexistent_player_returns_none(self):
        result = player_stats("__this_player_does_not_exist_xyz_12345__")
        assert result is None
