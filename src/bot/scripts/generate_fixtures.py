"""Generate test fixture JSON files from the live Wynncraft API.

Fetches minimal representative data and writes it to tests/fixtures/ so the
unit test suite has realistic but small sample data to work with.

Usage:
    python scripts/generate_fixtures.py
    python scripts/generate_fixtures.py --ign Salted --guild Wynncraft
    python scripts/generate_fixtures.py --dry-run   # print output, don't write
"""

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

FIXTURES_DIR = BASE_DIR / "tests" / "fixtures"

import requests
from lib.config import WYNN_AUTH_HEADER

TIMEOUT = 20
BASE_URL = "https://api.wynncraft.com/v3"


def _get(path: str, auth: bool = True):
    headers = dict(WYNN_AUTH_HEADER) if auth else {}
    resp = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def fetch_sample_player(ign: str) -> dict:
    data = _get(f"/player/{ign}")
    if "uuid" not in data:
        raise ValueError(f"Player '{ign}' not found: {data}")
    gd = data.get("globalData", {})
    return {
        "username": data["username"],
        "online": data.get("online", False),
        "server": data.get("server"),
        "uuid": data["uuid"],
        "rank": data.get("rank", "Player"),
        "rankBadge": data.get("rankBadge"),
        "legacyRankColour": data.get("legacyRankColour"),
        "shortenedRank": data.get("shortenedRank"),
        "supportRank": data.get("supportRank"),
        "firstJoin": data.get("firstJoin"),
        "lastJoin": data.get("lastJoin"),
        "playtime": data.get("playtime", 0),
        "guild": data.get("guild"),
        "globalData": {
            "wars": gd.get("wars", 0),
            "mobsKilled": gd.get("mobsKilled", 0),
            "chestsFound": gd.get("chestsFound", 0),
            "dungeons": gd.get("dungeons", {"total": 0, "list": {}}),
            "raids": gd.get("raids", {"total": 0, "list": {}}),
            "completedQuests": gd.get("completedQuests", 0),
            "pvp": gd.get("pvp", {"kills": 0, "deaths": 0}),
        },
        "characters": {},
    }


def fetch_sample_guild(guild: str) -> dict:
    data = _get(f"/guild/{guild}")
    if "name" not in data:
        raise ValueError(f"Guild '{guild}' not found: {data}")
    members = data.get("members", {})
    # Keep only a couple of members per rank to keep the fixture small
    trimmed_members = {"total": members.get("total", 0)}
    for rank in ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]:
        rank_data = members.get(rank, {})
        kept = dict(list(rank_data.items())[:2])
        trimmed_members[rank] = kept
    return {
        "name": data["name"],
        "prefix": data["prefix"],
        "level": data.get("level", 0),
        "xpPercent": data.get("xpPercent", 0),
        "territories": data.get("territories", 0),
        "wars": data.get("wars", 0),
        "created": data.get("created", ""),
        "banner": data.get("banner"),
        "members": trimmed_members,
        "seasonRanks": {},
    }


def fetch_sample_items() -> dict:
    raw = _get("/item/database?fullResult", auth=True)
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = list(raw.values())
    else:
        raise ValueError(f"Unexpected item database shape: {type(raw)}")
    # Pick 3 diverse items: one mythic, one legendary, one unique
    sample = {}
    targets = {"Mythic": None, "Legendary": None, "Unique": None}
    for item in items:
        if not isinstance(item, dict):
            continue
        tier = item.get("tier")
        if tier in targets and targets[tier] is None:
            targets[tier] = item
        if all(v is not None for v in targets.values()):
            break
    for tier, item in targets.items():
        if item:
            key = item.get("displayName", f"Sample{tier}")
            sample[key] = item
    return sample


def _write(path: Path, data: dict, dry_run: bool):
    text = json.dumps(data, indent=4, ensure_ascii=False)
    if dry_run:
        print(f"\n--- {path.name} ---")
        print(text[:500] + ("..." if len(text) > 500 else ""))
    else:
        path.write_text(text, encoding="utf-8")
        print(f"  Wrote {path} ({len(data)} top-level keys)")


def main():
    parser = argparse.ArgumentParser(description="Generate test fixture files from live Wynncraft API")
    parser.add_argument("--ign", default="Salted")
    parser.add_argument("--guild", default="Wynncraft")
    parser.add_argument("--dry-run", action="store_true", help="Print output without writing files")
    args = parser.parse_args()

    print("=== generate_fixtures.py ===\n")
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    errors = 0

    steps = [
        ("sample_player.json", lambda: fetch_sample_player(args.ign)),
        ("sample_guild.json", lambda: fetch_sample_guild(args.guild)),
        ("sample_items.json", fetch_sample_items),
    ]

    for filename, fetcher in steps:
        print(f"Fetching {filename}...")
        try:
            data = fetcher()
            _write(FIXTURES_DIR / filename, data, args.dry_run)
        except Exception as e:
            print(f"  FAIL: {e}")
            errors += 1

    print(f"\n{'='*30}")
    if errors:
        print(f"FAIL — {errors} fixture(s) could not be generated.")
        sys.exit(1)
    if args.dry_run:
        print("DRY RUN complete — no files written.")
    else:
        print("Done.")


if __name__ == "__main__":
    main()
