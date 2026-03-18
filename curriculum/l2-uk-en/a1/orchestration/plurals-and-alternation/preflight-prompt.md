You are about to build a module using the prompt below. Before you start, verify the prompt is ready.

**Default answer: PASS.** Only report genuine issues that would cause audit gate failures or introduce errors.

## The Prompt

<prompt>
**Curriculum context:** This is Module 13 of the A1 track (Ukrainian for English speakers). Title: "Plurals and Alternation" — More Than One. Phase: A1.1 [First Contact]. Previous module: Colors And Clothing. Next module: Checkpoint First Contact.

# Module Build: Content + Activities + Vocabulary

## 1. Goal

> **You are Patient & Supportive Ukrainian Tutor, writing in the voice of Patient Supportive Tutor.**
>
> Build a complete beginner module for English-speaking teens and adults learning Ukrainian at the a1 level. Your job: **search Ukrainian school textbooks using RAG tools**, then **adapt** the pedagogy for L2 learners.
>
> **Output capacity: 65,000+ tokens.** Do NOT truncate.

**What L2 learners need** (that L1 textbooks assume):
1. Explicit grammar rules in English (L1 learners know intuitively)
2. Level-appropriate vocabulary only
3. Setting/purpose for dialogues (L1 assumes shared cultural context)

## 2. Scoring Dimensions

Your content will be scored on these 7 dimensions (see GEMINI.md for details):
1. **Experience Quality** — would the learner continue?
2. **Language Accuracy** — correct Ukrainian, no Russianisms
3. **Pedagogy** — clear progression, quick wins
4. **Activities** — variety, appropriate difficulty
5. **Beginner Safety** — warm tone, not overwhelming
6. **LLM Fingerprint** — natural voice, not robotic
7. **Linguistic Accuracy** — factual correctness

---

## 3. Context

### Input Files (read ALL before writing)

| File | What to extract |
|------|----------------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/plurals-and-alternation-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/plurals-and-alternation.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Noun plural formation Vowel alternation (і → о/е)", grade=1-2)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 12
**Previous module:** Colors & Clothing

