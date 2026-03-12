#!/usr/bin/env python3
"""Pipeline shared utilities — single source of truth for build pipeline functions.

Consolidates shared utilities used by build_module_v5.py (via pipeline_v5.py)
and external scripts.

Key design decisions:
  - dispatch_gemini: includes rate-limit fallback (from v2)
  - dispatch_gemini_raw: original no-fallback version (for external scripts)
  - mark_phase: always uses FileLock (merged v1 base + v2 locking)
  - log: thread-safe by default (no string hacks)
  - No monkey-patching anywhere
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import warnings
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Setup: ensure scripts/ is on sys.path
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from batch_gemini_config import (
    FLASH_MODEL,
    PHASES_DIR,
    PRO_MODEL,
    PRO_TRACKS,
    PROJECT_ROOT,
    SEMINAR_TRACKS,
    VENV_PYTHON,
    get_module_paths,
    get_track_config,
    slug_for_num,
)

# ============================================================================
# 1. Config Tables (data only, no logic)
# ============================================================================

TRACK_SKILLS: dict[str, tuple[str, str, str]] = {
    # track_pattern: (skill_file, skill_identity, persona_flavor)
    "a1":       ("full-rebuild-core-a", "Patient & Supportive Ukrainian Tutor", "The Helpful Neighbor"),
    "a2":       ("full-rebuild-core-a", "Patient & Supportive Ukrainian Tutor", "The Helpful Neighbor"),
    "b1-early": ("full-rebuild-core-a", "Patient & Supportive Ukrainian Tutor", "The Helpful Neighbor"),
    "b1-late":  ("full-rebuild-core-b", "Senior Ukrainian Language & Culture Specialist", "Ethnographer"),
    "b2":       ("full-rebuild-core-b", "Senior Ukrainian Language & Culture Specialist", "Ethnographer"),
    "b2-pro":   ("full-rebuild-core-b", "Senior Ukrainian Language & Culture Specialist", "Ethnographer"),
    "c1":       ("full-rebuild-core-b", "Senior Ukrainian Language & Culture Specialist", "Ethnographer"),
    "c1-pro":   ("full-rebuild-core-b", "Senior Ukrainian Language & Culture Specialist", "Ethnographer"),
    "c2":       ("full-rebuild-core-b", "Senior Ukrainian Language & Culture Specialist", "Ethnographer"),
    "bio":   ("full-rebuild-bio", "Professor of Ukrainian Arts (biography)", "The Archival Detective"),
    "hist":  ("full-rebuild-hist", "Professor of Ukrainian Arts (history)", "The Decolonial Lecturer"),
    "istorio":  ("full-rebuild-istorio", "Professor of Ukrainian Arts (historiography)", "The Source Critic"),
    "lit":      ("full-rebuild-lit", "Professor of Ukrainian Arts (literature)", "The Stylistic Critic"),
    "oes":      ("full-rebuild-oes", "Professor of Ukrainian Arts (paleography)", "The Paleographer"),
    "ruth":     ("full-rebuild-ruth", "Professor of Ukrainian Arts (Ruthenian)", "The Baroque Scholar"),
}

IMMERSION_RULES: dict[str, str] = {
    "a1-m01-02": (
        "TARGET: 5-15% Ukrainian.\n"
        "LANGUAGE ROLES:\n"
        "- THEORY & EXPLANATION: 100% English.\n"
        "- UKRAINIAN CONTENT: Individual letters and words only — bolded inline in English prose "
        "with translation in parentheses: \"The letter **Н** looks like H but sounds like N.\"\n"
        "- TABLES: Simple letter-sound or word-meaning tables (Ukrainian in left column, English in right).\n"
        "- STRUCTURAL RULE: Every paragraph is English. Ukrainian never appears as a standalone sentence.\n"
        "Ukrainian sentences max 10 words."
    ),
    "a1-m03-05": (
        "TARGET: 10-25% Ukrainian.\n"
        "LANGUAGE ROLES:\n"
        "- THEORY & EXPLANATION: 100% English.\n"
        "- UKRAINIAN CONTENT: Words and short phrases bolded inline: \"The word **книга** (book) is feminine.\"\n"
        "- TABLES: Vocabulary tables, letter groups, simple word families.\n"
        "- STRUCTURAL RULE: Every paragraph is English. Ukrainian words/phrases appear inline bolded. "
        "Full Ukrainian sentences (3+ words with a verb) go in tables or bulleted example lists with English gloss.\n"
        "Ukrainian sentences max 10 words."
    ),
    "a1-m06-10": (
        "TARGET: 15-35% Ukrainian.\n"
        "LANGUAGE ROLES:\n"
        "- THEORY & EXPLANATION: English prose. Introduce Ukrainian grammar terms bolded with translation on first use.\n"
        "- UKRAINIAN CONTENT: Words and phrases inline bolded. Short example sentences in bulleted lists "
        "or tables — each with English gloss on the same line.\n"
        "- TABLES: Word families, vocabulary groups, simple paradigm tables.\n"
        "- PATTERN BOXES: Show transformations: `слово → слова` (word → words).\n"
        "- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian vocabulary. "
        "Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes — never in flowing prose.\n"
        "Ukrainian sentences max 10 words."
    ),
    "a1-m11-20": (
        "TARGET: 25-40% Ukrainian.\n"
        "LANGUAGE ROLES:\n"
        "- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.\n"
        "- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.\n"
        "- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.\n"
        "- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).\n"
        "- INLINE: Ukrainian words/phrases bolded in English prose.\n"
        "- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. "
        "Full Ukrainian sentences (3+ words with a verb) go in tables, bulleted example lists, or pattern boxes. "
        "Never write a Ukrainian sentence followed by its English translation in a prose paragraph.\n"
        "Ukrainian sentences max 10 words. Mix container types — don't use tables for everything."
    ),
    "a1-m21+": (
        "TARGET: 30-55% Ukrainian.\n"
        "LANGUAGE ROLES:\n"
        "- THEORY & EXPLANATION: English prose — MAXIMUM 2 sentences per concept. "
        "You must explain grammar primarily by demonstrating it. Show, don't tell.\n"
        "- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian. "
        "This is the highest-density immersion tool. Do not explain usage nuances in English prose — "
        "instead, create dual-column tables (Ukrainian Sentence | English Context/Translation) "
        "that map out the nuances. Move the teaching logic inside the tables.\n"
        "- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).\n"
        "- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.\n"
        "- PATTERN BOXES: Show transformations: `читати → читай → читайте`.\n"
        "- INLINE: Ukrainian words/phrases bolded in English prose.\n"
        "- IMMERSION BLOCKS: Every major H2 section MUST conclude with a substantial "
        "Ukrainian-only dialogue or narrative blockquote (>) of at least 80-150 words "
        "demonstrating the concepts in context. If translations are needed, place them "
        "in a separate table BELOW the blockquote.\n"
        "- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. "
        "Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes — never in flowing prose paragraphs. "
        "Vary your containers — never use the same type twice in a row.\n"
        "Ukrainian sentences max 10 words.\n"
        "NOTE: When the lexical sandbox has fewer than 20 lemmas, the immersion floor is lowered "
        "to prevent repetitive padding. Focus on quality immersion with the available vocabulary "
        "rather than forcing high percentages.\n\n"
        "BEFORE/AFTER EXAMPLE — follow the AFTER pattern:\n\n"
        "❌ BAD (too much English, ~10% immersion):\n"
        "To form the imperative mood in Ukrainian, you take the infinitive form of the verb "
        "and remove the -ти ending. Then you add the appropriate suffix depending on whether "
        "you are speaking to one person informally or to multiple people formally. For the "
        "informal singular form, you simply use the stem. For the formal or plural form, "
        "you add -те to the informal form.\n\n"
        "✅ GOOD (tables + dialogue + examples, ~45% immersion):\n"
        "Drop **-ти** from the infinitive to form commands.\n\n"
        "| Infinitive | ти-command | ви-command |\n"
        "|---|---|---|\n"
        "| читати | читай | читайте |\n"
        "| писати | пиши | пишіть |\n\n"
        "> — **Читай** текст! — Read the text!\n"
        "> — **Пишіть** відповідь. — Write the answer.\n"
        "> — **Слухайте** уважно! — Listen carefully!\n\n"
        "Add **будь ласка** to soften any command.\n\n"
        "- **Дайте, будь ласка, воду.** — Please give water.\n"
        "- **Скажіть, будь ласка, де метро?** — Please tell me, where is the metro?"
    ),
    "a2-m01-20": (
        "TARGET: 45-65% Ukrainian.\n"
        "LANGUAGE ROLES:\n"
        "- THEORY: English prose for grammar explanations that would be too complex in Ukrainian at this level.\n"
        "- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, cultural context.\n"
        "- HEADERS: Ukrainian with English in parentheses.\n"
        "- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix languages within a sentence. "
        "Ukrainian paragraphs and dialogues carry most content. English appears for grammar theory and in callout boxes.\n"
        "A2 register ONLY. Concrete everyday vocabulary. No literary/poetic language. No abstract nouns. "
        "Ukrainian sentences max 15 words. Max 2 clauses. "
        "All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles."
    ),
    "a2-m21-50": (
        "TARGET: 55-75% Ukrainian.\n"
        "LANGUAGE ROLES:\n"
        "- PRIMARY: Ukrainian for all content — dialogues, examples, section intros, cultural context.\n"
        "- ENGLISH: Only for abstract grammar concepts that need explicit explanation.\n"
        "- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English. "
        "Dialogues, examples, section intros all stay Ukrainian-only.\n"
        "A2 register. Concrete everyday vocabulary. No literary language, no metaphors. "
        "Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. "
        "Simple subordinate clauses only. Aspect pairs introduced. No participles."
    ),
    "a2-m51-70": (
        "TARGET: 70-90% Ukrainian.\n"
        "LANGUAGE ROLES:\n"
        "- PRIMARY: Ukrainian for everything.\n"
        "- ENGLISH: Only in vocabulary tables and one-line grammar notes where absolutely necessary.\n"
        "- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English.\n"
        "A2 register. Concrete everyday vocabulary. No literary language, no metaphors. "
        "Near-full Ukrainian immersion. Ukrainian sentences max 15 words. Max 2 clauses. "
        "All cases allowed. Simple subordinate clauses only. Full aspect pairs. No participles."
    ),
    "b1-bridge": (
        "Bridge modules: teach grammar metalanguage. English scaffolding for abstract concepts. "
        "Parenthetical equivalents for new terms. Sentences max 30 words."
    ),
    "b1-core": (
        "Full Ukrainian immersion. Grammar explained IN Ukrainian. "
        "English only for disambiguation of false friends. Sentences max 30 words."
    ),
    "b2+": (
        "Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words."
    ),
}

LEVEL_CONSTRAINTS: dict[str, str] = {
    "a1": (
        "HARD GRAMMAR RULES (audit will reject violations):\n"
        "- Max 10 words per Ukrainian sentence (STRICT — count every word)\n"
        "- ONLY 1 clause per sentence (no compound sentences)\n"
        "- Dative case FORBIDDEN (no мені, тобі, йому, їй, вам, їм, -ові/-еві endings)\n"
        "  Exception: нам is taught as decodable vocabulary in M1 (reading drill word, not grammar)\n"
        "  Exception (M19 likes-and-preferences): Dative forms мені/тобі/йому/їй/нам/вам/їм allowed\n"
        "    ONLY in the fixed construction «Мені подобається + noun/infinitive». Teach as a memorized\n"
        "    chunk — do NOT explain dative case rules or paradigms.\n"
        "- Instrumental case FORBIDDEN (no з другом, з мамою, -ом/-ою/-ем/-ею endings)\n"
        "- NO subordinate clauses: який/яка/яке, що-clause, коли, якщо, тому що, бо, щоб, поки are ALL BANNED\n"
        "- Only imperfective aspect verbs\n"
        "- No participles\n"
        "- Allowed cases: Nominative, Accusative, Locative (from M13), Genitive (basics), Vocative"
    ),
    "a2": (
        "GRAMMAR RULES:\n"
        "- Max 15 words per Ukrainian sentence\n"
        "- Max 2 clauses per sentence\n"
        "- All cases allowed\n"
        "- Simple subordinate clauses allowed (який/що/коли)\n"
        "- Aspect pairs introduced but not complex\n"
        "- No participles"
    ),
    "b1": (
        "GRAMMAR RULES:\n"
        "- Max 30 words per Ukrainian sentence\n"
        "- Max 4 clauses per sentence\n"
        "- All grammar constructions allowed\n"
        "- Participles allowed\n"
        "- Complex subordinate clauses allowed"
    ),
    "b2": (
        "GRAMMAR RULES:\n"
        "- Max 35 words per Ukrainian sentence\n"
        "- Max 6 clauses\n"
        "- Full grammar including adverbial participles"
    ),
    "c1": "No grammar restrictions. Full literary Ukrainian.",
    "c2": "No grammar restrictions. Full literary Ukrainian.",
}

# Phase-level pedagogical constraints for A1 — keyed by plan `phase` field.
# Grammar/imperative bans are genuinely per-phase (not per-module).
# Decodability is NOT here — it's derived from the plan at runtime.
_A1_PHASE_CONSTRAINTS: dict[str, str] = {
    "A1.1": (
        "GRAMMAR BAN (pre-verbal phase — no verbs exist yet):\n"
        "- NO imperative forms: Слухайте, Читайте, Повторюйте, Пишіть, Дивіться — ALL BANNED\n"
        "- NO verb conjugation of any kind (present, past, future)\n"
        "- Classroom instructions MUST be in English: 'Listen carefully', 'Read aloud', 'Repeat'\n"
        "- Allowed Ukrainian structures: bare nouns, noun phrases, Це + noun\n\n"
        "METALANGUAGE:\n"
        "- ALL terminology in English first, Ukrainian in parentheses: 'vowels (голосні)'\n"
        "- Section headings MUST be bilingual (e.g., '## Голосні — Vowels')\n"
        "- NEVER write Ukrainian-only explanatory prose\n\n"
        "VERB-FREE UKRAINIAN PATTERN BANK:\n"
        "- Це + noun: «Це кіт», «Це стіл»\n"
        "- Question particles: «Хто це?», «Що це?»\n"
        "- Adj + noun: «великий дім», «нова книга»\n"
        "- Contextual labels: «Наприклад — For example», «А тепер — And now»\n"
        "DO NOT use conjugated verbs, imperatives, or infinitives."
    ),
    "A1.2": (
        "SEQUENCE CONSTRAINTS (A1.2 — Verbs & Sentences):\n"
        "Present tense verbs are being introduced in this phase.\n\n"
        "KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) "
        "are NOT taught until M47 (imperative-and-requests). "
        "Use indirect requests or English for instructions.\n\n"
        "BANNED IMPERATIVE FORMS: Запам'ятайте, Уявіть, Порівняйте, "
        "Зверніть увагу, Спробуйте, Подивіться, Послухайте, Прочитайте, Повторіть, "
        "Напишіть, Скажіть, Виберіть, Подивімось, Поговорімо, Повторімо, "
        "Давайте розглянемо, Розглянемо.\n\n"
        "INSTEAD OF → USE:\n"
        "- Запам'ятайте → \"Remember that...\" (English)\n"
        "- Подивіться → \"Look at...\" (English)\n"
        "- Прочитайте → \"Read...\" (English)\n"
        "- Повторіть → \"Repeat...\" (English)"
    ),
    "A1.3": (
        "SEQUENCE CONSTRAINTS (A1.3 — Cases & Navigation):\n"
        "Present tense verbs available. Cases being introduced.\n\n"
        "IMPERATIVE BAN still applies (taught at M47).\n"
        "BANNED: Запам'ятайте, Порівняйте, Зверніть увагу, Подивіться, "
        "Прочитайте, Повторіть — use English equivalents."
    ),
    "A1.4": (
        "SEQUENCE CONSTRAINTS (A1.4 — Tenses & Daily Life):\n"
        "Past tense and future tense introduced. All present tense available.\n\n"
        "IMPERATIVE BAN still applies (taught at M47).\n"
        "BANNED: Запам'ятайте, Порівняйте, Зверніть увагу, Подивіться, "
        "Прочитайте, Повторіть — use English equivalents."
    ),
    "A1.5": (
        "SEQUENCE CONSTRAINTS (A1.5 — Modals, Commands & Life):\n"
        "All tenses available. Imperative mood is TAUGHT in this phase (M47).\n"
        "Imperative forms are ALLOWED after M47 introduces them.\n\n"
        "For M47 itself: Use imperative forms freely — читай/читайте, пиши/пишіть, "
        "скажи/скажіть, дай/дайте, іди/ідіть.\n"
        "Both imperfective AND perfective verbs allowed for imperatives."
    ),
    "A1.6": (
        "SEQUENCE CONSTRAINTS (A1.6 — Real-World Skills):\n"
        "Full A1 grammar available including imperatives. "
        "The standard A1 LEVEL_CONSTRAINTS apply."
    ),
}

# Shared imperative ban text (DRY — used by multiple phases)
_IMPERATIVE_BAN = (
    "BANNED IMPERATIVE FORMS: Запам'ятайте, Уявіть, Порівняйте, "
    "Зверніть увагу, Спробуйте, Подивіться, Послухайте, Прочитайте, Повторіть, "
    "Напишіть, Скажіть, Виберіть, Подивімось, Поговорімо, Повторімо, "
    "Давайте розглянемо, Розглянемо.\n"
    "Use English equivalents instead."
)


# Common Ukrainian section titles → bilingual equivalents
_BILINGUAL_TITLES: dict[str, str] = {
    "Вступ": "Вступ — Introduction",
    "Практика": "Практика — Practice",
    "Підсумок": "Підсумок — Summary",
    "Перші слова": "Перші слова — First Words",
    "Перші склади": "Перші склади — First Syllables",
    "Практика читання": "Практика читання — Reading Practice",
}
# Pattern: "Голосні — X, Y" → "Голосні — Vowels: X, Y"
_BILINGUAL_PREFIXES: dict[str, str] = {
    "Голосні": "Vowels",
    "Приголосні": "Consonants",
}


def bilingualify_section_titles(content_outline: list, track: str, module_num: int) -> list:
    """Make section titles bilingual for early A1 modules (M1-M14).

    Modifies the content_outline in-place and returns it. For A2+ or M15+,
    returns the outline unchanged. This ensures Gemini sees bilingual titles
    in the plan and produces bilingual headers in its output.
    """
    base = track.split("-")[0]
    if base != "a1" or module_num > 14:
        return content_outline

    for section in content_outline:
        if not isinstance(section, dict) or "section" not in section:
            continue
        title = section["section"]
        # Already bilingual (contains " — " with Latin chars after)?
        if " — " in title and any(c.isascii() and c.isalpha() for c in title.split(" — ", 1)[1]):
            continue
        # Exact match
        if title in _BILINGUAL_TITLES:
            section["section"] = _BILINGUAL_TITLES[title]
            continue
        # Prefix match: "Голосні — И, І, О" → "Голосні — Vowels: И, І, О"
        for ukr_prefix, eng_equiv in _BILINGUAL_PREFIXES.items():
            if title.startswith(ukr_prefix):
                rest = title[len(ukr_prefix):]
                if rest.startswith(" — "):
                    section["section"] = f"{ukr_prefix} — {eng_equiv}: {rest[3:]}"
                else:
                    section["section"] = f"{ukr_prefix} — {eng_equiv}{rest}"
                break

    return content_outline


def get_pedagogical_constraints(track: str, module_num: int, plan: dict | None = None) -> str:
    """Build pedagogical constraints from the plan's phase field.

    Constraints are derived from:
    1. Plan's `phase` field (e.g., "A1.1 [First Contact]") → grammar/imperative bans
    2. Plan's `grammar` field → what this module teaches (used for context)

    Only A1 has phase-specific constraints. A2+ use LEVEL_CONSTRAINTS only.
    """
    base = track.split("-")[0]
    if base != "a1":
        return ""

    if not plan:
        return ""

    # Extract phase key from plan (e.g., "A1.1 [First Contact]" → "A1.1")
    phase_str = plan.get("phase", "")
    phase_key = phase_str.split("[")[0].strip() if phase_str else ""

    phase_constraint = _A1_PHASE_CONSTRAINTS.get(phase_key, "")
    if not phase_constraint:
        # Fallback: if phase not recognized, use imperative ban for safety
        phase_constraint = _IMPERATIVE_BAN

    return phase_constraint


# ---------------------------------------------------------------------------
# Decodable vocabulary removed in #841 — plan's vocabulary_hints is source of truth.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Level-aware structural rules for content phase
# ---------------------------------------------------------------------------


def _build_exact_section_titles(ctx) -> str:
    """Build an explicit list of required H2 section titles from the content outline."""
    if not ctx.content_outline:
        return ""
    titles = []
    for section in ctx.content_outline:
        name = section.get("section") or section.get("title", "")
        words = section.get("words", 0)
        if name:
            titles.append(f"- `## {name}` (~{words} words)")
    if not titles:
        return ""
    return (
        "## REQUIRED H2 Sections (use EXACT titles)\n\n"
        "Your output MUST use these EXACT H2 headings — do NOT rephrase, translate differently, "
        "or add creative subtitles. The audit will reject any section with a different title.\n\n"
        + "\n".join(titles)
    )


def _get_checkpoint_guidance(ctx) -> str:
    """Return checkpoint-specific guidance if the module is a checkpoint."""
    if not _is_checkpoint_module(ctx.slug):
        return ""
    return textwrap.dedent("""\
        ## Checkpoint Module Guidance

        This is a CHECKPOINT (review/consolidation) module, NOT a teaching module.

        **Structure differences from regular modules:**
        - Do NOT introduce new grammar or vocabulary
        - REVIEW and consolidate concepts from the preceding phase
        - Use INTEGRATION exercises that combine skills from multiple prior modules
        - Include a self-assessment section where students can gauge their progress
        - Focus on PRACTICE, not explanation — students already learned the concepts
        - Activities should test recall and application, not introduce new patterns
        - Include a "What you should know by now" summary of prior module objectives
        - Feel like a CELEBRATION of progress, not a test
    """)


def _get_checkpoint_review_guidance(ctx) -> str:
    """Return checkpoint-specific review criteria for the D1 review template."""
    if not _is_checkpoint_module(ctx.slug):
        return ""
    return textwrap.dedent("""\
        ## Checkpoint-Specific Review Criteria

        **This module is a CHECKPOINT — apply different review standards:**

        ### What to Check (checkpoint-specific)

        1. **No new material introduced**: The checkpoint should NOT teach new grammar rules or introduce
           new vocabulary. All content should review/synthesize material from prior modules. Flag any
           new grammar explanation or unfamiliar vocabulary as **HIGH** severity.

        2. **Integration quality**: Each section should combine skills from 2+ prior modules, not just
           review them in isolation. Flag sections that only drill a single skill as **MEDIUM**.

        3. **Synthesis over explanation**: Brief reminders (1-2 sentences) are fine, but full
           re-explanations of grammar rules are wrong for a checkpoint. Flag lengthy re-teaching
           as **MEDIUM**.

        4. **Celebratory tone**: The checkpoint should feel encouraging and confidence-building,
           not like a test. Flag harsh or exam-like framing as **LOW**.

        5. **Self-assessment**: The module should help learners identify their own gaps.
           Flag missing self-assessment elements as **MEDIUM**.

        6. **Activity integration**: Activities should combine multiple skills per activity,
           not test isolated grammar points. Flag single-skill activities as **MEDIUM**.

        ### What NOT to Penalize (checkpoint exceptions)

        - Lower information density (checkpoints review, not teach)
        - Fewer new example patterns (they reuse from prior modules)
        - Simpler explanations (brief reminders are appropriate)
        - Repetition of vocabulary from prior modules (this is the POINT)
    """)


def _get_writing_tone(track: str, module_num: int) -> str:
    """Return level-appropriate tone/verbosity instruction for content phase."""
    base = track.split("-")[0]
    if base == "a1" and module_num <= 4:
        return (
            "Be concise — students know nothing yet. Short, clear explanations. "
            "Every H3 gets {H3_WORD_RANGE} words. The activities do the teaching, not the prose. "
            "Do NOT pad with adjectives, motivational filler, or over-explained phonetics."
        )
    if base == "a1":
        return (
            "Keep explanations clear and direct. Every H3 gets {H3_WORD_RANGE} words. "
            "Avoid verbose prose — students are beginners. Focus on practical examples over theory."
        )
    if base == "a2":
        return (
            "Write clear, practical prose. Every H3 gets {H3_WORD_RANGE} words. "
            "Focus on examples and usage patterns. Avoid unnecessary theory or padding."
        )
    return (
        "Every concept gets dedicated depth. Every H3 gets {H3_WORD_RANGE} words. "
        "This is how you hit the target."
    )


def _get_writing_style(ctx) -> str:
    """Return phase-appropriate writing style instructions.

    A1.1 (alphabet/phonology): letter-by-letter instruction, no dialogues, no verbs.
    A1.2+ (grammar modules): DISCOVER-UNDERSTAND-PRACTICE with dialogues.
    """
    phase_str = ctx.plan.get("phase", "") if ctx.plan else ""
    phase_key = phase_str.split("[")[0].strip() if phase_str else ""

    if phase_key == "A1.1":
        return textwrap.dedent("""\
            ### Writing Style (Alphabet / Phonology Module)

            You're writing for someone seeing Ukrainian for the first time. English explains; Ukrainian is what they're learning.

            Follow the structural containment rules above. Each H2 section MUST follow this sequence:

            1. **EXPLAIN** — English paragraph introducing the concept (with Ukrainian letters/words bolded inline)
            2. **SHOW** — A table, chart, or bulleted example list demonstrating the letters/sounds
            3. **REINFORCE** — A callout box (tip, warning, culture note, or fun fact)

            **This is an alphabet/phonology module — NOT a grammar module.** There are no grammar patterns to discover. Do NOT write dialogues. Do NOT use the DISCOVER-UNDERSTAND-PRACTICE pattern. Focus on:
            - Letter shapes and their sounds
            - False friends (letters that look like English but sound different)
            - Blending letters into syllables, syllables into words
            - Reading practice with decodable words

            **FORBIDDEN patterns (HARD FAIL):**
            - Dialogues (verbs are banned in this phase — dialogues need verbs)
            - Starting a section with Ukrainian sentences (start with English explanation)
            - Bulleted example lists longer than 8 items
            - Abstract phonetic descriptions (use comparisons to English sounds instead)""")

    # Default: grammar modules (A1.2+)
    return textwrap.dedent("""\
        ### Writing Style

        You're writing for an A1 learner progressing through a structured course. They already know previous modules' content. English scaffolds new grammar; Ukrainian is what they're learning and practicing.

        Follow the structural containment rules above. Each H2 section MUST follow this sequence:

        1. **DISCOVER** — Start with a Ukrainian dialogue or example set that demonstrates the pattern. NO English explanation yet. Let the learner notice the pattern themselves. Use a blockquote dialogue (4-8 lines) or a set of contrastive pairs in a table.
        2. **UNDERSTAND** — Now explain the pattern in 1-2 English sentences MAX. Use a paradigm table to show the system.
        3. **PRACTICE** — A second, different dialogue or scenario using the same pattern in a new context. End the section with a callout box (tip, warning, culture note, or fun fact).

        **FORBIDDEN patterns (HARD FAIL):**
        - Starting a section with an English grammar explanation (must start with Ukrainian examples)
        - Bulleted example lists longer than 5 items (spam — use a dialogue or table instead)
        - Robotic dialogues where one speaker just echoes the other ("Читай!" / "Я читаю." repeated)
        - Listing random permutations of the same verb forms as separate bullets

        ### Dialogue Quality (CRITICAL)

        Every blockquote dialogue MUST:
        1. **Start with a location header**: `> **(На уроці / In the classroom)**` — this is MANDATORY, not optional
        2. **Have a purpose** — why are they talking? (asking for help, giving directions, learning)
        3. **Have varied responses** — the second speaker reacts naturally, not just echoes the command

        **BAD** (echo drill — HARD FAIL, produces zero learning):
        > — Читай!
        > — Я читаю.
        > — Пиши!
        > — Я пишу.

        Why this fails: it's a verb conjugation table disguised as a dialogue. No situation, no purpose, no natural speech.

        **GOOD** (classroom — teacher gives instructions, student responds naturally):
        > **(На уроці / In the classroom)**
        > — Читайте тут. Дивіться!
        > — Добре. А це?
        > — Ні, не це. Слухайте!
        > — Так, я слухаю.

        **Key pattern**: Each speaker has a GOAL. One asks/commands, the other REACTS (agrees, questions, redirects) — never just echoes the verb back.

        Limit to **2-3 dialogues per module** (not 9). Each in a DIFFERENT situation. Dialogues should make the learner think "I could use this in real life." """)


def get_structural_rules(track: str, module_num: int) -> str:
    """Return level-appropriate content structure rules for content phase.

    Early A1 cannot meet B1+ structural depth expectations (80-100 words per H3,
    4-part concept blocks, 5+ format variety). This function returns rules
    calibrated to the student's level.
    """
    base = track.split("-")[0]

    if base == "a1" and module_num <= 4:
        return (
            "### Rule 1: Every Letter/Concept Gets Its Own Section\n\n"
            "Each new letter or concept MUST get its own `### H3` subsection. "
            "Letter modules are presentation-heavy (video embeds, stroke order, examples) "
            "so depth comes from variety of examples, not paragraphs of explanation.\n\n"
            "### Rule 2: Introduce → Show → Practice\n\n"
            "Each H3 block follows this pattern:\n"
            "1. **Introduce** the letter/concept (1-2 sentences)\n"
            "2. **Show** it in words and context (examples, video embed)\n"
            "3. **Practice tip** (what to listen for, what to try)\n\n"
            "Minimum **30-50 words per H3 block**. Quality over quantity at this stage.\n\n"
            "### Rule 3: Presentation Consistency\n\n"
            "All letters in a group: SAME format, SAME depth (±30%), SAME example count (±1).\n\n"
            "### Rule 4: Example Variety\n\n"
            "No minimum format variety requirement for M1-M4 (letter-focused modules). "
            "Use whatever format best teaches the letter: word lists, audio examples, "
            "comparison pairs."
        )
    elif base == "a1" and module_num <= 14:
        return (
            "### Rule 1: Every Concept Gets Dedicated Depth\n\n"
            "Each concept MUST get its own `### H3` subsection with dedicated depth. "
            "Closely related items (e.g., masculine/feminine/neuter endings) MAY share one H3.\n\n"
            "### Rule 2: Introduce → Examples → Practice Tip\n\n"
            "Each H3 concept block MUST contain:\n"
            "1. **Introduction/explanation** (1-2 sentences)\n"
            "2. **2+ example words or phrases** in context\n"
            "3. **Practice tip** — how to remember or use this\n\n"
            "Minimum **40-60 words per H3 block**.\n\n"
            "### Rule 3: Presentation Consistency\n\n"
            "All items in a category: SAME format, SAME depth (±25%), SAME example count (±1).\n\n"
            "### Rule 4: Example Variety\n\n"
            "Use at least **3 different formats** across the module: "
            "word lists, tables, inline examples, callout boxes."
        )
    elif base == "a1":  # M15+
        return (
            "### Rule 1: Every Concept Gets Dedicated Depth\n\n"
            "Each concept MUST get its own `### H3` subsection. "
            "Closely related items MAY share one H3 with equal coverage.\n\n"
            "### Rule 2: Depth Over Compression\n\n"
            "Each H3 concept block MUST contain:\n"
            "1. **Definition/explanation** (1-2 sentences)\n"
            "2. **How it works** (formation rules, patterns)\n"
            "3. **2+ example sentences** in context\n"
            "4. **Usage note** — when/why a speaker uses this form\n\n"
            "Minimum **60-80 words per H3 block**.\n\n"
            "### Rule 3: Presentation Consistency\n\n"
            "All items in a category: SAME format, SAME depth (±20%), SAME example count (±1).\n\n"
            "### Rule 4: Example Variety\n\n"
            "FORBIDDEN: 5+ consecutive examples in the same format. "
            "Use at least **3 different formats**: standalone examples, comparison tables, "
            "inline examples, mini-dialogues, callout boxes."
        )
    elif base == "a2":
        return (
            "### Rule 1: Every Concept Gets Dedicated Depth\n\n"
            "Each concept MUST get its own `### H3` subsection. "
            "Closely related items MAY share one H3 with equal coverage.\n\n"
            "### Rule 2: Depth Over Compression\n\n"
            "Each H3 concept block MUST contain ALL of these:\n"
            "1. **Definition/explanation** (2+ sentences)\n"
            "2. **How it works** (formation rules, patterns, grammatical function)\n"
            "3. **2+ example sentences** in context (not isolated words)\n"
            "4. **Usage note** — when/why a speaker uses this form\n\n"
            "Minimum **60-80 words per H3 block**. A 20-word table row is NOT a lesson.\n\n"
            "### Rule 3: Presentation Consistency\n\n"
            "All items in a category: SAME format, SAME depth (±20%), SAME example count (±1).\n\n"
            "### Rule 4: Example Variety\n\n"
            "FORBIDDEN: 5+ consecutive examples in the same format. Mix at least **4 different formats** "
            "across sections: standalone examples, comparison tables, inline examples, "
            "mini-dialogues, callout boxes."
        )
    else:
        # B1+ — full structural rules (moved from hardcoded template)
        return (
            "### Rule 1: Every Concept Gets Dedicated Depth (CRITICAL — #1 word count lever)\n\n"
            "When an H2 section teaches multiple items in a category, each item (or logical group "
            "of closely related items) MUST get its own `### H3` subsection with dedicated depth.\n\n"
            "**Grouping rule:** Closely related items that form a single system (e.g., "
            "masculine/feminine/neuter endings of the same paradigm) MAY share one H3 — but that "
            "H3 must then cover ALL items with equal depth. Independent concepts MUST get separate H3s.\n\n"
            "**Count the items from the plan/outline.** Each concept without dedicated depth = ~100 missing words.\n\n"
            "### Rule 2: Depth Over Compression\n\n"
            "Each H3 concept block MUST contain ALL of these:\n\n"
            "1. **Definition/explanation** (2+ sentences)\n"
            "2. **How it works** (formation rules, patterns, grammatical function)\n"
            "3. **2+ example sentences** in context (not isolated words)\n"
            "4. **Usage note** — when/why a speaker uses this form\n\n"
            "Minimum **80-100 words per H3 block**. A 20-word table row is NOT a lesson.\n\n"
            "### Rule 3: Presentation Consistency\n\n"
            "All items in a category: SAME format, SAME depth (±20%), SAME example count (±1).\n\n"
            "❌ Item A gets 150 words, Item B gets 40 words for equal-weight concepts\n"
            "✅ All items follow identical pattern: definition → formation → examples → usage note\n\n"
            "### Rule 4: Example Variety\n\n"
            "FORBIDDEN: 5+ consecutive examples in the same format (bullet lists, `_Приклад:_` blocks, "
            "`**Ukrainian.** (English.)` lines — any uniform pattern). Mix these formats across sections:\n"
            "- Standalone examples with context (max 3-4 consecutive in one format)\n"
            "- **Comparison tables** (paradigms, aspect pairs, case usage)\n"
            "- Inline examples woven into prose\n"
            "- **Mini-dialogues** showing real usage\n"
            "- Callout boxes with examples\n\n"
            "**Anti-batching rule**: If you notice 3+ sections each presenting examples as identical "
            "bullet lists, STOP and vary the format. Use a table in one section, inline examples in "
            "another, a dialogue in a third."
        )


def get_h3_word_range(track: str, module_num: int) -> str:
    """Return the H3 word range string for the content template."""
    base = track.split("-")[0]
    if base == "a1" and module_num <= 4:
        return "30-50"
    elif base == "a1" and module_num <= 14:
        return "40-60"
    elif base == "a1" or base == "a2":
        return "60-80"
    else:
        return "80-100+"


def get_expansion_method(track: str, module_num: int) -> str:
    """Return level-appropriate expansion guidance for content phase."""
    base = track.split("-")[0]
    if base == "a1" and module_num <= 4:
        return (
            "**Don't pad — add teaching value.** For EVERY letter you introduce:\n\n"
            "1. **Show it** (uppercase + lowercase, with video embed)\n"
            "2. **Give 2-3 example words** the student can decode\n"
            "3. **Add a practice tip** (what to listen for, mouth position)\n"
            "4. **Connect to something familiar** (English sound comparison)\n\n"
            "**If a section is still under target:** Add more example words, "
            "a `[!tip]` with pronunciation advice, or a comparison between similar-sounding letters."
        )
    elif base == "a1" and module_num <= 14:
        return (
            "**Don't just write more — write deeper.** For EVERY concept:\n\n"
            "1. **Introduce it** (1-2 sentences)\n"
            "2. **Give 2+ examples** with English translations\n"
            "3. **Add a practice tip** or memory aid\n"
            "4. **Connect to real life** (when would a learner encounter this?)\n\n"
            "**If a section is still under target:** Add a `[!tip]` with a common mistake, "
            "a comparison table, or more example words with translations."
        )
    elif base in ("a1", "a2"):
        return (
            "**Don't just write more — write deeper.** For EVERY concept:\n\n"
            "1. **Define it** (1-2 sentences explaining what it is)\n"
            "2. **Show how it works** (pattern, rule, formation)\n"
            "3. **Give 2+ examples** in full sentences with context\n"
            "4. **Add a comparison** (table, before/after, correct vs incorrect)\n"
            "5. **Connect to real life** (when would a Ukrainian speaker use this?)\n\n"
            "**If a section is still under target:** Add a `[!warning]` with a common mistake, "
            "a `[!culture]` connecting to Ukrainian culture, or a mini-dialogue."
        )
    else:
        # B1+ — full expansion method (moved from hardcoded template)
        return (
            "**Don't just write more — write deeper.** For EVERY concept you introduce:\n\n"
            "1. **Define it** (2+ sentences explaining what it is)\n"
            "2. **Show how it works** (pattern, rule, formation)\n"
            "3. **Give 2+ examples** in full sentences with context\n"
            "4. **Add a comparison** (table, before/after, correct vs incorrect)\n"
            "5. **Connect to real life** (when would a Ukrainian speaker use this?)\n\n"
            "**If a section is still under its Write Minimum after this, add:**\n"
            "- A `[!warning]` with a common mistake and correct alternative\n"
            "- A `[!culture]` or `[!quote]` connecting to Ukrainian culture\n"
            "- A mini-dialogue showing the concept in conversation\n"
            "- A comparison table or mermaid flowchart\n\n"
            "**The math:** If your H2 teaches 5 concepts × 100 words each = 500 words. "
            "Add an intro paragraph (50w) + 2 callouts (60w each) + a comparison table (80w) "
            "= **750 words** for that section. This is how you hit big targets."
        )


ACTIVITY_CONFIGS: dict[str, dict[str, str]] = {
    "a1": {
        "ACTIVITY_COUNT_TARGET": "10", "ACTIVITY_MIN": "8", "ACTIVITY_MAX": "15", "ITEMS_MIN": "6",
        "VOCAB_COUNT_TARGET": "20",
        "FORBIDDEN_ACTIVITY_TYPES": "cloze, error-correction, mark-the-words, select, translate, essay-response, critical-analysis, comparative-study, authorial-intent",
        "ALLOWED_ACTIVITY_TYPES": "quiz, true-false, fill-in, match-up, anagram, unjumble, group-sort, watch-and-repeat, classify, image-to-letter",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "fill-in, match-up, anagram, unjumble, quiz, true-false, classify, image-to-letter, watch-and-repeat",
    },
    "a2": {
        "ACTIVITY_COUNT_TARGET": "12", "ACTIVITY_MIN": "10", "ACTIVITY_MAX": "15", "ITEMS_MIN": "8",
        "VOCAB_COUNT_TARGET": "25",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, essay-response, critical-analysis, comparative-study, authorial-intent",
        "ALLOWED_ACTIVITY_TYPES": "quiz, true-false, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction, group-sort, watch-and-repeat, classify, image-to-letter",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "error-correction, unjumble, fill-in, classify, watch-and-repeat",
    },
    "b1-bridge": {
        "ACTIVITY_COUNT_TARGET": "6", "ACTIVITY_MIN": "4", "ACTIVITY_MAX": "10", "ITEMS_MIN": "6",
        "VOCAB_COUNT_TARGET": "25",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, comparative-study, authorial-intent",
        "ALLOWED_ACTIVITY_TYPES": "quiz, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction, essay-response, critical-analysis",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "quiz, match-up, fill-in, error-correction, mark-the-words",
    },
    "b1-core": {
        "ACTIVITY_COUNT_TARGET": "10", "ACTIVITY_MIN": "8", "ACTIVITY_MAX": "15", "ITEMS_MIN": "12",
        "VOCAB_COUNT_TARGET": "30",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, essay-response, critical-analysis, comparative-study, authorial-intent",
        "ALLOWED_ACTIVITY_TYPES": "quiz, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "fill-in, unjumble, error-correction",
    },
    "b2": {
        "ACTIVITY_COUNT_TARGET": "12", "ACTIVITY_MIN": "10", "ACTIVITY_MAX": "15", "ITEMS_MIN": "14",
        "VOCAB_COUNT_TARGET": "30",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram",
        "ALLOWED_ACTIVITY_TYPES": "quiz, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction, group-sort, select, translate",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "fill-in, unjumble, error-correction",
    },
    "c1-core": {
        "ACTIVITY_COUNT_TARGET": "14", "ACTIVITY_MIN": "12", "ACTIVITY_MAX": "18", "ITEMS_MIN": "12",
        "VOCAB_COUNT_TARGET": "30",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram",
        "ALLOWED_ACTIVITY_TYPES": "quiz, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction, group-sort, select, translate",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "fill-in, unjumble, error-correction",
    },
    "c2": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "30",
        "FORBIDDEN_ACTIVITY_TYPES": "",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, quiz, true-false",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "reading, essay-response, critical-analysis",
    },
    "hist": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "25",
        "FORBIDDEN_ACTIVITY_TYPES": "quiz, fill-in, cloze, match-up, error-correction, unjumble, mark-the-words, group-sort, select, translate, anagram",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, true-false",
        "REQUIRED_TYPES": "reading, essay-response", "PRIORITY_TYPES": "reading, essay-response, critical-analysis, comparative-study",
    },
    "bio": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "30",
        "FORBIDDEN_ACTIVITY_TYPES": "quiz, match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words, error-correction, select, translate",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, authorial-intent, true-false",
        "REQUIRED_TYPES": "reading, essay-response, critical-analysis",
        "PRIORITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, authorial-intent",
    },
    "istorio": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "30",
        "FORBIDDEN_ACTIVITY_TYPES": "quiz, match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words, error-correction, select, translate",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, true-false",
        "REQUIRED_TYPES": "reading, essay-response, critical-analysis",
        "PRIORITY_TYPES": "reading, essay-response, critical-analysis, comparative-study",
    },
    "lit": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "0",
        "FORBIDDEN_ACTIVITY_TYPES": "quiz, match-up, fill-in, unjumble, anagram, cloze, mark-the-words",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, authorial-intent, true-false",
        "REQUIRED_TYPES": "reading, essay-response, critical-analysis",
        "PRIORITY_TYPES": "reading, essay-response, critical-analysis, comparative-study",
    },
    "b2-pro": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "35",
        "FORBIDDEN_ACTIVITY_TYPES": "",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, quiz, true-false",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "reading, essay-response, critical-analysis",
    },
    "c1-pro": {
        "ACTIVITY_COUNT_TARGET": "5", "ACTIVITY_MIN": "3", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "40",
        "FORBIDDEN_ACTIVITY_TYPES": "",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, comparative-study, quiz, true-false",
        "REQUIRED_TYPES": "", "PRIORITY_TYPES": "reading, essay-response, critical-analysis",
    },
    "oes": {
        "ACTIVITY_COUNT_TARGET": "7", "ACTIVITY_MIN": "6", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "35",
        "FORBIDDEN_ACTIVITY_TYPES": "quiz, match-up, fill-in, unjumble, anagram, cloze, mark-the-words, group-sort, select, translate",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, etymology-trace, transcription, grammar-identify, phonology-lab, grammar-lab, parallel-text, paleography-analysis, historical-writing, loanword-trace",
        "REQUIRED_TYPES": "transcription, etymology-trace, grammar-identify",
        "PRIORITY_TYPES": "reading, essay-response, critical-analysis, etymology-trace, transcription, grammar-identify, phonology-lab, grammar-lab, parallel-text, paleography-analysis, historical-writing, loanword-trace",
    },
    "ruth": {
        "ACTIVITY_COUNT_TARGET": "7", "ACTIVITY_MIN": "6", "ACTIVITY_MAX": "9", "ITEMS_MIN": "1",
        "VOCAB_COUNT_TARGET": "35",
        "FORBIDDEN_ACTIVITY_TYPES": "quiz, match-up, fill-in, unjumble, anagram, cloze, mark-the-words, group-sort, select, translate",
        "ALLOWED_ACTIVITY_TYPES": "reading, essay-response, critical-analysis, transcription, etymology-trace, grammar-identify, grammar-lab, parallel-text, paleography-analysis, historical-writing, register-identify, loanword-trace, comparative-style",
        "REQUIRED_TYPES": "transcription, etymology-trace, grammar-identify",
        "PRIORITY_TYPES": "reading, essay-response, critical-analysis, transcription, etymology-trace, grammar-identify, grammar-lab, parallel-text, paleography-analysis, historical-writing, register-identify, loanword-trace, comparative-style",
    },
}


# ============================================================================
# 2. Resolver Functions
# ============================================================================

def get_track_skill(track: str, module_num: int) -> tuple[str, str, str]:
    """Return (skill_file, skill_identity, persona_flavor) for a track + module number."""
    if track == "b1":
        key = "b1-early" if module_num <= 5 else "b1-late"
        return TRACK_SKILLS[key]
    if track.startswith("lit-"):
        return TRACK_SKILLS["lit"]
    if track in TRACK_SKILLS:
        return TRACK_SKILLS[track]
    return TRACK_SKILLS["b2"]


def get_immersion_rule(track: str, module_num: int) -> str:
    """Compute immersion rule from track + module number."""
    base = track.split("-")[0] if track not in ("hist", "bio", "istorio", "b2-pro", "c1-pro") else track
    if base == "a1":
        if module_num <= 2:
            return IMMERSION_RULES["a1-m01-02"]
        elif module_num <= 5:
            return IMMERSION_RULES["a1-m03-05"]
        elif module_num <= 10:
            return IMMERSION_RULES["a1-m06-10"]
        elif module_num <= 20:
            return IMMERSION_RULES["a1-m11-20"]
        else:
            return IMMERSION_RULES["a1-m21+"]
    elif base == "a2":
        if module_num <= 20:
            return IMMERSION_RULES["a2-m01-20"]
        elif module_num <= 50:
            return IMMERSION_RULES["a2-m21-50"]
        else:
            return IMMERSION_RULES["a2-m51-70"]
    elif base == "b1":
        if module_num <= 5:
            return IMMERSION_RULES["b1-bridge"]
        else:
            return IMMERSION_RULES["b1-core"]
    else:
        return IMMERSION_RULES["b2+"]


def get_level_constraints(track: str, plan: dict | None = None) -> str:
    """Get grammar constraint text for the base level.

    For A1, if the module's plan explicitly teaches a banned grammar construct
    (e.g. Dative case), the corresponding ban is relaxed automatically.
    """
    base = track.split("-")[0]
    constraints = LEVEL_CONSTRAINTS.get(base, LEVEL_CONSTRAINTS["c1"])

    if base == "a1" and plan:
        grammar_list = plan.get("grammar", [])
        if grammar_list:
            # Filter out negative instructions ("do NOT teach", "avoid") before matching
            grammar_text = " ".join(
                str(g).lower() for g in grammar_list
                if not any(neg in str(g).lower() for neg in ("do not", "don't", "avoid", "не ", "заборон"))
            )
            relaxations: list[str] = []

            if any(kw in grammar_text for kw in ("dative", "давальн", "мені подобається")):
                relaxations.append("Dative case (plan teaches it)")
            if any(kw in grammar_text for kw in ("instrumental", "орудн", "з другом")):
                relaxations.append("Instrumental case (plan teaches it)")
            if any(kw in grammar_text for kw in ("subordinate", "підрядн", "який", "що-clause",
                                                   "коли", "якщо", "тому що", "бо", "щоб")):
                relaxations.append("Subordinate clauses (plan teaches them)")
            if any(kw in grammar_text for kw in ("perfective", "доконан", "imperative", "наказов",
                                                   "сказати", "показати", "допомогти", "взяти")):
                relaxations.append("Perfective aspect (plan teaches perfective verbs)")

            if relaxations:
                relaxed_list = ", ".join(relaxations)
                constraints += (
                    f"\n\nPLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module "
                    f"because the plan explicitly teaches these constructs: {relaxed_list}. "
                    "Exception: If a grammar construct appears in this module's plan grammar list "
                    "or objectives, it is ALLOWED for this module."
                )

    return constraints


def get_activity_config(track: str, module_num: int) -> dict[str, str]:
    """Get activity configuration for a track + module number."""
    if track.startswith("lit-"):
        return ACTIVITY_CONFIGS["lit"]
    if track == "b1":
        return ACTIVITY_CONFIGS["b1-bridge" if module_num <= 5 else "b1-core"]
    if track == "c1":
        return ACTIVITY_CONFIGS["c1-core"]
    if track in ACTIVITY_CONFIGS:
        return ACTIVITY_CONFIGS[track]
    return ACTIVITY_CONFIGS["b2"]


def get_item_minimums_table(track: str, module_num: int) -> str:
    """Build a markdown table of per-type item minimums from audit config."""
    try:
        from audit.config import ACTIVITY_COMPLEXITY
    except ImportError:
        return "*(Item minimums table unavailable)*"

    config = get_activity_config(track, module_num)
    allowed = [t.strip() for t in config.get("ALLOWED_ACTIVITY_TYPES", "").split(",") if t.strip()]
    if not allowed:
        return "*(No allowed activity types)*"

    # Resolve the audit config level key
    _TRACK_TO_AUDIT = {
        "hist": "history", "bio": "B2-biography", "istorio": "istorio",
        "lit": "lit", "oes": "C2", "ruth": "C2",
        "b2-pro": "B2", "c1-pro": "C1",
    }
    level_key = _TRACK_TO_AUDIT.get(track, track.upper().replace("-BRIDGE", "").replace("-CORE", ""))
    if track == "b1" and module_num <= 5:
        level_key = "B1"

    rows = []
    for atype in allowed:
        if atype not in ACTIVITY_COMPLEXITY:
            continue
        rules = ACTIVITY_COMPLEXITY[atype].get(level_key) or ACTIVITY_COMPLEXITY[atype].get(track)
        if not rules:
            # Try base level (A1, B1, etc.)
            base = track.split("-")[0].upper()
            rules = ACTIVITY_COMPLEXITY[atype].get(base, {})
        min_items = rules.get("min_items", rules.get("pairs_min", rules.get("items_min", "")))
        if min_items:
            unit = "pairs" if atype == "match-up" else "items"
            rows.append(f"| {atype} | ≥{min_items} {unit} |")

    if not rows:
        return "*(No per-type minimums defined)*"
    return "| Type | Minimum |\n|------|--------|\n" + "\n".join(rows)


def get_level_label(track: str) -> str:
    """Get human-readable level label (e.g., 'A1', 'BIO')."""
    return track.upper().replace("-", "_").rstrip("_")


_TRACK_FOCUS_MAP: dict[str, tuple[str, str | None]] = {
    "hist": ("B2", "history"),
    "bio": ("C1", "biography"),
    "istorio": ("C1", "history"),
    "b2-pro": ("B2", "professional"),
    "c1-pro": ("C1", "professional"),
    "lit": ("C1", "literature"),
    "oes": ("C2", "seminar"),
    "ruth": ("C2", "seminar"),
}


def track_to_level_focus(track: str) -> tuple[str, str | None]:
    """Map track name to (level_code, module_focus) for config resolution."""
    if track.startswith("lit-"):
        return ("C1", "literature")
    if track in _TRACK_FOCUS_MAP:
        return _TRACK_FOCUS_MAP[track]
    return (track.upper().split("-")[0], None)


# ============================================================================
# 3. ModuleContext Dataclass
# ============================================================================

@dataclass
class ModuleContext:
    """All paths, config, state for a module build."""
    track: str
    module_num: int
    slug: str
    mode: str  # "v5" (current) | DEPRECATED: "full", "content-only", "enrich", "e2e", "v3"

    # Paths (populated by preflight)
    paths: dict[str, Path] = field(default_factory=dict)
    orch_dir: Path = field(default=Path("."))

    # Plan data
    plan: dict = field(default_factory=dict)
    word_target: int = 0
    topic_title: str = ""
    content_outline: list[dict] = field(default_factory=list)

    # Config from tables
    skill_name: str = ""
    skill_identity: str = ""
    persona_flavor: str = ""
    immersion_rule: str = ""
    level_constraints: str = ""
    activity_config: dict[str, str] = field(default_factory=dict)
    model: str = PRO_MODEL

    # Track config from batch_gemini_config
    track_config: dict = field(default_factory=dict)

    # State tracking
    state: dict = field(default_factory=dict)
    state_path: Path = field(default=Path("."))

    # Built placeholders (in-memory, no YAML round-trip)
    placeholders: dict[str, str] = field(default_factory=dict)

    # CLI flags
    dry_run: bool = False
    force_phase: str | None = None
    rebuild: bool = False
    claude_review: bool = False


# ============================================================================
# 4. State Helpers
# ============================================================================

def _state_file(ctx: ModuleContext) -> Path:
    return ctx.orch_dir / "state.json"


def load_state(ctx: ModuleContext) -> dict:
    """Load state.json or return fresh state."""
    sf = _state_file(ctx)
    if sf.exists():
        try:
            return json.loads(sf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "slug": ctx.slug,
        "track": ctx.track,
        "module_num": ctx.module_num,
        "mode": ctx.mode,
        "phases": {},
        "last_updated": _now_iso(),
    }


def save_state(ctx: ModuleContext) -> None:
    """Persist state.json atomically."""
    if getattr(ctx, "mode", None) in ("v4", "v5"):
        return
    ctx.state["last_updated"] = _now_iso()
    tmp = _state_file(ctx).with_suffix(".tmp")
    tmp.write_text(json.dumps(ctx.state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.rename(_state_file(ctx))


def is_phase_complete(ctx: ModuleContext, phase: str) -> bool:
    """Check if a phase is marked complete in state."""
    if getattr(ctx, "mode", None) == "v5":
        return False
    if ctx.force_phase == phase:
        return False
    return ctx.state.get("phases", {}).get(phase, {}).get("status") == "complete"


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ============================================================================
# 5. Thread-safe Locks (from v2)
# ============================================================================

_HAS_FILELOCK = False
try:
    from filelock import FileLock
    _HAS_FILELOCK = True
except ImportError:
    warnings.warn(
        "filelock not installed — parallel 4a+4b will run sequentially. "
        "Install with: pip install filelock",
        stacklevel=1,
    )
    class FileLock:  # type: ignore[no-redef]
        def __init__(self, path: str | Path):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a: Any):
            pass

_state_lock: FileLock | None = None
_log_lock = threading.Lock()


def _init_state_lock(ctx: ModuleContext) -> None:
    """Create a file-based lock for thread-safe state writes."""
    global _state_lock
    lock_path = ctx.orch_dir / "state.json.lock"
    _state_lock = FileLock(str(lock_path))


# ============================================================================
# 6. mark_phase — Merged v1 base + v2 FileLock (always locks)
# ============================================================================

def mark_phase(ctx: ModuleContext, phase: str, status: str, **extra: Any) -> None:
    """Update phase status in state.json and persist (thread-safe via FileLock).

    Skips the file write in v4/v5 mode — they use their own state files.
    """
    if ctx.dry_run:
        return
    if getattr(ctx, "mode", None) in ("v4", "v5"):
        return
    lock = _state_lock or FileLock(str(ctx.orch_dir / "state.json.lock"))
    with lock:
        if "phases" not in ctx.state:
            ctx.state["phases"] = {}
        entry = {"status": status, "timestamp": _now_iso()}
        entry.update(extra)
        ctx.state["phases"][phase] = entry
        save_state(ctx)


# Backward-compat alias
mark_phase_locked = mark_phase


# ============================================================================
# 7. Logging (thread-safe, no string hacks)
# ============================================================================

_log_fh = None


def _init_log(slug: str) -> None:
    """Open a log file in logs/ for this build run."""
    global _log_fh
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"build-{slug}-{ts}.log"
    _log_fh = open(log_path, "a", encoding="utf-8")  # noqa: SIM115 — module-level log fd, closed at exit
    _log_fh.write(f"=== pipeline — {slug} — {ts} ===\n")
    print(f"Log: {log_path}", flush=True)


def log(msg: str) -> None:
    """Print to stdout and append to log file (thread-safe)."""
    with _log_lock:
        print(msg, flush=True)
        if _log_fh:
            _log_fh.write(msg + "\n")
            _log_fh.flush()


# ============================================================================
# 8. Phase Sequence + Artifact Cleanup
# ============================================================================

# BACKWARD-COMPAT: v2/v3 numbered phase IDs. Needed for cleaning old module artifacts.
PHASE_SEQUENCE = [
    "0", "0.5", "1", "2", "3", "4ab", "6", "6b", "5", "7", "8",
]


def _phase_state_ids(phase_id: str) -> list[str]:
    """Map v2 phase IDs to state.json phase IDs. BACKWARD-COMPAT."""
    if phase_id == "4ab":
        return ["3a", "3b"]
    if phase_id == "5":
        return ["5-enrich"]
    if phase_id == "7":
        return ["7-final"]
    return [phase_id]


# BACKWARD-COMPAT: v2/v3 artifact glob patterns. Maps old numbered phases to file patterns.
PHASE_ARTIFACT_PATTERNS: dict[str, list[str]] = {
    "0":    ["research-*", "phase-0-*"],
    "0.5":  ["discovery*", "phase-0-5-*"],
    "1":    ["phase-1-*"],
    "2":    ["content-*", "phase-2-*"],
    "3":    ["activities-*", "phase-3-*", "phase3-*", "phase-3a-*", "phase-3b-*"],
    "4ab":  ["validate-*", "phase-4a-*", "phase-4b-*", "phase4a-*", "phase4b-*", "phase-4-*"],
    "6":    ["review-*", "phase-6-*"],
    "6b":   ["phase-6b-*"],
    "5":    ["phase5-*", "phase-5-*"],
    "7":    ["final-review*", "phase7-*", "phase-7-*"],
    "8":    ["phase-8-*", "phase8-*"],
}


def _external_artifacts_for_phase(ctx: ModuleContext, phase_id: str) -> list[Path]:
    """Return paths to audit/review/status files produced by a phase."""
    slug = ctx.slug
    paths = ctx.paths
    result: list[Path] = []
    if phase_id in ("3", "5", "7"):
        audit_dir = paths["md"].parent / "audit"
        for ext in ["-audit.md", "-audit.log", "-grammar.yaml", "-quality.md"]:
            f = audit_dir / f"{slug}{ext}"
            if f.exists():
                result.append(f)
        status_f = paths["status"]
        if status_f.exists():
            result.append(status_f)
    if phase_id == "6":
        review_f = paths["review"]
        if review_f.exists():
            result.append(review_f)
    if phase_id == "8":
        completion = ctx.orch_dir / "completion.md"
        if completion.exists():
            result.append(completion)
        mdx_dir = PROJECT_ROOT / "starlight" / "src" / "content" / "docs" / ctx.track
        mdx_file = mdx_dir / f"{ctx.slug}.mdx"
        if mdx_file.exists():
            result.append(mdx_file)
    return result


def clean_phase_artifacts(ctx: ModuleContext, phase_id: str, forward: bool = False) -> int:
    """Delete orchestration artifacts for a phase (and all subsequent if forward=True)."""
    if forward:
        try:
            idx = PHASE_SEQUENCE.index(phase_id)
        except ValueError:
            idx = 0
        phases_to_clean = PHASE_SEQUENCE[idx:]
    else:
        phases_to_clean = [phase_id]

    deleted = 0
    orch_dir = ctx.orch_dir
    for pid in phases_to_clean:
        patterns = PHASE_ARTIFACT_PATTERNS.get(pid, [])
        for pattern in patterns:
            for f in orch_dir.glob(pattern):
                f.unlink()
                deleted += 1
        for f in _external_artifacts_for_phase(ctx, pid):
            f.unlink()
            deleted += 1
        if "phases" in ctx.state and pid in ctx.state["phases"]:
            del ctx.state["phases"][pid]
        for state_id in _phase_state_ids(pid):
            if "phases" in ctx.state and state_id in ctx.state["phases"]:
                del ctx.state["phases"][state_id]

    if deleted > 0:
        save_state(ctx)
    return deleted


# ============================================================================
# 9. Gemini Dispatch Helpers
# ============================================================================

TMP_DIR = Path(tempfile.gettempdir())
MAX_FIX_ITERATIONS = 3


def run_script(args: list[str], capture: bool = False, timeout: int = 600) -> subprocess.CompletedProcess:
    """Run a script via .venv/bin/python with cwd=PROJECT_ROOT."""
    cmd = [VENV_PYTHON, *args]
    return subprocess.run(
        cmd, cwd=str(PROJECT_ROOT), capture_output=capture,
        text=True, timeout=timeout,
    )


def _run_with_heartbeat(
    cmd: list[str], label: str, timeout: int = 1800,
    heartbeat_interval: int = 30, **kwargs,
) -> subprocess.CompletedProcess:
    """Run a subprocess with periodic heartbeat logging."""
    stop_event = threading.Event()
    t0 = time.time()

    def _heartbeat():
        while not stop_event.wait(heartbeat_interval):
            elapsed = int(time.time() - t0)
            m, s = divmod(elapsed, 60)
            print(f"    ⏳ {label} — {m}m {s:02d}s elapsed...", flush=True)

    thread = threading.Thread(target=_heartbeat, daemon=True)
    thread.start()
    try:
        result = subprocess.run(cmd, timeout=timeout, **kwargs)
        return result
    finally:
        stop_event.set()
        thread.join(timeout=2)


def dispatch_gemini_raw(
    prompt: str, task_id: str, model: str = PRO_MODEL,
    stdout_only: bool = False, allow_write: bool = False,
    output_file: Path | None = None, timeout: int = 1800,
    max_retries: int = 3,
) -> tuple[bool, str]:
    """Dispatch a prompt to Gemini via ai_agent_bridge (no rate-limit fallback).

    Retries up to max_retries times on transient network errors
    (TLS drops, socket resets, etc.) with exponential backoff.

    Returns (success, raw_output_text).
    """
    args = [
        str(SCRIPTS_DIR / "ai_agent_bridge/__main__.py"), "ask-gemini",
        "-",  # read prompt from stdin
        "--task-id", task_id,
        "--model", model,
    ]
    if stdout_only:
        args.append("--stdout-only")
    if allow_write:
        args.append("--allow-write")

    last_output = ""
    for attempt in range(1, max_retries + 1):
        try:
            result = _run_with_heartbeat(
                [VENV_PYTHON, *args],
                label=f"Gemini {task_id}",
                timeout=timeout,
                cwd=str(PROJECT_ROOT), capture_output=True, text=True,
                input=prompt,
            )
            output_text = result.stdout or ""
            last_output = output_text
            if result.returncode == 0:
                if output_file:
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text(output_text, encoding="utf-8")
                return True, output_text
            # Check if failure is a transient network error
            combined = f"{output_text}\n{result.stderr or ''}"
            if attempt < max_retries and _is_transient_error(combined):
                delay = 5 * (2 ** (attempt - 1))  # 5s, 10s
                log(f"  [retry] Transient network error on attempt {attempt}/{max_retries}, "
                    f"waiting {delay}s...")
                time.sleep(delay)
                continue
            # Non-transient failure or final attempt
            if output_file:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(output_text, encoding="utf-8")
            return False, output_text
        except subprocess.TimeoutExpired:
            log(f"  TIMEOUT: Gemini dispatch {task_id} exceeded {timeout}s")
            return False, ""

    # Exhausted retries
    return False, last_output


# ---------------------------------------------------------------------------
# Gemini session capture
# ---------------------------------------------------------------------------
_GEMINI_SESSION_DIR = Path.home() / ".gemini" / "tmp" / "learn-ukrainian" / "chats"


def save_gemini_session(dest: Path, label: str = "session") -> bool:
    """Copy the most recent gemini-cli session JSON to dest directory.

    Returns True if a session was found and copied.
    """
    if not _GEMINI_SESSION_DIR.exists():
        return False
    try:
        sessions = sorted(_GEMINI_SESSION_DIR.glob("session-*.json"), key=lambda p: p.stat().st_mtime)
        if not sessions:
            return False
        latest = sessions[-1]
        dest.mkdir(parents=True, exist_ok=True)
        target = dest / f"{label}-gemini-session.json"
        shutil.copy2(latest, target)
        return True
    except Exception:
        return False


# Rate limit / auth failure signatures in Gemini CLI output
_RATE_LIMIT_PATTERNS = [
    "Error authenticating",
    "FatalAuthenti",
    "RESOURCE_EXHAUSTED",
    "rate limit",
    "quota exceeded",
    "429",
]

# Transient network error signatures (TLS drops, socket resets)
_TRANSIENT_PATTERNS = [
    "premature close",
    "econnreset",
    "socket hang up",
    "fetch failed",
    "network error",
    "etimedout",
    "enotfound",
    "epipe",
    "connection reset",
]


def _is_rate_limited(output: str) -> bool:
    """Check if dispatch failed due to rate limiting or auth exhaustion."""
    lower = output.lower()
    return any(p.lower() in lower for p in _RATE_LIMIT_PATTERNS)


def _is_transient_error(output: str) -> bool:
    """Check if dispatch failed due to a transient network error."""
    lower = output.lower()
    return any(p in lower for p in _TRANSIENT_PATTERNS)


# ---------------------------------------------------------------------------
# Pre-dispatch prompt health check
# ---------------------------------------------------------------------------


def check_prompt_health(
    ctx: ModuleContext, prompt_text: str, phase_name: str
) -> list[str]:
    """Validate a filled prompt before dispatching to an LLM.

    Returns a list of issues found. Empty list = healthy prompt.
    Each issue is a string like "WARNING: ..." or "ERROR: ...".
    ERROR items should block dispatch; WARNING items are informational.
    """
    issues: list[str] = []
    track_base = ctx.track.split("-")[0] if ctx.track else ""
    is_core = track_base.lower() in {"a1", "a2", "b1", "b2", "c1", "c2"}

    # 1. Content-phase checks
    if phase_name == "content":
        if "{IMMERSION_RULE}" in prompt_text:
            issues.append("ERROR: IMMERSION_RULE placeholder was not filled")
        elif is_core:
            imm_rule = getattr(ctx, "immersion_rule", "")
            if not imm_rule or len(imm_rule.strip()) < 20:
                issues.append("WARNING: IMMERSION_RULE is empty/trivial — immersion targets will be missed")

        if "{SECTION_BUDGET_TABLE}" in prompt_text:
            issues.append("ERROR: SECTION_BUDGET_TABLE placeholder unfilled — word targets won't be communicated")

        if "{WORD_TARGET}" in prompt_text:
            issues.append("ERROR: WORD_TARGET placeholder unfilled")

    # 3. Activities-phase checks
    if phase_name == "activities" and "{REQUIRED_TYPES}" in prompt_text:
        issues.append("ERROR: REQUIRED_TYPES placeholder unfilled — activity diversity will be random")

    # 4. Universal: detect unfilled placeholders (any {UPPERCASE_THING} remaining)
    unfilled = set(re.findall(r"\{([A-Z][A-Z_]{3,})\}", prompt_text))
    # Filter out known false positives (markdown/code patterns)
    _false_positives = {"JSON", "YAML", "HTML", "UTF8", "VESUM", "PASS", "FAIL",
                        "TRUE", "FALSE", "NULL", "NONE", "TODO", "NOTE", "IMPORTANT"}
    unfilled -= _false_positives
    if unfilled:
        issues.append(
            f"WARNING: {len(unfilled)} unfilled placeholder(s) in {phase_name} prompt: "
            f"{', '.join(sorted(unfilled)[:5])}"
        )

    return issues


def log_prompt_health(issues: list[str], phase_name: str) -> bool:
    """Log prompt health issues. Returns False if any ERROR-level issue found."""
    if not issues:
        return True

    has_error = False
    for issue in issues:
        log(f"  {phase_name}: HEALTH-CHECK {issue}")
        if issue.startswith("ERROR:"):
            has_error = True

    if has_error:
        log(f"  {phase_name}: BLOCKED by prompt health check — fix template/placeholders before dispatch")

    return not has_error


def dispatch_gemini(
    prompt: str, task_id: str, model: str = PRO_MODEL,
    stdout_only: bool = False, allow_write: bool = False,
    output_file: Path | None = None, timeout: int = 1800,
) -> tuple[bool, str]:
    """Dispatch a prompt to Gemini with stdout_only=True and flash→pro fallback.

    This is the default dispatch used by the pipeline. Always forces stdout_only=True.
    If the specified model is Flash and it fails due to rate limiting, retries with Pro.
    """
    ok, output = dispatch_gemini_raw(
        prompt, task_id, model=model,
        stdout_only=True,  # Always stdout-only in pipeline
        allow_write=allow_write, output_file=output_file, timeout=timeout,
    )
    # Fallback: if flash failed due to rate limit, retry with pro
    if not ok and model == FLASH_MODEL and _is_rate_limited(output):
        log("  [fallback] Flash rate-limited, retrying with pro model...")
        ok, output = dispatch_gemini_raw(
            prompt, task_id, model=PRO_MODEL,
            stdout_only=True, allow_write=allow_write,
            output_file=output_file, timeout=timeout,
        )
        if ok:
            log("  [fallback] Pro model succeeded")
    return ok, output


# ============================================================================
# 10. Template & Extraction Helpers
# ============================================================================

def fill_template(
    template: Path, placeholders: dict[str, str], output: Path,
    overrides: dict[str, str] | None = None, strict: bool = False,
) -> bool:
    """Fill a template with placeholders dict (in-memory). Returns True on success."""
    from generate_mdx.fill_template import fill_template as _fill
    from generate_mdx.fill_template import find_unresolved

    if not template.exists():
        log(f"  fill_template FAILED: template not found: {template}")
        return False

    template_text = template.read_text(encoding="utf-8")
    merged = dict(placeholders)
    if overrides:
        merged.update(overrides)

    filled = _fill(template_text, merged)
    unresolved = find_unresolved(filled)
    if unresolved:
        msg = f"Unresolved placeholders ({len(unresolved)}): {', '.join(unresolved)}"
        if strict:
            log(f"  fill_template FAILED: {msg}")
            return False
        else:
            log(f"  fill_template WARNING: {msg}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(filled, encoding="utf-8")
    return True


def _gemini_output_path(slug: str, phase: str) -> Path:
    return TMP_DIR / f"gemini-output-{slug}-phase-{phase}.txt"


def _dispatch_prompt(ctx: ModuleContext, prompt_file: Path) -> str:
    """Build the standard dispatch prompt string."""
    content = prompt_file.read_text("utf-8")
    return f"Activate skill {ctx.skill_name}.\n\n{content}"


def extract_phase_output(
    input_file: Path, phase_key: str, output_dir: Path, attempt: int = 1,
    tags: list[str] | None = None,
) -> bool:
    """Extract delimited content via extract_phase.py. Returns True if all tags found."""
    args = [
        str(SCRIPTS_DIR / "extract_phase.py"),
        str(input_file),
        "--output-dir", str(output_dir),
        "--attempt", str(attempt),
    ]
    if tags:
        args.extend(["--tags", *tags])
        args.extend(["--phase", phase_key])
    else:
        args.extend(["--phase", phase_key])
    result = run_script(args, capture=True)
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            log(f"    {line}")
    return result.returncode == 0


def _extract_delimited_content(text: str, start_tag: str, end_tag: str) -> str | None:
    """Extract content between delimiter tags, handling code block wrapping.

    Uses the LONGEST match when multiple delimiter pairs exist.
    """
    cleaned = re.sub(r'```\w*\n', '', text)
    cleaned = re.sub(r'\n```', '', cleaned)
    pattern = re.compile(
        rf'{re.escape(start_tag)}\s*\n(.*?)\n\s*{re.escape(end_tag)}',
        re.DOTALL,
    )
    matches = pattern.findall(cleaned)
    if not matches:
        return None
    best = max(matches, key=len)
    return best.strip()


# ============================================================================
# 11. Verify Helpers
# ============================================================================

def run_verify(content_path: Path, content_only: bool = True,
               skip_review: bool = False) -> tuple[bool, str]:
    """Run verification gate. Returns (passed, output)."""
    if skip_review:
        audit_script = str(PROJECT_ROOT / "scripts" / "audit_module.sh")
        result = subprocess.run(
            [audit_script, "--skip-review", str(content_path)],
            cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=300,
        )
        output = (result.stdout or "") + (result.stderr or "")
        return result.returncode == 0, output

    script = "otaman_verify.py" if content_only else "hetman_verify.py"
    result = run_script([str(SCRIPTS_DIR / script), str(content_path)], capture=True, timeout=300)
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output


def write_review_with_hash(review_path: Path, review_text: str,
                           content_path: Path) -> None:
    """Write review file with embedded content hash for staleness detection."""
    content_hash = hashlib.md5(content_path.read_bytes(), usedforsecurity=False).hexdigest()[:12]
    header = f"<!-- content-hash: {content_hash} -->\n"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(header + review_text, "utf-8")


# Prose-only verification (from v2) — ignores review + activity gates
_NON_PROSE_GATES = {"review", "activities", "density", "unique_types", "priority",
                    "engagement", "activity_quality"}
_ACTIVITY_PEDAGOGY_CODES = {
    "MISSING_ADVANCED_ACTIVITY",
    "MISSING_REQUIRED_ACTIVITY",
    "ACTIVITY_TYPE_MISMATCH",
}


def run_verify_prose_only(content_path: Path) -> tuple[bool, str]:
    """Run audit_module.sh --skip-activities and check only prose-relevant gates."""
    audit_script = str(PROJECT_ROOT / "scripts" / "audit_module.sh")
    result = subprocess.run(
        [audit_script, "--skip-activities", str(content_path)],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=300,
    )
    output = (result.stdout or "") + (result.stderr or "")

    track_dir = content_path.parent
    slug = content_path.stem
    bare_slug = slug.split("-", 1)[1] if slug[0].isdigit() and "-" in slug else slug
    status_file = track_dir / "status" / f"{bare_slug}.json"

    if not status_file.exists():
        return False, output + "\nNo status JSON produced by audit"

    status = json.loads(status_file.read_text(encoding="utf-8"))
    gates = status.get("gates", {})

    activity_ped_count = 0
    for code in _ACTIVITY_PEDAGOGY_CODES:
        activity_ped_count += output.count(f"[{code}]")

    failing = []
    for gate_name, gate_data in gates.items():
        if gate_name in _NON_PROSE_GATES:
            continue
        if gate_data.get("status") == "fail":
            msg = gate_data.get("message", "")
            if gate_name == "lesson" and "pedagogy" in msg:
                ped_match = re.search(r"pedagogy:\s*(\d+)\s*violation", msg)
                if ped_match:
                    total_ped = int(ped_match.group(1))
                    if activity_ped_count >= total_ped:
                        continue
                    real_ped = total_ped - activity_ped_count
                    msg = re.sub(r"pedagogy:\s*\d+\s*violations?",
                                 f"pedagogy: {real_ped} violations", msg)
            failing.append(f"{gate_name}: {msg}")

    if failing:
        return False, output + "\nProse-relevant failures:\n" + "\n".join(f"  {f}" for f in failing)
    return True, output


# ============================================================================
# 12. Fix Prompt Helpers
# ============================================================================

def _parse_section(section: Any) -> tuple[str, int]:
    """Parse a content_outline section entry. Returns (title, words)."""
    if isinstance(section, dict):
        title = section.get("section", section.get("title", "Untitled"))
        words = section.get("words", 0)
        return str(title), int(words)
    return str(section), 0



# Fix-prompt helpers moved to pipeline_v5.py — the only consumer.


# ============================================================================
# 13. Claude CLI Helpers
# ============================================================================

def _claude_cli() -> str:
    """Return path to the claude CLI executable."""
    return shutil.which("claude") or "claude"


def _run_claude_headless(prompt: str, timeout: int = 300, model: str | None = None) -> tuple[bool, str]:
    """Call `claude -p <prompt>` headlessly and return (success, output)."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    cmd = [_claude_cli()]
    if model:
        cmd.extend(["--model", model])
    cmd.extend(["-p", prompt, "--output-format", "text"])
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=str(PROJECT_ROOT), env=env,
        )
        if result.returncode != 0:
            err = (result.stderr or "").strip()
            log(f"  Claude CLI error (rc={result.returncode}): {err[:200]}")
            return False, ""
        return True, result.stdout.strip()
    except FileNotFoundError:
        log("  Claude CLI not found — install claude and ensure it is on PATH")
        return False, ""
    except Exception as e:
        log(f"  Claude CLI exception: {e}")
        return False, ""


