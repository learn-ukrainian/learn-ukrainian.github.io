"""Kimi: web, UI and backend coding only — the path allowlist, the one gate, and its entry points."""

from __future__ import annotations

import json
import subprocess
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
_BACKEND_OWNED = ("scripts/agent_runtime/runner.py", "tests/agent_runtime/test_runner.py")
_UI_OWNED = ("site/src/components/Card.astro", "site/src/styles/course.css", "site/astro.config.mjs")


def _fail(*_args, **_kwargs):
    raise AssertionError("a refused Kimi call reached a side effect")


def _refusal(participants=("kimi",), models=(), **overrides) -> str | None:
    kwargs = {"mode": "workspace-write", "paths": _BACKEND_OWNED, "repo": "public-monorepo", "repo_root": _REPO_ROOT}
    kwargs.update(overrides)
    try:
        kimi_admission.refuse_kimi_if_disallowed(participants, models, **kwargs)
    except kimi_admission.KimiAdmissionRefused as exc:
        return str(exc)
    return None


# --- the allowlist ---------------------------------------------------------------

# Admitted: UI code, the named site/src/lib helpers, site config, verified backend
# packages with their tests, CI and Dagger. Paths are normalized first.
ADMITTED_PATHS = (
    "site/src/components/Card.astro",
    "site/src/components/practice/SettingsDrawer.tsx",
    "site/src/layouts/CourseLayout.astro",
    "site/src/pages/index.astro",
    "site/src/styles/course.css",
    "site/src/css/x.css",
    "site/src/assets/logo.svg",
    "site/src/lib/arc.ts",
    "site/src/lib/doc-nav.ts",
    "site/src/lib/readings.ts",
    "site/src/lib/a1-archive-routes.ts",
    "site/astro.config.mjs",
    "site/vitest.config.ts",
    "scripts/agent_runtime/runner.py",
    "scripts/api/state_router.py",
    "scripts/orchestration/dispatch_admission.py",
    "scripts/ci/pytest_shards.py",
    "scripts/fleet_comms/authority.py",
    "scripts/hygiene/branch_sweep.py",
    "scripts/storage/topology.py",
    "tests/agent_runtime/test_runner.py",
    "tests/storage/test_artifacts.py",
    ".github/workflows/ci.yml",
    ".github/actions/python-ci-env/action.yml",
    ".dagger/src/learn_ukrainian_ci/main.py",
    "./scripts/api/x.py",
    "scripts//ci/x.py",
)

# Refused: everything not on the allowlist (Ukrainian dataset exporters, wiki
# prompts, language tests and fixtures, site language test cases, curriculum,
# lexicon, rules, instructions, private state, non-UI site files) and the named
# exclusions inside allowlisted roots.
REFUSED_PATHS = (
    "scripts/dataset/export_ukrainian_pedagogy_dataset.py",
    "scripts/wiki/prompts/compile_pedagogy_brief.md",
    "tests/test_euphony.py",
    "tests/fixtures/messages.po",
    "site/tests/unit/adjective-mechanics.test.ts",
    "site/e2e/nav.spec.ts",
    "scripts/audit/naturalness_check.py",
    "scripts/curriculum/resolver/tokenize.py",
    "curriculum/l2-uk-en/a1/lesson.mdx",
    "wiki/topic.md",
    "data/sources.db",
    "registry/lexicon/x.yaml",
    "site/src/content/docs/a1/lesson.mdx",
    "site/src/data/words.json",
    "site/src/lexicon/entry.ts",
    "site/src/lib/i18n/chrome.ts",
    "site/src/lib/lexicon/adjective-mechanics.ts",
    "site/src/lib/new-helper.ts",
    "scripts/lexicon/x.py",
    "scripts/verification/stress.py",
    "scripts/practice/noun_mechanics_engine.py",
    "scripts/pipeline/stress_annotator.py",
    "scripts/launchd/x.plist",
    "scripts/delegate.py",
    "scripts/config/model_catalog.yaml",
    "docs/best-practices/code-quality.md",
    "agents_extensions/shared/rules/model-assignment.md",
    "CLAUDE.md",
    "AGENTS.md",
    ".claude/settings.json",
    ".github/CODEOWNERS",
    ".github/ISSUE_TEMPLATE/naturalness-quality.md",
    "site/package.json",
    "README.md",
    # Exclusions inside allowlisted roots.
    "scripts/agent_runtime/kimi_admission.py",
    "scripts/agent_runtime/adapters/kimi.py",
    "scripts/agent_runtime/profiles/acpx-grok-sealed-review.md",
    "scripts/api/hramatka_generator.py",
    "scripts/api/sources_router.py",
    "tests/api/test_hramatka_router.py",
    "scripts/orchestration/curriculum_readiness.py",
    "scripts/orchestration/prompt_contracts.py",
    "tests/orchestration/test_curriculum_readiness.py",
    # A differently cased spelling is not the allowlisted directory.
    "Scripts/agent_runtime/runner.py",
    "site/src/Components/Card.astro",
)


