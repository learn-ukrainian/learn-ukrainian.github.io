"""LLM reviewer prompt + evaluator layer.

Performs deterministic structural checks (like model answers in B2+) and
evaluates naturalness, register, and grammar using LLM review prompts.
Conforms to the canonical schema version ua_contact_quality_evidence.v1.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

from scripts.audit import qg_schema

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
DEFAULT_PROMPT_PATH = PROMPTS_DIR / "reviewer_prompt.md"


def load_reviewer_prompt_template(path: Path | None = None) -> str:
    """Load the LLM reviewer prompt template from disk."""
    resolved_path = path or DEFAULT_PROMPT_PATH
    if not resolved_path.exists():
        raise FileNotFoundError(f"Reviewer prompt template not found at {resolved_path}")
    return resolved_path.read_text(encoding="utf-8")


def build_reviewer_prompt(
    level: str,
    slug: str,
    module_md: str,
    activities_yaml: str = "",
    vocabulary_yaml: str = "",
    resources_yaml: str = "",
    template_path: Path | None = None,
) -> str:
    """Assemble the complete prompt for the LLM reviewer."""
    template = load_reviewer_prompt_template(template_path)

    # We construct a detailed user prompt with context and module content
    content_block = f"""## Module Metadata
Level: {level}
Slug: {slug}

## File: module.md
```markdown
{module_md}
```
"""
    if activities_yaml.strip():
        content_block += f"\n## File: activities.yaml\n```yaml\n{activities_yaml}\n```\n"
    if vocabulary_yaml.strip():
        content_block += f"\n## File: vocabulary.yaml\n```yaml\n{vocabulary_yaml}\n```\n"
    if resources_yaml.strip():
        content_block += f"\n## File: resources.yaml\n```yaml\n{resources_yaml}\n```\n"

    # Format user prompt with context and instructions
    prompt = f"""{template}

---

