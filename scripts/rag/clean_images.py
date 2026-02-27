"""Clean extracted textbook images — remove covers, backgrounds, and junk.

Filters:
1. Book covers (page 1, image index 0)
2. Full-page backgrounds (repeated identical dimensions, likely watermarks)
3. Back cover / last-page publisher info

Usage:
    .venv/bin/python scripts/rag/clean_images.py --dry-run   # preview what gets removed
    .venv/bin/python scripts/rag/clean_images.py              # actually remove files
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import IMAGES_DIR


def analyze_and_clean(dry_run: bool = True, grades: list[int] | None = None):
    """Find and optionally remove junk images."""
    total_removed = 0
    total_kept = 0

    for grade_dir in sorted(IMAGES_DIR.iterdir()):
        if not grade_dir.is_dir() or not grade_dir.name.startswith("grade-"):
            continue
        grade_num = int(grade_dir.name.split("-")[1])
        if grades and grade_num not in grades:
            continue

        for jsonl in sorted(grade_dir.glob("*-images.jsonl")):
            records = [json.loads(line) for line in open(jsonl)]
            if not records:
                continue

            max_page = max(r["page"] for r in records)

            # Detect repeated full-page backgrounds
            dims = Counter((r["width"], r["height"]) for r in records)
            background_dims = set()
            for dim, count in dims.items():
                # If same dimension appears on >30% of pages, it's a background
                if count > max_page * 0.3 and dim[0] > 400 and dim[1] > 400:
                    background_dims.add(dim)

            keep = []
            remove = []

            for r in records:
                reason = None
                w, h = r["width"], r["height"]

                # Rule 1: Book cover (page 1, first image, large)
                if r["page"] == 1 and r["image_index"] == 0 and w > 300 and h > 300:
                    reason = "cover"

                # Rule 2: Full-page background/watermark
                elif (w, h) in background_dims:
                    reason = f"background ({w}x{h} repeated {dims[(w,h)]}x)"

                # Rule 3: Last page publisher logos (last 2 pages, small)
                elif r["page"] >= max_page - 1 and w < 200 and h < 200:
                    reason = "last-page small"

                if reason:
                    remove.append((r, reason))
                else:
                    keep.append(r)

            if remove:
                print(f"\n{jsonl.name}: removing {len(remove)}/{len(records)}, keeping {len(keep)}")
                for r, reason in remove[:5]:
                    print(f"  - p{r['page']:03d} i{r['image_index']:02d} {r['width']}x{r['height']} [{reason}]")
                if len(remove) > 5:
                    print(f"  ... and {len(remove) - 5} more")

                if not dry_run:
                    # Delete image files
                    for r, _ in remove:
                        img_path = grade_dir / r["filename"]
                        if img_path.exists():
                            img_path.unlink()

                    # Rewrite JSONL with only kept records
                    with open(jsonl, "w", encoding="utf-8") as f:
                        for r in keep:
                            f.write(json.dumps(r, ensure_ascii=False) + "\n")

                total_removed += len(remove)
                total_kept += len(keep)
            else:
                total_kept += len(records)

    action = "Would remove" if dry_run else "Removed"
    print(f"\n=== {action} {total_removed} images, kept {total_kept} ===")
    if dry_run and total_removed:
        print("Run without --dry-run to actually delete files.")


def main():
    parser = argparse.ArgumentParser(description="Clean junk images from textbook extractions")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't delete")
    parser.add_argument("--grade", type=int, nargs="+", help="Filter by grades")
    args = parser.parse_args()

    analyze_and_clean(dry_run=args.dry_run, grades=args.grade)


if __name__ == "__main__":
    main()
