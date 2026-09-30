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
from scripts.opsec.gh_snapshot import graphql_write, snapshot
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


FORMS = [
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
]


def form_args(form, text, tmp_path):
    body = tmp_path / "body"
    body.write_bytes(text.encode())
    data = tmp_path / "data"
    data.write_text(json.dumps({"body": "clean", "comments": [{"path": "unit", "body": text}]}))
    gql = 'mutation {addComment(input:{subjectId:"unit",body:' + json.dumps(text) + "}){clientMutationId}}"
    query = tmp_path / "query"
    query.write_text(gql)
    graphql = tmp_path / "graphql"
    graphql.write_text(json.dumps({"query": gql, "variables": {"body": text}}))
    replacements = {"@file": str(body), "@json": str(data), "@gql": str(query), "@graphql": str(graphql)}
    args = []
    for item in form:
        item = item.replace("{text}", text)
        for key, value in replacements.items():
            item = item.replace(key, ("@" + value) if "=@" in item and not item.startswith("--") else value)
        args.append(item)
    args.extend(["--repo", "unit/public"] if args[0] != "api" else [])
    stdin = json.dumps({"body": text}) if "--input" in args and "-" in args else text
    return args, stdin


@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("text", [TOKEN, "clean\nexact UTF-8 text é\n"])
def test_send_spy_all_write_forms(synthetic_opsec, tmp_path, monkeypatch, form, text):
    args, stdin = form_args(form, text, tmp_path)
    calls = []
    scanned = []
    original = gate.check_texts

    def check(destination, texts, **kwargs):
        scanned.extend(texts)
        return original(destination, texts, **kwargs)

    monkeypatch.setattr(gate, "check_texts", check)

    def send(argv, **kwargs):
        with snapshot(
            argv[1:], cwd=tmp_path, environment={"GH_REPO": "unit/public"}, stdin=kwargs.get("input")
        ) as frozen:
            calls.append((argv, frozen.texts))
        assert "LU_OPSEC_OVERRIDE" not in kwargs.get("env", {})
        return subprocess.CompletedProcess(argv, 0, "sent", "")

    if text == TOKEN:
        with pytest.raises(gate.PublishBlocked):
            gate.checked_run(["gh", *args], runner=send, cwd=tmp_path, input=stdin, text=True)
        assert calls == []
    else:
        gate.checked_run(["gh", *args], runner=send, cwd=tmp_path, input=stdin, text=True)
        assert len(calls) == 1
        assert calls[0][1] == scanned
        assert any(text in value for value in scanned)


@pytest.mark.parametrize(
    "query",
    [
        "query {viewer{login}}",
        "{viewer{login}}",
        'query { search(query:"mutation { sentinel }"){issueCount}}',
        "# mutation ignored\nquery Named {viewer{login}}",
        'query {search(query:"""mutation fake"""){issueCount}}',
    ],
)
def test_graphql_post_queries_are_reads(query, tmp_path):
    assert not graphql_write(query)
    calls = []
    gate.checked_run(
        ["gh", "api", "graphql", "-f", "query=" + query], cwd=tmp_path, runner=lambda args, **kwargs: calls.append(args)
    )
    assert len(calls) == 1


@pytest.mark.parametrize(
    "args",
    [
        ["issue", "view", "1"],
        ["pr", "list"],
        ["api", "repos/unit/public/issues"],
        ["api", "-X", "GET", "repos/unit/public/issues", "-f", "body=" + TOKEN],
    ],
)
def test_reads_do_not_require_matcher(args, tmp_path):
    calls = []
    gate.checked_run(["gh", *args], cwd=tmp_path, runner=lambda a, **kw: calls.append(a))
    assert len(calls) == 1


@pytest.mark.parametrize(
    "args",
    [
        ["issue", "create"],
        ["pr", "comment", "1", "--editor"],
        ["pr", "create", "--editor", "--title", "clean", "--body", "clean"],
        ["api", "graphql", "-f", "query=unresolved"],
    ],
)
def test_unresolved_write_forms_refused(args, tmp_path, synthetic_opsec):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", *args], cwd=tmp_path, env={"GH_REPO": "unit/public"}, runner=lambda *a, **k: pytest.fail("send")
        )


