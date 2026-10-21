"""A Codex read-only review's worker holds its test slots outside the sandbox (#11230, #10744).

The worker queues in the host pool, holds ``review`` slots while the CLI runs, hands the CLI the holder marker
and gives the slots back once the runtime returns. Other routes keep taking their own slots, and a dispatched
worker never inherits its dispatcher's marker.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from scripts.common import test_slots

REPO_ROOT = Path(__file__).resolve().parent.parent
TASK = "review-11230-worker-fixture"


@pytest.fixture(autouse=True)
def pool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "pool"
    monkeypatch.setenv(test_slots.ENABLE_ENV, "on")
    monkeypatch.setenv(test_slots.DIR_ENV, str(path))
    monkeypatch.setenv(test_slots.COUNT_ENV, "4")
    monkeypatch.setenv(test_slots.WAIT_ENV, "5")
    monkeypatch.delenv(test_slots.HOLDER_ENV, raising=False)
    monkeypatch.delenv(test_slots.SESSION_ENV, raising=False)
    monkeypatch.delenv("CI", raising=False)
    return path


def _hold(**overrides: object) -> tuple[test_slots.Hold | None, dict[str, object] | None]:
    arguments: dict[str, object] = {
        "agent": "codex",
        "mode": "read-only",
        "review_typed": True,
        "sealed_attempt": False,
        "task_id": TASK,
    }
    arguments.update(overrides)
    return delegate._hold_review_test_slots(**arguments)  # type: ignore[arg-type]


def test_a_codex_read_only_review_holds_review_slots_for_its_task() -> None:
    hold, record = _hold()
    try:
        assert hold is not None and record == {"outcome": "held", "slots": 2, "waited_s": record["waited_s"]}
        holders = test_slots.status()["holders"]
        assert [(entry["task_id"], entry["kind"], entry["slots"]) for entry in holders] == [(TASK, "review", 2)]
        env = {**os.environ, **hold.environment(), test_slots.TASK_ENV: TASK}
        assert test_slots.inherited_hold(env) == delegate.REVIEW_TEST_SLOTS
    finally:
        if hold is not None:
            hold.release()
    assert test_slots.status()["slots_in_use"] == 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"agent": "claude"},
        {"agent": "agy"},
        {"mode": "workspace-write"},
        {"review_typed": False},
        {"sealed_attempt": True},
    ],
    ids=["claude", "agy", "workspace-write", "not-a-review", "sealed-attempt"],
)
def test_every_other_route_takes_its_own_slots_or_none(pool: Path, overrides: dict[str, object]) -> None:
    """No double counting: a seat that can prepare the pool, or runs no tests, holds nothing up front."""
    assert _hold(**overrides) == (None, None)
    assert not pool.exists()


def test_a_disabled_pool_holds_nothing(monkeypatch: pytest.MonkeyPatch, pool: Path) -> None:
    monkeypatch.setenv(test_slots.ENABLE_ENV, "off")
    assert _hold() == (None, {"outcome": "disabled"})
    assert not pool.exists()


def test_a_refused_hold_is_recorded_and_the_review_runs_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    shared = tmp_path / "shared"
    shared.mkdir(mode=0o777)
    shared.chmod(0o777)  # another user could redirect a pool below it
    monkeypatch.setenv(test_slots.DIR_ENV, str(shared / "pool"))

    assert _hold() == (None, {"outcome": "refused", "reason": "pool_unavailable"})
    assert "review test slots refused" in capsys.readouterr().err
    assert not (shared / "pool").exists()


def test_a_dispatched_worker_never_inherits_its_dispatchers_marker() -> None:
    base = {**os.environ, test_slots.HOLDER_ENV: "2:/elsewhere/holders/x.ticket", test_slots.SESSION_ENV: "/s"}
    env = delegate._build_worker_env(task_id=TASK, dispatch_agent="codex", base_env=base)
    assert test_slots.HOLDER_ENV not in env and test_slots.SESSION_ENV not in env


# ---- the worker -----------------------------------------------------------------------------------------------


def _git_checkout(path: Path) -> Path:
    env = {key: value for key, value in os.environ.items() if not key.startswith(("GIT_", "PRE_COMMIT"))}
    path.mkdir()
    for args in (("init", "-q", "-b", "main"), ("config", "user.email", "t@example.com"), ("config", "user.name", "t")):
        subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, env=env, timeout=30)
    (path / "README.md").write_text("fixture\n", encoding="utf-8")
    for args in (("add", "-A"), ("commit", "-qm", "fixture")):
        subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, env=env, timeout=30)
    return path


def _sandbox() -> list[str]:
    """Codex's view where available (unmapped root, read-only), else none: the marker must work either way."""
    prefix = ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--unshare-user", "--unshare-pid"]
    try:
        probe = subprocess.run([*prefix, "true"], capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [*prefix, "--die-with-parent"] if probe.returncode == 0 else []


@pytest.mark.parametrize("outcome", ["returns", "raises"])
def test_the_worker_holds_review_slots_for_the_cli_and_returns_them_after(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcome: str
) -> None:
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    (tmp_path / "tasks").mkdir()
    monkeypatch.setenv(test_slots.TASK_ENV, TASK)  # the worker's own identity, as dispatch exports it
    checkout = _git_checkout(tmp_path / "checkout")
    state_path = delegate._state_path(TASK)
    delegate._write_state_atomic(
        state_path,
        {"task_id": TASK, "cwd": str(checkout), "mode": "read-only", "review_profile": "code", "cli_version": "x"},
    )
    seen: dict[str, object] = {}
    governed = [
        *_sandbox(),
        sys.executable,
        "-m",
        "scripts.common.test_slots",
        "run",
        "--slots",
        "1",
        "--",
        sys.executable,
        "-c",
        "print('reviewer test ran')",
    ]

    def runtime(*_args: object, **_kwargs: object) -> object:
        seen["marker"] = os.environ.get(test_slots.HOLDER_ENV)
        seen["holders"] = [(h["task_id"], h["kind"], h["slots"]) for h in test_slots.status()["holders"]]
        env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        seen["run"] = subprocess.run(governed, cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=60)
        if outcome == "raises":
            raise RuntimeError("the CLI crashed")
        return type(
            "_Result",
            (),
            {
                "ok": True,
                "response": "VERDICT: APPROVE",
                "stderr_excerpt": None,
                "returncode": 0,
                "rate_limited": False,
            },
        )()

    with patch("agent_runtime.runner.invoke", side_effect=runtime):
        delegate._run_worker(
            task_id=TASK,
            agent="codex",
            prompt="Review the diff; run its tests.",
            mode="read-only",
            cwd_str=str(checkout),
            model="gpt-6.1-sol",
            hard_timeout=60,
        )

    run = seen["run"]
    assert isinstance(run, subprocess.CompletedProcess)
    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == "reviewer test ran"
    assert isinstance(seen["marker"], str) and seen["marker"].startswith(f"{delegate.REVIEW_TEST_SLOTS}:")
    assert seen["holders"] == [(TASK, "review", delegate.REVIEW_TEST_SLOTS)]
    assert test_slots.HOLDER_ENV not in os.environ
    assert test_slots.status()["holders"] == []
    state = delegate._read_state(state_path)
    assert state is not None and state["review_test_slots"]["outcome"] == "held"
