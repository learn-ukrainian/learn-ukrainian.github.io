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

PYTHON_QG_GATE_ORDER = (
    "word_count",
    "plan_sections",
    "formatting_standards",
    "vesum_verified",
    "citations_resolve",
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
    return _render_wiki_knowledge_packet(
        plan_data,
        wiki_packet,
        compressed,
        dictionary_context,
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
    elif isinstance(response, str) and all(name in response for name in WRITER_ARTIFACTS):
        write_writer_artifacts(module_dir, parse_writer_output_strict_json(response))


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
            "codex-tools",
            prompt,
            mode="read-only",
            cwd=module_dir,
            task_id=f"linear-python-qg-{gate}-fix",
            entrypoint="runtime",
            tool_config={"output_format": "text"},
        )
        response = str(getattr(result, "response", "") or "")
    else:
        response = reviewer_corrector(context) or ""
    fixes = _parse_reviewer_fixes(response)
    if fixes:
        module_path.write_text(_apply_reviewer_fixes(module_text, fixes), encoding="utf-8")


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


def _apply_reviewer_fixes(text: str, fixes: list[dict[str, str]]) -> str:
    updated = text
    for fix in fixes:
        if "insert_after" in fix and "text" in fix:
            anchor = fix["insert_after"]
            if anchor in updated:
                updated = updated.replace(anchor, anchor + fix["text"], 1)
            continue
        find = fix.get("find")
        replace = fix.get("replace")
        if find and replace is not None and find in updated:
            updated = updated.replace(find, replace, 1)
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
        from scripts.verification.vesum import verify_words as verify_words_fn

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
