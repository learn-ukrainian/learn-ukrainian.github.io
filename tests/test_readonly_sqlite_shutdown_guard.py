"""The shared-reader child must not look successful if a reader is still alive or has raised (#11208).

Removing the join call fails the source guard. Removing the excepthook assignment
fails that guard too, and the injected-reader test exits 0 instead of 3.
"""

from __future__ import annotations

from tests.test_readonly_sqlite import make_forms_database, run_shared_reader_child


def _forms(tmp_path):
    path = tmp_path / "forms.db"
    make_forms_database(path)
    return path


def test_live_reader_threads_fail_the_child(tmp_path):
    result = run_shared_reader_child(
        _forms(tmp_path),
        env={"SHARED_READER_HOLD_READERS": "1", "SHARED_READER_WORK_S": "0.15", "SHARED_READER_JOIN_S": "0.4"},
        timeout=15,
    )
    assert result.returncode == 2, result.stderr[-2000:]
    assert "still alive" in result.stderr
