"""
Compatibility shim for Wynncraft item API v3.3 → v3.7 migration.

In v3.7, GET /v3/item/database?fullResult returns a list of item objects.
In v3.3, it returned a dict keyed by displayName.

This module provides items_response_to_dict() which normalises both formats
into a dict, using internalName as a fallback key when displayName collides
(needed for the 7 "Ascended" mythics that share a displayName with their
original counterpart, e.g. "Fatal" / "Masterwork Fatal").
"""
import json


def looks_like_item_database(data) -> bool:
    """Return True only for a plausible item database, not API error payloads."""
    if isinstance(data, list):
        if len(data) < 1000:
            return False
        sample = next((item for item in data if isinstance(item, dict)), None)
        return isinstance(sample, dict) and ("internalName" in sample or "displayName" in sample)

    if not isinstance(data, dict) or len(data) < 1000:
        return False
    if any(key in data for key in ("error", "Error", "detail", "code", "message")) and len(data) < 20:
        return False
    sample = next((value for value in data.values() if isinstance(value, dict)), None)
    return isinstance(sample, dict) and ("internalName" in sample or "displayName" in sample)


def load_item_map(path):
    """Load items.json and return a displayName-keyed dict.

    Accepts both list (current API shape) and dict (legacy on-disk shape).
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    result, _ = items_response_to_dict(raw)
    if not looks_like_item_database(result):
        raise ValueError(f"{path} is not a valid item database")
    return result


def items_response_to_dict(response):
    """Convert a Wynncraft item API response to a displayName-keyed dict.

    Args:
        response: Either a legacy dict (v3.3) or a list of item objects (v3.7).

    Returns:
        - For dict input : (response, None)  — passthrough, no summary.
        - For list input : (result_dict, summary) where summary is
          {"collisions": [(displayName, [internalName, ...])], "total": int}.
    """
    if isinstance(response, dict):
        return response, None

    if not isinstance(response, list):
        raise TypeError(f"Expected dict or list, got {type(response).__name__!r}")

    result = {}
    collision_map = {}  # displayName -> [internalName, ...]
    skipped_duplicates = []

    for item in response:
        if not isinstance(item, dict):
            print(f"WARNING: skipping non-dict item: {item!r}")
            continue

        display = item.get("displayName")
        internal = item.get("internalName")

        if display is None:
            print(f"WARNING: skipping item missing displayName (internalName={internal!r})")
            continue
        if internal is None:
            print(f"WARNING: skipping item missing internalName (displayName={display!r})")
            continue

        if display not in result:
            result[display] = item
            collision_map.setdefault(display, [internal])
        elif internal == display:
            existing = result[display]
            existing_internal = existing.get("internalName", display) if isinstance(existing, dict) else display
            if display not in collision_map:
                collision_map[display] = [existing_internal]
            collision_map[display].append(internal)
            if existing_internal in result and result[existing_internal] is not existing:
                skipped_duplicates.append((display, existing_internal))
            else:
                result[existing_internal] = existing
            result[display] = item
        else:
            # Collision on displayName — fall back to internalName as key.
            if display not in collision_map:
                # Record the first entry's internalName retroactively.
                collision_map[display] = [result[display].get("internalName", display)]
            collision_map[display].append(internal)

            if internal in result:
                skipped_duplicates.append((display, internal))
                continue
            result[internal] = item

    collisions = [
        (dn, names)
        for dn, names in collision_map.items()
        if len(names) > 1
    ]

    summary = {
        "collisions": collisions,
        "skipped_duplicates": skipped_duplicates,
        "total": len(result),
    }
    return result, summary


if __name__ == "__main__":
    import requests
    import json

    url = "https://beta-api.wynncraft.com/v3/item/database?fullResult"
    resp = requests.get(url, timeout=30).json()
    result, summary = items_response_to_dict(resp)

    ascended = [
        "Masterwork Fatal", "Masterwork Nirvana", "Masterwork Apocalypse",
        "Masterwork Aftershock", "Masterwork Az", "Masterwork Archangel", "Masterwork Pure"
    ]
    originals = ["Fatal", "Nirvana", "Apocalypse", "Aftershock", "Az", "Archangel", "Pure"]

    print(f"Total keys: {summary['total']}")
    print(f"Collisions: {len(summary['collisions'])}")

    all_pass = True
    for key in ascended:
        if key not in result:
            print(f"FAIL: {key!r} missing from result")
            all_pass = False
        else:
            print(f"OK: {key!r} present")
    for key in originals:
        if key not in result:
            print(f"FAIL: {key!r} missing from result")
            all_pass = False
        elif result[key].get("internalName") != key:
            print(f"FAIL: {key!r} should point to original (internalName={result[key].get('internalName')!r})")
            all_pass = False
        else:
            print(f"OK: {key!r} → original internalName confirmed")

    print("ALL PASS" if all_pass else "SOME CHECKS FAILED")
