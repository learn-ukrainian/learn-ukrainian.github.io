"""Legacy launch-admission tests ported to the v2 dispatcher (C-2188 unit D).

Each test names its legacy source; assertions are adapted to the v2 entry points only.
"""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from scripts.dispatcher import admission, cli, git, host_admission, providers, store, worker
from scripts.dispatcher.environment import child_env
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec
from scripts.lib import rules_core
from tests.agent_runtime.test_attempt_boundary import CLAUDE_AMBIENT_AUTH, _private_json
from tests.agent_runtime.test_claude_account_worker import _calls, _run, accounts  # noqa: F401  (fixture)
from tests.test_rules_core_loading import core_without_addendum, missing_core  # noqa: F401  (fixtures)


@pytest.mark.parametrize("agent", providers.PROVIDERS)
@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
def test_worker_git_transport_restricts_network_only_in_read_only_mode(tmp_path, monkeypatch, agent, mode):
    """#11797: an explicit push URL must not escape the read-only worker's transport policy."""
    monkeypatch.setenv("GIT_ALLOW_PROTOCOL", "https:ssh:ext")
    spec = TaskSpec("transport", agent, "m", None, mode, tmp_path, tmp_path / "prompt", tmp_path / "final")
    env = child_env(spec)
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], env=env, check=True, timeout=10)
    subprocess.run(
        ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "core.hooksPath=/dev/null", "commit", "--quiet", "--allow-empty", "-m", "fixture"],
        cwd=tmp_path, env=env, check=True, timeout=10,
    )
    # A disposable helper makes transport admission observable without contacting a host.
    marker = tmp_path / "transport-started"
    helper = tmp_path / "git-remote-https"
    helper.write_text(f"#!{sys.executable}\nfrom pathlib import Path\nPath({str(marker)!r}).touch()\n")
    helper.chmod(0o755)
    env["GIT_EXEC_PATH"] = str(tmp_path)
    result = subprocess.run(
        ["git", "-c", "protocol.https.allow=always", "push", "https://example.invalid/repo.git", "HEAD"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10,
    )
    if mode == "read-only":
        assert result.returncode != 0
        assert "transport 'https' not allowed" in result.stderr
        assert not marker.exists()
        for protocol, url in (("ssh", "ssh://example.invalid/repo.git"),
                              ("git", "git://example.invalid/repo.git"),
                              ("ext", "ext::unused-helper")):
            refused = subprocess.run(
                ["git", "-c", f"protocol.{protocol}.allow=always", "push", url, "HEAD"],
                cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10,
            )
            assert refused.returncode != 0
            assert f"transport '{protocol}' not allowed" in refused.stderr
    else:
        assert marker.exists(), result.stderr
    # The issue's local-protocol alternative preserves local Git operations in both modes.
    remote = tmp_path / "local.git"
    subprocess.run(["git", "init", "--quiet", "--bare", str(remote)], env=env, check=True, timeout=10)
    subprocess.run(["git", "push", remote.as_uri(), "HEAD:refs/heads/proof"], cwd=tmp_path,
                   env=env, capture_output=True, check=True, timeout=10)
    local_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path, env=env,
                                capture_output=True, text=True, check=True, timeout=10).stdout.strip()
    remote_head = subprocess.run(["git", "--git-dir", str(remote), "rev-parse", "refs/heads/proof"], env=env,
                                 capture_output=True, text=True, check=True, timeout=10).stdout.strip()
    assert remote_head == local_head


def _refuse_side_effects(monkeypatch, tmp_path):
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    for target, name in ((git, "create_worktree"), (git, "resolve_repo"), (worker, "start")):
        monkeypatch.setattr(target, name, lambda *_a, _name=name, **_k: pytest.fail(f"{_name} ran before refusal"))
    return tasks


# ----------------------------------------------------------------- Claude account (#10619)


def _labelled(accounts, monkeypatch):  # noqa: F811
    monkeypatch.setenv("PATH", f"{accounts.binary.parent}{os.pathsep}{os.environ['PATH']}")
    prompt = accounts.workdir / "prompt.txt"
    prompt.write_text("do the task")
    spec = TaskSpec(
        "labelled", "claude", "m", None, "workspace-write", accounts.workdir, prompt, accounts.workdir / "final",
        claude_account="b",
    )
    # The fixture CLI logs its calls through a variable the v2 environment does not pass on.
    env = {**child_env(spec), "LU_FAKE_CLAUDE_DUMP": str(accounts.dump)}
    return spec, providers.load("claude").build(spec, env)


