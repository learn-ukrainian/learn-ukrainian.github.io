#!/usr/bin/env python3
"""Print or execute the Tier-2 disarm cache-invalidation checklist."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.api.resilience import connect_sqlite
from scripts.audit import llm_qg_store, qg_workflow

E0_SENTINEL_MODEL_ID = "llm-reviewer-disabled-until-4370"
SQL_INVALIDATE_GATE_VERSION = "DELETE FROM llm_qg_runs WHERE gate_version = ?"


def invalidate_gate_version_cache(*, db_path: Path | None, gate_version: str) -> int:
    """Delete current gate-version cache rows and cascade their findings."""
    resolved = llm_qg_store.init_db(db_path)
    with closing(connect_sqlite(str(resolved))) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.execute(SQL_INVALIDATE_GATE_VERSION, (gate_version,))
        conn.commit()
        return int(cursor.rowcount if cursor.rowcount is not None else 0)


def checklist(*, db_path: Path | None, gate_version: str) -> dict[str, Any]:
    resolved = llm_qg_store.db_path(db_path)
    return {
        "schema_version": "qg_tier2_disarm.v1",
        "e0_sentinel_model_id": E0_SENTINEL_MODEL_ID,
        "enable_llm_default": False,
        "gate_version": gate_version,
        "db_path": str(resolved),
        "cache_invalidation_sql": SQL_INVALIDATE_GATE_VERSION + ";",
        "cache_invalidation_command": (
            ".venv/bin/python scripts/audit/qg_tier2_disarm.py --execute "
            f"--gate-version {gate_version}"
        ),
        "steps": [
            "Restore qg_workflow.DEFAULT_REVIEWER_MODEL_ID to the E0 sentinel in a reviewed commit.",
            "Keep WorkflowOptions.enable_llm default set to false in that reviewed commit.",
            "Freeze the local spend ledger and note the freeze in the operator artifact before more live runs.",
            "Invalidate current gate_version cache rows with the SQL/command above.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, help="Optional LLM-QG SQLite cache path.")
    parser.add_argument("--gate-version", default=qg_workflow.DEFAULT_GATE_VERSION)
    parser.add_argument("--execute", action="store_true", help="Delete matching cache rows.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def render_text(payload: dict[str, Any]) -> str:
    lines = [
        "Tier-2 disarm checklist",
        f"- Restore DEFAULT_REVIEWER_MODEL_ID to {payload['e0_sentinel_model_id']}",
        "- Keep WorkflowOptions.enable_llm default off",
        "- Freeze the spend ledger and record the freeze note",
        f"- Invalidate cache rows for gate_version={payload['gate_version']}",
        f"  SQL: {payload['cache_invalidation_sql']}",
        f"  Command: {payload['cache_invalidation_command']}",
    ]
    if "rows_deleted" in payload:
        lines.append(f"- Rows deleted: {payload['rows_deleted']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = checklist(db_path=args.db, gate_version=args.gate_version)
    if args.execute:
        try:
            payload["rows_deleted"] = invalidate_gate_version_cache(
                db_path=args.db,
                gate_version=args.gate_version,
            )
        except sqlite3.DatabaseError as exc:
            print(f"error: {exc}")
            return 2
    output = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        if args.format == "json"
        else render_text(payload)
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
