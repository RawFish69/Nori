from fastapi import FastAPI, Request, Depends, HTTPException, Cookie, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from typing import List, Optional
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import os
import logging
import time
import httpx
from jose import jwt, JWTError
import secrets
import asyncio


log_filename = "/home/ubuntu/site-data/traffic.log"
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(message)s')

load_dotenv(os.path.expanduser('/home/ubuntu/.env'))
import wynntilsresolver

WYNNTOKEN = os.getenv("WYNN_API_TOKEN")
if not WYNNTOKEN:
    raise RuntimeError("Missing WYNNTOKEN in environment variables")
AUTH_HEADERS = {
    "Authorization": f"Bearer {WYNNTOKEN}"
}

SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_urlsafe(32))
ALGORITHM = "HS256"

app = FastAPI()

# Initialize the rate limiter
limiter = Limiter(key_func=get_remote_address)

# Register the rate limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

AI_API_KEY = os.getenv('GPT_KEY')

engine = "gpt-4" #gpt-4, gpt-4-vision-preview
item_map = {}
item_weights = {}
item_ranked = {}
item_names = []
item_prices = {
    "preset": {},
    "sales": {}
}

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://nori.fish"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # =origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputData(BaseModel):
    user_input: str

class SearchRequest(BaseModel):
    keyword: str
    class_types: Optional[List[str]] = []

class RecipeSearch(BaseModel):
    keyword: str
    recipe_types: Optional[List[str]] = []

class ItemEncoded(BaseModel):
    encoded_item: str

class Guild:
    """Wrapper for Wynncraft Guild"""

    def get_prefix_guild(self, prefix):
        guild_request = requests.get(f"https://api.wynncraft.com/v3/guild/prefix/{prefix}",
                                     headers=AUTH_HEADERS)
        return guild_request.json()

    def get_name_guild(self, name):
        guild_request = requests.get(f"https://api.wynncraft.com/v3/guild/{name}", headers=AUTH_HEADERS)
        return guild_request.json()

    def get_guild_data(self, user_input):
        try:
            if len(user_input) <= 4:
                guild_data = self.get_prefix_guild(user_input)
            else:
                guild_data = self.get_name_guild(user_input)
        except Exception:
            guild_data = self.get_name_guild(user_input)
        return guild_data

class Player:
    """Wrapper for Wynncraft Player"""

    def get_player_main(self, ign):
        api_url = f"https://api.wynncraft.com/v3/player/{ign}"
        stat_request = requests.get(api_url, headers=AUTH_HEADERS)
        player_data = stat_request.json()
        return player_data

    def get_player_full(self, ign):
        api_url = f"https://api.wynncraft.com/v3/player/{ign}?fullResult"
        stat_request = requests.get(api_url, headers=AUTH_HEADERS)
        player_data = stat_request.json()
        return player_data


@app.middleware("http")
async def log_requests(request: Request, call_next):
    counts_file = "/home/ubuntu/site-data/endpoint_counts.json"
    try:
        if os.path.exists(counts_file):
            try:
                with open(counts_file, "r") as f:
                    counts = json.load(f)
            except json.JSONDecodeError as e:
                logging.info(f"JSON decode error: {e}")
                counts = {}
        else:
            counts = {}

        path_parts = request.url.path.split("/")
        
        static_endpoints = [
            "/api/item/list", "/api/lootpool", "/api/aspects", "/api/changelog/item", 
            "/api/changelog/ingredient", "/api/build/search", "/api/recipe/search", 
            "/api/item/analysis", "/api/chat", "/api/uptime", "/api/leaderboard/profession", 
            "/api/leaderboard/guild", "/api/leaderboard/raid", "/api/tokens", "/api/item/price"
        ]
        
        base_endpoint = None
        for static_endpoint in static_endpoints:
            if request.url.path.startswith(static_endpoint):
                base_endpoint = static_endpoint
                break

        if base_endpoint is None:
            if len(path_parts) > 2:
                base_endpoint = "/" + "/".join(path_parts[1:3])
            else:
                base_endpoint = request.url.path

        if base_endpoint in counts:
            counts[base_endpoint] += 1
        else:
            counts[base_endpoint] = 1
        with open(counts_file, "w") as f:
            json.dump(counts, f, indent=3)

        client_host = request.client.host
        url = str(request.url)
        logged_content = f"Host: {client_host}, URL: {url}"
        logging.info(logged_content)
        response = await call_next(request)
        return response

    except Exception as error:
        logging.info(f"Error: {error}")
        return JSONResponse(content={'error': str(error)}, status_code=500)


