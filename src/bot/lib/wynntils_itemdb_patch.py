"""
Compatibility patch for wynntilsresolver 1.5.0 with the nori local item database.

Three issues fixed:

1. ITEMDB_PATH in .env may carry a trailing \\r (CRLF line endings). DataStore stores
   the raw path, so os.path.getmtime / open both fail with FileNotFoundError. We strip
   the path after import.

2. The local itemdb (items.json) is dict-format {name: item}, but 1.5.0's DataStore._get
   assumes a list and does {item["internalName"]: item for item in loaded}, which iterates
   dict keys as strings and raises TypeError: string indices must be integers. We replicate
   the caching logic and handle both formats.

3. Some identification values are plain ints or strings instead of {min, max, raw} dicts.
   Identification.from_simple does meta["raw"] and raises TypeError on scalars. We coerce
   them after loading.
"""

from __future__ import annotations

import functools
import json as _json
import os as _os
import pathlib
import time as _time
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Identification value normalisation (issue 3)
# ---------------------------------------------------------------------------

def _scalar_to_int(v: Any) -> Optional[int]:
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(round(v))
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            return int(s)
        except ValueError:
            try:
                return int(float(s))
            except ValueError:
                return None
    return None


def _coerce_identifications(identifications: Any) -> None:
    if not isinstance(identifications, dict):
        return
    for key, val in list(identifications.items()):
        if isinstance(val, dict) and "raw" in val:
            continue
        if isinstance(val, int):
            continue
        n = _scalar_to_int(val)
        if n is None:
            continue
        identifications[key] = {"min": n, "max": n, "raw": n}


def _normalize_itemdb(itemdb: Dict[str, Any]) -> None:
    for item in itemdb.values():
        if isinstance(item, dict):
            _coerce_identifications(item.get("identifications"))


# ---------------------------------------------------------------------------
# Main patch
# ---------------------------------------------------------------------------

def apply_wynntils_itemdb_identification_coercion() -> None:
    from wynntilsresolver.datastore import data_store

    if getattr(data_store._get, "_nori_patched", False):
        return

    # Issue 1: strip trailing \r / whitespace from the itemdb path
    raw = str(data_store._paths["itemdb"])
    clean = pathlib.Path(raw.strip())
    if clean != data_store._paths["itemdb"]:
        data_store.itemdb_path = clean
        data_store._paths["itemdb"] = clean

    _orig_get = data_store._get

    @functools.wraps(_orig_get)
    def _wrapped(name: str):
        if name != "itemdb":
            return _orig_get(name)

        # Replicate DataStore._get caching logic, but handle dict-format itemdb.
        # The initial sentinel in _cache is an object(), not a dict — use isinstance
        # to distinguish a real loaded itemdb from the sentinel.
        cache = data_store._cache["itemdb"]
        cache_loaded = isinstance(cache, dict)
        now = _time.monotonic()

        if cache_loaded and now - data_store._last_check["itemdb"] < data_store.check_interval:
            return cache

        data_store._last_check["itemdb"] = now
        path = data_store._paths["itemdb"]
        mtime = _os.path.getmtime(path)

        if cache_loaded and mtime == data_store._mtime["itemdb"]:
            return cache

        with open(path, encoding="utf-8") as f:
            loaded = _json.load(f)

        # Issue 2: accept both list-format (Wynncraft v3 API) and dict-format (local db)
        if isinstance(loaded, list):
            loaded = {item["internalName"]: item for item in loaded}
        # else: already a dict keyed by item name — use as-is

        # Issue 3: coerce scalar identification values to {min, max, raw}
        _normalize_itemdb(loaded)

        data_store._cache["itemdb"] = loaded
        data_store._mtime["itemdb"] = mtime
        return loaded

    _wrapped._nori_patched = True  # type: ignore[attr-defined]
    data_store._get = _wrapped  # type: ignore[method-assign]


__all__ = ["apply_wynntils_itemdb_identification_coercion"]
