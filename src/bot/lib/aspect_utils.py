"""Aspect database update helpers."""

import json

import requests

import lib.config as config

ASPECT_CHARACTERS = ["warrior", "mage", "archer", "assassin", "shaman"]


def aspects_response_to_dict(char_data):
    """Convert v3.7 aspects array responses to a display-name keyed dict."""
    if isinstance(char_data, dict):
        return char_data
    if not isinstance(char_data, list):
        print(f"[Aspects update] unexpected type {type(char_data).__name__!r}")
        return {}

    result = {}
    for aspect in char_data:
        if not isinstance(aspect, dict):
            continue
        name = aspect.get("name")
        if name is None:
            continue
        if name not in result:
            result[name] = aspect
        else:
            print(f"[Aspects update] duplicate aspect name {name!r}, keeping first")
    return result


def update_aspects(path) -> int:
    """Fetch the static aspect database from Wynncraft API and write it to disk."""
    output = {}
    icons = {}
    try:
        for character in ASPECT_CHARACTERS:
            url = f"https://api.wynncraft.com/v3/aspects/{character}"
            response = requests.get(url, headers=config.WYNN_AUTH_HEADER, timeout=15)
            if response.status_code != 200:
                print(f"[Aspects update] HTTP {response.status_code} for {character}, skipping")
                continue
            content_type = response.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                print(f"[Aspects update] non-JSON response for {character} ({content_type!r}), skipping")
                continue

            char_data = aspects_response_to_dict(response.json())
            output[character] = char_data
            for aspect_name, info in char_data.items():
                if info.get("rarity") == "mythic":
                    icons[aspect_name] = f"aspect_{info.get('requiredClass')}.gif"
                else:
                    icons[aspect_name] = f"static_{info.get('requiredClass')}.png"

        if not output:
            print("[Aspects update] all character fetches failed, skipping write")
            return 0

        payload = {"data": output, "icons": icons}
        with open(path, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=3)
        config.aspect_data = payload
        total = sum(len(value) for value in output.values())
        print(f"[Aspects update] {total} aspects written to {path}")
        return total
    except Exception as error:
        print(f"[Aspects update] unexpected error: {type(error).__name__}: {error}")
        return 0
