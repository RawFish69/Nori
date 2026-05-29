"""Thin sync HTTP client for the official Wynncraft /v3/map/* endpoints.

The endpoints in this module are unauthenticated (guest, 50 RPM on the MAP
rate-limit bucket). No ``Authorization`` header is sent. All calls are
synchronous to match the style of :mod:`lib.wynnsource_pool`.

Public surface:

- :func:`fetch_loot_pools` — calls ``/map/loot-pools``
- :func:`fetch_world_events` — calls ``/map/world-events``
- :func:`fetch_map_raids` — calls ``/map/raids`` (future use; same shape)
- :func:`fetch_map_camps` — calls ``/map/camps`` (future use; same shape)

Each returns a dict:

- On success: ``{"ok": True, "data": <list>, "source": "official"}``
- On failure: ``{"ok": False, "error": "<code>", "detail": "<message>"}``

The shared helper :func:`_get_json_with_retry` implements the loose §3.2
retry policy: on HTTP 429, sleep ``Retry-After`` (capped at
``OFFICIAL_API_RETRY_AFTER_CAP``) plus 1s of jitter, otherwise sleep
``OFFICIAL_API_RETRY_SLEEP``; retry exactly once. Any other failure mode
(timeout, 5xx, 4xx other than 429, malformed JSON, empty array) is reported
to the caller without retrying — those failures fall through to the
WynnSource fallback path one layer up.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from lib.config import (
    OFFICIAL_API_BASE_URL,
    OFFICIAL_API_RETRY_AFTER_CAP,
    OFFICIAL_API_RETRY_SLEEP,
    OFFICIAL_API_TIMEOUT,
)

BETA_API_BASE_URL = "https://beta-api.wynncraft.com/v3"

# Small constant jitter added to a honored Retry-After. Keeps us off the
# bucket boundary on the retry. Matches spec §3.2 "+ 1s of jitter".
_RETRY_AFTER_JITTER = 1


def _parse_retry_after(value: Any) -> int | None:
    """Parse ``Retry-After`` header into an int seconds value, or ``None``."""
    if value is None:
        return None
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    if parsed < 0:
        return None
    return parsed


def _compute_retry_sleep(retry_after: Any) -> float:
    """Return how long to sleep before the single 429 retry.

    Honors ``Retry-After`` (plus 1s jitter) when present and ``<=`` the cap;
    otherwise falls back to ``OFFICIAL_API_RETRY_SLEEP``.
    """
    parsed = _parse_retry_after(retry_after)
    if parsed is None or parsed > OFFICIAL_API_RETRY_AFTER_CAP:
        return OFFICIAL_API_RETRY_SLEEP
    return parsed + _RETRY_AFTER_JITTER


def _classify_response(
    response: requests.Response,
    *,
    expect_nonempty_array: bool,
) -> tuple[bool, dict]:
    """Inspect a successful network call's response.

    Returns ``(ok, result)`` where ``result`` is either the success payload
    (``{"ok": True, "data": ..., "source": "official"}``) or a failure dict
    (``{"ok": False, "error": "...", "detail": "..."}``).
    """
    status = response.status_code

    if status == 200:
        try:
            payload = response.json()
        except ValueError as exc:
            return False, {
                "ok": False,
                "error": "malformed_json",
                "detail": f"response body was not valid JSON: {exc}",
            }

        if expect_nonempty_array:
            if not isinstance(payload, list):
                return False, {
                    "ok": False,
                    "error": "malformed_json",
                    "detail": f"expected JSON array, got {type(payload).__name__}",
                }
            if len(payload) == 0:
                return False, {
                    "ok": False,
                    "error": "empty_payload",
                    "detail": "official endpoint returned an empty array",
                }

        return True, {"ok": True, "data": payload, "source": "official"}

    if status == 429:
        return False, {
            "ok": False,
            "error": "rate_limited",
            "detail": "HTTP 429 from official endpoint",
        }

    return False, {
        "ok": False,
        "error": f"http_{status}",
        "detail": f"HTTP {status} from official endpoint",
    }


def _get_json_with_retry(
    path: str,
    *,
    expect_nonempty_array: bool = True,
) -> dict:
    """Perform a single GET against ``{OFFICIAL_API_BASE_URL}{path}``.

    Implements the loose 429 retry policy from spec §3.2: at most one retry,
    only on HTTP 429. Any other failure (timeout, 5xx, malformed JSON, empty
    array) is returned to the caller immediately so the orchestration layer
    can fall back to WynnSource for this cycle.
    """
    url = f"{OFFICIAL_API_BASE_URL}{path}"
    headers = {"Accept": "application/json"}

    # ----- attempt 1 -----
    try:
        response = requests.get(url, headers=headers, timeout=OFFICIAL_API_TIMEOUT)
    except requests.exceptions.Timeout as exc:
        return {"ok": False, "error": "timeout", "detail": f"request timed out: {exc}"}
    except requests.exceptions.RequestException as exc:
        return {
            "ok": False,
            "error": "network_error",
            "detail": f"{type(exc).__name__}: {exc}",
        }

    ok, result = _classify_response(response, expect_nonempty_array=expect_nonempty_array)
    if ok or result.get("error") != "rate_limited":
        # Success, or a non-429 failure -> caller decides what to do, no retry.
        return result

    # ----- 429: sleep, then retry exactly once -----
    retry_after_header = response.headers.get("Retry-After")
    sleep_for = _compute_retry_sleep(retry_after_header)
    # Generic prefix so both the item-lootpool and raid-pool refresh paths
    # (which share this client) get a consistent retry log line. The
    # orchestration layer's own log uses the [Lootpool refresh] / [Raid
    # pool refresh] prefix from §8 of V3_7_2_LOOTPOOL_MIGRATION.md.
    print(
        f"[Wynn map API] official 429, Retry-After={retry_after_header}s, "
        f"retrying once after sleep..."
    )
    time.sleep(sleep_for)

    try:
        response = requests.get(url, headers=headers, timeout=OFFICIAL_API_TIMEOUT)
    except requests.exceptions.Timeout as exc:
        return {"ok": False, "error": "timeout", "detail": f"request timed out on retry: {exc}"}
    except requests.exceptions.RequestException as exc:
        return {
            "ok": False,
            "error": "network_error",
            "detail": f"retry failed: {type(exc).__name__}: {exc}",
        }

    _, result = _classify_response(response, expect_nonempty_array=expect_nonempty_array)
    return result


# ---------------------------------------------------------------------------
# Public fetchers
# ---------------------------------------------------------------------------


def fetch_loot_pools() -> dict:
    """Fetch ``/map/loot-pools``. Returns a result dict (see module docstring)."""
    return _get_json_with_retry("/map/loot-pools")


def _any_scheduled(data: Any) -> bool:
    """Return True if at least one event has a non-null schedule."""
    return isinstance(data, list) and any(
        isinstance(e, dict) and e.get("schedule") is not None for e in data
    )


def fetch_world_events() -> dict:
    """Fetch ``/map/world-events`` with beta fallback.

    If prod returns events but all schedules are null (outside the 15-min
    visibility window), try the beta API once. If beta has at least one
    scheduled event, return that with ``source="beta"``. Otherwise return
    the prod result unchanged.
    """
    result = _get_json_with_retry("/map/world-events")
    if not result.get("ok"):
        return result

    data = result.get("data") or []
    if data and not _any_scheduled(data):
        beta_url = f"{BETA_API_BASE_URL}/map/world-events"
        try:
            resp = requests.get(
                beta_url,
                headers={"Accept": "application/json"},
                timeout=OFFICIAL_API_TIMEOUT,
            )
            if resp.status_code == 200:
                beta_data = resp.json()
                if isinstance(beta_data, list) and _any_scheduled(beta_data):
                    print("[Wynn map API] prod events all unscheduled; using beta API for world-events")
                    return {"ok": True, "data": beta_data, "source": "beta"}
        except Exception as exc:
            print(f"[Wynn map API] beta world-events fallback failed: {type(exc).__name__}: {exc}")

    return result


def fetch_map_raids() -> dict:
    """Fetch ``/map/raids``. Returns a result dict. (Future use.)"""
    return _get_json_with_retry("/map/raids")


def fetch_map_camps() -> dict:
    """Fetch ``/map/camps``. Returns a result dict. (Future use.)"""
    return _get_json_with_retry("/map/camps")
