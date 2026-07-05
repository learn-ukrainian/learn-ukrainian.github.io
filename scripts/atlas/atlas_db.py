"""Word Atlas entry-model v1 SQLite store (`data/atlas.db`).

Build-time source of truth modeled on ``docs/runbooks/word-atlas-entry-model.md``.
The JSON manifest becomes a generated export of this DB, not the store.

Migration is deterministic and idempotent: it rebuilds the DB from the current
manifest. entry_type / alias / provenance are assigned by rule (no LLM).
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_DB = ROOT / "data" / "atlas.db"

ARTICLE_ENTRY_TYPES = {
    "lemma",
    "expression",
    "phraseologism",
    "proverb",
    "multiword_term",
    "proper_name",
}
ALIAS_KINDS = {
    "canonical",
    "unstressed",
    "transliteration",
    "inflected_form",
    "spelling_variant",
    "translation_hint",
    "component_head",
}
ENRICHMENT_SECTIONS = {
    "meaning",
    "definition_cards",
    "etymology",
    "morphology",
    "stress",
    "pronunciation",
    "translation",
    "synonyms",
    "antonyms",
    "idioms",
    "literary_attestation",
    "wiki_reference",
    "cefr",
    "heritage_status",
    "calque_note",
}

REVIEW_STATES = {"approved", "needs_review", "rejected"}
VISIBILITIES = {"public", "private"}
ENRICHMENT_PHASES = {"migration", "local", "slovnyk", "uncovered"}


def _sql_enum(values: set[str]) -> str:
    """Render a Python enum set as a deterministic SQL IN-list."""
    return ", ".join(f"'{v}'" for v in sorted(values))


# CHECK constraints are generated from the Python enum sets above so the
# entry-model gates are load-bearing at the STORAGE layer: a Phase-1/2 filler
# bug cannot silently insert an invalid entry_type/kind/section — the DB
# rejects it. The DB is rebuilt by migrate_manifest, so schema evolution is a
# code change, never an in-place migration.
SCHEMA = f"""
PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS articles (
    slug TEXT PRIMARY KEY,
    display_head TEXT NOT NULL,
    lemma TEXT NOT NULL,
    entry_type TEXT NOT NULL CHECK (entry_type IN ({_sql_enum(ARTICLE_ENTRY_TYPES)})),
    pos TEXT,
    gloss TEXT,
    review_state TEXT NOT NULL CHECK (review_state IN ({_sql_enum(REVIEW_STATES)})),
    visibility TEXT NOT NULL CHECK (visibility IN ({_sql_enum(VISIBILITIES)})),
    cefr TEXT,
    heritage_classification TEXT,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS article_provenance (
    slug TEXT NOT NULL,
    source_family TEXT,
    source_locator TEXT,
    extraction_mode TEXT,
    FOREIGN KEY (slug) REFERENCES articles(slug)
);
CREATE TABLE IF NOT EXISTS aliases (
    alias TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ({_sql_enum(ALIAS_KINDS)})),
    source TEXT,
    target_slug TEXT NOT NULL,
    UNIQUE (alias, kind, target_slug)
);
CREATE TABLE IF NOT EXISTS related_entries (
    slug TEXT NOT NULL,
    related_slug TEXT NOT NULL,
    entry_type TEXT,
    relation TEXT,
    component_role TEXT,
    FOREIGN KEY (slug) REFERENCES articles(slug)
);
CREATE TABLE IF NOT EXISTS enrichment (
    slug TEXT NOT NULL,
    section TEXT NOT NULL CHECK (section IN ({_sql_enum(ENRICHMENT_SECTIONS)})),
    payload_json TEXT NOT NULL,
    source TEXT,
    filled_at TEXT,
    phase TEXT CHECK (phase IS NULL OR phase IN ({_sql_enum(ENRICHMENT_PHASES)})),
    UNIQUE (slug, section),
    FOREIGN KEY (slug) REFERENCES articles(slug)
);
CREATE INDEX IF NOT EXISTS idx_aliases_target ON aliases(target_slug);
CREATE INDEX IF NOT EXISTS idx_prov_slug ON article_provenance(slug);
CREATE INDEX IF NOT EXISTS idx_enrichment_slug ON enrichment(slug);
CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    slug UNINDEXED, display_head, lemma, gloss, aliases
);
"""

_STRESS_RE = re.compile("[́̀]")
_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": "ie",
    "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "i", "й": "i", "к": "k", "л": "l",
    "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ь": "",
    "ю": "iu", "я": "ia", "'": "", "ʼ": "", " ": "-",
}


def strip_stress(text: str) -> str:
    return _STRESS_RE.sub("", unicodedata.normalize("NFD", text))


def unstressed(text: str) -> str:
    return unicodedata.normalize("NFC", strip_stress(text))


def transliterate(text: str) -> str:
    return "".join(_TRANSLIT.get(ch, ch) for ch in text.lower())


def classify_entry_type(entry: dict[str, Any]) -> str:
    """Deterministic entry_type for migration (no LLM).

    form_of records are handled as aliases, not articles (caller checks first).
    Multiword defaults to multiword_term (entry-model tie-breaker); idiom/proverb
    promotion happens later when phraseological evidence is attached.
    """
    lemma = str(entry.get("lemma") or "").strip()
    if " " in lemma:
        return "multiword_term"
    return "lemma"


def _iso(entry: dict[str, Any]) -> str | None:
    return entry.get("updated_at") or entry.get("created_at")


def migrate_manifest(manifest_path: Path, db_path: Path) -> dict[str, int]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    cur = conn.cursor()

    counts = {"articles": 0, "aliases": 0, "provenance": 0, "enrichment": 0, "form_aliases": 0}
    by_type: dict[str, int] = {}

    # first pass: gather article slugs so form_of aliases only resolve to real articles
    article_slugs: set[str] = set()
    for e in entries:
        if e.get("form_of"):
            continue
        article_slugs.add(str(e.get("url_slug") or e.get("lemma")).strip())

    def _form_of_target(form_of: Any) -> str | None:
        if isinstance(form_of, dict):
            return str(form_of.get("url_slug") or form_of.get("lemma") or "").strip() or None
        return str(form_of).strip() or None

    for e in entries:
        lemma = str(e.get("lemma") or "").strip()
        slug = str(e.get("url_slug") or lemma).strip()
        if not lemma or not slug:
            continue
        display_head = str(e.get("display_head") or lemma).strip()

        # form_of records -> alias rows, not articles (only if target is a real article)
        form_of = e.get("form_of")
        if form_of:
            target = _form_of_target(form_of)
            if target and target in article_slugs:
                cur.execute(
                    "INSERT OR IGNORE INTO aliases(alias, kind, source, target_slug) VALUES (?,?,?,?)",
                    (unstressed(lemma), "inflected_form", "manifest:form_of", target),
                )
                counts["form_aliases"] += 1
            else:
                counts["form_aliases_dropped"] = counts.get("form_aliases_dropped", 0) + 1
            continue

        etype = classify_entry_type(e)
        by_type[etype] = by_type.get(etype, 0) + 1
        heritage = e.get("heritage_status") or {}
        heritage_cls = heritage.get("classification") if isinstance(heritage, dict) else None
        enrichment = e.get("enrichment") or {}
        cefr_val = None
        if isinstance(enrichment.get("cefr"), dict):
            cefr_val = enrichment["cefr"].get("level")

        # Grammar metaterms (pluralia tantum, знахідний відмінок, …) are reference
        # data, not learner-facing dictionary articles — #3776's lexeme_filter
        # excludes them at every manifest consumer. Encode that decision at the
        # SSOT layer so DB-driven site generation cannot resurrect them as
        # public articles.
        visibility = "private" if e.get("pos") == "grammar term" else "public"
        cur.execute(
            """INSERT OR REPLACE INTO articles
               (slug, display_head, lemma, entry_type, pos, gloss, review_state,
                visibility, cefr, heritage_classification, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (slug, display_head, lemma, etype, e.get("pos"), e.get("gloss"),
             "approved", visibility, cefr_val, heritage_cls,
             e.get("created_at"), e.get("updated_at")),
        )
        counts["articles"] += 1

        # provenance
        prov = e.get("source_provenance")
        prov_rows = prov if isinstance(prov, list) else ([prov] if isinstance(prov, dict) else [])
        if not prov_rows and e.get("primary_source"):
            prov_rows = [{"source_family": e.get("primary_source")}]
        for p in prov_rows:
            if not isinstance(p, dict):
                continue
            cur.execute(
                "INSERT INTO article_provenance(slug, source_family, source_locator, extraction_mode) VALUES (?,?,?,?)",
                (slug, p.get("source_family"), p.get("source_locator") or p.get("locator"),
                 p.get("extraction_mode")),
            )
            counts["provenance"] += 1

        # canonical + unstressed + transliteration aliases
        alias_rows = [
            (unstressed(lemma), "canonical", "migration", slug),
            (transliterate(unstressed(lemma)), "transliteration", "migration", slug),
        ]
        for a, k, s, t in alias_rows:
            if a and a != slug:
                cur.execute("INSERT OR IGNORE INTO aliases(alias, kind, source, target_slug) VALUES (?,?,?,?)", (a, k, s, t))
                counts["aliases"] += 1

        # enrichment sections (from enrichment + sections + top-level pronunciation/wiki/heritage)
        buckets: dict[str, Any] = {}
        if isinstance(enrichment, dict):
            for sec, payload in enrichment.items():
                if sec in ENRICHMENT_SECTIONS and payload:
                    buckets[sec] = payload
        for sec, payload in (e.get("sections") or {}).items():
            if sec in ENRICHMENT_SECTIONS and payload:
                buckets[sec] = payload
        if e.get("pronunciation"):
            buckets["pronunciation"] = e["pronunciation"]
        if e.get("wiki_reference"):
            buckets["wiki_reference"] = e["wiki_reference"]
        if isinstance(heritage, dict) and heritage:
            buckets["heritage_status"] = heritage
        for sec, payload in buckets.items():
            src = payload.get("source") if isinstance(payload, dict) else None
            cur.execute(
                "INSERT OR REPLACE INTO enrichment(slug, section, payload_json, source, filled_at, phase) VALUES (?,?,?,?,?,?)",
                (slug, sec, json.dumps(payload, ensure_ascii=False), src, _iso(e), "migration"),
            )
            counts["enrichment"] += 1

    # FTS
    cur.execute("DELETE FROM articles_fts")
    cur.execute(
        """INSERT INTO articles_fts(slug, display_head, lemma, gloss, aliases)
           SELECT a.slug, a.display_head, a.lemma, COALESCE(a.gloss,''),
                  COALESCE((SELECT group_concat(al.alias, ' ') FROM aliases al WHERE al.target_slug = a.slug), '')
           FROM articles a"""
    )
    conn.commit()
    counts["by_type"] = by_type  # type: ignore[assignment]
    conn.close()
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description="Build/migrate the Word Atlas entry-model v1 SQLite DB.")
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args()
    counts = migrate_manifest(args.manifest, args.db)
    by_type = counts.pop("by_type", {})
    print("atlas_db migrate:", json.dumps(counts, ensure_ascii=False))
    print("by entry_type:", json.dumps(by_type, ensure_ascii=False))


if __name__ == "__main__":
    main()
