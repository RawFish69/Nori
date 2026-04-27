"""
Player-related utility functions for Nori bot.

This module contains functions for fetching, processing, and displaying
player statistics and information.
"""
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from lib.wynn_api import Player
from lib.utils import format_compact

RAID_STATS_LABELS = {
    "damageDealt": "Damage Dealt",
    "damageTaken": "Damage Taken",
    "healthHealed": "Healing",
    "deaths": "Deaths",
    "buffsTaken": "Buffs Taken",
    "gambitsUsed": "Gambits Used",
}

RAID_NAME_MAP = {
    "Nest of the Grootslangs": "NOG",
    "The Nameless Anomaly": "TNA",
    "The Canyon Colossus": "TCC",
    "Orphion's Nexus of Light": "NOL",
    "The Wartorn Palace": "TWP",
    "Unknown": "TWP",
}

RAID_DISPLAY_ORDER = ["TNA", "TCC", "NOL", "NOG", "TWP"]


def _format_number(value) -> str:
    try:
        return f"{int(value or 0):,}"
    except (TypeError, ValueError):
        return "0"


def _format_date(value: str) -> str:
    if not value:
        return "N/A"
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
    except Exception:
        return value


def _render_raid_stats_block(raid_stats: Optional[Dict[str, Any]]) -> str:
    if not raid_stats:
        return "No raid stats recorded."
    return "\n".join(f"**{label}:** {format_compact(raid_stats.get(key, 0))}" for key, label in RAID_STATS_LABELS.items())