def _apply_file_fixes(fix_response: str, ctx: ModuleContext) -> int:
    """Parse and apply OLD/NEW file fixes from Claude final review output."""
    blocks = re.findall(
        r"===FIX_START===\s*\n(.*?)===FIX_END===",
        fix_response, re.DOTALL,
    )
    applied = 0
    for block in blocks:
        file_match = re.search(r"^FILE:\s*(.+)$", block, re.MULTILINE)
        old_match = re.search(r"---OLD---\s*\n(.*?)---NEW---", block, re.DOTALL)
        new_match = re.search(r"---NEW---\s*\n(.*?)$", block, re.DOTALL)
        if not (file_match and old_match and new_match):
            log("    FIX: skipping malformed block")
            continue
        rel_path = file_match.group(1).strip()
        target = PROJECT_ROOT / rel_path
        if not target.exists():
            log(f"    FIX: file not found: {rel_path}")
            continue
        old_text = old_match.group(1).rstrip("\n")
        new_text = new_match.group(1).rstrip("\n")
        content = target.read_text(encoding="utf-8")
        if old_text not in content:
            log(f"    FIX: old text not found in {target.name} — skipping")
            continue
        content = content.replace(old_text, new_text, 1)
        target.write_text(content, encoding="utf-8")
        log(f"    FIX applied: {target.name}")
        applied += 1
    return applied


