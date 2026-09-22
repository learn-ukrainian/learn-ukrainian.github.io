#!/usr/bin/env python3
"""Read-only thin-page report over the Atlas entry store (``data/atlas.db``).

For every public Atlas entry the report computes a thinness tier, the list of
missing enrichment layers (all 18 ``ENRICHMENT_SECTIONS``), and how many of
those gaps each already-local source could fill today.  It never writes to any
database or manifest: every SQLite connection is opened with ``mode=ro``, so
the report is safe to run while ``dump_ulif.py`` holds the writer on
``data/ulif_dump_all.db``.

Definitions (the documented rule — AC-01 of #8313):

* **filled section** — an ``enrichment`` row exists for (slug, section) whose
  payload is non-empty JSON.  Empty ``phase='uncovered'`` placeholder rows
  written by ``scripts/atlas/fill_local.py`` count as missing.
* **rich buckets** — 8 learner-facing buckets mirroring the publish gate's
  richness bar: meaning (``meaning`` | ``definition_cards`` | article gloss),
  ``etymology``, ``morphology``, synonyms/antonyms, ``idioms``,
  ``literary_attestation``, ``translation``, ``wiki_reference``.
* **tier per entry** —
  ``bare``  : no definition layer (no filled ``meaning``/``definition_cards``
  and no article gloss) AND no filled ``translation``;
  ``thin``  : not bare, but fewer than 5 filled rich buckets;
  ``rich``  : 5 or more filled rich buckets.

The tier bar deliberately mirrors — but does not reproduce — the publish
gate's ``poc_thin_pages`` (``scripts/audit/audit_atlas_poc_richness.py``).
That gate reads the *manifest*, counts ``course_usage`` as a ninth bucket,
exempts form stubs, excludes SUM-11 definition cards, and applies a special
multiword rule; this report reads ``data/atlas.db`` and applies one uniform
bar to every public entry.  The two counts are expected to differ.

Fillability probes are heuristic on purpose: a probe says "this local source
has material for this lemma", not "the payload is publish-ready".
``sum11`` is excluded (rendered pages drop SUM-11 definition cards) and
``balla_en_uk`` is excluded (keyed by the English side, not by Ukrainian
lemma).  ULIF material inside ``sources.db`` (``ulif_dictua_*``) is skipped in
favour of the fresher, larger ``data/ulif_dump_all.db``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import sys
import unicodedata
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.atlas.atlas_db import ENRICHMENT_SECTIONS, unstressed
from scripts.lexicon.enrich_manifest import (
    _leading_phraseology_phrase,
    _load_current_slovnyk_cache_file,
    _phrase_contains_lemma,
)

DEFAULT_ATLAS_DB = PROJECT_ROOT / "data" / "atlas.db"
DEFAULT_SOURCES_DB = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_ULIF_DB = PROJECT_ROOT / "data" / "ulif_dump_all.db"
DEFAULT_SLOVNYK_CACHE = PROJECT_ROOT / "data" / "lexicon" / "slovnyk_cache"

# SQL-comparable payloads that mean "row exists but carries nothing".
EMPTY_PAYLOADS = ("{}", "[]", "null", '""', "")

TIER_BARE = "bare"
TIER_THIN = "thin"
TIER_RICH = "rich"
TIER_ORDER = (TIER_BARE, TIER_THIN, TIER_RICH)
MIN_RICH_BUCKETS = 5

# The 8 rich buckets (meaning is special-cased for the article gloss).
RICH_BUCKETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("meaning", ("meaning", "definition_cards")),
    ("etymology", ("etymology",)),
    ("morphology", ("morphology",)),
    ("synonyms_antonyms", ("synonyms", "antonyms")),
    ("idioms", ("idioms",)),
    ("literary_attestation", ("literary_attestation",)),
    ("translation", ("translation",)),
    ("wikipedia", ("wiki_reference",)),
)

# slovnyk.me cache dictionary slug -> Atlas sections it can fill
# (mapping mirrors scripts/lexicon/enrich_manifest.py's extractor wiring).
SLOVNYK_LOOKUP_SECTIONS: dict[str, tuple[str, ...]] = {
    "newsum": ("meaning", "definition_cards"),
    "vts": ("meaning", "definition_cards"),
    "synonyms": ("synonyms",),
    "phraseology": ("idioms",),
    "proverbs": ("proverbs",),
    "ukreng": ("translation",),
    "davydov": ("usage_notes",),
    "linguistic_norm": ("usage_notes",),
    "khreshchatyk": ("usage_notes",),
    "voloschak": ("usage_notes",),
    "foreign_shtepa": ("usage_notes",),
    "orthography": ("form_notes",),
    "holoskevych": ("form_notes",),
    "orthoepy": ("form_notes",),
}

SOURCE_SLOVNYK = "slovnyk_cache"
SOURCE_ULIF = "ulif_dump"
SOURCE_FRAZEOLOHICHNYI = "sources.db:frazeolohichnyi"
FRAZEOLOHICHNYI_PAGE_SIZE = 80

# Exact-lemma-keyed sources.db dictionaries:
# source name -> (SQL producing normalizable keys, sections it can fill).
SOURCES_DB_PROBES: dict[str, tuple[str, tuple[str, ...]]] = {
    "sources.db:sum20": (
        "SELECT normalized_lookup_key FROM sum20_articles WHERE definition_text IS NOT NULL AND definition_text != ''",
        ("meaning", "definition_cards"),
    ),
    "sources.db:grinchenko": (
        "SELECT word FROM grinchenko WHERE definition IS NOT NULL AND definition != ''",
        ("definition_cards",),
    ),
    "sources.db:dmklinger_uk_en": (
        "SELECT word FROM dmklinger_uk_en WHERE translations IS NOT NULL AND translations != ''",
        ("translation",),
    ),
    "sources.db:esum_etymology": (
        "SELECT lemma FROM esum_etymology_meta WHERE etymology_text IS NOT NULL AND etymology_text != ''",
        ("etymology",),
    ),
    "sources.db:puls_cefr": (
        "SELECT word FROM puls_cefr WHERE level IS NOT NULL AND level != ''",
        ("cefr",),
    ),
    "sources.db:wiktionary_synonyms": (
        "SELECT word FROM wiktionary WHERE synonyms IS NOT NULL AND synonyms NOT IN ('', '[]')",
        ("synonyms",),
    ),
    "sources.db:wiktionary_antonyms": (
        "SELECT word FROM wiktionary WHERE antonyms IS NOT NULL AND antonyms NOT IN ('', '[]')",
        ("antonyms",),
    ),
}

_APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'", "`": "'"})


@dataclass
class EntryReport:
    """Tier and missing-layer profile of one public Atlas entry."""

    slug: str
    lemma: str
    entry_type: str
    tier: str
    rich_buckets: int
    missing: list[str] = field(default_factory=list)


def normalize_key(text: str) -> str:
    """Normalize a lemma/headword to the report's cross-source match key."""
    cleaned = unstressed(unicodedata.normalize("NFC", str(text or "")))
    return cleaned.translate(_APOSTROPHES).casefold().strip()


