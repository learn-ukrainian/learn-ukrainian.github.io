#!/usr/bin/env python3
"""Compute preregistered paired efficacy and automated safety contrasts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.projects.ua_eval_harness.evaluate_model import (
    DEFAULT_DISPOSITIONS,
    DEFAULT_MANIFEST,
    DEFAULT_PROMPT,
    ItemScore,
    _f_score,
    _percentile,
    _wilson_interval,
    load_dispositions,
    load_manifest,
    load_saved_responses,
    score_item,
)

MODEL_REVISION = "842da3794eaa0b77d5f08bae87a17459d91ff475"
PAIRED_SCHEMA = "ua_eval_paired_treatment_contrast.v1"
SAFETY_SCHEMA = "ua_eval_treatment_safety_contrast.v1"


class ContrastError(ValueError):
    """Paired saved responses or safety-probe results violate the frozen contract."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ContrastError(f"expected object at {path}:{line_number}")
                rows.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise ContrastError(f"cannot read JSONL {path}: {exc}") from exc
    if not rows:
        raise ContrastError(f"empty JSONL file: {path}")
    return rows


def _scored_run(
    path: Path,
    *,
    manifest_path: Path,
    dispositions_path: Path,
    prompt_path: Path,
) -> tuple[dict[str, Any], list[ItemScore]]:
    manifest, items = load_manifest(manifest_path)
    _, dispositions = load_dispositions(dispositions_path, manifest=manifest)
    header, responses = load_saved_responses(
        path,
        manifest=manifest,
        items=items,
        prompt_path=prompt_path,
    )
    return header, [
        score_item(item, responses[str(item["id"])], dispositions=dispositions)
        for item in items
    ]


def _require_generation_parity(control: Mapping[str, Any], treatment: Mapping[str, Any]) -> None:
    constant_fields = (
        "schema_version",
        "generator_kind",
        "manifest_id",
        "manifest_payload_sha256",
        "prompt_sha256",
        "input_fields",
        "gold_fields_supplied",
        "decoding",
        "runner",
        "runner_version",
        "response_count",
    )
    drift = [field for field in constant_fields if control.get(field) != treatment.get(field)]
    if drift:
        raise ContrastError(f"paired generation constants drift: {drift}")


def _aggregate(scores: Sequence[ItemScore]) -> dict[str, float | int]:
    tp = sum(score.tp for score in scores)
    fp = sum(score.fp for score in scores)
    fn = sum(score.fn for score in scores)
    precision, recall, f_score = _f_score(tp, fp, fn)
    return {
        "exact_sentence_accuracy": sum(score.exact for score in scores) / len(scores),
        "f0_5": f_score,
        "false_negative": fn,
        "false_positive": fp,
        "over_edit_rate": sum(score.over_edited for score in scores) / len(scores),
        "precision": precision,
        "recall": recall,
        "true_positive": tp,
    }


