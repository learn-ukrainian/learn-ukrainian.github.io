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
CONTRACT_ROOT = Path("agents_extensions/shared/prompt-contracts")
REGISTRY_PATH = CONTRACT_ROOT / "registry.v1.yaml"
REGISTRY_SCHEMA_PATH = CONTRACT_ROOT / "schema/prompt-registry.v1.schema.json"
MANIFEST_SCHEMA_PATH = CONTRACT_ROOT / "schema/prompt-manifest.v1.schema.json"
PROFILE_SCHEMA_PATH = CONTRACT_ROOT / "schema/prompt-profile.v1.schema.json"
PROFILE_PATH = CONTRACT_ROOT / "profiles/curriculum-lifecycle.v1.yaml"
PARITY_PATH = Path("docs/architecture/curriculum-lifecycle-prompt-responsibility-parity.md")
LEGACY_PROMPT_ROOT = Path("docs/prompts/orchestrators")

_PLACEHOLDER_RE = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")
_PARITY_ROW_RE = re.compile(r"^\| `([^`]+\.md)` \|", re.MULTILINE)


class PromptContractError(ValueError):
    """Raised when prompt contract source or resolved evidence is invalid."""


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

    profiles = load_profiles(repo_root=repo_root)["profiles"]
    for profile_id, profile in profiles.items():
        manifest, _, _ = _load_manifest(
            str(profile["prompt_id"]),
            str(profile["prompt_version"]),
            repo_root=repo_root,
        )
        variant = manifest["variants"].get(profile["variant"])
        if not isinstance(variant, Mapping):
            raise PromptContractError(f"profile {profile_id} selects an unregistered variant")

    legacy_root = repo_root / LEGACY_PROMPT_ROOT
    inventory = sorted(path.relative_to(legacy_root).as_posix() for path in legacy_root.rglob("*") if path.is_file())
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
        "legacy_inventory_count": len(inventory),
        "classified_inventory_count": len(classified),
        "unclassified_inventory": missing,
        "legacy_entry_points_removed": 0,
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
        else:
            payload = audit_contracts()
    except PromptContractError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
