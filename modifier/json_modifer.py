import json
import csv
from datetime import datetime


def weight_file_generate():
    with open('Mythic Items - stats.csv') as stats_file:
        stats_reader = csv.reader(stats_file)
        stats = {}
        next(stats_reader)
        for row in stats_reader:
            stats[row[0]] = {
                'stat_1': row[1],
                'stat_2': row[2],
                'stat_3': row[3],
                'stat_4': row[4],
                'stat_5': row[5],
                'stat_6': row[6],
                'stat_7': row[7]
            }

    # Read the 'weights' CSV file
    with open('Mythic Items - weights.csv') as weights_file:
        weights_reader = csv.reader(weights_file)
        weights = {}
        # Skip header row
        next(weights_reader)
        for row in weights_reader:
            # Add item to weights dictionary
            weights[row[0]] = {
                'stat_1': row[1],
                'stat_2': row[2],
                'stat_3': row[3],
                'stat_4': row[4],
                'stat_5': row[5],
                'stat_6': row[6],
                'stat_7': row[7]
            }
    with open('Mythic Items - prices.csv') as price_file:
        price_reader = csv.reader(price_file)
        prices = {}
        next(price_reader)
        for row in price_reader:
            prices[row[0]] = {
                'unid': row[1],
            }
    stat_order = tils_stat_order()
    items = {"Data": {}, "unid": {}, "order": stat_order, "date": {}}
    for item_name in stats:
        items["Data"][item_name] = {}
        items["unid"][item_name] = {}
        for stat, weight in zip(stats[item_name].values(), weights[item_name].values()):
            if stat != '' and weight != '':
                items["Data"][item_name].update({stat: weight})
        for price in prices[item_name].items():
            items["unid"].update({item_name: price[1]})
    current_time = datetime.now()
    current_datetime = current_time.strftime("%Y-%m-%d %H:%M:%S")
    items["date"].update({"Last update": current_datetime})
    items_json = json.dumps(items, indent=2)

    with open('mythic_weights.json', 'w') as outfile:
        outfile.write(items_json)
    print("File successfully generated")
    print(f"Updated: {current_datetime}")

def build_file_generator():
    names = []
    links = []
    tags = []
    build_list = []
    for i in range(len(names)):
        build_list.append({'name': names[i], 'link': links[i], 'tag': tags[i]})
    build_dict = {'Builds': build_list}
    build_json = json.dumps(build_dict, indent=3)
    print(build_json)
    with open('build_list.json', 'w') as file:
        file.write(build_json)
    return build_json

def build_file_reader():
    with open('build_list.json', 'r') as file:
        file_dict = json.load(file)
    build_list = file_dict
    return build_list

def get_json_format():
    with open('build_list.json', 'r') as file:
        file_dict = json.load(file)
    build_json = json.dumps(file_dict, indent=3)
    return build_json


def build_file_updater(new_builds):
    saved_dict = build_file_reader()
    updated_list = saved_dict.get('Builds')
    updated_list.append(new_builds)
    updated_builds = {'Builds': updated_list}
    updated_json = json.dumps(updated_builds, indent=3)
    with open('build_list.json', 'w') as file:
        file.write(updated_json)
    print('updated build list:')
    print(get_json_format())

def build_file_search(key_word):
    with open('build_list.json', 'r') as file:
        file_dict = json.load(file)
    build_list = file_dict.get('Builds')
    result = ''
    for build in build_list:
        name = build.get('name')
        link = build.get('link')
        tag = build.get('tag')
        if key_word in name or key_word in tag:
            result += f'**{name}** [{tag}]\nLink: {link}\n'
        else:
            pass
    if result == '':
        print('No results found')
    else:
        print('Possible match:\n' + result)

def add_builds():
    name = input('Build Name: ')
    link = input('Builder Link: ')
    tag = input('Tag: ')
    new_build = {'name': name,
             'link': link,
             'tag': tag}
    build_file_updater(new_build)


def tils_stat_order():
    stat_order = [
                     "attackSpeedBonus",
                     "mainAttackDamageBonusRaw",
                     "mainAttackDamageBonus",
                     "mainAttackNeutralDamageBonusRaw",
                     "mainAttackNeutralDamageBonus",
                     "mainAttackEarthDamageBonusRaw",
                     "mainAttackEarthDamageBonus",
                     "mainAttackThunderDamageBonusRaw",
                     "mainAttackThunderDamageBonus",
                     "mainAttackWaterDamageBonusRaw",
                     "mainAttackWaterDamageBonus",
                     "mainAttackFireDamageBonusRaw",
                     "mainAttackFireDamageBonus",
                     "mainAttackAirDamageBonusRaw",
                     "mainAttackAirDamageBonus",
                     "mainAttackElementalDamageBonusRaw",
                     "mainAttackElementalDamageBonus",
                     "spellDamageBonusRaw",
                     "spellDamageBonus",
                     "spellNeutralDamageBonusRaw",
                     "spellNeutralDamageBonus",
                     "spellEarthDamageBonusRaw",
                     "spellEarthDamageBonus",
                     "spellThunderDamageBonusRaw",
                     "spellThunderDamageBonus",
                     "spellWaterDamageBonusRaw",
                     "spellWaterDamageBonus",
                     "spellFireDamageBonusRaw",
                     "spellFireDamageBonus",
                     "spellAirDamageBonusRaw",
                     "spellAirDamageBonus",
                     "spellElementalDamageBonusRaw",
                     "spellElementalDamageBonus",
                     "healthBonus",
                     "healthRegenRaw",
                     "healthRegen",
                     "lifeSteal",
                     "manaRegen",
                     "manaSteal",
                     "damageBonusRaw",
                     "damageBonus",
                     "neutralDamageBonusRaw",
                     "neutralDamageBonus",
                     "earthDamageBonusRaw",
                     "earthDamageBonus",
                     "thunderDamageBonusRaw",
                     "thunderDamageBonus",
                     "waterDamageBonusRaw",
                     "waterDamageBonus",
                     "fireDamageBonusRaw",
                     "fireDamageBonus",
                     "airDamageBonusRaw",
                     "airDamageBonus",
                     "elementalDamageBonusRaw",
                     "elementalDamageBonus",
                     "bonusEarthDefense",
                     "bonusThunderDefense",
                     "bonusWaterDefense",
                     "bonusFireDefense",
                     "bonusAirDefense",
                     "exploding",
                     "poison",
                     "thorns",
                     "reflection",
                     "speed",
                     "sprint",
                     "sprintRegen",
                     "jumpHeight",
                     "soulPoints",
                     "lootBonus",
                     "lootQuality",
                     "emeraldStealing",
                     "xpBonus",
                     "gatherXpBonus",
                     "gatherSpeed",
                     "spellCostRaw1",
                     "spellCostPct1",
                     "spellCostRaw2",
                     "spellCostPct2",
                     "spellCostRaw3",
                     "spellCostPct3",
                     "spellCostRaw4",
                     "spellCostPct4"
                    ]
    return stat_order


weight_file_generate()
