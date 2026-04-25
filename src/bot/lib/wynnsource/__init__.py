"""WynnSource protobuf package hosted under ``lib``.

Generated protobuf modules use absolute imports like ``wynnsource.common``.
Expose this package under the top-level ``wynnsource`` alias so those imports
continue to work without needing a root-level ``wynnsource/`` directory.
"""

from __future__ import annotations

import sys

# Make absolute imports inside generated pb2 modules resolve to this package.
sys.modules.setdefault("wynnsource", sys.modules[__name__])
