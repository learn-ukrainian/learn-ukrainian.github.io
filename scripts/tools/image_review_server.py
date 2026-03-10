#!/usr/bin/env python3
"""
Simple HTTP server for reviewing textbook images.
Browse to http://localhost:8765 to view images with filtering.
"""

import http.server
import urllib.parse
from pathlib import Path

PORT = 8791
BASE_DIR = Path(__file__).resolve().parent.parent.parent
IMAGE_DIR = BASE_DIR / "data" / "textbook_images"


def get_image_stats():
    """Collect stats about all images."""
    stats = {"grades": {}, "total": 0, "small": 0, "tiny": 0}
    for grade_dir in sorted(IMAGE_DIR.iterdir()):
        if not grade_dir.is_dir() or not grade_dir.name.startswith("grade-"):
            continue
        grade = grade_dir.name
        images = list(grade_dir.glob("*.png"))
        small = [f for f in images if f.stat().st_size < 5000]
        tiny = [f for f in images if f.stat().st_size < 2000]
        stats["grades"][grade] = {
            "total": len(images),
            "small": len(small),
            "tiny": len(tiny),
        }
        stats["total"] += len(images)
        stats["small"] += len(small)
        stats["tiny"] += len(tiny)
    return stats


def build_html(grade=None, max_size=None, min_size=None, page=0, per_page=100, sort="size"):
    """Build HTML gallery for image review."""
    images = []

    if grade:
        search_dirs = [IMAGE_DIR / grade]
    else:
        search_dirs = sorted(d for d in IMAGE_DIR.iterdir() if d.is_dir() and d.name.startswith("grade-"))

    for d in search_dirs:
        for f in d.glob("*.png"):
            size = f.stat().st_size
            if max_size and size > max_size:
                continue
            if min_size and size < min_size:
                continue
            images.append({
                "path": str(f.relative_to(BASE_DIR)),
                "name": f.name,
                "size": size,
                "grade": d.name,
            })

    if sort == "size":
        images.sort(key=lambda x: x["size"])
    elif sort == "name":
        images.sort(key=lambda x: x["name"])
    elif sort == "grade":
        images.sort(key=lambda x: (x["grade"], x["name"]))

    total = len(images)
    start = page * per_page
    end = start + per_page
    page_images = images[start:end]
    total_pages = (total + per_page - 1) // per_page

    stats = get_image_stats()

    # Build navigation

    nav_links = []
    for g in sorted(stats["grades"].keys()):
        g_info = stats["grades"][g]
        active = " style='font-weight:bold;background:#ddd'" if g == grade else ""
        nav_links.append(
            f'<a href="/?grade={g}&sort={sort}"{active}>{g} ({g_info["total"]} imgs, {g_info["small"]} small)</a>'
        )

    pagination = []
    if page > 0:
        pagination.append(f'<a href="/?grade={grade or ""}&max_size={max_size or ""}&sort={sort}&page={page-1}">&laquo; Prev</a>')
    pagination.append(f'<span>Page {page+1}/{total_pages} ({total} images)</span>')
    if end < total:
        pagination.append(f'<a href="/?grade={grade or ""}&max_size={max_size or ""}&sort={sort}&page={page+1}">Next &raquo;</a>')

    image_cards = []
    for img in page_images:
        size_kb = img["size"] / 1024
        color = "#f44" if img["size"] < 2000 else "#fa0" if img["size"] < 5000 else "#4a4"
        image_cards.append(f'''
        <div class="card" style="border-left: 4px solid {color}">
            <img src="/image/{img['path']}" loading="lazy" />
            <div class="info">
                <span class="name">{img['name']}</span>
                <span class="size" style="color:{color}">{size_kb:.1f} KB</span>
                <span class="grade">{img['grade']}</span>
                <button onclick="markBad('{img['path']}')" class="bad-btn">Mark Bad</button>
            </div>
        </div>''')

    return f'''<!DOCTYPE html>
<html>
<head>
<title>Textbook Image Review</title>
<style>
body {{ font-family: system-ui; margin: 20px; background: #1a1a2e; color: #eee; }}
h1 {{ color: #e94560; }}
.stats {{ background: #16213e; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
.stats table {{ border-collapse: collapse; width: 100%; }}
.stats td, .stats th {{ padding: 6px 12px; text-align: left; border-bottom: 1px solid #333; }}
.nav {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px; }}
.nav a {{ padding: 6px 12px; background: #16213e; border-radius: 4px; color: #eee; text-decoration: none; font-size: 13px; }}
.nav a:hover {{ background: #0f3460; }}
.filters {{ display: flex; gap: 15px; margin-bottom: 15px; align-items: center; }}
.filters a {{ color: #e94560; }}
.pagination {{ display: flex; gap: 15px; align-items: center; margin: 15px 0; }}
.pagination a {{ color: #e94560; font-size: 16px; }}
.gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 12px; }}
.card {{ background: #16213e; border-radius: 8px; overflow: hidden; }}
.card img {{ width: 100%; height: 200px; object-fit: contain; background: #fff; cursor: pointer; }}
.card img:hover {{ object-fit: cover; }}
.info {{ padding: 8px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; font-size: 12px; }}
.name {{ flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 100px; }}
.size {{ font-weight: bold; }}
.grade {{ background: #0f3460; padding: 2px 6px; border-radius: 3px; }}
.bad-btn {{ background: #e94560; color: white; border: none; padding: 3px 8px; border-radius: 3px; cursor: pointer; font-size: 11px; }}
.bad-btn:hover {{ background: #c23152; }}
#bad-list {{ position: fixed; bottom: 0; left: 0; right: 0; background: #16213e; padding: 10px 20px; border-top: 2px solid #e94560; display: none; max-height: 150px; overflow-y: auto; z-index: 100; }}
#bad-list.visible {{ display: block; }}
#bad-count {{ position: fixed; bottom: 10px; right: 20px; background: #e94560; color: white; padding: 8px 16px; border-radius: 20px; cursor: pointer; z-index: 101; }}
</style>
</head>
<body>
<h1>Textbook Image Review</h1>

<div class="stats">
<table>
<tr><th>Total images</th><td>{stats['total']}</td><th>Under 5KB (suspect)</th><td style="color:#fa0">{stats['small']}</td><th>Under 2KB (likely bad)</th><td style="color:#f44">{stats['tiny']}</td></tr>
</table>
</div>

<div class="nav">
<a href="/?sort={sort}">All grades</a>
{" ".join(nav_links)}
</div>

<div class="filters">
<strong>Quick filters:</strong>
<a href="/?grade={grade or ''}&max_size=2000&sort=size">Tiny (&lt;2KB)</a>
<a href="/?grade={grade or ''}&max_size=5000&sort=size">Small (&lt;5KB)</a>
<a href="/?grade={grade or ''}&max_size=10000&sort=size">Medium (&lt;10KB)</a>
<a href="/?grade={grade or ''}&sort=size">All (by size)</a>
<a href="/?grade={grade or ''}&sort=name">All (by name)</a>
</div>

<div class="pagination">
{" | ".join(pagination)}
</div>

<div class="gallery">
{"".join(image_cards)}
</div>

<div class="pagination">
{" | ".join(pagination)}
</div>

<div id="bad-list"></div>
<div id="bad-count" onclick="toggleBadList()">Bad: <span id="count">0</span></div>

<script>
let badImages = JSON.parse(localStorage.getItem('badImages') || '[]');
updateCount();

function markBad(path) {{
    if (!badImages.includes(path)) {{
        badImages.push(path);
        localStorage.setItem('badImages', JSON.stringify(badImages));
        updateCount();
    }}
}}

function updateCount() {{
    document.getElementById('count').textContent = badImages.length;
    let html = '<h3>Marked as bad (' + badImages.length + ') <button onclick="exportBad()">Export List</button> <button onclick="clearBad()">Clear</button></h3>';
    html += '<pre>' + badImages.join('\\n') + '</pre>';
    document.getElementById('bad-list').innerHTML = html;
}}

function toggleBadList() {{
    document.getElementById('bad-list').classList.toggle('visible');
}}

function exportBad() {{
    const blob = new Blob([badImages.join('\\n')], {{type: 'text/plain'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'bad-images.txt';
    a.click();
}}

function clearBad() {{
    if (confirm('Clear all marked images?')) {{
        badImages = [];
        localStorage.setItem('badImages', JSON.stringify(badImages));
        updateCount();
    }}
}}
</script>
</body>
</html>'''


class ImageReviewHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path.startswith("/image/"):
            # Serve image file
            img_path = BASE_DIR / urllib.parse.unquote(parsed.path[7:])
            if img_path.exists() and img_path.suffix == ".png":
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Cache-Control", "max-age=3600")
                self.end_headers()
                with open(img_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404)
            return

        # Parse query params
        params = urllib.parse.parse_qs(parsed.query)
        grade = params.get("grade", [None])[0] or None
        if grade == "":
            grade = None
        max_size = params.get("max_size", [None])[0]
        max_size = int(max_size) if max_size else None
        min_size = params.get("min_size", [None])[0]
        min_size = int(min_size) if min_size else None
        page = int(params.get("page", [0])[0])
        sort = params.get("sort", ["size"])[0]

        html = build_html(grade=grade, max_size=max_size, min_size=min_size, page=page, sort=sort)

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        # Suppress request logs
        pass


if __name__ == "__main__":
    print(f"Starting image review server at http://localhost:{PORT}")
    print(f"Image directory: {IMAGE_DIR}")
    print(f"Total PNG files: {sum(1 for _ in IMAGE_DIR.rglob('*.png'))}")
    server = http.server.HTTPServer(("localhost", PORT), ImageReviewHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
        server.shutdown()