def create_access_token():
    return jwt.encode({"message": "valid"}, SECRET_KEY, algorithm=ALGORITHM)

def create_csrf_token():
    return secrets.token_hex(16)

@app.get("/api/tokens")
async def set_tokens(response: Response):
    access_token = create_access_token()
    csrf_token = create_csrf_token()
    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="Strict")
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=False, samesite="Strict")
    return {"message": "Tokens set"}

def verify_token(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=403, detail="Not authenticated")
    try:
        jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token or token expired")

def verify_csrf_token(request: Request, csrf_token: str = Cookie(None)):
    header_csrf_token = request.headers.get("X-CSRF-Token")
    logging.info(f"Token verification passed: {csrf_token}")
    if not csrf_token or header_csrf_token != csrf_token:
        logging.info(f"[Invalid token] Cookie CSRF Token: {csrf_token}, Header CSRF Token: {header_csrf_token}")
        raise HTTPException(status_code=403, detail="Invalid session token")

@app.post("/api/chat")
@limiter.limit("20/minute")
async def process_data(request: Request, data: InputData):
    user_input = data.user_input
    try:
        output = await gpt_response(user_input)
        return {"output": output}
    except httpx.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        raise HTTPException(status_code=500, detail="External API error")
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/guild/{user_input}")
@limiter.limit("90/minute")
async def guild_stats(request: Request, user_input: str):
    try:
        guild = Guild()
        guild_data = guild.get_guild_data(user_input)
        created_time = datetime.strptime(guild_data["created"], '%Y-%m-%dT%H:%M:%S.%fZ')
        created_date = created_time.date()
        online_players = []
        guild_members = guild_data["members"]
        rank_map = {
            "owner": "*****",
            "chief": "****",
            "strategist": "***",
            "captain": "**",
            "recruiter": "*",
            "recruit": ""
        }
        for rank, members in guild_members.items():
            if rank in rank_map:
                for player, info in members.items():
                    if info["online"]:
                        online_players.append({
                            "name": player,
                            "server": info["server"],
                            "rank": rank_map[rank]
                        })

        return {
            "name": guild_data["name"],
            "prefix": guild_data["prefix"],
            "owner": list(guild_data["members"]["owner"].keys())[0],
            "created_date": str(created_date),
            "level": guild_data["level"],
            "xp_percent": guild_data["xpPercent"],
            "wars": guild_data.get("wars", 0),
            "territories": guild_data["territories"],
            "total_members": guild_data["members"]["total"],
            "online_players": online_players,
            "members": guild_data["members"],
            "seasonRanks": guild_data["seasonRanks"]
        }
    except Exception as e:
        raise {"Error": e}

@app.get("/api/player/{user_input}")
@limiter.limit("90/minute")
async def player_stats(request: Request, user_input: str):
    try:
        player = Player()
        player_data = player.get_player_full(user_input)
        return player_data
    except Exception as e:
        return {"error": e}

@app.post("/api/build/search")
@limiter.limit("3/second")
async def search_builds(request: Request, data: SearchRequest):
    with open('/home/ubuntu/nori-bot/data/build_db.json') as f:
        builds_data = json.load(f)
    keyword = data.keyword.lower()
    class_types = [cls.lower() for cls in data.class_types]

    results = []
    for build_name, build_info in builds_data["Builds"].items():
        if keyword in build_name.lower() or keyword in build_info['weapon'].lower() or keyword in build_info['tag'].lower() or keyword in build_info['credit'].lower():
            if not class_types or build_info['class'].lower() in class_types:
                results.append({
                    "name": build_name,
                    "link": build_info["link"],
                    "class": build_info["class"],
                    "weapon": build_info["weapon"],
                    "tag": build_info["tag"],
                    "icon": build_info["icon"],
                    "credit": build_info["credit"]
                })
    
    return results

