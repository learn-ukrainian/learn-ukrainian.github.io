#!/usr/bin/env python3
"""Profile-driven, hash-bound PREPARE contract for curriculum modules."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import lint_bio_dossier_xref
from scripts.audit.wiki_completeness_gate import check_wiki_completeness
from scripts.build import linear_pipeline
from scripts.orchestration import prompt_contracts
from scripts.orchestration.preparation_evidence import (
    RegistryValidationError,
    load_manual_evidence,
    load_yaml_mapping,
)
from scripts.validate import check_discovery_integrity, check_wiki_subject, lint_seminar_quality
from scripts.wiki.domains import resolve_write_domain

CONFIG_PATH = Path("agents_extensions/shared/curriculum-lifecycle/config/readiness-profiles.v1.yaml")
CONFIG_SCHEMA_PATH = Path(
    "agents_extensions/shared/curriculum-lifecycle/schema/readiness-profiles.v1.schema.json"
)
RESULT_SCHEMA_PATH = Path(
    "agents_extensions/shared/curriculum-lifecycle/schema/preparation-result.v1.schema.json"
)
MANIFEST_PATH = Path("curriculum/l2-uk-en/curriculum.yaml")
MODULE_BUNDLE_FILES = ("module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml")
DEPENDENT_EVIDENCE_CLASSES = frozenset({"build", "post-build", "production-qg"})
_TARGET_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class ReadinessError(ValueError):
    """Raised when a preparation contract cannot be evaluated safely."""


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    detail: str


@dataclass(frozen=True)
class ContractFiles:
    manifest: Path
    readiness_config: Path
    readiness_config_schema: Path
    preparation_result_schema: Path
    prompt_profiles: Path
    prompt_profile_schema: Path


@dataclass(frozen=True)
class LifecycleDecision:
    preparation_state: str
    state: str
    next_action: str


@dataclass
class ValidationContext:
    repo_root: Path
    track: str
    slug: str
    manifest_slugs: tuple[str, ...]
    cache: dict[str, Any] = field(default_factory=dict)

    def plan(self) -> Mapping[str, Any] | None:
        if "plan" not in self.cache:
            path = artifact_path("plan", self.repo_root, self.track, self.slug)
            try:
                self.cache["plan"] = load_yaml_mapping(path) if path.is_file() else None
            except RegistryValidationError:
                self.cache["plan"] = None
        value = self.cache["plan"]
        return value if isinstance(value, Mapping) else None

    def manual_evidence(self, path: Path) -> Mapping[str, Mapping[str, Any]]:
        key = f"manual:{path}"
        if key not in self.cache:
            self.cache[key] = load_manual_evidence(path, set(self.manifest_slugs))
        value = self.cache[key]
        return value if isinstance(value, Mapping) else {}


Validator = Callable[[Path, Mapping[str, Any], ValidationContext], ValidationResult]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _repo_file(repo_root: Path, relative: str | Path) -> Path:
    raw = str(relative)
    path = Path(raw)
    if not raw or "\\" in raw or path.is_absolute() or ".." in path.parts or raw.startswith("~"):
        raise ReadinessError(f"path must be a safe repository-relative path: {raw!r}")
    root = repo_root.resolve()
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ReadinessError(f"path escapes repository root: {raw!r}") from exc
    if not candidate.is_file():
        raise ReadinessError(f"required preparation contract file is missing: {raw}")
    return candidate


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ReadinessError(f"preparation evidence path escapes repository root: {path}") from exc


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReadinessError(f"invalid JSON contract {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReadinessError(f"JSON contract must be an object: {path}")
    return value


def _validate(document: Mapping[str, Any], schema: Mapping[str, Any], label: str) -> None:
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # jsonschema exposes multiple schema exception subclasses
        raise ReadinessError(f"invalid JSON schema for {label}: {exc}") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise ReadinessError(f"{label} failed schema validation at {location}: {error.message}")


def _source(role: str, path: Path, repo_root: Path) -> dict[str, Any]:
    exists = path.is_file()
    return {
        "role": role,
        "path": _relative(path, repo_root),
        "sha256": _sha256_bytes(path.read_bytes()) if exists else None,
        "exists": exists,
    }


def artifact_path(artifact: str, repo_root: Path, track: str, slug: str) -> Path:
    """Resolve a registered artifact ID without track-name branches."""
    curriculum = repo_root / "curriculum" / "l2-uk-en"
    resolvers: dict[str, Callable[[], Path]] = {
        "dossier": lambda: repo_root / "docs" / "research" / track / f"{slug}.md",
        "plan": lambda: curriculum / "plans" / track / f"{slug}.yaml",
        "manual-registry": lambda: curriculum / track / "promotion-evidence.yaml",
        "wiki-document": lambda: repo_root / "wiki" / resolve_write_domain(track, slug) / f"{slug}.md",
        "wiki-sources": lambda: repo_root
        / "wiki"
        / resolve_write_domain(track, slug)
        / f"{slug}.sources.yaml",
        "discovery": lambda: curriculum / track / "discovery" / f"{slug}.yaml",
    }
    resolver = resolvers.get(artifact)
    if resolver is None:
        raise ReadinessError(f"unregistered preparation artifact: {artifact}")
    path = resolver().resolve()
    _relative(path, repo_root)
    return path


def _exists(path: Path, _option: Mapping[str, Any], _context: ValidationContext) -> ValidationResult:
    return ValidationResult(path.is_file(), "file exists" if path.is_file() else "file is missing")


def _yaml_mapping(path: Path, _option: Mapping[str, Any], _context: ValidationContext) -> ValidationResult:
    try:
        load_yaml_mapping(path)
    except RegistryValidationError as exc:
        return ValidationResult(False, str(exc))
    return ValidationResult(True, "strict YAML mapping")


def _plan_check(path: Path, _option: Mapping[str, Any], _context: ValidationContext) -> ValidationResult:
    try:
        linear_pipeline.plan_check(path)
    except Exception as exc:  # authoritative plan validator has several error types
        return ValidationResult(False, f"{type(exc).__name__}: {exc}")
    return ValidationResult(True, "authoritative plan check passed")


def _seminar_plan_language(
    path: Path,
    _option: Mapping[str, Any],
    _context: ValidationContext,
) -> ValidationResult:
    findings = [finding for finding in lint_seminar_quality.lint_plan(path) if finding.severity == "high"]
    return ValidationResult(not findings, f"{len(findings)} high seminar-language finding(s)")


def _readings_present(path: Path, _option: Mapping[str, Any], _context: ValidationContext) -> ValidationResult:
    try:
        plan = load_yaml_mapping(path)
    except RegistryValidationError as exc:
        return ValidationResult(False, str(exc))
    readings = plan.get("readings")
    passed = isinstance(readings, list) and bool(readings)
    return ValidationResult(passed, "plan reading packet is present" if passed else "plan has no reading packet")


def _bio_dossier_xref(
    path: Path,
    _option: Mapping[str, Any],
    _context: ValidationContext,
) -> ValidationResult:
    findings = lint_bio_dossier_xref.lint_dossier(path)
    return ValidationResult(not findings, f"{len(findings)} dossier cross-reference finding(s)")


def _manual_gate(path: Path, option: Mapping[str, Any], context: ValidationContext) -> ValidationResult:
    gate = str(option["manual_gate"])
    try:
        record = context.manual_evidence(path).get(context.slug, {}).get(gate)
    except RegistryValidationError as exc:
        return ValidationResult(False, str(exc))
    passed = isinstance(record, Mapping) and record.get("status") == "pass"
    return ValidationResult(passed, f"manual gate {gate}: {'pass' if passed else 'missing-or-fail'}")


def _wiki_completeness(
    path: Path,
    _option: Mapping[str, Any],
    context: ValidationContext,
) -> ValidationResult:
    report = check_wiki_completeness(path, level=context.track, slug=context.slug)
    return ValidationResult(report["verdict"] == "PASS", str(report["diagnostic"]))


def _bio_wiki_subject(
    path: Path,
    _option: Mapping[str, Any],
    context: ValidationContext,
) -> ValidationResult:
    plan = context.plan()
    if plan is None:
        return ValidationResult(False, "plan title unavailable for wiki subject check")
    finding = check_wiki_subject.check_wiki_file(path, plan_title=str(plan.get("title", "")))
    return ValidationResult(finding is None, "wiki subject matches plan" if finding is None else str(finding))


def _seminar_wiki_language(
    path: Path,
    _option: Mapping[str, Any],
    _context: ValidationContext,
) -> ValidationResult:
    findings = [finding for finding in lint_seminar_quality.lint_text(path) if finding.severity == "high"]
    return ValidationResult(not findings, f"{len(findings)} high seminar-language finding(s)")


def _bio_discovery_integrity(
    path: Path,
    _option: Mapping[str, Any],
    context: ValidationContext,
) -> ValidationResult:
    plan = context.plan()
    if plan is None:
        return ValidationResult(False, "plan title unavailable for discovery integrity check")
    finding = check_discovery_integrity.check_discovery_file(path, plan_title=str(plan.get("title", "")))
    return ValidationResult(finding is None, "discovery subject matches plan" if finding is None else str(finding))


VALIDATORS: dict[str, Validator] = {
    "exists": _exists,
    "yaml-mapping": _yaml_mapping,
    "plan-check": _plan_check,
    "seminar-plan-language": _seminar_plan_language,
    "readings-present": _readings_present,
    "bio-dossier-xref": _bio_dossier_xref,
    "manual-gate": _manual_gate,
    "wiki-completeness": _wiki_completeness,
    "bio-wiki-subject": _bio_wiki_subject,
    "seminar-wiki-language": _seminar_wiki_language,
    "bio-discovery-integrity": _bio_discovery_integrity,
}


def load_config(*, repo_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    config_path = _repo_file(repo_root, CONFIG_PATH)
    schema = _load_json(_repo_file(repo_root, CONFIG_SCHEMA_PATH))
    try:
        config = load_yaml_mapping(config_path)
    except RegistryValidationError as exc:
        raise ReadinessError(str(exc)) from exc
    _validate(config, schema, "readiness profiles")
    profiles = config["profiles"]
    try:
        registered_prompt_profiles = prompt_contracts.load_profiles(repo_root=repo_root)["profiles"]
    except prompt_contracts.PromptContractError as exc:
        raise ReadinessError(f"invalid registered prompt profiles: {exc}") from exc
    for selector_group in config["selectors"].values():
        for profile_id in selector_group.values():
            if profile_id not in profiles:
                raise ReadinessError(f"readiness selector references unknown profile: {profile_id}")
    for profile_id, profile in profiles.items():
        if profile["prompt_profile"] not in registered_prompt_profiles:
            raise ReadinessError(
                f"readiness profile {profile_id} selects unknown prompt profile: {profile['prompt_profile']}"
            )
        ids = [requirement["id"] for requirement in profile["requirements"]]
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            raise ReadinessError(f"readiness profile {profile_id} has duplicate requirements: {duplicates}")
        for requirement in profile["requirements"]:
            for option in requirement["options"]:
                unknown = sorted(set(option["validators"]) - set(VALIDATORS))
                if unknown:
                    raise ReadinessError(f"readiness profile {profile_id} uses unknown validators: {unknown}")
        qg = profile["certification"]["production_qg"]
        if qg["mode"] == "armed-canary":
            for key in ("qualification_artifact", "human_arming_artifact"):
                _repo_file(repo_root, qg[key])
    return config


def load_manifest_track(
    repo_root: Path,
    track: str,
    manifest_path: Path = MANIFEST_PATH,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Load one active manifest track and its authoritative module order."""
    manifest_path = _repo_file(repo_root, manifest_path)
    try:
        manifest = load_yaml_mapping(manifest_path)
    except RegistryValidationError as exc:
        raise ReadinessError(str(exc)) from exc
    levels = manifest.get("levels")
    level = levels.get(track) if isinstance(levels, Mapping) else None
    if not isinstance(level, Mapping):
        raise ReadinessError(f"curriculum manifest has no active track: {track}")
    modules = level.get("modules")
    if not isinstance(modules, list) or not all(isinstance(item, str) and item for item in modules):
        raise ReadinessError(f"manifest levels.{track}.modules must be a list of non-empty slugs")
    duplicates = sorted({item for item in modules if modules.count(item) > 1})
    if duplicates:
        raise ReadinessError(f"manifest levels.{track}.modules contains duplicate slugs: {duplicates}")
    manifest_type = level.get("type")
    if not isinstance(manifest_type, str) or not manifest_type:
        raise ReadinessError(f"manifest levels.{track}.type must be a non-empty string")
    return {
        "type": manifest_type,
        "path": manifest_path,
        "sha256": _sha256_bytes(manifest_path.read_bytes()),
    }, tuple(modules)


