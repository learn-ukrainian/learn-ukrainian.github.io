#!/usr/bin/env python3
"""Migrate wiki source citations into sibling ``.sources.yaml`` files."""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wiki.config import WIKI_DIR
from wiki.sources_schema import (
    WikiSourcesRegistry,
    assign_source_ids,
    extract_short_citation_ids,
    load_sources_registry,
    normalize_source_filename,
    registry_path_for,
    save_sources_registry,
    validate_sources_registry,
)

WIKI_META_RE = re.compile(r"<!--\s*wiki-meta\b(?P<body>.*?)-->", re.DOTALL)
LEGACY_CITATION_RE = re.compile(
    r"\((?P<body>[^()]*?(?:Source\s+\d+(?:\s*:)?|Джерел[оа]\s*:)[^()]*)\)",
    re.IGNORECASE | re.DOTALL,
)
SOURCE_SEGMENT_RE = re.compile(
    r"Source\s+(\d+)\s*:\s*(.+?)(?=(?:[;,]\s*Source\s+\d+\s*:)|$)",
    re.IGNORECASE | re.DOTALL,
)
UA_LABEL_RE = re.compile(r"Джерел[оа]\s*:\s*(?P<body>.+)$", re.IGNORECASE | re.DOTALL)
SOURCE_TOKEN_RE = re.compile(r"Source\s+(\d+)", re.IGNORECASE)
BACKTICK_FILE_RE = re.compile(r"`([^`]+)`")
DIRECT_FILE_RE = re.compile(
    r"\b(?:"
    r"ext-[A-Za-z0-9_-]+"
    r"|[0-9A-Fa-f]{8}_c\d+"
    r"|\d+-?(?:klas|клас)-[A-Za-zА-Яа-яІіЇїЄєҐґ0-9_.-]+(?:_s\d+)?"
    r"|[A-Za-zА-Яа-яІіЇїЄєҐґ0-9_.-]+_s\d+"
    r"|unknown"
    r")\b",
)


@dataclass(slots=True)
class LegacyCitationMatch:
    start: int
    end: int
    raw: str
    files: list[str]
    warning: str | None = None


@dataclass(slots=True)
class ArticleMigrationResult:
    article_path: Path
    updated_text: str
    registry: WikiSourcesRegistry
    legacy_count_before: int
    short_count_after: int
    total_sources: int
    warnings: list[str]
    changed: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print diffs for the first 5 articles, no writes")
    parser.add_argument("--track", help="Only migrate articles whose wiki-meta tracks include this track")
    parser.add_argument("--verify", action="store_true", help="Verify migrated citations against sibling registries")
    return parser.parse_args()


def parse_wiki_meta(article_text: str) -> tuple[dict, re.Match[str] | None]:
    """Parse the ``<!-- wiki-meta ... -->`` block."""
    match = WIKI_META_RE.search(article_text)
    if not match:
        return {}, None

    body = match.group("body").strip()
    data: dict | None
    try:
        data = yaml.safe_load(body)
    except yaml.YAMLError:
        data = None

    if isinstance(data, dict):
        return data, match

    inline: dict[str, object] = {}
    for part in body.split():
        if "=" not in part:
            continue
        key, _, value = part.partition("=")
        inline[key.strip()] = value.strip()
    return inline, match


def render_wiki_meta(meta: dict) -> str:
    """Render wiki-meta in a stable multiline format without ``sources:``."""
    ordered_keys = ["slug", "domain", "tracks", "compiled"]
    seen: set[str] = set()
    lines = ["<!-- wiki-meta"]

    def _format_value(value: object) -> str:
        if isinstance(value, list):
            return "[" + ", ".join(str(item) for item in value) + "]"
        return str(value)

    for key in ordered_keys:
        if key in meta:
            lines.append(f"{key}: {_format_value(meta[key])}")
            seen.add(key)

    for key, value in meta.items():
        if key in seen:
            continue
        lines.append(f"{key}: {_format_value(value)}")

    lines.append("-->")
    return "\n".join(lines)


def iter_wiki_articles(*, track: str | None = None) -> list[Path]:
    """List migratable wiki articles."""
    articles: list[Path] = []
    for path in sorted(WIKI_DIR.rglob("*.md")):
        if path.name == "index.md":
            continue
        if ".reviews" in path.parts:
            continue
        if track:
            meta, _ = parse_wiki_meta(path.read_text(encoding="utf-8"))
            tracks = meta.get("tracks") or []
            if track not in tracks:
                continue
        articles.append(path)
    return articles


