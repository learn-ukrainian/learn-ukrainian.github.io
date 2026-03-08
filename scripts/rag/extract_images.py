"""Extract images from PDF textbooks using pymupdf.

Filters out tiny icons (< 100x100px) and saves images with metadata.

Usage:
    .venv/bin/python scripts/rag/extract_images.py data/textbooks/grade-01/1-klas-bukvar-bolshakova-2025-1.pdf
    .venv/bin/python scripts/rag/extract_images.py --all
    .venv/bin/python scripts/rag/extract_images.py --grade 1 3
"""

import argparse
import json
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import (
    IMAGES_DIR,
    MIN_IMAGE_HEIGHT,
    MIN_IMAGE_WIDTH,
    TEXTBOOKS_DIR,
    parse_pdf_metadata,
)


def extract_images_from_pdf(pdf_path: Path, output_dir: Path | None = None) -> dict:
    """Extract images from a single PDF.

    Returns summary dict with counts.
    """
    pdf_path = Path(pdf_path)
    meta = parse_pdf_metadata(pdf_path)

    if output_dir is None:
        output_dir = IMAGES_DIR / f"grade-{meta['grade']:02d}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[images] Processing {pdf_path.name}...")

    doc = pymupdf.open(str(pdf_path))
    extracted = 0
    skipped_small = 0
    skipped_error = 0
    image_records = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)

        for img_idx, img_info in enumerate(images):
            xref = img_info[0]
            try:
                pix = pymupdf.Pixmap(doc, xref)

                # Convert non-RGB colorspaces (CMYK, DeviceN, etc.) to RGB
                if (pix.colorspace and pix.colorspace.n >= 4) or pix.colorspace is None or pix.colorspace.name not in ("DeviceRGB", "DeviceGray"):
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)

                # Remove alpha channel if present (PNG doesn't need it for our use)
                if pix.alpha:
                    pix = pymupdf.Pixmap(pix, 0)

                # Size filter
                if pix.width < MIN_IMAGE_WIDTH or pix.height < MIN_IMAGE_HEIGHT:
                    skipped_small += 1
                    continue

                # Save as PNG
                filename = f"{meta['pdf_stem']}-p{page_num + 1:03d}-{img_idx:02d}.png"
                filepath = output_dir / filename
                pix.save(str(filepath))

                record = {
                    "image_id": f"{meta['pdf_stem']}_p{page_num + 1:03d}_i{img_idx:02d}",
                    "image_path": str(filepath.relative_to(IMAGES_DIR.parent.parent)),
                    "filename": filename,
                    "page": page_num + 1,
                    "image_index": img_idx,
                    "width": pix.width,
                    "height": pix.height,
                    **{k: v for k, v in meta.items() if k != "pdf_stem"},
                    "pdf_stem": meta["pdf_stem"],
                }
                image_records.append(record)
                extracted += 1

            except Exception as e:
                skipped_error += 1
                print(f"  Warning: page {page_num + 1}, image {img_idx}: {e}")

    doc.close()

    # Save image metadata as JSONL
    meta_file = output_dir / f"{meta['pdf_stem']}-images.jsonl"
    with open(meta_file, "w", encoding="utf-8") as f:
        for record in image_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "pdf": pdf_path.name,
        "extracted": extracted,
        "skipped_small": skipped_small,
        "skipped_error": skipped_error,
        "output_dir": str(output_dir),
        "meta_file": str(meta_file),
    }
    print(f"  Result: {extracted} images extracted "
          f"({skipped_small} too small, {skipped_error} errors)")

    return summary


def find_pdfs(grades: list[int] | None = None) -> list[Path]:
    """Find all PDF files, optionally filtered by grade."""
    pdfs = []
    for grade_dir in sorted(TEXTBOOKS_DIR.iterdir()):
        if not grade_dir.is_dir() or not grade_dir.name.startswith("grade-"):
            continue
        grade_num = int(grade_dir.name.split("-")[1])
        if grades and grade_num not in grades:
            continue
        for pdf in sorted(grade_dir.glob("*.pdf")):
            pdfs.append(pdf)
    return pdfs


def main():
    parser = argparse.ArgumentParser(description="Extract images from PDF textbooks")
    parser.add_argument("pdf", nargs="?", help="Path to a single PDF file")
    parser.add_argument("--all", action="store_true", help="Process all PDFs")
    parser.add_argument("--grade", type=int, nargs="+", help="Process specific grades")
    args = parser.parse_args()

    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"Error: {pdf_path} not found", file=sys.stderr)
            sys.exit(1)
        summary = extract_images_from_pdf(pdf_path)
        print(f"\nDone: {json.dumps(summary, indent=2)}")

    elif args.all or args.grade:
        pdfs = find_pdfs(args.grade)
        if not pdfs:
            print("No PDFs found", file=sys.stderr)
            sys.exit(1)
        print(f"Found {len(pdfs)} PDFs to process\n")
        total_extracted = 0
        for pdf in pdfs:
            summary = extract_images_from_pdf(pdf)
            total_extracted += summary["extracted"]
            print()
        print(f"=== Total: {total_extracted} images from {len(pdfs)} PDFs ===")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