@pytest.mark.parametrize("source", ["repo", "url", "api", "env", "host"])
def test_destination_private_positive_only(source, tmp_path):
    args, env = ["issue", "comment", "1", "--body", TOKEN], {}
    if source == "repo":
        args += ["-R", "unit/private"]
    elif source == "url":
        args[2] = "https://github.com/unit/private/issues/1"
    elif source == "api":
        args = ["api", "repos/unit/private/issues", "-f", "body=" + TOKEN]
    else:
        env = {"GH_REPO": "unit/private", **({"GH_HOST": "unit.invalid"} if source == "host" else {})}
    if source == "host":
        with pytest.raises(gate.PublishBlocked):
            gate.checked_run(["gh", *args], cwd=tmp_path, env=env, runner=lambda *a, **k: pytest.fail("send"))
    else:
        calls = []
        gate.checked_run(["gh", *args], cwd=tmp_path, env=env, runner=lambda *a, **k: calls.append(a))
        assert len(calls) == 1


def test_file_changed_after_scan_delivers_snapshot(synthetic_opsec, tmp_path, monkeypatch):
    source = tmp_path / "body"
    source.write_bytes(b"clean\nexact\n")
    original = gate.check_texts

    def check(*args, **kwargs):
        original(*args, **kwargs)
        source.write_text(TOKEN)

    monkeypatch.setattr(gate, "check_texts", check)

    def send(args, **kwargs):
        assert Path(args[args.index("--body-file") + 1]).read_bytes() == b"clean\nexact\n"

    gate.checked_run(["gh", "issue", "comment", "1", "--repo", "unit/public", "--body-file", str(source)], runner=send)


@pytest.mark.parametrize("text", [TOKEN, "clean\nbytes\n"])
def test_real_shim_send_spy(gh_shim_sandbox, tmp_path, text):
    root, shim, _tooling = gh_shim_sandbox
    spy = tmp_path / "send"
    outbound = tmp_path / "outbound"
    spy.write_text(f"""#!{sys.executable}
import json,sys
from pathlib import Path
args=sys.argv[1:]
body=args[args.index('--body-file')+1]
Path({str(outbound)!r}).write_bytes(Path(body).read_bytes())
""")
    spy.chmod(0o755)
    body = tmp_path / "body"
    body.write_text(text)
    result = subprocess.run(
        [str(shim), "issue", "comment", "1", "--body-file", str(body)],
        cwd=root,
        env={"PATH": os.defpath, "AGENT_REAL_GH": str(spy)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    if text == TOKEN:
        assert result.returncode == 2 and not outbound.exists()
        assert "field=body-file line=1" in result.stderr and TOKEN not in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        assert outbound.read_bytes() == text.encode()


def test_hook_installs_path_and_warns_literal(synthetic_opsec, monkeypatch, capsys):
    path = ROOT / "agents_extensions/shared/hooks/guard-public-github-text.py"
    spec = importlib.util.spec_from_file_location("test_hook", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(
        sys,
        "stdin",
        __import__("io").StringIO(
            json.dumps({"tool_name": "Bash", "tool_input": {"command": "gh issue comment 1 --body " + TOKEN}})
        ),
    )
    assert module.main() == 0
    data = json.loads(capsys.readouterr().out)
    assert "export PATH=" in data["hookSpecificOutput"]["updatedInput"]["command"]
    assert "rule=synthetic-rule" in data["systemMessage"] and TOKEN not in data["systemMessage"]


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


@pytest.mark.parametrize("fill", ["--fill", "--fill-first", "--fill-verbose"])
@pytest.mark.parametrize("text", [TOKEN, "clean commit"])
def test_generated_pr_body_snapshotted_before_send(fill, text, synthetic_opsec, tmp_path):
    calls = []

    def run(args, **kwargs):
        if args[0] == "git":
            return subprocess.CompletedProcess(args, 0, "clean title\0" + text + "\0\n", "")
        calls.append(args)
        assert fill not in args
        assert args[args.index("--title") + 1] == "clean title"
        assert args[args.index("--body") + 1] == text
        return subprocess.CompletedProcess(args, 0, "sent", "")

    if text == TOKEN:
        with pytest.raises(gate.PublishBlocked):
            gate.checked_run(
                ["gh", "pr", "create", "--base", "main", "--repo", "unit/public", fill], cwd=tmp_path, runner=run
            )
        assert calls == []
    else:
        gate.checked_run(
            ["gh", "pr", "create", "--base", "main", "--repo", "unit/public", fill], cwd=tmp_path, runner=run
        )
        assert len(calls) == 1


def test_encoded_json_is_checked_semantically(synthetic_opsec, tmp_path):
    body = tmp_path / "body.json"
    body.write_text('{"body":"\\u0053ENTINEL-HOST-TOKEN"}')
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", "api", "repos/unit/public/issues/1/comments", "--input", str(body)],
            runner=lambda *a, **kw: pytest.fail("send"),
        )


def test_opaque_graphql_cannot_be_exempted_by_ambient_private_repo(synthetic_opsec):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                'query=mutation{addComment(input:{subjectId:"unit",body:"' + TOKEN + '"}){clientMutationId}}',
            ],
            env={"GH_REPO": "unit/private"},
            runner=lambda *a, **kw: pytest.fail("send"),
        )


