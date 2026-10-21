from __future__ import annotations

import io
import sys

import pytest

from scripts.audit import lint_pr_closing_references


@pytest.mark.parametrize(
    "body, issue",
    [
        ("This PR does not close #42.", "42"),
        ("Do not close #43 until the follow-up completes.", "43"),
        ("This won't close #44.", "44"),
        ("The migration ships without closing #45.", "45"),
    ],
)
def test_negated_closing_references_are_rejected(body: str, issue: str) -> None:
    violations = lint_pr_closing_references.scan_text(body)

    assert len(violations) == 1
    assert f"#{issue}" in violations[0].phrase


@pytest.mark.parametrize(
    "body",
    [
        "Refs #42.",
        "This PR leaves #42 open.",
        "Closes #42 after the acceptance criteria are complete.",
        "The change does not close the browser window.",
    ],
)
def test_safe_or_non_reference_prose_is_accepted(body: str) -> None:
    assert lint_pr_closing_references.scan_text(body) == []


def test_stdin_guard_fails_for_a_disposable_pr_body(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("This PR does not close #42."))

    assert lint_pr_closing_references.main(["--stdin"]) == 1
    assert "negated GitHub closing reference" in capsys.readouterr().out