def dispatch_claude_final_review(ctx: ModuleContext) -> tuple[bool, str, str]:
    """Phase 9: Full final QA gate via headless Claude CLI.

    Returns (success, verdict, report_text).
    """
    def _read(path: Path | None) -> str:
        if path and path.exists():
            return path.read_text(encoding="utf-8")
        return "(file not found)"

    content_text   = _read(ctx.paths.get("md"))
    activities_text = _read(ctx.paths.get("activities"))
    vocab_text     = _read(ctx.paths.get("vocabulary"))
    plan_path = PROJECT_ROOT / f"curriculum/l2-uk-en/plans/{ctx.track}/{ctx.slug}.yaml"
    plan_text      = _read(plan_path)
    review_text    = _read(ctx.paths.get("review"))

    _, audit_output = run_verify(ctx.paths["md"], content_only=False)

    content_rel   = f"curriculum/l2-uk-en/{ctx.track}/{ctx.slug}.md"
    activities_rel = f"curriculum/l2-uk-en/{ctx.track}/activities/{ctx.slug}.yaml"
    vocab_rel     = f"curriculum/l2-uk-en/{ctx.track}/vocabulary/{ctx.slug}.yaml"

    system_prompt = (
        "You are the final adversarial QA gate for Ukrainian language curriculum modules. "
        "A Gemini pipeline built this module. Your job is to catch semantic errors, "
        "pedagogical traps, and LLM artifacts that automated audits cannot detect. "
        "Trust nothing — verify everything by reading the actual file contents. "
        "Apply fixes directly using the structured format. Be the adversary."
    )

    user_prompt = f"""# Phase 9: Final QA Review — {ctx.slug}

**Track:** {ctx.track} | **Module:** #{ctx.module_num}

---

## Files

### Content ({content_rel})
```markdown
{content_text}
```

### Activities ({activities_rel})
```yaml
{activities_text}
```

### Vocabulary ({vocab_rel})
```yaml
{vocab_text}
```

### Plan (source of truth)
```yaml
{plan_text}
```

### Existing Review (Green Team)
```markdown
{review_text}
```

### Fresh Audit Output
```
{audit_output}
```

---

## Your Task

Perform a deep adversarial review. Check ALL of the following:

**Ukrainian Language Quality:**
- No Russianisms (кушати, получати, приймати участь, слідуючий)
- No Russian characters (ы, э, ё, ъ)
- Gender agreement, case agreement, verb aspect correct

**Pedagogical Correctness:**
- No vocabulary outside the plan's vocabulary_hints used in activities
- No grammar forms beyond this module's level (check plan.grammar_focus)
- No forward references to future modules presented as teachable content
- Unjumble activities: words array contains all words+punctuation in the answer
- Fill-in activities: answer produces a grammatical sentence when inserted

**Factual Accuracy:**
- Dates, names, translations correct
- Historical/cultural claims accurate and not contested

**LLM Artifacts:**
- Purple prose, grandiose openers
- "Це не просто X, а Y" overuse
- Folk etymology presented as fact
- False statistics or invented percentages

**Plan Compliance:**
- All content_outline sections present
- Required vocabulary used in prose
- Objectives map to self-check questions

---

## Output Format

First, list every issue you found (be specific — quote the exact text, state the file and line context, explain what's wrong and what the correct version should be).

Then output fixes using EXACTLY this format for each fix (no code fences around the blocks):

===FIX_START===
FILE: {content_rel}
---OLD---
exact text to replace (must exist verbatim in the file)
---NEW---
exact replacement text
===FIX_END===

You may use multiple FIX blocks. The FILE field must be one of:
- {content_rel}
- {activities_rel}
- {vocab_rel}

Finally, output your verdict:

===VERDICT===
APPROVE
===END_VERDICT===

Verdict guide:
- APPROVE: audit passes, no remaining issues after fixes
- NEEDS_WORK: fixed what you could, minor issues remain (still pass audit)
- REJECT: content is thin (<70% word target), unfixable Russianisms, broken activities, or factual errors in core claims

Do not rubber-stamp. A verdict of APPROVE on a module with real unfixed issues is a failure.
"""

    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    claude_model_f = getattr(ctx, "claude_model_F", None)
    log(f"  Phase 9 (Claude): Calling headless claude for final QA review{f' [{claude_model_f}]' if claude_model_f else ''}...")
    ok, report = _run_claude_headless(full_prompt, timeout=600, model=claude_model_f)
    if not ok:
        return False, "", ""
    log(f"  Phase 9 (Claude): Review complete ({len(report)} chars)")

    fixes_applied = _apply_file_fixes(report, ctx)
    if fixes_applied:
        log(f"  Phase 9 (Claude): Applied {fixes_applied} fix(es)")

    verdict_match = re.search(
        r"===VERDICT===\s*\n\s*(APPROVE|NEEDS_WORK|REJECT)\s*\n\s*===END_VERDICT===",
        report,
    )
    verdict = verdict_match.group(1) if verdict_match else "NEEDS_WORK"
    log(f"  Phase 9 (Claude): Verdict → {verdict}")
    return True, verdict, report


