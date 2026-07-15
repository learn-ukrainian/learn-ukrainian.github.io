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
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.orchestration.prompt_contracts import (
    LifecycleConfigError,
    load_active_tracks,
    reject_stale_track_keys,
    resolve_profile_selectors,
)

CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SKILL_ROOT = PROJECT_ROOT / "agents_extensions" / "shared" / "skills" / "post-build-review"
POLICY_PATH = SKILL_ROOT / "config" / "track-policy.v1.yaml"
SCHEMA_PATHS = {
    "post-build-review.result.v1": SKILL_ROOT / "schema" / "review-result.v1.schema.json",
    "post-build-review.result.v2": SKILL_ROOT / "schema" / "review-result.v2.schema.json",
    "post-build-review.result.v3": SKILL_ROOT / "schema" / "review-result.v3.schema.json",
}
CURRENT_PACKET_VERSION = "post-build-review.packet.v3"
CURRENT_RESULT_SCHEMA_VERSION = "post-build-review.result.v3"
TRACK_AUDIT_CONFIG = PROJECT_ROOT / "scripts" / "audit" / "track_deterministic_audit_config.yaml"

CANONICAL_SEVERITIES = ("blocker", "high", "medium", "low", "info")
QUALITY_DIMENSIONS = ("pedagogical", "naturalness", "decolonization", "engagement", "tone")
REPRODUCIBILITY_FIELDS = (
    "schema_version",
    "review_protocol_version",
    "deterministic_contract_version",
    "semantic_prompt_version",
    "track_policy_version",
    "prompt_sha256",
    "target",
    "source_hashes",
    "reviewer",
    "semantic_response",
    "deterministic",
    "semantic",
    "findings",
    "combined_disposition",
)
SEVERITY_ALIASES = {
    "critical": "blocker",
    "major": "high",
    "warning": "medium",
    "minor": "medium",
    "nit": "low",
}
CONNECTS_TO_RE = re.compile(r"^(?P<track>[a-z0-9-]+)-(?P<sequence>\d+)-(?P<slug>[a-z0-9-]+)$")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


