class raidView(miru.View):
    @miru.button(label='TNA', style=hikari.ButtonStyle.PRIMARY)
    async def button_next(self, button: miru.Button, ctx: miru.Context):
        guild_name = guild_temporary
        await ctx.edit_response(f'Processing TNA Leaderboard for [{guild_name}]...')
        TNA_ranking = TNA_leaderboard(guild_name)
        names = []
        places_show = 1
        for player in TNA_ranking.keys():
            names.append(player)
        if len(names) >= 20:
            places_show = 20
        else:
            places_show = len(names)
        display = '```json\n'
        display += ' Wynncraft Raid\n'
        display += ' The Nameless Anomaly [Lv. 103+]\n'
        display += f' TNA Leaderboard in [{guild_name}]\n'
        display += f' #| Player               | Clears\n'
        for index in range(places_show):
            name = names[index]
            clears = TNA_ranking.get(name)
            display += '{0:2d}| {1:20s} | {2:d}\n'.format(index + 1, name, clears)
        display += '```'
        await ctx.edit_response(display)

    @miru.button(label='TCC', style=hikari.ButtonStyle.PRIMARY)
    async def button_tcc(self, button: miru.Button, ctx: miru.Context):
        guild_name = guild_temporary
        await ctx.edit_response(f'Processing TCC Leaderboard for [{guild_name}]')
        TCC_ranking = TCC_leaderboard(guild_name)
        names = []
        places_show = 1
        for player in TCC_ranking.keys():
            names.append(player)
        if len(names) >= 20:
            places_show = 20
        else:
            places_show = len(names)
        display = '```json\n'
        display += ' Wynncraft Raid\n'
        display += ' The Canyon Colossus [Lv. 95+]\n'
        display += f' TCC Leaderboard in [{guild_name}]\n'
        display += f' #| Player               | Clears\n'
        for index in range(places_show):
            name = names[index]
            clears = TCC_ranking.get(name)
            display += '{0:2d}| {1:20s} | {2:d}\n'.format(index + 1, name, clears)
        display += '```'
        await ctx.edit_response(display)

    @miru.button(label='NoL', style=hikari.ButtonStyle.PRIMARY)
    async def button_nol(self, button: miru.Button, ctx: miru.Context):
        guild_name = guild_temporary
        await ctx.edit_response(f'Processing NoL Leaderboard for [{guild_name}]')
        NOL_ranking = NOL_leaderboard(guild_name)
        names = []
        places_show = 1
        for player in NOL_ranking.keys():
            names.append(player)
        if len(names) >= 20:
            places_show = 20
        else:
            places_show = len(names)
        display = '```json\n'
        display += ' Wynncraft Raid\n'
        display += ' Nexus of Light [Lv. 80+]\n'
        display += f' NOL Leaderboard in [{guild_name}]\n'
        display += f' #| Player               | Clears\n'
        for index in range(places_show):
            name = names[index]
            clears = NOL_ranking.get(name)
            display += '{0:2d}| {1:20s} | {2:d}\n'.format(index + 1, name, clears)
        display += '```'
        await ctx.edit_response(display)

    @miru.button(label='NoG', style=hikari.ButtonStyle.PRIMARY)
    async def button_NOG(self, button: miru.Button, ctx: miru.Context):
        guild_name = guild_temporary
        await ctx.edit_response(f'Processing NoG Leaderboard for [{guild_name}]')
        NOG_ranking = NOG_leaderboard(guild_name)
        names = []
        places_show = 1
        for player in NOG_ranking.keys():
            names.append(player)
        if len(names) >= 20:
            places_show = 20
        else:
            places_show = len(names)
        display = '```json\n'
        display += ' Wynncraft Raid\n'
        display += ' Nest of the Grootslang [Lv. 54+]\n'
        display += f' NOG Leaderboard in [{guild_name}]\n'
        display += f' #| Player               | Clears\n'
        for index in range(places_show):
            name = names[index]
            clears = NOG_ranking.get(name)
            display += '{0:2d}| {1:20s} | {2:d}\n'.format(index + 1, name, clears)
        display += '```'
        await ctx.edit_response(display)

    @miru.button(label='xp', style=hikari.ButtonStyle.SUCCESS, row=2)
    async def button_xp(self, button: miru.Button, ctx: miru.Context):
        guild_name = guild_temporary
        display = xp_list(guild_name)
        await ctx.edit_response(display)

    @miru.button(label='menu', style=hikari.ButtonStyle.SUCCESS, row=2)
    async def button_back(self, button: miru.Button, ctx: miru.Context):
        guild_name = guild_temporary
        msg = '```json\n'
        msg += 'Wynncraft Raid Report [beta]\n'
        msg += 'Information:\n'
        msg += '1. TNA - The Nameless Anomaly\n'
        msg += '2. TCC - The Canyon Colossus\n'
        msg += '3. NoL - Nexus of Light\n'
        msg += '4. NoG - Nest of the Grootslangs\n'
        msg += f"Select a leaderboard for guild [{guild_name}]```"
        await ctx.edit_response(msg)



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


