"""Regression coverage for teacher-facing VESUM normalization and phrase recovery."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.atlas.teacher_vesum_attest import attest_lemma


def _vesum_db(path: Path) -> Path:
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, tags TEXT, pos TEXT)")
    connection.executemany(
        "INSERT INTO forms VALUES (?, ?, ?, ?)",
        [
            ("вибухати", "вибухати", "verb:imperf", "verb"),
            ("виходити", "виходити", "verb:imperf", "verb"),
            ("в'язниця", "в'язниця", "noun:inanim:f", "noun"),
        ],
    )
    connection.commit()
    connection.close()
    return path


@pytest.fixture
def vesum_db(tmp_path: Path) -> Path:
    return _vesum_db(tmp_path / "vesum.db")


def test_attests_title_cased_single_lemma(vesum_db: Path) -> None:
    result = attest_lemma("Вибухати", vesum_db=vesum_db)

    assert result["attested"] is True
    assert result["method"] == "full_string"
    assert result["matched_lemmas"] == ["вибухати"]


def test_attests_multiword_expression_by_head(vesum_db: Path) -> None:
    result = attest_lemma("виходити з ладу", vesum_db=vesum_db)

    assert result["attested"] is True
    assert result["method"] == "head_token"
    assert result["matched_forms"] == ["виходити"]


def test_folds_curly_apostrophe_before_vesum_lookup(vesum_db: Path) -> None:
    result = attest_lemma("В’язниця", vesum_db=vesum_db)

    assert result["attested"] is True
    assert result["method"] == "full_string"
    assert result["matched_lemmas"] == ["в'язниця"]


def test_keeps_named_true_miss_unattested(vesum_db: Path) -> None:
    result = attest_lemma("нініяково", vesum_db=vesum_db)

    assert result["attested"] is False
    assert result["method"] == "none"
    assert result["matched_forms"] == []
