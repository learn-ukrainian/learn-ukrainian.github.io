"""Behavior tests for the pre-push gate (#10033): refuse red, accept green, bounded, no stale receipts."""

from __future__ import annotations

import contextlib
import errno
import fcntl
import importlib.util
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from tests.helpers.python import project_python
from tests.wait_helpers import wait_for_line, wait_for_pid_line, wait_until

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_DIR = REPO_ROOT / ".githooks"
GATE_PATH = HOOK_DIR / "pre_push_gate.py"
PYTHON = project_python()
ZERO_SHA = "0" * 40
# Agent sessions shim ``git`` and refuse the fixture's pushes to a disposable remote; use the real binary there.
GIT = os.environ.get("AGENT_REAL_GIT") or "git"

REGISTRY = textwrap.dedent(
    """\
    KNOWN_REPO_WIDE_MODULES = frozenset({"tests/test_invariant.py"})
    KNOWN_REPO_WIDE_FUNCTIONS = (
        "tests/test_invariant.py::test_inside_a_registered_module",
        "tests/test_scanner.py::test_scan",
    )
    """
)
PRE_COMMIT = textwrap.dedent(
    """\
    repos:
      - repo: local
        hooks:
          - id: fixture-pre-push
            name: fixture pre-push
            entry: bash -c 'test ! -e BLOCK_PRE_PUSH'
            language: system
            always_run: true
            pass_filenames: false
            stages: [pre-push]
    """
)
GREEN_TEST = "def test_ok():\n    assert True\n"
RED_TEST = "def test_broken():\n    assert False\n"
# The changed file runs first (worksteal), then the two registered invariants (loadfile).
SPLIT_SUMMARY_RE = r"1 passed in \d+(?:\.\d+)?s; 2 passed in \d+(?:\.\d+)?s"


def _install_surface_scanners(root: Path) -> None:
    """Use the maintained scanners and the actual learner-surface hook filter."""
    audit = root / "scripts/audit"
    audit.mkdir(parents=True, exist_ok=True)
    for name in ("lint_opsec_leaks.py", "check_no_internal_ids.py"):
        shutil.copyfile(REPO_ROOT / "scripts/audit" / name, audit / name)
    actual = yaml.safe_load((REPO_ROOT / ".pre-commit-config.yaml").read_text())
    internal_hook = next(
        hook for repo in actual["repos"] for hook in repo.get("hooks", []) if hook["id"] == "check-no-internal-ids"
    )
    config = yaml.safe_load(PRE_COMMIT)
    config["repos"][0]["hooks"].append(internal_hook)
    _write(root, ".pre-commit-config.yaml", yaml.safe_dump(config))


