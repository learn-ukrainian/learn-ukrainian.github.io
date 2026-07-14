"""Separate local persistence for advisory judged LLM-QG shadow runs.

This store is intentionally disjoint from ``llm_qg_store``: Monitor and build
logic treat canonical Tier-2 evidence as production gate state, while judged
shadow results remain outcome-only evidence until an explicit cutover.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from scripts.api.config import PROJECT_ROOT
from scripts.api.resilience import connect_sqlite

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "telemetry" / "llm_qg_shadow.db"
SCHEMA_VERSION = "llm_qg_shadow_store.v1"


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def init_db(path: Path | None = None) -> Path:
    """Create the isolated, versioned shadow persistence schema."""

    resolved = path or DEFAULT_DB_PATH
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect_sqlite(str(resolved))) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS llm_qg_shadow_runs (
                shadow_run_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                tier2_run_id TEXT NOT NULL,
                level TEXT NOT NULL,
                slug TEXT NOT NULL,
                content_sha TEXT NOT NULL,
                artifact_path TEXT NOT NULL,
                artifact_sha256 TEXT NOT NULL,
                layerb_report_path TEXT NOT NULL,
                writer_family TEXT NOT NULL,
                qg_reviewer_family TEXT NOT NULL,
                tau REAL NOT NULL,
                summary_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_llm_qg_shadow_content
                ON llm_qg_shadow_runs(level, slug, content_sha, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_llm_qg_shadow_tier2
                ON llm_qg_shadow_runs(tier2_run_id);

            CREATE TABLE IF NOT EXISTS llm_qg_shadow_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shadow_run_id TEXT NOT NULL,
                grounding_key TEXT,
                fact_check_id TEXT,
                final_decision TEXT,
                payload_json TEXT NOT NULL,
                FOREIGN KEY(shadow_run_id) REFERENCES llm_qg_shadow_runs(shadow_run_id)
                    ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_llm_qg_shadow_findings_run
                ON llm_qg_shadow_findings(shadow_run_id, id);
            """
        )
        conn.commit()
    return resolved


def record_shadow_run(
    *,
    tier2_run_id: str,
    level: str,
    slug: str,
    content_sha: str,
    artifact_path: Path,
    artifact_sha256: str,
    layerb_report_path: Path,
    writer_family: str,
    qg_reviewer_family: str,
    tau: float,
    summary: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
    path: Path | None = None,
    shadow_run_id: str | None = None,
) -> str:
    """Persist advisory outcomes without writing canonical ``llm_qg_runs``."""

    resolved = init_db(path)
    run_id = shadow_run_id or f"llm-qg-shadow-{uuid4().hex}"
    with closing(connect_sqlite(str(resolved))) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            INSERT INTO llm_qg_shadow_runs (
                shadow_run_id, created_at, schema_version, tier2_run_id,
                level, slug, content_sha, artifact_path, artifact_sha256,
                layerb_report_path, writer_family, qg_reviewer_family, tau,
                summary_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                _now_z(),
                SCHEMA_VERSION,
                tier2_run_id,
                level,
                slug,
                content_sha,
                str(artifact_path),
                artifact_sha256,
                str(layerb_report_path),
                writer_family,
                qg_reviewer_family,
                tau,
                _json(summary),
            ),
        )
        conn.executemany(
            """
            INSERT INTO llm_qg_shadow_findings (
                shadow_run_id, grounding_key, fact_check_id, final_decision, payload_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(row.get("grounding_key") or "") or None,
                    str(row.get("fact_check_id") or "") or None,
                    str(row.get("final_decision") or "") or None,
                    _json(dict(row)),
                )
                for row in findings
            ],
        )
        conn.commit()
    return run_id
