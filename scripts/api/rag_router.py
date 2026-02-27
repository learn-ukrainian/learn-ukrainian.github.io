"""RAG search and image browse endpoints.

Mounts at /api/rag/ — wraps scripts/rag/query.py functions
and ports the browse logic from image_review_server.py.
"""

import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from .config import PROJECT_ROOT

# Ensure scripts/ is importable for rag.query
_scripts_dir = str(PROJECT_ROOT / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

router = APIRouter(tags=["rag"])

IMAGE_DIR = PROJECT_ROOT / "data" / "textbook_images"
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def _qdrant_available() -> bool:
    """Quick check if Qdrant is reachable."""
    try:
        from rag.query import get_client
        get_client().get_collections()
        return True
    except Exception:
        return False


def _qdrant_503():
    return JSONResponse(
        status_code=503,
        content={"error": "Qdrant is unavailable. Start it with: docker start qdrant"},
    )


# ── Search endpoints ──────────────────────────────────────────────


@router.get("/search_text")
async def search_text(
    q: str = Query(..., description="Search query in Ukrainian"),
    grade: Optional[int] = Query(None, description="Filter by grade (1-11)"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    trust_tier: Optional[int] = Query(None, description="Trust tier (1 or 2)"),
    limit: int = Query(5, ge=1, le=20),
):
    if not _qdrant_available():
        return _qdrant_503()
    from rag.query import search_text as _search_text
    return _search_text(q, grade=grade, subject=subject, trust_tier=trust_tier, limit=limit)


@router.get("/search_images")
async def search_images(
    q: str = Query(..., description="Image search query in Ukrainian"),
    grade: Optional[int] = Query(None, description="Filter by grade (1-11)"),
    limit: int = Query(5, ge=1, le=20),
):
    if not _qdrant_available():
        return _qdrant_503()
    from rag.query import search_images as _search_images
    return _search_images(q, grade=grade, limit=limit)


@router.get("/search_literary")
async def search_literary(
    q: str = Query(..., description="Search query in Ukrainian"),
    work: Optional[str] = Query(None, description="Filter by work title"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    period: Optional[str] = Query(None, description="Filter by language period"),
    limit: int = Query(5, ge=1, le=20),
):
    if not _qdrant_available():
        return _qdrant_503()
    from rag.query import search_literary as _search_literary
    return _search_literary(q, work=work, genre=genre, period=period, limit=limit)


@router.get("/stats")
async def collection_stats():
    if not _qdrant_available():
        return _qdrant_503()
    from rag.query import collection_stats as _collection_stats
    return _collection_stats()


# ── Browse images (disk scan, ported from image_review_server.py) ─


@router.get("/browse_images")
async def browse_images(
    grade: Optional[str] = Query(None, description="Grade directory name, e.g. grade-03"),
    sort: str = Query("size", description="Sort by: size, name, grade"),
    page: int = Query(0, ge=0),
    per_page: int = Query(100, ge=1, le=500),
    max_size: Optional[int] = Query(None, description="Max file size in bytes"),
    min_size: Optional[int] = Query(None, description="Min file size in bytes"),
):
    """Browse textbook images on disk with filtering and pagination."""
    if grade:
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
