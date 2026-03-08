"""POC: Extract image+text pairs from a textbook page using spatial matching.

Renders an HTML review page so a human can verify the pairing quality.

Usage:
    .venv/bin/python scripts/rag/poc_pair_page.py data/textbooks/grade-01/1-klas-bukvar-zaharijchuk-2025-2.pdf 43
    .venv/bin/python scripts/rag/poc_pair_page.py data/textbooks/grade-01/1-klas-bukvar-zaharijchuk-2025-2.pdf 40-50
    .venv/bin/python scripts/rag/poc_pair_page.py data/textbooks/grade-01/1-klas-bukvar-zaharijchuk-2025-2.pdf 43 --open
"""

import argparse
import base64
import sys
import tempfile
from pathlib import Path

import pymupdf

# Minimum image dimensions to consider (filters decorative dots, bullets)
MIN_IMG_WIDTH = 40
MIN_IMG_HEIGHT = 40

# DPI for rendering the annotated page
RENDER_DPI = 150
SCALE = RENDER_DPI / 72  # pymupdf coordinates are in 72dpi points


def extract_text_blocks(page):
    """Extract text blocks with bounding boxes from a page."""
    blocks = []
    data = page.get_text("dict")
    for block in data["blocks"]:
        if block["type"] != 0:  # text block only
            continue
        text = " ".join(
            span["text"]
            for line in block["lines"]
            for span in line["spans"]
        ).strip()
        if not text or len(text) < 2:
            continue
        # Skip page numbers (single short number at bottom)
        bbox = block["bbox"]
        blocks.append({
            "bbox": list(bbox),
            "text": text,
        })
    return blocks


def extract_images(page):
    """Extract images with valid bounding boxes from a page."""
    images = []
    for i, img_info in enumerate(page.get_image_info(xrefs=True)):
        bbox = img_info["bbox"]
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w < MIN_IMG_WIDTH or h < MIN_IMG_HEIGHT:
            continue
        # Extract the actual image bytes if possible
        xref = img_info.get("xref", 0)
        img_bytes = None
        if xref > 0:
            try:
                pix = pymupdf.Pixmap(page.parent, xref)
                if pix.n > 4:  # CMYK or similar
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                if pix.alpha:
                    pix = pymupdf.Pixmap(pix, 0)  # remove alpha
                img_bytes = pix.tobytes("png")
            except Exception:
                pass

        images.append({
            "index": i,
            "bbox": list(bbox),
            "width": img_info["width"],
            "height": img_info["height"],
            "xref": xref,
            "img_bytes": img_bytes,
        })
    return images


def bbox_center(bbox):
    """Return center (x, y) of a bounding box."""
    return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)


def bbox_distance(b1, b2):
    """Minimum distance between two bounding boxes (0 if overlapping)."""
    # Horizontal gap
    dx = max(0, b1[0] - b2[2], b2[0] - b1[2])
    # Vertical gap
    dy = max(0, b1[1] - b2[3], b2[1] - b1[3])
    return (dx**2 + dy**2) ** 0.5


def match_images_to_text(images, text_blocks):
    """For each image, find the closest text block(s)."""
    pairs = []
    for img in images:
        if not text_blocks:
            pairs.append({"image": img, "text_blocks": [], "distance": 999})
            continue

        # Find all text blocks sorted by distance
        scored = []
        for tb in text_blocks:
            dist = bbox_distance(img["bbox"], tb["bbox"])
            scored.append((dist, tb))
        scored.sort(key=lambda x: x[0])

        # Take the closest text block, plus any within 20pt
        closest_dist = scored[0][0]
        nearby = [tb for dist, tb in scored if dist <= max(closest_dist + 20, 50)]

        pairs.append({
            "image": img,
            "text_blocks": nearby,
            "distance": closest_dist,
        })
    return pairs


def render_annotated_page(page, images, text_blocks, pairs):
    """Render the page with colored bounding boxes for images and text."""
    # Create a copy of the page as a pixmap
    pix = page.get_pixmap(dpi=RENDER_DPI)

    # Draw on it using pymupdf Shape on the page, then re-render
    # Actually, let's draw directly using the pixmap approach —
    # we'll use a fresh page annotation approach
    # Simpler: render clean page, then overlay in HTML with CSS

    return pix.tobytes("png")


