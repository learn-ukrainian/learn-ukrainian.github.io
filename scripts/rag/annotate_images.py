"""Annotate extracted textbook images with nearby Ukrainian text using PyMuPDF spatial matching.

For each image in the per-book -images.jsonl, recovers its bounding box on the PDF page
via xref, then finds the nearest text blocks. Writes annotations to
data/textbook_images/image_text_pairs.jsonl (consumed by ingest.py).

No ML models, no API calls — pure coordinate geometry.

Usage:
    .venv/bin/python scripts/rag/annotate_images.py --all
    .venv/bin/python scripts/rag/annotate_images.py --grade 1 3
    .venv/bin/python scripts/rag/annotate_images.py --book 1-klas-bukvar-zaharijchuk-2025-1
    .venv/bin/python scripts/rag/annotate_images.py --stats
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import IMAGES_DIR, TEXTBOOKS_DIR

# ── Constants ─────────────────────────────────────────────────────
PROGRESS_DIR = IMAGES_DIR / ".annotate_progress"
OUTPUT_FILE = IMAGES_DIR / "image_text_pairs.jsonl"

# Spatial thresholds (in PDF points, 1pt = 1/72 inch)
MAX_TEXT_DISTANCE = 200  # Ignore text blocks further than this

# CP1251 mojibake: Latin chars in 0xC0-0xFF that appear when CP1251 bytes are decoded
# as Latin-1. Also covers single-char stress marks used in Ukrainian textbooks
# (PyMuPDF renders наголос as Latin diacritics: î=stressed о, å=stressed е, etc.)
_MOJIBAKE_CHARS = set("àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"
                      "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞß")

# Stress marks: Latin diacritics that represent Ukrainian stressed vowels in textbooks.
# These are isolated chars surrounded by Cyrillic, not encoding errors.
# î→о, å→е, è→и, à→а, ó→у, é→є, ê→к (rare)
_STRESS_MAP = {
    "\u00ee": "о",  # î → о (stressed о)
    "\u00e5": "е",  # å → е (stressed е)
    "\u00e8": "и",  # è → и (stressed и)
    "\u00e0": "а",  # à → а (stressed а)
    "\u00f3": "у",  # ó → у (stressed у)
    "\u00e9": "є",  # é → є (stressed є)
}


def _is_page_number(text: str) -> bool:
    """Check if text is just a page number (1-4 digit string)."""
    stripped = text.strip()
    return stripped.isdigit() and len(stripped) <= 4


def _has_mojibake(text: str) -> bool:
    """Detect CP1251→Latin-1 mojibake or stress marks in text."""
    return bool(_MOJIBAKE_CHARS & set(text))


def _repair_mojibake(text: str) -> str:
    """Repair CP1251→Latin-1 mojibake. Handles three cases:

    1. Full mojibake (entire string is Latin-1 encoded CP1251) → re-encode
    2. Stress marks (isolated Latin diacritics in Cyrillic text) → replace with base vowel
    3. Mixed/unrepairable → character-by-character best-effort
    """
    # Case 1: try full re-encode (works when entire string is mojibaked)
    try:
        repaired = text.encode("latin-1").decode("cp1251")
        # Verify the result looks like Ukrainian (has Cyrillic chars)
        if any("\u0400" <= c <= "\u04ff" for c in repaired):
            return repaired
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

    # Case 2: replace isolated stress marks (most common in textbooks)
    result = text
    for latin_char, ukr_char in _STRESS_MAP.items():
        result = result.replace(latin_char, ukr_char)

    # Case 3: strip any remaining mojibake chars that weren't stress marks
    result = "".join(c for c in result if c not in _MOJIBAKE_CHARS)

    return result if result.strip() else text


# ── Text extraction ───────────────────────────────────────────────
def extract_text_blocks(page) -> list[dict]:
    """Extract text blocks with bounding boxes from a PDF page.

    Returns list of {"bbox": [x0, y0, x1, y1], "text": str}.
    Skips empty/tiny text fragments.
    """
    blocks = []
    data = page.get_text("dict")
    for block in data["blocks"]:
        if block["type"] != 0:  # text blocks only
            continue
        text = " ".join(
            span["text"]
            for line in block["lines"]
            for span in line["spans"]
        ).strip()
        if not text or len(text) < 2:
            continue
        blocks.append({
            "bbox": list(block["bbox"]),
            "text": text,
        })
    return blocks


# ── Spatial geometry ──────────────────────────────────────────────
def bbox_distance(b1: list, b2: list) -> float:
    """Minimum distance between two bounding boxes (0 if overlapping)."""
    dx = max(0, b1[0] - b2[2], b2[0] - b1[2])
    dy = max(0, b1[1] - b2[3], b2[1] - b1[3])
    return (dx**2 + dy**2) ** 0.5


def bbox_position(bbox: list, page_width: float, page_height: float) -> str:
    """Classify image position on page as 3x3 grid label."""
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2

    if cx < page_width / 3:
        col = "left"
    elif cx < 2 * page_width / 3:
        col = "center"
    else:
        col = "right"

    if cy < page_height / 3:
        row = "top"
    elif cy < 2 * page_height / 3:
        row = "center"
    else:
        row = "bottom"

    if row == "center" and col == "center":
        return "center"
    return f"{row}-{col}"


# ── Classification heuristics ─────────────────────────────────────
def classify_element_type(
    bbox: list,
    page_width: float,
    page_height: float,
    nearest_text: str | None,
    nearest_dist: float,
) -> str:
    """Classify image as illustration/letter/QR/decoration/logo."""
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    aspect = w / h if h > 0 else 1.0

    # Very wide/thin → decoration (rules, dividers)
    if aspect > 8 or aspect < 0.125:
        return "decoration"

    # Covers >90% of page → full-page decoration / background
    page_area = page_width * page_height
    img_area = w * h
    if page_area > 0 and img_area / page_area > 0.9:
        return "decoration"

    # Small, in corner → logo
    if w < 60 and h < 60:
        near_left = bbox[0] < page_width * 0.1
        near_right = bbox[2] > page_width * 0.9
        near_top = bbox[1] < page_height * 0.1
        near_bottom = bbox[3] > page_height * 0.9
        if (near_left or near_right) and (near_top or near_bottom):
            return "logo"

    # Small image near short text (≤5 chars) → letter illustration (bukvar pages)
    # Must check BEFORE QR to avoid false positives on square letter pics
    if w < 150 and h < 150 and nearest_text and len(nearest_text.strip()) <= 5 and nearest_dist < 80:
        return "letter"

    # Nearly-perfect square, very small, no nearby text → QR code
    # Extremely conservative: only catches actual QR codes, not small illustrations
    if 0.95 <= aspect <= 1.05 and 30 <= w <= 70 and 30 <= h <= 70 and (not nearest_text or nearest_dist > 150):
        return "QR"

    return "illustration"


def classify_teaching_value(
    bbox: list,
    nearest_text: str | None,
    nearest_dist: float,
    page_height: float,
) -> str:
    """Classify teaching value: high/medium/low/none."""
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    # Tiny images → none
    if w < 30 or h < 30:
        return "none"

    # No text nearby → none
    if nearest_text is None or nearest_dist > MAX_TEXT_DISTANCE:
        return "none"

    # Unrepairable mojibake → none
    if _has_mojibake(nearest_text):
        return "none"

    # Short label very close → high (vocabulary illustration)
    if len(nearest_text) <= 30 and nearest_dist < 80:
        return "high"

    # Medium-length text close → medium
    if len(nearest_text) <= 100 and nearest_dist < 50:
        return "medium"

    # Paragraph nearby → medium
    if nearest_dist < 50:
        return "medium"

    return "low"


# ── Core annotation logic ─────────────────────────────────────────
def build_xref_to_bboxes(page) -> dict[int, list[list]]:
    """Build mapping from xref → list of bounding boxes on the page.

    Uses get_image_info(xrefs=True) which returns placement bboxes.
    Skips entries with xref=0 (inline images without explicit xref).
    """
    xref_bboxes: dict[int, list[list]] = {}
    for info in page.get_image_info(xrefs=True):
        xref = info.get("xref", 0)
        if xref == 0:
            continue
        bbox = list(info["bbox"])
        if xref not in xref_bboxes:
            xref_bboxes[xref] = []
        xref_bboxes[xref].append(bbox)
    return xref_bboxes


def annotate_page(
    page,
    page_images: list[tuple],  # (xref, ...) from get_images(full=True)
    image_records: list[dict],  # Records from JSONL for this page
) -> list[dict]:
    """Annotate all images on a single page.

    Returns list of annotation dicts ready for image_text_pairs.jsonl.
    """
    text_blocks = extract_text_blocks(page)
    # Pre-repair mojibake once per page (avoids redundant encode/decode in inner loop)
    for tb in text_blocks:
        if _has_mojibake(tb["text"]):
            tb["text"] = _repair_mojibake(tb["text"])
    xref_bboxes = build_xref_to_bboxes(page)
    page_rect = page.rect
    page_width = page_rect.width
    page_height = page_rect.height

    annotations = []

    for rec in image_records:
        img_idx = rec["image_index"]

        # Recover xref from get_images position
        if img_idx >= len(page_images):
            # image_index out of range — skip
            continue
        xref = page_images[img_idx][0]

        # Get bounding box(es) for this xref
        bboxes = xref_bboxes.get(xref, [])
        if not bboxes:
            # No bbox found — write minimal annotation
            annotations.append({
                "image_id": rec["image_id"],
                "description_uk": "",
                "associated_text_uk": "",
                "teaching_value": "low",
                "element_type": "illustration",
                "position": "center",
            })
            continue

        # Collect text near ALL placements of this image
        all_nearby_texts = []
        best_nearest_text = None
        best_nearest_dist = 999.0

        for bbox in bboxes:
            for tb in text_blocks:
                dist = bbox_distance(bbox, tb["bbox"])
                txt = tb["text"]
                if dist <= MAX_TEXT_DISTANCE:
                    all_nearby_texts.append((dist, txt))
                # Skip page numbers when choosing best nearest text
                if dist < best_nearest_dist and not _is_page_number(txt):
                    best_nearest_dist = dist
                    best_nearest_text = txt
        # If ALL nearby texts were page numbers, fall back to the closest one
        if best_nearest_text is None and all_nearby_texts:
            all_nearby_texts.sort(key=lambda x: x[0])
            best_nearest_text = all_nearby_texts[0][1]
            best_nearest_dist = all_nearby_texts[0][0]

        # Deduplicate and sort by distance
        all_nearby_texts.sort(key=lambda x: x[0])
        seen = set()
        unique_texts = []
        for _dist, text in all_nearby_texts:
            if text not in seen:
                seen.add(text)
                unique_texts.append(text)

        # Use the primary (largest) bbox for position/classification
        primary_bbox = max(bboxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))

        # Build description_uk: nearest short text (word/phrase)
        # Prefer text that looks like a proper label: starts with uppercase,
        # not a sentence fragment (doesn't start with lowercase or punctuation)
        description = ""
        for text in unique_texts:
            clean = text.strip()
            if len(clean) <= 50 and not clean.isdigit() and clean and clean[0].isupper():
                    description = clean
                    break
        # Fallback: first short text regardless of case
        if not description:
            for text in unique_texts:
                clean = text.strip()
                if len(clean) <= 50 and not clean.isdigit():
                    description = clean
                    break
        if not description and unique_texts:
            # Skip page numbers in final fallback too
            for text in unique_texts:
                if not _is_page_number(text):
                    description = text[:50]
                    break
            # Absolute last resort: use whatever we have
            if not description:
                description = unique_texts[0][:50]

        # Build associated_text_uk: concatenated nearby text, ~200 chars
        associated = " ".join(unique_texts)
        if len(associated) > 200:
            associated = associated[:197] + "..."

        # Classify
        element_type = classify_element_type(
            primary_bbox, page_width, page_height,
            best_nearest_text, best_nearest_dist,
        )
        teaching_value = classify_teaching_value(
            primary_bbox, best_nearest_text, best_nearest_dist, page_height,
        )
        position = bbox_position(primary_bbox, page_width, page_height)

        annotations.append({
            "image_id": rec["image_id"],
            "description_uk": description,
            "associated_text_uk": associated,
            "teaching_value": teaching_value,
            "element_type": element_type,
            "position": position,
        })

    return annotations


# ── Book-level processing ─────────────────────────────────────────
def find_pdf_for_stem(stem: str) -> Path | None:
    """Find the PDF file for a given stem."""
    for grade_dir in sorted(TEXTBOOKS_DIR.iterdir()):
        if not grade_dir.is_dir():
            continue
        pdf = grade_dir / f"{stem}.pdf"
        if pdf.exists():
            return pdf
    return None


def annotate_book(pdf_stem: str, jsonl_path: Path) -> list[dict]:
    """Annotate all images from a single book.

    Returns list of annotation dicts.
    """
    # Load image records
    records = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    if not records:
        return []

    # Find the PDF
    pdf_path = find_pdf_for_stem(pdf_stem)
    if not pdf_path:
        print(f"  Warning: PDF not found for {pdf_stem}, skipping")
        return []

    # Group records by page
    by_page: dict[int, list[dict]] = {}
    for rec in records:
        pg = rec["page"]
        if pg not in by_page:
            by_page[pg] = []
        by_page[pg].append(rec)

    doc = pymupdf.open(str(pdf_path))
    all_annotations = []

    for page_num in sorted(by_page.keys()):
        if page_num < 1 or page_num > len(doc):
            continue
        page = doc[page_num - 1]  # 0-indexed
        page_images = page.get_images(full=True)
        page_annotations = annotate_page(page, page_images, by_page[page_num])
        all_annotations.extend(page_annotations)

    doc.close()
    return all_annotations


# ── CLI / batch ───────────────────────────────────────────────────
def find_all_jsonls(grades: list[int] | None = None) -> list[tuple[str, Path]]:
    """Find all image JSONL files, optionally filtered by grade.

    Returns list of (pdf_stem, jsonl_path).
    """
    results = []
    for grade_dir in sorted(IMAGES_DIR.iterdir()):
        if not grade_dir.is_dir() or not grade_dir.name.startswith("grade-"):
            continue
        grade_num = int(grade_dir.name.split("-")[1])
        if grades and grade_num not in grades:
            continue
        for jsonl in sorted(grade_dir.glob("*-images.jsonl")):
            stem = jsonl.name.replace("-images.jsonl", "")
            results.append((stem, jsonl))
    return results


def print_stats():
    """Print annotation statistics."""
    if not OUTPUT_FILE.exists():
        print("No annotations found. Run --all first.")
        return

    records = []
    with open(OUTPUT_FILE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print(f"Total annotations: {len(records)}")
    print()

    # Teaching value distribution
    tv_counts: dict[str, int] = {}
    for rec in records:
        tv = rec.get("teaching_value", "unknown")
        tv_counts[tv] = tv_counts.get(tv, 0) + 1
    print("Teaching value distribution:")
    for tv in ["high", "medium", "low", "none", "unknown"]:
        if tv in tv_counts:
            pct = tv_counts[tv] / len(records) * 100
            print(f"  {tv:8s}: {tv_counts[tv]:5d} ({pct:.1f}%)")

    # Element type distribution
    et_counts: dict[str, int] = {}
    for rec in records:
        et = rec.get("element_type", "unknown")
        et_counts[et] = et_counts.get(et, 0) + 1
    print("\nElement type distribution:")
    for et in sorted(et_counts.keys()):
        pct = et_counts[et] / len(records) * 100
        print(f"  {et:15s}: {et_counts[et]:5d} ({pct:.1f}%)")

    # Has description
    has_desc = sum(1 for r in records if r.get("description_uk"))
    has_assoc = sum(1 for r in records if r.get("associated_text_uk"))
    print(f"\nWith description_uk:      {has_desc:5d} ({has_desc/len(records)*100:.1f}%)")
    print(f"With associated_text_uk:  {has_assoc:5d} ({has_assoc/len(records)*100:.1f}%)")

    # Quality issues
    page_num_desc = sum(
        1 for r in records
        if _is_page_number(r.get("description_uk", ""))
    )
    mojibake_desc = sum(
        1 for r in records
        if _has_mojibake(r.get("description_uk", ""))
    )
    print("\nQuality issues:")
    print(f"  Page number as description: {page_num_desc:5d} ({page_num_desc/len(records)*100:.1f}%)")
    print(f"  Mojibake in description:    {mojibake_desc:5d} ({mojibake_desc/len(records)*100:.1f}%)")

    # Per-grade breakdown
    grade_counts: dict[str, int] = {}
    for rec in records:
        # Extract grade from image_id (e.g., "1-klas-...")
        iid = rec.get("image_id", "")
        parts = iid.split("-")
        grade = parts[0] if parts[0].isdigit() else "?"
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
    print("\nPer-grade counts:")
    for g in sorted(grade_counts.keys(), key=lambda x: int(x) if x.isdigit() else 99):
        print(f"  Grade {g:>2s}: {grade_counts[g]:5d}")

    # Progress status
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    done_files = list(PROGRESS_DIR.glob("*.done"))
    all_jsonls = find_all_jsonls()
    print(f"\nProgress: {len(done_files)} / {len(all_jsonls)} books annotated")


def main():
    parser = argparse.ArgumentParser(
        description="Annotate textbook images with nearby Ukrainian text"
    )
    parser.add_argument("--all", action="store_true", help="Annotate all books")
    parser.add_argument("--grade", type=int, nargs="+", help="Annotate specific grades")
    parser.add_argument("--book", type=str, help="Annotate a single book (PDF stem)")
    parser.add_argument("--stats", action="store_true", help="Show annotation statistics")
    parser.add_argument(
        "--force", action="store_true",
        help="Ignore progress markers, re-annotate everything",
    )
    args = parser.parse_args()

    if args.stats:
        print_stats()
        return

    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

    if args.book:
        # Single book
        jsonls = find_all_jsonls()
        match = [(s, p) for s, p in jsonls if s == args.book]
        if not match:
            print(f"Error: No JSONL found for book '{args.book}'", file=sys.stderr)
            sys.exit(1)
        stem, jsonl_path = match[0]
        print(f"[annotate] {stem}...")
        annotations = annotate_book(stem, jsonl_path)
        # For single book: write to output (overwrite)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for ann in annotations:
                f.write(json.dumps(ann, ensure_ascii=False) + "\n")
        print(f"  {len(annotations)} annotations → {OUTPUT_FILE}")
        # Mark done
        (PROGRESS_DIR / f"{stem}.done").touch()
        return

    if args.all or args.grade:
        jsonls = find_all_jsonls(args.grade)
        if not jsonls:
            print("No image JSONL files found", file=sys.stderr)
            sys.exit(1)

        print(f"[annotate] Found {len(jsonls)} books to annotate\n")

        all_annotations = []
        skipped = 0

        for stem, jsonl_path in jsonls:
            # Check progress marker
            if not args.force and (PROGRESS_DIR / f"{stem}.done").exists():
                skipped += 1
                continue

            print(f"  {stem}...", end=" ", flush=True)

            # Skip empty JSONL files (scanned books with no extractable images)
            if jsonl_path.stat().st_size == 0:
                print("(empty, skipping)")
                (PROGRESS_DIR / f"{stem}.done").touch()
                continue

            annotations = annotate_book(stem, jsonl_path)
            all_annotations.extend(annotations)
            print(f"{len(annotations)} annotations")

            # Mark done
            (PROGRESS_DIR / f"{stem}.done").touch()

        # If some books were skipped, load their previous annotations
        if skipped > 0 and OUTPUT_FILE.exists():
            print(f"\n  ({skipped} books already done, loading previous annotations)")
            # Reload all annotations from the existing file for previously completed books
            prev_ids = {a["image_id"] for a in all_annotations}
            with open(OUTPUT_FILE, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        rec = json.loads(line)
                        if rec["image_id"] not in prev_ids:
                            all_annotations.append(rec)

        # Write atomically (temp file → rename)
        tmp = tempfile.NamedTemporaryFile(  # noqa: SIM115 — atomic write pattern: close then rename
            mode="w",
            dir=str(IMAGES_DIR),
            suffix=".jsonl.tmp",
            delete=False,
            encoding="utf-8",
        )
        try:
            for ann in all_annotations:
                tmp.write(json.dumps(ann, ensure_ascii=False) + "\n")
            tmp.close()
            Path(tmp.name).replace(OUTPUT_FILE)
        except Exception:
            Path(tmp.name).unlink(missing_ok=True)
            raise

        print(f"\n=== Total: {len(all_annotations)} annotations → {OUTPUT_FILE} ===")
        if skipped:
            print(f"    ({skipped} books reused from previous run)")
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
