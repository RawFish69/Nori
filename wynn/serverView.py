class serverView(miru.View):
    @miru.button(emoji='⬇', style=hikari.ButtonStyle.PRIMARY)
    async def button_server(self, button: miru.Button, ctx: miru.Context):
        serverList = get_server()
        serverTime = get_uptime()
        response = '```json\n'
        response += 'All Online Servers:\n'
        response += '+--------+----------+----------+------------+\n'
        response += '| Server | Players  | Uptime   | Soul Point |\n'
        response += '+--------+----------+----------+------------+\n'
        for server in sorted(serverList.items(), key=lambda x: serverTime[x[0]][0]):
            world_ID = server[0]
            player_count = len(server[1])
            uptime, soul_timer = serverTime.get(world_ID)
            if player_count >= 50:
                response += '| {:<6s} | {:>5d}/50 | {:>8} | {:>10} | [Full]\n'.format(world_ID, player_count, uptime,
                                                                                      soul_timer)
            else:
                response += '| {:<6s} | {:>5d}/50 | {:>8} | {:>10} |\n'.format(world_ID, player_count, uptime,
                                                                               soul_timer)
        response += '+--------+----------+----------+------------+\n'
        response += '```'
        await ctx.edit_response(response)

def get_online(ign):
    server_data = get_server()
    servers = server_data.keys()
    online_status = False
    online_server = 'Null'
    for world in servers:
        player_list = server_data[world]
        if ign in player_list:
            online_status = True
            online_server = world
        else:
            pass
    return online_status, online_server


def get_uptime():
    servers = requests.get('https://athena.wynntils.com/cache/get/serverList')
    data = servers.json()['servers']
    dataView = json.dumps(data, indent=3)
    world_uptime = {}
    for world in data:
        info = data[world]
        up = int(info['firstSeen'] / 1000)
        now = int(time.time())
        uptime_s = now - up
        uptime = str(timedelta(seconds=uptime_s))
        soul_point = 1200 - (uptime_s - 1200) % 1200
        soul_timer = str(timedelta(seconds=soul_point))
        world_uptime.update({world: (uptime, soul_timer)})
    return world_uptime

