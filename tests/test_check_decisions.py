"""Overdue stack-pin reviews sit beside expired decisions."""

from __future__ import annotations

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


def test_malformed_row_is_rejected() -> None:
    with pytest.raises(decisions.StackPinsError, match="malformed review_by"):
        decisions.find_overdue_reviews([_row("next week")], today=_TODAY)