def _connect_ro(path: Path) -> sqlite3.Connection:
    """Open a SQLite database strictly read-only (safe next to live writers)."""
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30.0)


def _filled_sections_by_slug(conn: sqlite3.Connection) -> dict[str, set[str]]:
    placeholders = ", ".join("?" for _ in EMPTY_PAYLOADS)
    filled: dict[str, set[str]] = {}
    for slug, section in conn.execute(
        f"SELECT slug, section FROM enrichment WHERE payload_json NOT IN ({placeholders})",
        EMPTY_PAYLOADS,
    ):
        filled.setdefault(str(slug), set()).add(str(section))
    return filled


def _rich_bucket_count(filled: set[str], gloss: str | None) -> int:
    count = 0
    for name, sections in RICH_BUCKETS:
        has = any(section in filled for section in sections)
        if name == "meaning" and not has and gloss and gloss.strip():
            has = True
        count += has
    return count


def classify_tier(filled: set[str], gloss: str | None) -> tuple[str, int]:
    """Apply the documented tier rule; returns (tier, rich_bucket_count)."""
    buckets = _rich_bucket_count(filled, gloss)
    has_definition = bool({"meaning", "definition_cards"} & filled or (gloss and gloss.strip()))
    has_translation = "translation" in filled
    if not has_definition and not has_translation:
        return TIER_BARE, buckets
    if buckets < MIN_RICH_BUCKETS:
        return TIER_THIN, buckets
    return TIER_RICH, buckets


def load_entry_reports(atlas_db: Path) -> list[EntryReport]:
    """Read all public Atlas entries and compute tier + missing sections."""
    sections_sorted = sorted(ENRICHMENT_SECTIONS)
    with _connect_ro(atlas_db) as conn:
        filled_by_slug = _filled_sections_by_slug(conn)
        rows = conn.execute(
            "SELECT slug, lemma, entry_type, gloss FROM articles WHERE visibility = 'public' ORDER BY slug"
        ).fetchall()

    reports: list[EntryReport] = []
    for slug, lemma, entry_type, gloss in rows:
        filled = filled_by_slug.get(str(slug), set())
        tier, buckets = classify_tier(filled, gloss)
        reports.append(
            EntryReport(
                slug=str(slug),
                lemma=str(lemma),
                entry_type=str(entry_type),
                tier=tier,
                rich_buckets=buckets,
                missing=[s for s in sections_sorted if s not in filled],
            )
        )
    return reports


