"""Private installed/pinned/running report. Versions stay out of paths and addresses."""

from __future__ import annotations

import json
import os
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

    path = drift.write_report(
        _REPO_ROOT,
        canonical_root=tmp_path / "canonical-checkout",
        read=read,
        env={"XDG_STATE_HOME": str(tmp_path / "xdg")},
    )
    assert path == tmp_path / "xdg" / "learn-ukrainian" / "stack-drift" / "report.json"
    assert not path.with_suffix(".json.tmp").exists()
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


def test_linked_worktree_refuses_state_inside_the_canonical_checkout(tmp_path: Path) -> None:
    worktree = tmp_path / "worktree"
    canonical = tmp_path / "canonical"
    worktree.mkdir()
    canonical.mkdir()
    state = canonical / "xdg"
    report_path = state / "learn-ukrainian" / "stack-drift" / "report.json"

    with pytest.raises(drift.DriftError, match="outside the repository"):
        drift.write_report(
            worktree,
            canonical_root=canonical,
            read=lambda _name: drift.Reading("unknown", "unknown"),
            env={"XDG_STATE_HOME": str(state)},
        )
    assert not report_path.exists()


def test_resolved_alias_into_the_canonical_checkout_is_refused(tmp_path: Path) -> None:
    worktree = tmp_path / "worktree"
    canonical = tmp_path / "canonical"
    outside = tmp_path / "outside"
    worktree.mkdir()
    canonical.mkdir()
    outside.mkdir()
    alias = outside / "state"
    alias.symlink_to(canonical, target_is_directory=True)
    report_path = canonical / "learn-ukrainian" / "stack-drift" / "report.json"

    with pytest.raises(drift.DriftError, match="outside the repository"):
        drift.write_report(
            worktree,
            canonical_root=canonical,
            read=lambda _name: drift.Reading("unknown", "unknown"),
            env={"XDG_STATE_HOME": str(alias)},
        )
    assert not report_path.exists()


_CHECKOUT_BYTES = b'{"keep":"checkout"}\n'


def _external_state(tmp_path: Path) -> tuple[Path, Path]:
    """A checkout and a state directory outside it. Returns ``(checkout, drift_dir)``."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    drift_dir = tmp_path / "external" / "learn-ukrainian" / "stack-drift"
    drift_dir.mkdir(parents=True)
    return checkout, drift_dir


def _planted_temp_alias_is_refused(tmp_path: Path, plant) -> None:
    checkout, drift_dir = _external_state(tmp_path)
    protected = checkout / "report.json"
    protected.write_bytes(_CHECKOUT_BYTES)
    plant(protected, drift_dir / "report.json.tmp")
    with pytest.raises(drift.DriftError, match="private file"):
        drift.write_report(
            checkout,
            read=lambda _name: drift.Reading("unknown", "unknown"),
            env={"XDG_STATE_HOME": str(tmp_path / "external")},
        )
    assert protected.read_bytes() == _CHECKOUT_BYTES
    assert not (drift_dir / "report.json").exists()


def test_planted_temp_symlink_does_not_change_a_checkout_file(tmp_path: Path) -> None:
    _planted_temp_alias_is_refused(tmp_path, lambda protected, planted: planted.symlink_to(protected))


def test_planted_temp_hardlink_does_not_change_a_checkout_file(tmp_path: Path) -> None:
    _planted_temp_alias_is_refused(tmp_path, lambda protected, planted: os.link(protected, planted))


def test_destination_symlink_does_not_change_a_checkout_file(tmp_path: Path) -> None:
    checkout, drift_dir = _external_state(tmp_path)
    protected = checkout / "report.json"
    protected.write_bytes(_CHECKOUT_BYTES)
    (drift_dir / "report.json").symlink_to(protected)
    with pytest.raises(drift.DriftError, match="private file"):
        drift.write_report(
            checkout,
            read=lambda _name: drift.Reading("unknown", "unknown"),
            env={"XDG_STATE_HOME": str(tmp_path / "external")},
        )
    assert protected.read_bytes() == _CHECKOUT_BYTES


def test_destination_hardlink_does_not_change_a_checkout_file(tmp_path: Path) -> None:
    checkout, drift_dir = _external_state(tmp_path)
    protected = checkout / "report.json"
    protected.write_bytes(_CHECKOUT_BYTES)
    os.link(protected, drift_dir / "report.json")
    with pytest.raises(drift.DriftError, match="private file"):
        drift.write_report(
            checkout,
            read=lambda _name: drift.Reading("unknown", "unknown"),
            env={"XDG_STATE_HOME": str(tmp_path / "external")},
        )
    assert protected.read_bytes() == _CHECKOUT_BYTES


def test_preexisting_regular_temp_file_is_not_opened(tmp_path: Path) -> None:
    checkout, drift_dir = _external_state(tmp_path)
    leftover = drift_dir / "report.json.tmp"
    leftover.write_bytes(b"leave-me")
    path = drift.write_report(
        checkout,
        read=lambda _name: drift.Reading("unknown", "unknown"),
        env={"XDG_STATE_HOME": str(tmp_path / "external")},
    )
    assert leftover.read_bytes() == b"leave-me"
    assert path == drift_dir / "report.json"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.mark.parametrize("kind", ["dir", "file"])
def test_state_dir_inside_any_git_checkout_is_refused(tmp_path: Path, kind: str) -> None:
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    marker = foreign / ".git"
    if kind == "dir":
        marker.mkdir()
    else:
        marker.write_text("gitdir: /unused\n", encoding="utf-8")
    session = tmp_path / "session"
    session.mkdir()
    report_path = foreign / "learn-ukrainian" / "stack-drift" / "report.json"
    with pytest.raises(drift.DriftError, match="outside the repository"):
        drift.write_report(
            session,
            read=lambda _name: drift.Reading("unknown", "unknown"),
            env={"XDG_STATE_HOME": str(foreign)},
        )
    assert not report_path.exists()


def test_resolved_alias_into_a_foreign_checkout_is_refused(tmp_path: Path) -> None:
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / ".git").write_text("gitdir: /unused\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    alias = outside / "state"
    alias.symlink_to(foreign, target_is_directory=True)
    session = tmp_path / "session"
    session.mkdir()
    report_path = foreign / "learn-ukrainian" / "stack-drift" / "report.json"
    with pytest.raises(drift.DriftError, match="outside the repository"):
        drift.write_report(
            session,
            read=lambda _name: drift.Reading("unknown", "unknown"),
            env={"XDG_STATE_HOME": str(alias)},
        )
    assert not report_path.exists()
