"""Documentation artifacts API router (#1814).

Mounted at /artifacts and /files in main.py.

Serves static documentation (HTML, MD, assets) and directory listings
from approved roots.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse

try:
    from path_safety import safe_join  # scripts/ on sys.path
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import

from .monitor_context import MonitorContext, get_ctx, production_context

logger = logging.getLogger(__name__)

router = APIRouter(tags=["docs"])


def _resolve_context(ctx: MonitorContext | None = None) -> MonitorContext:
    if isinstance(ctx, MonitorContext):
        return ctx
    return production_context()


# Path prefixes (relative to project_root) to exclude from discovery.
DISCOVERY_EXCLUDES = ("docs/archive", "docs/resources/podcasts/raw")


def build_allowed_roots(project_root: Path) -> dict[str, Path]:
    """Return approved documentation root directories under project_root."""
    resolved_root = Path(project_root)
    return {
        "audit": resolved_root / "audit",
        "session-state": resolved_root / "docs" / "session-state",
        "handoffs": resolved_root / "docs" / "handoffs",
        "reports": resolved_root / "docs" / "reports",
        "architecture": resolved_root / "docs" / "architecture",
        "best-practices": resolved_root / "docs" / "best-practices",
        "decisions": resolved_root / "docs" / "decisions",
        "references": resolved_root / "docs" / "references" / "external",
        "proposals": resolved_root / "docs" / "proposals",
        "poc": resolved_root / "docs" / "poc",
    }


def build_effective_roots(project_root: Path) -> dict[str, Path]:
    """Build effective roots as allowed roots union discovered docs/ dirs."""
    resolved_root = Path(project_root)
    effective = build_allowed_roots(resolved_root)
    docs_dir = resolved_root / "docs"
    if docs_dir.is_dir():
        for entry in sorted(docs_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            root_key = f"docs/{entry.name}"
            # Skip if this path prefix is excluded
            if any(root_key.startswith(excl) for excl in DISCOVERY_EXCLUDES):
                continue
            effective.setdefault(root_key, entry)
    return effective


_ALLOWED_EXT = {
    ".html", ".md", ".txt", ".json", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".pdf",
    ".css", ".js", ".gif", ".woff", ".woff2"
}
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
    ".css": "text/css",
    ".js": "application/javascript",
    ".gif": "image/gif",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
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


def _extract_md_frontmatter(path: Path) -> dict[str, str]:
    """Extract YAML frontmatter from MD files.

    Parses the leading YAML block delimited by ``---`` / ``---``.
    Falls back to first H1 as title if no frontmatter ``title`` key.
    Limits reads to 8KB head. Returns empty dict on any error.
    """
    meta: dict[str, str] = {}
    if path.suffix.lower() != ".md" or not path.is_file():
        return meta
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            head = f.read(8192)
    except Exception:
        return meta

    if not head.startswith("---"):
        # No frontmatter — try H1 as title fallback
        for line in head.split("\n"):
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                meta["title"] = stripped[2:].strip()
                break
        return meta

    # Find closing ---
    end_idx = head.find("\n---", 3)
    if end_idx == -1:
        return meta

    yaml_str = head[4:end_idx]  # Skip opening "---\n"
    try:
        data = yaml.safe_load(yaml_str)
        if isinstance(data, dict):
            for key, value in data.items():
                if value is not None:
                    meta[str(key)] = str(value)
    except Exception:
        logger.debug("Malformed YAML frontmatter in %s, skipping metadata", path)

    # Title: first H1 if no title in frontmatter
    if "title" not in meta:
        body_start = head[end_idx + 4:]  # after closing ---\n
        for line in body_start.split("\n"):
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                meta["title"] = stripped[2:].strip()
                break

    return meta


def _get_root_info(path: str, effective_roots: Mapping[str, Path]) -> tuple[str, Path, str] | None:
    """Find the matching root for a given path.

    Returns (root_key, root_path, relative_remainder) or None.
    """
    # Sort by length descending to match most specific root first
    for root_key in sorted(effective_roots.keys(), key=len, reverse=True):
        if path == root_key or path.startswith(f"{root_key}/"):
            remainder = path[len(root_key):].lstrip("/")
            return root_key, effective_roots[root_key], remainder
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


def _relative_to_root(path: Path, root: Path) -> str:
    """Return a stable root-relative path across symlinked checkout roots."""
    return path.relative_to(root).as_posix()


def _directory_listing(path: str, root_key: str, root_path: Path, remainder: str) -> dict:
    full_path = safe_join(root_path, remainder) if remainder else safe_join(root_path)
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


def _artifact_url_for(root_key: str, file_path: Path, root_path: Path) -> str:
    relative = _relative_to_root(file_path, root_path)
    return f"/artifacts/{root_key}/{relative}"


def _artifact_path_for(file_path: Path, project_root: Path) -> str:
    return _relative_to_root(file_path, project_root)


def _find_artifact_root(file_path: Path, effective_roots: Mapping[str, Path], project_root: Path) -> str | None:
    """Find the effective_roots key that contains this file path.

    Returns the longest matching root_key, or None if no root covers it.
    """
    rel = _relative_to_root(file_path, project_root)
    # Sort by key length descending — longest (most specific) match wins
    for root_key in sorted(effective_roots.keys(), key=len, reverse=True):
        if rel == root_key or rel.startswith(f"{root_key}/"):
            return root_key
    return None


def collect_artifacts(
    *,
    class_filter: str | None = None,
    date_from: str | None = None,
    status: str | None = None,
    author: str | None = None,
    types: tuple[str, ...] = ("html", "md"),
    ctx: MonitorContext | None = None,
) -> dict:
    """Return all HTML and MD artifacts under discovery roots.

    Walks discovery roots (docs/ + audit/) broadly. Skips
    DISCOVERY_EXCLUDES and dotfiles. Matches each file to an
    effective_roots entry for serving. Parses HTML <meta> tags
    and MD YAML frontmatter for metadata.

    Args:
        class_filter: Filter by artifact class.
        date_from: ISO date lower bound.
        status: Filter by status.
        author: Filter by author.
        types: Tuples of extensions to include (default: html, md).
        ctx: Application context providing filesystem roots.
    """
    resolved_ctx = _resolve_context(ctx)
    project_root = resolved_ctx.roots.project_root
    discovery_roots = (project_root / "docs", project_root / "audit")
    effective_roots = resolved_ctx.roots.effective_roots

    artifacts: list[dict] = []
    type_set = set(types)

    for discovery_root in discovery_roots:
        if not discovery_root.exists():
            continue
        for file_path in sorted(discovery_root.rglob("*")):
            if not file_path.is_file():
                continue

            # Skip dotfiles
            rel_to_project = Path(_relative_to_root(file_path, project_root))
            if any(part.startswith(".") for part in rel_to_project.parts):
                continue

            # Skip excluded paths
            rel_str = rel_to_project.as_posix()
            if any(rel_str == excl or rel_str.startswith(f"{excl}/") for excl in DISCOVERY_EXCLUDES):
                continue

            # Filter by type
            suffix = file_path.suffix.lower()
            if suffix == ".html":
                if "html" not in type_set:
                    continue
            elif suffix == ".md":
                if "md" not in type_set:
                    continue
            else:
                continue  # Only HTML and MD for now

            # Find the serving root for this file
            root_key = _find_artifact_root(file_path, effective_roots, project_root)
            if root_key is None:
                continue  # Not under any approved root

            _assert_under_root(file_path, effective_roots[root_key])

            # Extract metadata
            meta = _extract_html_meta(file_path) if suffix == ".html" else _extract_md_frontmatter(file_path)

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
                    "path": _artifact_path_for(file_path, project_root),
                    "url": _artifact_url_for(root_key, file_path, effective_roots[root_key]),
                    "class": report_class,
                    "date": report_date,
                    "status": report_status,
                    "title": meta.get("title") or file_path.stem,
                    "kpi_summary": meta.get("kpi_summary") or meta.get("kpi-summary") or "",
                    "related_issues": _split_csv_numbers(meta.get("related_issues") or meta.get("related-issues")),
                    "related_prs": _split_csv_numbers(meta.get("related_prs") or meta.get("related-prs")),
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


# Backward-compat alias — artifacts_router.py originally imported this name.
collect_html_artifacts = collect_artifacts


@router.get("/")
async def list_roots(
    request: Request,
    format: str | None = Query(None, pattern="^(json)$"),
    ctx: MonitorContext = Depends(get_ctx),
):
    """List all approved documentation roots."""
    resolved_ctx = _resolve_context(ctx)
    if request.url.path.startswith("/artifacts") and format != "json":
        return FileResponse(resolved_ctx.roots.dashboards_dir / "artifacts.html", media_type="text/html")
    return {
        "roots": [
            {
                "id": k,
                "path": _relative_to_root(v, resolved_ctx.roots.project_root),
                "exists": v.exists(),
            }
            for k, v in resolved_ctx.roots.effective_roots.items()
        ]
    }


@router.get("/{path:path}")
async def serve_artifact(
    path: str,
    request: Request,
    format: str | None = Query(None, pattern="^(json)$"),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Serve a documentation artifact or list a directory."""
    resolved_ctx = _resolve_context(ctx)
    if not path:
        return await list_roots(request, format, ctx=resolved_ctx)

    info = _get_root_info(path, resolved_ctx.roots.effective_roots)
    if not info:
        raise HTTPException(status_code=403, detail="Path not under an approved documentation root")

    root_key, root_path, remainder = info
    if _is_hidden_path(remainder):
        raise HTTPException(status_code=403, detail="Hidden files are not served as documentation artifacts")
    try:
        full_path = safe_join(root_path, remainder) if remainder else safe_join(root_path)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    _assert_under_root(full_path, root_path)

    # codeql[py/path-injection] -- full_path validated via safe_join + _assert_under_root above. See #1860.
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")

    # codeql[py/path-injection] -- full_path validated via safe_join + _assert_under_root above. See #1860.
    if full_path.is_dir():
        if request.url.path.startswith("/artifacts") and format != "json":
            return FileResponse(resolved_ctx.roots.dashboards_dir / "artifacts.html", media_type="text/html")
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
