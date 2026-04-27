# Nori

[![Status](https://img.shields.io/badge/status-active-success)](https://nori.fish)
[![Bot](https://img.shields.io/badge/discord%20bot-verified-5865F2?logo=discord&logoColor=white)](https://discord.com/discovery/applications/873677970928193568)
[![License](https://img.shields.io/badge/license-AGPL--3.0-green)](LICENSE)

### Discord bot, Web app, and APIs for Wynncraft.

Nori started as a Discord bot in 2022. Today it includes the bot, Nori-Web, public docs, and APIs used by Wynncraft community developers.
>  As of early 2026, Nori is the **largest Wynncraft Discord bot**, serving **more than 3,000 servers**.

## Quick Start

- [Add Nori to Discord](https://discord.com/discovery/applications/873677970928193568)
- [Visit Nori Web](https://nori.fish)
- [Read API Docs](https://nori.fish/docs/)
- [Join the Community Discord](https://discord.gg/eDssA6Jbwd)

## Code Development

The repository keeps the **Discord bot** and **web-facing files** in separate directories:

```text
src/
  bot/  Python Discord bot and command implementation
  web/  Separate static web interface and public docs
  db/   Backend notes and development/test utilities
```

The bot lives in `src/bot`. It uses **Hikari**, **Lightbulb**, and **Miru** for Discord commands and interactive components. Shared Wynncraft logic lives in `src/bot/lib`, command modules live in `src/bot/lib/commands`, and command registration is handled by `src/bot/lib/commands/loader.py`.

To run the bot locally:

```powershell
cd src/bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python nori_bot.py
```

Configuration is loaded from `~/.env` by `src/bot/lib/config.py`. **At minimum**, a local bot needs a Discord token:

```env
NORI_TOKEN=your_discord_bot_token
```

**Optional integrations** use additional variables such as `NORI_GPT_KEY`, `WYNN_BOT_TOKEN`, `WYNN_SOURCE_TOKEN`, `LOG_CHANNEL_ID`, and `BOT_OWNER_ID`. Some **production data files are not committed**, so data-heavy commands may need local fixtures, public API calls, or maintainer-provided data before they behave exactly like the hosted bot.

For more bot contributor notes, see [src/README.md](src/README.md) and [src/bot/README.md](src/bot/README.md).

## Working on Commands

Most bot work follows this path:

1. Add or update command behavior in `src/bot/lib/commands`.
2. Reuse shared helpers from `src/bot/lib` instead of duplicating API, rendering, or parsing logic.
3. Register new command modules in `src/bot/lib/commands/loader.py`.
4. Update `src/web/docs/commands.md` when a public slash command documented on the website changes.
5. Keep **secrets**, **deployment data**, **generated caches**, and **private API tokens** out of commits.

The web app is static and can be previewed with any local static server:

```powershell
python -m http.server 8000 -d src/web
```

Then open `http://localhost:8000`.

## Links

- **Web Interface**: [nori.fish](https://nori.fish)
- **Discord Bot**: [Add to Server](https://discord.com/discovery/applications/873677970928193568)
- **Kook Bot** (China): [Bot Market](https://www.botmarket.cn/bot/28)
- **API Documentation**: [nori.fish/docs](https://nori.fish/docs/)
- **Community Discord**: [Join Server](https://discord.gg/eDssA6Jbwd)
- **GitHub**: [RawFish69/Nori](https://github.com/RawFish69/Nori)

## Source Code Notice

Nori's **bot source** is published for community development under the repository license. The web files in this repository are **separate from the Discord bot runtime**. **Production credentials**, **private deployment configuration**, **generated runtime data**, and infrastructure-specific files are intentionally not included. Please do not commit secrets or data pulled from private services.

## Contributing

Pull requests should be focused, include a short summary and testing notes, and avoid mixing **Discord bot** changes with **Nori-Web** changes unless needed. Do not commit **secrets**, **generated caches**, production config, or private runtime data.

## Contact

- **Discord**: rawfish69
- **GitHub**: [@RawFish69](https://github.com/RawFish69)

## License

Nori is licensed under the [GNU Affero General Public License v3.0](LICENSE).

---

*Made for the Wynncraft community*
