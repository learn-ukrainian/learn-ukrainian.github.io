#!/usr/bin/env python3
"""Compose deterministic and semantic post-build review evidence.

The command is deliberately read-only with respect to the repository. It runs
the existing track deterministic audit without its mutating opt-ins, resolves
mechanical track policy, assembles the effective semantic prompt, and combines
an agent-authored semantic result into the canonical JSON schema.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SKILL_ROOT = PROJECT_ROOT / "agents_extensions" / "shared" / "skills" / "post-build-review"
POLICY_PATH = SKILL_ROOT / "config" / "track-policy.v1.yaml"
SCHEMA_PATH = SKILL_ROOT / "schema" / "review-result.v1.schema.json"
TRACK_AUDIT_CONFIG = PROJECT_ROOT / "scripts" / "audit" / "track_deterministic_audit_config.yaml"

CANONICAL_SEVERITIES = ("blocker", "high", "medium", "low", "info")
SEVERITY_ALIASES = {
    "critical": "blocker",
    "major": "high",
    "warning": "medium",
    "minor": "medium",
    "nit": "low",
}
CONNECTS_TO_RE = re.compile(r"^(?P<track>[a-z0-9-]+)-(?P<sequence>\d+)-(?P<slug>[a-z0-9-]+)$")


class ReviewProtocolError(RuntimeError):
    """Raised when protocol inputs cannot be resolved safely."""


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path, repo_root: Path = PROJECT_ROOT) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def resolve_repo_path(value: str, *, repo_root: Path = PROJECT_ROOT) -> Path:
    path = Path(value)
    if path.is_absolute():
        raise ReviewProtocolError(f"Repository path must be relative: {value!r}")
    resolved = (repo_root / path).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ReviewProtocolError(f"Repository path escapes the checkout: {value!r}") from exc
    return resolved


def read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReviewProtocolError(f"Expected YAML mapping: {display_path(path)}")
    return value


def load_track_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    policy = read_yaml(path)
    required = {
        "review_protocol_version",
        "deterministic_contract_version",
        "semantic_prompt_version",
        "track_policy_version",
        "families",
        "tracks",
    }
    missing = sorted(required - set(policy))
    if missing:
        raise ReviewProtocolError(f"Track policy missing: {', '.join(missing)}")
    return policy


def resolve_track_policy(track: str, policy: Mapping[str, Any]) -> dict[str, Any]:
    normalized = track.strip().lower()
    tracks = policy.get("tracks")
    if not isinstance(tracks, Mapping) or normalized not in tracks:
        raise ReviewProtocolError(f"Unknown track: {track!r}")
    track_config = tracks[normalized]
    if not isinstance(track_config, Mapping):
        raise ReviewProtocolError(f"Track policy must be a mapping: {normalized}")
    family_name = str(track_config.get("family") or "")
    families = policy.get("families")
    if not isinstance(families, Mapping) or family_name not in families:
        raise ReviewProtocolError(f"Unknown semantic family {family_name!r} for {normalized}")
    family_config = families[family_name]
    if not isinstance(family_config, Mapping):
        raise ReviewProtocolError(f"Family policy must be a mapping: {family_name}")
    merged = deepcopy(dict(family_config))
    for key, value in track_config.items():
        if key != "family":
            merged[key] = deepcopy(value)
    merged["family"] = family_name
    merged["track"] = normalized
    return merged


def _single_existing(candidates: Sequence[Path], label: str) -> Path | None:
    existing = sorted({path.resolve() for path in candidates if path.exists()})
    if len(existing) > 1:
        shown = ", ".join(path.as_posix() for path in existing)
        raise ReviewProtocolError(f"Ambiguous {label}: {shown}")
    return existing[0] if existing else None


def resolve_target(
    selector: str, *, repo_root: Path = PROJECT_ROOT, policy: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    if "/" not in selector.strip("/"):
        raise ReviewProtocolError("Target must be track/slug")
    track, slug = selector.strip("/").split("/", 1)
    track = track.lower()
    if not re.fullmatch(r"[a-z0-9-]+", track) or not re.fullmatch(r"[a-z0-9-]+", slug):
        raise ReviewProtocolError(f"Invalid target selector: {selector!r}")
    policy = policy or load_track_policy(repo_root / POLICY_PATH.relative_to(PROJECT_ROOT))
    track_policy = resolve_track_policy(track, policy)
    curriculum = repo_root / "curriculum" / "l2-uk-en"
    plan = curriculum / "plans" / track / f"{slug}.yaml"
    if not plan.exists():
        raise ReviewProtocolError(f"Missing plan: {display_path(plan, repo_root)}")

    track_dir = curriculum / track
    module_dir = track_dir / slug
    content = _single_existing(
        [module_dir / "module.md", track_dir / f"{slug}.md", *track_dir.glob(f"[0-9]*-{slug}.md")],
        "module content",
    )
    if content is None:
        raise ReviewProtocolError(f"No built content for {track}/{slug}")
    nested = content.name == "module.md" and content.parent == module_dir
    candidates: dict[str, Sequence[Path]] = {
        "activities": [module_dir / "activities.yaml"] if nested else [track_dir / "activities" / f"{slug}.yaml"],
        "vocabulary": [module_dir / "vocabulary.yaml"] if nested else [track_dir / "vocabulary" / f"{slug}.yaml"],
        "resources": [module_dir / "resources.yaml"] if nested else [track_dir / "resources" / f"{slug}.yaml"],
        "meta": [module_dir / "meta.yaml", track_dir / "meta" / f"{slug}.yaml"],
    }
    files: dict[str, str] = {
        "plan": display_path(plan, repo_root),
        "content": display_path(content, repo_root),
    }
    for name, paths in candidates.items():
        resolved = _single_existing(paths, name)
        if resolved is not None:
            files[name] = display_path(resolved, repo_root)
    return {
        "track": track,
        "slug": slug,
        "semantic_family": track_policy["family"],
        "layout": "directory" if nested else "flat",
        "files": files,
    }


def hash_target_files(target: Mapping[str, Any], *, repo_root: Path = PROJECT_ROOT) -> dict[str, str]:
    files = target.get("files")
    if not isinstance(files, Mapping):
        raise ReviewProtocolError("Target files must be a mapping")
    return {
        str(name): sha256_file(resolve_repo_path(str(path), repo_root=repo_root))
        for name, path in sorted(files.items())
    }


def resolve_venv_python(repo_root: Path = PROJECT_ROOT) -> Path:
    direct = repo_root / ".venv" / "bin" / "python"
    if direct.exists():
        # Preserve the venv entrypoint path. Resolving its interpreter symlink
        # bypasses pyvenv.cfg on symlink-based Linux environments.
        return direct
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode == 0:
        common_dir = Path(result.stdout.strip()).resolve()
        shared = common_dir.parent / ".venv" / "bin" / "python"
        if shared.exists():
            return shared
    raise ReviewProtocolError("Repository .venv/bin/python is unavailable")


RunCommand = Callable[..., subprocess.CompletedProcess[str]]


def _command_provenance(
    canonical_argv: list[str],
    executed_argv: list[str],
    result: subprocess.CompletedProcess[str],
    *,
    config_path: str,
    config_version: str,
) -> dict[str, Any]:
    return {
        "argv": canonical_argv,
        "executed_argv": executed_argv,
        "cwd": ".",
        "exit_code": result.returncode,
        "stdout_sha256": sha256_text(result.stdout),
        "stderr_sha256": sha256_text(result.stderr),
        "config_path": config_path,
        "config_version": config_version,
    }


def _run_json_command(
    canonical_argv: list[str],
    *,
    repo_root: Path,
    config_path: str,
    config_version: str,
    runner: RunCommand = subprocess.run,
) -> tuple[Any | None, dict[str, Any], str | None]:
    python = resolve_venv_python(repo_root)
    executed_argv = [str(python), *canonical_argv[1:]]
    result = runner(executed_argv, cwd=repo_root, capture_output=True, check=False, text=True)
    provenance = _command_provenance(
        canonical_argv,
        canonical_argv,
        result,
        config_path=config_path,
        config_version=config_version,
    )
    if result.returncode != 0:
        return None, provenance, f"command_exit_{result.returncode}: {result.stderr[-500:]}"
    try:
        return json.loads(result.stdout), provenance, None
    except json.JSONDecodeError as exc:
        return None, provenance, f"invalid_json: {exc}"


def run_existing_deterministic_audits(
    target: Mapping[str, Any],
    *,
    repo_root: Path = PROJECT_ROOT,
    policy: Mapping[str, Any],
    runner: RunCommand = subprocess.run,
) -> dict[str, Any]:
    track = str(target["track"])
    slug = str(target["slug"])
    audit_config = read_yaml(repo_root / TRACK_AUDIT_CONFIG.relative_to(PROJECT_ROOT))
    audit_config_version = str(audit_config.get("version"))
    audit_argv = [
        ".venv/bin/python",
        "scripts/audit/track_deterministic_audit.py",
        "--track",
        track,
        "--slugs",
        slug,
        "--format",
        "json",
        "--fail-on",
        "never",
    ]
    audit_data, audit_provenance, audit_error = _run_json_command(
        audit_argv,
        repo_root=repo_root,
        config_path="scripts/audit/track_deterministic_audit_config.yaml",
        config_version=audit_config_version,
        runner=runner,
    )

    size_argv = [
        ".venv/bin/python",
        "scripts/audit/module_size_policy_audit.py",
        "--tracks",
        track,
        "--slugs",
        slug,
        "--built-only",
        "--format",
        "json",
    ]
    size_data, size_provenance, size_error = _run_json_command(
        size_argv,
        repo_root=repo_root,
        config_path="agents_extensions/shared/skills/post-build-review/contracts/evidence-derived-size-policy-contract.md",
        config_version=str(policy["deterministic_contract_version"]),
        runner=runner,
    )
    size_record = size_data[0] if isinstance(size_data, list) and len(size_data) == 1 else None
    if size_data is not None and size_record is None:
        size_error = "expected exactly one size-policy record"
    return {
        "track_audit": {
            "status": "complete" if audit_error is None else "error",
            "provenance": audit_provenance,
            "result": audit_data,
            "error": audit_error,
        },
        "size_policy": {
            "status": "complete" if size_error is None else "error",
            "provenance": size_provenance,
            "result": size_record,
            "error": size_error,
        },
    }


def normalize_severity(value: str) -> str:
    normalized = value.strip().lower()
    normalized = SEVERITY_ALIASES.get(normalized, normalized)
    if normalized not in CANONICAL_SEVERITIES:
        raise ReviewProtocolError(f"Unknown severity: {value!r}")
    return normalized


def _policy_finding(
    finding_id: str, category: str, severity: str, message: str, *, evidence: str, location: str | None = None
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "source": "track_policy",
        "category": category,
        "severity": normalize_severity(severity),
        "message": message,
        "evidence": evidence,
        "location": location,
    }


def _check_size_policy_status(
    target: Mapping[str, Any],
    track_policy: Mapping[str, Any],
    size_record: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    if size_record is None:
        return []
    severities = track_policy.get("size_policy_signal_severities")
    if not isinstance(severities, Mapping):
        return []
    raw_signals = size_record.get("decision_signals") or [size_record.get("status")]
    signals = [str(signal) for signal in raw_signals if str(signal) in severities]
    messages = {
        "missing_plan_word_target": "Plan has no enforceable word floor.",
        "invalid_size_policy": "Explicit size-policy override is invalid.",
        "missing_dossier": "Required seminar research dossier is missing.",
        "plan_review_needed": "Grounded material and the reviewed plan floor require plan review; automatic expansion is forbidden.",
        "below_plan_floor": "Authored instructional prose is below the reviewed plan floor.",
        "repetitive_authored_prose": "Deterministic paragraph evidence found repetitive authored exposition requiring revision.",
        "over_advisory_ceiling": "Module exceeds the advisory ceiling; inspect source density and marginal pedagogical value without failing on length alone.",
        "exceptional_justification_required": "Exceptional length requires explicit source-backed pedagogical justification.",
    }
    findings: list[dict[str, Any]] = []
    content_path = str(target["files"].get("content") or target["files"]["plan"])
    for signal in dict.fromkeys(signals):
        location = (
            str(target["files"]["plan"])
            if signal in {
                "missing_plan_word_target",
                "invalid_size_policy",
                "missing_dossier",
                "plan_review_needed",
            }
            else content_path
        )
        findings.append(
            _policy_finding(
                f"size-policy-{signal}",
                "size_policy",
                str(severities[signal]),
                messages.get(signal, "Evidence-derived size policy requires review."),
                evidence=(
                    f"signal={signal}; status={size_record.get('status')}; "
                    f"notes={size_record.get('notes')}; "
                    f"repetition={size_record.get('repetition')}"
                ),
                location=location,
            )
        )
    return findings


def _check_connects_to(
    plan: Mapping[str, Any],
    plan_path: Path,
    spec: object,
    *,
    repo_root: Path,
) -> list[dict[str, Any]]:
    if not spec:
        return []
    severity = str(spec.get("severity", "high")) if isinstance(spec, Mapping) else "high"
    findings: list[dict[str, Any]] = []
    for index, raw in enumerate(plan.get("connects_to") or []):
        if not isinstance(raw, str):
            findings.append(
                _policy_finding(
                    f"connects-to-shape-{index}",
                    "crosslink_integrity",
                    severity,
                    "connects_to entries must be strings.",
                    evidence=repr(raw),
                    location=display_path(plan_path, repo_root),
                )
            )
            continue
        match = CONNECTS_TO_RE.fullmatch(raw)
        if not match:
            findings.append(
                _policy_finding(
                    f"connects-to-format-{index}",
                    "crosslink_integrity",
                    severity,
                    "connects_to entry does not match track-sequence-slug.",
                    evidence=raw,
                    location=display_path(plan_path, repo_root),
                )
            )
            continue
        linked_plan = repo_root / "curriculum" / "l2-uk-en" / "plans" / match["track"] / f"{match['slug']}.yaml"
        if not linked_plan.exists():
            findings.append(
                _policy_finding(
                    f"connects-to-missing-{index}",
                    "crosslink_integrity",
                    severity,
                    "connects_to target plan does not exist.",
                    evidence=raw,
                    location=display_path(plan_path, repo_root),
                )
            )
            continue
        actual = read_yaml(linked_plan).get("sequence")
        if str(actual) != str(int(match["sequence"])):
            findings.append(
                _policy_finding(
                    f"connects-to-sequence-{index}",
                    "crosslink_integrity",
                    severity,
                    "connects_to sequence does not match the target plan.",
                    evidence=f"declared={raw}; target_sequence={actual}",
                    location=display_path(plan_path, repo_root),
                )
            )
    return findings


def _dotted_value(mapping: Mapping[str, Any], dotted: str) -> Any:
    value: Any = mapping
    for part in dotted.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def _check_forbidden_placeholders(
    plan: Mapping[str, Any],
    plan_path: Path,
    specs: object,
    *,
    repo_root: Path,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for index, spec in enumerate(specs or []):
        if not isinstance(spec, Mapping):
            raise ReviewProtocolError("forbidden_placeholders entries must be mappings")
        dotted = str(spec.get("path") or "")
        value = _dotted_value(plan, dotted)
        forbidden = {str(item).strip().upper() for item in spec.get("values") or []}
        if value is not None and str(value).strip().upper() in forbidden:
            findings.append(
                _policy_finding(
                    f"forbidden-placeholder-{index}",
                    str(spec.get("category") or "unresolved_placeholder"),
                    str(spec.get("severity") or "high"),
                    str(spec.get("message") or f"Unresolved placeholder at {dotted}."),
                    evidence=f"{dotted}={value}",
                    location=display_path(plan_path, repo_root),
                )
            )
    return findings


def evaluate_mechanical_track_policy(
    target: Mapping[str, Any],
    track_policy: Mapping[str, Any],
    *,
    repo_root: Path = PROJECT_ROOT,
    size_record: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    plan_path = resolve_repo_path(str(target["files"]["plan"]), repo_root=repo_root)
    plan = read_yaml(plan_path)
    checks = track_policy.get("mechanical_checks")
    if not isinstance(checks, Mapping):
        return []
    return [
        *_check_size_policy_status(target, track_policy, size_record),
        *_check_connects_to(plan, plan_path, checks.get("connects_to_sequence"), repo_root=repo_root),
        *_check_forbidden_placeholders(
            plan,
            plan_path,
            checks.get("forbidden_placeholders"),
            repo_root=repo_root,
        ),
    ]


def assess_skips(track_result: Mapping[str, Any], track_policy: Mapping[str, Any]) -> list[dict[str, Any]]:
    allowed = track_policy.get("skip_policy")
    if not isinstance(allowed, Mapping):
        allowed = {}
    assessments: list[dict[str, Any]] = []
    for skipped in track_result.get("skipped") or []:
        category = str(skipped.get("category") or "unknown")
        disposition = str(allowed.get(category) or "unclassified")
        assessments.append(
            {
                "category": category,
                "disposition": disposition,
                "reason": str(skipped.get("reason") or ""),
            }
        )
    return assessments


def aggregate_deterministic(deterministic: Mapping[str, Any]) -> dict[str, Any]:
    """Return a pure, fail-closed summary of deterministic review evidence."""
    severities = {severity: 0 for severity in CANONICAL_SEVERITIES}
    track_result = deterministic.get("track_audit", {}).get("result") or {}
    for finding in track_result.get("findings") or []:
        severities[normalize_severity(str(finding.get("severity") or ""))] += 1
    for finding in deterministic.get("policy_findings") or []:
        severities[normalize_severity(str(finding.get("severity") or ""))] += 1

    reasons: list[str] = []
    for stage_name in ("track_audit", "size_policy"):
        if deterministic.get(stage_name, {}).get("status") != "complete":
            reasons.append(f"{stage_name} did not complete")
    required_skips = sorted(
        {
            str(item.get("category"))
            for item in deterministic.get("skip_assessments") or []
            if item.get("disposition") in {"required", "unclassified"}
        }
    )
    if required_skips:
        reasons.append("required or unclassified skips: " + ", ".join(required_skips))
    if reasons:
        status = "incomplete"
    elif severities["blocker"] or severities["high"]:
        status = "block"
    elif severities["medium"]:
        status = "review"
    else:
        status = "clear"
    return {
        "status": status,
        "findings_by_severity": severities,
        "reasons": reasons,
    }


def assemble_semantic_prompt(
    target: Mapping[str, Any],
    track_policy: Mapping[str, Any],
    deterministic: Mapping[str, Any],
    source_hashes: Mapping[str, str],
    *,
    repo_root: Path = PROJECT_ROOT,
) -> tuple[str, list[str]]:
    common_rel = "agents_extensions/shared/skills/post-build-review/prompts/common-semantic-review-prompt.md"
    family_rel = str(track_policy["semantic_prompt"])
    paths = [common_rel, family_rel]
    pieces = [(repo_root / path).read_text(encoding="utf-8").rstrip() for path in paths]
    track_result = deterministic["track_audit"].get("result") or {}
    context = {
        "target": target,
        "source_hashes": source_hashes,
        "deterministic_summary": track_result.get("summary"),
        "deterministic_findings": track_result.get("findings"),
        "mechanical_policy_findings": deterministic.get("policy_findings"),
        "skip_assessments": deterministic.get("skip_assessments"),
        "size_policy": deterministic["size_policy"].get("result"),
        "resolved_track_policy": {
            "family": track_policy.get("family"),
            "track": track_policy.get("track"),
            "semantic_requirements": track_policy.get("semantic_requirements"),
            "mechanical_checks": track_policy.get("mechanical_checks"),
            "size_policy_blocking_statuses": track_policy.get("size_policy_blocking_statuses"),
            "skip_policy": track_policy.get("skip_policy"),
        },
    }
    pieces.append(
        "# Resolved review context\n\n```json\n"
        + json.dumps(context, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n```"
    )
    return "\n\n---\n\n".join(pieces) + "\n", paths


def prepare_review(
    selector: str,
    reviewer: Mapping[str, str],
    *,
    repo_root: Path = PROJECT_ROOT,
    runner: RunCommand = subprocess.run,
) -> dict[str, Any]:
    policy_path = repo_root / POLICY_PATH.relative_to(PROJECT_ROOT)
    policy = load_track_policy(policy_path)
    target = resolve_target(selector, repo_root=repo_root, policy=policy)
    track_policy = resolve_track_policy(str(target["track"]), policy)
    source_hashes = hash_target_files(target, repo_root=repo_root)
    deterministic = run_existing_deterministic_audits(target, repo_root=repo_root, policy=policy, runner=runner)
    track_result = deterministic["track_audit"].get("result") or {}
    deterministic["policy_findings"] = evaluate_mechanical_track_policy(
        target,
        track_policy,
        repo_root=repo_root,
        size_record=deterministic["size_policy"].get("result"),
    )
    deterministic["skip_assessments"] = assess_skips(track_result, track_policy)
    deterministic["aggregate"] = aggregate_deterministic(deterministic)
    prompt_text, prompt_paths = assemble_semantic_prompt(
        target, track_policy, deterministic, source_hashes, repo_root=repo_root
    )
    return {
        "packet_version": "post-build-review.packet.v1",
        "review_protocol_version": str(policy["review_protocol_version"]),
        "deterministic_contract_version": str(policy["deterministic_contract_version"]),
        "semantic_prompt_version": str(policy["semantic_prompt_version"]),
        "track_policy_version": str(policy["track_policy_version"]),
        "prompt_sha256": sha256_text(prompt_text),
        "prompt_paths": prompt_paths,
        "semantic_prompt": prompt_text,
        "target": target,
        "source_hashes": source_hashes,
        "reviewer": dict(reviewer),
        "deterministic": deterministic,
    }


def source_drift_findings(packet: Mapping[str, Any], *, repo_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    current = hash_target_files(packet["target"], repo_root=repo_root)
    expected = packet.get("source_hashes") or {}
    findings: list[dict[str, Any]] = []
    for name in sorted(set(current) | set(expected)):
        if current.get(name) != expected.get(name):
            findings.append(
                _policy_finding(
                    f"source-drift-{name}",
                    "source_drift",
                    "blocker",
                    f"{name} changed after deterministic preparation.",
                    evidence=f"expected={expected.get(name)} current={current.get(name)}",
                    location=str(packet["target"]["files"].get(name)),
                )
            )
    return findings


def packet_integrity_findings(packet: Mapping[str, Any], *, repo_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    policy = load_track_policy(repo_root / POLICY_PATH.relative_to(PROJECT_ROOT))
    track_policy = resolve_track_policy(str(packet["target"]["track"]), policy)
    expected_prompt, expected_paths = assemble_semantic_prompt(
        packet["target"],
        track_policy,
        packet["deterministic"],
        packet["source_hashes"],
        repo_root=repo_root,
    )
    failures: list[str] = []
    actual_prompt = str(packet.get("semantic_prompt") or "")
    if sha256_text(actual_prompt) != packet.get("prompt_sha256"):
        failures.append("semantic_prompt does not match prompt_sha256")
    if actual_prompt != expected_prompt or packet.get("prompt_paths") != expected_paths:
        failures.append("semantic prompt does not match current canonical assembly")
    for key in (
        "review_protocol_version",
        "deterministic_contract_version",
        "semantic_prompt_version",
        "track_policy_version",
    ):
        if str(packet.get(key)) != str(policy[key]):
            failures.append(f"{key} does not match current policy")
    return [
        _policy_finding(
            f"packet-integrity-{index}",
            "packet_integrity",
            "blocker",
            message,
            evidence="Prepared packet is stale or was modified after preparation.",
        )
        for index, message in enumerate(failures)
    ]


def normalize_semantic_result(value: Mapping[str, Any], family: str) -> dict[str, Any]:
    verdict = str(value.get("verdict") or "").upper()
    if verdict not in {"PASS", "REVISE", "BLOCK", "INCOMPLETE"}:
        raise ReviewProtocolError(f"Invalid semantic verdict: {verdict!r}")
    findings = []
    for index, raw in enumerate(value.get("findings") or []):
        if not isinstance(raw, Mapping):
            raise ReviewProtocolError("Semantic findings must be mappings")
        findings.append(
            {
                "id": str(raw.get("id") or f"semantic-{index + 1}"),
                "source": "semantic",
                "category": str(raw.get("category") or "other"),
                "severity": normalize_severity(str(raw.get("severity") or "")),
                "message": str(raw.get("message") or ""),
                "evidence": str(raw.get("evidence") or ""),
                "location": str(raw["location"]) if raw.get("location") is not None else None,
            }
        )
    coverage = value.get("claim_coverage")
    if not isinstance(coverage, Mapping):
        raise ReviewProtocolError("semantic claim_coverage is required")
    status = str(coverage.get("status") or "")
    allowed_status = {"complete", "incomplete", "not_applicable"}
    if status not in allowed_status:
        raise ReviewProtocolError(f"Invalid claim coverage status: {status!r}")
    if family == "seminar" and status == "not_applicable":
        raise ReviewProtocolError("Seminar review requires exhaustive claim coverage")
    claims_total = int(coverage.get("claims_total") or 0)
    claims_verified = int(coverage.get("claims_verified") or 0)
    if claims_verified > claims_total:
        raise ReviewProtocolError("claims_verified cannot exceed claims_total")
    if family == "seminar" and status == "complete" and claims_total == 0:
        raise ReviewProtocolError("Complete seminar review must enumerate factual claims")
    return {
        "family": family,
        "verdict": verdict,
        "summary": str(value.get("summary") or ""),
        "claim_coverage": {
            "status": status,
            "claims_total": claims_total,
            "claims_verified": claims_verified,
        },
        "findings": findings,
    }


def _deterministic_findings(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    deterministic = packet["deterministic"]
    findings: list[dict[str, Any]] = []
    track_result = deterministic["track_audit"].get("result") or {}
    for index, raw in enumerate(track_result.get("findings") or []):
        findings.append(
            {
                "id": f"deterministic-{index + 1}",
                "source": "deterministic",
                "category": str(raw.get("category") or "other"),
                "severity": normalize_severity(str(raw.get("severity") or "")),
                "message": str(raw.get("message") or ""),
                "evidence": str(raw.get("evidence") or ""),
                "location": str(raw["file"]) if raw.get("file") is not None else None,
            }
        )
    findings.extend(deepcopy(deterministic.get("policy_findings") or []))
    return findings


def combine_disposition(
    deterministic: Mapping[str, Any],
    semantic: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    reasons: list[str] = []
    aggregate = deterministic.get("aggregate") or aggregate_deterministic(deterministic)
    reasons.extend(str(reason) for reason in aggregate.get("reasons") or [])
    coverage = semantic["claim_coverage"]
    if coverage["status"] == "incomplete" or coverage["claims_verified"] < coverage["claims_total"]:
        reasons.append("semantic claim coverage is incomplete")
    if semantic["verdict"] == "INCOMPLETE":
        reasons.append("semantic reviewer reported incomplete")
    integrity_categories = {item.get("category") for item in findings}
    if "source_drift" in integrity_categories:
        reasons.append("source files changed after deterministic preparation")
    if "packet_integrity" in integrity_categories:
        reasons.append("prepared packet failed integrity validation")
    if reasons:
        return {"status": "INCOMPLETE", "reasons": reasons}

    severities = {str(item["severity"]) for item in findings}
    if "blocker" in severities or semantic["verdict"] == "BLOCK":
        return {"status": "BLOCK", "reasons": ["blocking finding is unresolved"]}
    deterministic_high = any(
        item["source"] in {"deterministic", "track_policy"} and item["severity"] == "high" for item in findings
    )
    if deterministic_high:
        return {"status": "BLOCK", "reasons": ["high-severity mechanical finding is unresolved"]}
    if semantic["verdict"] == "REVISE" or severities.intersection({"high", "medium"}):
        return {"status": "REVISE", "reasons": ["actionable semantic finding is unresolved"]}
    return {"status": "PASS", "reasons": ["deterministic and semantic review passed"]}


def validate_result(result: Mapping[str, Any], *, schema_path: Path = SCHEMA_PATH) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(result)


def finalize_review(
    packet: Mapping[str, Any],
    semantic_input: Mapping[str, Any],
    *,
    repo_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    family = str(packet["target"]["semantic_family"])
    semantic = normalize_semantic_result(semantic_input, family)
    drift = source_drift_findings(packet, repo_root=repo_root)
    integrity = packet_integrity_findings(packet, repo_root=repo_root)
    deterministic = deepcopy(packet["deterministic"])
    deterministic["policy_findings"] = [
        *(deterministic.get("policy_findings") or []),
        *drift,
        *integrity,
    ]
    deterministic["aggregate"] = aggregate_deterministic(deterministic)
    normalized_packet = {**packet, "deterministic": deterministic}
    findings = [*_deterministic_findings(normalized_packet), *semantic["findings"]]
    disposition = combine_disposition(deterministic, semantic, findings)
    result: dict[str, Any] = {
        "schema_version": "post-build-review.result.v1",
        "review_protocol_version": str(packet["review_protocol_version"]),
        "deterministic_contract_version": str(packet["deterministic_contract_version"]),
        "semantic_prompt_version": str(packet["semantic_prompt_version"]),
        "track_policy_version": str(packet["track_policy_version"]),
        "prompt_sha256": str(packet["prompt_sha256"]),
        "target": deepcopy(packet["target"]),
        "source_hashes": deepcopy(packet["source_hashes"]),
        "reviewer": deepcopy(packet["reviewer"]),
        "deterministic": deterministic,
        "semantic": semantic,
        "findings": findings,
        "combined_disposition": disposition,
    }
    reproducible = {
        key: deepcopy(result[key])
        for key in (
            "schema_version",
            "review_protocol_version",
            "deterministic_contract_version",
            "semantic_prompt_version",
            "track_policy_version",
            "prompt_sha256",
            "target",
            "source_hashes",
            "deterministic",
            "semantic",
            "findings",
            "combined_disposition",
        )
    }
    result["reproducibility_key"] = sha256_text(_stable_json(reproducible))
    validate_result(result, schema_path=repo_root / SCHEMA_PATH.relative_to(PROJECT_ROOT))
    return result


def ensure_output_outside_repo(path: Path, *, repo_root: Path = PROJECT_ROOT) -> None:
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return
    raise ReviewProtocolError("Review outputs must be written outside the repository")


def _write_or_print(value: object, output: Path | None, *, repo_root: Path) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is None:
        print(text, end="")
        return
    ensure_output_outside_repo(output, repo_root=repo_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the canonical read-only post-build review protocol.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare", help="Run deterministic stages and assemble the semantic prompt.")
    prepare.add_argument("target", help="track/slug, e.g. bio/oleksandr-bilash")
    prepare.add_argument("--reviewer-agent", required=True)
    prepare.add_argument("--reviewer-family", required=True)
    prepare.add_argument("--reviewer-model", required=True)
    prepare.add_argument("--reviewer-effort", required=True)
    prepare.add_argument("--output", type=Path)

    finalize = subparsers.add_parser("finalize", help="Combine semantic JSON with a prepared packet.")
    finalize.add_argument("--packet", type=Path, required=True)
    finalize.add_argument("--semantic-result", type=Path, required=True)
    finalize.add_argument("--output", type=Path)

    validate = subparsers.add_parser("validate", help="Validate an existing canonical result.")
    validate.add_argument("result", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "prepare":
        reviewer = {
            "agent": args.reviewer_agent,
            "family": args.reviewer_family,
            "model": args.reviewer_model,
            "effort": args.reviewer_effort,
        }
        packet = prepare_review(args.target, reviewer)
        _write_or_print(packet, args.output, repo_root=PROJECT_ROOT)
        return 0
    if args.command == "finalize":
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
        semantic = json.loads(args.semantic_result.read_text(encoding="utf-8"))
        result = finalize_review(packet, semantic)
        _write_or_print(result, args.output, repo_root=PROJECT_ROOT)
        return 0 if result["combined_disposition"]["status"] == "PASS" else 1
    result = json.loads(args.result.read_text(encoding="utf-8"))
    validate_result(result)
    print("post-build-review result is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
