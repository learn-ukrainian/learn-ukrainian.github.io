"""Product routes that used to sit on the machinery core router: ``/api/config`` and ``/images/*``.

``/api/config`` returns the curriculum levels and the pipeline phase labels.
``/images/{path}`` serves textbook images from the product image root. Both
are mounted ahead of the machinery core router, so the static catch-all
still comes last (Monitor split, C-4687).
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from scripts.api.monitor_context import MonitorContext, get_ctx

from .config import LEVELS
from .context import product_roots
from .curriculum_state import load_phase_labels

try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.project_api package import (production)

router = APIRouter()


@router.get("/api/config")
async def get_config(request: Request, ctx: MonitorContext = Depends(get_ctx)):
    # Pipeline phase config from product data (scripts/curriculum/phase_labels.v1.json)
    try:
        phases, phase_labels = load_phase_labels()
        pipeline_info = {"phases": phases, "phase_labels": phase_labels}
    except (OSError, ValueError):
        pipeline_info = {}
    return {"levels": LEVELS, "api_version": request.app.version, "pipeline": pipeline_info}


# ==================== IMAGE SERVING ====================

_ALLOWED_IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
_MIME_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _safe_join(base: Path, *parts: str | Path) -> Path | None:
    try:
        return cast(Path, safe_join(base, *parts))
    except ValueError:
        return None


@router.get("/images/{path:path}")
async def serve_image(path: str, ctx: MonitorContext = Depends(get_ctx)):
    """Serve textbook images with caching. Path relative to data/textbook_images/."""
    image_dir = product_roots(ctx).images_dir
    file_path = _safe_join(image_dir, path)
    if file_path is None:
        raise HTTPException(status_code=403, detail="Invalid image path")
    if file_path.suffix.lower() not in _ALLOWED_IMG_EXT:
        raise HTTPException(status_code=403, detail="Forbidden file type")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404)
    # Prevent path traversal
    try:
        file_path.resolve().relative_to(image_dir.resolve())
    except ValueError as e:
        raise HTTPException(status_code=403, detail="Path traversal not allowed") from e
    return FileResponse(
        file_path,
        media_type=_MIME_TYPES.get(file_path.suffix.lower(), "application/octet-stream"),
        headers={"Cache-Control": "max-age=3600"},
    )
