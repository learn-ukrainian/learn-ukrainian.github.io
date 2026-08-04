"""Build and apply the Phase 3 model-neutral correction/protection product.

The public bundle is a non-learning known-answer and non-erasure product.  The
``apply`` command operates only on a corpus supplied by the consumer and emits
reversible views; it never edits the input, trains a model, uploads data, or
turns abstentions into corrections.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import correction_factory as evaluation
from scripts.projects.open_model_data.correction_protection_rules import iter_rule_matches

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
EVIDENCE = ROOT / "data/projects/open_model_data/evidence"
DEFAULT_FACTORY_MANIFEST = EVIDENCE / "correction_protection_bundle_manifest_v1.json"
DEFAULT_FACTORY_RECEIPT = EVIDENCE / "correction_protection_release_receipt_v1.json"
DEFAULT_RELEASE = ROOT / "data/projects/open_model_data/release/correction_protection_v1"
VIEW_SCHEMA = CONTRACTS / "correction_protection_consumer_view_v1.schema.json"
PUBLIC_FILES = ("sources", "evidence", "cases", "disagreements")
VIEW_TYPES = ("correction", "filtering", "preference", "protection", "abstention")


class ConsumerError(ValueError):
    """The consumer product cannot be built or applied safely."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ConsumerError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConsumerError(f"cannot read JSON {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                require(line.endswith("\n") and bool(line.strip()), f"blank or unterminated row: {path}:{line_number}")
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ConsumerError(f"invalid JSONL: {path}:{line_number}") from exc
                require(isinstance(value, dict), f"non-object JSONL row: {path}:{line_number}")
                yield value
    except OSError as exc:
        raise ConsumerError(f"cannot read JSONL {path}: {exc}") from exc


def artifact(path: Path, *, logical_path: str | None = None) -> dict[str, Any]:
    require(path.is_file(), f"missing artifact: {path}")
    records = 1
    if path.suffix == ".jsonl":
        with path.open("rb") as handle:
            records = sum(1 for _ in handle)
    return {
        "logical_path": logical_path or path.as_posix(),
        "records": records,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def jsonl_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join((canonical_json(dict(row)) + "\n").encode("utf-8") for row in rows)


def stable_id(prefix: str, value: Mapping[str, Any]) -> str:
    return f"{prefix}:{sha256_text(canonical_json(value))}"


def evaluation_version() -> tuple[str, evaluation.EvaluationRegistry]:
    registry = evaluation.load_evaluation_registry()
    value = {
        "v011_manifest_sha256": registry.v011_manifest_sha256,
        "v02_packet_sha256": registry.v02_packet_sha256,
        "algorithm": "exact-sha256-plus-bounded-five-gram-jaccard-v1",
    }
    return sha256_text(canonical_json(value)), registry


def view_validator() -> Draft202012Validator:
    schema = read_json(VIEW_SCHEMA)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_view(value: Mapping[str, Any], validator: Draft202012Validator) -> None:
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        where = ".".join(str(part) for part in error.path) or "<root>"
        raise ConsumerError(f"consumer view schema failure at {where}: {error.message}")


def public_bundle(factory_public_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    manifest = read_json(DEFAULT_FACTORY_MANIFEST)
    bundle: dict[str, list[dict[str, Any]]] = {}
    for name in PUBLIC_FILES:
        path = factory_public_dir / f"{name}.jsonl"
        expected = manifest["outputs"][f"public_{name}"]
        actual = artifact(path, logical_path=f"public/{name}.jsonl")
        require(
            {key: actual[key] for key in ("records", "bytes", "sha256")}
            == {key: expected[key] for key in ("records", "bytes", "sha256")},
            f"factory public artifact drift: {name}",
        )
        bundle[name] = list(iter_jsonl(path))
    return bundle, manifest


def source_by_locator(bundle: Mapping[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    result = {row["source_locator_id"]: row for row in bundle["sources"]}
    require(len(result) == len(bundle["sources"]), "duplicate public source locator")
    return result


def original_value(case: Mapping[str, Any], source: Mapping[str, Any]) -> dict[str, Any]:
    text = source["context"]["context_text"]
    require(isinstance(text, str), "public source context text unavailable")
    start = int(case["original"]["start_offset"])
    end = int(case["original"]["end_offset"])
    require(0 <= start <= end <= len(text), "public case span outside context")
    surface = text[start:end]
    require(sha256_text(surface) == case["original"]["surface_sha256"], "public case surface hash drift")
    return {
        "immutable": True,
        "text": text,
        "surface": surface,
        "start_offset": start,
        "end_offset": end,
        "text_sha256": sha256_text(text),
        "surface_sha256": sha256_text(surface),
    }


def decision_for(case: Mapping[str, Any], view_type: str) -> tuple[str, str]:
    disposition = str(case["disposition"])
    if view_type in {"correction", "preference"}:
        return "propose_correction", "Use the reversible proposal as non-gold correction or preference evidence."
    if view_type == "filtering":
        if disposition == "excluded":
            return "exclude", "Exclude the span from a learning candidate view."
        if disposition == "unresolved":
            return "abstain", "Withhold the span from correction and learning decisions."
        return "retain", "Keep the span while correction and protection decisions remain separate views."
    if view_type == "protection":
        return "retain", "Retain the evidenced context and prohibit source-blind normalization."
    if view_type == "abstention":
        return "abstain", "Do not promote the case beyond its recorded evidence and category gate."
    if disposition in {"correct", "protected"}:
        return "retain", "Keep the span when filtering a consumer-controlled corpus."
    return "abstain", "Withhold the span from correction and learning decisions."


def public_views(bundle: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    sources = source_by_locator(bundle)
    firewall_version, _registry = evaluation_version()
    validator = view_validator()
    rows: list[dict[str, Any]] = []
    for case in bundle["cases"]:
        source = sources[case["source"]["source_locator_id"]]
        original = original_value(case, source)
        proposal = None
        if "proposal" in case:
            proposal = {
                "replacement": case["proposal"]["replacement"],
                "replacement_sha256": case["proposal"]["replacement_sha256"],
                "reversible": True,
            }
        view_types = ["filtering"]
        if case["disposition"] == "correction":
            view_types.extend(("correction", "preference"))
        if case["disposition"] == "protected":
            view_types.append("protection")
        if case["disposition"] == "unresolved" or case["category_gate"]["state"] == "research_only":
            view_types.append("abstention")
        for view_type in view_types:
            action, consumer_decision = decision_for(case, view_type)
            payload = {
                "schema_version": "correction_protection_consumer_view_v1",
                "view_type": view_type,
                "assurance_tier": "evidence_graded_non_gold",
                "authoritative": False,
                "source_origin": "public_canary",
                "record_id": case["case_id"],
                "category_id": case["category_gate"]["category_id"],
                "disposition": case["disposition"],
                "action": action,
                "original": original,
                "proposal": proposal if action == "propose_correction" else None,
                "evidence_refs": sorted(item["evidence_id"] for item in case["evidence_refs"]),
                "evaluation_firewall": {
                    "version": firewall_version,
                    "overlap_state": "public_canary",
                    "consumer_authorized_local_learning": False,
                    "learning_eligible": False,
                },
                "consumer_decision": consumer_decision,
            }
            payload["view_id"] = stable_id("cp_view", payload)
            validate_view(payload, validator)
            rows.append(payload)
    rows.sort(key=lambda row: (VIEW_TYPES.index(row["view_type"]), row["record_id"]))
    return rows


def correction_rules(bundle: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    sources = source_by_locator(bundle)
    rules: list[dict[str, Any]] = []
    for case in bundle["cases"]:
        if case["disposition"] != "correction":
            continue
        original = original_value(case, sources[case["source"]["source_locator_id"]])
        rules.append(
            {
                "case_id": case["case_id"],
                "category_id": case["category_gate"]["category_id"],
                "surface": original["surface"],
                "replacement": case["proposal"]["replacement"],
                "evidence_refs": sorted(item["evidence_id"] for item in case["evidence_refs"]),
            }
        )
    return sorted(rules, key=lambda row: (-len(row["surface"]), row["case_id"]))


def overlaps_evaluation(text: str, registry: evaluation.EvaluationRegistry) -> bool:
    exact = sha256_text(text) in (registry.v011_exact | registry.v02_exact)
    return exact or evaluation.is_near_duplicate(text, registry.v011_texts + registry.v02_texts)


def consumer_view(
    *,
    view_type: str,
    record_id: str,
    category_id: str,
    disposition: str,
    action: str,
    text: str,
    surface: str,
    start: int,
    end: int,
    replacement: str | None,
    evidence_refs: list[str],
    firewall_version: str,
    overlap_state: str,
    authorized: bool,
    consumer_decision: str,
    validator: Draft202012Validator,
) -> dict[str, Any]:
    learning_eligible = authorized and overlap_state == "clear" and action != "abstain"
    proposal = None
    if replacement is not None and action == "propose_correction":
        proposal = {
            "replacement": replacement,
            "replacement_sha256": sha256_text(replacement),
            "reversible": True,
        }
    value = {
        "schema_version": "correction_protection_consumer_view_v1",
        "view_type": view_type,
        "assurance_tier": "evidence_graded_non_gold",
        "authoritative": False,
        "source_origin": "consumer_controlled_corpus",
        "record_id": record_id,
        "category_id": category_id,
        "disposition": disposition,
        "action": action,
        "original": {
            "immutable": True,
            "text": text,
            "surface": surface,
            "start_offset": start,
            "end_offset": end,
            "text_sha256": sha256_text(text),
            "surface_sha256": sha256_text(surface),
        },
        "proposal": proposal,
        "evidence_refs": sorted(evidence_refs),
        "evaluation_firewall": {
            "version": firewall_version,
            "overlap_state": overlap_state,
            "consumer_authorized_local_learning": authorized,
            "learning_eligible": learning_eligible,
        },
        "consumer_decision": consumer_decision,
    }
    value["view_id"] = stable_id("cp_view", value)
    validate_view(value, validator)
    return value


def apply_record(
    row: Mapping[str, Any],
    *,
    rules: list[dict[str, Any]],
    firewall_version: str,
    registry: evaluation.EvaluationRegistry,
    authorized: bool,
    validator: Draft202012Validator,
) -> list[dict[str, Any]]:
    record_id = str(row.get("id", ""))
    text = row.get("text")
    require(record_id != "" and isinstance(text, str), "consumer row requires non-empty id and string text")
    if overlaps_evaluation(text, registry):
        evidence_ref = stable_id("cp_evidence", {"reason": "evaluation_overlap", "record_id": record_id})
        return [
            consumer_view(
                view_type="filtering",
                record_id=record_id,
                category_id="evaluation_firewall",
                disposition="excluded",
                action="exclude",
                text=text,
                surface=text,
                start=0,
                end=len(text),
                replacement=None,
                evidence_refs=[evidence_ref],
                firewall_version=firewall_version,
                overlap_state="matched",
                authorized=authorized,
                consumer_decision="Exclude the record from every learning view because it overlaps evaluation data.",
                validator=validator,
            )
        ]
    result: list[dict[str, Any]] = []
    for match in iter_rule_matches(text, rules):
        rule = match.rule
        if match.protected:
            for view_type in ("filtering", "protection"):
                result.append(
                    consumer_view(
                        view_type=view_type,
                        record_id=record_id,
                        category_id=rule["category_id"],
                        disposition="protected",
                        action="retain",
                        text=text,
                        surface=rule["surface"],
                        start=match.start,
                        end=match.end,
                        replacement=None,
                        evidence_refs=rule["evidence_refs"],
                        firewall_version=firewall_version,
                        overlap_state="clear",
                        authorized=authorized,
                        consumer_decision=(
                            "Retain the marked quotation in the filtering view."
                            if view_type == "filtering"
                            else "Retain the marked quotation; do not apply the narration correction rule."
                        ),
                        validator=validator,
                    )
                )
            continue
        for view_type in ("correction", "preference", "filtering"):
            is_filtering = view_type == "filtering"
            result.append(
                consumer_view(
                    view_type=view_type,
                    record_id=record_id,
                    category_id=rule["category_id"],
                    disposition="correction",
                    action="retain" if is_filtering else "propose_correction",
                    text=text,
                    surface=rule["surface"],
                    start=match.start,
                    end=match.end,
                    replacement=None if is_filtering else rule["replacement"],
                    evidence_refs=rule["evidence_refs"],
                    firewall_version=firewall_version,
                    overlap_state="clear",
                    authorized=authorized,
                    consumer_decision=(
                        "Retain the original span in the filtering view; keep correction evidence separate."
                        if is_filtering
                        else "Apply only the reversible proposal while retaining the immutable consumer source."
                        if view_type == "correction"
                        else "Prefer the proposal over the original surface without calling it human gold."
                    ),
                    validator=validator,
                )
            )
    if result:
        return result
    evidence_ref = stable_id("cp_evidence", {"reason": "no_released_rule", "record_id": record_id})
    return [
        consumer_view(
            view_type="abstention",
            record_id=record_id,
            category_id="no_released_rule",
            disposition="unresolved",
            action="abstain",
            text=text,
            surface=text,
            start=0,
            end=len(text),
            replacement=None,
            evidence_refs=[evidence_ref],
            firewall_version=firewall_version,
            overlap_state="clear",
            authorized=authorized,
            consumer_decision="No released rule applies; preserve the record and abstain.",
            validator=validator,
        )
    ]


def public_benchmark(bundle: Mapping[str, list[dict[str, Any]]]) -> dict[str, Any]:
    sources = source_by_locator(bundle)
    rules = correction_rules(bundle)
    firewall_version, registry = evaluation_version()
    validator = view_validator()
    counts = Counter()
    by_category: dict[str, Counter[str]] = defaultdict(Counter)
    for case in bundle["cases"]:
        source = sources[case["source"]["source_locator_id"]]
        text = source["context"]["context_text"]
        output = apply_record(
            {"id": case["case_id"], "text": text},
            rules=rules,
            firewall_version=firewall_version,
            registry=registry,
            authorized=False,
            validator=validator,
        )
        correction_emitted = any(row["view_type"] == "correction" for row in output)
        abstention_emitted = any(row["view_type"] == "abstention" for row in output)
        category = case["category_gate"]["category_id"]
        role = case["benchmark_role"]
        by_category[category]["abstention_emitted"] += int(abstention_emitted)
        if case["disposition"] == "correction":
            counts["correction_total"] += 1
            counts["correction_detected"] += int(correction_emitted)
            by_category[category]["correction_total"] += 1
            by_category[category]["correction_detected"] += int(correction_emitted)
        elif role == "acceptable_control":
            counts["control_total"] += 1
            counts["control_preserved"] += int(not correction_emitted)
            by_category[category]["control_total"] += 1
            by_category[category]["control_preserved"] += int(not correction_emitted)
            by_category[category]["false_corrections"] += int(correction_emitted)
        else:
            counts["protected_total"] += 1
            counts["protected_preserved"] += int(not correction_emitted)
            by_category[category]["protected_total"] += 1
            by_category[category]["protected_preserved"] += int(not correction_emitted)
            by_category[category]["false_corrections"] += int(correction_emitted)
    metrics: dict[str, dict[str, Any]] = {}
    for category, values in sorted(by_category.items()):
        detected = values["correction_detected"]
        positives = values["correction_total"]
        false_corrections = values["false_corrections"]
        predicted = detected + false_corrections
        protected_total = values["protected_total"] + values["control_total"]
        protected_preserved = values["protected_preserved"] + values["control_preserved"]
        metrics[category] = {
            **dict(sorted(values.items())),
            "correction_precision": (detected / predicted) if predicted else None,
            "correction_coverage": (detected / positives) if positives else None,
            "non_erasure_rate": (protected_preserved / protected_total) if protected_total else None,
        }
    narration = apply_record(
        {"id": "mandatory-narration", "text": "Фраза звучит значно вишуканіше."},
        rules=rules,
        firewall_version=firewall_version,
        registry=registry,
        authorized=False,
        validator=validator,
    )
    quotation = apply_record(
        {"id": "mandatory-quotation", "text": "Автор навів: «Фраза звучит значно вишуканіше.»"},
        rules=rules,
        firewall_version=firewall_version,
        registry=registry,
        authorized=False,
        validator=validator,
    )
    mandatory = {
        "narration_correction_detected": any(row["view_type"] == "correction" for row in narration),
        "quotation_protected": any(row["view_type"] == "protection" for row in quotation)
        and not any(row["view_type"] == "correction" for row in quotation),
    }
    passed = (
        counts["correction_detected"] == counts["correction_total"]
        and counts["control_preserved"] == counts["control_total"]
        and counts["protected_preserved"] == counts["protected_total"]
        and all(mandatory.values())
    )
    return {
        "schema_version": "correction_protection_non_erasure_report_v1",
        "passed": passed,
        "evaluation_firewall_version": firewall_version,
        "counts": dict(sorted(counts.items())),
        "by_category": metrics,
        "mandatory_zvuchyt": mandatory,
        "public_canaries_learning_eligible": False,
        "held_back_strategy": {
            "public_repo_copy": False,
            "external_locator": "batch_state/issue-6333/heldback/phase3-v1",
            "post_publication_refresh_required": True,
        },
    }


def coverage_report(
    bundle: Mapping[str, list[dict[str, Any]]],
    manifest: Mapping[str, Any],
    views: list[dict[str, Any]],
) -> dict[str, Any]:
    receipt = read_json(DEFAULT_FACTORY_RECEIPT)
    cases = bundle["cases"]
    disagreement_case_ids = {row["case_id"] for row in bundle["disagreements"]}
    disagreement_by_category = Counter(
        row["category_gate"]["category_id"] for row in cases if row["case_id"] in disagreement_case_ids
    )
    phenomenon = Counter(row["phenomenon"] for row in cases)
    phenomenon["Source-blind Phase 2 stand-off candidate; no span-level linguistic claim"] += 189150
    return {
        "schema_version": "correction_protection_coverage_report_v1",
        "bundle_id": manifest["bundle_id"],
        "full_bundle": {
            "records": manifest["record_counts"],
            "categories": manifest["category_counts"],
            "dispositions": manifest["disposition_counts"],
            "source_family": receipt["axes_coverage"]["source_family"],
            "period": receipt["axes_coverage"]["period"],
            "genre": receipt["axes_coverage"]["genre"],
            "register": receipt["axes_coverage"]["register"],
            "evidence_grade": receipt["evidence_grades"],
            "phenomenon": dict(sorted(phenomenon.items())),
        },
        "public_product": {
            "cases": len(cases),
            "by_category": dict(sorted(Counter(row["category_gate"]["category_id"] for row in cases).items())),
            "by_disposition": dict(sorted(Counter(row["disposition"] for row in cases).items())),
            "by_evidence_grade": dict(sorted(Counter(row["evidence_grade"] for row in cases).items())),
            "disagreed_cases": len(disagreement_case_ids),
            "disagreement_by_category": dict(sorted(disagreement_by_category.items())),
            "views": dict(sorted(Counter(row["view_type"] for row in views).items())),
        },
        "category_gates": manifest["category_gates"],
        "benchmark": public_benchmark(bundle),
        "limitations": [
            "The public cases are frozen known-answer and non-erasure canaries, not a learning export or human gold.",
            "The 189,150 Phase 2 complement cases remain source-blind stand-off candidates; only evidence-backed public positives emit correction.",
            "Surzhyk remains research-only and unresolved/protected; no global normalization rule is released.",
        ],
    }


def build_release(*, factory_public_dir: Path, output_dir: Path) -> dict[str, Any]:
    bundle, manifest = public_bundle(factory_public_dir)
    views = public_views(bundle)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in PUBLIC_FILES:
        source = factory_public_dir / f"{name}.jsonl"
        target = output_dir / f"{name}.jsonl"
        atomic_write(target, source.read_bytes())
    atomic_write(output_dir / "model_neutral_views.jsonl", jsonl_bytes(views))
    coverage = coverage_report(bundle, manifest, views)
    require(coverage["benchmark"]["passed"], "public non-erasure benchmark failed")
    atomic_write(output_dir / "coverage.json", (canonical_json(coverage) + "\n").encode("utf-8"))
    output_artifacts = {
        path.name: artifact(path, logical_path=f"data/projects/open_model_data/release/correction_protection_v1/{path.name}")
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path.name != "receipt.json"
    }
    receipt = {
        "schema_version": "correction_protection_consumer_release_receipt_v1",
        "bundle_id": manifest["bundle_id"],
        "inputs": {
            "factory_manifest": artifact(DEFAULT_FACTORY_MANIFEST, logical_path=DEFAULT_FACTORY_MANIFEST.relative_to(ROOT).as_posix()),
            "factory_receipt": artifact(DEFAULT_FACTORY_RECEIPT, logical_path=DEFAULT_FACTORY_RECEIPT.relative_to(ROOT).as_posix()),
            "view_schema": artifact(VIEW_SCHEMA, logical_path=VIEW_SCHEMA.relative_to(ROOT).as_posix()),
            "consumer": artifact(Path(__file__), logical_path=Path(__file__).relative_to(ROOT).as_posix()),
        },
        "outputs": output_artifacts,
        "consumer_decisions": [
            "correction: propose a reversible evidence-graded edit",
            "filtering: retain, exclude, or abstain without mutating source text",
            "preference: prefer the proposal over the original without a gold claim",
            "protection: retain quotation, historical, dialectal, regional, heritage, folklore, or contested context",
            "abstention: withhold weak, research-only, or unmatched cases",
        ],
        "evaluation_firewall": coverage["benchmark"]["evaluation_firewall_version"],
        "public_canaries_learning_eligible": False,
        "benchmark_passed": True,
        "determinism": {
            "serialization": "UTF-8 canonical JSON sorted keys LF",
            "timestamps_omitted": True,
        },
        "safety": {
            "project_model_training": False,
            "local_model_inference": False,
            "accelerator": False,
            "upload": False,
            "source_mutation": False,
            "human_gold": False,
            "authoritative": False,
        },
    }
    receipt["receipt_id"] = stable_id("cp_consumer_receipt", receipt)
    atomic_write(output_dir / "receipt.json", (canonical_json(receipt) + "\n").encode("utf-8"))
    return receipt


def apply_corpus(*, input_path: Path, release_dir: Path, output_dir: Path, authorized: bool) -> dict[str, Any]:
    bundle = {name: list(iter_jsonl(release_dir / f"{name}.jsonl")) for name in PUBLIC_FILES}
    rules = correction_rules(bundle)
    firewall_version, registry = evaluation_version()
    validator = view_validator()
    outputs: dict[str, list[dict[str, Any]]] = {name: [] for name in VIEW_TYPES}
    records = 0
    for row in iter_jsonl(input_path):
        records += 1
        for view in apply_record(
            row,
            rules=rules,
            firewall_version=firewall_version,
            registry=registry,
            authorized=authorized,
            validator=validator,
        ):
            outputs[view["view_type"]].append(view)
    require(records > 0, "consumer corpus is empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in outputs.items():
        atomic_write(output_dir / f"{name}.jsonl", jsonl_bytes(rows))
    receipt = {
        "schema_version": "correction_protection_consumer_run_receipt_v1",
        "input": artifact(input_path),
        "release_receipt": artifact(release_dir / "receipt.json"),
        "records": records,
        "view_counts": {name: len(rows) for name, rows in outputs.items()},
        "consumer_authorized_local_learning": authorized,
        "evaluation_firewall_version": firewall_version,
        "source_mutated": False,
        "training_performed": False,
        "upload_performed": False,
    }
    receipt["receipt_id"] = stable_id("cp_consumer_run", receipt)
    atomic_write(output_dir / "receipt.json", (canonical_json(receipt) + "\n").encode("utf-8"))
    return receipt


def benchmark_release(*, release_dir: Path, output: Path, heldback: Path | None, heldback_sha256: str | None) -> dict[str, Any]:
    bundle = {name: list(iter_jsonl(release_dir / f"{name}.jsonl")) for name in PUBLIC_FILES}
    report = public_benchmark(bundle)
    if heldback is not None:
        require(heldback_sha256 is not None, "--heldback-sha256 is required with --heldback")
        require(sha256_file(heldback) == heldback_sha256, "held-back artifact hash mismatch")
        report["held_back_strategy"] = {
            **report["held_back_strategy"],
            "provided": True,
            "artifact_sha256": heldback_sha256,
            "records": sum(1 for _ in iter_jsonl(heldback)),
        }
    else:
        require(heldback_sha256 is None, "--heldback is required with --heldback-sha256")
        report["held_back_strategy"] = {**report["held_back_strategy"], "provided": False}
    atomic_write(output, (canonical_json(report) + "\n").encode("utf-8"))
    return report


def verify_release(release_dir: Path) -> dict[str, Any]:
    receipt = read_json(release_dir / "receipt.json")
    require(receipt["schema_version"] == "correction_protection_consumer_release_receipt_v1", "wrong receipt version")
    for name, expected in receipt["outputs"].items():
        actual = artifact(release_dir / name, logical_path=expected["logical_path"])
        require(actual == expected, f"release artifact drift: {name}")
    bundle = {name: list(iter_jsonl(release_dir / f"{name}.jsonl")) for name in PUBLIC_FILES}
    report = public_benchmark(bundle)
    require(report["passed"], "release benchmark failed")
    return {"verified": True, "receipt_id": receipt["receipt_id"], "benchmark": report}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build-release")
    build.add_argument("--factory-public-dir", type=Path, required=True)
    build.add_argument("--output-dir", type=Path, default=DEFAULT_RELEASE)
    apply = subparsers.add_parser("apply")
    apply.add_argument("--input", type=Path, required=True)
    apply.add_argument("--release-dir", type=Path, default=DEFAULT_RELEASE)
    apply.add_argument("--output-dir", type=Path, required=True)
    apply.add_argument("--authorize-local-learning", action="store_true")
    benchmark = subparsers.add_parser("benchmark")
    benchmark.add_argument("--release-dir", type=Path, default=DEFAULT_RELEASE)
    benchmark.add_argument("--output", type=Path, required=True)
    benchmark.add_argument("--heldback", type=Path)
    benchmark.add_argument("--heldback-sha256")
    verify = subparsers.add_parser("verify")
    verify.add_argument("--release-dir", type=Path, default=DEFAULT_RELEASE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "build-release":
        value = build_release(factory_public_dir=args.factory_public_dir, output_dir=args.output_dir)
    elif args.command == "apply":
        value = apply_corpus(
            input_path=args.input,
            release_dir=args.release_dir,
            output_dir=args.output_dir,
            authorized=args.authorize_local_learning,
        )
    elif args.command == "benchmark":
        value = benchmark_release(
            release_dir=args.release_dir,
            output=args.output,
            heldback=args.heldback,
            heldback_sha256=args.heldback_sha256,
        )
    else:
        value = verify_release(args.release_dir)
    print(canonical_json(value))


if __name__ == "__main__":
    main()