# ============================================================================
# 14. Review Tier Helpers
# ============================================================================

REVIEW_TIERS_DIR = PROJECT_ROOT / "claude_extensions" / "skills" / "plan-review" / "review-tiers"

TIER_MAP: dict[str, str] = {
    "a1": "tier-1-beginner.md",
    "a2": "tier-1-beginner.md",
    "b1": "tier-2-core.md",
    "b2": "tier-2-core.md",
    "b2-pro": "tier-2-core.md",
    "hist": "tier-3-seminar.md",
    "bio": "tier-3-seminar.md",
    "istorio": "tier-3-seminar.md",
    "lit": "tier-3-seminar.md",
    "c1": "tier-4-advanced.md",
    "c1-pro": "tier-4-advanced.md",
    "c2": "tier-4-advanced.md",
}


def get_tier_guidance(track: str) -> str:
    """Read the appropriate review-tier guidance file for a track."""
    key = "lit" if track.startswith("lit-") else track
    tier_file = TIER_MAP.get(key)
    if not tier_file:
        base = track.split("-")[0]
        tier_file = TIER_MAP.get(base, "tier-2-core.md")
    path = REVIEW_TIERS_DIR / tier_file
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"(Tier guidance file not found: {tier_file})"


def _is_tier1(track: str) -> bool:
    key = "lit" if track.startswith("lit-") else track
    tier_file = TIER_MAP.get(key)
    if not tier_file:
        base = track.split("-")[0]
        tier_file = TIER_MAP.get(base, "tier-2-core.md")
    return tier_file == "tier-1-beginner.md"


