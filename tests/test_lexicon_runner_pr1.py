"""Tests for lexicon runner PR1 — engine isolation + bounded lookup rewrite."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from scripts.lexicon import enrich_manifest as em
from scripts.lexicon.runner.contracts import ChunkSpec, ChunkState, ErrorCode, OomSplitChildren
from scripts.lexicon.runner.generate_pr1_fixture import load_slovnyk_cache
from scripts.lexicon.runner.memory import (
    require_hard_cap_protection,
    run_startup_self_test,
)
from scripts.lexicon.runner.phase_cefr import (
    apply_sealed_cefr_to_engine_cache,
    load_sealed_cefr_map,
    sealed_cefr_precompute,
)
from scripts.lexicon.runner.phase_relations import (
    extract_and_close_relations,
    load_closed_relations_by_headword,
)
from scripts.lexicon.runner.side_db import (
    BallaReverseSideDb,
    DmklingerSideDb,
    KaikkiSideDb,
    build_balla_reverse_side_db,
    build_dmklinger_side_db,
    build_kaikki_side_db,
)
from scripts.lexicon.runner.split import child_chunk_id, split_on_oom
from scripts.lexicon.runner.stream_manifest import (
    StreamingCandidateWriter,
    stage_manifest_to_sqlite,
    stream_manifest_entries_json,
)
from scripts.lexicon.runner.worker import run_capped_worker
from tests.helpers.lexicon_runner_fixtures import lexicon_slovnyk_offline as lexicon_slovnyk_offline
from tests.helpers.lexicon_runner_fixtures import sources_slice

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "lexicon" / "runner_pr1"


@pytest.mark.parametrize("contents", [None, "{broken", "[]"])
def test_kaikki_side_db_refuses_unreadable_or_malformed_input(tmp_path: Path, contents: str | None) -> None:
    lookup = tmp_path / "kaikki.json"
    if contents is not None:
        lookup.write_text(contents, encoding="utf-8")
    output = tmp_path / "kaikki.sqlite"
    output.write_bytes(b"previous output")

    with pytest.raises(ValueError, match="hydrate --group lexicon_kaikki"):
        build_kaikki_side_db(lookup, output)

    assert output.read_bytes() == b"previous output"


@pytest.fixture(scope="module")
def fixture_paths(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    sources_dir = tmp_path_factory.mktemp("runner_pr1_sources")
    return {
        "input": FIXTURE / "slice_input.json",
        "sources": sources_slice(sources_dir),
        "grac": FIXTURE / "grac_frequency_slice.json",
        "kaikki": FIXTURE / "kaikki_slice.json",
        "baseline": FIXTURE / "baseline_enriched.json",
        "baseline_sha": FIXTURE / "baseline.sha256",
    }


def test_memory_self_test_refuses_unproven_hard_cap() -> None:
    """Production must refuse hard-cap claims when enforcement is unproven."""
    from scripts.lexicon.runner.memory import EnforcementProof

    bad = EnforcementProof(kind="none", enforced=False, detail="unavailable", max_bytes=1)
    with pytest.raises(RuntimeError, match="hard memory cap self-test failed"):
        require_hard_cap_protection(bad)
    # Live OS probe: ``python -m scripts.lexicon.runner.memory_probe`` (PR evidence).
    # Unit tests avoid spawning — pre-commit pipes pytest through ``tail`` and Darwin
    # can SIGSEGV on subprocess teardown after an otherwise-green run.


def test_classify_oom_exitcodes() -> None:
    from scripts.lexicon.runner.memory import classify_oom_exit

    assert classify_oom_exit(-9) is True
    assert classify_oom_exit(137) is True
    assert classify_oom_exit(-15) is False
    assert classify_oom_exit(15) is False
    assert classify_oom_exit(1) is False
    assert classify_oom_exit(0) is False
    assert classify_oom_exit(None) is False
    assert classify_oom_exit(0, memory_error=True) is True
    # A readable oom_kill count overrides the returncode rule.
    assert classify_oom_exit(-9, oom_kill=0) is False
    assert classify_oom_exit(137, oom_kill=0) is False
    assert classify_oom_exit(-9, oom_kill=1) is True
    assert classify_oom_exit(1, oom_kill=None) is False


@pytest.mark.skipif(
    __import__("sys").platform == "darwin",
    reason="Darwin rejects RLIMIT_AS lowers; live probe is memory_probe CLI / Linux CI",
)
def test_injected_allocation_breach_classified_as_oom(tmp_path: Path) -> None:
    """OS hard limit must stop an injected allocation breach (not polling)."""
    proof = run_startup_self_test()
    if not proof.enforced:
        pytest.skip(f"OS memory limit not enforceable here: {proof.detail}")

    result = run_capped_worker(
        {
            "job": "inject_oom",
            "chunk_id": "oom-probe",
            "memory_high_bytes": proof.max_bytes,
            "memory_max_bytes": proof.max_bytes,
        },
        result_path=tmp_path / "oom_result.json",
        timeout_s=60.0,
    )
    assert result.error_code == ErrorCode.FAILED_OOM.value
    assert result.outcome == "failed_terminal"


def test_cgroup_guard_refuses_shared_fake_directory_and_writes_exclusive(tmp_path: Path) -> None:
    """The write guard is decided from cgroup.procs, not from a live kernel cgroup."""
    from scripts.lexicon.runner.memory import MemoryPolicy, _try_apply_cgroup_limit

    policy = MemoryPolicy(high_bytes=1000, max_bytes=2000)

    missing = tmp_path / "missing"
    missing.mkdir()
    assert _try_apply_cgroup_limit(missing, policy, 10) is False
    assert not (missing / "memory.max").exists()

    shared = tmp_path / "shared"
    shared.mkdir()
    (shared / "cgroup.procs").write_text("10\n20\n", encoding="utf-8")
    (shared / "memory.max").write_text("max\n", encoding="utf-8")
    (shared / "memory.high").write_text("max\n", encoding="utf-8")
    assert _try_apply_cgroup_limit(shared, policy, 10) is False
    assert (shared / "memory.max").read_text(encoding="utf-8") == "max\n"
    assert (shared / "memory.high").read_text(encoding="utf-8") == "max\n"

    exclusive = tmp_path / "exclusive"
    exclusive.mkdir()
    (exclusive / "cgroup.procs").write_text("10\n", encoding="utf-8")
    (exclusive / "cgroup.stat").write_text("nr_descendants 0\nnr_dying_descendants 0\n", encoding="utf-8")
    (exclusive / "memory.max").write_text("max\n", encoding="utf-8")
    (exclusive / "memory.high").write_text("max\n", encoding="utf-8")
    assert _try_apply_cgroup_limit(exclusive, policy, 10) is True
    assert (exclusive / "memory.max").read_text(encoding="utf-8").strip() == "2000"
    assert (exclusive / "memory.high").read_text(encoding="utf-8").strip() == "1000"

    descendants = tmp_path / "descendants"
    descendants.mkdir()
    (descendants / "cgroup.procs").write_text("10\n", encoding="utf-8")
    (descendants / "cgroup.stat").write_text(
        "nr_descendants 1\nnr_dying_descendants 0\n",
        encoding="utf-8",
    )
    (descendants / "memory.max").write_text("max\n", encoding="utf-8")
    (descendants / "memory.high").write_text("max\n", encoding="utf-8")
    assert _try_apply_cgroup_limit(descendants, policy, 10) is False
    assert (descendants / "memory.max").read_text(encoding="utf-8") == "max\n"
    assert (descendants / "memory.high").read_text(encoding="utf-8") == "max\n"

    missing_stat = tmp_path / "missing-stat"
    missing_stat.mkdir()
    (missing_stat / "cgroup.procs").write_text("10\n", encoding="utf-8")
    (missing_stat / "memory.max").write_text("max\n", encoding="utf-8")
    (missing_stat / "memory.high").write_text("max\n", encoding="utf-8")
    assert _try_apply_cgroup_limit(missing_stat, policy, 10) is False
    assert (missing_stat / "memory.max").read_text(encoding="utf-8") == "max\n"


def test_slice_name_from_dispatch_cgroup() -> None:
    from scripts.lexicon.runner.memory import MemoryPolicy, _scope_argv, slice_name_from_cgroup_relative

    dispatch = (
        "/user.slice/user-1000.slice/user@1000.service/lu.slice/"
        "lu-dispatch.slice/lu-worker-fix.scope"
    )
    assert slice_name_from_cgroup_relative(dispatch) == "lu-dispatch.slice"
    # No user@ segment: an ssh session or a system slice must not invent --slice.
    assert slice_name_from_cgroup_relative("/user.slice/user-1000.slice/session-3.scope") is None
    assert slice_name_from_cgroup_relative("/app.slice/run-p1.scope") is None
    assert slice_name_from_cgroup_relative("/user.slice/user-1000.slice/user@1000.service") is None
    omitted = _scope_argv(["/bin/true"], MemoryPolicy(), "lexicon-cap-x", None)
    assert not any(part.startswith("--slice=") for part in omitted)
    assert "OOMPolicy=kill" in omitted
    placed = _scope_argv(["/bin/true"], MemoryPolicy(), "lexicon-cap-x", "lu-dispatch.slice")
    assert "--slice=lu-dispatch.slice" in placed


def _skip_without_user_scope() -> None:
    import sys

    from scripts.lexicon.runner.memory import _user_systemd_environ, systemd_user_scope_available

    if not sys.platform.startswith("linux"):
        pytest.skip("user systemd scope is Linux-only")
    if _user_systemd_environ() is None:
        pytest.skip("user systemd bus is absent; a dedicated cgroup cannot be created without root")
    if not systemd_user_scope_available():
        pytest.skip("user transient scope is not writable without root")


def _lexicon_cap_units() -> list[str]:
    import subprocess

    from scripts.lexicon.runner.memory import _user_systemd_environ

    env = _user_systemd_environ()
    if env is None:
        return []
    completed = subprocess.run(
        ["systemctl", "--user", "list-units", "lexicon-cap-*", "--no-legend", "--plain", "--all"],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    return [line.strip() for line in completed.stdout.splitlines() if "lexicon-cap-" in line]


def _wait_lexicon_cap_units(before: list[str]) -> list[str]:
    import time

    after = _lexicon_cap_units()
    for _ in range(20):
        if after == before:
            return after
        time.sleep(0.1)
        after = _lexicon_cap_units()
    return after


def _enable_probe_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEXICON_WORKER_PROBE_JOBS", "1")


def test_failed_to_connect_stderr_runs_worker_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A worker that prints a scope-start marker and exits 1 runs exactly once."""
    import sys

    from scripts.lexicon.runner.memory import systemd_user_scope_available

    _enable_probe_jobs(monkeypatch)
    counter = tmp_path / "runs.txt"
    result = run_capped_worker(
        {
            "job": "stderr_exit",
            "chunk_id": "stderr-once",
            "stderr_text": "Failed to connect to user scope bus via local transport",
            "exit_code": 1,
            "counter_path": str(counter),
        },
        result_path=tmp_path / "result.json",
        timeout_s=30,
    )
    assert counter.read_text(encoding="utf-8").splitlines() == ["1"]
    assert result.error_code == "worker_crash"
    if sys.platform.startswith("linux"):
        expected = "systemd_scope" if systemd_user_scope_available() else "rlimit_as"
        assert result.memory_mechanism == expected