def find_legacy_citations(article_text: str, meta_sources: list[str]) -> list[LegacyCitationMatch]:
    """Find legacy citation parentheticals and resolve their source filenames."""
    matches: list[LegacyCitationMatch] = []
    for match in LEGACY_CITATION_RE.finditer(article_text):
        raw = match.group(0)
        body = match.group("body").strip()
        files, warning = _resolve_legacy_citation_body(body, meta_sources)
        matches.append(
            LegacyCitationMatch(
                start=match.start(),
                end=match.end(),
                raw=raw,
                files=files,
                warning=warning,
            )
        )
    return matches


def migrate_article(path: Path) -> ArticleMigrationResult:
    """Return migrated article text and sibling registry data."""
    original_text = path.read_text(encoding="utf-8")
    meta, meta_match = parse_wiki_meta(original_text)
    meta_sources = [
        normalize_source_filename(str(item))
        for item in (meta.get("sources") or [])
        if normalize_source_filename(str(item))
    ]
    citations = find_legacy_citations(original_text, meta_sources)
    inline_files = _ordered_inline_files(citations)
    merged_sources = _merge_sources(inline_files, meta_sources)
    preserved_from_meta = {source for source in meta_sources if source not in set(inline_files)}

    registry = assign_source_ids(
        merged_sources,
        existing=load_sources_registry(registry_path_for(path)),
        preserved_from_meta=preserved_from_meta,
    )
    file_to_id = {entry.file: entry.id for entry in registry.sources}

    updated_text = _rewrite_citations(original_text, citations, file_to_id)
    if meta_match:
        meta_without_sources = dict(meta)
        meta_without_sources.pop("sources", None)
        updated_text = (
            updated_text[:meta_match.start()]
            + render_wiki_meta(meta_without_sources)
            + updated_text[meta_match.end():]
        )

    warnings = [warning for warning in (citation.warning for citation in citations) if warning]
    return ArticleMigrationResult(
        article_path=path,
        updated_text=updated_text,
        registry=registry,
        legacy_count_before=len(citations),
        short_count_after=len(extract_short_citation_ids(updated_text)),
        total_sources=len(registry.sources),
        warnings=warnings,
        changed=(
            updated_text != original_text
            or (registry.sources and not registry_path_for(path).exists())
        ),
    )


def verify_articles(paths: list[Path], staged: dict[Path, ArticleMigrationResult] | None = None) -> list[str]:
    """Verify migrated articles against their sibling registries."""
    issues: list[str] = []
    staged = staged or {}
    for path in paths:
        if path in staged:
            article_text = staged[path].updated_text
            registry = staged[path].registry
        else:
            article_text = path.read_text(encoding="utf-8")
            registry = load_sources_registry(registry_path_for(path))

        legacy_left = find_legacy_citations(article_text, [])
        if legacy_left:
            issues.append(f"{path}: {len(legacy_left)} legacy citations remain")

        issues.extend(f"{path}: {issue}" for issue in validate_sources_registry(article_text, registry))
    return issues


def render_diff(result: ArticleMigrationResult) -> str:
    """Render a combined article + registry diff preview."""
    original_text = result.article_path.read_text(encoding="utf-8")
    article_diff = "\n".join(
        difflib.unified_diff(
            original_text.splitlines(),
            result.updated_text.splitlines(),
            fromfile=str(result.article_path),
            tofile=str(result.article_path),
            lineterm="",
        )
    )
    registry_path = registry_path_for(result.article_path)
    existing_registry = registry_path.read_text(encoding="utf-8").splitlines() if registry_path.exists() else []
    preview_path = result.article_path.parent / ".preview.sources.yaml"
    save_sources_registry(preview_path, result.registry, article_path=result.article_path)
    try:
        registry_text = preview_path.read_text(encoding="utf-8").splitlines()
    finally:
        preview_path.unlink(missing_ok=True)
    registry_diff = "\n".join(
        difflib.unified_diff(
            existing_registry,
            registry_text,
            fromfile=str(registry_path),
            tofile=str(registry_path),
            lineterm="",
        )
    )
    return f"{article_diff}\n{registry_diff}".strip()


