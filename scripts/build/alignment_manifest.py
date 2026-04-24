"""Alignment manifest helpers for cache invalidation across build sidecars."""

from __future__ import annotations

import ast
import copy
import functools
import hashlib
import inspect
import json
import re
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from build.phases import wiki_compressor

from audit import config as audit_config

_ACTIVE_DECISION_SCOPES = {"pipeline", "architecture"}
_TEMPLATE_KEY_RE = re.compile(r"[^A-Za-z0-9]+")
_PATH_ATTRS = {
    "PROJECT_ROOT",
    "CURRICULUM_ROOT",
    "SOURCES_DB_PATH",
    "CANONICAL_ANCHORS_PATH",
    "DECISIONS_PATH",
    "PHASE_TEMPLATES_ROOT",
    "CLAUDE_PHASES_ROOT",
    "GEMINI_PHASES_ROOT",
    "V6_BUILD_PATH",
}


def _default_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_v6_build_path() -> Path:
    return _default_project_root() / "scripts" / "build" / "v6_build.py"


def _static_default_attr(name: str) -> Any:
    if name == "PROJECT_ROOT":
        return _default_project_root()
    if name == "CURRICULUM_ROOT":
        return _default_project_root() / "curriculum" / "l2-uk-en"
    if name == "SOURCES_DB_PATH":
        return _default_project_root() / "data" / "sources.db"
    if name == "CANONICAL_ANCHORS_PATH":
        return _default_project_root() / "data" / "canonical_anchors.yaml"
    if name == "DECISIONS_PATH":
        return _default_project_root() / "docs" / "decisions" / "decisions.yaml"
    if name == "PHASE_TEMPLATES_ROOT":
        return _default_project_root() / "scripts" / "build" / "phases"
    if name == "CLAUDE_PHASES_ROOT":
        return _default_project_root() / ".claude" / "phases" / "claude"
    if name == "GEMINI_PHASES_ROOT":
        return _default_project_root() / ".gemini" / "phases" / "gemini"
    if name == "V6_BUILD_PATH":
        return _default_v6_build_path()
    raise AttributeError(f"module 'alignment_manifest' has no attribute {name!r}")


def _v6_build_module() -> Any | None:
    v6_build_path = _default_v6_build_path().resolve()

    frame = inspect.currentframe()
    while frame is not None:
        frame = frame.f_back
        if frame is None:
            break
        module_file = frame.f_globals.get("__file__")
        if module_file is None:
            continue
        if Path(module_file).resolve() != v6_build_path:
            continue
        module_name = frame.f_globals.get("__name__")
        module = sys.modules.get(str(module_name))
        if module is not None:
            return module

    for module_name in ("build.v6_build", "scripts.build.v6_build", "v6_build"):
        module = sys.modules.get(module_name)
        if module is not None:
            return module

    for module in sys.modules.values():
        module_file = getattr(module, "__file__", None)
        if module_file is not None and Path(module_file).resolve() == v6_build_path:
            return module
    return None


def _resolve_attr(name: str) -> Any:
    v6_build = _v6_build_module()

    if name == "PROJECT_ROOT":
        root = getattr(v6_build, "PROJECT_ROOT", None) if v6_build is not None else None
        return Path(root) if root is not None else _default_project_root()
    if name == "CURRICULUM_ROOT":
        root = getattr(v6_build, "CURRICULUM_ROOT", None) if v6_build is not None else None
        return Path(root) if root is not None else _resolve_attr("PROJECT_ROOT") / "curriculum" / "l2-uk-en"
    if name == "SOURCES_DB_PATH":
        return _resolve_attr("PROJECT_ROOT") / "data" / "sources.db"
    if name == "CANONICAL_ANCHORS_PATH":
        return _resolve_attr("PROJECT_ROOT") / "data" / "canonical_anchors.yaml"
    if name == "DECISIONS_PATH":
        return _resolve_attr("PROJECT_ROOT") / "docs" / "decisions" / "decisions.yaml"
    if name == "PHASE_TEMPLATES_ROOT":
        root = getattr(v6_build, "PHASES_DIR", None) if v6_build is not None else None
        return (
            Path(root)
            if root is not None
            else _resolve_attr("PROJECT_ROOT") / "scripts" / "build" / "phases"
        )
    if name == "CLAUDE_PHASES_ROOT":
        return _resolve_attr("PROJECT_ROOT") / ".claude" / "phases" / "claude"
    if name == "GEMINI_PHASES_ROOT":
        return _resolve_attr("PROJECT_ROOT") / ".gemini" / "phases" / "gemini"
    if name == "V6_BUILD_PATH":
        module_file = getattr(v6_build, "__file__", None) if v6_build is not None else None
        return (
            Path(module_file).resolve()
            if module_file is not None
            else _default_v6_build_path()
        )
    if name == "REVIEW_TARGET_SCORE":
        return _review_target_score()
    raise AttributeError(f"module 'alignment_manifest' has no attribute {name!r}")


