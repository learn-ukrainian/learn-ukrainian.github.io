"""Behavior and send-spy proof of the cooperative-agent publishing boundary."""

from __future__ import annotations

import importlib.util
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts.opsec import prepublish as gate
from tests.opsec_fixtures import CATALOG, ROOT, TOKEN, synthetic_rules


@pytest.fixture(autouse=True)
def fake_catalog(monkeypatch):
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)


@pytest.mark.parametrize(
    "value,host,expected",
    [
        ("unit/public", "github.com", "github.com/unit/public"),
        ("Unit/Repo_Name.git", "GIT.Example.test", "git.example.test/unit/repo_name"),
        (" git@GIT.Example.test:Unit/Repo_Name.git \n", "ignored.test", "git.example.test/unit/repo_name"),
        ("https://GIT.Example.test/Unit/Repo_Name.git", "ignored.test", "git.example.test/unit/repo_name"),
        ("http://GIT.Example.test/Unit/Repo_Name", "ignored.test", "git.example.test/unit/repo_name"),
        ("GIT.Example.test/Unit/Repo_Name", "bad_host", "git.example.test/unit/repo_name"),
        ("unit/public", "git_hub.com", "unknown"),
        ("unit/public", "Kithub.com", "unknown"),
        ("unit/public", "", "unknown"),
        ("unit/public", "git.example.test\n", "unknown"),
        ("unit/public", ".github.com", "unknown"),
        ("https://git_hub.com/unit/public", "github.com", "unknown"),
        ("git@github..com:unit/public.git", "github.com", "unknown"),
        ("github.com/unit/bad name", "github.com", "unknown"),
        ("github.com/unit/public/extra", "github.com", "unknown"),
        ("unknown", "github.com", "unknown"),
    ],
)
def test_repository_normalization_validates_host_at_resolution(value, host, expected):
    assert gate.normalize_repository(value, host) == expected


@pytest.mark.parametrize("level", range(1, 6))
def test_classes_block_with_masked_diagnostics(synthetic_opsec, level):
    (synthetic_opsec / "rules.json").write_text(json.dumps(synthetic_rules(level=level)))
    with pytest.raises(gate.PublishBlocked) as error:
        gate.check_texts("github.com/unit/public", [TOKEN])
    assert f"class={level}" in str(error.value)
    assert "rule=synthetic-rule" in str(error.value)
    assert "field=text[1] line=1" in str(error.value)
    assert TOKEN not in str(error.value)


@pytest.mark.parametrize(
    "rule,blocks",
    [
        ("6-quote-attribution", True),
        ("6-reported-speech", True),
        ("6-personal-details", True),
        ("6-personal-attribution", False),
    ],
)
def test_class6_policy(synthetic_opsec, rule, blocks):
    (synthetic_opsec / "rules.json").write_text(json.dumps(synthetic_rules(rule=rule, level=6)))
    if blocks:
        with pytest.raises(gate.PublishBlocked):
            gate.check_texts("github.com/unit/public", [TOKEN])
    else:
        gate.check_texts("github.com/unit/public", [TOKEN])


@pytest.mark.parametrize("failure", ["missing", "rules", "exception", "schema"])
def test_fail_closed_and_no_private_exception_text(synthetic_opsec, failure, capsys):
    if failure == "missing":
        synthetic_opsec = synthetic_opsec / "absent"
    elif failure == "rules":
        (synthetic_opsec / "rules.json").write_text("not-json")
    elif failure == "exception":
        (synthetic_opsec / "matcher.py").write_text(
            f"def scan_text(*args):\n print({TOKEN!r})\n raise RuntimeError({TOKEN!r})\n"
        )
    else:
        (synthetic_opsec / "matcher.py").write_text('def scan_text(*args):\n return [{"unrecognized": 1}]\n')
    with pytest.raises(gate.PublishBlocked) as error:
        gate.check_texts("github.com/unit/public", ["clean"], tooling=synthetic_opsec)
    assert TOKEN not in str(error.value) + capsys.readouterr().out + capsys.readouterr().err


def test_unreadable_rules(synthetic_opsec, monkeypatch):
    original = Path.read_bytes

    def read(path):
        if path == synthetic_opsec / "rules.json":
            raise PermissionError(TOKEN)
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(gate.PublishBlocked, match="unavailable"):
        gate.check_texts("github.com/unit/public", ["clean"])


def test_private_exemption_and_unknown_closed(tmp_path):
    gate.check_texts("github.com/unit/private", [TOKEN], tooling=tmp_path)
    with pytest.raises(gate.PublishBlocked):
        gate.check_texts("unknown", [TOKEN], tooling=tmp_path)


def test_override_consumed_once_logged_privately(synthetic_opsec, tmp_path):
    env = {"LU_OPSEC_OVERRIDE": "synthetic false positive"}
    log = tmp_path / "state/overrides.jsonl"
    gate.check_texts("github.com/unit/public", [TOKEN], environment=env, log_path=log)
    assert "LU_OPSEC_OVERRIDE" not in env
    record = json.loads(log.read_text())
    assert record["rule_ids"] == ["synthetic-rule"]
    assert record["destination"] == "github.com/unit/public"
    assert record["reason"] == "synthetic false positive"
    assert "timestamp" in record and TOKEN not in log.read_text()
    with pytest.raises(gate.PublishBlocked, match="blocked"):
        gate.check_texts("github.com/unit/public", [TOKEN], environment=env, log_path=log)
    with pytest.raises(gate.PublishBlocked, match="already consumed"):
        gate.check_texts(
            "github.com/unit/public", [TOKEN], environment={"LU_OPSEC_OVERRIDE": record["reason"]}, log_path=log
        )


def test_override_log_failure_refuses(synthetic_opsec, tmp_path):
    target = tmp_path / "not-a-directory"
    target.write_text("clean")
    with pytest.raises(gate.PublishBlocked, match="log unavailable"):
        gate.check_texts(
            "github.com/unit/public", [TOKEN], environment={"LU_OPSEC_OVERRIDE": "reason"}, log_path=target / "log"
        )


