"""
Server-related utility functions for Nori bot.

This module contains functions for fetching server information,
uptime calculations, and soul point timers.
"""
import time
import requests
from datetime import timedelta
from typing import Dict, Tuple
from lib.config import WYNN_AUTH_HEADER


def get_server() -> Dict[str, list]:
    """
    Get current server player distribution.

    Returns:
        Dictionary mapping server names to lists of player IGNs
    """
    servers = requests.get(
        'https://api.wynncraft.com/v3/player',
        headers=WYNN_AUTH_HEADER
    )
    server_data = servers.json()["players"]
    online_data = {}
    
    for ign, server in server_data.items():
        if server not in online_data:
            online_data.update({server: []})
        online_data[server].append(ign)
    
    return online_data


def get_uptime() -> Dict[str, Tuple[str, str]]:
    """
    Get server uptime and soul point timer information.

    Returns:
        Dictionary mapping server names to (uptime, soul_timer) tuples
    """
    try:
        servers = requests.get("https://nori.fish/api/uptime")
        data = servers.json()['servers']
        world_uptime = {}
        
        for world in data:
            info = data[world]
            up = int(info.get('initial'))
            now = int(time.time())
            uptime_s = now - up
            uptime = str(timedelta(seconds=uptime_s))
            soul_point = 1200 - (uptime_s - 1200) % 1200
            soul_timer = str(timedelta(seconds=soul_point))
            world_uptime.update({world: (uptime, soul_timer)})
        
        return world_uptime
    except Exception as error:
        print(f"Error fetching uptime: {error}")
        return {}


def soul_timer() -> str:
    """
    Generate formatted soul point timer display.

    Returns:
        Formatted string showing soul point timers for all servers
    """
    index = 0
    showed_servers = 19
    server_list = get_server()
    server_time = get_uptime()
    
    timer = '```json\n'
    timer += '+----+--------+----------+------------+\n'
    timer += '| #  | Server | Players  | Soul Point |\n'
    timer += '+----+--------+----------+------------+\n'
    
    for server in sorted(server_list.items(), key=lambda x: server_time[x[0]][1]):
        if index <= showed_servers:
            world_id = server[0]
            player_count = len(server[1])
            uptime, soul_timer = server_time.get(world_id, ("N/A", "N/A"))
            timer += '| {:<2s} | {:<6s} | {:>5d}/50 | {:>10} |\n'.format(
                str(index + 1),
                world_id,
                player_count,
                soul_timer
            )
            index += 1
    
    timer += '+----+--------+----------+------------+\n'
    timer += '```'
    
    return timer

