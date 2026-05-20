import json
from unittest.mock import MagicMock, patch

import pytest

from lib.item_manager import ItemManager


def _big_dict(n=1000):
    return {f"Item{i}": {"displayName": f"Item{i}", "internalName": f"item_{i}", "tier": "Unique"} for i in range(n)}


def _big_list(n=1000):
    return [{"displayName": f"Item{i}", "internalName": f"item_{i}", "tier": "Unique"} for i in range(n)]


# ---------------------------------------------------------------------------
# get_item_name
# ---------------------------------------------------------------------------

class TestGetItemName:
    def test_returns_none_when_map_empty(self, capsys):
        mgr = ItemManager()
        assert mgr.get_item_name("Sword") is None
        assert "empty" in capsys.readouterr().out

    def test_finds_exact_match(self):
        mgr = ItemManager()
        mgr.item_map = {"Gale's Force": {}, "Weathered": {}}
        assert mgr.get_item_name("Gale's Force") == "Gale's Force"

    def test_case_insensitive_lookup(self):
        mgr = ItemManager()
        mgr.item_map = {"Nirvana": {}}
        assert mgr.get_item_name("nirvana") == "Nirvana"
        assert mgr.get_item_name("NIRVANA") == "Nirvana"

    def test_returns_none_when_not_found(self):
        mgr = ItemManager()
        mgr.item_map = {"Nirvana": {}}
        assert mgr.get_item_name("NotAnItem") is None


# ---------------------------------------------------------------------------
# load_items_from_file
# ---------------------------------------------------------------------------

class TestLoadItemsFromFile:
    def test_loads_dict_format(self, tmp_json_file):
        data = _big_dict(5)
        path = tmp_json_file(data, "items.json")
        mgr = ItemManager()
        mgr.load_items_from_file(str(path))
        assert len(mgr.item_map) == 5
        assert str(path) == mgr.items_path

    def test_loads_list_format(self, tmp_json_file):
        data = _big_list(5)
        path = tmp_json_file(data, "items.json")
        mgr = ItemManager()
        mgr.load_items_from_file(str(path))
        assert len(mgr.item_map) == 5

    def test_handles_missing_file_gracefully(self, tmp_path, capsys):
        mgr = ItemManager()
        mgr.load_items_from_file(str(tmp_path / "nonexistent.json"))
        assert mgr.item_map == {}
        assert "Error" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _save_item_data
# ---------------------------------------------------------------------------

class TestSaveItemData:
    def test_saves_valid_data_and_updates_map(self, tmp_path):
        data = _big_dict(1000)
        path = tmp_path / "items.json"
        mgr = ItemManager()
        count = mgr._save_item_data(data, str(path))
        assert count == 1000
        assert len(mgr.item_map) == 1000
        assert path.exists()

    def test_refuses_invalid_data(self, tmp_path, capsys):
        data = {"error": "bad"}
        path = tmp_path / "items.json"
        mgr = ItemManager()
        count = mgr._save_item_data(data, str(path))
        assert count == 0
        assert not path.exists()

    def test_returns_zero_on_write_error(self, capsys):
        data = _big_dict(1000)
        mgr = ItemManager()
        # Pass an invalid path to trigger a write error
        count = mgr._save_item_data(data, "/nonexistent_dir/items.json")
        assert count == 0
        assert "error" in capsys.readouterr().out.lower()

    def test_saves_correct_json_to_disk(self, tmp_path):
        data = _big_dict(1000)
        path = tmp_path / "items.json"
        mgr = ItemManager()
        mgr._save_item_data(data, str(path))
        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data


# ---------------------------------------------------------------------------
# update_items
# ---------------------------------------------------------------------------

class TestUpdateItems:
    def test_updates_from_main_api(self, tmp_path):
        data = _big_dict(1000)
        path = tmp_path / "items.json"
        mock_items = MagicMock()
        mock_items.get_all_items_raw.return_value = data

        with patch("lib.item_manager.Items", return_value=mock_items):
            mgr = ItemManager()
            count = mgr.update_items(str(path))

        assert count == 1000
        assert path.exists()

    def test_falls_back_to_beta_when_main_invalid(self, tmp_path, capsys):
        beta_data = _big_dict(1000)
        path = tmp_path / "items.json"
        mock_main = MagicMock()
        mock_main.get_all_items_raw.return_value = {"error": "fail"}
        mock_beta = MagicMock()
        mock_beta.get_beta_items_raw.return_value = beta_data

        call_count = [0]

        def items_factory():
            call_count[0] += 1
            return mock_main if call_count[0] == 1 else mock_beta

        with patch("lib.item_manager.Items", side_effect=items_factory):
            mgr = ItemManager()
            count = mgr.update_items(str(path))

        assert count == 1000
        out = capsys.readouterr().out
        assert "beta" in out.lower() or "Beta" in out

    def test_returns_zero_when_both_apis_invalid(self, tmp_path, capsys):
        bad = {"error": "fail"}
        path = tmp_path / "items.json"
        mock_items = MagicMock()
        mock_items.get_all_items_raw.return_value = bad
        mock_items.get_beta_items_raw.return_value = bad

        with patch("lib.item_manager.Items", return_value=mock_items):
            mgr = ItemManager()
            count = mgr.update_items(str(path))

        assert count == 0
        assert not path.exists()

    def test_list_format_response_converted(self, tmp_path):
        data = _big_list(1000)
        path = tmp_path / "items.json"
        mock_items = MagicMock()
        mock_items.get_all_items_raw.return_value = data

        with patch("lib.item_manager.Items", return_value=mock_items):
            mgr = ItemManager()
            count = mgr.update_items(str(path))

        assert count == 1000
