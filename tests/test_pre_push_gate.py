"""Behavior tests for the pre-push gate (#10033): refuse findings, run no tests (#11276), bounded, no stale receipts."""

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
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest
import yaml

from tests.helpers.python import project_python
from tests.wait_helpers import wait_for_line, wait_until

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_DIR = REPO_ROOT / ".githooks"
GATE_PATH = HOOK_DIR / "pre_push_gate.py"
PYTHON = project_python()
ZERO_SHA = "0" * 40
# Agent sessions shim ``git`` and refuse the fixture's pushes to a disposable remote; use the real binary there.
GIT = os.environ.get("AGENT_REAL_GIT") or "git"

# The repository-wide invariant registry the gate's test stage read before #11276: present, and ignored.
REGISTRY = 'KNOWN_REPO_WIDE_MODULES = frozenset({"tests/test_invariant.py"})\nKNOWN_REPO_WIDE_FUNCTIONS = ()\n'
PRE_COMMIT = textwrap.dedent(
    """\
    repos:
      - repo: local
        hooks:
          - id: fixture-pre-push
            name: fixture pre-push
            entry: >-
              bash -c 'test ! -e BLOCK_PRE_PUSH && if test -e SLOW_PRE_PUSH; then sleep 30; fi
              && if test -e control_stage.py; then bash scripts/pre_commit/project_python.sh control_stage.py; fi'
            language: system
            always_run: true
            pass_filenames: false
            stages: [pre-push]
    """
)
GREEN_TEST = "def test_ok():\n    assert True\n"
RED_TEST = "def test_broken():\n    assert False\n"


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


@pytest.fixture(autouse=True)
def _no_inherited_gate_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    """An in-process gate under test never takes the invoking push's opt-in concurrency (#11207).

    With two runs allowed, a qualified host and a reachable user bus, ``validate`` runs its stages in a
    ``systemd-run`` scope child: a fresh process that the test's monkeypatches never reach. A test that
    needs two runs sets the value itself, after this fixture.
    """
    monkeypatch.delenv(gate.MAX_CONCURRENT_RUNS_ENV, raising=False)


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.pop("AGENT_NO_MERGE", None)
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("LU_TEST_SLOTS_HOLDER", None)  # a gate under test is never nested in this run's test slots
    # Nor does it inherit the invoking push's opt-in concurrency: under two slots a qualified host lets a
    # second gate share, which breaks serial FIFO assertions (#10820). Tests opt in through ``extra``.
    env.pop("LU_PRE_PUSH_GATE_MAX_CONCURRENT_RUNS", None)
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
    _git(repo, "commit", "--no-verify", "-m", message)  # fixtures commit what the push gate must refuse
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


def _hook_inputs(repo: Path) -> tuple[str, str]:
    """The launcher and pre-commit configuration the tracked hook passes for ``repo``."""
    return str(repo / "scripts/pre_commit/project_python.sh"), str(repo / ".pre-commit-config.yaml")


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


def _measurements_in_start_order(repo: Path) -> list[dict]:
    """Terminal rows ordered by their BEGIN rows (#11207).

    A gate appends its terminal row only after ``validate`` returns, which is after it released its
    head admission. A follower that reuses the leader's receipt can therefore append first; the BEGIN
    rows follow the order in which the test started the gates.
    """
    path = repo / ".git/lu-pre-push-gate/measurements.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    started = [row["attempt_id"] for row in rows if row.get("phase") == "BEGIN"]
    terminal = {row["attempt_id"]: row for row in rows if row.get("phase") != "BEGIN"}
    assert len(terminal) == len(started) == len(set(started)) and set(terminal) == set(started)
    return [terminal[attempt] for attempt in started]


def _receipts(repo: Path) -> list[Path]:
    return sorted((repo / ".git/lu-pre-push-gate/receipts").glob("*.json"))


# ---- both push paths run no tests; the kept stages still block (#11276) ----------------------------------

# Committed tripwires: each logs when a push loads it. pytest loads ``tests/conftest.py``; the gate's test
# stage loaded the host test-slot governor and ran the affected-test selector, both from its own checkout.
TRIPWIRES = {
    "tests/conftest.py": "pytest",
    "scripts/common/test_slots.py": "test_slots",
    "scripts/ci/pre_push_shadow.py": "selector",
}
PUSH_PATHS = ("git-push", "auto-finalize")


def _tripwire(name: str, log: Path) -> str:
    def record(tag: str) -> str:
        return f"open({str(log)!r}, 'a', encoding='utf-8').write({tag!r} + '\\n')\n"

    if name != "test_slots":
        return record(name)
    # Answers "disabled" so a gate that asks for slots goes on to run pytest, where the conftest logs too.
    return (
        record(name)
        + "class SlotError(Exception):\n    pass\n\n\ndef enabled():\n    "
        + record("test_slots.enabled")
        + "    return False\n"
    )


@pytest.fixture
def push_repo(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """``repo`` with the test-stage tripwires and the real OPSEC scanner hook at the ``pre-push`` stage."""
    log = tmp_path / "tripwire.log"
    for relative, name in TRIPWIRES.items():
        _write(repo, relative, _tripwire(name, log))
    config = yaml.safe_load((repo / ".pre-commit-config.yaml").read_text())
    actual = yaml.safe_load((REPO_ROOT / ".pre-commit-config.yaml").read_text())
    opsec = next(hook for item in actual["repos"] for hook in item.get("hooks", []) if hook["id"] == "lint-opsec-leaks")
    config["repos"][0]["hooks"].append(opsec)
    _write(repo, ".pre-commit-config.yaml", yaml.safe_dump(config))
    _git(repo, "checkout", "-q", "main")
    _commit(repo, "tripwires", ".")
    _git(repo, "push", "--no-verify", "origin", "main")
    _git(repo, "checkout", "-q", "-B", "feature")
    _git(repo, "config", "core.hooksPath", str(repo / ".githooks"))
    tools = tmp_path / "push-bin"
    tools.mkdir()
    (tools / "git-lfs").write_text("#!/usr/bin/env bash\ncat >/dev/null\nexit 0\n", encoding="utf-8")
    (tools / "git-lfs").chmod(0o755)
    real_git = shutil.which(GIT)
    assert real_git is not None
    (tools / "git").symlink_to(real_git)  # the auto-finalize path resolves ``git`` on PATH
    monkeypatch.setenv("PATH", f"{tools}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))  # the auto-finalize env drops PRE_COMMIT_*
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "LU_TEST_SLOTS_HOLDER", "AGENT_NO_MERGE"):
        monkeypatch.delenv(name, raising=False)
    return repo


def _tripwire_log(repo: Path) -> list[str]:
    log = repo.parent / "tripwire.log"
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def _push(repo: Path, path: str) -> tuple[bool, str]:
    """Push ``feature`` through the tracked hook by ``path``; ``(accepted, diagnostics)``."""
    if path == "git-push":
        result = subprocess.run(
            [GIT, "push", "-u", "origin", "feature"],
            capture_output=True,
            check=False,
            cwd=repo,
            env=_env({"PATH": os.environ["PATH"], "PRE_COMMIT_HOME": str(repo.parent / "pc")}),
            text=True,
            timeout=180,
        )
        return result.returncode == 0, result.stderr
    from scripts import delegate

    try:
        delegate._push_auto_finalize_branch(repo, "feature")
    except RuntimeError as error:
        return False, str(error)
    return True, ""


def _remote_feature(repo: Path) -> str:
    return _git(repo, "ls-remote", "origin", "refs/heads/feature").stdout.strip()


@pytest.mark.parametrize("path", PUSH_PATHS)
def test_a_push_runs_no_tests_takes_no_slot_and_calls_no_selector(push_repo: Path, path: str) -> None:
    """A range with a red test and a Python change reaches the remote: CI Gate is the test evidence."""
    _write(push_repo, "tests/test_new.py", RED_TEST)
    _write(push_repo, "scripts/changed.py", "VALUE = 1\n")
    head = _commit(push_repo, "red test and a python change", "tests/test_new.py", "scripts/changed.py")

    accepted, detail = _push(push_repo, path)

    assert accepted, detail
    assert _remote_feature(push_repo).startswith(head)
    assert _tripwire_log(push_repo) == []
    row = _measurements(push_repo)[-1]
    assert row["outcome"] == "green"
    assert set(row["stages"]) == {"pre_commit"}
    assert not {"pytest", "selection", "test_slots", "slot_wait_s", "nodes"} & set(row)


def _intermediate_private_key(repo: Path) -> None:
    """An OPSEC finding only in an intermediate commit: the net diff of the range is empty."""
    _write(repo, "docs/push-scan.md", "-----BEGIN " + "PRIVATE KEY-----\n")
    _commit(repo, "leak", "docs/push-scan.md")
    _git(repo, "rm", "-q", "docs/push-scan.md")
    _git(repo, "commit", "-q", "--no-verify", "-m", "revert the leak")


def _net_private_key(repo: Path) -> None:
    _write(repo, "docs/key.md", "-----BEGIN " + "PRIVATE KEY-----\n")
    _commit(repo, "secret", "docs/key.md")


def _internal_id(repo: Path) -> None:
    _write(repo, "site/src/content/docs/a1/topic.mdx", "Source section S4433 leaked.\n")
    _commit(repo, "learner surface", "site/src/content/docs/a1/topic.mdx")


def _stray_file(repo: Path) -> None:
    _write(repo, "docs/ok.md", "fine\n")
    _commit(repo, "docs", "docs/ok.md")
    _write(repo, "scripts/stray.py", "print('not committed')\n")  # untracked, so outside the validated commit


# kept stage -> (how the range trips it, the typed reason, the failing hooks it names)
KEPT_STAGES = {
    "per-commit-opsec": (_intermediate_private_key, "pre_commit_failed", ["lint-opsec-leaks"]),
    "secret-scan": (_net_private_key, "pre_commit_failed", ["check staged and committed files for OPSEC leaks"]),
    "internal-id": (_internal_id, "pre_commit_failed", ["check-no-internal-ids"]),
    "stray-file": (_stray_file, "untracked_inputs", []),
}


@pytest.mark.parametrize("path", PUSH_PATHS)
@pytest.mark.parametrize("stage", list(KEPT_STAGES))
def test_each_kept_stage_still_blocks_both_push_paths(push_repo: Path, path: str, stage: str) -> None:
    trip, reason, failing = KEPT_STAGES[stage]
    trip(push_repo)

    accepted, detail = _push(push_repo, path)

    assert not accepted, detail
    assert _remote_feature(push_repo) == ""
    row = _measurements(push_repo)[-1]
    assert (row["outcome"], row["reason"], row["failing"]) == ("refused", reason, failing)
    assert _tripwire_log(push_repo) == []


@pytest.mark.parametrize("path", PUSH_PATHS)
def test_a_kept_stage_timeout_is_validation_incomplete_on_both_push_paths(
    push_repo: Path, path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LU_PRE_PUSH_GATE_STAGE_BUDGET_S", "3")
    _write(push_repo, "SLOW_PRE_PUSH", "stall the fixture hook\n")  # the fixture hook sleeps past the budget
    _commit(push_repo, "slow", "SLOW_PRE_PUSH")

    accepted, detail = _push(push_repo, path)

    assert not accepted, detail
    assert _remote_feature(push_repo) == ""
    row = _measurements(push_repo)[-1]
    assert row["outcome"] == "validation_incomplete"
    assert row["reason"] in ("timeout", "timeout_under_load")
    assert row["stages"]["pre_commit"]["outcome"] == "validation_incomplete"
    if path == "git-push":
        assert '"outcome": "validation_incomplete"' in detail
    assert _tripwire_log(push_repo) == []


# ---- the gate refuses findings and accepts a clean range ------------------------------------------------


def test_a_clean_range_is_accepted_and_leaves_a_receipt(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "1")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "gate-test")
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")

    result = _run_gate(repo)

    assert result.returncode == 0, result.stderr
    assert len(_receipts(repo)) == 1
    begin, terminal = _raw_measurements(repo)
    assert terminal["outcome"] == "green" and terminal["stages"]["pre_commit"]["outcome"] == "green"
    assert set(terminal["stages"]) == {"pre_commit"}
    assert terminal["measurement_schema"] == begin["measurement_schema"] == "pre-push-measurement.v3"


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


def test_nothing_outgoing_is_accepted_without_running_a_stage(repo: Path) -> None:
    result = _run_gate(repo, remote_sha=_git(repo, "rev-parse", "HEAD").stdout.strip())

    assert result.returncode == 0
    assert _measurements(repo)[-1]["detail"] == "no outgoing commits"
    assert "stages" not in _measurements(repo)[-1]


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

    _write(repo, "BLOCK_PRE_PUSH", "x\n")
    _commit(repo, "trip the hook", "BLOCK_PRE_PUSH")
    refused = subprocess.run(
        [GIT, *push_args], capture_output=True, check=False, cwd=repo, env=env, text=True, timeout=120
    )
    assert refused.returncode != 0
    assert "(reason: pre_commit_failed)" in refused.stderr
    assert _git(repo, "ls-remote", "origin", "refs/heads/feature").stdout == ""

    _git(repo, "rm", "-q", "BLOCK_PRE_PUSH")
    _write(repo, "tests/test_new.py", RED_TEST)  # a red test reaches the remote: CI Gate runs it (#11276)
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
    _write(repo, "BLOCK_PRE_PUSH", "x\n")
    _git(repo, "add", "BLOCK_PRE_PUSH")
    _git(repo, "commit", "--no-verify", "--amend", "--no-edit")

    result = _run_gate(repo)

    assert result.returncode == gate.EXIT_REFUSED
    assert _verdict(result)["reason"] == "pre_commit_failed"


def _plan(**overrides):
    values = {"head": "a" * 40, "tree": "b" * 40, "base": "c" * 40, "tools": {"python": "3.x"}}
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
        ("base_fallback", "merge_base_ambiguous"),
        ("tools", {"python": "3.y"}),
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


def _version_11_receipt(plan, at: float) -> dict:
    """A sealed green receipt as gate version 11 wrote it: its key also bound the test selection that ran."""
    key = {
        **gate.receipt_key(plan),
        "gate_version": 11,
        "registry_version": "v11-0123456789abcdef",
        "deferred_to_ci": [],
        "node_ids": ["tests/test_invariant.py"],
        "changed_paths": ["tests/test_new.py"],
        "deleted_paths": [],
        "selection": {"status": "fallback", "reason": "selector_failed", "digest": None, "tests": []},
        "blocking_node_ids": ["tests/test_invariant.py", "tests/test_new.py"],
    }
    body = {"key": key, "outcome": "green", "at": at}
    return {**body, "seal": gate.receipt_seal(body)}


@pytest.mark.parametrize("version", [11, gate.GATE_VERSION])
def test_a_receipt_of_the_gate_that_ran_tests_is_never_reused(tmp_path: Path, version: int) -> None:
    """Old proof of a removed stage stands for nothing; only the gate-version field differs it from new (#11276)."""
    plan = _plan()
    receipt = _version_11_receipt(plan, 1000.0)
    if version == gate.GATE_VERSION:  # the same receipt with only the test fields removed would be current
        receipt["key"] = gate.receipt_key(plan)
        body = {name: receipt[name] for name in ("key", "outcome", "at")}
        receipt["seal"] = gate.receipt_seal(body)
    path = gate.receipt_path(tmp_path, plan)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(receipt), encoding="utf-8")

    assert gate.receipt_is_fresh(tmp_path, plan, 1001.0) is (version == gate.GATE_VERSION)


