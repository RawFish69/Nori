"""
Author: RawFish
Description: Module for retrieving and formatting guild data
             using the Guild class (Wynncraft API wrapper).
"""

from datetime import datetime
from typing import Optional, Tuple, Dict, Any

from .basic_wrapper import Guild


class GuildManager:
    """
    A manager for retrieving Wynncraft guild information and formatting it for display.
    It wraps around your Guild() class methods.
    """

    def __init__(self, guild_api: Guild = None):
        """
        :param guild_api: An instance of your Guild class for Wynncraft requests.
        """
        self.guild_api = guild_api or Guild()

    def get_guild_stats(self, user_input: str) -> Optional[Tuple[str, str, str, str, str]]:
        """
        Retrieve guild stats for a given guild name/prefix and format the display.

        :param user_input: The guild name or prefix to query.
        :return: (display_str, guild_name, guild_prefix, banner_tier, banner_structure)
                 or None if an error occurred.
        """
        try:
            guild_data = self.guild_api.get_guild_data(user_input)
            if not guild_data:
                print("No guild data found.")
                return None

            created_str = guild_data.get("created", "")
            created_dt = datetime.strptime(created_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            created_date = created_dt.date()

            name = guild_data.get("name", "Unknown")
            prefix = guild_data.get("prefix", "??")
            members = guild_data.get("members", {})
            level = guild_data.get("level", 0)
            xp_percent = guild_data.get("xpPercent", 0)
            territories = guild_data.get("territories", 0)
            wars = guild_data.get("wars", 0)

            online_players = self._collect_online_players(members)

            display = ""
            display += f"{name} [{prefix}]\n"
            display += f"Owner: {self._get_owner_name(members)}\n"
            display += f"Created on {created_date}\n"
            display += f"Level: {level} [{xp_percent}%]\n"
            display += f"War count: {wars}\n"
            display += f"Territory count: {territories}\n"
            total_members = self._count_total_members(members)
            display += f"Members: {total_members}\n"
            display += f"Online Players: {len(online_players)}/{total_members}\n"

            if online_players:
                display += self._format_online_table(online_players)

            banner = guild_data.get("banner", {})
            banner_tier = str(banner.get("tier", "0"))
            banner_structure = banner.get("structure", "No structure")

            return (display, name, prefix, banner_tier, banner_structure)

        except Exception as error:
            print(f"Error fetching guild stats: {error}")
            return None

    def _collect_online_players(self, members: Dict[str, Dict]) -> Dict[str, Dict[str, str]]:
        """
        Parse guild member structure from the Wynncraft API and find all online players.

        :return: {playerName: {"Server": server_name, "Rank": rank_display}}
        """
        online_players = {}
        ranks = ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]
        rank_map = {
            "owner": "*****",
            "chief": "****",
            "strategist": "***",
            "captain": "**",
            "recruiter": "*",
            "recruit": ""
        }

        for rank in ranks:
            rank_data = members.get(rank, {})
            for player_name, player_info in rank_data.items():
                if player_info.get("online", False):
                    server_name = player_info.get("server", "Unknown")
                    online_players[player_name] = {
                        "Server": server_name,
                        "Rank": rank_map.get(rank, "")
                    }

        return online_players

    def _format_online_table(self, online_players: Dict[str, Dict[str, str]]) -> str:
        """
        Returns a formatted table of the currently online players.
        """
        if not online_players:
            return ""

        max_name_length = max(len(name) for name in online_players.keys())
        max_server_length = max(len(data["Server"]) for data in online_players.values())

        line = ""
        line += "╔" + "═" * (max_server_length + 2) + "╦" + "═" * (max_name_length + 2) + "╦═══════╗\n"
        line += "║ " + "WC".center(max_server_length) + " ║ " + "Player".center(max_name_length) + " ║ Rank  ║\n"
        line += "╠" + "═" * (max_server_length + 2) + "╬" + "═" * (max_name_length + 2) + "╬═══════╣\n"

        for player, data in online_players.items():
            server_str = data["Server"].center(max_server_length)
            player_str = player.center(max_name_length)
            rank_str = data["Rank"].rjust(5)
            line += f"║ {server_str} ║ {player_str} ║ {rank_str} ║\n"

        line += "╚" + "═" * (max_server_length + 2) + "╩" + "═" * (max_name_length + 2) + "╩═══════╝\n"
        return line

    def _count_total_members(self, members: Dict[str, Dict]) -> int:
        """
        Count how many total members are in the provided structure.
        """
        total = 0
        for rank_data in members.values():
            total += len(rank_data)
        return total

    def _get_owner_name(self, members: Dict[str, Dict]) -> str:
        """
        Extract the single owner name from the guild member structure, or 'Unknown' if none found.
        """
        owner_data = members.get("owner", {})
        if not owner_data:
            return "Unknown"
        return list(owner_data.keys())[0] if owner_data else "Unknown"
