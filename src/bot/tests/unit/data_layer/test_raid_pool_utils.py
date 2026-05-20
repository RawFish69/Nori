import time
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from lib.raid_pool_utils import (
    _alias_legacy_grootslang_key,
    _bucket_has_tier_data,
    _next_gambit_rotation_ts,
    _normalize_gambit_loot_shape,
    _normalize_tier_bucket,
    _parse_rotation_ts,
    convert_gambit_format,
    current_gambit_refresh_interval,
    normalize_raid_loot,
)
from lib.config import ASPECT_TIERS, GAMBIT_REFRESH_BASE_INTERVAL, GAMBIT_REFRESH_FAST_INTERVAL, RAID_NAMES


# ---------------------------------------------------------------------------
# _bucket_has_tier_data
# ---------------------------------------------------------------------------

class TestBucketHasTierData:
    def test_returns_true_for_filled_bucket(self):
        assert _bucket_has_tier_data({"Mythic": ["item1"]}) is True

    def test_returns_false_for_empty_lists(self):
        assert _bucket_has_tier_data({"Mythic": [], "Fabled": []}) is False

    def test_returns_false_for_non_dict(self):
        assert _bucket_has_tier_data(None) is False
        assert _bucket_has_tier_data([]) is False
        assert _bucket_has_tier_data("string") is False

    def test_returns_false_for_empty_dict(self):
        assert _bucket_has_tier_data({}) is False


# ---------------------------------------------------------------------------
# _alias_legacy_grootslang_key
# ---------------------------------------------------------------------------

class TestAliasLegacyGrootslangKey:
    def test_renames_notg_to_nog_when_nog_empty(self):
        result = _alias_legacy_grootslang_key({"NOTG": {"Mythic": ["item1"]}, "TNA": {}})
        assert "NOTG" not in result
        assert result["NOG"] == {"Mythic": ["item1"]}

    def test_does_not_overwrite_filled_nog(self):
        result = _alias_legacy_grootslang_key({
            "NOTG": {"Mythic": ["old"]},
            "NOG": {"Mythic": ["existing"]},
        })
        assert result["NOG"] == {"Mythic": ["existing"]}
        assert "NOTG" not in result

    def test_no_notg_key_unchanged(self):
        data = {"TNA": {"Mythic": ["x"]}}
        result = _alias_legacy_grootslang_key(data)
        assert result == data

    def test_non_dict_returns_empty(self):
        assert _alias_legacy_grootslang_key(None) == {}
        assert _alias_legacy_grootslang_key("bad") == {}


# ---------------------------------------------------------------------------
# _normalize_tier_bucket
# ---------------------------------------------------------------------------

class TestNormalizeTierBucket:
    def test_known_tiers_preserved(self):
        bucket = {"Mythic": ["a", "b"], "Fabled": ["c"]}
        result = _normalize_tier_bucket(bucket, ASPECT_TIERS)
        assert result["Mythic"] == ["a", "b"]
        assert result["Fabled"] == ["c"]
        assert result["Legendary"] == []

    def test_unknown_tiers_excluded(self):
        bucket = {"Mythic": ["a"], "Unknown": ["x"]}
        result = _normalize_tier_bucket(bucket, ASPECT_TIERS)
        assert "Unknown" not in result

    def test_non_list_value_replaced_with_empty(self):
        bucket = {"Mythic": "not_a_list"}
        result = _normalize_tier_bucket(bucket, ASPECT_TIERS)
        assert result["Mythic"] == []

    def test_none_bucket_treated_as_empty(self):
        result = _normalize_tier_bucket(None, ASPECT_TIERS)
        assert all(result[t] == [] for t in ASPECT_TIERS)


# ---------------------------------------------------------------------------
# normalize_raid_loot
# ---------------------------------------------------------------------------

class TestNormalizeRaidLoot:
    def test_all_raid_names_present(self):
        result = normalize_raid_loot({}, ASPECT_TIERS)
        for name in RAID_NAMES:
            assert name in result

    def test_notg_aliased_to_nog(self):
        source = {"NOTG": {"Mythic": ["item"]}}
        result = normalize_raid_loot(source, ASPECT_TIERS)
        assert result["NOG"]["Mythic"] == ["item"]
        assert "NOTG" not in result

    def test_extra_raid_names_preserved(self):
        source = {"EXTRA_RAID": {"Mythic": ["item"]}}
        result = normalize_raid_loot(source, ASPECT_TIERS)
        assert "EXTRA_RAID" in result


# ---------------------------------------------------------------------------
# _normalize_gambit_loot_shape
# ---------------------------------------------------------------------------