def _load_gate():
    spec = importlib.util.spec_from_file_location("pre_push_gate_under_test", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module through sys.modules
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.pop("AGENT_NO_MERGE", None)
    env.pop("PYTEST_ADDOPTS", None)
    env["PYTHONPATH"] = str(REPO_ROOT / "scripts")
    env.update(extra or {})
    return env


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run([GIT, *args], capture_output=True, check=check, cwd=repo, env=_env(), text=True, timeout=60)


def _write(repo: Path, relative: str, text: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _commit(repo: Path, message: str, *paths: str) -> str:
    _git(repo, "add", *paths)
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A repository whose base commit is already on the remote ``main``."""
    monkeypatch.setenv("PYTHONPATH", str(REPO_ROOT / "scripts"))
    root = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    root.mkdir()
    subprocess.run([GIT, "init", "--bare", str(remote)], check=True, capture_output=True, timeout=60)
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "gate@example.invalid")
    _git(root, "config", "user.name", "Gate Test")
    shutil.copytree(HOOK_DIR, root / ".githooks")
    launcher = root / "scripts/pre_commit/project_python.sh"
    launcher.parent.mkdir(parents=True)
    launcher.write_text(f'#!/usr/bin/env bash\nexec "{PYTHON}" "$@"\n', encoding="utf-8")
    launcher.chmod(0o755)
    _install_surface_scanners(root)
    _write(root, "pytest.ini", "[pytest]\n")
    _write(root, "tests/test_repo_wide_marker_invariant.py", REGISTRY)
    _write(root, "tests/test_invariant.py", GREEN_TEST)
    _write(root, "tests/test_scanner.py", "def test_scan():\n    assert True\n")
    _commit(root, "base", ".")
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "--no-verify", "origin", "main")
    _git(root, "checkout", "-b", "feature")
    return root


def _run_gate(
    repo: Path, *, remote_sha: str | None = None, extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    base = remote_sha or ZERO_SHA
    update = f"refs/heads/feature {head} refs/heads/feature {base}\n"
    return subprocess.run(
        [
            str(PYTHON),
            str(repo / ".githooks/pre_push_gate.py"),
            "--launcher",
            str(repo / "scripts/pre_commit/project_python.sh"),
            "--config",
            str(repo / ".pre-commit-config.yaml"),
            "origin",
            "unused",
        ],
        capture_output=True,
        check=False,
        cwd=repo,
        input=update,
        text=True,
        timeout=120,
        env=_env({"PRE_COMMIT_HOME": str(repo.parent / "pre-commit-cache"), **(extra_env or {})}),
    )


def _verdict(result: subprocess.CompletedProcess[str]) -> dict:
    lines = [line for line in result.stderr.splitlines() if line.startswith('{"pre_push_gate"')]
    assert lines, result.stderr
    return json.loads(lines[-1])["pre_push_gate"]


def _measurements(repo: Path) -> list[dict]:
    path = repo / ".git/lu-pre-push-gate/measurements.jsonl"
    return [
        row
        for line in path.read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line)).get("phase") != "BEGIN"
    ]


def _receipts(repo: Path) -> list[Path]:
    return sorted((repo / ".git/lu-pre-push-gate/receipts").glob("*.json"))


# ---- each push path refuses red and accepts green -------------------------------------------------------


def test_green_changed_test_is_accepted_and_leaves_a_receipt(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "1")
    monkeypatch.delenv(gate.MAX_TEST_PROCESSES_ENV, raising=False)
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "gate-test")
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")

    result = _run_gate(repo)

    assert result.returncode == 0, result.stderr
    assert len(_receipts(repo)) == 1
    assert _measurements(repo)[-1]["outcome"] == "green"
    pytest_row = _measurements(repo)[-1]["stages"]["pytest"]
    assert pytest_row["stale_pytest_cleanup"] == "exclusive_sweep"
    assert pytest_row["requested_test_processes"] == 4
    assert pytest_row["effective_test_processes"] == 2


def test_red_changed_test_is_refused_with_its_node_id(repo: Path) -> None:
    _write(repo, "tests/test_new.py", RED_TEST)
    _commit(repo, "red", "tests/test_new.py")

    result = _run_gate(repo)

    assert result.returncode == gate.EXIT_REFUSED
    verdict = _verdict(result)
    assert verdict["reason"] == "tests_failed"
    assert verdict["failing"] == ["tests/test_new.py::test_broken"]
    assert _receipts(repo) == []


def test_red_registry_invariant_is_refused_even_when_its_file_is_unchanged(repo: Path) -> None:
    _write(repo, "tests/test_unrelated.py", GREEN_TEST)
    _write(repo, "tests/test_invariant.py", RED_TEST)  # breaks the registered module
    _commit(repo, "break invariant", "tests")

    verdict = _verdict(_run_gate(repo))

    assert verdict["reason"] == "tests_failed"
    assert "tests/test_invariant.py::test_broken" in verdict["failing"]


def test_red_registered_function_is_refused(repo: Path) -> None:
    _write(repo, "tests/test_scanner.py", "def test_scan():\n    assert False\n")
    _write(repo, "src_change.txt", "x\n")
    _commit(repo, "break scanner", "tests", "src_change.txt")

    verdict = _verdict(_run_gate(repo))

    assert verdict["reason"] == "tests_failed"
    assert verdict["failing"] == ["tests/test_scanner.py::test_scan"]


def test_failing_pre_commit_pre_push_stage_is_refused_with_the_hook_display_name(repo: Path) -> None:
    _write(repo, "BLOCK_PRE_PUSH", "x\n")
    _commit(repo, "trip the hook", "BLOCK_PRE_PUSH")

    result = _run_gate(repo)

    assert result.returncode == gate.EXIT_REFUSED
    verdict = _verdict(result)
    assert verdict["reason"] == "pre_commit_failed"
    assert verdict["failing"] == ["fixture pre-push"]


def test_pre_commit_stage_sees_only_the_outgoing_range(repo: Path) -> None:
    _write(repo, "docs.md", "docs\n")
    _commit(repo, "docs", "docs.md")

    assert _run_gate(repo).returncode == 0


def test_nothing_outgoing_is_accepted_without_running_tests(repo: Path) -> None:
    result = _run_gate(repo, remote_sha=_git(repo, "rev-parse", "HEAD").stdout.strip())

    assert result.returncode == 0
    assert _measurements(repo)[-1]["detail"] == "no outgoing commits"


@pytest.mark.parametrize(
    "push_args",
    [("push", "-u", "origin", "feature"), ("push", "origin", "HEAD:refs/heads/feature")],
    ids=["auto-finalize-form", "worker-head-form"],
)
def test_real_git_push_through_the_tracked_hook(repo: Path, push_args: tuple[str, ...], tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    lfs = bin_dir / "git-lfs"
    lfs.write_text("#!/usr/bin/env bash\ncat >/dev/null\nexit 0\n", encoding="utf-8")
    lfs.chmod(0o755)
    _git(repo, "config", "core.hooksPath", str(repo / ".githooks"))
    env = _env(
        {"PATH": f"{bin_dir}:{os.environ['PATH']}", "PRE_COMMIT_HOME": str(tmp_path / "pc"), "TMPDIR": str(tmp_path)}
    )

    _write(repo, "tests/test_new.py", RED_TEST)
    _commit(repo, "red", "tests/test_new.py")
    refused = subprocess.run(
        [GIT, *push_args], capture_output=True, check=False, cwd=repo, env=env, text=True, timeout=120
    )
    assert refused.returncode != 0
    assert "tests/test_new.py::test_broken" in refused.stderr
    assert _git(repo, "ls-remote", "origin", "refs/heads/feature").stdout == ""

    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "fix", "tests/test_new.py")
    accepted = subprocess.run(
        [GIT, *push_args], capture_output=True, check=False, cwd=repo, env=env, text=True, timeout=120
    )
    assert accepted.returncode == 0, accepted.stderr
    assert _git(repo, "ls-remote", "origin", "refs/heads/feature").stdout.strip()


# ---- receipts ---------------------------------------------------------------------------------------------


def test_a_green_receipt_is_reused_for_the_same_commit(repo: Path) -> None:
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")
    assert _run_gate(repo).returncode == 0

    # A rerun would fail the pre-commit stage, and admission would time out. Reuse bypasses both
    # because the committed inputs and plan have not changed (this non-Python sentinel is scratch).
    _write(repo, "BLOCK_PRE_PUSH", "rerunning the stage would fail")
    with (repo / ".git/lu-pre-push-gate/admission.lock").open("r") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        result = _run_gate(repo, extra_env={"LU_PRE_PUSH_GATE_ADMISSION_WAIT_S": "0"})

    assert result.returncode == 0, result.stderr

    assert _measurements(repo)[-1]["detail"] == "valid receipt"
    assert _measurements(repo)[-1]["queue_depth"] == 0


def test_receipt_is_rejected_after_the_commit_changes(repo: Path) -> None:
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")
    assert _run_gate(repo).returncode == 0
    _write(repo, "tests/test_new.py", RED_TEST)
    _git(repo, "add", "tests/test_new.py")
    _git(repo, "commit", "--amend", "--no-edit")

    result = _run_gate(repo)

    assert result.returncode == gate.EXIT_REFUSED
    assert _verdict(result)["reason"] == "tests_failed"


def _plan(**overrides):
    values = {
        "head": "a" * 40,
        "tree": "b" * 40,
        "base": "c" * 40,
        "registry_version": "v1-x",
        "registry_nodes": ("tests/test_a.py",),
        "changed_tests": ("tests/test_b.py",),
        "changed_paths": (),
    }
    values.update(overrides)
    return gate.Plan(**values)


@pytest.fixture
def surface_repo(tmp_path: Path) -> Path:
    """A real commit range without the unrelated remote-push fixture setup."""
    root = tmp_path / "surface-repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "gate@example.invalid")
    _git(root, "config", "user.name", "Gate Test")
    _install_surface_scanners(root)
    _write(root, "scripts/pre_commit/project_python.sh", f'#!/usr/bin/env bash\nexec "{sys.executable}" "$@"\n')
    _write(root, "docs/push-scan.md", "clean base\n")
    _commit(root, "base", ".")
    return root


@pytest.mark.parametrize("sensitive", [False, True])
def test_push_stage_scans_intermediate_commits_even_with_empty_net_diff(surface_repo: Path, sensitive: bool) -> None:
    base = _git(surface_repo, "rev-parse", "HEAD").stdout.strip()
    marker = "-----BEGIN " + "PRIVATE KEY-----"
    _write(surface_repo, "docs/push-scan.md", marker if sensitive else "clean change\n")
    _commit(surface_repo, "first change", "docs/push-scan.md")
    _write(surface_repo, "docs/push-scan.md", "clean base\n")
    head = _commit(surface_repo, "revert", "docs/push-scan.md")
    assert _git(surface_repo, "diff", "--name-only", f"{base}..{head}").stdout == ""
    plan = _plan(base=base, head=head)
    arguments = (plan, surface_repo, str(surface_repo / "scripts/pre_commit/project_python.sh"),
                 str(surface_repo / ".pre-commit-config.yaml"), time.monotonic() + 60)
    if sensitive:
        with pytest.raises(gate.GateOutcome) as raised:
            gate.run_pre_commit_stage(*arguments)
        assert raised.value.failing == ("lint-opsec-leaks",)
        assert marker not in raised.value.detail
        assert "Private Key Header" in raised.value.detail
    else:
        gate.run_pre_commit_stage(*arguments)


@pytest.mark.parametrize("path,refused", [
    ("site/src/content/docs/a1/topic.mdx", True),
    ("site/src/content/readings/topic.mdx", True),
    ("curriculum/l2-uk-en/folk/topic/module.md", True),
    ("docs/author-notes.md", False),
])
def test_push_stage_enforces_existing_internal_id_learner_filter(surface_repo: Path, path: str, refused: bool) -> None:
    base = _git(surface_repo, "rev-parse", "HEAD").stdout.strip()
    _write(surface_repo, path, "Source section S4433 leaked.\n")
    head = _commit(surface_repo, "learner surface", path)
    arguments = (_plan(base=base, head=head), surface_repo,
                 str(surface_repo / "scripts/pre_commit/project_python.sh"),
                 str(surface_repo / ".pre-commit-config.yaml"), time.monotonic() + 60)
    if refused:
        with pytest.raises(gate.GateOutcome) as raised:
            gate.run_pre_commit_stage(*arguments)
        assert raised.value.failing == ("check-no-internal-ids",)
        assert "internal source section id leaked" in raised.value.detail
    else:
        gate.run_pre_commit_stage(*arguments)


@pytest.mark.parametrize(
    "field,value",
    [
        ("head", "f" * 40),
        ("tree", "d" * 40),
        ("base", "e" * 40),
        ("registry_version", "v1-y"),
        ("changed_tests", ("tests/test_b.py", "tests/test_c.py")),
        ("registry_nodes", ("tests/test_z.py",)),
        ("changed_paths", ("scripts/other.py",)),
    ],
)
def test_receipt_is_stale_after_any_bound_input_changes(tmp_path: Path, field: str, value: object) -> None:
    plan = _plan()
    gate.write_receipt(tmp_path, plan, 1000.0)
    assert gate.receipt_is_fresh(tmp_path, plan, 1001.0)

    assert not gate.receipt_is_fresh(tmp_path, _plan(**{field: value}), 1001.0)


def test_receipt_expires_and_a_tampered_receipt_is_ignored(tmp_path: Path) -> None:
    plan = _plan()
    gate.write_receipt(tmp_path, plan, 1000.0)
    assert not gate.receipt_is_fresh(tmp_path, plan, 1000.0 + gate.RECEIPT_TTL_S + 1)

    path = gate.receipt_path(tmp_path, plan)
    path.write_text(json.dumps({"key": gate.receipt_key(plan), "outcome": "red", "at": 1000.0}), encoding="utf-8")
    assert not gate.receipt_is_fresh(tmp_path, plan, 1001.0)
    path.write_text("not json", encoding="utf-8")
    assert not gate.receipt_is_fresh(tmp_path, plan, 1001.0)


def test_gate_version_invalidates_a_green_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = _plan()
    gate.write_receipt(tmp_path, plan, 1000.0)
    monkeypatch.setattr(gate, "GATE_VERSION", gate.GATE_VERSION + 1)

    assert not gate.receipt_is_fresh(tmp_path, plan, 1001.0)


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.ticks = 0
        self.on_sleep = lambda: None

    def monotonic(self) -> float:
        return self.now

    def monotonic_ns(self) -> int:
        self.ticks += 1
        return int(self.now * 1_000_000_000) + self.ticks

    def time(self) -> float:
        return 1000.0 + self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds
        self.on_sleep()


def _locked_ticket(state: Path, name: str) -> tuple[Path, int]:
    path = state / "queue" / f"{name}.ticket"
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return path, fd


def test_admission_reports_depth_and_waits_for_two_predecessors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    clock = FakeClock()
    monkeypatch.setattr(gate, "time", clock)
    owner = gate.Admission(tmp_path, 1.0)
    owner.__enter__()
    other, fd = _locked_ticket(tmp_path, "00000000000000000000-other")
    released = False

    def release() -> None:
        nonlocal released
        if clock.now >= 1.2 and not released:
            owner.__exit__()
            other.unlink()
            os.close(fd)
            released = True

    clock.on_sleep = release
    try:
        with gate.Admission(tmp_path, 1.0) as admitted:
            assert admitted.waited >= 1.2  # exceeds the old fixed one-run bound
            assert admitted.queue_depth == 3 and admitted.queue_position == 3
            assert admitted.wait_limit == 2.0
        assert "queue position 3/3" in capsys.readouterr().err
        assert list((tmp_path / "queue").glob("*.ticket")) == []
    finally:
        if not released:
            owner.__exit__()
            other.unlink(missing_ok=True)
            os.close(fd)


def test_admission_hard_ceiling_refuses_and_removes_its_ticket(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = FakeClock()
    monkeypatch.setattr(gate, "time", clock)
    monkeypatch.setattr(gate, "ADMISSION_MAX_WAIT_S", 1.5)
    with gate.Admission(tmp_path, 1.0):
        other, fd = _locked_ticket(tmp_path, "00000000000000000000-other")
        try:
            admission = gate.Admission(tmp_path, 1.0)
            with pytest.raises(gate.GateOutcome, match="admission_timeout") as raised, admission:
                pytest.fail("a held lock must never grant admission")
            assert raised.value.incomplete
            assert admission.waited == 1.5 and admission.wait_limit == 1.5
            assert admission.queue_depth == 3
            assert len(list((tmp_path / "queue").glob("*.ticket"))) == 2
        finally:
            other.unlink()
            os.close(fd)


def test_abandoned_ticket_does_not_block_a_live_gate(tmp_path: Path) -> None:
    queue = tmp_path / "queue"
    queue.mkdir()
    (queue / "00000000000000000000-abandoned.ticket").touch()
    with gate.Admission(tmp_path, 0.0) as admitted:
        assert admitted.queue_depth == 1 and admitted.queue_position == 1
        assert len(list(queue.glob("*.ticket"))) == 1
    assert list(queue.glob("*.ticket")) == []


def test_queue_scan_is_bounded_and_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    queue = tmp_path / "queue"
    queue.mkdir()
    other, fd = _locked_ticket(tmp_path, "old")
    monkeypatch.setattr(gate, "MAX_QUEUE_ENTRIES", 1)
    try:
        with pytest.raises(gate.GateOutcome, match="queue scan limit") as raised, gate.Admission(tmp_path, 0.0):
            pytest.fail("oversized live queue must not admit a gate")
        assert raised.value.incomplete
        assert list(queue.glob("*.ticket")) == [other]
    finally:
        os.close(fd)


def _fake_validation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clock: FakeClock) -> list[float]:
    deadlines = []
    monkeypatch.setattr(gate, "time", clock)
    monkeypatch.setattr(gate, "build_plan", lambda *_args: _plan())
    monkeypatch.setattr(gate, "state_dir", lambda *_args: tmp_path)

    class WaitedAdmission:
        waited = 500.0
        queue_depth = 2
        queue_position = 2
        wait_limit = gate.ADMISSION_WAIT_S

        def __init__(self, state, _wait_s, **_kwargs):
            self.waited = 500.0 if state == tmp_path else 0.0
            self._started = clock.now

        def __enter__(self):
            clock.now += self.waited
            return self

        def __exit__(self, *_args: object):
            pass

    real_shadow = gate.Shadow

    def popen(_command, **kwargs):
        kwargs["stdout"].write('{"selected_tests": []}\n')
        kwargs["stdout"].flush()
        return SimpleNamespace(wait=lambda **_kwargs: 0, returncode=0)

    def start_shadow(*args: object):
        shadow = real_shadow(*args)
        deadlines.append(shadow.deadline)
        return shadow

    def pre_commit(_plan, _root, _launcher, _config, deadline, **_kwargs):
        deadlines.append(deadline)
        clock.now += 2.0

    def pytest_stage(_plan, _root, _launcher, deadline, **_kwargs):
        deadlines.append(deadline)
        clock.now += 3.0
        return "passed"

    monkeypatch.setattr(gate, "Admission", WaitedAdmission)
    monkeypatch.setattr(
        gate,
        "subprocess",
        SimpleNamespace(Popen=popen, DEVNULL=subprocess.DEVNULL, TimeoutExpired=subprocess.TimeoutExpired),
    )
    monkeypatch.setattr(gate, "terminate_run", lambda *_args: True)
    monkeypatch.setattr(gate, "Shadow", start_shadow)
    monkeypatch.setattr(gate, "run_pre_commit_stage", pre_commit)
    monkeypatch.setattr(gate, "run_pytest_stage", pytest_stage)
    return deadlines


def test_run_and_shadow_budgets_start_after_admission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = FakeClock()
    deadlines = _fake_validation(tmp_path, monkeypatch, clock)
    budget = gate.Budget(10.0)
    event = {}
    gate.validate(gate.Update("local", "a" * 40, "remote", ZERO_SHA), tmp_path, "x", "y", event, budget)

    assert deadlines == [500.0 + gate.SHADOW_BUDGET_S, 510.0, 510.0]
    assert event["outcome"] == "green" and event["admission_wait_s"] == 500.0
    assert event["queue_depth"] == 2


def test_a_green_receipt_written_during_admission_is_reused_at_current_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = FakeClock()
    deadlines = _fake_validation(tmp_path, monkeypatch, clock)
    # The other gate completes at t=499, after this caller started waiting at t=0.
    gate.write_receipt(tmp_path, _plan(), 1499.0)
    event = {}
    gate.validate(gate.Update("local", "a" * 40, "remote", ZERO_SHA), tmp_path, "x", "y", event)

    assert deadlines == []  # neither stage nor shadow started
    assert event["detail"] == "valid receipt after admission"
    assert event["outcome"] == "green" and event["admission_wait_s"] == 500.0


def test_a_receipt_expired_while_waiting_cannot_be_reused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = FakeClock()
    deadlines = _fake_validation(tmp_path, monkeypatch, clock)
    gate.write_receipt(tmp_path, _plan(), 1000.0)
    monkeypatch.setattr(gate, "RECEIPT_TTL_S", 100.0)
    # Force queue entry, then let the real freshness check reject the now-expired receipt.
    real_fresh = gate.receipt_is_fresh
    monkeypatch.setattr(gate, "receipt_is_fresh", lambda *args: clock.now > 0 and real_fresh(*args))
    event = {}
    gate.validate(gate.Update("local", "a" * 40, "remote", ZERO_SHA), tmp_path, "x", "y", event)

    assert len(deadlines) == 3 and event["outcome"] == "green"
    assert "detail" not in event


@pytest.mark.parametrize("change", ["dirty_tree", "untracked_inputs", "different_plan"])
def test_inputs_changed_while_queued_cannot_reuse_a_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    clock = FakeClock()
    deadlines = _fake_validation(tmp_path, monkeypatch, clock)
    gate.write_receipt(tmp_path, _plan(), 1499.0)  # it becomes fresh during the wait

    def changed_plan(*_args: object):
        if clock.now == 0:
            return _plan()
        if change == "different_plan":
            return _plan(tree="d" * 40)
        raise gate.GateOutcome(change, "inputs changed while waiting")

    monkeypatch.setattr(gate, "build_plan", changed_plan)
    event = {}
    with pytest.raises(gate.GateOutcome) as raised:
        gate.validate(gate.Update("local", "a" * 40, "remote", ZERO_SHA), tmp_path, "x", "y", event)

    assert raised.value.reason == ("tree_mismatch" if change == "different_plan" else change)
    assert deadlines == [] and "outcome" not in event
    assert event["admission_wait_s"] == 500.0 and event["queue_depth"] == 2


def test_four_process_pushers_all_validate_without_wait_consuming_the_run_budget(tmp_path: Path) -> None:
    """Actual flocks/processes, four distinct passing plans, shortened bounds and simulated stages."""
    driver = textwrap.dedent(
        """\
        import importlib.util, sys, time
        from pathlib import Path
        spec = importlib.util.spec_from_file_location('gate', sys.argv[1])
        gate = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = gate
        spec.loader.exec_module(gate)
        root = Path(sys.argv[2])
        number = sys.argv[3]
        plan = gate.Plan(number * 40, 'a' * 40, 'b' * 40, 'v-test', ('tests/test_ok.py',), (), ())
        gate.git_ok = lambda *args, **kwargs: str(root)
        gate.build_plan = lambda *args: plan
        gate.state_dir = lambda *args: root / 'state'
        class Shadow:
            def __init__(self, *args):
                pass
            def finish(self):
                return {'status': 'recorded'}
            def abandon(self):
                pass
        gate.Shadow = Shadow
        def pre_commit(plan, root, launcher, config, deadline, **kwargs):
            (root / ('pre-' + number)).write_text('ran')
            if deadline - time.monotonic() < 2.5:
                raise gate.GateOutcome('validation_incomplete', 'waiting consumed budget', incomplete=True)
        def pytest_stage(plan, root, launcher, deadline, **kwargs):
            time.sleep(2.0)
            if time.monotonic() >= deadline:
                raise gate.GateOutcome('validation_incomplete', 'pytest ran out of budget', incomplete=True)
            (root / ('pytest-' + number)).write_text('passed')
            return '1 simulated test passed'
        gate.run_pre_commit_stage = pre_commit
        gate.run_pytest_stage = pytest_stage
        updates = f'refs/heads/p{number} {plan.head} refs/heads/p{number} {gate.ZERO_SHA}\\n'
        sys.exit(gate.main(['--launcher', 'fixture', '--config', 'fixture'], stdin=updates))
        """
    )
    state = tmp_path / "state"
    state.mkdir()
    processes = []
    try:
        # Hold admission until all four have published their live tickets. It models an existing
        # (older, ticketless) gate and makes concurrent queue depth deterministic.
        with (state / "admission.lock").open("w") as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            for number in range(1, 5):
                processes.append(
                    subprocess.Popen(
                        [sys.executable, "-c", driver, str(GATE_PATH), str(tmp_path), str(number)],
                        cwd=tmp_path,
                        env=_env({"LU_PRE_PUSH_GATE_RUN_BUDGET_S": "3", "LU_PRE_PUSH_GATE_ADMISSION_WAIT_S": "4"}),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                )

            def four_registered() -> bool:
                if len(list((state / "queue").glob("*.ticket"))) == 4:
                    return True
                assert all(process.poll() is None for process in processes), "a pusher exited before admission"
                return False

            wait_until(four_registered, timeout=10.0, interval=0.02, message="four pushers registering")
        for process in processes:
            stdout, stderr = process.communicate(timeout=30)
            assert process.returncode == 0, stdout + stderr
            assert "queue position" in stderr
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
    rows = [
        row
        for line in (state / "measurements.jsonl").read_text().splitlines()
        if (row := json.loads(line)).get("phase") != "BEGIN"
    ]
    assert len(rows) == 4 and all(row["outcome"] == "green" for row in rows)
    assert max(row["admission_wait_s"] for row in rows) > 4.0  # old fixed wait would refuse
    assert max(row["queue_depth"] for row in rows) >= 4
    assert all(row["admission_wait_s"] <= row["admission_wait_limit_s"] for row in rows)
    assert len(list(tmp_path.glob("pre-*"))) == len(list(tmp_path.glob("pytest-*"))) == 4
    assert len(list((state / "receipts").glob("*.json"))) == 4
    assert list((state / "queue").glob("*.ticket")) == []


# ---- bounded resources: validation_incomplete, never green ------------------------------------------------


def test_time_budget_exhaustion_is_validation_incomplete_and_leaves_no_receipt(repo: Path) -> None:
    _write(repo, "tests/test_slow.py", "import time\n\n\ndef test_slow():\n    time.sleep(120)\n")
    _commit(repo, "slow", "tests/test_slow.py")

    result = _run_gate(repo, extra_env={"LU_PRE_PUSH_GATE_RUN_BUDGET_S": "4"})

    assert result.returncode == gate.EXIT_INCOMPLETE
    verdict = _verdict(result)
    assert verdict["outcome"] == "validation_incomplete"
    assert "NOT green" in result.stderr
    assert _receipts(repo) == []
    assert _measurements(repo)[-1]["outcome"] == "validation_incomplete"


def test_a_second_gate_waits_for_admission_then_reports_validation_incomplete(repo: Path) -> None:
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")
    state = repo / ".git/lu-pre-push-gate"
    state.mkdir(parents=True)
    with (state / "admission.lock").open("w") as held:
        fcntl.flock(held, fcntl.LOCK_EX)

        result = _run_gate(repo, extra_env={"LU_PRE_PUSH_GATE_ADMISSION_WAIT_S": "1"})

    assert result.returncode == gate.EXIT_INCOMPLETE
    assert "admission_timeout" in result.stderr
    row = _measurements(repo)[-1]
    assert row["detail"].startswith("admission_timeout:")
    assert result.stderr.rstrip("\n").endswith(row["detail"])
    assert row["queue_depth"] == 2 and row["queue_position"] == 2
    assert row["admission_wait_s"] >= 1.0
    assert _receipts(repo) == []


def test_environment_can_shorten_but_never_lengthen_a_bound(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_BOUND", "99999")
    assert gate.bounded("X_BOUND", 600.0) == 600.0
    monkeypatch.setenv("X_BOUND", "5")
    assert gate.bounded("X_BOUND", 600.0) == 5.0
    monkeypatch.setenv("X_BOUND", "nonsense")
    assert gate.bounded("X_BOUND", 600.0) == 600.0


# ---- exact outgoing commit --------------------------------------------------------------------------------


def test_dirty_tracked_tree_is_refused(repo: Path) -> None:
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")
    _write(repo, "tests/test_new.py", RED_TEST)  # uncommitted: not what would be pushed

    result = _run_gate(repo)

    assert _verdict(result)["reason"] == "dirty_tree"
    assert result.returncode == gate.EXIT_REFUSED


def test_pushing_a_commit_that_is_not_checked_out_is_refused(repo: Path) -> None:
    _write(repo, "first.txt", "x\n")
    first = _commit(repo, "first", "first.txt")
    _write(repo, "later.txt", "x\n")
    _commit(repo, "later", "later.txt")
    update = f"refs/heads/feature {first} refs/heads/feature {ZERO_SHA}\n"

    result = subprocess.run(
        [str(PYTHON), str(repo / ".githooks/pre_push_gate.py"), "--launcher", "x", "--config", "y"],
        capture_output=True,
        check=False,
        cwd=repo,
        input=update,
        text=True,
        timeout=60,
        env=_env(),
    )

    assert _verdict(result)["reason"] == "tree_mismatch"


def test_deletes_and_tag_pushes_are_not_validated(repo: Path) -> None:
    updates = f"(delete) {ZERO_SHA} refs/heads/old {'a' * 40}\nrefs/tags/v1 {'b' * 40} refs/tags/v1 {ZERO_SHA}\n"

    result = subprocess.run(
        [str(PYTHON), str(repo / ".githooks/pre_push_gate.py"), "--launcher", "x", "--config", "y"],
        capture_output=True,
        check=False,
        cwd=repo,
        input=updates,
        text=True,
        timeout=60,
        env=_env(),
    )

    assert result.returncode == 0


def test_unreadable_registry_is_validation_incomplete(repo: Path) -> None:
    (repo / "tests/test_repo_wide_marker_invariant.py").unlink()
    _commit(repo, "drop registry", "-A")

    result = _run_gate(repo)

    assert result.returncode == gate.EXIT_INCOMPLETE
    assert _verdict(result)["reason"] == "registry_unavailable"


# ---- registry ---------------------------------------------------------------------------------------------


def test_registry_is_deduplicated_and_versioned(repo: Path) -> None:
    nodes, version = gate.load_registry(repo)

    # The function entry inside an already-selected module is dropped.
    assert nodes == ("tests/test_invariant.py", "tests/test_scanner.py::test_scan")
    assert version.startswith(f"v{gate.GATE_VERSION}-")

    _write(repo, "tests/test_repo_wide_marker_invariant.py", REGISTRY.replace("})", '"tests/test_other.py"})', 1))
    assert gate.load_registry(repo)[1] != version


def test_dedupe_node_ids_keeps_the_broader_selection_and_sorts() -> None:
    assert gate.dedupe_node_ids(["b.py::t", "a.py", "a.py::t", "b.py::t", "a.py"]) == ("a.py", "b.py::t")


def test_the_real_registry_loads_by_ast_and_matches_the_module() -> None:
    from tests import test_repo_wide_marker_invariant as marker

    nodes, _ = gate.load_registry(REPO_ROOT)

    expected = gate.dedupe_node_ids(
        [gate.pytest_node_id(node) for node in (*marker.KNOWN_REPO_WIDE_MODULES, *marker.KNOWN_REPO_WIDE_FUNCTIONS)]
    )
    assert nodes == expected


def test_invalid_ref_update_lines_are_a_typed_failure() -> None:
    with pytest.raises(gate.GateOutcome) as caught:
        gate.parse_updates("only three fields\n")
    assert caught.value.reason == "invalid_ref_updates"


def test_failing_node_ids_are_parsed_from_the_pytest_summary() -> None:
    output = "FAILED tests/a.py::test_x - assert 0\nERROR tests/b.py::test_y\nFAILED tests/a.py::test_x - assert 0\n"

    assert gate.failing_node_ids(output) == ("tests/a.py::test_x", "tests/b.py::test_y")


# ---- shadow importer-closure selection: recorded, never blocking -----------------------------------------


def _install_shadow(repo: Path, body: str) -> None:
    _write(repo, "scripts/__init__.py", "")
    _write(repo, "scripts/ci/__init__.py", "")
    _write(repo, "scripts/ci/pre_push_shadow.py", body)
    _git(repo, "add", "scripts")
    _git(repo, "commit", "-m", "shadow")


def test_shadow_selection_is_recorded_and_does_not_change_the_verdict(repo: Path) -> None:
    _install_shadow(
        repo,
        "import json\nprint(json.dumps({'components': ['harness'], 'fallback_reasons': [], "
        "'selected_tests': ['tests/test_x.py']}))\n",
    )
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")

    result = _run_gate(repo)

    assert result.returncode == 0, result.stderr
    shadow = _measurements(repo)[-1]["shadow"]
    assert shadow["status"] == "recorded" and shadow["components"] == ["harness"] and shadow["selected_count"] == 1


@pytest.mark.parametrize(
    "body",
    ["raise SystemExit(3)\n", "print('not json')\n", "import time\ntime.sleep(60)\n"],
    ids=["crash", "garbage", "hang"],
)
def test_a_broken_shadow_never_blocks_a_green_push(
    repo: Path, body: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_shadow(repo, body)
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")
    # The shadow budget is a module constant, so drive validate() in-process with it shortened.
    monkeypatch.setattr(gate, "SHADOW_BUDGET_S", 2.0)
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "pre-commit-cache"))
    monkeypatch.chdir(repo)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    update = gate.Update("refs/heads/feature", head, "refs/heads/feature", ZERO_SHA)
    event: dict[str, object] = {}

    gate.validate(
        update, repo, str(repo / "scripts/pre_commit/project_python.sh"), str(repo / ".pre-commit-config.yaml"), event
    )

    assert event["outcome"] == "green"
    assert event["shadow"]["status"] == "unavailable"


def test_shadow_selector_unions_the_tests_of_every_affected_component(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.ci import components, pre_push_shadow

    monkeypatch.setattr(components, "load_manifest", lambda: {})
    monkeypatch.setattr(
        components,
        "affected",
        lambda paths, manifest: {
            "components": ["a", "b"],
            "fallback_reasons": ["dynamic-unresolved"],
            "changed_paths": len(paths),
        },
    )
    monkeypatch.setattr(
        components, "test_files", lambda component, manifest: [f"tests/test_{component}.py", "tests/test_shared.py"]
    )

    selection = pre_push_shadow.shadow_selection(["scripts/x.py"])

    assert selection == {
        "components": ["a", "b"],
        "fallback_reasons": ["dynamic-unresolved"],
        "changed_paths": 1,
        "selected_tests": ["tests/test_a.py", "tests/test_b.py", "tests/test_shared.py"],
    }


def test_empty_registry_literals_load_as_an_empty_registry(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "tests/test_repo_wide_marker_invariant.py",
        "KNOWN_REPO_WIDE_MODULES = frozenset()\nKNOWN_REPO_WIDE_FUNCTIONS = ()\n",
    )

    assert gate.load_registry(tmp_path)[0] == ()


def test_admission_wait_covers_one_full_gate_run() -> None:
    assert gate.ADMISSION_WAIT_S >= gate.RUN_BUDGET_S + gate.SHADOW_BUDGET_S + gate.CLEANUP_BUDGET_S


def test_auto_finalize_push_timeout_covers_the_queue_ceiling() -> None:
    from scripts import delegate

    gate_worst_case = gate.ADMISSION_MAX_WAIT_S + gate.ADMISSION_WAIT_S
    assert gate_worst_case + delegate.DEFAULT_NETWORK_GIT_TIMEOUT_S <= delegate.AUTO_FINALIZE_PUSH_TIMEOUT_S


def test_worker_closeout_text_carries_the_gate_and_merge_main_rules() -> None:
    from scripts import delegate

    source = Path(delegate.__file__).read_text(encoding="utf-8")
    assert "validation_incomplete" in source and "git merge-tree" in source


def test_registry_class_methods_become_pytest_node_ids() -> None:
    assert gate.pytest_node_id("tests/t.py::TestA.test_b") == "tests/t.py::TestA::test_b"
    assert gate.pytest_node_id("tests/t.py::test_b") == "tests/t.py::test_b"
    assert gate.pytest_node_id("tests/t.py") == "tests/t.py"


def test_every_real_registry_node_id_is_collectable() -> None:
    """The registry is only as good as pytest's ability to resolve each id it names."""
    nodes, _ = gate.load_registry(REPO_ROOT)

    result = subprocess.run(
        [str(PYTHON), "-m", "pytest", *nodes, "--collect-only", "-q", "-p", "no:cacheprovider"],
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
        env=_env(),
        text=True,
        timeout=300,
    )

    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-2000:]


def test_a_pytest_run_without_a_verdict_is_validation_incomplete(repo: Path) -> None:
    _write(repo, "tests/test_repo_wide_marker_invariant.py", REGISTRY.replace("::test_scan", "::test_missing"))
    _commit(repo, "registry names a test that does not exist", "tests")

    result = _run_gate(repo)

    assert result.returncode == gate.EXIT_INCOMPLETE
    assert _verdict(result)["reason"] == "pytest_error"


@pytest.mark.parametrize("ancestor_config", [False, True])
def test_modules_over_the_cost_cap_are_deferred_to_ci_and_recorded(repo: Path, ancestor_config: bool) -> None:
    if ancestor_config:
        _write(repo.parent, "pyproject.toml", "[tool.pytest.ini_options]\n")
    # A conftest breaks the registered module without changing the module itself.
    _write(
        repo,
        "tests/conftest.py",
        "def pytest_runtest_setup(item):\n"
        "    assert not item.nodeid.startswith('tests/test_invariant.py'), 'invariant broken'\n",
    )
    _commit(repo, "break the registered module from a conftest", "tests/conftest.py")
    control = _run_gate(repo)
    assert control.returncode == gate.EXIT_REFUSED  # without a cost record the module runs and fails

    _write(repo, gate.DURATIONS_FILE, json.dumps({"tests/test_invariant.py": gate.HEAVY_MODULE_S + 1}))
    _commit(repo, "record its CI cost", gate.DURATIONS_FILE)
    result = _run_gate(repo)

    assert result.returncode == 0, result.stderr
    assert _measurements(repo)[-1]["deferred_to_ci"] == ["tests/test_invariant.py"]


def test_cost_deferral_only_touches_whole_modules_and_tolerates_missing_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    nodes = ("tests/a.py", "tests/b.py::test_fast", "tests/c.py")
    _write(tmp_path, gate.DURATIONS_FILE, json.dumps({"tests/a.py": 500, "tests/b.py": 900, "tests/c.py": 5}))

    assert gate.defer_to_ci(nodes, tmp_path) == (("tests/b.py::test_fast", "tests/c.py"), ("tests/a.py",))
    assert gate.defer_to_ci(nodes, tmp_path / "nowhere") == (nodes, ())
    _write(tmp_path, gate.DURATIONS_FILE, "[1, 2]")
    assert gate.defer_to_ci(nodes, tmp_path) == (nodes, ())
    deferred = "tests/test_synthetic.py"
    monkeypatch.setattr(gate, "CI_DEFERRED_MODULES", frozenset({deferred}))
    assert gate.defer_to_ci((deferred, deferred + "::test_example"), tmp_path) == (
        (deferred + "::test_example",),
        (deferred,),
    )
    _write(tmp_path, gate.DURATIONS_FILE, json.dumps({deferred: 0}))
    assert gate.defer_to_ci((deferred,), tmp_path) == ((deferred,), ())


def test_deferral_changes_the_receipt_key(tmp_path: Path) -> None:
    plan = _plan()
    gate.write_receipt(tmp_path, plan, 1000.0)

    assert not gate.receipt_is_fresh(tmp_path, _plan(deferred_to_ci=("tests/x.py",)), 1001.0)


def test_the_real_registry_fits_the_run_budget_once_heavy_modules_are_deferred() -> None:
    nodes, _ = gate.load_registry(REPO_ROOT)
    run, deferred = gate.defer_to_ci(nodes, REPO_ROOT)
    durations = json.loads((REPO_ROOT / gate.DURATIONS_FILE).read_text(encoding="utf-8"))

    assert deferred, "the docs lookup modules are expected to be deferred"
    # The registry runs in the pytest stage, so it must fit that stage's own allowance (#10642).
    assert sum(durations.get(n, 0.0) for n in run if "::" not in n) <= gate.STAGE_BUDGET_S


def test_entries_that_read_a_tree_the_sparse_worktree_omits_are_deferred_only_there(repo: Path) -> None:
    node = gate.SPARSE_TREE_NODES["curriculum"][0]
    nodes = (node, "tests/other.py")
    _write(repo, "curriculum/plans/a.yaml", "a: 1\n")
    _write(repo, "curriculum/kept.yaml", "k: 1\n")
    _commit(repo, "curriculum", "curriculum")

    assert gate.defer_to_ci(nodes, repo) == (nodes, ())  # full checkout: the entry runs
    _git(repo, "sparse-checkout", "set", "--no-cone", "/*", "!/curriculum/plans/")
    assert not (repo / "curriculum/plans/a.yaml").exists() and (repo / "curriculum/kept.yaml").exists()
    assert gate.defer_to_ci(nodes, repo) == (("tests/other.py",), (node,))  # part of the tree is unmaterialized
    _git(repo, "sparse-checkout", "disable")
    assert gate.defer_to_ci(nodes, repo) == (nodes, ())


def test_sparse_deferrals_name_real_registry_entries() -> None:
    registry, _ = gate.load_registry(REPO_ROOT)

    for tree_nodes in gate.SPARSE_TREE_NODES.values():
        assert set(tree_nodes) <= set(registry)


def test_pytest_defaults_to_bounded_parallelism_kept_by_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(gate.MAX_TEST_PROCESSES_ENV, raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.setattr(gate.importlib.util, "find_spec", lambda name: object())
    assert gate.test_process_limit() == 4
    assert gate.parallel_options() == ["-n", "4", "--dist", "loadfile"]


def test_pytest_uses_configured_parallelism_kept_by_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.setenv(gate.MAX_TEST_PROCESSES_ENV, "3")
    monkeypatch.setattr(gate.importlib.util, "find_spec", lambda name: object())
    assert gate.parallel_options() == ["-n", "3", "--dist", "loadfile"]
    monkeypatch.setattr(gate.importlib.util, "find_spec", lambda name: None)
    assert gate.parallel_options() == []
    monkeypatch.setenv(gate.MAX_TEST_PROCESSES_ENV, "1")
    assert gate.parallel_options() == []


@pytest.mark.parametrize("value,expected", [(None, 2), ("6", 2), ("2", 2), ("1", 1)])
def test_pytest_preserves_dispatch_process_clamp(
    value: str | None, expected: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "gate-test")
    monkeypatch.setattr(gate.importlib.util, "find_spec", lambda name: object())
    if value is None:
        monkeypatch.delenv(gate.MAX_TEST_PROCESSES_ENV, raising=False)
    else:
        monkeypatch.setenv(gate.MAX_TEST_PROCESSES_ENV, value)
    assert gate.test_process_limit() == (4 if value is None else int(value))
    assert gate.parallel_options() == ([] if expected == 1 else ["-n", "2", "--dist", "loadfile"])


@pytest.mark.parametrize(
    "value,dispatch,xdist,requested,effective",
    [
        (None, "", True, 4, 4),
        (None, "gate-test", True, 4, 2),
        (None, "  ", True, 4, 4),
        ("3", "", True, 3, 3),
        ("6", "gate-test", True, 6, 2),
        ("1", "gate-test", True, 1, 1),
        (None, "gate-test", False, 4, 1),
    ],
)
@pytest.mark.parametrize("ending", ["green", "red", "timeout"])
def test_pytest_measurement_records_requested_and_effective_invocation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    value: str | None,
    dispatch: str,
    xdist: bool,
    requested: int,
    effective: int,
    ending: str,
) -> None:
    if value is None:
        monkeypatch.delenv(gate.MAX_TEST_PROCESSES_ENV, raising=False)
    else:
        monkeypatch.setenv(gate.MAX_TEST_PROCESSES_ENV, value)
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", dispatch)
    monkeypatch.setattr(gate.importlib.util, "find_spec", lambda name: object() if xdist else None)
    monkeypatch.setattr(gate, "state_dir", lambda _root: tmp_path / "state")
    seen = []

    def run(command: list[str], **kwargs: object) -> tuple[int, str]:
        seen.append(command)
        assert kwargs["diagnostics"]["requested_test_processes"] == requested
        assert kwargs["diagnostics"]["effective_test_processes"] == effective
        if ending == "timeout":
            raise gate.GateOutcome("time_budget_exhausted", "pytest stage timed out", incomplete=True)
        return (1, "FAILED tests/test_a.py::test_bad") if ending == "red" else (0, "1 passed in 0.1s")

    monkeypatch.setattr(gate, "run_bounded", run)
    event = {}
    if ending == "green":
        with gate.stage_measurement(event, "pytest") as diagnostics:
            assert (
                gate.run_pytest_stage(_plan(), tmp_path, "launcher", time.monotonic() + 30, diagnostics=diagnostics)
                == "1 passed in 0.1s; 1 passed in 0.1s"
            )
    else:
        with pytest.raises(gate.GateOutcome):
            with gate.stage_measurement(event, "pytest") as diagnostics:
                gate.run_pytest_stage(_plan(), tmp_path, "launcher", time.monotonic() + 30, diagnostics=diagnostics)
    assert len(seen) == (2 if ending == "green" else 1)
    for command, dist in zip(seen, ("worksteal", "loadfile"), strict=False):
        if effective == 1:
            assert "-n" not in command and "--dist" not in command
        else:
            assert command[-4:] == ["-n", str(effective), "--dist", dist]
    row = event["stages"]["pytest"]
    assert row["requested_test_processes"] == requested
    assert row["effective_test_processes"] == effective
    assert row["pytest_invocations"] == [{"dist": "worksteal", "nodes": 1}, {"dist": "loadfile", "nodes": 1}]
    assert row["outcome"] == {"green": "green", "red": "refused", "timeout": "validation_incomplete"}[ending]


@pytest.mark.parametrize(
    "value",
    ["", "0", "-1", "1.5", "nan", "inf", "auto", " 3", "+3", "٣", "9" * 5000],
    ids=["empty", "zero", "negative", "decimal", "nan", "infinite", "auto", "space", "sign", "unicode", "oversized"],
)
def test_invalid_process_configuration_refuses_even_without_xdist(value: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(gate.MAX_TEST_PROCESSES_ENV, value)
    monkeypatch.setattr(gate.importlib.util, "find_spec", lambda name: None)
    with pytest.raises(gate.GateOutcome) as raised:
        gate.parallel_options()
    assert raised.value.reason == "invalid_configuration"
    assert raised.value.incomplete
    assert raised.value.detail == f"{gate.MAX_TEST_PROCESSES_ENV} must be a positive integer"


# ---- #10610: changed whole files are distributed per test, not pinned to one worker -------------------


def test_pytest_invocations_split_changed_files_from_registered_invariants() -> None:
    plan = _plan(
        registry_nodes=(
            "tests/test_a.py",
            "tests/test_b.py::test_registered",  # subsumed by the changed whole file
            "tests/test_c.py::TestX::test_y",
        ),
        changed_tests=("tests/test_b.py", "tests/test_d.py"),
    )
    invocations = gate.pytest_invocations(plan)
    assert invocations == (
        (("tests/test_b.py", "tests/test_d.py"), "worksteal"),
        (("tests/test_a.py", "tests/test_c.py::TestX::test_y"), "loadfile"),
    )
    selected = [node for nodes, _dist in invocations for node in nodes]
    assert sorted(selected) == list(plan.node_ids) and len(selected) == len(set(selected))
    # An empty side is not invoked at all.
    assert gate.pytest_invocations(_plan(changed_tests=())) == ((("tests/test_a.py",), "loadfile"),)
    assert gate.pytest_invocations(_plan(registry_nodes=())) == ((("tests/test_b.py",), "worksteal"),)


def test_changed_whole_file_is_never_passed_as_a_loadfile_unit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.setenv(gate.MAX_TEST_PROCESSES_ENV, "4")
    monkeypatch.setattr(gate.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(gate, "state_dir", lambda _root: tmp_path / "state")
    plan = _plan(
        registry_nodes=("tests/test_a.py", "tests/test_slow.py::test_registered"),
        changed_tests=("tests/test_slow.py",),
    )
    commands = []

    def run(command: list[str], **kwargs: object) -> tuple[int, str]:
        commands.append(command)
        assert kwargs["deadline"] == deadline  # both runs share the one stage deadline
        return 0, "1 passed in 0.1s"

    monkeypatch.setattr(gate, "run_bounded", run)
    deadline = time.monotonic() + 30
    assert gate.run_pytest_stage(plan, tmp_path, "launcher", deadline) == "1 passed in 0.1s; 1 passed in 0.1s"
    by_dist = {command[command.index("--dist") + 1]: command for command in commands}
    assert set(by_dist) == {"worksteal", "loadfile"}
    assert "tests/test_slow.py" in by_dist["worksteal"]
    assert not any(arg.startswith("tests/test_slow.py") for arg in by_dist["loadfile"])
    executed = [arg for command in commands for arg in command if arg.startswith("tests/")]
    assert sorted(executed) == list(plan.node_ids)


@pytest.mark.parametrize(
    "codes,expected",
    [
        ((5, 0), "green"),  # a changed file collecting nothing, as in the former single run
        ((0, 5), "green"),
        ((5, 5), "pytest_error"),  # the selection as a whole ran nothing
        ((0, 2), "pytest_error"),  # a later usage error never yields green
        ((0, 1), "tests_failed"),
        ((1, None), "tests_failed"),  # the first refusal stops the stage
        ((4, None), "pytest_error"),
    ],
)
def test_split_pytest_stage_is_green_only_when_every_run_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, codes: tuple[int, int | None], expected: str
) -> None:
    monkeypatch.setattr(gate, "state_dir", lambda _root: tmp_path / "state")
    calls = []

    def run(command: list[str], **_kwargs: object) -> tuple[int, str]:
        code = codes[len(calls)]
        assert code is not None, "a run started after the stage was already refused"
        calls.append(command)
        if code == 0:
            return 0, "3 passed in 0.1s"
        return code, "FAILED tests/test_b.py::test_bad" if code == 1 else f"exit {code}"

    monkeypatch.setattr(gate, "run_bounded", run)
    if expected == "green":
        assert gate.run_pytest_stage(_plan(), tmp_path, "launcher", time.monotonic() + 30) == "3 passed in 0.1s"
        return
    with pytest.raises(gate.GateOutcome) as raised:
        gate.run_pytest_stage(_plan(), tmp_path, "launcher", time.monotonic() + 30)
    assert raised.value.reason == expected
    assert raised.value.incomplete == (expected == "pytest_error")
    if expected == "tests_failed":
        assert raised.value.failing == ("tests/test_b.py::test_bad",)


WORKER_RECORD_TEST = textwrap.dedent(
    """\
    import os
    from pathlib import Path

    def _record(name):
        Path(os.environ['GATE_WORKER_RECORD'], name).write_text(os.environ.get('PYTEST_XDIST_WORKER', 'main'))

    def test_first():
        _record('first')

    def test_second():
        _record('second')
    """
)


def test_changed_whole_file_runs_on_more_than_one_worker(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("xdist")
    _write(repo, "tests/test_changed_slow.py", WORKER_RECORD_TEST)
    _commit(repo, "changed whole file", "tests/test_changed_slow.py")
    record = tmp_path / "workers"
    record.mkdir()
    monkeypatch.setenv("GATE_WORKER_RECORD", str(record))
    monkeypatch.setenv(gate.MAX_TEST_PROCESSES_ENV, "2")
    plan = _plan(registry_nodes=("tests/test_invariant.py",), changed_tests=("tests/test_changed_slow.py",))
    result = gate.run_pytest_stage(
        plan, repo, str(repo / "scripts/pre_commit/project_python.sh"), time.monotonic() + 120
    )
    assert re.fullmatch(r"2 passed in \d+(?:\.\d+)?s; 1 passed in \d+(?:\.\d+)?s", result), result
    # Under ``--dist loadfile`` both tests of the changed file would share one worker.
    workers = {path.name: path.read_text() for path in record.iterdir()}
    assert set(workers) == {"first", "second"}
    assert workers["first"] != workers["second"] and set(workers.values()) <= {"gw0", "gw1"}


def test_invalid_process_configuration_cannot_reuse_a_green_receipt(repo: Path) -> None:
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")
    assert _run_gate(repo).returncode == 0
    receipts = _receipts(repo)
    assert receipts
    result = _run_gate(repo, extra_env={gate.MAX_TEST_PROCESSES_ENV: "invalid"})
    assert result.returncode == gate.EXIT_INCOMPLETE
    assert _verdict(result)["reason"] == "invalid_configuration"
    assert _receipts(repo) == receipts


def test_explicit_ci_deferrals_name_registered_modules_without_timings() -> None:
    registry, _ = gate.load_registry(REPO_ROOT)
    assert isinstance(gate.CI_DEFERRED_MODULES, frozenset)
    assert set(registry) >= gate.CI_DEFERRED_MODULES
    assert all("::" not in module for module in gate.CI_DEFERRED_MODULES)


def test_public_gate_material_omits_operational_measurements() -> None:
    text = GATE_PATH.read_text(encoding="utf-8") + (REPO_ROOT / "docs/runbooks/pre-push-gate.md").read_text(
        encoding="utf-8"
    )
    assert not re.search(r"(?i)load.average|cpu.seconds|loaded.host|measured[^\n]*\d", text)
    assert not re.search(r"(?i)(?:\d+|two) (?:test |xdist )?workers", text)
    assert not re.search(r"(?i)\b(?:cpu|minutes?|cores?|capacity)\b", text)
    assert not re.search(r"\b\d+(?:\.\d+)? ?s\b", text)


def test_auto_finalize_timeout_comment_omits_gate_timings() -> None:
    from scripts import delegate

    source = Path(delegate.__file__).read_text(encoding="utf-8")
    comment = re.search(r"# The auto-finalize push runs the pre-push gate.*\n(?:#.*\n)*?(?=\w)", source)
    assert comment is not None
    assert not re.search(r"\b\d+(?:\.\d+)? ?s\b", comment.group(0))


# ---- review round 1: every ref update, sparse tests, untracked inputs, bounded cleanup -----------------------


def _run_gate_with(repo: Path, updates: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(PYTHON),
            str(repo / ".githooks/pre_push_gate.py"),
            "--launcher",
            str(repo / "scripts/pre_commit/project_python.sh"),
            "--config",
            str(repo / ".pre-commit-config.yaml"),
        ],
        capture_output=True,
        check=False,
        cwd=repo,
        input=updates,
        text=True,
        timeout=120,
        env=_env({"PRE_COMMIT_HOME": str(repo.parent / "pre-commit-cache")}),
    )


def test_every_ref_update_is_validated_with_its_own_base(repo: Path) -> None:
    _write(repo, "tests/test_a_red.py", RED_TEST)
    first = _commit(repo, "red test", "tests/test_a_red.py")
    _write(repo, "tests/test_b.py", GREEN_TEST)
    head = _commit(repo, "green test", "tests/test_b.py")
    # The first update's range holds only the green test; the second's also holds the red one.
    updates = (
        f"refs/heads/feature {head} refs/heads/narrow {first}\nrefs/heads/feature {head} refs/heads/wide {ZERO_SHA}\n"
    )

    result = _run_gate_with(repo, updates)

    assert result.returncode == gate.EXIT_REFUSED, result.stderr
    assert "tests/test_a_red.py::test_broken" in _verdict(result)["failing"]
    rows = _measurements(repo)
    assert [row["outcome"] for row in rows] == ["green", "refused"]
    assert rows[0]["base"] != rows[1]["base"]
    assert len(_receipts(repo)) == 1  # only the green range left a receipt, keyed by its own base


def test_receipts_of_two_ranges_with_one_head_do_not_overwrite_each_other(tmp_path: Path) -> None:
    narrow, wide = _plan(base="a" * 40), _plan(base="b" * 40)

    assert gate.receipt_path(tmp_path, narrow) != gate.receipt_path(tmp_path, wide)


def test_one_run_budget_covers_the_whole_push_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = FakeClock()
    monkeypatch.setattr(gate, "time", clock)
    budget = gate.Budget(600.0)
    first = budget.after_admission(500.0)
    clock.now += 100.0

    assert budget.deadline == first  # execution still consumes the shared budget
    clock.now += 500.0  # a later ref queues again
    assert budget.after_admission(500.0) - clock.now == 500.0
    assert budget.deadline == first + 500.0  # waiting consumes none of the remaining execution budget


def test_a_changed_test_the_sparse_worktree_lacks_is_validation_incomplete(repo: Path) -> None:
    _write(repo, "tests/test_new.py", RED_TEST)
    _commit(repo, "red test", "tests/test_new.py")
    _git(repo, "sparse-checkout", "set", "--no-cone", "/*", "!/tests/test_new.py")
    assert not (repo / "tests/test_new.py").exists()

    result = _run_gate(repo)

    assert result.returncode == gate.EXIT_INCOMPLETE
    verdict = _verdict(result)
    assert verdict["outcome"] == "validation_incomplete"
    assert verdict["reason"] == "changed_tests_unmaterialized"
    assert "tests/test_new.py" in result.stderr
    assert _receipts(repo) == []


@pytest.mark.parametrize("ignored", [False, True], ids=["untracked", "ignored"])
def test_an_untracked_python_overlay_is_refused_before_execution(repo: Path, ignored: bool) -> None:
    if ignored:
        _write(repo, ".gitignore", "conftest.py\n")
        _commit(repo, "ignore overlays", ".gitignore")
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green test", "tests/test_new.py")
    _write(repo, "tests/conftest.py", "def pytest_collection_modifyitems(items):\n    items.clear()\n")

    result = _run_gate(repo)

    assert result.returncode == gate.EXIT_REFUSED
    assert _verdict(result)["reason"] == "untracked_inputs"
    assert "tests/conftest.py" in result.stderr
    assert _receipts(repo) == []


def test_untracked_overlay_blocks_receipt_reuse_and_unrelated_scratch_does_not(repo: Path) -> None:
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green test", "tests/test_new.py")
    _write(repo, "notes.txt", "scratch\n")
    assert _run_gate(repo).returncode == 0
    assert len(_receipts(repo)) == 1

    _write(repo, "conftest.py", "")

    assert _verdict(_run_gate(repo))["reason"] == "untracked_inputs"


def _gone(pid: int) -> bool:
    def exited() -> bool:
        try:
            state = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()[0]
        except OSError:
            return True
        return state == "Z"

    try:
        wait_until(exited, timeout=5.0, interval=0.05, message=f"process {pid} exiting")
    except AssertionError:
        return False
    return True


_DETACHED_CHILD = (
    "import os, subprocess, sys, time\n"
    "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)'], start_new_session=True)\n"
    "open(sys.argv[1], 'w').write(str(child.pid))\n"
)


@pytest.mark.parametrize("hang", [False, True], ids=["command-exits", "command-times-out"])
def test_a_detached_descendant_holding_the_output_cannot_stall_or_survive_the_gate(tmp_path: Path, hang: bool) -> None:
    pid_file = tmp_path / "child.pid"
    script = _DETACHED_CHILD + ("time.sleep(300)\n" if hang else "")
    started = time.monotonic()

    if hang:
        with pytest.raises(gate.GateOutcome) as raised:
            gate.run_bounded(
                [sys.executable, "-c", script, str(pid_file)],
                cwd=tmp_path,
                deadline=time.monotonic() + 2.0,
                label="probe",
            )
        assert raised.value.incomplete
    else:
        code, _ = gate.run_bounded(
            [sys.executable, "-c", script, str(pid_file)], cwd=tmp_path, deadline=time.monotonic() + 30.0, label="probe"
        )
        assert code == 0

    assert time.monotonic() - started < 25.0  # the long sleeper held the pipe in the old design
    assert _gone(int(pid_file.read_text(encoding="utf-8")))


def test_command_output_and_exit_code_are_returned(tmp_path: Path) -> None:
    code, output = gate.run_bounded(
        [sys.executable, "-c", "print('out'); import sys; print('err', file=sys.stderr); sys.exit(3)"],
        cwd=tmp_path,
        deadline=time.monotonic() + 30.0,
        label="probe",
    )

    assert code == 3
    assert "out" in output and "err" in output


@pytest.mark.parametrize("ending", ["nonzero", "signal", "timeout", "spawn-error", "no-budget"])
def test_failed_command_measurement_keeps_output_and_observed_exit(tmp_path: Path, ending: str) -> None:
    script = (
        "import os, signal, time; print('synthetic output', flush=True); "
        + {
            "nonzero": "raise SystemExit(3)",
            "signal": "os.kill(os.getpid(), signal.SIGTERM)",
            "timeout": "time.sleep(60)",
            "spawn-error": "raise SystemExit(0)",
            "no-budget": "raise SystemExit(0)",
        }[ending]
    )
    command = [sys.executable, "-c", script] if ending != "spawn-error" else [str(tmp_path / "absent")]
    allowance = 0.0 if ending == "no-budget" else 1.0 if ending == "timeout" else 30.0
    event = {}
    with pytest.raises(gate.GateOutcome) as raised:
        with gate.stage_measurement(event, "pre_commit") as diagnostics:
            code, _ = gate.run_bounded(
                command, cwd=tmp_path, deadline=time.monotonic() + allowance, label="synthetic", diagnostics=diagnostics
            )
            if code:
                raise gate.GateOutcome("pre_commit_failed", "synthetic refusal")

    row = event["stages"]["pre_commit"]
    assert row["elapsed_s"] >= 0.0
    if ending in {"nonzero", "signal", "timeout"}:
        assert row["output_tail"] == "synthetic output"
        assert row["returncode"] == {"nonzero": 3, "signal": -signal.SIGTERM, "timeout": -signal.SIGKILL}[ending]
        assert row["signal"] == {"nonzero": None, "signal": signal.SIGTERM, "timeout": signal.SIGKILL}[ending]
        assert row["child_unavailable_reason"] is None
    else:
        assert row["returncode"] is None and row["signal"] is None
        assert (
            row["child_unavailable_reason"]
            == {"spawn-error": "spawn_error", "no-budget": "budget_exhausted_before_start"}[ending]
        )
        assert row["output_tail"] == ("" if ending == "spawn-error" else None)
    assert row["outcome"] == ("validation_incomplete" if raised.value.incomplete else "refused")
    assert row["reason"] == raised.value.reason


def test_timeout_without_observed_exit_retains_output_and_null_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Unreaped:
        pid = 999999999
        returncode = None

        def __init__(self, *_args, **kwargs):
            kwargs["stdout"].write(b"synthetic unreaped output\n")
            kwargs["stdout"].flush()

        def wait(self, timeout):
            raise subprocess.TimeoutExpired("synthetic", timeout)

    monkeypatch.setattr(gate.subprocess, "Popen", Unreaped)
    monkeypatch.setattr(gate.os, "killpg", lambda *_args: None)
    monkeypatch.setattr(gate, "sweep_descendants", lambda *_args: None)
    event = {}
    with pytest.raises(gate.GateOutcome, match="could not reap"):
        with gate.stage_measurement(event, "pytest") as diagnostics:
            gate.run_bounded(
                ["synthetic"], cwd=tmp_path, deadline=time.monotonic() + 1.0, label="synthetic", diagnostics=diagnostics
            )
    row = event["stages"]["pytest"]
    assert row["returncode"] is None and row["signal"] is None
    assert row["child_unavailable_reason"] == "exit_unobserved"
    assert row["output_tail"] == "synthetic unreaped output"
    assert row["outcome"] == "validation_incomplete"


def test_command_diagnostics_bound_long_lines_and_line_count(tmp_path: Path) -> None:
    event = {}
    with gate.stage_measurement(event, "pytest") as diagnostics:
        code, output = gate.run_bounded(
            [sys.executable, "-c", "print('x' * 20000); print('line\\n' * 100, end='')"],
            cwd=tmp_path,
            deadline=time.monotonic() + 30.0,
            label="synthetic",
            diagnostics=diagnostics,
        )
    assert code == 0 and len(output) > gate.OUTPUT_TAIL_BYTES
    assert event["stages"]["pytest"]["output_tail"] == "\n".join(["line"] * 40)
    event = {}
    with gate.stage_measurement(event, "pytest") as diagnostics:
        gate.run_bounded(
            [sys.executable, "-c", "print('x' * 20000, end='')"],
            cwd=tmp_path,
            deadline=time.monotonic() + 30.0,
            label="synthetic",
            diagnostics=diagnostics,
        )
    assert event["stages"]["pytest"]["output_tail"] == "x" * gate.OUTPUT_TAIL_BYTES


@pytest.mark.parametrize("pre_commit_code,pytest_code", [(0, 0), (0, 1), (1, 0), (0, 2)])
def test_exact_head_row_attributes_only_entered_stages(repo: Path, pre_commit_code: int, pytest_code: int) -> None:
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _write(
        repo,
        "scripts/pre_commit/project_python.sh",
        textwrap.dedent(f"""\
        if [ "$1" = "scripts/audit/lint_opsec_leaks.py" ]; then exit 0; fi
        if [ "$2" = "pre_commit" ]; then
            echo 'synthetic hook'
            exit {pre_commit_code}
        fi
        echo 'synthetic pytest'
        if [ {pytest_code} = 1 ]; then echo 'FAILED tests/test_new.py::test_ok - synthetic'; fi
        exit {pytest_code}
        """),
    )
    head = _commit(repo, "synthetic stages", "tests/test_new.py", "scripts/pre_commit/project_python.sh")
    result = _run_gate(repo)
    row = _measurements(repo)[-1]
    assert row["head"] == head
    stages = row["stages"]
    assert set(stages) == ({"pre_commit"} if pre_commit_code else {"pre_commit", "pytest"})
    assert stages["pre_commit"]["returncode"] == pre_commit_code
    assert stages["pre_commit"]["output_tail"] == "synthetic hook"
    assert stages["pre_commit"]["outcome"] == ("refused" if pre_commit_code else "green")
    if not pre_commit_code:
        assert stages["pytest"]["returncode"] == pytest_code
        assert stages["pytest"]["outcome"] == {0: "green", 1: "refused", 2: "validation_incomplete"}[pytest_code]
    assert all(stage["elapsed_s"] >= 0.0 for stage in stages.values())
    assert sum(stage["elapsed_s"] for stage in stages.values()) <= row["duration_s"] + 0.01
    assert row["admission_wait_s"] >= 0.0
    expected = 1 if pre_commit_code or pytest_code == 1 else 75 if pytest_code == 2 else 0
    assert result.returncode == expected
    assert bool(_receipts(repo)) == (expected == 0)
    if pytest_code == 1 and not pre_commit_code:
        assert _verdict(result)["failing"] == ["tests/test_new.py::test_ok"]


def test_stage_timings_are_monotonic_and_separate_from_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = FakeClock()
    _fake_validation(tmp_path, monkeypatch, clock)
    event = {}
    gate.validate(gate.Update("local", "a" * 40, "remote", ZERO_SHA), tmp_path, "x", "y", event)
    assert event["admission_wait_s"] == 500.0
    assert event["stages"]["pre_commit"]["elapsed_s"] == 2.0
    assert event["stages"]["pytest"]["elapsed_s"] == 3.0


def test_pre_commit_failure_keeps_hook_verdict_and_child_diagnostics(tmp_path: Path) -> None:
    launcher = tmp_path / "launcher.sh"
    launcher.write_text("echo 'synthetic hook................................................Failed'\nexit 4\n")
    event = {}
    with pytest.raises(gate.GateOutcome) as raised:
        with gate.stage_measurement(event, "pre_commit") as diagnostics:
            gate.run_pre_commit_stage(
                _plan(), tmp_path, str(launcher), "synthetic", time.monotonic() + 30.0, diagnostics=diagnostics
            )
    assert raised.value.reason == "pre_commit_failed"
    assert raised.value.failing == ("synthetic hook",)
    row = event["stages"]["pre_commit"]
    assert row["returncode"] == 4 and row["signal"] is None
    assert row["outcome"] == "refused" and row["output_tail"].endswith("Failed")


def test_tail_read_failure_preserves_the_observed_nonzero_exit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_tempfile = gate.tempfile.TemporaryFile

    class BrokenTail:
        def __enter__(self):
            self.sink = real_tempfile()
            return self

        def __exit__(self, *_args):
            self.sink.close()

        def __getattr__(self, name):
            return getattr(self.sink, name)

        def seek(self, offset, whence=os.SEEK_SET):
            if whence == os.SEEK_END:
                raise OSError("synthetic tail read failure")
            return self.sink.seek(offset, whence)

    monkeypatch.setattr(gate.tempfile, "TemporaryFile", BrokenTail)
    event = {}
    with pytest.raises(gate.GateOutcome, match="synthetic refusal"):
        with gate.stage_measurement(event, "pytest") as diagnostics:
            code, output = gate.run_bounded(
                [sys.executable, "-c", "print('synthetic output'); raise SystemExit(3)"],
                cwd=tmp_path,
                deadline=time.monotonic() + 30.0,
                label="synthetic",
                diagnostics=diagnostics,
            )
            assert code == 3 and output == "synthetic output\n"
            raise gate.GateOutcome("tests_failed", "synthetic refusal")
    row = event["stages"]["pytest"]
    assert row["returncode"] == 3 and row["signal"] is None
    assert row["outcome"] == "refused" and row["output_tail"] is None
    assert row["output_unavailable_reason"] == "output_read_error"


@pytest.mark.parametrize("incomplete", [False, True])
@pytest.mark.parametrize("failure", [TypeError, ValueError, OSError])
def test_diagnostic_serialization_failure_never_authorizes_push(
    repo: Path, monkeypatch: pytest.MonkeyPatch, incomplete: bool, failure: type[Exception]
) -> None:
    monkeypatch.chdir(repo)
    real_dumps = json.dumps

    def broken_dumps(value, **kwargs):
        if isinstance(value, dict) and "stages" in value:
            raise failure("synthetic diagnostic failure")
        return real_dumps(value, **kwargs)

    def red_validate(_update, _root, _launcher, _config, event, _budget):
        with gate.stage_measurement(event, "pre_commit"):
            raise gate.GateOutcome("synthetic_failure", "synthetic failure", incomplete=incomplete)

    monkeypatch.setattr(gate, "validate", red_validate)
    monkeypatch.setattr(gate.json, "dumps", broken_dumps)
    update = f"refs/heads/feature {'a' * 40} refs/heads/feature {ZERO_SHA}\n"
    assert gate.main(["--launcher", "unused", "--config", "unused"], stdin=update) == (75 if incomplete else 1)
    assert _receipts(repo) == []


# ---- review round 2: absent invariants fail closed, shadow descendants are bounded ----------------------


def test_an_unchanged_registered_invariant_the_sparse_worktree_lacks_is_validation_incomplete(repo: Path) -> None:
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green test", "tests/test_new.py")
    _git(repo, "sparse-checkout", "set", "--no-cone", "/*", "!/tests/test_invariant.py")
    assert not (repo / "tests/test_invariant.py").exists()

    result = _run_gate(repo)

    assert result.returncode == gate.EXIT_INCOMPLETE
    verdict = _verdict(result)
    assert verdict["outcome"] == "validation_incomplete"
    assert verdict["reason"] == "registry_entries_unmaterialized"
    assert "tests/test_invariant.py" in result.stderr
    assert _receipts(repo) == []


def test_an_absent_registered_file_with_an_approved_deferral_is_not_incomplete(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(repo, "tests/test_new.py", GREEN_TEST)
    head = _commit(repo, "green test", "tests/test_new.py")
    (repo / "tests/test_invariant.py").unlink()
    _git(repo, "update-index", "--skip-worktree", "tests/test_invariant.py")
    monkeypatch.setattr(gate, "CI_DEFERRED_MODULES", frozenset({"tests/test_invariant.py"}))
    update = gate.Update("refs/heads/feature", head, "refs/heads/feature", ZERO_SHA)

    plan = gate.build_plan(update, repo)

    assert plan is not None and plan.deferred_to_ci == ("tests/test_invariant.py",)
    assert "tests/test_invariant.py" not in plan.node_ids


_SHADOW_DETACHED = (
    "import json, subprocess, sys\n"
    "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)'], start_new_session=True)\n"
    "open({pid_file!r}, 'w').write(str(child.pid) + '\\n')\n"
    "{tail}"
)
_SHADOW_ANSWER = "print(json.dumps({'components': [], 'fallback_reasons': [], 'selected_tests': []}))\n"


@pytest.mark.parametrize("ending", ["success", "timeout", "abandon"])
def test_a_detached_shadow_descendant_does_not_outlive_the_shadow(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ending: str
) -> None:
    pid_file = tmp_path / "shadow-child.pid"
    tail = _SHADOW_ANSWER if ending == "success" else "import time\ntime.sleep(300)\n"
    _install_shadow(repo, _SHADOW_DETACHED.format(pid_file=str(pid_file), tail=tail))
    monkeypatch.setattr(gate, "SHADOW_BUDGET_S", 3.0 if ending == "timeout" else 60.0)
    plan = gate.Plan("h", "t", "b", "v", (), (), ("scripts/x.py",))
    shadow = gate.Shadow(plan, repo, str(repo / "scripts/pre_commit/project_python.sh"))
    wait_for_pid_line(pid_file, timeout=10.0)  # the selector must have spawned its child before the ending
    started = time.monotonic()

    if ending == "abandon":
        shadow.abandon()
    else:
        result = shadow.finish()
        assert result["status"] == ("recorded" if ending == "success" else "unavailable")

    assert time.monotonic() - started < 25.0
    assert _gone(int(pid_file.read_text(encoding="utf-8")))


# ---- review round 3: receipt persistence and shadow result shapes ----------------------------------------


@pytest.mark.parametrize(
    ("answer", "detail"),
    [
        ("[]", "unexpected result shape"),
        ("None", "unexpected result shape"),
        ("123", "unexpected result shape"),
        ("'text'", "unexpected result shape"),
        ("{'components': [], 'fallback_reasons': [], 'selected_tests': None}", "unexpected selected_tests shape"),
        ("{'components': [], 'fallback_reasons': []}", "unexpected selected_tests shape"),
        ("{'selected_tests': 'tests/test_x.py'}", "unexpected selected_tests shape"),
        ("{'selected_tests': ['tests/test_x.py', 7]}", "unexpected selected_tests shape"),
    ],
)
def test_a_misshapen_shadow_result_is_unavailable_not_a_crash(repo: Path, answer: str, detail: str) -> None:
    _install_shadow(repo, f"import json\nprint(json.dumps({answer}))\n")
    plan = gate.Plan("h", "t", "b", "v", (), (), ("scripts/x.py",))
    shadow = gate.Shadow(plan, repo, str(repo / "scripts/pre_commit/project_python.sh"))

    result = shadow.finish()

    assert result == {"status": "unavailable", "detail": detail}


def test_a_failed_receipt_write_abandons_the_shadow_and_is_incomplete(
    repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "1")
    _install_shadow(repo, "import time\ntime.sleep(60)\n")
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "pre-commit-cache"))
    monkeypatch.chdir(repo)
    abandoned: list[bool] = []
    real_abandon = gate.Shadow.abandon

    def spy(self: gate.Shadow) -> None:
        abandoned.append(True)
        real_abandon(self)

    def broken_receipt(*_args: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(gate.Shadow, "abandon", spy)
    monkeypatch.setattr(gate, "write_receipt", broken_receipt)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    update = gate.Update("refs/heads/feature", head, "refs/heads/feature", ZERO_SHA)

    with pytest.raises(gate.GateOutcome) as raised:
        gate.validate(
            update,
            repo,
            str(repo / "scripts/pre_commit/project_python.sh"),
            str(repo / ".pre-commit-config.yaml"),
            {},
        )

    assert raised.value.reason == "receipt_unwritable" and raised.value.incomplete
    assert abandoned == [True]


# ---- review round 5: lifecycle-wide shadow cleanup and unencodable selections ----------------------------


def test_an_unencodable_selected_test_is_unavailable_not_a_crash(repo: Path) -> None:
    _install_shadow(repo, 'print(\'{"selected_tests": ["tests/test_x\\\\ud800.py"], "components": []}\')\n')
    plan = gate.Plan("h", "t", "b", "v", (), (), ("scripts/x.py",))
    shadow = gate.Shadow(plan, repo, str(repo / "scripts/pre_commit/project_python.sh"))

    result = shadow.finish()

    assert result == {"status": "unavailable", "detail": "cannot encode selected_tests"}


def test_an_io_error_during_a_stage_abandons_the_shadow_and_is_incomplete(
    repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "1")
    _install_shadow(repo, "import time\ntime.sleep(60)\n")
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "pre-commit-cache"))
    monkeypatch.chdir(repo)
    shadows: list[gate.Shadow] = []
    real_init = gate.Shadow.__init__

    def recording_init(self: gate.Shadow, *args: object) -> None:
        real_init(self, *args)  # type: ignore[arg-type]
        shadows.append(self)

    def broken_stage(*_args: object, **_kwargs: object) -> None:
        raise OSError("no space for the output file")

    monkeypatch.setattr(gate.Shadow, "__init__", recording_init)
    monkeypatch.setattr(gate, "run_pre_commit_stage", broken_stage)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    update = gate.Update("refs/heads/feature", head, "refs/heads/feature", ZERO_SHA)

    with pytest.raises(gate.GateOutcome) as raised:
        gate.validate(
            update,
            repo,
            str(repo / "scripts/pre_commit/project_python.sh"),
            str(repo / ".pre-commit-config.yaml"),
            {},
        )

    assert raised.value.reason == "validation_error" and raised.value.incomplete
    (shadow,) = shadows
    assert shadow.process is not None and shadow.process.poll() is not None
    assert shadow.output.closed


