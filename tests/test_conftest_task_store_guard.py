"""The suite must not write the live dispatch task store (#8654)."""

from __future__ import annotations

import ast
import os
import sqlite3
from pathlib import Path

import pytest

from tests.conftest import (
    _DERIVED_LIVE_TASK_PATHS,
    _REAL_TASKS_DIR,
)


def test_write_to_real_task_store_fails() -> None:
    """A direct write under the live ``batch_state/tasks`` fails before creating a file."""
    target = _REAL_TASKS_DIR / "t-guard-should-not-exist.json"
    assert not target.exists()
    with pytest.raises(pytest.fail.Exception, match="real dispatch task store"):
        target.write_text("{}\n", encoding="utf-8")
    assert not target.exists()


def test_bytes_sqlite_path_under_real_task_store_is_refused() -> None:
    """A raw bytes path, and a path-like that returns bytes, is refused."""
    target = _REAL_TASKS_DIR / "t-guard-bytes.sqlite3"
    assert not target.exists()

    class _BytesPath:
        def __fspath__(self) -> bytes:
            return os.fsencode(target)

    for database in (os.fsencode(target), _BytesPath()):
        with pytest.raises(pytest.fail.Exception, match="real dispatch task store"):
            sqlite3.connect(database)
    assert not target.exists()


def test_write_to_real_preflight_fast_fail_is_refused() -> None:
    """A write to the live ``batch_state/preflight_fast_fail.jsonl`` is refused."""
    target = _REAL_TASKS_DIR.parent / "preflight_fast_fail.jsonl"
    assert target.resolve() in _DERIVED_LIVE_TASK_PATHS
    before = target.stat().st_mtime_ns if target.exists() else None
    with pytest.raises(pytest.fail.Exception, match="real dispatch task store"):
        with target.open("a", encoding="utf-8") as handle:
            handle.write("refused\n")
    after = target.stat().st_mtime_ns if target.exists() else None
    assert before == after


def test_isolate_dispatch_task_store_is_not_the_live_dir(
    _isolate_dispatch_task_store: Path,
) -> None:
    """The autouse redirect is ``<session base>/<n>/tasks``, so its parent is also per-test."""
    import scripts.api.config as api_config
    import scripts.api.delegate_router as delegate_router
    import scripts.api.main as api_main
    import scripts.delegate as delegate_mod
    from scripts.common.task_store_paths import tasks_dir

    assert _isolate_dispatch_task_store != _REAL_TASKS_DIR
    assert _isolate_dispatch_task_store.name == "tasks"
    assert _isolate_dispatch_task_store == tasks_dir()
    assert _isolate_dispatch_task_store.parent != _REAL_TASKS_DIR.parent
    assert _isolate_dispatch_task_store.parent == api_config.BATCH_STATE_DIR
    assert _isolate_dispatch_task_store.parent == api_main.app.state.ctx.roots.batch_state_dir
    assert delegate_router._tasks_dir(api_main.app.state.ctx) == _isolate_dispatch_task_store
    assert delegate_router._tasks_dir(None) == _isolate_dispatch_task_store
    assert _REAL_TASKS_DIR not in delegate_mod._state_path("t-isolated").parents
    fast_fail = tasks_dir().parent / "preflight_fast_fail.jsonl"
    assert _REAL_TASKS_DIR.parent not in fast_fail.resolve().parents


def test_test_level_override_wins_over_autouse(
    _isolate_dispatch_task_store: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A test-level ``LU_TASKS_DIR`` override wins."""
    from scripts.common.task_store_paths import tasks_dir

    override = _isolate_dispatch_task_store.parent / "override-tasks"
    override.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(override))
    assert override == tasks_dir()
    assert _isolate_dispatch_task_store != tasks_dir()
    assert tasks_dir() != _REAL_TASKS_DIR


def _module_level_tasks_dir_constants(source: str) -> list[str]:
    """Names assigned at module level to a path ending in ``batch_state/tasks``."""
    tree = ast.parse(source)
    found: list[str] = []
    for node in tree.body:
        value = None
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            value = node.value
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            value = node.value
            targets = [node.target]
        else:
            continue
        if _div_string_tail(value) != ("batch_state", "tasks"):
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                found.append(target.id)
            elif isinstance(target, ast.Tuple):
                found.extend(element.id for element in target.elts if isinstance(element, ast.Name))
    return found


def _div_string_tail(node: ast.expr) -> tuple[str, ...]:
    parts: list[str] = []
    current: ast.expr = node
    while isinstance(current, ast.BinOp) and isinstance(current.op, ast.Div):
        right = current.right
        if not isinstance(right, ast.Constant) or not isinstance(right.value, str):
            break
        parts.append(right.value)
        current = current.left
    parts.reverse()
    return tuple(parts)


@pytest.mark.repo_wide
def test_task_store_consumers_use_call_time_resolver() -> None:
    """No module may bind the shared task-store path at import time."""
    repo = Path(__file__).resolve().parents[1]
    found: set[tuple[str, str]] = set()
    for path in sorted((repo / "scripts").rglob("*.py")):
        relative = path.relative_to(repo).with_suffix("")
        module_name = ".".join(relative.parts[:-1]) if relative.name == "__init__" else ".".join(relative.parts)
        source = path.read_text(encoding="utf-8")
        for name in _module_level_tasks_dir_constants(source):
            found.add((module_name, name))

    assert not found, f"replace module-level task-store paths with tasks_dir(): {sorted(found)}"

    consumers = (
        ("scripts/delegate.py", "tasks_dir"),
        ("scripts/fleet/post_task_reap.py", "default_tasks_dir"),
        ("scripts/fleet/hramatka_hygiene_check.py", "default_tasks_dir"),
        ("scripts/fleet/capacity_pick.py", "default_tasks_dir"),
        ("scripts/maintenance/reclassify_dispatch_status.py", "default_tasks_dir"),
        ("scripts/guardrails/delegate_ownership.py", "tasks_dir"),
    )
    for relative, name in consumers:
        tree = ast.parse((repo / relative).read_text(encoding="utf-8"))
        assert any(
            isinstance(node, ast.ImportFrom)
            and node.module == "scripts.common.task_store_paths"
            and any(alias.name == "tasks_dir" and (alias.asname or alias.name) == name for alias in node.names)
            for node in ast.walk(tree)
        ), relative
        assert any(
            isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name
            for node in ast.walk(tree)
        ), relative

    from scripts.orchestration import worktree_claims

    parent = _REAL_TASKS_DIR.parent
    assert (parent / "preflight_fast_fail.jsonl").resolve() in _DERIVED_LIVE_TASK_PATHS
    assert (parent / worktree_claims.LOCK_DIR_NAME).resolve() in _DERIVED_LIVE_TASK_PATHS
