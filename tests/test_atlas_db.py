"""Tests for the Word Atlas entry-model v1 SQLite store (scripts/atlas/atlas_db.py)."""

from __future__ import annotations

import json
import sqlite3

import pytest
import yaml

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

    # Compatibility projection keeps the exact current Astro route surface:
    # form_of rows still render until PR-3 redirects them, but grammar terms do not.
    payload_slugs = [row[0] for row in q("SELECT slug FROM article_payloads ORDER BY route_order")]
    assert payload_slugs == ["прапор", "іван", "іване", "гхост", "сліпа-зона"]
    payload = json.loads(q("SELECT payload_json FROM article_payloads WHERE slug='іване'")[0][0])
    assert payload["form_of"] == {"lemma": "Іван", "url_slug": "іван"}

    metadata = dict(q("SELECT key, value_json FROM manifest_metadata"))
    assert metadata == {}

    validation = atlas_db.validate_alias_targets(db)
    assert validation["failures"] == 0
    assert validation["public_aliases"] >= 1
    assert validation["private_aliases"] == 0
    conn.close()


def test_alias_helpers():
    assert atlas_db.unstressed("ро́звідка") == "розвідка"
    assert atlas_db.transliterate("розвідка") == "rozvidka"
    assert atlas_db.classify_entry_type({"lemma": "сліпа зона"}) == "multiword_term"
    assert atlas_db.classify_entry_type({"lemma": "розвідка"}) == "lemma"


def test_verified_synonym_relations_are_symmetric_and_resolved_through_aliases(tmp_path):
    entries = [
        {"lemma": "краєвид", "url_slug": "landscape", "pos": "noun"},
        {"lemma": "пейзаж", "url_slug": "scenery", "pos": "noun"},
        {"lemma": "родина", "url_slug": "family", "pos": "noun"},
        {"lemma": "сім'я", "url_slug": "family-uk", "pos": "noun"},
        {"lemma": "кафе", "url_slug": "cafe", "pos": "noun"},
        {"lemma": "кав'ярня", "url_slug": "coffeehouse", "pos": "noun"},
    ]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"entries": entries}, ensure_ascii=False), encoding="utf-8")
    verdicts = tmp_path / "synonym_pair_verdicts.yaml"
    verdicts.write_text(
        """approved:
- a: краєвид
  b: пейзаж
  polarity: synonym
  sources: [synonyms]
- a: родина
  b: сім'я
  polarity: synonym
  sources: [synonyms_karavansky]
- a: кафе
  b: кав'ярня
  polarity: synonym
  sources: [sum20, vts, synonyms]
- a: self
  b: self
  polarity: synonym
  sources: [synonyms]
- a: відсутній
  b: пейзаж
  polarity: synonym
  sources: [synonyms]
- a: холодний
  b: гарячий
  polarity: antonym
  sources: [synonyms]
rejected:
- a: кафе
  b: ресторан
  polarity: synonym
  reason: Different establishments.
""",
        encoding="utf-8",
    )
    db = tmp_path / "atlas.db"

    counts = atlas_db.migrate_manifest(manifest, db, verdicts)

    conn = sqlite3.connect(db)
    rows = set(
        conn.execute(
            "SELECT slug, related_slug, relation, provenance FROM related_entries ORDER BY slug, related_slug"
        ).fetchall()
    )
    assert rows == {
        ("cafe", "coffeehouse", "synonym", "verified"),
        ("coffeehouse", "cafe", "synonym", "verified"),
        ("family", "family-uk", "synonym", "verified"),
        ("family-uk", "family", "synonym", "verified"),
        ("landscape", "scenery", "synonym", "verified"),
        ("scenery", "landscape", "synonym", "verified"),
    }
    assert all(slug != related_slug for slug, related_slug, _, _ in rows)
    assert all(provenance == "verified" for _, _, _, provenance in rows)
    assert counts["verified_synonym_pairs"] == 4
    assert counts["verified_synonym_pairs_unresolved"] == 1
    assert counts["verified_synonym_self_pairs_skipped"] == 1
    assert counts["related_entries"] == 6
    conn.close()