# ---- review round 6: startup I/O errors are typed, not unhandled -----------------------------------------


@pytest.mark.parametrize("failing_step", ["admission_lock", "shadow_tempfile"])
def test_a_startup_io_error_is_a_typed_incomplete_outcome_and_leaks_nothing(
    repo: Path, monkeypatch: pytest.MonkeyPatch, failing_step: str
) -> None:
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "1")
    monkeypatch.chdir(repo)
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")
    state = gate.state_dir(repo)
    started: list[str] = []
    real_open = os.open

    def open_without_lock(path: object, *args: object, **kwargs: object) -> int:
        if str(path).endswith("admission.lock"):
            raise OSError("cannot open admission lock")
        return real_open(path, *args, **kwargs)  # type: ignore[arg-type]

    def no_tempfile(*_args: object, **_kwargs: object) -> None:
        raise OSError("no space for shadow output")

    def no_stage(*_args: object, **_kwargs: object) -> None:
        started.append("stage")

    if failing_step == "admission_lock":
        monkeypatch.setattr(gate.os, "open", open_without_lock)
    else:
        monkeypatch.setattr(gate.tempfile, "TemporaryFile", no_tempfile)
    monkeypatch.setattr(gate, "run_pre_commit_stage", no_stage)
    monkeypatch.setattr(gate, "run_pytest_stage", no_stage)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    update = gate.Update("refs/heads/feature", head, "refs/heads/feature", ZERO_SHA)

    with pytest.raises(gate.GateOutcome) as raised:
        gate.validate(
            update,
            repo,
            str(repo / "scripts/pre_commit/project_python.sh"),
            str(repo / ".pre-commit-config.yaml"),
            {},
        )

    assert raised.value.reason == "validation_error" and raised.value.incomplete
    assert "validation I/O failed" in raised.value.detail
    assert started == []  # no stage ran on an unadmitted or shadow-less gate
    monkeypatch.undo()
    with gate.Admission(state, 0.0):  # the admission lock was released, not leaked
        pass


