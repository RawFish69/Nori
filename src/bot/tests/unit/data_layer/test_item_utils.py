import random
from unittest.mock import patch

import pytest

from lib.item_utils import ItemUtils


def _make_item(display, internal, sub_type="bow", tier="Mythic", level=100):
    return {
        "displayName": display,
        "internalName": internal,
        "tier": tier,
        "type": "weapon",
        "subType": sub_type,
        "requirements": {"level": level},
        "base": {"baseDamage": {"min": 100, "max": 200}},
        "attackSpeed": "FAST",
        "icon": {"format": "legacy", "value": "261:0"},
        "identifications": {
            "rawStrength": {"min": 5, "max": 15, "raw": 10},
        },
    }


def _big_item_map(n=1000, extra=None):
    items = {f"Item{i}": {"displayName": f"Item{i}", "internalName": f"item_{i}", "tier": "Unique"} for i in range(n)}
    if extra:
        items.update(extra)
    return items


@pytest.fixture
def gales_force_item():
    return _make_item("Gale's Force", "gales_force", sub_type="bow", tier="Mythic")


@pytest.fixture
def full_item_map(gales_force_item):
    return _big_item_map(999, extra={"Gale's Force": gales_force_item})


@pytest.fixture
def utils(full_item_map):
    return ItemUtils(full_item_map)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------

class TestItemUtilsInit:
    def test_accepts_large_dict(self, full_item_map):
        u = ItemUtils(full_item_map)
        assert len(u.item_map) == 1000

    def test_accepts_list_format(self):
        items = [{"displayName": f"Item{i}", "internalName": f"item_{i}", "tier": "Unique"} for i in range(1000)]
        u = ItemUtils(items)
        assert len(u.item_map) == 1000

    def test_rejects_small_dict_sets_empty_map(self):
        small = {"Sword": {"displayName": "Sword", "internalName": "sword"}}
        u = ItemUtils(small)
        assert u.item_map == {}

    def test_name_lookup_is_lowercase_keyed(self, full_item_map):
        u = ItemUtils(full_item_map)
        assert "gale's force" in u.name_lookup
        assert u.name_lookup["gale's force"] == "Gale's Force"


# ---------------------------------------------------------------------------
# _get_item_by_name
# ---------------------------------------------------------------------------

class TestGetItemByName:
    def test_finds_item_case_insensitive(self, utils):
        name, data = utils._get_item_by_name("gale's force")
        assert name == "Gale's Force"
        assert data is not None

    def test_returns_none_for_missing(self, utils):
        name, data = utils._get_item_by_name("nonexistent")
        assert name is None
        assert data is None


# ---------------------------------------------------------------------------
# item_match
# ---------------------------------------------------------------------------

class TestItemMatch:
    def test_returns_none_when_map_empty(self, capsys):
        u = ItemUtils({})
        assert u.item_match("Anything") is None

    def test_returns_none_for_missing_item(self, utils):
        assert utils.item_match("NotAnItem") is None

    def test_returns_icon_and_class_for_bow(self, utils):
        result = utils.item_match("Gale's Force")
        assert result is not None
        assert result["class"] == "Archer"
        assert "261_0" in result["icon"]

    def test_class_none_for_unknown_subtype(self, full_item_map):
        full_item_map["TestItem"] = {
            "displayName": "TestItem",
            "internalName": "test_item",
            "subType": "unknown_type",
            "icon": {"format": "legacy", "value": "1:0"},
        }
        u = ItemUtils(full_item_map)
        result = u.item_match("TestItem")
        assert result["class"] is None

    def test_attribute_format_icon(self, full_item_map):
        full_item_map["AttrItem"] = {
            "displayName": "AttrItem",
            "internalName": "attr_item",
            "subType": "wand",
            "icon": {"format": "attribute", "value": {"name": "minecraft:blaze_rod"}},
        }
        u = ItemUtils(full_item_map)
        result = u.item_match("AttrItem")
        assert "minecraft:blaze_rod" in result["icon"]
        assert result["class"] == "Mage"

    def test_subtype_class_mapping(self, full_item_map):
        mapping = {
            "spear": "Warrior",
            "wand": "Mage",
            "bow": "Archer",
            "dagger": "Assassin",
            "relik": "Shaman",
        }
        for sub, expected_class in mapping.items():
            full_item_map[f"Test_{sub}"] = {"displayName": f"Test_{sub}", "internalName": sub, "subType": sub}
            u = ItemUtils(full_item_map)
            result = u.item_match(f"Test_{sub}")
            assert result["class"] == expected_class


