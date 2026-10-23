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
