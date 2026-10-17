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

# Catalog models whose lifecycle is active or fallback, in map order.
_ADMITTED_MODEL_IDS = (
    "gpt-6.1-sol, gpt-6-luna, claude-fable-5-1, claude-opus-5-5, "
    "claude-haiku-5-5, claude-sonnet-5-5, gemini-3.8-flash-high, "
    "gemini-3.1-pro-high, grok-4.7, kimi-code/k3, kimi-code/k3-256k, "
    "kimi-k3-max, kimi-code/kimi-for-coding, "
    "kimi-code/kimi-for-coding-highspeed, glm-5.3, deepseek-v4.1-flash, "
    "poolside/laguna-s-2.1, poolside/laguna-xs-2.1, poolside/laguna-m.1, "
    "composer-2.5, google-ais/gemma-4-31b-it, glm-5.3-flash"
)


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
    assert by_name["pinned-model-ids"]["pinned"] == _ADMITTED_MODEL_IDS
    assert "schema_version model-catalog.v1" in by_name["pinned-model-ids"]["note"]
    assert find_overdue_reviews(rows, today=date(2026, 10, 16)) == []


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
