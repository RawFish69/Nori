"""Shared manager registry for the modular bot runtime.

Avoids attaching dynamic attributes to BotApp instances, which may be
unsupported in some Lightbulb/Hikari versions.
"""

from __future__ import annotations

from typing import Any

_MANAGERS: dict[str, Any] = {}


def set_managers(managers: dict[str, Any]) -> None:
    global _MANAGERS
    _MANAGERS = managers


def get_managers() -> dict[str, Any]:
    return _MANAGERS

