#!/usr/bin/env python3
"""
Cleanup junk images from textbook image extraction.

Analyzes images and removes clearly useless ones based on:
1. File size < threshold
2. Dimension too small (width OR height < min_dim)
3. Nearly solid color (< min_unique_colors unique pixel values)

Dry-run by default. Pass --execute to actually delete.

Usage:
    .venv/bin/python scripts/cleanup_images.py                    # dry run
    .venv/bin/python scripts/cleanup_images.py --execute          # delete
    .venv/bin/python scripts/cleanup_images.py --grade grade-11   # one grade
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow required. Install: .venv/bin/pip install Pillow")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
IMAGE_DIR = BASE_DIR / "data" / "textbook_images"

# Cleanup thresholds
SIZE_THRESHOLD = 1500       # bytes — images under this are almost always junk
MIN_DIMENSION = 50          # pixels — width OR height below this = junk
MIN_UNIQUE_COLORS = 8       # images with fewer unique colors are solid-color artifacts
MAX_SIZE_FOR_COLOR_CHECK = 5000  # only check color uniqueness for small files
MIN_AREA = 10000            # pixels^2 — images smaller than 100x100 effective area


def analyze_image(path: Path) -> dict:
    """Analyze a single image and return classification."""
    size = path.stat().st_size
    result = {
        "path": str(path.relative_to(BASE_DIR)),
        "filename": path.name,
        "size": size,
        "reason": None,
        "delete": False,
    }

    # Rule 1: Very small files
    if size < SIZE_THRESHOLD:
        try:
            img = Image.open(path)
            w, h = img.size
            result["width"] = w
            result["height"] = h

            # Check if solid color
            pixels = list(img.getdata())
            unique = len(set(pixels[:2000]))  # sample first 2000 pixels
            result["unique_colors"] = unique

            if unique < MIN_UNIQUE_COLORS:
                result["delete"] = True
                result["reason"] = f"solid_color ({unique} colors, {size}B)"
            elif w < MIN_DIMENSION or h < MIN_DIMENSION:
                result["delete"] = True
                result["reason"] = f"tiny_dim ({w}x{h}, {size}B)"
            else:
                result["delete"] = True
                result["reason"] = f"very_small ({size}B, {w}x{h}, {unique} colors)"
            img.close()
        except Exception as e:
            result["delete"] = True
            result["reason"] = f"unreadable ({e})"
        return result

    # Rule 2: Small files — check colors, dimensions, and gradients
    if size < MAX_SIZE_FOR_COLOR_CHECK:
        try:
            img = Image.open(path)
            w, h = img.size
            result["width"] = w
            result["height"] = h

            if w < MIN_DIMENSION or h < MIN_DIMENSION:
                result["delete"] = True
                result["reason"] = f"tiny_dim ({w}x{h}, {size}B)"
                img.close()
                return result

            if w * h < MIN_AREA:
                result["delete"] = True
                result["reason"] = f"tiny_area ({w}x{h}={w*h}px, {size}B)"
                img.close()
                return result

            pixels = list(img.getdata())
            unique = len(set(pixels[:2000]))
            result["unique_colors"] = unique

            if unique < MIN_UNIQUE_COLORS:
                result["delete"] = True
                result["reason"] = f"solid_color ({unique} colors, {size}B)"
                img.close()
                return result

            # Gradient/placeholder detection via edge analysis
            gray = img.convert("L")
            arr = np.array(gray)
            std = float(arr.std())
            dx = float(np.abs(np.diff(arr, axis=1)).mean())
            dy = float(np.abs(np.diff(arr, axis=0)).mean())
            edge_score = dx + dy

            # Smooth gradient or near-solid color
            if edge_score < 25 and std < 50:
                result["delete"] = True
                result["reason"] = f"gradient (edge={edge_score:.1f}, std={std:.1f}, {size}B)"
            # Very low std = near-uniform regardless of edge (shadow edges on solid)
            elif std < 15 and edge_score < 40:
                result["delete"] = True
                result["reason"] = f"near_uniform (std={std:.1f}, edge={edge_score:.1f}, {size}B)"

            gray.close()
            img.close()
        except Exception:
            pass
        return result

    # Rule 3: Larger files — only check dimensions
    try:
        img = Image.open(path)
        w, h = img.size
        result["width"] = w
        result["height"] = h
        if w < MIN_DIMENSION or h < MIN_DIMENSION:
            result["delete"] = True
            result["reason"] = f"tiny_dim ({w}x{h}, {size}B)"
        elif w * h < MIN_AREA:
            result["delete"] = True
            result["reason"] = f"tiny_area ({w}x{h}={w*h}px, {size}B)"
        img.close()
    except Exception:
        pass

    return result


def update_jsonl(grade_dir: Path, deleted_filenames: set):
    """Remove entries from JSONL metadata files for deleted images."""
    updated = 0
    for jsonl_file in grade_dir.glob("*-images.jsonl"):
        lines = jsonl_file.read_text().strip().split("\n")
        original_count = len(lines)
        kept = []
        for line in lines:
            try:
                record = json.loads(line)
                if record.get("filename") not in deleted_filenames:
                    kept.append(line)
            except json.JSONDecodeError:
                kept.append(line)

        removed = original_count - len(kept)
        if removed > 0:
            jsonl_file.write_text("\n".join(kept) + "\n")
            updated += removed
            print(f"  Updated {jsonl_file.name}: removed {removed} entries")
    return updated


def main():
    parser = argparse.ArgumentParser(description="Cleanup junk textbook images")
    parser.add_argument("--execute", action="store_true", help="Actually delete files (default: dry run)")
    parser.add_argument("--grade", help="Only process one grade (e.g., grade-11)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show every file")
    args = parser.parse_args()

    if args.grade:
        grade_dirs = [IMAGE_DIR / args.grade]
    else:
        grade_dirs = sorted(d for d in IMAGE_DIR.iterdir() if d.is_dir() and d.name.startswith("grade-"))

    total_analyzed = 0
    total_delete = 0
    total_kept = 0
    by_reason = {}
    all_to_delete = {}  # grade_dir -> list of results

    for grade_dir in grade_dirs:
        grade = grade_dir.name
        images = sorted(grade_dir.glob("*.png"))
        grade_delete = []

        for img_path in images:
            total_analyzed += 1
            result = analyze_image(img_path)

            if result["delete"]:
                total_delete += 1
                grade_delete.append(result)
                reason_key = result["reason"].split(" (")[0]
                by_reason[reason_key] = by_reason.get(reason_key, 0) + 1
                if args.verbose:
                    print(f"  DELETE: {result['filename']} — {result['reason']}")
            else:
                total_kept += 1

        if grade_delete:
            all_to_delete[grade_dir] = grade_delete
            print(f"{grade}: {len(grade_delete)}/{len(images)} to delete")

    print()
    print(f"{'='*50}")
    print(f"TOTAL analyzed:  {total_analyzed}")
    print(f"TOTAL to delete: {total_delete}")
    print(f"TOTAL to keep:   {total_kept}")
    print()
    print("By reason:")
    for reason, count in sorted(by_reason.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}")
    print()

    if not args.execute:
        print("DRY RUN — no files deleted. Pass --execute to delete.")
        # Save delete list for reference
        delete_list_path = BASE_DIR / "data" / "images_to_delete.txt"
        with open(delete_list_path, "w") as f:
            for _grade_dir, results in all_to_delete.items():
                for r in results:
                    f.write(f"{r['path']}\t{r['reason']}\n")
        print(f"Delete list saved to: {delete_list_path}")
        return

    # Execute deletion
    print("EXECUTING DELETION...")
    deleted_count = 0
    jsonl_updated = 0

    for grade_dir, results in all_to_delete.items():
        grade = grade_dir.name
        deleted_filenames = set()

        for r in results:
            img_path = BASE_DIR / r["path"]
            if img_path.exists():
                img_path.unlink()
                deleted_count += 1
                deleted_filenames.add(r["filename"])

        # Update JSONL metadata
        if deleted_filenames:
            jsonl_updated += update_jsonl(grade_dir, deleted_filenames)

        print(f"  {grade}: deleted {len(deleted_filenames)} images")

    print()
    print(f"Deleted {deleted_count} image files")
    print(f"Removed {jsonl_updated} JSONL entries")


if __name__ == "__main__":
    main()
