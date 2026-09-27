#!/usr/bin/env python3
"""Census lesson links to Word Atlas pages against the published client-shell data.

The word-page client shell (``WordAtlasClientShell`` + ``preflightAtlasSlugInSearchIndex``)
shows "Word not found" when the percent-decoded NFC slug is absent from
``lexicon-search-index.json`` field ``s``. Alias rows live in
``lexicon-search-aliases.json`` (``a`` → ``s``) and are not pages themselves.

This census is the independent oracle for those two files. It does not import
``scripts.generate_mdx`` and it does not call ``atlas_href_for``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import urllib.parse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCS = ROOT / "site" / "src" / "content" / "docs"
DEFAULT_SEARCH_INDEX = ROOT / "site" / "src" / "data" / "lexicon-search-index.json"
DEFAULT_ALIASES = ROOT / "site" / "src" / "data" / "lexicon-search-aliases.json"

ENTRY = "entry"
ALIAS = "alias"
AMBIGUOUS = "ambiguous"
DEAD = "dead"
CLASSES = (ENTRY, ALIAS, AMBIGUOUS, DEAD)
BLOCKING = frozenset({AMBIGUOUS, DEAD})

_BAD_PERCENT_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_LEXICON_TARGET_RE = re.compile(r"/lexicon/([^/\"'`\\\s<>]+)/")
_ATLAS_HREF_RE = re.compile(r'"atlas_href"\s*:\s*"((?:\\.|[^"\\])*)"')
_WORD_RE = re.compile(r'"word"\s*:\s*"((?:\\.|[^"\\])*)"')
_ATLAS_FIELD_WITH_FOLLOWING_COMMA = re.compile(r'"atlas_href"\s*:\s*"(?:\\.|[^"\\])*"\s*,')
_ATLAS_FIELD_WITH_PRECEDING_COMMA = re.compile(r',\s*"atlas_href"\s*:\s*"(?:\\.|[^"\\])*"')
_ATLAS_FIELD = re.compile(r'"atlas_href"\s*:\s*"(?:\\.|[^"\\])*"')
_WORD_LOOKBACK = 4000


@dataclass(frozen=True)
class PublishedCatalog:
    """Published entry keys and alias targets the client shell ships.

    ``entries`` are search-index ``s`` values, compared exactly. ``aliases``
    maps an NFC alias string to every target slug published for it.
    """

    entries: frozenset[str]
    aliases: dict[str, frozenset[str]]

    def classify(self, slug: str) -> str:
        """Classify one already-decoded NFC slug."""
        if slug in self.entries:
            return ENTRY
        published = self.aliases.get(slug, frozenset()) & self.entries
        if len(published) == 1:
            return ALIAS
        if len(published) > 1:
            return AMBIGUOUS
        return DEAD


@dataclass(frozen=True)
class LinkHit:
    path: str
    level: str
    slug: str
    classification: str
    kind: str
    word: str = ""


def decode_lexicon_slug(raw: str) -> str | None:
    """Percent-decode and NFC-normalise a ``/lexicon/<slug>/`` path segment.

    Mirrors ``parseLexiconArticleSlug``: malformed ``%`` escapes do not decode.
    """
    if _BAD_PERCENT_ESCAPE.search(raw):
        return None
    try:
        decoded = urllib.parse.unquote(raw, errors="strict")
    except UnicodeDecodeError:
        return None
    slug = unicodedata.normalize("NFC", decoded)
    if not slug or slug != slug.strip() or "/" in slug or "\\" in slug or "\0" in slug:
        return None
    return slug


def _read_json_list(path: Path) -> list:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    return data


def load_published_catalog(search_index_path: Path, aliases_path: Path) -> PublishedCatalog:
    """Load the search index and alias file the client shell fetches."""
    entries: set[str] = set()
    for row in _read_json_list(search_index_path):
        if isinstance(row, dict) and isinstance(row.get("s"), str) and row["s"]:
            entries.add(row["s"])
    entry_set = frozenset(entries)

    grouped: dict[str, set[str]] = {}
    for row in _read_json_list(aliases_path):
        if not isinstance(row, dict):
            continue
        alias = row.get("a")
        target = row.get("s")
        if not isinstance(alias, str) or not isinstance(target, str) or not alias or not target:
            continue
        key = unicodedata.normalize("NFC", alias)
        grouped.setdefault(key, set()).add(target)
    aliases = {key: frozenset(values) for key, values in grouped.items()}
    return PublishedCatalog(entries=entry_set, aliases=aliases)


def _json_string(raw: str) -> str:
    try:
        value = json.loads(f'"{raw}"')
    except json.JSONDecodeError:
        return raw
    return value if isinstance(value, str) else raw


def _level_for(path: Path, docs_root: Path) -> str:
    relative = path.relative_to(docs_root)
    if len(relative.parts) == 1:
        return "(root)"
    return relative.parts[0]


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _classify_raw(catalog: PublishedCatalog, raw_slug: str) -> tuple[str, str]:
    slug = decode_lexicon_slug(raw_slug)
    if slug is None:
        return raw_slug, DEAD
    return slug, catalog.classify(slug)


def iter_lesson_hits(docs_root: Path, catalog: PublishedCatalog) -> list[LinkHit]:
    """Extract and classify every lesson ``/lexicon/<slug>/`` target.

    ``kind="atlas_href"`` hits are the VocabCard field the gate checks.
    ``kind="lexicon"`` hits are every ``/lexicon/<slug>/`` occurrence,
    including those ``atlas_href`` values.
    """
    hits: list[LinkHit] = []
    for path in sorted(docs_root.rglob("*.mdx")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        level = _level_for(path, docs_root)
        rel = _relative(path)
        for match in _LEXICON_TARGET_RE.finditer(text):
            slug, classification = _classify_raw(catalog, match.group(1))
            hits.append(LinkHit(rel, level, slug, classification, "lexicon"))
        for match in _ATLAS_HREF_RE.finditer(text):
            href = _json_string(match.group(1))
            target = _LEXICON_TARGET_RE.search(href)
            raw_slug = target.group(1) if target else href
            slug, classification = _classify_raw(catalog, raw_slug)
            window = text[max(0, match.start() - _WORD_LOOKBACK): match.start()]
            words = list(_WORD_RE.finditer(window))
            word = _json_string(words[-1].group(1)) if words else ""
            hits.append(LinkHit(rel, level, slug, classification, "atlas_href", word))
    return hits


def blocking_atlas_hrefs(docs_root: Path, catalog: PublishedCatalog) -> list[LinkHit]:
    """Lesson ``atlas_href`` values the gate rejects: dead or ambiguous."""
    return [
        hit
        for hit in iter_lesson_hits(docs_root, catalog)
        if hit.kind == "atlas_href" and hit.classification in BLOCKING
    ]


def mask_atlas_href_fields(text: str) -> str:
    """Drop ``atlas_href`` JSON fields so a regen diff can ignore link edits.

    Value changes, added fields, and removed fields all disappear. Any other
    character change remains.
    """
    stripped = _ATLAS_FIELD_WITH_FOLLOWING_COMMA.sub("", text)
    stripped = _ATLAS_FIELD_WITH_PRECEDING_COMMA.sub("", stripped)
    return _ATLAS_FIELD.sub("", stripped)


def _counts(hits: list[LinkHit]) -> dict[str, int]:
    counts = {name: 0 for name in CLASSES}
    for hit in hits:
        counts[hit.classification] += 1
    return counts


def _unique_counts(hits: list[LinkHit]) -> dict[str, int]:
    seen: dict[str, set[str]] = {name: set() for name in CLASSES}
    for hit in hits:
        seen[hit.classification].add(hit.slug)
    return {name: len(slugs) for name, slugs in seen.items()}


def _examples(hits: list[LinkHit], limit: int) -> list[str]:
    grouped: dict[tuple[str, str], list[LinkHit]] = defaultdict(list)
    for hit in hits:
        grouped[(hit.classification, hit.slug)].append(hit)
    lines: list[str] = []
    for classification in CLASSES:
        ranked = sorted(
            ((slug, group) for (kind, slug), group in grouped.items() if kind == classification),
            key=lambda item: (-len(item[1]), item[0]),
        )
        if not ranked:
            continue
        lines.append(f"{classification}:")
        for slug, group in ranked[:limit]:
            first = group[0]
            word = f" word={first.word}" if first.word else ""
            lines.append(
                f"  /lexicon/{slug}/  ×{len(group)}  {first.path}{word}"
            )
        remaining = len(ranked) - limit
        if remaining > 0:
            lines.append(f"  … {remaining} more unique {classification} slugs")
    return lines


def _level_table(hits: list[LinkHit], files_by_level: dict[str, int]) -> list[str]:
    by_level: dict[str, list[LinkHit]] = defaultdict(list)
    for hit in hits:
        by_level[hit.level].append(hit)
    levels = sorted(set(files_by_level) | set(by_level))
    lines = ["level        files  entry  alias  ambiguous   dead   unique"]
    for level in levels:
        group = by_level.get(level, [])
        counts = _counts(group)
        unique = len({hit.slug for hit in group})
        lines.append(
            f"{level:<12} {files_by_level.get(level, 0):5} "
            f"{counts[ENTRY]:6} {counts[ALIAS]:6} {counts[AMBIGUOUS]:10} "
            f"{counts[DEAD]:6} {unique:8}"
        )
    return lines


def _files_by_level(docs_root: Path) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for path in docs_root.rglob("*.mdx"):
        if path.is_file():
            counts[_level_for(path, docs_root)] += 1
    return dict(counts)


def format_report(
    docs_root: Path,
    catalog: PublishedCatalog,
    hits: list[LinkHit],
    *,
    examples: int,
) -> str:
    atlas_hits = [hit for hit in hits if hit.kind == "atlas_href"]
    lexicon_hits = [hit for hit in hits if hit.kind == "lexicon"]
    ambiguous_alias_keys = sum(
        1
        for targets in catalog.aliases.values()
        if len(targets & catalog.entries) > 1
    )
    atlas_counts = _counts(atlas_hits)
    atlas_unique = _unique_counts(atlas_hits)
    lexicon_counts = _counts(lexicon_hits)
    lexicon_unique = _unique_counts(lexicon_hits)
    files = _files_by_level(docs_root)

    lines = [
        "Lesson → Word Atlas link census",
        f"docs: {docs_root}",
        f"published entries (search-index s): {len(catalog.entries)}",
        f"alias keys: {len(catalog.aliases)}  ambiguous alias keys: {ambiguous_alias_keys}",
        f"mdx files: {sum(files.values())}",
        "",
        "atlas_href (VocabCard field; gate denominator)",
        (
            f"  occurrences: {len(atlas_hits)}  "
            f"unique slugs: {len({hit.slug for hit in atlas_hits})}"
        ),
    ]
    for name in CLASSES:
        lines.append(
            f"  {name:<10} occurrences {atlas_counts[name]:6}   unique {atlas_unique[name]:6}"
        )
    lines.extend([
        "",
        "all /lexicon/<slug>/ targets (includes atlas_href)",
        (
            f"  occurrences: {len(lexicon_hits)}  "
            f"unique slugs: {len({hit.slug for hit in lexicon_hits})}"
        ),
    ])
    for name in CLASSES:
        lines.append(
            f"  {name:<10} occurrences {lexicon_counts[name]:6}   unique {lexicon_unique[name]:6}"
        )
    lines.extend(["", "atlas_href by level"])
    lines.extend(_level_table(atlas_hits, files))
    lines.extend(["", "all /lexicon/ targets by level"])
    lines.extend(_level_table(lexicon_hits, files))
    lines.extend(["", f"atlas_href examples (up to {examples} unique slugs per class, most frequent first)"])
    lines.extend(_examples(atlas_hits, examples) or ["  (none)"])
    lines.extend(["", f"all /lexicon/ examples (up to {examples} unique slugs per class)"])
    lines.extend(_examples(lexicon_hits, examples) or ["  (none)"])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scripts/lexicon/lesson_atlas_link_census.py",
        description=(
            "Classify every committed lesson /lexicon/<slug>/ target as a published entry, "
            "a unique alias, an ambiguous alias, or dead.\n"
            "Use it to measure lesson→Atlas link health (#8734). Do NOT use it to generate "
            "or rewrite links (that is scripts/generate_mdx.py) or to decide HTTP status (#8311)."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/lexicon/lesson_atlas_link_census.py\n"
            "  .venv/bin/python scripts/lexicon/lesson_atlas_link_census.py --examples 8\n"
            "  .venv/bin/python scripts/lexicon/lesson_atlas_link_census.py \\\n"
            "      --docs site/src/content/docs \\\n"
            "      --search-index site/src/data/lexicon-search-index.json \\\n"
            "      --aliases site/src/data/lexicon-search-aliases.json\n"
            "\n"
            "Outputs:\n"
            "  A stdout report: atlas_href counts and all /lexicon/ counts, each by class\n"
            "  and by level, plus examples. No files are written.\n"
            "\n"
            "Exit codes:\n"
            "  0  report printed (dead links do not change the exit code; the pytest gate does)\n"
            "  2  docs directory or a published-data file is missing or unreadable\n"
            "\n"
            "Related:\n"
            "  site/src/lib/lexicon/word-atlas-client-shell.ts (Page Not Found preflight),\n"
            "  site/src/data/lexicon-search-index.json, site/src/data/lexicon-search-aliases.json,\n"
            "  scripts/generate_mdx/atlas_links.py, issue #8734.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--docs",
        type=Path,
        default=DEFAULT_DOCS,
        help=(
            "Root of committed lesson MDX to scan (default: site/src/content/docs). "
            "Example: site/src/content/docs"
        ),
    )
    parser.add_argument(
        "--search-index",
        type=Path,
        default=DEFAULT_SEARCH_INDEX,
        help=(
            "Published article index whose `s` values are entry keys "
            "(default: site/src/data/lexicon-search-index.json). "
            "Example: site/src/data/lexicon-search-index.json"
        ),
    )
    parser.add_argument(
        "--aliases",
        type=Path,
        default=DEFAULT_ALIASES,
        help=(
            "Published alias rows (`a` → `s`) "
            "(default: site/src/data/lexicon-search-aliases.json). "
            "Example: site/src/data/lexicon-search-aliases.json"
        ),
    )
    parser.add_argument(
        "--examples",
        type=int,
        default=5,
        help="Unique example slugs to print per class (default: 5). Example: 8",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    docs_root = args.docs if args.docs.is_absolute() else ROOT / args.docs
    search_index = args.search_index if args.search_index.is_absolute() else ROOT / args.search_index
    aliases = args.aliases if args.aliases.is_absolute() else ROOT / args.aliases
    missing = [path for path in (docs_root, search_index, aliases) if not path.exists()]
    if missing or args.examples < 0:
        for path in missing:
            print(f"missing path: {path}", file=sys.stderr)
        if args.examples < 0:
            print("--examples must be >= 0", file=sys.stderr)
        return 2
    try:
        catalog = load_published_catalog(search_index, aliases)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"could not read published Atlas data: {exc}", file=sys.stderr)
        return 2
    hits = iter_lesson_hits(docs_root, catalog)
    sys.stdout.write(format_report(docs_root, catalog, hits, examples=args.examples))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
