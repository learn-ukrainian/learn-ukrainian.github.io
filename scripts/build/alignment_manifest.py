"""Alignment manifest helpers for cache invalidation across build sidecars."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from build.phases import wiki_compressor

from audit import config as audit_config

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SOURCES_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
CANONICAL_ANCHORS_PATH = PROJECT_ROOT / "data" / "canonical_anchors.yaml"
DECISIONS_PATH = PROJECT_ROOT / "docs" / "decisions" / "decisions.yaml"
PHASE_TEMPLATES_ROOT = PROJECT_ROOT / "scripts" / "build" / "phases"
CLAUDE_PHASES_ROOT = PROJECT_ROOT / ".claude" / "phases" / "claude"
GEMINI_PHASES_ROOT = PROJECT_ROOT / ".gemini" / "phases" / "gemini"
V6_BUILD_PATH = PROJECT_ROOT / "scripts" / "build" / "v6_build.py"

_ACTIVE_DECISION_SCOPES = {"pipeline", "architecture"}
_TEMPLATE_KEY_RE = re.compile(r"[^A-Za-z0-9]+")


def _load_v6_build_constant(name: str) -> Any:
    module = ast.parse(V6_BUILD_PATH.read_text("utf-8"))
    for node in module.body:
        if isinstance(node, ast.Assign):
            targets = [target for target in node.targets if isinstance(target, ast.Name)]
            if any(target.id == name for target in targets):
                return ast.literal_eval(node.value)
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
            and node.value is not None
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError(f"Could not load {name} from {V6_BUILD_PATH}")


REVIEW_TARGET_SCORE = float(_load_v6_build_constant("REVIEW_TARGET_SCORE"))


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _stable_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple((key, _freeze(value[key])) for key in sorted(value))
    if isinstance(value, set):
        return tuple(sorted(_freeze(item) for item in value))
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _plan_path(level: str, slug: str) -> Path:
    return CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"


def _canonical_plan_hash(level: str, slug: str) -> str:
    plan_data = yaml.safe_load(_plan_path(level, slug).read_text("utf-8"))
    canonical_yaml = yaml.safe_dump(plan_data, sort_keys=True, allow_unicode=True)
    return _sha256_bytes(canonical_yaml.encode("utf-8"))


def _sqlite_indexed_table_names(connection: sqlite3.Connection) -> tuple[str, ...]:
    rows = connection.execute(
        """
        SELECT name, COALESCE(sql, '')
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        """
    ).fetchall()
    names: list[str] = []
    for name, sql in rows:
        table_name = str(name)
        table_sql = str(sql or "")
        has_explicit_index = bool(
            connection.execute(f'PRAGMA index_list("{table_name}")').fetchall()
        )
        is_virtual_table = "VIRTUAL TABLE" in table_sql.upper()
        if has_explicit_index or is_virtual_table:
            names.append(table_name)
    return tuple(sorted(names))


def _sqlite_table_snapshot(connection: sqlite3.Connection, table_name: str) -> dict[str, Any]:
    row_count, max_rowid = connection.execute(
        f'SELECT COUNT(*), MAX(rowid) FROM "{table_name}"'
    ).fetchone()
    return {
        "table_name": table_name,
        "row_count": int(row_count or 0),
        "max_rowid": None if max_rowid is None else int(max_rowid),
    }


def _sources_hash() -> str:
    if not SOURCES_DB_PATH.exists():
        return _sha256_bytes(_stable_json_bytes(()))

    with sqlite3.connect(f"file:{SOURCES_DB_PATH}?mode=ro", uri=True) as connection:
        manifest_rows = tuple(
            _sqlite_table_snapshot(connection, table_name)
            for table_name in _sqlite_indexed_table_names(connection)
        )
    return _sha256_bytes(_stable_json_bytes(manifest_rows))


def _template_key(prefix: str, relative_path: Path) -> str:
    stem = str(relative_path.with_suffix("")).replace("\\", "/")
    key = _TEMPLATE_KEY_RE.sub("_", stem).strip("_").lower()
    return f"{prefix}__{key}" if prefix else key


def _template_hashes_from_root(
    root: Path,
    *,
    prefix: str,
    include_all_files: bool,
) -> dict[str, str]:
    if not root.exists():
        return {}

    hashes: dict[str, str] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if not include_all_files and path.suffix != ".md":
            continue
        relative_path = path.relative_to(root)
        hashes[_template_key(prefix, relative_path)] = _sha256_bytes(path.read_bytes())
    return hashes


def _template_hashes() -> dict[str, str]:
    template_hashes: dict[str, str] = {}
    template_hashes.update(
        _template_hashes_from_root(CLAUDE_PHASES_ROOT, prefix="claude", include_all_files=True)
    )
    template_hashes.update(
        _template_hashes_from_root(GEMINI_PHASES_ROOT, prefix="gemini", include_all_files=True)
    )
    template_hashes.update(
        _template_hashes_from_root(PHASE_TEMPLATES_ROOT, prefix="", include_all_files=False)
    )
    return dict(sorted(template_hashes.items()))


def _canonical_anchor_hash() -> str:
    return _sha256_bytes(CANONICAL_ANCHORS_PATH.read_bytes())


def _resolve_level_config_key(level: str) -> str:
    candidates = (level, level.upper(), level.lower(), level.capitalize())
    for candidate in candidates:
        if candidate in audit_config.LEVEL_CONFIG:
            return candidate
    raise KeyError(f"No LEVEL_CONFIG entry for {level!r}")


def _threshold_snapshot(level: str) -> dict[str, Any]:
    level_key = _resolve_level_config_key(level)
    return {
        "level_config": _freeze(audit_config.LEVEL_CONFIG[level_key]),
        "review_target_score": REVIEW_TARGET_SCORE,
    }


def _decisions_subset() -> list[tuple[str, str]]:
    if not DECISIONS_PATH.exists():
        return []

    payload = yaml.safe_load(DECISIONS_PATH.read_text("utf-8")) or {}
    decisions = payload.get("decisions") or []
    subset = [
        (str(decision["id"]), str(decision["status"]))
        for decision in decisions
        if decision.get("status") == "active"
        and decision.get("scope") in _ACTIVE_DECISION_SCOPES
    ]
    return sorted(subset)


def compose_manifest(*, level: str, slug: str) -> dict:
    """Build the full manifest dict (callers can inspect fields or the hash)."""
    return {
        "plan_hash": _canonical_plan_hash(level, slug),
        "sources_hash": _sources_hash(),
        "template_hashes": _template_hashes(),
        "canonical_anchor_hash": _canonical_anchor_hash(),
        "tokenizer_version": wiki_compressor.TOKENIZER_VERSION,
        "threshold_snapshot": _threshold_snapshot(level),
        "decisions_subset": _decisions_subset(),
    }


def manifest_hash(manifest: dict) -> str:
    """Return the SHA-256 hex digest of the canonicalized manifest."""
    return _sha256_bytes(_stable_json_bytes(manifest))


def stamp_artifact(artifact: dict, manifest: dict) -> dict:
    """Return artifact with `alignment_manifest` block injected (non-destructive)."""
    stamped = copy.deepcopy(artifact)
    stamped["alignment_manifest"] = {
        "composite_hash": manifest_hash(manifest),
        "composed_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "components": copy.deepcopy(manifest),
    }
    return stamped


def _diff_component(prefix: str, current_value: Any, stamped_value: Any) -> tuple[str, ...]:
    if isinstance(current_value, dict) and isinstance(stamped_value, dict):
        reasons: list[str] = []
        for key in sorted(set(current_value) | set(stamped_value)):
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            if key not in current_value or key not in stamped_value:
                reasons.append(child_prefix)
                continue
            reasons.extend(_diff_component(child_prefix, current_value[key], stamped_value[key]))
        return tuple(reasons)
    if current_value != stamped_value:
        return (prefix,)
    return ()


def validate_stamped_artifact(
    artifact: dict,
    current_manifest: dict,
) -> tuple[bool, tuple[str, ...]]:
    """Return (is_fresh, mismatch_reasons)."""
    stamped_manifest = artifact.get("alignment_manifest")
    if not isinstance(stamped_manifest, dict):
        return False, ("alignment_manifest",)

    stamped_components = stamped_manifest.get("components")
    if not isinstance(stamped_components, dict):
        return False, ("alignment_manifest",)

    mismatch_reasons = _diff_component("", current_manifest, stamped_components)
    if mismatch_reasons:
        return False, mismatch_reasons

    if stamped_manifest.get("composite_hash") != manifest_hash(current_manifest):
        return False, ("composite_hash",)

    return True, ()
