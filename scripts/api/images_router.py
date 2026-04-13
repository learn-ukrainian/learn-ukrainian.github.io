"""Image Explorer API — browse textbook images with page context & annotations.

Mounts at /api/images/ — provides:
  - Textbook catalog (PDFs on disk)
  - Page context rendering (PDF page as PNG with bbox metadata)
  - Annotation browse/edit/bulk operations
  - Stats & quality metrics
  - Cleanup (delete bad images)

Data sources:
  - Per-book JSONLs: data/textbook_images/grade-*/*-images.jsonl (structural metadata)
  - Global annotations: data/textbook_images/image_text_pairs.jsonl (labels)
  - PDFs: data/textbooks/grade-*/*.pdf
"""

import asyncio
import json
import shutil
import sys
from collections import OrderedDict
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from .config import PROJECT_ROOT

# Ensure scripts/ is importable for rag.poc_pair_page
_scripts_dir = str(PROJECT_ROOT / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

router = APIRouter(tags=["images"])

# ── Paths ────────────────────────────────────────────────────────────

IMAGES_DIR = PROJECT_ROOT / "data" / "textbook_images"
TEXTBOOKS_DIR = PROJECT_ROOT / "data" / "textbooks"
ANNOTATIONS_FILE = IMAGES_DIR / "image_text_pairs.jsonl"


# ── Data Index (lazy singleton) ──────────────────────────────────────

class _ImageIndex:
    """In-memory index of all image metadata + annotations."""

    def __init__(self):
        self._loaded = False
        self._records: dict[str, dict] = {}           # image_id -> merged record
        self._by_pdf_page: dict[str, dict[int, list]] = {}  # pdf_stem -> page -> [records]
        self._annotations: dict[str, dict] = {}       # image_id -> annotation fields
        self._pdf_catalog: dict[str, dict] = {}       # pdf_stem -> {path, grade, pages}
        self._lock = asyncio.Lock()

    def _load_sync(self):
        """Load all data sources. Called once on first request."""
        records = {}
        annotations = {}

        # 1. Load per-book structural JSONLs
        for jsonl_file in sorted(IMAGES_DIR.rglob("*-images.jsonl")):
            with open(jsonl_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    image_id = rec.get("image_id", "")
                    if image_id:
                        records[image_id] = rec

        # 2. Load global annotations
        if ANNOTATIONS_FILE.exists():
            with open(ANNOTATIONS_FILE) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    ann = json.loads(line)
                    image_id = ann.get("image_id", "")
                    if image_id:
                        annotations[image_id] = ann

        # 3. Merge annotations into records
        for image_id, ann in annotations.items():
            if image_id in records:
                records[image_id].update(ann)
            else:
                # Annotation without structural metadata — still include
                records[image_id] = ann

        # 4. Build secondary index: pdf_stem -> page -> [records]
        by_pdf_page: dict[str, dict[int, list]] = {}
        for rec in records.values():
            stem = rec.get("pdf_stem", "")
            page = rec.get("page")
            if stem and page is not None:
                by_pdf_page.setdefault(stem, {}).setdefault(page, []).append(rec)

        # 5. Scan for actual PDFs on disk
        pdf_catalog = {}
        for grade_dir in sorted(TEXTBOOKS_DIR.iterdir()):
            if not grade_dir.is_dir() or not grade_dir.name.startswith("grade-"):
                continue
            for pdf_file in sorted(grade_dir.glob("*.pdf")):
                pdf_catalog[pdf_file.stem] = {
                    "path": str(pdf_file),
                    "grade_dir": grade_dir.name,
                    "stem": pdf_file.stem,
                }

        self._records = records
        self._annotations = annotations
        self._by_pdf_page = by_pdf_page
        self._pdf_catalog = pdf_catalog
        self._loaded = True

    async def ensure_loaded(self):
        if self._loaded:
            return
        async with self._lock:
            if self._loaded:
                return
            await asyncio.to_thread(self._load_sync)

    def reload(self):
        self._loaded = False
        self._records.clear()
        self._annotations.clear()
        self._by_pdf_page.clear()
        self._pdf_catalog.clear()

    @property
    def records(self):
        return self._records

    @property
    def annotations(self):
        return self._annotations

    @property
    def by_pdf_page(self):
        return self._by_pdf_page

    @property
    def pdf_catalog(self):
        return self._pdf_catalog


_index = _ImageIndex()


# ── PDF Pool (LRU, max 10 open docs) ────────────────────────────────

class _PDFPool:
    """LRU pool of open pymupdf.Document objects."""

    def __init__(self, max_size: int = 10):
        self._pool: OrderedDict[str, object] = OrderedDict()
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def get(self, pdf_path: str):
        async with self._lock:
            if pdf_path in self._pool:
                self._pool.move_to_end(pdf_path)
                return self._pool[pdf_path]

            import pymupdf
            doc = pymupdf.open(pdf_path)

            if len(self._pool) >= self._max_size:
                _, old_doc = self._pool.popitem(last=False)
                old_doc.close()

            self._pool[pdf_path] = doc
            return doc

    async def clear(self):
        async with self._lock:
            for doc in self._pool.values():
                doc.close()
            self._pool.clear()


_pdf_pool = _PDFPool()


# ── Page render cache (LRU, max 100 pages) ──────────────────────────

_page_cache: OrderedDict[str, bytes] = OrderedDict()
_PAGE_CACHE_MAX = 100


def _cache_page_render(key: str, png_bytes: bytes):
    _page_cache[key] = png_bytes
    _page_cache.move_to_end(key)
    while len(_page_cache) > _PAGE_CACHE_MAX:
        _page_cache.popitem(last=False)


# ── Request/Response models ──────────────────────────────────────────

class AnnotationUpdate(BaseModel):
    teaching_value: str | None = None
    element_type: str | None = None
    description_uk: str | None = None
    associated_text_uk: str | None = None
    position: str | None = None


class BulkAnnotationUpdate(BaseModel):
    image_ids: list[str]
    updates: AnnotationUpdate


class CleanupRequest(BaseModel):
    image_ids: list[str]


# ── JSONL write helper ───────────────────────────────────────────────

_write_lock = asyncio.Lock()


async def _rewrite_annotations_jsonl():
    """Rewrite the global annotations JSONL from in-memory index.

    Creates a timestamped .bak before writing.
    """
    async with _write_lock:
        await asyncio.to_thread(_rewrite_annotations_jsonl_sync)


def _rewrite_annotations_jsonl_sync():
    if ANNOTATIONS_FILE.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = ANNOTATIONS_FILE.with_suffix(f".jsonl.bak.{ts}")
        shutil.copy2(ANNOTATIONS_FILE, bak)

    annotation_fields = {
        "image_id", "description_uk", "associated_text_uk",
        "teaching_value", "element_type", "position",
    }

    with open(ANNOTATIONS_FILE, "w") as f:
        for image_id, rec in sorted(_index.records.items()):
            # Only write records that have annotation data
            ann = {k: rec[k] for k in annotation_fields if k in rec and rec[k] is not None}
            if len(ann) <= 1:  # Only image_id, no real annotation
                continue
            ann["image_id"] = image_id
            f.write(json.dumps(ann, ensure_ascii=False) + "\n")


# ── Endpoints ────────────────────────────────────────────────────────

@router.get("/textbooks")
async def list_textbooks():
    """List PDFs on disk with image counts and annotation coverage."""
    await _index.ensure_loaded()

    result = []
    for stem, info in sorted(_index.pdf_catalog.items()):
        # Count images from this PDF
        pages_with_images = _index.by_pdf_page.get(stem, {})
        image_count = sum(len(imgs) for imgs in pages_with_images.values())
        annotated_count = sum(
            1 for imgs in pages_with_images.values()
            for img in imgs
            if img.get("description_uk")
        )

        # Get page count from PDF
        try:
            doc = await _pdf_pool.get(info["path"])
            page_count = len(doc)
        except Exception:
            page_count = 0

        result.append({
            "stem": stem,
            "grade_dir": info["grade_dir"],
            "page_count": page_count,
            "image_count": image_count,
            "annotated_count": annotated_count,
        })

    return result


@router.get("/page/{pdf_stem}/{page_num}")
async def get_page_context(pdf_stem: str, page_num: int):
    """Get page metadata: image bboxes with annotations, text block bboxes."""
    await _index.ensure_loaded()

    if pdf_stem not in _index.pdf_catalog:
        raise HTTPException(404, f"PDF not found: {pdf_stem}")

    pdf_path = _index.pdf_catalog[pdf_stem]["path"]
    doc = await _pdf_pool.get(pdf_path)

    if page_num < 1 or page_num > len(doc):
        raise HTTPException(400, f"Page {page_num} out of range (1-{len(doc)})")

    def _extract(doc, page_num):
        from rag.poc_pair_page import SCALE, extract_images, extract_text_blocks
        page = doc[page_num - 1]
        text_blocks = extract_text_blocks(page)
        images = extract_images(page)
        rect = page.rect
        return text_blocks, images, rect, SCALE

    text_blocks, images, rect, scale = await asyncio.to_thread(
        _extract, doc, page_num
    )

    # Merge with annotation data
    page_records = _index.by_pdf_page.get(pdf_stem, {}).get(page_num, [])
    records_by_index = {r.get("image_index"): r for r in page_records}

    image_data = []
    for img in images:
        rec = records_by_index.get(img["index"] + 1, {})  # image_index is 1-based in JSONL
        image_data.append({
            "bbox": img["bbox"],
            "width": img["width"],
            "height": img["height"],
            "index": img["index"],
            "image_id": rec.get("image_id", ""),
            "image_path": rec.get("image_path", ""),
            "description_uk": rec.get("description_uk", ""),
            "teaching_value": rec.get("teaching_value", ""),
            "element_type": rec.get("element_type", ""),
            "position": rec.get("position", ""),
        })

    text_data = [{"bbox": tb["bbox"], "text": tb["text"][:200]} for tb in text_blocks]

    return {
        "pdf_stem": pdf_stem,
        "page_num": page_num,
        "page_width": rect.width,
        "page_height": rect.height,
        "scale": scale,
        "images": image_data,
        "text_blocks": text_data,
        "total_pages": len(doc),
    }


@router.get("/page_render/{pdf_stem}/{page_num}.png")
async def render_page_png(pdf_stem: str, page_num: int):
    """Render a PDF page as PNG at 150 DPI. Cached."""
    await _index.ensure_loaded()

    if pdf_stem not in _index.pdf_catalog:
        raise HTTPException(404, f"PDF not found: {pdf_stem}")

    cache_key = f"{pdf_stem}:{page_num}"
    if cache_key in _page_cache:
        _page_cache.move_to_end(cache_key)
        return Response(
            content=_page_cache[cache_key],
            media_type="image/png",
            headers={"Cache-Control": "max-age=3600"},
        )

    pdf_path = _index.pdf_catalog[pdf_stem]["path"]
    doc = await _pdf_pool.get(pdf_path)

    if page_num < 1 or page_num > len(doc):
        raise HTTPException(400, f"Page {page_num} out of range (1-{len(doc)})")

    def _render(doc, page_num):
        from rag.poc_pair_page import RENDER_DPI
        page = doc[page_num - 1]
        pix = page.get_pixmap(dpi=RENDER_DPI)
        return pix.tobytes("png")

    png_bytes = await asyncio.to_thread(_render, doc, page_num)
    _cache_page_render(cache_key, png_bytes)

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Cache-Control": "max-age=3600"},
    )


@router.get("/annotations")
async def browse_annotations(
    grade: int | None = Query(None, description="Filter by grade"),
    teaching_value: str | None = Query(None, description="Filter by teaching_value"),
    element_type: str | None = Query(None, description="Filter by element_type"),
    unannotated: bool = Query(False, description="Show only unannotated images"),
    q: str | None = Query(None, description="Search description_uk"),
    page: int = Query(0, ge=0),
    per_page: int = Query(50, ge=1, le=200),
):
    """Browse annotations with filters and pagination."""
    await _index.ensure_loaded()

    results = []
    for rec in _index.records.values():
        if grade is not None and rec.get("grade") != grade:
            continue
        if teaching_value and rec.get("teaching_value") != teaching_value:
            continue
        if element_type and rec.get("element_type") != element_type:
            continue
        if unannotated and rec.get("description_uk"):
            continue
        if q and q.lower() not in (rec.get("description_uk") or "").lower():
            continue
        results.append({
            "image_id": rec.get("image_id", ""),
            "image_path": rec.get("image_path", ""),
            "page": rec.get("page"),
            "width": rec.get("width"),
            "height": rec.get("height"),
            "grade": rec.get("grade"),
            "pdf_stem": rec.get("pdf_stem", ""),
            "description_uk": rec.get("description_uk", ""),
            "associated_text_uk": rec.get("associated_text_uk", ""),
            "teaching_value": rec.get("teaching_value", ""),
            "element_type": rec.get("element_type", ""),
            "position": rec.get("position", ""),
        })

    total = len(results)
    start = page * per_page
    page_results = results[start:start + per_page]

    return {
        "items": page_results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }


@router.put("/annotations/{image_id}")
async def update_annotation(image_id: str, body: AnnotationUpdate):
    """Update annotation fields for a single image."""
    await _index.ensure_loaded()

    if image_id not in _index.records:
        raise HTTPException(404, f"Image not found: {image_id}")

    rec = _index.records[image_id]
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")

    rec.update(updates)
    await _rewrite_annotations_jsonl()

    return {"status": "ok", "image_id": image_id, "updated_fields": list(updates.keys())}


@router.post("/annotations/bulk")
async def bulk_update_annotations(body: BulkAnnotationUpdate):
    """Bulk update annotation fields for multiple images."""
    await _index.ensure_loaded()

    updates = body.updates.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")

    updated = []
    missing = []
    for image_id in body.image_ids:
        if image_id in _index.records:
            _index.records[image_id].update(updates)
            updated.append(image_id)
        else:
            missing.append(image_id)

    if updated:
        await _rewrite_annotations_jsonl()

    return {
        "status": "ok",
        "updated_count": len(updated),
        "missing": missing,
    }


@router.get("/stats")
async def get_stats():
    """Image collection statistics and quality metrics."""
    await _index.ensure_loaded()

    total = len(_index.records)
    annotated = sum(1 for r in _index.records.values() if r.get("description_uk"))
    unannotated = total - annotated

    # Teaching value distribution
    tv_dist: dict[str, int] = {}
    et_dist: dict[str, int] = {}
    grade_dist: dict[int, dict] = {}

    for rec in _index.records.values():
        tv = rec.get("teaching_value", "unset")
        tv_dist[tv] = tv_dist.get(tv, 0) + 1

        et = rec.get("element_type", "unset")
        et_dist[et] = et_dist.get(et, 0) + 1

        g = rec.get("grade")
        if g is not None:
            if g not in grade_dist:
                grade_dist[g] = {"total": 0, "annotated": 0}
            grade_dist[g]["total"] += 1
            if rec.get("description_uk"):
                grade_dist[g]["annotated"] += 1

    # Bad candidates: none or low teaching_value
    bad_count = tv_dist.get("none", 0) + tv_dist.get("low", 0)

    return {
        "total": total,
        "annotated": annotated,
        "unannotated": unannotated,
        "bad_candidates": bad_count,
        "pdfs_on_disk": len(_index.pdf_catalog),
        "teaching_value": dict(sorted(tv_dist.items())),
        "element_type": dict(sorted(et_dist.items())),
        "per_grade": {str(k): v for k, v in sorted(grade_dist.items())},
    }


@router.post("/cleanup")
async def cleanup_images(body: CleanupRequest):
    """Delete image PNG files from disk and remove from indexes."""
    await _index.ensure_loaded()

    deleted = []
    not_found = []

    for image_id in body.image_ids:
        rec = _index.records.get(image_id)
        if not rec:
            not_found.append(image_id)
            continue

        # Delete PNG file if it exists (with path containment check)
        img_path = rec.get("image_path", "")
        if img_path:
            full_path = (PROJECT_ROOT / img_path).resolve()
            data_root = (PROJECT_ROOT / "data").resolve()
            # Prevent arbitrary file deletion — must stay within data/
            if not full_path.is_relative_to(data_root):
                not_found.append(image_id)
                continue
            if full_path.exists():
                full_path.unlink()

        # Remove from in-memory index
        del _index.records[image_id]

        # Remove from by_pdf_page index
        stem = rec.get("pdf_stem", "")
        page = rec.get("page")
        if stem and page is not None:
            page_list = _index.by_pdf_page.get(stem, {}).get(page, [])
            _index.by_pdf_page[stem][page] = [
                r for r in page_list if r.get("image_id") != image_id
            ]

        deleted.append(image_id)

    # Also remove from per-book JSONLs
    if deleted:
        deleted_set = set(deleted)
        await asyncio.to_thread(_remove_from_book_jsonls, deleted_set)
        await _rewrite_annotations_jsonl()

    return {
        "status": "ok",
        "deleted_count": len(deleted),
        "not_found": not_found,
    }


def _remove_from_book_jsonls(deleted_ids: set[str]):
    """Remove entries from per-book structural JSONLs."""
    for jsonl_file in IMAGES_DIR.rglob("*-images.jsonl"):
        lines = []
        changed = False
        with open(jsonl_file) as f:
            for line in f:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                rec = json.loads(line_stripped)
                if rec.get("image_id") in deleted_ids:
                    changed = True
                    continue
                lines.append(line_stripped)
        if changed:
            with open(jsonl_file, "w") as f:
                for l in lines:
                    f.write(l + "\n")


@router.post("/reload")
async def reload_index():
    """Force reload all data from disk."""
    _index.reload()
    _page_cache.clear()
    await _pdf_pool.clear()
    await _index.ensure_loaded()
    return {
        "status": "ok",
        "total_records": len(_index.records),
        "pdfs_on_disk": len(_index.pdf_catalog),
    }
