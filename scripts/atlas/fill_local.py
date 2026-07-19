"""Phase-1 local enrichment writer for ``data/atlas.db``.

The writer reuses ``scripts.lexicon.enrich_manifest.enrich_entry`` and stores
each attached field as a resumable row in ``enrichment``. Phase 1 is forced
offline with ``LEXICON_SLOVNYK_OFFLINE=1``: existing local caches may be read,
but cache misses must stay absent and never open a socket.

Before the per-article loop, the fill cohort gets the same run-level
precomputes as full ``enrich()`` / ``worker_enrich`` (#5331): CEFR quantile
estimates via ``_prepare_cefr_estimates`` and closed
``pointer_{synonym,antonym,homonym,paronym}_relations`` maps (reciprocal
within the fill cohort).

Absent-vs-uncovered rule:

- Phase-2-fillable sections stay absent when Phase 1 has no payload:
  ``meaning``, ``definition_cards``, ``synonyms``, ``idioms``, and
  ``wiki_reference``.
- Optional evidence sections stay absent when no source-attested datum exists:
  ``antonyms``, ``literary_attestation``, and ``calque_note``.
- General local article fields that Phase 2 will not fill are marked with an
  empty ``phase='uncovered'`` row when missing: ``cefr``, ``etymology``,
  ``morphology``, ``pronunciation``, ``stress``, ``translation``, and
  ``heritage_status``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.atlas import atlas_db
from scripts.lexicon import enrich_manifest

DEFAULT_DB = atlas_db.DEFAULT_DB
DEFAULT_SOURCES_DB = enrich_manifest.SOURCES_DB
DEFAULT_KAIKKI_LOOKUP = enrich_manifest.KAIKKI_LOOKUP

PHASE = "local"
UNCOVERED_PHASE = "uncovered"
UNCOVERED_SOURCE = "phase1-local:uncovered"
CALQUE_NOTE_KEY = "\u00a76_note"

PHASE2_FILLABLE_SECTIONS = {
    "meaning",
    "definition_cards",
    "synonyms",
    "idioms",
    "wiki_reference",
}
OPTIONAL_EVIDENCE_SECTIONS = {
    "antonyms",
    "calque_note",
    "literary_attestation",
}
UNCOVERED_ON_EMPTY_SECTIONS = (
    "cefr",
    "etymology",
    "heritage_status",
    "morphology",
    "pronunciation",
    "stress",
    "translation",
)

enrich_entry = enrich_manifest.enrich_entry


@dataclass(frozen=True)
class CoverageCell:
    rows: int
    uncovered: int


@dataclass(frozen=True)
class FillResult:
    total: int
    considered: int
    inserted: int
    skipped_existing: int
    before: dict[str, CoverageCell]
    after: dict[str, CoverageCell]


def _iso_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _article_rows(conn: sqlite3.Connection, slug: str | None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM articles"
    params: tuple[str, ...] = ()
    if slug:
        sql += " WHERE slug = ?"
        params = (slug,)
    sql += " ORDER BY slug"
    return list(conn.execute(sql, params).fetchall())


def _source_provenance(conn: sqlite3.Connection, slug: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """SELECT source_family, source_locator, extraction_mode
           FROM article_provenance
           WHERE slug = ?
           ORDER BY rowid""",
        (slug,),
    ).fetchall()
    return [
        {
            "source_family": row["source_family"],
            "source_locator": row["source_locator"],
            "extraction_mode": row["extraction_mode"],
        }
        for row in rows
    ]


def _entry_from_article(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    provenance = _source_provenance(conn, row["slug"])
    entry: dict[str, Any] = {
        "lemma": row["lemma"],
        "url_slug": row["slug"],
        "display_head": row["display_head"],
        "entry_type": row["entry_type"],
        "review_state": row["review_state"],
        "visibility": row["visibility"],
    }
    for key in ("pos", "gloss", "created_at", "updated_at"):
        if row[key]:
            entry[key] = row[key]
    if provenance:
        entry["source_provenance"] = provenance
        if provenance[0].get("source_family"):
            entry["primary_source"] = provenance[0]["source_family"]
    return entry


def _existing_payloads(conn: sqlite3.Connection, slug: str) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT section, payload_json FROM enrichment WHERE slug = ?",
        (slug,),
    ).fetchall()
    payloads: dict[str, Any] = {}
    for row in rows:
        try:
            payload = json.loads(row["payload_json"])
        except (TypeError, ValueError):
            payload = {}
        payloads[str(row["section"])] = payload
    return payloads


@contextmanager
def _skip_existing_extractors(existing_payloads: dict[str, Any]) -> Iterator[None]:
    replacements: dict[str, Callable[..., Any]] = {}
    if "pronunciation" in existing_payloads:
        replacements["_kaikki_pronunciation"] = lambda *args, **kwargs: None
    if "synonyms" in existing_payloads:
        replacements["_synonyms_slovnyk"] = lambda *args, **kwargs: None
    if "antonyms" in existing_payloads:
        replacements["_antonyms_wiktionary"] = lambda *args, **kwargs: None
    if "idioms" in existing_payloads:
        replacements["_idioms"] = lambda *args, **kwargs: None
    if "stress" in existing_payloads:
        replacements["_stress_display_form"] = lambda *args, **kwargs: ""
        replacements["_kaikki_stress"] = lambda *args, **kwargs: None
    if "cefr" in existing_payloads:
        replacements["_cefr"] = lambda *args, **kwargs: None
    if "morphology" in existing_payloads:
        replacements["_morphology"] = lambda *args, **kwargs: None
    if "meaning" in existing_payloads:
        replacements["_meaning"] = lambda *args, **kwargs: None
        replacements["_proper_noun_wikipedia_meaning"] = lambda *args, **kwargs: None
    if "definition_cards" in existing_payloads:
        replacements["_definition_cards"] = lambda *args, **kwargs: []
    if "etymology" in existing_payloads:
        replacements["_etymology"] = lambda *args, **kwargs: None
    if "literary_attestation" in existing_payloads:
        replacements["_literary_attestation"] = lambda *args, **kwargs: None
    if "translation" in existing_payloads:
        replacements["_translation"] = lambda *args, **kwargs: None
    if "wiki_reference" in existing_payloads:
        replacements["_wiki_reference"] = lambda *args, **kwargs: None
    if "heritage_status" in existing_payloads:
        heritage_payload = existing_payloads["heritage_status"]
        if isinstance(heritage_payload, dict):
            replacements["classify_lemma"] = lambda *args, **kwargs: dict(heritage_payload)
            replacements["_warning_slovnyk"] = lambda *args, **kwargs: None

    originals = {name: getattr(enrich_manifest, name) for name in replacements}
    try:
        for name, replacement in replacements.items():
            setattr(enrich_manifest, name, replacement)
        yield
    finally:
        for name, original in originals.items():
            setattr(enrich_manifest, name, original)


def _source_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        out: list[str] = []
        for key in ("source", "source_label", "source_pill", "attribution"):
            raw = value.get(key)
            if isinstance(raw, list | tuple | set):
                out.extend(str(item) for item in raw if item)
            elif raw:
                out.append(str(raw))
        nested = value.get("sources")
        if isinstance(nested, list | tuple | set):
            out.extend(str(item) for item in nested if item)
        return out
    if isinstance(value, list | tuple):
        out = []
        for item in value:
            out.extend(_source_values(item))
        return out
    return []


def _source_label(section: str, payload: Any) -> str | None:
    values = list(dict.fromkeys(_source_values(payload)))
    if values:
        return " + ".join(values)
    if section == "heritage_status":
        return "heritage_classifier"
    if section == "wiki_reference":
        return "query_wikipedia/cache"
    return None


def _add_payload(out: dict[str, Any], section: str, payload: Any) -> None:
    if section not in atlas_db.ENRICHMENT_SECTIONS:
        return
    if not payload:
        return
    out[section] = payload


def entry_payloads(entry: dict[str, Any]) -> dict[str, Any]:
    payloads: dict[str, Any] = {}

    enrichment = entry.get("enrichment")
    if isinstance(enrichment, dict):
        for section, payload in enrichment.items():
            if section == "sources":
                continue
            _add_payload(payloads, str(section), payload)

    sections = entry.get("sections")
    if isinstance(sections, dict):
        for section, payload in sections.items():
            _add_payload(payloads, str(section), payload)

    for section in ("pronunciation", "wiki_reference", "heritage_status"):
        _add_payload(payloads, section, entry.get(section))

    heritage = entry.get("heritage_status")
    if isinstance(heritage, dict):
        _add_payload(payloads, "calque_note", heritage.get(CALQUE_NOTE_KEY))

    return payloads


def _uncovered_sections(payloads: dict[str, Any]) -> list[str]:
    return [section for section in UNCOVERED_ON_EMPTY_SECTIONS if section not in payloads]


def _coverage(conn: sqlite3.Connection) -> dict[str, CoverageCell]:
    rows = conn.execute(
        """SELECT section,
                  COUNT(DISTINCT slug) AS row_count,
                  COUNT(DISTINCT CASE WHEN phase = 'uncovered' THEN slug END) AS uncovered_count
           FROM enrichment
           GROUP BY section"""
    ).fetchall()
    by_section = {
        str(row["section"]): CoverageCell(rows=int(row["row_count"]), uncovered=int(row["uncovered_count"]))
        for row in rows
    }
    return {
        section: by_section.get(section, CoverageCell(rows=0, uncovered=0))
        for section in sorted(atlas_db.ENRICHMENT_SECTIONS)
    }


def _coverage_json(cells: dict[str, CoverageCell]) -> dict[str, dict[str, int]]:
    return {section: {"rows": cell.rows, "uncovered": cell.uncovered} for section, cell in cells.items()}


def format_coverage_table(
    before: dict[str, CoverageCell],
    after: dict[str, CoverageCell],
    total: int,
) -> str:
    lines = [
        "section                 before       after        uncovered_after",
        "----------------------  -----------  -----------  ---------------",
    ]
    for section in sorted(atlas_db.ENRICHMENT_SECTIONS):
        before_cell = before[section]
        after_cell = after[section]
        lines.append(
            f"{section:<22}  "
            f"{before_cell.rows:>5}/{total:<5}  "
            f"{after_cell.rows:>5}/{total:<5}  "
            f"{after_cell.uncovered:>15}"
        )
    return "\n".join(lines)


@contextmanager
def _phase1_offline_env() -> Iterator[None]:
    previous = os.environ.get("LEXICON_SLOVNYK_OFFLINE")
    os.environ["LEXICON_SLOVNYK_OFFLINE"] = "1"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("LEXICON_SLOVNYK_OFFLINE", None)
        else:
            os.environ["LEXICON_SLOVNYK_OFFLINE"] = previous


def fill_local(
    db_path: Path = DEFAULT_DB,
    sources_db_path: Path = DEFAULT_SOURCES_DB,
    kaikki_lookup_path: Path = DEFAULT_KAIKKI_LOOKUP,
    *,
    slug: str | None = None,
    refresh: bool = False,
) -> FillResult:
    with _phase1_offline_env():
        return _fill_local(
            db_path,
            sources_db_path,
            kaikki_lookup_path,
            slug=slug,
            refresh=refresh,
        )


def _cohort_manifest(articles: list[sqlite3.Row]) -> dict[str, Any]:
    """Build a mini-manifest for CEFR quantiles + closed pointer maps (#5331)."""
    return {
        "entries": [
            {
                "lemma": row["lemma"],
                "url_slug": row["slug"],
                "pos": row["pos"],
                "gloss": row["gloss"],
            }
            for row in articles
        ]
    }


def _pointer_relation_maps(
    sources_conn: sqlite3.Connection,
    cohort_manifest: dict[str, Any],
    *,
    has_sum11_flags: bool,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Precompute reciprocal pointer maps over the fill cohort (mirror enrich())."""
    return {
        "synonym": enrich_manifest._definition_pointer_relations_by_headword(
            sources_conn, cohort_manifest, has_sum11_flags=has_sum11_flags
        ),
        "antonym": enrich_manifest._definition_antonym_relations_by_headword(
            sources_conn, cohort_manifest, has_sum11_flags=has_sum11_flags
        ),
        "homonym": enrich_manifest._homonym_relations_by_headword(
            sources_conn, cohort_manifest
        ),
        "paronym": enrich_manifest._paronym_relations_by_headword(
            sources_conn, cohort_manifest
        ),
    }


def _fill_local(
    db_path: Path = DEFAULT_DB,
    sources_db_path: Path = DEFAULT_SOURCES_DB,
    kaikki_lookup_path: Path = DEFAULT_KAIKKI_LOOKUP,
    *,
    slug: str | None = None,
    refresh: bool = False,
) -> FillResult:
    with _connect(db_path) as atlas_conn, sqlite3.connect(sources_db_path) as sources_conn:
        articles = _article_rows(atlas_conn, slug)
        if slug and not articles:
            raise ValueError(f"slug not found in atlas DB: {slug}")

        total = int(atlas_conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0])
        before = _coverage(atlas_conn)
        kaikki_lookup = enrich_manifest._load_kaikki_lookup(kaikki_lookup_path)
        has_sum11_flags = enrich_manifest._sum11_has_flag_columns(sources_conn)

        # Align with full enrich / worker_enrich (#5331): prepare cohort CEFR
        # estimates and closed pointer maps before the per-article loop. Single-slug
        # fills only close relations within that slug set; full-atlas fills get
        # cohort-wide reciprocity. Sealed full-cohort maps remain the #5230 path.
        cohort_manifest = _cohort_manifest(articles)
        enrich_manifest._prepare_cefr_estimates(sources_conn, cohort_manifest)
        pointer_maps = _pointer_relation_maps(
            sources_conn, cohort_manifest, has_sum11_flags=has_sum11_flags
        )

        filled_at = _iso_now()
        inserted = 0
        skipped_existing = 0

        for article in articles:
            entry = _entry_from_article(atlas_conn, article)
            existing_payloads = {} if refresh else _existing_payloads(atlas_conn, article["slug"])
            entry_key = enrich_manifest._canonical_synonym_term(str(entry.get("lemma") or "")) or ""
            with _skip_existing_extractors(existing_payloads):
                enrich_entry(
                    entry,
                    sources_conn,
                    kaikki_lookup,
                    has_sum11_flags=has_sum11_flags,
                    pointer_synonym_relations=pointer_maps["synonym"].get(entry_key, []),
                    pointer_antonym_relations=pointer_maps["antonym"].get(entry_key, []),
                    pointer_homonym_relations=pointer_maps["homonym"].get(entry_key, []),
                    pointer_paronym_relations=pointer_maps["paronym"].get(entry_key, []),
                )
            payloads = entry_payloads(entry)
            uncovered = set(_uncovered_sections(payloads))
            for section in uncovered:
                payloads[section] = {}

            existing = set(existing_payloads)
            for section, payload in sorted(payloads.items()):
                if section in existing:
                    skipped_existing += 1
                    continue
                phase = UNCOVERED_PHASE if section in uncovered else PHASE
                source = UNCOVERED_SOURCE if phase == UNCOVERED_PHASE else _source_label(section, payload)
                atlas_conn.execute(
                    """INSERT OR REPLACE INTO enrichment
                       (slug, section, payload_json, source, filled_at, phase)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        article["slug"],
                        section,
                        json.dumps(payload, ensure_ascii=False, sort_keys=True),
                        source,
                        filled_at,
                        phase,
                    ),
                )
                inserted += 1
            atlas_conn.commit()

        after = _coverage(atlas_conn)

    return FillResult(
        total=total,
        considered=len(articles),
        inserted=inserted,
        skipped_existing=skipped_existing,
        before=before,
        after=after,
    )


