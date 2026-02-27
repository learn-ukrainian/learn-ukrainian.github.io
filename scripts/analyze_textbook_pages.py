#!/usr/bin/env python3
"""Analyze textbook pages with Gemini Vision to extract image+text pairs.

Sends full-page renders (image_index=0) to Gemini 2.0 Flash, which identifies
visual elements and their associated Ukrainian text. This preserves the
pedagogical context that's lost when images are extracted individually.

Auth: Set GOOGLE_API_KEY env var (generate at https://aistudio.google.com/apikey).
      Keys from Ultra accounts get Ultra rate limits automatically.

Usage:
    # Analyze grade 1-2 pages (priority for l2-uk-direct A1)
    .venv/bin/python scripts/analyze_textbook_pages.py --grade grade-01 grade-02

    # Analyze all grades
    .venv/bin/python scripts/analyze_textbook_pages.py --all

    # Resume (skips already-processed pages automatically)
    .venv/bin/python scripts/analyze_textbook_pages.py --grade grade-01

    # Show stats from existing analysis
    .venv/bin/python scripts/analyze_textbook_pages.py --stats

    # Link analysis results back to extracted sub-images
    .venv/bin/python scripts/analyze_textbook_pages.py --link

    # Identify junk sub-images (dry run)
    .venv/bin/python scripts/analyze_textbook_pages.py --cleanup

    # Delete junk sub-images
    .venv/bin/python scripts/analyze_textbook_pages.py --cleanup --execute
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_DIR = BASE_DIR / "data" / "textbook_images"
ANALYSIS_FILE = IMAGE_DIR / "page_analysis.jsonl"
PAIRS_FILE = IMAGE_DIR / "image_text_pairs.jsonl"

MODEL = "gemini-2.0-flash"
MAX_CONCURRENT = 10
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0

VISION_PROMPT = """You are analyzing a Ukrainian school textbook page for a language learning app.

For each distinct visual element on this page (illustration, photo, diagram, letter display, chart, map, table), identify:
1. What the visual element depicts
2. The Ukrainian text most closely associated with it (word, phrase, or sentence that appears near it or labels it)
3. Whether this element is useful for teaching Ukrainian

Respond ONLY with valid JSON:
{
  "page_type": "lesson|exercise|reference|title|contents|blank",
  "elements": [
    {
      "type": "illustration|photo|diagram|letter|chart|map|table|QR|decoration|logo",
      "description_en": "A red apple with a green leaf",
      "associated_text_uk": "яблуко",
      "teaching_value": "high|medium|low|none",
      "position": "top-left|top-center|top-right|center-left|center|center-right|bottom-left|bottom-center|bottom-right"
    }
  ]
}

