import importlib
import json
import sys

import pytest


V3_CATACLYSM = "\U000f0002\U000f0100\U000f024d\U000f6173\U000f7465\U000f7277\U000f6f72\U000f6b20\U000f4361\U000f7461\U000f636c\U000f7973\U000f6d00\U000f0306\U000f004b\U000f0c04\U000f1a4c\U000f3404\U000f0b38\U000fcf41\U000f0523\U000f4d4e\U000f041f\U000f250a\U000f0423\U000f270a\U000f0423\U000f0403\U000f0005\U000f02ff"

V3_IDENTIFICATIONS = {
    "rawDexterity": 30,
    "stealing": {"raw": 5, "min": 2, "max": 7},
    "thorns": {"raw": 40, "min": 12, "max": 52},
    "rawHealth": {"raw": -6000, "min": -7800, "max": -4200},
    "thunderDamage": {"raw": 31, "min": 9, "max": 40},
    "raw1stSpellCost": {"raw": -4, "min": -5, "max": -3},
    "raw3rdSpellCost": {"raw": -4, "min": -5, "max": -3},
}

V3_ID_TABLE = {
    "rawDexterity": 47,
    "stealing": 75,
    "thorns": 76,
    "rawHealth": 56,
    "thunderDamage": 77,
    "raw1stSpellCost": 37,
    "raw3rdSpellCost": 39,
}


@pytest.fixture
def decoder_module(tmp_path, monkeypatch):
    itemdb_path = tmp_path / "items.json"
    id_table_path = tmp_path / "id_keys.json"
    shiny_table_path = tmp_path / "shiny_stats.json"

    item_data = {
        "Masterwork Cataclysm": {
            "internalName": "Masterwork Cataclysm",
            "displayName": "Masterwork Cataclysm",
            "tier": "Mythic",
            "identifications": V3_IDENTIFICATIONS,
        }
    }
    itemdb_path.write_text(json.dumps(item_data), encoding="utf-8")
    id_table_path.write_text(json.dumps(V3_ID_TABLE), encoding="utf-8")
    shiny_table_path.write_text("[]", encoding="utf-8")

    monkeypatch.setenv("ITEMDB_PATH", str(itemdb_path))
    monkeypatch.setenv("ID_TABLE_PATH", str(id_table_path))
    monkeypatch.setenv("SHINY_TABLE_PATH", str(shiny_table_path))

    for module_name in list(sys.modules):
        if module_name == "lib.decoders" or module_name.startswith("wynntilsresolver"):
            sys.modules.pop(module_name, None)

    module = importlib.import_module("lib.decoders")
    yield module, item_data

    for module_name in list(sys.modules):
        if module_name == "lib.decoders" or module_name.startswith("wynntilsresolver"):
            sys.modules.pop(module_name, None)


def test_decodes_wynntils_v3_values(decoder_module):
    module, item_data = decoder_module

    decoded = module.ItemDecoder().decode_item_string(V3_CATACLYSM, item_data)

    assert decoded is not None
    assert decoded.name == "Masterwork Cataclysm"
    assert decoded.item_tier == "Mythic"
    assert decoded.misc["reroll"] == 2
    assert decoded.stats == {
        "stealing": 6,
        "thorns": 26,
        "rawHealth": -4200,
        "thunderDamage": 39,
        "raw1stSpellCost": -5,
        "raw3rdSpellCost": -5,
    }

    weight_module = importlib.import_module("lib.item_weight")
    manager = weight_module.WeightManager.__new__(weight_module.WeightManager)
    weighted = manager._decode_item(V3_CATACLYSM, item_data)

    assert weighted is not None
    assert weighted["Masterwork Cataclysm"] == {
        "stealing": 6,
        "thorns": 26,
        "rawHealth": -4200,
        "thunderDamage": 39,
        "raw1stSpellCost": -5,
        "raw3rdSpellCost": -5,
    }
