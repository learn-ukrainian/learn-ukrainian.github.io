#!/usr/bin/env python3
"""Validate seminar tracks use prompt suites, not retired structural templates."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # GitHub prompt-lint job uses plain Python.
    yaml = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = PROJECT_ROOT / "docs" / "l2-uk-en" / "templates"

RETIRED_TEMPLATE_FILES = (
    "docs/l2-uk-en/templates/ai/c1-history-module-template.md",
    "docs/l2-uk-en/templates/ai/lit-module-template.md",
    "docs/l2-uk-en/templates/lit-module-template.md",
    "docs/l2-uk-en/templates/seminar-folk-module-template.md",
)

RETIRED_REFERENCE_MARKERS = (
    *RETIRED_TEMPLATE_FILES,
    "docs/l2-uk-en/templates/istorioory-module-template.md",
)

REQUIRED_PROMPT_FILES = (
    "docs/prompts/orchestrators/bio/suite-orchestrator.md",
    "docs/prompts/orchestrators/folk/preflight-readiness-audit-orchestrator.md",
    "docs/prompts/orchestrators/folk/production-build-orchestrator.md",
    "docs/prompts/orchestrators/folk/quality-audit-orchestrator.md",
    "docs/prompts/orchestrators/folk/remediation-build-orchestrator.md",
    "docs/prompts/orchestrators/hist/suite-orchestrator.md",
    "docs/prompts/orchestrators/istorio/suite-orchestrator.md",
    "docs/prompts/orchestrators/lit/suite-orchestrator.md",
    "docs/prompts/orchestrators/lit-drama/suite-orchestrator.md",
    "docs/prompts/orchestrators/lit-essay/suite-orchestrator.md",
    "docs/prompts/orchestrators/lit-fantastika/suite-orchestrator.md",
    "docs/prompts/orchestrators/lit-hist-fic/suite-orchestrator.md",
    "docs/prompts/orchestrators/lit-humor/suite-orchestrator.md",
    "docs/prompts/orchestrators/lit-war/suite-orchestrator.md",
    "docs/prompts/orchestrators/lit-youth/suite-orchestrator.md",
    "docs/prompts/orchestrators/oes/suite-orchestrator.md",
    "docs/prompts/orchestrators/ruth/suite-orchestrator.md",
)

ACTIVE_SCAN_ROOTS = (
    PROJECT_ROOT / "agents_extensions" / "shared" / "quick-ref",
    PROJECT_ROOT / "docs" / "l2-uk-en",
    PROJECT_ROOT / "docs" / "prompts" / "orchestrators",
)

ACTIVE_SCAN_FILES = (
    PROJECT_ROOT / "docs" / "l2-uk-en" / "template_mappings.yaml",
    PROJECT_ROOT / "scripts" / "generate_mdx" / "generate_skeleton.py",
)


def _load_template_mappings(errors: list[str]) -> dict[str, Any]:
    mapping_path = PROJECT_ROOT / "docs" / "l2-uk-en" / "template_mappings.yaml"
    if yaml is None:
        return {}

    try:
        data = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"{mapping_path}: invalid YAML: {exc}")
        return {}

    if not isinstance(data, dict):
        errors.append(f"{mapping_path}: expected YAML object")
        return {}
    if not isinstance(data.get("mappings"), list):
        errors.append(f"{mapping_path}: expected mappings list")
        return {}
    return data


def _template_mapping_entries(errors: list[str]) -> list[tuple[int, str | None]]:
    mapping_path = PROJECT_ROOT / "docs" / "l2-uk-en" / "template_mappings.yaml"
    if yaml is None:
        text = mapping_path.read_text(encoding="utf-8")
        templates = re.findall(r"^\s*template:\s*['\"]?([^'\"\s#]+)", text, re.MULTILINE)
        if not templates:
            errors.append(f"{mapping_path}: no template entries found")
        return list(enumerate(templates, start=1))

    data = _load_template_mappings(errors)
    entries: list[tuple[int, str | None]] = []
    for index, mapping in enumerate(data.get("mappings", []), start=1):
        if not isinstance(mapping, dict):
            errors.append(f"template_mappings.yaml entry {index}: expected object")
            continue

        template = mapping.get("template")
        if template is not None and not isinstance(template, str):
            errors.append(f"template_mappings.yaml entry {index}: template must be string")
            continue
        entries.append((index, template))
    return entries


def _check_required_prompt_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PROMPT_FILES:
        path = PROJECT_ROOT / rel_path
        if not path.is_file():
            errors.append(f"missing seminar prompt suite: {rel_path}")


def _check_retired_templates_absent(errors: list[str]) -> None:
    for rel_path in RETIRED_TEMPLATE_FILES:
        path = PROJECT_ROOT / rel_path
        if path.exists():
            errors.append(f"retired seminar template still exists: {rel_path}")


def _check_template_mappings(errors: list[str]) -> None:
    for index, template in _template_mapping_entries(errors):
        if not template:
            errors.append(f"template_mappings.yaml entry {index}: missing template")
            continue

        rel_path = f"docs/l2-uk-en/templates/{template}"
        if rel_path in RETIRED_TEMPLATE_FILES:
            errors.append(f"template_mappings.yaml entry {index}: retired template {template}")
        if not (TEMPLATE_ROOT / template).is_file():
            errors.append(f"template_mappings.yaml entry {index}: missing template {template}")


def _iter_active_scan_files() -> list[Path]:
    files = list(ACTIVE_SCAN_FILES)
    for root in ACTIVE_SCAN_ROOTS:
        files.extend(sorted(root.rglob("*.md")))
    return files


def _check_no_retired_refs(errors: list[str]) -> None:
    for path in _iter_active_scan_files():
        if "_archive" in path.parts:
            continue
        if not path.is_file():
            errors.append(f"missing active scan file: {path.relative_to(PROJECT_ROOT)}")
            continue

        text = path.read_text(encoding="utf-8")
        for marker in RETIRED_REFERENCE_MARKERS:
            if marker in text:
                rel_path = path.relative_to(PROJECT_ROOT)
                errors.append(f"{rel_path}: references retired template path {marker}")


def validate() -> list[str]:
    errors: list[str] = []
    _check_required_prompt_files(errors)
    _check_retired_templates_absent(errors)
    _check_template_mappings(errors)
    _check_no_retired_refs(errors)
    return errors


def main() -> int:
    errors = validate()

    if errors:
        print("Seminar prompt-suite reference validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Seminar prompt-suite reference validation passed.")
    print(f"required_prompt_files={len(REQUIRED_PROMPT_FILES)}")
    print(f"retired_template_files={len(RETIRED_TEMPLATE_FILES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