def slovnyk_capabilities(cache_dir: Path) -> dict[str, set[str]]:
    """Map normalized lemma -> sections the slovnyk.me cache has material for."""
    capabilities: dict[str, set[str]] = {}
    for path in cache_dir.glob("*.json"):
        payload = _load_current_slovnyk_cache_file(path)
        if not payload or not isinstance(payload, dict):
            continue
        lookups = payload.get("lookups")
        if not isinstance(lookups, dict):
            continue
        sections = {
            section
            for slug, value in lookups.items()
            if value
            for section in SLOVNYK_LOOKUP_SECTIONS.get(str(slug), ())
        }
        if not sections:
            continue
        for raw_key in (payload.get("lemma"), payload.get("lookup_word")):
            key = normalize_key(str(raw_key or ""))
            if key:
                capabilities.setdefault(key, set()).update(sections)
    return capabilities


def ulif_capabilities(ulif_db: Path) -> dict[str, set[str]]:
    """Map normalized lemma -> sections the ULIF dump has material for."""
    capabilities: dict[str, set[str]] = {}
    with _connect_ro(ulif_db) as conn:
        rows = conn.execute(
            """SELECT lemma, canonical_headword,
                      paradigm_json IS NOT NULL AND paradigm_json != '',
                      synonyms_json IS NOT NULL AND synonyms_json NOT IN ('', '[]', 'null'),
                      antonyms_json IS NOT NULL AND antonyms_json NOT IN ('', '[]', 'null'),
                      phraseology_json IS NOT NULL AND phraseology_json NOT IN ('', '[]', 'null')
               FROM ulif_entries WHERE status = 'ok'"""
        )
        for lemma, headword, has_paradigm, has_syn, has_ant, has_phr in rows:
            sections: set[str] = set()
            if has_paradigm:
                sections.add("morphology")
            headword_text = str(headword or "")
            if headword_text and unstressed(headword_text) != unicodedata.normalize("NFC", headword_text):
                sections.add("stress")
            if has_syn:
                sections.add("synonyms")
            if has_ant:
                sections.add("antonyms")
            if has_phr:
                sections.add("idioms")
            if not sections:
                continue
            for raw_key in (lemma, headword):
                key = normalize_key(str(raw_key or ""))
                if key:
                    capabilities.setdefault(key, set()).update(sections)
    return capabilities


def sources_db_capabilities(sources_db: Path) -> dict[str, dict[str, set[str]]]:
    """Per-source normalized-lemma capability maps for exact-keyed sources.db tables."""
    result: dict[str, dict[str, set[str]]] = {}
    with _connect_ro(sources_db) as conn:
        for source, (sql, sections) in SOURCES_DB_PROBES.items():
            keys: dict[str, set[str]] = {}
            try:
                rows = conn.execute(sql)
            except sqlite3.OperationalError:
                continue  # table absent in this sources.db build
            for (raw_key,) in rows:
                key = normalize_key(str(raw_key or ""))
                if key:
                    keys.setdefault(key, set()).update(sections)
            result[source] = keys
    return result


def frazeolohichnyi_idiom_keys(
    sources_db: Path,
    candidate_keys: Iterable[str],
    *,
    page_size: int = FRAZEOLOHICHNYI_PAGE_SIZE,
) -> set[str]:
    """Return candidate lemma keys attested in the phraseological dictionary.

    The ``frazeolohichnyi`` table is keyed by idiom phrase, not by lemma, so
    membership is probed through its trigram FTS index and confirmed by
    extracting the idiom phrase and checking lemma containment.
    """
    found: set[str] = set()
    with _connect_ro(sources_db) as conn:
        has_fts = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'frazeolohichnyi_fts'"
        ).fetchone()
        if not has_fts:
            return found
        for key in candidate_keys:
            if len(key) < 3:  # trigram index cannot match shorter strings
                continue
            quoted = '"' + key.replace('"', '""') + '"'
            offset = 0
            while True:
                try:
                    rows = conn.execute(
                        "SELECT word, definition FROM frazeolohichnyi WHERE id IN ("
                        "  SELECT rowid FROM frazeolohichnyi_fts WHERE frazeolohichnyi_fts MATCH ?"
                        ") ORDER BY id LIMIT ? OFFSET ?",
                        (quoted, page_size, offset),
                    ).fetchall()
                except sqlite3.OperationalError:
                    return found
                if not rows:
                    break
                matched = False
                for word, definition in rows:
                    phrase = _leading_phraseology_phrase(definition or "", word or "")
                    if phrase and _phrase_contains_lemma(phrase, key):
                        found.add(key)
                        matched = True
                        break
                if matched or len(rows) < page_size:
                    break
                offset += page_size
    return found


