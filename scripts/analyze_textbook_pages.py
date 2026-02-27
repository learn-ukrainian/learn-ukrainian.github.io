#!/usr/bin/env python3
"""Analyze textbook pages with Gemini Vision to extract image+text pairs.

Renders each PDF page with pymupdf and sends it to Gemini via gemini-cli,
which uses the user's Ultra subscription auth. Identifies visual elements
and their associated Ukrainian text, preserving pedagogical context.

Auth: Uses gemini-cli OAuth (Google AI Ultra subscription).
      No API key needed — gemini-cli must be installed and authenticated.

Usage:
    # Analyze grade 1-2 pages (priority for l2-uk-direct A1)
    .venv/bin/python scripts/analyze_textbook_pages.py --grade 1 2

    # Analyze all grades
    .venv/bin/python scripts/analyze_textbook_pages.py --all

    # Resume (skips already-processed pages automatically)
    .venv/bin/python scripts/analyze_textbook_pages.py --grade 1

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
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import pymupdf

BASE_DIR = Path(__file__).resolve().parent.parent
TEXTBOOKS_DIR = BASE_DIR / "data" / "textbooks"
IMAGE_DIR = BASE_DIR / "data" / "textbook_images"
ANALYSIS_FILE = IMAGE_DIR / "page_analysis.jsonl"
PAIRS_FILE = IMAGE_DIR / "image_text_pairs.jsonl"

RENDER_DPI = 150  # ~1250x1625 for A4, good balance of quality vs size
MAX_RETRIES = 3
RETRY_DELAY = 5.0

VISION_PROMPT = """Read the image file at {image_path}

You are analyzing a Ukrainian school textbook page for a language learning app.

For each distinct visual element on this page (illustration, photo, diagram, letter display, chart, map, table), identify:
1. What the visual element depicts (describe in Ukrainian)
2. The Ukrainian text most closely associated with it (word, phrase, or sentence that appears near it or labels it)
3. Whether this element is useful for teaching Ukrainian

Respond ONLY with valid JSON (no markdown, no code fences, no explanation):
{{"page_type": "lesson|exercise|reference|title|contents|blank", "elements": [{{"type": "illustration|photo|diagram|letter|chart|map|table|QR|decoration|logo", "description_uk": "Червоне яблуко із зеленим листком", "associated_text_uk": "яблуко", "teaching_value": "high|medium|low|none", "position": "top-left|top-center|top-right|center-left|center|center-right|bottom-left|bottom-center|bottom-right"}}]}}

