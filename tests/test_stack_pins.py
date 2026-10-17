"""stack_pins.yaml loads, and the loader rejects a broken row."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from scripts.audit.check_decisions import StackPinsError, find_overdue_reviews, load_stack_pins

_VALID_ROW = """\
pins:
  - name: python
    pinned: "3.12.14"
    source: .python-version
    owner: DevOps
    review_by: "2026-11-16"
    note: interpreter pin
"""


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "stack_pins.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_repo_pins_load_and_match_recorded_versions() -> None:
    rows = load_stack_pins()
    by_name = {row["name"]: row for row in rows}

    assert by_name["python"]["pinned"] == "3.12.14"
    assert by_name["python"]["source"] == ".python-version"
    assert by_name["node"]["pinned"] == "22"
    assert by_name["node"]["source"] == ".nvmrc"
    assert by_name["uv"]["pinned"] == "0.12.9"
    assert by_name["entire"]["pinned"] == "0.8.42"
    assert by_name["postgresql"]["pinned"] == "16"
    assert by_name["ci-literals"]["pinned"] == "ubuntu-latest"
    assert by_name["gh"]["pinned"] == "unknown"
    assert by_name["gh"]["source"] == "host"
    assert by_name["claude-code"]["owner"] == "Infra"
    assert by_name["claude-code"]["review_by"] == "2026-10-30"
    assert by_name["python"]["review_by"] == "2026-11-16"
    assert find_overdue_reviews(rows, today=date(2026, 10, 16)) == []


def test_missing_owner_fails(tmp_path: Path) -> None:
    body = _VALID_ROW.replace("    owner: DevOps\n", "")

    with pytest.raises(StackPinsError, match="missing an owner"):
        load_stack_pins(_write(tmp_path, body))


def test_malformed_date_fails(tmp_path: Path) -> None:
    body = _VALID_ROW.replace('review_by: "2026-11-16"', 'review_by: "next week"')

    with pytest.raises(StackPinsError, match="malformed review_by"):
        load_stack_pins(_write(tmp_path, body))


def test_duplicate_name_fails(tmp_path: Path) -> None:
    body = _VALID_ROW + _VALID_ROW.split("pins:\n", 1)[1]

    with pytest.raises(StackPinsError, match="duplicate stack pin name: python"):
        load_stack_pins(_write(tmp_path, body))
