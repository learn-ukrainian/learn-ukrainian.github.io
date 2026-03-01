# Plan: Image Explorer — Textbook Image Browser with Page Context & Annotation Editor

## Context

The project has **12,765 extracted textbook images** from 73 PDFs across grades 1-11, with **11,478 annotations** in `image_text_pairs.jsonl` (description_uk, teaching_value, element_type, position). But there's no unified way to:
- See images **in their original page context** (rendered PDF page with bounding boxes)
- **Edit/correct annotation labels** through a UI
- **Clean up bad images** (1,279 decorations, 925 logos, 236 teaching_value=none)

Current tools are fragmented: `images.html` shows thumbnails without annotations, `poc_pair_page.py` renders page context but only to `/tmp`, `image_review_server.py` is a standalone server with no annotation data.

**Goal**: Build a unified Image Explorer in the existing monitoring dashboard that shows images in page context, lets you edit labels, and provides quality stats.

---

## Architecture

**2 new files + 2 small edits:**

| File | Action |
|------|--------|
| `scripts/api/images_router.py` | **NEW** — FastAPI router at `/api/images/` (~450 lines) |
| `playgrounds/image-explorer.html` | **NEW** — Single-file HTML playground (~900 lines) |
| `scripts/api/main.py` | **EDIT** — 3 lines: import + mount router |
| `playgrounds/index.html` | **EDIT** — Add card link to Image Explorer |

---

## Backend: `scripts/api/images_router.py`

### Data Loading (lazy singleton)

On first request, load and merge two data sources into an in-memory index:

1. **Per-book JSONLs** (`data/textbook_images/grade-*/*-images.jsonl`) — structural metadata: image_id, page, width, height, grade, author, pdf_stem
2. **Global annotations** (`data/textbook_images/image_text_pairs.jsonl`) — labels: description_uk, associated_text_uk, teaching_value, element_type, position

Join key: `image_id`. Build secondary index `_by_pdf_page[pdf_stem][page_num] -> [records]`.

Scan `data/textbooks/grade-*/` for actual PDFs to build `_pdf_catalog` (only PDFs on disk).

### PDF Pool

LRU pool of max 10 open `pymupdf.Document` objects. Avoids reopening large PDFs on page flips.

### Endpoints

**Catalog:**
```
GET /api/images/textbooks
```
Returns list of PDFs on disk with page_count, image_count, annotated_count. Powers the textbook selector dropdown.

**Page Context (metadata):**
```
GET /api/images/page/{pdf_stem}/{page_num}
```
Returns JSON: page dimensions, image bboxes with annotations, text block bboxes. No image data in JSON.

**Page Render (PNG):**
```
GET /api/images/page_render/{pdf_stem}/{page_num}.png
```
Returns rendered PDF page as PNG (150 DPI). LRU cached (max 100 pages ~100MB). Served with `Cache-Control: max-age=3600`. Runs PyMuPDF in `asyncio.to_thread()`.

Reuses `extract_text_blocks()` and `extract_images()` from `scripts/rag/poc_pair_page.py`.

**Annotation Browse:**
```
GET /api/images/annotations?grade=&teaching_value=&element_type=&page=0&per_page=50
```
Paginated browse with filters. Returns image records with all annotation fields.

**Annotation Edit:**
```
PUT /api/images/annotations/{image_id}
Body: {"teaching_value": "low", "element_type": "decoration", "description_uk": "..."}
```
Updates in-memory index + rewrites JSONL. Creates timestamped `.bak` backup first. Protected by `asyncio.Lock()`.

**Bulk Edit:**
```
POST /api/images/annotations/bulk
Body: {"image_ids": [...], "updates": {"teaching_value": "none"}}
```
Same as single edit but for multiple records in one JSONL write.

**Stats:**
```
GET /api/images/stats
```
Returns: total_on_disk, total_annotated, unannotated_count, per_grade breakdown, teaching_value distribution, element_type distribution, bad_candidates count.

**Cleanup:**
```
POST /api/images/cleanup
Body: {"image_ids": [...]}
```
Deletes PNG files from disk + removes entries from both JSONLs. Backup first.

**Reload:**
```
POST /api/images/reload
```
Force reload of in-memory indexes from disk.

---

## Frontend: `playgrounds/image-explorer.html`

Follows existing patterns: vanilla JS, GitHub dark theme CSS vars, `fetch()` API, tab system.

### Tab 1: Page Context

```
[Textbook Dropdown v]  Page: [<- 43 ->] / 114

+---------------------+---------------------------+
|                     |  #  Thumb  Desc  TV  Type |
|  Rendered PDF page  |  1  [img]  abc   H   ill  |
|  with bbox overlays |  2  [img]  def   M   dec  |
|                     |  3  [img]  ghi   L   logo |
|  [Toggle: images]   |                           |
|  [Toggle: text]     |                           |
+---------------------+---------------------------+
```

