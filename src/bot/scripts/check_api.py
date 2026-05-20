"""Check Wynncraft API availability and response shapes.

Hits each API endpoint used by nori-bot and reports status, latency, and
whether the response shape looks correct.

Usage:
    python scripts/check_api.py
    python scripts/check_api.py --endpoint player --ign Salted
    python scripts/check_api.py --endpoint items
    python scripts/check_api.py --endpoint guild --guild Wynncraft
    python scripts/check_api.py --all
"""

import argparse
import json
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

import requests
from lib.config import WYNN_AUTH_HEADER
from lib.item_db_compat import looks_like_item_database

TIMEOUT = 20
BASE_URL = "https://api.wynncraft.com/v3"


def _get(path: str, use_auth: bool = True, base: str = BASE_URL):
    headers = dict(WYNN_AUTH_HEADER) if use_auth else {"User-Agent": "nori-bot-check/1.0"}
    t0 = time.monotonic()
    resp = requests.get(f"{base}{path}", headers=headers, timeout=TIMEOUT)
    elapsed = time.monotonic() - t0
    resp.raise_for_status()
    data = resp.json()
    return data, elapsed


def check_player(ign: str) -> bool:
    print(f"\n[Player] Checking IGN: {ign}")
    try:
        data, t = _get(f"/player/{ign}")
        print(f"  Status: OK ({t:.2f}s)")
        if "uuid" in data:
            print(f"  UUID: {data['uuid']}")
            print(f"  Username: {data.get('username')}")
            print(f"  Online: {data.get('online')}")
            print(f"  GlobalData keys: {list(data.get('globalData', {}).keys())[:5]}")
            return True
        elif "error" in data:
            print(f"  API error: {data['error']}")
            return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def check_items() -> bool:
    print("\n[Items] Checking item database endpoint")
    try:
        data, t = _get("/item/database?fullResult")
        print(f"  Status: OK ({t:.2f}s)")
        valid = looks_like_item_database(data)
        if isinstance(data, list):
            print(f"  Format: list ({len(data)} entries)")
        elif isinstance(data, dict):
            print(f"  Format: dict ({len(data)} keys)")
        print(f"  Passes item DB check: {valid}")
        return valid
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def check_guild(guild: str) -> bool:
    print(f"\n[Guild] Checking guild: {guild}")
    try:
        data, t = _get(f"/guild/{guild}")
        print(f"  Status: OK ({t:.2f}s)")
        if "name" in data:
            print(f"  Name: {data['name']} [{data.get('prefix')}]")
            print(f"  Level: {data.get('level')}  Members: {data.get('members', {}).get('total')}")
            return True
        print(f"  Unexpected shape: {list(data.keys())[:5]}")
        return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def check_metadata() -> bool:
    print("\n[Metadata] Checking item metadata endpoint")
    try:
        data, t = _get("/item/metadata")
        print(f"  Status: OK ({t:.2f}s)")
        print(f"  Keys: {list(data.keys())[:6]}")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Check Wynncraft API availability")
    parser.add_argument("--endpoint", choices=["player", "items", "guild", "metadata", "all"], default="all")
    parser.add_argument("--ign", default="Salted", help="Player IGN for player check")
    parser.add_argument("--guild", default="Wynncraft", help="Guild name for guild check")
    parser.add_argument("--all", dest="all_endpoints", action="store_true")
    args = parser.parse_args()

    run_all = args.endpoint == "all" or args.all_endpoints
    results = []

    print("=== Wynncraft API check ===")

    if run_all or args.endpoint == "metadata":
        results.append(check_metadata())
    if run_all or args.endpoint == "items":
        results.append(check_items())
    if run_all or args.endpoint == "player":
        results.append(check_player(args.ign))
    if run_all or args.endpoint == "guild":
        results.append(check_guild(args.guild))

    print(f"\n{'='*28}")
    failed = results.count(False)
    if failed:
        print(f"FAIL — {failed}/{len(results)} check(s) failed.")
        sys.exit(1)
    print(f"PASS — {len(results)}/{len(results)} checks OK.")


if __name__ == "__main__":
    main()
