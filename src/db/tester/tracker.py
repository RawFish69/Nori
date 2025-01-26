#!/usr/bin/env python3

import time
import json
import logging
import requests
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta, timezone

SERVER_JSON_FILE_PATH = "your file path here"
ONLINE_ACTIVITY_JSON_FILE_PATH = "your file path here"
GRAPH_OUTPUT_DIRECTORY = "your directory path here"
SERVER_CHECK_INTERVAL_SECS = 30
PLOT_GENERATION_INTERVAL_SECS = 1800
LOG_FILE_PATH = "your file path here"
LOG_LEVEL = logging.INFO
CST = timezone(timedelta(hours=-5))

logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def load_initial_data(json_file_path: str) -> dict:
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            return data.get("servers", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def fetch_server_data() -> dict:
    try:
        url = "https://api.wynncraft.com/v3/player"
        response = requests.get(url)
        response.raise_for_status()
        if response.json().get("total", 0) >= 50:
            return response.json().get("players", {})
        else:
            beta_url = "https://beta-api.wynncraft.com/v3/player"
            beta_response = requests.get(beta_url)
            beta_response.raise_for_status()
            return beta_response.json().get("players", {})
    except requests.RequestException as e:
        logger.error(f"Failed to fetch server data: {e}")
        time.sleep(60)
        return None

def update_server_data(current_servers: dict, new_data: dict, json_file_path: str) -> dict:
    updated = False
    new_servers = {}
    for player, server in new_data.items():
        new_servers.setdefault(server, []).append(player)
    for server, players in new_servers.items():
        if server not in current_servers:
            current_servers[server] = {
                "initial": int(time.time()),
                "players": players
            }
            logger.info(f"Server {server} just started.")
            updated = True
        else:
            current_servers[server]["players"] = players
            updated = True
    dead_servers = [srv for srv in current_servers if srv not in new_servers]
    for srv in dead_servers:
        logger.info(f"Server {srv} has stopped.")
        del current_servers[srv]
        updated = True
    if updated:
        try:
            with open(json_file_path, "w") as file:
                json.dump(
                    {"servers": current_servers, "Latest": int(time.time())},
                    file,
                    indent=3
                )
            logger.debug("Server uptime data updated on disk.")
        except IOError as e:
            logger.error(f"Failed to write updated server data to disk: {e}")
    return current_servers

def player_activity():
    logger.info("Starting activity plot generation...")
    time_now = datetime.now(CST)
    current_datetime = time_now.strftime("%Y-%m-%d %H:%M:%S")
    current_date = time_now.strftime("%Y-%m-%d")

    try:
        with open(ONLINE_ACTIVITY_JSON_FILE_PATH, "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Could not read online activity data: {e}")
        return

    plot_configs = [
        {"entries": -24, "tick": 2, "title": current_datetime, "style": "o-", "filename": "latest_activity.png", "dark": True},
        {"entries": -24, "tick": 2, "title": current_datetime, "style": "o-", "filename": f"daily/{current_date}.png", "dark": False},
        {"entries": -72, "tick": 4, "title": "Past 3 Days", "style": ".-", "filename": "latest_3_day_activity.png", "dark": False},
        {"entries": -168, "tick": 8, "title": "Past 7 Days", "style": "-", "filename": "latest_weekly_activity.png", "dark": False},
        {"days": 30, "tick": 2, "title": "Past 30 Days", "style": "o-", "filename": "latest_monthly_activity.png", "dark": False},
        {"days": 90, "tick": 8, "title": "Past 3 Months", "style": "-", "filename": "last_3_months_activity.png", "dark": True},
        {"days": 180, "tick": 8, "title": "Past 6 Months", "style": "-", "filename": "last_6_months_activity.png", "dark": True},
        {"days": 365, "tick": 12, "title": "Past Year", "style": "-", "filename": "annual_activity.png", "dark": True}
    ]
    timestamps, online_players, new_players = [], [], []
    days = list(data.keys())
    
    for day in days:
        for timestamp_str, info in data[day].items():
            dt = datetime.strptime(f"{day} {timestamp_str}", "%Y-%m-%d %H:%M:%S")
            timestamps.append(dt.strftime("%m-%d %H:%M"))
            online_players.append(info["online"])
            new_players.append(info["new"])
    
    logger.info(f"Parsed {len(timestamps)} data points from {len(days)} days")

    def get_averaged_data(days_count):
        relevant_days = days[-days_count:]
        dates, avg_online, avg_new = [], [], []
        
        for day in relevant_days:
            day_online = [info["online"] for info in data[day].values()]
            day_new = [info["new"] for info in data[day].values()]
            if day_online and day_new:
                dates.append(day)
                avg_online.append(int(sum(day_online) / len(day_online)))
                avg_new.append(int(sum(day_new) / len(day_new)))
        
        return dates, avg_online, avg_new

    for config in plot_configs:
        if "days" in config:
            x_data, y_online, y_new = get_averaged_data(config["days"])
        else:
            x_data = timestamps[config["entries"]:]
            y_online = online_players[config["entries"]:]
            y_new = new_players[config["entries"]:]
        plot_func = dark_activity_plot if config["dark"] else activity_plot
        plot_func(
            x_data, y_online, y_new,
            tick=config["tick"],
            title=config["title"],
            line_style=config["style"],
            filename=config["filename"]
        )
    logger.info("Activity plot generation complete.")

def activity_plot(timestamps, online_players, new_players, tick, title, line_style, filename):
    plt.style.use('default')
    plt.figure(figsize=(12, 8))
    average_online = int(sum(online_players) / len(online_players)) if online_players else 0
    plt.plot(timestamps, online_players, line_style, color="blue", label='Online Players')
    plt.hlines(
        average_online, timestamps[0] if timestamps else 0, timestamps[-1] if timestamps else 1,
        colors="limegreen", linestyles="dashed",
        label=f"Average {average_online} Online"
    )
    plt.plot(timestamps, new_players, line_style, color='orange', label='New Players')
    plt.xticks([t for i, t in enumerate(timestamps) if i % tick == 0], rotation=45)
    plt.xlabel('Time')
    plt.ylabel('Number of Players')
    plt.title(f'Player Activity of {title}')
    plt.subplots_adjust(bottom=0.25)
    plt.legend(loc='lower left', bbox_to_anchor=(0, -0.35), fancybox=True, shadow=True, ncol=1)
    plt.text(
        1, -0.25,
        'TEST Plot',
        horizontalalignment='right',
        verticalalignment='top',
        transform=plt.gca().transAxes,
        fontsize=14,
        color='deepskyblue'
    )
    plt.grid(True)
    full_path = f"{GRAPH_OUTPUT_DIRECTORY}{filename}"
    plt.savefig(full_path)
    plt.close()
    logger.info(f"Image {filename} generated and saved to {full_path} [Default Theme].")

def dark_activity_plot(timestamps, online_players, new_players, tick, title, line_style, filename):
    plt.style.use('default')
    plt.rcParams['axes.facecolor'] = '#202020'
    plt.rcParams['figure.facecolor'] = '#333333'
    plt.rcParams['axes.edgecolor'] = 'white'
    plt.rcParams['axes.labelcolor'] = 'white'
    plt.rcParams['xtick.color'] = 'white'
    plt.rcParams['ytick.color'] = 'white'
    plt.rcParams['grid.color'] = 'gray'
    plt.rcParams['text.color'] = 'white'
    plt.figure(figsize=(12, 8))
    average_online = int(sum(online_players) / len(online_players)) if online_players else 0
    plt.plot(timestamps, online_players, line_style, color="cyan", label='Online Players', linewidth=2)
    plt.hlines(
        average_online,
        timestamps[0] if timestamps else 0,
        timestamps[-1] if timestamps else 1,
        colors="limegreen", linestyles="dashed",
        label=f"Average {average_online} Online", linewidth=2
    )
    plt.plot(timestamps, new_players, line_style, color='orange', label='New Players', linewidth=2)
    plt.xticks([t for i, t in enumerate(timestamps) if i % tick == 0], rotation=45)
    plt.xlabel('Time')
    plt.ylabel('Number of Players')
    plt.title(f'Player Activity of {title}')
    plt.subplots_adjust(bottom=0.25)
    plt.legend(loc='lower left', bbox_to_anchor=(0, -0.35), fancybox=True, shadow=True, ncol=1)
    plt.text(
        1, -0.25,
        'TEST Plot',
        horizontalalignment='right',
        verticalalignment='top',
        transform=plt.gca().transAxes,
        fontsize=14
    )
    plt.grid(True)
    full_path = f"{GRAPH_OUTPUT_DIRECTORY}{filename}"
    plt.savefig(full_path)
    plt.close()
    logger.info(f"Image {filename} generated and saved to {full_path} [Dark Theme].")

def main():
    logger.info("Starting merged server uptime and plot generation script...")
    current_servers = load_initial_data(SERVER_JSON_FILE_PATH)
    if not current_servers:
        logger.info("No existing server data found. Starting fresh...")
    last_plot_generation = time.time()
    while True:
        data = fetch_server_data()
        if data:
            current_servers = update_server_data(current_servers, data, SERVER_JSON_FILE_PATH)
        now = time.time()
        if now - last_plot_generation >= PLOT_GENERATION_INTERVAL_SECS:
            try:
                player_activity()
                logger.info("Player activity plots successfully generated.")
            except Exception as e:
                logger.error(f"Failed to generate player activity plots: {e}")
            last_plot_generation = now
        time.sleep(SERVER_CHECK_INTERVAL_SECS)

if __name__ == '__main__':
    main()