def test_an_old_receipt_neither_passes_nor_breaks_a_new_push(repo: Path) -> None:
    _write(repo, "BLOCK_PRE_PUSH", "x\n")
    _commit(repo, "trip the hook", "BLOCK_PRE_PUSH")
    launcher, config = _hook_inputs(repo)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    plan = gate.build_plan(
        gate.Update("refs/heads/feature", head, "refs/heads/feature", ZERO_SHA), repo, launcher, config
    )
    path = gate.receipt_path(repo / ".git/lu-pre-push-gate", plan)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(_version_11_receipt(plan, time.time())), encoding="utf-8")

    refused = _run_gate(repo)  # the stage runs and still blocks: the old green receipt proves nothing
    assert refused.returncode == gate.EXIT_REFUSED and _verdict(refused)["reason"] == "pre_commit_failed"

    _git(repo, "rm", "-q", "BLOCK_PRE_PUSH")
    _git(repo, "commit", "-q", "--no-verify", "-m", "untrip")
    assert _run_gate(repo).returncode == 0
    written = [json.loads(receipt.read_text(encoding="utf-8")) for receipt in _receipts(repo)]
    assert sorted(receipt["key"]["gate_version"] for receipt in written) == [11, gate.GATE_VERSION]


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

    def pre_commit(_plan, _root, _launcher, _config, deadline, **_kwargs):
        deadlines.append(deadline)
        clock.now += 2.0

    monkeypatch.setattr(gate, "Admission", WaitedAdmission)
    monkeypatch.setattr(gate, "run_pre_commit_stage", pre_commit)
    return deadlines


def test_the_run_budget_starts_after_admission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = FakeClock()
    deadlines = _fake_validation(tmp_path, monkeypatch, clock)
    budget = gate.Budget(10.0)
    event = {}
    gate.validate(gate.Update("local", "a" * 40, "remote", ZERO_SHA), tmp_path, "x", "y", event, budget)

    assert deadlines == [510.0]
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

    assert deadlines == []  # the stage did not start
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

    assert len(deadlines) == 1 and event["outcome"] == "green"
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
        plan = gate.Plan(number * 40, 'a' * 40, 'b' * 40)
        gate.git_ok = lambda *args, **kwargs: str(root)
        gate.build_plan = lambda *args: plan
        gate.state_dir = lambda *args: root / 'state'
        def pre_commit(plan, root, launcher, config, deadline, **kwargs):
            if deadline - time.monotonic() < 2.5:
                raise gate.GateOutcome('validation_incomplete', 'waiting consumed budget', incomplete=True)
            time.sleep(2.0)
            if time.monotonic() >= deadline:
                raise gate.GateOutcome('validation_incomplete', 'the stage ran out of budget', incomplete=True)
            (root / ('pre-' + number)).write_text('ran')
        gate.run_pre_commit_stage = pre_commit
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
    assert len(list(tmp_path.glob("pre-*"))) == 4
    assert len(list((state / "receipts").glob("*.json"))) == 4
    assert list((state / "queue").glob("*.ticket")) == []


# ---- bounded resources: validation_incomplete, never green ------------------------------------------------


def test_time_budget_exhaustion_is_validation_incomplete_and_leaves_no_receipt(repo: Path) -> None:
    _write(repo, "SLOW_PRE_PUSH", "the fixture hook sleeps past the budget\n")
    head = _commit(repo, "slow", "SLOW_PRE_PUSH")
    base = _git(repo, "merge-base", "origin/main", "HEAD").stdout.strip()

    result = _run_gate(repo, extra_env={"LU_PRE_PUSH_GATE_RUN_BUDGET_S": "4"})

    assert result.returncode == gate.EXIT_INCOMPLETE
    verdict = _verdict(result)
    assert verdict["outcome"] == "validation_incomplete"
    assert "NOT green" in result.stderr
    assert _receipts(repo) == []
    row = _measurements(repo)[-1]
    assert row["outcome"] == "validation_incomplete"
    # The timeout names the range it scanned (#10820).
    assert "(timeout)" in row["detail"]
    scanned = f"range: {base}..{head}"
    assert row["detail"].endswith(scanned) and result.stderr.rstrip("\n").endswith(scanned)
    assert row["base"] == base and row["stages"]["pre_commit"]["outcome"] == "validation_incomplete"


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


# ---- registry ---------------------------------------------------------------------------------------------


def test_invalid_ref_update_lines_are_a_typed_failure() -> None:
    with pytest.raises(gate.GateOutcome) as caught:
        gate.parse_updates("only three fields\n")
    assert caught.value.reason == "invalid_ref_updates"


# ---- admission and push timeouts ----------------------------------------------------------------------------


# A stub's hang blocks until it is killed. A ``time.sleep`` hang can end while the gate is still busy
# on a loaded host, and the gate then rightly reads its empty answer as unparseable, not as a timeout.
_BLOCK_UNTIL_KILLED = "import threading\nthreading.Event().wait()\n"


def test_admission_wait_covers_one_full_gate_run_of_this_or_the_test_running_version() -> None:
    """A predecessor may still run gate version 11, which also waited for test slots and its selector (#11276)."""
    assert gate.ADMISSION_WAIT_S >= gate.RUN_BUDGET_S + 2 * gate.CLEANUP_BUDGET_S
    assert gate.ADMISSION_WAIT_S == 1940.0  # version 11: run budget, slot wait, selector, two cleanups


def test_auto_finalize_push_timeout_covers_the_queue_ceiling() -> None:
    from scripts import delegate

    gate_worst_case = gate.ADMISSION_MAX_WAIT_S + gate.ADMISSION_WAIT_S
    assert gate_worst_case + delegate.DEFAULT_NETWORK_GIT_TIMEOUT_S <= delegate.AUTO_FINALIZE_PUSH_TIMEOUT_S


def test_worker_closeout_text_carries_the_gate_and_merge_main_rules() -> None:
    from scripts import delegate

    source = Path(delegate.__file__).read_text(encoding="utf-8")
    assert "validation_incomplete" in source and "git merge-tree" in source
    # Workers are told what the gate runs: no tests since #11276, so a refusal names hooks, not node ids.
    assert "it runs no tests, CI runs the full suite" in source
    assert "tests they affect" not in source and "failing node ids" not in source


# ---- public material ------------------------------------------------------------------------------------


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
    _write(repo, "docs/leak.md", "-----BEGIN " + "PRIVATE KEY-----\n")
    first = _commit(repo, "leak", "docs/leak.md")
    _write(repo, "docs/leak.md", "clean\n")
    head = _commit(repo, "clean the leak", "docs/leak.md")
    # The first update's range holds only the clean commit; the second's also holds the leak.
    updates = (
        f"refs/heads/feature {head} refs/heads/narrow {first}\nrefs/heads/feature {head} refs/heads/wide {ZERO_SHA}\n"
    )

    result = _run_gate_with(repo, updates)

    assert result.returncode == gate.EXIT_REFUSED, result.stderr
    assert _verdict(result)["failing"] == ["lint-opsec-leaks"]
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


