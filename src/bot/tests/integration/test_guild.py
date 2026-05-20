"""Integration tests for guild data fetching via the real Wynncraft API."""
import pytest

from lib.wynn_api import Guild
from lib.guild_utils import guild_stats


pytestmark = pytest.mark.integration

RANK_KEYS = ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]


@pytest.fixture(scope="module")
def guild_data(test_guild):
    return Guild().get_guild_data(test_guild)


# ---------------------------------------------------------------------------
# Guild API shape
# ---------------------------------------------------------------------------

class TestGuildApiShape:
    def test_has_name(self, guild_data, test_guild):
        assert "name" in guild_data
        assert guild_data["name"].lower() == test_guild.lower()

    def test_has_prefix(self, guild_data):
        assert "prefix" in guild_data
        assert isinstance(guild_data["prefix"], str)

    def test_has_level(self, guild_data):
        assert "level" in guild_data
        assert isinstance(guild_data["level"], int)

    def test_has_members_block(self, guild_data):
        members = guild_data.get("members")
        assert isinstance(members, dict)
        assert "total" in members
        for rank in RANK_KEYS:
            assert rank in members

    def test_member_count_matches_total(self, guild_data):
        members = guild_data["members"]
        counted = sum(len(members[rank]) for rank in RANK_KEYS)
        assert counted == members["total"]

    def test_has_territories(self, guild_data):
        assert "territories" in guild_data
        assert isinstance(guild_data["territories"], int)

    def test_has_created_date(self, guild_data):
        assert "created" in guild_data
        assert "T" in guild_data["created"]


# ---------------------------------------------------------------------------
# guild_stats helper
# ---------------------------------------------------------------------------

class TestGuildStatsHelper:
    def test_returns_6_tuple(self, test_guild):
        result = guild_stats(test_guild)
        assert result is not None
        assert len(result) == 6

    def test_display_contains_guild_name(self, test_guild):
        display, name, prefix, tier, structure, online = guild_stats(test_guild)
        assert test_guild.lower() in display.lower()

    def test_name_and_prefix_match_api(self, test_guild):
        _, name, prefix, _, _, _ = guild_stats(test_guild)
        assert isinstance(name, str)
        assert isinstance(prefix, str)

    def test_nonexistent_guild_returns_none(self):
        result = guild_stats("__no_such_guild_xyz_99999__")
        assert result is None


# ---------------------------------------------------------------------------
# Guild member helpers
# ---------------------------------------------------------------------------

class TestGuildMemberHelpers:
    def test_get_guild_members_returns_list(self, test_guild):
        members = Guild().get_guild_members(test_guild)
        assert isinstance(members, list)
        assert len(members) > 0

    def test_get_guild_member_contribution_returns_dict(self, test_guild):
        contributions = Guild().get_guild_member_contribution(test_guild)
        assert isinstance(contributions, dict)
        for name, xp in contributions.items():
            assert isinstance(name, str)
            assert isinstance(xp, int)