def test_api_url_private_exemption():
    calls = []
    gate.checked_run(
        ["gh", "api", "https://api.github.com/repos/unit/private/issues/1/comments", "-f", "body=" + TOKEN],
        runner=lambda *a, **kw: calls.append(a),
    )
    assert len(calls) == 1


@pytest.mark.parametrize("text", [TOKEN, "clean"])
def test_hook_command_reaches_shim_gate(gh_shim_sandbox, tmp_path, text):
    root, _shim, _tooling = gh_shim_sandbox
    hook = root / "agents_extensions/shared/hooks/guard-public-github-text.py"
    hook.parent.mkdir(parents=True)
    __import__("shutil").copy2(ROOT / "agents_extensions/shared/hooks/guard-public-github-text.py", hook)
    spy = tmp_path / "real-gh"
    sent = tmp_path / "sent"
    spy.write_text(f'#!/bin/sh\nprintf "%s" "$*" > {sent}\n')
    spy.chmod(0o755)
    body = tmp_path / "body"
    body.write_text(text)
    environment = {"PATH": os.defpath, "AGENT_REAL_GH": str(spy)}
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": f"gh issue comment 1 --body-file {body}"}})
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=payload,
        env=environment,
        cwd=root,
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    command = json.loads(result.stdout)["hookSpecificOutput"]["updatedInput"]["command"]
    sent_result = subprocess.run(
        ["bash", "-c", command], cwd=root, env=environment, text=True, capture_output=True, timeout=10
    )
    assert sent.exists() == (text == "clean")
    assert sent_result.returncode == (0 if text == "clean" else 2)
    assert TOKEN not in sent_result.stderr


def test_shim_override_logs_once_and_does_not_inherit(gh_shim_sandbox, tmp_path):
    root, shim, _tooling = gh_shim_sandbox
    spy = tmp_path / "real-gh"
    sent = tmp_path / "sent"
    spy.write_text(f'#!/bin/sh\ntest -z "${{LU_OPSEC_OVERRIDE:-}}" || exit 10\nprintf "sent\\n" >> {sent}\n')
    spy.chmod(0o755)
    env = {"PATH": os.defpath, "AGENT_REAL_GH": str(spy), "LU_OPSEC_OVERRIDE": "synthetic one-command reason"}
    command = [str(shim), "issue", "comment", "1", "--body", TOKEN]
    first = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, timeout=10)
    second = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, timeout=10)
    assert first.returncode == 0, first.stderr
    assert second.returncode == 2 and "already consumed" in second.stderr
    assert sent.read_text() == "sent\n"
    log = root / "batch_state/opsec/overrides.jsonl"
    assert len(log.read_text().splitlines()) == 1 and TOKEN not in log.read_text()


