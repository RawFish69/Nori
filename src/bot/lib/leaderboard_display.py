"""
Author: RawFish
Description: Module for handling various leaderboards (profession, raid, stat).
"""

import requests
import json
from typing import Optional


class LeaderboardManager:
    """
    A manager for retrieving and formatting leaderboard data.
    """

    def __init__(self, leaderboard_path: str = "your path"):
        """
        :param leaderboard_path: The path where the leaderboard is stored.
        """
        self.leaderboard_path = leaderboard_path

    def get_profession_leaderboard(self, profession: str) -> str:
        """
        Fetch and format a Wynncraft profession leaderboard for 'solo' competition.

        :param profession: Name of the profession (e.g., 'mining', 'fishing', 'woodcutting', etc.)
        :return: Formatted string ready for display.
        """
        url = f'https://api.wynncraft.com/v2/leaderboards/player/solo/{profession}'
        response = requests.get(url)
        if response.status_code != 200:
            return f"Error fetching profession leaderboard for {profession}."

        try:
            data = response.json()
            prof_rank = data.get('data', [])
        except Exception:
            return f"Invalid response for profession leaderboard: {profession}"

        names = []
        levels = []
        exp = []

        for info in prof_rank:
            names.append(info.get('name', 'Unknown'))
            char_info = info.get('character', {})
            levels.append(char_info.get('level', 0))
            exp.append(char_info.get('xp', 0))

        # Reverse order
        names.reverse()
        levels.reverse()
        exp.reverse()

        display = '```json\n'
        display += f'   {profession} Solo Ranking\n'
        display += ' #| Player Name          | Level |  Current XP\n'
        for i in range(min(20, len(names))):
            line = '{0:2d}| {1:20s} |  {2:3d}  | {3:11d}\n'.format(
                i + 1, names[i], levels[i], exp[i]
            )
            display += line
        display += '```'
        return display

    async def get_raid_leaderboard(self, raid_name: str) -> Optional[dict]:
        """
        Retrieve pre-computed leaderboard data for a given raid from a local file.

        :param raid_name: 'tna', 'tcc', 'nol', 'nog', or 'all'.
        :return: Dict of {player: clears}, or None if not found.
        """
        with open(self.leaderboard_path, "r") as file:
            data = json.load(file).get("ranking", {})

        raid_name = raid_name.lower()
        try:
            if raid_name == "tna":
                return data["tna"]
            elif raid_name == "tcc":
                return data["tcc"]
            elif raid_name == "nol":
                return data["nol"]
            elif raid_name == "nog":
                return data["nog"]
            elif raid_name == "all":
                return data["raids_total"]
        except KeyError:
            pass

        return None

    async def get_stat_leaderboard(self, stat_name: str) -> Optional[dict]:
        """
        Retrieve pre-computed leaderboard data for a given stat (e.g., chests, mobs, wars, etc.)

        :param stat_name: 'chest', 'mob', 'war', 'dungeon', 'playtime', 'pvp', 'quests', 'levels'.
        :return: Dict of {player: value}, or None if not found.
        """
        with open(self.leaderboard_path, "r") as file:
            data = json.load(file).get("ranking", {})

        stat_name = stat_name.lower()
        mapping = {
            "chest": "chests",
            "mob": "mobs",
            "war": "wars",
            "dungeon": "dungeons",
            "playtime": "playtime",
            "pvp": "pvp_kills",
            "quests": "quests",
            "levels": "levels"
        }
        key = mapping.get(stat_name)
        if not key:
            return None

        return data.get(key)
