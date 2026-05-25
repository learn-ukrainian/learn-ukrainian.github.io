"""
Learn Ukrainian Project - Central Configuration Brain

This file stores track-level constants, model mappings, pedagogical floors,
and live immersion policy. It is the source of truth for the dispatcher,
watcher, writer, and audit scripts.
"""

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

try:
    from batch_gemini_config import FLASH_MODEL, PRO_MODEL
except ModuleNotFoundError:
    _SCRIPTS_DIR = Path(__file__).resolve().parent
    if str(_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS_DIR))
    from batch_gemini_config import FLASH_MODEL, PRO_MODEL

# =============================================================================
# TRACK CONFIGURATION
# =============================================================================

TRACK_CONFIG: dict[str, dict[str, Any]] = {
    # --- Core Tracks (Beginner/Intermediate) ---
    "a1": {
        "model": FLASH_MODEL,
        "persona": "The Helpful Neighbor",
        "immersion_range": [0.10, 0.50],
    },
    "a2": {
        "model": FLASH_MODEL,
        "persona": "The Cultural Guide",
        "immersion_range": [0.50, 0.90],
    },
    "b1": {
        "model": FLASH_MODEL,
        "persona": "The Storyteller",
        "immersion_range": [1.0, 1.0],
    },
    "b2": {
        "model": FLASH_MODEL,
        "persona": "The Urbanist",
        "immersion_range": [1.0, 1.0],
    },
    "c1": {
        "model": PRO_MODEL,
        "persona": "The Analyst",
        "immersion_range": [1.0, 1.0],
    },
    "c2": {
        "model": PRO_MODEL,
        "persona": "The Connoisseur",
        "immersion_range": [1.0, 1.0],
    },

    # --- Seminar Tracks (Advanced/Scholar) ---
    "hist": {
        "model": PRO_MODEL,
        "persona": "The Decolonizer",
        "immersion_range": [1.0, 1.0],
    },
    "istorio": {
        "model": PRO_MODEL,
        "persona": "The Sensory Historian",
        "immersion_range": [1.0, 1.0],
    },
    "bio": {
        "model": PRO_MODEL,
        "persona": "The Humanist Biographer",
        "immersion_range": [1.0, 1.0],
    },
    "lit": {
        "model": PRO_MODEL,
        "persona": "The Stylistic Critic",
        "immersion_range": [1.0, 1.0],
    },

    # --- Specialized Literature Tracks ---
    "lit-war": {
        "model": PRO_MODEL,
        "persona": "The Trauma Analyst",
        "immersion_range": [1.0, 1.0],
    },
    "lit-essay": {
        "model": PRO_MODEL,
        "persona": "The Intellectual Historian",
        "immersion_range": [1.0, 1.0],
    },
    "lit-fantastika": {
        "model": PRO_MODEL,
        "persona": "The World-Builder",
        "immersion_range": [1.0, 1.0],
    },
    "lit-hist-fic": {
        "model": PRO_MODEL,
        "persona": "The Historical Narratologist",
        "immersion_range": [1.0, 1.0],
    },
    "lit-humor": {
        "model": PRO_MODEL,
        "persona": "The Irony Analyst",
        "immersion_range": [1.0, 1.0],
    },
    "lit-youth": {
        "model": PRO_MODEL,
        "persona": "The Childhood Scholar",
        "immersion_range": [1.0, 1.0],
    },
    "lit-doc": {
        "model": PRO_MODEL,
        "persona": "The Witness Documentarian",
        "immersion_range": [1.0, 1.0],
    },
    "lit-drama": {
        "model": PRO_MODEL,
        "persona": "The Avant-Garde Playwright",
        "immersion_range": [1.0, 1.0],
    },
    "lit-crimea": {
        "model": PRO_MODEL,
        "persona": "The Crimean Narratologist",
        "immersion_range": [1.0, 1.0],
    },

    # --- Scholar Tracks ---
    "ruth": {
        "model": PRO_MODEL,
        "persona": "The Baroque Scholar",
        "immersion_range": [1.0, 1.0],
    },
    "oes": {
        "model": PRO_MODEL,
        "persona": "The Paleographer",
        "immersion_range": [1.0, 1.0],
    },
}

# =============================================================================
# IMMERSION POLICY
# =============================================================================

USE_ULP_IMMERSION_DERIVATION: bool = True  # Calibrated 2026-05-13 from ULP S1-S6 replay.