# ---- #10383: private pytest temps and safe queue admission ----------------------------------------------


@pytest.mark.parametrize("ending", ["green", "red", "timeout", "startup-error"])
def test_pytest_stage_owns_and_cleans_a_private_base_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ending: str
) -> None:
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(gate, "state_dir", lambda _root: state)
    temp_parent = gate.pytest_temp_parent(state)
    seen: list[Path] = []

    def run(command: list[str], **_kwargs: object) -> tuple[int, str]:
        assert "--basetemp" in command
        base = Path(command[command.index("--basetemp") + 1])
        assert base.parent == temp_parent and base.name.startswith("pytest-")
        base.mkdir(exist_ok=True)
        (base / "probe").touch()
        seen.append(base)
        if ending == "timeout":
            raise gate.GateOutcome("time_budget_exhausted", "pytest stage timed out", incomplete=True)
        if ending == "startup-error":
            raise OSError("cannot start pytest")
        return (1, "FAILED tests/test_a.py::test_bad") if ending == "red" else (0, "1 passed in 0.1s")

    monkeypatch.setattr(gate, "run_bounded", run)
    if ending == "green":
        assert (
            gate.run_pytest_stage(_plan(), tmp_path, "launcher", time.monotonic() + 30)
            == "1 passed in 0.1s; 1 passed in 0.1s"
        )
    else:
        with pytest.raises(OSError if ending == "startup-error" else gate.GateOutcome):
            gate.run_pytest_stage(_plan(), tmp_path, "launcher", time.monotonic() + 30)
    # Each run owns a distinct base; a refused first run never starts the second.
    assert len(seen) == (2 if ending == "green" else 1) and len(set(seen)) == len(seen)
    assert not any(base.exists() for base in seen)
    assert list(state.glob("pytest-*")) == list(temp_parent.glob("pytest-*")) == []


def test_stale_and_dangling_tickets_are_reaped_before_the_live_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queue = tmp_path / "queue"
    queue.mkdir()
    for number in range(5):
        (queue / f"{number}-stale.ticket").touch()
        (queue / f"{number}-dangling.ticket").symlink_to(tmp_path / "missing")
    monkeypatch.setattr(gate, "MAX_QUEUE_ENTRIES", 1)

    with gate.Admission(tmp_path, 0.0) as admitted:
        assert admitted.queue_depth == 1 and admitted.queue_position == 1
        assert list(queue.glob("*.ticket")) == [admitted._ticket]
    assert list(queue.glob("*.ticket")) == []


@pytest.mark.parametrize("tampering", ["missing", "symlink", "replacement", "fifo", "directory"])
def test_an_invalid_own_ticket_is_typed_incomplete_without_a_traceback(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tampering: str
) -> None:
    monkeypatch.chdir(repo)
    _write(repo, "tests/test_new.py", GREEN_TEST)
    head = _commit(repo, "green", "tests/test_new.py")
    original = gate.Admission._register

    def register(admission: gate.Admission) -> None:
        original(admission)
        ticket = admission._ticket
        assert ticket is not None
        target = ticket.parent / "original"
        ticket.rename(target)
        if tampering == "symlink":
            ticket.symlink_to(target)
        elif tampering == "replacement":
            ticket.touch()
        elif tampering == "fifo":
            os.mkfifo(ticket)
        elif tampering == "directory":
            ticket.mkdir()

    monkeypatch.setattr(gate.Admission, "_register", register)
    result = gate.main(
        ["--launcher", "unused", "--config", "unused"],
        f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
    )
    error = capsys.readouterr().err

    assert result == gate.EXIT_INCOMPLETE
    assert _verdict(subprocess.CompletedProcess([], result, stderr=error))["reason"] == "validation_incomplete"
    assert "Traceback" not in error
    assert _receipts(repo) == []


@pytest.mark.parametrize("kind", ["symlink", "directory", "fifo", "dangling-symlink"])
def test_nonregular_predecessors_cannot_count_as_live_tickets(tmp_path: Path, kind: str) -> None:
    queue = tmp_path / "queue"
    queue.mkdir()
    target = tmp_path / "target"
    target.write_text("preserve me")
    fd = os.open(target, os.O_RDONLY)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    ticket = queue / "00000000000000000000-other.ticket"
    if kind == "symlink":
        ticket.symlink_to(target)
    elif kind == "directory":
        ticket.mkdir()
        (ticket / "nested").mkdir()
        (ticket / "nested" / "stale").touch()
    elif kind == "dangling-symlink":
        ticket.symlink_to(tmp_path / "missing")
    else:
        os.mkfifo(ticket)
    try:
        for _ in range(2):
            with gate.Admission(tmp_path, 0.0) as admitted:
                assert admitted.queue_depth == admitted.queue_position == 1
                assert not os.path.lexists(ticket)
        assert target.read_text() == "preserve me"
    finally:
        os.close(fd)


def test_ticket_open_uses_nofollow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_open = os.open
    flags_seen: list[int] = []

    def recording_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
        if str(path).endswith(".ticket"):
            flags_seen.append(flags)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(gate.os, "open", recording_open)
    with gate.Admission(tmp_path, 0.0):
        pass
    assert flags_seen and all(flags & os.O_NOFOLLOW for flags in flags_seen)


def test_hard_link_to_own_locked_ticket_waits_then_is_reaped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = gate.Admission._register
    predecessor = tmp_path / "queue" / "00000000000000000000-hardlink.ticket"

    def register(admission: gate.Admission) -> None:
        original(admission)
        os.link(admission._ticket, predecessor)

    monkeypatch.setattr(gate.Admission, "_register", register)
    with pytest.raises(gate.GateOutcome) as raised, gate.Admission(tmp_path, 0.0):
        pytest.fail("the locked hard link must wait")
    assert raised.value.reason == "validation_incomplete"
    assert "admission_timeout" in raised.value.detail
    assert predecessor.exists()
    monkeypatch.undo()
    with gate.Admission(tmp_path, 0.0) as admitted:
        assert admitted.queue_depth == admitted.queue_position == 1
        assert not predecessor.exists()


@pytest.mark.parametrize("kind", ["file", "fifo", "symlink", "directory"])
def test_pytest_stage_reaps_stale_nodes_without_following_links(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    state = tmp_path / "state"
    state.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "preserved").write_text("preserve me")
    stale = state / "pytest-stale"
    if kind == "file":
        stale.touch()
    elif kind == "fifo":
        os.mkfifo(stale)
    elif kind == "symlink":
        stale.symlink_to(outside, target_is_directory=True)
    else:
        stale.mkdir()
        (stale / "nested").mkdir()
        (stale / "nested" / "file").touch()
        (stale / "link").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(gate, "state_dir", lambda _root: state)
    monkeypatch.setattr(gate, "run_bounded", lambda *_args, **_kwargs: (0, "1 passed in 0.1s"))

    for _ in range(2):
        with gate.Admission(state, 0) as admission:
            assert (
                gate.run_pytest_stage(_plan(), tmp_path, "launcher", time.monotonic() + 30, admission=admission)
                == "1 passed in 0.1s; 1 passed in 0.1s"
            )
        assert not os.path.lexists(stale)
        assert list(state.glob("pytest-*")) == []
        assert (outside / "preserved").read_text() == "preserve me"


def test_pytest_stale_reap_io_error_is_typed_incomplete(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stale = tmp_path / "pytest-stale"
    stale.mkdir()
    (stale / "nested").mkdir()
    monkeypatch.setattr(gate, "state_dir", lambda _root: tmp_path)

    def refuse(*_args: object, **_kwargs: object) -> None:
        raise PermissionError("cleanup denied")

    refuse.avoids_symlink_attacks = True
    monkeypatch.setattr(gate.shutil, "rmtree", refuse)
    with gate.Admission(tmp_path, 0) as admission, pytest.raises(gate.GateOutcome) as raised:
        gate.run_pytest_stage(_plan(), tmp_path, "launcher", time.monotonic() + 30, admission=admission)
    assert raised.value.reason == "validation_incomplete" and raised.value.incomplete
    assert (stale / "nested").is_dir()


@pytest.mark.parametrize("area", ["pytest", "queue"])
def test_stale_directory_swap_is_refused_without_touching_the_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, area: str
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "preserved").write_text("preserve me")
    if area == "queue":
        (tmp_path / "queue").mkdir()
        stale = tmp_path / "queue" / "00000000000000000000-other.ticket"
    else:
        stale = tmp_path / "pytest-stale"
    stale.mkdir()
    (stale / "preserved").touch()
    displaced = tmp_path / "displaced"
    original = os.open
    opened: list[int] = []

    def swap(path: object, flags: int, *args: object, **kwargs: object) -> int:
        fd = original(path, flags, *args, **kwargs)
        if Path(path) == stale and flags & os.O_DIRECTORY:
            opened.append(flags)
            stale.rename(displaced)
            stale.symlink_to(outside, target_is_directory=True)
        return fd

    monkeypatch.setattr(gate.os, "open", swap)
    monkeypatch.setattr(gate, "state_dir", lambda _root: tmp_path)
    with pytest.raises(gate.GateOutcome) as raised:
        if area == "queue":
            with gate.Admission(tmp_path, 0.0):
                pytest.fail("a replaced directory cannot be reaped")
        else:
            gate.reap_stale_node(stale)
    assert raised.value.reason == "validation_incomplete" and raised.value.incomplete
    assert opened and all(flags & os.O_NOFOLLOW for flags in opened)
    assert (outside / "preserved").read_text() == "preserve me"
    assert (displaced / "preserved").exists()


def test_a_concurrent_pytest_pruner_cannot_remove_the_gate_temp(repo: Path, tmp_path: Path) -> None:
    marker = tmp_path / "gate-temp.txt"
    release = tmp_path / "release"
    shared = tmp_path / "shared"
    shared.mkdir()
    # The pruner must actually delete an abandoned shared base, not merely run beside the gate.
    import getpass

    user_root = shared / f"pytest-of-{getpass.getuser()}"
    user_root.mkdir(mode=0o700)
    victim = user_root / "pytest-0"
    victim.mkdir()
    (victim / "abandoned").touch()
    body = (
        "from pathlib import Path\nimport time\n"
        "def test_temp_survives(tmp_path):\n"
        "    probe = tmp_path / 'survives'\n    probe.write_text('gate')\n"
        f"    Path({str(marker)!r}).write_text(str(probe) + '\\n')\n"
        f"    release = Path({str(release)!r})\n"
        "    deadline = time.monotonic() + 40\n"
        "    while not release.exists() and time.monotonic() < deadline:\n        time.sleep(0.05)\n"
        "    assert release.exists(), 'pruner did not finish'\n"
        "    assert probe.read_text() == 'gate'\n"
    )
    _write(repo, "tests/test_private_temp.py", body)
    head = _commit(repo, "temp survival", "tests/test_private_temp.py")
    pruner = tmp_path / "test_pruner.py"
    pruner.write_text("def test_prune(tmp_path):\n    assert tmp_path.is_dir()\n", encoding="utf-8")
    env = _env({"PYTEST_DEBUG_TEMPROOT": str(shared), "PRE_COMMIT_HOME": str(tmp_path / "pc")})
    process = subprocess.Popen(
        [
            sys.executable,
            str(repo / ".githooks/pre_push_gate.py"),
            "--launcher",
            str(repo / "scripts/pre_commit/project_python.sh"),
            "--config",
            str(repo / ".pre-commit-config.yaml"),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=repo,
        env=env,
        text=True,
    )
    try:
        assert process.stdin is not None
        process.stdin.write(f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n")
        process.stdin.close()
        process.stdin = None
        try:
            wait_for_line(marker, timeout=30.0, stop_if=lambda: process.poll() is not None)
        except AssertionError:
            if process.poll() is not None:
                pytest.fail(str(process.communicate()))
            pytest.fail("gate pytest did not start")
        # Expire the default-base lock, reproducing the stale-base pruning failure deterministically.
        for lock in user_root.glob("pytest-*/.lock"):
            os.utime(lock, (time.time() - 4 * 86400,) * 2)
        pruned = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(pruner),
                "-q",
                "-p",
                "no:cacheprovider",
                "-o",
                "tmp_path_retention_count=0",
                "-o",
                "tmp_path_retention_policy=all",
            ],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert pruned.returncode == 0, pruned.stdout + pruned.stderr
        assert not victim.exists(), "the unrelated session must prune shared state"
        release.touch()
        stdout, stderr = process.communicate(timeout=60)
        assert process.returncode == 0, stdout + stderr
        probe = Path(marker.read_text(encoding="utf-8").strip())
        temp_parent = gate.pytest_temp_parent(gate.state_dir(repo))
        assert probe.is_relative_to(temp_parent)
        assert not probe.exists()  # the gate cleaned its private base on completion
        assert list(gate.state_dir(repo).glob("pytest-*")) == list(temp_parent.glob("pytest-*")) == []
    finally:
        release.touch()
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=60)


SURVIVING_WORKER = textwrap.dedent(
    """\
    import json, os, pathlib, sys, time
    signals = pathlib.Path(sys.argv[1])
    base = pathlib.Path(sys.argv[sys.argv.index("--basetemp") + 1])
    (base / "live").write_text("in use")
    (signals / "ready").write_text(json.dumps({"pid": os.getpid(), "base": str(base)}) + "\\n")
    deadline = time.monotonic() + 60
    while not (signals / "release").exists() and time.monotonic() < deadline:
        if not (base / "live").exists():
            (signals / "deleted").touch()
        time.sleep(0.01)
    """
)


def test_a_killed_gate_leaves_its_live_base_to_scratch_aging(repo: Path, tmp_path: Path) -> None:
    # SIGKILL releases the gate's admission while its detached pytest worker keeps running (#10654 review).
    # The next exclusive gate must remove only its own base; the host's scratch aging owns the residue.
    signals = tmp_path / "signals"
    signals.mkdir()
    worker = tmp_path / "worker.py"
    worker.write_text(SURVIVING_WORKER, encoding="utf-8")
    launcher = tmp_path / "launcher.sh"
    launcher.write_text(f'exec "{sys.executable}" "{worker}" "{signals}" "$@"\n', encoding="utf-8")
    script = (
        f"import runpy, pathlib, time\ng = runpy.run_path({str(GATE_PATH)!r})\n"
        "plan = g['Plan']('h', 't', 'b', 'v', ('tests/test_invariant.py',), (), ())\n"
        f"g['run_pytest_stage'](plan, pathlib.Path({str(repo)!r}), {str(launcher)!r}, time.monotonic() + 60)\n"
    )
    killed = subprocess.Popen(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    worker_pid = None
    try:
        ready = json.loads(wait_for_line(signals / "ready", timeout=30.0, stop_if=lambda: killed.poll() is not None))
        worker_pid, base = ready["pid"], Path(ready["base"])
        killed.kill()
        assert killed.wait(timeout=30) == -signal.SIGKILL
        os.kill(worker_pid, 0)  # the worker outlived its gate
        plan = _plan(registry_nodes=("tests/test_invariant.py",), changed_tests=())
        with gate.Admission(gate.state_dir(repo), 0.0) as admission:
            assert admission._exclusive
            result = gate.run_pytest_stage(
                plan,
                repo,
                str(repo / "scripts/pre_commit/project_python.sh"),
                time.monotonic() + 30,
                admission=admission,
            )
        assert "1 passed" in result
        assert base.parent == gate.pytest_temp_parent(gate.state_dir(repo))
        assert (base / "live").read_text(encoding="utf-8") == "in use"
        assert not (signals / "deleted").exists()
        assert list(base.parent.glob("pytest-*")) == [base]  # the successor removed only its own base
    finally:
        (signals / "release").touch()
        if killed.poll() is None:
            killed.kill()
        killed.wait(timeout=30)
        if worker_pid is not None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(worker_pid, signal.SIGKILL)


@pytest.mark.parametrize("when", ["after-validation", "during-run"])
def test_replacing_the_scratch_ancestry_cannot_redirect_the_gates_own_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, when: str
) -> None:
    # A root another user can write is refused before anything is created (see the round-3 ancestry tests).
    # Below a verified root only this user can rename its directory, which is outside the trust model, and
    # pytest's own --basetemp handling then follows the path. This pins the narrower guarantee that the
    # gate's own create and remove never follow a replaced ancestor into another repository's live base.
    scratch = tmp_path / "scratch"
    scratch.mkdir(mode=0o700)
    monkeypatch.setenv(gate.SCRATCH_ROOT_ENV, str(scratch))
    state, other_state = tmp_path / "state", tmp_path / "other-state"
    state.mkdir()
    other_state.mkdir()
    monkeypatch.setattr(gate, "state_dir", lambda _root: state)
    parent, other = gate.pytest_temp_parent(state), gate.pytest_temp_parent(other_state)
    parked = scratch / "parked"
    decoys: list[Path] = []

    def replace_ancestry(decoy_name: str) -> None:
        parent.parent.rename(parked)
        parent.parent.mkdir()
        parent.symlink_to(parked / other.name, target_is_directory=True)
        decoy = parked / other.name / decoy_name  # another repository's live base
        decoy.mkdir()
        (decoy / "live").write_text("in use")
        decoys.append(decoy)

    if when == "after-validation":
        validated = gate.pytest_temp_parent

        def validate_then_replace(path: Path) -> Path:
            checked = validated(path)
            replace_ancestry("pytest-live")
            return checked

        monkeypatch.setattr(gate, "pytest_temp_parent", validate_then_replace)
        monkeypatch.setattr(gate, "run_bounded", lambda *_args, **_kwargs: (0, "1 passed in 0.1s"))
    else:
        own: list[Path] = []

        def run(command: list[str], **_kwargs: object) -> tuple[int, str]:
            base = Path(command[command.index("--basetemp") + 1])
            (base / "probe").touch()
            own.append(parked / parent.name / base.name)  # where this run's base lives after the rename
            replace_ancestry(base.name)  # the decoy shares the base's name, so a path-based removal hits it
            return 0, "1 passed in 0.1s"

        monkeypatch.setattr(gate, "run_bounded", run)

    with gate.Admission(state, 0) as admission:
        try:
            outcome = gate.run_pytest_stage(
                _plan(changed_tests=()), tmp_path, "launcher", time.monotonic() + 30, admission=admission
            )
        except gate.GateOutcome as error:
            outcome = error.reason
    assert len(decoys) == 1 and (decoys[0] / "live").read_text() == "in use"
    if when == "after-validation":
        assert outcome == "pytest_temp_unavailable"  # the replaced parent is refused, never followed
    else:
        assert outcome == "1 passed in 0.1s"
        assert len(own) == 1 and not own[0].exists()  # the run still removed its own base


@pytest.mark.parametrize("ending", ["green", "red"])
def test_own_base_is_removed_whatever_pytest_and_its_tests_leave_in_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ending: str
) -> None:
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(gate, "state_dir", lambda _root: state)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "preserved").write_text("preserve me")
    seen: list[Path] = []

    def run(command: list[str], **_kwargs: object) -> tuple[int, str]:
        base = Path(command[command.index("--basetemp") + 1])
        seen.append(base)
        base.rmdir()  # pytest deletes a given --basetemp and creates a fresh directory
        base.mkdir(mode=0o700)
        (base / "link").symlink_to(outside, target_is_directory=True)
        (base / "read-only" / "nested").mkdir(parents=True)
        (base / "read-only" / "nested" / "file").touch()
        (base / "read-only").chmod(0o500)
        (base / "unreadable").mkdir()
        (base / "unreadable" / "file").touch()
        (base / "unreadable").chmod(0o000)
        os.mkfifo(base / "fifo")
        return (1, "FAILED tests/test_a.py::test_bad") if ending == "red" else (0, "1 passed in 0.1s")

    monkeypatch.setattr(gate, "run_bounded", run)
    plan = _plan(changed_tests=())
    if ending == "green":
        assert gate.run_pytest_stage(plan, tmp_path, "launcher", time.monotonic() + 30) == "1 passed in 0.1s"
    else:
        with pytest.raises(gate.GateOutcome) as raised:
            gate.run_pytest_stage(plan, tmp_path, "launcher", time.monotonic() + 30)
        assert raised.value.reason == "tests_failed"
    assert len(seen) == 1 and not os.path.lexists(seen[0])
    assert list(seen[0].parent.iterdir()) == []
    assert [path.name for path in outside.iterdir()] == ["preserved"]


