def get_guild(name):
    guild = requests.get(f'https://api.wynncraft.com/public_api.php?action=guildStats&command={name}')
    request_data = guild.json()
    key = request_data.keys()
    value = request_data.values()
    title = []
    stats = []

    for i in key:
        title.append(i)
    for j in value:
        stats.append(j)
    guild_name = stats[0]
    guild_prefix = stats[1]
    member_stats = stats[2]
    member_names = []
    member_ranks = []
    xp_contributed = []
    joined_date = []
    for player in member_stats:
        player_name = player.get('name')
        member_names.append(player_name)
        player_guild_rank = player.get('rank')
        member_ranks.append(player_guild_rank)
        player_uuid = player.get('uuid')
        player_xp = player.get('contributed')
        xp_contributed.append(player_xp)
        player_joined = player.get('joinedFriendly')
        joined_date.append(player_joined)
    index = 0
    owner_id = 0
    for member in member_ranks:
        if member == 'OWNER':
            owner_id = index
        else:
            index += 1
    return member_names, member_ranks, xp_contributed, joined_date, owner_id
  
  def guild_data(prefix):
    leaderboard = guild_leaderboard()
    full_name_list = leaderboard[0]
    prefix_list = leaderboard[1]
    guild_level = leaderboard[2]
    guild_created = leaderboard[3]
    war_count = leaderboard[4]
    member_count = leaderboard[5]
    index = 0
    val = 0
    for i in prefix_list:
        if i == prefix:
            val = index
        else:
            index += 1
    guild_name = full_name_list[val]
    guild_prefix = prefix_list[val]
    guild = get_guild(guild_name)
    names = guild[0]
    ranks = guild[1]
    xp = guild[2]
    joined = guild[3]
    owner = guild[4]
    level = guild_level[val]
    created = guild_created[val]
    war = war_count[val]
    member = member_count[val]
    return guild_name, guild_prefix, names, ranks, xp, joined, level, created, war, member, owner


def guilds(ctx):
    user_prefix = ctx
    data = guild_data(user_prefix)
    guild_name = data[0]
    guild_prefix = data[1]
    guild_members = data[2]
    member_names = []
    for name in guild_members:
        member_names.append(name)

    guild_player_ranks = data[3]
    xp_contribution = data[4]
    guild_contribution = {}
    # for name in member_names:
    #     for xp in xp_contribution:
    #         guild_contribution[name] = xp
    #         xp_contribution.remove(xp)
    #         break
    for i in range(len(member_names)):
        guild_contribution.update({member_names[i]: xp_contribution[i]})
    sorted_contribution = sorted(guild_contribution.items(), key=lambda x: x[1], reverse=True)
    xp_ranking = dict(sorted_contribution)
    show_top = 10
    place = 1
    joined_date = data[5]
    guild_level = data[6]
    guild_created = data[7]
    created_time = datetime.strptime(guild_created, '%Y-%m-%dT%H:%M:%S.%f%z')
    created_date = created_time.date()
    war_count = data[8]
    member_count = data[9]
    display = '```'
    display += f' {guild_name} | [{guild_prefix}]\n' + f' Owner: {guild_members[0]}\n'
    display += f' Created on {created_date}\n'
    display += f' Level: {guild_level}\n'
    display += f' War count: {war_count}\n'
    display += f' Members: {member_count}\n'
    display += f' XP contribution top 10: \n'
    for member in xp_ranking:
        if place <= show_top:
            xp_value = xp_ranking.get(member)
            display += f' {place}. {member} -> {xp_value} xp\n'
            place += 1
    display += '```'
    print(display)
