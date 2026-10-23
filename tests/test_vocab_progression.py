"""Tests for scripts/analytics/vocab_progression.py."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.reads_content

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from analytics.vocab_progression import ProjectPaths, analyze_level


def _write_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _build_fake_project(tmp_path: Path) -> ProjectPaths:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    (curriculum_root / "a1" / "vocabulary").mkdir(parents=True)
    (curriculum_root / "plans" / "a1").mkdir(parents=True)
    (tmp_path / "data").mkdir(parents=True)

    _write_yaml(
        curriculum_root / "curriculum.yaml",
        {
            "version": "1.0",
            "levels": {
                "a1": {
                    "type": "core",
                    "modules": ["m1", "m2", "m3", "m4", "m5"],
                }
            },
        },
    )

    _write_yaml(
        curriculum_root / "plans" / "a1" / "m1.yaml",
        {"slug": "m1", "vocabulary_hints": {"required": ["кіт (cat)"]}},
    )
    _write_yaml(
        curriculum_root / "plans" / "a1" / "m2.yaml",
        {"slug": "m2", "vocabulary_hints": {"required": ["яхта (yacht)"]}},
    )
    _write_yaml(
        curriculum_root / "plans" / "a1" / "m3.yaml",
        {"slug": "m3", "vocabulary_hints": {"required": ["сонце (sun)"]}},
    )
    _write_yaml(
        curriculum_root / "plans" / "a1" / "m4.yaml",
        {"slug": "m4", "prior_words": ["кіт"]},
    )
    _write_yaml(
        curriculum_root / "plans" / "a1" / "m5.yaml",
        {"slug": "m5", "vocabulary_hints": {"required": ["блабла"]}},
    )

    _write_yaml(
        curriculum_root / "a1" / "vocabulary" / "m1.yaml",
        {"vocabulary": [{"word": "кіт", "translation": "cat"}]},
    )
    _write_yaml(
        curriculum_root / "a1" / "vocabulary" / "m2.yaml",
        {
            "vocabulary": [
                {"word": "кота", "translation": "cat"},
                {"word": "яхта", "translation": "yacht"},
            ]
        },
    )
    _write_yaml(
        curriculum_root / "a1" / "vocabulary" / "m5.yaml",
        {
            "vocabulary": [
                {"word": "кіт", "translation": "cat"},
                {"word": "блабла", "translation": "nonsense"},
            ]
        },
    )

    vesum_db = tmp_path / "data" / "vesum.db"
    with sqlite3.connect(vesum_db) as conn:
        conn.execute(
            "CREATE TABLE forms (word_form TEXT NOT NULL, lemma TEXT NOT NULL, tags TEXT NOT NULL, pos TEXT NOT NULL)"
        )
        conn.executemany(
            "INSERT INTO forms(word_form, lemma, tags, pos) VALUES (?, ?, ?, ?)",
            [
                ("кіт", "кіт", "noun", "noun"),
                ("кота", "кіт", "noun", "noun"),
                ("яхта", "яхта", "noun", "noun"),
                ("сонце", "сонце", "noun", "noun"),
            ],
        )

    sources_db = tmp_path / "data" / "sources.db"
    with sqlite3.connect(sources_db) as conn:
        conn.execute(
            """
            CREATE TABLE puls_cefr (
                id INTEGER PRIMARY KEY,
                word TEXT NOT NULL,
                guideword TEXT DEFAULT '',
                level TEXT DEFAULT '',
                pos TEXT DEFAULT '',
                type TEXT DEFAULT '',
                text TEXT NOT NULL DEFAULT '',
                source TEXT DEFAULT ''
            )
            """
        )
        conn.executemany(
            "INSERT INTO puls_cefr(word, level, text) VALUES (?, ?, ?)",
            [
                ("кіт", "A1", "кіт (A1)"),
                ("яхта", "B1", "яхта (B1)"),
                ("сонце", "A1", "сонце (A1)"),
            ],
        )

    return ProjectPaths.from_root(tmp_path)


def test_non_vesum_words_are_reported(tmp_path):
    paths = _build_fake_project(tmp_path)

    analysis = analyze_level("a1", paths)

    assert any(item.surface == "блабла" and item.modules == ["m5"] for item in analysis.non_vesum)
