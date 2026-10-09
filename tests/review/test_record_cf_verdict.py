"""Runtime Sources-call gate for Ukrainian verdict publication (#10074)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from scripts import delegate
from scripts.orchestration import integration_sweep as sweep
from scripts.orchestration import merge_queue_keeper as keeper
from scripts.review import record_cf_verdict as recorder
from scripts.review.language_lane import is_ukrainian_review
from tests.test_record_cf_verdict import SHA, setup_record, write_task


@pytest.fixture(autouse=True)
def recorder_matcher(synthetic_opsec):
    from tests.opsec_fixtures import synthetic_rules

    rules = synthetic_rules(rule="3-absolute-path", level=3, pattern=r"(?<![<\w:])/[A-Za-z][^\s`'\"<>),;\]}|*]*")
    (synthetic_opsec / "rules.json").write_text(json.dumps(rules))


@pytest.mark.parametrize("count", [1, 3])
@pytest.mark.parametrize(
    "classification",
    [
        {"review_profile": "ukrainian"},
        {"review_profile": " Ukrainian "},
        {"review_language_lane": True},
        {"language_lane": True},
        {"research_task_family": "ukrainian-review"},
        {"task_family": "ukrainian-authoring"},
    ],
)
def test_ukrainian_review_with_sources_calls_accepted(monkeypatch, tmp_path, count, classification):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    statuses = []
    original_status = recorder.post_commit_status

    def capture_status(**kwargs):
        statuses.append(kwargs)
        original_status(**kwargs)

    monkeypatch.setattr(recorder, "post_commit_status", capture_status)
    write_task(tasks, sources_mcp_call_count=count, **classification)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["verdict"] == "APPROVED"
    assert result["status"] == "posted"
    assert len(comments) == 1
    assert calls == {"posts": 1, "statuses": 1}
    assert f"Sources MCP calls: {count}\n" in comments[0]["body"].split("<details>", 1)[0]
    assert f"sources_calls={count}" in comments[0]["body"].splitlines()[-1]
    marker = recorder.parse_marker(comments[0]["body"])
    assert marker["sources_calls"] == count
    assert marker["review_profile"] == "ukrainian"
    assert f"sources={count}" in statuses[0]["description"]
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == "APPROVED"
    assert keeper._recorded_approval_for_head(comments, SHA, "fleet")
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert calls == {"posts": 1, "statuses": 2}


@pytest.mark.parametrize("verdict", ["APPROVE", "REQUEST_CHANGES", "BLOCKED"])
@pytest.mark.parametrize("count", [0, None, -1, True, "1", 1.0])
def test_ukrainian_review_without_known_positive_count_refused_before_network(
    monkeypatch, tmp_path, verdict, count
):
    tasks = tmp_path / "tasks"
    write_task(tasks, reply=f"VERDICT: {verdict}", review_profile="ukrainian", sources_mcp_call_count=count)

    def unexpected_network(*args, **kwargs):
        pytest.fail("Sources evidence must be checked before GitHub lookup or publication")

    monkeypatch.setattr(recorder, "_run_json", unexpected_network)
    reason = "zero Sources MCP calls" if count == 0 else "call count unknown"
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", task_root=tasks, lock_root=tmp_path / "locks")


def test_missing_runtime_count_cannot_be_replaced_by_reviewer_prose(tmp_path):
    tasks = tmp_path / "tasks"
    write_task(tasks, review_profile="ukrainian", reply="Used mcp__sources__verify_words.\nVERDICT: APPROVE")
    with pytest.raises(recorder.RecordError, match="call count unknown"):
        recorder.record("review-one", task_root=tasks, lock_root=tmp_path / "locks")


@pytest.mark.parametrize("count", [0, None])
@pytest.mark.parametrize(
    "classification",
    [
        {"review_language_lane": True},
        {"language_lane": True},
        {"research_task_family": "ukrainian-review"},
        {"task_family": "ukrainian-authoring"},
    ],
)
def test_task_classification_cannot_bypass_sources_gate(tmp_path, count, classification):
    tasks = tmp_path / "tasks"
    write_task(tasks, review_profile="code", sources_mcp_call_count=count, **classification)
    with pytest.raises(recorder.RecordError, match="Ukrainian review"):
        recorder.record("review-one", task_root=tasks, lock_root=tmp_path / "locks")


@pytest.mark.parametrize("count", [0, None])
def test_non_ukrainian_reviews_unaffected(monkeypatch, tmp_path, count):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    write_task(tasks, review_profile="code", sources_mcp_call_count=count)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["status"] == "posted"
    assert len(comments) == 1
    assert calls == {"posts": 1, "statuses": 1}


@pytest.mark.parametrize(
    "runtime,expected",
    [
        ({"tool_calls_total": 2, "tool_calls": [{"name": "mcp__sources__verify_words"}, {"name": "shell"}]}, 1),
        ({"tool_calls_total": 1, "tool_calls": [{"name": "mcp_sources_search_text"}]}, 1),
        ({"tool_calls_total": 0, "tool_calls": []}, 0),
        ({"tool_calls_total": 1, "tool_calls": [{"name": "mcp__other__verify_words"}]}, 0),
        ({"tool_calls_total": 1, "tool_calls": [{"name": "mcp__sources_fake__verify_words"}]}, 0),
        ({"tool_calls_total": 1, "tool_calls": [{"name": "mcp__sources__"}]}, 0),
        ({"tool_calls_total": None, "tool_calls": [{"name": "mcp__sources__verify_words"}]}, None),
        ({"tool_calls_total": 1, "tool_calls": []}, None),
        ({"tool_calls_total": True, "tool_calls": [{"name": "mcp__sources__verify_words"}]}, None),
        ({"tool_calls_total": 1, "tool_calls": [None]}, None),
        ({"tool_calls_total": 1, "tool_calls": [{}]}, None),
        ({}, None),
    ],
)
def test_sources_count_comes_from_runtime_tool_names(runtime, expected):
    assert delegate._sources_mcp_call_count(SimpleNamespace(**runtime)) == expected


@pytest.mark.parametrize("mode", ["cross_family", "red_team"])
@pytest.mark.parametrize("profile,count", [("code", None), ("code", 0), ("code", 4), ("ukrainian", 4)])
def test_parse_marker_extracts_optional_integer_count(mode, profile, count):
    body = recorder.build_comment(
        sha=SHA, task_id="review-one", started="2026-09-23T12:00:00.000001+00:00",
        verdict="APPROVED", model="gpt-6.1-sol", family="openai", reply="VERDICT: APPROVE",
        review_mode=mode, review_profile=profile, sources_mcp_call_count=count,
    )
    marker = recorder.parse_marker(body)
    assert marker["sources_calls"] == count
    assert count is None or type(marker["sources_calls"]) is int


@pytest.mark.parametrize("mode", ["cross_family", "red_team"])
@pytest.mark.parametrize("verdict", ["APPROVED", "APPROVE"])
@pytest.mark.parametrize("count", [None, "0", "-1", "unknown", "True", "1.0"])
def test_ukrainian_marker_without_positive_count_refused(monkeypatch, tmp_path, mode, verdict, count):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    write_task(tasks, review_profile="ukrainian", sources_mcp_call_count=3)
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    valid = comments[0]
    body = recorder.build_comment(
        sha=SHA, task_id="later", started="2026-09-23T12:00:01.000001+00:00",
        verdict=verdict, model="gpt-6.1-sol", family="openai", reply=f"VERDICT: {verdict}",
        review_mode=mode, review_profile="ukrainian", sources_mcp_call_count=3,
    )
    body = body.replace(" sources_calls=3", "" if count is None else f" sources_calls={count}")
    body = body.replace("Sources MCP calls: 3\n", "" if count is None else f"Sources MCP calls: {count}\n")
    invalid = {**valid, "body": body}
    assert recorder.parse_marker(body) is None
    assert sweep.lookup_verdict([valid, invalid], SHA, "fleet").state == "unknown"
    assert not keeper._recorded_approval_for_head([invalid], SHA, "fleet")
    assert not keeper._ever_approved([invalid], "fleet")


@pytest.mark.parametrize("replacement", ["sources_calls=2", "sources_calls=3 sources_calls=3"])
def test_sources_marker_must_match_published_count(replacement):
    body = recorder.build_comment(
        sha=SHA, task_id="review-one", started="2026-09-23T12:00:00.000001+00:00",
        verdict="APPROVED", model="gpt-6.1-sol", family="openai", reply="VERDICT: APPROVE",
        review_profile="ukrainian", sources_mcp_call_count=3,
    ).replace("sources_calls=3", replacement)
    assert recorder.parse_marker(body) is None


def test_removing_profile_marker_cannot_hide_missing_sources_count():
    body = recorder.build_comment(
        sha=SHA, task_id="review-one", started="2026-09-23T12:00:00.000001+00:00",
        verdict="APPROVED", model="gpt-6.1-sol", family="openai", reply="VERDICT: APPROVE",
        review_profile="ukrainian", sources_mcp_call_count=3,
    ).replace(" review_profile=ukrainian sources_calls=3", "")
    assert recorder.parse_marker(body) is None


def test_changed_runtime_count_conflicts_with_existing_marker(monkeypatch, tmp_path):
    tasks, _, calls = setup_record(monkeypatch, tmp_path)
    write_task(tasks, review_profile="ukrainian", sources_mcp_call_count=3)
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    write_task(tasks, review_profile="ukrainian", sources_mcp_call_count=4)
    with pytest.raises(recorder.RecordError, match="conflicts with task"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert calls == {"posts": 1, "statuses": 1}


@pytest.mark.parametrize("classification,expected", [
    ({"review_profile": " Ukrainian "}, True),
    ({"review_language_lane": True}, True),
    ({"language_lane": True}, True),
    ({"research_task_family": " UKRAINIAN-REVIEW "}, True),
    ({"task_family": "ukrainian-authoring"}, True),
    ({"research_task_family": "generic"}, False),
    ({}, False),
])
def test_shared_ukrainian_classification(classification, expected):
    assert is_ukrainian_review(classification) is expected