@app.post("/api/recipe/search")
@limiter.limit("3/second")
async def search_builds(request: Request, data: RecipeSearch):
    with open('/home/ubuntu/nori-bot/data/recipe_db.json') as f:
        recipe_data = json.load(f)
    keyword = data.keyword.lower()
    recipe_types = [recipe.lower() for recipe in data.recipe_types]
    results = []
    for recipe_name, recipe_info in recipe_data["Recipes"].items():
        if keyword in recipe_name.lower() or keyword in recipe_info['tag'].lower():
            if not recipe_types or recipe_info['type'].lower() in recipe_types:
                results.append({
                    "name": recipe_name,
                    "type": recipe_info["type"],
                    "link": recipe_info["link"],
                    "tag": recipe_info["tag"]
                })
    return results

@app.get("/api/leaderboard/raid/{raid_name}")
@limiter.limit("300/minute")
async def raid_leaderboard(request: Request, raid_name: str):
    leaderboard_data = await load_leaderboard_data(raid_name.lower())
    try:
        return leaderboard_data
    except Exception as error:
        raise {"error": error}

@app.get("/api/leaderboard/stat/{stat_name}")
@limiter.limit("300/minute")
async def stat_leaderboard(request: Request, stat_name: str):
    leaderboard_data = await load_leaderboard_data(stat_name.lower())
    try:
        return leaderboard_data
    except Exception as error:
        raise {"error": error}

@app.get("/api/leaderboard/profession/{category}")
@limiter.limit("300/minute")
async def profession_leaderboard(request: Request, category: str):
    PROFESSION_CATEGORIES = [
    "woodworking", "weaponsmithing", "armouring", "tailoring",
    "woodcutting", "mining", "fishing", "farming", 
    "jeweling", "scribing", "alchemism", "cooking",
    "professionsGlobal"]
    if category not in PROFESSION_CATEGORIES:
        return {"error": "Invalid profession category"}
    url = f"https://api.wynncraft.com/v3/leaderboards/{category}Level"
    response = requests.get(url, headers=AUTH_HEADERS)
    if response.status_code != 200:
        return {"error": "Error fetching data from Wynncraft API"}
    data = response.json()
    processed_data = await process_profession_leaderboard_data(data)
    return processed_data

@app.get("/api/leaderboard/guild/{category}")
@limiter.limit("300/minute")
async def guild_leaderboard(request: Request, category: str):
    guild_categories = ["guildLevel", "guildTerritories", "guildWars"]
    if category not in guild_categories:
        return {"error": "Invalid guild category"}
    url = f"https://api.wynncraft.com/v3/leaderboards/{category}"

    response = requests.get(url, headers=AUTH_HEADERS)
    if response.status_code != 200:
        return {"error": "Error fetching data from Wynncraft API"}

    data = response.json()

    processed_data = await process_guild_leaderboard_data(data)
    return processed_data

@app.get("/api/database/guild")
@limiter.limit("300/minute")
async def db_guild(request: Request):
    try:
        with open("/home/ubuntu/data-scripts/database/guild_data.json", "r") as file:
            data = json.load(file)
            return data
    except Exception as error:
        print(error)
        return {"Error": error}

@app.post("/api/item/analysis")
@limiter.limit("3/second")
async def item_analysis(request: Request, data: ItemEncoded):
    item_encoded = data.encoded_item
    try:
        analysis = await item_analyzer(item_encoded)
        return {"Result": analysis}
    except Exception as error:
        print(error)
        return {"Error": error}

@app.get("/api/item/mythic")
@limiter.limit("3/second")
async def mythic_items(request: Request):
    try:
        # if not item_ranked:
        await load_weight_data()
        data = {"weights": item_weights, "ranked": item_ranked}
        return data
    except Exception as error:
        print(error)
        return {"Error": error}

@app.get("/api/item/list")
@limiter.limit("3/second")
async def get_item_names(request: Request):
    data = await get_item_list()
    if data:
        return {"items": data}
    else:
        return {"error": "Error fetching item database"}