Rules:
- Include EVERY visual element, even junk (decorations, logos, QR codes)
- description_uk: describe in Ukrainian what the image shows
- associated_text_uk must be EXACT Ukrainian text from the page (not translated)
- If no Ukrainian text is associated, use null
- teaching_value: high = clear teaching image with text, medium = useful but indirect, low = marginally useful, none = decoration/junk"""


def parse_pdf_stem(pdf_path: Path) -> dict:
    """Parse metadata from PDF filename."""
    stem = pdf_path.stem
    parts = stem.split("-")
    meta = {"pdf_stem": stem, "grade": 0, "subject": "", "author": "", "year": 0}
    try:
        meta["grade"] = int(parts[0])
    except (ValueError, IndexError):
        pass
    # Find author, year, subject from naming convention
    # {grade}-klas-{subject}-{author}-{year}[-{part}].pdf
    if len(parts) >= 4:
        meta["subject"] = "-".join(parts[2:-2]) if len(parts) >= 5 else parts[2]
        meta["author"] = parts[-2] if len(parts) >= 5 else parts[-1]
        try:
            meta["year"] = int(parts[-1])
        except ValueError:
            try:
                meta["year"] = int(parts[-2])
            except (ValueError, IndexError):
                pass
    return meta


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


def collect_pages(grade_nums: list[int]) -> list[dict]:
    """Collect all PDF pages for given grades."""
    pages = []
    for grade_num in grade_nums:
        grade_dir = TEXTBOOKS_DIR / f"grade-{grade_num:02d}"
        if not grade_dir.exists():
            print(f"WARNING: {grade_dir} does not exist, skipping")
            continue
        for pdf_path in sorted(grade_dir.glob("*.pdf")):
            meta = parse_pdf_stem(pdf_path)
            doc = pymupdf.open(str(pdf_path))
            n_pages = len(doc)
            doc.close()
            for page_num in range(n_pages):
                page_id = f"{meta['pdf_stem']}_p{page_num + 1:03d}"
                pages.append({
                    "page_id": page_id,
                    "pdf_path": pdf_path,
                    "page_num": page_num,  # 0-indexed
                    "page": page_num + 1,  # 1-indexed
                    **meta,
                })
    return pages


def render_page(pdf_path: Path, page_num: int, output_path: Path) -> bool:
    """Render a single PDF page as PNG."""
    try:
        doc = pymupdf.open(str(pdf_path))
        page = doc[page_num]
        pix = page.get_pixmap(dpi=RENDER_DPI)
        pix.save(str(output_path))
        doc.close()
        return True
    except Exception as e:
        print(f"\n  Render error: {e}")
        return False


def extract_json_from_response(response_text: str) -> dict | None:
    """Extract JSON object from gemini-cli response text."""
    text = response_text.strip()

    # Strip markdown code fences
    if "```json" in text:
        text = text.split("```json", 1)[1]
        text = text.split("```", 1)[0].strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1].strip()
            if text.startswith("json\n"):
                text = text[5:]

    # Find outermost JSON object
    brace_start = text.find("{")
    if brace_start < 0:
        return None

    depth = 0
    for i in range(brace_start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[brace_start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def analyze_page_via_cli(record: dict, tmp_dir: Path) -> dict | None:
    """Render a page and analyze it via gemini-cli."""
    page_id = record["page_id"]
    pdf_path = record["pdf_path"]
    page_num = record["page_num"]

    # Render page to temp PNG
    tmp_img = tmp_dir / f"{page_id}.png"
    if not render_page(pdf_path, page_num, tmp_img):
        return None

    prompt = VISION_PROMPT.format(image_path=tmp_img)

    for attempt in range(MAX_RETRIES):
        try:
            result = subprocess.run(
                [
                    "gemini",
                    "--include-directories", str(tmp_dir),
                    "-p", prompt,
                    "-o", "text",
                    "--yolo",
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(BASE_DIR),
            )

            # gemini-cli writes status messages to stderr, response to stdout
            response_text = result.stdout.strip()
            stderr = result.stderr.strip()

            if result.returncode != 0:
                if "429" in stderr or "RESOURCE_EXHAUSTED" in stderr:
                    wait = RETRY_DELAY * (2**attempt)
                    print(f"\n  Rate limited, waiting {wait:.0f}s (attempt {attempt + 1})")
                    time.sleep(wait)
                    continue
                if "Thinking_config" in stderr:
                    print(f"\n  Model config error on {page_id}: {stderr[:100]}")
                    return None
                print(f"\n  ERROR on {page_id}: {stderr[:200]}")
                return None

            # Check for read_file errors (gitignore block → hallucination)
            if "Error executing tool read_file" in response_text or "is ignored by configured" in (response_text + stderr):
                print(f"\n  File read blocked for {page_id}, retrying...")
                time.sleep(RETRY_DELAY)
                continue

            data = extract_json_from_response(response_text)
            if data is None:
                print(f"\n  No JSON in response for {page_id}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return None

            return {
                "page_id": page_id,
                "page": record["page"],
                "grade": record.get("grade", 0),
                "subject": record.get("subject", ""),
                "author": record.get("author", ""),
                "pdf_stem": record.get("pdf_stem", ""),
                "page_type": data.get("page_type", "unknown"),
                "elements": data.get("elements", []),
                "model": "gemini-cli-default",
                "ts": datetime.now(timezone.utc).isoformat(),
            }

        except subprocess.TimeoutExpired:
            print(f"\n  TIMEOUT on {page_id} (attempt {attempt + 1})")
            time.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"\n  ERROR on {page_id}: {e}")
            return None
        finally:
            if tmp_img.exists():
                tmp_img.unlink()

    return None


def run_analysis(pages: list[dict], processed_ids: set[str]):
    """Run vision analysis on all unprocessed pages via gemini-cli."""
    if not shutil.which("gemini"):
        print("ERROR: gemini-cli not found.")
        sys.exit(1)

    to_process = [p for p in pages if p["page_id"] not in processed_ids]
    if not to_process:
        print("All pages already processed!")
        return

    print(f"Pages to analyze: {len(to_process)} (skipping {len(pages) - len(to_process)} already done)")
    print(f"Model: gemini-cli default (Ultra auth)")
    print()

    ANALYSIS_FILE.parent.mkdir(parents=True, exist_ok=True)

    done = 0
    errors = 0
    start = time.time()

    with tempfile.TemporaryDirectory(prefix="textbook_analysis_") as tmp_dir:
        tmp_path = Path(tmp_dir)

        for i, record in enumerate(to_process):
            result = analyze_page_via_cli(record, tmp_path)

            if result is not None:
                with open(ANALYSIS_FILE, "a") as f:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
                done += 1
                n_elements = len(result["elements"])
                elapsed = time.time() - start
                rate = done / elapsed if elapsed > 0 else 0
                remaining = len(to_process) - i - 1
                eta = remaining / rate if rate > 0 else 0
                print(
                    f"\r[{i + 1}/{len(to_process)}] "
                    f"p{record['page']:03d} {record['pdf_stem'][:40]} "
                    f"→ {n_elements} el ({result['page_type']}) "
                    f"[{rate:.2f}/s, ETA {eta / 60:.0f}m]   ",
                    end="",
                    flush=True,
                )
            else:
                errors += 1
                print(
                    f"\r[{i + 1}/{len(to_process)}] "
                    f"p{record['page']:03d} {record['pdf_stem'][:40]} → ERROR   ",
                    end="",
                    flush=True,
                )

    elapsed = time.time() - start
    print(f"\n\nDone! {done} pages analyzed in {elapsed:.0f}s ({elapsed / 60:.1f}m)")
    print(f"  Errors: {errors}")
    print(f"  Rate: {done / elapsed:.2f} pages/s" if elapsed > 0 else "")
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

    by_grade = {}
    for r in records:
        g = r.get("grade", 0)
        by_grade.setdefault(g, []).append(r)

    print("By grade:")
    for grade in sorted(by_grade):
        grade_records = by_grade[grade]
        total_elements = sum(len(r.get("elements", [])) for r in grade_records)
        print(f"  Grade {grade:2d}: {len(grade_records):5d} pages, {total_elements:6d} elements")

    print()
    by_type = {}
    for r in records:
        pt = r.get("page_type", "unknown")
        by_type[pt] = by_type.get(pt, 0) + 1
    print("By page type:")
    for pt, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {pt:15s}: {count:5d}")

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

    print()
    by_etype = {}
    for r in records:
        for el in r.get("elements", []):
            et = el.get("type", "unknown")
            by_etype[et] = by_etype.get(et, 0) + 1
    print("By element type:")
    for et, count in sorted(by_etype.items(), key=lambda x: -x[1]):
        print(f"  {et:15s}: {count:5d}")

    print()
    with_text = sum(
        1
        for r in records
        for el in r.get("elements", [])
        if el.get("associated_text_uk")
    )
    if total_elements:
        print(
            f"Elements with Ukrainian text: {with_text}/{total_elements} "
            f"({with_text / total_elements * 100:.1f}%)"
        )


def link_to_sub_images():
    """Match page-level elements to extracted sub-images."""
    if not ANALYSIS_FILE.exists():
        print("No analysis file found. Run analysis first.")
        return

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

    pairs = []
    matched = 0
    unmatched = 0

    for sub in sub_images:
        # New page_id format: {pdf_stem}_p{page:03d} (no _i00 suffix)
        parent_id = f"{sub['pdf_stem']}_p{sub['page']:03d}"

        if parent_id not in analyses:
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
            continue

        analysis = analyses[parent_id]
        elements = analysis.get("elements", [])
        img_idx = sub["image_index"] - 1

        teaching_elements = [
            e
            for e in elements
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

    with open(PAIRS_FILE, "w") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    print(f"\nLinked {matched} sub-images to page elements")
    print(f"Unmatched/unlinked: {unmatched}")
    print(f"Output: {PAIRS_FILE}")

    with_text = sum(1 for p in pairs if p.get("associated_text_uk"))
    print(f"Pairs with Ukrainian text: {with_text}")


def cleanup_junk(execute: bool = False):
    """Identify and optionally delete junk sub-images based on page analysis."""
    if not ANALYSIS_FILE.exists():
        print("No analysis file found. Run analysis first.")
        return

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

    junk_files = []
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
                    continue

                img_path = BASE_DIR / record["image_path"]
                if not img_path.exists():
                    continue

                key = (record.get("pdf_stem", ""), record.get("page", 0))
                analysis = page_elements.get(key)

                if analysis is None:
                    if img_path.stat().st_size < 5000:
                        junk_files.append((img_path, "unanalyzed_tiny"))
                    else:
                        kept += 1
                    continue

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

    deleted = 0
    deleted_by_grade = {}

    for path, _reason in junk_files:
        grade_dir = path.parent
        grade = grade_dir.name
        deleted_by_grade.setdefault(grade, set()).add(path.name)
        path.unlink()
        deleted += 1

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
        type=int,
        help="Grade numbers to process (e.g., 1 2)",
    )
    parser.add_argument("--all", action="store_true", help="Process all grades")
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics from existing analysis",
    )
    parser.add_argument(
        "--link",
        action="store_true",
        help="Link page analysis to extracted sub-images",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Identify junk sub-images for deletion",
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

    if args.all:
        grade_nums = list(range(1, 12))
    elif args.grade:
        grade_nums = args.grade
    else:
        parser.print_help()
        print("\nSpecify --grade, --all, --stats, --link, or --cleanup")
        sys.exit(1)

    print(f"Grades: {', '.join(str(g) for g in grade_nums)}")

    pages = collect_pages(grade_nums)
    processed = load_processed_ids()
    print(f"Total pages in PDFs: {len(pages)}")
    print(f"Already processed: {len(processed)}")

    run_analysis(pages, processed)


if __name__ == "__main__":
    main()
