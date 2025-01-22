"""
    The script fetches data from the Wynncraft API and builds local cache files.
    The data can be used for leaderboards, guild statistics, and player statistics.
    It is designed to run locally as testing and development purposes.
    I do not recommend running this script on a server or in a production environment.
"""


import os
import json
import time
import asyncio
import aiohttp
import matplotlib.pyplot as plt
import numpy as np
import psutil
from datetime import datetime, timedelta, timezone
from heapq import heappush, heapreplace, nlargest
from typing import Any, Dict, List

class DataBuilder:
    def __init__(self, data_path: str = "/path/to/data"):
        self.data_path = data_path
        self.cst = timezone(timedelta(hours=-5))
        self.time_now = datetime.now(self.cst)
        self.current_datetime = self.time_now.strftime("%Y-%m-%d %H:%M:%S")
        self.current_date = self.time_now.strftime("%Y-%m-%d")
        self.current_time = self.time_now.strftime("%H:%M:%S")

    @staticmethod
    async def universal_fetch(session: aiohttp.ClientSession, url: str, retries: int = 2, delay: float = 0.5) -> Dict[str, Any]:
        for attempt in range(retries + 1):
            try:
                async with session.get(url) as response:
                    return await response.json()
            except Exception as e:
                if attempt == retries:
                    print(f"Failed to fetch {url}: {e}")
                    return {}
                await asyncio.sleep(delay)

    class Player:
        def __init__(self, fetch_func):
            self.fetch_func = fetch_func

        async def get_online_players(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
            return await self.fetch_func(session, "https://api.wynncraft.com/v3/player")

        async def get_online_beta(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
            return await self.fetch_func(session, "https://beta-api.wynncraft.com/v3/player")

        async def get_player_main(self, session: aiohttp.ClientSession, ign: str) -> Dict[str, Any]:
            return await self.fetch_func(session, f"https://api.wynncraft.com/v3/player/{ign}")

        async def get_player_full(self, session: aiohttp.ClientSession, ign: str) -> Dict[str, Any]:
            return await self.fetch_func(session, f"https://api.wynncraft.com/v3/player/{ign}?fullResult=True")

    class Guild:
        def __init__(self, fetch_func):
            self.fetch_func = fetch_func

        async def get_prefix_guild(self, session: aiohttp.ClientSession, prefix: str) -> Dict[str, Any]:
            return await self.fetch_func(session, f"https://api.wynncraft.com/v3/guild/prefix/{prefix}")

        async def get_name_guild(self, session: aiohttp.ClientSession, name: str) -> Dict[str, Any]:
            return await self.fetch_func(session, f"https://api.wynncraft.com/v3/guild/{name}")

        async def get_guild_list(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
            return await self.fetch_func(session, "https://api.wynncraft.com/v3/guild/list/guild")

    class Leaderboard:
        def __init__(self, fetch_func):
            self.fetch_func = fetch_func

        async def get_raid_leaderboard(self, session: aiohttp.ClientSession, raid: str, limit: int) -> Dict[str, Any]:
            return await self.fetch_func(session, f"https://api.wynncraft.com/v3/leaderboards/{raid}?resultLimit={limit}")

    async def ensure_data_structure(self) -> None:
        files_needed = [
            ("player_data.json", {"data": {}}),
            ("player_leaderboard.json", {"ranking": {}, "timestamp": 0}),
            ("guild_data.json", {}),
            ("leaderboard_in_guild.json", {}),
            ("ign_from_discord.json", {"ign": []}),
            ("online_activity.json", {})
        ]
        os.makedirs(self.data_path, exist_ok=True)
        for filename, default_content in files_needed:
            file_path = os.path.join(self.data_path, filename)
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    json.dump(default_content, f, indent=3)

    async def read_player_data(self) -> Dict[str, Any]:
        path = os.path.join(self.data_path, "player_data.json")
        with open(path, "r") as file:
            return json.load(file)

    async def load_online_activity(self) -> Dict[str, Any]:
        path = os.path.join(self.data_path, "online_activity.json")
        with open(path, "r") as f:
            return json.load(f)

    async def update_player_stats(self, session: aiohttp.ClientSession, ign: str) -> Dict[str, Any]:
        try:
            player_stats = await self.universal_fetch(session, f"https://api.wynncraft.com/v3/player/{ign}")
            _ = player_stats["globalData"]
        except:
            return {}
        username = player_stats["username"]
        global_data = player_stats["globalData"]
        raids = global_data["raids"]
        return {
            "username": username,
            "raids_total": raids["total"] if raids["total"] else 0,
            "tna": raids["list"].get("The Nameless Anomaly", 0),
            "tcc": raids["list"].get("The Canyon Colossus", 0),
            "nol": raids["list"].get("Orphion's Nexus of Light", 0),
            "nog": raids["list"].get("Nest of the Grootslangs", 0),
            "dungeons": global_data["dungeons"]["total"] if global_data["dungeons"]["total"] else 0,
            "chests": global_data["chestsFound"] if global_data["chestsFound"] else 0,
            "mobs": global_data["killedMobs"] if global_data["killedMobs"] else 0,
            "wars": global_data["wars"] if global_data["wars"] else 0,
            "playtime": player_stats["playtime"] if player_stats["playtime"] else 0,
            "pvp_kills": global_data["pvp"]["kills"] if global_data["pvp"]["kills"] else 0,
            "quests": global_data["completedQuests"] if global_data["completedQuests"] else 0,
            "levels": global_data["totalLevel"] if global_data["totalLevel"] else 0
        }

    async def build_online_ign_list(self, online_players: List[str], player_data: Dict[str, Any]) -> None:
        online_log = await self.load_online_activity()
        async with aiohttp.ClientSession() as session:
            p = self.Player(self.universal_fetch)
            online_data = await self.universal_fetch(session, "https://api.wynncraft.com/v3/player")
            if online_data.get("total", 0) < 50:
                online_data = await p.get_online_beta(session)
            player_names = online_data["players"]
            new_players = 0
            for ign in player_names:
                if ign not in player_data["data"]:
                    player_data["data"][ign] = {}
                    new_players += 1
                try:
                    stats = await self.update_player_stats(session, ign)
                    player_data["data"][ign] = stats
                    online_players.append(ign)
                except:
                    await asyncio.sleep(0.5)
                    try:
                        stats = await self.update_player_stats(session, ign)
                        player_data["data"][ign] = stats
                    except:
                        pass
                await asyncio.sleep(0.25)
            if self.current_date not in online_log:
                online_log[self.current_date] = {}
            online_log[self.current_date][self.current_time] = {
                "online": len(player_names),
                "new": new_players
            }
            with open(os.path.join(self.data_path, "online_activity.json"), "w") as f:
                json.dump(online_log, f, indent=3)
        with open(os.path.join(self.data_path, "player_data.json"), "w") as file:
            json.dump(player_data, file)

    async def scan_official_leaderboard(self, player_data: Dict[str, Any]) -> None:
        l = self.Leaderboard(self.universal_fetch)
        unique_players = []
        try:
            async with aiohttp.ClientSession() as session:
                tna_lb = await l.get_raid_leaderboard(session, raid="tnaCompletion", limit=100)
                for val in tna_lb.values():
                    if val["name"] not in unique_players:
                        unique_players.append(val["name"])
                tcc_lb = await l.get_raid_leaderboard(session, raid="tccCompletion", limit=100)
                for val in tcc_lb.values():
                    if val["name"] not in unique_players:
                        unique_players.append(val["name"])
                nol_lb = await l.get_raid_leaderboard(session, raid="nolCompletion", limit=100)
                for val in nol_lb.values():
                    if val["name"] not in unique_players:
                        unique_players.append(val["name"])
                nog_lb = await l.get_raid_leaderboard(session, raid="nogCompletion", limit=100)
                for val in nog_lb.values():
                    if val["name"] not in unique_players:
                        unique_players.append(val["name"])
                for ign in unique_players:
                    stats = await self.update_player_stats(session, ign)
                    if "username" in stats:
                        username = stats["username"]
                        player_data["data"][username] = stats
                    await asyncio.sleep(0.25)
        except Exception as error:
            print(f"Failed to fetch official leaderboard: {error}")
        with open(os.path.join(self.data_path, "player_data.json"), "w") as file:
            json.dump(player_data, file)

    async def update_guild_data(self, player_data: Dict[str, Any]) -> None:
        limit = 500
        guild_data = {}
        leaderboard_data = {}
        async with aiohttp.ClientSession() as session:
            try:
                resp = await session.get(f"https://api.wynncraft.com/v3/leaderboards/guildLevel?resultLimit={limit}")
                lb_json = await resp.json()
                if not isinstance(lb_json, dict):
                    return
                guild_list = [g["prefix"] for g in lb_json.values() if isinstance(g, dict) and "prefix" in g]
            except Exception as e:
                print(f"Error fetching guild leaderboard data: {e}")
                return
            categories = ["raids_total","tna","tcc","nol","nog","dungeons","chests","mobs","playtime","quests","levels"]
            ranks = ["owner","chief","strategist","captain","recruiter","recruit"]
            for prefix in guild_list:
                guild_data[prefix] = {c: 0 for c in categories}
                try:
                    g_res = await session.get(f"https://api.wynncraft.com/v3/guild/prefix/{prefix}")
                    g_json = await g_res.json()
                    guild_data[prefix]["name"] = g_json["name"]
                    created_time = datetime.strptime(g_json["created"], '%Y-%m-%dT%H:%M:%S.%fZ')
                    guild_data[prefix]["created_at"] = str(created_time.date())
                    guild_data[prefix]["members"] = g_json["members"]["total"]
                    if g_json["seasonRanks"]:
                        sr_data = list(g_json["seasonRanks"].items())
                        guild_data[prefix]["sr"] = sr_data[-1][1]["rating"]
                    else:
                        guild_data[prefix]["sr"] = 0
                    g_leaderboards = {c: [] for c in categories}
                    for r in ranks:
                        for ign in g_json["members"][r]:
                            if ign in player_data["data"]:
                                for c in categories:
                                    val = int(player_data["data"][ign].get(c, 0))
                                    guild_data[prefix][c] += val
                                    g_leaderboards[c].append({ign: val})
                    for c in categories:
                        g_leaderboards[c] = sorted(g_leaderboards[c], key=lambda x: list(x.values())[0], reverse=True)
                    leaderboard_data[prefix] = g_leaderboards
                    await asyncio.sleep(0.5)
                except Exception:
                    pass
        with open(os.path.join(self.data_path, "guild_data.json"), "w") as f:
            json.dump(guild_data, f)
        with open(os.path.join(self.data_path, "leaderboard_in_guild.json"), "w") as f:
            json.dump(leaderboard_data, f)

    def print_memory_usage(self) -> None:
        process = psutil.Process()
        mem_info = process.memory_info()
        print(f"Memory used: {mem_info.rss / 1024 ** 2:.2f} MB")

    def update_rankings(self) -> None:
        data_path = os.path.join(self.data_path, "player_data.json")
        ranking_path = os.path.join(self.data_path, "player_leaderboard.json")
        rankings = {
            "raids_total": [], "tna": [], "tcc": [], "nol": [], "nog": [],
            "dungeons": [], "chests": [], "mobs": [], "wars": [], "playtime": [],
            "pvp_kills": [], "quests": [], "levels": []
        }
        def add_to_ranking(category: str, value: int, player: str):
            if len(rankings[category]) < 100:
                heappush(rankings[category], (value, player))
            else:
                if value > rankings[category][0][0]:
                    heapreplace(rankings[category], (value, player))
        with open(data_path, 'r') as file:
            data = json.load(file)
            for player, stats in data["data"].items():
                for category in rankings:
                    v = stats.get(category, 0)
                    add_to_ranking(category, int(v), player)
        for category in rankings:
            rankings[category] = nlargest(100, rankings[category])
            rankings[category] = [{p: v} for v, p in rankings[category]]
        timestamp = int(time.time())
        with open(ranking_path, 'w') as file:
            player_ranking = {"ranking": rankings, "timestamp": timestamp}
            json.dump(player_ranking, file)
        self.print_memory_usage()

    async def update_data(self) -> None:
        player_data = await self.read_player_data()
        online_players = []
        await self.build_online_ign_list(online_players, player_data)
        await self.scan_official_leaderboard(player_data)
        await self.update_guild_data(player_data)

    def run_all_operations(self) -> None:
        asyncio.run(self.ensure_data_structure())
        asyncio.run(self.update_data())
        self.update_rankings()

def main():
    builder = DataBuilder()
    builder.run_all_operations()

if __name__ == "__main__":
    main()