@app.get("/api/item/get/{item}")
@limiter.limit("300/minute")
async def get_item(request: Request, item: str):
    data = await get_item_stats(item)
    if data:
        return data
    else:
        return {"error": "Item not found"}

@app.get("/api/item/price")
@limiter.limit("180/minute")
async def get_item_price(request: Request):
    try:
        current_timestamp = int(time.time())
        if not item_prices["preset"]:
            await load_weight_data()
        price_data = {"preset": item_prices["preset"], 
                      "sales": item_prices["sales"], 
                      "timestamp": current_timestamp}
        return price_data
    except Exception as error:
        print("Error fetching item prices: ", error)
        return {"error: Error fetching item prices"}
    

@app.get("/api/lootpool")
@limiter.limit("3/second")
async def get_lootpool(request: Request, csrf_token: str = Cookie(None), token_data=Depends(verify_token)):
    verify_csrf_token(request, csrf_token)

    lootpool_file = '/home/ubuntu/nori-bot/data/weekly_lootpool.json'
    try:
        with open(lootpool_file, "r") as file:
            data = json.load(file)
        return data
    except Exception as e:
        return JSONResponse(content={'error': str(e)}, status_code=500)


@app.get("/api/aspects")
@limiter.limit("3/second")
async def get_lootpool(request: Request):
    # origin = request.headers.get("origin")
    # referer = request.headers.get("referer")
    # allowed_hosts = [
    #     "https://nori.fish",
    #     "https://norihub.com",
    # ]
    # if referer is None or not any(referer.startswith(host) for host in allowed_hosts):
    #     logging.info(f"[/api/aspects] Access denied, Origin: {origin}, Referer: {referer}")
    #     raise HTTPException(status_code=403, detail="Contact admin to request access.")

    aspect_file = '/home/ubuntu/nori-bot/data/weekly_aspects.json'
    try:
        with open(aspect_file, "r") as file:
            data = json.load(file)
        return data
    except Exception as e:
        return {'error': str(e)}


@app.get("/api/uptime")
@limiter.limit("300/minute")
async def get_uptime(request: Request):
    uptime_json = "/home/ubuntu/data-scripts/database/server_uptime.json"
    try:
        with open(uptime_json, "r") as file:
            data = json.load(file)
        return data
    except Exception as error:
        return {"error": str(error)}

@app.get("/api/showcase")
@limiter.limit("3/second")
async def get_build_showcase(request: Request):
    showcase_file = '/home/ubuntu/site-data/showcase.json'
    try:
        with open(showcase_file, "r") as file:
            data = json.load(file)
        return data
    except Exception as e:
        return {'error': str(e)}

@app.get("/api/changelog/all")
@limiter.limit("3/second")
async def get_all_changelog_dates(request: Request):
    changelog_dir = "/home/ubuntu/nori-bot/bot/changelog/"
    item_dates = []
    ingredient_dates = []

    for filename in os.listdir(changelog_dir):
        if filename.startswith("item_changelog_") and filename.endswith(".md"):
            date_str = filename.replace("item_changelog_", "").replace(".md", "")
            item_dates.append(date_str)
        elif filename.startswith("ingredient_changelog_") and filename.endswith(".md"):
            date_str = filename.replace("ingredient_changelog_", "").replace(".md", "")
            ingredient_dates.append(date_str)

    return {"item": sorted(item_dates), "ingredient": sorted(ingredient_dates)}

@app.get("/api/changelog/item/{date}")
@limiter.limit("300/minute")
async def get_item_changelog(request: Request, date: str):
    file_path = f"/home/ubuntu/nori-bot/bot/changelog/item_changelog_{date}.md"
    with open(file_path, "r", encoding="utf-8") as file:
        item_changelog_data = file.read()
    return PlainTextResponse(item_changelog_data)

@app.get("/api/changelog/ingredient/{date}")
@limiter.limit("300/minute")
async def get_ingredient_changelog(request: Request, date: str):
    file_path = f"/home/ubuntu/nori-bot/bot/changelog/ingredient_changelog_{date}.md"
    with open(file_path, "r", encoding="utf-8") as file:
        ingredient_changelog_data = file.read()
    return PlainTextResponse(ingredient_changelog_data)


