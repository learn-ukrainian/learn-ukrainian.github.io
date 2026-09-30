"""#9275: a bounded worker is dispatched only with a complete, bound advisory envelope.

Operator decision 2026-09-30: every ``gpt-6-luna`` dispatch, and every Gemini
Flash dispatch without an explicit Ukrainian authoring/review classification,
needs an envelope issued by a finished ``gpt-6.1-sol`` advisory task and bound
to this dispatch's arguments. Test names carry the frozen acceptance-matrix row
(M1–M18) they prove.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from scripts.agent_runtime import bounded_advisory

REPO_ROOT = delegate._REPO_ROOT
WORKER_ID = "luna-worker"
ADVISOR_ID = "sol-advisor"
OWNED = "scripts/delegate.py"


class _Stdin:
    def __init__(self, sink: list[str]) -> None:
        self._sink = sink

    def write(self, data: bytes) -> None:
        self._sink.append(data.decode("utf-8"))

    def close(self) -> None:
        pass


class _Health:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Tasks in ``tmp_path``; worker spawns and the prompts they receive are recorded."""
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setenv("LU_ALLOW_NOTEBOOK_DISPATCH", "1")
    monkeypatch.delenv("LU_DISPATCH_CHECK_BUDGET", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    spawned: list[list[str]] = []
    prompts: list[str] = []

    real_popen = subprocess.Popen

    def fake_popen(command, *args, **kwargs):
        if not (isinstance(command, (list, tuple)) and "_worker" in command):
            return real_popen(command, *args, **kwargs)
        spawned.append(list(command))
        return type("_Proc", (), {"pid": 424242, "stdin": _Stdin(prompts)})()

    def health_only(url, *_args, **_kwargs):
        if "/api/health" in str(url):
            return _Health()
        raise AssertionError(f"unexpected urlopen {url}")

    monkeypatch.setattr(delegate.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(delegate.urllib.request, "urlopen", health_only)
    telemetry = type("_Telemetry", (), {"model": "fixture-model", "effort": "high", "cli_version": "fixture"})()
    monkeypatch.setattr("agent_runtime.telemetry.resolve_dispatch_start_telemetry", lambda **_kwargs: telemetry)
    return type("_Env", (), {"tasks": tasks, "spawned": spawned, "prompts": prompts})()


def _argv(*extra: str, agent: str = "codex", model: str | None = "gpt-6-luna", task_id: str = WORKER_ID) -> list[str]:
    argv = ["dispatch", "--agent", agent, "--task-id", task_id, "--prompt", "Map the parser flags."]
    if model is not None:
        argv += ["--model", model]
    if "--mode" not in extra:
        argv += ["--mode", "read-only", "--cwd", str(REPO_ROOT)]
    return argv + list(extra)


def _parse(argv: list[str]):
    return delegate.build_parser().parse_args(argv)


def _binding(argv: list[str]) -> str:
    return delegate.advisory_binding_sha256(_parse(argv))


def _envelope(binding: str, **overrides) -> dict:
    envelope = {
        "task_contract": "List every dispatch flag the parser defines, with its default.",
        "owned_paths": [OWNED],
        "max_changed_files": 2,
        "max_non_test_loc": 40,
        "constraints": ["read the parser only"],
        "risk_boundaries": ["no change to admission logic"],
        "acceptance_evidence": ["a table of flags and defaults"],
        "escalation_triggers": ["a flag whose default depends on the environment"],
        "dispatch_args_sha256": binding,
    }
    envelope.update(overrides)
    return envelope


def _result_text(envelope: dict) -> str:
    return f"Advice follows.\n\n```advisory-envelope\n{json.dumps(envelope, indent=2)}\n```\n"


def _write_advisor(
    tasks: Path,
    binding: str,
    *,
    task_id: str = ADVISOR_ID,
    result: str | None = None,
    envelope: dict | None = None,
    **record_overrides,
) -> Path:
    tasks.mkdir(parents=True, exist_ok=True)
    result_path = tasks / f"{task_id}.result"
    result_path.write_text(result if result is not None else _result_text(envelope or _envelope(binding)))
    record = {
        "task_id": task_id,
        "run_nonce": "advisor-nonce",
        "agent": "codex",
        "model": "gpt-6.1-sol",
        "mode": "read-only",
        "status": "done",
        "result_file": str(result_path),
        "advisory_role": "bounded_advisory_envelope",
        "advisory_route": "execution_routing.sol_advised_bounded.advisor",
        "advisory_binding_sha256": binding,
    }
    record.update(record_overrides)
    (tasks / f"{task_id}.json").write_text(json.dumps(record))
    return result_path


def _dispatch(argv: list[str]) -> int:
    return delegate.cmd_dispatch(_parse(argv))


def _worker_record(tasks: Path, task_id: str = WORKER_ID) -> dict | None:
    path = tasks / f"{task_id}.json"
    return json.loads(path.read_text()) if path.exists() else None


def _assert_refused(env, capsys, rc: int, code: str, task_id: str = WORKER_ID) -> None:
    err = capsys.readouterr().err
    assert rc == 2, err
    assert code in err, err
    assert env.spawned == []
    assert _worker_record(env.tasks, task_id) is None


def _admitted_luna(env, *extra: str) -> list[str]:
    argv = _argv("--owned-path", OWNED, *extra)
    _write_advisor(env.tasks, _binding(argv))
    return [*argv, "--advisory-task", ADVISOR_ID]


# --- M1 -------------------------------------------------------------------


def test_m1_luna_without_advisory_task_is_refused_before_any_record(env, capsys):
    rc = _dispatch(_argv("--owned-path", OWNED))
    _assert_refused(env, capsys, rc, bounded_advisory.ENVELOPE_REQUIRED)


def test_m1_write_mode_luna_without_advisory_task_creates_no_worktree(env, capsys):
    rc = _dispatch(_argv("--mode", "workspace-write", "--worktree", "--owned-path", OWNED))
    _assert_refused(env, capsys, rc, bounded_advisory.ENVELOPE_REQUIRED)
    assert not (REPO_ROOT / ".worktrees" / "dispatch" / "codex" / WORKER_ID).exists()


# --- M2 -------------------------------------------------------------------


@pytest.mark.parametrize("status", ["failed", "cancelled", "running", "timeout", "needs_finalize"])
def test_m2_advisory_task_not_done_is_refused(env, capsys, status):
    argv = _argv("--owned-path", OWNED)
    _write_advisor(env.tasks, _binding(argv), status=status)
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, bounded_advisory.TASK_NOT_DONE)


def test_m2_missing_advisory_task_is_refused(env, capsys):
    rc = _dispatch(_argv("--owned-path", OWNED, "--advisory-task", "no-such-task"))
    _assert_refused(env, capsys, rc, bounded_advisory.TASK_NOT_FOUND)


# --- M3 -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"model": "gpt-6-luna"}, bounded_advisory.TASK_WRONG_MODEL),
        ({"model": "claude-opus-5-5", "agent": "claude"}, bounded_advisory.TASK_WRONG_MODEL),
        ({"model": None}, bounded_advisory.TASK_WRONG_MODEL),
        ({"resolved_model_known": False}, bounded_advisory.TASK_WRONG_MODEL),
        ({"advisory_role": "consequential_advisory"}, bounded_advisory.TASK_WRONG_ROLE),
        ({"advisory_route": "execution_routing.other"}, bounded_advisory.TASK_WRONG_ROLE),
        ({"mode": "workspace-write"}, bounded_advisory.TASK_WRONG_ROLE),
    ],
)
def test_m3_advisory_task_on_wrong_model_role_or_route_is_refused(env, capsys, overrides, code):
    argv = _argv("--owned-path", OWNED)
    _write_advisor(env.tasks, _binding(argv), **overrides)
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, code)


