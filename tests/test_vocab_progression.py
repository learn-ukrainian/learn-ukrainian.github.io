"""Tests for scripts/analytics/vocab_progression.py."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from analytics.vocab_progression import ProjectPaths, analyze_level, module_progression_delta


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


def test_progression_happy_path(tmp_path):
    paths = _build_fake_project(tmp_path)

    analysis = analyze_level("a1", paths)

    cat = next(item for item in analysis.word_progressions if item.lemma == "кіт")
    assert cat.first_intro == "m1"
    assert cat.rep_count == 2
    assert cat.spacing == [1, 3]

    delta = module_progression_delta("a1", "m1", paths)
    assert delta == {"delta": 2, "premature": 0, "gaps": 0, "well_paced": 1}


def test_gap_detection_from_plan_hints(tmp_path):
    paths = _build_fake_project(tmp_path)

    analysis = analyze_level("a1", paths)

    gap_terms = {item.term for item in analysis.gaps}
    assert "сонце" in gap_terms

    delta = module_progression_delta("a1", "m3", paths)
    assert delta["gaps"] == 1
    assert delta["delta"] == -1


def test_premature_detection(tmp_path):
    paths = _build_fake_project(tmp_path)

    analysis = analyze_level("a1", paths)

    assert any(item.lemma == "яхта" and item.level == "B1" and item.module == "m2" for item in analysis.premature)

    delta = module_progression_delta("a1", "m2", paths)
    assert delta["premature"] == 1
    assert delta["delta"] == -5


def test_non_vesum_words_are_reported(tmp_path):
    paths = _build_fake_project(tmp_path)

    analysis = analyze_level("a1", paths)

    assert any(item.surface == "блабла" and item.modules == ["m5"] for item in analysis.non_vesum)


def test_cli_smoke(tmp_path):
    paths = _build_fake_project(tmp_path)
    python_bin = REPO_ROOT / ".venv" / "bin" / "python"

    result = subprocess.run(
        [str(python_bin), "scripts/analytics/vocab_progression.py", "a1"],
        cwd=REPO_ROOT,
        env={**os.environ, "VOCAB_PROGRESSION_PROJECT_ROOT": str(paths.root)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "# Vocabulary Progression Report: A1" in result.stdout
    assert "яхта" in result.stdout
