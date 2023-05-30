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

        # Iterate over the guilds
        for guild in guild_list:
            guild_api_url = f'https://api.wynncraft.com/public_api.php?action=guildStats&command={guild}'
            response = requests.get(guild_api_url)
            guild_info = response.json()
            self.guild_prefixes.append({
                'name': guild,
                'prefix': guild_info['prefix']
            })
            print(guild, guild_info['prefix'])
            time.sleep(1)
        with open('guilds.json', 'w') as file:
            json.dump({'guild_list': self.guild_prefixes}, file)


if __name__ == "__main__":
    scraper = WynncraftGuildScraper()
    scraper.scrape_guilds()