# --- M4 -------------------------------------------------------------------


def test_m4_unrelated_sol_task_is_refused(env, capsys):
    argv = _argv("--owned-path", OWNED)
    _write_advisor(
        env.tasks,
        _binding(argv),
        result="Here is my review. VERDICT: APPROVE\n",
        advisory_role=None,
        advisory_route=None,
        advisory_binding_sha256=None,
    )
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, bounded_advisory.TASK_WRONG_ROLE)


def test_m4_advisor_result_without_envelope_is_refused(env, capsys):
    argv = _argv("--owned-path", OWNED)
    _write_advisor(env.tasks, _binding(argv), result="I think the worker should be careful.\n")
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, bounded_advisory.ENVELOPE_MISSING)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda e: e.pop("acceptance_evidence"),
        lambda e: e.update(acceptance_evidence=[]),
        lambda e: e.update(escalation_triggers=[" "]),
        lambda e: e.update(task_contract=""),
        lambda e: e.update(constraints="read only"),
        lambda e: e.update(extra_field="x"),
        lambda e: e.pop("dispatch_args_sha256"),
    ],
    ids=["missing", "empty-list", "blank-item", "empty-contract", "untyped", "extra", "no-binding"],
)
def test_m4_incomplete_envelope_is_refused(env, capsys, mutate):
    argv = _argv("--owned-path", OWNED)
    envelope = _envelope(_binding(argv))
    mutate(envelope)
    _write_advisor(env.tasks, _binding(argv), envelope=envelope)
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, bounded_advisory.ENVELOPE_INCOMPLETE)


