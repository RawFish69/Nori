# Nori API

The production database and API service are closed source and are not included in this repository. Community developers should use the  Nori API for data access instead of relying on private database files or generated caches.

## Public API

- Base URL: <https://nori.fish>
- Full documentation: <https://nori.fish/docs/>
- Support server: <https://discord.gg/eDssA6Jbwd>

Most endpoints return JSON. Public routes cover Wynncraft player and guild lookups, item data, leaderboards, raid lootpool data, aspects, gambits, uptime, build search, recipe search, and showcase data.

## Common Endpoints

```text
GET  /api/player/{user_input}
GET  /api/guild/{user_input}
GET  /api/item/list
GET  /api/item/get/{item}
GET  /api/item/price
POST /api/item/analysis
GET  /api/leaderboard/raid/{raid_name}
GET  /api/leaderboard/stat/{stat_name}
GET  /api/leaderboard/raid_all
GET  /api/leaderboard/guild/{category}
GET  /api/database/guild
GET  /api/lootpool
GET  /api/raids
GET  /api/aspects
GET  /api/gambits
GET  /api/uptime
POST /api/build/search
POST /api/recipe/search
GET  /api/showcase
```

## Notes

- Keep requests within the documented rate limits.
- Do not commit API keys, private datasets, generated caches, or deployment-specific database configuration.
- When public API behavior changes, update `src/web/docs/api.md` first and keep this file as a short db-area pointer.
