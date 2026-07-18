#!/usr/bin/env python3
"""Deterministic, versioned prompt contracts for curriculum lifecycle phases."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CONTRACT_ROOT = Path("agents_extensions/shared/prompt-contracts")
REGISTRY_PATH = CONTRACT_ROOT / "registry.v1.yaml"
REGISTRY_SCHEMA_PATH = CONTRACT_ROOT / "schema/prompt-registry.v1.schema.json"
MANIFEST_SCHEMA_PATH = CONTRACT_ROOT / "schema/prompt-manifest.v1.schema.json"
PROFILE_SCHEMA_PATH = CONTRACT_ROOT / "schema/prompt-profile.v1.schema.json"
PROFILE_PATH = CONTRACT_ROOT / "profiles/curriculum-lifecycle.v1.yaml"
PARITY_PATH = Path("docs/architecture/curriculum-lifecycle-prompt-responsibility-parity.md")
LEGACY_PROMPT_ROOT = Path("docs/prompts/orchestrators")
CURRICULUM_MANIFEST_PATH = Path("curriculum/l2-uk-en/curriculum.yaml")
MANIFEST_TYPE_FAMILIES = {"core": "core", "track": "seminar"}
MIGRATION_PATH = Path(
    "agents_extensions/shared/curriculum-lifecycle/config/legacy-prompt-migration.v1.yaml"
)
MIGRATION_SCHEMA_PATH = Path(
    "agents_extensions/shared/curriculum-lifecycle/schema/legacy-prompt-migration.v1.schema.json"
)

_PLACEHOLDER_RE = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")
_PARITY_ROW_RE = re.compile(r"^\| `([^`]+\.md)` \|", re.MULTILINE)
_LIFECYCLE_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class PromptContractError(ValueError):
    """Raised when prompt contract source or resolved evidence is invalid."""


class LifecycleConfigError(ValueError):
    """Raised when manifest authority and lifecycle selectors disagree."""


class _StrictLoader(yaml.SafeLoader):
    """YAML loader that fails instead of silently overwriting duplicate keys."""


def _construct_mapping(loader: _StrictLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise PromptContractError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


@dataclass(frozen=True)
class SourceIdentity:
    kind: str
    id: str
    path: str
    sha256: str


@dataclass(frozen=True)
class ResolvedPrompt:
    prompt_id: str
    version: str
    variant: str
    route: str
    profile_id: str | None
    context: dict[str, Any]
    context_sha256: str
    input_schema_id: str
    output_schema_id: str
    fragment_ids: tuple[str, ...]
    sources: tuple[SourceIdentity, ...]
    rendered_prompt: str
    prompt_sha256: str
    identity_sha256: str

    def to_record(self) -> dict[str, Any]:
        record = asdict(self)
        record["fragment_ids"] = list(self.fragment_ids)
        record["sources"] = [asdict(source) for source in self.sources]
        return record


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PromptContractError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise PromptContractError(f"non-standard JSON constant: {value}")


def _repo_file(repo_root: Path, relative: str | Path) -> Path:
    raw = str(relative)
    path = Path(raw)
    if not raw or "\\" in raw or path.is_absolute() or ".." in path.parts or raw.startswith("~"):
        raise PromptContractError(f"path must be a safe repository-relative path: {raw!r}")
    root = repo_root.resolve()
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise PromptContractError(f"path escapes repository root: {raw!r}") from exc
    if not candidate.is_file():
        raise PromptContractError(f"required prompt contract file is missing: {raw}")
    return candidate


def _relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _shared_file(repo_root: Path, relative: str | Path, label: str) -> Path:
    path = _repo_file(repo_root, relative)
    source = _relative(path, repo_root)
    if not source.startswith("agents_extensions/shared/"):
        raise PromptContractError(f"{label} must live under agents_extensions/shared: {source}")
    return path


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise PromptContractError(f"cannot read {path}: {exc}") from exc


def _load_yaml(path: Path) -> dict[str, Any]:
    raw = _read_bytes(path)
    try:
        value = yaml.load(raw.decode("utf-8", errors="strict"), Loader=_StrictLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise PromptContractError(f"invalid UTF-8/YAML in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PromptContractError(f"YAML document must be an object: {path}")
    return value


def load_active_tracks(
    repo_root: Path,
    manifest_path: str | Path = CURRICULUM_MANIFEST_PATH,
) -> dict[str, str]:
    """Return the active ``track -> manifest type`` map from curriculum.yaml."""
    try:
        manifest = _load_yaml(_repo_file(repo_root, manifest_path))
    except PromptContractError as exc:
        raise LifecycleConfigError(str(exc)) from exc
    levels = manifest.get("levels")
    if not isinstance(levels, Mapping) or not levels:
        raise LifecycleConfigError("curriculum manifest must contain a non-empty levels mapping")
    active: dict[str, str] = {}
    for raw_track, raw_record in levels.items():
        if not isinstance(raw_track, str) or not _LIFECYCLE_IDENTIFIER_RE.fullmatch(raw_track):
            raise LifecycleConfigError(f"invalid active curriculum track: {raw_track!r}")
        if not isinstance(raw_record, Mapping):
            raise LifecycleConfigError(f"manifest levels.{raw_track} must be a mapping")
        manifest_type = raw_record.get("type")
        modules = raw_record.get("modules")
        if not isinstance(manifest_type, str) or not _LIFECYCLE_IDENTIFIER_RE.fullmatch(
            manifest_type
        ):
            raise LifecycleConfigError(f"manifest levels.{raw_track}.type is invalid")
        if not isinstance(modules, list) or not all(
            isinstance(slug, str) and _LIFECYCLE_IDENTIFIER_RE.fullmatch(slug)
            for slug in modules
        ):
            raise LifecycleConfigError(
                f"manifest levels.{raw_track}.modules must be a list of repository slugs"
            )
        if len(modules) != len(set(modules)):
            raise LifecycleConfigError(f"manifest levels.{raw_track}.modules contains duplicates")
        active[raw_track] = manifest_type
    return active


def reject_stale_track_keys(
    keys: Mapping[str, Any] | set[str],
    active_tracks: Mapping[str, str],
    *,
    label: str,
) -> None:
    """Reject track-keyed config that names anything outside the active manifest."""
    stale = sorted(set(keys) - set(active_tracks))
    if stale:
        raise LifecycleConfigError(f"{label} references inactive tracks: {', '.join(stale)}")


def resolve_profile_selectors(
    *,
    selectors: Mapping[str, Any],
    profile_families: Mapping[str, str],
    active_tracks: Mapping[str, str],
    label: str,
    manifest_type_families: Mapping[str, str] = MANIFEST_TYPE_FAMILIES,
) -> dict[str, str]:
    """Resolve every active track through strict overrides or manifest-type defaults."""
    track_selectors = selectors.get("tracks")
    type_selectors = selectors.get("manifest_types")
    if not isinstance(track_selectors, Mapping) or not isinstance(type_selectors, Mapping):
        raise LifecycleConfigError(f"{label} selectors must contain tracks and manifest_types mappings")
    reject_stale_track_keys(track_selectors, active_tracks, label=f"{label} track selector")

    resolved: dict[str, str] = {}
    for track, manifest_type in active_tracks.items():
        expected_family = manifest_type_families.get(manifest_type)
        if expected_family is None:
            raise LifecycleConfigError(
                f"{label} has no family contract for active manifest type {manifest_type!r}"
            )
        profile_id = track_selectors.get(track) or type_selectors.get(manifest_type)
        if not isinstance(profile_id, str):
            raise LifecycleConfigError(
                f"{label} has no profile for active track={track} type={manifest_type}"
            )
        profile_family = profile_families.get(profile_id)
        if profile_family is None:
            raise LifecycleConfigError(f"{label} selects unknown profile {profile_id!r} for {track}")
        if profile_family != expected_family:
            raise LifecycleConfigError(
                f"{label} profile {profile_id!r} has family {profile_family!r}; "
                f"active track {track!r} requires {expected_family!r}"
            )
        resolved[track] = profile_id
    return resolved


def _load_json(path: Path) -> dict[str, Any]:
    raw = _read_bytes(path)
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PromptContractError(f"invalid UTF-8/JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PromptContractError(f"JSON document must be an object: {path}")
    return value


def _check_schema(schema: Mapping[str, Any], label: str) -> None:
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # jsonschema exposes several schema error subclasses
        raise PromptContractError(f"invalid JSON schema for {label}: {exc}") from exc


def _schema_id(schema: Mapping[str, Any], label: str) -> str:
    schema_id = schema.get("$id")
    if not isinstance(schema_id, str) or not schema_id:
        raise PromptContractError(f"{label} must declare a non-empty $id")
    return schema_id


def _validate(document: Mapping[str, Any], schema: Mapping[str, Any], label: str) -> None:
    _check_schema(schema, label)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda item: tuple(str(part) for part in item.path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise PromptContractError(f"{label} failed schema validation at {location}: {error.message}")


def _source_identity(kind: str, source_id: str, path: Path, repo_root: Path) -> SourceIdentity:
    return SourceIdentity(
        kind=kind,
        id=source_id,
        path=_relative(path, repo_root),
        sha256=_sha256_bytes(_read_bytes(path)),
    )


def load_registry(*, repo_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry_path = _repo_file(repo_root, REGISTRY_PATH)
    schema = _load_json(_repo_file(repo_root, REGISTRY_SCHEMA_PATH))
    registry = _load_yaml(registry_path)
    _validate(registry, schema, "prompt registry")
    for prompt_id, record in registry["prompts"].items():
        if record["current"] not in record["versions"]:
            raise PromptContractError(f"registry current version is not registered: {prompt_id}@{record['current']}")
    return registry


def load_profiles(*, repo_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    schema = _load_json(_repo_file(repo_root, PROFILE_SCHEMA_PATH))
    profiles = _load_yaml(_repo_file(repo_root, PROFILE_PATH))
    _validate(profiles, schema, "prompt profiles")
    return profiles


def _repo_existing(repo_root: Path, relative: str | Path, label: str) -> Path:
    raw = str(relative)
    path = Path(raw)
    if not raw or path.is_absolute() or ".." in path.parts:
        raise PromptContractError(f"{label} path must be repository-relative: {raw!r}")
    root = repo_root.resolve()
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise PromptContractError(f"{label} path escapes repository root: {raw!r}") from exc
    if not candidate.exists():
        raise PromptContractError(f"{label} path is missing: {raw}")
    return candidate


def load_legacy_migration(*, repo_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Load the hash-frozen legacy disposition and canonical owner registry."""
    migration = _load_yaml(_repo_file(repo_root, MIGRATION_PATH))
    schema = _load_json(_repo_file(repo_root, MIGRATION_SCHEMA_PATH))
    _validate(migration, schema, "legacy prompt migration")
    _repo_existing(
        repo_root,
        migration["canonical_replacement"]["source"],
        "canonical replacement",
    )
    _repo_existing(
        repo_root,
        migration["canonical_replacement"]["pilot_report"],
        "pilot report",
    )
    for owner, paths in migration["owner_paths"].items():
        for path in paths:
            _repo_existing(repo_root, path, f"{owner} owner")
    rationale_ids = set(migration["rationales"])
    unknown_rationales = sorted(
        {
            entry["rationale_id"]
            for entry in migration["entries"].values()
            if entry["rationale_id"] not in rationale_ids
        }
    )
    if unknown_rationales:
        raise PromptContractError(
            f"legacy prompt migration uses unknown rationales: {', '.join(unknown_rationales)}"
        )
    return migration


