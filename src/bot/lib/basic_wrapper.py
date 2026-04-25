import requests
from lib.item_db_compat import items_response_to_dict

class Player:
    """Wrapper for Wynncraft Player"""

    def _resolve_latest_player(self, response, use_full):
        # Wynn returns HTTP 300 MultipleObjectsReturned when an IGN maps to
        # more than one historical UUID (e.g. "Colena"). Shape:
        #   {"error": "MultipleObjectsReturned", "code": 300,
        #    "objects": {"<uuid>": {"username": ..., "rank": ...}, ...}}
        # Sub-objects lack lastJoin, so we re-fetch each UUID and keep the
        # one with the latest lastJoin (ISO-8601 strings sort lexicographically).
        if not isinstance(response, dict):
            return response
        objects = response.get("objects")
        if "uuid" in response or not isinstance(objects, dict) or not objects:
            return response
        suffix = "?fullResult=True" if use_full else ""
        candidates = []
        for uuid in objects:
            try:
                per = requests.get(
                    f"https://api.wynncraft.com/v3/player/{uuid}{suffix}"
                ).json()
            except Exception:
                continue
            if isinstance(per, dict) and "uuid" in per:
                candidates.append(per)
        if not candidates:
            return response
        candidates.sort(key=lambda p: p.get("lastJoin") or "", reverse=True)
        return candidates[0]

    def get_player_main(self, ign):
        api_url = f"https://api.wynncraft.com/v3/player/{ign}"
        stat_request = requests.get(api_url)
        player_data = stat_request.json()
        return self._resolve_latest_player(player_data, use_full=False)

    def get_player_full(self, ign):
        api_url = f"https://api.wynncraft.com/v3/player/{ign}?fullResult=True"
        stat_request = requests.get(api_url)
        player_data = stat_request.json()
        return self._resolve_latest_player(player_data, use_full=True)

    def player_uuid(self, ign):
        return Player.get_player_main(self, ign)["uuid"]

    def online_status(self, ign):
        return Player.get_player_main(self, ign)["online"]

    def online_server(self, ign):
        return Player.get_player_main(self, ign)["server"]

    def war_global(self, ign):
        return Player.get_player_main(self, ign)["globalData"]["wars"]

    def mobs_global(self, ign):
        return Player.get_player_main(self, ign)["globalData"]["mobsKilled"]

    def chest_global(self, ign):
        return Player.get_player_main(self, ign)["globalData"]["chestsFound"]

    def raid_global(self, ign):
        player_data = Player.get_player_main(self, ign)["globalData"]["raids"]
        raid_data = {"total": player_data["total"]}
        for raid in player_data["list"]:
            raid_data[raid] = player_data["list"][raid]
        return raid_data

    def dungeon_global(self, ign):
        player_data = Player.get_player_main(self, ign)["globalData"]["dungeons"]
        dungeon_total = player_data["total"]
        return dungeon_total


class Guild:
    """Wrapper for Wynncraft Guild"""

    def get_prefix_guild(self, prefix):
        guild_request = requests.get(f"https://api.wynncraft.com/v3/guild/prefix/{prefix}")
        prefix_guild_data = guild_request.json()
        # guild_json = json.dumps(prefix_guild_data, indent=3)
        # print(guild_json)
        return prefix_guild_data

    def get_name_guild(self, name):
        guild_request = requests.get(f"https://api.wynncraft.com/v3/guild/{name}")
        name_guild_data = guild_request.json()
        return name_guild_data

    def get_guild_members(self, user_input):
        guild_data = Guild.get_guild_data(self, user_input)
        all_players = []
        guild_members = guild_data["members"]
        ranks = ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]
        for rank in ranks:
            for player in guild_members[rank]:
                all_players.append(player)
        return all_players

    def get_guild_member_contribution(self, user_input):
        guild_data = Guild.get_guild_data(self, user_input)
        members_contribution = {}
        guild_members = guild_data["members"]
        ranks = ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]
        for rank in ranks:
            for player in guild_members[rank]:
                guild_rank = guild_members[rank]
                members_contribution[player] = guild_rank[player]["contributed"]
        return members_contribution

    def guild_list(self):
        guild_request = requests.get(f"https://api.wynncraft.com/v3/guild/list/guild")
        all_guilds = guild_request.json()
        return all_guilds

    def get_guild_data(self, user_input):
        try:
            guild_data = Guild.get_prefix_guild(self, user_input)
        except Exception as error:
            print(f"Guild prefix match error: {error}")
            try:
                guild_data = Guild.get_name_guild(self, user_input)
            except Exception as error:
                print(f"Guild name match error: {error}")
                return
        return guild_data

    def check_guild(self, user_input):
        try:
            Guild.get_prefix_guild(self, user_input)
        except Exception as error:
            print(f"Guild prefix match error: {error}")
            try:
                Guild.get_name_guild(self, user_input)
            except Exception as error:
                print(f"Guild name match error: {error}")
                return "NOT_FOUND"
        return "GUILD_FOUND"


class Items:
    """v3 item wrapping - Synchronous"""

    def fetch(self, url, headers=None):
        response = requests.get(url, headers=headers)
        return response.json()

    def post(self, url, data=None):
        response = requests.post(url, json=data)
        return response.json()

    def get_all_items(self):
        api_url = "https://api.wynncraft.com/v3/item/database?fullResult=True"
        raw = self.fetch(api_url)
        result, _ = items_response_to_dict(raw)
        return result

    def get_beta_items(self):
        """Beta endpoint requires no auth header."""
        api_url = "https://beta-api.wynncraft.com/v3/item/database?fullResult=True"
        try:
            raw = self.fetch(api_url, headers={})
            if not isinstance(raw, (dict, list)):
                return None
            result, _ = items_response_to_dict(raw)
            return result
        except Exception as error:
            print(f"Beta item fetch error: {error}")
            return None

    def get_metadata(self):
        url = "https://api.wynncraft.com/v3/item/metadata"
        return self.fetch(url)

    def item_query(self, data=None):
        api_url = "https://api.wynncraft.com/v3/item/search?fullResult=True"
        raw = self.post(api_url, data)
        result, _ = items_response_to_dict(raw)
        return result