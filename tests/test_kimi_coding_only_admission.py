"""Kimi: web, UI and backend coding only — refusal classes, entry points, and the allowed dispatches."""

from __future__ import annotations

import json
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
_TOKEN = "KIMI CODING-ONLY"
_BACKEND_OWNED = ("scripts/agent_runtime/kimi_admission.py", "tests/test_kimi_coding_only_admission.py")
_UI_OWNED = ("site/src/components/Card.astro", "site/src/styles/global.css", "site/astro.config.mjs")


def _fail(*_args, **_kwargs):
    raise AssertionError("a refused Kimi call reached a side effect")


def _refusal(**overrides):
    kwargs = {
        "agent": "kimi",
        "mode": "workspace-write",
        "repo_root": _REPO_ROOT,
        "owned_paths": _BACKEND_OWNED,
        "repo_role": "public-monorepo",
    }
    kwargs.update(overrides)
    return kimi_admission.dispatch_refusal(**kwargs)


# --- allowed -----------------------------------------------------------------


@pytest.mark.parametrize("agent", ["kimi", "kimicc"])
@pytest.mark.parametrize(
    "owned",
    [
        _BACKEND_OWNED,
        _UI_OWNED,
        (),
        (
            "site/src/layouts/Base.astro",
            "site/src/pages/index.astro",
            "site/src/css/x.css",
            "site/src/assets/logo.svg",
            "site/src/lib/arc.ts",
            "site/src/lib/doc-nav.ts",
            "scripts/agent_runtime/runner.py",
            "site/tests/arc.test.ts",
            "site/e2e/nav.spec.ts",
            "site/vitest.config.ts",
        ),
        (".github/workflows/ci.yml", ".dagger/src/main.py", "./scripts/x.py", "scripts//x.py"),
    ],
)
def test_web_ui_and_backend_coding_is_admitted(agent, owned):
    assert _refusal(agent=agent, owned_paths=owned) is None


@pytest.mark.parametrize("agent", ["claude", "codex", "grok", "agy", "cursor"])
def test_other_seats_are_untouched(agent):
    assert _refusal(agent=agent, mode="read-only", review_profile="code", owned_paths=("docs/x.md",)) is None
    assert kimi_admission.runtime_refusal(agent, mode="read-only", tool_config={"review_id": "r"}) is None
    assert kimi_admission.acp_refusal(agent) is None


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
    assert message and "cannot be proven non-curriculum" in message
    assert _refusal(research_track="infra") is None


# Every protected family: Ukrainian-language content and data, rules and
# instruction files, agent-private state, locale files, and non-coding roots.
PROTECTED_PATHS = (
    "curriculum/l2-uk-en/a1/lesson.mdx",
    "wiki/topic.md",
    "data/sources.db",
    "registry/lexicon/x.yaml",
    "site/src/content/docs/a1/lesson.mdx",
    "site/src/data/words.json",
    "site/src/lexicon/entry.ts",
    "site/src/lib/i18n/chrome.ts",
    "site/src/lib/lexicon/x.ts",
    "site/src/lib/lexicon/adjective-mechanics.ts",
    "scripts/lexicon/x.py",
    "scripts/verification/stress.py",
    "scripts/practice/noun_mechanics_engine.py",
    "scripts/audit/checks/grammar.py",
    "scripts/pipeline/stress_annotator.py",
    "site/src/lib/vesum-form-key.ts",
    "scripts/i18n/uk.json",
    "site/src/components/locales/strings.json",
    "tests/fixtures/messages.po",
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
    "scripts/.claude/x.py",
    "site/public/robots.txt",
    "site/package.json",
    "agents_extensions/claude/agents/x.md",
    "README.md",
)


def test_every_ukrainian_code_family_is_refused_with_its_reason():
    for prefix, reason in kimi_admission.UKRAINIAN_CODE_FAMILIES.items():
        assert reason
        assert kimi_admission.protected_path_reason(f"{prefix}module.ts")


def test_the_repository_name_alone_does_not_mark_language_code():
    assert kimi_admission.protected_path_reason("scripts/launchd/com.learn-ukrainian.watcher.plist") is None


@pytest.mark.parametrize("path", PROTECTED_PATHS)
def test_protected_and_non_coding_owned_paths_are_refused(path):
    message = _refusal(owned_paths=("scripts/ok.py", path))
    assert message and "owned path" in message


