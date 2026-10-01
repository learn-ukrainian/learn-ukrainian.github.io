"""Closed grammar and immutable payload adversarial tests; synthetic data only."""

from __future__ import annotations

import io
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts.opsec import prepublish as gate
from scripts.opsec.gh_snapshot import READ_GRAMMARS, admit
from scripts.publish import github as pub
from tests.opsec_fixtures import CATALOG, ROOT, TOKEN


@pytest.fixture(autouse=True)
def catalog(monkeypatch):
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)


def spy(calls):
    def send(args, **kwargs):
        if args[:3] == ["gh", "pr", "view"] and "--json" in args and args[args.index("--json") + 1] == "number,isDraft,headRefOid":
            return subprocess.CompletedProcess(args, 0, json.dumps({"number": int(args[3]), "isDraft": False, "headRefOid": "a" * 40}), "")
        if args[:3] == ["gh", "pr", "checks"] and "--json" in args and args[args.index("--json") + 1] == "name,bucket,state":
            return subprocess.CompletedProcess(args, 0, "[]", "")
        if args[:5] == ["gh", "api", "--method", "POST", "graphql"] and "viewerMergeHeadlineText" in Path(args[6]).read_text():
            pull = {"headRefOid": "a" * 40, "isMergeQueueEnabled": False,
                    "viewerMergeHeadlineText": "clean (#1)", "viewerMergeBodyText": "* clean"}
            return subprocess.CompletedProcess(args, 0, json.dumps({"data": {"repository": {"pullRequest": pull}}}), "")
        record = {"argv": args, "env": kwargs.get("env", {})}
        for flag in ("--body-file", "--notes-file", "--input"):
            if flag in args:
                record[flag] = Path(args[args.index(flag) + 1]).read_bytes()
        if "--" in args:
            record["artifacts"] = {
                Path(p).name: Path(p).read_bytes() for p in args[args.index("--") + 1 :] if Path(p).is_file()
            }
        calls.append(record)
        return subprocess.CompletedProcess(args, 0, "{}", "")

    return send


VERBS = [
    ("issue-create", {"title": "clean", "body": "clean", "labels": ["unit"]}),
    ("issue-edit", {"number": 1, "title": "clean", "body": "clean", "milestone": "unit"}),
    ("issue-comment", {"number": 1, "body": "clean"}),
    ("issue-comment-json", {"number": 1, "body": "clean"}),
    ("issue-close", {"number": 1, "comment": "clean"}),
    ("pr-create", {"title": "clean", "body": "clean", "base": "main", "head": "unit"}),
    ("pr-edit", {"number": 1, "title": "clean", "add_labels": ["unit"], "remove_labels": ["old"]}),
    ("pr-comment", {"number": 1, "body": "clean"}),
    ("pr-review", {"number": 1, "verdict": "request-changes", "body": "clean"}),
    ("pr-merge", {"number": 1, "subject": "clean", "body": "clean"}),
    ("pr-disarm", {"number": 1}),
    ("pr-dequeue", {"node_id": "UNIT_NODE"}),
    ("release-create", {"tag": "unit", "title": "clean", "notes": "clean"}),
    ("release-edit", {"tag": "unit", "title": "clean", "notes": "clean", "draft": False}),
    ("label-create", {"name": "unit", "color": "aabbcc", "description": "clean"}),
    ("label-edit", {"name": "unit", "new_name": "new", "description": "clean"}),
    ("milestone-create", {"title": "clean", "description": "clean"}),
    ("milestone-edit", {"number": 1, "title": "clean", "description": "clean"}),
    ("commit-status", {"sha": "a" * 40, "state": "success", "context": "unit", "description": "clean"}),
    ("issue-link", {"parent_id": "PARENT", "child_id": "CHILD"}),
]


@pytest.mark.parametrize("verb,fields", VERBS)
def test_each_typed_verb_delivers_fixed_payload(synthetic_opsec, verb, fields):
    calls = []
    assert pub.publish(verb, repo="unit/public", runner=spy(calls), **fields).returncode == 0
    assert len(calls) == 1


TEXT_CASES = [
    (verb, fields, key) for verb, fields in VERBS for key in fields if pub.SCHEMAS[verb][1][key] in {"text", "texts"}
]


@pytest.mark.parametrize("verb,fields,key", TEXT_CASES)
@pytest.mark.parametrize("payload", [TOKEN, TOKEN + "/unit", "--" + TOKEN, "123/" + TOKEN, "unit\n" + TOKEN])
def test_every_public_field_blocks_even_word_shaped(synthetic_opsec, verb, fields, key, payload):
    fields = dict(fields)
    fields[key] = [payload] if pub.SCHEMAS[verb][1][key] == "texts" else payload
    calls = []
    with pytest.raises(gate.PublishBlocked) as error:
        pub.publish(verb, repo="unit/public", runner=spy(calls), **fields)
    assert not calls and TOKEN not in str(error.value)
    assert "field=" in str(error.value) and "line=" in str(error.value)


