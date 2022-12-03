import requests

def player_stats(ign):
    player_stat_raw = requests.get(f'https://api.wynncraft.com/v2/player/{ign}/stats')
    request_data = player_stat_raw.json()
    return request_data

def guild_leaderboard():
    timeframe = 'alltime'
    guild_lb = requests.get(f'https://api.wynncraft.com/public_api.php?action=statsLeaderboard&type=guild&timeframe={timeframe}')
    lb_data = guild_lb.json()
    return lb_data

def get_guild(name):
    guild = requests.get(f'https://api.wynncraft.com/public_api.php?action=guildStats&command={name}')
    request_data = guild.json()
    key = request_data.keys()
    value = request_data.values()
    return key, value
    
def get_server():
    servers = requests.get('https://api.wynncraft.com/public_api.php?action=onlinePlayers')
    server_data = servers.json()
    server_list = []
    player_list = []
    for world in server_data:
        if 'WC' in world:
            server_list.append(world)
    for val in server_data.values():
        if 'timestamp' in val:
            pass
        else:
            player_list.append(val)
    online_servers = {}
    for i in range(len(server_list)):
        players_on = len(player_list[i])
        online_servers.update({server_list[i]: players_on})
    return online_servers
