# Nori API Documentation
> This documentation covers the public API for Nori
> - All endpoints return JSON unless otherwise specified
> - Keep requests under rate limits to avoid temporary IP blocks
> - View source code on [GitHub](https://github.com/RawFish69/Nori)

## General Information
- **Base URL**: <https://nori.fish>  
- **Rate Limiting**, Common limits include:
  - `180/minute`
  - `20/minute`
  - `300/minute`
- **Authentication**:  
  - Most endpoints are public.  
  - Others require authentication tokens set by `/api/tokens`, plus a CSRF token for HTTP modifications.  
> For inquiries or assistance, join our [Support Server](https://discord.gg/eDssA6Jbwd) or reach out to the developer directly.

---

## Table of Contents
1. [Item Endpoints](#item-endpoints)
    - [Item Analysis](#post-apiitemanalysis)
    - [Mythic Items](#get-apiitemmythic)
    - [Item List](#get-apiitemlist)
    - [Item Details](#get-apiitemgetitem)
    - [Item Price](#get-apiitemprice)
    - [Changelog](#changelog-endpoints)
2. [Uptime Endpoint](#uptime-endpoint)
3. [Leaderboard Endpoints](#leaderboard-endpoints)
    - [Raid & Stat Leaderboards](#get-apileaderboardraidraid_name)
    - [Profession Leaderboards](#get-apileaderboardprofessioncategory)
    - [Guild Leaderboards](#get-apileaderboardguildcategory)
4. [Database Guild Endpoint](#database-guild-endpoint)
5. [Build and Recipe Search](#build-and-recipe-search)
6. [Item Lootpool Endpoint](#item-lootpool-endpoint)
7. [Aspects Lootpool Endpoint](#aspect-lootpool-endpoint)
8. [Guild Endpoints](#guild-endpoints)
9. [Player Endpoint](#player-endpoint)
10. [Showcase Endpoint](#showcase-endpoint)
11. [Lootpool History](#item-loot-history) (Not yet implemented)

---

## Item Endpoints

### `POST` /api/item/analysis
- Rate Limit: 180/minute
- Description: Decodes wynntils encoded item and returns analysis for the item

Request:
```json
{
  "encoded_item": "string"
}
```

Response:
```json
{
  "itemName": {},
  "rate": {},
  "misc": {
    "reroll": 0,
    "powder": []
  },
  "shiny": null,
  "internalName": "string",
  "icon": "string",
  "item_type": "string",
  "item_tier": "string",
  "weights": {
    "scales": [],
    "weights": {}
  }
}
```
> **Note**: Payload should match current Wynntils gear encoding format. Only latest version compatibility is guaranteed. Legacy formats may not work correctly.

### `GET` /api/item/mythic
- Rate Limit: 180/minute
- Description: Returns mythic item scales and rankings.
- 

Response:
```json
{
  "weights": {
    "ItemName": {
        "Main": {
            "Stat_1": 0,
            "Stat_2": 0,
            ...
        },
        "Scale_2": {...}
    }
  },
  "ranked": {
    "ItemName": {
        "Main": {
            "owner": "string",
            "stats": {
            "ItemName": {
                "Stat_1": 0,
                "Stat_2": 0,
                ...
            },
            "rate": {
                "Stat_1": 0,
                "Stat_2": 0,
                ...
            },
            "weight": 0,
            "shiny": null,
            "icon": null,
            "item_type": "string",
            "item_tier": "string"
        }
      },
      "Scale_2": {...}
    }
  }
}
```

### `GET` /api/item/list
- Rate Limit: 180/minute
- Description: Lists all valid item names.

Response:
```json
{
  "items": ["string", "..."]
}
```

### `GET` /api/item/get/{item}
- Rate Limit: 300/minute
- Description: Returns item stats for the specified name.

Response:
```json
{
  "itemName": {
    "icon": "string",
    "type": "string",
    "rarity": "mixed",
    "identifications": {...}
  }
}
```

### `GET` /api/item/price
- Rate Limit: 180/minute
- Description: Returns the current item price data, including preset data and sales data.

Response schema:
```json
{
    "preset": {
        "ItemName": {
            "unid": 0.0,  // Base unidentified item value (may be outdated)
            "samples": [
                0.0,        // 0% weight
                0.0,        // 10% weight
                0.0,        // 20% weight
                0.0,        // 30% weight
                0.0,        // 40% weight
                0.0,        // 50% weight
                0.0,        // 60% weight
                0.0,        // 70% weight
                0.0,        // 80% weight
                0.0,        // 90% weight
                0.0,        // 95% weight
                0.0,        // 97% weight
                0.0         // 100% weight
            ]
        }
    },
    "sales": {
        "ItemName": [
            [
                0.0,        // Weight percentage (0-100)
                0,          // Sale price in emeralds
                0           // Unix timestamp of sale
            ]
        ]
    },
    "timestamp": Timestamp
}
```
### Sample Methods for Price Estimation

1. **Data-Driven Models**
    - Regression analysis for trend prediction
    - Random forest models for complex pattern recognition
    - Time series forecasting for temporal patterns

2. **Statistical Analysis**
    - Moving averages for smoothing price fluctuations
    - Kalman filtering for noise reduction
    - Bayesian inference for uncertainty estimation
    - Outlier detection for data cleaning

3. **Market-Based Approaches**  
    - Supply-demand equilibrium analysis
    - Price momentum tracking
    - Volume-weighted average pricing
    - Recent trade clustering

### Note from Developer:
> The discord bot version of Nori implements a hybrid regression model for price estimation. While proof of concept shows promise, data source limitations can lead to outdated estimates. Community developers are encouraged to explore improved prediction models, as reliable price estimation is achievable with sufficient data collection and analysis.

### Fallback Options
When insufficient data points are available:
1. Use pre-set values
2. Input custom values

### Contributing
- Preset value improvements are welcome
- Join our support server for discussions
- Current sales data are contributed by Marketplace Community, join discord for more info

> **Note**: Always prioritize actual sales data over preset values when possible


### Changelog Endpoints

### `GET` /api/changelog/all
- Rate Limit: 180/minute
- Description: Lists available dates for item/ingredient changelogs.

Response:
```json
{
  "item": ["string", "..."],
  "ingredient": ["string", "..."]
}
```

### `GET` /api/changelog/item/{date}
### `GET` /api/changelog/ingredient/{date}
- Rate Limit: 300/minute
- Description: Retrieves plain text changelogs by date.

Response (Plain Text):
```
Raw text content
```

## Uptime Endpoint

### `GET` /api/uptime
- Rate Limit: 180/minute
- Description: Offers server uptime info.
- 20-30 seconds TTL, so the uptime may be different from other sources, latency is expected.

Response:
```json
{
  "servers": {
    "WC9": {
      "initial": Timestamp,
      "players": []
    },
    "WC2": {
      "initial": Timestamp,
      "players": []
    }
  },
  "Latest": Timestamp
}
```
> **Note**: `Latest` is for lastest data update timestamp, not the latest server.

## Leaderboard Endpoints

### `GET` /api/leaderboard/raid/{raid_name}
### `GET` /api/leaderboard/stat/{stat_name}

- Description: Returns data for a specified raid or stat leaderboard.

Available Parameters:
- For raid leaderboards (`raid_name`):
    - `raids_total`: Total raids completed
    - `tna`: The Nameless Anomaly completions
    - `tcc`: The Canyon Colossus completions
    - `nol`: Nest of the Legends completions
    - `nog`: Orphion's Gate completions

- For stat leaderboards (`stat_name`):
    - `dungeons`: Total dungeon completions
    - `chests`: Chests discovered
    - `mobs`: Mobs killed
    - `wars`: Territory wars won
    - `playtime`: Total playtime
    - `pvp_kills`: PvP kills
    - `quests`: Quests completed
    - `levels`: Combined levels

Response:
```json
{
    "PlayerName1": 0,
    "PlayerName2": 0,
    ...
}
```


### `GET` /api/leaderboard/profession/{category}
### `GET` /api/leaderboard/guild/{category}
- Rate Limit: 180/minute
- Description: Queries Wynncraft leaderboards for professions or guild data.

- Available Parameters:
    - For professions (`category`):
        - `mining`: Mining leaderboard
        - `fishing`: Fishing leaderboard
        - `woodcutting`: Woodcutting leaderboard
        - `farming`: Farming leaderboard
        - `woodworking`: Woodworking leaderboard
        - `weaponsmithing`: Weaponsmithing leaderboard
        - `tailoring`: Tailoring leaderboard
        - `alchemism`: Alchemism leaderboard
        - `cooking`: Cooking leaderboard
        - `jeweling`: Jeweling leaderboard
        - `scribing`: Scribing leaderboard
        - `armouring`: Armouring leaderboard
        - `professionsGlobal`: Total professions

    - For guilds (`category`):
        - `raids_total`: All raids leaderboard
        - `chests`: Chests opened leaderboard
        - `mobs`: Mobs killed leaderboard
        - `tna`: TNA completions
        - `tcc`: TCC completions
        - `nol`: NOL completions
        - `nog`: NOG completions
        - `dungeons`: Dungeons completed
        - `playtime`: Total playtime
        - `quests`: Quests completed
        - `levels`: Total Player levels
        - `sr`: Season rating
        - `guildTerritories`: Territories owned
        - `guildWars`: Wars won
        - `guildLevel`: Guild levels


Response (Profession):
```json
[
  {
    "player_name": {
      "level": 0,
      "xp": 0
    }
  }
]
```

Response (Guild leaderboard):
```json
[
  {
    "guild_name": {
      "prefix": "string",
      "level": 0,
      "wars": 0,
      "members": 0,
      "territories": 0,
      "created_at": "string (YYYY-MM-DD)"
    }
  }
]
```

## Database Guild Endpoint

### `GET` /api/database/guild
- Rate Limit: 180/minute
- Description: Retrieves a locally stored guild database (JSON).

Response:
```json
  "GuildName": {
    "raids_total": 0,
    "tna": 0,
    "tcc": 0,
    "nol": 0,
    "nog": 0,
    "dungeons": 0,
    "chests": 0,
    "mobs": 0,
    "playtime": 0,
    "quests": 0,
    "levels": 0,
    "name": "string",
    "created_at": "string",
    "members": 0,
    "sr": 0
  },
```

## Build and Recipe Search

### `POST` /api/build/search
- Rate Limit: 180/minute
- Description: Searches builds by keyword and class.  

Request Body:
```json
{
  "keyword": "string",
  "class_types": ["string", "..."]
}
```

Response (Array of objects):
```json
[
  {
    "name": "string",
    "link": "string",
    "class": "string",
    "weapon": "string",
    "tag": "string",
    "icon": "string",
    "credit": "string"
  }
]
```

### `POST` /api/recipe/search
- Rate Limit: 180/minute
- Description: Searches recipes by keyword and type.

Request Body:
```json
{
  "keyword": "string",
  "recipe_types": ["string", "..."]
}
```

Response (Array of objects):
```json
[
  {
    "name": "string",
    "type": "string",
    "link": "string",
    "tag": "string"
  }
]
```

## Item Lootpool Endpoint

### `GET` /api/lootpool
- Rate Limit: 180/minute
- Description: Requires valid tokens. Returns weekly lootpool data.

Response:
```json
{
"Loot": {
    "Region": {
        "Shiny": {
            "Item": "string",
            "Tracker": "string"
        },
        "Mythic": [],
        "Fabled": [],
        "Legendary": [],
        "Rare": [],
        "Unique": []
    },
    "Region2": {...}
    },
"Icon": {
    "ItemName": "string",
    ...
    },
"Timestamp": Timestamp
}
```

## Item Loot History
> Note: Complete historical data since the lootrun update exists in our database but is not yet publicly accessible. This endpoint will be enabled after the feature is implemented in Nori-Web.


## Aspect Lootpool Endpoint

### `GET` /api/aspects
- Rate Limit: 180/minute
- Description: Provides weekly aspects data.

Response:
```json
{
  "Loot": {
    "RaidName": {
        "Mythic": [],
        "Fabled": [],
        "Legendary": []
    }
  },
  "Icon": {
    "AspectName": "string"
  },
  "Timestamp": Timestamp
}
```

## Guild Endpoints

### `GET` /api/guild/{user_input}
- Rate Limit: 180/minute
- Description: Returns guild info by prefix or name.

Response:
```json
{
  "name": "string",
  "prefix": "string",
  "owner": "string",
  "created_date": "string (YYYY-MM-DD)",
  "level": 0,
  "xp_percent": 0,
  "wars": 0,
  "territories": 0,
  "total_members": 0,
  "online_players": [
    {
      "name": "string",
      "server": "string",
      "rank": "string"  
    }
  ],
  "members": {
    "owner": {},
    "chief": {},
    "strategist": {},
    "captain": {},
    "recruiter": {},
    "recruit": {}
  },
  "seasonRanks": {}
}
```

## Player Endpoint

### `GET` /api/player/{user_input}
- Rate Limit: 180/minute
- Description: Returns full Wynncraft player data.
- This route serves as a proxy for users in China, where access to the official API is blocked.

Response:
```json
{
  // Refer to Official Wynncraft API Documentation for response schema
}
```

## Showcase Endpoint

### `GET` /api/showcase
- Rate Limit: 180/minute
- Description: Fetches build showcase data.

Response:
```json
{
  "showcase_data": {}
}
```


## Contributors
- [RawFish](https://github.com/RawFish69) - Core Developer, Documentation writing.
