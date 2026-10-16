"""Stale-decision issue creation fails closed when the issue lookup is refused (#10792)."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from scripts.audit import check_decisions

REFUSALS = {
    "rate_refusal_reset_only": (75, json.dumps({"error": "github_rate_limited", "reset_at": 1790000000})),
    "generic_non_zero": (1, json.dumps({"error": "github_http_error", "reset_at": None, "status": 502})),
    "empty_output": (0, ""),
    "malformed_output": (0, "not json"),
    "refusal_json_with_zero_rc": (0, json.dumps({"error": "github_rate_limited", "reset_at": None})),
}


def _decision(dec_id: str) -> dict:
    return {
        "id": dec_id,
        "title": "t",
        "status": "active",
        "expires": "2020-01-01",
        "date": "2019-01-01",
    }


def _run_main(monkeypatch, decisions, responses):
    """Run ``main --create-issues`` against canned lookup results; return (lookups, creates, rc)."""
    lookups, creates = [], []

    def run(command, **kwargs):
        lookups.append(command)
        returncode, stdout = responses[min(len(lookups), len(responses)) - 1]
        return subprocess.CompletedProcess(command, returncode, stdout, "")

    monkeypatch.setattr(check_decisions.github_client, "run", run)
    monkeypatch.setattr(check_decisions, "load_decisions", lambda: decisions)
    monkeypatch.setattr(check_decisions, "_ensure_label_exists", lambda: creates.append("label"))
    monkeypatch.setattr(check_decisions, "create_issue", lambda dec: creates.append(dec["id"]) or "url")
    monkeypatch.setattr(sys, "argv", ["check_decisions.py", "--create-issues"])
    return lookups, creates, check_decisions.main()


@pytest.mark.parametrize("shape", REFUSALS)
def test_issue_exists_is_unknown_for_every_refusal_shape(monkeypatch, shape) -> None:
    returncode, stdout = REFUSALS[shape]
    monkeypatch.setattr(
        check_decisions.github_client,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, returncode, stdout, ""),
    )
    assert check_decisions._gh_issue_exists("D-1") is None


@pytest.mark.parametrize("failure", [subprocess.TimeoutExpired("gh", 15), FileNotFoundError("gh")])
def test_issue_exists_is_unknown_when_the_call_fails(monkeypatch, failure) -> None:
    def broken(command, **kwargs):
        raise failure

    monkeypatch.setattr(check_decisions.github_client, "run", broken)
    assert check_decisions._gh_issue_exists("D-1") is None


@pytest.mark.parametrize("shape", REFUSALS)
def test_refused_lookup_skips_creation_and_stops_further_lookups(monkeypatch, capsys, shape) -> None:
    decisions = [_decision("D-1"), _decision("D-2")]
    lookups, creates, rc = _run_main(monkeypatch, decisions, [REFUSALS[shape]])
    out = capsys.readouterr().out
    assert rc == 1
    assert creates == []  # neither "an issue exists" nor a duplicate create
    assert len(lookups) == 1  # D-2 is not looked up after the refusal
    assert out.count("GH issue lookup unavailable") == 2
    assert "already exists" not in out


def test_known_lookup_results_behave_as_before(monkeypatch, capsys) -> None:
    decisions = [_decision("D-1"), _decision("D-2")]
    lookups, creates, rc = _run_main(
        monkeypatch, decisions, [(0, json.dumps([{"number": 5}])), (0, "[]")]
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert len(lookups) == 2
    assert creates == ["label", "D-2"]
    assert "GH issue already exists" in out
    assert "Created: url" in out
    assert "unavailable" not in out


@pytest.mark.parametrize(
    "stdout",
    [
        "[null]",
        '[{"error": "github_rate_limited"}]',
        '[{"error": "github_rate_limited", "reset_at": null}]',
        "[{}]",
        '["x"]',
        '[{"number": true}]',
        '[{"number": 5}, null]',
        '[{"number": 5}, {"error": "github_http_error"}]',
    ],
)
def test_malformed_list_elements_are_unknown_not_issue_exists(monkeypatch, stdout) -> None:
    """``[null]`` and an error object in a list used to read as "issue exists" (#10792)."""
    monkeypatch.setattr(
        check_decisions.github_client,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, stdout, ""),
    )
    assert check_decisions._gh_issue_exists("D-1") is None


def test_malformed_list_elements_skip_creation_in_main(monkeypatch, capsys) -> None:
    lookups, creates, rc = _run_main(monkeypatch, [_decision("D-1"), _decision("D-2")], [(0, "[null]")])
    out = capsys.readouterr().out
    assert rc == 1
    assert creates == []
    assert len(lookups) == 1
    assert "already exists" not in out
    assert out.count("GH issue lookup unavailable") == 2


def test_issue_exists_is_unknown_on_any_process_error(monkeypatch) -> None:
    def broken(command, **kwargs):
        raise PermissionError("gh")

    monkeypatch.setattr(check_decisions.github_client, "run", broken)
    assert check_decisions._gh_issue_exists("D-1") is None


