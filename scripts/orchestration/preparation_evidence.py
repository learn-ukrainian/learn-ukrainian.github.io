"""Strict source-controlled manual evidence shared by preparation adapters."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import yaml

MANUAL_GATES = frozenset(
    {
        "dossier_grounding",
        "reading_rights",
        "wiki_grounding",
        "wiki_quote_verification",
        "image_rights",
        "corpus_hammer",
        "independent_content_review",
        "cohort_promotion",
        "hold",
        "merged_publication",
    }
)
MANUAL_STATUSES = frozenset({"pass", "fail"})
REVIEWER_FAMILIES = frozenset({"agy", "claude", "codex", "deepseek", "gemini", "grok", "human", "mixed"})
RIGHTS_DISPOSITIONS = frozenset({"approved", "exception-approved", "link-only-approved", "not-approved"})
APPROVED_RIGHTS_DISPOSITIONS = RIGHTS_DISPOSITIONS - {"not-approved"}


class RegistryValidationError(ValueError):
    """Raised when source-controlled manual evidence is malformed."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: yaml.SafeLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    loader.flatten_mapping(node)
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise RegistryValidationError(f"duplicate YAML key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_yaml_mapping(path: Path) -> dict:
    """Load one strict UTF-8 YAML mapping."""
    try:
        value = yaml.load(path.read_text(encoding="utf-8", errors="strict"), Loader=UniqueKeyLoader)
    except (OSError, UnicodeDecodeError, yaml.YAMLError, RegistryValidationError) as exc:
        raise RegistryValidationError(f"invalid YAML mapping {path}: {exc}") from exc
    if not isinstance(value, Mapping):
        raise RegistryValidationError(f"YAML document must be a mapping: {path}")
    return dict(value)


def _http_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _evidence_date(slug: str, name: object, raw_date: object) -> date:
    if isinstance(raw_date, str):
        try:
            return date.fromisoformat(raw_date)
        except ValueError as exc:
            raise RegistryValidationError(f"manual evidence {slug}.{name} has invalid date") from exc
    if isinstance(raw_date, date):
        return raw_date
    raise RegistryValidationError(f"manual evidence {slug}.{name} has invalid date")


def _validated_manual_record(slug: str, name: object, record: object) -> dict:
    if name not in MANUAL_GATES:
        raise RegistryValidationError(f"unsupported manual evidence gate {name!r} for {slug!r}")
    if not isinstance(record, Mapping):
        raise RegistryValidationError(f"manual evidence {slug}.{name} must be a mapping")
    status = record.get("status")
    if status not in MANUAL_STATUSES:
        raise RegistryValidationError(f"manual evidence {slug}.{name} has invalid status {status!r}")
    family = record.get("reviewer_family")
    if family not in REVIEWER_FAMILIES:
        raise RegistryValidationError(f"manual evidence {slug}.{name} has invalid reviewer_family {family!r}")
    if not _http_url(record.get("evidence_url")):
        raise RegistryValidationError(f"manual evidence {slug}.{name} needs an HTTP(S) evidence_url")
    clean = dict(record)
    clean["date"] = _evidence_date(slug, name, record.get("date"))
    if name in {"reading_rights", "image_rights"}:
        disposition = clean.get("disposition")
        if disposition not in RIGHTS_DISPOSITIONS:
            raise RegistryValidationError(f"manual evidence {slug}.{name} has invalid disposition")
        if (status == "pass") != (disposition in APPROVED_RIGHTS_DISPOSITIONS):
            raise RegistryValidationError(
                f"manual evidence {slug}.{name} status conflicts with disposition {disposition!r}"
            )
    if name == "hold":
        if status != "pass":
            raise RegistryValidationError(f"manual evidence {slug}.hold must record a reviewed pass")
        if (
            not isinstance(clean.get("active"), bool)
            or not isinstance(clean.get("reason"), str)
            or not clean["reason"].strip()
        ):
            raise RegistryValidationError(f"manual evidence {slug}.hold needs active boolean and reason")
        if clean["active"] is True:
            checked_evidence = clean.get("checked_evidence")
            if (
                not isinstance(clean.get("owner"), str)
                or not clean["owner"].strip()
                or not isinstance(clean.get("unblock_condition"), str)
                or not clean["unblock_condition"].strip()
                or not isinstance(checked_evidence, list)
                or not checked_evidence
                or not all(isinstance(item, str) and item.strip() for item in checked_evidence)
            ):
                raise RegistryValidationError(
                    f"manual evidence {slug}.hold active record needs owner, "
                    "checked_evidence, and unblock_condition"
                )
    return clean


def load_manual_evidence(path: Path, manifest_slugs: set[str]) -> dict[str, dict[str, dict]]:
    """Load and strictly validate sparse source-controlled manual evidence."""
    if not path.exists():
        return {}
    raw = load_yaml_mapping(path)
    if raw.get("version") != 1:
        raise RegistryValidationError("registry must be a mapping with version: 1")
    entries = raw.get("entries", {})
    if not isinstance(entries, Mapping):
        raise RegistryValidationError("registry entries must be a mapping")

    validated: dict[str, dict[str, dict]] = {}
    for slug, gates in entries.items():
        if not isinstance(slug, str) or slug not in manifest_slugs:
            raise RegistryValidationError(f"off-manifest registry slug: {slug!r}")
        if not isinstance(gates, Mapping) or not gates:
            raise RegistryValidationError(f"registry entry for {slug!r} must be a non-empty mapping")
        validated[slug] = {}
        for name, record in gates.items():
            validated[slug][str(name)] = _validated_manual_record(slug, name, record)
    return validated