def _module_attr(name: str) -> Any:
    if name in globals():
        value = globals()[name]
        if name in _PATH_ATTRS and value == _static_default_attr(name):
            return _resolve_attr(name)
        return value
    return _resolve_attr(name)


def _load_v6_build_constant(name: str) -> Any:
    v6_build = _v6_build_module()
    if v6_build is not None and hasattr(v6_build, name):
        return getattr(v6_build, name)

    v6_build_path = _module_attr("V6_BUILD_PATH")
    module = ast.parse(v6_build_path.read_text("utf-8"))
    # Index top-level assigns so we can resolve Name aliases (e.g.
    # ``REVIEW_TARGET_SCORE = REVIEW_PASS_FLOOR``) without importing
    # v6_build. Maps target-name → (RHS AST node).
    top_level_values: dict[str, Any] = {}
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    top_level_values[target.id] = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.value is not None
        ):
            top_level_values[node.target.id] = node.value

    def _resolve_node(value_node: ast.AST, seen: set[str]) -> Any:
        if isinstance(value_node, ast.Name):
            if value_node.id in seen:
                raise RuntimeError(
                    f"Cycle resolving {name} in {v6_build_path}: {' -> '.join(seen)}"
                )
            seen.add(value_node.id)
            if value_node.id in top_level_values:
                return _resolve_node(top_level_values[value_node.id], seen)
            # Imported name — try the common.thresholds source of truth.
            from common import thresholds as _thresholds
            if hasattr(_thresholds, value_node.id):
                return getattr(_thresholds, value_node.id)
        return ast.literal_eval(value_node)

    if name in top_level_values:
        return _resolve_node(top_level_values[name], set())
    raise RuntimeError(f"Could not load {name} from {v6_build_path}")


@functools.lru_cache(maxsize=1)
def _review_target_score() -> float:
    """Lazy accessor for REVIEW_TARGET_SCORE.

    Loading at import time was brittle: it ran AST parsing on
    `v6_build.py` on every import of this module, which broke tests
    that monkeypatch `PROJECT_ROOT` (the constant was already
    evaluated against the real path before the fixture ran) and failed
    with `FileNotFoundError` whenever this module was imported outside
    a full checkout. Flagged by gemini-review on PR #1468.
    """
    return float(_load_v6_build_constant("REVIEW_TARGET_SCORE"))


def __getattr__(name: str) -> Any:
    """PEP 562 module-level lazy attribute.

    Preserves the `alignment_manifest.<CONST>` access shape used by
    tests without pinning repo paths at import time. Callers that
    monkeypatch this module still override the returned values by
    assigning real module attributes.
    """
    if name in _PATH_ATTRS or name == "REVIEW_TARGET_SCORE":
        return _resolve_attr(name)
    raise AttributeError(f"module 'alignment_manifest' has no attribute {name!r}")


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
    # Curriculum plan directories are lowercase on disk (a1, b2-pro, hist, …).
    # Canonicalize `level` so callers can pass "A1" or "B2-Pro" without
    # breaking on case-sensitive filesystems. Flagged by gemini-review on
    # PR #1468.
    return _module_attr("CURRICULUM_ROOT") / "plans" / level.lower() / f"{slug}.yaml"


def _canonical_plan_hash(level: str, slug: str) -> str:
    plan_data = yaml.safe_load(_plan_path(level, slug).read_text("utf-8"))
    canonical_yaml = yaml.safe_dump(plan_data, sort_keys=True, allow_unicode=True)
    return _sha256_bytes(canonical_yaml.encode("utf-8"))


