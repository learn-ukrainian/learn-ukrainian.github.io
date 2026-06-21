#!/usr/bin/env python3
"""Fill missing Word Atlas entries from built course vocabulary.

This is a conservative write-side companion to
``content_lexicon_reconciler.py``. It is intended for folk modules first:
scan built ``vocabulary.yaml`` files, compare their lemmas to the committed
Atlas manifest, VESUM-verify missing single-token lemmas, append real manifest
entries, and then optionally run the normal enrichment/fingerprint flow.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.build_data_manifest import LEMMA_FIELDS, _lemma_key, _slug_for_url
from scripts.lexicon.manifest_fingerprint import write_fingerprint
from scripts.verification.vesum import verify_words

CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
MANIFEST_PATH = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
_SINGLE_TOKEN_UK_RE = re.compile(r"^[\u0400-\u052f]+(?:['’ʼ-][\u0400-\u052f]+)*$", re.IGNORECASE)

VesumLookup = Callable[[list[str]], dict[str, list[dict[str, Any]]]]


@dataclass(frozen=True)
class ModuleInfo:
    track: str
    slug: str
    module_num: int
    vocab_path: Path


@dataclass(frozen=True)
class FillEntry:
    lemma: str
    module: ModuleInfo
    entry: dict[str, Any]
    vesum_match: dict[str, Any]


@dataclass(frozen=True)
class SkippedLemma:
    lemma: str
    module: ModuleInfo
    reason: str


@dataclass(frozen=True)
class FillResult:
    modules_scanned: int
    missing_candidates: tuple[str, ...]
    added: tuple[FillEntry, ...]
    skipped: tuple[SkippedLemma, ...]
    manifest_written: bool
    fingerprint_written: bool
    enrichment_ran: bool


def fill_manifest_from_vocab(
    *,
    track: str = "folk",
    curriculum_root: Path = CURRICULUM_ROOT,
    manifest_path: Path = MANIFEST_PATH,
    write: bool = True,
    enrich: bool = True,
    update_fingerprint: bool = True,
    vesum_lookup: VesumLookup = verify_words,
) -> FillResult:
    """Append verified missing vocabulary lemmas to the Atlas manifest."""
    payload = _load_manifest(manifest_path)
    existing_keys = _manifest_lemma_keys(payload)
    modules = _vocabulary_modules(curriculum_root, track)

    added: list[FillEntry] = []
    skipped: list[SkippedLemma] = []
    missing_candidates: list[str] = []

    for module in modules:
        for vocab_entry in _load_vocab_entries(module.vocab_path):
            lemma = _entry_lemma(vocab_entry)
            if not lemma:
                continue
            key = _lemma_key(lemma)
            if key in existing_keys:
                continue
            missing_candidates.append(lemma)
            if not _is_single_token_lemma(lemma):
                skipped.append(SkippedLemma(lemma, module, "not a single-token lemma"))
                continue
            matches = vesum_lookup([lemma]).get(lemma, [])
            exact = _exact_vesum_lemma_match(lemma, matches)
            if exact is None:
                skipped.append(SkippedLemma(lemma, module, "VESUM did not confirm this as a lemma"))
                continue
            manifest_entry = _manifest_entry(lemma, vocab_entry, module, exact)
            added.append(FillEntry(lemma, module, manifest_entry, exact))
            existing_keys.add(key)

    manifest_written = False
    enrichment_ran = False
    if write and added:
        entries = payload.setdefault("entries", [])
        if not isinstance(entries, list):
            raise ValueError(f"Manifest entries must be a list: {manifest_path}")
        entries.extend(item.entry for item in added)
        entries.sort(key=lambda item: str(item.get("lemma") or ""))
        _merge_manifest_modules(payload, modules)
        _refresh_manifest_stats(payload)
        manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest_written = True
        if enrich:
            _run_enrichment()
            enrichment_ran = True

    fingerprint_written = False
    if write and update_fingerprint:
        write_fingerprint()
        fingerprint_written = True

    return FillResult(
        modules_scanned=len(modules),
        missing_candidates=tuple(dict.fromkeys(missing_candidates)),
        added=tuple(added),
        skipped=tuple(skipped),
        manifest_written=manifest_written,
        fingerprint_written=fingerprint_written,
        enrichment_ran=enrichment_ran,
    )


def format_result(result: FillResult) -> str:
    lines = [
        "Atlas fill from course vocabulary",
        f"Modules scanned: {result.modules_scanned}",
        f"Missing candidates: {len(result.missing_candidates)}",
        f"VESUM-verified entries added: {len(result.added)}",
        f"Skipped candidates: {len(result.skipped)}",
        f"Manifest written: {str(result.manifest_written).lower()}",
        f"Enrichment ran: {str(result.enrichment_ran).lower()}",
        f"Fingerprint written: {str(result.fingerprint_written).lower()}",
    ]
    for item in result.added:
        lines.append(
            f"- added {item.lemma} from {item.module.track}/{item.module.slug} "
            f"as {item.entry['url_slug']}"
        )
    for item in result.skipped[:20]:
        lines.append(f"- skipped {item.lemma} from {item.module.track}/{item.module.slug}: {item.reason}")
    if len(result.skipped) > 20:
        lines.append(f"... {len(result.skipped) - 20} more skipped")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", default="folk", help="Curriculum track to scan")
    parser.add_argument("--curriculum-root", type=Path, default=CURRICULUM_ROOT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--dry-run", action="store_true", help="Report entries without writing")
    parser.add_argument("--no-enrich", action="store_true", help="Do not run enrich_manifest.py after adding entries")
    parser.add_argument("--no-fingerprint", action="store_true", help="Do not regenerate the manifest fingerprint")
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = fill_manifest_from_vocab(
        track=args.track,
        curriculum_root=args.curriculum_root,
        manifest_path=args.manifest,
        write=not args.dry_run,
        enrich=not args.no_enrich,
        update_fingerprint=not args.no_fingerprint,
    )
    if args.json:
        print(
            json.dumps(
                {
                    "modules_scanned": result.modules_scanned,
                    "missing_candidates": list(result.missing_candidates),
                    "added": [
                        {
                            "lemma": item.lemma,
                            "module": f"{item.module.track}/{item.module.slug}",
                            "entry": item.entry,
                            "vesum_match": item.vesum_match,
                        }
                        for item in result.added
                    ],
                    "skipped": [
                        {
                            "lemma": item.lemma,
                            "module": f"{item.module.track}/{item.module.slug}",
                            "reason": item.reason,
                        }
                        for item in result.skipped
                    ],
                    "manifest_written": result.manifest_written,
                    "fingerprint_written": result.fingerprint_written,
                    "enrichment_ran": result.enrichment_ran,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(format_result(result))
    return 0


def _load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Manifest must be a JSON object: {path}")
    if not isinstance(payload.get("entries"), list):
        raise ValueError(f"Manifest entries must be a list: {path}")
    return payload


def _manifest_lemma_keys(payload: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for entry in payload.get("entries", []):
        if not isinstance(entry, dict):
            continue
        lemma = entry.get("lemma")
        if isinstance(lemma, str) and lemma.strip():
            keys.add(_lemma_key(lemma))
    return keys


def _vocabulary_modules(curriculum_root: Path, track: str) -> list[ModuleInfo]:
    numbers = _course_module_numbers(curriculum_root)
    modules: list[ModuleInfo] = []
    track_root = curriculum_root / track
    for vocab_path in sorted(track_root.glob("*/vocabulary.yaml")):
        slug = vocab_path.parent.name
        module_num = numbers.get((track, slug), len(modules) + 1)
        modules.append(ModuleInfo(track, slug, module_num, vocab_path))
    return modules


def _course_module_numbers(curriculum_root: Path) -> dict[tuple[str, str], int]:
    path = curriculum_root / "curriculum.yaml"
    if not path.exists():
        return {}
    manifest = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    levels = manifest.get("levels") if isinstance(manifest, dict) else None
    if not isinstance(levels, dict):
        return {}
    numbers: dict[tuple[str, str], int] = {}
    for track, data in levels.items():
        if not isinstance(data, dict):
            continue
        modules = data.get("modules") or []
        if not isinstance(modules, list):
            continue
        for index, raw_slug in enumerate(modules, start=1):
            slug = str(raw_slug).split("#", 1)[0].strip()
            if slug:
                numbers[(str(track), slug)] = index
    return numbers


def _load_vocab_entries(path: Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _entry_lemma(entry: dict[str, Any]) -> str | None:
    for field in LEMMA_FIELDS:
        value = entry.get(field)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _is_single_token_lemma(lemma: str) -> bool:
    return bool(_SINGLE_TOKEN_UK_RE.fullmatch(lemma.strip()))


def _exact_vesum_lemma_match(lemma: str, matches: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    lemma_key = _lemma_key(lemma)
    for match in matches:
        if not isinstance(match, dict):
            continue
        if _lemma_key(str(match.get("lemma") or "")) == lemma_key:
            return match
    return None


def _manifest_entry(
    lemma: str,
    vocab_entry: dict[str, Any],
    module: ModuleInfo,
    vesum_match: dict[str, Any],
) -> dict[str, Any]:
    return {
        "lemma": lemma,
        "url_slug": _slug_for_url(lemma),
        "gloss": vocab_entry.get("translation") or vocab_entry.get("gloss"),
        "pos": vocab_entry.get("pos") or vesum_match.get("pos"),
        "ipa": vocab_entry.get("ipa") or None,
        "primary_source": "built_vocabulary",
        "course_usage": [
            {
                "track": module.track,
                "module_num": module.module_num,
                "slug": module.slug,
                "context": "built_vocabulary",
            }
        ],
    }


def _merge_manifest_modules(payload: dict[str, Any], modules: Sequence[ModuleInfo]) -> None:
    raw_modules = payload.setdefault("modules", [])
    if not isinstance(raw_modules, list):
        payload["modules"] = raw_modules = []
    seen = {
        (str(item.get("track")), str(item.get("slug")))
        for item in raw_modules
        if isinstance(item, dict)
    }
    for module in modules:
        key = (module.track, module.slug)
        if key in seen:
            continue
        raw_modules.append(
            {
                "track": module.track,
                "module_num": module.module_num,
                "slug": module.slug,
            }
        )
        seen.add(key)
    raw_modules.sort(key=lambda item: (str(item.get("track")), int(item.get("module_num") or 0), str(item.get("slug"))))


def _refresh_manifest_stats(payload: dict[str, Any]) -> None:
    entries = payload.get("entries", [])
    modules = payload.get("modules", [])
    if not isinstance(entries, list) or not isinstance(modules, list):
        return
    stats = payload.setdefault("stats", {})
    if not isinstance(stats, dict):
        payload["stats"] = stats = {}
    stats["lemmas_total"] = len(entries)
    stats["modules_covered"] = len(modules)
    stats["from_built"] = sum(
        1 for entry in entries
        if isinstance(entry, dict) and str(entry.get("primary_source") or "").startswith("built_vocabulary")
    )


def _run_enrichment() -> None:
    subprocess.run(
        [str(PYTHON), "scripts/lexicon/enrich_manifest.py"],
        cwd=PROJECT_ROOT,
        check=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