def validate_legacy_prompt_files(
    migration: Mapping[str, Any],
    legacy_root: Path,
) -> list[str]:
    """Require exact legacy inventory and bytes without modifying retained files."""
    inventory = sorted(
        path.relative_to(legacy_root).as_posix()
        for path in legacy_root.rglob("*")
        if path.is_file()
    )
    migration_entries = migration["entries"]
    migration_missing = sorted(set(inventory) - set(migration_entries))
    migration_extra = sorted(set(migration_entries) - set(inventory))
    if migration_missing or migration_extra:
        raise PromptContractError(
            "legacy prompt migration inventory drift: "
            f"missing={migration_missing} extra={migration_extra}"
        )
    hash_drift = sorted(
        relative
        for relative, entry in migration_entries.items()
        if _sha256_bytes((legacy_root / relative).read_bytes()) != entry["content_sha256"]
    )
    if hash_drift:
        raise PromptContractError(
            f"legacy prompt migration byte hashes changed: {', '.join(hash_drift)}"
        )
    return inventory


def _profile_families(
    profiles: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, str]:
    families: dict[str, str] = {}
    for profile_id, profile in profiles["profiles"].items():
        manifest, _, _ = _load_manifest(
            str(profile["prompt_id"]),
            str(profile["prompt_version"]),
            repo_root=repo_root,
        )
        variant = manifest["variants"].get(profile["variant"])
        if not isinstance(variant, Mapping):
            raise PromptContractError(f"profile {profile_id} selects an unregistered variant")
        families[str(profile_id)] = str(variant["family"])
    return families


