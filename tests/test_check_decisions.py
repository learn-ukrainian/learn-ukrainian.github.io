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


@pytest.mark.parametrize("content", ["", "streams: {epics: null}", "streams: {epics: {epics: [null]}}"])
def test_malformed_stream_registry_creates_no_issue(content, monkeypatch, tmp_path) -> None:
    registry = tmp_path / "issue_streams.yaml"
    registry.write_text(content, encoding="utf-8")
    real_load = decisions.issue_stream_audit.load_registry
    monkeypatch.setattr(
        decisions.issue_stream_audit, "load_registry", lambda **kwargs: real_load(registry, **kwargs)
    )
    monkeypatch.setattr(decisions, "request_run", lambda *args, **kwargs: pytest.fail("send"))

    assert decisions.create_issue({"id": "D", "title": "t", "expires": "2026-01-01", "date": "2026-01-01"}) is None