def generate_html(pdf_path, page_num, page_png, images, text_blocks, pairs):
    """Generate an HTML review page."""
    page_b64 = base64.b64encode(page_png).decode()
    pdf_name = Path(pdf_path).stem

    # Build pair rows
    pair_rows = []
    for i, pair in enumerate(pairs):
        img = pair["image"]
        texts = pair["text_blocks"]
        dist = pair["distance"]

        # Image thumbnail
        if img["img_bytes"]:
            img_b64 = base64.b64encode(img["img_bytes"]).decode()
            img_tag = f'<img src="data:image/png;base64,{img_b64}" style="max-width:200px;max-height:150px;border:1px solid #ccc;">'
        else:
            img_tag = '<div style="width:100px;height:60px;background:#eee;display:flex;align-items:center;justify-content:center;font-size:11px;">no xref</div>'

        # Text content
        text_html = "<br>".join(
            f'<span style="background:#ffffcc;padding:2px 4px;">{tb["text"][:120]}</span>'
            for tb in texts
        ) if texts else '<em style="color:#999;">no text matched</em>'

        # Bbox info
        ib = img["bbox"]
        bbox_str = f'[{ib[0]:.0f}, {ib[1]:.0f}, {ib[2]:.0f}, {ib[3]:.0f}]'

        color = "#4a4" if dist < 30 else "#aa4" if dist < 80 else "#a44"

        pair_rows.append(f"""
        <tr>
            <td>{i+1}</td>
            <td>{img_tag}</td>
            <td>{img["width"]}x{img["height"]}</td>
            <td>{bbox_str}</td>
            <td>{text_html}</td>
            <td style="color:{color};font-weight:bold;">{dist:.0f}pt</td>
        </tr>""")

    # Build overlay boxes for the page image (scaled to RENDER_DPI)
    overlay_boxes = []
    colors = ["#ff4444", "#44ff44", "#4444ff", "#ff44ff", "#44ffff", "#ffaa00", "#aa44ff", "#ff6644"]
    for i, pair in enumerate(pairs):
        img = pair["image"]
        b = img["bbox"]
        color = colors[i % len(colors)]
        overlay_boxes.append(
            f'<div style="position:absolute;left:{b[0]*SCALE:.0f}px;top:{b[1]*SCALE:.0f}px;'
            f'width:{(b[2]-b[0])*SCALE:.0f}px;height:{(b[3]-b[1])*SCALE:.0f}px;'
            f'border:3px solid {color};background:{color}22;pointer-events:none;">'
            f'<span style="background:{color};color:white;font-size:11px;padding:1px 4px;">{i+1}</span></div>'
        )

    # Text block overlays (blue, semi-transparent)
    text_overlays = []
    for tb in text_blocks:
        b = tb["bbox"]
        text_overlays.append(
            f'<div style="position:absolute;left:{b[0]*SCALE:.0f}px;top:{b[1]*SCALE:.0f}px;'
            f'width:{(b[2]-b[0])*SCALE:.0f}px;height:{(b[3]-b[1])*SCALE:.0f}px;'
            f'border:1px solid #2266ff44;background:#2266ff11;pointer-events:none;"></div>'
        )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Image-Text Pairing: {pdf_name} p.{page_num}</title>
