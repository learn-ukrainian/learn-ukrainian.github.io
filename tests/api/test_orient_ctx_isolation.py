"""#7494: /api/orient threads the app's own context — no production bleed."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import scripts.api.main as api_main
from scripts.api.monitor_context import fixture_context

pytestmark = pytest.mark.repo_invariant


def test_fixture_app_orient_git_is_not_production(tmp_path: Path) -> None:
    """A create_app() instance must report ITS root's git state (here: a
    non-repo tmp dir → error/degraded), never the production checkout's."""
    app = api_main.create_app(fixture_context(tmp_path))
    data = TestClient(app).get("/api/orient?sections=git&fresh=true").json()
    git = data.get("git") or {}
    production_head = None
    try:
        import subprocess

        production_head = subprocess.run(
            ["git", "rev-parse", "--short=9", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
    except Exception:
        pass
    if production_head:
        assert git.get("head") != production_head


def test_orient_cache_is_scoped_per_context(tmp_path: Path) -> None:
    """Two apps with different roots must not share orient cache entries."""
    a = api_main.create_app(fixture_context(tmp_path / "a"))
    b = api_main.create_app(fixture_context(tmp_path / "b"))
    da = TestClient(a).get("/api/orient?sections=health&fresh=true").json()
    db = TestClient(b).get("/api/orient?sections=health").json()
    # b's first call must be a cache MISS (a's entry is scoped to a's root).
    assert db["meta"]["health"]["cache"] == "miss"
    assert da["meta"]["health"]["cache"] == "miss"


def test_resolve_context_never_reads_the_module_global_app(tmp_path: Path) -> None:
    """#7494 / 4.1: plain-Python resolution falls to production_context(),
    never to whatever app instance happens to sit in module globals."""
    ctx = fixture_context(tmp_path)
    assert api_main.app.state.ctx is not None  # the production app exists
    resolved = api_main._resolve_context(None)
    assert resolved is not ctx
    # and an explicitly passed ctx always wins
    assert api_main._resolve_context(ctx) is ctx
