"""Linear Phase 4 module pipeline.

This module intentionally implements a one-way build path: plan validation,
research packet assembly, prompt rendering, writer invocation, deterministic
Python QG, independent LLM QG aggregation, and MDX assembly. It does not expose
any LLM rewrite or regeneration loop.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.build.prompt_builder import DOWNSTREAM_TOKENS, TOKEN_RE, render_prompt
from scripts.common.thresholds import QG_DIMS, aggregate_review
from scripts.config import get_immersion_policy, get_immersion_range, get_immersion_rule
from scripts.generate_mdx.core import generate_mdx

PLAN_REQUIRED_KEYS = {
    "module",
    "level",
    "sequence",
    "slug",
    "title",
    "subtitle",
    "content_outline",
    "word_target",
    "references",
}

WRITER_CHOICES = ("claude-tools", "gemini-tools")
WRITER_DEFAULTS: dict[str, dict[str, str]] = {
    "claude-tools": {"model": "claude-opus-4-7", "effort": "xhigh"},
    "gemini-tools": {"model": "gemini-3.1-pro-preview", "effort": "high"},
}
WRITER_ARTIFACTS = (
    "module.md",
    "activities.yaml",
    "vocabulary.yaml",
    "resources.yaml",
)


@dataclass(frozen=True, slots=True)
class JsonArtifactSchema:
    """Minimal runtime schema for writer JSON artifacts.

    Two extra-key policies are supported via `optional_item_fields`:

    - Tight schemas (vocabulary, resources): list every legitimate field in
      `required_item_fields` + `optional_item_fields`. Any other key is
      treated as a hallucinated field and rejected — without this, a writer
      that emits `{"lemma": ..., "translation": ..., "kek": "..."}` would
      silently leak `kek` into the artifact.
    - Polymorphic schemas (activities): the per-type schema (fields used by
      `fill-in` vs `quiz` vs `error-correction` etc.) is enforced later by
      `_component_prop_gate` against `docs/lesson-schema.yaml`. The parser-
      level schema here lists only the fields common to all activity types
      and leaves `optional_item_fields` permissive enough to accept any of
      the known per-type fields, so type-specific keys aren't mis-flagged
      as hallucinated.
    """

    root_type: type
    required_item_fields: Mapping[str, type]
    optional_item_fields: frozenset[str] = frozenset()


# Single source of truth for which artifacts use strict JSON: the keys of
# this map. `WRITER_JSON_ARTIFACTS` (a tuple of those keys, used downstream
# in `parse_writer_output_strict_json`) is derived below to keep the two
# constants from drifting out of sync.
WRITER_JSON_SCHEMAS: dict[str, JsonArtifactSchema] = {
    "activities.yaml": JsonArtifactSchema(
        root_type=list,
        required_item_fields={
            "id": str,
            "type": str,
        },
        # Polymorphic — per-activity-type fields enforced by
        # `_component_prop_gate` against `docs/lesson-schema.yaml`. This
        # set lists fields known to appear in some activity type so the
        # strict-extra-keys gate doesn't misfire on legitimate per-type
        # content. New activity types may need additions here.
        optional_item_fields=frozenset({
            "title",
            "instruction",
            "items",
            "passage",
            "sentences",
            "questions",
            "options",
            "pairs",
            "prompt",
            "answer",
            "statement",
            "question",
            "isCorrect",
            "correctAnswer",
            "correct_order",
            "source",
            "target",
            "sentence",
            "translation",
            "error",
            "correction",
            "note",
            "hints",
            "tags",
        }),
    ),
    "vocabulary.yaml": JsonArtifactSchema(
        root_type=list,
        required_item_fields={
            "lemma": str,
            "translation": str,
            "pos": str,
            "usage": str,
        },
        optional_item_fields=frozenset({"notes", "examples", "tags"}),
    ),
    "resources.yaml": JsonArtifactSchema(
        root_type=list,
        required_item_fields={
            "title": str,
        },
        optional_item_fields=frozenset({
            "notes",
            "source_ref",
            "packet_chunk_id",
            "url",
            "section",
            "page",
        }),
    ),
}
WRITER_JSON_ARTIFACTS: tuple[str, ...] = tuple(WRITER_JSON_SCHEMAS)

QUALITY_FIELD_PATTERNS: dict[str, tuple[str, ...]] = {
    "russianisms_clean": (
        r"\bпожалуйста\b",
        r"\bспасибо\b",
        r"\bхорошо\b",
        r"\bконечно\b",
        r"\bничего\b",
        r"\bсейчас\b",
        r"\bтоже\b",
        r"\bздесь\b",
        r"\bкот\b",
        r"\bкон\b",
        r"[ыэёъЫЭЁЪ]",
    ),
    "surzhyk_clean": (
        r"\bшо\b",
        r"\bканєшно\b",
        r"\bсчас\b",
        r"\bнє\b",
    ),
    "calques_clean": (
        r"\bприймати участь\b",
        r"\bна протязі\b",
        r"\bпо крайній мірі\b",
    ),
    "paronym_clean": (
        r"\bвідноситися до\b",
        r"\bрахувати що\b",
    ),
}

_WORD_RE = re.compile(r"[A-Za-zА-ЯІЇЄҐа-яіїєґ][A-Za-zА-ЯІЇЄҐа-яіїєґ'ʼ-]*")
_UK_WORD_RE = re.compile(r"[А-ЯІЇЄҐа-яіїєґ][А-ЯІЇЄҐа-яіїєґ'ʼ-]*")
_INJECT_RE = re.compile(r"<!--\s*INJECT_ACTIVITY:\s*([A-Za-z0-9_-]+)\s*-->")
_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


class LinearPipelineError(RuntimeError):
    """Raised when a linear pipeline stage fails fast."""


def load_yaml(path: Path) -> Any:
    """Load a YAML file and reject empty documents."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        raise LinearPipelineError(f"YAML file is empty: {path}")
    return data


