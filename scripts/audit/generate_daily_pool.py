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
import re
import sqlite3
from pathlib import Path
from typing import Any

from scripts.audit.daily_cefr import CEFR_LEVEL_ORDER, CEFR_LEVELS
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
# Minimum slots reserved per known CEFR level that has enough eligible words. Keeps
# the daily 12-card draw comfortably above zero for every tab while leaving the
# majority of slots for the beginner-friendly weighted fill.
MIN_PER_LEVEL = 40
# Derived-form + surzhyk source tags live in scripts.audit.lexeme_filter (single source
# of truth, shared with the search index, word-page routes, and the practice deck).
# Keep the underscore-prefixed aliases for the existing references in this module.
_DERIVED_FORM_SOURCES = DERIVED_FORM_SOURCES
_SURZHYK_SOURCE = SURZHYK_SOURCE

_LATIN_RE = re.compile(r"[A-Za-z]")

# Verified English translations for lemmas that lack bilingual glosses in upstream
# sources or where upstream fallback contains raw monolingual Ukrainian dictionary
# definitions from СУМ/ВТС (#8258).
VERIFIED_ENGLISH_GLOSSES: dict[str, str] = {
    "аналогічно": "similarly, likewise",
    "архаїка": "antiquity, archaism, archaic elements",
    "безкоштовний": "free of charge, complimentary",
    "біб": "broad bean, fava bean",
    "використовувати": "to use, to utilize, to employ",
    "відстань": "distance, gap",
    "відчуття": "feeling, sensation, perception",
    "двигун": "engine, motor",
    "дівчина": "girl, young woman",
    "етнічність": "ethnicity, ethnic identity",
    "захист": "defense, protection",
    "клавіатура": "keyboard",
    "контролювати": "to control, to monitor, to supervise",
    "м'яз": "muscle",
    "мох": "moss",
    "овес": "oats, oat",
    "ом": "ohm (unit of electrical resistance)",
    "продавати": "to sell",
    "простір": "space, expanse",
    "рости": "to grow, to increase",
    "сад": "garden, orchard",
    "свідомість": "consciousness, awareness",
    "спостереження": "observation, monitoring",
    "судома": "cramp, spasm, convulsion",
    "сума": "sum, total, amount",
    "умовний": "conventional, conditional, symbolic",
    "цвісти": "to bloom, to blossom, to flower",
    "цунамі": "tsunami",
    "шум": "noise, sound, rustle",
}

# Verified English translations for daily example sentences lacking an English gloss (#8258).
VERIFIED_EXAMPLE_EN: dict[str, str] = {
    "аналогічно": "Similarly, in this same record of the Salary field we will select the Sum function.",
    "безкоштовний": "Usually, a company providing free hosting earns money by displaying ads on pages hosted on it.",
    "біб": "At the same time, the authorized archon took out of the boxes a bean and a tablet with the candidate's name.",
    "відстань": "What will the distance between them be after 35 minutes?",
    "відчуття": "Because of this, serotonin and dopamine accumulate in the synaptic cleft, causing a sensation of pleasure.",
    "двигун": "A heat engine is a machine that operates cyclically and converts fuel energy into mechanical energy.",
    "захист": "One of the most important tasks of the state is the protection of the rights of all people, including teenagers.",
    "клавіатура": "Thus, the keyboard converts the notification of a particular key press into a set of electrical signals.",
    "контролювати": "Monitor for the onset of vomiting.",
    "м'яз": "Which muscle must contract for the shin to move in the direction shown by the arrow?",
    "мох": "Verbynka carefully lifted the moss.",
    "овес": "Green rye and oats too — here our whole kin has gathered.",
    "ом": "The total resistance of two lamps and a rheostat connected in series is 65 ohms.",
    "простір": "What personal space is and what its components are.",
    "свідомість": "Consciousness: the desire to know oneself is one of the main drivers of human development.",
    "спостереження": "A radiation and chemical observation post is set up on the facility's grounds near the control center.",
    "сума": "How many terms of this progression need to be taken so that their sum equals 253?",
    "умовний": "Therefore, scholars made a conventional division of history into periods — the periodization of history.",
    "цвісти": "To bloom like this, to grow like this, to marry thus and walk ahead, without quarreling on the arduous road...",
    "цунамі": "Tsunamis encompass the entire depth of water masses and move across the ocean.",
    "шум": "In ancient times, the word 'shum' also referred to the forest.",
}


