"""Deterministic implementation_map seeder for V7 Path 3."""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal, TypedDict

ObligationType = Literal[
    "sequence_step",
    "l2_error",
    "phonetic_rule",
    "decolonization_ban",
]
Artifact = Literal["module.md", "activities.yaml"]

OBLIGATION_GROUPS: tuple[tuple[str, ObligationType], ...] = (
    ("sequence_steps", "sequence_step"),
    ("l2_errors", "l2_error"),
    ("phonetic_rules", "phonetic_rule"),
    ("decolonization_bans", "decolonization_ban"),
)

IMPLEMENTATION_MAP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "schema_version",
        "slug",
        "wiki_path",
        "manifest_obligation_count",
        "entries",
    ],
    "properties": {
        "schema_version": {"const": 1},
        "slug": {"type": "string"},
        "wiki_path": {"type": "string"},
        "manifest_obligation_count": {"type": "integer", "minimum": 0},
        "entries": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "obligation_id",
                    "obligation_type",
                    "artifact",
                    "location_hint",
                    "treatment_template",
                    "manifest_payload",
                ],
                "properties": {
                    "obligation_id": {"type": "string"},
                    "obligation_type": {
                        "enum": [obligation_type for _, obligation_type in OBLIGATION_GROUPS],
                    },
                    "artifact": {"enum": ["module.md", "activities.yaml"]},
                    "location_hint": {"type": "string"},
                    "treatment_template": {"type": "object"},
                    "manifest_payload": {"type": "object"},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}

TREATMENT_TEMPLATES: dict[str, dict[str, Any]] = {
    "l2_error.contrast_pair": {
        "shape": "activities.yaml entry with fields {sentence, error, correction}",
        "expected_error_value": "<from manifest_payload.incorrect>",
        "expected_correction_value": "<from manifest_payload.correct>",
    },
    "l2_error.prose_explanation": {
        "shape": (
            "module.md prose paragraph that names manifest_payload.incorrect verbatim, "
            "contrasts with manifest_payload.correct, and explains manifest_payload.why"
        ),
    },
    "sequence_step": {
        "shape": (
            "module.md section heading or in-prose step marker matching "
            "manifest_payload.heading at the position implied by manifest_payload.step_num"
        ),
        "required_claim": "<from manifest_payload.required_claim>",
    },
    "phonetic_rule": {
        "shape": (
            "module.md prose that states the rule mapping manifest_payload.written "
            "-> manifest_payload.spoken with an explicit IPA bracket or equivalent"
        ),
    },
    "decolonization_ban": {
        "shape": (
            "module.md prose absent of any phrasing matching manifest_payload.rule "
            "(negative obligation: absence-of-pattern)"
        ),
    },
}


class ImplementationMapEntry(TypedDict):
    obligation_id: str
    obligation_type: ObligationType
    artifact: Artifact
    location_hint: str
    treatment_template: dict[str, Any]
    manifest_payload: dict[str, Any]