**Cumulative vocabulary (91 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, ніс, сон
сік, стіл, кіно, тут, там, так, ні, привіт, дякую, це
яблуко, риба, село, Україна, їжак, юнак, край, день, син, мій
вухо, їжа, яйце, юшка, каша, небо, сир, хліб, зуб, дім
вовк, жук, шапка, гора, рука, бабуся, павук, ґанок, кінь, людина
суп, вода, дим, люк, хор, сіль, Львів, мідь, осінь, мить
тінь, м'ясо, п'ять, сім'я, м'яч, цукор, цибуля, час, черепаха, чай
що, щастя, факт, джерело, дзвін, об'єкт, фото, ще, бджола, дзеркало
склад, голосний, приголосний, перенесення, сестра, дерево, вулиця, автобус, бібліотека, університет
чайка

**Grammar already taught (43 topics):**
- Full alphabet overview (33 letters)
- Sound-letter correspondence (букви vs звуки)
- Vowel vs consonant classification
- Basic syllable blending and word reading
- Base vowel pronunciation (А О У Е И І)
- Iotated vowels dual function (Я Ю Є Ї)
- И vs І distinction
- Word stress basics (наголос)
- Vowel purity rule (no reduction)
- Sonorant consonants (Л М Н Р В)
- Voiced/voiceless consonant pairs
- No final devoicing rule
- Hard/soft consonant distinction
- Г vs Ґ distinction
- Soft sign palatalization (Ь)
- Apostrophe function and rules
- Affricates (Ц, Ч, Щ)
- Digraphs (ДЖ, ДЗ)
- Ф — rare native, common in borrowings
- Full alphabet mastery
- Syllable structure
- Open and closed syllables
- Word division rules
- Word stress
- Stress mobility
- Intonation patterns
- Three-gender system
- Declension families overview
- Gender prediction rules
- T-V distinction
- Imperative forms in politeness expressions
- Personal pronouns
- Zero copula construction
- Demonstrative це
- Demonstratives цей/ця/це/ці (this)
- Demonstratives той/та/те/ті (that)
- Gender agreement with demonstratives
- Adjective endings for gender (m/f/n)
- Hard stem adjectives (-ий/-а/-е/-і)
- Soft stem adjectives (-ій/-я/-є/-і)
- Color adjectives with agreement
- Clothing vocabulary
- Adjective + noun gender agreement with clothing items

**Coming next (module after this):** Cyrillic alphabet (all 33 letters), Noun gender (m/f/n), Adjective-noun agreement
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- студент/студенти (student/students) — regular masculine plural -и; Top 500 word; collocations: нові студенти, молоді студенти
- книга/книги (book/books) — regular feminine plural -и replacing -а; Top 200 word; collocations: цікаві книги, старі книги
- місто/міста (city/cities) — regular neuter plural -а replacing -о; Top 100 word; collocations: великі міста, нові міста
- кіт/коти (cat/cats) — vowel alternation і → о; collocations: руді коти, домашні коти
- діти (children) — irregular plural from дитина; Top 100 word; collocations: маленькі діти, наші діти
- люди (people) — irregular plural from людина; Top 50 word; collocations: добрі люди, молоді люди
- гроші (money) — plural-only noun; Top 300 word; collocations: багато грошей, заробляти гроші
- двері (door) — plural-only noun; Top 500 word; collocations: відкрити двері, зачинити двері

**Recommended** (use in your content to reach the vocabulary target):
- очі (eyes) — irregular plural from око; Top 300 word; collocations: сині очі, великі очі
- ножиці (scissors) — plural-only noun; demonstrates pluralia tantum concept
- цукор (sugar) — uncountable noun; collocations: ложка цукру, без цукру
- молоко (milk) — uncountable noun; collocations: склянка молока, пити молоко

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 10-20% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose. Introduce Ukrainian grammar terms bolded with translation on first use.
- UKRAINIAN CONTENT: Words and short phrases bolded inline: "The word **книга** (book) is feminine."
- TABLES: Vocabulary tables, word families, simple paradigm tables.
- STRUCTURAL RULE: Every paragraph is English. Ukrainian words/phrases appear inline bolded. Full Ukrainian sentences (3+ words with a verb) go in tables or bulleted example lists with English gloss.
Ukrainian sentences max 10 words.

### Textbook References
- **Grade 3, Сторінка 114**
  114
Прочитай і розкажи  
у класі.
Я — учителька
Я — учитель
зірка
літак
місто
зірки
літаки
міста
Іменники мають два числа: однину і множину.
Іменники, які називають один предмет, уживаються в однині.
...

- **Grade 3, Сторінка 116**
  116
Досліди, чи всі іменни-
ки можуть мати фор-
му однини і множини.
Я — дослідник
Я — дослідниця
Спостерігаю за іменниками, які вживаються тільки  
в однині або тільки у множині
6   Прочитай слова і...

- **Grade 4, Сторінка 50**
  Ім енники-синонім и, ім енники-антонім и, 
багатозначність ім енників
101. Прочитайте іменники.
Добро, війна, радість, мир, герой, бруд, шум, тиша, 
крик, потворність, мовчання, чистота, купівля, прод...

- **Grade 2, Сторінка 12**
  12
сЛова — назви ПреДметІв
Слова — назви предметів — це іменники.
Слово іменник утворене від слова ім’я. Кожний 
предмет чи явище має своє ім’я, тобто свою назву.  
Назви зображені предмети спочатку ...

- **Grade 4, Сторінка 38**
  38
73. 
1. Розгляньте таблицю. Зверніть увагу на назви від-
мінків. На які питання відповідає кожен з них? Чим 
відрізняється кличний відмінок від інших відмінків?
ВІДМІНЮВАННЯ ІМЕННИКІВ
Назва  
відмі...






---

## 4. Outline

Write **Plurals and Alternation** for the a1 track. Target: 1200–1800 words.

### CRITICAL: EXACT H2 HEADERS (copy-paste, do not alter)

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Множина іменників (Noun plurals)` (~275 words)
  - Basic plural endings for masculine nouns: -и/-і (студент → студенти, хлопець → хлопці) — the most common and predictable pattern
  - Basic plural endings for feminine nouns: -и/-і replacing -а/-я (книга → книги, земля → землі) — the final vowel changes to -и or -і
  - Basic plural endings for neuter nouns: -а/-я replacing -о/-е (місто → міста, море → моря) — neuter plurals swap their characteristic ending
  - Irregular plurals that must be memorized: діти (children, from дитина), люди (people, from людина), очі (eyes, from око) — high-frequency exceptions
- `## Чергування (Alternation)` (~250 words)
  - Vowel alternation і → о/е in stems: when adding plural endings, the і in the stem may revert to о or е — кіт → коти, піч → печі, ніж → ножі
  - Why alternation happens: historical vowel changes (the 'fleeting і') — і appears in closed syllables but reverts when the syllable opens in plural forms
  - Consonant alternation preview: к → ц, г → з, х → с before the ending -і — рука → руці, нога → нозі (this pattern returns in the locative case)
  - Pattern recognition strategy: if a word has і in the last syllable of the stem, check whether it alternates in the plural — most common with monosyllabic masculine nouns
- `## Множина прикметників (Adjective plurals)` (~250 words)
  - Simplification: all three genders collapse into one plural form ending in -і/-ї — новий (m) / нова (f) / нове (n) → нові (plural for all genders)
  - Soft-stem adjectives: синій (m) / синя (f) / синє (n) → сині (plural) — the pattern is the same, just with the soft variant
  - Agreement with plural nouns: adjective must match the noun in number — нові книги, великі міста, молоді студенти
  - Practice forming noun phrases: combining plural adjectives with plural nouns in simple sentences — Це нові книги. Ті великі будинки старі.
- `## Винятки та особливості (Exceptions and special cases)` (~175 words)
  - Uncountable nouns that have no plural: молоко (milk), цукор (sugar), вода (water in general sense), повітря (air) — these exist only in singular
  - Plural-only nouns (pluralia tantum): гроші (money), двері (door), ножиці (scissors), окуляри (glasses) — these exist only in plural
  - Stress shifts in plural: some nouns change stress when pluralized — рукА → рУки, сестрА → сЕстри, ногА → нОги (review from a1-06 stress mobility)
- `## Практика (Practice)` (~250 words)
  - Plural formation drills: given singular nouns, produce the correct plural form with attention to ending changes and vowel alternation
  - Matching singulars to plurals: identify which plural form belongs to which singular, including irregular pairs like дитина → діти
  - Reading plural phrases: practice reading and understanding simple sentences with plural noun phrases — У мене є нові книги. Це великі міста.
- `## Підсумок — Summary` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Множина іменників (Noun plurals) | 275+ |
| Чергування (Alternation) | 250+ |
| Множина прикметників (Adjective plurals) | 250+ |
| Винятки та особливості (Exceptions and special cases) | 175+ |
| Практика (Practice) | 250+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Rules (read ALL before writing)

### RULE 1: GRAMMAR ALLOWLIST (A1.1 modules M1-M14)

You may ONLY write these Ukrainian sentence structures:
- **Це** + noun: `Це кіт.`
- **Noun** + **тут/там**: `Мама тут.`
- **Noun** + **—** + **noun**: `Мама — вчителька.`
- **Adjective** + **noun**: `Великий дім.`
- **Питання**: `Це кіт? Хто це? Де мама?`
- **Fixed phrases** (memorized, no grammar analysis): дякую, будь ласка, привіт, до побачення

Any other structure (including conjugated verbs) is FORBIDDEN. If you need to express an action, rephrase as a noun: "reading practice" not "let's read."

### RULE 2: VOCABULARY BANK

Use ONLY these Ukrainian words. Do NOT pull other Cyrillic words from memory:

**Allowed Ukrainian words:** студент/студенти, книга/книги, місто/міста, кіт/коти, діти, люди, гроші, двері, очі, ножиці, цукор, молоко

### RULE 3: VARIATION PATTERN

Alternate your example formatting across sections:
- Section 1: bulleted word list + [!tip] callout
- Section 2: mini-dialogue with location label `> **(Вдома / At home)**`
- Section 3: comparison pattern (X vs Y)
- Section 4: [!challenge] or [!practice] callout with exercise
- Section 5: reading practice sentences

NEVER start 3+ sections with the same phrase. NEVER use "Here is" or "Let's look at" more than once.

### RULE 4: STRESS MARKS

Do NOT add stress marks (´) to Ukrainian words. Write plain Ukrainian: `молоко` not `молоко́`. The pipeline adds stress marks deterministically after you write.

### RULE 5: ENGLISH PROSE STYLE

You are a warm tutor. Use "you/your" often. Include encouragement. Keep it conversational.

Cite textbook adaptations: `<!-- adapted from: {author}, Grade {N} -->`

## Language Quality Rules (Beginner Tier)

### Russian Characters (HARD FAIL)

**ы, э, ё, ъ** must NEVER appear in Ukrainian text. These are Russian-only characters.

### Stress Mark Typography

Use lowercase letters with a combining acute accent (´) on the stressed vowel:
- Correct: ма́ма, анана́с, оса́, сосна́
- Wrong: мА́ма, ананА́с, осА́, соснА́ (do NOT capitalize the stressed vowel)

### IPA and Latin Transliteration (BANNED at ALL levels)

Never include IPA symbols (ɑ, ɛ, ʃ, etc.) or bracketed pronunciation guides like `[ma-ma]`, `[a-na-nas]`, `[ˈmɑmɑ]`. The ONLY pronunciation aid is the stress mark (´) on the vowel.

Latin transliterations are BANNED: never use kh, sh, ch, zh, ts, ya, yu, ye, shch.

```markdown
❌ WRONG: "мама [ˈmɑmɑ]" or "хліб (khlib)"
✅ RIGHT: "**ма́ма** (mom)" or "**Х**, like the «ch» in Scottish «loch»"
```

### Typography

- **ALWAYS** use Ukrainian angular quotes: «...» (never straight quotes "...")
- Base content vocabulary on the plan's `vocabulary_hints`. Function words (pronouns, conjunctions, particles, question words) are always allowed

### No Word Salad (HARD FAIL)

Every paragraph must have ONE clear point and logical flow between sentences. Do NOT string together unrelated observations.

### LLM Writing Patterns to Avoid

1. **Grandiose openers** — don't inflate every topic
2. **Stacked identical callouts** — same title max twice, vary types
3. **"In this lesson, we will..."** — ALWAYS banned (formulaic opener)


### Activity Rules

- Activity **answers** must use words from your content. **Distractors** must be VESUM-verified Ukrainian words — call `verify_words` before including any distractor. Never use made-up or unverified words.
- Follow schemas exactly — `additionalProperties: false` means any unlisted field = FAIL.
- Read `schemas/activities-a1.schema.json` for full field definitions.

**Allowed types:** quiz, true-false, fill-in, match-up, anagram, unjumble, group-sort, watch-and-repeat, classify, image-to-letter
**Forbidden types:** cloze, error-correction, mark-the-words, select, translate, essay-response, critical-analysis, comparative-study, authorial-intent
**Required types:** fill-in, match-up, quiz, group-sort

| Module range | Use these | Avoid these |
|-------------|-----------|-------------|
| M1-M4 (alphabet) | quiz, match-up, group-sort, anagram, true-false, fill-in, watch-and-repeat, image-to-letter, classify | unjumble, cloze, translate |
| M5-M10 | + unjumble, fill-in with sentences | cloze, translate |
| M11+ | all types including translate | cloze (needs 14+ blanks) |

### Item Minimums (HARD FAIL if under)

| Type | Minimum |
|------|--------|
| quiz | ≥6 items |
| true-false | ≥6 items |
| fill-in | ≥6 items |
| match-up | ≥6 pairs |
| anagram | ≥6 items |
| unjumble | ≥6 items |
| group-sort | ≥8 items |
| watch-and-repeat | ≥1 items |
| classify | ≥1 items |
| image-to-letter | ≥5 items |

### Vocabulary YAML

Object with `items:` wrapper. Each entry: `lemma` (dictionary form), `translation`, `pos`. Optional: `gender`, `notes`, `usage`, `example`. No `ipa` field.

---

## 6. Hard Constraints

GRAMMAR CONSTRAINTS (A1.1 — First Contact):
Keep grammar simple — this is the learner's first exposure to Ukrainian.

ALLOWED:
- Це + noun: «Це кіт», «Це мама»
- Simple present tense (я читаю, я бачу)
- Basic imperatives (читай, слухай, дивись)
- Question words: «Хто це?», «Що це?», «Де?»
- Так/Ні answers
- Adj + noun: «великий дім», «нова книга»

BANNED (too complex for first contact):
- Past tense, future tense, conditionals
- Participles, passive voice, gerunds
- Compound/complex sentences — max 1 clause per sentence (no і/а/але joining clauses)
- Do not explicitly teach cases — use nouns in natural contexts

METALANGUAGE:
- ALL terminology in English first, Ukrainian in parentheses: 'vowels (голосні)'
- Section headings MUST be bilingual (e.g., '## Голосні — Vowels')
- Explanatory prose in English, Ukrainian for examples and dialogues

- **No Russianisms**: кушати→їсти, получати→отримувати, самий→найкращий
- **No Russian characters**: ы, э, ё, ъ — never
- **No colonial framing**: never define Ukrainian by comparing it to Russian. Don't say "unlike Russian..." or "not found in Russian." Present Ukrainian on its own terms
- **No IPA or Latin transliteration** — stress marks (´) only
- **Ukrainian quotes** in content: «...» | **YAML values**: plain text or single quotes (never «»)
- **Euphony** (у/в, і/й alternation): follow rules in the shared content rules section below — audit flags violations
- **YAML colon values**: quote with single quotes: `'text: with colon'`
- H2 titles must match the outline EXACTLY. You MAY add H3 sub-headings within H2 sections (e.g., for individual letters, grammar sub-topics)
- **MUST end with `## Підсумок — Summary`** with self-check questions

### Common Irregular Imperatives

If your module uses imperative verbs:
- взяти → **візьми/візьміть** (NOT ~~взяй~~)
- стояти → **стій/стійте** (NOT ~~стояй~~)
- сісти → **сядь/сядьте** (NOT ~~сісь~~)
- їсти → **їж/їжте** (NOT ~~їсь~~)

The Russian conjunction **"и"** (meaning "and") is forbidden. Use Ukrainian conjunctions **і**, **й** (after vowels), or **та**.

---

## 7. Output Format

> **Content outside delimiters is automatically discarded.**

Output FIVE blocks in this exact order (plus optional friction report):

**Block 1: Content** — `===CONTENT_START===` ... `===CONTENT_END===`
**Block 2: Word Counts** — `===WORD_COUNTS_START===` ... `===WORD_COUNTS_END===`
**Block 3: Activities** — `===ACTIVITIES_START===` ... `===ACTIVITIES_END===` (bare list, no wrapper)
**Block 4: Vocabulary** — `===VOCABULARY_START===` ... `===VOCABULARY_END===` (object with `items:`)
**Block 5: Builder Notes** — `===BUILDER_NOTES_START===` ... `===BUILDER_NOTES_END===`

### Builder Notes (MANDATORY)

```
===BUILDER_NOTES_START===
phase: CONTENT
status: SUCCESS | PARTIAL | BLOCKED
word_count: {actual}
deviations:
  - section: "{section}"
    reason: "{why}"
frictions:
  - type: TEMPLATE_CONSTRAINT | SCHEMA_MISMATCH | PLAN_GAP | RAG_FAILURE
    description: "{what went wrong}"
    proposed_fix: "{fix}"
research_gaps:
  - "{what you couldn't find}"
unverified_terms:
  - "{words you couldn't verify}"
review_focus:
  - "{what reviewer should check}"
rag_tools_used:
  - "{tool}: {query} → {result}"
===BUILDER_NOTES_END===
```

### Friction Report (OPTIONAL — only if you hit pipeline/schema issues)

```
===FRICTION_START===
**Phase**: Full Build
**Friction Type**: YAML_SCHEMA_VIOLATION | PLAN_GAP | CONTRADICTION
**Problem**: {what went wrong}
**Proposed Fix**: {how to fix the template/pipeline}
===FRICTION_END===
```


FRICTION CONSTRAINTS (from past build reviews — DO NOT repeat these errors):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.

</prompt>

## The Plan

<plan>
module: a1-013
level: A1
sequence: 13
slug: plurals-and-alternation
version: '2.0'
title: Plurals and Alternation
subtitle: More Than One
focus: grammar
pedagogy: PPP
phase: A1.1 [First Contact]
word_target: 1200
objectives:
- Form plurals for common masculine, feminine, and neuter nouns
- Recognize vowel alternation patterns (і → о/е) in plural formation
- Make adjectives agree with plural nouns using the -і/-ї ending
- Identify uncountable nouns and plural-only nouns
content_outline:
- section: Множина іменників (Noun plurals)
  words: 275
  points:
  - 'Basic plural endings for masculine nouns: -и/-і (студент → студенти, хлопець → хлопці) — the most common and predictable
    pattern'
  - 'Basic plural endings for feminine nouns: -и/-і replacing -а/-я (книга → книги, земля → землі) — the final vowel changes
    to -и or -і'
  - 'Basic plural endings for neuter nouns: -а/-я replacing -о/-е (місто → міста, море → моря) — neuter plurals swap their
    characteristic ending'
  - 'Irregular plurals that must be memorized: діти (children, from дитина), люди (people, from людина), очі (eyes, from око)
    — high-frequency exceptions'
- section: Чергування (Alternation)
  words: 250
  points:
  - 'Vowel alternation і → о/е in stems: when adding plural endings, the і in the stem may revert to о or е — кіт → коти,
    піч → печі, ніж → ножі'
  - 'Why alternation happens: historical vowel changes (the ''fleeting і'') — і appears in closed syllables but reverts when
    the syllable opens in plural forms'
  - 'Consonant alternation preview: к → ц, г → з, х → с before the ending -і — рука → руці, нога → нозі (this pattern returns
    in the locative case)'
  - 'Pattern recognition strategy: if a word has і in the last syllable of the stem, check whether it alternates in the plural
    — most common with monosyllabic masculine nouns'
