#!/usr/bin/env python3
"""DB-free Word Atlas coverage gate for current module vocabulary."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lexicon.build_data_manifest import (
    _atlas_record_for_manifest,
    _entry_lemma,
    _lemma_key,
)
from scripts.lexicon.manifest_io import load_manifest

DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
CURRICULUM_REL = Path("curriculum") / "l2-uk-en"


@dataclass(frozen=True)
class ModuleRef:
    track: str
    module_num: int
    slug: str


@dataclass
class ExpectedLemma:
    lemma: str
    modules: set[tuple[str, str]] = field(default_factory=set)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _course_module_numbers(curriculum_root: Path) -> dict[tuple[str, str], int]:
    manifest_path = curriculum_root / "curriculum.yaml"
    if not manifest_path.exists():
        return {}

    data = _load_yaml(manifest_path) or {}
    levels = data.get("levels") if isinstance(data, dict) else {}
    if not isinstance(levels, dict):
        return {}

    module_numbers: dict[tuple[str, str], int] = {}
    for track, level_data in levels.items():
        if not isinstance(level_data, dict):
            continue
        raw_modules = level_data.get("modules") or []
        if not isinstance(raw_modules, list):
            continue
        for index, raw_slug in enumerate(raw_modules, start=1):
            slug = str(raw_slug).split("#", 1)[0].strip()
            if slug and (curriculum_root / str(track) / slug / "vocabulary.yaml").exists():
                module_numbers[(str(track), slug)] = index
    return module_numbers


def _vocabulary_modules(root: Path) -> list[ModuleRef]:
    curriculum_root = root / CURRICULUM_REL
    indexed_numbers = _course_module_numbers(curriculum_root)
    max_index_by_track: dict[str, int] = {}
    for (track, _slug), module_num in indexed_numbers.items():
        max_index_by_track[track] = max(max_index_by_track.get(track, 0), module_num)

    extra_counts_by_track: dict[str, int] = {}
    modules: list[ModuleRef] = []
    for path in sorted(curriculum_root.glob("*/*/vocabulary.yaml")):
        track = path.parent.parent.name
        slug = path.parent.name
        module_num = indexed_numbers.get((track, slug))
        if module_num is None:
            extra_counts_by_track[track] = extra_counts_by_track.get(track, 0) + 1
            module_num = max_index_by_track.get(track, 0) + extra_counts_by_track[track]
        modules.append(ModuleRef(track=track, module_num=module_num, slug=slug))
    return modules


def changed_vocab_modules(root: Path, base: str) -> set[tuple[str, str]] | None:
    """Modules whose ``vocabulary.yaml`` changed vs ``base`` (PR diff-scope, #3150).

    Returns the ``{(track, slug)}`` set of changed modules, or ``None`` when the git
    diff cannot be computed (base ref absent, not a git tree). The caller treats
    ``None`` as "fall back to full-curriculum coverage" rather than silently passing —
    a fail-open here would let an uncovered new module slip through.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-only", f"{base}...HEAD", "--", str(CURRICULUM_REL)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None

    changed: set[tuple[str, str]] = set()
    for line in out.splitlines():
        parts = Path(line.strip()).parts
        # curriculum/l2-uk-en/{track}/{slug}/vocabulary.yaml — exactly this depth.
        if (
            len(parts) == 5
            and parts[0] == "curriculum"
            and parts[1] == "l2-uk-en"
            and parts[4] == "vocabulary.yaml"
        ):
            changed.add((parts[2], parts[3]))
    return changed


def _load_built_vocab(root: Path, module: ModuleRef) -> list[dict[str, Any]]:
    path = root / CURRICULUM_REL / module.track / module.slug / "vocabulary.yaml"
    if not path.exists():
        return []
    raw = _load_yaml(path) or []
    if not isinstance(raw, list):
        return []

    records: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        lemma = _entry_lemma(entry)
        if not lemma:
            continue
        records.append(
            {
                "lemma": lemma,
                "gloss": entry.get("translation"),
                "pos": entry.get("pos"),
                "ipa": entry.get("ipa") or None,
                "source": "built_vocabulary",
            }
        )
    return records


def expected_vocabulary_coverage(
    root: Path = ROOT,
    *,
    restrict: set[tuple[str, str]] | None = None,
) -> tuple[dict[str, ExpectedLemma], int]:
    """Return normalized Atlas lemmas current vocabulary files must cover.

    ``restrict`` (a ``{(track, slug)}`` set) limits the coverage requirement to those
    modules (PR diff-scope, #3150). ``taught_lemma_keys`` is still computed over the
    FULL curriculum so ``_atlas_record_for_manifest`` makes the same include/exclude
    decision it would in a full run — only the *checked* module set narrows.
    """
    root = root.resolve()
    modules = _vocabulary_modules(root)
    raw_records_by_module = [(module, _load_built_vocab(root, module)) for module in modules]
    taught_lemma_keys = {
        _lemma_key(rec["lemma"])
        for _module, records in raw_records_by_module
        for rec in records
    }

    expected: dict[str, ExpectedLemma] = {}
    checked = 0
    for module, raw_records in raw_records_by_module:
        if restrict is not None and (module.track, module.slug) not in restrict:
            continue
        checked += 1
        for raw_record in raw_records:
            record = _atlas_record_for_manifest(raw_record, taught_lemma_keys)
            if record is None:
                continue
            records = record if isinstance(record, list) else [record]
            for item in records:
                if item.get("form_of"):
                    continue
                lemma = str(item["lemma"])
                key = _lemma_key(lemma)
                expected.setdefault(key, ExpectedLemma(lemma=lemma)).modules.add(
                    (module.track, module.slug)
                )
    return expected, checked


def _manifest_entries_by_key(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        return {}

    by_key: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        lemma = entry.get("lemma")
        if lemma is None:
            continue
        by_key[_lemma_key(str(lemma))] = entry
    return by_key


def _usage_modules(entry: dict[str, Any]) -> set[tuple[str, str]]:
    usage = entry.get("course_usage")
    if not isinstance(usage, list):
        return set()

    out: set[tuple[str, str]] = set()
    for item in usage:
        if not isinstance(item, dict):
            continue
        track = item.get("track")
        slug = item.get("slug")
        if track is not None and slug is not None:
            out.add((str(track), str(slug)))
    return out


def check_vocabulary_coverage(
    *,
    root: Path = ROOT,
    manifest_path: Path = DEFAULT_MANIFEST,
    restrict: set[tuple[str, str]] | None = None,
) -> int:
    root = root.resolve()
    if restrict is not None and not restrict:
        print(
            "Atlas vocabulary coverage OK: no module vocabulary changed in this diff "
            "(diff-scoped) — nothing to check."
        )
        return 0

    try:
        manifest = load_manifest(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"::error::Atlas vocabulary coverage manifest unreadable ({exc}).")
        return 2

    manifest_entries = _manifest_entries_by_key(manifest)
    expected, module_count = expected_vocabulary_coverage(root, restrict=restrict)

    missing_entries = [
        expected_item
        for key, expected_item in expected.items()
        if key not in manifest_entries
    ]
    missing_usage: list[tuple[str, str, str]] = []
    for key, expected_item in expected.items():
        entry = manifest_entries.get(key)
        if entry is None:
            continue
        reflected_modules = _usage_modules(entry)
        for track, slug in expected_item.modules - reflected_modules:
            missing_usage.append((expected_item.lemma, track, slug))

    if missing_entries or missing_usage:
        print(
            "::error::Atlas manifest stale vs module vocabulary; "
            "run `make atlas` locally and commit site/src/data/lexicon-manifest.json "
            "+ site/src/data/lexicon-manifest.fingerprint.json."
        )
        if missing_entries:
            print(f"missing manifest entries for current vocabulary lemmas: {len(missing_entries)}")
            for item in sorted(missing_entries, key=lambda expected_item: expected_item.lemma)[:20]:
                modules = ", ".join(
                    f"{track}/{slug}" for track, slug in sorted(item.modules)
                )
                print(f"  - {item.lemma} ({modules})")
        if missing_usage:
            print(f"missing course_usage links for current vocabulary modules: {len(missing_usage)}")
            for lemma, track, slug in sorted(missing_usage)[:20]:
                print(f"  - {lemma}: {track}/{slug}")
        return 2

    print(
        "Atlas vocabulary coverage OK: "
        f"{len(expected)} Atlas vocabulary lemmas across {module_count} modules "
        "are reflected in site/src/data/lexicon-manifest.json."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DB-free Atlas vocabulary coverage.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Committed lexicon manifest.",
    )
    parser.add_argument(
        "--changed-only",
        action="store_true",
        help="Diff-scope (#3150): only require modules whose vocabulary.yaml changed vs --base "
        "to be covered. Removes cross-PR coupling on a fast merge-train.",
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Base ref for --changed-only diff (default: origin/main).",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = args.manifest
    if not manifest.is_absolute():
        manifest = root / manifest

    restrict: set[tuple[str, str]] | None = None
    if args.changed_only:
        restrict = changed_vocab_modules(root, args.base)
        if restrict is None:
            print(
                f"# diff-scope unavailable (could not diff vs {args.base}); "
                "falling back to full-curriculum coverage."
            )
        else:
            print(f"# diff-scoped vs {args.base}: {len(restrict)} changed vocabulary module(s).")
    return check_vocabulary_coverage(root=root, manifest_path=manifest, restrict=restrict)


if __name__ == "__main__":
    raise SystemExit(main())
