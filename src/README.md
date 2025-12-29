# Source Code Structure

This directory contains the three main components of the Nori project. Each component serves a distinct purpose and can be developed and deployed independently.

## Directory Structure

```
src/
├── bot/          # Discord/Kook bot implementation
├── web/          # Web application frontend
└── db/           # Database and backend services
```

## Bot (`bot/`)

The bot component is a multi-platform chat bot built with Python, providing Wynncraft-related commands and utilities through Discord and Kook platforms.

### Technology Stack
- **Framework**: Hikari + Lightbulb (Discord.py alternative)
- **Language**: Python 3.x
- **Key Libraries**: 
  - `hikari` - Discord API wrapper
  - `lightbulb` - Command framework
  - `miru` - Interactive components
  - `aiohttp` - Async HTTP client

### Main Components
- **`nori_bot.py`** - Main bot entry point and initialization
- **`lib/commands/`** - Command handlers for various features
  - `items.py` - Item-related commands (search, analysis, price checking)
  - `wynn_stats.py` - Player and guild statistics commands
  - `tower.py` - Guild tower calculation commands
  - `ping.py` - Basic utility commands
- **`lib/`** - Core libraries and utilities
  - `wynn_api.py` - Wynncraft API client wrapper
  - `item_manager.py` - Item data management
  - `item_weight.py` - Item value calculation
  - `price_estimator.py` - ML-based price estimation
  - `leaderboard_utils.py` - Leaderboard processing
  - `guild_display.py` - Guild information formatting
  - `player_display.py` - Player information formatting
  - `data_manager.py` - Local data caching and management
  - `ml_approach.py` - Machine learning models for item analysis

### Features
- Real-time Wynncraft player and guild statistics
- Item analysis, price checking, and weight calculation
- Leaderboard queries and rankings
- Build and recipe search
- Guild tower calculations
- Server uptime and online player tracking
- AI-powered features (GPT integration)

### Configuration
Bot configuration is managed through `lib/config.py` and environment variables:
- Bot token and API keys
- Path configurations
- Global state variables
- Feature flags

## Web (`web/`)

The web component is a modern, responsive frontend application that provides an interactive interface for all Nori features.

### Technology Stack
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Architecture**: Client-side rendering with API integration
- **Styling**: Custom CSS with dark theme support

### Main Components
- **`index.html`** - Main landing page and hub
- **`wynn/`** - Wynncraft-specific tools and pages
  - `player/` - Player statistics viewer
  - `guild/` - Guild information and statistics
  - `leaderboard/` - Various leaderboard displays
  - `item/` - Item analysis, lootpool, changelog, simulation
  - `build/` - Build search and management
  - `recipe/` - Recipe search
  - `aspects/` - Aspect browser
  - `uptime/` - Server uptime tracking
  - `online/` - Online player activity
- **`js_global/`** - Shared JavaScript modules
  - `fetch_player.js` - Player data fetching
  - `fetch_guild.js` - Guild data fetching
  - `item_analysis.js` - Item analysis interface
  - `item_rendering.js` - Item visualization
  - `leaderboard.js` - Leaderboard rendering
  - `build_search.js` - Build search functionality
  - `recipe_search.js` - Recipe search functionality
  - `config.js` - API configuration
  - `layout.js` - Page layout management
- **`css_global/`** - Shared stylesheets
  - `default.css` - Base styles
  - `dark_theme.css` - Dark mode support
  - `sidebar.css` - Navigation sidebar

### Features
- Responsive design for desktop and mobile
- Real-time data visualization
- Interactive item analysis and rendering
- Dark/light theme support
- Client-side routing and navigation
- API integration for all backend services

### Pages
- **Home** (`index.html`) - Project hub and navigation
- **Wynn Tools** (`wynn/index.html`) - Main Wynncraft tools page
- **Item Analysis** (`wynn/item/analysis/`) - Item decoder and analyzer
- **Leaderboards** (`wynn/leaderboard/`) - Various leaderboard views
- **Player Stats** (`wynn/player/`) - Player information viewer
- **Guild Stats** (`wynn/guild/`) - Guild information viewer

## Database (`db/`)

The database component handles backend services, data management, API endpoints, and data processing for the entire Nori ecosystem.

### Technology Stack
- **Language**: Python 3.x
- **Database**: AWS-hosted database (implementation details closed-source)
- **Key Libraries**: 
  - `aiohttp` - Async HTTP client
  - `matplotlib` - Data visualization
  - `numpy` - Data processing

### Main Components
- **`main.py`** - Main database service entry point (closed-source)
- **`tester/`** - Development and testing utilities
  - `data_fetch.py` - Wynncraft API data fetching and caching
  - `tracker.py` - Server uptime and player activity tracking

### Features
- RESTful API endpoints for all Nori services
- Real-time data synchronization with Wynncraft API
- Player and guild statistics caching
- Leaderboard data processing and ranking
- Command usage tracking and analytics
- User activity logging
- AI feature data management (prompts, responses)
- Rate limiting and authentication

### API Endpoints
The database component provides various API endpoints (documented at [nori.fish/docs/api.md](https://nori.fish/docs/api.md)):
- Item analysis and price checking
- Player and guild statistics
- Leaderboard data
- Build and recipe search
- Lootpool information
- Server uptime data
- Online player activity

### Development Tools
The `tester/` directory contains utilities for:
- Fetching and caching Wynncraft API data locally
- Tracking server uptime and player activity
- Generating activity graphs and visualizations
- Building local data caches for development

## Component Interaction

- **Bot** and **Web** both communicate with **DB** (API) for data
- **DB** fetches and caches data from Wynncraft API
- All components can operate independently but share the same backend

## Development

Each component can be developed and tested independently:

1. **Bot Development**: Run `nori_bot.py` with proper environment variables
2. **Web Development**: Serve `web/` directory with any static file server
3. **DB Development**: Use `tester/` utilities for local development and testing

See individual component directories for more specific development instructions.

## Notes

- The database main implementation (`db/main.py`) is closed-source
- Development and testing utilities are available in `db/tester/`
- All components share configuration through environment variables
- API documentation is available at [nori.fish/docs/](https://nori.fish/docs/)

