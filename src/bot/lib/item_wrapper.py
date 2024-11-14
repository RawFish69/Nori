"""
Description: Quick item save/search with v3 item database
API Documentation: https://documentation.wynncraft.com/docs/
Update item db: python item_wrapper.py update-item [file_directory]
Item search: python item_wrapper.py search -keyword [War] -itemType [mythic] ...
"""

import requests
import json
import argparse


class Items:
    """v3 item wrapping - Synchronous"""

    def fetch(self, url):
        response = requests.get(url)
        return response.json()

    def post(self, url, data=None):
        response = requests.post(url, json=data)
        return response.json()

    def get_all_items(self):
        api_url = "https://api.wynncraft.com/v3/item/database?fullResult=True"
        return self.fetch(api_url)

    def get_metadata(self):
        url = "https://api.wynncraft.com/v3/item/metadata"
        return self.fetch(url)

    def item_query(self, data=None):
        api_url = "https://api.wynncraft.com/v3/item/search?fullResult=True"
        return self.post(api_url, data)


def update_items(file_path):
    data = Items().get_all_items()
    update_file(data, file_path)
    print(f"{len(data)} items updated")


def update_metadata(file_path):
    data = Items().get_metadata()
    update_file(data, file_path)
    print("Metadata updated")


def update_file(input, output):
    try:
        with open(output, "w") as file:
            json.dump(input, file, indent=3)
    except Exception as error:
        print(f"File update error: {error}")


def item_search_param(keyword=None, itemType=None, itemTier=None, atkSpeed=None, lvlRange=None, prof=None, ids=None, majorId=None):
    payload = {
        "query": [] if keyword is None else keyword,
        "type": [] if itemType is None else itemType,
        "tier": [] if itemTier is None else itemTier,
        "attackSpeed": [] if atkSpeed is None else atkSpeed,
        "levelRange": [] if lvlRange is None else lvlRange,
        "professions": [] if prof is None else prof,
        "identifications": [] if ids is None else ids,
        "majorIds": [] if majorId is None else majorId
    }
    try:
        response = Items().item_query(payload)
        print(json.dumps(response, indent=3))
        # Save the response as needed

    except requests.RequestException as error:
        print(f"Request error: {error}")


def main():
    parser = argparse.ArgumentParser(description='Wynncraft Item API Script')
    subparsers = parser.add_subparsers(dest='command', help='Pick your poison')
    update_items_parser = subparsers.add_parser('update-items', help='Update all items')
    update_items_parser.add_argument('file', help='File path for saving item json')
    update_metadata_parser = subparsers.add_parser('update-metadata', help='Update metadata')
    update_metadata_parser.add_argument('file', help='File path for saving metadata json')

    search_parser = subparsers.add_parser('search', help='Search for items with parameters')
    search_parser.add_argument('-keyword', type=str, default=None, help='Keyword for item search')
    search_parser.add_argument('-itemType', type=str, default=None, help='Item type: wand, bow, etc')
    search_parser.add_argument('-itemTier', type=str, default=None, help='Item tier: mythic, legendary, etc')
    search_parser.add_argument('-atkSpeed', type=str, default=None, help='Attack speed param')
    search_parser.add_argument('-lvlRange', nargs=2, type=int, default=None, help='Level range for: min, max')
    search_parser.add_argument('-prof', type=str, default=None, help='Professions (Ing)')
    search_parser.add_argument('-ids', type=str, default=None, help='Identifications field')
    search_parser.add_argument('-majorId', type=str, default=None, help='Major IDs')

    args = parser.parse_args()

    if args.command == 'update-items':
        update_items(args.file)
    elif args.command == 'update-metadata':
        update_metadata(args.file)
    elif args.command == 'search':
        item_search_param(
            keyword=args.keyword,
            itemType=args.itemType,
            itemTier=args.itemTier,
            atkSpeed=args.atkSpeed,
            lvlRange=args.lvlRange,
            prof=args.prof,
            ids=args.ids,
            majorId=args.majorId
        )


main()