@pytest.mark.parametrize("ending", ["green", "timeout"])
def test_own_base_cleanup_failure_is_typed_and_never_masks_the_run_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ending: str
) -> None:
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(gate, "state_dir", lambda _root: state)
    real_rmdir = os.rmdir

    def refuse_own_base(path: object, *args: object, **kwargs: object) -> None:
        if kwargs.get("dir_fd") is not None and str(path).startswith("pytest-"):
            raise PermissionError(errno.EACCES, "denied", str(path))
        real_rmdir(path, *args, **kwargs)

    def run(_command: list[str], **_kwargs: object) -> tuple[int, str]:
        monkeypatch.setattr(gate.os, "rmdir", refuse_own_base)
        if ending == "timeout":
            raise gate.GateOutcome("validation_incomplete", "pytest stage: exceeded the time budget", incomplete=True)
        return 0, "1 passed in 0.1s"

    monkeypatch.setattr(gate, "run_bounded", run)
    with pytest.raises(gate.GateOutcome) as raised:
        gate.run_pytest_stage(_plan(changed_tests=()), tmp_path, "launcher", time.monotonic() + 30)
    monkeypatch.setattr(gate.os, "rmdir", real_rmdir)
    assert raised.value.reason == "validation_incomplete" and raised.value.incomplete
    if ending == "timeout":
        assert "time budget" in raised.value.detail  # the run's own refusal outranks a cleanup error
    else:
        assert raised.value.detail == "pytest base temp cleanup failed (EACCES)"  # typed, path-free


# ---- #10654: pytest base temps outside every Git checkout and Git directory -----------------------------

OUTSIDE_GIT_TEST = textwrap.dedent(
    """\
    def test_tmp_path_is_outside_every_git_checkout(tmp_path):
        # The data-tier runner's own guard (scripts/ci/data_tier.py) refuses scratch below any checkout.
        assert not any((parent / ".git").exists() for parent in (tmp_path, *tmp_path.parents))
    """
)


def _outside_git(path: Path) -> bool:
    """No ancestor is a checkout (``.git``) or a Git directory (``HEAD``, ``objects``, ``refs``)."""
    return not any(
        (directory / ".git").exists() or all((directory / name).exists() for name in ("HEAD", "objects", "refs"))
        for directory in (path, *path.parents)
    )


def test_pytest_base_temp_is_private_and_outside_every_git_tree(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = gate.state_dir(repo)
    seen: list[Path] = []

    def run(command: list[str], **_kwargs: object) -> tuple[int, str]:
        base = Path(command[command.index("--basetemp") + 1])
        seen.append(base)
        assert _outside_git(base)
        for tree in (repo, repo / ".git", state):
            assert not base.resolve().is_relative_to(tree.resolve())
        # The base, its repository directory and the per-user directory are all private to this user.
        for directory in (base, base.parent, base.parent.parent):
            info = directory.lstat()
            assert stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
            assert stat.S_IMODE(info.st_mode) == 0o700
        return 0, "1 passed in 0.1s"

    monkeypatch.setattr(gate, "run_bounded", run)
    assert (
        gate.run_pytest_stage(_plan(), repo, "launcher", time.monotonic() + 30) == "1 passed in 0.1s; 1 passed in 0.1s"
    )
    assert len(seen) == 2 and not any(base.exists() for base in seen)


def test_gate_runs_tests_that_require_a_temp_tree_outside_git(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "1")
    _write(repo, "tests/test_outside_git.py", OUTSIDE_GIT_TEST)
    _commit(repo, "outside git", "tests/test_outside_git.py")

    result = _run_gate(repo)

    assert result.returncode == 0, result.stderr
    assert len(_receipts(repo)) == 1
    # Only the base temp moved: admission, receipts and measurements stay under the Git common dir.
    state = gate.state_dir(repo)
    assert (state / "admission.lock").is_file() and (state / "measurements.jsonl").is_file()
    assert list(state.glob("pytest-*")) == list(gate.pytest_temp_parent(state).glob("pytest-*")) == []


@pytest.mark.parametrize("location", ["checkout", "git-dir", "bare-repo", "uncreatable", "fallback-in-checkout"])
def test_pytest_stage_refuses_without_a_safe_base_temp_location(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, location: str
) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("a file, not a directory")
    if location == "fallback-in-checkout":
        # An uncreatable default falls back to the system temp, which here is the checkout itself.
        monkeypatch.delenv(gate.SCRATCH_ROOT_ENV, raising=False)
        monkeypatch.setattr(gate, "DEFAULT_SCRATCH_ROOT", blocker / "lu")
        monkeypatch.setattr(gate.tempfile, "tempdir", str(repo))
        target = repo / gate.FALLBACK_SCRATCH_DIRNAME
    else:
        target = {
            "checkout": repo / "scratch",
            "git-dir": gate.state_dir(repo) / "scratch",
            "bare-repo": tmp_path / "remote.git" / "scratch",
            "uncreatable": blocker / "scratch",
        }[location]
        monkeypatch.setenv(gate.SCRATCH_ROOT_ENV, str(target))
    if location != "uncreatable":
        # Close the ancestry to others whatever the caller's umask, so the Git check is what refuses.
        gate.state_dir(repo).mkdir(mode=0o755, exist_ok=True)
        _close_to_others(target.parent, tmp_path)
    monkeypatch.setattr(gate, "run_bounded", lambda *_args, **_kwargs: pytest.fail("pytest must not start"))

    with pytest.raises(gate.GateOutcome) as raised:
        gate.run_pytest_stage(_plan(), repo, "launcher", time.monotonic() + 30)

    assert raised.value.reason == "pytest_temp_unavailable" and raised.value.incomplete
    assert gate.SCRATCH_ROOT_ENV in raised.value.detail and str(tmp_path) not in raised.value.detail
    assert ("inside a Git checkout" in raised.value.detail) == (location != "uncreatable")
    assert not target.exists()


@pytest.mark.parametrize(
    "tampering", ["symlink", "group-readable", "file", "foreign-owner", "repository-group-readable"]
)
def test_pytest_stage_refuses_a_base_temp_directory_that_is_not_private(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tampering: str
) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir(mode=0o700)  # a safe root, so only the tampered directory below it can refuse
    monkeypatch.setenv(gate.SCRATCH_ROOT_ENV, str(scratch))
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "preserved").write_text("preserve me")
    state = tmp_path / "state"
    state.mkdir()
    user = scratch / f"pre-push-gate-{os.geteuid()}"
    if tampering == "symlink":
        user.symlink_to(outside, target_is_directory=True)
    elif tampering == "group-readable":
        user.mkdir()
        user.chmod(0o750)
    elif tampering == "foreign-owner":
        user.mkdir(mode=0o700)
        _pretend_owned_by_another_user(monkeypatch, user)
    elif tampering == "repository-group-readable":
        gate.pytest_temp_parent(state).chmod(0o750)
    else:
        user.write_text("not a directory")
    monkeypatch.setattr(gate, "state_dir", lambda _root: state)
    monkeypatch.setattr(gate, "run_bounded", lambda *_args, **_kwargs: pytest.fail("pytest must not start"))

    with pytest.raises(gate.GateOutcome) as raised:
        gate.run_pytest_stage(_plan(), tmp_path, "launcher", time.monotonic() + 30)

    assert raised.value.reason == "pytest_temp_unavailable" and raised.value.incomplete
    assert "pytest base temp directory" in raised.value.detail  # refused at the tampered level, not the root
    assert [path.name for path in outside.iterdir()] == ["preserved"]


# ---- #10654 round 3: the scratch root's whole ancestry is verified before anything is created ----------
# Trust model: this user and root. A same-user process can already edit the hook, so same-user swaps are
# outside it; what must hold is that no other user can redirect the base temp.


def _pretend_owned_by_another_user(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    """Report ``path``'s own inode (a link itself, not its target) as owned by neither this user nor root."""
    real = path.lstat()
    key, other = (real.st_dev, real.st_ino), os.geteuid() + 1

    def reporting(original):
        def report(*args: object, **kwargs: object) -> os.stat_result:
            info = original(*args, **kwargs)
            if (info.st_dev, info.st_ino) != key:
                return info
            fields = list(info[:10])
            fields[4] = other  # st_uid
            return os.stat_result(fields)

        return report

    for name in ("lstat", "stat", "fstat"):
        monkeypatch.setattr(gate.os, name, reporting(getattr(os, name)))


def _gate_directories(top: Path) -> list[Path]:
    """Every per-user gate directory below ``top``, without following links."""
    return [Path(here) / name for here, names, _files in os.walk(top) for name in names if "pre-push-gate-" in name]


def _close_to_others(path: Path, stop: Path) -> None:
    """Remove group and other write from ``path`` and its existing ancestors up to ``stop``."""
    for directory in (path, *path.parents):
        if directory.is_dir() and not directory.is_symlink():
            directory.chmod(stat.S_IMODE(directory.lstat().st_mode) & ~0o022)
        if directory == stop:
            break


UNSAFE_ANCESTRY = {
    "foreign-owned-ancestor": "a directory owned by another user",
    "group-writable-ancestor": "a directory writable by group or others without the sticky bit",
    "other-writable-ancestor": "a directory writable by group or others without the sticky bit",
    "group-writable-root": "a directory writable by group or others without the sticky bit",
    "link-to-unsafe-directory": "a directory writable by group or others without the sticky bit",
    "foreign-link-in-sticky-directory": "a link owned by another user",
    "link-loop": "a link loop",
}


def _unsafe_ancestry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str) -> tuple[Path, list[Path]]:
    """Build one unsafe scratch root; return it and the paths that must still be absent after a refusal."""
    shared, safe = tmp_path / "shared", tmp_path / "safe"
    shared.mkdir(mode=0o755)
    safe.mkdir(mode=0o700)
    if case == "foreign-owned-ancestor":
        _pretend_owned_by_another_user(monkeypatch, shared)
    elif case in ("group-writable-ancestor", "group-writable-root"):
        shared.chmod(0o775)
    elif case == "other-writable-ancestor":
        shared.chmod(0o757)
    if case == "group-writable-root":
        root = tmp_path / "root"
        root.mkdir()
        root.chmod(0o775)  # an existing root created under umask 002
        return root, []
    if case == "link-to-unsafe-directory":
        shared.chmod(0o777)
        (tmp_path / "link").symlink_to(shared, target_is_directory=True)
        return tmp_path / "link" / "scratch", [shared / "scratch"]
    if case == "foreign-link-in-sticky-directory":
        sticky = tmp_path / "sticky"
        sticky.mkdir()
        sticky.chmod(0o1777)  # the system temp pattern: anyone may add entries, only their owner may replace them
        (sticky / "link").symlink_to(safe, target_is_directory=True)
        _pretend_owned_by_another_user(monkeypatch, sticky / "link")
        return sticky / "link" / "scratch", [safe / "scratch"]
    if case == "link-loop":
        (tmp_path / "loop-a").symlink_to(tmp_path / "loop-b")
        (tmp_path / "loop-b").symlink_to(tmp_path / "loop-a")
        return tmp_path / "loop-a" / "scratch", []
    return shared / "lu" / "scratch", [shared / "lu"]


@pytest.mark.parametrize("case", sorted(UNSAFE_ANCESTRY))
def test_an_unsafe_scratch_ancestry_refuses_before_anything_is_created(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    root, absent = _unsafe_ancestry(tmp_path, monkeypatch, case)
    monkeypatch.setenv(gate.SCRATCH_ROOT_ENV, str(root))
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(gate, "state_dir", lambda _root: state)
    monkeypatch.setattr(gate, "run_bounded", lambda *_args, **_kwargs: pytest.fail("pytest must not start"))

    with pytest.raises(gate.GateOutcome) as raised:
        gate.run_pytest_stage(_plan(), tmp_path, "launcher", time.monotonic() + 30)

    assert raised.value.reason == "pytest_temp_unavailable" and raised.value.incomplete
    # The message names the offending component's class and the fix, never a path.
    assert UNSAFE_ANCESTRY[case] in raised.value.detail and gate.SCRATCH_ROOT_ENV in raised.value.detail
    assert str(tmp_path) not in raised.value.detail
    assert _gate_directories(tmp_path) == [] and not any(os.path.lexists(path) for path in absent)


@pytest.mark.parametrize(
    "case", ["absent-root", "existing-root", "sticky-ancestor", "link-to-safe-directory", "parent-of-a-link-target"]
)
def test_a_safe_scratch_ancestry_keeps_create_pytest_and_cleanup_inside_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    private = tmp_path / "private"
    private.mkdir(mode=0o700)
    created: list[Path] = []
    if case == "absent-root":
        root = private / "a" / "b"
        created = [private / "a", root]
    elif case == "existing-root":
        root = private / "root"
        root.mkdir(mode=0o755)
    elif case == "sticky-ancestor":
        sticky = tmp_path / "sticky"
        sticky.mkdir()
        sticky.chmod(0o1777)
        root = sticky / "scratch"
        created = [root]
    elif case == "link-to-safe-directory":
        (tmp_path / "link").symlink_to(private, target_is_directory=True)
        root = tmp_path / "link" / "scratch"
        created = [private / "scratch"]
    else:  # ".." after a link leaves the link's target, as the kernel resolves it, not the link's directory
        (private / "inner").mkdir(mode=0o700)
        (tmp_path / "link").symlink_to(private / "inner", target_is_directory=True)
        root = tmp_path / "link" / ".." / "scratch"
        created = [private / "scratch"]
    monkeypatch.setenv(gate.SCRATCH_ROOT_ENV, str(root))
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(gate, "state_dir", lambda _root: state)
    seen: list[Path] = []

    def run(command: list[str], **_kwargs: object) -> tuple[int, str]:
        base = Path(command[command.index("--basetemp") + 1])
        seen.append(base)
        assert os.path.realpath(base) == str(base)  # pytest receives the verified, link-free path
        (base / "probe").touch()
        return 0, "1 passed in 0.1s"

    monkeypatch.setattr(gate, "run_bounded", run)
    assert gate.run_pytest_stage(_plan(changed_tests=()), tmp_path, "launcher", time.monotonic() + 30) == (
        "1 passed in 0.1s"
    )

    resolved_root = Path(os.path.realpath(root))
    assert len(seen) == 1 and seen[0].parent.parent.parent == resolved_root
    assert not os.path.lexists(seen[0]) and list(seen[0].parent.iterdir()) == []  # only its own base, removed
    for directory in created:  # components the gate created are private to this user
        assert stat.S_IMODE(directory.lstat().st_mode) == 0o700 and directory.lstat().st_uid == os.geteuid()
    if case == "existing-root":
        assert stat.S_IMODE(root.lstat().st_mode) == 0o755  # an existing safe root is used as it is
    if case == "parent-of-a-link-target":
        assert resolved_root == private / "scratch" and not (tmp_path / "scratch").exists()


@pytest.mark.parametrize("unsafe", ["ancestor", "root"])
def test_an_unsafe_default_scratch_root_refuses_without_falling_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, unsafe: str
) -> None:
    # The fallback covers only a default that cannot be created; an unsafe one must be fixed, not bypassed.
    monkeypatch.delenv(gate.SCRATCH_ROOT_ENV, raising=False)
    shared = tmp_path / "shared"
    shared.mkdir(mode=0o755)
    default = shared / "lu"
    if unsafe == "ancestor":
        shared.chmod(0o775)
    else:
        default.mkdir()
        default.chmod(0o775)
    monkeypatch.setattr(gate, "DEFAULT_SCRATCH_ROOT", default)
    system_temp = tmp_path / "system-temp"
    system_temp.mkdir(mode=0o700)
    monkeypatch.setattr(gate.tempfile, "tempdir", str(system_temp))
    state = tmp_path / "state"
    state.mkdir()

    with pytest.raises(gate.GateOutcome) as raised:
        gate.pytest_temp_parent(state)

    assert raised.value.reason == "pytest_temp_unavailable" and raised.value.incomplete
    assert UNSAFE_ANCESTRY["group-writable-ancestor"] in raised.value.detail
    assert gate.SCRATCH_ROOT_ENV in raised.value.detail and str(tmp_path) not in raised.value.detail
    assert not (system_temp / gate.FALLBACK_SCRATCH_DIRNAME).exists() and _gate_directories(tmp_path) == []
    assert os.path.isdir(default) == (unsafe == "root")


@pytest.mark.parametrize("default_usable", [True, False])
def test_pytest_temp_parent_follows_the_fleet_scratch_convention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, default_usable: bool
) -> None:
    from scripts.common import scratch

    assert gate.SCRATCH_ROOT_ENV == scratch.SCRATCH_ROOT_ENV_VAR
    assert gate.DEFAULT_SCRATCH_ROOT == scratch.DEFAULT_SCRATCH_ROOT
    assert gate.FALLBACK_SCRATCH_DIRNAME == scratch.FALLBACK_SCRATCH_DIRNAME
    monkeypatch.delenv(gate.SCRATCH_ROOT_ENV, raising=False)
    blocker = tmp_path / "blocker"
    blocker.write_text("a file, not a directory")
    default = tmp_path / "default" / "lu" if default_usable else blocker / "lu"
    monkeypatch.setattr(gate, "DEFAULT_SCRATCH_ROOT", default)
    system_temp = tmp_path / "system-temp"
    system_temp.mkdir(mode=0o700)
    monkeypatch.setattr(gate.tempfile, "tempdir", str(system_temp))
    states = [tmp_path / "state", tmp_path / "other-state"]
    for state in states:
        state.mkdir()

    parents = [gate.pytest_temp_parent(state) for state in states]

    root = default if default_usable else system_temp / gate.FALLBACK_SCRATCH_DIRNAME
    assert parents[0].parent == parents[1].parent == root / f"pre-push-gate-{os.geteuid()}"
    assert parents[0] != parents[1]  # one namespace per Git common dir
    assert parents[0] == gate.pytest_temp_parent(states[0])  # stable across runs, so crashes can be reaped


def test_moving_the_base_temp_keeps_admission_budget_and_process_caps(monkeypatch: pytest.MonkeyPatch) -> None:
    budgets = (gate.STAGE_BUDGET_S, gate.RUN_BUDGET_S, gate.SHADOW_BUDGET_S, gate.CLEANUP_BUDGET_S)
    assert budgets == (600.0, 1200.0, 120.0, 10.0)
    assert (gate.ADMISSION_WAIT_S, gate.ADMISSION_MAX_WAIT_S, gate.MAX_QUEUE_ENTRIES) == (1340.0, 13400.0, 256)
    monkeypatch.delenv(gate.MAX_TEST_PROCESSES_ENV, raising=False)
    monkeypatch.delenv(gate.MAX_CONCURRENT_RUNS_ENV, raising=False)
    assert (gate.test_process_limit(), gate.concurrent_run_limit()) == (4, 1)


# ---- #10523: exact-plan coalescing before global admission ---------------------------------------------

CONTROL_TEST = textwrap.dedent(
    """\
    import os
    from pathlib import Path

    def test_control():
        control = Path(os.environ['GATE_TEST_CONTROL'])
        (control / 'entered').write_text('entered\\n')
        with (control / 'release').open() as release:
            assert release.read() == 'green'
    """
)


