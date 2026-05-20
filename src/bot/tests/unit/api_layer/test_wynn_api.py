from unittest.mock import MagicMock, patch

import pytest

from lib.wynn_api import Guild, Items, Player


# ---------------------------------------------------------------------------
# Player._resolve_latest_player
# ---------------------------------------------------------------------------

class TestResolveLatestPlayer:
    def setup_method(self):
        self.player = Player()

    def test_passthrough_for_normal_response(self):
        data = {"uuid": "abc123", "username": "TestPlayer"}
        assert self.player._resolve_latest_player(data, use_full=False) is data

    def test_passthrough_for_non_dict(self):
        assert self.player._resolve_latest_player(None, use_full=False) is None
        assert self.player._resolve_latest_player("error", use_full=False) == "error"

    def test_passthrough_when_no_objects_key(self):
        data = {"error": "SomethingElse"}
        assert self.player._resolve_latest_player(data, use_full=False) is data

    def test_resolves_multiple_objects_to_latest(self):
        response = {
            "error": "MultipleObjectsReturned",
            "code": 300,
            "objects": {"uuid-1": {}, "uuid-2": {}},
        }
        candidate1 = {"uuid": "uuid-1", "lastJoin": "2024-01-01T00:00:00Z"}
        candidate2 = {"uuid": "uuid-2", "lastJoin": "2025-06-01T00:00:00Z"}

        def mock_get(url, **kwargs):
            m = MagicMock()
            if "uuid-1" in url:
                m.json.return_value = candidate1
            else:
                m.json.return_value = candidate2
            return m

        with patch("lib.wynn_api.requests.get", side_effect=mock_get):
            result = self.player._resolve_latest_player(response, use_full=False)
        assert result["uuid"] == "uuid-2"

    def test_falls_back_to_original_when_all_sub_fetches_fail(self):
        response = {
            "error": "MultipleObjectsReturned",
            "objects": {"uuid-x": {}},
        }
        with patch("lib.wynn_api.requests.get", side_effect=Exception("network")):
            result = self.player._resolve_latest_player(response, use_full=False)
        assert result is response


# ---------------------------------------------------------------------------
# Player API methods
# ---------------------------------------------------------------------------

class TestPlayerAPI:
    def _make_player_mock(self, data):
        m = MagicMock()
        m.json.return_value = data
        return m

    def test_get_player_main(self):
        data = {"uuid": "abc", "username": "Foo"}
        with patch("lib.wynn_api.requests.get", return_value=self._make_player_mock(data)):
            result = Player().get_player_main("Foo")
        assert result["uuid"] == "abc"

    def test_get_player_full(self):
        data = {"uuid": "abc", "username": "Foo", "characters": {}}
        with patch("lib.wynn_api.requests.get", return_value=self._make_player_mock(data)):
            result = Player().get_player_full("Foo")
        assert result["uuid"] == "abc"

    def test_player_uuid(self):
        data = {"uuid": "test-uuid"}
        with patch("lib.wynn_api.requests.get", return_value=self._make_player_mock(data)):
            assert Player().player_uuid("Foo") == "test-uuid"

    def test_online_status(self):
        data = {"uuid": "x", "online": True}
        with patch("lib.wynn_api.requests.get", return_value=self._make_player_mock(data)):
            assert Player().online_status("Foo") is True

    def test_war_global(self):
        data = {"uuid": "x", "globalData": {"wars": 42}}
        with patch("lib.wynn_api.requests.get", return_value=self._make_player_mock(data)):
            assert Player().war_global("Foo") == 42

    def test_dungeon_global(self):
        data = {"uuid": "x", "globalData": {"dungeons": {"total": 100, "list": {}}}}
        with patch("lib.wynn_api.requests.get", return_value=self._make_player_mock(data)):
            assert Player().dungeon_global("Foo") == 100

    def test_raid_global_structure(self):
        data = {
            "uuid": "x",
            "globalData": {
                "raids": {"total": 5, "list": {"TNA": 2, "TCC": 3}}
            }
        }
        with patch("lib.wynn_api.requests.get", return_value=self._make_player_mock(data)):
            result = Player().raid_global("Foo")
        assert result["total"] == 5
        assert result["TNA"] == 2


