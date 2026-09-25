"""Tests for ad-hoc /tmp leak sweep (# disk pressure)."""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import pytest

from scripts.orchestration import tmp_leak_sweep as tls


def _touch_old(path: Path, *, age_s: float, as_file: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if as_file or path.suffix:
        path.write_text("x", encoding="utf-8")
    else:
        path.mkdir(parents=True, exist_ok=True)
        (path / "marker").write_text("x", encoding="utf-8")
    past = time.time() - age_s
    os.utime(path, (past, past))


def test_name_patterns_match_known_leaks() -> None:
    assert tls.name_matches_leak_pattern("review-6621")
    assert tls.name_matches_leak_pattern("pr6591-exact-ujs9Ng")
    assert tls.name_matches_leak_pattern("lu-agent-runtime-git")
    assert tls.name_matches_leak_pattern("data_test_pipe3")
    assert tls.name_matches_leak_pattern("atlas6507-build.DnfqH3")
    assert tls.name_matches_leak_pattern("mq-runner-log-123")
    assert tls.name_matches_leak_pattern("contracts-job-scratch-456")
    assert tls.name_matches_leak_pattern("learn-ukrainian-bridge-asks")
    assert tls.name_matches_leak_pattern("learn-ukrainian-something")
    assert not tls.name_matches_leak_pattern("com.apple.imagent")
    assert not tls.name_matches_leak_pattern("claude-501")
    assert not tls.name_matches_leak_pattern("cc-socks")
    assert not tls.name_matches_leak_pattern("random-scratch")


def test_default_tmp_roots_includes_scratch_and_base_override(tmp_path: Path, monkeypatch) -> None:
    scratch_root = tmp_path / "scratch"
    scratch_root.mkdir()
    base_root = tmp_path / "base"
    base_root.mkdir()

    monkeypatch.setenv("LU_SCRATCH_ROOT", str(scratch_root))
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(base_root))

    roots = tls.default_tmp_roots()
    resolved_roots = [r.resolve() for r in roots]
    assert scratch_root.resolve() in resolved_roots
    assert base_root.resolve() in resolved_roots


def test_discover_skips_young_and_unrelated(tmp_path: Path) -> None:
    old = tmp_path / "review-1001"
    young = tmp_path / "review-1002"
    safe = tmp_path / "com.apple.foo"
    _touch_old(old, age_s=10_000)
    _touch_old(young, age_s=30)
    _touch_old(safe, age_s=10_000)

    found = tls.discover_candidates([tmp_path], now=time.time(), min_age_s=3600)
    names = {c.path.name for c in found}
    assert "review-1001" in names
    assert "review-1002" not in names
    assert "com.apple.foo" not in names


def test_dry_run_does_not_delete(tmp_path: Path, monkeypatch) -> None:
    _clear_proc_probe(monkeypatch)
    target = tmp_path / "pr6568"
    _touch_old(target, age_s=10_000)
    real_run = tls.subprocess.run

    def fake_run(cmd, *args, **kwargs):
        if cmd[0] == "pgrep":
            return tls.subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(tls.subprocess, "run", fake_run)
    report = tls.sweep_tmp_leaks(
        apply=False,
        tmp_roots=[tmp_path],
        now=time.time(),
        min_age_s=3600,
        min_free_gb=0.0,  # force non-pressure ages via min_age_s
    )
    assert report["candidates"] >= 1
    assert report["roots_reaped"] == 0
    assert target.exists()
    assert any(item["action"] == "would_reap" for item in report["reaped"])


def test_apply_reaps_old_candidate(tmp_path: Path, monkeypatch) -> None:
    _clear_proc_probe(monkeypatch)
    target = tmp_path / "review-2002"
    _touch_old(target, age_s=10_000)
    real_run = tls.subprocess.run

    def fake_run(cmd, *args, **kwargs):
        if cmd[0] == "pgrep":
            return tls.subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(tls.subprocess, "run", fake_run)
    report = tls.sweep_tmp_leaks(
        apply=True,
        tmp_roots=[tmp_path],
        now=time.time(),
        min_age_s=3600,
        min_free_gb=0.0,
    )
    assert report["roots_reaped"] == 1
    assert not target.exists()
    assert report["bytes_freed"] > 0


