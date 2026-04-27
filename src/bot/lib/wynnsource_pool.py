"""WynnSource pool integration with v2/beta/v1 failover.

This module ports the core WynnSource suite logic into nori-bot and keeps
payload shape compatible with legacy converters: data.loot[region][page].
"""

from __future__ import annotations

import base64
import importlib
import json
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
try:
    from google.protobuf.message import DecodeError
except Exception:  # pragma: no cover - runtime guard when protobuf is unavailable
    class DecodeError(Exception):
        pass


V1_POOL_ENDPOINTS = {
    "item": "/api/v1/pool/item/list",
    "aspect": "/api/v1/pool/raid/aspect/list",
    "tome": "/api/v1/pool/raid/tome/list",
}

V2_POOL_BASE_PATH = "/api/v2/pool/pools"

V2_POOL_CONFIG: dict[str, dict[str, Any]] = {
    "item": {
        "pool_type": "lr_item_pool",
        "regions": ("Sky", "Molten", "SE", "Canyon", "Corkus", "FrumaEast", "FrumaWest"),
    },
    "aspect": {
        "pool_type": "raid_aspect_pool",
        "regions": ("TNA", "TCC", "NOL", "NOTG", "TWP"),
    },
    "tome": {
        "pool_type": "raid_item_pool",
        "regions": ("TNA", "TCC", "NOL", "NOTG", "TWP"),
    },
}

RARITY_ORDER_ITEM = ("Mythic", "Fabled", "Legendary", "Rare", "Unique")
RARITY_LABELS_BY_NUMBER = {
    7: "Mythic",
    6: "Fabled",
    5: "Legendary",
    4: "Rare",
    3: "Unique",
}
RARITY_LABELS_BY_TOKEN = {
    "MYTHIC": "Mythic",
    "FABLED": "Fabled",
    "LEGENDARY": "Legendary",
    "RARE": "Rare",
    "UNIQUE": "Unique",
}
_POSSIBLE_B64_PATTERN = re.compile(r"^[A-Za-z0-9+/=]+$")


