#!/usr/bin/env python3
"""Build a words-only Atlas source inventory from a text-layer PDF.

The extractor deliberately retains no source prose.  Its YAML output consists
only of individual Ukrainian forms/lemmas, VESUM POS values, occurrence counts,
and neutral module/page locators.  It is therefore suitable for a copyrighted
book whose source text must not enter the repository.

Run from the repository root::

    .venv/bin/python scripts/lexicon/extract_book_headword_inventory.py \
      --pdf /private/book.pdf --out /tmp/book-headwords.yaml --report
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.verification.vesum import verify_words

SOURCE_ID = "ohoiko-oho-a1-book-headwords"
SOURCE_FAMILY = "ohoiko"
EXTRACTION_MODE = "headword_inventory"
DEFAULT_BATCH_SIZE = 500
MAX_UNKNOWN_FORM_RATE = 0.20

_NUMBERED_MODULE_HEADER_RE = re.compile(r"^\s*(?:«\s*)?(?P<number>[1-9]\d?)\s+\S")
_SECTION_HEADER_RE = re.compile(
    r"^\s*(?:«\s*)?(?P<section>Повторення|Мій\s+прогрес)\s*№\s*(?P<number>[1-9]\d?)\b",
    re.IGNORECASE,
)
_PAGE_NUMBER_RE = re.compile(r"^\s*(?:p(?:age)?\.?\s*)?\d{1,4}\s*$", re.IGNORECASE)
_CYRILLIC_LETTER = r"\u0400-\u052f"
_UKRAINIAN_TOKEN_RE = re.compile(
    rf"[{_CYRILLIC_LETTER}]+(?:['-][{_CYRILLIC_LETTER}]+)*", re.IGNORECASE
)
_APOSTROPHE_TRANSLATION = str.maketrans({"ʼ": "'", "’": "'", "`": "'", "′": "'"})
_HYPHEN_TRANSLATION = str.maketrans({"‐": "-", "‑": "-", "‒": "-", "–": "-"})
_RUNNING_FOOTERS = frozenset(
    {
        "inspiring resources for learning ukrainian — ukrainianlessons.com",
        "inspiring resources for learning ukrainian - ukrainianlessons.com",
        "back to contents",
    }
)

type VesumLookup = Callable[[list[str]], dict[str, list[dict[str, Any]]]]
type ModuleValue = int | str


class ExtractionError(RuntimeError):
    """Raised when extraction cannot safely produce an inventory."""


@dataclass(frozen=True)
class PageText:
    """One physical PDF page and its text-layer content."""

    number: int
    text: str


@dataclass(frozen=True)
class FormOccurrence:
    """A normalized Ukrainian token plus its neutral source locator."""

    form: str
    module: ModuleValue
    page: int
    capitalized: bool


@dataclass(frozen=True)
class ExtractionStats:
    """Deterministic summary of a complete extraction pass."""

    pages_read: int
    tokens_seen: int
    unique_forms: int
    unambiguous_forms: int
    ambiguous_forms: int
    unknown_forms: int
    lemmas_found: int

    @property
    def unknown_rate(self) -> float:
        if not self.unique_forms:
            return 1.0
        return self.unknown_forms / self.unique_forms


@dataclass(frozen=True)
class ExtractionResult:
    """Safe derived metadata ready for YAML serialization."""

    inventory: dict[str, Any]
    modules_map: dict[str, Any]
    stats: ExtractionStats
    module_coverage: dict[ModuleValue, dict[str, int]]
    modules_detected: int


def normalize_text(value: str) -> str:
    """Normalize source text without altering Ukrainian letters.

    The acute stress mark is intentionally removed through the shared helper:
    its NFD/NFC round trip preserves the combining marks that constitute ``й``
    and ``ї``.  ASCII apostrophe is the VESUM/source-inventory convention.
    """

    return strip_acute_stress(
        unicodedata.normalize("NFC", value).translate(_APOSTROPHE_TRANSLATION).translate(_HYPHEN_TRANSLATION)
    )


def strip_running_lines(page_text: str) -> str:
    """Remove known running footer/header artifacts and standalone page numbers."""

    kept: list[str] = []
    for raw_line in normalize_text(page_text).splitlines():
        compact = " ".join(raw_line.split())
        if not compact:
            kept.append("")
            continue
        if compact.casefold() in _RUNNING_FOOTERS or _PAGE_NUMBER_RE.fullmatch(compact):
            continue
        kept.append(raw_line)
    return "\n".join(kept)


def parse_module_header(line: str) -> ModuleValue | None:
    """Return a neutral page-module marker for a recognized section heading."""

    normalized = normalize_text(line)
    section_match = _SECTION_HEADER_RE.match(normalized)
    if section_match:
        section = section_match.group("section").casefold()
        prefix = "review" if section.startswith("повторення") else "progress"
        return f"{prefix}-{int(section_match.group('number'))}"

    module_match = _NUMBERED_MODULE_HEADER_RE.match(normalized)
    if module_match:
        return int(module_match.group("number"))
    return None


def map_pages_to_modules(pages: Sequence[PageText]) -> tuple[dict[int, ModuleValue], int]:
    """Map each page to the latest numbered module or review/progress heading."""

    page_modules: dict[int, ModuleValue] = {}
    current: ModuleValue = "front-matter"
    numbered_modules: set[int] = set()

    for page in pages:
        cleaned = strip_running_lines(page.text)
        markers = [parse_module_header(line) for line in cleaned.splitlines()]
        numbered_modules.update(marker for marker in markers if isinstance(marker, int))
        marker = next((item for item in reversed(markers) if item is not None), None)
        if marker is not None:
            current = marker
        page_modules[page.number] = current

    return page_modules, len(numbered_modules)


def _is_capitalized_word(token: str) -> bool:
    """Return true for a token beginning uppercase and otherwise letter-like."""

    return bool(token) and token[0].isupper() and token != token.upper()


def extract_occurrences(
    pages: Sequence[PageText], page_modules: Mapping[int, ModuleValue]
) -> list[FormOccurrence]:
    """Tokenize all cleaned pages while retaining only word-level provenance."""

    occurrences: list[FormOccurrence] = []
    for page in pages:
        cleaned = strip_running_lines(page.text)
        for match in _UKRAINIAN_TOKEN_RE.finditer(cleaned):
            token = match.group(0)
            normalized = normalize_text(token)
            if not normalized:
                continue
            occurrences.append(
                FormOccurrence(
                    form=normalized,
                    module=page_modules[page.number],
                    page=page.number,
                    capitalized=_is_capitalized_word(normalized),
                )
            )
    return occurrences


def _form_key(form: str) -> str:
    """Normalize a surface form for case-insensitive occurrence aggregation."""

    return form.casefold()


def _lookup_forms(occurrences: Sequence[FormOccurrence]) -> tuple[str, str | None, bool]:
    """Select VESUM forms and flag capitalized-only candidates.

    A capitalized-only token is tried in its observed case first so a proper
    noun can match VESUM as such.  If that fails, its lowercased form is a
    necessary fallback for ordinary heading or sentence-initial words.
    """

    first = occurrences[0].form
    capitalized_only = all(item.capitalized for item in occurrences)
    if capitalized_only:
        return first, first.casefold(), True
    return first.casefold(), None, False


def _module_sort_key(module: ModuleValue) -> tuple[int, int, str]:
    if module == "front-matter":
        return (0, 0, "")
    if isinstance(module, int):
        return (1, module, "")
    if isinstance(module, str) and "-" in module:
        kind, _, number = module.partition("-")
        if number.isdigit():
            return (2 if kind == "review" else 3, int(number), kind)
    return (4, 0, str(module))


def _module_label(module: ModuleValue) -> str:
    if module == "front-matter":
        return "front-matter"
    if isinstance(module, int):
        return f"module {module}"
    kind, _, number = str(module).partition("-")
    return f"{kind} {number}" if number else str(module)


def _locator(module: ModuleValue, page: int) -> str:
    return f"{_module_label(module)} p.{page}"


def _dedupe_matches(matches: Iterable[Mapping[str, Any]]) -> list[tuple[str, str]]:
    """Return VESUM lemma/POS candidates in deterministic order."""

    candidates = {
        (
            normalize_text(str(match.get("lemma", "")).strip()),
            str(match.get("pos", "")).strip(),
        )
        for match in matches
        if str(match.get("lemma", "")).strip() and str(match.get("pos", "")).strip()
    }
    return sorted(candidates, key=lambda item: (item[0].casefold(), item[1]))


def _lookup_in_batches(
    forms: Sequence[str], *, vesum_lookup: VesumLookup, batch_size: int
) -> dict[str, list[dict[str, Any]]]:
    """Look up unique VESUM forms without exceeding SQLite parameter limits."""

    results: dict[str, list[dict[str, Any]]] = {}
    for offset in range(0, len(forms), batch_size):
        batch = list(forms[offset : offset + batch_size])
        response = vesum_lookup(batch)
        for form in batch:
            matches = response.get(form, [])
            results[form] = matches if isinstance(matches, list) else []
    return results


def _coverage_template() -> dict[str, int]:
    return {
        "pages": 0,
        "tokens": 0,
        "unique_forms": 0,
        "unambiguous_forms": 0,
        "ambiguous_forms": 0,
        "unknown_forms": 0,
        "lemmas": 0,
    }


def extract_headword_inventory(
    pages: Sequence[PageText],
    *,
    vesum_lookup: VesumLookup = verify_words,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> ExtractionResult:
    """Derive a words-only, VESUM-backed headword inventory from PDF pages.

    This function accepts page text solely to make the privacy-sensitive
    pipeline testable with synthetic fixtures.  It never places ``PageText``
    content into its result.
    """

    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    page_modules, modules_detected = map_pages_to_modules(pages)
    occurrences = extract_occurrences(pages, page_modules)
    by_form: dict[str, list[FormOccurrence]] = defaultdict(list)
    for occurrence in occurrences:
        by_form[_form_key(occurrence.form)].append(occurrence)

    form_details: dict[str, tuple[str, str | None, bool, list[FormOccurrence]]] = {}
    for key, form_occurrences in by_form.items():
        lookup_form, fallback_form, capitalized_only = _lookup_forms(form_occurrences)
        form_details[key] = (lookup_form, fallback_form, capitalized_only, form_occurrences)

    lookup_forms = sorted(
        {
            lookup_form
            for lookup_form, fallback_form, _, _ in form_details.values()
            for lookup_form in (lookup_form, fallback_form)
            if lookup_form is not None
        },
        key=str.casefold,
    )
    matches_by_lookup_form = _lookup_in_batches(
        lookup_forms, vesum_lookup=vesum_lookup, batch_size=batch_size
    )

    headword_occurrences: dict[tuple[str, str], list[FormOccurrence]] = defaultdict(list)
    headword_ambiguous: dict[tuple[str, str], bool] = defaultdict(bool)
    headword_proper_candidate: dict[tuple[str, str], bool] = defaultdict(bool)
    unknown_occurrences: dict[str, list[FormOccurrence]] = {}
    unknown_proper_candidate: dict[str, bool] = {}
    form_status: dict[str, str] = {}

    for key in sorted(form_details):
        lookup_form, fallback_form, capitalized_only, form_occurrences = form_details[key]
        matches = matches_by_lookup_form.get(lookup_form, [])
        if not matches and fallback_form is not None:
            matches = matches_by_lookup_form.get(fallback_form, [])
        candidates = _dedupe_matches(matches)
        if not candidates:
            unknown_occurrences[lookup_form] = form_occurrences
            unknown_proper_candidate[lookup_form] = capitalized_only
            form_status[key] = "unknown"
            continue

        ambiguous = len(candidates) > 1
        form_status[key] = "ambiguous" if ambiguous else "unambiguous"
        for candidate in candidates:
            headword_occurrences[candidate].extend(form_occurrences)
            headword_ambiguous[candidate] = headword_ambiguous[candidate] or ambiguous
            headword_proper_candidate[candidate] = (
                headword_proper_candidate[candidate] or capitalized_only
            )

    coverage: dict[ModuleValue, dict[str, int]] = {}
    for module in sorted(set(page_modules.values()), key=_module_sort_key):
        coverage[module] = _coverage_template()
    for page in pages:
        coverage[page_modules[page.number]]["pages"] += 1
    for occurrence in occurrences:
        coverage[occurrence.module]["tokens"] += 1
    for key, (_, _, _, form_occurrences) in form_details.items():
        modules = {item.module for item in form_occurrences}
        status = form_status[key]
        for module in modules:
            coverage[module]["unique_forms"] += 1
            coverage[module][f"{status}_forms"] += 1

    def entry_from_occurrences(
        *,
        form_occurrences: Sequence[FormOccurrence],
        proper_candidate: bool,
    ) -> dict[str, Any]:
        first = min(form_occurrences, key=lambda item: (item.page, _module_sort_key(item.module)))
        modules = sorted({item.module for item in form_occurrences}, key=_module_sort_key)
        item: dict[str, Any] = {
            "count": len(form_occurrences),
            "first_module": first.module,
            "modules": modules,
            "locator": _locator(first.module, first.page),
        }
        if proper_candidate:
            item["proper_noun_candidate"] = True
        return item

    headwords: list[dict[str, Any]] = []
    for (lemma, pos), lemma_occurrences in headword_occurrences.items():
        item = {"lemma": lemma, "pos": pos}
        item.update(
            entry_from_occurrences(
                form_occurrences=lemma_occurrences,
                proper_candidate=headword_proper_candidate[(lemma, pos)],
            )
        )
        if headword_ambiguous[(lemma, pos)]:
            item["ambiguous"] = True
        headwords.append(item)

    headwords.sort(
        key=lambda item: (
            _module_sort_key(item["first_module"]),
            str(item["lemma"]).casefold(),
            str(item["pos"]),
        )
    )

    unknown_forms: list[dict[str, Any]] = []
    for form, form_occurrences in unknown_occurrences.items():
        item = {"form": form}
        item.update(
            entry_from_occurrences(
                form_occurrences=form_occurrences,
                proper_candidate=unknown_proper_candidate[form],
            )
        )
        unknown_forms.append(item)
    unknown_forms.sort(
        key=lambda item: (_module_sort_key(item["first_module"]), str(item["form"]).casefold())
    )

    for (_lemma, _), lemma_occurrences in headword_occurrences.items():
        for module in {item.module for item in lemma_occurrences}:
            coverage[module]["lemmas"] += 1

    stats = ExtractionStats(
        pages_read=len(pages),
        tokens_seen=len(occurrences),
        unique_forms=len(form_details),
        unambiguous_forms=sum(status == "unambiguous" for status in form_status.values()),
        ambiguous_forms=sum(status == "ambiguous" for status in form_status.values()),
        unknown_forms=sum(status == "unknown" for status in form_status.values()),
        lemmas_found=len(headwords),
    )
    inventory = {
        "version": 1,
        "kind": "atlas_source_inventory",
        "sources": [
            {
                "id": SOURCE_ID,
                "source_family": SOURCE_FAMILY,
                "extraction_mode": EXTRACTION_MODE,
                "headwords": headwords,
                "unknown_forms": unknown_forms,
            }
        ],
    }
    modules_map = {
        "version": 1,
        "pages": [
            {"page": page.number, "module": page_modules[page.number]}
            for page in sorted(pages, key=lambda item: item.number)
        ],
    }
    return ExtractionResult(
        inventory=inventory,
        modules_map=modules_map,
        stats=stats,
        module_coverage=coverage,
        modules_detected=modules_detected,
    )


def validate_result(result: ExtractionResult) -> None:
    """Fail closed before any output file is written."""

    if result.modules_detected == 0:
        raise ExtractionError("zero numbered modules detected")
    headwords = result.inventory["sources"][0]["headwords"]
    if not headwords:
        raise ExtractionError("empty headword output")
    if result.stats.unknown_rate > MAX_UNKNOWN_FORM_RATE:
        raise ExtractionError(
            "unknown forms exceed 20% "
            f"({result.stats.unknown_forms}/{result.stats.unique_forms})"
        )


def _resolve_binary(name: str) -> str:
    binary = shutil.which(name)
    if not binary:
        raise ExtractionError(f"required executable not found on PATH: {name}")
    return binary


def _run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "no stderr"
        raise ExtractionError(f"command failed ({Path(command[0]).name}): {detail}")
    return completed


def pdf_page_count(pdf_path: Path, *, pdfinfo_binary: str | None = None) -> int:
    """Read a PDF's physical page count using Poppler's metadata utility."""

    binary = pdfinfo_binary or _resolve_binary("pdfinfo")
    output = _run([binary, str(pdf_path)]).stdout
    match = re.search(r"^Pages:\s*(\d+)\s*$", output, re.MULTILINE)
    if not match or int(match.group(1)) < 1:
        raise ExtractionError("pdfinfo did not report a positive page count")
    return int(match.group(1))


def extract_pdf_pages(
    pdf_path: Path,
    *,
    pdftotext_binary: str | None = None,
    pdfinfo_binary: str | None = None,
) -> list[PageText]:
    """Extract each PDF page independently with Poppler's ``pdftotext``."""

    if not pdf_path.is_file():
        raise ExtractionError(f"PDF not found: {pdf_path}")
    pdftotext = pdftotext_binary or _resolve_binary("pdftotext")
    page_count = pdf_page_count(pdf_path, pdfinfo_binary=pdfinfo_binary)
    pages: list[PageText] = []
    for number in range(1, page_count + 1):
        completed = _run(
            [
                pdftotext,
                "-f",
                str(number),
                "-l",
                str(number),
                "-layout",
                str(pdf_path),
                "-",
            ]
        )
        pages.append(PageText(number=number, text=completed.stdout))
    return pages


