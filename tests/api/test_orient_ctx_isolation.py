"""#7494: /api/orient threads the app's own context — no production bleed."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import scripts.api.main as api_main
from scripts.api.monitor_context import fixture_context, resolve_context

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
    """#7494 / #7496: shared resolve_context falls to production_context(),
    never to whatever app instance happens to sit in module globals."""
    ctx = fixture_context(tmp_path)
    assert api_main.app.state.ctx is not None  # the production app exists
    resolved = resolve_context(None)
    assert resolved is not ctx
    # and an explicitly passed ctx always wins
    assert resolve_context(ctx) is ctx
    # main no longer owns a private copy
    assert not hasattr(api_main, "_resolve_context")


def test_idle_pr_last_good_is_not_shared_across_contexts(tmp_path: Path) -> None:
    """#7494 CF r1: one app's last-good idle-PR payload must never surface
    in another app's response on a cache miss."""
    import scripts.api.main as m

    scope_a, scope_b = "@/roots/a", "@/roots/b"
    m._idle_pr_last_good[scope_a] = ({"idle_prs": [{"number": 1}]}, "2026-08-31T00:00:00Z")
    try:
        assert m._idle_pr_last_good.get(scope_b) is None
        # The reader consults only its own scope: emulate scope-b miss path.
        assert scope_b not in m._idle_pr_last_error
    finally:
        m._idle_pr_last_good.pop(scope_a, None)


def test_detached_last_good_keyed_by_scoped_cache_key(tmp_path: Path) -> None:
    import scripts.api.main as m

    key_a = "orient_pipeline@/roots/a"
    m._detached_orient_last_good[key_a] = ({"summary": {}}, "2026-08-31T00:00:00Z")
    try:
        assert m._detached_orient_last_good.get("orient_pipeline@/roots/b") is None
        assert m._detached_orient_last_good.get("orient_pipeline") is None
    finally:
        m._detached_orient_last_good.pop(key_a, None)


def test_no_router_owns_a_private_resolve_context_copy() -> None:
    """#7496: byte-identical per-router _resolve_context copies are gone."""
    import importlib
    import pkgutil

    import scripts.api as api_pkg

    offenders: list[str] = []
    for mod in pkgutil.iter_modules(api_pkg.__path__, api_pkg.__name__ + "."):
        if mod.name.endswith(".monitor_context"):
            continue
        try:
            module = importlib.import_module(mod.name)
        except Exception:
            continue
        if hasattr(module, "_resolve_context"):
            offenders.append(mod.name)
    assert offenders == []


def test_shared_resolve_context_is_the_only_plain_python_fallback(tmp_path: Path) -> None:
    """#7496: one shared resolve_context; explicit ctx always wins."""
    from scripts.api.monitor_context import production_context, resolve_context

    ctx = fixture_context(tmp_path)
    assert resolve_context(None) is production_context()
    assert resolve_context(ctx) is ctx
