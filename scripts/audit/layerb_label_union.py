#!/usr/bin/env python3
"""Build deterministic, key-addressable Layer B label-union inputs.

``attach`` is authoritative for the 2026-07-10 frozen union.  It preserves
each existing row and appends only ``grounding_key`` and ``fact_check_index``.
``derive`` is for later tau replays; it sorts every control pool before seeded
sampling.  It intentionally does not promise to reproduce the original ad-hoc
control sample used by the frozen union.
"""

from __future__ import annotations

import argparse
import random
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "scripts"))

from scripts.audit.layerb_label_common import (
    LabelJoinError,
    artifact_filename_from_union,
    atomic_write_json,
    canonical_json,
    derivation_rows,
    fact_check_index_from_key,
    load_corpus,
    read_json,
    resolve_derivation_indices,
    resolve_derivation_to_shadow,
    sha256_file,
    shadow_rows,
    structural_key_from_union,
    union_rows,
)

DEFAULT_CONTROL_SEED = 4913
DEFAULT_CONTROL_PER_STRATUM = 25


def _rows_document(
    document: Mapping[str, Any], rows: list[dict[str, Any]], *, mode: str, report: Mapping[str, Any]
) -> dict[str, Any]:
    """Retain the original envelope while making output mode/provenance explicit."""
    result = dict(document)
    result["rows"] = rows
    result["total_rows"] = len(rows)
    result["keying"] = {
        "mode": mode,
        "grounding_key_source": "scripts.audit.layerb_shadow._stable_grounding_key",
        "join_report": dict(report),
    }
    return result


