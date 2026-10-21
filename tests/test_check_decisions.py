"""Overdue stack-pin reviews sit beside expired decisions."""

from __future__ import annotations

import sys
from datetime import date, timedelta

import pytest

from scripts.audit import check_decisions as decisions

_TODAY = date(2026, 10, 16)


def _row(review_by: str, name: str = "uv") -> dict:
    return {
        "name": name,
        "pinned": "0.12.9",
        "source": ".github/actions/python-ci-env/action.yml",
        "owner": "DevOps",
        "review_by": review_by,
        "note": "uv pin",
    }


def test_overdue_row_is_reported() -> None:
    yesterday = (_TODAY - timedelta(days=1)).isoformat()

    found = decisions.find_overdue_reviews([_row(yesterday)], today=_TODAY)

    assert [row["name"] for row in found] == ["uv"]


def test_future_row_is_not_overdue() -> None:
    tomorrow = (_TODAY + timedelta(days=1)).isoformat()

    assert decisions.find_overdue_reviews([_row(tomorrow)], today=_TODAY) == []
    assert decisions.find_overdue_reviews([_row(_TODAY.isoformat())], today=_TODAY) == []


def test_malformed_row_is_rejected() -> None:
    with pytest.raises(decisions.StackPinsError, match="malformed review_by"):
        decisions.find_overdue_reviews([_row("next week")], today=_TODAY)


def test_overdue_reviews_print_beside_expired_decisions(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["check_decisions.py"])
    monkeypatch.setattr(
        decisions,
        "load_decisions",
        lambda: [
            {
                "id": "dec-x",
                "status": "active",
                "expires": "2020-01-01",
                "title": "Old choice",
            }
        ],
    )
    monkeypatch.setattr(decisions, "load_stack_pins", lambda path=None: [_row("2020-01-02")])

    assert decisions.main() == 1
    report = capsys.readouterr().out
    assert "dec-x | expired 2020-01-01 | Old choice" in report
    assert "uv | review_by 2020-01-02 | uv pin" in report
    assert report.index("dec-x") < report.index("Overdue stack review")
