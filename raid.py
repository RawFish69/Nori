# Sample code for leaderboard display
@bot.command
@lightbulb.command('lb', 'Leaderboard')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def leaderboard(ctx):
    pass

@leaderboard.child()
@lightbulb.option('guild', 'Prefix of the guild')
@lightbulb.command('tna', 'The Nameless Anomaly')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def TNA_lb(ctx):
    await ctx.respond('Processing leaderboard data...')
    guild_name = ctx.options.guild
    TNA_ranking = TNA_leaderboard(guild_name)
    names = []
    places_show = 20
    for player in TNA_ranking.keys():
        names.append(player)
    display = '```'
    display += f'TNA Leaderboard in [{guild_name}]\n'
    display += f' #| Player               | Clears\n'
    for index in range(places_show):
        name = names[index]
        clears = TNA_ranking.get(name)
        display += '{0:2d}| {1:20s} | {2:d}\n'.format(index + 1, name, clears)
    display += '```'
    await ctx.edit_last_response(display)


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
