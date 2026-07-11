#!/usr/bin/env python3
"""Build deterministic, key-addressable Layer B label-union inputs.

``rederive`` is the authoritative path: it emits keys while walking the raw
corpus, proves that the 1,310 non-key records have not drifted, and hands those
keyed records to ``derive``.  ``derive`` selects the flag-derived union and
fresh deterministic controls without any shadow-row join.  ``select-all`` is
the separate, source-to-keyed-input path for a self-contained corpus whose
annotation set deliberately includes every row.

``attach`` remains available solely for inputs whose duplicate groups resolve
under its strict D2 invariant.  It is unsafe for ambiguous groups and is never
the authority for this frozen cycle.
"""

from __future__ import annotations

import argparse
import json
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

from scripts.audit.layerb_derivation import DEFAULT_TAU, derive_keyed_records
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
DEFAULT_REDERIVE_EXPECTED_ROWS = 1310
KEY_FIELDS = frozenset({"grounding_key", "fact_check_index"})
CATEGORY_NAMES = frozenset({"recovered", "regression", "abstain"})
CATEGORY_ORDER = ("recovered", "regression", "abstain", "control_both_accept", "control_both_reject")
SELECT_ALL_SOURCE_FIELDS = ("fixture", "claim", "excerpt", "grounding_key", "fact_check_index")


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
    """Attach keys only when every duplicate group resolves under D2.

    The union's source index is checked against all shared derivation fields;
    shadow rows are then joined by an exact multiset identity rather than their
    unrelated global list position.  This compatibility path is deliberately
    unsafe for ambiguous groups and must not be used as a frozen-cycle source
    of authority; use :func:`rederive_keyed_derivation` instead.
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
        "mode": "attach-unsafe-for-ambiguous-groups",
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
    return (
        _rows_document(union_document, keyed_rows, mode="attach-unsafe-for-ambiguous-groups", report=report),
        report,
    )


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


def _ordered_categories(categories: set[str]) -> list[str]:
    """Render flag categories in the frozen derivation's semantic order."""
    return [category for category in CATEGORY_ORDER if category in categories]


def _stable_pool_order(row: Mapping[str, Any], index: int) -> tuple[str, str, str, str, int]:
    key = structural_key_from_union(row)
    return (*key, index)


def _validate_keyed_derivation_rows(rows: Sequence[Mapping[str, Any]], *, operation: str) -> list[str]:
    """Require source-emitted keys before any selection mode can proceed."""
    for row in rows:
        grounding_key = row.get("grounding_key")
        if not isinstance(grounding_key, str) or not grounding_key:
            raise LabelJoinError(f"{operation} requires source-keyed derivation records")
        if row.get("fact_check_index") != fact_check_index_from_key(grounding_key):
            raise LabelJoinError(f"keyed derivation fact_check_index is invalid: {grounding_key!r}")
    grounding_keys = [str(row["grounding_key"]) for row in rows]
    if len(grounding_keys) != len(set(grounding_keys)):
        raise LabelJoinError("keyed derivation contains duplicate grounding keys")
    return grounding_keys


def _without_key_fields(row: Mapping[str, Any]) -> dict[str, Any]:
    """Project the legacy record shape for full-field multiset comparison."""
    return {key: value for key, value in row.items() if key not in KEY_FIELDS}


