"""Report-only batch_state staleness check (#9737)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from scripts.hygiene import batch_state_retention as retention

DAY = 86400


def make(root: Path, name: str, age_days: float, *, nested: str = "deep/file") -> Path:
    path = root / name
    leaf = path / nested
    leaf.parent.mkdir(parents=True, exist_ok=True)
    leaf.write_bytes(b"x" * 8192)
    stamp = time.time() - age_days * DAY
    for node in [*sorted(path.rglob("*"), reverse=True), path]:
        os.utime(node, (stamp, stamp), follow_symlinks=False)
    return path


def holds_file(tmp_path: Path, holds: list[dict]) -> Path:
    path = tmp_path / "retention.json"
    path.write_text(json.dumps({"schema": retention.SCHEMA, "holds": holds}))
    return path


@pytest.fixture
def batch(tmp_path):
    root = tmp_path / "batch_state"
    root.mkdir()
    return root


def test_stale_fresh_excluded_and_held(batch, tmp_path):
    make(batch, "old-run", 10)
    make(batch, "busy-run", 10)
    os.utime(batch / "busy-run" / "deep" / "file")  # one recent deep write keeps it fresh
    for name in ("tasks", "preserved", "reports", "branch-archive"):
        make(batch, name, 30)
    make(batch, "codex-atlas", 30, nested="session-20260929-resume/evidence")
    (batch / "loose-file").write_text("not a directory")
    (batch / "linked").symlink_to(batch / "old-run")
    holds = retention.load_holds(
        holds_file(tmp_path, [{"path": "batch_state/codex-atlas/session-20260929-resume/", "reason": "#9250"}])
    )
    before = {node: node.lstat().st_mtime_ns for node in batch.rglob("*")}
    result = retention.report(batch, holds=holds)
    rows = {row["path"]: row for row in result["rows"]}
    assert set(rows) == {"batch_state/old-run/", "batch_state/codex-atlas/"}
    assert rows["batch_state/old-run/"]["status"] == "stale" and rows["batch_state/old-run/"]["bytes"] > 8192
    assert rows["batch_state/codex-atlas/"]["status"] == "held"
    assert rows["batch_state/codex-atlas/"]["holds"] == [
        {"path": "batch_state/codex-atlas/session-20260929-resume/", "reason": "#9250"}
    ]
    assert result["counts"] == {"excluded": 4, "fresh": 1, "held": 1, "stale": 1, "unknown": 0}
    assert result["stale_bytes"] == rows["batch_state/old-run/"]["bytes"]
    # Report only: nothing created, removed or modified.
    assert {node: node.lstat().st_mtime_ns for node in batch.rglob("*")} == before


def test_stale_days_threshold(batch):
    make(batch, "run", 5)
    assert retention.report(batch, holds=[])["counts"]["fresh"] == 1
    assert retention.report(batch, holds=[], stale_days=3)["counts"]["stale"] == 1
    with pytest.raises(ValueError):
        retention.report(batch, holds=[], stale_days=0)


def test_symlinks_and_mounts_are_not_followed(batch, tmp_path, monkeypatch):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "fresh").write_text("new")
    run = make(batch, "run", 10)
    (run / "link").symlink_to(outside, target_is_directory=True)
    os.utime(run / "link", (time.time() - 10 * DAY,) * 2, follow_symlinks=False)
    os.utime(run, (time.time() - 10 * DAY,) * 2)
    assert retention.report(batch, holds=[])["rows"][0]["status"] == "stale"
    monkeypatch.setattr(retention, "mount_points", lambda: frozenset({str(run / "deep")}))
    row = retention.report(batch, holds=[])["rows"][0]
    assert row["status"] == "unknown" and row["reason"] == "mount_point"
    monkeypatch.setattr(retention, "mount_points", lambda: None)
    assert retention.report(batch, holds=[])["rows"][0]["reason"] == "mount_probe_unknown"


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        {"schema": "other", "holds": []},
        {"schema": retention.SCHEMA, "holds": {}},
        {"schema": retention.SCHEMA, "holds": [{"path": "batch_state/x/"}]},
        {"schema": retention.SCHEMA, "holds": [{"path": "/abs/batch_state/x", "reason": "r"}]},
        {"schema": retention.SCHEMA, "holds": [{"path": "batch_state/../x", "reason": "r"}]},
        {"schema": retention.SCHEMA, "holds": [{"path": "batch_state", "reason": "r"}]},
    ],
)
def test_malformed_retention_list_refused(tmp_path, payload):
    path = tmp_path / "retention.json"
    path.write_text(payload if isinstance(payload, str) else json.dumps(payload))
    with pytest.raises(retention.RetentionListError):
        retention.load_holds(path)


def test_seeded_retention_list_is_valid():
    holds = retention.load_holds(retention.RETENTION_LIST)
    assert ("codex-atlas", "session-20260929-resume") in {hold["parts"] for hold in holds}


def test_cli_json_table_and_errors(batch, tmp_path, capsys):
    make(batch, "old-run", 10)
    argv = ["--batch-root", str(batch), "--retention-list", str(holds_file(tmp_path, []))]
    assert retention.main([*argv, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["counts"]["stale"] == 1
    assert retention.main(argv) == 0
    out = capsys.readouterr().out
    assert "| batch_state/old-run/ | stale |" in out and str(tmp_path) not in out
    with pytest.raises(SystemExit) as exc:
        retention.main(["--batch-root", str(batch), "--retention-list", str(tmp_path / "missing.json")])
    assert exc.value.code == 2