def _get_scoring_section(track: str) -> str:
    """Return the STEP 4 scoring block with tier-appropriate dimensions."""
    if _is_tier1(track):
        return """### STEP 4: Score 7 Dimensions

| # | Dimension | Weight | Auto-fail |
|---|-----------|--------|-----------|
| 1 | Experience Quality | 1.5 | <7 |
| 2 | Language | 1.1 | <8 |
| 3 | Pedagogy | 1.2 | <7 |
| 4 | Activities | 1.3 | <7 |
| 5 | Beginner Safety | 1.3 | <7 |
| 6 | LLM Fingerprint | 1.0 | <7 |
| 7 | Linguistic Accuracy | 1.5 | <9 |

**Weighted Overall:**
```
Overall = (Experience x 1.5 + Language x 1.1 + Pedagogy x 1.2 +
          Activities x 1.3 + Beginner_Safety x 1.3 + LLM x 1.0 +
          Linguistic_Accuracy x 1.5) / 8.9
```

**Why 7 dimensions?** A1/A2 modules are short and topic-constrained, so Coherence, Relevance, Educational, Immersion, Richness, and Factual Accuracy are noise at this level — they auto-pass trivially and waste reviewer attention. Focus scoring on what actually differentiates good beginner modules."""
    else:
        return """### STEP 4: Score 13 Dimensions

| # | Dimension | Auto-fail |
|---|-----------|-----------|
| 1 | Experience Quality | <7 |
| 2 | Coherence | <7 |
| 3 | Relevance | <7 |
| 4 | Educational | <7 |
| 5 | Language | <8 |
| 6 | Pedagogy | <7 |
| 7 | Immersion | <6 |
| 8 | Activities | <7 |
| 9 | Richness | <6 |
| 10 | Beginner Safety | <7 |
| 11 | LLM Fingerprint | <7 |
| 12 | Linguistic Accuracy | <9 |
| 13 | Factual Accuracy | <8 |

**Weighted Overall:**
```
Overall = (Experience x 1.5 + Coherence x 1.0 + Relevance x 1.0 + Educational x 1.2 +
          Language x 1.1 + Pedagogy x 1.2 + Immersion x 1.0 + Activities x 1.3 +
          Richness x 0.9 + Beginner_Safety x 1.3 + LLM x 1.0 + Linguistic_Accuracy x 1.5 +
          Factual_Accuracy x 1.5) / 15.5
```

**Factual Accuracy note:** ALL tracks — verify callout boxes (`[!did-you-know]`, `[!myth-buster]`, `[!culture-note]`, `[!fun-fact]`) for fabricated claims. Seminar tracks — additionally verify against research notes/Key Facts Ledger. Do NOT auto-score 9 for any track."""


def _get_scoring_output_table(track: str) -> str:
    if _is_tier1(track):
        return """| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | X/10 | <7 | [specific finding] |
| 2 | Language | X/10 | <8 | [specific finding] |
| 3 | Pedagogy | X/10 | <7 | [specific finding] |
| 4 | Activities | X/10 | <7 | [specific finding] |
| 5 | Beginner Safety | X/10 | <7 | ["Would I Continue?" X/5] |
| 6 | LLM Fingerprint | X/10 | <7 | [specific finding] |
| 7 | Linguistic Accuracy | X/10 | <9 | [specific finding] |"""
    else:
        return """| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | X/10 | <7 | [specific finding] |
| 2 | Coherence | X/10 | <7 | [specific finding] |
| 3 | Relevance | X/10 | <7 | [specific finding] |
| 4 | Educational | X/10 | <7 | [specific finding] |
| 5 | Language | X/10 | <8 | [specific finding] |
| 6 | Pedagogy | X/10 | <7 | [specific finding] |
| 7 | Immersion | X/10 | <6 | [actual % vs target] |
| 8 | Activities | X/10 | <7 | [specific finding] |
| 9 | Richness | X/10 | <6 | [specific finding] |
| 10 | Beginner Safety | X/10 | <7 | ["Would I Continue?" X/5] |
| 11 | LLM Fingerprint | X/10 | <7 | [specific finding] |
| 12 | Linguistic Accuracy | X/10 | <9 | [specific finding] |
| 13 | Factual Accuracy | X/10 | <8 | [specific finding or "N/A — core track"] |"""


def _get_prompt_tier(track: str, module_num: int) -> str:
    """Determine prompt tier based on track and module number.

    Returns: 'beginner', 'core', or 'seminar'.
    """
    track_lower = track.lower()
    # Use canonical SEMINAR_TRACKS/PRO_TRACKS sets from batch_gemini_config
    if track_lower in SEMINAR_TRACKS or track_lower.split("-")[0] in SEMINAR_TRACKS:
        return "seminar"
    if track_lower in PRO_TRACKS:
        return "core"
    base = track.split("-")[0].upper()
    if base == "A1":
        return "beginner"
    if base == "A2" and module_num <= 20:
        return "beginner"
    return "core"


def _is_checkpoint_module(slug: str) -> bool:
    """Check if a module is a checkpoint based on its slug."""
    return "checkpoint" in slug


def _get_content_template(track: str, module_num: int,
                          full_build: bool = False, rag: bool = False,
                          slug: str = "") -> str:
    """Return the content prompt filename for the given tier."""
    tier = _get_prompt_tier(track, module_num)
    # Checkpoint modules get dedicated templates
    if slug and _is_checkpoint_module(slug):
        if tier == "beginner":
            return "beginner-checkpoint.md"
        return "core-checkpoint.md"
    if full_build and tier == "beginner":
        return "beginner-full-rag.md" if rag else "beginner-full.md"
    if tier == "beginner":
        return "beginner-content.md"
    if tier == "seminar":
        return "content.md"
    return "core-content.md"



def _get_activities_template(track: str, module_num: int,
                             slug: str = "") -> str:
    """Return the activities prompt filename for the given tier."""
    tier = _get_prompt_tier(track, module_num)
    # Checkpoint modules get dedicated activity templates
    if slug and _is_checkpoint_module(slug):
        if tier == "beginner":
            return "beginner-checkpoint-activities.md"
        return "core-checkpoint-activities.md"
    if tier == "beginner":
        return "beginner-activities.md"
    if tier == "seminar":
        return "activities.md"
    return "core-activities.md"


def _read_phase_file(filename: str) -> str:
    path = PHASES_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"(Phase file not found: {filename})"


# ============================================================================
# 15. Write Placeholders
# ============================================================================

