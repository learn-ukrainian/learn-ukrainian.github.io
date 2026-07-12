"""Word Atlas entry-model v1 SQLite store (`data/atlas.db`).

Build-time source of truth modeled on ``docs/runbooks/word-atlas-entry-model.md``.
The JSON manifest becomes a generated export of this DB, not the store.

Migration is deterministic and idempotent: it rebuilds the DB from the current
manifest. entry_type / alias / provenance are assigned by rule (no LLM).

Compatibility projection contract for PR-1 SSG DB reads:
``article_payloads.payload_json`` stores the exact public manifest entry object
that ``site/src/lexicon/WordAtlasArticle.astro`` consumes today, keyed by the
route slug and preserving manifest route order. This table is deliberately an
opaque build-time projection, not the normalized entry-model schema: it includes
current ``form_of`` routes until the alias/redirect split lands in PR-3, while
the normalized ``articles`` table continues to treat ``form_of`` rows as alias
records. Any field newly consumed by the Astro article must be present in this
projection and covered by render-parity tests.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_DB = ROOT / "data" / "atlas.db"
DEFAULT_SYNONYM_VERDICTS = ROOT / "data" / "lexicon" / "synonym_pair_verdicts.yaml"

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
RELATED_PROVENANCES = {"verified", "unverified"}


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
CREATE TABLE IF NOT EXISTS manifest_metadata (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS article_payloads (
    slug TEXT PRIMARY KEY,
    route_order INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    is_public_route INTEGER NOT NULL CHECK (is_public_route IN (0, 1))
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
    visibility TEXT NOT NULL DEFAULT 'public' CHECK (visibility IN ({_sql_enum(VISIBILITIES)})),
    UNIQUE (alias, kind, target_slug)
);
CREATE TABLE IF NOT EXISTS related_entries (
    slug TEXT NOT NULL,
    related_slug TEXT NOT NULL,
    entry_type TEXT,
    relation TEXT NOT NULL,
    component_role TEXT,
    provenance TEXT NOT NULL CHECK (provenance IN ({_sql_enum(RELATED_PROVENANCES)})),
    CHECK (slug != related_slug),
    UNIQUE (slug, related_slug, relation, provenance),
    FOREIGN KEY (slug) REFERENCES articles(slug),
    FOREIGN KEY (related_slug) REFERENCES articles(slug)
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
CREATE INDEX IF NOT EXISTS idx_related_entries_slug_relation ON related_entries(slug, relation);
CREATE INDEX IF NOT EXISTS idx_enrichment_slug ON enrichment(slug);
CREATE INDEX IF NOT EXISTS idx_article_payloads_route ON article_payloads(is_public_route, route_order);
CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    slug UNINDEXED, display_head, lemma, gloss, aliases
);
"""

_STRESS_RE = re.compile("[́̀]")
_APOSTROPHE_TRANSLATION = str.maketrans({"’": "'", "ʼ": "'"})
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


def _relation_lemma_key(lemma: str) -> str:
    """Normalize a verdict lemma to the same comparison surface as aliases."""
    return unstressed(lemma).translate(_APOSTROPHE_TRANSLATION).casefold().strip()