# One authoritative source for live immersion policy across prompt generation
# and audit gates. A band defines:
# - the module range it covers
# - advisory immersion-percent telemetry
# - structural audit thresholds for deterministic immersion gates
# - the qualitative writer instruction injected into prompts
IMMERSION_POLICIES: dict[str, tuple[dict[str, Any], ...]] = {
    "a1": (
        {
            "key": "a1-m01-03",
            "max_module": 3,
            "min_pct": 5,
            "max_pct": 25,
            "rule": (
                "TARGET: 5-25% Ukrainian.\n"
                "LANGUAGE ROLES:\n"
                "- THEORY & EXPLANATION: Mostly English with Ukrainian words bolded inline.\n"
                "- UKRAINIAN CONTENT: Letters, sounds, words, and very short phrases inline.\n"
                "- DIALOGUES & READING PRACTICE: Optional ultra-short Ukrainian sentence blocks.\n"
                "- TABLES: Letter-sound and word-meaning tables are encouraged.\n"
                "- STRUCTURAL RULE: English carries the explanation. Ukrainian appears in controlled chunks.\n"
                "Ukrainian sentences max 10 words."
            ),
        },
        {
            "key": "a1-m04-06",
            "max_module": 6,
            "min_pct": 8,
            "max_pct": 30,
            "rule": (
                "TARGET: 8-30% Ukrainian.\n"
                "LANGUAGE ROLES:\n"
                "- THEORY & EXPLANATION: Mostly English with Ukrainian words bolded inline.\n"
                "- UKRAINIAN CONTENT: Words and short phrases inline: \"The word **книга** means book.\"\n"
                "- DIALOGUES & READING PRACTICE: Short Ukrainian sentence blocks are encouraged.\n"
                "- TABLES: Simple identity, family, or stress-pattern tables.\n"
                "- STRUCTURAL RULE: English carries the explanation, but short Ukrainian examples should now appear regularly.\n"
                "Ukrainian sentences max 10 words."
            ),
        },
        {
            "key": "a1-m07-14",
            "max_module": 14,
            "min_pct": 10,
            "max_pct": 38,
            "rule": (
                "TARGET: 10-38% Ukrainian.\n"
                "LANGUAGE ROLES:\n"
                "- THEORY & EXPLANATION: English prose. Introduce Ukrainian grammar terms bolded with translation on first use.\n"
                "- UKRAINIAN CONTENT: Words and short phrases bolded inline: \"The word **книга** (book) is feminine.\"\n"
                "- TABLES: Vocabulary tables, word families, simple paradigm tables.\n"
                "- STRUCTURAL RULE: Every paragraph is English. Ukrainian words/phrases appear inline bolded. "
                "Full Ukrainian sentences (3+ words with a verb) go in tables or bulleted example lists with English gloss.\n"
                "Ukrainian sentences max 10 words."
            ),
        },
        {
            "key": "a1-m15-24",
            "max_module": 24,
            "min_pct": 15,
            "max_pct": 24,
            "rule": (
                "TARGET: 15-24% Ukrainian.\n"
                "LANGUAGE ROLES:\n"
                "- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.\n"
                "- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.\n"
                "- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.\n"
                "- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).\n"
                "- INLINE: Ukrainian words/phrases bolded in English prose.\n"
                "- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. "
                "Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes — never in flowing prose.\n"
                "Ukrainian sentences max 10 words. Mix container types."
            ),
        },
        {
            "key": "a1-m25-34",
            "max_module": 34,
            "min_pct": 15,
            "max_pct": 40,
            "rule": (
                "TARGET: 15-40% Ukrainian.\n"
                "LANGUAGE ROLES:\n"
                "- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.\n"
                "- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.\n"
                "- TABLES: Paradigm tables, case endings, vocabulary groups — all cells Ukrainian.\n"
                "- PATTERN BOXES: Show transformations: `книга → книгу` (nominative → accusative).\n"
                "- INLINE: Ukrainian words/phrases bolded in English prose.\n"
                "- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. "
                "Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes.\n"
                "Ukrainian sentences max 10 words. Mix container types."
            ),
        },
        {
            "key": "a1-m35-54",
            "max_module": 54,
            "min_pct": 20,
            "max_pct": 40,
            "rule": (
                "TARGET: 20-40% Ukrainian. HARD GATE — the audit rejects modules outside this range.\n"
                "LANGUAGE ROLES:\n"
                "- THEORY & EXPLANATION: English prose — brief, 2-3 sentences per concept. Explain once, then show Ukrainian.\n"
                "- UKRAINIAN NARRATIVE PARAGRAPHS: REQUIRED — minimum 1 per section. "
                "A 3-6 sentence Ukrainian paragraph demonstrating the concept in use, followed immediately by a "
                "`> *English translation*` blockquote.\n"
                "- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.\n"
                "- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss). Minimum 5 per rule.\n"
                "- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line. At least 1 dialogue per module.\n"
                "- PATTERN BOXES: Show transformations: `читати → читай → читайте`.\n"
                "- STRUCTURAL RULE: Every section must contain a Ukrainian narrative paragraph plus supporting tables/lists/dialogues/pattern boxes. "
                "Pure-English sections are forbidden at M35+.\n"
                "Ukrainian sentences max 12 words. Mix container types."
            ),
        },
        {
            "key": "a1-m55+",
            "max_module": 10_000,
            "min_pct": 25,
            "max_pct": 48,
            "rule": (
                "TARGET: 25-48% Ukrainian. HARD GATE — the audit rejects modules outside this range.\n"
                "LANGUAGE ROLES:\n"
                "- THEORY & EXPLANATION: English prose — brief, 2-3 sentences per concept. Explain once, then show Ukrainian.\n"
                "- UKRAINIAN NARRATIVE PARAGRAPHS: REQUIRED — minimum 2 per section. "
                "A 4-8 sentence Ukrainian paragraph demonstrating the concept in use, followed immediately by a "
                "`> *English translation*` blockquote.\n"
                "- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.\n"
                "- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss). Minimum 5 per rule.\n"
                "- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line. At least 1 dialogue per module.\n"
                "- PATTERN BOXES: Show transformations: `читати → читай → читайте`.\n"
                "- STRUCTURAL RULE: Every section must contain at least 2 Ukrainian narrative paragraphs plus supporting tables/lists/dialogues/pattern boxes. "
                "Pure-English sections are forbidden at M55+.\n"
                "Ukrainian sentences max 14 words. Mix container types."
            ),
        },
    ),
    "a2": (
        {
            "key": "a2-bridge",
            "max_module": 3,
            "min_pct": 20,
            "max_pct": 48,
            "rule": (
                "TARGET: 20-48% Ukrainian. Bridge modules continue from late A1.\n"
                "LANGUAGE ROLES:\n"
                "- THEORY: English prose for grammar review and metalanguage introduction.\n"
                "- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, pattern boxes.\n"
                "- HEADERS: Ukrainian with English in parentheses.\n"
                "- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix.\n"
                "These are review/bridge modules. English theory is expected. Ukrainian content comes from dialogues, example sentences, paradigm tables, and pattern boxes.\n"
                "A2 register only. Concrete everyday vocabulary. No literary/poetic language. "
                "Ukrainian sentences max 15 words. Max 2 clauses. "
                "All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles."
            ),
        },
        {
            "key": "a2-ramp",
            "max_module": 7,
            "min_pct": 30,
            "max_pct": 55,
            "rule": (
                "TARGET: 30-55% Ukrainian. HARD GATE — the audit rejects modules outside this range.\n"
                "LANGUAGE ROLES:\n"
                "- THEORY: English prose for grammar explanations — keep short (2-3 sentences per concept, then immediately show Ukrainian examples).\n"
                "- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, cultural context.\n"
                "- HEADERS: Ukrainian with English in parentheses.\n"
                "- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix.\n"
                "HOW TO REACH THE TARGET:\n"
                "1. Include 2-3 multi-turn dialogues (8+ lines each) spread through the module.\n"
                "2. After every grammar explanation, immediately show 5+ Ukrainian example sentences with translations.\n"
                "3. Add a `### Читаємо українською` block in each section — 5-8 connected Ukrainian sentences.\n"
                "4. Use `:::tip` callouts with Ukrainian mnemonic phrases and cultural notes.\n"
                "5. Use paradigm tables with Ukrainian content, not just endings.\n"
                "A2 register only. Concrete everyday vocabulary. No literary/poetic language. "
                "Ukrainian sentences max 15 words. Max 2 clauses. "
                "All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles."
            ),
        },
        {
            "key": "a2-m01-20",
            "max_module": 20,
            "min_pct": 40,
            "max_pct": 70,
            "rule": (
                "TARGET: 40-70% Ukrainian. HARD GATE — the audit rejects modules outside this range.\n"
                "LANGUAGE ROLES:\n"
                "- THEORY: English prose for grammar explanations — keep these short (2-3 sentences max per concept).\n"
                "- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, cultural context.\n"
                "- HEADERS: Ukrainian with English in parentheses.\n"
                "- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix languages within a sentence.\n"
                "HOW TO REACH THE TARGET:\n"
                "1. After every grammar explanation, add a `Читаємо українською` block: 4-6 full Ukrainian sentences demonstrating the concept.\n"
                "2. Include 3-4 multi-turn dialogues (6+ lines each) spread through the module.\n"
                "3. Use pattern boxes showing Ukrainian transformations: `стіл → стола → на столі`.\n"
                "4. Section introductions can be 1-2 Ukrainian sentences before the English theory.\n"
                "5. `:::tip` and `:::note` callouts should contain Ukrainian mnemonic phrases.\n"
                "A2 register only. Concrete everyday vocabulary. No literary/poetic language. No abstract nouns. "
                "Ukrainian sentences max 15 words. Max 2 clauses. "
                "All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles."
            ),
        },
        {
            "key": "a2-m21-50",
            "max_module": 50,
            "min_pct": 50,
            "max_pct": 80,
            "rule": (
                "TARGET: 50-80% Ukrainian.\n"
                "LANGUAGE ROLES:\n"
                "- PRIMARY: Ukrainian for all content — dialogues, examples, section intros, cultural context.\n"
                "- ENGLISH: Only for abstract grammar concepts that need explicit explanation.\n"
                "- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English. Dialogues, examples, and section intros stay Ukrainian-only.\n"
                "A2 register. Concrete everyday vocabulary. No literary language, no metaphors. "
                "Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. "
                "Simple subordinate clauses only. Aspect pairs introduced. No participles."
            ),
        },
        {
            "key": "a2-m51-70",
            "max_module": 10_000,
            "min_pct": 65,
            "max_pct": 90,
            "rule": (
                "TARGET: 65-90% Ukrainian. This is the final A2 immersion ramp into B1.\n"
                "LANGUAGE ROLES:\n"
                "- PRIMARY: Ukrainian for narrative, dialogues, examples, section intros, cultural notes, reading practice blocks, and learning callouts.\n"
                "- METALANGUAGE: For abstract grammar terms, you may provide ONE parenthetical English translation on first use only, "
                "for example `**доконаний вид** (perfective aspect)`. Subsequent uses must be Ukrainian only.\n"
                "- VOCABULARY TABLE: English glosses live there, not in prose.\n"
                "- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English. Never mix mid-sentence.\n"
                "HARD STRUCTURAL RULES:\n"
                "- FORBIDDEN: long English narrative paragraphs explaining grammar. If a concept needs more than one sentence of English scaffolding, "
                "put it in a `:::info` or `:::tip` callout, not the main prose.\n"
                "- FORBIDDEN: mirrored English translations after Ukrainian paragraphs or dialogues.\n"
                "- REQUIRED: learner is being prepared for B1, so grammar explanation should increasingly happen in simple Ukrainian.\n"
                "A2-late register only. Clear, natural, high-comprehension Ukrainian. "
                "Ukrainian sentences max 18 words. Max 2 clauses."
            ),
        },
    ),
    "b1": (
        {
            "key": "b1-core",
            "max_module": 10_000,
            "min_pct": 100,
            "max_pct": 100,
            "rule": (
                "Full Ukrainian immersion. No English in module body. "
                "Tab 2 (Словник) keeps L1 translations and idiom/expression "
                "explanations as the only English. Sentences max 30 words."
            ),
        },
    ),
    "default": (
        {
            "key": "b2+",
            "max_module": 10_000,
            "min_pct": 100,
            "max_pct": 100,
            "rule": (
                "Full Ukrainian immersion. No English in module body. "
                "Tab 2 (Словник) keeps L1 translations and idiom/expression "
                "explanations as the only English. Sentences max 35 words."
            ),
        },
    ),
}

