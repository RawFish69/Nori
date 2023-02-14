class serverView(miru.View):
    @miru.button(emoji='⬇', style=hikari.ButtonStyle.PRIMARY)
    async def button_server(self, button: miru.Button, ctx: miru.Context):
        serverList = get_server()
        serverTime = get_uptime()
        index = 0
        response = '```json\n'
        response += '|All Online Servers:\n'
        response += '|------------------------------|\n'
        response += '| Server |   Players | Uptime  |\n'
        for server in serverList.items():
            world_ID = server[0]
            player_count = len(server[1])
            uptime = serverTime.get(world_ID)
            if player_count >= 50:
                response += '| {0:6s} | {1:6d}/50 | {2} | [Full]\n'.format(world_ID, player_count, uptime)
                index += 1
            else:
                response += '| {0:6s} | {1:6d}/50 | {2} |\n'.format(world_ID, player_count, uptime)
                index += 1
        response += '|------------------------------|\n'
        response += '```'
        await ctx.edit_response(response)

@bot.command
@lightbulb.command('uptime', 'List of online servers')
@lightbulb.implements(lightbulb.SlashCommand)
async def server_list(ctx):
    view = serverView(timeout=60)
    serverList = get_server()
    serverTime = get_uptime()
    index = 0
    show_servers = 10
    response = '```json\n'
    response += '|Online Servers:\n'
    response += '|------------------------------|\n'
    response += '| Server |   Players | Uptime  |\n'
    for server in serverList.items():
        if index <= show_servers:
            world_ID = server[0]
            player_count = len(server[1])
            uptime = serverTime.get(world_ID)
            if player_count >= 50:
                response += '| {0:6s} | {1:6d}/50 | {2} | [Full]\n'.format(world_ID, player_count, uptime)
                index += 1
            else:
                response += '| {0:6s} | {1:6d}/50 | {2} |\n'.format(world_ID, player_count, uptime)
                index += 1
    response += '|------------------------------|\n'
    response += '|Click for Full list of servers|\n'
    response += '```'
    display = await ctx.respond(f'{response}', components=view.build())
    display = await display
    view.start(display)
    await view.wait()


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


def get_uptime():
    servers = requests.get('https://athena.wynntils.com/cache/get/serverList')
    data = servers.json().get('servers')
    dataView = json.dumps(data, indent=3)
    world_uptime = {}
    for world in data:
        info = data.get(world)
        up = int(info.get('firstSeen') / 1000)
        now = int(time.time())
        uptime_s = now - up
        uptime = str(timedelta(seconds=uptime_s))
        world_uptime.update({world: uptime})
    return world_uptime

