"""
Leaderboard utility functions for Nori bot.

This module contains functions for fetching and processing leaderboard data
for raids, stats, and professions.

The raid leaderboard is now unified: per-raid clears AND aggregate raid metrics
(damage dealt, damage taken, healing, deaths, buffs, gambits) live under the
same `ranking` block in `player_leaderboard.json`. Callers pass either a clear
key (`tna`, `tcc`, ..., `all`) or a metric key (`damage_dealt`, `heal`, ...)
and `raid_leaderboard()` resolves it to the right ranking list.
"""
import json
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path

# Friendly metric alias -> ranking key under `ranking` in player_leaderboard.json.
# Used by the bot's `/lb raid` choices so users type `damage_dealt` rather than
# the wire-side `raid_damage_dealt`.
RAID_METRIC_KEYS = {
    "damage_dealt": "raid_damage_dealt",
    "damage_taken": "raid_damage_taken",
    "heal": "raid_heal",
    "deaths": "raid_deaths",
    "buffs_taken": "raid_buffs_taken",
    "gambits_used": "raid_gambits_used",
}

# Per-raid clear key aliases. `all` -> `raids_total`; the rest map identity.
# Kept explicit so future raid additions land in one place.
RAID_CLEAR_KEYS = {
    "tna": "tna",
    "tcc": "tcc",
    "nol": "nol",
    "nog": "nog",
    "twp": "twp",
    "all": "raids_total",
    "raids_total": "raids_total",
}

# Back-compat: existing call sites still import this constant.
RAID_STATS_LEADERBOARD_KEYS = dict(RAID_METRIC_KEYS)


def _ranking_is_meaningful(ranking_data):
    """A ranking is "meaningful" when at least one entry has a non-zero value.

    Used to suppress empty-stat leaderboards (e.g. a raid metric Wynncraft has
    not yet backfilled, leaving every player at 0) so the bot prints "no data
    yet" instead of a 100-line wall of zeros.
    """
    return max(
        (list(entry.values())[0] for entry in (ranking_data or []) if entry),
        default=0,
    ) > 0


async def profession_leaderboard(prof: str) -> str:
    """
    Fetch and format profession leaderboard.

    Args:
        prof: Profession name

    Returns:
        Formatted string displaying top 20 players
    """
    profession = prof
    server = requests.get(f'https://api.wynncraft.com/v2/leaderboards/player/solo/{profession}')
    prof_info = server.json()
    prof_rank = prof_info.get('data')

    names = []
    levels = []
    exp = []

    for info in prof_rank:
        name = info.get('name')
        names.append(name)
        rank_info = info.get('character')
        level = rank_info.get('level')
        xp = rank_info.get('xp')
        levels.append(level)
        exp.append(xp)

    names.reverse()
    levels.reverse()
    exp.reverse()

    display = '```json\n'
    display += f'   {profession} Solo Ranking\n'
    display += ' #| Player Name          | Level |  Current XP\n'

    for i in range(20):
        line = '{0:2d}| {1:20s} |  {2:3d}  | {3:11d}\n'.format(i + 1, names[i], levels[i], exp[i])
        display += line

    display += '```'
    print(display)
    return display


def _resolve_raid_key(raid: str) -> Optional[str]:
    """Resolve a user-facing raid leaderboard key to the canonical ranking key.

    Returns None for unknown inputs so callers can short-circuit with a clean
    error rather than silently fetching an empty list.
    """
    key = (raid or "").strip().lower()
    if key in RAID_CLEAR_KEYS:
        return RAID_CLEAR_KEYS[key]
    if key in RAID_METRIC_KEYS:
        return RAID_METRIC_KEYS[key]
    return None


async def raid_leaderboard(
    raid: str,
    leaderboard_path: Optional[Path] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch a raid leaderboard.

    Accepts either a per-raid clear key (`tna`, `tcc`, `nol`, `nog`, `twp`,
    `all`/`raids_total`) or an aggregate raid metric key (`damage_dealt`,
    `damage_taken`, `heal`, `deaths`, `buffs_taken`, `gambits_used`).

    Returns:
        List of `{IGN: value}` entries (top-100), or `None` on read failure /
        unknown key. Returns an empty list when the underlying ranking exists
        but contains only zero values (e.g. a not-yet-backfilled metric).
    """
    if leaderboard_path is None:
        leaderboard_path = Path("/home/ubuntu/data-scripts/database/player_leaderboard.json")

    ranking_key = _resolve_raid_key(raid)
    if ranking_key is None:
        return None

    try:
        with open(leaderboard_path, "r") as file:
            leaderboard_data = json.load(file)["ranking"]
        ranking_data = leaderboard_data.get(ranking_key, [])

        # Aggregate raid metrics can legitimately be all-zero pre-backfill;
        # surface that as an empty list so callers render a "no data yet"
        # state. Per-raid clear counts are returned even if zero because the
        # absence of clears is itself meaningful for ranking display.
        if ranking_key in RAID_METRIC_KEYS.values() and not _ranking_is_meaningful(ranking_data):
            return []
        return ranking_data
    except Exception as error:
        print(f"Error fetching raid leaderboard: {error}")

    return None


# Back-compat shim. New code should call `raid_leaderboard(metric_alias)`.
async def raid_stats_leaderboard(
    sort_by: str,
    leaderboard_path: Optional[Path] = None,
) -> Optional[List[Dict[str, Any]]]:
    """Deprecated: use `raid_leaderboard(metric_alias)` instead.

    Kept so older callers that still pass the friendly metric alias keep
    working through the rollout. Returns the same list-of-`{IGN: value}`
    shape as `raid_leaderboard`.
    """
    if sort_by not in RAID_METRIC_KEYS:
        sort_by = "damage_dealt"
    return await raid_leaderboard(sort_by, leaderboard_path)


async def stat_leaderboard(stat: str, leaderboard_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch stat leaderboard data.

    Args:
        stat: Stat name (chest, mob, war, dungeon, playtime, pvp, quests, levels)
        leaderboard_path: Optional path to leaderboard JSON file

    Returns:
        Dictionary containing leaderboard data or None
    """
    stat_name = stat.lower()

    if leaderboard_path is None:
        leaderboard_path = Path("/home/ubuntu/data-scripts/database/player_leaderboard.json")

    try:
        with open(leaderboard_path, "r") as file:
            leaderboard_data = json.load(file)["ranking"]

        stat_map = {
            "chest": "chests",
            "mob": "mobs",
            "war": "wars",
            "dungeon": "dungeons",
            "playtime": "playtime",
            "pvp": "pvp_kills",
            "quests": "quests",
            "levels": "levels"
        }

        if stat_name in stat_map:
            return leaderboard_data[stat_map[stat_name]]
    except Exception as error:
        print(f"Error fetching stat leaderboard: {error}")

    return None