@pytest.mark.parametrize("ignored", [False, True], ids=["untracked", "ignored"])
@pytest.mark.parametrize("directory", ["node_modules", "site/node_modules", "site/vendor/node_modules"])
@pytest.mark.parametrize("filename", ["x.py", "x.pth", "pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml"])
def test_node_modules_overlays_do_not_block_the_scan(
    repo: Path, ignored: bool, directory: str, filename: str
) -> None:
    lock = f"{Path(directory).parent}/package-lock.json"
    _write(repo, lock, "{}\n")
    _commit(repo, "dependency lock", lock)
    relative = f"{directory}/katex/src/fonts/{filename}"
    if ignored:
        _write(repo, ".gitignore", f"/{relative}\n")
        _commit(repo, "ignore dependency overlay", ".gitignore")
    _write(repo, relative, "# dependency file\n")

    assert gate.reject_untracked_inputs(repo) is None


@pytest.mark.parametrize("lock_state", ["missing", "untracked", "ignored", "symlink"])
@pytest.mark.parametrize("filename", ["x.py", "x.pth", "pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml"])
def test_unproven_node_modules_overlays_are_refused(repo: Path, lock_state: str, filename: str) -> None:
    lock = "site/package-lock.json"
    if lock_state == "symlink":
        _write(repo, "lock-target.json", "{}\n")
        (repo / "site").mkdir()
        (repo / lock).symlink_to("../lock-target.json")
        _commit(repo, "symlink lock", lock)
    elif lock_state != "missing":
        _write(repo, lock, "{}\n")
        if lock_state == "ignored":
            _write(repo, ".gitignore", f"/{lock}\n")
            _commit(repo, "ignore lock", ".gitignore")
    relative = f"site/node_modules/katex/src/fonts/{filename}"
    _write(repo, relative, "# overlay\n")

    with pytest.raises(gate.GateOutcome) as raised:
        gate.reject_untracked_inputs(repo)

    assert raised.value.reason == "untracked_inputs"
    assert relative in raised.value.detail


@pytest.mark.parametrize(
    ("relative", "state", "expected"),
    [
        (f"{directory}/katex/src/fonts/{name}", state, state == "tracked_lock")
        for directory in ("node_modules", "site/node_modules", "site/vendor/node_modules")
        for name in ("x.py", "x.pth", "pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml")
        for state in ("tracked_lock", "missing_lock", "untracked_lock", "ignored_lock")
    ] + [
        ("site/node_modules/katex/src/fonts/x.py", state, False)
        for state in (
            "tracked_input", "symlink_lock", "directory_lock", "missing_tracked_lock",
            "symlink_dependency", "symlink_ancestor", "symlink_component",
        )
    ] + [
        (name, "tracked_lock", False)
        for name in (
            "site/node_modules_extra/x.py", "not_node_modules/x.py",
            "site/.venv/node_modules/x.py", "site/node_modules/.venv/x.py",
            "conftest.py", "sitecustomize.py", "tests/conftest.py", "tests/sitecustomize.py",
        )
    ],
)
def test_dependency_input_predicate_matches_reaper(
    repo: Path, monkeypatch: pytest.MonkeyPatch, relative: str, state: str, expected: bool
) -> None:
    from scripts.fleet.regenerable_output import is_regenerable_ignored_path

    parts = Path(relative).parts
    parent = Path(*parts[:parts.index("node_modules")]) if "node_modules" in parts else Path("site")
    lock = (parent / "package-lock.json").as_posix()
    _write(repo, relative, "# overlay\n")
    if state != "missing_lock":
        _write(repo, lock, "{}\n")
        if state == "ignored_lock":
            _write(repo, ".gitignore", f"/{lock}\n")
            _commit(repo, "ignore lock", ".gitignore")
        elif state != "untracked_lock":
            _commit(repo, "tracked lock", lock)
    if state == "tracked_input":
        _commit(repo, "tracked dependency input", relative)
    elif state in {"symlink_lock", "directory_lock", "missing_tracked_lock"}:
        (repo / lock).unlink()
        if state == "symlink_lock":
            _write(repo, "outside-lock.json", "{}\n")
            (repo / lock).symlink_to(repo / "outside-lock.json")
        elif state == "directory_lock":
            (repo / lock).mkdir()
    elif state.startswith("symlink_"):
        link = repo / {"symlink_dependency": "site/node_modules", "symlink_ancestor": "site",
                       "symlink_component": "site/vendor"}[state]
        if state == "symlink_component":
            relative = "site/vendor/node_modules/x.py"
            _write(repo, relative, "# overlay\n")
            _write(repo, "site/vendor/package-lock.json", "{}\n")
            _commit(repo, "nested lock", "site/vendor/package-lock.json")
        target = repo.parent / "link-target"
        link.rename(target)
        link.symlink_to(target, target_is_directory=True)
    tracked = set(_git(repo, "ls-files", "-z", "--cached").stdout.split("\0"))

    assert is_regenerable_ignored_path(relative, worktree=repo, tracked=tracked) is expected
    assert gate.is_regenerable_dependency_input(relative, root=repo, tracked=tracked) is expected
    # Git does not descend directory symlinks. Supply that enumerated path to
    # also prove the scan applies its predicate if such an input is returned.
    if state.startswith("symlink_") and state != "symlink_lock":
        original_git_ok = gate.git_ok

        def listing(*args: str, cwd: Path) -> str | None:
            if "--others" in args:
                return relative + "\0"
            return original_git_ok(*args, cwd=cwd)

        monkeypatch.setattr(gate, "git_ok", listing)
    if expected or state == "tracked_input":
        assert gate.reject_untracked_inputs(repo) is None
    else:
        with pytest.raises(gate.GateOutcome) as raised:
            gate.reject_untracked_inputs(repo)
        assert raised.value.reason == "untracked_inputs"
        assert relative in raised.value.detail


def test_dependency_input_scan_fails_closed_when_tracked_listing_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gate, "git_ok", lambda *args, **kwargs: "site/node_modules/x.py\0" if "--others" in args else None)
    with pytest.raises(gate.GateOutcome) as raised:
        gate.reject_untracked_inputs(tmp_path)
    assert raised.value.reason == "state_unavailable"
    assert raised.value.incomplete


@pytest.mark.parametrize("ignored", [False, True], ids=["untracked", "ignored"])
@pytest.mark.parametrize(
    "relative",
    [
        "site/katex/src/fonts/x.py",
        "site/katex/src/fonts/x.pth",
        "conftest.py",
        "sitecustomize.py",
        "tests/conftest.py",
        "tests/sitecustomize.py",
        "not_node_modules/x.py",
        "site/node_modules_extra/katex/src/fonts/x.py",
        "site/node_modules_extra/katex/src/fonts/x.pth",
        "site/not_node_modules/katex/src/fonts/x.py",
        "site/not_node_modules/katex/src/fonts/x.pth",
        "site/prefix_node_modules_suffix/katex/src/fonts/x.py",
        "site/prefix_node_modules_suffix/katex/src/fonts/x.pth",
    ],
)
def test_overlays_outside_exact_node_modules_directories_remain_refused(
    repo: Path, ignored: bool, relative: str
) -> None:
    if ignored:
        _write(repo, ".gitignore", f"/{relative}\n")
        _commit(repo, "ignore validation overlay", ".gitignore")
    _write(repo, relative, "# validation overlay\n")

    with pytest.raises(gate.GateOutcome) as raised:
        gate.reject_untracked_inputs(repo)

    assert raised.value.reason == "untracked_inputs"
    assert relative in raised.value.detail


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


def _wait_once_child_hangs(monkeypatch: pytest.MonkeyPatch, hung: Path) -> None:
    """Hold each wait on a child until the child creates ``hung`` (or exits), then let the wait's budget run.

    A short ``run_bounded`` budget then always kills a child that has reached its hang, after the output it
    wrote first, however slowly a loaded host started it.
    """

    class HangAwarePopen(subprocess.Popen):
        def wait(self, timeout: float | None = None) -> int:
            wait_until(lambda: hung.exists() or self.poll() is not None, timeout=60.0, message=f"{hung.name}")
            return super().wait(timeout)

    monkeypatch.setattr(gate.subprocess, "Popen", HangAwarePopen)


_DETACHED_CHILD = (
    "import os, subprocess, sys, time\n"
    "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)'], start_new_session=True)\n"
    "open(sys.argv[1], 'w').write(str(child.pid))\n"
)


@pytest.mark.parametrize("hang", [False, True], ids=["command-exits", "command-times-out"])
def test_a_detached_descendant_holding_the_output_cannot_stall_or_survive_the_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hang: bool
) -> None:
    pid_file = tmp_path / "child.pid"
    hung = tmp_path / "hung"
    script = _DETACHED_CHILD + (f"open({str(hung)!r}, 'w').close()\n{_BLOCK_UNTIL_KILLED}" if hang else "")
    started = time.monotonic()

    if hang:
        _wait_once_child_hangs(monkeypatch, hung)  # the kill finds the descendant already spawned
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
def test_failed_command_measurement_keeps_output_and_observed_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ending: str
) -> None:
    hung = tmp_path / "hung"
    script = (
        "import os, signal, threading; print('synthetic output', flush=True); "
        + {
            "nonzero": "raise SystemExit(3)",
            "signal": "os.kill(os.getpid(), signal.SIGTERM)",
            "timeout": f"open({str(hung)!r}, 'w').close(); threading.Event().wait()",
            "spawn-error": "raise SystemExit(0)",
            "no-budget": "raise SystemExit(0)",
        }[ending]
    )
    command = [sys.executable, "-c", script] if ending != "spawn-error" else [str(tmp_path / "absent")]
    allowance = 0.0 if ending == "no-budget" else 1.0 if ending == "timeout" else 30.0
    if ending == "timeout":
        _wait_once_child_hangs(monkeypatch, hung)  # the kill comes after the output, never before it
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
        with gate.stage_measurement(event, "synthetic") as diagnostics:
            gate.run_bounded(
                ["synthetic"], cwd=tmp_path, deadline=time.monotonic() + 1.0, label="synthetic", diagnostics=diagnostics
            )
    row = event["stages"]["synthetic"]
    assert row["returncode"] is None and row["signal"] is None
    assert row["child_unavailable_reason"] == "exit_unobserved"
    assert row["output_tail"] == "synthetic unreaped output"
    assert row["outcome"] == "validation_incomplete"


