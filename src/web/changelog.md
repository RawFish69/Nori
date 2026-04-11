# Nori-Wynn Changelog

## 2026-04-11
### Raid Platform Consolidation
- Migrated raid command routing to `/raid aspect`, `/raid item`, and `/raid gambit`.
- Kept `/aspect lootpool` as a deprecation alias that points users to the `/raid` commands.
- Standardized public raid links to `https://nori.fish/wynn/raids`.

### API and Data
- Added `GET /api/raids` for combined raid payload delivery.
- Kept `GET /api/aspects` backward-compatible for legacy aspect-only consumers.
- Normalized raid payload shape around direct sections:
  - `Aspects`
  - `Items`
  - `Gambits`
- Updated gambit handling for the WCS breaking change: all raids now share one daily gambit set.

### Web Frontend
- Added `/wynn/raids` as the primary raid page.
- Redirected `/wynn/aspects` to `/wynn/raids`.
- Added source toggles on raids page: `All`, `Aspects only`, `Items only`.
- Added shared daily gambit overview block with a refresh countdown.
- Kept per-raid card layout and tier filters for aspect and item sections.
- Improved aspect description hover tooltip behavior and layering.
- Added icon handling for wards and misc items (powders, runes, keys, emerald variants).
- Added duplicate compression for repeated item entries (`Item xN`) to reduce clutter.

### Documentation
- Updated API docs to include `/api/raids` and current gambit behavior.
- Refreshed command docs to match current slash command surface.

## Legacy Notes
Older pre-2026 release notes are preserved in git history.
