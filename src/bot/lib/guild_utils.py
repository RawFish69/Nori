"""
Guild-related utility functions for Nori bot.

This module contains functions for fetching, processing, and displaying
guild statistics and information.
"""
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from lib.wynn_api import Guild
from lib.utils import format_xp


def guild_stats(user_input: str) -> Optional[Tuple[str, str, str, str, str]]:
    """
    Fetch and format guild statistics.

    Args:
        user_input: Guild prefix or name

    Returns:
        Tuple containing (display_string, guild_name, guild_prefix, banner_tier, banner_structure)
        Returns None if guild not found
    """
    try:
        display = ""
        guild = Guild()
        guild_data = guild.get_guild_data(user_input)
        
        if not guild_data:
            return None
            
        created_time = datetime.strptime(guild_data["created"], '%Y-%m-%dT%H:%M:%S.%fZ')
        created_date = created_time.date()
        online_players = {}
        guild_members = guild_data["members"]
        ranks = ["owner", "chief", "strategist", "captain", "recruiter", "recruit"]
        rank_map = {
            "owner": "*****",
            "chief": "****",
            "strategist": "***",
            "captain": "**",
            "recruiter": "*",
            "recruit": ""
        }
        
        for rank in ranks:
            for player in guild_members[rank]:
                if guild_members[rank][player]["online"] is True:
                    guild_rank = guild_members[rank]
                    rank_display = rank_map[rank]
                    online_players[player] = {
                        "Server": guild_rank[player]["server"],
                        "Rank": rank_display
                    }

        display += f"{guild_data['name']} [{guild_data['prefix']}]\n"
        display += f'Owner: {list(guild_data["members"]["owner"].keys())[0]}\n'
        display += f'Created on {created_date}\n'
        display += f'Level: {guild_data["level"]} [{guild_data["xpPercent"]}%]\n'
        display += f'War count: {guild_data["wars"] if guild_data["wars"] else 0}\n'
        display += f'Territory count: {guild_data["territories"]}\n'
        display += f'Members: {guild_data["members"]["total"]}\n'
        display += f'Online Players: {len(online_players)}/{guild_data["members"]["total"]}\n'

        if online_players:
            max_name_length = 0
            for name in online_players.keys():
                if len(name) > max_name_length:
                    max_name_length = len(name)

            max_server_length = 0
            for player in online_players.values():
                if len(player["Server"]) > max_server_length:
                    max_server_length = len(player["Server"])

            display += '╔' + '═' * (max_server_length + 2) + '╦' + '═' * (max_name_length + 2) + '╦═══════╗\n'
            display += '║ ' + "WC".center(max_server_length) + ' ║ ' + "Player".center(
                max_name_length) + ' ║ Rank  ║\n'
            display += '╠' + '═' * (max_server_length + 2) + '╬' + '═' * (max_name_length + 2) + '╬═══════╣\n'

            for player, data in online_players.items():
                display += f'║ {data["Server"].center(max_server_length)} ║ {player.center(max_name_length)} ║ {data["Rank"]:5} ║\n'

            display += '╚' + '═' * (max_server_length + 2) + '╩' + '═' * (max_name_length + 2) + '╩═══════╝\n'
        
        print(display)
        
        if guild_data["banner"]:
            if "tier" in guild_data["banner"] and "structure" in guild_data["banner"]:
                return (
                    display,
                    guild_data["name"],
                    guild_data["prefix"],
                    guild_data["banner"]["tier"],
                    guild_data["banner"]["structure"]
                )
            else:
                return (
                    display,
                    guild_data["name"],
                    guild_data["prefix"],
                    guild_data["banner"]["tier"],
                    "No structure"
                )
        else:
            print("No banner info")
            return (
                display,
                guild_data["name"],
                guild_data["prefix"],
                "0 tier",
                "No structure"
            )
    except Exception as error:
        print(f"Error fetching guild stats: {error}")
        return None


def xp_list(user_input: str) -> str:
    """
    Generate formatted XP contribution list for a guild.

    Args:
        user_input: Guild prefix or name

    Returns:
        Formatted string displaying top contributors
    """
    guild = Guild()
    guild_contribution = guild.get_guild_member_contribution(user_input)
    sorted_contribution = sorted(guild_contribution.items(), key=lambda x: x[1], reverse=True)
    xp_ranking = dict(sorted_contribution)

    show_top = 15
    place = 1

    max_name_length = max(17, max(len(name) for name in xp_ranking.keys()))
    max_xp_length = 5
    max_exact_xp_length = 8
    
    for xp_value in xp_ranking.values():
        formatted_xp = format_xp(xp_value)
        max_xp_length = max(max_xp_length, len(formatted_xp))
        max_exact_xp_length = max(max_exact_xp_length, len(str(xp_value)))

    display = '```json\n'
    display += '╔════╦' + '═' * (max_name_length + 2) + '╦' + '═' * (max_xp_length + 2) + '╦' + '═' * (
            max_exact_xp_length + 2) + '╗\n'
    display += '║  # ║ Player' + ' ' * (max_name_length - 5) + '║  XP' + ' ' * (
            max_xp_length - 2) + '║ Exact XP' + ' ' * (max_exact_xp_length - 7) + '║\n'

    for member in xp_ranking:
        if place <= show_top:
            xp_value = xp_ranking[member]
            formatted_xp = format_xp(xp_value)
            display += '╟ {0:2} ║ {1:{2}} ║ {3:>{4}} ║ {5:>{6}} ║\n'.format(
                place,
                member,
                max_name_length,
                formatted_xp,
                max_xp_length,
                xp_value,
                max_exact_xp_length
            )
            place += 1

    display += '╚════╩' + '═' * (max_name_length + 2) + '╩' + '═' * (max_xp_length + 2) + '╩' + '═' * (
            max_exact_xp_length + 2) + '╝\n'
    display += '```'
    print(display)
    return display

