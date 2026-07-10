#!/usr/bin/env python3
"""Shared deterministic primitives for the offline Layer B label tools.

This module intentionally contains only stdlib code plus the already-offline
Layer B shadow helper.  It is not imported by the QG runtime.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.audit.layerb_shadow import _stable_grounding_key


class LabelJoinError(ValueError):
    """A frozen-input identity or accounting invariant failed."""


SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
FACT_CHECK_INDEX_RE = re.compile(r"#fact_checks\[(\d+)\]::")


def canonical_json(value: Any) -> str:
    """Return a stable JSON representation used only for deterministic keys."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    """Hash immutable source bytes without interpreting their encoding."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LabelJoinError(f"cannot read JSON input {path}: {exc}") from exc


def atomic_write_text(path: Path, text: str) -> None:
    """Atomically replace one output; a partial file is never publishable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def atomic_write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    atomic_write_text(
        path,
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
    )


def _dict_prefix(value: str) -> tuple[str, str]:
    """Split a legacy ``{...}/tooled`` seat arm without evaluating its suffix."""
    start = value.find("{")
    if start == -1:
        raise LabelJoinError(f"seat_arm has no dictionary prefix: {value!r}")
    depth = 0
    quote: str | None = None
    escaped = False
    for index, character in enumerate(value[start:], start=start):
        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if character in {"'", '"'}:
            quote = character
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return value[start : index + 1], value[index + 1 :]
    raise LabelJoinError(f"seat_arm has an unclosed dictionary prefix: {value!r}")


def parse_seat_arm(value: Any) -> tuple[dict[str, Any], str]:
    """Parse the documented stringified seat metadata and its trailing arm."""
    if not isinstance(value, str):
        raise LabelJoinError(f"seat_arm must be a string, got {type(value).__name__}")
    prefix, suffix = _dict_prefix(value)
    try:
        parsed = ast.literal_eval(prefix)
    except (SyntaxError, ValueError) as exc:
        raise LabelJoinError(f"seat_arm dictionary cannot be parsed: {value!r}") from exc
    if not isinstance(parsed, dict):
        raise LabelJoinError("seat_arm dictionary prefix did not parse to an object")
    return parsed, suffix


def artifact_filename_from_union(row: Mapping[str, Any]) -> str:
    """Return the documented base artifact filename from a frozen union row.

    Historical replays may add a run suffix (for example ``__r2``).  The
    keyed shadow record remains authoritative in that case; this helper keeps
    the documented base identity available for fresh future derivations.
    """
    seat, _arm = parse_seat_arm(row.get("seat_arm"))
    pin_slug = seat.get("pin_slug")
    fixture = row.get("fixture")
    if not isinstance(pin_slug, str) or not pin_slug or not isinstance(fixture, str) or not fixture:
        raise LabelJoinError("seat_arm.pin_slug and fixture are required for an artifact filename")
    return f"{pin_slug}__{fixture}.json"


def fact_check_index_from_key(grounding_key: str) -> int:
    match = FACT_CHECK_INDEX_RE.search(grounding_key)
    if match is None:
        raise LabelJoinError(f"grounding_key has no fact-check index: {grounding_key!r}")
    return int(match.group(1))


def _rows(document: Any, name: str) -> list[dict[str, Any]]:
    if isinstance(document, list):
        rows = document
    elif isinstance(document, Mapping):
        rows = document.get("rows")
        if not isinstance(rows, list):
            rows = document.get("records")
    else:
        rows = None
    if not isinstance(rows, list) or not all(isinstance(row, Mapping) for row in rows):
        raise LabelJoinError(f"{name} must contain a rows/records list of objects")
    return [dict(row) for row in rows]


def union_rows(document: Any) -> list[dict[str, Any]]:
    return _rows(document, "union input")


def derivation_rows(document: Any) -> list[dict[str, Any]]:
    return _rows(document, "union derivation")


def shadow_rows(document: Any) -> list[dict[str, Any]]:
    return _rows(document, "phase1 shadow")


def load_corpus(corpus_dir: Path) -> dict[str, dict[str, Any]]:
    """Load the immutable raw corpus by filename, rejecting malformed inputs."""
    if not corpus_dir.is_dir():
        raise LabelJoinError(f"corpus directory does not exist: {corpus_dir}")
    corpus: dict[str, dict[str, Any]] = {}
    for path in sorted(corpus_dir.glob("*.json")):
        document = read_json(path)
        if isinstance(document, Mapping):
            corpus[path.name] = dict(document)
    if not corpus:
        raise LabelJoinError(f"corpus contains no JSON artifacts: {corpus_dir}")
    return corpus


def artifact_fact_check(
    shadow: Mapping[str, Any], corpus: Mapping[str, Mapping[str, Any]]
) -> tuple[Path, dict[str, Any]]:
    """Resolve one shadow row to its immutable artifact and fact-check object."""
    artifact_name = shadow.get("artifact")
    grounding_key = shadow.get("grounding_key")
    if not isinstance(artifact_name, str) or not isinstance(grounding_key, str):
        raise LabelJoinError("shadow record requires artifact and grounding_key strings")
    artifact = corpus.get(artifact_name)
    if artifact is None:
        raise LabelJoinError(f"shadow artifact is absent from corpus: {artifact_name}")
    payload = artifact.get("payload")
    fact_checks = payload.get("fact_checks") if isinstance(payload, Mapping) else None
    index = fact_check_index_from_key(grounding_key)
    if (
        not isinstance(fact_checks, list)
        or not (0 <= index < len(fact_checks))
        or not isinstance(fact_checks[index], Mapping)
    ):
        raise LabelJoinError(f"missing fact check {index} in corpus artifact {artifact_name}")
    recomputed = _stable_grounding_key(Path(artifact_name), index, fact_checks[index])
    if recomputed != grounding_key:
        raise LabelJoinError(
            f"stable grounding key mismatch for {artifact_name} fact_checks[{index}]: "
            f"shadow={grounding_key!r} recomputed={recomputed!r}"
        )
    return Path(artifact_name), dict(fact_checks[index])


def excerpt_from_fact_check(fact_check: Mapping[str, Any]) -> str:
    grounding = fact_check.get("grounding")
    return str(grounding.get("evidence_excerpt") or "") if isinstance(grounding, Mapping) else ""


def structural_key_from_union(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    seat, _arm = parse_seat_arm(row.get("seat_arm"))
    return (
        canonical_json(seat),
        str(row.get("fixture") or ""),
        str(row.get("claim") or ""),
        str(row.get("excerpt") or ""),
    )


def structural_key_from_shadow(
    shadow: Mapping[str, Any], corpus: Mapping[str, Mapping[str, Any]]
) -> tuple[str, str, str, str]:
    _path, fact_check = artifact_fact_check(shadow, corpus)
    metadata = shadow.get("seat_metadata")
    if not isinstance(metadata, Mapping):
        raise LabelJoinError(f"shadow record has no seat_metadata for {shadow.get('grounding_key')!r}")
    return (
        canonical_json(dict(metadata)),
        str(shadow.get("fixture") or ""),
        str(shadow.get("claim") or ""),
        excerpt_from_fact_check(fact_check),
    )


def render_key(key: Sequence[str]) -> str:
    return canonical_json(list(key))


def _derivation_comparable(row: Mapping[str, Any]) -> dict[str, Any]:
    """Discard only union membership metadata for an exact source-index check."""
    return {key: value for key, value in row.items() if key not in {"union_categories", "source_index"}}


def resolve_derivation_indices(
    selected_rows: Sequence[Mapping[str, Any]], derivations: Sequence[Mapping[str, Any]]
) -> list[int]:
    """Resolve union rows to derivation rows without a shadow positional join.

    The frozen union deliberately retains ``source_index`` as a reference to
    the derivation list.  It is checked against every shared field rather than
    trusted blindly.  Synthetic/future rows without that field use an exact
    multiset key and fail loudly if a duplicate cannot be distinguished.
    """
    by_key: dict[tuple[str, str, str, str], list[int]] = defaultdict(list)
    for index, row in enumerate(derivations):
        by_key[structural_key_from_union(row)].append(index)
    used: set[int] = set()
    resolved: list[int] = []
    missing: list[str] = []
    ambiguous: list[str] = []
    for row in selected_rows:
        source_index = row.get("source_index")
        if isinstance(source_index, int) and 0 <= source_index < len(derivations):
            candidate = derivations[source_index]
            if _derivation_comparable(row) == _derivation_comparable(candidate) and source_index not in used:
                used.add(source_index)
                resolved.append(source_index)
                continue
        key = structural_key_from_union(row)
        candidates = [index for index in by_key.get(key, []) if index not in used]
        if not candidates:
            missing.append(render_key(key))
        elif len(candidates) != 1:
            ambiguous.append(render_key(key))
        else:
            used.add(candidates[0])
            resolved.append(candidates[0])
    if missing or ambiguous:
        details: list[str] = []
        if missing:
            details.append("missing keys=" + ", ".join(sorted(set(missing))))
        if ambiguous:
            details.append("ambiguous keys=" + ", ".join(sorted(set(ambiguous))))
        raise LabelJoinError("union-to-derivation exact join failed: " + "; ".join(details))
    return resolved


def resolve_derivation_to_shadow(
    derivations: Sequence[Mapping[str, Any]],
    shadows: Sequence[Mapping[str, Any]],
    corpus: Mapping[str, Mapping[str, Any]],
) -> dict[int, dict[str, Any]]:
    """Create a total deterministic multiset bijection to unordered shadow rows.

    Group membership is an exact tuple of seat metadata, fixture, claim, and
    raw evidence excerpt.  Only ties *within that exact group* are ordered by
    stable derivation index and immutable grounding key.  This never relies on
    the (known-different) global iteration order of the two frozen reports.
    """
    derivation_groups: dict[tuple[str, str, str, str], list[int]] = defaultdict(list)
    shadow_groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(derivations):
        derivation_groups[structural_key_from_union(row)].append(index)
    for shadow in shadows:
        shadow_groups[structural_key_from_shadow(shadow, corpus)].append(dict(shadow))

    missing = sorted(render_key(key) for key in derivation_groups.keys() - shadow_groups.keys())
    extra = sorted(render_key(key) for key in shadow_groups.keys() - derivation_groups.keys())
    count_mismatches = sorted(
        render_key(key)
        for key in derivation_groups.keys() & shadow_groups.keys()
        if len(derivation_groups[key]) != len(shadow_groups[key])
    )
    if missing or extra or count_mismatches:
        details: list[str] = []
        if missing:
            details.append("missing shadow keys=" + ", ".join(missing))
        if extra:
            details.append("extra shadow keys=" + ", ".join(extra))
        if count_mismatches:
            details.append("ambiguous cardinality keys=" + ", ".join(count_mismatches))
        raise LabelJoinError("derivation-to-shadow bijection failed: " + "; ".join(details))

    mapped: dict[int, dict[str, Any]] = {}
    seen_keys: set[str] = set()
    for key in sorted(derivation_groups):
        indexes = sorted(derivation_groups[key])
        candidates = sorted(shadow_groups[key], key=lambda row: str(row.get("grounding_key") or ""))
        for index, shadow in zip(indexes, candidates, strict=True):
            grounding_key = shadow.get("grounding_key")
            if not isinstance(grounding_key, str) or grounding_key in seen_keys:
                raise LabelJoinError(f"shadow grounding keys are not unique: {grounding_key!r}")
            seen_keys.add(grounding_key)
            mapped[index] = shadow
    if len(mapped) != len(derivations) or len(seen_keys) != len(shadows):
        raise LabelJoinError(
            f"derivation-to-shadow mapping is not total/bijective: derivation={len(derivations)} "
            f"mapped={len(mapped)} shadow={len(shadows)}"
        )
    return mapped