def test_m4_two_envelopes_in_one_result_are_refused(env, capsys):
    argv = _argv("--owned-path", OWNED)
    text = _result_text(_envelope(_binding(argv)))
    _write_advisor(env.tasks, _binding(argv), result=text + text)
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, bounded_advisory.ENVELOPE_MISSING)


def test_m4_forged_result_file_outside_the_canonical_result_is_refused(env, capsys, tmp_path):
    argv = _argv("--owned-path", OWNED)
    forged = tmp_path / "forged-envelope.md"
    forged.write_text(_result_text(_envelope(_binding(argv))))
    _write_advisor(env.tasks, _binding(argv), result="no envelope here\n", result_file=str(forged))
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, bounded_advisory.RESULT_UNREADABLE)


def test_m4_there_is_no_free_envelope_file_flag():
    with pytest.raises(SystemExit):
        _parse(_argv("--advisory-envelope", "envelope.json"))


# --- M5 -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"max_changed_files": 0}, bounded_advisory.ENVELOPE_INCOMPLETE),
        ({"max_changed_files": -3}, bounded_advisory.ENVELOPE_INCOMPLETE),
        ({"max_non_test_loc": 0}, bounded_advisory.ENVELOPE_INCOMPLETE),
        ({"max_non_test_loc": "40"}, bounded_advisory.ENVELOPE_INCOMPLETE),
        ({"max_changed_files": True}, bounded_advisory.ENVELOPE_INCOMPLETE),
        ({"max_non_test_loc": 2.5}, bounded_advisory.ENVELOPE_INCOMPLETE),
        ({"owned_paths": ["/etc/passwd"]}, bounded_advisory.OWNED_PATHS_INVALID),
        ({"owned_paths": ["../outside"]}, bounded_advisory.OWNED_PATHS_INVALID),
        ({"owned_paths": ["scripts/../../outside"]}, bounded_advisory.OWNED_PATHS_INVALID),
        ({"owned_paths": [".git/config"]}, bounded_advisory.OWNED_PATHS_INVALID),
        ({"owned_paths": ["batch_state/tasks/x.json"]}, bounded_advisory.OWNED_PATHS_INVALID),
        ({"owned_paths": ["no-such-root/file.py"]}, bounded_advisory.OWNED_PATHS_INVALID),
        ({"owned_paths": ["**/*.py"]}, bounded_advisory.OWNED_PATHS_INVALID),
        ({"owned_paths": ["scripts/delegate.py/child"]}, bounded_advisory.OWNED_PATHS_INVALID),
        ({"owned_paths": ["scripts/‮delegate.py"]}, bounded_advisory.OWNED_PATHS_INVALID),
        ({"owned_paths": []}, bounded_advisory.ENVELOPE_INCOMPLETE),
    ],
)
def test_m5_non_positive_ceilings_or_owned_paths_outside_allowed_roots_are_refused(env, capsys, overrides, code):
    paths = overrides.get("owned_paths", [OWNED])
    extra: list[str] = []
    for path in paths:
        extra += ["--owned-path", path]
    argv = _argv(*extra)
    _write_advisor(env.tasks, _binding(argv), envelope=_envelope(_binding(argv), **overrides))
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, code)


def test_m5_creatable_owned_path_under_an_existing_root_is_admitted(env, capsys):
    new_path = "scripts/agent_runtime/new_bounded_helper.py"
    argv = _argv("--owned-path", new_path)
    _write_advisor(env.tasks, _binding(argv), envelope=_envelope(_binding(argv), owned_paths=[new_path]))
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    assert rc == 0, capsys.readouterr().err
    assert len(env.spawned) == 1


# --- M6 -------------------------------------------------------------------