def test_shim_process_budget_20_10kb_bodies(gh_shim_sandbox, tmp_path):
    root, shim, _tooling = gh_shim_sandbox
    spy = tmp_path / "real-gh"
    spy.write_text("#!/bin/sh\nexit 0\n")
    spy.chmod(0o755)
    body = tmp_path / "body"
    body.write_text("a" * 10_240)
    timings = []
    for _ in range(20):
        start = time.perf_counter()
        result = subprocess.run(
            [str(shim), "issue", "comment", "1", "--body-file", str(body)],
            cwd=root,
            env={"PATH": os.defpath, "AGENT_REAL_GH": str(spy)},
            capture_output=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        timings.append((time.perf_counter() - start) * 1000)
    median = statistics.median(timings)
    print(f"shim median 20 x 10KB: {median:.3f} ms")
    assert median < 200


@pytest.mark.parametrize(
    "query",
    [
        "query Q($mutation:String){viewer{login}}",
        'query Q($input:Unit={name:"mutation"}){viewer{login}}',
        "fragment Unit on User {login}\nquery Q {viewer {...Unit}}",
        'query Q($query:String) @unit(value:"mutation") {viewer{login}}',
    ],
)
def test_graphql_operation_header_identifiers_do_not_turn_queries_into_writes(query):
    assert not graphql_write(query)


def test_label_description_blocks(synthetic_opsec):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", "label", "create", "unit-label", "--repo", "unit/public", "--description", TOKEN],
            runner=lambda *a, **kw: pytest.fail("send"),
        )


def test_direct_process_override_is_checked_once(synthetic_opsec, gh_shim_sandbox, tmp_path, monkeypatch):
    root, _shim, _tooling = gh_shim_sandbox
    monkeypatch.setattr(gate, "ROOT", root)
    monkeypatch.setattr(gate, "primary_root", lambda cwd=None: root)
    spy = tmp_path / "real-gh"
    sent = tmp_path / "sent"
    spy.write_text(f'#!/bin/sh\ntest -z "${{LU_OPSEC_OVERRIDE:-}}" || exit 10\nprintf "sent\\n" >> {sent}\n')
    spy.chmod(0o755)
    result = gate.checked_run(
        ["gh", "issue", "comment", "1", "--repo", "unit/public", "--body", TOKEN],
        env={"PATH": os.defpath, "AGENT_REAL_GH": str(spy), "LU_OPSEC_OVERRIDE": "one direct command"},
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert sent.read_text() == "sent\n"
    assert len((root / "batch_state/opsec/overrides.jsonl").read_text().splitlines()) == 1


def test_api_node_path_not_exempted_by_ambient_private_repo(synthetic_opsec):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", "api", "repositories/1/issues/1/comments", "-f", "body=" + TOKEN],
            env={"GH_REPO": "unit/private"},
            runner=lambda *a, **kw: pytest.fail("send"),
        )


def test_mixed_graphql_input_and_query_fields_refused(synthetic_opsec, tmp_path):
    document = tmp_path / "query.json"
    document.write_text(
        json.dumps({"query": 'mutation{addComment(input:{subjectId:"unit",body:"' + TOKEN + '"}){clientMutationId}}'})
    )
    with pytest.raises(gate.PublishBlocked, match="mixed GraphQL"):
        gate.checked_run(
            ["gh", "api", "graphql", "--input", str(document), "-f", "query=query{viewer{login}}"],
            runner=lambda *a, **kw: pytest.fail("send"),
        )


def test_absolute_graphql_query_url_remains_read():
    calls = []
    gate.checked_run(
        ["gh", "api", "https://api.github.com/graphql", "-f", "query=query{viewer{login}}"],
        runner=lambda *a, **kw: calls.append(a),
    )
    assert len(calls) == 1


def test_direct_reads_preserve_next_write_override(synthetic_opsec, tmp_path, monkeypatch):
    monkeypatch.setenv("LU_OPSEC_OVERRIDE", "after a read")
    monkeypatch.setattr(gate, "primary_root", lambda cwd=None: tmp_path)
    calls = []

    def send(args, **kwargs):
        assert "LU_OPSEC_OVERRIDE" not in kwargs["env"]
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "sent", "")

    gate.checked_run(["gh", "release", "view", "unit-tag"], runner=send)
    assert os.environ["LU_OPSEC_OVERRIDE"] == "after a read"
    gate.checked_run(["gh", "issue", "comment", "1", "--repo", "unit/public", "--body", TOKEN], runner=send)
    assert "LU_OPSEC_OVERRIDE" not in os.environ and len(calls) == 2
    assert len((tmp_path / "batch_state/opsec/overrides.jsonl").read_text().splitlines()) == 1


