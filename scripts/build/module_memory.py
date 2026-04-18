"""Persistent module memory for the convergent pipeline."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

PLAN_LEVEL_ERROR_CLASSES = {
    "vocab_density",
    "pedagogical_sequence",
    "scenario_grammar_misalignment",
    "plan_contradiction",
}

WRITER_ADDRESSABLE_ERROR_CLASSES = {
    "activity_order",
    "calque",
    "cultural_register",
    "dialogue_arc_fail",
    "exercise_logic",
    "factual_error",
    "meta_narration",
    "missing_vocab",
    "notation_error",
    "register_drift",
    "structural_gap",
    "surzhyk",
    "word_budget",
}


def module_memory_path(curriculum_root: Path, level: str, slug: str) -> Path:
    return curriculum_root / level / "orchestration" / slug / "module-memory.yaml"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text("utf-8"))


def _write_yaml_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        "utf-8",
    )
    temp_path.replace(path)


def _default_memory(
    *,
    plan_hash: str | None = None,
    plan_version: int | None = None,
    sources_hash: str | None = None,
) -> dict[str, Any]:
    return {
        "plan_hash": plan_hash or "",
        "plan_version": int(plan_version or 0),
        "sources_hash": sources_hash or "",
        "constraints": [],
        "history": [],
        "events": [],
    }


def find_pravopys_files(project_root: Path) -> list[Path]:
    candidates: list[Path] = []
    rag_dir = project_root / ".mcp" / "servers" / "rag"
    if rag_dir.exists():
        for path in sorted(rag_dir.rglob("*")):
            if path.is_file() and ("prav" in path.name.lower() or "прав" in path.name.lower()):
                candidates.append(path)
    if candidates:
        return candidates

    fallback = project_root / "pravopys.html"
    return [fallback] if fallback.exists() else []


def _tree_manifest(root: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    if not root.exists():
        return manifest
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        manifest[str(path.relative_to(root))] = _sha256_file(path)
    return manifest


def _manifest_path_key(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path.resolve())


def _sqlite_table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        """
    ).fetchall()
    return {str(row[0]) for row in rows}


def _sqlite_table_digest(connection: sqlite3.Connection, table_name: str) -> str:
    columns = [str(row[1]) for row in connection.execute(f'PRAGMA table_info("{table_name}")')]
    digest = hashlib.sha256()
    digest.update(table_name.encode("utf-8"))
    digest.update(b"\n")
    digest.update(_stable_json(columns))
    digest.update(b"\n")

    try:
        rows = connection.execute(f'SELECT rowid, * FROM "{table_name}" ORDER BY rowid')
    except sqlite3.OperationalError:
        order_clause = ", ".join(f'"{column}"' for column in columns)
        query = f'SELECT * FROM "{table_name}"'
        if order_clause:
            query += f" ORDER BY {order_clause}"
        rows = connection.execute(query)

    for row in rows:
        digest.update(_stable_json(list(row)))
        digest.update(b"\n")
    return digest.hexdigest()


