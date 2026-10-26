"""Ordinary Fleet finalization alert age and uncertainty correctness."""

from datetime import UTC, datetime, timedelta

import pytest

from scripts import driver_blockers as blockers


@pytest.mark.parametrize(("minutes", "expected"), [(29, False), (30, False), (31, True)])
def test_finalization_age_boundary_uses_terminal_evidence(tmp_path, monkeypatch, minutes, expected):
    monkeypatch.delenv(blockers.FINALIZE_AGE_ENV, raising=False)
    now = datetime(2026, 10, 17, 12, tzinfo=UTC) + timedelta(minutes=minutes)
    age = blockers.finalization_age({"finished_at": "2026-10-17T12:00:00Z"}, now=now)
    assert age == {
        "age_minutes": minutes, "age_state": "known", "terminal": "2026-10-17T12:00:00+00:00",
        "threshold_minutes": 30, "configuration": "valid", "attention": expected,
    }


@pytest.mark.parametrize("stamp", [None, "", "invalid", "2026-10-17T12:00:00", "2026-10-18T12:00:00Z"])
def test_unknown_or_future_finalization_age_is_attention(tmp_path, monkeypatch, stamp):
    monkeypatch.delenv(blockers.FINALIZE_AGE_ENV, raising=False)
    age = blockers.finalization_age({"finished_at": stamp}, now=datetime(2026, 10, 17, 12, tzinfo=UTC))
    assert age["attention"] is True
    assert age["age_minutes"] is None
    assert age["age_state"] == ("future" if stamp == "2026-10-18T12:00:00Z" else "unknown")


@pytest.mark.parametrize("configured", ["0", "-1", "nan", "inf", "bad", ""])
def test_invalid_age_configuration_never_suppresses_attention(tmp_path, monkeypatch, configured):
    monkeypatch.setenv(blockers.FINALIZE_AGE_ENV, configured)
    age = blockers.finalization_age(
        {"finished_at": "2026-10-17T12:00:00Z"}, now=datetime(2026, 10, 17, 12, tzinfo=UTC),
    )
    assert age["attention"] is True
    assert age["configuration"] == "unknown" and age["threshold_minutes"] is None