# ---------------------------------------------------------------------------
# item_search
# ---------------------------------------------------------------------------

class TestItemSearch:
    def test_returns_none_for_missing_item(self, utils):
        assert utils.item_search("NotAnItem") is None

    def test_returns_tuple_for_found_item(self, utils):
        result = utils.item_search("Gale's Force")
        assert result is not None
        display, ids, icon_id, lore, item_type = result
        assert "Gale's Force" in display["base"]
        assert "Mythic" in display["base"]
        assert icon_id == "261_0"
        assert item_type == "bow"

    def test_ids_dict_populated(self, utils):
        _, ids, _, _, _ = utils.item_search("Gale's Force")
        assert "rawStrength" in ids

    def test_lore_stripped_of_html(self, full_item_map):
        full_item_map["LoreItem"] = {
            "displayName": "LoreItem",
            "internalName": "lore_item",
            "tier": "Rare",
            "lore": "<b>Bold text</b> normal",
        }
        u = ItemUtils(full_item_map)
        _, _, _, lore, _ = u.item_search("LoreItem")
        assert "<b>" not in lore
        assert "Bold text" in lore

    def test_lore_none_when_absent(self, utils):
        _, _, _, lore, _ = utils.item_search("Gale's Force")
        assert lore is None

    def test_attack_speed_in_base_display(self, utils):
        display, _, _, _, _ = utils.item_search("Gale's Force")
        assert "FAST" in display["base"]


# ---------------------------------------------------------------------------
# _roll_star
# ---------------------------------------------------------------------------

class TestRollStar:
    def test_below_one_no_star(self):
        u = ItemUtils(_big_item_map())
        assert u._roll_star(0.9) == ""

    def test_one_star(self):
        u = ItemUtils(_big_item_map())
        assert u._roll_star(1.1) == "*"

    def test_two_stars(self):
        u = ItemUtils(_big_item_map())
        assert u._roll_star(1.27) == "**"

    def test_three_stars_exact(self):
        u = ItemUtils(_big_item_map())
        assert u._roll_star(1.3) == "***"


# ---------------------------------------------------------------------------
# _round_half_up
# ---------------------------------------------------------------------------

class TestRoundHalfUp:
    def test_positive_half_rounds_up(self):
        u = ItemUtils(_big_item_map())
        assert u._round_half_up(3.5) == 4
        assert u._round_half_up(2.5) == 3

    def test_negative_half_rounds_down(self):
        u = ItemUtils(_big_item_map())
        assert u._round_half_up(-2.5) == -3

    def test_normal_rounding(self):
        u = ItemUtils(_big_item_map())
        assert u._round_half_up(3.2) == 3
        assert u._round_half_up(3.7) == 4


# ---------------------------------------------------------------------------
# item_amp
# ---------------------------------------------------------------------------

class TestItemAmp:
    def test_returns_none_for_missing_item(self, utils):
        assert utils.item_amp("NotAnItem", 1) is None

    def test_returns_tuple_for_valid_item(self, utils):
        random.seed(42)
        result = utils.item_amp("Gale's Force", 1)
        assert result is not None
        base_display, rr_display, rolled, icon_id, item_type = result
        assert "5%" in base_display
        assert "rawStrength" in rolled
        assert icon_id == "261_0"
        assert item_type == "bow"

    def test_tier_scales_amp_percentage(self, utils):
        random.seed(0)
        result2 = utils.item_amp("Gale's Force", 2)
        assert "10%" in result2[0]