def _entry_gloss(entry: dict[str, Any]) -> str | None:
    """Return a verified English gloss for a daily-pool candidate entry.

    If an entry's upstream gloss is a raw monolingual Ukrainian definition from
    СУМ/ВТС (lacking Latin/English text), it is rejected unless covered by
    VERIFIED_ENGLISH_GLOSSES (#8258).
    """
    lemma = entry.get("lemma")
    if isinstance(lemma, str) and lemma in VERIFIED_ENGLISH_GLOSSES:
        return VERIFIED_ENGLISH_GLOSSES[lemma]
    gloss = entry.get("gloss")
    if not isinstance(gloss, str) or not gloss.strip():
        return None
    if not _LATIN_RE.search(gloss):
        return None
    return gloss.strip()


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


_MAX_ORIGIN_LENGTH = 160

# Matches a parenthetical that contains Latin-script characters (transliteration
# or English gloss). Tolerates one level of nested parentheses.
_LATIN_PARENTHETICAL_RE = re.compile(r"\((?:[^()]|\([^()]*\))*[A-Za-z](?:[^()]|\([^()]*\))*\)")
# Imperial comparison clauses that Kaikki sometimes appends.
# Keep the sentence's own period before the clause; only drop the clause itself.
_COMPARE_CLAUSE_RE = re.compile(r"(?:\s*,\s*)?\b[Cc]ompare\s+[A-Z][a-z]+[^.]*\.?")
# Source/license fragments that should never become prose.
_SOURCE_FRAGMENT_RE = re.compile(r"\bkaikki/Wiktionary\b|\(CC BY-SA[^)]*\)")
# Internal mphdict/ESUM labels are not learner-facing etymology.
_ESUM_LABEL_RE = re.compile(r"Стаття\s+ЕСУМ|етимонів\s*:", re.IGNORECASE)


def _clean_origin(text: str) -> str | None:
    """Clean a raw Kaikki/Wiktionary etymology string for the daily pool.

    Fails closed: returns ``None`` for empty/garbage input or internal labels.
    """
    collapsed = " ".join(text.split())
    if not collapsed or not any(c.isalpha() for c in collapsed):
        return None

    cleaned = _LATIN_PARENTHETICAL_RE.sub("", collapsed)
    cleaned = _COMPARE_CLAUSE_RE.sub("", cleaned)
    cleaned = _SOURCE_FRAGMENT_RE.sub("", cleaned)
    cleaned = " ".join(cleaned.split())
    # Pull stray punctuation back against the preceding word instead of deleting it.
    cleaned = re.sub(r"\s+([.,])", r"\1", cleaned).strip()

    if not cleaned or not any(c.isalpha() for c in cleaned):
        return None
    if _ESUM_LABEL_RE.search(cleaned):
        return None

    cleaned = cleaned[0].upper() + cleaned[1:]
    if len(cleaned) <= _MAX_ORIGIN_LENGTH:
        return cleaned
    breakpoint = cleaned.rfind(" ", 0, _MAX_ORIGIN_LENGTH)
    end = breakpoint if breakpoint > 0 else _MAX_ORIGIN_LENGTH
    return cleaned[:end] + "…"


def _first_origin(entry: dict[str, Any]) -> str | None:
    """Return a cleaned Kaikki/Wiktionary origin string for the daily pool, or None."""
    enrichment = entry.get("enrichment") if isinstance(entry.get("enrichment"), dict) else {}
    etymology = enrichment.get("etymology")
    if not isinstance(etymology, dict):
        return None
    raw_text = etymology.get("text")
    if not isinstance(raw_text, str) or not raw_text.strip():
        return None
    source = etymology.get("source", "")
    if not isinstance(source, str) or "Wiktionary" not in source:
        # Only surface Kaikki-sourced origin prose; ESUM has its own pages.
        return None
    return _clean_origin(raw_text)


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


