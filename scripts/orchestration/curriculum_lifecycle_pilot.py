#!/usr/bin/env python3
"""Deterministic cross-track shadow qualification and live-authorization gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from itertools import pairwise
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import post_build_review
from scripts.orchestration import curriculum_readiness, prompt_contracts

CONTRACT_ROOT = Path("agents_extensions/shared/curriculum-lifecycle")
DEFAULT_MATRIX_PATH = CONTRACT_ROOT / "config/pilot-matrix.v1.yaml"
MATRIX_SCHEMA_PATH = CONTRACT_ROOT / "schema/pilot-matrix.v1.schema.json"
REPORT_SCHEMA_PATH = CONTRACT_ROOT / "schema/pilot-report.v1.schema.json"
AUTHORIZATION_SCHEMA_PATH = CONTRACT_ROOT / "schema/pilot-authorization.v1.schema.json"
CERTIFICATION_PROFILES_PATH = CONTRACT_ROOT / "config/certification-profiles.v1.yaml"
TRACK_COMPLETION_CONFIG_PATH = Path("agents_extensions/shared/skills/track-completion/config/track-completion.v1.yaml")
LEARNER_BUNDLE_FILES = ("module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml")

REQUIRED_SCENARIOS = frozenset(
    {
        "built-folk-m01",
        "built-folk-wave",
        "built-folk-material-repair",
        "built-folk-minimal-repair",
        "built-bio",
        "built-a1",
        "built-a2",
        "built-b1",
        "built-b2",
        "unbuilt-bio-prepare",
        "unbuilt-c1",
        "unbuilt-c2",
        "unbuilt-seminar",
        "partial-ambiguous",
        "preparation-drift",
        "pbr-stale",
        "production-qg-pending",
        "production-qg-disarmed",
        "reviewer-instability",
        "crash-resume",
        "quota-pause",
    }
)

FIXTURE_ENTRIES: dict[str, dict[str, str]] = {
    "partial-ambiguous": {
        "module_state": "fixture",
        "preparation_state": "fixture",
        "state": "partial-recovery-required",
        "next_action": "recover",
    },
    "preparation-drift": {
        "module_state": "fixture",
        "preparation_state": "fixture",
        "state": "built-preparation-drift",
        "next_action": "rebuild",
    },
    "pbr-stale": {
        "module_state": "fixture",
        "preparation_state": "fixture",
        "state": "post-build-review-required",
        "next_action": "certify",
    },
    "production-qg-pending": {
        "module_state": "fixture",
        "preparation_state": "fixture",
        "state": "pbr-pass-qg-pending",
        "next_action": "hold",
    },
    "production-qg-disarmed": {
        "module_state": "fixture",
        "preparation_state": "fixture",
        "state": "certified-final",
        "next_action": "complete",
    },
    "reviewer-instability": {
        "module_state": "fixture",
        "preparation_state": "fixture",
        "state": "reviewer-instability",
        "next_action": "adjudicate",
    },
    "crash-resume": {
        "module_state": "fixture",
        "preparation_state": "fixture",
        "state": "module-active",
        "next_action": "resume",
    },
    "quota-pause": {
        "module_state": "fixture",
        "preparation_state": "fixture",
        "state": "paused-health",
        "next_action": "resume",
    },
}


class PilotError(RuntimeError):
    """Raised when pilot evidence is incomplete, stale, or unsafe."""


class _StrictLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_mapping(loader: _StrictLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise PilotError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_value(value: object) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _repo_file(repo_root: Path, raw: str | Path) -> Path:
    text = str(raw)
    relative = Path(text)
    if not text or relative.is_absolute() or ".." in relative.parts or "\\" in text or text.startswith("~"):
        raise PilotError(f"path must be repository-relative: {text!r}")
    root = repo_root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise PilotError(f"path escapes repository: {text!r}") from exc
    if not path.is_file():
        raise PilotError(f"required pilot file is missing: {text}")
    return path


def _repository_backed_file(repo_root: Path, path: Path) -> Path:
    if not path.is_absolute():
        return _repo_file(repo_root, path)
    root = repo_root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PilotError(f"pilot contract must be repository-backed: {path}") from exc
    if not resolved.is_file():
        raise PilotError(f"required pilot file is missing: {path}")
    return resolved


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PilotError(f"invalid JSON document {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PilotError(f"JSON document must be an object: {path}")
    return value


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.load(path.read_text(encoding="utf-8", errors="strict"), Loader=_StrictLoader)
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise PilotError(f"invalid YAML document {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PilotError(f"YAML document must be a mapping: {path}")
    return value


def _validate(value: Mapping[str, Any], schema_path: Path, label: str) -> None:
    schema = _read_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise PilotError(f"invalid JSON schema for {label}: {exc}") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise PilotError(f"{label} failed schema validation at {location}: {error.message}")


def _git(repo_root: Path, *args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=text,
    )
    if result.returncode:
        stderr = result.stderr.strip() if text else result.stderr.decode(errors="replace").strip()
        raise PilotError(f"git {' '.join(args)} failed: {stderr}")
    return result.stdout.strip() if text else result.stdout


def _commit_is_ancestor(repo_root: Path, commit: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", commit, "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in {0, 1}:
        raise PilotError(f"cannot verify historical commit {commit}: {result.stderr.strip()}")
    return result.returncode == 0


def _resume_evidence_exists(repo_root: Path, evidence: str) -> bool:
    if evidence.startswith("issue-"):
        return True
    test_paths = (
        "tests/orchestration/test_curriculum_coordinator.py",
        "tests/orchestration/test_curriculum_readiness.py",
        "tests/test_certification_evidence.py",
        "tests/test_track_completion.py",
    )
    needle = f"def {evidence}("
    return any(needle in _repo_file(repo_root, raw).read_text(encoding="utf-8") for raw in test_paths)


def _is_generated_artifact_path(path: Path) -> bool:
    parts = path.parts
    return parts[:2] == ("data", "telemetry") or (
        parts[:2] == ("curriculum", "l2-uk-en") and bool({"audit", "review", "status"}.intersection(parts[3:]))
    )


def _validate_matrix_semantics(matrix: Mapping[str, Any], repo_root: Path) -> None:
    rows = matrix["rows"]
    row_ids = [str(row["id"]) for row in rows]
    if len(row_ids) != len(set(row_ids)):
        raise PilotError("pilot row ids must be unique")
    scenarios = {str(row["scenario"]) for row in rows}
    missing = sorted(REQUIRED_SCENARIOS - scenarios)
    unknown = sorted(scenarios - REQUIRED_SCENARIOS)
    if missing or unknown:
        raise PilotError(f"pilot scenario coverage mismatch; missing={missing}, unknown={unknown}")

    wave = sorted(
        (
            int(row["wave"]["position"]),
            str(row["selector"]),
        )
        for row in rows
        if row.get("wave")
    )
    expected_wave = [
        (1, "folk/narodna-kultura-yak-systema"),
        (2, "folk/kalendarna-obriadovist-zvychai"),
        (3, "folk/koliadky-shchedrivky"),
    ]
    if wave != expected_wave:
        raise PilotError("FOLK pilot wave must be exactly M01-M03 in manifest order")

    for raw in matrix["identity_paths"]:
        path = Path(str(raw))
        if _is_generated_artifact_path(path):
            raise PilotError(f"generated artifact cannot be a pilot identity input: {raw}")
        _repo_file(repo_root, str(raw))

    for row in rows:
        transitions = row["transitions"]
        for prior, current in pairwise(transitions):
            if prior["to"] != current["from"]:
                raise PilotError(f"pilot row {row['id']} has a non-contiguous transition chain")
        if not _resume_evidence_exists(repo_root, str(row["resume_evidence"])):
            raise PilotError(f"pilot row {row['id']} references missing resume evidence")
        if row["kind"] == "fixture":
            if row["scenario"] not in FIXTURE_ENTRIES:
                raise PilotError(f"pilot fixture has no deterministic implementation: {row['scenario']}")
            continue
        track, slug = str(row["selector"]).split("/", 1)
        manifest, modules = curriculum_readiness.load_manifest_track(repo_root, track)
        if slug not in modules:
            raise PilotError(f"pilot target is not active in curriculum manifest: {row['selector']}")
        family = "core" if manifest["type"] == "core" else "seminar"
        if row["family"] != family:
            raise PilotError(f"pilot row family contradicts manifest: {row['id']}")
        if row["kind"] == "historical":
            provenance = row["provenance"]
            if provenance["outcome"] != row["expected"]["disposition"]:
                raise PilotError(f"historical outcome contradicts disposition: {row['id']}")
            if not _commit_is_ancestor(repo_root, str(provenance["merge_sha"])):
                raise PilotError(f"historical merge is not an ancestor of HEAD: {row['id']}")
            message = str(
                _git(
                    repo_root,
                    "show",
                    "-s",
                    "--format=%s%n%b",
                    str(provenance["merge_sha"]),
                )
            )
            if f"(#{provenance['pull_request']})" not in message or f"/{provenance['issue']}-" not in message:
                raise PilotError(f"historical merge does not bind configured issue/PR: {row['id']}")


def load_matrix(*, repo_root: Path = PROJECT_ROOT, matrix_path: Path = DEFAULT_MATRIX_PATH) -> dict[str, Any]:
    path = _repository_backed_file(repo_root, matrix_path)
    matrix = _read_yaml(path)
    _validate(matrix, _repo_file(repo_root, MATRIX_SCHEMA_PATH), "pilot matrix")
    _validate_matrix_semantics(matrix, repo_root)
    return matrix


def _learner_hashes(matrix: Mapping[str, Any], repo_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    selectors = sorted({str(row["selector"]) for row in matrix["rows"] if row["kind"] in {"repository", "historical"}})
    for selector in selectors:
        track, slug = selector.split("/", 1)
        candidates = [
            Path(f"curriculum/l2-uk-en/plans/{track}/{slug}.yaml"),
            *(Path(f"curriculum/l2-uk-en/{track}/{slug}/{name}") for name in LEARNER_BUNDLE_FILES),
        ]
        for relative in candidates:
            path = repo_root / relative
            if path.is_file():
                hashes[relative.as_posix()] = _sha256_bytes(path.read_bytes())
    return dict(sorted(hashes.items()))


def _phase(next_action: str) -> str:
    if next_action in {"prepare", "recover"}:
        return "prepare"
    if next_action == "plan":
        return "plan"
    if next_action in {"build", "rebuild"}:
        return "build"
    return "certify"


def _prompt_result(
    row: Mapping[str, Any],
    entry: Mapping[str, str],
    dependency_identity: str,
    repo_root: Path,
) -> dict[str, Any]:
    track, slug = str(row["selector"]).split("/", 1)
    context = {
        "track": track,
        "slug": slug,
        "family": row["family"],
        "phase": _phase(entry["next_action"]),
        "module_state": entry["module_state"],
        "evidence_identity": dependency_identity,
    }
    first = prompt_contracts.resolve_profile(str(row["prompt_profile"]), context=context, repo_root=repo_root)
    second = prompt_contracts.resolve_profile(str(row["prompt_profile"]), context=context, repo_root=repo_root)
    exact_replay = first.to_record() == second.to_record()
    required = row["prompt_assertions"]["required"]
    forbidden = row["prompt_assertions"]["forbidden"]
    policy_passed = all(marker in first.rendered_prompt for marker in required) and not any(
        marker in first.rendered_prompt for marker in forbidden
    )
    prompt_bytes = len(first.rendered_prompt.encode("utf-8"))
    context_bytes = len(_canonical_json(context).encode("utf-8"))
    return {
        "profile": row["prompt_profile"],
        "identity_sha256": first.identity_sha256,
        "prompt_sha256": first.prompt_sha256,
        "prompt_bytes": prompt_bytes,
        "context_bytes": context_bytes,
        "exact_replay": exact_replay,
        "policy_checks_passed": policy_passed,
    }


def _post_build_evidence_passes(row: Mapping[str, Any], repo_root: Path) -> bool:
    evidence = row.get("evidence")
    if not evidence:
        return True
    path = _repo_file(repo_root, str(evidence["path"]))
    value = _read_json(path)
    try:
        post_build_review.validate_result(value, repo_root=repo_root)
        target = post_build_review.resolve_target(str(row["selector"]), repo_root=repo_root)
        current_hashes = post_build_review.hash_target_files(target, repo_root=repo_root)
    except post_build_review.ReviewProtocolError as exc:
        raise PilotError(f"invalid post-build evidence for {row['id']}: {exc}") from exc
    return (
        value["combined_disposition"]["status"] == "PASS"
        and value["target"] == target
        and value["source_hashes"] == current_hashes
    )


def _repository_entry(row: Mapping[str, Any], repo_root: Path) -> tuple[dict[str, str], str]:
    track, slug = str(row["selector"]).split("/", 1)
    result = curriculum_readiness.evaluate_preparation(track, slug, repo_root=repo_root)
    entry = {key: str(result[key]) for key in ("module_state", "preparation_state", "state", "next_action")}
    dependency_identity = result.get("preparation_identity") or _sha256_value(
        {
            "selector": row["selector"],
            "sources": result["sources"],
            "requirements": result["requirements"],
        }
    )
    return entry, str(dependency_identity)


def _fixture_entry(row: Mapping[str, Any], repo_root: Path) -> tuple[dict[str, str], str]:
    scenario = str(row["scenario"])
    entry = dict(FIXTURE_ENTRIES[scenario])
    proof: dict[str, Any] = {"scenario": scenario, "transitions": row["transitions"]}
    if scenario in {"preparation-drift", "pbr-stale"}:
        before = curriculum_readiness.dependent_evidence_identity("post-build", "a" * 64, {"contract": "b" * 64})
        after = curriculum_readiness.dependent_evidence_identity("post-build", "c" * 64, {"contract": "b" * 64})
        if before == after:
            raise PilotError("preparation drift fixture did not invalidate dependent evidence")
        proof.update({"before": before, "after": after})
    elif scenario in {"production-qg-pending", "production-qg-disarmed"}:
        profiles = _read_yaml(_repo_file(repo_root, CERTIFICATION_PROFILES_PATH))
        profile_id = "core-pending" if scenario.endswith("pending") else "core-disabled"
        mode = profiles["profiles"][profile_id]["production_qg"]["mode"]
        expected_mode = "pending" if scenario.endswith("pending") else "disabled"
        if mode != expected_mode:
            raise PilotError(f"certification profile mode drifted for {scenario}")
        proof.update({"profile": profile_id, "mode": mode})
    elif scenario == "reviewer-instability":
        proof["material_fingerprints"] = sorted({_sha256_value("PASS"), _sha256_value("REVISE")})
        if len(proof["material_fingerprints"]) != 2:
            raise PilotError("reviewer instability fixture did not preserve disagreement")
    return entry, _sha256_value(proof)


def _row_result(row: Mapping[str, Any], repo_root: Path) -> dict[str, Any]:
    if row["kind"] == "fixture":
        entry, dependency_identity = _fixture_entry(row, repo_root)
        prompt = None
        prompt_passed = True
        freshness = "fixture-current"
    else:
        entry, dependency_identity = _repository_entry(row, repo_root)
        prompt = _prompt_result(row, entry, dependency_identity, repo_root)
        prompt_passed = bool(prompt["exact_replay"] and prompt["policy_checks_passed"])
        freshness = "historical-current" if row["kind"] == "historical" else "current"
    expected_entry = {
        key: str(row["expected"][key]) for key in ("module_state", "preparation_state", "state", "next_action")
    }
    passed = entry == expected_entry and prompt_passed and _post_build_evidence_passes(row, repo_root)
    return {
        "id": row["id"],
        "scenario": row["scenario"],
        "selector": row["selector"],
        "kind": row["kind"],
        "entry": entry,
        "dependency_identity": dependency_identity,
        "transitions": row["transitions"],
        "disposition": row["expected"]["disposition"],
        "resume_evidence": row["resume_evidence"],
        "cleanup_state": row["expected"]["cleanup_state"],
        "prompt": prompt,
        "freshness": freshness,
        "mutation_detected": False,
        "passed": passed,
    }


def _report_metrics(matrix: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    prompt_rows = [row for row in rows if row["prompt"] is not None]
    matrix_by_id = {row["id"]: row for row in matrix["rows"]}
    return {
        "row_count": len(rows),
        "prompt_bytes": sum(int(row["prompt"]["prompt_bytes"]) for row in prompt_rows),
        "context_bytes": sum(int(row["prompt"]["context_bytes"]) for row in prompt_rows),
        "model_calls": 0,
        "provider_cost_usd": 0,
        "resolver_requests": 2 * len(prompt_rows),
        "resolver_exact_replays": sum(bool(row["prompt"]["exact_replay"]) for row in prompt_rows),
        "external_cache_used": False,
        "false_positive_checks": sum(
            len(matrix_by_id[row["id"]]["prompt_assertions"][kind])
            for row in prompt_rows
            for kind in ("required", "forbidden")
        ),
        "false_positive_failures": sum(not bool(row["prompt"]["policy_checks_passed"]) for row in prompt_rows),
        "evidence_freshness": "current" if all(row["passed"] for row in rows) else "stale",
    }


def _source_records(matrix: Mapping[str, Any], repo_root: Path) -> list[dict[str, str]]:
    return [
        {"path": str(raw), "sha256": _sha256_bytes(_repo_file(repo_root, str(raw)).read_bytes())}
        for raw in sorted(matrix["identity_paths"])
    ]


def _report_identity(report: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in report.items() if key != "identity_sha256"}
    return _sha256_value(payload)


def build_shadow_report(
    *,
    repo_root: Path = PROJECT_ROOT,
    matrix_path: Path = DEFAULT_MATRIX_PATH,
) -> dict[str, Any]:
    matrix_file = _repository_backed_file(repo_root, matrix_path)
    matrix = load_matrix(repo_root=repo_root, matrix_path=matrix_file)
    before = _learner_hashes(matrix, repo_root)
    rows = [_row_result(row, repo_root) for row in matrix["rows"]]
    after = _learner_hashes(matrix, repo_root)
    mutated = before != after
    if mutated:
        for row in rows:
            row["mutation_detected"] = True
            row["passed"] = False
    sources = _source_records(matrix, repo_root)
    report: dict[str, Any] = {
        "schema_version": "curriculum-lifecycle-pilot-report.v1",
        "mode": "shadow",
        "verdict": "PASS" if all(row["passed"] for row in rows) and not mutated else "HOLD",
        "matrix_sha256": _sha256_bytes(matrix_file.read_bytes()),
        "source_commit": str(_git(repo_root, "rev-parse", "HEAD")),
        "source_tree_sha256": _sha256_value(sources),
        "identity_sha256": "0" * 64,
        "contract_sources": sources,
        "learner_tree": {
            "before_sha256": _sha256_value(before),
            "after_sha256": _sha256_value(after),
            "unchanged": not mutated,
            "file_count": len(before),
        },
        "rows": rows,
        "metrics": _report_metrics(matrix, rows),
        "live_authorization": {
            "eligible": False,
            "reason": "separate-exact-report-review-and-human-authorization-required",
            "production_qg_armed": False,
        },
    }
    report["identity_sha256"] = _report_identity(report)
    validate_report_value(
        report,
        matrix=matrix,
        repo_root=repo_root,
        matrix_path=matrix_file,
        verify_current_rows=False,
    )
    return report


def validate_report_value(
    report: Mapping[str, Any],
    *,
    matrix: Mapping[str, Any],
    repo_root: Path,
    matrix_path: Path = DEFAULT_MATRIX_PATH,
    verify_current_rows: bool = True,
) -> None:
    _validate(report, _repo_file(repo_root, REPORT_SCHEMA_PATH), "pilot report")
    if report["identity_sha256"] != _report_identity(report):
        raise PilotError("pilot report identity does not match its canonical payload")
    matrix_file = _repository_backed_file(repo_root, matrix_path)
    if report["matrix_sha256"] != _sha256_bytes(matrix_file.read_bytes()):
        raise PilotError("pilot report matrix identity is stale")
    expected_ids = [row["id"] for row in matrix["rows"]]
    actual_ids = [row["id"] for row in report["rows"]]
    if actual_ids != expected_ids or len(actual_ids) != len(set(actual_ids)):
        raise PilotError("pilot report must contain every matrix row exactly once in order")
    sources = _source_records(matrix, repo_root)
    if report["contract_sources"] != sources or report["source_tree_sha256"] != _sha256_value(sources):
        raise PilotError("pilot report contract source evidence is stale")
    if not _commit_is_ancestor(repo_root, str(report["source_commit"])):
        raise PilotError("pilot report source commit is not an ancestor of HEAD")
    if verify_current_rows:
        current_learner_hashes = _learner_hashes(matrix, repo_root)
        current_learner_identity = _sha256_value(current_learner_hashes)
        if (
            report["learner_tree"]["before_sha256"] != current_learner_identity
            or report["learner_tree"]["after_sha256"] != current_learner_identity
            or report["learner_tree"]["file_count"] != len(current_learner_hashes)
        ):
            raise PilotError("pilot report learner-artifact evidence is stale")
        expected_rows = [_row_result(row, repo_root) for row in matrix["rows"]]
        if report["rows"] != expected_rows:
            raise PilotError("pilot report row evidence does not match a current shadow replay")
        if report["metrics"] != _report_metrics(matrix, expected_rows):
            raise PilotError("pilot report metrics do not match current row evidence")
    clean_pass = (
        all(row["passed"] and not row["mutation_detected"] for row in report["rows"])
        and report["learner_tree"]["unchanged"]
        and report["metrics"]["false_positive_failures"] == 0
        and report["metrics"]["resolver_requests"] == 2 * report["metrics"]["resolver_exact_replays"]
    )
    expected_verdict = "PASS" if clean_pass else "HOLD"
    if report["verdict"] != expected_verdict:
        raise PilotError("pilot report verdict contradicts row and mutation evidence")
    if report["live_authorization"]["eligible"]:
        raise PilotError("a shadow report cannot authorize live mutation")


def load_report(
    path: Path, *, repo_root: Path = PROJECT_ROOT, matrix_path: Path = DEFAULT_MATRIX_PATH
) -> dict[str, Any]:
    report = _read_json(path)
    matrix = load_matrix(repo_root=repo_root, matrix_path=matrix_path)
    validate_report_value(
        report,
        matrix=matrix,
        repo_root=repo_root,
        matrix_path=matrix_path,
    )
    return report


def _authorized_selectors(
    passed_rows: Mapping[str, Mapping[str, Any]],
    row_ids: Sequence[str],
    *,
    maximum_mutating_modules: int,
) -> list[str]:
    if any(row_id not in passed_rows for row_id in row_ids):
        raise PilotError("authorization scope includes an absent or non-PASS row")
    if any(passed_rows[row_id]["kind"] != "repository" for row_id in row_ids):
        raise PilotError("live authorization scope may contain repository rows only")
    selectors = sorted({str(passed_rows[row_id]["selector"]) for row_id in row_ids})
    if len(selectors) > maximum_mutating_modules:
        raise PilotError("authorization scope exceeds its maximum mutating modules")
    return selectors


def verify_authorization(
    authorization_path: Path,
    report_path: Path,
    *,
    repo_root: Path = PROJECT_ROOT,
    matrix_path: Path = DEFAULT_MATRIX_PATH,
) -> dict[str, Any]:
    report = load_report(report_path, repo_root=repo_root, matrix_path=matrix_path)
    authorization = _read_json(authorization_path)
    _validate(
        authorization,
        _repo_file(repo_root, AUTHORIZATION_SCHEMA_PATH),
        "pilot authorization",
    )
    report_sha256 = _sha256_bytes(report_path.read_bytes())
    if report["verdict"] != "PASS":
        raise PilotError("live authorization requires a PASS shadow report")
    if authorization["matrix_sha256"] != report["matrix_sha256"]:
        raise PilotError("authorization matrix identity does not match the report")
    if authorization["report_sha256"] != report_sha256:
        raise PilotError("authorization does not bind the exact report bytes")
    if authorization["report_identity_sha256"] != report["identity_sha256"]:
        raise PilotError("authorization does not bind the report semantic identity")
    review = authorization["review"]
    if review["reviewed_report_sha256"] != report_sha256:
        raise PilotError("independent review did not bind the exact report bytes")
    family_groups = _read_yaml(_repo_file(repo_root, TRACK_COMPLETION_CONFIG_PATH))["review_family_groups"]
    author_group = family_groups.get(review["author_family"].strip().lower())
    reviewer_group = family_groups.get(review["reviewer_family"].strip().lower())
    if not author_group or not reviewer_group:
        raise PilotError("pilot authorization uses an unregistered review family")
    if author_group == reviewer_group:
        raise PilotError("pilot authorization requires an independent cross-family review")
    try:
        relative_report = report_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise PilotError("authorized report must be repository-backed") from exc
    if not _commit_is_ancestor(repo_root, str(authorization["reviewed_commit"])):
        raise PilotError("reviewed commit is not an ancestor of HEAD")
    reviewed_bytes = _git(
        repo_root,
        "show",
        f"{authorization['reviewed_commit']}:{relative_report}",
        text=False,
    )
    if _sha256_bytes(reviewed_bytes) != report_sha256:
        raise PilotError("reviewed commit does not contain the exact authorized report")
    passed_rows = {row["id"]: row for row in report["rows"] if row["passed"]}
    scope = authorization["scope"]
    row_ids = scope["row_ids"]
    selectors = scope["selectors"]
    expected_selectors = _authorized_selectors(
        passed_rows,
        row_ids,
        maximum_mutating_modules=scope["maximum_mutating_modules"],
    )
    if sorted(selectors) != expected_selectors:
        raise PilotError("authorization selectors do not exactly match its repository row scope")
    if authorization["production_qg_armed"]:
        raise PilotError("pilot authorization cannot arm production QG")
    return authorization


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or verify the deterministic curriculum-lifecycle pilot gate.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    shadow = subparsers.add_parser("shadow", help="Run the read-only cross-track matrix")
    shadow.add_argument("--output", type=Path)
    shadow.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX_PATH)
    validate = subparsers.add_parser("validate-report", help="Validate a shadow report")
    validate.add_argument("report", type=Path)
    validate.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX_PATH)
    authorization = subparsers.add_parser(
        "verify-authorization", help="Verify a separate human live-pilot authorization"
    )
    authorization.add_argument("authorization", type=Path)
    authorization.add_argument("--report", type=Path, required=True)
    authorization.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX_PATH)
    parser.add_argument("--repo-root", type=Path, default=PROJECT_ROOT, help=argparse.SUPPRESS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    matrix_path = args.matrix
    if args.command == "shadow":
        report = build_shadow_report(repo_root=repo_root, matrix_path=matrix_path)
        if args.output:
            _write_json(args.output, report)
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if report["verdict"] == "PASS" else 1
    if args.command == "validate-report":
        load_report(args.report, repo_root=repo_root, matrix_path=matrix_path)
        print("curriculum-lifecycle pilot report is valid")
        return 0
    verify_authorization(
        args.authorization,
        args.report,
        repo_root=repo_root,
        matrix_path=matrix_path,
    )
    print("curriculum-lifecycle live-pilot authorization is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
