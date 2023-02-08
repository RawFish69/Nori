@bot.command
@lightbulb.option('name', 'Guild Prefix')
@lightbulb.command('guild', 'Search a Guild\'s Stats')
@lightbulb.implements(lightbulb.SlashCommand)
async def guild(ctx):
    await ctx.respond('Processing guild data...')
    # view = guildView(timeout=60)
    user_prefix = ctx.options.name
    data = guild_data(user_prefix)
    display = '```json\n'
    try:
        guild_name = data[0]
        guild_prefix = data[1]
        guild_members = data[2]
        member_names = []
        for name in guild_members:
            member_names.append(name)
        guild_player_ranks = data[3]
        joined_date = data[5]
        guild_level = data[6]
        guild_created = data[7]
        created_time = datetime.strptime(guild_created, '%Y-%m-%dT%H:%M:%S.%f%z')
        created_date = created_time.date()
        war_count = data[8]
        member_count = data[9]
        owner_id = data[10]
        online_members = data[11]
        online_ranks = data[12]
        display_rank = []
        for rank in online_ranks:
            if rank == 'RECRUIT':
                display_rank.append('-')
            elif rank == 'RECRUITER':
                display_rank.append('*')
            elif rank == 'CAPTAIN':
                display_rank.append('**')
            elif rank == 'STRATEGIST':
                display_rank.append('***')
            elif rank == 'CHIEF':
                display_rank.append('****')
            elif rank == 'OWNER':
                display_rank.append('*****')
        online_servers = data[13]

        display += 'Guild Statistics:\n'
        display += f'{guild_name} | [{guild_prefix}]\n' + f'Owner: {guild_members[owner_id]}\n'
        display += f'Created on {created_date}\n'
        display += f'Level: {guild_level}\n'
        display += f'War count: {war_count}\n'
        display += f'Members: {member_count}\n'
        # for member in xp_ranking:
        #     if place <= show_top:
        #         xp_value = xp_ranking.get(member)
        #         display += f' {place}. {member} -> {xp_value} xp\n'
        #         place += 1
        display += f'Online Players: {len(online_members)}/{member_count} \n'
        display += f'WC  | Player           | Rank\n'
        for i in range(len(online_members)):
            display += '{0:4s}| {1:16s} | {2:s}\n'.format(online_servers[i], online_members[i], display_rank[i])
        display += '```'
    except ValueError:
        display += 'Cannot find target guild\n'
        display += 'Please enter a valid name or prefix```'
    print(display)
    await ctx.edit_last_response(display)
    # msg = await ctx.edit_last_response(f"{display}", components=view.build())
    # view.start(msg)
    # await view.wait()


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
    guild_level = stats[3]
    guild_created = stats[5]
    member_names = []
    member_ranks = []
    xp_contributed = []
    joined_date = []
    member_uuid = []
    for player in member_stats:
        player_name = player.get('name')
        member_names.append(player_name)
        player_guild_rank = player.get('rank')
        member_ranks.append(player_guild_rank)
        player_uuid = player.get('uuid')
        member_uuid.append(player_uuid)
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
    return member_names, member_ranks, xp_contributed, joined_date, owner_id, member_uuid, guild_level, guild_created, guild_prefix



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
    found = False
    found_result = False
    guild = ''
    guild_name = ''
    guild_prefix = ''
    names = []
    ranks = []
    xp = []
    joined = []
    level = ''
    created = ''
    war = ''
    member = []
    owner = ''
    online_players = []
    online_ranks = []
    online_servers = []
    for name in prefix_list:
        if prefix.lower() == name.lower():
            val = index
            found = True
        else:
            index += 1
    if found == False:
        index = 0
        for name in full_name_list:
            if prefix.lower() == name.lower():
                val = index
                found = True
                found_result = True
            else:
                index += 1
    if found == False and found_result == False:
        try:
            guild_stats = get_guild(prefix)
            print(guild_stats)
            guild_name = prefix
            guild_prefix = guild_stats[8]
            names = guild_stats[0]
            ranks = guild_stats[1]
            xp = guild_stats[2]
            joined = guild_stats[3]
            owner = guild_stats[4]
            level = guild_stats[6]
            created = guild_stats[7]
            war = 'null'
            member = len(names)
            server_data = get_server()
            worlds = server_data.keys()
            for server in worlds:
                players_on = server_data.get(server)
                for i in range(len(names)):
                    player = names[i]
                    if player in players_on:
                        print(f'{player} is on {server}')
                        online_players.append(player)
                        online_servers.append(server)
                        online_ranks.append(ranks[i])
        except IndexError:
            empty = ['','','','','','','','','','','','']
            return empty
    elif found == True:
        guild_name = full_name_list[val]
        guild_prefix = prefix_list[val]
        guild = get_guild(guild_name)
        names = guild[0]
        ranks = guild[1]
        xp = guild[2]
        joined = guild[3]
        owner = guild[4]
        uuid_list = guild[5]
        level = guild_level[val]
        created = guild_created[val]
        war = 'null'
        member = member_count[val]
        server_data = get_server()
        worlds = server_data.keys()
        for server in worlds:
            players_on = server_data.get(server)
            for i in range(len(names)):
                player = names[i]
                if player in players_on:
                    print(f'{player} is on {server}')
                    online_players.append(player)
                    online_servers.append(server)
                    online_ranks.append(ranks[i])
    return guild_name, guild_prefix, names, ranks, xp, joined, level, created, war, member, owner, online_players, online_ranks, online_servers


def xp_list(ctx):
    user_prefix = ctx
    data = guild_data(user_prefix)
    guild_members = data[2]
    xp_contribution = data[4]
    guild_contribution = {}
    for i in range(len(guild_members)):
        guild_contribution.update({guild_members[i]: xp_contribution[i]})
    sorted_contribution = sorted(guild_contribution.items(), key=lambda x: x[1], reverse=True)
    xp_ranking = dict(sorted_contribution)
    show_top = 40
    place = 1
    display = '```json\n'
    display += f' Guild XP contribution: \n'
    display += f' #| Player               | XP\n'
    for member in xp_ranking:
        if place <= show_top:
            xp_value = xp_ranking.get(member)
            display += '{0:2d}| {1:20s} | {2:d} xp\n'.format(place, member, xp_value)
            place += 1
    display += '```'
    return display