def paired_contrast(
    control_path: Path,
    treatment_path: Path,
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    dispositions_path: Path = DEFAULT_DISPOSITIONS,
    prompt_path: Path = DEFAULT_PROMPT,
    samples: int = 10000,
    seed: int = 6170,
) -> dict[str, Any]:
    if samples < 1:
        raise ContrastError("bootstrap samples must be positive")
    control_header, control_scores = _scored_run(
        control_path,
        manifest_path=manifest_path,
        dispositions_path=dispositions_path,
        prompt_path=prompt_path,
    )
    treatment_header, treatment_scores = _scored_run(
        treatment_path,
        manifest_path=manifest_path,
        dispositions_path=dispositions_path,
        prompt_path=prompt_path,
    )
    _require_generation_parity(control_header, treatment_header)
    if [score.item_id for score in control_scores] != [score.item_id for score in treatment_scores]:
        raise ContrastError("paired item order or coverage drift")

    control_aggregate = _aggregate(control_scores)
    treatment_aggregate = _aggregate(treatment_scores)
    point_f0_5 = float(treatment_aggregate["f0_5"]) - float(control_aggregate["f0_5"])
    point_exact = float(treatment_aggregate["exact_sentence_accuracy"]) - float(
        control_aggregate["exact_sentence_accuracy"]
    )
    point_over_edit = float(treatment_aggregate["over_edit_rate"]) - float(control_aggregate["over_edit_rate"])
    generator = random.Random(seed)
    f0_5_deltas: list[float] = []
    exact_deltas: list[float] = []
    over_edit_deltas: list[float] = []
    population = len(control_scores)
    for _ in range(samples):
        indices = [generator.randrange(population) for _ in range(population)]
        control_selected = [control_scores[index] for index in indices]
        treatment_selected = [treatment_scores[index] for index in indices]
        control_sample = _aggregate(control_selected)
        treatment_sample = _aggregate(treatment_selected)
        f0_5_deltas.append(float(treatment_sample["f0_5"]) - float(control_sample["f0_5"]))
        exact_deltas.append(
            float(treatment_sample["exact_sentence_accuracy"])
            - float(control_sample["exact_sentence_accuracy"])
        )
        over_edit_deltas.append(
            float(treatment_sample["over_edit_rate"]) - float(control_sample["over_edit_rate"])
        )
    f0_5_interval = [_percentile(f0_5_deltas, 0.025), _percentile(f0_5_deltas, 0.975)]
    return {
        "control": {
            "metrics": control_aggregate,
            "response_sha256": sha256_file(control_path),
            "run_id": control_header["run_id"],
        },
        "inference": {
            "confidence": 0.95,
            "method": "paired_sentence_bootstrap_percentile",
            "samples": samples,
            "seed": seed,
            "statistical_gate_passed": f0_5_interval[0] > 0,
        },
        "primary": {"delta_f0_5": point_f0_5, "delta_f0_5_95_ci": f0_5_interval},
        "safety_gate": "must_be_evaluated_separately_before_any_retention_decision",
        "schema_version": PAIRED_SCHEMA,
        "secondary": {
            "delta_exact_sentence_accuracy": point_exact,
            "delta_exact_sentence_accuracy_95_ci": [
                _percentile(exact_deltas, 0.025),
                _percentile(exact_deltas, 0.975),
            ],
            "delta_over_edit_rate": point_over_edit,
            "delta_over_edit_rate_95_ci": [
                _percentile(over_edit_deltas, 0.025),
                _percentile(over_edit_deltas, 0.975),
            ],
        },
        "treatment": {
            "metrics": treatment_aggregate,
            "response_sha256": sha256_file(treatment_path),
            "run_id": treatment_header["run_id"],
        },
    }


def _load_safety_responses(path: Path, *, probe_hash: str, probe_ids: set[str]) -> tuple[dict[str, Any], dict[str, str]]:
    rows = read_jsonl(path)
    header = rows[0]
    required_header = {"type", "schema_version", "arm", "model_revision", "decoding", "probe_artifact_sha256"}
    if set(header) != required_header or header["type"] != "safety_run":
        raise ContrastError("invalid safety-run header")
    if header["schema_version"] != "ua_eval_treatment_safety_responses.v1":
        raise ContrastError("safety-run schema mismatch")
    if header["model_revision"] != MODEL_REVISION:
        raise ContrastError("safety-run model revision mismatch")
    if header["probe_artifact_sha256"] != probe_hash:
        raise ContrastError("safety-run probe hash mismatch")
    responses: dict[str, str] = {}
    for row in rows[1:]:
        if set(row) != {"probe_id", "raw_response"}:
            raise ContrastError("invalid safety response row")
        probe_id = str(row["probe_id"])
        if probe_id not in probe_ids or probe_id in responses:
            raise ContrastError(f"invalid or duplicate safety response: {probe_id}")
        responses[probe_id] = str(row["raw_response"])
    if set(responses) != probe_ids:
        raise ContrastError("safety responses do not exactly cover the probe inventory")
    return header, responses


