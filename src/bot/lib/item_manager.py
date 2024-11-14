"""
Author: RawFish
Description: Core item management and data handling functionality
"""

import json
from .item_wrapper import Items

class ItemManager:
    def __init__(self):
        self.item_map = {}

    def update_items(self, path):
        data = Items().get_all_items()
        if not data:
            print("Invalid API response")
            return 0
            
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
        
        # Check for auth error (down)
        if "detail" in data and data["detail"] == "Authentication credentials were not provided.":
            print("Error fetching item data, is it down?")
            return 0
            
        return self._save_item_data(data, path)

    def _save_item_data(self, data, path):
        try:
            with open(path, "w") as file:
                json.dump(data, file, indent=3)
            print(f"{len(data)} items updated")
            return len(data)
        except Exception as error:
            print(f"File update error: {error}")
            return 0

    def get_item_name(self, name, items_path):
        try:
            with open(items_path, "r") as file:
                item_data = json.load(file)
                for item in item_data:
                    if name.lower() == item.lower():
                        return str(item)
            return None
        except Exception as error:
            print(f"Error getting item name: {error}")
            return None