# =============================================================================
# WIKI COVERAGE
# =============================================================================

# Placeholder thresholds for the Wiki Obligations Manifest gate. Calibrate with
# a Phase-B-style replay after the gate has real build telemetry.
WIKI_COVERAGE_HARD_FAIL = True
WIKI_COVERAGE_DEFAULT_MIN_PCT = 0.80
WIKI_COVERAGE_MIN_PCT_BY_LEVEL: dict[str, float] = {
    "a1": 0.80,
    "a2": 0.80,
    "b1": 0.80,
    "b2": 0.80,
    "c1": 0.80,
    "c2": 0.80,
    "hist": 0.80,
    "istorio": 0.80,
    "bio": 0.80,
    "lit": 0.80,
    "oes": 0.80,
    "ruth": 0.80,
}


_IMMERSION_STRUCTURAL_DEFAULTS: dict[str, Any] = {
    "min_uk_dialogue_lines": 0,
    "min_vocab_entries": 0,
    "min_uk_example_sentences": 0,
    "min_uk_tab3_activities": 0,
    "max_unsupported_uk_words": 10_000,
    "support_proximity": 8,
    "required_components": {},
}

_A1_COMPONENT_DENSITY = {"DialogueBox": (95, 100), "RuleBox": (0, 30)}
_A2_COMPONENT_DENSITY = {"DialogueBox": (95, 100), "RuleBox": (0, 40)}

