"""Read the dispatcher state for the dashboard pipeline view."""

from __future__ import annotations

import json
from typing import Any, cast

from lu_machinery.api.monitor_context import MonitorContext, resolve_context


def read_dispatcher_state(ctx: MonitorContext | None = None) -> dict:
    """Read the batch dispatcher state from disk."""
    ds_file = resolve_context(ctx).roots.batch_state_dir / "dispatcher_state.json"
    if not ds_file.exists():
        return {}
    try:
        with open(ds_file) as f:
            return cast("dict[Any, Any]", json.load(f))
    except Exception:
        return {}
