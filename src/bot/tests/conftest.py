import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_item_map():
    """Minimal item map dict for unit tests (bypasses 1000-item validation)."""
    with open(FIXTURES / "sample_items.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_player_data():
    with open(FIXTURES / "sample_player.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_guild_data():
    with open(FIXTURES / "sample_guild.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_lootpool():
    with open(FIXTURES / "sample_lootpool.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_raid_pool():
    with open(FIXTURES / "sample_raid_pool.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_mythic_weights():
    with open(FIXTURES / "sample_mythic_weights.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def tmp_items_file(tmp_path, sample_item_map):
    """Write sample_item_map to a temp file and return the path."""
    p = tmp_path / "items.json"
    p.write_text(json.dumps(sample_item_map), encoding="utf-8")
    return p


@pytest.fixture
def tmp_json_file(tmp_path):
    """Return a factory that writes JSON to a temp file."""
    def _make(data, name="data.json"):
        p = tmp_path / name
        p.write_text(json.dumps(data), encoding="utf-8")
        return p
    return _make