class TestNormalizeGambitLootShape:
    def test_list_passthrough(self):
        data = [{"name": "g1"}, {"name": "g2"}]
        assert _normalize_gambit_loot_shape(data) == data

    def test_dict_with_region_key_extracts_list(self):
        data = {"TNA": [{"name": "g1"}], "TCC": []}
        result = _normalize_gambit_loot_shape(data)
        assert result == [{"name": "g1"}]

    def test_empty_when_no_entries(self):
        assert _normalize_gambit_loot_shape({}) == []
        assert _normalize_gambit_loot_shape(None) == []

    def test_fallback_to_first_non_empty_list_value(self):
        data = {"unknown_region": [{"name": "g1"}]}
        result = _normalize_gambit_loot_shape(data)
        assert result == [{"name": "g1"}]


# ---------------------------------------------------------------------------
# _parse_rotation_ts
# ---------------------------------------------------------------------------

class TestParseRotationTs:
    def test_parses_iso_format(self):
        ts = _parse_rotation_ts("2026-05-01T13:00:00+00:00")
        assert isinstance(ts, int)
        assert ts > 0

    def test_parses_z_suffix(self):
        ts = _parse_rotation_ts("2026-05-01T13:00:00Z")
        assert isinstance(ts, int)

    def test_returns_none_for_invalid(self):
        assert _parse_rotation_ts("not-a-date") is None
        assert _parse_rotation_ts("") is None
        assert _parse_rotation_ts(None) is None
        assert _parse_rotation_ts(12345) is None


# ---------------------------------------------------------------------------
# convert_gambit_format
# ---------------------------------------------------------------------------

class TestConvertGambitFormat:
    def test_basic_gambits_list(self):
        payload = {
            "gambits": [
                {"name": "Gambit A", "description": "Do stuff", "confidence": 0.9},
                {"name": "Gambit B", "description": None, "confidence": None},
            ],
            "rotation_start": "2026-05-01T13:00:00Z",
            "rotation_end": "2026-05-08T13:00:00Z",
        }
        result = convert_gambit_format(payload)
        assert len(result["Loot"]) == 2
        assert result["Loot"][0]["name"] == "Gambit A"
        assert result["Loot"][0]["confidence"] == 0.9
        assert result["Loot"][1]["description"] == ""
        assert isinstance(result["RotationStart"], int)
        assert isinstance(result["RotationEnd"], int)

    def test_skips_entries_without_name(self):
        payload = {"gambits": [{"description": "no name"}, {"name": "Good"}]}
        result = convert_gambit_format(payload)
        assert len(result["Loot"]) == 1
        assert result["Loot"][0]["name"] == "Good"

    def test_handles_per_region_format(self):
        payload = {
            "TNA": {"gambits": [{"name": "RegionGambit", "description": "x", "confidence": 1.0}]}
        }
        result = convert_gambit_format(payload)
        assert any(e["name"] == "RegionGambit" for e in result["Loot"])

    def test_empty_payload(self):
        result = convert_gambit_format({})
        assert result["Loot"] == []
        assert result["RotationStart"] is None
        assert result["RotationEnd"] is None

    def test_invalid_confidence_becomes_none(self):
        payload = {"gambits": [{"name": "G", "confidence": "bad"}]}
        result = convert_gambit_format(payload)
        assert result["Loot"][0]["confidence"] is None


# ---------------------------------------------------------------------------
# _next_gambit_rotation_ts & current_gambit_refresh_interval
# ---------------------------------------------------------------------------

class TestNextGambitRotationTs:
    def test_returns_future_timestamp(self):
        now_ts = int(time.time())
        next_ts = _next_gambit_rotation_ts(now_ts)
        assert next_ts > now_ts

    def test_always_at_1pm_et(self):
        from zoneinfo import ZoneInfo
        now_ts = int(time.time())
        next_ts = _next_gambit_rotation_ts(now_ts)
        et = ZoneInfo("America/New_York")
        dt = datetime.fromtimestamp(next_ts, tz=et)
        assert dt.hour == 13
        assert dt.minute == 0


class TestCurrentGambitRefreshInterval:
    def test_returns_base_interval_far_from_reset(self):
        from zoneinfo import ZoneInfo
        et = ZoneInfo("America/New_York")
        # Use a timestamp that is exactly 2 hours before reset (well outside fast window)
        next_ts = _next_gambit_rotation_ts()
        far_before = next_ts - 7200  # 2 hours before
        interval = current_gambit_refresh_interval(far_before)
        assert interval == GAMBIT_REFRESH_BASE_INTERVAL

    def test_returns_fast_interval_just_before_reset(self):
        next_ts = _next_gambit_rotation_ts()
        just_before = next_ts - 60  # 60s before (within 300s fast window)
        interval = current_gambit_refresh_interval(just_before)
        assert interval == GAMBIT_REFRESH_FAST_INTERVAL

    def test_returns_fast_interval_just_after_reset(self):
        next_ts = _next_gambit_rotation_ts()
        just_after = next_ts - 86400 + 30  # 30s after previous rotation
        interval = current_gambit_refresh_interval(just_after)
        assert interval == GAMBIT_REFRESH_FAST_INTERVAL
