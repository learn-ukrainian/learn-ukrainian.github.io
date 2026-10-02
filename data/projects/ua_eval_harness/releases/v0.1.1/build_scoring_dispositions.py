#!/usr/bin/env python3
"""Build or verify fail-closed calque scoring dispositions.

UA-GEC's ``F/Calque`` tag is preserved as upstream provenance. It is not
treated as automatic benchmark adjudication. Style-marker collisions are
reported separately, bounded dictionary receipts may set their benchmark
disposition, and unresolved heritage/register cases fail closed.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.rag.vesum_reingest import (
    iter_analyses,
    load_lock,
    marker_rows,
    verify_pipeline_identity,
    verify_release_asset,
)

SCHEMA_VERSION = "ua_eval_scoring_dispositions.v1"
DEFAULT_CONFIG = ROOT / "data/projects/ua_eval_harness/scoring_disposition_config.json"
DEFAULT_MANIFEST = ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json"
DEFAULT_OUTPUT = ROOT / "data/projects/ua_eval_harness/scoring_dispositions_v1.json"
ROW_LAYOUT = [
    "item_id",
    "annotator_index",
    "start",
    "end",
    "upstream_tag",
    "replacement",
    "source_span",
    "disposition",
    "headline_calque",
    "reason",
    "evidence",
]
VALID_DISPOSITIONS = frozenset(
    {
        "HEADLINE_CALQUE",
        "REGIONAL_STANDARDIZATION",
        "REGISTER_STANDARDIZATION",
        "HERITAGE_CONFLICT",
        "CONTESTED",
    }
)
POLICY_DISPOSITION_KEYS = (
    "bad_marker",
    "arch_coll_dialect_without_contextual_adjudication",
    "rare_or_slang_without_contextual_adjudication",
    "confirmed_authentic_regional_or_dialect",
    "confirmed_colloquial_or_register_standardization",
    "unflagged_upstream_annotation",
)


class DispositionError(ValueError):
    """A disposition input, record, or receipt is invalid."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DispositionError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DispositionError(f"expected JSON object in {path}")
    return value


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise DispositionError(f"cannot hash {path}: {exc}") from exc


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validated_policy(policy: Mapping[str, Any]) -> tuple[dict[str, str], frozenset[str]]:
    dispositions: dict[str, str] = {}
    for key in POLICY_DISPOSITION_KEYS:
        status = str(policy.get(key, ""))
        if status not in VALID_DISPOSITIONS:
            raise DispositionError(f"policy {key} has invalid disposition: {status!r}")
        dispositions[key] = status
    raw_headline = policy.get("headline_includes")
    if not isinstance(raw_headline, list) or not raw_headline:
        raise DispositionError("policy headline_includes must be a non-empty array")
    headline_includes = frozenset(str(status) for status in raw_headline)
    if not headline_includes <= VALID_DISPOSITIONS:
        raise DispositionError("policy headline_includes contains an invalid disposition")
    if policy.get("fail_closed") is not True:
        raise DispositionError("disposition policy must fail closed")
    return dispositions, headline_includes


def decide_disposition(
    *,
    source_span: Sequence[str],
    attested: bool,
    style_markers: Sequence[str],
    policy: Mapping[str, Any],
    contextual_disposition: str | None = None,
    contextual_reason: str | None = None,
) -> tuple[str, bool, str]:
    """Return the benchmark disposition without changing the upstream tag."""
    policy_dispositions, headline_includes = _validated_policy(policy)
    if contextual_disposition is not None:
        if contextual_disposition not in set(policy_dispositions.values()):
            raise DispositionError(f"unsupported contextual disposition: {contextual_disposition}")
        if not contextual_reason:
            raise DispositionError("contextual disposition requires a reason")
        return (
            contextual_disposition,
            contextual_disposition in headline_includes,
            contextual_reason,
        )
    marker_set = set(style_markers)
    if marker_set & {"arch", "coll", "dialect"}:
        status = policy_dispositions["arch_coll_dialect_without_contextual_adjudication"]
        return (
            status,
            status in headline_includes,
            "pinned stylistic marker evidence lacks contextual adjudication; fail closed",
        )
    if marker_set & {"rare", "slang"}:
        status = policy_dispositions["rare_or_slang_without_contextual_adjudication"]
        return (
            status,
            status in headline_includes,
            "pinned register evidence does not adjudicate calque status; fail closed",
        )
    if marker_set == {"bad"}:
        status = policy_dispositions["bad_marker"]
        return (
            status,
            status in headline_includes,
            "the bad marker supports nonstandard-form status but does not replace the upstream calque label",
        )
    if marker_set:
        raise DispositionError(f"unhandled style markers: {sorted(marker_set)}")
    del attested, source_span
    status = policy_dispositions["unflagged_upstream_annotation"]
    return (
        status,
        status in headline_includes,
        "no reproducible dialect/heritage conflict candidate was detected",
    )


def _calque_records(manifest: Mapping[str, Any], upstream_tag: str) -> list[dict[str, Any]]:
    layouts = manifest["record_layouts"]
    item_layout = layouts["item"]
    reference_layout = layouts["reference"]
    edit_layout = layouts["edit"]
    records: list[dict[str, Any]] = []
    for raw_item in manifest["items"]:
        item = dict(zip(item_layout, raw_item, strict=True))
        source_tokens = str(item["source"]).split()
        for raw_reference in item["references"]:
            reference = dict(zip(reference_layout, raw_reference, strict=True))
            for raw_edit in reference["edits"]:
                edit = dict(zip(edit_layout, raw_edit, strict=True))
                if edit["tag"] != upstream_tag:
                    continue
                start, end = int(edit["start"]), int(edit["end"])
                records.append(
                    {
                        "item_id": str(item["id"]),
                        "annotator_index": str(reference["annotator_index"]),
                        "start": start,
                        "end": end,
                        "upstream_tag": str(edit["tag"]),
                        "replacement": str(edit["replacement"]),
                        "source_span": source_tokens[start:end],
                    }
                )
    return records


def _vesum_evidence(
    asset_path: Path,
    *,
    forms: set[str],
    style_markers: set[str],
) -> dict[str, dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {
        form: {"analysis_count": 0, "style_markers": set(), "receipt_rows": []} for form in forms
    }
    try:
        with bz2.open(asset_path, "rt", encoding="utf-8") as source:
            for analysis in iter_analyses(source):
                form = analysis.word_form.casefold()
                if form not in evidence:
                    continue
                raw_markers = set(analysis.tags.split(":"))
                normalized_markers = marker_rows(analysis.tags, analysis.source_comment)
                markers = sorted(
                    (raw_markers & style_markers)
                    | {marker for marker, _origin, _marker_class in normalized_markers if marker in style_markers}
                )
                value = evidence[form]
                value["analysis_count"] += 1
                value["style_markers"].update(markers)
                value["receipt_rows"].append(
                    [
                        analysis.entry_id,
                        analysis.lemma,
                        analysis.tags,
                        analysis.source_comment,
                        analysis.source_location,
                        markers,
                    ]
                )
    except OSError as exc:
        raise DispositionError(f"cannot open VESUM release asset: {exc}") from exc
    for value in evidence.values():
        rows = value.pop("receipt_rows")
        value["style_markers"] = sorted(value["style_markers"])
        value["analysis_receipt_sha256"] = _canonical_sha256(rows) if rows else None
    return evidence


def build_dispositions(
    *,
    manifest: Mapping[str, Any],
    config: Mapping[str, Any],
    asset_path: Path,
) -> dict[str, Any]:
    """Build all F/Calque annotation dispositions from pinned evidence."""
    if config.get("schema_version") != "ua_eval_scoring_disposition_config.v1":
        raise DispositionError("unsupported disposition config schema")
    if manifest.get("manifest_id") != config.get("manifest_id"):
        raise DispositionError("held-out manifest ID does not match disposition config")
    if manifest["integrity"]["payload_sha256"] != config.get("manifest_payload_sha256"):
        raise DispositionError("held-out manifest payload does not match disposition config")
    policy = config.get("policy")
    if not isinstance(policy, Mapping):
        raise DispositionError("disposition policy is missing")
    _validated_policy(policy)
    evidence_config = config["evidence"]
    lock_path = ROOT / str(evidence_config["source_lock"])
    parser_path = ROOT / str(evidence_config["parser"])
    if _sha256(lock_path) != evidence_config["source_lock_sha256"]:
        raise DispositionError("VESUM source lock hash mismatch")
    if _sha256(parser_path) != evidence_config["parser_sha256"]:
        raise DispositionError("VESUM parser hash mismatch")
    lock = load_lock(lock_path)
    verify_pipeline_identity(lock)
    verify_release_asset(asset_path, lock)
    release_asset = lock["release_asset"]
    if release_asset["sha256"] != evidence_config["release_asset_sha256"]:
        raise DispositionError("VESUM release asset hash does not match disposition config")

    upstream_tag = str(config["upstream_tag"])
    records = _calque_records(manifest, upstream_tag)
    forms = {token.casefold() for record in records for token in record["source_span"]}
    style_markers = set(evidence_config["style_markers"])
    evidence_by_form = _vesum_evidence(
        asset_path,
        forms=forms,
        style_markers=style_markers,
    )
    adjudications: dict[tuple[str, int, int, tuple[str, ...]], Mapping[str, Any]] = {}
    for adjudication in config.get("contextual_adjudications", []):
        key = (
            str(adjudication["item_id"]),
            int(adjudication["start"]),
            int(adjudication["end"]),
            tuple(str(token) for token in adjudication["source_span"]),
        )
        if key in adjudications:
            raise DispositionError(f"duplicate contextual adjudication: {key}")
        adjudications[key] = adjudication

    rows: list[list[Any]] = []
    counts: Counter[str] = Counter()
    item_sets: dict[str, set[str]] = {status: set() for status in VALID_DISPOSITIONS}
    style_span_markers: dict[tuple[str, int, int, tuple[str, ...]], set[str]] = {}
    matched_adjudications: set[tuple[str, int, int, tuple[str, ...]]] = set()
    for record in records:
        form_evidence = [
            {
                "surface": token,
                **evidence_by_form[token.casefold()],
            }
            for token in record["source_span"]
        ]
        markers = sorted({marker for value in form_evidence for marker in value["style_markers"]})
        span_key = (
            record["item_id"],
            record["start"],
            record["end"],
            tuple(record["source_span"]),
        )
        if markers:
            style_span_markers.setdefault(span_key, set()).update(markers)
        adjudication = adjudications.get(span_key)
        if adjudication is not None:
            matched_adjudications.add(span_key)
        status, headline, reason = decide_disposition(
            source_span=record["source_span"],
            attested=bool(record["source_span"]) and all(value["analysis_count"] > 0 for value in form_evidence),
            style_markers=markers,
            policy=policy,
            contextual_disposition=(str(adjudication["disposition"]) if adjudication is not None else None),
            contextual_reason=(str(adjudication["reason"]) if adjudication is not None else None),
        )
        counts[status] += 1
        item_sets[status].add(record["item_id"])
        rows.append(
            [
                record["item_id"],
                record["annotator_index"],
                record["start"],
                record["end"],
                record["upstream_tag"],
                record["replacement"],
                record["source_span"],
                status,
                headline,
                reason,
                {
                    "source": "dict_uk/VESUM",
                    "exact_form_evidence": form_evidence,
                    "contextual_adjudication": (
                        {
                            "disposition": adjudication["disposition"],
                            "evidence": adjudication["evidence"],
                        }
                        if adjudication is not None
                        else None
                    ),
                },
            ]
        )
    unused_adjudications = sorted(set(adjudications) - matched_adjudications)
    if unused_adjudications:
        raise DispositionError(f"contextual adjudication does not match a manifest record: {unused_adjudications[0]}")
    style_annotation_count = sum(
        bool({marker for value in row[-1]["exact_form_evidence"] for marker in value["style_markers"]}) for row in rows
    )
    style_marker_span_counts: Counter[str] = Counter()
    for markers in style_span_markers.values():
        style_marker_span_counts.update(markers)

    result = {
        "schema_version": SCHEMA_VERSION,
        "disposition_id": config["disposition_id"],
        "manifest_id": manifest["manifest_id"],
        "manifest_payload_sha256": manifest["integrity"]["payload_sha256"],
        "record_layout": ROW_LAYOUT,
        "semantics": {
            "upstream_tag_preserved": True,
            "upstream_tag_meaning": "UA-GEC standardization label",
            "benchmark_disposition_meaning": "separate calque scoring decision",
            "headline_includes": policy["headline_includes"],
            "fail_closed": True,
            "activation_dependency": policy["activation_dependency"],
            "contextual_adjudication": policy["contextual_adjudication"],
        },
        "evidence_receipt": {
            "source_lock": evidence_config["source_lock"],
            "source_lock_sha256": evidence_config["source_lock_sha256"],
            "parser": evidence_config["parser"],
            "parser_sha256": evidence_config["parser_sha256"],
            "release_version": evidence_config["release_version"],
            "release_asset_sha256": evidence_config["release_asset_sha256"],
            "style_markers": sorted(style_markers),
            "known_absent_markers": evidence_config["known_absent_markers"],
            "tag_semantics": config["tag_semantics"],
        },
        "counts": {
            "upstream_f_calque_annotations": len(rows),
            "raw_style_collision_annotations": style_annotation_count,
            "raw_style_collision_spans": len(style_span_markers),
            "raw_style_collision_spans_by_marker": dict(sorted(style_marker_span_counts.items())),
            "included_in_headline_calque": sum(bool(row[8]) for row in rows),
            "excluded_as_regional_standardization": counts["REGIONAL_STANDARDIZATION"],
            "excluded_as_register_standardization": counts["REGISTER_STANDARDIZATION"],
            "heritage_conflict": counts["HERITAGE_CONFLICT"],
            "contested": counts["CONTESTED"],
            "excluded_from_headline_calque": sum(not bool(row[8]) for row in rows),
            "items_by_disposition": {status: len(item_sets[status]) for status in sorted(VALID_DISPOSITIONS)},
        },
        "rows": rows,
    }
    validate_dispositions(result, manifest=manifest, config=config)
    return result


def validate_dispositions(
    dispositions: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any],
    config: Mapping[str, Any] | None = None,
) -> None:
    """Fail closed unless every upstream F/Calque annotation has one disposition."""
    if dispositions.get("schema_version") != SCHEMA_VERSION:
        raise DispositionError("unsupported disposition manifest schema")
    if dispositions.get("record_layout") != ROW_LAYOUT:
        raise DispositionError("unexpected disposition record layout")
    if dispositions.get("manifest_id") != manifest.get("manifest_id"):
        raise DispositionError("disposition manifest ID mismatch")
    if dispositions.get("manifest_payload_sha256") != manifest["integrity"]["payload_sha256"]:
        raise DispositionError("disposition manifest payload mismatch")
    if dispositions.get("semantics", {}).get("upstream_tag_preserved") is not True:
        raise DispositionError("upstream-tag preservation receipt is missing")
    raw_headline_includes = dispositions.get("semantics", {}).get("headline_includes")
    if not isinstance(raw_headline_includes, list):
        raise DispositionError("headline disposition semantics are missing")
    headline_includes = frozenset(str(status) for status in raw_headline_includes)
    if not headline_includes or not headline_includes <= VALID_DISPOSITIONS:
        raise DispositionError("headline disposition semantics are invalid")
    if config is not None:
        if dispositions.get("disposition_id") != config.get("disposition_id"):
            raise DispositionError("disposition config ID mismatch")
        evidence_config = config.get("evidence")
        if not isinstance(evidence_config, Mapping):
            raise DispositionError("disposition config evidence is missing")
        expected_receipt = {
            "source_lock": evidence_config["source_lock"],
            "source_lock_sha256": evidence_config["source_lock_sha256"],
            "parser": evidence_config["parser"],
            "parser_sha256": evidence_config["parser_sha256"],
            "release_version": evidence_config["release_version"],
            "release_asset_sha256": evidence_config["release_asset_sha256"],
            "style_markers": sorted(evidence_config["style_markers"]),
            "known_absent_markers": evidence_config["known_absent_markers"],
            "tag_semantics": config["tag_semantics"],
        }
        if dispositions.get("evidence_receipt") != expected_receipt:
            raise DispositionError("disposition evidence receipt does not match config")
        policy = config.get("policy")
        if not isinstance(policy, Mapping):
            raise DispositionError("disposition policy is missing")
        _validated_policy(policy)
        if list(raw_headline_includes) != policy["headline_includes"]:
            raise DispositionError("headline disposition semantics do not match config")
        for path_key, hash_key in (
            ("source_lock", "source_lock_sha256"),
            ("parser", "parser_sha256"),
        ):
            if _sha256(ROOT / str(evidence_config[path_key])) != evidence_config[hash_key]:
                raise DispositionError(f"disposition config {path_key} hash drift")

    expected = _calque_records(manifest, "F/Calque")
    expected_keys = {
        (
            record["item_id"],
            record["annotator_index"],
            record["start"],
            record["end"],
            record["upstream_tag"],
            record["replacement"],
            tuple(record["source_span"]),
        )
        for record in expected
    }
    rows = dispositions.get("rows")
    if not isinstance(rows, list):
        raise DispositionError("disposition rows must be an array")
    observed_keys: set[tuple[Any, ...]] = set()
    status_counts: Counter[str] = Counter()
    style_annotation_count = 0
    style_spans: dict[tuple[str, int, int, tuple[str, ...]], set[str]] = {}
    for raw_row in rows:
        if not isinstance(raw_row, list) or len(raw_row) != len(ROW_LAYOUT):
            raise DispositionError("invalid disposition row")
        row = dict(zip(ROW_LAYOUT, raw_row, strict=True))
        key = (
            row["item_id"],
            row["annotator_index"],
            row["start"],
            row["end"],
            row["upstream_tag"],
            row["replacement"],
            tuple(row["source_span"]),
        )
        if key in observed_keys:
            raise DispositionError("duplicate disposition row")
        observed_keys.add(key)
        if row["upstream_tag"] != "F/Calque":
            raise DispositionError("upstream tag was silently relabelled")
        status = str(row["disposition"])
        if status not in VALID_DISPOSITIONS:
            raise DispositionError(f"invalid disposition: {status}")
        if bool(row["headline_calque"]) != (status in headline_includes):
            raise DispositionError("headline flag contradicts disposition")
        if not row["reason"]:
            raise DispositionError("disposition reason is missing")
        evidence = row.get("evidence")
        if not isinstance(evidence, Mapping):
            raise DispositionError("disposition evidence is missing")
        form_evidence = evidence.get("exact_form_evidence")
        if not isinstance(form_evidence, list) or len(form_evidence) != len(row["source_span"]):
            raise DispositionError("exact-form evidence does not match source span")
        markers = {str(marker) for value in form_evidence for marker in value.get("style_markers", [])}
        if markers:
            style_annotation_count += 1
            span_key = (
                str(row["item_id"]),
                int(row["start"]),
                int(row["end"]),
                tuple(str(token) for token in row["source_span"]),
            )
            style_spans.setdefault(span_key, set()).update(markers)
        status_counts[status] += 1
    if observed_keys != expected_keys:
        raise DispositionError("dispositions do not exactly cover upstream F/Calque annotations")

    counts = dispositions.get("counts", {})
    style_marker_span_counts: Counter[str] = Counter()
    for markers in style_spans.values():
        style_marker_span_counts.update(markers)
    expected_counts = {
        "upstream_f_calque_annotations": len(rows),
        "raw_style_collision_annotations": style_annotation_count,
        "raw_style_collision_spans": len(style_spans),
        "raw_style_collision_spans_by_marker": dict(sorted(style_marker_span_counts.items())),
        "included_in_headline_calque": sum(bool(row[8]) for row in rows),
        "excluded_as_regional_standardization": status_counts["REGIONAL_STANDARDIZATION"],
        "excluded_as_register_standardization": status_counts["REGISTER_STANDARDIZATION"],
        "heritage_conflict": status_counts["HERITAGE_CONFLICT"],
        "contested": status_counts["CONTESTED"],
        "excluded_from_headline_calque": sum(not bool(row[8]) for row in rows),
    }
    if any(counts.get(key) != value for key, value in expected_counts.items()):
        raise DispositionError("disposition counts are stale")


def write_dispositions(path: Path, dispositions: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dispositions, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, help="hash-locked dict_uk/VESUM v6.8.0 asset")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-existing", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    manifest = _read_json(args.manifest)
    if args.verify_existing:
        validate_dispositions(
            _read_json(args.output),
            manifest=manifest,
            config=_read_json(args.config),
        )
        print(f"Disposition manifest valid: {args.output}")
        return 0
    if args.asset is None:
        parser.error("--asset is required unless --verify-existing is used")
    built = build_dispositions(
        manifest=manifest,
        config=_read_json(args.config),
        asset_path=args.asset,
    )
    if args.check:
        existing = _read_json(args.output)
        if existing != built:
            raise DispositionError("committed disposition manifest is stale")
        print(f"Disposition manifest reproducible: {args.output}")
        return 0
    write_dispositions(args.output, built)
    counts = built["counts"]
    print(
        "Calque dispositions: "
        f"{counts['included_in_headline_calque']} included, "
        f"{counts['excluded_as_regional_standardization'] + counts['excluded_as_register_standardization']} "
        "standardization-only, "
        f"{counts['heritage_conflict'] + counts['contested']} contested"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