def plan_path_for(level: str, slug: str) -> Path:
    return PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / level / f"{slug}.yaml"


def load_plan(plan_path: Path) -> dict[str, Any]:
    data = load_yaml(plan_path)
    if not isinstance(data, dict):
        raise LinearPipelineError(f"Plan must be a mapping: {plan_path}")
    return data


def validate_plan(plan: Mapping[str, Any]) -> None:
    """Validate the plan shape needed by the Phase 4 linear pipeline."""
    missing = sorted(PLAN_REQUIRED_KEYS - set(plan))
    if missing:
        raise LinearPipelineError(f"Plan missing required keys: {', '.join(missing)}")

    if not isinstance(plan["sequence"], int) or plan["sequence"] <= 0:
        raise LinearPipelineError("Plan sequence must be a positive integer")
    if not isinstance(plan["word_target"], int) or plan["word_target"] <= 0:
        raise LinearPipelineError("Plan word_target must be a positive integer")

    sections = plan["content_outline"]
    if not isinstance(sections, list) or not sections:
        raise LinearPipelineError("Plan content_outline must be a non-empty list")
    for index, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            raise LinearPipelineError(f"Plan section {index} must be a mapping")
        if not isinstance(section.get("section"), str) or not section["section"].strip():
            raise LinearPipelineError(f"Plan section {index} missing section title")
        if not isinstance(section.get("words"), int) or section["words"] <= 0:
            raise LinearPipelineError(f"Plan section {section['section']!r} has invalid words")
        points = section.get("points")
        if not isinstance(points, list) or not all(isinstance(p, str) for p in points):
            raise LinearPipelineError(
                f"Plan section {section['section']!r} must have string points"
            )

    references = plan["references"]
    if not isinstance(references, list) or not references:
        raise LinearPipelineError("Plan references must be a non-empty list")
    for ref in references:
        if not isinstance(ref, dict) or not ref.get("title"):
            raise LinearPipelineError("Every plan reference must include a title")


def plan_check(plan_path: Path) -> dict[str, Any]:
    plan = load_plan(plan_path)
    validate_plan(plan)
    return plan


def build_knowledge_packet(plan_path: Path) -> str:
    """Retrieve the writer research packet using the existing RAG packet builder."""
    from scripts.build.research.build_knowledge_packet import build_packet

    return build_packet(plan_path)


def render_phase_prompt(template_path: Path, context: Mapping[str, Any]) -> str:
    """Render Phase 0 preamble placeholders and downstream ALL_CAPS tokens."""
    unknown = sorted(set(context) - DOWNSTREAM_TOKENS)
    if unknown:
        raise LinearPipelineError(
            "Unknown downstream prompt context keys: " + ", ".join(unknown)
        )

    rendered = render_prompt(template_path)
    for key, value in context.items():
        rendered = rendered.replace(f"{{{key}}}", str(value))

    unresolved = sorted(
        {
            match.group(1)
            for match in TOKEN_RE.finditer(rendered)
            if match.group(1) in DOWNSTREAM_TOKENS
        }
    )
    if unresolved:
        raise LinearPipelineError(
            f"Unresolved downstream prompt tokens in {template_path}: "
            + ", ".join(unresolved)
        )
    return rendered