def test_direct_review_publisher_blocks_before_send(synthetic_opsec):
    from scripts.fleet_comms.review_publisher import post_commit_status, post_pr_comment

    for call in [
        lambda: post_pr_comment(repository="unit/public", pr_number=1, body=TOKEN, runner=send),
        lambda: post_commit_status(
            repository="unit/public", head_sha="a" * 40, state="success", context="unit", description=TOKEN, runner=send
        ),
    ]:

        def send(*args, **kwargs):
            pytest.fail("outbound call")

        with pytest.raises(
            __import__("scripts.fleet_comms.review_publisher", fromlist=["ReviewPublisherError"]).ReviewPublisherError,
            match="publish_blocked",
        ):
            call()


def test_child_environments_strip_override_and_keep_path(monkeypatch):
    from scripts import delegate
    from scripts.agent_runtime import env_sanitize

    monkeypatch.setenv("LU_OPSEC_OVERRIDE", "inherited")
    env = delegate._pinned_worker_venv_env({"PATH": os.defpath, "LU_OPSEC_OVERRIDE": "inherited"})
    assert "LU_OPSEC_OVERRIDE" not in env
    assert Path(env["PATH"].split(os.pathsep)[0]).name == "shims"
    monkeypatch.setattr(env_sanitize, "_isolated_git_env", lambda *a, **k: {})
    assert "LU_OPSEC_OVERRIDE" not in env_sanitize.build_agent_env(
        provider="codex", overrides={"LU_OPSEC_OVERRIDE": "inherited"}
    )


def test_budget_median_20_10kb_bodies(synthetic_opsec):
    timings = []
    for _ in range(20):
        start = time.perf_counter()
        gate.check_texts("github.com/unit/public", ["a" * 10_240])
        timings.append((time.perf_counter() - start) * 1000)
    median = statistics.median(timings)
    print(f"checker median 20 x 10KB: {median:.3f} ms")
    assert median < 200


def test_real_matcher_contract_when_available():
    path = real_tooling()
    matcher, identities, blocked = gate._load_matcher(path)
    assert blocked and blocked <= {rule for rule, level in identities.items() if level == 6}
    # Real scanner implementation with synthetic rules: no private pattern/text is exported.
    synthetic = type(matcher)(synthetic_rules())
    hits = synthetic.scan(TOKEN)
    assert len(hits) == 1
    assert hits[0].rule_id == "synthetic-rule" and hits[0].class_id == 1
    assert hits[0].span == (0, len(TOKEN))
    assert gate._scan(TOKEN, (synthetic, {"synthetic-rule": 1}, set())) == [
        {"rule_id": "synthetic-rule", "class": 1, "start": 0, "line": 1}
    ]


def test_real_matcher_budget_median_20_10kb_bodies():
    path = real_tooling()
    timings = []
    for _ in range(20):
        start = time.perf_counter()
        gate.check_texts("github.com/unit/public", ["a" * 10_240], tooling=path, environment={})
        timings.append((time.perf_counter() - start) * 1000)
    median = statistics.median(timings)
    print(f"real matcher median 20 x 10KB: {median:.3f} ms")
    assert median < 200


def test_private_write_leaves_inherited_override_unclaimed(synthetic_opsec, tmp_path):
    reason = "synthetic private command"
    log = tmp_path / "state/overrides.jsonl"
    for _ in range(2):
        env = {"LU_OPSEC_OVERRIDE": reason}
        gate.check_texts("github.com/unit/private", [TOKEN], environment=env, log_path=log)
        assert "LU_OPSEC_OVERRIDE" not in env
    assert not log.parent.exists()
    gate.check_texts("github.com/unit/public", [TOKEN], environment={"LU_OPSEC_OVERRIDE": reason}, log_path=log)
    assert len(log.read_text().splitlines()) == 1


# A command may publish several texts under one parent-scoped reason (#9678).
def test_override_then_clean_publish_both_succeed_with_one_log_entry(synthetic_opsec, tmp_path):
    reason = "synthetic false positive"
    log = tmp_path / "state/overrides.jsonl"
    gate.check_texts("github.com/unit/public", [TOKEN], environment={"LU_OPSEC_OVERRIDE": reason}, log_path=log)
    env = {"LU_OPSEC_OVERRIDE": reason}
    gate.check_texts("github.com/unit/public", ["VERDICT: APPROVED unit review"], environment=env, log_path=log)
    assert "LU_OPSEC_OVERRIDE" not in env
    (row,) = [json.loads(line) for line in log.read_text().splitlines()]
    assert row["rule_ids"] == ["synthetic-rule"] and row["reason"] == reason


def test_override_covers_one_flagged_publish_across_clean_ones(synthetic_opsec, tmp_path):
    reason = "synthetic false positive"
    log = tmp_path / "state/overrides.jsonl"
    for text in ("clean", TOKEN, "clean"):
        gate.check_texts("github.com/unit/public", [text], environment={"LU_OPSEC_OVERRIDE": reason}, log_path=log)
    with pytest.raises(gate.PublishBlocked, match="already consumed"):
        gate.check_texts("github.com/unit/public", [TOKEN], environment={"LU_OPSEC_OVERRIDE": reason}, log_path=log)
    assert len(log.read_text().splitlines()) == 1


def test_clean_publish_without_override_logs_nothing(synthetic_opsec, tmp_path):
    log = tmp_path / "state/overrides.jsonl"
    gate.check_texts("github.com/unit/public", ["clean"], environment={}, log_path=log)
    assert not log.parent.exists()


def test_clean_publish_with_override_neither_logs_nor_claims(synthetic_opsec, tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "_record_override", lambda *a, **k: pytest.fail("override claimed for clean text"))
    log = tmp_path / "state/overrides.jsonl"
    env = {"LU_OPSEC_OVERRIDE": "synthetic unused"}
    gate.check_texts("github.com/unit/public", ["clean"], environment=env, log_path=log)
    assert "LU_OPSEC_OVERRIDE" not in env and not log.parent.exists()


def test_clean_publish_with_override_needs_no_log(synthetic_opsec, tmp_path):
    target = tmp_path / "not-a-directory"
    target.write_text("clean")
    gate.check_texts(
        "github.com/unit/public", ["clean"], environment={"LU_OPSEC_OVERRIDE": "reason"}, log_path=target / "log"
    )


