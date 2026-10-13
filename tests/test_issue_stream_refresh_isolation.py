"""Cold import of the issue-stream audit must see redirected refresh sidecars (#10519)."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

from tests.helpers.restore_import_state import restore_import_state

_AUDIT = "scripts.orchestration.issue_stream_audit"


def test_cold_import_redirects_refresh_sidecars(_write_ownership_base: Path) -> None:
    """A first import inside the test body must not bind the live primary sidecars.

    The autouse fixture used to return while this module was absent, so the
    import below received the primary checkout's state and lock paths.
    """
    with restore_import_state(_AUDIT):
        sys.modules.pop(_AUDIT, None)
        parent = sys.modules.get("scripts.orchestration")
        if isinstance(parent, types.ModuleType):
            parent.__dict__.pop("issue_stream_audit", None)
        assert _AUDIT not in sys.modules

        audit = importlib.import_module(_AUDIT)

        state = audit.REFRESH_STATE_PATH
        lock = audit.REFRESH_LOCK_PATH
        live_state, live_lock = audit.refresh_sidecar_paths(audit.ROOT)
        assert state != live_state
        assert lock != live_lock
        assert state.parent.parent == _write_ownership_base
        assert lock.parent == state.parent
        assert state.parent.name.startswith("issue-audit-refresh-")
        assert state.name == "issue_stream_audit_refresh.json"
        assert lock.name == "issue_stream_audit_refresh.lock"