def test_path_has_live_process_matching_and_nonmatching(tmp_path: Path, monkeypatch) -> None:
    _clear_proc_probe(monkeypatch)
    target = tmp_path / "review-process-check"

    # returncode == 0 means matching process found -> True
    monkeypatch.setattr(
        tls.subprocess,
        "run",
        lambda *args, **kwargs: tls.subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=b"1234\n", stderr=b""
        ),
    )
    assert tls.path_has_live_process(target) is True

    # returncode == 1 means proven no-match -> False
    monkeypatch.setattr(
        tls.subprocess,
        "run",
        lambda *args, **kwargs: tls.subprocess.CompletedProcess(args=args[0], returncode=1, stdout=b"", stderr=b""),
    )
    assert tls.path_has_live_process(target) is False


def test_path_has_live_process_rc3_fails_closed(tmp_path: Path, monkeypatch) -> None:
    """pgrep exit code 3 (fatal error) must fail closed as live (rc 1 is only non-live rc)."""
    target = tmp_path / "review-rc3-check"
    monkeypatch.setattr(
        tls.subprocess,
        "run",
        lambda *args, **kwargs: tls.subprocess.CompletedProcess(
            args=args[0], returncode=3, stdout=b"", stderr=b"pgrep: fatal error\n"
        ),
    )
    assert tls.path_has_live_process(target) is True


