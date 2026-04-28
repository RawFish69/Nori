"""Shared leaderboard cache loaders."""

import json
from urllib.request import Request, urlopen

from lib.config import LEADERBOARD_IN_GUILD_API_URL, LEADERBOARD_IN_GUILD_FILE


def _read_json_file(path, default):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return default


def _read_json_url(url: str, default):
    if not url:
        return default
    try:
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "nori-bot/2.1.0"})
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as error:
        print(f"Error loading JSON from {url}: {error}")
        return default


def load_leaderboard_in_guild():
    """Load in-guild leaderboard data from API when configured, then file fallback."""
    api_data = _read_json_url(LEADERBOARD_IN_GUILD_API_URL, None)
    if isinstance(api_data, dict) and api_data:
        print(f"Leaderboard data loaded from API: {LEADERBOARD_IN_GUILD_API_URL}")
        return api_data

    file_data = _read_json_file(LEADERBOARD_IN_GUILD_FILE, None)
    if isinstance(file_data, dict):
        print(f"Leaderboard data loaded from {LEADERBOARD_IN_GUILD_FILE}")
        return file_data

    print(
        "Leaderboard in-guild data unavailable. "
        f"Set NORI_LEADERBOARD_IN_GUILD_FILE or NORI_LEADERBOARD_IN_GUILD_API_URL. "
        f"Tried file: {LEADERBOARD_IN_GUILD_FILE}"
    )
    return {}