- section: Множина прикметників (Adjective plurals)
  words: 250
  points:
  - 'Simplification: all three genders collapse into one plural form ending in -і/-ї — новий (m) / нова (f) / нове (n) → нові
    (plural for all genders)'
  - 'Soft-stem adjectives: синій (m) / синя (f) / синє (n) → сині (plural) — the pattern is the same, just with the soft variant'
  - 'Agreement with plural nouns: adjective must match the noun in number — нові книги, великі міста, молоді студенти'
  - 'Practice forming noun phrases: combining plural adjectives with plural nouns in simple sentences — Це нові книги. Ті
    великі будинки старі.'
- section: Винятки та особливості (Exceptions and special cases)
  words: 175
  points:
  - 'Uncountable nouns that have no plural: молоко (milk), цукор (sugar), вода (water in general sense), повітря (air) — these
    exist only in singular'
  - 'Plural-only nouns (pluralia tantum): гроші (money), двері (door), ножиці (scissors), окуляри (glasses) — these exist
    only in plural'
  - 'Stress shifts in plural: some nouns change stress when pluralized — рукА → рУки, сестрА → сЕстри, ногА → нОги (review
    from a1-06 stress mobility)'
- section: Практика (Practice)
  words: 250
  points:
  - 'Plural formation drills: given singular nouns, produce the correct plural form with attention to ending changes and vowel
    alternation'
  - 'Matching singulars to plurals: identify which plural form belongs to which singular, including irregular pairs like дитина
    → діти'
  - 'Reading plural phrases: practice reading and understanding simple sentences with plural noun phrases — У мене є нові
    книги. Це великі міста.'