def _fillable_counts(
    reports: Sequence[EntryReport],
    capability_maps: dict[str, dict[str, set[str]]],
) -> dict[str, dict[str, int]]:
    fillable: dict[str, Counter[str]] = {section: Counter() for section in sorted(ENRICHMENT_SECTIONS)}
    for report in reports:
        key = normalize_key(report.lemma)
        if not key:
            continue
        for source, capabilities in capability_maps.items():
            sections = capabilities.get(key)
            if not sections:
                continue
            for section in report.missing:
                if section in sections:
                    fillable[section][source] += 1
    return {
        section: dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
        for section, counts in fillable.items()
        if counts
    }


def build_report(
    *,
    atlas_db: Path,
    sources_db: Path,
    ulif_db: Path,
    slovnyk_cache: Path,
    include_entries: bool = True,
) -> dict[str, Any]:
    """Assemble the full machine-readable thin-page report."""
    reports = load_entry_reports(atlas_db)

    availability: dict[str, dict[str, Any]] = {}
    capability_maps: dict[str, dict[str, set[str]]] = {}

    if slovnyk_cache.is_dir():
        capability_maps[SOURCE_SLOVNYK] = slovnyk_capabilities(slovnyk_cache)
        availability[SOURCE_SLOVNYK] = {"available": True, "keys": len(capability_maps[SOURCE_SLOVNYK])}
    else:
        availability[SOURCE_SLOVNYK] = {"available": False, "path": str(slovnyk_cache)}

    if ulif_db.is_file():
        capability_maps[SOURCE_ULIF] = ulif_capabilities(ulif_db)
        availability[SOURCE_ULIF] = {"available": True, "keys": len(capability_maps[SOURCE_ULIF])}
    else:
        availability[SOURCE_ULIF] = {"available": False, "path": str(ulif_db)}

    if sources_db.is_file():
        for source, keys in sources_db_capabilities(sources_db).items():
            capability_maps[source] = keys
            availability[source] = {"available": True, "keys": len(keys)}
        idiom_candidates = {normalize_key(report.lemma) for report in reports if "idioms" in report.missing} - {""}
        idiom_keys = frazeolohichnyi_idiom_keys(sources_db, sorted(idiom_candidates))
        capability_maps[SOURCE_FRAZEOLOHICHNYI] = {key: {"idioms"} for key in idiom_keys}
        availability[SOURCE_FRAZEOLOHICHNYI] = {"available": True, "keys": len(idiom_keys)}
    else:
        availability["sources.db"] = {"available": False, "path": str(sources_db)}

    tiers = Counter(report.tier for report in reports)
    tiers_by_entry_type: dict[str, Counter[str]] = {}
    for report in reports:
        tiers_by_entry_type.setdefault(report.entry_type, Counter())[report.tier] += 1

    missing_by_section = Counter()
    for report in reports:
        missing_by_section.update(report.missing)

    payload: dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "atlas_db": str(atlas_db),
        "tier_rule": (
            f"bare = no definition layer (meaning/definition_cards/gloss) and no translation; "
            f"thin = fewer than {MIN_RICH_BUCKETS} filled rich buckets of "
            f"{len(RICH_BUCKETS)} ({', '.join(name for name, _ in RICH_BUCKETS)}); "
            f"rich = the rest. Filled = non-empty enrichment payload."
        ),
        "sources": availability,
        "totals": {
            "public_entries": len(reports),
            "by_entry_type": dict(Counter(report.entry_type for report in reports).most_common()),
            "tiers": {tier: tiers.get(tier, 0) for tier in TIER_ORDER},
            "thin_or_bare": tiers.get(TIER_BARE, 0) + tiers.get(TIER_THIN, 0),
            "tiers_by_entry_type": {
                entry_type: {tier: counts.get(tier, 0) for tier in TIER_ORDER}
                for entry_type, counts in sorted(tiers_by_entry_type.items())
            },
        },
        "missing_by_section": {section: missing_by_section.get(section, 0) for section in sorted(ENRICHMENT_SECTIONS)},
        "fillable": _fillable_counts(reports, capability_maps),
    }
    if include_entries:
        payload["entries"] = [
            {
                "slug": report.slug,
                "lemma": report.lemma,
                "entry_type": report.entry_type,
                "tier": report.tier,
                "rich_buckets": report.rich_buckets,
                "missing": report.missing,
            }
            for report in reports
        ]
    return payload


