"""Tests for the primary-venv integrity probe (#6830).

scripts/audit/check_venv_integrity.py — detection ONLY of an empty/broken
primary venv: (a) a curated set of lightweight core modules failing to
import, (b) console-script launchers whose embedded interpreter doesn't
match the venv's own. No repair path exists here; a detection is always an
ALERT (mirrors check_node_modules_integrity.py's posture and test shape).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from scripts.audit.check_venv_integrity import (
    check_sentinel_imports,
    check_venv_integrity,
    find_broken_console_scripts,
    main,
)


def _events(state_dir: Path) -> list[dict]:
    path = state_dir / "events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _make_fake_venv(tmp_path: Path, name: str = "venv") -> tuple[Path, Path]:
    """A minimal venv: bin/python + bin/python3 symlinked to THIS interpreter,
    mirroring how `python -m venv` / `uv venv` actually lay out bin/ (the
    venv's own python is normally a symlink OUT to the base interpreter, not
    a copy — the whole reason find_broken_console_scripts cannot use a
    "resolves inside venv_dir" test)."""
    venv_dir = tmp_path / name
    bin_dir = venv_dir / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "python").symlink_to(Path(sys.executable))
    (bin_dir / "python3").symlink_to(Path("python"))
    return venv_dir, bin_dir


def _write_direct_launcher(bin_dir: Path, name: str, interpreter: Path) -> Path:
    script = bin_dir / name
    script.write_text(f"#!{interpreter}\n# -*- coding: utf-8 -*-\nprint('ok')\n")
    script.chmod(0o755)
    return script


def _write_exec_trick_launcher(bin_dir: Path, name: str, interpreter: Path) -> Path:
    """Pip's long-path launcher form — matches the real broken pytest/py.test/
    cbor2 scripts found on the primary venv verbatim (#6830 live finding)."""
    script = bin_dir / name
    script.write_text(f"#!/bin/sh\n'''exec' '{interpreter}' \"$0\" \"$@\"\n' '''\n# -*- coding: utf-8 -*-\nprint('ok')\n")
    script.chmod(0o755)
    return script


# ---------------------------------------------------------------------------
# console-script shebang detection
# ---------------------------------------------------------------------------


def test_healthy_direct_shebang_is_not_flagged(tmp_path: Path) -> None:
    venv_dir, bin_dir = _make_fake_venv(tmp_path)
    _write_direct_launcher(bin_dir, "healthy", bin_dir / "python")

    assert find_broken_console_scripts(venv_dir) == []


def test_healthy_exec_trick_launcher_is_not_flagged(tmp_path: Path) -> None:
    """The long-path launcher form itself is healthy when the embedded path
    IS this venv's interpreter — only the pointed-at path matters, not which
    of the two pip launcher forms is used."""
    venv_dir, bin_dir = _make_fake_venv(tmp_path)
    _write_exec_trick_launcher(bin_dir, "pytest", bin_dir / "python")

    assert find_broken_console_scripts(venv_dir) == []


def test_launcher_pointing_at_deleted_path_is_detected(tmp_path: Path) -> None:
    """Reproduces the live #6830 finding verbatim: the exec-trick form
    pointing at a python3 under a worktree venv that no longer exists."""
    venv_dir, bin_dir = _make_fake_venv(tmp_path)
    deleted = tmp_path / "some-worktree" / ".venv" / "bin" / "python3"
    _write_exec_trick_launcher(bin_dir, "pytest", deleted)

    found = find_broken_console_scripts(venv_dir)
    assert len(found) == 1
    assert found[0] == {"script": "pytest", "interpreter": str(deleted), "exists": False}


def test_launcher_pointing_at_a_different_existing_interpreter_is_detected(tmp_path: Path) -> None:
    """A launcher can point at a path that EXISTS but still isn't this venv's
    interpreter (e.g. another venv survives but this one's identity drifted)
    — existence alone must not clear it."""
    venv_dir, bin_dir = _make_fake_venv(tmp_path)
    other_interpreter = tmp_path / "other-venv" / "bin" / "python3"
    other_interpreter.parent.mkdir(parents=True)
    other_interpreter.write_text("#!/usr/bin/env python3\n")  # real file, distinct realpath
    _write_direct_launcher(bin_dir, "stray", other_interpreter)

    found = find_broken_console_scripts(venv_dir)
    assert len(found) == 1
    assert found[0]["script"] == "stray"
    assert found[0]["exists"] is True


def test_interpreter_symlinks_themselves_are_not_scanned(tmp_path: Path) -> None:
    """bin/python and bin/python3 are the venv's own identity, not
    console-script launchers — scanning them would be nonsensical (they'd
    trivially "match themselves") and is explicitly skipped."""
    venv_dir, _bin_dir = _make_fake_venv(tmp_path)

    assert find_broken_console_scripts(venv_dir) == []


def test_non_launcher_files_are_ignored(tmp_path: Path) -> None:
    """A binary/non-text entry in bin/ (no `#!` first line) must not crash
    the scan or be misread as a broken launcher."""
    venv_dir, bin_dir = _make_fake_venv(tmp_path)
    (bin_dir / "some-binary-tool").write_bytes(b"\x7fELF\x02\x01\x01\x00" + os.urandom(32))

    assert find_broken_console_scripts(venv_dir) == []


def test_missing_venv_bin_directory_does_not_crash(tmp_path: Path) -> None:
    venv_dir = tmp_path / "no-such-venv"
    assert find_broken_console_scripts(venv_dir) == []


# ---------------------------------------------------------------------------
# sentinel import detection
# ---------------------------------------------------------------------------


def test_sentinel_imports_all_present(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.audit.check_venv_integrity as mod

    monkeypatch.setattr(mod, "CORE_SENTINEL_MODULES", {"json": "stdlib", "os": "stdlib"})
    missing, error = check_sentinel_imports(Path(sys.executable))
    assert missing == []
    assert error is None


def test_sentinel_imports_detects_missing_module(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.audit.check_venv_integrity as mod

    monkeypatch.setattr(
        mod,
        "CORE_SENTINEL_MODULES",
        {"json": "stdlib", "definitely_not_a_real_module_xyz123": "fake-pkg"},
    )
    missing, error = check_sentinel_imports(Path(sys.executable))
    assert error is None
    assert len(missing) == 1
    assert "definitely_not_a_real_module_xyz123" in missing[0]


def test_sentinel_imports_missing_interpreter_reports_error(tmp_path: Path) -> None:
    missing, error = check_sentinel_imports(tmp_path / "no-such-python")
    assert missing == []
    assert error is not None
    assert "does not exist" in error


# ---------------------------------------------------------------------------
# combined probe
# ---------------------------------------------------------------------------


def test_healthy_venv_is_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.audit.check_venv_integrity as mod

    monkeypatch.setattr(mod, "CORE_SENTINEL_MODULES", {"json": "stdlib"})
    repo = tmp_path / "repo"
    _venv_dir, bin_dir = _make_fake_venv(repo, name=".venv")
    _write_exec_trick_launcher(bin_dir, "pytest", bin_dir / "python")

    ok, message = check_venv_integrity(
        repo, tasks_dir=tmp_path / "no-tasks", state_dir=tmp_path / "state", python_exe=bin_dir / "python"
    )
    assert ok is True
    assert "ok" in message
    assert _events(tmp_path / "state") == []


def test_broken_launcher_is_alerted_and_recorded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.audit.check_venv_integrity as mod

    monkeypatch.setattr(mod, "CORE_SENTINEL_MODULES", {"json": "stdlib"})
    repo = tmp_path / "repo"
    _venv_dir, bin_dir = _make_fake_venv(repo, name=".venv")
    deleted = tmp_path / "gone" / ".venv" / "bin" / "python3"
    _write_exec_trick_launcher(bin_dir, "pytest", deleted)

    ok, message = check_venv_integrity(
        repo, tasks_dir=tmp_path / "no-tasks", state_dir=tmp_path / "state", python_exe=bin_dir / "python"
    )
    assert ok is False
    assert "pytest" in message
    assert "force-reinstall" in message
    assert "pip install --force-reinstall" in message
    # the printed repair command must name the OWNING PACKAGE, never invoke
    # anything here — this probe must never mutate the venv itself.
    assert f"{bin_dir / 'python'} -m pip install --force-reinstall pytest" in message

    alerts = [e for e in _events(tmp_path / "state") if e["event"] == "venv_integrity_alert"]
    assert alerts
    assert alerts[0]["broken_console_scripts"][0]["script"] == "pytest"


def test_py_test_and_pytest_dedupe_to_one_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """py.test and pytest are both launchers from the SAME `pytest`
    distribution — the repair command must not suggest installing a
    nonexistent `py.test` package."""
    import scripts.audit.check_venv_integrity as mod

    monkeypatch.setattr(mod, "CORE_SENTINEL_MODULES", {"json": "stdlib"})
    repo = tmp_path / "repo"
    _venv_dir, bin_dir = _make_fake_venv(repo, name=".venv")
    deleted = tmp_path / "gone" / ".venv" / "bin" / "python3"
    _write_exec_trick_launcher(bin_dir, "pytest", deleted)
    _write_exec_trick_launcher(bin_dir, "py.test", deleted)

    ok, message = check_venv_integrity(
        repo, tasks_dir=tmp_path / "no-tasks", state_dir=tmp_path / "state", python_exe=bin_dir / "python"
    )
    assert ok is False
    assert "py.test" not in message.split("force-reinstall", 1)[1]  # not suggested as an install target
    assert message.count(" pytest") >= 1


def test_missing_sentinel_module_is_alerted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.audit.check_venv_integrity as mod

    monkeypatch.setattr(mod, "CORE_SENTINEL_MODULES", {"definitely_not_a_real_module_xyz123": "fake-pkg"})
    repo = tmp_path / "repo"
    _venv_dir, bin_dir = _make_fake_venv(repo, name=".venv")

    ok, message = check_venv_integrity(
        repo, tasks_dir=tmp_path / "no-tasks", state_dir=tmp_path / "state", python_exe=bin_dir / "python"
    )
    assert ok is False
    assert "sentinel module" in message


# ---------------------------------------------------------------------------
# attribution: running dispatches recorded on the alert event
# ---------------------------------------------------------------------------


def test_alert_event_names_running_dispatches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.audit.check_venv_integrity as mod

    monkeypatch.setattr(mod, "CORE_SENTINEL_MODULES", {"json": "stdlib"})
    repo = tmp_path / "repo"
    _venv_dir, bin_dir = _make_fake_venv(repo, name=".venv")
    _write_exec_trick_launcher(bin_dir, "pytest", tmp_path / "gone" / "python3")

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "agy-suspect.json").write_text(
        json.dumps({"task_id": "agy/suspect", "agent": "agy", "status": "running", "pid": os.getpid()})
    )

    check_venv_integrity(repo, tasks_dir=tasks_dir, state_dir=tmp_path / "state", python_exe=bin_dir / "python")
    alerts = [e for e in _events(tmp_path / "state") if e["event"] == "venv_integrity_alert"]
    assert alerts
    running = alerts[0]["running_dispatches"]
    assert any(d["task_id"] == "agy/suspect" for d in running)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_exit_codes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.audit.check_venv_integrity as mod

    monkeypatch.setattr(mod, "CORE_SENTINEL_MODULES", {"json": "stdlib"})
    repo = tmp_path / "repo"
    _venv_dir, bin_dir = _make_fake_venv(repo, name=".venv")
    _write_exec_trick_launcher(bin_dir, "pytest", bin_dir / "python")
    state_dir = tmp_path / "cli-state"
    tasks_dir = tmp_path / "no-tasks"
    argv = [
        "--repo",
        str(repo),
        "--python-exe",
        str(bin_dir / "python"),
        "--state-dir",
        str(state_dir),
        "--tasks-dir",
        str(tasks_dir),
    ]

    assert main(argv) == 0

    # Break it: overwrite the launcher to point somewhere else.
    _write_exec_trick_launcher(bin_dir, "pytest", tmp_path / "gone" / "python3")
    assert main(argv) == 1
