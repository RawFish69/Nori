"""Integration tests for item data fetching via the real Wynncraft API."""
import pytest

from lib.wynn_api import Items
from lib.item_db_compat import looks_like_item_database, items_response_to_dict
from lib.item_utils import ItemUtils


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def live_item_map():
    raw = Items().get_all_items()
    return raw


# ---------------------------------------------------------------------------
# Item database API shape
# ---------------------------------------------------------------------------

class TestItemApiShape:
    def test_returns_large_dict(self, live_item_map):
        assert isinstance(live_item_map, dict)
        assert len(live_item_map) >= 1000

    def test_passes_item_database_check(self, live_item_map):
        assert looks_like_item_database(live_item_map)

    def test_values_are_dicts(self, live_item_map):
        sample = next(iter(live_item_map.values()))
        assert isinstance(sample, dict)

    def test_items_have_tier(self, live_item_map):
        for item in list(live_item_map.values())[:20]:
            assert "tier" in item

    def test_known_mythic_present(self, live_item_map):
        # At least one well-known mythic should be present
        mythics = ["Nirvana", "Apocalypse", "Fatal", "Gale's Force"]
        found = [m for m in mythics if m in live_item_map]
        assert len(found) >= 1, f"None of {mythics} found in item map"

    def test_no_error_keys_in_response(self, live_item_map):
        assert "error" not in live_item_map
        assert "Error" not in live_item_map


# ---------------------------------------------------------------------------
# ItemUtils with live data
# ---------------------------------------------------------------------------

class TestItemUtilsLive:
    def test_item_match_returns_result(self, live_item_map):
        # Pick the first item name in the map
        first_name = next(iter(live_item_map))
        u = ItemUtils(live_item_map)
        result = u.item_match(first_name)
        assert result is not None
        assert "icon" in result
        assert "class" in result

    def test_item_search_returns_result(self, live_item_map):
        first_name = next(iter(live_item_map))
        u = ItemUtils(live_item_map)
        result = u.item_search(first_name)
        assert result is not None

    def test_case_insensitive_lookup_works(self, live_item_map):
        first_name = next(iter(live_item_map))
        u = ItemUtils(live_item_map)
        assert u.item_match(first_name.upper()) is not None or u.item_match(first_name.lower()) is not None


# ---------------------------------------------------------------------------
# Raw API response format
# ---------------------------------------------------------------------------

class TestRawApiFormat:
    def test_raw_list_response_converts(self):
        items_api = Items()
        raw = items_api.fetch("https://api.wynncraft.com/v3/item/database?fullResult")
        if isinstance(raw, list):
            result, summary = items_response_to_dict(raw)
            assert isinstance(result, dict)
            assert summary["total"] >= 1000
        elif isinstance(raw, dict):
            assert len(raw) >= 1000
