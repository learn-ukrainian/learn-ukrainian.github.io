"""Site API router — public-facing Starlight site health + deploys.

Mounted at /api/site in main.py.

Endpoints:
    GET /api/site/health        Reachability + freshness of the public site
    GET /api/site/deployments   Recent GitHub Pages deployments

Boundary vs ``artifacts_router.py``: artifacts is about INTERNAL
completeness (MDX on disk, audit pass, final review approved). Site is
about what actually shipped — can users load it, when was the last
deploy, does a canary slug still render. Codex flagged that mixing
these muddies the contract; they stay in separate files.

Nothing in this router is a hard dependency. If ``gh`` isn't available
or the public URL is unreachable, the response degrades gracefully —
each field carries a string ``error`` rather than returning 500. An
agent can still make a decision from the populated fields.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Query

from .config import PROJECT_ROOT

router = APIRouter(tags=["site"])

# Defaults match the current deployment (``learn-ukrainian.github.io``).
# An override via env allows preview deployments / local dry-runs.
PUBLIC_SITE_URL = os.environ.get(
    "LEARN_UK_SITE_URL",
    "https://learn-ukrainian.github.io/",
)
# Canary slugs — lightweight existence checks. If these start 404'ing
# the deploy is broken for more than just the homepage. Keep the list
# short; each entry is an HTTP HEAD.
CANARY_PATHS: tuple[str, ...] = (
    "/",
    "/a1/",
)

STARLIGHT_DIR = PROJECT_ROOT / "starlight"
ASTRO_OUTPUT_DIR = STARLIGHT_DIR / "dist"


# ---------------------------------------------------------------------
# Low-level helpers — HEAD + subprocess with a short, hard timeout.
# ---------------------------------------------------------------------


def _head(url: str, timeout_s: float = 2.0) -> dict[str, Any]:
    """HTTP HEAD with a short timeout. Never raises; returns a status dict."""
    req = urllib.request.Request(url, method="HEAD")
    start = datetime.now(UTC)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return {
                "url": url,
                "status": resp.status,
                "elapsed_ms": round(
                    (datetime.now(UTC) - start).total_seconds() * 1000, 1
                ),
            }
    except urllib.error.HTTPError as exc:
        return {"url": url, "status": exc.code, "error": f"HTTPError: {exc}"}
    except urllib.error.URLError as exc:
        return {"url": url, "status": None, "error": f"URLError: {exc}"}
    except Exception as exc:  # pragma: no cover — defensive
        return {"url": url, "status": None, "error": f"{type(exc).__name__}: {exc}"}


def _run(cmd: list[str], timeout_s: float = 3.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


# ---------------------------------------------------------------------
# /api/site/health
# ---------------------------------------------------------------------


def _last_astro_build() -> dict[str, Any]:
    """Introspect ``starlight/dist`` to see when the site was last built."""
    if not ASTRO_OUTPUT_DIR.is_dir():
        return {"built": False, "reason": "starlight/dist missing — site never built locally"}
    try:
        latest = max(
            (p.stat().st_mtime for p in ASTRO_OUTPUT_DIR.rglob("*") if p.is_file()),
            default=None,
        )
    except OSError as exc:
        return {"built": False, "error": str(exc)}
    if latest is None:
        return {"built": False, "reason": "starlight/dist empty"}
    return {
        "built": True,
        "last_build_at": datetime.fromtimestamp(latest, tz=UTC).isoformat().replace("+00:00", "Z"),
        "age_seconds": int(datetime.now(UTC).timestamp() - latest),
    }


def _last_deploy_commit() -> dict[str, Any]:
    """Last commit SHA on the deploy branch (``gh-pages`` by default).

    Uses local git refs if present, which is fast. Falls back to a
    short ``git ls-remote`` if the ref isn't cached locally. Any
    failure → ``error`` string, not a 500.
    """
    for ref in ("refs/heads/gh-pages", "refs/remotes/origin/gh-pages"):
        proc = _run(["git", "rev-parse", "--verify", "--short=9", ref])
        if proc.returncode == 0 and proc.stdout.strip():
            sha = proc.stdout.strip()
            ts_proc = _run([
                "git", "show", "-s", "--format=%cI", sha,
            ])
            ts = ts_proc.stdout.strip() if ts_proc.returncode == 0 else None
            return {"sha": sha, "committed_at": ts, "source": ref}

    # Last resort: ask the remote.
    proc = _run(["git", "ls-remote", "origin", "gh-pages"], timeout_s=5.0)
    if proc.returncode == 0 and proc.stdout:
        sha = proc.stdout.split()[0][:9]
        return {"sha": sha, "committed_at": None, "source": "remote ls-remote"}
    return {"error": (proc.stderr or "gh-pages ref not resolvable").strip()}


def _sitemap_freshness() -> dict[str, Any]:
    sitemap = ASTRO_OUTPUT_DIR / "sitemap-index.xml"
    if not sitemap.is_file():
        sitemap = ASTRO_OUTPUT_DIR / "sitemap-0.xml"
    if not sitemap.is_file():
        return {"exists": False}
    mtime = sitemap.stat().st_mtime
    return {
        "exists": True,
        "path": str(sitemap.relative_to(PROJECT_ROOT)),
        "last_modified": datetime.fromtimestamp(mtime, tz=UTC).isoformat().replace("+00:00", "Z"),
        "age_seconds": int(datetime.now(UTC).timestamp() - mtime),
    }


def _canary_probes(base_url: str) -> list[dict[str, Any]]:
    base = base_url.rstrip("/")
    return [_head(base + path) for path in CANARY_PATHS]


def _compute_site_health() -> dict[str, Any]:
    canaries = _canary_probes(PUBLIC_SITE_URL)
    reachable = any(c.get("status") == 200 for c in canaries)
    return {
        "public_url": PUBLIC_SITE_URL,
        "reachable": reachable,
        "canaries": canaries,
        "last_astro_build": _last_astro_build(),
        "last_deploy_commit": _last_deploy_commit(),
        "sitemap": _sitemap_freshness(),
        "checked_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


@router.get("/health")
async def site_health():
    """Aggregate public-site health — reachability, freshness, canaries."""
    return await asyncio.to_thread(_compute_site_health)


# ---------------------------------------------------------------------
# /api/site/deployments
# ---------------------------------------------------------------------


def _recent_deployments(limit: int) -> dict[str, Any]:
    """Recent GitHub Actions ``pages-build-deployment`` runs via ``gh``.

    Falls back to an empty list + error string if ``gh`` isn't
    available or the caller lacks auth.
    """
    proc = _run(
        [
            "gh", "run", "list",
            "--workflow", "pages-build-deployment",
            "--limit", str(limit),
            "--json", "databaseId,conclusion,displayTitle,createdAt,updatedAt,headSha,event,status",
        ],
        timeout_s=5.0,
    )
    if proc.returncode != 0:
        return {
            "runs": [],
            "error": (
                proc.stderr.strip()
                or "gh run list failed (is gh installed + authenticated?)"
            ),
        }
    try:
        runs = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        return {"runs": [], "error": f"invalid gh json: {exc}"}
    return {"runs": runs}


@router.get("/deployments")
async def site_deployments(
    limit: int = Query(5, ge=1, le=20, description="Max runs to return."),
):
    """Recent GH Pages build+deploy workflow runs."""
    return await asyncio.to_thread(_recent_deployments, limit)