vocabulary_hints:
  required:
  - 'студент/студенти (student/students) — regular masculine plural -и; Top 500 word; collocations: нові студенти, молоді
    студенти'
  - 'книга/книги (book/books) — regular feminine plural -и replacing -а; Top 200 word; collocations: цікаві книги, старі книги'
  - 'місто/міста (city/cities) — regular neuter plural -а replacing -о; Top 100 word; collocations: великі міста, нові міста'
  - 'кіт/коти (cat/cats) — vowel alternation і → о; collocations: руді коти, домашні коти'
  - 'діти (children) — irregular plural from дитина; Top 100 word; collocations: маленькі діти, наші діти'
  - 'люди (people) — irregular plural from людина; Top 50 word; collocations: добрі люди, молоді люди'
  - 'гроші (money) — plural-only noun; Top 300 word; collocations: багато грошей, заробляти гроші'
  - 'двері (door) — plural-only noun; Top 500 word; collocations: відкрити двері, зачинити двері'
  recommended:
  - 'очі (eyes) — irregular plural from око; Top 300 word; collocations: сині очі, великі очі'
  - ножиці (scissors) — plural-only noun; demonstrates pluralia tantum concept
  - 'цукор (sugar) — uncountable noun; collocations: ложка цукру, без цукру'
  - 'молоко (milk) — uncountable noun; collocations: склянка молока, пити молоко'