def test_path_has_live_process_fails_closed_on_exceptions(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "review-fail-closed"

    def raise_timeout(*args, **kwargs):
        raise tls.subprocess.TimeoutExpired(cmd="pgrep", timeout=5)

    monkeypatch.setattr(tls.subprocess, "run", raise_timeout)
    assert tls.path_has_live_process(target) is True

    def raise_fnf(*args, **kwargs):
        raise FileNotFoundError("pgrep not found")

    monkeypatch.setattr(tls.subprocess, "run", raise_fnf)
    assert tls.path_has_live_process(target) is True

    def raise_oserror(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(tls.subprocess, "run", raise_oserror)
    assert tls.path_has_live_process(target) is True


def test_live_process_is_skipped_via_pgrep(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "review-3003"
    _touch_old(target, age_s=10_000)
    # pgrep finds a process
    monkeypatch.setattr(
        tls.subprocess,
        "run",
        lambda *args, **kwargs: tls.subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=b"9999\n", stderr=b""
        ),
    )
    report = tls.sweep_tmp_leaks(
        apply=True,
        tmp_roots=[tmp_path],
        now=time.time(),
        min_age_s=3600,
        min_free_gb=0.0,
    )
    assert report["roots_reaped"] == 0
    assert report["skipped_live"] == 1
    assert target.exists()


def test_live_process_skipped_on_pgrep_timeout_fail_closed(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "review-3004"
    _touch_old(target, age_s=10_000)

    def raise_timeout(*args, **kwargs):
        raise tls.subprocess.TimeoutExpired(cmd="pgrep", timeout=5)

    monkeypatch.setattr(tls.subprocess, "run", raise_timeout)
    report = tls.sweep_tmp_leaks(
        apply=True,
        tmp_roots=[tmp_path],
        now=time.time(),
        min_age_s=3600,
        min_free_gb=0.0,
    )
    assert report["roots_reaped"] == 0
    assert report["skipped_live"] == 1
    assert target.exists()


def test_recheck_liveness_immediately_before_deletion(tmp_path: Path, monkeypatch) -> None:
    _clear_proc_probe(monkeypatch)
    target = tmp_path / "review-3005"
    _touch_old(target, age_s=10_000)

    pgrep_call_count = 0
    real_run = tls.subprocess.run

    def fake_run(cmd, *args, **kwargs):
        nonlocal pgrep_call_count
        if cmd[0] == "pgrep":
            pgrep_call_count += 1
            # First pgrep call during candidate loop: dead (rc=1)
            # Second pgrep call immediately before deletion: live (rc=0)
            if pgrep_call_count == 1:
                return tls.subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="")
            return tls.subprocess.CompletedProcess(args=cmd, returncode=0, stdout="8888\n", stderr="")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(tls.subprocess, "run", fake_run)
    report = tls.sweep_tmp_leaks(
        apply=True,
        tmp_roots=[tmp_path],
        now=time.time(),
        min_age_s=3600,
        min_free_gb=0.0,
    )
    assert report["roots_reaped"] == 0
    assert report["skipped_live"] == 1
    assert target.exists()
    assert pgrep_call_count == 2


def test_pressure_shortens_age(tmp_path: Path, monkeypatch) -> None:
    """Under free-space pressure, 45-minute-old leak is eligible."""
    target = tmp_path / "pr7001-exact-abc"
    _touch_old(target, age_s=45 * 60)
    monkeypatch.setattr(tls, "free_space_gb", lambda _path: 5.0)
    found = tls.discover_candidates(
        [tmp_path],
        now=time.time(),
        min_age_s=tls.DEFAULT_PRESSURE_MIN_AGE_S,
    )
    assert any(c.path.name == "pr7001-exact-abc" for c in found)


# --------------------------------------------------------------------------
# #8738: Atlas/QA legacy residue, managed-namespace exclusion, /proc probe
# --------------------------------------------------------------------------


def _quiet_pgrep(monkeypatch) -> None:
    real_run = tls.subprocess.run

    def fake_run(cmd, *args, **kwargs):
        if cmd[0] == "pgrep":
            return tls.subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(tls.subprocess, "run", fake_run)


def _clear_proc_probe(monkeypatch) -> None:
    """Sweep-logic tests assert on deletion policy, not on this host's ``/proc``.

    A real host usually has a non-dumpable same-uid daemon (``systemd --user``,
    ``ssh-agent``), which the fail-closed probe rightly reports as unknown.
    """
    monkeypatch.setattr(tls, "proc_references", lambda _p, **_kw: False)


def test_classify_candidate_name_orders_protected_exact_inventory_pattern() -> None:
    for name in sorted(tls.LEGACY_EXACT_ALLOWLIST):
        assert tls.classify_candidate_name(name) == tls.CANDIDATE_KIND_LEGACY_EXACT
    assert {
        "atlas-8307-410k-final.db",
        "atlas-8307-410k-r2.db",
        "atlas-8307-synthetic-410k.json",
        "qa-8686-ui-r2",
        "qa-8686-exercises-r2",
    } == tls.LEGACY_EXACT_ALLOWLIST
    assert tls.classify_candidate_name("atlas-8672-ci-pytest3.log") == tls.CANDIDATE_KIND_LEGACY_INVENTORY
    assert tls.classify_candidate_name("qa-8686-ui-r3") == tls.CANDIDATE_KIND_LEGACY_INVENTORY
    assert tls.classify_candidate_name("atlas-8307-410k-final.db.bak") == tls.CANDIDATE_KIND_LEGACY_INVENTORY
    assert tls.classify_candidate_name("review-6621") == tls.CANDIDATE_KIND_PATTERN
    assert tls.classify_candidate_name("atlas-8307-promotion-plan.md") is None
    assert tls.classify_candidate_name("atlas-8307-decision.yaml") is None
    assert tls.classify_candidate_name("qa-1.decision.yml") is None
    assert tls.classify_candidate_name(tls.NAMESPACE_DIRNAME) is None
    assert tls.classify_candidate_name("atlas-consult") is None  # no issue number: not a known family
    assert tls.classify_candidate_name("com.apple.imagent") is None


def test_legacy_exact_names_drain_but_other_atlas_qa_residue_is_inventory_only(tmp_path: Path, monkeypatch) -> None:
    _quiet_pgrep(monkeypatch)
    _clear_proc_probe(monkeypatch)
    exact_db = tmp_path / "atlas-8307-410k-final.db"
    exact_json = tmp_path / "atlas-8307-synthetic-410k.json"
    exact_qa = tmp_path / "qa-8686-ui-r2"
    other_atlas = tmp_path / "atlas-8672-ci-pytest3.log"
    other_qa = tmp_path / "qa-9999-scratch"
    promotion = tmp_path / "atlas-8307-promotion-plan.md"
    decision = tmp_path / "atlas-8307-decision.yaml"
    for target in (exact_db, exact_json, other_atlas, promotion, decision):
        _touch_old(target, age_s=10_000, as_file=True)
    for target in (exact_qa, other_qa):
        _touch_old(target, age_s=10_000)

    dry = tls.sweep_tmp_leaks(apply=False, tmp_roots=[tmp_path], now=time.time(), min_age_s=3600, min_free_gb=0.0)
    assert {item["path"] for item in dry["inventory"]} == {str(other_atlas), str(other_qa)}
    assert all(item["action"] == "inventory_only" for item in dry["inventory"])
    assert dry["inventory_only"] == 2
    assert {item["path"] for item in dry["reaped"]} == {str(exact_db), str(exact_json), str(exact_qa)}
    assert all(item["action"] == "would_reap" for item in dry["reaped"])
    assert dry["roots_reaped"] == 0
    reported = str(dry)
    assert str(promotion) not in reported and str(decision) not in reported

    applied = tls.sweep_tmp_leaks(apply=True, tmp_roots=[tmp_path], now=time.time(), min_age_s=3600, min_free_gb=0.0)
    assert applied["roots_reaped"] == 3
    assert applied["errors"] == 0
    assert not exact_db.exists() and not exact_json.exists() and not exact_qa.exists()
    assert other_atlas.exists() and other_qa.exists()
    assert promotion.exists() and decision.exists()
    assert applied["inventory_only"] == 2


def test_managed_namespace_and_scratch_roots_are_never_candidates(tmp_path: Path, monkeypatch) -> None:
    _quiet_pgrep(monkeypatch)
    _clear_proc_probe(monkeypatch)
    scratch_root = tmp_path / "scratch"
    scratch_root.mkdir()
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(scratch_root))
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path / "lu-base"))
    monkeypatch.setattr(tls.tempfile, "gettempdir", lambda: str(tmp_path))
    namespace = scratch_root / tls.NAMESPACE_DIRNAME
    _touch_old(namespace, age_s=10_000)
    fallback = tmp_path / "lu-scratch"  # matches ^lu- but is the fallback scratch root
    _touch_old(fallback, age_s=10_000)
    base = tmp_path / "lu-base"  # matches ^lu- but is the dispatcher base root
    _touch_old(base, age_s=10_000)
    residue = tmp_path / "lu-real-leak"
    _touch_old(residue, age_s=10_000)

    found = tls.discover_candidates([tmp_path, scratch_root], now=time.time(), min_age_s=3600)
    assert {c.path for c in found} == {residue}
    report = tls.sweep_tmp_leaks(
        apply=True, tmp_roots=[tmp_path, scratch_root], now=time.time(), min_age_s=3600, min_free_gb=0.0
    )
    assert report["roots_reaped"] == 1
    assert namespace.is_dir() and fallback.is_dir() and base.is_dir()
    assert not residue.exists()


