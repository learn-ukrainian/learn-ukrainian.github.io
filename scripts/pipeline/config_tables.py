"""Config tables and resolver functions for the build pipeline.

Data-only config (TRACK_SKILLS, IMMERSION_RULES, etc.) and pure accessor functions.
Extracted from pipeline_lib.py for separation of concerns.
"""

from __future__ import annotations

import textwrap

# ============================================================================
# 1. Config Tables (data only, no logic)
# ============================================================================

# ── Writer personas ──────────────────────────────────────────
# Single source of truth for all track personas.
# Tracks MUST match curriculum/l2-uk-en/curriculum.yaml (22 tracks).
# Used by: v6_build.py (write prompts), Gemini skills, review prompts.
TRACK_PERSONAS: dict[str, tuple[str, str]] = {
    # Core levels — ONE teacher, evolving tone.
    # Same primary identity throughout so the learner feels continuity.
    # The flavor shifts from patient hand-holding to academic challenge.
    "a1": ("Lead Ukrainian Instructor", "The Patient Guide"),
    "a2": ("Lead Ukrainian Instructor", "The Conversation Partner"),
    "b1": ("Lead Ukrainian Instructor", "The Cultural Mentor"),
    "b2": ("Lead Ukrainian Instructor", "The Senior Specialist"),
    "c1": ("Lead Ukrainian Instructor", "The Academic Advisor"),
    "c2": ("Lead Ukrainian Instructor", "The Demanding Colleague"),
    # Professional tracks (legacy — will be replaced by STEMS courses, see #862)
    "b2-pro": ("Lead Ukrainian Instructor", "The Professional Mentor"),
    "c1-pro": ("Lead Ukrainian Instructor", "The Professional Academic"),
    # Seminar tracks — distinct specialist voices (different people, different subjects)
    "hist": ("Professor of Ukrainian History", "The Decolonial Lecturer"),
    "bio": ("Professor of Ukrainian Biography", "The Archival Detective"),
    "istorio": ("Professor of Historiography", "The Source Critic"),
    "lit": ("Professor of Ukrainian Literature", "The Stylistic Critic"),
    "lit-essay": ("Professor of Ukrainian Literature", "The Essay Analyst"),
    "lit-hist-fic": ("Professor of Ukrainian Literature", "The Historical Fiction Scholar"),
    "lit-fantastika": ("Professor of Ukrainian Literature", "The Speculative Fiction Scholar"),
    "lit-war": ("Professor of Ukrainian Literature", "The War Literature Scholar"),
    "lit-humor": ("Professor of Ukrainian Literature", "The Satirist"),
    "lit-youth": ("Professor of Ukrainian Literature", "The Youth Literature Scholar"),
    "lit-drama": ("Professor of Ukrainian Drama", "The Theatre Scholar"),
    "folk": ("Professor of Ukrainian Folklore", "The Oral Tradition Scholar"),
    "oes": ("Professor of Old East Slavic", "The Paleographer"),
    "ruth": ("Professor of Ruthenian Studies", "The Baroque Scholar"),
}
DEFAULT_PERSONA: tuple[str, str] = ("Lead Ukrainian Instructor", "The Dedicated Teacher")

# Skill file mapping (which Gemini skill handles which track)
_SKILL_FILES: dict[str, str] = {
    "a1": "full-rebuild-core-a", "a2": "full-rebuild-core-a",
    "b1": "full-rebuild-core-a",  # early B1
    "b2": "full-rebuild-core-b", "b2-pro": "full-rebuild-core-b",
    "c1": "full-rebuild-core-b", "c1-pro": "full-rebuild-core-b",
    "c2": "full-rebuild-core-b",
    "bio": "full-rebuild-bio", "hist": "full-rebuild-hist",
    "istorio": "full-rebuild-istorio", "lit": "full-rebuild-lit",
    "oes": "full-rebuild-oes", "ruth": "full-rebuild-ruth",
    "folk": "full-rebuild-lit",  # folk uses lit skill
}

