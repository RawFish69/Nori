"""
Build and recipe file management utilities for Nori bot.

This module contains functions for searching, updating, and removing
builds and recipes from the database files.
"""
import json
from typing import List, Dict, Any, Optional
from lib.config import DATA_PATH


async def build_file_search(keywords: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search builds by keywords.

    Args:
        keywords: List of search keywords

    Returns:
        Dictionary with "Result" key containing matching builds
    """
    with open(DATA_PATH / "build_db.json", "r") as file:
        data = json.load(file)["Builds"]
    
    result = {"Result": []}
    keywords = [keyword.lower() for keyword in keywords]
    
    for build in data:
        tags = data[build]["tag"]
        
        if len(keywords) == 3:
            if (keywords[0] in tags.lower() and keywords[1] in tags.lower() and keywords[2] in tags.lower()) or \
               (keywords[0] in build.lower() and keywords[1] in build.lower() and keywords[2] in build.lower()):
                result["Result"].insert(0, {build: data[build]})
        elif len(keywords) == 2:
            if (keywords[0] in tags.lower() and keywords[1] in tags.lower()) or \
               (keywords[0] in build.lower() and keywords[1] in build.lower()):
                result["Result"].append({build: data[build]})
        else:
            for keyword in keywords:
                if keyword in build.lower() or keyword in tags.lower():
                    result["Result"].append({build: data[build]})
                    break
    
    return result


async def build_file_updater(new_build: Dict[str, Any]) -> None:
    """
    Update build database with new build.

    Args:
        new_build: Dictionary containing build data
    """
    with open(DATA_PATH / "build_db.json", "r") as file:
        data = json.load(file)["Builds"]
    
    build_name = str(list(new_build.keys())[0])
    
    if build_name not in data:
        new_build.update(data)
        data = new_build
    else:
        data[build_name] = new_build[build_name]
    
    updated_json = json.dumps({"Builds": data}, indent=3)
    with open(DATA_PATH / 'build_db.json', 'w') as file:
        file.write(updated_json)


async def build_file_remove(build_name: str) -> bool:
    """
    Remove a build from the database.

    Args:
        build_name: Name of the build to remove

    Returns:
        True if build was found and removed, False otherwise
    """
    with open(DATA_PATH / "build_db.json", "r") as file:
        data = json.load(file)["Builds"]
    
    found = False
    actual_name = None
    
    for build in data:
        if build_name.lower() == build.lower():
            found = True
            actual_name = build
            break
    
    if found and actual_name:
        data.pop(actual_name)
        updated_json = json.dumps({"Builds": data}, indent=3)
        with open(DATA_PATH / 'build_db.json', 'w') as file:
            file.write(updated_json)
        return True
    
    return False


async def recipe_file_search(keywords: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search recipes by keywords.

    Args:
        keywords: List of search keywords

    Returns:
        Dictionary with "Result" key containing matching recipes
    """
    with open(DATA_PATH / "recipe_db.json", "r") as file:
        data = json.load(file)["Recipes"]
    
    result = {"Result": []}
    keywords = [keyword.lower() for keyword in keywords]
    
    for recipe in data:
        tags = data[recipe]["tag"]
        
        if len(keywords) == 3:
            if (keywords[0] in tags.lower() and keywords[1] in tags.lower() and keywords[2] in tags.lower()) or \
               (keywords[0] in recipe.lower() and keywords[1] in recipe.lower() and keywords[2] in recipe.lower()):
                result["Result"].insert(0, {recipe: data[recipe]})
        elif len(keywords) == 2:
            if (keywords[0] in tags.lower() and keywords[1] in tags.lower()) or \
               (keywords[0] in recipe.lower() and keywords[1] in recipe.lower()):
                result["Result"].append({recipe: data[recipe]})
        else:
            for keyword in keywords:
                if keyword in recipe.lower() or keyword in tags.lower():
                    result["Result"].append({recipe: data[recipe]})
                    break
    
    return result


async def recipe_file_updater(new_recipe: Dict[str, Any]) -> None:
    """
    Update recipe database with new recipe.

    Args:
        new_recipe: Dictionary containing recipe data
    """
    with open(DATA_PATH / "recipe_db.json", "r") as file:
        data = json.load(file)["Recipes"]
    
    recipe_name = str(list(new_recipe.keys())[0])
    
    if recipe_name not in data:
        new_recipe.update(data)
        data = new_recipe
    else:
        data[recipe_name] = new_recipe[recipe_name]
    
    updated_json = json.dumps({"Recipes": data}, indent=3)
    with open(DATA_PATH / 'recipe_db.json', 'w') as file:
        file.write(updated_json)


async def recipe_file_remove(recipe_name: str) -> bool:
    """
    Remove a recipe from the database.

    Args:
        recipe_name: Name of the recipe to remove

    Returns:
        True if recipe was found and removed, False otherwise
    """
    with open(DATA_PATH / "recipe_db.json", "r") as file:
        data = json.load(file)["Recipes"]
    
    found = False
    actual_name = None
    
    for recipe in data:
        if recipe_name.lower() == recipe.lower():
            found = True
            actual_name = recipe
            break
    
    if found and actual_name:
        data.pop(actual_name)
        updated_json = json.dumps({"Recipes": data}, indent=3)
        with open(DATA_PATH / 'recipe_db.json', 'w') as file:
            file.write(updated_json)
        return True
    
    return False