@pytest.mark.parametrize(
    "changed",
    [
        ["--owned-path", "scripts/delegate.py", "--owned-path", "tests/test_delegate.py"],
        ["--owned-path", OWNED, "--research-task-family", "recon"],
        ["--owned-path", OWNED, "--effort", "max"],
        ["--owned-path", OWNED, "--hard-timeout", "99"],
    ],
    ids=["owned-paths", "scope", "effort", "timeout"],
)
def test_m6_envelope_bound_to_other_dispatch_arguments_is_refused(env, capsys, changed):
    issued_for = _argv("--owned-path", OWNED)
    _write_advisor(env.tasks, _binding(issued_for))
    rc = _dispatch([*_argv(*changed), "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, bounded_advisory.BINDING_MISMATCH)


def test_m6_mode_change_is_refused_before_any_worktree(env, capsys):
    issued_for = _argv("--owned-path", OWNED)
    _write_advisor(env.tasks, _binding(issued_for))
    argv = _argv("--mode", "workspace-write", "--worktree", "--owned-path", OWNED, "--advisory-task", ADVISOR_ID)
    rc = _dispatch(argv)
    _assert_refused(env, capsys, rc, bounded_advisory.BINDING_MISMATCH)
    assert not (REPO_ROOT / ".worktrees" / "dispatch" / "codex" / WORKER_ID).exists()


def test_m6_envelope_binding_field_differs_from_the_advisor_record(env, capsys):
    argv = _argv("--owned-path", OWNED)
    _write_advisor(env.tasks, _binding(argv), envelope=_envelope("0" * 64))
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, bounded_advisory.BINDING_MISMATCH)


def test_m6_owned_path_set_must_equal_the_envelope(env, capsys):
    argv = _argv("--owned-path", OWNED)
    envelope = _envelope(_binding(argv), owned_paths=[OWNED, "tests/test_delegate.py"])
    _write_advisor(env.tasks, _binding(argv), envelope=envelope)
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, bounded_advisory.OWNED_PATHS_MISMATCH)


