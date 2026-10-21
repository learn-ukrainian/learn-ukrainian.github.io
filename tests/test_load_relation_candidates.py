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

    first, counts = loader.load_candidates(db_path, candidates_dir, heritage_db_path=None)
    second, _ = loader.load_candidates(db_path, candidates_dir, heritage_db_path=None)

    assert first.accepted == 5
    assert first.inserted == 4
    assert first.skipped_invalid == 1
    assert first.skipped_vesum == 0
    assert first.kept_via_trusted_source == 1
    assert counts == {
        ("miyklas.com.ua", "antonym"): 2,
        ("miyklas.com.ua", "synonym"): 2,
        ("ukr-mova.in.ua", "paronym"): 1,
    }
    assert second.inserted == 0
    assert second.unchanged == 5
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT relation, word_a, word_b, gloss_a, gloss_b, confidence FROM relation_pairs ORDER BY relation, word_a"
        ).fetchall()
    finally:
        conn.close()
    assert rows == [
        ("antonym", "гарний", "неіснуюче", "", "", "high"),
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
    loader.load_candidates(db_path, candidates_dir, heritage_db_path=None)
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


def test_loader_keeps_exact_dictionary_attestation_and_drops_untrusted_fake_pair(tmp_path, monkeypatch, capsys) -> None:
    candidates_dir = tmp_path / "candidates"
    candidates_dir.mkdir()
    (candidates_dir / "relation_candidates_heritage.json").write_text(
        json.dumps(
            [
                {
                    "relation": "paronym",
                    "word_a": "віла",
                    "word_b": "вілла",
                    "source": "untrusted.example",
                },
                {
                    "relation": "paronym",
                    "word_a": "вигадслов",
                    "word_b": "несправньо",
                    "source": "untrusted.example",
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    heritage_db = tmp_path / "heritage.db"
    conn = sqlite3.connect(heritage_db)
    try:
        conn.executescript(
            """
            CREATE TABLE grinchenko (word TEXT);
            CREATE TABLE esum_etymology (lemma TEXT);
            CREATE TABLE slovnyk_me_entries (
                normalized_word TEXT,
                dictionary_slug TEXT
            );
            """
        )
        # Exact СУМ-20 snapshot evidence for віла; a related or prefix match
        # must not clear the unrelated fake pair.
        conn.execute(
            "INSERT INTO slovnyk_me_entries(normalized_word, dictionary_slug) VALUES (?, ?)",
            ("віла", "newsum"),
        )
        conn.commit()
    finally:
        conn.close()
    monkeypatch.setattr(loader, "is_exact_vesum_lemma", lambda word: word == "вілла")

    summary, counts = loader.load_candidates(
        tmp_path / "sources.db",
        candidates_dir,
        dry_run=True,
        heritage_db_path=heritage_db,
    )

    assert summary.accepted == 1
    assert summary.kept_via_heritage == 1
    assert summary.kept_via_trusted_source == 0
    assert summary.still_dropped == 1
    assert summary.skipped_vesum == 1
    assert summary.dropped_lemmas == {"вигадслов": 1, "несправньо": 1}
    assert counts == {("untrusted.example", "paronym"): 1}
    loader._print_summary(summary, counts)
    output = capsys.readouterr().out
    assert "kept_via_heritage=1 kept_via_trusted_source=0 still_dropped=1" in output
    assert "dropped_lemmas=вигадслов,несправньо" in output
