class serverView(miru.View):
    @miru.button(emoji='⬇', style=hikari.ButtonStyle.PRIMARY)
    async def button_server(self, button: miru.Button, ctx: miru.Context):
        serverList = get_server()
        response = '```'
        response += '|All Online Servers:\n'
        response += '|------------------------------|\n'
        response += '| Server       |       Players |\n'
        for server in serverList.items():
            world_ID = server[0]
            player_count = len(server[1])
            if player_count >= 50:
                response += '| {0:12s} | {1:10d}/50 | [FULL]\n'.format(world_ID, player_count)
            else:
                response += '| {0:12s} | {1:10d}/50 |\n'.format(world_ID, player_count)
        response += '|------------------------------|\n'
        response += '|Full worlds need champion rank|\n'
        response += '```'
        await ctx.edit_response(response)


@bot.command
@lightbulb.command('wc', 'List of online servers')
@lightbulb.implements(lightbulb.SlashCommand)
async def server_list(ctx):
    view = serverView(timeout=60)
    serverList = get_server()
    index = 0
    show_servers = 10
    response = '```'
    response += '|Online Servers:\n'
    response += '|------------------------------|\n'
    response += '| Server       |       Players |\n'
    for server in serverList.items():
        if index <= show_servers:
            world_ID = server[0]
            player_count = len(server[1])
            if player_count >= 50:
                response += '| {0:12s} | {1:10d}/50 | [FULL]\n'.format(world_ID, player_count)
                index += 1
            else:
                response += '| {0:12s} | {1:10d}/50 |\n'.format(world_ID, player_count)
                index += 1
    response += '|------------------------------|\n'
    response += '|Click for Full list of servers|\n'
    response += '```'
    display = await ctx.respond(f'{response}', components=view.build())
    display = await display
    view.start(display)
    await view.wait()

    
def get_online(ign):
    server_data = get_server()
    servers = server_data.keys()
    online_status = False
    online_server = 'Null'
    for world in servers:
        player_list = server_data.get(world)
        if ign in player_list:
            online_status = True
            online_server = world
        else:
            pass
    return online_status, online_server


def get_server():
    servers = requests.get('https://api.wynncraft.com/public_api.php?action=onlinePlayers')
    server_data = servers.json()
    online_servers = []
    online_data = {}
    for world in server_data:
        if 'timestamp' in server_data.values():
            pass
        elif 'WC' in world:
            online_servers.append(world)
    for server in online_servers:
        server_players = server_data.get(server)
        online_data.update({server: server_players})
    return online_data