def test_m6_print_advisory_binding_matches_and_has_no_effect(env, capsys):
    argv = _argv("--owned-path", OWNED)
    rc = _dispatch([*argv, "--print-advisory-binding"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert out == _binding(argv) == _binding([*argv, "--advisory-task", "any-advisor"])
    assert env.spawned == [] and not env.tasks.exists()


# --- M7 -------------------------------------------------------------------


@pytest.mark.parametrize(
    "tamper",
    [
        lambda result, record: result.write_text(result.read_text() + "\nappended after validation\n"),
        lambda result, record: record.write_text(json.dumps({**json.loads(record.read_text()), "status": "failed"})),
        lambda result, record: record.write_text(json.dumps({**json.loads(record.read_text()), "run_nonce": "rerun"})),
    ],
    ids=["result-modified", "record-not-done", "advisor-rerun"],
)
def test_m7_advisor_result_changed_after_validation_is_refused_before_spawn(env, capsys, monkeypatch, tamper):
    argv = _admitted_luna(env)
    real_admit = delegate._admit_advisory

    def admit_then_tamper(*args, **kwargs):
        admission = real_admit(*args, **kwargs)
        tamper(env.tasks / f"{ADVISOR_ID}.result", env.tasks / f"{ADVISOR_ID}.json")
        return admission

    monkeypatch.setattr(delegate, "_admit_advisory", admit_then_tamper)
    rc = _dispatch(argv)
    err = capsys.readouterr().err
    assert rc == 2, err
    assert "dispatch refused before spawn" in err
    assert env.spawned == []
    record = _worker_record(env.tasks)
    assert record is not None and record["status"] == "failed"
    assert record["failure_reason"] in {bounded_advisory.ENVELOPE_CHANGED, bounded_advisory.TASK_NOT_DONE}


# --- M8 -------------------------------------------------------------------


def _substitute_into(monkeypatch, agent: str, model: str | None) -> None:
    def guard(requested_agent, *, model_resolution=None, requested_model=None, **_kwargs):
        delegate._remember_agent_substitution(
            model_resolution,
            source="budget-guard",
            requested_agent=requested_agent,
            requested_model=requested_model,
            actual_agent=agent,
            actual_model=model,
            how="fixture",
        )
        return agent

    monkeypatch.setattr(delegate, "_resolve_agent_with_budget_guard", guard)


def test_m8_budget_substitution_from_sol_into_luna_without_envelope_is_refused(env, capsys, monkeypatch):
    _substitute_into(monkeypatch, "codex", "gpt-6-luna")
    rc = _dispatch(_argv("--check-budget", "--owned-path", OWNED, model="gpt-6.1-sol"))
    _assert_refused(env, capsys, rc, bounded_advisory.ENVELOPE_REQUIRED)


# --- M9 -------------------------------------------------------------------


@pytest.mark.parametrize("spelling", ["GPT-6-Luna", "gpt-6-luna-high", "openai/gpt-6-luna", "codex:gpt-6-luna"])
def test_m9_luna_alias_spellings_without_envelope_are_refused(env, capsys, spelling):
    rc = _dispatch(_argv("--owned-path", OWNED, model=spelling))
    _assert_refused(env, capsys, rc, bounded_advisory.ENVELOPE_REQUIRED)


def test_m9_force_agent_luna_without_envelope_is_refused(env, capsys):
    rc = _dispatch(_argv("--check-budget", "--force-agent", "--owned-path", OWNED))
    _assert_refused(env, capsys, rc, bounded_advisory.ENVELOPE_REQUIRED)


# --- M10 / M15 / M16 / M17: the Gemini Flash bounded fallback ---------------


def test_m10_write_mode_gemini_flash_without_classification_is_refused(env, capsys):
    rc = _dispatch(_argv("--mode", "workspace-write", "--worktree", "--owned-path", OWNED, agent="agy", model=None))
    _assert_refused(env, capsys, rc, bounded_advisory.ENVELOPE_REQUIRED)
    assert not (REPO_ROOT / ".worktrees" / "dispatch" / "agy" / WORKER_ID).exists()


def test_m15_read_only_gemini_flash_recon_without_envelope_is_refused(env, capsys):
    rc = _dispatch(_argv(agent="agy", model="gemini-3.8-flash-high"))
    _assert_refused(env, capsys, rc, bounded_advisory.ENVELOPE_REQUIRED)


@pytest.mark.parametrize(
    "extra",
    [
        ["--research-task-family", "ukrainian-authoring", "--review-profile", "code"],
        ["--research-task-family", "code-review", "--review-profile", "ukrainian"],
        ["--research-task-family", "ukrainian-review", "--research-owned-path", "scripts/delegate.py"],
        ["--research-task-family", "ukrainian-authoring", "--owned-path", "tests/test_delegate.py"],
        ["--research-task-family", "ukrainian-authoring", "--research-owned-path", ".github/workflows/ci.yml"],
        ["--research-task-family", "ukrainian-review", "--research-owned-path", "./scripts/delegate.py"],
    ],
    ids=[
        "ukr-family-code-profile",
        "code-family-ukr-profile",
        "ukr-family-code-research-path",
        "ukr-family-code-owned",
        "ukr-family-dot-github",
        "ukr-family-dot-slash-scripts",
    ],
)
def test_m16_gemini_flash_with_conflicting_classification_is_refused(env, capsys, extra):
    rc = _dispatch(_argv(*extra, agent="agy", model=None))
    err = capsys.readouterr().err
    assert rc == 2, err
    assert bounded_advisory.ENVELOPE_REQUIRED in err and "ambiguous classification" in err
    assert env.spawned == [] and _worker_record(env.tasks) is None


def test_m16_ukrainian_review_profile_in_write_mode_without_family_is_refused(env, capsys):
    rc = _dispatch(
        _argv("--mode", "workspace-write", "--worktree", "--review-profile", "ukrainian", agent="agy", model=None)
    )
    _assert_refused(env, capsys, rc, bounded_advisory.ENVELOPE_REQUIRED)


@pytest.mark.parametrize(
    ("agent", "model", "extra"),
    [
        ("gemini", None, []),
        ("agy", "gemini-3.8-flash", []),
        ("agy", "gemini-3.8-flash-low", []),
        ("agy", None, ["--check-budget", "--force-agent"]),
    ],
    ids=["retired-cli-alias", "model-alias", "model-alias-low", "force-agent"],
)
def test_m17_gemini_flash_via_alias_or_force_agent_without_envelope_is_refused(env, capsys, agent, model, extra):
    rc = _dispatch(_argv(*extra, agent=agent, model=model))
    _assert_refused(env, capsys, rc, bounded_advisory.ENVELOPE_REQUIRED)


def test_m17_substitution_into_gemini_flash_without_envelope_is_refused(env, capsys, monkeypatch):
    _substitute_into(monkeypatch, "agy", "gemini-3.8-flash-high")
    rc = _dispatch(_argv("--check-budget", agent="claude", model=None))
    _assert_refused(env, capsys, rc, bounded_advisory.ENVELOPE_REQUIRED)


# --- M11 / M18: admitted Gemini Flash dispatches ---------------------------


@pytest.mark.parametrize(
    "extra",
    [
        ["--research-task-family", "ukrainian-authoring"],
        ["--research-task-family", "ukrainian-review"],
        ["--review-profile", "ukrainian"],
        ["--research-task-family", "ukrainian-review", "--review-profile", "ukrainian"],
    ],
    ids=["authoring-family", "review-family", "ukrainian-review-profile", "family-and-profile"],
)
def test_m11_gemini_flash_with_ukrainian_classification_is_admitted_without_envelope(env, capsys, extra):
    rc = _dispatch(_argv(*extra, agent="agy", model=None))
    assert rc == 0, capsys.readouterr().err
    assert len(env.spawned) == 1
    assert "advisory_envelope" not in _worker_record(env.tasks)


def test_m11_write_mode_gemini_ukrainian_authoring_is_admitted(env, capsys):
    argv = _argv(
        "--mode",
        "workspace-write",
        "--worktree",
        "--dry-run",
        "--research-task-family",
        "ukrainian-authoring",
        agent="agy",
        model=None,
    )
    rc = _dispatch(argv)
    assert rc == 0, capsys.readouterr().err
    assert _worker_record(env.tasks)["status"] == "dry_run"


def test_m18_read_only_gemini_flash_recon_with_bound_envelope_is_admitted(env, capsys):
    argv = _argv("--owned-path", OWNED, agent="agy", model=None)
    _write_advisor(env.tasks, _binding(argv))
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    assert rc == 0, capsys.readouterr().err
    assert len(env.spawned) == 1
    assert _worker_record(env.tasks)["advisory_envelope"]["advisor_task_id"] == ADVISOR_ID


# --- M13 / M14 --------------------------------------------------------------


def test_m13_luna_with_complete_bound_envelope_is_admitted_and_recorded(env, capsys):
    argv = _admitted_luna(env)
    rc = _dispatch(argv)
    assert rc == 0, capsys.readouterr().err
    assert len(env.spawned) == 1
    record = _worker_record(env.tasks)
    result_path = env.tasks / f"{ADVISOR_ID}.result"
    envelope = record["advisory_envelope"]
    assert envelope["advisor_task_id"] == ADVISOR_ID
    assert envelope["advisor_model"] == "gpt-6.1-sol"
    assert envelope["result_path"] == str(result_path)
    assert envelope["result_sha256"] == __import__("hashlib").sha256(result_path.read_bytes()).hexdigest()
    assert envelope["dispatch_args_sha256"] == _binding(argv)
    assert (envelope["max_changed_files"], envelope["max_non_test_loc"]) == (2, 40)
    assert record["owned_paths"] == [OWNED]
    assert "advisory_envelope" in record["prompt_blocks"]
    (prompt,) = env.prompts
    assert "at most 2 changed files and at most 40 changed non-test lines" in prompt
    assert "List every dispatch flag the parser defines" in prompt


def test_m13_substitution_into_luna_with_bound_envelope_is_admitted(env, capsys, monkeypatch):
    _substitute_into(monkeypatch, "codex", "gpt-6-luna")
    argv = _argv("--check-budget", "--owned-path", OWNED, model="gpt-6.1-sol")
    _write_advisor(env.tasks, _binding(argv))
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    assert rc == 0, capsys.readouterr().err
    assert _worker_record(env.tasks)["advisory_envelope"]["requirement"] == "gpt-6-luna is the bounded worker"


@pytest.mark.parametrize(("agent", "model"), [("claude", "claude-opus-5-5"), ("codex", "gpt-6.1-sol"), ("codex", None)])
def test_m14_non_bounded_models_without_envelope_are_unaffected(env, capsys, agent, model):
    rc = _dispatch(_argv(agent=agent, model=model))
    assert rc == 0, capsys.readouterr().err
    assert len(env.spawned) == 1
    record = _worker_record(env.tasks)
    assert "advisory_envelope" not in record and "advisory_role" not in record
    assert "advisory_envelope" not in record["prompt_blocks"]


def test_m14_advisory_task_on_a_non_bounded_dispatch_is_refused(env, capsys):
    argv = _argv("--owned-path", OWNED, model="gpt-6.1-sol")
    _write_advisor(env.tasks, _binding(argv))
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, bounded_advisory.FLAG_CONFLICT)


# --- The advisor side --------------------------------------------------------


def test_advisor_dispatch_records_role_binding_and_output_contract(env, capsys):
    binding = _binding(_argv("--owned-path", OWNED))
    argv = _argv(
        "--advisory-role",
        "bounded_advisory_envelope",
        "--advisory-binding",
        binding,
        model="gpt-6.1-sol",
        task_id=ADVISOR_ID,
    )
    rc = _dispatch(argv)
    assert rc == 0, capsys.readouterr().err
    record = _worker_record(env.tasks, ADVISOR_ID)
    assert record["advisory_role"] == "bounded_advisory_envelope"
    assert record["advisory_route"] == "execution_routing.sol_advised_bounded.advisor"
    assert record["advisory_binding_sha256"] == binding
    assert "advisory_contract" in record["prompt_blocks"]
    (prompt,) = env.prompts
    assert "```advisory-envelope" not in prompt and "`advisory-envelope`" in prompt
    assert binding in prompt


@pytest.mark.parametrize(
    ("extra", "model", "code"),
    [
        (
            ["--advisory-role", "bounded_advisory_envelope", "--advisory-binding", "a" * 64],
            "gpt-6-luna",
            "ADVISORY_ROLE_REFUSED",
        ),
        (["--advisory-role", "bounded_advisory_envelope"], "gpt-6.1-sol", bounded_advisory.FLAG_CONFLICT),
        (["--advisory-binding", "a" * 64], "gpt-6.1-sol", bounded_advisory.FLAG_CONFLICT),
        (
            ["--advisory-role", "bounded_advisory_envelope", "--advisory-binding", "XYZ"],
            "gpt-6.1-sol",
            bounded_advisory.FLAG_CONFLICT,
        ),
        (
            ["--advisory-role", "bounded_advisory_envelope", "--advisory-binding", "a" * 64, "--advisory-task", "x"],
            "gpt-6.1-sol",
            bounded_advisory.FLAG_CONFLICT,
        ),
    ],
    ids=["advisor-on-luna", "role-without-binding", "binding-without-role", "bad-binding", "role-and-task"],
)
def test_advisor_flags_are_refused_when_inconsistent(env, capsys, extra, model, code):
    rc = _dispatch(_argv(*extra, model=model, task_id=ADVISOR_ID))
    _assert_refused(env, capsys, rc, code, task_id=ADVISOR_ID)


def test_advisor_must_run_read_only(env, capsys):
    argv = _argv(
        "--mode",
        "workspace-write",
        "--worktree",
        "--advisory-role",
        "bounded_advisory_envelope",
        "--advisory-binding",
        "a" * 64,
        model="gpt-6.1-sol",
        task_id=ADVISOR_ID,
    )
    rc = _dispatch(argv)
    _assert_refused(env, capsys, rc, bounded_advisory.ADVISOR_ROUTE_REFUSED, task_id=ADVISOR_ID)


# --- M12 / M13 at finalize: the envelope ceilings ------------------------------


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, timeout=30)