def _select_profile(config: Mapping[str, Any], track: str, manifest_type: str) -> tuple[str, Mapping[str, Any]]:
    selectors = config["selectors"]
    profile_id = selectors["tracks"].get(track) or selectors["manifest_types"].get(manifest_type)
    if not isinstance(profile_id, str):
        raise ReadinessError(f"no readiness profile for track={track} manifest_type={manifest_type}")
    profile = config["profiles"].get(profile_id)
    if not isinstance(profile, Mapping):
        raise ReadinessError(f"selected readiness profile is missing: {profile_id}")
    return profile_id, profile


def module_bundle_state(repo_root: Path, track: str, slug: str) -> str:
    """Classify the canonical four-file learner bundle without reading audit state."""
    module_dir = repo_root / "curriculum" / "l2-uk-en" / track / slug
    count = sum((module_dir / filename).is_file() for filename in MODULE_BUNDLE_FILES)
    if count == 0:
        return "unbuilt"
    if count == len(MODULE_BUNDLE_FILES):
        return "built"
    return "partial"


def _run_validator(
    validator_id: str,
    path: Path,
    option: Mapping[str, Any],
    context: ValidationContext,
    validators: Mapping[str, Validator],
) -> ValidationResult:
    validator = validators.get(validator_id)
    if validator is None:
        raise ReadinessError(f"validator implementation is unavailable: {validator_id}")
    try:
        return validator(path, option, context)
    except Exception as exc:  # external validators fail closed at the adapter boundary
        return ValidationResult(False, f"{type(exc).__name__}: {exc}")