def _atomic_write_yaml(payload: Mapping[str, Any], output_path: Path) -> None:
    """Atomically write deterministic UTF-8 YAML after validation has passed."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(
        dict(payload),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=1000,
    )
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=output_path.parent, delete=False
    ) as handle:
        temporary_path = Path(handle.name)
        handle.write(text)
    try:
        os.replace(temporary_path, output_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def format_report(result: ExtractionResult) -> str:
    """Render deterministic, source-prose-free extraction statistics."""

    stats = result.stats
    lines = [
        (
            "BEFORE "
            f"pages_read={stats.pages_read} tokens_seen={stats.tokens_seen} "
            f"unique_forms={stats.unique_forms}"
        ),
        (
            "AFTER "
            f"lemmas_found={stats.lemmas_found} "
            f"unambiguous_forms={stats.unambiguous_forms} "
            f"ambiguous_forms={stats.ambiguous_forms} "
            f"unknown_forms={stats.unknown_forms} "
            f"unknown_rate={stats.unknown_rate:.2%}"
        ),
        "MODULE COVERAGE",
    ]
    for module in sorted(result.module_coverage, key=_module_sort_key):
        row = result.module_coverage[module]
        lines.append(
            f"{_module_label(module)} "
            f"pages={row['pages']} tokens={row['tokens']} unique_forms={row['unique_forms']} "
            f"lemmas={row['lemmas']} ambiguous_forms={row['ambiguous_forms']} "
            f"unknown_forms={row['unknown_forms']}"
        )
    return "\n".join(lines)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract a words-only VESUM headword inventory from a text-layer PDF."
    )
    parser.add_argument("--pdf", type=Path, required=True, help="Text-layer PDF to process")
    parser.add_argument("--out", type=Path, required=True, help="Inventory YAML destination")
    parser.add_argument(
        "--modules-map-out", type=Path, help="Optional page-to-module YAML destination"
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate but do not write YAML")
    parser.add_argument("--report", action="store_true", help="Print per-module coverage")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        pages = extract_pdf_pages(args.pdf)
        result = extract_headword_inventory(pages)
    except ExtractionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        validate_result(result)
    except ExtractionError as exc:
        print(format_report(result), file=sys.stderr)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(format_report(result))
    if args.dry_run:
        print("DRY RUN: no output written")
        return 0

    _atomic_write_yaml(result.inventory, args.out)
    if args.modules_map_out:
        _atomic_write_yaml(result.modules_map, args.modules_map_out)
    if args.report:
        print(f"WROTE inventory={args.out}")
        if args.modules_map_out:
            print(f"WROTE modules_map={args.modules_map_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
