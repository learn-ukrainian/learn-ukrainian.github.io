"""Behavioral proofs for the batch_state TTL sweep (#11418).

Each test names the defect class it would catch: a dry run that mutates, a
reference or hold guard that stops protecting, a missing recheck, a followed
symlink, a crossed mount, an unreadable tree, or an unapproved TTL that apply
accepts.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import time
from pathlib import Path

import pytest

from scripts.hygiene import batch_state_ttl_sweep as sweep_module
from scripts.hygiene.batch_state_ttl_sweep import TtlUnapproved, sweep_batch_state

DAY = 86400.0
OLD_DAYS = 30.0
TTL_DAYS = 7.0


def _age_tree(path: Path, days: float) -> None:
    stamp = time.time() - days * DAY
    for node in sorted(path.rglob("*"), reverse=True):
        os.utime(node, (stamp, stamp), follow_symlinks=False)
    os.utime(path, (stamp, stamp), follow_symlinks=False)


def _digest(root: Path) -> str:
    """Content and metadata digest; a dry run must leave it byte-for-byte identical."""
    digest = hashlib.sha256()
    for node in sorted(root.rglob("*")):
        info = node.lstat()
        digest.update(f"{node.relative_to(root)}|{info.st_mode}|{info.st_mtime_ns}|{info.st_size}".encode())
        if stat.S_ISREG(info.st_mode):
            digest.update(node.read_bytes())
        elif stat.S_ISLNK(info.st_mode):
            digest.update(os.readlink(node).encode())
    return digest.hexdigest()


def _manifest(entry: Path, name: str, owner: str | None, *, legacy: bool = False) -> None:
    data = {"task_id": name, "retention_disposition": "retained"}
    if owner is not None and not legacy:
        data["owner"] = owner
    (entry / f"{name}.manifest.json").write_text(json.dumps(data) + "\n")


def _preserved(batch: Path, name: str, *, owner: str | None = None, legacy: bool = False) -> Path:
    entry = batch / "preserved" / name
    (entry / "artifact").mkdir(parents=True)
    (entry / "artifact" / "data.bin").write_bytes(b"x" * 4096)
    if owner is not None or legacy:
        _manifest(entry, name, owner, legacy=legacy)
    return entry


def _config(tmp_path: Path, *, unapproved: bool = False) -> Path:
    value = "UNAPPROVED" if unapproved else TTL_DAYS
    path = tmp_path / "ttl.json"
    path.write_text(
        json.dumps(
            {
                "schema": "batch-state-ttl-sweep.v1",
                "roots": [
                    {"path": "batch_state/preserved", "ttl_days": value, "owner": "manifest"},
                    {
                        "path": "batch_state/backups/archives",
                        "ttl_days": value,
                        "owner": "backup",
                        "keep_newest_archive": True,
                    },
                    {
                        "path": "batch_state/backups/alerts",
                        "ttl_days": value,
                        "owner": "backup",
                        "exclude_names": ["last-run.json"],
                    },
                ],
            }
        )
        + "\n"
    )
    return path


@pytest.fixture
def area(tmp_path):
    batch = (tmp_path / "batch_state").resolve()
    for name in ("preserved", "backups/archives", "backups/alerts", "tasks"):
        (batch / name).mkdir(parents=True)
    (batch / "reports").mkdir()

    eligible = _preserved(batch, "old-owner", owner="old-owner")
    legacy = _preserved(batch, "legacy-owner", legacy=True)
    fresh = _preserved(batch, "fresh-owner", owner="fresh-owner")
    held = _preserved(batch, "held-owner", owner="held-owner")
    referenced = _preserved(batch, "referenced-owner", owner="referenced-owner")
    unknown = _preserved(batch, "unknown-owner")
    unreadable = _preserved(batch, "unreadable-owner", owner="unreadable-owner")
    mounted = _preserved(batch, "mount-owner", owner="mount-owner")
    for entry in (eligible, legacy, held, referenced, unknown, unreadable, mounted):
        _age_tree(entry, OLD_DAYS)
    _age_tree(fresh, 0.0)

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.bin").write_bytes(b"outside")
    link = batch / "preserved" / "link-owner"
    link.symlink_to(outside, target_is_directory=True)

    archives = batch / "backups" / "archives"
    for stem, days in (("old-archive", OLD_DAYS), ("new-archive", 0.0)):
        for suffix in (".tar.zst", ".tar.zst.manifest", ".tar.zst.contents.sha256"):
            (archives / f"{stem}{suffix}").write_bytes(b"a" * 1024)
        _age_tree(archives / f"{stem}.tar.zst", days)
        _age_tree(archives / f"{stem}.tar.zst.manifest", days)
        _age_tree(archives / f"{stem}.tar.zst.contents.sha256", days)

    alerts = batch / "backups" / "alerts"
    (alerts / "last-run.json").write_text("{}\n")
    (alerts / "alert-old.json").write_text("{}\n")
    _age_tree(alerts, OLD_DAYS)

    tasks = batch / "tasks"
    (tasks / "run-old.json").write_text(
        json.dumps(
            {
                "task_id": "run-old",
                "status": "running",
                "worktree_path": str(referenced),
                "cwd": str(referenced / "artifact"),
            }
        )
        + "\n"
    )
    (batch / "holds.json").write_text(
        json.dumps(
            {
                "schema": "batch-state-retention.v1",
                "holds": [
                    {
                        "path": "batch_state/preserved/held-owner/",
                        "reason": "Evidence for #1.",
                        "until": "#1 closes",
                    }
                ],
            }
        )
        + "\n"
    )
    return {
        "batch": batch,
        "tmp": tmp_path,
        "config": _config(tmp_path),
        "tasks": tasks,
        "holds": batch / "holds.json",
        "eligible": eligible,
        "legacy": legacy,
        "fresh": fresh,
        "held": held,
        "referenced": referenced,
        "unknown": unknown,
        "unreadable": unreadable,
        "mounted": mounted,
        "link": link,
        "outside": outside,
    }


def _sweep(area, **overrides):
    options = dict(
        batch_root=area["batch"],
        config_path=area["config"],
        task_root=area["tasks"],
        retention_list=area["holds"],
        now=time.time(),
        repo_root=area["tmp"],
    )
    options.update(overrides)
    return sweep_batch_state(**options)


def test_dry_run_reports_every_entry_and_deletes_nothing(area):
    before = _digest(area["batch"])
    report = _sweep(area)
    assert _digest(area["batch"]) == before, "dry run mutated the tree"
    assert not [name for name in os.listdir(area["batch"] / "preserved") if name.startswith(".lu-")]
    reasons = {row["path"].rsplit("/", 1)[-1]: row["reason"] for row in report["rows"]}
    assert reasons["old-owner"] == "expired"
    assert reasons["legacy-owner"] == "expired"
    assert reasons["fresh-owner"] == "too_young"
    assert reasons["held-owner"] == "held"
    assert reasons["referenced-owner"] == "task_reference"
    assert reasons["unknown-owner"] == "owner_unknown"
    assert reasons["link-owner"] == "symlink_or_not_directory"
    assert reasons["old-archive"] == "expired"
    assert reasons["new-archive"] == "newest_archive"
    assert reasons["alert-old.json"] == "expired"
    assert "last-run.json" not in reasons
    assert {row["path"].rsplit("/", 1)[-1] for row in report["rows"] if row["decision"] == "would_delete"} == {
        "old-owner",
        "legacy-owner",
        "old-archive",
        "alert-old.json",
        "unreadable-owner",
        "mount-owner",
    }
    assert report["deleted_entries"] == 0


def test_apply_deletes_only_expired_and_writes_measured_receipt(area):
    receipt = area["tmp"] / "receipt.json"
    report = _sweep(area, apply=True, receipt_path=receipt)
    assert report["errors"] == 0
    assert not area["eligible"].exists()
    assert not area["legacy"].exists()
    assert not (area["batch"] / "backups" / "archives" / "old-archive.tar.zst").exists()
    assert not (area["batch"] / "backups" / "alerts" / "alert-old.json").exists()
    for kept in (
        area["fresh"],
        area["held"],
        area["referenced"],
        area["unknown"],
        area["link"],
        area["outside"],
        area["batch"] / "backups" / "archives" / "new-archive.tar.zst",
        area["batch"] / "backups" / "alerts" / "last-run.json",
    ):
        assert os.path.lexists(kept), f"{kept} should be preserved"
    assert report["deleted_entries"] == 6
    data = json.loads(receipt.read_text())
    assert data["schema"] == "batch-state-ttl-sweep-receipt.v1"
    assert {row["path"].rsplit("/", 1)[-1] for row in data["entries"]} == {
        "old-owner",
        "legacy-owner",
        "old-archive",
        "alert-old.json",
        "unreadable-owner",
        "mount-owner",
    }
    assert data["freed_bytes_summed"] == sum(row["bytes"] for row in data["entries"])
    assert data["freed_bytes_measured"] == max(0, data["free_bytes_after"] - data["free_bytes_before"])
    for row in data["entries"]:
        assert row["owner"]
        assert row["age_days"] > TTL_DAYS
        assert row["bytes"] > 0


def test_apply_refuses_while_any_ttl_is_unapproved(area):
    config = _config(area["tmp"], unapproved=True)
    before = _digest(area["batch"])
    with pytest.raises(TtlUnapproved):
        _sweep(area, config_path=config, apply=True)
    assert _digest(area["batch"]) == before


def test_unapproved_config_dry_run_is_typed_and_override_is_hypothetical(area):
    config = _config(area["tmp"], unapproved=True)
    report = _sweep(area, config_path=config)
    assert report["ttl_source"] == "unapproved"
    assert {row["reason"] for row in report["rows"]} >= {"ttl_unapproved"}
    assert report["would_delete_entries"] == 0
    hypothetical = _sweep(area, config_path=config, ttl_override=TTL_DAYS)
    assert hypothetical["ttl_source"] == "override_hypothetical"
    hypothetical_names = {
        row["path"].rsplit("/", 1)[-1] for row in hypothetical["rows"] if row["decision"] == "would_delete"
    }
    assert {"old-owner", "legacy-owner", "old-archive", "alert-old.json"} <= hypothetical_names
    with pytest.raises(ValueError):
        _sweep(area, config_path=config, apply=True, ttl_override=TTL_DAYS)


def test_apply_refused_by_cli_returns_typed_exit_code(area):
    config = _config(area["tmp"], unapproved=True)
    code = sweep_module.main(
        [
            "--batch-root",
            str(area["batch"]),
            "--config",
            str(config),
            "--tasks",
            str(area["tasks"]),
            "--retention-list",
            str(area["holds"]),
            "--apply",
            "--summary",
        ]
    )
    assert code == sweep_module.EXIT_TTL_UNAPPROVED


def test_symlink_is_preserved_and_target_is_untouched(area):
    report = _sweep(area)
    row = next(row for row in report["rows"] if row["path"].endswith("/link-owner"))
    assert row["reason"] == "symlink_or_not_directory"
    _sweep(area, apply=True, receipt_path=area["tmp"] / "receipt.json")
    assert area["link"].is_symlink()
    assert (area["outside"] / "keep.bin").read_bytes() == b"outside"


def test_mount_point_is_preserved(area, monkeypatch):
    monkeypatch.setattr(sweep_module.sweep, "mount_points", lambda: frozenset({str(area["mounted"])}))
    report = _sweep(area)
    row = next(row for row in report["rows"] if row["path"].endswith("/mount-owner"))
    assert row["reason"] == "mount_point"
    _sweep(area, apply=True, receipt_path=area["tmp"] / "receipt.json")
    assert area["mounted"].exists()


def test_unreadable_tree_is_preserved(area):
    if os.geteuid() == 0:
        pytest.skip("root can read a mode-000 tree")
    area["unreadable"].chmod(0o000)
    try:
        report = _sweep(area)
        row = next(row for row in report["rows"] if row["path"].endswith("/unreadable-owner"))
        assert row["reason"] == "tree_unknown"
        _sweep(area, apply=True, receipt_path=area["tmp"] / "receipt.json")
        assert area["unreadable"].exists()
    finally:
        area["unreadable"].chmod(0o755)


def test_write_after_fingerprint_is_caught_by_the_recheck(area, monkeypatch):
    """Dropping the post-rename recheck would delete a tree written after the scan."""
    entry = area["eligible"]
    target = entry / "artifact" / "data.bin"
    original = sweep_module.sweep.tree_fingerprint
    calls = {"count": 0}

    def racing(path):
        result = original(path)
        if path == entry:
            calls["count"] += 1
            if calls["count"] == 1 and result is not None:
                target.write_bytes(b"written after the scan")
        return result

    monkeypatch.setattr(sweep_module.sweep, "tree_fingerprint", racing)
    report = _sweep(area, apply=True, receipt_path=area["tmp"] / "receipt.json")
    row = next(row for row in report["rows"] if row["path"].endswith("/old-owner"))
    assert row["reason"] == "recent_write"
    assert row["decision"] == "preserve"
    assert target.exists()


def test_archives_group_sidecars_with_the_newest_archive_protected(area):
    report = _sweep(area)
    rows = {row["path"].rsplit("/", 1)[-1]: row for row in report["rows"]}
    assert set(rows) >= {"old-archive", "new-archive"}
    assert rows["new-archive"]["reason"] == "newest_archive"
    assert rows["old-archive"]["reason"] == "expired"
    assert "old-archive.tar.zst" not in rows
