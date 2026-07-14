#!/usr/bin/env python3
"""Check static Word of the Day and practice assets.

The public practice page must work without backend/API/DB services. This audit
validates the hydrated static files that page fetches: the daily pool and the
per-level practice index, lexeme, and cloze shards.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = PROJECT_ROOT / "scripts" / "audit"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(AUDIT_DIR) not in sys.path:
    sys.path.insert(0, str(AUDIT_DIR))

from generate_practice_deck import (
    THIN_WARN_THRESHOLDS,
    validate_classify_item,
    validate_classify_session_cap,
    validate_heritage_item,
    validate_paradigm_item,
    validate_synonym_item,
)

from scripts.practice_deck.io import ensure_practice_deck_hydrated

DEFAULT_DAILY_POOL = Path("site/src/data/lexicon-daily-pool.json")
DEFAULT_PRACTICE_DIR = Path("site/public/lexicon")
DEFAULT_REVIEWED_SOURCES = Path("site/src/data/lexicon-practice-reviewed-sources.json")
DEFAULT_LEVELS = ("A1", "A2", "B1", "B2", "C1")
DAILY_CEFR_LEVELS = {"A1", "A2", "B1"}
# Must mirror PRACTICE_MODES in site/src/lib/lexicon/srs.ts (spec v5 §9 union;
# the check flags asset modes OUTSIDE this set, so listing not-yet-shipped
# modes is safe — decks for them simply don't exist yet).
PRACTICE_MODES = {
    "flashcards",
    "matching",
    "choice",
    "cloze",
    "paradigm",
    "stress",
    "heritage",
    "synonym",
    "classify",
    "paronym",
}
EXPECTED_SCHEMAS = {
    "index": "atlas-practice-index",
    "lexemes": "atlas-practice-lexemes",
    "cloze": "atlas-practice-cloze",
    "stress": "atlas-practice-stress",
    "classify": "atlas-practice-classify",
    "paradigm": "atlas-practice-paradigm",
    "synonym": "atlas-practice-synonym",
    "heritage": "atlas-practice-heritage",
    "paronym": "atlas-practice-paronym",
}
MODE_BODY_KEYS = {
    "cloze": "cloze",
    "stress": "stress",
    "classify": "classify",
    "paradigm": "paradigm",
    "synonym": "synonym",
    "heritage": "heritage",
    "paronym": "paronym",
}
DRILL_MODES = ("stress", "classify", "paradigm", "synonym", "heritage", "paronym")
MODE_SHARD_KINDS = ("cloze", *DRILL_MODES)


def _read_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{path}: missing")
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}")
    return None


def _has_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_scalar(value: object) -> bool:
    return isinstance(value, int) or _has_text(value)


def _is_tatoeba_provenance(provenance: object) -> bool:
    if not isinstance(provenance, dict):
        return False
    status = str(provenance.get("status") or "").strip()
    source_path = str(provenance.get("path") or "").strip()
    return status == "tatoeba" or source_path.startswith("tatoeba:")


def _check_tatoeba_attribution(
    prefix: str,
    item: dict[str, Any],
    provenance: dict[str, Any],
    errors: list[str],
) -> None:
    if not _is_tatoeba_provenance(provenance):
        return
    source_path = str(provenance.get("path") or "").strip()
    path_sentence_id = source_path.removeprefix("tatoeba:") if source_path.startswith("tatoeba:") else ""
    for field in ("license", "author", "enSentenceId", "enAuthor", "enLicense"):
        if not _has_scalar(provenance.get(field)):
            errors.append(f"{prefix} Tatoeba provenance missing {field}")
    if not _has_scalar(provenance.get("sentenceId")) and not path_sentence_id:
        errors.append(f"{prefix} Tatoeba provenance missing sentenceId")
    attribution = item.get("attribution")
    if not isinstance(attribution, dict):
        errors.append(f"{prefix} missing Tatoeba attribution")
        return
    if attribution.get("source") != "Tatoeba":
        errors.append(f"{prefix} Tatoeba attribution source must be Tatoeba")
    for key, label in (("uk", "Ukrainian"), ("en", "English")):
        sentence = attribution.get(key)
        if not isinstance(sentence, dict):
            errors.append(f"{prefix} missing {label} Tatoeba attribution")
            continue
        for field in ("sentenceId", "author", "license"):
            if not _has_scalar(sentence.get(field)):
                errors.append(f"{prefix} missing {label} Tatoeba attribution {field}")
    uk = attribution.get("uk") if isinstance(attribution, dict) else None
    if path_sentence_id and isinstance(uk, dict) and str(uk.get("sentenceId") or "").strip() != path_sentence_id:
        errors.append(f"{prefix} Tatoeba attribution sentenceId does not match provenance path")


def _reviewed_source_keys(path: Path, errors: list[str]) -> set[tuple[str, str]]:
    payload = _read_json(path, errors)
    rows = payload.get("reviewed") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        errors.append(f"{path}: reviewed sources must be a list or an object with a reviewed list")
        return set()

    reviewed: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        if isinstance(row, str):
            if _has_text(row):
                reviewed.add(("reviewed", row.strip()))
            else:
                errors.append(f"{path}: reviewed[{index}] is empty")
        elif isinstance(row, dict):
            status = str(row.get("status") or "reviewed").strip()
            source_path = str(row.get("path") or "").strip()
            if not source_path:
                errors.append(f"{path}: reviewed[{index}] missing path")
                continue
            reviewed.add((status, source_path))
        else:
            errors.append(f"{path}: reviewed[{index}] must be string or object")
    return reviewed


def _check_daily_pool(path: Path, min_size: int, errors: list[str]) -> dict[str, Any]:
    payload = _read_json(path, errors)
    if not isinstance(payload, list):
        errors.append(f"{path}: daily pool must be a list")
        return {"count": 0, "by_cefr": {}, "by_kind": {}}

    if len(payload) < min_size:
        errors.append(f"{path}: daily pool has {len(payload)} entries, expected at least {min_size}")

    slugs: set[str] = set()
    by_cefr: Counter[str] = Counter()
    by_kind: Counter[str] = Counter()
    for index, item in enumerate(payload):
        prefix = f"{path}: item[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue

        lemma = item.get("lemma")
        slug = item.get("slug")
        gloss = item.get("gloss")
        kind = item.get("k")
        cefr = item.get("cefr")
        if not _has_text(lemma):
            errors.append(f"{prefix} missing lemma")
        if not _has_text(slug):
            errors.append(f"{prefix} missing slug")
        elif slug in slugs:
            errors.append(f"{prefix} duplicate slug {slug!r}")
        else:
            slugs.add(slug)
        if not _has_text(gloss):
            errors.append(f"{prefix} missing learner gloss")
        if not _has_text(kind):
            errors.append(f"{prefix} missing source kind k")
        else:
            by_kind[str(kind)] += 1

        if _has_text(cefr):
            by_cefr[str(cefr)] += 1
        elif kind != "avoid":
            errors.append(f"{prefix} missing CEFR for non-avoid daily word")

        if _has_text(cefr) and cefr not in DAILY_CEFR_LEVELS:
            errors.append(f"{prefix} CEFR {cefr!r} outside daily levels {sorted(DAILY_CEFR_LEVELS)}")
        if kind == "avoid" and isinstance(gloss, str) and not gloss.casefold().startswith("avoid:"):
            errors.append(f"{prefix} avoid item gloss must start with 'avoid:'")

    return {
        "count": len(payload),
        "by_cefr": dict(by_cefr.most_common()),
        "by_kind": dict(by_kind.most_common()),
    }


def _size_budget_ok(path: Path, payload: dict[str, Any], errors: list[str]) -> None:
    size_budget = payload.get("sizeBudget")
    if not isinstance(size_budget, dict):
        errors.append(f"{path}: missing sizeBudget")
        return
    if size_budget.get("ok") is not True:
        errors.append(f"{path}: sizeBudget.ok is not true")
    for used_key, limit_key in (("rawBytes", "rawLimitBytes"), ("gzipBytes", "gzipLimitBytes")):
        used = size_budget.get(used_key)
        limit = size_budget.get(limit_key)
        if not isinstance(used, int) or not isinstance(limit, int):
            errors.append(f"{path}: sizeBudget missing integer {used_key}/{limit_key}")
        elif used > limit:
            errors.append(f"{path}: {used_key} {used} exceeds {limit_key} {limit}")


def _check_shard_meta(path: Path, payload: Any, *, level: str, kind: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        errors.append(f"{path}: shard must be an object")
        return {}

    expected_schema = EXPECTED_SCHEMAS[kind]
    if payload.get("schema") != expected_schema:
        errors.append(f"{path}: schema {payload.get('schema')!r} != {expected_schema!r}")
    if payload.get("schemaVersion") != 1:
        errors.append(f"{path}: schemaVersion must be 1")
    if payload.get("level") != level:
        errors.append(f"{path}: level {payload.get('level')!r} != {level!r}")
    if not _has_text(payload.get("deckVersion")):
        errors.append(f"{path}: missing deckVersion")
    _size_budget_ok(path, payload, errors)
    return payload


def _check_cloze_item(
    path: Path,
    item: Any,
    *,
    index: int,
    level: str,
    lexeme_ids: set[str],
    index_cloze_ids: set[str],
    reviewed: set[tuple[str, str]],
    errors: list[str],
) -> None:
    prefix = f"{path}: cloze[{index}]"
    if not isinstance(item, dict):
        errors.append(f"{prefix} must be an object")
        return

    cloze_id = item.get("clozeId")
    lemma_id = item.get("lemmaId")
    sentence = item.get("sentence")
    form = item.get("form")
    if not _has_text(cloze_id):
        errors.append(f"{prefix} missing clozeId")
    elif cloze_id not in index_cloze_ids:
        errors.append(f"{prefix} {cloze_id!r} not referenced by {level} index shard")
    if not _has_text(lemma_id):
        errors.append(f"{prefix} missing lemmaId")
    elif lemma_id not in lexeme_ids:
        errors.append(f"{prefix} lemmaId {lemma_id!r} missing from {level} lexeme shard")
    if not (_has_text(sentence) and "___" in sentence):
        errors.append(f"{prefix} sentence must contain ___ blank")
    if not _has_text(form):
        errors.append(f"{prefix} missing target form")
    if not isinstance(item.get("caseRule"), dict):
        errors.append(f"{prefix} missing caseRule")

    options = item.get("options")
    if not isinstance(options, list) or len(options) < 4:
        errors.append(f"{prefix} must have at least 4 options")
    else:
        answer_count = sum(1 for option in options if isinstance(option, dict) and option.get("kind") == "answer")
        if answer_count != 1:
            errors.append(f"{prefix} must have exactly one answer option")

    provenance = item.get("provenance")
    status = provenance.get("status") if isinstance(provenance, dict) else None
    source_path = provenance.get("path") if isinstance(provenance, dict) else None
    key = (str(status or "").strip(), str(source_path or "").strip())
    if key not in reviewed:
        errors.append(f"{prefix} provenance {key!r} is not in reviewed source allowlist")
    if isinstance(provenance, dict):
        _check_tatoeba_attribution(prefix, item, provenance, errors)


def _check_level(
    practice_dir: Path,
    level: str,
    min_lexemes: int,
    reviewed: set[tuple[str, str]],
    errors: list[str],
    warnings: list[str],
    *,
    lower_lexeme_ids: set[str] | None = None,
) -> dict[str, Any]:
    paths = {
        "index": practice_dir / f"practice-index.{level}.json",
        "lexemes": practice_dir / f"practice-lexemes.{level}.json",
        **{
            kind: practice_dir / f"practice-{kind}.{level}.json"
            for kind in MODE_SHARD_KINDS
        },
    }
    shards = {
        kind: _check_shard_meta(
            path,
            _read_json(path, errors),
            level=level,
            kind=kind,
            errors=errors,
        )
        for kind, path in paths.items()
    }

    index_items = shards["index"].get("items")
    lexemes = shards["lexemes"].get("lexemes")
    cloze_items = shards["cloze"].get("cloze")
    mode_items = {
        kind: shards[kind].get(MODE_BODY_KEYS[kind])
        for kind in DRILL_MODES
    }
    if not isinstance(index_items, list):
        errors.append(f"{paths['index']}: items must be a list")
        index_items = []
    if not isinstance(lexemes, list):
        errors.append(f"{paths['lexemes']}: lexemes must be a list")
        lexemes = []
    if not isinstance(cloze_items, list):
        errors.append(f"{paths['cloze']}: cloze must be a list")
        cloze_items = []
    for kind in DRILL_MODES:
        if not isinstance(mode_items[kind], list):
            errors.append(f"{paths[kind]}: {MODE_BODY_KEYS[kind]} must be a list")
            mode_items[kind] = []

    if len(index_items) < min_lexemes:
        errors.append(f"{paths['index']}: {len(index_items)} items, expected at least {min_lexemes}")
    if len(lexemes) < min_lexemes:
        errors.append(f"{paths['lexemes']}: {len(lexemes)} lexemes, expected at least {min_lexemes}")

    versions = {str(shard.get("deckVersion")) for shard in shards.values() if shard.get("deckVersion")}
    if len(versions) > 1:
        errors.append(f"{practice_dir}: {level} shard deckVersion mismatch: {sorted(versions)}")

    lexeme_by_id = {str(item.get("lemmaId")): item for item in lexemes if isinstance(item, dict)}
    if len(lexeme_by_id) != len(lexemes):
        errors.append(f"{paths['lexemes']}: duplicate or invalid lemmaId values")

    index_cloze_ids: set[str] = set()
    for index, item in enumerate(index_items):
        prefix = f"{paths['index']}: items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        lemma_id = item.get("lemmaId")
        if not _has_text(lemma_id):
            errors.append(f"{prefix} missing lemmaId")
        elif str(lemma_id) not in lexeme_by_id:
            errors.append(f"{prefix} lemmaId {lemma_id!r} missing from lexeme shard")
        if item.get("cefr") != level:
            errors.append(f"{prefix} cefr {item.get('cefr')!r} != {level!r}")
        modes = item.get("modes")
        if not isinstance(modes, list) or "flashcards" not in modes:
            errors.append(f"{prefix} modes must include flashcards")
            modes = modes if isinstance(modes, list) else []
        unknown_modes = sorted({mode for mode in modes if mode not in PRACTICE_MODES})
        if unknown_modes:
            errors.append(f"{prefix} unknown modes: {unknown_modes}")
        cloze_ids = item.get("clozeIds")
        if not isinstance(cloze_ids, list):
            errors.append(f"{prefix} clozeIds must be a list")
            cloze_ids = []
        index_cloze_ids.update(str(cloze_id) for cloze_id in cloze_ids if _has_text(cloze_id))
        has_cloze = bool(cloze_ids)
        if item.get("hasCloze") is not has_cloze:
            errors.append(f"{prefix} hasCloze does not match clozeIds")
        if ("cloze" in modes) != has_cloze:
            errors.append(f"{prefix} cloze mode does not match clozeIds")

    for index, lexeme in enumerate(lexemes):
        prefix = f"{paths['lexemes']}: lexemes[{index}]"
        if not isinstance(lexeme, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("lemmaId", "lemma", "lemmaPlain", "gloss"):
            if not _has_text(lexeme.get(field)):
                errors.append(f"{prefix} missing {field}")
        if lexeme.get("cefr") != level:
            errors.append(f"{prefix} cefr {lexeme.get('cefr')!r} != {level!r}")

    for index, item in enumerate(cloze_items):
        _check_cloze_item(
            paths["cloze"],
            item,
            index=index,
            level=level,
            lexeme_ids=set(lexeme_by_id),
            index_cloze_ids=index_cloze_ids,
            reviewed=reviewed,
            errors=errors,
        )
    for kind, rows in mode_items.items():
        assert isinstance(rows, list)
        for index, item in enumerate(rows):
            prefix = f"{paths[kind]}: {MODE_BODY_KEYS[kind]}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            lemma_id = item.get("lemmaId")
            if not _has_text(lemma_id):
                errors.append(f"{prefix} missing lemmaId")
            elif str(lemma_id) not in lexeme_by_id:
                # Heritage items sit at max(lexeme cefr, curator availability floor)
                # (#4719/#4720), so their native lexeme may live in a LOWER-level
                # shard. The static client loads lexeme shards cumulatively, keeping
                # that join resolvable (generate_practice_deck.py, heritage placement
                # note) — mirror that here for heritage ONLY; all other drill kinds
                # remain strictly same-level.
                if kind == "heritage" and str(lemma_id) in (lower_lexeme_ids or set()):
                    pass
                elif kind == "heritage":
                    errors.append(
                        f"{prefix} lemmaId {lemma_id!r} missing from lexeme shards at or below {level}"
                    )
                else:
                    errors.append(f"{prefix} lemmaId {lemma_id!r} missing from {level} lexeme shard")
        if kind == "classify":
            classify_rows = [item for item in rows if isinstance(item, dict)]
            for index, item in enumerate(classify_rows):
                errors.extend(
                    f"{paths[kind]}: classify[{index}] {error}"
                    for error in validate_classify_item(item)
                )
            errors.extend(f"{paths[kind]}: {error}" for error in validate_classify_session_cap(classify_rows))
        elif kind == "synonym":
            for index, item in enumerate(item for item in rows if isinstance(item, dict)):
                errors.extend(
                    f"{paths[kind]}: synonym[{index}] {error}"
                    for error in validate_synonym_item(item)
                )
        elif kind == "heritage":
            for index, item in enumerate(item for item in rows if isinstance(item, dict)):
                errors.extend(
                    f"{paths[kind]}: heritage[{index}] {error}"
                    for error in validate_heritage_item(item)
                )
        elif kind == "paradigm":
            for index, item in enumerate(item for item in rows if isinstance(item, dict)):
                errors.extend(
                    f"{paths[kind]}: paradigm[{index}] {error}"
                    for error in validate_paradigm_item(item)
                )

    counts = shards["index"].get("counts")
    if not isinstance(counts, dict):
        errors.append(f"{paths['index']}: missing counts")
        counts = {}
    expected_cloze_lexemes = len({item.get("lemmaId") for item in cloze_items if isinstance(item, dict)})
    expected_coverage = round(expected_cloze_lexemes / len(lexemes), 4) if lexemes else 0.0
    expected_counts = {
        "lexemes": len(lexemes),
        "cloze": len(cloze_items),
        "clozeEligibleLexemes": expected_cloze_lexemes,
        "clozeCoverage": expected_coverage,
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            errors.append(f"{paths['index']}: counts.{key} {counts.get(key)!r} != {expected!r}")
    mode_counts = counts.get("modeCounts")
    mode_coverage = counts.get("modeCoverage")
    if not isinstance(mode_counts, dict):
        errors.append(f"{paths['index']}: missing counts.modeCounts")
        mode_counts = {}
    if not isinstance(mode_coverage, dict):
        errors.append(f"{paths['index']}: missing counts.modeCoverage")
        mode_coverage = {}
    for kind in MODE_SHARD_KINDS:
        rows = cloze_items if kind == "cloze" else mode_items[kind]
        assert isinstance(rows, list)
        expected_count = len(rows)
        expected_mode_coverage = (
            round(len({item.get("lemmaId") for item in rows if isinstance(item, dict)}) / len(lexemes), 4)
            if lexemes
            else 0.0
        )
        if mode_counts.get(kind) != expected_count:
            errors.append(f"{paths['index']}: counts.modeCounts.{kind} {mode_counts.get(kind)!r} != {expected_count!r}")
        if mode_coverage.get(kind) != expected_mode_coverage:
            errors.append(
                f"{paths['index']}: counts.modeCoverage.{kind} "
                f"{mode_coverage.get(kind)!r} != {expected_mode_coverage!r}"
            )

    if isinstance(mode_coverage, dict):
        for mode, threshold in THIN_WARN_THRESHOLDS.items():
            cov = mode_coverage.get(mode, 0.0)
            if cov < threshold:
                warnings.append(
                    f"{level} {mode} coverage {cov:.4f} is below thin-deck threshold {threshold:.2f}"
                )

    return {
        "index": len(index_items),
        "lexemes": len(lexemes),
        "cloze": len(cloze_items),
        **{kind: len(rows) for kind, rows in mode_items.items() if isinstance(rows, list)},
        "deck_versions": sorted(versions),
        "lexeme_ids": frozenset(lexeme_by_id),
    }


def check_assets(
    *,
    daily_pool: Path = DEFAULT_DAILY_POOL,
    practice_dir: Path = DEFAULT_PRACTICE_DIR,
    reviewed_sources: Path = DEFAULT_REVIEWED_SOURCES,
    levels: tuple[str, ...] = DEFAULT_LEVELS,
    min_daily_pool_size: int = 250,
    min_practice_lexemes_per_level: int = 25,
) -> dict[str, Any]:
    if practice_dir == DEFAULT_PRACTICE_DIR:
        ensure_practice_deck_hydrated(practice_dir)

    errors: list[str] = []
    warnings: list[str] = []
    daily = _check_daily_pool(daily_pool, min_daily_pool_size, errors)
    reviewed = _reviewed_source_keys(reviewed_sources, errors)
    practice: dict[str, dict[str, Any]] = {}
    # Levels are ordered (A1..C1); heritage items may reference native lexemes from
    # any LOWER level (availability floor, #4720) — accumulate ids as we ascend.
    seen_lexeme_ids: set[str] = set()
    for level in levels:
        row = _check_level(
            practice_dir,
            level,
            min_practice_lexemes_per_level,
            reviewed,
            errors,
            warnings,
            lower_lexeme_ids=seen_lexeme_ids,
        )
        seen_lexeme_ids |= set(row.pop("lexeme_ids", None) or ())
        practice[level] = row

    deck_versions = {
        version
        for row in practice.values()
        for version in row.get("deck_versions", [])
        if version
    }
    if len(deck_versions) > 1:
        errors.append(f"{practice_dir}: cross-level deckVersion mismatch: {sorted(deck_versions)}")

    total_cloze = sum(int(row["cloze"]) for row in practice.values())
    if total_cloze and not reviewed:
        errors.append(f"{reviewed_sources}: cloze shards are nonempty but reviewed allowlist is empty")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "daily": daily,
        "practice": practice,
        "reviewed_sources": len(reviewed),
        "total_cloze": total_cloze,
        "deck_versions": sorted(deck_versions),
    }


def _parse_levels(raw: str) -> tuple[str, ...]:
    levels = tuple(level.strip().upper() for level in raw.split(",") if level.strip())
    if not levels:
        raise argparse.ArgumentTypeError("levels must contain at least one CEFR level")
    return levels


def _print_summary(summary: dict[str, Any]) -> None:
    print(
        "Static practice assets: "
        f"{summary['daily']['count']} daily words, "
        f"{sum(row['lexemes'] for row in summary['practice'].values())} practice lexemes, "
        f"{summary['total_cloze']} cloze items."
    )
    print(f"Deck versions: {', '.join(summary['deck_versions']) or 'none'}")
    print(f"Reviewed cloze source allowlist rows: {summary['reviewed_sources']}")
    for level, row in summary["practice"].items():
        mode_counts = " ".join(f"{mode}={row.get(mode, 0)}" for mode in DRILL_MODES)
        print(
            f"  {level}: index={row['index']} lexemes={row['lexemes']} "
            f"cloze={row['cloze']} {mode_counts}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--daily-pool", type=Path, default=DEFAULT_DAILY_POOL)
    parser.add_argument("--practice-dir", type=Path, default=DEFAULT_PRACTICE_DIR)
    parser.add_argument("--reviewed-sources", type=Path, default=DEFAULT_REVIEWED_SOURCES)
    parser.add_argument("--levels", type=_parse_levels, default=DEFAULT_LEVELS)
    parser.add_argument("--min-daily-pool-size", type=int, default=250)
    parser.add_argument("--min-practice-lexemes-per-level", type=int, default=25)
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    args = parser.parse_args(argv)

    summary = check_assets(
        daily_pool=args.daily_pool,
        practice_dir=args.practice_dir,
        reviewed_sources=args.reviewed_sources,
        levels=args.levels,
        min_daily_pool_size=args.min_daily_pool_size,
        min_practice_lexemes_per_level=args.min_practice_lexemes_per_level,
    )

    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        _print_summary(summary)
        if summary["warnings"]:
            print("Static practice asset warnings:", file=sys.stderr)
            for warning in summary["warnings"]:
                print(f"- {warning}", file=sys.stderr)
        if summary["errors"]:
            print("Static practice asset gate failed:")
            for error in summary["errors"]:
                print(f"- {error}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