- `<img>` points to `/api/images/page_render/{stem}/{page}.png`
- Bbox overlays as `position: absolute` divs (colored borders, numbered labels)
- Text blocks as semi-transparent blue outlines
- Toggle buttons for image/text overlays
- Click image row -> highlights corresponding bbox; hover bbox -> highlights row
- Arrow keys for prev/next page

### Tab 2: Annotation Editor

```
Filters: [Grade v] [Teaching Value v] [Type v]
[Select All] [Bulk: Set TV v] [Bulk: Delete]

[ ] [thumb] desc: [__________] TV: [high v] Type: [illustration v] [Save]
[ ] [thumb] desc: [__________] TV: [medium v] Type: [decoration v]  [Save]
...
[<- Prev] Page 1/230 [Next ->]
```

- Filter buttons (same pattern as `images.html`)
- Each row: checkbox, thumbnail (80px), editable description_uk input, teaching_value select, element_type select, Save button
- Bulk: select all, set teaching_value for selected, mark for deletion + confirm
- Pagination (50 per page)

### Tab 3: Stats & Quality

```
Total: 12,765  Annotated: 11,478  Gap: 1,287  Bad: 1,394

[Teaching Value Bar]  [Element Type Bar]  [Per-Grade Coverage]

Bad Candidates by Grade:
  Grade 1: 52 none + 103 low  [View ->]
  Grade 2: 18 none + 87 low   [View ->]
```

- Summary stat pills (like comms.html health pills)
- CSS-only horizontal stacked bars for distributions
- Per-grade table with "View" links that switch to Tab 2 with filters pre-set

---

## Key Design Decisions

1. **Separate PNG endpoint** (not base64 in JSON): Page renders are 500KB-2MB. Serving as PNG allows browser caching and parallel loading.

2. **Reuse poc_pair_page.py** functions: Import `extract_text_blocks()`, `extract_images()` instead of duplicating. Add `scripts/rag/` to sys.path in the router.

3. **LRU page cache**: 100 pages max (~100MB). Cleared on `/reload`. Acceptable for a dev tool.

4. **Write-back with backup**: Every JSONL edit creates a timestamped `.bak` copy. 11K-line rewrite takes <100ms.

5. **Graceful PDF mismatch handling**: Some image_ids reference PDFs that don't exist on disk (e.g., `bolshakova-2025` vs `bolshakova-2018`). The `/textbooks` endpoint only lists PDFs on disk. Tab 2 works for all images regardless of PDF availability.

---

## Implementation Order

1. `scripts/api/images_router.py` — data loading + stats + textbooks + annotations browse/edit + page render
2. `scripts/api/main.py` — mount the router (3 lines)
3. `playgrounds/image-explorer.html` — Tab 3 (stats) first, then Tab 2 (annotations), then Tab 1 (page context)
4. `playgrounds/index.html` — add card

---

## Verification

```bash
# 1. Start the API server
.venv/bin/python -m uvicorn scripts.api.main:app --host 0.0.0.0 --port 8765

# 2. Test endpoints with curl
curl http://localhost:8765/api/images/stats | python -m json.tool
curl http://localhost:8765/api/images/textbooks | python -m json.tool
curl "http://localhost:8765/api/images/annotations?grade=1&per_page=3" | python -m json.tool
curl http://localhost:8765/api/images/page/1-klas-bukvar-zaharijchuk-2025-1/43 | python -m json.tool
curl http://localhost:8765/api/images/page_render/1-klas-bukvar-zaharijchuk-2025-1/43.png -o /tmp/test.png && open /tmp/test.png

# 3. Test annotation edit
curl -X PUT http://localhost:8765/api/images/annotations/1-klas-bukvar-zaharijchuk-2025-1_p003_i01 \
  -H "Content-Type: application/json" \
  -d '{"teaching_value": "low"}'

# 4. Open browser and verify all 3 tabs
open http://localhost:8765/image-explorer.html

# 5. Verify backup creation
ls -la data/textbook_images/image_text_pairs.jsonl.bak.*
```

---

## Key Files to Reference

| File | Purpose |
|------|---------|
| `scripts/rag/poc_pair_page.py` | Reuse: `extract_text_blocks()`, `extract_images()`, RENDER_DPI, SCALE |
| `scripts/rag/config.py` | Paths: IMAGES_DIR, TEXTBOOKS_DIR, metadata parsing |
| `scripts/api/rag_router.py` | Pattern: how existing RAG endpoints are structured |
| `playgrounds/images.html` | Pattern: tab system, filter buttons, gallery grid, lightbox |
| `playgrounds/comms.html` | Pattern: stat pills, auto-refresh, dark theme |
| `data/textbook_images/image_text_pairs.jsonl` | Global annotations (11,478 records) |
| `data/textbook_images/grade-*/*-images.jsonl` | Per-book structural metadata |
