**Curriculum context:** This is Module 6 of the A1 track (Ukrainian for English speakers). Title: "Stress and Intonation" — The Music of Ukrainian. Phase: A1.1 [First Contact]. Previous module: Syllables And Word Division. Next module: The Gender Code.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/stress-and-intonation-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/stress-and-intonation.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Word stress Stress mobility", grade=1-2)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 5
**Previous module:** Syllables and Word Division

**Cumulative vocabulary (84 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, ніс, сон
сік, стіл, кіно, тут, там, так, ні, привіт, дякую, це
яблуко, риба, село, Україна, їжак, юнак, край, день, син, мій
вухо, їжа, яйце, юшка, каша, небо, сир, хліб, зуб, дім
вовк, жук, шапка, гора, рука, бабуся, павук, ґанок, кінь, людина
суп, вода, дим, люк, сіль, Львів, м'ясо, п'ять, сім'я, цукор
час, що, джерело, дзвін, осінь, м'яч, щастя, факт, бджола, дзеркало
черепаха, цибуля, чай, склад, голосний, приголосний, перенос, сестра, дерево, вулиця
автобус, бібліотека, університет, ґудзик

**Grammar already taught (23 topics):**
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

**Coming next (module after this):** Three-gender system, Declension families overview, Gender prediction rules
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- замок (castle/lock) — stress minimal pair: зАмок (castle) vs замОк (lock)
- вода (water) — last-syllable stress водА; Top 300 word; collocations: пити воду, холодна вода
- рука (hand/arm) — mobile stress рукА → рУки; Top 200 word
- писати (to write) — mobile stress in conjugation писАти → пишУ → пИшеш; Top 200 word
- школа (school) — penultimate stress шкОла; Top 200 word
- молоко (milk) — last-syllable stress молокО
- добрий (good) — first-syllable stress дОбрий; Top 100 word; collocations: добрий день

**Recommended** (use in your content to reach the vocabulary target):
- далеко (far) — penultimate stress дале́ко
- наголос (stress/accent) — metalinguistic term
- інтонація (intonation) — metalinguistic term
- питання (question) — high-frequency word
- відповідь (answer) — high-frequency word

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 5-15% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: Mostly English with Ukrainian words bolded inline.
- UKRAINIAN CONTENT: Words and short phrases inline: "The letter **Н** looks like H but sounds like N."
- DIALOGUES & READING PRACTICE: Short Ukrainian sentences in blockquotes are encouraged.
- TABLES: Simple letter-sound or word-meaning tables.
Ukrainian sentences max 10 words.

### Textbook References
- **Grade 4, Сторінка 171**
  Зразок
Приїжджала (коли?) влітку.
ОС*Я/ К'/ Ь<ЬС’£$Ю /
Спілкуючись, завжди пам’ятайте про інтонацію. Так, 
слово дякую можна вимовити м ’яко або грубо, тепло 
чи холодно, сором’язливо або нахабно. Якщ...

- **Grade 1, Сторінка 24**
  24
ЗВУКИ. ГОЛОСНІ І ПРИГОЛОСНІ
Ти вимовляєш різні звуки: голосні і приголосні. 
Голосні звуки утворюються за допомогою голосу.
Голосні почуєш в пісні,
І у темному у лісі, 
І коли дивуєшся,
І коли милу...

- **Grade 5, Сторінка 246**
  246
557   Прочитайте епіграф до уроку. Чому інтонації приділяють таку 
увагу?
558   Прочитайте тексти. Що їх об’єднує? Про які невербальні засоби 
спілкування ідеться? Чи погоджуєтеся ви з автором? Як...

- **Grade 2, Сторінка 16**
  ЕКСПЕРИМЕНТУЮ З НАГОЛОСОМ
б| Змініть слова за зразком і запишіть. 
Запам'ятайте, як наголошуються ці 
слова.
ручка 
нитка 
ложка
шапка
картка
стежка
-------------------------------------------------
п...

- **Grade 1, Сторінка 15**
  13
	 Вимов голосні звуки в словах — назвах предме-
тів.   
	 Вимов приголосні звуки в словах — назвах 
предметів.
	 Який у тебе сьогодні настрій? Вибери.
Мовні звуки: голосні та приголосні
[•]
[•]
 [ ...






---

## 4. Outline

Write **Stress and Intonation** for the a1 track.

**Targets:** 1200–1800 words | 2+ callout boxes | **0–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Наголос — Stress` (~350 words)
  - Free and mobile stress concept: unlike Polish (penultimate) or French (final), Ukrainian stress can fall on any syllable of a content word (note: clitics like short prepositions/conjunctions typically lack stress) — there is no fixed rule.
  - Stress changes meaning: зАмок (castle) vs замОк (lock), мУка (torment) vs мукА (flour) — minimal pairs that demonstrate the functional load of stress.
  - How stress is marked in dictionaries and textbooks: the acute accent (´) over the stressed vowel; practice reading dictionary entries.
  - Learner strategy: when encountering a new word, always check stress placement — guessing from spelling will often be wrong.
- `## Типові наголоси — Common Stress Patterns` (~250 words)
  - First-syllable stress: мАма, тАто, хАта, кАва — common in basic family and household words.
  - Last-syllable stress: молокО, далекО, Україна — common in longer words.
  - Penultimate stress: шкОла, кнИжка, дорОга — frequent in two- and three-syllable words.
  - No fixed rule: the same ending can have different stress (кнИжка vs водА, both -а ending) — stress must be learned per word.
- `## Рухомий наголос — Mobile Stress` (~250 words)
  - Stress shifts in declension: рукА (nominative singular) → рУки (nominative/accusative plural) — the stress moves when the word form changes. (Note: genitive singular is рукИ — stress stays).
  - Stress shifts in number: водА (singular) → вОди (plural) — noun stress can shift between singular and plural forms. (Preview — details in later modules.)
  - Preview note: mobile stress will matter more when learning cases and verb conjugation — for now, awareness is the goal.
  - Practical tip: listening to native speakers is the best way to internalize stress patterns.
- `## Інтонація — Intonation` (~250 words)
  - Declarative intonation: pitch falls at the end of the sentence — Це кафе. with a downward contour.
  - Interrogative with question word: pitch rises on the question word, then falls — ДЕ кафе?
  - Yes/no questions (without question word): pitch rises sharply on the stressed syllable of the key word, then falls — Це МАма? (rise on МА, fall on ма). Not a simple terminal rise like English.
  - Exclamatory intonation: sharp rise with emphasis — Це кафе! expressing surprise or excitement.
  - Contrast drill: practicing the same sentence with all four intonation patterns.
- `## Практика — Practice` (~100 words)
  - Stress placement drills: identify which syllable carries the stress in common words.
  - Minimal pairs practice: distinguish words that differ only in stress (зАмок/замОк, мУка/мукА).
  - Intonation reading exercises: read the same sentence as a statement, question, and exclamation.
- `## Підсумок — Summary` (~100 words)
  - Recap: stress is free and mobile, vowel purity under stress, rising intonation for questions, stress minimal pairs.
  - Self-check: Where is the stress in вода? What happens to vowel quality when unstressed? How does question intonation differ from statement?
  - Next: M7 — greetings and basic phrases.

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Наголос — Stress | 350+ |
| Типові наголоси — Common Stress Patterns | 250+ |
| Рухомий наголос — Mobile Stress | 250+ |
| Інтонація — Intonation | 250+ |
| Практика — Practice | 100+ |
| Підсумок — Summary | 100+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Word stress Stress mobility", grade=1-2)` — find how textbooks teach this
2. **Write content** — focus on being a warm, patient tutor. Make it engaging. Vary your transitions.
3. **Create activities** from your content
4. **Use vocabulary from the plan** — stick to words from `vocabulary_hints`

### Your Priority: Teaching Quality

You are a warm, patient Ukrainian tutor writing for beginners. Your #1 job is making the learner feel capable and excited. Write like a human teacher, not a textbook.

**Anti-robotics (scored — LLM Fingerprint dimension):**
- NEVER use "Here is / Here are" more than once in a module
- NEVER start 3+ sections with the same phrase pattern
- Use direct, conversational transitions: "Now try this", "Ready?", "Let's practice", "Good — next..."
- Weave Ukrainian examples into flowing prose, not bullet-point dumps
- Read your text back — if it sounds like a Wikipedia article, rewrite it

**Trust the pipeline**: After you write, the validate phase automatically checks every Ukrainian word against VESUM, verifies stress marks, and scans for Russianisms. You do NOT need to verify words yourself — focus on writing naturally and engagingly. The pipeline catches errors; your job is making the lesson feel alive.

**Tools if needed**: `search_text` for textbook pedagogy, `verify_words` if genuinely unsure about a specific word. But don't let verification interrupt your creative flow.

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

- Activity **answers** must use words from your content. **Distractors** must be VESUM-verified Ukrainian words — call `verify_words` before including any distractor. Never use made-up or unverified words.
- Follow schemas exactly — `additionalProperties: false` means any unlisted field = FAIL.
- Read `schemas/activities-a1.schema.json` for full field definitions.

**Allowed types:** quiz, true-false, fill-in, match-up, anagram, unjumble, group-sort, watch-and-repeat, classify, image-to-letter
**Forbidden types:** cloze, error-correction, mark-the-words, select, translate, essay-response, critical-analysis, comparative-study, authorial-intent
**Required types:** quiz, match-up, true-false, fill-in

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