@pytest.mark.parametrize(
    ("path", "canonical"),
    [
        ("site//src/content/docs/x.mdx", "site/src/content/docs/x.mdx"),
        ("./docs/../docs/x", "docs/x"),
        ("scripts/../docs/x.md", "docs/x.md"),
        ("site/src/pages/../content/x.mdx", "site/src/content/x.mdx"),
        ("site/src/components/../../src/lib/i18n/x.ts", "site/src/lib/i18n/x.ts"),
        ("scripts\\..\\CLAUDE.md", "CLAUDE.md"),
        ("Docs/x.md", "Docs/x.md"),
    ],
)
def test_paths_are_normalized_before_the_prefix_checks(path, canonical):
    assert kimi_admission.normalize_owned_path(path) == canonical
    message = _refusal(owned_paths=(path,))
    assert message and f"owned path {canonical!r}" in message


@pytest.mark.parametrize(
    "path", ["/etc/passwd", "/home/me/repo/scripts/x.py", "~/x.py", "C:/x.py", "../x.py", "scripts/../../x.py", ".", ""]
)
def test_absolute_and_escaping_paths_are_refused(path):
    assert kimi_admission.normalize_owned_path(path) is None
    message = _refusal(owned_paths=(path,))
    assert message and "is not a repository-relative path" in message


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


def test_refusal_states_the_policy_and_names_the_alternative_seats():
    message = _refusal(mode="read-only", require_review_verdict=True, owned_paths=("docs/x.md",))
    assert message.startswith(f"ROUTING REFUSED: {_TOKEN}")
    assert kimi_admission.POLICY_LINE in message
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


_WRITE = ("--mode", "workspace-write", "--worktree")


