"""Persistent storage for LLM quality-gate results.

The pipeline may still emit ``llm_qg.json`` artifacts for debugging or
promotion workflows, but durable gate state belongs in a local SQLite store.
This keeps generated QG files out of PR diffs while still giving the Monitor
API and certification code a queryable source of truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from collections import Counter
from collections.abc import Mapping
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from scripts.api.config import PROJECT_ROOT
from scripts.api.resilience import connect_sqlite

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "telemetry" / "llm_qg.db"
DB_ENV_VAR = "LEARN_UKRAINIAN_LLM_QG_DB"
CONTENT_FILES = ("module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml")
EVIDENCE_SCHEMA_VERSION = "llm_qg_evidence.v1"
SUPPORTED_EVIDENCE_GATE_VERSIONS = frozenset({"v7.llm_qg.1"})
DIMENSION_ORDER = ("pedagogical", "naturalness", "decolonization", "engagement", "tone")


@dataclass(frozen=True, slots=True)
class StoredQG:
    """One persisted LLM-QG run."""

    run_id: str
    level: str
    slug: str
    content_sha: str
    gate_version: str
    prompt_hash: str | None
    reviewer_model: str | None
    reviewer_family: str | None
    source: str
    payload: dict[str, Any]
    created_at: str

    def is_current_for(self, module_dir: Path) -> bool:
        return self.content_sha == content_sha_for_module(module_dir)


def db_path(path: Path | None = None) -> Path:
    """Return the configured QG database path."""
    if path is not None:
        return path
    return Path(os.environ.get(DB_ENV_VAR, str(DEFAULT_DB_PATH)))


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_sha_for_module(module_dir: Path) -> str:
    """Hash the learner-facing source artifacts for one module directory."""
    h = hashlib.sha256()
    for name in CONTENT_FILES:
        path = module_dir / name
        if not path.exists():
            continue
        h.update(name.encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def llm_qg_file_is_current_for_module(module_dir: Path, path: Path | None = None) -> bool:
    """Return True when a module-local QG artifact is not older than content.

    File artifacts do not carry a content hash. Treat them as a fallback only
    when their mtime is at least as new as every learner-facing source file.
    """
    qg_path = path or module_dir / "llm_qg.json"
    try:
        artifact_mtime_ns = qg_path.stat().st_mtime_ns
    except OSError:
        return False

    for name in CONTENT_FILES:
        content_path = module_dir / name
        if not content_path.exists():
            continue
        try:
            if content_path.stat().st_mtime_ns > artifact_mtime_ns:
                return False
        except OSError:
            return False
    return True


def prompt_hash_for_text(prompt: str | None) -> str | None:
    """Return a stable hash for a prompt body, if present."""
    if prompt is None:
        return None
    return _sha256_bytes(prompt.encode("utf-8"))


def init_db(path: Path | None = None) -> Path:
    """Create the LLM-QG persistence schema if needed."""
    resolved = db_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect_sqlite(str(resolved))) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS llm_qg_runs (
                run_id          TEXT PRIMARY KEY,
                created_at      TEXT NOT NULL,
                level           TEXT NOT NULL,
                slug            TEXT NOT NULL,
                content_sha     TEXT NOT NULL,
                gate_version    TEXT NOT NULL,
                prompt_hash     TEXT,
                reviewer_model  TEXT,
                reviewer_family TEXT,
                source          TEXT NOT NULL,
                verdict         TEXT,
                terminal_verdict TEXT,
                min_score       REAL,
                min_dim         TEXT,
                payload_json    TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_llm_qg_level_slug_created
                ON llm_qg_runs(level, slug, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_llm_qg_level_slug_content
                ON llm_qg_runs(level, slug, content_sha, created_at DESC);

            CREATE TABLE IF NOT EXISTS llm_qg_findings (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          TEXT NOT NULL,
                category        TEXT,
                severity        TEXT,
                file            TEXT,
                quote           TEXT,
                replacement     TEXT,
                payload_json    TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES llm_qg_runs(run_id)
                    ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_llm_qg_findings_run
                ON llm_qg_findings(run_id, id);
            CREATE INDEX IF NOT EXISTS idx_llm_qg_findings_category
                ON llm_qg_findings(category, severity);
            """
        )
        conn.commit()
    return resolved


