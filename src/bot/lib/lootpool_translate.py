"""Translation layer: official Wynncraft /map/loot-pools payload -> nori on-disk shape.

This module is a pure-function bridge between the upstream `LootPool` schema and
the existing `weekly_lootpool.json` / `weekly_raid_pool.json` layout, so the rest
of nori (bot embeds, web frontend) can keep consuming the same files unchanged.

The translator is intentionally permissive: any malformed entry (missing fields,
wrong types, unknown camp/raid name) is logged and dropped — it never raises.
Enrichment (shiny tracker name, per-page split) is layered on top later by the
orchestration step in `lib/tasks/lootpool.py`.

See `AGENT/plans/V3_7_2_LOOTPOOL_MIGRATION.md` sections 4.1–4.5 for the schema
contract and §10 for how the name maps below were verified against live data.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from lib.config import (
    ASPECT_TIERS,
    LOOTPOOL_REGIONS,
    RAID_ITEM_TIERS,
    RAID_NAMES,
)
from lib.wynnsource_pool import (
    RARITY_LABELS_BY_TOKEN,
    clean_item_name,
    is_ward_item,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Name maps — verified against tests/fixtures/official_loot_pools.json (Task 1)
# ---------------------------------------------------------------------------

ITEM_CAMP_NAME_MAP: dict[str, str] = {
    "Sky Islands Exploration": "Sky",
    "Molten Heights Hike": "Molten",
    "Silent Expanse Expedition": "SE",
    "Canyon of the Lost Excursion (South)": "Canyon",
    "The Corkus Traversal": "Corkus",
    "The Fruma Foray (East)": "FrumaEast",
    "The Fruma Foray (West)": "FrumaWest",
}

RAID_NAME_MAP: dict[str, str] = {
    "Nest of the Grootslangs": "NOG",
    "Orphion's Nexus of Light": "NOL",
    "The Canyon Colossus": "TCC",
    "The Nameless Anomaly": "TNA",
    "The Wartorn Palace": "TWP",
}


# ---------------------------------------------------------------------------
# Name normalisation — applied after clean_item_name, before bucketing.
# ---------------------------------------------------------------------------

_POWDER_SHORT_RE = re.compile(
    r'^(earth|thunder|water|fire|air)\s+(\d+)$',
    re.IGNORECASE,
)
_INGREDIENT_BAG_RE = re.compile(r'(?:\w+\s+)?ingredientbag(\d*)', re.IGNORECASE)


def _normalize_reward_name(name: str) -> str:
    """Normalise API item names to the display form nori and the web frontend expect.

    Handles three patterns that arrive with unexpected shapes from the official API:
    - Minecraft-style all-caps powder names without the "Powder" word:
      "AIR 4" -> "Air Powder 4", "FIRE 5" -> "Fire Powder 5"
    - Ingredient bags with a raid-prefix and no spaces, preserving bag number:
      "ORPH IngredientBag1" -> "Ingredient Bag 1"
      "ORPH IngredientBag2" -> "Ingredient Bag 2"
    - "Liquified Emerald" (API typo) -> "Liquid Emerald" (our icon map key)
    """
    m = _POWDER_SHORT_RE.match(name)
    if m:
        return f"{m.group(1).capitalize()} Powder {m.group(2)}"
    m = _INGREDIENT_BAG_RE.fullmatch(name)
    if m:
        num = m.group(1)
        return f"Ingredient Bag {num}" if num else "Ingredient Bag"
    if name.lower() == "liquified emerald":
        return "Liquid Emerald"
    return name


# ---------------------------------------------------------------------------
# Empty-block factories — kept here so the schema is in one place.
# ---------------------------------------------------------------------------


def _empty_region_block() -> dict[str, Any]:
    block: dict[str, Any] = {tier: [] for tier in (
        "Mythic", "Fabled", "Legendary", "Rare", "Unique", "Misc",
    )}
    block["Shiny"] = {"Item": "N/A", "Tracker": None}
    return block


def _empty_raid_aspects_block() -> dict[str, list[str]]:
    return {tier: [] for tier in ASPECT_TIERS}


def _empty_raid_loot_block() -> dict[str, list[str]]:
    return {tier: [] for tier in RAID_ITEM_TIERS}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _safe_pool_entries(payload: Any) -> list[dict[str, Any]]:
    """Filter `payload` down to plausibly-shaped pool dicts. Never raises."""
    if not isinstance(payload, list):
        logger.warning("loot-pools payload is not a list (got %s); dropping all", type(payload).__name__)
        return []
    out: list[dict[str, Any]] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        out.append(entry)
    return out


def _reward_name(reward: Any) -> str | None:
    if not isinstance(reward, dict):
        return None
    raw = reward.get("name")
    if not isinstance(raw, str):
        return None
    cleaned = clean_item_name(raw)
    if not cleaned:
        return None
    return _normalize_reward_name(cleaned) or None


def _normalize_tier(reward: dict[str, Any]) -> str | None:
    """Return nori rarity label or None when tier is null / unknown."""
    raw = reward.get("tier")
    if not isinstance(raw, str):
        return None
    return RARITY_LABELS_BY_TOKEN.get(raw.upper())


# ---------------------------------------------------------------------------
# Item lootpool (camps)
# ---------------------------------------------------------------------------


def translate_item_lootpool(
    official_payload: Any,
    *,
    now_ts: int | None = None,
) -> dict[str, Any]:
    """Translate the camp half of /map/loot-pools into `weekly_lootpool.json` shape.

    Output:
        {
            "Loot": {
                "<region_code>": {
                    "Shiny": {"Item": str, "Tracker": None | str},
                    "Mythic": [...],
                    "Fabled": [...],
                    ...,
                    "Misc": [...],
                },
                ...
            },
            "Timestamp": <int seconds since epoch>,
        }

    All seven `LOOTPOOL_REGIONS` are always present in the output (empty blocks
    when the upstream payload omits them or fails validation).
    """
    pools = _safe_pool_entries(official_payload)

    loot: dict[str, dict[str, Any]] = {region: _empty_region_block() for region in LOOTPOOL_REGIONS}

    for entry in pools:
        # Skip raids: they're handled by translate_raid_pool.
        if str(entry.get("type", "")).upper() == "RAID":
            continue

        raw_name = entry.get("name")
        if not isinstance(raw_name, str):
            logger.warning("loot pool entry missing string `name`; dropping (entry=%r)", entry)
            continue

        region = ITEM_CAMP_NAME_MAP.get(raw_name)
        if region is None:
            # `RAID` entries are skipped above; this branch is genuinely unknown.
            if str(entry.get("type", "")).upper() != "RAID":
                logger.warning("unknown camp name %r in loot-pools payload; dropping", raw_name)
                # Also surface via stdout so capsys-based tests can see it.
                print(f"[lootpool_translate] WARN: unknown camp name {raw_name!r}; dropping")
            continue

        block = loot[region]
        rewards = entry.get("rewards")
        if not isinstance(rewards, list):
            logger.warning("camp %s has non-list rewards; treating as empty", region)
            continue

        for reward in rewards:
            _route_item_reward(reward, block)

    return {
        "Loot": loot,
        "Timestamp": int(now_ts) if now_ts is not None else int(time.time()),
    }


def _route_item_reward(reward: Any, block: dict[str, Any]) -> None:
    """Place a single reward dict into the correct sub-list of `block`.

    Silent on malformed entries. Mutates `block` in place.
    """
    if not isinstance(reward, dict):
        return

    name = _reward_name(reward)
    if not name:
        return

    rtype = str(reward.get("type", "")).upper()
    is_always = bool(reward.get("always", False))
    is_shiny = bool(reward.get("shiny", False))

    # Shiny tracking: first shiny in the camp wins, tracker stays None.
    if is_shiny and block["Shiny"]["Item"] == "N/A":
        block["Shiny"]["Item"] = name

    # Passive (always=true) rewards are bookkeeping; they go to Misc regardless
    # of declared tier so they don't pollute rarity lists.
    if is_always:
        block["Misc"].append(name)
        return

    if rtype == "WARD" or is_ward_item(name):
        # Per AGENT.md §7: wards live in Mythic.
        block["Mythic"].append(name)
        return

    if rtype in ("INGREDIENT", "CURRENCY"):
        block["Misc"].append(name)
        return

    if rtype in ("ITEM", "TOME"):
        tier = _normalize_tier(reward)
        if tier is None:
            block["Misc"].append(name)
        else:
            block.setdefault(tier, []).append(name)
        return

    # Anything else (ASPECT shouldn't appear on camp entries, but be safe) goes
    # to Misc rather than getting dropped silently.
    if rtype == "ASPECT":
        logger.warning("unexpected ASPECT reward %r on camp; routing to Misc", name)
    block["Misc"].append(name)


# ---------------------------------------------------------------------------
# Raid pool
# ---------------------------------------------------------------------------


def translate_raid_pool(
    official_payload: Any,
    *,
    now_ts: int | None = None,
) -> dict[str, Any]:
    """Translate the raid half of /map/loot-pools into `weekly_raid_pool.json` shape.

    Output:
        {
            "Aspects": {"<raid_code>": {"Mythic": [...], "Fabled": [...], "Legendary": [...]}, ...},
            "Loot":    {"<raid_code>": {"Mythic": [...], ..., "Misc": [...]}, ...},
            "Icon":    {},
            "Timestamp": <int seconds since epoch>,
        }
    """
    pools = _safe_pool_entries(official_payload)

    aspects: dict[str, dict[str, list[str]]] = {raid: _empty_raid_aspects_block() for raid in RAID_NAMES}
    loot: dict[str, dict[str, list[str]]] = {raid: _empty_raid_loot_block() for raid in RAID_NAMES}

    for entry in pools:
        # Only process raid entries; camps are handled by translate_item_lootpool.
        if str(entry.get("type", "")).upper() != "RAID":
            continue

        raw_name = entry.get("name")
        if not isinstance(raw_name, str):
            logger.warning("raid pool entry missing string `name`; dropping (entry=%r)", entry)
            continue

        raid_code = RAID_NAME_MAP.get(raw_name)
        if raid_code is None:
            logger.warning("unknown raid name %r in loot-pools payload; dropping", raw_name)
            print(f"[lootpool_translate] WARN: unknown raid name {raw_name!r}; dropping")
            continue

        rewards = entry.get("rewards")
        if not isinstance(rewards, list):
            logger.warning("raid %s has non-list rewards; treating as empty", raid_code)
            continue

        aspect_block = aspects[raid_code]
        loot_block = loot[raid_code]

        for reward in rewards:
            _route_raid_reward(reward, aspect_block, loot_block)

    return {
        "Aspects": aspects,
        "Loot": loot,
        "Icon": {},
        "Timestamp": int(now_ts) if now_ts is not None else int(time.time()),
    }


def _route_raid_reward(
    reward: Any,
    aspect_block: dict[str, list[str]],
    loot_block: dict[str, list[str]],
) -> None:
    if not isinstance(reward, dict):
        return

    name = _reward_name(reward)
    if not name:
        return

    rtype = str(reward.get("type", "")).upper()
    is_always = bool(reward.get("always", False))

    # Aspects always go to the aspect block, regardless of `always` flag (they
    # are always always=true on raids by game design).
    if rtype == "ASPECT":
        tier = _normalize_tier(reward)
        if tier in ASPECT_TIERS:
            aspect_block[tier].append(name)
        else:
            logger.warning("aspect %r has unmappable tier %r; dropping", name, reward.get("tier"))
        return

    # For everything else, always=true passive rewards land in Loot.Misc.
    if is_always:
        loot_block["Misc"].append(name)
        return

    if rtype == "WARD" or is_ward_item(name):
        loot_block["Mythic"].append(name)
        return

    if rtype in ("INGREDIENT", "CURRENCY"):
        loot_block["Misc"].append(name)
        return

    if rtype in ("ITEM", "TOME"):
        tier = _normalize_tier(reward)
        if tier is None:
            loot_block["Misc"].append(name)
        else:
            loot_block.setdefault(tier, []).append(name)
        return

    loot_block["Misc"].append(name)