_IMMERSION_STRUCTURAL_OVERRIDES: dict[str, dict[str, Any]] = {
    # Calibrated in audit/immersion-gate-calibration-2026-05-13/REPORT.html.
    "a1-m01-03": {
        "min_vocab_entries": 0,
        "min_uk_example_sentences": 0,
        "min_uk_tab3_activities": 5,
        "max_unsupported_uk_words": 10,
        "required_components": _A1_COMPONENT_DENSITY,
    },
    # Calibrated in audit/immersion-gate-calibration-2026-05-13/REPORT.html.
    "a1-m04-06": {
        "min_uk_dialogue_lines": 10,
        "min_vocab_entries": 0,
        "min_uk_example_sentences": 0,
        "min_uk_tab3_activities": 4,
        "max_unsupported_uk_words": 36,
        "required_components": _A1_COMPONENT_DENSITY,
    },
    # Calibrated in audit/immersion-gate-calibration-2026-05-13/REPORT.html.
    "a1-m07-14": {
        "min_uk_dialogue_lines": 13,
        "min_vocab_entries": 0,
        "min_uk_example_sentences": 6,
        "min_uk_tab3_activities": 3,
        "max_unsupported_uk_words": 68,
        "required_components": _A1_COMPONENT_DENSITY,
    },
    # Calibrated in audit/immersion-gate-calibration-2026-05-13/REPORT.html.
    # max_unsupported_uk_words bumped 28 → 50 → 80 on 2026-05-17 to
    # accommodate textbook-quote excerpts (the Захарійчук Grade 1 p.52
    # Євген paragraph that triggered both bumps regularly exceeds 50
    # words when the writer quotes it fully). 80 sits cleanly inside
    # the neighbor pattern (m04-06: 36, m07-14: 68, m25-34: 71) and is
    # the largest band in this family — appropriate for the m15-24
    # range where reflexive-verb modules quote multi-sentence
    # textbook narratives. Further bumps must be paired with a writer
    # prompt change to inline-gloss long quotes, not just more ceiling.
    "a1-m15-24": {
        "min_uk_dialogue_lines": 14,
        "min_vocab_entries": 0,
        "min_uk_example_sentences": 14,
        "min_uk_tab3_activities": 3,
        "max_unsupported_uk_words": 80,
        "required_components": _A1_COMPONENT_DENSITY,
    },
    # Calibrated in audit/immersion-gate-calibration-2026-05-13/REPORT.html.
    "a1-m25-34": {
        "min_uk_dialogue_lines": 9,
        "min_vocab_entries": 0,
        "min_uk_example_sentences": 6,
        "min_uk_tab3_activities": 3,
        "max_unsupported_uk_words": 71,
        "required_components": _A1_COMPONENT_DENSITY,
    },
    # Calibrated in audit/immersion-gate-calibration-2026-05-13/REPORT.html.
    "a1-m35-54": {
        "min_uk_dialogue_lines": 8,
        "min_vocab_entries": 0,
        "min_uk_example_sentences": 13,
        "min_uk_tab3_activities": 3,
        "max_unsupported_uk_words": 20,
        "required_components": _A1_COMPONENT_DENSITY,
    },
    # Calibrated in audit/immersion-gate-calibration-2026-05-13/REPORT.html.
    "a1-m55+": {
        "min_uk_dialogue_lines": 42,
        "min_vocab_entries": 0,
        "min_uk_example_sentences": 8,
        "min_uk_tab3_activities": 4,
        "max_unsupported_uk_words": 16,
        "required_components": _A1_COMPONENT_DENSITY,
    },
    "a2-bridge": {
        "min_uk_dialogue_lines": 2,
        "min_vocab_entries": 5,
        "min_uk_example_sentences": 5,
        "min_uk_tab3_activities": 1,
        "max_unsupported_uk_words": 15,
        "required_components": _A2_COMPONENT_DENSITY,
    },
    "a2-ramp": {
        "min_uk_dialogue_lines": 3,
        "min_vocab_entries": 6,
        "min_uk_example_sentences": 5,
        "min_uk_tab3_activities": 1,
        "max_unsupported_uk_words": 15,
        "required_components": _A2_COMPONENT_DENSITY,
    },
    "a2-m01-20": {
        "min_uk_dialogue_lines": 3,
        "min_vocab_entries": 8,
        "min_uk_example_sentences": 6,
        "min_uk_tab3_activities": 1,
        "max_unsupported_uk_words": 18,
        "required_components": _A2_COMPONENT_DENSITY,
    },
    "a2-m21-50": {
        "min_uk_dialogue_lines": 4,
        "min_vocab_entries": 8,
        "min_uk_example_sentences": 8,
        "min_uk_tab3_activities": 1,
        "max_unsupported_uk_words": 24,
        "required_components": _A2_COMPONENT_DENSITY,
    },
    "a2-m51-70": {
        "min_uk_dialogue_lines": 4,
        "min_vocab_entries": 8,
        "min_uk_example_sentences": 8,
        "min_uk_tab3_activities": 1,
        "max_unsupported_uk_words": 30,
        "required_components": _A2_COMPONENT_DENSITY,
    },
}