# One override per command across processes (#9681); multi-process flows are in tests/opsec/.
# probe ROOT REASON [set] [child]: prints its pid and command keys; "set" sets the
# override in its own environment first, "child" adds a child probe's output.
KEY_PROBE = """
import json, os, subprocess, sys
sys.path.insert(0, sys.argv[1])
from scripts.opsec import prepublish as gate
if "set" in sys.argv[3:]:
    os.environ[gate.OVERRIDE] = sys.argv[2]
out = {"pid": os.getpid(), "keys": gate.command_keys(sys.argv[2])}
if "child" in sys.argv[3:]:
    child = subprocess.run([sys.executable, *sys.argv[:3]], capture_output=True, text=True, check=True)
    out["child"] = json.loads(child.stdout)
print(json.dumps(out))
"""


@pytest.fixture
def key_probe(tmp_path):
    probe = tmp_path / "key_probe.py"
    probe.write_text(KEY_PROBE)
    return str(probe)


def _key_pid(key):
    return int(key.split(":")[1])


def test_every_program_of_a_command_line_names_the_shell_that_set_the_override(key_probe):
    """bash runs the last program in place of itself: it still shares a key with its sibling."""
    reason = "synthetic: reason"
    line = 'export LU_OPSEC_OVERRIDE="$1"; echo "$$"; "$2" "$3" "$4" "$1" child; "$2" "$3" "$4" "$1"'
    result = subprocess.run(
        ["bash", "-c", line, "bash", reason, sys.executable, key_probe, str(ROOT)],
        env={"PATH": os.defpath},
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    shell, first, last = result.stdout.splitlines()
    first, last = json.loads(first), json.loads(last)
    # The first program inherited the override from the shell, which set it.
    assert [_key_pid(key) for key in first["keys"]] == [first["pid"], int(shell)]
    assert first["child"]["keys"] == first["keys"]
    # The last program is the shell's process now: its inheritor key is the shell's key.
    assert last["pid"] == int(shell) and last["keys"][0] == first["keys"][1]


def test_a_program_that_sets_the_override_itself_is_the_command(key_probe):
    result = subprocess.run(
        [sys.executable, key_probe, str(ROOT), "synthetic reason", "set", "child"],
        env={"PATH": os.defpath},
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    probe = json.loads(result.stdout)
    assert [_key_pid(key) for key in probe["keys"]] == [probe["pid"]]
    assert probe["child"]["keys"][1] == probe["keys"][0]
    assert _key_pid(probe["child"]["keys"][0]) == probe["child"]["pid"]


def test_an_override_set_in_this_process_claims_once_for_this_process(synthetic_opsec, tmp_path):
    reason = "synthetic false positive"
    assert [_key_pid(key) for key in gate.command_keys(reason)] == [os.getpid()]
    log = tmp_path / "state/overrides.jsonl"
    gate.check_texts("github.com/unit/public", [TOKEN], environment={gate.OVERRIDE: reason}, log_path=log)
    with pytest.raises(gate.PublishBlocked, match="already consumed"):
        gate.check_texts("github.com/unit/public", [TOKEN], environment={gate.OVERRIDE: reason}, log_path=log)


def _fake_processes(monkeypatch, table):
    """table: pid -> (parent, start time, carries); this process is pid 100."""
    monkeypatch.setattr(gate.os, "getpid", lambda: 100)
    monkeypatch.setattr(gate, "_process", lambda pid, assignment: table[pid])


def test_the_setter_and_the_outermost_inheritor_are_the_keys(monkeypatch):
    _fake_processes(monkeypatch, {100: (90, 30, True), 90: (80, 20, True), 80: (70, 10, False)})
    assert [key.split(":", 1)[1] for key in gate.command_keys("reason")] == ["90:20", "80:10"]


@pytest.mark.parametrize(
    "table",
    [
        pytest.param({100: (90, 30, True), 90: (80, 40, False)}, id="parent-started-after-its-child"),
        pytest.param({100: (1, 30, True)}, id="inherited-from-init"),
        pytest.param({100: (0, 30, True)}, id="top-of-a-pid-namespace"),
        pytest.param({100: (90, 30, True)}, id="unreadable-parent"),
        pytest.param({100: (90, 30, True), 90: (100, 30, True)}, id="cycle"),
    ],
)
def test_an_undeterminable_command_refuses_the_flagged_publish(monkeypatch, synthetic_opsec, tmp_path, table):
    _fake_processes(monkeypatch, table)
    log = tmp_path / "state/overrides.jsonl"
    with pytest.raises(gate.PublishBlocked, match="unidentifiable"):
        gate.check_texts("github.com/unit/public", [TOKEN], environment={gate.OVERRIDE: "reason"}, log_path=log)
    assert not log.exists() and not list(log.parent.glob("consumed-*"))


def test_without_proc_a_flagged_publish_is_refused_and_a_clean_one_sent(monkeypatch, synthetic_opsec, tmp_path):
    """Non-Linux hosts or an unreadable /proc: the command is unidentifiable."""
    monkeypatch.setattr(gate, "PROC", tmp_path / "no-proc")
    log = tmp_path / "state/overrides.jsonl"
    with pytest.raises(gate.PublishBlocked, match="unidentifiable"):
        gate.check_texts("github.com/unit/public", [TOKEN], environment={gate.OVERRIDE: "reason"}, log_path=log)
    gate.check_texts("github.com/unit/public", ["clean"], environment={gate.OVERRIDE: "reason"}, log_path=log)
    assert not log.exists()


def test_a_pid_reused_while_it_is_read_is_refused(monkeypatch, tmp_path):
    """The start time is read on both sides of the environment."""
    proc = tmp_path / "proc"
    (proc / "7").mkdir(parents=True)
    (proc / "7/environ").write_bytes(b"LU_OPSEC_OVERRIDE=reason\0")
    starts = iter(["5", "6", "5", "5", "5", "5"])

    def read_bytes(path):
        if path.name == "stat":
            return f"7 (a) b) S 3 {' '.join(['0'] * 17)} {next(starts)} 0".encode()
        return original(path)

    original = Path.read_bytes
    monkeypatch.setattr(gate, "PROC", proc)
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    with pytest.raises(LookupError):
        gate._process(7, b"LU_OPSEC_OVERRIDE=reason")
    assert gate._process(7, b"LU_OPSEC_OVERRIDE=reason") == (3, 5, True)
    assert gate._process(7, b"LU_OPSEC_OVERRIDE=other") == (3, 5, False)


def test_internal_lookups_receive_no_override(monkeypatch, tmp_path):
    from scripts.opsec import gh_snapshot

    monkeypatch.setenv(gate.OVERRIDE, "reason")
    seen = []

    def reader(argv, **kwargs):
        seen.append((argv[0], kwargs["env"]))
        return subprocess.CompletedProcess(argv, 0, f"{tmp_path}/.git\n", "")

    monkeypatch.setattr(gate.subprocess, "run", reader)
    gate.primary_root(tmp_path)
    gh_snapshot.repository(tmp_path, dict(os.environ), reader=reader)
    gate.checked_run(["gh", "pr", "list", "--json", "number"], runner=reader, env=dict(os.environ))
    published = gate.publish_environment(dict(os.environ))
    assert [name for name, _ in seen] == ["git", "git", "gh"]
    for env in [*(env for _, env in seen), published]:
        assert gate.OVERRIDE not in env


def test_nondefault_public_catalog_entry_is_not_private(monkeypatch):
    monkeypatch.setattr(
        gate, "catalog", lambda: {"unit": {"github": "unit/public", "default": False, "role": "public-monorepo"}}
    )
    assert not gate.is_private("github.com/unit/public")


@pytest.mark.parametrize(
    "path",
    [
        "scripts/delegate.py",
        "scripts/review/record_cf_verdict.py",
        "scripts/orchestration/dispatch_settle.py",
        "scripts/orchestration/task_closeout.py",
        "scripts/orchestration/issue_stream_audit.py",
        "scripts/orchestration/merge_queue_keeper.py",
    ],
)
def test_publish_consumer_cli_help_runs_as_script(path):
    result = subprocess.run(
        [sys.executable, str(ROOT / path), "--help"], cwd=ROOT, capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, result.stderr.splitlines()[-1:] if result.stderr else ""
    assert "usage:" in result.stdout.lower()


@pytest.mark.parametrize("group", ["issue", "pr"])
@pytest.mark.parametrize("verb", ["close", "reopen"])
def test_short_comment_value_never_classifies_destination(group, verb, synthetic_opsec):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", group, verb, "1", "-c", "https://github.com/unit/private/issues/1"],
            env={"GH_REPO": "unit/public"},
            runner=lambda *a, **k: pytest.fail("send"),
        )


@pytest.mark.parametrize("command", ["printf hello", "git status", "printf '%s' gh", "echo ghastly"])
def test_non_gh_hook_preserves_prefix_allow_rules(command, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location(
        "non_gh_hook", ROOT / "agents_extensions/shared/hooks/guard-public-github-text.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(
        sys, "stdin", __import__("io").StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}))
    )
    assert module.main() == 0
    assert capsys.readouterr().out == ""


