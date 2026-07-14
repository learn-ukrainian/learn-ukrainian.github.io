#!/usr/bin/env python3
"""Fail-closed Anna Ohoiko corpus intake for Word Atlas (#4223 Phase 1).

Enumerates in-scope private Ohoiko source units by opaque ``source_ref``,
extracts Ukrainian lexical candidates without committing raw copyrighted
text, and emits safe inventory + ledger metadata through the shared
``atlas_intake_core`` machinery used by curriculum intake (#4222).

This command never publishes Atlas or learner-surface outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ingest import ohoiko_books_ingest as words_ingest
from scripts.ingest import ohoiko_verbs_ingest as verbs_ingest
from scripts.lexicon import atlas_intake_core as core
from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.content_lexicon_reconciler import (
    PROJECT_ROOT,
    extract_ukrainian_tokens,
    strip_mdx_to_prose,
)
from scripts.lexicon.heritage_classifier import classify_lemma
from scripts.lexicon.lemma_normalization import strip_acute_stress

DEFAULT_PRIVATE_ROOT = PROJECT_ROOT / "docs" / "references" / "private"
DEFAULT_JUNE_NOTES_ROOT = DEFAULT_PRIVATE_ROOT / "ohoiko-june-a1-book" / "notes"
DEFAULT_INVENTORY_OUT = Path("/tmp/atlas-ohoiko-corpus-inventory.json")
DEFAULT_REPORT_OUT = Path("/tmp/atlas-ohoiko-corpus-intake.json")
DEFAULT_INVENTORY_PATH = "data/lexicon/source-inventory/ohoiko-corpus-intake.json"
WORKFLOW_ID = "ohoiko_corpus_atlas_intake.v1"
SOURCE_FAMILY = "ohoiko"

TEXT_SUFFIXES = frozenset({".md", ".txt"})
_VERB_HEADWORD_RE = re.compile(
    r"^([А-ЯҐЄІЇа-яґєії][А-ЯҐЄІЇа-яґєії'ʼ’`′\- ]*?)\s*(?:\||\s{2,})"
)


class OhoikoIntakeError(ValueError):
    """A private Ohoiko source cannot be safely included in intake."""


@dataclass(frozen=True)
class OhoikoBookSource:
    slug: str
    source_id: str
    extraction_mode: str
    filename: str
    parser: str
    source_title: str
    max_entries: int | None = None


@dataclass(frozen=True)
class OhoikoTextSource:
    source_ref: str
    source_id: str
    extraction_mode: str
    source_title: str
    unit_kind: str


@dataclass(frozen=True)
class OhoikoSourceUnit:
    """One safe, opaque source unit for public reporting."""

    source_ref: str
    source_id: str
    source_family: str
    extraction_mode: str
    unit_kind: str
    available: bool


BOOK_CATALOG: tuple[OhoikoBookSource, ...] = (
    OhoikoBookSource(
        slug="1000-words",
        source_id="ohoiko-1000-words-2nd-ed",
        extraction_mode="book_candidate",
        filename="1000-Ukrainian-Words-2.0-Ukrainian-Lessons-PDF-4mwsom.txt",
        parser="numbered_entries",
        source_title="Anna Ohoiko 1000 Most Useful Ukrainian Words (2nd ed)",
        max_entries=1000,
    ),
    OhoikoBookSource(
        slug="500-verbs",
        source_id="ohoiko-500-verbs",
        extraction_mode="book_candidate",
        filename="500+ Ukrainian Verbs - Ukrainian Lessons - PDF.txt",
        parser="verb_pages",
        source_title="Anna Ohoiko 500+ Ukrainian Verbs",
        max_entries=500,
    ),
)

ULP_NOTE_CATALOG: tuple[tuple[str, str, str], ...] = (
    ("ulp-1-00-lesson-notes", "ULP 1-00 Lesson Notes (all in one file) (2023).txt", "ULP Season 1 lesson notes"),
    ("ulp-2-00-lesson-notes", "ULP 2-00 Lesson Notes (all in one file).txt", "ULP Season 2 lesson notes"),
    ("ulp-3-00-lesson-notes", "ULP 3-00 Lesson Notes (all in one file).txt", "ULP Season 3 lesson notes"),
    ("ulp-4-00-lesson-notes", "ULP 4-00 Lesson Notes (all in one file).txt", "ULP Season 4 lesson notes"),
    ("ulp-5-00-lesson-notes", "ULP 5-00 Lesson Notes (all in one file).txt", "ULP Season 5 lesson notes"),
    ("ulp-6-00-lesson-notes", "ULP 6-00 Lesson Notes (all in one file).txt", "ULP Season 6 lesson notes"),
)


def committed_ohoiko_inventory_paths(*, project_root: Path = PROJECT_ROOT) -> list[Path]:
    inventory_dir = project_root / "data" / "lexicon" / "source-inventory"
    return sorted(inventory_dir.glob("ohoiko-*.yaml"))


def discover_source_units(
    *,
    private_root: Path = DEFAULT_PRIVATE_ROOT,
    june_notes_root: Path = DEFAULT_JUNE_NOTES_ROOT,
) -> tuple[OhoikoSourceUnit, ...]:
    """Enumerate every in-scope Ohoiko source unit with opaque locators."""

    units: list[OhoikoSourceUnit] = []
    for index, book in enumerate(BOOK_CATALOG, start=1):
        available = (private_root / book.filename).is_file()
        units.append(
            OhoikoSourceUnit(
                source_ref=f"ohoiko-book-{index:03d}",
                source_id=book.source_id,
                source_family=SOURCE_FAMILY,
                extraction_mode=book.extraction_mode,
                unit_kind=f"book:{book.slug}",
                available=available,
            )
        )
    for index, (source_id, filename, _title) in enumerate(ULP_NOTE_CATALOG, start=1):
        available = (private_root / filename).is_file()
        units.append(
            OhoikoSourceUnit(
                source_ref=f"ohoiko-notes-{index:03d}",
                source_id=source_id,
                source_family=SOURCE_FAMILY,
                extraction_mode="content_token",
                unit_kind="ulp_lesson_notes",
                available=available,
            )
        )
    if june_notes_root.is_dir():
        note_files = sorted(
            path
            for path in june_notes_root.glob("**/*")
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
        )
        for index, _path in enumerate(note_files, start=1):
            units.append(
                OhoikoSourceUnit(
                    source_ref=f"ohoiko-june-note-{index:03d}",
                    source_id=f"ohoiko-june-a1-note-{index:03d}",
                    source_family=SOURCE_FAMILY,
                    extraction_mode="content_token",
                    unit_kind="june_a1_note",
                    available=True,
                )
            )
    return tuple(units)


def collect_ohoiko_occurrences(
    units: Sequence[OhoikoSourceUnit],
    *,
    private_root: Path = DEFAULT_PRIVATE_ROOT,
    june_notes_root: Path = DEFAULT_JUNE_NOTES_ROOT,
) -> list[core.IntakeOccurrence]:
    occurrences: list[core.IntakeOccurrence] = []
    book_units = {unit.source_id: unit for unit in units if unit.unit_kind.startswith("book:")}
    for book in BOOK_CATALOG:
        unit = book_units.get(book.source_id)
        if unit is None or not unit.available:
            continue
        path = private_root / book.filename
        if book.parser == "numbered_entries":
            occurrences.extend(_occurrences_from_numbered_book(path, book=book, unit=unit))
        elif book.parser == "verb_pages":
            occurrences.extend(_occurrences_from_verb_book(path, book=book, unit=unit))
    ulp_units = [unit for unit in units if unit.unit_kind == "ulp_lesson_notes"]
    for _catalog_index, (source_id, filename, title) in enumerate(ULP_NOTE_CATALOG, start=1):
        unit = next((row for row in ulp_units if row.source_id == source_id), None)
        if unit is None or not unit.available:
            continue
        path = private_root / filename
        occurrences.extend(
            _occurrences_from_running_text(
                path.read_text(encoding="utf-8"),
                source_id=source_id,
                source_ref=unit.source_ref,
                extraction_mode="content_token",
                source_title=title,
                locator_prefix=f"{unit.source_ref}::block",
            )
        )
    june_units = [unit for unit in units if unit.unit_kind == "june_a1_note"]
    if june_units and june_notes_root.is_dir():
        note_files = sorted(
            path
            for path in june_notes_root.glob("**/*")
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
        )
        for unit, path in zip(june_units, note_files, strict=False):
            text = strip_mdx_to_prose(path.read_text(encoding="utf-8"))
            occurrences.extend(
                _occurrences_from_running_text(
                    text,
                    source_id=unit.source_id,
                    source_ref=unit.source_ref,
                    extraction_mode="content_token",
                    source_title="Anna Ohoiko June A1 book note",
                    locator_prefix=f"{unit.source_ref}::block",
                )
            )
    return _compact_occurrences(occurrences)


def build_ohoiko_intake(
    *,
    private_root: Path = DEFAULT_PRIVATE_ROOT,
    june_notes_root: Path = DEFAULT_JUNE_NOTES_ROOT,
    project_root: Path = PROJECT_ROOT,
    manifest_lemma_keys: set[str] | None = None,
    existing_ledger_keys: set[str] | None = None,
    committed_inventory_keys: set[str] | None = None,
    vesum_lookup: core.VesumLookup | None = None,
    heritage_lookup: core.HeritageLookup = classify_lemma,
    inventory_path: str = DEFAULT_INVENTORY_PATH,
) -> core.AtlasIntakeResult:
    units = discover_source_units(private_root=private_root, june_notes_root=june_notes_root)
    occurrences = collect_ohoiko_occurrences(units, private_root=private_root, june_notes_root=june_notes_root)
    forms = tuple(sorted({occurrence.form for occurrence in occurrences}, key=core.stable_lemma_sort_key))
    resolutions = core.resolve_forms(forms, vesum_lookup=vesum_lookup)
    atlas_keys = manifest_lemma_keys if manifest_lemma_keys is not None else core.load_atlas_lemma_keys()
    ledger_keys = (
        existing_ledger_keys
        if existing_ledger_keys is not None
        else core.load_existing_ledger_keys(project_root=project_root)
    )
    committed_keys = (
        committed_inventory_keys
        if committed_inventory_keys is not None
        else core.load_committed_inventory_keys(
            committed_ohoiko_inventory_paths(project_root=project_root),
            project_root=project_root,
        )
    )
    candidates = core.build_intake_candidates(
        occurrences,
        resolutions=resolutions,
        atlas_keys={_lemma_key(lemma) for lemma in atlas_keys},
        ledger_keys={_lemma_key(lemma) for lemma in ledger_keys},
        committed_inventory_keys=committed_keys,
        heritage_lookup=heritage_lookup,
        inventory_path=inventory_path,
        source_family=SOURCE_FAMILY,
    )
    return core.AtlasIntakeResult(
        workflow=WORKFLOW_ID,
        source_family=SOURCE_FAMILY,
        source_units=tuple(_public_source_unit(unit) for unit in units),
        token_occurrences=sum(occurrence.count for occurrence in occurrences),
        unique_forms=len(forms),
        candidates=tuple(candidates),
        inventory_path=inventory_path,
    )


def inventory_counts(units: Sequence[OhoikoSourceUnit]) -> dict[str, int]:
    """Return deterministic in-scope inventory counts for PR reporting."""

    book_total = len(BOOK_CATALOG)
    book_available = sum(1 for unit in units if unit.unit_kind.startswith("book:") and unit.available)
    ulp_total = len(ULP_NOTE_CATALOG)
    ulp_available = sum(1 for unit in units if unit.unit_kind == "ulp_lesson_notes" and unit.available)
    june_total = sum(1 for unit in units if unit.unit_kind == "june_a1_note")
    june_available = sum(1 for unit in units if unit.unit_kind == "june_a1_note" and unit.available)
    return {
        "source_units_total": len(units),
        "source_units_available": sum(1 for unit in units if unit.available),
        "book_sources_total": book_total,
        "book_sources_available": book_available,
        "ulp_note_sources_total": ulp_total,
        "ulp_note_sources_available": ulp_available,
        "june_note_sources_total": june_total,
        "june_note_sources_available": june_available,
    }


def format_summary(result: core.AtlasIntakeResult) -> str:
    counts = result.classification_counts
    inventory = inventory_counts(
        tuple(
            OhoikoSourceUnit(
                source_ref=str(unit["source_ref"]),
                source_id=str(unit["source_id"]),
                source_family=str(unit["source_family"]),
                extraction_mode=str(unit["extraction_mode"]),
                unit_kind=str(unit["unit_kind"]),
                available=bool(unit["available"]),
            )
            for unit in result.source_units
        )
    )
    lines = [
        "Ohoiko Word Atlas intake",
        f"source_units_total: {inventory['source_units_total']}",
        f"source_units_available: {inventory['source_units_available']}",
        f"book_sources_total: {inventory['book_sources_total']}",
        f"book_sources_available: {inventory['book_sources_available']}",
        f"ulp_note_sources_total: {inventory['ulp_note_sources_total']}",
        f"ulp_note_sources_available: {inventory['ulp_note_sources_available']}",
        f"june_note_sources_total: {inventory['june_note_sources_total']}",
        f"june_note_sources_available: {inventory['june_note_sources_available']}",
        f"token_occurrences: {result.token_occurrences}",
        f"unique_forms: {result.unique_forms}",
        f"deduped_candidates: {len(result.candidates)}",
        f"auto_approve: {counts['auto_approve']}",
        f"review_queue: {counts['review_queue']}",
        f"reject: {counts['reject']}",
        "production_outputs_updated: []",
        "surface_admission: Daily Word unchanged; Practice unchanged; Cloze unchanged",
    ]
    return "\n".join(lines)


def _public_source_unit(unit: OhoikoSourceUnit) -> dict[str, Any]:
    return {
        "source_ref": unit.source_ref,
        "source_id": unit.source_id,
        "source_family": unit.source_family,
        "extraction_mode": unit.extraction_mode,
        "unit_kind": unit.unit_kind,
        "available": unit.available,
    }


def _occurrences_from_numbered_book(
    path: Path,
    *,
    book: OhoikoBookSource,
    unit: OhoikoSourceUnit,
) -> list[core.IntakeOccurrence]:
    entries = words_ingest.parse_book(path, max_entry_number=book.max_entries)
    occurrences: list[core.IntakeOccurrence] = []
    for entry in entries:
        headword = strip_acute_stress(entry.headword.split("=")[0].strip())
        if not headword:
            continue
        gloss = entry.english.strip() or None
        occurrences.append(
            core.IntakeOccurrence(
                form=headword,
                source_id=book.source_id,
                source_family=SOURCE_FAMILY,
                extraction_mode=book.extraction_mode,
                locator=f"{unit.source_ref}::entry-{entry.number:04d}",
                count=1,
                explicit_gloss=gloss,
                source_title=book.source_title,
            )
        )
    return occurrences


def _occurrences_from_verb_book(
    path: Path,
    *,
    book: OhoikoBookSource,
    unit: OhoikoSourceUnit,
) -> list[core.IntakeOccurrence]:
    verbs = verbs_ingest.parse_book(path)
    occurrences: list[core.IntakeOccurrence] = []
    for verb in verbs:
        headword = _verb_headword(verb.headword_line or verb.title)
        if headword:
            occurrences.append(
                core.IntakeOccurrence(
                    form=headword,
                    source_id=book.source_id,
                    source_family=SOURCE_FAMILY,
                    extraction_mode=book.extraction_mode,
                    locator=f"{unit.source_ref}::verb-{verb.number:04d}",
                    count=1,
                    source_title=book.source_title,
                )
            )
        body_text = verb.render()
        occurrences.extend(
            _occurrences_from_running_text(
                body_text,
                source_id=book.source_id,
                source_ref=unit.source_ref,
                extraction_mode="content_token",
                source_title=book.source_title,
                locator_prefix=f"{unit.source_ref}::verb-{verb.number:04d}::token",
            )
        )
    return occurrences


def _verb_headword(line: str) -> str | None:
    cleaned = strip_acute_stress(line.strip())
    if not cleaned:
        return None
    match = _VERB_HEADWORD_RE.match(cleaned)
    candidate = match.group(1).strip() if match else cleaned.split("|", 1)[0].strip()
    candidate = candidate.split()[0].strip() if candidate else ""
    return candidate or None


def _occurrences_from_running_text(
    text: str,
    *,
    source_id: str,
    source_ref: str,
    extraction_mode: str,
    source_title: str,
    locator_prefix: str,
) -> list[core.IntakeOccurrence]:
    counts = Counter(extract_ukrainian_tokens(strip_mdx_to_prose(text)))
    return [
        core.IntakeOccurrence(
            form=form,
            source_id=source_id,
            source_family=SOURCE_FAMILY,
            extraction_mode=extraction_mode,
            locator=f"{locator_prefix}-{index:04d}",
            count=count,
            source_title=source_title,
        )
        for index, (form, count) in enumerate(
            sorted(counts.items(), key=lambda item: _lemma_key(item[0])),
            start=1,
        )
    ]


def _compact_occurrences(occurrences: Sequence[core.IntakeOccurrence]) -> list[core.IntakeOccurrence]:
    grouped: dict[tuple[str, str, str, str | None], core.IntakeOccurrence] = {}
    for occurrence in occurrences:
        key = (
            occurrence.form,
            occurrence.source_id,
            occurrence.locator,
            occurrence.explicit_gloss,
        )
        previous = grouped.get(key)
        grouped[key] = (
            occurrence
            if previous is None
            else core.IntakeOccurrence(
                form=previous.form,
                source_id=previous.source_id,
                source_family=previous.source_family,
                extraction_mode=previous.extraction_mode,
                locator=previous.locator,
                count=previous.count + occurrence.count,
                explicit_gloss=previous.explicit_gloss,
                source_title=previous.source_title,
                source_path=previous.source_path,
            )
        )
    return sorted(
        grouped.values(),
        key=lambda item: (item.source_id, item.locator, _lemma_key(item.form), item.explicit_gloss or ""),
    )


def source_ref_for_path(path: Path, *, prefix: str = "ohoiko-source") -> str:
    """Return a stable opaque locator key for a private path (local tooling only)."""

    digest = hashlib.sha256(path.as_posix().encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run fail-closed Anna Ohoiko corpus Word Atlas intake.")
    parser.add_argument("--private-root", type=Path, default=DEFAULT_PRIVATE_ROOT)
    parser.add_argument("--june-notes-root", type=Path, default=DEFAULT_JUNE_NOTES_ROOT)
    parser.add_argument("--inventory-path", default=DEFAULT_INVENTORY_PATH)
    parser.add_argument("--inventory-out", type=Path, default=DEFAULT_INVENTORY_OUT)
    parser.add_argument("--report-out", type=Path, default=DEFAULT_REPORT_OUT)
    parser.add_argument("--ledger-out", type=Path)
    parser.add_argument("--batch-id")
    parser.add_argument("--batch-label")
    parser.add_argument("--reviewed-at", help="Required when --ledger-out is supplied (YYYY-MM-DD).")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.ledger_out and not all((args.batch_id, args.batch_label, args.reviewed_at)):
        parser.error("--ledger-out requires --batch-id, --batch-label, and --reviewed-at")
    try:
        if args.ledger_out:
            core.assert_ledger_inventory_destination(args.inventory_out, args.inventory_path)
        result = build_ohoiko_intake(
            private_root=args.private_root,
            june_notes_root=args.june_notes_root,
            inventory_path=args.inventory_path,
        )
        core.write_flat_source_inventory(result.records, args.inventory_out)
        report = result.report_payload(
            policy=(
                "Anna Ohoiko private-corpus intake. Public output uses opaque source_ref locators "
                "only; raw copyrighted text never leaves the private boundary. Uncertain VESUM or "
                "heritage outcomes are review_queue. This command does not update Atlas or learner surfaces."
            )
        )
        report["inventory_counts"] = inventory_counts(
            tuple(
                OhoikoSourceUnit(
                    source_ref=str(unit["source_ref"]),
                    source_id=str(unit["source_id"]),
                    source_family=str(unit["source_family"]),
                    extraction_mode=str(unit["extraction_mode"]),
                    unit_kind=str(unit["unit_kind"]),
                    available=bool(unit["available"]),
                )
                for unit in result.source_units
            )
        )
        core.write_json_payload(report, args.report_out)
        if args.ledger_out:
            core.write_yaml_payload(
                core.build_ledger_append_payload(
                    result,
                    batch_id=args.batch_id,
                    batch_label=args.batch_label,
                    reviewed_at=args.reviewed_at,
                    reviewer="ohoiko-intake-automation",
                ),
                args.ledger_out,
            )
    except (OhoikoIntakeError, core.AtlasIntakeError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(format_summary(result))
    print(f"inventory_out: {args.inventory_out}")
    print(f"report_out: {args.report_out}")
    if args.ledger_out:
        print(f"ledger_out: {args.ledger_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
