"""CEFR bands admitted on Word-of-the-Day daily-pool rows.

Shared by the pool generator and the static-asset gate so the validator cannot
drift behind true-CEFR emission (#6728). Keep this module dependency-free — both
callers also run as ``python scripts/audit/<name>.py`` scripts.
"""

from __future__ import annotations

# Every CEFR level the WotD level selector exposes. The pool emits a row's true
# level (any of these) and reserves per-level slots, so C1/C2/B2 tabs point at
# real level-matched cards instead of an A1/A2/B1-only pool.
CEFR_LEVEL_ORDER = ("A1", "A2", "B1", "B2", "C1", "C2")
CEFR_LEVELS = frozenset(CEFR_LEVEL_ORDER)
