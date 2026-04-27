"""
Configuration and constants for Nori bot.

This module centralizes all configuration values, constants, and global state
variables used throughout the bot.
"""
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.expanduser('~/.env'))

# ============================================================================
# Bot Configuration
# ============================================================================
VERSION = "2.0.0"
DISPLAY_STATUS = "/nori"
MODE = "Production"
MODE_LIST = ["Development", "Testing", "Staging", "Production"]
ENGINE = "gpt-4-turbo"

# Runtime variables
deploy_time = time.time()
mode = MODE
engine = ENGINE
MODELS = [
    "gpt-4-turbo", "gpt-4", "gpt-4o", "gpt-3.5-turbo",
    "text-davinci-003", "text-babbage-001", "text-curie-001",
    "text-cushing-001", "text-edison-002", "gpt-4-vision-preview"
]

# ============================================================================
# API Keys and Tokens
# ============================================================================
AI_API_KEY = os.getenv('NORI_GPT_KEY')
BOT_TOKEN = os.getenv('NORI_TOKEN')
WYNN_SOURCE_TOKEN = os.getenv('WYNN_SOURCE_TOKEN')
WYNN_API_TOKEN = os.getenv("WYNN_BOT_TOKEN")
NORI_API_BASE_URL = os.getenv("NORI_API_BASE_URL", "https://nori.fish").rstrip("/")
NORI_API_USAGE_TOKEN = os.getenv("NORI_API_USAGE_TOKEN") or os.getenv("API_USAGE_TOKEN")

# WynnSource pool source-chain configuration (v2 -> beta -> optional v1)
WCS_POOL_PRIMARY_BASE_URL = os.getenv("WCS_POOL_PRIMARY_BASE_URL", "https://wcs.fyw.fyi").rstrip("/")
WCS_POOL_BETA_BASE_URL = os.getenv("WCS_POOL_BETA_BASE_URL", "https://wcs-beta.fyw.fyi").rstrip("/")
WCS_POOL_V1_BASE_URL = os.getenv("WCS_POOL_V1_BASE_URL", "https://wcs.fyw.fyi").rstrip("/")
# V1 fallback is ON by default for now. To turn it OFF set WCS_POOL_ENABLE_V1_FALLBACK=false.
WCS_POOL_ENABLE_V1_FALLBACK = os.getenv("WCS_POOL_ENABLE_V1_FALLBACK", "true").strip().lower() in {
    "1", "true", "yes", "on"
}
WCS_POOL_ALLOW_MISSING_REGIONS = os.getenv("WCS_POOL_ALLOW_MISSING_REGIONS", "true").strip().lower() not in {
    "0", "false", "no", "off"
}
WCS_POOL_TIMEOUT = int(os.getenv("WCS_POOL_TIMEOUT", "30"))

# Wynncraft API Headers
WYNN_AUTH_HEADER = {"Authorization": f"Bearer {WYNN_API_TOKEN}"} if WYNN_API_TOKEN else {}

# Flight Tracker Credentials
FLIGHT_USER_NAME = os.getenv('FLIGHT_USER_NAME', '')
FLIGHT_PASSWORD = os.getenv('FLIGHT_PASSWORD', '')

# ============================================================================
# Path Configuration
# ============================================================================
BASE_PATH = Path(__file__).parent.parent
DATA_PATH = Path(os.getenv("NORI_DATA_PATH", str(BASE_PATH / "data"))).expanduser()
BOT_PATH = Path(os.getenv("NORI_BOT_DATA_PATH", str(BASE_PATH / "bot"))).expanduser()
LOG_PATH = Path(os.getenv("NORI_LOG_PATH", str(BASE_PATH / "log"))).expanduser()
USER_IMG_PATH = Path(os.getenv("NORI_USER_IMG_PATH", str(BASE_PATH / "user_img"))).expanduser()
RESOURCES_PATH = BOT_PATH / "resources"
CHANGELOG_PATH = BOT_PATH / "changelog"
DATA_SCRIPTS_PATH = Path(os.getenv("NORI_DATA_SCRIPTS_PATH", str(BASE_PATH.parent / "data-scripts"))).expanduser()
DATA_SCRIPTS_GRAPHS_PATH = Path(os.getenv("NORI_DATA_SCRIPTS_GRAPHS_PATH", str(DATA_SCRIPTS_PATH / "graphs"))).expanduser()
DATA_SCRIPTS_DATABASE_PATH = Path(os.getenv("NORI_DATA_SCRIPTS_DATABASE_PATH", str(DATA_SCRIPTS_PATH / "database"))).expanduser()
DATA_SCRIPTS_FILES_PATH = Path(os.getenv("NORI_DATA_SCRIPTS_FILES_PATH", str(DATA_SCRIPTS_PATH / "files"))).expanduser()
SITE_DATA_PATH = Path(os.getenv("NORI_SITE_DATA_PATH", "/home/ubuntu/site-data")).expanduser()
LEADERBOARD_IN_GUILD_FILE = Path(
    os.getenv(
        "NORI_LEADERBOARD_IN_GUILD_FILE",
        os.getenv("LB_IN_GUILD_PATH", str(DATA_SCRIPTS_DATABASE_PATH / "leaderboard_in_guild.json")),
    )
).expanduser()
LEADERBOARD_IN_GUILD_API_URL = os.getenv("NORI_LEADERBOARD_IN_GUILD_API_URL", "").strip()
PLAYER_LEADERBOARD_FILE = Path(
    os.getenv("NORI_PLAYER_LEADERBOARD_FILE", str(DATA_SCRIPTS_DATABASE_PATH / "player_leaderboard.json"))
).expanduser()

