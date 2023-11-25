"""
Name: Wrapper for Wynncraft API v3
Author: RawFish
Github: https://github.com/RawFish69
"""
import json
import request
import aiohttp

class Player:
    async def fetch(self, session, url):
        async with session.get(url) as response:
            response_json = await response.json()
            return response_json

    async def get_online_players(self, session):
        api_url = "https://api.wynncraft.com/v3/player"
        return await self.fetch(session, api_url)

    async def get_player_main(self, session, ign):
        api_url = f"https://api.wynncraft.com/v3/player/{ign}"
        return await self.fetch(session, api_url)

    async def get_player_full(self, session, ign):
        api_url = f"https://api.wynncraft.com/v3/player/{ign}?fullResult=True"
        return await self.fetch(session, api_url)

    async def player_uuid(self, session, ign):
        player_main = await self.get_player_main(session, ign)
        return player_main["uuid"]

    async def online_status(self, session, ign):
        player_main = await self.get_player_main(session, ign)
        return player_main["online"]

    async def online_server(self, session, ign):
        player_main = await self.get_player_main(session, ign)
        return player_main["server"]

    async def war_global(self, session, ign):
        player_main = await self.get_player_main(session, ign)
        return player_main["globalData"]["wars"]

    async def mobs_global(self, session, ign):
        player_main = await self.get_player_main(session, ign)
        return player_main["globalData"]["killedMobs"]

    async def chest_global(self, session, ign):
        player_main = await self.get_player_main(session, ign)
        return player_main["globalData"]["chestsFound"]

    async def raid_global(self, session, ign):
        player_main = await self.get_player_main(session, ign)
        raid_data = player_main["globalData"]["raids"]
        return raid_data

    async def dungeon_global(self, session, ign):
        player_main = await self.get_player_main(session, ign)
        return player_main["globalData"]["dungeons"]["total"]


class Guild:
    async def fetch(self, session, url):
        async with session.get(url) as response:
            response_json = await response.json()
            return response_json

    async def get_prefix_guild(self, session, prefix):
        url = f"https://api.wynncraft.com/v3/guild/prefix/{prefix}"
        return await self.fetch(session, url)

    async def get_name_guild(self, session, name):
        url = f"https://api.wynncraft.com/v3/guild/{name}"
        return await self.fetch(session, url)

    async def get_guild_list(self, session):
        url = "https://api.wynncraft.com/v3/guild/list/guild"
        return await self.fetch(session, url)

    async def get_guild_members(self, session, user_input):
        guild_data = await self.get_guild_data(session, user_input)
        all_players = []
        guild_members = guild_data["members"]
        ranks = ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]
        for rank in ranks:
            for player in guild_members[rank]:
                all_players.append(player)
        return all_players

    async def get_guild_member_contribution(self, session, user_input):
        guild_data = await self.get_guild_data(session, user_input)
        members_contribution = {}
        guild_members = guild_data["members"]
        ranks = ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]
        for rank in ranks:
            for player in guild_members[rank]:
                guild_rank = guild_members[rank]
                members_contribution[player] = guild_rank[player]["contributed"]
        return members_contribution

    async def get_guild_data(self, session, user_input):
        try:
            guild_data = await self.get_prefix_guild(session, user_input)
        except Exception as error:
            print(f"Guild prefix match error: {error}")
            try:
                guild_data = await self.get_name_guild(session, user_input)
            except Exception as error:
                print(f"Guild name match error: {error}")
                return
        return guild_data

    async def check_guild(self, session, user_input):
        try:
            await self.get_prefix_guild(session, user_input)
        except Exception as error:
            print(f"Guild prefix match error: {error}")
            try:
                await self.get_name_guild(session, user_input)
            except Exception as error:
                print(f"Guild name match error: {error}")
                return "NOT_FOUND"
        return "GUILD_FOUND"
