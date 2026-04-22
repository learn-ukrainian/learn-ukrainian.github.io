#!/usr/bin/env python3
"""Deterministically strip L2-English-learner framing from A1/A2 wiki articles."""

from __future__ import annotations

import argparse
import glob
import re
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "audit" / "phase-2c-wiki-strip" / "report.md"
WIKI_META_START = "<!-- wiki-meta"

SECTION_TITLE_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")
TABLE_DIVIDER_RE = re.compile(r"^\|\s*:?[-]{3,}")
LIST_PREFIX_RE = re.compile(r"^(?P<prefix>\s*(?:[-*+]\s+|\d+\.\s+))(?=\S)")

SECTION_TITLE_PATTERNS = (
    re.compile(r"\bl2\b", re.IGNORECASE),
    re.compile(r"англомовн", re.IGNORECASE),
    re.compile(r"english learners?", re.IGNORECASE),
    re.compile(r"english speakers?", re.IGNORECASE),
)

SENTENCE_FRAGMENT_PATTERNS = (
    re.compile(r"англомовн", re.IGNORECASE),
    re.compile(r"англійськомовн", re.IGNORECASE),
    re.compile(r"англомовній аудитор", re.IGNORECASE),
    re.compile(r"\bl2[-\s]?(?:учн|аудитор|learner)", re.IGNORECASE),
    re.compile(r"english speakers?\s+often", re.IGNORECASE),
    re.compile(r"native english speakers?", re.IGNORECASE),
    re.compile(r"english learners?", re.IGNORECASE),
    re.compile(r"for english speakers?", re.IGNORECASE),
    re.compile(r"unlike in english", re.IGNORECASE),
    re.compile(r"на відміну від англій", re.IGNORECASE),
    re.compile(r"учні з англійської мови", re.IGNORECASE),
)

EXPLICIT_COMPARISON_PATTERNS = (
    re.compile(r"english\s+vs\.?\s+ukrain", re.IGNORECASE),
    re.compile(r"ukrain(?:ian)?\s+vs\.?\s+english", re.IGNORECASE),
    re.compile(r"англій\w*\s+vs\.?\s+україн", re.IGNORECASE),
    re.compile(r"україн\w*\s+vs\.?\s+англій", re.IGNORECASE),
    re.compile(r"порівнян\w*.*англій\w*.*україн", re.IGNORECASE),
)


@dataclass(frozen=True)
class FileStats:
    path: Path
    sections_removed: int
    sentences_removed: int
    tables_removed: int
    before_chars: int
    after_chars: int
    changed: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "targets",
        nargs="+",
        help="Wiki file/dir/glob targets. Literal ** globs are supported.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without rewriting files.",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Write a markdown summary report.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help=f"Report destination (default: {DEFAULT_REPORT_PATH.relative_to(PROJECT_ROOT)})",
    )
    return parser.parse_args()


