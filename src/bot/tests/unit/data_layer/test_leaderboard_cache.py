import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from lib.leaderboard_cache import (
    _read_json_file,
    _read_json_url,
    load_leaderboard_in_guild,
)


# ---------------------------------------------------------------------------
# _read_json_file
# ---------------------------------------------------------------------------

class TestReadJsonFile:
    def test_reads_valid_file(self, tmp_path):
        data = {"key": "value"}
        p = tmp_path / "data.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        assert _read_json_file(str(p), {}) == data

    def test_returns_default_for_missing_file(self, tmp_path):
        assert _read_json_file(str(tmp_path / "missing.json"), {"default": 1}) == {"default": 1}

    def test_returns_list_default(self, tmp_path):
        assert _read_json_file(str(tmp_path / "gone.json"), []) == []

    def test_reads_nested_data(self, tmp_path):
        data = {"players": [{"name": "A", "score": 100}]}
        p = tmp_path / "lb.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        result = _read_json_file(str(p), {})
        assert result["players"][0]["name"] == "A"


# ---------------------------------------------------------------------------
# _read_json_url
# ---------------------------------------------------------------------------

class TestReadJsonUrl:
    def test_returns_default_for_empty_url(self):
        assert _read_json_url("", {"default": True}) == {"default": True}
        assert _read_json_url(None, []) == []

    def test_returns_parsed_json_on_success(self):
        data = {"leaderboard": [{"rank": 1, "player": "Alpha"}]}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(data).encode("utf-8")
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("lib.leaderboard_cache.urlopen", return_value=mock_response):
            result = _read_json_url("https://example.com/lb.json", {})
        assert result == data

    def test_returns_default_on_network_error(self, capsys):
        with patch("lib.leaderboard_cache.urlopen", side_effect=Exception("timeout")):
            result = _read_json_url("https://example.com/lb.json", {"fallback": True})
        assert result == {"fallback": True}
        assert "Error" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# load_leaderboard_in_guild
# ---------------------------------------------------------------------------

class TestLoadLeaderboardInGuild:
    def test_returns_api_data_when_available(self):
        api_data = {"PlayerA": {"score": 1000}}
        with patch("lib.leaderboard_cache._read_json_url", return_value=api_data):
            result = load_leaderboard_in_guild()
        assert result == api_data

    def test_falls_back_to_file_when_api_empty(self, tmp_json_file):
        file_data = {"PlayerB": {"score": 500}}
        path = tmp_json_file(file_data, "lb.json")
        with (
            patch("lib.leaderboard_cache._read_json_url", return_value=None),
            patch("lib.leaderboard_cache.LEADERBOARD_IN_GUILD_FILE", str(path)),
        ):
            result = load_leaderboard_in_guild()
        assert result == file_data

    def test_returns_empty_dict_when_both_unavailable(self, tmp_path, capsys):
        with (
            patch("lib.leaderboard_cache._read_json_url", return_value=None),
            patch("lib.leaderboard_cache.LEADERBOARD_IN_GUILD_FILE", str(tmp_path / "gone.json")),
        ):
            result = load_leaderboard_in_guild()
        assert result == {}
        assert "unavailable" in capsys.readouterr().out.lower()

    def test_ignores_non_dict_api_response(self, tmp_json_file):
        file_data = {"PlayerC": {"score": 200}}
        path = tmp_json_file(file_data, "lb.json")
        with (
            patch("lib.leaderboard_cache._read_json_url", return_value=[1, 2, 3]),
            patch("lib.leaderboard_cache.LEADERBOARD_IN_GUILD_FILE", str(path)),
        ):
            result = load_leaderboard_in_guild()
        assert result == file_data

    def test_ignores_empty_dict_api_response(self, tmp_json_file):
        file_data = {"PlayerD": {"score": 300}}
        path = tmp_json_file(file_data, "lb.json")
        with (
            patch("lib.leaderboard_cache._read_json_url", return_value={}),
            patch("lib.leaderboard_cache.LEADERBOARD_IN_GUILD_FILE", str(path)),
        ):
            result = load_leaderboard_in_guild()
        assert result == file_data
