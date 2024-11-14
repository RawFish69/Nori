
import aiohttp
import asyncio

class AsyncPlayer:
    """Async wrapper for Wynncraft Player"""

    async def get_player_main(self, ign):
        async with aiohttp.ClientSession() as session:
            api_url = f"https://api.wynncraft.com/v3/player/{ign}"
            async with session.get(api_url) as response:
                return await response.json()

    async def get_player_full(self, ign):
        async with aiohttp.ClientSession() as session:
            api_url = f"https://api.wynncraft.com/v3/player/{ign}?fullResult=True"
            async with session.get(api_url) as response:
                return await response.json()

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
        return data["globalData"]["killedMobs"]

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
            async with session.get(f"https://api.wynncraft.com/v3/guild/prefix/{prefix}") as response:
                return await response.json()

    async def get_name_guild(self, name):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.wynncraft.com/v3/guild/{name}") as response:
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
            async with session.get("https://api.wynncraft.com/v3/guild/list/guild") as response:
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

    async def fetch(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

    async def post(self, url, data=None):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                return await response.json()

    async def get_all_items(self):
        api_url = "https://api.wynncraft.com/v3/item/database?fullResult=True"
        return await self.fetch(api_url)

    async def get_beta_items(self):
        api_url = "https://beta-api.wynncraft.com/v3/item/database?fullResult=True"
        return await self.fetch(api_url)

    async def get_metadata(self):
        url = "https://api.wynncraft.com/v3/item/metadata"
        return await self.fetch(url)

    async def item_query(self, data=None):
        api_url = "https://api.wynncraft.com/v3/item/search?fullResult=True"
        return await self.post(api_url, data)