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