def _start_controlled_gate(
    repo: Path, control: Path, *, base: str = ZERO_SHA, registry_change: str | None = None, **environment: str
):
    control.mkdir()
    os.mkfifo(control / "release")
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    command = [sys.executable, str(repo / ".githooks/pre_push_gate.py")]
    if registry_change is not None:
        # Synthetic registry authority, with real build_plan, stages and production main.
        # Separate version and selected-node controls detect either missing key dimension.
        program = textwrap.dedent("""\
            import importlib.util, sys
            spec = importlib.util.spec_from_file_location('gate', sys.argv.pop(1))
            gate = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = gate
            spec.loader.exec_module(gate)
            change = sys.argv.pop(1)
            original = gate.load_registry
            def registry(root):
                nodes, version = original(root)
                if change == 'registry':
                    return nodes, version + '-control'
                return (*nodes, 'tests/test_red.py'), version
            gate.load_registry = registry
            sys.exit(gate.main())
        """)
        command = [sys.executable, "-c", program, str(repo / ".githooks/pre_push_gate.py"), registry_change]
    process = subprocess.Popen(
        [
            *command,
            "--launcher",
            str(repo / "scripts/pre_commit/project_python.sh"),
            "--config",
            str(repo / ".pre-commit-config.yaml"),
        ],
        cwd=repo,
        env=_env(
            {
                "PRE_COMMIT_HOME": str(repo.parent / "pre-commit-cache"),
                "LU_PRE_PUSH_GATE_MAX_TEST_PROCESSES": "1",
                "GATE_TEST_CONTROL": str(control),
                **environment,
            }
        ),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    local_ref = _git(repo, "symbolic-ref", "HEAD").stdout.strip()
    process.stdin.write(f"{local_ref} {head} refs/heads/feature {base}\n")
    process.stdin.close()
    process.stdin = None
    return process


def _wait_tickets(state: Path, count: int, processes: list[subprocess.Popen]) -> list[dict]:
    """Wait for complete atomic publications, not for an assumed scheduler delay."""
    paths: list[Path] = []

    def published() -> bool:
        nonlocal paths
        paths = list((state / "queue").glob("*.ticket"))
        if len(paths) == count:
            return True
        exited = [process for process in processes if process.poll() is not None]
        assert not exited, "gate exited before publishing its ticket: " + "\n".join(
            process.stderr.read() for process in exited
        )
        return False

    try:
        wait_until(published, timeout=30.0, interval=0.01, message=f"{count} tickets")
    except AssertionError as error:
        if str(error).startswith(f"{count} tickets"):
            pytest.fail(f"expected {count} tickets, observed {len(paths)}")
        raise
    return [json.loads(path.read_text()) for path in paths]


def _finish_controlled(process: subprocess.Popen, control: Path, result: str = "green") -> tuple[str, str]:
    assert wait_for_line(control / "entered", stop_if=lambda: process.poll() is not None) == "entered"
    # Nonblocking open proves the validator is already waiting on the FIFO. Retry only the
    # synchronization probe; never restart a validation attempt.
    fds: list[int] = []

    def reader_waiting() -> bool:
        try:
            fds.append(os.open(control / "release", os.O_WRONLY | os.O_NONBLOCK))
        except OSError as error:
            assert error.errno == errno.ENXIO, error
            return False
        return True

    wait_until(reader_waiting, timeout=30.0, interval=0.01, message="validator waiting on the release FIFO")
    fd = fds[0]
    with os.fdopen(fd, "w") as release:
        release.write(result)
    return process.communicate(timeout=60)


def _stop_controls(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
        process.communicate(timeout=20)


def _assert_queue_released(state: Path) -> None:
    assert list(state.rglob("*.ticket")) == []
    assert list(state.rglob("*.pending")) == []
    assert list(state.glob("pytest-*")) == list(gate.pytest_temp_parent(state).glob("pytest-*")) == []
    for lock in state.rglob("admission.lock"):
        with lock.open() as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _start_global_load(state: Path, control: Path, ticket_count: int = 2) -> subprocess.Popen:
    """Hold an admission lock and optional tickets in a separate process."""
    control.mkdir()
    os.mkfifo(control / "release")
    program = textwrap.dedent("""\
        import contextlib, fcntl, sys
        from pathlib import Path

        state, control = map(Path, sys.argv[1:3])
        ticket_count = int(sys.argv[3])
        (state / 'queue').mkdir(parents=True, exist_ok=True)
        with contextlib.ExitStack() as locks:
            for path in [state / 'admission.lock',
                         *[state / 'queue' / f'{index:020d}-load.ticket' for index in range(ticket_count)]]:
                held = locks.enter_context(path.open('w'))
                fcntl.flock(held, fcntl.LOCK_EX)
                held.write('{}')
                held.flush()
            (control / 'entered').write_text('entered\\n')
            with (control / 'release').open() as release:
                assert release.read() == 'green'
        for ticket in (state / 'queue').glob('*-load.ticket'):
            ticket.unlink()
    """)
    process = subprocess.Popen(
        [sys.executable, "-c", program, str(state), str(control), str(ticket_count)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert wait_for_line(control / "entered", stop_if=lambda: process.poll() is not None) == "entered"
    return process


def test_production_head_follower_reuses_green_under_global_queue_load(repo: Path, tmp_path: Path) -> None:
    _write(repo, "tests/test_control.py", CONTROL_TEST)
    head = _commit(repo, "controlled checks", "tests/test_control.py")
    state = gate.state_dir(repo)
    controls = [tmp_path / name for name in ("load", "leader", "follower")]
    processes = []
    try:
        processes.append(_start_global_load(state, controls[0]))
        processes.append(_start_controlled_gate(repo, controls[1], LU_PRE_PUSH_GATE_ADMISSION_WAIT_S="4"))
        _wait_tickets(state, 3, processes)
        processes.append(_start_controlled_gate(repo, controls[2], LU_PRE_PUSH_GATE_ADMISSION_WAIT_S="4"))
        _wait_tickets(state / "heads" / head, 2, processes)
        # Keep the synchronized load beyond one shortened allowance. The leader has
        # two real predecessors, so its valid global allowance is eight seconds.
        time.sleep(4.5)  # wall-clock hold: the allowance under test is measured in elapsed seconds
        _finish_controlled(processes[0], controls[0])
        stdout, stderr = _finish_controlled(processes[1], controls[1])
        assert processes[1].returncode == 0, stdout + stderr
        stdout, stderr = processes[2].communicate(timeout=30)
        assert processes[2].returncode == 0, stdout + stderr
        assert not (controls[2] / "entered").exists(), "identical follower must reuse green proof"
    finally:
        _stop_controls(processes)
    rows = _measurements(repo)
    assert len(rows) == 2
    leader, follower = rows
    assert leader["queue_position"] == 3
    assert set(leader["stages"]) == {"pre_commit", "pytest"}
    assert re.fullmatch(SPLIT_SUMMARY_RE, leader["pytest"])
    assert follower["detail"] == "valid receipt after coalescing"
    assert follower["coalescing_wait_s"] > 4
    assert follower["admission_wait_limit_s"] == 16
    assert "stages" not in follower and follower["queue_depth"] == 0
    assert len(_receipts(repo)) == 1
    _assert_queue_released(state)


def test_production_non_green_head_holder_keeps_later_global_allowance(repo: Path, tmp_path: Path) -> None:
    _write(repo, "tests/test_control.py", CONTROL_TEST)
    head = _commit(repo, "controlled checks", "tests/test_control.py")
    state = gate.state_dir(repo)
    controls = [tmp_path / name for name in ("head-load", "global-load", "validator")]
    processes = []
    try:
        # Legacy head holders publish no receipt; the caller must validate itself.
        processes.append(_start_global_load(state / "heads" / head, controls[0]))
        processes.append(_start_global_load(state, controls[1], ticket_count=0))
        processes.append(_start_controlled_gate(repo, controls[2], LU_PRE_PUSH_GATE_ADMISSION_WAIT_S="6"))
        _wait_tickets(state / "heads" / head, 3, processes)
        time.sleep(8)  # wall-clock hold: the coalescing wait under test is measured in elapsed seconds
        _finish_controlled(processes[0], controls[0])
        _wait_tickets(state, 1, processes[1:])
        time.sleep(5)  # wall-clock hold: no receipt may appear while the global allowance is still running
        assert _receipts(repo) == [], "head holders without green proof must not authorize reuse"
        _finish_controlled(processes[1], controls[1])
        stdout, stderr = _finish_controlled(processes[2], controls[2])
        assert processes[2].returncode == 0, stdout + stderr
    finally:
        _stop_controls(processes)
    rows = _measurements(repo)
    assert len(rows) == 1
    row = rows[0]
    assert row["coalescing_wait_s"] >= 8 and row["admission_wait_s"] > 12
    assert row["admission_wait_limit_s"] >= row["coalescing_wait_s"] + 6 - 0.02
    assert row["queue_position"] == 2 and set(row["stages"]) == {"pre_commit", "pytest"}
    assert re.fullmatch(SPLIT_SUMMARY_RE, row["pytest"])
    assert "detail" not in row and len(_receipts(repo)) == 1
    _assert_queue_released(state)


@pytest.fixture
def native_repo(tmp_path: Path) -> Path:
    """A local remote and native Git hook invoking the unchanged production entry point."""
    root = tmp_path / "native-repo"
    root.mkdir()
    remote = tmp_path / "native-remote.git"
    _git(tmp_path, "init", "--bare", str(remote))
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "gate@example.invalid")
    _git(root, "config", "user.name", "Gate Test")
    # This fixture installs its hook only after publishing the initial base.
    _git(root, "config", "core.hooksPath", str(root / ".git/hooks"))
    _write(root, ".githooks/pre_push_gate.py", GATE_PATH.read_text())
    _write(root, "scripts/pre_commit/project_python.sh", f'#!/usr/bin/env bash\nexec "{sys.executable}" "$@"\n')
    (root / "scripts/pre_commit/project_python.sh").chmod(0o755)
    _install_surface_scanners(root)
    _write(root, "pytest.ini", "[pytest]\n")
    _write(root, "tests/test_repo_wide_marker_invariant.py", REGISTRY)
    _write(root, "tests/test_invariant.py", GREEN_TEST)
    _write(root, "tests/test_scanner.py", "def test_scan():\n    assert True\n")
    _commit(root, "base", ".")
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "origin", "main")
    _git(root, "checkout", "-b", "feature")
    _write(
        root,
        ".git/hooks/pre-push",
        f"#!{sys.executable}\n"
        + textwrap.dedent("""\
        import os
        from pathlib import Path
        import subprocess
        import sys

        updates = sys.stdin.read()
        Path(os.environ['NATIVE_UPDATES']).write_text(updates)
        result = subprocess.run(
            [sys.executable, '.githooks/pre_push_gate.py', '--launcher',
             'scripts/pre_commit/project_python.sh', '--config', '.pre-commit-config.yaml',
             *sys.argv[1:]], input=updates, text=True, timeout=120,
        )
        sys.exit(result.returncode)
    """),
    )
    (root / ".git/hooks/pre-push").chmod(0o755)
    return root


@pytest.mark.parametrize(
    ("source", "movement", "owner"),
    [
        ("HEAD", "none", "native-task_10523"),
        ("HEAD", "same-sha", "native-task_10523"),
        ("HEAD", "different-sha", "native-task_10523"),
        ("detached", "none", None),
        ("refs/heads/feature", "same-sha", "private@example.invalid"),
        ("HEAD", "none", None),
        ("HEAD", "none", "bad\nowner"),
    ],
)
def test_native_push_freezes_ticket_attribution_before_queue_waits(
    native_repo: Path,
    tmp_path: Path,
    source: str,
    movement: str,
    owner: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if owner is None:
        monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    _write(native_repo, "change.txt", "outgoing\n")
    head = _commit(native_repo, "outgoing", "change.txt")
    if source == "detached":
        _git(native_repo, "checkout", "--detach", head)
    state = native_repo / ".git/lu-pre-push-gate"
    head_state = state / "heads" / head
    head_state.mkdir(parents=True)
    expected = {
        "head": head,
        "branch": "unknown" if source == "detached" else "refs/heads/feature",
        "task_owner": owner if owner == "native-task_10523" else "unknown",
    }
    updates = tmp_path / "native-updates"
    environment = {
        "PRE_COMMIT_HOME": str(tmp_path / "pc"),
        "TMPDIR": str(tmp_path),
        "LU_PRE_PUSH_GATE_MAX_TEST_PROCESSES": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "NATIVE_UPDATES": str(updates),
        "UNRELATED_SECRET": "must-not-appear-in-ticket",
    }
    if owner is not None:
        environment["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] = owner
    processes = []
    with (state / "admission.lock").open("w") as global_lock, (head_state / "admission.lock").open("w") as head_lock:
        fcntl.flock(global_lock, fcntl.LOCK_EX)
        fcntl.flock(head_lock, fcntl.LOCK_EX)
        try:
            refspec = "HEAD:refs/heads/feature" if source == "detached" else source
            process = subprocess.Popen(
                [GIT, "push", "-u", "origin", refspec],
                cwd=native_repo,
                env=_env(environment),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            processes.append(process)
            assert _wait_tickets(head_state, 1, processes) == [expected]
            assert updates.read_text() == (
                f"{'HEAD' if source == 'detached' else source} {head} refs/heads/feature {ZERO_SHA}\n"
            )
            if movement == "same-sha":
                _git(native_repo, "checkout", "-b", "later", head)
            elif movement == "different-sha":
                _git(native_repo, "checkout", "main")
            assert _wait_tickets(head_state, 1, processes) == [expected]
            fcntl.flock(head_lock, fcntl.LOCK_UN)
            if movement != "different-sha":
                assert _wait_tickets(state, 1, processes) == [expected]
                assert _wait_tickets(head_state, 1, processes) == [expected]
            fcntl.flock(global_lock, fcntl.LOCK_UN)
            stdout, stderr = process.communicate(timeout=120)
            row = _measurements(native_repo)[-1]
            remote = _git(native_repo, "ls-remote", "origin", "refs/heads/feature").stdout.strip()
            if movement == "different-sha":
                assert process.returncode != 0, (stdout, stderr)
                assert row["reason"] == "tree_mismatch"
                assert row["outcome"] == "refused"
                assert "stages" not in row and _receipts(native_repo) == [] and remote == ""
            else:
                assert process.returncode == 0, (stdout, stderr)
                assert row["local_ref"] == ("HEAD" if source == "detached" else source)
                assert row["outcome"] == "green"
                assert row["stages"]["pre_commit"]["outcome"] == "green"
                assert row["stages"]["pytest"]["outcome"] == "green"
                assert remote == f"{head}\trefs/heads/feature"
        finally:
            fcntl.flock(head_lock, fcntl.LOCK_UN)
            fcntl.flock(global_lock, fcntl.LOCK_UN)
            _stop_controls(processes)
    _assert_queue_released(state)


def test_equivalent_production_followers_never_register_global_tickets(repo: Path, tmp_path: Path) -> None:
    _write(repo, "tests/test_control.py", CONTROL_TEST)
    head = _commit(repo, "controlled checks", "tests/test_control.py")
    state = gate.state_dir(repo)
    controls = [tmp_path / f"control-{n}" for n in range(3)]
    processes = []
    try:
        processes.append(_start_controlled_gate(repo, controls[0], LEARN_UKRAINIAN_DISPATCH_TASK_ID="leader"))
        wait_for_line(controls[0] / "entered", stop_if=lambda: processes[0].poll() is not None)
        for n in (1, 2):
            processes.append(
                _start_controlled_gate(repo, controls[n], LEARN_UKRAINIAN_DISPATCH_TASK_ID=f"follower-{n}")
            )
            _wait_tickets(state / "heads" / head, n + 1, processes)
        assert _wait_tickets(state, 1, processes) == [
            {"head": head, "branch": "refs/heads/feature", "task_owner": "leader"}
        ]
        stdout, stderr = _finish_controlled(processes[0], controls[0])
        assert processes[0].returncode == 0, stdout + stderr
        for process, control in zip(processes[1:], controls[1:], strict=True):
            stdout, stderr = process.communicate(timeout=60)
            assert process.returncode == 0, stdout + stderr
            assert not (control / "entered").exists(), "follower reran checks instead of reusing exact green proof"
    finally:
        _stop_controls(processes)
    rows = _measurements(repo)
    assert len(rows) == 3
    assert sum("stages" in row for row in rows) == 1
    followers = [row for row in rows if row.get("detail") == "valid receipt after coalescing"]
    assert len(followers) == 2 and all(row["queue_depth"] == 0 for row in followers)
    _assert_queue_released(state)


def test_same_head_different_base_production_follower_runs_the_missing_check(repo: Path, tmp_path: Path) -> None:
    _write(repo, "tests/test_red.py", RED_TEST)
    narrow_base = _commit(repo, "wide range must check red", "tests/test_red.py")
    _write(repo, "tests/test_control.py", CONTROL_TEST)
    head = _commit(repo, "narrow range is green", "tests/test_control.py")
    state = gate.state_dir(repo)
    controls = [tmp_path / "narrow", tmp_path / "wide"]
    processes = []
    try:
        processes.append(_start_controlled_gate(repo, controls[0], base=narrow_base))
        wait_for_line(controls[0] / "entered", stop_if=lambda: processes[0].poll() is not None)
        processes.append(_start_controlled_gate(repo, controls[1]))
        _wait_tickets(state / "heads" / head, 2, processes)
        assert len(_wait_tickets(state, 1, processes)) == 1
        _finish_controlled(processes[0], controls[0])
        assert processes[0].returncode == 0
        stdout, stderr = _finish_controlled(processes[1], controls[1])
        assert processes[1].returncode == gate.EXIT_REFUSED, stdout + stderr
        assert (
            "tests/test_red.py::test_broken" in _verdict(subprocess.CompletedProcess([], 1, stderr=stderr))["failing"]
        )
    finally:
        _stop_controls(processes)
    assert [row["outcome"] for row in _measurements(repo)] == ["green", "refused"]
    _assert_queue_released(state)


@pytest.mark.parametrize("ending", ["refused", "incomplete", "interrupted"])
def test_non_green_production_leader_releases_and_follower_checks_once(
    repo: Path, tmp_path: Path, ending: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "1")
    _write(repo, "tests/test_control.py", CONTROL_TEST)
    head = _commit(repo, "controlled checks", "tests/test_control.py")
    state = gate.state_dir(repo)
    controls = [tmp_path / "leader", tmp_path / "follower"]
    processes = []
    try:
        options = {"LU_PRE_PUSH_GATE_RUN_BUDGET_S": "8"} if ending == "incomplete" else {}
        processes.append(_start_controlled_gate(repo, controls[0], **options))
        wait_for_line(controls[0] / "entered", stop_if=lambda: processes[0].poll() is not None)
        processes.append(_start_controlled_gate(repo, controls[1]))
        _wait_tickets(state / "heads" / head, 2, processes)
        if ending == "refused":
            _finish_controlled(processes[0], controls[0], "red")
            assert processes[0].returncode == gate.EXIT_REFUSED
        else:
            if ending == "interrupted":
                processes[0].send_signal(signal.SIGINT)
            processes[0].communicate(timeout=30)
            assert processes[0].returncode == gate.EXIT_INCOMPLETE
        assert _receipts(repo) == []
        stdout, stderr = _finish_controlled(processes[1], controls[1])
        assert processes[1].returncode == 0, stdout + stderr
    finally:
        _stop_controls(processes)
    rows = _measurements(repo)
    assert len(rows) == 2
    if ending == "interrupted":
        assert rows[0]["reason"] == "interrupted"
    assert sum(row.get("outcome") == "green" for row in rows) == 1
    assert all("stages" in row for row in rows), "non-green leader cannot authorize reuse"
    _assert_queue_released(state)


@pytest.mark.parametrize("change", ["tracked", "untracked"])
def test_production_follower_rechecks_inputs_before_reusing_leader_receipt(
    repo: Path, tmp_path: Path, change: str
) -> None:
    _write(repo, "tests/test_control.py", CONTROL_TEST)
    head = _commit(repo, "controlled checks", "tests/test_control.py")
    state = gate.state_dir(repo)
    controls = [tmp_path / "leader", tmp_path / "follower"]
    processes = []
    try:
        processes.append(_start_controlled_gate(repo, controls[0]))
        wait_for_line(controls[0] / "entered", stop_if=lambda: processes[0].poll() is not None)
        processes.append(_start_controlled_gate(repo, controls[1]))
        _wait_tickets(state / "heads" / head, 2, processes)
        if change == "tracked":
            _write(repo, "tests/test_control.py", RED_TEST)
        else:
            _write(repo, "conftest.py", "# an untracked overlay\n")
        _finish_controlled(processes[0], controls[0])
        stdout, stderr = processes[1].communicate(timeout=30)
        assert processes[1].returncode == gate.EXIT_REFUSED, stdout + stderr
        verdict = _verdict(subprocess.CompletedProcess([], 1, stderr=stderr))
        assert verdict["reason"] == ("dirty_tree" if change == "tracked" else "untracked_inputs")
        assert not (controls[1] / "entered").exists()
    finally:
        _stop_controls(processes)
    _assert_queue_released(state)


@pytest.mark.parametrize("owner", [None, "", "safe-task_10523", "private@example.invalid", "bad\nowner", "x" * 129])
def test_ticket_publication_is_atomic_and_metadata_is_allowlisted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, owner: str | None
) -> None:
    if owner is None:
        monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    else:
        monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", owner)
    monkeypatch.setenv("UNRELATED_SECRET", "never-publish-this")
    update = gate.Update("refs/heads/frozen", "a" * 40, "unused-remote", "b" * 40)
    original = Path.rename
    observed = []

    def rename(source: Path, target: Path):
        if source.suffix == ".pending":
            assert list(source.parent.glob("*.ticket")) == []
            observed.append(json.loads(source.read_text()))
            with source.open() as held, pytest.raises(BlockingIOError):
                fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return original(source, target)

    monkeypatch.setattr(Path, "rename", rename)
    with gate.Admission(tmp_path, 0, update=update) as admitted:
        identity = json.loads(admitted._ticket.read_text())
        assert identity == {
            "head": "a" * 40,
            "branch": "refs/heads/frozen",
            "task_owner": owner if owner == "safe-task_10523" else "unknown",
        }
        assert admitted._ticket.stat().st_mode & 0o777 == 0o600
        assert observed == [identity]
    _assert_queue_released(tmp_path)


@pytest.mark.parametrize("binding", ["matching", "mismatched", "detached", "missing", "missing-sha", "nonbranch"])
def test_head_ticket_identity_requires_an_exact_named_binding(
    native_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    binding: str,
) -> None:
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "binding-control")
    head = _git(native_repo, "rev-parse", "HEAD").stdout.strip()
    if binding == "mismatched":
        _write(native_repo, "different.txt", "different\n")
        _commit(native_repo, "different head", "different.txt")
    elif binding == "detached":
        _git(native_repo, "checkout", "--detach", head)
    elif binding in {"missing", "missing-sha"}:
        _git(native_repo, "symbolic-ref", "HEAD", "refs/heads/unborn")
        if binding == "missing-sha":
            head = ""
    elif binding == "nonbranch":
        _git(native_repo, "update-ref", "refs/control/nonbranch", head)
        _git(native_repo, "symbolic-ref", "HEAD", "refs/control/nonbranch")
    update = gate.Update("HEAD", head, "unused", ZERO_SHA)
    assert gate.ticket_identity(update, native_repo) == {
        "head": head,
        "branch": "refs/heads/feature" if binding == "matching" else "unknown",
        "task_owner": "binding-control",
    }
    if binding in {"mismatched", "missing"}:
        with pytest.raises(gate.GateOutcome) as raised:
            gate.build_plan(update, native_repo)
        assert raised.value.reason == "tree_mismatch"


@pytest.mark.parametrize("source", ["HEAD", "HEAD~1", "refs/heads/direct", "a" * 40])
def test_ticket_without_resolved_head_never_guesses_a_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
) -> None:
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.setattr(gate, "git_ok", lambda *_args, **_kwargs: None)
    update = gate.Update(source, "a" * 40, "unused", ZERO_SHA)
    expected = {"head": "a" * 40, "branch": "unknown" if source == "HEAD" else source, "task_owner": "unknown"}
    assert gate.ticket_identity(update, tmp_path) == expected
    assert gate.ticket_identity(update) == expected


@pytest.mark.parametrize("field", ["head", "tree", "base", "registry_version"])
def test_missing_immutable_identity_cannot_reuse_even_a_matching_green_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    plan = _plan(**{field: ""})
    gate.write_receipt(tmp_path, plan, time.time())
    monkeypatch.setattr(gate, "build_plan", lambda *_args: plan)
    monkeypatch.setattr(gate, "state_dir", lambda *_args: tmp_path)
    with pytest.raises(gate.GateOutcome, match="immutable validation identity"):
        gate.validate(
            gate.Update("refs/heads/feature", plan.head, "unused", ZERO_SHA), tmp_path, "unused", "unused", {}
        )
    assert not (tmp_path / "queue").exists()


@pytest.mark.parametrize("area", ["heads", "head"])
def test_unsafe_coalescing_directory_never_reuses_green(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, area: str
) -> None:
    plan = _plan()
    gate.write_receipt(tmp_path, plan, time.time())
    outside = tmp_path / "preserve"
    outside.mkdir()
    if area == "heads":
        (tmp_path / "heads").symlink_to(outside, target_is_directory=True)
    else:
        (tmp_path / "heads").mkdir()
        (tmp_path / "heads" / plan.head).symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(gate, "build_plan", lambda *_args: plan)
    monkeypatch.setattr(gate, "state_dir", lambda *_args: tmp_path)
    with pytest.raises(gate.GateOutcome, match="coalescing directory is unsafe"):
        gate.validate(
            gate.Update("refs/heads/feature", plan.head, "unused", ZERO_SHA), tmp_path, "unused", "unused", {}
        )
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("change", ["registry", "selection"])
def test_same_head_production_registry_or_selection_difference_cannot_coalesce(
    repo: Path, tmp_path: Path, change: str
) -> None:
    _write(repo, "tests/test_red.py", RED_TEST)
    base = _commit(repo, "negative selection control", "tests/test_red.py")
    _write(repo, "tests/test_control.py", CONTROL_TEST)
    head = _commit(repo, "controlled checks", "tests/test_control.py")
    state = gate.state_dir(repo)
    controls = [tmp_path / "original", tmp_path / "changed"]
    processes = []
    try:
        processes.append(_start_controlled_gate(repo, controls[0], base=base))
        wait_for_line(controls[0] / "entered", stop_if=lambda: processes[0].poll() is not None)
        processes.append(_start_controlled_gate(repo, controls[1], base=base, registry_change=change))
        _wait_tickets(state / "heads" / head, 2, processes)
        _finish_controlled(processes[0], controls[0])
        assert processes[0].returncode == 0
        stdout, stderr = _finish_controlled(processes[1], controls[1])
        assert processes[1].returncode == (0 if change == "registry" else gate.EXIT_REFUSED), stdout + stderr
        if change == "selection":
            assert (
                "tests/test_red.py::test_broken"
                in _verdict(subprocess.CompletedProcess([], 1, stderr=stderr))["failing"]
            )
    finally:
        _stop_controls(processes)
    rows = _measurements(repo)
    assert len(rows) == 2 and all("stages" in row for row in rows)
    _assert_queue_released(state)


def test_explicit_production_resubmission_joins_global_tail_after_incomplete(repo: Path, tmp_path: Path) -> None:
    _write(repo, "tests/test_control.py", CONTROL_TEST)
    _commit(repo, "controlled checks", "tests/test_control.py")
    other = tmp_path / "other-worktree"
    _git(repo, "worktree", "add", "-b", "other", str(other), "HEAD")
    _write(other, "notes.txt", "different outgoing head\n")
    _commit(other, "other head", "notes.txt")
    state = gate.state_dir(repo)
    state.mkdir(parents=True)
    processes = []
    controls = [tmp_path / name for name in ("incomplete", "older", "resubmission")]
    try:
        with (state / "admission.lock").open("w") as legacy:
            fcntl.flock(legacy, fcntl.LOCK_EX)
            processes.append(_start_controlled_gate(repo, controls[0], LU_PRE_PUSH_GATE_ADMISSION_WAIT_S="0"))
            stdout, stderr = processes[0].communicate(timeout=30)
            assert processes[0].returncode == gate.EXIT_INCOMPLETE, stdout + stderr
            assert _verdict(subprocess.CompletedProcess([], 75, stderr=stderr))["reason"] == "validation_incomplete"
            assert list(state.rglob("*.ticket")) == []
            processes.append(_start_controlled_gate(other, controls[1], LEARN_UKRAINIAN_DISPATCH_TASK_ID="older"))
            _wait_tickets(state, 1, processes[1:])
            processes.append(_start_controlled_gate(repo, controls[2], LEARN_UKRAINIAN_DISPATCH_TASK_ID="resubmission"))
            _wait_tickets(state, 2, processes[1:])
            identities = [json.loads(path.read_text()) for path in sorted((state / "queue").glob("*.ticket"))]
            assert [identity["task_owner"] for identity in identities] == ["older", "resubmission"]
        wait_for_line(controls[1] / "entered", stop_if=lambda: processes[1].poll() is not None)
        assert not (controls[2] / "entered").exists(), "resubmission bypassed the existing queue predecessor"
        _finish_controlled(processes[1], controls[1])
        _finish_controlled(processes[2], controls[2])
        assert processes[1].returncode == processes[2].returncode == 0
    finally:
        _stop_controls(processes)
    rows = _measurements(repo)
    assert [row["outcome"] for row in rows] == ["validation_incomplete", "green", "green"]
    _assert_queue_released(state)


def test_coalescing_and_global_wait_share_the_original_hard_ceiling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = FakeClock()
    monkeypatch.setattr(gate, "time", clock)
    monkeypatch.setattr(gate, "ADMISSION_MAX_WAIT_S", 1.5)
    head_state = tmp_path / "head"
    holder = gate.Admission(head_state, 1)
    holder.__enter__()
    clock.on_sleep = lambda: holder.__exit__() if clock.now >= 1 else None
    with gate.Admission(head_state, 1) as grouped:
        assert grouped.waited >= 1
        with gate.Admission(tmp_path, 1):
            other, fd = _locked_ticket(tmp_path, "00000000000000000000-other")
            try:
                admission = gate.Admission(tmp_path, 1, prior=grouped)
                with pytest.raises(gate.GateOutcome, match="admission_timeout"), admission:
                    pytest.fail("both waits must share a clock and hard ceiling")
                assert admission.waited == 1.5
            finally:
                other.unlink()
                os.close(fd)
    _assert_queue_released(tmp_path)


def test_global_allowance_after_failed_head_holder_starts_at_the_transition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = FakeClock()
    monkeypatch.setattr(gate, "time", clock)
    head_state = tmp_path / "head"
    holder = gate.Admission(head_state, 1)
    holder.__enter__()
    clock.on_sleep = lambda: holder.__exit__() if clock.now >= 0.8 else None
    with gate.Admission(head_state, 1) as grouped:
        assert grouped.waited == pytest.approx(0.8)
        assert grouped.wait_limit == 1
        # The head holder failed without publishing proof. A different global
        # holder arrived meanwhile, so this caller now needs its own full wait.
        with gate.Admission(tmp_path, 1) as global_holder:
            clock.on_sleep = lambda: global_holder.__exit__() if clock.now >= 1.6 else None
            with gate.Admission(tmp_path, 1, prior=grouped) as admitted:
                assert admitted.waited >= 1.6
                assert admitted.wait_limit == pytest.approx(1.8)
                assert admitted._started == grouped._started
    assert list((tmp_path / "receipts").glob("*.json")) == []
    _assert_queue_released(tmp_path)


@pytest.mark.parametrize("kind", ["live", "stale", "symlink", "directory", "fifo", "dangling"])
def test_head_allowance_counts_only_flock_live_regular_global_tickets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    clock = FakeClock()
    monkeypatch.setattr(gate, "time", clock)
    queue = tmp_path / "queue"
    queue.mkdir()
    ticket = queue / "00000000000000000000-global.ticket"
    target = tmp_path / "preserve"
    target.write_text("preserve me")
    fd = os.open(target, os.O_RDONLY)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if kind == "live":
        ticket.touch()  # a legacy empty ticket is still live when locked
        os.close(fd)
        fd = os.open(ticket, os.O_RDONLY)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    elif kind == "stale":
        ticket.write_text('{"head": "forged"}')
    elif kind in {"symlink", "dangling"}:
        ticket.symlink_to(target if kind == "symlink" else tmp_path / "missing")
    elif kind == "directory":
        ticket.mkdir()
    else:
        os.mkfifo(ticket)
    head_state = tmp_path / "head"
    holder = gate.Admission(head_state, 1)
    holder.__enter__()
    clock.on_sleep = lambda: holder.__exit__() if clock.now >= 1.2 else None
    follower = gate.Admission(head_state, 1, global_state=tmp_path)
    try:
        if kind == "live":
            with follower:
                assert follower.waited >= 1.2
                assert follower.wait_limit == 2
                assert ticket.exists()
        else:
            with pytest.raises(gate.GateOutcome, match="admission_timeout"), follower:
                pytest.fail("non-live global tickets must not grow the allowance")
            assert follower.waited == follower.wait_limit == 1
            assert not os.path.lexists(ticket)
        assert target.read_text() == "preserve me"
    finally:
        holder.__exit__()
        os.close(fd)
        ticket.unlink(missing_ok=True)
    _assert_queue_released(tmp_path)


def test_head_allowance_global_depth_still_respects_total_hard_ceiling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = FakeClock()
    monkeypatch.setattr(gate, "time", clock)
    monkeypatch.setattr(gate, "ADMISSION_MAX_WAIT_S", 1.5)
    with gate.Admission(tmp_path, 1), gate.Admission(tmp_path / "head", 1):
        follower = gate.Admission(tmp_path / "head", 1, global_state=tmp_path)
        with pytest.raises(gate.GateOutcome, match="admission_timeout"), follower:
            pytest.fail("live global depth cannot raise the hard ceiling")
        assert follower.waited == follower.wait_limit == 1.5
    _assert_queue_released(tmp_path)


def test_owner_is_frozen_before_any_wait_and_preserved_on_global_ticket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "original-task")
    update = gate.Update("refs/heads/original", "a" * 40, "unused", ZERO_SHA)
    with gate.Admission(tmp_path / "head", 1, update=update) as grouped:
        monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "later-task")
        with gate.Admission(tmp_path, 1, update=update, prior=grouped) as admitted:
            assert json.loads(admitted._ticket.read_text()) == {
                "head": "a" * 40,
                "branch": "refs/heads/original",
                "task_owner": "original-task",
            }
    _assert_queue_released(tmp_path)


