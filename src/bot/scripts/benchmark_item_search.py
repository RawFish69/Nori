"""Benchmark ItemUtils item search performance against the live item database.

Loads the local items.json and times how long it takes to do N successive
item lookups across different search methods.

Usage:
    python scripts/benchmark_item_search.py
    python scripts/benchmark_item_search.py --n 1000 --item "Gale's Force"
    python scripts/benchmark_item_search.py --all-items   # bench every item
"""

import argparse
import random
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from lib.config import BOT_PATH
from lib.item_db_compat import load_item_map, looks_like_item_database
from lib.item_utils import ItemUtils


def load_items(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"items.json not found at {path}")
    return load_item_map(str(path))


def _bench(label: str, fn, n: int):
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    elapsed = time.perf_counter() - t0
    per_call = (elapsed / n) * 1000
    print(f"  {label:<30} {n:>6} calls  {elapsed:6.3f}s  ({per_call:.4f} ms/call)")


def benchmark(item_map: dict, target: str, n: int, all_items: bool):
    utils = ItemUtils(item_map)
    items_list = list(item_map.keys())

    print(f"\n=== Item search benchmark (n={n}) ===\n")
    print(f"Item map size: {len(item_map)} items")
    print(f"Target item:   {target!r}\n")

    # item_match benchmark
    _bench("item_match (exact)", lambda: utils.item_match(target), n)
    _bench("item_match (lower)", lambda: utils.item_match(target.lower()), n)
    _bench("item_match (upper)", lambda: utils.item_match(target.upper()), n)

    # item_search benchmark
    _bench("item_search (exact)", lambda: utils.item_search(target), n)

    # Random lookup benchmark (simulates real usage)
    def _random_lookup():
        name = random.choice(items_list)
        utils.item_match(name)

    _bench("item_match (random)", _random_lookup, n)

    if all_items:
        print(f"\n  Benchmarking all {len(items_list)} items (1 pass each)...")
        t0 = time.perf_counter()
        misses = 0
        for name in items_list:
            result = utils.item_match(name)
            if result is None:
                misses += 1
        elapsed = time.perf_counter() - t0
        per_item = (elapsed / len(items_list)) * 1000
        print(f"  Full scan: {elapsed:.3f}s  ({per_item:.4f} ms/item)  misses: {misses}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark nori-bot item search")
    parser.add_argument("--n", type=int, default=500, help="Number of iterations per benchmark")
    parser.add_argument("--item", default=None, help="Item name to benchmark (default: first item in map)")
    parser.add_argument("--all-items", action="store_true", help="Also benchmark a full single-pass scan")
    parser.add_argument("--items-path", default=None, help="Path to items.json (default: bot/items.json)")
    args = parser.parse_args()

    items_path = Path(args.items_path) if args.items_path else BOT_PATH / "items.json"

    print(f"Loading items from {items_path}...")
    try:
        item_map = load_items(items_path)
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

    target = args.item or next(iter(item_map))
    if target not in item_map:
        # Try case-insensitive match
        lower_map = {k.lower(): k for k in item_map}
        real = lower_map.get(target.lower())
        if real:
            target = real
        else:
            print(f"Item {target!r} not in item map — using first item instead.")
            target = next(iter(item_map))

    benchmark(item_map, target, args.n, args.all_items)
    print("\nDone.")


if __name__ == "__main__":
    main()