def _structural_immersion_rule(band: dict[str, Any]) -> str:
    old_rule = str(band["rule"])
    language_roles = old_rule
    if old_rule.startswith("TARGET:") and "\n" in old_rule:
        language_roles = old_rule.split("\n", 1)[1]
    structural = (
        "STRUCTURAL TARGETS (Phase A placeholders; Phase B calibrates):\n"
        f"- At least N UK dialogue lines (band: {band['min_uk_dialogue_lines']})\n"
        f"- At least N vocab entries (band: {band['min_vocab_entries']})\n"
        "- At least N UK example sentences in bulleted lists "
        f"(band: {band['min_uk_example_sentences']})\n"
        "- No UK-only run longer than K words without inline English support "
        f"(band: {band['max_unsupported_uk_words']})\n"
    )
    return structural + language_roles


def _ulp_practices_rule(track: str, module_num: int) -> str:
    """Return the compact ULP S1 presentation baseline for early A1 prompts."""
    if track != "a1" or module_num > 25:
        return ""
    return (
        "## ULP Presentation Pattern (A1 S1 baseline)\n"
        "Follow Anna Ohoiko's Ukrainian-first bilingual practices from "
        "`docs/best-practices/ulp-presentation-pattern.md`:\n"
        "Key checks: UK-first presentation; em-dash glosses; stress marks; "
        "named persona.\n"
        "1. EM-DASH GLOSS: every UK term in EN narration uses UK-first, "
        "em-dash gloss order: `Приві́т! — Hi!`; never gloss-first.\n"
        "2. SIDE-BY-SIDE BILINGUAL: narrative passages of 3+ sentences render "
        "as a two-column MD table (UK left, EN right) or `<DialogueBox>`-style "
        "side-by-side translation, not EN-only prose with a vocab dump.\n"
        "3. STRESS MARKS: every multi-syllable UK term has stress marks "
        "throughout Tab 1 prose, Tab 2 vocabulary, and Tab 3 activity prompts "
        "(`Приві́т`, `спра́ви`, `чудо́во`).\n"
        "4. DIALOGUE UK-ONLY: Tab 1 dialogues use pure Ukrainian named-speaker "
        "turns first. Translation or breakdown follows after the dialogue; do "
        "not interleave English inside the UK turn text.\n"
        "5. UK-ONLY Q&A: Tab 3 comprehension/recall stems and answer options "
        "are Ukrainian-only for content questions. English appears only as "
        "secondary UI support where needed.\n"
        "6. TRANSLATE -> WORKBOOK: EN-to-UK translation is a workbook/booster "
        "activity in Tab 3, never Tab 1 teaching prose.\n"
        "7. NAMED PERSONA: Tab 1 uses a named persona or named characters, with "
        "real Ukrainian places, foods, and activities instead of generic L2 "
        "fillers.\n"
        "A1 violations: English-first framing, transliteration tables, inline "
        "EN glossing inside dialogue turns, single-column EN narration with "
        "vocab dumps, and abstract 'the student must learn' framing."
    )