<style>
body {{ font-family: -apple-system, sans-serif; margin: 20px; background: #f5f5f5; }}
h1 {{ font-size: 18px; }}
.layout {{ display: flex; gap: 24px; align-items: flex-start; }}
.page-container {{ position: relative; flex-shrink: 0; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
.page-container img {{ display: block; }}
.pairs-table {{ flex: 1; min-width: 500px; }}
table {{ border-collapse: collapse; width: 100%; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
th {{ background: #333; color: white; padding: 8px 12px; text-align: left; font-size: 13px; }}
td {{ padding: 8px 12px; border-bottom: 1px solid #eee; vertical-align: top; font-size: 13px; }}
tr:hover {{ background: #f0f8ff; }}
.legend {{ margin: 12px 0; font-size: 13px; color: #666; }}
.toggle {{ cursor: pointer; padding: 4px 12px; border: 1px solid #ccc; border-radius: 4px; background: white; margin-right: 8px; }}
.toggle.active {{ background: #333; color: white; border-color: #333; }}
</style>
</head>
<body>
<h1>{pdf_name} — Page {page_num}</h1>
<div class="legend">
    <button class="toggle active" onclick="toggleOverlay('img')">Image boxes</button>
    <button class="toggle active" onclick="toggleOverlay('txt')">Text boxes</button>
    | Found <strong>{len(images)}</strong> images, <strong>{len(text_blocks)}</strong> text blocks, <strong>{len(pairs)}</strong> pairs
    | Distance: <span style="color:#4a4;font-weight:bold;">green &lt;30pt</span>
    <span style="color:#aa4;font-weight:bold;">yellow &lt;80pt</span>
    <span style="color:#a44;font-weight:bold;">red &gt;80pt</span>
</div>

<div class="layout">
    <div class="page-container">
        <img src="data:image/png;base64,{page_b64}">
        <div id="img-overlay">{"".join(overlay_boxes)}</div>
        <div id="txt-overlay">{"".join(text_overlays)}</div>
    </div>

    <div class="pairs-table">
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Image</th>
                    <th>Size</th>
                    <th>BBox</th>
                    <th>Matched Text</th>
                    <th>Dist</th>
                </tr>
            </thead>
            <tbody>
                {"".join(pair_rows)}
            </tbody>
        </table>
    </div>
</div>

<script>
function toggleOverlay(type) {{
    const el = document.getElementById(type + '-overlay');
    const btn = event.target;
    if (el.style.display === 'none') {{
        el.style.display = '';
        btn.classList.add('active');
    }} else {{
        el.style.display = 'none';
        btn.classList.remove('active');
    }}
}}
</script>
</body>
</html>"""
    return html


def process_page(doc, pdf_path, page_num):
    """Process a single page and return (html, pairs_data)."""
    page = doc[page_num - 1]  # 1-indexed input

    text_blocks = extract_text_blocks(page)
    images = extract_images(page)
    pairs = match_images_to_text(images, text_blocks)

    # Render clean page
    page_png = page.get_pixmap(dpi=RENDER_DPI).tobytes("png")

    html = generate_html(pdf_path, page_num, page_png, images, text_blocks, pairs)

    # Build JSON-serializable pairs data
    pairs_data = []
    for p in pairs:
        pairs_data.append({
            "image_bbox": p["image"]["bbox"],
            "image_size": f'{p["image"]["width"]}x{p["image"]["height"]}',
            "matched_texts": [tb["text"] for tb in p["text_blocks"]],
            "distance": round(p["distance"], 1),
        })

    return html, pairs_data


def main():
    parser = argparse.ArgumentParser(description="POC: Extract image-text pairs from textbook pages")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("pages", help="Page number or range (e.g., 43 or 40-50)")
    parser.add_argument("--open", action="store_true", help="Open HTML in browser")
    parser.add_argument("--out", help="Output directory (default: /tmp/page-pairs)")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found", file=sys.stderr)
        sys.exit(1)

    # Parse page range
    if "-" in args.pages:
        start, end = args.pages.split("-")
        page_nums = list(range(int(start), int(end) + 1))
    else:
        page_nums = [int(args.pages)]

    out_dir = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="page-pairs-"))
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(str(pdf_path))
    stem = pdf_path.stem

    all_pages_html = []
    total_pairs = 0

    for page_num in page_nums:
        if page_num < 1 or page_num > len(doc):
            print(f"  Skipping page {page_num} (out of range 1-{len(doc)})")
            continue

        html, pairs_data = process_page(doc, str(pdf_path), page_num)

        # Write individual page HTML
        page_file = out_dir / f"{stem}_p{page_num:03d}.html"
        page_file.write_text(html, encoding="utf-8")

        n = len(pairs_data)
        total_pairs += n
        print(f"  Page {page_num}: {n} image-text pairs → {page_file}")

        all_pages_html.append(f'<li><a href="{page_file.name}">{stem} p.{page_num}</a> — {n} pairs</li>')

    # Write index if multiple pages
    if len(page_nums) > 1:
        index_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Page Pairs Index</title>
<style>body{{font-family:sans-serif;margin:20px;}}a{{color:#2266cc;}}</style>
</head><body>
<h1>{stem} — Image-Text Pairs</h1>
<p>{len(page_nums)} pages, {total_pairs} total pairs</p>
<ul>{"".join(all_pages_html)}</ul>
</body></html>"""
        index_file = out_dir / f"{stem}_index.html"
        index_file.write_text(index_html, encoding="utf-8")
        print(f"\n  Index: {index_file}")

    doc.close()

    # Open in browser
    target = out_dir / f"{stem}_index.html" if len(page_nums) > 1 else out_dir / f"{stem}_p{page_nums[0]:03d}.html"
    if args.open:
        import subprocess
        subprocess.run(["open", str(target)])
    else:
        print(f"\n  Open with: open {target}")


if __name__ == "__main__":
    main()
