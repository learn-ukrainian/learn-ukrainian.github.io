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
        {"rule_id": "synthetic-rule", "class": 1, "start": 0}
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


def test_private_write_consumes_inherited_override(tmp_path):
    reason = "synthetic private command"
    log = tmp_path / "overrides.jsonl"
    gate.check_texts("github.com/unit/private", [TOKEN], environment={"LU_OPSEC_OVERRIDE": reason}, log_path=log)
    with pytest.raises(gate.PublishBlocked, match="already consumed"):
        gate.check_texts("github.com/unit/private", [TOKEN], environment={"LU_OPSEC_OVERRIDE": reason}, log_path=log)
    assert TOKEN not in log.read_text() and json.loads(log.read_text())["rule_ids"] == []


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
            closeout.GhGitHubAdapter(tmp_path, runner=runner).arm_auto_merge("unit/public", 1)


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


def test_no_text_override_logs_without_loading_matcher(monkeypatch, tmp_path):
    monkeypatch.setattr(gate, "private_tooling", lambda: pytest.fail("matcher for empty set"))
    log = tmp_path / "override.jsonl"
    gate.check_texts(
        "github.com/unit/public", [], environment={"LU_OPSEC_OVERRIDE": "synthetic empty set"}, log_path=log
    )
    assert json.loads(log.read_text())["rule_ids"] == []


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
    ["api", "repos/unit/public/issues"],
    ["api", "-X", "GET", "repos/unit/public/issues"],
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
