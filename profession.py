def profession_leaderboard(prof):
    profession = prof
    server = requests.get(f'https://api.wynncraft.com/v2/leaderboards/player/solo/{profession}')
    prof_info = server.json()
    prof_rank = prof_info.get('data')
    names = []
    levels = []
    exp = []
    for info in prof_rank:
        name = info.get('name')
        names.append(name)
        rank_info = info.get('character')
        level = rank_info.get('level')
        xp = rank_info.get('xp')
        levels.append(level)
        exp.append(xp)
    names.reverse()
    levels.reverse()
    exp.reverse()
    display = '```'
    display += f'   {profession} Solo Ranking\n'
    display += ' #| Player Name          | Level |  Current XP\n'
    # display += '----------------------------------------------\n'
    for i in range(20):
        line = '{0:2d}| {1:20s} |  {2:3d}  | {3:11d}\n'.format(i + 1, names[i], levels[i], exp[i])
        display += line
    display += '```'
    print(display)
    return display
