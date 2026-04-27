# Nori Bot Development

This directory contains the **Source code for Nori discord bot**. It is the best place to start if you want to **add commands**, **fix Wynncraft data handling**, or **use it for your own project*.

As of early 2026, Nori is the **largest Wynncraft Discord bot**, serving **more than 3,000 servers**.

The **Discord bot** is separate from **Nori-Web**. This README covers only the **bot runtime** and **bot-side development**.

## Local Setup

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python nori_bot.py
```

The bot reads **environment variables** from `~/.env` through `lib/config.py`.

**Required** for a basic local bot:

```env
NORI_TOKEN=your_discord_bot_token
```

Common **optional values**:

```env
NORI_GPT_KEY=optional_openai_or_compatible_key
WYNN_BOT_TOKEN=optional_wynncraft_api_token
WYNN_SOURCE_TOKEN=optional_wynnsource_token
LOG_CHANNEL_ID=optional_discord_channel_id
BOT_OWNER_ID=optional_discord_user_id
DATA_MANAGER_ROLE_ID=optional_discord_role_id
CONTRIBUTOR_ROLE_ID=optional_discord_role_id
LB_IN_GUILD_PATH=optional_path_to_local_leaderboard_json
```

Some startup files are loaded from local data paths, such as **lootpool data**, **item maps**, **stat maps**, and **blocked users**. Missing files are handled with fallback empty data, but commands that depend on those files may be limited until local fixtures or maintainer-provided data are available.

## Directory Map

```text
src/bot/
  nori_bot.py          Bot entry point and manager initialization
  requirements.txt     Python dependencies
  lib/
    config.py          Environment variables, constants, paths, runtime state
    commands/          Slash command modules
    views/             Miru/Discord component views
    tasks/             Background task helpers
    wynn_api.py        Wynncraft API wrapper
    item_*.py          Item parsing, rendering, weighing, and pricing helpers
    player_*.py        Player data helpers and display formatting
    guild_*.py         Guild data helpers and display formatting
    leaderboard_*.py   Leaderboard processing and presentation
```

## Adding or Updating Commands

1. Put command code in the closest existing module under `lib/commands`.
2. If a new module is needed, expose a `load_*_commands(bot, blocked_users)` function.
3. Register that loader in `lib/commands/loader.py`.
4. Put shared parsing, API, or rendering behavior in `lib/` so other commands can reuse it.
5. Update `../web/docs/commands.md` when a public command documented on the website changes.

Commands generally receive **shared services** through `bot.managers`, which is built in `nori_bot.py`. Add new managers there only when the state or helper needs to be shared across command modules.

## Data and Secrets

**Do not commit** Discord tokens, API keys, private server IDs, generated production caches, or private datasets. Use `~/.env` for **secrets** and local JSON fixtures for development data.

When changing code that uses public Nori APIs, keep `../web/docs/api.md` in sync with **endpoint behavior** and **response shapes**.