@pytest.mark.parametrize(
    ("name", "settings"),
    [
        ("settings.local.json", {"apiKeyHelper": "fixture-helper-command"}),
        ("settings.json", {"apiKeyHelper": "fixture-helper-command"}),
        ("settings.local.json", {"env": {"CLAUDE_CODE_USE_BEDROCK": "1"}}),
    ],
)
def test_bound_label_checkout_setting_that_changes_auth_is_refused(accounts, monkeypatch, name, settings):  # noqa: F811
    """Ported from tests/agent_runtime/test_claude_account_worker.py::test_bound_label_checkout_setting_that_changes_auth_is_refused.

    A project or local setting the run still loads cannot switch its authentication.
    """
    _private_json(accounts.workdir / ".claude" / name, settings)
    spec, invocation = _labelled(accounts, monkeypatch)

    with pytest.raises(ValueError) as refused:
        admission.claude_launch(spec, invocation)

    assert str(refused.value) == "CLAUDE_ACCOUNT_REFUSED: claude_account_auth_method_conflict"
    assert len(_calls(accounts, "auth_status")) == 1
    assert _calls(accounts, "run") == []


def test_bound_label_runs_with_only_the_bound_login_directory(accounts, monkeypatch):  # noqa: F811
    """Ported from tests/agent_runtime/test_claude_account_worker.py::test_bound_label_runs_with_only_the_bound_login_directory.

    Label b's worker runs behind the launch guard in the bound login directory, with no user-scope
    settings and no other credential source.
    """
    spec, invocation = _labelled(accounts, monkeypatch)
    launched = admission.claude_launch(spec, invocation)

    completed = subprocess.run(
        launched.argv, input=launched.stdin, env=launched.env, cwd=spec.worktree, capture_output=True, timeout=60
    )

    assert completed.returncode == 0, completed.stderr
    seen = _run(accounts)
    env = seen["env"]
    assert env["CLAUDE_CONFIG_DIR"] == str(accounts.config_dir)
    assert not {name for name in env if name.upper() in CLAUDE_AMBIENT_AUTH or name.upper().startswith("ANTHROPIC_")}
    assert not [name for name, value in env.items() if accounts.bound_token in value or accounts.default_token in value]
    assert accounts.profile_calls == [accounts.bound_token]
    argv = seen["argv"]
    assert argv[argv.index("--setting-sources") + 1] == "project,local"
    assert str(accounts.config_dir) not in repr(argv) + repr(launched.argv)


# ----------------------------------------------------------------- rules core


def test_delegate_dispatch_without_the_core_refuses(tmp_path, monkeypatch, missing_core, capsys):  # noqa: F811
    """Ported from tests/test_rules_core_loading.py::test_delegate_dispatch_without_the_core_refuses."""
    tasks = _refuse_side_effects(monkeypatch, tmp_path)

    assert cli.main(["dispatch", "--agent", "codex", "--model", "m", "--prompt", "the source prompt"]) == 2

    err = capsys.readouterr().err
    assert "dispatch refused" in err
    assert "agents_extensions/shared/rules/core.md" in err
    assert not tasks.exists()


def test_delegate_content_seat_without_the_addendum_refuses(
    tmp_path, monkeypatch, core_without_addendum, capsys  # noqa: F811
):
    """Ported from tests/test_rules_core_loading.py::test_delegate_content_seat_without_the_addendum_refuses."""
    monkeypatch.setenv(rules_core.SEAT_ENV, "content")
    tasks = _refuse_side_effects(monkeypatch, tmp_path)

    assert cli.main(["dispatch", "--agent", "codex", "--model", "m", "--prompt", "the source prompt"]) == 2

    assert "core-curriculum.md" in capsys.readouterr().err
    assert not tasks.exists()


# ----------------------------------------------------------------- plan headroom and runtime exhaustion (unit D6)


