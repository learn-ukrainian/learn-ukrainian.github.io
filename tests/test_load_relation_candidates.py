import json
import sqlite3
from pathlib import Path

from scripts.lexicon import load_relation_candidates as loader


def _write_candidates(directory: Path) -> None:
    (directory / "paronym_candidates_fixture.json").write_text(
        json.dumps(
            {
                "source": "ukr-mova.in.ua",
                "pairs": [
                    {
                        "word_a": "Адреса",
                        "word_b": "адрес",
                        "source_page": "https://example.invalid/address",
                        "site_distinction": "This copyrighted source text must not be retained.",
                    },
                    {"word_a": "invalid token", "word_b": "адрес", "source_page": "https://example.invalid/bad"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (directory / "relation_candidates_fixture.json").write_text(
        json.dumps(
            [
                {
                    "relation": "synonym",
                    "word_a": "гарний",
                    "word_b": "вродливий",
                    "source": "miyklas.com.ua",
                    "distinction": "This source prose must not be retained.",
                },
                {
                    "relation": "synonym",
                    "word_a": "вродливий",
                    "word_b": "гарний",
                    "source": "miyklas.com.ua",
                },
                {
                    "relation": "antonym",
                    "word_a": "гарний",
                    "word_b": "неіснуюче",
                    "source": "miyklas.com.ua",
                },
                {
                    "relation": "antonym",
                    "word_a": "світлий",
                    "word_b": "темний",
                    "gloss_a": "з великою кількістю світла",
                    "gloss_b": "з малою кількістю світла",
                    "glosses_are_project_authored": True,
                    "source": "miyklas.com.ua",
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (directory / "relation_candidates_sample.json").write_text(
        json.dumps(
            {
                "source": "sample.invalid",
                "pairs": [
                    {
                        "relation": "synonym",
                        "word_a": "гарний",
                        "word_b": "чудовий",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_loader_upserts_normalized_pairs_and_discards_source_prose(tmp_path, monkeypatch) -> None:
    candidates_dir = tmp_path / "candidates"
    candidates_dir.mkdir()
    _write_candidates(candidates_dir)
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(loader, "is_exact_vesum_lemma", lambda word: word != "неіснуюче")

    first, counts = loader.load_candidates(db_path, candidates_dir)
    second, _ = loader.load_candidates(db_path, candidates_dir)

    assert first.accepted == 4
    assert first.inserted == 3
    assert first.skipped_invalid == 1
    assert first.skipped_vesum == 1
    assert counts == {
        ("miyklas.com.ua", "antonym"): 1,
        ("miyklas.com.ua", "synonym"): 2,
        ("ukr-mova.in.ua", "paronym"): 1,
    }
    assert second.inserted == 0
    assert second.unchanged == 4
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT relation, word_a, word_b, gloss_a, gloss_b, confidence FROM relation_pairs ORDER BY relation, word_a"
        ).fetchall()
    finally:
        conn.close()
    assert rows == [
        ("antonym", "світлий", "темний", "з великою кількістю світла", "з малою кількістю світла", "high"),
        ("paronym", "адрес", "адреса", "", "", "high"),
        ("synonym", "вродливий", "гарний", "", "", "high"),
    ]

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("UPDATE relation_pairs SET review_status = 'approved' WHERE relation = 'paronym'")
        conn.commit()
    finally:
        conn.close()
    loader.load_candidates(db_path, candidates_dir)
    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("SELECT review_status FROM relation_pairs WHERE relation = 'paronym'").fetchone() == (
            "approved",
        )
    finally:
        conn.close()


def test_loader_dry_run_is_read_only_and_source_filter_is_precise(tmp_path, monkeypatch) -> None:
    candidates_dir = tmp_path / "candidates"
    candidates_dir.mkdir()
    _write_candidates(candidates_dir)
    db_path = tmp_path / "sources.db"
    monkeypatch.setattr(loader, "is_exact_vesum_lemma", lambda word: word != "неіснуюче")

    summary, counts = loader.load_candidates(
        db_path,
        candidates_dir,
        source_filter="ukr-mova.in.ua",
        dry_run=True,
    )

    assert summary.accepted == 1
    assert summary.inserted == 0
    assert counts == {("ukr-mova.in.ua", "paronym"): 1}
    assert not db_path.exists()


def test_loader_excludes_relation_candidate_sample_artifact(tmp_path, monkeypatch) -> None:
    candidates_dir = tmp_path / "candidates"
    candidates_dir.mkdir()
    _write_candidates(candidates_dir)
    monkeypatch.setattr(loader, "is_exact_vesum_lemma", lambda word: True)

    summary, counts = loader.load_candidates(tmp_path / "sources.db", candidates_dir, dry_run=True)

    assert summary.accepted == 5
    assert ("sample.invalid", "synonym") not in counts