@pytest.mark.parametrize("verb,fields", VERBS)
def test_closed_schema_rejects_payload_passthrough(verb, fields):
    with pytest.raises(gate.PublishBlocked, match="unknown publisher field"):
        pub.publish(
            verb,
            repo="unit/public",
            arbitrary_argv=["--body", TOKEN],
            runner=lambda *a, **k: pytest.fail("send"),
            **fields,
        )


@pytest.mark.parametrize(
    "fields",
    [
        {"number": "1"},
        {"number": True},
        {"number": -1},
        {"number": 1, "body": "x", "body_file": "x"},
        {"number": 1, "repo": "github.com/unit/private/extra"},
    ],
)
def test_schema_refuses_invalid_operands(fields):
    with pytest.raises(gate.PublishBlocked):
        pub.publish("issue-edit", runner=lambda *a, **k: pytest.fail("send"), **fields)


@pytest.mark.parametrize("verb", ["issue-comment", "pr-comment", "pr-review", "pr-merge", "pr-create"])
@pytest.mark.parametrize("source_kind", ["absolute", "relative", "stdin"])
def test_body_inputs_are_frozen_and_transport_paths_not_scanned(
    synthetic_opsec, tmp_path, monkeypatch, verb, source_kind
):
    original = gate.check_texts
    body = tmp_path / "clean.md"
    body.write_bytes(b"clean\nexact UTF-8 \xc3\xa9\r\n")
    expected = body.read_bytes()

    def check(dest, texts, **kw):
        original(dest, texts, **kw)
        body.write_text(TOKEN)

    monkeypatch.setattr(gate, "check_texts", check)
    fields = {"body_file": str(body) if source_kind == "absolute" else body.name if source_kind == "relative" else "-"}
    if verb == "pr-create":
        fields.update(title="clean", base="main", head="unit")
    else:
        fields["number"] = 1
    if verb == "pr-review":
        fields["verdict"] = "approve"
    calls = []
    pub.publish(verb, repo="unit/public", cwd=tmp_path, stdin=expected, runner=spy(calls), **fields)
    assert calls[0]["--body-file"] == expected
    assert not Path(calls[0]["argv"][calls[0]["argv"].index("--body-file") + 1]).exists()


@pytest.mark.parametrize("verb", ["release-create", "release-upload", "gist-create"])
@pytest.mark.parametrize("content", [b"clean\n", TOKEN.encode(), b"\x1f\x8b\xffbinary"])
def test_artifacts_explicit_names_utf8_scanned_binary_releases_work(synthetic_opsec, tmp_path, verb, content):
    source = tmp_path / "source"
    source.write_bytes(content)
    fields = {"files" if verb == "gist-create" else "assets": [pub.Asset(source, "unit.bin")]}
    if verb != "gist-create":
        fields.update(repo="unit/public", tag="unit")
    calls = []
    if content == TOKEN.encode() or (verb == "gist-create" and content.startswith(b"\x1f")):
        with pytest.raises(gate.PublishBlocked):
            pub.publish(verb, runner=spy(calls), **fields)
        assert not calls
    else:
        pub.publish(verb, runner=spy(calls), **fields)
        assert calls[0]["artifacts"]["unit.bin"] == content


@pytest.mark.parametrize("verb", ["release-create", "release-upload", "gist-create"])
def test_artifact_names_block_and_files_are_not_reread(synthetic_opsec, tmp_path, monkeypatch, verb):
    source = tmp_path / "unit.bin"
    source.write_bytes(b"\xffunit" if verb != "gist-create" else b"clean")
    fields = {} if verb == "gist-create" else {"repo": "unit/public", "tag": "unit"}
    key = "files" if verb == "gist-create" else "assets"
    with pytest.raises(gate.PublishBlocked):
        pub.publish(verb, **fields, **{key: [pub.Asset(source, TOKEN)]}, runner=lambda *a, **k: pytest.fail("send"))
    original = gate.check_texts
    expected = source.read_bytes()

    def mutate(*a, **k):
        original(*a, **k)
        source.write_bytes(TOKEN.encode())

    monkeypatch.setattr(gate, "check_texts", mutate)
    calls = []
    pub.publish(verb, **fields, **{key: [pub.Asset(source)]}, runner=spy(calls))
    assert calls[0]["artifacts"]["unit.bin"] == expected


@pytest.mark.parametrize(
    "verb,fields",
    [
        ("issue-close", {"number": 1}),
        ("pr-review", {"number": 1, "verdict": "approve"}),
        ("pr-disarm", {"number": 1}),
    ],
)
def test_no_text_verbs_work_without_private_tooling(verb, fields, monkeypatch):
    monkeypatch.setattr(gate, "private_tooling", lambda: pytest.fail("must not load matcher"))
    calls = []
    pub.publish(verb, repo="unit/public", runner=spy(calls), **fields)
    assert len(calls) == 1


