"""Shared loader for ``scripts/config/agent_fallback_substitutions.yaml``.

The ``dispatch_fallbacks`` table is the single source of truth for hard seat
substitutions. ``delegate.py --check-budget`` (pre-dispatch budget shed) and
the ACP ask path (#8499: post-failure quota substitution) both read it through
this loader so the mapping is never duplicated: a deleted row means refuse,
not a silently resurrected route.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def load_dispatch_fallbacks(config_path: Path) -> dict[str, str]:
    """Return the ``dispatch_fallbacks`` seat-to-seat map, or {} when unreadable."""
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    subs = data.get("dispatch_fallbacks") if isinstance(data, dict) else {}
    if isinstance(subs, dict):
        return {str(k).lower(): str(v).lower() for k, v in subs.items() if v}
    return {}
