"""Export the Word Atlas open dataset shards from lexicon-manifest.json (#10513 / #8977).

Run from the repo root::

    .venv/bin/python scripts/lexicon/export_open_dataset.py --write

Bare invocation and ``--help`` refuse / print usage without writing dataset
files (``#5393`` sibling guard).

SAFETY GUARD (#10513 / AC-02):
Uncertified cards and legacy manifest entries are strictly refused before
writing any output. Cannot export dataset without exact-artifact card certification.
Use ``--draft-mechanics`` for Phase 2/3 draft engineering (AC-03) which isolates
draft artifacts to data/lexicon-dataset/draft/ and marks them export-ineligible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path for direct CLI execution (F4: documented script invocation)
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.atlas.word_card_certification import (
    UncertifiedCardRefusal,
    get_canonical_source_snapshots,
    refuse_uncertified_dataset_export,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DATASET_ROOT = PROJECT_ROOT / "data" / "lexicon-dataset"
DATASET_DIR = DATASET_ROOT / "dataset"

ATTRIBUTION_MD = """# Word Atlas Open Dataset Attribution

This dataset aggregates data from the following sources. The provenance of each field in the dataset is tracked per-entry in the data itself.

- **СУМ-20** (Словник української мови у 20 томах)
- **ЕСУМ** (Етимологічний словник української мови)
- **Горох** (Goroh.pp.ua)
- **kaikki** / **Wiktionary** (English Wiktionary machine-readable extracts) — CC BY-SA 3.0
- **Вікісловник** (Ukrainian Wiktionary) — CC BY-SA
- **Вікіпедія** (Ukrainian Wikipedia) — CC BY-SA
- **Грінченко** (Словарь української мови, 1907-1909) — Public Domain
- **dmklinger** (Dictionary mappings / datasets)
- **ukrainian-word-stress** (Stress marks data)
- **VESUM** (Великий електронний словник української мови)
- **UA-GEC** (Ukrainian Grammatical Error Correction dataset)
- **Learn Ukrainian Project** (Our own derived data, classifications, and course usage)
"""

NOTICE_MD = """# Word Atlas Dataset Notice

All rights to the original definitions, etymologies, and extracted text belong to their respective source creators (e.g., the National Academy of Sciences of Ukraine for СУМ/ЕСУМ, the respective communities for Wikipedia/Wiktionary, etc.).

We claim ownership only over our derived structure, custom classifications, English pedagogical translations, and the specific syllabus-mapping used in the Learn Ukrainian curriculum.

**Takedown Requests:**
If you are the rightsholder of any source material included in this dataset and object to its open publication in this format, please open an issue on our GitHub repository, and we will remove your data upon request.
"""

README_MD = """# Word Atlas Lexicon Dataset

This directory contains the open, sharded dataset of the Word Atlas lexicon.

## Structure

The data is provided in JSONL (JSON Lines) format, sharded by the first letter of the Ukrainian headword (`lemma`), located in the `dataset/` directory.

- `dataset/А.jsonl`, `dataset/Б.jsonl`, etc.
- Each line in the `.jsonl` files is a standalone JSON object representing a single lemma.

## Schema

Each entry represents a single word (lemma) and contains:
- `lemma` (string): The Ukrainian headword.
- `url_slug` (string): Slug used for routing.
- `gloss` (string): English translation/gloss.
- `pos` (string): Part of speech.
- `ipa` (string): International Phonetic Alphabet representation.
- `course_usage` (array): List of course modules where this word is taught.
- Plus any available enriched fields (`etymology`, `definitions`, `paradigm`, `heritage_status`, etc.).

Provenance is tracked per-field where applicable. For full attribution details, see [ATTRIBUTION.md](./ATTRIBUTION.md) and [NOTICE.md](./NOTICE.md).
"""


def build_parser() -> argparse.ArgumentParser:
    """CLI parser for export_open_dataset (``#5393`` argv guard, ``#10513`` safety guard)."""
    parser = argparse.ArgumentParser(
        description=(
            "Export the Word Atlas open dataset (sharded JSONL + attribution docs) "
            "from site/src/data/lexicon-manifest.json. "
            "Requires exact-artifact card certification (AC-02 / Issue #10513). "
            "Bare invocation and --help refuse / print usage without writing dataset files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Print usage without touching any files\n"
            "  .venv/bin/python scripts/lexicon/export_open_dataset.py --help\n\n"
            "  # Export open dataset shards (requires certified cards)\n"
            "  .venv/bin/python scripts/lexicon/export_open_dataset.py --write\n\n"
            "  # Mechanics-only draft export (Phase 2/3 engineering, AC-03)\n"
            "  .venv/bin/python scripts/lexicon/export_open_dataset.py --write --draft-mechanics\n\n"
            "Outputs:\n"
            "  data/lexicon-dataset/ATTRIBUTION.md, NOTICE.md, README.md\n"
            "  data/lexicon-dataset/dataset/*.jsonl  — lemma shards by first letter\n\n"
            "Exit codes:\n"
            "  0  success (--help, or successful export)\n"
            "  2  refused (no --write, uncertified card refusal, or argparse error)\n\n"
            "Related:\n"
            "  issue #10513                        — refuse acceptance/export of uncertified cards\n"
            "  issue #8977                         — word cards programme\n"
            "  issue #5393                         — argv guard sibling"
        ),
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Write open dataset shards and attribution docs. "
            "Refuses if input cards lack exact-artifact certification (Issue #10513). "
            "Default: refuse with usage and exit non-zero (no files touched)."
        ),
    )
    parser.add_argument(
        "--draft-mechanics",
        action="store_true",
        help=(
            "Allow exporting mechanics-only draft artifacts to data/lexicon-dataset/draft/ "
            "without certifying cards (AC-03 / Phase 2/3). Draft files are marked "
            "non-certified and export-ineligible."
        ),
    )
    return parser