@pytest.mark.parametrize("payload", ["123", "a" * 40, "word/word", "--flag"])
def test_text_shape_never_disables_fail_closed(tmp_path, monkeypatch, payload):
    monkeypatch.setattr(gate, "private_tooling", lambda: tmp_path / "absent")
    with pytest.raises(gate.PublishBlocked, match="unavailable"):
        pub.publish(
            "issue-comment",
            number=1,
            body=payload,
            repo="unit/public",
            env={"LU_OPSEC_OVERRIDE": "reason"},
            runner=lambda *a, **k: pytest.fail("send"),
        )


@pytest.mark.parametrize("group", ["issue", "pr"])
@pytest.mark.parametrize("flag", ["--title", "-t", "--body", "--body-file", "--repo"])
@pytest.mark.parametrize("fake_verb", ["list", "view", "status"])
def test_round3_value_flag_hiding_real_verb_never_sends(group, flag, fake_verb):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", group, flag, fake_verb, "create", "--body", TOKEN],
            env={"GH_REPO": "unit/public"},
            runner=lambda *a, **k: pytest.fail("send"),
        )


@pytest.mark.parametrize("flag", ["-p", "-q", "--jq", "--header"])
def test_round3_api_endpoint_hiding_is_refused(flag):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            [
                "gh",
                "api",
                flag,
                "graphql",
                "repos/unit/public/issues/1/comments",
                "-f",
                "body=" + TOKEN,
                "-f",
                "query={x}",
            ],
            runner=lambda *a, **k: pytest.fail("send"),
        )


@pytest.mark.parametrize(
    "args",
    [
        ["api", "--method", "GET", "-X", "POST", "repos/unit/public/issues?title=" + TOKEN],
        ["api", "graphql", "-f", "query={viewer{login}}"],
        ["alias", "list"],
        ["extension", "exec", "unit"],
        ["unit-alias", "view"],
        ["gist", "create", "--public", "unit.md"],
        ["workflow", "run", "ci.yml", "--json"],
    ],
)
def test_api_alias_extension_nonrepo_and_implicit_stdin_refused(args):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", *args], env={"GH_REPO": "unit/private"}, input=TOKEN, runner=lambda *a, **k: pytest.fail("send")
        )


@pytest.mark.parametrize("key,grammar", list(READ_GRAMMARS.items()))
def test_every_read_grammar_accepts_minimal_and_known_flags_only(key, grammar, tmp_path):
    low, _high, flags = grammar
    args = [*key, *(str(i + 1) for i in range(low))]
    calls = []
    gate.checked_run(["gh", *args], cwd=tmp_path, env={}, runner=spy(calls))
    assert len(calls) == 1
    for flag, arity in flags.items():
        admit([*args, flag, *(["unit"] if arity else [])], cwd=tmp_path, environment={})


@pytest.mark.parametrize("key,grammar", list(READ_GRAMMARS.items()))
@pytest.mark.parametrize(
    "extra",
    [
        ["--unknown"],
        ["--body", TOKEN],
        ["--json"],
        ["--web=true"],
        ["extra", "positional", "operands"],
        ["--", "create"],
    ],
)
def test_strict_read_grammar_rejects_unknown_missing_and_extra(key, grammar, extra, tmp_path):
    args = [*key, *(["1"] * grammar[0]), *extra]
    # --json is unknown or requires a value in every grammar.
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(["gh", *args], cwd=tmp_path, env={}, runner=lambda *a, **k: pytest.fail("send"))


@pytest.mark.parametrize(
    "selectors,environment,allowed",
    [
        (["-R", "unit/public", "--repo", "unit/private"], {}, True),
        (["-R", "unit/private", "--repo", "unit/public"], {}, False),
        (["--repo=unit/private"], {"GH_REPO": "unit/public"}, True),
        ([], {"GH_REPO": "unit/private"}, True),
        ([], {"GH_REPO": "unit/private", "GH_HOST": "other.invalid"}, False),
        (["-R", "unit/private"], {"GH_REPO": "unit/private"}, False),
    ],
)
def test_private_destination_last_selector_and_resource_url(selectors, environment, allowed, tmp_path):
    target = "https://github.com/unit/public/issues/1" if len(selectors) == 2 else "1"
    args = ["gh", "issue", "comment", target, *selectors, "--body", TOKEN]
    calls = []
    if allowed:
        gate.checked_run(args, env=environment, cwd=tmp_path, runner=spy(calls))
        assert len(calls) == 1
    else:
        with pytest.raises(gate.PublishBlocked):
            gate.checked_run(args, env=environment, cwd=tmp_path, runner=spy(calls))
        assert not calls


