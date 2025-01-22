"""
Author: RawFish
Description: Module for retrieving and managing player data/stats
             using the Player class (Wynncraft API wrapper).
"""

import json
import time
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

from .basic_wrapper import Player

class PlayerManager:
    """
    A manager for retrieving Wynncraft player information and storing local references.
    It wraps around your Player() class to provide additional formatting, caching, etc.
    """

    def __init__(
        self,
        player_api: Player = None,
        ign_db_path: str = "your path",
        player_data_path: str = "your path"
    ):
        """
        :param player_api: An instance of your Player class for Wynncraft requests.
        :param ign_db_path: Path to the file.
        :param player_data_path: Path to the file.
        """
        self.player_api = player_api or Player()
        self.ign_db_path = ign_db_path
        self.player_data_path = player_data_path

    def get_player_stats(self, ign: str) -> Optional[Tuple[str, bool, str]]:
        """
        Fetch a player's main stats and produce a formatted display output.

        :param ign: Player IGN
        :return: (display_str, online_status, player_uuid) or None if something goes wrong.
        """
        try:
            player_data = self.player_api.get_player_main(ign)
            player_uuid = player_data.get("uuid", "")
            online_status = player_data.get("online", False)

            if not player_uuid:
                pass

            game_rank = self._resolve_rank(player_data)
            display_str = self._build_player_display(ign, player_data, online_status, game_rank)

            print(display_str)
            return (display_str, online_status, player_uuid)

        except Exception as error:
            print(f"Error in get_player_stats: {error}")
            return None

    async def check_ign_db(self, ign: str):
        """
        Check if the given IGN is in the local database. If not, add it.
        """
        with open(self.ign_db_path, "r") as f:
            data = json.load(f)
            ign_list = data.get("ign", [])

        with open(self.player_data_path, "r") as f:
            player_data = json.load(f)
            if ign in player_data.get("data", {}) or ign in ign_list:
                print(f"{ign} already in database")
            else:
                ign_list.append(ign)
                print(f"{ign} added to list")

        with open(self.ign_db_path, "w") as f:
            output = {"ign": ign_list, "timestamp": int(time.time())}
            json.dump(output, f, indent=3)

    async def fetch_player_data(self, ign: str) -> Dict[str, Any]:
        """
        Gathers a summary of the player's key stats by calling your Player() methods.

        :param ign: The player's in-game name.
        :return: A dict summarizing raids, dungeons, etc.
        """
        raid_stats = self.player_api.raid_global(ign)
        dungeon_stats = self.player_api.dungeon_global(ign)
        chest_stats = self.player_api.chest_global(ign)
        mob_stats = self.player_api.mobs_global(ign)
        war_stats = self.player_api.war_global(ign)

        player_info = {
            "raids_total": raid_stats.get("total", 0),
            "tna": raid_stats.get("The Nameless Anomaly", 0),
            "tcc": raid_stats.get("The Canyon Colossus", 0),
            "nol": raid_stats.get("Orphion's Nexus of Light", 0),
            "nog": raid_stats.get("Nest of the Grootslangs", 0),
            "dungeons": dungeon_stats or 0,
            "chests": chest_stats or 0,
            "mobs": mob_stats or 0,
            "wars": war_stats or 0
        }
        return player_info

    def get_server(self) -> Dict[str, list]:
        """
        Example function if you need Wynncraft server data. 
        If not needed, you can remove or adapt it.
        """
        import requests
        url = "https://api.wynncraft.com/v3/player"
        response = requests.get(url)
        if response.status_code != 200:
            print("Error fetching server data.")
            return {}

        server_data = response.json().get("players", {})
        online_data = {}
        for username, server in server_data.items():
            online_data.setdefault(server, []).append(username)

        return online_data

    def _build_player_display(
        self,
        ign: str,
        player_data: Dict[str, Any],
        online_status: bool,
        game_rank: str
    ) -> str:
        """
        Helper that constructs a multi-line string with basic player info.
        """
        display = ""

        if online_status:
            server = player_data.get("server", "Unknown")
            display += f"[{game_rank}] {ign} is on {server}\n"
        else:
            display += f"[{game_rank}] {ign} is offline\n"

        guild_info = player_data.get("guild")
        if guild_info:
            prefix = guild_info.get("prefix", "")
            name = guild_info.get("name", "N/A")
            rank = guild_info.get("rank", "")
            display += f"Guild: [{prefix}] {name} | {rank}\n"
        else:
            display += "Guild: N/A\n"

        first_join = self._format_datetime(player_data.get("firstJoin", ""))
        last_join = self._format_datetime(player_data.get("lastJoin", ""))
        display += f"First Joined: {first_join}\n"
        display += f"Last Seen: {last_join}\n"

        global_data = player_data.get("globalData", {})
        display += f"Mobs Killed: {global_data.get('killedMobs', 0)}\n"
        display += f"Chests Opened: {global_data.get('chestsFound', 0)}\n"
        display += f"Playtime: {player_data.get('playtime', 0)} hours\n"
        display += f"War Count: {global_data.get('wars', 0)}\n"

        pvp_data = global_data.get("pvp", {})
        kills = pvp_data.get("kills", 0)
        deaths = pvp_data.get("deaths", 0)
        kd = round(kills / deaths, 2) if deaths else kills
        display += f"PvP: {kills} K / {deaths} D [{kd}]\n"

        display += f"Quests Total: {global_data.get('completedQuests', 0)}\n"
        display += f"Total Level: {global_data.get('totalLevel', 0)}\n"

        return display

    def _format_datetime(self, dt_str: str) -> str:
        """
        Converts Wynncraft date/time string to a more user-friendly format if possible.
        """
        if not dt_str:
            return "N/A"
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return dt_str

    def _resolve_rank(self, player_data: Dict[str, Any]) -> str:
        """
        Determine a suitable rank string from the Wynncraft data.
        E.g., 'Player', 'VIP+', 'Moderator', etc.
        """
        rank_map = {
            "vip": "VIP",
            "vipplus": "VIP+",
            "hero": "Hero",
            "champion": "Champion",
        }

        main_rank = player_data.get("rank", "Player")
        support_rank = player_data.get("supportRank", "")
        shortened_rank = player_data.get("shortenedRank", "")

        if main_rank.lower() == "player":
            return rank_map.get(support_rank.lower(), "None")
        else:
            return shortened_rank if shortened_rank else main_rank
