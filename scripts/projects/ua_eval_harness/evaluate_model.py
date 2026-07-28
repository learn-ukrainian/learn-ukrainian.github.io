#!/usr/bin/env python3
"""Prepare, validate, and score saved UA-GEC benchmark responses.

Generation and scoring are deliberately separate. ``prepare`` emits only public
item IDs, source sentences, and source hashes. ``score`` joins a versioned
saved-response JSONL file to the committed held-out manifest after generation.
Gold targets and edit spans never enter a real-model request.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.ua_eval_harness.build_heldout_manifest import validate_manifest

DEFAULT_MANIFEST = ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json"
DEFAULT_DEV_FIXTURES = ROOT / "data/projects/ua_eval_harness/evalset_v1.jsonl"
DEFAULT_PROMPT = ROOT / "data/projects/ua_eval_harness/minimal_edit_prompt_v1.txt"
SAVED_RESPONSE_SCHEMA = "ua_eval_saved_responses.v1"
REQUEST_SCHEMA = "ua_eval_generation_requests.v1"
REPORT_SCHEMA = "ua_eval_score_report.v1"
SCORER_ID = "ua_eval_exact_token_edits.v1"
RUNNER_ID = "ua_eval_saved_response_runner.v1"
UNLP_SCORER_REFERENCE = {
    "repository": "https://github.com/asivokon/unlp-2023-shared-task",
    "commit": "fbff22905f8c9a3677c900d56599284151c029e6",
    "evaluate_py_sha256": "6e37b7a41a3a3c303647ca29507cd51b4b6deb9b0952c2a62d8e0b0374fae31a",
    "semantic_contract": (
        "Correction true positives require an exact source span and exact replacement; "
        "precision, recall, and F0.5 are primary."
    ),
}
GOLD_FORBIDDEN_FIELDS = frozenset({"target", "targets", "reference", "references", "edit", "edits"})


class EvaluationError(ValueError):
    """A saved run, manifest, or scoring contract is invalid."""


@dataclass(frozen=True, slots=True)
class TokenEdit:
    start: int
    end: int
    replacement: str
    tag: str | None = None

    @property
    def key(self) -> tuple[int, int, str]:
        return (self.start, self.end, self.replacement)


@dataclass(frozen=True, slots=True)
class ItemScore:
    item_id: str
    tp: int
    fp: int
    fn: int
    exact: bool
    unchanged: bool
    over_edited: bool
    chosen_annotator: str
    tag_counts: Mapping[str, tuple[int, int]]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvaluationError(f"expected JSON object in {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise EvaluationError(f"cannot read JSONL {path}: {exc}") from exc
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvaluationError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise EvaluationError(f"expected object at {path}:{line_number}")
        rows.append(row)
    if not rows:
        raise EvaluationError(f"empty JSONL file: {path}")
    return rows


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(_canonical_json(dict(row)) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_manifest(path: Path = DEFAULT_MANIFEST) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load and expand the committed compact manifest."""
    manifest = _read_json(path)
    try:
        validate_manifest(manifest)
    except ValueError as exc:
        raise EvaluationError(f"manifest validation failed: {exc}") from exc
    layouts = manifest["record_layouts"]
    items: list[dict[str, Any]] = []
    for raw_item in manifest["items"]:
        item = dict(zip(layouts["item"], raw_item, strict=True))
        references: list[dict[str, Any]] = []
        for raw_reference in item["references"]:
            reference = dict(zip(layouts["reference"], raw_reference, strict=True))
            reference["edits"] = [dict(zip(layouts["edit"], raw_edit, strict=True)) for raw_edit in reference["edits"]]
            references.append(reference)
        item["references"] = references
        items.append(item)
    return manifest, items


def prompt_receipt(prompt_path: Path = DEFAULT_PROMPT) -> dict[str, Any]:
    """Return the frozen prompt text and its content hash."""
    try:
        text = prompt_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EvaluationError(f"cannot read prompt {prompt_path}: {exc}") from exc
    if not text.strip():
        raise EvaluationError("generation prompt is empty")
    lowered = text.casefold()
    if any(f"{{{field}}}" in lowered for field in GOLD_FORBIDDEN_FIELDS):
        raise EvaluationError("generation prompt contains a forbidden gold placeholder")
    try:
        display_path = prompt_path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        display_path = prompt_path.as_posix()
    return {"path": display_path, "sha256": _sha256_text(text), "text": text}