def expand_targets(raw_targets: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for raw_target in raw_targets:
        candidate = Path(raw_target)
        matched: list[Path] = []
        if candidate.exists():
            matched = [candidate]
        else:
            matched = [Path(value) for value in glob.glob(raw_target, recursive=True)]

        for path in matched:
            resolved = path.resolve()
            if resolved.is_dir():
                paths.update(
                    file_path
                    for file_path in resolved.rglob("*.md")
                    if ".reviews" not in file_path.parts
                )
            elif resolved.suffix == ".md":
                paths.add(resolved)

    return sorted(paths)


def matches_section_title(title: str) -> bool:
    normalized = title.strip()
    return any(pattern.search(normalized) for pattern in SECTION_TITLE_PATTERNS)


def matches_sentence_fragment(text: str) -> bool:
    return any(pattern.search(text) for pattern in SENTENCE_FRAGMENT_PATTERNS)


def normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def row_cells(row: str) -> list[str]:
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def is_explicit_english_ukrainian_table(header_row: str) -> bool:
    normalized = normalize_text(header_row)
    if any(pattern.search(normalized) for pattern in EXPLICIT_COMPARISON_PATTERNS):
        return True

    cells = row_cells(header_row)
    if not cells:
        return False

    first = normalize_text(cells[0])
    return any(pattern.search(first) for pattern in EXPLICIT_COMPARISON_PATTERNS)


def split_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    start = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char not in ".!?":
            index += 1
            continue

        lookahead = index + 1
        while lookahead < len(text) and text[lookahead] in "\"')]*_`”’":
            lookahead += 1
        if lookahead < len(text) and not text[lookahead].isspace():
            index += 1
            continue

        next_index = lookahead
        while next_index < len(text) and text[next_index].isspace():
            next_index += 1

        if next_index < len(text) and text[next_index].islower():
            index += 1
            continue

        sentences.append(text[start:next_index])
        start = next_index
        index = next_index

    if start < len(text):
        sentences.append(text[start:])
    return sentences if sentences else [text]


def strip_sentence_fragments_from_line(line: str) -> tuple[str, int]:
    if not line.strip():
        return line, 0
    if line.lstrip().startswith(("#", "|", "<!--", "```")):
        return line, 0

    prefix_match = LIST_PREFIX_RE.match(line)
    prefix = prefix_match.group("prefix") if prefix_match else ""
    content = line[len(prefix) :] if prefix else line
    sentences = split_sentences(content)
    kept_sentences = [sentence for sentence in sentences if not matches_sentence_fragment(sentence)]
    removed = len(sentences) - len(kept_sentences)
    if removed == 0:
        return line, 0
    if not kept_sentences:
        return "", removed

    rebuilt = "".join(kept_sentences).strip()
    if not rebuilt:
        return "", removed
    return f"{prefix}{rebuilt}", removed


def strip_l2_sections(lines: list[str]) -> tuple[list[str], int]:
    kept_lines: list[str] = []
    sections_removed = 0
    skip_section = False

    for line in lines:
        match = SECTION_TITLE_RE.match(line)
        if match:
            title = match.group("title").strip()
            if matches_section_title(title):
                skip_section = True
                sections_removed += 1
                continue
            skip_section = False

        if skip_section:
            continue
        kept_lines.append(line)

    return kept_lines, sections_removed


def strip_explicit_english_tables(lines: list[str]) -> tuple[list[str], int]:
    kept_lines: list[str] = []
    tables_removed = 0
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith("|"):
            kept_lines.append(line)
            index += 1
            continue

        table_start = index
        table_end = index
        while table_end < len(lines) and lines[table_end].startswith("|"):
            table_end += 1

        header_line = lines[table_start]
        divider_line = lines[table_start + 1] if table_start + 1 < table_end else ""
        if TABLE_DIVIDER_RE.match(divider_line) and is_explicit_english_ukrainian_table(header_line):
            caption_index = None
            previous_index = len(kept_lines) - 1
            if previous_index >= 0:
                previous_line = kept_lines[previous_index]
                if (
                    previous_line.strip()
                    and not previous_line.lstrip().startswith(("#", "|", "<!--"))
                    and any(
                        pattern.search(normalize_text(previous_line))
                        for pattern in EXPLICIT_COMPARISON_PATTERNS
                    )
                ):
                    caption_index = previous_index
            if caption_index is not None:
                kept_lines.pop(caption_index)
            tables_removed += 1
            index = table_end
            continue

        kept_lines.extend(lines[table_start:table_end])
        index = table_end

    return kept_lines, tables_removed


def normalize_blank_lines(text: str) -> str:
    normalized = re.sub(r"\n{3,}", "\n\n", text.rstrip())
    return normalized + "\n"


def process_article(original_text: str) -> tuple[str, int, int, int]:
    lines = original_text.splitlines()
    lines, sections_removed = strip_l2_sections(lines)
    lines, tables_removed = strip_explicit_english_tables(lines)

    sentence_lines: list[str] = []
    sentences_removed = 0
    in_meta_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(WIKI_META_START):
            in_meta_block = True
            sentence_lines.append(line)
            continue
        if in_meta_block:
            sentence_lines.append(line)
            if stripped == "-->":
                in_meta_block = False
            continue

        updated_line, removed = strip_sentence_fragments_from_line(line)
        sentences_removed += removed
        if updated_line or not line.strip():
            sentence_lines.append(updated_line)

    updated_text = normalize_blank_lines("\n".join(sentence_lines))
    return updated_text, sections_removed, sentences_removed, tables_removed


def render_report(stats: list[FileStats]) -> str:
    changed = [item for item in stats if item.changed]
    totals = {
        "files_changed": len(changed),
        "sections_removed": sum(item.sections_removed for item in changed),
        "sentences_removed": sum(item.sentences_removed for item in changed),
        "tables_removed": sum(item.tables_removed for item in changed),
        "before_chars": sum(item.before_chars for item in changed),
        "after_chars": sum(item.after_chars for item in changed),
    }

    lines = [
        "# Phase 2C Wiki Strip Report",
        "",
        f"Files scanned: {len(stats)}",
        f"Files changed: {totals['files_changed']}",
        "",
        "| File | Sections removed | Sentences removed | Tables removed | Chars before | Chars after |",
        "| :--- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for item in changed:
        relative_path = item.path.relative_to(PROJECT_ROOT)
        lines.append(
            f"| `{relative_path}` | {item.sections_removed} | {item.sentences_removed} | "
            f"{item.tables_removed} | {item.before_chars} | {item.after_chars} |"
        )

    lines.extend(
        [
            "",
            "## Totals",
            "",
            f"- Sections removed: {totals['sections_removed']}",
            f"- Sentences removed: {totals['sentences_removed']}",
            f"- Tables removed: {totals['tables_removed']}",
            f"- Characters removed: {totals['before_chars'] - totals['after_chars']}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    article_paths = expand_targets(args.targets)
    if not article_paths:
        raise SystemExit("No markdown files matched the supplied targets.")

    stats: list[FileStats] = []
    for article_path in article_paths:
        original_text = article_path.read_text(encoding="utf-8")
        updated_text, sections_removed, sentences_removed, tables_removed = process_article(original_text)
        changed = updated_text != original_text
        stats.append(
            FileStats(
                path=article_path,
                sections_removed=sections_removed,
                sentences_removed=sentences_removed,
                tables_removed=tables_removed,
                before_chars=len(original_text),
                after_chars=len(updated_text),
                changed=changed,
            )
        )

        if changed and not args.dry_run:
            article_path.write_text(updated_text, encoding="utf-8")

        if changed:
            relative_path = article_path.relative_to(PROJECT_ROOT)
            action = "WOULD CHANGE" if args.dry_run else "UPDATED"
            print(
                f"{action} {relative_path}: sections={sections_removed}, "
                f"sentences={sentences_removed}, tables={tables_removed}, "
                f"chars={len(original_text)}->{len(updated_text)}"
            )

    if args.report:
        args.report_path.parent.mkdir(parents=True, exist_ok=True)
        args.report_path.write_text(render_report(stats), encoding="utf-8")
        print(f"REPORT {args.report_path.relative_to(PROJECT_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
