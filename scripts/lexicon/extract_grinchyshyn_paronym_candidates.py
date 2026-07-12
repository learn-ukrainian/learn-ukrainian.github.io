"""Extract VESUM-gated paronym candidates from the local Grinchyshyn OCR.

The source is a local, ignored reference file. This extractor reads only the
all-caps headword lines from its ``ПАРОНІМИ`` section and never copies the
dictionary's definitions into the output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.verification.vesum import verify_word

DEFAULT_SOURCE = PROJECT_ROOT / "docs" / "references" / "private" / "grinchyshyn-slovnyk-paronimiv-1986.txt"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "lexicon" / "paronym_candidates_grinchyshyn.json"

UPPER_CYRILLIC = "А-ЩЬЮЯЄІЇҐ"
HEADWORD_TOKEN = rf"[{UPPER_CYRILLIC}][{UPPER_CYRILLIC}’ʼ\'\-]*"
HEADWORD_LINE_RE = re.compile(rf"^\s*({HEADWORD_TOKEN}(?:\s*/+\s*{HEADWORD_TOKEN})+)\s*$")


@dataclass(frozen=True)
class Drop:
    word_a: str
    word_b: str
    missing_words: tuple[str, ...]


@dataclass(frozen=True)
class ExtractionResult:
    rows: list[dict[str, str]]
    groups_found: int
    pairs_found: int
    malformed_groups: int
    drops: list[Drop]


VesumLookup = Callable[[str], list[dict]]


def _joined_candidate_lines(lines: list[str], start: int) -> Iterable[tuple[int, str]]:
    """Yield physical-line numbers and logical lines after wrapped slashes."""
    index = start
    while index < len(lines):
        line_number = index + 1
        logical = lines[index].strip()
        while logical.endswith("/") and index + 1 < len(lines):
            index += 1
            logical = f"{logical} {lines[index].strip()}".strip()
        yield line_number, logical
        index += 1


def _parse_headword_line(line: str) -> list[str] | None:
    """Return lowercase slash-delimited members, or ``None`` if malformed."""
    normalized = re.sub(r"/+", "/", line.strip())
    match = HEADWORD_LINE_RE.fullmatch(normalized)
    if not match:
        return None
    return [member.strip().lower() for member in match.group(1).split("/")]


def _is_exact_vesum_lemma(word: str, vesum_lookup: VesumLookup) -> bool:
    return any(str(row.get("lemma") or "") == word for row in vesum_lookup(word))


def extract_candidates(
    source: Path,
    *,
    vesum_lookup: VesumLookup = verify_word,
) -> ExtractionResult:
    """Parse, expand, deduplicate, and VESUM-gate dictionary headword groups."""
    lines = source.read_text(encoding="utf-8").splitlines()
    try:
        section_start = next(index for index, line in enumerate(lines) if line.strip() == "ПАРОНІМИ")
    except StopIteration as exc:
        raise ValueError("source does not contain the ПАРОНІМИ section") from exc

    groups: list[list[str]] = []
    malformed_groups = 0
    for _, line in _joined_candidate_lines(lines, section_start + 1):
        if "/" not in line:
            continue
        members = _parse_headword_line(line)
        if members is not None:
            groups.append(members)
        elif line[:1].isupper() and line.split("/", 1)[0].strip().upper() == line.split("/", 1)[0].strip():
            malformed_groups += 1

    raw_pairs = {
        tuple(sorted((first, second)))
        for members in groups
        for offset, first in enumerate(members)
        for second in members[offset + 1 :]
        if first != second
    }
    verified_rows: list[dict[str, str]] = []
    drops: list[Drop] = []
    for word_a, word_b in sorted(raw_pairs):
        missing = tuple(word for word in (word_a, word_b) if not _is_exact_vesum_lemma(word, vesum_lookup))
        if missing:
            drops.append(Drop(word_a, word_b, missing))
            continue
        verified_rows.append(
            {
                "relation": "paronym",
                "word_a": word_a,
                "word_b": word_b,
                "source": "grinchyshyn-1986",
                "confidence": "high",
            }
        )
    return ExtractionResult(verified_rows, len(groups), len(raw_pairs), malformed_groups, drops)


def write_output(result: ExtractionResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _report(result: ExtractionResult) -> str:
    lines = [
        f"headword_groups_found={result.groups_found}",
        f"headword_pairs_found={result.pairs_found}",
        f"vesum_passed={len(result.rows)}",
        f"dropped={len(result.drops)}",
        f"malformed_groups={result.malformed_groups}",
    ]
    for drop in result.drops[:10]:
        lines.append(f"drop={drop.word_a} / {drop.word_b}; missing_exact_lemma={','.join(drop.missing_words)}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = extract_candidates(args.source)
    write_output(result, args.output)
    print(_report(result))


if __name__ == "__main__":
    main()
