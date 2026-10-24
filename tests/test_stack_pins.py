"""stack_pins.yaml loads, and the loader rejects a broken row."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit.check_decisions import StackPinsError, load_stack_pins

_VALID_ROW = """\
pins:
  - name: python
    pinned: "3.12.15"
    source: .python-version
    owner: DevOps
    review_by: "2026-11-16"
    note: interpreter pin
"""


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "stack_pins.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_missing_owner_fails(tmp_path: Path) -> None:
    body = _VALID_ROW.replace("    owner: DevOps\n", "")

    with pytest.raises(StackPinsError, match="missing an owner"):
        load_stack_pins(_write(tmp_path, body))


def test_malformed_date_fails(tmp_path: Path) -> None:
    body = _VALID_ROW.replace('review_by: "2026-11-16"', 'review_by: "next week"')

    with pytest.raises(StackPinsError, match="malformed review_by"):
        load_stack_pins(_write(tmp_path, body))


def test_unquoted_impossible_date_fails(tmp_path: Path) -> None:
    body = _VALID_ROW.replace('review_by: "2026-11-16"', "review_by: 2026-02-30")

    with pytest.raises(StackPinsError, match="failed to parse") as raised:
        load_stack_pins(_write(tmp_path, body))
    assert type(raised.value) is StackPinsError


def test_duplicate_name_fails(tmp_path: Path) -> None:
    body = _VALID_ROW + _VALID_ROW.split("pins:\n", 1)[1]

    with pytest.raises(StackPinsError, match="duplicate stack pin name: python"):
        load_stack_pins(_write(tmp_path, body))
