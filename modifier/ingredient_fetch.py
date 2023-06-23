"""
Name: Ingredient updater
Author: RawFish
Github: https://github.com/RawFish69
Description: To fetch the ingredients from API and save into json file
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "https://api.wynncraft.com/v2/ingredient/"


class IngredientUpdater:
    def __init__(self):
        self.base_url = BASE_URL
        self.retry_after = 3  # seconds to wait before retrying after rate limit error

    def get_ingredient(self, name):
        """Fetch single ingredient from API."""
        response = requests.get(f"{self.base_url}get/{name}")
        ingredient_info = response.json()['data'][0]
        print(ingredient_info)

    def fetch_ingredient_list(self):
        """Fetch all ingredients from API."""
        response = requests.get(f"{self.base_url}list")
        return response.json()['data']

    def fetch_old_ingredient_data(self):
        """Load previously fetched ingredients from local json file."""
        try:
            with open("wynn_ingredients.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def fetch_ingredient_info(self, name):
        """Fetch detailed info for a single ingredient from API and handle potential errors."""
        while True:
            try:
                response = requests.get(f"{self.base_url}get/{name}")
                response.raise_for_status()  # raises an exception for HTTP errors
                return response.json()['data'][0]
            except requests.exceptions.RequestException as e:
                print(f"An error occurred: {e}")
                print(f"Retrying in {self.retry_after} seconds...")
                time.sleep(self.retry_after)

    def update_ingredient_data(self, ingredient_data, i, total_ingredients):
        """Save updated ingredients data to local json file and show progress bar."""
        with open("wynn_ingredients.json", 'w') as f:
            f.write(json.dumps(ingredient_data, indent=4))
        # Simple progress bar displayed every time data is written to the file
        print(f'Progress: [{"|" * (i // 10)}{" " * ((total_ingredients - i) // 10)}] {i}/{total_ingredients}')

    def write_to_log(self, changelog):
        """Write the changelog to local file."""
        with open("ingredient_change.log", 'w', encoding="utf-8") as log:
            log.write(changelog)
        print(changelog)

    def build_ingredient_changelog(self, ingredient_data_old, ingredient_data_new, ingredients_added,
                                   ingredients_removed):
        """Construct ingredient changelog"""
        ingredients_modified = [x for x in ingredient_data_new.keys() if x in ingredient_data_old]
        ingredient_changelog = ""
        time_now = datetime.now()
        current_datetime = time_now.strftime("%Y-%m-%d %H:%M:%S")
        ingredient_changelog += f"Ingredient changelog - Updated from API\n"
        ingredient_changelog += f"{len(ingredient_data_new)} total ingredients scanned\n"
        modified_count = 0
        modified_log = ""
        for name in ingredients_modified:
            new = ingredient_data_new[name]
            old = ingredient_data_old[name]
            if new != old:
                modified_count += 1
                modified_log += f"{name}:\n"
                for (new_stat, new_val), (old_stat, old_val) in zip(new.items(), old.items()):
                    if new_val != old_val:
                        modified_log += f"{new_stat}: {old_val} -> {new_val}\n"
                modified_log += "\n"
        ingredient_changelog += f"New Ingredients: {len(ingredients_added)}, Ingredients Removed: {len(ingredients_removed)}, Ingredients changed: {modified_count}\n"
        ingredient_changelog += f"Ingredient Changes: \n{modified_log}"
        ingredient_changelog += f"Ingredients Added:\n"
        for ingredient in ingredients_added:
            ingredient_changelog += f"- {ingredient}\n"
        ingredient_changelog += f"Ingredients Removed:\n"
        for ingredient in ingredients_removed:
            ingredient_changelog += f"- {ingredient}\n"
        ingredient_changelog += "\n"
        ingredient_changelog += f"Log Update Date: {current_datetime}"
        return ingredient_changelog

    def ingredient_update(self):
        """Main function to update ingredient data with a simple progress bar."""
        ingredient_list = self.fetch_ingredient_list()
        ingredient_data_old = self.fetch_old_ingredient_data()
        ingredient_data_new = {}
        total_ingredients = len(ingredient_list)
        print(f"Start processing ingredients, total: {total_ingredients}")
        for i, name in enumerate(ingredient_list, 1):
            print(f"{name} [{i}/{total_ingredients}]")
            ingredient_data_new[name] = self.fetch_ingredient_info(name)
            if i % 10 == 0:
                self.update_ingredient_data(ingredient_data_new, i, total_ingredients)
            time.sleep(3)  # Adjusted sleep time considering the rate limit
        ingredients_added = [name for name in ingredient_data_new if name not in ingredient_data_old]
        ingredients_removed = [name for name in ingredient_data_old if name not in ingredient_data_new]
        ingredient_changelog = self.build_ingredient_changelog(ingredient_data_old, ingredient_data_new, ingredients_added, ingredients_removed)
        self.write_to_log(ingredient_changelog)
        self.update_ingredient_data(ingredient_data_new, total_ingredients, total_ingredients)


# Create an instance of the class
updater = IngredientUpdater()

# Fetch ingredient list from API
ingredient_list = updater.fetch_ingredient_list()
print(f"Total ingredients fetched: {len(ingredient_list)}")

# Main function to update ingredient data
updater.ingredient_update()


# Fetch single ingredient info from API
single_ingredient = updater.get_ingredient(ingredient_list[0])  # getting info for the first ingredient
print(f"Single ingredient info: {single_ingredient}")

# Load previously fetched ingredients from local json file
ingredient_data_old = updater.fetch_old_ingredient_data()
print(f"Old ingredient data loaded: {ingredient_data_old}")

# Fetch detailed info for a single ingredient from API
ingredient_info = updater.fetch_ingredient_info(ingredient_list[0])  # getting detailed info for the first ingredient
print(f"Detailed ingredient info: {ingredient_info}")