# ============================================================================
# Time Constants
# ============================================================================
SECONDS_PER_WEEK = 604800
FIRST_WEEK_TIMESTAMP = 1690567200  # timestamp + 3600 if daylight saving
FIRST_WEEK_ASPECT_POOL = 1723222800  # + 3600 if daylight saving
IS_DST_NOW = time.localtime().tm_isdst > 0
DST_OFFSET = 3600 if IS_DST_NOW else 0

# Lootpool/aspect constants
GAMBIT_ROTATION_HOUR_ET = 13
GAMBIT_REFRESH_BASE_INTERVAL = 1800
GAMBIT_REFRESH_FAST_INTERVAL = 30
GAMBIT_REFRESH_FAST_WINDOW_BEFORE = 300
GAMBIT_REFRESH_FAST_WINDOW_AFTER = 600
GAMBIT_REFRESH_INTERVAL = GAMBIT_REFRESH_BASE_INTERVAL

LOOTPOOL_REFRESH_BURST_INTERVAL = 30
LOOTPOOL_REFRESH_BURST_DURATION = 600
LOOTPOOL_REFRESH_BASE_INTERVAL = 1800

RAID_POOL_REFRESH_BURST_INTERVAL = 30
RAID_POOL_REFRESH_BURST_DURATION = 600
RAID_POOL_REFRESH_BASE_INTERVAL = 1800

LOOTPOOL_REGIONS = ["SE", "Corkus", "Molten", "Sky", "Canyon", "FrumaEast", "FrumaWest"]
RAID_NAMES = ["TNA", "TCC", "NOL", "NOG", "TWP"]
LOOT_TIERS = ["Mythic", "Fabled", "Legendary", "Rare", "Unique", "Misc"]
ASPECT_TIERS = ["Mythic", "Fabled", "Legendary"]
RAID_ITEM_TIERS = ["Mythic", "Fabled", "Legendary", "Rare", "Unique", "Misc"]
GAMBIT_REGIONS = RAID_NAMES
RAID_WEB_URL = "https://nori.fish/wynn/raids"

WEEKLY_LOOTPOOL_FILE = DATA_PATH / "weekly_lootpool.json"
WEEKLY_ASPECT_POOL_FILE = DATA_PATH / "weekly_aspects.json"
WEEKLY_RAID_POOL_FILE = DATA_PATH / "weekly_raid_pool.json"
GAMBIT_POOL_FILE = DATA_PATH / "daily_gambits.json"
ITEM_LOOTPOOL_DEFAULT_FILE = DATA_PATH / "lootpool_default.json"
ASPECT_POOL_DEFAULT_FILE = DATA_PATH / "default_aspect_pool.json"
RAID_ITEM_POOL_DEFAULT_FILE = DATA_PATH / "default_raid_item_pool.json"

WARD_EMOJIS = {
    "Yellow Ward": "<:yellow_ward:1489621423113634022>",
    "White Ward": "<:white_ward:1489621422127976549>",
    "Red Ward": "<:red_ward:1489621420999704618>",
    "Purple Ward": "<:purple_ward:1489621420328747079>",
    "Pink Ward": "<:pink_ward:1489621419598938132>",
    "Orange Ward": "<:orange_ward:1489621418873196705>",
    "Green Ward": "<:green_ward:1489621418185588816>",
    "Cyan Ward": "<:cyan_ward:1489621417078296787>",
    "Blue Ward": "<:blue_ward:1489621416268791858>",
    "Black Ward": "<:black_ward:1489621415488520192>",
}

WARD_ICON_FILES = {
    "Yellow Ward": "yellow_ward.png",
    "White Ward": "white_ward.png",
    "Red Ward": "red_ward.png",
    "Purple Ward": "purple_ward.png",
    "Pink Ward": "pink_ward.png",
    "Orange Ward": "orange_ward.png",
    "Green Ward": "green_ward.png",
    "Cyan Ward": "cyan_ward.png",
    "Blue Ward": "blue_ward.png",
    "Black Ward": "black_ward.png",
}