def _load_verified_synonym_pairs(verdicts_path: Path) -> tuple[list[tuple[str, str]], int]:
    """Load only approved synonym verdicts; raw candidate sources never enter Atlas.

    The verdict file is the cross-family adjudicated source of truth.  Its
    ``sources`` tags are intentionally not used as a filter: an approved pair
    remains verified even when one of several attestations is Ukrajinet's
    ``synonyms`` source.
    """
    data = yaml.safe_load(verdicts_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Synonym verdicts must be a mapping: {verdicts_path}")
    approved = data.get("approved")
    if not isinstance(approved, list):
        raise ValueError(f"Synonym verdicts approved section must be a list: {verdicts_path}")

    pairs: set[tuple[str, str]] = set()
    self_pairs_skipped = 0
    for index, verdict in enumerate(approved):
        if not isinstance(verdict, dict):
            raise ValueError(f"Approved synonym verdict {index} must be a mapping: {verdicts_path}")
        if verdict.get("polarity") != "synonym":
            continue
        a = _relation_lemma_key(str(verdict.get("a") or ""))
        b = _relation_lemma_key(str(verdict.get("b") or ""))
        if not a or not b:
            raise ValueError(f"Approved synonym verdict {index} lacks a lemma: {verdicts_path}")
        if a == b:
            self_pairs_skipped += 1
            continue
        pairs.add(tuple(sorted((a, b))))
    return sorted(pairs), self_pairs_skipped


def _relation_targets_by_lemma(cur: sqlite3.Cursor) -> dict[str, tuple[str, ...]]:
    """Map verdict lemmas to public Atlas slugs through the aliases table.

    Older builds intentionally omit aliases that equal their article slug.  The
    exact-lemma fallback covers those canonical rows without deriving a slug
    from source text; non-identical route slugs must still resolve through an
    emitted alias.
    """
    targets: dict[str, set[str]] = {}
    for alias, target_slug in cur.execute(
        "SELECT alias, target_slug FROM aliases WHERE visibility = 'public'"
    ):
        targets.setdefault(_relation_lemma_key(str(alias)), set()).add(str(target_slug))
    for lemma, slug in cur.execute(
        """SELECT lemma, slug FROM articles
           WHERE review_state = 'approved' AND visibility = 'public'"""
    ):
        targets.setdefault(_relation_lemma_key(str(lemma)), set()).add(str(slug))
    return {lemma: tuple(sorted(slugs)) for lemma, slugs in targets.items()}


def _insert_verified_synonym_relations(
    cur: sqlite3.Cursor,
    verdicts_path: Path,
) -> dict[str, int]:
    """Insert deterministic symmetric edges from approved synonym verdicts."""
    pairs, self_pairs_skipped = _load_verified_synonym_pairs(verdicts_path)
    targets_by_lemma = _relation_targets_by_lemma(cur)
    rows: set[tuple[str, str, str, str]] = set()
    unresolved_pairs = 0

    for a, b in pairs:
        a_targets = targets_by_lemma.get(a, ())
        b_targets = targets_by_lemma.get(b, ())
        if not a_targets or not b_targets:
            unresolved_pairs += 1
            continue
        for a_slug in a_targets:
            for b_slug in b_targets:
                if a_slug == b_slug:
                    continue
                rows.add((a_slug, b_slug, "synonym", "verified"))
                rows.add((b_slug, a_slug, "synonym", "verified"))

    cur.executemany(
        """INSERT INTO related_entries(slug, related_slug, relation, provenance)
           VALUES (?, ?, ?, ?)""",
        sorted(rows),
    )
    return {
        "verified_synonym_pairs": len(pairs),
        "verified_synonym_pairs_unresolved": unresolved_pairs,
        "verified_synonym_self_pairs_skipped": self_pairs_skipped,
        "related_entries": len(rows),
    }


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


def is_public_route_payload(entry: dict[str, Any]) -> bool:
    """Mirror the current Astro word-page route filter for compatibility payloads."""
    lemma = str(entry.get("lemma") or "").strip()
    slug = str(entry.get("url_slug") or "").strip()
    return bool(lemma and slug and entry.get("pos") != "grammar term")


def _insert_manifest_metadata(cur: sqlite3.Cursor, manifest: dict[str, Any]) -> None:
    for key in ("version", "generated_at"):
        value = manifest.get(key)
        if value is not None:
            cur.execute(
                "INSERT OR REPLACE INTO manifest_metadata(key, value_json) VALUES (?, ?)",
                (key, json.dumps(value, ensure_ascii=False)),
            )


def migrate_manifest(
    manifest_path: Path,
    db_path: Path,
    synonym_verdicts_path: Path = DEFAULT_SYNONYM_VERDICTS,
) -> dict[str, int]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    cur = conn.cursor()
    _insert_manifest_metadata(cur, manifest)

    counts = {"articles": 0, "aliases": 0, "provenance": 0, "enrichment": 0, "form_aliases": 0, "payloads": 0}
    by_type: dict[str, int] = {}

    # first pass: gather article slugs so form_of aliases only resolve to real articles
    article_visibility: dict[str, str] = {}
    for e in entries:
        if e.get("form_of"):
            continue
        slug = str(e.get("url_slug") or e.get("lemma")).strip()
        if slug:
            article_visibility[slug] = "private" if e.get("pos") == "grammar term" else "public"

    def _form_of_target(form_of: Any) -> str | None:
        if isinstance(form_of, dict):
            return str(form_of.get("url_slug") or form_of.get("lemma") or "").strip() or None
        return str(form_of).strip() or None

    for route_order, e in enumerate(entries):
        lemma = str(e.get("lemma") or "").strip()
        slug = str(e.get("url_slug") or lemma).strip()
        if not lemma or not slug:
            continue
        display_head = str(e.get("display_head") or lemma).strip()

        if is_public_route_payload(e):
            cur.execute(
                """INSERT OR REPLACE INTO article_payloads
                   (slug, route_order, payload_json, is_public_route)
                   VALUES (?, ?, ?, 1)""",
                (slug, route_order, json.dumps(e, ensure_ascii=False)),
            )
            counts["payloads"] += 1

        # form_of records -> alias rows, not articles (only if target is a real article)
        form_of = e.get("form_of")
        if form_of:
            target = _form_of_target(form_of)
            if target and target in article_visibility:
                cur.execute(
                    "INSERT OR IGNORE INTO aliases(alias, kind, source, target_slug, visibility) VALUES (?,?,?,?,?)",
                    (unstressed(lemma), "inflected_form", "manifest:form_of", target, article_visibility[target]),
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
                cur.execute(
                    "INSERT OR IGNORE INTO aliases(alias, kind, source, target_slug, visibility) VALUES (?,?,?,?,?)",
                    (a, k, s, t, visibility),
                )
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

    counts.update(_insert_verified_synonym_relations(cur, synonym_verdicts_path))

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


def validate_alias_targets(db_path: Path) -> dict[str, int]:
    """Validate every emitted alias resolves to an approved public article."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    failures = conn.execute(
        """SELECT al.alias, al.kind, al.target_slug, a.review_state, a.visibility
           FROM aliases al
           LEFT JOIN articles a ON a.slug = al.target_slug
           WHERE al.visibility = 'public'
             AND (
                a.slug IS NULL
                OR a.review_state != 'approved'
                OR a.visibility != 'public'
             )
           ORDER BY al.target_slug, al.kind, al.alias"""
    ).fetchall()
    counts = {
        "public_aliases": int(conn.execute("SELECT COUNT(*) FROM aliases WHERE visibility='public'").fetchone()[0]),
        "private_aliases": int(conn.execute("SELECT COUNT(*) FROM aliases WHERE visibility='private'").fetchone()[0]),
        "distinct_public_targets": int(
            conn.execute("SELECT COUNT(DISTINCT target_slug) FROM aliases WHERE visibility='public'").fetchone()[0]
        ),
        "approved_public_articles": int(
            conn.execute("SELECT COUNT(*) FROM articles WHERE review_state='approved' AND visibility='public'").fetchone()[0]
        ),
        "failures": len(failures),
    }
    conn.close()

    if failures:
        for row in failures:
            if row["review_state"] is None:
                reason = "missing target article"
            elif row["review_state"] != "approved":
                reason = f"target review_state={row['review_state']!r}"
            else:
                reason = f"target visibility={row['visibility']!r}"
            print(
                "alias_target_integrity failure: "
                f"alias={row['alias']!r} kind={row['kind']!r} target_slug={row['target_slug']!r} reason={reason}",
                file=sys.stderr,
            )
        raise ValueError(f"{len(failures)} alias target(s) are not approved public articles")

    print("atlas_db alias validation:", json.dumps(counts, ensure_ascii=False))
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description="Build/migrate the Word Atlas entry-model v1 SQLite DB.")
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument(
        "--validate-aliases-only",
        action="store_true",
        help="Validate alias targets in an existing DB without rebuilding it.",
    )
    args = ap.parse_args()
    try:
        if args.validate_aliases_only:
            validate_alias_targets(args.db)
            return
        counts = migrate_manifest(args.manifest, args.db)
        by_type = counts.pop("by_type", {})
        print("atlas_db migrate:", json.dumps(counts, ensure_ascii=False))
        print("by entry_type:", json.dumps(by_type, ensure_ascii=False))
        validate_alias_targets(args.db)
    except ValueError as exc:
        print(f"atlas_db validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