def _request_payload(item: Mapping[str, Any], prompt_sha256: str) -> dict[str, Any]:
    return {
        "item_id": item["id"],
        "source": item["source"],
        "source_sha256": item["source_sha256"],
        "prompt_sha256": prompt_sha256,
    }


def prepare_requests(
    manifest_path: Path = DEFAULT_MANIFEST,
    prompt_path: Path = DEFAULT_PROMPT,
) -> list[dict[str, Any]]:
    """Build a source-only generation packet with an explicit gold firewall."""
    manifest, items = load_manifest(manifest_path)
    prompt = prompt_receipt(prompt_path)
    header = {
        "type": "request_run",
        "schema_version": REQUEST_SCHEMA,
        "manifest_id": manifest["manifest_id"],
        "manifest_payload_sha256": manifest["integrity"]["payload_sha256"],
        "prompt_path": prompt["path"],
        "prompt_sha256": prompt["sha256"],
        "input_fields": ["item_id", "source", "source_sha256", "prompt_sha256"],
        "gold_fields_supplied": [],
        "request_count": len(items),
    }
    rows = [header]
    for item in items:
        payload = _request_payload(item, prompt["sha256"])
        rows.append({"type": "request", **payload, "request_sha256": _sha256_text(_canonical_json(payload))})
    return rows


def _run_header(
    *,
    manifest: Mapping[str, Any],
    prompt: Mapping[str, Any],
    run_id: str,
    generator_kind: str,
    provider: str,
    model: str,
    model_version: str,
    decoding: Mapping[str, Any],
    response_count: int,
    runner_version: str = RUNNER_ID,
    generation_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "type": "run",
        "schema_version": SAVED_RESPONSE_SCHEMA,
        "run_id": run_id,
        "generator_kind": generator_kind,
        "provider": provider,
        "model": model,
        "model_version": model_version,
        "decoding": dict(decoding),
        "runner": RUNNER_ID,
        "runner_version": runner_version,
        "manifest_id": manifest["manifest_id"],
        "manifest_payload_sha256": manifest["integrity"]["payload_sha256"],
        "prompt_path": prompt["path"],
        "prompt_sha256": prompt["sha256"],
        "input_fields": ["item_id", "source", "source_sha256", "prompt_sha256"],
        "gold_fields_supplied": [],
        "generation_metadata": dict(generation_metadata or {}),
        "response_count": response_count,
    }


def _response_row(item: Mapping[str, Any], prompt_sha256: str, raw_response: str) -> dict[str, Any]:
    request = _request_payload(item, prompt_sha256)
    return {
        "type": "response",
        "item_id": item["id"],
        "source_sha256": item["source_sha256"],
        "request_sha256": _sha256_text(_canonical_json(request)),
        "raw_response": raw_response,
        "response_sha256": _sha256_text(raw_response),
    }


def _fixture_rules(path: Path = DEFAULT_DEV_FIXTURES) -> list[tuple[str, str]]:
    """Derive deterministic literal rules only from the 52 train fixtures."""
    rules: set[tuple[str, str]] = set()
    for row in _read_jsonl(path):
        for edit in row.get("edits", []):
            source = str(edit.get("source_span", "")).strip()
            target = str(edit.get("target_span", "")).strip()
            if source and source != target:
                rules.add((source, target))
    return sorted(rules, key=lambda pair: (-len(pair[0]), pair))


def _apply_fixture_rules(source: str, rules: Sequence[tuple[str, str]]) -> str:
    corrected = source
    for old, new in rules:
        corrected = corrected.replace(old, new)
    return corrected


