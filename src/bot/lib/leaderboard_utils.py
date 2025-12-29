"""
Leaderboard utility functions for Nori bot.

This module contains functions for fetching and processing leaderboard data
for raids, stats, and professions.
"""
import json
import requests
from typing import Optional, Dict, Any
from pathlib import Path


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


async def raid_leaderboard(raid: str, leaderboard_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch raid leaderboard data.

    Args:
        raid: Raid name (tna, tcc, nol, nog, all)
        leaderboard_path: Optional path to leaderboard JSON file

    Returns:
        Dictionary containing leaderboard data or None
    """
    raid_name = raid.lower()
    
    if leaderboard_path is None:
        leaderboard_path = Path("/home/ubuntu/data-scripts/database/player_leaderboard.json")
    
    try:
        with open(leaderboard_path, "r") as file:
            leaderboard_data = json.load(file)["ranking"]
        
        raid_map = {
            "tna": "tna",
            "tcc": "tcc",
            "nol": "nol",
            "nog": "nog",
            "all": "raids_total"
        }
        
        if raid_name in raid_map:
            return leaderboard_data[raid_map[raid_name]]
    except Exception as error:
        print(f"Error fetching raid leaderboard: {error}")
    
    return None


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

