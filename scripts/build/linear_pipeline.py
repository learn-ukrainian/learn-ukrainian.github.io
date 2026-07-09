"""Linear Phase 4 module pipeline.

This module intentionally implements a one-way build path: plan validation,
research packet assembly, prompt rendering, writer invocation, deterministic
Python QG, independent LLM QG aggregation, and MDX assembly. It does not expose
any LLM rewrite or regeneration loop.

Path 3 PR3 adds a bounded wiki_coverage correction loop around deterministic
fix proposals; see
docs/decisions/2026-05-17-path3-per-obligation-review-loop.md.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
TEXTBOOK_SOURCES_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
FOLK_HERITAGE_ATTESTATIONS_PATH = PROJECT_ROOT / "data" / "folk_heritage_attestations.yaml"
FOREIGN_PROPER_NOUN_ATTESTATIONS_PATH = PROJECT_ROOT / "data" / "foreign_proper_noun_attestations.yaml"
PRIMARY_TEXT_SOURCES_PATH = PROJECT_ROOT / "data" / "primary_text_sources.yaml"
CLAUDE_WRITER_AGENT_SOURCE = PROJECT_ROOT / "agents_extensions/shared" / "agents" / "curriculum-writer.md"
CLAUDE_WRITER_AGENT_TARGET = PROJECT_ROOT / ".claude" / "agents" / "curriculum-writer.md"

from scripts.audit.content_surface_gates import scan_module_surface, scan_surface_text
from scripts.audit.failure_classes import FailureClass, FailureRecord
from scripts.audit.wiki_completeness_gate import SEMINAR_LEVELS
from scripts.build.citation_matcher import (
    CitationKey,
    citation_keys_match,
    extract_chunk_id_from_notes,
    extract_citation_key,
    extract_plan_reference_titles,
    fold_citation_author,
    normalize_citation_ref,
)
from scripts.build.module_size_policy import (
    build_size_policy_for_plan,
    render_reviewer_size_policy,
    render_writer_size_policy,
    size_policy_allows_auto_expansion,
    size_policy_summary,
)
from scripts.build.prompt_builder import DOWNSTREAM_TOKENS, TOKEN_RE, render_prompt
from scripts.common.review_loop import (
    aggregate_min as review_loop_aggregate_min,
)
from scripts.common.review_loop import (
    best_round_index,
    min_score_regressed,
)
from scripts.common.thresholds import QG_DIMS, aggregate_review
from scripts.config import get_immersion_policy, get_immersion_range, get_immersion_rule
from scripts.generate_mdx.core import generate_mdx
from scripts.generate_mdx.resources import validate_and_clean_url
from scripts.pipeline.learner_state import build_learner_state, format_learner_state
from scripts.pipeline.module_archetypes import format_module_archetype, resolve_module_archetype

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

WRITER_CHOICES = (
    "claude-tools",
    "gemini-tools",
    "codex-tools",
    "grok-tools",
    "cursor-tools",
    "deepseek-tools",
    "qwen-tools",
    "agy-tools",
)
WRITER_DEFAULTS: dict[str, dict[str, str]] = {
    "claude-tools": {"model": "claude-opus-4-8", "effort": "xhigh"},
    "gemini-tools": {"model": "gemini-3.1-pro-preview", "effort": "high"},
    "codex-tools": {"model": "gpt-5.5", "effort": "high"},
    "grok-tools": {"model": "grok-4.3", "effort": "medium"},
    "cursor-tools": {"model": "composer-2.5", "effort": "medium"},
    "deepseek-tools": {"model": "deepseek-v4-pro", "effort": "medium"},
    "qwen-tools": {"model": "qwen/qwen3.6-plus", "effort": "medium"},
    # agy effort is a no-op on the CLI today (Phase-2 follow-up). The
    # model field is informational only; the TUI-selected model is what
    # actually runs. "medium" is a placeholder for telemetry parity.
    "agy-tools": {"model": "gemini-3.5-flash-high", "effort": "medium"},
}
PROMPT_BY_WRITER = {
    "grok-tools": "linear-write-grok.md",
}
CORRECTION_PROMPT_BY_WRITER = {
    "grok-tools": "linear-writer-correction-grok.md",
}
WRITER_SPECIFIC_DIRECTIVES: dict[str, str] = {
    "cursor-tools": """\
## cursor-tools writer directives
- Use ONLY `mcp__sources__*` tools for verification. Do NOT run shell commands or edit files.
- Emit all artifacts as fenced blocks in your final message (`markdown file=…`, `json file=…`).
- If MCP is unavailable, emit `<!-- VERIFY: … -->` and continue — do not improvise with Bash/Write.
""",
    "agy-tools": """\
## agy-tools writer directives

These directives apply only when the selected writer is `agy-tools`.

- Use `mcp_sources_*` tools directly. Do NOT issue curl-via-Bash for MCP retrieval — your native integration is wired.
- After each MCP call, emit the verbatim TEXT field from the server's response (the markdown-text payload inside `content[0].text`). Do NOT substitute your parsed JSON view of the response — the pipeline parser expects the raw payload format.
- If an MCP retrieval returns 0 hits or the wrong page, emit a `<!-- VERIFY: ... -->` marker in the artifact and continue. Do NOT side-investigate via `sqlite3`, codebase grep, `python` scripts, or any other path outside MCP.
- Allowed bash: NONE except `curl` against `http://127.0.0.1:8766/mcp` as a fallback when the native integration returns an error.
- Allowed file operations: read/write ONLY within the build worktree's `curriculum/l2-uk-en/<level>/<slug>/` directory.
""",
}
REVIEWER_CHOICES = (
    "claude-tools",
    "gemini-tools",
    "codex-tools",
    "grok-tools",
    "cursor-tools",
    "deepseek-tools",
    "qwen-tools",
    "agy-tools",
)
REVIEWER_DEFAULTS: dict[str, dict[str, str]] = {
    "claude-tools": {"model": "claude-opus-4-8", "effort": "xhigh"},
    "gemini-tools": {"model": "gemini-3.1-pro-preview", "effort": "high"},
    "codex-tools": {"model": "gpt-5.5", "effort": "high"},
    "grok-tools": {"model": "grok-4.3", "effort": "medium"},
    "cursor-tools": {"model": "grok-4.20-reasoning", "effort": "medium"},
    "deepseek-tools": {"model": "deepseek-v4-pro", "effort": "medium"},
    "qwen-tools": {"model": "qwen/qwen3.6-plus", "effort": "medium"},
    "agy-tools": {"model": "gemini-3.5-flash-high", "effort": "medium"},
}
WRITER_ARTIFACTS = (
    "module.md",
    "activities.yaml",
    "vocabulary.yaml",
    "resources.yaml",
)
_LABEL_LINE_RE = re.compile(
    r"^[\s>#\-*]*(?P<name>" + "|".join(re.escape(name) for name in WRITER_ARTIFACTS) + r")\s*:?\s*$"
)

PYTHON_QG_GATE_ORDER = (
    "tool_theatre",
    "strict_json_parse",
    "activity_schema",
    "quiz_translate_explanations",
    "word_count",
    "vocab_count",
    "vocab_floor",
    "plan_sections",
    "formatting_standards",
    "scaffolding_leak",
    "vesum_verified",
    "bad_form_heritage",
    "citations_resolve",
    "plan_reference_match",
    "resource_coverage",
    "reading_coverage",
    "resources_url_resolve",
    "chunk_context_for_all_refs",
    "published_quote_for_publishable_refs",
    "textbook_quote_fidelity",
    "textbook_grounding",
    "resources_search_attempted",
    "immersion_advisory",
    "l2_exposure_floor",
    "long_uk_ceiling",
    "component_density",
    "archetype_fit",
    "inject_activity_ids",
    "activity_types",
    "ai_slop_clean",
    "surface_policy",
    "russianisms_strict",
    "register_consistency",
    "engagement_floor",
    "component_props",
    "russianisms_clean",
    "surzhyk_clean",
    "calques_clean",
    "paronym_clean",
    "mdx_render",
)
PYTHON_QG_META_GATES = frozenset(
    {
        "passed",
        "correction_terminal",
        "previously_passed_regression",
    }
)
PYTHON_QG_UNMAPPED_FAILURE_FRONTIER = -1
WRITER_CORRECTION_GATES = frozenset(
    {
        "activity_schema",
        "strict_json_parse",
        "tool_theatre",
        "word_count",
        "plan_sections",
        "formatting_standards",
        "mdx_render",
    }
)
DETERMINISTIC_VOCAB_FLOOR_GATES = frozenset({"vocab_count", "vocab_floor"})
DICTIONARY_CANDIDATE_GATES = frozenset(
    {
        "vesum_verified",
        "russianisms_clean",
        "surzhyk_clean",
        "calques_clean",
        "paronym_clean",
        "citations_resolve",
        "plan_reference_match",
    }
)
REVIEWER_FIX_GATES = DICTIONARY_CANDIDATE_GATES | frozenset(
    {
        "l2_exposure_floor",
        "long_uk_ceiling",
        "component_density",
        "resources_url_resolve",
        "ai_slop_clean",
    }
)
REVIEWER_FIX_ADDITIONAL_ARTIFACTS_BY_GATE: dict[str, tuple[str, ...]] = {
    "vesum_verified": ("activities.yaml", "vocabulary.yaml", "resources.yaml"),
    "russianisms_clean": ("activities.yaml", "vocabulary.yaml", "resources.yaml"),
    "surzhyk_clean": ("activities.yaml", "vocabulary.yaml", "resources.yaml"),
    "calques_clean": ("activities.yaml", "vocabulary.yaml", "resources.yaml"),
    "paronym_clean": ("activities.yaml", "vocabulary.yaml", "resources.yaml"),
    "citations_resolve": ("resources.yaml",),
    "plan_reference_match": ("resources.yaml",),
    "resources_url_resolve": ("resources.yaml",),
    "ai_slop_clean": ("activities.yaml", "vocabulary.yaml", "resources.yaml"),
    "llm_qg_grammar_calque": ("activities.yaml", "vocabulary.yaml", "resources.yaml"),
}
PIPELINE_INSERT_GATES = frozenset({"inject_activity_ids"})
TERMINAL_ZERO_RETRY_GATES = frozenset(
    {
        "component_props",
        "previously_passed_regression",
        "quiz_translate_explanations",
        "bad_form_heritage",
        "resources_search_attempted",
    }
)

# Deterministic first-pass replacements used to seed reviewer SELECT prompts.
# The reviewer may select among these candidates but must not invent new ones.
DICTIONARY_REPLACEMENTS = {
    "пожалуйста": ("будь ласка", "Антоненко-Давидович / standard Ukrainian usage"),
    "спасибо": ("дякую", "Антоненко-Давидович / standard Ukrainian usage"),
    "хорошо": ("добре", "Антоненко-Давидович / standard Ukrainian usage"),
    "конечно": ("звичайно", "Антоненко-Давидович / standard Ukrainian usage"),
    "ничего": ("нічого", "Антоненко-Давидович / standard Ukrainian usage"),
    "сейчас": ("зараз", "Антоненко-Давидович / standard Ukrainian usage"),
    "тоже": ("також", "Антоненко-Давидович / standard Ukrainian usage"),
    "здесь": ("тут", "Антоненко-Давидович / standard Ukrainian usage"),
    "кот": ("кіт", "VESUM-verified Ukrainian equivalent"),
    "шо": ("що", "Антоненко-Давидович / standard Ukrainian usage"),
    "канєшно": ("звісно", "Антоненко-Давидович / standard Ukrainian usage"),
    "счас": ("зараз", "Антоненко-Давидович / standard Ukrainian usage"),
    "нє": ("ні", "Антоненко-Давидович / standard Ukrainian usage"),
    "приймати участь": ("брати участь", "Антоненко-Давидович style guide"),
    "на протязі": ("протягом", "Антоненко-Давидович style guide"),
    "по крайній мірі": ("принаймні", "Антоненко-Давидович style guide"),
    "відноситися до": ("стосуватися", "Антоненко-Давидович style guide"),
    "рахувати що": ("вважати, що", "Антоненко-Давидович style guide"),
}

PROMPT_ADHERENCE_FIELDS: tuple[str, ...] = (
    "word_budget",
    "plan_vocab",
    "register",
    "teaching_sequence",
    "verification_plan",
    "verification_trace",
)
PROMPT_ADHERENCE_FIELD_PATTERNS: dict[str, tuple[str, ...]] = {
    "word_budget": (r"<word_budget\b[^>]*>.*?\S.*?</word_budget>",),
    "plan_vocab": (r"<plan_vocab\b[^>]*>.*?\S.*?</plan_vocab>",),
    "register": (r"<register\b[^>]*>.*?\S.*?</register>",),
    "teaching_sequence": (r"<teaching_sequence\b[^>]*>.*?\S.*?</teaching_sequence>",),
    "verification_plan": (r"<verification_plan\b[^>]*>.*?\S.*?</verification_plan>",),
    "verification_trace": (r"<verification_trace\b[^>]*>.*?\S.*?</verification_trace>",),
}
WRITER_TOOL_NAMES = frozenset(
    {
        "verify_words",
        "verify_lemma",
        "search_definitions",
        "search_definitions_slovnyk",
        "search_esum",
        "search_grinchenko_1907",
        "search_heritage",
        "search_literary",
        "search_slovnyk_me",
        "search_style_guide",
        "search_idioms",
        "query_pravopys",
        "query_wikipedia",
        "search_external",
        "search_images",
        "search_text",
        "check_modern_form",
    }
)
WRITER_ALLOWED_TOOL_PREFIX = "mcp__sources__"
# Gemini CLI 0.42.0+ emits tool calls with single-underscore separators
# (`mcp_sources_search_text`) instead of the canonical double-underscore MCP
# convention (`mcp__sources__search_text`) used by claude, codex, hermes-backed
# writers. Both are the same MCP "sources" server tool — Gemini's representation
# changed between 0.40.x and 0.42.x. Accept both prefixes for the
# writer-trace-isolation gate so gemini-tools' valid MCP calls aren't
# misclassified as wrong-tool-family. Genuinely dangerous wrong-family calls
# (shell exec / arbitrary file Read / Bash) remain flagged via the absence
# of either prefix and the absence from WRITER_AGENT_ANNOTATION_TOOLS below.
# Related: #2159-adjacent; see 2026-05-19 B1 bakeoff gemini-tools investigation
# and 2026-05-21 night handoff Section 1b (gemini-tools writer success run).
WRITER_ALLOWED_TOOL_PREFIXES = (
    "mcp__sources__",  # canonical (claude, codex, deepseek, qwen, grok)
    "mcp_sources_",  # gemini-cli 0.42.0+ single-underscore convention
)
# Agent-CLI built-in self-annotation tools. These emit METADATA only — no file
# access, no command execution, no curriculum-content impact — and are
# preserved in `writer_tool_calls.json` for forensics but DO NOT trigger
# wrong_tool_family. Distinct from dangerous built-ins like `run_shell_command`
# (exec capable), `Read`/`Write` (file I/O), `Bash`/`Edit` (both) — those
# remain flagged because they're not in this allowlist.
#
# Empirical evidence (2026-05-21 a1/my-morning gemini-tools run): gemini-cli
# 0.42.0 emits exactly one `update_topic` call as the writer's first tool
# invocation (strategic_intent / title / summary fields, agent self-narration).
# The writer then proceeds to make 13 valid `mcp_sources_*` calls and writes
# all 6 V7 artifacts. Without this allowlist the rigid prefix check trips
# wrong_tool_family on the one annotation call and discards a successful
# build. See `curriculum/l2-uk-en/_orchestration/a1/my-morning/runs/20260520-234426/`
# for the smoking-gun trace.
#
# Claude Code 2.1.159 may emit `ToolSearch` before a sources MCP call when
# selecting dynamically exposed MCP tools. Treat that as discovery metadata,
# not content grounding. The positive source-call gate below still hard-fails
# when no real `mcp__sources__*` call follows.
WRITER_AGENT_ANNOTATION_TOOLS = frozenset(
    {
        "update_topic",  # gemini-cli 0.42.0+ strategic-intent / title / summary
        "ToolSearch",  # claude-code 2.1.159+ dynamic MCP tool discovery
    }
)
WRITER_INFRA_DENYLIST_PATHS = (
    "docs/session-state/**",
    "docs/decisions/**",
    "docs/dispatch-briefs/**",
    "memory/MEMORY.md",
    "~/.claude/CLAUDE.md",
    "CLAUDE.md",
    "scripts/delegate.py",
    "scripts/ai_agent_bridge/**",
    "agents_extensions/shared/agents/curriculum-orchestrator.md",
    "agents_extensions/shared/rules/**",
    ".claude/rules/**",
    "*handoff*",
    "*orchestration*",
    "*dispatch*",
)


def ensure_claude_writer_agent_deployed(
    *,
    source_path: Path = CLAUDE_WRITER_AGENT_SOURCE,
    target_path: Path = CLAUDE_WRITER_AGENT_TARGET,
) -> dict[str, Any]:
    """Materialize the tracked Claude writer agent into the runtime tree.

    Claude Code resolves `--agent curriculum-writer` from `.claude/agents`
    in or above the run cwd. V7 builds run from nested worktrees, so relying
    on an ancestor checkout's ignored `.claude` copy can select stale tools.
    """
    source_text = _read_required(source_path)
    previous_text = target_path.read_text(encoding="utf-8") if target_path.exists() else None
    changed = previous_text != source_text
    if changed:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(source_text, encoding="utf-8")
    return {
        "source": str(source_path),
        "path": str(target_path),
        "changed": changed,
    }
RESOURCE_ROLES = frozenset(
    {
        "textbook",
        "youtube",
        "video",
        "blog",
        "podcast",
        "audio",
        "article",
        "reading",
        "wiki",
    }
)
INTERNAL_RESOURCE_URL_PREFIXES = ("wiki/", "docs/wiki/")
URL_BEARING_RESOURCE_ROLES = frozenset(
    {"reading", "article", "blog", "video", "youtube", "podcast", "audio", "wiki"}
)
MULTIMEDIA_SEARCH_TOOLS = frozenset(
    {
        "query_wikipedia",
        "search_external",
        "search_images",
        "browser_search",
        "search_query",
        "web_search",
    }
)
REVIEW_AUDIT_TYPES = frozenset(
    {
        "source_attribution",
        "quote_verification",
        "sovietization_check",
        "modern_form_check",
    }
)
TELEMETRY_MAX_QUOTES = 5
TELEMETRY_MAX_QUOTE_CHARS = 240
TELEMETRY_MAX_MAPPING_CHARS = 500
TELEMETRY_MAX_FAILED_WORDS = 5
TELEMETRY_MAX_THEATRE_VIOLATIONS = 25
TEXTBOOK_GROUNDING_MIN_WORDS = 30
VESUM_PRIMARY_EXEMPTION_MIN_WORDS = 8

RULE_VOICE_META = "#R-VOICE-META"
RULE_BAD_FORM_MARKER = "#R-BAD-FORM-MARKER"
RULE_VESUM_ALL_WORDS = "#R-VESUM-ALL-WORDS"
RULE_IMPL_MAP_COMPLETE = "#R-IMPL-MAP-COMPLETE"
RULE_NO_SCAFFOLDING_LEAKS = "#R-NO-SCAFFOLDING-LEAKS"
RULE_TEXTBOOK_30W = "#R-TEXTBOOK-30W"
RULE_CITE_HONEST = "#R-CITE-HONEST"
CORRECTION_PREVIEW_CHARS = 200
WIKI_COVERAGE_BATCH_MAX_ITERATIONS = 2
WIKI_COVERAGE_NARROW_MAX_ITERATIONS = 2
WIKI_COVERAGE_PATCHABLE_ARTIFACTS = frozenset({"module.md", "activities.yaml"})
WIKI_COVERAGE_ARTIFACT_INFERENCE_ORDER = ("activities.yaml", "module.md")
CORRECTION_YAML_ARTIFACT_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    # NOTE: `id` is intentionally NOT required on activities.yaml entries —
    # the V7 writer prompt (`scripts/build/phases/linear-write.md`, lines
    # 700-701 as of PR #2214) specifies that WORKBOOK activities should
    # OMIT `id`; only INLINE activities (those referenced from a
    # `<!-- INJECT_ACTIVITY: act-N -->` marker in the prose) need a string
    # id so the marker can resolve. The bidirectional consistency check
    # lives in the `inject_activity_ids` content gate (not here). The
    # deeper `_activity_schema_gate` likewise tolerates missing id (it
    # falls back to `f"#{activity_index}"` for diagnostics).
    "activities.yaml": ("type",),
    "vocabulary.yaml": ("lemma", "translation", "pos", "usage"),
    "resources.yaml": ("title", "role"),
}
ALLOWED_WIKI_COVERAGE_VERDICTS = {"PASS", "KEYWORD_STUFFING", "PARTIAL", "FAIL"}
WIKI_COVERAGE_OVERALL_FAIL_VERDICTS = {"FAIL", "KEYWORD_STUFFING"}
WIKI_COVERAGE_OVERALL_VERDICTS = {"PASS", "PARTIAL", "FAIL"}
WIKI_COVERAGE_EVIDENCE_QUOTE_MARKERS = ('"', "“", "«")
LLM_QG_CORE_MAX_ROUNDS = 2
LLM_QG_SEMINAR_MAX_ROUNDS = 3
LLM_QG_REVIEWER_SAMPLES = {"seminar": 3}
LLM_QG_GRAMMAR_CALQUE_GATE = "llm_qg_grammar_calque"
LLM_QG_GRAMMAR_CALQUE_ISSUE_IDS = frozenset(
    {
        "UKRAINIAN_GRAMMAR_CALQUE",
        "AWKWARD_PASSIVE_RESULT_STATE",
        "UNNATURAL_ANTHROPOMORPHISM",
        "UNNATURAL_META_REGISTER",
    }
)
# LLM judges have measurable round-over-round noise; only stop correction on
# min-score drops that exceed this conservative tolerance.
LLM_QG_REGRESSION_NOISE_TOLERANCE = 0.5
PYTHON_QG_CORE_MAX_CORRECTION_ROUNDS = 1
PYTHON_QG_SEMINAR_MAX_CORRECTION_ROUNDS = 8
PYTHON_QG_MIN_REGRESSION_PATIENCE = 3
PYTHON_QG_MALFORMED_REPORT_VIOLATIONS = 999
PYTHON_QG_VIOLATION_COUNT_KEYS = (
    "missing",
    "violations",
    "errors",
    "findings",
    "critical_findings",
    "detections",
    "regressions",
    "invalid",
    "missing_terms",
    "missing_sections",
    "malformed_callouts",
    "missing_mandatory_callouts",
    "unresolved",
    "unresolved_citations",
    "missing_required",
    "missing_optional",
    "missing_activity_ids",
    "duplicate_ids",
)
_TELEMETRY_EVENT_SINK: Callable[..., None] | None = None


@dataclass(frozen=True, slots=True)
class CorrectionCandidate:
    """Pipeline-proposed replacement candidate for reviewer selection."""

    original: str
    replacement: str
    source: str
    gate: str


@dataclass(frozen=True, slots=True)
class CorrectionContext:
    """Context passed to ADR-008 correction handlers."""

    gate: str
    gate_report: Mapping[str, Any]
    module_dir: Path
    plan_path: Path
    qg_report: Mapping[str, Any]
    candidates: tuple[CorrectionCandidate, ...] = ()
    prompt: str = ""


@dataclass(frozen=True, slots=True)
class ReviewerFixApplyResult:
    text: str
    unmatched_anchors: frozenset[str]


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
        # NOTE: `id` is intentionally NOT required here. The V7 writer prompt
        # (`scripts/build/phases/linear-write.md`, lines 700-701 as of
        # PR #2214) specifies that WORKBOOK activities should OMIT `id`;
        # only INLINE activities (those targeted by
        # `<!-- INJECT_ACTIVITY: act-N -->` markers in the lesson prose)
        # need a string id so the marker can resolve. The bidirectional
        # consistency check between INJECT markers and present ids lives
        # in the `inject_activity_ids` content gate. `id` remains in
        # `_UNIVERSAL_AUTHORING_FIELDS` so it is ALLOWED when present —
        # just not required. Same rationale applied to
        # `CORRECTION_YAML_ARTIFACT_REQUIRED_FIELDS["activities.yaml"]`.
        required_item_fields={
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
            "role": str,
        },
        optional_item_fields=frozenset(
            {
                "notes",
                "description",
                "source_ref",
                "packet_chunk_id",
                # Alias for packet_chunk_id — writers naturally emit this name
                # (it matches plan.notes wording and MCP tool arg names). Both
                # accepted; downstream code (L7757) reads packet_chunk_id, so a
                # writer-emitted chunk_id is decorative metadata. Added 2026-05-23
                # after m20 build #5 schema-rejected writer's chunk_id field.
                "chunk_id",
                "url",
                "section",
                "page",
                "pages",
                "author",
                "channel",
                "source",
                "match_reason",
            }
        ),
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
        # r"\bшо\b",  # Reclassified as register_consistency (WARN), see PR #2294
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
# Bounded markdown-decoration quantifiers to avoid ReDoS (py/redos).
# Decoration markers (`*`, `_`, `` ` ``) appear at most twice contiguously in
# real markdown (`**bold**`, single `*italic*`, `_italic_`, backtick code).
# Bounding the leading/trailing decoration to {0,2} chars and the inner
# repetition to {0,4} word-segment boundaries makes the match linear-time
# while still catching every realistic decorated Ukrainian surface form.
_VESUM_DECORATED_WORD_RE = re.compile(
    r"[*_`]{0,2}"
    r"[А-ЯІЇЄҐа-яіїєґ][А-ЯІЇЄҐа-яіїєґ'ʼ\-\u0300\u0301]*"
    r"(?:[*_`]{1,2}[А-ЯІЇЄҐа-яіїєґ][А-ЯІЇЄҐа-яіїєґ'ʼ\-\u0300\u0301]*){0,4}"
    r"[*_`]{0,2}"
)
_INJECT_RE = re.compile(r"<!--\s*INJECT_ACTIVITY:\s*([A-Za-z0-9_-]+)\s*-->")
_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_VESUM_SHORT_DECORATED_WORDS = frozenset({"ся", "сь"})
_VESUM_STRESS_MARKS = frozenset({"\u0300", "\u0301"})
_VESUM_APOSTROPHE_TRANSLATION = str.maketrans(
    {
        "\u02bc": "'",
        "\u2019": "'",
        "\u2018": "'",
        "`": "'",
        "\u00b4": "'",
    }
)
_VESUM_WORD_EDGE_CHARS = "-'ʼ’‘`´"
_CYRILLIC_ROMAN_NUMERAL_TRANSLATION = str.maketrans({"Х": "X", "І": "I"})
_ROMAN_NUMERAL_RE = re.compile(
    r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$",
    re.IGNORECASE,
)
# O-grade plural obliques (`-остей`, `-остями`, `-остях`, `-остям`) overlap
# Russian `-ость` forms such as `новостей`; keep that fallback to longer
# stems so it does not pass merely because short bases like `новий` verify.
_VESUM_PRODUCTIVE_IST_ENDINGS = (
    ("остями", 5),
    ("остей", 5),
    ("остях", 5),
    ("остям", 5),
    ("істю", 1),
    ("ості", 1),
    ("ість", 1),
)

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
# stripping morpheme labels in `**-шся**`, `__-шся__`, and `-**юся**`
# (markdown emphasis around all or part of the label). We don't use Python's
# `\B` because `_` is a word character there, which would make `__-шся__`
# un-strippable.
_MORPHEME_FRAGMENT_RE = re.compile(
    r"(?<![А-ЯІЇЄҐа-яіїєґ'ʼA-Za-z0-9])[*_`]{0,2}-[*_`]{0,2}"
    r"[А-ЯІЇЄҐа-яіїєґ][А-ЯІЇЄҐа-яіїєґ'ʼ]*[*_`]{0,2}"
)
_PRONUNCIATION_CUE_PATTERN = re.compile(
    r"(?:sounds?\s+like|звучить\s+як|вимовляється\s+як|вимова[:\s])\s*\*\*[^*]+\*\*",
    re.IGNORECASE,
)

# Pedagogical "bad form" marker for prose Russianism / surzhyk / calque
# callouts. Patterns like `<!-- bad -->завтрак<!-- /bad -->` deliberately
# show a non-standard form for learner contrast (e.g. "stick to сніданок,
# not the Russian-borrowed завтрак"). The bad form is intentionally absent
# from VESUM — flagging it would be a false positive. The HTML comments
# don't render in MDX, so the learner still sees `завтрак` in plain prose.
# Bounded by `re.DOTALL` so multi-line callouts are still caught; the
# inner-content alternation `.+?` is non-greedy so adjacent `<!-- bad -->`
# spans don't fuse.
_AVOID_MARKER_RE = re.compile(r"<!--\s*bad\s*-->(.+?)<!--\s*/bad\s*-->", re.DOTALL)
# True-false grammar statements often teach contrast as "X, а не Y." / "X, not Y."
# The Y form can be intentionally malformed and absent from VESUM. This safety
# net is deliberately narrow: it only strips the sentence-final tail after an
# explicit comma + negator, and only in true-false statements that are otherwise
# VESUM-checked.
_TF_NEGATIVE_EXAMPLE_RE = re.compile(
    r"(?:,\s*(?:а\s+)?не|,\s*not)\s+([\w'’ʼ-]+)\s*[.!?]",
    re.UNICODE | re.IGNORECASE,
)
# Anti-example contrast patterns in pedagogical prose. Writers use these to
# show learners "say X, not Y" — Y is intentionally the wrong form and must
# be excluded from VESUM lookup (it's NOT a valid Ukrainian word; VESUM would
# correctly fail it, but the writer's pedagogical intent is to show it as
# wrong, not to assert it as Ukrainian).
#
# Four surface forms supported, both English and Ukrainian negators:
#   1. Straight quotes:    `not "дивюся"`   /  `не "завтрак"`
#   2. Guillemets:         `not «дивюся»`   /  `не «завтрак»`
#   3. Closed markdown italics: `not *дивюся*` / `не *завтрак*`
#   4. Unclosed italic terminated by sentence punctuation:
#        `not *дивюся.`  /  `не *завтрак,`  /  `not *дивюся` (end-of-string)
#
# #2038 originally shipped quote-only. PR #2076 added closed-italic. The
# unclosed-italic variant was added 2026-05-17 after a1/m20 rebuild #4
# surfaced `*дивюся` (no closing `*` — the writer typed
# `not *дивюся.` inside a JSON `"explanation"` field, where the sentence-
# ending period takes the role of the closing italic marker).
#
# Strikethrough, bold, and explicit ❌ markers are NOT matched here —
# extend alternation rather than introducing new constants.
#
# Bold (`**X**`) is intentionally excluded. Writers reserve bold for the
# CORRECT form (the structural emphasis: "**л**" is the epenthetic
# consonant being taught). Matching bold here would strip the very tokens
# we want VESUM to verify.
#
# Citation/example frame (#3132): a foreign/Russian term CITED as an example in
# decolonization prose — `як «лєший»`, `such as «X»`, `like «X»` — is a mention,
# not a use, and лєший is correctly absent from VESUM (the Ukrainian is лісовик).
# Unlike the negator frame this arm is restricted to «» guillemets (the Ukrainian
# citation mark): the negator `не/not` already explicitly marks the form wrong, so
# it is allowed to strip any quote style; `як/as/like` is a weaker "such as"
# signal, so it requires the strong «»-citation mark and will NOT exempt a
# straight-quoted or italicised span. A bare (un-cited) invalid form still fails
# unless the seminar-only verified-primary citation guard below can resolve the
# exact normalized token back to the module's quote-fidelity-verified primary.
_WARNING_QUOTE_RE = re.compile(
    r"\b(?:"
    # Negator frame ("say X, not Y") — Y is marked wrong; all three quote styles.
    # The unclosed-italic arm requires the inner span to be Cyrillic-only (no
    # asterisk, whitespace, or punctuation) so it stops cleanly at the next
    # boundary instead of swallowing the rest of the sentence.
    r"(?:not|не)\s+(?:"
    r'["«][^"»]+["»]'
    r"|\*[^*\n]+?\*"
    r"|\*[A-Za-zА-ЯІЇЄҐа-яіїєґ\'ʼ-]+"
    r")"
    # Citation/example frame ("як «X»", "such as «X»") — «»-guillemets only.
    r"|(?:як|such\s+as|as|like)\s+«[^»]+»"
    r")",
    re.IGNORECASE,
)
_BARE_PRIMARY_CITATION_WORD_BOUNDARY = r"0-9A-Za-zА-Яа-яҐґЄєІіЇї_ʼ’'-"
_BARE_PRIMARY_CITATION_RE = re.compile(
    r"«(?P<guillemet>[^»\n]+)»"
    r"|(?<![" + _BARE_PRIMARY_CITATION_WORD_BOUNDARY + r"])'"
    r"(?P<single>(?:[^'\n]|'(?=[" + _BARE_PRIMARY_CITATION_WORD_BOUNDARY + r"]))+)'"
    r"(?![" + _BARE_PRIMARY_CITATION_WORD_BOUNDARY + r"])"
)
_BARE_PRIMARY_CITATION_GROUPS = ("guillemet", "single")

_STANDALONE_POSTFIX_FRAGMENTS = frozenset({"ся", "сь", "тся", "тсь", "ться", "шся", "шсь", "чся", "чсь"})

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
# sentence punctuation (including Ukrainian `…`, `‼`, `⁇`, `⁈`, `⁉`) with
# optional closing markdown/quote marks, markdown hard line breaks, plus
# markdown structure that makes adjacent lines independent prose units.
# The zero-width structural branch preserves line markers in the returned
# chunks and requires re.MULTILINE so `^` anchors each line, including quoted
# dialogue turns at the top of a body.
_SENTENCE_SPLIT_RE = re.compile(
    r"[.!?…‼⁇⁈⁉]+(?:[*_~\"'»”)\]]{0,4})(?:\s+|$)| {2,}\n+|\n\s*\n+|"
    r"(?=^[\s«“\"']*(?:[—–-]\s*(?:\*\*)?|\|\s*|[*-]\s+|\d+\.\s+|>\s*|#{1,6}\s+))",
    re.MULTILINE,
)

# Activity fields whose values are intentionally misspelled — students correct
# them. Excluded from VESUM lookup only for error-correction activities.
_ERROR_CORRECTION_TYPE = "error-correction"
_ERROR_CORRECTION_INTENTIONAL_FIELDS = frozenset(
    {"error", "errors", "errorWord", "error_word", "explanation", "sentence"}
)
_HIGHLIGHT_MORPHEMES_TYPE = "highlight-morphemes"
_HIGHLIGHT_MORPHEMES_ANSWER_KEY_FIELDS = frozenset({"morphemes"})
_ERROR_CORRECTION_REQUIRED_ITEM_FIELDS = frozenset({"sentence", "error"})
_ERROR_CORRECTION_OPTIONAL_ITEM_FIELDS = frozenset({"answer", "correction", "options", "explanation"})
_ACTIVITY_ITEM_AUTHORING_FIELDS: dict[str, frozenset[str]] = {
    _ERROR_CORRECTION_TYPE: (_ERROR_CORRECTION_REQUIRED_ITEM_FIELDS | _ERROR_CORRECTION_OPTIONAL_ITEM_FIELDS),
}
_ACTIVITY_ITEM_REQUIRED_FIELDS: dict[str, frozenset[str]] = {
    _ERROR_CORRECTION_TYPE: _ERROR_CORRECTION_REQUIRED_ITEM_FIELDS,
}
_ACTIVITY_ITEM_FORBIDDEN_ALIASES: dict[str, dict[str, str]] = {
    _ERROR_CORRECTION_TYPE: {
        "wrong": "error",
        "incorrect": "error",
        "mistake": "error",
        "bad": "error",
        "original": "error",
        "wrong_form": "error",
        "incorrect_form": "error",
        "correct": "correction",
        "correctAnswer": "correction",
        "right": "correction",
        "fix": "correction",
        "fixed": "correction",
    },
}
_ACTIVITY_ITEM_FIELD_PURPOSES: dict[str, str] = {
    "sentence": "the sentence containing the error",
    "error": "the misspelled form",
    "correction": "the corrected form",
    "answer": "the corrected form",
}
_ACTIVITY_EXPLANATION_REQUIRED_TYPES = frozenset({"quiz", "translate"})
_VESUM_ABBREVIATION_RE = re.compile(r"\bдіал\.", re.IGNORECASE)

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


def _normalize_curriculum_profile(raw_type: object) -> str | None:
    value = str(raw_type or "").strip().casefold()
    if value == "core":
        return "core"
    if value in {"seminar", "track"}:
        return "seminar"
    return value or None


def curriculum_profile_for_level(
    level_code: str | None,
    *,
    curriculum_manifest: Path | None = None,
) -> str | None:
    """Resolve a curriculum profile from ``curriculum.yaml``.

    ``type: track`` is the current manifest spelling for seminar tracks.
    Missing or unknown entries return ``None`` so QG gating fails closed.
    """
    if not level_code:
        return None
    key = str(level_code).strip().casefold()
    if not key:
        return None
    manifest_path = curriculum_manifest or (
        PROJECT_ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    )
    data = load_yaml(manifest_path)
    if not isinstance(data, Mapping):
        return None
    levels = data.get("levels")
    if not isinstance(levels, Mapping):
        return None
    entry = levels.get(key)
    if not isinstance(entry, Mapping):
        return None
    return _normalize_curriculum_profile(entry.get("type"))


def plan_path_for(level: str, slug: str) -> Path:
    return PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / level / f"{slug}.yaml"


def _legacy_section_points(section: Mapping[str, Any]) -> list[str]:
    """Return writer points for legacy B2 plan sections without mutating plans."""
    raw_subsections = section.get("subsections")
    points: list[str] = []
    if isinstance(raw_subsections, str):
        points.extend(
            part.strip()
            for part in re.split(r"\s+-\s+|\n+", raw_subsections)
            if part.strip()
        )
    elif isinstance(raw_subsections, list):
        points.extend(str(part).strip() for part in raw_subsections if str(part).strip())

    raw_concepts = section.get("key_concepts")
    if isinstance(raw_concepts, list):
        concepts = [str(concept).strip() for concept in raw_concepts if str(concept).strip()]
        if concepts:
            points.append("Ключові поняття: " + ", ".join(concepts))

    return points


def _legacy_reference_title(reference: Any) -> str | None:
    if isinstance(reference, str):
        return reference.strip() or None
    if isinstance(reference, Mapping):
        for key in ("source", "title", "file", "topic"):
            value = reference.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        if len(reference) == 1:
            key, value = next(iter(reference.items()))
            key_text = str(key).strip()
            value_text = str(value).strip()
            if key_text and value_text:
                return f"{key_text}: {value_text}"
            if key_text:
                return key_text
    return None


def _normalize_legacy_plan_shape(plan: dict[str, Any]) -> None:
    """Normalize locked legacy B2 plan fields into the V7 in-memory contract."""
    if str(plan.get("level") or "").strip().casefold() != "b2":
        return

    sections = plan.get("content_outline")
    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, dict):
                continue
            points = section.get("points")
            if isinstance(points, list) and all(isinstance(point, str) for point in points):
                continue
            legacy_points = _legacy_section_points(section)
            if legacy_points:
                section["points"] = legacy_points

    references = plan.get("references")
    if isinstance(references, list):
        for index, reference in enumerate(references):
            if isinstance(reference, str):
                title = _legacy_reference_title(reference)
                if title:
                    references[index] = {"title": title}
                continue
            if isinstance(reference, dict) and not reference.get("title"):
                title = _legacy_reference_title(reference)
                if title:
                    reference["title"] = title


def load_plan(plan_path: Path) -> dict[str, Any]:
    data = load_yaml(plan_path)
    if not isinstance(data, dict):
        raise LinearPipelineError(f"Plan must be a mapping: {plan_path}")
    _normalize_legacy_plan_shape(data)
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
        if not isinstance(section.get("words"), int) or section["words"] < 0:
            raise LinearPipelineError(f"Plan section {section['section']!r} has invalid words")
        points = section.get("points")
        if not isinstance(points, list) or not all(isinstance(p, str) for p in points):
            raise LinearPipelineError(f"Plan section {section['section']!r} must have string points")

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


def build_knowledge_packet(
    plan_path: Path | None = None,
    *,
    level: str | None = None,
    slug: str | None = None,
    plan: Mapping[str, Any] | None = None,
) -> str:
    """Build the writer knowledge packet from compiled wiki articles.

    The legacy implementation delegated to
    ``scripts.build.research.build_knowledge_packet`` and Qdrant. V7's source
    of truth is the compiled wiki plus sibling source registries, so this
    reader keeps the public return shape as markdown while removing the vector
    retrieval dependency.
    """
    if plan is None:
        if plan_path is None:
            if level is None or slug is None:
                raise LinearPipelineError("build_knowledge_packet requires plan_path or level+slug")
            plan_path = plan_path_for(level.lower(), slug)
        plan_data = load_plan(plan_path)
    else:
        plan_data = dict(plan)

    validate_plan(plan_data)
    level_key = str(level or plan_data["level"]).lower()
    slug_key = str(slug or plan_data["slug"]).strip()
    if not slug_key:
        raise LinearPipelineError("Plan slug must be non-empty")

    wiki_packet = _build_wiki_packet(level_key, slug_key)

    from scripts.build.phases.wiki_compressor import compress_wiki_packet

    compressed = compress_wiki_packet(plan_data, wiki_packet)
    dictionary_context = _build_dictionary_context(plan_data)
    textbook_context = _build_textbook_excerpt_context(plan_data, level_key)
    return _render_wiki_knowledge_packet(
        plan_data,
        wiki_packet,
        compressed,
        dictionary_context,
        textbook_context,
    )


def build_wiki_manifest_data(
    plan_path: Path | None = None,
    *,
    level: str | None = None,
    slug: str | None = None,
    plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the deterministic Wiki Obligations Manifest for one module."""
    if plan is None:
        if plan_path is None:
            if level is None or slug is None:
                raise LinearPipelineError("build_wiki_manifest_data requires plan_path or level+slug")
            plan_path = plan_path_for(level.lower(), slug)
        plan_data = load_plan(plan_path)
    else:
        plan_data = dict(plan)
    validate_plan(plan_data)

    level_key = str(level or plan_data["level"]).lower()
    slug_key = str(slug or plan_data["slug"]).strip()
    article_paths = _wiki_article_paths(level_key, slug_key)
    if not article_paths:
        raise LinearPipelineError(f"No wiki article found for level={level_key!r}, slug={slug_key!r}")
    from scripts.build.phases.wiki_manifest import extract_manifest, validate_manifest

    # Current module wiki layout resolves to one canonical article. If future
    # tracks add siblings, preserve deterministic order by merging list fields.
    merged: dict[str, Any] | None = None
    for article_path in article_paths:
        manifest = extract_manifest(article_path)
        if merged is None:
            merged = manifest
            continue
        for key in (
            "sequence_steps",
            "l2_errors",
            "phonetic_rules",
            "decolonization_bans",
            "wiki_vocabulary_minimum",
        ):
            merged.setdefault(key, [])
            for item in manifest.get(key, []):
                copied = dict(item)
                prefix = str(copied.get("id") or "").split("-", 1)[0] or key[:4]
                if "id" in copied:
                    copied["id"] = f"{prefix}-{len(merged[key]) + 1}"
                merged[key].append(copied)
        merged.setdefault("external_resources", [])
        merged["external_resources"].extend(manifest.get("external_resources", []))
        merged["wiki_path"] = f"{merged['wiki_path']}; {manifest['wiki_path']}"
    if merged is not None:
        validate_manifest(merged)
    return merged or {}


def run_wiki_completeness_gate(
    *,
    level: str,
    slug: str,
    wiki_manifest: Mapping[str, Any] | str | None = None,
) -> dict[str, Any]:
    """Run the V7.1 upstream wiki completeness gate for one module."""
    level_key = level.lower()
    slug_key = slug.strip()
    article_paths = _wiki_article_paths(level_key, slug_key)
    if not article_paths:
        raise LinearPipelineError(f"No wiki article found for level={level_key!r}, slug={slug_key!r}")
    from scripts.audit.wiki_completeness_gate import check_wiki_completeness

    # TODO(folk-seminar-gate): the module excerpt builder now retrieves
    # seminar primaries from literary_texts, but this completeness gate still
    # needs an in-process verify_quote adapter that accepts (source_id,
    # citation_context, source_mapping). The current implementation lives at
    # .mcp/servers/sources/server.py::handle_verify_quote and only accepts
    # author/text search arguments, so it cannot verify registry `file` chunk
    # ids without changing semantics.
    verify_quote_fn = None

    # Current build layout resolves to a single canonical wiki article. If a
    # future module has multiple articles, each must be complete enough to act
    # as the renderer spine; fail fast on the first thin article.
    reports = [
        check_wiki_completeness(path, level=level_key, slug=slug_key, verify_quote_fn=verify_quote_fn)
        for path in article_paths
    ]
    if len(reports) == 1:
        return reports[0]
    failed = [report for report in reports if report.get("verdict") != "PASS"]
    if failed:
        return failed[0]
    merged_report = dict(reports[0])
    merged_report["diagnostic"] = f"{len(reports)} wiki articles passed completeness gate."
    if wiki_manifest is not None:
        merged_report["wiki_manifest_slug"] = (
            wiki_manifest.get("slug")
            if isinstance(wiki_manifest, Mapping)
            else slug_key
        )
    return merged_report


PHONETIC_FORMAT_REFERENCE = (
    "Spoken target in `[...]` single-character square brackets, not Unicode look-alikes",
    "Pair written and spoken form in close lexical proximity (same sentence or adjacent bullet)",
    "Copy >=1 textbook example verbatim when the wiki provides one",
)


def _first_sentence(value: Any, *, max_chars: int = 260) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return ""
    match = re.search(r"(?<=[.!?])\s+", text)
    if match:
        text = text[: match.start()].strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _compact_wiki_manifest_for_prompt(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Render only write-time obligation IDs and summaries for the prompt."""
    sequence_steps = [
        {
            "id": str(item.get("id") or ""),
            "obligation_id": str(item.get("id") or ""),
            "category": "sequence_steps",
            "summary": _first_sentence(item.get("required_claim") or item.get("heading")),
        }
        for item in manifest.get("sequence_steps", [])
        if isinstance(item, Mapping)
    ]
    l2_errors = [
        {
            "id": str(item.get("id") or ""),
            "obligation_id": str(item.get("id") or ""),
            "category": "l2_errors",
            "summary": _first_sentence(
                f"Use {item.get('correct')} instead of {item.get('incorrect')}: {item.get('why')}",
                max_chars=340,
            ),
        }
        for item in manifest.get("l2_errors", [])
        if isinstance(item, Mapping)
    ]
    phonetic_rules = [
        {
            "id": str(item.get("id") or ""),
            "obligation_id": str(item.get("id") or ""),
            "category": "phonetic_rules",
            "written": str(item.get("written") or ""),
            "spoken": str(item.get("spoken") or ""),
        }
        for item in manifest.get("phonetic_rules", [])
        if isinstance(item, Mapping)
    ]
    decolonization_bans = [
        {
            "id": str(item.get("id") or ""),
            "obligation_id": str(item.get("id") or ""),
            "category": "decolonization_bans",
            "summary": _first_sentence(item.get("rule"), max_chars=320),
        }
        for item in manifest.get("decolonization_bans", [])
        if isinstance(item, Mapping)
    ]
    return {
        "slug": manifest.get("slug"),
        "wiki_path": manifest.get("wiki_path"),
        "phonetic_format_reference": list(PHONETIC_FORMAT_REFERENCE),
        "sequence_steps": sequence_steps,
        "l2_errors": l2_errors,
        "phonetic_rules": phonetic_rules,
        "decolonization_bans": decolonization_bans,
        "external_resources": manifest.get("external_resources", []),
    }


def _render_prompt_wiki_manifest(wiki_manifest: str | Mapping[str, Any]) -> str:
    if isinstance(wiki_manifest, Mapping):
        manifest = wiki_manifest
    else:
        try:
            manifest = json.loads(wiki_manifest)
        except json.JSONDecodeError:
            return wiki_manifest
        if not isinstance(manifest, Mapping):
            return wiki_manifest
    compact = _compact_wiki_manifest_for_prompt(manifest)
    return json.dumps(compact, ensure_ascii=False, indent=2)


def _manifest_mapping(wiki_manifest: str | Mapping[str, Any]) -> dict[str, Any] | None:
    if isinstance(wiki_manifest, Mapping):
        return dict(wiki_manifest)
    try:
        manifest = json.loads(wiki_manifest)
    except json.JSONDecodeError:
        return None
    if not isinstance(manifest, Mapping):
        return None
    return dict(manifest)


def build_wiki_coverage_obligation_checklist(
    wiki_manifest: str | Mapping[str, Any],
    *,
    seeded_map: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the structured checklist shared by generated prompts and gate."""
    from scripts.audit.wiki_coverage_gate import build_obligation_checklist_object

    return build_obligation_checklist_object(wiki_manifest, seeded_map=seeded_map)


def _render_wiki_coverage_required_items(
    wiki_manifest: str | Mapping[str, Any],
    *,
    obligation_checklist: Mapping[str, Any] | None = None,
) -> str:
    """Render a breakdown of required items for the writer prompt."""
    if obligation_checklist is not None:
        return _render_structured_wiki_coverage_required_items(obligation_checklist)

    if isinstance(wiki_manifest, str):
        try:
            manifest = json.loads(wiki_manifest)
        except json.JSONDecodeError:
            return ""
    else:
        manifest = wiki_manifest

    from scripts.audit.wiki_coverage_gate import (
        _extract_required_items,
        _normalize_required_claim,
    )

    lines = [
        "**Coverage rule**: every listed item MUST appear at least once in `module.md` PROSE (model sentence, definition, or paragraph). A vocab table entry alone is NOT coverage. Structural elements (tables, dialogue boxes) count for vocabulary but NOT for wiki_coverage obligations.",
        "",
    ]
    # Sequence steps
    vocab_items = [
        str(item.get("lemma") or "")
        for item in manifest.get("wiki_vocabulary_minimum", [])
        if isinstance(item, Mapping) and item.get("lemma")
    ]
    if vocab_items:
        lines.append("### wiki_vocabulary_minimum")
        lines.append("- Lemmas: " + ", ".join(vocab_items))
        lines.append("")

    # Sequence steps
    for item in manifest.get("sequence_steps", []):
        oid = str(item.get("id") or "")
        claim = str(item.get("required_claim") or item.get("heading") or "")
        if not claim:
            continue
        normalized = _normalize_required_claim(claim)
        extracted = _extract_required_items(normalized)

        if not (extracted["vocabulary"] or extracted["examples"]):
            continue

        lines.append(f"### {oid} (sequence step)")
        if extracted["vocabulary"]:
            lines.append(f"- Vocabulary to introduce: {', '.join(extracted['vocabulary'])}")
        if extracted["examples"]:
            lines.append(f"- Required examples: {', '.join(f'«{e}»' for e in extracted['examples'])}")
        lines.append(f"- Pedagogical goal: {normalized}")
        lines.append("")

    # L2 errors
    for item in manifest.get("l2_errors", []):
        oid = str(item.get("id") or "")
        incorrect = str(item.get("incorrect") or "")
        correct = str(item.get("correct") or "")
        why = str(item.get("why") or "")
        if not (incorrect or correct):
            continue

        lines.append(f"### {oid} (L2 error contrast)")
        lines.append(f"- Required contrast: incorrect `{incorrect}` vs correct `{correct}`")
        lines.append(f"- Pedagogical goal: {why}")
        if str(item.get("treatment")) == "contrast_pair":
             lines.append("- Required location: activities.yaml `error-correction` activity, entry with `sentence`, `error`, `correction` fields")
        lines.append("")

    return "\n".join(lines).strip()


def _render_structured_wiki_coverage_required_items(
    obligation_checklist: Mapping[str, Any],
) -> str:
    """Render the generator checklist object used by the gate."""
    from scripts.audit.wiki_coverage_gate import obligations_from_checklist

    lines = [
        "**Coverage rule**: every listed item MUST appear at least once in `module.md` PROSE (model sentence, definition, or paragraph). A vocab table entry alone is NOT coverage. Structural elements (tables, dialogue boxes) count for vocabulary but NOT for wiki_coverage obligations.",
        "",
    ]
    vocab_items = [
        str(item)
        for item in obligation_checklist.get("vocabulary_minimum", [])
        if str(item).strip()
    ]
    if vocab_items:
        lines.append("### wiki_vocabulary_minimum")
        lines.append("- Lemmas: " + ", ".join(vocab_items))
        lines.append("")

    for item in obligations_from_checklist(obligation_checklist):
        oid = str(item.get("id") or "")
        obligation_type = str(item.get("type") or "")
        if obligation_type == "sequence_step":
            lines.append(f"### {oid} (sequence step)")
            extracted = item.get("required_items")
            if isinstance(extracted, Mapping):
                vocabulary = [
                    str(value)
                    for value in extracted.get("vocabulary", [])
                    if str(value).strip()
                ]
                examples = [
                    str(value)
                    for value in extracted.get("examples", [])
                    if str(value).strip()
                ]
                if vocabulary:
                    lines.append(f"- Vocabulary to introduce: {', '.join(vocabulary)}")
                if examples:
                    lines.append(f"- Required examples: {', '.join(f'«{e}»' for e in examples)}")
            goal = str(item.get("normalized_claim") or item.get("required_claim") or item.get("heading") or "")
            if goal:
                lines.append(f"- Pedagogical goal: {goal}")
        elif obligation_type == "l2_error":
            incorrect = str(item.get("incorrect") or "")
            correct = str(item.get("correct") or "")
            why = str(item.get("why") or "")
            if not (incorrect or correct):
                continue
            lines.append(f"### {oid} (L2 error contrast)")
            lines.append(f"- Required contrast: incorrect `{incorrect}` vs correct `{correct}`")
            if why:
                lines.append(f"- Pedagogical goal: {why}")
            if str(item.get("treatment")) == "contrast_pair":
                lines.append("- Required location: activities.yaml `error-correction` activity, entry with `sentence`, `error`, `correction` fields")
        elif obligation_type == "phonetic_rule":
            written = str(item.get("written") or "")
            spoken = str(item.get("spoken") or "")
            if not (written or spoken):
                continue
            lines.append(f"### {oid} (phonetic rule)")
            lines.append(f"- Required mapping: written `{written}` -> spoken `{spoken}`")
            if item.get("examples"):
                lines.append(f"- Required examples: {json.dumps(item.get('examples'), ensure_ascii=False)}")
        elif obligation_type == "decolonization_ban":
            rule = str(item.get("rule") or "")
            if not rule:
                continue
            lines.append(f"### {oid} (decolonization ban)")
            if item.get("subtype"):
                lines.append(f"- Subtype: {item['subtype']}")
            lines.append(f"- Required rule: {rule}")
        else:
            lines.append(f"### {oid} ({obligation_type})")
        lines.append("")

    return "\n".join(lines).strip()


def build_wiki_manifest(
    plan_path: Path | None = None,
    *,
    level: str | None = None,
    slug: str | None = None,
    plan: Mapping[str, Any] | None = None,
) -> str:
    """Return compact JSON for the writer/reviewer manifest slot."""
    manifest = build_wiki_manifest_data(plan_path, level=level, slug=slug, plan=plan)
    return _render_prompt_wiki_manifest(manifest)


def _extract_dictionary_lemmas(plan: Mapping[str, Any]) -> list[str]:
    """Return required vocabulary lemmas for dictionary-context enrichment."""
    candidates: list[Any] = []
    required_vocab = plan.get("required_vocab")
    if isinstance(required_vocab, list):
        candidates = required_vocab
    else:
        vocab_hints = plan.get("vocabulary_hints")
        if isinstance(vocab_hints, dict):
            required = vocab_hints.get("required")
            if isinstance(required, list) and required:
                candidates = required
            else:
                for category in ("recommended", "sight_words"):
                    items = vocab_hints.get(category)
                    if isinstance(items, list):
                        candidates.extend(items)
        elif isinstance(vocab_hints, list):
            candidates = vocab_hints

    lemmas: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        lemma = _normalize_vocab_hint(item)
        if lemma and lemma not in seen:
            seen.add(lemma)
            lemmas.append(lemma)
    return lemmas


def _normalize_vocab_hint(item: Any) -> str:
    """Extract the Ukrainian lemma from a plan vocabulary hint item."""
    if isinstance(item, Mapping):
        raw = item.get("lemma") or item.get("word") or item.get("uk") or ""
    elif isinstance(item, str):
        raw = item
    else:
        return ""
    text = str(raw).split("(", 1)[0].strip()
    text = re.split(r"\s+[–—-]\s+", text, maxsplit=1)[0].strip()
    return text.strip(" \t\r\n,;:.")


def _build_dictionary_context(
    plan: Mapping[str, Any],
    *,
    max_chars: int = 6000,
    definition_chars: int = 200,
) -> str:
    """Build compact VESUM + dictionary context for plan vocabulary."""
    lemmas = _extract_dictionary_lemmas(plan)
    if not lemmas:
        return ""

    try:
        from scripts.verification import vesum as vesum_lookup
        from wiki import sources_db
    except Exception as exc:
        return f"## Dictionary context\n\n*Dictionary context unavailable: {type(exc).__name__}: {exc}*"

    try:
        batch_matches = vesum_lookup.verify_words(lemmas)
    except Exception:
        batch_matches = {lemma: [] for lemma in lemmas}

    lines = ["## Dictionary context", ""]
    current_chars = sum(len(line) + 1 for line in lines)
    for lemma in lemmas:
        word_matches = batch_matches.get(lemma, [])
        forms = _safe_lookup(vesum_lookup.verify_lemma, [], lemma)
        definitions = _safe_lookup(sources_db.search_definitions, [], lemma, limit=1)
        style_notes = _safe_lookup(sources_db.search_style_guide, [], lemma, limit=1)

        pos = _dictionary_pos_label(word_matches, forms)
        entry = [
            f"- **{lemma}** [{pos}]",
            f"  - VESUM: {_vesum_form_summary(lemma, word_matches, forms)}",
        ]
        definition = _dictionary_hit_text(definitions)
        if definition:
            entry.append(f"  - Definition: {_truncate_prompt_text(definition, definition_chars)}")
        else:
            entry.append("  - Definition: Not found in SUM-11.")

        style_note = _dictionary_hit_text(style_notes)
        if style_note:
            entry.append(f"  - Style note: {_truncate_prompt_text(style_note, definition_chars)}")

        entry_chars = sum(len(line) + 1 for line in entry)
        if current_chars + entry_chars <= max_chars:
            lines.extend(entry)
            current_chars += entry_chars
            continue

        short_entry = f"- **{lemma}** [{pos}]"
        if current_chars + len(short_entry) + 1 <= max_chars:
            lines.append(short_entry)
            current_chars += len(short_entry) + 1
        else:
            break

    return "\n".join(lines).rstrip()


def _safe_lookup(fn: Callable[..., Any], fallback: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except Exception:
        return fallback


def _dictionary_pos_label(word_matches: list[dict], forms: list[dict]) -> str:
    values: list[str] = []
    for item in [*word_matches, *forms]:
        pos = str(item.get("pos") or "").strip()
        if pos and pos not in values:
            values.append(pos)
    return ", ".join(values) if values else "unknown"


def _vesum_form_summary(lemma: str, word_matches: list[dict], forms: list[dict]) -> str:
    if word_matches:
        match = word_matches[0]
        tags = str(match.get("tags") or "").strip()
        return f"{lemma}" + (f" (`{tags}`)" if tags else "")
    if forms:
        form = forms[0]
        word_form = str(form.get("word_form") or lemma).strip()
        tags = str(form.get("tags") or "").strip()
        return f"{word_form}" + (f" (`{tags}`)" if tags else "")
    return "Not found in VESUM."


def _dictionary_hit_text(hits: Any) -> str:
    if not isinstance(hits, list) or not hits:
        return ""
    first = hits[0]
    if not isinstance(first, Mapping):
        return str(first)
    for key in ("definition", "definitions", "text", "note", "notes"):
        value = first.get(key)
        if value:
            return str(value)
    return ""


def _truncate_prompt_text(text: str, max_chars: int) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    trimmed = cleaned[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"{trimmed}..."


def _plan_topic_query(plan: Mapping[str, Any]) -> str:
    parts = [
        str(plan.get("title") or ""),
        str(plan.get("subtitle") or ""),
    ]
    for section in plan.get("content_outline") or []:
        if isinstance(section, Mapping):
            parts.append(str(section.get("section") or ""))
            points = section.get("points")
            if isinstance(points, list):
                parts.extend(str(point) for point in points[:3])
    return " ".join(part.strip() for part in parts if part and part.strip())


def _textbook_hit_text(hit: Mapping[str, Any], max_chars: int = 1400) -> str:
    for key in ("text", "content", "excerpt", "snippet", "body"):
        value = hit.get(key)
        if value:
            return _truncate_prompt_text(str(value), max_chars)
    return ""


def _textbook_hit_label(hit: Mapping[str, Any]) -> str:
    title = str(hit.get("title") or hit.get("section_title") or "Textbook").strip()
    details: list[str] = []
    author = str(hit.get("author") or "").strip()
    if author and author not in title:
        details.append(author)
    grade = hit.get("grade")
    if grade not in (None, ""):
        details.append(f"Grade {grade}")
    page = hit.get("page")
    if page not in (None, ""):
        details.append(f"p.{page}")
    source_file = str(hit.get("source_file") or hit.get("source") or "").strip()
    if source_file:
        details.append(source_file)
    return title + (f" ({', '.join(details)})" if details else "")


_TEXTBOOK_REFERENCE_TITLE_RE = re.compile(
    r"^(?P<author>\S+)\s+Grade\s+(?P<grade>\d+),\s*p\.\s*(?P<page>\d+)$",
    re.IGNORECASE,
)

# Cyrillic spelling-variant canonicalization. Maps non-canonical Cyrillic
# author spellings (regional/historical variants like Литвінова or the
# soft-sign-bearing Пономарьова) to the canonical form stored in
# textbooks.author_uk. This is NOT transliteration — it never crosses
# writing systems. Add entries only when a real plan citation surfaces a
# variant spelling not in textbooks.author_uk.
_CYRILLIC_AUTHOR_CANONICAL: dict[str, str] = {
    "Литвінова": "Літвінова",
    "Пономарьова": "Пономарова",
}

# Historical: an _TEXTBOOK_AUTHOR_TRANSLITS dict lived here and mapped
# Cyrillic plan-author names to Latin source_file fragments. It is gone:
# the matcher now queries textbooks.author_uk directly (Cyrillic-native).
# The Latin→Cyrillic bridge survives only in
# scripts/migrations/2026-05-15-add-author-uk-to-textbooks.py for the
# one-time back-fill of historical rows. See ADR
# docs/decisions/2026-05-15-cyrillic-native-matcher.md.


def _canonicalize_author_uk(author: str) -> str:
    """Map a Cyrillic author name to its canonical form (handles spelling variants).

    Pure Cyrillic-to-Cyrillic mapping; never crosses writing systems.
    """
    return _CYRILLIC_AUTHOR_CANONICAL.get(author, author)


def _parse_textbook_reference_title(title: str) -> tuple[str, int, int] | None:
    match = _TEXTBOOK_REFERENCE_TITLE_RE.match(title.strip())
    if not match:
        return None
    return (
        match.group("author"),
        int(match.group("grade")),
        int(match.group("page")),
    )


def _textbook_source_year(source_file: str) -> int:
    years = [int(year) for year in re.findall(r"(?:^|-)(\d{4})(?:-|$)", source_file)]
    return max(years) if years else 0


def _source_files_for_textbook_reference(
    conn: sqlite3.Connection,
    author: str,
    grade: int,
) -> list[str] | None:
    """Resolve source_files for a Cyrillic-author + grade citation.

    Queries textbooks.author_uk directly — no transliteration, no
    LIKE patterns. Returns None if the author has no rows at any grade
    (treated as "unknown author"), [] if rows exist for the author but
    not at this grade, or a non-empty list of source_files.
    """
    canonical = _canonicalize_author_uk(author)
    has_any_rows = conn.execute(
        "SELECT 1 FROM textbooks WHERE author_uk = ? LIMIT 1",
        (canonical,),
    ).fetchone()
    if has_any_rows is None:
        return None

    rows = conn.execute(
        """
        SELECT DISTINCT source_file
        FROM textbooks
        WHERE author_uk = ?
          AND grade = ?
        """,
        (canonical, str(grade)),
    ).fetchall()
    return sorted(
        (str(row["source_file"]) for row in rows),
        key=lambda source_file: (_textbook_source_year(source_file), source_file),
        reverse=True,
    )


def _lookup_textbook_reference_chunk(
    title: str,
    *,
    limit: int = 1,
    missing_reason: list[str] | None = None,
) -> list[dict] | None:
    parsed = _parse_textbook_reference_title(title)
    if parsed is None:
        return None
    author, grade, page = parsed
    if not TEXTBOOK_SOURCES_DB_PATH.exists():
        return None

    try:
        with sqlite3.connect(str(TEXTBOOK_SOURCES_DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            source_files = _source_files_for_textbook_reference(conn, author, grade)
            if source_files is None:
                return None
            if not source_files:
                if missing_reason is not None:
                    missing_reason.append(f"source_file not in corpus for {author} Grade {grade}")
                return []
            quoted_sources = ",".join("?" for _ in source_files)
            rows: list[sqlite3.Row] = []
            for width in (4, 3):
                suffix = f"\\_s{page:0{width}d}"
                rows = conn.execute(
                    f"""
                    SELECT chunk_id, title, text, source_file, grade, author
                    FROM textbooks
                    WHERE source_file IN ({quoted_sources})
                      AND chunk_id LIKE ? ESCAPE '\\'
                    ORDER BY source_file DESC, chunk_id
                    """,
                    (*source_files, f"%{suffix}"),
                ).fetchall()
                if rows:
                    break
    except sqlite3.Error:
        return None

    if not rows:
        if missing_reason is not None:
            missing_reason.append(f"page {page} not in corpus for {', '.join(source_files)}")
        return []

    source_file_count = len({str(row["source_file"]) for row in rows})
    if source_file_count > 1:
        LOGGER.warning(
            "Ambiguous textbook source_file candidates for %s: %s; using most recent",
            title,
            ", ".join(sorted({str(row["source_file"]) for row in rows})),
        )
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            _textbook_source_year(str(row["source_file"])),
            str(row["source_file"]),
            str(row["chunk_id"]),
        ),
        reverse=True,
    )
    return [
        {
            "chunk_id": str(row["chunk_id"]),
            "title": str(row["title"]),
            "text": str(row["text"]),
            "source_file": str(row["source_file"]),
            "source_type": "textbook",
            "grade": str(row["grade"]),
            "author": str(row["author"] or author),
            "page": page,
        }
        for row in sorted_rows[:limit]
    ]


def _search_textbook_hits(query: str, *, level: str, limit: int = 1) -> list[dict]:
    direct_hits = _lookup_textbook_reference_chunk(query, limit=limit)
    if direct_hits is not None:
        return direct_hits

    try:
        from wiki.sources_db import search_sources
    except Exception:
        return []
    try:
        hits = search_sources(query, track=level, limit=max(limit * 4, limit))
    except Exception:
        return []
    textbook_hits = [
        hit
        for hit in hits
        if isinstance(hit, dict)
        and "textbook" in str(hit.get("source_type") or hit.get("corpus") or hit.get("source") or "").casefold()
    ]
    return textbook_hits[:limit]


_SOURCE_SEARCH_TERM_RE = re.compile(r"[A-Za-zА-Яа-яІіЇїЄєҐґ0-9]{3,}")
_PRIMARY_TEXT_QUOTE_RES = (
    re.compile(r"«(.{8,160}?)»"),
    re.compile(r"“(.{8,160}?)”"),
    re.compile(r'"(.{8,160}?)"'),
)


def _source_search_terms(query: str) -> set[str]:
    return {term.casefold() for term in _SOURCE_SEARCH_TERM_RE.findall(query)}


def _literary_fallback_queries(
    plan: Mapping[str, Any],
    reference: Mapping[str, Any],
    fallback_query: str,
) -> list[str]:
    queries: list[str] = []
    for section in plan.get("content_outline") or []:
        if not isinstance(section, Mapping):
            continue
        for point in section.get("points") or []:
            point_text = str(point or "")
            for quote_re in _PRIMARY_TEXT_QUOTE_RES:
                for match in quote_re.finditer(point_text):
                    quote = match.group(1).replace("...", " ").replace("…", " ").strip(" .,:;!?")
                    if len(_source_search_terms(quote)) >= 2:
                        queries.append(quote)

    reference_query = " ".join(
        str(reference.get(key) or "").strip()
        for key in ("title", "author", "work", "note")
        if str(reference.get(key) or "").strip()
    )
    if reference_query:
        queries.append(reference_query)
    queries.append(fallback_query)
    return list(dict.fromkeys(queries))


def _is_literary_source_hit(hit: Mapping[str, Any]) -> bool:
    source_type = str(hit.get("source_type") or "").casefold()
    source_marker = " ".join(
        str(hit.get(key) or "").casefold()
        for key in ("source_type", "corpus", "source", "unit_key")
    )
    return (
        "textbook" not in source_marker
        and (
            "literary" in source_marker
            or "literary_texts" in source_marker
            or source_type == "primary"
        )
    )


def _normalize_literary_hit(hit: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(hit)
    normalized.setdefault("source_type", "literary")
    normalized.setdefault("corpus", "literary_texts")
    if not normalized.get("title") and normalized.get("work"):
        normalized["title"] = normalized["work"]
    return normalized


def _search_literary_hits(query: str, *, level: str, limit: int = 1) -> list[dict]:
    try:
        from wiki import sources_db
    except Exception:
        return []

    candidate_limit = max(limit * 4, limit)
    search_literary = getattr(sources_db, "search_literary", None)
    if callable(search_literary):
        terms = _source_search_terms(query)
        if terms:
            try:
                hits = search_literary(terms, max_total=candidate_limit)
            except TypeError:
                try:
                    hits = search_literary(terms, limit=candidate_limit)
                except Exception:
                    hits = []
            except Exception:
                hits = []
            literary_hits = [
                _normalize_literary_hit(hit)
                for hit in hits or []
                if isinstance(hit, Mapping) and _is_literary_source_hit(hit)
            ]
            if literary_hits:
                return literary_hits[:limit]

    search_sources = getattr(sources_db, "search_sources", None)
    if not callable(search_sources):
        return []
    try:
        hits = search_sources(query, track=level, limit=candidate_limit)
    except Exception:
        return []
    literary_hits = [
        _normalize_literary_hit(hit)
        for hit in hits or []
        if isinstance(hit, Mapping) and _is_literary_source_hit(hit)
    ]
    return literary_hits[:limit]


def _build_textbook_excerpt_context(
    plan: Mapping[str, Any],
    level: str,
) -> str:
    references = [str(title).strip() for title in extract_plan_reference_titles(plan) if str(title).strip()]
    if not references:
        return ""

    topic_query = _plan_topic_query(plan)
    lines = ["## Textbook Excerpts (verbatim, must be cited)", ""]
    level_key = str(level).lower()
    references_by_title = {
        str(ref.get("title") or "").strip(): ref
        for ref in plan.get("references") or []
        if isinstance(ref, Mapping)
    }
    found_any = False
    for title in references:
        reference = references_by_title.get(title, {})
        is_primary_reference = str(reference.get("type") or "").casefold() == "primary"
        query = f"{title} {topic_query}".strip()
        missing_reasons: list[str] = []
        direct_hits = _lookup_textbook_reference_chunk(
            title,
            limit=1,
            missing_reason=missing_reasons,
        )
        hits = direct_hits if direct_hits is not None else _search_textbook_hits(query, level=level, limit=1)
        hit_source = "textbook"
        if not hits and level_key in SEMINAR_LEVELS and is_primary_reference:
            for literary_query in _literary_fallback_queries(plan, reference, query):
                hits = _search_literary_hits(literary_query, level=level_key, limit=1)
                if hits:
                    hit_source = "literary"
                    break
        lines.append(f"### {title}")
        lines.append("")
        if not hits:
            missing_reason = missing_reasons[0] if missing_reasons else ""
            for ref in plan.get("references") or []:
                if isinstance(ref, dict) and str(ref.get("title") or "").strip() == title:
                    ref["corpus_missing"] = True
                    if missing_reason:
                        ref["corpus_missing_reason"] = missing_reason
            lines.append("*No textbook excerpt found for this reference.*")
            lines.append("corpus_missing: true")
            if missing_reason:
                lines.append(f"corpus_missing_reason: {missing_reason}")
            lines.append("")
            continue
        hit = hits[0]
        text = _textbook_hit_text(hit)
        if not text:
            lines.append("*Textbook search returned metadata without excerpt text.*")
            lines.append("")
            continue
        found_any = True
        if hit_source == "literary":
            lines.append("Primary text (literary corpus)")
            chunk_id = str(hit.get("chunk_id") or "").strip()
            if chunk_id:
                lines.append(f"chunk_id: {chunk_id}")
        lines.append(f"Source: {_textbook_hit_label(hit)}")
        lines.append("")
        for quote_line in text.splitlines():
            lines.append(f"> {quote_line}")
        lines.append("")

    return "\n".join(lines).rstrip() if found_any or references else ""


def _build_wiki_packet(level: str, slug: str) -> str:
    """Build raw wiki context from exact module article(s) and source registries."""
    article_paths = _wiki_article_paths(level, slug)
    if not article_paths:
        raise LinearPipelineError(f"No wiki article found for level={level!r}, slug={slug!r}")

    from wiki.config import WIKI_DIR
    from wiki.context import strip_meta
    from wiki.sources_schema import load_sources_registry, registry_path_for

    parts: list[str] = []
    for article_path in article_paths:
        rel_path = article_path.relative_to(WIKI_DIR)
        content = strip_meta(article_path.read_text(encoding="utf-8"))
        registry = load_sources_registry(registry_path_for(article_path))
        source_summary = _format_wiki_sources(registry.sources)
        source_block = f"\n\nSources: {source_summary}" if source_summary else ""
        parts.append(f"### Вікі: {rel_path}\n\nArticle: `wiki/{rel_path}`\n\n{content}{source_block}")

    body = "\n\n---\n\n".join(parts)
    return (
        "<wiki_context>\n"
        "## Compiled Wiki Knowledge\n\n"
        "The following project wiki articles provide the authoritative module "
        "knowledge. They were compiled from textbooks, dictionaries, primary "
        "sources, external articles, and Ukrainian wiki material. Use their "
        "sibling `.sources.yaml` registries to resolve inline [S] citations.\n\n"
        f"{body}\n"
        "</wiki_context>"
    )


def _wiki_article_paths(level: str, slug: str) -> list[Path]:
    """Return exact wiki article paths for a level/slug pair."""
    from wiki.config import TRACK_DOMAINS, TRACK_WRITE_DOMAIN, WIKI_DIR

    domains: list[str] = []
    write_domain = TRACK_WRITE_DOMAIN.get(level)
    if write_domain:
        domains.append(write_domain)
    domains.extend(TRACK_DOMAINS.get(level, []))
    domains.append(level)

    seen_domains: set[str] = set()
    paths: list[Path] = []
    seen_paths: set[Path] = set()
    for domain in domains:
        if not domain or domain in seen_domains:
            continue
        seen_domains.add(domain)
        domain_dir = WIKI_DIR / domain
        if not domain_dir.exists():
            continue

        direct = domain_dir / f"{slug}.md"
        candidates = [direct] if direct.exists() else list(domain_dir.rglob(f"{slug}.md"))
        for candidate in candidates:
            if candidate.name == "index.md" or candidate in seen_paths:
                continue
            seen_paths.add(candidate)
            paths.append(candidate)
    return paths


def _format_wiki_sources(sources: list[Any]) -> str:
    """Render a compact source registry line for prompt inclusion."""
    entries: list[str] = []
    for source in sources:
        details = [f"{source.id}={source.file}", f"type={source.type}"]
        if source.title:
            details.append(f"title={source.title}")
        if source.page is not None:
            details.append(f"page={source.page}")
        if source.grade is not None:
            details.append(f"grade={source.grade}")
        if source.section_path:
            details.append(f"section={source.section_path}")
        entries.append(" (" + "; ".join(details) + ")")
    return ", ".join(entries)


def _render_wiki_knowledge_packet(
    plan: Mapping[str, Any],
    wiki_packet: str,
    compressed: Mapping[str, Any],
    dictionary_context: str = "",
    textbook_context: str = "",
) -> str:
    """Render raw and compressed wiki context as the writer packet."""
    lines: list[str] = [
        f"# Knowledge Packet: {plan['title']}",
        "",
        f"**Module:** {plan['module']} | **Level:** {plan['level']} | **Slug:** {plan['slug']}",
        "**Retrieval:** compiled wiki + MCP sources, no Qdrant",
        "",
        "## Targeted Wiki Excerpts by Plan Section",
        "",
    ]

    section_excerpts = compressed.get("section_excerpts") or {}
    for section in plan.get("content_outline") or []:
        title = str(section.get("section") or "").strip()
        if not title:
            continue
        lines.append(f"### {title}")
        lines.append("")
        items = section_excerpts.get(title) or []
        if not items:
            lines.append("*No compressed wiki excerpt matched this section.*")
            lines.append("")
            continue
        for item in items:
            lines.append(f"- **{item['citation']}**")
            lines.append(f"  {item['excerpt']}")
            lines.append("")

    anchors = compressed.get("factual_anchors") or []
    if anchors:
        lines.extend(["## Factual Anchors", ""])
        for anchor in anchors:
            lines.append(f"- **{anchor['section']}** — {anchor['claim']} ({anchor['citation']})")
        lines.append("")

    if dictionary_context:
        lines.extend([dictionary_context, ""])

    if textbook_context:
        lines.extend([textbook_context, ""])

    lines.extend(
        [
            "## MCP Dictionary Verification",
            "",
            "Use the canonical `sources` MCP tools for live dictionary checks:",
            "- `mcp__sources__verify_lemma` for VESUM morphology and inflections.",
            "- `mcp__sources__search_style_guide` for russianisms, surzhyk, calques, and paronym-risk phrases.",
            "- `mcp__sources__search_definitions` for СУМ-11 definitions and usage disambiguation.",
            "",
            "Verify suspicious forms before using them in prose, vocabulary, "
            "activities, or resources. Do not call legacy `scripts.rag` or "
            "Qdrant retrieval for this packet.",
            "",
            "## Compiled Wiki Context",
            "",
            "Raw compiled wiki prose is compressed into the targeted excerpts, "
            "factual anchors, Wiki Obligations Manifest, and Implementation Map "
            "above. Do not duplicate the full article text in the writer prompt.",
            "",
            "## Plan References",
            "",
        ]
    )
    for ref in plan.get("references") or []:
        title = str(ref.get("title") or "").strip()
        if not title:
            continue
        note = str(ref.get("notes") or "").strip()
        url = str(ref.get("url") or "").strip()
        line = f"- **{title}**"
        if note:
            line += f": {note}"
        if url:
            line += f" ({url})"
        lines.append(line)

    return "\n".join(lines).rstrip() + "\n"


def render_phase_prompt(template_path: Path, context: Mapping[str, Any]) -> str:
    """Render Phase 0 preamble placeholders and downstream ALL_CAPS tokens."""
    unknown = sorted(set(context) - DOWNSTREAM_TOKENS)
    if unknown:
        raise LinearPipelineError("Unknown downstream prompt context keys: " + ", ".join(unknown))

    rendered = render_prompt(template_path)
    for key, value in context.items():
        rendered = rendered.replace(f"{{{key}}}", str(value))

    unresolved = sorted(
        {match.group(1) for match in TOKEN_RE.finditer(rendered) if match.group(1) in DOWNSTREAM_TOKENS}
    )
    if unresolved:
        raise LinearPipelineError(f"Unresolved downstream prompt tokens in {template_path}: " + ", ".join(unresolved))
    return rendered


def writer_prompt_path(writer_family: str) -> Path:
    prompt_filename = PROMPT_BY_WRITER.get(writer_family, "linear-write.md")
    return PROJECT_ROOT / "scripts" / "build" / "phases" / prompt_filename


def generated_writer_prompt_path() -> Path:
    """V7.2 Step 5: the generator-fed writer template (opt-in --use-generator).

    Writer-family agnostic for now — the grok writer variant gets its own
    generated template in the full-parity follow-up (ADR sequencing step 5+).
    """
    return PROJECT_ROOT / "scripts" / "build" / "phases" / "linear-write.generated.md"


def generated_review_prompt_path() -> Path:
    """V7.2 Step 5: the generator-fed per-dimension reviewer template."""
    return PROJECT_ROOT / "scripts" / "build" / "phases" / "linear-review-dim.generated.md"


def writer_correction_prompt_path(writer_family: str) -> Path:
    prompt_filename = CORRECTION_PROMPT_BY_WRITER.get(
        writer_family,
        "linear-writer-correction.md",
    )
    return PROJECT_ROOT / "scripts" / "build" / "phases" / prompt_filename


def render_writer_prompt(
    *,
    plan: Mapping[str, Any],
    plan_content: str,
    knowledge_packet: str,
    plan_path: Path | None = None,
    wiki_manifest: str | Mapping[str, Any] | None = None,
    implementation_map: Mapping[str, Any] | None = None,
    writer: str = "claude-tools",
    use_generator: bool = False,
    obligation_checklist: Mapping[str, Any] | None = None,
) -> str:
    template_path = generated_writer_prompt_path() if use_generator else writer_prompt_path(writer)
    return render_phase_prompt(
        template_path,
        writer_context(
            plan,
            plan_content,
            knowledge_packet,
            wiki_manifest,
            plan_path=plan_path,
            implementation_map=implementation_map,
            writer=writer,
            use_generator=use_generator,
            obligation_checklist=obligation_checklist,
        ),
    )


def _writer_specific_directives(writer: str | None) -> str:
    if not writer:
        return ""
    return WRITER_SPECIFIC_DIRECTIVES.get(writer, "")


def emit_event(event: str, **fields: Any) -> None:
    """Emit one monitor-friendly JSONL event using the V6 event shape."""
    if _TELEMETRY_EVENT_SINK is not None:
        _TELEMETRY_EVENT_SINK(event, **fields)
        return
    line = json.dumps(
        {"event": event, "ts": datetime.now(UTC).isoformat(), **fields},
        ensure_ascii=False,
        default=str,
    )
    print(line, flush=True)


def _make_file_event_sink(path: Path) -> tuple[Callable[..., None], Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a", encoding="utf-8")

    def sink(event: str, **fields: Any) -> None:
        line = json.dumps(
            {"event": event, "ts": datetime.now(UTC).isoformat(), **fields},
            ensure_ascii=False,
            default=str,
        )
        handle.write(f"{line}\n")
        handle.flush()

    return sink, handle


@contextmanager
def telemetry_event_sink(path: Path | None):
    """Temporarily route JSONL telemetry to ``path`` in append mode."""
    global _TELEMETRY_EVENT_SINK

    previous = _TELEMETRY_EVENT_SINK
    sink: Callable[..., None] | None = None
    handle: Any = None
    try:
        if path is not None:
            sink, handle = _make_file_event_sink(path)
            _TELEMETRY_EVENT_SINK = sink
        yield
    finally:
        _TELEMETRY_EVENT_SINK = previous
        if handle is not None:
            handle.close()


def _emit(event_sink: Callable[..., None] | None, event: str, **fields: Any) -> None:
    sink = event_sink or emit_event
    sink(event, **fields)


def _emit_writer_rule_fired(
    event_sink: Callable[..., None] | None,
    *,
    rule_id: str,
    gate: str,
    evidence: str,
    level: str | None = None,
    slug: str | None = None,
    **fields: Any,
) -> None:
    payload = {
        "rule_id": rule_id,
        "gate": gate,
        "evidence": _clean_telemetry_text(evidence, 240),
        **fields,
    }
    if level:
        payload["level"] = level
    if slug:
        payload["slug"] = slug
    _emit(event_sink, "writer_rule_fired", **payload)


def _writer_rule_ids_for_gate_failure(
    gate: str,
    report: Mapping[str, Any],
) -> list[str]:
    if gate == "engagement_floor":
        return [RULE_VOICE_META] if report.get("meta_narration_hits") else []
    if gate == "scaffolding_leak":
        return [RULE_NO_SCAFFOLDING_LEAKS]
    if gate == "vesum_verified":
        return [RULE_VESUM_ALL_WORDS, RULE_BAD_FORM_MARKER]
    if gate == "bad_form_heritage":
        return [RULE_BAD_FORM_MARKER]
    if gate in {"russianisms_strict", "russianisms_clean", "surzhyk_clean", "calques_clean", "paronym_clean"}:
        return [RULE_BAD_FORM_MARKER]
    if gate == "citations_resolve":
        return [RULE_CITE_HONEST]
    if gate == "textbook_grounding":
        return [RULE_TEXTBOOK_30W]
    return []


def _writer_rule_evidence_for_gate(
    gate: str,
    report: Mapping[str, Any],
) -> str:
    if gate == "engagement_floor":
        hits = report.get("meta_narration_hits")
        if isinstance(hits, list):
            return ", ".join(str(hit) for hit in hits[:3])
    if gate == "scaffolding_leak":
        offending = report.get("offending")
        if isinstance(offending, list):
            return "; ".join(str(item) for item in offending[:3])
    if gate == "vesum_verified":
        missing = report.get("missing")
        if isinstance(missing, list):
            return "missing=" + ", ".join(str(item) for item in missing[:5])
        if report.get("error"):
            return str(report["error"])
    if gate == "bad_form_heritage":
        findings = report.get("findings")
        if isinstance(findings, list) and findings:
            return "; ".join(str(item) for item in findings[:3])
        if report.get("error"):
            return str(report["error"])
    if gate == "russianisms_strict":
        findings = report.get("critical_findings")
        if isinstance(findings, list) and findings:
            first = findings[0]
            if isinstance(first, Mapping):
                return str(
                    first.get("text") or first.get("match") or first.get("pattern") or first.get("note") or first
                )
    if gate in {"russianisms_clean", "surzhyk_clean", "calques_clean", "paronym_clean"}:
        detections = report.get("detections")
        if isinstance(detections, list) and detections:
            first = detections[0]
            if isinstance(first, Mapping):
                return str(first.get("text") or first.get("pattern") or first)
    if gate == "citations_resolve":
        unknown = report.get("unknown")
        if isinstance(unknown, list):
            return "unknown=" + ", ".join(str(item) for item in unknown[:5])
    if gate == "textbook_grounding":
        return (
            f"long_blockquotes_checked={report.get('long_blockquotes_checked')}; "
            f"min_words={report.get('min_words')}; missing={report.get('missing')}"
        )
    return str(report)


def _correction_preview(text: Any, limit: int = CORRECTION_PREVIEW_CHARS) -> str:
    return str(text or "")[:limit]


def _module_ref_from_module_dir(module_dir: Path) -> str | None:
    match = re.match(r"^(?P<sequence>\d+)-", module_dir.name)
    if not match:
        return None
    return _module_ref(module_dir.parent.name, match.group("sequence"))


def _correction_event_fields(
    *,
    gate: str,
    module_dir: Path,
    plan_path: Path,
) -> dict[str, str]:
    fields = {
        "gate": gate,
        "module_dir": str(module_dir),
        "plan_path": str(plan_path),
    }
    module = _module_ref_from_module_dir(module_dir)
    if module is not None:
        fields["module"] = module
    return fields


def _module_ref(level: str | None, module_num: str | int | None) -> str | None:
    if not level or module_num is None:
        return None
    raw_num = str(module_num).strip()
    if not raw_num:
        return None
    try:
        module_part = str(int(raw_num))
    except ValueError:
        module_part = raw_num.lower()
    return f"{level.strip().lower()}/{module_part}"


def _prompt_module_ref(prompt: str) -> str | None:
    level_match = re.search(r"^\s*-\s*Level:\s*(?P<level>\S+)\s*$", prompt, re.MULTILINE)
    module_match = re.search(r"^\s*-\s*Module:\s*(?P<module>\S+)\s*$", prompt, re.MULTILINE)
    if not level_match or not module_match:
        return None
    return _module_ref(level_match.group("level"), module_match.group("module"))


def _prompt_sections(prompt: str) -> list[str]:
    match = re.search(
        r"##\s+Contract YAML\s*```yaml\s*(?P<body>.*?)```",
        prompt,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return []
    try:
        contract = yaml.safe_load(match.group("body")) or {}
    except yaml.YAMLError:
        return []
    sections = contract.get("sections") if isinstance(contract, Mapping) else None
    if not isinstance(sections, list):
        return []
    titles: list[str] = []
    for section in sections:
        if isinstance(section, Mapping):
            title = str(section.get("title") or section.get("section") or "").strip()
            if title:
                titles.append(title)
    return titles


def _clean_telemetry_text(value: Any, max_chars: int = 120) -> str:
    text = re.sub(r"\s+", " ", str(value)).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:") + "..."


def _section_key(section: str | None) -> str:
    if not section:
        return ""
    return re.sub(r"\W+", "_", section.casefold()).strip("_")


def _reasoning_section_from_body(body: str) -> str | None:
    match = re.search(r"^\s*section\s*:\s*(?P<section>.+?)\s*$", body, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    return match.group("section").strip(" *`\"'")


def _reasoning_fields_filled(body: str) -> list[str]:
    filled: list[str] = []
    for field in PROMPT_ADHERENCE_FIELDS:
        patterns = PROMPT_ADHERENCE_FIELD_PATTERNS[field]
        for pattern in patterns:
            if re.search(pattern, body, flags=re.IGNORECASE | re.DOTALL):
                filled.append(field)
                break
    return filled


def _extract_plan_reasoning_blocks(output: str) -> list[dict[str, str | None]]:
    blocks: list[dict[str, str | None]] = []
    xml_re = re.compile(
        r"<plan_reasoning(?P<attrs>[^>]*)>(?P<body>.*?)</plan_reasoning>",
        flags=re.DOTALL | re.IGNORECASE,
    )
    for match in xml_re.finditer(output):
        attrs = match.group("attrs") or ""
        section_match = re.search(r"\bsection\s*=\s*['\"](?P<section>[^'\"]+)['\"]", attrs)
        body = match.group("body").strip()
        section = section_match.group("section").strip() if section_match else _reasoning_section_from_body(body)
        blocks.append({"section": section, "body": body})

    heading_re = re.compile(
        r"^\s*(?:#{1,6}\s*)?\*{0,2}Section reasoning\*{0,2}\s*:?\s*(?P<section>[^\n]*)$",
        flags=re.MULTILINE | re.IGNORECASE,
    )
    headings = list(heading_re.finditer(output))
    for index, match in enumerate(headings):
        start = match.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(output)
        body = output[start:end].strip()
        raw_section = match.group("section").strip(" *`:-")
        blocks.append(
            {
                "section": raw_section or _reasoning_section_from_body(body),
                "body": body,
            }
        )
    thinking_re = re.compile(
        r"<plan_thinking\b[^>]*>(?P<body>.*?)</plan_thinking>",
        flags=re.DOTALL | re.IGNORECASE,
    )
    sections_re = re.compile(
        r"<sections\b[^>]*>(?P<body>.*?)</sections>",
        flags=re.DOTALL | re.IGNORECASE,
    )
    for match in thinking_re.finditer(output):
        body = match.group("body").strip()
        sections_match = sections_re.search(body)
        section_lines = []
        if sections_match:
            section_lines = [
                line.strip()
                for line in sections_match.group("body").splitlines()
                if line.strip() and not line.lstrip().startswith("<")
            ]
        if not section_lines:
            blocks.append({"section": None, "body": body})
            continue
        for line in section_lines:
            section = line.split(":", 1)[0].strip(" *`\"'") if ":" in line else None
            blocks.append({"section": section, "body": line})
    return blocks


def _writer_cot_results(output: str, sections: list[str]) -> list[dict[str, Any]]:
    blocks = _extract_plan_reasoning_blocks(output)
    by_section: dict[str, list[dict[str, str | None]]] = {}
    unnamed: list[dict[str, str | None]] = []
    for block in blocks:
        key = _section_key(block.get("section"))
        if key:
            by_section.setdefault(key, []).append(block)
        else:
            unnamed.append(block)

    if not sections and blocks:
        sections = [str(block.get("section") or f"section_{index}") for index, block in enumerate(blocks, start=1)]

    results: list[dict[str, Any]] = []
    for section in sections:
        key = _section_key(section)
        block = by_section.get(key, []).pop(0) if by_section.get(key) else None
        if block is None and unnamed:
            block = unnamed.pop(0)
        body = str(block.get("body") or "").strip() if block else ""
        results.append(
            {
                "section": section,
                "block_present": bool(body),
                "block_chars": len(body),
                "fields_filled": _reasoning_fields_filled(body) if body else [],
            }
        )
    return results


def _extract_writer_gate(output: str) -> dict[str, Any]:
    gate_patterns = (
        r"<(?:writer_)?end_gate[^>]*>(?P<body>.*?)</(?:writer_)?end_gate>",
        r"<tier1_self_review[^>]*>(?P<body>.*?)</tier1_self_review>",
        r"<tier_1_self_review[^>]*>(?P<body>.*?)</tier_1_self_review>",
    )
    body = ""
    for pattern in gate_patterns:
        match = re.search(pattern, output, flags=re.DOTALL | re.IGNORECASE)
        if match:
            body = match.group("body").strip()
            break
    if not body:
        heading_re = re.compile(
            r"^\s*(?:#{1,6}\s*)?\*{0,2}(?:End gate|Tier-1 self-review|Tier 1 self-review)"
            r"\*{0,2}\s*:?\s*$",
            flags=re.MULTILINE | re.IGNORECASE,
        )
        match = heading_re.search(output)
        if match:
            next_heading = re.search(
                r"^\s*(?:#{1,6}\s+\S|```)",
                output[match.end() :],
                re.MULTILINE,
            )
            end = match.end() + next_heading.start() if next_heading else len(output)
            body = output[match.end() : end].strip()

    if not body:
        return {"gate_present": False, "gate_actions": [], "removed_count": 0}

    lower = body.casefold()
    actions: list[str] = []
    if "rescanned_words" in lower or (
        "rescan" in lower and any(token in lower for token in ("word", "vocab", "vesum"))
    ):
        actions.append("rescanned_words")
    if "rescanned_sources" in lower or ("rescan" in lower and any(token in lower for token in ("source", "citation"))):
        actions.append("rescanned_sources")
    if re.search(
        r"<grammar_claims_grounded\b[^>]*>.*?</grammar_claims_grounded>"
        r"|\bgrammar_claims_grounded\b\s*[:=]",
        body,
        flags=re.DOTALL | re.IGNORECASE,
    ):
        actions.append("grammar_claims_grounded")
    if "removed_unverified" in lower or ("removed" in lower and "unverified" in lower):
        actions.append("removed_unverified")

    removed_count = 0
    for pattern in (
        r"\bremoved_count\s*[:=]\s*(?P<count>\d+)",
        r"\bremoved(?:\s+unverified)?\s*[:=]\s*(?P<count>\d+)",
        r"\bremoved\s+(?P<count>\d+)\b",
    ):
        count_match = re.search(pattern, body, flags=re.IGNORECASE)
        if count_match:
            removed_count = int(count_match.group("count"))
            break
    return {
        "gate_present": True,
        "gate_actions": actions,
        "removed_count": removed_count,
    }


def _mapping_from_tool_call(call: Any) -> dict[str, Any]:
    if isinstance(call, Mapping):
        return dict(call)
    data: dict[str, Any] = {}
    for key in (
        "tool",
        "tool_name",
        "name",
        "args",
        "arguments",
        "result",
        "response",
        "duration_ms",
        "duration_s",
        "section",
        "dim",
        "audit_type",
        "items_checked",
        "items_failed",
        "flags_raised",
    ):
        if hasattr(call, key):
            data[key] = getattr(call, key)
    return data


_PLAN_REASONING_BLOCK_RE = re.compile(
    r"<plan_reasoning\b[^>]*>(.*?)</plan_reasoning>",
    re.DOTALL | re.IGNORECASE,
)
_PLAN_REASONING_ELEMENT_RE = re.compile(
    r"<plan_reasoning\b(?P<attrs>[^>]*)>(?P<body>.*?)</plan_reasoning>",
    re.DOTALL | re.IGNORECASE,
)
_PLAN_THINKING_ELEMENT_RE = re.compile(
    r"<plan_thinking\b(?P<attrs>[^>]*)>(?P<body>.*?)</plan_thinking>",
    re.DOTALL | re.IGNORECASE,
)
_TOOL_CITATION_RE = re.compile(r"`?(?P<name>(?:mcp__sources__|search_|verify_|check_|query_|translate_)\w+)`?")


def _normalize_tool_citation_name(raw_tool: Any) -> str:
    """Strip the MCP prefix from a tool name so gate-side matches work against
    the bare tool name (``search_text``, ``verify_words``, …).

    Two prefixes appear in the wild:

    * ``mcp__sources__`` — canonical double-underscore convention used by
      claude / codex / gemini-cli ≤0.41 / direct anthropic-tools calls.
    * ``mcp_sources_`` — single-underscore convention used by Hermes (and
      gemini-cli 0.42.0+). Hermes registers MCP tools under this name and
      the post-tool-call shell hook receives this form in its ``tool_name``
      payload field. Without stripping it here, the gate's downstream
      ``_tool_name_from_call(call) == "search_text"`` checks all fail
      silently — every Hermes-routed writer (deepseek/qwen/grok) gets
      ``search_text_calls: 0`` and a HARD ``textbook_grounding`` REJECT
      even when the calls actually fired. Matches the symmetry of
      ``WRITER_ALLOWED_TOOL_PREFIXES`` which already accepts both.
    """
    tool = str(raw_tool or "").strip()
    if tool.startswith("mcp__sources__"):
        tool = tool.removeprefix("mcp__sources__")
    elif tool.startswith("mcp_sources_"):
        tool = tool.removeprefix("mcp_sources_")
    return tool


def _tool_name_from_call(call: Any) -> str:
    mapped = _mapping_from_tool_call(call)
    return _normalize_tool_citation_name(mapped.get("tool") or mapped.get("tool_name") or mapped.get("name"))


def _raw_tool_name_from_call(call: Any) -> str:
    mapped = _mapping_from_tool_call(call)
    return str(mapped.get("tool") or mapped.get("tool_name") or mapped.get("name") or "").strip()


def _tool_args_from_call(call: Mapping[str, Any]) -> Mapping[str, Any]:
    args = call.get("args", call.get("arguments", {}))
    return args if isinstance(args, Mapping) else {}


def _normalize_trace_path(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    home = str(Path.home())
    if raw.startswith(f"{home}/"):
        raw = "~/" + raw[len(home) + 1 :]
    root = str(PROJECT_ROOT)
    if raw.startswith(f"{root}/"):
        raw = raw[len(root) + 1 :]
    return raw.replace("\\", "/")


def _read_path_from_call(call: Mapping[str, Any]) -> str:
    args = _tool_args_from_call(call)
    for key in ("file_path", "path", "filename"):
        if args.get(key):
            return _normalize_trace_path(args[key])
    return ""


def _is_writer_infra_path(path: str) -> bool:
    if not path:
        return False
    return any(fnmatch(path, pattern) for pattern in WRITER_INFRA_DENYLIST_PATHS)


def _failure_record_to_event(record: FailureRecord) -> dict[str, Any]:
    payload = asdict(record)
    payload["failure_class"] = record.failure_class.value
    return payload


def classify_writer_trace(
    writer_tool_calls: list[Mapping[str, Any]],
) -> list[FailureRecord]:
    """Classify raw writer trace violations before normalized filtering hides them."""
    wrong_family_calls: list[dict[str, Any]] = []
    handoff_reads: list[dict[str, Any]] = []

    for index, raw_call in enumerate(writer_tool_calls):
        call = _mapping_from_tool_call(raw_call)
        tool_name = _raw_tool_name_from_call(call)
        if not tool_name:
            continue
        # Harmless annotation-only built-ins (e.g. gemini-cli's
        # `update_topic`) are preserved in the trace for forensics but do
        # not count against wrong_tool_family. See
        # WRITER_AGENT_ANNOTATION_TOOLS for rationale.
        if (
            not any(tool_name.startswith(p) for p in WRITER_ALLOWED_TOOL_PREFIXES)
            and tool_name not in WRITER_AGENT_ANNOTATION_TOOLS
        ):
            wrong_family_calls.append(
                {
                    "index": index,
                    "name": tool_name,
                    "arguments": dict(_tool_args_from_call(call)),
                }
            )
        if tool_name == "Read":
            read_path = _read_path_from_call(call)
            if _is_writer_infra_path(read_path):
                handoff_reads.append(
                    {
                        "index": index,
                        "name": tool_name,
                        "path": read_path,
                    }
                )

    failures: list[FailureRecord] = []
    if wrong_family_calls:
        # Demoted from TERMINAL → WARN on 2026-05-22 (user direction:
        # "i dont care how they do it as long as they do it" — quality is
        # judged by python_qg / wiki_coverage / llm_qg, not by tool-family
        # cosmetics). The 2026-05-22 codex-tools build that surfaced this
        # used `mcp__node_repl__js` to spawn `rg` and `sed` against the
        # worktree's own scripts/ — resourceful self-correction behavior
        # that the prior TERMINAL framing punished. The companion
        # `handoff_or_orchestrator_file` check below remains TERMINAL
        # because reading session-state into curriculum content IS a
        # content-quality concern (orchestrator decisions leaking into
        # learner-facing material), distinct from tool-choice surface.
        failures.append(
            FailureRecord(
                failure_class=FailureClass.INFRA_CONTEXT_CONTAMINATION,
                sub_class="wrong_tool_family",
                gate="writer_trace_isolation",
                severity="WARN",
                recovery_action="none",
                evidence={"offending_tool_calls": wrong_family_calls},
                terminal=False,
            )
        )
    if handoff_reads:
        failures.append(
            FailureRecord(
                failure_class=FailureClass.INFRA_CONTEXT_CONTAMINATION,
                sub_class="handoff_or_orchestrator_file",
                gate="writer_trace_isolation",
                severity="TERMINAL",
                recovery_action="none",
                evidence={"offending_reads": handoff_reads},
                terminal=True,
            )
        )
    return failures


def _markdown_fence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start: int | None = None
    for match in re.finditer(r"^```", text, flags=re.MULTILINE):
        if start is None:
            start = match.start()
        else:
            spans.append((start, match.end()))
            start = None
    if start is not None:
        spans.append((start, len(text)))
    return spans


def _position_in_spans(position: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in spans)


def _cited_plan_reasoning_tools(writer_output: str) -> set[str]:
    cited: set[str] = set()
    fenced_spans = _markdown_fence_spans(writer_output)
    for element_re in (_PLAN_REASONING_ELEMENT_RE, _PLAN_THINKING_ELEMENT_RE):
        for match in element_re.finditer(writer_output):
            if _position_in_spans(match.start(), fenced_spans):
                continue
            searchable = f"{match.group('attrs')} {match.group('body')}"
            cited.update(_normalize_tool_citation_name(citation) for citation in _TOOL_CITATION_RE.findall(searchable))
    return cited


def detect_tool_theatre(
    writer_output: str,
    tool_calls: list[Mapping[str, Any]],
) -> list[str]:
    """Return cited plan-reasoning tool names absent from the actual trace."""
    cited = _cited_plan_reasoning_tools(writer_output)
    called = {_tool_name_from_call(call) for call in tool_calls}
    called.discard("")

    # Canonical-only: aliases/family maps do not count. The writer must cite
    # the actual tool name it called so telemetry cannot be satisfied by prose.
    return sorted(cited - called)


def _runtime_tool_calls(result: Any) -> list[dict[str, Any]] | None:
    if getattr(result, "tool_calls_total", "known") is None:
        return None
    # Runtime Result.tool_calls is the producer today. usage_record support is
    # read-only forward compatibility; persisting raw arguments needs redaction.
    calls: list[dict[str, Any]] = []
    for attr in ("tool_calls", "mcp_tool_calls"):
        value = getattr(result, attr, None)
        if isinstance(value, list):
            calls.extend(_mapping_from_tool_call(item) for item in value)
    usage_record = getattr(result, "usage_record", None)
    if isinstance(usage_record, Mapping):
        for key in ("tool_calls", "mcp_tool_calls"):
            value = usage_record.get(key)
            if isinstance(value, list):
                calls.extend(_mapping_from_tool_call(item) for item in value)
    return calls


def _normalize_tool_name(raw_tool: Any) -> str:
    tool = str(raw_tool or "").strip()
    if "__" in tool:
        # Canonical MCP: `mcp__sources__search_text` → `search_text`.
        tool = tool.rsplit("__", 1)[-1]
    elif tool.startswith("mcp_sources_"):
        # Gemini CLI 0.42.0+ emits single-underscore MCP tool names. Strip
        # the `mcp_sources_` prefix so the unqualified tool name can match
        # WRITER_TOOL_NAMES (and downstream telemetry/gates work the same
        # for both prefix conventions). See WRITER_ALLOWED_TOOL_PREFIXES
        # for the gate-side counterpart.
        tool = tool.removeprefix("mcp_sources_")
    return tool


def _tool_duration_ms(call: Mapping[str, Any]) -> int:
    if isinstance(call.get("duration_ms"), int | float):
        return max(0, int(call["duration_ms"]))
    if isinstance(call.get("duration_s"), int | float):
        return max(0, int(float(call["duration_s"]) * 1000))
    return 0


def _count_arg_items(args: Any) -> int | None:
    if isinstance(args, list | tuple | set):
        return len(args)
    if not isinstance(args, Mapping):
        return None
    for key in ("words", "lemmas", "items", "queries"):
        value = args.get(key)
        if isinstance(value, list | tuple | set):
            return len(value)
    return None


def _summarize_tool_args(tool: str, args: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    count = _count_arg_items(args)
    if count is not None:
        summary["count"] = count
    if isinstance(args, Mapping):
        if tool in {"verify_lemma", "check_modern_form"} and args.get("lemma"):
            summary["lemma"] = _clean_telemetry_text(args["lemma"], 80)
        elif args.get("word"):
            summary["word"] = _clean_telemetry_text(args["word"], 80)
        elif args.get("query"):
            summary["query_chars"] = len(str(args["query"]))
        if not summary:
            summary["keys"] = sorted(str(key) for key in args)[:5]
    elif not summary and args is not None:
        summary["type"] = type(args).__name__
    return summary


def _summarize_verify_words_result(result: Any) -> dict[str, Any]:
    if isinstance(result, Mapping) and {"verified", "failed"} & set(result):
        failed_words = result.get("failed_words") or []
        if not isinstance(failed_words, list):
            failed_words = []
        return {
            "verified": int(result.get("verified") or 0),
            "failed": int(result.get("failed") or 0),
            "failed_words": [_clean_telemetry_text(word, 80) for word in failed_words[:TELEMETRY_MAX_FAILED_WORDS]],
        }
    if not isinstance(result, Mapping):
        return _summarize_generic_tool_result(result)

    verified = 0
    failed_words: list[str] = []
    for word, matches in result.items():
        if matches:
            verified += 1
        else:
            failed_words.append(str(word))
    return {
        "verified": verified,
        "failed": len(failed_words),
        "failed_words": [_clean_telemetry_text(word, 80) for word in failed_words[:TELEMETRY_MAX_FAILED_WORDS]],
    }


def _summarize_generic_tool_result(result: Any) -> dict[str, Any]:
    if isinstance(result, Mapping):
        summary: dict[str, Any] = {}
        for key in ("verified", "failed", "items_checked", "items_failed"):
            if isinstance(result.get(key), int | float):
                summary[key] = int(result[key])
        flags = result.get("flags_raised")
        if isinstance(flags, list):
            summary["flags_raised"] = [_clean_telemetry_text(flag, 120) for flag in flags[:TELEMETRY_MAX_FAILED_WORDS]]
        if summary:
            return summary
        return {"keys": sorted(str(key) for key in result)[:5]}
    if isinstance(result, list | tuple | set):
        return {"count": len(result)}
    if result is None:
        return {}
    return {"text_chars": len(str(result))}


SEARCH_TEXT_RESULT_ITEM_LIMIT = 10
SEARCH_TEXT_RESULT_TEXT_LIMIT = 500


def _maybe_parse_json_string(value: str) -> Any:
    stripped = value.strip()
    if not stripped or stripped[0] not in "[{":
        return value
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return value


def _search_text_result_items(result: Any) -> list[Mapping[str, Any]]:
    result = _maybe_parse_json_string(result) if isinstance(result, str) else result
    if isinstance(result, Mapping):
        for key in ("structuredContent", "structured_content"):
            structured = result.get(key)
            if structured is not None:
                structured_items = _search_text_result_items(structured)
                if structured_items:
                    return structured_items
        raw_hits = result.get("results") or result.get("hits") or result.get("items")
        if isinstance(raw_hits, list):
            return [item for item in raw_hits if isinstance(item, Mapping)]
        content = result.get("content")
        if isinstance(content, list | tuple):
            content_items = _search_text_result_items(content)
            if content_items:
                return content_items
        text = result.get("text")
        if (
            result.get("type") == "text"
            and isinstance(text, str)
            and (parsed := _maybe_parse_json_string(text)) is not text
        ):
            return _search_text_result_items(parsed)
        return [result]
    if isinstance(result, list | tuple):
        items: list[Mapping[str, Any]] = []
        for item in result:
            if isinstance(item, Mapping) and item.get("type") == "text" and isinstance(item.get("text"), str):
                parsed = _maybe_parse_json_string(item["text"])
                if parsed is not item["text"]:
                    items.extend(_search_text_result_items(parsed))
                    continue
            if isinstance(item, Mapping):
                items.append(item)
        return items
    return []


def _summarize_search_text_result(result: Any) -> dict[str, Any]:
    items = _search_text_result_items(result)
    if not items:
        return _summarize_generic_tool_result(result)

    summary_items: list[dict[str, Any]] = []
    for item in items[:SEARCH_TEXT_RESULT_ITEM_LIMIT]:
        summary_item: dict[str, Any] = {}
        for key in (
            "source_type",
            "corpus",
            "type",
            "source",
            "author",
            "grade",
            "page",
            "title",
            "section_title",
            "chunk_id",
        ):
            value = item.get(key)
            if value not in (None, ""):
                summary_item[key] = _clean_telemetry_text(str(value), 160)
        text = _textbook_hit_text(item, max_chars=SEARCH_TEXT_RESULT_TEXT_LIMIT)
        if text:
            summary_item["text"] = _clean_telemetry_text(
                text,
                SEARCH_TEXT_RESULT_TEXT_LIMIT,
            )
        if summary_item:
            summary_items.append(summary_item)

    summary: dict[str, Any] = {"count": len(items)}
    if summary_items:
        summary["items"] = summary_items
    if len(items) > SEARCH_TEXT_RESULT_ITEM_LIMIT:
        summary["truncated_items"] = len(items) - SEARCH_TEXT_RESULT_ITEM_LIMIT
    return summary


def _summarize_tool_result(tool: str, result: Any) -> dict[str, Any]:
    if tool == "verify_words":
        return _summarize_verify_words_result(result)
    if tool == "search_text":
        return _summarize_search_text_result(result)
    return _summarize_generic_tool_result(result)


def _bounded_result_excerpt(result: Any, max_chars: int = 4000) -> str:
    texts: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key in {"text", "content", "excerpt", "snippet", "quote", "body"}:
                    texts.append(str(child))
                else:
                    walk(child)
        elif isinstance(value, list | tuple):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            texts.append(value)

    walk(result)
    excerpt = re.sub(r"\s+", " ", "\n".join(texts)).strip()
    return excerpt[:max_chars]


def emit_writer_response_telemetry(
    output: str,
    *,
    writer: str,
    module: str,
    sections: list[str],
    tool_calls: list[Mapping[str, Any]] | None = None,
    event_sink: Callable[..., None] | None = None,
) -> dict[str, Any]:
    """Emit writer-side prompt-adherence and tool-use telemetry."""
    cot_results = _writer_cot_results(output, sections)
    for result in cot_results:
        _emit(
            event_sink,
            "writer_cot_emit",
            writer=writer,
            module=module,
            section=result["section"],
            block_present=result["block_present"],
            block_chars=result["block_chars"],
            fields_filled=result["fields_filled"],
        )

    telemetry_unavailable = tool_calls is None
    tool_calls_total: int | None = None if telemetry_unavailable else 0
    verify_words_calls: int | None = None if telemetry_unavailable else 0
    for call in tool_calls or []:
        tool = _normalize_tool_name(call.get("tool") or call.get("tool_name") or call.get("name"))
        if tool not in WRITER_TOOL_NAMES:
            continue
        args = call.get("args", call.get("arguments", {}))
        result = call.get("result", call.get("response"))
        assert tool_calls_total is not None
        tool_calls_total += 1
        if tool == "verify_words":
            assert verify_words_calls is not None
            verify_words_calls += 1
        fields: dict[str, Any] = {
            "writer": writer,
            "module": module,
            "section": str(call.get("section") or "unknown"),
            "tool": tool,
            "args_summary": _summarize_tool_args(tool, args),
            "result_summary": _summarize_tool_result(tool, result),
            "duration_ms": _tool_duration_ms(call),
        }
        if tool == "search_text":
            excerpt = _bounded_result_excerpt(result)
            if excerpt:
                fields["result_excerpt"] = excerpt
        _emit(
            event_sink,
            "writer_tool_call",
            **fields,
        )

    gate = _extract_writer_gate(output)
    _emit(
        event_sink,
        "writer_end_gate",
        writer=writer,
        module=module,
        gate_present=gate["gate_present"],
        gate_actions=gate["gate_actions"],
        removed_count=gate["removed_count"],
    )

    summary = {
        "sections_total": len(cot_results),
        "sections_with_cot": sum(1 for result in cot_results if result["block_present"]),
        "tool_calls_total": tool_calls_total,
        "verify_words_calls": verify_words_calls,
        "tool_call_telemetry_available": not telemetry_unavailable,
        "end_gate_fired": bool(gate["gate_present"]),
        "removed_via_gate": int(gate["removed_count"]),
    }
    theatre_violations = [] if telemetry_unavailable else detect_tool_theatre(output, list(tool_calls or []))
    capped_theatre_violations = theatre_violations[:TELEMETRY_MAX_THEATRE_VIOLATIONS]
    summary["tool_theatre_violations"] = capped_theatre_violations
    summary["tool_theatre_violation_count"] = len(theatre_violations)
    if theatre_violations:
        called_tools = {_tool_name_from_call(call) for call in tool_calls or []}
        called_tools.discard("")
        _emit(
            event_sink,
            "writer_tool_theatre",
            writer=writer,
            module=module,
            violations=capped_theatre_violations,
            violation_count=len(theatre_violations),
            cited_count=len(_cited_plan_reasoning_tools(output)),
            called_count=len(called_tools),
        )
        _emit_writer_rule_fired(
            event_sink,
            rule_id=RULE_CITE_HONEST,
            gate="tool_theatre",
            evidence=", ".join(capped_theatre_violations),
            writer=writer,
            module=module,
        )
    _emit(event_sink, "phase_writer_summary", writer=writer, module=module, **summary)
    return summary


def _enforce_tools_writer_runtime_gate(
    *,
    writer: str,
    module: str,
    phase_writer_summary: Mapping[str, Any],
) -> None:
    """Fail when a tools writer resolved MCP config but never invoked a tool."""
    if not writer.endswith("-tools"):
        return
    if phase_writer_summary["tool_calls_total"] is None:
        return
    if phase_writer_summary["tool_calls_total"] != 0:
        return
    raise LinearPipelineError(
        "MCP_TOOLS_NEVER_INVOKED: "
        f"writer={writer!r} module={module!r} expected='>=1 mcp__sources__* call "
        "from a -tools writer' got=0. Pre-flight "
        "mcp_config_resolved.resolution_status='ok' only verifies config string "
        "resolution. The model must actually invoke at least one MCP tool. If "
        "this fires, check the rollout JSONL for catalog-visibility errors "
        "(e.g., 'tools are not exposed in this session')."
    )


def _mcp_tools_never_invoked_failure(
    *,
    writer: str,
    module: str,
    phase_writer_summary: Mapping[str, Any],
) -> FailureRecord | None:
    if not writer.endswith("-tools"):
        return None
    if phase_writer_summary["tool_calls_total"] is None:
        return None
    if phase_writer_summary["tool_calls_total"] != 0:
        return None
    return FailureRecord(
        failure_class=FailureClass.MCP_TOOLS_NEVER_INVOKED,
        sub_class=None,
        gate="tools_writer_runtime_gate",
        severity="HARD",
        recovery_action="none",
        evidence={
            "writer": writer,
            "module": module,
            "phase_writer_summary": dict(phase_writer_summary),
        },
        terminal=True,
    )


def _enforce_writer_runtime_gates(
    *,
    writer: str,
    module: str,
    phase_writer_summary: Mapping[str, Any],
    tool_calls: list[Mapping[str, Any]] | None,
    event_sink: Callable[..., None] | None = None,
) -> None:
    failures = [
        *classify_writer_trace(tool_calls or []),
    ]
    mcp_failure = _mcp_tools_never_invoked_failure(
        writer=writer,
        module=module,
        phase_writer_summary=phase_writer_summary,
    )
    if mcp_failure is not None:
        failures.append(mcp_failure)
    if not failures:
        return

    # Emit ALL failures (including WARN) for telemetry / forensics — but
    # only raise on TERMINAL ones. The writer_trace_isolation
    # `wrong_tool_family` record is WARN since 2026-05-22: a writer
    # reaching for a non-sources tool is observed and logged, but does
    # not kill the build — python_qg / wiki_coverage / llm_qg judge
    # quality, not tool-family cosmetics. TERMINAL conditions
    # (`handoff_or_orchestrator_file`, `mcp_tools_never_invoked`) still
    # halt the build because they represent content-leakage or
    # zero-corpus-grounding states that python_qg cannot recover from
    # downstream.
    for record in failures:
        _emit(
            event_sink,
            "writer_failure_class",
            writer=writer,
            module=module,
            **_failure_record_to_event(record),
        )

    terminal_failures = [record for record in failures if record.terminal]
    if not terminal_failures:
        return

    classes = ", ".join(
        f"{record.failure_class.value}" + (f":{record.sub_class}" if record.sub_class else "")
        for record in terminal_failures
    )
    raise LinearPipelineError(f"WRITER_RUNTIME_GATE_FAILED: writer={writer!r} module={module!r} failures=[{classes}]")


def _inline_prompt_tokens(text: str, token_map: Mapping[str, Any]) -> str:
    """Substitute ``{KEY}`` placeholders inside an already-composed block.

    Registry rule bodies can carry build-time ``{TOKEN}`` placeholders (e.g.
    ``R-ACTIVITY-COMPOSITION`` references ``{ACTIVITY_COUNT_TARGET}``). The
    generator-composed rules block is itself injected into the prompt as a
    single ``{GENERATED_*_RULES}`` token, so its inner placeholders must be
    resolved BEFORE injection — ``render_phase_prompt`` substitutes the outer
    token last and would otherwise leave the inner ones unresolved. Resolving
    here (rather than in ``render_phase_prompt``) keeps the legacy path's
    single-pass substitution untouched, so the flag-OFF output stays
    byte-identical.
    """
    for key, value in token_map.items():
        text = text.replace(f"{{{key}}}", str(value))
    return text


SEMINAR_FOLK_WRITER_RULES_PATH = (
    PROJECT_ROOT / "scripts" / "build" / "phases" / "linear-write-seminar-folk-rules.md"
)


def _seminar_folk_writer_rules(level: str, context: Mapping[str, Any]) -> str:
    """Seminar/FOLK-only writer rules, gated OUT of core (a1-c2) prompts.

    The folk/seminar source-discipline, word-count floor, primary-text
    embedding, regional-vocabulary, and experiential-layer rules apply only to
    ``SEMINAR_LEVELS``. Rendering them into every core level's prompt is pure
    overhead — an A1 letter module needs no folk-coinage examples — and it
    pushed the A1 writer prompt over ``WRITER_PROMPT_CEILING_BYTES``. Returns
    ``""`` for non-seminar levels; the block's inner ``{WORD_TARGET}`` token is
    resolved here so ``render_phase_prompt``'s single outer pass stays correct.
    """
    if str(level).lower() not in SEMINAR_LEVELS:
        return ""
    block = SEMINAR_FOLK_WRITER_RULES_PATH.read_text(encoding="utf-8").strip()
    return _inline_prompt_tokens(block, context)


def _render_section_word_budgets(plan: Mapping[str, Any]) -> str:
    """Render plan section word budgets as a compact writer checklist."""
    outline = plan.get("content_outline")
    if not isinstance(outline, list):
        return "- No `content_outline` section budgets found."

    lines: list[str] = []
    running_total = 0
    for index, section in enumerate(outline, start=1):
        if not isinstance(section, Mapping):
            continue
        title = str(section.get("section") or "").strip()
        words = section.get("words")
        if not title or words is None:
            continue
        try:
            budget = int(words)
        except (TypeError, ValueError):
            continue
        running_total += budget
        lines.append(f"{index}. {title}: {budget} words (running total {running_total})")

    if not lines:
        return "- No valid `content_outline[].section` + `words` budgets found."
    return "\n".join(lines)


def writer_context(
    plan: Mapping[str, Any],
    plan_content: str,
    knowledge_packet: str,
    wiki_manifest: str | Mapping[str, Any] | None = None,
    *,
    plan_path: Path | None = None,
    implementation_map: Mapping[str, Any] | None = None,
    writer: str | None = None,
    use_generator: bool = False,
    obligation_checklist: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    level = str(plan["level"])
    sequence = int(plan["sequence"])
    learner_state = build_learner_state(level.lower(), sequence)
    module_archetype = resolve_module_archetype(level.lower(), sequence)
    activity_config = _activity_config(level, sequence, str(plan["slug"]))
    if wiki_manifest is None:
        manifest_for_checklist = build_wiki_manifest_data(level=level.lower(), slug=str(plan["slug"]), plan=plan)
        wiki_manifest_text = _render_prompt_wiki_manifest(manifest_for_checklist)
        required_items_text = _render_wiki_coverage_required_items(manifest_for_checklist)
    elif isinstance(wiki_manifest, str):
        manifest_for_checklist = wiki_manifest
        wiki_manifest_text = _render_prompt_wiki_manifest(wiki_manifest)
        required_items_text = _render_wiki_coverage_required_items(wiki_manifest)
    else:
        manifest_for_checklist = wiki_manifest
        wiki_manifest_text = _render_prompt_wiki_manifest(wiki_manifest)
        required_items_text = _render_wiki_coverage_required_items(wiki_manifest)

    if implementation_map is None:
        impl_map_contract = "(no implementation_map provided to render_writer_prompt — gate will fail)"
    else:
        from scripts.build.phases.implementation_map import render_for_writer_prompt

        impl_map_contract = render_for_writer_prompt(dict(implementation_map))

    context = {
        "LEVEL": level,
        "MODULE_NUM": str(sequence),
        "MODULE_SLUG": str(plan["slug"]),
        "TOPIC_TITLE": str(plan["title"]),
        "PHASE": str(plan.get("phase", "")),
        "WORD_TARGET": str(plan["word_target"]),
        "SIZE_POLICY": render_writer_size_policy(
            build_size_policy_for_plan(plan, plan_path=plan_path)
        ),
        "SECTION_WORD_BUDGETS": _render_section_word_budgets(plan),
        "WRITER_SPECIFIC_DIRECTIVES": _writer_specific_directives(writer),
        "PLAN_CONTENT": plan_content,
        "KNOWLEDGE_PACKET": knowledge_packet,
        "WIKI_MANIFEST": wiki_manifest_text,
        "WIKI_COVERAGE_REQUIRED_ITEMS": required_items_text,
        "IMPLEMENTATION_MAP_CONTRACT": impl_map_contract,
        "LEARNER_STATE": format_learner_state(learner_state),
        "MODULE_ARCHETYPE": format_module_archetype(module_archetype),
        "IMMERSION_RULE": get_immersion_rule(
            level.lower(),
            sequence,
            learner_state=learner_state,
            letter_module=bool(plan.get("letter_module")),
        ),
        "CONTRACT_YAML": _contract_yaml(plan),
        "ALLOWED_ACTIVITY_TYPES": activity_config["ALLOWED_ACTIVITY_TYPES"],
        "FORBIDDEN_ACTIVITY_TYPES": activity_config["FORBIDDEN_ACTIVITY_TYPES"],
        "INLINE_ALLOWED_TYPES": activity_config["INLINE_ALLOWED_TYPES"],
        "WORKBOOK_ALLOWED_TYPES": activity_config["WORKBOOK_ALLOWED_TYPES"],
        "ACTIVITY_COUNT_TARGET": activity_config["ACTIVITY_COUNT_TARGET"],
        "VOCAB_COUNT_TARGET": activity_config["VOCAB_COUNT_TARGET"],
        "COMPONENT_PROPS_SCHEMA": _render_component_props_schema(activity_config["ALLOWED_ACTIVITY_TYPES"]),
    }
    # Seminar/FOLK-only writer rules: gated out of core (a1-c2) prompts so the
    # A1 letter module stays under WRITER_PROMPT_CEILING_BYTES. Resolved after
    # the dict so its inner {WORD_TARGET} token interpolates against context.
    context["SEMINAR_FOLK_WRITER_RULES"] = _seminar_folk_writer_rules(level, context)
    if use_generator:
        # V7.2 Step 5: inject the registry-composed writer-rules block + the
        # single-source Obligation Checklist for the generator-fed template
        # (`linear-write.generated.md`). OBLIGATION_CHECKLIST reuses the already
        # computed required_items_text so the writer prompt, reviewer prompt, and
        # wiki_coverage_gate all read one rendering. Keyed behind the flag so the
        # legacy return above stays byte-identical with the flag OFF.
        from scripts.build.prompt_generator import (
            build_obligation_checklist,
            build_obligation_checklist_object,
            build_writer_rules_block,
            track_for_level,
        )

        rules_block = build_writer_rules_block(level.lower(), track_for_level(level))
        # Resolve any build-time tokens the rule bodies carry (e.g.
        # {ACTIVITY_COUNT_TARGET}) against the context computed above.
        context["GENERATED_WRITER_RULES"] = _inline_prompt_tokens(rules_block, context)
        checklist = (
            dict(obligation_checklist)
            if obligation_checklist is not None
            else build_obligation_checklist_object(
                manifest_for_checklist,
                seeded_map=implementation_map,
            )
        )
        context["OBLIGATION_CHECKLIST"] = build_obligation_checklist(
            manifest_for_checklist,
            obligation_checklist=checklist,
        )
    return context


def _render_component_props_schema(allowed_activity_types: str) -> str:
    """Render compact authoring-field spec per allowed activity type.

    Historical name retained for prompt-token compatibility. The writer must
    see the AUTHORING JSON/YAML shape consumed by ``scripts/yaml_activities.py``
    and validated by ``_validate_writer_json_artifact`` — not React component
    prop names from ``docs/lesson-schema.yaml``. Those views diverge for
    adapter-style activities: quiz/select/translate authoring uses ``items``,
    while React components may expose ``questions``. Showing component props in
    this prompt caused Gemini to emit ``quiz: {questions: [...]}``, which the
    strict writer parser correctly rejects.
    """
    allowed = {token.strip() for token in allowed_activity_types.split(",") if token.strip()}
    authoring_by_type = _activity_type_field_whitelist()
    lines: list[str] = []
    for activity_type in sorted(allowed):
        fields = authoring_by_type.get(activity_type)
        if fields is None:
            lines.append(
                f"- {activity_type}:  # WARNING: no authoring schema entry — "
                "DO NOT USE this activity type until the schema is fixed "
                "(see #1604 for schema drift)"
            )
            continue
        content_fields = sorted(fields - _UNIVERSAL_AUTHORING_FIELDS)
        optional_fields = sorted((fields & _UNIVERSAL_AUTHORING_FIELDS) - {"id", "type"})
        required = ["id", "type", *content_fields]
        lines.append(f"- {activity_type}:")
        lines.append(f"    required authoring fields: {', '.join(required)}")
        lines.append(f"    optional authoring fields: {', '.join(optional_fields) or '—'}")
    if not lines:
        return "(no allowed activity types resolved against authoring schema)"
    return "\n".join(lines)


def _ensure_codex_writer_home(
    *,
    event_sink: Callable[..., None] | None = None,
) -> str:
    """Materialize a scoped ``$CODEX_HOME`` for the V7 codex-tools writer.

    The Codex.app desktop integration registers several MCP servers in
    the user's ``~/.codex/config.toml`` (``node_repl``,
    ``openaiDeveloperDocs``, ``codex_apps.github``). These survive
    per-invocation ``-c mcp_servers.X.url=...`` overrides — those
    MERGE with the user config rather than REPLACE it. The writer
    trace-isolation gate (``WRITER_ALLOWED_TOOL_PREFIXES``) catches
    any call outside ``mcp__sources__*`` and fires
    ``wrong_tool_family`` TERMINAL.

    Fix: repoint ``$CODEX_HOME`` at a project-local directory that
    contains ONLY the minimal config registering the ``sources`` MCP
    server, plus a symlink of the user's real ``auth.json`` so the
    OpenAI provider still authenticates. Codex CLI 0.133.0's
    ``--ignore-user-config`` alone is insufficient because it also
    skips MCP config, and ``-c`` overrides can't add a fresh server
    entry — verified via ``ab ask-codex`` 2026-05-22 + smoke tests.

    The scoped home is materialized at
    ``$CODEX_HOME_USER/.../codex-v7-writer/`` (project temp dir under
    the OS temp root) and updated idempotently each call so changes
    to the canonical config get picked up. Auth is symlinked rather
    than copied so token refreshes propagate.

    Returns the absolute path to the scoped home.

    Missing-auth behavior: when the user's ``$CODEX_HOME/auth.json``
    doesn't exist (e.g. on a CI runner that has never run
    ``codex login``), the symlink is skipped and a
    ``codex_writer_home_auth_missing`` event is emitted so build paths
    can detect the condition. The scoped config is still materialized so
    test paths exercising ``_runtime_tool_config`` work without real
    Codex auth. Codex will fail loud at the actual ``codex exec`` call
    with its own missing-auth error — that's the right layer for the
    failure to surface, not config resolution.
    """
    real_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    real_auth = real_home / "auth.json"

    # Scoped home under tempdir — survives across invocations within a
    # single user session but doesn't pollute the repo tree. Per-user
    # uid stays away from cross-user clobbering when multiple shells
    # share /tmp.
    scoped_home = Path(tempfile.gettempdir()) / f"codex-v7-writer-{os.getuid()}"
    scoped_home.mkdir(parents=True, exist_ok=True)

    config_path = scoped_home / "config.toml"
    desired_config = (
        "# Auto-generated by linear_pipeline._ensure_codex_writer_home.\n"
        "# Restricts the V7 codex-tools writer to the sources MCP only.\n"
        "# Regenerated on every writer invocation — do not edit by hand.\n"
        "\n"
        "[mcp_servers.sources]\n"
        'url = "http://127.0.0.1:8766/mcp"\n'
    )
    if not config_path.exists() or config_path.read_text(encoding="utf-8") != desired_config:
        config_path.write_text(desired_config, encoding="utf-8")

    auth_link = scoped_home / "auth.json"
    auth_present = real_auth.exists()
    if auth_present:
        # Symlink (not copy) so token refreshes by the desktop Codex.app
        # propagate without us having to invalidate the scoped home.
        if auth_link.is_symlink():
            try:
                if Path(os.readlink(auth_link)) == real_auth:
                    pass  # link already correct
                else:
                    auth_link.unlink()
                    auth_link.symlink_to(real_auth)
            except OSError:
                # Recover from a dangling/corrupt link
                auth_link.unlink(missing_ok=True)
                auth_link.symlink_to(real_auth)
        elif auth_link.exists():
            # Stale file at that path — replace with symlink.
            auth_link.unlink()
            auth_link.symlink_to(real_auth)
        else:
            auth_link.symlink_to(real_auth)
    else:
        # No auth.json to link. Remove any stale link so codex doesn't
        # silently authenticate against a broken target. The actual
        # ``codex exec`` invocation will fail loud with its own missing-auth
        # error at runtime — the right layer for that failure to surface.
        if auth_link.is_symlink() or auth_link.exists():
            with contextlib.suppress(OSError):
                auth_link.unlink()

    _emit(
        event_sink,
        "codex_writer_home_resolved",
        scoped_home=str(scoped_home),
        real_home=str(real_home),
        auth_present=auth_present,
    )
    if not auth_present:
        _emit(
            event_sink,
            "codex_writer_home_auth_missing",
            scoped_home=str(scoped_home),
            real_home=str(real_home),
            real_auth=str(real_auth),
        )
    return str(scoped_home)


def _ensure_cursor_writer_workspace(
    cwd: Path,
    *,
    event_sink: Callable[..., None] | None = None,
) -> Path:
    """Materialize scoped .cursor/mcp.json for V7 cursor-tools writer.

    Cursor loads MCP from the workspace directory (--workspace / cwd),
    not from repo-root .mcp.json (Claude/Codex path). Only the sources
    server may be registered — same contract as _ensure_codex_writer_home.
    """
    cursor_dir = cwd / ".cursor"
    cursor_dir.mkdir(parents=True, exist_ok=True)
    config_path = cursor_dir / "mcp.json"
    desired = '{\n  "mcpServers": {\n    "sources": {\n      "url": "http://127.0.0.1:8766/mcp"\n    }\n  }\n}\n'
    if not config_path.exists() or config_path.read_text(encoding="utf-8") != desired:
        config_path.write_text(desired, encoding="utf-8")

    _emit(
        event_sink,
        "cursor_writer_workspace_resolved",
        workspace=str(cwd.resolve()),
        mcp_config=str(config_path),
    )
    return cwd.resolve()


def _runtime_tool_config(
    agent_label: str,
    *,
    workspace_dir: Path,
    event_sink: Callable[..., None] | None = None,
) -> dict[str, Any]:
    tool_config: dict[str, Any] = {"output_format": "stream-json"}
    if not agent_label.endswith("-tools"):
        return tool_config

    from scripts.agent_runtime.tool_config import _load_mcp_config, build_mcp_tool_config

    codex_disable_features: list[str] = []
    codex_home_override: str | None = None
    if agent_label == "codex-tools":
        agent_kwargs = {
            "mcp_servers": ["sources"],
        }
        # V7 writer tool-isolation for codex-tools requires two
        # complementary mechanisms, both per-invocation:
        #
        # 1. Feature-flag disable list. Codex's default surfaces several
        #    non-MCP tool families (shell_tool / goals / browser_use /
        #    in_app_browser / image_generation / apps / plugins /
        #    multi_agent). The writer gate's `WRITER_ALLOWED_TOOL_PREFIXES`
        #    only allows `mcp__sources__*` (+ `mcp_sources_*` for
        #    gemini-cli). Anything else trips `wrong_tool_family`.
        #    `--disable shell_tool` alone is insufficient (PR #2227 +
        #    issue #2228): writers gravitated to `mcp__node_repl__js`
        #    + `get_goal` instead.
        #
        # 2. Scoped CODEX_HOME. The user-level `$CODEX_HOME/config.toml`
        #    typically registers MCP servers (`node_repl`,
        #    `openaiDeveloperDocs`, `codex_apps.github`) from the
        #    Codex.app desktop integration. Per-invocation `-c
        #    mcp_servers.X.url=...` overrides MERGE with that config;
        #    they do NOT replace it. The actual isolation mechanism is
        #    repointing $CODEX_HOME at a directory containing ONLY the
        #    `sources` MCP definition + a symlink of the user's
        #    `auth.json`. Verified via `ab ask-codex` 2026-05-22.
        codex_disable_features = [
            "shell_tool",
            "goals",
            "browser_use",
            "in_app_browser",
            "image_generation",
            "apps",
            "plugins",
            "multi_agent",
        ]
        # NOTE: scoped CODEX_HOME is materialized further down so that the
        # `mcp_config_resolved` event stays first in the emission stream
        # (downstream observability + tests assume that ordering).
    elif agent_label == "claude-tools":
        agent_kwargs = {
            "mcp_servers": ["sources"],
            "allowed_tools": "mcp__sources__*",
        }
    elif agent_label == "cursor-tools":
        agent_kwargs = {"mcp_servers": ["sources"]}
        cursor_workspace = _ensure_cursor_writer_workspace(
            workspace_dir,
            event_sink=event_sink,
        )
        tool_config.update(
            {
                "cursor_workspace": str(cursor_workspace),
                "approve_mcps": True,
                "cursor_mode": "plan",
                "sandbox": "enabled",
            }
        )
    elif agent_label in {
        "gemini-tools",
        "grok-tools",
        "deepseek-tools",
        "qwen-tools",
        "agy-tools",
    }:
        agent_kwargs = {
            "mcp_servers": ["sources"],
        }
    else:
        raise LinearPipelineError(
            f"Unknown -tools writer {agent_label!r}; expected one of "
            "cursor-tools / codex-tools / claude-tools / gemini-tools / "
            "grok-tools / deepseek-tools / qwen-tools / agy-tools."
        )

    canonical_agent = agent_label.split("-", 1)[0]
    mcp_dict, diagnostics = build_mcp_tool_config(canonical_agent, **agent_kwargs)
    if canonical_agent in {"claude", "gemini"}:
        diagnostics = _mcp_config_server_name_diagnostics(
            diagnostics,
            load_mcp_config=_load_mcp_config,
        )
    _emit(event_sink, "mcp_config_resolved", writer=agent_label, **diagnostics)

    requested = diagnostics["requested_servers"]
    resolved = diagnostics["resolved_servers"]
    status = diagnostics["resolution_status"]
    if requested and not resolved:
        raise LinearPipelineError(
            f"Writer {agent_label!r} requested MCP servers {requested!r} "
            f"but resolver returned none ({status}). Refusing to dispatch "
            "tool-less."
        )
    if mcp_dict:
        tool_config.update(mcp_dict)
    if codex_disable_features:
        tool_config["disable_features"] = codex_disable_features
    if agent_label == "codex-tools":
        # Materialize the scoped CODEX_HOME AFTER mcp_config_resolved so the
        # event stream's first row remains the canonical MCP-resolution
        # diagnostic (downstream consumers + tests rely on the ordering).
        codex_home_override = _ensure_codex_writer_home(event_sink=event_sink)
        tool_config["codex_home_override"] = codex_home_override
    if agent_label == "claude-tools":
        deploy_result = ensure_claude_writer_agent_deployed()
        _emit(event_sink, "claude_writer_agent_deployed", writer=agent_label, **deploy_result)
        tool_config["agent"] = "curriculum-writer"
    assert tool_config.get("output_format") == "stream-json", (
        f"tool-call writers must keep output_format='stream-json'; got {tool_config.get('output_format')!r}"
    )
    return tool_config


def _mcp_config_server_name_diagnostics(
    diagnostics: dict[str, Any],
    *,
    load_mcp_config: Callable[[Path], dict[str, Any] | None],
) -> dict[str, Any]:
    """Validate non-Codex MCP server names against the canonical repo config."""
    requested = list(diagnostics["requested_servers"])
    if not requested:
        return diagnostics

    config_path = Path(diagnostics["config_path"])
    data = load_mcp_config(config_path)
    if not data:
        return {
            **diagnostics,
            "resolved_servers": [],
            "resolution_status": "config_missing",
            "missing_server_names": requested,
        }

    servers = data.get("mcpServers")
    if not isinstance(servers, dict) or not servers:
        return {
            **diagnostics,
            "resolved_servers": [],
            "resolution_status": "config_empty",
            "missing_server_names": requested,
        }

    resolved = [server_name for server_name in requested if server_name in servers]
    missing = [server_name for server_name in requested if server_name not in servers]
    return {
        **diagnostics,
        "resolved_servers": resolved,
        "resolution_status": "ok" if resolved else "servers_not_found",
        "missing_server_names": missing,
    }


def invoke_writer(
    prompt: str,
    writer: str,
    *,
    cwd: Path = PROJECT_ROOT,
    invoker: Callable[..., Any] | None = None,
    module: str | None = None,
    sections: list[str] | None = None,
    event_sink: Callable[..., None] | None = None,
    tool_trace_path: Path | None = None,
    stdout_silence_timeout: int | None = None,
    effort: str | None = None,
) -> str:
    """Call the selected writer through the universal agent runtime.

    ``effort`` overrides ``WRITER_DEFAULTS[writer]["effort"]`` when provided.
    The bakeoff runner uses this to probe writer behaviour at higher
    reasoning budgets without mutating the global default.
    """
    if writer not in WRITER_CHOICES:
        raise LinearPipelineError(f"Unknown writer {writer!r}; expected one of {WRITER_CHOICES}")
    if invoker is None:
        from scripts.agent_runtime.runner import invoke as invoker

    defaults = WRITER_DEFAULTS[writer]
    resolved_effort = effort if effort is not None else defaults["effort"]
    agent_name = writer.split("-", 1)[0]
    result = invoker(
        agent_name,
        prompt,
        mode="workspace-write",
        cwd=cwd,
        model=defaults["model"],
        task_id="phase-4-a1-20-writer",
        entrypoint="dispatch",
        effort=resolved_effort,
        tool_config=_runtime_tool_config(writer, workspace_dir=cwd, event_sink=event_sink),
        event_sink=event_sink,
        stdout_silence_timeout=stdout_silence_timeout,
    )
    response = getattr(result, "response", None)
    if not response:
        # Surface the runtime's debug fields so silent-no-response failures
        # (e.g. codex CLI dying at startup with returncode=1) are diagnosable
        # without re-running with bespoke instrumentation. Filed as part of
        # the 2026-05-19 B1 bakeoff codex-tools investigation: original error
        # said only "Writer call returned no response" while the runtime
        # actually had returncode=1, duration_s<1.0 in its usage record.
        stderr_excerpt = getattr(result, "stderr_excerpt", None) or "<empty>"
        returncode = getattr(result, "returncode", None)
        duration_s = getattr(result, "duration_s", None)
        stalled = getattr(result, "stalled", None)
        rate_limited = getattr(result, "rate_limited", None)
        raise LinearPipelineError(
            "Writer call returned no response "
            f"(writer={writer}, effort={resolved_effort}, "
            f"returncode={returncode}, duration_s={duration_s}, "
            f"stalled={stalled}, rate_limited={rate_limited}, "
            f"stderr_excerpt={stderr_excerpt!r})"
        )
    response_text = str(response)
    module_ref = module or _prompt_module_ref(prompt)
    section_names = list(sections) if sections is not None else _prompt_sections(prompt)
    tool_calls = _runtime_tool_calls(result)
    # Backfill from sidecar JSONL when the runtime adapter is a black box.
    # ``hermes -z`` strips tool-call traces from stdout by design, so the
    # HermesGrok/Qwen/DeepSeek adapters return ``tool_calls_total=None`` —
    # which makes ``_runtime_tool_calls`` return ``None``. Without backfill,
    # in-memory writer-runtime gates (``detect_tool_theatre``,
    # ``emit_writer_response_telemetry``, ``_enforce_writer_runtime_gates``)
    # all see zero calls and treat every cited tool as a tool-theatre
    # violation, even when the post_tool_call shell hook actually captured
    # the calls in ``$cwd/*.write.jsonl``. The gate-side
    # ``_load_writer_tool_calls`` already reads that file; this restores
    # parity for the in-memory path. Empirical evidence: 2026-05-19 b1
    # genitive-nuances build, whose ``phase_writer_summary`` reported
    # ``tool_calls_total: null`` while the hook captured 11 real MCP calls.
    if tool_calls is None:
        sidecar_calls = _load_writer_tool_calls(Path(cwd))
        if sidecar_calls:
            tool_calls = [dict(call) for call in sidecar_calls]
    if tool_trace_path is not None and tool_calls is not None:
        tool_trace_path.parent.mkdir(parents=True, exist_ok=True)
        existing_calls: list[Any] = []
        if tool_trace_path.exists():
            try:
                existing_data = json.loads(tool_trace_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing_data = []
            if isinstance(existing_data, list):
                existing_calls = existing_data
        tool_trace_path.write_text(
            json.dumps(
                [*existing_calls, *tool_calls],
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )
    if module_ref and section_names:
        phase_writer_summary = emit_writer_response_telemetry(
            response_text,
            writer=writer,
            module=module_ref,
            sections=section_names,
            tool_calls=tool_calls,
            event_sink=event_sink,
        )
        _enforce_writer_runtime_gates(
            writer=writer,
            module=module_ref,
            phase_writer_summary=phase_writer_summary,
            tool_calls=tool_calls,
            event_sink=event_sink,
        )
    return response_text


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
    fence_open_run = 0  # Backtick-run length of the OPEN fence (CommonMark).
    fence_lines: list[str] = []

    # CommonMark fence semantics (#2026-05-20 design triangulation via Codex +
    # DeepSeek consults): an opening fence of N>=3 backticks is closed by a
    # bare fence of at least N backticks. A 4-backtick OUTER fence therefore
    # permits arbitrary 3-backtick inner content fences to pass through. This
    # mirrors the existing `_attempt_module_md_only_recovery` precedent at
    # ~line 3013 (which already implements N>=4 wrappers for the correction
    # path). Before this rewrite the parser treated every triple-backtick
    # line as a structural fence-toggle, which (a) forced writers to forgo
    # markdown code blocks inside `module.md`, (b) produced "unnamed fenced
    # block" HARD-FAILs whenever a writer ignored the prohibition (2026-05-19
    # a2/aspect-concept build), and (c) fought CommonMark instead of using
    # it. Backward-compatible: 3-backtick artifact fences still work exactly
    # as before because the close-fence run-length check matches when both
    # opens and closes are 3.
    _FENCE_LINE_RE = re.compile(r"^\s*(?P<run>`{3,})(?P<info>.*)$")

    for line_no, line in enumerate(output.splitlines(), start=1):
        fence_match = _FENCE_LINE_RE.match(line)
        if fence_match:
            run_len = len(fence_match.group("run"))
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
                fence_open_run = run_len
                if fence_name is None:
                    raise LinearPipelineError(f"Writer output contains unnamed fenced block at line {line_no}")
                if fence_name in artifacts:
                    raise LinearPipelineError(f"Writer output contains duplicate artifact block: {fence_name}")
                if fence_name in WRITER_JSON_ARTIFACTS and fence_lang != "json":
                    got = fence_lang or "<none>"
                    raise LinearPipelineError(f"{fence_name} must be fenced as json, got {got} at line {line_no}")
                in_fence = True
                fence_lines = []
                continue

            # In-fence backtick line: only close on a bare run >= open run AND
            # an empty info string (CommonMark close-fence rule). A shorter
            # run, OR a run with content after the backticks, is treated as
            # inner content (writers can use 3-backtick code blocks inside
            # a 4-backtick module.md wrapper). The empty-info check guards
            # against the rare case where the writer opens a NEW info-bearing
            # fence inside an artifact — that's content too, not a close.
            close_info = fence_match.group("info").strip()
            if run_len < fence_open_run or close_info:
                fence_lines.append(line)
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
            fence_open_run = 0
            fence_lines = []
            continue

        if in_fence:
            fence_lines.append(line)
            continue

        name = _artifact_name_from_label_line(line)
        if name in WRITER_ARTIFACTS:
            pending_name = name

    if in_fence:
        raise LinearPipelineError(f"Writer output has an unterminated fenced block for {fence_name}")

    missing = [name for name in WRITER_ARTIFACTS if name not in artifacts]
    extra = sorted(set(artifacts) - set(WRITER_ARTIFACTS))
    if missing or extra:
        raise LinearPipelineError(
            f"Writer output must contain exactly {WRITER_ARTIFACTS}. missing={missing} extra={extra}"
        )
    return {name: artifacts[name] for name in WRITER_ARTIFACTS}


def parse_writer_output(output: str) -> dict[str, str]:
    """Compatibility wrapper for the strict JSON writer-output parser."""
    return parse_writer_output_strict_json(output)


# Recognized info strings that identify a fence as the patched module.md.
# Accepted: ``` ```markdown file=module.md```, ``` ```markdown module.md```,
#           ``` ```module.md```, ``` ```file=module.md```.
# The module.md label is REQUIRED — a bare ``` ```markdown``` fence does not
# qualify because the gate semantics is "this is the patched module.md".
_MODULE_FENCE_INFO_RE = re.compile(
    r"\A\s*(?:markdown\s+(?:file=)?module\.md|(?:file=)?module\.md)\s*\Z",
)


def parse_writer_correction_module_only(response: str) -> str | None:
    """Extract the patched module.md from a single-fence correction response.

    The patch-bounded writer-correction prompt (`linear-writer-correction.md`)
    instructs the writer to return EXACTLY one fenced block labeled
    `module.md`, with no leading or trailing prose. This parser accepts that
    contract and rejects everything else:

    - leading prose before the fence
    - trailing prose after the fence
    - multiple fenced blocks (e.g., a strict-json 4-block writer response
      that incidentally contains a module.md fence)
    - bare ``` ```markdown``` fences without the module.md label
    - empty fence body

    **Outer-fence-wrapper tolerance**: when the writer's correction output
    is itself a fenced code block (a CommonMark convention for "code block
    containing code blocks", using ≥4 backticks to disambiguate from the
    inner triple-backticks), peel one wrapper layer before parsing. This
    was observed 2026-05-19 from deepseek-v4-pro xhigh on a2/aspect-concept
    word_count correction: model emitted ````` ```` markdown\\n```markdown
    file=module.md\\n...\\n```\\n``` ````` and the strict 3-backtick split
    parser returned 5 parts instead of 3. Peeling one wrapper layer recovers
    the inner fence.

    Returns the module.md body (with one trailing newline) on the contract
    match, else None. Used by `_apply_writer_correction` for gates that only
    modify module.md (everything in WRITER_CORRECTION_GATES except
    `strict_json_parse`, which needs all four artifacts re-emitted).
    """
    if not isinstance(response, str):
        return None
    stripped = response.strip()
    # Peel one ≥4-backtick wrapper if present. The CommonMark convention is:
    # an opening fence of N backticks (N >= 3) is closed by a fence of EXACTLY
    # N backticks (or more). Writers use 4-backtick wrappers when their
    # content itself contains 3-backtick code blocks. We accept exactly one
    # wrapper level — nested wrappers would be hostile to the parser
    # contract and should still fail.
    if stripped.startswith("````"):
        # Find the run length of the opening fence.
        open_run = 0
        for ch in stripped:
            if ch == "`":
                open_run += 1
            else:
                break
        # The opening fence has an optional info-line (which we discard) until
        # the first newline. The matching close is a run of at least open_run
        # backticks on its own line.
        after_open = stripped[open_run:]
        nl_idx = after_open.find("\n")
        if nl_idx == -1:
            return None
        wrapper_info = after_open[:nl_idx].strip()
        # Allowed wrapper info-lines: empty, "markdown", or a generic language
        # hint. Anything that looks like a real fence label (file=...) means
        # this isn't a wrapper — it's a single bare fence we shouldn't peel.
        if "file=" in wrapper_info:
            # Don't peel — let the normal triple-backtick parser handle it.
            pass
        else:
            inner = after_open[nl_idx + 1 :]
            # Strip the matching close fence at the end of the inner block.
            inner_stripped = inner.rstrip()
            close_marker = "`" * open_run
            if inner_stripped.endswith(close_marker):
                inner_stripped = inner_stripped[:-open_run].rstrip()
                stripped = inner_stripped
    # Hard guards: the entire (possibly unwrapped) response must be one
    # triple-fence block.
    if not (stripped.startswith("```") and stripped.endswith("```")):
        return None
    # Splitting on the triple-backtick delimiter gives exactly 3 parts when
    # the response is one fence: ["", fence_content, ""]. More parts → there
    # are extra fences (i.e., 4-block writer output) or stray ``` characters,
    # which violates the contract.
    parts = stripped.split("```")
    if len(parts) != 3 or parts[0] != "" or parts[2] != "":
        return None
    fence_content = parts[1]
    info_line, sep, body = fence_content.partition("\n")
    if sep == "":  # No body delimiter — fence is malformed
        return None
    if not _MODULE_FENCE_INFO_RE.fullmatch(info_line):
        return None
    body = body.strip()
    if not body:
        return None
    return body + "\n"


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
        if name == "activities.yaml" and isinstance(parsed, dict) and (
            "inline" in parsed or "workbook" in parsed
        ):
            activity_items: list[Any] = []
            for section_name in ("inline", "workbook"):
                section = parsed.get(section_name, [])
                if section is None:
                    continue
                if not isinstance(section, list):
                    raise LinearPipelineError(
                        f"{name} {section_name} section must be a YAML list"
                    )
                activity_items.extend(section)
            if not all(isinstance(item, dict) for item in activity_items):
                raise LinearPipelineError(f"{name} entries must be mappings")
            continue
        if not isinstance(parsed, list):
            raise LinearPipelineError(f"{name} must be a bare YAML list")
        if not all(isinstance(item, dict) for item in parsed):
            raise LinearPipelineError(f"{name} entries must be mappings")

    module_dir.mkdir(parents=True, exist_ok=True)
    for name in WRITER_ARTIFACTS:
        (module_dir / name).write_text(str(artifacts[name]), encoding="utf-8")
    module_ref = _module_ref_from_module_dir(module_dir)
    for finding in detect_unmarkered_negative_examples(str(artifacts["activities.yaml"])):
        fields = dict(finding)
        if module_ref is not None:
            fields["module"] = module_ref
        emit_event("writer_negative_example_unmarkered", **fields)


def run_stress_annotation(module_dir: Path) -> dict[str, Any]:
    """Deterministically add Ukrainian stress marks to writer artifacts."""
    from scripts.pipeline.stress_annotator import annotate_file

    targets = ("module.md", "vocabulary.yaml")
    counts: dict[str, int] = {}
    for target in targets:
        path = module_dir / target
        _read_required(path)
        counts[target] = annotate_file(path)
    return {
        "passed": True,
        "phase": "stress_annotation",
        "files": counts,
        "total_added": sum(counts.values()),
    }


def strip_stress_marks_for_seminar(module_dir: Path) -> dict[str, Any]:
    """Remove residual stress marks from seminar authoring artifacts."""
    targets = ("module.md", "vocabulary.yaml", "activities.yaml")
    counts: dict[str, int] = {}
    for target in targets:
        path = module_dir / target
        text = _read_required(path)
        count = text.count("\u0301")
        counts[target] = count
        if count:
            path.write_text(text.replace("\u0301", ""), encoding="utf-8")
    return {
        "passed": True,
        "phase": "stress_annotation",
        "skipped": True,
        "reason": "seminar level - no stress",
        "files": counts,
        "total_removed": sum(counts.values()),
    }


def run_ulp_fidelity_gate(
    module_dir: Path,
    plan_path: Path,
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    """Run the deterministic ULP fidelity gate on final post-stress module.md."""
    from scripts.audit.ulp_fidelity_gate import check_ulp_fidelity

    plan = plan_check(plan_path)
    module_text = _read_required(module_dir / "module.md")
    return check_ulp_fidelity(module_text, plan, profile=profile)


def run_ulp_fidelity_with_correction(
    module_dir: Path,
    plan_path: Path,
    *,
    profile: str | None = None,
    writer: str = "claude-tools",
    writer_corrector: Callable[[CorrectionContext], str | Mapping[str, str] | None] | None = None,
    invoker: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Run ULP fidelity and apply one ADR-008 writer correction when needed."""
    report = run_ulp_fidelity_gate(module_dir, plan_path, profile=profile)
    if report.get("passed") is True:
        return report

    correction_payload = _apply_writer_correction(
        "ulp_fidelity",
        report,
        qg_report={"gates": {"ulp_fidelity": report}},
        module_dir=module_dir,
        plan_path=plan_path,
        writer_corrector=writer_corrector,
        writer=writer,
        invoker=invoker,
    )
    artifact: dict[str, Any] = {
        "round": 1,
        "before": report,
        "correction": correction_payload,
    }

    if correction_payload and correction_payload.get("applied") in {
        "module_patch",
        "strict_json_artifacts",
        "writer_artifacts_mapping",
    }:
        plan = plan_check(plan_path)
        level = str(plan.get("level") or "").lower()
        if level in SEMINAR_LEVELS:
            stress_annotation = strip_stress_marks_for_seminar(module_dir)
        else:
            stress_annotation = run_stress_annotation(module_dir)
        write_json(module_dir / "stress_annotation.json", stress_annotation)
        artifact["stress_annotation"] = stress_annotation
        report = run_ulp_fidelity_gate(module_dir, plan_path, profile=profile)
        artifact["after"] = report

    write_json(module_dir / "ulp_fidelity_correction_r1.json", artifact)
    return report


def run_wiki_coverage_gate(
    *,
    manifest: Mapping[str, Any] | str | Path,
    writer_output: str,
    module_dir: Path,
    level: str | None = None,
    obligation_checklist: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from scripts.audit.wiki_coverage_gate import check_wiki_coverage_paths

    result = check_wiki_coverage_paths(
        manifest=manifest,
        implementation_map=writer_output,
        module_dir=module_dir,
        level=level,
        obligation_checklist=obligation_checklist,
    )
    if result.get("passed") is False:
        proposals = list(result.get("fix_proposals") or [])
        emit_event(
            "wiki_coverage_fix_proposals",
            slug=_wiki_manifest_slug(manifest, module_dir),
            fail_count=len(proposals),
            proposals=proposals,
        )
    return result


def _wiki_manifest_slug(manifest: Mapping[str, Any] | str | Path, module_dir: Path) -> str:
    if isinstance(manifest, Mapping):
        return str(manifest.get("slug") or module_dir.name)
    try:
        raw = str(manifest)
        if raw.lstrip().startswith(("{", "[")):
            data = json.loads(raw)
        else:
            path = Path(manifest)
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        data = {}
    if isinstance(data, Mapping):
        return str(data.get("slug") or module_dir.name)
    return module_dir.name


def review_context(
    plan: Mapping[str, Any],
    plan_content: str,
    generated_content: str,
    dim: str,
    wiki_manifest: str | Mapping[str, Any] | None = None,
    implementation_map: Mapping[str, Any] | None = None,
    *,
    use_generator: bool = False,
    obligation_checklist: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Build context for one independent per-dimension LLM QG prompt."""
    if dim not in QG_DIMS:
        raise LinearPipelineError(f"Unknown LLM QG dimension: {dim}")
    level = str(plan["level"])
    sequence = int(plan["sequence"])
    learner_state = build_learner_state(level.lower(), sequence)
    if wiki_manifest is None:
        wiki_manifest_data = build_wiki_manifest_data(level=level.lower(), slug=str(plan["slug"]), plan=plan)
        wiki_manifest_text = _render_prompt_wiki_manifest(wiki_manifest_data)
        manifest_for_checklist: str | Mapping[str, Any] = wiki_manifest_data
    else:
        wiki_manifest_text = _render_prompt_wiki_manifest(wiki_manifest)
        manifest_for_checklist = wiki_manifest

    if implementation_map is None:
        manifest_for_map = _manifest_mapping(manifest_for_checklist)
        if manifest_for_map is None:
            impl_map_contract = "(no implementation_map provided and wiki_manifest was not parseable)"
        else:
            from scripts.build.phases.implementation_map import render_for_writer_prompt, seed_implementation_map

            impl_map_contract = render_for_writer_prompt(
                seed_implementation_map(dict(manifest_for_map), plan=dict(plan))
            )
    else:
        from scripts.build.phases.implementation_map import render_for_writer_prompt

        impl_map_contract = render_for_writer_prompt(dict(implementation_map))

    context = {
        "LEVEL": level,
        "MODULE_NUM": str(sequence),
        "MODULE_SLUG": str(plan["slug"]),
        "WORD_TARGET": str(plan["word_target"]),
        "SIZE_POLICY": render_reviewer_size_policy(
            build_size_policy_for_plan(
                plan,
                actual_words=_writer_draft_countable_words(generated_content),
            )
        ),
        "LEARNER_STATE": format_learner_state(learner_state),
        "IMMERSION_RULE": get_immersion_rule(
            level.lower(),
            sequence,
            learner_state=learner_state,
            letter_module=bool(plan.get("letter_module")),
        ),
        "CONTRACT_YAML": _contract_yaml(plan),
        "PLAN_CONTENT": plan_content,
        "GENERATED_CONTENT": generated_content,
        "WIKI_MANIFEST": wiki_manifest_text,
        "IMPLEMENTATION_MAP_CONTRACT": impl_map_contract,
        "DIM": dim,
    }
    if use_generator:
        # V7.2 Step 5: inject the registry-composed reviewer-rules block + the
        # SAME single-source Obligation Checklist the writer received, for the
        # generator-fed reviewer template (`linear-review-dim.generated.md`).
        # Keyed behind the flag so the legacy return above stays byte-identical
        # with the flag OFF.
        from scripts.build.prompt_generator import (
            build_obligation_checklist,
            build_obligation_checklist_object,
            build_reviewer_rules_block,
            track_for_level,
        )

        rules_block = build_reviewer_rules_block(level.lower(), track_for_level(level))
        # shared.contract rules (e.g. R-ACTIVITY-COMPOSITION) can carry build-time
        # tokens like {ACTIVITY_COUNT_TARGET}; resolve them against the reviewer
        # context plus the level's activity config so none survive into the prompt.
        token_map = {**context, **_activity_config(level, sequence, str(plan["slug"]))}
        context["GENERATED_REVIEWER_RULES"] = _inline_prompt_tokens(rules_block, token_map)
        checklist = (
            dict(obligation_checklist)
            if obligation_checklist is not None
            else build_obligation_checklist_object(
                manifest_for_checklist,
                seeded_map=implementation_map,
            )
        )
        context["OBLIGATION_CHECKLIST"] = build_obligation_checklist(
            manifest_for_checklist,
            obligation_checklist=checklist,
        )
    return context


def render_review_prompt(
    plan: Mapping[str, Any],
    plan_content: str,
    generated_content: str,
    dim: str,
    wiki_manifest: str | Mapping[str, Any] | None = None,
    implementation_map: Mapping[str, Any] | None = None,
    *,
    use_generator: bool = False,
    obligation_checklist: Mapping[str, Any] | None = None,
) -> str:
    template_path = (
        generated_review_prompt_path()
        if use_generator
        else PROJECT_ROOT / "scripts" / "build" / "phases" / "linear-review-dim.md"
    )
    return render_phase_prompt(
        template_path,
        review_context(
            plan,
            plan_content,
            generated_content,
            dim,
            wiki_manifest,
            implementation_map,
            use_generator=use_generator,
            obligation_checklist=obligation_checklist,
        ),
    )


def wiki_coverage_review_context(
    plan: Mapping[str, Any],
    plan_content: str,
    generated_content: str,
    wiki_manifest: str | Mapping[str, Any],
    wiki_coverage_gate: Mapping[str, Any],
) -> dict[str, str]:
    level = str(plan["level"])
    sequence = int(plan["sequence"])
    manifest_text = (
        wiki_manifest if isinstance(wiki_manifest, str) else json.dumps(wiki_manifest, ensure_ascii=False, indent=2)
    )
    return {
        "LEVEL": level,
        "MODULE_NUM": str(sequence),
        "MODULE_SLUG": str(plan["slug"]),
        "WORD_TARGET": str(plan["word_target"]),
        "PLAN_CONTENT": plan_content,
        "GENERATED_CONTENT": generated_content,
        "WIKI_MANIFEST": manifest_text,
        "WIKI_COVERAGE_GATE": json.dumps(
            dict(wiki_coverage_gate),
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
    }


def render_wiki_coverage_review_prompt(
    plan: Mapping[str, Any],
    plan_content: str,
    generated_content: str,
    wiki_manifest: str | Mapping[str, Any],
    wiki_coverage_gate: Mapping[str, Any],
) -> str:
    return render_phase_prompt(
        PROJECT_ROOT / "scripts" / "build" / "phases" / "linear-review-wiki-coverage.md",
        wiki_coverage_review_context(
            plan,
            plan_content,
            generated_content,
            wiki_manifest,
            wiki_coverage_gate,
        ),
    )


def wiki_coverage_correction_context(
    *,
    plan: Mapping[str, Any],
    failure_group_key: str,
    fix_proposals: Sequence[Mapping[str, Any]],
    artifact_text: str,
    coverage_pct_before: float,
    iteration: int,
) -> dict[str, str]:
    """Build prompt context for one batched wiki_coverage correction group."""
    level = str(plan["level"])
    sequence = int(plan["sequence"])
    return {
        "LEVEL": level,
        "MODULE_NUM": str(sequence),
        "MODULE_SLUG": str(plan["slug"]),
        "WORD_TARGET": str(plan["word_target"]),
        "FAILURE_GROUP_KEY": failure_group_key,
        "FIX_PROPOSALS_YAML": yaml.safe_dump(
            list(fix_proposals),
            allow_unicode=True,
            sort_keys=False,
        ).strip(),
        "ARTIFACT_TEXT": artifact_text,
        "COVERAGE_PCT_BEFORE": f"{coverage_pct_before:.4f}",
        "ITERATION": str(iteration),
    }


def render_wiki_coverage_correction_prompt(
    *,
    plan: Mapping[str, Any],
    failure_group_key: str,
    fix_proposals: Sequence[Mapping[str, Any]],
    artifact_text: str,
    coverage_pct_before: float,
    iteration: int,
) -> str:
    return render_phase_prompt(
        PROJECT_ROOT / "scripts" / "build" / "phases" / "linear-correction-wiki-coverage.md",
        wiki_coverage_correction_context(
            plan=plan,
            failure_group_key=failure_group_key,
            fix_proposals=fix_proposals,
            artifact_text=artifact_text,
            coverage_pct_before=coverage_pct_before,
            iteration=iteration,
        ),
    )


def wiki_coverage_narrow_correction_context(
    *,
    plan: Mapping[str, Any],
    fix_proposal: Mapping[str, Any],
    artifact_text: str,
    previous_batched_attempts: int,
) -> dict[str, str]:
    """Build prompt context for one per-obligation wiki_coverage correction."""
    level = str(plan["level"])
    sequence = int(plan["sequence"])
    expected_treatment = fix_proposal.get("expected_treatment")
    manifest_payload = fix_proposal.get("manifest_payload")
    return {
        "LEVEL": level,
        "MODULE_NUM": str(sequence),
        "MODULE_SLUG": str(plan["slug"]),
        "WORD_TARGET": str(plan.get("word_target", "")),
        "OBLIGATION_ID": str(fix_proposal.get("obligation_id") or ""),
        "OBLIGATION_TYPE": str(fix_proposal.get("obligation_type") or ""),
        "FAILURE_REASON": str(fix_proposal.get("failure_reason") or ""),
        "EXPECTED_TREATMENT": yaml.safe_dump(
            dict(expected_treatment) if isinstance(expected_treatment, Mapping) else {},
            allow_unicode=True,
            sort_keys=False,
        ).strip(),
        "MANIFEST_PAYLOAD": yaml.safe_dump(
            dict(manifest_payload) if isinstance(manifest_payload, Mapping) else {},
            allow_unicode=True,
            sort_keys=False,
        ).strip(),
        "SURGICAL_DIFF_HINT": str(fix_proposal.get("surgical_diff_hint") or ""),
        "CURRENT_ARTIFACT_STATE": str(fix_proposal.get("current_artifact_state") or ""),
        "FULL_ARTIFACT_TEXT": artifact_text,
        "PREVIOUS_BATCHED_ATTEMPTS": str(previous_batched_attempts),
    }


def render_wiki_coverage_narrow_correction_prompt(
    *,
    plan: Mapping[str, Any],
    fix_proposal: Mapping[str, Any],
    artifact_text: str,
    previous_batched_attempts: int,
) -> str:
    return render_phase_prompt(
        PROJECT_ROOT / "scripts" / "build" / "phases" / "linear-correction-wiki-coverage-narrow.md",
        wiki_coverage_narrow_correction_context(
            plan=plan,
            fix_proposal=fix_proposal,
            artifact_text=artifact_text,
            previous_batched_attempts=previous_batched_attempts,
        ),
    )


def llm_qg_max_rounds_for_level(level: str | None) -> int:
    """Return the LLM-QG review-round budget for a curriculum level."""
    return (
        LLM_QG_SEMINAR_MAX_ROUNDS
        if str(level or "").strip().lower() in SEMINAR_LEVELS
        else LLM_QG_CORE_MAX_ROUNDS
    )


def python_qg_max_correction_rounds_for_level(level: str | None) -> int:
    """Return the Python-QG correction-round budget for a curriculum level."""
    return (
        PYTHON_QG_SEMINAR_MAX_CORRECTION_ROUNDS
        if str(level or "").strip().lower() in SEMINAR_LEVELS
        else PYTHON_QG_CORE_MAX_CORRECTION_ROUNDS
    )


def llm_qg_reviewer_samples_for_level(level: str | None) -> int:
    """Return the per-dim LLM-QG reviewer sample count for a curriculum level."""
    profile = "seminar" if str(level or "").strip().lower() in SEMINAR_LEVELS else "core"
    return max(1, int(LLM_QG_REVIEWER_SAMPLES.get(profile, 1)))


def _python_qg_level_from_plan_path(plan_path: Path) -> str | None:
    with contextlib.suppress(LinearPipelineError, OSError, yaml.YAMLError):
        return str(load_plan(plan_path).get("level") or "").strip().lower()
    return None


def _prompt_yaml_or_text(value: str | Mapping[str, Any] | None) -> str:
    if value is None:
        return "{}"
    if isinstance(value, str):
        return value
    return _yaml_inline(value)


def pedagogical_correction_context(
    *,
    plan: Mapping[str, Any],
    llm_qg: Mapping[str, Any],
    module_text: str,
    plan_content: str,
    wiki_manifest: str | Mapping[str, Any] | None = None,
    obligation_checklist: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Build prompt context for one insert-only pedagogical correction."""
    dimensions = llm_qg.get("dimensions")
    pedagogical = dimensions.get("pedagogical") if isinstance(dimensions, Mapping) else {}
    aggregate = llm_qg.get("aggregate")
    findings = {
        "pedagogical": dict(pedagogical) if isinstance(pedagogical, Mapping) else {},
        "aggregate": dict(aggregate) if isinstance(aggregate, Mapping) else {},
    }
    return {
        "LEVEL": str(plan.get("level") or ""),
        "MODULE_NUM": str(plan.get("sequence") or ""),
        "MODULE_SLUG": str(plan.get("slug") or ""),
        "PEDAGOGICAL_FINDINGS": _yaml_inline(findings),
        "PLAN_CONTENT": plan_content,
        "WIKI_MANIFEST": _prompt_yaml_or_text(wiki_manifest),
        "OBLIGATION_CHECKLIST": _prompt_yaml_or_text(obligation_checklist),
        "MODULE_CONTENT": module_text,
    }


def render_pedagogical_correction_prompt(
    *,
    plan: Mapping[str, Any],
    llm_qg: Mapping[str, Any],
    module_text: str,
    plan_content: str,
    wiki_manifest: str | Mapping[str, Any] | None = None,
    obligation_checklist: Mapping[str, Any] | None = None,
) -> str:
    return render_phase_prompt(
        PROJECT_ROOT / "scripts" / "build" / "phases" / "linear-correction-pedagogical.md",
        pedagogical_correction_context(
            plan=plan,
            llm_qg=llm_qg,
            module_text=module_text,
            plan_content=plan_content,
            wiki_manifest=wiki_manifest,
            obligation_checklist=obligation_checklist,
        ),
    )


def _quote_items_from_text(text: str) -> list[str]:
    quotes: list[str] = []
    quote_re = re.compile(r'"(?P<double>[^"\n]{1,500})"|“(?P<curly>[^”\n]{1,500})”|«(?P<guillemets>[^»\n]{1,500})»')
    for match in quote_re.finditer(text):
        quote = match.group("double") or match.group("curly") or match.group("guillemets")
        if quote:
            quotes.append(_clean_telemetry_text(quote, TELEMETRY_MAX_QUOTE_CHARS))
    return quotes


def _evidence_quotes_from_payload(payload: Mapping[str, Any]) -> list[str]:
    raw_quotes = payload.get("evidence_quotes")
    quotes: list[str] = []
    if isinstance(raw_quotes, list):
        quotes.extend(
            _clean_telemetry_text(item, TELEMETRY_MAX_QUOTE_CHARS) for item in raw_quotes if str(item).strip()
        )

    evidence = payload.get("evidence")
    if isinstance(evidence, list):
        quotes.extend(_clean_telemetry_text(item, TELEMETRY_MAX_QUOTE_CHARS) for item in evidence if str(item).strip())
    elif isinstance(evidence, str):
        quotes.extend(_quote_items_from_text(evidence))
        if not quotes and evidence.strip():
            quotes.append(_clean_telemetry_text(evidence, TELEMETRY_MAX_QUOTE_CHARS))

    deduped: list[str] = []
    seen: set[str] = set()
    for quote in quotes:
        if quote and quote not in seen:
            seen.add(quote)
            deduped.append(quote)
        if len(deduped) >= TELEMETRY_MAX_QUOTES:
            break
    return deduped


def _rubric_mapping_from_payload(payload: Mapping[str, Any]) -> str:
    for key in ("rubric_mapping", "mapping", "rationale", "rubric_rationale"):
        value = payload.get(key)
        if value:
            return _clean_telemetry_text(value, TELEMETRY_MAX_MAPPING_CHARS)
    mappings = payload.get("evidence_mapping")
    if isinstance(mappings, list) and mappings:
        return _clean_telemetry_text("; ".join(str(item) for item in mappings), TELEMETRY_MAX_MAPPING_CHARS)
    return ""


def emit_reviewer_dim_telemetry(
    payload: Mapping[str, Any],
    *,
    reviewer: str,
    module: str,
    writer_under_review: str,
    dim: str,
    event_sink: Callable[..., None] | None = None,
) -> None:
    """Emit one reviewer_dim_evidence event from a parsed per-dim response."""
    score = payload.get("score")
    _emit(
        event_sink,
        "reviewer_dim_evidence",
        reviewer=reviewer,
        module=module,
        writer_under_review=writer_under_review,
        dim=dim,
        evidence_quotes=_evidence_quotes_from_payload(payload),
        rubric_mapping=_rubric_mapping_from_payload(payload),
        score=float(score) if isinstance(score, int | float) else score,
    )


def _audit_type_for_tool(tool: str, explicit: Any = None) -> str:
    audit_type = str(explicit or "").strip()
    if audit_type in REVIEW_AUDIT_TYPES:
        return audit_type
    if tool in {"search_grinchenko_1907", "search_literary", "search_definitions", "search_definitions_slovnyk"}:
        return "source_attribution"
    if tool in {"search_text", "query_wikipedia"}:
        return "quote_verification"
    if tool in {"search_style_guide", "search_idioms"}:
        return "sovietization_check"
    return "modern_form_check"


def _items_checked_for_audit(call: Mapping[str, Any], args: Any, result: Any) -> int:
    if isinstance(call.get("items_checked"), int | float):
        return int(call["items_checked"])
    arg_count = _count_arg_items(args)
    if arg_count is not None:
        return arg_count
    if isinstance(result, Mapping) and isinstance(result.get("items_checked"), int | float):
        return int(result["items_checked"])
    if isinstance(result, list | tuple | set):
        return len(result)
    return 1


def _items_failed_for_audit(call: Mapping[str, Any], result: Any) -> int:
    if isinstance(call.get("items_failed"), int | float):
        return int(call["items_failed"])
    if isinstance(result, Mapping):
        for key in ("items_failed", "failed"):
            if isinstance(result.get(key), int | float):
                return int(result[key])
    return 0


def _flags_for_audit(call: Mapping[str, Any], result: Any) -> list[str]:
    flags = call.get("flags_raised")
    if flags is None and isinstance(result, Mapping):
        flags = result.get("flags_raised") or result.get("flags")
    if not isinstance(flags, list):
        return []
    return [_clean_telemetry_text(flag, 120) for flag in flags[:TELEMETRY_MAX_FAILED_WORDS]]


def emit_reviewer_audit_telemetry(
    tool_calls: list[Mapping[str, Any]],
    *,
    reviewer: str,
    module: str,
    writer_under_review: str,
    dim: str,
    event_sink: Callable[..., None] | None = None,
) -> dict[str, int]:
    """Emit reviewer audit-call telemetry and return roll-up counters."""
    calls_total = 0
    flags_total = 0
    for call in tool_calls:
        tool = _normalize_tool_name(call.get("tool") or call.get("tool_name") or call.get("name"))
        if tool not in WRITER_TOOL_NAMES:
            continue
        args = call.get("args", call.get("arguments", {}))
        result = call.get("result", call.get("response"))
        flags = _flags_for_audit(call, result)
        calls_total += 1
        flags_total += len(flags)
        _emit(
            event_sink,
            "reviewer_audit_call",
            reviewer=reviewer,
            module=module,
            writer_under_review=writer_under_review,
            dim=str(call.get("dim") or dim),
            audit_type=_audit_type_for_tool(tool, call.get("audit_type")),
            tool=tool,
            items_checked=_items_checked_for_audit(call, args, result),
            items_failed=_items_failed_for_audit(call, result),
            flags_raised=flags,
        )
    return {"audit_calls_total": calls_total, "flags_raised_total": flags_total}


def invoke_reviewer_dim(
    prompt: str,
    reviewer: str,
    *,
    dim: str,
    writer_under_review: str,
    cwd: Path = PROJECT_ROOT,
    invoker: Callable[..., Any] | None = None,
    module: str | None = None,
    event_sink: Callable[..., None] | None = None,
    stdout_silence_timeout: int | None = None,
) -> str:
    """Call one per-dimension reviewer and emit response/audit telemetry."""
    if reviewer not in REVIEWER_CHOICES:
        raise LinearPipelineError(f"Unknown reviewer {reviewer!r}; expected one of {REVIEWER_CHOICES}")
    if invoker is None:
        from scripts.agent_runtime.runner import invoke as invoker

    defaults = REVIEWER_DEFAULTS[reviewer]
    agent_name = reviewer.split("-", 1)[0]
    result = invoker(
        agent_name,
        prompt,
        mode="read-only",
        cwd=cwd,
        model=defaults["model"],
        task_id=f"phase-4-review-{dim}",
        entrypoint="dispatch",
        effort=defaults["effort"],
        tool_config=_runtime_tool_config(reviewer, workspace_dir=cwd, event_sink=event_sink),
        event_sink=event_sink,
        stdout_silence_timeout=stdout_silence_timeout,
    )
    response = getattr(result, "response", None)
    if not response:
        raise LinearPipelineError(f"Reviewer call for {dim} returned no response")
    response_text = str(response)
    module_ref = module or _prompt_module_ref(prompt)
    if module_ref:
        parse_review_response(
            response_text,
            dim,
            reviewer=reviewer,
            module=module_ref,
            writer_under_review=writer_under_review,
            event_sink=event_sink,
        )
        tool_calls = _runtime_tool_calls(result)
        if tool_calls:
            emit_reviewer_audit_telemetry(
                tool_calls,
                reviewer=reviewer,
                module=module_ref,
                writer_under_review=writer_under_review,
                dim=dim,
                event_sink=event_sink,
            )
    return response_text


def _gate_int(gate_report: Mapping[str, Any], *keys: str, default: int = 0) -> int:
    for key in keys:
        value = gate_report.get(key)
        if isinstance(value, bool):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return default


def _yaml_inline(value: Any) -> str:
    return yaml.safe_dump(value, allow_unicode=True, sort_keys=False).strip()


def _render_vesum_surgical_instruction(gate_report: Mapping[str, Any]) -> str:
    missing_tokens = [str(token) for token in gate_report.get("missing", [])]
    token_text = ", ".join(missing_tokens) if missing_tokens else "(none listed)"
    return (
        f"The following tokens FAILED VESUM verification: {token_text}. "
        "For EACH offending token, find the smallest fix (likely a typo, wrong stress mark, "
        "or missing/extra character) and replace that EXACT token. Do NOT modify any other "
        "word in the prose. Do NOT change any prose that does not contain the offending token. "
        "If you cannot determine the correct form, leave the token as-is with a `<!-- VERIFY -->` "
        "HTML comment immediately after."
    )


def _render_word_count_surgical_instruction(gate_report: Mapping[str, Any]) -> str:
    current_count = _gate_int(gate_report, "count", "actual")
    target_min = _gate_int(gate_report, "min_with_tolerance", "minimum", "target", default=current_count)
    target_max = _gate_int(gate_report, "target_max", "max", "target", default=target_min)
    delta = max(0, target_min - current_count)
    return (
        f"Current: {current_count} words. Target: {target_min}-{target_max}. "
        f"Delta to floor: {delta} words. Append a NEW short section (2-3 sentences) "
        f"or extend the existing 'Підсумок' / final section with {delta}+10 words. "
        "Do NOT modify the existing prose, vocab, or dialogues. ONLY append."
    )


def _render_engagement_surgical_instruction(gate_report: Mapping[str, Any]) -> str:
    current_callouts = _gate_int(gate_report, "callout_count", "current_callouts")
    min_callouts = _gate_int(gate_report, "callout_min", "min_callouts", default=1)
    return (
        f"Current: {current_callouts} callouts. Target: >={min_callouts}. "
        "Insert a `:::tip` or `:::note` block at the end of the lesson body with a "
        "content-anchored mnemonic or cultural note. Do NOT modify existing prose."
    )


def _render_russianisms_surgical_instruction(gate_report: Mapping[str, Any]) -> str:
    findings = gate_report.get("critical_findings") or gate_report.get("detections") or gate_report.get("findings") or []
    return (
        "The following spans matched Russianism patterns: "
        f"{_yaml_inline(findings)}. Replace EXACTLY these spans with the suggested Ukrainian "
        "alternatives or rephrasings. Do NOT modify any other prose."
    )


def _render_l2_exposure_surgical_instruction(gate_report: Mapping[str, Any]) -> str:
    observed = gate_report.get("observed")
    required = gate_report.get("required")
    current_exposure = 0
    min_exposure = 0
    if isinstance(observed, Mapping):
        current_exposure = _gate_int(observed, "uk_example_sentences")
    if isinstance(required, Mapping):
        min_exposure = _gate_int(required, "uk_example_sentences")
    delta = max(0, min_exposure - current_exposure)
    return (
        f"Current: {current_exposure} UK example surfaces. Target: >={min_exposure}. "
        f"Add {delta}+2 NEW gate-countable Ukrainian example bullets or table rows. "
        "Do NOT modify existing examples."
    )


def _render_plan_sections_surgical_instruction(gate_report: Mapping[str, Any]) -> str:
    missing_headings = [str(heading) for heading in gate_report.get("missing_headings", [])]
    duplicate_headings = gate_report.get("duplicate_headings") or []
    instructions = []

    if missing_headings:
        instructions.append(
            "Missing H2 sections: "
            f"{', '.join(missing_headings)}. Add each missing `## <section>` heading at the "
            "appropriate plan position with the smallest amount of section content needed."
        )
    if duplicate_headings:
        instructions.append(
            "Duplicate stress-equivalent H2 sections: "
            f"{_yaml_inline(duplicate_headings)}. For each duplicate group, keep exactly one "
            "`##` heading for the planned section. Apply the smallest structural edit: merge "
            "unique prose under the kept section, demote supporting duplicate blocks to `###`, "
            "or delete an empty/redundant duplicate H2 block. Do not add a new duplicate heading."
        )
    if not instructions:
        instructions.append(
            "The plan section structure failed. Use the YAML diagnostic to add missing H2 sections "
            "or collapse duplicate H2 sections with the smallest structural edit."
        )

    return " ".join(instructions) + " Preserve all unrelated prose byte-for-byte. Do not re-author the lesson."


def _render_ulp_fidelity_surgical_instruction(gate_report: Mapping[str, Any]) -> str:
    failed = gate_report.get("failed_checks") or []
    return (
        f"ULP fidelity failed checks: {_yaml_inline(failed)}. "
        "Patch only `module.md`. Preserve the existing lesson structure, activities, "
        "vocabulary, citations, and already-good Ukrainian dialogue. Fix terminal ULP "
        "issues surgically: make every section opener begin with a Ukrainian-first "
        "example or dialogue chunk followed by an em-dash English gloss; for mixed "
        "English scaffold lines that introduce Ukrainian terms, use `український термін "
        "— English gloss` in the same line. Do not add hand stress marks as a goal; the "
        "pipeline re-runs deterministic stress annotation after your patch."
    )


def _render_default_surgical_instruction(gate_report: Mapping[str, Any]) -> str:
    return (
        "No gate-specific surgical playbook exists for this gate. Fix only the failed gate "
        "listed in the YAML feedback above. Apply the smallest append/insert patch possible, "
        "preserve previously-passing prose byte-for-byte, and do not re-author any section."
    )


GATE_SPECIFIC_INSTRUCTION_RENDERERS: dict[str, Callable[[Mapping[str, Any]], str]] = {
    "vesum_verified": _render_vesum_surgical_instruction,
    "word_count": _render_word_count_surgical_instruction,
    "plan_sections": _render_plan_sections_surgical_instruction,
    "engagement_floor": _render_engagement_surgical_instruction,
    "russianisms_strict": _render_russianisms_surgical_instruction,
    "l2_exposure_floor": _render_l2_exposure_surgical_instruction,
    "ulp_fidelity": _render_ulp_fidelity_surgical_instruction,
}


def render_writer_correction_prompt(
    *,
    gate: str,
    gate_report: Mapping[str, Any],
    module_text: str,
    writer: str = "claude-tools",
) -> str:
    """Render the ADR-008 patch-bounded writer correction prompt."""
    renderer = GATE_SPECIFIC_INSTRUCTION_RENDERERS.get(gate, _render_default_surgical_instruction)
    return render_phase_prompt(
        writer_correction_prompt_path(writer),
        {
            "MODULE_CONTENT": module_text,
            "CORRECTION_SECTION": yaml.safe_dump(
                {
                    "gate": gate,
                    "diagnostic": dict(gate_report),
                },
                allow_unicode=True,
                sort_keys=False,
            ).strip(),
            "GATE_SPECIFIC_INSTRUCTIONS": renderer(gate_report),
        },
    )


def render_reviewer_correction_prompt(
    *,
    gate: str,
    gate_report: Mapping[str, Any],
    module_text: str,
    candidates: tuple[CorrectionCandidate, ...] = (),
    artifact_texts: Mapping[str, str] | None = None,
) -> str:
    """Build a reviewer-as-fixer prompt for one failed Python QG gate."""
    candidate_rows = [
        {
            "original": candidate.original,
            "replacement": candidate.replacement,
            "source": candidate.source,
        }
        for candidate in candidates
    ]
    if candidate_rows:
        candidate_section = yaml.safe_dump(candidate_rows, allow_unicode=True, sort_keys=False).strip()
        reviewer_role = (
            "Pipeline-proposed candidates are provided below. SELECT from these candidates; do not invent replacements."
        )
    else:
        candidate_section = "[]"
        reviewer_role = "Emit local <fixes> entries only. Do not rewrite sections."
    diagnostic = yaml.safe_dump(
        {
            "gate": gate,
            "diagnostic": dict(gate_report),
        },
        allow_unicode=True,
        sort_keys=False,
    ).strip()
    artifact_sections = [
        "## Current module.md",
        "```markdown",
        module_text,
        "```",
    ]
    if artifact_texts:
        artifact_sections.extend(
            [
                "",
                "## Additional patchable artifacts",
                "The pipeline applies each literal fix to any listed artifact where the anchor occurs.",
            ]
        )
        for artifact_name, artifact_text in artifact_texts.items():
            artifact_sections.extend(
                [
                    "",
                    f"### {artifact_name}",
                    f"```yaml file={artifact_name}",
                    artifact_text,
                    "```",
                ]
            )
    return "\n".join(
        [
            "# Python QG correction",
            "",
            reviewer_role,
            "Return a single <fixes> block. Use these two shapes only:",
            "  - `<fix><find>...</find><replace>...</replace></fix>` for textual"
            " swaps. Each `<replace>` body MUST be ≤ 6 lines OR ≤ 240 chars.",
            "  - `<fix><insert_after>ANCHOR</insert_after><text>...</text></fix>` for"
            " ADDITIONS. Use this when the gate failure is 'missing/insufficient X'"
            " (l2_exposure_floor, inject_activity_ids, n_resources, etc.).",
            "Decision rule: if the gate says you need to ADD content, you MUST use"
            " `insert_after` + `text`. Using `find` + `replace` to add multiple new"
            " entries triggers `reviewer_fix_oversize_rejected` and the build fails.",
            "",
            "## Gate diagnostic",
            "```yaml",
            diagnostic,
            "```",
            "",
            "## Pipeline-proposed candidates",
            "```yaml",
            candidate_section,
            "```",
            "",
            *artifact_sections,
        ]
    )


def parse_review_response(
    response: str,
    dim: str,
    *,
    reviewer: str | None = None,
    module: str | None = None,
    writer_under_review: str | None = None,
    event_sink: Callable[..., None] | None = None,
) -> dict[str, Any]:
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
    evidence_quotes = payload.get("evidence_quotes")
    verdict = str(payload.get("verdict", "")).upper()
    entry: dict[str, Any] = {
        "score": score,
        "evidence": evidence,
        "verdict": verdict,
    }
    # Preserve `evidence_quotes` when the reviewer emitted the richer schema
    # (list of supporting excerpts). Build #11 a1/my-morning (2026-05-21)
    # gemini-pro pedagogical dim used this shape; validator + downstream
    # telemetry both honor it. Without this field, validate_llm_review_report
    # raises "missing quoted excerpt" even when 3 valid quotes are present.
    if isinstance(evidence_quotes, list) and evidence_quotes:
        entry["evidence_quotes"] = evidence_quotes
    rubric_mapping = _rubric_mapping_from_payload(payload)
    if rubric_mapping:
        entry["rubric_mapping"] = rubric_mapping
    raw_flags = payload.get("flags")
    if raw_flags is None:
        raw_flags = payload.get("flags_raised")
    if isinstance(raw_flags, str):
        raw_flags = [raw_flags]
    if isinstance(raw_flags, list) and raw_flags:
        entry["flags"] = [_clean_telemetry_text(flag, 120) for flag in raw_flags if str(flag).strip()]
    issue_ids = _llm_qg_issue_ids_from_payload(payload)
    if issue_ids:
        entry["issue_ids"] = issue_ids
    findings = _llm_qg_findings_from_payload(payload)
    if findings:
        entry["findings"] = findings
    validate_llm_review_report({**_placeholder_review_report(), dim: entry})
    if verdict not in {"PASS", "REVISE", "REJECT"}:
        raise LinearPipelineError(f"LLM QG response for {dim} has invalid verdict")
    if reviewer and module and writer_under_review:
        telemetry_payload = dict(payload)
        telemetry_payload.setdefault("score", score)
        telemetry_payload.setdefault("evidence", evidence)
        emit_reviewer_dim_telemetry(
            telemetry_payload,
            reviewer=reviewer,
            module=module,
            writer_under_review=writer_under_review,
            dim=dim,
            event_sink=event_sink,
        )
    return entry


def llm_qg_median_sample_index(scores: Sequence[float]) -> int:
    """Return the source-sample index for the median score.

    Even-sized ensembles choose the lower-middle score so the selected report
    remains one real reviewer sample rather than synthesized evidence.
    """
    if not scores:
        raise LinearPipelineError("LLM QG reviewer ensemble requires at least one score")
    return sorted(range(len(scores)), key=lambda index: (float(scores[index]), index))[
        (len(scores) - 1) // 2
    ]


def select_median_llm_review_sample(
    dim_results: Sequence[Mapping[str, Any]],
    *,
    dim: str,
    reviewer: str | None = None,
    module: str | None = None,
    writer_under_review: str | None = None,
    event_sink: Callable[..., None] | None = None,
) -> dict[str, Any]:
    """Select the full per-dim result whose score is the ensemble median."""
    if not dim_results:
        raise LinearPipelineError(f"LLM QG reviewer ensemble for {dim} has no samples")
    scores = [float(result["score"]) for result in dim_results]
    chosen_index = llm_qg_median_sample_index(scores)
    _emit(
        event_sink,
        "reviewer_ensemble",
        dim=dim,
        n=len(dim_results),
        scores=scores,
        median_score=scores[chosen_index],
        chosen_sample_index=chosen_index,
        reviewer=reviewer,
        module=module,
        writer_under_review=writer_under_review,
    )
    return dict(dim_results[chosen_index])


def invoke_reviewer_dim_ensemble(
    prompt: str,
    reviewer: str,
    *,
    dim: str,
    writer_under_review: str,
    reviewer_samples: int,
    cwd: Path = PROJECT_ROOT,
    invoker: Callable[..., Any] | None = None,
    module: str | None = None,
    event_sink: Callable[..., None] | None = None,
    stdout_silence_timeout: int | None = None,
) -> dict[str, Any]:
    """Invoke a per-dim reviewer once or as a median-of-N ensemble."""
    sample_count = max(1, int(reviewer_samples))
    if sample_count == 1:
        response = invoke_reviewer_dim(
            prompt,
            reviewer,
            dim=dim,
            writer_under_review=writer_under_review,
            cwd=cwd,
            invoker=invoker,
            module=module,
            event_sink=event_sink,
            stdout_silence_timeout=stdout_silence_timeout,
        )
        return parse_review_response(response, dim)

    dim_results: list[dict[str, Any]] = []
    for _sample_index in range(sample_count):
        response = invoke_reviewer_dim(
            prompt,
            reviewer,
            dim=dim,
            writer_under_review=writer_under_review,
            cwd=cwd,
            invoker=invoker,
            module=module,
            event_sink=event_sink,
            stdout_silence_timeout=stdout_silence_timeout,
        )
        dim_results.append(parse_review_response(response, dim))
    return select_median_llm_review_sample(
        dim_results,
        dim=dim,
        reviewer=reviewer,
        module=module,
        writer_under_review=writer_under_review,
        event_sink=event_sink,
    )


def parse_wiki_coverage_review_response(response: str) -> dict[str, Any]:
    payload = _parse_json_or_yaml_mapping(response)
    verdicts = payload.get("verdicts")
    if not isinstance(verdicts, list):
        raise LinearPipelineError("Wiki coverage review response missing verdicts list")
    normalized_verdicts: list[dict[str, Any]] = []
    hard_fail_seen = False
    for item in verdicts:
        if not isinstance(item, Mapping):
            raise LinearPipelineError("Wiki coverage review verdict entries must be mappings")
        verdict = str(item.get("verdict") or "").upper()
        if verdict not in ALLOWED_WIKI_COVERAGE_VERDICTS:
            raise LinearPipelineError("Wiki coverage review verdict must be PASS, KEYWORD_STUFFING, PARTIAL, or FAIL")
        if not str(item.get("obligation_id") or "").strip():
            raise LinearPipelineError("Wiki coverage review verdict missing obligation_id")
        evidence = str(item.get("evidence") or "").strip()
        if not evidence:
            raise LinearPipelineError("Wiki coverage review verdict missing evidence")
        if len(evidence) < 8 or not any(marker in evidence for marker in WIKI_COVERAGE_EVIDENCE_QUOTE_MARKERS):
            raise LinearPipelineError("Wiki coverage review evidence must be a quoted excerpt of ≥8 chars")
        if verdict in WIKI_COVERAGE_OVERALL_FAIL_VERDICTS:
            hard_fail_seen = True
        normalized_item = dict(item)
        normalized_item["verdict"] = verdict
        normalized_item["evidence"] = evidence
        normalized_verdicts.append(normalized_item)
    overall = str(payload.get("overall_verdict") or "").upper()
    if overall not in WIKI_COVERAGE_OVERALL_VERDICTS:
        raise LinearPipelineError("Wiki coverage review overall_verdict must be PASS, PARTIAL, or FAIL")
    if hard_fail_seen and overall != "FAIL":
        raise LinearPipelineError("Wiki coverage review overall_verdict must be FAIL when any obligation verdict fails")
    return {**payload, "verdicts": normalized_verdicts, "overall_verdict": overall}


_LLM_QG_QUOTE_MARKERS = ('"', "“", "”", "«", "»")
_LLM_QG_ISSUE_ID_RE = re.compile(r"[^A-Z0-9_]")


def _normalize_llm_qg_issue_id(raw: Any) -> str | None:
    if not isinstance(raw, str):
        return None
    normalized = _LLM_QG_ISSUE_ID_RE.sub("_", raw.strip().upper())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or None


def _llm_qg_issue_ids_from_payload(payload: Mapping[str, Any]) -> list[str]:
    ids: set[str] = set()

    def add(value: Any) -> None:
        if isinstance(value, str):
            normalized = _normalize_llm_qg_issue_id(value)
            if normalized:
                ids.add(normalized)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                add(item)

    add(payload.get("issue_ids"))
    findings = payload.get("findings")
    if isinstance(findings, Sequence) and not isinstance(findings, (str, bytes, bytearray)):
        for finding in findings:
            if isinstance(finding, Mapping):
                for key in ("issue_id", "issue_type", "type", "kind", "tag", "error_class", "issue"):
                    add(finding.get(key))
            else:
                add(finding)
    return sorted(ids)


def _llm_qg_findings_from_payload(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_findings = payload.get("findings")
    if not isinstance(raw_findings, Sequence) or isinstance(raw_findings, (str, bytes, bytearray)):
        return []

    findings: list[dict[str, Any]] = []
    for raw in raw_findings[:50]:
        if isinstance(raw, str):
            issue_id = _normalize_llm_qg_issue_id(raw)
            if issue_id:
                findings.append({"issue_id": issue_id})
            continue
        if not isinstance(raw, Mapping):
            continue
        item: dict[str, Any] = {}
        issue_id = None
        for key in ("issue_id", "issue_type", "type", "kind", "tag", "error_class", "issue"):
            issue_id = _normalize_llm_qg_issue_id(raw.get(key))
            if issue_id:
                break
        if issue_id:
            item["issue_id"] = issue_id
        for key in ("severity", "quote", "replacement", "explanation", "dimension"):
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                item[key] = _clean_telemetry_text(value, 500)
        if item:
            findings.append(item)
    return findings


def _evidence_passes_quote_contract(entry: Mapping[str, Any]) -> bool:
    """Return True iff the dim entry carries falsifiable quoted evidence.

    Two accepted shapes (both seen in production reviewer responses):

    1. Bare ``evidence`` scalar containing a quote marker (``"``, ``«``,
       ``""``, curly quotes). This is what the prompt currently asks for.
    2. ``evidence_quotes`` list of one or more strings ≥8 chars each. Build
       #11 (2026-05-21) showed gemini-pro emitting this richer schema for
       the ``pedagogical`` dim — multiple supporting quotes are more
       falsifiable than a single one, so we accept the array form even when
       the bare ``evidence`` scalar lacks literal quote markers.

    Either shape satisfies the falsifiability contract: a reviewer cannot
    claim PASS without citing concrete text from the artifact.
    """
    evidence = entry.get("evidence")
    if isinstance(evidence, str) and evidence.strip() and any(q in evidence for q in _LLM_QG_QUOTE_MARKERS):
        return True

    quotes = entry.get("evidence_quotes")
    if isinstance(quotes, list) and quotes:
        valid = [q for q in quotes if isinstance(q, str) and len(q.strip()) >= 8]
        if valid:
            return True
    return False


def validate_llm_review_report(report: Mapping[str, Any]) -> None:
    """Validate per-dim LLM QG reports before aggregation."""
    dims = set(QG_DIMS)
    actual = set(report)
    if actual != dims:
        missing = sorted(dims - actual)
        extra = sorted(actual - dims)
        raise LinearPipelineError(f"LLM QG dims must be exactly QG_DIMS. missing={missing} extra={extra}")

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
        evidence_quotes = entry.get("evidence_quotes")
        if (not isinstance(evidence, str) or not evidence.strip()) and not (
            isinstance(evidence_quotes, list) and evidence_quotes
        ):
            raise LinearPipelineError(f"LLM QG entry for {dim} missing evidence")
        if not _evidence_passes_quote_contract(entry):
            raise LinearPipelineError(f"LLM QG evidence for {dim} must include a quoted excerpt")
        if not isinstance(entry.get("verdict"), str) or not entry["verdict"].strip():
            raise LinearPipelineError(f"LLM QG entry for {dim} missing verdict")
        if entry["verdict"].upper() not in {"PASS", "REVISE", "REJECT"}:
            raise LinearPipelineError(f"LLM QG entry for {dim} has invalid verdict")


def _review_weighted_score(scores: Mapping[str, float]) -> float:
    if not scores:
        return 0.0
    return round(sum(float(score) for score in scores.values()) / len(scores), 2)


def emit_phase_review_summary(
    report: Mapping[str, Any],
    *,
    reviewer: str,
    module: str,
    writer_under_review: str,
    audit_calls_total: int = 0,
    flags_raised_total: int = 0,
    weighted_score: float | None = None,
    event_sink: Callable[..., None] | None = None,
) -> dict[str, Any]:
    """Emit the reviewer phase roll-up event."""
    scores = {dim: float(report[dim]["score"]) for dim in QG_DIMS if isinstance(report.get(dim), Mapping)}
    dims_with_evidence = 0
    for dim in QG_DIMS:
        entry = report.get(dim)
        if isinstance(entry, Mapping):
            evidence = entry.get("evidence") or entry.get("evidence_quotes")
            if evidence:
                dims_with_evidence += 1
    summary = {
        "dims_scored": len(scores),
        "dims_with_evidence": dims_with_evidence,
        "audit_calls_total": int(audit_calls_total),
        "flags_raised_total": int(flags_raised_total),
        "min_dim_score": min(scores.values()) if scores else None,
        "weighted_score": weighted_score if weighted_score is not None else _review_weighted_score(scores),
    }
    _emit(
        event_sink,
        "phase_review_summary",
        reviewer=reviewer,
        module=module,
        writer_under_review=writer_under_review,
        **summary,
    )
    return summary


def aggregate_llm_review(
    report: Mapping[str, Any],
    level_code: str,
    *,
    profile: str | None = None,
    reviewer: str | None = None,
    module: str | None = None,
    writer_under_review: str | None = None,
    audit_calls_total: int = 0,
    flags_raised_total: int = 0,
    event_sink: Callable[..., None] | None = None,
) -> dict[str, Any]:
    validate_llm_review_report(report)
    scores = {dim: float(report[dim]["score"]) for dim in QG_DIMS}
    verdict = aggregate_review(scores, level_code, profile=profile)
    weighted_score = _review_weighted_score(scores)
    if reviewer and module and writer_under_review:
        emit_phase_review_summary(
            report,
            reviewer=reviewer,
            module=module,
            writer_under_review=writer_under_review,
            audit_calls_total=audit_calls_total,
            flags_raised_total=flags_raised_total,
            weighted_score=weighted_score,
            event_sink=event_sink,
        )
    return {
        "dimensions": {dim: dict(report[dim]) for dim in QG_DIMS},
        "aggregate": asdict(verdict),
    }


def _llm_qg_dimensions(llm_qg: Mapping[str, Any]) -> Mapping[str, Any]:
    dimensions = llm_qg.get("dimensions")
    return dimensions if isinstance(dimensions, Mapping) else {}


def _llm_qg_aggregate(llm_qg: Mapping[str, Any]) -> Mapping[str, Any]:
    aggregate = llm_qg.get("aggregate")
    return aggregate if isinstance(aggregate, Mapping) else {}


def _llm_qg_needs_pedagogical_fix(llm_qg: Mapping[str, Any]) -> bool:
    failing = _llm_qg_aggregate(llm_qg).get("failing_dims") or ()
    return "pedagogical" in {str(dim) for dim in failing}


def _llm_qg_fixable_grammar_findings(llm_qg: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return quoted LLM-QG grammar/calque findings that can be locally patched."""
    findings: list[dict[str, Any]] = []
    for dim, entry in _llm_qg_dimensions(llm_qg).items():
        if not isinstance(entry, Mapping):
            continue
        dim_issue_ids = {
            issue_id
            for issue_id in _llm_qg_issue_ids_from_payload(entry)
            if issue_id in LLM_QG_GRAMMAR_CALQUE_ISSUE_IDS
        }
        for finding in _llm_qg_findings_from_payload(entry):
            issue_id = finding.get("issue_id")
            if issue_id not in LLM_QG_GRAMMAR_CALQUE_ISSUE_IDS:
                if issue_id is not None:
                    continue
                if not dim_issue_ids:
                    continue
                issue_id = sorted(dim_issue_ids)[0]
            quote = str(finding.get("quote") or "").strip()
            if not quote:
                continue
            normalized = dict(finding)
            normalized["issue_id"] = issue_id
            normalized["quote"] = quote
            normalized.setdefault("dimension", str(dim))
            findings.append(normalized)
    return findings


def _llm_qg_grammar_gate_report(
    llm_qg: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    aggregate = _llm_qg_aggregate(llm_qg)
    return {
        "source": "llm_qg",
        "gate": LLM_QG_GRAMMAR_CALQUE_GATE,
        "aggregate": dict(aggregate),
        "failing_dims": list(aggregate.get("failing_dims") or ()),
        "findings": [dict(finding) for finding in findings],
    }


def _llm_qg_grammar_candidates(
    findings: Sequence[Mapping[str, Any]],
) -> tuple[CorrectionCandidate, ...]:
    candidates: list[CorrectionCandidate] = []
    seen: set[tuple[str, str]] = set()
    for finding in findings:
        quote = str(finding.get("quote") or "").strip()
        replacement = str(finding.get("replacement") or "").strip()
        if not quote or not replacement:
            continue
        key = (quote, replacement)
        if key in seen:
            continue
        seen.add(key)
        issue_id = str(finding.get("issue_id") or LLM_QG_GRAMMAR_CALQUE_GATE)
        dimension = str(finding.get("dimension") or "llm_qg")
        candidates.append(
            CorrectionCandidate(
                original=quote,
                replacement=replacement,
                source=f"LLM-QG {dimension}/{issue_id}",
                gate=LLM_QG_GRAMMAR_CALQUE_GATE,
            )
        )
    return tuple(candidates)


def _apply_llm_qg_grammar_correction(
    *,
    llm_qg: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
    module_dir: Path,
    plan_path: Path,
    reviewer_corrector: Callable[[CorrectionContext], str | None] | None,
    invoker: Callable[..., Any] | None,
) -> dict[str, Any]:
    gate_report = _llm_qg_grammar_gate_report(llm_qg, findings)
    candidates = _llm_qg_grammar_candidates(findings)
    _, payload = _apply_reviewer_correction(
        LLM_QG_GRAMMAR_CALQUE_GATE,
        gate_report,
        qg_report=llm_qg,
        module_dir=module_dir,
        plan_path=plan_path,
        candidates=candidates,
        reviewer_corrector=reviewer_corrector,
        invoker=invoker,
    )
    changed = any(
        isinstance(record, Mapping) and record.get("changed") is True
        for record in payload.get("artifacts", [])
    )
    payload["applied"] = bool(payload.get("applied")) and changed
    payload["findings"] = [dict(finding) for finding in findings]
    return payload


def _apply_llm_qg_pedagogical_correction(
    *,
    llm_qg: Mapping[str, Any],
    plan: Mapping[str, Any],
    plan_path: Path,
    plan_content: str,
    module_dir: Path,
    wiki_manifest: str | Mapping[str, Any] | None,
    obligation_checklist: Mapping[str, Any] | None,
    round_num: int,
    corrector: Callable[[CorrectionContext], str | None] | None,
    invoker: Callable[..., Any] | None,
    stdout_silence_timeout: int | None,
) -> dict[str, Any]:
    module_text = _read_required(module_dir / "module.md")
    prompt = render_pedagogical_correction_prompt(
        plan=plan,
        llm_qg=llm_qg,
        module_text=module_text,
        plan_content=plan_content,
        wiki_manifest=wiki_manifest,
        obligation_checklist=obligation_checklist,
    )
    (module_dir / f"llm-qg-pedagogical-correction-r{round_num}-prompt.md").write_text(
        prompt,
        encoding="utf-8",
    )
    context = CorrectionContext(
        gate="llm_qg_pedagogical",
        gate_report=_llm_qg_dimensions(llm_qg).get("pedagogical", {}),
        module_dir=module_dir,
        plan_path=plan_path,
        qg_report=llm_qg,
        prompt=prompt,
    )
    response = (
        corrector(context)
        if corrector is not None
        else _invoke_pedagogical_corrector(
            prompt=prompt,
            module_dir=module_dir,
            plan=plan,
            round_num=round_num,
            invoker=invoker,
            stdout_silence_timeout=stdout_silence_timeout,
        )
    ) or ""
    (module_dir / f"llm-qg-pedagogical-correction-r{round_num}-response.raw.md").write_text(
        response,
        encoding="utf-8",
    )
    return _apply_pedagogical_insert_fixes(
        response=response,
        module_dir=module_dir,
        plan_path=plan_path,
    )


def _llm_qg_round_summary(round_record: Mapping[str, Any]) -> dict[str, Any]:
    llm_qg = round_record.get("llm_qg")
    aggregate = _llm_qg_aggregate(llm_qg) if isinstance(llm_qg, Mapping) else {}
    min_score, min_dim = (
        review_loop_aggregate_min(_llm_qg_dimensions(llm_qg))
        if isinstance(llm_qg, Mapping)
        else (0.0, None)
    )
    return {
        "round": round_record.get("round"),
        "verdict": aggregate.get("verdict"),
        "terminal_verdict": aggregate.get("terminal_verdict"),
        "min_score": min_score,
        "min_dim": min_dim,
        "failing_dims": list(aggregate.get("failing_dims") or ()),
    }


def _invoke_pedagogical_corrector(
    *,
    prompt: str,
    module_dir: Path,
    plan: Mapping[str, Any],
    round_num: int,
    invoker: Callable[..., Any] | None = None,
    stdout_silence_timeout: int | None = None,
) -> str:
    if invoker is None:
        from scripts.agent_runtime.runner import invoke as runtime_invoke
    else:
        runtime_invoke = invoker

    result = runtime_invoke(
        "codex",
        prompt,
        mode="read-only",
        cwd=module_dir,
        model=REVIEWER_DEFAULTS["codex-tools"]["model"],
        task_id=f"linear-llm-qg-pedagogical-fix-{plan.get('slug', 'module')}-r{round_num}",
        entrypoint="runtime",
        effort=REVIEWER_DEFAULTS["codex-tools"]["effort"],
        tool_config=_runtime_tool_config("codex-tools", workspace_dir=module_dir),
        stdout_silence_timeout=stdout_silence_timeout,
    )
    return str(getattr(result, "response", "") or "")


def _apply_pedagogical_insert_fixes(
    *,
    response: str,
    module_dir: Path,
    plan_path: Path,
) -> dict[str, Any]:
    fixes = _parse_reviewer_fixes(response)
    insert_fixes = [
        fix for fix in fixes
        if "insert_after" in fix and "text" in fix
    ]
    rejected_shape_fixes = [
        fix for fix in fixes
        if not ("insert_after" in fix and "text" in fix)
    ]
    accepted_fixes, rejected_oversize = _validate_reviewer_fix_shapes(
        insert_fixes,
        max_lines=8,
        max_chars=800,
    )
    module_path = module_dir / "module.md"
    original_text = _read_required(module_path)
    apply_result = _apply_reviewer_fixes(
        original_text,
        accepted_fixes,
        gate="llm_qg_pedagogical",
        module_dir=module_dir,
        plan_path=plan_path,
    )
    changed = apply_result.text != original_text
    if changed:
        module_path.write_text(apply_result.text, encoding="utf-8")
    return {
        "kind": "llm_qg_pedagogical",
        "response": response,
        "fixes": fixes,
        "accepted_fixes": accepted_fixes,
        "rejected_fixes": [*rejected_shape_fixes, *rejected_oversize],
        "unmatched_anchors": sorted(apply_result.unmatched_anchors),
        "applied": changed,
    }


def _python_qg_passed(report: Mapping[str, Any]) -> bool:
    gates = report.get("gates")
    return isinstance(gates, Mapping) and gates.get("passed") is True


def _run_python_qg_for_llm_regression_guard(
    *,
    module_dir: Path,
    plan_path: Path,
    python_qg_runner: Callable[[], dict[str, Any]] | None,
    event_sink: Callable[..., None] | None,
) -> dict[str, Any]:
    if python_qg_runner is not None:
        report = python_qg_runner()
    else:
        report = run_python_qg(module_dir, plan_path, event_sink=event_sink)
    _attach_vocab_count_gate(report, module_dir=module_dir, plan_path=plan_path)
    return report


def _python_qg_violation_value_count(value: Any) -> int:
    if isinstance(value, Mapping):
        return len(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return len(value)
    return 1 if value else 0


def _python_qg_explicit_violation_count(gate_report: Mapping[str, Any]) -> int:
    return sum(
        _python_qg_violation_value_count(gate_report.get(key))
        for key in PYTHON_QG_VIOLATION_COUNT_KEYS
    )


def _python_qg_gate_violation_count(gate_report: Mapping[str, Any]) -> int:
    explicit_count = _python_qg_explicit_violation_count(gate_report)
    if "passed" not in gate_report:
        return max(1, explicit_count)
    if gate_report.get("passed") is not False:
        return 0
    return max(1, explicit_count)


def _python_qg_violation_count(report: Mapping[str, Any]) -> int:
    gates = report.get("gates")
    if not isinstance(gates, Mapping):
        return PYTHON_QG_MALFORMED_REPORT_VIOLATIONS
    return sum(
        _python_qg_gate_violation_count(gate_report)
        for gate, gate_report in gates.items()
        if gate != "passed" and isinstance(gate_report, Mapping)
    )


def _python_qg_frontier(report: Mapping[str, Any]) -> int:
    gates = report.get("gates")
    if not isinstance(gates, Mapping):
        return -1
    for index, gate in enumerate(PYTHON_QG_GATE_ORDER):
        gate_report = gates.get(gate)
        if isinstance(gate_report, Mapping) and gate_report.get("passed") is False:
            return index
    if not _python_qg_passed(report):
        # A failed report with no ordered failing gate has no trustworthy
        # frontier. Rank it before the first mapped gate so it can never tie
        # with, or beat, a truly passing report.
        return PYTHON_QG_UNMAPPED_FAILURE_FRONTIER
    return len(PYTHON_QG_GATE_ORDER)


def _python_qg_frontier_gate(report: Mapping[str, Any]) -> str | None:
    gates = report.get("gates")
    if not isinstance(gates, Mapping):
        return None
    for gate in PYTHON_QG_GATE_ORDER:
        gate_report = gates.get(gate)
        if isinstance(gate_report, Mapping) and gate_report.get("passed") is False:
            return gate
    for gate in sorted(set(gates) - set(PYTHON_QG_GATE_ORDER) - PYTHON_QG_META_GATES):
        gate_report = gates.get(gate)
        if isinstance(gate_report, Mapping) and gate_report.get("passed") is False:
            return gate
    return None


def _python_qg_round_frontier(round_record: Mapping[str, Any]) -> int:
    raw_frontier = round_record.get("frontier")
    if isinstance(raw_frontier, int):
        return raw_frontier
    report = round_record.get("report")
    if isinstance(report, Mapping):
        return _python_qg_frontier(report)
    return -1


def _python_qg_best_round_index(rounds: Sequence[Mapping[str, Any]]) -> int:
    if not rounds:
        raise ValueError("_python_qg_best_round_index requires at least one round")
    return max(
        range(len(rounds)),
        key=lambda i: (
            _python_qg_round_frontier(rounds[i]),
            -int(rounds[i].get("violation_count") or 0),
            -i,
        ),
    )


def _python_qg_frontier_regressed(
    reference: Mapping[str, Any],
    current: Mapping[str, Any],
) -> bool:
    return _python_qg_frontier(current) < _python_qg_frontier(reference)


def _python_qg_review_loop_dims(violation_count: int) -> Mapping[str, Any]:
    return {
        "python_qg_violations": {
            "score": -float(violation_count),
            "verdict": "PASS" if violation_count == 0 else "REVISE",
        }
    }


def _python_qg_round_summary(round_record: Mapping[str, Any]) -> dict[str, Any]:
    report = round_record.get("report")
    violation_count = int(round_record.get("violation_count") or 0)
    frontier = _python_qg_round_frontier(round_record)
    return {
        "round": round_record.get("round"),
        "correction_round": round_record.get("correction_round"),
        "passed": _python_qg_passed(report) if isinstance(report, Mapping) else False,
        "violation_count": violation_count,
        "score": -violation_count,
        "frontier": frontier,
        "frontier_gate": _python_qg_frontier_gate(report) if isinstance(report, Mapping) else None,
        "failed_gate": round_record.get("failed_gate"),
    }


def run_llm_qg_with_corrections(
    *,
    plan: Mapping[str, Any],
    plan_path: Path,
    plan_content: str,
    module_dir: Path,
    writer: str,
    llm_qg_runner: Callable[..., dict[str, Any]],
    profile: str | None = None,
    reviewer_override: str | None = None,
    wiki_manifest: str | Mapping[str, Any] | None = None,
    implementation_map: Mapping[str, Any] | None = None,
    stdout_silence_timeout: int | None = None,
    use_generator: bool = False,
    obligation_checklist: Mapping[str, Any] | None = None,
    max_rounds: int | None = None,
    corrector: Callable[[CorrectionContext], str | None] | None = None,
    python_qg_runner: Callable[[], dict[str, Any]] | None = None,
    invoker: Callable[..., Any] | None = None,
    event_sink: Callable[..., None] | None = None,
    reviewer_samples: int | None = None,
) -> dict[str, Any]:
    """Run LLM-QG with a bounded correction loop for actionable review findings."""
    review_rounds = max(1, int(max_rounds or llm_qg_max_rounds_for_level(plan.get("level"))))
    llm_qg_reviewer_samples = max(
        1,
        int(reviewer_samples or llm_qg_reviewer_samples_for_level(plan.get("level"))),
    )
    rounds: list[dict[str, Any]] = []
    corrections: list[dict[str, Any]] = []
    pending_python_qg: dict[str, Any] | None = None
    stopped_reason = "max_rounds"

    for round_num in range(1, review_rounds + 1):
        review_snapshot = _snapshot_correction_artifacts(module_dir)
        llm_qg = llm_qg_runner(
            plan=plan,
            plan_content=plan_content,
            module_dir=module_dir,
            writer=writer,
            reviewer_override=reviewer_override,
            profile=profile,
            wiki_manifest=wiki_manifest,
            implementation_map=implementation_map,
            stdout_silence_timeout=stdout_silence_timeout,
            use_generator=use_generator,
            obligation_checklist=obligation_checklist,
            event_sink=event_sink,
            reviewer_samples=llm_qg_reviewer_samples,
        )
        round_record = {
            "round": round_num,
            "llm_qg": llm_qg,
            "artifacts": review_snapshot,
            "python_qg": pending_python_qg,
        }
        rounds.append(round_record)
        round_summary = _llm_qg_round_summary(round_record)
        _emit(
            event_sink,
            "llm_qg_correction_round",
            max_rounds=review_rounds,
            **round_summary,
        )

        aggregate = _llm_qg_aggregate(llm_qg)
        grammar_findings = _llm_qg_fixable_grammar_findings(llm_qg)
        if aggregate.get("verdict") == "PASS" and not grammar_findings:
            stopped_reason = "pass"
            break
        if round_num > 1 and min_score_regressed(
            _llm_qg_dimensions(rounds[-2]["llm_qg"]),
            _llm_qg_dimensions(llm_qg),
            tolerance=LLM_QG_REGRESSION_NOISE_TOLERANCE,
        ):
            stopped_reason = "min_score_regressed"
            break
        if round_num >= review_rounds:
            stopped_reason = "max_rounds"
            break
        if grammar_findings:
            python_qg_before = _run_python_qg_for_llm_regression_guard(
                module_dir=module_dir,
                plan_path=plan_path,
                python_qg_runner=python_qg_runner,
                event_sink=event_sink,
            )
            correction = _apply_llm_qg_grammar_correction(
                llm_qg=llm_qg,
                findings=grammar_findings,
                module_dir=module_dir,
                plan_path=plan_path,
                reviewer_corrector=corrector,
                invoker=invoker,
            )
        elif _llm_qg_needs_pedagogical_fix(llm_qg):
            python_qg_before = _run_python_qg_for_llm_regression_guard(
                module_dir=module_dir,
                plan_path=plan_path,
                python_qg_runner=python_qg_runner,
                event_sink=event_sink,
            )
            correction = _apply_llm_qg_pedagogical_correction(
                llm_qg=llm_qg,
                plan=plan,
                plan_path=plan_path,
                plan_content=plan_content,
                module_dir=module_dir,
                wiki_manifest=wiki_manifest,
                obligation_checklist=obligation_checklist,
                round_num=round_num,
                corrector=corrector,
                invoker=invoker,
                stdout_silence_timeout=stdout_silence_timeout,
            )
        else:
            stopped_reason = "no_fixable_llm_qg_failure"
            break
        correction["round"] = round_num
        corrections.append(correction)
        if not correction.get("applied"):
            stopped_reason = "no_fixes_applied"
            break

        python_qg = _run_python_qg_for_llm_regression_guard(
            module_dir=module_dir,
            plan_path=plan_path,
            python_qg_runner=python_qg_runner,
            event_sink=event_sink,
        )
        regressions = _previously_passing_regressions(python_qg_before, python_qg)
        frontier_regressed = _python_qg_frontier_regressed(python_qg_before, python_qg)
        correction["python_qg_before"] = python_qg_before
        correction["python_qg"] = python_qg
        correction["python_qg_regressions"] = regressions
        correction["python_qg_frontier_regressed"] = frontier_regressed
        if regressions or frontier_regressed:
            _restore_correction_artifacts(module_dir, review_snapshot)
            correction["rolled_back"] = True
            correction["rollback_reason"] = "python_qg_regressed"
            stopped_reason = "python_qg_regressed"
            break
        pending_python_qg = python_qg

    best_idx = best_round_index(rounds, lambda item: _llm_qg_dimensions(item["llm_qg"]))
    best_round = rounds[best_idx]
    _restore_correction_artifacts(module_dir, best_round["artifacts"])
    if best_round.get("python_qg") is not None:
        write_json(module_dir / "python_qg.json", best_round["python_qg"])
    best_report = dict(best_round["llm_qg"])
    correction_loop = {
        "max_rounds": review_rounds,
        "rounds": [_llm_qg_round_summary(item) for item in rounds],
        "best_round": best_round["round"],
        "stopped_reason": stopped_reason,
        "corrections": corrections,
    }
    write_json(module_dir / "llm_qg_correction_loop.json", correction_loop)
    return best_report


def run_python_qg_with_corrections(
    module_dir: Path,
    plan_path: Path,
    *,
    verify_words_fn: Callable[[list[str]], dict[str, list[dict[str, Any]]]] | None = None,
    heritage_lookup_fn: Callable[[str], list[dict[str, Any]]] | None = None,
    qg_runner: Callable[[], dict[str, Any]] | None = None,
    writer_corrector: Callable[[CorrectionContext], str | Mapping[str, str] | None] | None = None,
    reviewer_corrector: Callable[[CorrectionContext], str | None] | None = None,
    dictionary_lookup_fn: Callable[[str, str], list[str | Mapping[str, str]]] | None = None,
    writer: str = "claude-tools",
    invoker: Callable[..., Any] | None = None,
    event_sink: Callable[..., None] | None = None,
) -> dict[str, Any]:
    """Run Python QG with core legacy behavior and seminar best-round selection."""
    level = _python_qg_level_from_plan_path(plan_path)
    if level in SEMINAR_LEVELS:
        return _run_python_qg_with_bounded_corrections(
            module_dir,
            plan_path,
            verify_words_fn=verify_words_fn,
            heritage_lookup_fn=heritage_lookup_fn,
            qg_runner=qg_runner,
            writer_corrector=writer_corrector,
            reviewer_corrector=reviewer_corrector,
            dictionary_lookup_fn=dictionary_lookup_fn,
            writer=writer,
            invoker=invoker,
            event_sink=event_sink,
            max_correction_rounds=python_qg_max_correction_rounds_for_level(level),
        )
    return _run_python_qg_with_legacy_single_shot_corrections(
        module_dir,
        plan_path,
        verify_words_fn=verify_words_fn,
        heritage_lookup_fn=heritage_lookup_fn,
        qg_runner=qg_runner,
        writer_corrector=writer_corrector,
        reviewer_corrector=reviewer_corrector,
        dictionary_lookup_fn=dictionary_lookup_fn,
        writer=writer,
        invoker=invoker,
        event_sink=event_sink,
    )


def _run_python_qg_with_bounded_corrections(
    module_dir: Path,
    plan_path: Path,
    *,
    verify_words_fn: Callable[[list[str]], dict[str, list[dict[str, Any]]]] | None = None,
    heritage_lookup_fn: Callable[[str], list[dict[str, Any]]] | None = None,
    qg_runner: Callable[[], dict[str, Any]] | None = None,
    writer_corrector: Callable[[CorrectionContext], str | Mapping[str, str] | None] | None = None,
    reviewer_corrector: Callable[[CorrectionContext], str | None] | None = None,
    dictionary_lookup_fn: Callable[[str, str], list[str | Mapping[str, str]]] | None = None,
    writer: str = "claude-tools",
    invoker: Callable[..., Any] | None = None,
    event_sink: Callable[..., None] | None = None,
    max_correction_rounds: int = PYTHON_QG_SEMINAR_MAX_CORRECTION_ROUNDS,
) -> dict[str, Any]:
    """Run seminar Python QG with bounded corrections and restore the best round."""
    correction_budget = max(1, int(max_correction_rounds))
    rounds: list[dict[str, Any]] = []
    corrections: list[dict[str, Any]] = []
    stopped_reason = "max_rounds"
    consecutive_regressions = 0

    def _run_qg() -> dict[str, Any]:
        if qg_runner is not None:
            report = qg_runner()
        else:
            report = run_python_qg(
                module_dir,
                plan_path,
                verify_words_fn=verify_words_fn,
                heritage_lookup_fn=heritage_lookup_fn,
                event_sink=event_sink,
            )
        _attach_vocab_count_gate(report, module_dir=module_dir, plan_path=plan_path)
        return report

    def _record_round(
        report: dict[str, Any],
        *,
        correction_round: int,
        failed_gate: str | None = None,
    ) -> dict[str, Any]:
        round_record = {
            "round": len(rounds) + 1,
            "correction_round": correction_round,
            "report": report,
            "artifacts": _snapshot_correction_artifacts(module_dir),
            "violation_count": _python_qg_violation_count(report),
            "frontier": _python_qg_frontier(report),
            "failed_gate": failed_gate,
        }
        rounds.append(round_record)
        _emit(
            event_sink,
            "python_qg_correction_round",
            max_correction_rounds=correction_budget,
            **_python_qg_round_summary(round_record),
        )
        return round_record

    report = _run_qg()
    _record_round(report, correction_round=0)
    correction_round = 0

    while True:
        if _python_qg_passed(report):
            stopped_reason = "pass"
            break
        if correction_round >= correction_budget:
            stopped_reason = "max_rounds"
            break

        failed_gate = _first_failed_correctable_gate(report)
        if failed_gate is None:
            stopped_reason = "no_correctable_failure"
            break

        correction_round += 1
        before = report
        artifact_snapshot = rounds[-1]["artifacts"]
        handled, unmatched_anchors, correction_payload = _apply_python_qg_correction(
            failed_gate,
            report,
            module_dir=module_dir,
            plan_path=plan_path,
            writer_corrector=writer_corrector,
            reviewer_corrector=reviewer_corrector,
            dictionary_lookup_fn=dictionary_lookup_fn,
            writer=writer,
            invoker=invoker,
        )
        if not handled:
            _write_correction_artifact(
                module_dir / f"python_qg_correction_r{correction_round}.json",
                {
                    "round": correction_round,
                    "gate": failed_gate,
                    "handled": False,
                    "before": before,
                    "correction": correction_payload,
                },
            )
            _annotate_correction_terminal(
                report,
                failed_gate,
                f"{failed_gate} has no ADR-008 correction path",
            )
            stopped_reason = "no_correction_path"
            break

        report = _run_qg()
        regressions = _previously_passing_regressions(before, report)
        correction_artifact: dict[str, Any] = {
            "round": correction_round,
            "gate": failed_gate,
            "handled": True,
            "unmatched_anchors": sorted(unmatched_anchors),
            "before": before,
            "correction": correction_payload,
            "after": report,
            "regressions": regressions,
        }

        if correction_payload.get("yaml_invalid"):
            _restore_correction_artifacts(module_dir, artifact_snapshot)
            report = _run_qg()
            _annotate_correction_terminal(
                report,
                failed_gate,
                f"{failed_gate} correction produced invalid YAML and was rolled back",
            )
            correction_artifact["rolled_back"] = True
            correction_artifact["rollback_reason"] = "yaml_invalid"
            correction_artifact["restored_after"] = report
            _write_correction_artifact(
                module_dir / f"python_qg_correction_r{correction_round}.json",
                correction_artifact,
            )
            corrections.append(correction_artifact)
            _record_round(report, correction_round=correction_round, failed_gate=failed_gate)
            stopped_reason = "yaml_invalid"
            break

        if (
            failed_gate == "vesum_verified"
            and not _vesum_correction_improved(before, report)
        ):
            _restore_correction_artifacts(module_dir, artifact_snapshot)
            report = _run_qg()
            _annotate_correction_terminal(
                report,
                failed_gate,
                "vesum_verified correction did not clear any previous missing surface and was rolled back",
            )
            correction_artifact["rolled_back"] = True
            correction_artifact["rollback_reason"] = "vesum_no_improvement"
            correction_artifact["restored_after"] = report
            _write_correction_artifact(
                module_dir / f"python_qg_correction_r{correction_round}.json",
                correction_artifact,
            )
            corrections.append(correction_artifact)
            _record_round(report, correction_round=correction_round, failed_gate=failed_gate)
            stopped_reason = "vesum_no_improvement"
            break

        if regressions:
            _restore_correction_artifacts(module_dir, artifact_snapshot)
            report = _run_qg()
            gates = report.setdefault("gates", {})
            if isinstance(gates, dict):
                gates["previously_passed_regression"] = {
                    "passed": False,
                    "regressions": regressions,
                }
                gates["passed"] = False
            correction_artifact["rolled_back"] = True
            correction_artifact["rollback_reason"] = "previously_passed_regression"
            correction_artifact["restored_after"] = report
            _write_correction_artifact(
                module_dir / f"python_qg_correction_r{correction_round}.json",
                correction_artifact,
            )
            corrections.append(correction_artifact)
            _record_round(report, correction_round=correction_round, failed_gate=failed_gate)
            stopped_reason = "previously_passed_regression"
            break

        _write_correction_artifact(
            module_dir / f"python_qg_correction_r{correction_round}.json",
            correction_artifact,
        )
        corrections.append(correction_artifact)
        current_round = _record_round(
            report,
            correction_round=correction_round,
            failed_gate=failed_gate,
        )
        if _python_qg_passed(report):
            stopped_reason = "pass"
            break

        best_idx = _python_qg_best_round_index(rounds)
        best_round = rounds[best_idx]
        if _python_qg_frontier_regressed(best_round["report"], current_round["report"]):
            consecutive_regressions += 1
            if consecutive_regressions >= PYTHON_QG_MIN_REGRESSION_PATIENCE:
                stopped_reason = "min_score_regressed"
                break
        else:
            consecutive_regressions = 0

    best_idx = _python_qg_best_round_index(rounds)
    best_round = rounds[best_idx]
    _restore_correction_artifacts(module_dir, best_round["artifacts"])
    correction_loop = {
        "max_correction_rounds": correction_budget,
        "rounds": [_python_qg_round_summary(item) for item in rounds],
        "best_round": best_round["round"],
        "stopped_reason": stopped_reason,
        "min_regression_patience": PYTHON_QG_MIN_REGRESSION_PATIENCE,
        "consecutive_regressions": consecutive_regressions,
        "corrections": corrections,
    }
    write_json(module_dir / "python_qg_correction_loop.json", correction_loop)
    return dict(best_round["report"])


def _run_python_qg_with_legacy_single_shot_corrections(
    module_dir: Path,
    plan_path: Path,
    *,
    verify_words_fn: Callable[[list[str]], dict[str, list[dict[str, Any]]]] | None = None,
    heritage_lookup_fn: Callable[[str], list[dict[str, Any]]] | None = None,
    qg_runner: Callable[[], dict[str, Any]] | None = None,
    writer_corrector: Callable[[CorrectionContext], str | Mapping[str, str] | None] | None = None,
    reviewer_corrector: Callable[[CorrectionContext], str | None] | None = None,
    dictionary_lookup_fn: Callable[[str, str], list[str | Mapping[str, str]]] | None = None,
    writer: str = "claude-tools",
    invoker: Callable[..., Any] | None = None,
    event_sink: Callable[..., None] | None = None,
) -> dict[str, Any]:
    """Run Python QG and apply one ADR-008 correction attempt per failed gate.

    This wrapper preserves ``run_python_qg`` as the deterministic gate runner.
    Corrections are intentionally single-shot. After every correction the full
    Python QG report is recomputed, and any gate that regresses from PASS to
    FAIL triggers the ``previously_passed_regression`` terminal meta-gate.
    """
    attempts: set[str] = set()
    correction_round = 0

    def _run_qg() -> dict[str, Any]:
        if qg_runner is not None:
            report = qg_runner()
        else:
            report = run_python_qg(
                module_dir,
                plan_path,
                verify_words_fn=verify_words_fn,
                heritage_lookup_fn=heritage_lookup_fn,
                event_sink=event_sink,
            )
        _attach_vocab_count_gate(report, module_dir=module_dir, plan_path=plan_path)
        return report

    report = _run_qg()
    while True:
        failed_gate = _first_failed_correctable_gate(report)
        if failed_gate is None:
            return report
        if failed_gate in attempts:
            _annotate_correction_terminal(
                report,
                failed_gate,
                f"{failed_gate} failed after its single ADR-008 correction attempt",
            )
            return report
        attempts.add(failed_gate)
        correction_round += 1

        before = report
        artifact_snapshot = (
            _snapshot_correction_artifacts(module_dir)
            if failed_gate in REVIEWER_FIX_GATES
            else None
        )
        handled, unmatched_anchors, correction_payload = _apply_python_qg_correction(
            failed_gate,
            report,
            module_dir=module_dir,
            plan_path=plan_path,
            writer_corrector=writer_corrector,
            reviewer_corrector=reviewer_corrector,
            dictionary_lookup_fn=dictionary_lookup_fn,
            writer=writer,
            invoker=invoker,
        )
        if not handled:
            _write_correction_artifact(
                module_dir / f"python_qg_correction_r{correction_round}.json",
                {
                    "round": correction_round,
                    "gate": failed_gate,
                    "handled": False,
                    "before": before,
                    "correction": correction_payload,
                },
            )
            _annotate_correction_terminal(
                report,
                failed_gate,
                f"{failed_gate} has no ADR-008 correction path",
            )
            return report

        report = _run_qg()
        regressions = _previously_passing_regressions(before, report)
        correction_artifact: dict[str, Any] = {
            "round": correction_round,
            "gate": failed_gate,
            "handled": True,
            "unmatched_anchors": sorted(unmatched_anchors),
            "before": before,
            "correction": correction_payload,
            "after": report,
            "regressions": regressions,
        }
        if artifact_snapshot is not None and correction_payload.get("yaml_invalid"):
            _restore_correction_artifacts(module_dir, artifact_snapshot)
            restored_report = _run_qg()
            _annotate_correction_terminal(
                restored_report,
                failed_gate,
                f"{failed_gate} correction produced invalid YAML and was rolled back",
            )
            correction_artifact["rolled_back"] = True
            correction_artifact["rollback_reason"] = "yaml_invalid"
            correction_artifact["restored_after"] = restored_report
            _write_correction_artifact(
                module_dir / f"python_qg_correction_r{correction_round}.json",
                correction_artifact,
            )
            return restored_report
        if (
            failed_gate == "vesum_verified"
            and artifact_snapshot is not None
            and not _vesum_correction_improved(before, report)
        ):
            _restore_correction_artifacts(module_dir, artifact_snapshot)
            restored_report = _run_qg()
            _annotate_correction_terminal(
                restored_report,
                failed_gate,
                "vesum_verified correction did not clear any previous missing surface and was rolled back",
            )
            correction_artifact["rolled_back"] = True
            correction_artifact["rollback_reason"] = "vesum_no_improvement"
            correction_artifact["restored_after"] = restored_report
            _write_correction_artifact(
                module_dir / f"python_qg_correction_r{correction_round}.json",
                correction_artifact,
            )
            return restored_report
        if regressions:
            if artifact_snapshot is not None:
                _restore_correction_artifacts(module_dir, artifact_snapshot)
                restored_report = _run_qg()
                gates = restored_report.setdefault("gates", {})
                if isinstance(gates, dict):
                    gates["previously_passed_regression"] = {
                        "passed": False,
                        "regressions": regressions,
                    }
                    gates["passed"] = False
                correction_artifact["rolled_back"] = True
                correction_artifact["rollback_reason"] = "previously_passed_regression"
                correction_artifact["restored_after"] = restored_report
                _write_correction_artifact(
                    module_dir / f"python_qg_correction_r{correction_round}.json",
                    correction_artifact,
                )
                return restored_report
            gates = report.setdefault("gates", {})
            if isinstance(gates, dict):
                gates["previously_passed_regression"] = {
                    "passed": False,
                    "regressions": regressions,
                }
                gates["passed"] = False
            correction_artifact["after"] = report
            _write_correction_artifact(
                module_dir / f"python_qg_correction_r{correction_round}.json",
                correction_artifact,
            )
            return report
        _write_correction_artifact(
            module_dir / f"python_qg_correction_r{correction_round}.json",
            correction_artifact,
        )


def run_wiki_coverage_with_corrections(
    *,
    plan: Mapping[str, Any],
    manifest: Mapping[str, Any] | str | Path,
    writer_output: str,
    module_dir: Path,
    level: str | None = None,
    batched_corrector: Callable[..., str] | None = None,
    narrow_corrector: Callable[..., str] | None = None,
    invoker: Callable[..., Any] | None = None,
    event_sink: Callable[..., None] | None = None,
    obligation_checklist: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run wiki_coverage_gate with batched and narrow correction loops.

    PR1 provides the seeded ``implementation_map.json`` sidecar, PR2 provides
    structured ``fix_proposals``, and PR3 applies bounded deterministic fixes
    from those proposals. PR4's Goodhart sentinel stays out of scope here and
    remains the existing wiki_coverage_review phase.

    Returns the final gate report. The caller decides whether ``passed=False``
    should abort the build.
    """

    def _run_gate() -> dict[str, Any]:
        return run_wiki_coverage_gate(
            manifest=manifest,
            writer_output=writer_output,
            module_dir=module_dir,
            level=level,
            obligation_checklist=obligation_checklist,
        )

    result = _run_gate()
    _emit_wiki_coverage_rule_events(
        result,
        manifest=manifest,
        module_dir=module_dir,
        level=level,
        event_sink=event_sink,
    )
    if result.get("passed") is True:
        return result

    batched_attempts = 0
    narrow_attempts = 0
    correction_round = 0
    for iteration in range(1, WIKI_COVERAGE_BATCH_MAX_ITERATIONS + 1):
        proposals = _wiki_coverage_fix_proposals(result)
        if not proposals:
            break
        batched_attempts = iteration
        correction_round += 1
        coverage_before = _wiki_coverage_coverage_pct(result)
        groups = _wiki_coverage_grouped_fix_proposals(proposals, module_dir)
        _emit(
            event_sink,
            "wiki_coverage_correction_pass_start",
            phase="batched",
            iteration=iteration,
            coverage_pct_before=coverage_before,
            fail_count=len(proposals),
        )
        backup_dir = _backup_wiki_coverage_artifacts(
            module_dir,
            phase="batched",
            iteration=iteration,
        )
        fixes_applied_total = 0
        attempt_records: list[dict[str, Any]] = []
        for group in groups:
            artifact = str(group["artifact"])
            artifact_text = _read_required(module_dir / artifact)
            prompt = render_wiki_coverage_correction_prompt(
                plan=plan,
                failure_group_key=str(group["key"]),
                fix_proposals=group["proposals"],
                artifact_text=artifact_text,
                coverage_pct_before=coverage_before,
                iteration=iteration,
            )
            response = _wiki_coverage_corrector_response(
                corrector=batched_corrector,
                invoker=invoker,
                prompt=prompt,
                module_dir=module_dir,
                effort="xhigh",
                task_id=f"wiki-coverage-batched-{iteration}",
                event_sink=event_sink,
                phase="batched",
                iteration=iteration,
                group_key=str(group["key"]),
                fix_proposals=group["proposals"],
                artifact_text=artifact_text,
            )
            fixes = _parse_reviewer_fixes(response)
            attempt_record: dict[str, Any] = {
                "group_key": str(group["key"]),
                "artifact": artifact,
                "prompt": prompt,
                "response": response,
                "fixes": fixes,
                "fixes_applied": 0,
            }
            if not fixes:
                _emit(
                    event_sink,
                    "wiki_coverage_correction_unparseable",
                    phase="batched",
                    iteration=iteration,
                    group_key=str(group["key"]),
                    response_preview=str(response or "")[:800],
                )
                attempt_record["status"] = "unparseable"
                attempt_records.append(attempt_record)
                continue
            fixes_applied = _apply_wiki_coverage_fixes(
                module_dir=module_dir,
                artifact=artifact,
                fixes=fixes,
                phase="batched",
                iteration=iteration,
                event_sink=event_sink,
                group_key=str(group["key"]),
            )
            fixes_applied_total += fixes_applied
            attempt_record["fixes_applied"] = fixes_applied
            attempt_record["status"] = "applied" if fixes_applied else "no_applicable_fix"
            attempt_records.append(attempt_record)

        after = _run_gate()
        coverage_after = _wiki_coverage_coverage_pct(after)
        correction_payload: dict[str, Any] = {
            "round": correction_round,
            "phase": "batched",
            "iteration": iteration,
            "coverage_pct_before": coverage_before,
            "coverage_pct_after": coverage_after,
            "fail_count": len(proposals),
            "fixes_applied_total": fixes_applied_total,
            "groups_processed": len(groups),
            "before": result,
            "after": after,
            "attempts": attempt_records,
        }
        if coverage_after < coverage_before - 1e-6:
            _restore_wiki_coverage_artifacts(module_dir, backup_dir)
            result = _run_gate()
            correction_payload["status"] = "regression"
            correction_payload["restored"] = result
            _write_correction_artifact(
                module_dir / f"wiki_coverage_correction_r{correction_round}.json",
                correction_payload,
            )
            _emit(
                event_sink,
                "wiki_coverage_correction_regression",
                phase="batched",
                iteration=iteration,
                coverage_pct_before=coverage_before,
                coverage_pct_after=coverage_after,
            )
            break
        correction_payload["status"] = "done"
        _write_correction_artifact(
            module_dir / f"wiki_coverage_correction_r{correction_round}.json",
            correction_payload,
        )
        _emit(
            event_sink,
            "wiki_coverage_correction_pass_done",
            phase="batched",
            iteration=iteration,
            coverage_pct_before=coverage_before,
            coverage_pct_after=coverage_after,
            fail_count=len(proposals),
            fixes_applied_total=fixes_applied_total,
            groups_processed=len(groups),
        )
        result = after
        if result.get("passed") is True:
            return result
        if coverage_after <= coverage_before + 1e-6:
            break

    for iteration in range(1, WIKI_COVERAGE_NARROW_MAX_ITERATIONS + 1):
        proposals = _wiki_coverage_fix_proposals(result)
        if not proposals:
            break
        narrow_attempts = iteration
        correction_round += 1
        coverage_before = _wiki_coverage_coverage_pct(result)
        _emit(
            event_sink,
            "wiki_coverage_correction_pass_start",
            phase="narrow",
            iteration=iteration,
            coverage_pct_before=coverage_before,
            fail_count=len(proposals),
        )
        backup_dir = _backup_wiki_coverage_artifacts(
            module_dir,
            phase="narrow",
            iteration=iteration,
        )
        fixes_applied_total = 0
        obligations_processed = 0
        attempt_records = []
        for proposal in proposals:
            obligations_processed += 1
            artifact = _wiki_coverage_target_artifact(proposal, module_dir)
            artifact_text = _read_required(module_dir / artifact)
            prompt = render_wiki_coverage_narrow_correction_prompt(
                plan=plan,
                fix_proposal=proposal,
                artifact_text=artifact_text,
                previous_batched_attempts=batched_attempts,
            )
            response = _wiki_coverage_corrector_response(
                corrector=narrow_corrector,
                invoker=invoker,
                prompt=prompt,
                module_dir=module_dir,
                effort="high",
                task_id=f"wiki-coverage-narrow-{iteration}",
                event_sink=event_sink,
                phase="narrow",
                iteration=iteration,
                obligation_id=str(proposal.get("obligation_id") or ""),
                fix_proposal=proposal,
                artifact_text=artifact_text,
            )
            fixes = _parse_reviewer_fixes(response)
            attempt_record = {
                "obligation_id": str(proposal.get("obligation_id") or ""),
                "artifact": artifact,
                "prompt": prompt,
                "response": response,
                "fixes": fixes,
                "fixes_applied": 0,
            }
            if not fixes:
                _emit(
                    event_sink,
                    "wiki_coverage_correction_unparseable",
                    phase="narrow",
                    iteration=iteration,
                    obligation_id=str(proposal.get("obligation_id") or ""),
                    response_preview=str(response or "")[:800],
                )
                attempt_record["status"] = "unparseable"
                attempt_records.append(attempt_record)
                continue
            fixes_applied = _apply_wiki_coverage_fixes(
                module_dir=module_dir,
                artifact=artifact,
                fixes=fixes,
                phase="narrow",
                iteration=iteration,
                event_sink=event_sink,
                obligation_id=str(proposal.get("obligation_id") or ""),
            )
            fixes_applied_total += fixes_applied
            attempt_record["fixes_applied"] = fixes_applied
            attempt_record["status"] = "applied" if fixes_applied else "no_applicable_fix"
            attempt_records.append(attempt_record)

        after = _run_gate()
        coverage_after = _wiki_coverage_coverage_pct(after)
        correction_payload = {
            "round": correction_round,
            "phase": "narrow",
            "iteration": iteration,
            "coverage_pct_before": coverage_before,
            "coverage_pct_after": coverage_after,
            "fail_count": len(proposals),
            "fixes_applied_total": fixes_applied_total,
            "obligations_processed": obligations_processed,
            "before": result,
            "after": after,
            "attempts": attempt_records,
        }
        if coverage_after < coverage_before - 1e-6:
            _restore_wiki_coverage_artifacts(module_dir, backup_dir)
            result = _run_gate()
            correction_payload["status"] = "regression"
            correction_payload["restored"] = result
            _write_correction_artifact(
                module_dir / f"wiki_coverage_correction_r{correction_round}.json",
                correction_payload,
            )
            _emit(
                event_sink,
                "wiki_coverage_correction_regression",
                phase="narrow",
                iteration=iteration,
                coverage_pct_before=coverage_before,
                coverage_pct_after=coverage_after,
            )
            break
        correction_payload["status"] = "done"
        _write_correction_artifact(
            module_dir / f"wiki_coverage_correction_r{correction_round}.json",
            correction_payload,
        )
        _emit(
            event_sink,
            "wiki_coverage_correction_pass_done",
            phase="narrow",
            iteration=iteration,
            coverage_pct_before=coverage_before,
            coverage_pct_after=coverage_after,
            fail_count=len(proposals),
            fixes_applied_total=fixes_applied_total,
            obligations_processed=obligations_processed,
        )
        result = after
        if result.get("passed") is True:
            return result

    _emit(
        event_sink,
        "wiki_coverage_plan_revision_request",
        coverage_pct_final=_wiki_coverage_coverage_pct(result),
        remaining_failures=_wiki_coverage_remaining_failures(result),
        total_iterations=batched_attempts + narrow_attempts,
        iterations_exhausted=True,
    )
    return result


def _wiki_coverage_fix_proposals(
    result: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    proposals = result.get("fix_proposals") or []
    if not isinstance(proposals, Sequence) or isinstance(proposals, (str, bytes)):
        return []
    return [item for item in proposals if isinstance(item, Mapping)]


def _wiki_coverage_coverage_pct(result: Mapping[str, Any]) -> float:
    try:
        return float(result.get("coverage_pct", 0.0))
    except (TypeError, ValueError):
        return 0.0


def _emit_wiki_coverage_rule_events(
    result: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] | str | Path,
    module_dir: Path,
    level: str | None,
    event_sink: Callable[..., None] | None,
) -> None:
    proposals = _wiki_coverage_fix_proposals(result)
    missing_impl_ids = [
        str(proposal.get("obligation_id") or "")
        for proposal in proposals
        if str(proposal.get("failure_reason") or proposal.get("reason") or proposal.get("status") or "")
        == "implementation_map_missing"
    ]
    if not missing_impl_ids:
        obligations = result.get("obligations") or []
        if isinstance(obligations, Sequence) and not isinstance(obligations, (str, bytes)):
            missing_impl_ids = [
                str(item.get("obligation_id") or item.get("id") or "")
                for item in obligations
                if isinstance(item, Mapping) and str(item.get("reason") or "") == "implementation_map_missing"
            ]
    if not missing_impl_ids:
        return
    _emit_writer_rule_fired(
        event_sink,
        rule_id=RULE_IMPL_MAP_COMPLETE,
        level=(str(level).lower() if level else None),
        slug=_wiki_manifest_slug(manifest, module_dir),
        gate="implementation_map_missing",
        evidence="missing_obligation_ids=" + ", ".join(sorted(set(missing_impl_ids))[:10]),
    )


def _wiki_coverage_grouped_fix_proposals(
    proposals: Sequence[Mapping[str, Any]],
    module_dir: Path,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for proposal in proposals:
        obligation_type = str(proposal.get("obligation_type") or "unknown")
        group_artifact = _wiki_coverage_group_key_artifact(proposal)
        if group_artifact:
            group_key = f"(artifact={group_artifact}, obligation_type={obligation_type})"
        else:
            group_key = f"(obligation_type={obligation_type})"
        target_artifact = _wiki_coverage_target_artifact(proposal, module_dir)
        grouped.setdefault((group_key, target_artifact), []).append(proposal)
    return [
        {
            "key": group_key,
            "artifact": artifact,
            "proposals": tuple(items),
        }
        for (group_key, artifact), items in grouped.items()
    ]


def _wiki_coverage_group_key_artifact(proposal: Mapping[str, Any]) -> str | None:
    expected_treatment = proposal.get("expected_treatment")
    if isinstance(expected_treatment, Mapping):
        artifact = _wiki_coverage_normalize_artifact(expected_treatment.get("artifact"))
        if artifact:
            return artifact
    return _wiki_coverage_normalize_artifact(proposal.get("artifact"))


def _wiki_coverage_target_artifact(proposal: Mapping[str, Any], module_dir: Path) -> str:
    artifact = _wiki_coverage_group_key_artifact(proposal)
    if artifact:
        return artifact
    obligation_id = str(proposal.get("obligation_id") or "")
    artifact_index = _wiki_coverage_seeded_artifact_index(module_dir)
    artifact = _wiki_coverage_normalize_artifact(artifact_index.get(obligation_id))
    if artifact:
        return artifact
    return _wiki_coverage_infer_artifact(proposal)


def _wiki_coverage_seeded_artifact_index(module_dir: Path) -> dict[str, str]:
    implementation_map_path = module_dir / "implementation_map.json"
    if not implementation_map_path.exists():
        return {}
    try:
        data = json.loads(implementation_map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    entries = data.get("entries") if isinstance(data, Mapping) else None
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
        return {}
    index: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        obligation_id = str(entry.get("obligation_id") or "")
        artifact = _wiki_coverage_normalize_artifact(entry.get("artifact"))
        if obligation_id and artifact:
            index[obligation_id] = artifact
    return index


def _wiki_coverage_infer_artifact(proposal: Mapping[str, Any]) -> str:
    expected_treatment = proposal.get("expected_treatment")
    if isinstance(expected_treatment, Mapping):
        treatment_text = "\n".join(str(value) for value in expected_treatment.values())
        for artifact in WIKI_COVERAGE_ARTIFACT_INFERENCE_ORDER:
            if artifact in treatment_text:
                return artifact
    haystack_parts: list[str] = []
    for key in ("surgical_diff_hint", "current_artifact_state"):
        haystack_parts.append(str(proposal.get(key) or ""))
    haystack = "\n".join(haystack_parts)
    for artifact in WIKI_COVERAGE_ARTIFACT_INFERENCE_ORDER:
        if artifact in haystack:
            return artifact
    return "module.md"


def _wiki_coverage_normalize_artifact(value: Any) -> str | None:
    artifact = str(value or "").strip()
    if artifact in WIKI_COVERAGE_PATCHABLE_ARTIFACTS:
        return artifact
    return None


def _wiki_coverage_corrector_response(
    *,
    corrector: Callable[..., str] | None,
    invoker: Callable[..., Any] | None,
    prompt: str,
    module_dir: Path,
    effort: str,
    task_id: str,
    event_sink: Callable[..., None] | None,
    **corrector_kwargs: Any,
) -> str:
    if corrector is not None:
        return str(
            corrector(
                prompt=prompt,
                module_dir=module_dir,
                **corrector_kwargs,
            )
            or ""
        )
    runtime_invoke = invoker
    if runtime_invoke is None:
        from scripts.agent_runtime.runner import invoke as runtime_invoke

    result = runtime_invoke(
        "codex",
        prompt,
        mode="read-only",
        cwd=module_dir,
        model=REVIEWER_DEFAULTS["codex-tools"]["model"],
        task_id=task_id,
        entrypoint="runtime",
        effort=effort,
        tool_config=_runtime_tool_config("codex-tools", workspace_dir=module_dir, event_sink=event_sink),
        event_sink=event_sink,
    )
    return str(getattr(result, "response", "") or "")


def _backup_wiki_coverage_artifacts(
    module_dir: Path,
    *,
    phase: str,
    iteration: int,
) -> Path:
    backup_dir = module_dir / ".wiki_correction_backup" / f"{phase}_iter_{iteration}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for artifact in WIKI_COVERAGE_PATCHABLE_ARTIFACTS:
        source = module_dir / artifact
        if source.exists():
            shutil.copy2(source, backup_dir / artifact)
    return backup_dir


def _restore_wiki_coverage_artifacts(module_dir: Path, backup_dir: Path) -> None:
    if not backup_dir.exists():
        return
    for backup_file in backup_dir.iterdir():
        if backup_file.name in WIKI_COVERAGE_PATCHABLE_ARTIFACTS:
            shutil.copy2(backup_file, module_dir / backup_file.name)


def _apply_wiki_coverage_fixes(
    *,
    module_dir: Path,
    artifact: str,
    fixes: list[dict[str, str]],
    phase: str,
    iteration: int,
    event_sink: Callable[..., None] | None,
    group_key: str | None = None,
    obligation_id: str | None = None,
) -> int:
    artifact_path = module_dir / artifact
    original = _read_required(artifact_path)
    normalized_fixes = _normalize_wiki_coverage_yaml_fixes(artifact, fixes)
    accepted_fixes, rejected_fixes = _validate_reviewer_fix_shapes(normalized_fixes)
    _emit_reviewer_fix_oversize_rejections(
        rejected_fixes,
        gate="wiki_coverage_gate",
        group_key=group_key,
        event_sink=event_sink,
        phase=phase,
        iteration=iteration,
        artifact=artifact,
        obligation_id=obligation_id,
    )
    if not accepted_fixes:
        return 0
    applicable_count = _count_applicable_reviewer_fixes(original, accepted_fixes)
    result = _apply_reviewer_fixes(
        original,
        accepted_fixes,
        gate="wiki_coverage_gate",
        module_dir=module_dir,
    )
    artifact_path.write_text(result.text, encoding="utf-8")
    try:
        _validate_wiki_coverage_artifact_text(artifact, result.text)
    except LinearPipelineError as exc:
        artifact_path.write_text(original, encoding="utf-8")
        _emit(
            event_sink,
            "wiki_coverage_correction_yaml_invalid",
            phase=phase,
            iteration=iteration,
            artifact=artifact,
            error_preview=str(exc)[:800],
        )
        return 0
    _emit(
        event_sink,
        "wiki_coverage_correction_fixes_applied",
        phase=phase,
        iteration=iteration,
        artifact=artifact,
        fixes_applied=applicable_count,
        group_key=group_key,
        obligation_id=obligation_id,
    )
    return applicable_count


def _count_applicable_reviewer_fixes(text: str, fixes: Sequence[Mapping[str, str]]) -> int:
    updated = text
    count = 0
    for fix in fixes:
        if "insert_after" in fix and "text" in fix:
            anchor = str(fix["insert_after"])
            if span := _find_reviewer_fix_span(updated, anchor):
                _, end = span
                updated = updated[:end] + str(fix["text"]) + updated[end:]
                count += 1
            continue
        find = str(fix.get("find") or "")
        replace = fix.get("replace")
        if find and replace is not None and (
            span := _find_reviewer_fix_span(updated, find)
        ):
            start, end = span
            updated = updated[:start] + str(replace) + updated[end:]
            count += 1
    return count


def _normalize_wiki_coverage_yaml_fixes(
    artifact: str,
    fixes: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    if artifact not in CORRECTION_YAML_ARTIFACT_REQUIRED_FIELDS:
        return [dict(fix) for fix in fixes]
    normalized: list[dict[str, str]] = []
    for fix in fixes:
        item = {str(key): str(value) for key, value in fix.items()}
        if "insert_after" in item and "text" in item:
            anchor = item["insert_after"]
            insert_text = item["text"]
            if insert_text and not insert_text.startswith("\n") and not anchor.endswith("\n"):
                item["text"] = "\n" + insert_text
        normalized.append(item)
    return normalized


def _reviewer_fix_body(fix: Mapping[str, str]) -> tuple[str, str] | None:
    if "replace" in fix:
        return "replace", str(fix["replace"])
    if "text" in fix:
        return "text", str(fix["text"])
    return None


def _reviewer_fix_line_count(body: str) -> int:
    if body == "":
        return 0
    return body.count("\n") + 1


def _validate_reviewer_fix_shapes(
    fixes: list[dict[str, str]],
    *,
    max_lines: int = 6,
    max_chars: int = 240,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Split parsed fixes into (accepted, rejected_oversize).

    A fix is rejected when its `replace` or `text` body exceeds the size
    limit, which is evidence of regeneration per the corrector prompt contract.
    """
    accepted: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    for fix in fixes:
        body_info = _reviewer_fix_body(fix)
        if body_info is None:
            accepted.append(fix)
            continue
        _, body = body_info
        if _reviewer_fix_line_count(body) > max_lines or len(body) > max_chars:
            rejected.append(fix)
            continue
        accepted.append(fix)
    return accepted, rejected


def _emit_reviewer_fix_oversize_rejections(
    rejected_fixes: Sequence[Mapping[str, str]],
    *,
    gate: str,
    group_key: str | None,
    event_sink: Callable[..., None] | None = None,
    **fields: Any,
) -> None:
    for fix in rejected_fixes:
        body_info = _reviewer_fix_body(fix)
        if body_info is None:
            continue
        body_field, body = body_info
        _emit(
            event_sink,
            "reviewer_fix_oversize_rejected",
            gate=gate,
            group_key=group_key,
            body_field=body_field,
            body_len=len(body),
            line_count=_reviewer_fix_line_count(body),
            body_preview=_correction_preview(body),
            **fields,
        )


def _validate_wiki_coverage_artifact_text(artifact: str, text: str) -> None:
    required_fields = CORRECTION_YAML_ARTIFACT_REQUIRED_FIELDS.get(artifact)
    if required_fields is None:
        return
    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise LinearPipelineError(f"{artifact} invalid YAML: {exc}") from exc
    if artifact == "activities.yaml":
        items_to_validate = _activity_list_from_loaded_data(parsed)
    else:
        if not isinstance(parsed, list):
            raise LinearPipelineError(f"{artifact} must remain a bare YAML list")
        items_to_validate = parsed
    for index, item in enumerate(items_to_validate, start=1):
        if not isinstance(item, dict):
            raise LinearPipelineError(f"{artifact} entries must remain mappings; item {index} is {type(item).__name__}")
    try:
        redumped = yaml.safe_dump(parsed, allow_unicode=True, sort_keys=False)
        reparsed = yaml.safe_load(redumped)
    except yaml.YAMLError as exc:
        raise LinearPipelineError(f"{artifact} failed YAML round-trip: {exc}") from exc
    if parsed != reparsed:
        raise LinearPipelineError(
            f"{artifact} does not round-trip cleanly; likely scalar/mapping ambiguity or non-portable scalar value"
        )
    for index, item in enumerate(items_to_validate, start=1):
        for field in required_fields:
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise LinearPipelineError(
                    f"{artifact} item {index} requires {field} as a non-empty "
                    f"string (got {type(value).__name__}: {value!r})"
                )
        if artifact == "activities.yaml" and "items" in item:
            items = item["items"]
            if not isinstance(items, list):
                raise LinearPipelineError(f"{artifact} item {index} field items must remain a list")
            activity_type = str(item.get("type") or "")
            required_item_fields = _ACTIVITY_ITEM_REQUIRED_FIELDS.get(activity_type)
            if required_item_fields is None:
                continue
            for item_index, nested_item in enumerate(items, start=1):
                if not isinstance(nested_item, dict):
                    raise LinearPipelineError(
                        f"{artifact} item {index} items entry {item_index} "
                        f"must remain a mapping (got {type(nested_item).__name__})"
                    )
                for field in required_item_fields:
                    value = nested_item.get(field)
                    if not isinstance(value, str) or not value.strip():
                        raise LinearPipelineError(
                            f"{artifact} item {index} items entry {item_index} "
                            f"requires {field} as a non-empty string "
                            f"(got {type(value).__name__}: {value!r})"
                        )


def _wiki_coverage_remaining_failures(result: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    proposals = _wiki_coverage_fix_proposals(result)
    if proposals:
        return proposals
    obligations = result.get("obligations") or []
    if not isinstance(obligations, Sequence) or isinstance(obligations, (str, bytes)):
        return []
    return [item for item in obligations if isinstance(item, Mapping) and item.get("status") == "FAIL"]


def _first_failed_correctable_gate(report: Mapping[str, Any]) -> str | None:
    gates = report.get("gates")
    if not isinstance(gates, Mapping):
        return None
    for gate in PYTHON_QG_GATE_ORDER:
        gate_report = gates.get(gate)
        if isinstance(gate_report, Mapping) and gate_report.get("passed") is False:
            return gate
    return None


def _annotate_correction_terminal(
    report: dict[str, Any],
    gate: str,
    message: str,
) -> None:
    gates = report.setdefault("gates", {})
    if isinstance(gates, dict):
        gates["correction_terminal"] = {
            "passed": False,
            "gate": gate,
            "message": message,
        }
        gates["passed"] = False


def _snapshot_correction_artifacts(module_dir: Path) -> dict[str, str | None]:
    snapshot: dict[str, str | None] = {}
    for artifact in WRITER_ARTIFACTS:
        path = module_dir / artifact
        snapshot[artifact] = path.read_text(encoding="utf-8") if path.exists() else None
    return snapshot


def _restore_correction_artifacts(module_dir: Path, snapshot: Mapping[str, str | None]) -> None:
    for artifact, text in snapshot.items():
        path = module_dir / artifact
        if text is None:
            path.unlink(missing_ok=True)
            continue
        path.write_text(text, encoding="utf-8")


def _normalized_vesum_missing(report: Mapping[str, Any]) -> frozenset[str]:
    gates = report.get("gates")
    if not isinstance(gates, Mapping):
        return frozenset()
    gate_report = gates.get("vesum_verified")
    if not isinstance(gate_report, Mapping):
        return frozenset()
    missing = gate_report.get("missing")
    if not isinstance(missing, Sequence) or isinstance(missing, (str, bytes)):
        return frozenset()
    return frozenset(
        _normalize_for_vesum(str(surface)).lower()
        for surface in missing
        if str(surface).strip()
    )


def _vesum_correction_improved(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> bool:
    before_missing = _normalized_vesum_missing(before)
    after_missing = _normalized_vesum_missing(after)
    return bool(before_missing) and after_missing < before_missing


def _attach_vocab_count_gate(report: dict[str, Any], *, module_dir: Path, plan_path: Path) -> None:
    gates = report.get("gates")
    if not isinstance(gates, dict) or "vocab_count" in gates:
        return
    vocab_path = module_dir / "vocabulary.yaml"
    if not vocab_path.exists() or not plan_path.exists():
        return
    try:
        plan = plan_check(plan_path)
        vocabulary = _load_yaml_list(vocab_path, "vocabulary")
    except LinearPipelineError:
        return
    gate_report = _vocab_count_gate(vocabulary, plan)
    gates["vocab_count"] = gate_report
    if gate_report.get("passed") is False:
        gates["passed"] = False


def _vocab_count_gate(vocabulary: list[dict[str, Any]], plan: Mapping[str, Any]) -> dict[str, Any]:
    floor = _vocab_floor_for_plan(plan)
    count = len(vocabulary)
    unused_candidates = _unused_recommended_vocab_candidates(plan, vocabulary)
    report: dict[str, Any] = {
        "passed": count >= floor,
        "count": count,
        "floor": floor,
        "candidate_source": "plan.vocabulary_hints.recommended",
        "unused_recommended_count": len(unused_candidates),
        "unused_recommended_lemmas": [str(item.get("lemma") or "") for item in unused_candidates],
    }
    if count < floor:
        message = f"vocabulary.yaml has {count} entries; floor is {floor}"
        if count + len(unused_candidates) < floor:
            message += "; plan recommends insufficient unused vocabulary to reach floor"
        report["message"] = message
    return report


def _vocab_floor_for_plan(plan: Mapping[str, Any]) -> int:
    level = str(plan.get("level") or "").lower()
    slug = str(plan.get("slug") or "").lower()
    try:
        sequence = int(plan.get("sequence") or 0)
    except (TypeError, ValueError):
        sequence = 0
    try:
        configured = int(_activity_config(level, sequence, slug).get("VOCAB_COUNT_TARGET") or 0)
    except (LinearPipelineError, KeyError, TypeError, ValueError):
        configured = 0
    if "checkpoint" in slug:
        return configured
    return max(configured, 25)


def _vocab_lemma_key(value: Any) -> str:
    text = str(value or "").strip().casefold()
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _vocab_item_lemma(item: Mapping[str, Any]) -> str:
    return str(item.get("lemma") or item.get("word") or "").strip()


def _vocab_hint_to_item(item: Any) -> dict[str, Any] | None:
    if isinstance(item, Mapping):
        lemma = str(item.get("lemma") or item.get("word") or item.get("term") or "").strip()
        if not lemma:
            return None
        translation = str(item.get("translation") or item.get("definition") or item.get("gloss") or "").strip()
        pos = str(item.get("pos") or "").strip() or ("phrase" if " " in lemma else "term")
        usage = str(item.get("usage") or item.get("example") or "").strip()
        return {
            "lemma": lemma,
            "translation": translation,
            "pos": pos,
            "usage": usage,
        }
    if not isinstance(item, str):
        return None
    raw = item.strip()
    if not raw:
        return None
    match = re.match(r"^(?P<lemma>[^()]+?)(?:\s*\((?P<translation>[^)]*)\))?\s*$", raw)
    if not match:
        return None
    lemma = match.group("lemma").strip()
    if not lemma:
        return None
    translation = (match.group("translation") or "").strip()
    return {
        "lemma": lemma,
        "translation": translation,
        "pos": "phrase" if " " in lemma else "term",
        "usage": "",
    }


def _unused_recommended_vocab_candidates(
    plan: Mapping[str, Any],
    vocabulary: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    hints = plan.get("vocabulary_hints")
    if not isinstance(hints, Mapping):
        return []
    recommended = hints.get("recommended")
    if not isinstance(recommended, list):
        return []
    seen = {_vocab_lemma_key(_vocab_item_lemma(item)) for item in vocabulary}
    candidates: list[dict[str, Any]] = []
    for hint in recommended:
        item = _vocab_hint_to_item(hint)
        if item is None:
            continue
        key = _vocab_lemma_key(item["lemma"])
        if not key or key in seen:
            continue
        seen.add(key)
        candidates.append(item)
    return candidates


def _coerce_vocab_yaml(vocab_yaml: str | Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    parsed = yaml.safe_load(vocab_yaml) or [] if isinstance(vocab_yaml, str) else list(vocab_yaml)
    if not isinstance(parsed, list) or not all(isinstance(item, Mapping) for item in parsed):
        raise LinearPipelineError("vocabulary YAML must be a list of mappings for vocab_floor correction")
    return [dict(item) for item in parsed]


def _correct_vocab_floor(
    plan: Mapping[str, Any],
    vocab_yaml: str | Sequence[Mapping[str, Any]],
    gate_payload: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    vocabulary = _coerce_vocab_yaml(vocab_yaml)
    floor = _gate_int(gate_payload, "floor", "minimum", "min_count", "target_min", default=_vocab_floor_for_plan(plan))
    count_before = len(vocabulary)
    candidates = _unused_recommended_vocab_candidates(plan, vocabulary)
    needed = max(0, floor - count_before)
    added = candidates[:needed]
    updated = [*vocabulary, *added]
    exhausted = len(updated) < floor
    diagnostic: dict[str, Any] = {
        "kind": "vocab_floor",
        "candidate_source": "plan.vocabulary_hints.recommended",
        "floor": floor,
        "count_before": count_before,
        "count_after": len(updated),
        "needed_count": needed,
        "candidate_count": len(candidates),
        "added_count": len(added),
        "added_lemmas": [str(item.get("lemma") or "") for item in added],
        "exhausted": exhausted,
    }
    if exhausted:
        diagnostic["message"] = (
            "plan recommends insufficient unused vocabulary to reach floor: "
            f"count_after={len(updated)} floor={floor}"
        )
    return updated, diagnostic


def _apply_vocab_floor_correction(
    *,
    module_dir: Path,
    plan_path: Path,
    gate_report: Mapping[str, Any],
) -> dict[str, Any]:
    plan = plan_check(plan_path)
    vocab_path = module_dir / "vocabulary.yaml"
    vocabulary = _load_yaml_list(vocab_path, "vocabulary")
    updated, diagnostic = _correct_vocab_floor(plan, vocabulary, gate_report)
    vocab_path.write_text(yaml.safe_dump(updated, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return {
        "kind": "pipeline_vocab_floor",
        "gate": "vocab_count",
        "gate_report": dict(gate_report),
        "diagnostic": diagnostic,
    }


def _normalize_performance_self_check_duplicates(
    activities: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    for activity_index, activity in enumerate(activities, start=1):
        if (
            str(activity.get("type") or "") == "performance"
            and "self_check" in activity
            and not isinstance(activity.get("self_check"), list)
            and "self_checklist" in activity
            and isinstance(activity.get("self_checklist"), list)
        ):
            removed_value = activity.pop("self_check")
            normalized.append(activity)
            removed.append(
                {
                    "activity_index": activity_index,
                    "activity_id": str(activity.get("id") or f"#{activity_index}"),
                    "removed_field": "self_check",
                    "removed_type": type(removed_value).__name__,
                    "self_checklist_count": len(activity["self_checklist"]),
                }
            )
            continue
        normalized.append(activity)
    return normalized, {
        "kind": "performance_self_check_duplicate",
        "normalized_count": len(removed),
        "normalized": removed,
    }


def _normalize_activity_schema_forbidden_item_fields(
    activities: Sequence[dict[str, Any]],
    gate_report: Mapping[str, Any],
) -> dict[str, Any]:
    violations = gate_report.get("violations")
    if not isinstance(violations, Sequence) or isinstance(violations, (str, bytes, bytearray)):
        violations = []
    removed: list[dict[str, Any]] = []
    for violation in violations:
        if not isinstance(violation, Mapping):
            continue
        if violation.get("expected_field") is not None:
            continue
        offending_field = str(violation.get("offending_field") or "").strip()
        if not offending_field:
            continue
        try:
            activity_index = int(violation.get("activity_index")) - 1
            item_index = int(violation.get("item_index")) - 1
        except (TypeError, ValueError):
            continue
        if activity_index < 0 or item_index < 0 or activity_index >= len(activities):
            continue
        activity = activities[activity_index]
        items = activity.get("items")
        if not isinstance(items, list) or item_index >= len(items):
            continue
        item = items[item_index]
        if not isinstance(item, dict) or offending_field not in item:
            continue
        item.pop(offending_field)
        removed.append(
            {
                "activity_index": activity_index + 1,
                "activity_id": str(activity.get("id") or f"#{activity_index + 1}"),
                "item_index": item_index + 1,
                "removed_field": offending_field,
            }
        )
    return {
        "kind": "forbidden_item_fields",
        "normalized_count": len(removed),
        "normalized": removed,
    }


def _activity_schema_line_targets(
    diagnostics: Sequence[Mapping[str, Any]],
    *,
    field_key: str,
) -> set[tuple[int | None, str, int | None, str]]:
    targets: set[tuple[int | None, str, int | None, str]] = set()
    for diagnostic in diagnostics:
        field = str(diagnostic.get(field_key) or "").strip()
        if not field:
            continue
        try:
            activity_index = int(diagnostic.get("activity_index"))
        except (TypeError, ValueError):
            activity_index = None
        try:
            item_index = int(diagnostic.get("item_index"))
        except (TypeError, ValueError):
            item_index = None
        targets.add(
            (
                activity_index,
                str(diagnostic.get("activity_id") or "").strip(),
                item_index,
                field,
            )
        )
    return targets


def _activity_line_id(line: str) -> tuple[int, str] | None:
    match = re.match(r"^(?P<indent>\s*)-\s+id:\s*(?P<id>.+?)\s*$", line)
    if match is None or len(match.group("indent")) > 2:
        return None
    raw_id = match.group("id").strip()
    return len(match.group("indent")), raw_id.strip("\"'")


def _activity_schema_target_matches(
    targets: set[tuple[int | None, str, int | None, str]],
    *,
    activity_index: int,
    activity_id: str,
    item_index: int | None,
    field: str,
) -> bool:
    return any(
        target_activity_index in (None, activity_index)
        and (not target_activity_id or target_activity_id == activity_id)
        and target_item_index == item_index
        and target_field == field
        for target_activity_index, target_activity_id, target_item_index, target_field in targets
    )


def _remove_activity_field_lines(
    text: str,
    targets: set[tuple[int | None, str, int | None, str]],
) -> str:
    if not targets:
        return text
    output: list[str] = []
    activity_index = 0
    activity_id = ""
    activity_indent = -1
    for line in text.splitlines(keepends=True):
        activity = _activity_line_id(line)
        if activity is not None:
            activity_index += 1
            activity_indent, activity_id = activity
        field_match = re.match(r"^(?P<indent>\s*)(?P<field>[A-Za-z_][A-Za-z0-9_-]*)\s*:\s*.*(?:\n|$)", line)
        if (
            field_match is not None
            and activity_index > 0
            and len(field_match.group("indent")) > activity_indent
            and _activity_schema_target_matches(
                targets,
                activity_index=activity_index,
                activity_id=activity_id,
                item_index=None,
                field=field_match.group("field"),
            )
        ):
            continue
        output.append(line)
    return "".join(output)


def _remove_forbidden_activity_item_field_lines(text: str, gate_report: Mapping[str, Any]) -> str:
    violations = gate_report.get("violations")
    if not isinstance(violations, Sequence) or isinstance(violations, (str, bytes, bytearray)):
        violations = []
    targets = _activity_schema_line_targets(
        [violation for violation in violations if isinstance(violation, Mapping)],
        field_key="offending_field",
    )
    if not targets:
        return text
    output: list[str] = []
    activity_index = 0
    activity_id = ""
    in_items = False
    items_indent = -1
    item_indent: int | None = None
    item_index = 0
    for line in text.splitlines(keepends=True):
        activity = _activity_line_id(line)
        if activity is not None:
            activity_index += 1
            _activity_indent, activity_id = activity
            in_items = False
            item_indent = None
            item_index = 0
        indent_len = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if in_items and stripped and indent_len <= items_indent:
            in_items = False
            item_indent = None
            item_index = 0
        if activity_index > 0 and re.match(r"^\s*items\s*:\s*$", line):
            in_items = True
            items_indent = indent_len
            item_indent = None
            item_index = 0
        elif in_items:
            item_match = re.match(r"^(?P<indent>\s*)-\s+", line)
            if item_match is not None:
                current_indent = len(item_match.group("indent"))
                if item_indent is None and current_indent > items_indent:
                    item_indent = current_indent
                    item_index += 1
                elif item_indent is not None and current_indent == item_indent:
                    item_index += 1
            field_match = re.match(r"^\s+(?P<field>[A-Za-z_][A-Za-z0-9_-]*)\s*:\s*.*(?:\n|$)", line)
            if (
                field_match is not None
                and item_indent is not None
                and item_index > 0
                and _activity_schema_target_matches(
                    targets,
                    activity_index=activity_index,
                    activity_id=activity_id,
                    item_index=item_index,
                    field=field_match.group("field"),
                )
            ):
                continue
        output.append(line)
    return "".join(output)


def _apply_activity_schema_correction(
    *,
    module_dir: Path,
    gate_report: Mapping[str, Any],
) -> dict[str, Any]:
    activities_path = module_dir / "activities.yaml"
    data = load_yaml(activities_path)
    activities = _activity_list_from_loaded_data(data)
    normalized, self_check_diagnostic = _normalize_performance_self_check_duplicates(activities)
    forbidden_field_diagnostic = _normalize_activity_schema_forbidden_item_fields(activities, gate_report)
    normalized_count = int(self_check_diagnostic["normalized_count"]) + int(
        forbidden_field_diagnostic["normalized_count"]
    )
    if normalized_count > 0:
        if isinstance(data, dict):
            original_text = activities_path.read_text(encoding="utf-8")
            self_check_targets = _activity_schema_line_targets(
                [
                    diagnostic
                    for diagnostic in self_check_diagnostic.get("normalized", ())
                    if isinstance(diagnostic, Mapping)
                ],
                field_key="removed_field",
            )
            updated_text = _remove_activity_field_lines(original_text, self_check_targets)
            updated_text = _remove_forbidden_activity_item_field_lines(updated_text, gate_report)
            activities_path.write_text(updated_text, encoding="utf-8")
        else:
            activities_path.write_text(
                yaml.safe_dump(
                    data if isinstance(data, dict) else normalized,
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
    return {
        "kind": "pipeline_activity_schema_normalization",
        "gate": "activity_schema",
        "gate_report": dict(gate_report),
        "applied": bool(normalized_count),
        "diagnostic": {
            "kind": "activity_schema_normalization",
            "normalized_count": normalized_count,
            "self_check": self_check_diagnostic,
            "forbidden_item_fields": forbidden_field_diagnostic,
        },
    }


def _apply_python_qg_correction(
    gate: str,
    qg_report: Mapping[str, Any],
    *,
    module_dir: Path,
    plan_path: Path,
    writer_corrector: Callable[[CorrectionContext], str | Mapping[str, str] | None] | None,
    reviewer_corrector: Callable[[CorrectionContext], str | None] | None,
    dictionary_lookup_fn: Callable[[str, str], list[str | Mapping[str, str]]] | None,
    writer: str,
    invoker: Callable[..., Any] | None,
) -> tuple[bool, frozenset[str], dict[str, Any]]:
    gates = qg_report.get("gates")
    if not isinstance(gates, Mapping):
        return False, frozenset(), {"reason": "missing gates mapping"}
    gate_report = gates.get(gate)
    if not isinstance(gate_report, Mapping):
        return False, frozenset(), {"reason": "missing gate report"}
    if gate in TERMINAL_ZERO_RETRY_GATES:
        return False, frozenset(), {"reason": "terminal zero-retry gate"}
    if gate in PIPELINE_INSERT_GATES:
        _apply_activity_id_inserts(module_dir / "module.md", gate_report)
        return (
            True,
            frozenset(),
            {
                "kind": "pipeline_insert",
                "gate": gate,
                "gate_report": dict(gate_report),
            },
        )
    if gate in DETERMINISTIC_VOCAB_FLOOR_GATES:
        payload = _apply_vocab_floor_correction(module_dir=module_dir, plan_path=plan_path, gate_report=gate_report)
        return True, frozenset(), payload
    if gate == "activity_schema":
        payload = _apply_activity_schema_correction(module_dir=module_dir, gate_report=gate_report)
        if payload.get("applied") is True:
            return True, frozenset(), payload
    if gate in WRITER_CORRECTION_GATES:
        payload = _apply_writer_correction(
            gate,
            gate_report,
            qg_report=qg_report,
            module_dir=module_dir,
            plan_path=plan_path,
            writer_corrector=writer_corrector,
            writer=writer,
            invoker=invoker,
        )
        return True, frozenset(), payload
    if gate in REVIEWER_FIX_GATES:
        candidates = ()
        if gate in DICTIONARY_CANDIDATE_GATES:
            candidates = generate_dictionary_candidates(
                gate,
                gate_report,
                qg_report=qg_report,
                dictionary_lookup_fn=dictionary_lookup_fn,
            )
        unmatched_anchors, payload = _apply_reviewer_correction(
            gate,
            gate_report,
            qg_report=qg_report,
            module_dir=module_dir,
            plan_path=plan_path,
            candidates=candidates,
            reviewer_corrector=reviewer_corrector,
            invoker=invoker,
        )
        return True, unmatched_anchors, payload
    return False, frozenset(), {"reason": "no correction path", "gate": gate}


def _apply_writer_correction(
    gate: str,
    gate_report: Mapping[str, Any],
    *,
    qg_report: Mapping[str, Any],
    module_dir: Path,
    plan_path: Path,
    writer_corrector: Callable[[CorrectionContext], str | Mapping[str, str] | None] | None,
    writer: str,
    invoker: Callable[..., Any] | None,
) -> dict[str, Any]:
    module_text = _read_required(module_dir / "module.md")
    prompt = render_writer_correction_prompt(
        gate=gate,
        gate_report=gate_report,
        module_text=module_text,
        writer=writer,
    )
    context = CorrectionContext(
        gate=gate,
        gate_report=gate_report,
        module_dir=module_dir,
        plan_path=plan_path,
        qg_report=qg_report,
        prompt=prompt,
    )
    if writer_corrector is None:
        response: str | Mapping[str, str] | None = invoke_writer(
            prompt,
            writer=writer,
            cwd=module_dir,
            invoker=invoker,
        )
    else:
        response = writer_corrector(context)
    if isinstance(response, Mapping):
        write_writer_artifacts(module_dir, response)
        return {
            "kind": "writer",
            "gate": gate,
            "prompt": prompt,
            "response": dict(response),
            "applied": "writer_artifacts_mapping",
        }
    if isinstance(response, str):
        # Strict-JSON-parse failures need all 4 artifact blocks back since the
        # original parse was the failure mode itself. Other gates are
        # module.md-only patches per the linear-writer-correction.md output
        # contract.
        if all(name in response for name in WRITER_ARTIFACTS):
            write_writer_artifacts(module_dir, parse_writer_output_strict_json(response))
            return {
                "kind": "writer",
                "gate": gate,
                "prompt": prompt,
                "response": response,
                "applied": "strict_json_artifacts",
            }
        if gate != "strict_json_parse":
            patched = parse_writer_correction_module_only(response)
            if patched is not None:
                (module_dir / "module.md").write_text(patched, encoding="utf-8")
                return {
                    "kind": "writer",
                    "gate": gate,
                    "prompt": prompt,
                    "response": response,
                    "applied": "module_patch",
                }
    emit_event(
        "writer_correction_unparseable",
        **_correction_event_fields(
            gate=gate,
            module_dir=module_dir,
            plan_path=plan_path,
        ),
        response_preview=_correction_preview(response),
    )
    return {
        "kind": "writer",
        "gate": gate,
        "prompt": prompt,
        "response": response,
        "applied": "unparseable",
    }


def _apply_reviewer_correction(
    gate: str,
    gate_report: Mapping[str, Any],
    *,
    qg_report: Mapping[str, Any],
    module_dir: Path,
    plan_path: Path,
    candidates: tuple[CorrectionCandidate, ...],
    reviewer_corrector: Callable[[CorrectionContext], str | None] | None,
    invoker: Callable[..., Any] | None,
) -> tuple[frozenset[str], dict[str, Any]]:
    module_path = module_dir / "module.md"
    module_text = _read_required(module_path)
    additional_artifact_names = REVIEWER_FIX_ADDITIONAL_ARTIFACTS_BY_GATE.get(gate, ())
    additional_artifact_texts = {
        artifact: _read_required(module_dir / artifact)
        for artifact in additional_artifact_names
        if (module_dir / artifact).exists()
    }
    prompt = render_reviewer_correction_prompt(
        gate=gate,
        gate_report=gate_report,
        module_text=module_text,
        candidates=candidates,
        artifact_texts=additional_artifact_texts,
    )
    context = CorrectionContext(
        gate=gate,
        gate_report=gate_report,
        module_dir=module_dir,
        plan_path=plan_path,
        qg_report=qg_report,
        candidates=candidates,
        prompt=prompt,
    )
    if reviewer_corrector is None:
        if invoker is None:
            from scripts.agent_runtime.runner import invoke as runtime_invoke
        else:
            runtime_invoke = invoker

        result = runtime_invoke(
            "codex",
            prompt,
            mode="read-only",
            cwd=module_dir,
            model=REVIEWER_DEFAULTS["codex-tools"]["model"],
            task_id=f"linear-python-qg-{gate}-fix",
            entrypoint="runtime",
            effort=REVIEWER_DEFAULTS["codex-tools"]["effort"],
            tool_config=_runtime_tool_config("codex-tools", workspace_dir=module_dir),
        )
        response = str(getattr(result, "response", "") or "")
    else:
        response = reviewer_corrector(context) or ""
    fixes = _parse_reviewer_fixes(response)
    if not fixes:
        emit_event(
            "reviewer_fixes_unparseable",
            **_correction_event_fields(
                gate=gate,
                module_dir=module_dir,
                plan_path=plan_path,
            ),
            response_preview=_correction_preview(response),
        )
        return frozenset(), {
            "kind": "reviewer",
            "gate": gate,
            "prompt": prompt,
            "response": response,
            "fixes": [],
            "accepted_fixes": [],
            "rejected_fixes": [],
            "applied": False,
        }
    accepted_fixes, rejected_fixes = _validate_reviewer_fix_shapes(fixes)
    correction_fields = _correction_event_fields(
        gate=gate,
        module_dir=module_dir,
        plan_path=plan_path,
    )
    correction_fields.pop("gate", None)
    _emit_reviewer_fix_oversize_rejections(
        rejected_fixes,
        gate=gate,
        group_key=None,
        **correction_fields,
    )
    if not accepted_fixes:
        return frozenset(), {
            "kind": "reviewer",
            "gate": gate,
            "prompt": prompt,
            "response": response,
            "fixes": fixes,
            "accepted_fixes": [],
            "rejected_fixes": rejected_fixes,
            "applied": False,
        }
    artifact_names = ("module.md", *additional_artifact_names)
    unmatched_by_artifact: list[set[str]] = []
    artifact_results: list[dict[str, Any]] = []
    for artifact in artifact_names:
        artifact_path = module_dir / artifact
        if artifact != "module.md" and not artifact_path.exists():
            continue
        original_text = module_text if artifact == "module.md" else _read_required(artifact_path)
        result = _apply_reviewer_fixes(
            original_text,
            accepted_fixes,
            gate=gate,
            module_dir=module_dir,
            plan_path=plan_path,
            emit_unmatched_events=False,
        )
        unmatched_by_artifact.append(set(result.unmatched_anchors))
        changed = result.text != original_text
        artifact_record: dict[str, Any] = {"artifact": artifact, "changed": changed}
        if changed:
            artifact_path.write_text(result.text, encoding="utf-8")
            try:
                _validate_wiki_coverage_artifact_text(artifact, result.text)
            except LinearPipelineError as exc:
                artifact_path.write_text(original_text, encoding="utf-8")
                artifact_record["changed"] = False
                artifact_record["yaml_valid"] = False
                emit_event(
                    "reviewer_correction_yaml_invalid",
                    **_correction_event_fields(
                        gate=gate,
                        module_dir=module_dir,
                        plan_path=plan_path,
                    ),
                    artifact=artifact,
                    error_preview=str(exc)[:800],
                )
            else:
                artifact_record["yaml_valid"] = True
        artifact_results.append(artifact_record)
    yaml_invalid = any(record.get("yaml_valid") is False for record in artifact_results)

    unmatched_anchors = (
        frozenset(set.intersection(*unmatched_by_artifact))
        if unmatched_by_artifact
        else frozenset()
    )
    _emit_final_reviewer_unmatched_events(
        unmatched_anchors,
        accepted_fixes,
        gate=gate,
        module_dir=module_dir,
        plan_path=plan_path,
    )
    return unmatched_anchors, {
        "kind": "reviewer",
        "gate": gate,
        "prompt": prompt,
        "response": response,
        "fixes": fixes,
        "accepted_fixes": accepted_fixes,
        "rejected_fixes": rejected_fixes,
        "unmatched_anchors": sorted(unmatched_anchors),
        "artifacts": artifact_results,
        "yaml_invalid": yaml_invalid,
        "applied": True,
    }


def _apply_activity_id_inserts(module_path: Path, gate_report: Mapping[str, Any]) -> None:
    """Resolve ``inject_activity_ids:unused_activities_not_injected`` by
    stripping ``id`` from unused workbook activities — NOT by promoting
    them to inline with new INJECT markers.

    Background: PR #2218 (2026-05-21) made ``id`` optional on workbook
    activities (``inject_activity_ids`` only enforces bidirectional
    consistency for activities INTENDED to be inline-injected, and the
    schema rule per ``scripts/build/phases/linear-write.md`` L700 is
    "workbook activity objects should omit `id` entirely"). When a
    writer leaves an activity-with-id WITHOUT a matching
    ``<!-- INJECT_ACTIVITY: act-X -->`` marker, the most-faithful
    interpretation under the new contract is *that activity is workbook
    and the writer over-emitted id* — NOT *that activity is inline and
    the writer forgot the marker*.

    The previous implementation appended INJECT markers for every
    ``unused`` id to ``module.md``. That auto-promoted EVERY workbook
    activity to inline, blowing past the level's
    ``INLINE_MIN..INLINE_MAX`` range and producing the anti-pattern that
    got m20 reverted on 2026-05-23 morning (``inline_n=10 / workbook_n=0``
    in build #14). Empirical reproduction of the same anti-pattern
    across 4 writers on 2026-05-22 night (codex / gemini / deepseek /
    claude builds of a1/my-morning, see session-state handoff for
    forensics).

    The fix: strip ``id`` from each unused activity in
    ``activities.yaml`` so the bidirectional consistency gate passes
    WITHOUT touching ``module.md``, preserving the writer's authored
    INLINE/WORKBOOK split. If the writer *did* mean these as inline
    and forgot markers, the resulting ``inline_n`` shortfall is the
    writer's responsibility to flag via the ``<activity_split_audit>``
    self-audit line — that's where the corrective signal belongs, not
    in a downstream pipeline insert that has no visibility into the
    writer's intent.
    """

    unused = [str(activity_id) for activity_id in gate_report.get("unused", [])]
    if not unused:
        return

    module_dir = module_path.parent
    activities_path = module_dir / "activities.yaml"
    if not activities_path.exists():
        return

    try:
        activities = yaml.safe_load(activities_path.read_text(encoding="utf-8")) or []
    except yaml.YAMLError:
        return
    if not isinstance(activities, list):
        return

    unused_set = {str(activity_id) for activity_id in unused}
    changed = False
    for activity in activities:
        if not isinstance(activity, dict):
            continue
        if str(activity.get("id") or "") in unused_set:
            del activity["id"]
            changed = True
    if changed:
        activities_path.write_text(
            yaml.safe_dump(activities, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )


def _parse_reviewer_fixes(review_text: str) -> list[dict[str, str]]:
    match = re.search(r"<fixes>\s*(.*?)\s*</fixes>", review_text, re.DOTALL)
    if not match:
        return []
    body = match.group(1).strip()
    xml_fixes = _parse_reviewer_fixes_xml(body)
    if xml_fixes:
        return xml_fixes
    try:
        parsed = yaml.safe_load(body)
    except yaml.YAMLError:
        return []
    if not isinstance(parsed, list):
        return []
    fixes: list[dict[str, str]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        if "insert_after" in item and "text" in item:
            fixes.append(
                {
                    "insert_after": str(item["insert_after"]),
                    "text": str(item["text"]),
                }
            )
        elif "find" in item and "replace" in item:
            fixes.append(
                {
                    "find": str(item["find"]),
                    "replace": str(item["replace"]),
                }
            )
    return fixes


def _parse_reviewer_fixes_xml(body: str) -> list[dict[str, str]]:
    if "<fix" not in body:
        return []
    try:
        root = ET.fromstring(f"<fixes>{body}</fixes>")
    except ET.ParseError:
        return []
    fixes: list[dict[str, str]] = []
    for node in root.findall("fix"):
        find_node = node.find("find")
        replace_node = node.find("replace")
        if find_node is not None and replace_node is not None:
            fixes.append(
                {
                    "find": "".join(find_node.itertext()),
                    "replace": "".join(replace_node.itertext()),
                }
            )
            continue
        insert_after_node = node.find("insert_after")
        text_node = node.find("text")
        if insert_after_node is not None and text_node is not None:
            fixes.append(
                {
                    "insert_after": "".join(insert_after_node.itertext()),
                    "text": "".join(text_node.itertext()),
                }
            )
    return fixes


def _emit_reviewer_fix_anchor_unmatched(
    anchor: str,
    replacement: str | None,
    *,
    gate: str | None,
    module_dir: Path | None,
    plan_path: Path | None,
) -> None:
    emit_event(
        "reviewer_fixes_anchor_unmatched",
        **_correction_event_fields(
            gate=gate or "",
            module_dir=module_dir,
            plan_path=plan_path,
        )
        if module_dir is not None and plan_path is not None
        else {"gate": gate},
        anchor_preview=_correction_preview(anchor),
        text_preview=_correction_preview(replacement),
    )


def _emit_reviewer_fix_anchor_normalized_match(
    anchor: str,
    matched: str,
    replacement: str | None,
    *,
    operation: str,
    gate: str | None,
    module_dir: Path | None,
    plan_path: Path | None,
) -> None:
    emit_event(
        "reviewer_fix_anchor_normalized_match",
        **_correction_event_fields(
            gate=gate or "",
            module_dir=module_dir,
            plan_path=plan_path,
        )
        if module_dir is not None and plan_path is not None
        else {"gate": gate},
        operation=operation,
        anchor_preview=_correction_preview(anchor),
        matched_preview=_correction_preview(matched),
        text_preview=_correction_preview(replacement),
    )


def _emit_final_reviewer_unmatched_events(
    unmatched_anchors: frozenset[str],
    fixes: list[dict[str, str]],
    *,
    gate: str,
    module_dir: Path,
    plan_path: Path,
) -> None:
    if not unmatched_anchors:
        return
    for fix in fixes:
        if "insert_after" in fix and "text" in fix:
            anchor = fix["insert_after"]
            replacement = fix["text"]
        else:
            anchor = fix.get("find") or ""
            replacement = fix.get("replace")
        if anchor in unmatched_anchors:
            _emit_reviewer_fix_anchor_unmatched(
                anchor,
                replacement,
                gate=gate,
                module_dir=module_dir,
                plan_path=plan_path,
            )


def _reviewer_fix_whitespace_normalized_view(
    text: str,
) -> tuple[str, tuple[tuple[int, int], ...]]:
    chars: list[str] = []
    spans: list[tuple[int, int]] = []
    index = 0
    while index < len(text):
        if text[index].isspace():
            start = index
            while index < len(text) and text[index].isspace():
                index += 1
            chars.append(" ")
            spans.append((start, index))
            continue
        chars.append(text[index])
        spans.append((index, index + 1))
        index += 1
    return "".join(chars), tuple(spans)


def _strip_reviewer_anchor_stress(anchor: str) -> str:
    decomposed = unicodedata.normalize("NFD", anchor)
    stripped = "".join(char for char in decomposed if char != "\u0301")
    return unicodedata.normalize("NFC", stripped)


def _strip_reviewer_anchor_markdown_wrapper(anchor: str) -> str:
    wrapper_chars = "*_`~"
    start = 0
    end = len(anchor)
    while start < end and anchor[start] in wrapper_chars:
        start += 1
    while end > start and anchor[end - 1] in wrapper_chars:
        end -= 1
    return anchor[start:end]


def _reviewer_anchor_normalized_variants(anchor: str) -> tuple[str, ...]:
    variants: list[str] = []
    candidates = (
        anchor,
        _strip_reviewer_anchor_stress(anchor),
        _strip_reviewer_anchor_markdown_wrapper(anchor),
        _strip_reviewer_anchor_markdown_wrapper(_strip_reviewer_anchor_stress(anchor)),
    )
    for candidate in candidates:
        if candidate not in variants:
            variants.append(candidate)
    return tuple(variants)


def _normalized_reviewer_anchor_offsets(
    normalized_text: str,
    normalized_anchor: str,
) -> list[int]:
    if not normalized_anchor:
        return []
    offsets: list[int] = []
    start = 0
    while True:
        offset = normalized_text.find(normalized_anchor, start)
        if offset < 0:
            return offsets
        offsets.append(offset)
        if len(offsets) > 1:
            return offsets
        start = offset + 1


def _span_from_normalized_reviewer_anchor_offset(
    spans: tuple[tuple[int, int], ...],
    offset: int,
    anchor_length: int,
) -> tuple[int, int]:
    start = spans[offset][0]
    end = spans[offset + anchor_length - 1][1]
    return start, end


def _trim_reviewer_fix_boundary_span(
    text: str,
    span: tuple[int, int],
) -> tuple[int, int] | None:
    start, end = span
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    if start == end:
        return None
    return start, end


def _find_exact_reviewer_fix_span(
    text: str,
    anchor: str,
) -> tuple[int, int] | None:
    if not anchor or all(char.isspace() for char in anchor):
        return None
    offset = text.find(anchor)
    if offset < 0:
        return None
    return offset, offset + len(anchor)


def _find_unique_reviewer_fix_normalized_span(
    text: str,
    anchor: str,
) -> tuple[int, int] | None:
    normalized_text, spans = _reviewer_fix_whitespace_normalized_view(text)
    normalized_anchor, _anchor_spans = _reviewer_fix_whitespace_normalized_view(anchor)
    offsets = _normalized_reviewer_anchor_offsets(normalized_text, normalized_anchor)
    if len(offsets) == 1:
        return _trim_reviewer_fix_boundary_span(
            text,
            _span_from_normalized_reviewer_anchor_offset(
                spans,
                offsets[0],
                len(normalized_anchor),
            ),
        )
    if len(offsets) > 1:
        return None

    matched_spans: set[tuple[int, int]] = set()
    ambiguous = False
    seen_normalized_anchors = {normalized_anchor}
    for variant in _reviewer_anchor_normalized_variants(anchor)[1:]:
        variant_anchor, _variant_spans = _reviewer_fix_whitespace_normalized_view(
            variant
        )
        if not variant_anchor or variant_anchor in seen_normalized_anchors:
            continue
        seen_normalized_anchors.add(variant_anchor)
        variant_offsets = _normalized_reviewer_anchor_offsets(
            normalized_text,
            variant_anchor,
        )
        if len(variant_offsets) == 1:
            if span := _trim_reviewer_fix_boundary_span(
                text,
                _span_from_normalized_reviewer_anchor_offset(
                    spans,
                    variant_offsets[0],
                    len(variant_anchor),
                ),
            ):
                matched_spans.add(span)
        elif len(variant_offsets) > 1:
            ambiguous = True
    if ambiguous or len(matched_spans) != 1:
        return None
    return next(iter(matched_spans))


def _find_reviewer_fix_span(
    text: str,
    anchor: str,
) -> tuple[int, int] | None:
    return _find_exact_reviewer_fix_span(
        text,
        anchor,
    ) or _find_unique_reviewer_fix_normalized_span(text, anchor)


def _apply_reviewer_fixes(
    text: str,
    fixes: list[dict[str, str]],
    *,
    gate: str | None = None,
    module_dir: Path | None = None,
    plan_path: Path | None = None,
    emit_unmatched_events: bool = True,
) -> ReviewerFixApplyResult:
    updated = text
    unmatched_anchors: set[str] = set()
    for fix in fixes:
        if "insert_after" in fix and "text" in fix:
            anchor = fix["insert_after"]
            if span := _find_exact_reviewer_fix_span(updated, anchor):
                _, end = span
                updated = updated[:end] + fix["text"] + updated[end:]
            elif span := _find_unique_reviewer_fix_normalized_span(updated, anchor):
                start, end = span
                matched = updated[start:end]
                updated = updated[:end] + fix["text"] + updated[end:]
                _emit_reviewer_fix_anchor_normalized_match(
                    anchor,
                    matched,
                    fix["text"],
                    operation="insert_after",
                    gate=gate,
                    module_dir=module_dir,
                    plan_path=plan_path,
                )
            else:
                unmatched_anchors.add(anchor)
                if emit_unmatched_events:
                    _emit_reviewer_fix_anchor_unmatched(
                        anchor,
                        fix["text"],
                        gate=gate,
                        module_dir=module_dir,
                        plan_path=plan_path,
                    )
            continue
        find = fix.get("find")
        replace = fix.get("replace")
        if find and replace is not None and (
            span := _find_exact_reviewer_fix_span(updated, find)
        ):
            start, end = span
            updated = updated[:start] + replace + updated[end:]
        elif find and replace is not None and (
            span := _find_unique_reviewer_fix_normalized_span(updated, find)
        ):
            start, end = span
            matched = updated[start:end]
            updated = updated[:start] + replace + updated[end:]
            _emit_reviewer_fix_anchor_normalized_match(
                find,
                matched,
                replace,
                operation="replace",
                gate=gate,
                module_dir=module_dir,
                plan_path=plan_path,
            )
        elif find:
            unmatched_anchors.add(find)
            if emit_unmatched_events:
                _emit_reviewer_fix_anchor_unmatched(
                    find,
                    replace,
                    gate=gate,
                    module_dir=module_dir,
                    plan_path=plan_path,
                )
    return ReviewerFixApplyResult(updated, frozenset(unmatched_anchors))


def _previously_passing_regressions(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> list[str]:
    before_gates = before.get("gates")
    after_gates = after.get("gates")
    if not isinstance(before_gates, Mapping) or not isinstance(after_gates, Mapping):
        return []
    ordered_gate_set = set(PYTHON_QG_GATE_ORDER)
    all_gate_names = (set(before_gates) | set(after_gates)) - PYTHON_QG_META_GATES
    ordered_gate_names = [gate for gate in PYTHON_QG_GATE_ORDER if gate in all_gate_names]
    ordered_gate_names.extend(
        sorted(gate for gate in all_gate_names if gate not in ordered_gate_set)
    )
    regressions = []
    for gate in ordered_gate_names:
        before_gate = before_gates.get(gate)
        after_gate = after_gates.get(gate)
        if (
            isinstance(before_gate, Mapping)
            and isinstance(after_gate, Mapping)
            and before_gate.get("passed") is True
            and after_gate.get("passed") is False
        ):
            regressions.append(gate)
    return regressions


def generate_dictionary_candidates(
    gate: str,
    gate_report: Mapping[str, Any],
    *,
    qg_report: Mapping[str, Any] | None = None,
    dictionary_lookup_fn: Callable[[str, str], list[str | Mapping[str, str]]] | None = None,
) -> tuple[CorrectionCandidate, ...]:
    """Generate deterministic candidate replacements before reviewer fixes."""
    originals: list[str] = []
    if gate == "vesum_verified":
        originals.extend(str(item) for item in gate_report.get("missing", []))
    elif gate == "citations_resolve":
        originals.extend(str(item) for item in gate_report.get("unknown", []))
    else:
        detections = gate_report.get("detections", [])
        if isinstance(detections, list):
            originals.extend(
                str(item.get("text")) for item in detections if isinstance(item, Mapping) and item.get("text")
            )

    candidates: list[CorrectionCandidate] = []
    for original in sorted(set(originals)):
        if dictionary_lookup_fn is not None:
            for item in dictionary_lookup_fn(gate, original):
                if isinstance(item, Mapping):
                    replacement = str(item.get("replacement") or item.get("text") or "")
                    source = str(item.get("source") or "pipeline lookup")
                else:
                    replacement = str(item)
                    source = "pipeline lookup"
                if replacement:
                    candidates.append(CorrectionCandidate(original, replacement, source, gate))
            continue
        if gate == "citations_resolve" and qg_report is not None:
            candidates.extend(_citation_candidates(original, qg_report))
            continue
        replacement = DICTIONARY_REPLACEMENTS.get(original.lower())
        if replacement is not None:
            candidates.append(
                CorrectionCandidate(
                    original=original,
                    replacement=replacement[0],
                    source=replacement[1],
                    gate=gate,
                )
            )
    return tuple(candidates)


def _citation_candidates(
    unknown: str,
    qg_report: Mapping[str, Any],
) -> tuple[CorrectionCandidate, ...]:
    plan_refs = qg_report.get("plan_references", [])
    candidates = []
    if isinstance(plan_refs, list):
        for ref in plan_refs:
            if isinstance(ref, Mapping) and ref.get("title"):
                candidates.append(
                    CorrectionCandidate(
                        original=unknown,
                        replacement=str(ref["title"]),
                        source="sources registry / plan references",
                        gate="citations_resolve",
                    )
                )
    return tuple(candidates)


def run_python_qg(
    module_dir: Path,
    plan_path: Path,
    *,
    verify_words_fn: Callable[[list[str]], dict[str, list[dict[str, Any]]]] | None = None,
    heritage_lookup_fn: Callable[[str], list[dict[str, Any]]] | None = None,
    gate_observer: Callable[[str], None] | None = None,
    ignored_vesum_missing_surfaces: Collection[str] = (),
    event_sink: Callable[..., None] | None = None,
    resource_liveness_fn: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    """Run deterministic Phase 4 quality gates for one module directory.

    ``resource_liveness_fn`` (optional): a URL -> bool liveness checker. Only
    invoked during static re-verification (when build-time writer telemetry is
    absent) to let ``resources_search_attempted`` substitute proof-that-the-
    resources-are-real for the missing search telemetry. Left ``None`` at build
    time, so builds never perform network liveness checks.
    """
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

    gates: dict[str, Any] = {}
    level = str(plan.get("level") or "").lower()
    slug = str(plan.get("slug") or "")

    def record(name: str, report: dict[str, Any]) -> None:
        if gate_observer is not None:
            gate_observer(name)
        if report.get("passed") is False:
            rule_ids = _writer_rule_ids_for_gate_failure(name, report)
            if rule_ids:
                report = dict(report)
                report["rule_ids"] = rule_ids
                evidence = _writer_rule_evidence_for_gate(name, report)
                for rule_id in rule_ids:
                    _emit_writer_rule_fired(
                        event_sink,
                        rule_id=rule_id,
                        level=level,
                        slug=slug,
                        gate=name,
                        evidence=evidence,
                    )
        gates[name] = report

    record("activity_schema", _activity_schema_gate(activities))
    if gates["activity_schema"].get("passed") is False:
        gates["passed"] = False
        return _python_qg_report(plan, gates)

    record("quiz_translate_explanations", _quiz_translate_explanation_gate(activities))
    record("word_count", _word_count_gate(module_text, int(plan["word_target"])))
    record("plan_sections", _section_gate(module_text, plan))
    record("formatting_standards", _formatting_standards_gate(module_text))
    record("scaffolding_leak", _scaffolding_leak_gate(module_text))
    record(
        "vesum_verified",
        _vesum_gate(
            module_text=module_text,
            activities=activities,
            vocabulary=vocabulary,
            resources=resources,
            verify_words_fn=verify_words_fn,
            level=level,
            ignored_missing_surfaces=ignored_vesum_missing_surfaces,
            plan_vesum_exemptions=plan.get("vesum_exemptions"),
        ),
    )
    record(
        "bad_form_heritage",
        _bad_form_heritage_gate(
            module_text=module_text,
            activities=activities,
            vocabulary=vocabulary,
            resources=resources,
            heritage_lookup_fn=heritage_lookup_fn,
        ),
    )
    record(
        "citations_resolve",
        _citation_gate(resources, plan, module_text=module_text, level=level),
    )
    record("plan_reference_match", _plan_reference_match_gate(resources, plan))
    wiki_manifest: dict[str, Any] | None = None
    with contextlib.suppress(LinearPipelineError, ValueError):
        wiki_manifest = build_wiki_manifest_data(plan_path, plan=plan)
    record("resource_coverage", _resource_coverage_gate(resources, plan, wiki_manifest))
    record(
        "reading_coverage",
        _reading_coverage_gate(
            module_text,
            plan,
            readings_dir=PROJECT_ROOT / "site" / "src" / "content" / "readings",
        ),
    )
    record(
        "resources_url_resolve",
        _resources_url_resolve_gate(
            resources,
            level=level,
            resource_liveness_fn=resource_liveness_fn,
        ),
    )
    # record("textbook_grounding", _textbook_grounding_gate(module_text, plan, module_dir))
    record(
        "chunk_context_for_all_refs",
        _chunk_context_for_all_refs_gate(plan, _load_writer_tool_calls(module_dir), module_dir),
    )
    record(
        "published_quote_for_publishable_refs",
        _published_quote_for_publishable_refs_gate(module_text, plan, module_dir),
    )
    record(
        "textbook_quote_fidelity",
        _textbook_quote_fidelity_gate(module_text, level=level, module_slug=slug),
    )
    telemetry_present = _writer_tool_call_telemetry_present(module_dir)
    record(
        "resources_search_attempted",
        _resources_search_attempted_gate(
            _load_writer_tool_calls(module_dir),
            plan=plan,
            resource_coverage=gates.get("resource_coverage"),
            telemetry_present=telemetry_present,
            resource_liveness=(
                _verify_resources_live(resources, url_live_fn=resource_liveness_fn)
                if (resource_liveness_fn is not None and not telemetry_present)
                else None
            ),
        ),
    )
    record("immersion_advisory", _advisory_immersion_pct(module_text, plan))
    record("l2_exposure_floor", _l2_exposure_floor_gate(module_text, plan))
    record(
        "long_uk_ceiling",
        _long_uk_ceiling_gate(
            module_text,
            plan,
            grounding_evidence=gates.get("published_quote_for_publishable_refs"),
        ),
    )
    record("component_density", _component_density_gate(module_text, plan))
    record("archetype_fit", _archetype_fit_gate(module_text, plan, activities))
    record("inject_activity_ids", _inject_activity_gate(module_text, activities, plan, module_dir))
    record(
        "activity_types",
        _activity_type_gate(
            activities,
            str(plan["level"]),
            int(plan["sequence"]),
            str(plan["slug"]),
        ),
    )
    record("ai_slop_clean", _ai_slop_gate(prose_text))
    record(
        "surface_policy",
        scan_module_surface(module_dir, level=str(plan["level"])),
    )
    record("russianisms_strict", _russianisms_strict_gate(text_for_quality))
    record("register_consistency", _register_consistency_gate(module_text, plan))
    record("engagement_floor", _engagement_floor_gate(module_text, plan))
    record("component_props", _component_prop_gate(activities))
    for gate_name, gate_report in _quality_fields(text_for_quality).items():
        record(gate_name, gate_report)
    gates["previously_passed_regression"] = {"passed": True, "regressions": []}
    gates["mdx_render"] = {
        "passed": None,
        "message": (
            "deferred — no assembled MDX at python_qg time; run the standalone "
            "render gate after assemble_mdx (run_mdx_render_gate / "
            "scripts.build.mdx_render_gate / verify_shippable.py). #3137"
        ),
    }
    gates["passed"] = all(
        gate.get("passed") is True for key, gate in gates.items() if isinstance(gate, dict) and key != "mdx_render"
    )
    return _python_qg_report(plan, gates)


def _python_qg_report(
    plan: Mapping[str, Any],
    gates: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "module": plan["module"],
        "level": plan["level"],
        "slug": plan["slug"],
        "pipeline": "linear-phase-4",
        "plan_references": plan.get("references", []),
        "gates": dict(gates),
    }


def _archetype_fit_gate(
    module_text: str,
    plan: Mapping[str, Any],
    activities: list[dict[str, Any]],
) -> dict[str, Any]:
    from scripts.audit.checks.contract_compliance import check_archetype_fit

    return check_archetype_fit(
        module_text,
        {
            "module": {
                "level": str(plan.get("level") or "").lower(),
                "module_num": int(plan.get("sequence") or 0),
                "slug": str(plan.get("slug") or ""),
            }
        },
        activities=activities,
    )


def assemble_mdx(module_dir: Path, output_path: Path, plan_path: Path) -> str:
    """Assemble the 4-tab Site MDX file from authoring artifacts."""
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
        build_status="validated",
    )
    mdx = mdx.replace("\n{/**/}\n", "\n")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # fmt: off
    output_path.write_text(mdx, encoding="utf-8")  # codeql[py/clear-text-storage-sensitive-data] - .mdx curriculum content, never sensitive data
    # fmt: on
    return mdx


def run_mdx_render_gate(mdx: str | Path) -> dict[str, Any]:
    """Standalone ``mdx_render`` gate over assembled MDX (text or path).

    The ``mdx_render`` gate is deferred inside ``run_python_qg`` (no assembled
    MDX exists yet at that stage) and must run as its own post-assemble step so
    it is never silently skipped — including when ``python_qg`` failed, so a
    broken render is still surfaced rather than masked by an earlier gate (#3137).
    """
    from scripts.build.mdx_render_gate import check_mdx_render, check_mdx_render_path

    if isinstance(mdx, Path):
        return check_mdx_render_path(mdx)
    text = str(mdx)
    # Treat a short, single-line value that points at an existing file as a path.
    if "\n" not in text and len(text) < 4096 and Path(text).exists():
        return check_mdx_render_path(text)
    return check_mdx_render(text)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_correction_artifact(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _artifact_name_from_text(text: str) -> str | None:
    for artifact in WRITER_ARTIFACTS:
        if re.search(rf"(?<![\w.-]){re.escape(artifact)}(?![\w.-])", text):
            return artifact
    return None


def _artifact_name_from_label_line(line: str) -> str | None:
    """Return the artifact name if `line` is a standalone label line.

    This is intentionally narrower than `_artifact_name_from_text`, which
    finds artifact names embedded in fence info strings like
    `markdown file=module.md`. Preceding labels should only count when the
    artifact name is the line's dominant content, not when it appears in
    prose such as `<plan_reasoning>` implementation-map rows.
    """
    match = _LABEL_LINE_RE.match(line)
    return match.group("name") if match else None


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

    _normalize_writer_json_artifact(artifact, parsed)
    _validate_writer_json_artifact(artifact, parsed)
    return yaml.safe_dump(parsed, allow_unicode=True, sort_keys=False)


def _normalize_writer_json_artifact(artifact: str, parsed: Any) -> None:
    """Normalize narrow, lossless legacy writer shapes before validation."""
    if artifact != "activities.yaml" or not isinstance(parsed, list):
        return
    for activity in parsed:
        if isinstance(activity, dict) and activity.get("type") == "group-sort":
            _normalize_group_sort_activity(activity)
        if isinstance(activity, dict) and activity.get("type") == "letter-grid":
            _normalize_letter_grid_activity(activity)
        if isinstance(activity, dict) and activity.get("type") == "count-syllables":
            _normalize_count_syllables_activity(activity)
        if isinstance(activity, dict) and activity.get("type") == "watch-and-repeat":
            _normalize_watch_and_repeat_activity(activity)


def _group_sort_label(group: Mapping[str, Any]) -> str | None:
    for field in ("label", "name", "title", "key", "id"):
        value = group.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _group_sort_item_text(item: Mapping[str, Any]) -> str | None:
    for field in ("word", "text", "label", "item", "value"):
        value = item.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _normalize_group_sort_activity(activity: dict[str, Any]) -> None:
    """Convert keyed top-level group-sort items into nested group items.

    Writers often use an assessment-style shape:
    ``groups: [{name, key}], items: [{word, group}]``. The authoring format
    consumed by the renderer keeps sortable strings inside each group:
    ``groups: [{label, items}]``. Convert only when every top-level item can
    be assigned unambiguously; otherwise leave validation to fail loud.
    """
    groups = activity.get("groups")
    if not isinstance(groups, list) or not groups:
        return

    normalized_groups: list[dict[str, Any]] = []
    aliases: dict[str, dict[str, Any]] = {}
    for group in groups:
        if not isinstance(group, Mapping):
            return
        label = _group_sort_label(group)
        if label is None:
            return
        raw_items = group.get("items", [])
        if raw_items is None:
            raw_items = []
        if not isinstance(raw_items, list):
            return
        normalized = {
            "label": label,
            "items": [str(item).strip() for item in raw_items if str(item).strip()],
        }
        normalized_groups.append(normalized)
        for field in ("key", "id", "label", "name", "title"):
            value = group.get(field)
            if isinstance(value, str) and value.strip():
                aliases[value.strip()] = normalized

    top_level_items = activity.get("items")
    if top_level_items is not None:
        if not isinstance(top_level_items, list):
            return
        for item in top_level_items:
            if not isinstance(item, Mapping):
                return
            group_key = item.get("group") or item.get("category") or item.get("group_key")
            text = _group_sort_item_text(item)
            if not isinstance(group_key, str) or not group_key.strip() or text is None:
                return
            target = aliases.get(group_key.strip())
            if target is None:
                return
            target["items"].append(text)
        activity.pop("items", None)

    activity["groups"] = normalized_groups


_LETTER_GRID_EMOJI_BY_KEY_WORD: Mapping[str, str] = {
    "ананас": "🍍",
    "банан": "🍌",
    "вода": "💧",
    "гора": "⛰️",
    "ґудзик": "🔘",
    "дім": "🏠",
    "екран": "🖥️",
    "єнот": "🦝",
    "жук": "🪲",
    "зуб": "🦷",
    "сир": "🧀",
    "ім'я": "🪪",
    "їжак": "🦔",
    "йогурт": "🥛",
    "кіт": "🐈",
    "лимон": "🍋",
    "мама": "👩",
    "ніс": "👃",
    "око": "👁️",
    "пес": "🐕",
    "рука": "✋",
    "сон": "🌙",
    "тато": "👨",
    "урок": "📚",
    "фото": "📷",
    "хата": "🏠",
    "цукор": "🍬",
    "час": "🕒",
    "школа": "🏫",
    "щука": "🐟",
    "день": "📅",
    "юшка": "🥣",
    "яблуко": "🍎",
}


def _normalize_letter_grid_activity(activity: dict[str, Any]) -> None:
    """Convert common letter-grid aliases into renderer-ready fields."""
    letters = activity.get("letters")
    if not isinstance(letters, list) or not letters:
        return

    normalized_letters: list[dict[str, Any]] = []
    for entry in letters:
        if not isinstance(entry, Mapping):
            return
        upper = entry.get("upper") or entry.get("letter")
        key_word = entry.get("key_word") or entry.get("word") or entry.get("example")
        if not isinstance(upper, str) or not upper.strip():
            return
        if not isinstance(key_word, str) or not key_word.strip():
            return
        lower = entry.get("lower")
        if not isinstance(lower, str) or not lower.strip():
            lower = upper.casefold()
        emoji = entry.get("emoji")
        if not isinstance(emoji, str) or not emoji.strip():
            emoji = _LETTER_GRID_EMOJI_BY_KEY_WORD.get(key_word.casefold(), "🔤")

        normalized = {
            "upper": upper.strip(),
            "lower": lower.strip(),
            "emoji": emoji.strip(),
            "key_word": key_word.strip(),
        }
        sound_type = entry.get("sound_type") or entry.get("kind")
        if isinstance(sound_type, str) and sound_type.strip():
            normalized["sound_type"] = sound_type.strip()
        note = entry.get("note") or entry.get("sound")
        if isinstance(note, str) and note.strip():
            normalized["note"] = note.strip()
        normalized_letters.append(normalized)

    activity["letters"] = normalized_letters


def _normalize_count_syllables_activity(activity: dict[str, Any]) -> None:
    """Convert count-syllables item `answer` aliases into `correct`."""
    items = activity.get("items")
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, dict):
            return
        if "correct" not in item and "answer" in item:
            item["correct"] = item.pop("answer")


def _normalize_watch_and_repeat_activity(activity: dict[str, Any]) -> None:
    """Convert watch-and-repeat item `url` aliases into renderer `video`."""
    items = activity.get("items")
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, dict):
            return
        if "video" not in item and "url" in item:
            item["video"] = item.pop("url")


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

    static_allowed_fields = set(schema.required_item_fields) | schema.optional_item_fields
    required_field_names = set(schema.required_item_fields)

    for index, item in enumerate(parsed, start=1):
        if not isinstance(item, dict):
            raise LinearPipelineError(
                f"{artifact} schema validation failed: item {index} must be object, got {type(item).__name__}"
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
        if artifact == "resources.yaml":
            role = str(item.get("role") or "").strip()
            url = str(item.get("url") or "").strip()
            normalized_url = url.lstrip("./")
            if role not in RESOURCE_ROLES:
                raise LinearPipelineError(
                    f"{artifact} schema validation failed: item {index} "
                    f"has invalid role {role!r}; allowed: {sorted(RESOURCE_ROLES)}"
                )
            if role != "textbook" and not url:
                raise LinearPipelineError(
                    f"{artifact} schema validation failed: item {index} role {role!r} requires url"
                )
            if normalized_url.startswith(INTERNAL_RESOURCE_URL_PREFIXES):
                raise LinearPipelineError(
                    f"{artifact} schema validation failed: item {index} has internal "
                    f"AI-facing resource url {url!r}; resources.yaml must contain "
                    "student-facing sources only (on-site primary text belongs in a "
                    ":::primary-reading block, reading-task links use public allowlisted URLs)"
                )


# Per-activity-type allowed top-level fields in the **authoring YAML
# wire format** (what `ActivityParser._parse_activity` in
# `scripts/yaml_activities.py` consumes, what writers are told to emit
# in `agents_extensions/shared/quick-ref/ACTIVITY-SCHEMAS.md` and the per-level
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
_UNIVERSAL_AUTHORING_FIELDS: frozenset[str] = frozenset(
    {
        "id",
        "type",
        "title",
        "instruction",
        "notes",
    }
)


def _activity(*type_specific: str) -> frozenset[str]:
    """Helper: per-type set = universal fields ∪ supplied type-specific extras."""
    return _UNIVERSAL_AUTHORING_FIELDS | frozenset(type_specific)


_ACTIVITY_AUTHORING_FIELDS: dict[str, frozenset[str]] = {
    # Core L2 question/practice types — items-bearing.
    "quiz": _activity("items"),
    "select": _activity("items"),
    "true-false": _activity("items"),
    "fill-in": _activity("items"),
    "cloze": _activity("passage", "text", "blanks"),
    "match-up": _activity("pairs"),
    "group-sort": _activity("groups"),
    "unjumble": _activity("items"),
    "error-correction": _activity("items"),
    "mark-the-words": _activity("text", "answers"),
    "translate": _activity("items"),
    "anagram": _activity("items"),
    # Pre-literacy (A1 Cyrillic).
    "classify": _activity("categories"),
    "image-to-letter": _activity("items"),
    "watch-and-repeat": _activity("items"),
    # Pre-literacy types declared in `docs/lesson-schema.yaml` but with
    # no `_parse_*` method in `ActivityParser` (silently dropped at
    # parse time). Listed here to preserve the pre-#1624 behavior of
    # the old `lesson-schema.yaml`-sourced loader, which accepted them.
    "count-syllables": _activity("items", "maxCount"),
    "divide-words": _activity("items"),
    "highlight-morphemes": _activity("items", "text"),
    "letter-grid": _activity("letters"),
    "observe": _activity("examples", "prompt"),
    "odd-one-out": _activity("items"),
    "order": _activity("items", "correct_order"),
    "pick-syllables": _activity("syllables", "category", "correctIndices", "explanation"),
    # Seminar / B2+ analytical types. The fields below cover both
    # the canonical and legacy authoring shapes that `ActivityParser`
    # accepts (e.g. `target_text` / `questions` / `model_answers` is
    # canonical for critical-analysis, `context` / `question` /
    # `model_answer` is legacy — both are still read).
    "reading": _activity("text", "passage", "context", "source", "resource", "tasks", "questions"),
    "essay-response": _activity(
        "source_reading", "prompt", "min_words", "model_answer", "rubric", "peer_review_guidelines"
    ),
    "critical-analysis": _activity(
        "source_reading",
        "target_text",
        "questions",
        "model_answers",
        "context",
        "question",
        "model_answer",
        "focus_points",
    ),
    "comparative-study": _activity(
        "source_reading", "items_to_compare", "criteria", "prompt", "model_answer", "source_a", "source_b", "task"
    ),
    # FOLK text-layer activity families (#42-#45).
    "ritual-sequencing": _activity("steps", "items", "correct_order", "model_answer"),
    "variant-comparison": _activity("variants", "features", "prompt", "model_answer"),
    "motif-formula": _activity("passage", "text", "formulas", "answers", "prompt", "model_answer"),
    "performance": _activity("prompt", "fragment", "self_check", "self_checklist", "show_record_button", "model_answer"),
    "authorial-intent": _activity("source_reading", "text_excerpt", "prompt", "techniques_to_identify", "model_answer"),
    # ISTORIO / HIST.
    "source-evaluation": _activity(
        "source_text", "source_metadata", "evaluation_criteria", "guiding_questions", "model_evaluation"
    ),
    "debate": _activity("debate_question", "historical_context", "positions", "analysis_tasks", "model_analysis"),
    # OES / RUTH (historical-Ukrainian linguistic types).
    "etymology-trace": _activity("items"),
    "grammar-identify": _activity("items"),
    "transcription": _activity("original", "answer", "hints"),
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


def _activity_item_schema_whitelist() -> dict[str, frozenset[str]]:
    """Return per-activity-type allowed item fields in authoring YAML.

    V1 is intentionally narrow: `error-correction` is the only strict
    item-level schema needed for #2018. Its required fields come directly from
    `ActivityParser._parse_error_correction`, which indexes `sentence` and
    `error`, while `answer`/`correction`/`options`/`explanation` are optional
    parser-supported fields.
    """
    return _ACTIVITY_ITEM_AUTHORING_FIELDS


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
    # FOLK text-layer activity families.
    "ritual-sequencing": {
        "correctOrder": "correct_order",
        "modelAnswer": "model_answer",
    },
    "variant-comparison": {
        "modelAnswer": "model_answer",
    },
    "motif-formula": {
        "modelAnswer": "model_answer",
    },
    "performance": {
        "selfCheck": "self_check",
        "showRecordButton": "show_record_button",
        "modelAnswer": "model_answer",
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
_COMPONENT_PROP_GATE_JSX_ONLY_PROPS: frozenset[str] = frozenset(
    {
        "children",
    }
)


def _strip_outer_code_fence(text: str) -> str:
    stripped = text.strip()
    match = re.match(r"^```(?:json|yaml|yml)?\s*\n(?P<body>.*)\n```\s*$", stripped, re.DOTALL)
    if match:
        return match.group("body").strip()
    return stripped


# Fenced-block + bare-JSON-object extractor used when the LLM wraps the
# expected JSON/YAML payload in prose preamble/epilogue (a common pattern —
# "I have verified all 18 obligations. Here is the structured output:" + ```json
# {...} ``` + closing remarks). Without these fallbacks, ``json.loads`` and
# ``yaml.safe_load`` both fail on the prose, masking the actual reviewer
# output. Build #10 (a1/my-morning, 2026-05-21) exposed this: codex-tools
# emitted a prose preamble, the gate raised
# ``LLM QG response must be a JSON/YAML mapping`` with no way to recover the
# structured payload from inside the response. Order matters: try a fenced
# block first (most LLMs use ``` ```json `` or `` ```yaml ``); then try to
# extract the first balanced ``{...}`` object span; finally fall through to
# the whole-string parse so existing well-formed responses are unchanged.
_FENCED_BLOCK_RE = re.compile(
    r"```(?:json|yaml|yml)?\s*\n(?P<body>.*?)\n```",
    re.DOTALL,
)


def _extract_first_fenced_block(text: str) -> str | None:
    match = _FENCED_BLOCK_RE.search(text)
    if match:
        return match.group("body").strip()
    return None


def _extract_first_balanced_json_object(text: str) -> str | None:
    """Return the first top-level ``{...}`` span with balanced braces.

    Naive bracket-counter that ignores braces inside double-quoted strings
    (so ``"key": "}{"`` does not break the count) and respects backslash
    escapes inside those strings. Returns None if no balanced object is found.
    Used as a last-resort extractor for prose-wrapped reviewer responses; we
    don't try to handle arrays — every reviewer-response schema is a top-level
    mapping.
    """
    depth = 0
    start = -1
    in_string = False
    escape = False
    for idx, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            if depth == 0:
                start = idx
            depth += 1
            continue
        if ch == "}":
            if depth == 0:
                continue
            depth -= 1
            if depth == 0 and start >= 0:
                return text[start : idx + 1]
    return None


def _parse_json_or_yaml_mapping(text: str) -> dict[str, Any]:
    candidates: list[str] = []
    body = _strip_outer_code_fence(text)
    candidates.append(body)
    fenced = _extract_first_fenced_block(text)
    if fenced is not None and fenced != body:
        candidates.append(fenced)
    bare_object = _extract_first_balanced_json_object(text)
    if bare_object is not None and bare_object not in candidates:
        candidates.append(bare_object)

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            try:
                parsed = yaml.safe_load(candidate)
            except yaml.YAMLError as yaml_exc:
                last_error = yaml_exc
                continue
        if isinstance(parsed, dict):
            return parsed
    if last_error is not None:
        raise LinearPipelineError("LLM QG response must be a JSON/YAML mapping") from last_error
    raise LinearPipelineError("LLM QG response must be a JSON/YAML mapping")


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


def _required_vocabulary_for_contract(plan: Mapping[str, Any]) -> list[Any]:
    """Extract required-vocabulary list, tolerating both plan-schema shapes.

    Two shapes exist in the wild (discovered 2026-05-20 seminar smoke build):

    * CORE plans + some LIT plans: ``vocabulary_hints`` is a dict with
      ``required`` / ``optional`` / ``recommended`` keys, each a list.
    * Most LIT/BIO seminar plans + ``required_vocab`` callers: a bare list
      of ``{word, pos, definition}`` entries.

    ``_vocabulary_lemmas`` already handles both shapes (line ~895); this
    helper applies the same pattern to ``_contract_yaml`` so seminar
    builds don't crash with ``'list' object has no attribute 'get'``.
    Follow-up: schema unification (see issue tracking the parallel
    ``title:`` gap).
    """
    vh = plan.get("vocabulary_hints")
    if isinstance(vh, dict):
        required = vh.get("required")
        return list(required) if isinstance(required, list) else []
    if isinstance(vh, list):
        return list(vh)
    return []


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
            }
            for section in plan.get("content_outline", [])
        ],
        "vocabulary_required": plan.get("vocabulary_hints", {}).get("required", [])
        if isinstance(plan.get("vocabulary_hints"), dict)
        else plan.get("vocabulary_hints", []),
        "vocabulary_optional": plan.get("vocabulary_hints", {}).get("optional", [])
        if isinstance(plan.get("vocabulary_hints"), dict)
        else [],
        "source_note": "Full plan below is authoritative for points, activity hints, vocabulary, and references.",
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


def _activity_list_from_loaded_data(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and "activities" in data:
        raise LinearPipelineError("activities.yaml must be a bare list, not activities:")
    if isinstance(data, dict) and ("inline" in data or "workbook" in data):
        unexpected_keys = sorted(set(data) - {"version", "module", "level", "inline", "workbook"})
        if unexpected_keys:
            raise LinearPipelineError(
                f"activities.yaml inline/workbook object has unexpected keys: {unexpected_keys}"
            )
        activities: list[dict[str, Any]] = []
        for section in ("inline", "workbook"):
            section_data = data.get(section, [])
            if section_data is None:
                continue
            if not isinstance(section_data, list):
                raise LinearPipelineError(f"activities.yaml {section}: must be a list")
            activities.extend(section_data)
        data = activities
    if not isinstance(data, list):
        raise LinearPipelineError("activities.yaml must be a bare list at root or inline/workbook object")
    if not all(isinstance(item, dict) for item in data):
        raise LinearPipelineError("Every activity must be a mapping")
    return data


def _load_bare_activity_list(path: Path) -> list[dict[str, Any]]:
    return _activity_list_from_loaded_data(load_yaml(path))


def _activity_schema_gate(activities: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate strict item-level authoring schemas before content gates run."""
    item_fields_by_type = _activity_item_schema_whitelist()
    violations: list[dict[str, Any]] = []
    checked = 0

    for activity_index, activity in enumerate(activities, start=1):
        if not isinstance(activity, Mapping):
            continue
        activity_type = str(activity.get("type") or "")
        activity_id = str(activity.get("id") or f"#{activity_index}")
        if (
            activity_type == "performance"
            and "self_check" in activity
            and not isinstance(activity.get("self_check"), list)
        ):
            violations.append(
                _activity_schema_activity_field_type_violation(
                    activity_id=activity_id,
                    activity_index=activity_index,
                    activity_type=activity_type,
                    field="self_check",
                    expected_type="list",
                    actual_type=type(activity.get("self_check")).__name__,
                )
            )
        allowed_fields = item_fields_by_type.get(activity_type)
        if allowed_fields is None:
            continue
        aliases = _ACTIVITY_ITEM_FORBIDDEN_ALIASES.get(activity_type, {})
        required_fields = _ACTIVITY_ITEM_REQUIRED_FIELDS.get(activity_type, frozenset())
        items = activity.get("items", [])
        if not isinstance(items, list):
            continue

        for item_index, item in enumerate(items, start=1):
            if not isinstance(item, Mapping):
                continue
            checked += 1
            item_fields = {str(field) for field in item}
            aliased_required = {
                expected for field in item_fields if (expected := aliases.get(field)) in required_fields
            }

            for field in sorted(item_fields):
                if field in allowed_fields:
                    continue
                expected = aliases.get(field)
                violations.append(
                    _activity_schema_violation(
                        activity_id=activity_id,
                        activity_index=activity_index,
                        item_index=item_index,
                        activity_type=activity_type,
                        offending_field=field,
                        expected_field=expected,
                    )
                )

            for required_field in sorted(required_fields - item_fields - aliased_required):
                violations.append(
                    _activity_schema_violation(
                        activity_id=activity_id,
                        activity_index=activity_index,
                        item_index=item_index,
                        activity_type=activity_type,
                        offending_field=None,
                        expected_field=required_field,
                    )
                )

    report = {
        "passed": not violations,
        "checked": checked,
        "violations": violations,
    }
    if violations:
        report["message"] = _format_activity_schema_diagnostic(violations)
    return report


def _activity_schema_violation(
    *,
    activity_id: str,
    activity_index: int,
    item_index: int,
    activity_type: str,
    offending_field: str | None,
    expected_field: str | None,
) -> dict[str, Any]:
    if offending_field is None:
        purpose = _ACTIVITY_ITEM_FIELD_PURPOSES.get(expected_field or "", "this item")
        message = f"{activity_type} items must include '{expected_field}:' for {purpose}"
    elif expected_field is not None:
        purpose = _ACTIVITY_ITEM_FIELD_PURPOSES.get(expected_field, "this value")
        message = f"{activity_type} items must use '{expected_field}:' for {purpose}, not '{offending_field}:'"
    else:
        message = f"{activity_type} items do not allow field '{offending_field}:'"

    return {
        "activity_id": activity_id,
        "activity_index": activity_index,
        "item_index": item_index,
        "activity_type": activity_type,
        "offending_field": offending_field,
        "expected_field": expected_field,
        "message": message,
    }


def _activity_schema_activity_field_type_violation(
    *,
    activity_id: str,
    activity_index: int,
    activity_type: str,
    field: str,
    expected_type: str,
    actual_type: str,
) -> dict[str, Any]:
    message = f"{activity_type} activity '{field}' must be a {expected_type}, not a {actual_type}"
    return {
        "activity_id": activity_id,
        "activity_index": activity_index,
        "item_index": None,
        "activity_type": activity_type,
        "offending_field": field,
        "expected_field": field,
        "expected_type": expected_type,
        "actual_type": actual_type,
        "message": message,
        "scope": "activity",
    }


def _format_activity_schema_diagnostic(violations: list[dict[str, Any]]) -> str:
    lines = [
        f"ACTIVITY_SCHEMA_GATE FAILED: {len(violations)} violations",
        "",
    ]
    for violation in violations[:10]:
        activity_id = violation["activity_id"]
        activity_index = violation["activity_index"]
        item_index = violation["item_index"]
        if item_index is None:
            lines.append(f"  activity #{activity_index} '{activity_id}':")
            lines.append(f"    {violation['message']}")
            lines.append("")
            continue
        lines.append(f"  activity #{activity_index} '{activity_id}' (item {item_index}):")
        offending = violation.get("offending_field")
        expected = violation.get("expected_field")
        if offending is None:
            lines.append(f"    missing required field '{expected}:'")
        elif expected is None:
            lines.append(f"    forbidden field '{offending}'")
        else:
            purpose = _ACTIVITY_ITEM_FIELD_PURPOSES.get(str(expected), "this value")
            lines.append(f"    forbidden field '{offending}' - use '{expected}:' for {purpose}")
        lines.append("")

    remaining = len(violations) - 10
    if remaining > 0:
        lines.append(f"  ... ({remaining} more)")
        lines.append("")

    lines.extend(
        [
            "Canonical 'error-correction' item shape:",
            '  - sentence: "Я <error> вранці."',
            '    error: "вмиваюся"',
            '    correction: "вмиваюся"',
        ]
    )
    return "\n".join(lines)


def _quiz_translate_explanation_gate(activities: list[dict[str, Any]]) -> dict[str, Any]:
    """Require teaching feedback for quiz and translate multiple-choice items."""
    violations: list[dict[str, Any]] = []
    checked = 0

    for activity_index, activity in enumerate(activities, start=1):
        if not isinstance(activity, Mapping):
            continue
        activity_type = str(activity.get("type") or "")
        if activity_type not in _ACTIVITY_EXPLANATION_REQUIRED_TYPES:
            continue
        activity_id = str(activity.get("id") or f"#{activity_index}")
        items = activity.get("items", [])
        if not isinstance(items, list):
            continue

        for item_index, item in enumerate(items, start=1):
            if not isinstance(item, Mapping):
                continue
            checked += 1
            explanation = item.get("explanation")
            if isinstance(explanation, str) and explanation.strip():
                continue
            if "explanation" not in item:
                reason = "missing"
            elif not isinstance(explanation, str):
                reason = "invalid_type"
            else:
                reason = "empty"
            violations.append(
                {
                    "activity_id": activity_id,
                    "activity_index": activity_index,
                    "item_index": item_index,
                    "activity_type": activity_type,
                    "field": "explanation",
                    "reason": reason,
                    "message": (
                        f"{activity_type} item {item_index} in activity '{activity_id}' "
                        "must include a non-empty explanation for the correct answer"
                    ),
                }
            )

    report = {
        "passed": not violations,
        "checked": checked,
        "violations": violations,
    }
    if violations:
        report["message"] = _format_quiz_translate_explanation_diagnostic(violations)
    return report


def _format_quiz_translate_explanation_diagnostic(violations: list[dict[str, Any]]) -> str:
    lines = [
        f"QUIZ_TRANSLATE_EXPLANATIONS_GATE FAILED: {len(violations)} violations",
        "",
    ]
    for violation in violations[:10]:
        activity_id = violation["activity_id"]
        activity_index = violation["activity_index"]
        item_index = violation["item_index"]
        activity_type = violation["activity_type"]
        reason = violation["reason"]
        lines.append(f"  activity #{activity_index} '{activity_id}' ({activity_type}, item {item_index}):")
        lines.append(f"    {reason} required field 'explanation'")
        lines.append("")

    remaining = len(violations) - 10
    if remaining > 0:
        lines.append(f"  ... ({remaining} more)")
    return "\n".join(lines).rstrip()


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


# Word-target tolerance: 8% lower band. User direction 2026-05-23
# (handoff docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md
# decision row B): word targets stay as MINIMUMS for the writer prompt
# guidance, but the gate tolerates ±8% below target to avoid 0.25%-short
# rejections like deepseek-pro 1197/1200. Empirically the 8% band still
# rejects gemini-tools 1031/1200 (14% short).
_WORD_COUNT_TOLERANCE_BELOW = 0.08
_PRIMARY_READING_BLOCK_RE = re.compile(
    r"(?:<!--\s*PRIMARY-READING\s*-->.*?<!--\s*/PRIMARY-READING\s*-->|^:::primary-reading(?:\s*\{[^\n]*\})?\s*\n.*?\n:::\s*$)",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)


def _strip_primary_reading_blocks(text: str) -> str:
    return _PRIMARY_READING_BLOCK_RE.sub("", text)


def _word_count_gate(text: str, target: int) -> dict[str, Any]:
    count = _word_count(_strip_comments(_strip_primary_reading_blocks(text)))
    min_with_tolerance = int(target * (1 - _WORD_COUNT_TOLERANCE_BELOW))
    return {
        "passed": count >= min_with_tolerance,
        "count": count,
        "target": target,
        "min_with_tolerance": min_with_tolerance,
        "tolerance_below_pct": _WORD_COUNT_TOLERANCE_BELOW * 100,
    }


_WRITER_DRAFT_SECTION_FLOOR_RATIO = 0.85


def _writer_draft_countable_words(text: str) -> int:
    return _word_count(_strip_comments(_strip_primary_reading_blocks(text)))


def _writer_draft_section_length_report(
    plan: Mapping[str, Any],
    module_text: str,
    *,
    section_floor_ratio: float = _WRITER_DRAFT_SECTION_FLOOR_RATIO,
) -> list[dict[str, Any]]:
    outline = plan.get("content_outline")
    if not isinstance(outline, list):
        return []

    archetype = resolve_module_archetype(
        str(plan.get("level") or ""),
        int(plan.get("sequence") or 0),
    )
    archetype_id = str(archetype.get("id") or "")
    reports: list[dict[str, Any]] = []
    for section in outline:
        if not isinstance(section, Mapping):
            continue
        title = str(section.get("section") or "").strip()
        if not title:
            continue
        try:
            budget = int(section["words"])
        except (KeyError, TypeError, ValueError):
            continue
        section_text = _extract_section_text(module_text, title, archetype_key=archetype_id)
        count = _writer_draft_countable_words(section_text)
        floor = int(budget * section_floor_ratio)
        reports.append(
            {
                "section": title,
                "count": count,
                "budget": budget,
                "floor": floor,
                "floor_ratio": section_floor_ratio,
                "shortfall": max(0, budget - count),
                "passed": count >= floor,
            }
        )
    return reports


def writer_draft_length_report(
    plan: Mapping[str, Any],
    module_text: str,
    *,
    plan_path: Path | None = None,
    section_floor_ratio: float = _WRITER_DRAFT_SECTION_FLOOR_RATIO,
) -> dict[str, Any]:
    target = int(plan["word_target"])
    count = _writer_draft_countable_words(module_text)
    size_policy = build_size_policy_for_plan(
        plan,
        plan_path=plan_path,
        actual_words=count,
    )
    section_reports = _writer_draft_section_length_report(
        plan,
        module_text,
        section_floor_ratio=section_floor_ratio,
    )
    short_sections = [section for section in section_reports if section["passed"] is False]
    total_shortfall = max(0, target - count)
    return {
        "passed": total_shortfall == 0 and not short_sections,
        "count": count,
        "target": target,
        "total_shortfall": total_shortfall,
        "section_floor_ratio": section_floor_ratio,
        "sections": section_reports,
        "short_sections": short_sections,
        "size_policy": size_policy_summary(size_policy),
    }


def _writer_draft_shortfall_lines(report: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    total_shortfall = int(report.get("total_shortfall") or 0)
    if total_shortfall > 0:
        lines.append(
            f"- Overall draft is {total_shortfall} words short of "
            f"{int(report.get('target') or 0)} (counted {int(report.get('count') or 0)})."
        )
    for section in report.get("short_sections") or []:
        if not isinstance(section, Mapping):
            continue
        lines.append(
            "- "
            f"{section.get('section')}: {int(section.get('shortfall') or 0)} words short "
            f"of {int(section.get('budget') or 0)} "
            f"(counted {int(section.get('count') or 0)}; "
            f"85% floor {int(section.get('floor') or 0)})."
        )
    return lines or ["- No shortfalls."]


def render_writer_draft_length_expansion_prompt(
    *,
    plan: Mapping[str, Any],
    module_text: str,
    length_report: Mapping[str, Any],
    plan_path: Path | None = None,
) -> str:
    shortfall_lines = "\n".join(_writer_draft_shortfall_lines(length_report))
    diagnostic = _yaml_inline(length_report)
    size_policy = build_size_policy_for_plan(
        plan,
        plan_path=plan_path,
        actual_words=int(length_report.get("count") or 0),
    )
    return "\n".join(
        [
            "# Writer Draft Length Pre-check",
            "",
            "The deterministic first-draft length pre-check failed before the full Python QG loop.",
            "Gate-counted words exclude markdown comments and `:::primary-reading` blocks.",
            "",
            "## Size policy",
            render_writer_size_policy(size_policy),
            "",
            "## Required expansion",
            shortfall_lines,
            "",
            "Expand the named short sections only with source-backed analytic/textual substance: deeper close-reading, richer source comparison, more cultural context from the provided material, and clearer explanation of examples.",
            "Do NOT add padding, filler transitions, meta-narration, invented citations, or new uncited claims.",
            "Keep ALL existing content, citations, headings, activities, vocabulary, resources, and `:::primary-reading` blocks verbatim.",
            "Do not edit text inside any `:::primary-reading` block. Add explanatory prose around those blocks instead.",
            "Return the FULL patched `module.md`; do not return the other writer artifacts.",
            "",
            "## Output contract",
            "Return exactly one fenced markdown block and nothing else:",
            "```markdown file=module.md",
            "... full patched module.md content ...",
            "```",
            "",
            "## Length diagnostic",
            "```yaml",
            diagnostic,
            "```",
            "",
            "## Current module.md",
            "```markdown",
            module_text,
            "```",
        ]
    )


def run_writer_draft_length_precheck(
    *,
    plan: Mapping[str, Any],
    module_dir: Path,
    plan_path: Path,
    writer: str = "claude-tools",
    writer_corrector: Callable[[CorrectionContext], str | Mapping[str, str] | None] | None = None,
    invoker: Callable[..., Any] | None = None,
    event_sink: Callable[..., None] | None = None,
) -> dict[str, Any]:
    """Run one targeted writer expansion before the full Python QG loop."""
    module_path = module_dir / "module.md"
    before_text = _read_required(module_path)
    before = writer_draft_length_report(plan, before_text, plan_path=plan_path)
    if before.get("passed") is True:
        _emit(
            event_sink,
            "writer_draft_length_precheck",
            status="skipped",
            count=before["count"],
            target=before["target"],
            short_section_count=0,
        )
        return {"applied": False, "before": before, "after": before}

    size_policy = build_size_policy_for_plan(
        plan,
        plan_path=plan_path,
        actual_words=int(before["count"]),
    )
    if not size_policy_allows_auto_expansion(size_policy):
        _emit(
            event_sink,
            "writer_draft_length_precheck",
            status="policy_mismatch",
            count=before["count"],
            target=before["target"],
            short_section_count=len(before["short_sections"]),
            size_policy_status=size_policy.status,
        )
        return {
            "applied": False,
            "kind": "writer_draft_length_precheck",
            "patch_status": "policy_mismatch",
            "policy_mismatch": True,
            "before": before,
            "after": before,
            "size_policy": size_policy_summary(size_policy),
        }

    prompt = render_writer_draft_length_expansion_prompt(
        plan=plan,
        plan_path=plan_path,
        module_text=before_text,
        length_report=before,
    )
    context = CorrectionContext(
        gate="writer_draft_length_precheck",
        gate_report=before,
        module_dir=module_dir,
        plan_path=plan_path,
        qg_report={"gates": {"writer_draft_length_precheck": before}},
        prompt=prompt,
    )
    if writer_corrector is None:
        response: str | Mapping[str, str] | None = invoke_writer(
            prompt,
            writer=writer,
            cwd=module_dir,
            invoker=invoker,
        )
    else:
        response = writer_corrector(context)

    applied = "unparseable"
    if isinstance(response, Mapping):
        write_writer_artifacts(module_dir, response)
        applied = "writer_artifacts_mapping"
    elif isinstance(response, str):
        patched = parse_writer_correction_module_only(response)
        if patched is not None:
            module_path.write_text(patched, encoding="utf-8")
            applied = "module_patch"

    after_text = _read_required(module_path)
    after = writer_draft_length_report(plan, after_text, plan_path=plan_path)
    _emit(
        event_sink,
        "writer_draft_length_precheck",
        status="applied" if applied != "unparseable" else "unparseable",
        applied=applied,
        count_before=before["count"],
        count_after=after["count"],
        target=before["target"],
        short_section_count=len(before["short_sections"]),
    )
    return {
        "applied": applied != "unparseable",
        "kind": "writer_draft_length_precheck",
        "prompt": prompt,
        "response": dict(response) if isinstance(response, Mapping) else response,
        "patch_status": applied,
        "before": before,
        "after": after,
    }


_A1_M1_M7_SECTION_ALIASES = {
    "Звуки і літери": ("Sound First, Letter Second",),
    "Голосні звуки": ("Six Vowel Sounds, Ten Letters",),
    "Приголосні звуки": ("Consonant Sounds",),
    "Привіт!": ("Your First Conversation",),
    "Склади": ("Syllables",),
    "Голосні літери": ("Vowel Letters",),
    "Читання слів": ("Reading Words",),
    "Йотовані голосні як передумова": ("Iotated Vowels First",),
    "М'який знак": ("The Soft Sign",),
    "Апостроф": ("The Apostrophe",),
    "Контраст і типові помилки L2": ("Contrast and L2 Reading Traps",),
    "Перенос і підсумок": ("Line Breaks and Textbook Check",),
    "Наголос": ("Stress",),
    "Інтонація": ("Intonation",),
    "Читаємо вголос": ("Reading Aloud",),
    "Діалоги": ("Dialogues",),
    "Мене звати...": ("My Name Is...",),
    "Це...": ("This Is...",),
    "Особові займенники": ("Personal Pronouns",),
    "Я — студент": ("I Am a Student",),
    "Звідки?": ("Where From?",),
    "Сім'я": ("Family",),
    "У мене є": ("I Have",),
    "Мій, моя, моє": ("My",),
    "Що ми знаємо?": ("What We Know",),
    "Читання": ("Reading",),
    "Граматика": ("Grammar",),
    "Діалог": ("Dialogue",),
    "Підсумок": ("Textbook Check",),
}

_A1_M1_M7_ARCHETYPES = {
    "a1-zero-script-onboarding",
    "a1-script-building",
    "a1-first-contact-survival",
}


def _section_gate(text: str, plan: Mapping[str, Any]) -> dict[str, Any]:
    archetype = resolve_module_archetype(
        str(plan.get("level") or ""),
        int(plan.get("sequence") or 0),
    )
    archetype_id = str(archetype.get("id") or "")
    headings_by_key: dict[str, list[str]] = {}
    for match in _HEADING_RE.finditer(text):
        raw_heading = match.group(1).strip()
        headings_by_key.setdefault(_section_heading_key(raw_heading), []).append(raw_heading)
    missing = []
    duplicate_headings = []
    seen_keys: set[str] = set()
    for section in plan["content_outline"]:
        title = section["section"]
        heading_keys = _section_heading_keys_for_plan_section(title, archetype_id)
        primary_heading_key = heading_keys[0]
        if primary_heading_key in seen_keys:
            continue
        seen_keys.add(primary_heading_key)
        matching_headings = [
            heading
            for key in heading_keys
            for heading in headings_by_key.get(key, [])
        ]
        if not matching_headings:
            missing.append(title)
        elif len(matching_headings) > 1:
            duplicate_headings.append(
                {
                    "section": title,
                    "headings": matching_headings,
                    "count": len(matching_headings),
                }
            )
    budgets = []
    for section in plan["content_outline"]:
        title = section["section"]
        target = int(section["words"])
        section_text = _extract_section_text(text, title, archetype_key=archetype_id)
        count = _word_count(_strip_comments(section_text))
        min_words = int(target * 0.9)
        # Per user direction (2026-05-17, reaffirmed 2026-05-23): word targets
        # are MINIMUMS. Overshoot is welcome, never an error. We retain `min`
        # and `max` fields in the output for diagnostic visibility — they feed
        # the writer correction prompt as targeting guidance — but they do
        # NOT fail the gate. The 2026-05-23 reaffirmation is specifically:
        # "the section wordcount is a guidance for the writer, it is not a
        # reason to drop an error. The important is that the whole content
        # is a whole and not less than the planned word count." The total
        # `word_count` gate enforces the only hard floor; per-section budgets
        # surface as advisory diagnostics. The 2026-05-21 a1/my-morning
        # build #13 cascade — where word_count r1 correction balanced the
        # total but left Діалоги (257/270) and Мій ранок (265/270) under
        # their per-section min and triggered a terminal halt — is the
        # canonical failure pattern this relaxation prevents.
        max_words = int(target * 1.1)  # diagnostic-only
        budgets.append(
            {
                "section": title,
                "count": count,
                "min": min_words,
                "max": max_words,
                # `passed` is retained on every per-section budget for backward
                # compatibility with diagnostic consumers (writer correction
                # render, telemetry dashboards). It marks per-section min
                # adherence, NOT a build-fail signal — see gate-level `passed`
                # below.
                "passed": count >= min_words,
                "under_min": count < min_words,
                "over_max": count > max_words,
            }
        )
    return {
        # Gate-level `passed` reflects ONLY missing headings: every contracted
        # section must EXIST as a level-2 heading in the module. Per-section
        # word budgets are advisory (see comment in budgets construction
        # above). A future stricter mode could surface per-section under-min
        # as a separate `plan_sections_balance` advisory gate, but the build
        # halt no longer fires on it.
        "passed": not missing and not duplicate_headings,
        "missing_headings": missing,
        "duplicate_headings": duplicate_headings,
        "archetype": archetype_id,
        "word_budgets": budgets,
    }


def _section_heading_keys_for_plan_section(title: Any, archetype_key: str | None = None) -> list[str]:
    keys = [_section_heading_key(title)]
    if archetype_key in _A1_M1_M7_ARCHETYPES:
        for alias in _A1_M1_M7_SECTION_ALIASES.get(str(title), ()):
            alias_key = _section_heading_key(alias)
            if alias_key not in keys:
                keys.append(alias_key)
    return keys


def _section_heading_key(title: Any) -> str:
    title_str = str(title) if title is not None else ""
    normalized = unicodedata.normalize("NFD", title_str.strip())
    without_stress = "".join(ch for ch in normalized if ch not in _VESUM_STRESS_MARKS)
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", without_stress)).strip()


def _extract_section_text(text: str, title: str, *, archetype_key: str | None = None) -> str:
    title_keys = set(_section_heading_keys_for_plan_section(title, archetype_key))
    match = next(
        (
            heading_match
            for heading_match in _HEADING_RE.finditer(text)
            if _section_heading_key(heading_match.group(1)) in title_keys
        ),
        None,
    )
    if match is None:
        return ""
    next_heading = re.search(r"^##\s+", text[match.end() :], flags=re.MULTILINE)
    if not next_heading:
        return text[match.end() :]
    return text[match.end() : match.end() + next_heading.start()]


def _vesum_heritage_attestation_enabled(level: str | None) -> bool:
    return str(level or "").strip().lower() in SEMINAR_LEVELS


def _folk_heritage_attestation_citations(row: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    citations = row.get("citations")
    if isinstance(citations, list):
        return [citation for citation in citations if isinstance(citation, Mapping)]

    dictionary = row.get("dictionary")
    url = row.get("url")
    if isinstance(dictionary, str) and isinstance(url, str):
        return [{"dictionary": dictionary, "url": url}]
    return []


def _folk_heritage_attestation_is_valid(row: Mapping[str, Any]) -> bool:
    if row.get("is_russianism") is not False:
        return False
    for citation in _folk_heritage_attestation_citations(row):
        dictionary = str(citation.get("dictionary_slug") or citation.get("dictionary") or "").strip()
        url = str(citation.get("url") or "").strip()
        if dictionary and url.startswith("https://slovnyk.me/dict/"):
            return True
    return False


def _folk_heritage_attestation_index(
    path: Path | None = None,
) -> dict[str, Mapping[str, Any]]:
    source_path = path or FOLK_HERITAGE_ATTESTATIONS_PATH
    if not source_path.exists():
        return {}

    data = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, Mapping):
        raise ValueError(f"{source_path} must contain a YAML mapping")
    rows = data.get("attestations", [])
    if not isinstance(rows, list):
        raise ValueError(f"{source_path} field 'attestations' must be a list")

    index: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not _folk_heritage_attestation_is_valid(row):
            continue
        lemma = _normalize_for_vesum(str(row.get("lemma") or "")).lower()
        if not lemma:
            continue
        surfaces = {lemma}
        accepted_surfaces = row.get("accepted_surfaces", [])
        if accepted_surfaces is None:
            accepted_surfaces = []
        if not isinstance(accepted_surfaces, list):
            raise ValueError(
                f"{source_path} lemma {lemma!r} field 'accepted_surfaces' must be a list"
            )
        for surface in accepted_surfaces:
            normalized = _normalize_for_vesum(str(surface or "")).lower()
            if normalized:
                surfaces.add(normalized)
        for surface in surfaces:
            index[surface] = row
    return index


def _foreign_proper_noun_attestation_urls(row: Mapping[str, Any]) -> list[str]:
    urls = row.get("wikipedia_urls")
    if isinstance(urls, list):
        return [str(url).strip() for url in urls if str(url or "").strip()]

    url = row.get("wikipedia_url") or row.get("url")
    if isinstance(url, str) and url.strip():
        return [url.strip()]
    return []


_UK_WIKI_ARTICLE_PREFIX = "https://uk.wikipedia.org/wiki/"


def _foreign_proper_noun_attestation_is_valid(row: Mapping[str, Any]) -> bool:
    # Require a non-empty article slug after the prefix: the degenerate
    # "https://uk.wikipedia.org/wiki/" (no article) must NOT validate, so a
    # plan-declared foreign_cultural_terms exemption cannot be blessed with a
    # placeholder URL that points at no real page.
    return any(
        url.startswith(_UK_WIKI_ARTICLE_PREFIX)
        and url[len(_UK_WIKI_ARTICLE_PREFIX) :].strip("/").strip() != ""
        for url in _foreign_proper_noun_attestation_urls(row)
    )


def _foreign_proper_noun_attestation_index(
    path: Path | None = None,
) -> dict[str, Mapping[str, Any]]:
    source_path = path or FOREIGN_PROPER_NOUN_ATTESTATIONS_PATH
    if not source_path.exists():
        return {}

    data = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, Mapping):
        raise ValueError(f"{source_path} must contain a YAML mapping")
    rows = data.get("attestations", [])
    if not isinstance(rows, list):
        raise ValueError(f"{source_path} field 'attestations' must be a list")

    index: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not _foreign_proper_noun_attestation_is_valid(row):
            continue
        lemma = _normalize_for_vesum(str(row.get("lemma") or "")).lower()
        if not lemma:
            continue
        surfaces = {lemma}
        forms = row.get("forms", [])
        if forms is None:
            forms = []
        if not isinstance(forms, list):
            raise ValueError(f"{source_path} lemma {lemma!r} field 'forms' must be a list")
        for surface in forms:
            normalized = _normalize_for_vesum(str(surface or "")).lower()
            if normalized:
                surfaces.add(normalized)
        for surface in surfaces:
            index[surface] = row
    return index


def _is_titlecase_ukrainian_proper_noun_surface(surface: str) -> bool:
    token = surface.strip(_VESUM_WORD_EDGE_CHARS)
    if not token or not _CYRILLIC_LETTER_RE.search(token):
        return False

    parts = [part for part in re.split(r"[-‐-―]", token) if part]
    if not parts:
        return False
    for part in parts:
        letters = [char for char in part if char.isalpha()]
        if not letters or not letters[0].isupper():
            return False
        if any(not char.islower() for char in letters[1:]):
            return False
    return True


def _resolve_foreign_proper_noun_attested_missing(
    missing_lc: set[str],
    unchecked_pairs: Sequence[tuple[str, str, str]],
) -> set[str]:
    if not missing_lc:
        return set()

    attestation_index = _foreign_proper_noun_attestation_index()
    if not attestation_index:
        return set()

    attested: set[str] = set()
    for surface, lower, original_case_lookup in unchecked_pairs:
        if lower not in missing_lc:
            continue
        for raw in (surface, original_case_lookup):
            normalized = _normalize_for_vesum(raw).strip()
            if not _is_titlecase_ukrainian_proper_noun_surface(normalized):
                continue
            if normalized.lower() in attestation_index:
                attested.add(lower)
                break

    return attested


_PLAN_VESUM_EXEMPTION_CATEGORIES: tuple[str, ...] = (
    "foreign_cultural_terms",
    "quoted_critical_terms",
    "corpus_attested_quotes",
)


def _span_surface_lc(span_texts: Iterable[str]) -> set[str]:
    surfaces: set[str] = set()
    for span_text in span_texts:
        for word in _iter_vesum_word_surfaces(_normalize_for_vesum(span_text)):
            normalized = _normalize_for_vesum(word).lower()
            if normalized:
                surfaces.add(normalized)
    return surfaces


_BACKTICK_SPAN_RE = re.compile(r"`([^`]*)`")

# A legitimate inline «…» citation in seminar/folk prose is short (the longest
# across all shipped folk modules is ~65 chars; verbatim verse lives in stripped
# :::primary-reading fences, not inline guillemets). An unbalanced «  paired with
# a far-later » by the stack below would otherwise yield a runaway span that
# falsely marks an un-quoted token as quoted (→ a false exemption). Bounding the
# span length cleanly separates real citations from such parse artifacts.
_MAX_GUILLEMET_SPAN_CHARS = 200


def _guillemet_span_texts(module_text: str) -> list[str]:
    spans: list[str] = []
    starts: list[int] = []
    for index, char in enumerate(module_text):
        if char == "«":
            starts.append(index + 1)
        elif char == "»" and starts:
            start = starts.pop()
            if index - start <= _MAX_GUILLEMET_SPAN_CHARS:
                spans.append(module_text[start:index])
    return spans


def _backtick_span_texts(module_text: str) -> list[str]:
    return [match.group(1) for match in _BACKTICK_SPAN_RE.finditer(module_text)]


def _quoted_surface_lc(module_text: str) -> set[str]:
    """Return normalized-lowercase surfaces quoted in guillemets or backticks."""
    return _span_surface_lc(_guillemet_span_texts(module_text)) | _span_surface_lc(
        _backtick_span_texts(module_text)
    )


def _guillemet_surface_lc(module_text: str) -> set[str]:
    return _span_surface_lc(_guillemet_span_texts(module_text))


def _plan_vesum_exemption_surfaces_lc(
    category: str,
    entry: Mapping[str, Any],
    index: int,
) -> set[str]:
    term = entry.get("term")
    if not isinstance(term, str) or not term.strip():
        raise ValueError(f"vesum_exemptions.{category}[{index}] missing non-empty term")

    forms = entry.get("forms")
    if not isinstance(forms, list):
        raise ValueError(f"vesum_exemptions.{category}[{index}] missing forms list")

    rationale = entry.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError(
            f"vesum_exemptions.{category}[{index}] missing non-empty rationale"
        )

    if category == "foreign_cultural_terms":
        wikipedia_url = entry.get("wikipedia_url")
        if (
            not isinstance(wikipedia_url, str)
            or not wikipedia_url.strip()
            or not _foreign_proper_noun_attestation_is_valid(entry)
        ):
            raise ValueError(
                f"vesum_exemptions.{category}[{index}] "
                "missing valid uk.wikipedia.org wikipedia_url"
            )

    if category == "corpus_attested_quotes":
        source_chunk = entry.get("source_chunk")
        if not isinstance(source_chunk, str) or not source_chunk.strip():
            raise ValueError(
                f"vesum_exemptions.{category}[{index}] missing non-empty source_chunk"
            )

    surfaces = {_normalize_for_vesum(term).lower()}
    for form_index, form in enumerate(forms):
        if not isinstance(form, str):
            raise ValueError(
                f"vesum_exemptions.{category}[{index}].forms[{form_index}] must be string"
            )
        normalized = _normalize_for_vesum(form).lower()
        if not normalized:
            raise ValueError(
                f"vesum_exemptions.{category}[{index}].forms[{form_index}] is empty"
            )
        surfaces.add(normalized)
    if "" in surfaces:
        raise ValueError(f"vesum_exemptions.{category}[{index}] has empty term")
    return surfaces


def _resolve_plan_declared_vesum_exemptions(
    missing_lc: set[str],
    unchecked_pairs: Sequence[tuple[str, str, str]],
    module_text: str,
    plan_vesum_exemptions: Mapping[str, Any] | None,
) -> tuple[set[str], dict[str, list[str]]]:
    if plan_vesum_exemptions is None:
        return set(), {category: [] for category in _PLAN_VESUM_EXEMPTION_CATEGORIES}
    if not isinstance(plan_vesum_exemptions, Mapping):
        raise ValueError("vesum_exemptions must be a mapping")

    unknown_categories = sorted(
        set(plan_vesum_exemptions) - set(_PLAN_VESUM_EXEMPTION_CATEGORIES)
    )
    if unknown_categories:
        raise ValueError(
            "vesum_exemptions contains unknown categories: "
            + ", ".join(unknown_categories)
        )

    quoted_lc: set[str] | None = None
    guillemet_lc: set[str] | None = None
    by_category_lc: dict[str, set[str]] = {
        category: set() for category in _PLAN_VESUM_EXEMPTION_CATEGORIES
    }

    for category in _PLAN_VESUM_EXEMPTION_CATEGORIES:
        rows = plan_vesum_exemptions.get(category, [])
        if not isinstance(rows, list):
            raise ValueError(f"vesum_exemptions.{category} must be a list")
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise ValueError(f"vesum_exemptions.{category}[{index}] must be a mapping")
            declared_lc = _plan_vesum_exemption_surfaces_lc(category, row, index)
            candidates = declared_lc & missing_lc
            if category == "quoted_critical_terms":
                if guillemet_lc is None:
                    guillemet_lc = _guillemet_surface_lc(module_text)
                candidates &= guillemet_lc
            elif category == "corpus_attested_quotes":
                if quoted_lc is None:
                    quoted_lc = _quoted_surface_lc(module_text)
                candidates &= quoted_lc
            by_category_lc[category].update(candidates)

    exempted_lc = set().union(*by_category_lc.values())
    by_category_words: dict[str, list[str]] = {}
    for category, category_lc in by_category_lc.items():
        by_category_words[category] = sorted(
            {
                surface
                for surface, lower, _original in unchecked_pairs
                if lower in category_lc
            }
        )
    return exempted_lc, by_category_words


_HERITAGE_AUTHENTIC_CLASSIFICATIONS = frozenset(
    {"authentic-archaism", "dialect", "historism", "borrowing", "standard"}
)

_HERITAGE_FALLBACK_BLOCKED_SURFACES = frozenset(
    {
        # Adversarial leak battery for the missing-word heritage fallback. Some
        # have standard/dialect homographs or VESUM entries, but they must not be
        # accepted by derivational or heritage fallback when the verifier reports
        # the surface as missing. Contextual style handling remains outside this
        # gate; the legacy active-participle cases below intentionally are not here.
        "глазний",
        "вкусний",
        "діюча",
        "заказувати",
        "настаювати",
        "находячийся",
        "оказувати",
        "получаючий",
        "поступаючий",
        "протиріччя",
        "решати",
        "слідувати",
    }
)

# Existence-gate accept-set (#3647, user decision 2026-06-21): real Ukrainian
# active-participle surfaces that the heritage classifier flags is_russianism=True
# yet are morphologically real forms of real verbs (оточувати → оточуючий,
# слідувати → слідуючий). The folk/seminar VESUM gate is an EXISTENCE gate: a real
# form passes. Calque-flagging ("we suggest довколишній / наступний") is a SEPARATE
# concern handled by the russianism layer (Антоненко / UA-GEC / check_russian_shadow),
# NOT by rejecting the form here — one gate, one job. This is the explicit accept
# counterpart to _HERITAGE_FALLBACK_BLOCKED_SURFACES above; it bypasses the russianism
# guard for these specific surfaces only, so genuine russianisms (діюча, протиріччя —
# blocked above) keep failing. бажаючий / керуючий / завідуючий already pass via the
# classifier (classification=standard) and need no entry here.
_FOLK_EXISTENCE_ACCEPTED_CALQUE_PARTICIPLES = frozenset(
    {
        "оточуючий",
        "слідуючий",
    }
)


def _engine_classifies_authentic(candidate: str) -> bool:
    """True iff the shared heritage classifier (#2912) attests ``candidate`` as
    authentic Ukrainian (archaism / dialect / historism / borrowing / standard)
    and NOT a russianism.

    Reads ``data/sources.db`` directly via ``scripts.lexicon.heritage_classifier``.
    A Russian-shadow morphology hit never decides on its own — the classifier
    records it as a warning but authentic dictionary/quote evidence overrides it
    (so поетичне ``другоє`` and dialectal ``ягілка`` pass while ``протиріччя``
    stays a russianism). Degrades to ``False`` (committed-allowlist-only fallback)
    when the classifier is unavailable — e.g. the corpus DB is absent on CI."""
    try:
        from scripts.lexicon.heritage_classifier import classify_surface_form

        verdict = classify_surface_form(candidate)
    except Exception:
        return False
    return (
        verdict.get("classification") in _HERITAGE_AUTHENTIC_CLASSIFICATIONS
        and not verdict.get("is_russianism", False)
    )


def _engine_flags_russianism(candidate: str) -> bool:
    """True iff the shared classifier directly flags ``candidate`` as a russianism.

    Such a form must NEVER be morphology-rescued via a standard base: e.g. the
    russianism ``діюча`` (→ чинна/дійова) lemmatises to the standard verb ``діяти``,
    but ``діюча`` itself stays a russianism and must remain flagged. Degrades to
    ``False`` when the classifier is unavailable (CI) — the independent russianism
    gates still apply."""
    try:
        from scripts.lexicon.heritage_classifier import classify_surface_form

        return bool(classify_surface_form(candidate).get("is_russianism", False))
    except Exception:
        return False


_UK_MORPH_ANALYZER: Any = None
_UK_MORPH_ANALYZER_TRIED = False


def _uk_morph_analyzer() -> Any:
    """Lazy Ukrainian morphological analyzer (pymorphy3); None if unavailable."""
    global _UK_MORPH_ANALYZER, _UK_MORPH_ANALYZER_TRIED
    if not _UK_MORPH_ANALYZER_TRIED:
        _UK_MORPH_ANALYZER_TRIED = True
        try:
            import pymorphy3

            _UK_MORPH_ANALYZER = pymorphy3.MorphAnalyzer(lang="uk")
        except Exception:
            _UK_MORPH_ANALYZER = None
    return _UK_MORPH_ANALYZER


def _morphological_base_candidates(word: str) -> set[str]:
    """Derived bases offered to the heritage classifier for an authentic-vocabulary
    surface form: the lemma (resolving oblique inflections of dialectal words, e.g.
    ``гагілку``→``гагілка``, ``ягілками``→``ягілка``) and a regular ``не``-stripped
    base (negated participles, e.g. ``незгладжений``→``згладжений``).

    A base is only *offered* — it is accepted solely when the classifier itself rules
    it authentic-and-not-russianism, so coinages (``обрядознавчий``) and russianisms
    (``протиріччя``) that lemmatise to themselves stay flagged and the russianism guard
    is untouched. Empty when the analyzer is unavailable (CI), leaving the surface-form
    + committed-allowlist checks unchanged. Productive derivational bases
    (``виворожувати``←``виворожити``) are handled by
    ``scripts.lexicon.derivational_morphology`` and verified by the same classifier.
    """
    candidates: set[str] = set()
    analyzer = _uk_morph_analyzer()
    if analyzer is not None:
        try:
            for parse in analyzer.parse(word)[:3]:
                lemma = (parse.normal_form or "").strip().lower()
                if lemma and lemma != word:
                    candidates.add(lemma)
        except Exception:
            pass
    if word.startswith("не") and len(word) > 4:
        candidates.add(word[2:])
    return candidates


def _derivational_base_candidates(word: str) -> set[str]:
    """Full derivational base lemmas proposed for heritage-classifier verification.

    The derivational module is a deterministic candidate generator only; this gate
    keeps policy authority by requiring every proposed base to classify as authentic
    and by preserving the direct surface russianism guard above.
    """
    try:
        from scripts.lexicon.derivational_morphology import derivational_bases

        return {row["base"] for row in derivational_bases(word) if row.get("base")}
    except Exception:
        return set()


def _resolve_folk_heritage_attested_missing(
    missing_lc: set[str],
    unchecked_pairs: Sequence[tuple[str, str, str]],
) -> set[str]:
    if not missing_lc:
        return set()

    candidates_by_missing: dict[str, set[str]] = {word: {word} for word in missing_lc}
    for surface, lower, original_case_lookup in unchecked_pairs:
        if lower not in missing_lc:
            continue
        candidates_by_missing[lower].add(_normalize_for_vesum(surface).lower())
        candidates_by_missing[lower].add(_normalize_for_vesum(original_case_lookup).lower())

    # Primary authority: the shared heritage classifier (#2912). It accepts
    # authentic archaic/dialectal/standard Ukrainian and keeps russianisms +
    # unknown coinages flagged, replacing the per-term whack-a-mole allowlist.
    # The committed slovnyk.me allowlist (#2899) collapses to a thin deterministic
    # override — consulted first (cheap dict lookup) and as the offline fallback
    # when the corpus DB is absent (CI).
    attestation_index = _folk_heritage_attestation_index()

    attested: set[str] = set()
    for word, candidates in candidates_by_missing.items():
        if candidates & _HERITAGE_FALLBACK_BLOCKED_SURFACES:
            continue
        # Existence-gate accept (#3647): real active-participle calques the classifier
        # mislabels russianism. Checked before the russianism guard so they pass; the
        # calque suggestion is the separate russianism layer's job, not a rejection here.
        if candidates & _FOLK_EXISTENCE_ACCEPTED_CALQUE_PARTICIPLES:
            attested.add(word)
            continue
        if attestation_index and any(candidate in attestation_index for candidate in candidates):
            attested.add(word)
            continue
        # Russianism guard: never morphology-rescue a form the classifier directly
        # flags as a russianism. A russianism participle/adjective lemmatises to its
        # standard verb root (діюча→діяти), which would otherwise leak it through —
        # but діюча itself must stay flagged. This keeps the gate's teeth.
        if any(_engine_flags_russianism(candidate) for candidate in candidates):
            continue
        # Offer each surface candidate plus its morphological bases (lemma + regular
        # `не`-stripped base) to the classifier. This resolves oblique inflections of
        # dialectal words (гагілку→гагілка) and negated participles of standard bases
        # (незгладжений→згладжений) that VESUM does not enumerate — VESUM-absence of a
        # valid inflected form, not a russianism.
        engine_candidates = set(candidates)
        for candidate in candidates:
            engine_candidates |= _morphological_base_candidates(candidate)
            engine_candidates |= _derivational_base_candidates(candidate)
        if any(_engine_classifies_authentic(candidate) for candidate in engine_candidates):
            attested.add(word)
    return attested


def _vesum_gate(
    *,
    module_text: str,
    activities: list[dict[str, Any]],
    vocabulary: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    verify_words_fn: Callable[[list[str]], dict[str, list[dict[str, Any]]]] | None,
    level: str | None = None,
    ignored_missing_surfaces: Collection[str] = (),
    plan_vesum_exemptions: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify Ukrainian words against VESUM, walking artifacts structurally.

    Four classes of false positives are deliberately excluded:

    1. **Phonetic transcriptions and inline code** — `[с':а]`, `[ц':а]`, and
       backticked fragments like `` `вмиваєс':а` `` are metalinguistic notation
       (parts of words, IPA-ish symbols), not VESUM lemmas.
    2. **Intentional misspellings in `error-correction` activities** —
       `error:`, `errorWord:`, and `error_word:` fields contain the typo the
       student must fix (e.g. `прокидаєштся`). Verifying them would always fail.
    3. **Intentional-error multiple-choice options** — `options: [{text, correct, intentional_error}]`
       values with `intentional_error: true` are deliberately incorrect/nonstandard forms
       (e.g. overgeneralized morphology like "п'юся") used as distractors to test common
       learner errors. They are excluded from VESUM verification (the opt-out). Regular
       distractors (`correct: false` without `intentional_error`) are real Ukrainian words
       placed in pedagogically wrong context and must be verified.
    4. **Sentence-initial capitalization** — VESUM is case-sensitive, so
       `Спочатку` (capitalized first word) returns no matches even though
       `спочатку` does. Lookup is performed in lowercase; the report keeps
       original casing for evidence.
    """
    from scripts.audit.config import VESUM_MIN_WORD_LENGTH

    text = _build_vesum_text(
        module_text,
        activities,
        vocabulary,
        resources,
        level=level,
        emit_negative_example_events=True,
    )

    # Pair each surface form with its normalized lowercase lookup key once, so
    # subsequent whitelist + missing computations don't re-normalize repeatedly.
    surface_pairs = sorted(_iter_vesum_lookup_surface_pairs(text, min_word_length=VESUM_MIN_WORD_LENGTH))
    whitelist_lc = _proper_name_whitelist_lc()
    unchecked_pairs = [
        (surface, lower, original_case_lookup)
        for surface, lower, original_case_lookup in surface_pairs
        if lower not in whitelist_lc
    ]
    if verify_words_fn is None:
        from scripts.verification.vesum import verify_words as verify_words_fn

    # VESUM is case-sensitive — lowercase before lookup so sentence-initial
    # words like "Спочатку" match the lemma "спочатку".
    lookup_words = sorted({lower for _surface, lower, _original in unchecked_pairs})
    try:
        verified = verify_words_fn(lookup_words)
    except Exception as exc:
        return {"passed": False, "error": str(exc), "checked": len(unchecked_pairs)}

    missing_lc = {word for word, matches in verified.items() if not matches}
    if missing_lc:
        original_case_words = sorted(
            {
                original_case_lookup
                for _surface, lower, original_case_lookup in unchecked_pairs
                if lower in missing_lc and original_case_lookup != lower
            }
        )
        if original_case_words:
            try:
                original_case_verified = verify_words_fn(original_case_words)
            except Exception as exc:
                return {"passed": False, "error": str(exc), "checked": len(unchecked_pairs)}
            resolved_lc = {surface.lower() for surface, matches in original_case_verified.items() if matches}
            missing_lc -= resolved_lc
    # Textbook syllable-break notation such as `за-пи-са-ний` should still
    # resolve to the canonical VESUM form, but only after the intact whole
    # hyphenated token has had a chance to verify. Doing this as a fallback
    # prevents real lexical compounds like `будь-який` from being fused into
    # non-words before lookup.
    if missing_lc:
        syllable_lookup_by_missing = {
            word: collapsed
            for word in missing_lc
            if "-" in word
            for collapsed in (_collapse_syllable_break(word),)
            if collapsed != word and len(collapsed) >= VESUM_MIN_WORD_LENGTH
        }
        if syllable_lookup_by_missing:
            try:
                syllable_verified = verify_words_fn(sorted(set(syllable_lookup_by_missing.values())))
            except Exception as exc:
                return {"passed": False, "error": str(exc), "checked": len(unchecked_pairs)}
            missing_lc -= {
                word
                for word, collapsed in syllable_lookup_by_missing.items()
                if syllable_verified.get(collapsed)
            }
    # Hyphenated multi-word constructions fallback (per user direction
    # 2026-05-23). Many legitimate Ukrainian forms appear as hyphenated
    # compounds that VESUM only indexes by individual lemma: adverbial
    # expressions like `літера-в-літеру` ("letter by letter"), reduplicative
    # intensifiers like `тихо-тихо` / `день-у-день`, range constructions
    # like `п'ять-шість`, and color/temporal compounds like `темно-синій`.
    # The primary VESUM lookup treats the whole token as one lemma and
    # fails. Per user: "do not drop [an] error if VESUM is not supporting
    # it but we need to be able to check if they are correct with another
    # tool." Tier-1 fallback: split on hyphens, verify each constituent
    # in VESUM, accept the compound if every part above the lookup
    # threshold itself verifies. Short connector parts (`в`, `у`, `і`,
    # `до`) below VESUM_MIN_WORD_LENGTH are accepted without lookup —
    # they're under the gate's standard threshold and would be skipped if
    # encountered standalone. Russified compounds where one part fails
    # VESUM (e.g. hypothetical `буквенного-щось`) still fail the gate
    # because the failing constituent is itself a VESUM miss.
    if missing_lc:
        hyphenated_missing = sorted(w for w in missing_lc if "-" in w)
        if hyphenated_missing:
            constituent_lookups: set[str] = set()
            constituent_map: dict[str, list[str]] = {}
            compound_base_candidates_by_part: dict[str, list[str]] = {}
            compound_base_lookups: set[str] = set()
            for compound in hyphenated_missing:
                parts = [part for part in compound.split("-") if part]
                if len(parts) < 2:
                    continue
                eligible_parts = [part for part in parts if len(part) >= VESUM_MIN_WORD_LENGTH]
                constituent_lookups.update(eligible_parts)
                constituent_map[compound] = eligible_parts
                for part in eligible_parts[:-1]:
                    candidates = _compound_adjective_base_candidates(part)
                    if candidates:
                        compound_base_candidates_by_part[part] = candidates
                        compound_base_lookups.update(candidates)
            if constituent_lookups:
                try:
                    constituent_verified = verify_words_fn(sorted(constituent_lookups))
                except Exception as exc:
                    return {
                        "passed": False,
                        "error": str(exc),
                        "checked": len(unchecked_pairs),
                    }
            else:
                constituent_verified = {}
            if compound_base_lookups:
                try:
                    compound_base_verified = verify_words_fn(sorted(compound_base_lookups))
                except Exception as exc:
                    return {
                        "passed": False,
                        "error": str(exc),
                        "checked": len(unchecked_pairs),
                    }
                verified_compound_base_adjectives = {
                    word
                    for word, matches in compound_base_verified.items()
                    if any(_vesum_match_is_adjective(match) for match in matches)
                    and not _engine_flags_russianism(word)
                }
            else:
                verified_compound_base_adjectives = set()
            resolved_compounds: set[str] = set()
            for compound, parts in constituent_map.items():
                # All eligible parts must verify. If there are zero
                # eligible parts (every constituent below threshold),
                # accept conservatively — the compound is a string of
                # very short tokens we wouldn't gate individually.
                last_part_index = len(parts) - 1
                if all(
                    _vesum_part_verifies_as_compound_constituent(
                        constituent_verified.get(part) or [],
                        require_modifier=index < last_part_index
                        and bool(compound_base_candidates_by_part.get(part)),
                    )
                    or (
                        index < last_part_index
                        and any(
                            candidate in verified_compound_base_adjectives
                            for candidate in compound_base_candidates_by_part.get(part, ())
                        )
                    )
                    for index, part in enumerate(parts)
                ):
                    resolved_compounds.add(compound)
            missing_lc -= resolved_compounds
    if missing_lc:
        ist_adjective_candidates_by_missing = {
            word: candidates
            for word in missing_lc
            if (candidates := _productive_ist_adjective_candidates(word))
        }
        ist_adjective_lookups = {
            candidate
            for candidates in ist_adjective_candidates_by_missing.values()
            for candidate in candidates
        }
        if ist_adjective_lookups:
            try:
                ist_adjective_verified = verify_words_fn(sorted(ist_adjective_lookups))
            except Exception as exc:
                return {
                    "passed": False,
                    "error": str(exc),
                    "checked": len(unchecked_pairs),
                }
            verified_adjectives = {
                word
                for word, matches in ist_adjective_verified.items()
                if any(_vesum_match_is_adjective(match) for match in matches)
            }
            missing_lc -= {
                word
                for word, candidates in ist_adjective_candidates_by_missing.items()
                if any(candidate in verified_adjectives for candidate in candidates)
            }
    if missing_lc:
        missing_lc = {word for word in missing_lc if not _is_sung_vowel_practice_lookup(word)}
    roman_numeral_exempted_pairs: set[tuple[str, str, str]] = set()
    if missing_lc:
        roman_numeral_exempted_pairs = {
            (surface, lower, original_case_lookup)
            for surface, lower, original_case_lookup in unchecked_pairs
            if lower in missing_lc and _is_roman_numeral_lookup(original_case_lookup)
        }
        non_roman_missing_lc = {
            lower
            for _surface, lower, original_case_lookup in unchecked_pairs
            if lower in missing_lc and not _is_roman_numeral_lookup(original_case_lookup)
        }
        missing_lc -= {
            lower
            for _surface, lower, _original_case_lookup in roman_numeral_exempted_pairs
            if lower not in non_roman_missing_lc
        }
    foreign_proper_attested_lc: set[str] = set()
    if missing_lc and _vesum_heritage_attestation_enabled(level):
        try:
            foreign_proper_attested_lc = _resolve_foreign_proper_noun_attested_missing(
                missing_lc,
                unchecked_pairs,
            )
        except Exception as exc:
            return {
                "passed": False,
                "error": str(exc),
                "checked": len(unchecked_pairs),
            }
        missing_lc -= foreign_proper_attested_lc
    heritage_attested_lc: set[str] = set()
    if missing_lc and _vesum_heritage_attestation_enabled(level):
        try:
            heritage_attested_lc = _resolve_folk_heritage_attested_missing(missing_lc, unchecked_pairs)
        except Exception as exc:
            return {
                "passed": False,
                "error": str(exc),
                "checked": len(unchecked_pairs),
            }
    missing_lc -= heritage_attested_lc
    plan_exempted_lc: set[str] = set()
    plan_exempted_by_category: dict[str, list[str]] = {
        category: [] for category in _PLAN_VESUM_EXEMPTION_CATEGORIES
    }
    if _vesum_heritage_attestation_enabled(level) and plan_vesum_exemptions is not None:
        try:
            plan_exempted_lc, plan_exempted_by_category = (
                _resolve_plan_declared_vesum_exemptions(
                    missing_lc,
                    unchecked_pairs,
                    module_text,
                    plan_vesum_exemptions,
                )
            )
        except Exception as exc:
            return {
                "passed": False,
                "error": str(exc),
                "checked": len(unchecked_pairs),
            }
    missing_lc -= plan_exempted_lc
    missing = sorted(
        {
            surface
            for surface, lower, original in unchecked_pairs
            if lower in missing_lc
            and (surface, lower, original) not in roman_numeral_exempted_pairs
        }
    )
    heritage_attested_words = sorted(
        {surface for surface, lower, _original in unchecked_pairs if lower in heritage_attested_lc}
    )
    foreign_proper_attested_words = sorted(
        {surface for surface, lower, _original in unchecked_pairs if lower in foreign_proper_attested_lc}
    )
    plan_exempted_words = sorted(
        {surface for words in plan_exempted_by_category.values() for surface in words}
    )
    ignored_missing_lc = _vesum_missing_exclusion_keys(
        ignored_missing_surfaces,
        min_word_length=VESUM_MIN_WORD_LENGTH,
    )
    if ignored_missing_lc:
        missing = [surface for surface in missing if _normalize_for_vesum(surface).lower() not in ignored_missing_lc]
    return {
        "passed": not missing,
        "checked": len(unchecked_pairs),
        "whitelisted": len(surface_pairs) - len(unchecked_pairs),
        "heritage_attested": len(heritage_attested_words),
        "heritage_attested_words": heritage_attested_words[:100],
        "foreign_proper_noun_attested": len(foreign_proper_attested_words),
        "foreign_proper_noun_attested_words": foreign_proper_attested_words[:100],
        "plan_exempted": len(plan_exempted_words),
        "plan_exempted_words": plan_exempted_words[:100],
        "plan_exempted_by_category": {
            category: words[:100] for category, words in plan_exempted_by_category.items()
        },
        "missing": missing[:100],
        "missing_count": len(missing),
    }


def _bad_form_heritage_gate(
    *,
    module_text: str,
    activities: list[dict[str, Any]],
    vocabulary: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    heritage_lookup_fn: Callable[[str], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Reject bad-form markers for forms attested as authentic Ukrainian."""
    markers = _collect_bad_form_markers(module_text, activities, vocabulary, resources)
    if heritage_lookup_fn is None:
        heritage_lookup_fn = _search_heritage_no_live

    findings: list[dict[str, Any]] = []
    checked = 0
    skipped_empty = 0
    for marker in markers:
        query = _normalize_bad_form_query(marker["form"])
        if not query:
            skipped_empty += 1
            continue
        checked += 1
        try:
            hits = heritage_lookup_fn(query)
        except Exception as exc:
            return {
                "passed": False,
                "error": str(exc),
                "checked": checked,
                "marker_count": len(markers),
            }
        for hit in hits:
            if not _heritage_hit_blocks_bad_form_marker(hit):
                continue
            findings.append(_bad_form_heritage_finding(marker, query, hit))
            break

    return {
        "passed": not findings,
        "checked": checked,
        "marker_count": len(markers),
        "skipped_empty": skipped_empty,
        "findings": findings[:100],
        "finding_count": len(findings),
    }


def _search_heritage_no_live(query: str) -> list[dict[str, Any]]:
    from scripts.wiki.sources_db import search_heritage

    return search_heritage(query, include_live_slovnyk=False)


def _collect_bad_form_markers(
    module_text: str,
    activities: list[dict[str, Any]],
    vocabulary: list[dict[str, Any]],
    resources: list[dict[str, Any]],
) -> list[dict[str, str]]:
    markers: list[dict[str, str]] = []
    for artifact, strings in (
        ("module.md", [module_text]),
        ("activities.yaml", _walk_yaml_strings(activities)),
        ("vocabulary.yaml", _walk_yaml_strings(vocabulary)),
        ("resources.yaml", _walk_yaml_strings(resources)),
    ):
        for text in strings:
            for match in _AVOID_MARKER_RE.finditer(text):
                markers.append({"artifact": artifact, "form": match.group(1)})
    return markers


def _normalize_bad_form_query(raw: str) -> str:
    normalized = unicodedata.normalize("NFD", raw)
    normalized = "".join(char for char in normalized if char not in _VESUM_STRESS_MARKS)
    text = unicodedata.normalize("NFC", normalized)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("**", " ").replace("__", " ").replace("~~", " ")
    text = re.sub(r"[*_`]+", " ", text)
    text = text.strip()
    text = text.strip(" \t\r\n\"'’ʼ“”„«».,;:!?()[]{}<>")
    return re.sub(r"\s+", " ", text)


def _heritage_hit_blocks_bad_form_marker(hit: Mapping[str, Any]) -> bool:
    authentic = bool(
        hit.get("is_authentic_ukrainian")
        or hit.get("authentic_ukrainian")
        or hit.get("authentic")
    )
    russianism = bool(
        hit.get("is_russianism")
        or hit.get("russianism_warning")
        or hit.get("Russianism warning")
    )
    return authentic and not russianism


def _bad_form_heritage_finding(
    marker: Mapping[str, str],
    query: str,
    hit: Mapping[str, Any],
) -> dict[str, Any]:
    text = str(hit.get("text") or hit.get("definition") or hit.get("snippet") or "")
    return {
        "artifact": marker.get("artifact", ""),
        "form": marker.get("form", ""),
        "query": query,
        "source_family": hit.get("source_family", ""),
        "source": hit.get("source", ""),
        "word": hit.get("word", ""),
        "classification": hit.get("classification", ""),
        "evidence_tags": hit.get("evidence_tags", []),
        "text": text[:240],
    }


def _is_sung_vowel_practice_lookup(word: str) -> bool:
    compact = re.sub(r"[-‐-―\s]+", "", _normalize_for_vesum(word).casefold())
    return len(compact) >= 3 and len(set(compact)) == 1 and compact[0] in "аоуеиі"


def _is_roman_numeral_lookup(word: str) -> bool:
    token = _normalize_for_vesum(word).strip()
    if len(token) < 2 or token != token.upper():
        return False
    latin_token = token.translate(_CYRILLIC_ROMAN_NUMERAL_TRANSLATION)
    return bool(_ROMAN_NUMERAL_RE.fullmatch(latin_token))


def _normalize_for_vesum(lemma: str) -> str:
    """Strip stress marks, Markdown wrappers, and apostrophe variants before VESUM lookup.

    Writer output may contain combining accents such as U+0301 and local
    emphasis like `вмива́ю**ся**`. VESUM stores Ukrainian apostrophe words
    with ASCII U+0027, so lookup keys canonicalize U+02BC/curly/backtick/acute
    apostrophes after Markdown stripping.
    """
    text = unicodedata.normalize("NFD", lemma)
    text = "".join(char for char in text if char not in _VESUM_STRESS_MARKS)
    text = unicodedata.normalize("NFC", text)
    previous = None
    while previous != text:
        previous = text
        # Strip emphasis wrappers (bold/italic/code/italic-underscore).
        # Hyphens INSIDE emphasis are stripped only for explicit grammar
        # morpheme notation like `прокида**ю-ся**` and `**-ться**`. Lexical
        # hyphenated words must stay hyphenated because VESUM contains forms
        # like `будь-що` and `по-перше` as whole entries.
        #
        # 2026-05-17 regression context: PR #2068 introduced unconditional
        # hyphen-strip-inside-emphasis to fix m20's `прокида**ю-ся**`
        # VESUM misses, but it also stripped the hyphen from
        # `**темно-синій**` and broke
        # `test_vesum_gate_strips_hyphen_prefix_morpheme_notation`. The
        # conditional strip resolves both — morpheme breaks normalize,
        # compound words survive.
        text = re.sub(r"\*\*(.+?)\*\*", lambda m: _strip_morpheme_hyphen(m.group(1)), text)
        text = re.sub(
            r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)",
            lambda m: _strip_morpheme_hyphen(m.group(1)),
            text,
        )
        text = re.sub(r"`([^`]+)`", lambda m: _strip_morpheme_hyphen(m.group(1)), text)
        text = re.sub(
            r"(?<![_A-Za-z0-9А-ЯІЇЄҐа-яіїєґ])_([^_]+)_(?![_A-Za-z0-9А-ЯІЇЄҐа-яіїєґ])",
            lambda m: _strip_morpheme_hyphen(m.group(1)),
            text,
        )
    text = _strip_markdown_edge_markers(text)
    return _canonicalize_vesum_apostrophes(text).strip()


def _strip_markdown_edge_markers(text: str) -> str:
    return text.strip().lstrip("*_").rstrip("*_")


def _canonicalize_vesum_apostrophes(text: str) -> str:
    return str(text).translate(_VESUM_APOSTROPHE_TRANSLATION)


_VESUM_MORPHEME_HYPHEN_PARTS = frozenset(
    {
        "ся",
        "сь",
        "тся",
        "тсь",
        "ться",
        "шся",
        "шсь",
        "чся",
        "чсь",
        "ть",
        "ш",
        "мо",
        "те",
        "ю",
        "юся",
        "є",
        "єш",
        "єшся",
        "єть",
        "ємо",
        "ємося",
        "єте",
        "єтеся",
        "ють",
        "ються",
        "ється",
        "ва",
    }
)


def _strip_morpheme_hyphen(emphasis_inner: str) -> str:
    """Collapse a morpheme-break hyphen INSIDE markdown emphasis, but only
    when one side is an explicit grammar morpheme fragment.

    See ``_normalize_for_vesum`` for the rationale + regression context.
    """
    # Fast path: no hyphen → no decision needed.
    if "-" not in emphasis_inner:
        return emphasis_inner
    parts = emphasis_inner.split("-")
    # Only collapse single-hyphen forms — multi-hyphen tokens (`раз-два-три`,
    # exotic transliterations) are conservatively left intact.
    if len(parts) != 2:
        return emphasis_inner
    left, right = parts
    if not left and right in _VESUM_MORPHEME_HYPHEN_PARTS:
        return right
    if not right and left in _VESUM_MORPHEME_HYPHEN_PARTS:
        return left
    if not left or not right:
        return emphasis_inner
    if left in _VESUM_MORPHEME_HYPHEN_PARTS or right in _VESUM_MORPHEME_HYPHEN_PARTS:
        return left + right
    return emphasis_inner


def _vesum_missing_exclusion_keys(
    surfaces: Collection[str],
    *,
    min_word_length: int,
) -> frozenset[str]:
    keys: set[str] = set()
    for surface in surfaces:
        normalized = _normalize_for_vesum(str(surface))
        for word in _iter_vesum_word_surfaces(normalized):
            if len(word) >= min_word_length:
                keys.add(word.lower())
    return frozenset(keys)


def _productive_ist_adjective_candidates(word: str) -> tuple[str, ...]:
    for ending, min_stem_length in _VESUM_PRODUCTIVE_IST_ENDINGS:
        if not word.endswith(ending):
            continue
        stem = word[: -len(ending)]
        if len(stem) < min_stem_length:
            return ()
        return (f"{stem}ий", f"{stem}ій")
    return ()


def _compound_adjective_base_candidates(part: str) -> list[str]:
    if not part.endswith("о"):
        return []
    stem = part[:-1]
    candidates: list[str] = []
    for ending in ("ий", "ій"):
        candidate = f"{stem}{ending}"
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _vesum_match_is_adjective(match: Mapping[str, Any]) -> bool:
    return str(match.get("pos", "")).lower() in {"adj", "adjective"}


def _vesum_part_verifies_as_compound_constituent(
    matches: Sequence[Mapping[str, Any]],
    *,
    require_modifier: bool,
) -> bool:
    if not matches:
        return False
    if not require_modifier:
        return True
    return any(str(match.get("pos", "")).lower() in {"adj", "adjective", "adv", "adverb"} for match in matches)


def _iter_vesum_lookup_surface_pairs(
    text: str,
    *,
    min_word_length: int,
) -> set[tuple[str, str, str]]:
    normalized_words = {
        word for word in _iter_vesum_word_surfaces(_normalize_for_vesum(text)) if len(word) >= min_word_length
    }
    decorated_by_lower: dict[str, set[tuple[str, str]]] = {}
    decorated_text = _canonicalize_vesum_apostrophes(text)
    for match in _VESUM_DECORATED_WORD_RE.finditer(decorated_text):
        raw = match.group(0).strip(_VESUM_WORD_EDGE_CHARS)
        if not raw or "__" in raw or not _has_vesum_lookup_decoration(raw):
            continue
        if _looks_like_stem_fragment(decorated_text, match.start(), match.end()):
            continue
        normalized = _normalize_for_vesum(raw)
        for word in _iter_vesum_candidate_words(normalized):
            lower = word.lower()
            if len(word) < min_word_length and lower not in _VESUM_SHORT_DECORATED_WORDS:
                continue
            decorated_by_lower.setdefault(lower, set()).add((raw, word))

    pairs: set[tuple[str, str, str]] = set()
    for word in normalized_words:
        lower = word.lower()
        decorated = decorated_by_lower.pop(lower, set())
        if decorated:
            pairs.update((surface, lower, original_case) for surface, original_case in decorated)
        else:
            pairs.add((word, lower, word))
    for lower, decorated in decorated_by_lower.items():
        pairs.update((surface, lower, original_case) for surface, original_case in decorated)
    return pairs


def _has_vesum_lookup_decoration(text: str) -> bool:
    return any(char in text for char in "*_`") or any(
        char in _VESUM_STRESS_MARKS for char in unicodedata.normalize("NFD", text)
    )


def _iter_vesum_candidate_words(text: str) -> list[str]:
    words: list[str] = []
    text = _canonicalize_vesum_apostrophes(text)
    for match in _UK_WORD_RE.finditer(text):
        word = match.group(0).strip(_VESUM_WORD_EDGE_CHARS)
        if word:
            words.append(word)
    return words


def _iter_vesum_word_surfaces(text: str) -> list[str]:
    """Extract Ukrainian surface forms that are meaningful VESUM candidates."""
    words: list[str] = []
    text = _canonicalize_vesum_apostrophes(text)
    for match in _UK_WORD_RE.finditer(text):
        if _touches_blank_marker(text, match.start(), match.end()):
            continue
        if _touches_latin_letter(text, match.start(), match.end()):
            # Mixed-script tokens like `Buкварь` (writer typo: Latin "Bu"
            # immediately abutting Cyrillic "кварь") are typo artifacts,
            # not real Ukrainian words. The `_UK_WORD_RE` regex would
            # extract just the Cyrillic substring (`кварь`) and forward
            # it to VESUM, which would correctly fail it — but the
            # downstream signal is a gate failure on a token that doesn't
            # exist as written. Skipping here keeps VESUM honest. Real
            # script boundaries (Latin word followed by Cyrillic word
            # across whitespace) are unaffected because `_touches_latin_letter`
            # only fires when the abutting character is a Latin LETTER,
            # not whitespace or punctuation.
            continue
        if _looks_like_stem_fragment(text, match.start(), match.end()):
            continue
        raw = match.group(0)
        if _looks_like_elided_notation(text, match.start(), raw):
            continue
        word = raw.strip(_VESUM_WORD_EDGE_CHARS)
        if not word:
            continue
        if word.lower() in _STANDALONE_POSTFIX_FRAGMENTS:
            continue
        words.append(word)
    return words


def _collapse_syllable_break(word: str) -> str:
    """Collapse textbook syllable-break notation like `за-пи-са-ний` →
    `записаний` or `у-весь` → `увесь`.

    Early-reader Ukrainian textbooks (Захарійчук Grade 1 in particular)
    use hyphens to mark syllable boundaries in newly-introduced words.
    When the writer quotes a textbook excerpt verbatim, these
    pedagogical hyphens flow through to VESUM and fail (VESUM has
    `записаний` but not `за-пи-са-ний`).

    Heuristic: 2+ hyphen-separated parts where ALL parts are ≤4 chars
    (syllable-width) → strip all hyphens. Spares real compound nouns
    (`Івано-Франківськ` = 5+10 chars, kept; `темно-синій` = 5+6 chars,
    kept) and pronoun-noun terminology (`я-форма` = 1+5 chars, kept —
    `форма` exceeds 4). The 4-char threshold is the upper bound for a
    Ukrainian syllable (closed syllables like `буль` or `шість` rarely
    exceed 4 graphemes).

    Surfaced 2026-05-17 by a1/m20 rebuild #5 quoting the Захарійчук
    p.24 Frog & Toad excerpt: "тут за-пи-са-ний у-весь мій день" —
    both `за-пи-са-ний` (4 parts × 2-3 chars) and `у-весь` (1+4 chars)
    are textbook syllable breaks the writer copied verbatim.
    """
    if "-" not in word:
        return word
    parts = word.split("-")
    if len(parts) < 2:
        return word
    if all(len(part) <= 4 for part in parts):
        return "".join(parts)
    return word


def _touches_blank_marker(text: str, start: int, end: int) -> bool:
    """Return true when a regex word is a stem fragment next to `__` blanks."""
    return (start > 0 and text[start - 1] == "_") or (end < len(text) and text[end] == "_")


_CYRILLIC_LETTER_RE = re.compile(r"[А-ЯІЇЄҐа-яіїєґ]")
_STEM_FRAGMENT_LEFT_BOUNDARY = frozenset({"*", "_", "`"})
_STEM_FRAGMENT_MARKDOWN_CLOSERS = frozenset({"*", "_", "`"})


def _looks_like_stem_fragment(text: str, start: int, end: int) -> bool:
    """Return true for pedagogical stem notation like `користу-`.

    Motivated by claude-tools a1/my-morning build 2026-05-21: the correct
    stem fragment `**користу**-` is not a VESUM lemma and should not be checked.
    """
    if start > 0:
        previous = text[start - 1]
        if not previous.isspace() and previous not in _STEM_FRAGMENT_LEFT_BOUNDARY:
            return False

    if start >= end:
        return False

    hyphen_pos: int | None = None
    if text[end - 1] == "-":
        hyphen_pos = end - 1
    else:
        cursor = end
        while cursor < len(text) and text[cursor] in _STEM_FRAGMENT_MARKDOWN_CLOSERS:
            cursor += 1
        if cursor < len(text) and text[cursor] == "-":
            hyphen_pos = cursor

    if hyphen_pos is None:
        return False

    after_hyphen = hyphen_pos + 1
    return after_hyphen >= len(text) or not _CYRILLIC_LETTER_RE.match(text[after_hyphen])


_LATIN_LETTER_RE = re.compile(r"[A-Za-z]")


def _touches_latin_letter(text: str, start: int, end: int) -> bool:
    """Return true when a Cyrillic-word match abuts a Latin letter with no
    whitespace/punctuation between them.

    Catches writer typos like `Buкварь` (Latin "Bu" + Cyrillic "кварь" with
    no boundary), which `_UK_WORD_RE` would otherwise extract as the
    spurious token `кварь`. Real script transitions (Latin word followed
    by Cyrillic word across whitespace, punctuation, or markdown) do not
    fire this guard because the character at the boundary is not a Latin
    letter.
    """
    if start > 0 and _LATIN_LETTER_RE.match(text[start - 1]):
        return True
    return bool(end < len(text) and _LATIN_LETTER_RE.match(text[end]))


def _looks_like_elided_notation(text: str, start: int, raw: str) -> bool:
    """Skip clipped pronunciation notes like `прокидаюс'`, not quoted words."""
    return raw.endswith(("'", "ʼ")) and not (start > 0 and text[start - 1] in {"'", "ʼ"})


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

    textbook_author_variants = {
        *(_CYRILLIC_AUTHOR_CANONICAL.keys()),
        *(_CYRILLIC_AUTHOR_CANONICAL.values()),
    }
    return frozenset(name.lower() for name in {*PROPER_NAME_WHITELIST, *textbook_author_variants})


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

    These categories of metalinguistic content are removed before VESUM lookup:

    - `[...]` — phonetic notation like `[с':а]`, `[ц':а]`
    - `` `...` `` and ` ``` ... ``` ` — inline/fenced code
    - `{...}` — fill-in blank syntax like `Я вмиваю{ся}. Він прокидає{ться}.`
    - `-морфема` — hyphen-prefixed conjugation labels like `**-шся**`,
      `**-ться**`, and `-**юся**`. The regex lookbehind protects legitimate
      hyphenated compounds (`темно-синій`) where the char before `-` is a
      word char.
    - `sounds like **...**` — cue-prefixed bold pronunciation transcriptions.
    - `діал.` — textbook abbreviation for `діалектне`, not a lemma.
    - `<!-- bad -->форма<!-- /bad -->` — pedagogical Russianism / surzhyk /
      calque callouts in prose (e.g. "stick to сніданок, not the
      Russian-borrowed `<!-- bad -->завтрак<!-- /bad -->`"). The bad form
      is deliberately non-VESUM and would otherwise be a false positive;
      HTML comments don't render in MDX, so the learner still sees the
      bad form in plain prose for contrast.
    - `<!-- ... -->` — remaining HTML comments such as VERIFY annotations,
      after bad-form marker spans have already been removed.
    - `not "форма"` / `not «форма»` — prose-quoted warning examples where the
      quoted form is explicitly marked as wrong.
    - `як «лєший»` / `such as «X»` — a foreign/Russian term cited as an example
      in decolonization prose (a mention, not a use). «»-guillemets only (#3132).

    Used by the VESUM gate to avoid false positives on fragments that aren't
    VESUM-checkable lemmas.
    """
    text = _FENCED_CODE_RE.sub(" ", text)
    text = _INLINE_CODE_RE.sub(" ", text)
    text = _BRACKETS_RE.sub(" ", text)
    text = _BRACES_RE.sub(" ", text)
    text = _PRONUNCIATION_CUE_PATTERN.sub(" ", text)
    text = _MORPHEME_FRAGMENT_RE.sub(" ", text)
    text = _AVOID_MARKER_RE.sub(" ", text)
    text = _strip_comments(text)
    text = _WARNING_QUOTE_RE.sub(" ", text)
    text = _VESUM_ABBREVIATION_RE.sub(" ", text)
    return text


_USAGE_PARENTHETICAL_RE = re.compile(r"\([^()]*\)")


def _strip_usage_parentheticals(text: str) -> str:
    """Strip vocabulary-usage parentheticals before VESUM lookup.

    Vocabulary `usage:` fields sometimes append English or grammatical notes
    after the Ukrainian sample sentence, e.g. `(стем + -л- ...)`. Those notes
    are not asserted Ukrainian prose, while parentheticals in module prose can
    be meaningful learner-facing Ukrainian, so this is usage-field specific.
    """
    return _USAGE_PARENTHETICAL_RE.sub(" ", text)


def _negative_example_tail_forms(text: str) -> list[str]:
    forms: list[str] = []
    for match in _TF_NEGATIVE_EXAMPLE_RE.finditer(text):
        forms.extend(_iter_vesum_word_surfaces(match.group(1)))
    return _unique_preserving_order(forms)


def _unique_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def _strip_truefalse_negative_examples(statement: str) -> tuple[str, list[str]]:
    """Remove narrow sentence-final negative examples from TF VESUM scope."""
    skipped_forms: list[str] = []
    chunks: list[str] = []
    last_end = 0
    for match in _TF_NEGATIVE_EXAMPLE_RE.finditer(statement):
        forms = _negative_example_tail_forms(match.group(0))
        if not forms:
            continue
        start, end = match.span(1)
        chunks.append(statement[last_end:start])
        chunks.append(" " * (end - start))
        last_end = end
        skipped_forms.extend(forms)
    if not skipped_forms:
        return statement, []
    chunks.append(statement[last_end:])
    return "".join(chunks), _unique_preserving_order(skipped_forms)


def detect_unmarkered_negative_examples(activities_yaml: str) -> list[dict[str, Any]]:
    """Find obvious unmarkered negative examples in writer activity YAML.

    This is a soft writer-output warning, not a gate. It catches the narrow
    `X, а не Y.` / `X, not Y.` pattern in true-false statements and item bodies
    outside `error-correction`, where malformed forms should normally be wrapped
    in `<!-- bad -->...<!-- /bad -->` markers.
    """
    try:
        activities = yaml.safe_load(activities_yaml)
    except yaml.YAMLError:
        return []
    if not isinstance(activities, list):
        return []

    findings: list[dict[str, Any]] = []
    for activity in activities:
        if not isinstance(activity, dict):
            continue
        activity_type = str(activity.get("type") or "")
        if activity_type == _ERROR_CORRECTION_TYPE:
            continue
        activity_id = str(activity.get("id") or "")
        items = activity.get("items")
        if isinstance(items, list):
            for item_idx, item in enumerate(items):
                texts = _negative_example_candidate_texts(activity_type, item)
                findings.extend(_negative_example_findings(activity_id, item_idx, texts))
        else:
            texts = _negative_example_candidate_texts(activity_type, activity)
            findings.extend(_negative_example_findings(activity_id, None, texts))
    return findings


def _negative_example_candidate_texts(activity_type: str, item: Any) -> list[str]:
    if activity_type == "true-false":
        if isinstance(item, dict) and isinstance(item.get("statement"), str):
            return [item["statement"]]
        return []
    return _walk_yaml_strings(item)


def _walk_yaml_strings(node: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(node, dict):
        for child in node.values():
            strings.extend(_walk_yaml_strings(child))
    elif isinstance(node, list):
        for child in node:
            strings.extend(_walk_yaml_strings(child))
    elif isinstance(node, str):
        strings.append(node)
    return strings


def _negative_example_findings(
    activity_id: str,
    item_idx: int | None,
    texts: list[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    seen: set[tuple[int | None, str]] = set()
    for text in texts:
        for form in _negative_example_tail_forms(text):
            key = (item_idx, form)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                {
                    "activity_id": activity_id,
                    "item_idx": item_idx,
                    "form": form,
                    "hint": (f"Wrap the negative example as <!-- bad -->{form}<!-- /bad -->."),
                }
            )
    return findings


def _build_vesum_text(
    module_text: str,
    activities: list[dict[str, Any]],
    vocabulary: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    *,
    level: str | None = None,
    emit_negative_example_events: bool = False,
) -> str:
    """Compose the text blob that VESUM verifies, with structural exclusions."""
    strip_verbatim_primaries = _vesum_heritage_attestation_enabled(level)
    verified_primary_texts: list[str] = []
    if strip_verbatim_primaries:
        verified_primary_texts = _quote_fidelity_verified_blockquote_texts(
            module_text,
            level=level,
        )
        module_text = _strip_quote_fidelity_verified_blockquotes(module_text, level=level)
    verified_primary_token_keys = _verified_primary_token_keys(verified_primary_texts)
    if strip_verbatim_primaries:
        module_text = _strip_verified_primary_bare_citations(
            module_text,
            verified_primary_token_keys=verified_primary_token_keys,
        )
        module_text = _strip_primary_reading_blocks(module_text)
    parts = [_strip_metalinguistic(module_text)]
    strip_activity_field: Callable[[str], str] | None = None
    if strip_verbatim_primaries:

        def strip_activity_field(value: str) -> str:
            value = _strip_vesum_verbatim_primary_spans(
                value,
                level=level,
                verified_primary_texts=verified_primary_texts,
            )
            return _strip_verified_primary_bare_citations(
                value,
                verified_primary_token_keys=verified_primary_token_keys,
            )

    for activity in activities:
        activity_text = _activity_vesum_text(
            activity,
            emit_negative_example_events=emit_negative_example_events,
            string_transform=strip_activity_field,
        )
        parts.append(_strip_metalinguistic(activity_text))
    for entry in vocabulary:
        if isinstance(entry, dict):
            parts.append(_strip_metalinguistic(str(entry.get("lemma", ""))))
            usage = _strip_usage_parentheticals(str(entry.get("usage", "")))
            if strip_verbatim_primaries:
                usage = _strip_vesum_verbatim_primary_spans(
                    usage,
                    level=level,
                    verified_primary_texts=verified_primary_texts,
                )
                usage = _strip_verified_primary_bare_citations(
                    usage,
                    verified_primary_token_keys=verified_primary_token_keys,
                )
            parts.append(_strip_metalinguistic(usage))
    for entry in resources:
        if isinstance(entry, dict):
            parts.append(_strip_metalinguistic(str(entry.get("title", ""))))
            # Resource `notes` field is descriptive metadata (textbook
            # attribution, sourcing context) — proper-noun inflections
            # like "за Ларисою Ніцою" trip VESUM with false positives.
            # The notes field is NOT learner-facing content. Skip from
            # VESUM scope. Keep title / lemma / usage in scope (#2098).
    return "\n".join(part for part in parts if part)


def _activity_vesum_text(
    activity: dict[str, Any],
    *,
    emit_negative_example_events: bool = False,
    string_transform: Callable[[str], str] | None = None,
) -> str:
    """Walk an activity's string values, excluding intentional-error fields.

    For `error-correction` activities, fields like `error:`, `errorWord:`,
    and `sentence:` hold the typo the student must fix; verifying them against
    VESUM would always fail. The skip is at the dict (subtree) level so even a
    future nested shape like `error: { text: "...", note: "..." }` would be
    entirely excluded.

    For multiple-choice-style `options: [{text, correct}]` lists, verify distractors
    by default. Only skip the `text` leaf of options explicitly marked with
    `intentional_error: true`.

    For fill-in activities, bare-list `options:` values are suffix fragments,
    not VESUM lemmas, and are unconditionally skipped.

    For true-false activities, false statements are intentional wrong claims
    and may contain fabricated Ukrainian forms. Only true statements are
    verified; missing answers fail soft by skipping the statement. True
    statements also get a narrow safety net for sentence-final negative examples
    like ``X, а не дивюся.`` where the tail is named as wrong teaching content.

    For highlight-morphemes activities, `morphemes:` is an answer key of bare
    sub-word units. Skip that subtree while keeping `text:`, `word:`, title,
    and instruction strings in VESUM scope.

    When supplied, `string_transform` runs on each retained string leaf before
    flattening so transforms cannot match across separate YAML fields.
    """
    activity_type = activity.get("type")
    activity_id = str(activity.get("id") or "")
    skip_subtree: set[str] = set()
    if activity_type == _ERROR_CORRECTION_TYPE:
        skip_subtree.update(_ERROR_CORRECTION_INTENTIONAL_FIELDS)
    if activity_type == _HIGHLIGHT_MORPHEMES_TYPE:
        skip_subtree.update(_HIGHLIGHT_MORPHEMES_ANSWER_KEY_FIELDS)

    out: list[str] = []

    def walk_truefalse_statement(
        statement: Any,
        answer: Any,
        *,
        item_idx: int | None = None,
    ) -> None:
        if answer is True:
            if isinstance(statement, str):
                original_statement = statement
                statement, skipped_forms = _strip_truefalse_negative_examples(statement)
                if skipped_forms and emit_negative_example_events:
                    emit_event(
                        "vesum_verified_negative_example_stripped",
                        activity_id=activity_id,
                        item_idx=item_idx,
                        forms=skipped_forms,
                        statement_preview=_clean_telemetry_text(
                            original_statement,
                            180,
                        ),
                    )
            walk(statement, "statement")

    def walk(
        node: Any,
        parent_key: str | None,
        *,
        in_options_list: bool = False,
        item_idx: int | None = None,
    ) -> None:
        if isinstance(node, dict):
            intentional_error_option = (
                in_options_list
                and isinstance(node.get("text"), str)
                and node.get("intentional_error") is True
            )
            for key, child in node.items():
                if key in skip_subtree:
                    continue
                if activity_type == "fill-in" and key == "options":
                    continue
                if activity_type == "fill-in" and key == "answer":
                    # Fill-in answers are morphological suffix fragments by
                    # design (e.g. -юся, -ються, -єшся) — they are never
                    # standalone VESUM lemmas. #1963 skipped them only when
                    # the answer was also listed in `options:`; in build #4
                    # (m20 a1-m15-24 contract) the writer emits fill-in items
                    # with a `sentence` + `answer` pair and no `options` list,
                    # so the conditional skip didn't fire. The pedagogical
                    # rationale doesn't change with shape: a fill-in answer
                    # is always a suffix fragment.  Skip unconditionally.
                    # See #1967.
                    continue
                if activity_type == "true-false" and key == "statement":
                    walk_truefalse_statement(
                        child,
                        node.get("answer"),
                        item_idx=item_idx,
                    )
                    continue
                if intentional_error_option and key == "text":
                    continue
                walk(child, key, item_idx=item_idx)
        elif isinstance(node, list):
            for index, item in enumerate(node):
                child_item_idx = index if activity_type == "true-false" and parent_key == "items" else item_idx
                walk(
                    item,
                    parent_key,
                    in_options_list=parent_key == "options",
                    item_idx=child_item_idx,
                )
        elif isinstance(node, str):
            out.append(string_transform(node) if string_transform else node)

    walk(activity, None)
    return "\n".join(out)


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
        detections = []
        hits = []
        for pattern in patterns:
            matches = sorted({match.group(0) for match in re.finditer(pattern, lower)})
            if matches:
                hits.append(pattern)
                detections.extend({"pattern": pattern, "text": match} for match in matches)
        results[field] = {
            "passed": not hits,
            "hits": sorted(hits),
            "detections": detections,
        }
    return results


def _formatting_standards_gate(text: str) -> dict[str, Any]:
    """Check markdown callout syntax required by linear module formatting."""
    malformed_callouts = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if re.search(r"\[![A-Za-z][\w-]*\]", line) and not re.match(r"^\s*>\s*\[![A-Za-z][\w-]*\]", line):
            malformed_callouts.append({"line": line_no, "text": line.strip()})
    missing_mandatory = []
    if re.search(r"\bmodel[_ -]?answer\b", text, flags=re.IGNORECASE) and not re.search(
        r"^\s*>\s*\[!model-answer\]", text, flags=re.MULTILINE
    ):
        missing_mandatory.append("> [!model-answer]")
    return {
        "passed": not malformed_callouts and not missing_mandatory,
        "malformed_callouts": malformed_callouts,
        "missing_mandatory_callouts": missing_mandatory,
    }


_SCAFFOLDING_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
# Gate flags only the UKRAINIAN step labels (Крок/Урок) — the observed leak class
# is Ukrainian wiki-manifest scaffolding. English "Step N:" is intentionally NOT
# flagged here: it can appear in legitimate English pedagogical prose (e.g. a
# how-to sequence), and the source-marker check below already catches the
# unambiguous `[SN]` signature that accompanies a real leak. (The writer-prompt
# sanitizer still strips English "Step N:" defensively; this is the published-
# prose detector, where a false positive blocks a real build.)
_SCAFFOLDING_STEP_LABEL_RE = re.compile(
    r"(?:Крок|Урок)\s+\d+\s*:",
    re.IGNORECASE,
)
_SCAFFOLDING_SOURCE_MARKER_RE = re.compile(
    r"\[[SС]\d+(?:\s*,\s*[SС]\d+)*\]"
)
# Internal pipeline artifacts that must NEVER be named in learner-facing prose.
# These are writer-only build objects (the wiki Knowledge Packet, the
# implementation map, the wiki manifest); a learner is never told a rule "comes
# from the Knowledge Packet". Build-#6 a1/my-morning tone REVISE (2026-05-29) hung
# on a single body-prose leak the LLM tone reviewer caught but python_qg did not:
# "These rules come from the Knowledge Packet's phonetic obligations for this
# module." (#R-NO-SCAFFOLDING-LEAKS). These phrases have NO legitimate learner-
# content use at any CEFR level, so the regex is high-precision by design (cf. the
# step-label note above about avoiding false positives on real prose). VERIFY-
# comment / fenced-code references — e.g. `<!-- VERIFY: source="Knowledge Packet:
# ..." -->` — are already excluded upstream by _strip_scaffolding_scan_exclusions,
# so honest in-comment provenance citations do NOT trip this gate. The inter-word
# separator is `[\s_-]+` so the snake_case identifier forms these artifacts carry
# in the codebase (knowledge_packet.md, implementation_map.json, wiki_manifest.json)
# leak just as the spaced display forms do (gemini-code-assist review, PR #2417).
_SCAFFOLDING_ARTIFACT_RE = re.compile(
    r"\b(?:knowledge[\s_-]+packet|implementation[\s_-]+map|wiki[\s_-]+manifest|wiki[\s_-]+coverage[\s_-]+gate)\b",
    re.IGNORECASE,
)


def _line_preserving_blank(match: re.Match[str]) -> str:
    return "\n" * match.group(0).count("\n")


def _strip_scaffolding_scan_exclusions(text: str) -> str:
    text = _SCAFFOLDING_COMMENT_RE.sub(_line_preserving_blank, text)
    lines: list[str] = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            lines.append("\n" if line.endswith("\n") else "")
            is_just_backticks = not stripped.rstrip().strip("`")
            single_line_fence = (
                not is_just_backticks and stripped.rstrip().endswith("```")
            )
            if not single_line_fence:
                in_fence = not in_fence
            continue
        if in_fence:
            lines.append("\n" if line.endswith("\n") else "")
            continue
        lines.append(line)
    return "".join(lines)


def _scaffolding_leak_gate(text: str) -> dict[str, Any]:
    """Fail when writer-only wiki scaffolding leaks into published prose."""
    scan_text = _strip_scaffolding_scan_exclusions(text)
    offending = []
    for line_no, line in enumerate(scan_text.splitlines(), start=1):
        if (
            _SCAFFOLDING_STEP_LABEL_RE.search(line)
            or _SCAFFOLDING_SOURCE_MARKER_RE.search(line)
            or _SCAFFOLDING_ARTIFACT_RE.search(line)
        ):
            offending.append({"line": line_no, "text": line.strip()})
    return {"passed": not offending, "offending": offending}


def _normalize_citation_ref(value: Any) -> str:
    return normalize_citation_ref(value)


def _normalize_citation_match_text(value: Any) -> str:
    normalized = _normalize_citation_ref(value).casefold()
    return re.sub(r"[^\wа-яіїєґА-ЯІЇЄҐ]+", "", normalized)


def _citation_match_tokens(value: Any) -> list[str]:
    return [token.text for token in _textbook_match_token_spans(_normalize_citation_ref(value))]


def _citation_token_sequence_contains(needle: Sequence[str], haystack: Sequence[str]) -> bool:
    return _citation_token_sequence_start(needle, haystack) is not None


def _citation_token_sequence_start(needle: Sequence[str], haystack: Sequence[str]) -> int | None:
    if not needle or len(needle) > len(haystack):
        return None
    needle_tuple = tuple(needle)
    for start in range(0, len(haystack) - len(needle_tuple) + 1):
        if tuple(haystack[start : start + len(needle_tuple)]) == needle_tuple:
            return start
    return None


def _citation_ref_text_contains(reference_title: str, text: str) -> bool:
    return _citation_token_sequence_contains(
        _citation_match_tokens(reference_title),
        _citation_match_tokens(text),
    )


_CITATION_CONTAINMENT_MIN_CHARS = 8
_CITATION_TITLE_OPEN_QUOTES = ("«", "“", "„", '"')


def _citation_ref_specific_enough_for_containment(reference_title: Any) -> bool:
    normalized_ref = _normalize_citation_match_text(reference_title)
    return (
        len(normalized_ref) >= _CITATION_CONTAINMENT_MIN_CHARS
        and len(_citation_match_tokens(reference_title)) >= 2
    )


def _citation_author_tokens(author: Any) -> list[str]:
    return [
        token
        for token in _citation_match_tokens(author)
        if not re.fullmatch(r"[a-zа-яіїєґ]", token)
    ]


def _citation_folded_author_tokens(author: Any) -> list[str]:
    return [
        folded
        for token in _citation_author_tokens(author)
        if (folded := fold_citation_author(token))
    ]


def _citation_author_anchor_tokens(author: Any, author_tokens: Sequence[str]) -> set[str]:
    distinctive = [token for token in author_tokens if len(token) >= 4 and not token.isdigit()]
    if not distinctive:
        return set()
    if len(distinctive) == 1:
        return {distinctive[0]}
    if "," in str(author):
        return {distinctive[0]}
    return {distinctive[-1]}


def _citation_author_appears_in_source_tokens(
    author: Any,
    source_author_tokens: Sequence[str],
) -> bool:
    author_tokens = _citation_author_tokens(author)
    if _citation_token_sequence_contains(author_tokens, source_author_tokens):
        return True
    author_anchors = _citation_author_anchor_tokens(author, author_tokens)
    if author_anchors & set(source_author_tokens):
        return True

    folded_source_tokens = [
        folded
        for token in source_author_tokens
        if (folded := fold_citation_author(token))
    ]
    folded_author_tokens = _citation_folded_author_tokens(author)
    if _citation_token_sequence_contains(folded_author_tokens, folded_source_tokens):
        return True
    folded_author_anchors = _citation_author_anchor_tokens(author, folded_author_tokens)
    return bool(folded_author_anchors & set(folded_source_tokens))


def _citation_first_title_open_quote_index(source_ref: str) -> int | None:
    quote_indexes = [
        index
        for quote in _CITATION_TITLE_OPEN_QUOTES
        if (index := source_ref.find(quote)) != -1
    ]
    if not quote_indexes:
        return None
    return min(quote_indexes)


def _citation_author_slot_text(source_ref: str) -> str | None:
    title_slot_start = _citation_first_title_open_quote_index(source_ref)
    if title_slot_start is None:
        return None
    return source_ref[:title_slot_start]


def _citation_source_author_tokens(
    reference_title: Any,
    source_ref: str,
) -> list[str] | None:
    title_tokens = _citation_match_tokens(reference_title)
    normalized_source_ref = _normalize_citation_ref(source_ref)
    first_title_quote = _citation_first_title_open_quote_index(normalized_source_ref)
    if first_title_quote is None:
        return None
    source_token_spans = _textbook_match_token_spans(normalized_source_ref)
    source_tokens = [token.text for token in source_token_spans]
    title_start = _citation_token_sequence_start(title_tokens, source_tokens)
    if title_start is None:
        return None
    if source_token_spans[title_start].start <= first_title_quote:
        return None
    author_slot = _citation_author_slot_text(normalized_source_ref)
    if author_slot is None:
        return None
    return _citation_match_tokens(author_slot)


def _citation_author_appears_in_source(
    author: Any,
    reference_title: Any,
    source_ref: str,
) -> bool:
    source_author_tokens = _citation_source_author_tokens(
        reference_title,
        source_ref,
    )
    if source_author_tokens is None:
        return False
    return _citation_author_appears_in_source_tokens(
        author,
        source_author_tokens,
    )


def _citation_plan_reference_records(plan: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    references = plan.get("references")
    if references is None:
        references = plan.get("plan_references", [])
    if not isinstance(references, list):
        return []
    return [
        ref
        for ref in references
        if isinstance(ref, Mapping) and (ref.get("title") or ref.get("work"))
    ]


def _citation_ref_resolves_by_containment(
    reference: Mapping[str, Any],
    source_ref: str,
) -> bool:
    reference_title = str(reference.get("title") or reference.get("work") or "")
    if not (
        _citation_ref_specific_enough_for_containment(reference_title)
        and _citation_ref_text_contains(reference_title, source_ref)
    ):
        return False

    author = str(reference.get("author") or "").strip()
    if author:
        return _citation_author_appears_in_source(author, reference_title, source_ref)
    return False


_ANONYMOUS_FOLK_PRIMARY_MARKERS = (
    "народна творчість",
    "фольклорний запис",
    "народна пісня",
    "усна народна творчість",
)
_QUOTED_CITATION_TITLE_RE = re.compile(
    r"«(?P<guillemet>[^»\n]{3,240})»"
    r'|"(?P<double>[^"\n]{3,240})"'
    r"|“(?P<curly>[^”\n]{3,240})”"
)
_ANONYMOUS_PRIMARY_MIN_TITLE_TOKENS = 3
_ANONYMOUS_FOLK_AUTHOR_MARKERS = frozenset(
    {
        "народна творчість",
        "народна пісня",
        "народні пісні",
        "народна дума",
        "народні думи",
        "народна казка",
        "народна балада",
        "фольклор",
        "фольклорний запис",
        "усна народна творчість",
    }
)
_ANONYMOUS_FOLK_METADATA_FIELDS = (
    "author",
    "authors",
    "creator",
    "contributors",
    "attribution",
    "title",
    "work",
    "source_ref",
    "source",
    "source_file",
    "genre",
    "corpus",
    "unit_key",
)


def _quoted_citation_titles(text: str) -> list[str]:
    titles: list[str] = []
    for match in _QUOTED_CITATION_TITLE_RE.finditer(text):
        for group_name in ("guillemet", "double", "curly"):
            title = match.group(group_name)
            if title:
                titles.append(title.strip())
                break
    return titles


def _primary_excerpt_resolves_against_source(excerpt: str, source_text: str) -> bool:
    excerpt_tokens = _textbook_match_token_spans(excerpt)
    if len(excerpt_tokens) < _ANONYMOUS_PRIMARY_MIN_TITLE_TOKENS:
        return False
    return bool(
        _matching_token_spans(
            excerpt,
            source_text,
            min_words=len(excerpt_tokens),
        )
    )


def _anonymous_folk_metadata_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return " ".join(_anonymous_folk_metadata_text(child) for child in value.values())
    if isinstance(value, list | tuple | set):
        return " ".join(_anonymous_folk_metadata_text(child) for child in value)
    return str(value or "")


def _has_anonymous_folk_marker(text: str) -> bool:
    folded = text.casefold()
    return any(marker in folded for marker in _ANONYMOUS_FOLK_AUTHOR_MARKERS)


def _authorship_text_is_only_anonymous_folk(text: str) -> bool:
    if not text.strip():
        return True
    if not _has_anonymous_folk_marker(text):
        return False
    remainder = _QUOTED_CITATION_TITLE_RE.sub(" ", text).casefold()
    for marker in sorted(_ANONYMOUS_FOLK_AUTHOR_MARKERS, key=len, reverse=True):
        remainder = remainder.replace(marker, " ")
    return not re.findall(r"[A-Za-zА-ЯІЇЄҐа-яіїєґ]{2,}", remainder)


def _metadata_authorship_is_anonymous_folk(candidate: Mapping[str, Any]) -> bool:
    metadata_text = " ".join(
        _anonymous_folk_metadata_text(candidate.get(field))
        for field in _ANONYMOUS_FOLK_METADATA_FIELDS
    )
    if not _has_anonymous_folk_marker(metadata_text):
        return False

    author_text = " ".join(
        _anonymous_folk_metadata_text(candidate.get(field))
        for field in ("author", "authors", "creator", "contributors", "attribution")
    ).strip()
    return _authorship_text_is_only_anonymous_folk(author_text)


def _anonymous_folk_primary_citation_resolves(
    resource: Mapping[str, Any],
    source_ref: str,
    *,
    module_text: str,
    level: str | None,
) -> bool:
    level_key = str(level or "").strip().casefold()
    if level_key not in SEMINAR_LEVELS:
        return False

    marker_text = " ".join(
        str(resource.get(field) or "")
        for field in ("source_ref", "title")
    )
    marker_text = f"{marker_text} {source_ref}".casefold()
    if not any(marker in marker_text for marker in _ANONYMOUS_FOLK_PRIMARY_MARKERS):
        return False

    quoted_titles = _quoted_citation_titles(source_ref) or _quoted_citation_titles(marker_text)
    if not quoted_titles:
        return False

    verified_primary_records = (
        [
            record
            for record in _extract_blockquote_records(module_text, level=level_key)
            if _blockquote_record_is_quote_fidelity_verified(record)
            and _metadata_authorship_is_anonymous_folk(record)
        ]
        if module_text
        else []
    )
    for title in quoted_titles:
        if any(
            _primary_excerpt_resolves_against_source(title, str(record.get("quote") or ""))
            for record in verified_primary_records
        ):
            return True
        for hit in _search_literary_hits(title, level=level_key, limit=20):
            if not _metadata_authorship_is_anonymous_folk(hit):
                continue
            hit_text = _result_text_for_match(hit)
            if hit_text and _primary_excerpt_resolves_against_source(title, hit_text):
                return True

    return False


def _citation_gate(
    resources: list[dict[str, Any]],
    plan: Mapping[str, Any],
    *,
    module_text: str = "",
    level: str | None = None,
) -> dict[str, Any]:
    plan_reference_records = _citation_plan_reference_records(plan)
    plan_reference_titles = [str(ref.get("title") or ref.get("work") or "") for ref in plan_reference_records]
    plan_titles = {_normalize_citation_ref(title) for title in plan_reference_titles}
    plan_keys = {key for title in plan_reference_titles if (key := extract_citation_key(title)) is not None}
    level_key = str(level or plan.get("level") or "").strip().casefold()
    unknown = []
    for resource in resources:
        role = str(resource.get("role") or "textbook").strip()
        if role != "textbook":
            continue
        source_ref = str(resource.get("source_ref") or resource.get("title") or "")
        normalized_ref = _normalize_citation_ref(source_ref)
        source_key = extract_citation_key(source_ref)
        if (
            normalized_ref not in plan_titles
            and (source_key is None or not any(citation_keys_match(source_key, plan_key) for plan_key in plan_keys))
            and not any(
                _citation_ref_resolves_by_containment(reference, source_ref)
                for reference in plan_reference_records
            )
            and resource.get("packet_chunk_id") is None
            and not _anonymous_folk_primary_citation_resolves(
                resource,
                source_ref,
                module_text=module_text,
                level=level_key,
            )
        ):
            unknown.append(source_ref)
    return {"passed": not unknown, "unknown": unknown}


def _plan_reference_match_gate(resources: list[dict[str, Any]], plan: Mapping[str, Any]) -> dict[str, Any]:
    plan_chunk_ids = set()
    has_chunk_ids_in_plan = False

    references = plan.get("references")
    if references is None:
        references = plan.get("plan_references", [])

    if isinstance(references, list):
        for ref in references:
            if isinstance(ref, dict) and "notes" in ref:
                chunk_id = extract_chunk_id_from_notes(ref["notes"])
                if chunk_id:
                    plan_chunk_ids.add(chunk_id)
                    has_chunk_ids_in_plan = True

    if not has_chunk_ids_in_plan and references:
        return {"passed": True, "warnings": ["plan_has_no_chunk_ids_skipping_membership_check"]}

    out_of_plan = []

    for resource in resources:
        role = str(resource.get("role") or "textbook").strip()
        if role != "textbook":
            continue

        cited_chunk_id = resource.get("packet_chunk_id") or resource.get("chunk_id")
        if not cited_chunk_id and "notes" in resource:
            cited_chunk_id = extract_chunk_id_from_notes(resource["notes"])

        if cited_chunk_id and cited_chunk_id not in plan_chunk_ids:
            source_ref = str(resource.get("source_ref") or resource.get("title") or "")
            out_of_plan.append({"source_ref": source_ref, "cited_chunk_id": cited_chunk_id})

    if out_of_plan:
        return {
            "passed": False,
            "severity": "HARD",
            "plan_chunk_ids": sorted(list(plan_chunk_ids)),
            "out_of_plan": out_of_plan,
            "rule_ids": ["#R-CITE-HONEST", "#R-TEXTBOOK-30W"],
            "reason": "resources_cite_chunk_ids_not_in_plan_references",
        }

    return {"passed": True}


def _is_internal_wiki_ref(ref: Mapping[str, Any]) -> bool:
    title = str(ref.get("title") or "").strip().casefold()
    url = str(ref.get("url") or "").strip()
    notes = str(ref.get("notes") or "").strip().casefold()
    return (
        title.startswith("wiki:")
        or url.startswith(("wiki/", "docs/wiki/"))
        or "wiki/" in notes
    )


def _resource_url_set(resources: list[dict[str, Any]]) -> set[str]:
    urls: set[str] = set()
    for resource in resources:
        for field in ("url", "notes", "description"):
            value = resource.get(field)
            if not value:
                continue
            urls.update(re.findall(r"https?://[^\s)>,]+", str(value)))
    return {url.rstrip(".,;") for url in urls}


def _resource_chunk_id(resource: Mapping[str, Any]) -> str:
    chunk_id = resource.get("packet_chunk_id") or resource.get("chunk_id")
    if not chunk_id and "notes" in resource:
        chunk_id = extract_chunk_id_from_notes(str(resource["notes"]))
    return str(chunk_id or "").strip()


def _resource_match_tokens(value: Any) -> set[str]:
    text = str(value or "").casefold()
    text = re.sub(r"\b(?:стор(?:інка)?|p|page|pages|с)\.?\b", " ", text)
    return {
        token
        for token in re.findall(r"[0-9A-Za-zА-Яа-яҐґЄєІіЇї'-]+", text)
        if len(token) >= 3 or token.isdigit()
    }


_RESOURCE_MATCH_STOPWORDS = {
    "буквар",
    "клас",
    "grade",
    "class",
    "season",
    "episode",
}


def _resource_anchor_tokens(value: Any) -> set[str]:
    return {
        token
        for token in _resource_match_tokens(value)
        if not token.isdigit() and token not in _RESOURCE_MATCH_STOPWORDS
    }


def _plan_ref_covered_by_resource(ref: Mapping[str, Any], resource: Mapping[str, Any]) -> bool:
    ref_url = str(ref.get("url") or "").strip()
    if ref_url and ref_url == str(resource.get("url") or "").strip():
        return True

    ref_chunk_id = extract_chunk_id_from_notes(str(ref.get("notes") or ""))
    if ref_chunk_id and ref_chunk_id == _resource_chunk_id(resource):
        return True

    ref_title = str(ref.get("title") or "")
    resource_title = str(resource.get("source_ref") or resource.get("title") or "")
    if not ref_title or not resource_title:
        return False

    if _citation_ref_text_contains(ref_title, resource_title) or _citation_ref_text_contains(resource_title, ref_title):
        return True

    ref_tokens = _resource_match_tokens(ref_title)
    resource_tokens = _resource_match_tokens(resource_title)
    if not ref_tokens or not resource_tokens:
        return False
    overlap = ref_tokens & resource_tokens
    anchor_overlap = _resource_anchor_tokens(ref_title) & _resource_anchor_tokens(resource_title)
    has_name_overlap = any(not token.isdigit() for token in overlap)
    has_page_overlap = any(token.isdigit() for token in overlap)
    return bool(anchor_overlap) and has_name_overlap and (has_page_overlap or len(overlap) >= 3)


def _extract_plan_pronunciation_video_urls(plan: Mapping[str, Any]) -> list[dict[str, str]]:
    videos = plan.get("pronunciation_videos")
    if not isinstance(videos, Mapping):
        return []

    records: list[dict[str, str]] = []

    def add(path: str, value: Any) -> None:
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            records.append({"path": path, "url": value.strip()})

    add("pronunciation_videos.overview", videos.get("overview"))
    add("pronunciation_videos.playlist", videos.get("playlist"))
    for group in ("vowels", "consonants", "special"):
        group_values = videos.get(group)
        if not isinstance(group_values, Mapping):
            continue
        for key, value in group_values.items():
            add(f"pronunciation_videos.{group}.{key}", value)
    return records


_HOSTED_READING_VALUES = frozenset({"host", "hosted"})
_READING_COVERAGE_FLOOR = 4
_READING_COVERAGE_MIN_STRUCTURED = 1
_READING_COVERAGE_MIN_PASSAGE_LINES = 6
_READING_COVERAGE_MIN_PASSAGE_WORDS = 40
_READING_TITLE_STRIP_CHARS = " \t\r\n«»„“”\"'‘’"
_READING_COVERAGE_BLOCK_RE = re.compile(
    r"^:::primary-reading(?P<attrs>[^\n]*)\n(?P<body>.*?)^:::\s*$",
    re.MULTILINE | re.DOTALL,
)
_PRIMARY_READING_SLUG_ATTR_RE = re.compile(r'\breading\s*=\s*"(?P<slug>[^"]+)"')
_PRIMARY_READING_TEXT_PROP_RE = re.compile(
    r"<PrimaryReading\b[^>]*\btext=\{`(?P<text>.*?)`\}\s*/?>",
    re.DOTALL,
)
_PRIMARY_READING_CHILDREN_RE = re.compile(
    r"<PrimaryReading\b[^>]*>\s*(?P<text>.*?)\s*</PrimaryReading>",
    re.DOTALL,
)
_PRIMARY_READING_ATTRIBUTION_MARKERS = (
    "суспільне надбання",
    "public domain",
    "creative commons",
    "cc by",
    "cc-by",
    "джерел",
    "публічн",
    "wikisource",
    "ukrlib",
    "ізборник",
    "енциклопед",
    "збірник",
    "видан",
    "досліджен",
    "корпус",
    "народна творчість",
    "літопис",
    "пісня",
    "фрагмент",
    "свідчення",
    "цитовано",
    "зібрання",
    "твор",
)


def _normalize_reading_title(value: object) -> str:
    text = str(value or "").strip(_READING_TITLE_STRIP_CHARS).casefold()
    return re.sub(r"\s+", " ", text)


def _primary_reading_blocks(module_text: str) -> list[re.Match[str]]:
    return list(_READING_COVERAGE_BLOCK_RE.finditer(module_text))


def _primary_reading_body_lines(block_body: str) -> list[str]:
    lines: list[str] = []
    for line in block_body.splitlines():
        stripped = line.strip()
        while stripped.startswith(">"):
            stripped = stripped[1:].strip()
        lines.append(stripped)
    return lines


def _looks_like_primary_reading_attribution(paragraph: str) -> bool:
    stripped = paragraph.strip()
    if not stripped.startswith(("—", "–", "-")):
        return False
    normalized = stripped.casefold()
    return any(marker in normalized for marker in _PRIMARY_READING_ATTRIBUTION_MARKERS)


def _primary_reading_attribution_indexes(block_body: str) -> set[int]:
    lines = _primary_reading_body_lines(block_body)
    end = len(lines) - 1
    while end >= 0 and not lines[end]:
        end -= 1
    if end < 0:
        return set()

    start = end
    while start >= 0 and not lines[start].startswith(("—", "–", "-")):
        start -= 1
    if start < 0:
        return set()

    paragraph = "\n".join(lines[start : end + 1])
    if not _looks_like_primary_reading_attribution(paragraph):
        return set()
    return set(range(start, end + 1))


def _primary_reading_attribution_lines(block_body: str) -> list[str]:
    lines = _primary_reading_body_lines(block_body)
    return [lines[index] for index in sorted(_primary_reading_attribution_indexes(block_body)) if lines[index]]


def _primary_reading_slug_attrs(blocks: Sequence[re.Match[str]]) -> set[str]:
    return {
        match.group("slug").strip()
        for block in blocks
        for match in _PRIMARY_READING_SLUG_ATTR_RE.finditer(block.group("attrs"))
    }


def _structured_primary_reading_blocks(blocks: Sequence[re.Match[str]]) -> list[re.Match[str]]:
    """Return blocks that are both on-site linked and attributed."""

    structured_blocks: list[re.Match[str]] = []
    for block in blocks:
        if not _primary_reading_attribution_lines(block.group("body")):
            continue
        has_reading_slug = any(
            match.group("slug").strip() for match in _PRIMARY_READING_SLUG_ATTR_RE.finditer(block.group("attrs"))
        )
        if has_reading_slug:
            structured_blocks.append(block)
    return structured_blocks


def _primary_reading_passage_text(block_body: str) -> str:
    passage_lines: list[str] = []
    attribution_indexes = _primary_reading_attribution_indexes(block_body)
    for index, stripped in enumerate(_primary_reading_body_lines(block_body)):
        if not stripped or index in attribution_indexes:
            continue
        passage_lines.append(stripped)
    return "\n".join(passage_lines)


def _reading_passage_counts(text: str) -> tuple[int, int]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    words = re.findall(r"[А-Яа-яІіЇїЄєҐґA-Za-z0-9'’\-]+", text)
    return len(lines), len(words)


def _substantial_reading_passage(text: str) -> bool:
    lines, words = _reading_passage_counts(text)
    return lines >= 2 and (
        lines >= _READING_COVERAGE_MIN_PASSAGE_LINES
        or words >= _READING_COVERAGE_MIN_PASSAGE_WORDS
    )


def _hosted_reading_text(reading_slug: str, readings_dir: Path) -> str:
    if not reading_slug:
        return ""
    path = readings_dir / f"{reading_slug}.mdx"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    match = _PRIMARY_READING_TEXT_PROP_RE.search(text)
    if match:
        return match.group("text")
    match = _PRIMARY_READING_CHILDREN_RE.search(text)
    if not match:
        return ""
    return re.sub(r"<[^>]+>", "", match.group("text"))


def _substantial_structured_primary_readings(
    blocks: Sequence[re.Match[str]],
    readings_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    substantial: list[dict[str, Any]] = []
    too_short: list[dict[str, Any]] = []
    for block in blocks:
        slug_match = next(_PRIMARY_READING_SLUG_ATTR_RE.finditer(block.group("attrs")), None)
        slug = slug_match.group("slug").strip() if slug_match else ""
        inline_text = _primary_reading_passage_text(block.group("body"))
        hosted_text = _hosted_reading_text(slug, readings_dir)
        inline_lines, inline_words = _reading_passage_counts(inline_text)
        hosted_lines, hosted_words = _reading_passage_counts(hosted_text)
        record = {
            "reading_slug": slug,
            "inline_lines": inline_lines,
            "inline_words": inline_words,
            "hosted_lines": hosted_lines,
            "hosted_words": hosted_words,
        }
        if _substantial_reading_passage(inline_text) or _substantial_reading_passage(hosted_text):
            substantial.append(record)
        else:
            too_short.append(record)
    return substantial, too_short


def _hosted_plan_readings(plan: Mapping[str, Any]) -> list[dict[str, str]]:
    readings = plan.get("readings")
    if not isinstance(readings, list):
        return []
    hosted_readings: list[dict[str, str]] = []
    for entry in readings:
        if not isinstance(entry, Mapping):
            continue
        hosting = str(entry.get("hosting") or "").strip().casefold()
        if hosting not in _HOSTED_READING_VALUES:
            continue
        hosted_readings.append(
            {
                "title": str(entry.get("title") or "").strip(),
                "reading_slug": str(entry.get("reading_slug") or "").strip(),
            }
        )
    return hosted_readings


def _reading_coverage_gate(
    module_text: str,
    plan: Mapping[str, Any],
    *,
    readings_dir: Path | None = None,
) -> dict[str, Any]:
    level_key = str(plan.get("level") or "").strip().casefold()
    if level_key not in SEMINAR_LEVELS:
        return {"passed": True, "skipped": "non-seminar"}

    blocks = _primary_reading_blocks(module_text)
    hosted_readings = _hosted_plan_readings(plan)
    normalized_attribution_lines = [
        _normalize_reading_title(line)
        for block in blocks
        for line in _primary_reading_attribution_lines(block.group("body"))
    ]
    reading_slug_attrs = _primary_reading_slug_attrs(blocks)
    structured_blocks = _structured_primary_reading_blocks(blocks)
    structured_reading_slug_attrs = _primary_reading_slug_attrs(structured_blocks)
    readings_dir = readings_dir or PROJECT_ROOT / "site" / "src" / "content" / "readings"
    substantial_readings, short_readings = _substantial_structured_primary_readings(
        structured_blocks,
        readings_dir,
    )
    unstructured_primary_readings = len(blocks) - len(structured_blocks)

    missing: list[dict[str, str]] = []
    matched: list[dict[str, str]] = []
    for reading in hosted_readings:
        normalized_title = _normalize_reading_title(reading["title"])
        slug = reading["reading_slug"]
        matched_by_title = bool(
            normalized_title and any(normalized_title in line for line in normalized_attribution_lines)
        )
        matched_by_slug = bool(slug and f"/readings/{slug}/" in module_text)
        # Source modules can surface generated hosted readings before MDX conversion
        # as a primary-reading directive attribute rather than a rendered link.
        matched_by_directive_attr = bool(slug and slug in reading_slug_attrs)
        matched_by_structured_directive = bool(slug and slug in structured_reading_slug_attrs)
        matched_by_on_site_reading = matched_by_structured_directive
        if level_key != "folk":
            matched_by_on_site_reading = matched_by_title or matched_by_slug or matched_by_directive_attr
        if matched_by_on_site_reading:
            matched_by = "title"
            if matched_by_structured_directive:
                matched_by = "structured_primary_reading"
            elif matched_by_slug:
                matched_by = "reading_link"
            elif matched_by_directive_attr:
                matched_by = "primary_reading_attr"
            matched.append({**reading, "matched_by": matched_by})
        else:
            missing.append(reading)

    missing_on_site_reading = level_key == "folk" and len(structured_reading_slug_attrs) < _READING_COVERAGE_MIN_STRUCTURED
    missing_substantial_reading = level_key == "folk" and len(substantial_readings) < _READING_COVERAGE_MIN_STRUCTURED
    has_unstructured_readings = level_key == "folk" and unstructured_primary_readings > 0
    passed = not missing and not missing_on_site_reading and not missing_substantial_reading and not has_unstructured_readings
    report: dict[str, Any] = {
        "passed": passed,
        "severity": "HARD" if not passed else None,
        "checked": len(hosted_readings),
        "surfaced_primary_readings": len(blocks),
        "structured_on_site_readings": len(structured_blocks),
        "substantial_on_site_readings": len(substantial_readings),
        "unstructured_primary_readings": unstructured_primary_readings,
        "matched_hosted_readings": matched,
        "missing_hosted_readings": missing,
        "short_structured_readings": short_readings,
    }
    if missing_on_site_reading:
        report["missing_on_site_reading"] = {
            "severity": "HARD",
            "message": (
                "FOLK modules require at least one structured on-site "
                'primary-reading block with a reading="..." slug and attribution; '
                "external link-only resources and orphan inline snippets are supplementary only"
            ),
            "expected_minimum": _READING_COVERAGE_MIN_STRUCTURED,
        }
    if missing_substantial_reading:
        report["missing_substantial_reading"] = {
            "severity": "HARD",
            "message": (
                "FOLK modules require at least one structured on-site reading "
                "with a real shortened passage, not a one-line/token quote"
            ),
            "expected_minimum": _READING_COVERAGE_MIN_STRUCTURED,
            "minimum_lines": _READING_COVERAGE_MIN_PASSAGE_LINES,
            "minimum_words": _READING_COVERAGE_MIN_PASSAGE_WORDS,
        }
    if has_unstructured_readings:
        report["unstructured_reading_failure"] = {
            "severity": "HARD",
            "message": (
                "FOLK primary-reading blocks must include a reading=\"...\" slug "
                "and dash-led source attribution; orphan snippets are not valid reading content"
            ),
            "count": unstructured_primary_readings,
        }

    exception = str(plan.get("reading_coverage_exception") or "").strip()
    if len(blocks) < _READING_COVERAGE_FLOOR and not exception:
        report["warning"] = {
            "severity": "WARNING",
            "message": (
                "fewer than 4 primary-reading blocks surfaced; floor is advisory "
                "and does not affect gate pass/fail"
            ),
            "surfaced": len(blocks),
            "expected_minimum": _READING_COVERAGE_FLOOR,
        }
    return report


def _resource_coverage_gate(
    resources: list[dict[str, Any]],
    plan: Mapping[str, Any],
    wiki_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Ensure A1 M1-M7 required sources and media are canonical resources."""
    contract = resolve_module_archetype(str(plan.get("level") or ""), int(plan.get("sequence") or 0))
    if not _is_a1_m1_m7_archetype(contract):
        return {"passed": True, "skipped": "not_a1_m1_m7_archetype"}

    references = plan.get("references") or plan.get("plan_references") or []
    missing_plan_references: list[dict[str, Any]] = []
    skipped_internal_references: list[str] = []
    if isinstance(references, list):
        for ref in references:
            if not isinstance(ref, Mapping):
                continue
            if _is_internal_wiki_ref(ref):
                skipped_internal_references.append(str(ref.get("title") or ""))
                continue
            if any(_plan_ref_covered_by_resource(ref, resource) for resource in resources):
                continue
            missing_plan_references.append(
                {
                    "title": str(ref.get("title") or ""),
                    "url": str(ref.get("url") or ""),
                    "notes": str(ref.get("notes") or ""),
                }
            )

    resource_urls = _resource_url_set(resources)
    missing_pronunciation_videos = [
        record
        for record in _extract_plan_pronunciation_video_urls(plan)
        if record["url"] not in resource_urls
    ]

    missing_wiki_external_resources: list[dict[str, Any]] = []
    if wiki_manifest is not None:
        external_resources = wiki_manifest.get("external_resources", [])
        if isinstance(external_resources, list):
            for resource in external_resources:
                if not isinstance(resource, Mapping):
                    continue
                url = str(resource.get("url") or "").strip()
                if url and url not in resource_urls:
                    missing_wiki_external_resources.append(
                        {
                            "title": str(resource.get("title") or ""),
                            "role": str(resource.get("role") or ""),
                            "url": url,
                        }
                    )

    passed = not (
        missing_plan_references
        or missing_pronunciation_videos
        or missing_wiki_external_resources
    )
    return {
        "passed": passed,
        "severity": "HARD" if not passed else None,
        "missing_plan_references": missing_plan_references,
        "missing_pronunciation_videos": missing_pronunciation_videos,
        "missing_wiki_external_resources": missing_wiki_external_resources,
        "skipped_internal_references": skipped_internal_references,
        "rule_ids": ["#R-CITE-HONEST", "#R-RESOURCE-COVERAGE"] if not passed else [],
    }


def _extract_blockquote_records(text: str, *, level: str | None = None) -> list[dict[str, Any]]:
    quotes: list[dict[str, Any]] = []
    current_section = ""
    level_key = str(level or "").strip().lower()
    lines = text.splitlines()
    no_verify = False
    i = 0

    while i < len(lines):
        line = lines[i]
        # Track only H1/H2 as the blockquote's `section_title` — the
        # `_textbook_grounding_gate`'s `_quote_topic_matches` check uses
        # this string as the topic context, and sub-headings (H3+) are
        # typically step/sub-step markers (e.g. `### Крок N: ...`) whose
        # pedagogy-meta-talk lexicon poisons the token set. The H2 is
        # the actual learner-navigable section that defines the topic.
        # Build-#7 a1/my-morning regression: writer used H3 ### Крок N
        # (pedagogically clearer than inline-bold) and the gate
        # rejected real Захарійчук blockquotes for topical_mismatch
        # because the H3 stems didn't overlap with concrete-content
        # quotes. See `tests/test_textbook_grounding_gate.py::
        # test_blockquote_under_h3_inherits_h2_section_title`.
        heading = re.match(r"^\s{0,3}#{1,2}\s+(?P<title>.+?)\s*#*\s*$", line)
        if heading:
            current_section = re.sub(r"[*_`~]+", "", heading.group("title")).strip()

        if re.match(r"^\s*<!--\s*NO_VERIFY:", line):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip().startswith(">"):
                no_verify = True
            i += 1
            continue

        match = re.match(r"^\s*>\s?(?P<body>.*)$", line)
        if match is None:
            i += 1
            continue

        content = match.group("body").strip()
        if content.startswith("[!"):
            while i < len(lines) and re.match(r"^\s*>\s?(?P<body>.*)$", lines[i]):
                i += 1
            continue

        quote_lines: list[str] = []
        line_numbers: list[int] = []
        quote_section = current_section
        while i < len(lines):
            quote_match = re.match(r"^\s*>\s?(?P<body>.*)$", lines[i])
            if quote_match is None:
                break
            quote_lines.append(quote_match.group("body"))
            line_numbers.append(i)
            i += 1

        if level_key in SEMINAR_LEVELS:
            quote_text, embedded_attr = _extract_embedded_blockquote_attribution(quote_lines)
        else:
            quote_text = "\n".join(quote_lines).strip()
            embedded_attr = ""

        attr_line = embedded_attr
        j = i
        if j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines):
            attr = _extract_textbook_attribution(lines[j])
            if attr:
                attr_line = attr

        if quote_text:
            quotes.append(
                {
                    "quote": quote_text,
                    "section_title": quote_section,
                    "attribution": attr_line,
                    "no_verify": no_verify,
                    "line_numbers": line_numbers,
                }
            )
        no_verify = False

    return quotes


def _extract_blockquotes(text: str) -> list[str]:
    return [record["quote"] for record in _extract_blockquote_records(text)]


def _extract_embedded_blockquote_attribution(quote_lines: list[str]) -> tuple[str, str]:
    lines_without_attr = list(quote_lines)
    while lines_without_attr and not lines_without_attr[-1].strip():
        lines_without_attr.pop()
    if not lines_without_attr:
        return "", ""

    possible_attribution = lines_without_attr[-1].strip()
    if not possible_attribution.startswith(("*", "_", "`", "~")):
        return "\n".join(quote_lines).strip(), ""

    attribution = _extract_textbook_attribution(possible_attribution)
    if not attribution:
        return "\n".join(quote_lines).strip(), ""

    lines_without_attr.pop()
    while lines_without_attr and not lines_without_attr[-1].strip():
        lines_without_attr.pop()
    return "\n".join(lines_without_attr).strip(), attribution


def _blockquote_record_is_quote_fidelity_verified(record: Mapping[str, Any]) -> bool:
    return bool(record.get("quote") and record.get("attribution") and not record.get("no_verify"))


def _quote_fidelity_verified_blockquote_texts(text: str, *, level: str | None) -> list[str]:
    return [
        str(record["quote"])
        for record in _extract_blockquote_records(text, level=level)
        if _blockquote_record_is_quote_fidelity_verified(record)
    ]


def _strip_quote_fidelity_verified_blockquotes(text: str, *, level: str | None) -> str:
    records = _extract_blockquote_records(text, level=level)
    quote_line_numbers = {
        line_number
        for record in records
        if _blockquote_record_is_quote_fidelity_verified(record)
        for line_number in record.get("line_numbers", ())
        if isinstance(line_number, int)
    }
    if not quote_line_numbers:
        return text
    return "\n".join(
        line for index, line in enumerate(text.splitlines()) if index not in quote_line_numbers
    )


def _extract_textbook_attribution(line: str) -> str:
    stripped = line.strip().strip("*_`~ ")
    match = re.match(r"^[—–-]\s*(?P<body>.+?)\s*$", stripped)
    if match is None:
        return ""
    return match.group("body").strip().strip("*_`~ ")


def _normalize_match_text(text: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", text)
    text = text.replace("\xad", "")
    text = re.sub(
        r"(?<=[A-Za-zА-Яа-яҐґЄєІіЇї])-\s+(?=[A-Za-zА-Яа-яҐґЄєІіЇї])",
        "",
        text,
    )
    text = text.replace("’", "'").replace("ʼ", "'")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _textbook_match_tokens(text: str) -> list[str]:
    text = _normalize_match_text(text)
    text = re.sub(r"[*_`~#>|]", " ", text)
    tokens = re.findall(r"[0-9A-Za-zА-Яа-яҐґЄєІіЇї'-]+", text.casefold())
    # Symmetric syllable-break normalization (see #2084 + writer-prompt §2
    # "Textbook syllable-break notation"). The writer is instructed to strip
    # pedagogical syllable hyphens like `за-пи-са-ний` → `записаний` before
    # pasting a quote. The textbook chunk text itself usually KEEPS those
    # hyphens, so without symmetric stripping on both sides the writer's
    # clean quote fails to match the hyphenated chunk. Applying
    # `_collapse_syllable_break` here makes the match work regardless of
    # whether the writer stripped or copied verbatim.
    return [_collapse_syllable_break(token) for token in tokens]


def _contains_textbook_quote(blockquote: str, result_text: str) -> bool:
    quote_tokens = _textbook_match_tokens(blockquote)
    if len(quote_tokens) < TEXTBOOK_GROUNDING_MIN_WORDS:
        return False
    result_blob = " ".join(_textbook_match_tokens(result_text))
    if not result_blob:
        return False
    for start in range(0, len(quote_tokens) - TEXTBOOK_GROUNDING_MIN_WORDS + 1):
        window = " ".join(quote_tokens[start : start + TEXTBOOK_GROUNDING_MIN_WORDS])
        if window in result_blob:
            return True
    return False


_MATCH_TOKEN_WITH_SPAN_RE = re.compile(
    r"[0-9A-Za-zА-Яа-яҐґЄєІіЇї][0-9A-Za-zА-Яа-яҐґЄєІіЇї'’ʼ-]*"
)


@dataclass(frozen=True)
class _MatchToken:
    text: str
    start: int
    end: int


def _match_token_key(token: str) -> str:
    normalized = _normalize_match_text(token)
    normalized = re.sub(r"[*_`~#>|]", " ", normalized)
    pieces = re.findall(r"[0-9A-Za-zА-Яа-яҐґЄєІіЇї'-]+", normalized.casefold())
    if not pieces:
        return ""
    return _collapse_syllable_break("".join(pieces))


def _textbook_match_token_spans(text: str) -> list[_MatchToken]:
    tokens: list[_MatchToken] = []
    for match in _MATCH_TOKEN_WITH_SPAN_RE.finditer(text):
        token = _match_token_key(match.group(0))
        if token:
            tokens.append(_MatchToken(token, match.start(), match.end()))
    return tokens


def _verified_primary_token_keys(verified_primary_texts: Sequence[str]) -> frozenset[str]:
    return frozenset(
        token.text
        for source_text in verified_primary_texts
        for token in _textbook_match_token_spans(source_text)
    )


def _strip_verified_primary_bare_citations(
    text: str,
    *,
    verified_primary_token_keys: Collection[str],
) -> str:
    """Blank quote-delimited tokens only when they occur in verified primaries."""
    if not text or not verified_primary_token_keys:
        return text

    spans: list[tuple[int, int]] = []
    for match in _BARE_PRIMARY_CITATION_RE.finditer(text):
        group_name = next(
            name
            for name in _BARE_PRIMARY_CITATION_GROUPS
            if match.group(name) is not None
        )
        inner_start = match.start(group_name)
        for token in _textbook_match_token_spans(match.group(group_name)):
            if token.text in verified_primary_token_keys:
                spans.append((inner_start + token.start, inner_start + token.end))
    return _blank_text_spans(text, spans)


def _merge_text_spans(spans: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if start >= end:
            continue
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
            continue
        previous_start, previous_end = merged[-1]
        merged[-1] = (previous_start, max(previous_end, end))
    return merged


def _matching_token_spans(
    candidate_text: str,
    source_text: str,
    *,
    min_words: int,
) -> list[tuple[int, int]]:
    candidate_tokens = _textbook_match_token_spans(candidate_text)
    source_tokens = [token.text for token in _textbook_match_token_spans(source_text)]
    if len(candidate_tokens) < min_words or len(source_tokens) < min_words:
        return []

    source_windows: dict[tuple[str, ...], list[int]] = {}
    for source_start in range(0, len(source_tokens) - min_words + 1):
        window = tuple(source_tokens[source_start : source_start + min_words])
        source_windows.setdefault(window, []).append(source_start)

    candidate_token_texts = [token.text for token in candidate_tokens]
    spans: list[tuple[int, int]] = []
    for candidate_start in range(0, len(candidate_tokens) - min_words + 1):
        window = tuple(candidate_token_texts[candidate_start : candidate_start + min_words])
        source_starts = source_windows.get(window)
        if not source_starts:
            continue
        for source_start in source_starts:
            match_len = min_words
            while (
                candidate_start + match_len < len(candidate_token_texts)
                and source_start + match_len < len(source_tokens)
                and candidate_token_texts[candidate_start + match_len]
                == source_tokens[source_start + match_len]
            ):
                match_len += 1
            spans.append(
                (
                    candidate_tokens[candidate_start].start,
                    candidate_tokens[candidate_start + match_len - 1].end,
                )
            )
            break
    return _merge_text_spans(spans)


def _blank_text_spans(text: str, spans: Sequence[tuple[int, int]]) -> str:
    merged = _merge_text_spans(spans)
    if not merged:
        return text
    chunks: list[str] = []
    cursor = 0
    for start, end in merged:
        chunks.append(text[cursor:start])
        removed = text[start:end]
        chunks.append("\n" * removed.count("\n") or " ")
        cursor = end
    chunks.append(text[cursor:])
    return "".join(chunks)


def _strip_vesum_verbatim_primary_spans(
    text: str,
    *,
    level: str | None,
    verified_primary_texts: Sequence[str],
) -> str:
    """Blank matched seminar primary spans before modern VESUM verification."""
    if len(_textbook_match_token_spans(text)) < VESUM_PRIMARY_EXEMPTION_MIN_WORDS:
        return text

    stripped = text
    for source_text in verified_primary_texts:
        spans = _matching_token_spans(
            stripped,
            source_text,
            min_words=VESUM_PRIMARY_EXEMPTION_MIN_WORDS,
        )
        stripped = _blank_text_spans(stripped, spans)

    if len(_textbook_match_token_spans(stripped)) < VESUM_PRIMARY_EXEMPTION_MIN_WORDS:
        return stripped

    corpus_spans: list[tuple[int, int]] = []
    for hit in _search_literary_hits(stripped, level=str(level or ""), limit=20):
        hit_text = _result_text_for_match(hit)
        if not hit_text:
            continue
        corpus_spans.extend(
            _matching_token_spans(
                stripped,
                hit_text,
                min_words=VESUM_PRIMARY_EXEMPTION_MIN_WORDS,
            )
        )
    return _blank_text_spans(stripped, corpus_spans)


_TOPIC_STOPWORDS = {
    "about",
    "after",
    "before",
    "class",
    "grade",
    "into",
    "lesson",
    "module",
    "page",
    "section",
    "textbook",
    "that",
    "this",
    "with",
    "без",
    "для",
    "про",
    "та",
    "але",
    "або",
    "його",
    "її",
    "які",
    "яка",
    "яке",
    "який",
    "цей",
    "ця",
    "це",
    "такий",
    "такі",
}


def _topic_token_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for token in _textbook_match_tokens(text):
        stripped = token.strip("'-")
        if len(stripped) < 4 or stripped in _TOPIC_STOPWORDS or stripped.isdigit():
            continue
        keys.add(stripped[:6] if len(stripped) >= 6 else stripped)
    return keys


def _quote_topic_matches(quote: str, topic_text: str) -> bool:
    topic_tokens = _topic_token_keys(topic_text)
    if len(topic_tokens) < 2:
        return True
    quote_body = re.sub(r"^\s*(?:\*\*)?[^:\n]{1,120}:\s*", " ", quote, count=1)
    quote_tokens = _topic_token_keys(quote_body)
    # Minimal topicality guard: at least one normalized content-word stem from
    # the quote must also appear in the surrounding section title or
    # plan_reasoning text. This is intentionally lightweight and tunable.
    return bool(quote_tokens & topic_tokens)


def _plan_reasoning_text(module_text: str) -> str:
    return (
        " ".join(match.group("body") for match in _PLAN_REASONING_ELEMENT_RE.finditer(module_text))
        + " "
        + " ".join(match.group("body") for match in _PLAN_THINKING_ELEMENT_RE.finditer(module_text))
    )


def _flatten_tool_text(value: Any) -> list[str]:
    texts: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, Mapping):
            for child in node.values():
                walk(child)
        elif isinstance(node, list | tuple):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            texts.append(node)
        elif node is not None:
            texts.append(str(node))

    walk(value)
    return texts


def _load_jsonl_tool_calls(path: Path) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    if not path.exists():
        return calls
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, Mapping):
            continue
        if event.get("event") != "writer_tool_call":
            continue
        call = dict(event)
        if call.get("result_excerpt") and not call.get("result"):
            call["result"] = {"text": call["result_excerpt"]}
        calls.append(call)
    return calls


_WRITER_TOOL_CALL_TELEMETRY_NAMES = (
    "writer_tool_calls.json",
    "writer_trace.json",
    "writer_telemetry.jsonl",
)


def _writer_tool_call_telemetry_present(module_dir: Path) -> bool:
    """True iff any writer tool-call telemetry artifact exists for this module.

    Distinguishes a build-time run (``invoke_writer`` persists the trace) from a
    static re-verification of an already-built module whose telemetry was never
    persisted (e.g. pre-#3373 folk modules). ``resources_search_attempted`` is a
    build-time tool-call gate; without this signal a static shippability check
    cannot tell "writer ran no search" (a real failure) from "telemetry is simply
    not on disk" (un-evaluable). See ``_resources_search_attempted_gate``.
    """
    if any((module_dir / name).exists() for name in _WRITER_TOOL_CALL_TELEMETRY_NAMES):
        return True
    return any(module_dir.glob("*.write.jsonl"))


def _load_writer_tool_calls(module_dir: Path) -> list[dict[str, Any]]:
    candidates = [module_dir / name for name in _WRITER_TOOL_CALL_TELEMETRY_NAMES]
    calls: list[dict[str, Any]] = []
    for path in candidates:
        if not path.exists():
            continue
        if path.suffix == ".jsonl":
            calls.extend(_load_jsonl_tool_calls(path))
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            calls.extend(dict(item) for item in data if isinstance(item, Mapping))
        elif isinstance(data, Mapping):
            raw_calls = data.get("tool_calls") or data.get("mcp_tool_calls")
            if isinstance(raw_calls, list):
                calls.extend(dict(item) for item in raw_calls if isinstance(item, Mapping))
    for path in sorted(module_dir.glob("*.write.jsonl")):
        calls.extend(_load_jsonl_tool_calls(path))
    return calls


_PRIMARY_TEXT_SOURCE_DOMAINS_CACHE: frozenset[str] | None = None


def _load_primary_text_source_domains() -> frozenset[str]:
    global _PRIMARY_TEXT_SOURCE_DOMAINS_CACHE
    if _PRIMARY_TEXT_SOURCE_DOMAINS_CACHE is not None:
        return _PRIMARY_TEXT_SOURCE_DOMAINS_CACHE
    try:
        raw = yaml.safe_load(PRIMARY_TEXT_SOURCES_PATH.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        raw = {}
    domains: set[str] = set()
    sources = raw.get("sources") if isinstance(raw, Mapping) else []
    if isinstance(sources, list):
        for entry in sources:
            if isinstance(entry, Mapping):
                domain = str(entry.get("domain") or "").strip().lower()
            else:
                domain = str(entry).strip().lower()
            if not domain:
                continue
            host = urllib.parse.urlsplit(domain).hostname if "://" in domain else domain
            if host:
                domains.add(host.rstrip(".").lower())
    _PRIMARY_TEXT_SOURCE_DOMAINS_CACHE = frozenset(domains)
    return _PRIMARY_TEXT_SOURCE_DOMAINS_CACHE


def _resource_url_resolve_applies(level: str) -> bool:
    level_key = str(level or "").lower()
    return level_key == "folk" or level_key in SEMINAR_LEVELS


def _clean_resource_url(url: str, title: str = "") -> str:
    return validate_and_clean_url(str(url or "").strip(), title=title).strip()


def _is_on_site_resource_url(url: str) -> bool:
    cleaned = str(url or "").strip()
    if not cleaned:
        return False
    parts = urllib.parse.urlsplit(cleaned)
    return not parts.scheme and not parts.netloc and not cleaned.startswith("//")


def _matching_primary_text_domain(hostname: str, allowed_domains: frozenset[str]) -> str | None:
    host = hostname.rstrip(".").lower()
    candidates = [host]
    if host.startswith("www."):
        candidates.append(host[4:])
    for candidate in candidates:
        if candidate in allowed_domains:
            return candidate
    return None


def _shallow_resource_url_reason(url: str) -> str | None:
    parts = urllib.parse.urlsplit(url)
    path = urllib.parse.unquote(parts.path or "")
    path_key = re.sub(r"/+", "/", path).lower()
    if path_key in {"", "/"}:
        return "bare_domain"
    if re.fullmatch(r"/narod/?", path_key):
        return "ukrlib_narod_landing"
    if re.fullmatch(r"/school/literature/?", path_key):
        return "school_literature_landing"
    if re.fullmatch(r"/category(?:/[^/?#]+)+/?", path_key):
        return "category_landing"
    query = urllib.parse.parse_qs(parts.query, keep_blank_values=True)
    numeric_ids = query.get("id") or []
    if path_key.endswith("/book.php") and len(numeric_ids) == 1 and numeric_ids[0].isdigit():
        return "guessed_numeric_book_id"
    if path_key.endswith("/") and not parts.query:
        return "trailing_slash_directory"
    return None


def _resources_url_resolve_gate(
    resources: list[dict[str, Any]],
    *,
    level: str,
    resource_liveness_fn: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    if not _resource_url_resolve_applies(level):
        # TODO(#3630): design a separate core-track link-hygiene policy that
        # permits learner media/blog resources without using this primary-text allowlist.
        return {
            "passed": True,
            "severity": None,
            "skipped": "not_applicable_non_seminar_level",
            "level": level,
            "checked": 0,
            "results": [],
        }

    allowed_domains = _load_primary_text_source_domains()
    results: list[dict[str, Any]] = []
    all_ok = True
    checked = 0
    for entry in resources:
        if not isinstance(entry, Mapping):
            all_ok = False
            results.append({"resource": str(entry)[:80], "resolved": False, "reason": "not_a_mapping"})
            continue
        role = str(entry.get("role") or "").strip()
        title = str(entry.get("title") or "").strip()
        raw_url = str(entry.get("url") or "").strip()
        if role == "textbook" and not raw_url:
            continue
        if role not in URL_BEARING_RESOURCE_ROLES:
            continue
        checked += 1
        if not raw_url:
            all_ok = False
            results.append(
                {
                    "title": title,
                    "role": role,
                    "url": None,
                    "resolved": False,
                    "reason": "missing_url_for_url_bearing_role",
                }
            )
            continue
        url = _clean_resource_url(raw_url, title=title)
        if _is_on_site_resource_url(url):
            all_ok = False
            results.append(
                {
                    "title": title,
                    "role": role,
                    "url": url,
                    "resolved": False,
                    "reason": "relative_url_not_allowed",
                    "live": None,
                }
            )
            continue
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            all_ok = False
            results.append(
                {
                    "title": title,
                    "role": role,
                    "url": url,
                    "resolved": False,
                    "reason": "invalid_external_url",
                }
            )
            continue
        matched_domain = _matching_primary_text_domain(parts.hostname, allowed_domains)
        if matched_domain is None:
            all_ok = False
            results.append(
                {
                    "title": title,
                    "role": role,
                    "url": url,
                    "resolved": False,
                    "reason": "domain_not_allowlisted",
                    "domain": parts.hostname.lower(),
                }
            )
            continue
        shallow_reason = _shallow_resource_url_reason(url)
        if shallow_reason is not None:
            all_ok = False
            results.append(
                {
                    "title": title,
                    "role": role,
                    "url": url,
                    "resolved": False,
                    "reason": shallow_reason,
                    "domain": matched_domain,
                }
            )
            continue
        live: bool | None = None
        if resource_liveness_fn is not None:
            live = bool(resource_liveness_fn(url))
            if not live:
                all_ok = False
                results.append(
                    {
                        "title": title,
                        "role": role,
                        "url": url,
                        "resolved": False,
                        "reason": "url_not_live",
                        "domain": matched_domain,
                        "live": False,
                    }
                )
                continue
        results.append(
            {
                "title": title,
                "role": role,
                "url": url,
                "resolved": True,
                "reason": "resolved",
                "domain": matched_domain,
                "live": live,
            }
        )
    return {
        "passed": all_ok,
        "severity": "HARD" if not all_ok else None,
        "checked": checked,
        "results": results,
        "liveness_checked": resource_liveness_fn is not None,
    }


def _verify_resources_live(
    resources: list[dict[str, Any]],
    *,
    url_live_fn: Callable[[str], bool],
) -> dict[str, Any]:
    """Independently verify that every resource is real (fail-closed).

    Used only to substitute for ABSENT build-time search telemetry during static
    re-verification (see ``_resources_search_attempted_gate``). Each resource
    bearing a ``url`` is confirmed live via ``url_live_fn`` (HTTP liveness / wiki
    existence). A resource WITHOUT a url is only acceptable when ``role`` is
    ``textbook`` (validated separately by ``citations_resolve``); any other
    no-url resource fails closed, so an unverifiable resource blocks the skip.
    ``passed`` is True only when there is ≥1 resource and EVERY resource verified
    — a single fabricated/dead URL keeps the gate failing. This is what closes
    the over-exemption hole: the skip requires PROOF the resources are real, not
    an inference from textbook-grounding gates.
    """
    results: list[dict[str, Any]] = []
    all_ok = True
    for entry in resources:
        if not isinstance(entry, Mapping):
            all_ok = False
            results.append({"resource": str(entry)[:80], "live": False, "reason": "not_a_mapping"})
            continue
        url = str(entry.get("url") or "").strip()
        role = str(entry.get("role") or "")
        title = entry.get("title")
        if not url:
            ok = role == "textbook"
            results.append(
                {
                    "title": title,
                    "role": role,
                    "url": None,
                    "live": ok,
                    "reason": "textbook_via_citations" if ok else "no_url_unverifiable",
                }
            )
            all_ok = all_ok and ok
            continue
        url = _clean_resource_url(url, title=str(title or ""))
        if _is_on_site_resource_url(url):
            results.append(
                {
                    "title": title,
                    "role": role,
                    "url": url,
                    "live": True,
                    "reason": "on_site_reference",
                }
            )
            continue
        live = bool(url_live_fn(url))
        results.append({"title": title, "role": role, "url": url, "live": live})
        all_ok = all_ok and live
    return {"passed": bool(resources) and all_ok, "checked": len(resources), "results": results}


def _resources_search_attempted_gate(
    writer_tool_calls: list[dict[str, Any]],
    *,
    plan: Mapping[str, Any] | None = None,
    resource_coverage: Mapping[str, Any] | None = None,
    telemetry_present: bool = True,
    resource_liveness: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """HARD gate: writer must attempt at least one external-resource search.

    This inspects build-time writer tool-call telemetry, so it can only be
    evaluated during a build (when ``invoke_writer`` persists the trace). When a
    module is re-verified statically (e.g. ``verify_shippable`` on an
    already-built module) the telemetry file may be absent — which is NOT
    evidence the writer skipped the search. To avoid a false HARD failure the
    gate is treated as not-applicable (skipped, passing) when BOTH:

    * ``telemetry_present`` is False (no writer trace on disk), AND
    * ``resource_liveness`` proves EVERY resource is real (``passed`` True from
      ``_verify_resources_live`` — each url-bearing resource confirmed live, no
      unverifiable resource present).

    Verifying the resources are real is a STRONGER anti-fabrication signal than
    the search telemetry it replaces: a fabricated or dead resource fails the
    liveness check, so a fabricated-resource module can never reach the skip.
    Build-time runs are unaffected — telemetry is present, the liveness path is
    not taken, and a present trace with no search still fails exactly as before.
    """
    attempted = [
        call
        for call in writer_tool_calls
        if _tool_name_from_call(call) in MULTIMEDIA_SEARCH_TOOLS
    ]
    search_tools_used = sorted({_tool_name_from_call(call) for call in attempted})
    manual_coverage_verified = (
        not attempted
        and _manual_resource_coverage_can_stand_in_for_search_telemetry(
            plan,
            resource_coverage,
        )
    )
    liveness_verified = bool(resource_liveness) and resource_liveness.get("passed") is True
    telemetry_absent_resources_verified_live = (
        not attempted
        and not manual_coverage_verified
        and not telemetry_present
        and liveness_verified
    )
    result: dict[str, Any] = {
        "passed": bool(attempted)
        or manual_coverage_verified
        or telemetry_absent_resources_verified_live,
        "severity": "HARD",
        "search_attempt_count": len(attempted),
        "search_tools_used": search_tools_used,
        "manual_coverage_verified": manual_coverage_verified,
    }
    if telemetry_absent_resources_verified_live:
        result["skipped"] = "build_telemetry_absent_resources_verified_live"
        result["resources_verified_live"] = resource_liveness.get("checked")
    return result


def _manual_resource_coverage_can_stand_in_for_search_telemetry(
    plan: Mapping[str, Any] | None,
    resource_coverage: Mapping[str, Any] | None,
) -> bool:
    if not isinstance(plan, Mapping) or not isinstance(resource_coverage, Mapping):
        return False
    if resource_coverage.get("passed") is not True:
        return False
    archetype = resolve_module_archetype(
        str(plan.get("level") or ""),
        int(plan.get("sequence") or 0),
    )
    return _is_a1_m1_m7_archetype(archetype)


def _is_a1_m1_m7_archetype(archetype: Mapping[str, Any]) -> bool:
    return archetype.get("id") in {
        "a1-zero-script-onboarding",
        "a1-script-building",
        "a1-first-contact-survival",
    }


_MCP_SEARCH_TEXT_RESULT_RE = re.compile(
    r"(?ms)^###\s+Result\s+\d+\s*$"
    r"(?P<body>.*?)(?=^###\s+Result\s+\d+\s*$|\Z)"
)


def _parse_mcp_search_text_markdown(text: str) -> list[Mapping[str, Any]]:
    """Parse sources.search_text markdown output into textbook result items."""
    items: list[Mapping[str, Any]] = []
    for match in _MCP_SEARCH_TEXT_RESULT_RE.finditer(text):
        body = match.group("body").strip()
        source_match = re.search(r"(?m)^-\s+\*\*Source\*\*:\s*(?P<source>.+?)\s*$", body)
        text_match = re.search(r"(?ms)^-\s+\*\*Text\*\*:\s*\n(?P<text>.*)\Z", body)
        if source_match is None or text_match is None:
            continue

        source = source_match.group("source").strip()
        grade_match = re.search(r"(?i)\bgrade\s+(?P<grade>1[01]|[1-9])\b", source)
        page_match = re.search(
            r"(?im)^-\s+\*\*Section\*\*:\s*(?:Сторінка|Page|p\.?)\s*(?P<page>\d+)\b",
            body,
        )
        author = re.sub(r"(?i)\bgrade\s+(?:1[01]|[1-9])\b", "", source)
        author = author.strip(" ,;:-")
        title = source
        if author and grade_match and page_match:
            title = f"{author[:1].upper()}{author[1:]} Grade {grade_match.group('grade')}, p.{page_match.group('page')}"

        item: dict[str, Any] = {
            "source_type": "textbook",
            "source": source,
            "title": title,
            "text": text_match.group("text").strip(),
        }
        if author:
            item["author"] = author
        if grade_match:
            item["grade"] = int(grade_match.group("grade"))
        if page_match:
            item["page"] = int(page_match.group("page"))
        items.append(item)
    return items


_MCP_GET_CHUNK_CONTEXT_RE = re.compile(
    r"(?s)^\s*\*\*\[(?P<chunk_id>[^\]]+)\]\*\*\s+—\s+"
    r"(?:Сторінка|Page|p\.?)\s+(?P<section>\d+)\s*\n+"
    r"(?P<body>.*)$"
)

_CHUNK_ID_PAGE_SUFFIX_RE = re.compile(r"^(?P<source_file>.+)_s(?P<page>\d{3,4})$")


def _lookup_textbook_metadata(source_file: str) -> dict[str, str] | None:
    """Look up author_uk + grade for a textbook ``source_file``.

    Pulled out of ``_parse_mcp_get_chunk_context_markdown`` so tests can
    monkeypatch the DB hit. Returns ``None`` if the DB is unavailable, the
    source_file has no row, or the query fails. Cyrillic-native — never
    crosses writing systems (per ADR
    ``docs/decisions/2026-05-15-cyrillic-native-matcher.md``).
    """
    if not TEXTBOOK_SOURCES_DB_PATH.exists():
        return None
    try:
        with sqlite3.connect(str(TEXTBOOK_SOURCES_DB_PATH)) as conn:
            row = conn.execute(
                "SELECT author_uk, grade FROM textbooks WHERE source_file = ? LIMIT 1",
                (source_file,),
            ).fetchone()
    except sqlite3.Error:
        return None
    if row is None:
        return None
    author_uk = str(row[0] or "").strip()
    grade = str(row[1] or "").strip()
    if not author_uk or not grade:
        return None
    return {"author_uk": author_uk, "grade": grade}


def _parse_mcp_get_chunk_context_markdown(
    text: str,
) -> list[Mapping[str, Any]]:
    """Parse sources.get_chunk_context markdown output into a textbook item.

    Output shape:

        **[<chunk_id>]** — Сторінка <N>

        <verbatim body>

    The writer prompt's Step B (writer_prompt §"Textbook quotes") instructs
    every CORE-level writer to call ``get_chunk_context(chunk_id=...)`` with
    the chunk_id resolved from the plan's reference_records, then paste ≥30
    contiguous words from the returned body. Before this parser landed the
    textbook_grounding gate only ingested ``search_text`` results, so a
    writer doing the prompt-prescribed thing produced ``matched=[]`` and
    HARD-REJECTED on textbook_grounding (observed on a1/my-morning
    build 2026-05-19 21:06 — the writer's two verbatim blockquotes WERE
    in the returned chunk_context body but the gate never saw them).

    To make the synthesized item match the plan reference title (e.g.
    ``"Захарійчук Grade 1, p.52"``), we derive ``page`` deterministically
    from the chunk_id pattern ``<source_file>_s<NNNN>`` and look up
    ``author_uk`` + ``grade`` from the textbooks table via
    ``_lookup_textbook_metadata``. If the DB is unavailable the item is
    returned without a synthesized title (the body still contributes to
    the long-blockquote substring match path in
    ``_textbook_grounding_gate``).
    """
    match = _MCP_GET_CHUNK_CONTEXT_RE.match(text)
    if match is None:
        return []
    chunk_id = match.group("chunk_id").strip()
    body = match.group("body").strip()
    item: dict[str, Any] = {
        "source_type": "textbook",
        "chunk_id": chunk_id,
        "text": body,
    }
    suffix_match = _CHUNK_ID_PAGE_SUFFIX_RE.match(chunk_id)
    if suffix_match is None:
        return [item]
    source_file = suffix_match.group("source_file")
    page = int(suffix_match.group("page"))
    item["source_file"] = source_file
    item["page"] = page
    metadata = _lookup_textbook_metadata(source_file)
    if metadata is not None:
        author = metadata["author_uk"]
        grade_str = metadata["grade"]
        item["author"] = author
        item["grade"] = int(grade_str) if grade_str.isdigit() else grade_str
        item["title"] = f"{author} Grade {grade_str}, p.{page}"
    return [item]


def _result_items_from_call(call: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    result = call.get("result", call.get("response"))
    result_summary = call.get("result_summary")
    has_summary_items = isinstance(result_summary, Mapping) and isinstance(
        result_summary.get("items"),
        list,
    )
    result_is_excerpt_only = isinstance(result, Mapping) and set(result) <= {"text"}
    if has_summary_items and (result is None or result_is_excerpt_only):
        result = result_summary
    if result is None and call.get("result_excerpt"):
        result = {"text": call["result_excerpt"]}
        if call.get("source_type"):
            result["source_type"] = call["source_type"]
    # Codex CLI envelope: tool outputs from codex (mcp_sources_* via codex-cli
    # 0.133.0+) arrive as a wrapped string ``Wall time: X.XXXX seconds\nOutput:\n<json>``
    # where ``<json>`` is the canonical content-block list shape
    # ``[{"type":"text","text":"<md>"}]``. Without unwrapping, the canonical
    # list branch below skips the result (string isn't list/Mapping) and
    # ``textbook_grounding`` reads ``textbook_result_hits: 0`` even when
    # the writer's search_text/get_chunk_context calls returned grounded
    # textbook chunks. Empirical reference: rollout-2026-05-22T22-58-38
    # for the post-#2233 codex-tools a1/my-morning build — 38 valid
    # mcp__sources__* calls fired with full results, all dropped by the
    # result-extraction pass.
    if isinstance(result, str):
        stripped = result.lstrip()
        if stripped.startswith("Wall time:"):
            output_marker = "Output:\n"
            idx = stripped.find(output_marker)
            if idx >= 0:
                payload_text = stripped[idx + len(output_marker):]
                try:
                    parsed = json.loads(payload_text)
                except (json.JSONDecodeError, ValueError):
                    parsed = None
                if isinstance(parsed, (list, dict)):
                    result = parsed
    if isinstance(result, list):
        items: list[Mapping[str, Any]] = []
        tool_name = _tool_name_from_call(call)
        for item in result:
            if not isinstance(item, Mapping):
                continue
            if tool_name == "search_text" and item.get("type") == "text" and isinstance(item.get("text"), str):
                parsed = _parse_mcp_search_text_markdown(item["text"])
                if parsed:
                    items.extend(parsed)
                    continue
            # Mirror of the search_text branch above for the
            # ``get_chunk_context`` canonical MCP content-block shape
            # ``[{"type": "text", "text": "**[<chunk_id>]** — ..."}]``.
            # Empirical reference: m20 build #7 (2026-05-26, codex-tools
            # writer): codex called ``get_chunk_context`` twice and returned
            # the canonical list-of-text-blocks envelope, but the gate
            # produced ``matched=[]`` and HARD-rejected on
            # ``textbook_grounding`` because the items got appended raw
            # (with ``type="text"`` and no ``source_type``), so
            # ``_is_textbook_result`` returned False and dropped every chunk.
            # The dict-shape branch at line 8440 handles the equivalent
            # ``{"type": "text", "text": "<md>"}`` for get_chunk_context;
            # this branch closes the LIST-shape gap and is symmetric with
            # the search_text branch directly above.
            if (
                tool_name == "get_chunk_context"
                and item.get("type") == "text"
                and isinstance(item.get("text"), str)
            ):
                parsed = _parse_mcp_get_chunk_context_markdown(item["text"])
                if parsed:
                    items.extend(parsed)
                    continue
            # Gemini-CLI list-shape MCP response. Empirical evidence: the
            # 2026-05-21 a1/my-morning gemini-tools build wrote the writer
            # call result as
            # ``[{"functionResponse": {"id": ..., "name": "...",
            # "response": {"output": "**[chunk_id]** — Сторінка N\n\n<md>"}}}]``
            # — neither the canonical ``{"text": <md>}`` nor the Hermes
            # ``{"result": <md>}`` shapes the parser previously handled.
            # Without this unwrap textbook_grounding reads
            # ``textbook_result_hits: 0`` even when get_chunk_context fired
            # and returned grounded textbook chunks (the 2026-05-20 textbook
            # parser fix `07c12f2dd7` only covered the dict-shape responses).
            function_response = item.get("functionResponse")
            if isinstance(function_response, Mapping):
                response = function_response.get("response")
                if isinstance(response, Mapping):
                    output = response.get("output")
                    if isinstance(output, str):
                        if tool_name == "search_text":
                            parsed = _parse_mcp_search_text_markdown(output)
                            if parsed:
                                items.extend(parsed)
                                continue
                        elif tool_name == "get_chunk_context":
                            parsed = _parse_mcp_get_chunk_context_markdown(output)
                            if parsed:
                                items.extend(parsed)
                                continue
            items.append(item)
        return items
    if isinstance(result, Mapping):
        result = dict(result)
        if call.get("source_type") and not result.get("source_type"):
            result["source_type"] = call["source_type"]
        raw_hits = result.get("results") or result.get("hits") or result.get("items")
        if isinstance(raw_hits, list):
            return [item for item in raw_hits if isinstance(item, Mapping)]
        tool_name = _tool_name_from_call(call)
        if tool_name == "search_text":
            # Canonical MCP content-block shape (claude / codex / direct
            # anthropic-tools): result is ``{"type": "text", "text": "<md>"}``.
            if result.get("type") == "text" and isinstance(result.get("text"), str):
                parsed = _parse_mcp_search_text_markdown(result["text"])
                if parsed:
                    return parsed
            # Hermes-routed MCP variant shape: the sources MCP server wraps
            # its single-string response under an inner ``result`` key, so
            # the captured hook payload reads
            # ``{"tool":"mcp_sources_search_text","result":{"result":"<md>"}}``.
            # The inner markdown payload follows the same
            # ``### Result N / **Source** / **Text**`` format the parser
            # already handles. Empirical evidence: 2026-05-19 b1
            # genitive-nuances build's hermes.write.jsonl. Without this
            # unwrap every Hermes-routed writer reads
            # ``textbook_result_hits: 0`` even when the calls fired and
            # returned grounded textbook chunks.
            inner = result.get("result")
            if isinstance(inner, str):
                parsed = _parse_mcp_search_text_markdown(inner)
                if parsed:
                    return parsed
        elif tool_name == "get_chunk_context":
            # The writer prompt's Step B prescribes get_chunk_context for
            # plan-referenced chunks (after search_text resolves chunk_id).
            # Without parsing this shape the textbook_grounding gate ignores
            # the writer's deterministic retrieval path entirely — observed
            # 2026-05-19 a1/my-morning build, where the writer's two verbatim
            # blockquotes WERE in the chunk_context bodies but the gate
            # produced ``matched=[]``.
            for candidate in (result.get("text"), result.get("result")):
                if isinstance(candidate, str):
                    parsed = _parse_mcp_get_chunk_context_markdown(candidate)
                    if parsed:
                        return parsed
        return [result]
    return []


def _result_source_type(result: Mapping[str, Any]) -> str:
    return str(
        result.get("source_type") or result.get("type") or result.get("corpus") or result.get("source") or ""
    ).casefold()


def _is_textbook_result(result: Mapping[str, Any]) -> bool:
    return "textbook" in _result_source_type(result)


def _result_text_for_match(result: Mapping[str, Any]) -> str:
    text = _textbook_hit_text(result, max_chars=50_000)
    if text:
        return text
    return "\n".join(_flatten_tool_text(result))


def _call_text_parts(call: Mapping[str, Any]) -> tuple[str, str]:
    args = call.get("args", call.get("arguments", {}))
    result = call.get("result", call.get("response", call.get("result_excerpt", "")))
    query_text = "\n".join(_flatten_tool_text(args))
    result_text = "\n".join(_flatten_tool_text(result))
    return query_text, result_text


def _reference_matches_search_call(reference_title: str, call: Mapping[str, Any]) -> bool:
    return any(_reference_matches_result(reference_title, result) for result in _result_items_from_call(call))


def _reference_matches_result(
    reference_title: str,
    result: Mapping[str, Any],
) -> bool:
    result_text = "\n".join(_flatten_tool_text(result))
    ref_key = extract_citation_key(reference_title)
    if ref_key is not None:
        citation_texts = [
            str(result.get("title") or ""),
            str(result.get("source_ref") or ""),
            result_text,
        ]
        for text in citation_texts:
            result_key = extract_citation_key(text)
            if result_key is not None and citation_keys_match(result_key, ref_key):
                return True
    return _citation_ref_text_contains(reference_title, result_text)


def _missing_corpus_refs_from_packet(module_dir: Path) -> set[str]:
    packet_path = module_dir / "knowledge_packet.md"
    if not packet_path.exists():
        return set()
    missing: set[str] = set()
    current_ref = ""
    for line in packet_path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^###\s+(?P<title>.+?)\s*$", line)
        if heading:
            current_ref = heading.group("title").strip()
            continue
        if current_ref and re.search(r"\bcorpus_missing:\s*true\b", line):
            missing.add(current_ref)
    return missing


def _plan_reference_records(
    plan: Mapping[str, Any],
    module_dir: Path,
) -> list[dict[str, Any]]:
    missing_from_packet = _missing_corpus_refs_from_packet(module_dir)
    records: list[dict[str, Any]] = []
    references = plan.get("references") or plan.get("plan_references") or []
    if not isinstance(references, list):
        return records
    for ref in references:
        if not isinstance(ref, Mapping) or not ref.get("title"):
            continue
        title = str(ref["title"])
        records.append(
            {
                "title": title,
                "corpus_missing": bool(ref.get("corpus_missing")) or title in missing_from_packet,
                "verbatim_required": ref.get("verbatim_required") is not False,
            }
        )
    return records


def _level_requires_references(level: str) -> bool:
    return level.casefold() in {"b1", "b2", "c1", "c2", "pro"}


def is_publishable_ref(ref: Mapping[str, Any]) -> bool:
    """Predicate to determine if a plan reference is appropriate for learner-facing publication.

    Children's primers (Grade 1-3) are internal-only for grounding lexical choices.
    Grade 7+, adult literature, style guides, and dictionaries are publishable.
    """
    if not isinstance(ref, Mapping):
        return False

    title = str(ref.get("title") or "")
    notes = str(ref.get("notes") or "")
    source_type = str(ref.get("source_type") or "").lower()
    author = str(ref.get("author") or "").lower()

    # 1. source_type check
    if source_type in {"literature", "style_guide", "dictionary"}:
        return True

    # 2. author list check
    # Антоненко-Давидович, Грінченко
    combined_metadata = (title + " " + author + " " + notes).lower()
    if re.search(r"антоненко-давидович|грінченк", combined_metadata):
        return True

    # 3. Grade check
    grade_val = ref.get("grade")
    grade_int: int | None = None
    if isinstance(grade_val, (int, str)):
        with contextlib.suppress(ValueError, TypeError):
            grade_int = int(grade_val)

    if grade_int is None:
        # Try parsing from title or notes: "Grade 7", "7 клас", "7-klas"
        match = re.search(r"(?i)\b(?:grade|клас|klas|class)[-\s]*(?P<grade>1[01]|[1-9])\b", title + " " + notes)
        if not match:
            # Try reverse: "7 grade", "7-klas"
            match = re.search(r"(?i)\b(?P<grade>1[01]|[1-9])[-\s]*(?:grade|клас|klas|class)\b", title + " " + notes)
        if match:
            grade_int = int(match.group("grade"))

    if grade_int is not None:
        if grade_int >= 7:
            return True
        if grade_int in {1, 2, 3}:
            return False

    # Default to internal-only for ambiguous (no grade, no source_type, no author)
    # or for grades 4-6 that are not explicitly publishable via other signals.
    return False


def _chunk_context_for_all_refs_gate(
    plan: Mapping[str, Any],
    writer_tool_calls: list[Mapping[str, Any]],
    module_dir: Path,
) -> dict[str, Any]:
    """Every plan_reference MUST be retrieved via mcp__sources__get_chunk_context.

    Applies regardless of source grade (Grade 1-3 grounding still needs the full
    chunk context, even if they don't publish a blockquote).
    """
    references = plan.get("references") or plan.get("plan_references") or []
    if not isinstance(references, list):
        return {"passed": True, "verdict": "PASS"}

    missing_from_packet = _missing_corpus_refs_from_packet(module_dir)
    called_chunk_ids = set()
    for call in writer_tool_calls:
        if _tool_name_from_call(call) == "get_chunk_context":
            args = call.get("arguments") or {}
            chunk_id = args.get("chunk_id")
            if chunk_id:
                called_chunk_ids.add(chunk_id)

    violations = []
    for ref in references:
        if not isinstance(ref, Mapping):
            continue
        title = str(ref.get("title") or "")
        corpus_missing = bool(ref.get("corpus_missing")) or title in missing_from_packet
        if corpus_missing:
            continue

        chunk_id = extract_chunk_id_from_notes(str(ref.get("notes") or ""))
        if chunk_id and chunk_id not in called_chunk_ids:
            violations.append({"title": title, "chunk_id": chunk_id})

    if violations:
        return {
            "passed": False,
            "verdict": "REJECT",
            "severity": "HARD",
            "reason": "missing_chunk_context_calls",
            "violations": violations,
        }
    return {"passed": True, "verdict": "PASS"}


def _published_quote_for_publishable_refs_gate(
    module_text: str,
    plan: Mapping[str, Any],
    module_dir: Path,
) -> dict[str, Any]:
    """Only publishable refs (Grade 7+, adult lit, etc.) require a blockquote.

    Verifies a >=30-word blockquote literally appears in module.md and matches
    the retrieved chunk text. Skips internal-only refs (Grade 1-3).
    """
    level = str(plan.get("level") or "").casefold()
    reference_records = _plan_reference_records(plan, module_dir)

    # Filter to publishable references only
    raw_refs = plan.get("references") or plan.get("plan_references") or []
    publishable_titles = set()
    for ref in raw_refs:
        if is_publishable_ref(ref):
            publishable_titles.add(str(ref.get("title") or ""))

    # We only enforce publication for refs that are:
    # 1. In the plan references
    # 2. Flagged as publishable by is_publishable_ref
    # 3. Not corpus-missing (we can't quote what we don't have)
    # 4. Verbatim-required (some rare seminar refs are topical-only)
    refs_to_check = [
        record
        for record in reference_records
        if record["title"] in publishable_titles
        and not record["corpus_missing"]
        and record["verbatim_required"]
    ]

    if not refs_to_check:
        return {"passed": True, "verdict": "PASS", "matched": [], "blockquotes_checked": 0}

    blockquote_records = _extract_blockquote_records(module_text)
    plan_reasoning = _plan_reasoning_text(module_text)
    long_blockquote_records = [
        record
        for record in blockquote_records
        if len(_textbook_match_tokens(record["quote"])) >= TEXTBOOK_GROUNDING_MIN_WORDS
    ]

    all_writer_calls = _load_writer_tool_calls(module_dir)
    search_calls = [call for call in all_writer_calls if _tool_name_from_call(call) == "search_text"]
    chunk_context_calls = [call for call in all_writer_calls if _tool_name_from_call(call) == "get_chunk_context"]
    relevant_calls = search_calls + chunk_context_calls

    textbook_results: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for call in relevant_calls:
        for result in _result_items_from_call(call):
            if _is_textbook_result(result):
                textbook_results.append((call, result))

    matched: dict[str, int] = {}
    topical_mismatches: list[str] = []

    for record in refs_to_check:
        ref = record["title"]
        ref_results = [result for call, result in textbook_results if _reference_matches_result(ref, result)]
        for b_record in long_blockquote_records:
            quote = b_record["quote"]
            attribution = b_record.get("attribution", "")
            candidate_results = ref_results
            if not candidate_results and _citation_ref_text_contains(ref, attribution):
                candidate_results = [result for _call, result in textbook_results]

            if not any(
                _contains_textbook_quote(quote, _result_text_for_match(result)) for result in candidate_results
            ):
                continue

            topic_text = f"{b_record['section_title']} {plan_reasoning}".strip()
            if not _quote_topic_matches(quote, topic_text):
                topical_mismatches.append(ref)
                continue

            matched[ref] = len(_textbook_match_tokens(quote))
            break

    # If level is A1, we usually only require ONE match total across all refs.
    # However, this gate is now specifically for PUBLISHABLE refs.
    # If the plan has 5 Grade 1 refs and 1 Grade 7 ref, and we are A1,
    # we still want that Grade 7 ref to be quoted if it's there.
    # Actually, the old gate used `required = 1 if level == "a1" else len(references)`.
    # We should probably follow similar logic for publishable refs.

    required = 1 if level == "a1" and refs_to_check else len(refs_to_check)
    passed = len(matched) >= required

    return {
        "passed": passed,
        "verdict": "PASS" if passed else "REJECT",
        "severity": "HARD",
        "required": required,
        "matched": list(matched.keys()),
        "missing": [r["title"] for r in refs_to_check if r["title"] not in matched],
        "blockquotes_checked": len(long_blockquote_records),
        "reason": "missing_publishable_quotes" if not passed else None,
        "topical_mismatches": topical_mismatches,
    }


# DEPRECATED: split into chunk_context_for_all_refs + published_quote_for_publishable_refs as of 2026-05-27.
# Remove after one successful Phase 2a refire.
def _textbook_grounding_gate(
    module_text: str,
    plan: Mapping[str, Any],
    module_dir: Path,
) -> dict[str, Any]:
    level = str(plan.get("level") or "").casefold()
    reference_records = _plan_reference_records(plan, module_dir)
    references = [record["title"] for record in reference_records]
    if not references:
        if _level_requires_references(level):
            return {
                "passed": False,
                "verdict": "REJECT",
                "severity": "HARD",
                "required": 1,
                "matched": [],
                "missing": [],
                "blockquotes_checked": 0,
                "search_text_calls": 0,
                "reason": "missing_references",
            }
        return {
            "passed": True,
            "verdict": "PASS",
            "required": 0,
            "matched": [],
            "missing": [],
            "blockquotes_checked": 0,
            "search_text_calls": 0,
        }

    blockquote_records = _extract_blockquote_records(module_text)
    plan_reasoning = _plan_reasoning_text(module_text)
    long_blockquote_records = [
        record
        for record in blockquote_records
        if len(_textbook_match_tokens(record["quote"])) >= TEXTBOOK_GROUNDING_MIN_WORDS
    ]
    all_writer_calls = _load_writer_tool_calls(module_dir)
    search_calls = [call for call in all_writer_calls if _tool_name_from_call(call) == "search_text"]
    # Per writer_prompt §"Textbook quotes" Step B, writers retrieve the
    # plan-referenced chunk via ``get_chunk_context(chunk_id=...)`` after
    # ``search_text`` resolves the chunk_id. Both call families produce
    # textbook items the matcher needs to see — collecting only one half
    # (the historical state until 2026-05-20) makes the writer's
    # prompt-prescribed retrieval path invisible to the gate.
    chunk_context_calls = [call for call in all_writer_calls if _tool_name_from_call(call) == "get_chunk_context"]
    relevant_calls = search_calls + chunk_context_calls
    textbook_results: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for call in relevant_calls:
        for result in _result_items_from_call(call):
            if _is_textbook_result(result):
                textbook_results.append((call, result))

    matched: dict[str, int] = {}
    topical_mismatches: list[str] = []
    unattributed_matches = 0
    downgraded = [
        record["title"]
        for record in reference_records
        if not record["corpus_missing"] and not record["verbatim_required"]
    ]
    missing_corpus = [record["title"] for record in reference_records if record["corpus_missing"]]
    for ref in references:
        if ref in downgraded:
            continue
        ref_results = [result for call, result in textbook_results if _reference_matches_result(ref, result)]
        for record in long_blockquote_records:
            quote = record["quote"]
            attribution = record.get("attribution", "")
            candidate_results = ref_results
            if not candidate_results and _citation_ref_text_contains(ref, attribution):
                candidate_results = [result for _call, result in textbook_results]
            if not any(_contains_textbook_quote(quote, _result_text_for_match(result)) for result in candidate_results):
                continue
            topic_text = f"{record['section_title']} {plan_reasoning}".strip()
            if not _quote_topic_matches(quote, topic_text):
                topical_mismatches.append(ref)
                continue
            matched[ref] = len(_textbook_match_tokens(quote))
            break

    for ref in downgraded:
        matched[ref] = 0

    if level == "a1" and not matched:
        for record in long_blockquote_records:
            quote = record["quote"]
            topic_text = f"{record['section_title']} {plan_reasoning}".strip()
            for _call, result in textbook_results:
                if not _contains_textbook_quote(quote, _result_text_for_match(result)):
                    continue
                if not _quote_topic_matches(quote, topic_text):
                    topical_mismatches.append("unattributed")
                    continue
                actual_ref = next(
                    (ref for ref in references if _reference_matches_result(ref, result)),
                    "unattributed",
                )
                if actual_ref == "unattributed":
                    unattributed_matches += 1
                    continue
                matched[actual_ref] = len(_textbook_match_tokens(quote))
                break
            if matched:
                break

    required = 1 if level == "a1" else len(references)
    passed = len(matched) >= required
    warnings = []
    if missing_corpus:
        warnings.append("corpus_missing")
    if downgraded:
        warnings.append("corpus_missing_or_verbatim_not_required")
    reason = (
        "corpus_missing"
        if missing_corpus and not passed
        else "topical_mismatch"
        if not passed and topical_mismatches
        else None
    )
    # Step B enforcement (#2294, 2026-05-26): writer prompt rule
    # ``#R-TEXTBOOK-30W`` (B) requires ``mcp__sources__get_chunk_context(
    # chunk_id=<ID>)`` for every fetchable plan reference (present in corpus
    # AND verbatim-required). The matcher previously accepted blockquote
    # evidence derived from ``search_text`` results alone, which let a Step-B-
    # skipped writer pass the gate. m20 build #4 (a1-my-morning-20260525-
    # 235634) demonstrated the false-pass: ``search_text_calls=2``,
    # ``chunk_context_calls=0``, ``passed=true``, with the writer self-
    # reporting ``<chunk_context_calls>0</chunk_context_calls>``. The prompt
    # promised "HARD-rejects regardless of blockquote content"; this code
    # keeps that promise. Downgraded refs (corpus-missing OR verbatim-not-
    # required) are excluded because the writer cannot fetch a chunk that
    # does not exist and is not asked to quote verbatim from one.
    # Diagnostic supplement to the 2026-05-23 reason logic: this block
    # subsumes the prior "diagnostic clarity" gate that only set ``reason``
    # without flipping ``passed``.
    has_fetchable_refs = any(
        not record["corpus_missing"] and record["verbatim_required"]
        for record in reference_records
    )
    if has_fetchable_refs and not chunk_context_calls:
        passed = False
        if reason is None or reason == "topical_mismatch":
            reason = "step_b_skipped_no_get_chunk_context"
    # Per #1765, missing-corpus citations get rejected here — the proper fix is
    # plan-review-time corpus check that prevents plans from getting this far.
    # Until #1765 lands, this guard prevents shipping false authority.
    return {
        "passed": passed,
        "verdict": "WARN" if passed and warnings else "PASS" if passed else "REJECT",
        "severity": "WARN" if passed and warnings else "HARD",
        "required": required,
        "matched": sorted(matched),
        "missing": [ref for ref in references if ref not in matched],
        "blockquotes_checked": len(blockquote_records),
        "long_blockquotes_checked": len(long_blockquote_records),
        "search_text_calls": len(search_calls),
        "chunk_context_calls": len(chunk_context_calls),
        "textbook_result_hits": len(textbook_results),
        "min_words": TEXTBOOK_GROUNDING_MIN_WORDS,
        "downgraded": downgraded,
        "missing_corpus": missing_corpus,
        "warnings": warnings,
        "reason": reason,
        "unattributed_matches": unattributed_matches,
    }


def _advisory_immersion_pct(text: str, plan: Mapping[str, Any]) -> dict[str, Any]:
    """Compute advisory Ukrainian immersion ratio telemetry.

    This is the demoted form of the old immersion gate. It still strips JSX
    syntax before counting body tokens and adds learner-facing JSX strings
    back into the numerator/denominator, but it never hard-fails. Structural
    pass/fail decisions live in the L2 exposure, long-UK ceiling, and component
    density gates.
    """
    level = str(plan["level"]).lower()
    sequence = int(plan["sequence"])
    min_pct, max_pct = get_immersion_range(level, sequence)
    comment_stripped = _strip_comments(text)
    body = _strip_frontmatter_and_headings(comment_stripped)

    body_no_jsx = _JSX_BLOCK_RE.sub(" ", body)
    jsx_string_props: list[str] = []
    for jsx_block in _JSX_BLOCK_RE.findall(body):
        jsx_string_props.extend(_JSX_STRING_VALUE_RE.findall(jsx_block))
    counted_text = "\n".join([body_no_jsx, *jsx_string_props])

    tokens = _WORD_RE.findall(counted_text)
    uk_tokens = [token for token in tokens if _UK_WORD_RE.search(token)]
    pct = round((len(uk_tokens) / len(tokens) * 100), 2) if tokens else 0.0

    return {
        "passed": True,
        "pct": pct,
        "min_pct": min_pct,
        "max_pct": max_pct,
        "policy": get_immersion_policy(level, sequence)["key"],
    }


def _l2_exposure_floor_gate(text: str, plan: Mapping[str, Any]) -> dict[str, Any]:
    policy = get_immersion_policy(str(plan["level"]).lower(), int(plan["sequence"]))
    body = _strip_frontmatter_and_headings(_strip_comments(text))
    observed = {
        "uk_dialogue_lines": _count_uk_dialogue_lines(body),
        "vocab_entries": _count_vocab_entries(body),
        "uk_example_sentences": _count_uk_example_bullets(body),
        "uk_tab3_activities": len(_INJECT_RE.findall(text)),
    }
    required = {
        "uk_dialogue_lines": int(policy["min_uk_dialogue_lines"]),
        "vocab_entries": int(policy["min_vocab_entries"]),
        "uk_example_sentences": int(policy["min_uk_example_sentences"]),
        "uk_tab3_activities": int(policy["min_uk_tab3_activities"]),
    }
    reasons = [f"too_few_{key}" for key, required_count in required.items() if observed[key] < required_count]
    return {
        "passed": not reasons,
        "required": required,
        "observed": observed,
        "reason": reasons[0] if len(reasons) == 1 else ",".join(reasons) or None,
        "policy": policy["key"],
    }


def _count_uk_dialogue_lines(text: str) -> int:
    count = sum(1 for line in text.splitlines() if re.match(r"^\s*>\s", line) and _UK_WORD_RE.search(line))
    for jsx_block in _JSX_BLOCK_RE.findall(text):
        if _jsx_tag(jsx_block) != "DialogueBox":
            continue
        count += sum(1 for value in _jsx_text_values(jsx_block) if _UK_WORD_RE.search(value))
    return count


def _count_vocab_entries(text: str) -> int:
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if set(cells) <= {"", "---", ":---", "---:", ":---:"}:
            continue
        if any(_UK_WORD_RE.search(cell) for cell in cells) and any(re.search(r"[A-Za-z]", cell) for cell in cells):
            count += 1
    count += sum(1 for block in _JSX_BLOCK_RE.findall(text) if _jsx_tag(block) == "VocabCard")
    return count


def _count_uk_example_bullets(text: str) -> int:
    """Count UK example sentences exposed to the learner.

    Counts two pedagogical surfaces:

    1. **Bullet-list lines** (`- ...` / `* ...`) containing UK content.
       Used for routine-verb examples, phonetic-rule examples, trap
       explanations, etc.

    2. **Markdown table data rows** containing UK content. Contrast
       tables (Wrong / Right pairs), paradigm tables, IPA tables, and
       pronunciation reference tables are all valid UK example
       surfaces for the learner — the form is tabular but the content
       is example sentences. Skipping them under-counts modules that
       prefer tabular presentation. Surfaced 2026-05-17 by a1/m20
       Path A rebuild: writer produced 13 bullet examples + 8 table-
       row examples but counter saw only 13, failing the floor of 14
       by one despite pedagogical density well over the threshold.

    Header rows and `---` separator rows are excluded.
    """
    bullet_count = sum(1 for line in text.splitlines() if re.match(r"^\s*[-*]\s+", line) and _UK_WORD_RE.search(line))
    table_count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if set(cells) <= {"", "---", ":---", "---:", ":---:"}:
            continue
        if any(_UK_WORD_RE.search(cell) for cell in cells):
            table_count += 1
    return bullet_count + table_count


def _long_uk_ceiling_gate(
    text: str,
    plan: Mapping[str, Any],
    *,
    grounding_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    policy = get_immersion_policy(str(plan["level"]).lower(), int(plan["sequence"]))
    max_unsupported = int(policy["max_unsupported_uk_words"])
    support_proximity = int(policy["support_proximity"])
    runs = _unsupported_uk_runs(
        text,
        max_unsupported,
        support_proximity,
        grounding_evidence=grounding_evidence,
    )
    return {
        "passed": not runs,
        "required": {
            "max_unsupported_uk_words": max_unsupported,
            "support_proximity": support_proximity,
        },
        "observed": {"offending_runs": len(runs)},
        "reason": "long_uk_without_gloss" if runs else None,
        "offending_runs": runs[:5],
        "policy": policy["key"],
    }


def _unsupported_uk_runs(
    text: str,
    max_unsupported: int,
    support_proximity: int,
    *,
    grounding_evidence: Mapping[str, Any] | None = None,
) -> list[str]:
    text = _strip_frontmatter_and_headings(_strip_comments(text))
    text = _FENCED_CODE_RE.sub(" ", text)
    text = _JSX_BLOCK_RE.sub(" ", text)
    text = re.sub(r"(?m)^\s*\|.*\|\s*$", " ", text)
    offending: list[str] = []
    for segment in _unsupported_run_segments(
        text,
        grounding_evidence=grounding_evidence,
    ):
        tokens = list(_WORD_RE.finditer(segment))
        run_start: int | None = None
        run_end: int | None = None
        for index, token in enumerate(tokens):
            value = token.group(0)
            if _UK_WORD_RE.search(value):
                if run_start is None:
                    run_start = index
                run_end = index
                continue
            if run_start is not None and run_end is not None:
                _append_unsupported_run(
                    offending,
                    tokens,
                    run_start,
                    run_end,
                    max_unsupported,
                    support_proximity,
                )
            run_start = None
            run_end = None
        if run_start is not None and run_end is not None:
            _append_unsupported_run(offending, tokens, run_start, run_end, max_unsupported, support_proximity)
    return offending[:5]


def _unsupported_run_segments(
    text: str,
    *,
    grounding_evidence: Mapping[str, Any] | None = None,
) -> list[str]:
    """Return UK runs that lack inline English support.

    Citation-grounded source blockquotes are exempted as textbook grounding,
    not learner-target prose. Learner practice blockquotes remain in scope.
    """
    grounded_keys = _grounded_citation_keys(grounding_evidence)
    segments: list[str] = []
    prose_lines: list[str] = []
    quote_lines: list[str] = []

    def flush_prose() -> None:
        nonlocal prose_lines
        if prose_lines:
            segments.append("\n".join(prose_lines))
            prose_lines = []

    def flush_quote() -> None:
        nonlocal quote_lines
        if quote_lines:
            quote_text = "\n".join(quote_lines)
            if not _is_grounded_source_blockquote(quote_text, grounded_keys):
                segments.append(quote_text)
            quote_lines = []

    for line in text.splitlines():
        quote_match = re.match(r"^\s*>\s?(?P<body>.*)$", line)
        if quote_match:
            flush_prose()
            quote_lines.append(quote_match.group("body"))
            continue
        if re.match(r"^\s*[-*]\s+", line):
            flush_prose()
            flush_quote()
            segments.append(line)
            continue
        if not line.strip():
            flush_prose()
            flush_quote()
            continue
        flush_quote()
        prose_lines.append(line)
    flush_prose()
    flush_quote()
    return segments


def _grounded_citation_keys(
    grounding_evidence: Mapping[str, Any] | None,
) -> set[CitationKey]:
    if not isinstance(grounding_evidence, Mapping):
        return set()
    matched = grounding_evidence.get("matched")
    if not isinstance(matched, list):
        return set()
    return {key for value in matched if (key := extract_citation_key(value)) is not None}


def _is_grounded_source_blockquote(
    quote_text: str,
    grounded_keys: set[CitationKey],
) -> bool:
    if not grounded_keys:
        return False
    quote_key = extract_citation_key(quote_text)
    if quote_key is None:
        return False
    return any(citation_keys_match(quote_key, grounded_key) for grounded_key in grounded_keys)


def _append_unsupported_run(
    offending: list[str],
    tokens: list[re.Match[str]],
    start: int,
    end: int,
    max_unsupported: int,
    support_proximity: int,
) -> None:
    run_len = end - start + 1
    if run_len <= max_unsupported or _has_english_support(tokens, start, end, support_proximity):
        return
    words = [token.group(0) for token in tokens[start : min(end + 1, start + 40)]]
    if _is_ukrainian_alphabet_sequence(words):
        return
    suffix = " ..." if run_len > len(words) else ""
    offending.append(" ".join(words) + suffix)


_UKRAINIAN_ALPHABET_ORDER = tuple("АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ")


def _is_ukrainian_alphabet_sequence(words: Sequence[str]) -> bool:
    letters = [word.upper() for word in words]
    if len(letters) < 8:
        return False
    if any(len(letter) != 1 or letter not in _UKRAINIAN_ALPHABET_ORDER for letter in letters):
        return False
    joined = "".join(letters)
    return joined in "".join(_UKRAINIAN_ALPHABET_ORDER)


def _has_english_support(
    tokens: list[re.Match[str]],
    start: int,
    end: int,
    support_proximity: int,
) -> bool:
    before = tokens[max(0, start - support_proximity) : start]
    after = tokens[end + 1 : min(len(tokens), end + 1 + support_proximity)]
    return any(re.search(r"[A-Za-z]", token.group(0)) for token in (*before, *after))


def _component_density_gate(text: str, plan: Mapping[str, Any]) -> dict[str, Any]:
    policy = get_immersion_policy(str(plan["level"]).lower(), int(plan["sequence"]))
    required = dict(policy["required_components"])
    mismatches: list[dict[str, Any]] = []
    observed: list[dict[str, Any]] = []
    ignored_components: list[str] = []
    for jsx_block in _JSX_BLOCK_RE.findall(_strip_comments(text)):
        tag = _jsx_tag(jsx_block)
        if tag is None or tag == "VocabCard":
            continue
        if tag not in required:
            ignored_components.append(tag)
            continue
        min_pct, max_pct = required[tag]
        component_text = _component_language_text(tag, jsx_block)
        tokens = _WORD_RE.findall(component_text)
        if not tokens:
            continue
        uk_pct = round(
            len([token for token in tokens if _UK_WORD_RE.search(token)]) / len(tokens) * 100,
            2,
        )
        record = {
            "component_tag": tag,
            "observed_pct": uk_pct,
            "expected_range": [int(min_pct), int(max_pct)],
        }
        observed.append(record)
        if uk_pct < int(min_pct) or uk_pct > int(max_pct):
            mismatches.append(record)
    return {
        "passed": not mismatches,
        "required": required,
        "observed": observed,
        "reason": "component_density_mismatch" if mismatches else None,
        "mismatches": mismatches,
        "ignored_components": sorted(set(ignored_components)),
        "policy": policy["key"],
    }


def _jsx_tag(jsx_block: str) -> str | None:
    match = re.match(r"<([A-Z][A-Za-z0-9]*)\b", jsx_block.strip())
    return match.group(1) if match else None


def _jsx_text_values(jsx_block: str) -> list[str]:
    """Extract canonical UK-content attributes from V7 components.

    `text=` is the legacy convention; `uk=` is the V7 DialogueBox convention
    introduced by the a1-m15-24 shape contract (#1964 / PR #1962).
    """
    text_attrs = re.findall(r"\btext\s*(?:=|:)\s*\"([^\"\n]*)\"", jsx_block)
    uk_attrs = re.findall(r"\buk\s*(?:=|:)\s*\"([^\"\n]*)\"", jsx_block)
    return text_attrs + uk_attrs


def _component_language_text(tag: str, jsx_block: str) -> str:
    if tag == "DialogueBox":
        text_values = _jsx_text_values(jsx_block)
        if text_values:
            return "\n".join(text_values)
    paired = re.match(
        r"<([A-Z][A-Za-z0-9]*)\b[^>]*>(.*)</\1>",
        jsx_block.strip(),
        flags=re.DOTALL,
    )
    if paired:
        return paired.group(2)
    return "\n".join(_JSX_STRING_VALUE_RE.findall(jsx_block))


def _split_immersion_sentences(text: str) -> list[str]:
    """Split prose for the immersion gate's Ukrainian sentence-length check."""
    text = re.sub(r"(?m)^\s*#{1,6}\s+.*$", "\n", text)
    sentences = []
    for sentence in _SENTENCE_SPLIT_RE.split(text):
        sentence = sentence.strip()
        if sentence:
            sentences.append(sentence)
    return sentences


def _long_ukrainian_sentences(text: str) -> list[str]:
    text = _FENCED_CODE_RE.sub(" ", text)
    return [sentence for sentence in _split_immersion_sentences(text) if len(_UK_WORD_RE.findall(sentence)) > 10]


def _inject_activity_gate(
    text: str,
    activities: list[dict[str, Any]],
    plan: Mapping[str, Any] | None = None,
    module_dir: Path | None = None,
) -> dict[str, Any]:
    ids = {str(activity.get("id")) for activity in activities if activity.get("id")}
    injected = _INJECT_RE.findall(text)
    missing = [activity_id for activity_id in injected if activity_id not in ids]
    injected_ids = set(injected)
    workbook_ids: set[str] = set()
    if module_dir is not None:
        activities_path = module_dir / "activities.yaml"
        if activities_path.exists():
            try:
                raw_activities = load_yaml(activities_path)
            except Exception:
                raw_activities = None
            if isinstance(raw_activities, dict):
                workbook_section = raw_activities.get("workbook", [])
                if isinstance(workbook_section, list):
                    workbook_ids = {
                        str(activity.get("id"))
                        for activity in workbook_section
                        if isinstance(activity, dict) and activity.get("id")
                    }
    unused = sorted((ids - injected_ids) - workbook_ids)
    workbook_only = sorted((ids - injected_ids) & workbook_ids)
    if plan is not None:
        archetype = resolve_module_archetype(str(plan.get("level") or ""), int(plan.get("sequence") or 0))
        if archetype.get("id") in {
            "a1-zero-script-onboarding",
            "a1-script-building",
            "a1-first-contact-survival",
        }:
            workbook_only = sorted(set(workbook_only) | set(unused))
            unused = []
    reasons = []
    if missing:
        reasons.append("missing_activity_ids")
    if unused:
        reasons.append("unused_activities_not_injected")
    return {
        "passed": not missing and not unused,
        "injected": injected,
        "missing": missing,
        "unused": unused,
        "workbook_only": workbook_only,
        "reason": ",".join(reasons) or None,
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

    hits = sorted({pattern for pattern in AI_CONTAMINATION_PATTERNS if re.search(pattern, text, flags=re.IGNORECASE)})
    return {"passed": not hits, "hits": hits}


# ---- engagement_floor ------------------------------------------------------
#
# Replaces what V6 paid the LLM `engagement & tone` reviewer to evaluate. Every
# item below is a deterministic count or absence check — exactly the kind of
# work that should live in code per the project deal "don't dim-check what
# code can check." The LLM `engagement` dim survives but its rubric narrows
# to judgment-only items (does the hook resonate, does the tone land) that
# regex can't measure.
#
# Floors restored from V6 `v6-write.md` § "Writing Quality" line 537 and
# `docs/best-practices/module-content-quality.md` § "Required engagement
# elements" (lines 92-102). Build #11 a1/my-morning REVISE-with-no-critique
# (2026-05-22) was the exact failure mode: writer emitted 0 callouts, 0
# direct addresses, 0 META_NARRATION violations — but the reviewer had no
# rubric, so it scored 6.5 without a concrete shortfall to name.

#: Markdown callout patterns we accept as engagement signal. Covers Site
#: directive blocks (``:::tip``) and GitHub-style admonitions
#: (``[!myth-buster]``). Both render to highlighted blocks in the MDX output.
_CALLOUT_PATTERN = re.compile(
    r"(?m)^(?:"
    r":::\s*(?:tip|caution|note|warning|important|info)\b"
    r"|"
    r"> *\[!(?:tip|note|warning|important|caution|info|myth-buster|history-bite)\]"
    r")",
    flags=re.IGNORECASE,
)

#: English META_NARRATION patterns from V6 ``v6-review.md`` line 118
#: (engagement DEDUCT list) AND the V7 writer prompt's own banned list at
#: ``linear-write.md`` § "Tone and immersion (mandatory)". The writer's
#: persona is a teacher addressing the learner, not a narrator describing
#: the lesson container. Self-referential framing ("In this lesson...")
#: breaks immersion and adds zero pedagogical signal. V7 already TELLS the
#: writer not to do this; what was missing was deterministic enforcement.
#:
#: Note: bare ``Notice that…`` / ``Observe how…`` are deliberately NOT in
#: this list. V7 forbids them in the abstract, but V6 rewarded them when
#: content-anchored ("Notice the soft sign in **писатися**"). Deciding
#: which is which requires judgment; that part stays in the LLM dim.
_META_NARRATION_PATTERNS = (
    r"\bLet us (?:begin|explore|examine|look|learn|see|consider|now)\b",
    r"\bIn this (?:section|module|lesson|chapter|unit)\b",
    r"\bThis section teaches\b",
    r"\b(?:learners|students) will\b",
    r"\bThe (?:activity|exercise) asks\b",
    r"\bWelcome to (?:[ABC][12]\b|the [ABC][12]\b)",
    r"\bCongratulations on completing\b",
    r"\bYou have unlocked\b",
    r"\bYou now possess\b",
    r"\bYour journey (?:begins|starts|continues)\b",
)
_META_NARRATION_RE = re.compile(
    "|".join(_META_NARRATION_PATTERNS),
    flags=re.IGNORECASE,
)


def _engagement_floor_gate(text: str, plan: Mapping[str, Any]) -> dict[str, Any]:
    """Count engagement signals against the V6 + module-content-quality floor.

    Two signals tracked (scope intentionally tight — direct-address phrase
    counting is deferred because the content-anchored vs generic distinction
    requires judgment that this gate can't make):

    1. **Callouts** (Site ``:::tip``-style or GitHub ``[!myth-buster]``).
       Minimum 2 per module (``docs/best-practices/module-content-quality.md``
       line 97; V6 ``v6-write.md`` line 537 said 3, we relax to 2 to match
       the documented standard). Callouts are unambiguous engagement signal
       because their syntax forces content-anchored prose (mnemonics, myth
       busts, cultural notes, common-mistake callouts).
    2. **META_NARRATION violations** (``In this section...``, ``Welcome to
       A2``, ``Let us begin...``, ``You have unlocked``, ``Your journey
       begins``...). HARD 0. These are persona breaks that V7's writer
       prompt already forbids in prose but never enforced.

    The threshold floor is intentionally low. Exceeding is rewarded by the
    LLM engagement dim's judgment-only rubric, not the gate. This gate just
    catches the "0 callouts, 3 META_NARRATION lines" failure mode that
    build #11 a1/my-morning (2026-05-22) shipped past silently.
    """
    callout_hits = _CALLOUT_PATTERN.findall(text)
    meta_hits = sorted({m.lower().strip() for m in _META_NARRATION_RE.findall(text)})

    # callout_min: 2 → 1 per user direction 2026-05-23 (handoff decision row B).
    # Writers consistently emit 1 callout; "minimum 2" was aspirational not
    # empirical. The full engagement_floor still catches modules with 0 callouts.
    callout_min = 1
    callouts_ok = len(callout_hits) >= callout_min
    meta_ok = not meta_hits

    issues: list[str] = []
    if not callouts_ok:
        issues.append(
            f"callouts: found {len(callout_hits)}, minimum {callout_min} "
            f"(emit :::tip / :::note / :::caution or [!myth-buster] blocks; "
            f"content-anchored mnemonics, myth-busts, cultural notes, or "
            f"common-mistake reminders)"
        )
    if not meta_ok:
        issues.append(
            f"meta_narration: {len(meta_hits)} distinct violations — "
            f"{', '.join(meta_hits[:3])} (persona breaks; address the "
            f"learner directly with content-anchored claims, do not narrate "
            f"the lesson container)"
        )

    return {
        "passed": callouts_ok and meta_ok,
        "callout_count": len(callout_hits),
        "callout_min": callout_min,
        "meta_narration_hits": meta_hits,
        "issues": issues,
        "_plan_word_target": int(plan.get("word_target", 0)),
    }


# ---- russianisms_strict ----------------------------------------------------
#
# Wraps the project's mature russianism detection layer into a pipeline gate.
# Two complementary detectors run:
#
# - ``scripts.audit.checks.russicism_detection.check_russicisms``: hand-curated
#   regex patterns for known Russian calques + lexical Russicisms (e.g.
#   ``приймати участь``, ``самий кращий``, ``получати``, ``відноситися``,
#   ``слідуючий``, ``давайте попрактикуємо``...). 676 lines of patterns;
#   each match carries a `fix` suggestion and a `note` explaining why.
# - ``scripts.audit.checks.russicism_detection.check_ua_gec_calques``:
#   UA-GEC corpus (8,937 human-annotated error→correction pairs from the
#   Grammarly UA team), filtered to russianism-relevant tags
#   (F/Calque, F/Collocation, G/Case, G/Gender).
#
# Both detectors classify findings by severity (``critical`` / ``warning`` /
# ``info``). The gate fails on any ``critical`` finding from either source.
# Lower-severity findings appear in the report for visibility but do not
# block the build — they surface to the LLM review dim as advisory signal.
#
# This replaces what V6 covered with a 10-word ``SEVERE_RUSSIANISMS`` list
# in ``scripts/build/quick_verify.py`` (#1189). The V7 pipeline never wired
# quick_verify in; this gate ports the canonical detection layer instead of
# resurrecting the shorter list.


def _russianisms_strict_gate(text: str) -> dict[str, Any]:
    """Run both russianism detectors; fail on any ``critical`` finding.

    Returns the merged findings keyed by source so the writer correction
    path (ADR-008) can target either detector's output independently. The
    LLM ``naturalness`` / ``decolonization`` dims read advisory-severity
    findings as residual evidence — they are NOT scored deterministically
    here, only the critical tier is gated.
    """
    from scripts.audit.checks.russicism_detection import (
        check_russicisms,
        check_ua_gec_calques,
    )

    rus_findings = check_russicisms(text) or []
    gec_findings = check_ua_gec_calques(text) or []

    critical_findings: list[dict[str, Any]] = []
    warning_findings: list[dict[str, Any]] = []

    for source_name, findings in (
        ("russicism_detection", rus_findings),
        ("ua_gec_calques", gec_findings),
    ):
        for finding in findings:
            severity = str(finding.get("severity", "")).lower()
            tagged = {"source": source_name, **finding}
            if severity == "critical":
                critical_findings.append(tagged)
            elif severity == "warning":
                warning_findings.append(tagged)

    return {
        "passed": not critical_findings,
        "critical_findings": critical_findings,
        "warning_findings": warning_findings,
        "critical_count": len(critical_findings),
        "warning_count": len(warning_findings),
    }


_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_DIALOGUE_BOX_RE = re.compile(
    r"<DialogueBox\b(?:[^>]*/>|.*?</DialogueBox>)",
    re.DOTALL | re.IGNORECASE,
)
_SHO_RE = re.compile(r"(?i)\bшо\b")


def _mask_region(match: re.Match[str]) -> str:
    """Replace a matched region with spaces while preserving newlines.

    Preserving newlines keeps the line numbers in the masked text aligned
    with the original text, so the matcher reports the line where ``шо``
    actually appears in the writer's module.md.
    """
    return "".join("\n" if ch == "\n" else " " for ch in match.group(0))


def _register_consistency_gate(text: str, plan: Mapping[str, Any]) -> dict[str, Any]:
    """WARN-only register-consistency gate for the literary↔colloquial pair.

    `шо` (colloquial reduction of `що`) is a native Ukrainian form,
    NOT surzhyk — Antonenko-Davydovych has no entry for it, Russian has
    `что`/`[што]` (not `шо`), and `шо` is widespread in colloquial speech
    across all Ukrainian-speaking regions. The diglossia is a TEACHING
    TARGET: learners benefit from knowing the literary↔colloquial pair
    and when each is appropriate.

    This gate flags out-of-register `шо` for A1-B2 modules as WARN (never
    HARD). A1-B2 learners benefit from explicit register scaffolding; C1+
    learners are expected to handle the distinction without it. Exempt
    contexts: ``<DialogueBox>`` JSX blocks (open + close OR self-closing),
    markdown ``>`` blockquotes, and fenced code blocks — all are legitimate
    colloquial-register surfaces.

    Pre-mask exempt regions with whitespace (preserving newlines so line
    numbers stay aligned with the original text), then scan for ``шо`` on
    the masked text. The masking approach eliminates the line-by-line
    state-machine edge cases that miss/over-count when JSX tags share a
    line with prose. See PR #2307 review for the original state-machine
    bug analysis.
    """
    level = str(plan.get("level", "")).lower()

    if level in {"c1", "c2", "pro"}:
        return {
            "passed": True,
            "verdict": "PASS",
            "severity": "WARN",
            "violations": [],
            "violation_count": 0,
            "scope_level": level,
        }

    text_masked = _CODE_BLOCK_RE.sub(_mask_region, text)
    text_masked = _DIALOGUE_BOX_RE.sub(_mask_region, text_masked)

    masked_lines = text_masked.splitlines()
    original_lines = text.splitlines()

    # Mask blockquote lines (those whose stripped form starts with ``>``).
    # Per-line masking avoids the regex overhead and respects the
    # line-number alignment guarantee from _mask_region.
    for idx, line in enumerate(masked_lines):
        if line.strip().startswith(">"):
            masked_lines[idx] = " " * len(line)

    violations: list[dict[str, Any]] = []
    for line_no, masked_line in enumerate(masked_lines, 1):
        for match in _SHO_RE.finditer(masked_line):
            context_line = (
                original_lines[line_no - 1].strip()
                if line_no <= len(original_lines)
                else ""
            )
            violations.append(
                {
                    "form": match.group(0),
                    "line": line_no,
                    "context": context_line[:100],
                }
            )

    return {
        "passed": True,
        "verdict": "WARN" if violations else "PASS",
        "severity": "WARN",
        "violations": violations,
        "violation_count": len(violations),
        "scope_level": level,
    }


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
            prop["name"] for prop in component.get("props", {}).get("required", []) if isinstance(prop, dict)
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
            if isinstance(comp_prop, str) and comp_prop not in _COMPONENT_PROP_GATE_JSX_ONLY_PROPS
        ]
        missing = [field for field in required_authoring_fields if field not in activity]
        if missing:
            errors.append(f"{activity.get('id', '<missing-id>')}: missing required props " + ", ".join(missing))
    return {"passed": not errors, "errors": errors}


def _strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end >= 0:
            text = text[end + 4 :]
    return text


def _strip_frontmatter_and_headings(text: str) -> str:
    text = _strip_frontmatter(text)
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
def _textbook_quote_fidelity_gate(
    module_text: str,
    level: str | None = None,
    *,
    module_slug: str | None = None,
) -> dict[str, Any]:
    """Verify textbook quote fidelity against the sources DB."""
    import re

    from rapidfuzz import distance

    from scripts.build.seminar_quote_exemptions import lookup_seminar_quote_exemption
    from scripts.wiki.sources_db import search_literary, search_textbooks

    violations: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    checked = 0
    level_key = str(level or "").strip().lower()
    slug_key = str(module_slug or "").strip().lower()
    quotes = _extract_blockquote_records(module_text, level=level)

    def _normalize(s: str) -> str:
        s = re.sub(r'[^а-яіїєґА-ЯІЇЄҐ0-9]', '', s.lower())
        return s

    def _is_textbook_attribution(attribution: str) -> bool:
        return bool(
            re.search(r"\bGrade\s+\d+\b", attribution, flags=re.IGNORECASE)
            and re.search(r"\bp\.?\s*\d+", attribution, flags=re.IGNORECASE)
        )

    def _corpus_fidelity_violation(text: str, attr: str) -> dict[str, Any] | None:
        ukr_words = re.findall(r'[а-яіїєґА-ЯІЇЄҐ]+', text)
        keywords = {w.lower() for w in ukr_words if len(w) >= 3}
        if not keywords:
            return None

        search_fn = search_textbooks
        corpus_name = "textbook corpus"
        if level_key in SEMINAR_LEVELS and not _is_textbook_attribution(attr):
            search_fn = search_literary
            corpus_name = "literary corpus"

        try:
            hits = search_fn(keywords, 20)
        except Exception:
            hits = []

        if not hits:
            return {
                "quote": text,
                "attribution": attr,
                "reason": f"No match in {corpus_name}",
            }

        norm_quote = _normalize(text)
        best_diff = float('inf')
        best_source_text = ""

        for hit in hits:
            chunk = hit.get("text", "")
            norm_chunk = _normalize(chunk)

            l_q = len(norm_quote)
            if l_q == 0:
                continue

            if norm_quote in norm_chunk:
                best_diff = 0
                best_source_text = chunk
                break

            for k in range(max(1, len(norm_chunk) - l_q + 1)):
                window = norm_chunk[k:k+l_q]
                d = distance.Levenshtein.distance(norm_quote, window)
                if d < best_diff:
                    best_diff = d
                    best_source_text = chunk

            if len(norm_chunk) < l_q:
                d = distance.Levenshtein.distance(norm_quote, norm_chunk)
                if d < best_diff:
                    best_diff = d
                    best_source_text = chunk

        if best_diff >= 3:
            return {
                "quote": text,
                "attribution": attr,
                "reason": f"Text differs by >=3 chars (diff: {best_diff})",
                "nearest_source": best_source_text,
            }
        return None

    for q in quotes:
        text = q["quote"]
        attr = q["attribution"]
        nv = q["no_verify"]

        if not text:
            continue

        checked += 1

        if not attr:
            if not nv:
                violations.append({
                    "quote": text,
                    "attribution": "",
                    "reason": "Missing attribution without NO_VERIFY"
                })
            continue

        if nv and level_key not in SEMINAR_LEVELS:
            continue

        violation = _corpus_fidelity_violation(text, attr)
        if violation is None:
            continue

        if nv and level_key in SEMINAR_LEVELS:
            exemption = lookup_seminar_quote_exemption(slug_key, text)
            if exemption:
                warnings.append({
                    "quote": text,
                    "attribution": attr,
                    "reason": "NO_VERIFY seminar quote exempted from corpus match",
                    "exemption": exemption,
                })
                continue
            violations.append({
                "quote": text,
                "attribution": attr,
                "reason": (
                    "NO_VERIFY on seminar level but fragment not corpus-attested "
                    "and not exempted"
                ),
            })
            continue

        violations.append(violation)

    passed = len(violations) == 0
    if violations:
        message = f"verify_quote: {checked} checked, {len(violations)} violations"
    elif warnings:
        message = (
            f"verify_quote: {checked} verified, {len(warnings)} seminar exemptions"
        )
    else:
        message = f"verify_quote: {checked} verified"
    return {
        "passed": passed,
        "checked": checked,
        "violations": violations,
        "warnings": warnings,
        "message": message,
        "verdict": "WARN" if passed and warnings else "PASS" if passed else "REJECT",
        "severity": "WARN" if passed and warnings else "HARD" if not passed else None,
    }