def _short_raid_map(raid_list: Dict[str, Any]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for name, value in (raid_list or {}).items():
        short = RAID_NAME_MAP.get(name, name)
        out[short] = out.get(short, 0) + int(value or 0)
    return out


def _render_combined_raid_clears(raids: Dict[str, Any], guild_raids: Optional[Dict[str, Any]]) -> str:
    raid_list = _short_raid_map((raids or {}).get("list") or {})
    guild_raid_list = _short_raid_map((guild_raids or {}).get("list") or {})
    rows = []
    for raid in RAID_DISPLAY_ORDER:
        rows.append((raid, _format_number(raid_list.get(raid, 0)), _format_number(guild_raid_list.get(raid, 0))))
    rows.append(("All", _format_number((raids or {}).get("total", 0)), _format_number((guild_raids or {}).get("total", 0))))

    content_width = max(len("Content"), *(len(row[0]) for row in rows))
    normal_width = max(len("Normal"), *(len(row[1]) for row in rows))
    guild_width = max(len("Guild"), *(len(row[2]) for row in rows))
    header = f"{'Content'.ljust(content_width)}  {'Normal'.rjust(normal_width)}  {'Guild'.rjust(guild_width)}"
    sep = f"{'-' * content_width}  {'-' * normal_width}  {'-' * guild_width}"
    body = [
        f"{content.ljust(content_width)}  {normal.rjust(normal_width)}  {guild.rjust(guild_width)}"
        for content, normal, guild in rows
    ]
    return "```\n" + "\n".join([header, sep, *body]) + "\n```"


def player_stats(ign: str, include_history: bool = False) -> Optional[Tuple[Dict[str, str], bool, str]]:
    """
    Fetch and format player statistics.

    Args:
        ign: Player in-game name

    Returns:
        Tuple containing (display fields, online_status, player_uuid)
        Returns None if player not found
    """
    player = Player()
    player_data = player.get_player_main(ign)

    # Player.get_player_main now handles MultipleObjectsReturned (HTTP 300) by
    # picking the UUID with the latest lastJoin. If we still lack a uuid here,
    # the player genuinely doesn't exist or the API returned an error payload.
    try:
        player_uuid = player_data["uuid"]
        online_status = player_data.get("online", False)
    except (KeyError, TypeError) as error:
        print(f"Unable to resolve player '{ign}': {player_data}")
        return None
    
    rank_map = {
        "vip": "VIP",
        "vipplus": "VIP+",
        "hero": "Hero",
        "champion": "Champion",
    }
    
    rank = player_data.get("rank") or "Player"
    if rank == "Player":
        support = player_data.get("supportRank") or ""
        game_rank = rank_map.get(support, "None")
    else:
        game_rank = player_data.get("shortenedRank") or rank
    
    print(player_data)
    
    first_joined = _format_date(player_data.get("firstJoin", ""))
    last_joined = _format_date(player_data.get("lastJoin", ""))

    global_data = player_data.get("globalData", {})
    raids = global_data.get("raids", {})
    guild_raids = global_data.get("guildRaids") or {}
    dungeon_total = (global_data.get("dungeons") or {}).get("total", 0)
    guild = player_data.get("guild") or None

    status = f"Online on `{player_data.get('server', 'Unknown')}`" if online_status else "Offline"
    guild_display = f"[{guild['prefix']}] {guild['name']} | {guild['rank']}" if guild else "N/A"
    pvp = global_data.get("pvp", {})
    pvp_kills = pvp.get("kills", 0)
    pvp_deaths = pvp.get("deaths", 0)
    kd = round(pvp_kills / pvp_deaths, 2) if pvp_deaths else 0

    display = {
        "profile": (
            f"**Rank:** {game_rank}\n"
            f"**Status:** {status}\n"
            f"**Guild:** {guild_display}\n"
            f"**First Joined:** {first_joined}\n"
            f"**Last Seen:** {last_joined}"
        ),
        "progress": (
            f"**Total Level:** {_format_number(global_data.get('totalLevel', 0))}\n"
            f"**Playtime:** {_format_number(player_data.get('playtime', 0))} hours\n"
            f"**Dungeons:** {_format_number(dungeon_total)}\n"
            f"**Quests:** {_format_number(global_data.get('completedQuests', 0))}\n"
            f"**World Events:** {_format_number(global_data.get('worldEvents', 0))}"
        ),
        "gameplay": (
            f"**Mobs Killed:** {format_compact(global_data.get('mobsKilled', 0))}\n"
            f"**Chests Opened:** {format_compact(global_data.get('chestsFound', 0))}\n"
            f"**Wars Joined:** {_format_number(global_data.get('wars', 0))}\n"
            f"**PvP:** {_format_number(pvp_kills)} K / {_format_number(pvp_deaths)} D [{kd}]"
        ),
        "raids": _render_combined_raid_clears(raids, guild_raids),
        "raid_stats": _render_raid_stats_block(global_data.get("raidStats")),
    }

    if include_history:
        restrictions = player_data.get("restrictions") or {}
        if restrictions.get("guildHistoryAccess") is False:
            display["guild_history"] = "Player has hidden their guild history."
        elif player_data.get("guildHistory"):
            history = player_data["guildHistory"]
            display["guild_history"] = "\n".join(f"- {entry}" for entry in history[:10])
    
    print(display)
    return display, online_status, player_uuid


async def fetch_player_data(ign: str) -> Dict[str, Any]:
    """
    Fetch comprehensive player data for leaderboard purposes.

    Args:
        ign: Player in-game name

    Returns:
        Dictionary containing player statistics
    """
    player = Player()
    full_player = player.get_player_main(ign)
    raid_stats = full_player["globalData"]["raids"]
    dungeon_stats = full_player["globalData"]["dungeons"]["total"]
    chest_stats = full_player["globalData"]["chestsFound"]
    mob_stats = full_player["globalData"]["mobsKilled"]
    war_stats = full_player["globalData"]["wars"]
    world_events = full_player["globalData"].get("worldEvents") or 0
    guild_raids = full_player["globalData"].get("guildRaids") or {}
    g_list = guild_raids.get("list") or {}

    player_info = {
        "raids_total": raid_stats["total"],
        "tna": raid_stats.get("The Nameless Anomaly", 0),
        "tcc": raid_stats.get("The Canyon Colossus", 0),
        "nol": raid_stats.get("Orphion's Nexus of Light", 0),
        "nog": raid_stats.get("Nest of the Grootslangs", 0),
        # TWP arrives under "Unknown" on v3.3 prod; expected to be "The Wartorn Palace"
        # post-v3.7. Remove the Unknown alias after cut-day verification.
        "twp": raid_stats.get("The Wartorn Palace", raid_stats.get("Unknown", 0)),
        "dungeons": dungeon_stats if dungeon_stats else 0,
        "chests": chest_stats if chest_stats else 0,
        "mobs": mob_stats if mob_stats else 0,
        "wars": war_stats if war_stats else 0,
        "world_events": world_events,
        "guild_raids_total": guild_raids.get("total") or 0,
        "g_tna": g_list.get("The Nameless Anomaly") or 0,
        "g_tcc": g_list.get("The Canyon Colossus") or 0,
        "g_nol": g_list.get("Orphion's Nexus of Light") or 0,
        "g_nog": g_list.get("Nest of the Grootslangs") or 0,
        "g_twp": g_list.get("The Wartorn Palace", g_list.get("Unknown", 0)) or 0,
    }
    raid_stats_raw = full_player["globalData"].get("raidStats") or {}
    if raid_stats_raw:
        player_info["raid_stats"] = {
            "damage_dealt": raid_stats_raw.get("damageDealt", 0),
            "damage_taken": raid_stats_raw.get("damageTaken", 0),
            "heal": raid_stats_raw.get("healthHealed", 0),
            "deaths": raid_stats_raw.get("deaths", 0),
            "buffs_taken": raid_stats_raw.get("buffsTaken", 0),
            "gambits_used": raid_stats_raw.get("gambitsUsed", 0),
        }
    guild_history = full_player.get("guildHistory") or []
    if guild_history:
        player_info["guild_history"] = guild_history
    return player_info