@pytest.mark.parametrize(
    "operation,fields",
    [
        ("issue-parent", {"number": 1}),
        ("membership", {"number": 1}),
        ("subissues", {"number": 1}),
        ("subissues-next", {"number": 1, "cursor": TOKEN}),
        ("queue-snapshot", {"branches": ['unit") { mutation {x} }']}),
        ("subissue-batch", {"cursors": {1: 'unit") { mutation {x} }'}, "body_roots": {1}}),
    ],
)
def test_specific_graphql_reads_keep_variables_as_data(operation, fields):
    calls = []
    pub.read(operation, repo="unit/public", runner=spy(calls), **fields)
    payload = json.loads(calls[0]["--input"])
    assert payload["query"].startswith("query(")
    assert "--method" in calls[0]["argv"]


@pytest.mark.parametrize(
    "operation,fields",
    [
        ("identity", {}),
        ("issue", {"number": 1}),
        ("comments", {"number": 1}),
        ("checks", {"sha": "a" * 40}),
        ("runs", {"start": "2026-01-01", "end": "2026-01-02"}),
    ],
)
def test_specific_rest_reads_are_fixed_get_without_matcher(operation, fields, monkeypatch):
    monkeypatch.setattr(gate, "private_tooling", lambda: pytest.fail("matcher"))
    calls = []
    pub.read(operation, repo="unit/public", runner=spy(calls), **fields)
    assert calls[0]["argv"][2:4] == ["--method", "GET"]


@pytest.mark.parametrize(
    "operation,fields",
    [
        ("comments", {"number": "1/comments?x=unit"}),
        ("checks", {"sha": "unit?x=y"}),
        ("graphql", {"query": "mutation{x}"}),
        ("subissue-batch", {"cursors": {"unit": None}, "body_roots": set()}),
        ("membership", {"number": 1, "query": "mutation{x}"}),
    ],
)
def test_typed_reads_refuse_arbitrary_documents_paths_and_fields(operation, fields):
    with pytest.raises(gate.PublishBlocked):
        pub.read(operation, repo="unit/public", runner=lambda *a, **k: pytest.fail("send"), **fields)


def test_publisher_cli_closed_schema_and_stdin(synthetic_opsec, monkeypatch):
    calls = []
    monkeypatch.setattr(pub, "_run_transport", spy(calls))
    assert pub.main(["issue-comment", "--repo", "unit/public", "--number", "1", "--body", "clean"], runner=spy(calls)) == 0
    with pytest.raises(SystemExit) as exc:
        pub.main(["issue-comment", "--number", "1", "--raw-argv", "unit"])
    assert exc.value.code == 2
    monkeypatch.setattr(sys, "stdin", type("Input", (), {"buffer": io.BytesIO(TOKEN.encode())})())
    assert pub.main(["issue-comment", "--repo", "unit/public", "--number", "1", "--body-file", "-"]) == 2
    assert len(calls) == 1


def test_real_matcher_absolute_body_binary_assets_and_overhead(tmp_path, monkeypatch):
    from tests.test_opsec_prepublish import real_tooling

    tooling = real_tooling()
    monkeypatch.setattr(gate, "private_tooling", lambda: tooling)
    body = tmp_path / "clean.md"
    body.write_text("a" * 10_240)
    asset = tmp_path / "unit.gz"
    asset.write_bytes(b"\x1f\x8b\xffunit")
    calls = []
    timings = []
    for _ in range(20):
        start = time.perf_counter()
        pub.publish("issue-comment", number=1, body_file=body, repo="unit/public", runner=spy(calls))
        timings.append((time.perf_counter() - start) * 1000)
    median = statistics.median(timings)
    print(f"typed writes real matcher median 20 x 10KB: {median:.3f} ms")
    assert median < 200 and len(calls) == 20
    pub.publish("release-upload", repo="unit/public", tag="unit", assets=[pub.Asset(asset)], runner=spy(calls))
    assert calls[-1]["artifacts"]["unit.gz"] == asset.read_bytes()


@pytest.mark.parametrize("body", [TOKEN, "clean\nexact UTF-8 é\n"])
def test_real_cli_with_spy_and_raw_shim_refusal(gh_shim_sandbox, tmp_path, body):
    root, shim, _ = gh_shim_sandbox
    executable = tmp_path / "real-gh"
    output = tmp_path / "outbound"
    executable.write_text(f"""#!{sys.executable}
import sys
from pathlib import Path
args = sys.argv[1:]
assert '--body-file' in args
Path({str(output)!r}).write_bytes(Path(args[args.index('--body-file')+1]).read_bytes())
""")
    executable.chmod(0o755)
    source = tmp_path / "body.md"
    source.write_text(body)
    env = {"PATH": os.defpath, "AGENT_REAL_GH": str(executable)}
    raw = subprocess.run(
        [str(shim), "issue", "comment", "1", "--body-file", str(source)],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert raw.returncode == 2 and not output.exists()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.publish",
            "issue-comment",
            "--number",
            "1",
            "--repo",
            "unit/public",
            "--body-file",
            str(source),
        ],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if body == TOKEN:
        assert result.returncode == 2 and not output.exists()
        assert "field=body line=1" in result.stderr and TOKEN not in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        assert output.read_bytes() == body.encode()