def _aggregate(payload: dict[str, Any]) -> dict[str, Any]:
    aggregate = payload.get("aggregate")
    return aggregate if isinstance(aggregate, dict) else {}


def _iter_findings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    findings = payload.get("findings")
    if isinstance(findings, list):
        return [item for item in findings if isinstance(item, dict)]
    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, dict):
        return []
    out: list[dict[str, Any]] = []
    for dim, entry in dimensions.items():
        if not isinstance(entry, dict):
            continue
        dim_findings = entry.get("findings")
        if isinstance(dim_findings, list):
            for item in dim_findings:
                if isinstance(item, dict):
                    out.append({"dimension": dim, **item})
    return out


def _finding_category(item: dict[str, Any]) -> Any:
    return (
        item.get("category")
        or item.get("issue_id")
        or item.get("issue_type")
        or item.get("type")
        or item.get("kind")
    )


def record_llm_qg(
    *,
    level: str,
    slug: str,
    module_dir: Path,
    payload: dict[str, Any],
    gate_version: str,
    prompt_hash: str | None = None,
    reviewer_model: str | None = None,
    reviewer_family: str | None = None,
    source: str = "pipeline",
    run_id: str | None = None,
    path: Path | None = None,
) -> StoredQG:
    """Persist one LLM-QG run and return the stored record."""
    resolved = init_db(path)
    clean_level = level.strip().lower()
    clean_slug = slug.strip()
    clean_run_id = run_id or f"llm-qg-{uuid4().hex}"
    created_at = _now_z()
    content_sha = content_sha_for_module(module_dir)
    aggregate = _aggregate(payload)
    findings = _iter_findings(payload)

    with closing(connect_sqlite(str(resolved))) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            INSERT INTO llm_qg_runs (
                run_id, created_at, level, slug, content_sha, gate_version,
                prompt_hash, reviewer_model, reviewer_family, source, verdict,
                terminal_verdict, min_score, min_dim, payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                created_at = excluded.created_at,
                level = excluded.level,
                slug = excluded.slug,
                content_sha = excluded.content_sha,
                gate_version = excluded.gate_version,
                prompt_hash = excluded.prompt_hash,
                reviewer_model = excluded.reviewer_model,
                reviewer_family = excluded.reviewer_family,
                source = excluded.source,
                verdict = excluded.verdict,
                terminal_verdict = excluded.terminal_verdict,
                min_score = excluded.min_score,
                min_dim = excluded.min_dim,
                payload_json = excluded.payload_json
            """,
            (
                clean_run_id,
                created_at,
                clean_level,
                clean_slug,
                content_sha,
                gate_version,
                prompt_hash,
                reviewer_model,
                reviewer_family,
                source,
                aggregate.get("verdict"),
                aggregate.get("terminal_verdict"),
                aggregate.get("min_score"),
                aggregate.get("min_dim"),
                _json_dumps(payload),
            ),
        )
        conn.execute("DELETE FROM llm_qg_findings WHERE run_id = ?", (clean_run_id,))
        conn.executemany(
            """
            INSERT INTO llm_qg_findings (
                run_id, category, severity, file, quote, replacement, payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    clean_run_id,
                    _finding_category(item),
                    item.get("severity"),
                    item.get("file"),
                    item.get("quote"),
                    item.get("replacement"),
                    _json_dumps(item),
                )
                for item in findings
            ],
        )
        conn.commit()

    return StoredQG(
        run_id=clean_run_id,
        level=clean_level,
        slug=clean_slug,
        content_sha=content_sha,
        gate_version=gate_version,
        prompt_hash=prompt_hash,
        reviewer_model=reviewer_model,
        reviewer_family=reviewer_family,
        source=source,
        payload=payload,
        created_at=created_at,
    )