def _bounded_worktree(tmp_path: Path, monkeypatch) -> Path:
    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)
    origin = tmp_path / "origin.git"
    worktree = tmp_path / "worktree"
    _git("init", "--bare", str(origin), cwd=tmp_path)
    _git("init", "--initial-branch=main", str(worktree), cwd=tmp_path)
    _git("config", "user.email", "test@example.com", cwd=worktree)
    _git("config", "user.name", "test", cwd=worktree)
    (worktree / "README.md").write_text("base\n")
    _git("add", "README.md", cwd=worktree)
    _git("commit", "-m", "base", cwd=worktree)
    _git("remote", "add", "origin", str(origin), cwd=worktree)
    _git("push", "-u", "origin", "main", cwd=worktree)
    _git("checkout", "-b", "codex/luna-worker", cwd=worktree)
    return worktree


def _commit_and_push(worktree: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = worktree / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    _git("add", "-A", cwd=worktree)
    _git("commit", "-m", "worker change", cwd=worktree)
    _git("push", "-u", "origin", "codex/luna-worker", cwd=worktree)


def _run_bounded_worker(tmp_path, monkeypatch, files: dict[str, str]) -> dict:
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    worktree = _bounded_worktree(tmp_path, monkeypatch)
    _commit_and_push(worktree, files)
    state_path = delegate._state_path(WORKER_ID)
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": WORKER_ID,
            "worktree_path": str(worktree),
            "worktree_branch": "codex/luna-worker",
            "worktree_base": "main",
            "owned_paths": ["src/"],
            "advisory_envelope": {"max_changed_files": 2, "max_non_test_loc": 10, "advisor_task_id": ADVISOR_ID},
        },
    )
    result = type(
        "_Result",
        (),
        {
            "ok": True,
            "response": "Committed and pushed the change.",
            "stderr_excerpt": None,
            "returncode": 0,
            "rate_limited": False,
            "model": "gpt-6-luna",
            "effort": "high",
            "cli_version": "fixture",
        },
    )()
    monkeypatch.setattr("agent_runtime.runner.invoke", lambda *_a, **_k: result)
    monkeypatch.setattr(delegate, "_background_jobs_at_exit", lambda *_a, **_k: None)
    monkeypatch.setattr(delegate, "_emit_terminal_dispatch_event", lambda **_kwargs: None)
    delegate._run_worker(
        task_id=WORKER_ID,
        agent="codex",
        prompt="bounded work",
        mode="workspace-write",
        cwd_str=str(worktree),
        model="gpt-6-luna",
        hard_timeout=60,
        keep_worktree=True,
    )
    return delegate._read_state(state_path)


