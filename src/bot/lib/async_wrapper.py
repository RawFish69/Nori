import aiohttp
import asyncio
from lib.item_db_compat import items_response_to_dict
from lib.config import WYNN_AUTH_HEADER

class AsyncPlayer:
    """Async wrapper for Wynncraft Player"""

    async def _resolve_latest_player(self, session, response, use_full):
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
        suffix = "?fullResult" if use_full else ""
        candidates = []
        for uuid in objects:
            try:
                async with session.get(
                    f"https://api.wynncraft.com/v3/player/{uuid}{suffix}",
                    headers=WYNN_AUTH_HEADER,
                ) as per_resp:
                    per = await per_resp.json()
            except Exception:
                continue
            if isinstance(per, dict) and "uuid" in per:
                candidates.append(per)
        if not candidates:
            return response
        candidates.sort(key=lambda p: p.get("lastJoin") or "", reverse=True)
        return candidates[0]

    async def get_player_main(self, ign):
        async with aiohttp.ClientSession() as session:
            api_url = f"https://api.wynncraft.com/v3/player/{ign}"
            async with session.get(api_url, headers=WYNN_AUTH_HEADER) as response:
                data = await response.json()
            return await self._resolve_latest_player(session, data, use_full=False)

    async def get_player_full(self, ign):
        async with aiohttp.ClientSession() as session:
            api_url = f"https://api.wynncraft.com/v3/player/{ign}?fullResult"
            async with session.get(api_url, headers=WYNN_AUTH_HEADER) as response:
                data = await response.json()
            return await self._resolve_latest_player(session, data, use_full=True)

    async def player_uuid(self, ign):
        data = await self.get_player_main(ign)
        return data["uuid"]

    async def online_status(self, ign):
        data = await self.get_player_main(ign)
        return data["online"]

    async def online_server(self, ign):
        data = await self.get_player_main(ign)
        return data["server"]

    async def war_global(self, ign):
        data = await self.get_player_main(ign)
        return data["globalData"]["wars"]

    async def mobs_global(self, ign):
        data = await self.get_player_main(ign)
        return data["globalData"]["mobsKilled"]

    async def chest_global(self, ign):
        data = await self.get_player_main(ign)
        return data["globalData"]["chestsFound"]

    async def raid_global(self, ign):
        data = await self.get_player_main(ign)
        player_data = data["globalData"]["raids"]
        raid_data = {"total": player_data["total"]}
        for raid in player_data["list"]:
            raid_data[raid] = player_data["list"][raid]
        return raid_data

    async def dungeon_global(self, ign):
        data = await self.get_player_main(ign)
        return data["globalData"]["dungeons"]["total"]


class AsyncGuild:
    """Async wrapper for Wynncraft Guild"""

    async def get_prefix_guild(self, prefix):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.wynncraft.com/v3/guild/prefix/{prefix}", headers=WYNN_AUTH_HEADER) as response:
                return await response.json()

    async def get_name_guild(self, name):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.wynncraft.com/v3/guild/{name}", headers=WYNN_AUTH_HEADER) as response:
                return await response.json()

    async def get_guild_members(self, user_input):
        guild_data = await self.get_guild_data(user_input)
        all_players = []
        guild_members = guild_data["members"]
        ranks = ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]
        for rank in ranks:
            for player in guild_members[rank]:
                all_players.append(player)
        return all_players

    async def get_guild_member_contribution(self, user_input):
        guild_data = await self.get_guild_data(user_input)
        members_contribution = {}
        guild_members = guild_data["members"]
        ranks = ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]
        for rank in ranks:
            for player in guild_members[rank]:
                guild_rank = guild_members[rank]
                members_contribution[player] = guild_rank[player]["contributed"]
        return members_contribution

    async def guild_list(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.wynncraft.com/v3/guild/list/guild", headers=WYNN_AUTH_HEADER) as response:
                return await response.json()

    async def get_guild_data(self, user_input):
        try:
            return await self.get_prefix_guild(user_input)
        except Exception as error:
            print(f"Guild prefix match error: {error}")
            try:
                return await self.get_name_guild(user_input)
            except Exception as error:
                print(f"Guild name match error: {error}")
                return None

    async def check_guild(self, user_input):
        try:
            await self.get_prefix_guild(user_input)
        except Exception as error:
            print(f"Guild prefix match error: {error}")
            try:
                await self.get_name_guild(user_input)
            except Exception as error:
                print(f"Guild name match error: {error}")
                return "NOT_FOUND"
        return "GUILD_FOUND"


class AsyncItems:
    """Async v3 item wrapping"""

    async def fetch(self, url, headers=None):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers if headers is not None else WYNN_AUTH_HEADER) as response:
                return await response.json(content_type=None)

    async def post(self, url, data=None):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=WYNN_AUTH_HEADER) as response:
                return await response.json(content_type=None)

    async def get_all_items(self):
        api_url = "https://api.wynncraft.com/v3/item/database?fullResult"
        raw = await self.fetch(api_url)
        result, _ = items_response_to_dict(raw)
        return result

    async def get_beta_items(self):
        """Beta endpoint requires no auth header."""
        api_url = "https://beta-api.wynncraft.com/v3/item/database?fullResult"
        try:
            raw = await self.fetch(api_url, headers={})
            if not isinstance(raw, (dict, list)):
                return None
            result, _ = items_response_to_dict(raw)
            return result
        except Exception as error:
            print(f"Beta item fetch error: {error}")
            return None

    async def get_metadata(self):
        url = "https://api.wynncraft.com/v3/item/metadata"
        return await self.fetch(url)

    async def item_query(self, data=None):
        api_url = "https://api.wynncraft.com/v3/item/search?fullResult"
        raw = await self.post(api_url, data)
        result, _ = items_response_to_dict(raw)
        return result