def player_stats(ign):
    stat_request = requests.get(f'https://api.wynncraft.com/v2/player/{ign}/stats')
    stat = stat_request.json()
    var = stat.values()
    data_raw = []
    data = []
    for i in var:
        data_raw.append(i)
    player_data = data_raw[4][0]
    for i in player_data.values():
        data.append(i)

    name = data[0]
    uuid = data[1]
    rank = data[2]
    join_info = data[3]
    game_info = data[4]
    characters_full = []
    each_class = game_info.values()
    char_raw = []
    raids = []
    index = 0
    raid_index = 0
    # Getting all raids in one list
    for i in each_class:
        characters_full.append(i)
    for char in characters_full:
        for var in char.keys():
            if var == 'raids':
                raid_index = index
            else:
                index += 1
        for items in char.values():
            char_raw.append(items)
        raids.append(char_raw[raid_index])
        char_raw.clear()
        index = 0
        raid_index = 0
    raid_completed_total = 0
    all_raids = []
    NOG = []
    TCC = []
    NOL = []
    TNA = []
    for char in raids:
        # print(char)
        raid_completed_total += int(char.get('completed'))
        for var in char.values():
            all_raids.append(var)
            for item in all_raids:
                if type(item) is not int:
                    for raid in item:
                        if raid.get('name') == 'The Canyon Colossus':
                            TCC.append(raid.get('completed'))
                        elif raid.get('name') == 'Orphion\'s Nexus of Light':
                            NOL.append(raid.get('completed'))
                        elif raid.get('name') == 'The Nameless Anomaly':
                            TNA.append(raid.get('completed'))
                        elif raid.get('name') == 'Nest of the Grootslangs':
                            NOG.append(raid.get('completed'))
                        else:
                            print('Unknown raid')
            all_raids.clear()
    NOG_runs = sum(NOG)
    TCC_runs = sum(TCC)
    NOL_runs = sum(NOL)
    TNA_runs = sum(TNA)
    guild_info = data[5]
    overall_stats = data[6]
    profession = data[7].values()
    location = join_info.get('location')
    online_status = location.get('online')
    online_server = location.get('server')
    display = '```'
    if online_status == True:
        display += f'{ign} is on {online_server}\n'
    else:
        display += f'{ign} is offline\n'
    display += 'Overall Statistics:\n'
    stat_list = []
    val_list = []
    for stat in overall_stats.keys():
        if stat == 'totalLevel':
            stat_list.append('Level')
        elif stat == 'itemsIdentified':
            stat_list.append('IQ')
        elif stat == 'eventsWon':
            stat_list.append('Descendant')
        else:
            stat_list.append(stat)
    for val in overall_stats.values():
        val_list.append(val)
    print(val_list)
    display += f'Blocks Walked: {val_list[0]}\n'
    display += f'Mobs Killed: {val_list[2]}\n'
    display += f'Logins: {val_list[5]}\n'
    pvp_kills = val_list[4].get('kills')
    pvp_deaths = val_list[4].get('deaths')
    display += f'Nether PvP: {pvp_kills} Kills & {pvp_deaths} Deaths\n'
    display += f'Deaths: {val_list[6]}\n'
    display += f'Raid Data: \n'
    display += '|           Raid           | Total Clears\n'
    display += f'|The Canyon Colossus       | {TCC_runs}\n'
    display += f'|Orphion\'s Nexus of Light  | {NOL_runs}\n'
    display += f'|The Nameless Anomaly      | {TNA_runs}\n'
    display += f'|Nest of the Grootslangs   | {NOG_runs}\n'
    display += '```'
    print(display)
    return display
