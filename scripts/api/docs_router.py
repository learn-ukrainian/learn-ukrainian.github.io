"""Documentation artifacts API router (#1814).

Mounted at /artifacts in main.py.

Serves static documentation (HTML, MD, assets) and directory listings
from approved roots.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse

try:
    from path_safety import safe_join  # scripts/ on sys.path
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import

from .config import DASHBOARDS_DIR, PROJECT_ROOT

router = APIRouter(tags=["docs"])

# Approved roots for documentation artifacts.
#
# Maintenance note: this is a whitelist by design — adding a new docs/<dir>
# does NOT auto-surface its HTML artifacts in /api/artifacts/html. When you
# create a new top-level docs subdirectory that ships HTML reports, add it
# here AND bump the count assertion in
# tests/test_docs_router.py::test_docs_router_root_index_lists_allowed_roots.
# Explicit excludes (not added on purpose): docs/archive/ (literal scratch),
# docs/resources/podcasts/raw/ (raw scrapes — not curated reports).
ALLOWED_ROOTS = {
    "audit": PROJECT_ROOT / "audit",
    "docs/session-state": PROJECT_ROOT / "docs" / "session-state",
    "docs/handoffs": PROJECT_ROOT / "docs" / "handoffs",
    "docs/reports": PROJECT_ROOT / "docs" / "reports",
    "docs/architecture": PROJECT_ROOT / "docs" / "architecture",
    "docs/best-practices": PROJECT_ROOT / "docs" / "best-practices",
    "docs/decisions": PROJECT_ROOT / "docs" / "decisions",
    "docs/references/external": PROJECT_ROOT / "docs" / "references" / "external",
    "docs/proposals": PROJECT_ROOT / "docs" / "proposals",
    "docs/poc": PROJECT_ROOT / "docs" / "poc",
}

_ALLOWED_EXT = {".html", ".md", ".txt", ".json", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".pdf"}
_MIME_TYPES = {
    ".html": "text/html",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}


def _iso_from_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat().replace("+00:00", "Z")


def _split_csv_numbers(value: str | None) -> list[int]:
    items: list[int] = []
    for raw in (value or "").split(","):
        raw = raw.strip().lstrip("#")
        if raw.isdigit():
            items.append(int(raw))
    return items


def _split_csv_strings(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


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


def _is_hidden_path(remainder: str) -> bool:
    return any(part.startswith(".") for part in Path(remainder).parts)


def _assert_under_root(full_path: Path, root_path: Path) -> None:
    # codeql[py/path-injection] -- this IS the path-traversal validator; full_path
    # has already been validated by safe_join (commonpath) upstream. See #1860.
    try:
        full_path.resolve().relative_to(root_path.resolve())
    except ValueError as e:
        raise HTTPException(status_code=403, detail="Path traversal not allowed") from e


def _directory_listing(path: str, root_key: str, root_path: Path, remainder: str) -> dict:
    full_path = safe_join(root_path, remainder) if remainder else root_path.resolve()
    _assert_under_root(full_path, root_path)
    items = []
    for entry in sorted(full_path.iterdir()):
        if entry.name.startswith("."):
            continue
        _assert_under_root(entry, root_path)
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


def _artifact_url_for(root_key: str, file_path: Path) -> str:
    relative = file_path.relative_to(ALLOWED_ROOTS[root_key]).as_posix()
    return f"/artifacts/{root_key}/{relative}"


def _artifact_path_for(file_path: Path) -> str:
    return file_path.relative_to(PROJECT_ROOT).as_posix()


def collect_html_artifacts(
    *,
    class_filter: str | None = None,
    date_from: str | None = None,
    status: str | None = None,
    author: str | None = None,
) -> dict:
    """Return all HTML report artifacts under approved documentation roots."""
    artifacts = []
    for root_key, root_path in ALLOWED_ROOTS.items():
        if not root_path.exists():
            continue
        for file_path in sorted(root_path.rglob("*.html")):
            rel_parts = file_path.relative_to(root_path).parts
            if any(part.startswith(".") for part in rel_parts):
                continue
            _assert_under_root(file_path, root_path)
            meta = _extract_html_meta(file_path)
            report_class = meta.get("class") or "document"
            report_status = meta.get("status") or "unknown"
            report_date = meta.get("date") or _iso_from_mtime(file_path)[:10]
            report_author = meta.get("author") or ""
            if class_filter and report_class != class_filter:
                continue
            if status and report_status != status:
                continue
            if author and report_author != author:
                continue
            if date_from and report_date < date_from:
                continue
            artifacts.append(
                {
                    "path": _artifact_path_for(file_path),
                    "url": _artifact_url_for(root_key, file_path),
                    "class": report_class,
                    "date": report_date,
                    "status": report_status,
                    "title": meta.get("title") or file_path.stem,
                    "kpi_summary": meta.get("kpi-summary") or "",
                    "related_issues": _split_csv_numbers(meta.get("related-issues")),
                    "related_prs": _split_csv_numbers(meta.get("related-prs")),
                    "agents": _split_csv_strings(meta.get("agents")),
                    "author": report_author,
                    "size_bytes": file_path.stat().st_size,
                    "modified_at": _iso_from_mtime(file_path),
                }
            )
    artifacts.sort(key=lambda item: (item["date"], item["modified_at"], item["path"]), reverse=True)
    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "total": len(artifacts),
        "artifacts": artifacts,
    }


@router.get("/")
async def list_roots(request: Request, format: str | None = Query(None, pattern="^(json)$")):
    """List all approved documentation roots."""
    if request.url.path.startswith("/artifacts") and format != "json":
        return FileResponse(DASHBOARDS_DIR / "artifacts.html", media_type="text/html")
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
async def serve_artifact(
    path: str,
    request: Request,
    format: str | None = Query(None, pattern="^(json)$"),
):
    """Serve a documentation artifact or list a directory."""
    if not path:
        return await list_roots(request, format)

    info = _get_root_info(path)
    if not info:
        raise HTTPException(status_code=403, detail="Path not under an approved documentation root")

    root_key, root_path, remainder = info
    if _is_hidden_path(remainder):
        raise HTTPException(status_code=403, detail="Hidden files are not served as documentation artifacts")
    try:
        full_path = safe_join(root_path, remainder) if remainder else root_path.resolve()
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    _assert_under_root(full_path, root_path)

    # codeql[py/path-injection] -- full_path validated via safe_join + _assert_under_root above. See #1860.
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")

    # codeql[py/path-injection] -- full_path validated via safe_join + _assert_under_root above. See #1860.
    if full_path.is_dir():
        if request.url.path.startswith("/artifacts") and format != "json":
            return FileResponse(DASHBOARDS_DIR / "artifacts.html", media_type="text/html")
        return _directory_listing(path, root_key, root_path, remainder)

    # File serving
    if full_path.suffix.lower() not in _ALLOWED_EXT:
        raise HTTPException(
            status_code=403,
            detail=f"File extension {full_path.suffix} not allowed for documentation artifacts",
        )

    # codeql[py/path-injection] -- full_path validated via safe_join + _assert_under_root + extension allowlist above. See #1860.
    return FileResponse(
        full_path,
        media_type=_MIME_TYPES.get(full_path.suffix.lower(), "application/octet-stream"),
        headers={"Cache-Control": "max-age=300, must-revalidate"},
    )
