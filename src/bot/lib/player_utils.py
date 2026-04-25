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


def _render_raid_stats_block(raid_stats: Optional[Dict[str, Any]]) -> str:
    if not raid_stats:
        return ""
    display = "\nRaid Stats\n"
    for key, label in RAID_STATS_LABELS.items():
        display += f"{label}: {format_compact(raid_stats.get(key, 0))}\n"
    return display


def _render_guild_raid_table(guild_raids: Optional[Dict[str, Any]]) -> str:
    """Render the per-guild-raid clears block. Returns "" when the player has
    no guild raid data so the embed stays compact for non-raiders.

    Earlier revisions of `player_stats` referenced this helper without
    actually defining it — it was inlined into the legacy monolith bot but
    never re-exported into the modular package. This stub keeps the
    function name resolved while preserving the empty-on-missing contract.
    """
    if not guild_raids:
        return ""
    total = int(guild_raids.get("total") or 0)
    raid_list = guild_raids.get("list") or {}
    if total == 0 and not raid_list:
        return ""
    raid_map = {
        "The Nameless Anomaly": "TNA",
        "The Canyon Colossus": "TCC",
        "Orphion's Nexus of Light": "NOL",
        "Nest of the Grootslangs": "NOG",
        "The Wartorn Palace": "TWP",
        "Unknown": "TWP",
    }
    lines = ["\nGuild Raid Clears"]
    for name, value in raid_list.items():
        short = raid_map.get(name, name)
        lines.append(f"{short}: {format_compact(value)}")
    lines.append(f"Total: {format_compact(total)}")
    return "\n".join(lines) + "\n"


def player_stats(ign: str, include_history: bool = False) -> Optional[Tuple[str, bool, str]]:
    """
    Fetch and format player statistics.

    Args:
        ign: Player in-game name

    Returns:
        Tuple containing (display_string, online_status, player_uuid)
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
    
    if player_data["rank"] == "Player":
        game_rank = rank_map[player_data["supportRank"]] if player_data["supportRank"] else "None"
    else:
        game_rank = player_data["shortenedRank"] if player_data["shortenedRank"] else player_data["rank"]
    
    print(player_data)
    
    try:
        first_joined = datetime.strptime(player_data["firstJoin"], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d %H:%M:%S')
        last_joined = datetime.strptime(player_data["lastJoin"], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d %H:%M:%S')
    except Exception as error:
        print(error)
        first_joined = player_data["firstJoin"]
        last_joined = player_data["lastJoin"]
    
    raids = player_data["globalData"]["raids"]
    raid_total = raids["total"]
    dungeon_total = player_data["globalData"]["dungeons"]["total"]
    guild = player_data["guild"] if player_data["guild"] else None
    display = ""
    
    if online_status is True:
        online_server = player_data["server"]
        display += f'[{game_rank}] {ign} is on {online_server}\n'
    else:
        display += f'[{game_rank}] {ign} is offline\n'
    
    display += f'Guild: [{guild["prefix"]}] {guild["name"]} | {guild["rank"]}\n' if guild else f"Guild: N/A\n"
    display += f"First Joined: {first_joined}\n"
    display += f"Last Seen: {last_joined}\n"
    display += f'Mobs Killed: {player_data["globalData"]["mobsKilled"]}\n'
    display += f'Chests Opened: {player_data["globalData"]["chestsFound"]}\n'
    display += f'Playtime: {player_data["playtime"]} hours\n'
    display += f'War Count: {player_data["globalData"]["wars"]}\n'
    
    pvp_kills = player_data["globalData"]["pvp"]["kills"]
    pvp_deaths = player_data["globalData"]["pvp"]["deaths"]
    if pvp_kills == 0 or pvp_deaths == 0:
        KD = 0
    else:
        KD = round(pvp_kills / pvp_deaths, 2)
    
    display += f'PvP: {pvp_kills} K / {pvp_deaths} D [{KD}]\n'
    display += f'Quests Total: {player_data["globalData"]["completedQuests"]}\n'
    display += f'World Events: {player_data["globalData"].get("worldEvents", 0)}\n'
    guild_raids_total = (player_data["globalData"].get("guildRaids") or {}).get("total") or 0
    display += f'Guild Raids: {guild_raids_total}\n'
    total_deaths = sum(int((c or {}).get("deaths") or 0) for c in (player_data.get("characters") or {}).values())
    display += f'Total Deaths: {total_deaths}\n'
    display += f"Total Level: {player_data['globalData']['totalLevel']}\n"
    
    max_raid_name_length = 0
    # "Unknown" is the v3.3-prod label for TWP; unrecognized raids fall through to "NEW".
    raid_map = {
        "Nest of the Grootslangs": "NOG",
        "The Nameless Anomaly": "TNA",
        "The Canyon Colossus": "TCC",
        "Orphion's Nexus of Light": "NOL",
        "The Wartorn Palace": "TWP",
        "Unknown": "TWP",
    }
    
    for raid in raids["list"].keys():
        short = raid_map.get(raid, "NEW")
        if len(short) > max_raid_name_length:
            max_raid_name_length = len(short)
    
    max_width = max(max_raid_name_length, len("Dungeons"), len("All Raids"))
    max_raid_value_length = 0
    
    for value in raids["list"].values():
        if len(str(value)) > max_raid_value_length:
            max_raid_value_length = len(str(value))
    
    num_width = max(max_raid_value_length, len(str(dungeon_total)), len(str(raid_total)), 6)
    border_width_1 = max_width + 2
    border_width_2 = num_width + 2
    
    display += '╔' + '═' * border_width_1 + '╦' + '═' * border_width_2 + '╗\n'
    raid_heading = "Content".center(max_width)
    clears_heading = "Clears".center(num_width)
    display += f'║ {raid_heading} ║ {clears_heading} ║\n'
    display += '╠' + '═' * border_width_1 + '╬' + '═' * border_width_2 + '╣\n'
    
    for raid in raids["list"]:
        short = raid_map.get(raid, "NEW")
        display += f'║ {short.ljust(max_width)} ║ {str(raids["list"][raid]).rjust(num_width)} ║\n'
    
    display += f'║ {"Dungeons".ljust(max_width)} ║ {str(dungeon_total).rjust(num_width)} ║\n'
    display += f'║ {"All Raids".ljust(max_width)} ║ {str(raid_total).rjust(num_width)} ║\n'
    display += '╚' + '═' * border_width_1 + '╩' + '═' * border_width_2 + '╝\n'
    display += _render_guild_raid_table(player_data["globalData"].get("guildRaids"))
    display += _render_raid_stats_block(player_data["globalData"].get("raidStats"))
    if include_history:
        restrictions = player_data.get("restrictions") or {}
        if restrictions.get("guildHistoryAccess") is False:
            display += "\nGuild History\nPlayer has hidden their guild history.\n"
        elif player_data.get("guildHistory"):
            display += f"\nGuild History ({len(player_data['guildHistory'])} guilds)\n"
            for entry in player_data["guildHistory"][:10]:
                display += f"- {entry}\n"
    
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
    total_deaths = sum(int((c or {}).get("deaths") or 0) for c in (full_player.get("characters") or {}).values())
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
        "deaths": total_deaths,
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