def writer_context(plan: Mapping[str, Any], plan_content: str, knowledge_packet: str) -> dict[str, str]:
    level = str(plan["level"])
    sequence = int(plan["sequence"])
    activity_config = _activity_config(level, sequence, str(plan["slug"]))
    return {
        "LEVEL": level,
        "MODULE_NUM": str(sequence),
        "MODULE_SLUG": str(plan["slug"]),
        "TOPIC_TITLE": str(plan["title"]),
        "PHASE": str(plan.get("phase", "")),
        "WORD_TARGET": str(plan["word_target"]),
        "PLAN_CONTENT": plan_content,
        "KNOWLEDGE_PACKET": knowledge_packet,
        "IMMERSION_RULE": get_immersion_rule(level.lower(), sequence),
        "CONTRACT_YAML": _contract_yaml(plan),
        "ALLOWED_ACTIVITY_TYPES": activity_config["ALLOWED_ACTIVITY_TYPES"],
        "FORBIDDEN_ACTIVITY_TYPES": activity_config["FORBIDDEN_ACTIVITY_TYPES"],
        "INLINE_ALLOWED_TYPES": activity_config["INLINE_ALLOWED_TYPES"],
        "WORKBOOK_ALLOWED_TYPES": activity_config["WORKBOOK_ALLOWED_TYPES"],
        "ACTIVITY_COUNT_TARGET": activity_config["ACTIVITY_COUNT_TARGET"],
        "VOCAB_COUNT_TARGET": activity_config["VOCAB_COUNT_TARGET"],
    }


def invoke_writer(
    prompt: str,
    writer: str,
    *,
    cwd: Path = PROJECT_ROOT,
    invoker: Callable[..., Any] | None = None,
) -> str:
    """Call the selected writer through the universal agent runtime."""
    if writer not in WRITER_CHOICES:
        raise LinearPipelineError(
            f"Unknown writer {writer!r}; expected one of {WRITER_CHOICES}"
        )
    if invoker is None:
        from scripts.agent_runtime.runner import invoke as invoker

    defaults = WRITER_DEFAULTS[writer]
    agent_name = writer.split("-", 1)[0]
    result = invoker(
        agent_name,
        prompt,
        mode="workspace-write",
        cwd=cwd,
        model=defaults["model"],
        task_id="phase-4-a1-20-writer",
        entrypoint="dispatch",
        effort=defaults["effort"],
        tool_config={"output_format": "text"},
    )
    response = getattr(result, "response", None)
    if not response:
        raise LinearPipelineError("Writer call returned no response")
    return str(response)


def parse_writer_output_strict_json(output: str) -> dict[str, str]:
    """Parse writer output with strict JSON for structured artifacts.

    The structured JSON values are serialized back to YAML strings so downstream
    storage and MDX assembly keep the existing artifact file contracts.
    """
    artifacts: dict[str, str] = {}
    pending_name: str | None = None
    in_fence = False
    fence_name: str | None = None
    fence_lang: str | None = None
    fence_start_line = 0
    fence_lines: list[str] = []

    for line_no, line in enumerate(output.splitlines(), start=1):
        fence_match = re.match(r"^\s*```(?P<info>.*)$", line)
        if fence_match:
            if not in_fence:
                info = fence_match.group("info").strip()
                info_name = _artifact_name_from_text(info)
                # Detect label-vs-fence-name mismatches. If a preceding label
                # line said "activities.yaml" but the fence info string says
                # "file=vocabulary.yaml", silently picking one would land
                # content under the wrong artifact and produce a confusing
                # downstream "missing artifact" error. Fail loud instead.
                if info_name and pending_name and info_name != pending_name:
                    raise LinearPipelineError(
                        f"Writer output has mismatched artifact label and "
                        f"fence name at line {line_no}: label={pending_name!r} "
                        f"but fence info has {info_name!r}"
                    )
                fence_name = info_name or pending_name
                fence_lang = _fence_language(info)
                fence_start_line = line_no
                if fence_name is None:
                    raise LinearPipelineError(
                        f"Writer output contains unnamed fenced block at line {line_no}"
                    )
                if fence_name in artifacts:
                    raise LinearPipelineError(
                        f"Writer output contains duplicate artifact block: {fence_name}"
                    )
                if fence_name in WRITER_JSON_ARTIFACTS and fence_lang != "json":
                    got = fence_lang or "<none>"
                    raise LinearPipelineError(
                        f"{fence_name} must be fenced as json, got {got} "
                        f"at line {line_no}"
                    )
                in_fence = True
                fence_lines = []
                continue

            if fence_name == "module.md":
                artifacts[fence_name] = "\n".join(fence_lines).strip() + "\n"
            elif fence_name in WRITER_JSON_ARTIFACTS:
                artifacts[fence_name] = _parse_and_dump_writer_json_artifact(
                    fence_name,
                    "\n".join(fence_lines),
                    fence_start_line + 1,
                )
            in_fence = False
            fence_name = None
            fence_lang = None
            pending_name = None
            fence_start_line = 0
            fence_lines = []
            continue

        if in_fence:
            fence_lines.append(line)
            continue

        name = _artifact_name_from_text(line)
        if name in WRITER_ARTIFACTS:
            pending_name = name

    if in_fence:
        raise LinearPipelineError(
            f"Writer output has an unterminated fenced block for {fence_name}"
        )

    missing = [name for name in WRITER_ARTIFACTS if name not in artifacts]
    extra = sorted(set(artifacts) - set(WRITER_ARTIFACTS))
    if missing or extra:
        raise LinearPipelineError(
            f"Writer output must contain exactly {WRITER_ARTIFACTS}. "
            f"missing={missing} extra={extra}"
        )
    return {name: artifacts[name] for name in WRITER_ARTIFACTS}