@pytest.mark.parametrize(
    "verb,fields", [("pr-merge", {"number": 1}), ("pr-review", {"number": 1, "verdict": "approve"})]
)
def test_production_transport_retains_worker_merge_approval_guard(synthetic_opsec, tmp_path, verb, fields):
    executable = tmp_path / "real-gh"
    output = tmp_path / "outbound"
    executable.write_text(f"#!/bin/sh\nprintf sent > '{output}'\n")
    executable.chmod(0o755)
    if verb == "pr-merge":
        with pytest.raises(gate.PublishBlocked, match="AGENT_NO_MERGE"):
            pub.publish(verb, repo="unit/public", env={"AGENT_NO_MERGE": "1"},
                        runner=lambda *a, **k: pytest.fail("send"), **fields)
        assert not output.exists()
        return
    result = pub.publish(
        verb,
        repo="unit/public",
        env={"PATH": os.defpath, "AGENT_REAL_GH": str(executable), "AGENT_NO_MERGE": "1"},
        capture_output=True,
        text=True,
        **fields,
    )
    assert result.returncode == 1 and not output.exists()


def test_production_override_logs_once_and_retries_frozen_body(synthetic_opsec, tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "primary_root", lambda cwd=None: tmp_path)
    executable = tmp_path / "real-gh"
    state = tmp_path / "attempts"
    source = tmp_path / "body"
    source.write_text(TOKEN)
    executable.write_text(f"""#!{sys.executable}
import json,os,sys
from pathlib import Path
assert 'LU_OPSEC_OVERRIDE' not in os.environ
args=sys.argv[1:]
body=Path(args[args.index('--body-file')+1]).read_text()
state=Path({str(state)!r})
rows=json.loads(state.read_text()) if state.exists() else []
rows.append(body)
state.write_text(json.dumps(rows))
Path({str(source)!r}).write_text('changed')
if len(rows)==1:
    print('HTTP 429 secondary rate limit',file=sys.stderr)
    sys.exit(1)
""")
    executable.chmod(0o755)
    result = pub.publish(
        "issue-comment",
        number=1,
        body_file=source,
        repo="unit/public",
        capture_output=True,
        text=True,
        env={
            "PATH": os.defpath,
            "AGENT_REAL_GH": str(executable),
            "LU_OPSEC_OVERRIDE": "synthetic retry",
            "AGENT_GH_SECONDARY_RATE_LIMIT_BACKOFF_SECONDS": "0",
            "AGENT_GH_SECONDARY_RATE_LIMIT_RETRIES": "1",
        },
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(state.read_text()) == [TOKEN, TOKEN]
    log = tmp_path / "batch_state/opsec/overrides.jsonl"
    assert len(log.read_text().splitlines()) == 1 and TOKEN not in log.read_text()


def test_checker_exception_is_typed_and_never_sends(monkeypatch):
    def broken(*a, **k):
        raise RuntimeError(TOKEN)

    monkeypatch.setattr(gate, "check_texts", broken)
    with pytest.raises(gate.PublishBlocked, match="checker unavailable") as error:
        pub.publish(
            "issue-comment", repo="unit/public", number=1, body="clean", runner=lambda *a, **k: pytest.fail("send")
        )
    assert TOKEN not in str(error.value)


def test_scanned_label_list_is_frozen(synthetic_opsec, monkeypatch):
    labels = ["unit"]
    original = gate.check_texts

    def mutate(*a, **k):
        original(*a, **k)
        labels[0] = TOKEN

    monkeypatch.setattr(gate, "check_texts", mutate)
    calls = []
    pub.publish("issue-create", repo="unit/public", title="clean", body="clean", labels=labels, runner=spy(calls))
    assert "--label=unit" in calls[0]["argv"] and TOKEN not in " ".join(calls[0]["argv"])


def test_verified_host_is_pinned_in_transport(synthetic_opsec):
    calls = []
    pub.publish(
        "issue-comment",
        repo="github.com/unit/private",
        number=1,
        body=TOKEN,
        env={"GH_HOST": "other.invalid", "GH_REPO": "unit/public"},
        runner=spy(calls),
    )
    assert calls[0]["env"]["GH_HOST"] == "github.com"
    assert calls[0]["argv"][calls[0]["argv"].index("--repo") + 1] == "unit/private"


@pytest.mark.parametrize(
    "consumer",
    [
        "bridge",
        "decision",
        "review-audit",
        "verify",
        "verdict",
        "review-publisher",
        "settle",
        "closeout",
        "keeper",
        "stream",
        "practice",
        "dataset",
        "manifest",
        "fmu",
        "delegate",
    ],
)
def test_each_inventory_publisher_uses_module_and_never_sends_blocked_text(
    synthetic_opsec, publisher_transport, tmp_path, monkeypatch, consumer
):
    """Invoke each caller with a transport spy; gate failures cannot become sends."""
    import importlib

    from scripts.publish.github import Request

    monkeypatch.setenv("GH_REPO", "unit/public")
    calls = []
    payloads = []

    def transport(args, **kwargs):
        if args[:3] == ["gh", "release", "view"]:
            return subprocess.CompletedProcess(args, 1, "", "missing")
        if args[:3] == ["gh", "repo", "view"]:
            return subprocess.CompletedProcess(args, 0, '{"defaultBranchRef":{"name":"trunk"}}', "")
        if args[0] == "git":
            return subprocess.CompletedProcess(args, 0, "https://github.com/unit/public.git", "")
        calls.append(args)
        if "--input" in args:
            payloads.append(json.loads(Path(args[args.index("--input") + 1]).read_bytes()))
        return subprocess.CompletedProcess(args, 0, "{}", "")

    monkeypatch.setattr(subprocess, "run", transport)
    artifact = tmp_path / "unit.gz"
    artifact.write_bytes(b"\xffunit")

    def invoke():
        if consumer == "bridge":
            assert not importlib.import_module("scripts.ai_agent_bridge._github")._gh_comment(1, TOKEN)
        elif consumer == "decision":
            module = importlib.import_module("scripts.audit.check_decisions")
            assert (
                module.create_issue({"id": "unit", "title": TOKEN, "expires": "2026-01-01", "date": "2026-01-01"})
                is None
            )
        elif consumer == "review-audit":
            importlib.import_module("scripts.audit.check_review_issues")._comment_issue(1, TOKEN)
        elif consumer == "verify":
            importlib.import_module("scripts.verify_review")._post_summary(1, {"final_disposition": TOKEN})
        elif consumer == "verdict":
            module = importlib.import_module("scripts.review.record_cf_verdict")
            task = {
                "repository": "unit/public",
                "worktree_branch": "unit",
                "worktree_base_sha": "a" * 40,
                "model": "gpt-6.1-sol",
                "started_at": "2026-01-01T00:00:00+00:00",
            }
            monkeypatch.setattr(module, "_task", lambda *a: (task, "VERDICT: APPROVE\n" + TOKEN))
            monkeypatch.setattr(module, "_pr", lambda *a: {"number": 1, "headRefName": "unit", "headRefOid": "a" * 40})
            monkeypatch.setattr(module, "author_families", lambda *a: {"anthropic"})
            monkeypatch.setattr(module.GitHubAdapter, "identity", lambda *a: "unit")
            monkeypatch.setattr(module.GitHubAdapter, "comments", lambda *a: [])
            module.record("unit-review", pr_number=1, task_root=tmp_path, lock_root=tmp_path / "locks")
        elif consumer == "review-publisher":
            importlib.import_module("scripts.fleet_comms.review_publisher").post_pr_comment(
                repository="unit/public", pr_number=1, body=TOKEN, runner=transport
            )
        elif consumer == "settle":
            module = importlib.import_module("scripts.orchestration.dispatch_settle")
            monkeypatch.setattr(module, "_find_pr", lambda *a: (None, None))
            module.push_and_maybe_open_pr(tmp_path, "unit", open_pr=True, title=TOKEN, body="clean")
        elif consumer == "closeout":
            importlib.import_module("scripts.orchestration.task_closeout").GhGitHubAdapter(tmp_path).update_issue_body(
                "unit/public", 1, TOKEN
            )
        elif consumer == "keeper":
            importlib.import_module("scripts.orchestration.merge_queue_keeper").GitHub(tmp_path, "unit/public").comment(
                1, TOKEN
            )
        elif consumer == "stream":
            # Membership has no public text; fixed mutation succeeds without the matcher.
            importlib.import_module("scripts.orchestration.issue_stream_audit")._gh_json(
                Request("issue-link", repo="unit/public", parent_id="PARENT", child_id="CHILD"), cwd=tmp_path
            )
        elif consumer == "practice":
            importlib.import_module("scripts.practice_deck.publish").upload_release_asset(
                artifact, repo="unit/public", release_tag="unit", asset_name=TOKEN
            )
        elif consumer in {"dataset", "practice"}:
            artifact.rename(tmp_path / TOKEN)
            importlib.import_module("scripts.open_dataset.publish").upload_release_asset(
                tmp_path / TOKEN, repo="unit/public", release_tag="unit"
            )
        elif consumer == "manifest":
            importlib.import_module("scripts.lexicon.publish_manifest").upload_release_asset(
                artifact, repo="unit/public", release_tag="unit", asset_name=TOKEN
            )
        elif consumer == "fmu":
            artifact.rename(tmp_path / TOKEN)
            importlib.import_module("scripts.lexicon.admit_fmu_boosters")._publish_asset(tmp_path / TOKEN)
        else:
            importlib.import_module("scripts.delegate")._create_auto_finalize_pr(
                tmp_path, branch="unit", base_branch="main", title=TOKEN, body="clean"
            )

    if consumer in {"bridge", "decision", "stream"}:
        invoke()
    else:
        with pytest.raises((RuntimeError, ValueError)) as error:
            invoke()
        assert "blocked" in str(error.value)
    if consumer == "stream":
        assert len(calls) == 1
        assert calls[0][:2] == ["gh", "api"]
        assert payloads[0]["query"].startswith("mutation($p:ID!,$c:ID!){addSubIssue")
    elif consumer in {"dataset", "practice"}:
        # Creating the clean release is allowed; uploading the blocked filename is not.
        assert len(calls) == 1 and calls[0][:3] == ["gh", "release", "create"]
    else:
        assert calls == []


@pytest.mark.parametrize("host,allowed", [("github.com", True), ("other.invalid", False)])
def test_raw_rest_private_exemption_requires_actual_endpoint_host(host, allowed):
    calls = []
    args = ["gh", "api", "repos/unit/private/issues/1/comments", "-f", "body=" + TOKEN, "--hostname", host]
    if allowed:
        gate.checked_run(args, runner=spy(calls))
        assert len(calls) == 1
    else:
        with pytest.raises(gate.PublishBlocked):
            gate.checked_run(args, runner=spy(calls))
        assert not calls


@pytest.mark.parametrize(
    "args,expected", [(["pr", "list"], 0), (["issue", "comment", "1", "--body", TOKEN], 2), (["api", "graphql"], 2)]
)
def test_raw_entry_main_exact_admission(args, expected, tmp_path, monkeypatch, capsys):
    from scripts.opsec import gh_entry

    executable = tmp_path / "real-gh"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    monkeypatch.setattr(sys, "argv", ["entry", str(executable), str(ROOT / "scripts/agent_runtime/shims/gh"), *args])
    monkeypatch.setenv("GH_REPO", "unit/public")
    assert gh_entry.main() == expected
    assert TOKEN not in capsys.readouterr().err


def test_raw_entry_masks_unexpected_failure(tmp_path, monkeypatch, capsys):
    from scripts.opsec import gh_entry

    executable = tmp_path / "real-gh"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    monkeypatch.setattr(sys, "argv", ["entry", str(executable), "unit-shim", "pr", "list"])

    def broken(*a, **k):
        raise RuntimeError(TOKEN)

    monkeypatch.setattr(gh_entry, "admit", broken)
    assert gh_entry.main() == 2
    assert TOKEN not in capsys.readouterr().err


@pytest.mark.parametrize(
    "environment,explicit,origin,expected",
    [
        ({}, None, "https://github.com/unit/public.git", "github.com/unit/public"),
        ({"GH_REPO": "unit/private"}, None, "unit/public", "github.com/unit/private"),
        ({"GH_REPO": "unit/private"}, "unit/public", "unit/private", "github.com/unit/public"),
        ({}, None, "not-a-repository", "unknown"),
    ],
)
def test_repository_resolution_is_exact_and_ordered(environment, explicit, origin, expected, tmp_path):
    from scripts.opsec.gh_snapshot import repository

    def local_read(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, origin, "")

    assert repository(tmp_path, environment, explicit, local_read) == expected


def test_repository_read_failure_is_unknown(tmp_path):
    from scripts.opsec.gh_snapshot import repository

    def broken(*a, **k):
        raise OSError(TOKEN)

    assert repository(tmp_path, {}, reader=broken) == "unknown"


@pytest.mark.parametrize(
    "path", ["/dev/null", "unit/../unit", "unit/extra/public/extra", "https://github.com/unit/private/issues/1"]
)
def test_repository_prefix_never_grants_private_exemption(path):
    assert not gate.is_private(gate.normalize_repository(path))


def test_real_matcher_cli_overhead_median_20_writes(gh_shim_sandbox, tmp_path):
    import shutil

    from tests.test_opsec_prepublish import real_tooling

    source = real_tooling()
    root, _shim, tooling = gh_shim_sandbox
    shutil.copyfile(source / "matcher.py", tooling / "matcher.py")
    shutil.copyfile(source / "rules.json", tooling / "rules.json")
    executable = tmp_path / "real-gh"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    body = tmp_path / "clean.md"
    body.write_text("a" * 10_240)
    timings = []
    for _ in range(20):
        start = time.perf_counter()
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.publish",
                "issue-comment",
                "--repo",
                "unit/public",
                "--number",
                "1",
                "--body-file",
                str(body),
            ],
            cwd=root,
            env={"PATH": os.defpath, "AGENT_REAL_GH": str(executable)},
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        timings.append((time.perf_counter() - start) * 1000)
    median = statistics.median(timings)
    print(f"CLI writes real matcher median 20 x 10KB: {median:.3f} ms")
    assert median < 200


@pytest.mark.parametrize(
    "reference",
    [
        "http://github.com/unit/public/issues/1",
        "https://github.com/unit/public/issues/1?unit",
        "https://github.com/unit/private/../public/issues/1",
        "ssh://unit/public/1",
        "unit:branch",
    ],
)
def test_raw_private_reference_cannot_hide_a_public_resource(reference):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", "issue", "comment", reference, "--repo", "unit/private", "--body", TOKEN],
            runner=lambda *a, **k: pytest.fail("send"),
        )


@pytest.mark.parametrize(
    "path",
    [
        "repos/unit/private/../../public/issues/1",
        "repos/unit/private/%2e%2e/public/issues/1",
        "repos/unit/private/issues/%2funit",
        "repositories/1/issues/1",
        "https://api.github.com/repos/unit/private/issues/1",
    ],
)
def test_raw_private_api_exemption_rejects_opaque_and_traversing_paths(path):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", "api", path, "-f", "body=" + TOKEN],
            env={"GH_REPO": "unit/private"},
            runner=lambda *a, **k: pytest.fail("send"),
        )


def test_release_download_stdout_operand_is_valid_read():
    calls = []
    gate.checked_run(
        ["gh", "release", "download", "unit", "-p", "unit.gz", "-O", "-", "--repo", "unit/public"], runner=spy(calls)
    )
    assert len(calls) == 1