def test_private_write_consumes_inherited_override(tmp_path):
    reason = "synthetic private command"
    log = tmp_path / "overrides.jsonl"
    gate.check_texts("github.com/unit/private", [TOKEN], environment={"LU_OPSEC_OVERRIDE": reason}, log_path=log)
    with pytest.raises(gate.PublishBlocked, match="already consumed"):
        gate.check_texts("github.com/unit/private", [TOKEN], environment={"LU_OPSEC_OVERRIDE": reason}, log_path=log)
    assert TOKEN not in log.read_text() and json.loads(log.read_text())["rule_ids"] == []


def test_launcher_worker_and_runtime_keep_shim_first(tmp_path, monkeypatch):
    from scripts import delegate
    from scripts.agent_runtime import runner

    probe = tmp_path / "probe"
    probe.write_text(f"#!{sys.executable}\nimport json,os\nprint(json.dumps(dict(os.environ)))\n")
    probe.chmod(0o755)
    environment = {"PATH": os.defpath, "LU_OPSEC_OVERRIDE": "inherited"}
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; LC_ROOT="$2"; launcher_publication_path; "$3"',
            "unit",
            str(ROOT / "scripts/lib/launcher_core.sh"),
            str(ROOT),
            str(probe),
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    launched = json.loads(result.stdout)
    shim = str(ROOT / "scripts/agent_runtime/shims")
    assert launched["PATH"].split(os.pathsep)[0] == shim and "LU_OPSEC_OVERRIDE" not in launched
    monkeypatch.setattr(delegate, "_REPO_ROOT", ROOT)
    worker = delegate._pinned_worker_venv_env(launched)
    assert worker["PATH"].split(os.pathsep)[0] == shim
    for mode in ["workspace-write", "danger"]:
        guarded = runner._apply_merge_guard(mode=mode, env=worker)
        _command, prepared = runner._prepare_spawn_command([str(probe)], guarded)
        assert prepared["PATH"].split(os.pathsep)[0] == shim


def test_nondefault_public_catalog_entry_is_not_private(monkeypatch):
    monkeypatch.setattr(
        gate, "catalog", lambda: {"unit": {"github": "unit/public", "default": False, "role": "public-monorepo"}}
    )
    assert not gate.is_private("github.com/unit/public")


@pytest.mark.parametrize(
    "fill,expected_title,expected_body",
    [
        ("--fill", "unit branch", "- **Older**\n- **Newer**\n"),
        ("--fill-first", "Older", "older body\n"),
        ("--fill-verbose", "unit branch", "- **Older**\n  older body\n  \n\n- **Newer**\n  newer body\n  "),
    ],
)
def test_multi_commit_fill_matches_cli_defaults(fill, expected_title, expected_body, synthetic_opsec, tmp_path):
    calls = []

    def send(args, **kwargs):
        if args[0] == "git":
            assert "--cherry" in args
            return subprocess.CompletedProcess(args, 0, "Newer\0newer body\n\0\nOlder\0older body\n\0", "")
        calls.append(args)
        assert args[args.index("--title") + 1] == expected_title
        assert args[args.index("--body") + 1] == expected_body
        return subprocess.CompletedProcess(args, 0, "sent", "")

    gate.checked_run(
        ["gh", "pr", "create", "--repo", "unit/public", "--base", "main", "--head", "unit_branch", fill],
        runner=send,
        cwd=tmp_path,
    )
    assert len(calls) == 1


@pytest.mark.parametrize("fill,blocks", [("--fill", False), ("--fill-first", True), ("--fill-verbose", True)])
def test_fill_scans_only_commit_text_that_will_be_sent(fill, blocks, synthetic_opsec, tmp_path):
    calls = []

    def send(args, **kwargs):
        if args[0] == "git":
            return subprocess.CompletedProcess(args, 0, "Newer\0clean\0\nOlder\0" + TOKEN + "\0", "")
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "sent", "")

    args = ["gh", "pr", "create", "--repo", "unit/public", "--base", "main", "--head", "unit_branch", fill]
    if blocks:
        with pytest.raises(gate.PublishBlocked):
            gate.checked_run(args, runner=send, cwd=tmp_path)
        assert calls == []
    else:
        gate.checked_run(args, runner=send, cwd=tmp_path)
        assert len(calls) == 1


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
@pytest.mark.parametrize("flag", ["--comment", "-c", "-c="])
def test_close_reopen_short_comments_cannot_escape(group, verb, flag, synthetic_opsec):
    args = ["gh", group, verb, "1", "--repo", "unit/public"]
    args += [flag + TOKEN] if flag.endswith("=") else [flag, TOKEN]
    with pytest.raises(gate.PublishBlocked, match="field="):
        gate.checked_run(args, runner=lambda *a, **kw: pytest.fail("outbound"))