## Target Module Content to Review:
{content_block}
"""
    return prompt


def run_structural_checks(
    level: str,
    activities_yaml: str,
    file_name: str = "activities.yaml",
) -> list[dict[str, Any]]:
    """Perform deterministic structural checks, e.g., missing model answers for B2+/C1/C2 productive tasks."""
    findings: list[dict[str, Any]] = []
    level_lower = level.strip().lower()

    # Structural check applies to levels starting with b2, c1, c2 (e.g. b2, c1, c2, c1-bio)
    if not level_lower.startswith(("b2", "c1", "c2")):
        return findings

    if not activities_yaml.strip():
        return findings

    try:
        activities = yaml.safe_load(activities_yaml)
    except Exception:
        # If YAML is malformed, let the syntax checkers handle it
        return findings

    if not isinstance(activities, list):
        return findings

    for activity in activities:
        if not isinstance(activity, dict):
            continue

        act_type = activity.get("type")
        # Production/productive tasks are typically essay-response
        if act_type == "essay-response":
            model_answer = activity.get("model_answer")
            act_id = activity.get("id", "unknown")

            # Find the line of the activity for locator accuracy
            line_no = 1
            lines = activities_yaml.splitlines()
            for idx, line in enumerate(lines, 1):
                if f"id: {act_id}" in line or f"id: '{act_id}'" in line or f'id: "{act_id}"' in line:
                    line_no = idx
                    break

            span_start = activities_yaml.find(f"id: {act_id}")
            if span_start == -1:
                span_start = activities_yaml.find(act_id)
            span_end = span_start + len(act_id) if span_start != -1 else None
            span = {"start": span_start if span_start != -1 else None, "end": span_end}

            excerpt = f"id: {act_id}"

            is_missing = False
            if model_answer is None or not isinstance(model_answer, str) or "> [!model-answer]" not in model_answer:
                is_missing = True

            if is_missing:
                findings.append(
                    qg_schema.build_finding(
                        issue_id="MISSING_MODEL_ANSWER",
                        issue_class="pedagogy",
                        dimension="pedagogical",
                        severity="critical",
                        file=file_name,
                        line=line_no,
                        span=span,
                        excerpt=excerpt,
                        message=(
                            f"Productive activity '{act_id}' at level '{level}' is missing the "
                            "mandatory model answer block starting with '> [!model-answer]'."
                        ),
                        confidence="deterministic",
                        disposition="defect",
                        detector={
                            "adapter": "llm_reviewer_structural",
                            "rule_id": "missing_model_answer",
                        },
                        attribution={
                            "corpus": "curriculum_structure_rules",
                            "evidence": "Mandatory model-answer block for B2+/C1/C2",
                        }
                    )
                )

    return findings


def locate_excerpt(text: str, excerpt: str) -> tuple[int | None, dict[str, int | None]]:
    """Helper to locate line number and span of an excerpt in text."""
    if not excerpt:
        return None, {"start": None, "end": None}

    start = text.find(excerpt)
    if start == -1:
        return None, {"start": None, "end": None}

    line = text.count("\n", 0, start) + 1
    return line, {"start": start, "end": start + len(excerpt)}


def parse_and_evaluate_llm_response(
    response_text: str,
    module_md: str,
    activities_yaml: str = "",
    vocabulary_yaml: str = "",
    resources_yaml: str = "",
    *,
    return_payload: bool = False,
) -> list[dict[str, Any]] | dict[str, Any]:
    """Parse JSON response from the LLM and map findings to qg_schema."""
    findings: list[dict[str, Any]] = []

    try:
        # Simple extraction of JSON from raw response text in case it has markdown wrappers
        data = _json_payload_from_response(response_text)
    except Exception as e:
        # Return a parsing defect finding if JSON parsing completely fails
        parse_findings = [
            qg_schema.build_finding(
                issue_id="LLM_RESPONSE_PARSE_FAILURE",
                issue_class="other",
                dimension="mechanics",
                severity="critical",
                file="llm_response",
                line=None,
                span=None,
                excerpt="JSON parsing failed",
                message=f"Failed to parse JSON from LLM reviewer response: {e}",
                confidence="llm_judgment",
                detector={
                    "adapter": "llm_reviewer_parser",
                    "rule_id": "json_parse_error",
                }
            )
        ]
        if return_payload:
            return {"findings": parse_findings, "fact_checks": [], "evidence_gaps": []}
        return parse_findings

    raw_findings = data.get("findings", [])
    if not isinstance(raw_findings, list):
        payload = {"findings": findings, "fact_checks": [], "evidence_gaps": []}
        return payload if return_payload else findings

    for item in raw_findings:
        if not isinstance(item, dict):
            continue

        issue_id = item.get("issue_id", "UNKNOWN_ISSUE")
        issue_class = item.get("issue_class", "other")
        dimension = item.get("dimension", "naturalness")
        severity = item.get("severity", "warning")
        excerpt = item.get("excerpt", "").strip()
        message = item.get("message", "No message provided.")
        suggested_replacement = item.get("suggested_replacement")
        grounding = item.get("grounding") if isinstance(item.get("grounding"), dict) else None

        # Decide which file this excerpt lives in
        file_name = "module.md"
        file_text = module_md

        if excerpt:
            if excerpt in module_md:
                file_name = "module.md"
                file_text = module_md
            elif activities_yaml and excerpt in activities_yaml:
                file_name = "activities.yaml"
                file_text = activities_yaml
            elif vocabulary_yaml and excerpt in vocabulary_yaml:
                file_name = "vocabulary.yaml"
                file_text = vocabulary_yaml
            elif resources_yaml and excerpt in resources_yaml:
                file_name = "resources.yaml"
                file_text = resources_yaml

        line_no, span = locate_excerpt(file_text, excerpt)

        findings.append(
            qg_schema.build_finding(
                issue_id=issue_id,
                issue_class=issue_class,
                dimension=dimension,
                severity=severity,
                file=file_name,
                line=line_no,
                span=span,
                excerpt=excerpt or "unknown excerpt",
                message=message,
                confidence="llm_judgment",
                disposition="defect",
                suggested_replacement=suggested_replacement,
                grounding=grounding,
                detector={
                    "adapter": "llm_reviewer_evaluator",
                    "rule_id": f"llm_{issue_id.lower()}",
                },
                attribution={
                    "corpus": "curriculum_review",
                    "evidence": "LLM reviewer judgment",
                }
            )
        )

    payload = {
        "findings": findings,
        "fact_checks": _list_of_mappings(data.get("fact_checks")),
        "evidence_gaps": _list_of_mappings(data.get("evidence_gaps")),
    }
    return payload if return_payload else findings


def validate_reviewer_payload(payload: Mapping[str, Any], policy_family: str | None) -> None:
    """Validate a parsed reviewer payload before persistence or cache reuse."""
    qg_schema.validate_reviewer_payload(payload, policy_family)


def _json_payload_from_response(response_text: str) -> Mapping[str, Any]:
    clean_text = response_text.strip()
    if "```json" in clean_text:
        clean_text = clean_text.split("```json")[1].split("```")[0].strip()
    elif "```" in clean_text:
        clean_text = clean_text.split("```")[1].split("```")[0].strip()
    data = json.loads(clean_text)
    if not isinstance(data, Mapping):
        raise ValueError("reviewer response JSON must be an object")
    return data


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]