def _duplicate_group_report(
    rows: Sequence[Mapping[str, Any]],
    resolutions: Mapping[tuple[str, str, str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        groups[structural_key_from_union(row)].append(index)
    reports: list[dict[str, Any]] = []
    for key, indexes in sorted(groups.items()):
        if len(indexes) < 2:
            continue
        resolution = resolutions.get(key)
        if resolution is None:
            raise LabelJoinError(f"duplicate union group has no shadow resolution: {canonical_json(list(key))}")
        reports.append(
            {
                "key": list(key),
                "count": len(indexes),
                "row_indexes": indexes,
                "resolution_basis": resolution.get("resolution_basis"),
                "identity_fields": list(resolution.get("identity_fields") or []),
            }
        )
    return reports


def attach_keys(
    union_document: Mapping[str, Any],
    derivation_document: Mapping[str, Any],
    shadow_document: Mapping[str, Any],
    *,
    corpus_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Attach shadow-runner grounding identities to every frozen union row.

    The union's source index is checked against all shared derivation fields;
    shadow rows are then joined by an exact multiset identity rather than their
    unrelated global list position.
    """
    selected = union_rows(union_document)
    derivations = derivation_rows(derivation_document)
    shadows = shadow_rows(shadow_document)
    corpus = load_corpus(corpus_dir)
    selected_derivation_indexes = resolve_derivation_indices(selected, derivations)
    derivation_to_shadow, group_resolutions = resolve_derivation_to_shadow(
        derivations,
        shadows,
        corpus,
        derivation_indexes=selected_derivation_indexes,
    )

    keyed_rows: list[dict[str, Any]] = []
    for row, derivation_index in zip(selected, selected_derivation_indexes, strict=True):
        shadow = derivation_to_shadow[derivation_index]
        grounding_key = shadow.get("grounding_key")
        if not isinstance(grounding_key, str):
            raise LabelJoinError(f"shadow row has no grounding_key at derivation index {derivation_index}")
        keyed = dict(row)
        keyed["grounding_key"] = grounding_key
        keyed["fact_check_index"] = fact_check_index_from_key(grounding_key)
        keyed_rows.append(keyed)

    grounding_keys = [str(row["grounding_key"]) for row in keyed_rows]
    if len(set(grounding_keys)) != len(grounding_keys):
        duplicates = sorted(key for key, count in Counter(grounding_keys).items() if count > 1)
        raise LabelJoinError("keyed union is not bijective; duplicate grounding keys=" + ", ".join(duplicates))
    duplicate_groups = _duplicate_group_report(selected, group_resolutions)
    report: dict[str, Any] = {
        "mode": "attach",
        "union_rows": len(selected),
        "derivation_rows": len(derivations),
        "shadow_rows": len(shadows),
        "matched_rows": len(keyed_rows),
        "grounding_keys_unique": len(set(grounding_keys)),
        "total": len(keyed_rows) == len(selected),
        "bijective": len(set(grounding_keys)) == len(keyed_rows),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_group_rows": sum(group["count"] for group in duplicate_groups),
        "duplicate_group_resolutions": duplicate_groups,
        "stable_key_recomputations": len(shadows),
        "documented_base_artifact_filenames": len({artifact_filename_from_union(row) for row in selected}),
    }
    return _rows_document(union_document, keyed_rows, mode="attach", report=report), report


def _category_names(row: Mapping[str, Any]) -> set[str]:
    categories: set[str] = set()
    v1 = row.get("v1_admissible") is True
    effective = row.get("v2_effective") is True
    if not v1 and effective:
        categories.add("recovered")
    if v1 and not effective:
        categories.add("regression")
    if row.get("v2_abstained") is True:
        categories.add("abstain")
    return categories


def _stable_pool_order(row: Mapping[str, Any], index: int) -> tuple[str, str, str, str, int]:
    key = structural_key_from_union(row)
    return (*key, index)


def derive_union(
    derivation_document: Mapping[str, Any],
    shadow_document: Mapping[str, Any],
    *,
    corpus_dir: Path,
    seed: int = DEFAULT_CONTROL_SEED,
    control_per_stratum: int = DEFAULT_CONTROL_PER_STRATUM,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Re-derive future label membership with deterministic stratified controls."""
    derivations = derivation_rows(derivation_document)
    shadows = shadow_rows(shadow_document)
    corpus = load_corpus(corpus_dir)
    derivation_to_shadow, _group_resolutions = resolve_derivation_to_shadow(derivations, shadows, corpus)
    selected_categories: dict[int, set[str]] = {
        index: _category_names(row) for index, row in enumerate(derivations) if _category_names(row)
    }
    selected_indexes = set(selected_categories)

    both_accept = [
        index
        for index, row in enumerate(derivations)
        if index not in selected_indexes and row.get("v1_admissible") is True and row.get("v2_effective") is True
    ]
    both_reject = [
        index
        for index, row in enumerate(derivations)
        if index not in selected_indexes
        and row.get("v1_admissible") is not True
        and row.get("v2_effective") is not True
    ]
    rng = random.Random(seed)
    selected_controls: dict[str, list[int]] = {}
    for name, pool in (("control_both_accept", both_accept), ("control_both_reject", both_reject)):
        ordered_pool = sorted(pool, key=lambda index: _stable_pool_order(derivations[index], index))
        if len(ordered_pool) < control_per_stratum:
            raise LabelJoinError(f"control pool {name} has {len(ordered_pool)} rows; requires {control_per_stratum}")
        sampled = sorted(
            rng.sample(ordered_pool, control_per_stratum),
            key=lambda index: _stable_pool_order(derivations[index], index),
        )
        selected_controls[name] = sampled
        for index in sampled:
            selected_categories.setdefault(index, set()).add(name)

    keyed_rows: list[dict[str, Any]] = []
    for index in sorted(selected_categories, key=lambda value: _stable_pool_order(derivations[value], value)):
        row = dict(derivations[index])
        shadow = derivation_to_shadow[index]
        grounding_key = str(shadow["grounding_key"])
        row["source_index"] = index
        row["union_categories"] = sorted(selected_categories[index])
        row["grounding_key"] = grounding_key
        row["fact_check_index"] = fact_check_index_from_key(grounding_key)
        keyed_rows.append(row)
    keys = [str(row["grounding_key"]) for row in keyed_rows]
    if len(keys) != len(set(keys)):
        raise LabelJoinError("fresh derivation selected duplicate grounding keys")
    category_counts = Counter(category for categories in selected_categories.values() for category in categories)
    report: dict[str, Any] = {
        "mode": "derive",
        "seed": seed,
        "control_per_stratum": control_per_stratum,
        "derivation_rows": len(derivations),
        "shadow_rows": len(shadows),
        "matched_rows": len(keyed_rows),
        "category_counts": dict(sorted(category_counts.items())),
        "control_pool_counts": {"control_both_accept": len(both_accept), "control_both_reject": len(both_reject)},
        "sampled_control_indexes": selected_controls,
        "mode_a_authoritative_for_frozen_cycle": True,
        "frozen_control_sample_reproduction_guaranteed": False,
    }
    document = {
        "kind": "qg-layer-b-label-union-input",
        "version": 2,
        "total_rows": len(keyed_rows),
        "control_seed": seed,
        "rows": keyed_rows,
        "keying": {
            "mode": "derive",
            "note": "Mode B is deterministic, but does not reproduce this cycle's ad-hoc frozen controls; Mode A is authoritative.",
            "join_report": report,
        },
    }
    return document, report


def _write_outputs(
    document: Mapping[str, Any], report: Mapping[str, Any], output: Path, report_path: Path | None
) -> None:
    atomic_write_json(output, document)
    atomic_write_json(report_path or output.with_name(output.stem + ".join-report.json"), report)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    for mode in ("attach", "derive"):
        command = subparsers.add_parser(mode)
        command.add_argument("--derivation", type=Path, required=True)
        command.add_argument("--shadow", type=Path, required=True)
        command.add_argument("--corpus-dir", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--report", type=Path)
    attach = subparsers.choices["attach"]
    attach.add_argument("--union", type=Path, required=True)
    derive = subparsers.choices["derive"]
    derive.add_argument("--seed", type=int, default=DEFAULT_CONTROL_SEED)
    derive.add_argument("--control-per-stratum", type=int, default=DEFAULT_CONTROL_PER_STRATUM)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    derivation_document = read_json(args.derivation)
    shadow_document = read_json(args.shadow)
    if args.mode == "attach":
        document, report = attach_keys(
            read_json(args.union), derivation_document, shadow_document, corpus_dir=args.corpus_dir
        )
    else:
        document, report = derive_union(
            derivation_document,
            shadow_document,
            corpus_dir=args.corpus_dir,
            seed=args.seed,
            control_per_stratum=args.control_per_stratum,
        )
    _write_outputs(document, report, args.output, args.report)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the CLI
    raise SystemExit(main())
