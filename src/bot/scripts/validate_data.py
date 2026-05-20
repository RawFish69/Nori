"""Validate local JSON data files used by nori-bot.

Checks that critical data files exist, are valid JSON, and have the expected
top-level structure. Exits non-zero if any check fails.

Usage:
    python scripts/validate_data.py
    python scripts/validate_data.py --strict   # fail on warnings too
"""

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from lib.config import DATA_PATH, BOT_PATH
from lib.item_db_compat import looks_like_item_database

CHECKS = [
    # (path, description, validator_fn)
    # validator_fn(data) -> (ok: bool, message: str)
]


def _check_json_dict(data):
    return isinstance(data, dict), f"Expected dict, got {type(data).__name__}"


def _check_item_db(data):
    ok = looks_like_item_database(data)
    return ok, "Valid item database" if ok else "Failed item database check (< 1000 entries or wrong shape)"


def _check_lootpool(data):
    if not isinstance(data, dict):
        return False, f"Expected dict, got {type(data).__name__}"
    has_loot = "Loot" in data or "TNA" in data or "NOG" in data
    return has_loot, "Has raid loot keys" if has_loot else "Missing expected loot keys (Loot/TNA/NOG)"


def _check_gambit_pool(data):
    if isinstance(data, dict) and "Loot" in data:
        return True, f"{len(data.get('Loot', []))} gambit entries"
    if isinstance(data, list):
        return True, f"{len(data)} gambit entries"
    return False, "Unexpected gambit pool shape"


def _check_mythic_weights(data):
    if not isinstance(data, dict):
        return False, "Expected dict"
    has_data = isinstance(data.get("Data"), dict) and len(data["Data"]) > 0
    return has_data, f"{len(data.get('Data', {}))} items in weight data" if has_data else "Missing or empty Data key"


FILE_CHECKS = [
    (BOT_PATH / "items.json",          "Item database",       _check_item_db),
    (DATA_PATH / "weekly_aspects.json", "Weekly aspects",      _check_lootpool),
    (DATA_PATH / "weekly_lootpool.json","Weekly lootpool",     _check_lootpool),
    (DATA_PATH / "weekly_raid_pool.json","Weekly raid pool",   _check_json_dict),
    (DATA_PATH / "daily_gambits.json",  "Daily gambits",       _check_gambit_pool),
    (DATA_PATH / "mythic_weights.json", "Mythic weights",      _check_mythic_weights),
]

WARN_IF_MISSING = [
    DATA_PATH / "lootpool_default.json",
    DATA_PATH / "default_aspect_pool.json",
    DATA_PATH / "default_raid_item_pool.json",
]


def validate(strict: bool = False) -> int:
    errors = 0
    warnings = 0

    print("=== nori-bot data validation ===\n")

    for path, description, validator in FILE_CHECKS:
        if not path.exists():
            print(f"[FAIL] {description}: file not found ({path})")
            errors += 1
            continue

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[FAIL] {description}: invalid JSON — {e}")
            errors += 1
            continue

        ok, message = validator(data)
        status = "OK  " if ok else "FAIL"
        marker = "" if ok else " ← CHECK"
        print(f"[{status}] {description}: {message}{marker}")
        if not ok:
            errors += 1

    print()
    for path in WARN_IF_MISSING:
        if not path.exists():
            print(f"[WARN] Optional file missing: {path}")
            warnings += 1

    print(f"\n{'='*36}")
    print(f"Errors: {errors}  Warnings: {warnings}")

    if errors:
        print("FAIL — fix errors above before running the bot.")
        return 1
    if strict and warnings:
        print("FAIL (strict) — warnings treated as errors.")
        return 1
    print("PASS")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Validate nori-bot data files")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()
    sys.exit(validate(strict=args.strict))


if __name__ == "__main__":
    main()