def main() -> int:
    args = parse_args()
    articles = iter_wiki_articles(track=args.track)
    staged: dict[Path, ArticleMigrationResult] = {}
    total_warnings = 0

    if not articles:
        print("No wiki articles matched the migration scope.")
        return 0

    for path in articles:
        result = migrate_article(path)
        staged[path] = result
        total_warnings += len(result.warnings)
        print(
            f"{path.relative_to(WIKI_DIR)}: legacy={result.legacy_count_before} "
            f"short={result.short_count_after} sources={result.total_sources}"
        )
        for warning in result.warnings:
            print(f"  WARNING: {warning}")

    if args.dry_run:
        print("\n# Dry-run diff preview\n")
        for path in articles[:5]:
            print(render_diff(staged[path]))
            print()
    else:
        for path in articles:
            result = staged[path]
            path.write_text(result.updated_text, encoding="utf-8")
            if result.registry.sources:
                save_sources_registry(registry_path_for(path), result.registry, article_path=path)

    if args.verify:
        issues = verify_articles(articles, staged=staged)
        if issues:
            print("\nVerification failed:")
            for issue in issues:
                print(f"  {issue}")
            return 1

    print(
        f"\nMigrated {len(articles)} articles. "
        f"Warnings: {total_warnings}. "
        f"Dry run: {'yes' if args.dry_run else 'no'}."
    )
    return 0


def _merge_sources(inline_files: list[str], meta_sources: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for source in inline_files + meta_sources:
        normalized = normalize_source_filename(source)
        if not normalized or normalized in seen:
            continue
        merged.append(normalized)
        seen.add(normalized)
    return merged


def _ordered_inline_files(citations: list[LegacyCitationMatch]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for citation in citations:
        if citation.warning:
            continue
        for file_name in citation.files:
            if file_name in seen:
                continue
            ordered.append(file_name)
            seen.add(file_name)
    return ordered


def _rewrite_citations(
    article_text: str,
    citations: list[LegacyCitationMatch],
    file_to_id: dict[str, str],
) -> str:
    updated = article_text
    for citation in reversed(citations):
        if citation.warning:
            continue
        short = "".join(f"[{file_to_id[file_name]}]" for file_name in citation.files if file_name in file_to_id)
        updated = updated[:citation.start] + short + updated[citation.end:]
    return updated


def _resolve_legacy_citation_body(body: str, meta_sources: list[str]) -> tuple[list[str], str | None]:
    files: list[str] = []
    source_matches = list(SOURCE_SEGMENT_RE.finditer(body))
    if source_matches:
        for match in source_matches:
            resolved, warning = _resolve_reference_token(match.group(2), meta_sources)
            if warning:
                return [], f"Unresolved citation segment `{match.group(0).strip()}`: {warning}"
            files.extend(resolved)
        return _dedupe(files), None

    ua_match = UA_LABEL_RE.search(body)
    token_body = ua_match.group("body") if ua_match else body
    for token in _split_reference_tokens(token_body):
        resolved, warning = _resolve_reference_token(token, meta_sources)
        if warning:
            return [], f"Unresolved citation token `{token}`: {warning}"
        files.extend(resolved)
    deduped = _dedupe(files)
    if deduped:
        return deduped, None
    return [], f"Legacy citation format not recognized: {body}"


def _resolve_reference_token(token: str, meta_sources: list[str]) -> tuple[list[str], str | None]:
    value = token.strip()
    if not value:
        return [], "empty token"

    if value.lower() in {"adapted", "адаптовано"}:
        return [], None

    backtick_files = [
        normalize_source_filename(match)
        for match in BACKTICK_FILE_RE.findall(value)
        if normalize_source_filename(match)
    ]
    if backtick_files:
        return _dedupe(backtick_files), None

    direct_files = [
        normalize_source_filename(match)
        for match in DIRECT_FILE_RE.findall(value)
        if normalize_source_filename(match)
    ]
    if direct_files:
        return _dedupe(direct_files), None

    source_token = SOURCE_TOKEN_RE.search(value)
    if source_token:
        return _resolve_meta_index(int(source_token.group(1)), meta_sources)

    if value.isdigit():
        return _resolve_meta_index(int(value), meta_sources)

    return [], f"no filename-like source id in token {token!r}"


def _resolve_meta_index(index: int, meta_sources: list[str]) -> tuple[list[str], str | None]:
    if index < 1 or index > len(meta_sources):
        return [], f"meta source index {index} out of range"
    resolved = normalize_source_filename(meta_sources[index - 1])
    if not resolved:
        return [], f"meta source index {index} is empty"
    return [resolved], None


def _split_reference_tokens(body: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    in_backticks = False
    for char in body:
        if char == "`":
            in_backticks = not in_backticks
            current.append(char)
            continue
        if char in ",;" and not in_backticks:
            token = "".join(current).strip()
            if token:
                tokens.append(token)
            current = []
            continue
        current.append(char)
    token = "".join(current).strip()
    if token:
        tokens.append(token)
    return tokens


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        ordered.append(value)
        seen.add(value)
    return ordered


if __name__ == "__main__":
    raise SystemExit(main())