def safety_contrast(probes_path: Path, faithful_path: Path, modern_path: Path) -> dict[str, Any]:
    probes = read_jsonl(probes_path)
    probe_by_id = {str(probe["probe_id"]): probe for probe in probes}
    if len(probe_by_id) != len(probes):
        raise ContrastError("duplicate probe IDs")
    probe_hash = sha256_file(probes_path)
    faithful_header, faithful_responses = _load_safety_responses(
        faithful_path,
        probe_hash=probe_hash,
        probe_ids=set(probe_by_id),
    )
    modern_header, modern_responses = _load_safety_responses(
        modern_path,
        probe_hash=probe_hash,
        probe_ids=set(probe_by_id),
    )
    if faithful_header["decoding"] != modern_header["decoding"]:
        raise ContrastError("safety-run decoding drift")
    if faithful_header["arm"] != "faithful_cpt" or modern_header["arm"] != "modern_mask_cpt":
        raise ContrastError("safety-run arm mismatch")

    def score(responses: Mapping[str, str]) -> dict[str, Any]:
        no_change_total = 0
        no_change_changed = 0
        protected_total = 0
        protected_failures = 0
        for probe_id, probe in probe_by_id.items():
            response = responses[probe_id]
            if probe["kind"] == "clean_no_change":
                no_change_total += 1
                no_change_changed += " ".join(response.split()) != " ".join(str(probe["source"]).split())
            elif probe["kind"] == "protected_span":
                protected_total += 1
                protected_failures += str(probe["protected"]["text"]) not in response
            else:
                raise ContrastError(f"unknown safety probe kind: {probe['kind']}")
        return {
            "no_change": {
                "changed": no_change_changed,
                "rate": no_change_changed / no_change_total,
                "rate_95_ci_wilson": _wilson_interval(no_change_changed, no_change_total),
                "total": no_change_total,
            },
            "protected_span": {"failures": protected_failures, "total": protected_total},
        }

    faithful_metrics = score(faithful_responses)
    modern_metrics = score(modern_responses)
    gate_passed = (
        modern_metrics["protected_span"]["failures"] == 0
        and modern_metrics["no_change"]["rate"] <= faithful_metrics["no_change"]["rate"]
    )
    return {
        "decision_scope": "automated_non_human_safety_proxy_not_linguistic_gold",
        "faithful": faithful_metrics,
        "gate": {
            "passed": gate_passed,
            "rule": "zero modern protected-span failures and modern no-change edit rate no higher than faithful",
        },
        "modern": modern_metrics,
        "probe_artifact_sha256": probe_hash,
        "schema_version": SAFETY_SCHEMA,
    }


def write_report(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor, raw_temp_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(raw_temp_path)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    paired = subparsers.add_parser("paired")
    paired.add_argument("--control", type=Path, required=True)
    paired.add_argument("--treatment", type=Path, required=True)
    paired.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    paired.add_argument("--dispositions", type=Path, default=DEFAULT_DISPOSITIONS)
    paired.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    paired.add_argument("--samples", type=int, default=10000)
    paired.add_argument("--seed", type=int, default=6170)
    paired.add_argument("--output", type=Path, required=True)
    safety = subparsers.add_parser("safety")
    safety.add_argument("--probes", type=Path, required=True)
    safety.add_argument("--faithful", type=Path, required=True)
    safety.add_argument("--modern", type=Path, required=True)
    safety.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "paired":
            report = paired_contrast(
                args.control,
                args.treatment,
                manifest_path=args.manifest,
                dispositions_path=args.dispositions,
                prompt_path=args.prompt,
                samples=args.samples,
                seed=args.seed,
            )
        else:
            report = safety_contrast(args.probes, args.faithful, args.modern)
        write_report(args.output, report)
        print(canonical_json(report))
    except (ContrastError, ValueError) as exc:
        print(f"treatment comparison failed: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