def active_track_profiles(
    *,
    repo_root: Path = PROJECT_ROOT,
    active_tracks: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Resolve exact semantic profiles from the active curriculum manifest."""
    profiles = load_profiles(repo_root=repo_root)
    try:
        return resolve_profile_selectors(
            selectors=profiles["selectors"],
            profile_families=_profile_families(profiles, repo_root=repo_root),
            active_tracks=active_tracks if active_tracks is not None else load_active_tracks(repo_root),
            label="curriculum prompt profiles",
        )
    except LifecycleConfigError as exc:
        raise PromptContractError(str(exc)) from exc


def _load_manifest(
    prompt_id: str,
    version: str | None,
    *,
    repo_root: Path,
) -> tuple[dict[str, Any], Path, str]:
    registry = load_registry(repo_root=repo_root)
    prompt_record = registry["prompts"].get(prompt_id)
    if not isinstance(prompt_record, Mapping):
        raise PromptContractError(f"prompt id is not registered: {prompt_id}")
    resolved_version = version or str(prompt_record["current"])
    manifest_ref = prompt_record["versions"].get(resolved_version)
    if not isinstance(manifest_ref, str):
        raise PromptContractError(f"prompt version is not registered: {prompt_id}@{resolved_version}")
    manifest_path = _shared_file(repo_root, manifest_ref, "executable prompt manifest")
    manifest = _load_yaml(manifest_path)
    schema = _load_json(_repo_file(repo_root, MANIFEST_SCHEMA_PATH))
    _validate(manifest, schema, f"prompt manifest {prompt_id}@{resolved_version}")
    if manifest["prompt_id"] != prompt_id or manifest["version"] != resolved_version:
        raise PromptContractError("registry identity does not match manifest prompt_id/version")
    return manifest, manifest_path, resolved_version


def _ordered_fragment_ids(manifest: Mapping[str, Any], variant: str) -> tuple[str, ...]:
    variants = manifest["variants"]
    variant_record = variants.get(variant)
    if not isinstance(variant_record, Mapping):
        raise PromptContractError(f"prompt variant is not registered: {variant}")
    fragments = manifest["fragments"]
    emitted: set[str] = set()
    active: list[str] = []
    sections: dict[str, str] = {}
    ordered: list[str] = []

    def visit(fragment_id: str) -> None:
        fragment = fragments.get(fragment_id)
        if not isinstance(fragment, Mapping):
            raise PromptContractError(f"missing registered fragment: {fragment_id}")
        if fragment_id in active:
            cycle = " -> ".join([*active, fragment_id])
            raise PromptContractError(f"prompt include cycle: {cycle}")
        if fragment_id in emitted:
            raise PromptContractError(f"duplicate fragment inclusion: {fragment_id}")
        active.append(fragment_id)
        for included in fragment["includes"]:
            visit(str(included))
        active.pop()
        section = str(fragment["section"])
        owner = sections.get(section)
        if owner is not None:
            raise PromptContractError(f"conflicting prompt section {section!r}: {owner} and {fragment_id}")
        sections[section] = fragment_id
        emitted.add(fragment_id)
        ordered.append(fragment_id)

    for root in variant_record["roots"]:
        visit(str(root))
    return tuple(ordered)


def _fragment_text(path: Path) -> str:
    raw = _read_bytes(path)
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise PromptContractError(f"prompt fragment is not strict UTF-8: {path}") from exc
    if "\r" in text or not text.endswith("\n") or text.endswith("\n\n"):
        raise PromptContractError(f"prompt fragment must use LF and end with exactly one newline: {path}")
    return text[:-1]


def _render_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return _canonical_json(value)


def _render_fragment(text: str, context: Mapping[str, Any], declared_inputs: set[str]) -> str:
    placeholders = set(_PLACEHOLDER_RE.findall(text))
    undeclared = sorted(placeholders - declared_inputs)
    if undeclared:
        raise PromptContractError(f"fragment uses undeclared input placeholders: {', '.join(undeclared)}")
    missing = sorted(placeholders - set(context))
    if missing:
        raise PromptContractError(f"fragment inputs are missing: {', '.join(missing)}")
    rendered = _PLACEHOLDER_RE.sub(lambda match: _render_value(context[match.group(1)]), text)
    if "{{" in rendered or "}}" in rendered:
        raise PromptContractError("rendered prompt contains an unresolved or malformed placeholder")
    return rendered


def resolve_prompt(
    prompt_id: str,
    *,
    variant: str,
    context: Mapping[str, Any],
    version: str | None = None,
    route: str = "tool-capable",
    profile_id: str | None = None,
    repo_root: Path = PROJECT_ROOT,
) -> ResolvedPrompt:
    manifest, manifest_path, resolved_version = _load_manifest(
        prompt_id,
        version,
        repo_root=repo_root,
    )
    if route not in manifest["compatible"]["routes"]:
        raise PromptContractError(f"route is not compatible with prompt contract: {route}")
    variant_record = manifest["variants"].get(variant)
    if not isinstance(variant_record, Mapping):
        raise PromptContractError(f"prompt variant is not registered: {variant}")
    if variant_record["family"] not in manifest["compatible"]["families"]:
        raise PromptContractError(f"variant family is not compatible with prompt contract: {variant}")

    input_schema_path = _shared_file(repo_root, manifest["input_schema"], "prompt input schema")
    output_schema_path = _shared_file(repo_root, manifest["output_schema"], "prompt output schema")
    input_schema = _load_json(input_schema_path)
    output_schema = _load_json(output_schema_path)
    _validate(dict(context), input_schema, "prompt input")
    _check_schema(output_schema, "prompt output")
    input_schema_id = _schema_id(input_schema, "prompt input schema")
    output_schema_id = _schema_id(output_schema, "prompt output schema")
    if context.get("family") != variant_record["family"]:
        raise PromptContractError("prompt context family does not match selected variant family")

    ordered_ids = _ordered_fragment_ids(manifest, variant)
    declared_inputs = set((input_schema.get("properties") or {}).keys())
    sources: list[SourceIdentity] = [
        _source_identity("registry", "prompt-registry.v1", _repo_file(repo_root, REGISTRY_PATH), repo_root),
        _source_identity("manifest", f"{prompt_id}@{resolved_version}", manifest_path, repo_root),
        _source_identity("input-schema", input_schema_id, input_schema_path, repo_root),
        _source_identity("output-schema", output_schema_id, output_schema_path, repo_root),
    ]
    if profile_id is not None:
        sources.append(_source_identity("profile", profile_id, _repo_file(repo_root, PROFILE_PATH), repo_root))
    for policy_id in sorted(manifest["policy_ids"]):
        policy_path = _shared_file(
            repo_root,
            manifest["policy_ids"][policy_id],
            f"prompt policy {policy_id}",
        )
        sources.append(_source_identity("policy", policy_id, policy_path, repo_root))

    rendered_fragments: list[str] = []
    for fragment_id in ordered_ids:
        fragment = manifest["fragments"][fragment_id]
        fragment_path = _shared_file(repo_root, fragment["path"], f"prompt fragment {fragment_id}")
        sources.append(_source_identity("fragment", fragment_id, fragment_path, repo_root))
        rendered_fragments.append(_render_fragment(_fragment_text(fragment_path), context, declared_inputs))

    rendered_prompt = "\n\n---\n\n".join(rendered_fragments) + "\n"
    prompt_sha256 = _sha256_bytes(rendered_prompt.encode("utf-8"))
    context_record = dict(context)
    context_sha256 = _sha256_bytes(_canonical_json(context_record).encode("utf-8"))
    identity_payload = {
        "prompt_id": prompt_id,
        "version": resolved_version,
        "variant": variant,
        "route": route,
        "profile_id": profile_id,
        "context_sha256": context_sha256,
        "prompt_sha256": prompt_sha256,
        "sources": [asdict(source) for source in sources],
    }
    identity_sha256 = _sha256_bytes(_canonical_json(identity_payload).encode("utf-8"))
    return ResolvedPrompt(
        prompt_id=prompt_id,
        version=resolved_version,
        variant=variant,
        route=route,
        profile_id=profile_id,
        context=context_record,
        context_sha256=context_sha256,
        input_schema_id=input_schema_id,
        output_schema_id=output_schema_id,
        fragment_ids=ordered_ids,
        sources=tuple(sources),
        rendered_prompt=rendered_prompt,
        prompt_sha256=prompt_sha256,
        identity_sha256=identity_sha256,
    )


def resolve_profile(
    profile_id: str,
    *,
    context: Mapping[str, Any],
    route: str = "tool-capable",
    repo_root: Path = PROJECT_ROOT,
) -> ResolvedPrompt:
    profile = load_profiles(repo_root=repo_root)["profiles"].get(profile_id)
    if not isinstance(profile, Mapping):
        raise PromptContractError(f"prompt profile is not registered: {profile_id}")
    return resolve_prompt(
        str(profile["prompt_id"]),
        version=str(profile["prompt_version"]),
        variant=str(profile["variant"]),
        context=context,
        route=route,
        profile_id=profile_id,
        repo_root=repo_root,
    )


def resolve_track_profile(
    track: str,
    *,
    context: Mapping[str, Any],
    route: str = "tool-capable",
    repo_root: Path = PROJECT_ROOT,
) -> ResolvedPrompt:
    """Resolve one active track through the manifest-derived profile map."""
    normalized = track.strip().lower()
    if context.get("track") != normalized:
        raise PromptContractError("prompt context track does not match requested active track")
    profile_id = active_track_profiles(repo_root=repo_root).get(normalized)
    if profile_id is None:
        raise PromptContractError(f"curriculum manifest has no active track: {normalized}")
    return resolve_profile(profile_id, context=context, route=route, repo_root=repo_root)


def validate_output(resolved: ResolvedPrompt, payload: Mapping[str, Any], *, repo_root: Path = PROJECT_ROOT) -> None:
    manifest, _, _ = _load_manifest(resolved.prompt_id, resolved.version, repo_root=repo_root)
    output_schema = _load_json(_repo_file(repo_root, manifest["output_schema"]))
    _validate(dict(payload), output_schema, "prompt output")


def verify_record(record: Mapping[str, Any], *, repo_root: Path = PROJECT_ROOT) -> ResolvedPrompt:
    required = set(ResolvedPrompt.__dataclass_fields__)
    if set(record) != required:
        raise PromptContractError("resolved prompt record has missing or extra fields")
    context = record.get("context")
    if not isinstance(context, Mapping):
        raise PromptContractError("resolved prompt record context must be an object")
    profile_id = record.get("profile_id")
    if profile_id is None:
        resolved = resolve_prompt(
            str(record["prompt_id"]),
            version=str(record["version"]),
            variant=str(record["variant"]),
            context=context,
            route=str(record["route"]),
            repo_root=repo_root,
        )
    else:
        resolved = resolve_profile(
            str(profile_id),
            context=context,
            route=str(record["route"]),
            repo_root=repo_root,
        )
    if resolved.to_record() != dict(record):
        raise PromptContractError("resolved prompt record does not match current exact contract bytes and identities")
    return resolved


def audit_contracts(*, repo_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = load_registry(repo_root=repo_root)
    prompt_versions: list[str] = []
    variants: list[str] = []
    for prompt_id in sorted(registry["prompts"]):
        for version in sorted(registry["prompts"][prompt_id]["versions"]):
            manifest, _, _ = _load_manifest(prompt_id, version, repo_root=repo_root)
            for variant in sorted(manifest["variants"]):
                _ordered_fragment_ids(manifest, variant)
                variants.append(f"{prompt_id}@{version}:{variant}")
            prompt_versions.append(f"{prompt_id}@{version}")

    profile_document = load_profiles(repo_root=repo_root)
    profiles = profile_document["profiles"]
    for profile_id, profile in profiles.items():
        manifest, _, _ = _load_manifest(
            str(profile["prompt_id"]),
            str(profile["prompt_version"]),
            repo_root=repo_root,
        )
        variant = manifest["variants"].get(profile["variant"])
        if not isinstance(variant, Mapping):
            raise PromptContractError(f"profile {profile_id} selects an unregistered variant")

    track_profiles = active_track_profiles(repo_root=repo_root)
    migration = load_legacy_migration(repo_root=repo_root)
    legacy_root = repo_root / LEGACY_PROMPT_ROOT
    inventory = validate_legacy_prompt_files(migration, legacy_root)
    migration_entries = migration["entries"]
    parity_text = _repo_file(repo_root, PARITY_PATH).read_text(encoding="utf-8")
    classified = _PARITY_ROW_RE.findall(parity_text)
    duplicate_classifications = sorted({item for item in classified if classified.count(item) > 1})
    missing = sorted(set(inventory) - set(classified))
    extra = sorted(set(classified) - set(inventory))
    if duplicate_classifications or missing or extra:
        raise PromptContractError(
            "responsibility parity is incomplete: "
            f"duplicates={duplicate_classifications} missing={missing} extra={extra}"
        )
    return {
        "registry_version": registry["registry_version"],
        "canonical_source_root": CONTRACT_ROOT.as_posix(),
        "docs_prompts_executable_authority": False,
        "registered_prompt_versions": prompt_versions,
        "registered_variants": variants,
        "registered_profiles": sorted(profiles),
        "active_track_profiles": track_profiles,
        "legacy_migration_version": migration["config_version"],
        "canonical_invocation": migration["canonical_replacement"]["invocation"],
        "legacy_inventory_count": len(inventory),
        "classified_inventory_count": len(classified),
        "unclassified_inventory": missing,
        "legacy_entry_points_removed": 0,
        "legacy_entry_points_deprecated": len(migration_entries),
        "legacy_operator_entry_points": sum(
            bool(entry["operator_entry_point"]) for entry in migration_entries.values()
        ),
        "legacy_retained_eval_count": sum(
            entry["disposition"] == "retained-eval" for entry in migration_entries.values()
        ),
    }


def _context_from_file(value: str, repo_root: Path) -> dict[str, Any]:
    path = _repo_file(repo_root, value)
    return _load_json(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    resolve_parser = subparsers.add_parser("resolve", help="Resolve one registered profile to exact prompt bytes")
    resolve_parser.add_argument("--profile", required=True)
    resolve_parser.add_argument("--context", required=True, help="Repository-relative JSON context path")
    resolve_parser.add_argument("--route", default="tool-capable")
    resolve_track_parser = subparsers.add_parser(
        "resolve-track", help="Resolve one active manifest track to exact prompt bytes"
    )
    resolve_track_parser.add_argument("--track", required=True)
    resolve_track_parser.add_argument("--context", required=True, help="Repository-relative JSON context path")
    resolve_track_parser.add_argument("--route", default="tool-capable")
    subparsers.add_parser("audit", help="Validate contracts and report P0 responsibility parity")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "resolve":
            payload = resolve_profile(
                args.profile,
                context=_context_from_file(args.context, PROJECT_ROOT),
                route=args.route,
            ).to_record()
        elif args.command == "resolve-track":
            payload = resolve_track_profile(
                args.track,
                context=_context_from_file(args.context, PROJECT_ROOT),
                route=args.route,
            ).to_record()
        else:
            payload = audit_contracts()
    except PromptContractError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
