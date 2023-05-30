"""
Author: RawFish
Github Repository: https://github.com/RawFish69/Nori
License: AGPL-3.0
"""
import requests
import json
import time


class WynncraftGuildScraper:
    def __init__(self):
        self.guild_list_api_url = 'https://api.wynncraft.com/public_api.php?action=guildList'
        self.guild_prefixes = []

    def scrape_guilds(self):
        response = requests.get(self.guild_list_api_url)
        guild_list = response.json()['guilds']
        total_guilds = len(guild_list)
        print(f"Total guilds: {total_guilds}")
        for i, guild in enumerate(guild_list):
            guild_api_url = f'https://api.wynncraft.com/public_api.php?action=guildStats&command={guild}'
            response = requests.get(guild_api_url)
            guild_info = response.json()
            self.guild_prefixes.append({
                'name': guild,
                'prefix': guild_info['prefix']
            })
            print(f"{guild} [{guild_info['prefix']}] - {i+1}/{total_guilds}")
            if (i+1) % 100 == 0:
                self.update_json_file()
            time.sleep(1)
        self.update_json_file()
        print("All guilds fetched successfully")

    def update_json_file(self):
        with open('guild_prefixes.json', 'w') as file:
            json.dump({'guild_list': self.guild_prefixes}, file)


if __name__ == "__main__":
    scraper = WynncraftGuildScraper()
    scraper.scrape_guilds()