def test_command_diagnostics_bound_long_lines_and_line_count(tmp_path: Path) -> None:
    event = {}
    with gate.stage_measurement(event, "synthetic") as diagnostics:
        code, output = gate.run_bounded(
            [sys.executable, "-c", "print('x' * 20000); print('line\\n' * 100, end='')"],
            cwd=tmp_path,
            deadline=time.monotonic() + 30.0,
            label="synthetic",
            diagnostics=diagnostics,
        )
    assert code == 0 and len(output) > gate.OUTPUT_TAIL_BYTES
    assert event["stages"]["synthetic"]["output_tail"] == "\n".join(["line"] * 40)
    event = {}
    with gate.stage_measurement(event, "synthetic") as diagnostics:
        gate.run_bounded(
            [sys.executable, "-c", "print('x' * 20000, end='')"],
            cwd=tmp_path,
            deadline=time.monotonic() + 30.0,
            label="synthetic",
            diagnostics=diagnostics,
        )
    assert event["stages"]["synthetic"]["output_tail"] == "x" * gate.OUTPUT_TAIL_BYTES


@pytest.mark.parametrize("pre_commit_code", [0, 1])
def test_exact_head_row_attributes_only_entered_stages(repo: Path, pre_commit_code: int) -> None:
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
        echo "unexpected launch: $*" >> launched-otherwise
        exit 2
        """),
    )
    head = _commit(repo, "synthetic stages", "tests/test_new.py", "scripts/pre_commit/project_python.sh")
    result = _run_gate(repo)
    row = _measurements(repo)[-1]
    assert row["head"] == head
    stages = row["stages"]
    assert set(stages) == {"pre_commit"}  # no test stage follows a green pre-commit stage (#11276)
    assert stages["pre_commit"]["returncode"] == pre_commit_code
    assert stages["pre_commit"]["output_tail"] == "synthetic hook"
    assert stages["pre_commit"]["outcome"] == ("refused" if pre_commit_code else "green")
    assert stages["pre_commit"]["elapsed_s"] >= 0.0
    assert stages["pre_commit"]["elapsed_s"] <= row["duration_s"] + 0.01
    assert row["admission_wait_s"] >= 0.0
    assert result.returncode == pre_commit_code
    assert bool(_receipts(repo)) == (pre_commit_code == 0)
    assert not (repo / "launched-otherwise").exists()


def test_stage_timings_are_monotonic_and_separate_from_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = FakeClock()
    _fake_validation(tmp_path, monkeypatch, clock)
    event = {}
    gate.validate(gate.Update("local", "a" * 40, "remote", ZERO_SHA), tmp_path, "x", "y", event)
    assert event["admission_wait_s"] == 500.0
    assert event["stages"]["pre_commit"]["elapsed_s"] == 2.0
    assert set(event["stages"]) == {"pre_commit"}


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
        with gate.stage_measurement(event, "synthetic") as diagnostics:
            code, output = gate.run_bounded(
                [sys.executable, "-c", "print('synthetic output'); raise SystemExit(3)"],
                cwd=tmp_path,
                deadline=time.monotonic() + 30.0,
                label="synthetic",
                diagnostics=diagnostics,
            )
            assert code == 3 and output == "synthetic output\n"
            raise gate.GateOutcome("pre_commit_failed", "synthetic refusal")
    row = event["stages"]["synthetic"]
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


# ---- receipt persistence and stage I/O errors are typed incomplete outcomes ---------------------------------


def _validate_feature(repo: Path) -> None:
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    update = gate.Update("refs/heads/feature", head, "refs/heads/feature", ZERO_SHA)
    gate.validate(update, repo, *_hook_inputs(repo), {})


def test_a_failed_receipt_write_is_incomplete(repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "1")
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "pre-commit-cache"))
    monkeypatch.chdir(repo)

    def broken_receipt(*_args: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(gate, "write_receipt", broken_receipt)

    with pytest.raises(gate.GateOutcome) as raised:
        _validate_feature(repo)

    assert raised.value.reason == "receipt_unwritable" and raised.value.incomplete


def test_an_io_error_during_the_stage_is_incomplete(repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "1")
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")
    monkeypatch.setenv("PRE_COMMIT_HOME", str(tmp_path / "pre-commit-cache"))
    monkeypatch.chdir(repo)

    def broken_stage(*_args: object, **_kwargs: object) -> None:
        raise OSError("no space for the output file")

    monkeypatch.setattr(gate, "run_pre_commit_stage", broken_stage)

    with pytest.raises(gate.GateOutcome) as raised:
        _validate_feature(repo)

    assert raised.value.reason == "validation_error" and raised.value.incomplete
    assert _receipts(repo) == []


# ---- review round 6: startup I/O errors are typed, not unhandled -----------------------------------------


def test_a_startup_io_error_is_a_typed_incomplete_outcome_and_leaks_nothing(
    repo: Path, monkeypatch: pytest.MonkeyPatch
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

    def no_stage(*_args: object, **_kwargs: object) -> None:
        started.append("stage")

    monkeypatch.setattr(gate.os, "open", open_without_lock)
    monkeypatch.setattr(gate, "run_pre_commit_stage", no_stage)
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
    assert started == []  # no stage ran on an unadmitted gate
    monkeypatch.undo()
    with gate.Admission(state, 0.0):  # the admission lock was released, not leaked
        pass


# ---- #10383: private pytest temps and safe queue admission ----------------------------------------------


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


@pytest.mark.parametrize("area", ["direct", "queue"])
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
        stale = tmp_path / "stale-node"
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


# ---- #10523: exact-plan coalescing before global admission ---------------------------------------------

# A committed script the fixture's pre-commit hook runs when present: it holds the stage on a FIFO until the
# test releases it, and fails the stage unless released with ``green``.
CONTROL_STAGE = textwrap.dedent(
    """\
    import os
    from pathlib import Path

    control = Path(os.environ['GATE_TEST_CONTROL'])
    (control / 'entered').write_text('entered\\n')
    with (control / 'release').open() as release:
        raise SystemExit(0 if release.read() == 'green' else 1)
    """
)


def _start_controlled_gate(
    repo: Path, control: Path, *, base: str = ZERO_SHA, tool_change: bool = False, **environment: str
):
    control.mkdir()
    os.mkfifo(control / "release")
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    command = [sys.executable, str(repo / ".githooks/pre_push_gate.py")]
    if tool_change:
        # A synthetic tool version, with real build_plan, stages and production main: a key dimension
        # beyond the head and base.
        program = textwrap.dedent("""\
            import importlib.util, sys
            spec = importlib.util.spec_from_file_location('gate', sys.argv.pop(1))
            gate = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = gate
            spec.loader.exec_module(gate)
            original = gate.tool_versions
            gate.tool_versions = lambda *args: {**original(*args), 'pre_commit': 'control'}
            sys.exit(gate.main())
        """)
        command = [sys.executable, "-c", program, str(repo / ".githooks/pre_push_gate.py")]
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
    _write(repo, "control_stage.py", CONTROL_STAGE)
    head = _commit(repo, "controlled checks", "control_stage.py")
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
    rows = _measurements_in_start_order(repo)
    assert len(rows) == 2
    leader, follower = rows
    assert leader["queue_position"] == 3
    assert set(leader["stages"]) == {"pre_commit"} and leader["stages"]["pre_commit"]["outcome"] == "green"
    assert follower["detail"] == "valid receipt after coalescing"
    assert follower["coalescing_wait_s"] > 4
    assert follower["admission_wait_limit_s"] == 16
    assert "stages" not in follower and follower["queue_depth"] == 0
    assert len(_receipts(repo)) == 1
    _assert_queue_released(state)


def test_production_non_green_head_holder_keeps_later_global_allowance(repo: Path, tmp_path: Path) -> None:
    _write(repo, "control_stage.py", CONTROL_STAGE)
    head = _commit(repo, "controlled checks", "control_stage.py")
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
    assert row["queue_position"] == 2 and set(row["stages"]) == {"pre_commit"}
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
                assert row["stages"]["pre_commit"]["outcome"] == "green" and set(row["stages"]) == {"pre_commit"}
                assert remote == f"{head}\trefs/heads/feature"
        finally:
            fcntl.flock(head_lock, fcntl.LOCK_UN)
            fcntl.flock(global_lock, fcntl.LOCK_UN)
            _stop_controls(processes)
    _assert_queue_released(state)


def test_equivalent_production_followers_never_register_global_tickets(repo: Path, tmp_path: Path) -> None:
    _write(repo, "control_stage.py", CONTROL_STAGE)
    head = _commit(repo, "controlled checks", "control_stage.py")
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
    _write(repo, "docs/leak.md", "-----BEGIN " + "PRIVATE KEY-----\n")
    narrow_base = _commit(repo, "the wide range must scan this commit", "docs/leak.md")
    _write(repo, "control_stage.py", CONTROL_STAGE)
    head = _commit(repo, "narrow range is clean", "control_stage.py")
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
        assert _verdict(subprocess.CompletedProcess([], 1, stderr=stderr))["failing"] == ["lint-opsec-leaks"]
    finally:
        _stop_controls(processes)
    assert [row["outcome"] for row in _measurements(repo)] == ["green", "refused"]
    _assert_queue_released(state)


@pytest.mark.parametrize("ending", ["refused", "incomplete", "interrupted"])
def test_non_green_production_leader_releases_and_follower_checks_once(
    repo: Path, tmp_path: Path, ending: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "1")
    _write(repo, "control_stage.py", CONTROL_STAGE)
    head = _commit(repo, "controlled checks", "control_stage.py")
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
    _write(repo, "control_stage.py", CONTROL_STAGE)
    head = _commit(repo, "controlled checks", "control_stage.py")
    state = gate.state_dir(repo)
    controls = [tmp_path / "leader", tmp_path / "follower"]
    processes = []
    try:
        processes.append(_start_controlled_gate(repo, controls[0]))
        wait_for_line(controls[0] / "entered", stop_if=lambda: processes[0].poll() is not None)
        processes.append(_start_controlled_gate(repo, controls[1]))
        _wait_tickets(state / "heads" / head, 2, processes)
        if change == "tracked":
            _write(repo, "control_stage.py", "raise SystemExit(1)\n")  # a tracked file now differs from the commit
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
            gate.build_plan(update, native_repo, *_hook_inputs(native_repo))
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


@pytest.mark.parametrize("field", ["head", "tree", "base"])
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
def test_unsafe_coalescing_directory_never_reuses(
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


def test_same_head_production_tool_difference_cannot_coalesce(repo: Path, tmp_path: Path) -> None:
    _write(repo, "notes.txt", "base of the range\n")
    base = _commit(repo, "range base", "notes.txt")
    _write(repo, "control_stage.py", CONTROL_STAGE)
    head = _commit(repo, "controlled checks", "control_stage.py")
    state = gate.state_dir(repo)
    controls = [tmp_path / "original", tmp_path / "changed"]
    processes = []
    try:
        processes.append(_start_controlled_gate(repo, controls[0], base=base))
        wait_for_line(controls[0] / "entered", stop_if=lambda: processes[0].poll() is not None)
        processes.append(_start_controlled_gate(repo, controls[1], base=base, tool_change=True))
        _wait_tickets(state / "heads" / head, 2, processes)
        _finish_controlled(processes[0], controls[0])
        assert processes[0].returncode == 0
        stdout, stderr = _finish_controlled(processes[1], controls[1])
        assert processes[1].returncode == 0, stdout + stderr
    finally:
        _stop_controls(processes)
    rows = _measurements(repo)
    assert len(rows) == 2 and all("stages" in row for row in rows)
    _assert_queue_released(state)


def test_explicit_production_resubmission_joins_global_tail_after_incomplete(repo: Path, tmp_path: Path) -> None:
    _write(repo, "control_stage.py", CONTROL_STAGE)
    _commit(repo, "controlled checks", "control_stage.py")
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


def _cpu_pressure(avg10: str, avg60: str) -> str:
    return f"some avg10={avg10} avg60={avg60} avg300=1.00 total=10\nfull avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"


def _patch_admission_proc(monkeypatch, pressure, memory) -> None:
    """Feed /proc pressure and meminfo. Load average must not decide the second slot."""
    original = Path.read_text

    def read_text(path, *args, **kwargs):
        name = str(path)
        if name == "/proc/pressure/cpu":
            if isinstance(pressure, BaseException):
                raise pressure
            return pressure
        if name == "/proc/meminfo":
            if isinstance(memory, BaseException):
                raise memory
            return memory
        return original(path, *args, **kwargs)

    def load_must_not_decide():
        raise OSError("load average must not decide admission")

    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr(gate.os, "getloadavg", load_must_not_decide)


_EIGHT_GIB = 8 * 1024**3


@pytest.mark.parametrize(
    "pressure,memory,expected",
    [
        pytest.param(
            _cpu_pressure("10.00", "5.00"),
            "MemAvailable: 8388608 kB\n",
            {"cpu_some_avg10": 10.0, "cpu_some_avg60": 5.0, "mem_available_bytes": _EIGHT_GIB, "qualified": True},
            id="qualify",
        ),
        pytest.param(
            _cpu_pressure("34.00", "24.00"),
            "MemAvailable: 8388608 kB\n",
            {"cpu_some_avg10": 34.0, "cpu_some_avg60": 24.0, "mem_available_bytes": _EIGHT_GIB, "qualified": True},
            id="qualify-under-caps",
        ),
        pytest.param(
            _cpu_pressure("35.00", "5.00"),
            "MemAvailable: 8388608 kB\n",
            {"cpu_some_avg10": 35.0, "cpu_some_avg60": 5.0, "mem_available_bytes": _EIGHT_GIB, "qualified": False},
            id="cpu-busy-avg10",
        ),
        pytest.param(
            _cpu_pressure("10.00", "25.00"),
            "MemAvailable: 8388608 kB\n",
            {"cpu_some_avg10": 10.0, "cpu_some_avg60": 25.0, "mem_available_bytes": _EIGHT_GIB, "qualified": False},
            id="cpu-busy-avg60",
        ),
        pytest.param(
            _cpu_pressure("100.00", "100.00"),
            "MemAvailable: 8388608 kB\n",
            {
                "cpu_some_avg10": 100.0,
                "cpu_some_avg60": 100.0,
                "mem_available_bytes": _EIGHT_GIB,
                "qualified": False,
            },
            id="cpu-saturated",
        ),
        pytest.param(
            _cpu_pressure("10.00", "5.00"),
            "MemAvailable: 8388607 kB\n",
            {
                "cpu_some_avg10": 10.0,
                "cpu_some_avg60": 5.0,
                "mem_available_bytes": 8388607 * 1024,
                "qualified": False,
            },
            id="low-memory",
        ),
        pytest.param(
            "not-a-pressure-file\n",
            "MemAvailable: 8388608 kB\n",
            {"cpu_some_avg10": None, "cpu_some_avg60": None, "mem_available_bytes": None, "qualified": False},
            id="unreadable-pressure",
        ),
        pytest.param(
            _cpu_pressure("101.00", "5.00"),
            "MemAvailable: 8388608 kB\n",
            {"cpu_some_avg10": None, "cpu_some_avg60": None, "mem_available_bytes": None, "qualified": False},
            id="pressure-outside-percent",
        ),
        pytest.param(
            _cpu_pressure("10.00", "5.00"),
            "MemAvailable: garbage kB\n",
            {"cpu_some_avg10": None, "cpu_some_avg60": None, "mem_available_bytes": None, "qualified": False},
            id="unreadable-memory",
        ),
        pytest.param(
            "",
            "MemAvailable: 8388608 kB\n",
            {"cpu_some_avg10": None, "cpu_some_avg60": None, "mem_available_bytes": None, "qualified": False},
            id="empty-pressure",
        ),
        pytest.param(
            OSError("cpu pressure unavailable"),
            "MemAvailable: 8388608 kB\n",
            {"cpu_some_avg10": None, "cpu_some_avg60": None, "mem_available_bytes": None, "qualified": False},
            id="pressure-oserror",
        ),
    ],
)
def test_parallel_admission_uses_cpu_pressure_not_load(pressure, memory, expected, monkeypatch):
    _patch_admission_proc(monkeypatch, pressure, memory)
    assert gate.admission_resources() == expected


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
    assert terminal["peak_memory_bytes"] is None


@pytest.mark.parametrize("ending", ["green", "red"])
def test_actual_missing_user_bus_runs_each_serial_check_once(repo, ending, monkeypatch):
    _write(
        repo,
        "scripts/pre_commit/project_python.sh",
        textwrap.dedent(f"""\
        #!/bin/bash
        if [ "$1" = scripts/audit/lint_opsec_leaks.py ]; then echo opsec >> scans; exec "{sys.executable}" "$@"; fi
        if [ "$4" = check-no-internal-ids ]; then echo internal-ids >> scans; exec "{sys.executable}" "$@"; fi
        if [ "$2" = pre_commit ]; then echo pre >> checks; exit {dict(green=0, red=1)[ending]}; fi
        echo "other: $*" >> checks
        exit 3
    """),
    )
    _commit(repo, "serial fallback control", "scripts/pre_commit/project_python.sh")
    monkeypatch.chdir(repo)
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "2")
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
    assert code == dict(green=0, red=1)[ending]
    assert (repo / "checks").read_text().splitlines() == ["pre"]
    assert (repo / "scans").exists() == (ending == "green")
    if ending == "green":
        assert (repo / "scans").read_text().splitlines() == ["opsec", "internal-ids"]
    row = _measurements(repo)[-1]
    assert row["scope"]["status"] == "serial"
    assert row["scope"]["reason"].startswith("scope_setup_")
    assert row["peak_memory_bytes"] is None
    assert row["peak_memory_unknown_reason"] == "no_supported_scope"
    assert row["execution_s"] >= 0 and row["queue_wait_s"] >= 0
    assert set(row["stages"]) == {"pre_commit"}
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


@pytest.mark.parametrize("ending", ["green", "red", "missing_peak", "resource_breach", "unsettled"])
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
        if [ "$2" != pre_commit ]; then echo "other: $*" >> checks; exit 3; fi
        echo pre >> checks
        if [ {ending} = missing_peak ]; then find "{injected_systemd.parent / "cgroups"}" -name memory.peak -delete; fi
        if [ {ending} = resource_breach ]; then find "{injected_systemd.parent / "cgroups"}" -name memory.peak -exec sh -c 'echo {gate.SCOPE_MEMORY_MAX + 1} > "$1"' -- {{}} \\; ; fi
        if [ {ending} = unsettled ]; then find "{injected_systemd.parent / "cgroups"}" -name cgroup.procs -exec sh -c 'echo 999999999 >> "$1"' -- {{}} \\; ; fi
        exit {dict(green=0, red=1, missing_peak=0, resource_breach=0, unsettled=0)[ending]}
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
    assert code == dict(green=0, red=1, missing_peak=0, resource_breach=75, unsettled=75)[ending]
    assert (repo / "checks").read_text().splitlines() == ["pre"]
    assert (repo / "scans").exists() == (ending != "red")
    if ending != "red":
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
    assert set(row["stages"]) == {"pre_commit"}
    assert row["stage_budget_s"] == 300.0
    stage = row["stages"]["pre_commit"]
    assert stage["allowance_s"] == pytest.approx(300.0) and stage["allowance_limited_by"] == "stage_budget"
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
    _write(repo, "control_stage.py", CONTROL_STAGE)
    _commit(repo, "kill attempt control", "control_stage.py")
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

    monkeypatch.setattr(gate, "concurrent_run_limit", interrupt)
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


@pytest.mark.parametrize("step", ["unit kill", "executor reap", "descendant drain"])
def test_unverified_scope_cleanup_names_the_step_that_failed(tmp_path, qualified_cgroups, monkeypatch, step):
    monkeypatch.setattr(gate, "CLEANUP_BUDGET_S", 0.2)
    scope = gate.ResourceScope(tmp_path, "unused", gate.Admission(tmp_path / "head", 0))
    _fake_cgroup(qualified_cgroups, scope.unit)  # stays populated: only the drain step reads it
    scope.group = "/" + scope.unit
    scope.completed = step != "unit kill"  # a settled executor is reaped without a kill
    body = _BLOCK_UNTIL_KILLED if step == "executor reap" else "pass"
    scope.process = process = subprocess.Popen([sys.executable, "-c", body], env=_env())
    if step != "executor reap":
        process.wait(timeout=10)

    def kill(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(gate.subprocess, "run", kill)
    try:
        with pytest.raises(gate.GateOutcome) as raised:
            scope.close()
    finally:
        process.kill()
        process.wait(timeout=10)

    error = {"unit kill": "TimeoutExpired", "executor reap": "TimeoutExpired", "descendant drain": "OSError"}[step]
    settled = "not proven settled" if step == "unit kill" else "settled"
    assert raised.value.incomplete and raised.value.reason == "validation_incomplete"
    assert raised.value.detail == f"own scope cleanup is unverified at the {step} ({error}; executor {settled}); stop"
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
    real_pre_commit = gate.run_pre_commit_stage
    _fake_validation(tmp_path, monkeypatch, clock)
    monkeypatch.setattr(gate, "run_pre_commit_stage", real_pre_commit)
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "1")
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
        return 0, f"{label} passed in {need}s"

    monkeypatch.setattr(gate, "run_bounded", run_bounded)


UPDATE = gate.Update("local", "a" * 40, "remote", ZERO_SHA)
INSTANT_SCANS = {"per-commit OPSEC scan": [0.0], "learner-surface internal-ID scan": [0.0]}


def test_the_stage_still_expires_at_its_own_allowance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = FakeClock()
    _journal_shaped_push(tmp_path, monkeypatch, clock, {"pre-commit pre-push stage": [650.0]})
    event: dict[str, object] = {}
    with pytest.raises(gate.GateOutcome) as raised:
        gate.validate(UPDATE, tmp_path, "x", "y", event)

    assert raised.value.incomplete and raised.value.failing == ()
    assert "exceeded the time budget (timeout)" in raised.value.detail
    assert set(event["stages"]) == {"pre_commit"}
    row = event["stages"]["pre_commit"]
    assert row["outcome"] == "validation_incomplete" and row["signal"] == signal.SIGKILL
    assert row["elapsed_s"] == pytest.approx(gate.STAGE_BUDGET_S) == row["allowance_s"]
    assert row["allowance_limited_by"] == "stage_budget"
    assert not gate.receipt_is_fresh(tmp_path, _plan(), clock.time())


def test_the_run_budget_caps_the_stage_allowance_across_ref_updates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = FakeClock()
    _journal_shaped_push(tmp_path, monkeypatch, clock, {"pre-commit pre-push stage": [550.0, 10.0]})
    budget = gate.Budget(500.0, 600.0)  # a total shorter than the allowance binds the stage
    event: dict[str, object] = {}
    with pytest.raises(gate.GateOutcome) as raised:
        gate.validate(UPDATE, tmp_path, "x", "y", event, budget)

    assert raised.value.incomplete and raised.value.failing == ()
    stage = event["stages"]["pre_commit"]
    assert stage["allowance_s"] == pytest.approx(500.0) and stage["allowance_limited_by"] == "run_budget"
    assert stage["elapsed_s"] == pytest.approx(500.0)

    # One push shares the total across its ref updates: the second gets only what the first left.
    second: dict[str, object] = {}
    with pytest.raises(gate.GateOutcome):
        gate.validate(UPDATE, tmp_path, "x", "y", second, budget)
    assert second["stages"]["pre_commit"]["allowance_s"] == pytest.approx(0.0)
    assert second["stages"]["pre_commit"]["allowance_limited_by"] == "run_budget"


def test_admission_waits_consume_neither_the_stage_allowance_nor_the_total(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = FakeClock()
    # The stage uses almost all of its own allowance after the 500 s admission wait.
    needs = {
        "pre-commit pre-push stage": [590.0],
        "per-commit OPSEC scan": [4.0],
        "learner-surface internal-ID scan": [4.0],
    }
    _journal_shaped_push(tmp_path, monkeypatch, clock, needs)
    event: dict[str, object] = {}
    gate.validate(UPDATE, tmp_path, "x", "y", event, gate.Budget(600.0, 600.0))

    assert event["outcome"] == "green" and event["admission_wait_s"] == 500.0
    assert clock.now == pytest.approx(500.0 + 598.0)
    assert event["stages"]["pre_commit"]["allowance_limited_by"] == "stage_budget"
    assert gate.receipt_is_fresh(tmp_path, _plan(), clock.time())


def _stage_launcher(repo: Path, pre_commit: str) -> None:
    """A synthetic launcher whose pre-commit commands run the given shell body; scans are instant."""
    _write(
        repo,
        "scripts/pre_commit/project_python.sh",
        textwrap.dedent(f"""\
        if [ "$1" = scripts/audit/lint_opsec_leaks.py ]; then exit 0; fi
        if [ "$2" = pre_commit ]; then
        {pre_commit}
        exit 0
        fi
        echo "unexpected launch: $*" >> launched-otherwise
        exit 3
        """),
    )
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "synthetic timed stages", "tests/test_new.py", "scripts/pre_commit/project_python.sh")


@pytest.mark.parametrize("ending", ["green", "red"])
def test_the_actual_stage_runs_inside_its_own_allowance(repo: Path, ending: str) -> None:
    # pre-commit runs twice (pre-push stage, internal-ID scan), about 3 s together, under a 5 s allowance.
    verdict = 'case "$*" in *--hook-stage\\ pre-push*) echo "fixture................Failed"; exit 1;; esac'
    _stage_launcher(repo, "sleep 1.5; " + (verdict if ending == "red" else ":"))

    result = _run_gate(repo, extra_env={gate.MAX_CONCURRENT_RUNS_ENV: "1", "LU_PRE_PUSH_GATE_STAGE_BUDGET_S": "5"})

    assert result.returncode == (0 if ending == "green" else gate.EXIT_REFUSED), result.stderr
    row = _measurements(repo)[-1]
    stage = row["stages"]["pre_commit"]
    assert set(row["stages"]) == {"pre_commit"}
    assert row["stage_budget_s"] == 5.0 and row["run_budget_s"] == gate.RUN_BUDGET_S
    assert stage["allowance_s"] == pytest.approx(5.0) and stage["allowance_limited_by"] == "stage_budget"
    assert stage["elapsed_s"] < stage["allowance_s"]
    assert not (repo / "launched-otherwise").exists()
    if ending == "green":
        assert row["outcome"] == "green" and len(_receipts(repo)) == 1
    else:
        assert _verdict(result) == {"outcome": "refused", "reason": "pre_commit_failed", "failing": ["fixture"]}
        assert _receipts(repo) == []


@pytest.mark.parametrize("bound", ["stage", "total"])
def test_an_actual_overrun_is_killed_at_its_bound_with_descendants(repo: Path, tmp_path: Path, bound: str) -> None:
    pid_file = tmp_path / "child.pid"
    (tmp_path / "detach.py").write_text(_DETACHED_CHILD, encoding="utf-8")
    _stage_launcher(repo, f'"{sys.executable}" "{tmp_path / "detach.py"}" "{pid_file}"; sleep 60')
    budgets = {"LU_PRE_PUSH_GATE_STAGE_BUDGET_S": "3"}
    if bound == "total":  # the run budget is shorter than the stage allowance and binds it
        budgets = {"LU_PRE_PUSH_GATE_STAGE_BUDGET_S": "4", "LU_PRE_PUSH_GATE_RUN_BUDGET_S": "3"}

    result = _run_gate(repo, extra_env={gate.MAX_CONCURRENT_RUNS_ENV: "1", **budgets})

    assert result.returncode == gate.EXIT_INCOMPLETE, result.stderr
    row = _measurements(repo)[-1]
    killed = row["stages"]["pre_commit"]
    # The reason is typed by the host load the killed stage observed (#11140); this host's load is not pinned.
    reason = "timeout_under_load" if killed["load_at_timeout"]["load"] == "above_caps" else "timeout"
    assert _verdict(result) == {"outcome": "validation_incomplete", "reason": reason, "failing": []}
    assert killed["reason"] == row["reason"] == reason
    assert "NOT green" in result.stderr and _receipts(repo) == []
    assert _gone(int(pid_file.read_text(encoding="utf-8")))
    assert row["outcome"] == "validation_incomplete" and row["failing"] == []
    assert set(row["stages"]) == {"pre_commit"}
    assert killed["outcome"] == "validation_incomplete" and killed["signal"] == signal.SIGKILL
    assert killed["allowance_s"] <= killed["elapsed_s"] < killed["allowance_s"] + 2 * gate.CLEANUP_BUDGET_S
    if bound == "total":
        assert killed["allowance_limited_by"] == "run_budget" and killed["allowance_s"] < 4.0
    else:
        assert killed["allowance_limited_by"] == "stage_budget"
        assert killed["allowance_s"] == pytest.approx(3.0)


def test_the_stage_allowance_and_run_budget_are_unchanged() -> None:
    """Removing the test stage changes no remaining timeout (#11276)."""
    assert (gate.STAGE_BUDGET_S, gate.RUN_BUDGET_S) == (600, 1200)


# ---- #10820: closed scoped executors and main-refresh base selection ---------------------------------------


def test_exclusive_admission_never_keeps_an_unstarted_scope(qualified_cgroups, tmp_path):
    """A busy sharing transition falls back to exclusive admission, which must run the serial path."""
    state = tmp_path / "state"
    state.mkdir()
    candidate = InjectedScope(qualified_cgroups)
    with (state / "sharing.lock").open("a") as busy:
        fcntl.flock(busy, fcntl.LOCK_EX | fcntl.LOCK_NB)  # another waiter is inside its transition check
        with gate.Admission(state, 0, scope=candidate) as admitted:
            assert admitted._exclusive and admitted.scope is None
            assert candidate.group is None and candidate.reason == "exclusive_admission_serial"
            fd = os.open(state / "admission.lock", os.O_RDWR)
            try:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)  # the serial holder still excludes sharing
            finally:
                os.close(fd)
    _assert_queue_released(state)