# FTS5 creates these shadow tables for every virtual table `<name>`:
#   <name>_data, <name>_idx, <name>_content, <name>_docsize, <name>_config
# They must be excluded from the manifest for TWO reasons (#1517):
#   1. Correctness: `_idx` and `_config` are declared WITHOUT ROWID, so
#      `SELECT MAX(rowid)` raises "no such column: rowid" and crashes every
#      build. The shadow tables pass the `PRAGMA index_list` filter below
#      because their PRIMARY KEYs register as implicit indexes.
#   2. Stability: segids, pgnos, and serialized segment blobs inside the
#      shadow tables are SQLite-internal bookkeeping that differs across
#      identical content rebuilds (after VACUUM, `INSERT … INTO …('optimize')`,
#      or re-ingest). Hashing them would produce a non-deterministic manifest.
# The virtual table itself (e.g. `literary_fts`) answers the rowid query
# correctly and IS included — its rowid tracks content identity.
_FTS5_SHADOW_SUFFIXES: tuple[str, ...] = (
    "_data",
    "_idx",
    "_content",
    "_docsize",
    "_config",
)


def _sqlite_indexed_table_names(connection: sqlite3.Connection) -> tuple[str, ...]:
    rows = connection.execute(
        """
        SELECT name, COALESCE(sql, '')
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        """
    ).fetchall()

    # Pass 1: identify virtual tables so we can recognize their shadows.
    virtual_table_names: set[str] = set()
    for name, sql in rows:
        table_sql = str(sql or "")
        # Substring `"VIRTUAL TABLE"` would false-positive on a table
        # named e.g. `my_virtual_table_data`. Match the DDL prefix instead.
        # Flagged by gemini-review on PR #1468.
        if table_sql.upper().lstrip().startswith("CREATE VIRTUAL TABLE"):
            virtual_table_names.add(str(name))

    shadow_names: set[str] = {
        f"{vt}{suffix}"
        for vt in virtual_table_names
        for suffix in _FTS5_SHADOW_SUFFIXES
    }

    # Pass 2: keep virtual tables and any regular table with an explicit
    # index, BUT subtract FTS5 shadows — see the block comment above for
    # why we must exclude them even though they pass the index filter.
    names: list[str] = []
    for name, sql in rows:
        table_name = str(name)
        if table_name in shadow_names:
            continue
        table_sql = str(sql or "")
        is_virtual_table = table_sql.upper().lstrip().startswith("CREATE VIRTUAL TABLE")
        has_explicit_index = bool(
            connection.execute(f'PRAGMA index_list("{table_name}")').fetchall()
        )
        if is_virtual_table or has_explicit_index:
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
    sources_db_path = _module_attr("SOURCES_DB_PATH")
    if not sources_db_path.exists():
        return _sha256_bytes(_stable_json_bytes(()))

    # `Path.as_uri()` produces a cross-platform-safe `file://…` URI;
    # raw f-string interpolation leaks backslashes on Windows. Flagged
    # by gemini-review on PR #1468.
    db_uri = f"{sources_db_path.as_uri()}?mode=ro"
    with sqlite3.connect(db_uri, uri=True) as connection:
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
        _template_hashes_from_root(
            _module_attr("CLAUDE_PHASES_ROOT"),
            prefix="claude",
            include_all_files=True,
        )
    )
    template_hashes.update(
        _template_hashes_from_root(
            _module_attr("GEMINI_PHASES_ROOT"),
            prefix="gemini",
            include_all_files=True,
        )
    )
    template_hashes.update(
        _template_hashes_from_root(
            _module_attr("PHASE_TEMPLATES_ROOT"),
            prefix="",
            include_all_files=False,
        )
    )
    return dict(sorted(template_hashes.items()))


def _canonical_anchor_hash() -> str:
    canonical_anchors_path = _module_attr("CANONICAL_ANCHORS_PATH")
    if not canonical_anchors_path.exists():
        return _sha256_bytes(b"")
    return _sha256_bytes(canonical_anchors_path.read_bytes())


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
        # Access the module attribute (not the `_review_target_score()`
        # function directly) so tests can `monkeypatch.setattr` the
        # value. See `__getattr__` / `_review_target_score` docstrings.
        "review_target_score": _module_attr("REVIEW_TARGET_SCORE"),
    }


def _decisions_subset() -> list[tuple[str, str]]:
    decisions_path = _module_attr("DECISIONS_PATH")
    if not decisions_path.exists():
        return []

    payload = yaml.safe_load(decisions_path.read_text("utf-8")) or {}
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
