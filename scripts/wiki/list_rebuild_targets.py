#!/usr/bin/env python3
"""Enumerate wikis that benefit from a #1553 re-chunked-retrieval rebuild.

A wiki is a "rebuild candidate" if its ``.sources.yaml`` references at
least one source from a corpus whose chunking policy changed in step 1
of the #1553 overhaul (``textbook_sections``, ``external``, ``wikipedia``).
Wikis that pull only from ``literary`` / ``ukrainian_wiki`` / ``folk``
have NO_CHUNK policies — their embeddings are bit-identical post-step-1,
so re-compiling produces the same retrieval -> same output.

Used by step 7 of the wiki retrieval overhaul. Pipe the output into
the wiki compile pipeline; skip wikis NOT in this list to save Gemini
compute.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterator
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WIKI_DIR = PROJECT_ROOT / "wiki"

# Corpora whose chunk_policy_version flipped in #1553 step 1. Sources
# from these corpora will have stale embeddings until re-encode (step
# 6) lands; wikis referencing them get a retrieval-quality lift on
# rebuild (step 7).
RECHUNKED_CORPORA = {"textbook_sections", "external", "wikipedia"}

# Source-file prefixes that map to each corpus. The dataset uses
# multiple naming conventions historically; this is the union.
_TEXTBOOK_PREFIXES: tuple[str, ...] = ("textbook",)
_TEXTBOOK_REGEX = re.compile(r"^\d+-klas-ukrmova-")
_TEXTBOOK_S_REGEX = re.compile(r"_s\d+$")
_WIKIPEDIA_PREFIXES: tuple[str, ...] = ("wikipedia/", "wikipedia:")
_EXTERNAL_PREFIXES: tuple[str, ...] = ("ext-",)
_LITERARY_PREFIXES: tuple[str, ...] = ("wave", "ukrlib")
_UKRWIKI_PREFIXES: tuple[str, ...] = ("ukrainian_wiki",)
_FOLK_PREFIXES: tuple[str, ...] = ("folk",)


def classify_source(file: str) -> str:
    """Return the corpus a source file belongs to, or ``"unknown"``."""

    if file.startswith(_TEXTBOOK_PREFIXES) or _TEXTBOOK_REGEX.match(file):
        return "textbook_sections"
    if file.startswith(_WIKIPEDIA_PREFIXES):
        return "wikipedia"
    if file.startswith(_EXTERNAL_PREFIXES) or "external" in file:
        return "external"
    if file.startswith(_UKRWIKI_PREFIXES):
        return "ukrainian_wiki"
    if file.startswith(_LITERARY_PREFIXES) or "literary" in file:
        return "literary"
    if file.startswith(_FOLK_PREFIXES):
        return "folk"
    # Numeric grade prefix without "klas-ukrmova-" (e.g. "11-2-...") —
    # almost always textbook in this project; classify as such.
    if _TEXTBOOK_S_REGEX.search(file) or re.match(r"^\d+-", file):
        return "textbook_sections"
    return "unknown"


def iter_wiki_sources(wiki_dir: Path) -> Iterator[tuple[Path, list[str]]]:
    """Yield ``(wiki_md_path, [source_corpora])`` for every wiki with a
    ``.sources.yaml`` registry."""

    for sources_yaml in wiki_dir.rglob("*.sources.yaml"):
        try:
            with sources_yaml.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except Exception as exc:  # pragma: no cover — defensive
            print(f"[warn] failed to parse {sources_yaml}: {exc}", file=sys.stderr)
            continue
        wiki_md = sources_yaml.with_suffix("").with_suffix(".md")
        # ".sources.yaml" doubles up suffix removal; recompute.
        wiki_md = sources_yaml.parent / sources_yaml.name.replace(".sources.yaml", ".md")
        sources = data.get("sources") or []
        corpora = [classify_source(str(src.get("file", ""))) for src in sources]
        yield wiki_md, corpora


def is_rebuild_candidate(corpora: list[str]) -> bool:
    """A wiki is a rebuild candidate iff it references at least one
    re-chunked corpus."""

    return any(corpus in RECHUNKED_CORPORA for corpus in corpora)


def is_high_priority(corpora: list[str]) -> bool:
    """High priority: re-chunked corpora are >=50% of the source mix."""

    if not corpora:
        return False
    rechunked = sum(1 for corpus in corpora if corpus in RECHUNKED_CORPORA)
    return rechunked / len(corpora) >= 0.5


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "List wikis that need a rebuild after the #1553 chunking "
            "overhaul. By default prints every rebuild candidate; use "
            "--high-priority to narrow to the wikis where re-chunked "
            "corpora dominate the source mix."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/wiki/list_rebuild_targets.py\n"
            "  .venv/bin/python scripts/wiki/list_rebuild_targets.py --high-priority\n"
            "  .venv/bin/python scripts/wiki/list_rebuild_targets.py --skipped > skipped.txt\n"
            "\n"
            "Outputs:\n"
            "  Stdout: one path per line, relative to the project root.\n"
            "\n"
            "Exit codes:\n"
            "  0  always (even if zero candidates).\n"
            "\n"
            "Related:\n"
            "  Issue: #1553 (wiki retrieval overhaul)\n"
            "  Step 7 (full wiki rebuild) consumes this list.\n"
        ),
    )
    parser.add_argument(
        "--wiki-dir",
        type=Path,
        default=WIKI_DIR,
        help=f"Override the wiki/ directory. Default: {WIKI_DIR}",
    )
    parser.add_argument(
        "--high-priority",
        action="store_true",
        help=(
            "Restrict to wikis where re-chunked corpora are >=50%% of the "
            "source mix. Use for incremental rebuilds when budget is tight."
        ),
    )
    parser.add_argument(
        "--skipped",
        action="store_true",
        help=(
            "Inverse: print wikis that do NOT need a rebuild (only "
            "NO_CHUNK corpora). Used for sanity-check / coverage audit."
        ),
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print only the count summary, not individual paths.",
    )
    args = parser.parse_args(argv)

    rebuild = []
    high_priority = []
    skipped = []
    for wiki_md, corpora in iter_wiki_sources(args.wiki_dir):
        if not corpora:
            skipped.append(wiki_md)
            continue
        if is_rebuild_candidate(corpora):
            rebuild.append(wiki_md)
            if is_high_priority(corpora):
                high_priority.append(wiki_md)
        else:
            skipped.append(wiki_md)

    if args.summary:
        print(f"Total wikis with sources.yaml: {len(rebuild) + len(skipped)}")
        print(f"Rebuild candidates: {len(rebuild)}")
        print(f"  of which high-priority (>=50% rechunked): {len(high_priority)}")
        print(f"Skipped (NO_CHUNK only): {len(skipped)}")
        return 0

    if args.skipped:
        targets = skipped
    elif args.high_priority:
        targets = high_priority
    else:
        targets = rebuild

    for path in sorted(targets):
        print(path.relative_to(PROJECT_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