@pytest.mark.parametrize("ending", ["green", "red"])
def test_a_busy_sharing_transition_validates_once_on_the_serial_path(repo, ending, monkeypatch, qualified_cgroups):
    """The #10820 crash: an exclusive holder kept its unstarted scope and ``execute`` hit an assertion."""
    _write(
        repo,
        "scripts/pre_commit/project_python.sh",
        textwrap.dedent(f"""\
        #!/bin/bash
        if [ "$1" = scripts/audit/lint_opsec_leaks.py ]; then echo opsec >> scans; exec "{sys.executable}" "$@"; fi
        if [ "$4" = check-no-internal-ids ]; then echo internal-ids >> scans; exec "{sys.executable}" "$@"; fi
        if [ "$2" = pre_commit ]; then echo pre >> checks; exit {dict(green=0, red=1)[ending]}; fi
        echo "other: $*" >> checks
        exit 3
    """),
    )
    _commit(repo, "serial fallback after a busy sharing transition", "scripts/pre_commit/project_python.sh")
    monkeypatch.chdir(repo)
    monkeypatch.setenv(gate.MAX_CONCURRENT_RUNS_ENV, "2")
    state = gate.state_dir(repo)
    state.mkdir(parents=True, exist_ok=True)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    with (state / "sharing.lock").open("a") as busy:
        fcntl.flock(busy, fcntl.LOCK_EX | fcntl.LOCK_NB)
        code = gate.main(
            [
                "--launcher",
                str(repo / "scripts/pre_commit/project_python.sh"),
                "--config",
                str(repo / ".pre-commit-config.yaml"),
            ],
            stdin=f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
        )
    assert code == dict(green=0, red=1)[ending]
    assert (repo / "checks").read_text().splitlines() == ["pre"]
    assert (repo / "scans").exists() == (ending == "green")
    row = _measurements(repo)[-1]
    assert row["outcome"] == dict(green="green", red="refused")[ending]
    assert row["scope"] == {"status": "serial", "reason": "exclusive_admission_serial"}
    assert set(row["stages"]) == {"pre_commit"}
    assert (_receipts(repo) != []) is (ending == "green")  # only a genuinely passed execution is green
    _assert_queue_released(state)


