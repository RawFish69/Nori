"""
Compatibility shim for Wynncraft item API v3.3 → v3.7 migration.

In v3.7, GET /v3/item/database?fullResult returns a list of item objects.
In v3.3, it returned a dict keyed by displayName.

This module provides items_response_to_dict() which normalises both formats
into a dict, using internalName as a fallback key when displayName collides
(needed for the 7 "Ascended" mythics that share a displayName with their
original counterpart, e.g. "Fatal" / "Masterwork Fatal").
"""


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
        else:
            # Collision on displayName — fall back to internalName as key.
            if display not in collision_map:
                # Record the first entry's internalName retroactively.
                collision_map[display] = [result[display].get("internalName", display)]
            collision_map[display].append(internal)

            if internal in result:
                print(
                    f"WARNING: skipping duplicate — internalName {internal!r} already used as key"
                )
                continue
            result[internal] = item

    collisions = [
        (dn, names)
        for dn, names in collision_map.items()
        if len(names) > 1
    ]

    summary = {
        "collisions": collisions,
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