def build_placeholders(ctx: ModuleContext) -> None:
    """Build placeholders dict and store on ctx (in-memory, no disk YAML)."""
    if ctx.placeholders and not ctx.rebuild and not getattr(ctx, "force_phase", False):
        log("Placeholders: Using existing (in-memory)")
        return

    level_label = get_level_label(ctx.track)
    quick_ref_path = ctx.track_config.get("quick_ref", "")
    placeholders = {
        "TRACK": ctx.track,
        "LEVEL": level_label,
        "SLUG": ctx.slug,
        "TOPIC_TITLE": ctx.topic_title,
        "MODULE_NUM": str(ctx.module_num),
        "PLAN_PATH": str(ctx.paths["plan"]),
        "PLAN_CONTENT": ctx.paths["plan"].read_text(encoding="utf-8") if ctx.paths["plan"].exists() else "",
        "CONTENT_PATH": str(ctx.paths["md"]),
        "ACTIVITIES_PATH": str(ctx.paths["activities"]),
        "VOCAB_PATH": str(ctx.paths["vocabulary"]),
        "RESEARCH_PATH": str(ctx.paths["research"]),
        "REVIEW_PATH": str(ctx.paths["review"]),
        "QUICK_REF_PATH": str(quick_ref_path) if quick_ref_path else "",
        "QUICK_REF_CONTENT": quick_ref_path.read_text(encoding="utf-8") if quick_ref_path and quick_ref_path.exists() else "",
        "SCHEMA_PATH": f"schemas/activities-{ctx.track}.schema.json",
        "WORD_TARGET": str(ctx.word_target),
        "WORD_CEILING": str(int(ctx.word_target * 1.5)),
        "SKILL_IDENTITY": ctx.skill_identity,
        "PERSONA_FLAVOR": ctx.persona_flavor,
        "PERSONA_VOICE": ctx.plan.get("persona", {}).get("voice", ""),
        "PERSONA_ROLE": ctx.plan.get("persona", {}).get("role", ""),
        "IMMERSION_RULE": ctx.immersion_rule,
        "LEVEL_CONSTRAINTS": ctx.level_constraints,
        "PEDAGOGICAL_CONSTRAINTS": get_pedagogical_constraints(ctx.track, ctx.module_num, ctx.plan),
        "DECODABLE_VOCABULARY": "",  # Decodable system removed (#841) — plan vocabulary_hints is source of truth
        "STRUCTURAL_RULES": get_structural_rules(ctx.track, ctx.module_num),
        "H3_WORD_RANGE": get_h3_word_range(ctx.track, ctx.module_num),
        "EXPANSION_METHOD": get_expansion_method(ctx.track, ctx.module_num),
        "WRITING_TONE_INSTRUCTION": _get_writing_tone(ctx.track, ctx.module_num),
        "WRITING_STYLE": _get_writing_style(ctx),
        "TEXTBOOK_EXAMPLES": _prefetch_textbook_examples(ctx),
        "TEXTBOOK_ACTIVITY_EXAMPLES": _prefetch_textbook_activity_examples(ctx),
        "TEXTBOOK_GRADE": _get_textbook_grade(ctx),
        "TOPIC_KEYWORDS": " ".join(ctx.plan.get("keywords", [])[:3]),
        "CHECKPOINT_GUIDANCE": _get_checkpoint_guidance(ctx),
        "CHECKPOINT_REVIEW_GUIDANCE": _get_checkpoint_review_guidance(ctx),
        "EXACT_SECTION_TITLES": _build_exact_section_titles(ctx),
        "INTRO_HOOK": (
            "Why does this matter?" if (ctx.track.startswith("a1") and ctx.module_num <= 4)
            else "Чому це важливо? — Why does this matter?" if (ctx.track.startswith("a1") and ctx.module_num <= 14)
            else "Чому це важливо?"
        ),
        "SUMMARY_HEADING": (
            "Summary" if (ctx.track.startswith("a1") and ctx.module_num <= 4)
            else "Підсумок — Summary" if (ctx.track.startswith("a1") and ctx.module_num <= 14)
            else "Підсумок"
        ),
        "SELF_CHECK_HEADING": (
            "Check yourself:" if (ctx.track.startswith("a1") and ctx.module_num <= 4)
            else "Перевірте себе — Check yourself:" if (ctx.track.startswith("a1") and ctx.module_num <= 14)
            else "Перевірте себе:"
        ),
        "TIER_EXEMPLAR": "",  # Removed — structural rules work better than exemplars
        "TIER_GUIDANCE": get_tier_guidance(ctx.track),
        "D1_OUTPUT_FORMAT": _read_phase_file("review-output-format.md"),
        "SCORING_SECTION": _get_scoring_section(ctx.track),
        "SCORING_OUTPUT_TABLE": _get_scoring_output_table(ctx.track),
    }

    # Vocabulary hints from plan — injected inline so Gemini sees the actual
    # required/recommended items without needing to read the plan file from disk.
    vocab_hints = ctx.plan.get("vocabulary_hints", {})
    if vocab_hints:
        vh_lines = ["### Vocabulary from Plan (MANDATORY — include ALL required items)\n"]
        required = vocab_hints.get("required", [])
        recommended = vocab_hints.get("recommended", [])
        if required:
            vh_lines.append("**Required** (MUST appear in vocabulary YAML):")
            for item in required:
                vh_lines.append(f"- {item}")
            vh_lines.append("")
        if recommended:
            vh_lines.append("**Recommended** (include if space allows):")
            for item in recommended:
                vh_lines.append(f"- {item}")
            vh_lines.append("")
        vh_lines.append("These are your TARGET words — teach them all and use them heavily. "
                        "For the rest of the text, use natural, level-appropriate Ukrainian.")
        vh_lines.append("")
        vh_lines.append("**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints "
                        "MUST appear at least once in the module content. Orphaned vocabulary "
                        "(listed but never used in content) is a validation failure.")
        placeholders["VOCAB_HINTS"] = "\n".join(vh_lines)
        placeholders["VOCABULARY_HINTS"] = placeholders["VOCAB_HINTS"]
    else:
        placeholders["VOCAB_HINTS"] = ""
        placeholders["VOCABULARY_HINTS"] = ""

    # Video discovery placeholder
    discovery_path = ctx.orch_dir / "discovery.yaml"
    if discovery_path.exists():
        try:
            from video_discovery import format_discovery_for_template, read_discovery_yaml
            result = read_discovery_yaml(discovery_path)
            placeholders["VIDEO_DISCOVERY"] = format_discovery_for_template(result)
        except Exception:
            placeholders["VIDEO_DISCOVERY"] = "(No video discoveries available)"
    else:
        placeholders["VIDEO_DISCOVERY"] = "(No video discoveries available)"

    # Supplement with YouTube links from research (research may find per-letter
    # videos that channel-based discovery missed)
    research_path = ctx.paths.get("research")
    if research_path and research_path.exists():
        try:
            import re as _re
            research_text = research_path.read_text("utf-8")
            yt_links = _re.findall(
                r'-\s*(.+?)\s*[-—]\s*(https://www\.youtube\.com/watch\?v=[^\s]+)',
                research_text,
            )
            if yt_links:
                lines = ["\n### Research Videos"]
                lines.append("*These videos were found during the research phase. "
                             "Embed each one next to its corresponding letter/topic section "
                             "using a markdown link.*\n")
                for desc, url in yt_links:
                    lines.append(f"- {desc.strip()} — {url}")
                placeholders["VIDEO_DISCOVERY"] += "\n".join(lines)
        except Exception:
            pass

    # Pronunciation videos from plan (alphabet modules)
    pv = ctx.plan.get("pronunciation_videos")
    if pv and isinstance(pv, dict):
        credit = pv.get('credit', 'Anna Ohoiko — Ukrainian Lessons')
        letters = pv.get("letters", {})
        overview = pv.get("overview")
        playlist = pv.get("playlist")

        pv_lines = ["### Pronunciation Videos (from plan — MANDATORY embeds)"]
        pv_lines.append(f"*Credit: {credit}*\n")
        if overview:
            pv_lines.append(f"- **Overview**: [{credit} — Overview]({overview})")
        if playlist:
            pv_lines.append(f"- **Full Playlist**: [{credit} — Playlist]({playlist})")
        if letters:
            pv_lines.append("")
            pv_lines.append("**Each letter below MUST get its video embedded "
                            "in the corresponding H3 section:**\n")
            for letter, url in letters.items():
                pv_lines.append(f"- **Літера {letter}**: [{credit} — {letter}]({url})")
        elif overview:
            pv_lines.append("")
            pv_lines.append("**Embed the overview video in the introduction section "
                            "and reference the playlist for students who want per-letter videos.**")
        placeholders["PRONUNCIATION_VIDEOS"] = "\n".join(pv_lines)
    else:
        placeholders["PRONUNCIATION_VIDEOS"] = ""

    # Shared rules — tier-aware: beginner gets minimal rules, core/seminar get full set
    tier = _get_prompt_tier(ctx.track, ctx.module_num)
    # Core and seminar share the same rules (can diverge later by adding a seminar file)
    rules_tier = "beginner" if tier == "beginner" else "core"
    _shared_rules_file = f"_shared-content-rules-{rules_tier}.md"
    placeholders["SHARED_CONTENT_RULES"] = _read_phase_file(_shared_rules_file)
    placeholders["SHARED_ACTIVITY_RULES"] = _read_phase_file("_shared-activity-rules.md")
    # Self-audit: beginner tier skips it (validate phase catches everything);
    # core/seminar keep the full self-audit snippet.
    if tier == "beginner":
        placeholders["SELF_AUDIT_SNIPPET"] = ""
    else:
        # Resolve {CONTENT_PATH} inside the snippet so nested placeholders expand correctly.
        # fill_template does a single pass; snippets included via {SELF_AUDIT_SNIPPET} would
        # otherwise leave {CONTENT_PATH} unresolved in the final prompt.
        _self_audit_raw = _read_phase_file("_shared-self-audit.md")
        placeholders["SELF_AUDIT_SNIPPET"] = _self_audit_raw.replace(
            "{CONTENT_PATH}", placeholders.get("CONTENT_PATH", "")
        )

    # Lexical Sandbox removed in #820 — VESUM post-validation replaces it.
    # Placeholder kept as empty string so existing templates don't break.
    placeholders["LEXICAL_SANDBOX"] = ""

    # Folk Micro-Genres (загадки, скоромовки, прислів'я etc.)
    try:
        from folk_injector import build_folk_material
        folk_text = build_folk_material(track=ctx.track, slug=ctx.slug)
        placeholders["FOLK_MATERIAL"] = folk_text
        ctx._folk_material = folk_text
        if folk_text:
            log(f"  folk: Injected folk material ({len(folk_text)} chars)")
    except Exception as e:
        logger.debug("folk_injector not available: %s", e)
        placeholders["FOLK_MATERIAL"] = ""
        ctx._folk_material = ""

    placeholders.update(ctx.activity_config)

    # Populate REQUIRED_TYPES if empty — from plan activity_hints or PRIORITY_TYPES
    if not placeholders.get("REQUIRED_TYPES"):
        plan_hints = ctx.plan.get("activity_hints", [])
        if plan_hints and isinstance(plan_hints, list):
            # Hints can be strings ("quiz") or dicts ({"type": "quiz", "focus": "..."})
            hint_types = []
            for h in plan_hints[:5]:
                if isinstance(h, dict):
                    hint_types.append(h.get("type", str(h)))
                else:
                    hint_types.append(str(h))
            placeholders["REQUIRED_TYPES"] = ", ".join(hint_types)
        elif placeholders.get("PRIORITY_TYPES"):
            # Use first 3 priority types as required minimum variety
            priorities = [t.strip() for t in placeholders["PRIORITY_TYPES"].split(",")]
            placeholders["REQUIRED_TYPES"] = ", ".join(priorities[:3])

    # REQUIRED_TYPES comes from plan activity_hints (source of truth).
    # No hardcoded overrides — if a plan needs bukvar types, they're in activity_hints.

    placeholders["ITEM_MINIMUMS_TABLE"] = get_item_minimums_table(ctx.track, ctx.module_num)
    ctx.placeholders = placeholders
    log(f"Placeholders: Built ({len(placeholders)} keys)")


# ============================================================================
# 16. Archive Helpers (from v2)
# ============================================================================

ARCHIVE_DIR = PROJECT_ROOT / "_archive"
ARCHIVE_WORD_THRESHOLD = 2000
ARCHIVE_GIT_REF = os.environ.get("ARCHIVE_GIT_REF", "944f3524a^")
ARCHIVE_SKIP_TRACKS: set[str] = {"bio", "istorio", "lit"}


def detect_archived_prose(track: str, slug: str) -> tuple[bool, str, Path | None]:
    """Check for restorable archived prose."""
    if track in ARCHIVE_SKIP_TRACKS:
        return False, "", None
    track_archive = ARCHIVE_DIR / track
    if track_archive.is_dir():
        ts_dirs = sorted(
            [d for d in track_archive.iterdir() if d.is_dir() and not d.name.startswith("_")],
            reverse=True,
        )
        for ts_dir in ts_dirs:
            md_path = ts_dir / f"{slug}.md"
            if md_path.exists():
                word_count = len(md_path.read_text(encoding="utf-8").split())
                if word_count >= ARCHIVE_WORD_THRESHOLD:
                    return True, f"filesystem: {ts_dir.name} ({word_count}w)", ts_dir
                log(f"  Archive: found {md_path.name} but only {word_count}w (need {ARCHIVE_WORD_THRESHOLD})")
    if not track_archive.is_dir():
        try:
            git_path = f"curriculum/l2-uk-en/{track}/{slug}.md"
            result = subprocess.run(
                ["git", "show", f"{ARCHIVE_GIT_REF}:{git_path}"],
                capture_output=True, text=True, timeout=10,
                cwd=str(PROJECT_ROOT),
            )
            if result.returncode == 0 and result.stdout:
                word_count = len(result.stdout.split())
                if word_count >= ARCHIVE_WORD_THRESHOLD:
                    return True, f"git:{ARCHIVE_GIT_REF} ({word_count}w)", None
        except (subprocess.TimeoutExpired, OSError):
            pass
    return False, "", None