def _write_report_json(path: Path, result: FillResult) -> None:
    payload = {
        "total": result.total,
        "considered": result.considered,
        "inserted": result.inserted,
        "skipped_existing": result.skipped_existing,
        "before": _coverage_json(result.before),
        "after": _coverage_json(result.after),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fill data/atlas.db with Phase-1 local enrichment rows.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to atlas.db.")
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB, help="Path to data/sources.db.")
    parser.add_argument(
        "--kaikki-lookup",
        type=Path,
        default=DEFAULT_KAIKKI_LOOKUP,
        help="Path to data/lexicon/kaikki_uk_lookup.json.",
    )
    parser.add_argument("--slug", help="Fill one atlas article slug.")
    parser.add_argument("--refresh", action="store_true", help="Replace existing rows for sections produced now.")
    parser.add_argument("--report-json", type=Path, help="Write machine-readable before/after coverage report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = fill_local(
        args.db,
        args.sources_db,
        args.kaikki_lookup,
        slug=args.slug,
        refresh=args.refresh,
    )
    print(format_coverage_table(result.before, result.after, result.total))
    print(
        "filled "
        f"{result.inserted} rows across {result.considered}/{result.total} articles "
        f"(skipped_existing={result.skipped_existing}, refresh={args.refresh})"
    )
    if args.report_json:
        _write_report_json(args.report_json, result)
        print(f"wrote report_json={args.report_json}")


if __name__ == "__main__":
    main()