@pytest.mark.parametrize("condition", ["unstarted", "closed"])
def test_a_missing_or_closed_scope_is_typed_incomplete_and_runs_nothing(
    tmp_path: Path, injected_systemd: object, qualified_cgroups: object, condition: str
) -> None:
    state = tmp_path / "state"
    launcher = tmp_path / "launcher"
    launcher.write_text(f'#!/bin/bash\nexec "{sys.executable}" "$@"\n')
    event: dict[str, object] = {}
    with gate.Admission(state / "head", 0) as head:
        scope = gate.ResourceScope(tmp_path, str(launcher), head)
        with contextlib.ExitStack() as admitted:
            if condition == "closed":
                admission = admitted.enter_context(gate.Admission(state, 0, scope=scope))
                assert admission.scope is scope and scope.stream is not None  # a genuinely started scope
                scope.close()
            with pytest.raises(gate.GateOutcome) as raised:
                scope.execute(_plan(), "config", time.monotonic() + 30, event, stage_budget_s=30.0)
    assert raised.value.reason == "scope_setup_unavailable" and raised.value.incomplete
    assert event == {} and not scope.completed  # no stage ran and nothing was inferred
    _assert_queue_released(state)


def _feature_remote_then_newer_main(repo: Path) -> tuple[str, str]:
    """An older pushed feature tip, then newer main on ``origin`` with changes unrelated to the feature."""
    _write(repo, "tests/test_feature_old.py", GREEN_TEST)
    remote = _commit(repo, "feature work already on the remote", "tests/test_feature_old.py")
    _git(repo, "push", "--no-verify", "origin", "feature")
    _git(repo, "checkout", "main")
    _write(repo, "tests/test_main_only.py", GREEN_TEST)
    _write(repo, "scripts/main_only.py", "VALUE = 1\n")
    main = _commit(repo, "unrelated main change", "tests/test_main_only.py", "scripts/main_only.py")
    _git(repo, "push", "--no-verify", "origin", "main")
    _git(repo, "checkout", "feature")
    return remote, main


