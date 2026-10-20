"""Only ``record_cf_verdict`` may publish review-verdict markers (#11127); synthetic data only."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.opsec import prepublish as gate
from scripts.orchestration import integration_sweep as sweep
from scripts.publish import github as pub
from scripts.review.record_cf_verdict import build_comment
from tests.common.github_cache_isolation import isolate_github_client_cache
from tests.opsec_fixtures import CATALOG

SHA = "a" * 40
MARKER = (
    f"<!-- cf-verdict v1 sha={SHA} task=hand started=2026-09-23T12:00:00.000001+00:00 "
    "verdict=BLOCKED model=gpt-6.1-sol family=openai -->"
)
COMMENT_VERBS = [
    ("issue-comment", {"number": 1}),
    ("issue-comment-json", {"number": 1}),
    ("pr-comment", {"number": 1}),
    ("pr-review", {"number": 1, "verdict": "comment"}),
    ("issue-close", {"number": 1}),
]


@pytest.fixture(autouse=True)
def _isolate_github_client_cache(tmp_path, monkeypatch):
    yield from isolate_github_client_cache(tmp_path, monkeypatch)


@pytest.fixture(autouse=True)
def catalog(monkeypatch):
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)


def spy(calls):
    def send(args, **kwargs):
        record = {"argv": args}
        for flag in ("--body-file", "--input"):
            if flag in args:
                record[flag] = Path(args[args.index(flag) + 1]).read_text()
        calls.append(record)
        return subprocess.CompletedProcess(args, 0, "{}", "")

    return send


def recorder_comment(**changes):
    fields = {
        "sha": SHA,
        "task_id": "review-one",
        "started": "2026-09-23T12:00:00.000001+00:00",
        "verdict": "APPROVED",
        "model": "gpt-6.1-sol",
        "family": "openai",
        "reply": "VERDICT: APPROVE",
    }
    return build_comment(**{**fields, **changes})


def test_comment_field_map_names_every_comment_verb():
    assert {verb: pub.COMMENT_FIELDS[verb] for verb, _ in COMMENT_VERBS} == pub.COMMENT_FIELDS
    for verb, key in pub.COMMENT_FIELDS.items():
        assert pub.SCHEMAS[verb][1][key] == "text"


@pytest.mark.parametrize("verb,fields", COMMENT_VERBS)
@pytest.mark.parametrize(
    "text",
    [
        MARKER,
        f"Looks fine.\n\n{MARKER}",
        f"{MARKER}\nTrailing prose.",
        "Quoting a marker: `<!-- cf-verdict v1 sha=... -->`",
        "<!-- cf-verdict",
    ],
)
def test_comment_verbs_refuse_hand_written_markers(synthetic_opsec, verb, fields, text):
    calls = []
    key = pub.COMMENT_FIELDS[verb]
    with pytest.raises(gate.PublishBlocked, match="CF_VERDICT_MARKER_REFUSED"):
        pub.publish(verb, repo="unit/public", runner=spy(calls), **fields, **{key: text})
    assert calls == []


@pytest.mark.parametrize("verb", ["issue-comment", "issue-comment-json", "pr-comment", "pr-review"])
def test_body_file_marker_is_refused(synthetic_opsec, tmp_path, verb):
    path = tmp_path / "reply.md"
    path.write_text(f"Hand-written verdict.\n\n{MARKER}\n")
    extra = {"verdict": "approve"} if verb == "pr-review" else {}
    calls = []
    with pytest.raises(gate.PublishBlocked, match="CF_VERDICT_MARKER_REFUSED"):
        pub.publish(verb, repo="unit/public", number=1, body_file=str(path), runner=spy(calls), **extra)
    assert calls == []


@pytest.mark.parametrize("verb", ["issue-comment", "pr-comment"])
def test_cli_refuses_hand_written_marker(synthetic_opsec, tmp_path, capsys, verb):
    path = tmp_path / "reply.md"
    path.write_text(recorder_comment())
    argv = [verb, "--repo", "unit/public", "--number", "1", "--body-file", str(path)]
    assert pub.main(argv, runner=lambda *a, **k: pytest.fail("send")) == 2
    assert "CF_VERDICT_MARKER_REFUSED" in capsys.readouterr().err


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"verdict": "CHANGES_REQUESTED"},
        {"review_mode": "red_team", "unknown_history": ["b" * 40]},
        {"withheld_findings": 2},
        {"app_bot": True},
    ],
)
def test_recorder_record_is_the_admitted_marker_carrier(synthetic_opsec, changes):
    body = recorder_comment(**changes)
    assert sweep.parse_marker(body) is not None
    calls = []
    record = pub.CfVerdictRecord(body)
    assert (
        pub.publish("issue-comment-json", repo="unit/public", number=1, body=record, runner=spy(calls)).returncode == 0
    )
    assert [json.loads(call["--input"])["body"] for call in calls] == [body]


@pytest.mark.parametrize("verb", ["issue-comment", "pr-comment", "pr-review"])
def test_record_is_admitted_only_on_the_recorder_verb(synthetic_opsec, verb):
    extra = {"verdict": "comment"} if verb == "pr-review" else {}
    calls = []
    with pytest.raises(gate.PublishBlocked, match="CF_VERDICT_MARKER_REFUSED"):
        pub.publish(
            verb, repo="unit/public", number=1, body=pub.CfVerdictRecord(recorder_comment()), runner=spy(calls), **extra
        )
    assert calls == []


def test_subclassed_record_is_refused(synthetic_opsec):
    class Lookalike(pub.CfVerdictRecord):
        pass

    calls = []
    with pytest.raises(gate.PublishBlocked, match="CF_VERDICT_MARKER_REFUSED"):
        pub.publish("issue-comment-json", repo="unit/public", number=1, body=Lookalike(MARKER), runner=spy(calls))
    assert calls == []


@pytest.mark.parametrize(
    "text",
    ["No marker here.", f"{MARKER}\nTrailing prose.", f"{MARKER}\n{MARKER}", f"Prose {MARKER} prose", None],
)
def test_record_type_refuses_malformed_records(text):
    with pytest.raises(gate.PublishBlocked, match="CF_VERDICT_MARKER_REFUSED"):
        pub.CfVerdictRecord(text)


def test_marker_free_comments_are_unaffected(synthetic_opsec):
    calls = []
    assert (
        pub.publish("pr-comment", repo="unit/public", number=1, body="<!-- mq-keeper -->", runner=spy(calls)).returncode
        == 0
    )
    assert len(calls) == 1


def test_sweep_reader_and_publisher_share_one_marker_prefix():
    assert sweep.MARKER_PREFIX is pub.CF_VERDICT_MARKER_PREFIX