def test_coalescing_receipt_reuse_preserves_remaining_multi_ref_execution_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = FakeClock()
    monkeypatch.setattr(gate, "time", clock)
    monkeypatch.setattr(gate, "build_plan", lambda *_args: _plan())
    monkeypatch.setattr(gate, "state_dir", lambda *_args: tmp_path)
    budget = gate.Budget(10)
    assert budget.after_admission(0) == 10
    clock.now = 2  # the earlier ref already consumed two seconds of execution
    head_state = gate.coalescing_state(tmp_path, _plan())
    holder = gate.Admission(head_state, gate.ADMISSION_WAIT_S)
    holder.__enter__()

    def finish_holder():
        gate.write_receipt(tmp_path, _plan(), clock.time())
        holder.__exit__()

    clock.on_sleep = finish_holder
    event = {}
    try:
        gate.validate(
            gate.Update("refs/heads/feature", "a" * 40, "unused", ZERO_SHA), tmp_path, "unused", "unused", event, budget
        )
    finally:
        holder.__exit__()
    assert event["detail"] == "valid receipt after coalescing" and event["queue_depth"] == 0
    assert budget.deadline - clock.now == pytest.approx(8)
    assert event["admission_wait_s"] == 0.2
    _assert_queue_released(tmp_path)


def test_metadata_publication_error_removes_partial_ticket_and_releases_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_publication(_identity, stream, **_kwargs):
        stream.write('{"head":')
        raise OSError("synthetic metadata publication error")

    monkeypatch.setattr(gate.json, "dump", fail_publication)
    with pytest.raises(OSError, match="synthetic metadata publication error"):
        with gate.Admission(tmp_path, 1, update=gate.Update("refs/heads/feature", "a" * 40, "unused", ZERO_SHA)):
            pytest.fail("partial metadata must never become a live ticket")
    _assert_queue_released(tmp_path)


def test_unsafe_lock_path_cannot_authorize_validation(repo: Path) -> None:
    _write(repo, "tests/test_new.py", GREEN_TEST)
    head = _commit(repo, "green", "tests/test_new.py")
    state = gate.state_dir(repo)
    head_state = state / "heads" / head
    head_state.mkdir(parents=True)
    target = repo.parent / "preserve-lock-target"
    target.write_text("preserve me")
    (head_state / "admission.lock").symlink_to(target)
    result = _run_gate(repo)
    assert result.returncode == gate.EXIT_INCOMPLETE
    assert _verdict(result)["reason"] == "validation_error"
    assert _receipts(repo) == [] and target.read_text() == "preserve me"
    assert list(state.rglob("*.ticket")) == []


# ---- #10555: scoped reservations and durable attempts ---------------------------------------


@pytest.mark.parametrize("value", ["", "0", "3", "02", " 2", "+2", "2.0", "nan", "inf", "٢", "9" * 5000])
def test_concurrency_configuration_never_interprets_garbage_as_permission(value, monkeypatch):
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, value)
    with pytest.raises(gate.GateOutcome) as raised:
        gate.concurrent_run_limit()
    assert raised.value.reason == "invalid_configuration" and raised.value.incomplete


@pytest.mark.parametrize("value,expected", [(None, 1), ("1", 1), ("2", 2)])
def test_only_explicit_experiment_adds_a_reservation(value, expected, monkeypatch):
    if value is None:
        monkeypatch.delenv(gate.MAX_CONCURRENT_RUNS_ENV, raising=False)
    else:
        monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, value)
    assert gate.concurrent_run_limit() == expected


@pytest.mark.parametrize(
    "load,memory,qualified",
    [
        (0.0, "MemAvailable: 8388608 kB\n", True),
        (11.99, "MemAvailable: 8388608 kB\n", True),
        (12.0, "MemAvailable: 8388608 kB\n", False),
        (float("nan"), "MemAvailable: 8388608 kB\n", False),
        (float("inf"), "MemAvailable: 8388608 kB\n", False),
        (-1.0, "MemAvailable: 8388608 kB\n", False),
        (0.0, "MemAvailable: 8388607 kB\n", False),
        (0.0, "MemAvailable: garbage kB\n", False),
        (0.0, "", False),
    ],
)
def test_parallel_admission_qualifies_only_current_numeric_resources(load, memory, qualified, monkeypatch):
    original = Path.read_text
    monkeypatch.setattr(gate.os, "getloadavg", lambda: (load, load, load))
    monkeypatch.setattr(
        Path, "read_text", lambda path, *a, **kw: memory if str(path) == "/proc/meminfo" else original(path, *a, **kw)
    )
    assert gate.admission_resources()["qualified"] is qualified


def test_resource_read_failure_is_unknown(monkeypatch):
    def unavailable():
        raise OSError("load unavailable")

    monkeypatch.setattr(gate.os, "getloadavg", unavailable)
    assert gate.admission_resources() == {"load_1m": None, "mem_available_bytes": None, "qualified": False}


def _raw_measurements(repo):
    return [json.loads(line) for line in (gate.state_dir(repo) / "measurements.jsonl").read_text().splitlines()]


def test_invalid_concurrency_cannot_reuse_green_and_has_paired_durable_attempt(repo):
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "new test", "tests/test_new.py")
    assert _run_gate(repo).returncode == 0
    assert _run_gate(repo, extra_env={gate.MAX_CONCURRENT_RUNS_ENV: "garbage"}).returncode == 75
    begin, terminal = _raw_measurements(repo)[-2:]
    assert begin["phase"] == "BEGIN" and terminal["phase"] == "TERMINAL"
    assert begin["attempt_id"] == terminal["attempt_id"]
    assert begin["fingerprints"] == terminal["fingerprints"]
    assert re.fullmatch("[0-9a-f]{64}", begin["fingerprints"]["input"])
    assert terminal["reason"] == "invalid_configuration"
    assert terminal["begin_durable"] is True
    assert terminal["effective_test_processes"] is None
    assert terminal["peak_memory_bytes"] is None


@pytest.mark.parametrize("ending", ["green", "red", "incomplete"])
def test_actual_missing_user_bus_runs_each_serial_check_once(repo, ending, monkeypatch):
    _write(
        repo,
        "scripts/pre_commit/project_python.sh",
        textwrap.dedent(f"""\
        #!/bin/bash
        if [ "$1" = scripts/audit/lint_opsec_leaks.py ]; then echo opsec >> scans; exec "{sys.executable}" "$@"; fi
        if [ "$4" = check-no-internal-ids ]; then echo internal-ids >> scans; exec "{sys.executable}" "$@"; fi
        if [ "$2" = pre_commit ]; then echo pre >> checks; exit 0; fi
        if [ "$2" = scripts.ci.pre_push_shadow ]; then echo shadow >> checks; echo '{{"selected_tests":[]}}'; exit 0; fi
        echo pytest >> checks
        echo '1 passed in 0.1s'
        exit {dict(green=0, red=1, incomplete=2)[ending]}
    """),
    )
    _commit(repo, "serial fallback control", "scripts/pre_commit/project_python.sh")
    monkeypatch.chdir(repo)
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "2")
    # The scope is attempted only for at most 4 effective workers; a pushing caller's override must not decide.
    monkeypatch.delenv(gate.MAX_TEST_PROCESSES_ENV, raising=False)
    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", "unix:path=/nonexistent-gate-test-bus")
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(repo.parent / "absent-runtime"))
    monkeypatch.setattr(
        gate, "admission_resources", lambda: {"qualified": True, "load_1m": 0.5, "mem_available_bytes": 9 * 1024**3}
    )
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    code = gate.main(
        [
            "--launcher",
            str(repo / "scripts/pre_commit/project_python.sh"),
            "--config",
            str(repo / ".pre-commit-config.yaml"),
        ],
        stdin=f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
    )
    assert code == dict(green=0, red=1, incomplete=75)[ending]
    assert sorted((repo / "checks").read_text().splitlines()) == ["pre", "pytest", "shadow"]
    assert (repo / "scans").read_text().splitlines() == ["opsec", "internal-ids"]
    row = _measurements(repo)[-1]
    assert row["scope"]["status"] == "serial"
    assert row["scope"]["reason"].startswith("scope_setup_")
    assert row["peak_memory_bytes"] is None
    assert row["peak_memory_unknown_reason"] == "no_supported_scope"
    assert row["execution_s"] >= 0 and row["queue_wait_s"] >= 0
    assert set(row["stages"]) == {"pre_commit", "pytest"}
    _assert_queue_released(gate.state_dir(repo))


def _fake_cgroup(root, unit):
    group = root / unit
    group.mkdir()
    (group / "memory.max").write_text(str(gate.SCOPE_MEMORY_MAX))
    (group / "memory.peak").write_text("123456")
    (group / "cgroup.events").write_text("populated 1\n")
    return group


class InjectedScope:
    def __init__(self, cgroups):
        self.cgroups = cgroups
        self.resources = {}
        self.reason = None
        self.group = None
        self.setup_s = 0.0

    def start(self, admitted):
        self.unit = f"fixture-{id(self)}.scope"
        self.group = _fake_cgroup(self.cgroups, self.unit)
        proof = {
            "mode": "optin_scope",
            "max_concurrent_runs": 2,
            "unit": self.unit,
            "cgroup": "/" + self.unit,
            "effective_workers": 4,
            "ticket_inode": os.fstat(admitted._ticket_fd).st_ino,
        }
        admitted._ticket.with_suffix(".scope.json").write_text(json.dumps(proof))
        return True

    def close(self):
        if self.group is not None:
            (self.group / "cgroup.events").write_text("populated 0\n")


@pytest.fixture
def qualified_cgroups(tmp_path, monkeypatch):
    groups = tmp_path / "cgroups"
    groups.mkdir()
    monkeypatch.setattr(gate, "CGROUP_ROOT", groups)
    monkeypatch.setattr(
        gate, "admission_resources", lambda: {"qualified": True, "load_1m": 0.5, "mem_available_bytes": 9 * 1024**3}
    )
    return groups


def test_two_scoped_holders_exclude_third_and_serial_legacy(qualified_cgroups, tmp_path):
    state = tmp_path / "state"
    with (
        gate.Admission(state, 0, scope=InjectedScope(qualified_cgroups)),
        gate.Admission(state, 0, scope=InjectedScope(qualified_cgroups)),
    ):
        with (
            pytest.raises(gate.GateOutcome, match="admission_timeout"),
            gate.Admission(state, 0, scope=InjectedScope(qualified_cgroups)),
        ):
            pytest.fail("a third scope cannot enter")
        with pytest.raises(gate.GateOutcome, match="admission_timeout"), gate.Admission(state, 0):
            pytest.fail("a default holder cannot share")
        fd = os.open(state / "admission.lock", os.O_RDWR)
        try:
            with pytest.raises(BlockingIOError):
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(fd)
    _assert_queue_released(state)


@pytest.mark.parametrize("mode", ["shared", "missing", "released", "head_only"])
def test_pytest_stale_sweep_requires_live_exclusive_global_admission(qualified_cgroups, tmp_path, monkeypatch, mode):
    state = tmp_path / "state"
    state.mkdir()
    stale = state / "pytest-other"
    stale.mkdir()
    (stale / "preserved").write_text("other run")
    current = gate.pytest_temp_parent(state) / "pytest-current"
    current.mkdir()
    (current / "preserved").write_text("other run")
    monkeypatch.setattr(gate, "state_dir", lambda _root: state)
    monkeypatch.setattr(gate, "run_bounded", lambda *_args, **_kwargs: (0, "1 passed in 0.1s"))
    admission = None
    if mode == "shared":
        admission = gate.Admission(state, 0, scope=InjectedScope(qualified_cgroups))
    elif mode == "released":
        admission = gate.Admission(state, 0)
    elif mode == "head_only":
        admission = gate.Admission(state / "heads" / "other", 0)
    diagnostics = {}
    try:
        if admission is not None:
            admission.__enter__()
            if mode == "released":
                admission.__exit__()
        assert (
            gate.run_pytest_stage(
                _plan(),
                tmp_path,
                "launcher",
                time.monotonic() + 30,
                admission=admission,
                diagnostics=diagnostics,
            )
            == "1 passed in 0.1s; 1 passed in 0.1s"
        )
        assert (stale / "preserved").read_text() == (current / "preserved").read_text() == "other run"
        assert list(state.glob("pytest-*")) == [stale]
        assert list(current.parent.glob("pytest-*")) == [current]
        assert diagnostics["stale_pytest_cleanup"] == "skipped_shared_or_unknown"
    finally:
        if admission is not None:
            admission.__exit__()


def test_a_serial_waiter_cannot_be_skipped_by_a_scoped_follower(qualified_cgroups, tmp_path):
    state = tmp_path / "state"
    with gate.Admission(state, 0, scope=InjectedScope(qualified_cgroups)):
        waiter = gate.Admission(state, 0)
        waiter._register()
        try:
            with (
                pytest.raises(gate.GateOutcome, match="admission_timeout"),
                gate.Admission(state, 0, scope=InjectedScope(qualified_cgroups)),
            ):
                pytest.fail("FIFO forbids overtaking the serial waiter")
        finally:
            waiter.__exit__()


def test_legacy_unscoped_holder_forces_optin_exclusive_admission(qualified_cgroups, tmp_path):
    with gate.Admission(tmp_path, 0):
        with (
            pytest.raises(gate.GateOutcome, match="admission_timeout"),
            gate.Admission(tmp_path, 0, scope=InjectedScope(qualified_cgroups)),
        ):
            pytest.fail("scope text cannot turn a serial holder into a shared holder")


@pytest.mark.parametrize(
    "failure",
    [
        "proof_missing",
        "wrong_inode",
        "unbounded",
        "unpopulated",
        "peak_unavailable",
        "proof_symlink",
        "proof_fifo",
        "proof_garbage",
    ],
)
def test_unknown_holder_proof_never_adds_permission(qualified_cgroups, tmp_path, failure):
    with gate.Admission(tmp_path, 0, scope=InjectedScope(qualified_cgroups)) as holder:
        path = holder._ticket.with_suffix(".scope.json")
        if failure == "proof_missing":
            path.unlink()
        elif failure == "wrong_inode":
            proof = json.loads(path.read_text())
            proof["ticket_inode"] += 1
            path.write_text(json.dumps(proof))
        elif failure == "unbounded":
            (holder.scope.group / "memory.max").write_text("max")
        elif failure == "unpopulated":
            (holder.scope.group / "cgroup.events").write_text("populated 0\n")
        elif failure == "peak_unavailable":
            (holder.scope.group / "memory.peak").unlink()
        elif failure == "proof_symlink":
            target = tmp_path / "proof"
            path.rename(target)
            path.symlink_to(target)
        elif failure == "proof_fifo":
            path.unlink()
            os.mkfifo(path)
        else:
            path.write_text("garbage")
        assert gate.scoped_holder(holder._ticket) is False
        with (
            pytest.raises(gate.GateOutcome, match="admission_timeout"),
            gate.Admission(tmp_path, 0, scope=InjectedScope(qualified_cgroups)),
        ):
            pytest.fail("unknown scope proof cannot grant admission")


def test_resource_unknown_serializes_even_an_explicit_scoped_candidate(tmp_path, qualified_cgroups, monkeypatch):
    monkeypatch.setattr(
        gate, "admission_resources", lambda: {"qualified": False, "load_1m": None, "mem_available_bytes": None}
    )
    candidate = InjectedScope(qualified_cgroups)
    with gate.Admission(tmp_path, 0, scope=candidate) as admitted:
        assert admitted.scope is None and candidate.group is None
        assert candidate.reason == "resources_unqualified_or_unknown"
        with pytest.raises(gate.GateOutcome), gate.Admission(tmp_path, 0, scope=InjectedScope(qualified_cgroups)):
            pytest.fail("unknown resources keep the holder exclusive")


def test_durable_journal_handles_short_writes_and_fsyncs_both_objects(tmp_path, monkeypatch):
    original_write = os.write
    original_fsync = os.fsync
    synced = []
    monkeypatch.setattr(gate.os, "write", lambda fd, data: original_write(fd, data[:7]))

    def sync(fd):
        synced.append(os.fstat(fd).st_mode)
        original_fsync(fd)

    monkeypatch.setattr(gate.os, "fsync", sync)
    assert gate.record(tmp_path, {"large": "x" * 10000}) is True
    assert json.loads((tmp_path / "measurements.jsonl").read_text()) == {"large": "x" * 10000}
    assert len(synced) == 2


@pytest.mark.parametrize("failure", ["zero_write", "fsync", "encode", "symlink", "fifo"])
def test_journal_failure_is_explicit_unknown(tmp_path, monkeypatch, capsys, failure):
    if failure == "zero_write":
        monkeypatch.setattr(gate.os, "write", lambda *a: 0)
    elif failure == "fsync":

        def broken(fd):
            raise OSError("durability unavailable")

        monkeypatch.setattr(gate.os, "fsync", broken)
    elif failure == "symlink":
        outside = tmp_path / "outside"
        outside.write_text("preserve")
        (tmp_path / "measurements.jsonl").symlink_to(outside)
    elif failure == "fifo":
        os.mkfifo(tmp_path / "measurements.jsonl")
    event = {"value": object()} if failure == "encode" else {"value": "data"}
    assert gate.record(tmp_path, event) is False
    assert "measurement_unavailable" in capsys.readouterr().err
    if failure == "symlink":
        assert outside.read_text() == "preserve"


def test_concurrent_large_measurements_are_complete_after_writer_exit(tmp_path):
    source = f"""import runpy,sys,pathlib
module = runpy.run_path({str(GATE_PATH)!r})
for n in range(8):
    assert module['record'](pathlib.Path(sys.argv[1]), {{'owner':sys.argv[2], 'n':n, 'large':'x'*100000}})
"""
    processes = [subprocess.Popen([sys.executable, "-c", source, str(tmp_path), str(n)], env=_env()) for n in range(2)]
    try:
        for process in processes:
            assert process.wait(timeout=30) == 0
    finally:
        _stop_controls(processes)
    rows = [json.loads(line) for line in (tmp_path / "measurements.jsonl").read_text().splitlines()]
    assert len(rows) == 16
    assert {(row["owner"], row["n"]) for row in rows} == {(str(owner), n) for owner in range(2) for n in range(8)}
    assert all(row["large"] == "x" * 100000 for row in rows)


@pytest.mark.parametrize("relative", ["/", "../x", "/a/../x", "/a//x", "x"])
def test_scope_paths_cannot_escape_the_cgroup_mount(relative):
    with pytest.raises(ValueError):
        gate.scope_cgroup(relative)


@pytest.fixture
def injected_systemd(tmp_path, monkeypatch, qualified_cgroups):
    """Source-aware injected runtime, never evidence of real cgroup enforcement."""
    binaries = tmp_path / "bin"
    binaries.mkdir()
    runner = binaries / "systemd-run"
    runner.write_text(f"""#!{sys.executable}
import os,sys,runpy,pathlib
args = sys.argv[1:]
index = args.index('--scope-child')
gate_path = args[index-1]
child_args = args[index+1:]
unit = child_args[1]
root = pathlib.Path({str(qualified_cgroups)!r})
group = root / unit
group.mkdir()
(group / 'memory.max').write_text({str(gate.SCOPE_MEMORY_MAX)!r})
(group / 'memory.peak').write_text('123456')
(group / 'cgroup.events').write_text('populated 1\\n')
(group / 'cgroup.procs').write_text(str(os.getpid()) + '\\n')
module = runpy.run_path(gate_path)
module['scope_child'].__globals__['CGROUP_ROOT'] = root
original = pathlib.Path.read_text
pathlib.Path.read_text = lambda path,*a,**kw: '0::/' + unit + '\\n' if str(path) == '/proc/self/cgroup' else original(path,*a,**kw)
try:
    sys.exit(module['scope_child'](child_args))
finally:
    (group / 'cgroup.events').write_text('populated 0\\n')
""")
    runner.chmod(0o755)
    killer = binaries / "systemctl"
    killer.write_text("#!/bin/sh\nexit 0\n")
    killer.chmod(0o755)
    monkeypatch.setenv("PATH", str(binaries) + os.pathsep + os.environ["PATH"])
    return binaries


@pytest.mark.parametrize("ending", ["green", "red", "incomplete", "missing_peak", "resource_breach", "unsettled"])
def test_injected_scope_executes_full_stages_once_and_reads_peak_before_exit(
    repo, injected_systemd, ending, monkeypatch
):
    _write(
        repo,
        "scripts/pre_commit/project_python.sh",
        textwrap.dedent(f'''\
        #!/bin/bash
        if [ "$1" = scripts/audit/lint_opsec_leaks.py ]; then echo opsec >> scans; exec "{sys.executable}" "$@"; fi
        if [ "$4" = check-no-internal-ids ]; then echo internal-ids >> scans; exec "{sys.executable}" "$@"; fi
        if [ "$2" = pre_commit ]; then echo pre >> checks; exit 0; fi
        if [ "$2" = scripts.ci.pre_push_shadow ]; then echo shadow >> checks; echo '{{"selected_tests":[]}}'; exit 0; fi
        echo pytest >> checks
        if [ {ending} = missing_peak ]; then find "{injected_systemd.parent / "cgroups"}" -name memory.peak -delete; fi
        echo '1 passed in 0.1s'
        if [ {ending} = resource_breach ]; then find "{injected_systemd.parent / "cgroups"}" -name memory.peak -exec sh -c 'echo {gate.SCOPE_MEMORY_MAX + 1} > "$1"' -- {{}} \\; ; fi
        if [ {ending} = unsettled ]; then find "{injected_systemd.parent / "cgroups"}" -name cgroup.procs -exec sh -c 'echo 999999999 >> "$1"' -- {{}} \\; ; fi
        exit {dict(green=0, red=1, incomplete=2, missing_peak=0, resource_breach=0, unsettled=0)[ending]}
    '''),
    )
    _commit(repo, "injected full scoped stages", "scripts/pre_commit/project_python.sh")
    if ending == "unsettled":
        (injected_systemd / "systemctl").write_text(f"""#!{sys.executable}
import os,sys,pathlib,signal
unit=sys.argv[-1]
group=pathlib.Path({str(injected_systemd.parent / "cgroups")!r})/unit
pid=int((group/'cgroup.procs').read_text().splitlines()[0])
os.kill(pid,signal.SIGKILL)
(group/'cgroup.events').write_text('populated 0\\n')
""")
    # The scope launcher must invoke the actual interpreter, while the stage launcher remains synthetic.
    original = gate.ResourceScope.start

    def start(scope, admitted):
        scoped_launcher = injected_systemd / "project-launcher"
        scoped_launcher.write_text(f'#!/bin/bash\nexec "{sys.executable}" "$@"\n')
        scope.launcher = str(scoped_launcher)
        return original(scope, admitted)

    monkeypatch.setattr(gate.ResourceScope, "start", start)
    original_execute = gate.ResourceScope.execute

    def execute(scope, plan, config, deadline, event, **kwargs):
        scope.launcher = str(repo / "scripts/pre_commit/project_python.sh")
        return original_execute(scope, plan, config, deadline, event, **kwargs)

    monkeypatch.setattr(gate.ResourceScope, "execute", execute)
    monkeypatch.chdir(repo)
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "2")
    # The scope is attempted only for at most 4 effective workers; a pushing caller's override must not decide.
    monkeypatch.delenv(gate.MAX_TEST_PROCESSES_ENV, raising=False)
    monkeypatch.setenv("LU_PRE_PUSH_GATE_STAGE_BUDGET_S", "300")  # the scoped child must apply this, not 600
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    code = gate.main(
        [
            "--launcher",
            str(repo / "scripts/pre_commit/project_python.sh"),
            "--config",
            str(repo / ".pre-commit-config.yaml"),
        ],
        stdin=f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
    )
    assert code == dict(green=0, red=1, incomplete=75, missing_peak=0, resource_breach=75, unsettled=75)[ending]
    assert sorted((repo / "checks").read_text().splitlines()) == ["pre", "pytest", "shadow"]
    assert (repo / "scans").read_text().splitlines() == ["opsec", "internal-ids"]
    row = _measurements(repo)[-1]
    assert row["scope"]["status"] == "supported"
    assert row["peak_memory_bytes"] == (
        None if ending == "missing_peak" else gate.SCOPE_MEMORY_MAX + 1 if ending == "resource_breach" else 123456
    )
    assert row["peak_memory_unknown_reason"] == ("cgroup_peak_unavailable" if ending == "missing_peak" else None)
    if ending in ("resource_breach", "unsettled"):
        assert _receipts(repo) == []
        assert (
            row["reason"]
            == {"resource_breach": "resource_bound_exceeded", "unsettled": "scope_cleanup_unverified"}[ending]
        )
    assert set(row["stages"]) == {"pre_commit", "pytest"}
    assert row["stage_budget_s"] == 300.0
    for stage in row["stages"].values():
        assert stage["allowance_s"] == pytest.approx(300.0) and stage["allowance_limited_by"] == "stage_budget"
    assert row["requested_test_processes"] == 4
    assert row["effective_test_processes"] in (2, 4)
    _assert_queue_released(gate.state_dir(repo))


