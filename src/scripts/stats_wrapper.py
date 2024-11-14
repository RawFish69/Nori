import requests


class Guild:
    """Wrapper for Wynncraft Guild"""

    def get_prefix_guild(self, prefix):
        guild_request = requests.get(f"https://api.wynncraft.com/v3/guild/prefix/{prefix}")

        return guild_request.json()

    def get_name_guild(self, name):
        guild_request = requests.get(f"https://api.wynncraft.com/v3/guild/{name}")

        return guild_request.json()

    def get_guild_data(self, user_input):
        try:
            if len(user_input) <= 4:
                guild_data = self.get_prefix_guild(user_input)
            else:
                guild_data = self.get_name_guild(user_input)
        except Exception:
            guild_data = self.get_name_guild(user_input)
        return guild_data

class Player:
    """Wrapper for Wynncraft Player"""

    def get_player_main(self, ign):
        api_url = f"https://api.wynncraft.com/v3/player/{ign}"
        stat_request = requests.get(api_url)
        player_data = stat_request.json()
        return player_data

    def get_player_full(self, ign):
        api_url = f"https://api.wynncraft.com/v3/player/{ign}?fullResult=True"
        stat_request = requests.get(api_url)
        player_data = stat_request.json()
        return player_data
