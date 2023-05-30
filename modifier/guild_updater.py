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
        # Send GET request to the Wynncraft API to get guild list
        response = requests.get(self.guild_list_api_url)
        guild_list = response.json()['guilds']

        # Iterate over the guilds
        for guild in guild_list:
            # Build the URL for the API request for this guild
            guild_api_url = f'https://api.wynncraft.com/public_api.php?action=guildStats&command={guild}'

            # Send GET request to the Wynncraft API to get guild info
            response = requests.get(guild_api_url)
            guild_info = response.json()

            # Get the guild prefix and add it to the list
            self.guild_prefixes.append({
                'name': guild,
                'prefix': guild_info['prefix']
            })
            print(guild, guild_info['prefix'])

            # Pause for 1 second to stay below the rate limit
            time.sleep(1)

        # Save the guild names and prefixes to a JSON file
        with open('guilds.json', 'w') as file:
            json.dump({'guild_list': self.guild_prefixes}, file)


if __name__ == "__main__":
    scraper = WynncraftGuildScraper()
    scraper.scrape_guilds()
