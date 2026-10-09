"""Behavior tests for the pre-push gate (#10033): refuse red, accept green, bounded, no stale receipts."""

from __future__ import annotations

import fcntl
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from tests.helpers.python import project_python

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
def repo(tmp_path: Path) -> Path:
    """A repository whose base commit is already on the remote ``main``."""
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
    _write(root, ".pre-commit-config.yaml", PRE_COMMIT)
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
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _receipts(repo: Path) -> list[Path]:
    return sorted((repo / ".git/lu-pre-push-gate/receipts").glob("*.json"))


# ---- each push path refuses red and accepts green -------------------------------------------------------


def test_green_changed_test_is_accepted_and_leaves_a_receipt(repo: Path) -> None:
    _write(repo, "tests/test_new.py", GREEN_TEST)
    _commit(repo, "green", "tests/test_new.py")

    result = _run_gate(repo)

    assert result.returncode == 0, result.stderr
    assert len(_receipts(repo)) == 1
    assert _measurements(repo)[-1]["outcome"] == "green"


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

    assert _run_gate(repo).returncode == 0

    assert _measurements(repo)[-1]["detail"] == "valid receipt"


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


@pytest.mark.parametrize(
    "field,value",
    [
        ("tree", "d" * 40),
        ("base", "e" * 40),
        ("registry_version", "v1-y"),
        ("changed_tests", ("tests/test_b.py", "tests/test_c.py")),
        ("registry_nodes", ("tests/test_z.py",)),
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
    assert _receipts(repo) == []


def test_environment_can_shorten_but_never_lengthen_a_bound(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_BOUND", "99999")
    assert gate.bounded("X_BOUND", 600.0) == 600.0
    monkeypatch.setenv("X_BOUND", "5")
    assert gate.bounded("X_BOUND", 600.0) == 5.0
    monkeypatch.setenv("X_BOUND", "nonsense")
    assert gate.bounded("X_BOUND", 600.0) == 600.0
    assert gate.MAX_TEST_PROCESSES == 2


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

    expected = gate.dedupe_node_ids([*marker.KNOWN_REPO_WIDE_MODULES, *marker.KNOWN_REPO_WIDE_FUNCTIONS])
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


def test_auto_finalize_push_timeout_covers_the_gate_bounds() -> None:
    from scripts import delegate

    gate_worst_case = gate.ADMISSION_WAIT_S + gate.RUN_BUDGET_S + gate.SHADOW_BUDGET_S
    assert gate_worst_case + delegate.DEFAULT_NETWORK_GIT_TIMEOUT_S <= delegate.AUTO_FINALIZE_PUSH_TIMEOUT_S


def test_worker_closeout_text_carries_the_gate_and_merge_main_rules() -> None:
    from scripts import delegate

    source = Path(delegate.__file__).read_text(encoding="utf-8")
    assert "validation_incomplete" in source and "git merge-tree" in source
