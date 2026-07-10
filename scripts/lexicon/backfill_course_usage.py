#!/usr/bin/env python3
"""Backfill empty Atlas ``course_usage`` rows from visible course content.

This deliberately stays conservative: VESUM supplies inflected surfaces, but
any surface shared by more than one Atlas lemma is excluded for every
inflected-form match. An exact lemma match remains safe. The command defaults
to a dry run; pass ``--write`` only after reviewing its JSON summary.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.content_lexicon_reconciler import extract_ukrainian_tokens, strip_mdx_to_prose
from scripts.lexicon.manifest_fingerprint import write_fingerprint
from scripts.lexicon.manifest_io import DEFAULT_MANIFEST, load_manifest, write_manifest
from scripts.verification.vesum import verify_lemma

CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
DEFAULT_FINGERPRINT = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"
MAX_COURSE_USAGE_ROWS = 6

_WORD_BOUNDARY = r"(?<!\w){surface}(?!\w)"
_APOSTROPHE_TRANSLATION = str.maketrans({"ʼ": "'", "’": "'"})

VesumFormsLookup = Callable[[str], list[dict[str, Any]]]


@dataclass(frozen=True)
class ModuleContent:
    """Curriculum-ordered content files for one module."""

    track: str
    module_num: int
    slug: str
    order: int
    paths: tuple[Path, ...]


@dataclass(frozen=True)
class CourseUsageUpdate:
    """The prospective ``course_usage`` value for one manifest entry."""

    entry_index: int
    lemma: str
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class BackfillResult:
    """Deterministic outcome of a course-usage backfill run."""

    modules_scanned: int
    content_files_scanned: int
    eligible_entries: int
    ambiguous_surface_forms_skipped: int
    updates: tuple[CourseUsageUpdate, ...]
    manifest_written: bool
    fingerprint_written: bool

    @property
    def course_usage_rows_added(self) -> int:
        return sum(len(update.rows) for update in self.updates)

    def json_summary(self) -> dict[str, int | bool]:
        return {
            "modules_scanned": self.modules_scanned,
            "content_files_scanned": self.content_files_scanned,
            "eligible_entries": self.eligible_entries,
            "entries_would_gain_course_usage": len(self.updates),
            "course_usage_rows_to_add": self.course_usage_rows_added,
            "ambiguous_surface_forms_skipped": self.ambiguous_surface_forms_skipped,
            "manifest_written": self.manifest_written,
            "fingerprint_written": self.fingerprint_written,
        }


def backfill_course_usage(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    curriculum_root: Path = CURRICULUM_ROOT,
    write: bool = False,
    vesum_forms_lookup: VesumFormsLookup | None = None,
    fingerprint_path: Path | None = None,
) -> BackfillResult:
    """Find real course-content usage for empty manifest rows.

    The manifest is only mutated after all prospective matches have been
    computed, so a dry run has no write-side effects beyond normal release
    manifest hydration when the default manifest is absent locally.
    """
    manifest = load_manifest(manifest_path)
    vesum_forms_lookup = vesum_forms_lookup or verify_lemma
    entries = _manifest_entries(manifest, manifest_path)
    modules = _curriculum_modules(curriculum_root)
    visible_text = _visible_module_text(modules)

    forms_by_lemma = _forms_by_lemma(entries, vesum_forms_lookup)
    surface_owners = _surface_owners(entries, forms_by_lemma)
    candidates = _eligible_candidates(entries)
    matchers, skipped_surfaces = _candidate_matchers(candidates, forms_by_lemma, surface_owners)
    matches = _find_module_matches(modules, visible_text, matchers)

    updates = tuple(
        CourseUsageUpdate(entry_index=index, lemma=lemma, rows=_course_usage_rows(matches.get(index, {})))
        for index, lemma in candidates
        if matches.get(index)
    )

    manifest_written = False
    fingerprint_written = False
    if write and updates:
        for update in updates:
            entries[update.entry_index]["course_usage"] = list(update.rows)
        output_fingerprint = fingerprint_path or _fingerprint_path_for(manifest_path)
        _refresh_manifest_fingerprint(manifest, output_fingerprint)
        write_manifest(manifest_path, manifest)
        manifest_written = True
        fingerprint_written = True

    return BackfillResult(
        modules_scanned=len(modules),
        content_files_scanned=sum(len(module.paths) for module in modules),
        eligible_entries=len(candidates),
        ambiguous_surface_forms_skipped=len(skipped_surfaces),
        updates=updates,
        manifest_written=manifest_written,
        fingerprint_written=fingerprint_written,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--curriculum-root", type=Path, default=CURRICULUM_ROOT)
    parser.add_argument("--write", action="store_true", help="Write prospective rows and re-stamp the fingerprint.")
    parser.add_argument("--json", action="store_true", help="Print the machine-readable summary.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = backfill_course_usage(
        manifest_path=args.manifest,
        curriculum_root=args.curriculum_root,
        write=args.write,
    )
    summary = result.json_summary()
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for key, value in summary.items():
            print(f"{key}: {value}")
        if not args.write:
            print("Dry run only; pass --write to update the manifest.")
    return 0


def _manifest_entries(manifest: dict[str, Any], manifest_path: Path) -> list[dict[str, Any]]:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"Manifest entries must be a list: {manifest_path}")
    return [entry if isinstance(entry, dict) else {} for entry in entries]


def _curriculum_modules(curriculum_root: Path) -> tuple[ModuleContent, ...]:
    curriculum_path = curriculum_root / "curriculum.yaml"
    curriculum = yaml.safe_load(curriculum_path.read_text(encoding="utf-8")) or {}
    levels = curriculum.get("levels") if isinstance(curriculum, dict) else None
    if not isinstance(levels, dict):
        raise ValueError(f"Curriculum levels must be a mapping: {curriculum_path}")

    modules: list[ModuleContent] = []
    order = 0
    for track, raw_level in levels.items():
        if not isinstance(raw_level, dict):
            continue
        raw_modules = raw_level.get("modules") or []
        if not isinstance(raw_modules, list):
            continue
        for module_num, raw_slug in enumerate(raw_modules, start=1):
            slug = str(raw_slug).split("#", 1)[0].strip()
            if not slug:
                continue
            module_dir = curriculum_root / str(track) / slug
            paths = tuple(path for path in (module_dir / "module.md", module_dir / "module.mdx") if path.is_file())
            if not paths:
                continue
            modules.append(
                ModuleContent(
                    track=str(track),
                    module_num=module_num,
                    slug=slug,
                    order=order,
                    paths=paths,
                )
            )
            order += 1
    return tuple(modules)


def _visible_module_text(modules: Iterable[ModuleContent]) -> dict[ModuleContent, str]:
    visible_text: dict[ModuleContent, str] = {}
    for module in modules:
        source = "\n".join(path.read_text(encoding="utf-8") for path in module.paths)
        visible_text[module] = _normalize_for_match(strip_mdx_to_prose(source))
    return visible_text


def _forms_by_lemma(
    entries: Iterable[dict[str, Any]],
    vesum_forms_lookup: VesumFormsLookup,
) -> dict[str, frozenset[str]]:
    forms_by_lemma: dict[str, frozenset[str]] = {}
    for entry in entries:
        lemma = _entry_lemma(entry)
        if lemma is None:
            continue
        lemma_key = _normalize_for_match(lemma)
        if lemma_key in forms_by_lemma:
            continue
        forms = {lemma_key}
        if " " not in lemma_key:
            for query in _vesum_queries(lemma):
                for record in vesum_forms_lookup(query):
                    if not isinstance(record, dict):
                        continue
                    word_form = record.get("word_form")
                    if isinstance(word_form, str) and word_form.strip():
                        forms.add(_normalize_for_match(word_form))
        forms_by_lemma[lemma_key] = frozenset(forms)
    return forms_by_lemma


def _vesum_queries(lemma: str) -> tuple[str, ...]:
    original = lemma.strip()
    canonical = _strip_stress(original).translate(_APOSTROPHE_TRANSLATION)
    return tuple(dict.fromkeys(query for query in (original, canonical) if query))


def _surface_owners(
    entries: Iterable[dict[str, Any]],
    forms_by_lemma: dict[str, frozenset[str]],
) -> dict[str, frozenset[str]]:
    owners: dict[str, set[str]] = defaultdict(set)
    for entry in entries:
        lemma = _entry_lemma(entry)
        if lemma is None:
            continue
        lemma_key = _normalize_for_match(lemma)
        for surface in forms_by_lemma.get(lemma_key, frozenset({lemma_key})):
            owners[surface].add(lemma_key)
    return {surface: frozenset(lemma_keys) for surface, lemma_keys in owners.items()}


def _eligible_candidates(entries: Iterable[dict[str, Any]]) -> tuple[tuple[int, str], ...]:
    return tuple(
        (index, lemma)
        for index, entry in enumerate(entries)
        if not entry.get("course_usage") and (lemma := _entry_lemma(entry)) is not None
    )


def _candidate_matchers(
    candidates: Iterable[tuple[int, str]],
    forms_by_lemma: dict[str, frozenset[str]],
    surface_owners: dict[str, frozenset[str]],
) -> tuple[dict[str, tuple[tuple[int, bool], ...]], set[str]]:
    matchers: dict[str, list[tuple[int, bool]]] = defaultdict(list)
    skipped_surfaces: set[str] = set()
    for entry_index, lemma in candidates:
        lemma_key = _normalize_for_match(lemma)
        for surface in forms_by_lemma.get(lemma_key, frozenset({lemma_key})):
            exact = surface == lemma_key
            # Owner sets include every manifest lemma, not merely empty rows.
            # An exact headword remains safe; every shared inflected surface is
            # excluded for all otherwise matching entries.
            if not exact and len(surface_owners.get(surface, frozenset())) != 1:
                skipped_surfaces.add(surface)
                continue
            matchers[surface].append((entry_index, exact))
    return {surface: tuple(items) for surface, items in matchers.items()}, skipped_surfaces


def _find_module_matches(
    modules: Iterable[ModuleContent],
    visible_text: dict[ModuleContent, str],
    matchers: dict[str, tuple[tuple[int, bool], ...]],
) -> dict[int, dict[ModuleContent, bool]]:
    matches: dict[int, dict[ModuleContent, bool]] = defaultdict(dict)
    phrase_matchers = {surface: candidates for surface, candidates in matchers.items() if not _is_single_token(surface)}
    single_matchers = {surface: candidates for surface, candidates in matchers.items() if _is_single_token(surface)}

    for module in modules:
        text = visible_text[module]
        for token in set(extract_ukrainian_tokens(text)):
            for entry_index, exact in single_matchers.get(token, ()):
                matches[entry_index][module] = matches[entry_index].get(module, False) or exact
        for phrase, candidates in phrase_matchers.items():
            if not re.search(_WORD_BOUNDARY.format(surface=re.escape(phrase)), text):
                continue
            for entry_index, exact in candidates:
                matches[entry_index][module] = matches[entry_index].get(module, False) or exact
    return matches


def _course_usage_rows(matches: dict[ModuleContent, bool]) -> tuple[dict[str, Any], ...]:
    ranked = sorted(matches.items(), key=lambda item: (not item[1], item[0].order))
    return tuple(
        {
            "track": module.track,
            "module_num": module.module_num,
            "slug": module.slug,
            "context": "content_backfill",
        }
        for module, _exact in ranked[:MAX_COURSE_USAGE_ROWS]
    )


def _entry_lemma(entry: dict[str, Any]) -> str | None:
    lemma = entry.get("lemma")
    return lemma.strip() if isinstance(lemma, str) and lemma.strip() else None


def _is_single_token(surface: str) -> bool:
    return extract_ukrainian_tokens(surface) == [surface]


def _normalize_for_match(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text).replace("\u0301", "")
    return unicodedata.normalize("NFC", normalized.translate(_APOSTROPHE_TRANSLATION).casefold())


def _strip_stress(text: str) -> str:
    return unicodedata.normalize("NFC", unicodedata.normalize("NFD", text).replace("\u0301", ""))


def _fingerprint_path_for(manifest_path: Path) -> Path:
    resolved = manifest_path if manifest_path.is_absolute() else PROJECT_ROOT / manifest_path
    if resolved.resolve() == DEFAULT_MANIFEST.resolve():
        return DEFAULT_FINGERPRINT
    return resolved.with_name("lexicon-manifest.fingerprint.json")


def _refresh_manifest_fingerprint(manifest: dict[str, Any], fingerprint_path: Path) -> None:
    fingerprint = write_fingerprint(fingerprint_path, root=PROJECT_ROOT)
    manifest["manifest_fingerprint"] = {
        "schema_version": fingerprint["schema_version"],
        "fingerprint": fingerprint["fingerprint"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