@pytest.mark.parametrize(
    "args",
    [["pr-review", "--verdict", TOKEN], ["issue-comment", "--number", TOKEN], ["issue-comment", "--unknown", TOKEN]],
)
def test_cli_parse_errors_never_echo_values(args, capsys):
    with pytest.raises(SystemExit) as error:
        pub.main(args)
    assert error.value.code == 2
    stderr = capsys.readouterr().err
    assert TOKEN not in stderr and "OPSEC:" in stderr


@pytest.mark.parametrize("command", ["version", "--version"])
def test_exact_cli_version_read_needs_no_matcher(command):
    calls = []
    gate.checked_run(["gh", command], runner=spy(calls))
    assert len(calls) == 1
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(["gh", command, "--body", TOKEN], runner=lambda *a, **k: pytest.fail("send"))


def test_transport_timeout_and_checked_failure(tmp_path):
    with pytest.raises(subprocess.TimeoutExpired):
        pub._run_transport([sys.executable, "-c", "import time; time.sleep(30)"], timeout=0.05, capture_output=True)
    with pytest.raises(subprocess.CalledProcessError) as failure:
        pub._run_transport(
            [sys.executable, "-c", "import sys; print('unit'); sys.exit(3)"], check=True, capture_output=True, text=True
        )
    assert failure.value.returncode == 3 and failure.value.output == "unit\n"