TRACK_SKILLS: dict[str, tuple[str, str, str]] = {
    # track_pattern: (skill_file, skill_identity, persona_flavor)
    # Auto-built from TRACK_PERSONAS + _SKILL_FILES
    k: (_SKILL_FILES.get(k.split("-")[0], "full-rebuild-core-b"), v[0], v[1])
    for k, v in TRACK_PERSONAS.items()
    if k in _SKILL_FILES or k.split("-")[0] in _SKILL_FILES
}
# B1 has early/late split for skills
TRACK_SKILLS["b1-early"] = ("full-rebuild-core-a", *TRACK_PERSONAS["b1"])
TRACK_SKILLS["b1-late"] = ("full-rebuild-core-b", *TRACK_PERSONAS["b1"])

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
    "a2-bridge": (
        "TARGET: 20-40% Ukrainian. Bridge modules continue from A1 (which ends at 20-41%).\n"
        "LANGUAGE ROLES:\n"
        "- THEORY: English prose for grammar review and metalanguage introduction.\n"
        "- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, pattern boxes.\n"
        "- HEADERS: Ukrainian with English in parentheses.\n"
        "- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix.\n"
        "These are review/bridge modules. English theory is expected. Ukrainian content comes from "
        "dialogues, example sentences, paradigm tables, and pattern boxes.\n"
        "A2 register ONLY. Concrete everyday vocabulary. No literary/poetic language. "
        "Ukrainian sentences max 15 words. Max 2 clauses. "
        "All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles."
    ),
    "a2-ramp": (
        "TARGET: 30-50% Ukrainian. ⚠️ HARD GATE — the audit REJECTS modules below 30%.\n"
        "LANGUAGE ROLES:\n"
        "- THEORY: English prose for grammar explanations — keep SHORT (2-3 sentences per concept, then IMMEDIATELY show Ukrainian examples).\n"
        "- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, cultural context.\n"
        "- HEADERS: Ukrainian with English in parentheses.\n"
        "- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix.\n"
        "⚠️ CRITICAL: You MUST write at least 30% Ukrainian text or the module will be REJECTED.\n"
        "HOW TO REACH 30-50% UKRAINIAN:\n"
        "1. Include 2-3 multi-turn dialogues (8+ lines each) spread through the module — these are your biggest Ukrainian contributors.\n"
        "2. After EVERY grammar explanation (max 2-3 English sentences), IMMEDIATELY show 5+ Ukrainian example sentences with translations.\n"
        "3. Add a '### Читаємо українською (Reading Practice)' block in EACH section — 5-8 connected Ukrainian sentences forming a mini-narrative.\n"
        "4. Use :::tip callouts with Ukrainian mnemonic phrases and cultural notes.\n"
        "5. Paradigm tables with Ukrainian content (not just endings but full phrases).\n"
        "SELF-CHECK: Before finishing, count Ukrainian text. If it feels like less than 1/3 of the module, add more Ukrainian dialogues and reading practice blocks.\n"
        "A2 register ONLY. Concrete everyday vocabulary. No literary/poetic language. "
        "Ukrainian sentences max 15 words. Max 2 clauses. "
        "All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles."
    ),
    "a2-m01-20": (
        "TARGET: 45-65% Ukrainian. THIS IS A HARD GATE — the audit REJECTS modules below 45%.\n"
        "LANGUAGE ROLES:\n"
        "- THEORY: English prose for grammar explanations — keep these SHORT (2-3 sentences max per concept).\n"
        "- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, cultural context.\n"
        "- HEADERS: Ukrainian with English in parentheses.\n"
        "- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix languages within a sentence.\n"
        "HOW TO REACH 45-65% UKRAINIAN (mandatory techniques):\n"
        "1. After EVERY grammar explanation, add a «Читаємо українською» block: 4-6 full Ukrainian sentences "
        "demonstrating the concept just explained. These are comprehensible input, not exercises.\n"
        "2. Include 3-4 multi-turn dialogues (6+ lines each) spread through the module. "
        "Dialogues are the fastest way to boost Ukrainian content.\n"
        "3. Pattern boxes showing Ukrainian transformations: «стіл → стола → на столі».\n"
        "4. Section introductions can be 1-2 Ukrainian sentences before the English theory.\n"
        "5. :::tip and :::note callout boxes should contain Ukrainian mnemonic phrases.\n"
        "If your module has long English paragraphs without Ukrainian blocks between them, "
        "you are below target. Every English paragraph should be followed by Ukrainian content.\n"
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
    "b1-core": (
        "Full Ukrainian immersion. Grammar explained IN Ukrainian. "
        "English only for disambiguation of false friends. Sentences max 30 words."
    ),
    "b2+": (
        "Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words."
    ),
}

# Golden fragments — level-appropriate tone/style examples injected into writing prompts.
# These show the LLM HOW to write, not just what rules to follow.
# 4 bands mapped to immersion progression.
GOLDEN_FRAGMENTS: dict[str, str] = {
    "early-beginner": textwrap.dedent("""\
        ### Style Reference (match this tone and structure)

        Look at the text on this page. What you are seeing are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the first grade: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери**. We hear and pronounce sounds, but we see and write letters.

        These friendly letters are **А**, **О**, **К**, **М**, and **Т**. Because they are so familiar, you can start reading real Ukrainian words immediately. Look at the word **мама**. It means mother, and you already know how to read it. Now look at **тато**. It means father.

        *Note: English prose dominates. Ukrainian words appear bolded inline. Short Ukrainian sentences illustrate one concept at a time. No conjugated verbs. Tables and bulleted lists for vocabulary.*"""),

    "late-beginner": textwrap.dedent("""\
        ### Style Reference (match this tone and structure)

        > **(У магазині / At the store)**
        > — Добрий день! Скільки коштує хліб? (Good day! How much does the bread cost?)
        > — Дванадцять гривень. (Twelve hryvnias.)
        > — Дякую! Ось, будь ласка. (Thanks! Here you go.)

        Notice that the shopkeeper uses **Добрий день** — the formal greeting for strangers. If this were a friend, they would say **Привіт** instead.

        The word **скільки** (how much/how many) is one of the most useful question words. It always pairs with the genitive case: **скільки коштує** (how much does it cost), **скільки часу** (how much time).

        *Note: Short dialogues in Ukrainian with per-line English glosses. Grammar explained in English. Ukrainian sentences in blockquotes and bulleted lists.*"""),

    "intermediate": textwrap.dedent("""\
        ### Style Reference (match this tone and structure)

        Дієприкметники — це особлива форма дієслова, яка поєднує ознаки дієслова та прикметника. Вони відповідають на питання «який?» і змінюються за родами, числами та відмінками, як звичайні прикметники.

        Порівняйте:
        - **написаний лист** (a written letter) — пасивний дієприкметник
        - **зігрітий чай** (warmed tea) — пасивний дієприкметник

        :::tip
        В українській мові активні дієприкметники теперішнього часу (на -учий/-ючий) вважаються стилістично небажаними. Замість «працюючий лікар» краще сказати «лікар, який працює».
        :::

        *Note: Grammar explained IN Ukrainian using Ukrainian linguistic terms. English appears only in parenthetical translations for disambiguation. Callout boxes in Ukrainian.*"""),

    "advanced": textwrap.dedent("""\
        ### Style Reference (match this tone and structure)

        Функціональні стилі української мови — це різновиди літературної мови, що обслуговують певні сфери суспільного життя. Кожен стиль має власну лексику, синтаксичні конструкції та комунікативну мету.

        Офіційно-діловий стиль характеризується чіткістю формулювань, стандартизованою лексикою та відсутністю емоційного забарвлення. Порівняймо:

        | Розмовний стиль | Офіційно-діловий стиль |
        |---|---|
        | Я хочу звільнитися. | Прошу звільнити мене з посади за власним бажанням. |
        | Дайте мені довідку. | Прошу надати довідку про місце проживання. |

        Зверніть увагу на ключову відмінність: розмовний стиль використовує пряме звертання та скорочені конструкції, тоді як діловий стиль послуговується безособовими формами та канцелярськими зворотами.

        *Note: 100% Ukrainian prose. Advanced syntax and register. Cultural and stylistic analysis in Ukrainian. No English.*"""),

    "seminar": textwrap.dedent("""\
        ### Style Reference (match this tone and structure)

        ## Текст для читання: Лесь Курбас і театр «Березіль»

        У 1922 році Лесь Курбас заснував у Києві мистецьке об'єднання «Березіль», яке за кілька років стало найвпливовішим театром в Україні. Курбас відкидав натуралістичний театр і шукав нові форми: експресіонізм, конструктивізм, політичний театр. Його постановка «Газ» за п'єсою Кайзера вразила глядачів несподіваною сценографією — замість декорацій актори працювали з абстрактними конструкціями та ритмічним рухом.

        У 1926 році «Березіль» переїхав до Харкова, тодішньої столиці УРСР. Саме тут Курбас поставив «Народного Малахія» за п'єсою Миколи Куліша — виставу, яку радянська критика назвала «націоналістичною». Це звинувачення стало початком кінця: у 1933 році Курбаса заарештували, а у 1937-му — розстріляли в урочищі Сандармох разом із сотнями інших українських митців.

        :::note
        **Завдання для роздуму:**
        Чому радянська влада сприймала експериментальний театр як загрозу? Яку роль відіграв театр «Березіль» у формуванні Розстріляного відродження?
        :::

        *Note: 100% Ukrainian academic prose. Dates, names, and historical context. Critical analysis prompt at the end. Decolonization through critical source analysis and centering the Ukrainian perspective.*"""),
}


