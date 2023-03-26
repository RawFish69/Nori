def item_update():
    category = 'all'
    request_data = requests.get(f'https://api.wynncraft.com/public_api.php?action=itemDB&category={category}')
    item_data = request_data.json()
    items = json.dumps(item_data, indent=3)
    with open('update_items.json', 'w') as file:
        file.write(items)
    item_names_old = []
    item_names_new = []
    with open("wynn_items.json", 'r') as f1, open("update_items.json", 'r') as f2:
        old_items_raw = json.load(f1)
        old_items_list = old_items_raw['items']
        new_items_raw = json.load(f2)
        new_items_list = new_items_raw['items']
    for item in old_items_list:
        item_names_old.append(item.get("name"))
    for item in new_items_list:
        item_names_new.append(item.get("name"))
    # Check for added
    # print(len(old_items_list), len(new_items_list))
    items_added = []
    items_removed = []
    for name in item_names_old:
        if name not in item_names_new:
            items_removed.append(name)
    for name in item_names_new:
        if name not in item_names_old:
            items_added.append(name)
    items_modified = [x for x in item_names_new if x in item_names_old]
    item_changelog = ""
    time_now = datetime.now()
    current_datetime = time_now.strftime("%Y-%m-%d %H:%M:%S")
    item_changelog += f"Item changelog - Updated from API\n"
    item_changelog += f"{len(new_items_list)} total items scanned\n"
    modified_count = 0
    # Only the items that were changed
    modified_log = ""
    temp_dict = {}
    val = old_items_list
    for new, old in zip(new_items_list, old_items_list):
        item_name = new["name"]
        if item_name in items_modified:
            # Same position
            if new != old and item_name == old["name"]:
                modified_count += 1
                modified_log += f"{item_name}:\n"
                for (new_stat, new_id), (old_stat, old_id) in zip(new.items(), old.items()):
                    if new_id != old_id:
                        modified_log += f"{new_stat}: {old_id} -> {new_id}\n"
                modified_log += "\n"
            # Moved position
            elif item_name != old["name"]:
                for old_item in old_items_list:
                    if item_name == old_item["name"] and new != old_item:
                        modified_count += 1
                        modified_log += f"{item_name}:\n"
                        for (stat_new, id_new), (stat_old, id_old) in zip(new.items(), old_item.items()):
                            if id_new != id_old:
                                modified_log += f"{stat_new}: {id_old} -> {id_new}\n"
                        modified_log += "\n"
    item_changelog += f"New Items: {len(items_added)}, Items Removed: {len(items_removed)}, Items changed: {modified_count}\n"
    item_changelog += f"Item Changes: \n{modified_log}"
    item_changelog += f"Items Added:\n"
    for item in items_added:
        item_changelog += f"- {item}\n"
    item_changelog += f"Removed Items:\n"
    for item in items_removed:
        item_changelog += f"- {item}\n"
    item_changelog += "\n"
    item_changelog += f"Log Update Date: {current_datetime}"
    # Write to the log file
    with open("item_change.log", 'w', encoding="utf-8") as log:
        log.write(item_changelog)
    print(item_changelog)
    with open("wynn_items.json", 'w') as f:
        f.write(json.dumps(new_items_raw, indent=4))



def item_sort(tier):
    """Work in progress"""
    with open('/app/bot/wynn_items.json', 'r') as file:
        item_data = json.load(file).get('items')
    file_json = json.dumps(item_data, indent=3)
    for item in item_data:
        if item.get('tier') == tier:
            print(item.get('name'))


def item_search(name):
    with open('/app/bot/wynn_items.json', 'r') as file:
        item_data = json.load(file).get('items')
    file_json = json.dumps(item_data, indent=3)
    found = False
    min_val = 0
    max_val = 0
    result = {}
    display = '```json\n\n'
    for item in item_data:
        if name.lower() == item.get('name').lower():
            found = True
            result = item
    if found == False:
        display += 'Cannot find the item you are looking for.```'
    elif found == True:
        display += f"{result.get('name')}\n"
        if 'accessoryType' in result:
            display += f"Lv. {result.get('level')} {result.get('tier')} {result.get('accessoryType')}\n"
        else:
            display += f"Lv. {result.get('level')} {result.get('tier')} {result.get('type')}\n"
        item_sp = ''
        item_base = ''
        item_def = ''
        sp_req = ['strength', 'dexterity', 'intelligence', 'defense', 'agility']
        sp_types = ['strengthPoints', 'dexterityPoints', 'intelligencePoints', 'defensePoints', 'agilityPoints']
        base_dmg = ['damage', 'earthDamage', 'thunderDamage', 'waterDamage', 'fireDamage', 'airDamage']
        base_def = ['earthDefense', 'thunderDefense', 'waterDefense', 'fireDefense', 'airDefense']
        other_ids = ['tier', 'name', 'type', 'category', 'attackSpeed', 'majorIds', 'sockets',
                     'level', 'dropType', 'addedLore', 'material', 'quest', 'classRequirement',
                     'set', 'armorType', 'armorColor', 'accessoryType', 'restrictions', 'health']
        for sp in sp_types:
            if result.get(sp[:-6]) != 0:
                item_sp += f'{sp[:-6]} Req: {result.get(sp[:-6])} '
            if result.get(sp) != 0:
                item_sp += f'{sp[:-6]} SP: {result.get(sp)}\n'
        for base in base_dmg:
            if result.get(base) != '0-0' and base in result:
                if base == 'damage':
                    item_base += f'neutral base: {result.get(base)}\n'
                elif base != 'damage':
                    item_base += f'{base[:-6]} base: {result.get(base)}\n'
        for baseDef in base_def:
            if result.get(baseDef) != 0:
                item_def += f'{baseDef[:-7]} defense: {result.get(baseDef)}\n'
        if 'health' in result:
            display += f"Health: {result.get('health')}\n"
        display += item_base
        if result.get('category') != 'weapon':
            display += item_def
        if 'attackSpeed' in result:
            display += f"Attack Speed: {result.get('attackSpeed')}\n"
        display += item_sp
        display += '\n'
        for stat in result:
            value = result.get(stat)
            if stat in sp_req:
                pass
            elif stat in sp_types:
                pass
            elif stat in base_dmg:
                pass
            elif stat in other_ids:
                pass
            elif stat in base_def:
                pass
            elif value != 0 and 'identified' not in result:
                if int(value) > 0:
                    max_val = round(value * 1.3)
                    if 'spellcost' not in stat.lower():
                        min_val = round(value * 0.3)
                    elif 'spellcost' in stat.lower():
                        min_val = round(value * 0.7)
                    display += '{}: [{:.1f}, {:.1f}]\n'.format(stat, min_val, max_val)
                elif int(value) < 0:
                    max_val = round(value * 1.3)
                    if 'spellcost' not in stat.lower():
                        min_val = round(value * 0.7)
                    elif 'spellcost' in stat.lower():
                        min_val = round(value * 0.3)
                    display += '{}: [{:.1f}, {:.1f}]\n'.format(stat, min_val, max_val)
                else:
                    display += f'{stat}: {value} [Non number]\n'
            elif value != 0 and 'identified' in result:
                if int(value) > 0:
                    display += '{}: [{:.1f}]\n'.format(stat, value)
                elif int(value) < 0:
                    display += '{}: [{:.1f}]\n'.format(stat, value)
        if 'majorIds' in result:
            display += '\n'
            display += f"Major ID: {result.get('majorIds')}"
        else:
            display += '\n'
            display += 'No major ID'
        display += '```'
    return display