def _cefr_level(entry: dict[str, Any]) -> str | None:
    """Return the entry's true CEFR level (any of A1–C2), or None.

    Unlike :func:`_early_cefr` (which gates the beginner-friendly weight boost to
    A1/A2/B1), this is the level emitted on the pool row and used for level-balanced
    selection. Capping the emitted level to ``EARLY_CEFR`` is what hid every B2/C1/C2
    word and left the WotD C-level tabs pointing at an all-A1/A2/B1 pool (#6728).
    """
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return None
    cefr = enrichment.get("cefr")
    level = cefr.get("level") if isinstance(cefr, dict) else cefr
    return level if isinstance(level, str) and level in CEFR_LEVELS else None


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
    """A daily card needs a real lemma headword and an English translation; drop grammar
    metaterms (via is_lexeme_entry), inflected/normalized duplicates, and avoid-classified
    forms so cards show only learner-safe headwords rather than case forms, grammar labels,
    or error-modeling lemmas."""
    return (
        is_lexeme_entry(entry)
        and _entry_gloss(entry) is not None
        and entry.get("primary_source") not in _DERIVED_FORM_SOURCES
        and entry.get("primary_source") != _SURZHYK_SOURCE
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
    gloss = _entry_gloss(entry)
    if not _has_text(lemma) or not _has_text(slug) or gloss is None:
        return None

    item: dict[str, Any] = {
        "lemma": lemma,
        "slug": slug,
        "gloss": gloss,
        "k": kind_for_source(entry.get("primary_source")),
        "weight": compute_weight(entry),
    }
    lesson_tag = _first_course_track(entry)
    if lesson_tag is not None:
        item["lessonTag"] = lesson_tag
    cefr = _cefr_level(entry)
    if cefr is not None:
        item["cefr"] = cefr
    pos = entry.get("pos")
    if _has_text(pos):
        item["pos"] = pos
    example, example_en = _first_example(entry)
    if example_en is None and isinstance(lemma, str) and lemma in VERIFIED_EXAMPLE_EN:
        example_en = VERIFIED_EXAMPLE_EN[lemma]
    inventory_row = (sentence_inventory or {}).get(str(lemma))
    if inventory_row is not None:
        item["example"] = str(inventory_row["sentence"]).strip()
        if example_en is not None:
            item["exampleEn"] = example_en
        item["exampleProvenance"] = inventory_row["provenance"]
        item["exampleLicense"] = inventory_row["license"]
    elif sentence_inventory is None and example is not None:
        item["example"] = example
        if example_en is not None:
            item["exampleEn"] = example_en
    origin = _first_origin(entry)
    if origin is not None:
        item["etymology"] = origin
    return item


def build_pool(
    entries: list[dict[str, Any]],
    size: int = 300,
    sentence_inventory: dict[str, dict[str, Any]] | None = None,
    min_per_level: int = MIN_PER_LEVEL,
) -> list[dict[str, Any]]:
    """Build the daily pool and return lemma-sorted JSON rows.

    Selection is level-balanced: each CEFR level with enough eligible words is
    reserved ``min_per_level`` slots so the WotD level selector's B2/C1/C2 tabs
    point at real level-matched cards, not an A1/A2/B1-only pool (#6728). The
    remaining slots are filled from the deterministic weight tier (course +
    beginner-CEFR bias) with a stable per-lemma hash tiebreak, so a dominant tier
    does not collapse the pool to an alphabetical prefix. Avoid-classified forms
    are excluded before selection, so error-modeling lemmas cannot surface as
    neutral daily cards.
    """
    if size < 0:
        raise ValueError("size must be non-negative")
    if min_per_level < 0:
        raise ValueError("min_per_level must be non-negative")

    eligible = [entry for entry in entries if _is_eligible(entry)]

    def sort_key(entry: dict[str, Any]) -> tuple[int, str]:
        return (-compute_weight(entry), _stable_hash(entry["lemma"]))

    by_level: dict[str, list[dict[str, Any]]] = {level: [] for level in CEFR_LEVEL_ORDER}
    unlevelled: list[dict[str, Any]] = []
    for entry in eligible:
        level = _cefr_level(entry)
        if level is not None:
            by_level[level].append(entry)
        else:
            unlevelled.append(entry)
    for bucket in by_level.values():
        bucket.sort(key=sort_key)
    unlevelled.sort(key=sort_key)

    selected: list[dict[str, Any]] = []
    chosen: set[str] = set()

    def take_from(bucket: list[dict[str, Any]], quota: int) -> None:
        for entry in bucket:
            if len(selected) >= size or quota <= 0:
                return
            lemma = entry["lemma"]
            if lemma in chosen:
                continue
            chosen.add(lemma)
            selected.append(entry)
            quota -= 1

    # 1) Reserve per-level quotas so every WotD tab has real level-matched words.
    for level in CEFR_LEVEL_ORDER:
        take_from(by_level[level], min_per_level)
    # 2) Fill remaining slots from the full weighted pool (beginner-friendly character).
    take_from(sorted(eligible, key=sort_key), size)
    # 3) Last resort: top up from unlevelled entries if still short of `size`.
    take_from(unlevelled, size)

    rows = [item for entry in selected if (item := _pool_item(entry, sentence_inventory)) is not None]
    return sorted(rows, key=lambda item: item["lemma"])


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
