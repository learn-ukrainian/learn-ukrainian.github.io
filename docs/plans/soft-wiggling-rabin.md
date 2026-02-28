# Plan: Image Annotation Pipeline — PyMuPDF Spatial Matching

## Context

Qdrant has 18,711 text chunks and 11,478 images from all grades 1-11, but images have **no Ukrainian text context**. SigLIP finds apple pictures for "яблуко", but we don't know what Ukrainian word/sentence was on the textbook page next to that image. This blocks building l2-uk-direct curriculum (#662) where images anchor meaning instead of English.

**Goal:** For each of the ~11.5K extracted images, find the nearest Ukrainian text from the same PDF page using PyMuPDF bounding box coordinates. Write annotations to `data/textbook_images/image_text_pairs.jsonl` — the file `ingest.py` already reads and merges into Qdrant payloads. No new dependencies, no API calls, no Gemini Vision.

**Blocks:** #662 (A1 Module Build), #664 (source_images_direct.py)

## Pre-Step: POC Verification + Search Smoke Test

Before building anything, verify existing infrastructure works:

1. **Search smoke test** — confirm Qdrant text+image search returns results:
   ```bash
   .venv/bin/python scripts/rag/query.py text "яблуко" --grade 1
   .venv/bin/python scripts/rag/query.py images "яблуко" --grade 1
   ```
   Also test via MCP: `mcp__rag__search_text` and `mcp__rag__search_images`

2. **POC spatial matching** — run on 3 diverse pages, visually verify HTML output:
   ```bash
   .venv/bin/python scripts/rag/poc_pair_page.py data/textbooks/grade-01/1-klas-bukvar-zaharijchuk-2025-1.pdf 43 --open
   .venv/bin/python scripts/rag/poc_pair_page.py data/textbooks/grade-05/5-klas-ukrmova-avramenko-2022.pdf 13 --open
   .venv/bin/python scripts/rag/poc_pair_page.py data/textbooks/grade-03/3-klas-ukrainska-mova-vashulenko-2020-1.pdf 6 --open
   ```

3. **Verify xref mapping** — confirm that `page.get_images()[image_index][0]` xref matches `page.get_image_info(xrefs=True)` bbox for the same image. This is the critical bridge between extracted images and spatial coordinates.

## Step 1: Build `scripts/rag/annotate_images.py`

### Core Algorithm

For each book (PDF + its `-images.jsonl`):
1. Load image records, group by page number
2. Open PDF once
3. For each page that has images:
   - `page.get_images(full=True)` → xref list
   - `page.get_image_info(xrefs=True)` → xref→bbox mapping
   - `page.get_text("dict")` → text blocks with bboxes
   - For each image record: recover xref via `image_index`, look up bbox, find nearest text block(s) by bbox distance
4. Write annotations

### Xref Mapping (Critical Bridge)

```
image_index (from JSONL) → page.get_images(full=True)[image_index][0] → xref
xref → page.get_image_info(xrefs=True) → bbox
bbox → bbox_distance(image_bbox, text_bbox) → nearest text
```

`image_index` in JSONL is the enumeration position in `page.get_images()` (see `extract_images.py:53,83`), NOT a contiguous counter of kept images.

### CLI Interface

```bash
.venv/bin/python scripts/rag/annotate_images.py --all           # All books
.venv/bin/python scripts/rag/annotate_images.py --grade 1 3     # Specific grades
.venv/bin/python scripts/rag/annotate_images.py --book {stem}   # Single book
.venv/bin/python scripts/rag/annotate_images.py --stats         # Progress/distribution stats
```

### Output: `data/textbook_images/image_text_pairs.jsonl`

One JSON line per image:
```json
{
  "image_id": "3-klas-ukrainska-mova-vashulenko-2020-1_p006_i01",
  "description_uk": "Вправа",
  "associated_text_uk": "Прочитай вірш. Спиши, вставляючи пропущені букви.",
  "teaching_value": "medium",
  "element_type": "illustration",
  "position": "top-right"
}
```

- `description_uk` = nearest short text block (word/phrase) — for vocabulary images this IS the label
- `associated_text_uk` = concatenated nearby text blocks, up to ~200 chars — the broader context
- `teaching_value` = high / medium / low / none (heuristic, see below)
- `element_type` = illustration / letter / diagram / decoration / QR / logo (heuristic)
- `position` = 3×3 grid: top-left, center, bottom-right, etc.