def restore_from_archive(ctx: ModuleContext, archive_dir: Path | None) -> bool:
    """Restore archived prose (and optionally activities/vocab) to live paths."""
    slug = ctx.slug
    content_path = ctx.paths["md"]
    content_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_dir is not None:
        src_md = archive_dir / f"{slug}.md"
        if not src_md.exists():
            log(f"  Restore: {src_md} not found")
            return False
        shutil.copy2(src_md, content_path)
        log(f"  Restore: prose {src_md.name} → {content_path.name}")
    else:
        git_path = f"curriculum/l2-uk-en/{ctx.track}/{slug}.md"
        result = subprocess.run(
            ["git", "show", f"{ARCHIVE_GIT_REF}:{git_path}"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode != 0 or not result.stdout:
            log("  Restore: git extraction failed")
            return False
        content_path.write_text(result.stdout, encoding="utf-8")
        log(f"  Restore: git:{ARCHIVE_GIT_REF}:{git_path} → {content_path.name}")
    if not content_path.exists():
        return False
    word_count = len(content_path.read_text(encoding="utf-8").split())
    if word_count < ARCHIVE_WORD_THRESHOLD:
        log(f"  Restore: REJECTED — only {word_count}w (need {ARCHIVE_WORD_THRESHOLD})")
        content_path.unlink()
        return False
    for sub, dest_key in [("activities", "activities"), ("vocabulary", "vocabulary")]:
        if archive_dir is not None:
            src = archive_dir / sub / f"{slug}.yaml"
            if src.exists():
                ctx.paths[dest_key].parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, ctx.paths[dest_key])
                log(f"  Restore: {sub}/{slug}.yaml")
        else:
            git_sub = f"curriculum/l2-uk-en/{ctx.track}/{sub}/{slug}.yaml"
            r = subprocess.run(
                ["git", "show", f"{ARCHIVE_GIT_REF}:{git_sub}"],
                capture_output=True, text=True, timeout=10,
                cwd=str(PROJECT_ROOT),
            )
            if r.returncode == 0 and r.stdout.strip():
                ctx.paths[dest_key].parent.mkdir(parents=True, exist_ok=True)
                ctx.paths[dest_key].write_text(r.stdout, encoding="utf-8")
                log(f"  Restore: git {sub}/{slug}.yaml")
    pct = word_count * 100 // max(ctx.word_target, 1)
    log(f"  Restore: {word_count} words ({pct}% of {ctx.word_target} target)")
    return True


def _check_archive_fits_outline(ctx: ModuleContext) -> tuple[bool, list[str], list[str]]:
    """Check if archived prose covers the sections from the current content_outline."""
    archive_dir = getattr(ctx, "archive_dir", None)
    slug = ctx.slug
    if archive_dir is not None:
        src = archive_dir / f"{slug}.md"
        if not src.exists():
            return False, [], []
        content = src.read_text(encoding="utf-8")
    else:
        git_path = f"curriculum/l2-uk-en/{ctx.track}/{slug}.md"
        result = subprocess.run(
            ["git", "show", f"{ARCHIVE_GIT_REF}:{git_path}"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode != 0:
            return False, [], []
        content = result.stdout
    archive_h2s = {h.strip().lower() for h in re.findall(r"^## (.+)$", content, re.MULTILINE)}
    outline = ctx.content_outline
    if not outline:
        word_count = len(content.split())
        return word_count >= ARCHIVE_WORD_THRESHOLD, [], []
    matched = []
    missing = []
    for section in outline:
        title, _ = _parse_section(section)
        if title.strip().lower() in archive_h2s:
            matched.append(title)
        else:
            missing.append(title)
    total = len(outline)
    coverage = len(matched) / total if total > 0 else 0
    return coverage >= 0.7, matched, missing


# ============================================================================
# 17. Phase 2 Content Generation (from v1, used as fallback by Phase B)
# ============================================================================

def _build_section_budget_table(sections: list, word_target: int) -> str:
    """Build a markdown table of section word budgets."""
    rows = ["| Section | Target |", "|---------|--------|"]
    for section in sections:
        title, words = _parse_section(section)
        if words <= 0:
            words = word_target // max(len(sections), 1)
        rows.append(f"| {title} | {words} |")
    rows.append(f"| **Total** | **{word_target}** |")
    return "\n".join(rows)


def _build_phase2_expansion_prompt(
    ctx: ModuleContext, current_text: str, current_words: int,
    deficit: int, had_truncation: bool = False,
) -> str:
    """Build a prompt telling Gemini to expand thin content to meet word target."""
    sections: list[tuple[str, int]] = []
    current_section = ""
    section_text: list[str] = []
    for line in current_text.split("\n"):
        h2_match = re.match(r'^##\s+(.+)', line)
        if h2_match:
            if current_section and section_text:
                wc = len(" ".join(section_text).split())
                sections.append((current_section, wc))
            current_section = h2_match.group(1)
            section_text = []
        else:
            section_text.append(line)
    if current_section and section_text:
        wc = len(" ".join(section_text).split())
        sections.append((current_section, wc))
    section_report = "\n".join(f"- **{name}**: {wc} words" for name, wc in sections)
    research_path = ctx.paths.get("research", "")
    base_level = ctx.track.split('-')[0].upper() if ctx.track else ''
    # A1/A2: no overshoot, just hit the target. B1+: 1.5x.
    overshoot = ctx.word_target if base_level in ('A1', 'A2') or had_truncation else int(ctx.word_target * 1.5)
    return f"""# content: EXPAND — Content is {current_words} words, need {ctx.word_target}+

> **Persona reminder:** You are {ctx.skill_identity}. Write in the voice of {ctx.persona_flavor}. Maintain your voice throughout.

## Problem

Your previous output was **{current_words} words** — below the **{ctx.word_target} word minimum**.
You need to add approximately **{deficit} more words** of substantive content.

### Current section word counts:
{section_report}

## Your Task

Read the current content file at `{ctx.paths["md"]}` and the original prompt at `{ctx.orch_dir / "content-prompt.md"}`.

**Rewrite the ENTIRE module** with expanded content. Every H3 subsection needs:
- Substantive explanatory prose (not just headings and bullet points)
- Example sentences in context
- Callout boxes where appropriate

**DO NOT add filler or padding.** Expand with real pedagogical content only.

## Critical Rules
- Write at least **{overshoot} words**
- Use research file: `{research_path}`
- Immersion: {ctx.immersion_rule}
- Output between `===CONTENT_START===` and `===CONTENT_END===` delimiters

## Output Format

===CONTENT_START===
{{entire rewritten module with dramatically expanded content}}
===CONTENT_END===

===WORD_COUNTS===
Section "{{name}}": {{count}} words
...
Total: {{total}} words
===WORD_COUNTS===
"""


def _prefetch_sources_for_phase_B(ctx: ModuleContext) -> str:
    """Pre-fetch primary source excerpts from RAG for Phase B content generation.

    For seminar tracks: extracts section names + key terms from plan/meta,
    searches literary RAG, returns formatted excerpts Gemini can cite.
    """
    track_key = "lit" if ctx.track.startswith("lit-") else ctx.track
    if track_key not in SEMINAR_TRACKS:
        return ""

    # Extract search terms from content_outline section names + topic title
    search_terms = []
    topic = ctx.topic_title or ctx.slug.replace("-", " ")
    search_terms.append(topic)
    for section in ctx.content_outline:
        section_name = section.get("section") or section.get("title", "")
        if section_name:
            search_terms.append(section_name)
    # Add vocabulary hints as search terms
    vocab_hints = ctx.plan.get("vocabulary_hints", {})
    for term in vocab_hints.get("required", [])[:3]:
        search_terms.append(term)
    # Cap at 5 searches
    search_terms = [t for t in search_terms if t.strip()][:5]
    if not search_terms:
        return ""

    try:
        from rag.query import search_literary
    except ImportError:
        return ""

    results = []
    seen_chunks = set()
    for term in search_terms:
        try:
            hits = search_literary(term, limit=2)
        except Exception:
            continue
        for hit in hits:
            cid = hit.get("chunk_id", "")
            if cid in seen_chunks:
                continue
            seen_chunks.add(cid)
            work = hit.get("work", "unknown")
            year = hit.get("year", "?")
            genre = hit.get("genre", "")
            text = hit.get("text", "")[:300]
            results.append(
                f"**{work}** ({year}, {genre}):\n> {text}"
            )

    if not results:
        return ""

    return "\n\n".join(results[:8])  # Cap at 8 excerpts


def _clean_textbook_text(text: str) -> str:
    """Strip OCR artifacts from textbook text without destroying numbered lists.

    Removes: stray brackets [], excessive blank lines, stray pipe characters.
    Preserves: numbered lists (1. Foo), lettered sub-tasks (А. Б. В.).
    """
    # Remove stray brackets — preserve markdown links [text](url) and images ![alt](url)
    text = re.sub(r'\[([^\]]*)\]\(([^)]*)\)', r'MDLINK\1MDURL\2MDEND', text)  # protect links
    text = re.sub(r'[\[\]]', '', text)  # strip stray brackets
    text = re.sub(r'MDLINK(.*?)MDURL(.*?)MDEND', r'[\1](\2)', text)  # restore links
    # Collapse 3+ blank lines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove stray pipe chars at start/end of lines (OCR table artifacts)
    text = re.sub(r'^\|?\s*\|\s*$', '', text, flags=re.MULTILINE)
    return text.strip()


def _prefetch_textbook_examples(ctx: ModuleContext) -> str:
    """Pre-fetch textbook/encyclopedia examples from RAG for content generation.

    - A1/A2: searches bukvar (grade 1-2) for letter/syllable exercises
    - B1+ core: searches ukrainska-mova for grammar explanations
    - Seminar (HIST/BIO/ISTORIO/LIT/OES/RUTH): searches textbooks for factual grounding
    Returns formatted examples Gemini can use as reference material.
    """
    base = ctx.track.split("-")[0]
    track_key = "lit" if ctx.track.startswith("lit-") else ctx.track
    is_seminar = track_key in SEMINAR_TRACKS

    # Build search terms from plan keywords and section titles
    search_terms = []
    plan_keywords = ctx.plan.get("keywords", [])
    if plan_keywords:
        search_terms.extend(plan_keywords[:3])
    for section in ctx.content_outline[:3]:
        section_name = section.get("section") or section.get("title", "")
        if section_name:
            # Strip English translations in parentheses or after em-dash
            uk_part = section_name.split("(")[0].strip() if "(" in section_name else section_name
            if "—" in uk_part:
                parts = uk_part.split("—", 1)
                # Pick whichever side has Cyrillic (handles English-first titles)
                def has_cyr(s: str) -> bool:
                    return any("\u0400" <= c <= "\u04ff" for c in s)
                uk_part = parts[0].strip() if has_cyr(parts[0]) else parts[1].strip()
            search_terms.append(uk_part)
    if not search_terms:
        topic = ctx.topic_title or ctx.slug.replace("-", " ")
        search_terms.append(topic)

    search_terms = [t for t in search_terms if t.strip()][:4]
    if not search_terms:
        return ""

    results = []
    seen_chunks = set()

    # --- Seminar tracks: search textbooks (history, literature) ---
    if is_seminar:
        try:
            from rag.query import search_text as _st
        except ImportError:
            _st = None

        # Search textbooks without subject filter — plan keywords naturally match
        # history textbooks for HIST/ISTORIO, literature for LIT/OES/RUTH
        if _st:
            for term in search_terms:
                try:
                    hits = _st(term, limit=3)
                except Exception:
                    continue
                for hit in hits:
                    cid = hit.get("chunk_id", "")
                    if cid in seen_chunks:
                        continue
                    seen_chunks.add(cid)
                    source = hit.get("source", "")
                    section = hit.get("section", "")
                    text = _clean_textbook_text(hit.get("text", "")[:500])
                    results.append(
                        f"**{source}** — {section}:\n```\n{text}\n```"
                    )


        if results:
            header = (
                "## Textbook & Encyclopedia Reference\n\n"
                "These are excerpts from real Ukrainian school textbooks and encyclopedias. "
                "Use them for **factual grounding** — verify dates, names, events, and literary analysis "
                "against these authoritative sources. Do NOT invent historical details or attribute "
                "incorrect quotes to authors.\n\n"
            )
            return header + "\n\n".join(results[:8])
        return ""  # Literary sources still handled by _prefetch_sources_for_phase_B

    # --- A1/A2: bukvar ---
    try:
        from rag.query import search_text
    except ImportError:
        return ""

    if base in ("a1", "a2") and (base != "a1" or ctx.module_num <= 14):
        # M1-M14 (script & first contact): bukvar syllable/letter exercises
        # A2: grade 2 bukvar
        subject = "bukvar"
        grade = 1 if base == "a1" else 2
        header = (
            "## Textbook Reference Examples (from real Ukrainian буквар)\n\n"
            "These are real exercises from Ukrainian 1st-grade primers. "
            "Use them as **inspiration for style and difficulty level** — "
            "notice how they use simple syllable combinations, short words, "
            "and build progressively. Do NOT copy them verbatim, but match their "
            "pedagogical approach and simplicity.\n\n"
        )
    elif base == "a1" and ctx.module_num >= 15:
        # M15+: grammar textbooks (verbs, cases, tenses) — bukvar is irrelevant
        # Higher grades first: imperative mood = Grade 7, not Grade 3
        # No subject filter — some Grade 4 books lack subject metadata
        subject = None
        grade = [7, 6, 5, 4, 3]  # Higher grades first for grammar topics
        header = (
            "## Textbook Reference (from Ukrainian grammar textbooks)\n\n"
            "These are explanations from Ukrainian school grammar textbooks. "
            "Use them as **reference** for grammar rules and examples. "
            "Adapt for adult A1 learners — keep explanations simple "
            "but maintain grammatical accuracy.\n\n"
        )
    else:
        # --- B1+ core tracks: ukrainska-mova grammar ---
        subject = "ukrainska-mova"
        grade = None  # Search all grades — grammar concepts span multiple years
        header = (
            "## Textbook Reference (from real Ukrainian grammar textbooks)\n\n"
            "These are explanations from Ukrainian school grammar textbooks. "
            "Use them as **authoritative reference** for grammar rules, terminology, "
            "and examples. Cross-check your explanations against these. "
            "Adapt for adult learners but keep the grammatical accuracy.\n\n"
        )

    # Normalize grade to a list for iteration
    grade_list = grade if isinstance(grade, list) else ([grade] if grade is not None else [None])

    for term in search_terms:
        for g in grade_list:
            try:
                hits = search_text(term, grade=g, subject=subject, limit=2)
            except Exception:
                continue
            for hit in hits:
                cid = hit.get("chunk_id", "")
                if cid in seen_chunks:
                    continue
                seen_chunks.add(cid)
                author = hit.get("author", "")
                hit_grade = hit.get("grade", "")
                section = hit.get("section_title", hit.get("section", ""))
                text = _clean_textbook_text(hit.get("text", "")[:500])
                label = f"Grade {hit_grade}, {author}" if author else f"Grade {hit_grade}"
                results.append(
                    f"**{label}** — {section}:\n```\n{text}\n```"
                )

    if not results:
        return ""

    note = (
        "\n\nNOTE: The textbook examples above are provided as INSPIRATION "
        "for the pedagogical approach, NOT as content to copy. For modules M15+, "
        "focus on the communicative patterns, not the letter/syllable exercises.\n"
    )
    return header + "\n\n".join(results[:6]) + note


def _get_textbook_grade(ctx: ModuleContext) -> str:
    """Return the recommended textbook grade range for RAG searches.

    Mapping rationale (CEFR → Ukrainian school grades):
      A1 M1-14 (phonology)    → Grades 1-2 (Большакова, Вашуленко — bukvar)
      A1 M15+  (early grammar) → Grades 3-5 (basic cases, tenses, gender)
      A2                       → Grades 3-5 (elementary grammar, simple texts)
      B1                       → Grades 5-7 (Заболотний, Авраменко — morphology)
      B2                       → Grades 8-9 (register, error correction, complex syntax)
      C1                       → Grades 9-10 (stylistics, complex structures)
      C2                       → Grades 10-11 (mastery, rare forms)
      Seminars (HIST, BIO...) → Grades 9-11 (full advanced range)

    Grade is a HARD FILTER in Qdrant — only chunks tagged with matching
    grade(s) are returned.  Overly wide ranges pull in too-complex material.
    """
    base = ctx.track.split("-")[0]
    if base == "a1" and ctx.module_num <= 14:
        return "1-2"
    elif base == "a1":
        return "3-5"  # was 3-7; grades 6-7 contain morphology beyond A1
    elif base == "a2":
        return "3-5"  # was 3-4; grade 5 adds transitive verbs, cases
    elif base == "b1":
        return "5-7"
    elif base == "b2":
        return "8-9"  # was 7-8; grade 7 overlaps B1
    elif base == "c1":
        return "9-10"
    elif base == "c2":
        return "10-11"
    # Seminars (hist, bio, lit, istorio, oes, ruth) — full advanced range
    return "9-11"


# Imperative verbs that signal exercise blocks (task instructions) in textbooks.
# Grade 1-2 use bare imperatives; grade 3+ use formal/plural imperatives.
_EXERCISE_MARKERS = (
    # Singular (grade 1-4)
    "знайди", "спиши", "визнач", "прочитай", "утвори", "добери",
    "запиши", "виправ", "випиши", "підкресли", "розгадай", "склади",
    "збери", "розглянь", "назви", "відшукай", "поміркуй", "пригадай",
    # Plural formal (grade 5-11)
    "спишіть", "визначте", "утворіть", "доберіть", "запишіть",
    "виправте", "випишіть", "підкресліть", "перепишіть", "розберіть",
    "відредагуйте", "скоригуйте", "установіть", "згрупуйте",
    # Exercise markers
    "вправа", "крок 1",
)

_EXERCISE_MARKER_RE = re.compile(
    r'\b(' + '|'.join(re.escape(m) for m in _EXERCISE_MARKERS) + r')',
    re.IGNORECASE,
)


def _prefetch_textbook_activity_examples(ctx: ModuleContext) -> str:
    """Pre-fetch real textbook exercises (вправи) from RAG as activity inspiration.

    Grade mapping (validated against textbook content analysis):
    - A1 M1-M14 → grade 1-2 bukvar (letters, syllables, basic words)
    - A1 M15+   → grade 2-3 (gender, number, basic parts of speech)
    - A2        → grade 3-4 (cases, verb tenses, adj-noun agreement)
    - B1        → grade 5-7 (morphology, word building, style)
    - B2        → grade 7-8 (syntax, error correction, register)
    - C1+       → grade 9-11 (complex syntax, stylistics)

    Exercise labeling varies by grade:
    - Grade 1: bare imperatives (Знайди, Збери, Утвори) — no "Вправа"
    - Grade 2-4: sequential numbers (70., 195., 430.)
    - Grade 5-7: "Вправа NNN" (Litvinova) or plain numbers (others)
    - Grade 8-11: plain numbers + І./ІІ. sub-levels, А./Б./В. sub-tasks
    """
    try:
        from rag.query import search_text
    except ImportError:
        return ""

    base = ctx.track.split("-")[0]

    # Grade mapping + subject + search focus per level
    # Each entry: (grades, subject, focus_queries)
    if base == "a1" and ctx.module_num <= 14:
        grades = [1, 2]
        subject = "bukvar"
        # Grade 1-2 bukvar: bare imperative tasks, no "Вправа" numbering
        focus_queries = [
            "знайди слово букву склад",
            "збери утвори визнач назви",
        ]
    elif base == "a1" and ctx.module_num >= 15:
        grades = [3, 5, 6, 7]  # Grammar topics taught across grades 3-7
        subject = "ukrainska-mova"
        # Use plan section titles as search terms (topic-specific)
        focus_queries = []
        for section in ctx.content_outline[:3]:
            section_name = section.get("section") or section.get("title", "")
            if section_name:
                uk_part = section_name.split("(")[0].strip()
                focus_queries.append(uk_part)
        if not focus_queries:
            focus_queries = [
                "визнач рід іменників число",
                "добери прикметник спиши",
            ]
    elif base == "a2":
        grades = [3, 4]
        subject = "ukrainska-mova"
        # Grade 3-4: case declension, verb conjugation, agreement
        focus_queries = [
            "відмінок іменника називний родовий",
            "дієслово час особа спиши",
        ]
    elif base == "b1":
        grades = [5, 6, 7]
        subject = "ukrainska-mova"
        focus_queries = [
            "спишіть визначте утворіть слова",
            "суфікс префікс будова слова",
        ]
    elif base == "b2":
        grades = [7, 8]
        subject = "ukrainska-mova"
        focus_queries = [
            "спишіть речення підкресліть граматичні основи",
            "відредагуйте речення виправте помилки",
        ]
    else:  # C1, C2
        grades = [9, 10, 11]
        subject = "ukrainska-mova"
        focus_queries = [
            "складнопідрядне речення підрядне",
            "стилістичні засоби установіть відповідність",
        ]

    # Add topic-specific terms from plan keywords
    search_terms = list(focus_queries)
    plan_keywords = ctx.plan.get("keywords", [])
    # Grade 1-2: no "вправа" prefix; grade 3+: add it for better relevance
    prefix = "" if base == "a1" and ctx.module_num <= 14 else "вправа "
    for kw in plan_keywords[:2]:
        search_terms.append(f"{prefix}{kw}")

    results: list[str] = []
    seen_chunks: set[str] = set()

    grade_list = grades if grades is not None else [None]
    for term in search_terms:
        if len(results) >= 5:
            break
        for grade in grade_list:
            if len(results) >= 5:
                break
            try:
                hits = search_text(term, grade=grade, subject=subject, limit=2)
            except Exception:
                continue
            for hit in hits:
                cid = hit.get("chunk_id", "")
                if cid in seen_chunks:
                    continue
                seen_chunks.add(cid)
                text = hit.get("text", "")[:600]
                # Filter: must contain exercise instruction verbs (word boundary)
                if not _EXERCISE_MARKER_RE.search(text):
                    continue
                author = hit.get("author", "")
                hit_grade = hit.get("grade", "")
                section = hit.get("section_title", hit.get("section", ""))
                label = f"Grade {hit_grade}, {author}" if author else f"Grade {hit_grade}"
                results.append(
                    f"**{label}** — {section}:\n```\n{text}\n```"
                )

    if not results:
        return ""

    translate_note = (
        " Since your students are English-speaking adults, **translate exercise instructions "
        "to English** while keeping Ukrainian content words. Adapt the pedagogical approach "
        "(progressive difficulty, real-world context) but not the language of instruction."
        if base in ("a1", "a2") else ""
    )

    return (
        f"### Real Textbook Exercises (вправи) — Pedagogical Inspiration\n\n"
        f"These are real exercises from Ukrainian school textbooks{' (grade ' + '/'.join(str(g) for g in grades) + ')' if grades else ''}. "
        f"Study their **pedagogical patterns** — how they build progressively, "
        f"use familiar vocabulary, and test specific skills.{translate_note}\n\n"
        + "\n\n".join(results[:5])
    )


def phase_2_content(ctx: ModuleContext) -> bool:
    """content: Content (whole-module, single Gemini call)."""
    phase = "2"
    if is_phase_complete(ctx, phase):
        log("  content: SKIP (already complete)")
        return True

    sections = ctx.content_outline
    if not sections:
        log("  content: FAILED — no content_outline in plan")
        return False
    # Ensure bilingual section titles for early A1 (idempotent)
    sections = bilingualify_section_titles(sections, ctx.track, ctx.module_num)

    num_sections = len(sections)
    # Read engagement minimum from audit config (source of truth)
    try:
        from audit.config import LEVEL_CONFIG
        _base = ctx.track.split('-')[0].upper() if ctx.track else 'A1'
        _cfg_engagement = LEVEL_CONFIG.get(_base, {}).get('min_engagement', 3)
    except Exception:
        _cfg_engagement = 3
    engagement_min = _cfg_engagement
    example_min = 8
    base_level = ctx.track.split('-')[0].upper() if ctx.track else ''
    overshoot = ctx.word_target if base_level in ('A1', 'A2') else int(ctx.word_target * 1.5)

    log(f"  content: Whole-module generation ({num_sections} sections, target: {ctx.word_target}w, overshoot: {overshoot}w)")

    # Tier-based content prompt dispatch
    content_template_name = _get_content_template(
        ctx.track, ctx.module_num,
        full_build=getattr(ctx, "full_build", False),
        rag=getattr(ctx, "rag", False),
        slug=ctx.slug,
    )
    template = PHASES_DIR / content_template_name
    if not template.exists():
        # Fallback to monolithic prompt
        template = PHASES_DIR / "content.md"
        log(f"  content: Tier template {content_template_name} not found, falling back to content.md")
    else:
        log(f"  content: Using tier template: {content_template_name}")
    prompt_file = ctx.orch_dir / "content-prompt.md"

    word_target_tokens = ctx.word_target * 2 // 1000
    primary_sources = _prefetch_sources_for_phase_B(ctx)

    # Fix 12: Extract research-identified errors and surface them to content prompt
    research_errors = ""
    _research_path = ctx.paths.get("research")
    if _research_path and _research_path.exists():
        try:
            _research_text = _research_path.read_text("utf-8")
            _error_lines: list[str] = []
            _in_error_section = False
            for _rline in _research_text.split("\n"):
                _lower = _rline.lower()
                if any(kw in _lower for kw in ["common errors:", "помилки", "common mistakes:",
                                                 "типові помилки", "frequent errors"]):
                    _in_error_section = True
                    _error_lines.append(_rline)
                elif _in_error_section:
                    if _rline.startswith("#"):
                        # Next heading — stop collecting
                        break  # New heading ends the section
                    else:
                        _error_lines.append(_rline)
            if len(_error_lines) > 1:
                research_errors = "\n".join(_error_lines).strip()
                log(f"  content: Extracted {len(_error_lines)-1} research error line(s) for content prompt")
        except Exception:
            pass

    overrides = {
        "OVERSHOOT_TARGET": str(overshoot),
        "ENGAGEMENT_MIN": str(engagement_min),
        "EXAMPLE_MIN": str(example_min),
        "SECTION_BUDGET_TABLE": _build_section_budget_table(sections, ctx.word_target),
        "WORD_TARGET_TOKENS": str(word_target_tokens),
        "PRIMARY_SOURCE_EXCERPTS": primary_sources or "(No primary source excerpts available from RAG)",
        "RESEARCH_ERRORS": (
            f"RESEARCH-IDENTIFIED ERRORS (avoid these in content):\n{research_errors}"
            if research_errors else ""
        ),
        "FOLK_MATERIAL": getattr(ctx, "_folk_material", ""),
    }
    if not fill_template(template, ctx.placeholders, prompt_file, overrides=overrides):
        return False

    # Pre-dispatch health check: catch template/placeholder bugs before wasting a Gemini call
    prompt_text = prompt_file.read_text("utf-8")
    health_issues = check_prompt_health(ctx, prompt_text, "content")
    if not log_prompt_health(health_issues, "Phase 2"):
        return False

    if ctx.dry_run:
        log("  content: DRY-RUN — would dispatch whole-module content generation")
        return True

    MAX_P2_ATTEMPTS = 3
    content_path = ctx.paths["md"]
    content_path.parent.mkdir(parents=True, exist_ok=True)
    last_friction = None
    _dispatch_fn = getattr(ctx, "content_dispatch_fn", None) or dispatch_gemini

    for attempt in range(1, MAX_P2_ATTEMPTS + 1):
        attempt_suffix = "" if attempt == 1 else f"-r{attempt}"
        task_suffix = "" if attempt == 1 else f"-r{attempt}"

        if attempt > 1 and content_path.exists():
            current_text = content_path.read_text(encoding="utf-8")
            current_words = len(current_text.split())
            # Skip expand if content already meets or exceeds word target
            if current_words >= ctx.word_target:
                log(f"  content: word count {current_words} >= target {ctx.word_target}, skipping expand")
                mark_phase(ctx, phase, "complete", words=current_words, attempts=attempt - 1)
                return True
            deficit = ctx.word_target - current_words
            had_truncation = last_friction and "TOKEN_LIMIT_TRUNCATION" in last_friction
            if had_truncation:
                log(f"  content: Adjusting expansion target to {ctx.word_target}w (1.0x) due to previous truncation")
            expand_prompt = _build_phase2_expansion_prompt(
                ctx, current_text, current_words, deficit, had_truncation
            )
            expand_prompt_file = ctx.orch_dir / f"content-expand-{attempt}.md"
            expand_prompt_file.write_text(expand_prompt, encoding="utf-8")
            dispatch_file = expand_prompt_file
            log(f"  content: Retry {attempt}/{MAX_P2_ATTEMPTS} — expanding {current_words}w → {ctx.word_target}w target")
        else:
            dispatch_file = prompt_file

        output_file = _gemini_output_path(ctx.slug, f"2{attempt_suffix}")
        ok, _ = _dispatch_fn(
            _dispatch_prompt(ctx, dispatch_file),
            task_id=f"yw-{ctx.slug}-p2{task_suffix}",
            model=ctx.model, stdout_only=True, output_file=output_file,
            allow_write=True, timeout=1200,
        )
        if not ok:
            log(f"  content: Dispatch failed (attempt {attempt})")
            continue

        content_text = None
        if output_file.exists():
            raw = output_file.read_text(encoding="utf-8")
            content_text = _extract_delimited_content(raw, "===CONTENT_START===", "===CONTENT_END===")
            friction = _extract_delimited_content(raw, "===FRICTION_START===", "===FRICTION_END===")
            if friction:
                friction_file = ctx.orch_dir / f"content-friction-{attempt}.md"
                friction_file.write_text(friction, encoding="utf-8")
                log(f"  content: Friction report saved → {friction_file.name}")
                is_real_truncation = (
                    "TOKEN_LIMIT_TRUNCATION" in friction
                    and "YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION" not in friction
                )
                if is_real_truncation:
                    log("  content: ⚠ Gemini reported token limit truncation")
                last_friction = friction if is_real_truncation else last_friction

            # Extract self-audit result if Gemini ran audit in-session
            self_audit = _extract_delimited_content(raw, "===SELF_AUDIT_START===", "===SELF_AUDIT_END===")
            if self_audit:
                sa_file = ctx.orch_dir / f"self-audit-output-{attempt}.md"
                sa_file.write_text(self_audit, encoding="utf-8")
                sa_passed = "status: PASS" in self_audit or "status:PASS" in self_audit
                log(f"  content: Self-audit {'PASSED' if sa_passed else 'FAILED'} → {sa_file.name}")
                if sa_passed:
                    ctx._self_audited = True  # type: ignore[attr-defined]

        if not content_text:
            # Fallback: Gemini may have written directly to CONTENT_PATH via allow_write
            if content_path.exists() and content_path.stat().st_size > 100:
                content_text = content_path.read_text(encoding="utf-8")
                log(f"  content: No delimiters, but Gemini wrote {content_path.name} directly ({len(content_text.split())}w)")
            else:
                log(f"  content: No delimited content extracted (attempt {attempt})")
                continue

        content_path.write_text(content_text, encoding="utf-8")
        # Save extracted content + session to orchestration dir for traceability
        (ctx.orch_dir / f"content-output-{attempt}.md").write_text(content_text, encoding="utf-8")
        save_gemini_session(ctx.orch_dir, label=f"content-attempt-{attempt}")
        total_words = len(content_text.split())
        pct = total_words * 100 // max(ctx.word_target, 1)
        log(f"  content: {total_words} words written ({pct}% of {ctx.word_target} target)")

        # Full-build mode: extract activities + vocabulary from same response
        if getattr(ctx, "full_build", False) and raw:
            for path_key, start, end, orch_name, label in (
                ("activities", "===ACTIVITIES_START===", "===ACTIVITIES_END===",
                 "activities-output.yaml", "Activities"),
                ("vocabulary", "===VOCABULARY_START===", "===VOCABULARY_END===",
                 "activities-output-vocabulary.yaml", "Vocabulary"),
            ):
                text = _extract_delimited_content(raw, start, end)
                target = ctx.paths.get(path_key) if text else None
                if target:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(text, encoding="utf-8")
                    (ctx.orch_dir / orch_name).write_text(text, "utf-8")
                    log(f"  content: {label} extracted from full-build → {target.name}")

        if total_words >= ctx.word_target * 0.75:
            mark_phase(ctx, phase, "complete", words=total_words, attempts=attempt)
            return True
        log(f"  content: Too thin — {total_words}w vs {ctx.word_target}w target (attempt {attempt})")

    log(f"  content: FAIL — exhausted {MAX_P2_ATTEMPTS} attempts, content still under 50% of target")
    return False


# ============================================================================
# 18. Phase B Content (from v2, renamed from phase_2_v2)
# ============================================================================

def phase_B_content(ctx: ModuleContext) -> bool:
    """Phase B: Write Prose. Checks archived prose against plan+research outline.

    Archive is used only if it covers >=70% of the content_outline sections.
    Falls back to phase_2_content if archive doesn't fit.
    """
    phase = "2"
    if getattr(ctx, "refresh", False) and is_phase_complete(ctx, phase):
        state_phases = ctx.state.get("phases", {})
        downstream = [k for k in state_phases if k >= "2"]
        for k in downstream:
            del state_phases[k]
        save_state(ctx)
        log(f"  content: RESET (--refresh flag, cleared {len(downstream)} phases)")
    elif is_phase_complete(ctx, phase):
        log("  content: SKIP (already complete)")
        return True

    content_path = ctx.paths["md"]
    if content_path.exists():
        word_count = len(content_path.read_text(encoding="utf-8").split())
        if word_count >= ctx.word_target * 0.8:
            refresh_needed = False
            research_path = ctx.paths.get("research")
            if research_path and research_path.exists():
                try:
                    from research_quality import assess_research_compat
                    info = assess_research_compat(research_path, ctx.track, content_path)
                    if info and info.get("content_alignment", {}).get("refresh_recommended"):
                        refresh_needed = True
                        reasons = info["content_alignment"].get("reasons", [])
                        log("  content: Research-content misalignment detected")
                        for r in reasons:
                            log(f"    - {r}")
                except ImportError:
                    pass
            if refresh_needed and getattr(ctx, "refresh", False):
                log("  content: --refresh flag set — regenerating prose from research")
            elif refresh_needed:
                log("  content: ADOPT (use --refresh to regenerate from updated research)")
                mark_phase(ctx, phase, "complete", note="adopted-stale-prose", words=word_count)
                return True
            else:
                log(f"  content: ADOPT — existing prose found ({word_count}w, target {ctx.word_target}w)")
                mark_phase(ctx, phase, "complete", note="adopted-existing-prose", words=word_count)
                return True

    if getattr(ctx, "is_archived", False):
        fits, matched, missing = _check_archive_fits_outline(ctx)
        archive_source = getattr(ctx, "archive_source", "unknown")
        if fits:
            log(f"  content: Archive fits outline — {len(matched)}/{len(matched)+len(missing)} sections match")
            if missing:
                log(f"  content: Missing sections (will be caught in activities): {', '.join(missing)}")
            if ctx.dry_run:
                log(f"  content: DRY-RUN — would restore from archive ({archive_source})")
                return True
            archive_dir = getattr(ctx, "archive_dir", None)
            if restore_from_archive(ctx, archive_dir):
                mark_phase(ctx, phase, "complete", note="restored-from-archive",
                           source=archive_source,
                           sections_matched=len(matched),
                           sections_missing=len(missing))
                return True
            else:
                log("  content: Archive restore FAILED — falling back to generation")
        else:
            log(f"  content: Archive does NOT fit outline — only {len(matched)}/{len(matched)+len(missing)} sections match")
            log("  content: Generating fresh prose instead")

    if ctx.dry_run and not ctx.content_outline:
        log("  content: DRY-RUN — would generate prose (outline depends on research)")
        return True

    return phase_2_content(ctx)


# ============================================================================
# 19. Phase E (MDX) + Phase F (Final Review) Delegates
# ============================================================================

def phase_8_mdx(ctx: ModuleContext) -> bool:
    """Phase 8/E: MDX generation + lint. Deterministic, no LLM."""
    phase = "8"
    if is_phase_complete(ctx, phase):
        log("  Phase 8: SKIP (already complete)")
        return True
    if ctx.dry_run:
        log("  Phase 8: DRY-RUN — would generate MDX")
        return True
    log("  Phase 8: Generating MDX...")
    result = run_script([
        str(SCRIPTS_DIR / "generate_mdx.py"), "l2-uk-en", ctx.track, str(ctx.module_num),
    ], capture=True)
    if result.returncode != 0:
        log(f"  Phase 8: WARNING — MDX generation returned {result.returncode}")
    mark_phase(ctx, phase, "complete")
    return True


def phase_9_final_review(ctx: ModuleContext) -> bool:
    """Phase 9/F: Final adversarial QA gate via Claude API."""
    if not getattr(ctx, "final_review", False):
        return True
    phase = "9-final-review"
    if is_phase_complete(ctx, phase):
        log("  Phase 9: SKIP (already complete)")
        return True
    if ctx.dry_run:
        log("  Phase 9: DRY-RUN — would call Claude API for final review")
        return True

    ok, verdict, report = dispatch_claude_final_review(ctx)
    if not ok:
        log("  Phase 9: FAILED — Claude CLI unavailable")
        return False

    final_review_path = ctx.paths["review"].parent / f"{ctx.slug}-final-review.md"
    write_review_with_hash(final_review_path, report, ctx.paths["md"])
    log(f"  Phase 9: Report saved → {final_review_path.name}")
    orch_report = ctx.orch_dir / "final-review.md"
    orch_report.write_text(report, encoding="utf-8")

    if "===FIX_START===" in report:
        passed, audit_out = run_verify(ctx.paths["md"], content_only=False)
        audit_log = ctx.orch_dir / "phase9-post-fix-audit.log"
        audit_log.write_text(audit_out, encoding="utf-8")
        if not passed:
            log(f"  Phase 9: Post-fix audit FAILED (verdict: {verdict})")
            if verdict == "REJECT":
                mark_phase(ctx, phase, "failed", verdict=verdict)
                return False
            log("  Phase 9: Audit failed but verdict is not REJECT — marking NEEDS_WORK")
        else:
            log("  Phase 9: Post-fix audit PASS")

    if verdict == "REJECT":
        log("  Phase 9: REJECT — module needs rebuild")
        mark_phase(ctx, phase, "failed", verdict=verdict)
        return False

    mark_phase(ctx, phase, "complete", verdict=verdict)
    return True


# ============================================================================
# 20. Preflight (from v1 + v2)
# ============================================================================

def preflight(args: argparse.Namespace) -> ModuleContext:
    """Resolve all paths, load plan, compute config. Returns ModuleContext."""
    track = args.track
    num = args.num
    slug = slug_for_num(track, num)
    log(f"Module: {track} #{num} → {slug}")

    if getattr(args, "content_only", False):
        mode = "content-only"
    elif getattr(args, "enrich", False):
        mode = "enrich"
    else:
        mode = "full"

    paths = get_module_paths(track, slug)
    orch_dir = paths["orchestration"]
    for d in [orch_dir, paths["md"].parent,
              paths["activities"].parent, paths["vocabulary"].parent,
              paths["review"].parent, paths["research"].parent,
              paths["status"].parent]:
        d.mkdir(parents=True, exist_ok=True)

    plan_path = paths["plan"]
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan not found: {plan_path}")
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))

    skill_name, skill_identity, persona_flavor = get_track_skill(track, num)
    immersion_rule = get_immersion_rule(track, num)
    level_constraints = get_level_constraints(track, plan)
    activity_config = get_activity_config(track, num)
    track_config = get_track_config(track)

    # config.py is the source of truth for word targets
    try:
        from audit.config import get_word_target as _get_wt
        level_code, module_focus = track_to_level_focus(track)
        word_target = _get_wt(level_code, num, module_focus)
    except Exception:
        word_target = plan.get("word_target", 0)
    topic_title = plan.get("title", slug.replace("-", " ").title())
    content_outline = plan.get("content_outline", [])

    ctx = ModuleContext(
        track=track, module_num=num, slug=slug, mode=mode,
        paths=paths, orch_dir=orch_dir,
        plan=plan,
        word_target=word_target, topic_title=topic_title,
        content_outline=content_outline,
        skill_name=skill_name, skill_identity=skill_identity,
        persona_flavor=persona_flavor,
        immersion_rule=immersion_rule, level_constraints=level_constraints,
        activity_config=activity_config,
        model=track_config.get("model", PRO_MODEL),
        track_config=track_config,
        dry_run=getattr(args, "dry_run", False),
        force_phase=getattr(args, "force_phase", None),
        rebuild=getattr(args, "rebuild", False),
    )

    is_dry = getattr(args, "dry_run", False)
    if getattr(args, "rebuild", False):
        if is_dry:
            ctx.state = load_state(ctx)
            log("State: RESET (--rebuild) — DRY-RUN, no artifacts deleted")
        else:
            ctx.state = load_state(ctx)
            deleted = clean_phase_artifacts(ctx, PHASE_SEQUENCE[0], forward=True)
            state_file = _state_file(ctx)
            lock_file = state_file.with_suffix(".json.lock")
            for f in [state_file, lock_file]:
                if f.exists():
                    f.unlink()
            ctx.state = load_state(ctx)
            log(f"State: RESET (--rebuild) — deleted {deleted} artifacts")
    else:
        ctx.state = load_state(ctx)
        restart_from = getattr(args, "restart_from", None)
        if not is_dry:
            if getattr(args, "force_phase", None):
                deleted = clean_phase_artifacts(ctx, args.force_phase, forward=False)
                if deleted:
                    log(f"Cleaned {deleted} artifacts for phase {args.force_phase}")
            if restart_from:
                deleted = clean_phase_artifacts(ctx, restart_from, forward=True)
                if deleted:
                    log(f"Cleaned {deleted} artifacts from phase {restart_from} onward")
        if restart_from:
            log(f"State: Restarting from {restart_from}")
        elif ctx.state.get("phases"):
            completed = [p for p, v in ctx.state["phases"].items() if v.get("status") == "complete"]
            log(f"State: Loaded — phases complete: {', '.join(completed) or 'none'}")
        else:
            log("State: Fresh")
    return ctx


def preflight_v2(args: argparse.Namespace) -> ModuleContext:
    """Resolve all paths, load plan, detect archive. Returns ModuleContext."""
    track, num = args.track, args.num
    slug_for_num(track, num)  # validate slug exists

    args.content_only = False
    args.enrich = False
    ctx = preflight(args)
    ctx.mode = "e2e"
    ctx.state["mode"] = "e2e"
    _init_state_lock(ctx)

    is_seminar = ctx.track in SEMINAR_TRACKS or ctx.track.startswith("lit-")
    if is_seminar:
        is_archived, archive_source, archive_dir = detect_archived_prose(ctx.track, ctx.slug)
    else:
        is_archived, archive_source, archive_dir = False, "", None

    ctx.is_archived = is_archived  # type: ignore[attr-defined]
    ctx.archive_source = archive_source  # type: ignore[attr-defined]
    ctx.archive_dir = archive_dir  # type: ignore[attr-defined]
    ctx.force_research = getattr(args, "force_research", False)  # type: ignore[attr-defined]
    ctx.refresh = getattr(args, "refresh", False)  # type: ignore[attr-defined]
    ctx.restart_from = getattr(args, "restart_from", None)  # type: ignore[attr-defined]
    ctx.claude_review = getattr(args, "claude_review", False)  # type: ignore[attr-defined]
    ctx.final_review = getattr(args, "final_review", False)  # type: ignore[attr-defined]

    if is_archived:
        log(f"Archive: DETECTED — {archive_source}")
    else:
        log("Archive: none found")
    return ctx


# ============================================================================
# 21. Completion Reports
# ============================================================================

def write_completion_report_v2(ctx: ModuleContext, passed: bool) -> None:
    """Write completion report to orchestration dir."""
    content_path = ctx.paths["md"]
    word_count = 0
    if content_path.exists():
        word_count = len(content_path.read_text(encoding="utf-8").split())
    verdict = "PASS" if passed else "FAIL"
    is_archived = getattr(ctx, "is_archived", False)
    sections_info = ctx.state.get("phases", {}).get("2", {})
    sections_done = sections_info.get("sections_done", "?")
    sections_total = sections_info.get("sections_total", "?")
    # Check for plan auto-fix changelog
    plan_fix_lines = ""
    plan_path = ctx.paths.get("plan")
    if plan_path and plan_path.exists():
        try:
            plan_data = yaml.safe_load(plan_path.read_text("utf-8"))
            if isinstance(plan_data, dict) and plan_data.get("plan_fixes"):
                fixes = plan_data["plan_fixes"]
                if isinstance(fixes, list) and fixes:
                    latest = fixes[-1]
                    changes = latest.get("changes", [])
                    plan_fix_lines = f"\n          Plan fixes: v{latest.get('version', '?')} — {len(changes)} change(s)"
        except Exception:
            pass

    report = textwrap.dedent(f"""\
        {verdict}: pipeline {ctx.track} {ctx.module_num}

          Module:   {ctx.slug}
          Track:    {ctx.track}
          Mode:     {ctx.mode}
          Words:    {word_count} (target: {ctx.word_target})
          Sections: {sections_done}/{sections_total}
          Archive:  {'yes — ' + getattr(ctx, 'archive_source', '') if is_archived else 'no'}
          Verdict:  {verdict}
          Date:     {_now_iso()}{plan_fix_lines}
    """)
    completion_file = ctx.orch_dir / "completion.md"
    completion_file.write_text(report, encoding="utf-8")
    log(f"\nCompletion report → {completion_file}")


# ============================================================================
# 22. Validation Helpers
# ============================================================================

def _validate_activities_yaml(path: Path) -> bool:
    """Check if an activities YAML file passes schema validation."""
    try:
        from audit.checks.yaml_schema_validation import validate_activity_yaml_file
        valid, errors = validate_activity_yaml_file(path)
        if not valid:
            for e in errors[:3]:
                err_str = e.replace('\n', ' ')
                if len(err_str) > 200:
                    err_str = err_str[:197] + "..."
                log(f"    Schema error: {err_str}")
        return valid
    except Exception as e:
        log(f"    Schema validation error: {e}")
        return False