@pytest.fixture
def no_spawn(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.delenv("LU_DISPATCH_CHECK_BUDGET", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.setattr(delegate.subprocess, "Popen", _fail)
    monkeypatch.setattr(delegate.subprocess, "run", _fail)
    monkeypatch.setattr(delegate, "_run_dor_preflight", _fail)
    return tasks


def _assert_refused(no_spawn, capsys, argv, reason):
    rc = delegate.main(argv)
    err = capsys.readouterr().err
    assert rc == 2, err
    assert _TOKEN in err
    assert reason in err
    assert not no_spawn.exists() or not any(no_spawn.iterdir())


@pytest.mark.parametrize(
    ("argv", "reason"),
    [
        (_dispatch(), "--mode read-only"),
        (_dispatch("--mode", "danger", "--worktree"), "--mode danger"),
        (_dispatch("--harness", "kimicc", "--require-review-verdict"), "review dispatches"),
        (_dispatch(*_WRITE, "--review-profile", "code"), "review dispatches"),
        (_dispatch(*_WRITE, "--language-lane"), "Ukrainian-language work"),
        (_dispatch(*_WRITE, "--research-track", "l2-uk-en"), "Ukrainian-language work"),
        (_dispatch(*_WRITE, "--research-track", "core"), "curriculum track"),
        (_dispatch(*_WRITE, "--repo", "infra-private"), "private repository"),
        (_dispatch(*_WRITE, "--repo", "hramatka"), "private repository"),
    ],
)
def test_dispatch_refuses_before_any_side_effect(no_spawn, capsys, argv, reason):
    _assert_refused(no_spawn, capsys, argv, reason)


@pytest.mark.parametrize("flag", ["--owned-path", "--research-owned-path"])
@pytest.mark.parametrize("path", PROTECTED_PATHS)
def test_dispatch_refuses_every_protected_family_through_either_ownership_flag(no_spawn, capsys, flag, path):
    _assert_refused(no_spawn, capsys, _dispatch(*_WRITE, flag, "scripts/ok.py", flag, path), "owned path")


@pytest.mark.parametrize("flag", ["--owned-path", "--research-owned-path"])
def test_dispatch_refuses_a_normalized_protected_path(no_spawn, capsys, flag):
    _assert_refused(
        no_spawn, capsys, _dispatch(*_WRITE, flag, "site//src/content/docs/x.mdx"), "'site/src/content/docs/x.mdx'"
    )


def test_dispatch_refuses_a_private_state_prompt_file(no_spawn, capsys, tmp_path):
    prompt = tmp_path / ".claude" / "brief.md"
    prompt.parent.mkdir()
    prompt.write_text("Implement the fix.\n", encoding="utf-8")
    argv = ["dispatch", "--agent", "kimi", "--task-id", "kimi-admission-fixture", "--prompt-file", str(prompt)]
    rc = delegate.main([*argv, *_WRITE])
    err = capsys.readouterr().err
    assert rc == 2
    assert "agent-private state" in err


class _AdmittedSentinel(Exception):
    pass


@pytest.mark.parametrize(
    "owned",
    [
        pytest.param(_BACKEND_OWNED, id="backend"),
        pytest.param(_UI_OWNED, id="ui"),
    ],
)
def test_web_ui_and_backend_dispatches_pass_admission(tmp_path, monkeypatch, owned):
    """The allowed classes clear both admission checks and reach the capacity hint."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.delenv("LU_DISPATCH_CHECK_BUDGET", raising=False)
    monkeypatch.delenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", raising=False)
    monkeypatch.setattr(delegate, "_run_dor_preflight", lambda *_a, **_k: (None, None))
    seen: list[str] = []

    def reached(agent, **_kwargs):
        seen.append(agent)
        raise _AdmittedSentinel

    monkeypatch.setattr(delegate, "_check_capacity_hint", reached)
    ownership: list[str] = []
    for path in owned:
        ownership += ["--owned-path", path, "--research-owned-path", path]
    argv = _dispatch(*_WRITE, "--research-role", "harness", *ownership)
    with pytest.raises(_AdmittedSentinel):
        delegate.main(argv)
    assert seen == ["kimi"]


# --- delegate worker ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("mode", "review"),
    [("read-only", {"require_review_verdict": True}), ("danger", {}), ("workspace-write", {"review_id": "rev-1"})],
)
def test_worker_refuses_before_invocation(tmp_path, monkeypatch, mode, review):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setattr("agent_runtime.runner.invoke", _fail)
    task_id = f"kimi-worker-{mode}"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(state_path, {"task_id": task_id, "status": "spawning"})

    rc = delegate._run_worker(
        task_id=task_id,
        agent="kimi",
        prompt="Review the diff.",
        mode=mode,
        cwd_str=str(tmp_path),
        model=None,
        hard_timeout=60,
        harness="kimicc",
        **review,
    )

    assert rc == 1
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["status"] == "failed"
    assert _TOKEN in state["stderr_excerpt"]
    assert state["returncode_reason"] == "routing refused before invocation"


# --- runtime boundary ----------------------------------------------------------------


def test_runtime_refusal_admits_workspace_write_only():
    assert kimi_admission.runtime_refusal("kimi", mode="workspace-write") is None
    assert kimi_admission.runtime_refusal("kimi", mode="workspace-write", tool_config={"harness": "kimicc"}) is None
    for mode in ("read-only", "danger"):
        assert "--mode " + mode in kimi_admission.runtime_refusal("kimi", mode=mode)
    for marker in ("review_verdict_required", "review_isolation", "review_id"):
        refusal = kimi_admission.runtime_refusal("kimi", mode="workspace-write", tool_config={marker: "x"})
        assert refusal and "review dispatches" in refusal


@pytest.mark.parametrize(
    ("mode", "tool_config"),
    [
        ("read-only", None),
        ("danger", None),
        ("read-only", {"harness": "kimicc", "trail_isolation": True}),
        ("workspace-write", {"review_id": "rev-1"}),
    ],
)
def test_runner_invoke_refuses_before_attribution_or_trail_provisioning(tmp_path, monkeypatch, mode, tool_config):
    from scripts.agent_runtime import runner

    monkeypatch.setattr(runner, "resolve_invocation_attribution", _fail)
    monkeypatch.setattr(runner, "prepare_trail_isolation", _fail)
    monkeypatch.setattr(runner, "_invoke_impl", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        runner.invoke("kimi", "Review this.", mode=mode, cwd=tmp_path, tool_config=tool_config)


@pytest.mark.parametrize("harness", [None, "kimicc"])
@pytest.mark.parametrize("mode", ["read-only", "danger"])
def test_kimi_adapters_refuse_read_only_and_danger_before_planning(tmp_path, monkeypatch, harness, mode):
    from scripts.agent_runtime.adapters import kimi as kimi_adapter
    from scripts.agent_runtime.adapters import kimicc as kimicc_adapter

    monkeypatch.setattr(kimi_adapter, "_resolve_kimi_binary", _fail)
    monkeypatch.setattr(kimicc_adapter, "_default_claude_bin", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        kimi_adapter.KimiAdapter().build_invocation(
            prompt="p",
            mode=mode,
            cwd=tmp_path,
            model=None,
            task_id="t",
            session_id=None,
            tool_config={"harness": harness} if harness else None,
        )
    with pytest.raises(ValueError, match=_TOKEN):
        kimicc_adapter.KimiccHarness().build_invocation(
            prompt="p", mode=mode, cwd=tmp_path, model=None, task_id="t", session_id=None, tool_config=None
        )


def test_trail_isolation_refuses_kimi():
    from scripts.agent_runtime.trail_isolation import TrailIsolationError, prepare_trail_isolation

    with pytest.raises(TrailIsolationError, match=_TOKEN):
        prepare_trail_isolation(
            agent_name="kimi", mode="read-only", tool_config={"trail_isolation": True, "harness": "kimicc"}
        )


# --- ACP, bridge and fleet-comms entry points ------------------------------------------


def test_compat_ask_refuses_before_telemetry(monkeypatch):
    from scripts.ai_agent_bridge import _acp_compat
    from scripts.telemetry import legacy_bridge

    monkeypatch.setattr(legacy_bridge, "start_bridge_invocation_safely", _fail)
    monkeypatch.setattr(_acp_compat, "_run_compat_ask_impl", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _acp_compat.run_compat_ask("kimi", "Consult on this design.", task_id="kimi-consult")
    with pytest.raises(ValueError, match=_TOKEN):
        _acp_compat.run_compat_ask("claude", "Consult.", task_id="kimi-model", model="kimi-code/k3")


def test_compat_ask_impl_refuses_before_the_job_host_forward(monkeypatch):
    from scripts.ai_agent_bridge import _acp_compat, _job_host_forward

    monkeypatch.setattr(_job_host_forward, "maybe_forward_compat_ask", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _acp_compat._run_compat_ask_impl("kimi", "Consult.", task_id="kimi-forward")


def test_a_kimi_quota_substitute_is_refused_before_its_job_is_enqueued(monkeypatch):
    from scripts.ai_agent_bridge import _acp_compat
    from scripts.fleet_comms import authority

    monkeypatch.setattr(authority, "AuthorityService", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _acp_compat._run_single_acp_job(
            "kimi", "Consult.", task_id="t", source=None, model=None, effort=None, review=False, hard_timeout=60
        )


@pytest.mark.parametrize("extra", [[], ["--pr", "9158"], ["--review"]])
def test_ask_kimi_cli_refuses_before_pr_resolution_or_dispatch(monkeypatch, extra):
    from scripts.ai_agent_bridge import _acp_compat, _cli, _dispatch_wrappers

    monkeypatch.setattr(_cli, "_resolve_same_repo_pr_head", _fail)
    monkeypatch.setattr(_acp_compat, "run_compat_ask", _fail)
    monkeypatch.setattr(_dispatch_wrappers, "run_ask_review_dispatch", _fail)
    monkeypatch.setattr("sys.stdin", types.SimpleNamespace(read=_fail))
    args = _cli._build_parser().parse_args(["ask-kimi", "-", "--task-id", "kimi-cli", *extra])
    with pytest.raises(SystemExit, match=_TOKEN):
        _cli._handle_ask_kimi(args)


def test_ask_review_dispatch_refuses_before_the_temporary_prompt(monkeypatch):
    from scripts.ai_agent_bridge import _dispatch_wrappers

    monkeypatch.setattr(_dispatch_wrappers, "_prompt_directory", _fail)
    monkeypatch.setattr(_dispatch_wrappers.subprocess, "run", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _dispatch_wrappers.run_ask_review_dispatch("kimi", "Review PR #1.", task_id="kimi-review")


def test_ask_review_dispatch_command_never_selects_a_kimi_harness(tmp_path):
    from scripts.ai_agent_bridge import _dispatch_wrappers

    cmd = _dispatch_wrappers.build_ask_review_dispatch_command(
        "claude", "t", tmp_path / "p.md", model=None, effort=None
    )
    assert "--harness" not in cmd


def test_authority_enqueue_request_refuses_before_any_write():
    from scripts.fleet_comms.authority import AuthorityService

    service = AuthorityService.__new__(AuthorityService)  # no connection: any write would raise AttributeError
    with pytest.raises(ValueError, match=_TOKEN):
        service.enqueue_request(recipient="kimi", body="Consult on this design.")
    with pytest.raises(ValueError, match=_TOKEN):
        service.enqueue_request(recipient="claude", body="Consult.", metadata={"requested_model": "kimi-code/k3"})


def test_authority_enqueue_discussion_refuses_before_any_write():
    from scripts.fleet_comms.authority import AuthorityService

    service = AuthorityService.__new__(AuthorityService)
    with pytest.raises(ValueError, match=_TOKEN):
        service.enqueue_discussion(
            channel="architecture",
            prompt="Compare the options.",
            participants=("claude", "kimicc"),
            rounds=1,
            task_digest="digest",
            correlation_id="corr",
            deadline_at="2026-09-30T00:00:00+00:00",
        )


def test_fleet_request_to_kimi_is_refused_before_any_insert():
    executor = RequestExecutor.__new__(RequestExecutor)
    executor.registry = load_endpoint_registry()
    with pytest.raises(ValueError, match=_TOKEN):
        executor.create_request(recipient="kimi", body="Consult on this design.")


def test_acp_discussion_refuses_before_the_plane_is_opened(tmp_path, monkeypatch):
    from scripts.agent_runtime import acpx_discuss

    monkeypatch.setattr(acpx_discuss, "AcpxDiscussionController", _fail)
    with pytest.raises(acpx_discuss.AcpxDiscussionError, match=_TOKEN):
        acpx_discuss.run_discussion(
            prompt="Compare the options.",
            cwd=tmp_path,
            task_id="t",
            correlation_id="c",
            idempotency_key="i",
            rounds=1,
            participants=("claude", "kimi"),
        )


def test_ab_discuss_refuses_before_any_channel_write(monkeypatch, capsys):
    from scripts.ai_agent_bridge import _channels_cli
    from scripts.fleet_comms import authority

    monkeypatch.delenv("LU_AGENT_COMM_TRANSPORT", raising=False)
    monkeypatch.setattr(authority, "AuthorityService", _fail)
    args = types.SimpleNamespace(
        channel="architecture", body="Compare.", with_agents="claude,kimicc", max_rounds=1, review=False, models=None
    )
    assert _channels_cli._handle_discuss(args) == 2
    assert _TOKEN in capsys.readouterr().err


def test_broker_message_to_kimi_is_refused_before_invocation(monkeypatch):
    from scripts.ai_agent_bridge import _process

    msg = {"id": 7, "to": "kimi", "from": "codex", "task_id": "t", "type": "query", "content": "Consult."}
    monkeypatch.setattr(_process, "read_message", lambda _id: msg)
    monkeypatch.setattr(_process, "_message_acknowledged", lambda _id: False)
    monkeypatch.setattr(_process, "run_compat_ask", _fail)
    reasons: list[str] = []
    monkeypatch.setattr(_process, "_notify_processing_failure", lambda _m, _i, _p, reason: reasons.append(reason))
    assert _process.process_message_for_recipient(7) is None
    assert reasons and _TOKEN in reasons[0]
    assert not _process.recipient_has_acp_route("kimi")


def test_legacy_kimi_bridge_refuses_before_broker_write_or_worktree(monkeypatch):
    from scripts.ai_agent_bridge import _kimi

    monkeypatch.setattr(_kimi, "send_message", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _kimi.ask_kimi("Review this.", task_id="t", review=True)

    msg = {"id": 3, "task_id": "t", "from": "codex", "to": "kimi", "type": "query", "content": "q", "data": None}
    monkeypatch.setattr(_kimi, "_fetch_kimi_message", lambda _id: msg)
    monkeypatch.setattr(_kimi, "provision_review_worktree", _fail)
    reasons: list[str] = []
    monkeypatch.setattr(_kimi, "_handle_kimi_error", lambda _m, _i, reason: reasons.append(reason))
    _kimi.process_for_kimi(3, review=True)
    assert reasons and _TOKEN in reasons[0]


# --- capacity hint -----------------------------------------------------------------


def _busy_codex(tmp_path, monkeypatch):
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


def test_capacity_hint_never_suggests_kimi_for_owned_content(tmp_path, monkeypatch, capsys):
    _busy_codex(tmp_path, monkeypatch)
    content = types.SimpleNamespace(
        json=False, quiet=False, mode="workspace-write", owned_path=["site/src/content/docs/x.mdx"]
    )
    delegate._check_capacity_hint("codex", args=content)
    assert "kimi" not in capsys.readouterr().err.split("available in:", 1)[1]


def test_capacity_hint_suggests_kimi_for_web_ui_and_backend_coding(tmp_path, monkeypatch, capsys):
    _busy_codex(tmp_path, monkeypatch)
    coding = types.SimpleNamespace(
        json=False,
        quiet=False,
        mode="workspace-write",
        owned_path=["site/src/components/Card.astro"],
        research_owned_path=["scripts/x.py"],
    )
    delegate._check_capacity_hint("codex", args=coding)
    assert "kimi" in capsys.readouterr().err.split("available in:", 1)[1]
