# Nori Map frontend

Interactive world clocks, weather, categorized natural-event reports and airspace planning references. Live app: https://nori.fish/map/.

This directory contains browser code, map assets and third-party license notices only. It includes no backend runtime, credentials, deployment configuration or runtime datasets.

## Preview and test

From `src/web`, open `map/index.html` directly, or serve the frontend locally:

```sh
python -m http.server 8000
node --test tests/map/*.test.cjs
```

The homepage embeds a compact interactive preview. Opening the full map preserves the selected location and event layers. Location permission is requested only after clicking Locate me. Saved places and display preferences stay in that browser's localStorage; no account synchronization is provided.

## Hosted API dependency

The China report layer calls the public, read-only endpoint `https://nori.fish/api/map/china-alerts`. No API key or production credentials are needed. This public repository does not include the hosted backend. Running the static frontend locally does not start an API server. If a feed is unavailable, the map reports the missing coverage rather than substituting generated data.

Other browser feeds include Open-Meteo, USGS, NASA EONET, NWS, Hong Kong Observatory and US FAA/USGS land-use services. Sources, dates and coverage limits appear in the tool. Address searches are sent to Photon only when submitted. Weather requests send the selected coordinates to Open-Meteo. Review each provider's service terms before operating a separate hosted deployment.

## Meaning and coverage

Weather categories share filters across supported sources; severity retains the source's meaning. Mainland China reports include updates and cancellations and are not a complete active-warning inventory. Regional badges use reference points rather than precise event locations or hazard boundaries. Expired snapshots are rejected.

US flight colors describe only loaded datasets, not permission to fly. Temporary restrictions and local ground rules remain incomplete. Mainland China and Hong Kong airspace polygons are not loaded; their planning options link to CAAC UOM and Hong Kong CAD and are labeled Not assessed. Airport markers are references only.

## Attribution

MapLibre GL JS, OpenFreeMap/Positron style notices and licenses are included under `vendor/`. Map data uses OpenStreetMap/OpenMapTiles and a Natural Earth public-domain land outline. Keep these notices and visible map attribution when redistributing the frontend.
