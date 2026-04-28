"""
Author: RawFish
Description: Quick item save/search with v3 item database integration
API Documentation: https://documentation.wynncraft.com/docs/
Update item db: python item_wrapper.py update-item [file_directory]
Item search: python item_wrapper.py search -keyword [War] -itemType [mythic] ...
"""

import requests
import json
import argparse
from typing import Any, Dict, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.item_db_compat import items_response_to_dict, looks_like_item_database
from lib.config import WYNN_AUTH_HEADER


class Items:
    """v3 item wrapping - Synchronous"""

    def __init__(self):
        self.base_url = "https://api.wynncraft.com/v3"
        self.headers = {"User-Agent": "NoriBot/2.1.0 (+https://nori.fish)"}

    def fetch(self, url, headers=None):
        request_headers = self.headers.copy()
        if headers is None and "api.wynncraft.com" in url:
            request_headers.update(WYNN_AUTH_HEADER)
        elif headers:
            request_headers.update(headers)
        response = requests.get(url, headers=request_headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def post(self, url, data=None):
        request_headers = self.headers.copy()
        if "api.wynncraft.com" in url:
            request_headers.update(WYNN_AUTH_HEADER)
        response = requests.post(url, json=data, headers=request_headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_all_items(self) -> Optional[Dict]:
        """Fetch all items from main API, normalised to displayName-keyed dict."""
        try:
            raw = self.get_all_items_raw()
            result, _ = items_response_to_dict(raw)
            return result
        except Exception as error:
            print(f"API error: {error}")
            return None

    def get_all_items_raw(self) -> Optional[Any]:
        """Fetch all items from main API in the upstream native shape."""
        try:
            raw = self.fetch(f"{self.base_url}/item/database?fullResult")
            return raw if isinstance(raw, (dict, list)) else None
        except Exception as error:
            print(f"API error: {error}")
            return None

    def get_beta_items(self) -> Optional[Dict]:
        """Fetch items from beta API (no auth required)."""
        try:
            raw = self.get_beta_items_raw()
            result, _ = items_response_to_dict(raw)
            return result
        except Exception as error:
            print(f"Beta API error: {error}")
            return None

    def get_beta_items_raw(self) -> Optional[Any]:
        """Fetch beta items in the upstream native shape."""
        try:
            raw = self.fetch(
                "https://beta-api.wynncraft.com/v3/item/database?fullResult",
                headers={}
            )
            return raw if isinstance(raw, (dict, list)) else None
        except Exception as error:
            print(f"Beta API error: {error}")
            return None

    def get_metadata(self):
        url = "https://api.wynncraft.com/v3/item/metadata"
        return self.fetch(url)

    def item_query(self, data=None):
        api_url = "https://api.wynncraft.com/v3/item/search?fullResult"
        raw = self.post(api_url, data)
        result, _ = items_response_to_dict(raw)
        return result


def update_items(file_path):
    data = Items().get_all_items_raw()
    if data is None or not looks_like_item_database(data):
        print("Failed to fetch items")
        return
    update_file(data, file_path)
    normalized, _ = items_response_to_dict(data)
    print(f"{len(normalized)} items updated")


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


if __name__ == "__main__":
    main()