def _extend_immersion_band(raw_band: dict[str, Any]) -> dict[str, Any]:
    band = dict(raw_band)
    band["advisory_pct_min"] = int(band.pop("min_pct"))
    band["advisory_pct_max"] = int(band.pop("max_pct"))
    structural = {
        **_IMMERSION_STRUCTURAL_DEFAULTS,
        **_IMMERSION_STRUCTURAL_OVERRIDES.get(str(band["key"]), {}),
    }
    band.update(structural)
    band["required_components"] = dict(band["required_components"])
    band["rule"] = _structural_immersion_rule(band)
    return band


IMMERSION_POLICIES = {
    family: tuple(_extend_immersion_band(band) for band in bands)
    for family, bands in IMMERSION_POLICIES.items()
}

_ULP_VOCAB_KNEE_PER_BAND: dict[str, tuple[tuple[int, str], ...]] = {
    # Calibrated 2026-05-13 from ULP S1-S6 replay. Audit: audit/ulp-calibration-2026-05-13/REPORT.html
    "a1": (
        (0, "a1-m01-03"),
        (140, "a1-m04-06"),
        (242, "a1-m07-14"),
        (573, "a1-m15-24"),
        (593, "a1-m25-34"),
        (621, "a1-m35-54"),
        (647, "a1-m55+"),
    ),
    # Calibrated 2026-05-13 from ULP S1-S6 replay. Audit: audit/ulp-calibration-2026-05-13/REPORT.html
    "a2": (
        (0, "a2-bridge"),
        (1153, "a2-ramp"),
        (1292, "a2-m01-20"),
        (3622, "a2-m21-50"),
        (4470, "a2-m51-70"),
    ),
    # Calibrated 2026-05-13 from ULP S1-S6 replay. Audit: audit/ulp-calibration-2026-05-13/REPORT.html
    "b1": ((0, "b1-core"),),
    "default": ((0, "b2+"),),
}