# ---------------------------------------------------------------------------
# Guild API methods
# ---------------------------------------------------------------------------

class TestGuildAPI:
    def _make_guild_mock(self, data):
        m = MagicMock()
        m.json.return_value = data
        return m

    def _make_guild_data(self):
        return {
            "name": "TestGuild",
            "prefix": "TG",
            "members": {
                "owner": {"PlayerA": {"contributed": 1000}},
                "chief": {"PlayerB": {"contributed": 500}},
                "strategist": {},
                "captain": {},
                "recruiter": {},
                "recruit": {"PlayerC": {"contributed": 100}},
            },
        }

    def test_get_prefix_guild(self):
        data = {"name": "MyGuild"}
        with patch("lib.wynn_api.requests.get", return_value=self._make_guild_mock(data)):
            assert Guild().get_prefix_guild("MG")["name"] == "MyGuild"

    def test_get_name_guild(self):
        data = {"name": "MyGuild"}
        with patch("lib.wynn_api.requests.get", return_value=self._make_guild_mock(data)):
            assert Guild().get_name_guild("MyGuild")["name"] == "MyGuild"

    def test_get_guild_members(self):
        data = self._make_guild_data()
        with patch("lib.wynn_api.requests.get", return_value=self._make_guild_mock(data)):
            members = Guild().get_guild_members("TG")
        assert "PlayerA" in members
        assert "PlayerC" in members

    def test_get_guild_member_contribution(self):
        data = self._make_guild_data()
        with patch("lib.wynn_api.requests.get", return_value=self._make_guild_mock(data)):
            contributions = Guild().get_guild_member_contribution("TG")
        assert contributions["PlayerA"] == 1000
        assert contributions["PlayerC"] == 100

    def test_get_guild_data_falls_back_to_name(self):
        data = {"name": "MyGuild"}
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("prefix not found")
            return self._make_guild_mock(data)

        with patch("lib.wynn_api.requests.get", side_effect=side_effect):
            result = Guild().get_guild_data("MyGuild")
        assert result["name"] == "MyGuild"

    def test_check_guild_found(self):
        data = {"name": "MyGuild"}
        with patch("lib.wynn_api.requests.get", return_value=self._make_guild_mock(data)):
            assert Guild().check_guild("MG") == "GUILD_FOUND"

    def test_check_guild_not_found(self):
        with patch("lib.wynn_api.requests.get", side_effect=Exception("not found")):
            assert Guild().check_guild("XX") == "NOT_FOUND"


# ---------------------------------------------------------------------------
# Items API methods
# ---------------------------------------------------------------------------

class TestItemsAPI:
    def _make_items_mock(self, data):
        m = MagicMock()
        m.json.return_value = data
        m.content = b"{}"
        return m

    def _big_item_dict(self, n=1000):
        return {f"Item{i}": {"displayName": f"Item{i}", "internalName": f"item_{i}"} for i in range(n)}

    def test_get_all_items(self):
        data = self._big_item_dict(1000)
        with patch("lib.wynn_api.requests.get", return_value=self._make_items_mock(data)):
            result = Items().get_all_items()
        assert len(result) == 1000

    def test_get_beta_items_returns_none_on_error(self):
        with patch("lib.wynn_api.requests.get", side_effect=Exception("network")):
            assert Items().get_beta_items() is None

    def test_get_beta_items_returns_none_for_invalid_response(self):
        m = MagicMock()
        m.json.return_value = 42  # not dict or list
        with patch("lib.wynn_api.requests.get", return_value=m):
            assert Items().get_beta_items() is None

    def test_get_metadata(self):
        data = {"version": "3.7"}
        with patch("lib.wynn_api.requests.get", return_value=self._make_items_mock(data)):
            result = Items().get_metadata()
        assert result["version"] == "3.7"