def _row_to_record(row: sqlite3.Row) -> StoredQG:
    return StoredQG(
        run_id=str(row["run_id"]),
        level=str(row["level"]),
        slug=str(row["slug"]),
        content_sha=str(row["content_sha"]),
        gate_version=str(row["gate_version"]),
        prompt_hash=row["prompt_hash"],
        reviewer_model=row["reviewer_model"],
        reviewer_family=row["reviewer_family"],
        source=str(row["source"]),
        payload=json.loads(str(row["payload_json"])),
        created_at=str(row["created_at"]),
    )


def latest_llm_qg(
    level: str,
    slug: str,
    *,
    content_sha: str | None = None,
    path: Path | None = None,
) -> StoredQG | None:
    """Return the newest persisted QG run for a module, optionally hash-bound."""
    resolved = db_path(path)
    if not resolved.exists():
        return None
    params: list[Any] = [level.strip().lower(), slug.strip()]
    where = "level = ? AND slug = ?"
    if content_sha is not None:
        where += " AND content_sha = ?"
        params.append(content_sha)
    try:
        with closing(connect_sqlite(str(resolved))) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                f"""
                SELECT *
                FROM llm_qg_runs
                WHERE {where}
                ORDER BY created_at DESC, run_id DESC
                LIMIT 1
                """,
                params,
            ).fetchone()
        return _row_to_record(row) if row else None
    except (json.JSONDecodeError, OSError, sqlite3.DatabaseError, ValueError):
        return None


def current_llm_qg_for_module(
    level: str,
    slug: str,
    module_dir: Path,
    *,
    path: Path | None = None,
) -> StoredQG | None:
    """Return the newest QG run whose content hash matches current artifacts."""
    return latest_llm_qg(
        level,
        slug,
        content_sha=content_sha_for_module(module_dir),
        path=path,
    )


def current_payload_for_module(
    level: str,
    slug: str,
    module_dir: Path,
    *,
    path: Path | None = None,
) -> dict[str, Any] | None:
    """Return the current QG payload for a module, or ``None`` if missing/stale."""
    record = current_llm_qg_for_module(level, slug, module_dir, path=path)
    if record is None:
        return None
    return {
        **record.payload,
        "_store": {
            "run_id": record.run_id,
            "created_at": record.created_at,
            "content_sha": record.content_sha,
            "gate_version": record.gate_version,
            "source": record.source,
        },
    }


def compact_evidence_for_record(
    record: StoredQG,
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    """Return a compact, git-friendly evidence snapshot for one stored run."""
    aggregate = _aggregate(record.payload)
    raw_dimensions = record.payload.get("dimensions")
    dimensions: dict[str, dict[str, Any]] = {}
    if isinstance(raw_dimensions, dict):
        ordered_dims = [
            *[dim for dim in DIMENSION_ORDER if dim in raw_dimensions],
            *sorted(dim for dim in raw_dimensions if dim not in DIMENSION_ORDER),
        ]
        for dim in ordered_dims:
            entry = raw_dimensions.get(dim)
            if not isinstance(entry, dict):
                continue
            compact_entry: dict[str, Any] = {}
            if isinstance(entry.get("score"), int | float):
                compact_entry["score"] = float(entry["score"])
            if isinstance(entry.get("verdict"), str):
                compact_entry["verdict"] = entry["verdict"]
            if compact_entry:
                dimensions[dim] = compact_entry

    findings_summary = _findings_summary(record.payload)
    result: dict[str, Any] = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "level": record.level,
        "slug": record.slug,
        "content_sha": record.content_sha,
        "gate_version": record.gate_version,
        "prompt_hash": record.prompt_hash,
        "provenance": {
            "created_at": record.created_at,
            "run_id": record.run_id,
            "source": record.source,
        },
        "reviewer": {
            "family": record.reviewer_family,
            "model": record.reviewer_model,
        },
        "verdict": aggregate.get("verdict"),
        "terminal_verdict": aggregate.get("terminal_verdict"),
        "min_score": aggregate.get("min_score"),
        "min_dim": aggregate.get("min_dim"),
        "dimensions": dimensions,
        "findings_summary": findings_summary,
    }
    if profile:
        result["profile"] = profile
    return result


