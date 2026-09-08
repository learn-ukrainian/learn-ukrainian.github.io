from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from scripts.lexicon import admit_textbook_book_glossary as admit


def test_dmklinger_gloss_dedupes_and_caps_senses() -> None:
    index = {
        "мама": [
            ("noun", json.dumps(["mother", "mama", "mom", "mum", "extra sense"])),
        ]
    }
    gloss = admit.dmklinger_gloss(index, "мама")
    assert gloss == "mother; mama; mom"


def test_dmklinger_gloss_missing_returns_none() -> None:
    assert admit.dmklinger_gloss({}, "невідоме") is None


def test_uk_definition_prefers_sum20_over_vts() -> None:
    cache = {
        "lookup_word": "мама",
        "lookups": {
            "newsum": {"text": "мама МА́МА, и, ж. Ласкаве називання матері.", "word": "мама", "source_url": "u1"},
            "vts": {"text": "мама ма́ма -и, ж. Звертання до матері.", "word": "мама", "source_url": "u2"},
        },
    }
    text, source, url = admit.uk_definition(cache, "мама")
    assert source == "sum20"
    assert url == "u1"
    assert "МА́МА" in text or "Ласкаве" in text


def test_uk_definition_falls_back_to_vts() -> None:
    cache = {
        "lookup_word": "мама",
        "lookups": {"newsum": None, "vts": {"text": "мама ма́ма опис.", "word": "мама", "source_url": "u2"}},
    }
    _text, source, url = admit.uk_definition(cache, "мама")
    assert source == "vts"
    assert url == "u2"


def test_uk_definition_missing_returns_none() -> None:
    cache = {"lookup_word": "х", "lookups": {"newsum": None, "vts": None}}
    assert admit.uk_definition(cache, "х") is None


def test_en_gloss_prefers_dmklinger_then_ukreng() -> None:
    index = {"школа": [("noun", json.dumps(["school"]))]}
    cache = {"lookup_word": "школа", "lookups": {}}
    gloss, source = admit.en_gloss(cache, "школа", index)
    assert (gloss, source) == ("school", "dmklinger")

    cache2 = {"lookup_word": "тест", "lookups": {"ukreng": {"text": "тест test опис.", "word": "тест"}}}
    result = admit.en_gloss(cache2, "тест", {})
    assert result is not None
    assert result[1] == "ukreng"


def test_admit_candidates_requires_both_gates(monkeypatch) -> None:
    def fake_cache(lemma: str) -> dict:
        caches = {
            "мама": {"lookup_word": "мама", "lookups": {"newsum": {"text": "означення мами.", "word": "мама"}}},
            "хмара": {"lookup_word": "хмара", "lookups": {"newsum": None, "vts": None}},
        }
        return caches.get(lemma, {"lookup_word": lemma, "lookups": {}})

    monkeypatch.setattr(admit, "ensure_slovnyk_cache", fake_cache)
    dmklinger_index = {"мама": [("noun", json.dumps(["mother"]))]}
    candidates = [
        {"lemma": "мама", "pos": "noun", "count": 5, "locators": ["p.1"]},
        {"lemma": "хмара", "pos": "noun", "count": 2, "locators": ["p.2"]},
    ]
    admitted, residual = admit.admit_candidates(candidates, dmklinger_index=dmklinger_index)
    assert [item["lemma"] for item in admitted] == ["мама"]
    assert admitted[0]["gloss"] == "mother"
    assert residual == [{"lemma": "хмара", "pos": "noun", "count": 2, "reasons": ["no_uk_definition", "no_en_gloss"]}]


