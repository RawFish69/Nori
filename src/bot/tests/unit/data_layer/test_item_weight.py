import json
from pathlib import Path
from unittest.mock import patch

import pytest

from lib.item_weight import WeightManager, WeightResult, mythic_weigh, weigh_scale


SAMPLE_WEIGHT_DATA = {
    "latest": {"Timestamp": "2024-01-01"},
    "Data": {
        "Gale's Force": {
            "Main": {"airDamage": "50", "rawStrength": "30", "walkSpeed": "20"},
            "Alt": {"airDamage": "40", "rawStrength": "40", "walkSpeed": "20"},
        }
    },
    "ranked": {
        "Gale's Force": {
            "Main": {"owner": "PlayerOne"},
            "Alt": {"owner": ["PlayerA", "PlayerB"]},
        }
    },
}


@pytest.fixture
def weight_file(tmp_path):
    path = tmp_path / "mythic_weights.json"
    path.write_text(json.dumps(SAMPLE_WEIGHT_DATA), encoding="utf-8")
    return path


@pytest.fixture
def mgr(weight_file):
    return WeightManager(str(weight_file))


# ---------------------------------------------------------------------------
# WeightManager.__init__ / _load_weight_data
# ---------------------------------------------------------------------------

class TestWeightManagerInit:
    def test_loads_data_from_file(self, mgr):
        assert "Gale's Force" in mgr.weight_data.get("Data", {})

    def test_returns_empty_dict_for_missing_file(self, tmp_path, capsys):
        m = WeightManager(str(tmp_path / "nonexistent.json"))
        assert m.weight_data == {}
        assert "Error" in capsys.readouterr().out

    def test_returns_empty_dict_for_invalid_json(self, tmp_path, capsys):
        bad = tmp_path / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        m = WeightManager(str(bad))
        assert m.weight_data == {}


# ---------------------------------------------------------------------------
# WeightManager.calculate_mythic_weight
# ---------------------------------------------------------------------------

class TestCalculateMythicWeight:
    def test_returns_weight_result(self, mgr):
        result = mgr.calculate_mythic_weight("Gale's Force", [80.0, 70.0, 60.0])
        assert isinstance(result, WeightResult)
        assert result.item_name == "Gale's Force"
        assert "Main" in result.scale_weights
        assert "Alt" in result.scale_weights
        assert result.timestamp == "2024-01-01"

    def test_case_insensitive_lookup(self, mgr):
        result = mgr.calculate_mythic_weight("gale's force", [80.0, 70.0, 60.0])
        assert result is not None
        assert result.item_name == "Gale's Force"

    def test_returns_none_for_unknown_item(self, mgr):
        assert mgr.calculate_mythic_weight("Unknown Item", [1.0]) is None

    def test_main_products_length_matches_inputs(self, mgr):
        inputs = [90.0, 80.0, 70.0]
        result = mgr.calculate_mythic_weight("Gale's Force", inputs)
        assert len(result.main_products) == len(inputs)

    def test_scale_weights_are_rounded(self, mgr):
        result = mgr.calculate_mythic_weight("Gale's Force", [100.0, 100.0, 100.0])
        # Main: (100*0.5) + (100*0.3) + (100*0.2) = 100.0
        assert result.scale_weights["Main"] == 100.0

    def test_scale_data_is_main_stats(self, mgr):
        result = mgr.calculate_mythic_weight("Gale's Force", [80.0, 70.0, 60.0])
        assert result.scale_data == {"airDamage": "50", "rawStrength": "30", "walkSpeed": "20"}


# ---------------------------------------------------------------------------
# WeightManager.get_scale_info
# ---------------------------------------------------------------------------

class TestGetScaleInfo:
    def test_returns_tuple_for_known_item(self, mgr):
        result = mgr.get_scale_info("Gale's Force")
        assert result is not None
        scale_display, timestamp, scale_data, item_name = result
        assert item_name == "Gale's Force"
        assert timestamp == "2024-01-01"
        assert "Main" in scale_display[item_name]
        assert "Alt" in scale_display[item_name]

    def test_returns_none_for_unknown_item(self, mgr):
        assert mgr.get_scale_info("Unknown") is None

    def test_scale_display_contains_stat_names(self, mgr):
        scale_display, _, _, item_name = mgr.get_scale_info("Gale's Force")
        assert "airDamage" in scale_display[item_name]["Main"]

    def test_case_insensitive(self, mgr):
        result = mgr.get_scale_info("GALE'S FORCE")
        assert result is not None


# ---------------------------------------------------------------------------
# mythic_weigh (module-level function)
# ---------------------------------------------------------------------------

class TestMythicWeigh:
    def test_returns_result_and_main_products(self, weight_file):
        result, products = mythic_weigh("Gale's Force", [80.0, 70.0, 60.0], str(weight_file))
        assert "Gale's Force" in result
        assert "Main" in result["Gale's Force"]
        assert isinstance(products, list)

    def test_case_insensitive(self, weight_file):
        result, _ = mythic_weigh("gale's force", [80.0, 70.0, 60.0], str(weight_file))
        assert result is not None

    def test_returns_none_for_unknown(self, weight_file):
        assert mythic_weigh("Unknown", [1.0, 2.0], str(weight_file)) is None

    def test_main_scale_calculation(self, weight_file):
        # Main: airDamage=50%, rawStrength=30%, walkSpeed=20%
        # Inputs: 100, 100, 100 → weighted = 100
        result, _ = mythic_weigh("Gale's Force", [100.0, 100.0, 100.0], str(weight_file))
        assert result["Gale's Force"]["Main"] == 100.0


# ---------------------------------------------------------------------------
# weigh_scale (module-level function)
# ---------------------------------------------------------------------------

class TestWeighScale:
    def test_returns_scale_display_and_metadata(self, weight_file):
        result = weigh_scale("Gale's Force", str(weight_file))
        assert result is not None
        scale_display, timestamp, scale_data, item_name = result
        assert item_name == "Gale's Force"
        assert timestamp == "2024-01-01"
        assert "Main" in scale_display[item_name]

    def test_returns_none_for_unknown(self, weight_file):
        assert weigh_scale("Unknown", str(weight_file)) is None

    def test_owner_display_single(self, weight_file):
        _, _, _, item_name = weigh_scale("Gale's Force", str(weight_file))
        scale_display, _, _, _ = weigh_scale("Gale's Force", str(weight_file))
        assert "PlayerOne" in scale_display[item_name]["Main"]

    def test_owner_display_list(self, weight_file):
        scale_display, _, _, item_name = weigh_scale("Gale's Force", str(weight_file))
        assert "PlayerA" in scale_display[item_name]["Alt"]
        assert "PlayerB" in scale_display[item_name]["Alt"]

    def test_case_insensitive(self, weight_file):
        assert weigh_scale("gale's force", str(weight_file)) is not None
