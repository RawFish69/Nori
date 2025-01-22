"""
Author: RawFish
Description: Utilities for item searching, matching, stat rolling, and item decoding.
"""

import re
import random
import json
from typing import Optional, Dict, Tuple, Any, List

STAT_MAPPING = {
    # load from stats_mapping or whatever your source is
}

class ItemUtils:
    """
    A utility class for searching items, matching classes, rolling/amplifying stats,
    and decoding item data from WynnTils (UTF-16) format.
    """

    def __init__(self, item_map: Dict[str, Any]):
        """
        :param item_map: A dictionary of item data, typically loaded from items.json.
        """
        self.item_map = item_map

    def item_match(self, name: str) -> Optional[Dict[str, str]]:
        """
        Attempt to find a single item in self.item_map that exactly matches `name`,
        and return some basic metadata (icon link, associated class).
        
        :param name: The user-provided item name (case-insensitive).
        :return: A dict with `{"icon": icon_link, "class": class_type}` or None if not found.
        """
        if not self.item_map:
            print("Item map is empty.")
            return None

        for item_key, data in self.item_map.items():
            if name.lower() == item_key.lower():
                icon_id = None
                if "icon" in data:
                    if data["icon"]["format"] == "legacy":
                        icon_id = data["icon"]["value"].replace(":", "_")
                    elif data["icon"]["format"] == "attribute":
                        icon_id = data["icon"]["value"]["name"]
                if icon_id:
                    icon_link = f"https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp"
                else:
                    icon_link = None

                item_type = data.get("weaponType", None)
                type_translate = {
                    "spear": "Warrior",
                    "wand": "Mage",
                    "bow": "Archer",
                    "dagger": "Assassin",
                    "relik": "Shaman"
                }
                class_type = type_translate.get(item_type, None)
                return {"icon": icon_link, "class": class_type}
        return None

    def item_search(
        self, 
        name: str
    ) -> Optional[Tuple[str, Dict[str, Any], Optional[str], Optional[str], Optional[str]]]:
        """
        Searches for an item in `self.item_map` by exact name, then compiles 
        and returns display strings and relevant fields.

        :param name: Item name (case-insensitive).
        :return: A tuple: 
            (base_display, IDs, icon_id, lore, item_type)
            or None if not found.
        """
        found_data = None
        found_key = None

        for item_key in self.item_map:
            if name.lower() == item_key.lower():
                found_data = self.item_map[item_key]
                found_key = item_key
                break

        if not found_data:
            return None

        base_display = f"{found_key}\n"
        IDs = {}
        id_display = ""
        icon_id = None
        lore = found_data.get("lore")
        item_type = None

        try:
            if "requirements" in found_data:
                level_req = found_data["requirements"].get("level", 0)
                rarity = found_data.get("rarity", "")
                if "type" in found_data and found_data["type"] == "weapon":
                    base_display += f"Lv. {level_req} {rarity} {found_data['type']}\n"
                elif "accessoryType" in found_data:
                    base_display += f"Lv. {level_req} {rarity} {found_data['accessoryType']}\n"
                elif "type" in found_data:
                    base_display += f"Lv. {level_req} {rarity} {found_data['type']}\n"

            base_stats = found_data.get("base", {})
            for stat, value in base_stats.items():
                if isinstance(value, dict) and "min" in value and "max" in value:
                    base_display += f"{stat}: {value['min']} - {value['max']}\n"
                else:
                    base_display += f"{stat}: {value}\n"

            if "attackSpeed" in found_data:
                base_display += f"Attack speed: {found_data['attackSpeed']}\n"

            identification = found_data.get("identifications", {})
            for stat, value in identification.items():
                if isinstance(value, dict) and "min" in value and "max" in value:
                    base_value = value.get("raw", 0)
                    IDs[stat] = base_value
                    id_display += f"{stat}: {base_value} [{value['min']}, {value['max']}]\n"
                else:
                    id_display += f"{stat}: {value}\n"

            if "majorIds" in found_data:
                major_data = found_data["majorIds"]
                if major_data:
                    name_key = list(major_data.keys())[0]
                    pattern = r'&[a-zA-Z0-9+](?![a-zA-Z0-9])'
                    cleaned_string = re.sub(pattern, '', name_key)
                    parts = cleaned_string.split(":", 1)
                    cleaned_description = parts[1].strip() if len(parts) > 1 else cleaned_string.strip()
                    cleaned_description = re.sub("&3", "", cleaned_description)
                    id_display += f"Major ID: {cleaned_description}\n"

            if "dropMeta" in found_data:
                drop_meta = found_data["dropMeta"]
                drop_name = drop_meta.get("name", "")
                drop_type = drop_meta.get("type", "")
                coords = drop_meta.get("coordinates", "")
                id_display += f"Drop: {drop_name} ({drop_type})\nCoordinates: {coords}"

            if "icon" in found_data:
                if found_data["icon"]["format"] == "legacy":
                    icon_id = found_data["icon"]["value"].replace(":", "_")
                elif found_data["icon"]["format"] == "attribute":
                    icon_id = found_data["icon"]["value"]["name"]

            if "type" in found_data:
                if found_data["type"] == "weapon":
                    item_type = found_data.get("weaponType", None)
                elif found_data["type"] == "armour":
                    item_type = found_data.get("armourType", None)

        except Exception as error:
            print(f"Error in item_search: {error}")
            return None

        return (base_display, IDs, icon_id, lore, item_type)

    def item_amp(self, name: str, tier: int) -> Tuple[str, str, Dict[str, int], Optional[str], Optional[str]]:
        """
        Applies a random "amplification" to item IDs based on a tier factor.
        This simulates rolling the stats with some random variation.

        :param name: Item name (case-insensitive).
        :param tier: The amplification tier used to scale the roll (1,2,3,...).
        :return: 
            (base_display, rr_display, rolled_values, icon_id, item_type)
        """
        amp = 0.05 * int(tier)
        item_data = self.item_search(name)
        if not item_data:
            return ("", "", {}, None, None)
        
        base_display_str = item_data[0]
        IDs = item_data[1]
        icon_id = item_data[2]
        item_type = item_data[4]

        display_name = None
        for item_key in self.item_map:
            if name.lower() == item_key.lower():
                display_name = item_key
                break
        if not display_name:
            display_name = name

        result = {}
        overall = 0.0
        stat_count = 0
        rr_display = f"{round(amp * 100)}% Increase to IDs\n"
        stat_display = ""

        for stat, base_value in IDs.items():
            raw_val = int(base_value)
            if raw_val > 0:
                positive_roll = round(random.uniform(0.3, 1.3), 2)
                amp_roll = round(positive_roll + (1.3 - positive_roll) * amp, 2)
                star = self._roll_star(amp_roll, is_spellcost=("spellcost" in stat.lower()))

                max_val = int(raw_val * 1.3) + 1
                if "spellcost" in stat.lower():
                    id_rolled = self._round_half_up(raw_val * round(random.uniform(0.7, 1.3), 2))
                    min_val = round(raw_val * 0.7)
                    if min_val != max_val:
                        percentage = ((max_val - id_rolled) / (max_val - min_val)) * 100
                    else:
                        percentage = 100
                else:
                    id_rolled = self._round_half_up(raw_val * amp_roll)
                    min_val = round(raw_val * 0.3)
                    if min_val != max_val:
                        percentage = ((id_rolled - min_val) / (max_val - min_val)) * 100
                    else:
                        percentage = 100

                overall += percentage
                stat_count += 1
                result[stat] = id_rolled
                stat_display += f"{id_rolled}{star} {STAT_MAPPING.get(stat, stat)} [{abs(percentage):.1f}%]\n"

            elif raw_val < 0:
                negative_roll = round(random.uniform(0.7, 1.3), 2)
                amp_roll = round(negative_roll + (1.3 - negative_roll) * amp, 2)
                star = self._roll_star(amp_roll, is_spellcost=("spellcost" in stat.lower()))

                max_val = int(raw_val * 1.3)
                if "spellcost" in stat.lower():
                    id_rolled = self._round_half_up(raw_val * amp_roll)
                    min_val = round(raw_val * 0.3)
                    if min_val != max_val:
                        percentage = ((id_rolled - min_val) / (max_val - min_val)) * 100
                    else:
                        percentage = 100
                else:
                    id_rolled = self._round_half_up(raw_val * negative_roll)
                    min_val = round(raw_val * 0.7)
                    if min_val != max_val:
                        percentage = ((max_val - id_rolled) / (max_val - min_val)) * 100
                    else:
                        percentage = 100

                overall += percentage
                stat_count += 1
                result[stat] = id_rolled
                stat_display += f"{id_rolled}{star} {STAT_MAPPING.get(stat, stat)} [{abs(percentage):.1f}%]\n"

        rr_display += f"{display_name} [{abs(overall / stat_count) if stat_count else 0:.1f}%]\n"
        rr_display += stat_display

        print(f"{display_name}: {result}")
        return (base_display_str, rr_display, result, icon_id, item_type)

    def _roll_star(self, roll_val: float, is_spellcost: bool = False) -> str:
        """
        Determine how many 'stars' to append based on the roll value.
        This is purely aesthetic. Lower thresholds for spellcost to 
        differentiate if needed, or keep same logic.
        """
        if is_spellcost:
            if 1.0 <= roll_val < 1.25:
                return "*"
            elif 1.25 <= roll_val < 1.3:
                return "**"
            elif abs(roll_val - 1.3) < 1e-9:
                return "***"
            return ""
        else:
            if 1.0 <= roll_val < 1.25:
                return "*"
            elif 1.25 <= roll_val < 1.3:
                return "**"
            elif abs(roll_val - 1.3) < 1e-9:
                return "***"
            return ""

    def _round_half_up(self, val: float) -> int:
        """
        Round half values (.5) up instead of to the nearest even (default python behavior).
        Example: 3.5 -> 4, -2.5 -> -2
        """
        return int(val + 0.5 if val >= 0 else val - 0.5)

    def decode_item(self, item_string: str) -> Optional[dict]:
        """
        Decodes a WynnTils UTF-16 item string into a dictionary of 
        {itemName: {stat: value}, 'rate': {stat: rollPercentage}, 'shiny': ... }

        :param item_string: A WynnTils-resolved gear string.
        :return: A structured dict, or None if decoding fails.
        """
        try:
            item = self._mock_wynntils_decode(item_string)

            name = item["name"]
            identifications = item["identifications"]
            stats_output = {name: {}, "rate": {}, "shiny": None}

            data = self.item_map.get(name, {})
            id_range = data.get("identifications", {})

            if "shiny" in item and item["shiny"]:
                shiny_data = item["shiny"]
                stats_output["shiny"] = f"{shiny_data['display_name']}: {shiny_data['value']}"

            for stat_id, roll_data in identifications.items():
                roll_percentage = roll_data["roll"] / 100
                base_stat_info = id_range.get(stat_id, {})
                
                id_min = base_stat_info.get("min", 0)
                id_max = base_stat_info.get("max", 0)
                id_base = base_stat_info.get("raw", 0)

                id_rolled = round(id_base * roll_percentage)
                if id_min != id_max:
                    percentage = ((id_rolled - id_min) / (id_max - id_min)) * 100
                else:
                    percentage = 100

                stats_output[name].update({stat_id: id_rolled})
                stats_output["rate"].update({stat_id: round(percentage, 2)})

            print(json.dumps(stats_output, indent=2))
            return stats_output
        except Exception as error:
            print(f"Decode error: {error}")
            return None

    def _mock_wynntils_decode(self, item_string: str) -> dict:
        """
        use WynntilsResolver or whatever library you have to decode the gear item.
        """
        return None
