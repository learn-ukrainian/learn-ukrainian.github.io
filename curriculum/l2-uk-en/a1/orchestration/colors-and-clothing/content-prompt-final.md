**Curriculum context:** This is Module 12 of the A1 track (Ukrainian for English speakers). Title: "Colors & Clothing" — Describing What You Wear. Phase: A1.1 [First Contact]. Previous module: Describing Things Adjectives. Next module: Plurals And Alternation.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/colors-and-clothing-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/colors-and-clothing.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Color adjectives with agreement Clothing vocabulary", grade=1-2)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 11
**Previous module:** Describing Things - Adjectives

**Cumulative vocabulary (163 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, ніс, мак, сік, стіл, тут, там, привіт, дякую, це
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, сало, хліб
зуб, дім, вовк, жук, шапка, гора, рука, бабуся, павук, ґанок
сіль, люди, суп, вода, цибуля, люк, Львів, кінь, осінь, м'ясо
п'ять, сім'я, м'яч, цукор, час, чай, черепаха, що, щастя, факт
джерело, бджола, дзвін, склад, голосний, приголосний, перенесення, сестра, вікно, ґудзик
пальці, книга, вулиця, автобус, брат, море, ніч, земля, серце, сонце
машина, ім'я, артефакт, зона, укриття, добрий ранок, добрий день, добрий вечір, до побачення, будь ласка
вибачте, перепрошую, дуже приємно, пане, пані, бувай, здрастуйте, ласкаво просимо, на все добре, добраніч
ти, ви, як справи, я, він, вона, воно, ми, вони, хто
студент, студентка, українець, українка, вчитель, вчителька, звати, ось, друзі, цей
ця, ці, той, та, те, ті, телефон, кімната, стілець, ліжко
лампа, шафа, двері, ніж, ложка, крісло, диван, новий, старий, гарний
великий, малий, добрий, поганий, цікавий, синій, червоний, молодий, дорогий, дешевий
смачний, зелений, рідний

**Grammar already taught (40 topics):**
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

**Coming next (module after this):** Noun plural formation, Vowel alternation (і → о/е), Adjective plural agreement
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- білий (white) — біла сорочка, білий сніг, білий світ; частотне (High Core A1); символ чистоти та божественного світу
- чорний (black) — чорні штани, чорна кава, чорний хліб; символ родючої землі та мудрості
- червоний (red) — червона сукня, червона ручка, червона калина; символ життя, любові та енергії
- синій (blue) — сині джинси, синій светр; частотне вживання для повсякденного одягу
- зелений (green) — зелена трава, зелений колір
- сорочка (shirt) — вишита сорочка, біла сорочка, одягати сорочку; частотне (High Core A1); основа традиційного вбрання
- штани (pants) — нові штани, джинсові штани; plural-only (pluralia tantum); завжди вживається в множині
- сукня (dress) — вечірня сукня, нова сукня; частотний та стилістично вишуканий синонім до 'плаття'
- куртка (jacket) — тепла куртка, осіння куртка; частотне (High Core A1)

**Recommended** (use in your content to reach the vocabulary target):
- плаття (dress) — розмовний синонім до 'сукня'; літнє плаття
- жовтий (yellow) — жовте сонце, жовтий лимон
- светр (sweater) — вовняний светр, синій светр
- окуляри (glasses) — великі окуляри; plural-only
- джинси (jeans) — сині джинси; plural-only; відмінюється як 'штани'

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

### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **ULP S1 Ep25: Colors in Ukrainian + Pronunciation Trainer**
  URL: https://www.ukrainianlessons.com/episode25/
  Relevance: 0.5
  Topics: vocabulary, colors, pronunciation

- **ULP S1 Ep32: Shopping for clothes — Accusative case in Ukrainian**
  URL: https://www.ukrainianlessons.com/episode32/
  Relevance: 0.4
  Topics: grammar, cases, accusative, vocabulary, clothing

- **ULP S6 Ep228: Ukrainian Lessons Podcast Season 6**
  URL: https://www.ukrainianlessons.com/episode228/
  Relevance: 0.3
  Topics: vocabulary, colors, culture, poetry

### Blog Articles & Guides
- **Ukrainian Phrasebook: Clothing** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ph-clothing/
  Relevance: 0.4
  Topics: clothing, shopping


### Textbook References
- **Grade 1, Сторінка 61**
  61
М’ЯКИЙ ПРИГОЛОСНИЙ ЗВУК [й]
Назви предмети. Як вимовляється звук [й] у словах?
М АЙ|К А
Й О Д
СЛОВА — НАЗВИ ОЗНАК
Добери слова до малюнків.
 
холодний 
сірий 
білий 
зелений
 
високий 
довгий 
теп...

- **Grade 4, Сторінка 68**
  68
РОЗУМІЄМО КРАСУ Й ДОБРО
РОЗУМІЄМО КРАСУ Й ДОБРО
 
Наближається до нас срібна зима. Ця пора року має 
свої кольори, звуки, малюнки, форми. Тільки приглядай-
ся, уявляй, доповнюй. Тоді побачиш ту чар...

- **Grade 10, Сторінка 31**
  31
Слово і  контекст. Залежність значень слова від контексту. Слововживання § 5 
47. Попрацюйте в  групах. Прочитайте. Усно перекажіть текст, замінивши по-
дані в  ньому приклади іншими, самостійно д...

- **Grade 6, Сторінка 34**
  34
1.	Прочитайте речення та виконайте завдання. 
Ми беремо на себе відпові­
дальність, коли приручаємо ко­
та чи собаку. 
Руденьке кошеня зіщулилося, 
помітивши чорного розлюченого 
собацюру.
А.	 У як...

- **Grade 8, Сторінка 158**
  34. ОДНОРІДНІ Й НЕОДНОРІДНІ ОЗНАЧЕННЯ
Про те, коли два й більше означень однорідні, та про інтонування речень 
із такими означеннями
ПРИГАДАЙМО. Що таке означення та означувані слова? 362	 А. Знайдіть...






---

## 4. Outline

Write **Colors & Clothing** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ та культурний контекст (Introduction & Cultural Context)` (~250 words)
  - Символізм кольорів в українській традиції: червоний як колір життя та любові, чорний як символ родючої землі та мудрості, білий як знак чистоти. Пов'язання з фольклорними образами (червона калина, чорний хліб).
  - Вишиванка як оберіг (talisman): функція вишивки на комірі та манжетах як захисного кола, що охороняє власника. Концепція 'закриття' енергетичних зон через візерунок.
- `## Презентація кольорів та граматика узгодження (Colors & Grammar of Agreement)` (~300 words)
  - Презентація основних кольорів згідно з Державним стандартом (§4.2.1.2): білий, чорний, червоний, синій, зелений, жовтий.
  - Узгодження прикметників з іменниками в роді: детальне відпрацювання закінчень (-ий/-а/-е). Виправлення типової помилки 'червоний сорочка' через контрастні пари: червоний светр (M) vs червона сорочка (F).
  - Незмінювані кольори-запозичення (бордо, беж, хакі) — пояснення відсутності закінчень незалежно від роду іменника.
- `## Одяг — Clothing Vocabulary` (~350 words)
  - Лексика теми 'Одяг': сорочка, штани, сукня, куртка, светр. Стилістична різниця між синонімами: 'сукня' (елегантний/офіційний варіант) та 'плаття' (загальна назва).
  - Опис одягу через прикметник + іменник (verb-free): червона сукня, синій светр, білі штани. Gender agreement practice with clothing: чорний светр (M), чорна куртка (F), чорне плаття (N).
  - Особливості Pluralia Tantum: штани, джинси, окуляри. Узгодження прикметників у множині ('ці штани', 'нові джинси'); займенник 'одні' замість 'один'.
- `## Практичне застосування — Describing Outfits` (~300 words)
  - Опис одягу інших людей через verb-free patterns: «Це червона сукня», «Ці штани — сині», «Мій светр — зелений». Practice combining colors with clothing items and gender agreement.
  - Культурний контекст одягу: кольори вишиванки за регіонами, повсякденний стиль українців. Описи з використанням прикметників: «Це традиційна сорочка», «Ця вишиванка — червона й чорна».
- `## Підсумок — Summary` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ та культурний контекст (Introduction & Cultural Context) | 250+ |
| Презентація кольорів та граматика узгодження (Colors & Grammar of Agreement) | 300+ |
| Одяг — Clothing Vocabulary | 350+ |
| Практичне застосування — Describing Outfits | 300+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Color adjectives with agreement Clothing vocabulary", grade=1-2)` — find how textbooks teach this
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
**Required types:** match-up, match-up, fill-in, fill-in

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