def test_injected_scope_retains_flocks_when_launching_process_exits(tmp_path, injected_systemd, qualified_cgroups):
    state = tmp_path / "state"
    marker = tmp_path / "ready"
    release = tmp_path / "release"
    launcher = tmp_path / "launcher"
    launcher.write_text(f'#!/bin/bash\nexec "{sys.executable}" "$@"\n')
    source = f"""import runpy,pathlib,os,time
module=runpy.run_path({str(GATE_PATH)!r})
g=module['Admission'].__init__.__globals__
g['CGROUP_ROOT']=pathlib.Path({str(qualified_cgroups)!r})
g['admission_resources']=lambda: {{'qualified':True, 'load_1m':0.5, 'mem_available_bytes':9*1024**3}}
state=pathlib.Path({str(state)!r})
head=module['Admission'](state/'head',1)
head.__enter__()
scope=module['ResourceScope'](pathlib.Path({str(tmp_path)!r}),{str(launcher)!r},head)
admission=module['Admission'](state,1,scope=scope)
admission.__enter__()
# Duplicate the inherited socket in a child, so the idle executor retains its channel after launcher exit.
pid=os.fork()
if pid == 0:
    for fd in (admission._fd, admission._ticket_fd, admission._launcher_fd, head._fd, head._ticket_fd):
        os.close(fd)
    os.close(1)
    os.close(2)
    pathlib.Path({str(marker)!r}).write_text(str(admission._ticket) + '\\n')
    until = time.monotonic() + 30
    while not pathlib.Path({str(release)!r}).exists() and time.monotonic() < until:
        time.sleep(0.02)
    scope.stream.close()
    scope.channel.close()
    os._exit(0)
os._exit(0)
"""
    parent = subprocess.Popen(
        [sys.executable, "-c", source], env=_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = parent.communicate(timeout=30)
    assert parent.returncode == 0, stdout.decode() + stderr.decode()
    wait_for_line(marker)
    ticket = Path(marker.read_text().strip())
    assert gate.scoped_holder(ticket) is False
    with (
        pytest.raises(gate.GateOutcome, match="admission_timeout"),
        gate.Admission(state, 0, scope=InjectedScope(qualified_cgroups)),
    ):
        pytest.fail("orphaned scoped work cannot permit a second slot")
    # The launcher is gone; inherited scope reservations still refuse a legacy exclusive lock.
    fd = os.open(state / "admission.lock", os.O_RDWR)
    try:
        with pytest.raises(BlockingIOError):
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        release.touch()

        def lock_free() -> bool:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
            return True

        wait_until(lock_free, timeout=10.0, interval=0.05, message="scoped reservation releasing the lock")
    finally:
        release.touch()
        os.close(fd)


def test_unpaired_begin_remains_visible_after_sigkill(repo, tmp_path):
    _write(repo, "tests/test_control.py", CONTROL_TEST)
    _commit(repo, "kill attempt control", "tests/test_control.py")
    control = tmp_path / "kill"
    process = _start_controlled_gate(repo, control)
    try:
        wait_for_line(control / "entered", stop_if=lambda: process.poll() is not None)
        process.kill()
        process.communicate(timeout=30)
    finally:
        # Release the fixture child so a deliberately killed serial launcher leaves no test process.
        with (control / "release").open("w") as output:
            output.write("green")
        _stop_controls([process])
    rows = _raw_measurements(repo)
    assert len(rows) == 1 and rows[0]["phase"] == "BEGIN"
    assert "outcome" not in rows[0]


def test_sigterm_after_begin_and_before_validation_has_a_terminal_row(repo, monkeypatch):
    monkeypatch.chdir(repo)

    def interrupt():
        os.kill(os.getpid(), signal.SIGTERM)
        pytest.fail("SIGTERM must interrupt configuration")

    monkeypatch.setattr(gate, "test_process_limit", interrupt)
    assert gate.main(["--launcher", "unused", "--config", "unused"], stdin="") == 75
    begin, terminal = _raw_measurements(repo)
    assert begin["phase"] == "BEGIN"
    assert terminal["phase"] == "TERMINAL" and terminal["reason"] == "interrupted"
    assert begin["attempt_id"] == terminal["attempt_id"]
    assert _receipts(repo) == []


def test_a_ticketless_legacy_kernel_waiter_prevents_new_scoped_sharing(tmp_path, qualified_cgroups):
    with gate.Admission(tmp_path, 0, scope=InjectedScope(qualified_cgroups)) as holder:
        marker = tmp_path / "legacy-ready"
        program = """import fcntl,pathlib,sys
with pathlib.Path(sys.argv[1]).open('r+') as stream:
    pathlib.Path(sys.argv[2]).write_text('waiting\\n')
    fcntl.flock(stream,fcntl.LOCK_EX)
"""
        legacy = subprocess.Popen(
            [sys.executable, "-c", program, str(tmp_path / "admission.lock"), str(marker)], env=_env()
        )
        try:
            wait_for_line(marker, stop_if=lambda: legacy.poll() is not None)
            wait_until(
                lambda: not gate.sharing_lock_inventory(holder._fd, "READ"),
                timeout=10.0,
                interval=0.02,
                message="legacy waiter queued behind the scoped holder",
            )
            with (
                pytest.raises(gate.GateOutcome, match="admission_timeout"),
                gate.Admission(tmp_path, 0, scope=InjectedScope(qualified_cgroups)),
            ):
                pytest.fail("an earlier legacy kernel waiter cannot be bypassed")
        finally:
            legacy.terminate()
            legacy.wait(timeout=10)


@pytest.mark.parametrize("evidence", ["missing", "garbage", "invisible", "oversized", "unknown_lock"])
def test_unknown_kernel_lock_inventory_never_permits_sharing(tmp_path, monkeypatch, evidence):
    original = Path.open
    with gate.Admission(tmp_path, 0) as admitted:
        info = os.fstat(admitted._fd)
        node = f"{os.major(info.st_dev):02x}:{os.minor(info.st_dev):02x}:{info.st_ino}"
        content = {
            "garbage": b"bad\n",
            "invisible": b"",
            "oversized": b"x" * (2 * 1024**2 + 1),
            "unknown_lock": f"1: POSIX ADVISORY WRITE 0 {node} 0 EOF\n".encode(),
        }.get(evidence, b"")
        import io

        def open_file(path, *args, **kwargs):
            if str(path) == "/proc/locks":
                if evidence == "missing":
                    raise OSError("kernel inventory unavailable")
                return io.BytesIO(content)
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, "open", open_file)
        assert gate.sharing_lock_inventory(admitted._fd, "WRITE") is False


@pytest.mark.parametrize("phase", ["BEGIN", "TERMINAL"])
def test_catchable_signal_during_journal_write_keeps_complete_rows_and_refuses(repo, monkeypatch, phase):
    monkeypatch.chdir(repo)
    original = os.write
    interrupted = False

    def write(fd, data):
        nonlocal interrupted
        if not interrupted and f'"phase": "{phase}"'.encode() in bytes(data):
            interrupted = True
            os.kill(os.getpid(), signal.SIGTERM)
        return original(fd, data[:7])  # Exercise actual multi-write append under the deferred signal.

    monkeypatch.setattr(gate.os, "write", write)
    assert gate.main(["--launcher", "unused", "--config", "unused"], stdin="") == 75
    rows = _raw_measurements(repo)
    assert len(rows) == (2 if phase == "BEGIN" else 3)
    assert rows[0]["phase"] == "BEGIN"
    assert rows[-1]["outcome"] == "validation_incomplete" and rows[-1]["reason"] == "interrupted"
    assert len({row["attempt_id"] for row in rows}) == 1
    if phase == "TERMINAL":
        assert rows[-1]["measurement_unknown_reason"] == "interrupted_terminal_append"


def test_dead_scope_executor_still_requires_own_unit_descendant_cleanup(tmp_path, qualified_cgroups, monkeypatch):
    head = gate.Admission(tmp_path / "head", 0)
    scope = gate.ResourceScope(tmp_path, "unused", head)
    group = _fake_cgroup(qualified_cgroups, scope.unit)
    scope.group = "/" + scope.unit
    scope.process = subprocess.Popen([sys.executable, "-c", "pass"], env=_env())
    scope.process.wait(timeout=10)
    calls = []

    def kill(command, **kwargs):
        calls.append(command)
        (group / "cgroup.events").write_text("populated 0\n")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(gate.subprocess, "run", kill)
    scope.close()
    assert calls == [["systemctl", "--user", "kill", "--signal=SIGKILL", "--kill-whom=all", scope.unit]]
    assert scope.process is None


@pytest.mark.parametrize("failure_phase", ["BEGIN", "TERMINAL"])
def test_measurement_storage_failure_cannot_claim_green_or_start_without_begin(repo, monkeypatch, failure_phase):
    monkeypatch.chdir(repo)
    original = gate.record
    observed = []

    def record(state, event):
        observed.append(event["phase"])
        return False if event["phase"] == failure_phase else original(state, event)

    monkeypatch.setattr(gate, "record", record)

    def should_not_validate(*args, **kwargs):
        pytest.fail("no validation may start without its durable BEGIN")

    if failure_phase == "BEGIN":
        monkeypatch.setattr(gate, "validate", should_not_validate)
    assert gate.main(["--launcher", "unused", "--config", "unused"], stdin="") == 75
    assert observed == ["BEGIN", "TERMINAL"]
    assert _receipts(repo) == []


@pytest.mark.parametrize("interruption", ["state_lookup", "row_preparation"])
def test_terminal_publication_interrupt_refuses_with_paired_complete_measurements(repo, monkeypatch, interruption):
    monkeypatch.chdir(repo)
    original_state = gate.state_dir
    original_clock = gate.time.monotonic
    state_calls = 0
    interrupt_next_clock = False

    def state(root):
        nonlocal state_calls, interrupt_next_clock
        state_calls += 1
        if state_calls == 2:
            if interruption == "state_lookup":
                os.kill(os.getpid(), signal.SIGTERM)
            else:
                interrupt_next_clock = True
        return original_state(root)

    def clock():
        nonlocal interrupt_next_clock
        if interrupt_next_clock:
            interrupt_next_clock = False
            os.kill(os.getpid(), signal.SIGTERM)
        return original_clock()

    monkeypatch.setattr(gate, "state_dir", state)
    monkeypatch.setattr(gate.time, "monotonic", clock)
    assert gate.main(["--launcher", "unused", "--config", "unused"], stdin="") == 75
    rows = _raw_measurements(repo)
    assert [row["phase"] for row in rows] == ["BEGIN", "TERMINAL"]
    assert rows[0]["attempt_id"] == rows[1]["attempt_id"]
    assert rows[0]["fingerprints"] == rows[1]["fingerprints"]
    assert rows[1]["outcome"] == "validation_incomplete"
    assert rows[1]["reason"] == "interrupted"
    assert rows[1]["queue_wait_s"] == 0
    assert rows[1]["execution_s"] >= 0
    assert rows[1]["peak_memory_bytes"] is None


# ---- #10642: each blocking stage has its own allowance inside the total cap ---------------------------------


def _journal_shaped_push(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clock: FakeClock, needs: dict[str, list[float]]
) -> None:
    """Run the real stage functions on a fake clock; each command needs the next duration under its label.

    Like ``run_bounded``, a command whose deadline comes first is killed there (SIGKILL) and the
    stage ends ``validation_incomplete``; otherwise it consumes its duration and passes.
    """
    real_pre_commit, real_pytest = gate.run_pre_commit_stage, gate.run_pytest_stage
    _fake_validation(tmp_path, monkeypatch, clock)
    monkeypatch.setattr(gate, "run_pre_commit_stage", real_pre_commit)
    monkeypatch.setattr(gate, "run_pytest_stage", real_pytest)
    monkeypatch.setattr(gate.Admission, "_exclusive", False, raising=False)  # no stale-temp sweep
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "1")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "gate-test")  # a dispatch caps pytest processes
    remaining = {label: iter(durations) for label, durations in needs.items()}

    def run_bounded(command, *, cwd, deadline, label, diagnostics=None):
        need = next(remaining[label])
        if clock.now + need > deadline:
            clock.now = max(clock.now, deadline)
            if diagnostics is not None:
                diagnostics.update(returncode=-signal.SIGKILL, signal=signal.SIGKILL, child_unavailable_reason=None)
            raise gate.GateOutcome(
                "validation_incomplete", f"{label}: exceeded the time budget (timeout)", incomplete=True
            )
        clock.now += need
        if diagnostics is not None:
            diagnostics.update(returncode=0, signal=None, child_unavailable_reason=None)
        return 0, f"1 passed in {need}s"

    monkeypatch.setattr(gate, "run_bounded", run_bounded)


# Synthetic values in the shape #10642 reports: pre-commit spends part of a shared budget, then the
# pytest stage is killed when the remainder runs out, with no failing test.
SLOW_PRE_COMMIT = {
    "pre-commit pre-push stage": [100.0],
    "per-commit OPSEC scan": [5.0],
    "learner-surface internal-ID scan": [5.0],
}
UPDATE = gate.Update("local", "a" * 40, "remote", ZERO_SHA)


def test_slow_pre_commit_no_longer_shortens_the_pytest_allowance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = FakeClock()
    # The pytest stage needs 595 s: more than the 490 s a shared budget leaves, inside its own 600 s.
    _journal_shaped_push(tmp_path, monkeypatch, clock, {**SLOW_PRE_COMMIT, "pytest stage": [20.0, 575.0]})
    event: dict[str, object] = {}
    try:
        gate.validate(UPDATE, tmp_path, "x", "y", event)
    except gate.GateOutcome as error:
        stages = {name: round(stage["elapsed_s"], 1) for name, stage in event.get("stages", {}).items()}
        pytest.fail(f"expired as {error.reason}: {error.detail}; stage elapsed {stages}")

    assert event["outcome"] == "green" and event["admission_wait_s"] == 500.0
    assert (event["run_budget_s"], event["stage_budget_s"]) == (gate.RUN_BUDGET_S, gate.STAGE_BUDGET_S) == (1200, 600)
    stages = event["stages"]
    assert stages["pre_commit"]["elapsed_s"] == pytest.approx(110.0)
    assert stages["pytest"]["elapsed_s"] == pytest.approx(595.0)
    for stage in stages.values():
        assert stage["allowance_s"] == pytest.approx(gate.STAGE_BUDGET_S)
        assert stage["allowance_limited_by"] == "stage_budget"
    assert gate.receipt_is_fresh(tmp_path, _plan(), clock.time())


@pytest.mark.parametrize("stage", ["pre_commit", "pytest"])
def test_each_stage_still_expires_at_its_own_allowance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    clock = FakeClock()
    needs = {"pytest stage": [20.0, 650.0]}
    needs.update(SLOW_PRE_COMMIT if stage == "pytest" else {"pre-commit pre-push stage": [650.0]})
    _journal_shaped_push(tmp_path, monkeypatch, clock, needs)
    event: dict[str, object] = {}
    with pytest.raises(gate.GateOutcome) as raised:
        gate.validate(UPDATE, tmp_path, "x", "y", event)

    assert raised.value.incomplete and raised.value.failing == ()
    assert "exceeded the time budget (timeout)" in raised.value.detail
    assert set(event["stages"]) == ({"pre_commit"} if stage == "pre_commit" else {"pre_commit", "pytest"})
    row = event["stages"][stage]
    assert row["outcome"] == "validation_incomplete" and row["signal"] == signal.SIGKILL
    assert row["elapsed_s"] == pytest.approx(gate.STAGE_BUDGET_S) == row["allowance_s"]
    assert row["allowance_limited_by"] == "stage_budget"
    assert not gate.receipt_is_fresh(tmp_path, _plan(), clock.time())


def test_the_run_budget_caps_the_sum_of_stage_allowances(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = FakeClock()
    _journal_shaped_push(
        tmp_path, monkeypatch, clock, {"pre-commit pre-push stage": [300.0, 300.0], "pytest stage": [20.0, 430.0]}
    )
    budget = gate.Budget(700.0, 600.0)  # a total shorter than two allowances binds the later stage
    event: dict[str, object] = {}
    timed_run = gate.run_bounded

    def instant_scans(command, **kwargs):
        if kwargs["label"] in ("per-commit OPSEC scan", "learner-surface internal-ID scan"):
            return 0, ""
        return timed_run(command, **kwargs)

    monkeypatch.setattr(gate, "run_bounded", instant_scans)
    with pytest.raises(gate.GateOutcome) as raised:
        gate.validate(UPDATE, tmp_path, "x", "y", event, budget)

    assert raised.value.incomplete and raised.value.failing == ()
    stages = event["stages"]
    assert stages["pre_commit"]["allowance_limited_by"] == "stage_budget"
    assert stages["pytest"]["allowance_s"] == pytest.approx(400.0)  # 700 total - 300 spent by pre-commit
    assert stages["pytest"]["allowance_limited_by"] == "run_budget"
    assert stages["pre_commit"]["elapsed_s"] + stages["pytest"]["elapsed_s"] == pytest.approx(700.0)

    # One push shares the total across its ref updates: the second gets only what the first left.
    second: dict[str, object] = {}
    with pytest.raises(gate.GateOutcome):
        gate.validate(UPDATE, tmp_path, "x", "y", second, budget)
    assert second["stages"]["pre_commit"]["allowance_s"] == pytest.approx(0.0)
    assert second["stages"]["pre_commit"]["allowance_limited_by"] == "run_budget"


def test_admission_waits_consume_neither_a_stage_allowance_nor_the_total(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = FakeClock()
    # Both stages use almost all of their own allowance after the 500 s admission wait.
    needs = {
        "pre-commit pre-push stage": [590.0],
        "per-commit OPSEC scan": [4.0],
        "learner-surface internal-ID scan": [4.0],
        "pytest stage": [20.0, 578.0],
    }
    _journal_shaped_push(tmp_path, monkeypatch, clock, needs)
    event: dict[str, object] = {}
    gate.validate(UPDATE, tmp_path, "x", "y", event)

    assert event["outcome"] == "green" and event["admission_wait_s"] == 500.0
    assert clock.now == pytest.approx(500.0 + 598.0 + 598.0)  # 1,196 s of stages after the wait
    assert all(stage["allowance_limited_by"] == "stage_budget" for stage in event["stages"].values())


def _stage_launcher(repo: Path, pre_commit: str, pytest_run: str) -> None:
    """A synthetic launcher whose stage commands run the given shell bodies; scans and shadow are instant."""
    _write(
        repo,
        "scripts/pre_commit/project_python.sh",
        textwrap.dedent(f"""\
        if [ "$1" = scripts/audit/lint_opsec_leaks.py ]; then exit 0; fi
        if [ "$2" = scripts.ci.pre_push_shadow ]; then echo '{{"selected_tests":[]}}'; exit 0; fi
        if [ "$2" = pre_commit ]; then
        {pre_commit}
        exit 0
        fi
        {pytest_run}
        """),
    )
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "synthetic timed stages", "tests/test_new.py", "scripts/pre_commit/project_python.sh")


@pytest.mark.parametrize("ending", ["green", "red"])
def test_actual_stages_each_get_their_own_allowance(repo: Path, ending: str) -> None:
    # pre-commit runs twice (pre-push stage, internal-ID scan) and pytest twice (changed file, invariants):
    # about 3 s per stage, 6 s together, under a 5 s stage budget that a shared budget would exceed.
    # A red run fails in the second (invariant) invocation, so it too has spent both stages' time.
    failure = "FAILED tests/test_invariant.py::test_ok - synthetic"
    verdict = f'case "$*" in *tests/test_invariant.py*) echo "{failure}"; exit 1;; esac' if ending == "red" else ":"
    _stage_launcher(repo, "sleep 1.5", f"sleep 1.5; {verdict}; echo '1 passed in 1.5s'; exit 0")

    result = _run_gate(repo, extra_env={gate.MAX_CONCURRENT_RUNS_ENV: "1", "LU_PRE_PUSH_GATE_STAGE_BUDGET_S": "5"})

    assert result.returncode == (0 if ending == "green" else gate.EXIT_REFUSED), result.stderr
    row = _measurements(repo)[-1]
    stages = row["stages"]
    assert row["stage_budget_s"] == 5.0 and row["run_budget_s"] == gate.RUN_BUDGET_S
    assert stages["pre_commit"]["elapsed_s"] + stages["pytest"]["elapsed_s"] > 5.0
    for stage in stages.values():
        assert stage["allowance_s"] == pytest.approx(5.0) and stage["allowance_limited_by"] == "stage_budget"
        assert stage["elapsed_s"] < stage["allowance_s"]
    if ending == "green":
        assert row["outcome"] == "green" and len(_receipts(repo)) == 1
    else:
        assert _verdict(result) == {
            "outcome": "refused",
            "reason": "tests_failed",
            "failing": ["tests/test_invariant.py::test_ok"],
        }
        assert _receipts(repo) == []


@pytest.mark.parametrize("bound", ["pre_commit", "pytest", "total"])
def test_an_actual_overrun_is_killed_at_its_bound_with_descendants(repo: Path, tmp_path: Path, bound: str) -> None:
    pid_file = tmp_path / "child.pid"
    (tmp_path / "detach.py").write_text(_DETACHED_CHILD, encoding="utf-8")
    overrun = f'"{sys.executable}" "{tmp_path / "detach.py"}" "{pid_file}"; sleep 60'
    pre_commit = overrun if bound == "pre_commit" else "sleep 1.2" if bound == "total" else ":"
    _stage_launcher(repo, pre_commit, overrun if bound != "pre_commit" else "echo '1 passed in 0.1s'")
    budgets = {"LU_PRE_PUSH_GATE_STAGE_BUDGET_S": "3"}
    if bound == "total":  # pre-commit spends about 2.4 s of a 5 s total, leaving pytest less than its 4 s
        budgets = {"LU_PRE_PUSH_GATE_STAGE_BUDGET_S": "4", "LU_PRE_PUSH_GATE_RUN_BUDGET_S": "5"}

    result = _run_gate(repo, extra_env={gate.MAX_CONCURRENT_RUNS_ENV: "1", **budgets})

    assert result.returncode == gate.EXIT_INCOMPLETE, result.stderr
    assert _verdict(result) == {"outcome": "validation_incomplete", "reason": "validation_incomplete", "failing": []}
    assert "NOT green" in result.stderr and _receipts(repo) == []
    assert _gone(int(pid_file.read_text(encoding="utf-8")))
    row = _measurements(repo)[-1]
    assert row["outcome"] == "validation_incomplete" and row["failing"] == []
    killed = row["stages"]["pre_commit" if bound == "pre_commit" else "pytest"]
    assert set(row["stages"]) == ({"pre_commit"} if bound == "pre_commit" else {"pre_commit", "pytest"})
    assert killed["outcome"] == "validation_incomplete" and killed["signal"] == signal.SIGKILL
    assert killed["allowance_s"] <= killed["elapsed_s"] < killed["allowance_s"] + 2 * gate.CLEANUP_BUDGET_S
    if bound == "total":
        assert killed["allowance_limited_by"] == "run_budget" and killed["allowance_s"] < 4.0
        assert row["stages"]["pre_commit"]["allowance_limited_by"] == "stage_budget"
    else:
        assert killed["allowance_limited_by"] == "stage_budget"
        assert killed["allowance_s"] == pytest.approx(3.0)


def test_the_run_budget_is_the_sum_of_the_two_stage_allowances() -> None:
    assert gate.RUN_BUDGET_S == 2 * gate.STAGE_BUDGET_S == 1200
