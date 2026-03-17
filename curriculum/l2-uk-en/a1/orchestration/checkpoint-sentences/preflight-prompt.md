You are about to build a module using the prompt below. Before you start, verify the prompt is ready.

**Default answer: PASS.** Only report genuine issues that would cause audit gate failures or introduce errors.

## The Prompt

<prompt>
# Beginner Checkpoint: Synthesis & Review

> **Persona reminder:** You are Patient & Supportive Ukrainian Tutor. Write in the voice of Patient Supportive Tutor.

> **Your task: Write approximately 1200 words that REVIEW and SYNTHESIZE prior material — NOT teach new concepts.**
> Keep explanations clear and direct. Every H3 gets {H3_WORD_RANGE} words. Avoid verbose prose — students are beginners. Focus on practical examples over theory.

> **Output capacity: You can generate 65,000+ tokens per response.** Do NOT preemptively truncate.

## CHECKPOINT IDENTITY — READ THIS FIRST

**This is a CHECKPOINT module.** Checkpoints are fundamentally different from teaching modules:

| Teaching Module | Checkpoint Module |
|----------------|-------------------|
| Introduces new grammar/vocabulary | Reviews grammar/vocabulary from prior modules |
| Explains concepts for the first time | Creates new CONTEXTS that combine prior concepts |
| Learning objectives | Synthesis objectives |
| "Here's how it works" | "Show me you can use it" |
| Feels like a lecture | Feels like a celebration of progress |

**The golden rule: If the learner hasn't seen it in a prior module, it does NOT belong here.**

### What Checkpoints Do

1. **Reuse ALL vocabulary and grammar from the preceding block** — no new teaching
2. **Create new contexts** that force combining multiple skills learned separately
3. **Feel like a reward/celebration**, not a test — the learner should feel proud of how far they've come
4. **Synthesis over explanation** — show how pieces fit together, don't re-explain them
5. **Self-assessment** — help learners identify gaps before moving forward

### What Checkpoints Do NOT Do

- Introduce new grammar rules or patterns
- Teach new vocabulary (only reuse from prior modules)
- Explain concepts in detail (brief reminders only, not full explanations)
- Present theory-heavy sections

---

## Files to Read

| File | Purpose |
|------|---------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/checkpoint-sentences-research.md` | Research notes |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/checkpoint-sentences.yaml` | Content outline, section word allocations, vocabulary_hints |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion % |

Read ALL files before writing.

## Resource Discoveries

### Videos
- **What is this? - Ukrainian Grammar** (Bright Kids Ukrainian)
  URL: https://www.youtube.com/watch?v=Sr7Jv9TVOgk
  Score: 0.8 -- This video explains the distinction between animate and inanimate nouns and how it affects question formation ('Хто це?' vs 'Що це?'), directly reinforcing 'Skill 2: Questions & Negation'.
  Suggested placement: After Skill 2: Questions & Negation -- it elaborates on question types based on noun categories.
  Key excerpt: від категорії істот чи не істот залежить питання хто це або що це


### Textbook References
- **Grade 4, Сторінка 110**
  1
Слова для довідки: червоніти, втікати, думати, мріяти, ліну­
ватися, зазнаватися.
2. Запиши дієслова в тому порядку, що й фразеологізми. Через 
риску запиши дієслова майбутнього часу в 2-й особі мно...

- **Grade 3, Сторінка 101**
  Частини  мови
У розділі ти будеш вивчати:
ІМЕННИКИ
хто? що?
який? яка? 
яке? які?
що робить? 
що роблять?
скільки?  
котрий?
ЧИСЛІВНИКИ
ДІЄСЛОВА
ПРИКМЕТНИКИ...

- **Grade 1, Сторінка 3**
  3
Дорогий друже!
Ти хочеш учитися читати?
Ти прагнеш спілкуватися?
Ти любиш фантазувати?
Тоді ця книга саме для тебе! 
Вона допоможе тобі навчитися читати, 
висловлювати думки й почуття, спілкуватися....

- **Grade 4, Сторінка 2**
  Умовні позначення:
— урок розвитку писемного
мовлення.
— вивчити 
напам’ять;
— словник;
— домашнє завдання;
— робота в парах, 
читання діалогів;
— тема уроку;
— завдання на вибір;
— завдання підвищено...

- **Grade 7, Сторінка 54**
  А. Перепишіть речення, уставивши, де потрібно, м’який знак. Б. Надпишіть над кожним дієсловом його форму. було
кажу
принести...




## Module Constraints (HARD FAIL if violated)

GRAMMAR CONSTRAINTS (A1.2 — Verbs & Sentences):
Present tense verbs are fully available. Simple sentences.

ALLOWED:
- Present tense (я читаю, він іде, вони мають)
- Basic imperatives (читай/читайте, слухай/слухайте, дивись/дивіться)
- Infinitives in simple contexts (можна читати, треба слухати)
- Simple questions and answers

BANNED (too complex for A1.2):
- Past tense, future tense, conditionals
- Participles, passive voice
- Complex subordinate clauses



**Target vocabulary** (from the plan — these are REVIEW words from prior modules, not new vocabulary):

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- читати (to read) — читати книгу, я читаю; I conjugation review
- писати (to write) — писати лист, я пишу; I conjugation review
- говорити (to speak) — говорити українською, я говорю; II conjugation review
- подобатися (to like) — мені подобається, тобі подобається; Dative construction
- хотіти (to want) — я хочу їсти, я хочу каву; Irregular conjugation
- мій (my m.) — мій телефон, мій друг; Possessive review
- твій (your m.) — твій будинок, твоя книга; Possessive review
- цей (this m.) — цей стілець, ця книга; Demonstrative review
- той (that m.) — той будинок, та вулиця; Demonstrative review
- хто (who) — Хто це? Хто говорить?; Question word review
- що (what) — Що це? Що ти хочеш?; Question word review
- де (where) — Де ти? Де кафе?; Question word review

**Recommended** (use in your content to reach the vocabulary target):
- тому що (because) — тому що я хочу; Causal conjunction
- бо (because) — бо мені подобається; Colloquial causal conjunction
- звідки (from where) — Звідки ти?; Question word
- куди (where to) — Куди ти йдеш?; Direction question word

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

**Rules:**
- Every word listed above was taught in a prior module. Use them in NEW combinations and contexts.
- Do NOT explain these words as if seeing them for the first time — the learner already knows them.
- Create fresh example sentences that combine vocabulary from different prior modules.
- Match the syntactic complexity of the prior modules — do not escalate difficulty.

## Textbook Reference (from Ukrainian grammar textbooks)

These are explanations from Ukrainian school grammar textbooks. Use them as **reference** for grammar rules and examples. Adapt for adult A1 learners — keep explanations simple but maintain grammatical accuracy.

**Grade 7, mishhenko** — Сторінка 3:
```
3
```

**Grade 7, litvinova** — Сторінка 1:
```
Підручник 
 
         видавництво "Ранок"
```

**Grade 6, shchupak** — Сторінка 2:
```
Український освітянський 
видавничий центр 
«Оріон»
```

**Grade 6, shchupak** — Сторінка 260:
```
Український освітянський 
видавничий центр 
«Оріон»
```

**Grade 5, avramenko** — Сторінка 89:
```
89
 § 38–39.  Наголос.  Орфоепічна  помилка
ІІ. Квартал, кілометр, корисний, курятина, листопад, навчання, на-
чинка, ненависть, новий, обіцянка, одинадцять, ознака, олень, підлітко-
вий, пізнання, подруга, поняття.
ІІІ. Посередині, проміжок, псевдонім, разом, сантиметр, середина, сли-
на, стрибати, текстовий, течія, тулуб, фартух, фаховий, фольга, чорнозем, 
чорнослив, шовковий. 
А. Запишіть неправильно наголошені слова й позначте в них наголос. 
Б. Вивчіть ці слова. 
3.	Випишіть слова, що мают
```

**Grade 5, avramenko** — Сторінка 76:
```
76
ФОНЕТИКА. ГРАФІКА. ОРФОЕПІЯ. ОРФОГРАФІЯ 
2.	Прочитайте речення та виконайте завдання.
1. Лань вискочила на широкий лан. 2. Стань, випрямся, глибоко дихай, 
аби твій фізичний стан був спокійним. 3. Син біля нічного моря спрямував 
свій погляд у далеку синь. 4. Хіба рись їсть рис? 5. Увесь берег покриває галь-
ка, а галка своїм забарвленням зливається із цими дрібними камінчиками 
(З інтернету).
А. Знайдіть і прочитайте слова, що розрізняються лише твердістю/ 
м’якістю одного з приголосних. 
Б.
```

NOTE: The textbook examples above are provided as INSPIRATION for the pedagogical approach, NOT as content to copy. For modules M15+, focus on the communicative patterns, not the letter/syllable exercises.


---

## Writing Instructions

Write the checkpoint content for **Checkpoint: Sentences** (a1 track).

- **Target**: 1200–1800 words (below 1200 = FAIL)
- **Engagement callouts**: **3+ MANDATORY** — spread across sections, at least 3 different types
- **Structure**: Use the EXACT H2 section titles listed below. Missing or renamed sections fail validation.

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Огляд (Overview)` (~180 words)
  - Структура контрольної точки TTT: консолідація навичок A1.2 — дієвідмінювання, формування питань, вираження уподобань, присвійні та вказівні займенники.
  - Мета: виявлення прогалин перед переходом до знахідного відмінка (A1.3). Практичний підхід до перевірки через реальні комунікативні завдання.
- `## Навичка 1: Дієслова (Skill 1: Verbs)` (~300 words)
  - Теперішній час I та II дієвідміни: повторення парадигм (читаю/читаєш/читає vs говорю/говориш/говорить). Зворотні дієслова (-ся/-сь).
  - Типові помилки: закінчення 3-ї особи множини (-уть/-ють vs -ать/-ять). Контрастні вправи на найчастіші дієвідмінювальні помилки початківців.
- `## Навичка 2: Питання та заперечення (Skill 2: Questions & Negation)` (~240 words)
  - Питальні слова: Хто/Що/Де/Куди/Звідки. Чи-питання з інтонацією. Побудова питальних речень із правильним порядком слів.
  - Заперечення з «не» та причинні конструкції: тому що/бо. Побудова складнопідрядних речень причини.
- `## Навичка 3: Уподобання та присвійні (Skill 3: Preferences & Possessives)` (~240 words)
  - Три конструкції уподобань: Мені подобається (Dative), Я люблю (Acc), Я хочу (+ inf/Acc). Контрастний вибір залежно від ситуації.
  - Присвійні займенники: мій/моя/моє/мої, твій/твоя. Вказівні займенники: цей/ця/це/ці, той/та/те/ті. Узгодження за родом та числом.
- `## Інтеграційне завдання (Integration Task)` (~240 words)
  - Комбінований діалог із використанням усіх навичок A1.2: дієвідмінювання, питання, уподобання, присвійні та вказівні займенники в одному комунікативному сценарії.
  - Самооцінка готовності до переходу на A1.3 (Cases & Navigation): підбиття підсумків засвоєних структур.
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Checkpoint Writing Style

**Tone: Celebratory and encouraging.** The learner has completed a block of lessons. This is a victory lap, not an exam.

- Open with acknowledgment of progress: "You've learned X, Y, and Z — now let's see how they work together!"
- Use warm, encouraging language throughout
- Frame challenges as "puzzles" or "adventures", not "tests"
- End with a clear signal of readiness for the next phase

**Structure each skill-review section as:**
1. **Brief reminder** (1-2 sentences max) of what the skill is — NOT a full re-explanation
2. **New context** that exercises the skill — a scenario, dialogue, or situation the learner hasn't seen
3. **Integration challenge** that combines this skill with others from the same block
4. **Reinforcement callout** (tip, culture note, or encouragement)

**Integration sections must:**
- Combine 2+ skills from different prior modules in a single task
- Use a realistic scenario (ordering food, describing a room, introducing family)
- Show how grammar and vocabulary work together in natural speech

### Immersion Target

TARGET: 15-25% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes — never in flowing prose.
Ukrainian sentences max 10 words. Mix container types.

### Structural Containment (how to achieve immersion without code-switching)

**Three rules govern where each language appears:**

1. **Paragraphs = English** with Ukrainian vocabulary **bolded inline**: "Remember **книга** (book)? Now combine it with the adjective **нова** to get **нова книга**."

2. **Full Ukrainian sentences = prefer structural containers.** Ukrainian sentences (3+ words with a verb) work best in containers, but short inline Ukrainian is fine in explanatory context (e.g., "Remember how **Це нова книга** uses the adjective before the noun?"):
   - **Tables** — paradigms, vocabulary groups, gender sorting (tables count ZERO for immersion — use for structure/explanation only)
   - **Bulleted example lists** — Ukrainian line + English gloss: `- **Читай книгу!** — Read the book!`
   - **Blockquote dialogues** — mini-conversations with labeled speakers
   - **Pattern boxes** — transformations: `читати → читай → читайте`

3. **Vary containers.** Never use the same container type twice in a row.

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Огляд (Overview) | 180+ |
| Навичка 1: Дієслова (Skill 1: Verbs) | 300+ |
| Навичка 2: Питання та заперечення (Skill 2: Questions & Negation) | 240+ |
| Навичка 3: Уподобання та присвійні (Skill 3: Preferences & Possessives) | 240+ |
| Інтеграційне завдання (Integration Task) | 240+ |
| **Total** | **1200+ (aim for ~1440)** |

### Callout Types to Use

- `[!tip]` — practical reminders for learners
- `[!warning]` — common mistakes to watch for (review traps)
- `[!did-you-know]` — fun facts about Ukrainian
- `[!culture]` — cultural connections that make the language come alive

### Audit Gates (your content will be checked for)

- **Word count**: minimum 1200 words
- **Russianisms**: banned (кушати, получати, etc.)
- **Russian characters**: ы, э, ё, ъ must NEVER appear
- **Euphony**: і/й, у/в alternation
- **Engagement callouts**: 3+
- **IPA/phonetic brackets**: BANNED
- **New grammar/vocabulary**: BANNED — checkpoint reviews only

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


---

## Pre-Submission Checks

1. **Plan compliance**: Does every point in the content_outline have dedicated prose?
2. **Word count**: Does the total meet 1200?
3. **Language scan**: No Russianisms, no Russian characters, no IPA, no Latin transliteration?
4. **Decodable vocabulary**: Does every Ukrainian word use only the allowed letter set?
5. **Synthesis check**: Does every section COMBINE skills rather than re-teach them individually?
6. **No new material**: Have you avoided introducing any grammar or vocabulary not from prior modules?



---

## Output Format

```
===CONTENT_START===

<!-- SCOPE
Covers: Review and synthesis of {prior modules}
Not covered:
  - New grammar or vocabulary
  - {next phase topic} → {next-slug}
-->

# {Title}

> **Чому це важливо?**
>
> {2-3 celebratory sentences acknowledging progress}

## {Section 1}
...

---

# Підсумок

{Summary + 3-4 self-check questions. Each question MUST include an English translation if the question is in Ukrainian. Format: "Який? (Which?) — answer / відповідь"}

---

===CONTENT_END===
```

```
===WORD_COUNTS===
Section "{name}": {count} words (minimum: {allocation})
...
Total: {total} words (target: 1200)
===WORD_COUNTS===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Beginner Checkpoint Content
**Step**: {what you were doing}
**Friction Type**: NONE | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT generate activities or vocabulary tables (separate phase)
- Do NOT introduce new vocabulary or grammar not from prior modules
- **VOCABULARY COVERAGE RULE:** All words from `vocabulary_hints` in the plan MUST appear at least once in the module content.
- Do NOT skip sections from the content_outline
- Do NOT write fewer than 1200 words
- Do NOT use straight quotes "..." — always «...»
- Do NOT re-explain concepts in detail — brief reminders only, then synthesize

</prompt>

## The Plan

<plan>
module: a1-024
level: A1
sequence: 24
slug: checkpoint-sentences
version: '2.0'
title: 'Checkpoint: Sentences'
subtitle: Can You Do the A1.2 Skills?
focus: checkpoint
pedagogy: TTT
phase: A1.2 [Verbs & Sentences]
word_target: 1200
objectives:
- Demonstrate verb conjugation fluency for I and II conjugation
- Form questions and negations correctly with appropriate word order
- Express preferences using three constructions (подобається, люблю, хочу)
- Use possessives and demonstratives with correct gender and number agreement
content_outline:
- section: Огляд (Overview)
  words: 180
  points:
  - 'Структура контрольної точки TTT: консолідація навичок A1.2 — дієвідмінювання,
    формування питань, вираження уподобань, присвійні та вказівні займенники.'
  - 'Мета: виявлення прогалин перед переходом до знахідного відмінка (A1.3). Практичний
    підхід до перевірки через реальні комунікативні завдання.'
- section: 'Навичка 1: Дієслова (Skill 1: Verbs)'
  words: 300
  points:
  - 'Теперішній час I та II дієвідміни: повторення парадигм (читаю/читаєш/читає vs
    говорю/говориш/говорить). Зворотні дієслова (-ся/-сь).'
  - 'Типові помилки: закінчення 3-ї особи множини (-уть/-ють vs -ать/-ять). Контрастні
    вправи на найчастіші дієвідмінювальні помилки початківців.'
- section: 'Навичка 2: Питання та заперечення (Skill 2: Questions & Negation)'
  words: 240
  points:
  - 'Питальні слова: Хто/Що/Де/Куди/Звідки. Чи-питання з інтонацією. Побудова питальних
    речень із правильним порядком слів.'
  - 'Заперечення з «не» та причинні конструкції: тому що/бо. Побудова складнопідрядних
    речень причини.'
- section: 'Навичка 3: Уподобання та присвійні (Skill 3: Preferences & Possessives)'
  words: 240
  points:
  - 'Три конструкції уподобань: Мені подобається (Dative), Я люблю (Acc), Я хочу (+
    inf/Acc). Контрастний вибір залежно від ситуації.'
  - 'Присвійні займенники: мій/моя/моє/мої, твій/твоя. Вказівні займенники: цей/ця/це/ці,
    той/та/те/ті. Узгодження за родом та числом.'
- section: Інтеграційне завдання (Integration Task)
  words: 240
  points:
  - 'Комбінований діалог із використанням усіх навичок A1.2: дієвідмінювання, питання,
    уподобання, присвійні та вказівні займенники в одному комунікативному сценарії.'
  - 'Самооцінка готовності до переходу на A1.3 (Cases & Navigation): підбиття підсумків
    засвоєних структур.'
vocabulary_hints:
  required:
  - читати (to read) — читати книгу, я читаю; I conjugation review
  - писати (to write) — писати лист, я пишу; I conjugation review
  - говорити (to speak) — говорити українською, я говорю; II conjugation review
  - подобатися (to like) — мені подобається, тобі подобається; Dative construction
  - хотіти (to want) — я хочу їсти, я хочу каву; Irregular conjugation
  - мій (my m.) — мій телефон, мій друг; Possessive review
  - твій (your m.) — твій будинок, твоя книга; Possessive review
  - цей (this m.) — цей стілець, ця книга; Demonstrative review
  - той (that m.) — той будинок, та вулиця; Demonstrative review
  - хто (who) — Хто це? Хто говорить?; Question word review
  - що (what) — Що це? Що ти хочеш?; Question word review
  - де (where) — Де ти? Де кафе?; Question word review
  recommended:
  - тому що (because) — тому що я хочу; Causal conjunction
  - бо (because) — бо мені подобається; Colloquial causal conjunction
  - звідки (from where) — Звідки ти?; Question word
  - куди (where to) — Куди ти йдеш?; Direction question word
activity_hints:
- type: quiz
  focus: A1.2 grammar and vocabulary comprehensive test
  items: 30
connects_to:
- a1-25 (The Accusative I)
prerequisites:
- a1-23 (What Time Is It)
persona:
  voice: Patient Supportive Tutor
  role: Language Examiner
grammar:
- Present tense conjugation (I and II)
- Question words and Чи-questions
- Preference constructions (Dative, Accusative, Infinitive)
- Possessive pronouns
- Demonstrative pronouns
register: розмовний

</plan>

## Audit Gates

## Audit Gates (your content will be checked against these)

Level: A1
Word target: 1200
Word ceiling: ~1800 (exceeding = FAIL)
Min activities: 8
Min engagement boxes: 3
Min activity types: 4

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