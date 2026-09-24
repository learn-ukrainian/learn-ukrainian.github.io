"""The suite must not write the live dispatch task store (#8654)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import _REAL_TASKS_DIR


def test_write_to_real_task_store_fails() -> None:
    """A direct write under the live ``batch_state/tasks`` fails before creating a file."""
    target = _REAL_TASKS_DIR / "t-guard-should-not-exist.json"
    assert not target.exists()
    with pytest.raises(pytest.fail.Exception, match="real dispatch task store"):
        target.write_text("{}\n", encoding="utf-8")
    assert not target.exists()


def test_isolate_dispatch_task_store_is_not_the_live_dir(
    _isolate_dispatch_task_store: Path,
) -> None:
    """The autouse redirect is a temp directory, and a later override still wins."""
    import scripts.delegate as delegate_mod

    assert _isolate_dispatch_task_store != _REAL_TASKS_DIR
    assert _isolate_dispatch_task_store == delegate_mod._TASKS_DIR
    assert _REAL_TASKS_DIR not in delegate_mod._state_path("t-isolated").parents
