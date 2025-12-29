"""
Wynncraft API wrapper classes.
Provides interfaces for fetching player, guild, and item data.
"""
import requests
from lib.config import WYNN_AUTH_HEADER


class Player:
    """Wrapper for Wynncraft Player API"""

    def get_player_main(self, ign):
        """Get basic player data."""
        api_url = f"https://api.wynncraft.com/v3/player/{ign}"
        stat_request = requests.get(api_url, headers=WYNN_AUTH_HEADER)
        player_data = stat_request.json()
        return player_data

    def get_player_full(self, ign):
        """Get full player data."""
        api_url = f"https://api.wynncraft.com/v3/player/{ign}?fullResult"
        stat_request = requests.get(api_url, headers=WYNN_AUTH_HEADER)
        player_data = stat_request.json()
        return player_data

    def player_uuid(self, ign):
        """Get player UUID."""
        return self.get_player_main(ign)["uuid"]

    def online_status(self, ign):
        """Check if player is online."""
        return self.get_player_main(ign)["online"]

    def online_server(self, ign):
        """Get player's current server."""
        return self.get_player_main(ign)["server"]

    def war_global(self, ign):
        """Get player's global war stats."""
        return self.get_player_main(ign)["globalData"]["wars"]

    def mobs_global(self, ign):
        """Get player's global mob kills."""
        return self.get_player_main(ign)["globalData"]["killedMobs"]

    def chest_global(self, ign):
        """Get player's global chests found."""
        return self.get_player_main(ign)["globalData"]["chestsFound"]

    def raid_global(self, ign):
        """Get player's global raid stats."""
        player_data = self.get_player_main(ign)["globalData"]["raids"]
        raid_data = {"total": player_data["total"]}
        for raid in player_data["list"]:
            raid_data[raid] = player_data["list"][raid]
        return raid_data

    def dungeon_global(self, ign):
        """Get player's global dungeon completions."""
        player_data = self.get_player_main(ign)["globalData"]["dungeons"]
        dungeon_total = player_data["total"]
        return dungeon_total


class Guild:
    """Wrapper for Wynncraft Guild API"""

    def get_prefix_guild(self, prefix):
        """Get guild data by prefix."""
        guild_request = requests.get(
            f"https://api.wynncraft.com/v3/guild/prefix/{prefix}", 
            headers=WYNN_AUTH_HEADER
        )
        prefix_guild_data = guild_request.json()
        return prefix_guild_data

    def get_name_guild(self, name):
        """Get guild data by name."""
        guild_request = requests.get(
            f"https://api.wynncraft.com/v3/guild/{name}", 
            headers=WYNN_AUTH_HEADER
        )
        name_guild_data = guild_request.json()
        return name_guild_data

    def get_guild_members(self, user_input):
        """Get all guild members."""
        guild_data = self.get_guild_data(user_input)
        all_players = []
        guild_members = guild_data["members"]
        ranks = ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]
        for rank in ranks:
            for player in guild_members[rank]:
                all_players.append(player)
        return all_players

    def get_guild_member_contribution(self, user_input):
        """Get member contributions."""
        guild_data = self.get_guild_data(user_input)
        members_contribution = {}
        guild_members = guild_data["members"]
        ranks = ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]
        for rank in ranks:
            for player in guild_members[rank]:
                guild_rank = guild_members[rank]
                members_contribution[player] = guild_rank[player]["contributed"]
        return members_contribution

    def guild_list(self):
        """Get list of all guilds."""
        guild_request = requests.get(
            "https://api.wynncraft.com/v3/guild/list/guild", 
            headers=WYNN_AUTH_HEADER
        )
        all_guilds = guild_request.json()
        return all_guilds

    def get_guild_data(self, user_input):
        """Get guild data by prefix or name."""
        try:
            guild_data = self.get_prefix_guild(user_input)
        except Exception as error:
            print(f"Guild prefix match error: {error}")
            try:
                guild_data = self.get_name_guild(user_input)
            except Exception as error:
                print(f"Guild name match error: {error}")
                return None
        return guild_data

    def check_guild(self, user_input):
        """Check if guild exists."""
        try:
            self.get_prefix_guild(user_input)
        except Exception as error:
            print(f"Guild prefix match error: {error}")
            try:
                self.get_name_guild(user_input)
            except Exception as error:
                print(f"Guild name match error: {error}")
                return "NOT_FOUND"
        return "GUILD_FOUND"


class Items:
    """v3 item wrapping - Synchronous"""

    def fetch(self, url):
        """Fetch data from URL."""
        response = requests.get(url, headers=WYNN_AUTH_HEADER)
        return response.json()

    def post(self, url, data=None):
        """POST data to URL."""
        response = requests.post(url, json=data, headers=WYNN_AUTH_HEADER)
        return response.json()

    def get_all_items(self):
        """Get all items from database."""
        api_url = "https://api.wynncraft.com/v3/item/database?fullResult"
        return self.fetch(api_url)

    def get_beta_items(self):
        """Get beta items from database."""
        api_url = "https://beta-api.wynncraft.com/v3/item/database?fullResult"
        return self.fetch(api_url)

    def get_metadata(self):
        """Get item metadata."""
        url = "https://api.wynncraft.com/v3/item/metadata"
        return self.fetch(url)

    def item_query(self, data=None):
        """Query items with search parameters."""
        api_url = "https://api.wynncraft.com/v3/item/search?fullResult"
        return self.post(api_url, data)

