# Source Code Guide

This directory contains separate source areas for Nori's **Discord bot**, **web-facing files**, and **backend/data utilities**. The Discord bot and web app are **not the same application** and do **not share a runtime**.

```text
src/
  bot/  Discord bot source, command modules, and bot-side Wynncraft helpers
  web/  Separate static frontend, public docs, assets, and browser-side scripts
  db/   Backend placeholder plus local data/test utilities
```

## Bot

`bot/` is the main **open-source Discord bot** implementation. It is written in **Python** and uses:

- `hikari` for Discord API access
- `hikari-lightbulb` for slash commands
- `hikari-miru` for interactive components
- `aiohttp`, `httpx`, and `requests` for HTTP/API work
- `numpy`, `pandas`, `scipy`, `matplotlib`, and related libraries for data-heavy utilities

Important paths:

- `nori_bot.py` initializes the **bot**, managers, command loader, logging, and startup tasks.
- `requirements.txt` pins **bot dependencies**.
- `lib/config.py` centralizes **environment variables**, paths, constants, and runtime state.
- `lib/commands/` contains **slash command modules**.
- `lib/commands/loader.py` registers command modules with the bot.
- `lib/views/` contains **Discord component views**.
- `lib/tasks/` contains **background or scheduled task helpers**.
- `lib/wynn_api.py`, `lib/item_*`, `lib/player_*`, `lib/guild_*`, and `lib/leaderboard_*` contain reusable **Wynncraft data logic**.

See [bot/README.md](bot/README.md) for local setup and command development notes.

## Web

`web/` is a **separate static frontend** for Nori's public web tools and docs. It is **not the Discord bot runtime**. Most pages are plain HTML, CSS, and JavaScript, with shared browser modules under `web/js_global` and shared CSS under `web/css_global`.

Important paths:

- `index.html` is the main web entry point.
- `wynn/` contains Wynncraft tool pages.
- `docs/` contains public API, command, and tower documentation.
- `js_global/config.js` contains public site links and frontend configuration.
- `resources/` contains shared item, aspect, and UI assets.

Preview the web app locally with:

```powershell
python -m http.server 8000 -d src/web
```

## Database and Data Utilities

`db/` does **not** contain the production API service. The hosted API is documented at [nori.fish/docs](https://nori.fish/docs/), and development utilities live under `db/tester`.

Use this area for local scripts, experiments, and data-fetching helpers. **Do not commit** production credentials, generated private datasets, or deployment-specific database configuration.

## Development Notes

- Keep `web/docs/commands.md` aligned when a public bot command documented on the website changes.
- Prefer shared helpers in `bot/lib` over copying API or rendering logic into command files.
- Keep environment-specific values in `~/.env`, not in the repository.
- Public API behavior should be documented in `web/docs/api.md` when endpoints or response shapes change.
