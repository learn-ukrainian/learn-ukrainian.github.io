"""Tests for the Word Atlas entry-model v1 SQLite store (scripts/lexicon/atlas_db.py)."""

from __future__ import annotations

import json
import sqlite3

from scripts.atlas import atlas_db


def _manifest(tmp_path):
    entries = [
        {"lemma": "прапор", "url_slug": "прапор", "gloss": "flag", "pos": "noun",
         "primary_source": "curriculum", "heritage_status": {"classification": "standard"},
         "enrichment": {"cefr": {"level": "A1"}, "meaning": {"definitions": ["стяг"], "source": "СУМ"}},
         "pronunciation": {"ipa": "[ˈprapor]"}},
        {"lemma": "Іван", "url_slug": "іван", "gloss": "Ivan", "pos": "noun", "primary_source": "curriculum"},
        # form_of -> alias record, must resolve to іван, not become an article
        {"lemma": "Іване", "url_slug": "іване", "form_of": {"lemma": "Іван", "url_slug": "іван"}},
        # form_of with a non-article target -> alias dropped, no orphan
        {"lemma": "Гхост", "url_slug": "гхост", "form_of": {"lemma": "Nope", "url_slug": "nope"}},
        # multiword -> multiword_term
        {"lemma": "сліпа зона", "url_slug": "сліпа-зона", "gloss": "blind spot", "pos": "noun",
         "primary_source": "teacher_lesson"},
    ]
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps({"entries": entries}, ensure_ascii=False), encoding="utf-8")
    return p


def test_migration_shapes_and_gates(tmp_path):
    db = tmp_path / "atlas.db"
    counts = atlas_db.migrate_manifest(_manifest(tmp_path), db)
    conn = sqlite3.connect(db)
    q = lambda s: conn.execute(s).fetchall()  # noqa: E731

    # 3 articles (прапор, Іван, сліпа зона); Іване + Гхост are form_of aliases
    assert q("SELECT COUNT(*) FROM articles")[0][0] == 3
    assert dict(q("SELECT entry_type, COUNT(*) FROM articles GROUP BY entry_type")) == {
        "lemma": 2,
        "multiword_term": 1,
    }
    # form_of that resolves becomes an alias; the unresolved one is dropped (not an orphan)
    assert counts["form_aliases"] == 1
    assert counts.get("form_aliases_dropped") == 1

    # entry-model gates
    assert q(
        "SELECT COUNT(*) FROM articles WHERE entry_type NOT IN "
        "('lemma','expression','phraseologism','proverb','multiword_term','proper_name')"
    )[0][0] == 0
    assert q("SELECT COUNT(*) FROM aliases WHERE target_slug NOT IN (SELECT slug FROM articles)")[0][0] == 0
    # every article is a public approved article
    assert q("SELECT COUNT(*) FROM articles WHERE review_state!='approved' OR visibility!='public'")[0][0] == 0

    # enrichment carried across; FTS populated and searchable
    assert q("SELECT COUNT(*) FROM enrichment WHERE slug='прапор'")[0][0] >= 3
    assert q("SELECT COUNT(*) FROM articles_fts")[0][0] == 3
    assert q("SELECT slug FROM articles_fts WHERE articles_fts MATCH 'прапор'")[0][0] == "прапор"
    conn.close()


def test_alias_helpers():
    assert atlas_db.unstressed("ро́звідка") == "розвідка"
    assert atlas_db.transliterate("розвідка") == "rozvidka"
    assert atlas_db.classify_entry_type({"lemma": "сліпа зона"}) == "multiword_term"
    assert atlas_db.classify_entry_type({"lemma": "розвідка"}) == "lemma"
