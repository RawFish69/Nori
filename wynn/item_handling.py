"""
Name: Item handler
Author: RawFish
Github: https://github.com/RawFish69
Description: Item parsing and handling for nori-bot and other supporting applications
"""


def item_search(name):
    """Replace old item_search when Wynntils is updated with new ID order"""
    with open("items.json", "r") as file:
        item_data = json.load(file)
    found = False
    data = {}
    IDs = {}
    material_id = None
    for item in item_data:
        if name.lower() == item.lower():
            found = True
            data = item_data[item]
            base_display += item + "\n"
    if found:
        try:
            lore = data["lore"] if "lore" in data else None
            base = data["base"]
            for stat, value in base.items():
                if type(value) is dict:
                    base_display += f"{stat}: {base[stat]['min']} - {base[stat]['max']}\n"
                else:
                    base_display += f"{stat}: {base[stat]}\n"
            identification = data["identifications"]
            for stat, value in identification.items():
                if type(value) is dict:
                    if identification[stat]["max"] > 0:
                        base_value = round(identification[stat]["max"] / 1.3)
                    else:
                        base_value = round(identification[stat]["min"] / 1.3)
                    IDs[stat] = base_value
            if "majorIds" in data:
                description = data['majorIds']['description']
                pattern = r'&[a-zA-Z0-9+](?![a-zA-Z0-9])'
                cleaned_string = re.sub(pattern, '', description)
                parts = cleaned_string.split(":", 1)
                cleaned_description = parts[1].strip() if len(parts) > 1 else cleaned_string.strip()
                cleaned = re.sub("&3", "", cleaned_description)
                # Add cleaned variable to final return, if needed
            if "material" in data:
                material = data["material"]
                material_id = material.replace(":", "_")
        except Exception as error:
            print(error)
            return None
    else:
        return None
    return IDs, material_id, lore


def item_amp(name, tier):
  pass

def item_decode(params):
  pass

def item_weight_output(params):
  pass

def item_pricecheck(params):
  pass

def item_changelog(param):
  pass
  
