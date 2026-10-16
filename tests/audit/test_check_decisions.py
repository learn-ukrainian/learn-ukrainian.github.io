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
