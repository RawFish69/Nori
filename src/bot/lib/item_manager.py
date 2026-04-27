"""
Author: RawFish
Description: Core item management and data handling functionality
"""

import json
from .item_wrapper import Items
from .item_db_compat import items_response_to_dict, looks_like_item_database


class ItemManager:
    """
    Manages the retrieval and storage of item data from Wynncraft APIs.
    Also provides basic name lookups.
    """

    def __init__(self):
        """Initialize the ItemManager."""
        self.item_map = {}
        self.items_path = ""

    def update_items(self, path: str) -> int:
        """
        Fetch all items from the main API (or fallback/beta API on error).
        Save them to a JSON file, and store the data internally in `self.item_map`.
        
        :param path: The path to the items.json file on disk.
        :return: The number of items updated (0 if error/failure).
        """
        self.items_path = path
        raw = Items().get_all_items_raw()
        if not looks_like_item_database(raw):
            print(f"Invalid item API response; refusing to overwrite {path}.")
            beta_raw = Items().get_beta_items_raw()
            if looks_like_item_database(beta_raw):
                print("Beta API Item DB valid, updating from beta fallback.")
                return self._save_item_data(beta_raw, path)
            return 0

        data, summary = items_response_to_dict(raw)
        if summary is not None:
            print(f"v3.7 array response converted: {summary['total']} keys, "
                  f"{len(summary['collisions'])} displayName collisions")

        if not looks_like_item_database(data):
            print(f"Normalized item data is invalid; refusing to overwrite {path}.")
            return 0

        return self._save_item_data(raw, path)

    def _save_item_data(self, data, path: str) -> int:
        """
        Saves the provided `data` into `path` as JSON.
        Updates `self.item_map` in memory.
        
        :param data: The parsed JSON data of items.
        :param path: The path to which the items JSON is saved.
        :return: Number of items saved, 0 on error.
        """
        try:
            if not looks_like_item_database(data):
                print(f"Refusing to save invalid item database to {path}.")
                return 0
            item_map, _ = items_response_to_dict(data)
            if not looks_like_item_database(item_map):
                print(f"Refusing to save invalid normalized item map from {path}.")
                return 0
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=3)
            self.item_map = item_map  # Store runtime lookup map in memory.
            print(f"{len(item_map)} items updated")
            return len(item_map)
        except Exception as error:
            print(f"File update error: {error}")
            return 0

    def load_items_from_file(self, path: str):
        """
        Manually load items from a JSON file into memory. 
        Useful if you already have an items.json and don't need an API call.
        
        :param path: Path to the JSON file on disk.
        """
        try:
            self.items_path = path
            with open(path, "r", encoding="utf-8") as file:
                self.item_map, _ = items_response_to_dict(json.load(file))
        except Exception as error:
            print(f"Error loading items from file: {error}")

    def get_item_name(self, name: str) -> str:
        """
        Return the item name (properly cased) if found in the item database.
        
        :param name: The user-provided item name to match (case-insensitive).
        :return: Exact matching name in the DB, or None if not found.
        """
        if not self.item_map:
            print("Item map is empty; ensure items are loaded/updated.")
            return None

        for item_key in self.item_map:
            if name.lower() == item_key.lower():
                return item_key
        return None
