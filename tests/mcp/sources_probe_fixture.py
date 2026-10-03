"""Minimal sources stores on which every read-only sources tool's lookup succeeds (#9551).

``sources_side_effects_probe.py --hermetic`` builds these in its scratch directory,
so each audited call runs its success path: a write a tool attempts after a hit is
seen, not skipped by an early "no such table" error.

The schema is the production DDL of the tables the tools read, dumped from the
real stores into ``fixtures/sources_probe/*.sql`` (schema only, no rows). Every row
is synthetic and written here. Regenerate the DDL after a schema change with::

    .venv/bin/python tests/mcp/sources_probe_fixture.py dump \
        --sources-db data/sources.db --vesum-db data/vesum.db
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

FIXTURE_DIR = Path(__file__).with_name("fixtures") / "sources_probe"
SOURCES_SCHEMA = FIXTURE_DIR / "sources.sql"
VESUM_SCHEMA = FIXTURE_DIR / "vesum.sql"

SOURCES_TABLES = (
    "textbook_sections",
    "textbooks",
    "textbooks_fts",
    "literary_texts",
    "literary_fts",
    "external_articles",
    "external_fts",
    "wikipedia",
    "wikipedia_fts",
    "ukrainian_wiki",
    "ukrainian_wiki_fts",
    "resource_catalogue",
    "resource_catalogue_fts",
    "puls_cefr",
    "ua_gec_errors",
    "ua_gec_errors_fts",
    "style_guide",
    "sum11",
    "grinchenko",
    "esum_etymology",
    "esum_etymology_meta",
    "frazeolohichnyi",
    "ukrajinet",
    "balla_en_uk",
    "dmklinger_uk_en",
    "wiktionary",
    "ulif_dictua_entries",
    "ulif_dictua_sections",
    "ulif_forms",
    "ulif_forms_build",
    "sum20_articles",
    "sum20_articles_fts",
    "sum20_senses",
    "sum20_citations",
    "slovnyk_me_entries",
    "slovnyk_me_entries_fts",
)
VESUM_TABLES = ("forms_all", "form_markers", "vesum_build_metadata", "forms")

_KIND_ORDER = {"table": 0, "view": 1, "index": 2, "trigger": 3}


def dump_schema(database: Path, tables: Iterable[str]) -> str:
    """The DDL of ``tables`` (with their indexes, views and triggers), tables first so triggers resolve."""
    conn = sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro", uri=True)
    try:
        statements: list[tuple[int, int, str]] = []
        for position, table in enumerate(tables):
            rows = conn.execute(
                "SELECT type, sql FROM sqlite_master WHERE tbl_name = ? AND sql IS NOT NULL ORDER BY name", (table,)
            ).fetchall()
            if not rows:
                raise SystemExit(f"{database}: no table or view named {table}")
            statements.extend((_KIND_ORDER[kind], position, sql) for kind, sql in rows)
    finally:
        conn.close()
    return "\n\n".join(f"{sql};" for _, _, sql in sorted(statements)) + "\n"


def _insert(conn: sqlite3.Connection, table: str, rows: Iterable[dict[str, Any]]) -> None:
    for row in rows:
        columns = ", ".join(f'"{column}"' for column in row)
        marks = ", ".join("?" for _ in row)
        conn.execute(f'INSERT INTO "{table}" ({columns}) VALUES ({marks})', tuple(row.values()))


def build(scratch: Path) -> tuple[Path, Path]:
    """Create ``sources.db`` and ``vesum.db`` in ``scratch``; return their paths."""
    sources_db = scratch / "sources.db"
    vesum_db = scratch / "vesum.db"
    for database, schema, rows in (
        (sources_db, SOURCES_SCHEMA, SOURCES_ROWS),
        (vesum_db, VESUM_SCHEMA, VESUM_ROWS),
    ):
        conn = sqlite3.connect(database)
        try:
            conn.executescript(schema.read_text(encoding="utf-8"))
            for table, table_rows in rows.items():
                _insert(conn, table, table_rows)
            conn.commit()
        finally:
            conn.close()
    return sources_db, vesum_db


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


# The probe's lookup words. Every row below exists so one of them is found.
WORD = "мова"
OLD_WORD = "хата"
EN_WORD = "language"
NOTE = "Синтетичний запис для перевірки інструмента."
TEXT = f"{WORD.capitalize()} — головний засіб спілкування. {NOTE}"
# Prose searches skip chunks under 300 characters (sources_db._fts_search), so the
# textbook and literary chunks repeat their line until they are long enough.
LONG_TEXT = "\n".join([TEXT] * 6)
VERSE = "Рідна мова співає в серці."
LITERARY_TEXT = "\n".join([VERSE, *[NOTE] * 7])
STAMP = "2026-10-03T00:00:00+00:00"
SHA = "0" * 64
ULIF_FORMS_PARSER = "ulif-forms-v4"
ULIF_FORMS_FINGERPRINT = "1" * 64

SOURCES_ROWS: dict[str, list[dict[str, Any]]] = {
    "textbook_sections": [
        {
            "section_id": 1,
            "source_file": "probe-textbook",
            "grade": 5,
            "section_title": "Мова",
            "chunk_count": 1,
            "full_text": LONG_TEXT,
        }
    ],
    "textbooks": [
        {
            "id": 1,
            "chunk_id": "probe-textbook_c0001",
            "title": "Мова",
            "text": LONG_TEXT,
            "source_file": "probe-textbook",
            "grade": "5",
            "author": "Probe",
            "author_uk": "Зонд",
            "char_count": len(LONG_TEXT),
            "parent_section_id": 1,
            "subject": "ukrmova",
        }
    ],
    "literary_texts": [
        {
            "id": 1,
            "chunk_id": "probe-literary_c0001",
            "title": "Слово про мову",
            "text": LITERARY_TEXT,
            "source_file": "probe-literary",
            "author": "Зондовий О.",
            "work": "Слово про мову",
            "work_id": "probe_slovo_pro_movu",
            "year": 1900,
            "genre": "poetry",
            "language_period": "modern",
            "char_count": len(LITERARY_TEXT),
        }
    ],
    "external_articles": [
        {
            "id": 1,
            "chunk_id": "ext-probe-1",
            "url": "https://example.org/mova",
            "url_normalized": "https://example.org/mova",
            "title": "Мова і спілкування",
            "text": TEXT,
            "source_file": "probe-external",
            "domain": "example.org",
            "char_count": len(TEXT),
            "channel_id": "probe",
            "quality_tier": 1,
        }
    ],
    "wikipedia": [
        {"id": 1, "title": "Мова", "url": "https://uk.wikipedia.org/wiki/Мова", "text": TEXT, "fetched_at": STAMP}
    ],
    "ukrainian_wiki": [
        {
            "id": 1,
            "passage_id": "probe-mova:p1-1",
            "article_slug": "probe-mova",
            "article_title": "Мова",
            "article_path": "wiki/probe/mova.md",
            "track": "b1",
            "heading_path": "Мова",
            "section_path": "Мова",
            "chunk_index": 1,
            "paragraph_start": 1,
            "paragraph_end": 1,
            "word_count": 9,
            "char_count": len(TEXT),
            "text": TEXT,
            "source_registry_path": "wiki/probe/mova.sources.yaml",
            "gate_report_json": "{}",
            "inserted_at": STAMP,
        }
    ],
    "resource_catalogue": [
        {
            "id": 1,
            "url": "https://example.org/podcast/mova",
            "kind": "podcast",
            "title": "Мова щодня",
            "channel": "example.org",
            "access": "free",
            "levels": _json(["A1"]),
            "modules": _json([]),
            "topics": _json(["мова"]),
            "source_files": _json(["tests/mcp/sources_probe_fixture.py"]),
            "source_entries": _json([]),
            "discovery_evidence": _json([]),
            "search_text": f"Мова щодня {NOTE}",
            "http_status": 200,
            "checked_at": STAMP,
            "link_check": "ok",
            "letters": _json([]),
            "letter_evidence": _json([]),
            "access_evidence": _json([]),
        }
    ],
    "puls_cefr": [
        {
            "id": 1,
            "word": WORD,
            "level": "A1",
            "pos": "іменник",
            "type": "значення",
            "text": "мова (A1, іменник)",
            "source": "PULS (puls.peremova.org)",
        }
    ],
    "ua_gec_errors": [
        {
            "id": 1,
            "error": "приймати участь",
            "correct": "брати участь",
            "error_type": "F/Calque",
            "doc_id": "0001",
            "annotator_id": "1",
            "partition": "gec-only/train",
            "is_native": 1,
            "source_lang": "",
        }
    ],
    "style_guide": [
        {
            "id": 1,
            "word": "Приймати участь – брати участь",
            "section": "ДІЄСЛОВА",
            "text": NOTE,
            "source": "Антоненко-Давидович",
            "word_lower": "приймати участь – брати участь",
            "page": 1,
            "russianism_pattern": "",
        }
    ],
    "sum11": [
        {"id": 1, "word": WORD, "definition": f"МО́ВА, и, ж. {NOTE}", "text": f"мова: {NOTE}", "source": "СУМ-11"}
    ],
    "grinchenko": [{"id": 1, "word": OLD_WORD, "definition": f"Хата, -ти, ж. {NOTE}", "source": "Грінченко"}],
    "esum_etymology": [{"lemma": WORD, "etymology_text": f"мова — {NOTE}", "cognates": "[]", "vol": 3, "page": 1}],
    "esum_etymology_meta": [
        {
            "id": 1,
            "lemma": WORD,
            "vol": 3,
            "page": 1,
            "entry_hash": "probe",
            "etymology_text": f"мова — {NOTE}",
            "cognates": "[]",
            "source": "ЕСУМ vol. 3",
        }
    ],
    "frazeolohichnyi": [
        {
            "id": 1,
            "word": "рука",
            "definition": f"Рука руку миє. {NOTE}",
            "text": f"рука: {NOTE}",
            "source": "Фразеологічний словник",
        }
    ],
    "ukrajinet": [
        {
            "id": 1,
            "synset_id": "probe-1-n",
            "words": _json([WORD, "говір"]),
            "text": "Синоніми: мова, говір",
            "source": "Ukrajinet WordNet",
        }
    ],
    "balla_en_uk": [
        {"id": 1, "word": EN_WORD, "definition": "n мова", "text": "language: n мова", "source": "Балла EN→UK"}
    ],
    "dmklinger_uk_en": [{"id": 1, "word": WORD, "pos": "noun", "translations": "language", "text": "мова: language"}],
    "wiktionary": [{"id": 1, "word": WORD, "definitions": NOTE, "text": f"мова: {NOTE}"}],
    "ulif_dictua_entries": [
        {
            "id": 1,
            "normalized_query": WORD,
            "homonym_index": 1,
            "canonical_headword": "мо́ва",
            "grammatical_label": "іменник жіночого роду",
            "content_sha256": SHA,
            "register_position": "1:1",
            "homonym_checked": 1,
            "raw_response_ref": f"sha256:{SHA}",
            "retrieved_at": STAMP,
            "response_sha256": SHA,
            "parser_version": "ulif-dictua-v2",
            "status": "ok",
        }
    ],
    "ulif_dictua_sections": [
        {
            "id": 1,
            "entry_id": 1,
            "kind": "synonyms",
            "source_order": 0,
            "sense_or_group_id": "synonyms:1",
            "payload_json": _json({"words": ["говір"], "citations": []}),
        },
        {
            "id": 2,
            "entry_id": 1,
            "kind": "phraseology",
            "source_order": 0,
            "sense_or_group_id": "phraseology:1",
            "payload_json": _json({"phrase": "рідна мова", "citations": []}),
        },
    ],
    "ulif_forms": [
        {
            "id": 1,
            "entry_id": 1,
            "entry_key": "мова#1",
            "form_unstressed": WORD,
            "form_stressed": "мо́ва",
            "stress_vowel_indices": "[1]",
            "grammatical_tags": _json(["noun", "f"]),
            "is_lemma": 1,
            "pedagogical_stressed_form": "мо́ва",
            "source_page_sha256": SHA,
            "parser_version": ULIF_FORMS_PARSER,
            "source_entry_fingerprint": SHA,
        }
    ],
    "ulif_forms_build": [
        {
            "id": 1,
            "state": "complete",
            "parser_version": ULIF_FORMS_PARSER,
            "total_entries": 1,
            "entries_done": 1,
            "total_forms": 1,
            "started_at": STAMP,
            "finished_at": STAMP,
            "source_fingerprint": ULIF_FORMS_FINGERPRINT,
        }
    ],
    "sum20_articles": [
        {
            "id": 1,
            "wordid": 1,
            "normalized_lookup_key": WORD,
            "headword": "МОВА",
            "stressed_headword": "МО́ВА",
            "pos": "ж.",
            "grammar": "и, ж.",
            "article_html": f'<article><div class="WORD">МО́ВА</div>{NOTE}</article>',
            "article_text": f"МО́ВА , и, ж. 1 . {NOTE}",
            "definition_text": NOTE,
            "official_url": "https://sum20ua.com/?wordid=1",
            "fetched_at": STAMP,
            "content_sha256": SHA,
            "parser_version": "sum20_official_v1",
        }
    ],
    "sum20_senses": [{"id": 1, "article_id": 1, "sense_order": 1, "definition": NOTE}],
    "sum20_citations": [
        {
            "id": 1,
            "article_id": 1,
            "sense_ref": 1,
            "order": 1,
            "citation_text": "Рідна мова співає в серці.",
            "parsed_bib_fields": _json({"author": "О. Зондовий"}),
        }
    ],
    "slovnyk_me_entries": [
        {
            "id": 1,
            "query": OLD_WORD,
            "word": OLD_WORD,
            "normalized_word": OLD_WORD,
            "dictionary_slug": "franko",
            "dictionary_label": "Галицько-руські народні приповідки",
            "source_type": "heritage_or_regional",
            "source_url": "https://slovnyk.me/dict/franko/хата",
            "title": "хата",
            "snippet": NOTE,
            "text": f"хата {NOTE}",
            "is_dialect": 1,
            "fetched_at": STAMP,
        },
        {
            "id": 2,
            "query": WORD,
            "word": WORD,
            "normalized_word": WORD,
            "dictionary_slug": "vts",
            "dictionary_label": "Великий тлумачний словник сучасної української мови",
            "source_type": "modern",
            "source_url": "https://slovnyk.me/dict/vts/мова",
            "title": "мова",
            "snippet": NOTE,
            "text": f"мова мо́ва -и, ж. {NOTE}",
            "is_modern": 1,
            "fetched_at": STAMP,
        },
    ],
}

_FORMS = (
    (1, "мова", "noun:inanim:f:v_naz"),
    (2, "мови", "noun:inanim:f:v_rod"),
    (3, "хата", "noun:inanim:f:v_naz"),
)
VESUM_ROWS: dict[str, list[dict[str, Any]]] = {
    "forms_all": [
        {
            "id": form_id,
            "entry_id": 1 if form.startswith("мов") else 2,
            "word_form": form,
            "lemma": "мова" if form.startswith("мов") else "хата",
            "pos": "noun",
            "tags": tags,
            "source_location": "probe",
            "word_form_folded": form,
            "lemma_folded": "мова" if form.startswith("мов") else "хата",
        }
        for form_id, form, tags in _FORMS
    ],
    "vesum_build_metadata": [
        {"key": "canonical_jsonl_sha256", "value": SHA},
        {"key": "compatibility_hidden_markers", "value": _json(["bad", "obsc", "subst"])},
        {"key": "marker_policy_version", "value": "v1"},
        {"key": "schema_version", "value": "vesum-reingest-v2"},
    ],
}

# Synthetic pages for the hosts the read-only tools fetch, keyed by host. Hosts not
# listed get an empty page, which is how the persisting tools reach their cache write.
_SLOVNYK_PAGE = (
    '<html><head><title>{word} — словник</title><meta name="description" content="{note}"></head>'
    '<body><section id="dictionary-acticle"><article><h1>{word}</h1><p>{word} {note}</p></article>'
    "</section></body></html>"
)
FAKE_PAGES: dict[str, tuple[str, str]] = {
    "r2u.org.ua": (
        "text/html; charset=utf-8",
        '<table><tr><td class="result_row"><b>язык</b> мова, язик</td></tr></table>',
    ),
    "e2u.org.ua": (
        "text/html; charset=utf-8",
        f'<table><tr><td class="result_row"><b>{EN_WORD}</b> мова</td></tr></table>',
    ),
    "sketch.uacorpus.org": (
        "application/json",
        _json({"Items": [{"str": WORD, "frq": 1000, "relfreq": 12.5}]}),
    ),
    "2019.pravopys.net": (
        "text/html; charset=utf-8",
        f"<html><body><p>§ 7. Апостроф</p><p>{NOTE}</p></body></html>",
    ),
}


def fake_page(url: str) -> tuple[str, str]:
    """Content type and body the hermetic network returns for ``url``."""
    from urllib.parse import unquote, urlsplit

    parts = urlsplit(url)
    if parts.hostname == "slovnyk.me":
        word = unquote(parts.path.rstrip("/").rsplit("/", 1)[-1])
        return "text/html; charset=utf-8", _SLOVNYK_PAGE.format(word=word, note=NOTE)
    return FAKE_PAGES.get(parts.hostname or "", ("text/html; charset=utf-8", "<html><body></body></html>"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    dump = sub.add_parser("dump", help="Rewrite the fixture DDL from real stores (schema only).")
    dump.add_argument("--sources-db", type=Path, required=True)
    dump.add_argument("--vesum-db", type=Path, required=True)
    args = parser.parse_args(argv)
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_SCHEMA.write_text(dump_schema(args.sources_db, SOURCES_TABLES), encoding="utf-8")
    VESUM_SCHEMA.write_text(dump_schema(args.vesum_db, VESUM_TABLES), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