def _evaluate_requirements(
    profile: Mapping[str, Any],
    context: ValidationContext,
    validators: Mapping[str, Validator],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    requirements: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    sources: dict[str, dict[str, Any]] = {}
    for requirement in profile["requirements"]:
        options: list[dict[str, Any]] = []
        for option in requirement["options"]:
            path = artifact_path(str(option["artifact"]), context.repo_root, context.track, context.slug)
            source = _source(f"artifact:{option['artifact']}", path, context.repo_root)
            sources.setdefault(source["path"], source)
            results: list[dict[str, Any]] = []
            for validator_id in option["validators"]:
                result = _run_validator(str(validator_id), path, option, context, validators)
                results.append({"id": str(validator_id), "passed": result.passed, "detail": result.detail})
                if not result.passed:
                    break
            options.append(
                {
                    "artifact": str(option["artifact"]),
                    "path": source["path"],
                    "sha256": source["sha256"],
                    "passed": bool(results) and all(result["passed"] for result in results),
                    "validators": results,
                }
            )
        passed = any(option["passed"] for option in options)
        record = {
            "id": str(requirement["id"]),
            "owner": str(requirement["owner"]),
            "passed": passed,
            "options": options,
        }
        requirements.append(record)
        if not passed:
            findings.append(
                {
                    "id": f"PREPARATION_{str(requirement['id']).upper().replace('-', '_')}",
                    "category": "plan" if requirement["owner"] == "plan" else "preparation",
                    "severity": "high",
                    "summary": f"Required evidence did not pass: {requirement['id']}",
                    "owner": str(requirement["owner"]),
                }
            )
    return requirements, findings, list(sources.values())


def _identity_requirements(requirements: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Remove diagnostic prose so identities remain repository-root independent."""
    return [
        {
            "id": requirement["id"],
            "owner": requirement["owner"],
            "passed": requirement["passed"],
            "options": [
                {
                    "artifact": option["artifact"],
                    "path": option["path"],
                    "sha256": option["sha256"],
                    "passed": option["passed"],
                    "validators": [
                        {"id": result["id"], "passed": result["passed"]}
                        for result in option["validators"]
                    ],
                }
                for option in requirement["options"]
            ],
        }
        for requirement in requirements
    ]


def _contract_files(repo_root: Path, manifest_path: Path) -> ContractFiles:
    return ContractFiles(
        manifest=manifest_path,
        readiness_config=_repo_file(repo_root, CONFIG_PATH),
        readiness_config_schema=_repo_file(repo_root, CONFIG_SCHEMA_PATH),
        preparation_result_schema=_repo_file(repo_root, RESULT_SCHEMA_PATH),
        prompt_profiles=_repo_file(repo_root, prompt_contracts.PROFILE_PATH),
        prompt_profile_schema=_repo_file(repo_root, prompt_contracts.PROFILE_SCHEMA_PATH),
    )


def _contract_sources(files: ContractFiles, repo_root: Path) -> list[dict[str, Any]]:
    return [
        _source("manifest", files.manifest, repo_root),
        _source("readiness-config", files.readiness_config, repo_root),
        _source("readiness-config-schema", files.readiness_config_schema, repo_root),
        _source("preparation-result-schema", files.preparation_result_schema, repo_root),
        _source("prompt-profiles", files.prompt_profiles, repo_root),
        _source("prompt-profile-schema", files.prompt_profile_schema, repo_root),
    ]


def _manifest_evidence(
    files: ContractFiles,
    sources: Sequence[Mapping[str, Any]],
    repo_root: Path,
    index: int | None,
) -> dict[str, Any]:
    return {"path": _relative(files.manifest, repo_root), "sha256": sources[0]["sha256"], "index": index}


def _result_document(
    *,
    track: str,
    slug: str,
    profile_id: str,
    profile: Mapping[str, Any],
    manifest: Mapping[str, Any],
    module_state: str,
    decision: LifecycleDecision,
    requirements: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    preparation_identity: str | None,
    consumed_preparation_identity: str | None,
) -> dict[str, Any]:
    return {
        "contract_version": "curriculum-preparation-result.v1",
        "track": track,
        "slug": slug,
        "profile_id": profile_id,
        "profile_version": str(profile["version"]),
        "family": str(profile["family"]),
        "manifest": dict(manifest),
        "module_state": module_state,
        "preparation_state": decision.preparation_state,
        "state": decision.state,
        "next_action": decision.next_action,
        "requirements": requirements,
        "findings": findings,
        "sources": sources,
        "preparation_identity": preparation_identity,
        "consumed_preparation_identity": consumed_preparation_identity,
    }


def _off_manifest_result(
    *,
    repo_root: Path,
    track: str,
    slug: str,
    profile_id: str,
    profile: Mapping[str, Any],
    files: ContractFiles,
) -> dict[str, Any]:
    sources = _contract_sources(files, repo_root)
    return _result_document(
        track=track,
        slug=slug,
        profile_id=profile_id,
        profile=profile,
        manifest=_manifest_evidence(files, sources, repo_root, None),
        module_state="off-manifest",
        decision=LifecycleDecision("not-applicable", "off-manifest", "stop"),
        requirements=[],
        findings=[
            {
                "id": "OFF_MANIFEST_TARGET",
                "category": "authority",
                "severity": "blocker",
                "summary": "Target is not an active curriculum manifest member",
                "owner": "authority",
            }
        ],
        sources=sources,
        preparation_identity=None,
        consumed_preparation_identity=None,
    )


def _preparation_identity(
    *,
    track: str,
    slug: str,
    profile_id: str,
    profile: Mapping[str, Any],
    manifest_index: int,
    requirements: Sequence[Mapping[str, Any]],
    sources: Sequence[Mapping[str, Any]],
) -> str:
    payload = {
        "contract_version": "curriculum-preparation-result.v1",
        "track": track,
        "slug": slug,
        "profile_id": profile_id,
        "profile": profile,
        "manifest_index": manifest_index,
        "requirements": _identity_requirements(requirements),
        "sources": sources,
    }
    return _sha256_bytes(_canonical_json(payload).encode("utf-8"))


def _plan_is_missing(requirements: Sequence[Mapping[str, Any]]) -> bool:
    return any(
        requirement["id"] == "plan"
        and not requirement["passed"]
        and any(option["artifact"] == "plan" and option["sha256"] is None for option in requirement["options"])
        for requirement in requirements
    )


def _built_decision(
    requirements_pass: bool,
    preparation_identity: str,
    consumed_preparation_identity: str | None,
) -> tuple[LifecycleDecision, list[dict[str, Any]]]:
    if requirements_pass and consumed_preparation_identity == preparation_identity:
        return LifecycleDecision("current", "built-current", "certify"), []
    findings: list[dict[str, Any]] = []
    if consumed_preparation_identity is None:
        findings.append(
            {
                "id": "PREPARATION_IDENTITY_MISSING",
                "category": "audit_tooling",
                "severity": "high",
                "summary": "Built bundle does not record the preparation identity it consumed",
                "owner": "audit_tooling",
            }
        )
    elif consumed_preparation_identity != preparation_identity:
        findings.append(
            {
            "id": "PREPARATION_IDENTITY_DRIFT",
            "category": "preparation",
            "severity": "high",
            "summary": "Current preparation identity differs from the identity consumed by the build",
            "owner": "preparation",
            }
        )
    return LifecycleDecision("stale", "built-preparation-drift", "prepare"), findings


def _lifecycle_decision(
    *,
    module_state: str,
    requirements_pass: bool,
    plan_missing: bool,
    plan_owner_only: bool,
    preparation_identity: str,
    consumed_preparation_identity: str | None,
) -> tuple[LifecycleDecision, list[dict[str, Any]]]:
    if module_state == "partial":
        finding = {
            "id": "PARTIAL_LEARNER_BUNDLE",
            "category": "built_artifact",
            "severity": "blocker",
            "summary": "Learner bundle is partial and requires non-destructive recovery",
            "owner": "built_artifact",
        }
        preparation_state = "current" if requirements_pass else "missing"
        return LifecycleDecision(preparation_state, "partial-bundle", "stop"), [finding]
    if module_state == "built":
        return _built_decision(requirements_pass, preparation_identity, consumed_preparation_identity)
    if requirements_pass:
        return LifecycleDecision("current", "prepared-plan", "build"), []
    if plan_missing:
        return LifecycleDecision("missing", "missing-plan", "plan"), []
    next_action = "plan" if plan_owner_only else "prepare"
    return LifecycleDecision("missing", "preparation-required", next_action), []


def _evaluate_manifest_target(
    *,
    repo_root: Path,
    track: str,
    slug: str,
    profile_id: str,
    profile: Mapping[str, Any],
    manifest_slugs: tuple[str, ...],
    files: ContractFiles,
    validators: Mapping[str, Validator],
    consumed_preparation_identity: str | None,
) -> dict[str, Any]:
    context = ValidationContext(repo_root, track, slug, manifest_slugs)
    requirements, findings, artifact_sources = _evaluate_requirements(profile, context, validators)
    sources = [*_contract_sources(files, repo_root), *artifact_sources]
    manifest_index = manifest_slugs.index(slug)
    preparation_identity = _preparation_identity(
        track=track,
        slug=slug,
        profile_id=profile_id,
        profile=profile,
        manifest_index=manifest_index,
        requirements=requirements,
        sources=sources,
    )
    module_state = module_bundle_state(repo_root, track, slug)
    decision, state_findings = _lifecycle_decision(
        module_state=module_state,
        requirements_pass=all(requirement["passed"] for requirement in requirements),
        plan_missing=_plan_is_missing(requirements),
        plan_owner_only=bool(findings) and all(item["owner"] == "plan" for item in findings),
        preparation_identity=preparation_identity,
        consumed_preparation_identity=consumed_preparation_identity,
    )
    result = _result_document(
        track=track,
        slug=slug,
        profile_id=profile_id,
        profile=profile,
        manifest=_manifest_evidence(files, sources, repo_root, manifest_index),
        module_state=module_state,
        decision=decision,
        requirements=requirements,
        findings=[*findings, *state_findings],
        sources=sources,
        preparation_identity=preparation_identity,
        consumed_preparation_identity=consumed_preparation_identity,
    )
    validate_result(result, repo_root=repo_root)
    return result


def evaluate_preparation(
    track: str,
    slug: str,
    *,
    consumed_preparation_identity: str | None = None,
    repo_root: Path = PROJECT_ROOT,
    validators: Mapping[str, Validator] = VALIDATORS,
) -> dict[str, Any]:
    """Evaluate one manifest target without reading legacy QG state."""
    track = track.lower()
    slug = slug.lower()
    if not _TARGET_RE.fullmatch(track) or not _TARGET_RE.fullmatch(slug):
        raise ReadinessError("track and slug must be lowercase repository identifiers")
    if consumed_preparation_identity is not None and not _HASH_RE.fullmatch(consumed_preparation_identity):
        raise ReadinessError("consumed preparation identity must be a SHA-256 hex digest")

    config = load_config(repo_root=repo_root)
    manifest_record, manifest_slugs = load_manifest_track(repo_root, track)
    profile_id, profile = _select_profile(config, track, str(manifest_record["type"]))
    files = _contract_files(repo_root, manifest_record["path"])

    if slug not in manifest_slugs:
        result = _off_manifest_result(
            repo_root=repo_root,
            track=track,
            slug=slug,
            profile_id=profile_id,
            profile=profile,
            files=files,
        )
        validate_result(result, repo_root=repo_root)
        return result
    return _evaluate_manifest_target(
        repo_root=repo_root,
        track=track,
        slug=slug,
        profile_id=profile_id,
        profile=profile,
        manifest_slugs=manifest_slugs,
        files=files,
        validators=validators,
        consumed_preparation_identity=consumed_preparation_identity,
    )


def validate_result(result: Mapping[str, Any], *, repo_root: Path = PROJECT_ROOT) -> None:
    schema = _load_json(_repo_file(repo_root, RESULT_SCHEMA_PATH))
    _validate(result, schema, "preparation result")


def dependent_evidence_identity(
    evidence_class: str,
    preparation_identity: str,
    dependencies: Mapping[str, str],
) -> str:
    """Bind build, PBR, or production-QG evidence to preparation identity."""
    if evidence_class not in DEPENDENT_EVIDENCE_CLASSES:
        raise ReadinessError(f"unsupported dependent evidence class: {evidence_class}")
    if not _HASH_RE.fullmatch(preparation_identity):
        raise ReadinessError("preparation identity must be a SHA-256 hex digest")
    if not all(isinstance(key, str) and key and isinstance(value, str) and value for key, value in dependencies.items()):
        raise ReadinessError("dependent evidence identities require non-empty string keys and values")
    payload = {
        "evidence_class": evidence_class,
        "preparation_identity": preparation_identity,
        "dependencies": dict(sorted(dependencies.items())),
    }
    return _sha256_bytes(_canonical_json(payload).encode("utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--consumed-preparation-identity")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = evaluate_preparation(
            args.track,
            args.slug,
            consumed_preparation_identity=args.consumed_preparation_identity,
        )
    except (ReadinessError, RegistryValidationError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
