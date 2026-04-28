# Nori Bot Development

This directory contains the **Source code for Nori discord bot**. It is the best place to start if you want to **add commands**, **fix Wynncraft data handling**, or **use it for your own project**.

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

For a local bot, provide your Discord bot token and any optional public API credentials your test commands need. Some startup files are loaded from local data paths, such as **lootpool data**, **item maps**, and **stat maps**. Missing files are handled with fallback empty data, but commands that depend on those files may be limited until local fixtures are available.

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
2. If a new module is needed, create a Lightbulb 3 extension with `loader = lightbulb.Loader()`.
3. Register command classes with `@loader.command`.
4. Add the module path to `client.load_extensions(...)` in `nori_bot.py`.
5. Put shared parsing, API, or rendering behavior in `lib/` so other commands can reuse it.
6. Update `../web/docs/commands.md` when a public command documented on the website changes.

Example command module:

```python
"""Example public command."""
import lightbulb

loader = lightbulb.Loader()


@loader.command
class Example(lightbulb.SlashCommand, name="example", description="Run an example command"):
    topic = lightbulb.string("topic", "What to echo", default="Nori")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.respond(f"Example command received: {self.topic}")
```

Then load it in `nori_bot.py`:

```python
async def load_commands(event: hikari.StartingEvent) -> None:
    await client.load_extensions(
        "lib.commands.ping",
        "lib.commands.example",
    )
```

Use `self.<option_name>` for command options. If a command needs the Hikari app or REST client, use `ctx.client.app`, for example `await ctx.client.app.rest.fetch_user(ctx.user.id)`.

Shared services are registered in `lib/manager_registry.py` by `nori_bot.py`. Add new managers only when state or helpers need to be shared across command modules.

## Data and Secrets

**Do not commit** Discord tokens, API keys, private server IDs, generated production caches, or private datasets. Use `~/.env` for **secrets** and local JSON fixtures for development data.

When changing code that uses public Nori APIs, keep `../web/docs/api.md` in sync with **endpoint behavior** and **response shapes**.
