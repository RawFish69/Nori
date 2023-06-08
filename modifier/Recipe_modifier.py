"""
Name: Recipe modifier
Author: RawFish
Github: https://github.com/RawFish69
Description: To modify recipe database for Nori
"""

import json

class RecipeManager:
    def __init__(self, file_name):
        self.file_name = file_name

    def recipe_file_generator(self, types=None, links=None, tags=None):
        if types is None:
            types = []
        if links is None:
            links = []
        if tags is None:
            tags = []

        recipe_list = [{'type': type_, 'link': link, 'tag': tag} for type_, link, tag in zip(types, links, tags)]
        recipe_dict = {'Recipes': recipe_list}
        recipe_json = json.dumps(recipe_dict, indent=3)
        print(recipe_json)
        with open(self.file_name, 'w') as file:
            file.write(recipe_json)
        return recipe_json

    def recipe_file_reader(self):
        with open(self.file_name, 'r') as file:
            file_dict = json.load(file)
        return file_dict

    def recipe_file_updater(self, new_recipes):
        saved_dict = self.recipe_file_reader()
        updated_list = saved_dict.get('Recipes')
        updated_list.append(new_recipes)
        updated_recipes = {'Recipes': updated_list}
        updated_json = json.dumps(updated_recipes, indent=3)
        with open(self.file_name, 'w') as file:
            file.write(updated_json)
        print('updated recipe list:')
        print(self.recipe_file_reader())

    def recipe_file_search(self, key_word):
        with open(self.file_name, 'r') as file:
            file_dict = json.load(file)
        recipe_list = file_dict.get('Recipes')
        results = [f'**{recipe["type"]}** [{recipe["tag"]}]\nLink: {recipe["link"]}\n' for recipe in recipe_list if key_word in recipe['type'] or key_word in recipe['tag']]
        print('No results found' if not results else 'Possible match:\n' + '\n'.join(results))

    def add_recipes(self):
        type_ = input('Type: ')
        link = input('Recipe Link: ')
        tag = input('Tag: ')
        new_recipe = {'type': type_, 'link': link, 'tag': tag}
        self.recipe_file_updater(new_recipe)

if __name__ == "__main__":
    rm = RecipeManager('recipe_list.json')
    rm.add_recipes()
