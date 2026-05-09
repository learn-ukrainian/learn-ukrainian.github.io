"""Documentation artifacts API router (#1814).

Mounted at /artifacts in main.py.

Serves static documentation (HTML, MD, assets) and directory listings
from approved roots.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

try:
    from path_safety import safe_join  # scripts/ on sys.path
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import

from .config import PROJECT_ROOT

router = APIRouter(tags=["docs"])

# Approved roots for documentation artifacts.
ALLOWED_ROOTS = {
    "audit": PROJECT_ROOT / "audit",
    "docs/session-state": PROJECT_ROOT / "docs" / "session-state",
    "docs/handoffs": PROJECT_ROOT / "docs" / "handoffs",
    "docs/reports": PROJECT_ROOT / "docs" / "reports",
    "docs/architecture": PROJECT_ROOT / "docs" / "architecture",
    "docs/best-practices": PROJECT_ROOT / "docs" / "best-practices",
    "docs/decisions": PROJECT_ROOT / "docs" / "decisions",
    "docs/references/external": PROJECT_ROOT / "docs" / "references" / "external",
}

_ALLOWED_EXT = {".html", ".md", ".txt", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".pdf"}
_MIME_TYPES = {
    ".html": "text/html",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}


def _extract_html_meta(path: Path) -> dict[str, str]:
    """Extract <meta name="report-*" content="..."> tags from HTML."""
    meta = {}
    if path.suffix.lower() != ".html" or not path.is_file():
        return meta
    try:
        # Read the head of the file (first 8KB is usually enough for meta tags)
        with open(path, encoding="utf-8", errors="replace") as f:
            head = f.read(8192)
        # Match <meta name="report-class" content="handoff" />
        # and variants with different spacing/quotes
        matches = re.finditer(
            r'<meta\s+name="report-([^"]+)"\s+content="([^"]*)"\s*/?>', head, re.IGNORECASE
        )
        for m in matches:
            meta[m.group(1)] = m.group(2)
    except Exception:
        pass
    return meta


def _get_root_info(path: str) -> tuple[str, Path, str] | None:
    """Find the matching root for a given path.

    Returns (root_key, root_path, relative_remainder) or None.
    """
    # Sort by length descending to match most specific root first
    for root_key in sorted(ALLOWED_ROOTS.keys(), key=len, reverse=True):
        if path == root_key or path.startswith(f"{root_key}/"):
            remainder = path[len(root_key) :].lstrip("/")
            return root_key, ALLOWED_ROOTS[root_key], remainder
    return None


@router.get("/")
async def list_roots():
    """List all approved documentation roots."""
    return {
        "roots": [
            {
                "id": k,
                "path": str(v.relative_to(PROJECT_ROOT)),
                "exists": v.exists(),
            }
            for k, v in ALLOWED_ROOTS.items()
        ]
    }


@router.get("/{path:path}")
async def serve_artifact(path: str):
    """Serve a documentation artifact or list a directory."""
    if not path:
        return await list_roots()

    info = _get_root_info(path)
    if not info:
        raise HTTPException(status_code=403, detail="Path not under an approved documentation root")

    root_key, root_path, remainder = info
    try:
        full_path = safe_join(root_path, remainder) if remainder else root_path.resolve()
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")

    if full_path.is_dir():
        # Directory listing
        items = []
        for entry in sorted(full_path.iterdir()):
            if entry.name.startswith("."):
                continue
            stat = entry.stat()
            item = {
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size": stat.st_size if not entry.is_dir() else None,
                "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": f"{path}/{entry.name}".replace("//", "/"),
            }
            if not entry.is_dir() and entry.suffix.lower() == ".html":
                item["meta"] = _extract_html_meta(entry)
            items.append(item)
        return {
            "root": root_key,
            "relative_path": remainder,
            "items_count": len(items),
            "items": items,
        }

    # File serving
    if full_path.suffix.lower() not in _ALLOWED_EXT:
        raise HTTPException(
            status_code=403,
            detail=f"File extension {full_path.suffix} not allowed for documentation artifacts",
        )

    return FileResponse(
        full_path,
        media_type=_MIME_TYPES.get(full_path.suffix.lower(), "application/octet-stream"),
        headers={"Cache-Control": "max-age=300"},
    )