@pytest.mark.parametrize("group", ["issue", "pr"])
@pytest.mark.parametrize("verb", ["close", "reopen"])
def test_short_comment_value_never_classifies_destination(group, verb, synthetic_opsec):
    from scripts.opsec.gh_snapshot import destination, options

    args = [group, verb, "1", "-c", "https://github.com/unit/private/issues/1"]
    found, positional = options(args)
    assert positional == [group, verb, "1"]
    assert (
        destination(args, found, positional, cwd=ROOT, environment={"GH_REPO": "unit/public"}, reader=None)
        == "github.com/unit/public"
    )


@pytest.mark.parametrize("args", [["pr", "checkout", "1", "-f"], ["workflow", "list", "-a"], ["pr", "list", "-d"]])
def test_boolean_read_flags_never_load_matcher(args, monkeypatch):
    monkeypatch.setattr(gate, "private_tooling", lambda: pytest.fail("matcher on read"))
    calls = []
    gate.checked_run(["gh", *args], runner=lambda *a, **kw: calls.append(a))
    assert calls == [(["gh", *args],)]


def test_pr_create_draft_does_not_consume_title(synthetic_opsec):
    calls = []
    gate.checked_run(
        ["gh", "pr", "create", "-d", "--title", "clean", "--body", "clean", "--repo", "unit/public"],
        runner=lambda *a, **kw: calls.append(a),
    )
    assert calls[0][0][3:] == ["-d", "--title", "clean", "--body", "clean", "--repo", "unit/public"]


@pytest.mark.parametrize("flags", [[], ["--subject", "clean"], ["-t", "clean", "-b", "clean"]])
def test_merge_scans_only_supplied_text(flags, synthetic_opsec):
    calls = []
    gate.checked_run(
        ["gh", "pr", "merge", "1", "--squash", "--repo", "unit/public", *flags], runner=lambda *a, **kw: calls.append(a)
    )
    assert len(calls) == 1


@pytest.mark.parametrize("flag", ["--subject", "-t", "--body", "-b"])
def test_merge_supplied_text_blocks(flag, synthetic_opsec):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", "pr", "merge", "1", "--repo", "unit/public", flag, TOKEN],
            runner=lambda *a, **kw: pytest.fail("outbound"),
        )


@pytest.mark.parametrize("verb", ["comment", "merge", "review"])
def test_current_branch_pr_commands_pin_environment_without_repo_argument(verb, synthetic_opsec):
    def send(args, **kwargs):
        assert "--repo" not in args and kwargs["env"]["GH_REPO"] == "github.com/unit/public"
        return subprocess.CompletedProcess(args, 0, "sent", "")

    gate.checked_run(["gh", "pr", verb, "--body", "clean"], env={"GH_REPO": "unit/public"}, runner=send)


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


@pytest.mark.parametrize(
    "args",
    [
        ["repo", "edit", "unit/public", "--description", TOKEN],
        ["workflow", "run", "unit.yml", "-f", "value=" + TOKEN],
        ["project", "item-create", "1", "--title", TOKEN, "--body", "clean"],
        ["project", "item-create", "1", "--title", "clean", "--body", TOKEN],
        ["api", "repos/unit/public/issues/1/comments", "-if", "body=" + TOKEN],
    ],
)
def test_extended_public_text_commands_block(args, synthetic_opsec):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(["gh", *args], env={"GH_REPO": "unit/public"}, runner=lambda *a, **kw: pytest.fail("outbound"))


@pytest.mark.parametrize("text", [TOKEN, "clean"])
def test_gist_description_and_file_scanned(text, synthetic_opsec, tmp_path):
    body = tmp_path / "gist.txt"
    body.write_text("clean")
    calls = []

    def send(args, **kwargs):
        assert Path(args[args.index("create") + 1]).read_text() == "clean"
        calls.append(args)

    if text == TOKEN:
        with pytest.raises(gate.PublishBlocked):
            gate.checked_run(["gh", "gist", "create", str(body), "-d", text], runner=send)
    else:
        gate.checked_run(["gh", "gist", "create", str(body), "-d", text], runner=send)
    assert len(calls) == (text == "clean")


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


def test_location_reports_field_and_line_without_text(synthetic_opsec):
    with pytest.raises(gate.PublishBlocked, match="field=body line=2") as error:
        gate.checked_run(
            ["gh", "issue", "comment", "1", "--repo", "unit/public", "--body", "clean\n" + TOKEN],
            runner=lambda *a, **kw: pytest.fail("send"),
        )
    assert TOKEN not in str(error.value)


def test_attached_body_file_preserves_flag(synthetic_opsec, tmp_path):
    body = tmp_path / "body.txt"
    body.write_text("clean")

    def send(args, **kwargs):
        flag = next(a for a in args if a.startswith("-F="))
        assert Path(flag[3:]).read_text() == "clean"

    gate.checked_run(["gh", "issue", "comment", "1", "--repo", "unit/public", "-F=" + str(body)], runner=send)


def test_contents_base64_payload_is_scanned(synthetic_opsec):
    import base64

    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            [
                "gh",
                "api",
                "repos/unit/public/contents/unit.txt",
                "-f",
                "content=" + base64.b64encode(TOKEN.encode()).decode(),
            ],
            runner=lambda *a, **kw: pytest.fail("send"),
        )


def test_nonagent_shims_directory_can_supply_real_gh(tmp_path):
    path = tmp_path / "shims" / "gh"
    path.parent.mkdir()
    path.write_text("#!/bin/sh\nexit 0\n")
    path.chmod(0o755)
    assert gate.real_gh({"PATH": str(path.parent)}) == str(path)


def test_keeper_enqueue_and_closeout_auto_merge_pass_gate(synthetic_opsec, monkeypatch, tmp_path):
    from scripts.orchestration import merge_queue_keeper as keeper
    from scripts.orchestration import task_closeout as closeout

    calls = []

    def send(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "null", "")

    monkeypatch.setattr(subprocess, "run", send)
    keeper.GitHub(tmp_path, "unit/public").enqueue(1, "a" * 40)
    adapter = closeout.GhGitHubAdapter(tmp_path, runner=lambda args, stdin=None: send(args).stdout)
    adapter.arm_auto_merge("unit/public", 1)
    assert len(calls) == 2
    assert all(args[:3] == ["gh", "pr", "merge"] and "--body" not in args for args in calls)


