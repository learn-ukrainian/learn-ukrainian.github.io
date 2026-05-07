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
import unicodedata
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.build.citation_matcher import (
    extract_citation_key,
    extract_plan_reference_titles,
    normalize_citation_ref,
)
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

WRITER_CHOICES = ("claude-tools", "gemini-tools", "codex-tools")
WRITER_DEFAULTS: dict[str, dict[str, str]] = {
    "claude-tools": {"model": "claude-opus-4-7", "effort": "xhigh"},
    "gemini-tools": {"model": "gemini-3.1-pro-preview", "effort": "high"},
    "codex-tools": {"model": "gpt-5.5", "effort": "high"},
}
REVIEWER_CHOICES = ("claude-tools", "gemini-tools", "codex-tools")
REVIEWER_DEFAULTS: dict[str, dict[str, str]] = {
    "claude-tools": {"model": "claude-opus-4-7", "effort": "xhigh"},
    "gemini-tools": {"model": "gemini-3.1-pro-preview", "effort": "high"},
    "codex-tools": {"model": "gpt-5.5", "effort": "high"},
}
WRITER_ARTIFACTS = (
    "module.md",
    "activities.yaml",
    "vocabulary.yaml",
    "resources.yaml",
)

PYTHON_QG_GATE_ORDER = (
    "tool_theatre",
    "word_count",
    "plan_sections",
    "formatting_standards",
    "vesum_verified",
    "citations_resolve",
    "textbook_grounding",
    "immersion",
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
        "immersion",
        "ai_slop_clean",
    }
)
PIPELINE_INSERT_GATES = frozenset({"inject_activity_ids"})
TERMINAL_ZERO_RETRY_GATES = frozenset(
    {
        "component_props",
        "previously_passed_regression",
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
)
PROMPT_ADHERENCE_FIELD_PATTERNS: dict[str, tuple[str, ...]] = {
    "word_budget": (
        r"word[_\s-]*budget",
        r"budget\s+per\s+section",
    ),
    "plan_vocab": (
        r"plan[_\s-]*vocab",
        r"required[_\s-]*(?:plan[_\s-]*)?vocab",
        r"required[_\s-]*terms",
        r"required[_\s-]*vocabulary",
    ),
    "register": (
        r"register",
        r"immersion",
        r"ukrainian\s+and\s+english",
    ),
    "teaching_sequence": (
        r"teaching[_\s-]*sequence",
        r"knowledge\s+packet",
        r"citation\s+sequence",
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
        "search_text",
        "check_modern_form",
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
CORRECTION_PREVIEW_CHARS = 200
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


def _search_textbook_hits(query: str, *, level: str, limit: int = 1) -> list[dict]:
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
        hits = _search_textbook_hits(query, level=level, limit=1)
        lines.append(f"### {title}")
        lines.append("")
        if not hits:
            for ref in plan.get("references") or []:
                if isinstance(ref, dict) and str(ref.get("title") or "").strip() == title:
                    ref["corpus_missing"] = True
            lines.append("*No textbook excerpt found for this reference.*")
            lines.append("corpus_missing: true")
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
            if re.search(pattern + r".{0,80}\S", body, flags=re.IGNORECASE | re.DOTALL):
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
_TOOL_CITATION_RE = re.compile(
    r"`?(?P<name>(?:mcp__sources__|search_|verify_|check_|query_|translate_)\w+)`?"
)


def _normalize_tool_citation_name(raw_tool: Any) -> str:
    tool = str(raw_tool or "").strip()
    if tool.startswith("mcp__sources__"):
        tool = tool.removeprefix("mcp__sources__")
    return tool


def _tool_name_from_call(call: Any) -> str:
    mapped = _mapping_from_tool_call(call)
    return _normalize_tool_citation_name(
        mapped.get("tool") or mapped.get("tool_name") or mapped.get("name")
    )


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
    for match in _PLAN_REASONING_ELEMENT_RE.finditer(writer_output):
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


def _runtime_tool_calls(result: Any) -> list[dict[str, Any]]:
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
        tool = tool.rsplit("__", 1)[-1]
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


def _summarize_tool_result(tool: str, result: Any) -> dict[str, Any]:
    if tool == "verify_words":
        return _summarize_verify_words_result(result)
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

    tool_calls_total = 0
    verify_words_calls = 0
    for call in tool_calls or []:
        tool = _normalize_tool_name(
            call.get("tool") or call.get("tool_name") or call.get("name")
        )
        if tool not in WRITER_TOOL_NAMES:
            continue
        args = call.get("args", call.get("arguments", {}))
        result = call.get("result", call.get("response"))
        tool_calls_total += 1
        if tool == "verify_words":
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
        "end_gate_fired": bool(gate["gate_present"]),
        "removed_via_gate": int(gate["removed_count"]),
    }
    theatre_violations = detect_tool_theatre(output, list(tool_calls or []))
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
    _emit(event_sink, "phase_writer_summary", writer=writer, module=module, **summary)
    return summary


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


def _runtime_tool_config(agent_label: str) -> dict[str, Any]:
    tool_config: dict[str, Any] = {"output_format": "text"}
    if agent_label == "codex-tools":
        from scripts.agent_runtime.tool_config import build_mcp_tool_config

        codex_tools = build_mcp_tool_config("codex", mcp_servers=["sources"])
        if codex_tools:
            tool_config.update(codex_tools)
    return tool_config


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
        tool_config=_runtime_tool_config(writer),
        stdout_silence_timeout=stdout_silence_timeout,
    )
    response = getattr(result, "response", None)
    if not response:
        raise LinearPipelineError("Writer call returned no response")
    response_text = str(response)
    module_ref = module or _prompt_module_ref(prompt)
    section_names = list(sections) if sections is not None else _prompt_sections(prompt)
    tool_calls = _runtime_tool_calls(result)
    if tool_trace_path is not None:
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
        emit_writer_response_telemetry(
            response_text,
            writer=writer,
            module=module_ref,
            sections=section_names,
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

    Returns the module.md body (with one trailing newline) on the contract
    match, else None. Used by `_apply_writer_correction` for gates that only
    modify module.md (everything in WRITER_CORRECTION_GATES except
    `strict_json_parse`, which needs all four artifacts re-emitted).
    """
    if not isinstance(response, str):
        return None
    stripped = response.strip()
    # Hard guards: the entire response must be one triple-fence block.
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
        tool_config=_runtime_tool_config(reviewer),
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
) -> str:
    """Render the ADR-008 patch-bounded writer correction prompt."""
    return render_phase_prompt(
        PROJECT_ROOT / "scripts" / "build" / "phases" / "linear-writer-correction.md",
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
            "Emit only local <fixes> find/replace pairs. Do not rewrite sections."
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
            "Return a single <fixes> block. Use find/replace pairs only.",
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
    verdict = str(payload.get("verdict", "")).upper()
    entry = {
        "score": score,
        "evidence": evidence,
        "verdict": verdict,
    }
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
) -> dict[str, Any]:
    """Run Python QG and apply one ADR-008 correction attempt per failed gate.

    This wrapper preserves ``run_python_qg`` as the deterministic gate runner.
    Corrections are intentionally single-shot. After every correction the full
    Python QG report is recomputed, and any gate that regresses from PASS to
    FAIL triggers the ``previously_passed_regression`` terminal meta-gate.
    """
    attempts: set[str] = set()

    def _run_qg() -> dict[str, Any]:
        if qg_runner is not None:
            return qg_runner()
        return run_python_qg(
            module_dir,
            plan_path,
            verify_words_fn=verify_words_fn,
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

        before = report
        handled = _apply_python_qg_correction(
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
            _annotate_correction_terminal(
                report,
                failed_gate,
                f"{failed_gate} has no ADR-008 correction path",
            )
            return report

        report = _run_qg()
        regressions = _previously_passing_regressions(before, report)
        if regressions:
            gates = report.setdefault("gates", {})
            if isinstance(gates, dict):
                gates["previously_passed_regression"] = {
                    "passed": False,
                    "regressions": regressions,
                }
                gates["passed"] = False
            return report


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
) -> bool:
    gates = qg_report.get("gates")
    if not isinstance(gates, Mapping):
        return False
    gate_report = gates.get(gate)
    if not isinstance(gate_report, Mapping):
        return False
    if gate in TERMINAL_ZERO_RETRY_GATES:
        return False
    if gate in PIPELINE_INSERT_GATES:
        _apply_activity_id_inserts(module_dir / "module.md", gate_report)
        return True
    if gate in WRITER_CORRECTION_GATES:
        _apply_writer_correction(
            gate,
            gate_report,
            qg_report=qg_report,
            module_dir=module_dir,
            plan_path=plan_path,
            writer_corrector=writer_corrector,
            writer=writer,
            invoker=invoker,
        )
        return True
    if gate in REVIEWER_FIX_GATES:
        candidates = ()
        if gate in DICTIONARY_CANDIDATE_GATES:
            candidates = generate_dictionary_candidates(
                gate,
                gate_report,
                qg_report=qg_report,
                dictionary_lookup_fn=dictionary_lookup_fn,
            )
        _apply_reviewer_correction(
            gate,
            gate_report,
            qg_report=qg_report,
            module_dir=module_dir,
            plan_path=plan_path,
            candidates=candidates,
            reviewer_corrector=reviewer_corrector,
            invoker=invoker,
        )
        return True
    return False


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
) -> None:
    module_text = _read_required(module_dir / "module.md")
    prompt = render_writer_correction_prompt(
        gate=gate,
        gate_report=gate_report,
        module_text=module_text,
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
        return
    if isinstance(response, str):
        # Strict-JSON-parse failures need all 4 artifact blocks back since the
        # original parse was the failure mode itself. Other gates are
        # module.md-only patches per the linear-writer-correction.md output
        # contract.
        if all(name in response for name in WRITER_ARTIFACTS):
            write_writer_artifacts(module_dir, parse_writer_output_strict_json(response))
            return
        if gate != "strict_json_parse":
            patched = parse_writer_correction_module_only(response)
            if patched is not None:
                (module_dir / "module.md").write_text(patched, encoding="utf-8")
                return
    emit_event(
        "writer_correction_unparseable",
        **_correction_event_fields(
            gate=gate,
            module_dir=module_dir,
            plan_path=plan_path,
        ),
        response_preview=_correction_preview(response),
    )


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
) -> None:
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
        return
    updated = _apply_reviewer_fixes(
        module_text,
        fixes,
        gate=gate,
        module_dir=module_dir,
        plan_path=plan_path,
    )
    if fixes:
        module_path.write_text(updated, encoding="utf-8")


def _apply_activity_id_inserts(module_path: Path, gate_report: Mapping[str, Any]) -> None:
    unused = [str(activity_id) for activity_id in gate_report.get("unused", [])]
    if not unused:
        return
    text = _read_required(module_path).rstrip()
    markers = "\n\n".join(f"<!-- INJECT_ACTIVITY: {activity_id} -->" for activity_id in unused)
    module_path.write_text(f"{text}\n\n{markers}\n", encoding="utf-8")


def _parse_reviewer_fixes(review_text: str) -> list[dict[str, str]]:
    match = re.search(r"<fixes>\s*(.*?)\s*</fixes>", review_text, re.DOTALL)
    if not match:
        return []
    body = match.group(1).strip()
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


def _apply_reviewer_fixes(
    text: str,
    fixes: list[dict[str, str]],
    *,
    gate: str | None = None,
    module_dir: Path | None = None,
    plan_path: Path | None = None,
) -> str:
    updated = text
    for fix in fixes:
        if "insert_after" in fix and "text" in fix:
            anchor = fix["insert_after"]
            if anchor in updated:
                updated = updated.replace(anchor, anchor + fix["text"], 1)
            else:
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
    return updated


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

    def record(name: str, report: dict[str, Any]) -> None:
        if gate_observer is not None:
            gate_observer(name)
        gates[name] = report

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
        ),
    )
    record("citations_resolve", _citation_gate(resources, plan))
    record("textbook_grounding", _textbook_grounding_gate(module_text, plan, module_dir))
    record("immersion", _immersion_gate(module_text, plan))
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
    return {
        "module": plan["module"],
        "level": plan["level"],
        "slug": plan["slug"],
        "pipeline": "linear-phase-4",
        "plan_references": plan.get("references", []),
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
    output_path.write_text(mdx, encoding="utf-8")  # codeql[py/clear-text-storage-sensitive-data] - .mdx curriculum content, never sensitive data
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
            for word in _iter_vesum_word_surfaces(text)
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
        from scripts.verification.vesum import verify_words as verify_words_fn

    # VESUM is case-sensitive — lowercase before lookup so sentence-initial
    # words like "Спочатку" match the lemma "спочатку".
    lookup_words = sorted({lower for _surface, lower in unchecked_pairs})
    try:
        verified = verify_words_fn(lookup_words)
    except Exception as exc:
        return {"passed": False, "error": str(exc), "checked": len(unchecked_pairs)}

    missing_lc = {word for word, matches in verified.items() if not matches}
    if missing_lc:
        original_case_words = sorted(
            {
                surface
                for surface, lower in unchecked_pairs
                if lower in missing_lc and surface != lower
            }
        )
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


def _iter_vesum_word_surfaces(text: str) -> list[str]:
    """Extract Ukrainian surface forms that are meaningful VESUM candidates."""
    words: list[str] = []
    for match in _UK_WORD_RE.finditer(text):
        if _touches_blank_marker(text, match.start(), match.end()):
            continue
        raw = match.group(0)
        if _looks_like_elided_notation(text, match.start(), raw):
            continue
        word = raw.strip("-'ʼ")
        if not word:
            continue
        if word.lower() in _STANDALONE_POSTFIX_FRAGMENTS:
            continue
        words.append(word)
    return words


def _touches_blank_marker(text: str, start: int, end: int) -> bool:
    """Return true when a regex word is a stem fragment next to `__` blanks."""
    return (start > 0 and text[start - 1] == "_") or (
        end < len(text) and text[end] == "_"
    )


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
        source_ref = str(resource.get("source_ref") or resource.get("title") or "")
        normalized_ref = _normalize_citation_ref(source_ref)
        source_key = extract_citation_key(source_ref)
        if (
            normalized_ref not in plan_titles
            and source_key not in plan_keys
            and resource.get("packet_chunk_id") is None
        ):
            unknown.append(source_ref)
    return {"passed": not unknown, "unknown": unknown}


def _extract_blockquote_records(text: str) -> list[dict[str, str]]:
    quotes: list[dict[str, str]] = []
    current: list[str] = []
    current_section = ""
    quote_section = ""
    for line in text.splitlines():
        heading = re.match(r"^\s{0,3}#{1,6}\s+(?P<title>.+?)\s*#*\s*$", line)
        if heading:
            current_section = re.sub(r"[*_`~]+", "", heading.group("title")).strip()
        match = re.match(r"^\s*>\s?(?P<body>.*)$", line)
        if match:
            if not current:
                quote_section = current_section
            current.append(match.group("body"))
            continue
        if current:
            quotes.append(
                {
                    "quote": "\n".join(current).strip(),
                    "section_title": quote_section,
                }
            )
            current = []
            quote_section = ""
    if current:
        quotes.append(
            {"quote": "\n".join(current).strip(), "section_title": quote_section}
        )
    return [record for record in quotes if record["quote"]]


def _extract_blockquotes(text: str) -> list[str]:
    return [record["quote"] for record in _extract_blockquote_records(text)]


def _normalize_match_text(text: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", text)
    text = text.replace("’", "'").replace("ʼ", "'")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _textbook_match_tokens(text: str) -> list[str]:
    text = _normalize_match_text(text)
    text = re.sub(r"[*_`~#>|]", " ", text)
    return re.findall(r"[0-9A-Za-zА-Яа-яҐґЄєІіЇї'-]+", text.casefold())


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


def _result_items_from_call(call: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    result = call.get("result", call.get("response"))
    if result is None and call.get("result_excerpt"):
        result = {"text": call["result_excerpt"]}
        if call.get("source_type"):
            result["source_type"] = call["source_type"]
    if isinstance(result, list):
        return [item for item in result if isinstance(item, Mapping)]
    if isinstance(result, Mapping):
        result = dict(result)
        if call.get("source_type") and not result.get("source_type"):
            result["source_type"] = call["source_type"]
        raw_hits = result.get("results") or result.get("hits") or result.get("items")
        if isinstance(raw_hits, list):
            return [item for item in raw_hits if isinstance(item, Mapping)]
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
    if ref_key is not None and result_text and extract_citation_key(result_text) == ref_key:
        return True
    normalized_ref = _normalize_citation_ref(reference_title).casefold()
    normalized_result = _normalize_citation_ref(result_text).casefold()
    return bool(normalized_ref and normalized_ref in normalized_result)


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
    search_calls = [
        call
        for call in _load_writer_tool_calls(module_dir)
        if _tool_name_from_call(call) == "search_text"
    ]
    textbook_results: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for call in search_calls:
        for result in _result_items_from_call(call):
            if _is_textbook_result(result):
                textbook_results.append((call, result))

    matched: dict[str, int] = {}
    topical_mismatches: list[str] = []
    unattributed_matches = 0
    downgraded = [
        record["title"]
        for record in reference_records
        if record["corpus_missing"] or not record["verbatim_required"]
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
            if not any(
                _contains_textbook_quote(quote, _result_text_for_match(result))
                for result in ref_results
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
    if downgraded:
        warnings.append("corpus_missing_or_verbatim_not_required")
    reason = "topical_mismatch" if not passed and topical_mismatches else None
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
        "textbook_result_hits": len(textbook_results),
        "min_words": TEXTBOOK_GROUNDING_MIN_WORDS,
        "downgraded": downgraded,
        "warnings": warnings,
        "reason": reason,
        "unattributed_matches": unattributed_matches,
    }


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
    (`. ! ? … ‼ ⁇ ⁈ ⁉`) and markdown structure starts: dialogue dashes,
    table rows, bullets, numbered list items, blockquotes, and headers. This
    keeps dialogue turns and table rows from being joined into one giant run.
    """
    level = str(plan["level"]).lower()
    sequence = int(plan["sequence"])
    min_pct, max_pct = get_immersion_range(level, sequence)
    comment_stripped = _strip_comments(text)
    body = _strip_frontmatter_and_headings(comment_stripped)
    sentence_body = _strip_frontmatter(comment_stripped)

    body_no_jsx = _JSX_BLOCK_RE.sub(" ", body)
    sentence_body_no_jsx = _JSX_BLOCK_RE.sub(" ", sentence_body)
    jsx_string_props: list[str] = []
    for jsx_block in _JSX_BLOCK_RE.findall(body):
        jsx_string_props.extend(_JSX_STRING_VALUE_RE.findall(jsx_block))
    counted_text = "\n".join([body_no_jsx, *jsx_string_props])

    tokens = _WORD_RE.findall(counted_text)
    uk_tokens = [token for token in tokens if _UK_WORD_RE.search(token)]
    pct = round((len(uk_tokens) / len(tokens) * 100), 2) if tokens else 0.0

    long_sentences = _long_ukrainian_sentences(sentence_body_no_jsx)
    return {
        "passed": min_pct <= pct <= max_pct and not long_sentences,
        "pct": pct,
        "min_pct": min_pct,
        "max_pct": max_pct,
        "policy": get_immersion_policy(level, sequence)["key"],
        "long_ukrainian_sentences": long_sentences[:20],
    }


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