_RECYCLE_CADENCE_DEFAULTS: dict[str, dict[str, int]] = {
    # Calibrated 2026-05-13 from ULP S1-S6 replay. Audit: audit/ulp-calibration-2026-05-13/REPORT.html
    "a1": {"recycle_window": 6, "recycle_floor": 3},
    "a2": {"recycle_window": 8, "recycle_floor": 6},
    "default": {"recycle_window": 21, "recycle_floor": 12},
}

# =============================================================================
# GLOBAL CONSTRAINTS
# =============================================================================

OVERSHOOT_FACTOR = 1.5  # Default for B1+; A1/A2 use 1.0 (no overshoot)


def get_overshoot_factor(level: str) -> float:
    """A1/A2 should hit the target, not overshoot. B1+ benefits from 1.5x."""
    base = level.split('-')[0].upper() if level else ''
    if base in ('A1', 'A2'):
        return 1.0
    return OVERSHOOT_FACTOR
MAX_SENTENCE_LENGTH = 25  # Words
MANDATORY_CALLOUT_DENSITY = 6 # Callouts per module

# =============================================================================
# TURN SEQUENCE LOGIC
# =============================================================================

TURN_SEQUENCE = [1, 2, 3, 3.1, 3.5, 4, 5]

def get_next_turn(current_turn: float) -> float:
    """Returns the next turn in the sequence, or None if finished."""
    try:
        idx = TURN_SEQUENCE.index(current_turn)
        if idx + 1 < len(TURN_SEQUENCE):
            return TURN_SEQUENCE[idx + 1]
    except ValueError:
        pass
    return None

def get_config(track: str) -> dict[str, Any]:
    """Retrieves config for a specific track, falling back to default core config."""
    return TRACK_CONFIG.get(track, {
        "model": FLASH_MODEL,
        "persona": "The Helpful Neighbor",
        "immersion_range": [0.5, 1.0],
    })


def _immersion_track_key(track: str) -> str:
    """Map concrete tracks to the immersion policy family that governs them."""
    base = track.split("-")[0] if "-" in track else track
    if base in IMMERSION_POLICIES:
        return base
    return "default"