def test_cafe_verdict_is_an_approved_synonym_with_attested_sources():
    verdicts = yaml.safe_load(atlas_db.DEFAULT_SYNONYM_VERDICTS.read_text(encoding="utf-8"))
    cafe = next(
        item
        for item in verdicts["approved"]
        if item.get("a") == "кафе" and item.get("b") == "кав'ярня"
    )
    assert cafe == {
        "a": "кафе",
        "b": "кав'ярня",
        "polarity": "synonym",
        "sources": ["sum20", "vts", "synonyms"],
    }


def test_alias_validator_reports_actionable_failures(tmp_path, capsys):
    db = tmp_path / "atlas.db"
    atlas_db.migrate_manifest(_manifest(tmp_path), db)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO aliases(alias, kind, source, target_slug) VALUES (?,?,?,?)",
        ("orphan-alias", "spelling_variant", "test", "missing-slug"),
    )
    conn.commit()
    conn.close()

    with pytest.raises(ValueError, match="alias target"):
        atlas_db.validate_alias_targets(db)

    captured = capsys.readouterr()
    assert "alias_target_integrity failure:" in captured.err
    assert "alias='orphan-alias'" in captured.err
    assert "target_slug='missing-slug'" in captured.err


def test_hardening_gates(tmp_path):
    """PR #4380 review findings: metaterm visibility, CHECKs, timestamps, display_head."""
    entries = [
        # grammar metaterm -> article kept but PRIVATE (the #3776 lexeme_filter
        # decision, encoded at the SSOT layer)
        {"lemma": "pluralia tantum", "url_slug": "pluralia-tantum", "gloss": "plural-only",
         "pos": "grammar term", "primary_source": "curriculum"},
        # distinct created_at / updated_at survive separately (agy finding);
        # display_head honored when present
        {"lemma": "ка́ва", "url_slug": "кава", "gloss": "coffee", "pos": "noun",
         "display_head": "ка́ва", "created_at": "2026-01-01", "updated_at": "2026-06-30",
         "primary_source": "curriculum"},
    ]
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps({"entries": entries}, ensure_ascii=False), encoding="utf-8")
    db = tmp_path / "atlas.db"
    atlas_db.migrate_manifest(p, db)
    conn = sqlite3.connect(db)

    # metaterm is private, real word is public
    rows = dict(conn.execute("SELECT slug, visibility FROM articles").fetchall())
    assert rows == {"pluralia-tantum": "private", "кава": "public"}
    assert conn.execute("SELECT COUNT(*) FROM article_payloads").fetchone()[0] == 1

    # timestamps not conflated; display_head kept verbatim (incl. stress mark)
    head, created, updated = conn.execute(
        "SELECT display_head, created_at, updated_at FROM articles WHERE slug='кава'"
    ).fetchone()
    assert head == "ка́ва"
    assert (created, updated) == ("2026-01-01", "2026-06-30")

    # CHECK constraints are load-bearing: invalid enum values are REJECTED by
    # the storage layer (a filler bug cannot silently write them)
    for stmt, params in [
        ("INSERT INTO articles(slug, display_head, lemma, entry_type, review_state, visibility) VALUES (?,?,?,?,?,?)",
         ("x", "x", "x", "grammar term", "approved", "public")),  # not an entry-model type
        ("INSERT INTO articles(slug, display_head, lemma, entry_type, review_state, visibility) VALUES (?,?,?,?,?,?)",
         ("y", "y", "y", "lemma", "looks_fine", "public")),  # invalid review_state
        ("INSERT INTO aliases(alias, kind, source, target_slug) VALUES (?,?,?,?)",
         ("z", "typo_kind", "test", "кава")),  # invalid alias kind
        ("INSERT INTO enrichment(slug, section, payload_json, phase) VALUES (?,?,?,?)",
         ("кава", "unknown_section", "{}", "local")),  # invalid section
        ("INSERT INTO enrichment(slug, section, payload_json, phase) VALUES (?,?,?,?)",
         ("кава", "meaning", "{}", "guessed")),  # invalid phase
    ]:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(stmt, params)

    # NULL phase and NULL pos remain valid (the CHECKs constrain values, not presence)
    conn.execute("INSERT INTO enrichment(slug, section, payload_json) VALUES ('кава', 'etymology', '{}')")
    conn.execute(
        "INSERT INTO articles(slug, display_head, lemma, entry_type, review_state, visibility)"
        " VALUES ('тест', 'тест', 'тест', 'lemma', 'approved', 'public')"
    )
    conn.close()
