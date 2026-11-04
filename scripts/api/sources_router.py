"""Sources browse/search endpoints backed by SQLite source helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import cast

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from .monitor_context import MonitorContext, get_ctx
from .state_helpers import monitor_surface

router = APIRouter(tags=["sources"])

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def _image_dir(ctx: MonitorContext) -> Path:
    if ctx.roots.images_dir is not None:
        return ctx.roots.images_dir
    return ctx.roots.project_root / "data" / "textbook_images"


@router.get("/search_text")
async def search_text(
    q: str = Query(..., description="Search query in Ukrainian"),
    grade: int | None = Query(None, description="Filter by grade (1-11)"),
    subject: str | None = Query(None, description="Filter by subject"),
    trust_tier: int | None = Query(None, description="Trust tier"),
    limit: int = Query(5, ge=1, le=20),
    ctx: MonitorContext = Depends(get_ctx),
):
    return monitor_surface.search_sources_text(
        ctx.stores.sources_db, q, grade=grade, subject=subject, trust_tier=trust_tier, limit=limit
    )


@router.get("/search_literary")
async def search_literary(
    q: str = Query(..., description="Search query"),
    work: str | None = Query(None, description="Filter by work"),
    genre: str | None = Query(None, description="Filter by genre"),
    period: str | None = Query(None, description="Filter by language period"),
    limit: int = Query(5, ge=1, le=20),
    ctx: MonitorContext = Depends(get_ctx),
):
    return monitor_surface.search_sources_literary(
        ctx.stores.sources_db, q, work=work, genre=genre, period=period, limit=limit
    )


@router.get("/stats")
async def collection_stats(ctx: MonitorContext = Depends(get_ctx)):
    return monitor_surface.sources_collection_stats(ctx.stores.sources_db)


@router.get("/browse_images")
async def browse_images(
    grade: str | None = Query(None, description="Grade directory name, e.g. grade-03"),
    sort: str = Query("size", description="Sort by: size, name, grade"),
    page: int = Query(0, ge=0),
    per_page: int = Query(100, ge=1, le=500),
    max_size: int | None = Query(None, description="Max file size in bytes"),
    min_size: int | None = Query(None, description="Min file size in bytes"),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Browse textbook images on disk with filtering and pagination."""
    image_dir = _image_dir(ctx)
    if grade:
        if not re.match(r"^grade-\d{2}$", grade):
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid grade format: {grade}"},
            )
        search_dirs = [image_dir / grade]
        if not search_dirs[0].exists():
            return JSONResponse(
                status_code=404,
                content={"error": f"Grade directory not found: {grade}"},
            )
    else:
        search_dirs = (
            sorted(d for d in image_dir.iterdir() if d.is_dir() and d.name.startswith("grade-"))
            if image_dir.exists()
            else []
        )

    images = []
    for directory in search_dirs:
        for file_path in directory.iterdir():
            if not file_path.is_file() or file_path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
                continue
            size = file_path.stat().st_size
            if max_size is not None and size > max_size:
                continue
            if min_size is not None and size < min_size:
                continue
            images.append(
                {
                    "path": f"data/textbook_images/{directory.name}/{file_path.name}",
                    "name": file_path.name,
                    "size": size,
                    "grade": directory.name,
                }
            )

    if sort == "size":
        images.sort(key=lambda item: cast(int, item["size"]))
    elif sort == "name":
        images.sort(key=lambda item: cast(str, item["name"]))
    elif sort == "grade":
        images.sort(key=lambda item: (item["grade"], item["name"]))

    total = len(images)
    start = page * per_page
    page_images = images[start : start + per_page]
    total_pages = max(1, (total + per_page - 1) // per_page)

    return {
        "images": page_images,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }
