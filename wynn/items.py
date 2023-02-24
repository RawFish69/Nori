def item_roll(name):
    with open('/app/bot/wynn_items.json', 'r') as file:
        item_data = json.load(file).get('items')
    file_json = json.dumps(item_data, indent=3)
    found = False
    result = {}
    display = '\n'
    for item in item_data:
        if name.lower() == item.get('name').lower():
            found = True
            result = item
    if found == False:
        display += 'Cannot find the item you are looking for.'
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
        overall = 0
        stat_count = 0
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
        display += 'Rerolled Stats:\n'
        stat_display = ''
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
            elif value == -1:
                pass
            elif value != 0 or result.get('identified') == True:
                if int(value) > 0:
                    positive_roll = round(random.uniform(0.3, 1.3), 2)
                    negative_roll = round(random.uniform(0.7, 1.3), 2)
                    star = ''
                    if 'spellcost' not in stat.lower():
                        if 1.0 <= positive_roll <= 1.24:
                            star = '*'
                        elif 1.25 <= positive_roll <= 1.29:
                            star = '**'
                        elif positive_roll == 1.3:
                            star = '***'
                    id_rolled = 0
                    min_val = 0
                    max_val = round(value * 1.3)
                    percentage = 0
                    if 'spellcost' in stat.lower():
                        id_rolled = round(value * negative_roll)
                        min_val = round(value * 0.7)
                        percentage = ((max_val - id_rolled) / (max_val - min_val)) * 100
                    else:
                        id_rolled = round(value * positive_roll)
                        min_val = round(value * 0.3)
                        percentage = ((id_rolled - min_val) / (max_val - min_val)) * 100
                    overall += percentage
                    stat_count += 1
                    stat_display += '{}: {}{} [{:.1f}%]\n'.format(stat, id_rolled, star, abs(percentage))
                elif int(value) < 0:
                    positive_roll = round(random.uniform(0.3, 1.3), 2)
                    negative_roll = round(random.uniform(0.7, 1.3), 2)
                    star = ''
                    if 'spellcost' in stat.lower():
                        if 1.0 <= positive_roll <= 1.24:
                            star = '*'
                        elif 1.25 <= positive_roll <= 1.29:
                            star = '**'
                        elif positive_roll == 1.3:
                            star = '***'
                    id_rolled = 0
                    max_val = round(value * 1.3)
                    min_val = 0
                    # Fixed formula
                    percentage = 0
                    if 'spellcost' in stat.lower():
                        id_rolled = round(value * positive_roll)
                        min_val = round(value * 0.3)
                        percentage = ((id_rolled - min_val) / (max_val - min_val)) * 100
                        stat_display += '{}: {}{} [{:.1f}%]\n'.format(stat, id_rolled, star, abs(percentage))
                    else:
                        id_rolled = round(value * negative_roll)
                        min_val = round(value * 0.7)
                        percentage = ((max_val - id_rolled) / (max_val - min_val)) * 100
                        stat_display += '{}: {} [{:.1f}%]\n'.format(stat, id_rolled, abs(percentage))
                    overall += percentage
                    stat_count += 1
                else:
                    pass
            elif value != 0 and 'identified' in result and result.get('identified') == True:
                if int(value) > 0:
                    display += '{}: [{:.1f}]\n'.format(stat, value)
                elif int(value) < 0:
                    display += '{}: [{:.1f}]\n'.format(stat, value)
        display += "{} [{:.1f}%]\n".format(result.get('name'), abs(overall/stat_count))
        display += stat_display
        if 'majorIds' in result:
            display += '\n'
            display += f"Major ID: {result.get('majorIds')}"
        else:
            display += '\n'
            display += 'No major ID'
    return display