def _make_sqlite_db(path: Path, rows: list[tuple[str, str, str]] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
    if rows:
        conn.executemany("INSERT INTO dmklinger_uk_en VALUES (?, ?, ?)", rows)
    conn.commit()
    conn.close()


def test_is_valid_sources_db(tmp_path: Path) -> None:
    assert not admit.is_valid_sources_db(tmp_path / "nonexistent.db")

    empty = tmp_path / "empty.db"
    empty.touch()
    assert not admit.is_valid_sources_db(empty)

    text = tmp_path / "text.db"
    text.write_text("not a sqlite database file at all", encoding="utf-8")
    assert not admit.is_valid_sources_db(text)

    valid = tmp_path / "valid.db"
    _make_sqlite_db(valid)
    assert admit.is_valid_sources_db(valid)


def test_resolve_sources_db_prefers_worktree_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    worktree = tmp_path / "worktree"
    primary = tmp_path / "primary"
    worktree_db = worktree / "data" / "sources.db"
    primary_db = primary / "data" / "sources.db"

    _make_sqlite_db(worktree_db)
    _make_sqlite_db(primary_db)
    monkeypatch.setattr(admit, "_resolve_primary_checkout", lambda root=None: primary)

    resolved = admit.resolve_sources_db(project_root=worktree)
    assert resolved == worktree_db


def test_resolve_sources_db_missing_worktree_falls_back_to_primary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = tmp_path / "worktree"
    primary = tmp_path / "primary"
    worktree_db = worktree / "data" / "sources.db"
    primary_db = primary / "data" / "sources.db"

    _make_sqlite_db(primary_db)
    monkeypatch.setattr(admit, "_resolve_primary_checkout", lambda root=None: primary)

    resolved = admit.resolve_sources_db(project_root=worktree)
    assert resolved == primary_db
    # Never symlink or copy into worktree
    assert not worktree_db.exists()


def test_resolve_sources_db_empty_worktree_falls_back_to_primary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = tmp_path / "worktree"
    primary = tmp_path / "primary"
    worktree_db = worktree / "data" / "sources.db"
    primary_db = primary / "data" / "sources.db"

    worktree_db.parent.mkdir(parents=True, exist_ok=True)
    worktree_db.touch()  # 0-byte invalid file
    _make_sqlite_db(primary_db)
    monkeypatch.setattr(admit, "_resolve_primary_checkout", lambda root=None: primary)

    resolved = admit.resolve_sources_db(project_root=worktree)
    assert resolved == primary_db


def test_resolve_sources_db_fails_closed_when_neither_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    worktree = tmp_path / "worktree"
    primary = tmp_path / "primary"

    monkeypatch.setattr(admit, "_resolve_primary_checkout", lambda root=None: primary)

    with pytest.raises(FileNotFoundError, match=r"sources\.db not found: checked worktree.*primary checkout"):
        admit.resolve_sources_db(project_root=worktree)


def test_resolve_sources_db_fails_closed_no_primary_resolved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    worktree = tmp_path / "worktree"

    monkeypatch.setattr(admit, "_resolve_primary_checkout", lambda root=None: None)

    with pytest.raises(FileNotFoundError, match=r"sources\.db not found: checked worktree"):
        admit.resolve_sources_db(project_root=worktree)


def test_resolve_sources_db_refuses_network_path() -> None:
    with pytest.raises(admit.ActiveDatabaseNetworkError, match=r"Active sources\.db must remain on local storage"):
        admit.resolve_sources_db(explicit="/Volumes/UkrainianData/data/sources.db")

    with pytest.raises(admit.ActiveDatabaseNetworkError, match=r"Active sources\.db must remain on local storage"):
        admit.resolve_sources_db(explicit="//server/share/sources.db")


def test_resolve_sources_db_explicit_override(tmp_path: Path) -> None:
    custom = tmp_path / "custom.db"
    _make_sqlite_db(custom)

    assert admit.resolve_sources_db(explicit=custom) == custom

    with pytest.raises(FileNotFoundError, match=r"sources\.db specified at.*does not exist"):
        admit.resolve_sources_db(explicit=tmp_path / "missing.db")


def test_resolve_primary_checkout_matches_git_common_dir() -> None:
    from scripts.guardrails.worktree_containment import (
        NotAGitRepositoryError,
        resolve_main_root,
    )

    resolved = admit._resolve_primary_checkout()
    try:
        expected = resolve_main_root(admit.PROJECT_ROOT)
    except NotAGitRepositoryError:
        assert resolved is None
        return
    assert resolved == expected
    assert (resolved / ".git").is_dir()


def test_main_runs_with_primary_fallback_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    primary = tmp_path / "primary"
    primary_db = primary / "data" / "sources.db"
    _make_sqlite_db(
        primary_db,
        rows=[("мама", "noun", json.dumps(["mother"]))],
    )

    worktree = tmp_path / "worktree"
    worktree.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(admit, "_resolve_primary_checkout", lambda root=None: primary)

    def fake_cache(lemma: str) -> dict:
        return {
            "lookup_word": lemma,
            "lookups": {
                "newsum": {"text": "мама МА́МА, и, ж. Мати.", "word": lemma, "source_url": "https://slovnyk.me"}
            },
        }

    monkeypatch.setattr(admit, "ensure_slovnyk_cache", fake_cache)

    candidates_file = worktree / "candidates.json"
    candidates_file.write_text(
        json.dumps(
            {
                "attempted": [{"lemma": "мама", "pos": "noun", "count": 10, "locators": ["p. 5"]}],
                "total_content_candidates": 1,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    out_file = worktree / "glossary.yaml"

    rc = admit.main(
        [
            "--candidates",
            str(candidates_file),
            "--book-id",
            "test-bukvar",
            "--title",
            "Тестовий буквар",
            "--out",
            str(out_file),
            "--report",
        ]
    )
    assert rc == 0
    assert out_file.exists()
    payload = yaml.safe_load(out_file.read_text(encoding="utf-8"))
    assert payload["stats"]["admitted"] == 1
    headwords = payload["sources"][0]["headwords"]
    assert len(headwords) == 1
    assert headwords[0]["lemma"] == "мама"
    assert headwords[0]["gloss"] == "mother"
    assert headwords[0]["gloss_source"] == "dmklinger"