@pytest.fixture
def headroom_box(tmp_path, monkeypatch):
    from scripts.agent_runtime import model_pause, usage

    tasks = tmp_path / "tasks"
    tasks.mkdir()
    (tasks / "logs").mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    policy = tmp_path / "model-pause.json"
    monkeypatch.setenv("LU_MODEL_PAUSE_FILE", str(policy))
    monkeypatch.delenv("LU_BYPASS_RATE_LIMIT", raising=False)
    monkeypatch.setattr(usage, "_usage_dir", lambda: tmp_path)
    usage._reset_rate_limit_cache_for_tests()
    monkeypatch.setattr(admission, "claude_account", lambda agent, label: (
        {"claude_account": label or "a", "claude_account_source": "explicit"} if agent == "claude" else {}
    ))
    monkeypatch.setattr(host_admission, "precheck", lambda *_a, **_k: None)
    monkeypatch.setattr(host_admission, "check_credit", lambda *_a: None)
    monkeypatch.setattr(git, "resolve_repo", lambda *_a: (tmp_path, {"key": "public"}))
    monkeypatch.setattr(git, "worktree_plan", lambda *_a: (tmp_path, "fixture", "a" * 40))
    monkeypatch.setattr(host_admission, "check", lambda *_a, **_k: None)
    monkeypatch.setattr(worker, "_reap_settled", lambda *_a, **_k: None)
    monkeypatch.setattr(git, "snapshot_delivery", lambda *_a: {})
    monkeypatch.setattr(admission, "claude_launch", lambda _spec, invocation: invocation)
    launches = []

    def build(spec, env):
        launches.append((spec.agent, spec.model, spec.claude_account))
        return Invocation([sys.executable, "-c", "print('literal final response')"], None, env, None)

    monkeypatch.setattr(providers, "load", lambda _agent: SimpleNamespace(
        build=build, parse=lambda *_a: ParsedResult("literal final response", None, None)
    ))

    def meter(a_used=84.0, b_used=11.0, codex_used=30.0):
        import io

        window = dict(left_pct=None, resets_at=None, pace=None, pace_delta_pct=None, leftover_pct=None)
        payload = {
            "agents": {"claude": {"status": "hot", "codexbar": {
                "stale": False, "freshness": "fresh", "weekly_used_pct": a_used,
            }, "runtime": {"headroom_blocked": True}}, "codex": {"status": "cool", "codexbar": {
                "stale": False, "freshness": "fresh", "weekly_used_pct": codex_used,
            }}},
            "claude_accounts": {"claude:b": {
                "session5h": window | {"left_pct": 100.0},
                "weekly": window | {"left_pct": None if b_used is None else 100 - b_used},
                "updated": None, "age_s": 60.0, "stale": False, "status": "ok", "reason": None,
            }},
        }
        monkeypatch.setattr(model_pause.urllib.request, "urlopen", lambda *_a, **_k: io.StringIO(json.dumps(payload)))

    def set_policy(value):
        policy.write_text(json.dumps(value))

    def dispatch(*flags, agent="claude", model="claude-opus-5-5"):
        return cli.main(["dispatch", "--agent", agent, "--model", model, "--prompt", "Explain the result",
                         "--dry-run", *flags])

    def supervise(label="a", *, agent="claude", model="claude-opus-5-5", mode="read-only"):
        prompt = tmp_path / "prompt"
        prompt.write_text("Explain the result")
        spec = TaskSpec("headroom-worker", agent, model, None, mode, tmp_path, prompt, tmp_path / "result", label)
        record = store.new_record(spec, {"key": "public", "github": "example/repo"}, "fixture", "a" * 40,
                                  {"research_owned_path": []})
        record["prompt_file"] = str(tasks / "headroom-worker.prompt")
        path = store.create(record, prompt.read_bytes())
        worker.supervise(path, {}, 10)
        return json.loads(path.read_text())

    meter()
    set_policy({"headroom": [{"lane": "claude", "pattern": "claude-*", "max_weekly_used_pct": 80}]})
    yield SimpleNamespace(meter=meter, policy=set_policy, dispatch=dispatch, supervise=supervise,
                          launches=launches, tasks=tasks, root=tmp_path)
    usage._reset_rate_limit_cache_for_tests()


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
@pytest.mark.parametrize("label", ["a", "b"])
@pytest.mark.parametrize("force", [[], ["--force-admission", "operator host override"]])
def test_plan_headroom_stop_cannot_be_bypassed_by_pin_or_host_override(headroom_box, capsys, mode, label, force):
    """Granted D6 defect class: v2 launches a pinned account at the plan-headroom threshold."""
    box = headroom_box
    box.meter(a_used=80.0 if label == "a" else 11.0, b_used=80.0 if label == "b" else 11.0)
    assert box.dispatch("--mode", mode, "--claude-account", label, *force) == 2
    assert capsys.readouterr().err == "❌ MODEL_HEADROOM: claude-opus-5-5 is held for plan headroom\n"
    assert box.launches == []
    assert list(box.tasks.glob("*.json")) == []


