"""Ended-session proofs and scratch boundary tests for #8783."""

from __future__ import annotations

import errno
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.maintenance import claude_session_scratch as scratch

SESSION = "12345678-1234-1234-1234-123456789abc"
REPLACEMENT = "87654321-4321-4321-4321-cba987654321"
DEAD = scratch.ProcessEvidence(complete=True)
UNKNOWN = scratch.ProcessEvidence()
LIVE = scratch.ProcessEvidence(frozenset({SESSION}), complete=True)


def _session(tmp_path: Path, *, project: bool = True, session: str = SESSION) -> tuple[Path, Path]:
    root = tmp_path / f"claude-{os.getuid()}"
    directory = root / "project" / session if project else root / session
    directory.mkdir(parents=True)
    (directory / "scratchpad").mkdir()
    (directory / "scratchpad" / "payload").write_bytes(b"keep every byte\x00\xff")
    return root, directory


def _confirmed(tmp_path: Path) -> Path:
    root = tmp_path / "thread-rollovers" / "claude"
    lineage = root / "lineage"
    lineage.mkdir(parents=True)
    (lineage / "lease.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "agent": "claude",
                "active": {"thread_id": SESSION},
                "replacement": {
                    "thread_id": REPLACEMENT,
                    "status": "started",
                    "confirmed_at": "2026-10-03T00:00:00Z",
                    "identity": {
                        "predecessor_task_id": SESSION,
                        "replacement_task_id": REPLACEMENT,
                        "lifecycle_state": "confirmed",
                    },
                    "canary_proof": {"status": "PASS"},
                    "strict_verdict": {"verdict": "PASS"},
                },
                "cleanup": {"old_automation_ready_to_delete": True, "confirmed_at": "2026-10-03T00:00:00Z"},
            }
        )
    )
    return root


@pytest.mark.parametrize("project", [False, True])
def test_process_gone_removes_even_fresh_session(tmp_path: Path, project: bool) -> None:
    root, directory = _session(tmp_path, project=project)
    result = scratch.sweep_sessions(root, apply=True, probe=lambda: DEAD)
    assert not directory.exists()
    assert result["summary"]["removed"] == 1
    assert result["summary"]["bytes_freed"] == 17
    assert result["entries"][0]["reason"] == "process_gone"


def test_live_session_kept_despite_rollover_and_age(tmp_path: Path) -> None:
    root, directory = _session(tmp_path)
    os.utime(directory, (1, 1))
    rollover = _confirmed(tmp_path)
    result = scratch.sweep_sessions(root, rollover_roots=[rollover], apply=True, probe=lambda: LIVE)
    assert directory.exists()
    assert result["summary"]["kept_by_reason"] == {"live_session": 1}


def test_confirmed_rollover_cannot_override_unknown_pid_view(tmp_path: Path) -> None:
    root, directory = _session(tmp_path)
    rollover = _confirmed(tmp_path)
    result = scratch.sweep_sessions(root, rollover_roots=[rollover], apply=True, probe=lambda: UNKNOWN)
    assert directory.exists()
    assert result["entries"][0]["reason"] == "unknown_session"


def test_confirmed_ended_session_removed_with_complete_registry(tmp_path: Path) -> None:
    root, directory = _session(tmp_path)
    result = scratch.sweep_sessions(root, rollover_roots=[_confirmed(tmp_path)], apply=True, probe=lambda: DEAD)
    assert not directory.exists()
    assert result["entries"][0]["reason"] == "confirmed_rollover"


def test_unknown_kept_regardless_of_age(tmp_path: Path) -> None:
    root, directory = _session(tmp_path)
    os.utime(directory, (1, 1))
    result = scratch.sweep_sessions(root, apply=True, probe=lambda: UNKNOWN)
    assert (directory / "scratchpad/payload").read_bytes() == b"keep every byte\x00\xff"
    assert result["summary"]["kept_by_reason"] == {"unknown_session": 1}