def seed_implementation_map(
    manifest: dict[str, Any],
    *,
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Seed one deterministic implementation-map entry per manifest obligation."""
    entries: list[ImplementationMapEntry] = []
    for obligation_type, manifest_payload in _iter_manifest_obligations(manifest):
        artifact = _artifact_for(obligation_type, manifest_payload)
        entries.append(
            {
                "obligation_id": str(manifest_payload.get("id") or ""),
                "obligation_type": obligation_type,
                "artifact": artifact,
                "location_hint": _location_hint(obligation_type, manifest_payload, artifact, plan),
                "treatment_template": _treatment_template(obligation_type, manifest_payload),
                "manifest_payload": manifest_payload,
            }
        )

    payload = {
        "schema_version": 1,
        "slug": str(manifest.get("slug") or ""),
        "wiki_path": str(manifest.get("wiki_path") or ""),
        "manifest_obligation_count": len(entries),
        "entries": entries,
    }
    validate_implementation_map(payload)
    return payload


def write_implementation_map(payload: dict[str, Any], path: Path) -> None:
    """Write a validated implementation map as deterministic JSON."""
    validate_implementation_map(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_implementation_map(path: Path) -> dict[str, Any]:
    """Read and validate an implementation map from JSON."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("implementation_map payload must be an object")
    validate_implementation_map(payload)
    return payload


def validate_implementation_map(payload: dict[str, Any]) -> None:
    """Validate the implementation_map.json contract."""
    if not isinstance(payload, dict):
        raise ValueError("implementation_map payload must be an object")

    required = set(IMPLEMENTATION_MAP_SCHEMA["required"])
    missing = sorted(required.difference(payload))
    if missing:
        raise ValueError(f"implementation_map missing required keys: {', '.join(missing)}")

    allowed = required
    extra = sorted(set(payload).difference(allowed))
    if extra:
        raise ValueError(f"implementation_map has unexpected keys: {', '.join(extra)}")

    if payload["schema_version"] != 1:
        raise ValueError("implementation_map schema_version must be 1")
    if not isinstance(payload["slug"], str) or not payload["slug"].strip():
        raise ValueError("implementation_map slug must be a non-empty string")
    if not isinstance(payload["wiki_path"], str):
        raise ValueError("implementation_map wiki_path must be a string")
    if not isinstance(payload["manifest_obligation_count"], int) or payload["manifest_obligation_count"] < 0:
        raise ValueError("implementation_map manifest_obligation_count must be a non-negative integer")

    entries = payload["entries"]
    if not isinstance(entries, list):
        raise ValueError("implementation_map entries must be a list")
    if payload["manifest_obligation_count"] != len(entries):
        raise ValueError("implementation_map manifest_obligation_count must equal len(entries)")

    for index, entry in enumerate(entries, start=1):
        _validate_entry(index, entry)


def _iter_manifest_obligations(manifest: Mapping[str, Any]) -> list[tuple[ObligationType, dict[str, Any]]]:
    obligations: list[tuple[ObligationType, dict[str, Any]]] = []
    for group, obligation_type in OBLIGATION_GROUPS:
        raw_items = manifest.get(group) or []
        if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes)):
            continue
        for item in raw_items:
            if isinstance(item, Mapping):
                obligations.append((obligation_type, copy.deepcopy(dict(item))))
    return obligations


def _artifact_for(obligation_type: ObligationType, manifest_payload: Mapping[str, Any]) -> Artifact:
    if obligation_type == "l2_error" and manifest_payload.get("treatment") == "contrast_pair":
        return "activities.yaml"
    return "module.md"


def _template_key(obligation_type: ObligationType, manifest_payload: Mapping[str, Any]) -> str:
    if obligation_type == "l2_error":
        if manifest_payload.get("treatment") == "contrast_pair":
            return "l2_error.contrast_pair"
        return "l2_error.prose_explanation"
    return obligation_type


def _treatment_template(
    obligation_type: ObligationType,
    manifest_payload: Mapping[str, Any],
) -> dict[str, Any]:
    template = copy.deepcopy(TREATMENT_TEMPLATES[_template_key(obligation_type, manifest_payload)])
    for key, value in list(template.items()):
        if isinstance(value, str) and value.startswith("<from manifest_payload.") and value.endswith(">"):
            payload_key = value.removeprefix("<from manifest_payload.").removesuffix(">")
            template[key] = manifest_payload.get(payload_key)
    return template


def _location_hint(
    obligation_type: ObligationType,
    manifest_payload: Mapping[str, Any],
    artifact: Artifact,
    plan: Mapping[str, Any] | None,
) -> str:
    if artifact == "activities.yaml":
        return "activities.yaml"
    if obligation_type == "sequence_step":
        return f"§{str(manifest_payload.get('heading') or '').strip()}"
    if plan is None:
        return "(any prose section)"

    keywords = _location_keywords(obligation_type, manifest_payload)
    for heading in _plan_section_headings(plan):
        heading_text = heading.casefold()
        if any(keyword.casefold() in heading_text for keyword in keywords):
            return f"§{heading}"
    return "(any prose section)"


def _location_keywords(
    obligation_type: ObligationType,
    manifest_payload: Mapping[str, Any],
) -> list[str]:
    fields = ["id"]
    if obligation_type == "l2_error":
        fields.append("incorrect")
    elif obligation_type == "phonetic_rule":
        fields.append("written")
    elif obligation_type == "decolonization_ban":
        fields.append("rule")

    keywords: list[str] = []
    for field in fields:
        value = manifest_payload.get(field)
        if value is None:
            continue
        keywords.extend(_keywords(str(value)))
    return keywords