@pytest.mark.parametrize("block", ["pause", "headroom", "runtime"])
@pytest.mark.parametrize("agent,model", [("claude", "claude-opus-5-5"), ("codex", "gpt-6.1-sol")])
def test_paused_or_exhausted_lane_never_silently_substitutes(headroom_box, capsys, block, agent, model):
    """Granted D6 defect class: a refused/exhausted v2 route silently launches a different model."""
    box = headroom_box
    if block == "runtime":
        box.policy({})
        records = [{"ts": (datetime.now(UTC) - timedelta(seconds=age)).isoformat(), "agent": agent,
                    "model": model, "outcome": "rate_limited"} for age in (30, 10)]
        (box.root / f"usage_{agent}-fixture.jsonl").write_text("".join(json.dumps(row) + "\n" for row in records))
    elif block == "pause":
        box.policy({"pauses": [{"pattern": model, "until": "2999-01-01T00:00:00Z"}]})
    else:
        box.meter(a_used=100.0, codex_used=100.0)
        box.policy({"headroom": [{"lane": agent, "pattern": model, "max_weekly_used_pct": 80}]})
    if block != "runtime":
        assert box.dispatch(agent=agent, model=model) == 2
        expected = "MODEL_PAUSED" if block == "pause" else "MODEL_HEADROOM"
        assert expected in capsys.readouterr().err
        assert list(box.tasks.glob("*.json")) == []
    record = box.supervise(agent=agent, model=model)
    assert record["status"] == ("rate_limited" if block == "runtime" else "failed")
    assert record["agent"] == agent and record["model"] == model
    assert record["returncode"] is None
    assert record["finished_at"] is not None
    assert box.launches == []


@pytest.mark.parametrize("label,refused", [("b", False), ("a", True), (None, True)])
def test_worker_admission_reads_the_records_claude_account(headroom_box, label, refused):
    """Ported from tests/test_model_pause.py::test_worker_admission_reads_the_records_claude_account."""
    record = headroom_box.supervise(label)
    assert record["status"] == ("failed" if refused else "done")
    if refused:
        assert record["error"] == "MODEL_HEADROOM: claude-opus-5-5 is held for plan headroom"
        assert headroom_box.launches == []
    else:
        assert headroom_box.launches == [("claude", "claude-opus-5-5", "b")]


def test_invoke_rate_limit_short_circuit(headroom_box, monkeypatch):
    """Ported from tests/test_agent_runtime.py::test_invoke_rate_limit_short_circuit."""
    from scripts.agent_runtime import usage

    headroom_box.policy({})
    monkeypatch.setattr(usage, "has_headroom", lambda *_a, **_k: (False, "cached rate limit"))
    record = headroom_box.supervise(agent="codex", model="gpt-6.1-sol")
    assert record["status"] == "rate_limited"
    assert record["error"] == "codex/gpt-6.1-sol rate limited: cached rate limit"
    assert record["returncode"] is None
    assert headroom_box.launches == []


def test_headroom_stop_refuses_matching_models_only(headroom_box, capsys):
    """Ported from tests/test_model_pause.py::test_headroom_stop_refuses_matching_models_only."""
    assert headroom_box.dispatch(model="claude-sonnet-5-5") == 2
    assert "MODEL_HEADROOM: claude-sonnet-5-5" in capsys.readouterr().err
    assert headroom_box.dispatch(agent="codex", model="gpt-6.1-sol") == 0


def test_unreadable_usage_does_not_block(headroom_box):
    """Ported from tests/test_model_pause.py::test_unreadable_usage_does_not_block."""
    headroom_box.meter(a_used=None, b_used=None)
    assert headroom_box.dispatch() == 0


def test_pause_lifts_by_itself_after_until(headroom_box):
    """Ported from tests/test_model_pause.py::test_pause_lifts_by_itself_after_until."""
    headroom_box.policy({"pauses": [{"pattern": "claude-*", "until": "2000-01-01T00:00:00Z"}]})
    assert headroom_box.dispatch() == 0