def _find_immersion_band(track: str, module_num: int) -> dict[str, Any]:
    """Return the band record for a track/module pair."""
    family = _immersion_track_key(track)
    bands: Sequence[dict[str, Any]] = IMMERSION_POLICIES[family]
    for band in bands:
        if module_num <= int(band["max_module"]):
            return band
    return bands[-1]


def _find_immersion_band_by_key(track: str, band_key: str) -> dict[str, Any]:
    family = _immersion_track_key(track)
    for band in IMMERSION_POLICIES[family]:
        if band["key"] == band_key:
            return band
    for band in IMMERSION_POLICIES["default"]:
        if band["key"] == band_key:
            return band
    return _find_immersion_band(track, 10_000)


def _learner_vocab_count(learner_state: dict | None) -> int:
    if not learner_state:
        return 0
    cumulative = learner_state.get("cumulative_vocabulary", [])
    if isinstance(cumulative, int):
        return cumulative
    if isinstance(cumulative, (list, tuple, set)):
        return len(cumulative)
    return 0


def _has_learner_vocab_signal(learner_state: dict | None) -> bool:
    return isinstance(learner_state, dict) and "cumulative_vocabulary" in learner_state


def compute_immersion_band(
    track: str,
    module_num: int,
    learner_state: dict | None = None,
) -> dict[str, Any]:
    """Compute the immersion band for module N derived from cumulative-vocab state.

    When USE_ULP_IMMERSION_DERIVATION is False, this is a thin shim around the
    static IMMERSION_POLICIES fallback. When True, it derives the band from
    learner_state's cumulative_vocabulary count using calibration constants.
    """
    if not USE_ULP_IMMERSION_DERIVATION or not _has_learner_vocab_signal(learner_state):
        return dict(_find_immersion_band(track, module_num))

    family = _immersion_track_key(track)
    knees = _ULP_VOCAB_KNEE_PER_BAND.get(family, _ULP_VOCAB_KNEE_PER_BAND["default"])
    vocab_count = _learner_vocab_count(learner_state)
    selected_key = knees[0][1]
    for threshold, band_key in knees:
        if vocab_count >= threshold:
            selected_key = band_key
        else:
            break
    return dict(_find_immersion_band_by_key(track, selected_key))


def get_recycle_cadence_policy(track: str) -> dict[str, int]:
    """Return placeholder recycle-cadence policy for a track."""
    family = _immersion_track_key(track)
    return dict(_RECYCLE_CADENCE_DEFAULTS.get(family, _RECYCLE_CADENCE_DEFAULTS["default"]))


def get_immersion_policy(
    track: str,
    module_num: int,
    learner_state: dict | None = None,
) -> dict[str, Any]:
    """Return the full immersion policy dict for a track/module pair."""
    return compute_immersion_band(track, module_num, learner_state)


def get_immersion_range(
    track: str,
    module_num: int,
    learner_state: dict | None = None,
) -> tuple[int, int]:
    """Return advisory immersion percent telemetry range for a track/module pair."""
    band = compute_immersion_band(track, module_num, learner_state)
    return int(band["advisory_pct_min"]), int(band["advisory_pct_max"])


def get_immersion_structural(
    track: str,
    module_num: int,
    learner_state: dict | None = None,
) -> dict[str, Any]:
    """Return structural immersion thresholds for a track/module pair."""
    band = compute_immersion_band(track, module_num, learner_state)
    return {
        key: band[key]
        for key in (
            "min_uk_dialogue_lines",
            "min_vocab_entries",
            "min_uk_example_sentences",
            "min_uk_tab3_activities",
            "max_unsupported_uk_words",
            "support_proximity",
            "required_components",
        )
    }


def get_immersion_rule(
    track: str,
    module_num: int,
    learner_state: dict | None = None,
) -> str:
    """Return the writer-facing immersion instruction for a track/module pair."""
    rule = str(compute_immersion_band(track, module_num, learner_state)["rule"])
    ulp_rule = _ulp_practices_rule(track, module_num)
    if ulp_rule:
        return f"{rule}\n\n{ulp_rule}"
    return rule

if __name__ == "__main__":
    # Simple CLI test
    import sys
    if len(sys.argv) > 1:
        print(get_config(sys.argv[1]))
    else:
        print("Usage: python scripts/config.py <track_name>")
