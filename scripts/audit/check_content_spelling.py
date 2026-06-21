#!/usr/bin/env python3
"""Advisory content spell gate backed by local VESUM forms.

This gate reports Ukrainian surface forms in built MDX content that are not
present in ``data/vesum.db``. An unrecognized form is only a spelling warning:
it may be a typo, a proper name, or a valid form absent from VESUM.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPT_DIR) in sys.path:
    sys.path.remove(str(SCRIPT_DIR))
for import_root in (SCRIPTS_DIR, PROJECT_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts.lexicon import content_lexicon_reconciler as reconciler


@dataclass(frozen=True)
class SpellingExample:
    """One unrecognized surface form plus the first deterministic source line."""

    form: str
    example_source: Path
    example_line: str


@dataclass(frozen=True)
class SpellingResult:
    """Spell-gate result data with count helpers for output formats."""

    files_scanned: int
    unique_forms: tuple[str, ...]
    unrecognized_forms: tuple[SpellingExample, ...]

    @property
    def summary(self) -> dict[str, int]:
        return {
            "files_scanned": self.files_scanned,
            "unique_forms": len(self.unique_forms),
            "unrecognized": len(self.unrecognized_forms),
        }


def check_content_spelling(
    paths: Sequence[Path],
    *,
    vesum_lookup: reconciler.VesumLookup = reconciler.verify_words,
) -> SpellingResult:
    """Return unique Ukrainian forms not found in the VESUM ``forms`` table."""
    source_by_form = reconciler.collect_forms(paths)
    forms = tuple(sorted(source_by_form))
    matches_by_form = reconciler.lemmatize_forms(forms, vesum_lookup=vesum_lookup)
    example_lines = _collect_first_example_lines(paths)

    unrecognized = tuple(
        SpellingExample(
            form=form,
            example_source=source_by_form[form],
            example_line=example_lines.get((form, source_by_form[form]), ""),
        )
        for form in forms
        if not matches_by_form.get(form)
    )

    return SpellingResult(
        files_scanned=len(paths),
        unique_forms=forms,
        unrecognized_forms=tuple(
            sorted(
                unrecognized,
                key=lambda item: (_display_path(item.example_source, PROJECT_ROOT), item.form),
            )
        ),
    )


def result_to_json_payload(
    result: SpellingResult,
    *,
    limit: int | None = None,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    """Return a machine-readable spelling report payload."""
    unrecognized = _limit_sequence(result.unrecognized_forms, limit)
    return {
        "summary": result.summary,
        "unrecognized_forms": [
            {
                "form": item.form,
                "example_source": _display_path(item.example_source, project_root),
                "example_line": item.example_line,
            }
            for item in unrecognized
        ],
        "grouped_by_file": [
            {
                "source": source,
                "forms": [
                    {
                        "form": item.form,
                        "example_line": item.example_line,
                    }
                    for item in items
                ],
            }
            for source, items in _group_by_file(unrecognized, project_root).items()
        ],
        "limit": limit,
        "truncated": {
            "unrecognized_forms": limit is not None
            and len(result.unrecognized_forms) > len(unrecognized),
        },
    }


def format_human_summary(
    result: SpellingResult,
    *,
    limit: int | None = None,
    project_root: Path = PROJECT_ROOT,
) -> str:
    """Format an advisory spelling report grouped by source file."""
    summary = result.summary
    lines = [
        "Content spelling gate",
        f"Files scanned: {summary['files_scanned']}",
        f"Unique Ukrainian forms: {summary['unique_forms']}",
        f"Unrecognized forms: {summary['unrecognized']}",
        "",
        "Potential misspellings:",
    ]

    unrecognized = _limit_sequence(result.unrecognized_forms, limit)
    if unrecognized:
        for source, items in _group_by_file(unrecognized, project_root).items():
            lines.append(f"- {source}")
            for item in items:
                lines.append(f"  - {item.form}: {item.example_line}")
        lines.extend(
            _truncation_lines(
                len(result.unrecognized_forms),
                len(unrecognized),
                "unrecognized forms",
            )
        )
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "Advisory mode: unrecognized forms are warnings, not definitive typos.",
            "Use --strict to return non-zero when unrecognized forms are present.",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report Ukrainian content forms not recognized by local VESUM."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")
    parser.add_argument("--limit", type=int, help="Limit listed unrecognized examples")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any unrecognized forms are found",
    )
    parser.add_argument(
        "--changed-vs-base",
        metavar="BASE",
        help="Only scan content MDX changed against BASE, including local edits",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    vesum_lookup: reconciler.VesumLookup = reconciler.verify_words,
    paths: Sequence[Path] | None = None,
    project_root: Path = PROJECT_ROOT,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be non-negative")

    resolved_paths = list(paths) if paths is not None else _resolve_content_paths(args.changed_vs_base)

    try:
        result = check_content_spelling(resolved_paths, vesum_lookup=vesum_lookup)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(
            json.dumps(
                result_to_json_payload(result, limit=args.limit, project_root=project_root),
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(format_human_summary(result, limit=args.limit, project_root=project_root))

    return 1 if args.strict and result.unrecognized_forms else 0


def _resolve_content_paths(base: str | None) -> list[Path]:
    if base:
        return reconciler.changed_content_mdx_paths(base)
    return reconciler.discover_content_mdx_paths()


def _collect_first_example_lines(paths: Sequence[Path]) -> dict[tuple[str, Path], str]:
    examples: dict[tuple[str, Path], str] = {}
    for path in sorted(paths):
        prose = reconciler.strip_mdx_to_prose(path.read_text(encoding="utf-8"))
        for line in prose.splitlines():
            example_line = " ".join(line.strip().split())
            if not example_line:
                continue
            for token in reconciler.extract_ukrainian_tokens(line):
                examples.setdefault((token, path), example_line)
    return examples


def _group_by_file(
    items: Sequence[SpellingExample],
    project_root: Path,
) -> dict[str, list[SpellingExample]]:
    grouped: dict[str, list[SpellingExample]] = defaultdict(list)
    for item in items:
        grouped[_display_path(item.example_source, project_root)].append(item)
    return dict(grouped)


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def _limit_sequence[T](items: Sequence[T], limit: int | None) -> Sequence[T]:
    if limit is None:
        return items
    return items[:limit]


def _truncation_lines(total: int, shown: int, label: str) -> list[str]:
    if shown >= total:
        return []
    return [f"... {total - shown} more {label} not shown"]


if __name__ == "__main__":
    raise SystemExit(main())
