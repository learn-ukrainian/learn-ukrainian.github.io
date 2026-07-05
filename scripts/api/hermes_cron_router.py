"""FastAPI router for serving the latest nightly Hermes audit cron results."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from .config import PROJECT_ROOT

router = APIRouter(tags=["hermes-cron"])


@router.get("/latest")
async def get_latest(format: str | None = Query(None, description="Output format: 'json' or 'markdown'")):
    """Get the latest nightly audit report."""
    cron_dir = PROJECT_ROOT / "batch_state" / "hermes_cron"

    if format == "markdown":
        md_file = cron_dir / "latest.md"
        if not md_file.exists():
            raise HTTPException(status_code=404, detail="Latest nightly audit markdown report not found")
        try:
            content = md_file.read_text(encoding="utf-8")
            return PlainTextResponse(
                content=content,
                media_type="text/markdown; charset=utf-8",
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to read latest nightly audit markdown report: {e}"
            ) from e
    else:
        # Default is JSON
        json_file = cron_dir / "latest.json"
        if not json_file.exists():
            raise HTTPException(status_code=404, detail="Latest nightly audit json report not found")
        try:
            return json.loads(json_file.read_text(encoding="utf-8"))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to parse latest nightly audit json report: {e}"
            ) from e
