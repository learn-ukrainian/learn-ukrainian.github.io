"""Kimi seats admit neutral coding only: refusal classes and the allowed dispatch."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from scripts.agent_runtime import kimi_admission
from scripts.fleet_comms.endpoints import load_endpoint_registry
from scripts.fleet_comms.request_executor import RequestExecutor

_REPO_ROOT = Path(__file__).resolve().parent.parent
_NEUTRAL_OWNED = ("scripts/agent_runtime/kimi_admission.py", "tests/test_kimi_neutral_coding_admission.py")


def _refusal(**overrides):
    kwargs = {
        "agent": "kimi",
        "mode": "workspace-write",
        "repo_root": _REPO_ROOT,
        "owned_paths": _NEUTRAL_OWNED,
        "repo_role": "public-monorepo",
    }
    kwargs.update(overrides)
    return kimi_admission.neutral_coding_refusal(**kwargs)


# --- allowed -----------------------------------------------------------------


@pytest.mark.parametrize("agent", ["kimi", "kimicc"])
def test_neutral_coding_in_scripts_and_tests_is_admitted(agent):
    assert _refusal(agent=agent) is None
    assert _refusal(agent=agent, owned_paths=()) is None
    assert _refusal(agent=agent, owned_paths=("site/src/components/Card.astro", ".github/workflows/ci.yml")) is None
    assert _refusal(agent=agent, owned_paths=(".dagger/src/main.py", "./scripts/x.py")) is None


@pytest.mark.parametrize("agent", ["claude", "codex", "grok", "agy", "cursor"])
def test_other_seats_are_untouched(agent):
    assert _refusal(agent=agent, mode="read-only", review_profile="code", owned_paths=("docs/x.md",)) is None


@pytest.mark.parametrize(
    ("agent", "model"),
    [
        ("kimi", None),
        ("kimicc", None),
        ("acpx-kimi-shadow", None),
        ("codex", "kimi-code/k3"),
        ("x", "kimi-k3-max"),
        ("x", "k3"),
    ],
)
def test_every_kimi_seat_and_model_id_is_recognised(agent, model):
    assert kimi_admission.is_kimi_seat(agent, model=model)


def test_non_kimi_models_are_not_kimi_seats():
    assert not kimi_admission.is_kimi_seat("codex", model="gpt-6-sol")
    assert not kimi_admission.is_kimi_seat("cursor", model="composer-2.5")


# --- refused classes -----------------------------------------------------------


@pytest.mark.parametrize("mode", ["read-only", "danger"])
def test_non_workspace_write_modes_are_refused(mode):
    message = _refusal(mode=mode)
    assert message and f"--mode {mode}" in message


@pytest.mark.parametrize(
    "flags",
    [
        {"require_review_verdict": True},
        {"review_profile": "code"},
        {"review_attempt": True},
        {"review": True},
    ],
)
def test_review_flags_are_refused(flags):
    message = _refusal(**flags)
    assert message and "review dispatches" in message


def test_language_lane_is_refused():
    message = _refusal(language_lane=True)
    assert message and "Ukrainian-language work" in message


@pytest.mark.parametrize("track", ["l2-uk-en", "l2-uk-direct", "core", "a1", "b2", "folk", "bio", "hramatka"])
def test_curriculum_research_tracks_are_refused(track):
    message = _refusal(research_track=track)
    assert message and "curriculum track" in message


def test_research_track_fails_closed_without_the_curriculum_manifest(tmp_path):
    message = _refusal(research_track="infra", repo_root=tmp_path)
    assert message and "cannot be proven neutral" in message
    assert _refusal(research_track="infra") is None


@pytest.mark.parametrize(
    "path",
    [
        "curriculum/l2-uk-en/a1/lesson.mdx",
        "wiki/topic.md",
        "data/sources.db",
        "registry/lexicon/x.yaml",
        "docs/best-practices/code-quality.md",
        "agents_extensions/shared/rules/model-assignment.md",
        "agents_extensions/shared/memory/MEMORY.md",
        "agents_extensions/shared/skills/content-review/SKILL.md",
        "CLAUDE.md",
        "AGENTS.md",
        "GEMINI.md",
        ".claude/settings.json",
        ".agent/state.json",
        ".codex/config.toml",
        "site/src/content/docs/a1/lesson.mdx",
        "scripts/.claude/x.py",
        "agents_extensions/claude/agents/x.md",
        "README.md",
        "/etc/passwd",
        "scripts/../docs/x.md",
    ],
)
def test_protected_and_non_code_owned_paths_are_refused(path):
    message = _refusal(owned_paths=("scripts/ok.py", path))
    assert message and "owned path" in message


@pytest.mark.parametrize(
    "prompt_file",
    ["/home/me/.claude/briefs/task.md", ".agent/handoff.md", "repo/.codex/prompt.md"],
)
def test_prompt_file_in_private_state_is_refused(prompt_file):
    message = _refusal(prompt_file=prompt_file)
    assert message and "agent-private state" in message


@pytest.mark.parametrize(("key", "role"), [("infra-private", "private-infra"), ("hramatka", "private-product")])
def test_private_repositories_are_refused(key, role):
    message = _refusal(repo_key=key, repo_role=role)
    assert message and f"--repo {key!r} is a private repository" in message


def test_refusal_names_the_alternative_seats_and_every_reason():
    message = _refusal(mode="read-only", require_review_verdict=True, owned_paths=("docs/x.md",))
    assert message.startswith("ROUTING REFUSED: KIMI NEUTRAL-CODING-ONLY")
    assert "claude, codex, or grok" in message
    assert "--mode read-only" in message and "review dispatches" in message and "docs/x.md" in message


# --- delegate dispatch admission --------------------------------------------------


def _dispatch(*extra: str) -> list[str]:
    return [
        "dispatch",
        "--agent",
        "kimi",
        "--task-id",
        "kimi-admission-fixture",
        "--prompt",
        "Implement the fix.",
        *extra,
    ]


@pytest.fixture
def no_spawn(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.delenv("LU_DISPATCH_CHECK_BUDGET", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)

    def refuse(*_args, **_kwargs):
        raise AssertionError("a refused Kimi dispatch reached a side effect")

    monkeypatch.setattr(delegate.subprocess, "Popen", refuse)
    monkeypatch.setattr(delegate.subprocess, "run", refuse)
    monkeypatch.setattr(delegate, "_run_dor_preflight", refuse)
    return tasks


@pytest.mark.parametrize(
    ("argv", "reason"),
    [
        (_dispatch(), "--mode read-only"),
        (_dispatch("--mode", "danger", "--worktree"), "--mode danger"),
        (_dispatch("--harness", "kimicc", "--require-review-verdict"), "review dispatches"),
        (_dispatch("--mode", "workspace-write", "--worktree", "--review-profile", "code"), "review dispatches"),
        (_dispatch("--mode", "workspace-write", "--worktree", "--language-lane"), "Ukrainian-language work"),
        (
            _dispatch("--mode", "workspace-write", "--worktree", "--research-track", "l2-uk-en"),
            "Ukrainian-language work",
        ),
        (_dispatch("--mode", "workspace-write", "--worktree", "--research-track", "core"), "curriculum track"),
        (
            _dispatch(
                "--mode", "workspace-write", "--worktree", "--research-owned-path", "curriculum/l2-uk-en/a1/x.mdx"
            ),
            "Ukrainian-language work",
        ),
        (
            _dispatch("--mode", "workspace-write", "--worktree", "--research-owned-path", "wiki/x.md"),
            "protected 'wiki/'",
        ),
        (
            _dispatch("--mode", "workspace-write", "--worktree", "--research-owned-path", "docs/x.md"),
            "protected 'docs/'",
        ),
        (
            _dispatch(
                "--mode",
                "workspace-write",
                "--worktree",
                "--research-owned-path",
                "agents_extensions/shared/rules/x.md",
            ),
            "protected 'agents_extensions/shared/rules/'",
        ),
        (
            _dispatch("--mode", "workspace-write", "--worktree", "--research-owned-path", "CLAUDE.md"),
            "agent instruction file",
        ),
        (_dispatch("--mode", "workspace-write", "--worktree", "--repo", "infra-private"), "private repository"),
        (_dispatch("--mode", "workspace-write", "--worktree", "--repo", "hramatka"), "private repository"),
    ],
)
def test_dispatch_refuses_before_any_side_effect(no_spawn, capsys, argv, reason):
    rc = delegate.main(argv)
    err = capsys.readouterr().err
    assert rc == 2, err
    assert "KIMI NEUTRAL-CODING-ONLY" in err
    assert reason in err
    assert not no_spawn.exists() or not any(no_spawn.iterdir())


def test_dispatch_refuses_a_private_state_prompt_file(no_spawn, capsys, tmp_path):
    prompt = tmp_path / ".claude" / "brief.md"
    prompt.parent.mkdir()
    prompt.write_text("Implement the fix.\n", encoding="utf-8")
    argv = ["dispatch", "--agent", "kimi", "--task-id", "kimi-admission-fixture", "--prompt-file", str(prompt)]
    rc = delegate.main([*argv, "--mode", "workspace-write", "--worktree"])
    err = capsys.readouterr().err
    assert rc == 2
    assert "agent-private state" in err


class _AdmittedSentinel(Exception):
    pass


def test_neutral_coding_dispatch_in_scripts_and_tests_passes_admission(tmp_path, monkeypatch):
    """The allowed class clears both admission checks and reaches the capacity hint."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.delenv("LU_DISPATCH_CHECK_BUDGET", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.setattr(delegate, "_run_dor_preflight", lambda *_a, **_k: (None, None))
    seen: list[str] = []

    def reached(agent, **_kwargs):
        seen.append(agent)
        raise _AdmittedSentinel

    monkeypatch.setattr(delegate, "_check_capacity_hint", reached)
    argv = _dispatch(
        "--mode",
        "workspace-write",
        "--worktree",
        "--research-role",
        "harness",
        "--research-owned-path",
        "scripts/agent_runtime/kimi_admission.py",
        "--research-owned-path",
        "tests/test_kimi_neutral_coding_admission.py",
    )
    with pytest.raises(_AdmittedSentinel):
        delegate.main(argv)
    assert seen == ["kimi"]


