"""Generate the small daily-curated Word Atlas pool.

Two source modes, mirroring ``generate_search_index``:

* ``--db data/atlas.db`` — read the daily-pool candidates from the entry-model
  SSOT (``atlas.db``). This is the site-build path (``npm run hydrate``): every
  learner-facing Atlas surface then reads from the one database. Candidate
  selection is structurally constrained to approved, public *article* rows, so
  ``form_of`` alias routes can never surface as Word-of-the-Day.
* ``--manifest`` (default) — the legacy flat-manifest path used by ``make atlas``
  before the DB is materialized.

Both modes feed the identical ``build_pool`` admission logic, so flipping the
source does not change which words are admitted (GH #4385, "no admission
changes"): the migration only moves the read to the SSOT.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from scripts.audit.generate_search_index import _site_build_entry_model_gates
from scripts.audit.lexeme_filter import (
    DERIVED_FORM_SOURCES,
    SURFACE_DAILY,
    SURZHYK_SOURCE,
    is_lexeme_entry,
    is_surface_admitted,
)

DEFAULT_MANIFEST = Path("site/src/data/lexicon-manifest.json")
DEFAULT_OUT = Path("site/src/data/lexicon-daily-pool.json")
DEFAULT_SENTENCE_INVENTORY = Path("site/src/data/lexicon-sentence-inventory.json")
EARLY_CEFR = {"A1", "A2", "B1"}
# Derived-form + surzhyk source tags live in scripts.audit.lexeme_filter (single source
# of truth, shared with the search index, word-page routes, and the practice deck).
# Keep the underscore-prefixed aliases for the existing references in this module.
_DERIVED_FORM_SOURCES = DERIVED_FORM_SOURCES
_SURZHYK_SOURCE = SURZHYK_SOURCE


def kind_for_source(source: Any) -> str:
    """Return the compact Atlas source-kind bucket for a manifest source."""
    if isinstance(source, str) and source.startswith("built_vocabulary"):
        return "vyv"
    if source == "plan_required":
        return "obov"
    if source == "plan_recommended":
        return "rek"
    if source == _SURZHYK_SOURCE:
        return "avoid"
    return "other"


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _first_course_track(entry: dict[str, Any]) -> str | None:
    course_usage = entry.get("course_usage")
    if not isinstance(course_usage, list) or not course_usage:
        return None
    first = course_usage[0]
    if not isinstance(first, dict):
        return None
    track = first.get("track")
    return track if _has_text(track) else None


def _early_cefr(entry: dict[str, Any]) -> str | None:
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return None
    cefr = enrichment.get("cefr")
    # In the real manifest, enrichment.cefr is a dict {"level": "A1", "source": ..., "text": ...};
    # tolerate a bare string too (defensive). Anything else → no early-CEFR signal.
    level = cefr.get("level") if isinstance(cefr, dict) else cefr
    return level if isinstance(level, str) and level in EARLY_CEFR else None


def compute_weight(entry: dict[str, Any]) -> int:
    """Return the deterministic daily-pool priority weight for a manifest entry."""
    weight = 0
    if _first_course_track(entry) is not None:
        weight += 3
    if entry.get("primary_source") == "surzhyk_to_avoid" and _has_text(entry.get("gloss")):
        weight += 2
    if _early_cefr(entry) is not None:
        weight += 2
    return weight


def _is_eligible(entry: dict[str, Any]) -> bool:
    """A daily card needs a real lemma headword and a translation; drop grammar metaterms
    (via is_lexeme_entry) and inflected/normalized duplicates so cards show headwords
    rather than case forms or grammar labels."""
    return (
        is_lexeme_entry(entry)
        and _has_text(entry.get("gloss"))
        and entry.get("primary_source") not in _DERIVED_FORM_SOURCES
        and is_surface_admitted(entry, SURFACE_DAILY)
    )


def _stable_hash(text: str) -> str:
    """Deterministic per-lemma ordering key (build-time only)."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _first_example(entry: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return the first verified example sentence and optional English gloss.

    Looks in common manifest/article payload shapes so the daily pool can carry
    one short example per word without a second large shard. Returns (None, None)
    when no usable sentence is present.
    """
    enrichment = entry.get("enrichment") if isinstance(entry.get("enrichment"), dict) else {}

    # Prefer a single verified example with English scaffolding.
    single = enrichment.get("example") or entry.get("example")
    if isinstance(single, dict):
        uk = single.get("uk") or single.get("sentence") or single.get("text")
        en = single.get("en") or single.get("translation") or single.get("gloss")
        if _has_text(uk):
            return (str(uk).strip(), str(en).strip() if _has_text(en) else None)

    # Fall back to an array of examples.
    examples = enrichment.get("examples") or entry.get("examples") or []
    if isinstance(examples, list) and examples:
        first = examples[0]
        if isinstance(first, dict):
            uk = first.get("uk") or first.get("sentence") or first.get("text")
            en = first.get("en") or first.get("translation") or first.get("gloss")
            if _has_text(uk):
                return (str(uk).strip(), str(en).strip() if _has_text(en) else None)
        if _has_text(first):
            return (str(first).strip(), None)

    return (None, None)


def load_sentence_inventory(path: Path | None) -> dict[str, dict[str, Any]]:
    """Load the public, provenance-bearing sentence inventory by lemma.

    This is intentionally a sibling artifact rather than a cloze-source entry:
    daily examples have no blanked form or case-rule contract.
    """
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows", []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        raise ValueError("sentence inventory rows must be a list")
    inventory: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        lemma = row.get("lemma")
        sentence = row.get("sentence")
        provenance = row.get("provenance")
        license_info = row.get("license")
        if _has_text(lemma) and _has_text(sentence) and isinstance(provenance, dict) and isinstance(license_info, dict):
            inventory[str(lemma)] = row
    return inventory


def _pool_item(
    entry: dict[str, Any], sentence_inventory: dict[str, dict[str, Any]] | None = None
) -> dict[str, Any] | None:
    lemma = entry.get("lemma")
    slug = entry.get("url_slug")
    if not _has_text(lemma) or not _has_text(slug):
        return None

    gloss = entry.get("gloss")
    item: dict[str, Any] = {
        "lemma": lemma,
        "slug": slug,
        "gloss": gloss if isinstance(gloss, str) else None,
        "k": kind_for_source(entry.get("primary_source")),
        "weight": compute_weight(entry),
    }
    lesson_tag = _first_course_track(entry)
    if lesson_tag is not None:
        item["lessonTag"] = lesson_tag
    cefr = _early_cefr(entry)
    if cefr is not None:
        item["cefr"] = cefr
    example, example_en = _first_example(entry)
    inventory_row = (sentence_inventory or {}).get(str(lemma))
    if inventory_row is not None:
        example = str(inventory_row["sentence"]).strip()
    if example is not None:
        item["example"] = example
    if example_en is not None:
        item["exampleEn"] = example_en
    if inventory_row is not None:
        item["exampleProvenance"] = inventory_row["provenance"]
        item["exampleLicense"] = inventory_row["license"]
    return item


def build_pool(
    entries: list[dict[str, Any]], size: int = 300, sentence_inventory: dict[str, dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    """Build the daily pool and return lemma-sorted JSON rows.

    Selection is deterministic but *representative*: within a weight tier we order by a
    stable lemma hash, not by lemma, so a dominant tier (course + early-CEFR words) does not
    collapse the pool to an alphabetical prefix. The small surzhyk-to-avoid set is reserved
    so the "avoid this form" tier always surfaces in the rotation.
    """
    if size < 0:
        raise ValueError("size must be non-negative")

    eligible = [entry for entry in entries if _is_eligible(entry)]
    surzhyk = [e for e in eligible if e.get("primary_source") == _SURZHYK_SOURCE]
    rest = [e for e in eligible if e.get("primary_source") != _SURZHYK_SOURCE]
    rest.sort(key=lambda e: (-compute_weight(e), _stable_hash(e["lemma"])))

    ordered = surzhyk + rest
    selected = [item for entry in ordered[:size] if (item := _pool_item(entry, sentence_inventory)) is not None]
    return sorted(selected, key=lambda item: item["lemma"])


def write_pool(pool: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(pool, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_db_entries(db_path: Path) -> list[dict[str, Any]]:
    """Load daily-pool candidate entries from the entry-model SSOT (``atlas.db``).

    Only approved, public *article* payloads are returned — the same rows the
    entry-model gates count as reviewed entries. ``form_of`` alias routes have no
    ``articles`` row, so the join structurally excludes them (they are search
    resolvers, never Word-of-the-Day candidates). Each ``article_payloads`` row
    stores the manifest-shaped public payload, so ``build_pool`` runs unchanged.
    """
    conn = sqlite3.connect(db_path)
    try:
        # Fail loudly on a stale/hand-edited DB before selecting candidates —
        # the same count/target gates the search-artifact builder runs (#4385 §CI).
        _site_build_entry_model_gates(conn)
        rows = conn.execute(
            """SELECT payload.payload_json
               FROM article_payloads AS payload
               JOIN articles AS article ON article.slug = payload.slug
               WHERE payload.is_public_route = 1
                 AND article.review_state = 'approved'
                 AND article.visibility = 'public'
               ORDER BY payload.route_order"""
        ).fetchall()
    finally:
        conn.close()
    return [json.loads(row[0]) for row in rows]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--db",
        type=Path,
        help="Build the daily pool from atlas.db (entry-model SSOT) instead of the legacy manifest.",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--sentence-inventory", type=Path, default=DEFAULT_SENTENCE_INVENTORY)
    parser.add_argument("--size", type=int, default=300)
    args = parser.parse_args(argv)

    if args.db is not None:
        entries = load_db_entries(args.db)
    else:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        entries = manifest.get("entries", [])
        if not isinstance(entries, list):
            raise ValueError("manifest entries must be a list")
    pool = build_pool(entries, args.size, load_sentence_inventory(args.sentence_inventory))
    write_pool(pool, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
