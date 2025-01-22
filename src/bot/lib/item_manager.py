"""
Author: RawFish
Description: Core item management and data handling functionality
"""

import json
from .item_wrapper import Items


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
        data = Items().get_all_items()
        if not data:
            print("Invalid API response")
            return 0

        # If API returned an error
        if "Error" in data:
            print(f"Error in item API response: {data['Error']}")
            beta_data = Items().get_beta_items()
            if beta_data and "Error" not in beta_data:
                print("Beta API Item DB Valid, updating")
                return self._save_item_data(beta_data, path)
            return 0

        # Check for rate limit
        if "message" in data and data["message"] == "API rate limit exceeded":
            print("Item Update - Exceeded API Rate limit") 
            return 0

        # Check for authentication/down
        if "detail" in data and data["detail"] == "Authentication credentials were not provided.":
            print("Error fetching item data, is it down?")
            return 0

        return self._save_item_data(data, path)

    def _save_item_data(self, data: dict, path: str) -> int:
        """
        Saves the provided `data` into `path` as JSON.
        Updates `self.item_map` in memory.
        
        :param data: The parsed JSON data of items.
        :param path: The path to which the items JSON is saved.
        :return: Number of items saved, 0 on error.
        """
        try:
            with open(path, "w") as file:
                json.dump(data, file, indent=3)
            self.item_map = data  # Store in memory
            print(f"{len(data)} items updated")
            return len(data)
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
            with open(path, "r") as file:
                self.item_map = json.load(file)
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