def parse_writer_output(output: str) -> dict[str, str]:
    """Compatibility wrapper for the strict JSON writer-output parser."""
    return parse_writer_output_strict_json(output)


def write_writer_artifacts(module_dir: Path, artifacts: Mapping[str, str]) -> None:
    """Write parsed writer artifacts after validating their basic shapes."""
    missing = [name for name in WRITER_ARTIFACTS if name not in artifacts]
    if missing:
        raise LinearPipelineError(f"Missing writer artifacts: {', '.join(missing)}")

    module_text = str(artifacts["module.md"])
    if not module_text.strip():
        raise LinearPipelineError("module.md artifact is empty")

    for name in ("activities.yaml", "vocabulary.yaml", "resources.yaml"):
        parsed = yaml.safe_load(str(artifacts[name]))
        if not isinstance(parsed, list):
            raise LinearPipelineError(f"{name} must be a bare YAML list")
        if not all(isinstance(item, dict) for item in parsed):
            raise LinearPipelineError(f"{name} entries must be mappings")

    module_dir.mkdir(parents=True, exist_ok=True)
    for name in WRITER_ARTIFACTS:
        (module_dir / name).write_text(str(artifacts[name]), encoding="utf-8")


def review_context(
    plan: Mapping[str, Any],
    plan_content: str,
    generated_content: str,
    dim: str,
) -> dict[str, str]:
    """Build context for one independent per-dimension LLM QG prompt."""
    if dim not in QG_DIMS:
        raise LinearPipelineError(f"Unknown LLM QG dimension: {dim}")
    level = str(plan["level"])
    sequence = int(plan["sequence"])
    return {
        "LEVEL": level,
        "MODULE_NUM": str(sequence),
        "MODULE_SLUG": str(plan["slug"]),
        "WORD_TARGET": str(plan["word_target"]),
        "IMMERSION_RULE": get_immersion_rule(level.lower(), sequence),
        "CONTRACT_YAML": _contract_yaml(plan),
        "PLAN_CONTENT": plan_content,
        "GENERATED_CONTENT": generated_content,
        "DIM": dim,
    }


def render_review_prompt(
    plan: Mapping[str, Any],
    plan_content: str,
    generated_content: str,
    dim: str,
) -> str:
    return render_phase_prompt(
        PROJECT_ROOT / "scripts" / "build" / "phases" / "linear-review-dim.md",
        review_context(plan, plan_content, generated_content, dim),
    )