def TNA_leaderboard(ctx):
    names = guild_data(ctx)[2]
    player_list = []
    TNA_runs = []
    TNA_stats = {}
    for player in names:
        try:
            TNA_count = raid_stats(player)[3]
            if TNA_count >= 0:
                TNA_runs.append(TNA_count)
                player_list.append(player)
        except IndexError:
            print('Invalid player')
            pass
    for i in range(len(TNA_runs)):
        TNA_stats.update({player_list[i]: TNA_runs[i]})
    sorted_ranking = sorted(TNA_stats.items(), key=lambda x: x[1], reverse=True)
    TNA_ranking = dict(sorted_ranking)
    return TNA_ranking


def NOL_leaderboard(ctx):
    names = guild_data(ctx)[2]
    player_list = []
    NOL_runs = []
    NOL_stats = {}
    for player in names:
        try:
            NOL_count = raid_stats(player)[2]
            if NOL_count >= 0:
                NOL_runs.append(NOL_count)
                player_list.append(player)
        except IndexError:
            print('Invalid player')
            pass
    for i in range(len(NOL_runs)):
        NOL_stats.update({player_list[i]: NOL_runs[i]})
    sorted_ranking = sorted(NOL_stats.items(), key=lambda x: x[1], reverse=True)
    NOL_ranking = dict(sorted_ranking)
    return NOL_ranking


def TCC_leaderboard(ctx):
    names = guild_data(ctx)[2]
    player_list = []
    TCC_runs = []
    TCC_stats = {}
    for player in names:
        try:
            TCC_count = raid_stats(player)[1]
            if TCC_count >= 0:
                TCC_runs.append(TCC_count)
                player_list.append(player)
        except IndexError:
            print('Invalid player')
            pass
    for i in range(len(TCC_runs)):
        TCC_stats.update({player_list[i]: TCC_runs[i]})
    sorted_ranking = sorted(TCC_stats.items(), key=lambda x: x[1], reverse=True)
    TCC_ranking = dict(sorted_ranking)
    return TCC_ranking


def NOG_leaderboard(ctx):
    names = guild_data(ctx)[2]
    player_list = []
    NOG_runs = []
    NOG_stats = {}
    for player in names:
        try:
            NOG_count = raid_stats(player)[0]
            if NOG_count >= 0:
                NOG_runs.append(NOG_count)
                player_list.append(player)
        except IndexError:
            print('Invalid player')
            pass
    for i in range(len(NOG_runs)):
        NOG_stats.update({player_list[i]: NOG_runs[i]})
    sorted_ranking = sorted(NOG_stats.items(), key=lambda x: x[1], reverse=True)
    NOG_ranking = dict(sorted_ranking)
    return NOG_ranking