Rules:
- Include EVERY visual element, even junk (decorations, logos, QR codes)
- associated_text_uk must be EXACT Ukrainian text from the page (not translated)
- If no Ukrainian text is associated, use null
- teaching_value: high = clear teaching image with text, medium = useful but indirect, low = marginally useful, none = decoration/junk"""


def load_processed_ids() -> set[str]:
    """Load already-processed page IDs from the analysis file."""
    if not ANALYSIS_FILE.exists():
        return set()
    ids = set()
    for line in ANALYSIS_FILE.read_text().strip().split("\n"):
        if not line:
            continue
        try:
            ids.add(json.loads(line)["page_id"])
        except (json.JSONDecodeError, KeyError):
            pass
    return ids


def load_full_pages(grade_dirs: list[Path]) -> list[dict]:
    """Load metadata for all full-page images (image_index=0) in given grades."""
    pages = []
    for grade_dir in grade_dirs:
        if not grade_dir.exists():
            print(f"WARNING: {grade_dir} does not exist, skipping")
            continue
        for jsonl_file in sorted(grade_dir.glob("*-images.jsonl")):
            for line in jsonl_file.read_text().strip().split("\n"):
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("image_index") == 0:
                    # Resolve image path
                    img_path = BASE_DIR / record["image_path"]
                    if not img_path.exists():
                        # Try relative from IMAGE_DIR
                        parts = record["image_path"].split("/")
                        img_path = IMAGE_DIR / parts[-2] / parts[-1] if len(parts) >= 2 else img_path
                    record["_resolved_path"] = img_path
                    pages.append(record)
    return pages


async def analyze_page(
    client,
    types_module,
    record: dict,
    semaphore: asyncio.Semaphore,
    progress: dict,
) -> dict | None:
    """Analyze a single page with Gemini Vision."""
    page_id = record["image_id"]
    img_path: Path = record["_resolved_path"]

    if not img_path.exists():
        progress["skipped"] += 1
        return None

    img_bytes = img_path.read_bytes()

    async with semaphore:
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.aio.models.generate_content(
                    model=MODEL,
                    contents=[
                        types_module.Part.from_bytes(
                            data=img_bytes, mime_type="image/png"
                        ),
                        VISION_PROMPT,
                    ],
                    config={
                        "response_mime_type": "application/json",
                        "temperature": 0.1,
                    },
                )

                # Parse JSON response
                text = response.text.strip()
                # Handle markdown code blocks
                if text.startswith("```"):
                    text = text.split("\n", 1)[1]
                    if text.endswith("```"):
                        text = text[:-3].strip()

                data = json.loads(text)

                result = {
                    "page_id": page_id,
                    "page": record.get("page", 0),
                    "grade": record.get("grade", 0),
                    "subject": record.get("subject", ""),
                    "author": record.get("author", ""),
                    "pdf_stem": record.get("pdf_stem", ""),
                    "page_type": data.get("page_type", "unknown"),
                    "elements": data.get("elements", []),
                    "model": MODEL,
                    "ts": datetime.now(timezone.utc).isoformat(),
                }

                progress["done"] += 1
                total = progress["total"]
                done = progress["done"]
                skipped = progress["skipped"]
                elapsed = time.time() - progress["start"]
                rate = done / elapsed if elapsed > 0 else 0
                eta = (total - done - skipped) / rate if rate > 0 else 0
                n_elements = len(result["elements"])
                print(
                    f"\r[{done + skipped}/{total}] "
                    f"{img_path.parent.name}/{img_path.name} "
                    f"→ {n_elements} elements ({result['page_type']}) "
                    f"[{rate:.1f}/s, ETA {eta/60:.0f}m]   ",
                    end="",
                    flush=True,
                )
                return result

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    wait = INITIAL_BACKOFF * (2**attempt)
                    print(
                        f"\n  Rate limited on {page_id}, waiting {wait:.0f}s "
                        f"(attempt {attempt + 1}/{MAX_RETRIES})"
                    )
                    await asyncio.sleep(wait)
                elif "500" in err_str or "503" in err_str:
                    wait = INITIAL_BACKOFF * (2**attempt)
                    print(
                        f"\n  Server error on {page_id}, retrying in {wait:.0f}s "
                        f"(attempt {attempt + 1}/{MAX_RETRIES})"
                    )
                    await asyncio.sleep(wait)
                else:
                    print(f"\n  ERROR on {page_id}: {e}")
                    progress["errors"] += 1
                    return None

        print(f"\n  FAILED after {MAX_RETRIES} retries: {page_id}")
        progress["errors"] += 1
        return None


async def run_analysis(pages: list[dict], processed_ids: set[str]):
    """Run vision analysis on all unprocessed pages."""
    from google import genai
    from google.genai import types as genai_types

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: Set GOOGLE_API_KEY or GEMINI_API_KEY env var.")
        print("  Generate at: https://aistudio.google.com/apikey")
        print("  Ultra subscription keys get Ultra rate limits.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Filter already processed
    to_process = [p for p in pages if p["image_id"] not in processed_ids]
    if not to_process:
        print("All pages already processed!")
        return

    print(f"Pages to analyze: {len(to_process)} (skipping {len(pages) - len(to_process)} already done)")
    print(f"Model: {MODEL}, concurrency: {MAX_CONCURRENT}")
    print()

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    progress = {
        "done": 0,
        "skipped": 0,
        "errors": 0,
        "total": len(to_process),
        "start": time.time(),
    }

    # Open output file in append mode
    ANALYSIS_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Process in batches to write results incrementally
    batch_size = 50
    for batch_start in range(0, len(to_process), batch_size):
        batch = to_process[batch_start : batch_start + batch_size]
        tasks = [
            analyze_page(client, genai_types, record, semaphore, progress)
            for record in batch
        ]
        results = await asyncio.gather(*tasks)

        # Write successful results
        with open(ANALYSIS_FILE, "a") as f:
            for result in results:
                if result is not None:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")

    elapsed = time.time() - progress["start"]
    print(f"\n\nDone! {progress['done']} pages analyzed in {elapsed:.0f}s")
    print(f"  Errors: {progress['errors']}, Skipped: {progress['skipped']}")
    print(f"  Output: {ANALYSIS_FILE}")


def show_stats():
    """Show statistics from existing analysis."""
    if not ANALYSIS_FILE.exists():
        print("No analysis file found. Run analysis first.")
        return

    records = []
    for line in ANALYSIS_FILE.read_text().strip().split("\n"):
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass

    if not records:
        print("No records found.")
        return

    print(f"Total pages analyzed: {len(records)}")
    print()

    # By grade
    by_grade = {}
    for r in records:
        g = r.get("grade", 0)
        by_grade.setdefault(g, []).append(r)

    print("By grade:")
    for grade in sorted(by_grade):
        grade_records = by_grade[grade]
        total_elements = sum(len(r.get("elements", [])) for r in grade_records)
        print(f"  Grade {grade:2d}: {len(grade_records):5d} pages, {total_elements:6d} elements")

    # By page type
    print()
    by_type = {}
    for r in records:
        pt = r.get("page_type", "unknown")
        by_type[pt] = by_type.get(pt, 0) + 1
    print("By page type:")
    for pt, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {pt:15s}: {count:5d}")

    # By teaching value
    print()
    by_value = {"high": 0, "medium": 0, "low": 0, "none": 0}
    total_elements = 0
    for r in records:
        for el in r.get("elements", []):
            tv = el.get("teaching_value", "none")
            by_value[tv] = by_value.get(tv, 0) + 1
            total_elements += 1
    print(f"Elements by teaching value (total: {total_elements}):")
    for tv in ["high", "medium", "low", "none"]:
        count = by_value[tv]
        pct = count / total_elements * 100 if total_elements else 0
        print(f"  {tv:8s}: {count:6d} ({pct:.1f}%)")

    # By element type
    print()
    by_etype = {}
    for r in records:
        for el in r.get("elements", []):
            et = el.get("type", "unknown")
            by_etype[et] = by_etype.get(et, 0) + 1
    print("By element type:")
    for et, count in sorted(by_etype.items(), key=lambda x: -x[1]):
        print(f"  {et:15s}: {count:5d}")

    # Elements with Ukrainian text
    print()
    with_text = sum(
        1
        for r in records
        for el in r.get("elements", [])
        if el.get("associated_text_uk")
    )
    print(f"Elements with Ukrainian text: {with_text}/{total_elements} "
          f"({with_text / total_elements * 100:.1f}%)" if total_elements else "")


def link_to_sub_images():
    """Match page-level elements to extracted sub-images."""
    if not ANALYSIS_FILE.exists():
        print("No analysis file found. Run analysis first.")
        return

    # Load all page analyses
    analyses = {}
    for line in ANALYSIS_FILE.read_text().strip().split("\n"):
        if not line:
            continue
        try:
            r = json.loads(line)
            analyses[r["page_id"]] = r
        except (json.JSONDecodeError, KeyError):
            pass

    print(f"Loaded {len(analyses)} page analyses")

    # Load all sub-image metadata (image_index >= 1)
    sub_images = []
    for jsonl_file in sorted(IMAGE_DIR.rglob("*-images.jsonl")):
        for line in jsonl_file.read_text().strip().split("\n"):
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("image_index", 0) >= 1:
                sub_images.append(record)

    print(f"Found {len(sub_images)} sub-images to link")

    # Match: for each sub-image, find its parent page analysis
    pairs = []
    matched = 0
    unmatched = 0

    for sub in sub_images:
        # Build parent page_id: same pdf_stem + page, image_index=0
        parent_id = f"{sub['pdf_stem']}_p{sub['page']:03d}_i00"

        if parent_id not in analyses:
            unmatched += 1
            # Still create a record but mark as unmatched
            pairs.append({
                "image_id": sub["image_id"],
                "image_path": sub["image_path"],
                "filename": sub["filename"],
                "associated_text_uk": None,
                "description_en": None,
                "teaching_value": "unmatched",
                "page": sub["page"],
                "grade": sub.get("grade", 0),
                "subject": sub.get("subject", ""),
                "author": sub.get("author", ""),
                "pdf_stem": sub["pdf_stem"],
                "width": sub.get("width", 0),
                "height": sub.get("height", 0),
                "file_size": sub.get("file_size", 0),
            })
            continue

        analysis = analyses[parent_id]
        elements = analysis.get("elements", [])

        # Simple strategy: assign elements to sub-images by order
        # Sub-images are extracted in page order; elements are listed top-to-bottom
        # This is imperfect but provides a reasonable starting point
        img_idx = sub["image_index"] - 1  # 0-based index into elements

        # Filter to non-junk elements (skip decorations, QR, logos)
        teaching_elements = [
            e for e in elements
            if e.get("teaching_value") in ("high", "medium", "low")
        ]

        if img_idx < len(teaching_elements):
            el = teaching_elements[img_idx]
            pairs.append({
                "image_id": sub["image_id"],
                "image_path": sub["image_path"],
                "filename": sub["filename"],
                "associated_text_uk": el.get("associated_text_uk"),
                "description_en": el.get("description_en"),
                "teaching_value": el.get("teaching_value", "unknown"),
                "element_type": el.get("type"),
                "position": el.get("position"),
                "page": sub["page"],
                "grade": sub.get("grade", 0),
                "subject": sub.get("subject", ""),
                "author": sub.get("author", ""),
                "pdf_stem": sub["pdf_stem"],
                "width": sub.get("width", 0),
                "height": sub.get("height", 0),
            })
            matched += 1
        elif elements:
            # More sub-images than teaching elements — use page-level info
            # Mark as having partial context from the page
            pairs.append({
                "image_id": sub["image_id"],
                "image_path": sub["image_path"],
                "filename": sub["filename"],
                "associated_text_uk": None,
                "description_en": None,
                "teaching_value": "unlinked",
                "page": sub["page"],
                "page_type": analysis.get("page_type"),
                "grade": sub.get("grade", 0),
                "subject": sub.get("subject", ""),
                "author": sub.get("author", ""),
                "pdf_stem": sub["pdf_stem"],
                "width": sub.get("width", 0),
                "height": sub.get("height", 0),
            })
            unmatched += 1
        else:
            unmatched += 1
            pairs.append({
                "image_id": sub["image_id"],
                "image_path": sub["image_path"],
                "filename": sub["filename"],
                "associated_text_uk": None,
                "description_en": None,
                "teaching_value": "unmatched",
                "page": sub["page"],
                "grade": sub.get("grade", 0),
                "subject": sub.get("subject", ""),
                "author": sub.get("author", ""),
                "pdf_stem": sub["pdf_stem"],
                "width": sub.get("width", 0),
                "height": sub.get("height", 0),
            })

    # Write pairs
    with open(PAIRS_FILE, "w") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    print(f"\nLinked {matched} sub-images to page elements")
    print(f"Unmatched/unlinked: {unmatched}")
    print(f"Output: {PAIRS_FILE}")

    # Stats on linked pairs
    with_text = sum(1 for p in pairs if p.get("associated_text_uk"))
    print(f"Pairs with Ukrainian text: {with_text}")


def cleanup_junk(execute: bool = False):
    """Identify and optionally delete junk sub-images based on page analysis."""
    if not ANALYSIS_FILE.exists():
        print("No analysis file found. Run analysis first.")
        return

    # Load analyses indexed by (pdf_stem, page)
    page_elements = {}
    for line in ANALYSIS_FILE.read_text().strip().split("\n"):
        if not line:
            continue
        try:
            r = json.loads(line)
            key = (r.get("pdf_stem", ""), r.get("page", 0))
            page_elements[key] = r
        except (json.JSONDecodeError, KeyError):
            pass

    # Find junk sub-images
    junk_files = []  # (path, reason)
    kept = 0

    for grade_dir in sorted(IMAGE_DIR.iterdir()):
        if not grade_dir.is_dir() or not grade_dir.name.startswith("grade-"):
            continue

        for jsonl_file in sorted(grade_dir.glob("*-images.jsonl")):
            for line in jsonl_file.read_text().strip().split("\n"):
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if record.get("image_index", 0) == 0:
                    continue  # Keep full-page renders

                img_path = BASE_DIR / record["image_path"]
                if not img_path.exists():
                    continue

                key = (record.get("pdf_stem", ""), record.get("page", 0))
                analysis = page_elements.get(key)

                if analysis is None:
                    # Page not analyzed — check if tiny file
                    if img_path.stat().st_size < 5000:
                        junk_files.append((img_path, "unanalyzed_tiny"))
                    else:
                        kept += 1
                    continue

                # Check if ALL elements on this page are junk
                elements = analysis.get("elements", [])
                has_teaching = any(
                    e.get("teaching_value") in ("high", "medium")
                    for e in elements
                )

                if not has_teaching and img_path.stat().st_size < 5000:
                    junk_files.append((img_path, "no_teaching_tiny"))
                elif not elements:
                    if img_path.stat().st_size < 5000:
                        junk_files.append((img_path, "empty_page_tiny"))
                    else:
                        kept += 1
                else:
                    kept += 1

    print(f"Junk sub-images found: {len(junk_files)}")
    print(f"Kept: {kept}")

    if not junk_files:
        print("Nothing to clean up!")
        return

    # Show breakdown by reason
    by_reason = {}
    total_size = 0
    for path, reason in junk_files:
        by_reason[reason] = by_reason.get(reason, 0) + 1
        total_size += path.stat().st_size

    print(f"\nBy reason:")
    for reason, count in sorted(by_reason.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}")
    print(f"Total size: {total_size / 1024:.0f} KB")

    if not execute:
        print("\nDRY RUN — pass --execute to delete.")
        return

    # Execute deletion
    deleted = 0
    deleted_by_grade = {}

    for path, _reason in junk_files:
        grade_dir = path.parent
        grade = grade_dir.name
        deleted_by_grade.setdefault(grade, set()).add(path.name)
        path.unlink()
        deleted += 1

    # Update JSONL metadata
    jsonl_updated = 0
    for grade, filenames in deleted_by_grade.items():
        grade_dir = IMAGE_DIR / grade
        for jsonl_file in grade_dir.glob("*-images.jsonl"):
            lines = jsonl_file.read_text().strip().split("\n")
            original_count = len(lines)
            kept_lines = []
            for line in lines:
                try:
                    record = json.loads(line)
                    if record.get("filename") not in filenames:
                        kept_lines.append(line)
                except json.JSONDecodeError:
                    kept_lines.append(line)
            removed = original_count - len(kept_lines)
            if removed > 0:
                jsonl_file.write_text("\n".join(kept_lines) + "\n")
                jsonl_updated += removed

    print(f"\nDeleted {deleted} files")
    print(f"Updated {jsonl_updated} JSONL entries")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze textbook pages with Gemini Vision"
    )
    parser.add_argument(
        "--grade",
        nargs="+",
        help="Grade directories to process (e.g., grade-01 grade-02)",
    )
    parser.add_argument("--all", action="store_true", help="Process all grades")
    parser.add_argument(
        "--stats", action="store_true", help="Show statistics from existing analysis"
    )
    parser.add_argument(
        "--link",
        action="store_true",
        help="Link page analysis to extracted sub-images",
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Identify junk sub-images for deletion"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete files (with --cleanup)",
    )
    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    if args.link:
        link_to_sub_images()
        return

    if args.cleanup:
        cleanup_junk(execute=args.execute)
        return

    # Determine grade directories
    if args.all:
        grade_dirs = sorted(
            d
            for d in IMAGE_DIR.iterdir()
            if d.is_dir() and d.name.startswith("grade-")
        )
    elif args.grade:
        grade_dirs = [IMAGE_DIR / g for g in args.grade]
    else:
        parser.print_help()
        print("\nSpecify --grade, --all, --stats, --link, or --cleanup")
        sys.exit(1)

    print(f"Grades: {', '.join(d.name for d in grade_dirs)}")

    # Load pages and check what's already done
    pages = load_full_pages(grade_dirs)
    processed = load_processed_ids()
    print(f"Full-page images found: {len(pages)}")
    print(f"Already processed: {len(processed)}")

    # Run analysis
    asyncio.run(run_analysis(pages, processed))


if __name__ == "__main__":
    main()