async def load_leaderboard_data(data_type):
    with open("/home/ubuntu/data-scripts/database/player_leaderboard.json", "r") as file:
        leaderboard_data = json.load(file)["ranking"]
    return leaderboard_data[data_type]

async def process_profession_leaderboard_data(data):
    processed_data = []
    for player in data.values():
        username = player['name']
        level = player['score']  
        xp = player['metadata']['xp']
        processed_data.append({username: {"level": level, "xp": xp}})
    
    processed_data = sorted(processed_data, key=lambda x: (list(x.values())[0]['level'], list(x.values())[0]['xp']), reverse=True)
    
    return processed_data

async def process_guild_leaderboard_data(data):
    processed_data = []

    for guild in data.values():
        guild_name = guild['name']
        created_time = datetime.strptime(guild["created"], '%Y-%m-%dT%H:%M:%S.%fZ')
        created_date = created_time.date()
        processed_data.append({guild_name: {"prefix": guild["prefix"],
                                            "level": guild["level"],
                                            "wars": guild["wars"],
                                            "members": guild["members"],
                                            "territories": guild["territories"],
                                            "created_at": created_date
                                            }
                               })
    return processed_data

async def load_item_data():
    global item_map
    with open("/home/ubuntu/nori-bot/bot/items.json", "r") as file:
        item_map = json.load(file)


async def load_weight_data():
    global item_weights, item_ranked, item_prices
    with open("/home/ubuntu/nori-bot/data/mythic_weights.json", "r") as file:
        mythic_data = json.load(file)
        item_weights = mythic_data["Data"]
        item_ranked = mythic_data["ranked"]
        item_prices["preset"] = mythic_data["price"]

async def load_sales_data():
    global item_prices
    with open("/home/ubuntu/nori-bot/data/sales_data.json", "r") as file:
        sales_data = json.load(file)
        item_prices["sales"] = sales_data

async def get_item_list():
    if not item_map:
        await load_item_data()
    if not item_names:
        for item in item_map.items():
            if "rarity" in item[1]:
                if not isinstance(item[1]["rarity"], int) and "toolType" not in item[1] and "tomeType" not in item[1] and "charmType" not in item[1]:
                    item_names.append(item[0])
    return item_names


async def get_item_stats(name):
    if not item_map:
        await load_item_data()
    icon_link = None
    item_type = None
    for item in item_map:
        if name.lower() == item.lower():
            item_data = item_map[item]
            icon = item_data["icon"] if "icon" in item_data else None
            if icon:
                icon_name = icon if "http" in icon else item_data["icon"]["value"]["name"]
                if "http" not in icon:
                    icon_link = f"https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_name}.webp" if icon_name else None
                else:
                    icon_link = icon
                item_data["icon"] = icon_link
            if "weaponType" in item_data:
                item_type = item_data["weaponType"]
            elif "accessoryType" in item_data:
                item_type = item_data["accessoryType"]
            elif "armourType" in item_data:
                item_type = item_data["armourType"]
    
            if item_type:
                item_data["type"] = item_type
            return {item: item_data}


async def get_texture(item):
    data = item_map[item]
    icon_link = None
    icon = data["icon"] if "icon" in data else None
    item_type = None
    if icon:
        icon_name = icon if "http" in icon else data["icon"]["value"]["name"]
        if "http" not in icon:
            icon_link = f"https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_name}.webp" if icon_name else None
        else:
            icon_link = icon_name
        data["icon"] = icon_link
    if "weaponType" in data:
        item_type = data["weaponType"]
    elif "accessoryType" in data:
        item_type = data["accessoryType"]
    elif "armourType" in data:
        item_type = data["armourType"]
    item_tier = data["rarity"] if "rarity" in data else None
    return {"icon": icon_link, "item_type": item_type, "item_tier": item_tier}


