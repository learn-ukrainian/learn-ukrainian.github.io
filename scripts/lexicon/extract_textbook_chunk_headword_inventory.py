#!/usr/bin/env python3
"""Build a words-only VESUM headword inventory from local textbook JSONL chunks.

Sibling of ``extract_book_headword_inventory.py`` (which reads a text-layer
PDF directly). This variant reads the already-chunked JSONL produced by the
textbook ingest pipeline (``data/textbook_chunks/grade-XX/*.jsonl``) — one
JSON object per page/section with a ``text`` field — and applies the same
words-only, VESUM-backed extraction discipline: only individual Ukrainian
forms/lemmas, VESUM POS values, occurrence counts, and neutral page locators
leave this script. No source prose is retained in the output.

Run from the repository root::

    .venv/bin/python scripts/lexicon/extract_textbook_chunk_headword_inventory.py \
      --jsonl data/textbook_chunks/grade-01/1-klas-bukvar-zaharijchuk-2025-1.jsonl \
      --jsonl data/textbook_chunks/grade-01/1-klas-bukvar-zaharijchuk-2025-2.jsonl \
      --source-id bukvar-zaharijchuk-grade1-2025 \
      --title "Захарійчук М. Українська мова. Буквар. 1 клас, 2025" \
      --out /tmp/bukvar-headwords.yaml --report
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.extract_book_headword_inventory import (
    _UKRAINIAN_TOKEN_RE,
    MAX_UNKNOWN_FORM_RATE,
    ExtractionError,
    _atomic_write_yaml,
    _dedupe_matches,
    _lookup_in_batches,
    normalize_text,
)
from scripts.verification.vesum import verify_words

DEFAULT_BATCH_SIZE = 500


def _form_key(form: str) -> str:
    return form.casefold()


def _is_capitalized_word(token: str) -> bool:
    return bool(token) and token[0].isupper() and token != token.upper()


def load_chunks(jsonl_paths: list[Path]) -> list[dict[str, Any]]:
    """Read and concatenate chunk records, sorted into stable reading order."""

    chunks: list[dict[str, Any]] = []
    for path in jsonl_paths:
        if not path.is_file():
            raise ExtractionError(f"chunk file not found: {path}")
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    record = json.loads(raw_line)
                except json.JSONDecodeError as exc:
                    raise ExtractionError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
                if "text" not in record:
                    raise ExtractionError(f"{path}:{line_number}: chunk has no 'text' field")
                chunks.append(record)
    chunks.sort(
        key=lambda item: (
            int(item.get("part", 1) or 1),
            int(item.get("page_start", 0) or 0),
            str(item.get("chunk_id", "")),
        )
    )
    return chunks


def extract_headword_inventory_from_chunks(
    chunks: list[dict[str, Any]],
    *,
    source_id: str,
    title: str,
    subject: str | None = None,
    vesum_lookup=verify_words,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, Any]:
    """Derive a words-only, VESUM-backed headword inventory from chunk text.

    Mirrors ``extract_book_headword_inventory.extract_headword_inventory`` but
    keys occurrences by ``(part, page_start-page_end)`` locators taken from
    chunk metadata instead of PDF page numbers plus curriculum-module
    headers — grade-1 subject textbooks do not carry numbered-module front
    matter, so that detector does not apply here.
    """

    occurrences: dict[str, list[tuple[str, str, bool]]] = {}
    tokens_seen = 0
    for chunk in chunks:
        part = chunk.get("part", 1)
        page_start = chunk.get("page_start")
        page_end = chunk.get("page_end")
        # Grade-1 chunk metadata sets `part` to the real print-part number for a
        # book split across files (1, 2, ...) but to the publication year for a
        # single-file book — only the former is a meaningful within-book locator.
        part_prefix = f"part {part} " if isinstance(part, int) and 1 <= part <= 9 else ""
        page_locator = f"p.{page_start}" if page_start == page_end else f"pp.{page_start}-{page_end}"
        locator = f"{part_prefix}{page_locator}"
        text = normalize_text(str(chunk.get("text", "")))
        for match in _UKRAINIAN_TOKEN_RE.finditer(text):
            token = normalize_text(match.group(0))
            if not token:
                continue
            tokens_seen += 1
            key = _form_key(token)
            occurrences.setdefault(key, []).append((token, locator, _is_capitalized_word(token)))

    # Bukvar-style primers visually hyphenate whole words into syllables for
    # reading practice (e.g. "ма-ма" for мама, "во-ни" for вони). Such a form
    # never appears in VESUM under its hyphenated spelling, so a dehyphenated
    # variant is queried as a last-resort fallback before a token is admitted
    # to `unknown_forms`. This introduces no new candidate lemmas beyond what
    # VESUM already recognizes as real, dictionary-attested forms.
    form_lookup: dict[str, tuple[str, str | None, str | None, bool]] = {}
    for key, entries in occurrences.items():
        first_form = entries[0][0]
        capitalized_only = all(item[2] for item in entries)
        dehyphenated = first_form.replace("-", "") if "-" in first_form else None
        if dehyphenated:
            dehyphenated = dehyphenated if capitalized_only else dehyphenated.casefold()
        if capitalized_only:
            form_lookup[key] = (first_form, first_form.casefold(), dehyphenated, True)
        else:
            form_lookup[key] = (first_form.casefold(), None, dehyphenated, False)

    lookup_forms = sorted(
        {
            form
            for lookup_form, fallback_form, dehyphenated_form, _ in form_lookup.values()
            for form in (lookup_form, fallback_form, dehyphenated_form)
            if form is not None
        },
        key=str.casefold,
    )
    matches_by_form = _lookup_in_batches(lookup_forms, vesum_lookup=vesum_lookup, batch_size=batch_size)

    headword_locators: dict[tuple[str, str], dict[str, int]] = {}
    headword_ambiguous: dict[tuple[str, str], bool] = {}
    headword_proper_candidate: dict[tuple[str, str], bool] = {}
    unknown_locators: dict[str, dict[str, int]] = {}
    unknown_proper_candidate: dict[str, bool] = {}
    unambiguous_forms = ambiguous_forms = unknown_forms = 0

    dehyphenated_matches: set[tuple[str, str]] = set()
    for key in sorted(form_lookup):
        lookup_form, fallback_form, dehyphenated_form, capitalized_only = form_lookup[key]
        entries = occurrences[key]
        matches = matches_by_form.get(lookup_form, [])
        if not matches and fallback_form is not None:
            matches = matches_by_form.get(fallback_form, [])
        used_dehyphenation = False
        if not matches and dehyphenated_form is not None:
            matches = matches_by_form.get(dehyphenated_form, [])
            used_dehyphenation = bool(matches)
        candidates = _dedupe_matches(matches)
        if not candidates:
            unknown_forms += 1
            bucket = unknown_locators.setdefault(lookup_form, {})
            for _, locator, _ in entries:
                bucket[locator] = bucket.get(locator, 0) + 1
            unknown_proper_candidate[lookup_form] = capitalized_only
            continue
        ambiguous = len(candidates) > 1
        ambiguous_forms += ambiguous
        unambiguous_forms += not ambiguous
        for candidate in candidates:
            if used_dehyphenation:
                dehyphenated_matches.add(candidate)
            bucket = headword_locators.setdefault(candidate, {})
            for _, locator, _ in entries:
                bucket[locator] = bucket.get(locator, 0) + 1
            headword_ambiguous[candidate] = headword_ambiguous.get(candidate, False) or ambiguous
            headword_proper_candidate[candidate] = (
                headword_proper_candidate.get(candidate, False) or capitalized_only
            )

    headwords: list[dict[str, Any]] = []
    for (lemma, pos), locator_counts in headword_locators.items():
        count = sum(locator_counts.values())
        item: dict[str, Any] = {
            "lemma": lemma,
            "pos": pos,
            "count": count,
            "locators": sorted(locator_counts),
        }
        if headword_ambiguous[(lemma, pos)]:
            item["ambiguous"] = True
        if headword_proper_candidate[(lemma, pos)]:
            item["proper_noun_candidate"] = True
        if (lemma, pos) in dehyphenated_matches:
            item["from_hyphenated_syllables"] = True
        headwords.append(item)
    headwords.sort(key=lambda item: (str(item["lemma"]).casefold(), str(item["pos"])))

    unknown_forms_list: list[dict[str, Any]] = []
    for form, locator_counts in unknown_locators.items():
        item = {
            "form": form,
            "count": sum(locator_counts.values()),
            "locators": sorted(locator_counts),
        }
        if unknown_proper_candidate[form]:
            item["proper_noun_candidate"] = True
        unknown_forms_list.append(item)
    unknown_forms_list.sort(key=lambda item: str(item["form"]).casefold())

    unique_forms = len(form_lookup)
    unknown_rate = (unknown_forms / unique_forms) if unique_forms else 1.0

    stats = {
        "pages_read": len(chunks),
        "tokens_seen": tokens_seen,
        "unique_forms": unique_forms,
        "unambiguous_forms": unambiguous_forms,
        "ambiguous_forms": ambiguous_forms,
        "unknown_forms": unknown_forms,
        "unknown_rate": round(unknown_rate, 4),
        "lemmas_found": len(headwords),
    }
    source: dict[str, Any] = {
        "id": source_id,
        "source_family": "textbook",
        "extraction_mode": "headword_inventory",
        "title": title,
        "headwords": headwords,
        "unknown_forms": unknown_forms_list,
    }
    if subject:
        source["subject"] = subject
    return {
        "version": 1,
        "kind": "atlas_source_inventory",
        "sources": [source],
        "stats": stats,
    }


def validate_result(payload: dict[str, Any], *, max_unknown_rate: float = MAX_UNKNOWN_FORM_RATE) -> None:
    stats = payload["stats"]
    headwords = payload["sources"][0]["headwords"]
    if not headwords:
        raise ExtractionError("empty headword output")
    if stats["unknown_rate"] > max_unknown_rate:
        raise ExtractionError(
            f"unknown forms exceed {max_unknown_rate:.0%} "
            f"({stats['unknown_forms']}/{stats['unique_forms']})"
        )


def format_report(payload: dict[str, Any]) -> str:
    stats = payload["stats"]
    return "\n".join(
        [
            (
                "BEFORE "
                f"pages_read={stats['pages_read']} tokens_seen={stats['tokens_seen']} "
                f"unique_forms={stats['unique_forms']}"
            ),
            (
                "AFTER "
                f"lemmas_found={stats['lemmas_found']} "
                f"unambiguous_forms={stats['unambiguous_forms']} "
                f"ambiguous_forms={stats['ambiguous_forms']} "
                f"unknown_forms={stats['unknown_forms']} "
                f"unknown_rate={stats['unknown_rate']:.2%}"
            ),
        ]
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract a words-only VESUM headword inventory from local textbook JSONL chunks."
    )
    parser.add_argument(
        "--jsonl", type=Path, action="append", required=True, help="Chunk JSONL path (repeatable)"
    )
    parser.add_argument("--source-id", required=True, help="Atlas source-inventory id for this book")
    parser.add_argument("--title", required=True, help="Human-readable book title")
    parser.add_argument("--subject", help="Optional subject label (e.g. bukvar, matematyka)")
    parser.add_argument("--out", type=Path, required=True, help="Inventory YAML destination")
    parser.add_argument("--dry-run", action="store_true", help="Validate but do not write YAML")
    parser.add_argument("--report", action="store_true", help="Print extraction stats")
    parser.add_argument(
        "--max-unknown-rate",
        type=float,
        default=MAX_UNKNOWN_FORM_RATE,
        help=(
            "Override the default 20%% unknown-forms gate for one book whose own "
            "source JSONL is independently known to carry an upstream PDF-extraction "
            "defect (e.g. dropped glyphs). Requires --unknown-rate-override-reason. "
            "Never use this to paper over a real vocabulary gap."
        ),
    )
    parser.add_argument(
        "--unknown-rate-override-reason",
        help="Required justification when --max-unknown-rate differs from the 20%% default; echoed in the report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    if args.max_unknown_rate != MAX_UNKNOWN_FORM_RATE and not args.unknown_rate_override_reason:
        print(
            "ERROR: --max-unknown-rate override requires --unknown-rate-override-reason",
            file=sys.stderr,
        )
        return 2
    try:
        chunks = load_chunks(args.jsonl)
        payload = extract_headword_inventory_from_chunks(
            chunks, source_id=args.source_id, title=args.title, subject=args.subject
        )
        validate_result(payload, max_unknown_rate=args.max_unknown_rate)
    except ExtractionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.unknown_rate_override_reason:
        print(f"UNKNOWN-RATE OVERRIDE ({args.max_unknown_rate:.0%}): {args.unknown_rate_override_reason}")

    print(format_report(payload))
    if args.dry_run:
        print("DRY RUN: no output written")
        return 0

    stats = payload.pop("stats")
    _atomic_write_yaml(payload, args.out)
    if args.report:
        print(f"WROTE inventory={args.out}")
        print(f"stats: {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
