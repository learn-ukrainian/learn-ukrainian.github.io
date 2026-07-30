#!/usr/bin/env python3
"""Deterministically analyze frozen UA evaluation v0.1.1 evidence only.

This program never generates a response.  It validates the immutable release,
re-scores the two comparable saved model runs, and writes an item-level evidence
join plus aggregate diagnostics suitable for designing a future evaluation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.ua_eval_harness import verify_release_freeze_v011 as freeze_v011
from scripts.projects.ua_eval_harness.evaluate_model import (
    EvaluationError,
    load_dispositions,
    load_manifest,
    load_saved_responses,
    score_item,
    score_saved_run,
)

DATA = ROOT / "data/projects/ua_eval_harness"
MANIFEST = DATA / "heldout_manifest_v1.json"
DISPOSITIONS = DATA / "scoring_dispositions_v1.json"
REQUESTS = DATA / "baselines/v1/generation_requests.jsonl"
RUNS = {
    "gpt_5_6_terra": DATA / "baselines/v1/gpt-5.6-terra.responses.jsonl",
    "gemma_4_31b_it": DATA / "baselines/v2/gemma-4-31b-it.responses.jsonl",
    "identity": DATA / "baselines/v1/identity.responses.jsonl",
    "fixture_rules": DATA / "baselines/v1/fixture-rules.responses.jsonl",
}
REPORTS = {
    "gpt_5_6_terra": DATA / "baselines/v1/gpt-5.6-terra.report.json",
    "gemma_4_31b_it": DATA / "baselines/v2/gemma-4-31b-it.report.json",
}


class EvidenceError(ValueError):
    """Frozen evidence is incomplete, reordered, or inconsistent."""


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read {path}: {exc}") from exc
    if not rows or not all(isinstance(row, dict) for row in rows):
        raise EvidenceError(f"invalid JSONL evidence: {path}")
    return rows


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"invalid JSON evidence object: {path}")
    return value


def ordered_responses(path: Path, expected_ids: Sequence[str]) -> dict[str, str]:
    """Require complete, unique *and manifest-ordered* saved-response rows."""
    rows = read_jsonl(path)
    response_rows = rows[1:]
    actual_ids = [str(row.get("item_id", "")) for row in response_rows]
    if len(actual_ids) != len(expected_ids):
        raise EvidenceError(f"response count mismatch in {path}")
    if len(set(actual_ids)) != len(actual_ids):
        raise EvidenceError(f"duplicate response IDs in {path}")
    if actual_ids != list(expected_ids):
        raise EvidenceError(f"response IDs missing, reordered, or mismatched in {path}")
    return {item_id: str(row.get("raw_response", "")) for item_id, row in zip(actual_ids, response_rows, strict=True)}


def verify_inputs() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    dict[tuple[Any, ...], dict[str, Any]],
    dict[str, dict[str, str]],
]:
    freeze_v011.validate_freeze(read_json(freeze_v011.DEFAULT_OUTPUT))
    manifest, items = load_manifest(MANIFEST)
    _, disposition_lookup = load_dispositions(DISPOSITIONS, manifest=manifest)
    expected_ids = [str(item["id"]) for item in items]
    request_rows = read_jsonl(REQUESTS)
    request_ids = [str(row.get("item_id", "")) for row in request_rows[1:]]
    if request_ids != expected_ids:
        raise EvidenceError("generation requests missing, reordered, or mismatched")
    responses: dict[str, dict[str, str]] = {}
    for name, path in RUNS.items():
        # Existing loader validates content hashes and response/request receipts.
        _, validated = load_saved_responses(path, manifest=manifest, items=items)
        ordered = ordered_responses(path, expected_ids)
        if validated != ordered:
            raise EvidenceError(f"saved-response loaders disagree for {path}")
        responses[name] = ordered
    return manifest, items, disposition_lookup, responses


def report_metrics(report: Mapping[str, Any]) -> dict[str, Any]:
    try:
        return {
            "edit_correction": report["edit_correction"],
            "exact_sentence": report["exact_sentence"],
            "diagnostics": report["diagnostics"],
            "headline_calque": report["headline_calque"],
        }
    except KeyError as exc:
        raise EvidenceError(f"frozen report missing aggregate section: {exc.args[0]}") from exc


def disposition_summary(item: Mapping[str, Any], lookup: Mapping[tuple[Any, ...], Mapping[str, Any]]) -> tuple[list[str], bool, bool, list[dict[str, Any]]]:
    entries: list[dict[str, Any]] = []
    for reference in item["references"]:
        for edit in reference["edits"]:
            if edit["tag"] != "F/Calque":
                continue
            key = (str(item["id"]), str(reference["annotator_index"]), int(edit["start"]), int(edit["end"]), str(edit["tag"]), str(edit["replacement"]))
            if key in lookup:
                entries.append(dict(lookup[key]))
    dispositions = sorted({str(entry["disposition"]) for entry in entries})
    defect = any(value in {"CONTESTED", "HERITAGE_CONFLICT"} for value in dispositions)
    risk = bool(item["is_sensitive"]) or any(value in {"HERITAGE_CONFLICT", "REGIONAL_STANDARDIZATION", "REGISTER_STANDARDIZATION"} for value in dispositions)
    return dispositions, defect, risk, entries


def classify_pair(gpt: Any, gemma: Any) -> str:
    """Compare exact-edit measurements, not linguistic quality."""
    # Negated error counts make fewer false positives/negatives rank higher.
    left = (gpt.tp, -gpt.fp, -gpt.fn, gpt.exact)
    right = (gemma.tp, -gemma.fp, -gemma.fn, gemma.exact)
    if left == right:
        return "tie_exact_measurement"
    return "gpt_measurement_win" if left > right else "gemma_measurement_win"


def build_analysis() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    _manifest, items, lookup, responses = verify_inputs()
    reproduced: dict[str, Any] = {}
    for name, path in REPORTS.items():
        derived = score_saved_run(RUNS[name], bootstrap_samples=0)
        frozen = json.loads(path.read_text(encoding="utf-8"))
        if report_metrics(derived) != report_metrics(frozen):
            raise EvidenceError(f"frozen aggregate metrics not reproduced for {name}")
        reproduced[name] = report_metrics(derived)

    rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    by_tag: dict[str, Counter[str]] = defaultdict(Counter)
    tag_item_support: Counter[str] = Counter()
    category_gap_evidence: dict[str, Counter[str]] = defaultdict(Counter)
    reference_counts: Counter[str] = Counter()
    for item in items:
        item_id = str(item["id"])
        gpt = score_item(item, responses["gpt_5_6_terra"][item_id], dispositions=lookup)
        gemma = score_item(item, responses["gemma_4_31b_it"][item_id], dispositions=lookup)
        statuses, possible_defect, protected_risk, entries = disposition_summary(item, lookup)
        pair = classify_pair(gpt, gemma)
        same_output = responses["gpt_5_6_terra"][item_id] == responses["gemma_4_31b_it"][item_id]
        uncertainty = ["exact_mismatch_not_linguistic_error"]
        if possible_defect or protected_risk:
            uncertainty.append("needs_ua_review")
        if len(item["references"]) > 1:
            uncertainty.append("multiple_references")
        uncertainty.sort()
        next_disposition = "needs_ua_review" if possible_defect or protected_risk else "measurement_only"
        row = {
            "item_id": item_id,
            "source_sha256": item["source_sha256"],
            "eligible_tags": sorted(item["eligible_tags"]),
            "observed_tags": sorted(item["observed_tags"]),
            "is_sensitive": bool(item["is_sensitive"]),
            "acceptable_reference_count": len(item["references"]),
            "calque_dispositions": statuses,
            "saved_responses": {name: responses[name][item_id] for name in sorted(responses)},
            "gpt_5_6_terra": {"tp": gpt.tp, "fp": gpt.fp, "fn": gpt.fn, "exact": gpt.exact, "unchanged": gpt.unchanged, "over_edited": gpt.over_edited, "under_edited": gpt.fn > 0},
            "gemma_4_31b_it": {"tp": gemma.tp, "fp": gemma.fp, "fn": gemma.fn, "exact": gemma.exact, "unchanged": gemma.unchanged, "over_edited": gemma.over_edited, "under_edited": gemma.fn > 0},
            "model_agreement": {"same_response": same_output, "measurement_comparison": pair, "ordering": "stable_for_this_frozen_prompt_only" if same_output else "uninterpretable_without_matched_prompt_variation"},
            "possible_reference_ambiguity_or_benchmark_defect": possible_defect,
            "protected_heritage_dialect_register_risk": protected_risk,
            "uncertainty": uncertainty,
            "evidence_links": {"manifest": "heldout_manifest_v1.json", "dispositions": "scoring_dispositions_v1.json", "calque_entries": entries},
            "next_disposition": next_disposition,
        }
        rows.append(row)
        counts[pair] += 1
        counts["gpt_unchanged"] += int(gpt.unchanged)
        counts["gemma_unchanged"] += int(gemma.unchanged)
        counts["gpt_over_edited"] += int(gpt.over_edited)
        counts["gemma_over_edited"] += int(gemma.over_edited)
        counts["gpt_under_edited"] += int(gpt.fn > 0)
        counts["gemma_under_edited"] += int(gemma.fn > 0)
        counts["needs_ua_review"] += int(next_disposition == "needs_ua_review")
        counts["possible_benchmark_defect"] += int(possible_defect)
        counts["protected_variation_risk"] += int(protected_risk)
        reference_counts[str(len(item["references"]))] += 1
        for tag in item["eligible_tags"]:
            by_tag[str(tag)][pair] += 1
            tag_item_support[str(tag)] += 1
        category_membership = {
            "clean_no_change_control": not item["eligible_tags"],
            "core_grammar": any(str(tag).startswith("G/") for tag in item["eligible_tags"]),
            "calque_lexical_choice": "F/Calque" in item["eligible_tags"],
            # v0.1.1 intentionally contains error-bearing inputs, not protected
            # no-change examples. Risk flags are review seeds, not positives.
            "hard_positive_must_not_normalize": False,
            "cognate_contested_or_protected_review": possible_defect or protected_risk,
            "multiple_acceptable_references": len(item["references"]) > 1,
        }
        for category, included in category_membership.items():
            if not included:
                continue
            evidence = category_gap_evidence[category]
            evidence["items"] += 1
            evidence["gpt_unchanged"] += int(gpt.unchanged)
            evidence["gemma_unchanged"] += int(gemma.unchanged)
            evidence["gpt_over_edited"] += int(gpt.over_edited)
            evidence["gemma_over_edited"] += int(gemma.over_edited)
            evidence["gpt_under_edited"] += int(gpt.fn > 0)
            evidence["gemma_under_edited"] += int(gemma.fn > 0)
            evidence["model_measurement_disagreement"] += int(pair != "tie_exact_measurement")

    input_paths = [MANIFEST, DATA / "heldout_manifest_config.json", DISPOSITIONS, DATA / "scoring_disposition_config.json", REQUESTS, *RUNS.values(), *REPORTS.values(), freeze_v011.DEFAULT_OUTPUT]
    for absent_category in ("clean_no_change_control", "hard_positive_must_not_normalize"):
        category_gap_evidence[absent_category]["items"] += 0
    summary = {
        "schema_version": "ua_eval_v011_evidence_analysis.v1",
        "purpose": "frozen-evidence measurement; not linguistic adjudication or a model ranking",
        "items": len(rows),
        "reproduced_aggregate_metrics": reproduced,
        "counts": dict(sorted(counts.items())),
        "reference_count_distribution": dict(sorted(reference_counts.items())),
        "measurement_comparison_by_eligible_tag": {tag: dict(sorted(value.items())) for tag, value in sorted(by_tag.items())},
        "category_gap_evidence": {
            "eligible_tag_item_support": dict(sorted(tag_item_support.items())),
            "strata": {
                category: dict(sorted(value.items()))
                for category, value in sorted(category_gap_evidence.items())
            },
            "interpretation": (
                "Counts describe frozen v0.1.1 measurement gaps. Protected-risk rows "
                "are review seeds, not hard-positive controls."
            ),
        },
        "input_sha256": {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(input_paths)},
        "limitations": ["Exact mismatch is not automatically a linguistic error.", "VESUM/dictionary markers are evidence, not contextual adjudication.", "Saved model output is never authority.", "No matched prompt-variation run exists; prompt sensitivity is uninterpretable."],
    }
    return rows, summary


def write_analysis(output: Path) -> dict[str, Any]:
    rows, summary = build_analysis()
    output.mkdir(parents=True, exist_ok=True)
    (output / "item_evidence.jsonl").write_text("".join(canonical(row) + "\n" for row in rows), encoding="utf-8")
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DATA / "analysis/v0.1.1")
    args = parser.parse_args(argv)
    try:
        summary = write_analysis(args.output)
    except (EvidenceError, EvaluationError, ValueError) as exc:
        parser.error(str(exc))
    print(f"wrote {summary['items']} evidence rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