class ReviewProtocolError(RuntimeError):
    """Raised when protocol inputs cannot be resolved safely."""


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def load_track_policy(
    path: Path = POLICY_PATH,
    *,
    repo_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    policy = read_yaml(path)
    required = {
        "review_protocol_version",
        "deterministic_contract_version",
        "semantic_prompt_version",
        "track_policy_version",
        "families",
        "selectors",
        "track_overrides",
    }
    missing = sorted(required - set(policy))
    if missing:
        raise ReviewProtocolError(f"Track policy missing: {', '.join(missing)}")
    if "tracks" in policy:
        raise ReviewProtocolError("Track policy must derive active tracks from curriculum.yaml")
    families = policy.get("families")
    overrides = policy.get("track_overrides")
    if not isinstance(families, Mapping) or not isinstance(overrides, Mapping):
        raise ReviewProtocolError("Track policy families and track_overrides must be mappings")
    try:
        active_tracks = load_active_tracks(repo_root)
        resolved = resolve_profile_selectors(
            selectors=policy["selectors"],
            profile_families={str(family): str(family) for family in families},
            active_tracks=active_tracks,
            label="post-build track policy",
        )
        reject_stale_track_keys(overrides, active_tracks, label="post-build track override")
    except LifecycleConfigError as exc:
        raise ReviewProtocolError(str(exc)) from exc
    tracks: dict[str, dict[str, Any]] = {}
    for track, family in resolved.items():
        override = overrides.get(track, {})
        if not isinstance(override, Mapping) or "family" in override:
            raise ReviewProtocolError(f"Track override must be policy data without family: {track}")
        tracks[track] = {"family": family, **dict(override)}
    policy["tracks"] = tracks
    return policy


def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = deepcopy(dict(base))
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


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
    defaults = policy.get("defaults")
    if defaults is not None and not isinstance(defaults, Mapping):
        raise ReviewProtocolError("Track policy defaults must be a mapping")
    merged = _deep_merge(defaults or {}, family_config)
    merged = _deep_merge(merged, {key: value for key, value in track_config.items() if key != "family"})
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
    policy = policy or load_track_policy(
        repo_root / POLICY_PATH.relative_to(PROJECT_ROOT), repo_root=repo_root
    )
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


def _learner_surface_texts(
    target: Mapping[str, Any], *, repo_root: Path = PROJECT_ROOT
) -> dict[str, str]:
    files = target.get("files")
    if not isinstance(files, Mapping):
        raise ReviewProtocolError("Target files must be a mapping")
    texts: dict[str, str] = {}
    for name in ("content", "activities", "vocabulary", "resources"):
        if name not in files:
            continue
        path = resolve_repo_path(str(files[name]), repo_root=repo_root)
        text = path.read_text(encoding="utf-8")
        texts[display_path(path, repo_root)] = HTML_COMMENT_RE.sub(
            lambda match: re.sub(r"[^\n]", " ", match.group(0)), text
        )
    return texts


def _configured_pattern(spec: Mapping[str, Any]) -> re.Pattern[str]:
    pattern = spec.get("regex")
    if not isinstance(pattern, str) or not pattern:
        raise ReviewProtocolError("Mechanical learner-surface pattern requires a regex")
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise ReviewProtocolError(f"Invalid learner-surface regex {pattern!r}: {exc}") from exc


def scan_learner_workflow_leakage(
    texts: Mapping[str, str], spec: object
) -> list[dict[str, Any]]:
    if not spec:
        return []
    if not isinstance(spec, Mapping):
        raise ReviewProtocolError("learner_workflow_leakage must be a mapping")
    severity = str(spec.get("severity") or "medium")
    findings: list[dict[str, Any]] = []
    occurrence = 0
    for raw_pattern in spec.get("patterns") or []:
        if not isinstance(raw_pattern, Mapping):
            raise ReviewProtocolError("learner_workflow_leakage patterns must be mappings")
        pattern_id = str(raw_pattern.get("id") or "workflow-register")
        pattern = _configured_pattern(raw_pattern)
        for path, text in texts.items():
            for line_no, line in enumerate(text.splitlines(), start=1):
                for match in pattern.finditer(line):
                    occurrence += 1
                    findings.append(
                        _policy_finding(
                            f"learner-workflow-leakage-{pattern_id}-{occurrence}",
                            "learner_workflow_leakage",
                            severity,
                            "Internal research/build workflow language leaked to a learner surface.",
                            evidence=match.group(0),
                            location=f"{path}:{line_no}",
                        )
                    )
    return findings


def inventory_evidence_requirements(
    texts: Mapping[str, str], specs: object
) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    for raw_spec in specs or []:
        if not isinstance(raw_spec, Mapping):
            raise ReviewProtocolError("evidence_requirements entries must be mappings")
        pattern_id = str(raw_spec.get("id") or "evidence")
        modality = str(raw_spec.get("modality") or "")
        if modality not in {"text", "audio", "video", "image", "interactive"}:
            raise ReviewProtocolError(f"Invalid evidence modality: {modality!r}")
        pattern = _configured_pattern(raw_spec)
        exclude_pattern: re.Pattern[str] | None = None
        if "exclude_line_regex" in raw_spec:
            exclude_pattern = _configured_pattern(
                {"regex": raw_spec.get("exclude_line_regex")}
            )
        occurrence = 0
        for path, text in texts.items():
            for line_no, line in enumerate(text.splitlines(), start=1):
                if exclude_pattern is not None and exclude_pattern.search(line):
                    continue
                match = pattern.search(line)
                if match is None:
                    continue
                occurrence += 1
                requirements.append(
                    {
                        "id": f"{pattern_id}-{occurrence}",
                        "modality": modality,
                        "location": f"{path}:{line_no}",
                        "evidence": match.group(0),
                    }
                )
    return requirements


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
    learner_texts = _learner_surface_texts(target, repo_root=repo_root)
    return [
        *_check_size_policy_status(target, track_policy, size_record),
        *_check_connects_to(plan, plan_path, checks.get("connects_to_sequence"), repo_root=repo_root),
        *_check_forbidden_placeholders(
            plan,
            plan_path,
            checks.get("forbidden_placeholders"),
            repo_root=repo_root,
        ),
        *scan_learner_workflow_leakage(learner_texts, checks.get("learner_workflow_leakage")),
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
        "learner_evidence_requirements": deterministic.get("evidence_requirements"),
        "skip_assessments": deterministic.get("skip_assessments"),
        "size_policy": deterministic["size_policy"].get("result"),
        "resolved_track_policy": {
            "family": track_policy.get("family"),
            "track": track_policy.get("track"),
            "semantic_requirements": track_policy.get("semantic_requirements"),
            "mechanical_checks": track_policy.get("mechanical_checks"),
            "size_policy_signal_severities": track_policy.get("size_policy_signal_severities"),
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
    policy = load_track_policy(policy_path, repo_root=repo_root)
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
    checks = track_policy.get("mechanical_checks")
    deterministic["evidence_requirements"] = inventory_evidence_requirements(
        _learner_surface_texts(target, repo_root=repo_root),
        checks.get("evidence_requirements") if isinstance(checks, Mapping) else None,
    )
    deterministic["skip_assessments"] = assess_skips(track_result, track_policy)
    deterministic["aggregate"] = aggregate_deterministic(deterministic)
    prompt_text, prompt_paths = assemble_semantic_prompt(
        target, track_policy, deterministic, source_hashes, repo_root=repo_root
    )
    return {
        "packet_version": CURRENT_PACKET_VERSION,
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
    policy = load_track_policy(
        repo_root / POLICY_PATH.relative_to(PROJECT_ROOT), repo_root=repo_root
    )
    track_policy = resolve_track_policy(str(packet["target"]["track"]), policy)
    expected_prompt, expected_paths = assemble_semantic_prompt(
        packet["target"],
        track_policy,
        packet["deterministic"],
        packet["source_hashes"],
        repo_root=repo_root,
    )
    failures: list[str] = []
    if packet.get("packet_version") != CURRENT_PACKET_VERSION:
        failures.append("packet_version is not the current canonical version")
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


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ReviewProtocolError(f"Duplicate JSON key: {key!r}")
        value[key] = item
    return value


def _reject_json_constant(value: str) -> None:
    raise ReviewProtocolError(f"Non-standard JSON constant: {value}")


def parse_semantic_response(raw: bytes) -> tuple[Mapping[str, Any] | None, dict[str, Any]]:
    provenance: dict[str, Any] = {
        "raw_sha256": sha256_bytes(raw),
        "byte_count": len(raw),
        "parser": "strict-json-object-v1",
        "parse_status": "invalid",
        "contract_status": "not_evaluated",
        "error": None,
    }
    try:
        text = raw.decode("utf-8", errors="strict")
        parsed = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
        if not isinstance(parsed, Mapping):
            raise ReviewProtocolError("Semantic response root must be one JSON object")
    except (UnicodeDecodeError, json.JSONDecodeError, ReviewProtocolError) as exc:
        provenance["error"] = str(exc)
        return None, provenance
    provenance["parse_status"] = "valid"
    return parsed, provenance


def _require_exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    missing = sorted(expected - set(value))
    extra = sorted(set(value) - expected)
    if missing or extra:
        details = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if extra:
            details.append("extra=" + ",".join(extra))
        raise ReviewProtocolError(f"{label} fields are invalid: {'; '.join(details)}")


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewProtocolError(f"{label} must be a non-empty string")
    return value


def _nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReviewProtocolError(f"{label} must be a non-negative integer")
    return value


def normalize_semantic_result(
    value: Mapping[str, Any],
    family: str,
    reviewer: Mapping[str, Any],
    evidence_requirements: Sequence[Mapping[str, Any]] = (),
    source_texts: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    _require_exact_keys(
        value,
        {
            "verdict",
            "summary",
            "quality_dimensions",
            "claim_coverage",
            "claim_ledger",
            "learner_evidence_ledger",
            "findings",
        },
        "semantic response",
    )
    verdict = value["verdict"]
    if verdict not in {"PASS", "REVISE", "BLOCK", "INCOMPLETE"}:
        raise ReviewProtocolError(f"Invalid semantic verdict: {verdict!r}")
    summary = value["summary"]
    if not isinstance(summary, str):
        raise ReviewProtocolError("semantic summary must be a string")

    raw_findings = value["findings"]
    if not isinstance(raw_findings, list):
        raise ReviewProtocolError("Semantic findings must be a list")
    findings: list[dict[str, Any]] = []
    finding_ids: set[str] = set()
    expected_finding_keys = {
        "id",
        "issue_id",
        "category",
        "severity",
        "message",
        "evidence",
        "location",
    }
    for raw in raw_findings:
        if not isinstance(raw, Mapping):
            raise ReviewProtocolError("Semantic findings must be mappings")
        _require_exact_keys(raw, expected_finding_keys, "semantic finding")
        finding_id = _nonempty_string(raw["id"], "semantic finding id")
        if finding_id in finding_ids:
            raise ReviewProtocolError(f"Duplicate semantic finding id: {finding_id}")
        finding_ids.add(finding_id)
        issue_id = _nonempty_string(raw["issue_id"], "semantic finding issue_id")
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", issue_id) is None:
            raise ReviewProtocolError(
                f"Semantic finding issue_id must be uppercase underscore form: {issue_id!r}"
            )
        location = raw["location"]
        if location is not None and not isinstance(location, str):
            raise ReviewProtocolError("semantic finding location must be a string or null")
        semantic_severity = _nonempty_string(raw["severity"], "semantic finding severity")
        if semantic_severity not in CANONICAL_SEVERITIES:
            raise ReviewProtocolError(f"Invalid semantic finding severity: {semantic_severity!r}")
        findings.append(
            {
                "id": finding_id,
                "issue_id": issue_id,
                "source": "semantic",
                "category": _nonempty_string(raw["category"], "semantic finding category"),
                "severity": semantic_severity,
                "message": _nonempty_string(raw["message"], "semantic finding message"),
                "evidence": _nonempty_string(raw["evidence"], "semantic finding evidence"),
                "location": location,
            }
        )

    raw_dimensions = value["quality_dimensions"]
    if not isinstance(raw_dimensions, Mapping):
        raise ReviewProtocolError("quality_dimensions must be a mapping")
    _require_exact_keys(raw_dimensions, set(QUALITY_DIMENSIONS), "quality dimensions")
    dimensions: dict[str, dict[str, Any]] = {}
    dimension_statuses = {"PASS", "REVISE", "BLOCK", "INCOMPLETE"}
    expected_dimension_keys = {"status", "evidence", "finding_ids"}
    source_lookup = dict(source_texts or {})
    for dimension in QUALITY_DIMENSIONS:
        raw = raw_dimensions[dimension]
        if not isinstance(raw, Mapping):
            raise ReviewProtocolError(f"Quality dimension {dimension} must be a mapping")
        _require_exact_keys(raw, expected_dimension_keys, f"quality dimension {dimension}")
        dimension_status = raw["status"]
        if dimension_status not in dimension_statuses:
            raise ReviewProtocolError(
                f"Invalid quality dimension status for {dimension}: {dimension_status!r}"
            )
        raw_evidence = raw["evidence"]
        if not isinstance(raw_evidence, list):
            raise ReviewProtocolError(f"Quality dimension {dimension} evidence must be a list")
        if dimension_status != "INCOMPLETE" and not raw_evidence:
            raise ReviewProtocolError(f"Quality dimension {dimension} requires cited evidence")
        dimension_evidence: list[dict[str, str]] = []
        for item in raw_evidence:
            if not isinstance(item, Mapping):
                raise ReviewProtocolError(
                    f"Quality dimension {dimension} evidence entries must be mappings"
                )
            _require_exact_keys(item, {"location", "excerpt"}, f"quality dimension {dimension} evidence")
            location = _nonempty_string(item["location"], f"quality dimension {dimension} location")
            excerpt = _nonempty_string(item["excerpt"], f"quality dimension {dimension} excerpt")
            if len(excerpt.strip()) < 8:
                raise ReviewProtocolError(
                    f"Quality dimension {dimension} evidence excerpt must contain at least 8 characters"
                )
            if source_lookup:
                matching_paths = [
                    path
                    for path in source_lookup
                    if location == path or location.startswith(f"{path}:")
                ]
                if not matching_paths:
                    raise ReviewProtocolError(
                        f"Quality dimension {dimension} evidence location is not a target file: {location}"
                    )
                if not any(excerpt in source_lookup[path] for path in matching_paths):
                    raise ReviewProtocolError(
                        f"Quality dimension {dimension} evidence excerpt is not present at {location}"
                    )
            dimension_evidence.append({"location": location, "excerpt": excerpt})
        raw_dimension_finding_ids = raw["finding_ids"]
        if not isinstance(raw_dimension_finding_ids, list):
            raise ReviewProtocolError(
                f"Quality dimension {dimension} finding_ids must be a list"
            )
        dimension_finding_ids: list[str] = []
        for finding_id_value in raw_dimension_finding_ids:
            referenced = _nonempty_string(
                finding_id_value, f"quality dimension {dimension} finding id"
            )
            if referenced in dimension_finding_ids:
                raise ReviewProtocolError(
                    f"Quality dimension {dimension} repeats finding {referenced}"
                )
            if referenced not in finding_ids:
                raise ReviewProtocolError(
                    f"Quality dimension {dimension} references unknown finding {referenced}"
                )
            dimension_finding_ids.append(referenced)
        referenced_severities = {
            finding["severity"] for finding in findings if finding["id"] in dimension_finding_ids
        }
        if dimension_status == "PASS" and referenced_severities.intersection(
            {"blocker", "high", "medium"}
        ):
            raise ReviewProtocolError(
                f"Quality dimension {dimension} PASS references a material finding"
            )
        if dimension_status == "REVISE" and not referenced_severities.intersection(
            {"high", "medium"}
        ):
            raise ReviewProtocolError(
                f"Quality dimension {dimension} REVISE requires a high or medium finding"
            )
        if dimension_status == "BLOCK" and "blocker" not in referenced_severities:
            raise ReviewProtocolError(
                f"Quality dimension {dimension} BLOCK requires a blocker finding"
            )
        if dimension_status == "INCOMPLETE" and not dimension_finding_ids:
            raise ReviewProtocolError(
                f"Quality dimension {dimension} INCOMPLETE requires a finding"
            )
        dimensions[dimension] = {
            "status": dimension_status,
            "evidence": dimension_evidence,
            "finding_ids": dimension_finding_ids,
        }

    nonpassing_dimensions = {
        dimension: entry["status"]
        for dimension, entry in dimensions.items()
        if entry["status"] != "PASS"
    }
    if verdict == "PASS" and nonpassing_dimensions:
        raise ReviewProtocolError(
            "Semantic PASS requires PASS for every quality dimension: "
            + ", ".join(sorted(nonpassing_dimensions))
        )
    if any(status == "INCOMPLETE" for status in nonpassing_dimensions.values()) and verdict != "INCOMPLETE":
        raise ReviewProtocolError("An incomplete quality dimension requires semantic INCOMPLETE")
    if any(status == "BLOCK" for status in nonpassing_dimensions.values()) and verdict not in {
        "BLOCK",
        "INCOMPLETE",
    }:
        raise ReviewProtocolError("A blocked quality dimension requires semantic BLOCK or INCOMPLETE")
    if any(status == "REVISE" for status in nonpassing_dimensions.values()) and verdict == "PASS":
        raise ReviewProtocolError("A revisable quality dimension is inconsistent with semantic PASS")

    coverage = value["claim_coverage"]
    if not isinstance(coverage, Mapping):
        raise ReviewProtocolError("semantic claim_coverage is required")
    _require_exact_keys(
        coverage,
        {"status", "claims_total", "claims_checked", "claims_supported"},
        "claim coverage",
    )
    status = coverage["status"]
    if status not in {"complete", "incomplete", "not_applicable"}:
        raise ReviewProtocolError(f"Invalid claim coverage status: {status!r}")
    claims_total = _nonnegative_int(coverage["claims_total"], "claims_total")
    claims_checked = _nonnegative_int(coverage["claims_checked"], "claims_checked")
    claims_supported = _nonnegative_int(coverage["claims_supported"], "claims_supported")

    raw_claims = value["claim_ledger"]
    if not isinstance(raw_claims, list):
        raise ReviewProtocolError("claim_ledger must be a list")
    claims: list[dict[str, Any]] = []
    claim_ids: set[str] = set()
    claim_statuses = {"supported", "contradicted", "imprecise", "unattested", "unverifiable"}
    expected_claim_keys = {"id", "claim", "location", "status", "evidence", "finding_id"}
    for raw in raw_claims:
        if not isinstance(raw, Mapping):
            raise ReviewProtocolError("claim_ledger entries must be mappings")
        _require_exact_keys(raw, expected_claim_keys, "claim ledger entry")
        claim_id = _nonempty_string(raw["id"], "claim id")
        if claim_id in claim_ids:
            raise ReviewProtocolError(f"Duplicate claim id: {claim_id}")
        claim_ids.add(claim_id)
        claim_status = raw["status"]
        if claim_status not in claim_statuses:
            raise ReviewProtocolError(f"Invalid claim status: {claim_status!r}")
        finding_id = raw["finding_id"]
        if claim_status == "supported" and finding_id is not None:
            raise ReviewProtocolError(f"Supported claim {claim_id} cannot reference a finding")
        if claim_status != "supported":
            finding_id = _nonempty_string(finding_id, f"finding_id for claim {claim_id}")
            if finding_id not in finding_ids:
                raise ReviewProtocolError(f"Claim {claim_id} references unknown finding {finding_id}")
        claims.append(
            {
                "id": claim_id,
                "claim": _nonempty_string(raw["claim"], f"claim text for {claim_id}"),
                "location": _nonempty_string(raw["location"], f"claim location for {claim_id}"),
                "status": claim_status,
                "evidence": _nonempty_string(raw["evidence"], f"claim evidence for {claim_id}"),
                "finding_id": finding_id,
            }
        )
    actual_checked = sum(claim["status"] != "unverifiable" for claim in claims)
    actual_supported = sum(claim["status"] == "supported" for claim in claims)
    if claims_total != len(claims):
        raise ReviewProtocolError(f"claims_total={claims_total} does not match ledger length={len(claims)}")
    if claims_checked != actual_checked:
        raise ReviewProtocolError(f"claims_checked={claims_checked} does not match ledger={actual_checked}")
    if claims_supported != actual_supported:
        raise ReviewProtocolError(f"claims_supported={claims_supported} does not match ledger={actual_supported}")
    if family == "seminar" and status == "not_applicable":
        raise ReviewProtocolError("Seminar review requires exhaustive claim coverage")
    if family == "seminar" and status == "complete" and claims_total == 0:
        raise ReviewProtocolError("Complete seminar review must enumerate factual claims")
    if status == "complete" and claims_checked != claims_total:
        raise ReviewProtocolError("Complete claim coverage requires every claim to be checked")
    if status == "not_applicable" and (claims_total or claims_checked or claims_supported):
        raise ReviewProtocolError("not_applicable claim coverage requires an empty ledger")

    raw_evidence = value["learner_evidence_ledger"]
    if not isinstance(raw_evidence, list):
        raise ReviewProtocolError("learner_evidence_ledger must be a list")
    evidence_ledger: list[dict[str, Any]] = []
    evidence_ids: set[str] = set()
    expected_evidence_keys = {
        "id",
        "location",
        "task",
        "modality",
        "source",
        "access_status",
        "verification_method",
        "finding_id",
    }
    modalities = {"text", "audio", "video", "image", "interactive"}
    access_statuses = {"verified_access", "metadata_only", "inaccessible", "not_provided", "reviewer_unverified"}
    capabilities = set(reviewer.get("capabilities") or [])
    finding_severities = {finding["id"]: finding["severity"] for finding in findings}
    for raw in raw_evidence:
        if not isinstance(raw, Mapping):
            raise ReviewProtocolError("learner_evidence_ledger entries must be mappings")
        _require_exact_keys(raw, expected_evidence_keys, "learner evidence entry")
        evidence_id = _nonempty_string(raw["id"], "learner evidence id")
        if evidence_id in evidence_ids:
            raise ReviewProtocolError(f"Duplicate learner evidence id: {evidence_id}")
        evidence_ids.add(evidence_id)
        modality = raw["modality"]
        if modality not in modalities:
            raise ReviewProtocolError(f"Invalid learner evidence modality: {modality!r}")
        access_status = raw["access_status"]
        if access_status not in access_statuses:
            raise ReviewProtocolError(f"Invalid learner evidence access status: {access_status!r}")
        finding_id = raw["finding_id"]
        if access_status == "verified_access":
            if modality not in capabilities:
                raise ReviewProtocolError(
                    f"Reviewer lacks declared {modality} capability for verified learner evidence {evidence_id}"
                )
            if finding_id is not None:
                raise ReviewProtocolError(f"Verified learner evidence {evidence_id} cannot reference a finding")
        else:
            finding_id = _nonempty_string(finding_id, f"finding_id for learner evidence {evidence_id}")
            if finding_id not in finding_ids:
                raise ReviewProtocolError(
                    f"Learner evidence {evidence_id} references unknown finding {finding_id}"
                )
            if (
                access_status in {"metadata_only", "inaccessible", "not_provided"}
                and finding_severities[finding_id] not in {"blocker", "high"}
            ):
                raise ReviewProtocolError(
                    f"Learner evidence {evidence_id} with {access_status} requires a high or blocker finding"
                )
        evidence_ledger.append(
            {
                "id": evidence_id,
                "location": _nonempty_string(raw["location"], f"learner evidence location for {evidence_id}"),
                "task": _nonempty_string(raw["task"], f"learner evidence task for {evidence_id}"),
                "modality": modality,
                "source": _nonempty_string(raw["source"], f"learner evidence source for {evidence_id}"),
                "access_status": access_status,
                "verification_method": _nonempty_string(
                    raw["verification_method"], f"verification method for {evidence_id}"
                ),
                "finding_id": finding_id,
            }
        )
    required_modalities = {str(item.get("modality")) for item in evidence_requirements}
    covered_modalities = {item["modality"] for item in evidence_ledger}
    missing_modalities = sorted(required_modalities - covered_modalities)
    if missing_modalities:
        raise ReviewProtocolError(
            "learner_evidence_ledger does not cover detected modalities: " + ", ".join(missing_modalities)
        )
    if verdict == "PASS" and any(claim["status"] != "supported" for claim in claims):
        raise ReviewProtocolError("Semantic PASS is inconsistent with a non-supported claim ledger entry")

    return {
        "family": family,
        "verdict": verdict,
        "summary": summary,
        "quality_dimensions": dimensions,
        "claim_coverage": {
            "status": status,
            "claims_total": claims_total,
            "claims_checked": claims_checked,
            "claims_supported": claims_supported,
        },
        "claim_ledger": claims,
        "learner_evidence_ledger": evidence_ledger,
        "findings": findings,
    }


def _incomplete_semantic(family: str, error: str) -> dict[str, Any]:
    finding = {
        "id": "semantic-response-integrity",
        "issue_id": "SEMANTIC_RESPONSE_INTEGRITY",
        "source": "semantic",
        "category": "semantic_response_integrity",
        "severity": "high",
        "message": "The reviewer response could not be accepted without repair or normalization.",
        "evidence": error,
        "location": None,
    }
    return {
        "family": family,
        "verdict": "INCOMPLETE",
        "summary": "Semantic review output was malformed or violated the response contract.",
        "quality_dimensions": {
            dimension: {
                "status": "INCOMPLETE",
                "evidence": [],
                "finding_ids": ["semantic-response-integrity"],
            }
            for dimension in QUALITY_DIMENSIONS
        },
        "claim_coverage": {
            "status": "incomplete",
            "claims_total": 0,
            "claims_checked": 0,
            "claims_supported": 0,
        },
        "claim_ledger": [],
        "learner_evidence_ledger": [],
        "findings": [finding],
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
    if coverage["status"] == "incomplete" or coverage["claims_checked"] < coverage["claims_total"]:
        reasons.append("semantic claim coverage is incomplete")
    if any(
        item.get("access_status") == "reviewer_unverified"
        for item in semantic.get("learner_evidence_ledger") or []
    ):
        reasons.append("reviewer could not verify required learner evidence")
    if semantic["verdict"] == "INCOMPLETE":
        reasons.append("semantic reviewer reported incomplete")
    incomplete_dimensions = sorted(
        dimension
        for dimension, assessment in semantic.get("quality_dimensions", {}).items()
        if assessment.get("status") == "INCOMPLETE"
    )
    if incomplete_dimensions:
        reasons.append("quality dimension coverage is incomplete: " + ", ".join(incomplete_dimensions))
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


def _validate_normalized_quality_dimensions(semantic: Mapping[str, Any]) -> None:
    dimensions = semantic["quality_dimensions"]
    finding_severities = {
        str(finding["id"]): str(finding["severity"])
        for finding in semantic["findings"]
    }
    nonpassing: dict[str, str] = {}
    for dimension in QUALITY_DIMENSIONS:
        assessment = dimensions[dimension]
        status = str(assessment["status"])
        evidence = assessment["evidence"]
        finding_ids = [str(finding_id) for finding_id in assessment["finding_ids"]]
        if status != "INCOMPLETE" and not evidence:
            raise ReviewProtocolError(
                f"Quality dimension {dimension} requires cited evidence"
            )
        unknown = sorted(set(finding_ids) - set(finding_severities))
        if unknown:
            raise ReviewProtocolError(
                f"Quality dimension {dimension} references unknown findings: "
                + ", ".join(unknown)
            )
        severities = {finding_severities[finding_id] for finding_id in finding_ids}
        if status == "PASS" and severities.intersection({"blocker", "high", "medium"}):
            raise ReviewProtocolError(
                f"Quality dimension {dimension} PASS references a material finding"
            )
        if status == "REVISE" and not severities.intersection({"high", "medium"}):
            raise ReviewProtocolError(
                f"Quality dimension {dimension} REVISE requires a high or medium finding"
            )
        if status == "BLOCK" and "blocker" not in severities:
            raise ReviewProtocolError(
                f"Quality dimension {dimension} BLOCK requires a blocker finding"
            )
        if status == "INCOMPLETE" and not finding_ids:
            raise ReviewProtocolError(
                f"Quality dimension {dimension} INCOMPLETE requires a finding"
            )
        if status != "PASS":
            nonpassing[dimension] = status

    verdict = str(semantic["verdict"])
    if verdict == "PASS" and nonpassing:
        raise ReviewProtocolError(
            "Semantic PASS requires PASS for every quality dimension: "
            + ", ".join(sorted(nonpassing))
        )
    if "INCOMPLETE" in nonpassing.values() and verdict != "INCOMPLETE":
        raise ReviewProtocolError("An incomplete quality dimension requires semantic INCOMPLETE")
    if "BLOCK" in nonpassing.values() and verdict not in {"BLOCK", "INCOMPLETE"}:
        raise ReviewProtocolError("A blocked quality dimension requires semantic BLOCK or INCOMPLETE")


def validate_result(
    result: Mapping[str, Any], *, schema_path: Path | None = None, repo_root: Path = PROJECT_ROOT
) -> None:
    if schema_path is None:
        schema_version = str(result.get("schema_version") or "")
        relative = SCHEMA_PATHS.get(schema_version)
        if relative is None:
            raise ReviewProtocolError(f"Unknown result schema version: {schema_version!r}")
        schema_path = repo_root / relative.relative_to(PROJECT_ROOT)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(result)
    if result.get("schema_version") != CURRENT_RESULT_SCHEMA_VERSION:
        return
    _validate_normalized_quality_dimensions(result["semantic"])
    expected_findings = [
        *_deterministic_findings(result),
        *deepcopy(result["semantic"]["findings"]),
    ]
    if result["findings"] != expected_findings:
        raise ReviewProtocolError("Result findings do not match deterministic plus semantic evidence")
    expected_disposition = combine_disposition(
        result["deterministic"], result["semantic"], expected_findings
    )
    if result["combined_disposition"] != expected_disposition:
        raise ReviewProtocolError("Combined disposition does not match canonical precedence")
    reproducible = {key: deepcopy(result[key]) for key in REPRODUCIBILITY_FIELDS}
    expected_key = sha256_text(_stable_json(reproducible))
    if result["reproducibility_key"] != expected_key:
        raise ReviewProtocolError("Result reproducibility key does not match canonical evidence")


def finalize_review(
    packet: Mapping[str, Any],
    semantic_response: bytes,
    *,
    repo_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    family = str(packet["target"]["semantic_family"])
    semantic_input, response_provenance = parse_semantic_response(semantic_response)
    if semantic_input is None:
        error = str(response_provenance["error"] or "invalid semantic response")
        semantic = _incomplete_semantic(family, error)
        response_provenance["contract_status"] = "not_evaluated"
    else:
        try:
            semantic = normalize_semantic_result(
                semantic_input,
                family,
                packet["reviewer"],
                packet["deterministic"].get("evidence_requirements") or [],
                {
                    str(path): resolve_repo_path(str(path), repo_root=repo_root).read_text(
                        encoding="utf-8"
                    )
                    for path in packet["target"]["files"].values()
                },
            )
        except ReviewProtocolError as exc:
            error = str(exc)
            semantic = _incomplete_semantic(family, error)
            response_provenance["contract_status"] = "invalid"
            response_provenance["error"] = error
        else:
            response_provenance["contract_status"] = "valid"
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
        "schema_version": CURRENT_RESULT_SCHEMA_VERSION,
        "review_protocol_version": str(packet["review_protocol_version"]),
        "deterministic_contract_version": str(packet["deterministic_contract_version"]),
        "semantic_prompt_version": str(packet["semantic_prompt_version"]),
        "track_policy_version": str(packet["track_policy_version"]),
        "prompt_sha256": str(packet["prompt_sha256"]),
        "target": deepcopy(packet["target"]),
        "source_hashes": deepcopy(packet["source_hashes"]),
        "reviewer": deepcopy(packet["reviewer"]),
        "semantic_response": response_provenance,
        "deterministic": deterministic,
        "semantic": semantic,
        "findings": findings,
        "combined_disposition": disposition,
    }
    reproducible = {key: deepcopy(result[key]) for key in REPRODUCIBILITY_FIELDS}
    result["reproducibility_key"] = sha256_text(_stable_json(reproducible))
    validate_result(result, repo_root=repo_root)
    return result


def ensure_output_outside_repo(path: Path, *, repo_root: Path = PROJECT_ROOT) -> None:
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return
    raise ReviewProtocolError("Review outputs must be written outside the repository")


def allocate_run_paths(
    target_value: str,
    *,
    temp_root: Path | None = None,
    repo_root: Path = PROJECT_ROOT,
) -> dict[str, str]:
    """Reserve one invocation-scoped directory for every review artifact."""
    target = resolve_target(target_value, repo_root=repo_root)
    root = (temp_root or Path(tempfile.gettempdir())).resolve()
    ensure_output_outside_repo(root / "post-build-review-placeholder", repo_root=repo_root)
    root.mkdir(parents=True, exist_ok=True)
    prefix = f"post-build-review-{target['track']}-{target['slug']}-"
    run_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=root)).resolve()
    return {
        "run_dir": str(run_dir),
        "packet": str(run_dir / "packet.json"),
        "semantic_response": str(run_dir / "semantic-response.json"),
        "result": str(run_dir / "result.json"),
    }


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
    allocate = subparsers.add_parser(
        "allocate",
        help="Reserve invocation-scoped paths for packet, semantic response, and result.",
    )
    allocate.add_argument("target", help="track/slug, e.g. bio/oleksandr-bilash")
    allocate.add_argument("--temp-root", type=Path)

    prepare = subparsers.add_parser("prepare", help="Run deterministic stages and assemble the semantic prompt.")
    prepare.add_argument("target", help="track/slug, e.g. bio/oleksandr-bilash")
    prepare.add_argument("--reviewer-agent", required=True)
    prepare.add_argument("--reviewer-family", required=True)
    prepare.add_argument("--reviewer-model", required=True)
    prepare.add_argument("--reviewer-effort", required=True)
    prepare.add_argument(
        "--reviewer-capability",
        action="append",
        required=True,
        choices=("text", "audio", "video", "image", "interactive"),
        help="Repeat for every evidence modality the reviewer can directly inspect.",
    )
    prepare.add_argument("--output", type=Path)

    finalize = subparsers.add_parser("finalize", help="Combine an exact raw semantic response with a prepared packet.")
    finalize.add_argument("--packet", type=Path, required=True)
    finalize.add_argument("--semantic-response", type=Path, required=True)
    finalize.add_argument("--output", type=Path)

    validate = subparsers.add_parser("validate", help="Validate an existing canonical result.")
    validate.add_argument("result", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "allocate":
        _write_or_print(
            allocate_run_paths(args.target, temp_root=args.temp_root),
            None,
            repo_root=PROJECT_ROOT,
        )
        return 0
    if args.command == "prepare":
        reviewer = {
            "agent": args.reviewer_agent,
            "family": args.reviewer_family,
            "model": args.reviewer_model,
            "effort": args.reviewer_effort,
            "capabilities": sorted(set(args.reviewer_capability)),
        }
        packet = prepare_review(args.target, reviewer)
        _write_or_print(packet, args.output, repo_root=PROJECT_ROOT)
        return 0
    if args.command == "finalize":
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
        result = finalize_review(packet, args.semantic_response.read_bytes())
        _write_or_print(result, args.output, repo_root=PROJECT_ROOT)
        return 0 if result["combined_disposition"]["status"] == "PASS" else 1
    result = json.loads(args.result.read_text(encoding="utf-8"))
    validate_result(result)
    print("post-build-review result is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