def test_unknown_policy_id_fails_at_load_even_without_hits(synthetic_opsec, monkeypatch, tmp_path):
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"class6_block_ids": ["absent-id"]}))
    monkeypatch.setattr(gate, "POLICY", policy)
    with pytest.raises(gate.PublishBlocked, match="load refused"):
        gate._load_matcher(synthetic_opsec)


def test_class6_block_override_consulted(synthetic_opsec, tmp_path):
    (synthetic_opsec / "rules.json").write_text(json.dumps(synthetic_rules(rule="6-quote-attribution", level=6)))
    gate.check_texts(
        "github.com/unit/public",
        [TOKEN],
        environment={"LU_OPSEC_OVERRIDE": "synthetic policy exception"},
        log_path=tmp_path / "override.jsonl",
    )
    assert json.loads((tmp_path / "override.jsonl").read_text())["rule_ids"] == ["6-quote-attribution"]


def test_nonagent_shims_directory_can_supply_real_gh(tmp_path):
    path = tmp_path / "shims" / "gh"
    path.parent.mkdir()
    path.write_text("#!/bin/sh\nexit 0\n")
    path.chmod(0o755)
    assert gate.real_gh({"PATH": str(path.parent)}) == str(path)


def test_cli_block_is_typed_without_traceback(capsys):
    @gate.publication_cli()
    def command():
        raise gate.PublishBlocked("synthetic refusal")

    assert command() == 2
    assert capsys.readouterr().err == "publish_blocked: synthetic refusal\n"


@pytest.mark.parametrize(
    "module,function,args,error_type",
    [
        ("scripts.orchestration.dispatch_settle", "_run", (["gh", "pr", "merge", "1"],), ValueError),
        ("scripts.review.record_cf_verdict", "_run_json", (["gh", "pr", "merge", "1"],), RuntimeError),
        ("scripts.practice_deck.publish", "ensure_release", ("unit", "unit/public"), RuntimeError),
        ("scripts.open_dataset.publish", "ensure_release", ("unit", "unit/public"), RuntimeError),
        ("scripts.delegate", "_create_auto_finalize_pr", (), RuntimeError),
    ],
)
def test_publishers_translate_policy_refusals(module, function, args, error_type, monkeypatch, tmp_path):
    import importlib

    publisher = importlib.import_module(module)

    def refuse(*args, **kwargs):
        raise gate.PublishBlocked("synthetic refusal")

    monkeypatch.setattr(publisher, "request_run", refuse)
    kwargs = {}
    if module == "scripts.delegate":
        args = (tmp_path,)
        kwargs = {"branch": "unit", "base_branch": "main", "title": "clean", "body": "clean"}
    with pytest.raises(error_type, match=r"publish_blocked:.*synthetic refusal") as error:
        getattr(publisher, function)(*args, **kwargs)
    assert not isinstance(error.value, gate.PublishBlocked)
    assert error.value.__suppress_context__