def test_dry_run_byte_for_byte_unchanged(tmp_path: Path) -> None:
    root, directory = _session(tmp_path)

    def snapshot() -> dict:
        return {
            str(path.relative_to(root)): (
                path.stat().st_mtime_ns,
                path.stat().st_mode,
                path.read_bytes() if path.is_file() else None,
            )
            for path in [root, *root.rglob("*")]
        }

    before = snapshot()
    result = scratch.sweep_sessions(root, rollover_roots=[_confirmed(tmp_path)], probe=lambda: DEAD)
    assert result["summary"]["would_remove"] == 1
    assert result["summary"]["bytes_freed"] == 0
    assert snapshot() == before
    assert directory.exists()


def test_symlinks_at_root_project_session_and_inside_not_followed(tmp_path: Path) -> None:
    root, directory = _session(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious").write_bytes(b"outside")
    (directory / "link").symlink_to(outside, target_is_directory=True)
    (root / REPLACEMENT).symlink_to(outside, target_is_directory=True)
    (root / "linked-project").symlink_to(outside, target_is_directory=True)
    (root / "project" / REPLACEMENT).symlink_to(outside, target_is_directory=True)
    report = scratch.sweep_sessions(root, apply=True, probe=lambda: DEAD)
    assert report["summary"]["removed"] == 1
    assert report["summary"]["kept_by_reason"] == {"symlink": 3}
    assert (outside / "precious").read_bytes() == b"outside"
    linked_root = tmp_path / "linked" / root.name
    linked_root.parent.mkdir()
    linked_root.symlink_to(root, target_is_directory=True)
    assert scratch.sweep_sessions(linked_root, apply=True, probe=lambda: DEAD)["summary"]["errors"] == 1
    ancestor = tmp_path / "linked-ancestor"
    ancestor.symlink_to(root.parent, target_is_directory=True)
    assert scratch.sweep_sessions(ancestor / root.name, apply=True, probe=lambda: DEAD)["summary"]["errors"] == 1


def test_apply_rechecks_process_ownership(tmp_path: Path) -> None:
    root, directory = _session(tmp_path)
    scans = iter([DEAD, LIVE])
    result = scratch.sweep_sessions(root, apply=True, probe=lambda: next(scans))
    assert directory.exists()
    assert result["summary"]["kept_by_reason"] == {"live_session": 1}


def test_apply_rejects_directory_swap(tmp_path: Path) -> None:
    root, directory = _session(tmp_path)
    calls = 0

    def probe() -> scratch.ProcessEvidence:
        nonlocal calls
        calls += 1
        if calls == 2:
            directory.rename(tmp_path / "original")
            directory.mkdir()
            (directory / "new-session").write_bytes(b"keep")
        return DEAD

    result = scratch.sweep_sessions(root, apply=True, probe=probe)
    assert result["summary"]["kept_by_reason"] == {"entry_changed": 1}
    assert (directory / "new-session").read_bytes() == b"keep"


def test_one_entry_error_does_not_abort(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, bad = _session(tmp_path)
    _, good = _session(tmp_path, session=REPLACEMENT)
    real = scratch.shutil.rmtree

    def remove(name, *, dir_fd):
        if name == SESSION:
            raise PermissionError(errno.EACCES, "inaccessible")
        real(name, dir_fd=dir_fd)

    monkeypatch.setattr(scratch.shutil, "rmtree", remove)
    remove.avoids_symlink_attacks = True
    result = scratch.sweep_sessions(root, apply=True, probe=lambda: DEAD)
    assert bad.exists() and not good.exists()
    assert result["summary"]["errors"] == result["summary"]["removed"] == 1
    assert result["entries"][0]["reason"] == "EACCES"


def test_unknown_names_foreign_owner_and_unsafe_platform_kept(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, directory = _session(tmp_path)
    (root / "project" / "unidentified").mkdir()
    monkeypatch.setattr(scratch.shutil.rmtree, "avoids_symlink_attacks", False)
    report = scratch.sweep_sessions(root, apply=True, probe=lambda: DEAD)
    assert report["summary"]["kept_by_reason"] == {"unknown_entry": 1, "unsafe_platform": 1}
    assert directory.exists()
    # Synthetic ownership proof: don't chown files on the host in a test.
    real_stat = scratch.os.stat

    def foreign(name, **kwargs):
        info = real_stat(name, **kwargs)
        if name == SESSION:
            values = list(info)
            values[4] = os.getuid() + 1
            return os.stat_result(values)
        return info

    monkeypatch.setattr(scratch.os, "stat", foreign)
    report = scratch.sweep_sessions(root, apply=True, probe=lambda: DEAD)
    assert report["summary"]["kept_by_reason"]["foreign_owner"] == 1


@pytest.mark.parametrize("field", ["status", "identity", "canary_proof", "strict_verdict", "confirmed_at", "thread_id"])
def test_incomplete_rollover_is_not_confirmation(tmp_path: Path, field: str) -> None:
    root = _confirmed(tmp_path)
    lease = root / "lineage/lease.json"
    record = json.loads(lease.read_text())
    del record["replacement"][field]
    lease.write_text(json.dumps(record))
    assert scratch.confirmed_sessions([root]) == set()


def test_rollover_symlink_malformed_and_missing_records_ignored(tmp_path: Path) -> None:
    root = _confirmed(tmp_path)
    assert scratch.confirmed_sessions([root]) == {SESSION}
    (root / "lineage/lease.json").write_text("{")
    (root / "bad").mkdir()
    (root / "bad/lease.json").symlink_to(tmp_path / "absent")
    (root / "linked").symlink_to(root / "lineage", target_is_directory=True)
    assert scratch.confirmed_sessions([root, tmp_path / "absent"]) == set()


class FakeProcess:
    def __init__(
        self, *, args=None, env=None, uid=None, error=None, paths=(), status="running", pid=999, exe="/bin/other"
    ):
        self.args = args or ["other"]
        self.env = env or {}
        self.uid = os.getuid() if uid is None else uid
        self.error = error
        self.paths = paths
        self.state = status
        self.pid = pid
        self.executable = exe

    def uids(self):
        if self.error:
            raise self.error
        return SimpleNamespace(real=self.uid)

    def status(self):
        return self.state

    def exe(self):
        return self.executable

    def cmdline(self):
        return self.args

    def environ(self):
        return self.env

    def cwd(self):
        return "/"

    def open_files(self):
        return [SimpleNamespace(path=path) for path in self.paths]


@pytest.fixture
def registry(tmp_path, monkeypatch):
    config = tmp_path / "config"
    root = config / "sessions"
    root.mkdir(parents=True)
    (root / "123.json").write_text(
        json.dumps(
            {
                "pid": 123,
                "sessionId": SESSION,
                "procStart": "100",
                "pidDomain": "linux:test:pid:[1]",
            }
        )
    )
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config))
    monkeypatch.setattr(scratch, "_pid_domain", lambda: "linux:test:pid:[1]")

    def gone(_pid):
        raise FileNotFoundError

    monkeypatch.setattr(scratch, "_kernel_start", gone)
    return root


@pytest.mark.parametrize(
    "process,complete,live",
    [
        (FakeProcess(args=["claude", "--session-id", SESSION]), False, {SESSION}),
        (FakeProcess(args=["claude", f"--resume={SESSION}"]), False, {SESSION}),
        (FakeProcess(args=["claude"], env={"CLAUDE_SESSION_ID": SESSION}), False, {SESSION}),
        (FakeProcess(args=["claude"], env={"CLAUDE_CODE_SESSION_ID": SESSION}), False, {SESSION}),
        (FakeProcess(args=["claude"], paths=[f"/tmp/claude-{os.getuid()}/project/{SESSION}/file"]), False, {SESSION}),
        (FakeProcess(args=["claude"], env={"RANDOM_UUID": SESSION}), False, {SESSION}),
        (FakeProcess(args=["claude"]), False, set()),
        (FakeProcess(args=["node", "/package/claude-code/cli.js"]), False, set()),
        (FakeProcess(exe="/bin/nodejs", args=["renamed", "/package/@anthropic-ai/claude-code/cli.js"]), False, set()),
        (FakeProcess(exe="/install/claude/versions/2.1.0", args=["2.1.0", "-p"]), False, set()),
        (FakeProcess(args=["/install/claude/versions/2.1.0", "-p"]), False, set()),
        (FakeProcess(args=["bash", "/package/claude-code/cli.js"]), True, set()),
        (FakeProcess(args=["node", "/package/other/cli.js", "/package/claude-code/cli.js"]), True, set()),
        (FakeProcess(args=["node", "/package/claude-code/not-cli.js"]), True, set()),
        (FakeProcess(args=["bash", "/install/claude/versions/2.1.0"]), True, set()),
        (FakeProcess(exe="/install/other/versions/2.1.0", args=["2.1.0"]), True, set()),
        (FakeProcess(args=["bash", "/worktrees/claude/task"]), True, set()),
        (FakeProcess(exe="/bin/claude", args=["renamed"]), False, set()),
        (FakeProcess(error=scratch.psutil.AccessDenied(1)), True, set()),
        (FakeProcess(args=["claude"], error=scratch.psutil.AccessDenied(1)), False, set()),
        (FakeProcess(error=scratch.psutil.NoSuchProcess(1)), True, set()),
        (FakeProcess(uid=os.getuid() + 1), True, set()),
        (FakeProcess(status=scratch.psutil.STATUS_ZOMBIE), True, set()),
    ],
)
def test_process_scan_proves_positive_ownership_and_fails_closed(
    registry, monkeypatch, process, complete, live
) -> None:
    monkeypatch.setattr(scratch.psutil, "process_iter", lambda: iter([process]))
    assert scratch.process_evidence() == scratch.ProcessEvidence(frozenset(live), complete)


def test_process_enumeration_failure_is_unknown(registry, monkeypatch) -> None:
    def fail():
        raise OSError(errno.EACCES, "inaccessible")

    monkeypatch.setattr(scratch.psutil, "process_iter", fail)
    assert scratch.process_evidence() == UNKNOWN


@pytest.mark.parametrize(
    "process",
    [
        FakeProcess(exe="/install/claude/versions/2.1.0", args=["2.1.0", "-p"]),
        FakeProcess(exe="/bin/node", args=["node", "/package/@anthropic-ai/claude-code/cli.js", "-p"]),
    ],
)
def test_unregistered_native_or_node_claude_preserves_scratch(registry, tmp_path, monkeypatch, process) -> None:
    monkeypatch.setattr(scratch.psutil, "process_iter", lambda: iter([process]))
    root, directory = _session(tmp_path)
    report = scratch.sweep_sessions(root, apply=True)
    assert report["summary"]["kept_by_reason"] == {"unknown_session": 1}
    assert report["summary"]["removed"] == report["summary"]["would_remove"] == 0
    assert (directory / "scratchpad/payload").read_bytes() == b"keep every byte\x00\xff"


def test_registered_version_named_claude_still_proves_liveness(registry, monkeypatch) -> None:
    process = FakeProcess(pid=123, exe="/install/claude/versions/2.1.0", args=["2.1.0", "-p"])
    monkeypatch.setattr(scratch, "_kernel_start", lambda _pid: "100")
    monkeypatch.setattr(scratch.psutil, "process_iter", lambda: iter([process]))
    assert scratch.process_evidence() == LIVE


@pytest.mark.parametrize(
    "payload", [b"[" * 10000 + b"]" * 10000, b"{", b"\xff"], ids=["deeply_nested", "malformed", "invalid_unicode"]
)
def test_registry_parse_failure_preserves_scratch(registry, tmp_path, monkeypatch, payload) -> None:
    (registry / "123.json").write_bytes(payload)
    monkeypatch.setattr(scratch.psutil, "process_iter", lambda: iter([]))
    root, directory = _session(tmp_path)
    report = scratch.sweep_sessions(root, apply=True)
    assert report["summary"]["kept_by_reason"] == {"unknown_session": 1}
    assert report["summary"]["removed"] == report["summary"]["would_remove"] == 0
    assert (directory / "scratchpad/payload").read_bytes() == b"keep every byte\x00\xff"


@pytest.mark.parametrize(
    "payload,reason",
    [
        (b"[" * 10000 + b"]" * 10000, "RecursionError"),
        (b"{", "JSONDecodeError"),
        (b"\xff", "UnicodeDecodeError"),
    ],
    ids=["deeply_nested", "malformed", "invalid_unicode"],
)
@pytest.mark.parametrize("evidence,kept_reason", [(DEAD, "unknown_session"), (LIVE, "live_session")])
def test_lease_parse_failure_is_recorded_and_preserves_scratch(
    tmp_path, payload, reason, evidence, kept_reason
) -> None:
    rollover = _confirmed(tmp_path)
    (rollover / "lineage/lease.json").write_bytes(payload)
    root, directory = _session(tmp_path)
    report = scratch.sweep_sessions(root, rollover_roots=[rollover], apply=True, probe=lambda: evidence)
    assert report["summary"]["errors"] == 1
    assert report["entries"][0]["reason"] == f"unreadable_lease_{reason}"
    assert report["summary"]["kept_by_reason"] == {kept_reason: 1}
    assert report["summary"]["removed"] == report["summary"]["would_remove"] == 0
    assert (directory / "scratchpad/payload").read_bytes() == b"keep every byte\x00\xff"


def test_partial_process_probe_keeps_positive_ownership(registry, monkeypatch) -> None:
    process = FakeProcess(args=["claude", "--session-id", SESSION])

    def inaccessible():
        raise scratch.psutil.AccessDenied(1)

    monkeypatch.setattr(process, "environ", inaccessible)
    monkeypatch.setattr(scratch.psutil, "process_iter", lambda: iter([process]))
    assert scratch.process_evidence() == scratch.ProcessEvidence(frozenset({SESSION}), complete=False)


def test_narrowed_enumeration_keeps_registry_session_with_renamed_binary(registry, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(scratch, "_kernel_start", lambda _pid: "100")
    monkeypatch.setattr(scratch.psutil, "process_iter", lambda: iter([]))
    root, directory = _session(tmp_path)
    result = scratch.sweep_sessions(root)
    assert directory.exists()
    assert result["summary"]["kept_by_reason"] == {"live_session": 1}
    assert scratch.process_evidence() == LIVE


def test_mismatched_pid_domain_refuses_absence_even_with_rollover(registry, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(scratch, "_pid_domain", lambda: "linux:test:pid:[2]")
    monkeypatch.setattr(scratch.psutil, "process_iter", lambda: iter([]))
    root, directory = _session(tmp_path)
    result = scratch.sweep_sessions(root, rollover_roots=[_confirmed(tmp_path)])
    assert directory.exists()
    assert result["summary"]["kept_by_reason"] == {"unknown_session": 1}
    assert scratch.process_evidence() == UNKNOWN


def test_pid_reuse_with_different_start_is_not_live(registry, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(scratch, "_kernel_start", lambda _pid: "200")
    monkeypatch.setattr(scratch.psutil, "process_iter", lambda: iter([FakeProcess(pid=123)]))
    root, directory = _session(tmp_path)
    result = scratch.sweep_sessions(root)
    assert directory.exists()  # Dry-run only.
    assert result["entries"][0]["reason"] == "process_gone"
    assert result["summary"]["would_remove"] == 1


def test_pid_reuse_as_unregistered_claude_blocks(registry, monkeypatch) -> None:
    monkeypatch.setattr(scratch, "_kernel_start", lambda _pid: "200")
    monkeypatch.setattr(scratch.psutil, "process_iter", lambda: iter([FakeProcess(pid=123, args=["claude"])]))
    assert scratch.process_evidence() == UNKNOWN


@pytest.mark.parametrize("accessor", ["environ", "cmdline", "exe", "cwd", "open_files"])
def test_unrelated_access_denied_does_not_block_absence(registry, monkeypatch, accessor) -> None:
    process = FakeProcess()

    def denied():
        raise scratch.psutil.AccessDenied(999)

    monkeypatch.setattr(process, accessor, denied)
    monkeypatch.setattr(scratch.psutil, "process_iter", lambda: iter([process]))
    assert scratch.process_evidence() == DEAD


def test_registered_claude_without_id_or_environment_is_complete(registry, monkeypatch) -> None:
    process = FakeProcess(pid=123, args=["claude"])

    def denied():
        raise scratch.psutil.AccessDenied(123)

    monkeypatch.setattr(process, "environ", denied)
    monkeypatch.setattr(scratch, "_kernel_start", lambda _pid: "100")
    monkeypatch.setattr(scratch.psutil, "process_iter", lambda: iter([process]))
    assert scratch.process_evidence() == LIVE


@pytest.mark.parametrize("kind", ["missing", "empty", "malformed", "symlink", "inaccessible", "foreign_owner"])
def test_unverified_registry_refuses_absence(registry, monkeypatch, kind) -> None:
    record = registry / "123.json"
    if kind == "missing":
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(registry / "absent"))
    elif kind == "empty":
        record.unlink()
    elif kind == "malformed":
        record.write_text("{")
    elif kind == "symlink":
        saved = registry.parent / "saved.json"
        record.rename(saved)
        record.symlink_to(saved)
    elif kind == "inaccessible":

        def denied(_pid):
            raise PermissionError(errno.EACCES, "denied")

        monkeypatch.setattr(scratch, "_kernel_start", denied)
    else:
        real_fstat = scratch.os.fstat

        def foreign(fd):
            info = real_fstat(fd)
            if stat.S_ISREG(info.st_mode):
                values = list(info)
                values[4] = os.getuid() + 1
                return os.stat_result(values)
            return info

        monkeypatch.setattr(scratch.os, "fstat", foreign)
    monkeypatch.setattr(scratch.psutil, "process_iter", lambda: iter([]))
    assert scratch.process_evidence() == UNKNOWN


def test_kernel_start_reads_ticks_with_parentheses_in_comm(tmp_path, monkeypatch) -> None:
    sample = tmp_path / "stat"
    sample.write_text("123 (odd ) process) S " + "0 " * 18 + "100 0 0")
    monkeypatch.setattr(scratch, "Path", lambda _path: sample)
    assert scratch._kernel_start(123) == "100"


def test_pid_domain_matches_registry_format(tmp_path, monkeypatch) -> None:
    machine = tmp_path / "machine-id"
    machine.write_text("a" * 32 + "\n")
    monkeypatch.setattr(scratch, "Path", lambda _path: machine)
    monkeypatch.setattr(scratch.os, "readlink", lambda _path: "pid:[123]")
    assert scratch._pid_domain() == "linux:" + "a" * 32 + ":pid:[123]"
    machine.write_text("")
    with pytest.raises(ValueError, match="unknown PID domain"):
        scratch._pid_domain()


def test_deep_tree_error_does_not_abort_other_entries(tmp_path) -> None:
    root, deep = _session(tmp_path)
    _session(tmp_path, session=REPLACEMENT)
    nested = deep
    for _ in range(130):
        nested /= "d"
        nested.mkdir()
    report = scratch.sweep_sessions(root, probe=lambda: DEAD)
    assert report["summary"]["errors"] == report["summary"]["would_remove"] == 1
    assert report["entries"][0]["reason"] == "ELOOP"
    assert deep.exists()


def test_recursion_error_is_per_entry(tmp_path, monkeypatch) -> None:
    root, directory = _session(tmp_path)

    def fail(_fd):
        raise RecursionError

    monkeypatch.setattr(scratch, "_tree_bytes", fail)
    report = scratch.sweep_sessions(root, probe=lambda: DEAD)
    assert report["summary"]["errors"] == 1
    assert report["entries"][0]["reason"] == "RecursionError"
    assert directory.exists()


def test_cli_counts_only_and_error_exit(registry, tmp_path: Path, monkeypatch, capsys) -> None:
    root, directory = _session(tmp_path)
    monkeypatch.setattr(scratch.psutil, "process_iter", lambda: iter([]))
    assert scratch.main(["--temp-root", str(root)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["would_remove"] == 1
    assert str(directory) not in json.dumps(report) and SESSION not in json.dumps(report)
    assert scratch.main(["--temp-root", str(root), "--apply"]) == 0
    assert not directory.exists()
    assert scratch.main(["--temp-root", str(tmp_path)]) == 1
    assert scratch.sweep_sessions(tmp_path / "missing", probe=lambda: DEAD)["summary"]["errors"] == 0
    help_result = subprocess.run(
        [sys.executable, "-m", "scripts.maintenance.claude_session_scratch", "--help"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert all(text in help_result.stdout for text in ["Examples:", "Outputs:", "Exit codes:", "Related:", "--apply"])