# --- Round 3: one strict parse-or-unknown choke point for the issue list (#10792) ---------------

_BAD_ISSUE_LISTS = {
    "number_zero": [{"number": 0}],
    "number_negative": [{"number": -1}],
    "number_string": [{"number": "5"}],
    "number_float": [{"number": 5.0}],
    "number_null": [{"number": None}],
    "number_false": [{"number": False}],
    "number_true": [{"number": True}],
    "number_list": [{"number": [5]}],
    "number_object": [{"number": {"value": 5}}],
    "number_missing": [{"title": "x"}],
    "valid_then_zero": [{"number": 5}, {"number": 0}],
    "valid_then_null": [{"number": 5}, None],
    "valid_then_nested_error": [{"number": 5}, {"error": {"message": "x"}}],
    "object_container": {"number": 5},
    "object_wrapping_list": {"items": [{"number": 5}]},
    "nested_error_object": {"error": {"message": "x", "status": 502}},
    "json_null": None,
    "json_true": True,
    "scalar_int": 5,
    "scalar_string": "[]",
    "nested_list": [[{"number": 5}]],
    "bare_int_element": [5],
    "bare_string_element": ["5"],
}


def _lookup_returning(monkeypatch, returncode, stdout):
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, returncode, stdout, "")

    monkeypatch.setattr(check_decisions.github_client, "run", run)
    return calls


@pytest.mark.parametrize("shape", _BAD_ISSUE_LISTS)
def test_issue_list_matrix_is_unknown_never_exists(monkeypatch, shape) -> None:
    """``[{"number": 0}]`` and ``[{"number": -1}]`` once reported that an issue already exists."""
    calls = _lookup_returning(monkeypatch, 0, json.dumps(_BAD_ISSUE_LISTS[shape]))
    assert check_decisions._gh_issue_exists("D-1") is None
    assert len(calls) == 1


@pytest.mark.parametrize("shape", _BAD_ISSUE_LISTS)
def test_issue_list_matrix_skips_creation_and_stops_further_lookups(monkeypatch, capsys, shape) -> None:
    lookups, creates, rc = _run_main(
        monkeypatch, [_decision("D-1"), _decision("D-2")], [(0, json.dumps(_BAD_ISSUE_LISTS[shape]))]
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert creates == []
    assert len(lookups) == 1
    assert "already exists" not in out
    assert out.count("GH issue lookup unavailable") == 2


@pytest.mark.parametrize("stdout", [None, b"[]", b'[{"number": 5}]', 5, ["x"]])
def test_non_text_lookup_output_is_unknown(monkeypatch, stdout) -> None:
    calls = _lookup_returning(monkeypatch, 0, stdout)
    assert check_decisions._gh_issue_exists("D-1") is None
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("stdout", "expected"),
    [
        ("[]", False),
        ('[{"number": 1}]', True),
        ('[{"number": 5, "title": "x", "labels": []}]', True),
        ('[{"number": 5}, {"number": 6}]', True),
        (' [ ] \n', False),
    ],
)
def test_valid_issue_lists_keep_their_meaning(monkeypatch, stdout, expected) -> None:
    _lookup_returning(monkeypatch, 0, stdout)
    assert check_decisions._gh_issue_exists("D-1") is expected


@pytest.mark.parametrize(
    "stdout",
    [
        "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/123\n",
        "  https://github.com/o/r/issues/1  ",
    ],
)
def test_created_issue_url_is_accepted_only_in_its_exact_shape(monkeypatch, stdout) -> None:
    monkeypatch.setattr(
        check_decisions,
        "request_run",
        lambda *a, **kw: subprocess.CompletedProcess(["gh"], 0, stdout, ""),
    )
    assert check_decisions.create_issue(_decision("D-1") | {"alternatives": []}) == stdout.strip()


@pytest.mark.parametrize(
    "stdout",
    [
        "",
        "\n",
        "ok",
        "https://github.com/o/r/issues/0",
        "https://github.com/o/r/issues/-1",
        "https://github.com/o/r/issues/abc",
        "https://github.com/o/r/pull/5",
        "http://github.com/o/r/issues/5",
        "https://evil.example/o/r/issues/5",
        "https://github.com/o/r/issues/5\nhttps://github.com/o/r/issues/6",
        '{"error": "github_rate_limited"}',
        None,
        b"https://github.com/o/r/issues/5",
    ],
)
def test_created_issue_output_that_is_not_an_issue_url_is_a_failure(monkeypatch, stdout) -> None:
    monkeypatch.setattr(
        check_decisions,
        "request_run",
        lambda *a, **kw: subprocess.CompletedProcess(["gh"], 0, stdout, ""),
    )
    assert check_decisions.create_issue(_decision("D-1") | {"alternatives": []}) is None
