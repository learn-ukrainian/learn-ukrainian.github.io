"""Re-attribute quarantined ukrlib JSONL files with correct author metadata.

ukrlib.com.ua has broken author-to-works database mappings for several IDs.
The scraper correctly downloaded the texts but stamped them with wrong author
metadata. This script fixes the metadata and writes corrected JSONL files.

See: https://github.com/... (issue #807)

Usage:
    .venv/bin/python scripts/rag/reattribute_ukrlib.py
    .venv/bin/python scripts/rag/reattribute_ukrlib.py --dry-run
"""

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.config import LITERARY_DIR

QUARANTINE_DIR = LITERARY_DIR / "_quarantine"

# Files that are duplicates of existing correct files — delete, don't reattribute
DUPLICATES = {
    "ukrlib-kotlyarevsky.jsonl": "ukrlib-shevchenko.jsonl",
    "ukrlib-kotsyubynsky.jsonl": "ukrlib-skovoroda.jsonl",
    "ukrlib-vynnychenko.jsonl": "ukrlib-karpenko_karyi.jsonl",
}

# Files to reattribute: quarantined filename → correction metadata
REATTRIBUTE = {
    "ukrlib-kvitka.jsonl": {
        "old_author": "Квітка-Основ'яненко Г.",
        "new_author": "Коцюбинський М.",
        "old_prefix": "Григорій Квітка-Основ'яненко",
        "new_prefix": "Михайло Коцюбинський",
        "new_filename": "ukrlib-kotsyubynsky.jsonl",
        "year": 1864,
    },
    "ukrlib-myrny.jsonl": {
        "old_author": "Мирний П.",
        "new_author": "Котляревський І.",
        "old_prefix": "Панас Мирний",
        "new_prefix": "Іван Котляревський",
        "new_filename": "ukrlib-kotlyarevsky.jsonl",
        "year": 1769,
    },
    "ukrlib-tychyna.jsonl": {
        "old_author": "Тичина П.",
        "new_author": "Мирний П.",
        "old_prefix": "Павло Тичина",
        "new_prefix": "Панас Мирний",
        "new_filename": "ukrlib-myrny.jsonl",
        "year": 1849,
    },
    "ukrlib-nechuy.jsonl": {
        "old_author": "Нечуй-Левицький І.",
        "new_author": "Тичина П.",
        "old_prefix": "Іван Нечуй-Левицький",
        "new_prefix": "Павло Тичина",
        "new_filename": "ukrlib-tychyna.jsonl",
        "year": 1891,
    },
    "ukrlib-rylsky.jsonl": {
        "old_author": "Рильський М.",
        "new_author": "Нечуй-Левицький І.",
        "old_prefix": "Максим Рильський",
        "new_prefix": "Іван Нечуй-Левицький",
        "new_filename": "ukrlib-nechuy.jsonl",
        "year": 1838,
    },
}


def reattribute_chunk(chunk: dict, mapping: dict) -> dict:
    """Fix author metadata in a single chunk."""
    new = dict(chunk)

    # Fix author
    new["author"] = mapping["new_author"]

    # Fix work title prefix: "Old Author. Title" → "New Author. Title"
    work = new.get("work", "")
    if work.startswith(mapping["old_prefix"] + ". "):
        title = work[len(mapping["old_prefix"]) + 2:]  # strip "Old Author. "
        new["work"] = f"{mapping['new_prefix']}. {title}"
    elif work.startswith(mapping["old_prefix"]):
        # Handle edge case where there's no ". " separator
        rest = work[len(mapping["old_prefix"]):]
        new["work"] = mapping["new_prefix"] + rest

    # Fix year
    new["year"] = mapping["year"]

    # Regenerate chunk_id (includes work title in MD5)
    old_id = new["chunk_id"]
    # Extract chunk index suffix (e.g., "_c0042")
    suffix = old_id[old_id.index("_c"):]
    new_hash = hashlib.md5(new["work"].encode(), usedforsecurity=False).hexdigest()[:8]
    new["chunk_id"] = f"{new_hash}{suffix}"

    return new


def run(dry_run: bool = False) -> dict:
    """Run the reattribution. Returns stats dict."""
    stats = {"reattributed": {}, "skipped_duplicates": [], "errors": []}

    if not QUARANTINE_DIR.exists():
        print(f"ERROR: Quarantine directory not found: {QUARANTINE_DIR}")
        return stats

    # Process reattributions
    for src_name, mapping in REATTRIBUTE.items():
        src_path = QUARANTINE_DIR / src_name
        dst_path = LITERARY_DIR / mapping["new_filename"]

        if not src_path.exists():
            stats["errors"].append(f"Missing: {src_path}")
            print(f"  ERROR: {src_name} not found in quarantine")
            continue

        if dst_path.exists():
            stats["errors"].append(f"Target already exists: {dst_path}")
            print(f"  ERROR: {dst_path.name} already exists — would overwrite!")
            continue

        print(f"\n  {src_name} → {mapping['new_filename']}")
        print(f"    {mapping['old_author']} → {mapping['new_author']}")

        chunks = []
        with open(src_path, encoding="utf-8") as f:
            for line in f:
                chunk = json.loads(line)
                chunks.append(reattribute_chunk(chunk, mapping))

        print(f"    {len(chunks)} chunks reattributed")

        if not dry_run:
            with open(dst_path, "w", encoding="utf-8") as f:
                for chunk in chunks:
                    f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            print(f"    Written: {dst_path}")

        stats["reattributed"][mapping["new_filename"]] = len(chunks)

    # Report duplicates (not processed, just noted)
    for dup_name, correct_name in DUPLICATES.items():
        dup_path = QUARANTINE_DIR / dup_name
        correct_path = LITERARY_DIR / correct_name
        if dup_path.exists() and correct_path.exists():
            stats["skipped_duplicates"].append(dup_name)
            print(f"\n  DUPLICATE: {dup_name} (correct data in {correct_name})")

    return stats


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Re-attribute quarantined ukrlib JSONL files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without writing")
    args = parser.parse_args()

    print("=" * 60)
    print("Re-attributing quarantined ukrlib files")
    print("=" * 60)

    stats = run(dry_run=args.dry_run)

    print(f"\n{'=' * 60}")
    print(f"Reattributed: {len(stats['reattributed'])} files, "
          f"{sum(stats['reattributed'].values())} total chunks")
    print(f"Duplicates skipped: {len(stats['skipped_duplicates'])}")
    if stats["errors"]:
        print(f"ERRORS: {len(stats['errors'])}")
        for e in stats["errors"]:
            print(f"  - {e}")

    if args.dry_run:
        print("\n(dry run — no files written)")


if __name__ == "__main__":
    main()
