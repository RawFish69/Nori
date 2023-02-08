@leaderboard.child()
@lightbulb.option('guild', 'Prefix of the guild')
@lightbulb.command('tna', 'The Nameless Anomaly')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def TNA_lb(ctx):
    await ctx.respond('Processing leaderboard data...')
    guild_name = ctx.options.guild
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
    display += f' TNA Leaderboard in [{guild_name}]\n'
    display += f' #| Player               | Clears\n'
    for index in range(places_show):
        name = names[index]
        clears = TNA_ranking.get(name)
        display += '{0:2d}| {1:20s} | {2:d}\n'.format(index + 1, name, clears)
    display += '```'
    await ctx.edit_last_response(display)


@leaderboard.child()
@lightbulb.option('guild', 'Prefix of the guild')
@lightbulb.command('tcc', 'The Nameless Anomaly')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def TCC_lb(ctx):
    await ctx.respond('Processing leaderboard data...')
    guild_name = ctx.options.guild
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
    display += f' TCC Leaderboard in [{guild_name}]\n'
    display += f' #| Player               | Clears\n'
    for index in range(places_show):
        name = names[index]
        clears = TCC_ranking.get(name)
        display += '{0:2d}| {1:20s} | {2:d}\n'.format(index + 1, name, clears)
    display += '```'
    await ctx.edit_last_response(display)


@leaderboard.child()
@lightbulb.option('guild', 'Prefix of the guild')
@lightbulb.command('nol', 'The Nameless Anomaly')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def NOL_lb(ctx):
    await ctx.respond('Processing leaderboard data...')
    guild_name = ctx.options.guild
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
    display += f' NOL Leaderboard in [{guild_name}]\n'
    display += f' #| Player               | Clears\n'
    for index in range(places_show):
        name = names[index]
        clears = NOL_ranking.get(name)
        display += '{0:2d}| {1:20s} | {2:d}\n'.format(index + 1, name, clears)
    display += '```'
    await ctx.edit_last_response(display)


@leaderboard.child()
@lightbulb.option('guild', 'Prefix of the guild')
@lightbulb.command('nog', 'The Nameless Anomaly')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def NOG_lb(ctx):
    await ctx.respond('Processing leaderboard data...')
    guild_name = ctx.options.guild
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
    display += f' NOG Leaderboard in [{guild_name}]\n'
    display += f' #| Player               | Clears\n'
    for index in range(places_show):
        name = names[index]
        clears = NOG_ranking.get(name)
        display += '{0:2d}| {1:20s} | {2:d}\n'.format(index + 1, name, clears)
    display += '```'
    await ctx.edit_last_response(display)