LEVEL_CONSTRAINTS: dict[str, str] = {
    "a1": (
        "HARD GRAMMAR RULES (audit will reject violations):\n"
        "- Max 10 words per Ukrainian sentence (STRICT — count every word)\n"
        "- ONLY 1 clause per sentence (no compound sentences)\n"
        "- Dative case FORBIDDEN (no мені, тобі, йому, їй, вам, їм, -ові/-еві endings)\n"
        "  Exception: нам is taught as decodable vocabulary in M1 (reading drill word, not grammar)\n"
        "  Exception (M15 what-i-like): Dative forms мені/тобі/йому/їй/нам/вам/їм allowed\n"
        "    ONLY in the fixed construction «Мені подобається + noun/infinitive». Teach as a memorized\n"
        "    chunk — do NOT explain dative case rules or paradigms.\n"
        "- Instrumental case FORBIDDEN (no з другом, з мамою, -ом/-ою/-ем/-ею endings)\n"
        "  Exception: M37 introduces basic Instrumental 'з' (кава з молоком)\n"
        "- NO subordinate clauses: який/яка/яке, що-clause, коли, якщо, тому що, бо, щоб, поки are ALL BANNED\n"
        "- Only imperfective aspect verbs\n"
        "- No participles\n"
        "- Allowed cases: Nominative, Accusative, Locative (from M30), Genitive (basics), Vocative"
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
_A1_PHASE_CONSTRAINTS_PHONETICS = (
    "GRAMMAR CONSTRAINTS (A1.1 — Phonetics, M01-M03):\n"
    "NO CONJUGATED VERBS. NO IMPERATIVES. This is the phonetics phase.\n\n"
    "VIDEO-FIRST PEDAGOGY (M01-M03 ONLY):\n"
    "The learner CANNOT read Cyrillic yet. Letters are introduced BY VIDEO, not by text.\n"
    "When the plan provides Anna Ohoiko pronunciation videos, structure each letter as:\n"
    "1. Embed the video (the pipeline handles the actual embed)\n"
    "2. Short English note about what the learner just heard/saw\n"
    "3. Example words with English translations\n"
    "Do NOT write paragraphs describing how to position your tongue or shape your mouth.\n"
    "The video shows pronunciation — your job is to explain what the learner heard,\n"
    "point out patterns, and give practice words. Keep it short and visual.\n\n"
    "ALLOWED structures (Ukrainian examples only):\n"
    "- Це + noun: «Це кіт», «Це мама»\n"
    "- Noun + тут/там: «Мама тут», «Кіт там»\n"
    "- Question words: «Хто це?», «Що це?», «Де мама?»\n"
    "- Так/Ні: «Так, це кіт», «Ні, це не кіт»\n"
    "- Fixed phrases (memorized, no grammar): дякую, будь ласка, привіт\n\n"
    "BANNED: ALL verbs, past/future tense, cases, compound sentences\n\n"
    "STRESS MARKS: Do NOT add stress marks (´). Write plain Ukrainian.\n"
    "The pipeline adds stress marks deterministically after you write.\n\n"
    "METALANGUAGE: English prose, Ukrainian examples. Bilingual headings."
)

_A1_PHASE_CONSTRAINTS_GRAMMAR = (
    "GRAMMAR CONSTRAINTS (A1.1 — Communication, M04-M14):\n"
    "Keep grammar simple — first exposure to Ukrainian sentences.\n\n"
    "ALLOWED:\n"
    "- Це + noun: «Це кіт», «Це мама»\n"
    "- Fixed verbal phrases: «Мене звати», «У мене є», «Як справи?»\n"
    "- Simple present tense (я читаю, я бачу) — from M08+\n"
    "- Question words: «Хто це?», «Що це?», «Де?», «Як?»\n"
    "- Так/Ні answers\n"
    "- Adj + noun: «великий дім», «нова книга» — from M09+\n"
    "- Possessive pronouns: мій/моя/моє — from M06+\n\n"
    "BANNED: Past/future tense, conditionals, participles, passive, gerunds,\n"
    "compound sentences (no і/а/але joining clauses)\n\n"
    "METALANGUAGE: English first, Ukrainian in parentheses. Bilingual headings."
)

_A1_PHASE_CONSTRAINTS: dict[str, str] = {
    "A1.1": _A1_PHASE_CONSTRAINTS_GRAMMAR,  # default for A1.1 — overridden for M01-M03
    "A1.2": (
        "GRAMMAR CONSTRAINTS (A1.2 — My World, M08-M14):\n"
        "Noun gender, adjective agreement, plurals, numbers, demonstratives.\n\n"
        "ALLOWED:\n"
        "- Це + noun, У мене є/немає\n"
        "- Adjective-noun agreement (nominative only)\n"
        "- Numbers 1-1000\n"
        "- Demonstratives цей/ця/це/ці\n"
        "- Question words: Який? Яка? Яке? Скільки?\n"
        "- Fixed verbal phrases from A1.1 (Мене звати, працювати)\n\n"
        "BANNED: Verb conjugation (taught in A1.3), past/future tense, cases beyond nominative,\n"
        "participles, passive voice, subordinate clauses"
    ),
    "A1.3": (
        "GRAMMAR CONSTRAINTS (A1.3 — Actions & Desires, M15-M21):\n"
        "Present tense verbs, modals, questions, reflexives.\n\n"
        "ALLOWED:\n"
        "- Present tense conjugation (both groups: -ати and -ити)\n"
        "- Modal verbs: хотіти, могти, мусити + infinitive\n"
        "- Question words: Хто? Що? Де? Куди? Коли? Чому?\n"
        "- Negation: не/ні\n"
        "- Reflexive verbs (-ся/-сь)\n"
        "- 'Мені подобається' as lexical chunk (NO dative grammar)\n\n"
        "BANNED: Past/future tense, cases beyond nominative,\n"
        "participles, passive voice, complex subordinate clauses"
    ),
    "A1.4": (
        "GRAMMAR CONSTRAINTS (A1.4 — Time & Nature, M22-M28):\n"
        "Time expressions, days, months, weather, daily routines.\n\n"
        "ALLOWED:\n"
        "- All present tense (from A1.3)\n"
        "- Time expressions as chunks (О першій, У понеділок)\n"
        "- Sequence adverbs (спочатку, потім, нарешті)\n"
        "- Impersonal weather constructions (Сьогодні холодно)\n\n"
        "BANNED: Past/future tense, case endings (time chunks only),\n"
        "participles, passive voice, complex subordination"
    ),
    "A1.5": (
        "GRAMMAR CONSTRAINTS (A1.5 — Places & Movement, M29-M36):\n"
        "Euphony, locative, accusative direction, genitive origin.\n\n"
        "ALLOWED:\n"
        "- Euphony rules (у/в, і/й, з/із/зі)\n"
        "- Locative case with в/у/на (Де?)\n"
        "- Accusative for direction (Куди?)\n"
        "- Genitive for origin (Звідки? З + genitive)\n"
        "- All present tense verbs\n\n"
        "BANNED: Past/future tense, dative, instrumental,\n"
        "participles, passive voice, complex subordination"
    ),
    "A1.6": (
        "GRAMMAR CONSTRAINTS (A1.6 — Food & Shopping, M37-M43):\n"
        "Instrumental з, accusative objects, genitive quantities.\n\n"
        "ALLOWED:\n"
        "- Instrumental case with 'з' (кава з молоком)\n"
        "- Accusative inanimate and animate objects\n"
        "- Genitive for quantities (кілограм цукру)\n"
        "- All cases from previous phases\n"
        "- All present tense verbs\n\n"
        "BANNED: Past/future tense, dative (until A1.7),\n"
        "participles, passive voice, complex subordination"
    ),
    "A1.7": (
        "GRAMMAR CONSTRAINTS (A1.7 — People & Communication, M44-M50):\n"
        "Vocative, imperative, dative, conjunctions, subordinate clauses.\n\n"
        "ALLOWED:\n"
        "- Vocative case (Олено! Тарасе!)\n"
        "- Imperative mood (Читай! Скажіть! Дайте!)\n"
        "- Dative case basics (мені, тобі, йому)\n"
        "- Conjunctions (і, а, але, бо, тому що)\n"
        "- Simple subordinate clauses (що, де, коли, якщо)\n"
        "- All cases and tenses from previous phases\n\n"
        "BANNED: Past/future tense, participles, passive voice"
    ),
    "A1.8": (
        "GRAMMAR CONSTRAINTS (A1.8 — Past, Future & Graduation, M51-M60):\n"
        "Full A1 grammar including past and future tense.\n\n"
        "ALLOWED:\n"
        "- Past tense (він читав, вона читала — gendered!)\n"
        "- Future tense (я буду читати, ми будемо працювати)\n"
        "- All cases, moods, and constructions from A1.1-A1.7\n"
        "- Combining tenses in connected speech\n\n"
        "BANNED: Participles, passive voice, complex literary constructions"
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

    # Override for phonetics modules M01-M03: no verbs at all (#979, updated #981)
    # M04+ (greetings, introductions) need fixed verbal phrases (звати, працювати)
    if phase_key == "A1.1" and module_num <= 3:
        phase_constraint = _A1_PHASE_CONSTRAINTS_PHONETICS

    return phase_constraint


# ---------------------------------------------------------------------------
# Decodable vocabulary removed in #841 — plan's vocabulary_hints is source of truth.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Level-aware structural rules for content phase
# ---------------------------------------------------------------------------


def _build_vocabulary_bank(ctx) -> str:
    """Build a flat Ukrainian vocabulary bank from plan vocabulary_hints.

    Extracts the first Ukrainian word from each hint, providing a clean
    word list that Gemini should use instead of pulling from memory.
    This prevents Russianisms (дом→дім) by giving exact Ukrainian lemmas.

    Issue: #979 AC3
    """
    import re as _re
    if not ctx.plan:
        return "(No vocabulary bank available)"
    hints = ctx.plan.get("vocabulary_hints", {})
    if not hints:
        return "(No vocabulary bank available)"

    from pipeline.vocab_helpers import extract_vocab_words
    words = extract_vocab_words(hints)

    if not words:
        return "(No Ukrainian vocabulary found in plan)"

    return "**Allowed Ukrainian words:** " + ", ".join(words)


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

    if phase_key == "A1.1" and ctx.module_num <= 3:
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

    elif phase_key == "A1.1":
        # A1.1 M04-M07: grammar modules, not alphabet/phonology
        pass

    # Default: grammar modules (A1.1 M04+ and A1.2+)
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

    if base == "a1" and module_num <= 3:
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
    if base == "a1" and module_num <= 3:
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
    if base == "a1" and module_num <= 3:
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


# ---------------------------------------------------------------------------
# Activity type taxonomy — where each type can appear
# ---------------------------------------------------------------------------
# INLINE = short, focused checks placed mid-prose after a teaching point
# WORKBOOK = deeper, longer practice in the dedicated Зошит tab
#
# Some types only work in one context. This is enforced by the validator
# independently of per-level allowlists.
INLINE_ONLY_TYPES: set[str] = {
    "image-to-letter",      # beginner visual aid (A1 only)
    "letter-grid",          # alphabet reference (A1 only)
    "watch-and-repeat",     # pronunciation video (A1-A2)
}

WORKBOOK_ONLY_TYPES: set[str] = {
    "essay-response",       # 50-500w free writing — breaks prose flow
    "reading",              # long passage + questions — too long for inline
    "cloze",                # 14+ blank passage — too disruptive inline
    "critical-analysis",    # deep argumentative response
    "source-evaluation",    # scholarly evaluation of primary source
    "debate",               # multi-turn argumentative exchange
    "comparative-study",    # multi-text comparison
    "authorial-intent",     # deep interpretation of author's choices
    "translation-critique", # compare two translations of same text
    "etymology-trace",      # historical linguistics exercise
    "paleography-analysis", # script/manuscript analysis
    "transcription",        # transcribe from old orthography
    "dialect-comparison",   # compare dialect features
}
# All other types are BOTH_CONTEXTS — work in inline or workbook depending on
# level-specific config.


ACTIVITY_CONFIGS: dict[str, dict[str, str]] = {
    # =====================================================================
    # A1 — Decoding + Recognition (10 total: 4 inline + 6 workbook)
    # 1200-word modules, alphabet + first words + basic phrases
    # =====================================================================
    "a1": {
        "TOTAL_TARGET": "10",
        "INLINE_MIN": "4", "INLINE_MAX": "6",
        "WORKBOOK_MIN": "6", "WORKBOOK_MAX": "9",
        "ITEMS_MIN": "6",
        "VOCAB_COUNT_TARGET": "20",
        "INLINE_ALLOWED_TYPES": "image-to-letter, letter-grid, match-up, watch-and-repeat, quiz, true-false, fill-in, classify",
        "WORKBOOK_ALLOWED_TYPES": "fill-in, match-up, group-sort, anagram, unjumble, quiz, true-false, classify, divide-words, count-syllables, pick-syllables, observe, phrase-table, odd-one-out",
        "INLINE_PRIORITY_TYPES": "image-to-letter, match-up, fill-in, quiz, watch-and-repeat",
        "WORKBOOK_PRIORITY_TYPES": "fill-in, match-up, group-sort, anagram, unjumble",
        # Backward compat — union of inline + workbook, used by legacy callers
        "ACTIVITY_COUNT_TARGET": "10", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "15",
        "ALLOWED_ACTIVITY_TYPES": "image-to-letter, letter-grid, watch-and-repeat, match-up, quiz, true-false, fill-in, classify, group-sort, anagram, unjumble, divide-words, count-syllables, pick-syllables, observe, phrase-table, odd-one-out",
        "FORBIDDEN_ACTIVITY_TYPES": "cloze, error-correction, mark-the-words, translate, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, highlight-morphemes, grammar-identify, select",
        "REQUIRED_TYPES": "",
        "PRIORITY_TYPES": "fill-in, match-up, quiz, image-to-letter, watch-and-repeat",
    },
    # =====================================================================
    # A2 — Transformation + Basic Production (12 total: 4 inline + 8 workbook)
    # 2000-word modules, case drills, verb conjugation, basic dialogues
    # =====================================================================
    "a2": {
        "TOTAL_TARGET": "12",
        "INLINE_MIN": "4", "INLINE_MAX": "6",
        "WORKBOOK_MIN": "8", "WORKBOOK_MAX": "11",
        "ITEMS_MIN": "8",
        "VOCAB_COUNT_TARGET": "25",
        "INLINE_ALLOWED_TYPES": "quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words",
        "WORKBOOK_ALLOWED_TYPES": "cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, observe, phrase-table, quiz, true-false, mark-the-words",
        "INLINE_PRIORITY_TYPES": "fill-in, match-up, true-false, quiz",
        "WORKBOOK_PRIORITY_TYPES": "error-correction, cloze, unjumble, translate, fill-in",
        "ACTIVITY_COUNT_TARGET": "12", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "16",
        "ALLOWED_ACTIVITY_TYPES": "quiz, true-false, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction, group-sort, classify, translate, odd-one-out, observe, phrase-table",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify",
        "REQUIRED_TYPES": "",
        "PRIORITY_TYPES": "error-correction, cloze, fill-in, unjumble, translate",
    },
    # =====================================================================
    # B1 — Production + Analysis (16 total: 5 inline + 11 workbook)
    # 4000-word modules, full case system, aspect, motion verbs
    # =====================================================================
    "b1-core": {
        "TOTAL_TARGET": "16",
        "INLINE_MIN": "5", "INLINE_MAX": "7",
        "WORKBOOK_MIN": "11", "WORKBOOK_MAX": "15",
        "ITEMS_MIN": "8",
        "VOCAB_COUNT_TARGET": "30",
        "INLINE_ALLOWED_TYPES": "quiz, true-false, fill-in, match-up, group-sort, mark-the-words, grammar-identify, highlight-morphemes",
        "WORKBOOK_ALLOWED_TYPES": "cloze, error-correction, translate, fill-in, unjumble, essay-response, match-up, mark-the-words, grammar-identify, highlight-morphemes, group-sort",
        "INLINE_PRIORITY_TYPES": "fill-in, match-up, mark-the-words, quiz",
        "WORKBOOK_PRIORITY_TYPES": "cloze, error-correction, translate, essay-response, highlight-morphemes",
        "ACTIVITY_COUNT_TARGET": "16", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "20",
        "ALLOWED_ACTIVITY_TYPES": "quiz, true-false, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction, group-sort, translate, essay-response, grammar-identify, highlight-morphemes",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, critical-analysis, source-evaluation, reading, comparative-study, authorial-intent, debate, paleography-analysis, dialect-comparison, transcription, translation-critique, etymology-trace, classify, observe, phrase-table, odd-one-out",
        "REQUIRED_TYPES": "",
        "PRIORITY_TYPES": "cloze, error-correction, translate, mark-the-words, essay-response",
    },
    # =====================================================================
    # B2 — Register + Translation (16 total: 5 inline + 11 workbook)
    # 4000-word modules, stylistic awareness, formal/informal
    # =====================================================================
    "b2": {
        "TOTAL_TARGET": "16",
        "INLINE_MIN": "5", "INLINE_MAX": "7",
        "WORKBOOK_MIN": "11", "WORKBOOK_MAX": "15",
        "ITEMS_MIN": "8",
        "VOCAB_COUNT_TARGET": "30",
        "INLINE_ALLOWED_TYPES": "quiz, true-false, fill-in, match-up, mark-the-words, group-sort, grammar-identify",
        "WORKBOOK_ALLOWED_TYPES": "cloze, error-correction, translate, translation-critique, essay-response, unjumble, reading, grammar-identify, highlight-morphemes, mark-the-words, fill-in, match-up",
        "INLINE_PRIORITY_TYPES": "mark-the-words, fill-in, match-up, quiz",
        "WORKBOOK_PRIORITY_TYPES": "cloze, error-correction, translate, translation-critique, essay-response",
        "ACTIVITY_COUNT_TARGET": "16", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "20",
        "ALLOWED_ACTIVITY_TYPES": "quiz, true-false, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction, group-sort, translate, essay-response, grammar-identify, highlight-morphemes, reading, translation-critique",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, paleography-analysis, dialect-comparison, transcription, critical-analysis, debate, source-evaluation, etymology-trace, classify, observe, phrase-table, odd-one-out, select",
        "REQUIRED_TYPES": "",
        "PRIORITY_TYPES": "cloze, error-correction, translate, essay-response, translation-critique",
    },
    # =====================================================================
    # C1 — Stylistics + Sophisticated Production (16 total: 5 inline + 11 workbook)
    # 4000-word modules, academic register, literary features, morphology
    # =====================================================================
    "c1-core": {
        "TOTAL_TARGET": "16",
        "INLINE_MIN": "5", "INLINE_MAX": "7",
        "WORKBOOK_MIN": "11", "WORKBOOK_MAX": "15",
        "ITEMS_MIN": "8",
        "VOCAB_COUNT_TARGET": "30",
        "INLINE_ALLOWED_TYPES": "mark-the-words, fill-in, match-up, grammar-identify, quiz, highlight-morphemes",
        "WORKBOOK_ALLOWED_TYPES": "critical-analysis, essay-response, translation-critique, cloze, reading, error-correction, translate, etymology-trace, grammar-identify, highlight-morphemes, mark-the-words, fill-in",
        "INLINE_PRIORITY_TYPES": "mark-the-words, grammar-identify, fill-in, match-up",
        "WORKBOOK_PRIORITY_TYPES": "critical-analysis, essay-response, translation-critique, cloze, reading",
        "ACTIVITY_COUNT_TARGET": "16", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "20",
        "ALLOWED_ACTIVITY_TYPES": "quiz, fill-in, match-up, mark-the-words, cloze, error-correction, translate, essay-response, grammar-identify, highlight-morphemes, reading, critical-analysis, translation-critique, etymology-trace",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, true-false, unjumble, group-sort, classify, observe, phrase-table, odd-one-out, select, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, authorial-intent, comparative-study",
        "REQUIRED_TYPES": "",
        "PRIORITY_TYPES": "critical-analysis, essay-response, translation-critique, reading",
    },
    # =====================================================================
    # C2 — Mastery: Language-analytical (12 total: 4 inline + 8 workbook)
    # 5000-word modules, near-native mastery, rare constructions
    # Seminar-like but still about LANGUAGE mastery.
    # =====================================================================
    "c2": {
        "TOTAL_TARGET": "12",
        "INLINE_MIN": "4", "INLINE_MAX": "5",
        "WORKBOOK_MIN": "8", "WORKBOOK_MAX": "10",
        "ITEMS_MIN": "6",
        "VOCAB_COUNT_TARGET": "30",
        "INLINE_ALLOWED_TYPES": "mark-the-words, quiz, match-up, grammar-identify, fill-in",
        "WORKBOOK_ALLOWED_TYPES": "reading, critical-analysis, essay-response, translation-critique, etymology-trace, cloze, comparative-study, error-correction, highlight-morphemes",
        "INLINE_PRIORITY_TYPES": "mark-the-words, match-up, quiz",
        "WORKBOOK_PRIORITY_TYPES": "reading, critical-analysis, essay-response, translation-critique, etymology-trace",
        "ACTIVITY_COUNT_TARGET": "12", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "15",
        "ALLOWED_ACTIVITY_TYPES": "mark-the-words, quiz, match-up, grammar-identify, fill-in, reading, critical-analysis, essay-response, translation-critique, etymology-trace, cloze, comparative-study, error-correction, highlight-morphemes",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, true-false, unjumble, group-sort, classify, observe, phrase-table, odd-one-out, select, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, authorial-intent, translate",
        "REQUIRED_TYPES": "",
        "PRIORITY_TYPES": "reading, critical-analysis, essay-response, translation-critique",
    },
    # =====================================================================
    # SEMINAR TRACKS (HIST, BIO, LIT, ISTORIO) — 10 total: 3 inline + 7 workbook
    # 5000-word modules, primary source engagement, scholarly discourse
    # Content-focused. Language is a tool, not the subject.
    # =====================================================================
    "hist": {
        "TOTAL_TARGET": "10",
        "INLINE_MIN": "3", "INLINE_MAX": "4",
        "WORKBOOK_MIN": "7", "WORKBOOK_MAX": "9",
        "ITEMS_MIN": "4",
        "VOCAB_COUNT_TARGET": "25",
        "INLINE_ALLOWED_TYPES": "quiz, true-false, fill-in, mark-the-words",
        "WORKBOOK_ALLOWED_TYPES": "reading, source-evaluation, essay-response, critical-analysis, comparative-study",
        "INLINE_PRIORITY_TYPES": "quiz, true-false, fill-in",
        "WORKBOOK_PRIORITY_TYPES": "reading, source-evaluation, essay-response, critical-analysis",
        "ACTIVITY_COUNT_TARGET": "10", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "12",
        "ALLOWED_ACTIVITY_TYPES": "quiz, true-false, fill-in, mark-the-words, reading, source-evaluation, essay-response, critical-analysis, comparative-study",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, unjumble, cloze, error-correction, match-up, group-sort, classify, observe, phrase-table, odd-one-out, select, translate, translation-critique, etymology-trace, paleography-analysis, dialect-comparison, transcription, debate, authorial-intent, grammar-identify, highlight-morphemes",
        "REQUIRED_TYPES": "reading, essay-response",
        "PRIORITY_TYPES": "reading, source-evaluation, essay-response, critical-analysis",
    },
    "bio": {
        "TOTAL_TARGET": "10",
        "INLINE_MIN": "3", "INLINE_MAX": "4",
        "WORKBOOK_MIN": "7", "WORKBOOK_MAX": "9",
        "ITEMS_MIN": "4",
        "VOCAB_COUNT_TARGET": "30",
        "INLINE_ALLOWED_TYPES": "quiz, true-false, fill-in, mark-the-words",
        "WORKBOOK_ALLOWED_TYPES": "reading, essay-response, critical-analysis, authorial-intent, comparative-study",
        "INLINE_PRIORITY_TYPES": "quiz, true-false, fill-in",
        "WORKBOOK_PRIORITY_TYPES": "reading, essay-response, critical-analysis, authorial-intent",
        "ACTIVITY_COUNT_TARGET": "10", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "12",
        "ALLOWED_ACTIVITY_TYPES": "quiz, true-false, fill-in, mark-the-words, reading, essay-response, critical-analysis, authorial-intent, comparative-study",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, unjumble, cloze, error-correction, match-up, group-sort, classify, observe, phrase-table, odd-one-out, select, translate, translation-critique, etymology-trace, paleography-analysis, dialect-comparison, transcription, debate, source-evaluation, grammar-identify, highlight-morphemes",
        "REQUIRED_TYPES": "reading, essay-response, critical-analysis",
        "PRIORITY_TYPES": "reading, essay-response, critical-analysis, authorial-intent",
    },
    "istorio": {
        "TOTAL_TARGET": "10",
        "INLINE_MIN": "3", "INLINE_MAX": "4",
        "WORKBOOK_MIN": "7", "WORKBOOK_MAX": "9",
        "ITEMS_MIN": "4",
        "VOCAB_COUNT_TARGET": "30",
        "INLINE_ALLOWED_TYPES": "quiz, true-false, fill-in, mark-the-words",
        "WORKBOOK_ALLOWED_TYPES": "reading, source-evaluation, essay-response, critical-analysis, comparative-study",
        "INLINE_PRIORITY_TYPES": "quiz, true-false, fill-in",
        "WORKBOOK_PRIORITY_TYPES": "reading, source-evaluation, essay-response, critical-analysis",
        "ACTIVITY_COUNT_TARGET": "10", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "12",
        "ALLOWED_ACTIVITY_TYPES": "quiz, true-false, fill-in, mark-the-words, reading, source-evaluation, essay-response, critical-analysis, comparative-study",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, unjumble, cloze, error-correction, match-up, group-sort, classify, observe, phrase-table, odd-one-out, select, translate, translation-critique, etymology-trace, paleography-analysis, dialect-comparison, transcription, debate, authorial-intent, grammar-identify, highlight-morphemes",
        "REQUIRED_TYPES": "reading, essay-response, critical-analysis",
        "PRIORITY_TYPES": "reading, source-evaluation, essay-response, critical-analysis",
    },
    "lit": {
        "TOTAL_TARGET": "10",
        "INLINE_MIN": "3", "INLINE_MAX": "4",
        "WORKBOOK_MIN": "7", "WORKBOOK_MAX": "9",
        "ITEMS_MIN": "4",
        "VOCAB_COUNT_TARGET": "0",
        "INLINE_ALLOWED_TYPES": "quiz, true-false, fill-in, mark-the-words",
        "WORKBOOK_ALLOWED_TYPES": "reading, essay-response, critical-analysis, authorial-intent, comparative-study, translation-critique, debate",
        "INLINE_PRIORITY_TYPES": "quiz, true-false, mark-the-words",
        "WORKBOOK_PRIORITY_TYPES": "reading, critical-analysis, essay-response, authorial-intent",
        "ACTIVITY_COUNT_TARGET": "10", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "12",
        "ALLOWED_ACTIVITY_TYPES": "quiz, true-false, fill-in, mark-the-words, reading, essay-response, critical-analysis, authorial-intent, comparative-study, translation-critique, debate",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, unjumble, cloze, error-correction, match-up, group-sort, classify, observe, phrase-table, odd-one-out, select, translate, etymology-trace, paleography-analysis, dialect-comparison, transcription, source-evaluation, grammar-identify, highlight-morphemes",
        "REQUIRED_TYPES": "reading, essay-response, critical-analysis",
        "PRIORITY_TYPES": "reading, critical-analysis, essay-response, authorial-intent",
    },
    # =====================================================================
    # Professional tracks (B2-PRO, C1-PRO) — workplace Ukrainian
    # =====================================================================
    "b2-pro": {
        "TOTAL_TARGET": "12",
        "INLINE_MIN": "4", "INLINE_MAX": "5",
        "WORKBOOK_MIN": "8", "WORKBOOK_MAX": "10",
        "ITEMS_MIN": "6",
        "VOCAB_COUNT_TARGET": "35",
        "INLINE_ALLOWED_TYPES": "quiz, true-false, fill-in, match-up, mark-the-words",
        "WORKBOOK_ALLOWED_TYPES": "reading, essay-response, critical-analysis, translate, cloze, error-correction, translation-critique",
        "INLINE_PRIORITY_TYPES": "fill-in, match-up, quiz",
        "WORKBOOK_PRIORITY_TYPES": "essay-response, translate, reading, critical-analysis",
        "ACTIVITY_COUNT_TARGET": "12", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "14",
        "ALLOWED_ACTIVITY_TYPES": "quiz, true-false, fill-in, match-up, mark-the-words, reading, essay-response, critical-analysis, translate, cloze, error-correction, translation-critique",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, paleography-analysis, dialect-comparison, transcription, debate, source-evaluation, authorial-intent, etymology-trace, comparative-study, unjumble, group-sort, classify, observe, phrase-table, odd-one-out, select, grammar-identify, highlight-morphemes",
        "REQUIRED_TYPES": "",
        "PRIORITY_TYPES": "essay-response, translate, reading, critical-analysis",
    },
    "c1-pro": {
        "TOTAL_TARGET": "12",
        "INLINE_MIN": "4", "INLINE_MAX": "5",
        "WORKBOOK_MIN": "8", "WORKBOOK_MAX": "10",
        "ITEMS_MIN": "6",
        "VOCAB_COUNT_TARGET": "40",
        "INLINE_ALLOWED_TYPES": "quiz, fill-in, match-up, mark-the-words, grammar-identify",
        "WORKBOOK_ALLOWED_TYPES": "reading, essay-response, critical-analysis, translate, translation-critique, cloze, error-correction",
        "INLINE_PRIORITY_TYPES": "mark-the-words, fill-in, match-up",
        "WORKBOOK_PRIORITY_TYPES": "essay-response, critical-analysis, translation-critique, reading",
        "ACTIVITY_COUNT_TARGET": "12", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "14",
        "ALLOWED_ACTIVITY_TYPES": "quiz, fill-in, match-up, mark-the-words, grammar-identify, reading, essay-response, critical-analysis, translate, translation-critique, cloze, error-correction",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, paleography-analysis, dialect-comparison, transcription, debate, source-evaluation, authorial-intent, etymology-trace, comparative-study, true-false, unjumble, group-sort, classify, observe, phrase-table, odd-one-out, select, highlight-morphemes",
        "REQUIRED_TYPES": "",
        "PRIORITY_TYPES": "essay-response, critical-analysis, translation-critique, reading",
    },
    # =====================================================================
    # OES / RUTH — Old East Slavonic / Ruthenian philology
    # Specialized types: transcription, paleography-analysis, etymology-trace
    # =====================================================================
    "oes": {
        "TOTAL_TARGET": "10",
        "INLINE_MIN": "3", "INLINE_MAX": "4",
        "WORKBOOK_MIN": "7", "WORKBOOK_MAX": "9",
        "ITEMS_MIN": "4",
        "VOCAB_COUNT_TARGET": "35",
        "INLINE_ALLOWED_TYPES": "quiz, true-false, fill-in, mark-the-words, grammar-identify, highlight-morphemes",
        "WORKBOOK_ALLOWED_TYPES": "reading, essay-response, critical-analysis, etymology-trace, transcription, paleography-analysis, comparative-study",
        "INLINE_PRIORITY_TYPES": "mark-the-words, grammar-identify, fill-in",
        "WORKBOOK_PRIORITY_TYPES": "transcription, etymology-trace, paleography-analysis, reading, critical-analysis",
        "ACTIVITY_COUNT_TARGET": "10", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "12",
        "ALLOWED_ACTIVITY_TYPES": "quiz, true-false, fill-in, mark-the-words, grammar-identify, highlight-morphemes, reading, essay-response, critical-analysis, etymology-trace, transcription, paleography-analysis, comparative-study",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, unjumble, cloze, error-correction, match-up, group-sort, classify, observe, phrase-table, odd-one-out, select, translate, translation-critique, debate, authorial-intent, source-evaluation, dialect-comparison",
        "REQUIRED_TYPES": "transcription, etymology-trace",
        "PRIORITY_TYPES": "transcription, etymology-trace, paleography-analysis, reading, critical-analysis",
    },
    "ruth": {
        "TOTAL_TARGET": "10",
        "INLINE_MIN": "3", "INLINE_MAX": "4",
        "WORKBOOK_MIN": "7", "WORKBOOK_MAX": "9",
        "ITEMS_MIN": "4",
        "VOCAB_COUNT_TARGET": "35",
        "INLINE_ALLOWED_TYPES": "quiz, true-false, fill-in, mark-the-words, grammar-identify, highlight-morphemes",
        "WORKBOOK_ALLOWED_TYPES": "reading, essay-response, critical-analysis, etymology-trace, transcription, paleography-analysis, comparative-study, dialect-comparison",
        "INLINE_PRIORITY_TYPES": "mark-the-words, grammar-identify, fill-in",
        "WORKBOOK_PRIORITY_TYPES": "transcription, etymology-trace, paleography-analysis, reading, critical-analysis",
        "ACTIVITY_COUNT_TARGET": "10", "ACTIVITY_MIN": "0", "ACTIVITY_MAX": "12",
        "ALLOWED_ACTIVITY_TYPES": "quiz, true-false, fill-in, mark-the-words, grammar-identify, highlight-morphemes, reading, essay-response, critical-analysis, etymology-trace, transcription, paleography-analysis, comparative-study, dialect-comparison",
        "FORBIDDEN_ACTIVITY_TYPES": "anagram, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, unjumble, cloze, error-correction, match-up, group-sort, classify, observe, phrase-table, odd-one-out, select, translate, translation-critique, debate, authorial-intent, source-evaluation",
        "REQUIRED_TYPES": "transcription, etymology-trace",
        "PRIORITY_TYPES": "transcription, etymology-trace, paleography-analysis, reading, critical-analysis",
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
        if module_num <= 3:
            return IMMERSION_RULES["a2-bridge"]
        elif module_num <= 7:
            return IMMERSION_RULES["a2-ramp"]
        elif module_num <= 20:
            return IMMERSION_RULES["a2-m01-20"]
        elif module_num <= 50:
            return IMMERSION_RULES["a2-m21-50"]
        else:
            return IMMERSION_RULES["a2-m51-70"]
    elif base == "b1":
        return IMMERSION_RULES["b1-core"]
    else:
        return IMMERSION_RULES["b2+"]


def get_golden_fragment(track: str, module_num: int) -> str:
    """Return a level-appropriate golden fragment for the writing prompt.

    5 bands: early-beginner (A1.1-A1.2), late-beginner (A1.3-A2),
    intermediate (B1), advanced (B2-C2), seminar (HIST/BIO/LIT/etc.).
    """
    base = track.split("-")[0] if track not in ("hist", "bio", "istorio", "b2-pro", "c1-pro") else track
    if base in ("hist", "bio", "istorio", "lit", "oes", "ruth"):
        return GOLDEN_FRAGMENTS["seminar"]
    if base == "a1":
        if module_num <= 14:
            return GOLDEN_FRAGMENTS["early-beginner"]
        return GOLDEN_FRAGMENTS["late-beginner"]
    elif base == "a2":
        return GOLDEN_FRAGMENTS["late-beginner"]
    elif base == "b1":
        return GOLDEN_FRAGMENTS["intermediate"]
    else:
        return GOLDEN_FRAGMENTS["advanced"]


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
        return ACTIVITY_CONFIGS["b1-core"]
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