def _keywords(value: str) -> list[str]:
    return [token for token in re.findall(r"[\w'’ʼ]+", value, flags=re.UNICODE) if len(token) >= 3]


def _plan_section_headings(plan: Mapping[str, Any]) -> list[str]:
    headings: list[str] = []
    for collection_key in ("sections", "content_outline"):
        sections = plan.get(collection_key)
        if not isinstance(sections, Sequence) or isinstance(sections, (str, bytes)):
            continue
        for section in sections:
            if not isinstance(section, Mapping):
                continue
            for heading_key in ("heading", "section", "title", "id"):
                heading = section.get(heading_key)
                if isinstance(heading, str) and heading.strip():
                    headings.append(heading.strip())
                    break
    return headings


def _validate_entry(index: int, entry: Any) -> None:
    if not isinstance(entry, dict):
        raise ValueError(f"implementation_map entries[{index}] must be an object")

    required = set(IMPLEMENTATION_MAP_SCHEMA["properties"]["entries"]["items"]["required"])
    missing = sorted(required.difference(entry))
    if missing:
        raise ValueError(f"implementation_map entries[{index}] missing required keys: {', '.join(missing)}")

    extra = sorted(set(entry).difference(required))
    if extra:
        raise ValueError(f"implementation_map entries[{index}] has unexpected keys: {', '.join(extra)}")

    obligation_id = entry["obligation_id"]
    obligation_type = entry["obligation_type"]
    artifact = entry["artifact"]
    location_hint = entry["location_hint"]
    treatment_template = entry["treatment_template"]
    manifest_payload = entry["manifest_payload"]

    if not isinstance(obligation_id, str) or not obligation_id.strip():
        raise ValueError(f"implementation_map entries[{index}] obligation_id must be a non-empty string")
    if obligation_type not in {obligation_type for _, obligation_type in OBLIGATION_GROUPS}:
        raise ValueError(f"implementation_map entries[{index}] has invalid obligation_type: {obligation_type}")
    if artifact not in {"module.md", "activities.yaml"}:
        raise ValueError(f"implementation_map entries[{index}] has invalid artifact: {artifact}")
    if not isinstance(location_hint, str) or not location_hint.strip():
        raise ValueError(f"implementation_map entries[{index}] location_hint must be a non-empty string")
    if not isinstance(treatment_template, dict) or not treatment_template.get("shape"):
        raise ValueError(f"implementation_map entries[{index}] treatment_template must include shape")
    if not isinstance(manifest_payload, dict):
        raise ValueError(f"implementation_map entries[{index}] manifest_payload must be an object")
    if manifest_payload.get("id") != obligation_id:
        raise ValueError(f"implementation_map entries[{index}] obligation_id must match manifest_payload.id")


def render_for_writer_prompt(payload: dict[str, Any]) -> str:
    """Render the implementation map as a human-readable contract block for the writer."""
    validate_implementation_map(payload)
    rows: list[str] = []
    for entry in sorted(payload["entries"], key=lambda e: str(e.get("obligation_id") or "")):
        rows.extend(
            [
                f"- obligation_id: {entry['obligation_id']}  "
                f"(obligation_type: {entry['obligation_type']})",
                f"  artifact: {entry['artifact']}",
                f"  location_hint: {entry['location_hint']}",
                "  treatment_template:",
            ]
        )
        for key, value in sorted(entry["treatment_template"].items()):
            rows.append(f"    {key}: {_render_template_value(value)}")
    body = "\n".join(rows)
    header = (
        f"Manifest obligations: {payload['manifest_obligation_count']}.\n"
        "Each row below is a pre-resolved slot the writer MUST fill at the artifact "
        "indicated by `artifact`, located by `location_hint`, populated using "
        "`treatment_template` as the structural blueprint."
    )
    return f"{header}\n\n{body}\n"


def _render_template_value(value: Any) -> str:
    if isinstance(value, Mapping):
        return json.dumps(dict(value), ensure_ascii=False, sort_keys=True)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return json.dumps(list(value), ensure_ascii=False)
    return str(value)
