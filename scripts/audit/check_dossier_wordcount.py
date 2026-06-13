#!/usr/bin/env python3
"""Check research dossier total word count against the Phase 1 template floor.

The count is the deterministic total whitespace-delimited word count of the
file (``wc -w`` semantics), matching non-negotiable rule #1 ("Total word count
>= word_target") and the dossier template's stated range (~1500 target, 1200
floor).

It is intentionally NOT prose-stripped. The template's 1200/1500/2000 figures
are total-word figures, and the dossiers were authored against ``wc -w`` of the
whole file (frontmatter included). Prose-stripping double-discounts them: an
empirical sweep of the 137-dossier corpus showed a prose-only floor of 1200
fails 51/137 dossiers including the gold-standard exemplar mykola-kostomarov
(1147 prose / 1232 total), whereas a total-word floor of 1200 fails only the 4
genuinely-thin dossiers (979-1017 words). This is a template-floor guard, not a
readability metric.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORD_FLOOR = 1200

# Subdirs under docs/research/ that hold tooling / research notes rather than
# curriculum dossiers. Files here are exempt from the dossier word-count floor.
# Real dossiers live under a track-named subdir (docs/research/{track}/{slug}.md).
_NON_DOSSIER_RESEARCH_SUBDIRS = frozenset({"atlas", "lexicon"})


@dataclass(frozen=True)
class DossierCount:
    path: Path
    words: int

    @property
    def passed(self) -> bool:
        return self.words >= WORD_FLOOR


def count_words(path: Path) -> int:
    """Total whitespace-delimited word count of the file (wc -w semantics)."""
    return len(path.read_text(encoding="utf-8").split())


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _repo_relative(path: Path) -> Path | None:
    absolute = path if path.is_absolute() else PROJECT_ROOT / path
    try:
        return absolute.resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return None


def _is_research_dossier(path: Path) -> bool:
    relative = _repo_relative(path)
    if relative is None or path.suffix != ".md":
        return False
    if len(relative.parts) < 3 or relative.parts[:2] != ("docs", "research"):
        return False
    # Curriculum dossiers live under a track-named subdir (docs/research/{track}/).
    # Other docs/research/ subdirs hold tooling / research notes that are NOT
    # subject to the 1200-word dossier floor — exclude them so editing e.g. an
    # Atlas calque-triage note doesn't trip the dossier gate.
    return relative.parts[2] not in _NON_DOSSIER_RESEARCH_SUBDIRS


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    cwd_path = path.resolve()
    if cwd_path.exists():
        return cwd_path
    return PROJECT_ROOT / path


def changed_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=AM", "origin/main...HEAD"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        raise SystemExit(result.returncode)
    return [PROJECT_ROOT / line for line in result.stdout.splitlines() if line]


def _dedupe(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    deduped: list[Path] = []
    for path in paths:
        resolved = _resolve_path(path)
        key = resolved.resolve()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(resolved)
    return deduped


def collect_paths(args: argparse.Namespace) -> list[Path]:
    paths = [_resolve_path(path) for path in args.paths]
    if args.changed:
        paths.extend(changed_paths())
    return [
        path
        for path in _dedupe(paths)
        if _is_research_dossier(path) and path.exists() and path.is_file()
    ]


def print_report(counts: list[DossierCount]) -> None:
    if not counts:
        print("No docs/research dossier files to check.")
        return

    file_width = max(len(_display_path(item.path)) for item in counts)
    print(f"Dossier word-count floor: {WORD_FLOOR}")
    print(f"{'file':<{file_width}}  {'words':>5}  {'floor':>5}  status")
    print("-" * (file_width + 25))
    for item in counts:
        status = "PASS" if item.passed else "FAIL"
        print(
            f"{_display_path(item.path):<{file_width}}  "
            f"{item.words:>5}  {WORD_FLOOR:>5}  {status}"
        )

    failures = [item for item in counts if not item.passed]
    if failures:
        print()
        print(f"{len(failures)} dossier(s) below the {WORD_FLOOR}-word floor.")
    else:
        print()
        print(f"All checked dossiers meet the {WORD_FLOOR}-word floor.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check docs/research dossier total word counts against the template floor.",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        type=Path,
        default=[],
        metavar="PATH",
        help="One or more dossier markdown files to check.",
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Check changed dossier files from git diff origin/main...HEAD.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.paths and not args.changed:
        parser.error("provide --paths or --changed")

    counts = [DossierCount(path=path, words=count_words(path)) for path in collect_paths(args)]
    print_report(counts)
    return 1 if any(not item.passed for item in counts) else 0


if __name__ == "__main__":
    sys.exit(main())