@pytest.mark.parametrize("path", ADMITTED_PATHS)
def test_allowlisted_paths_are_admitted(path):
    assert kimi_admission.owned_path_reason(path) is None
    assert _refusal(paths=(path,)) is None


@pytest.mark.parametrize("path", REFUSED_PATHS)
def test_everything_off_the_allowlist_is_refused(path):
    assert kimi_admission.owned_path_reason(path)
    message = _refusal(paths=("scripts/agent_runtime/runner.py", path))
    assert message and "owned path" in message


def test_every_allowlisted_root_and_exclusion_carries_a_reason():
    for table in (kimi_admission.KIMI_OWNED_ROOTS, kimi_admission.KIMI_EXCLUDED_PATHS):
        for key, reason in table.items():
            assert reason.strip(), key


def test_every_allowlisted_root_exists_in_the_repository():
    tracked = subprocess.run(
        ["git", "ls-files", "site/src", "scripts", "tests", ".github", ".dagger"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout.splitlines()
    for root in kimi_admission.KIMI_OWNED_ROOTS:
        if root.endswith("/"):
            assert any(path.startswith(root) for path in tracked), root
        else:
            assert root in tracked, root


def test_every_backend_package_admits_its_tests():
    for root in kimi_admission.KIMI_OWNED_ROOTS:
        if root.startswith("scripts/"):
            assert f"tests/{root.removeprefix('scripts/')}" in kimi_admission.KIMI_OWNED_ROOTS


@pytest.mark.parametrize(
    ("path", "canonical"),
    [
        ("site//src/content/docs/x.mdx", "site/src/content/docs/x.mdx"),
        ("./docs/../docs/x", "docs/x"),
        ("scripts/api/../../docs/x.md", "docs/x.md"),
        ("site/src/pages/../content/x.mdx", "site/src/content/x.mdx"),
        ("site/src/components/../../src/lib/i18n/x.ts", "site/src/lib/i18n/x.ts"),
        ("scripts\\api\\..\\..\\CLAUDE.md", "CLAUDE.md"),
    ],
)
def test_paths_are_normalized_before_the_allowlist(path, canonical):
    assert kimi_admission.normalize_owned_path(path) == canonical
    message = _refusal(paths=(path,))
    assert message and f"owned path {canonical!r}" in message


@pytest.mark.parametrize(
    "path", ["/etc/passwd", "/home/me/repo/scripts/x.py", "~/x.py", "C:/x.py", "../x.py", "scripts/../../x.py", ".", ""]
)
def test_absolute_and_escaping_paths_are_refused(path):
    assert kimi_admission.normalize_owned_path(path) is None
    message = _refusal(paths=(path,))
    assert message and "is not a repository-relative path" in message


# --- the gate ------------------------------------------------------------------------


@pytest.mark.parametrize("participant", ["kimi", "kimicc"])
@pytest.mark.parametrize("owned", [_BACKEND_OWNED, _UI_OWNED, ()])
def test_web_ui_and_backend_coding_is_admitted(participant, owned):
    assert _refusal(participants=(participant,), paths=owned) is None


@pytest.mark.parametrize("agent", ["claude", "codex", "grok", "agy", "cursor"])
def test_other_seats_are_untouched(agent):
    assert _refusal(participants=(agent,), mode="read-only", review=True, paths=("docs/x.md",)) is None
    assert _refusal(participants=(agent,), models=("gpt-6-sol",), mode=kimi_admission.ACP_MODE) is None


@pytest.mark.parametrize(
    ("agent", "model"),
    [
        ("kimi", None),
        ("kimicc", None),
        ("kimi-infra", None),
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


def test_an_effective_kimi_model_on_any_seat_is_gated():
    message = _refusal(participants=("claude", "codex"), models=(None, "kimi-code/k3"), mode=kimi_admission.ACP_MODE)
    assert message and "ACP asks, consults, discussions, and reviews" in message


@pytest.mark.parametrize("mode", ["read-only", "danger"])
def test_non_workspace_write_modes_are_refused(mode):
    message = _refusal(mode=mode)
    assert message and f"--mode {mode}" in message


@pytest.mark.parametrize("mode", [kimi_admission.ACP_MODE, kimi_admission.REVIEW_MODE])
def test_acp_and_review_activities_are_refused(mode):
    assert _refusal(mode=mode, paths=())


@pytest.mark.parametrize("marker", ["review_verdict_required", "review_isolation", "review_id"])
def test_review_markers_are_refused(marker):
    assert "review dispatches" in _refusal(review=False, tool_config={marker: "x"})
    assert "review dispatches" in _refusal(review=True)


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


@pytest.mark.parametrize(
    "prompt_file",
    ["/home/me/.claude/briefs/task.md", ".agent/handoff.md", "repo/.codex/prompt.md"],
)
def test_prompt_file_in_private_state_is_refused(prompt_file):
    message = _refusal(prompt_file=prompt_file)
    assert message and "agent-private state" in message


@pytest.mark.parametrize("role", ["private-infra", "private-product"])
def test_private_repositories_are_refused(role):
    message = _refusal(repo=role)
    assert message and f"--repo role {role!r} is a private repository" in message


def test_refusal_states_the_policy_and_names_the_alternative_seats():
    message = _refusal(mode="read-only", review=True, paths=("docs/x.md",))
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
@pytest.mark.parametrize("path", REFUSED_PATHS)
def test_dispatch_refuses_every_off_allowlist_path_through_either_ownership_flag(no_spawn, capsys, flag, path):
    _assert_refused(no_spawn, capsys, _dispatch(*_WRITE, flag, "scripts/ci/x.py", flag, path), "owned path")


def test_dispatch_refuses_a_kimi_model_on_another_seat(no_spawn, capsys):
    argv = ["dispatch", "--agent", "codex", "--model", "kimi-code/k3", "--task-id", "t", "--prompt", "Review it."]
    _assert_refused(no_spawn, capsys, argv, "--mode read-only")


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
def test_worker_refuses_with_zero_side_effects(tmp_path, monkeypatch, capsys, mode, review):
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    for sentinel in ("_state_path", "_read_state", "_write_state_atomic"):
        monkeypatch.setattr(delegate, sentinel, _fail)
    monkeypatch.setattr(delegate.signal, "signal", _fail)
    monkeypatch.setattr("agent_runtime.runner.invoke", _fail)

    rc = delegate._run_worker(
        task_id=f"kimi-worker-{mode}",
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
    assert _TOKEN in capsys.readouterr().err
    assert not tasks.exists()


# --- runtime boundary ----------------------------------------------------------------


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


def test_inter_agent_route_refuses_a_kimi_model_override():
    from scripts.agent_runtime import runner

    for participant, model in (("kimi", None), ("kimicc", None), ("claude", "kimi-code/k3")):
        with pytest.raises(runner.InterAgentTransportError, match=_TOKEN):
            runner.resolve_inter_agent_route(participant, model=model)


def test_no_non_kimi_acp_participant_pins_a_kimi_model():
    from scripts.agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    for name, route in ACPX_SUPPORTED_PARTICIPANTS.items():
        if kimi_admission.is_kimi_model(route.get("model")):
            assert kimi_admission.is_kimi_seat(name), name


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
    with pytest.raises(ValueError, match=_TOKEN):
        _dispatch_wrappers.run_ask_review_dispatch("claude", "Review PR #1.", task_id="r", model="kimi-code/k3")


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


@pytest.mark.parametrize(
    ("participants", "models"),
    [
        (("claude", "kimi"), None),
        (("claude", "codex"), {"claude": "kimi-code/k3"}),
        (("codex", "kimicc"), None),
    ],
)
def test_acp_discussion_refuses_on_effective_seats_and_models_before_the_plane(
    tmp_path, monkeypatch, participants, models
):
    from scripts.agent_runtime import acpx_discuss

    monkeypatch.setattr(acpx_discuss, "AcpxDiscussionController", _fail)
    monkeypatch.setattr(acpx_discuss, "ArtifactStore", _fail)
    monkeypatch.setattr(acpx_discuss, "default_plane_root", _fail)
    with pytest.raises(acpx_discuss.AcpxDiscussionError, match=_TOKEN):
        acpx_discuss.run_discussion(
            prompt="Compare the options.",
            cwd=tmp_path,
            task_id="t",
            correlation_id="c",
            idempotency_key="i",
            rounds=1,
            participants=participants,
            models=models,
        )


@pytest.mark.parametrize(("with_agents", "models"), [("claude,kimicc", None), ("claude,codex", "claude:kimi-code/k3")])
def test_ab_discuss_refuses_on_effective_models_before_any_channel_write(monkeypatch, capsys, with_agents, models):
    from scripts.ai_agent_bridge import _channels_cli
    from scripts.fleet_comms import authority

    monkeypatch.delenv("LU_AGENT_COMM_TRANSPORT", raising=False)
    monkeypatch.setattr(authority, "AuthorityService", _fail)
    args = types.SimpleNamespace(
        channel="architecture", body="Compare.", with_agents=with_agents, max_rounds=1, review=False, models=models
    )
    assert _channels_cli._handle_discuss(args) == 2
    assert _TOKEN in capsys.readouterr().err


def test_ab_inbox_run_for_kimi_is_refused_before_housekeeping(monkeypatch, capsys):
    from scripts.ai_agent_bridge import _channels, _channels_cli

    monkeypatch.setattr(_channels, "expire_stale_deliveries", _fail)
    args = types.SimpleNamespace(agent="kimi", once=True, until_idle=False, max_messages=None)
    assert _channels_cli._handle_inbox_run(args) == 2
    assert _TOKEN in capsys.readouterr().err


def test_inbox_worker_refuses_kimi_before_any_claim(monkeypatch):
    from scripts.ai_agent_bridge import _channels, _inbox

    monkeypatch.setattr(_inbox, "_claim_next_thread", _fail)
    monkeypatch.setattr(_channels, "expire_stale_deliveries", _fail)
    with pytest.raises(ValueError, match=_TOKEN):
        _inbox.run_inbox("kimi")


# --- broker drain paths: refusal returns an error and records nothing ------------------


@pytest.fixture
def broker_sentinels(monkeypatch):
    """Every write, telemetry and broker call on the drain paths fails the test."""
    from scripts.ai_agent_bridge import _ask_lifecycle, _messaging, _process

    for module, names in (
        (_process, ("send_message", "acknowledge", "record_ask_failure", "record_ask_reply", "run_compat_ask")),
        (_process, ("_notify_processing_failure", "_message_acknowledged")),
        (_ask_lifecycle, ("mark_ask_processing", "record_ask_failure", "_AskTerminalRecorder")),
        (_messaging, ("send_message", "acknowledge")),
    ):
        for name in names:
            monkeypatch.setattr(module, name, _fail)

    def message(to: str, data: str | None = None) -> None:
        msg = {"id": 7, "to": to, "from": "codex", "task_id": "t", "type": "query", "content": "q", "data": data}
        monkeypatch.setattr(_process, "read_message", lambda _id, **_k: msg)
        monkeypatch.setattr(_messaging, "read_message", lambda _id, **_k: msg)

    return message


@pytest.mark.parametrize(("to", "data"), [("kimi", None), ("claude", json.dumps({"to_model": "kimi-code/k3"}))])
def test_process_message_refuses_with_zero_side_effects(broker_sentinels, to, data):
    from scripts.ai_agent_bridge import _process

    broker_sentinels(to, data)
    with pytest.raises(ValueError, match=_TOKEN):
        _process.process_message_for_recipient(7)
    assert not _process.recipient_has_acp_route("kimi")


def test_process_cli_commands_refuse_with_zero_side_effects(broker_sentinels):
    from scripts.ai_agent_bridge import _cli

    broker_sentinels("kimi")
    for argv in (["process", "7"], ["process-kimi", "7"]):
        with pytest.raises(SystemExit, match=_TOKEN):
            _cli._dispatch_command(_cli._build_parser().parse_args(argv))


def test_detached_ask_worker_refuses_with_zero_side_effects(broker_sentinels, monkeypatch):
    from scripts.ai_agent_bridge import _ask_lifecycle

    broker_sentinels("kimi")
    monkeypatch.setattr(_ask_lifecycle.atexit, "register", _fail)
    with pytest.raises(SystemExit, match=_TOKEN):
        _ask_lifecycle.process_background_ask(7, "kimi")


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
        research_owned_path=["scripts/agent_runtime/runner.py"],
    )
    delegate._check_capacity_hint("codex", args=coding)
    assert "kimi" in capsys.readouterr().err.split("available in:", 1)[1]