def _findings_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return count-only finding metadata safe to persist in git."""
    by_category: Counter[str] = Counter()
    by_severity: Counter[str] = Counter()
    total = 0
    raw_dimensions = payload.get("dimensions")
    if isinstance(raw_dimensions, Mapping):
        for entry in raw_dimensions.values():
            if not isinstance(entry, Mapping):
                continue
            findings = entry.get("findings")
            if not isinstance(findings, list):
                continue
            for finding in findings:
                if not isinstance(finding, Mapping):
                    continue
                total += 1
                category = finding.get("category") or finding.get("issue_id") or "uncategorized"
                severity = finding.get("severity") or "unknown"
                by_category[str(category)] += 1
                by_severity[str(severity)] += 1
    return {
        "total": total,
        "by_category": dict(sorted(by_category.items())),
        "by_severity": dict(sorted(by_severity.items())),
    }


def current_evidence_for_module(
    level: str,
    slug: str,
    module_dir: Path,
    *,
    profile: str | None = None,
    path: Path | None = None,
) -> dict[str, Any] | None:
    """Return a compact evidence snapshot for the current module hash."""
    record = current_llm_qg_for_module(level, slug, module_dir, path=path)
    if record is None:
        return None
    return compact_evidence_for_record(record, profile=profile)


def evidence_record_is_current_for_module(
    evidence: Mapping[str, Any],
    module_dir: Path,
) -> bool:
    """Return True when a compact evidence record matches module content."""
    return evidence.get("content_sha") == content_sha_for_module(module_dir)


def evidence_record_passes_for_module(
    evidence: Mapping[str, Any],
    module_dir: Path,
    *,
    supported_gate_versions: set[str] | frozenset[str] = SUPPORTED_EVIDENCE_GATE_VERSIONS,
) -> bool:
    """Return True when evidence is current and acceptable for promotion."""
    return (
        evidence.get("schema_version") == EVIDENCE_SCHEMA_VERSION
        and str(evidence.get("terminal_verdict", "")).upper() == "PASS"
        and evidence.get("gate_version") in supported_gate_versions
        and evidence_record_is_current_for_module(evidence, module_dir)
    )


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export/check compact LLM-QG evidence records.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-record", action="store_true", help="Export current DB evidence as compact JSON.")
    mode.add_argument("--check-record", action="store_true", help="Check compact JSON content_sha against a module.")
    parser.add_argument("--level", help="Curriculum level, e.g. b1.")
    parser.add_argument("--slug", help="Module slug.")
    parser.add_argument("--module-dir", type=Path, required=True, help="Module artifact directory.")
    parser.add_argument("--profile", help="Optional curriculum profile label.")
    parser.add_argument("--db", type=Path, help="Optional LLM-QG SQLite path.")
    parser.add_argument("--out", type=Path, help="Output JSON path for --emit-record.")
    parser.add_argument("--record", type=Path, help="Input JSON path for --check-record.")
    args = parser.parse_args(argv)

    if args.emit_record:
        if not args.level or not args.slug or not args.out:
            parser.error("--emit-record requires --level, --slug, and --out")
        evidence = current_evidence_for_module(
            args.level,
            args.slug,
            args.module_dir,
            profile=args.profile,
            path=args.db,
        )
        if evidence is None:
            print("No current LLM-QG DB record for module content")
            return 1
        _write_json(args.out, evidence)
        return 0

    if not args.record:
        parser.error("--check-record requires --record")
    evidence = json.loads(args.record.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict) or not evidence_record_passes_for_module(
        evidence,
        args.module_dir,
    ):
        print("LLM-QG evidence record is stale or not acceptable for module content")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