async def item_analyzer(item_string):
    try:
        if not item_map:
            await load_item_data()
        if not item_weights:
            await load_weight_data()
        item = wynntilsresolver.item.GearItemResolver.from_utf16(item_string)
        name = item.name
        texture = await get_texture(name)
        ids = item.identifications if item.identifications else {}
        stats_output = {name: {}, "rate": {}, "misc": {}, "shiny": None, "internalName": name}
        data = item_map[name]
        id_range = data["identifications"] if item.identifications else None
        if item.shiny:
            stats_output["shiny"] = f"{item.shiny.display_name}: {item.shiny.value}"
        for stat in ids:
            if stat.roll >= 0 and stat.id in id_range:
                if isinstance(id_range[stat.id], dict):
                    id_min = id_range[stat.id]["min"]
                    id_max = id_range[stat.id]["max"]
                    id_base = id_range[stat.id]["raw"]
                    if stat.roll > 0:
                        id_rolled = round((stat.roll / 100) * id_base, 2)
                        if abs(abs(id_rolled) - abs(int(id_rolled))) == 0.5:
                            if id_base > 0:
                                id_rolled = int(id_rolled) + 1
                            else:
                                id_rolled = int(id_rolled)
                        else:
                            id_rolled = round(id_rolled)
                    else:
                        id_rolled = stat.roll

                    if stat.base > 0:
                        if id_min != id_max:
                            percentage = (id_rolled - id_min) / (id_max - id_min) * 100
                        else:
                            percentage = 100
                    else:
                        if id_min != id_max:
                            percentage = (1 - (id_max - id_rolled) / (id_max - id_min)) * 100
                        else:
                            percentage = 100
                    stats_output[name].update({stat.id: id_rolled})
                    stats_output["rate"].update({stat.id: round(percentage, 2)})
                    stats_output["misc"].update({"reroll": item.reroll, "powder": item.powder.powders if item.powder else None})
        stats_output.update(texture)
        if name in item_weights:
            weight_result = await weight_output(name, stats_output[name], stats_output["rate"])
            stats_output.update(weight_result)
        # print(json.dumps(stats_output, indent=3))
        return stats_output
    except Exception as error:
        print(f"Decode error: {error}")
        return None


async def weight_output(item, item_stats, rate):
    global item_weights
    index = 0
    item_IDs = {}
    ID_values = [0, 0, 0, 0, 0, 0, 0, 0]
    rate_values = [0, 0, 0, 0, 0, 0, 0, 0]
    weighing_factors = [0, 0, 0, 0, 0, 0, 0, 0]
    scales = item_weights[item]
    item_IDs["scales"] = scales
    for scale in scales:
        item_IDs.setdefault("weights", {}).setdefault(scale, {})
        weight = item_IDs["weights"][scale]
        stats = item_weights[item][scale]
        for id in stats:  # ID -> the STAT, stats[id] -> Value
            acutal_ID = item_stats[id]
            rating = rate[id]
            factor = float(stats[id]) / 100
            if factor < 0:
                rating = 100 - rating
                factor = abs(factor)
            weighing_factors[index] = factor
            ID_values[index] = acutal_ID
            rate_values[index] = float(rating)
            weight.update({id: acutal_ID})
            index += 1
        product = list(map(lambda x, y: x * y, rate_values, weighing_factors))
        weighted_overall = round(sum(product), 2)
        index = 0
        item_IDs["weights"][scale] = weighted_overall
        weighing_factors = [0, 0, 0, 0, 0, 0, 0, 0]

    """
    Output structure:
    items_IDs = {
        item_name: {
            scale_1: 100,
            scale_2: 69
        }
    }
    """
    return item_IDs

async def gpt_response(prompt):
    gpt_endpoint = "https://api.openai.com/v1/chat/completions"
    api_key = AI_API_KEY

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": engine,
        "messages": [
            {"role": "system", "content": "You are Nori, RawFish's Assistant Bot"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "top_p": 1,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(gpt_endpoint, headers=headers, json=data)

    response.raise_for_status()  # Raise an exception for HTTP errors

    result = response.json()
    generated_text = result["choices"][0]["message"]["content"]
    return generated_text

@app.on_event("startup")
async def reload_sales_data_periodically():
    asyncio.create_task(sales_data_updater())

async def sales_data_updater():
    while True:
        await load_sales_data()
        await asyncio.sleep(600)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