def test_catalog_c_safe_loader_matches_safe_loader(tmp_path, monkeypatch):
    import yaml

    monkeypatch.undo()

    root = tmp_path / "catalog-root"
    target = root / "scripts/config/fleet_repos.yaml"
    target.parent.mkdir(parents=True)
    content = "repos:\n  public:\n    github: unit/public\n    default: true\n"
    target.write_text(content)
    monkeypatch.setattr(gate, "ROOT", root)
    assert gate.catalog() == yaml.safe_load(content)["repos"]
    with pytest.raises(gate.PublishBlocked):
        target.write_text("!!python/object:unit {}")
        gate.catalog()


def test_mutated_artifact_name_is_validated_before_snapshot(tmp_path, synthetic_opsec):
    source = tmp_path / "unit.bin"
    source.write_bytes(b"\xffunit")
    asset = pub.Asset(source)
    asset.name = "../unit.bin"
    calls = []
    with pytest.raises(gate.PublishBlocked, match="invalid artifact name"):
        pub.publish("release-upload", repo="unit/public", tag="unit", assets=[asset], runner=spy(calls))
    assert not calls


@pytest.mark.parametrize("fields", [{}, {"base": "main"}, {"head": "unit"}, {"base": "", "head": "unit"}])
def test_pr_creation_cannot_publish_implicit_branch_names(fields):
    calls = []
    with pytest.raises(gate.PublishBlocked):
        pub.publish("pr-create", repo="unit/public", title="clean", body="clean", runner=spy(calls), **fields)
    assert not calls
