"""Render Phase 0 document placeholders inside prompt templates."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NORTH_STAR_PATH = PROJECT_ROOT / "docs" / "north-star.md"
LESSON_CONTRACT_PATH = PROJECT_ROOT / "docs" / "lesson-contract.md"

PLACEHOLDERS = {
    "{NORTH_STAR}": NORTH_STAR_PATH,
    "{LESSON_CONTRACT}": LESSON_CONTRACT_PATH,
}

DOWNSTREAM_TOKENS = frozenset(
    {
        "ACTIVITY_COUNT_TARGET",
        "ALLOWED_ACTIVITY_TYPES",
        "CANONICAL_ANCHORS",
        "CANONICAL_ANCHORS_REVIEWER",
        "CONTRACT_YAML",
        "CORRECTION_SECTION",
        "DIALOGUE_SITUATIONS",
        "DIM",
        "EXACT_SECTION_TITLES",
        "FORBIDDEN_ACTIVITY_TYPES",
        "GENERATED_CONTENT",
        "GOLDEN_DIALOGUE_ANCHORS",
        "GOLDEN_FRAGMENT",
        "IMMERSION_RULE",
        "IMMERSION_TARGET_SHORT",
        "INJECTION_MARKERS",
        "INLINE_ALLOWED_TYPES",
        "INLINE_MAX",
        "INLINE_MIN",
        "INLINE_PRIORITY_TYPES",
        "ITEMS_MIN",
        "ITEM_MINIMUMS_TABLE",
        "KNOWLEDGE_PACKET",
        "LETTER_MODULE_ACTIVE",
        "LEVEL",
        "LEVEL_CONSTRAINTS",
        "LEVEL_CONTEXT",
        "MIN_TYPES_UNIQUE",
        "MODULE_CONTENT",
        "MODULE_NUM",
        "MODULE_SLUG",
        "PEDAGOGICAL_CONSTRAINTS",
        "PEDAGOGY_PATTERNS",
        "PHASE",
        "PLAN_ACTIVITY_HINTS",
        "PLAN_CONTENT",
        "PLAN_VOCABULARY",
        "PRE_VERIFIED_FACTS",
        "PRIORITY_TYPES",
        "PRONUNCIATION_VIDEOS",
        "REQUIRED_TYPES",
        "SECTION_QUERIES",
        "SECTION_WIKI_EXCERPTS",
        "SEMINAR_TYPE_REFERENCE",
        "SKELETON_SECTION",
        "SUMMARY_HEADING",
        "TOOL_INSTRUCTIONS",
        "TOPIC_TITLE",
        "TOTAL_TARGET",
        "UNGROUNDED_FEEDBACK",
        "VOCABULARY_CHECKLIST",
        "VOCABULARY_HINTS",
        "VOCAB_COUNT_TARGET",
        "WORD_CEILING",
        "WORD_COUNT",
        "WORD_OVERSHOOT",
        "WORD_TARGET",
        "WORKBOOK_ALLOWED_TYPES",
        "WORKBOOK_MAX",
        "WORKBOOK_MIN",
        "WORKBOOK_PRIORITY_TYPES",
        "WRITER_MODEL",
    }
)

TOKEN_RE = re.compile(r"\{([A-Z][A-Z0-9_]*)\}")


def render_prompt(template_path: Path) -> str:
    """Render Phase 0 placeholders in a prompt template."""
    text = template_path.read_text(encoding="utf-8")

    for match in TOKEN_RE.finditer(text):
        token = match.group(1)
        if f"{{{token}}}" not in PLACEHOLDERS and token not in DOWNSTREAM_TOKENS:
            raise RuntimeError(
                f"Unknown placeholder-shaped token {{{token}}} in {template_path}. "
                "If this is a new Phase-0 placeholder, register it in PLACEHOLDERS. "
                "If it's a downstream .format() variable, register it in DOWNSTREAM_TOKENS. "
                "If it's a literal brace string, escape it."
            )

    for placeholder, source in PLACEHOLDERS.items():
        if not source.exists():
            raise FileNotFoundError(f"Phase 0 source missing for {placeholder}: {source}")
        source_text = source.read_text(encoding="utf-8")
        for literal_placeholder in PLACEHOLDERS:
            source_text = source_text.replace(literal_placeholder, literal_placeholder.strip("{}"))
        text = text.replace(placeholder, source_text)

    for placeholder in PLACEHOLDERS:
        if placeholder in text:
            raise RuntimeError(
                f"Unfilled placeholder remains after substitution: {placeholder} in {template_path}"
            )
    return text