def _merge_main(repo: Path) -> str:
    _git(repo, "merge", "--no-ff", "--no-edit", "-m", "merge newer main", "main")
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _update(repo: Path, remote_sha: str) -> object:
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    return gate.Update("refs/heads/feature", head, "refs/heads/feature", remote_sha)


def _range_paths(repo: Path, plan) -> tuple[str, ...]:
    """The paths the scanned range ``plan.base..plan.head`` adds or changes."""
    names = _git(repo, "diff", "--name-only", "--no-renames", "--diff-filter=d", f"{plan.base}..{plan.head}").stdout
    return tuple(sorted(names.split()))


def _range_tests(repo: Path, plan) -> tuple[str, ...]:
    return tuple(path for path in _range_paths(repo, plan) if re.fullmatch(r"tests/(?:.+/)?test_[^/]+\.py", path))


def _pull_request_paths(repo: Path) -> tuple[str, ...]:
    """What the pull request carries: the three-dot diff from the merge-base with ``origin/main``."""
    names = _git(repo, "diff", "--name-only", "--diff-filter=ACMR", "origin/main...HEAD").stdout.split()
    return tuple(sorted(names))


@pytest.mark.parametrize("commit_after_merge", [False, True])
def test_a_merge_of_newer_main_scans_the_pull_request_change_not_mains(repo: Path, commit_after_merge: bool) -> None:
    remote, main = _feature_remote_then_newer_main(repo)
    _merge_main(repo)
    expected = ["tests/test_feature_old.py"]
    if commit_after_merge:
        _write(repo, "tests/test_feature_new.py", GREEN_TEST)
        _commit(repo, "feature work after the merge", "tests/test_feature_new.py")
        expected.append("tests/test_feature_new.py")

    plan = gate.build_plan(_update(repo, remote), repo, *_hook_inputs(repo))

    assert plan is not None and plan.base == main
    assert _range_tests(repo, plan) == tuple(sorted(expected))
    assert _range_paths(repo, plan) == _pull_request_paths(repo)
    assert not {"scripts/main_only.py", "tests/test_main_only.py"} & set(_range_paths(repo, plan))


def _criss_cross(repo: Path) -> tuple[str, str, tuple[str, ...]]:
    """Main and feature each merged the other's tip: two merge-bases, so the range is not narrowed."""
    _write(repo, "tests/test_a_side.py", GREEN_TEST)
    remote = _commit(repo, "feature side", "tests/test_a_side.py")
    _git(repo, "checkout", "main")
    _write(repo, "tests/test_b_side.py", GREEN_TEST)
    _commit(repo, "main side", "tests/test_b_side.py")
    _git(repo, "checkout", "feature")
    _git(repo, "merge", "--no-ff", "--no-edit", "-m", "feature merges main", "main")
    _git(repo, "checkout", "main")
    _git(repo, "merge", "--no-ff", "--no-edit", "-m", "main merges feature side", remote)
    _git(repo, "push", "--no-verify", "origin", "main")
    _git(repo, "checkout", "feature")
    bases = _git(repo, "merge-base", "--all", "origin/main", "HEAD").stdout.split()
    assert len(bases) == 2
    return remote, remote, ("tests/test_b_side.py",)


def _graph(repo: Path, kind: str) -> tuple[str, str, tuple[str, ...]]:
    """Build one control graph; return the remote tip, the expected base and the expected changed tests."""
    fork = _git(repo, "rev-parse", "HEAD").stdout.strip()
    if kind == "criss_cross":
        return _criss_cross(repo)
    if kind in ("incremental", "new_branch"):
        _write(repo, "tests/test_feature_old.py", GREEN_TEST)
        remote = _commit(repo, "feature work already on the remote", "tests/test_feature_old.py")
    else:
        remote, main = _feature_remote_then_newer_main(repo)
    if kind == "rebased_onto_newer_main":
        _git(repo, "rebase", "main")
        return remote, main, ("tests/test_feature_old.py",)
    if kind == "unproven_main":
        _merge_main(repo)
        _git(repo, "update-ref", "-d", "refs/remotes/origin/main")  # main cannot be resolved: no narrowing
        return remote, remote, ("tests/test_main_only.py",)
    _write(repo, "tests/test_feature_new.py", GREEN_TEST)
    _commit(repo, "new feature work", "tests/test_feature_new.py")
    if kind == "new_branch":
        return ZERO_SHA, fork, ("tests/test_feature_new.py", "tests/test_feature_old.py")
    return remote, remote, ("tests/test_feature_new.py",)  # incremental, main moved or not


@pytest.mark.parametrize(
    "kind",
    ["incremental", "incremental_main_moved", "new_branch", "rebased_onto_newer_main", "unproven_main", "criss_cross"],
)
def test_base_selection_controls_keep_the_complete_outgoing_range(repo: Path, kind: str) -> None:
    remote, expected_base, expected_tests = _graph(repo, kind)

    plan = gate.build_plan(_update(repo, remote), repo, *_hook_inputs(repo))

    assert plan is not None and plan.base == expected_base
    assert _range_tests(repo, plan) == expected_tests
    # Without one proven merge-base the previous range stays, so the scans cover it whole.
    expected_fallback = {"unproven_main": "merge_base_unavailable", "criss_cross": "merge_base_ambiguous"}
    assert plan.base_fallback == expected_fallback.get(kind)


@pytest.mark.parametrize("failure", ["exit_128", "timeout"])
def test_an_ancestry_error_never_narrows_the_range(repo: Path, monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    remote, main = _feature_remote_then_newer_main(repo)
    _merge_main(repo)
    real_git = gate.git

    def git(*args: str, cwd: Path, timeout: float = 30.0):
        if args == ("merge-base", "--is-ancestor", main, remote):
            if failure == "timeout":
                raise subprocess.TimeoutExpired(["git", *args], timeout)
            return subprocess.CompletedProcess(["git", *args], 128, "", "fatal: synthetic")
        return real_git(*args, cwd=cwd, timeout=timeout)

    monkeypatch.setattr(gate, "git", git)

    plan = gate.build_plan(_update(repo, remote), repo, *_hook_inputs(repo))

    assert plan is not None and plan.base == remote
    assert "tests/test_main_only.py" in _range_tests(repo, plan)  # uncertainty keeps the complete outgoing range
    assert plan.base_fallback == "merge_base_unproven"


def test_a_divergent_push_without_history_in_common_with_main_is_refused(repo: Path) -> None:
    _write(repo, "tests/test_feature_old.py", GREEN_TEST)
    remote = _commit(repo, "feature work already on the remote", "tests/test_feature_old.py")
    _git(repo, "checkout", "--orphan", "lonely")
    _commit(repo, "unrelated history", ".")

    with pytest.raises(gate.GateOutcome) as raised:
        gate.build_plan(_update(repo, remote), repo, *_hook_inputs(repo))

    assert raised.value.reason == "range_unresolved" and not raised.value.incomplete


def test_a_pushed_main_refresh_validates_and_records_the_pull_request_base(repo: Path) -> None:
    remote, main = _feature_remote_then_newer_main(repo)
    _merge_main(repo)

    result = _run_gate(repo, remote_sha=remote)

    assert result.returncode == 0, result.stderr
    row = _measurements(repo)[-1]
    assert row["outcome"] == "green" and row["base"] == main and row["base_fallback"] is None


def _main_contains_the_head(repo: Path, relation: str, feature_test: str = GREEN_TEST) -> str:
    """An older feature remote, a later feature commit, a merge of newer main, then main reaching the head.

    The remote stays at its old tip, so the update is not empty, yet the merge-base with ``origin/main`` is the
    head itself: the graph that skipped every required check (#10820 review F1).
    """
    remote, _main = _feature_remote_then_newer_main(repo)
    _write(repo, "tests/test_feature_new.py", feature_test)
    _commit(repo, "feature work after the remote tip", "tests/test_feature_new.py")
    head = _merge_main(repo)
    _git(repo, "push", "--no-verify", "origin", "HEAD:main")
    if relation == "descendant":
        _git(repo, "checkout", "main")
        _git(repo, "merge", "--ff-only", "feature")
        _write(repo, "notes/after_landing.md", "main moved on\n")
        _commit(repo, "main after the feature landed", "notes/after_landing.md")
        _git(repo, "push", "--no-verify", "origin", "main")
        _git(repo, "checkout", "feature")
    assert _git(repo, "merge-base", "origin/main", "HEAD").stdout.strip() == head
    assert _git(repo, "rev-parse", "origin/main").stdout.strip() != head or relation == "equal"
    return remote


@pytest.mark.parametrize("relation", ["equal", "descendant"])
def test_a_main_that_contains_the_head_keeps_the_complete_outgoing_range(repo: Path, relation: str) -> None:
    remote = _main_contains_the_head(repo, relation)

    plan = gate.build_plan(_update(repo, remote), repo, *_hook_inputs(repo))

    assert plan is not None and plan.base == remote  # never the head: the update moves the remote
    assert _range_tests(repo, plan) == ("tests/test_feature_new.py", "tests/test_main_only.py")
    assert plan.base_fallback == "merge_base_is_head"


LEAKED_KEY = "-----BEGIN " + "PRIVATE KEY-----\n"


@pytest.mark.parametrize("ending", ["green", "red"])
@pytest.mark.parametrize("relation", ["equal", "descendant"])
def test_an_outgoing_update_inside_main_still_runs_its_required_checks(repo: Path, relation: str, ending: str) -> None:
    remote = _main_contains_the_head(repo, relation, GREEN_TEST if ending == "green" else LEAKED_KEY)

    result = _run_gate(repo, remote_sha=remote, extra_env={gate.MAX_CONCURRENT_RUNS_ENV: "1"})

    row = _measurements(repo)[-1]
    assert row.get("detail") != "no outgoing commits" and row["base"] == remote
    assert set(row["stages"]) == {"pre_commit"}
    assert row["base_fallback"] == "merge_base_is_head"
    if ending == "green":
        assert result.returncode == 0, result.stderr
        assert row["outcome"] == "green" and len(_receipts(repo)) == 1
    else:  # the per-commit scan still covers a range main already contains
        assert result.returncode == gate.EXIT_REFUSED, result.stderr
        assert _verdict(result) == {
            "outcome": "refused",
            "reason": "pre_commit_failed",
            "failing": ["lint-opsec-leaks"],
        }
        assert _receipts(repo) == []


def test_an_unmoved_remote_inside_main_is_still_nothing_outgoing(repo: Path) -> None:
    _main_contains_the_head(repo, "equal")
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()

    result = _run_gate(repo, remote_sha=head)

    assert result.returncode == 0, result.stderr
    row = _measurements(repo)[-1]
    assert row["detail"] == "no outgoing commits" and "stages" not in row


# ---- #10820: a new branch inside main still runs its checks -------------------------------------------------


def test_a_new_branch_already_inside_main_still_runs_the_stage(repo: Path) -> None:
    """A new branch whose head ``origin/main`` contains: the merge-base is the head, never "nothing outgoing"."""
    result = _run_gate(repo)  # the fixture's feature branch is still main's tip

    assert result.returncode == 0, result.stderr
    row = _measurements(repo)[-1]
    assert row.get("detail") != "no outgoing commits" and set(row["stages"]) == {"pre_commit"}
    assert row["base"] == row["head"] and row["base_fallback"] == "merge_base_is_head"


def test_a_new_branch_without_origin_main_is_refused_as_unresolved(repo: Path) -> None:
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "new", "tests/test_new.py")
    _git(repo, "update-ref", "-d", "refs/remotes/origin/main")

    result = _run_gate(repo)  # no remote tip and no origin/main: no range can be named

    assert result.returncode == gate.EXIT_REFUSED
    assert _verdict(result)["reason"] == "range_unresolved"
    assert _receipts(repo) == []


