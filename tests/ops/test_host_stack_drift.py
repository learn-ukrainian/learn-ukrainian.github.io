"""Private installed/pinned/running report. Versions stay out of paths and addresses."""

from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest

from scripts.ops import host_stack_drift as drift
from tests._host_path_guard import FIXTURE_HOME, assert_no_host_facts, assert_no_host_paths

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_version_token_ignores_paths_and_addresses() -> None:
    text = f"gh version 2.2.2 ({FIXTURE_HOME}/bin/gh) see https://example.invalid/tag 203.0.113.10"
    assert drift.version_token(text) == "2.2.2"
    assert drift.version_token("203.0.113.10") == "unknown"


def test_probe_keeps_the_version_and_drops_the_binary_path(tmp_path: Path) -> None:
    binary = tmp_path / "gh"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    other = tmp_path / "other-gh"
    other.write_text("#!/bin/sh\n", encoding="utf-8")

    def which(command: str) -> str | None:
        return str(binary) if command == "gh" else None

    def run(argv: tuple[str, ...]) -> str:
        return f"gh version 2.2.2 from {binary}"

    matched = drift.probe_component(
        "gh",
        which=which,
        run=run,
        exes_for=lambda comm: [binary] if comm == "gh" else [],
        python_version="3.12.14",
        python_executable=None,
    )
    assert matched == drift.Reading("2.2.2", "2.2.2")

    drifted = drift.probe_component(
        "gh",
        which=which,
        run=run,
        exes_for=lambda comm: [other] if comm == "gh" else [],
        python_version="3.12.14",
        python_executable=None,
    )
    assert drifted.running == "differs"
    assert str(binary) not in drifted.installed
    assert str(other) not in drifted.running


def test_report_is_versions_under_stack_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg"))

    def read(name: str) -> drift.Reading:
        if name == "gh":
            return drift.Reading("2.2.2", "not_running")
        return drift.Reading("absent", "not_running")

    path = drift.write_report(_REPO_ROOT, read=read, env={"XDG_STATE_HOME": str(tmp_path / "xdg")})
    assert path == tmp_path / "xdg" / "learn-ukrainian" / "stack-drift" / "report.json"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    text = path.read_text(encoding="utf-8")
    saved = json.loads(text)
    by_name = {row["name"]: row for row in saved["rows"]}
    assert by_name["gh"] == {"name": "gh", "pinned": "unknown", "installed": "2.2.2", "running": "not_running"}
    assert by_name["python"]["pinned"] == "3.12.14"
    assert str(tmp_path) not in text
    assert_no_host_paths(text, "stack drift report")
    assert_no_host_facts(text, "stack drift report")


def test_state_dir_inside_the_repository_is_refused(tmp_path: Path) -> None:
    inside = tmp_path / "repo"
    inside.mkdir()
    with pytest.raises(drift.DriftError):
        drift.write_report(
            inside, read=lambda _name: drift.Reading("unknown", "unknown"), env={"XDG_STATE_HOME": str(inside)}
        )