# --- capacity hint -----------------------------------------------------------------


def _busy_codex(tmp_path, monkeypatch):
    import json

    tasks = tmp_path / "tasks"
    tasks.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setattr(delegate, "_pid_alive", lambda _pid: True)
    (tasks / "busy.json").write_text(
        json.dumps({"task_id": "busy", "agent": "codex", "status": "running", "pid": 99999}), encoding="utf-8"
    )


def test_capacity_hint_never_suggests_kimi_for_non_coding_work(tmp_path, monkeypatch, capsys):
    _busy_codex(tmp_path, monkeypatch)
    review = types.SimpleNamespace(json=False, quiet=False, mode="read-only", require_review_verdict=True)
    delegate._check_capacity_hint("codex", args=review)
    err = capsys.readouterr().err
    assert "idle capacity is available in:" in err
    assert "kimi" not in err.split("available in:", 1)[1]


def test_capacity_hint_suggests_kimi_for_neutral_coding(tmp_path, monkeypatch, capsys):
    _busy_codex(tmp_path, monkeypatch)
    coding = types.SimpleNamespace(
        json=False, quiet=False, mode="workspace-write", research_owned_path=["scripts/x.py"]
    )
    delegate._check_capacity_hint("codex", args=coding)
    assert "kimi" in capsys.readouterr().err.split("available in:", 1)[1]


# --- fleet comms --------------------------------------------------------------------


def test_fleet_request_to_kimi_is_refused_before_any_insert(tmp_path):
    executor = RequestExecutor.__new__(RequestExecutor)
    executor.registry = load_endpoint_registry()
    with pytest.raises(ValueError, match="KIMI NEUTRAL-CODING-ONLY"):
        executor.create_request(recipient="kimi", body="Consult on this design.")