MISC_ITEM_ICON_FILES = {
    "Liquid Emerald": "liquid_emerald.png",
    "Emerald Block": "emerald_block.png",
    "Emerald": "emerald.png",
    "Packed Crafter Bag [1/1]": "crafter_packed.png",
    "Stuffed Crafter Bag [1/1]": "crafter_stuffed.png",
    "Varied Crafter Bag [1/1]": "crafter_varied.png",
    "Corkian Insulator": "insulator.png",
    "Corkian Simulator": "simulator.png",
    "Tol Rune": "tol.png",
    "Uth Rune": "uth.png",
    "Nii Rune": "nii.png",
    "Az Rune": "az.png",
    "Ek Rune": "ek.png",
}

ASPECT_ANIM_EMOJIS = {
    "aspect_warrior.gif": "<a:aspect_warrior:1274305374417063956>",
    "aspect_mage.gif": "<a:aspect_mage:1274305357304565760>",
    "aspect_archer.gif": "<a:aspect_archer:1274305340959227971>",
    "aspect_assassin.gif": "<a:aspect_assassin:1274305350102945814>",
    "aspect_shaman.gif": "<a:aspect_shaman:1274305366011678793>",
}

ASPECT_STATIC_EMOJIS = {
    "static_warrior.png": "<:static_warrior:1274305305576079391>",
    "static_mage.png": "<:static_mage:1274305289491058743>",
    "static_archer.png": "<:static_archer:1274305243068497930>",
    "static_assassin.png": "<:static_assassin:1274305280351408238>",
    "static_shaman.png": "<:static_shaman:1274305297003057179>",
}


def format_ward_display(item_name: str) -> str:
    ward_emoji = WARD_EMOJIS.get(item_name)
    return f"{ward_emoji} {item_name}" if ward_emoji else item_name


def format_aspect_display(aspect_name: str, icon_name: str | None, use_static: bool = False) -> str:
    emoji_map = ASPECT_STATIC_EMOJIS if use_static else ASPECT_ANIM_EMOJIS
    emoji = emoji_map.get(icon_name or "") or WARD_EMOJIS.get(aspect_name, "")
    return f"{emoji} {aspect_name}" if emoji else aspect_name


def format_compacted_item_lines(items: list, formatter=None, prefix: str = "- ") -> list[str]:
    """Render item lines with duplicate compression while preserving order."""
    counts: dict[str, int] = {}
    for raw_item in items if isinstance(items, list) else []:
        if not isinstance(raw_item, str):
            continue
        item_name = raw_item.strip()
        if item_name:
            counts[item_name] = counts.get(item_name, 0) + 1

    lines: list[str] = []
    for item_name, count in counts.items():
        display = formatter(item_name) if callable(formatter) else item_name
        suffix = f" x{count}" if count > 1 else ""
        lines.append(f"{prefix}{display}{suffix}")
    return lines

# ============================================================================
# Global State Variables
# ============================================================================
# Note: These are initialized at runtime and managed by the bot
# deploy_time is set when bot starts, not here
task_index = 1
latest_period = []
lootpool_history = {}
lootpool_user = {}
item_map = {}
stat_mapping = {}
user_chat_histories = {}
bot_responses = {}
item_amp_data = {}
guild_prefix_data = {}
all_tasks = {}
build_data = {}
recipe_data = {}
help_data = {}
guild_prefixes = []
local_curve_data = {"user": "N/A"}
mini_game = {"logic": {"default_user": []}}
game_record = {
    "3x3": {"default_user": []},
    "4x4": {"default_user": []},
    "5x5": {"default_user": []}
}
lb_user_cache = {}
ign_list = []
aspect_user = {}
lootpool_data = {}
lootpool_icon = {}
aspect_data = {}
item_processed = {}
sales_data = {}
aspect_pool_data = {}
aspect_icon = {}
raid_item_pool_data = {}
raid_item_icon = {}
gambit_pool_data = []
gambit_refresh_started = False
item_db_refresh_started = False
lootpool_refresh_started = False
raid_pool_refresh_started = False
lb_in_guild = {}
user_lb_in_guild = {}

# Sensitive data - loaded from files at runtime
blocked_users = []
CONTRIBUTOR_ROLE_ID = os.getenv('CONTRIBUTOR_ROLE_ID')
LOG_CHANNEL_ID = os.getenv('LOG_CHANNEL_ID', '1167675251547717662')
COMMAND_LOG_CHANNEL_ID = int(os.getenv('COMMAND_LOG_CHANNEL_ID', '1109761057926426664'))
ITEM_DB_LOG_CHANNEL_ID = int(os.getenv('ITEM_DB_LOG_CHANNEL_ID', '1240536972007706686'))
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '322231571786629120'))
GPT_LOG_CHANNEL_ID = int(os.getenv('GPT_LOG_CHANNEL_ID', '1115061504283267123'))
DATA_MANAGER_ROLE_ID = int(os.getenv('DATA_MANAGER_ROLE_ID', '1160073663123570718'))