def test_worker_scope_is_sibling_in_caller_slice(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    import logging

    from scripts.lexicon.runner.memory import caller_slice_name, self_cgroup_relative

    _skip_without_user_scope()
    _enable_probe_jobs(monkeypatch)
    slice_name = caller_slice_name()
    assert slice_name
    parent = self_cgroup_relative() or ""
    with caplog.at_level(logging.INFO, logger="scripts.lexicon.runner.memory"):
        result = run_capped_worker(
            {"job": "placement", "chunk_id": "placement"},
            result_path=tmp_path / "placement.json",
            timeout_s=30,
        )
    assert result.outcome == "done"
    assert result.memory_mechanism == "systemd_scope"
    assert any("mechanism=systemd_scope" in record.message for record in caplog.records)
    child_parts = [part for part in result.message.split("/") if part]
    parent_parts = [part for part in parent.split("/") if part]
    assert child_parts[-1].startswith("lexicon-cap-")
    assert child_parts[-1].endswith(".scope")
    assert child_parts[-2] == slice_name
    assert child_parts[-1] != parent_parts[-1]


def test_scope_sigkill_classified_as_oom(tmp_path: Path) -> None:
    _skip_without_user_scope()
    cap = 128 * 1024 * 1024
    result = run_capped_worker(
        {
            "job": "inject_oom",
            "chunk_id": "scope-oom",
            "memory_high_bytes": cap,
            "memory_max_bytes": cap,
        },
        result_path=tmp_path / "oom.json",
        timeout_s=60,
    )
    assert result.error_code == ErrorCode.FAILED_OOM.value
    assert result.outcome == "failed_terminal"
    assert result.memory_mechanism == "systemd_scope"
    assert "returncode=-9" in result.message


def test_timeout_stops_worker_scope(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _skip_without_user_scope()
    _enable_probe_jobs(monkeypatch)
    before = _lexicon_cap_units()
    result = run_capped_worker(
        {"job": "sleep", "chunk_id": "timeout", "sleep_s": 30},
        result_path=tmp_path / "sleep.json",
        timeout_s=3,
    )
    assert result.error_code == "worker_timeout"
    assert result.memory_mechanism == "systemd_scope"
    assert _wait_lexicon_cap_units(before) == before


def test_unavailable_scope_records_rlimit_as(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import logging
    import sys

    if not sys.platform.startswith("linux"):
        pytest.skip("RLIMIT_AS fallback is the Linux plain-child path")
    _enable_probe_jobs(monkeypatch)
    monkeypatch.setattr("scripts.lexicon.runner.memory.systemd_user_scope_available", lambda: False)
    with caplog.at_level(logging.INFO, logger="scripts.lexicon.runner.memory"):
        result = run_capped_worker(
            {"job": "placement", "chunk_id": "fallback"},
            result_path=tmp_path / "fallback.json",
            timeout_s=30,
        )
    assert result.outcome == "done"
    assert result.memory_mechanism == "rlimit_as"
    assert any("mechanism=rlimit_as" in record.message for record in caplog.records)


def test_shared_cgroup_memory_max_unchanged_and_breach_is_oom(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A plain child must not lower a cgroup it shares with another process.

    The scope probe is forced off so this goes through the plain-child path
    and the ``cgroup.procs`` guard. ``RLIMIT_AS`` still classifies
    ``failed_oom``, and ``memory.max`` stays unchanged.
    """
    import subprocess
    import sys
    import time
    from pathlib import Path as FsPath

    from scripts.lexicon.runner.memory import self_cgroup_relative

    if not sys.platform.startswith("linux"):
        pytest.skip("cgroup v2 shared-scope probe is Linux-only")
    monkeypatch.setattr("scripts.lexicon.runner.memory.systemd_user_scope_available", lambda: False)
    relative = self_cgroup_relative()
    if not relative:
        pytest.skip("this process has no readable cgroup v2 path")
    cgroup_dir = FsPath("/sys/fs/cgroup") / relative.lstrip("/")
    max_path = cgroup_dir / "memory.max"
    procs_path = cgroup_dir / "cgroup.procs"
    try:
        before = max_path.read_text(encoding="utf-8").strip()
    except OSError:
        pytest.skip("this process has no readable memory.max")
    sleeper = subprocess.Popen(["/bin/sleep", "30"])
    try:
        time.sleep(0.2)
        procs = [int(line) for line in procs_path.read_text(encoding="utf-8").split() if line.strip()]
        if sleeper.pid not in procs or len(set(procs)) < 2:
            pytest.fail(f"sleeper did not share the cgroup: procs={procs} sleeper={sleeper.pid}")
        cap = 128 * 1024 * 1024
        result = run_capped_worker(
            {
                "job": "inject_oom",
                "chunk_id": "shared-cgroup",
                "memory_high_bytes": cap,
                "memory_max_bytes": cap,
            },
            result_path=tmp_path / "result.json",
            timeout_s=60,
        )
        after = max_path.read_text(encoding="utf-8").strip()
    finally:
        sleeper.kill()
        sleeper.wait(timeout=5)
    assert after == before
    assert result.error_code == ErrorCode.FAILED_OOM.value
    assert result.outcome == "failed_terminal"
    assert result.memory_mechanism == "rlimit_as"


def test_production_payload_rejects_probe_only_jobs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """stderr_exit, sleep, and placement are not reachable from a production payload."""
    monkeypatch.delenv("LEXICON_WORKER_PROBE_JOBS", raising=False)
    for job in ("stderr_exit", "sleep", "placement"):
        result = run_capped_worker(
            {"job": job, "chunk_id": f"prod-{job}"},
            result_path=tmp_path / f"{job}.json",
            timeout_s=30,
        )
        assert result.error_code == "unknown_job"
        assert job in result.message


def test_scope_start_failure_includes_stderr_tail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A scope that fails after the probe passed keeps a stderr tail on worker_crash."""
    import subprocess

    head = "HEAD-MARKER"
    tail = "TAIL-scope-unit-failed"
    stderr = head + ("x" * 800) + tail

    def fake_run(argv, **kwargs):
        failed = bool(argv) and argv[0] == "systemd-run"
        return subprocess.CompletedProcess(argv, 1 if failed else 0, "", stderr if failed else "")

    monkeypatch.setattr("scripts.lexicon.runner.memory.systemd_user_scope_available", lambda: True)
    monkeypatch.setattr("scripts.lexicon.runner.memory._user_systemd_environ", lambda: {"PATH": "/usr/bin"})
    monkeypatch.setattr("scripts.lexicon.runner.memory.subprocess.run", fake_run)
    result = run_capped_worker(
        {"job": "enrich", "chunk_id": "scope-start"},
        result_path=tmp_path / "scope-start.json",
        timeout_s=30,
    )
    assert result.error_code == "worker_crash"
    assert result.memory_mechanism == "systemd_scope"
    assert "returncode=1" in result.message
    assert tail in result.message
    assert head not in result.message


def test_recorded_oom_kill_zero_is_not_oom_when_stop_drops_the_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """oom_kill is consumed before stop. Stop tearing the record down must not fall back to SIGKILL."""
    import subprocess

    state: dict[str, object] = {"path": None, "stopped": False}

    def fake_run(argv, **kwargs):
        if argv and argv[0] == "systemd-run":
            path = Path(kwargs["env"]["LEXICON_OOM_EVENTS_FILE"])
            state["path"] = path
            path.write_text("0\n", encoding="utf-8")
            return subprocess.CompletedProcess(argv, -9, "", "")
        if argv and argv[0] == "systemctl" and "stop" in argv:
            path = state["path"]
            assert isinstance(path, Path)
            assert path.read_text(encoding="utf-8").strip() == "0"
            path.unlink()
            state["stopped"] = True
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 1, "", "")

    monkeypatch.setattr("scripts.lexicon.runner.memory.systemd_user_scope_available", lambda: True)
    monkeypatch.setattr("scripts.lexicon.runner.memory._user_systemd_environ", lambda: {"PATH": "/usr/bin"})
    monkeypatch.setattr("scripts.lexicon.runner.memory.subprocess.run", fake_run)
    result = run_capped_worker(
        {"job": "enrich", "chunk_id": "external-kill"},
        result_path=tmp_path / "external.json",
        timeout_s=30,
    )
    assert state["stopped"] is True
    assert result.error_code == "worker_crash"
    assert result.memory_mechanism == "systemd_scope"


def test_unreadable_oom_events_fall_back_to_sigkill(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When memory.events was not recorded, returncode -9 is still an OOM."""
    import subprocess

    def fake_run(argv, **kwargs):
        if argv and argv[0] == "systemd-run":
            return subprocess.CompletedProcess(argv, -9, "", "")
        return subprocess.CompletedProcess(argv, 1, "", "")

    monkeypatch.setattr("scripts.lexicon.runner.memory.systemd_user_scope_available", lambda: True)
    monkeypatch.setattr("scripts.lexicon.runner.memory._user_systemd_environ", lambda: {"PATH": "/usr/bin"})
    monkeypatch.setattr("scripts.lexicon.runner.memory.subprocess.run", fake_run)
    result = run_capped_worker(
        {"job": "enrich", "chunk_id": "unreadable-oom"},
        result_path=tmp_path / "unreadable.json",
        timeout_s=30,
    )
    assert result.error_code == ErrorCode.FAILED_OOM.value
    assert "returncode=-9" in result.message


def _kill_worker_in_new_scope(before: list[str]) -> bool:
    """SIGKILL the lexicon worker inside a scope started after ``before``. Leave the reaper shell."""
    import os
    import subprocess
    import time

    from scripts.lexicon.runner.memory import _user_systemd_environ

    env = _user_systemd_environ()
    if env is None:
        return False
    before_units = {line.split()[0] for line in before}
    for _ in range(80):
        for line in _lexicon_cap_units():
            unit = line.split()[0]
            if unit in before_units or "lexicon-cap-" not in unit:
                continue
            if not unit.endswith(".scope"):
                continue
            shown = subprocess.run(
                ["systemctl", "--user", "show", "-p", "ControlGroup", "--value", unit],
                env=env,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            relative = shown.stdout.strip()
            if not relative.startswith("/"):
                continue
            procs = Path("/sys/fs/cgroup") / relative.lstrip("/") / "cgroup.procs"
            try:
                pids = [int(item) for item in procs.read_text(encoding="utf-8").split() if item.strip()]
            except OSError:
                continue
            for pid in pids:
                try:
                    command = Path(f"/proc/{pid}/cmdline").read_bytes()
                except OSError:
                    continue
                # The reaper shell's argv also contains the worker module path.
                # Kill only the interpreter, so the shell can still read oom_kill.
                argv0 = command.split(b"\0", 1)[0]
                if b"python" not in argv0:
                    continue
                if b"scripts.lexicon.runner.worker" not in command:
                    continue
                os.kill(pid, 9)
                return True
        time.sleep(0.05)
    return False


def test_external_sigkill_is_not_recorded_as_oom(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A kill -9 from outside does not increment oom_kill, so it is not failed_oom."""
    import threading

    _skip_without_user_scope()
    _enable_probe_jobs(monkeypatch)
    before = _lexicon_cap_units()
    killed = {"ok": False}

    def _kill() -> None:
        killed["ok"] = _kill_worker_in_new_scope(before)

    thread = threading.Thread(target=_kill, daemon=True)
    thread.start()
    result = run_capped_worker(
        {"job": "sleep", "chunk_id": "external-sigkill", "sleep_s": 30},
        result_path=tmp_path / "external-sigkill.json",
        timeout_s=20,
    )
    thread.join(timeout=5)
    assert killed["ok"] is True
    assert result.error_code == "worker_crash"
    assert result.memory_mechanism == "systemd_scope"
    assert _wait_lexicon_cap_units(before) == before


def test_deterministic_oom_split_and_single_lemma_failed_oom() -> None:
    parent = ChunkSpec(chunk_id="parent", lemma_ids=["a", "b", "c", "d"])
    split = split_on_oom(parent)
    assert isinstance(split, OomSplitChildren)
    assert split.left.chunk_id == child_chunk_id("parent", 1, ["a", "b"])
    assert split.right.chunk_id == child_chunk_id("parent", 1, ["c", "d"])
    # Crash-retry stability
    again = split_on_oom(parent)
    assert isinstance(again, OomSplitChildren)
    assert again.left.chunk_id == split.left.chunk_id
    assert again.right.chunk_id == split.right.chunk_id

    single = ChunkSpec(chunk_id="leaf", lemma_ids=["only"])
    failed, code = split_on_oom(single)  # type: ignore[misc]
    assert code == ErrorCode.FAILED_OOM.value
    assert failed.state == ChunkState.FAILED_TERMINAL


def test_streaming_manifest_roundtrip(tmp_path: Path, fixture_paths: dict[str, Path]) -> None:
    staged = stage_manifest_to_sqlite(fixture_paths["input"], tmp_path / "staged.sqlite")
    assert staged["entry_count"] == 500
    entries = list(stream_manifest_entries_json(tmp_path / "staged.sqlite"))
    assert len(entries) == 500
    out = tmp_path / "candidate.json"
    with StreamingCandidateWriter(out, meta={"enrichment_generated": True}) as writer:
        for entry in entries:
            writer.write_entry(entry)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["enrichment_generated"] is True
    assert len(data["entries"]) == 500


def test_side_dbs_match_python_index_lookups(
    tmp_path: Path, fixture_paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    em._BALLA_SIDE_DB = None
    em._DMKLINGER_SIDE_DB = None
    em._DMKLINGER_INDEX = None
    em._BALLA_REVERSE_INDEX.clear()
    monkeypatch.setattr(em, "_vesum_word_analyses", lambda word: ((word, "noun"),))

    conn = sqlite3.connect(f"file:{fixture_paths['sources'].resolve().as_posix()}?mode=ro", uri=True)
    try:
        py_balla = em._load_balla_reverse_index(conn)
        py_dmk = em._load_dmklinger_index(conn)
        balla_art = build_balla_reverse_side_db(
            conn,
            tmp_path / "balla.sqlite",
            candidate_keys=em._balla_reverse_candidate_keys,
            headword_fn=em._balla_reverse_headword,
            segment_fn=em._balla_reverse_definition_segments,
            token_re=em._BALLA_REVERSE_UKRAINIAN_TOKEN_RE,
        )
        dmk_art = build_dmklinger_side_db(
            conn,
            tmp_path / "dmk.sqlite",
            key_fn=em._dmklinger_key,
        )
    finally:
        conn.close()

    kaikki_art = build_kaikki_side_db(fixture_paths["kaikki"], tmp_path / "kaikki.sqlite")
    assert balla_art.sha256
    assert dmk_art.sha256
    assert kaikki_art.sha256

    balla = BallaReverseSideDb(Path(balla_art.path))
    dmk = DmklingerSideDb(Path(dmk_art.path))
    kaikki = KaikkiSideDb(Path(kaikki_art.path))
    try:
        for key, values in py_balla.items():
            assert balla.lookup(key) == values
        for key, values in py_dmk.items():
            assert dmk.lookup(key) == [(str(p or ""), str(t or "")) for p, t in values]
        raw_kaikki = json.loads(fixture_paths["kaikki"].read_text(encoding="utf-8"))
        for key, payload in raw_kaikki.items():
            assert kaikki.get(key) == payload
    finally:
        balla.close()
        dmk.close()
        kaikki.close()


def test_sealed_cefr_matches_legacy_prepare(tmp_path: Path, fixture_paths: dict[str, Path]) -> None:
    entries = json.loads(fixture_paths["input"].read_text(encoding="utf-8"))["entries"]
    grac = json.loads(fixture_paths["grac"].read_text(encoding="utf-8"))
    em._CEFR_ESTIMATE_LEVEL_BY_KEY.clear()
    em._GRAC_FREQUENCY_CACHE_DATA = grac

    conn = sqlite3.connect(f"file:{fixture_paths['sources'].resolve().as_posix()}?mode=ro", uri=True)
    try:
        em._prepare_cefr_estimates(conn, {"entries": entries})
        legacy = dict(em._CEFR_ESTIMATE_LEVEL_BY_KEY)
        seal = sealed_cefr_precompute(
            lemmas=(str(e.get("lemma") or "") for e in entries),
            puls_cefr_fn=lambda lemma: em._puls_cefr(conn, lemma),
            grac_lookup_key_fn=em._grac_lookup_key,
            grac_cache=grac,
            output_db=tmp_path / "cefr.sqlite",
        )
    finally:
        conn.close()

    sealed = load_sealed_cefr_map(tmp_path / "cefr.sqlite")
    assert seal.row_count == len(legacy) == len(sealed)
    # Load-bearing: unwarmed GRAC cache yields zero ranks; this cohort must seal >0.
    assert seal.row_count > 0
    assert sum(1 for row in sealed.values() if int(row["rank"]) >= 1 and int(row["freq"]) > 0) > 0
    assert sealed == legacy
    # Band boundaries: ranks must map to the same A1..C1 bands.
    for key, row in sealed.items():
        assert row["level"] == legacy[key]["level"]
        assert row["rank"] == legacy[key]["rank"]
        assert row["total"] == legacy[key]["total"]


def test_coordinator_warms_grac_before_cefr_seal(
    tmp_path: Path, fixture_paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unwarmed empty cache must not silently seal zero ranks when legacy has ranks."""
    from scripts.lexicon.runner.memory import EnforcementProof
    from scripts.lexicon.runner.offline_engine import enrich_offline_slice
    from scripts.lexicon.runner.phase_cefr import load_sealed_cefr_map

    entries = json.loads(fixture_paths["input"].read_text(encoding="utf-8"))["entries"]
    grac = json.loads(fixture_paths["grac"].read_text(encoding="utf-8"))
    em._CEFR_ESTIMATE_LEVEL_BY_KEY.clear()
    em._GRAC_FREQUENCY_CACHE_DATA = {}  # start empty — warm must populate from ensure

    ensure_calls: list[list[str]] = []

    def _fake_ensure(words: list[str]) -> None:
        ensure_calls.append(list(words))
        # Simulate online warm: fill the global cache from the fixture slice.
        cache = em._load_grac_frequency_cache()
        for word in words:
            if word in grac:
                cache[word] = grac[word]

    monkeypatch.setattr(em, "_ensure_grac_frequency_cache", _fake_ensure)
    monkeypatch.setattr(em, "_vesum_valid_synonym", lambda term: bool(term))
    monkeypatch.setattr(
        "scripts.lexicon.runner.offline_engine.run_startup_self_test",
        lambda **_kwargs: EnforcementProof(
            kind="rlimit_as",
            enforced=True,
            detail="test stub",
            max_bytes=64 * 1024 * 1024,
        ),
    )
    # Seal phase is under test; skip leaf enrichment (needs full sources.db).
    monkeypatch.setattr(
        "scripts.lexicon.runner.worker_enrich.enrich_chunk_payload",
        lambda _payload: {},
    )

    # Legacy baseline ranks on this cohort (with warmed fixture GRAC).
    em._GRAC_FREQUENCY_CACHE_DATA = dict(grac)
    conn = sqlite3.connect(f"file:{fixture_paths['sources'].resolve().as_posix()}?mode=ro", uri=True)
    try:
        em._prepare_cefr_estimates(conn, {"entries": entries})
        legacy_count = len(em._CEFR_ESTIMATE_LEVEL_BY_KEY)
    finally:
        conn.close()
    assert legacy_count > 0

    em._CEFR_ESTIMATE_LEVEL_BY_KEY.clear()
    em._GRAC_FREQUENCY_CACHE_DATA = {}

    work = tmp_path / "runner_work"
    out = tmp_path / "candidate.json"
    result = enrich_offline_slice(
        manifest_path=fixture_paths["input"],
        sources_db=fixture_paths["sources"],
        kaikki_json=fixture_paths["kaikki"],
        work_dir=work,
        output_path=out,
        grac_cache={},
        require_memory_self_test=False,
        skip_workers=True,
        chunk_size=50,
    )
    assert ensure_calls, "coordinator must call _ensure_grac_frequency_cache before seal"
    assert len(ensure_calls[0]) > 0
    sealed = load_sealed_cefr_map(work / "seals" / "cefr.sqlite")
    assert result["cefr_seal"]
    assert len(sealed) > 0
    assert len(sealed) == legacy_count
    assert sum(1 for row in sealed.values() if int(row["rank"]) >= 1) > 0


def test_runner_spawns_use_primary_project_interpreter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Self-test and worker spawns use the primary checkout interpreter.

    A primary checkout uses its own ``.venv/bin/python``. A linked worktree
    uses that same primary interpreter even when the worktree has a local
    virtualenv. When neither checkout has a ``.venv``, ``sys.executable``
    is accepted unless it lives in some other checkout's ``.venv``.
    """
    import inspect

    from scripts.common.repo_root import main_checkout_root
    from scripts.lexicon.runner import memory as memory_mod
    from scripts.lexicon.runner import worker as worker_mod

    live = main_checkout_root(memory_mod.ROOT) / ".venv" / "bin" / "python"
    assert live.is_file()
    assert live == memory_mod.project_interpreter()
    for fn in (memory_mod.run_startup_self_test, worker_mod.run_capped_worker):
        source = inspect.getsource(fn)
        assert "sys.executable" not in source
        assert "project_interpreter()" in source

    primary = tmp_path / "primary"
    (primary / ".git").mkdir(parents=True)
    primary_python = primary / ".venv" / "bin" / "python"
    primary_python.parent.mkdir(parents=True)
    primary_python.write_text("", encoding="utf-8")
    assert memory_mod.project_interpreter(primary) == primary_python

    worktree = primary / ".worktrees" / "dispatch" / "grok" / "task"
    git_dir = primary / ".git" / "worktrees" / "task"
    git_dir.mkdir(parents=True)
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n", encoding="utf-8")
    local_python = worktree / ".venv" / "bin" / "python"
    local_python.parent.mkdir(parents=True)
    local_python.write_text("", encoding="utf-8")
    assert memory_mod.project_interpreter(worktree) == primary_python

    bare = tmp_path / "bare"
    bare.mkdir()
    foreign = tmp_path / "running" / ".venv" / "bin" / "python"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("", encoding="utf-8")
    monkeypatch.setattr(memory_mod.sys, "executable", str(foreign))
    with pytest.raises(FileNotFoundError, match="project interpreter not found"):
        memory_mod.project_interpreter(bare)

    monkeypatch.setattr(memory_mod.sys, "executable", "/usr/bin/python3")
    assert memory_mod.project_interpreter(bare) == Path("/usr/bin/python3")


def test_import_succeeds_when_project_interpreter_resolution_would_fail() -> None:
    """Importing memory and worker does not resolve the project interpreter.

    A fresh interpreter hides every ``.venv/bin/python`` and points
    ``sys.executable`` at another checkout's ``.venv/bin/python``. Import
    still succeeds. The spawn paths raise the same ``FileNotFoundError``
    when they resolve.
    """
    import subprocess
    import sys
    import textwrap

    repo = Path(__file__).resolve().parents[1]
    script = textwrap.dedent(
        """\
        import sys
        import tempfile
        from pathlib import Path

        sys.executable = "/tmp/foreign-checkout/.venv/bin/python"
        real_is_file = Path.is_file

        def hide_project_venv(self: Path) -> bool:
            if self.parts[-3:] == (".venv", "bin", "python"):
                return False
            return real_is_file(self)

        Path.is_file = hide_project_venv

        import scripts.lexicon.runner.memory as memory
        import scripts.lexicon.runner.worker as worker

        try:
            memory.project_interpreter()
        except FileNotFoundError as exc:
            message = str(exc)
        else:
            raise SystemExit("project_interpreter() did not fail")
        if "project interpreter not found" not in message:
            raise SystemExit(message)

        try:
            memory.run_startup_self_test(test_max_bytes=1024)
        except FileNotFoundError as exc:
            spawn_message = str(exc)
        else:
            raise SystemExit("run_startup_self_test did not fail")
        if "project interpreter not found" not in spawn_message:
            raise SystemExit(spawn_message)

        with tempfile.TemporaryDirectory() as tmp:
            try:
                worker.run_capped_worker(
                    {"chunk_id": "import-probe", "job": "enrich"},
                    result_path=Path(tmp) / "result.json",
                )
            except FileNotFoundError as exc:
                worker_message = str(exc)
            else:
                raise SystemExit("run_capped_worker did not fail")
        if "project interpreter not found" not in worker_message:
            raise SystemExit(worker_message)
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout


def test_rlimit_ceiling_rejects_infinity_sentinel() -> None:
    import resource

    from scripts.lexicon.runner.memory import _is_finite_positive_ceiling, _try_set_rlimit_as

    assert _is_finite_positive_ceiling(1024 * 1024) is True
    assert _is_finite_positive_ceiling(0) is False
    assert _is_finite_positive_ceiling(-1) is False
    assert _is_finite_positive_ceiling(resource.RLIM_INFINITY) is False
    with pytest.raises(ValueError, match="invalid RLIMIT_AS ceiling"):
        _try_set_rlimit_as(0)
    with pytest.raises(ValueError, match="invalid RLIMIT_AS ceiling"):
        _try_set_rlimit_as(resource.RLIM_INFINITY)


def _cache_from_slice(conn: sqlite3.Connection, lemma: str) -> dict:
    """СУМ-20 cache document stored in the temp sources slice."""
    return load_slovnyk_cache(conn, lemma)


def test_relation_closure_matches_legacy_by_headword(
    tmp_path: Path, fixture_paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    entries = json.loads(fixture_paths["input"].read_text(encoding="utf-8"))["entries"]
    monkeypatch.setattr(em, "_vesum_valid_synonym", lambda term: bool(term))

    conn = sqlite3.connect(f"file:{fixture_paths['sources'].resolve().as_posix()}?mode=ro", uri=True)
    try:
        monkeypatch.setattr(
            em,
            "_read_cached_slovnyk_rows",
            lambda lemma: _cache_from_slice(conn, lemma),
        )
        manifest = {"entries": entries}
        legacy_syn = em._definition_pointer_relations_by_headword(conn, manifest, has_sum11_flags=False)
        legacy_ant = em._definition_antonym_relations_by_headword(conn, manifest, has_sum11_flags=False)
        headwords = em._manifest_headwords(manifest)
        extract_and_close_relations(
            entries=entries,
            extractors={
                "synonym": lambda entry: em._definition_pointer_relations(
                    conn,
                    str(entry.get("lemma") or ""),
                    has_sum11_flags=False,
                    cache=_cache_from_slice(conn, str(entry.get("lemma") or "")),
                ),
                "antonym": lambda entry: em._definition_antonym_relations(
                    conn,
                    str(entry.get("lemma") or ""),
                    has_sum11_flags=False,
                    cache=_cache_from_slice(conn, str(entry.get("lemma") or "")),
                ),
            },
            headwords=headwords,
            canonical_term_fn=em._canonical_synonym_term,
            vesum_valid_fn=em._vesum_valid_synonym,
            output_db=tmp_path / "rel.sqlite",
            reciprocal_kinds=frozenset({"synonym", "antonym"}),
        )
    finally:
        conn.close()

    closed_syn = load_closed_relations_by_headword(tmp_path / "rel.sqlite", kind="synonym")
    closed_ant = load_closed_relations_by_headword(tmp_path / "rel.sqlite", kind="antonym")
    assert closed_syn == legacy_syn
    assert closed_ant == legacy_ant
    assert len(closed_syn) == 100
    assert sum(len(edges) for edges in closed_syn.values()) == 200
    assert len(closed_ant) == 50
    assert sum(len(edges) for edges in closed_ant.values()) == 50


def test_500_lemma_equivalence_cefr_and_relations(
    tmp_path: Path, fixture_paths: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Record-equivalent CEFR + reciprocal relations vs committed legacy baseline."""
    baseline = json.loads(fixture_paths["baseline"].read_text(encoding="utf-8"))
    expected_sha = fixture_paths["baseline_sha"].read_text(encoding="utf-8").strip()
    actual_sha = hashlib.sha256(fixture_paths["baseline"].read_bytes()).hexdigest()
    assert actual_sha == expected_sha

    entries = json.loads(fixture_paths["input"].read_text(encoding="utf-8"))["entries"]
    grac = json.loads(fixture_paths["grac"].read_text(encoding="utf-8"))
    monkeypatch.setattr(em, "_vesum_valid_synonym", lambda term: bool(term))
    em._CEFR_ESTIMATE_LEVEL_BY_KEY.clear()
    em._GRAC_FREQUENCY_CACHE_DATA = grac

    tmp_cefr = tmp_path / "cefr.sqlite"
    tmp_rel = tmp_path / "rel.sqlite"
    conn = sqlite3.connect(f"file:{fixture_paths['sources'].resolve().as_posix()}?mode=ro", uri=True)
    try:
        sealed_cefr_precompute(
            lemmas=(str(e.get("lemma") or "") for e in entries),
            puls_cefr_fn=lambda lemma: em._puls_cefr(conn, lemma),
            grac_lookup_key_fn=em._grac_lookup_key,
            grac_cache=grac,
            output_db=tmp_cefr,
        )
        apply_sealed_cefr_to_engine_cache(load_sealed_cefr_map(tmp_cefr), em._CEFR_ESTIMATE_LEVEL_BY_KEY)
        assert dict(em._CEFR_ESTIMATE_LEVEL_BY_KEY) == baseline["cefr_estimates"]
        # Load-bearing: sealed CEFR must carry GRAC-derived ranks (unwarmed cache → 0).
        assert len(em._CEFR_ESTIMATE_LEVEL_BY_KEY) > 0
        assert (
            sum(
                1
                for row in em._CEFR_ESTIMATE_LEVEL_BY_KEY.values()
                if int(row["rank"]) >= 1 and float(row["rel_freq"]) > 0.0
            )
            > 0
        )

        headwords = em._manifest_headwords({"entries": entries})
        extract_and_close_relations(
            entries=entries,
            extractors={
                "synonym": lambda entry: em._definition_pointer_relations(
                    conn,
                    str(entry.get("lemma") or ""),
                    has_sum11_flags=False,
                    cache=_cache_from_slice(conn, str(entry.get("lemma") or "")),
                ),
                "antonym": lambda entry: em._definition_antonym_relations(
                    conn,
                    str(entry.get("lemma") or ""),
                    has_sum11_flags=False,
                    cache=_cache_from_slice(conn, str(entry.get("lemma") or "")),
                ),
                "homonym": lambda entry: em._homonym_relations(conn, str(entry.get("lemma") or "")),
                "paronym": lambda entry: em._paronym_relations(conn, str(entry.get("lemma") or "")),
            },
            headwords=headwords,
            canonical_term_fn=em._canonical_synonym_term,
            vesum_valid_fn=em._vesum_valid_synonym,
            output_db=tmp_rel,
            reciprocal_kinds=frozenset({"synonym", "antonym"}),
        )
        for kind in ("synonym", "antonym", "homonym", "paronym"):
            closed = load_closed_relations_by_headword(tmp_rel, kind=kind)
            assert closed == baseline["relations"][kind], kind
    finally:
        conn.close()