def _canonical_row_multiset(rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(canonical_json(_without_key_fields(row)) for row in rows)


def _counter_rows(counter: Counter[str]) -> list[dict[str, Any]]:
    """Render a compact, deterministic Counter difference for failure output."""
    return [
        {"count": count, "row": json.loads(row)}
        for row, count in sorted(counter.items())
        if count
    ]


def assert_no_drift(
    regenerated_rows: Sequence[Mapping[str, Any]], frozen_derivation_document: Mapping[str, Any]
) -> dict[str, Any]:
    """Hard-fail unless keyed source regeneration matches every frozen field.

    Only the two source-emitted identity fields are excluded.  Every other
    field—including booleans, float values, and nullable gold truth—is compared
    as canonical JSON, with multiplicity retained.
    """
    frozen_rows = derivation_rows(frozen_derivation_document)
    regenerated_counter = _canonical_row_multiset(regenerated_rows)
    frozen_counter = _canonical_row_multiset(frozen_rows)
    regenerated_only = regenerated_counter - frozen_counter
    frozen_only = frozen_counter - regenerated_counter
    report = {
        "mode": "rederive-at-source",
        "excluded_key_fields": sorted(KEY_FIELDS),
        "regenerated_rows": len(regenerated_rows),
        "frozen_rows": len(frozen_rows),
        "regenerated_distinct_tuples": len(regenerated_counter),
        "frozen_distinct_tuples": len(frozen_counter),
        "symmetric_difference": {
            "regenerated_only": _counter_rows(regenerated_only),
            "frozen_only": _counter_rows(frozen_only),
        },
        "no_drift": not regenerated_only and not frozen_only,
    }
    if not report["no_drift"]:
        raise LabelJoinError("rederive no-drift proof failed: " + canonical_json(report))
    return report


def rederive_keyed_derivation(
    *,
    artifacts_dir: Path,
    fixtures_dir: Path,
    frozen_derivation_document: Mapping[str, Any],
    tau: float = DEFAULT_TAU,
    expected_rows: int = DEFAULT_REDERIVE_EXPECTED_ROWS,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Emit a keyed derivation directly from raw source and prove no drift."""
    records = derive_keyed_records(artifacts_dir, fixtures_dir=fixtures_dir, tau=tau)
    if len(records) != expected_rows:
        raise LabelJoinError(f"rederive emitted {len(records)} rows; expected {expected_rows}")
    keys = [record.get("grounding_key") for record in records]
    if not all(isinstance(key, str) and key for key in keys) or len(set(keys)) != len(keys):
        raise LabelJoinError("rederive must emit one non-empty grounding_key per source record")
    for record in records:
        key = str(record["grounding_key"])
        if record.get("fact_check_index") != fact_check_index_from_key(key):
            raise LabelJoinError(f"rederive fact_check_index does not match grounding_key: {key!r}")
    proof = assert_no_drift(records, frozen_derivation_document)
    report = {
        **proof,
        "tau": tau,
        "expected_rows": expected_rows,
        "grounding_keys_unique": len(set(keys)),
        "keyed_at_source": True,
    }
    document = {
        "kind": "qg-layer-b-keyed-union-derivation",
        "version": 1,
        "total_rows": len(records),
        "records": records,
        "metadata": {
            "tau": tau,
            "artifacts_dir": str(artifacts_dir),
            "fixtures_dir": str(fixtures_dir),
            "keying": "source-artifact-path-plus-fact-check-index",
            "no_drift": True,
        },
        "keying": {"mode": "rederive-at-source", "join_report": report},
    }
    return document, report


def _category_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in rows
        if CATEGORY_NAMES.intersection(row.get("union_categories") or [])
    ]


def _assert_category_membership(
    category_rows: Sequence[Mapping[str, Any]], frozen_union_document: Mapping[str, Any]
) -> dict[str, Any]:
    frozen_category_rows = _category_rows(union_rows(frozen_union_document))
    selected_counter = _canonical_row_multiset(category_rows)
    frozen_counter = _canonical_row_multiset(frozen_category_rows)
    selected_only = selected_counter - frozen_counter
    frozen_only = frozen_counter - selected_counter
    report = {
        "category_rows": len(category_rows),
        "frozen_category_rows": len(frozen_category_rows),
        "category_multiset_equal": not selected_only and not frozen_only,
        "category_symmetric_difference": {
            "selected_only": _counter_rows(selected_only),
            "frozen_only": _counter_rows(frozen_only),
        },
    }
    if not report["category_multiset_equal"]:
        raise LabelJoinError("flag-derived category membership drifted: " + canonical_json(report))
    return report


def derive_union(
    derivation_document: Mapping[str, Any],
    *,
    frozen_union_document: Mapping[str, Any],
    seed: int = DEFAULT_CONTROL_SEED,
    control_per_stratum: int = DEFAULT_CONTROL_PER_STRATUM,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Select the union directly from keyed source records and fresh controls."""
    derivations = derivation_rows(derivation_document)
    if control_per_stratum < 1:
        raise LabelJoinError("control_per_stratum must be positive")
    _validate_keyed_derivation_rows(derivations, operation="derive")
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
        row["source_index"] = index
        row["union_categories"] = _ordered_categories(selected_categories[index])
        keyed_rows.append(row)
    category_membership = _assert_category_membership(_category_rows(keyed_rows), frozen_union_document)
    category_counts = Counter(category for categories in selected_categories.values() for category in categories)
    report: dict[str, Any] = {
        "mode": "derive-from-keyed-rederive",
        "seed": seed,
        "control_per_stratum": control_per_stratum,
        "keyed_derivation_rows": len(derivations),
        "matched_rows": len(keyed_rows),
        "category_counts": dict(sorted(category_counts.items())),
        "control_pool_counts": {"control_both_accept": len(both_accept), "control_both_reject": len(both_reject)},
        "sampled_control_indexes": selected_controls,
        "control_resampled": True,
        "category_membership": category_membership,
        "source_keyed_derivation_required": True,
        "frozen_control_sample_reproduction_guaranteed": False,
    }
    document = {
        "kind": "qg-layer-b-label-union-input",
        "version": 3,
        "total_rows": len(keyed_rows),
        "control_seed": seed,
        "rows": keyed_rows,
        "keying": {
            "mode": "derive-from-keyed-rederive",
            "note": "Category membership is source-keyed and frozen-verified; controls were freshly resampled.",
            "control_resampled": True,
            "join_report": report,
        },
    }
    return document, report


def select_all_corpus(artifacts_dir: Path, *, tau: float = DEFAULT_TAU) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build a minimal keyed input that selects every raw corpus fact check.

    This intentionally does not accept a frozen derivation, flag categories,
    control seed, or fixture truth lookup. It shares the normal raw source
    walker so every grounding key is emitted by :mod:`layerb_keys` at the same
    point as the phase-1 shadow runner.
    """
    derivations = derive_keyed_records(artifacts_dir, fixtures_dir=None, tau=tau)
    grounding_keys = _validate_keyed_derivation_rows(derivations, operation="select-all")
    keyed_rows: list[dict[str, Any]] = []
    for index in sorted(range(len(derivations)), key=lambda value: (str(derivations[value]["grounding_key"]), value)):
        source = derivations[index]
        missing = [field for field in SELECT_ALL_SOURCE_FIELDS if field not in source or source[field] in (None, "")]
        if missing:
            raise LabelJoinError(f"select-all source row lacks required fields at index {index}: {', '.join(missing)}")
        row = {field: source[field] for field in SELECT_ALL_SOURCE_FIELDS}
        row["source_index"] = index
        row["union_categories"] = []
        keyed_rows.append(row)
    report: dict[str, Any] = {
        "mode": "select-all-from-source-artifacts",
        "selection": "all-corpus-rows",
        "artifacts_dir": str(artifacts_dir),
        "tau": tau,
        "keyed_derivation_rows": len(derivations),
        "matched_rows": len(keyed_rows),
        "grounding_keys_unique": len(set(grounding_keys)),
        "source_keyed_derivation_required": True,
        "fixture_truth_lookup_used": False,
        "flag_categories_used": False,
        "control_sampling_used": False,
        "control_resampled": False,
        "frozen_derivation_verified": False,
        "projected_row_fields": [*SELECT_ALL_SOURCE_FIELDS, "source_index", "union_categories"],
    }
    document = {
        "kind": "qg-layer-b-label-union-input",
        "version": 3,
        "total_rows": len(keyed_rows),
        "rows": keyed_rows,
        "keying": {
            "mode": "select-all-from-source-artifacts",
            "note": "Every source-keyed corpus row is selected; no flags, controls, or fixture truth labels are used.",
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
    for mode in ("attach", "derive", "rederive"):
        command = subparsers.add_parser(mode)
        command.add_argument("--derivation", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--report", type=Path)
    attach = subparsers.choices["attach"]
    attach.add_argument("--union", type=Path, required=True)
    attach.add_argument("--shadow", type=Path, required=True)
    attach.add_argument("--corpus-dir", type=Path, required=True)
    derive = subparsers.choices["derive"]
    derive.add_argument("--frozen-union", type=Path, required=True)
    derive.add_argument("--seed", type=int, default=DEFAULT_CONTROL_SEED)
    derive.add_argument("--control-per-stratum", type=int, default=DEFAULT_CONTROL_PER_STRATUM)
    rederive = subparsers.choices["rederive"]
    rederive.add_argument("--artifacts-dir", type=Path, required=True)
    rederive.add_argument("--fixtures-dir", type=Path, default=Path("tests/fixtures/qg_bakeoff"))
    rederive.add_argument("--tau", type=float, default=DEFAULT_TAU)
    rederive.add_argument("--expected-rows", type=int, default=DEFAULT_REDERIVE_EXPECTED_ROWS)
    select_all = subparsers.add_parser("select-all")
    select_all.add_argument("--artifacts-dir", type=Path, required=True)
    select_all.add_argument("--output", type=Path, required=True)
    select_all.add_argument("--report", type=Path)
    select_all.add_argument("--tau", type=float, default=DEFAULT_TAU)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.mode == "select-all":
        document, report = select_all_corpus(args.artifacts_dir, tau=args.tau)
    else:
        derivation_document = read_json(args.derivation)
        if args.mode == "attach":
            document, report = attach_keys(
                read_json(args.union), derivation_document, read_json(args.shadow), corpus_dir=args.corpus_dir
            )
        elif args.mode == "derive":
            document, report = derive_union(
                derivation_document,
                frozen_union_document=read_json(args.frozen_union),
                seed=args.seed,
                control_per_stratum=args.control_per_stratum,
            )
        else:
            document, report = rederive_keyed_derivation(
                artifacts_dir=args.artifacts_dir,
                fixtures_dir=args.fixtures_dir,
                frozen_derivation_document=derivation_document,
                tau=args.tau,
                expected_rows=args.expected_rows,
            )
            report["frozen_derivation"] = {"path": str(args.derivation), "sha256": sha256_file(args.derivation)}
            document["metadata"]["frozen_derivation"] = dict(report["frozen_derivation"])
    _write_outputs(document, report, args.output, args.report)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the CLI
    raise SystemExit(main())