def generate_baseline(
    kind: str,
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    prompt_path: Path = DEFAULT_PROMPT,
    fixtures_path: Path = DEFAULT_DEV_FIXTURES,
) -> list[dict[str, Any]]:
    """Generate the identity or train-fixture-rule baseline without gold access."""
    manifest, items = load_manifest(manifest_path)
    prompt = prompt_receipt(prompt_path)
    runner_source_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if kind == "identity":

        def transform(source: str) -> str:
            return source

        model = "identity-v1"
        model_version = "1"
        extra_version = f"{RUNNER_ID};source_sha256={runner_source_sha256}"
    elif kind == "fixture-rules":
        rules = _fixture_rules(fixtures_path)

        def transform(source: str) -> str:
            return _apply_fixture_rules(source, rules)

        model = "train-fixture-literal-rules-v1"
        model_version = _sha256_text(_canonical_json(rules))
        extra_version = (
            f"{RUNNER_ID};source_sha256={runner_source_sha256};"
            f"fixtures_sha256={hashlib.sha256(fixtures_path.read_bytes()).hexdigest()}"
        )
    else:
        raise EvaluationError(f"unknown baseline kind: {kind}")
    header = _run_header(
        manifest=manifest,
        prompt=prompt,
        run_id=f"{manifest['manifest_id']}--{model}",
        generator_kind=kind,
        provider="builtin",
        model=model,
        model_version=model_version,
        decoding={"deterministic": True},
        response_count=len(items),
        runner_version=extra_version,
        generation_metadata={
            "gold_fields_supplied": [],
            "source": "builtin deterministic generator",
        },
    )
    return [header, *[_response_row(item, prompt["sha256"], transform(item["source"])) for item in items]]


def import_model_responses(
    *,
    requests_path: Path,
    model_output_path: Path,
    metadata_path: Path,
    manifest_path: Path = DEFAULT_MANIFEST,
    prompt_path: Path = DEFAULT_PROMPT,
) -> list[dict[str, Any]]:
    """Convert source-only model output into the frozen saved-response schema."""
    request_rows = _read_jsonl(requests_path)
    if request_rows[0].get("schema_version") != REQUEST_SCHEMA:
        raise EvaluationError("request packet schema mismatch")
    requests = {str(row["item_id"]): row for row in request_rows[1:] if row.get("type") == "request"}
    raw_outputs = _read_jsonl(model_output_path)
    outputs: dict[str, str] = {}
    for row in raw_outputs:
        item_id = str(row.get("item_id", ""))
        if not item_id or item_id in outputs:
            raise EvaluationError(f"missing or duplicate model-output item_id: {item_id!r}")
        if set(row) - {"item_id", "raw_response"}:
            raise EvaluationError(f"model output contains unsupported fields for {item_id}")
        outputs[item_id] = str(row.get("raw_response", ""))
    metadata = _read_json(metadata_path)
    required_metadata = {
        "run_id",
        "provider",
        "model",
        "model_version",
        "decoding",
        "runner_version",
    }
    if not required_metadata.issubset(metadata):
        raise EvaluationError(f"run metadata missing: {sorted(required_metadata - set(metadata))}")
    manifest, items = load_manifest(manifest_path)
    prompt = prompt_receipt(prompt_path)
    item_ids = {str(item["id"]) for item in items}
    if set(requests) != item_ids or set(outputs) != item_ids:
        raise EvaluationError("request/model-output IDs do not exactly cover the manifest")
    for item in items:
        request = requests[str(item["id"])]
        expected = _request_payload(item, prompt["sha256"])
        if any(request.get(field) != value for field, value in expected.items()):
            raise EvaluationError(f"request drift for {item['id']}")
        if request.get("request_sha256") != _sha256_text(_canonical_json(expected)):
            raise EvaluationError(f"request hash mismatch for {item['id']}")
    header = _run_header(
        manifest=manifest,
        prompt=prompt,
        run_id=str(metadata["run_id"]),
        generator_kind="model",
        provider=str(metadata["provider"]),
        model=str(metadata["model"]),
        model_version=str(metadata["model_version"]),
        decoding=dict(metadata["decoding"]),
        response_count=len(items),
        runner_version=str(metadata["runner_version"]),
        generation_metadata=dict(metadata.get("generation_metadata", {})),
    )
    return [
        header,
        *[_response_row(item, prompt["sha256"], outputs[str(item["id"])]) for item in items],
    ]


