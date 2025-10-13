# Nori-Wynn Changelog

## Latest Changes
- Removed ads
- UI Overhaul

### v1.0.2
- Nori now checks API itemDB and generates changelog automatically
- Reworked guild tower stats calculation, now works for both HQ and regular tower, user may define the upgrades and links/externals
- Build & Pricecheck features up to date and maintained

### v1.0.3
- Added a command where it shows weekly loot pool from Lootrun camps
- Added lootpool history lookup

### v1.0.4
- Added Ingredient search
- Added function to update the database with API and create new data files, this allows better generation of changelog, and able to output downloadable files in chat.

### v1.0.5
- Automated data update for guilds, items, ingredients
- Ingredient changelog can be viewed via command /ingredient changelog
- Lootpool history now shows up to 12 weeks
- Guild tower graphs

### v1.0.6
- Reworked Code Structure to boost performance

### v1.0.7
- Reworked wrapper for Wynncraft API v3
- Reworked Player, Guild, Leaderboard modules

### v1.0.8
- Reworked Item search, item roll functions to fit Wynncraft API v3 Item data
- Added calculator & plotter for mathematical operations, including derivative and integrals
- Enhanced overall performance by algorithm change

### v1.0.9 - v1.1.2
- Mini-game related
- Reworked structure to deal with memory leaks, to prepare for server migration

### v1.1.3
- Migrated to a VPS with much higher capacity
- Reworked leaderboard (/lb) command, now shows global player leaderboard instead of guild-specific.
- Established database for player stats, updating on an hourly basis, shares the same server as Nori-bot
- Pricecheck updated with regression & spline prediction models, the base prices will be maintained by the contributor.

### v1.1.4
- Fixed issue where players with a certain version of wynntils cannot perform auto pricecheck
- Fixed rounding error of item identification simulator
- Added player activity display, command: /online

### v1.1.5
- Added internal maintenance tools
- Added 4 more item tiers to lootpool
- Updated Item decoder to support latest wynntils gear item format

### v1.1.6
- Reworked Item lootpool history feature
- User may now search for specific item from historical record

### v1.1.7
- Most scales are updated to the current sandbox, and more specific scales will be added in the near future.
- Items now have multiple scales, this will affect both weighing and pricechecking. The highest weight value will be used for any sort of price analysis.
- The current mythic rankings are based on Main scale for each item, feel free to check your items using /item weigh command, with the wynntils f3 item.
- These changes are aimed to make the weight system less "outdated" and more fitting to measure the effectiveness of items.

### v1.1.8
- Updated item/ingredient chanagelog generation for v3 API format
- Nori-bot checks item-db every 12 hours and generates log if any change is present in the item data
- Updated ingredient search for v3 API format

### v1.1.9
- Build / Recipe Maintenance Tools
- Server uptime and soul point timer data now fetched from Nori-API
- Reworked backend to be more compatible with Nori-Web

### v1.2.0
- Improved backend to work better with Nori-Web
- MISC Fixes

### v1.2.1 
- Fixed url synchronization issue for build, recipe, player, guild searching.

### v1.2.2
- Performance improvement

### v1.2.3
- New Icon for Nori-Web
- MISC Fixes

### v1.2.4
- Custom command for submitting sales/trade in Marketplace community, including custom rendering

### v1.2.5
- Pricecheck system upgrade: Now sales data submitted by user also contribute to the price estimation algorithm
- Reworked price estimation function that yields result, added interpolation method as a fail-safe route if both regression and spline produce invalid result.
- Plot quality improvement

### v1.2.6
- Item changelog page now shows all changes since 2.0.3

### v1.3.0
- Added Canyon of the lost (COTL) to Item Lootpool
- Prepare internal structure for upcoming wynn 2.1 update
- Codebase clean-up

### v1.3.1
- Adjusted function to fit new Item Database format
- Changed CDN path from Wynncraft
- Added Aspect Lootpool to both Discord Bot and Website

### v1.3.2
- UI Overhaul

### v1.3.3
- Reworked home page & Wynn main page
- **Removed ads**