# ---- #11140: a stage timeout is typed by the observed load and never hides a reported failure -----------


def _observation(avg10: float | None, avg60: float | None, memory: int | None) -> dict[str, object]:
    """The shape ``admission_resources`` returns, qualified by the same admission caps."""
    return {
        "cpu_some_avg10": avg10,
        "cpu_some_avg60": avg60,
        "mem_available_bytes": memory,
        "qualified": avg10 is not None
        and avg60 is not None
        and memory is not None
        and avg10 < gate.CPU_SOME_AVG10_MAX
        and avg60 < gate.CPU_SOME_AVG60_MAX
        and memory >= 8 * 1024**3,
    }


GIB = 1024**3
TIMEOUT_LOADS = {
    "cpu_avg10_at_cap": (_observation(gate.CPU_SOME_AVG10_MAX, 1.0, 64 * GIB), "above_caps", "timeout_under_load"),
    "cpu_avg60_at_cap": (_observation(1.0, gate.CPU_SOME_AVG60_MAX, 64 * GIB), "above_caps", "timeout_under_load"),
    "memory_short": (_observation(1.0, 1.0, 8 * GIB - 1), "above_caps", "timeout_under_load"),
    "below_caps": (_observation(24.8, 12.0, 64 * GIB), "below_caps", "timeout"),
    "unobserved": (_observation(None, None, None), "unknown", "timeout"),
    "partly_observed": (_observation(90.0, None, 64 * GIB), "unknown", "timeout"),
}


@pytest.mark.parametrize("case", sorted(TIMEOUT_LOADS))
def test_a_killed_stage_is_typed_by_the_load_observed_at_its_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    observed, load, reason = TIMEOUT_LOADS[case]
    monkeypatch.setattr(gate, "admission_resources", lambda: dict(observed))
    hung = tmp_path / "hung"
    script = f"open({str(hung)!r}, 'w').close()\n" + _BLOCK_UNTIL_KILLED
    _wait_once_child_hangs(monkeypatch, hung)
    diagnostics: dict[str, object] = {}

    with pytest.raises(gate.GateOutcome) as raised:
        gate.run_bounded(
            [sys.executable, "-c", script],
            cwd=tmp_path,
            deadline=time.monotonic() + 1.5,
            label="pre-commit pre-push stage",
            diagnostics=diagnostics,
        )

    error = raised.value
    assert error.reason == reason and error.incomplete and error.failing == ()
    assert error.detail.startswith(
        "pre-commit pre-push stage: exceeded the time budget (timeout); host load at the timeout: "
    )
    assert ("unobserved" in error.detail) is (load == "unknown")
    assert diagnostics["load_at_timeout"] == {
        "cpu_some_avg10": observed["cpu_some_avg10"],
        "cpu_some_avg60": observed["cpu_some_avg60"],
        "mem_available_bytes": observed["mem_available_bytes"],
        "load": load,
    }
    assert diagnostics["signal"] == signal.SIGKILL


def test_a_budget_spent_before_a_stage_starts_is_typed_like_any_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "admission_resources", lambda: _observation(None, None, None))
    diagnostics: dict[str, object] = {}

    with pytest.raises(gate.GateOutcome) as raised:
        gate.run_bounded(
            ["true"], cwd=Path("."), deadline=time.monotonic() - 1, label="pre-commit stage", diagnostics=diagnostics
        )

    assert raised.value.reason == "timeout" and raised.value.incomplete
    assert "time budget exhausted before start (timeout)" in raised.value.detail
    assert diagnostics["child_unavailable_reason"] == "budget_exhausted_before_start"
    load = diagnostics["load_at_timeout"]
    assert isinstance(load, dict) and load["load"] == "unknown"


# ---- receipts bind every field (#11207); a receipt of the test-running gate is never reused (#11276) ------


def _altered(value: object) -> object:
    if isinstance(value, bool) or value is None:
        return "altered"
    if isinstance(value, int | float):
        return value + 1
    if isinstance(value, str):
        return value + "-altered"
    if isinstance(value, dict):
        return {**value, "altered": True}
    raise AssertionError(f"no alteration for {value!r}")


# Every field of a green receipt: the reuse check must refuse each one removed and each one altered.
RECEIPT_FIELDS = (
    ("seal",),
    ("outcome",),
    ("at",),
    ("key",),
    ("key", "gate_version"),
    ("key", "head"),
    ("key", "tree"),
    ("key", "base"),
    ("key", "base_fallback"),
    ("key", "tools"),
    *(("key", "tools", name) for name in gate.TOOL_NAMES),
)
TOOLS = {name: f"{name}-1" for name in gate.TOOL_NAMES}


def _receipt_plan(**overrides):
    return _plan(tools=dict(TOOLS), **overrides)


def test_the_receipt_field_table_covers_every_written_field(tmp_path: Path) -> None:
    gate.write_receipt(tmp_path, _receipt_plan(), 1000.0)
    receipt = json.loads(gate.receipt_path(tmp_path, _receipt_plan()).read_text(encoding="utf-8"))

    def paths(value: object, prefix: tuple[str, ...]) -> set[tuple[str, ...]]:
        found = {prefix} if prefix else set()
        if isinstance(value, dict):
            for name, item in value.items():
                found |= paths(item, (*prefix, name))
        return found

    assert paths(receipt, ()) == set(RECEIPT_FIELDS)


# Resealed: a sealed receipt that differs as written, e.g. by other gate code; a later time is a later receipt.
RESEALED_ACCEPTED = {(("at",), "altered")}


@pytest.mark.parametrize("sealed", ["edited", "resealed"])
@pytest.mark.parametrize("change", ["removed", "altered", "extra"])
@pytest.mark.parametrize("field", RECEIPT_FIELDS, ids=".".join)
def test_a_receipt_with_a_missing_or_altered_field_is_never_reused(
    tmp_path: Path, field: tuple[str, ...], change: str, sealed: str
) -> None:
    if sealed == "resealed" and field == ("seal",):
        return  # resealing would overwrite the very change under test; "edited" covers the seal
    gate.write_receipt(tmp_path, _receipt_plan(), 1000.0)
    path = gate.receipt_path(tmp_path, _receipt_plan())
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert gate.receipt_is_fresh(tmp_path, _receipt_plan(), 1001.0)

    *parents, name = field
    holder = receipt
    for parent in parents:
        holder = holder[parent]
    if change == "removed":
        holder.pop(name, None)
    elif change == "altered":
        holder[name] = _altered(holder.get(name))
    else:
        holder[name] = {"value": holder.get(name), "extra": 1} if name != "key" else {**holder[name], "extra": 1}
    if sealed == "resealed":
        body = {name: receipt[name] for name in ("key", "outcome", "at") if name in receipt}
        receipt["seal"] = gate.receipt_seal(body)
    path.write_text(json.dumps(receipt), encoding="utf-8")

    accepted = sealed == "resealed" and (field, change) in RESEALED_ACCEPTED
    assert gate.receipt_is_fresh(tmp_path, _receipt_plan(), 1001.0) is accepted


def test_a_receipt_for_a_different_tool_or_base_fallback_is_never_reused(tmp_path: Path) -> None:
    gate.write_receipt(tmp_path, _receipt_plan(), 1000.0)

    for name in gate.TOOL_NAMES:
        assert not gate.receipt_is_fresh(tmp_path, _plan(tools={**TOOLS, name: "other"}), 1001.0), name
    assert not gate.receipt_is_fresh(tmp_path, _receipt_plan(base_fallback="merge_base_ambiguous"), 1001.0)
    gate.write_receipt(tmp_path, _receipt_plan(base_fallback="merge_base_ambiguous"), 1000.0)
    assert gate.receipt_is_fresh(tmp_path, _receipt_plan(base_fallback="merge_base_ambiguous"), 1001.0)
    assert not gate.receipt_is_fresh(tmp_path, _receipt_plan(), 1001.0)


# ---- the tree that runs is the outgoing commit -----------------------------------------------------------


def test_a_dirty_gitlink_is_a_dirty_tree_whatever_the_submodule_setting(repo: Path) -> None:
    """A submodule checked out at another commit than the outgoing one: the tree that would run differs."""
    nested = repo / "vendor/lib"
    nested.mkdir(parents=True)
    _git(nested, "init", "-q", "-b", "main")
    _git(nested, "config", "user.email", "gate@example.invalid")
    _git(nested, "config", "user.name", "Gate Test")
    for message in ("first", "second"):
        _git(nested, "commit", "-q", "--allow-empty", "-m", message)
    first = _git(nested, "rev-parse", "HEAD~1").stdout.strip()
    _git(repo, "update-index", "--add", "--cacheinfo", f"160000,{first},vendor/lib")
    _git(repo, "commit", "-m", "a gitlink behind its checkout")
    _git(repo, "config", "diff.ignoreSubmodules", "all")

    with pytest.raises(gate.GateOutcome) as refused:
        gate.build_plan(_update(repo, ZERO_SHA), repo, *_hook_inputs(repo))

    assert refused.value.reason == "dirty_tree"


@pytest.mark.parametrize(
    ("returncode", "stdout", "records"),
    [
        (0, b"", []),
        (0, b"D\0scripts/gone.py\0", ["D", "scripts/gone.py"]),
        (0, b"D\0scripts/a\xffb.py\0", ["D", "scripts/a\udcffb.py"]),  # not UTF-8: kept whole, no crash
        (0, b"D\0scripts/gone.py\0M\0scripts/kep", None),  # cut short: the last name is not known whole
        (128, b"D\0scripts/gone.py\0", None),
    ],
)
def test_a_listing_is_read_only_when_git_succeeds_and_ends_on_a_record(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, returncode: int, stdout: bytes, records: list[str] | None
) -> None:
    completed = subprocess.CompletedProcess(["git"], returncode, stdout=stdout, stderr=b"")
    monkeypatch.setattr(gate.subprocess, "run", lambda *_args, **_kwargs: completed)

    assert gate.git_records("diff", "--name-status", "-z", cwd=tmp_path) == records
