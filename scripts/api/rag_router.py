"""RAG search and image browse endpoints.

Mounts at /api/rag/ — wraps scripts/wiki/sources_db.py functions.
This router is FTS5-backed (SQLite), not vector-backed.
"""

import re
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from .config import DASHBOARDS_DIR, PROJECT_ROOT, TEXTBOOK_IMAGES_DIR

# Ensure scripts/ is importable
_scripts_dir = str(PROJECT_ROOT / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from wiki import sources_db as sdb

router = APIRouter(tags=["rag"])

IMAGE_DIR = TEXTBOOK_IMAGES_DIR
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


# ── Search endpoints ──────────────────────────────────────────────


@router.get("/search_text")
async def search_text(
    q: str = Query(..., description="Search query in Ukrainian"),
    limit: int = Query(5, ge=1, le=20),
):
    """FTS5 search across textbooks."""
    keywords = {w for w in q.lower().split() if len(w) >= 3}
    if not keywords:
        return []
    try:
        return sdb.search_textbooks(keywords, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/search_literary")
async def search_literary(
    q: str = Query(..., description="Search query in Ukrainian"),
    limit: int = Query(5, ge=1, le=20),
):
    """FTS5 search across literary texts."""
    keywords = {w for w in q.lower().split() if len(w) >= 3}
    if not keywords:
        return []
    try:
        return sdb.search_literary(keywords, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/stats")
async def collection_stats():
    """Returns database table statistics."""
    try:
        return sdb.list_tables()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ── Browse images (disk scan) ───────────────────────────────────


@router.get("/browse_images")
async def browse_images(
    grade: str | None = Query(None, description="Grade directory name, e.g. grade-03"),
    sort: str = Query("size", description="Sort by: size, name, grade"),
    page: int = Query(0, ge=0),
    per_page: int = Query(100, ge=1, le=500),
    max_size: int | None = Query(None, description="Max file size in bytes"),
    min_size: int | None = Query(None, description="Min file size in bytes"),
):
    """Browse textbook images on disk with filtering and pagination."""
    if not IMAGE_DIR.exists():
        return {"images": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0, "grade_stats": {}}

    if grade:
        # Validate grade format to prevent path traversal
        if not re.match(r"^grade-\d{2}$", grade):
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid grade format: {grade}"},
            )
        search_dirs = [IMAGE_DIR / grade]
        if not search_dirs[0].exists():
            return JSONResponse(
                status_code=404,
                content={"error": f"Grade directory not found: {grade}"},
            )
    else:
        search_dirs = sorted(
            d for d in IMAGE_DIR.iterdir()
            if d.is_dir() and d.name.startswith("grade-")
        )

    images = []
    for d in search_dirs:
        for f in d.iterdir():
            if not f.is_file() or f.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
                continue
            size = f.stat().st_size
            if max_size and size > max_size:
                continue
            if min_size and size < min_size:
                continue
            images.append({
                "path": f"data/textbook_images/{d.name}/{f.name}",
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
    page_images = images[start:start + per_page]
    total_pages = max(1, (total + per_page - 1) // per_page)

    # Grade-level stats
    grade_stats = {}
    for d in sorted(IMAGE_DIR.iterdir()):
        if not d.is_dir() or not d.name.startswith("grade-"):
            continue
        all_imgs = [f for f in d.iterdir() if f.is_file() and f.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS]
        sizes = [f.stat().st_size for f in all_imgs]
        grade_stats[d.name] = {
            "total": len(all_imgs),
            "small": sum(1 for s in sizes if s < 5000),
            "tiny": sum(1 for s in sizes if s < 2000),
        }

    return {
        "images": page_images,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "grade_stats": grade_stats,
    }
