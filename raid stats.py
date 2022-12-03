def raid_stats(ign):
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
    game_info = data[4]
    characters_full = []
    each_class = game_info.values()
    char_raw = []
    raids = []
    index = 0
    raid_index = 0
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

    return NOG_runs, TCC_runs, NOL_runs, TNA_runs