def _fake_proc(
    tmp_path: Path,
    pid: int,
    *,
    cmdline: bytes = b"",
    cwd: Path | None = None,
    fd: Path | None = None,
    environ: bytes = b"",
    state: str = "S",
) -> Path:
    proc_root = tmp_path / "proc"
    entry = proc_root / str(pid)
    entry.mkdir(parents=True, exist_ok=True)
    (entry / "stat").write_text(
        f"{pid} (sleep) {state} 1 {pid} {pid} 0 -1 4194560 0 0 0 0 0 0 0 0 0 20 0 1 0 12345 0 0\n"
    )
    (entry / "cmdline").write_bytes(cmdline)
    (entry / "environ").write_bytes(environ)
    (entry / "cwd").symlink_to(cwd if cwd is not None else tmp_path)
    (entry / "fd").mkdir(exist_ok=True)
    if fd is not None:
        (entry / "fd" / "7").symlink_to(fd)
    return proc_root


def test_proc_probe_detects_cwd_fd_environ_and_cmdline(tmp_path: Path) -> None:
    target = tmp_path / "atlas-8307-410k-final.db"
    target.write_text("x")
    workdir = tmp_path / "qa-8686-ui-r2"
    (workdir / "inner").mkdir(parents=True)
    assert tls.proc_references(target, proc_root=tmp_path / "missing") is None

    proc_root = _fake_proc(tmp_path, 4001, cmdline=b"python\0--other\0")
    assert tls.proc_references(target, proc_root=proc_root) is False
    _fake_proc(tmp_path, 4002, cmdline=b"sqlite3\0" + str(target).encode() + b"\0")
    assert tls.proc_references(target, proc_root=proc_root) is True

    proc_root = _fake_proc(tmp_path / "cwd-case", 4003, cwd=workdir / "inner")
    assert tls.proc_references(workdir, proc_root=proc_root) is True
    proc_root = _fake_proc(tmp_path / "fd-case", 4004, fd=target)
    assert tls.proc_references(target, proc_root=proc_root) is True
    proc_root = _fake_proc(tmp_path / "env-case", 4005, environ=b"HOME=/x\0LU_DB=" + str(target).encode() + b"\0")
    assert tls.proc_references(target, proc_root=proc_root) is True
    proc_root = _fake_proc(tmp_path / "prefix-case", 4006, cmdline=b"cat\0" + str(target).encode() + b"-other\0")
    # Command lines match by substring on purpose (same conservatism as pgrep -f).
    assert tls.proc_references(target, proc_root=proc_root) is True
    proc_root = _fake_proc(tmp_path / "unrelated-case", 4007, cwd=tmp_path, fd=tmp_path / "elsewhere")
    assert tls.proc_references(target, proc_root=proc_root) is False


