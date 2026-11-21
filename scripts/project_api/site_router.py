"""Site API router — public-facing site deploys.

Mounted at /api/site in main.py.

Endpoints:
    GET /api/site/deployments   Recent GitHub Pages deployments

Boundary vs ``artifacts_router.py``: artifacts is about INTERNAL
completeness (MDX on disk, audit pass, final review approved). Site is
about what actually shipped: the recent GitHub Pages deployments.
Codex flagged that mixing these muddies the contract; they stay in
separate files.

Nothing in this router is a hard dependency. If ``gh`` isn't available,
the response degrades gracefully — it carries a string ``error`` rather
than returning 500.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, cast

from fastapi import APIRouter, Depends, Query
from lu_machinery.api import config as api_config
from lu_machinery.api.monitor_context import MonitorContext, get_ctx
from lu_machinery.common import github_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["site"])

# ---------------------------------------------------------------------
# Low-level helpers — HEAD + subprocess with a short, hard timeout.
# ---------------------------------------------------------------------


def _run_cwd(cmd: list[str], ctx: MonitorContext | None = None) -> Path:
    """Resolve the subprocess cwd without constructing a production context.

    ``production_context()`` itself runs git (session-streams path
    resolution). Unit tests that stub ``subprocess.run`` must still be
    able to call ``_run`` directly.
    """
    if isinstance(ctx, MonitorContext):
        return (
            ctx.roots.live_repo_root
            if cmd and cmd[0] == "git"
            else ctx.roots.project_root
        )
    return (
        Path(api_config.LIVE_REPO_ROOT)
        if cmd and cmd[0] == "git"
        else Path(api_config.PROJECT_ROOT)
    )


def _run(
    cmd: list[str],
    timeout_s: float = 3.0,
    ctx: MonitorContext | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with a bounded timeout. Never raises.

    The file contract says "every field degrades to an error string,
    not a 500". ``subprocess.run`` can raise two unrelated exceptions
    that would otherwise break that contract:

    - ``subprocess.TimeoutExpired`` when the command wall-clocks past
      ``timeout_s`` (common with a hung ``git ls-remote`` to an
      unreachable origin or a wedged ``gh run list``).
    - ``FileNotFoundError`` when the binary isn't on ``PATH`` — e.g.
      ``gh`` on a machine where it hasn't been installed.

    We catch both (and any other ``OSError``) and return a
    ``CompletedProcess`` with a non-zero ``returncode`` and a
    descriptive ``stderr``. Downstream collectors already branch on
    ``returncode != 0`` to surface the error in their own field, so
    this degrades naturally.

    ``AssertionError`` is included so an isolated OPSEC fixture's
    process-wide ``subprocess.run`` deny degrades the same way — the
    route keeps its documented error-string envelope without a
    router-local ``_run`` monkeypatch seam (#7269 step 12d).

    Both Codex and Gemini flagged this as the single BLOCKER in the
    final pre-PR review (#1309) — fixing it here means the three
    site-health helpers all inherit the safety net for free.
    """
    cwd = _run_cwd(cmd, ctx)
    try:
        return cast("subprocess.CompletedProcess[str]", github_client.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        ))
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,  # conventional shell exit for timeout
            stdout="",
            stderr=f"TimeoutExpired after {exc.timeout}s",
        )
    except (FileNotFoundError, PermissionError, OSError, AssertionError) as exc:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=127,  # conventional "command not found"
            stdout="",
            stderr=f"{type(exc).__name__}: {exc}",
        )


# ---------------------------------------------------------------------
# /api/site/deployments
# ---------------------------------------------------------------------


def _recent_deployments(limit: int, ctx: MonitorContext | None = None) -> dict[str, Any]:
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
        ctx=ctx,
    )
    if proc.returncode != 0:
        logger.warning("gh run list failed (exit %d): %r", proc.returncode, proc.stderr)
        return {"runs": [], "error": "Could not load recent deployments."}
    try:
        runs = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        logger.exception("gh run list returned invalid JSON")
        return {"runs": [], "error": "Could not load recent deployments."}
    return {"runs": runs}


@router.get("/deployments")
def site_deployments(
    limit: int = Query(5, ge=1, le=20, description="Max runs to return."),
    ctx: MonitorContext = Depends(get_ctx),
):
    """Recent GH Pages build+deploy workflow runs."""
    return _recent_deployments(limit, ctx)
