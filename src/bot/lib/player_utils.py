"""
Player-related utility functions for Nori bot.

This module contains functions for fetching, processing, and displaying
player statistics and information.
"""
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from lib.wynn_api import Player


def player_stats(ign: str) -> Optional[Tuple[str, bool, str]]:
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
    
    try:
        online_status = player.online_status(ign)
        player_uuid = player_data["uuid"]
    except Exception as error:
        try:
            player_uuid = list(player_data)[0]
            player_data = player.get_player_main(player_uuid)
        except Exception:
            player_uuid = list(player_data)[1]
            player_data = player.get_player_main(player_uuid)
        online_status = player.online_status(player_uuid)
    
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
    display += f"Total Level: {player_data['globalData']['totalLevel']}\n"
    
    max_raid_name_length = 0
    raid_map = {
        "Nest of the Grootslangs": "NOG",
        "The Nameless Anomaly": "TNA",
        "The Canyon Colossus": "TCC",
        "Orphion's Nexus of Light": "NOL"
    }
    
    for raid in raids["list"].keys():
        if len(raid_map[raid]) > max_raid_name_length:
            max_raid_name_length = len(raid_map[raid])
    
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
        display += f'║ {raid_map[raid].ljust(max_width)} ║ {str(raids["list"][raid]).rjust(num_width)} ║\n'
    
    display += f'║ {"Dungeons".ljust(max_width)} ║ {str(dungeon_total).rjust(num_width)} ║\n'
    display += f'║ {"All Raids".ljust(max_width)} ║ {str(raid_total).rjust(num_width)} ║\n'
    display += '╚' + '═' * border_width_1 + '╩' + '═' * border_width_2 + '╝\n'
    
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
    raid_stats = player.raid_global(ign)
    dungeon_stats = player.dungeon_global(ign)
    chest_stats = player.chest_global(ign)
    mob_stats = player.mobs_global(ign)
    war_stats = player.war_global(ign)
    
    player_info = {
        "raids_total": raid_stats["total"],
        "tna": raid_stats.get("The Nameless Anomaly", 0),
        "tcc": raid_stats.get("The Canyon Colossus", 0),
        "nol": raid_stats.get("Orphion's Nexus of Light", 0),
        "nog": raid_stats.get("Nest of the Grootslangs", 0),
        "dungeons": dungeon_stats if dungeon_stats else 0,
        "chests": chest_stats if chest_stats else 0,
        "mobs": mob_stats if mob_stats else 0,
        "wars": war_stats if war_stats else 0
    }
    return player_info