def test_keeper_and_closeout_native_refusal_types(monkeypatch, tmp_path):
    from scripts.orchestration import merge_queue_keeper as keeper
    from scripts.orchestration import task_closeout as closeout
    from scripts.orchestration import task_lifecycle

    def refuse(*args, **kwargs):
        raise gate.PublishBlocked("synthetic refusal")

    for publisher in [keeper, closeout]:
        monkeypatch.setattr(publisher, "request_run", refuse)
    with pytest.raises(keeper.KeeperError, match="publish_blocked"):
        keeper.GitHub(tmp_path, "unit/public").enqueue(1, "a" * 40)
    for runner in [None, lambda *a: pytest.fail("outbound")]:
        with pytest.raises(task_lifecycle.LifecycleError, match="publish_blocked"):
            closeout.GhGitHubAdapter(tmp_path, runner=runner).enqueue_pr("unit/public", 1)


def test_bridge_comment_refusal_is_rendered_and_returns_false(monkeypatch, capsys):
    from scripts.ai_agent_bridge import _github

    def refuse(*args, **kwargs):
        raise gate.PublishBlocked("synthetic refusal")

    monkeypatch.setattr(_github, "request_run", refuse)
    assert not _github._gh_comment(1, "clean")
    assert "publish_blocked: synthetic refusal" in capsys.readouterr().out


@pytest.mark.parametrize(
    "command",
    [
        "printf hello\ngh issue list",
        "cat <<'EOF'\nhello\nEOF\ngh issue list",
        "if gh issue list; then printf hello; fi",
        "time gh issue list",
        "timeout 30 gh issue list",
        "timeout --signal TERM 30s gh issue list",
        "printf 1 | xargs gh issue view",
        "bash -c 'gh issue list'",
        "bash -lc 'gh issue list'",
    ],
)
def test_hook_detects_wrapped_and_newline_gh(command, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location(
        "wrapped_hook", ROOT / "agents_extensions/shared/hooks/guard-public-github-text.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("PATH", os.defpath)
    monkeypatch.setattr(
        sys, "stdin", __import__("io").StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}))
    )
    assert module.main() == 0
    assert "export PATH=" in json.loads(capsys.readouterr().out)["hookSpecificOutput"]["updatedInput"]["command"]


def test_no_text_override_unclaimed_without_loading_matcher(monkeypatch, tmp_path):
    monkeypatch.setattr(gate, "private_tooling", lambda: pytest.fail("matcher for empty set"))
    log = tmp_path / "state/override.jsonl"
    env = {"LU_OPSEC_OVERRIDE": "synthetic empty set"}
    gate.check_texts("github.com/unit/public", [], environment=env, log_path=log)
    assert "LU_OPSEC_OVERRIDE" not in env and not log.parent.exists()


# Earlier raw-public forms are now refused, including clean payloads.
PRIOR_RAW_WRITES = [
    ["issue", "create", "--title", "{text}", "--body", "clean"],
    ["pr", "create", "--title", "clean", "--body", "{text}"],
    ["issue", "edit", "1", "--title={text}"],
    ["pr", "edit", "1", "-t{text}"],
    ["issue", "comment", "1", "--body-file", "@file"],
    ["pr", "comment", "1", "-F", "-"],
    ["pr", "review", "1", "--comment", "--body-file=@file"],
    ["issue", "close", "1", "--comment", "{text}"],
    ["pr", "close", "1", "--comment", "{text}"],
    ["pr", "merge", "1", "--subject", "{text}", "--body", "clean"],
    ["pr", "merge", "1", "--subject", "clean", "--body", "{text}"],
    ["api", "repos/unit/public/issues", "-f", "title={text}"],
    ["api", "repos/unit/public/issues/1/comments", "-F", "body=@file"],
    ["api", "repos/unit/public/pulls/1/reviews", "--input", "@json"],
    ["api", "repos/unit/public/pulls/1/reviews", "--field", "comments[][body]={text}"],
    ["api", "repos/unit/public/pulls/comments/1", "-XPATCH", "--input", "-"],
    [
        "api",
        "graphql",
        "-f",
        'query=mutation($body:String!){addComment(input:{body:$body,subjectId:"unit"}){clientMutationId}}',
        "-f",
        "body={text}",
    ],
    ["api", "graphql", "--input", "@graphql"],
    ["api", "graphql", "-F", "query=@gql"],
    ["release", "create", "unit-tag", "--title", "clean", "--notes-file", "@file"],
    ["release", "edit", "unit-tag", "--notes", "{text}"],
    ["api", "repos/unit/public/issues", "--input", "-"],
    ["api", "-X", "GET", "repos/unit/public/issues", "--input", "-"],
    ["issue", "create"],
    ["pr", "comment", "1", "--editor"],
    ["pr", "create", "--editor", "--title", "clean", "--body", "clean"],
    ["api", "graphql", "-f", "query=unresolved"],
    ["repo", "edit", "unit/public", "--description", "SENTINEL-HOST-TOKEN"],
    ["project", "item-create", "1", "--title", "SENTINEL-HOST-TOKEN", "--body", "clean"],
    ["project", "item-create", "1", "--title", "clean", "--body", "SENTINEL-HOST-TOKEN"],
    ["api", "repos/unit/public/issues/1/comments", "-if", "body=SENTINEL-HOST-TOKEN"],
    ["repo", "edit", "unit/public", "--description", "clean"],
    ["project", "item-create", "1", "--title", "clean", "--body", "clean"],
    ["api", "repos/unit/public/issues/1/comments", "-if", "body=clean"],
    ["issue", "-R", "unit/public", "comment", "1", "--body", "SENTINEL-HOST-TOKEN"],
    ["issue", "--repo=unit/public", "comment", "1", "--body", "SENTINEL-HOST-TOKEN"],
    ["pr", "--repo", "unit/public", "comment", "1", "--body", "SENTINEL-HOST-TOKEN"],
    ["issue", "-R", "unit/public", "create", "--title", "t", "--body", "SENTINEL-HOST-TOKEN"],
    ["pr", "merge", "1", "-m", "-b", "SENTINEL-HOST-TOKEN"],
    ["pr", "merge", "1", "-m", "-t", "SENTINEL-HOST-TOKEN"],
    ["pr", "merge", "1", "-r", "-t", "SENTINEL-HOST-TOKEN"],
    ["pr", "merge", "1", "-m"],
    ["pr", "merge", "1", "-r"],
    ["pr", "review", "1", "-r", "-b", "text"],
    ["release", "create", "unit-tag", "-p", "-n", "notes", "-t", "title"],
    ["release", "edit", "unit-tag", "--draft=false"],
    ["issue", "edit", "1", "--remove-milestone"],
    ["repo", "edit", "--add-topic", "unit-topic"],
    ["repo", "edit", "-d", "clean"],
    ["pr", "merge", "1", "--squash"],
    ["issue", "edit", "1", "--milestone", "123"],
    ["pr", "merge", "1", "--match-head-commit", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],
    ["issue", "edit", "1", "--add-label", "SENTINEL-HOST-TOKEN"],
    ["issue", "edit", "1", "--milestone", "SENTINEL-HOST-TOKEN"],
    ["label", "create", "SENTINEL-HOST-TOKEN"],
    ["repo", "create", "unit/public", "--description", "SENTINEL-HOST-TOKEN"],
    ["project", "create", "--title", "SENTINEL-HOST-TOKEN"],
    ["project", "edit", "1", "--description", "SENTINEL-HOST-TOKEN"],
    ["unit-unknown", "unit-write", "--unknown", "SENTINEL-HOST-TOKEN"],
    ["pr", "unit-unknown", "--unknown=SENTINEL-HOST-TOKEN"],
    ["issue", "comment", "--unknown", "https://github.com/unit/private/issues/1", "--body", "SENTINEL-HOST-TOKEN"],
    ["issue", "comment", "--assignee", "https://github.com/unit/private/issues/1", "--body", "SENTINEL-HOST-TOKEN"],
    ["api", "repos/unit/public/issues", "-pfbody=SENTINEL-HOST-TOKEN"],
    ["api", "repos/unit/public/issues", "-pifbody=SENTINEL-HOST-TOKEN"],
    ["unit-unknown", "write"],
    ["secret", "set", "unit-name"],
]