def test_stdin_shim_replay_works_outside_git(gh_shim_sandbox, tmp_path):
    _root, shim, _tooling = gh_shim_sandbox
    spy = tmp_path / "real-gh"
    spy.write_text("#!/bin/sh\ncat\n")
    spy.chmod(0o755)
    result = subprocess.run(
        [str(shim), "issue", "comment", "1", "--repo", "unit/public", "-F", "-"],
        cwd=tmp_path,
        input="clean bytes\n",
        env={"PATH": os.defpath, "AGENT_REAL_GH": str(spy)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "clean bytes\n"


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

    monkeypatch.setattr(publisher, "checked_run", refuse)
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
        monkeypatch.setattr(publisher, "checked_run", refuse)
    with pytest.raises(keeper.KeeperError, match="publish_blocked"):
        keeper.GitHub(tmp_path, "unit/public").enqueue(1, "a" * 40)
    for runner in [None, lambda *a: pytest.fail("outbound")]:
        with pytest.raises(task_lifecycle.LifecycleError, match="publish_blocked"):
            closeout.GhGitHubAdapter(tmp_path, runner=runner).arm_auto_merge("unit/public", 1)


def test_bridge_comment_refusal_is_rendered_and_returns_false(monkeypatch, capsys):
    from scripts.ai_agent_bridge import _github

    def refuse(*args, **kwargs):
        raise gate.PublishBlocked("synthetic refusal")

    monkeypatch.setattr(_github, "checked_run", refuse)
    assert not _github._gh_comment(1, "clean")
    assert "publish_blocked: synthetic refusal" in capsys.readouterr().out


def test_real_matcher_process_budget_20_10kb_bodies():
    path = real_tooling()
    timings = []
    script = (
        "import sys; from pathlib import Path; from scripts.opsec.prepublish import check_texts; "
        "check_texts('github.com/unit/public', ['a'*10240], tooling=Path(sys.argv[1]), environment={})"
    )
    for _ in range(20):
        start = time.perf_counter()
        result = subprocess.run([sys.executable, "-c", script, str(path)], cwd=ROOT, capture_output=True, timeout=10)
        assert result.returncode == 0, "real matcher subprocess refused neutral synthetic payload"
        timings.append((time.perf_counter() - start) * 1000)
    median = statistics.median(timings)
    print(f"real matcher process median 20 x 10KB: {median:.3f} ms")
    assert median < 200


def test_attached_short_body_file_is_scanned(synthetic_opsec, tmp_path):
    body = tmp_path / "body.txt"
    body.write_text(TOKEN)
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", "issue", "comment", "1", "--repo", "unit/public", "-F" + str(body)],
            runner=lambda *a, **kw: pytest.fail("send"),
        )


@pytest.mark.parametrize(
    "args",
    [
        ["repo", "edit", "unit/public", "--description", "clean"],
        ["workflow", "run", "unit.yml", "-f", "value=clean"],
        ["project", "item-create", "1", "--title", "clean", "--body", "clean"],
        ["api", "repos/unit/public/issues/1/comments", "-if", "body=clean"],
    ],
)
def test_extended_public_text_commands_deliver_clean_snapshot(args, synthetic_opsec):
    calls = []
    gate.checked_run(["gh", *args], env={"GH_REPO": "unit/public"}, runner=lambda *a, **kw: calls.append(a))
    assert len(calls) == 1
    if args[0] == "repo":
        assert calls[0][0] == ["gh", *args]


def test_api_global_flags_do_not_hide_write(synthetic_opsec):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            [
                "gh",
                "--hostname",
                "github.com",
                "-Runit/public",
                "api",
                "repos/unit/public/issues/1/comments",
                "-f",
                "body=" + TOKEN,
            ],
            runner=lambda *a, **kw: pytest.fail("send"),
        )


def test_gist_snapshot_preserves_filename(synthetic_opsec, tmp_path):
    body = tmp_path / "unit.txt"
    body.write_text("clean")

    def send(args, **kwargs):
        target = Path(args[args.index("create") + 1])
        assert target.name == body.name and target.read_bytes() == body.read_bytes()

    gate.checked_run(["gh", "gist", "create", str(body), "-d", "clean"], runner=send)


def test_real_matcher_shim_budget_20_10kb_bodies(gh_shim_sandbox, tmp_path):
    path = real_tooling()
    root, shim, _synthetic = gh_shim_sandbox
    repos = {key: dict(row) for key, row in CATALOG.items()}
    repos["infra-private"]["local_name"] = "real-private-fixture"
    (root / "scripts/config/fleet_repos.yaml").write_text(json.dumps({"repos": repos}))
    tooling = root.parent / "real-private-fixture/tools/public_opsec_scan"
    tooling.parent.mkdir(parents=True)
    tooling.symlink_to(path, target_is_directory=True)
    spy = tmp_path / "real-gh"
    spy.write_text("#!/bin/sh\nexit 0\n")
    spy.chmod(0o755)
    body = tmp_path / "body"
    body.write_text("a" * 10_240)
    timings = []
    for _ in range(20):
        start = time.perf_counter()
        result = subprocess.run(
            [str(shim), "issue", "comment", "1", "--body-file", str(body)],
            cwd=root,
            env={"PATH": os.defpath, "AGENT_REAL_GH": str(spy)},
            capture_output=True,
            timeout=10,
        )
        assert result.returncode == 0, "real matcher shim refused neutral synthetic payload"
        timings.append((time.perf_counter() - start) * 1000)
    median = statistics.median(timings)
    print(f"real matcher shim median 20 x 10KB: {median:.3f} ms")
    assert median < 200
