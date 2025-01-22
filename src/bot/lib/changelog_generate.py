"""
Author: RawFish
Description: Module for generating changelogs (items, ingredients, etc.)
"""

import json
import time
from datetime import datetime
from typing import Dict, Any


class ChangelogManager:
    """
    A manager for generating item and ingredient changelogs.
    """

    def __init__(
        self,
        item_changelog_dir: str = "your path",
        ingredient_changelog_dir: str = "your path",
    ):
        """
        :param item_changelog_dir: Base path for item changelog output.
        :param ingredient_changelog_dir: Base path for ingredient changelog output.
        """
        self.item_changelog_base = item_changelog_dir
        self.ingredient_changelog_base = ingredient_changelog_dir

    async def generate_item_changelog(
        self, before_json: Dict[str, Any], after_json: Dict[str, Any]
    ) -> str:
        """
        Generates a changelog for items by comparing two dicts:
         - `before_json` (old data)
         - `after_json` (new data)

        :param before_json: The old item database (dict).
        :param after_json: The new item database (dict).
        :return: The filename (without extension) of the generated changelog.
        """
        non_items = {"ingredient", "tool", "tome", "charm", "material"}
        changelog_data = {"Changed": {}, "Added": {}, "Removed": {}, "Generated": {}}

        # Build sets for easier detection
        before_keys = set(before_json.keys())
        after_keys = set(after_json.keys())

        items_added = "## Items Added:\n"
        items_removed = "## Items Removed:\n"
        changelog_text = ""

        # Detect newly added items
        for added_item in (after_keys - before_keys):
            # Only consider if it's not in non_items
            if "type" in after_json[added_item]:
                if after_json[added_item]["type"] not in non_items:
                    items_added += f"- {added_item}\n"
                    changelog_data["Added"][added_item] = after_json[added_item]

        # Detect removed items
        for removed_item in (before_keys - after_keys):
            if "type" in before_json[removed_item]:
                if before_json[removed_item]["type"] not in non_items:
                    items_removed += f"- {removed_item}\n"
                    changelog_data["Removed"][removed_item] = before_json[removed_item]

        # Check items present in both
        common_items = before_keys & after_keys
        for item_name in common_items:
            # If it’s not one of the non-item types
            if "type" in before_json[item_name]:
                if before_json[item_name]["type"] not in non_items:
                    # Check if the entire object differs
                    if before_json[item_name] != after_json[item_name]:
                        # Something changed
                        changelog_text += f"### {item_name}\n"
                        self._compare_item_fields(
                            item_name,
                            before_json[item_name],
                            after_json[item_name],
                            changelog_data,
                            changelog_text
                        )
                        changelog_text += "\n"

        # Build final text
        current_datetime = datetime.now().strftime("%Y-%m-%d")
        current_time = int(time.time())
        changelog_data["Generated"]["Date"] = current_datetime
        changelog_data["Generated"]["Timestamp"] = current_time

        header = (
            f"# Item Changelog generated at {current_datetime}\n"
            f"## Summary: {len(changelog_data['Changed'])} items changed, "
            f"{len(changelog_data['Added'])} items added, {len(changelog_data['Removed'])} items removed.\n"
        )
        changelog_text = header + "## Items Changes:\n\n" + changelog_text
        changelog_text += items_added + "\n" + items_removed

        # Write outputs
        json_out = f"{self.item_changelog_base}.json"
        md_out = f"{self.item_changelog_base}.md"
        md_timestamped_out = f"{self.item_changelog_base}_{current_datetime}.md"

        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(changelog_data, f, indent=2)

        with open(md_out, "w", encoding="utf-8") as f:
            f.write(changelog_text)

        with open(md_timestamped_out, "w", encoding="utf-8") as f:
            f.write(changelog_text)

        print(f"Item changelog generated {current_datetime}")
        return f"item_changelog_{current_datetime}"

    def _compare_item_fields(
        self,
        item_name: str,
        before_data: Dict[str, Any],
        after_data: Dict[str, Any],
        changelog_data: Dict[str, Any],
        changelog_text: str
    ) -> None:
        """
        Compare individual fields within the before/after data for a single item.
        Modifies `changelog_data` in-place and appends to `changelog_text`.
        """
        # To keep building the text, we can store each line in a list & join at the end
        lines = []
        changed_dict = changelog_data["Changed"].setdefault(item_name, {})

        before_fields = set(before_data.keys())
        after_fields = set(after_data.keys())

        # Check identifications separately
        if "identifications" in before_data and "identifications" in after_data:
            pre_id = before_data["identifications"]
            post_id = after_data["identifications"]
            if pre_id != post_id:
                changed_dict.setdefault("ids", {})

                pre_id_keys = set(pre_id.keys())
                post_id_keys = set(post_id.keys())

                # Removed IDs
                for removed_id in pre_id_keys - post_id_keys:
                    changed_dict["ids"].setdefault("Removed", {})
                    changed_dict["ids"]["Removed"][removed_id] = pre_id[removed_id]
                    lines.append(f"- Removed ID: {removed_id} {pre_id[removed_id]}")

                # New IDs
                for new_id in post_id_keys - pre_id_keys:
                    changed_dict["ids"].setdefault("New", {})
                    changed_dict["ids"]["New"][new_id] = post_id[new_id]
                    lines.append(f"- New ID: {new_id} {post_id[new_id]}")

                # Changed IDs
                common_id_keys = pre_id_keys & post_id_keys
                for stat_id in common_id_keys:
                    if pre_id[stat_id] != post_id[stat_id]:
                        changed_dict["ids"].setdefault("Change", {})
                        changed_dict["ids"]["Change"][stat_id] = {
                            "Before": pre_id[stat_id],
                            "After": post_id[stat_id],
                        }
                        lines.append(
                            f"- Changed ID: {stat_id} {pre_id[stat_id]} -> {post_id[stat_id]}"
                        )

        # Compare standard fields (excluding identifications which is handled above)
        for field in (before_fields | after_fields):
            if field == "identifications":
                continue
            # If field was removed
            if field in before_fields and field not in after_fields:
                changed_dict.setdefault("Removed_Fields", {})
                changed_dict["Removed_Fields"][field] = before_data[field]
                lines.append(f"- Removed field {field}: {before_data[field]}")
            # If field is new
            elif field in after_fields and field not in before_fields:
                changed_dict.setdefault("New", {})
                changed_dict["New"][field] = after_data[field]
                lines.append(f"- Added {field}: {after_data[field]}")
            else:
                # Field in both, check if changed
                if before_data[field] != after_data[field]:
                    changed_dict.setdefault(field, {})
                    changed_dict[field]["Before"] = before_data[field]
                    changed_dict[field]["After"] = after_data[field]
                    lines.append(
                        f"- {field}: {before_data[field]} -> {after_data[field]}"
                    )

        # Append lines to the global changelog_text
        if lines:
            # In Python, strings are immutable, so returning the new text might be simpler
            # but since we pass it in, we just rely on them being appended in the caller.
            # For clarity, we can store them in a list and return. We'll just do:
            for line in lines:
                changelog_text += line + "\n"

    async def generate_ingredient_changelog(
        self, before_json: Dict[str, Any], after_json: Dict[str, Any]
    ) -> str:
        """
        Generates a changelog for ingredients by comparing two dicts.

        :param before_json: Old ingredient data.
        :param after_json: New ingredient data.
        :return: The filename (without extension) of the generated changelog.
        """
        changelog_data = {"Changed": {}, "Added": {}, "Removed": {}, "Generated": {}}
        ing_added = "## Ingredients Added:\n"
        ing_removed = "## Ingredients Removed:\n"
        changelog_text = ""

        before_keys = set(before_json.keys())
        after_keys = set(after_json.keys())

        # Detect newly added ingredients
        for added_ing in (after_keys - before_keys):
            if "ingredient" in after_json[added_ing].get("type", ""):
                ing_added += f"- {added_ing}\n"
                changelog_data["Added"][added_ing] = after_json[added_ing]

        # Detect removed ingredients
        for removed_ing in (before_keys - after_keys):
            if "ingredient" in before_json[removed_ing].get("type", ""):
                ing_removed += f"- {removed_ing}\n"
                changelog_data["Removed"][removed_ing] = before_json[removed_ing]

        # Compare common ingredients
        common_ings = before_keys & after_keys
        for ing_name in common_ings:
            before_data = before_json[ing_name]
            after_data = after_json[ing_name]
            if "ingredient" in before_data.get("type", ""):
                if before_data != after_data:
                    changelog_text += f"### {ing_name}\n"
                    self._compare_ingredient_fields(
                        ing_name, before_data, after_data, changelog_data, changelog_text
                    )
                    changelog_text += "\n"

        current_datetime = datetime.now().strftime("%Y-%m-%d")
        current_time = int(time.time())
        header = (
            f"# Ingredient Changelog generated at {current_datetime}\n"
            f"## Summary: {len(changelog_data['Changed'])} ingredients changed, "
            f"{len(changelog_data['Added'])} added, {len(changelog_data['Removed'])} removed.\n"
        )
        changelog_text = header + "## Ingredient Changes:\n\n" + changelog_text
        changelog_text += ing_added + "\n" + ing_removed

        changelog_data["Generated"]["Date"] = current_datetime
        changelog_data["Generated"]["Timestamp"] = current_time

        # Save the files
        json_out = f"{self.ingredient_changelog_base}.json"
        md_out = f"{self.ingredient_changelog_base}.md"
        md_timestamped_out = f"{self.ingredient_changelog_base}_{current_datetime}.md"

        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(changelog_data, f, indent=2)

        with open(md_out, "w", encoding="utf-8") as f:
            f.write(changelog_text)

        with open(md_timestamped_out, "w", encoding="utf-8") as f:
            f.write(changelog_text)

        print(f"Ingredient changelog generated {current_datetime}")
        return f"ingredient_changelog_{current_datetime}"

    def _compare_ingredient_fields(
        self,
        ing_name: str,
        before_data: Dict[str, Any],
        after_data: Dict[str, Any],
        changelog_data: Dict[str, Any],
        changelog_text: str,
    ):
        """
        Compare individual fields for an ingredient and populate changelog data.
        """
        lines = []
        changed_dict = changelog_data["Changed"].setdefault(ing_name, {})

        before_fields = set(before_data.keys())
        after_fields = set(after_data.keys())

        for field in (before_fields | after_fields):
            if field in before_fields and field not in after_fields:
                # Field removed
                changed_dict.setdefault("Removed_Fields", {})
                changed_dict["Removed_Fields"][field] = before_data[field]
                lines.append(f"- Removed field {field}: {before_data[field]}")
            elif field in after_fields and field not in before_fields:
                # New field
                changed_dict.setdefault("New", {})
                changed_dict["New"][field] = after_data[field]
                lines.append(f"- Added {field}: {after_data[field]}")
            else:
                # Field in both, check if changed
                if before_data[field] != after_data[field]:
                    changed_dict.setdefault(field, {})
                    changed_dict[field]["Before"] = before_data[field]
                    changed_dict[field]["After"] = after_data[field]
                    lines.append(f"- {field}: {before_data[field]} -> {after_data[field]}")

        for line in lines:
            changelog_text += line + "\n"
