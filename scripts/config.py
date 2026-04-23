"""
Learn Ukrainian Project - Central Configuration Brain

This file stores track-level constants, model mappings, pedagogical floors,
and live immersion policy. It is the source of truth for the dispatcher,
watcher, writer, and audit scripts.
"""

from collections.abc import Sequence
from typing import Any

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
        "immersion_range": [0.85, 1.0],
    },
    "b2": {
        "model": FLASH_MODEL,
        "persona": "The Urbanist",
        "immersion_range": [0.95, 1.0],
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
        "immersion_range": [0.95, 1.0],
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

    # --- Scholar Tracks (Ancient/Professional) ---
    "ruth": {
        "model": PRO_MODEL,
        "persona": "The Baroque Scholar",
        "immersion_range": [0.97, 1.0],
    },
    "oes": {
        "model": PRO_MODEL,
        "persona": "The Paleographer",
        "immersion_range": [0.97, 1.0],
    },
    "b2-pro": {
        "model": PRO_MODEL,
        "persona": "The Professional Coach",
        "immersion_range": [0.95, 1.0],
    },
    "c1-pro": {
        "model": PRO_MODEL,
        "persona": "The Corporate Strategist",
        "immersion_range": [1.0, 1.0],
    },
}

# =============================================================================
# IMMERSION POLICY
# =============================================================================

# One authoritative source for live immersion policy across prompt generation
# and audit gates. A band defines:
# - the module range it covers
# - the quantitative audit threshold (min/max immersion)
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
            "max_pct": 35,
            "rule": (
                "TARGET: 15-35% Ukrainian.\n"
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
            "key": "b1-m01-05",
            "max_module": 5,
            "min_pct": 75,
            "max_pct": 100,
            "rule": (
                "TARGET: 75-100% Ukrainian. This is the B1 entry band continuing from late A2.\n"
                "LANGUAGE ROLES:\n"
                "- THEORY & EXPLANATION: Ukrainian by default. Explain grammar in clear Ukrainian using Ukrainian linguistic terms.\n"
                "- EXAMPLES & NARRATIVE: 100% Ukrainian.\n"
                "- DIALOGUES: 100% Ukrainian. No inline English glosses.\n"
                "- RESCUE ENGLISH: Occasional rescue notes are allowed only when absolutely necessary for first-use abstraction. Keep them minimal.\n"
                "- STRUCTURAL RULE: Ukrainian is the default language of the module. English is a rare support tool, not a parallel track.\n"
                "FORBIDDEN: mirrored paragraph translations or English blockquotes after Ukrainian prose.\n"
                "Ukrainian sentences max 30 words."
            ),
        },
        {
            "key": "b1-core",
            "max_module": 10_000,
            "min_pct": 85,
            "max_pct": 100,
            "rule": (
                "TARGET: 85-100% Ukrainian.\n"
                "LANGUAGE ROLES:\n"
                "- THEORY & EXPLANATION: Ukrainian prose. Explain grammar in Ukrainian using Ukrainian linguistic terms (дієслово, відмінок, недоконаний вид).\n"
                "- EXAMPLES & NARRATIVE: 100% Ukrainian.\n"
                "- DIALOGUES: 100% Ukrainian. No inline English glosses.\n"
                "- METALANGUAGE: For abstract grammar terms, you may provide ONE parenthetical English translation on first use only, "
                "for example `**видова пара** (aspectual pair)`. Subsequent uses must be Ukrainian only.\n"
                "HARD STRUCTURAL RULES:\n"
                "- FORBIDDEN: English translation blockquotes after Ukrainian paragraphs.\n"
                "- FORBIDDEN: mirrored English paragraphs translating Ukrainian prose.\n"
                "- FORBIDDEN: long English scaffolding in the main body. If a rescue note is genuinely required, keep it brief and exceptional.\n"
                "B1 is Ukrainian by default. English appears only as occasional rescue support, never as the main teaching language.\n"
                "Ukrainian sentences max 30 words."
            ),
        },
    ),
    "default": (
        {
            "key": "b2+",
            "max_module": 10_000,
            "min_pct": 95,
            "max_pct": 100,
            "rule": "Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words.",
        },
    ),
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


def get_immersion_policy(track: str, module_num: int) -> dict[str, Any]:
    """Return the full immersion policy dict for a track/module pair."""
    return dict(_find_immersion_band(track, module_num))


def get_immersion_range(track: str, module_num: int) -> tuple[int, int]:
    """Return the quantitative immersion gate range for a track/module pair."""
    band = _find_immersion_band(track, module_num)
    return int(band["min_pct"]), int(band["max_pct"])


def get_immersion_rule(track: str, module_num: int) -> str:
    """Return the writer-facing immersion instruction for a track/module pair."""
    return str(_find_immersion_band(track, module_num)["rule"])

if __name__ == "__main__":
    # Simple CLI test
    import sys
    if len(sys.argv) > 1:
        print(get_config(sys.argv[1]))
    else:
        print("Usage: python scripts/config.py <track_name>")