def export_dataset(*, allow_draft: bool = False) -> tuple[int, int]:
    """Write open-dataset shards from the card inventory or manifest.

    Enforces AC-02 certification refusal before creating or touching any output files.
    Returns ``(entry_count, shard_count)``.
    """
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found at {MANIFEST_PATH}")

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    # AC-02: Strictly refuse uncertified cards BEFORE touching any dataset directory or writing any files.
    canonical_snapshots = get_canonical_source_snapshots()
    refuse_uncertified_dataset_export(
        manifest,
        allow_draft=allow_draft,
        expected_snapshots=canonical_snapshots or None,
    )

    target_root = DATASET_ROOT if not allow_draft else (DATASET_ROOT / "draft")
    target_dir = DATASET_DIR if not allow_draft else (target_root / "dataset")

    target_root.mkdir(parents=True, exist_ok=True)
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    (target_root / "ATTRIBUTION.md").write_text(ATTRIBUTION_MD, encoding="utf-8")
    (target_root / "NOTICE.md").write_text(NOTICE_MD, encoding="utf-8")
    (target_root / "README.md").write_text(README_MD, encoding="utf-8")

    entries: list[dict[str, Any]] = []
    if "cards" in manifest and isinstance(manifest["cards"], list):
        entries.extend(manifest["cards"])
    if "entries" in manifest and isinstance(manifest["entries"], list):
        entries.extend(manifest["entries"])
    if not entries:
        entries = manifest.get("cards", manifest.get("entries", []))

    # Group entries by first character
    shards: dict[str, list[dict]] = {}
    for entry in entries:
        key_at_creation = entry.get("key_at_creation") if isinstance(entry, dict) else None
        spelling = key_at_creation.get("spelling", "") if isinstance(key_at_creation, dict) else ""
        lemma = entry.get("lemma") or spelling
        if not lemma:
            continue

        first_char = lemma[0].upper()
        if not first_char.isalpha():
            first_char = "symbol"

        if first_char not in shards:
            shards[first_char] = []
        shards[first_char].append(entry)

    shard_integrity: dict[str, dict[str, Any]] = {}

    for char, char_entries in shards.items():
        shard_filename = f"{char}.jsonl"
        file_path = target_dir / shard_filename
        tmp_path = target_dir / f"{shard_filename}.tmp"

        hasher = hashlib.sha256()
        total_bytes = 0
        with open(tmp_path, "w", encoding="utf-8") as out_f:
            for entry in char_entries:
                line = json.dumps(entry, ensure_ascii=False) + "\n"
                encoded = line.encode("utf-8")
                hasher.update(encoded)
                total_bytes += len(encoded)
                out_f.write(line)

        tmp_path.replace(file_path)
        shard_integrity[shard_filename] = {
            "sha256": hasher.hexdigest(),
            "bytes": total_bytes,
            "entries": len(char_entries),
        }

    metadata = {k: v for k, v in manifest.items() if k not in ("entries", "cards")}
    metadata["shard_integrity"] = shard_integrity
    metadata["certified"] = not allow_draft
    metadata["draft_engineering"] = allow_draft
    metadata["export_eligible"] = not allow_draft

    meta_file = target_dir / "_metadata.json"
    meta_tmp = target_dir / "_metadata.json.tmp"
    meta_tmp.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    meta_tmp.replace(meta_file)

    return len(entries), len(shards)


def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI args and export only when ``--write`` is given and cards are certified."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.write:
        parser.error(
            "refusing to export the open dataset without --write "
            "(writes data/lexicon-dataset/; pass --write to proceed)"
        )

    try:
        entry_count, shard_count = export_dataset(allow_draft=args.draft_mechanics)
    except UncertifiedCardRefusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    target_dir = DATASET_DIR if not args.draft_mechanics else (DATASET_ROOT / "draft" / "dataset")
    mode_str = "certified" if not args.draft_mechanics else "draft mechanics"
    print(
        f"Exported {entry_count} entries ({mode_str}) to {target_dir.relative_to(PROJECT_ROOT)} "
        f"across {shard_count} shards."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
