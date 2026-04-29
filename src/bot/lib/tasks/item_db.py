"""Item DB, changelog, aspect DB, and in-guild leaderboard refresh loop."""

import asyncio
import json
import time
from datetime import datetime

import hikari

import lib.config as config
from lib.aspect_utils import update_aspects
from lib.item_db_compat import items_response_to_dict, looks_like_item_database
from lib.leaderboard_cache import load_leaderboard_in_guild
from lib.manager_registry import get_managers


def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def _normalize_item_map(raw_items) -> dict:
    try:
        normalized, summary = items_response_to_dict(raw_items)
        if summary is not None:
            print(
                f"[ItemDB refresh] normalized v3.7 list: {summary['total']} keys, "
                f"{len(summary['collisions'])} displayName collisions"
            )
        if not looks_like_item_database(normalized):
            print("[ItemDB refresh] normalized item map is invalid; ignoring it.")
            return {}
        return normalized
    except Exception as error:
        print(f"[ItemDB refresh] item map normalization failed: {type(error).__name__}: {error}")
        return {}


async def item_db_refresh_task(bot: hikari.GatewayBot, interval: int = 7200):
    """Refresh item/aspect static data and guild leaderboard cache every 2 hours."""
    print(f"Repeat Task interval: {interval} seconds")
    while True:
        try:
            managers = get_managers()
            item_manager = managers.get("item_manager")
            changelog_manager = managers.get("changelog_manager")

            config.lb_in_guild = load_leaderboard_in_guild()
            item_path = config.BOT_PATH / "items.json"
            before_items = _normalize_item_map(config.item_map or _load_json(item_path, {}))
            had_valid_before_items = bool(before_items)

            updated_count = await asyncio.to_thread(item_manager.update_items, str(item_path)) if item_manager is not None else 0
            after_items = _normalize_item_map(_load_json(item_path, {}))
            if updated_count <= 0 and not after_items and before_items:
                after_items = before_items

            if updated_count <= 0 or before_items == after_items:
                print("No change detected from ItemDB API.")
                config.item_map = after_items or before_items
            elif not had_valid_before_items:
                print("ItemDB recovered from invalid baseline; skipping changelog generation.")
                config.item_map = after_items
            else:
                print("ItemDB change detected, generating changelogs.")
                if changelog_manager is not None:
                    file_name = await changelog_manager.generate_item_changelog(before_items, after_items)
                    await changelog_manager.generate_ingredient_changelog(before_items, after_items)
                else:
                    file_name = None

                current_date = datetime.now().strftime("%Y-%m-%d")
                archive_path = config.BOT_PATH / "item_db" / f"items_{current_date}.json"
                if item_manager is not None:
                    await asyncio.to_thread(item_manager.update_items, str(archive_path))
                config.item_map = after_items

                if file_name and config.ITEM_DB_LOG_CHANNEL_ID:
                    changelog_path = config.BOT_PATH / "changelog" / f"{file_name}.md"
                    await bot.rest.create_message(
                        channel=config.ITEM_DB_LOG_CHANNEL_ID,
                        content="Local ItemDB Updated.",
                        attachment=hikari.files.File(str(changelog_path)),
                    )

        config.item_db_last_updated = int(time.time())
        await asyncio.to_thread(update_aspects, config.BOT_PATH / "aspects.json")
        except Exception as error:
            print(f"[ItemDB refresh] unexpected error: {type(error).__name__}: {error}")

        await asyncio.sleep(interval)
