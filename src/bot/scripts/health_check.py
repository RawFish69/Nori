"""Bot health check — verifies critical subsystems can initialise.

Checks:
  1. Config loads without error
  2. Item database file exists and is a valid item map
  3. Mythic weights file loads
  4. Lootpool/aspect data files are readable
  5. Wynn API is reachable (basic HTTP check)

Usage:
    python scripts/health_check.py
    python scripts/health_check.py --no-api   # skip live API check
"""

import argparse
import json
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))


def _check(label: str, fn, *args, **kwargs):
    try:
        result = fn(*args, **kwargs)
        print(f"[OK] {label}")
        return True, result
    except Exception as exc:
        print(f"[FAIL] {label}: {exc}")
        return False, None


def check_config():
    import lib.config as config
    assert hasattr(config, "DATA_PATH"), "DATA_PATH missing"
    assert hasattr(config, "BOT_PATH"), "BOT_PATH missing"
    return config


def check_item_db():
    from lib.config import BOT_PATH
    from lib.item_db_compat import load_item_map, looks_like_item_database
    items_path = BOT_PATH / "items.json"
    if not items_path.exists():
        raise FileNotFoundError(f"items.json not found at {items_path}")
    item_map = load_item_map(str(items_path))
    if not looks_like_item_database(item_map):
        raise ValueError("item_map failed looks_like_item_database check")
    return len(item_map)


def check_mythic_weights():
    from lib.config import DATA_PATH
    path = DATA_PATH / "mythic_weights.json"
    if not path.exists():
        raise FileNotFoundError(f"mythic_weights.json not found at {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    n = len(data.get("Data", {}))
    if n == 0:
        raise ValueError("No items in mythic_weights Data")
    return n


def check_lootpool_files():
    from lib.config import DATA_PATH
    found = []
    for name in ("weekly_aspects.json", "weekly_lootpool.json", "weekly_raid_pool.json"):
        p = DATA_PATH / name
        if p.exists():
            with open(p, encoding="utf-8") as f:
                json.load(f)
            found.append(name)
    if not found:
        raise FileNotFoundError("No lootpool files found in DATA_PATH")
    return found


def check_api(timeout: int = 10):
    import requests
    url = "https://api.wynncraft.com/v3/item/metadata"
    t0 = time.monotonic()
    resp = requests.get(url, timeout=timeout)
    elapsed = time.monotonic() - t0
    resp.raise_for_status()
    return f"HTTP {resp.status_code} in {elapsed:.2f}s"


def main():
    parser = argparse.ArgumentParser(description="nori-bot health check")
    parser.add_argument("--no-api", action="store_true", help="Skip live Wynn API check")
    args = parser.parse_args()

    print("=== nori-bot health check ===\n")
    failures = 0

    ok, _ = _check("Config loads", check_config)
    failures += not ok

    ok, count = _check("Item database", check_item_db)
    if ok:
        print(f"    -> {count} items loaded")
    failures += not ok

    ok, count = _check("Mythic weights", check_mythic_weights)
    if ok:
        print(f"    -> {count} mythics with weight data")
    failures += not ok

    ok, files = _check("Lootpool files", check_lootpool_files)
    if ok:
        print(f"    -> {files}")
    failures += not ok

    if not args.no_api:
        ok, status = _check("Wynn API reachable", check_api)
        if ok:
            print(f"    -> {status}")
        failures += not ok
    else:
        print("[SKIP] Wynn API check (--no-api)")

    print(f"\n{'='*32}")
    if failures:
        print(f"FAIL — {failures} check(s) failed.")
        sys.exit(1)
    print("PASS -- all checks OK.")


if __name__ == "__main__":
    main()
