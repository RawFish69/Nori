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
VERSION = "1.4.0"
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
WYNN_AUTH_HEADER = {
    "Authorization": f"Bearer {WYNN_API_TOKEN}"
}

# ============================================================================
# Path Configuration
# ============================================================================
BASE_PATH = Path(__file__).parent.parent
DATA_PATH = BASE_PATH / "data"
BOT_PATH = BASE_PATH / "bot"
LOG_PATH = BASE_PATH / "log"
USER_IMG_PATH = BASE_PATH / "user_img"
RESOURCES_PATH = BOT_PATH / "resources"
CHANGELOG_PATH = BOT_PATH / "changelog"
DATA_SCRIPTS_PATH = BASE_PATH.parent / "data-scripts"
DATA_SCRIPTS_GRAPHS_PATH = DATA_SCRIPTS_PATH / "graphs"
DATA_SCRIPTS_DATABASE_PATH = DATA_SCRIPTS_PATH / "database"
DATA_SCRIPTS_FILES_PATH = DATA_SCRIPTS_PATH / "files"
SITE_DATA_PATH = Path("/home/ubuntu/site-data")

# ============================================================================
# Time Constants
# ============================================================================
SECONDS_PER_WEEK = 604800
FIRST_WEEK_TIMESTAMP = 1690567200  # timestamp + 3600 if daylight saving
FIRST_WEEK_ASPECT_POOL = 1723222800  # + 3600 if daylight saving
IS_DST_NOW = time.localtime().tm_isdst > 0
DST_OFFSET = 3600 if IS_DST_NOW else 0

# Lootpool/aspect constants
LOOTPOOL_REGIONS = ["SE", "Corkus", "Molten", "Sky", "Canyon", "FrumaEast", "FrumaWest"]
RAID_NAMES = ["TNA", "TCC", "NOL", "NOG", "TWP"]
LOOT_TIERS = ["Mythic", "Fabled", "Legendary", "Rare", "Unique"]
ASPECT_TIERS = ["Mythic", "Fabled", "Legendary"]

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
lb_in_guild = {}
user_lb_in_guild = {}

# Sensitive data - loaded from files at runtime
blocked_users = []
CONTRIBUTOR_ROLE_ID = os.getenv('CONTRIBUTOR_ROLE_ID')
LOG_CHANNEL_ID = os.getenv('LOG_CHANNEL_ID')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '322231571786629120'))
GPT_LOG_CHANNEL_ID = int(os.getenv('GPT_LOG_CHANNEL_ID', '1115061504283267123'))
DATA_MANAGER_ROLE_ID = int(os.getenv('DATA_MANAGER_ROLE_ID', '1160073663123570718'))