### Restartability

- Progress dir: `data/textbook_images/.annotate_progress/`
- After each book completes: write `{pdf_stem}.done` marker file
- On startup: skip books with existing `.done` markers
- Single book takes <2s, so losing in-progress book on crash is acceptable
- `--all` rewrites entire `image_text_pairs.jsonl` atomically (temp file → rename)

### Classification Heuristics

**Teaching value:**
| Condition | Value |
|-----------|-------|
| Rendered size < 30pt either dimension | `none` |
| No text within 200pt | `none` |
| Only nearby text is page number (bottom 5% of page, digits only) | `low` |
| Nearest text ≤30 chars, distance < 80pt | `high` (vocabulary illustration) |
| Nearest text ≤100 chars, distance < 50pt | `medium` |
| Paragraph-level text nearby, distance < 50pt | `medium` |
| Everything else | `low` |

**Element type:**
| Condition | Type |
|-----------|------|
| Square-ish (0.8-1.2 aspect), 30-120pt, small | `QR` |
| Small (<80pt), near single-char text (≤3 chars) | `letter` |
| Aspect ratio > 8 or < 0.125 (very wide/thin) | `decoration` |
| Covers >90% of page | `decoration` |
| Small (<60pt), in corner (<10% from edge) | `logo` |
| Default | `illustration` |

### Functions to Reuse from POC (`poc_pair_page.py`)

- `extract_text_blocks(page)` → lines 29-49 (text blocks with bboxes)
- `bbox_distance(b1, b2)` → lines 92-97 (min distance between bboxes)
- `bbox_center(bbox)` → lines 87-88

### Key Files

| File | Action |
|------|--------|
| `scripts/rag/annotate_images.py` | **CREATE** — main annotation script |
| `scripts/rag/poc_pair_page.py` | READ — reuse spatial matching logic |
| `scripts/rag/extract_images.py` | READ — understand `image_index` → xref mapping |
| `scripts/rag/ingest.py:242-277` | NO CHANGE — already reads `image_text_pairs.jsonl` |
| `scripts/rag/config.py` | READ — import `IMAGES_DIR`, `TEXTBOOKS_DIR`, `parse_pdf_metadata` |
| `.mcp/servers/rag/server.py` | NO CHANGE — already returns annotation fields |

## Step 2: Run Annotation

```bash
# Single book test first
.venv/bin/python scripts/rag/annotate_images.py --book 1-klas-bukvar-zaharijchuk-2025-1

# Verify output
head -5 data/textbook_images/image_text_pairs.jsonl

# Full batch
.venv/bin/python scripts/rag/annotate_images.py --all

# Check stats
.venv/bin/python scripts/rag/annotate_images.py --stats
```

Expected: ~11.5K annotation records. Scanned books (empty JSONLs) auto-skipped. Runtime: <5 minutes for all books (PyMuPDF only, no ML models).

## Step 3: Re-ingest Annotated Images

```bash
# Re-ingest all grades (upserts — same image IDs, enriched payloads)
.venv/bin/python scripts/rag/ingest.py --all --grade 1 2 3 4 5 6 7 8 9 10 11
```

This reloads SigLIP (heavy), re-embeds images (unchanged vectors), and merges annotation fields from `image_text_pairs.jsonl` into Qdrant payloads. Existing points are upserted (same hash-based IDs).

## Step 4: Verify End-to-End

```bash
# CLI search — should now show description_uk and associated_text_uk
.venv/bin/python scripts/rag/query.py images "яблуко" --grade 1

# MCP search
# mcp__rag__search_images query="яблуко" grade=1

# Filter by teaching value
# mcp__rag__search_images query="буква А" teaching_value="high"

# Playground
.venv/bin/python -m uvicorn scripts.api.main:app --port 8790
```

## What Does NOT Change

- `ingest.py` — already reads `image_text_pairs.jsonl` ✅
- MCP server — already returns annotation fields ✅
- `query.py` — already displays annotation fields ✅
- Image extraction — already done ✅
- Qdrant schema — `teaching_value` already indexed as KEYWORD ✅

## Resource Notes

- Annotation: CPU-only, ~100MB RAM (PyMuPDF only, no ML models)
- Re-ingestion: ~1.5GB RAM (SigLIP model loading)
- Qdrant: already running
