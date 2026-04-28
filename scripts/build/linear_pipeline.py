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

    Two extra-key policies are supported:

    - Tight schemas (vocabulary, resources): list every legitimate field in
      `required_item_fields` + `optional_item_fields`. Any other key is
      treated as a hallucinated field and rejected — without this, a writer
      that emits `{"lemma": ..., "translation": ..., "kek": "..."}` would
      silently leak `kek` into the artifact.
    - Polymorphic schemas (activities): set `per_type_extras_authoring=True`.
      The allowed extra fields for each item are looked up by the item's
      `type` discriminator in `_ACTIVITY_AUTHORING_FIELDS` (the
      WRITER-FACING YAML wire format, *not* the React component prop
      schema). `optional_item_fields` is unused in this mode.

      The split matters because adapter-style activities rename fields
      between authoring YAML and component props in `_*_to_mdx`
      (`scripts/yaml_activities.py`). For example: `quiz: {items: [...]}`
      is the authoring shape, but `<Quiz questions=...>` is the component
      shape — sourcing the writer-extras gate from `docs/lesson-schema.yaml`
      (the component side, as #1624 first attempted) would mis-flag the
      canonical authoring shape and silently accept the
      empty-quiz-causing component-prop name. See PR #1627 Codex review.
    """

    root_type: type
    required_item_fields: Mapping[str, type]
    optional_item_fields: frozenset[str] = frozenset()
    per_type_extras_authoring: bool = False


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
        # Polymorphic — per-activity-type allowed fields come from the
        # authoring-shape map `_ACTIVITY_AUTHORING_FIELDS`, *not* the
        # component-prop schema in `docs/lesson-schema.yaml`. The two
        # diverge for adapter-style activities (e.g. `quiz: {items: ...}`
        # authoring vs `<Quiz questions=...>` component prop). See
        # `_validate_writer_json_artifact` and PR #1627.
        per_type_extras_authoring=True,
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

# Metalinguistic content that must be stripped before VESUM lookup:
# phonetic transcriptions like [с':а] and inline code in backticks contain
# fragments of words and IPA-ish notation, not whole VESUM-checkable lemmas.
_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")

# Phonetic-style brackets like `[с':а]`. The negative lookahead `(?!\()`
# protects Markdown link syntax `[text](url)` — Markdown link text is
# followed by `(`, phonetic transcriptions are not. Without this, link text
# would be stripped and any misspellings inside `[слово](url)` would be
# hidden from VESUM.
_BRACKETS_RE = re.compile(r"\[[^\]\n]*\](?!\()")

# Fill-in blank syntax: passages like `Я вмиваю{ся}. Ти одягаєш{ться}.` mark
# the blank students fill in. Restricted to Ukrainian-letter-only content so
# we don't accidentally strip JSX object literals like
# `{ speaker: "Ліна", text: "Коли ти прокидаєшся?" }` (which would hide
# misspellings in dialogue text from VESUM).
_BRACES_RE = re.compile(r"\{[А-ЯІЇЄҐа-яіїєґ'ʼ]{1,12}\}")

# Hyphen-prefixed morpheme notation: `-ться`, `-шся`, `-юся` — the conjugation
# ending labels Ukrainian grammar texts use when discussing suffixes. The
# explicit lookbehind requires the char before `-` to NOT be a Ukrainian or
# Latin letter or digit — i.e., the hyphen must sit at a non-linguistic
# boundary (markdown `*`/`_`, paren, whitespace, line start). This protects
# legitimate hyphenated compounds like `темно-синій` (preceded by `о`) while
# stripping morpheme labels in `**-шся**` and `__-шся__` (markdown bold). We
# don't use Python's `\B` because `_` is a word character there, which would
# make `__-шся__` un-strippable.
_MORPHEME_FRAGMENT_RE = re.compile(
    r"(?<![А-ЯІЇЄҐа-яіїєґ'ʼA-Za-z0-9])-[А-ЯІЇЄҐа-яіїєґ][А-ЯІЇЄҐа-яіїєґ'ʼ]*"
)

# JSX self-closing or paired component blocks. Treated as one structural unit
# in `_immersion_gate`'s long-sentence detection so prop arrays like
# `<DialogueBox lines={[{text: "..."}]}/>` aren't read as a single 50-word
# Ukrainian sentence. The inner-content alternation `[^<]|<(?![A-Z/])` allows
# `>` inside props (`condition={count > 0}`) but stops at any nested
# capitalized JSX tag.
#
# Known limits — regex cannot fully parse JSX:
#   1. Nested same-name components (`<Box><Box/></Box>`) leave a residual
#      outer wrapper; the inner self-close eats the rest.
#   2. Literal `<Capital>` inside a string prop (`text="Press <Enter>"`) or
#      JSX comments (`{/* <X/> */}`) abort the non-greedy match early.
# These are documented and tested as known shortcomings. A proper JSX
# tokenizer would replace this regex; for the QG gate's purpose (avoiding
# false-positive long-sentence flags) the regex catches the dominant case
# (single-component dialogue/exercise blocks).
_JSX_BLOCK_RE = re.compile(
    r"<[A-Z][A-Za-z0-9]*(?:[^<]|<(?![A-Z/]))*?(?:/>|</[A-Z][A-Za-z0-9]*>)",
    re.DOTALL,
)

# Capture the Ukrainian-bearing string values from JSX prop expressions
# (`text: "..."`, `text="..."`). Used by `_immersion_gate` to give credit for
# Ukrainian inside dialogue components without counting JSX prop KEYS or
# English translation strings as English tokens.
_JSX_STRING_VALUE_RE = re.compile(r'"([^"\n]*)"')

# Sentence boundaries for the immersion gate's long-sentence check: end-of-
# sentence punctuation (including Ukrainian `…`, `‼`, `⁇`, `⁈`, `⁉`) or a
# markdown bullet/numbered-list marker (`* `, `- `, `1. `). The bullet-marker
# alternations match start-of-string OR after a newline, so a list at the
# very top of the body (e.g., immediately after frontmatter) is recognized
# as a sentence boundary.
_SENTENCE_SPLIT_RE = re.compile(
    r"[.!?…‼⁇⁈⁉]+(?:\s+|$)|(?:\n|^)\s*[*\-]\s+|(?:\n|^)\s*\d+\.\s+",
    re.MULTILINE,
)

# Activity fields whose values are intentionally misspelled — students correct
# them. Excluded from VESUM lookup only for error-correction activities.
_ERROR_CORRECTION_TYPE = "error-correction"
_ERROR_CORRECTION_INTENTIONAL_FIELDS = frozenset({"error", "errorWord", "error_word"})

# String fields whose values are user-facing prose (subject to AI-slop checks).
# YAML structural keys like `correction:` and `correctAnswer:` are deliberately
# excluded — those are schema field names, not prose.
_PROSE_VALUE_FIELDS = frozenset(
    {
        "instruction",
        "title",
        "subtitle",
        "passage",
        "statement",
        "prompt",
        "question",
        "sentence",
        "translation",
        "source",
        "target",
        "usage",
        "notes",
        "summary",
        "description",
    }
)


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


def build_knowledge_packet(plan_path: Path, allow_degraded_rag: bool = False) -> str:
    """Retrieve the writer research packet using the existing RAG packet builder."""
    from scripts.build.research.build_knowledge_packet import build_packet

    return build_packet(plan_path, allow_degraded_rag=allow_degraded_rag)


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
        "COMPONENT_PROPS_SCHEMA": _render_component_props_schema(
            activity_config["ALLOWED_ACTIVITY_TYPES"]
        ),
    }


# Multi-line TSDoc comments embedded in raw type strings would leak into the
# rendered writer prompt verbatim — `odd-one-out`'s `items` field, for example,
# carries `{ /** * @schemaDescription Words... */ words: string[]; ... }[]`.
# That burns tokens and confuses the writer with TypeScript syntax. Strip them
# before rendering. Generator-side fix tracked in #1604.
_TSDOC_BLOCK_RE = re.compile(r"/\*\*.*?\*/", re.DOTALL)


def _strip_tsdoc(raw_type: str) -> str:
    """Remove embedded TSDoc comment blocks and collapse runs of whitespace."""
    cleaned = _TSDOC_BLOCK_RE.sub("", raw_type)
    return " ".join(cleaned.split()).strip()


def _render_component_props_schema(allowed_activity_types: str) -> str:
    """Render compact required/optional prop spec per allowed activity type.

    Reads ``docs/lesson-schema.yaml`` and emits a writer-facing markdown list,
    one bullet per allowed activity type, naming the required and optional
    props plus the nested-item field names. Without this, the writer guesses
    prop shapes — e.g. it produced ``passage:`` for ``fill-in`` (which the
    schema says needs ``items: FillInItem[]``) and omitted ``correct_order``
    on ``order`` activities. The component-prop QG gate then failed late with
    cryptic errors. Surfacing the contract in the prompt is the cheapest fix
    that matches what the gate actually checks (#1602, round 3.5).

    The same ``docs/lesson-schema.yaml`` file is the source of truth for both
    this prompt section and the ``_component_prop_gate`` validator, so the
    writer can never see a stale contract.

    Allowed types that have no resolvable schema entry (the
    ``activity_type: null`` drift class — see #1604 for the ``phrase-table``
    instance) are NOT silently dropped. They emit an explicit
    ``# WARNING: <type> has no schema entry…`` line so the writer is told
    not to use them. Failing loudly here would block round 3.5 dispatch on
    an unrelated generator-side bug; warning + follow-up issue is the right
    scope for this PR.
    """
    allowed = {token.strip() for token in allowed_activity_types.split(",") if token.strip()}
    schema = load_yaml(PROJECT_ROOT / "docs" / "lesson-schema.yaml")
    components = schema.get("components", {}) or {}
    by_type: dict[str, dict[str, Any]] = {}
    for data in components.values():
        if not isinstance(data, dict):
            continue
        activity_type = data.get("activity_type")
        if activity_type in allowed:
            by_type[activity_type] = data
    unresolved = sorted(allowed - by_type.keys())

    def _format_prop(prop: Mapping[str, Any], nested: Mapping[str, Any]) -> str:
        name = prop.get("name", "?")
        ptype = _strip_tsdoc(str(prop.get("type", "")))
        # Resolve nested-item field names so the writer sees the inner shape
        # of arrays like FillInItem[] without us having to repeat the whole
        # schema. Falls back to the raw type string when there's no match.
        item_type = ptype[:-2] if ptype.endswith("[]") else None
        if item_type and item_type in nested:
            fields = ", ".join(
                str(field.get("name", "?"))
                for field in nested[item_type]
                if isinstance(field, dict)
            )
            return f"{name} ({ptype}: {fields})" if fields else f"{name} ({ptype})"
        return f"{name} ({ptype})" if ptype else str(name)

    lines: list[str] = []
    for activity_type in sorted(by_type):
        data = by_type[activity_type]
        props = data.get("props", {}) or {}
        nested = data.get("nested_types", {}) or {}
        required = [p for p in (props.get("required", []) or []) if isinstance(p, dict)]
        optional = [p for p in (props.get("optional", []) or []) if isinstance(p, dict)]
        req_str = ", ".join(_format_prop(p, nested) for p in required) if required else "—"
        opt_str = ", ".join(_format_prop(p, nested) for p in optional) if optional else "—"
        lines.append(f"- {activity_type}:")
        lines.append(f"    required: {req_str}")
        lines.append(f"    optional: {opt_str}")
    for activity_type in unresolved:
        # Visible to both the writer (via the prompt) and to anyone reading
        # the rendered output. Keep the wording stable — tests grep for it.
        lines.append(
            f"- {activity_type}:  # WARNING: no schema entry in "
            f"docs/lesson-schema.yaml — DO NOT USE this activity type "
            f"(see #1604 for the schema-generator drift)"
        )
    if not lines:
        return "(no allowed activity types resolved against lesson-schema.yaml)"
    return "\n".join(lines)


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

    # AI slop and VESUM walk artifacts structurally so YAML schema field names
    # like `correction:` (in error-correction activities) and intentional
    # misspellings in `error:` fields don't trigger false positives.
    prose_text = _extract_prose_text(module_text, activities, vocabulary, resources)

    gates: dict[str, Any] = {
        "word_count": _word_count_gate(module_text, int(plan["word_target"])),
        "plan_sections": _section_gate(module_text, plan),
        "vesum_verified": _vesum_gate(
            module_text=module_text,
            activities=activities,
            vocabulary=vocabulary,
            resources=resources,
            verify_words_fn=verify_words_fn,
        ),
        "citations_resolve": _citation_gate(resources, plan),
        "immersion": _immersion_gate(module_text, plan),
        "inject_activity_ids": _inject_activity_gate(module_text, activities),
        "activity_types": _activity_type_gate(
            activities,
            str(plan["level"]),
            int(plan["sequence"]),
            str(plan["slug"]),
        ),
        "ai_slop_clean": _ai_slop_gate(prose_text),
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

    per_type_fields: dict[str, frozenset[str]] | None = None
    if schema.per_type_extras_authoring:
        per_type_fields = _activity_type_field_whitelist()

    static_allowed_fields = (
        set(schema.required_item_fields) | schema.optional_item_fields
    )
    required_field_names = set(schema.required_item_fields)

    for index, item in enumerate(parsed, start=1):
        if not isinstance(item, dict):
            raise LinearPipelineError(
                f"{artifact} schema validation failed: item {index} must be "
                f"object, got {type(item).__name__}"
            )

        if per_type_fields is None:
            allowed_fields = static_allowed_fields
        else:
            # Polymorphic items: the allowed-field set depends on the `type`
            # discriminator. Validate `type` early so the extra-keys error
            # message can name the actual activity type — and so an unknown
            # type fails with a targeted message instead of a noisy
            # "unexpected fields [...everything...]" report.
            activity_type = item.get("type")
            if not isinstance(activity_type, str) or not activity_type.strip():
                raise LinearPipelineError(
                    f"{artifact} schema validation failed: item {index} "
                    f"requires type as a non-empty string "
                    f"(got {type(activity_type).__name__}: {activity_type!r})"
                )
            type_str = activity_type.strip()
            if type_str not in per_type_fields:
                raise LinearPipelineError(
                    f"{artifact} schema validation failed: item {index} has "
                    f"unknown activity type {type_str!r}; "
                    f"known types: {sorted(per_type_fields)}"
                )
            allowed_fields = required_field_names | per_type_fields[type_str]

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


# Per-activity-type allowed top-level fields in the **authoring YAML
# wire format** (what `ActivityParser._parse_activity` in
# `scripts/yaml_activities.py` consumes, what writers are told to emit
# in `claude_extensions/quick-ref/ACTIVITY-SCHEMAS.md` and the per-level
# `schemas/activities-*.schema.json` JSON Schemas).
#
# This is intentionally NOT sourced from `docs/lesson-schema.yaml` —
# that file describes React component props, which are *renamed* by
# `_*_to_mdx` adapters in `scripts/yaml_activities.py`:
#   - quiz authoring `items` → component prop `questions`
#   - select authoring `items` → component prop `questions`
#   - translate authoring `items` → component prop `questions`
#   - authorial-intent authoring `text_excerpt`/`prompt` → dataclass
#     `excerpt`/`questions`
#   - many seminar types: snake_case authoring → camelCase component
#     props (e.g. `model_answer` → `modelAnswer`, `image_url` →
#     `imageUrl`, `debate_question` → `debateQuestion`)
# Pre-#1627 the gate sourced from `lesson-schema.yaml` and would have
# accepted `quiz: {questions: [...]}` (a writer typo of the component
# prop name) while rejecting the canonical `quiz: {items: [...]}`,
# silently producing empty quizzes (Codex review on #1627).
#
# Drift between this map and the parser is caught by
# `test_activity_authoring_fields_match_parser_dispatch` —
# every parser type has a map entry and vice versa.
# Universal authoring fields valid on every activity type. Sourced from
# the per-level JSON Schemas (`schemas/activities-*.schema.json`), which
# uniformly allow `id`/`type`/`title`/`instruction`/`notes` across types.
_UNIVERSAL_AUTHORING_FIELDS: frozenset[str] = frozenset({
    "id", "type", "title", "instruction", "notes",
})


def _activity(*type_specific: str) -> frozenset[str]:
    """Helper: per-type set = universal fields ∪ supplied type-specific extras."""
    return _UNIVERSAL_AUTHORING_FIELDS | frozenset(type_specific)


_ACTIVITY_AUTHORING_FIELDS: dict[str, frozenset[str]] = {
    # Core L2 question/practice types — items-bearing.
    "quiz":               _activity("items"),
    "select":             _activity("items"),
    "true-false":         _activity("items"),
    "fill-in":            _activity("items"),
    "cloze":              _activity("passage", "blanks"),
    "match-up":           _activity("pairs"),
    "group-sort":         _activity("groups"),
    "unjumble":           _activity("items"),
    "error-correction":   _activity("items"),
    "mark-the-words":     _activity("text", "answers"),
    "translate":          _activity("items"),
    "anagram":            _activity("items"),
    # Pre-literacy (A1 Cyrillic).
    "classify":           _activity("categories"),
    "image-to-letter":    _activity("items"),
    "watch-and-repeat":   _activity("items"),
    # Pre-literacy types declared in `docs/lesson-schema.yaml` but with
    # no `_parse_*` method in `ActivityParser` (silently dropped at
    # parse time). Listed here to preserve the pre-#1624 behavior of
    # the old `lesson-schema.yaml`-sourced loader, which accepted them.
    "count-syllables":    _activity("items", "maxCount"),
    "divide-words":       _activity("items"),
    "highlight-morphemes": _activity(),
    "letter-grid":        _activity("letters"),
    "observe":            _activity("examples", "prompt"),
    "odd-one-out":        _activity("items"),
    "order":              _activity("items", "correct_order"),
    "pick-syllables":     _activity("syllables", "category", "correctIndices", "explanation"),
    # Seminar / B2+ analytical types. The fields below cover both
    # the canonical and legacy authoring shapes that `ActivityParser`
    # accepts (e.g. `target_text` / `questions` / `model_answers` is
    # canonical for critical-analysis, `context` / `question` /
    # `model_answer` is legacy — both are still read).
    "reading":            _activity("text", "context", "source", "resource", "tasks"),
    "essay-response":     _activity("source_reading", "prompt", "min_words", "model_answer", "rubric", "peer_review_guidelines"),
    "critical-analysis":  _activity("source_reading", "target_text", "questions", "model_answers", "context", "question", "model_answer", "focus_points"),
    "comparative-study":  _activity("source_reading", "items_to_compare", "criteria", "prompt", "model_answer", "source_a", "source_b", "task"),
    "authorial-intent":   _activity("source_reading", "text_excerpt", "prompt", "techniques_to_identify", "model_answer"),
    # ISTORIO / HIST.
    "source-evaluation":  _activity("source_text", "source_metadata", "evaluation_criteria", "guiding_questions", "model_evaluation"),
    "debate":             _activity("debate_question", "historical_context", "positions", "analysis_tasks", "model_analysis"),
    # OES / RUTH (historical-Ukrainian linguistic types).
    "etymology-trace":    _activity("items"),
    "grammar-identify":   _activity("items"),
    "transcription":      _activity("original", "answer", "hints"),
    "paleography-analysis": _activity("image_url", "hotspots", "options"),
    "dialect-comparison": _activity("text_a", "text_b", "label_a", "label_b", "features"),
    "translation-critique": _activity("original", "translations", "focus_points"),
}


def _activity_type_field_whitelist() -> dict[str, frozenset[str]]:
    """Return per-activity-type allowed top-level fields in authoring YAML.

    See `_ACTIVITY_AUTHORING_FIELDS` for source-of-truth notes and the
    rationale for sourcing from authoring shape rather than from
    `docs/lesson-schema.yaml` (component-prop side).
    """
    return _ACTIVITY_AUTHORING_FIELDS


# Per-type aliases mapping React COMPONENT prop names (as declared
# in `docs/lesson-schema.yaml`) to AUTHORING YAML field names (as
# emitted by writers and consumed by `scripts/yaml_activities.py`
# parser methods). Sourced from the `_*_to_mdx` adapters in
# `yaml_activities.py` — every line of the form
# `<Component someProp={activity.author_field}>` defines an alias
# `someProp -> author_field` for that component's activity_type.
#
# The default (no entry, or no rename) is identity:
# component-prop-name == authoring-field-name. Most types match:
# `<MatchUp pairs={activity.pairs}>` needs no alias because
# authoring already says `pairs:`.
#
# Used by `_component_prop_gate` to translate
# `lesson-schema.yaml`-declared required props back to the
# authoring-field name expected in the writer's YAML, so the gate
# can validate canonical authoring shape rather than the renamed
# component-prop view.
#
# Drift guard: `test_component_to_authoring_renames_cover_known_renames`
# enforces that every rename-affected type listed here has a
# matching entry in `_ACTIVITY_AUTHORING_FIELDS` (so a rename
# entry can never reference a type unknown to the parser).
_COMPONENT_TO_AUTHORING_RENAMES: dict[str, dict[str, str]] = {
    # `<AuthorialIntent excerpt={activity.excerpt} questions={...} modelAnswer={activity.model_answer}>`
    # — `activity.excerpt` is the dataclass field; parser at
    # `_parse_authorial_intent` reads YAML `text_excerpt:` into it.
    # `questions` is built from YAML `prompt:` (single value lifted
    # to a one-element list).
    "authorial-intent": {
        "excerpt": "text_excerpt",
        "questions": "prompt",
        "modelAnswer": "model_answer",
    },
    # `<Debate debateQuestion={activity.debate_question} ... modelAnalysis={activity.model_analysis}>`
    "debate": {
        "debateQuestion": "debate_question",
    },
    # `<DialectComparison textA={activity.text_a} textB={activity.text_b}>`
    "dialect-comparison": {
        "textA": "text_a",
        "textB": "text_b",
    },
    # `<PaleographyAnalysis imageUrl={activity.image_url}>`
    "paleography-analysis": {
        "imageUrl": "image_url",
    },
    # `<SourceEvaluation sourceText={activity.source_text}>`
    "source-evaluation": {
        "sourceText": "source_text",
    },
}


# JSX-only required props that are RENDERED from activity content
# (or assembled from non-top-level fields), rather than read from
# any authoring YAML top-level field. `_component_prop_gate` skips
# these when checking required props.
#
# Example: `mark-the-words` declares `children` as required because
# the React component receives nested JSX. Authoring YAML has
# `text:` and `answers:` instead — those are not required by the
# schema (the gate validates the inner structure separately via
# strict-JSON parser), so missing `children` in the authoring
# artifact is correct, not a violation.
_COMPONENT_PROP_GATE_JSX_ONLY_PROPS: frozenset[str] = frozenset({
    "children",
})


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
    *,
    module_text: str,
    activities: list[dict[str, Any]],
    vocabulary: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    verify_words_fn: Callable[[list[str]], dict[str, list[dict[str, Any]]]] | None,
) -> dict[str, Any]:
    """Verify Ukrainian words against VESUM, walking artifacts structurally.

    Three classes of false positives are deliberately excluded:

    1. **Phonetic transcriptions and inline code** — `[с':а]`, `[ц':а]`, and
       backticked fragments like `` `вмиваєс':а` `` are metalinguistic notation
       (parts of words, IPA-ish symbols), not VESUM lemmas.
    2. **Intentional misspellings in `error-correction` activities** —
       `error:`, `errorWord:`, and `error_word:` fields contain the typo the
       student must fix (e.g. `прокидаєштся`). Verifying them would always fail.
    3. **Sentence-initial capitalization** — VESUM is case-sensitive, so
       `Спочатку` (capitalized first word) returns no matches even though
       `спочатку` does. Lookup is performed in lowercase; the report keeps
       original casing for evidence.
    """
    from scripts.audit.config import VESUM_MIN_WORD_LENGTH

    text = _build_vesum_text(module_text, activities, vocabulary, resources)

    # Pair each surface form with its lowercase lookup key once, so subsequent
    # whitelist + missing computations don't re-`.lower()` repeatedly.
    surface_pairs = sorted(
        {
            (word, word.lower())
            for raw in _UK_WORD_RE.findall(text)
            for word in [raw.strip("-'ʼ")]
            if len(word) >= VESUM_MIN_WORD_LENGTH
        }
    )
    whitelist_lc = _proper_name_whitelist_lc()
    unchecked_pairs = [
        (surface, lower)
        for surface, lower in surface_pairs
        if lower not in whitelist_lc
    ]
    if verify_words_fn is None:
        from scripts.rag.query import verify_words as verify_words_fn

    # VESUM is case-sensitive — lowercase before lookup so sentence-initial
    # words like "Спочатку" match the lemma "спочатку".
    lookup_words = sorted({lower for _surface, lower in unchecked_pairs})
    try:
        verified = verify_words_fn(lookup_words)
    except Exception as exc:
        return {"passed": False, "error": str(exc), "checked": len(unchecked_pairs)}

    missing_lc = {word for word, matches in verified.items() if not matches}
    missing = sorted(
        {surface for surface, lower in unchecked_pairs if lower in missing_lc}
    )
    return {
        "passed": not missing,
        "checked": len(unchecked_pairs),
        "whitelisted": len(surface_pairs) - len(unchecked_pairs),
        "missing": missing[:100],
        "missing_count": len(missing),
    }


def _proper_name_whitelist_lc() -> frozenset[str]:
    """Lowercase form of `PROPER_NAME_WHITELIST`, computed on every call.

    `_vesum_gate` lowercases each surface form before whitelist membership
    testing, so the whitelist itself must be lowercased once per gate run.

    Adversarial review (Gemini, 2026-04-26, PR #1603): an earlier version
    used `@functools.cache` here. That created a test-isolation hazard —
    any test that mutated `PROPER_NAME_WHITELIST` (e.g. via
    `monkeypatch.setattr` or direct `set.add`) would not be observed by
    pipeline code, because the cache had already snapshotted the original
    set. The constant is small (~90 entries) and `_vesum_gate` is called
    at most once per `run_python_qg`, so re-lowercasing on every call costs
    a few microseconds and is not worth the silent test-flakes the cache
    caused. If profiling ever shows this is hot, prefer recomputing on
    a SHA1 of the constant rather than reintroducing `@functools.cache`.

    Lazy import keeps `scripts.audit.config` out of the module-import path.
    """
    from scripts.audit.config import PROPER_NAME_WHITELIST

    return frozenset(name.lower() for name in PROPER_NAME_WHITELIST)


def _walk_artifact_strings(
    node: Any,
    *,
    keep: Callable[[str | None, str], str | None],
    skip_subtree_keys: frozenset[str] = frozenset(),
) -> list[str]:
    """Recursively collect string leaves from a YAML-like tree.

    Two-level inclusion control:

    - `skip_subtree_keys`: dict keys whose entire VALUE subtree (string OR
      nested dict/list) should be excluded. Used to drop intentional
      misspellings stored under fields like `error:` or `errorWord:` in
      `error-correction` activities, so a future schema like
      `error: { text: "...", note: "..." }` would
      still be entirely excluded — not just the top-level string.
    - `keep(parent_key, string_value)`: leaf-level predicate, called for
      every string leaf NOT skipped by the subtree filter. Returns the
      string to include, or `None` to drop.

    Used to build the VESUM and AI-slop text blobs over
    `activities`/`vocabulary`/`resources` with different inclusion rules.
    """
    out: list[str] = []

    def _walk(value: Any, parent_key: str | None) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in skip_subtree_keys:
                    continue
                _walk(child, key)
        elif isinstance(value, list):
            for item in value:
                _walk(item, parent_key)
        elif isinstance(value, str):
            chunk = keep(parent_key, value)
            if chunk is not None:
                out.append(chunk)

    _walk(node, None)
    return out


def _strip_metalinguistic(text: str) -> str:
    """Strip phonetic transcriptions, code, blank syntax, and morpheme labels.

    Four categories of metalinguistic content are removed before VESUM lookup:

    - `[...]` — phonetic notation like `[с':а]`, `[ц':а]`
    - `` `...` `` and ` ``` ... ``` ` — inline/fenced code
    - `{...}` — fill-in blank syntax like `Я вмиваю{ся}. Він прокидає{ться}.`
    - `\\B-морфема` — hyphen-prefixed conjugation labels like `**-шся**`,
      `**-ться**`. The `\\B` lookbehind protects legitimate hyphenated
      compounds (`темно-синій`) where the char before `-` is a word char.

    Used by the VESUM gate to avoid false positives on fragments that aren't
    VESUM-checkable lemmas.
    """
    text = _FENCED_CODE_RE.sub(" ", text)
    text = _INLINE_CODE_RE.sub(" ", text)
    text = _BRACKETS_RE.sub(" ", text)
    text = _BRACES_RE.sub(" ", text)
    text = _MORPHEME_FRAGMENT_RE.sub(" ", text)
    return text


def _build_vesum_text(
    module_text: str,
    activities: list[dict[str, Any]],
    vocabulary: list[dict[str, Any]],
    resources: list[dict[str, Any]],
) -> str:
    """Compose the text blob that VESUM verifies, with structural exclusions."""
    parts = [_strip_metalinguistic(module_text)]
    for activity in activities:
        parts.append(_strip_metalinguistic(_activity_vesum_text(activity)))
    for entry in vocabulary:
        if isinstance(entry, dict):
            parts.append(_strip_metalinguistic(str(entry.get("lemma", ""))))
            parts.append(_strip_metalinguistic(str(entry.get("usage", ""))))
    for entry in resources:
        if isinstance(entry, dict):
            parts.append(_strip_metalinguistic(str(entry.get("title", ""))))
            parts.append(_strip_metalinguistic(str(entry.get("notes", ""))))
    return "\n".join(part for part in parts if part)


def _activity_vesum_text(activity: dict[str, Any]) -> str:
    """Walk an activity's string values, excluding intentional-error fields.

    For `error-correction` activities, fields like `error:` and `errorWord:`
    hold the typo the student must fix; verifying them against VESUM would
    always fail. The skip is at the dict (subtree) level so even a future
    nested shape like `error: { text: "...", note: "..." }` would be entirely
    excluded.
    """
    if activity.get("type") == _ERROR_CORRECTION_TYPE:
        skip_subtree = _ERROR_CORRECTION_INTENTIONAL_FIELDS
    else:
        skip_subtree = frozenset()

    def keep(_parent_key: str | None, value: str) -> str | None:
        return value

    return "\n".join(
        _walk_artifact_strings(activity, keep=keep, skip_subtree_keys=skip_subtree)
    )


def _extract_prose_text(
    module_text: str,
    activities: list[dict[str, Any]],
    vocabulary: list[dict[str, Any]],
    resources: list[dict[str, Any]],
) -> str:
    """Concatenate user-facing prose strings for AI-slop pattern checks.

    Slop patterns target English chatter (e.g., "Welcome", "Buckle up",
    "Correction:"). They run on `module.md` plus the prose-bearing values of
    activities/vocab/resources — not on the YAML field NAMES, which include
    legitimate schema keys like `correction:` (in `error-correction`
    activities) that would otherwise produce false positives.
    """
    def keep(parent_key: str | None, value: str) -> str | None:
        return value if parent_key in _PROSE_VALUE_FIELDS else None

    parts = [module_text]
    for source in (activities, vocabulary, resources):
        parts.extend(_walk_artifact_strings(source, keep=keep))
    return "\n".join(parts)


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
    """Check Ukrainian immersion ratio + flag overly long Ukrainian sentences.

    Both the percent calculation AND the long-sentence check operate on a
    JSX-stripped view of the body. Without that, prop KEYS (`speaker`,
    `text`, `translation`) and English translation strings inside dialogue
    components are counted as English tokens, deflating the immersion
    percentage. To still credit Ukrainian-bearing dialogue text, we
    separately extract string values from JSX (`text="..."` / `text: "..."`)
    and add their tokens back. Net effect: only learner-facing Ukrainian
    text inside JSX counts toward immersion, structural prop syntax doesn't.

    The long-sentence check splits on Ukrainian-aware sentence punctuation
    (`. ! ? … ‼ ⁇ ⁈ ⁉`) and markdown list-item starts (`* `, `- `, `1. `,
    including at start-of-string) so bullet items render as separate
    sentences instead of one giant joined run.
    """
    level = str(plan["level"]).lower()
    sequence = int(plan["sequence"])
    min_pct, max_pct = get_immersion_range(level, sequence)
    body = _strip_frontmatter_and_headings(_strip_comments(text))

    body_no_jsx = _JSX_BLOCK_RE.sub(" ", body)
    jsx_string_props: list[str] = []
    for jsx_block in _JSX_BLOCK_RE.findall(body):
        jsx_string_props.extend(_JSX_STRING_VALUE_RE.findall(jsx_block))
    counted_text = "\n".join([body_no_jsx, *jsx_string_props])

    tokens = _WORD_RE.findall(counted_text)
    uk_tokens = [token for token in tokens if _UK_WORD_RE.search(token)]
    pct = round((len(uk_tokens) / len(tokens) * 100), 2) if tokens else 0.0

    long_sentences = [
        sentence.strip()
        for sentence in _SENTENCE_SPLIT_RE.split(body_no_jsx)
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
    """Validate authoring activities against component-prop required-prop schema.

    Required props in `docs/lesson-schema.yaml` are React component prop
    names (e.g. `<AuthorialIntent excerpt={...}>` declares `excerpt` as
    required). Authoring YAML emitted by writers uses field names that
    `scripts/yaml_activities.py` parser methods consume — sometimes those
    are renamed at render time (e.g. `text_excerpt:` in YAML →
    `activity.excerpt` dataclass field → `<AuthorialIntent excerpt=...>`).

    The gate translates each required component-prop name through
    `_COMPONENT_TO_AUTHORING_RENAMES` to its authoring-field name (or
    keeps it unchanged if no rename exists), then checks the authoring
    activity dict for that field. JSX-only props in
    `_COMPONENT_PROP_GATE_JSX_ONLY_PROPS` (e.g. `children` for
    `mark-the-words`) are skipped — they're rendered from non-top-level
    activity content.
    """
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
        required_component_props = [
            prop["name"]
            for prop in component.get("props", {}).get("required", [])
            if isinstance(prop, dict)
        ]
        # `activity_type` is non-None here (guarded by `component is None`
        # check above), but Pyright can't track that across the dict lookup.
        renames = _COMPONENT_TO_AUTHORING_RENAMES.get(activity_type or "", {})
        # Translate component-prop names to authoring field names; skip
        # JSX-only props that aren't represented as top-level YAML fields.
        # `isinstance(comp_prop, str)` narrows the type for `renames.get`
        # (required_component_props comes from `prop["name"]` over a
        # dict[str, Any], so its element type is Any from Pyright's POV).
        required_authoring_fields: list[str] = [
            renames.get(comp_prop, comp_prop)
            for comp_prop in required_component_props
            if isinstance(comp_prop, str)
            and comp_prop not in _COMPONENT_PROP_GATE_JSX_ONLY_PROPS
        ]
        missing = [field for field in required_authoring_fields if field not in activity]
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


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Linear Phase 4 pipeline")
    parser.add_argument("level", help="Level (e.g., a1)")
    parser.add_argument("slug", help="Module slug (e.g., my-morning)")
    parser.add_argument("--writer", choices=WRITER_CHOICES, default="gemini-tools")
    parser.add_argument(
        "--allow-degraded-rag",
        action="store_true",
        help="Allow thin packets on RAG failure",
    )
    args = parser.parse_args()

    plan_path = plan_path_for(args.level, args.slug)
    print(f"📋 Checking plan: {plan_path}")
    plan = plan_check(plan_path)

    print("🔍 Building knowledge packet...")
    if args.allow_degraded_rag:
        print(
            "  ⚠️  LOUD WARNING: --allow-degraded-rag is ON. Knowledge packet may be thin if RAG fails.",
            file=sys.stderr,
        )
    packet = build_knowledge_packet(plan_path, allow_degraded_rag=args.allow_degraded_rag)

    print(f"🤖 Invoking writer ({args.writer})...")
    plan_content = plan_path.read_text(encoding="utf-8")
    ctx = writer_context(plan, plan_content, packet)
    prompt_path = PROJECT_ROOT / "scripts/build/phases/linear-write.md"
    prompt = render_phase_prompt(prompt_path, ctx)

    output = invoke_writer(prompt, args.writer)

    print("📦 Parsing artifacts...")
    artifacts = parse_writer_output(output)

    module_dir = PROJECT_ROOT / "curriculum" / "l2-uk-en" / args.level / args.slug
    print(f"💾 Writing artifacts to {module_dir}...")
    write_writer_artifacts(module_dir, artifacts)

    print("✅ Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