def _print_summary(report: dict[str, Any]) -> None:
    totals = report["totals"]
    by_type = " · ".join(f"{name}={count}" for name, count in totals["by_entry_type"].items())
    print(f"Thin-page report — read-only view of {report['atlas_db']}")
    print(f"Public entries: {totals['public_entries']} ({by_type})")
    print(f"Tier rule: {report['tier_rule']}")
    print("Tiers:")
    for tier in TIER_ORDER:
        print(f"  {tier:<5} {totals['tiers'][tier]:>7}")
    print(f"  thin_or_bare = {totals['thin_or_bare']}")
    print("Sources scored:")
    for source, info in sorted(report["sources"].items()):
        if info.get("available"):
            print(f"  {source:<34} available, {info['keys']} lemma keys")
        else:
            print(f"  {source:<34} UNAVAILABLE ({info.get('path', '?')})")
    print("Missing sections (public entries without a non-empty payload):")
    denominator = totals["public_entries"]
    fillable = report["fillable"]
    for section, missing in report["missing_by_section"].items():
        share = f"{missing / denominator * 100:5.1f}%" if denominator else "  n/a"
        print(f"  {section:<21} {missing:>7}  {share}")
        for source, count in fillable.get(section, {}).items():
            print(f"      fillable via {source:<30} {count:>7}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scripts.lexicon.thin_page_report",
        description=(
            "Report how many public Atlas entries are thin, which of the 18 enrichment "
            "sections each is missing, and how many gaps each already-local source could fill.\n"
            "Use it to size enrichment work (#8313); it is read-only — do NOT use it to park, "
            "hide, or mutate entries (that is scripts/lexicon/park_thin_entries.py, deliberately not wired here)."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.lexicon.thin_page_report\n"
            "  .venv/bin/python -m scripts.lexicon.thin_page_report --json /tmp/thin.json\n"
            "  .venv/bin/python -m scripts.lexicon.thin_page_report --json /tmp/thin.json --no-entries\n"
            "\n"
            "Outputs:\n"
            "  stdout summary; with --json also a machine-readable report (totals, tier rule,\n"
            "  per-section missing counts, per-section x per-source fillable counts, and a\n"
            "  per-entry tier + missing-layer profile unless --no-entries). No DB or manifest\n"
            "  is ever written; all SQLite connections use mode=ro.\n"
            "\n"
            "Exit codes:\n"
            "  0  report produced (missing optional sources are reported as UNAVAILABLE)\n"
            "  2  bad input (e.g. atlas DB missing/unreadable)\n"
            "\n"
            "Related:\n"
            "  scripts/audit/audit_atlas_poc_richness.py (publish gate poc_thin_pages),\n"
            "  scripts/atlas/fill_local.py (Phase-1 filler), issue #8313 / epic #4387."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--atlas",
        type=Path,
        default=DEFAULT_ATLAS_DB,
        help=f"Path to atlas.db (read-only; default: {DEFAULT_ATLAS_DB}).",
    )
    parser.add_argument(
        "--sources-db",
        type=Path,
        default=DEFAULT_SOURCES_DB,
        help=f"Path to sources.db (read-only; default: {DEFAULT_SOURCES_DB}).",
    )
    parser.add_argument(
        "--ulif-db",
        type=Path,
        default=DEFAULT_ULIF_DB,
        help=(
            "Path to the growing ULIF dump DB (opened mode=ro, safe while dump_ulif.py writes; "
            f"default: {DEFAULT_ULIF_DB})."
        ),
    )
    parser.add_argument(
        "--slovnyk-cache",
        type=Path,
        default=DEFAULT_SLOVNYK_CACHE,
        help=f"Directory of slovnyk.me cache JSON files (default: {DEFAULT_SLOVNYK_CACHE}).",
    )
    parser.add_argument(
        "--json",
        type=Path,
        metavar="PATH",
        help="Write the machine-readable report JSON to PATH (e.g. /tmp/thin.json).",
    )
    parser.add_argument(
        "--no-entries",
        action="store_true",
        help="Omit the per-entry profile array from the JSON report (default: included).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = build_report(
            atlas_db=args.atlas,
            sources_db=args.sources_db,
            ulif_db=args.ulif_db,
            slovnyk_cache=args.slovnyk_cache,
            include_entries=not args.no_entries,
        )
    except (sqlite3.Error, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    _print_summary(report)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote json={args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