def test_m12_worker_exceeding_envelope_ceilings_is_a_typed_failure(tmp_path, monkeypatch):
    state = _run_bounded_worker(
        tmp_path,
        monkeypatch,
        {"src/a.py": "x = 1\n" * 8, "src/b.py": "y = 2\n" * 8, "tests/test_a.py": "assert True\n" * 50},
    )
    assert state["status"] == "failed"
    assert state["failure_reason"] == bounded_advisory.CEILING_EXCEEDED
    check = state["advisory_ceiling_check"]
    assert (check["changed_files"], check["non_test_loc"]) == (3, 16)
    assert check["exceeded"] == [
        "changed_files 3 > max_changed_files 2",
        "non_test_loc 16 > max_non_test_loc 10",
    ]
    assert state["last_error"].startswith(bounded_advisory.CEILING_EXCEEDED)


def test_m13_worker_within_envelope_ceilings_settles_done(tmp_path, monkeypatch):
    state = _run_bounded_worker(tmp_path, monkeypatch, {"src/a.py": "x = 1\n" * 4, "tests/test_a.py": "ok\n" * 90})
    assert state["status"] == "done", state.get("last_error")
    assert state["advisory_ceiling_check"]["exceeded"] == []
    assert state["advisory_ceiling_check"]["non_test_loc"] == 4


