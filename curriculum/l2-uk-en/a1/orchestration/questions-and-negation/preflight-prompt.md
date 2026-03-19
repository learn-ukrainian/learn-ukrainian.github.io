You are about to build a module using the prompt below. Before you start, verify the prompt is ready.

**Default answer: PASS.** Only report genuine issues that would cause audit gate failures or introduce errors.

## The Prompt

<prompt>
**Curriculum context:** This is Module 18 of the A1 track (Ukrainian for English speakers). Title: "Questions & Negation" — Asking Questions and Saying No. Phase: A1.2 [Verbs & Sentences]. Previous module: Reflexive Verbs. Next module: Likes And Preferences.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/questions-and-negation-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/questions-and-negation.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Yes/no questions with чи Question words", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 17
**Previous module:** Reflexive Verbs (-ся)

**Cumulative vocabulary (262 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно
яблуко, риба, село, Україна, їжак, юнак, край, день, син, мій
вухо, їжа, яйце, юшка, каша, небо, сир, Європа, хліб, зуб
дім, вовк, жук, шапка, гора, рука, бабуся, павук, ґанок, кінь
люди, суп, вода, дим, люк, сіль, Львів, м'ясо, п'ять, сім'я
цукор, час, що, джерело, дзвін, осінь, м'яч, щастя, факт, бджола
дзеркало, черепаха, чай, фото, склад, голосний, приголосний, перенос, сестра, дерево
вулиця, автобус, бібліотека, університет, буква, звук, слово, книга, замок, добрий
школа, мука, хата, кава, книжка, дорога, далеко, наголос, інтонація, питання
відповідь, кафе, голос, брат, вікно, море, ніч, земля, серце, сонце
собака, ім'я, артефакт, зона, укриття, привіт, ранок, вечір, побачення, дякувати
ласка, вибачити, перепрошувати, приємно, пан, пані, ти, ви, дуже, щиро
бувати, здрастуйте, справа, це, я, він, вона, воно, ми, вони
хто, студент, студентка, вчитель, вчителька, українець, українка, ось, звати, цей
ця, ці, той, та, те, ті, телефон, кімната, стілець, ліжко
лампа, шафа, двері, квартира, ніж, ложка, блюдо, диван, крісло, річ
новий, старий, гарний, великий, малий, поганий, цікавий, синій, червоний, молодий
дорогий, дешевий, смачний, зелений, який, будинок, білий, чорний, жовтий, сорочка
штани, сукня, куртка, светр, плаття, джинси, окуляри, одяг, вишиванка, калина
дитина, людина, гроші, ножиці, маленький, де, торт, читати, писати, знати
працювати, слухати, питати, грати, чекати, думати, розуміти, вивчати, відпочивати, гуляти
відповідати, журнал, лист, радіо, повідомлення, новини, текст, говорити, робити, бачити
любити, їсти, пити, ходити, просити, сидіти, стояти, платити, вчити, дивитися
природа, сміятися, вмиватися, одягатися, називатися, вчитися, займатися, повертатися, голитися, зупинятися
знайомитися, цікавитися, подобатися, митися, зустрічатися, вітатися, цілуватися, мити, одягати, називати
розминатися, розслаблятися

**Grammar already taught (59 topics):**
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
- Noun plural formation
- Vowel alternation (і → о/е)
- Adjective plural agreement
- Cyrillic alphabet (all 33 letters)
- Noun gender (m/f/n)
- Adjective-noun agreement
- Plural formation
- First Conjugation pattern (-ати → -аю, -аєш...)
- Personal verb endings
- Imperfective aspect introduction
- Second Conjugation pattern (-ити → -у, -иш...)
- Consonant mutation patterns
- Irregular verbs
- Reflexive particle -ся/-сь
- Conjugation of reflexive verbs
- Transitive vs reflexive pairs

**Coming next (module after this):** Dative construction Мені подобається, Люблю + Accusative, Хочу + infinitive
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- чи (question particle) — Чи ти...? Чи це...? (Polite/Standard question marker)
- що (what) — Що це? Що ти робиш?; mention spoken variant 'шо' (Top 10 word)
- хто (who) — Хто це? Хто там? (Top 50 word)
- де (where) — Де ти? Де туалет? (High frequency adverb)
- коли (when) — Коли сніданок? Коли ти вдома?
- не (not) — не знаю, не розумію, не хочу (Top 5 particle; always before the verb)
- так (yes) — так, звичайно; так, будь ласка
- ні (no) — ні, дякую; ні, не... (Phonetic contrast with 'не')

**Recommended** (use in your content to reach the vocabulary target):
- куди (where to) — Куди ви їдете? (Standard §4.3.1)
- звідки (from where) — Звідки ти? (Standard §4.3.1)
- чому (why) — Чому ти тут? Чому ні?
- як (how) — Як справи? Як це?
- скільки (how much) — Скільки це коштує?
- завжди (always) — я завжди тут
- ніколи (never) — я ніколи не... (Requires double negation)

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

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

### Videos
- **Ukrainian listening practice: What do you like to eat? Що ви любите їсти? 🥐 Slow vs. Fast input** (Ukrainian with Olha)
  URL: https://www.youtube.com/watch?v=QE9JOcQfLE0
  Score: 0.8 -- The video provides excellent listening practice using core module concepts: questions with 'що' and 'які', and negation with 'не'. It reinforces the grammar taught in the module.
  Suggested placement: After section 'Practice: The Interrogation Game' — as an additional listening comprehension exercise reinforcing question words and negation in context.
  Key excerpt: Вітаю. Сьогодні я вам розповім про те, що я зазвичай їм щодня. ... А які ваші улюблені страви та напої?


### Blog Articles & Guides
- **Питальні слова** (All question words with examples)
  URL: https://www.ukrainianlessons.com/question-words/
  Relevance: 1.0

- **Double Negation Rules** (Master Ukrainian negative sentences)
  URL: https://www.ukrainianlessons.com/negation-in-ukrainian/
  Relevance: 1.0

- **Short Ukrainian Questions** (Practical phrases for travelers)
  URL: https://www.ukrainianlessons.com/useful-ukrainian-questions/
  Relevance: 1.0

- **Dobra Forma: Genitive Case for Direct Objects after Negation (Neuter and Masculine)** (dobraforma)
  URL: https://opentext.ku.edu/dobraforma/chapter/5-3/
  Relevance: 0.3
  Topics: genitive, negation, cases, grammar

- **Dobra Forma: Genitive Case for Direct Objects after Negation (Masculine)** (dobraforma)
  URL: https://opentext.ku.edu/dobraforma/chapter/5-4/
  Relevance: 0.3
  Topics: genitive, negation, cases, grammar


### Textbook References
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

- **Grade 6, Сторінка 269**
  § 54. Розряди займенників за значенням та особливості відмінювання   
269
Зверніть увагу на варіанти наголошування запереч-
них займенників ніхто і  ніщо в  непрямих відмінках: 
ніко́го — нíкого, нічо...

- **Grade 6, Сторінка 264**
  Розділ 8. Займенник 
264
Питальні й  відносні займенники
Питальні займенники вживаються в  питальних ре-
ченнях. Ці займенники вам добре знайомі, адже вони 
є  питаннями до всіх іменних частин мови: х...

- **Grade 8, Сторінка 2**
  РЕЧЕННЯ
ЧЛЕНИ  РЕЧЕННЯ
ВІДМІНКИ
Критерій
Типи речень
За метою
висловлювання
розповідні
(містять повідомлення про факти,  
події чи явища дійсності)
питальні
(містять запитання)
спонукальні
(виражають ...

- **Grade 6, Сторінка 186**
  186
1.	Прочитайте словосполучення та виконайте завдання. 
нікого не оминути	
мою увагу
чимсь зайнятий	
набрати всього
у тій бібліотеці 	
пишатися нею
А.	 Визначте відмінки виділених займенників.
Б.	 В...






---

## 4. Outline

Write **Questions & Negation** for the a1 track. Target: 1200–1800 words.

### CRITICAL: EXACT H2 HEADERS (copy-paste, do not alter)

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ: Основи заперечення та інтонації (Introduction: Basics of Negation and Intonation)` (~250 words)
  - The simplicity of Ukrainian syntax: unlike English, there is no auxiliary 'do/does'. This section explicitly addresses the 'Do Trap' by comparing direct statement-to-question transformations.
  - Introducing the negation particle 'не' (not) vs the response 'ні' (no). Learner error focus: avoiding the phonetic and functional confusion between these two essential words ('Ні, я не знаю').
  - Visualizing the voice: using arrows (↗) to illustrate rising intonation in questions without 'чи', contrasting with the falling tone (↘) of negative statements.
- `## Презентація: Питальні конструкції (Presentation: Interrogative Structures)` (~325 words)
  - Standard yes/no questions using the particle 'чи'. Contextualizing 'чи' as a marker of politeness, emphasis, or formal register in sentences like 'Чи ви розумієте?'.
  - The spoken alternative: rising intonation alone. Explain that dropping 'чи' is standard in casual conversation but requires a sharp pitch rise (↗) on the focus word to avoid sounding like a statement.
  - Comprehensive set of interrogative words aligned with State Standard §4.3.1 (A1): що, хто, де, коли, куди, звідки. Note on the standard 'що' vs the ubiquitous spoken variant 'шо'.
  - Answering patterns: 'Так' vs 'Ні'. Practice responding to 'чи'-questions with confirmation or negation using 'так' or 'ні' + 'не' + verb.
- `## Практика: Тренування заперечень та запитань (Practice: Drilling Negation and Questions)` (~250 words)
  - Sentence transformation drills: turning positive statements into negative ones and then into interrogative forms (e.g., 'Ти знаєш' -> 'Ти не знаєш' -> 'Чи ти знаєш?').
  - Error correction lab: identifying and fixing 'English-transfer' questions that incorrectly use auxiliary verbs or flat intonation patterns.
  - Matching exercise: pairing question words ('хто', 'що', 'де', 'куди') with appropriate situational answers to build contextual syntactic intuition.
- `## Продукція: Комунікативні сценарії (Production: Communicative Scenarios)` (~250 words)
  - The Café Scenario: asking questions about the menu, availability, and prices (e.g., 'Де кава?', 'Скільки це коштує?', 'Чи є цукор?').
  - Roleplay: 'The Investigative Journalist' (Persona). Students interview each other using a checklist of question words to uncover basic facts about their partners.
  - Negative responses and frequency: practicing 'Ні, я ніколи не...' to integrate frequency adverbs like 'ніколи', 'завжди', and 'часто' into negative statements.
- `## З'єднуємо речення (Joining Sentences)` (~200 words)
  - Compound sentences with і/й (and), а (and/but), але (but): Я люблю каву, і він любить каву. Я люблю каву, але він любить чай. State Standard §4.3.2 requires these at A1.
  - Causal clauses with тому що / бо (because): Я не йду, тому що я хворий. Він не прийшов, бо холодно. бо is more colloquial, тому що is neutral/formal.
  - Pattern: [sentence 1] + [conjunction] + [sentence 2]. The word order within each sentence stays the same — just add the connector.
- `## Культурний контекст та ALF (Cultural Context and ALF)` (~125 words)
  - Register nuances: when to use the formal 'чи' (standard/polite) versus intonation-only questions (conversational/casual) in various Ukrainian social settings.
  - Pop culture integration: the iconic ALF quote 'Ти не любиш котів? Ти просто не вмієш їх готувати!'. Use this to demonstrate negation, rhetorical intonation, and a touch of dark Ukrainian humor.
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ: Основи заперечення та інтонації (Introduction: Basics of Negation and Intonation) | 250+ |
| Презентація: Питальні конструкції (Presentation: Interrogative Structures) | 325+ |
| Практика: Тренування заперечень та запитань (Practice: Drilling Negation and Questions) | 250+ |
| Продукція: Комунікативні сценарії (Production: Communicative Scenarios) | 250+ |
| З'єднуємо речення (Joining Sentences) | 200+ |
| Культурний контекст та ALF (Cultural Context and ALF) | 125+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Rules (read ALL before writing)

### RULE 1: GRAMMAR — see Section 6

Section 6 (Hard Constraints) defines exactly what grammar structures you may use for this module. Follow those constraints — they vary by module number.

### RULE 2: VOCABULARY

Prioritize these Ukrainian words (from the plan). You may also use words from the cumulative vocabulary and common Ukrainian words, but these are your core teaching targets:

**Allowed Ukrainian words:** чи, що, хто, де, коли, не, так, ні, куди, звідки, чому, як, скільки, завжди, ніколи

### RULE 3: VARIATION

Vary your formatting across sections. Do NOT start 3+ sections the same way. Mix: bulleted lists, dialogues, comparison patterns, callout boxes, practice exercises.

### RULE 4: STRESS MARKS

Write Ukrainian without stress marks — the pipeline adds them after. Exception: if the plan uses capitalized stress (молокО, далекО) to indicate stress position, you may use that notation in teaching examples.

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
**Required types:** fill-in, fill-in, fill-in, fill-in

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

- **No Russianisms**: кушати→їсти, получати→отримувати, самий→найкращий
- **No Russian characters**: ы, э, ё, ъ — never
- **No colonial framing**: never define Ukrainian by comparing it to Russian. Don't say "unlike Russian..." or "not found in Russian." Present Ukrainian on its own terms
- **No IPA or Latin transliteration** — stress marks (´) only
- **Ukrainian quotes** in content: «...» | **YAML values**: plain text or single quotes (never «»)
- **Euphony** (у/в, і/й alternation): follow rules in the shared content rules section below — audit flags violations
- **YAML colon values**: quote with single quotes: `'text: with colon'`
- H2 titles must match the outline EXACTLY. You MAY add H3 sub-headings within H2 sections (e.g., for individual letters, grammar sub-topics)
- **MUST end with `## Підсумок`** with self-check questions

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
module: a1-018
level: A1
sequence: 18
slug: questions-and-negation
version: '2.0'
title: Questions & Negation
subtitle: Asking Questions and Saying No
focus: grammar
pedagogy: PPP
phase: A1.2 [Verbs & Sentences]
word_target: 1200
objectives:
- Learner can ask yes/no questions using 'чи'
- Learner can form questions with question words (що, хто, де, коли)
- Learner can make negative statements with 'не'
- Learner can explain frequency adverbs (завжди, часто, іноді, ніколи)
content_outline:
- section: 'Вступ: Основи заперечення та інтонації (Introduction: Basics of Negation and Intonation)'
  words: 250
  points:
  - 'The simplicity of Ukrainian syntax: unlike English, there is no auxiliary ''do/does''. This section explicitly addresses
    the ''Do Trap'' by comparing direct statement-to-question transformations.'
  - 'Introducing the negation particle ''не'' (not) vs the response ''ні'' (no). Learner error focus: avoiding the phonetic
    and functional confusion between these two essential words (''Ні, я не знаю'').'
  - 'Visualizing the voice: using arrows (↗) to illustrate rising intonation in questions without ''чи'', contrasting with
    the falling tone (↘) of negative statements.'
- section: 'Презентація: Питальні конструкції (Presentation: Interrogative Structures)'
  words: 325
  points:
  - Standard yes/no questions using the particle 'чи'. Contextualizing 'чи' as a marker of politeness, emphasis, or formal
    register in sentences like 'Чи ви розумієте?'.
  - 'The spoken alternative: rising intonation alone. Explain that dropping ''чи'' is standard in casual conversation but
    requires a sharp pitch rise (↗) on the focus word to avoid sounding like a statement.'
  - 'Comprehensive set of interrogative words aligned with State Standard §4.3.1 (A1): що, хто, де, коли, куди, звідки. Note
    on the standard ''що'' vs the ubiquitous spoken variant ''шо''.'
  - 'Answering patterns: ''Так'' vs ''Ні''. Practice responding to ''чи''-questions with confirmation or negation using ''так''
    or ''ні'' + ''не'' + verb.'
- section: 'Практика: Тренування заперечень та запитань (Practice: Drilling Negation and Questions)'
  words: 250
  points:
  - 'Sentence transformation drills: turning positive statements into negative ones and then into interrogative forms (e.g.,
    ''Ти знаєш'' -> ''Ти не знаєш'' -> ''Чи ти знаєш?'').'
  - 'Error correction lab: identifying and fixing ''English-transfer'' questions that incorrectly use auxiliary verbs or flat
    intonation patterns.'
  - 'Matching exercise: pairing question words (''хто'', ''що'', ''де'', ''куди'') with appropriate situational answers to
    build contextual syntactic intuition.'
- section: 'Продукція: Комунікативні сценарії (Production: Communicative Scenarios)'
  words: 250
  points:
  - 'The Café Scenario: asking questions about the menu, availability, and prices (e.g., ''Де кава?'', ''Скільки це коштує?'',
    ''Чи є цукор?'').'
  - 'Roleplay: ''The Investigative Journalist'' (Persona). Students interview each other using a checklist of question words
    to uncover basic facts about their partners.'
  - 'Negative responses and frequency: practicing ''Ні, я ніколи не...'' to integrate frequency adverbs like ''ніколи'', ''завжди'',
    and ''часто'' into negative statements.'