@pytest.mark.parametrize("args", PRIOR_RAW_WRITES)
def test_prior_round_raw_writes_never_send(args, tmp_path):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", *args],
            cwd=tmp_path,
            env={"GH_REPO": "unit/public"},
            runner=lambda *a, **k: pytest.fail("outbound request"),
        )


def real_tooling():
    import yaml

    override = os.environ.get("LU_OPSEC_TEST_TOOLING")
    repos = yaml.safe_load((ROOT / "scripts/config/fleet_repos.yaml").read_text())["repos"]
    path = (
        Path(override)
        if override
        else gate.primary_root().parent / repos["infra-private"]["local_name"] / "tools/public_opsec_scan"
    )
    if not (path / "matcher.py").exists() or not (path / "rules.json").exists():
        pytest.skip("private matcher/rules absent; provide detached origin/main tooling via LU_OPSEC_TEST_TOOLING")
    return path


@pytest.mark.parametrize(
    "ignorable",
    [
        "\u200b",  # Zero-width space (Cf)
        "\u200c",  # Zero-width non-joiner (Cf)
        "\u200d",  # Zero-width joiner (Cf)
        "\xad",  # Soft hyphen (Cf)
        "\u200e",  # Left-to-right mark (Cf)
        "\u202e",  # Right-to-left override (Cf)
        "\u2065",  # Unassigned in General Punctuation / controls (Cn)
        "\u2066",  # Left-to-right isolate (Cf)
        "\u202b",  # Right-to-left embedding (Cf)
        "\u034f",  # Combining grapheme joiner (Mn)
        "\ufe0f",  # Variation selector 16 (Mn)
        "\U000e0000",  # Plane 14 tag start
        "\U000e0080",  # Plane 14 unassigned tag
        "\U000e0100",  # Variation selector 17 (Mn)
        "\U000e01f0",  # Plane 14 unassigned VS
        "\U000e0fff",  # Plane 14 ignorable end
        "\u180b",  # Mongolian free variation selector 1 (Mn)
        "\u3164",  # Hangul filler (Lo)
        "\u115f",  # Hangul choseong filler (Lo)
        "\u1160",  # Hangul jungseong filler (Lo)
        "\uffa0",  # Halfwidth Hangul filler (Lo)
        "\u2800",  # Braille pattern blank (So)
    ],
)
def test_synthetic_normalization_ignorables(synthetic_opsec, ignorable):
    (synthetic_opsec / "rules.json").write_text(json.dumps(synthetic_rules(rule="synthetic-rule", level=1)))
    obfuscated = TOKEN[:4] + ignorable + TOKEN[4:]

    # Verify failing-before on raw unnormalized matcher
    spec = importlib.util.spec_from_file_location("_matcher", synthetic_opsec / "matcher.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    matcher = module.Matcher(json.loads((synthetic_opsec / "rules.json").read_text()))
    assert not matcher.scan(obfuscated), f"expected raw {obfuscated!r} to evade unnormalized matcher"

    # Verify passing-after via prepublish check_texts
    with pytest.raises(gate.PublishBlocked) as error:
        gate.check_texts("github.com/unit/public", [obfuscated])
    assert "class=1" in str(error.value)
    assert "rule=synthetic-rule" in str(error.value)


@pytest.mark.parametrize(
    "raw_target,obfuscated",
    [
        ("TOKEN-1234", "ＴＯＫＥＮ-1234"),  # Fullwidth Latin
        ("TOKEN-1234", "TOKEN-１２３４"),  # Fullwidth digits
        ("TOKEN-1234", "TOKEN-١٢٣٤"),  # Arabic-Indic digits
        ("TOKEN-1234", "TOKEN-۱۲۳۴"),  # Eastern Arabic digits
        ("TOKEN-1234", "TOKEN-१२३४"),  # Devanagari digits
        ("TOKEN-1234", "TOKEN-①②③④"),  # Circled digits
        ("TOKEN-1234", "TOKEN-𝟏𝟐𝟑𝟒"),  # Mathematical bold digits
        ("TOKEN-1234", "TOKEN-𝟙𝟚𝟛𝟜"),  # Mathematical double-struck digits
        ("TOKEN-1234", "TOKEN-𝟣𝟤𝟥𝟦"),  # Mathematical sans-serif digits
    ],
)
def test_synthetic_normalization_fullwidth_and_decimal_digits(synthetic_opsec, raw_target, obfuscated):
    (synthetic_opsec / "rules.json").write_text(
        json.dumps(synthetic_rules(rule="synthetic-digits", level=2, pattern=raw_target))
    )

    # Raw obfuscated string evades unnormalized matcher
    spec = importlib.util.spec_from_file_location("_matcher", synthetic_opsec / "matcher.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    matcher = module.Matcher(json.loads((synthetic_opsec / "rules.json").read_text()))
    assert not matcher.scan(obfuscated), f"expected raw {obfuscated!r} to evade unnormalized matcher"

    # Prepublish normalizes and blocks
    with pytest.raises(gate.PublishBlocked) as error:
        gate.check_texts("github.com/unit/public", [obfuscated])
    assert "class=2" in str(error.value)
    assert "rule=synthetic-digits" in str(error.value)


@pytest.mark.parametrize(
    "token",
    [
        "ghp_1234567890abcdefghijklmnopqrstuvwxyz12",
        "github_pat_11AAAAAAA01234567890abcdefghijklmnopqrstuvwxyz",
        "gho_1234567890abcdefghijklmnopqrstuvwxyz12",
        "ghu_1234567890abcdefghijklmnopqrstuvwxyz12",
        "ghs_1234567890abcdefghijklmnopqrstuvwxyz12",
        "ghr_1234567890abcdefghijklmnopqrstuvwxyz12",
        "sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890",
        "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890",
        "sk-1234567890abcdefghijklmnopqrstuvwxyz123456",
        "xoxb-" + "1234567890-abcdefghijklmnopqrstuvwxyz",
        "AKIA" + "IOSFODNN7EXAMPLE",
        "-----BEGIN " + "RSA PRIVATE KEY-----",
        "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
        "-----BEGIN " + "PRIVATE KEY-----",
        "ghp_1234\u034f567890abcdefghijklmnopqrstuvwxyz12",
        "ghp_1234\u200b567890abcdefghijklmnopqrstuvwxyz12",
        "ghp_1234\ufe0f567890abcdefghijklmnopqrstuvwxyz12",
    ],
)
def test_credential_tokens_are_blocked_even_with_synthetic_rules(synthetic_opsec, token):
    with pytest.raises(gate.PublishBlocked) as error:
        gate.check_texts("github.com/unit/public", [token])
    assert "class=5" in str(error.value)
    assert "rule=5-credential-token" in str(error.value)
    assert "field=text[1] line=1" in str(error.value)
    assert token not in str(error.value)


@pytest.mark.parametrize(
    "safe_text",
    [
        "see sk-learn-preprocessing-pipeline-docs",
        "task-sk-abcdefghijklmnopqrstuv",
        "sk-SK language model documentation",
        "regular text with -sk- infix",
    ],
)
def test_ordinary_text_with_hyphenated_sk_is_not_blocked(synthetic_opsec, safe_text):
    gate.check_texts("github.com/unit/public", [safe_text])


def test_unnormalized_rules_fail_closed_at_load(synthetic_opsec):
    rules = synthetic_rules()
    # Add a pattern with an unnormalized character that NFKC rewrites (e.g. № -> No)
    rules["1"]["patterns"].append({"id": "1-unnormalized", "regex": r"\b№\d+\b"})
    (synthetic_opsec / "rules.json").write_text(json.dumps(rules))
    with pytest.raises(gate.PublishBlocked, match="contains unnormalized characters"):
        gate._load_matcher(synthetic_opsec)


@pytest.mark.parametrize(
    "obfuscated,expected_rule,expected_class",
    [
        ("192.0.2.\u200b7", "2-ipv4", 2),  # Zero-width space
        ("192.0.2.\u200c7", "2-ipv4", 2),  # Zero-width non-joiner
        ("192.0.2.\u200d7", "2-ipv4", 2),  # Zero-width joiner
        ("192.0.2.\xad7", "2-ipv4", 2),  # Soft hyphen
        ("192.0.2.\u20657", "2-ipv4", 2),  # Unassigned in General Punctuation
        ("192.0.2.\u034f7", "2-ipv4", 2),  # Combining grapheme joiner
        ("192.0.2.\ufe0f7", "2-ipv4", 2),  # Variation selector 16
        ("192.0.2.\U000e00807", "2-ipv4", 2),  # Plane 14 tag
        ("192.0.2.\U000e01007", "2-ipv4", 2),  # Variation selector 17
        ("192.0.2.\u180b7", "2-ipv4", 2),  # Mongolian free variation selector 1
        ("192.0.2.\u31647", "2-ipv4", 2),  # Hangul filler
        ("192.0.2.\u115f7", "2-ipv4", 2),  # Hangul choseong filler
        ("192.0.2.\u11607", "2-ipv4", 2),  # Hangul jungseong filler
        ("192.0.2.\uffa07", "2-ipv4", 2),  # Halfwidth Hangul filler
        ("192.0.2.\u28007", "2-ipv4", 2),  # Braille pattern blank
        ("１９２.０.２.７", "2-ipv4", 2),  # Full-width digits
        ("１９２．０．２．７", "2-ipv4", 2),  # Full-width digits and dots
        ("١٩٢.٠.٢.٧", "2-ipv4", 2),  # Arabic-Indic digits
        ("۱۲۳.۰.۲.۷", "2-ipv4", 2),  # Eastern Arabic digits
        ("१९२.०.२.७", "2-ipv4", 2),  # Devanagari digits
        ("192.0.2.\u202e7", "2-ipv4", 2),  # Right-to-left override
        ("192.0.2.\u200e7", "2-ipv4", 2),  # Left-to-right mark
        ("192.0.2.\u20667", "2-ipv4", 2),  # Left-to-right isolate
        ("192.0.2.\u202b7", "2-ipv4", 2),  # Right-to-left embedding
        ("𝟙𝟡𝟚.𝟘.𝟚.𝟟", "2-ipv4", 2),  # Mathematical double-struck homoglyphs
        ("𝟏𝟗𝟐.𝟎.𝟐.𝟕", "2-ipv4", 2),  # Mathematical bold homoglyphs
        ("𝟣𝟫𝟤.𝟢.𝟤.𝟩", "2-ipv4", 2),  # Mathematical sans-serif homoglyphs
        ("①⑨②.⓪.②.⑦", "2-ipv4", 2),  # Circled digits
        ("／home／ops／secret", "3-absolute-path", 3),  # Full-width slashes
        ("оператор\u200b сказав: секрет", "6-uk-reported-speech", 6),  # Ukrainian operator speech with ZWSP
    ],
)
def test_unicode_normalization_hardens_scanner(obfuscated, expected_rule, expected_class):
    tooling = real_tooling()
    matcher, _identities, _blocked = gate._load_matcher(tooling)

    # Prove failing-before: raw unnormalized text completely evades the unnormalized matcher
    raw_hits = matcher.scan(obfuscated)
    assert not any(h.rule_id == expected_rule for h in raw_hits), (
        f"expected raw {obfuscated!r} to evade {expected_rule}"
    )

    # Verify passing-after: prepublish scan normalizes and blocks the obfuscated text
    with pytest.raises(gate.PublishBlocked) as error:
        gate.check_texts("github.com/unit/public", [obfuscated], tooling=tooling)
    assert f"class={expected_class}" in str(error.value)
    assert f"rule={expected_rule}" in str(error.value)


def test_absolute_path_spans_only_return_validated_offsets(synthetic_opsec):
    rules = synthetic_rules(rule="3-absolute-path", level=3, pattern=r"/unit/[a-z]+")
    rules["1"] = {"patterns": [{"id": "synthetic-rule", "regex": TOKEN}]}
    (synthetic_opsec / "rules.json").write_text(json.dumps(rules))
    text = "/unit/one " + TOKEN + " /unit/two"
    assert gate.absolute_path_spans(text) == [(0, 9), (len(text) - 9, len(text))]
    assert gate.absolute_path_spans("clean") == []


@pytest.mark.parametrize("level", [None, 2])
def test_absolute_path_spans_require_absolute_rule(synthetic_opsec, level):
    if level is not None:
        (synthetic_opsec / "rules.json").write_text(json.dumps(synthetic_rules(rule="3-absolute-path", level=level)))
    with pytest.raises(gate.PublishBlocked, match="absolute-path rule unavailable/incompatible"):
        gate.absolute_path_spans("clean")


@pytest.mark.parametrize(
    "spans",
    [
        [(0, 0)],
        [(-1, 2)],
        [(0, 100)],
        [(3, 2)],
        [(False, 2)],
        [(0, 2.0)],
        [(0, "2")],
        [(0,)],
        [(0, 1, 2)],
        [(0, 2), (1, 3)],
        [(0, 2), (0, 2)],
    ],
)
def test_absolute_path_spans_refuse_malformed_offsets(monkeypatch, spans):
    from types import SimpleNamespace

    hits = [SimpleNamespace(rule_id="3-absolute-path", class_id=3, span=span) for span in spans]
    matcher = SimpleNamespace(scan=lambda text: hits)
    monkeypatch.setattr(gate, "_load_matcher", lambda path: (matcher, {"3-absolute-path": 3}, set()))
    with pytest.raises(gate.PublishBlocked, match="result incompatible"):
        gate.absolute_path_spans("/unit/file", tooling=Path("unused"))


def test_absolute_path_spans_sort_disjoint_offsets(monkeypatch):
    from types import SimpleNamespace

    hits = [SimpleNamespace(rule_id="3-absolute-path", class_id=3, span=span) for span in [(2, 4), (0, 2)]]
    monkeypatch.setattr(
        gate, "_load_matcher", lambda path: (SimpleNamespace(scan=lambda text: hits), {"3-absolute-path": 3}, set())
    )
    assert gate.absolute_path_spans("abcd", tooling=Path("unused")) == [(0, 2), (2, 4)]


@pytest.mark.parametrize("failure", ["raise", "bad-hit", "wrong-rule", "wrong-class", "no-hits"])
def test_absolute_path_spans_refuse_failed_matcher(monkeypatch, capsys, failure):
    from types import SimpleNamespace

    def scan(text):
        print(TOKEN)
        if failure == "raise":
            raise RuntimeError(TOKEN)
        if failure == "no-hits":
            return None
        if failure == "bad-hit":
            return [object()]
        return [
            SimpleNamespace(
                rule_id="unknown" if failure == "wrong-rule" else "3-absolute-path",
                class_id=2 if failure == "wrong-class" else 3,
                span=(0, 1),
            )
        ]

    monkeypatch.setattr(gate, "_load_matcher", lambda path: (SimpleNamespace(scan=scan), {"3-absolute-path": 3}, set()))
    with pytest.raises(gate.PublishBlocked, match="result incompatible") as error:
        gate.absolute_path_spans("/unit/file", tooling=Path("unused"))
    captured = capsys.readouterr()
    assert TOKEN not in str(error.value) + captured.out + captured.err


def test_absolute_path_spans_missing_tooling_refuses(tmp_path):
    with pytest.raises(gate.PublishBlocked, match="unavailable/incompatible"):
        gate.absolute_path_spans("clean", tooling=tmp_path / "missing")


def test_absolute_path_spans_lazy_matcher_failure_is_masked(monkeypatch, capsys):
    from types import SimpleNamespace

    def scan(text):
        yield SimpleNamespace(rule_id="3-absolute-path", class_id=3, span=(0, 1))
        print(TOKEN)
        raise RuntimeError(TOKEN)

    monkeypatch.setattr(gate, "_load_matcher", lambda path: (SimpleNamespace(scan=scan), {"3-absolute-path": 3}, set()))
    with pytest.raises(gate.PublishBlocked, match="result incompatible") as error:
        gate.absolute_path_spans("/unit/file", tooling=Path("unused"))
    captured = capsys.readouterr()
    assert TOKEN not in str(error.value) + captured.out + captured.err