def test_m12_unmeasurable_ceilings_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(delegate, "_worktree_diff_output", lambda *_a, **_k: None)
    state = _run_bounded_worker(tmp_path, monkeypatch, {"src/a.py": "x = 1\n"})
    assert state["status"] == "failed"
    assert state["failure_reason"] == bounded_advisory.CEILING_UNMEASURED


# --- Pure helpers --------------------------------------------------------------


def test_numstat_parser_and_test_path_classifier():
    entries = bounded_advisory.parse_numstat_z("3\t1\tsrc/a.py\x00-\t-\timg.png\x0010\t0\ttests/test_a.py\x00")
    assert entries == [(3, 1, "src/a.py"), (None, None, "img.png"), (10, 0, "tests/test_a.py")]
    verdict = bounded_advisory.ceiling_verdict(entries, max_changed_files=3, max_non_test_loc=4)
    assert (verdict["changed_files"], verdict["non_test_loc"], verdict["exceeded"]) == (3, 4, [])
    assert bounded_advisory.is_test_path("scripts/x/test_y.py")
    assert bounded_advisory.is_test_path("pkg/conftest.py")
    assert bounded_advisory.is_test_path("site/foo_test.ts")
    assert not bounded_advisory.is_test_path("scripts/testing_helpers.py")
    with pytest.raises(ValueError):
        bounded_advisory.parse_numstat_z("garbage\x00")


# --- M6: the binding covers the prompt text, not only the prompt path -------------


def _file_argv(prompt_file: Path) -> list[str]:
    argv = _argv("--owned-path", OWNED)
    index = argv.index("--prompt")
    return [*argv[:index], "--prompt-file", str(prompt_file), *argv[index + 2 :]]


def test_m6_prompt_file_edited_after_the_envelope_is_refused(env, capsys, tmp_path):
    prompt_file = tmp_path / "brief.md"
    prompt_file.write_text("Map the parser flags.\n")
    argv = _file_argv(prompt_file)
    _write_advisor(env.tasks, _binding(argv))
    prompt_file.write_text("Map the parser flags, then rewrite admission.\n")
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, bounded_advisory.BINDING_MISMATCH)


def test_m6_prompt_file_edited_between_admission_and_prompt_read_is_refused(env, capsys, monkeypatch, tmp_path):
    prompt_file = tmp_path / "brief.md"
    prompt_file.write_text("Map the parser flags.\n")
    argv = _file_argv(prompt_file)
    _write_advisor(env.tasks, _binding(argv))
    real_admit = delegate._admit_advisory

    def admit_then_edit(*args, **kwargs):
        admission = real_admit(*args, **kwargs)
        prompt_file.write_text("Something else entirely.\n")
        return admission

    monkeypatch.setattr(delegate, "_admit_advisory", admit_then_edit)
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    err = capsys.readouterr().err
    assert rc == 2 and "the prompt changed after advisory admission" in err, err
    assert env.spawned == [] and _worker_record(env.tasks) is None


def test_m6_prompt_file_envelope_is_admitted_and_binding_printed_by_content(env, capsys, tmp_path):
    prompt_file = tmp_path / "brief.md"
    prompt_file.write_text("Map the parser flags.\n")
    argv = _file_argv(prompt_file)
    assert _dispatch([*argv, "--print-advisory-binding"]) == 0
    printed = capsys.readouterr().out.strip()
    assert printed == _binding(argv)
    _write_advisor(env.tasks, printed)
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    assert rc == 0, capsys.readouterr().err
    assert len(env.spawned) == 1


def test_bounded_dispatch_with_a_stdin_prompt_is_refused(env, capsys):
    argv = _argv("--owned-path", OWNED)
    argv[argv.index("--prompt") + 1] = "-"
    _write_advisor(env.tasks, "0" * 64)
    rc = _dispatch([*argv, "--advisory-task", ADVISOR_ID])
    _assert_refused(env, capsys, rc, bounded_advisory.FLAG_CONFLICT)