def load_saved_responses(
    path: Path,
    *,
    manifest: Mapping[str, Any],
    items: Sequence[Mapping[str, Any]],
    prompt_path: Path = DEFAULT_PROMPT,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Validate a complete saved run and return its raw response map."""
    rows = _read_jsonl(path)
    header = rows[0]
    prompt = prompt_receipt(prompt_path)
    if header.get("type") != "run" or header.get("schema_version") != SAVED_RESPONSE_SCHEMA:
        raise EvaluationError("saved-response header/schema mismatch")
    required = {
        "run_id",
        "generator_kind",
        "provider",
        "model",
        "model_version",
        "decoding",
        "runner",
        "runner_version",
        "manifest_id",
        "manifest_payload_sha256",
        "prompt_sha256",
        "input_fields",
        "gold_fields_supplied",
        "generation_metadata",
        "response_count",
    }
    if not required.issubset(header):
        raise EvaluationError(f"saved-response header missing: {sorted(required - set(header))}")
    if header["manifest_id"] != manifest["manifest_id"]:
        raise EvaluationError("saved-response manifest id mismatch")
    if header["manifest_payload_sha256"] != manifest["integrity"]["payload_sha256"]:
        raise EvaluationError("saved-response manifest payload mismatch")
    if header["prompt_sha256"] != prompt["sha256"]:
        raise EvaluationError("saved-response prompt hash mismatch")
    if header["gold_fields_supplied"] != []:
        raise EvaluationError("saved-response run reports gold leakage")
    if GOLD_FORBIDDEN_FIELDS & set(header["input_fields"]):
        raise EvaluationError("saved-response input fields include gold")
    item_by_id = {str(item["id"]): item for item in items}
    responses: dict[str, str] = {}
    for row in rows[1:]:
        item_id = str(row.get("item_id", ""))
        if row.get("type") != "response" or item_id not in item_by_id or item_id in responses:
            raise EvaluationError(f"invalid or duplicate saved response: {item_id!r}")
        item = item_by_id[item_id]
        raw_response = str(row.get("raw_response", ""))
        if row.get("source_sha256") != item["source_sha256"]:
            raise EvaluationError(f"source hash mismatch: {item_id}")
        if row.get("response_sha256") != _sha256_text(raw_response):
            raise EvaluationError(f"response hash mismatch: {item_id}")
        request = _request_payload(item, prompt["sha256"])
        if row.get("request_sha256") != _sha256_text(_canonical_json(request)):
            raise EvaluationError(f"request hash mismatch: {item_id}")
        responses[item_id] = raw_response
    if set(responses) != set(item_by_id) or header["response_count"] != len(responses):
        raise EvaluationError("saved responses do not exactly cover the manifest")
    return header, responses


def align_token_edits(source: str, target: str) -> list[TokenEdit]:
    """Extract deterministic minimal token edits with Wagner-Fischer alignment."""
    source_tokens = source.split()
    target_tokens = target.split()
    rows, columns = len(source_tokens) + 1, len(target_tokens) + 1
    costs = [[0] * columns for _ in range(rows)]
    steps = [[""] * columns for _ in range(rows)]
    for i in range(1, rows):
        costs[i][0], steps[i][0] = i, "D"
    for j in range(1, columns):
        costs[0][j], steps[0][j] = j, "I"
    for i in range(1, rows):
        for j in range(1, columns):
            if source_tokens[i - 1] == target_tokens[j - 1]:
                costs[i][j], steps[i][j] = costs[i - 1][j - 1], "M"
                continue
            candidates = [
                (costs[i - 1][j - 1] + 1, 0, "S"),
                (costs[i - 1][j] + 1, 1, "D"),
                (costs[i][j - 1] + 1, 2, "I"),
            ]
            cost, _, step = min(candidates)
            costs[i][j], steps[i][j] = cost, step
    operations: list[tuple[str, str | None]] = []
    i, j = len(source_tokens), len(target_tokens)
    while i or j:
        step = steps[i][j]
        if step in {"M", "S"}:
            operations.append((step, target_tokens[j - 1]))
            i -= 1
            j -= 1
        elif step == "D":
            operations.append((step, None))
            i -= 1
        elif step == "I":
            operations.append((step, target_tokens[j - 1]))
            j -= 1
        else:
            raise EvaluationError("alignment backtrace failed")
    operations.reverse()

    edits: list[TokenEdit] = []
    source_position = 0
    edit_start: int | None = None
    replacement: list[str] = []

    def flush() -> None:
        nonlocal edit_start, replacement
        if edit_start is not None:
            edits.append(TokenEdit(edit_start, source_position, " ".join(replacement)))
        edit_start, replacement = None, []

    for operation, token in operations:
        if operation == "M":
            flush()
            source_position += 1
            continue
        if edit_start is None:
            edit_start = source_position
        if operation in {"S", "I"} and token is not None:
            replacement.append(token)
        if operation in {"S", "D"}:
            source_position += 1
    flush()
    return edits


def _f_score(tp: int, fp: int, fn: int, beta: float = 0.5) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    beta_squared = beta * beta
    denominator = beta_squared * precision + recall
    f_score = (1 + beta_squared) * precision * recall / denominator if denominator else 0.0
    return precision, recall, f_score


def _gold_edits(reference: Mapping[str, Any]) -> list[TokenEdit]:
    return [
        TokenEdit(int(edit["start"]), int(edit["end"]), str(edit["replacement"]), str(edit["tag"]))
        for edit in reference["edits"]
    ]


def _score_against_reference(
    candidate: Sequence[TokenEdit],
    reference: Mapping[str, Any],
) -> tuple[int, int, int, dict[str, tuple[int, int]]]:
    candidate_keys = {edit.key for edit in candidate}
    gold = _gold_edits(reference)
    gold_keys = {edit.key for edit in gold}
    tp = len(candidate_keys & gold_keys)
    fp = len(candidate_keys - gold_keys)
    fn = len(gold_keys - candidate_keys)
    by_tag: dict[str, list[int]] = {}
    for edit in gold:
        bucket = by_tag.setdefault(str(edit.tag), [0, 0])
        bucket[0 if edit.key in candidate_keys else 1] += 1
    return tp, fp, fn, {tag: (values[0], values[1]) for tag, values in by_tag.items()}


def score_item(item: Mapping[str, Any], response: str) -> ItemScore:
    """Score one response against its best matching upstream annotator."""
    candidate = align_token_edits(str(item["source"]), response)
    ranked: list[tuple[tuple[float, int, int, int, str], Mapping[str, Any], tuple[int, int, int, Any]]] = []
    for reference in item["references"]:
        counts = _score_against_reference(candidate, reference)
        tp, fp, fn, _ = counts
        _, _, f_score = _f_score(tp, fp, fn)
        annotator = str(reference["annotator_index"])
        rank = (f_score, tp, -fp, -fn, annotator)
        ranked.append((rank, reference, counts))
    if not ranked:
        raise EvaluationError(f"manifest item has no references: {item['id']}")
    _, chosen_reference, counts = max(ranked, key=lambda entry: entry[0])
    tp, fp, fn, tag_counts = counts
    normalized_response = " ".join(response.split())
    targets = {" ".join(str(reference["target"]).split()) for reference in item["references"]}
    source = " ".join(str(item["source"]).split())
    return ItemScore(
        item_id=str(item["id"]),
        tp=tp,
        fp=fp,
        fn=fn,
        exact=normalized_response in targets,
        unchanged=normalized_response == source,
        over_edited=fp > 0,
        chosen_annotator=str(chosen_reference["annotator_index"]),
        tag_counts=tag_counts,
    )


def _percentile(values: Sequence[float], quantile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _bootstrap_uncertainty(
    scores: Sequence[ItemScore],
    *,
    samples: int = 1000,
    seed: int = 2156,
) -> dict[str, Any]:
    if not scores:
        return {"method": "none", "samples": 0}
    generator = random.Random(seed)
    f_scores: list[float] = []
    exact_scores: list[float] = []
    for _ in range(samples):
        selected = [scores[generator.randrange(len(scores))] for _ in scores]
        tp = sum(score.tp for score in selected)
        fp = sum(score.fp for score in selected)
        fn = sum(score.fn for score in selected)
        f_scores.append(_f_score(tp, fp, fn)[2])
        exact_scores.append(sum(score.exact for score in selected) / len(selected))
    return {
        "method": "sentence_bootstrap_percentile",
        "confidence": 0.95,
        "samples": samples,
        "seed": seed,
        "edit_f0_5": [_percentile(f_scores, 0.025), _percentile(f_scores, 0.975)],
        "exact_sentence_accuracy": [_percentile(exact_scores, 0.025), _percentile(exact_scores, 0.975)],
    }


def _wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    if not total:
        return [0.0, 0.0]
    probability = successes / total
    denominator = 1 + z * z / total
    center = (probability + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(probability * (1 - probability) / total + z * z / (4 * total * total))
    margin /= denominator
    return [max(0.0, center - margin), min(1.0, center + margin)]


def score_saved_run(
    responses_path: Path,
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    prompt_path: Path = DEFAULT_PROMPT,
    bootstrap_samples: int = 1000,
) -> dict[str, Any]:
    """Compute standard exact-edit P/R/F0.5 plus companion diagnostics."""
    manifest, items = load_manifest(manifest_path)
    header, responses = load_saved_responses(
        responses_path,
        manifest=manifest,
        items=items,
        prompt_path=prompt_path,
    )
    item_scores = [score_item(item, responses[str(item["id"])]) for item in items]
    tp = sum(score.tp for score in item_scores)
    fp = sum(score.fp for score in item_scores)
    fn = sum(score.fn for score in item_scores)
    precision, recall, f_score = _f_score(tp, fp, fn)
    tag_totals: dict[str, list[int]] = {}
    for score in item_scores:
        for tag, (tag_tp, tag_fn) in score.tag_counts.items():
            bucket = tag_totals.setdefault(tag, [0, 0])
            bucket[0] += tag_tp
            bucket[1] += tag_fn
    annotation_support = manifest["counts"]["eligible_edits_by_tag"]
    per_tag = {}
    for tag in sorted(set(annotation_support) | set(tag_totals)):
        tag_tp, tag_fn = tag_totals.get(tag, [0, 0])
        selected_reference_support = tag_tp + tag_fn
        per_tag[tag] = {
            "support": int(annotation_support.get(tag, 0)),
            "support_definition": "all eligible upstream annotations across retained references",
            "selected_reference_support": selected_reference_support,
            "true_positive": tag_tp,
            "false_negative": tag_fn,
            "recall": tag_tp / selected_reference_support if selected_reference_support else 0.0,
            "recall_95_ci_wilson": _wilson_interval(tag_tp, selected_reference_support),
            "recall_denominator_note": (
                "Recall uses the deterministic best-reference selection for this saved run; "
                "selected_reference_support may vary by run."
            ),
            "precision": None,
            "precision_note": "Hypothesis-only false positives are untyped and reported in overall edit precision.",
        }
    response_file_sha256 = hashlib.sha256(responses_path.read_bytes()).hexdigest()
    exact_count = sum(score.exact for score in item_scores)
    unchanged_count = sum(score.unchanged for score in item_scores)
    over_edited_count = sum(score.over_edited for score in item_scores)
    return {
        "schema_version": REPORT_SCHEMA,
        "scorer": {
            "id": SCORER_ID,
            "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "matching": "exact source token span plus exact replacement text",
            "reference_policy": "best F0.5 upstream annotator per sentence; deterministic tie-break",
            "beta": 0.5,
            "standard_metric_reference": UNLP_SCORER_REFERENCE,
            "alignment_note": (
                "This dependency-free v1 uses a pinned Wagner-Fischer token aligner. "
                "It implements the official exact-edit metric semantics but does not claim "
                "byte-for-byte ERRANT alignment parity in ambiguous alignments."
            ),
        },
        "manifest": {
            "id": manifest["manifest_id"],
            "payload_sha256": manifest["integrity"]["payload_sha256"],
            "items": len(items),
        },
        "saved_run": {
            "path": responses_path.as_posix(),
            "sha256": response_file_sha256,
            **{
                key: header[key]
                for key in (
                    "run_id",
                    "generator_kind",
                    "provider",
                    "model",
                    "model_version",
                    "decoding",
                    "runner",
                    "runner_version",
                    "prompt_sha256",
                    "input_fields",
                    "gold_fields_supplied",
                    "generation_metadata",
                )
            },
        },
        "edit_correction": {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "precision": precision,
            "recall": recall,
            "f0_5": f_score,
        },
        "exact_sentence": {
            "correct": exact_count,
            "total": len(item_scores),
            "accuracy": exact_count / len(item_scores) if item_scores else 0.0,
        },
        "diagnostics": {
            "unchanged_outputs": unchanged_count,
            "unchanged_rate": unchanged_count / len(item_scores) if item_scores else 0.0,
            "over_edited_outputs": over_edited_count,
            "over_edit_rate": over_edited_count / len(item_scores) if item_scores else 0.0,
            "untyped_false_positive_edits": fp,
        },
        "per_tag": per_tag,
        "uncertainty": _bootstrap_uncertainty(item_scores, samples=bootstrap_samples),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="write source-only generation requests")
    prepare.add_argument("--output", type=Path, required=True)

    baseline = subparsers.add_parser("baseline", help="write a deterministic saved-response baseline")
    baseline.add_argument("--kind", choices=["identity", "fixture-rules"], required=True)
    baseline.add_argument("--fixtures", type=Path, default=DEFAULT_DEV_FIXTURES)
    baseline.add_argument("--output", type=Path, required=True)

    imported = subparsers.add_parser("import", help="import source-only real-model outputs")
    imported.add_argument("--requests", type=Path, required=True)
    imported.add_argument("--model-output", type=Path, required=True)
    imported.add_argument("--metadata", type=Path, required=True)
    imported.add_argument("--output", type=Path, required=True)

    score = subparsers.add_parser("score", help="score a complete saved-response run")
    score.add_argument("--responses", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    score.add_argument("--bootstrap-samples", type=int, default=1000)

    verify = subparsers.add_parser("verify", help="validate a saved-response run without scoring")
    verify.add_argument("--responses", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            rows = prepare_requests(args.manifest, args.prompt)
            _write_jsonl(args.output, rows)
            print(f"wrote {len(rows) - 1} source-only requests to {args.output}")
        elif args.command == "baseline":
            rows = generate_baseline(
                args.kind,
                manifest_path=args.manifest,
                prompt_path=args.prompt,
                fixtures_path=args.fixtures,
            )
            _write_jsonl(args.output, rows)
            print(f"wrote {args.kind} saved responses ({len(rows) - 1} items) to {args.output}")
        elif args.command == "import":
            rows = import_model_responses(
                requests_path=args.requests,
                model_output_path=args.model_output,
                metadata_path=args.metadata,
                manifest_path=args.manifest,
                prompt_path=args.prompt,
            )
            _write_jsonl(args.output, rows)
            print(f"imported {len(rows) - 1} real-model responses to {args.output}")
        elif args.command == "score":
            report = score_saved_run(
                args.responses,
                manifest_path=args.manifest,
                prompt_path=args.prompt,
                bootstrap_samples=args.bootstrap_samples,
            )
            _write_json(args.output, report)
            metrics = report["edit_correction"]
            print(
                f"edit P/R/F0.5={metrics['precision']:.4f}/{metrics['recall']:.4f}/"
                f"{metrics['f0_5']:.4f}; report={args.output}"
            )
        elif args.command == "verify":
            manifest, items = load_manifest(args.manifest)
            header, responses = load_saved_responses(
                args.responses,
                manifest=manifest,
                items=items,
                prompt_path=args.prompt,
            )
            print(f"valid saved run {header['run_id']}: {len(responses)} responses")
        return 0
    except EvaluationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