def _parse_bool_env(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


DEFAULT_PRIMARY_BASE_URL = os.getenv("WCS_POOL_PRIMARY_BASE_URL", "https://wcs.fyw.fyi").rstrip("/")
DEFAULT_BETA_BASE_URL = os.getenv("WCS_POOL_BETA_BASE_URL", "https://wcs-beta.fyw.fyi").rstrip("/")
DEFAULT_V1_BASE_URL = os.getenv("WCS_POOL_V1_BASE_URL", "https://wcs.fyw.fyi").rstrip("/")
# V1 fallback default is enabled; set WCS_POOL_ENABLE_V1_FALLBACK=false to disable.
DEFAULT_ENABLE_V1_FALLBACK = _parse_bool_env(os.getenv("WCS_POOL_ENABLE_V1_FALLBACK"), True)
DEFAULT_ALLOW_MISSING_REGIONS = _parse_bool_env(os.getenv("WCS_POOL_ALLOW_MISSING_REGIONS"), True)
DEFAULT_TIMEOUT_SECONDS = int(os.getenv("WCS_POOL_TIMEOUT", "30"))


@dataclass
class PoolFetchResult:
    payload: dict | None
    source: str | None
    attempts: list[str]


def clean_item_name(value: str) -> str:
    if not isinstance(value, str):
        return ""
    cleaned: list[str] = []
    for ch in value:
        cp = ord(ch)
        if not ch.isprintable():
            continue
        is_private_use = (
            (0xE000 <= cp <= 0xF8FF)
            or (0xF0000 <= cp <= 0xFFFFD)
            or (0x100000 <= cp <= 0x10FFFD)
        )
        if not is_private_use:
            cleaned.append(ch)
    cleaned_text = "".join(cleaned)
    cleaned_text = cleaned_text.replace("\xa0", " ").replace("\u00c0", " ")
    return " ".join(cleaned_text.split()).strip()


_WARD_PATTERN = re.compile(r"\bward\b", flags=re.IGNORECASE)


def is_ward_item(name: str) -> bool:
    if not name:
        return False
    return _WARD_PATTERN.search(name) is not None


_PROTO_RUNTIME: tuple[Any, dict[int, str]] | None = None


def _load_proto_runtime() -> tuple[Any, dict[int, str]]:
    global _PROTO_RUNTIME
    if _PROTO_RUNTIME is not None:
        return _PROTO_RUNTIME

    last_exc: Exception | None = None
    enums_pb2 = None
    WynnSourceItem = None

    for enums_mod, item_mod in (
        ("lib.wynnsource.common.enums_pb2", "lib.wynnsource.wynn_source_item_pb2"),
        ("wynnsource.common.enums_pb2", "wynnsource.wynn_source_item_pb2"),
    ):
        try:
            enums_pb2 = importlib.import_module(enums_mod)
            WynnSourceItem = getattr(importlib.import_module(item_mod), "WynnSourceItem")
            break
        except Exception as exc:
            last_exc = exc

    if enums_pb2 is None or WynnSourceItem is None:
        detail = f"{type(last_exc).__name__}: {last_exc}" if last_exc else "unknown import failure"
        raise RuntimeError(
            "V2 protobuf parsing requires generated WynnSource protobuf files and "
            "protobuf>=6.31.1. "
            f"Original error: {detail}"
        ) from last_exc

    rarity_labels = {
        enums_pb2.RARITY_MYTHIC: "Mythic",
        enums_pb2.RARITY_FABLED: "Fabled",
        enums_pb2.RARITY_LEGENDARY: "Legendary",
        enums_pb2.RARITY_RARE: "Rare",
        enums_pb2.RARITY_UNIQUE: "Unique",
    }
    _PROTO_RUNTIME = (WynnSourceItem, rarity_labels)
    return _PROTO_RUNTIME


def _decode_wynn_item(item_b64: str):
    if not item_b64:
        return None

    padding = "=" * (-len(item_b64) % 4)
    try:
        raw = base64.b64decode(item_b64 + padding)
    except ValueError:
        return None

    WynnSourceItem, _ = _load_proto_runtime()
    message = WynnSourceItem()
    try:
        message.ParseFromString(raw)
    except DecodeError:
        return None
    return message


def _load_shiny_display_mapping() -> dict[int, str]:
    mapping_path = Path(__file__).resolve().parent / "references" / "shiny.json"
    if not mapping_path.exists():
        return {}

    try:
        payload = json.loads(mapping_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    out: dict[int, str] = {}
    for entry in payload.get("data", []):
        if not isinstance(entry, dict):
            continue
        shiny_id = entry.get("id")
        display_name = entry.get("displayName")
        if isinstance(shiny_id, int) and isinstance(display_name, str):
            out[shiny_id] = display_name
    return out


SHINY_TRACKER_BY_ID = _load_shiny_display_mapping()


def _extract_shiny(item) -> dict[str, str | None] | None:
    if item.WhichOneof("data") != "gear":
        return None

    state = item.gear.WhichOneof("state")
    shiny = None
    if state == "identified" and item.gear.identified.HasField("shiny"):
        shiny = item.gear.identified.shiny
    elif state == "unidentified" and item.gear.unidentified.HasField("shiny"):
        shiny = item.gear.unidentified.shiny

    if shiny is None:
        return None

    name = clean_item_name(item.name)
    if not name:
        return None

    tracker_name = SHINY_TRACKER_BY_ID.get(shiny.id)
    if tracker_name is None and shiny.id != 0:
        tracker_name = f"unknown_{shiny.id}"

    return {"item": name, "tracker": tracker_name}


def _rarity_label_from_json_item(raw_item: dict[str, Any]) -> str | None:
    rarity = raw_item.get("rarity") or raw_item.get("tier")
    if isinstance(rarity, int):
        return RARITY_LABELS_BY_NUMBER.get(rarity)
    if isinstance(rarity, str):
        token = rarity.strip().upper()
        if token.startswith("RARITY_"):
            token = token[len("RARITY_") :]
        return RARITY_LABELS_BY_TOKEN.get(token)
    return None


def _extract_shiny_from_json_item(raw_item: dict[str, Any], name: str) -> dict[str, str | None] | None:
    gear = raw_item.get("gear")
    if not isinstance(gear, dict):
        return None

    for state in ("identified", "unidentified"):
        state_data = gear.get(state)
        if not isinstance(state_data, dict):
            continue
        shiny = state_data.get("shiny")
        if not isinstance(shiny, dict):
            continue
        shiny_id = shiny.get("id")
        if not isinstance(shiny_id, int):
            continue

        tracker_name = SHINY_TRACKER_BY_ID.get(shiny_id)
        if tracker_name is None and shiny_id != 0:
            tracker_name = f"unknown_{shiny_id}"
        return {"item": name, "tracker": tracker_name}

    return None


def _is_probable_encoded_item_blob(text: str) -> bool:
    """Heuristic guard to avoid treating undecodable b64 blobs as item names."""
    if not isinstance(text, str):
        return False
    value = text.strip()
    if len(value) < 24:
        return False
    if " " in value:
        return False
    return bool(_POSSIBLE_B64_PATTERN.fullmatch(value))


def _fetch_pool_raw_v1(
    pool: str,
    token: str | None,
    *,
    base_url: str,
    timeout: int,
) -> dict:
    endpoint = V1_POOL_ENDPOINTS.get(pool)
    if endpoint is None:
        raise ValueError(f"Unknown pool alias: {pool}")

    headers = {"Accept": "application/json"}
    if token:
        headers["X-API-KEY"] = token

    response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _fetch_pool_region_payloads_v2(
    pool: str,
    token: str | None,
    *,
    base_url: str,
    timeout: int,
    allow_missing_regions: bool,
    item_return_type: str = "b64",
) -> dict[str, dict]:
    config = V2_POOL_CONFIG.get(pool)
    if not config:
        raise ValueError(f"Unknown pool type: {pool}")

    headers = {"Accept": "application/json"}
    if token:
        headers["X-API-KEY"] = token

    payloads: dict[str, dict] = {}
    for region in config["regions"]:
        url = f"{base_url}{V2_POOL_BASE_PATH}/{config['pool_type']}/{region}"
        response = requests.get(
            url,
            headers=headers,
            params={"item_return_type": item_return_type},
            timeout=timeout,
        )

        if response.status_code in (404, 422) and allow_missing_regions:
            continue

        response.raise_for_status()
        payload = response.json().get("data", {})
        if isinstance(payload, dict):
            payloads[region] = payload

    return payloads


def _build_legacy_loot_payload(region_payloads: dict[str, dict]) -> dict:
    loot: dict[str, dict] = {}
    proto_rarity_labels: dict[int, str] | None = None

    for region, pool_data in region_payloads.items():
        region_out: dict[str, dict] = {}
        page_consensus = pool_data.get("page_consensus", [])
        if not isinstance(page_consensus, list):
            page_consensus = []

        sorted_pages = sorted(page_consensus, key=lambda page: page.get("page", 0) if isinstance(page, dict) else 0)

        for page in sorted_pages:
            if not isinstance(page, dict):
                continue

            page_key = str(page.get("page", len(region_out) + 1))
            rarity_buckets = {rarity: [] for rarity in RARITY_ORDER_ITEM}
            rarity_buckets["Misc"] = []
            shiny = None

            raw_items = page.get("items", [])
            if not isinstance(raw_items, list):
                raw_items = []

            for raw_item in raw_items:
                if isinstance(raw_item, str):
                    decoded = _decode_wynn_item(raw_item)
                    if decoded is None:
                        fallback_name = clean_item_name(raw_item)
                        if fallback_name and not _is_probable_encoded_item_blob(fallback_name):
                            rarity_buckets["Misc"].append(fallback_name)
                        continue

                    name = clean_item_name(decoded.name)
                    if not name:
                        continue

                    if is_ward_item(name):
                        rarity_buckets["Mythic"].append(name)
                    else:
                        if proto_rarity_labels is None:
                            _, proto_rarity_labels = _load_proto_runtime()
                        rarity_label = proto_rarity_labels.get(decoded.rarity)
                        if rarity_label:
                            rarity_buckets[rarity_label].append(name)
                        else:
                            rarity_buckets["Misc"].append(name)

                    if shiny is None:
                        shiny_data = _extract_shiny(decoded)
                        if shiny_data:
                            shiny = shiny_data
                    continue

                if not isinstance(raw_item, dict):
                    continue

                name_value = raw_item.get("name")
                if not isinstance(name_value, str):
                    continue
                name = clean_item_name(name_value)
                if not name:
                    continue

                if is_ward_item(name):
                    rarity_buckets["Mythic"].append(name)
                else:
                    rarity_label = _rarity_label_from_json_item(raw_item)
                    if rarity_label:
                        rarity_buckets[rarity_label].append(name)
                    else:
                        rarity_buckets["Misc"].append(name)

                if shiny is None:
                    shiny_data = _extract_shiny_from_json_item(raw_item, name)
                    if shiny_data:
                        shiny = shiny_data

            page_out = {"items": {rarity: names for rarity, names in rarity_buckets.items() if names}}
            if shiny:
                page_out["shiny"] = shiny
            region_out[page_key] = page_out

        loot[region] = region_out

    return {"data": {"loot": loot}}


def _fetch_pool_as_legacy_v2(
    pool: str,
    token: str | None,
    *,
    base_url: str,
    timeout: int,
    allow_missing_regions: bool,
) -> dict:
    try:
        payloads = _fetch_pool_region_payloads_v2(
            pool,
            token,
            base_url=base_url,
            timeout=timeout,
            allow_missing_regions=allow_missing_regions,
            item_return_type="b64",
        )
        return _build_legacy_loot_payload(payloads)
    except RuntimeError as exc:
        text = str(exc).lower()
        if "protobuf" not in text and "versionerror" not in text and "wynnsource" not in text:
            raise

    payloads = _fetch_pool_region_payloads_v2(
        pool,
        token,
        base_url=base_url,
        timeout=timeout,
        allow_missing_regions=allow_missing_regions,
        item_return_type="json",
    )
    return _build_legacy_loot_payload(payloads)


def _summarize_payload(payload: dict) -> dict[str, int]:
    loot = payload.get("data", {}).get("loot", {})
    if not isinstance(loot, dict):
        return {"regions": 0, "pages": 0, "rarity_bucket_items": 0}

    region_count = len(loot)
    page_count = 0
    item_count = 0

    for region_data in loot.values():
        if not isinstance(region_data, dict):
            continue
        page_count += len(region_data)
        for page in region_data.values():
            if not isinstance(page, dict):
                continue
            items = page.get("items", {})
            if not isinstance(items, dict):
                continue
            for names in items.values():
                if isinstance(names, list):
                    item_count += len(names)

    return {
        "regions": region_count,
        "pages": page_count,
        "rarity_bucket_items": item_count,
    }


def _is_payload_usable(payload: dict) -> tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "payload is not a dictionary"

    summary = _summarize_payload(payload)
    if summary["regions"] <= 0:
        return False, "no regions in payload"
    if summary["pages"] <= 0:
        return False, "no pages in payload"
    if summary["rarity_bucket_items"] <= 0:
        return False, "no rarity bucket items in payload"

    return True, "ok"


def _fetch_from_source(
    source_key: str,
    pool: str,
    token: str | None,
    *,
    primary_base_url: str,
    beta_base_url: str,
    v1_base_url: str,
    timeout: int,
    allow_missing_regions: bool,
) -> dict:
    if source_key == "v2_primary":
        return _fetch_pool_as_legacy_v2(
            pool,
            token,
            base_url=primary_base_url,
            timeout=timeout,
            allow_missing_regions=allow_missing_regions,
        )
    if source_key == "v2_beta":
        return _fetch_pool_as_legacy_v2(
            pool,
            token,
            base_url=beta_base_url,
            timeout=timeout,
            allow_missing_regions=allow_missing_regions,
        )
    if source_key == "v1":
        return _fetch_pool_raw_v1(pool, token, base_url=v1_base_url, timeout=timeout)

    raise ValueError(f"Unsupported source key: {source_key}")


def fetch_pool_legacy_with_failover(
    pool: str,
    token: str | None,
    *,
    primary_base_url: str = DEFAULT_PRIMARY_BASE_URL,
    beta_base_url: str = DEFAULT_BETA_BASE_URL,
    v1_base_url: str = DEFAULT_V1_BASE_URL,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    allow_missing_regions: bool = DEFAULT_ALLOW_MISSING_REGIONS,
    enable_v1_fallback: bool = DEFAULT_ENABLE_V1_FALLBACK,
) -> PoolFetchResult:
    ordered_sources = ["v2_primary", "v2_beta"]
    if enable_v1_fallback:
        ordered_sources.append("v1")

    attempts: list[str] = []

    for source_key in ordered_sources:
        try:
            payload = _fetch_from_source(
                source_key,
                pool,
                token,
                primary_base_url=primary_base_url,
                beta_base_url=beta_base_url,
                v1_base_url=v1_base_url,
                timeout=timeout,
                allow_missing_regions=allow_missing_regions,
            )
        except Exception as exc:
            attempts.append(f"{source_key}: request error ({type(exc).__name__}: {exc})")
            continue

        usable, reason = _is_payload_usable(payload)
        if usable:
            summary = _summarize_payload(payload)
            attempts.append(
                f"{source_key}: usable payload (regions={summary['regions']}, pages={summary['pages']}, items={summary['rarity_bucket_items']})"
            )
            return PoolFetchResult(payload=payload, source=source_key, attempts=attempts)

        attempts.append(f"{source_key}: unusable payload ({reason})")

    return PoolFetchResult(payload=None, source=None, attempts=attempts)


def format_attempt_log(attempts: list[str]) -> str:
    if not attempts:
        return "no attempts recorded"
    return " | ".join(attempts)
