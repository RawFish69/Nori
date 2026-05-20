import json
from unittest.mock import patch

import pytest

from lib.item_db_compat import items_response_to_dict, load_item_map, looks_like_item_database


def _make_item(display, internal):
    return {"displayName": display, "internalName": internal, "tier": "Unique"}


def _big_dict(n=1000):
    return {f"Item{i}": {"displayName": f"Item{i}", "internalName": f"item_{i}"} for i in range(n)}


def _big_list(n=1000):
    return [_make_item(f"Item{i}", f"item_{i}") for i in range(n)]


# ---------------------------------------------------------------------------
# looks_like_item_database
# ---------------------------------------------------------------------------

class TestLooksLikeItemDatabase:
    def test_large_dict_with_display_name(self):
        data = _big_dict(1000)
        assert looks_like_item_database(data) is True

    def test_small_dict_returns_false(self):
        data = _big_dict(3)
        assert looks_like_item_database(data) is False

    def test_large_list_with_display_name(self):
        data = _big_list(1000)
        assert looks_like_item_database(data) is True

    def test_small_list_returns_false(self):
        data = _big_list(3)
        assert looks_like_item_database(data) is False

    def test_error_payload_dict_returns_false(self):
        data = {"error": "not found", "code": 404}
        assert looks_like_item_database(data) is False

    def test_non_dict_non_list_returns_false(self):
        assert looks_like_item_database("string") is False
        assert looks_like_item_database(42) is False
        assert looks_like_item_database(None) is False

    def test_empty_list_returns_false(self):
        assert looks_like_item_database([]) is False

    def test_list_with_internal_name_only(self):
        data = [{"internalName": f"item_{i}"} for i in range(1000)]
        assert looks_like_item_database(data) is True


# ---------------------------------------------------------------------------
# items_response_to_dict
# ---------------------------------------------------------------------------

class TestItemsResponseToDict:
    def test_dict_passthrough(self):
        data = {"Sword": {"displayName": "Sword", "internalName": "sword"}}
        result, summary = items_response_to_dict(data)
        assert result is data
        assert summary is None

    def test_list_basic(self):
        items = [_make_item("Sword", "sword"), _make_item("Bow", "bow")]
        result, summary = items_response_to_dict(items)
        assert "Sword" in result
        assert "Bow" in result
        assert summary["total"] == 2
        assert summary["collisions"] == []

    def test_collision_falls_back_to_internal_name(self):
        # Two items share displayName "Fatal" but have different internalNames
        items = [
            _make_item("Fatal", "fatal"),
            _make_item("Fatal", "masterwork_fatal"),
        ]
        result, summary = items_response_to_dict(items)
        assert "Fatal" in result
        assert "masterwork_fatal" in result
        assert len(summary["collisions"]) == 1

    def test_item_missing_display_name_skipped(self, capsys):
        items = [{"internalName": "no_display", "tier": "Unique"}]
        result, summary = items_response_to_dict(items)
        assert len(result) == 0
        captured = capsys.readouterr()
        assert "displayName" in captured.out

    def test_item_missing_internal_name_skipped(self, capsys):
        items = [{"displayName": "NoInternal", "tier": "Unique"}]
        result, summary = items_response_to_dict(items)
        assert len(result) == 0
        captured = capsys.readouterr()
        assert "internalName" in captured.out

    def test_non_dict_item_in_list_skipped(self, capsys):
        items = ["bad_entry", _make_item("Sword", "sword")]
        result, summary = items_response_to_dict(items)
        assert "Sword" in result
        assert len(result) == 1

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            items_response_to_dict(42)

    def test_empty_list(self):
        result, summary = items_response_to_dict([])
        assert result == {}
        assert summary["total"] == 0

    def test_summary_total_matches_result_length(self):
        items = _big_list(50)
        result, summary = items_response_to_dict(items)
        assert summary["total"] == len(result)

    def test_ascended_mythic_collision_pattern(self):
        """Original + Ascended variant: original should be keyed by displayName."""
        items = [
            _make_item("Fatal", "Fatal"),
            _make_item("Fatal", "Masterwork Fatal"),
        ]
        result, summary = items_response_to_dict(items)
        # "Fatal" key should point to the item whose internalName == "Fatal"
        assert result["Fatal"]["internalName"] == "Fatal"
        assert "Masterwork Fatal" in result


# ---------------------------------------------------------------------------
# load_item_map
# ---------------------------------------------------------------------------

class TestLoadItemMap:
    def test_load_valid_file(self, tmp_json_file):
        data = _big_dict(1000)
        path = tmp_json_file(data, "items.json")
        result = load_item_map(path)
        assert len(result) == 1000

    def test_load_small_file_raises(self, tmp_json_file):
        data = _big_dict(3)
        path = tmp_json_file(data, "items.json")
        with pytest.raises(ValueError, match="not a valid item database"):
            load_item_map(path)

    def test_load_list_format(self, tmp_json_file):
        data = _big_list(1000)
        path = tmp_json_file(data, "items.json")
        result = load_item_map(path)
        assert isinstance(result, dict)
        assert len(result) == 1000

    def test_load_error_payload_raises(self, tmp_json_file):
        data = {"error": "not found", "code": 404}
        path = tmp_json_file(data, "items.json")
        with pytest.raises(ValueError, match="not a valid item database"):
            load_item_map(path)