def test_proc_probe_unknown_when_same_uid_process_unreadable(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "qa-8686-exercises-r2"
    target.mkdir()
    proc_root = _fake_proc(tmp_path, 4010, cmdline=b"sleep\0")
    real_read_bytes = Path.read_bytes

    def flaky_read_bytes(self):
        if self.name == "environ":
            raise OSError(5, "input/output error")
        return real_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", flaky_read_bytes)
    assert tls.proc_references(target, proc_root=proc_root) is None

    def opaque_read_bytes(self):
        if self.name == "environ":
            raise PermissionError(13, "permission denied")
        return real_read_bytes(self)

    # EACCES/EPERM on a same-uid process is not "no reference": the process
    # may hold the path open, so the verdict is unknown (fail closed, #8738).
    monkeypatch.setattr(Path, "read_bytes", opaque_read_bytes)
    assert tls.proc_references(target, proc_root=proc_root) is None


@pytest.mark.parametrize("errno_value", [13, 1])
def test_proc_probe_unknown_when_same_uid_cwd_or_fd_table_denied(tmp_path: Path, monkeypatch, errno_value: int) -> None:
    target = tmp_path / "atlas-8307-410k-final.db"
    target.write_text("x")
    proc_root = _fake_proc(tmp_path, 4011, cmdline=b"sleep\0")
    real_readlink = os.readlink

    def denied_cwd(path, *args, **kwargs):
        if str(path).endswith("/cwd"):
            raise PermissionError(errno_value, "denied")
        return real_readlink(path, *args, **kwargs)

    monkeypatch.setattr(tls.os, "readlink", denied_cwd)
    assert tls.proc_references(target, proc_root=proc_root) is None
    monkeypatch.undo()

    proc_root = _fake_proc(tmp_path / "fd-denied", 4012, cmdline=b"sleep\0")
    real_iterdir = Path.iterdir

    def denied_fd_table(self):
        if self.name == "fd":
            raise PermissionError(errno_value, "denied")
        return real_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", denied_fd_table)
    assert tls.proc_references(target, proc_root=proc_root) is None


def test_proc_probe_unknown_when_a_descriptor_link_is_denied(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "qa-8686-ui-r2"
    target.mkdir()
    proc_root = _fake_proc(tmp_path, 4013, cmdline=b"sleep\0", fd=tmp_path / "elsewhere")
    real_readlink = os.readlink

    def denied_fd(path, *args, **kwargs):
        if "/fd/" in str(path):
            raise PermissionError(13, "denied")
        return real_readlink(path, *args, **kwargs)

    monkeypatch.setattr(tls.os, "readlink", denied_fd)
    assert tls.proc_references(target, proc_root=proc_root) is None


def _deny_probe(monkeypatch, *, names: tuple[str, ...]) -> None:
    """Make cwd/environ/fd reads of a fake process fail with EACCES, as a foreign-uid process does."""
    real_readlink = os.readlink
    real_read_bytes = Path.read_bytes
    real_iterdir = Path.iterdir

    def denied_readlink(path, *args, **kwargs):
        if Path(path).name in names:
            raise PermissionError(13, "denied")
        return real_readlink(path, *args, **kwargs)

    def denied_read_bytes(self):
        if self.name in names:
            raise PermissionError(13, "denied")
        return real_read_bytes(self)

    def denied_iterdir(self):
        if self.name in names:
            raise PermissionError(13, "denied")
        return real_iterdir(self)

    monkeypatch.setattr(tls.os, "readlink", denied_readlink)
    monkeypatch.setattr(Path, "read_bytes", denied_read_bytes)
    monkeypatch.setattr(Path, "iterdir", denied_iterdir)


def test_foreign_uid_process_cwd_and_fd_are_probed_and_denial_is_unknown(tmp_path: Path, monkeypatch) -> None:
    """A foreign-uid process may hold a world-readable legacy file open without naming it (#8738).

    Every fake process here is foreign: the sweeper's effective uid is shifted
    away from the uid that owns the fake ``/proc`` entries. Ownership must not
    change the probe, and a denied cwd/fd table is unknown, never absence.
    """
    monkeypatch.setattr(tls.os, "geteuid", lambda: os.getuid() + 1)
    target = tmp_path / "qa-8686-ui-r2"
    target.mkdir()

    proc_root = _fake_proc(tmp_path / "cwd", 4014, cmdline=b"sleep\0", cwd=target)
    assert tls.proc_references(target, proc_root=proc_root) is True
    proc_root = _fake_proc(tmp_path / "fd", 4015, cmdline=b"sleep\0", fd=target)
    assert tls.proc_references(target, proc_root=proc_root) is True
    proc_root = _fake_proc(tmp_path / "cmd", 4016, cmdline=b"sleep\0" + str(target).encode() + b"\0")
    assert tls.proc_references(target, proc_root=proc_root) is True
    proc_root = _fake_proc(tmp_path / "clean", 4017, cmdline=b"sleep\0", cwd=tmp_path, fd=tmp_path / "elsewhere")
    assert tls.proc_references(target, proc_root=proc_root) is False

    # The realistic foreign-uid shape on Linux: cmdline readable, cwd/environ/fd EACCES.
    proc_root = _fake_proc(tmp_path / "opaque", 4018, cmdline=b"sleep\0", cwd=target, fd=target)
    _deny_probe(monkeypatch, names=("cwd", "environ", "fd"))
    assert tls.proc_references(target, proc_root=proc_root) is None
    _quiet_pgrep(monkeypatch)
    assert tls.path_liveness(target, proc_root=proc_root) == tls.LIVENESS_UNKNOWN


@pytest.mark.parametrize("denied", [("cwd",), ("fd",)])
def test_foreign_uid_partial_denial_is_unknown(tmp_path: Path, monkeypatch, denied: tuple[str, ...]) -> None:
    monkeypatch.setattr(tls.os, "geteuid", lambda: os.getuid() + 1)
    target = tmp_path / "atlas-8307-410k-final.db"
    target.write_text("x")
    proc_root = _fake_proc(tmp_path, 4019, cmdline=b"sleep\0")
    _deny_probe(monkeypatch, names=denied)
    assert tls.proc_references(target, proc_root=proc_root) is None


def test_unreadable_stat_or_cmdline_is_unknown_unless_process_vanished(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "atlas-8307-410k-r2.db"
    target.write_text("x")
    proc_root = _fake_proc(tmp_path, 4020, cmdline=b"sleep\0")
    entry = proc_root / "4020"

    # Unreadable stat while /proc/<pid> still exists: unknown.
    _deny_probe(monkeypatch, names=("stat",))
    assert tls.proc_references(target, proc_root=proc_root) is None
    monkeypatch.undo()
    # Unreadable cmdline while /proc/<pid> still exists: unknown.
    _deny_probe(monkeypatch, names=("cmdline",))
    assert tls.proc_references(target, proc_root=proc_root) is None
    monkeypatch.undo()
    # Missing stat file while the directory exists is still not proof of exit.
    (entry / "stat").unlink()
    assert tls.proc_references(target, proc_root=proc_root) is None

    # The process exits between the directory listing and the probe: the
    # whole /proc/<pid> tree is gone, so it provably holds nothing.
    proc_root = _fake_proc(tmp_path / "vanish", 4021, cmdline=b"sleep\0")
    entry = proc_root / "4021"
    real_read_bytes = Path.read_bytes

    def vanish_on_stat(self):
        if self.name == "stat" and self.parent == entry:
            shutil.rmtree(entry)
            raise FileNotFoundError(2, "no such process")
        return real_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", vanish_on_stat)
    assert tls.proc_references(target, proc_root=proc_root) is False


def test_zombie_process_holds_nothing(tmp_path: Path) -> None:
    """A zombie has no cwd, no fd table and no environ; its state letter proves it holds nothing."""
    target = tmp_path / "qa-8686-exercises-r2"
    target.mkdir()
    proc_root = _fake_proc(tmp_path, 4022, cmdline=b"", state="Z")
    entry = proc_root / "4022"
    (entry / "cwd").unlink()  # readlink -> ENOENT, as on a real zombie
    (entry / "fd").chmod(0o000)
    try:
        assert tls.proc_references(target, proc_root=proc_root) is False
    finally:
        (entry / "fd").chmod(0o755)


def test_path_liveness_unknown_without_proc_and_negative_pgrep(tmp_path: Path, monkeypatch) -> None:
    """No /proc (macOS): a negative pgrep cannot see cwd or fd holders, so the verdict is unknown (#8738)."""
    _quiet_pgrep(monkeypatch)
    target = tmp_path / "atlas-8307-410k-final.db"
    _touch_old(target, age_s=10_000, as_file=True)
    missing_proc = tmp_path / "no-proc"
    assert not missing_proc.exists()
    assert tls.path_liveness(target, proc_root=missing_proc) == tls.LIVENESS_UNKNOWN

    monkeypatch.setattr(tls, "_PROC_ROOT", missing_proc)
    assert tls.path_liveness(target) == tls.LIVENESS_UNKNOWN
    for apply in (False, True):
        report = tls.sweep_tmp_leaks(
            apply=apply, tmp_roots=[tmp_path], now=time.time(), min_age_s=3600, min_free_gb=0.0
        )
        assert report["roots_reaped"] == 0
        assert report["reaped"] == []
        assert report["skipped"] == [{"path": str(target), "reason": "liveness_unknown"}]
    assert target.exists()


def test_unknown_liveness_is_reported_distinctly_and_preserves(tmp_path: Path, monkeypatch) -> None:
    _quiet_pgrep(monkeypatch)
    target = tmp_path / "atlas-8307-410k-r2.db"
    _touch_old(target, age_s=10_000, as_file=True)
    monkeypatch.setattr(tls, "proc_references", lambda _p, **_kw: None)
    monkeypatch.setattr(tls, "_PROC_ROOT", tmp_path / "proc-present")
    (tmp_path / "proc-present").mkdir()
    assert tls.path_liveness(target) == tls.LIVENESS_UNKNOWN
    report = tls.sweep_tmp_leaks(apply=True, tmp_roots=[tmp_path], now=time.time(), min_age_s=3600, min_free_gb=0.0)
    assert report["roots_reaped"] == 0
    assert report["skipped_live"] == 1
    assert report["skipped"] == [{"path": str(target), "reason": "liveness_unknown"}]
    assert target.exists()


def test_path_has_live_process_preserves_on_unknown_proc_verdict(tmp_path: Path, monkeypatch) -> None:
    _quiet_pgrep(monkeypatch)
    target = tmp_path / "review-unknown"
    monkeypatch.setattr(tls, "proc_references", lambda _p, **_kw: None)
    assert tls.path_has_live_process(target) is True  # unknown preserves on every host
    monkeypatch.setattr(tls, "proc_references", lambda _p, **_kw: True)
    assert tls.path_has_live_process(target) is True
    monkeypatch.setattr(tls, "proc_references", lambda _p, **_kw: False)
    assert tls.path_has_live_process(target) is False


def test_legacy_exact_name_held_open_is_preserved(tmp_path: Path, monkeypatch) -> None:
    _quiet_pgrep(monkeypatch)
    target = tmp_path / "atlas-8307-410k-r2.db"
    _touch_old(target, age_s=10_000, as_file=True)
    if not Path("/proc").is_dir():
        pytest.skip("open-file probe needs /proc")
    with target.open("rb") as handle:
        holder = tls.subprocess.Popen(["sleep", "30"], stdin=handle, stdout=tls.subprocess.DEVNULL)
    try:
        report = tls.sweep_tmp_leaks(apply=True, tmp_roots=[tmp_path], now=time.time(), min_age_s=3600, min_free_gb=0.0)
    finally:
        holder.kill()
        holder.wait()
    assert report["roots_reaped"] == 0
    assert report["skipped_live"] == 1
    assert target.exists()