activity_hints:
- type: fill-in
  focus: Form the correct plural from a given singular noun
  items: 12
- type: match-up
  focus: Match singular nouns to their plural forms
  items: 12
- type: quiz
  focus: Choose the correct plural form (including alternation)
  items: 10
- type: group-sort
  focus: Sort nouns into countable vs uncountable/plural-only
  items: 10
connects_to:
- a1-14 (Checkpoint First Contact)
prerequisites:
- a1-12 (Colors and Clothing)
persona:
  voice: Patient Supportive Tutor
  role: Market Vendor
grammar:
- Noun plural formation
- Vowel alternation (і → о/е)
- Adjective plural agreement
register: розмовний

</plan>

## Audit Gates

## Audit Gates (your content will be checked against these)

Level: A1
Word target: 1200
Word ceiling: ~1800 (exceeding = FAIL)
Min activities: 0
Min engagement boxes: 1
Min activity types: 0

### Immersion
Target range: defined in the prompt's Immersion Target section (varies by module).
Tables count ZERO for immersion — only blockquotes, bulleted lists, and pattern boxes count.

### Grammar constraints
Max words per Ukrainian sentence: 10
Participles allowed: False
Max clauses: 1

### Structure
MUST have a Summary/Підсумок section (structure gate FAILS without it).

### Pedagogy
Sentences exceeding word limit = COMPLEXITY violation.
Participles before B1 = GRAMMAR violation.
Euphony (у/в alternation) errors are flagged.

## Scoring Dimensions (7 — Beginner Tier)
Your content will be scored on these dimensions (9-10 = PASS):
1. Language Quality — no Russianisms, correct Ukrainian, natural phrasing
2. Engagement — would the learner continue reading? Hook in first 50 words
3. Writing Quality — clarity, pacing, no word salad, logical flow
4. Immersion — % Ukrainian must hit target range (tables = ZERO)
5. Structure — lesson arc: WELCOME → PREVIEW → PRESENT → PRACTICE → CELEBRATE
6. Emotional Safety — ≥15 direct address, encouragement, quick wins
7. Lesson Quality — does it feel like a patient, encouraging tutor?

## Check 1: Prompt Feasibility

Only report if:
- Two instructions **directly contradict** each other AND following one will FAIL a named gate
- A target is **mathematically impossible** to reach given the constraints
- A required gate has **zero guidance** in the prompt (literally missing, not "could be clearer")

**Gate names**: Words, Activities, Density, Unique_types, Engagement, Vocab, Structure, Pedagogy, Immersion.

## Check 2: Semantic False Friends (Russianisms)

These Ukrainian words exist in BOTH Ukrainian and Russian but have DIFFERENT meanings:

- **лук**: Russian meaning = onion, цибуля, onions; Ukrainian meaning = bow (weapon). Correct word for 'onion, цибуля, onions' → **цибуля**
- **луна**: Russian meaning = moon, місяць, lunar; Ukrainian meaning = echo (відлуння). Correct word for 'moon, місяць, lunar' → **місяць**
- **город**: Russian meaning = city, місто, town; Ukrainian meaning = garden, vegetable patch. Correct word for 'city, місто, town' → **місто**
- **неділя**: Russian meaning = week, тиждень; Ukrainian meaning = Sunday. Correct word for 'week, тиждень' → **тиждень**
- **річ**: Russian meaning = speech; Ukrainian meaning = thing, item. Correct word for 'speech' → **промова**
- **шар**: Russian meaning = ball, sphere; Ukrainian meaning = layer. Correct word for 'ball, sphere' → **куля**
- **мешкати**: Russian meaning = to dawdle, to delay, dawdle; Ukrainian meaning = to live, to dwell. Correct word for 'to dawdle, to delay, dawdle' → **баритися**
- **лічити**: Russian meaning = to treat, to heal, treatment; Ukrainian meaning = to count. Correct word for 'to treat, to heal, treatment' → **лікувати**
- **наглий**: Russian meaning = arrogant, impudent, insolent; Ukrainian meaning = sudden, unexpected. Correct word for 'arrogant, impudent, insolent' → **зухвалий**
- **лаяти**: Russian meaning = to bark, bark, barking; Ukrainian meaning = to scold, to swear at. Correct word for 'to bark, bark, barking' → **гавкати**
- **палиця**: Russian meaning = finger; Ukrainian meaning = stick, cane. Correct word for 'finger' → **палець**
- **сварка**: Russian meaning = welding; Ukrainian meaning = quarrel, argument. Correct word for 'welding' → **зварювання**

**Only flag if the prompt USES or DEFINES a word with the Russian meaning.** Do NOT flag:
- Warnings about the false friend (e.g., "неділя ≠ week")
- Discussions explaining the difference
- Correct Ukrainian usage

## Check 3: Plan-Prompt Coherence

Compare the plan (above) to the rendered prompt. Check:
1. **Section coverage**: Every plan `content_outline` section has a matching section in the prompt
2. **Word target**: Plan's `word_target` matches the prompt's word budget
3. **Vocabulary**: All `vocabulary_hints.required` items appear in the prompt
4. **Objectives**: The prompt's instructions would achieve all plan `objectives`

Only flag if a plan section is **completely missing**, the word target **differs**, or required vocabulary is **absent**. Do NOT flag rewordings or extra scaffolding.

## Output Format (YAML)

```yaml
prompt_preflight:
  status: PASS  # or ISSUES_FOUND
  issues:
    - type: CONTRADICTION  # MISSING_INSTRUCTION, IMPOSSIBLE_TARGET, RUSSICISM, MISSING_PLAN_SECTION, PLAN_CONTRADICTION, WORD_TARGET_MISMATCH
      location: "where in the prompt"
      problem: "what's wrong"
      suggested_fix: "how to fix it"
      severity: HIGH  # or MEDIUM, LOW
```

If no issues: `prompt_preflight: {status: PASS, issues: []}`

Be SPECIFIC. Cite exact text.