def _sqlite_group_digest(db_path: Path, tables: tuple[str, ...]) -> str | None:
    if not db_path.exists():
        return None

    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as connection:
        existing_tables = _sqlite_table_names(connection)
        digest = hashlib.sha256()
        used = False
        for table_name in tables:
            if table_name not in existing_tables:
                continue
            digest.update(table_name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(_sqlite_table_digest(connection, table_name).encode("utf-8"))
            digest.update(b"\n")
            used = True
    return digest.hexdigest() if used else None


def _sqlite_table_hashes(db_path: Path, tables: tuple[str, ...]) -> dict[str, str]:
    if not db_path.exists():
        return {}

    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as connection:
        existing_tables = _sqlite_table_names(connection)
        return {
            table_name: _sqlite_table_digest(connection, table_name)
            for table_name in tables
            if table_name in existing_tables
        }


def compute_sources_manifest(
    *,
    project_root: Path,
    curriculum_root: Path,
    level: str,
    slug: str,
    writer_template_path: Path,
) -> dict[str, str]:
    manifest: dict[str, str] = {}

    vesum_db = project_root / "data" / "vesum.db"
    for table_name, digest in _sqlite_table_hashes(vesum_db, ("lemmas", "forms")).items():
        manifest[f"sqlite://data/vesum.db#{table_name}"] = digest

    sources_db = project_root / "data" / "sources.db"
    textbooks_hash = _sqlite_group_digest(sources_db, ("textbooks_fts",))
    if textbooks_hash is not None:
        manifest["sqlite://data/sources.db#textbooks_fts"] = textbooks_hash
    literary_hash = _sqlite_group_digest(sources_db, ("literary_fts",))
    if literary_hash is not None:
        manifest["sqlite://data/sources.db#literary_fts"] = literary_hash
    dictionary_hash = _sqlite_group_digest(
        sources_db,
        (
            "balla_en_uk",
            "dmklinger_uk_en",
            "frazeolohichnyi",
            "grinchenko",
            "ukrajinet",
            "wiktionary",
        ),
    )
    if dictionary_hash is not None:
        manifest["sqlite://data/sources.db#dictionary_indexes"] = dictionary_hash

    for path in find_pravopys_files(project_root):
        manifest[_manifest_path_key(path, project_root)] = _sha256_file(path)

    wiki_root = curriculum_root / "wiki" / level / slug
    wiki_manifest = _tree_manifest(wiki_root)
    for rel_path, digest in wiki_manifest.items():
        manifest[f"wiki://{level}/{slug}/{rel_path}"] = digest

    if writer_template_path.exists():
        manifest[_manifest_path_key(writer_template_path, project_root)] = _sha256_file(
            writer_template_path
        )

    return manifest


def compute_sources_hash(
    *,
    project_root: Path,
    curriculum_root: Path,
    level: str,
    slug: str,
    writer_template_path: Path,
) -> str:
    manifest = compute_sources_manifest(
        project_root=project_root,
        curriculum_root=curriculum_root,
        level=level,
        slug=slug,
        writer_template_path=writer_template_path,
    )
    return _sha256_bytes(_stable_json(manifest))


def reset_module_memory(path: Path) -> bool:
    if not path.exists():
        return False
    path.unlink()
    return True


def load_module_memory(
    path: Path,
    *,
    expected_plan_hash: str | None = None,
    expected_plan_version: int | None = None,
    expected_sources_hash: str | None = None,
    reset: bool = False,
) -> tuple[dict[str, Any], bool]:
    if reset:
        reset_module_memory(path)

    if path.exists():
        loaded = _read_yaml(path)
        memory = loaded if isinstance(loaded, dict) else {}
    else:
        memory = {}

    merged = _default_memory(
        plan_hash=memory.get("plan_hash"),
        plan_version=memory.get("plan_version"),
        sources_hash=memory.get("sources_hash"),
    )
    merged["constraints"] = list(memory.get("constraints") or [])
    merged["history"] = list(memory.get("history") or [])
    merged["events"] = list(memory.get("events") or [])

    invalidated = False
    if (
        expected_plan_hash
        and merged["plan_hash"]
        and merged["plan_hash"] != expected_plan_hash
    ):
        invalidated = True
        merged["constraints"] = []
        merged["events"].append(
            {
                "type": "plan_hash_invalidation",
                "ts": datetime.now(tz=UTC).isoformat(),
                "previous_plan_hash": merged["plan_hash"],
                "current_plan_hash": expected_plan_hash,
            }
        )

    if expected_plan_hash is not None:
        merged["plan_hash"] = expected_plan_hash
    if expected_plan_version is not None:
        merged["plan_version"] = int(expected_plan_version)
    if expected_sources_hash is not None:
        merged["sources_hash"] = expected_sources_hash

    if not path.exists() or invalidated:
        save_module_memory(path, merged)

    return merged, invalidated


def save_module_memory(path: Path, memory: dict[str, Any]) -> None:
    normalized = _default_memory(
        plan_hash=str(memory.get("plan_hash") or ""),
        plan_version=int(memory.get("plan_version") or 0),
        sources_hash=str(memory.get("sources_hash") or ""),
    )
    normalized["constraints"] = list(memory.get("constraints") or [])
    normalized["history"] = list(memory.get("history") or [])
    normalized["events"] = list(memory.get("events") or [])
    _write_yaml_atomic(path, normalized)


def append_history(memory: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    memory.setdefault("history", [])
    memory["history"] = [*list(memory["history"]), entry]
    return memory


def _scope_key(constraint: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    scope = constraint.get("scope") or {}
    if not isinstance(scope, dict):
        scope = {}
    return (
        _normalized_text(scope.get("speaker")),
        _normalized_text(scope.get("section_title") or scope.get("section")),
        _normalized_text(scope.get("target_lexeme")),
    )


def _normalized_text(value: Any) -> str | None:
    text = str(value).strip().lower() if value is not None else ""
    return text or None


def _tokenize_directive(text: str) -> set[str]:
    return {token for token in re_split_words(text.lower()) if len(token) > 2}


def re_split_words(text: str) -> list[str]:
    current = []
    token = []
    for char in text:
        if char.isalnum() or char in {"'", "’", "-"}:
            token.append(char)
            continue
        if token:
            current.append("".join(token))
            token = []
    if token:
        current.append("".join(token))
    return current


def directives_conflict(left: str, right: str) -> bool:
    left_norm = " ".join(re_split_words(left.lower()))
    right_norm = " ".join(re_split_words(right.lower()))
    if not left_norm or not right_norm or left_norm == right_norm:
        return False

    antonym_pairs = (
        ("formal", "informal"),
        ("ви", "ти"),
        ("teacher", "peer"),
        ("добрий день", "привіт"),
    )
    for first, second in antonym_pairs:
        if ({first, second} <= {left_norm, right_norm}) or (
            (first in left_norm
            and second in right_norm)
            or (second in left_norm
            and first in right_norm)
        ):
            return True

    negations = (" no ", " not ", " never ", " avoid ", " forbid ", " without ")
    left_negated = any(token in f" {left_norm} " for token in negations)
    right_negated = any(token in f" {right_norm} " for token in negations)
    if left_negated == right_negated:
        return False

    overlap = _tokenize_directive(left_norm) & _tokenize_directive(right_norm)
    return len(overlap) >= 2


def find_conflicting_constraints(
    constraints: list[dict[str, Any]],
    candidate: dict[str, Any],
) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    candidate_scope = _scope_key(candidate)
    if candidate_scope == (None, None, None):
        return conflicts

    candidate_directive = str(candidate.get("directive") or "")
    for current in constraints:
        if str(current.get("status") or "active") != "active":
            continue
        if _scope_key(current) != candidate_scope:
            continue
        if directives_conflict(str(current.get("directive") or ""), candidate_directive):
            conflicts.append(current)
    return conflicts


def quarantine_conflicting_constraints(
    memory: dict[str, Any],
    candidate: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    constraints = list(memory.get("constraints") or [])
    conflicts = find_conflicting_constraints(constraints, candidate)
    if not conflicts:
        return candidate, False

    for current in constraints:
        if current in conflicts:
            current["status"] = "quarantined"
            current["quarantine_reason"] = "same_scope_opposite_directive"
    candidate["status"] = "quarantined"
    candidate["quarantine_reason"] = "same_scope_opposite_directive"
    memory["constraints"] = constraints
    return candidate, True


def upsert_constraint(
    memory: dict[str, Any],
    constraint: dict[str, Any],
) -> dict[str, Any]:
    constraints = list(memory.get("constraints") or [])
    normalized_id = str(constraint.get("normalized_id") or "")
    existing = next(
        (item for item in constraints if str(item.get("normalized_id") or "") == normalized_id),
        None,
    )
    if existing is None:
        constraint.setdefault("status", "active")
        constraint, _quarantined = quarantine_conflicting_constraints(memory, constraint)
        constraints.append(constraint)
    else:
        existing["recur_count"] = max(
            int(existing.get("recur_count") or 1),
            int(constraint.get("recur_count") or 1),
        )
        source_ids = {
            *list(existing.get("source_finding_ids") or []),
            *list(constraint.get("source_finding_ids") or []),
        }
        existing["source_finding_ids"] = sorted(source_ids)
        existing["severity"] = constraint.get("severity") or existing.get("severity")
        existing["directive"] = constraint.get("directive") or existing.get("directive")
    memory["constraints"] = constraints
    return memory