- section: "З'єднуємо речення (Joining Sentences)"
  words: 200
  points:
  - "Compound sentences with і/й (and), а (and/but), але (but):
    Я люблю каву, і він любить каву. Я люблю каву, але він любить чай.
    State Standard §4.3.2 requires these at A1."
  - "Causal clauses with тому що / бо (because):
    Я не йду, тому що я хворий. Він не прийшов, бо холодно.
    бо is more colloquial, тому що is neutral/formal."
  - "Pattern: [sentence 1] + [conjunction] + [sentence 2]. The word order
    within each sentence stays the same — just add the connector."
- section: Культурний контекст та ALF (Cultural Context and ALF)
  words: 125
  points:
  - 'Register nuances: when to use the formal ''чи'' (standard/polite) versus intonation-only questions (conversational/casual)
    in various Ukrainian social settings.'
  - 'Pop culture integration: the iconic ALF quote ''Ти не любиш котів? Ти просто не вмієш їх готувати!''. Use this to demonstrate
    negation, rhetorical intonation, and a touch of dark Ukrainian humor.'
vocabulary_hints:
  required:
  - чи (question particle) — Чи ти...? Чи це...? (Polite/Standard question marker)
  - що (what) — Що це? Що ти робиш?; mention spoken variant 'шо' (Top 10 word)
  - хто (who) — Хто це? Хто там? (Top 50 word)
  - де (where) — Де ти? Де туалет? (High frequency adverb)
  - коли (when) — Коли сніданок? Коли ти вдома?
  - не (not) — не знаю, не розумію, не хочу (Top 5 particle; always before the verb)
  - так (yes) — так, звичайно; так, будь ласка
  - ні (no) — ні, дякую; ні, не... (Phonetic contrast with 'не')
  recommended:
  - куди (where to) — Куди ви їдете? (Standard §4.3.1)
  - звідки (from where) — Звідки ти? (Standard §4.3.1)
  - чому (why) — Чому ти тут? Чому ні?
  - як (how) — Як справи? Як це?
  - скільки (how much) — Скільки це коштує?
  - завжди (always) — я завжди тут
  - ніколи (never) — я ніколи не... (Requires double negation)
activity_hints:
- type: fill-in
  focus: Form questions with чи
  items: 15
- type: fill-in
  focus: Complete with question words
  items: 20
- type: fill-in
  focus: Make sentences negative
  items: 15
- type: fill-in
  focus: Question-answer pairs
  items: 8
connects_to:
- a1-16 (The Living Verb II)
- a1-41 (At The Cafe)
prerequisites:
- a1-15 (The Living Verb I)
persona:
  voice: Patient Supportive Tutor
  role: Investigative Journalist
grammar:
- Yes/no questions with чи
- Question words
- Negation with не
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