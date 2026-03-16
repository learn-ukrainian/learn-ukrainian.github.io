"""Config tables and resolver functions for the build pipeline.

Data-only config (TRACK_SKILLS, IMMERSION_RULES, etc.) and pure accessor functions.
Extracted from pipeline_lib.py for separation of concerns.
"""

from __future__ import annotations

import textwrap

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
    "a1-m01-06": (
        "TARGET: 5-15% Ukrainian.\n"
        "LANGUAGE ROLES:\n"
        "- THEORY & EXPLANATION: Mostly English with Ukrainian words bolded inline.\n"
        "- UKRAINIAN CONTENT: Words and short phrases inline: \"The letter **Н** looks like H but sounds like N.\"\n"
        "- DIALOGUES & READING PRACTICE: Short Ukrainian sentences in blockquotes are encouraged.\n"
        "- TABLES: Simple letter-sound or word-meaning tables.\n"
        "Ukrainian sentences max 10 words."
    ),
    "a1-m07-14": (
        "TARGET: 10-20% Ukrainian.\n"
        "LANGUAGE ROLES:\n"
        "- THEORY & EXPLANATION: English prose. Introduce Ukrainian grammar terms bolded with translation on first use.\n"
        "- UKRAINIAN CONTENT: Words and short phrases bolded inline: \"The word **книга** (book) is feminine.\"\n"
        "- TABLES: Vocabulary tables, word families, simple paradigm tables.\n"
        "- STRUCTURAL RULE: Every paragraph is English. Ukrainian words/phrases appear inline bolded. "
        "Full Ukrainian sentences (3+ words with a verb) go in tables or bulleted example lists with English gloss.\n"
        "Ukrainian sentences max 10 words."
    ),
    "a1-m15-24": (
        "TARGET: 15-25% Ukrainian.\n"
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
    "a1-m25-34": (
        "TARGET: 15-30% Ukrainian.\n"
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
    "a1-m35-54": (
        "TARGET: 20-35% Ukrainian.\n"
        "LANGUAGE ROLES:\n"
        "- THEORY & EXPLANATION: English prose — brief and clear. Show, don't tell.\n"
        "- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.\n"
        "- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).\n"
        "- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.\n"
        "- PATTERN BOXES: Show transformations: `читати → читай → читайте`.\n"
        "- INLINE: Ukrainian words/phrases bolded in English prose.\n"
        "- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. "
        "Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes.\n"
        "Ukrainian sentences max 10 words. Mix container types."
    ),
    "a1-m55+": (
        "TARGET: 25-40% Ukrainian.\n"
        "LANGUAGE ROLES:\n"
        "- THEORY & EXPLANATION: English prose — brief and clear. Show, don't tell.\n"
        "- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.\n"
        "- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).\n"
        "- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.\n"
        "- PATTERN BOXES: Show transformations: `читати → читай → читайте`.\n"
        "- INLINE: Ukrainian words/phrases bolded in English prose.\n"
        "- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. "
        "Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes.\n"
        "Ukrainian sentences max 10 words. Mix container types."
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
        "GRAMMAR CONSTRAINTS (A1.1 — First Contact):\n"
        "Keep grammar simple — this is the learner's first exposure to Ukrainian.\n\n"
        "ALLOWED:\n"
        "- Це + noun: «Це кіт», «Це мама»\n"
        "- Simple present tense (я читаю, я бачу)\n"
        "- Basic imperatives (читай, слухай, дивись)\n"
        "- Question words: «Хто це?», «Що це?», «Де?»\n"
        "- Так/Ні answers\n"
        "- Adj + noun: «великий дім», «нова книга»\n\n"
        "BANNED (too complex for first contact):\n"
        "- Past tense, future tense, conditionals\n"
        "- Participles, passive voice, gerunds\n"
        "- Compound/complex sentences — max 1 clause per sentence (no і/а/але joining clauses)\n"
        "- Do not explicitly teach cases — use nouns in natural contexts\n\n"
        "METALANGUAGE:\n"
        "- ALL terminology in English first, Ukrainian in parentheses: 'vowels (голосні)'\n"
        "- Section headings MUST be bilingual (e.g., '## Голосні — Vowels')\n"
        "- Explanatory prose in English, Ukrainian for examples and dialogues"
    ),
    "A1.2": (
        "GRAMMAR CONSTRAINTS (A1.2 — Verbs & Sentences):\n"
        "Present tense verbs are fully available. Simple sentences.\n\n"
        "ALLOWED:\n"
        "- Present tense (я читаю, він іде, вони мають)\n"
        "- Basic imperatives (читай/читайте, слухай/слухайте, дивись/дивіться)\n"
        "- Infinitives in simple contexts (можна читати, треба слухати)\n"
        "- Simple questions and answers\n\n"
        "BANNED (too complex for A1.2):\n"
        "- Past tense, future tense, conditionals\n"
        "- Participles, passive voice\n"
        "- Complex subordinate clauses"
    ),
    "A1.3": (
        "GRAMMAR CONSTRAINTS (A1.3 — Cases & Navigation):\n"
        "Present tense and imperatives available. Cases being introduced.\n\n"
        "ALLOWED: present tense, imperatives, infinitives, basic cases\n"
        "BANNED: participles, passive voice, complex subordination"
    ),
    "A1.4": (
        "GRAMMAR CONSTRAINTS (A1.4 — Tenses & Daily Life):\n"
        "Past tense and future tense introduced. All present tense available.\n"
        "Imperatives available.\n\n"
        "BANNED: participles, passive voice, complex subordination"
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
    phase_raw = plan.get("phase", "")
    phase_str = str(phase_raw) if phase_raw else ""
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
    """Build an explicit list of required H2 section titles from the content outline.

    Auto-appends Summary/Підсумок if missing from the outline — the audit
    structure gate requires it and 35+ A2 plans omit it.
    """
    if not ctx.content_outline:
        return ""
    titles = []
    has_summary = False
    for section in ctx.content_outline:
        name = section.get("section") or section.get("title", "")
        words = section.get("words", 0)
        points = section.get("points", [])
        if name:
            entry = f"- `## {name}` (~{words} words)"
            if points:
                entry += "\n" + "\n".join(f"  - {p}" for p in points)
            titles.append(entry)
            if "підсумок" in name.lower() or "summary" in name.lower():
                has_summary = True
    if not titles:
        return ""

    # Auto-inject Summary if the plan doesn't include it
    if not has_summary:
        summary_heading = (
            "Summary" if (ctx.track.startswith("a1") and ctx.module_num <= 4)
            else "Підсумок — Summary" if (ctx.track.startswith("a1") and ctx.module_num <= 14)
            else "Підсумок"
        )
        titles.append(f"- `## {summary_heading}` (~150 words) — recap + 3-4 self-check questions")

    return (
        "## REQUIRED H2 Sections and Points (MANDATORY)\n\n"
        "Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. "
        "Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says "
        "*айтішник*, use *айтішник*, not a synonym).\n\n"
        + "\n".join(titles)
    )


def _is_checkpoint_module(slug: str) -> bool:
    """Check if a module is a checkpoint based on its slug."""
    return "checkpoint" in slug


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
    phase_raw = ctx.plan.get("phase", "") if ctx.plan else ""
    phase_str = str(phase_raw) if phase_raw else ""
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
        if module_num <= 6:
            return IMMERSION_RULES["a1-m01-06"]
        elif module_num <= 14:
            return IMMERSION_RULES["a1-m07-14"]
        elif module_num <= 24:
            return IMMERSION_RULES["a1-m15-24"]
        elif module_num <= 34:
            return IMMERSION_RULES["a1-m25-34"]
        elif module_num <= 54:
            return IMMERSION_RULES["a1-m35-54"]
        else:
            return IMMERSION_RULES["a1-m55+"]
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

