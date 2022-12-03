def guild_leaderboard():
    timeframe = 'alltime'
    guild_lb = requests.get(
        f'https://api.wynncraft.com/public_api.php?action=statsLeaderboard&type=guild&timeframe={timeframe}')
    lb_data = guild_lb.json()
    value = lb_data.values()
    leaderboard = []
    guild_name = []
    guild_prefix = []
    guild_level = []
    guild_created = []
    guild_warcount = []
    guild_member_count = []
    for item in value:
        if 'timestamp' not in item and 'version' not in item:
            leaderboard = item
    for guild in leaderboard:
        name = guild.get('name')
        prefix = guild.get('prefix')
        level = guild.get('level')
        created = guild.get('created')
        war_count = guild.get('warCount')
        members_count = guild.get('membersCount')
        guild_name.append(name)
        guild_prefix.append(prefix)
        guild_level.append(level)
        guild_created.append(created)
        guild_warcount.append(war_count)
        guild_member_count.append(members_count)
    return guild_name, guild_prefix, guild_level, guild_created, guild_warcount, guild_member_count


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
