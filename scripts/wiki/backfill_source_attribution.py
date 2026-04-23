#!/usr/bin/env python3
"""Backfill rich attribution metadata for existing wiki source registries.

Use this after `sources.db` has real attribution data and legacy `wiki/**/*.sources.yaml`
files still contain bare chunk ids or `type: unknown`. Do not use it to renumber
citations or rewrite article markdown bodies.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TextIO

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from wiki.config import PROJECT_ROOT, WIKI_DIR
    from wiki.migrate_sources import parse_wiki_meta
    from wiki.source_attribution import connect_sources_db, resolve_chunk_attribution_any_corpus_with_conn
    from wiki.sources_schema import (
        WikiSourceEntry,
        WikiSourcesRegistry,
        load_sources_registry,
        serialize_sources_registry,
    )
else:
    from .config import PROJECT_ROOT, WIKI_DIR
    from .migrate_sources import parse_wiki_meta
    from .source_attribution import connect_sources_db, resolve_chunk_attribution_any_corpus_with_conn
    from .sources_schema import (
        WikiSourceEntry,
        WikiSourcesRegistry,
        load_sources_registry,
        serialize_sources_registry,
    )


LOG_DIR = PROJECT_ROOT / "docs" / "data-quality"
BARE_CHUNK_ID_PREFIX = "S"


@dataclass(slots=True)
class UnresolvableSource:
    registry_path: Path
    citation_id: str
    chunk_id: str


@dataclass(slots=True)
class RegistryBackfillResult:
    registry_path: Path
    article_path: Path
    original_text: str
    updated_text: str
    resolved_count: int
    unresolved: list[UnresolvableSource]
    unknown_before: int
    unknown_after: int

    @property
    def changed(self) -> bool:
        return self.original_text != self.updated_text

    @property
    def diff_text(self) -> str:
        if not self.changed:
            return ""
        return "".join(
            difflib.unified_diff(
                self.original_text.splitlines(keepends=True),
                self.updated_text.splitlines(keepends=True),
                fromfile=str(self.registry_path),
                tofile=str(self.registry_path),
            )
        )


@dataclass(slots=True)
class BackfillSummary:
    mode: str
    track: str | None
    slug: str | None
    results: list[RegistryBackfillResult]
    log_path: Path | None = None

    @property
    def files_scanned(self) -> int:
        return len(self.results)

    @property
    def files_changed(self) -> int:
        return sum(1 for result in self.results if result.changed)

    @property
    def total_resolved(self) -> int:
        return sum(result.resolved_count for result in self.results)

    @property
    def total_unresolved(self) -> int:
        return sum(len(result.unresolved) for result in self.results)

    @property
    def unknown_before(self) -> int:
        return sum(result.unknown_before for result in self.results)

    @property
    def unknown_after(self) -> int:
        return sum(result.unknown_after for result in self.results)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill rich attribution metadata into legacy wiki `.sources.yaml` registries.\n"
            "Use this for existing wiki source registries that still store bare chunk ids or "
            "`type: unknown`; do not use it to rewrite article markdown or renumber `[S*]` citations."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/wiki/backfill_source_attribution.py --dry-run\n"
            "  .venv/bin/python scripts/wiki/backfill_source_attribution.py --track a1 --apply\n"
            "  .venv/bin/python scripts/wiki/backfill_source_attribution.py --slug colors --dry-run\n"
            "\n"
            "Outputs:\n"
            "  Writes unified diffs to stdout in `--dry-run` mode, rewrites matching `.sources.yaml`\n"
            "  files in `--apply` mode, and always writes a markdown migration log under\n"
            "  `docs/data-quality/source-attribution-backfill-<timestamp>.md`.\n"
            "\n"
            "Exit codes:\n"
            "  0 = completed successfully (including runs with unresolved chunks logged to stderr)\n"
            "  1 = no matching registries found or a fatal runtime error occurred\n"
            "\n"
            "Related:\n"
            "  scripts/wiki/source_attribution.py, scripts/wiki/migrate_sources.py, issue #1435"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes only and print unified diffs for each changed registry; default is off.",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Write updated attribution metadata back to matching `.sources.yaml` files; default is off.",
    )
    parser.add_argument(
        "--track",
        help=(
            "Only process registries whose sibling article `wiki-meta` tracks contain this value "
            "(example: `a1`, `b2`, `hist`); default is all tracks."
        ),
    )
    parser.add_argument(
        "--slug",
        help=(
            "Only process the wiki article slug matching this registry basename, without `.sources.yaml` "
            "(example: `colors`); default is all slugs."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run_backfill(
        apply=args.apply,
        track=args.track,
        slug=args.slug,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    if summary.files_scanned == 0:
        print("No matching wiki source registries found.", file=sys.stderr)
        return 1

    summary.log_path = write_summary_log(summary)
    print_summary(summary, stdout=sys.stdout)
    print(f"Migration log: {summary.log_path}", file=sys.stdout)
    return 0


def run_backfill(
    *,
    apply: bool,
    track: str | None,
    slug: str | None,
    stdout: TextIO,
    stderr: TextIO,
) -> BackfillSummary:
    results: list[RegistryBackfillResult] = []
    with connect_sources_db() as conn:
        for registry_path in iter_registry_paths(track=track, slug=slug):
            result = backfill_registry(registry_path, conn=conn, stderr=stderr)
            results.append(result)
            if apply and result.changed:
                registry_path.write_text(result.updated_text, encoding="utf-8")
            if not apply and result.changed:
                stdout.write(result.diff_text)
                if result.diff_text and not result.diff_text.endswith("\n"):
                    stdout.write("\n")

    return BackfillSummary(
        mode="apply" if apply else "dry-run",
        track=track,
        slug=slug,
        results=results,
    )


def iter_registry_paths(*, track: str | None = None, slug: str | None = None) -> list[Path]:
    candidates: list[Path] = []
    for path in sorted(WIKI_DIR.rglob("*.sources.yaml")):
        if slug and source_slug_for_path(path) != slug:
            continue
        if track and not registry_matches_track(path, track):
            continue
        candidates.append(path)
    return candidates


def registry_matches_track(path: Path, track: str) -> bool:
    article_path = article_path_for_registry(path)
    if not article_path.exists():
        return False
    article_text = article_path.read_text(encoding="utf-8")
    meta, _ = parse_wiki_meta(article_text)
    tracks = meta.get("tracks") or []
    return track in tracks


def article_path_for_registry(path: Path) -> Path:
    return path.with_name(f"{source_slug_for_path(path)}.md")


def source_slug_for_path(path: Path) -> str:
    suffix = ".sources.yaml"
    if not path.name.endswith(suffix):
        raise ValueError(f"Expected a `.sources.yaml` path, got {path}")
    return path.name[: -len(suffix)]


def backfill_registry(path: Path, *, conn, stderr: TextIO) -> RegistryBackfillResult:
    article_path = article_path_for_registry(path)
    registry = load_sources_registry(path)
    original_text = path.read_text(encoding="utf-8")
    updated_sources: list[WikiSourceEntry] = []
    unresolved: list[UnresolvableSource] = []
    resolved_count = 0

    for entry in registry.sources:
        if not needs_backfill(entry):
            updated_sources.append(entry)
            continue

        resolved = resolve_chunk_attribution_any_corpus_with_conn(conn, entry.file)
        if resolved is None:
            unresolved_entry = UnresolvableSource(
                registry_path=path,
                citation_id=entry.id,
                chunk_id=entry.file,
            )
            unresolved.append(unresolved_entry)
            print(
                f"Unresolved source attribution: {path} {entry.id} -> {entry.file}",
                file=stderr,
            )
            updated_sources.append(entry)
            continue

        _, attribution = resolved
        updated_entry = entry_with_resolved_attribution(entry, attribution)
        if updated_entry.to_dict() != entry.to_dict():
            resolved_count += 1
        updated_sources.append(updated_entry)

    updated_registry = WikiSourcesRegistry(sources=updated_sources)
    updated_text = serialize_sources_registry(
        updated_registry,
        article_path=article_path,
        registry_path=path,
    )
    return RegistryBackfillResult(
        registry_path=path,
        article_path=article_path,
        original_text=original_text,
        updated_text=updated_text,
        resolved_count=resolved_count,
        unresolved=unresolved,
        unknown_before=sum(1 for entry in registry.sources if entry.type == "unknown"),
        unknown_after=sum(1 for entry in updated_registry.sources if entry.type == "unknown"),
    )


def needs_backfill(entry: WikiSourceEntry) -> bool:
    return entry.type == "unknown" or is_bare_chunk_id(entry.file)


def is_bare_chunk_id(value: str) -> bool:
    text = str(value or "").strip()
    return text.startswith(BARE_CHUNK_ID_PREFIX) and text[1:].isdigit()


def entry_with_resolved_attribution(entry: WikiSourceEntry, attribution: dict) -> WikiSourceEntry:
    return WikiSourceEntry(
        id=entry.id,
        file=str(attribution["file"]),
        type=str(attribution["type"]),
        title=optional_text(attribution.get("title")),
        url=optional_text(attribution.get("url")),
        domain=optional_text(attribution.get("domain")),
        video_id=optional_text(attribution.get("video_id")),
        ts_start=optional_int(attribution.get("ts_start")),
        ts_end=optional_int(attribution.get("ts_end")),
        page=optional_int(attribution.get("page")),
        grade=optional_int(attribution.get("grade")),
        author=optional_text(attribution.get("author")),
        section_path=optional_text(attribution.get("section_path")),
        notes=entry.notes,
        preserved_from_meta=entry.preserved_from_meta,
    )


def optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def print_summary(summary: BackfillSummary, *, stdout: TextIO) -> None:
    scope_bits = []
    if summary.track:
        scope_bits.append(f"track={summary.track}")
    if summary.slug:
        scope_bits.append(f"slug={summary.slug}")
    scope_text = ", ".join(scope_bits) if scope_bits else "all wiki registries"

    print(
        (
            f"Backfill {summary.mode}: {summary.files_scanned} files scanned, "
            f"{summary.files_changed} files changed, {summary.total_resolved} entries resolved, "
            f"{summary.total_unresolved} entries unresolved, "
            f"type: unknown {summary.unknown_before} -> {summary.unknown_after} ({scope_text})"
        ),
        file=stdout,
    )
    for result in summary.results:
        if not result.changed and not result.unresolved:
            continue
        print(
            (
                f"{result.registry_path}: resolved={result.resolved_count}, "
                f"unresolved={len(result.unresolved)}, unknown={result.unknown_before}->{result.unknown_after}, "
                f"changed={'yes' if result.changed else 'no'}"
            ),
            file=stdout,
        )


def write_summary_log(summary: BackfillSummary) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = LOG_DIR / f"source-attribution-backfill-{timestamp}.md"
    log_path.write_text(render_summary_log(summary), encoding="utf-8")
    return log_path


def render_summary_log(summary: BackfillSummary) -> str:
    lines = [
        "# Wiki Source Attribution Backfill",
        "",
        f"- Mode: `{summary.mode}`",
        f"- Track filter: `{summary.track or 'all'}`",
        f"- Slug filter: `{summary.slug or 'all'}`",
        f"- Files scanned: `{summary.files_scanned}`",
        f"- Files changed: `{summary.files_changed}`",
        f"- Entries resolved: `{summary.total_resolved}`",
        f"- Entries unresolved: `{summary.total_unresolved}`",
        f"- `type: unknown`: `{summary.unknown_before}` -> `{summary.unknown_after}`",
        "",
        "## Per-file results",
        "",
        "| Registry | Resolved | Unresolved | Unknown Before | Unknown After | Changed |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in summary.results:
        lines.append(
            "| "
            f"`{result.registry_path.relative_to(PROJECT_ROOT).as_posix()}` | "
            f"{result.resolved_count} | "
            f"{len(result.unresolved)} | "
            f"{result.unknown_before} | "
            f"{result.unknown_after} | "
            f"{'yes' if result.changed else 'no'} |"
        )

    lines.extend(["", "## Unresolvable chunks", ""])
    unresolved = [entry for result in summary.results for entry in result.unresolved]
    if not unresolved:
        lines.append("- None.")
    else:
        for entry in unresolved:
            lines.append(
                "- "
                f"`{entry.registry_path.relative_to(PROJECT_ROOT).as_posix()}` "
                f"`{entry.citation_id}` -> `{entry.chunk_id}`"
            )

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