def parse_review_response(response: str, dim: str) -> dict[str, Any]:
    """Parse and validate one per-dim LLM QG response."""
    if dim not in QG_DIMS:
        raise LinearPipelineError(f"Unknown LLM QG dimension: {dim}")

    payload = _parse_json_or_yaml_mapping(response)
    if dim in payload and isinstance(payload[dim], Mapping):
        payload = dict(payload[dim])

    try:
        score = float(payload["score"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LinearPipelineError(f"LLM QG response for {dim} has invalid score") from exc

    evidence = payload.get("evidence")
    verdict = str(payload.get("verdict", "")).upper()
    entry = {
        "score": score,
        "evidence": evidence,
        "verdict": verdict,
    }
    validate_llm_review_report({**_placeholder_review_report(), dim: entry})
    if verdict not in {"PASS", "REVISE", "REJECT"}:
        raise LinearPipelineError(f"LLM QG response for {dim} has invalid verdict")
    return entry


def validate_llm_review_report(report: Mapping[str, Any]) -> None:
    """Validate per-dim LLM QG reports before aggregation."""
    dims = set(QG_DIMS)
    actual = set(report)
    if actual != dims:
        missing = sorted(dims - actual)
        extra = sorted(actual - dims)
        raise LinearPipelineError(
            f"LLM QG dims must be exactly QG_DIMS. missing={missing} extra={extra}"
        )

    for dim in QG_DIMS:
        entry = report[dim]
        if not isinstance(entry, Mapping):
            raise LinearPipelineError(f"LLM QG entry for {dim} must be a mapping")
        try:
            score = float(entry["score"])
        except (KeyError, TypeError, ValueError) as exc:
            raise LinearPipelineError(f"LLM QG entry for {dim} has invalid score") from exc
        if not 0 <= score <= 10:
            raise LinearPipelineError(f"LLM QG score for {dim} out of range: {score}")
        evidence = entry.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            raise LinearPipelineError(f"LLM QG entry for {dim} missing evidence")
        if not any(q in evidence for q in ('"', "“", "”", "«", "»")):
            raise LinearPipelineError(
                f"LLM QG evidence for {dim} must include a quoted excerpt"
            )
        if not isinstance(entry.get("verdict"), str) or not entry["verdict"].strip():
            raise LinearPipelineError(f"LLM QG entry for {dim} missing verdict")
        if entry["verdict"].upper() not in {"PASS", "REVISE", "REJECT"}:
            raise LinearPipelineError(f"LLM QG entry for {dim} has invalid verdict")


def aggregate_llm_review(report: Mapping[str, Any], level_code: str) -> dict[str, Any]:
    validate_llm_review_report(report)
    scores = {dim: float(report[dim]["score"]) for dim in QG_DIMS}
    verdict = aggregate_review(scores, level_code)
    return {
        "dimensions": {dim: dict(report[dim]) for dim in QG_DIMS},
        "aggregate": asdict(verdict),
    }


def run_python_qg(
    module_dir: Path,
    plan_path: Path,
    *,
    verify_words_fn: Callable[[list[str]], dict[str, list[dict[str, Any]]]] | None = None,
) -> dict[str, Any]:
    """Run deterministic Phase 4 quality gates for one module directory."""
    plan = plan_check(plan_path)
    module_text = _read_required(module_dir / "module.md")
    activities = _load_bare_activity_list(module_dir / "activities.yaml")
    vocabulary = _load_yaml_list(module_dir / "vocabulary.yaml", "vocabulary")
    resources = _load_yaml_list(module_dir / "resources.yaml", "resources")

    text_for_quality = "\n".join(
        [
            module_text,
            yaml.safe_dump(activities, allow_unicode=True, sort_keys=False),
            yaml.safe_dump(vocabulary, allow_unicode=True, sort_keys=False),
            yaml.safe_dump(resources, allow_unicode=True, sort_keys=False),
        ]
    )

    gates: dict[str, Any] = {
        "word_count": _word_count_gate(module_text, int(plan["word_target"])),
        "plan_sections": _section_gate(module_text, plan),
        "vesum_verified": _vesum_gate(text_for_quality, verify_words_fn),
        "citations_resolve": _citation_gate(resources, plan),
        "immersion": _immersion_gate(module_text, plan),
        "inject_activity_ids": _inject_activity_gate(module_text, activities),
        "activity_types": _activity_type_gate(
            activities,
            str(plan["level"]),
            int(plan["sequence"]),
            str(plan["slug"]),
        ),
        "ai_slop_clean": _ai_slop_gate(text_for_quality),
        "component_props": _component_prop_gate(activities),
        "mdx_render": {"passed": None, "message": "Run after publish stage"},
    }
    gates.update(_quality_fields(text_for_quality))
    gates["passed"] = all(
        gate.get("passed") is True
        for key, gate in gates.items()
        if isinstance(gate, dict) and key != "mdx_render"
    )
    return {
        "module": plan["module"],
        "level": plan["level"],
        "slug": plan["slug"],
        "pipeline": "linear-phase-4",
        "gates": gates,
    }


def assemble_mdx(module_dir: Path, output_path: Path, plan_path: Path) -> str:
    """Assemble the 4-tab Starlight MDX file from authoring artifacts."""
    plan = plan_check(plan_path)
    activities_path = module_dir / "activities.yaml"
    vocabulary_path = module_dir / "vocabulary.yaml"
    resources_path = module_dir / "resources.yaml"

    from scripts.yaml_activities import ActivityParser

    activities = ActivityParser().parse(activities_path)
    vocabulary = _load_yaml_list(vocabulary_path, "vocabulary")
    resources_list = _load_yaml_list(resources_path, "resources")
    resources = {"books": resources_list}
    mdx = generate_mdx(
        (module_dir / "module.md").read_text(encoding="utf-8"),
        int(plan["sequence"]),
        yaml_activities=activities,
        meta_data=dict(plan),
        vocab_items=vocabulary,
        external_resources=resources,
        level=str(plan["level"]).lower(),
        pipeline_version="linear-phase-4",
        build_status="draft",
    )
    mdx = mdx.replace("\n{/**/}\n", "\n")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(mdx, encoding="utf-8")
    return mdx


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _artifact_name_from_text(text: str) -> str | None:
    for artifact in WRITER_ARTIFACTS:
        if re.search(rf"(?<![\w.-]){re.escape(artifact)}(?![\w.-])", text):
            return artifact
    return None


def _fence_language(info: str) -> str | None:
    token = info.strip().split(maxsplit=1)[0] if info.strip() else ""
    return token.lower() or None


def _reject_non_strict_json_constant(token: str) -> Any:
    """`json.loads` parse_constant hook that rejects `NaN`/`Infinity`.

    Python's `json.loads` accepts `NaN`, `Infinity`, and `-Infinity` by
    default — RFC 8259 forbids these tokens. Without this hook, those
    values would round-trip through `yaml.safe_dump` as `.nan`/`.inf`,
    leaking non-portable YAML into the artifact files. The strict-JSON
    contract demands fail-fast on any non-conformant token.
    """
    raise ValueError(f"non-strict-JSON token: {token!r} (NaN/Infinity not allowed)")


def _parse_and_dump_writer_json_artifact(
    artifact: str,
    body: str,
    content_start_line: int,
) -> str:
    try:
        parsed = json.loads(body, parse_constant=_reject_non_strict_json_constant)
    except json.JSONDecodeError as exc:
        absolute_line = content_start_line + exc.lineno - 1
        raise LinearPipelineError(
            f"{artifact} invalid JSON: {exc} "
            f"(artifact line {exc.lineno}, absolute line {absolute_line}, "
            f"column {exc.colno})"
        ) from exc
    except ValueError as exc:
        raise LinearPipelineError(f"{artifact} invalid JSON: {exc}") from exc

    _validate_writer_json_artifact(artifact, parsed)
    return yaml.safe_dump(parsed, allow_unicode=True, sort_keys=False)


def _validate_writer_json_artifact(artifact: str, parsed: Any) -> None:
    schema = WRITER_JSON_SCHEMAS[artifact]
    if not isinstance(parsed, schema.root_type):
        raise LinearPipelineError(
            f"{artifact} schema validation failed: root must be "
            f"{schema.root_type.__name__}, got {type(parsed).__name__}"
        )

    # The downstream item-iteration assumes a list. All current schemas
    # specify `root_type=list`; if a future schema uses a different root
    # (e.g. `dict`), this function needs a different iteration strategy.
    assert isinstance(parsed, list), (
        f"validator for {artifact!r} expects list root; "
        f"add per-root-type handling if {schema.root_type.__name__} is added"
    )

    allowed_fields = set(schema.required_item_fields) | schema.optional_item_fields
    for index, item in enumerate(parsed, start=1):
        if not isinstance(item, dict):
            raise LinearPipelineError(
                f"{artifact} schema validation failed: item {index} must be "
                f"object, got {type(item).__name__}"
            )

        # Reject hallucinated fields. Without this, a writer that emits
        # `{"lemma": ..., "translation": ..., "kek": "..."}` for vocabulary
        # would silently leak `kek` into the YAML artifact even though the
        # schema doesn't define it. The error message lists the unexpected
        # keys so the corrective redispatch has actionable context.
        extra_keys = sorted(set(item) - allowed_fields)
        if extra_keys:
            raise LinearPipelineError(
                f"{artifact} schema validation failed: item {index} has "
                f"unexpected fields {extra_keys}; allowed: {sorted(allowed_fields)}"
            )

        for field, expected_type in schema.required_item_fields.items():
            value = item.get(field)
            if not isinstance(value, expected_type):
                raise LinearPipelineError(
                    f"{artifact} schema validation failed: item {index} "
                    f"requires {field} as {expected_type.__name__}, "
                    f"got {type(value).__name__} ({value!r})"
                )
            # String fields must be non-empty after whitespace strip — an
            # empty `id` or `lemma` is meaningless downstream. Reported
            # separately from type errors so the redispatch context is clear.
            if isinstance(value, str) and not value.strip():
                raise LinearPipelineError(
                    f"{artifact} schema validation failed: item {index} "
                    f"requires {field} as a non-empty string (got empty/whitespace)"
                )


def _strip_outer_code_fence(text: str) -> str:
    stripped = text.strip()
    match = re.match(r"^```(?:json|yaml|yml)?\s*\n(?P<body>.*)\n```\s*$", stripped, re.DOTALL)
    if match:
        return match.group("body").strip()
    return stripped


def _parse_json_or_yaml_mapping(text: str) -> dict[str, Any]:
    body = _strip_outer_code_fence(text)
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        parsed = yaml.safe_load(body)
    if not isinstance(parsed, dict):
        raise LinearPipelineError("LLM QG response must be a JSON/YAML mapping")
    return parsed


def _placeholder_review_report() -> dict[str, dict[str, Any]]:
    return {
        dim: {
            "score": 10.0,
            "evidence": '"placeholder"',
            "verdict": "PASS",
        }
        for dim in QG_DIMS
    }


def _activity_config(level: str, module_num: int, slug: str | None = None) -> dict[str, str]:
    from pipeline.config_tables import get_activity_config

    return get_activity_config(level.lower(), module_num, slug)


def _contract_yaml(plan: Mapping[str, Any]) -> str:
    contract = {
        "sections": [
            {
                "title": section["section"],
                "word_budget": {
                    "target": section["words"],
                    "min": int(section["words"] * 0.9),
                    "max": int(section["words"] * 1.1),
                },
                "covers": section.get("points", []),
            }
            for section in plan.get("content_outline", [])
        ],
        "activity_hints": plan.get("activity_hints", []),
        "vocabulary_required": plan.get("vocabulary_hints", {}).get("required", []),
        "references": plan.get("references", []),
    }
    return yaml.safe_dump(contract, allow_unicode=True, sort_keys=False).strip()


def _read_required(path: Path) -> str:
    if not path.exists():
        raise LinearPipelineError(f"Missing required artifact: {path}")
    return path.read_text(encoding="utf-8")


def _load_yaml_list(path: Path, label: str) -> list[dict[str, Any]]:
    data = load_yaml(path)
    if not isinstance(data, list):
        raise LinearPipelineError(f"{label} YAML must be a bare list: {path}")
    if not all(isinstance(item, dict) for item in data):
        raise LinearPipelineError(f"{label} YAML entries must be mappings: {path}")
    return data


def _load_bare_activity_list(path: Path) -> list[dict[str, Any]]:
    data = load_yaml(path)
    if isinstance(data, dict) and "activities" in data:
        raise LinearPipelineError("activities.yaml must be a bare list, not activities:")
    if not isinstance(data, list):
        raise LinearPipelineError("activities.yaml must be a bare list at root")
    if not all(isinstance(item, dict) for item in data):
        raise LinearPipelineError("Every activity must be a mapping")
    return data


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _word_count_gate(text: str, target: int) -> dict[str, Any]:
    count = _word_count(_strip_comments(text))
    return {
        "passed": count >= target,
        "count": count,
        "target": target,
    }


def _section_gate(text: str, plan: Mapping[str, Any]) -> dict[str, Any]:
    headings = {match.group(1).strip() for match in _HEADING_RE.finditer(text)}
    missing = [
        section["section"]
        for section in plan["content_outline"]
        if section["section"] not in headings
    ]
    budgets = []
    for section in plan["content_outline"]:
        title = section["section"]
        target = int(section["words"])
        section_text = _extract_section_text(text, title)
        count = _word_count(_strip_comments(section_text))
        min_words = int(target * 0.9)
        max_words = int(target * 1.1)
        budgets.append({
            "section": title,
            "count": count,
            "min": min_words,
            "max": max_words,
            "passed": min_words <= count <= max_words,
        })
    return {
        "passed": not missing and all(item["passed"] for item in budgets),
        "missing_headings": missing,
        "word_budgets": budgets,
    }


def _extract_section_text(text: str, title: str) -> str:
    match = re.search(rf"^##\s+{re.escape(title)}\s*$", text, flags=re.MULTILINE)
    if not match:
        return ""
    next_heading = re.search(r"^##\s+", text[match.end() :], flags=re.MULTILINE)
    if not next_heading:
        return text[match.end() :]
    return text[match.end() : match.end() + next_heading.start()]


def _vesum_gate(
    text: str,
    verify_words_fn: Callable[[list[str]], dict[str, list[dict[str, Any]]]] | None,
) -> dict[str, Any]:
    from scripts.audit.config import PROPER_NAME_WHITELIST, VESUM_MIN_WORD_LENGTH

    words = sorted(
        {
            word.strip("-'ʼ")
            for word in _UK_WORD_RE.findall(text)
            if len(word.strip("-'ʼ")) >= VESUM_MIN_WORD_LENGTH
        }
    )
    unchecked = [word for word in words if word not in PROPER_NAME_WHITELIST]
    if verify_words_fn is None:
        from scripts.rag.query import verify_words as verify_words_fn

    try:
        verified = verify_words_fn(unchecked)
    except Exception as exc:
        return {"passed": False, "error": str(exc), "checked": len(unchecked)}

    missing = sorted(word for word, matches in verified.items() if not matches)
    return {
        "passed": not missing,
        "checked": len(unchecked),
        "whitelisted": len(words) - len(unchecked),
        "missing": missing[:100],
        "missing_count": len(missing),
    }


def _quality_fields(text: str) -> dict[str, dict[str, Any]]:
    lower = text.lower()
    results = {}
    for field, patterns in QUALITY_FIELD_PATTERNS.items():
        hits = sorted({pattern for pattern in patterns if re.search(pattern, lower)})
        results[field] = {"passed": not hits, "hits": hits}
    return results


def _citation_gate(resources: list[dict[str, Any]], plan: Mapping[str, Any]) -> dict[str, Any]:
    plan_titles = {str(ref["title"]) for ref in plan.get("references", [])}
    unknown = []
    for resource in resources:
        source_ref = str(resource.get("source_ref") or resource.get("title") or "")
        if source_ref not in plan_titles and resource.get("packet_chunk_id") is None:
            unknown.append(source_ref)
    return {"passed": not unknown, "unknown": unknown}


def _immersion_gate(text: str, plan: Mapping[str, Any]) -> dict[str, Any]:
    level = str(plan["level"]).lower()
    sequence = int(plan["sequence"])
    min_pct, max_pct = get_immersion_range(level, sequence)
    body = _strip_frontmatter_and_headings(_strip_comments(text))
    tokens = _WORD_RE.findall(body)
    uk_tokens = [token for token in tokens if _UK_WORD_RE.search(token)]
    pct = round((len(uk_tokens) / len(tokens) * 100), 2) if tokens else 0.0
    long_sentences = [
        sentence.strip()
        for sentence in re.split(r"[.!?]\s+", body)
        if len(_UK_WORD_RE.findall(sentence)) > 10
    ]
    return {
        "passed": min_pct <= pct <= max_pct and not long_sentences,
        "pct": pct,
        "min_pct": min_pct,
        "max_pct": max_pct,
        "policy": get_immersion_policy(level, sequence)["key"],
        "long_ukrainian_sentences": long_sentences[:20],
    }


def _inject_activity_gate(text: str, activities: list[dict[str, Any]]) -> dict[str, Any]:
    ids = {str(activity.get("id")) for activity in activities if activity.get("id")}
    injected = _INJECT_RE.findall(text)
    missing = [activity_id for activity_id in injected if activity_id not in ids]
    unused = sorted(ids - set(injected))
    return {
        "passed": not missing,
        "injected": injected,
        "missing": missing,
        "unused": unused,
    }


def _activity_type_gate(
    activities: list[dict[str, Any]],
    level: str,
    module_num: int,
    slug: str | None = None,
) -> dict[str, Any]:
    config = _activity_config(level, module_num, slug)
    allowed = {item.strip() for item in config["ALLOWED_ACTIVITY_TYPES"].split(",")}
    forbidden = {item.strip() for item in config["FORBIDDEN_ACTIVITY_TYPES"].split(",")}
    types = [str(activity.get("type")) for activity in activities]
    disallowed = sorted({activity_type for activity_type in types if activity_type not in allowed})
    forbidden_hits = sorted({activity_type for activity_type in types if activity_type in forbidden})
    return {
        "passed": not disallowed and not forbidden_hits,
        "types": types,
        "disallowed": disallowed,
        "forbidden": forbidden_hits,
    }


def _ai_slop_gate(text: str) -> dict[str, Any]:
    from scripts.audit.config import AI_CONTAMINATION_PATTERNS

    hits = sorted(
        {
            pattern
            for pattern in AI_CONTAMINATION_PATTERNS
            if re.search(pattern, text, flags=re.IGNORECASE)
        }
    )
    return {"passed": not hits, "hits": hits}


def _component_prop_gate(activities: list[dict[str, Any]]) -> dict[str, Any]:
    schema = load_yaml(PROJECT_ROOT / "docs" / "lesson-schema.yaml")
    components = schema.get("components", {})
    by_type = {
        data.get("activity_type"): data
        for data in components.values()
        if isinstance(data, dict) and data.get("activity_type")
    }
    errors = []
    for activity in activities:
        activity_type = activity.get("type")
        component = by_type.get(activity_type)
        if component is None:
            errors.append(f"{activity.get('id', '<missing-id>')}: unknown activity type {activity_type}")
            continue
        required = [
            prop["name"]
            for prop in component.get("props", {}).get("required", [])
            if isinstance(prop, dict)
        ]
        missing = [prop for prop in required if prop not in activity]
        if missing:
            errors.append(
                f"{activity.get('id', '<missing-id>')}: missing required props "
                + ", ".join(missing)
            )
    return {"passed": not errors, "errors": errors}


def _strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _strip_frontmatter_and_headings(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end >= 0:
            text = text[end + 4 :]
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )
