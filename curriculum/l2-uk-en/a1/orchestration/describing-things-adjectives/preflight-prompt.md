You are about to build a module using the prompt below. This prompt has been carefully engineered to produce content that passes all audit gates. Your job is to confirm it is ready.

**Default answer: PASS.** This prompt is designed to work. Only report issues if something will genuinely cause an audit gate to FAIL.

## The Prompt

<prompt>
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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/describing-things-adjectives-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/describing-things-adjectives.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Adjective endings for gender (m/f/n) Hard stem adjectives (-ий/-а/-е/-і)", grade=1-2)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 10
**Previous module:** My World: Objects

**Cumulative vocabulary (156 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, суп, хліб
зуб, дім, вовк, жук, шапка, гора, рука, бабуся, павук, ґанок
сіль, люди, вода, люк, сестра, дерево, вулиця, автобус, бібліотека, університет
склад, переніс, голосний, приголосний, острів, сім'я, ґудзик, кава, чай, замок
писати, школа, добрий, далеко, наголос, інтонація, питання, відповідь, хата, книжка
дорога, кафе, він, вона, воно, книга, слово, мова, вікно, брат
ніч, час, море, сонце, земля, Добрий день, Добрий ранок, Добрий вечір, Привіт, До побачення
Па-па, Дякую, Будь ласка, Вибачте, Перепрошую, Так, Ні, Як справи?, Добре, Погано
Нормально, Чудово, Смачного, На здоров'я, Добраніч, це, я, ти, ми, ви
вони, хто, що, студент, студентка, українець, українка, вчитель, вчителька, ось
мене звати, особовий займенник, займенник, граматичний рід, рід, телефон, дуже приємно, давай на ти, удома, на роботі
підручник, паспорт, цей, ця, ці, той, та, те, ті, кімната
стілець, ліжко, лампа, шафа, двері, квартира

**Grammar already taught (37 topics):**
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

**Coming next (module after this):** Color adjectives with agreement, Clothing vocabulary, Adjective + noun gender agreement with clothing items
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- новий (new) — Collocations: новий рік, новий день, нове життя; Top 100 high-frequency adjective.
- старий (old/ancient) — Collocations: старий будинок, стара книга; used for describing St. Sophia's Cathedral.
- гарний (beautiful/nice) — Collocations: гарна погода, гарний день, гарна дівчина; high-frequency social descriptor.
- великий (big/grand) — Collocations: велике місто, велика родина, великий привіт; essential for scale.
- малий (small) — Collocations: малий бізнес, мале вікно, мале дитя; high-frequency antonym.
- добрий (good/kind) — Collocations: добрий день, добрий вечір, добра людина; essential for greetings and character.
- поганий (bad) — Collocations: погана погода, поганий настрій; primary descriptor for negative states.
- цікавий (interesting) — Collocations: цікава книга, цікаве питання, цікава людина; essential for personal expression.

**Recommended** (use in your content to reach the vocabulary target):
- синій (blue) — Primary example for soft stem (-ій); practical anchor: Kyiv Metro tokens/lines.
- червоний (red) — Common hard stem adjective for color contrast.
- молодий (young) — Useful for describing people and folklore figures like Mavka.
- дорогий (expensive) — High frequency in shopping and real estate contexts.
- дешевий (cheap) — Essential antonym for shopping scenarios.
- смачний (tasty) — High-frequency descriptor for food and hospitality.
- зелений (green) — Cultural descriptor for nature and Mavka's forest context.

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 25-40% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences (3+ words with a verb) go in tables, bulleted example lists, or pattern boxes. Never write a Ukrainian sentence followed by its English translation in a prose paragraph.
Ukrainian sentences max 10 words. Mix container types — don't use tables for everything.

### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **ULP S3 Ep108: Kyiv tour + Participle in Ukrainian**
  URL: https://www.ukrainianlessons.com/episode108/
  Relevance: 0.4
  Topics: grammar, adjectives, phrases, introductions, culture

- **ULP S2 Ep56: Asking for advice + Accusative case in Ukrainian**
  URL: https://www.ukrainianlessons.com/episode56/
  Relevance: 0.3
  Topics: grammar, cases, accusative, adjectives, phrases

### Blog Articles & Guides
- **Talk Ukrainian: Adjectives** (talkukrainian)
  URL: https://talkukrainian.com/adjectives/
  Relevance: 0.7
  Topics: adjectives, прикметник, grammar

- **Dobra Forma: Adjectives (Gender and Number in Nominative)** (dobraforma)
  URL: https://opentext.ku.edu/dobraforma/chapter/16-1/
  Relevance: 0.4
  Topics: adjectives, gender, grammar

- **Ukrainian Adjectives and Adverbs Chart** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/adjectives-adverbs-chart/
  Relevance: 0.3
  Topics: adjectives, adverbs, grammar, declension


### Textbook References
- **Grade 6, Сторінка 132**
  132
1.	Прочитайте словосполучення та виконайте завдання.
дружна компанія
дружня підтримка
А.	 Якою значущою частиною відрізняються виділені прикметники?
Б.	 Доберіть до кожного з них синонім.
Прикметн...

- **Grade 2, Сторінка 12**
  12
сЛова — назви ПреДметІв
Слова — назви предметів — це іменники.
Слово іменник утворене від слова ім’я. Кожний 
предмет чи явище має своє ім’я, тобто свою назву.  
Назви зображені предмети спочатку ...

- **Grade 6, Сторінка 133**
  133
318   Прочитайте речення. Якою темою вони об’єднані? Випишіть 
прикметники разом з іменниками, від яких вони залежать. 
Визначте відміну й групу (де можна) іменників. Як ви це вста-
новили? Виділі...

- **Grade 6, Сторінка 191**
  § 40. Групи прикметників за значенням  
191
Дерев’яний, весняний, кошачий, цікавий, веселий, 
настільний, теплий, домашній, братів, шкільний, старан-
ний, спортивний, математичний, швидкий, відповідал...

- **Grade 5, Сторінка 163**
  163
РОЗВИТОК МОВЛЕННЯ
До речі…
Означення найчастіше виражені прикметниками. Їх використову­
ють в описах. Що більше означень-прикметників ви знати­мете, то 
легше вам буде висловлювати думки, описуват...






---

## 4. Outline

Write **Describing Things - Adjectives** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ: Світ прикметників (Introduction: The World of Adjectives)` (~250 words)
  - Warm-up activity: Asking questions 'Який? Яка? Яке? Які?' to describe classroom objects, reinforcing State Standard §4.2.1.2 requirements for adjective agreement in the Nominative case.
  - Cultural Hook: Introduce St. Sophia's Cathedral (Софійський собор) as the 'старий' (ancient) and 'великий' (grand) heart of Kyiv, establishing the need for descriptive language in historical contexts.
  - Bridge to A1-03: Quick review of the 'Gender Code' (masculine, feminine, neuter nouns) as the mandatory foundation for adjective agreement rules.
- `## Презентація: Тверда група (Presentation: Hard Stem Adjectives)` (~350 words)
  - Introduction to Hard Stem endings (-ий, -а, -е, -і) using high-frequency vocabulary like 'новий' and 'гарний'; include visual scaffolding with color-coded gender markers (Blue/Red/Yellow/Green).
  - Explaining Adjective Placement: Contrast attributive position ('гарна погода') with predicative position after 'бути' ('Погода гарна'), emphasizing that gender endings remain consistent.
  - Correction of Gender Mismatch: Explicitly address the common error of using masculine dictionary forms for all nouns (e.g., correcting *'новий машина'* to *'нова машина'*) with focused minimal pair drills.
  - Expanding the Descriptive Toolkit: Introduction of high-frequency opposites like 'великий/малий' and 'добрий/поганий' as identified in frequency research.
- `## Презентація 2: М'яка група та Специфіка (Presentation 2: Soft Stem and Nuances)` (~300 words)
  - Introduction to Soft Stem endings (-ій, -я, -є, -і) focusing on 'синій' as the primary example; use the Kyiv Metro 'синя лінія' (Blue Line) as a practical mnemonic anchor for A1 learners.
  - Targeting Hard/Soft Stem Confusion: Correcting the learner error of writing *'синий'* (influenced by phonetic patterns) vs. the correct Ukrainian orthography *'синій'*.
  - Plural Consistency: Highlight that plural adjectives take the ending '-і' regardless of gender (e.g., 'гарні дні', 'гарні дівчата', 'гарні вікна') to prevent the common error of using singular forms for plural nouns.
- `## Практика та Культурний контекст (Practice and Cultural Context)` (~300 words)
  - Cultural Portrait: Describe the folklore figure Mavka (Мавка) from Lesya Ukrainka's 'Forest Song' using 'молода', 'гарна', 'цікава', and 'зелена' to practice feminine adjective agreement.
  - Real Estate Persona Practice: Roleplay describing a 'нова квартира' or 'великий будинок' using vocabulary from A1-25 (Daily Routine) to solidify functional usage in physical descriptions.
  - Final Synthesis: A summary of the 'Який?' question-answer pattern for all three genders and plural, preparing learners for the upcoming color vocabulary in A1-27.
- `## Підсумок — Summary` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ: Світ прикметників (Introduction: The World of Adjectives) | 250+ |
| Презентація: Тверда група (Presentation: Hard Stem Adjectives) | 350+ |
| Презентація 2: М'яка група та Специфіка (Presentation 2: Soft Stem and Nuances) | 300+ |
| Практика та Культурний контекст (Practice and Cultural Context) | 300+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Adjective endings for gender (m/f/n) Hard stem adjectives (-ий/-а/-е/-і)", grade=1-2)` — find how textbooks teach this
2. **Write content** following the outline and lesson arc below
3. **Verify as you write**: `verify_words` on any Ukrainian word you're unsure about
4. **Create activities** from your content
5. **Verify activities**: batch `verify_words` on all activity items

### Beginner Lesson Arc

1. **WELCOME** — warm greeting, set context
2. **PREVIEW** — "By the end of this module, you'll be able to..."
3. **PRESENT** — the main content sections
4. **PRACTICE** — examples, dialogues, reading practice
5. **CELEBRATE** — in the final `## Підсумок — Summary` section, tell learners what they can now do

### Emotional Safety (scored — Beginner Safety dimension)

Use direct address ("you", "your") at least 15 times throughout the module. Include encouragement ("Great job!", "You're doing well", "Don't worry"), quick wins (learner reads their first word early), and reassurance ("This is normal", "Take your time"). The learner should feel supported, not overwhelmed.

### Writing Style

English explains; Ukrainian is what they're learning. In each section:
1. **Explain** the concept in English (with Ukrainian vocabulary **bolded inline**). Short Ukrainian phrases are fine inline.
2. **Show** with **5-10 Ukrainian examples** per grammar point using bulleted lists, dialogues, and pattern boxes.
3. **Reinforce** with a callout box (`[!tip]`, `[!warning]`, `[!note]`, `[!culture]`, `[!challenge]`, `[!practice]`)

Tables contribute zero to immersion. Use **dialogues** and **bulleted examples** for Ukrainian content.

**MANDATORY for A2+:** Reading Practice blocks after each major section (5-8 Ukrainian sentences + English translation).

**Grammar terminology by level:**
- A1 M1-M10: English terms in prose, bilingual section headings with em-dash: `## Голосні — Vowels`
- A1 M11+: Introduce Ukrainian terms with gloss: **іменник** (noun)
- A2+: Ukrainian terms freely after first gloss

### Dialogue Quality

**No echo drills.** For M5+: every dialogue MUST start with `> **(Location / Місце)**`, have a real situation, 4-6 dialogues, 4-8 lines each.

**Alphabet modules (M1-M10):** Include 4-5 micro-dialogues using decodable words + sight words. Keep them short (2-4 lines each) and conversationally natural. Good patterns:
- Greeting: `— Привіт! — Привіт!`
- Identification: `— Це кіт? — Так, це кіт.`
- Location: `— Молоко тут? — Ні, молоко там.`
- Combined: `— Мама тут? — Так, мама тут. А тато там.`

Every line must make conversational sense. Do NOT pair unrelated speech acts (e.g., "Це мама?" → "Дякую!" makes no sense). Use `search_text` to find real dialogue patterns from Grade 1 textbooks (Заhaрійчук, Большакова) and adapt them to the available letter set.

**Cite textbook adaptations:** `<!-- adapted from: {author}, Grade {N} -->`

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

- Activity **answers** must use words from your content. **Distractors** may use other level-appropriate words.
- Follow schemas exactly — `additionalProperties: false` means any unlisted field = FAIL.
- Read `schemas/activities-a1.schema.json` for full field definitions.

**Allowed types:** quiz, true-false, fill-in, match-up, anagram, unjumble, group-sort, watch-and-repeat, classify, image-to-letter
**Forbidden types:** cloze, error-correction, mark-the-words, select, translate, essay-response, critical-analysis, comparative-study, authorial-intent
**Required types:** fill-in, fill-in, match-up, fill-in

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

</prompt>

## Audit Gates (what your content will be checked against)

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

## Instructions

Read the prompt carefully. If you can build a module that passes all audit gates using this prompt, return PASS.

Only report an issue if:
- Two instructions **directly contradict** each other AND following one will FAIL a named gate
- A target is **mathematically impossible** to reach given the constraints
- A required gate has **zero guidance** in the prompt (not "could be clearer" — literally missing)

Do NOT report: style preferences, wording suggestions, minor ambiguities, things that "could be improved." Focus on issues that would prevent you from building excellent content.

**Gate names** (only these matter): Words, Activities, Density, Unique_types, Engagement, Vocab, Structure, Pedagogy, Immersion.

## Output Format (YAML)

```yaml
prompt_preflight:
  status: PASS  # or ISSUES_FOUND
  issues:
    - type: CONTRADICTION  # or MISSING_INSTRUCTION, IMPOSSIBLE_TARGET, UNCLEAR
      location: "Section 4, line about tables"
      problem: "Template says tables have highest density but audit strips tables from immersion"
      suggested_fix: "Remove 'highest density' claim, add warning that tables = zero immersion"
      severity: HIGH  # or MEDIUM, LOW
```

If there are no issues, return:
```yaml
prompt_preflight:
  status: PASS
  issues: []
```

Be SPECIFIC. Cite exact text from the prompt. Focus on issues that will cause audit FAILURES, not style preferences.