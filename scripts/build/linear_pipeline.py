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
import xml.etree.ElementTree as ET
from collections.abc import Callable, Collection, Mapping, Sequence
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

from scripts.audit.failure_classes import FailureClass, FailureRecord
from scripts.build.citation_matcher import (
    CitationKey,
    citation_keys_match,
    extract_citation_key,
    extract_plan_reference_titles,
    normalize_citation_ref,
)
from scripts.build.prompt_builder import DOWNSTREAM_TOKENS, TOKEN_RE, render_prompt
from scripts.common.thresholds import QG_DIMS, aggregate_review
from scripts.config import get_immersion_policy, get_immersion_range, get_immersion_rule
from scripts.generate_mdx.core import generate_mdx
from scripts.pipeline.learner_state import build_learner_state, format_learner_state

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
    "deepseek-tools",
    "qwen-tools",
    "agy-tools",
)
WRITER_DEFAULTS: dict[str, dict[str, str]] = {
    "claude-tools": {"model": "claude-opus-4-7", "effort": "xhigh"},
    "gemini-tools": {"model": "gemini-3.1-pro-preview", "effort": "high"},
    "codex-tools": {"model": "gpt-5.5", "effort": "high"},
    "grok-tools": {"model": "grok-4.3", "effort": "medium"},
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
    "deepseek-tools",
    "qwen-tools",
    "agy-tools",
)
REVIEWER_DEFAULTS: dict[str, dict[str, str]] = {
    "claude-tools": {"model": "claude-opus-4-7", "effort": "xhigh"},
    "gemini-tools": {"model": "gemini-3.1-pro-preview", "effort": "high"},
    "codex-tools": {"model": "gpt-5.5", "effort": "high"},
    "grok-tools": {"model": "grok-4.3", "effort": "medium"},
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
    r"^[\s>#\-*]*(?P<name>"
    + "|".join(re.escape(name) for name in WRITER_ARTIFACTS)
    + r")\s*:?\s*$"
)

PYTHON_QG_GATE_ORDER = (
    "tool_theatre",
    "activity_schema",
    "word_count",
    "plan_sections",
    "formatting_standards",
    "vesum_verified",
    "citations_resolve",
    "textbook_grounding",
    "resources_search_attempted",
    "immersion_advisory",
    "l2_exposure_floor",
    "long_uk_ceiling",
    "component_density",
    "inject_activity_ids",
    "activity_types",
    "ai_slop_clean",
    "component_props",
    "russianisms_clean",
    "surzhyk_clean",
    "calques_clean",
    "paronym_clean",
)
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
DICTIONARY_CANDIDATE_GATES = frozenset(
    {
        "vesum_verified",
        "russianisms_clean",
        "surzhyk_clean",
        "calques_clean",
        "paronym_clean",
        "citations_resolve",
    }
)
REVIEWER_FIX_GATES = DICTIONARY_CANDIDATE_GATES | frozenset(
    {
        "l2_exposure_floor",
        "long_uk_ceiling",
        "component_density",
        "ai_slop_clean",
    }
)
PIPELINE_INSERT_GATES = frozenset({"inject_activity_ids"})
TERMINAL_ZERO_RETRY_GATES = frozenset(
    {
        "component_props",
        "previously_passed_regression",
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
    "word_budget": (
        r"<word_budget\b[^>]*>.*?\S.*?</word_budget>",
    ),
    "plan_vocab": (
        r"<plan_vocab\b[^>]*>.*?\S.*?</plan_vocab>",
    ),
    "register": (
        r"<register\b[^>]*>.*?\S.*?</register>",
    ),
    "teaching_sequence": (
        r"<teaching_sequence\b[^>]*>.*?\S.*?</teaching_sequence>",
    ),
    "verification_plan": (
        r"<verification_plan\b[^>]*>.*?\S.*?</verification_plan>",
    ),
    "verification_trace": (
        r"<verification_trace\b[^>]*>.*?\S.*?</verification_trace>",
    ),
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
    "mcp_sources_",    # gemini-cli 0.42.0+ single-underscore convention
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
WRITER_AGENT_ANNOTATION_TOOLS = frozenset(
    {
        "update_topic",  # gemini-cli 0.42.0+ strategic-intent / title / summary
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
    "claude_extensions/agents/curriculum-orchestrator.md",
    "claude_extensions/rules/**",
    ".claude/rules/**",
    "*handoff*",
    "*orchestration*",
    "*dispatch*",
)
RESOURCE_ROLES = frozenset(
    {
        "textbook",
        "youtube",
        "video",
        "blog",
        "podcast",
        "audio",
        "article",
        "wiki",
    }
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

RULE_VOICE_META = "#R-VOICE-META"
RULE_BAD_FORM_MARKER = "#R-BAD-FORM-MARKER"
RULE_VESUM_ALL_WORDS = "#R-VESUM-ALL-WORDS"
RULE_IMPL_MAP_COMPLETE = "#R-IMPL-MAP-COMPLETE"
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
        optional_item_fields=frozenset({
            "notes",
            "description",
            "source_ref",
            "packet_chunk_id",
            "url",
            "section",
            "page",
            "pages",
            "author",
            "channel",
            "source",
            "match_reason",
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
_WARNING_QUOTE_RE = re.compile(
    # Four alternations: quotes, guillemets, closed italics, unclosed italics.
    # The unclosed-italic arm requires the inner span to be Cyrillic-only
    # (no asterisk, no whitespace, no punctuation) so it stops cleanly at
    # the next boundary instead of swallowing the rest of the sentence.
    r'\b(?:not|не)\s+(?:'
    r'["«][^"»]+["»]'
    r'|\*[^*\n]+?\*'
    r'|\*[A-Za-zА-ЯІЇЄҐа-яіїєґ\'ʼ-]+'
    r')',
    re.IGNORECASE,
)

_STANDALONE_POSTFIX_FRAGMENTS = frozenset(
    {"ся", "сь", "тся", "тсь", "ться", "шся", "шсь", "чся", "чсь"}
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
_ERROR_CORRECTION_REQUIRED_ITEM_FIELDS = frozenset({"sentence", "error"})
_ERROR_CORRECTION_OPTIONAL_ITEM_FIELDS = frozenset(
    {"answer", "correction", "options", "explanation"}
)
_ACTIVITY_ITEM_AUTHORING_FIELDS: dict[str, frozenset[str]] = {
    _ERROR_CORRECTION_TYPE: (
        _ERROR_CORRECTION_REQUIRED_ITEM_FIELDS
        | _ERROR_CORRECTION_OPTIONAL_ITEM_FIELDS
    ),
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
                raise LinearPipelineError(
                    "build_knowledge_packet requires plan_path or level+slug"
                )
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
                raise LinearPipelineError(
                    "build_wiki_manifest_data requires plan_path or level+slug"
                )
            plan_path = plan_path_for(level.lower(), slug)
        plan_data = load_plan(plan_path)
    else:
        plan_data = dict(plan)
    validate_plan(plan_data)

    level_key = str(level or plan_data["level"]).lower()
    slug_key = str(slug or plan_data["slug"]).strip()
    article_paths = _wiki_article_paths(level_key, slug_key)
    if not article_paths:
        raise LinearPipelineError(
            f"No wiki article found for level={level_key!r}, slug={slug_key!r}"
        )
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
        ):
            merged.setdefault(key, [])
            for item in manifest.get(key, []):
                copied = dict(item)
                prefix = str(copied.get("id") or "").split("-", 1)[0] or key[:4]
                copied["id"] = f"{prefix}-{len(merged[key]) + 1}"
                merged[key].append(copied)
        merged.setdefault("external_resources", [])
        merged["external_resources"].extend(manifest.get("external_resources", []))
        merged["wiki_path"] = f"{merged['wiki_path']}; {manifest['wiki_path']}"
    if merged is not None:
        validate_manifest(merged)
    return merged or {}


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
        return (
            "## Dictionary context\n\n"
            f"*Dictionary context unavailable: {type(exc).__name__}: {exc}*"
        )

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
            entry.append(
                f"  - Definition: {_truncate_prompt_text(definition, definition_chars)}"
            )
        else:
            entry.append("  - Definition: Not found in SUM-11.")

        style_note = _dictionary_hit_text(style_notes)
        if style_note:
            entry.append(
                f"  - Style note: {_truncate_prompt_text(style_note, definition_chars)}"
            )

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
                    missing_reason.append(
                        f"source_file not in corpus for {author} Grade {grade}"
                    )
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
            missing_reason.append(
                f"page {page} not in corpus for {', '.join(source_files)}"
            )
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
        and "textbook" in str(
            hit.get("source_type") or hit.get("corpus") or hit.get("source") or ""
        ).casefold()
    ]
    return textbook_hits[:limit]


def _build_textbook_excerpt_context(
    plan: Mapping[str, Any],
    level: str,
) -> str:
    references = [
        str(title).strip()
        for title in extract_plan_reference_titles(plan)
        if str(title).strip()
    ]
    if not references:
        return ""

    topic_query = _plan_topic_query(plan)
    lines = ["## Textbook Excerpts (verbatim, must be cited)", ""]
    found_any = False
    for title in references:
        query = f"{title} {topic_query}".strip()
        missing_reasons: list[str] = []
        direct_hits = _lookup_textbook_reference_chunk(
            title,
            limit=1,
            missing_reason=missing_reasons,
        )
        hits = (
            direct_hits
            if direct_hits is not None
            else _search_textbook_hits(query, level=level, limit=1)
        )
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
        raise LinearPipelineError(
            f"No wiki article found for level={level!r}, slug={slug!r}"
        )

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
        parts.append(
            f"### Вікі: {rel_path}\n\n"
            f"Article: `wiki/{rel_path}`\n\n"
            f"{content}{source_block}"
        )

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
        f"**Module:** {plan['module']} | **Level:** {plan['level']} | "
        f"**Slug:** {plan['slug']}",
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
            lines.append(
                f"- **{anchor['section']}** — {anchor['claim']} "
                f"({anchor['citation']})"
            )
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
            "- `mcp__sources__search_style_guide` for russianisms, surzhyk, "
            "calques, and paronym-risk phrases.",
            "- `mcp__sources__search_definitions` for СУМ-11 definitions and "
            "usage disambiguation.",
            "",
            "Verify suspicious forms before using them in prose, vocabulary, "
            "activities, or resources. Do not call legacy `scripts.rag` or "
            "Qdrant retrieval for this packet.",
            "",
            "## Full Wiki Context",
            "",
            wiki_packet,
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


def writer_prompt_path(writer_family: str) -> Path:
    prompt_filename = PROMPT_BY_WRITER.get(writer_family, "linear-write.md")
    return PROJECT_ROOT / "scripts" / "build" / "phases" / prompt_filename


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
    wiki_manifest: str | Mapping[str, Any] | None = None,
    implementation_map: Mapping[str, Any] | None = None,
    writer: str = "claude-tools",
) -> str:
    return render_phase_prompt(
        writer_prompt_path(writer),
        writer_context(
            plan,
            plan_content,
            knowledge_packet,
            wiki_manifest,
            implementation_map=implementation_map,
            writer=writer,
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
    if gate == "vesum_verified":
        return [RULE_VESUM_ALL_WORDS, RULE_BAD_FORM_MARKER]
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
    if gate == "vesum_verified":
        missing = report.get("missing")
        if isinstance(missing, list):
            return "missing=" + ", ".join(str(item) for item in missing[:5])
        if report.get("error"):
            return str(report["error"])
    if gate == "russianisms_strict":
        findings = report.get("critical_findings")
        if isinstance(findings, list) and findings:
            first = findings[0]
            if isinstance(first, Mapping):
                return str(
                    first.get("text")
                    or first.get("match")
                    or first.get("pattern")
                    or first.get("note")
                    or first
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
        section = (
            section_match.group("section").strip()
            if section_match
            else _reasoning_section_from_body(body)
        )
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
        blocks.append({
            "section": raw_section or _reasoning_section_from_body(body),
            "body": body,
        })
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
        sections = [
            str(block.get("section") or f"section_{index}")
            for index, block in enumerate(blocks, start=1)
        ]

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
                output[match.end():],
                re.MULTILINE,
            )
            end = match.end() + next_heading.start() if next_heading else len(output)
            body = output[match.end():end].strip()

    if not body:
        return {"gate_present": False, "gate_actions": [], "removed_count": 0}

    lower = body.casefold()
    actions: list[str] = []
    if "rescanned_words" in lower or ("rescan" in lower and any(token in lower for token in ("word", "vocab", "vesum"))):
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
_TOOL_CITATION_RE = re.compile(
    r"`?(?P<name>(?:mcp__sources__|search_|verify_|check_|query_|translate_)\w+)`?"
)


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
    return _normalize_tool_citation_name(
        mapped.get("tool") or mapped.get("tool_name") or mapped.get("name")
    )


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
            cited.update(
                _normalize_tool_citation_name(citation)
                for citation in _TOOL_CITATION_RE.findall(searchable)
            )
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
            "failed_words": [
                _clean_telemetry_text(word, 80)
                for word in failed_words[:TELEMETRY_MAX_FAILED_WORDS]
            ],
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
        "failed_words": [
            _clean_telemetry_text(word, 80)
            for word in failed_words[:TELEMETRY_MAX_FAILED_WORDS]
        ],
    }


def _summarize_generic_tool_result(result: Any) -> dict[str, Any]:
    if isinstance(result, Mapping):
        summary: dict[str, Any] = {}
        for key in ("verified", "failed", "items_checked", "items_failed"):
            if isinstance(result.get(key), int | float):
                summary[key] = int(result[key])
        flags = result.get("flags_raised")
        if isinstance(flags, list):
            summary["flags_raised"] = [
                _clean_telemetry_text(flag, 120)
                for flag in flags[:TELEMETRY_MAX_FAILED_WORDS]
            ]
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
            if (
                isinstance(item, Mapping)
                and item.get("type") == "text"
                and isinstance(item.get("text"), str)
            ):
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
        tool = _normalize_tool_name(
            call.get("tool") or call.get("tool_name") or call.get("name")
        )
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
    theatre_violations = (
        [] if telemetry_unavailable else detect_tool_theatre(output, list(tool_calls or []))
    )
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
        f"{record.failure_class.value}"
        + (f":{record.sub_class}" if record.sub_class else "")
        for record in terminal_failures
    )
    raise LinearPipelineError(
        f"WRITER_RUNTIME_GATE_FAILED: writer={writer!r} module={module!r} "
        f"failures=[{classes}]"
    )


def writer_context(
    plan: Mapping[str, Any],
    plan_content: str,
    knowledge_packet: str,
    wiki_manifest: str | Mapping[str, Any] | None = None,
    *,
    implementation_map: Mapping[str, Any] | None = None,
    writer: str | None = None,
) -> dict[str, str]:
    level = str(plan["level"])
    sequence = int(plan["sequence"])
    learner_state = build_learner_state(level.lower(), sequence)
    activity_config = _activity_config(level, sequence, str(plan["slug"]))
    if wiki_manifest is None:
        wiki_manifest_text = build_wiki_manifest(level=level.lower(), slug=str(plan["slug"]), plan=plan)
    elif isinstance(wiki_manifest, str):
        wiki_manifest_text = _render_prompt_wiki_manifest(wiki_manifest)
    else:
        wiki_manifest_text = _render_prompt_wiki_manifest(wiki_manifest)
    if implementation_map is None:
        impl_map_contract = "(no implementation_map provided to render_writer_prompt — gate will fail)"
    else:
        from scripts.build.phases.implementation_map import render_for_writer_prompt

        impl_map_contract = render_for_writer_prompt(dict(implementation_map))
    return {
        "LEVEL": level,
        "MODULE_NUM": str(sequence),
        "MODULE_SLUG": str(plan["slug"]),
        "TOPIC_TITLE": str(plan["title"]),
        "PHASE": str(plan.get("phase", "")),
        "WORD_TARGET": str(plan["word_target"]),
        "WRITER_SPECIFIC_DIRECTIVES": _writer_specific_directives(writer),
        "PLAN_CONTENT": plan_content,
        "KNOWLEDGE_PACKET": knowledge_packet,
        "WIKI_MANIFEST": wiki_manifest_text,
        "IMPLEMENTATION_MAP_CONTRACT": impl_map_contract,
        "LEARNER_STATE": format_learner_state(learner_state),
        "IMMERSION_RULE": get_immersion_rule(level.lower(), sequence, learner_state=learner_state),
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


def _runtime_tool_config(
    agent_label: str,
    *,
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
            "codex-tools / claude-tools / gemini-tools / grok-tools / "
            "deepseek-tools / qwen-tools / agy-tools."
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
        tool_config["agent"] = "curriculum-writer"
    assert tool_config.get("output_format") == "stream-json", (
        "tool-call writers must keep output_format='stream-json'; "
        f"got {tool_config.get('output_format')!r}"
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
        raise LinearPipelineError(
            f"Unknown writer {writer!r}; expected one of {WRITER_CHOICES}"
        )
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
        tool_config=_runtime_tool_config(writer, event_sink=event_sink),
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
                inner_stripped = inner_stripped[: -open_run].rstrip()
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


def run_wiki_coverage_gate(
    *,
    manifest: Mapping[str, Any] | str | Path,
    writer_output: str,
    module_dir: Path,
    level: str | None = None,
) -> dict[str, Any]:
    from scripts.audit.wiki_coverage_gate import check_wiki_coverage_paths

    result = check_wiki_coverage_paths(
        manifest=manifest,
        implementation_map=writer_output,
        module_dir=module_dir,
        level=level,
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
) -> dict[str, str]:
    """Build context for one independent per-dimension LLM QG prompt."""
    if dim not in QG_DIMS:
        raise LinearPipelineError(f"Unknown LLM QG dimension: {dim}")
    level = str(plan["level"])
    sequence = int(plan["sequence"])
    learner_state = build_learner_state(level.lower(), sequence)
    return {
        "LEVEL": level,
        "MODULE_NUM": str(sequence),
        "MODULE_SLUG": str(plan["slug"]),
        "WORD_TARGET": str(plan["word_target"]),
        "LEARNER_STATE": format_learner_state(learner_state),
        "IMMERSION_RULE": get_immersion_rule(
            level.lower(), sequence, learner_state=learner_state
        ),
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
        wiki_manifest
        if isinstance(wiki_manifest, str)
        else json.dumps(wiki_manifest, ensure_ascii=False, indent=2)
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
        PROJECT_ROOT
        / "scripts"
        / "build"
        / "phases"
        / "linear-correction-wiki-coverage.md",
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
        "CURRENT_ARTIFACT_STATE": str(
            fix_proposal.get("current_artifact_state") or ""
        ),
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
        PROJECT_ROOT
        / "scripts"
        / "build"
        / "phases"
        / "linear-correction-wiki-coverage-narrow.md",
        wiki_coverage_narrow_correction_context(
            plan=plan,
            fix_proposal=fix_proposal,
            artifact_text=artifact_text,
            previous_batched_attempts=previous_batched_attempts,
        ),
    )


def _quote_items_from_text(text: str) -> list[str]:
    quotes: list[str] = []
    quote_re = re.compile(
        r'"(?P<double>[^"\n]{1,500})"|“(?P<curly>[^”\n]{1,500})”|«(?P<guillemets>[^»\n]{1,500})»'
    )
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
            _clean_telemetry_text(item, TELEMETRY_MAX_QUOTE_CHARS)
            for item in raw_quotes
            if str(item).strip()
        )

    evidence = payload.get("evidence")
    if isinstance(evidence, list):
        quotes.extend(
            _clean_telemetry_text(item, TELEMETRY_MAX_QUOTE_CHARS)
            for item in evidence
            if str(item).strip()
        )
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
    return [
        _clean_telemetry_text(flag, 120)
        for flag in flags[:TELEMETRY_MAX_FAILED_WORDS]
    ]


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
        tool = _normalize_tool_name(
            call.get("tool") or call.get("tool_name") or call.get("name")
        )
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
        raise LinearPipelineError(
            f"Unknown reviewer {reviewer!r}; expected one of {REVIEWER_CHOICES}"
        )
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
        tool_config=_runtime_tool_config(reviewer, event_sink=event_sink),
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


def render_writer_correction_prompt(
    *,
    gate: str,
    gate_report: Mapping[str, Any],
    module_text: str,
    writer: str = "claude-tools",
) -> str:
    """Render the ADR-008 patch-bounded writer correction prompt."""
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
        },
    )


def render_reviewer_correction_prompt(
    *,
    gate: str,
    gate_report: Mapping[str, Any],
    module_text: str,
    candidates: tuple[CorrectionCandidate, ...] = (),
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
        candidate_section = yaml.safe_dump(
            candidate_rows, allow_unicode=True, sort_keys=False
        ).strip()
        reviewer_role = (
            "Pipeline-proposed candidates are provided below. SELECT from these "
            "candidates; do not invent replacements."
        )
    else:
        candidate_section = "[]"
        reviewer_role = (
            "Emit local <fixes> entries only. Do not rewrite sections."
        )
    diagnostic = yaml.safe_dump(
        {
            "gate": gate,
            "diagnostic": dict(gate_report),
        },
        allow_unicode=True,
        sort_keys=False,
    ).strip()
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
            "## Current module.md",
            "```markdown",
            module_text,
            "```",
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
            raise LinearPipelineError(
                "Wiki coverage review verdict must be PASS, KEYWORD_STUFFING, PARTIAL, or FAIL"
            )
        if not str(item.get("obligation_id") or "").strip():
            raise LinearPipelineError("Wiki coverage review verdict missing obligation_id")
        evidence = str(item.get("evidence") or "").strip()
        if not evidence:
            raise LinearPipelineError("Wiki coverage review verdict missing evidence")
        if len(evidence) < 8 or not any(
            marker in evidence for marker in WIKI_COVERAGE_EVIDENCE_QUOTE_MARKERS
        ):
            raise LinearPipelineError(
                "Wiki coverage review evidence must be a quoted excerpt of ≥8 chars"
            )
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
        raise LinearPipelineError(
            "Wiki coverage review overall_verdict must be FAIL when any obligation verdict fails"
        )
    return {**payload, "verdicts": normalized_verdicts, "overall_verdict": overall}


_LLM_QG_QUOTE_MARKERS = ('"', "“", "”", "«", "»")


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
    if (
        isinstance(evidence, str)
        and evidence.strip()
        and any(q in evidence for q in _LLM_QG_QUOTE_MARKERS)
    ):
        return True

    quotes = entry.get("evidence_quotes")
    if isinstance(quotes, list) and quotes:
        valid = [
            q for q in quotes
            if isinstance(q, str) and len(q.strip()) >= 8
        ]
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
        evidence_quotes = entry.get("evidence_quotes")
        if (not isinstance(evidence, str) or not evidence.strip()) and not (
            isinstance(evidence_quotes, list) and evidence_quotes
        ):
            raise LinearPipelineError(f"LLM QG entry for {dim} missing evidence")
        if not _evidence_passes_quote_contract(entry):
            raise LinearPipelineError(
                f"LLM QG evidence for {dim} must include a quoted excerpt"
            )
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
    scores = {
        dim: float(report[dim]["score"])
        for dim in QG_DIMS
        if isinstance(report.get(dim), Mapping)
    }
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
    reviewer: str | None = None,
    module: str | None = None,
    writer_under_review: str | None = None,
    audit_calls_total: int = 0,
    flags_raised_total: int = 0,
    event_sink: Callable[..., None] | None = None,
) -> dict[str, Any]:
    validate_llm_review_report(report)
    scores = {dim: float(report[dim]["score"]) for dim in QG_DIMS}
    verdict = aggregate_review(scores, level_code)
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


def run_python_qg_with_corrections(
    module_dir: Path,
    plan_path: Path,
    *,
    verify_words_fn: Callable[[list[str]], dict[str, list[dict[str, Any]]]] | None = None,
    qg_runner: Callable[[], dict[str, Any]] | None = None,
    writer_corrector: Callable[[CorrectionContext], str | Mapping[str, str] | None]
    | None = None,
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
    vesum_missing_exclusions: set[str] = set()
    correction_round = 0

    def _run_qg() -> dict[str, Any]:
        if qg_runner is not None:
            return qg_runner()
        return run_python_qg(
            module_dir,
            plan_path,
            verify_words_fn=verify_words_fn,
            ignored_vesum_missing_surfaces=vesum_missing_exclusions,
            event_sink=event_sink,
        )

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

        if failed_gate == "vesum_verified":
            vesum_missing_exclusions.update(unmatched_anchors)
        report = _run_qg()
        vesum_missing_exclusions.clear()
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
        if regressions:
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
        if str(
            proposal.get("failure_reason")
            or proposal.get("reason")
            or proposal.get("status")
            or ""
        )
        == "implementation_map_missing"
    ]
    if not missing_impl_ids:
        obligations = result.get("obligations") or []
        if isinstance(obligations, Sequence) and not isinstance(obligations, (str, bytes)):
            missing_impl_ids = [
                str(item.get("obligation_id") or item.get("id") or "")
                for item in obligations
                if isinstance(item, Mapping)
                and str(item.get("reason") or "") == "implementation_map_missing"
            ]
    if not missing_impl_ids:
        return
    _emit_writer_rule_fired(
        event_sink,
        rule_id=RULE_IMPL_MAP_COMPLETE,
        level=(str(level).lower() if level else None),
        slug=_wiki_manifest_slug(manifest, module_dir),
        gate="implementation_map_missing",
        evidence="missing_obligation_ids="
        + ", ".join(sorted(set(missing_impl_ids))[:10]),
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
        tool_config=_runtime_tool_config("codex-tools", event_sink=event_sink),
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
    accepted_fixes, rejected_fixes = _validate_reviewer_fix_shapes(fixes)
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
            if anchor in updated:
                updated = updated.replace(anchor, anchor + str(fix["text"]), 1)
                count += 1
            continue
        find = str(fix.get("find") or "")
        if find and find in updated:
            updated = updated.replace(find, str(fix.get("replace") or ""), 1)
            count += 1
    return count


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
    if not isinstance(parsed, list):
        raise LinearPipelineError(f"{artifact} must remain a bare YAML list")
    for index, item in enumerate(parsed, start=1):
        if not isinstance(item, dict):
            raise LinearPipelineError(
                f"{artifact} entries must remain mappings; item {index} is "
                f"{type(item).__name__}"
            )
    try:
        redumped = yaml.safe_dump(parsed, allow_unicode=True, sort_keys=False)
        reparsed = yaml.safe_load(redumped)
    except yaml.YAMLError as exc:
        raise LinearPipelineError(f"{artifact} failed YAML round-trip: {exc}") from exc
    if parsed != reparsed:
        raise LinearPipelineError(
            f"{artifact} does not round-trip cleanly; likely scalar/mapping "
            "ambiguity or non-portable scalar value"
        )
    for index, item in enumerate(parsed, start=1):
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
                raise LinearPipelineError(
                    f"{artifact} item {index} field items must remain a list"
                )
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
    return [
        item
        for item in obligations
        if isinstance(item, Mapping) and item.get("status") == "FAIL"
    ]


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


def _apply_python_qg_correction(
    gate: str,
    qg_report: Mapping[str, Any],
    *,
    module_dir: Path,
    plan_path: Path,
    writer_corrector: Callable[[CorrectionContext], str | Mapping[str, str] | None]
    | None,
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
        return True, frozenset(), {
            "kind": "pipeline_insert",
            "gate": gate,
            "gate_report": dict(gate_report),
        }
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
    writer_corrector: Callable[[CorrectionContext], str | Mapping[str, str] | None]
    | None,
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
    prompt = render_reviewer_correction_prompt(
        gate=gate,
        gate_report=gate_report,
        module_text=module_text,
        candidates=candidates,
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
            tool_config=_runtime_tool_config("codex-tools"),
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
    result = _apply_reviewer_fixes(
        module_text,
        accepted_fixes,
        gate=gate,
        module_dir=module_dir,
        plan_path=plan_path,
    )
    if accepted_fixes:
        module_path.write_text(result.text, encoding="utf-8")
        try:
            _validate_wiki_coverage_artifact_text(module_path.name, result.text)
        except LinearPipelineError as exc:
            module_path.write_text(module_text, encoding="utf-8")
            emit_event(
                "reviewer_correction_yaml_invalid",
                **_correction_event_fields(
                    gate=gate,
                    module_dir=module_dir,
                    plan_path=plan_path,
                ),
                artifact=module_path.name,
                error_preview=str(exc)[:800],
            )
    return result.unmatched_anchors, {
        "kind": "reviewer",
        "gate": gate,
        "prompt": prompt,
        "response": response,
        "fixes": fixes,
        "accepted_fixes": accepted_fixes,
        "rejected_fixes": rejected_fixes,
        "unmatched_anchors": sorted(result.unmatched_anchors),
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
            fixes.append({
                "insert_after": str(item["insert_after"]),
                "text": str(item["text"]),
            })
        elif "find" in item and "replace" in item:
            fixes.append({
                "find": str(item["find"]),
                "replace": str(item["replace"]),
            })
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
            fixes.append({
                "find": "".join(find_node.itertext()),
                "replace": "".join(replace_node.itertext()),
            })
            continue
        insert_after_node = node.find("insert_after")
        text_node = node.find("text")
        if insert_after_node is not None and text_node is not None:
            fixes.append({
                "insert_after": "".join(insert_after_node.itertext()),
                "text": "".join(text_node.itertext()),
            })
    return fixes


def _apply_reviewer_fixes(
    text: str,
    fixes: list[dict[str, str]],
    *,
    gate: str | None = None,
    module_dir: Path | None = None,
    plan_path: Path | None = None,
) -> ReviewerFixApplyResult:
    updated = text
    unmatched_anchors: set[str] = set()
    for fix in fixes:
        if "insert_after" in fix and "text" in fix:
            anchor = fix["insert_after"]
            if anchor in updated:
                updated = updated.replace(anchor, anchor + fix["text"], 1)
            else:
                unmatched_anchors.add(anchor)
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
                    text_preview=_correction_preview(fix["text"]),
                )
            continue
        find = fix.get("find")
        replace = fix.get("replace")
        if find and replace is not None and find in updated:
            updated = updated.replace(find, replace, 1)
        elif find:
            unmatched_anchors.add(find)
            emit_event(
                "reviewer_fixes_anchor_unmatched",
                **_correction_event_fields(
                    gate=gate or "",
                    module_dir=module_dir,
                    plan_path=plan_path,
                )
                if module_dir is not None and plan_path is not None
                else {"gate": gate},
                anchor_preview=_correction_preview(find),
                text_preview=_correction_preview(replace),
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
    regressions = []
    for gate in PYTHON_QG_GATE_ORDER:
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
                str(item.get("text"))
                for item in detections
                if isinstance(item, Mapping) and item.get("text")
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
                    candidates.append(
                        CorrectionCandidate(original, replacement, source, gate)
                    )
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
    gate_observer: Callable[[str], None] | None = None,
    ignored_vesum_missing_surfaces: Collection[str] = (),
    event_sink: Callable[..., None] | None = None,
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

    record("word_count", _word_count_gate(module_text, int(plan["word_target"])))
    record("plan_sections", _section_gate(module_text, plan))
    record("formatting_standards", _formatting_standards_gate(module_text))
    record(
        "vesum_verified",
        _vesum_gate(
            module_text=module_text,
            activities=activities,
            vocabulary=vocabulary,
            resources=resources,
            verify_words_fn=verify_words_fn,
            ignored_missing_surfaces=ignored_vesum_missing_surfaces,
        ),
    )
    record("citations_resolve", _citation_gate(resources, plan))
    record("textbook_grounding", _textbook_grounding_gate(module_text, plan, module_dir))
    record(
        "resources_search_attempted",
        _resources_search_attempted_gate(_load_writer_tool_calls(module_dir)),
    )
    record("immersion_advisory", _advisory_immersion_pct(module_text, plan))
    record("l2_exposure_floor", _l2_exposure_floor_gate(module_text, plan))
    record(
        "long_uk_ceiling",
        _long_uk_ceiling_gate(
            module_text,
            plan,
            grounding_evidence=gates.get("textbook_grounding"),
        ),
    )
    record("component_density", _component_density_gate(module_text, plan))
    record("inject_activity_ids", _inject_activity_gate(module_text, activities))
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
    record("russianisms_strict", _russianisms_strict_gate(text_for_quality))
    record("engagement_floor", _engagement_floor_gate(module_text, plan))
    record("component_props", _component_prop_gate(activities))
    for gate_name, gate_report in _quality_fields(text_for_quality).items():
        record(gate_name, gate_report)
    gates["previously_passed_regression"] = {"passed": True, "regressions": []}
    gates["mdx_render"] = {"passed": None, "message": "Run after publish stage"}
    gates["passed"] = all(
        gate.get("passed") is True
        for key, gate in gates.items()
        if isinstance(gate, dict) and key != "mdx_render"
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
    output_path.write_text(mdx, encoding="utf-8")  # codeql[py/clear-text-storage-sensitive-data] - .mdx curriculum content, never sensitive data
    return mdx


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
        if artifact == "resources.yaml":
            role = str(item.get("role") or "").strip()
            if role not in RESOURCE_ROLES:
                raise LinearPipelineError(
                    f"{artifact} schema validation failed: item {index} "
                    f"has invalid role {role!r}; allowed: {sorted(RESOURCE_ROLES)}"
                )
            if role != "textbook" and not str(item.get("url") or "").strip():
                raise LinearPipelineError(
                    f"{artifact} schema validation failed: item {index} "
                    f"role {role!r} requires url"
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
    "highlight-morphemes": _activity("items", "text"),
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
        raise LinearPipelineError(
            "LLM QG response must be a JSON/YAML mapping"
        ) from last_error
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
                "covers": section.get("points", []),
            }
            for section in plan.get("content_outline", [])
        ],
        "activity_hints": plan.get("activity_hints", []),
        "vocabulary_required": _required_vocabulary_for_contract(plan),
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


def _activity_schema_gate(activities: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate strict item-level authoring schemas before content gates run."""
    item_fields_by_type = _activity_item_schema_whitelist()
    violations: list[dict[str, Any]] = []
    checked = 0

    for activity_index, activity in enumerate(activities, start=1):
        if not isinstance(activity, Mapping):
            continue
        activity_type = str(activity.get("type") or "")
        allowed_fields = item_fields_by_type.get(activity_type)
        if allowed_fields is None:
            continue
        aliases = _ACTIVITY_ITEM_FORBIDDEN_ALIASES.get(activity_type, {})
        required_fields = _ACTIVITY_ITEM_REQUIRED_FIELDS.get(activity_type, frozenset())
        activity_id = str(activity.get("id") or f"#{activity_index}")
        items = activity.get("items", [])
        if not isinstance(items, list):
            continue

        for item_index, item in enumerate(items, start=1):
            if not isinstance(item, Mapping):
                continue
            checked += 1
            item_fields = {str(field) for field in item}
            aliased_required = {
                expected
                for field in item_fields
                if (expected := aliases.get(field)) in required_fields
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
        message = (
            f"{activity_type} items must include '{expected_field}:' for {purpose}"
        )
    elif expected_field is not None:
        purpose = _ACTIVITY_ITEM_FIELD_PURPOSES.get(expected_field, "this value")
        message = (
            f"{activity_type} items must use '{expected_field}:' for {purpose}, "
            f"not '{offending_field}:'"
        )
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


def _format_activity_schema_diagnostic(violations: list[dict[str, Any]]) -> str:
    lines = [
        f"ACTIVITY_SCHEMA_GATE FAILED: {len(violations)} violations",
        "",
    ]
    for violation in violations[:10]:
        activity_id = violation["activity_id"]
        activity_index = violation["activity_index"]
        item_index = violation["item_index"]
        lines.append(
            f"  activity #{activity_index} '{activity_id}' (item {item_index}):"
        )
        offending = violation.get("offending_field")
        expected = violation.get("expected_field")
        if offending is None:
            lines.append(f"    missing required field '{expected}:'")
        elif expected is None:
            lines.append(f"    forbidden field '{offending}'")
        else:
            purpose = _ACTIVITY_ITEM_FIELD_PURPOSES.get(str(expected), "this value")
            lines.append(
                f"    forbidden field '{offending}' - use '{expected}:' for {purpose}"
            )
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


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


# Word-target tolerance: 8% lower band. User direction 2026-05-23
# (handoff docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md
# decision row B): word targets stay as MINIMUMS for the writer prompt
# guidance, but the gate tolerates ±8% below target to avoid 0.25%-short
# rejections like deepseek-pro 1197/1200. Empirically the 8% band still
# rejects gemini-tools 1031/1200 (14% short).
_WORD_COUNT_TOLERANCE_BELOW = 0.08


def _word_count_gate(text: str, target: int) -> dict[str, Any]:
    count = _word_count(_strip_comments(text))
    min_with_tolerance = int(target * (1 - _WORD_COUNT_TOLERANCE_BELOW))
    return {
        "passed": count >= min_with_tolerance,
        "count": count,
        "target": target,
        "min_with_tolerance": min_with_tolerance,
        "tolerance_below_pct": _WORD_COUNT_TOLERANCE_BELOW * 100,
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
        budgets.append({
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
        })
    return {
        # Gate-level `passed` reflects ONLY missing headings: every contracted
        # section must EXIST as a level-2 heading in the module. Per-section
        # word budgets are advisory (see comment in budgets construction
        # above). A future stricter mode could surface per-section under-min
        # as a separate `plan_sections_balance` advisory gate, but the build
        # halt no longer fires on it.
        "passed": not missing,
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
    ignored_missing_surfaces: Collection[str] = (),
) -> dict[str, Any]:
    """Verify Ukrainian words against VESUM, walking artifacts structurally.

    Four classes of false positives are deliberately excluded:

    1. **Phonetic transcriptions and inline code** — `[с':а]`, `[ц':а]`, and
       backticked fragments like `` `вмиваєс':а` `` are metalinguistic notation
       (parts of words, IPA-ish symbols), not VESUM lemmas.
    2. **Intentional misspellings in `error-correction` activities** —
       `error:`, `errorWord:`, and `error_word:` fields contain the typo the
       student must fix (e.g. `прокидаєштся`). Verifying them would always fail.
    3. **Wrong multiple-choice options** — `options: [{text, correct}]` values
       with `correct: false` are author-labeled distractors. They may include
       intentionally non-standard forms that test overgeneralization.
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
        emit_negative_example_events=True,
    )

    # Pair each surface form with its normalized lowercase lookup key once, so
    # subsequent whitelist + missing computations don't re-normalize repeatedly.
    surface_pairs = sorted(
        _iter_vesum_lookup_surface_pairs(text, min_word_length=VESUM_MIN_WORD_LENGTH)
    )
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
            resolved_lc = {
                surface.lower()
                for surface, matches in original_case_verified.items()
                if matches
            }
            missing_lc -= resolved_lc
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
            for compound in hyphenated_missing:
                parts = [part for part in compound.split("-") if part]
                if len(parts) < 2:
                    continue
                eligible_parts = [
                    part for part in parts if len(part) >= VESUM_MIN_WORD_LENGTH
                ]
                constituent_lookups.update(eligible_parts)
                constituent_map[compound] = eligible_parts
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
            resolved_compounds: set[str] = set()
            for compound, parts in constituent_map.items():
                # All eligible parts must verify. If there are zero
                # eligible parts (every constituent below threshold),
                # accept conservatively — the compound is a string of
                # very short tokens we wouldn't gate individually.
                if all(constituent_verified.get(part) for part in parts):
                    resolved_compounds.add(compound)
            missing_lc -= resolved_compounds
    missing = sorted(
        {surface for surface, lower, _original in unchecked_pairs if lower in missing_lc}
    )
    ignored_missing_lc = _vesum_missing_exclusion_keys(
        ignored_missing_surfaces,
        min_word_length=VESUM_MIN_WORD_LENGTH,
    )
    if ignored_missing_lc:
        missing = [
            surface
            for surface in missing
            if _normalize_for_vesum(surface).lower() not in ignored_missing_lc
        ]
    return {
        "passed": not missing,
        "checked": len(unchecked_pairs),
        "whitelisted": len(surface_pairs) - len(unchecked_pairs),
        "missing": missing[:100],
        "missing_count": len(missing),
    }


def _normalize_for_vesum(lemma: str) -> str:
    """Strip stress marks and Markdown wrappers before VESUM lookup.

    Writer output may contain combining accents such as U+0301 and local
    emphasis like `вмива́ю**ся**`. The QG report still keeps the original
    surface form; this helper is only for the VESUM lookup key.
    """
    text = unicodedata.normalize("NFD", lemma)
    text = "".join(char for char in text if char not in _VESUM_STRESS_MARKS)
    text = unicodedata.normalize("NFC", text)
    previous = None
    while previous != text:
        previous = text
        # Strip emphasis wrappers (bold/italic/code/italic-underscore).
        # Hyphens INSIDE emphasis are conditionally stripped: pedagogical
        # morpheme breaks like `прокида**ю-ся**` and `**-ться**` (where
        # a hyphen splits a short morpheme fragment) collapse to the
        # canonical VESUM lemma; real compound words like `**темно-синій**`
        # (both halves are full-length lexemes) preserve their hyphen.
        # The heuristic: strip the hyphen only if either side is ≤3 chars
        # (morpheme-fragment width). 3-char threshold captures all observed
        # Ukrainian reflexive/aspectual suffixes (`ся/сь/ть/єть/єте/ємо/...`)
        # while keeping every Ukrainian compound noun/adjective intact
        # (compound halves are ≥4 chars in practice: `темно`, `синій`,
        # `жовто`, `гарячий`, …).
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
    return text.strip()


def _strip_morpheme_hyphen(emphasis_inner: str, *, fragment_max_chars: int = 3) -> str:
    """Collapse a morpheme-break hyphen INSIDE markdown emphasis, but only
    when at least one side of the hyphen is short enough to be a morpheme
    fragment (≤``fragment_max_chars`` chars by default).

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
    if len(left) <= fragment_max_chars or len(right) <= fragment_max_chars:
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


def _iter_vesum_lookup_surface_pairs(
    text: str,
    *,
    min_word_length: int,
) -> set[tuple[str, str, str]]:
    normalized_words = {
        word
        for word in _iter_vesum_word_surfaces(_normalize_for_vesum(text))
        if len(word) >= min_word_length
    }
    decorated_by_lower: dict[str, set[tuple[str, str]]] = {}
    for match in _VESUM_DECORATED_WORD_RE.finditer(text):
        raw = match.group(0).strip("-'ʼ")
        if not raw or "__" in raw or not _has_vesum_lookup_decoration(raw):
            continue
        if _looks_like_stem_fragment(text, match.start(), match.end()):
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
    for match in _UK_WORD_RE.finditer(text):
        word = match.group(0).strip("-'ʼ")
        if word:
            words.append(word)
    return words


def _iter_vesum_word_surfaces(text: str) -> list[str]:
    """Extract Ukrainian surface forms that are meaningful VESUM candidates."""
    words: list[str] = []
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
        word = raw.strip("-'ʼ")
        if not word:
            continue
        if word.lower() in _STANDALONE_POSTFIX_FRAGMENTS:
            continue
        word = _collapse_syllable_break(word)
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
    return (start > 0 and text[start - 1] == "_") or (
        end < len(text) and text[end] == "_"
    )


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
    return raw.endswith(("'", "ʼ")) and not (
        start > 0 and text[start - 1] in {"'", "ʼ"}
    )


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
    - `not "форма"` / `not «форма»` — prose-quoted warning examples where the
      quoted form is explicitly marked as wrong.

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
                findings.extend(
                    _negative_example_findings(activity_id, item_idx, texts)
                )
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
                    "hint": (
                        "Wrap the negative example as "
                        f"<!-- bad -->{form}<!-- /bad -->."
                    ),
                }
            )
    return findings


def _build_vesum_text(
    module_text: str,
    activities: list[dict[str, Any]],
    vocabulary: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    *,
    emit_negative_example_events: bool = False,
) -> str:
    """Compose the text blob that VESUM verifies, with structural exclusions."""
    parts = [_strip_metalinguistic(module_text)]
    for activity in activities:
        parts.append(
            _strip_metalinguistic(
                _activity_vesum_text(
                    activity,
                    emit_negative_example_events=emit_negative_example_events,
                )
            )
        )
    for entry in vocabulary:
        if isinstance(entry, dict):
            parts.append(_strip_metalinguistic(str(entry.get("lemma", ""))))
            usage = _strip_usage_parentheticals(str(entry.get("usage", "")))
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
) -> str:
    """Walk an activity's string values, excluding intentional-error fields.

    For `error-correction` activities, fields like `error:`, `errorWord:`,
    and `sentence:` hold the typo the student must fix; verifying them against
    VESUM would always fail. The skip is at the dict (subtree) level so even a
    future nested shape like `error: { text: "...", note: "..." }` would be
    entirely excluded.

    For multiple-choice-style `options: [{text, correct}]` lists, `text` on
    options with falsy `correct` is an intentional wrong answer. Skip only that
    option's text leaf so correct options and surrounding prompts are still
    verified.

    For fill-in activities, bare-list `options:` values are suffix fragments,
    not VESUM lemmas. For quiz-like item dicts with `options:` plus `answer:`,
    only the option equal to the answer is verified; sibling distractors can be
    fabricated wrong forms.

    For true-false activities, false statements are intentional wrong claims
    and may contain fabricated Ukrainian forms. Only true statements are
    verified; missing answers fail soft by skipping the statement. True
    statements also get a narrow safety net for sentence-final negative examples
    like ``X, а не дивюся.`` where the tail is named as wrong teaching content.
    """
    activity_type = activity.get("type")
    activity_id = str(activity.get("id") or "")
    skip_subtree = (
        _ERROR_CORRECTION_INTENTIONAL_FIELDS
        if activity_type == _ERROR_CORRECTION_TYPE
        else frozenset()
    )

    out: list[str] = []

    def answer_values(*answers: Any) -> set[str]:
        values: set[str] = set()
        for answer in answers:
            if isinstance(answer, str):
                values.add(answer)
            elif isinstance(answer, list):
                values.update(item for item in answer if isinstance(item, str))
        return values

    def walk_answer_options(options: Any, answers: set[str]) -> None:
        if not answers:
            return
        if isinstance(options, list):
            for option in options:
                if isinstance(option, str):
                    if option in answers:
                        walk(option, "options")
                elif isinstance(option, dict):
                    text = option.get("text")
                    if isinstance(text, str) and text in answers:
                        walk(option, "options", in_options_list=True)
        elif isinstance(options, str) and options in answers:
            walk(options, "options")

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
            wrong_option = (
                in_options_list
                and isinstance(node.get("text"), str)
                and "correct" in node
                and not node.get("correct", False)
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
                if key == "options" and (
                    "answer" in node or "correctAnswer" in node
                ):
                    walk_answer_options(
                        child,
                        answer_values(node.get("answer"), node.get("correctAnswer")),
                    )
                    continue
                if activity_type == "true-false" and key == "statement":
                    walk_truefalse_statement(
                        child,
                        node.get("answer"),
                        item_idx=item_idx,
                    )
                    continue
                if wrong_option and key == "text":
                    continue
                walk(child, key, item_idx=item_idx)
        elif isinstance(node, list):
            for index, item in enumerate(node):
                child_item_idx = (
                    index
                    if activity_type == "true-false" and parent_key == "items"
                    else item_idx
                )
                walk(
                    item,
                    parent_key,
                    in_options_list=parent_key == "options",
                    item_idx=child_item_idx,
                )
        elif isinstance(node, str):
            out.append(node)

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
        if re.search(r"\[![A-Za-z][\w-]*\]", line) and not re.match(
            r"^\s*>\s*\[![A-Za-z][\w-]*\]", line
        ):
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


def _normalize_citation_ref(value: Any) -> str:
    return normalize_citation_ref(value)


def _normalize_citation_match_text(value: Any) -> str:
    normalized = _normalize_citation_ref(value).casefold()
    return re.sub(r"[^\wа-яіїєґА-ЯІЇЄҐ]+", "", normalized)


def _citation_ref_text_contains(reference_title: str, text: str) -> bool:
    normalized_ref = _normalize_citation_match_text(reference_title)
    normalized_text = _normalize_citation_match_text(text)
    return bool(normalized_ref and normalized_ref in normalized_text)


def _citation_gate(resources: list[dict[str, Any]], plan: Mapping[str, Any]) -> dict[str, Any]:
    plan_reference_titles = extract_plan_reference_titles(plan)
    plan_titles = {_normalize_citation_ref(title) for title in plan_reference_titles}
    plan_keys = {
        key
        for title in plan_reference_titles
        if (key := extract_citation_key(title)) is not None
    }
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
            and (
                source_key is None
                or not any(citation_keys_match(source_key, plan_key) for plan_key in plan_keys)
            )
            and resource.get("packet_chunk_id") is None
        ):
            unknown.append(source_ref)
    return {"passed": not unknown, "unknown": unknown}


def _extract_blockquote_records(text: str) -> list[dict[str, str]]:
    quotes: list[dict[str, str]] = []
    current: list[str] = []
    current_section = ""
    quote_section = ""
    pending_attribution_index: int | None = None

    def flush_quote() -> None:
        nonlocal current, quote_section, pending_attribution_index
        if not current:
            return
        quotes.append(
            {
                "quote": "\n".join(current).strip(),
                "section_title": quote_section,
                "attribution": "",
            }
        )
        current = []
        quote_section = ""
        pending_attribution_index = len(quotes) - 1

    for line in text.splitlines():
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
        match = re.match(r"^\s*>\s?(?P<body>.*)$", line)
        if match:
            if not current:
                quote_section = current_section
            current.append(match.group("body"))
            continue
        if current:
            flush_quote()
        if pending_attribution_index is not None:
            if not line.strip():
                continue
            attribution = _extract_textbook_attribution(line)
            if attribution:
                quotes[pending_attribution_index]["attribution"] = attribution
                pending_attribution_index = None
                continue
            pending_attribution_index = None
    if current:
        flush_quote()
    return [record for record in quotes if record["quote"]]


def _extract_blockquotes(text: str) -> list[str]:
    return [record["quote"] for record in _extract_blockquote_records(text)]


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
        window = " ".join(
            quote_tokens[start : start + TEXTBOOK_GROUNDING_MIN_WORDS]
        )
        if window in result_blob:
            return True
    return False


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
    return " ".join(
        match.group("body") for match in _PLAN_REASONING_ELEMENT_RE.finditer(module_text)
    ) + " " + " ".join(
        match.group("body") for match in _PLAN_THINKING_ELEMENT_RE.finditer(module_text)
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


def _load_writer_tool_calls(module_dir: Path) -> list[dict[str, Any]]:
    candidates = [
        module_dir / "writer_tool_calls.json",
        module_dir / "writer_trace.json",
        module_dir / "writer_telemetry.jsonl",
    ]
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
                calls.extend(
                    dict(item) for item in raw_calls if isinstance(item, Mapping)
                )
    for path in sorted(module_dir.glob("*.write.jsonl")):
        calls.extend(_load_jsonl_tool_calls(path))
    return calls


def _resources_search_attempted_gate(
    writer_tool_calls: list[dict[str, Any]],
) -> dict[str, Any]:
    """HARD gate: writer must attempt at least one external-resource search."""
    attempted = [
        call
        for call in writer_tool_calls
        if _tool_name_from_call(call) in MULTIMEDIA_SEARCH_TOOLS
    ]
    search_tools_used = sorted({_tool_name_from_call(call) for call in attempted})
    return {
        "passed": bool(attempted),
        "severity": "HARD",
        "search_attempt_count": len(attempted),
        "search_tools_used": search_tools_used,
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
            title = (
                f"{author[:1].upper()}{author[1:]} "
                f"Grade {grade_match.group('grade')}, p.{page_match.group('page')}"
            )

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
    if isinstance(result, list):
        items: list[Mapping[str, Any]] = []
        tool_name = _tool_name_from_call(call)
        for item in result:
            if not isinstance(item, Mapping):
                continue
            if (
                tool_name == "search_text"
                and item.get("type") == "text"
                and isinstance(item.get("text"), str)
            ):
                parsed = _parse_mcp_search_text_markdown(item["text"])
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
        result.get("source_type")
        or result.get("type")
        or result.get("corpus")
        or result.get("source")
        or ""
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
    return any(
        _reference_matches_result(reference_title, result)
        for result in _result_items_from_call(call)
    )


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
                "corpus_missing": bool(ref.get("corpus_missing"))
                or title in missing_from_packet,
                "verbatim_required": ref.get("verbatim_required") is not False,
            }
        )
    return records


def _level_requires_references(level: str) -> bool:
    return level.casefold() in {"b1", "b2", "c1", "c2", "pro"}


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
    search_calls = [
        call
        for call in all_writer_calls
        if _tool_name_from_call(call) == "search_text"
    ]
    # Per writer_prompt §"Textbook quotes" Step B, writers retrieve the
    # plan-referenced chunk via ``get_chunk_context(chunk_id=...)`` after
    # ``search_text`` resolves the chunk_id. Both call families produce
    # textbook items the matcher needs to see — collecting only one half
    # (the historical state until 2026-05-20) makes the writer's
    # prompt-prescribed retrieval path invisible to the gate.
    chunk_context_calls = [
        call
        for call in all_writer_calls
        if _tool_name_from_call(call) == "get_chunk_context"
    ]
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
    missing_corpus = [
        record["title"] for record in reference_records if record["corpus_missing"]
    ]
    for ref in references:
        if ref in downgraded:
            continue
        ref_results = [
            result
            for call, result in textbook_results
            if _reference_matches_result(ref, result)
        ]
        for record in long_blockquote_records:
            quote = record["quote"]
            attribution = record.get("attribution", "")
            candidate_results = ref_results
            if not candidate_results and _citation_ref_text_contains(ref, attribution):
                candidate_results = [result for _call, result in textbook_results]
            if not any(
                _contains_textbook_quote(quote, _result_text_for_match(result))
                for result in candidate_results
            ):
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
                    (
                        ref
                        for ref in references
                        if _reference_matches_result(ref, result)
                    ),
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
    reasons = [
        f"too_few_{key}"
        for key, required_count in required.items()
        if observed[key] < required_count
    ]
    return {
        "passed": not reasons,
        "required": required,
        "observed": observed,
        "reason": reasons[0] if len(reasons) == 1 else ",".join(reasons) or None,
        "policy": policy["key"],
    }


def _count_uk_dialogue_lines(text: str) -> int:
    count = sum(
        1
        for line in text.splitlines()
        if re.match(r"^\s*>\s", line) and _UK_WORD_RE.search(line)
    )
    for jsx_block in _JSX_BLOCK_RE.findall(text):
        if _jsx_tag(jsx_block) != "DialogueBox":
            continue
        count += sum(
            1
            for value in _jsx_text_values(jsx_block)
            if _UK_WORD_RE.search(value)
        )
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
        if any(_UK_WORD_RE.search(cell) for cell in cells) and any(
            re.search(r"[A-Za-z]", cell) for cell in cells
        ):
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
    bullet_count = sum(
        1
        for line in text.splitlines()
        if re.match(r"^\s*[-*]\s+", line) and _UK_WORD_RE.search(line)
    )
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
            _append_unsupported_run(
                offending, tokens, run_start, run_end, max_unsupported, support_proximity
            )
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
    return {
        key
        for value in matched
        if (key := extract_citation_key(value)) is not None
    }


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
    suffix = " ..." if run_len > len(words) else ""
    offending.append(" ".join(words) + suffix)


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
    return [
        sentence
        for sentence in _split_immersion_sentences(text)
        if len(_UK_WORD_RE.findall(sentence)) > 10
    ]


def _inject_activity_gate(text: str, activities: list[dict[str, Any]]) -> dict[str, Any]:
    ids = {str(activity.get("id")) for activity in activities if activity.get("id")}
    injected = _INJECT_RE.findall(text)
    missing = [activity_id for activity_id in injected if activity_id not in ids]
    unused = sorted(ids - set(injected))
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

    hits = sorted(
        {
            pattern
            for pattern in AI_CONTAMINATION_PATTERNS
            if re.search(pattern, text, flags=re.IGNORECASE)
        }
    )
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

#: Markdown callout patterns we accept as engagement signal. Covers Starlight
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

    1. **Callouts** (Starlight ``:::tip``-style or GitHub ``[!myth-buster]``).
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


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end >= 0:
            text = text[end + 4 :]
    return text


def _strip_frontmatter_and_headings(text: str) -> str:
    text = _strip_frontmatter(text)
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )
