**Curriculum context:** This is Module 5 of the A1 track (Ukrainian for English speakers). Title: "Syllables and Word Division" — Breaking Words into Pieces. Phase: A1.1 [First Contact]. Previous module: Completing The Alphabet. Next module: Stress And Intonation.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/syllables-and-word-division-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/syllables-and-word-division.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Syllable structure Open and closed syllables", grade=1-2)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 4
**Previous module:** Completing the Alphabet

**Cumulative vocabulary (73 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, ніс, сон
сік, стіл, кіно, тут, там, так, ні, привіт, дякую, це
яблуко, риба, село, Україна, їжак, юнак, край, день, син, мій
вухо, їжа, яйце, юшка, каша, небо, сир, хліб, зуб, дім
вовк, жук, шапка, гора, рука, бабуся, павук, ґанок, кінь, людина
суп, вода, дим, люк, сіль, Львів, м'ясо, п'ять, сім'я, цукор
час, що, джерело, дзвін, осінь, м'яч, щастя, факт, бджола, дзеркало
черепаха, цибуля, чай

**Grammar already taught (20 topics):**
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

**Coming next (module after this):** Word stress, Stress mobility, Intonation patterns
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- молоко (milk) — 3 open syllables мо-ло-ко; Top 500 word; collocations: пити молоко, склянка молока
- Україна (Ukraine) — 4 syllables у-кра-ї-на; Top 100 word; collocations: жити в Україні, рідна Україна
- сестра (sister) — consonant cluster split се-стра; Top 500 word; collocations: моя сестра, старша сестра
- дерево (tree) — 3 syllables де-ре-во; collocations: старе дерево, зелене дерево
- вулиця (street) — 3 syllables ву-ли-ця; Top 500 word; collocations: на вулиці, головна вулиця
- автобус (bus) — 3 syllables ав-то-бус (closed final syllable); collocations: їхати автобусом

**Recommended** (use in your content to reach the vocabulary target):
- бібліотека (library) — 5 syllables бі-блі-о-те-ка; collocations: у бібліотеці
- університет (university) — 5 syllables у-ні-вер-си-тет; collocations: навчатися в університеті
- склад (syllable) — metalinguistic term; essential for understanding lesson content
- перенос (word division/hyphenation) — metalinguistic term for the writing rule
- голосний (vowel) — metalinguistic term; every голосний creates a syllable
- приголосний (consonant) — metalinguistic term; consonant clusters follow specific split rules

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
- **Grade 2, Сторінка 15**
  15
Крок 1. Уважно розглянь, як перенесли слова. На скільки частин 
їх поділили? Як, на твою думку, ділили слова для переносу?
вере-сень	
бе-реза	
	
яго-да
Крок 2. Чому ці слова не поділені для перенос...

- **Grade 2, Сторінка 18**
  ПОДІЛ СЛІВ НА СКЛАДИ
НАВЧАЮСЯ ДІЛИТИ СЛОВА НА СКЛАДИ
Склади і запиши слова, які «заховалися» 
в пазлах.
визначаю
2| Додайте до частин слів склади так, щоб утворилися 
слова. Запишіть їх, поділяючи на ...

- **Grade 5, Сторінка 170**
  170
Фонетика. Графіка. Орфоепія. Орфографія. Склад . Правила перенесення слів
Склад. 
Правила перенесення слів із  рядка  в  рядок
Вправа 282
1. Розгляньте сторінки зошита на  фото .
2. Висловте свої ...

- **Grade 5, Сторінка 87**
  87
217   Поділіть слова на склади, запишіть фонетичною транскрипцією. 
Цінності, Україна, пісня, тризуб, незалежність, спадщина, 
історія, культура. 
218   Ознайомтеся з таблицею. До кожного правила д...

- **Grade 5, Сторінка 85**
  85
 § 36–37.  Склад.  Основні  правила  переносу
Зауважте!
При збігу однакових приголосних на межі значущих частин слова одну 
букву залишаємо, а другу переносимо в наступний рядок: без-зубий (не бе-
...






---

## 4. Outline

Write **Syllables and Word Division** for the a1 track.

**Targets:** 1200–1800 words | 2+ callout boxes | **0–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Що таке склад? — What Is a Syllable?` (~300 words)
  - Vowel as the syllable core — every vowel creates one syllable, so counting syllables means counting vowels.
  - Counting syllables by vowels: мо-ло-ко (3 vowels = 3 syllables), кіт (1 vowel = 1 syllable), у-кра-ї-на (4 vowels = 4 syllables).
  - Contrast with English syllable intuition: Ukrainian syllable boundaries follow different rules.
- `## Типи складів — Syllable Types` (~300 words)
  - Open syllables end in a vowel (ма-, но-, мо-ло-ко) — the default and most common type in Ukrainian.
  - Closed syllables end in a consonant (кіт, там) — occur at word boundaries and when a sonorant (й, в, р, л, м, н) precedes another consonant (e.g., чай-ка).
  - Consonant clusters: phonetic syllables follow maximal onset (се-стра, о-стрів). Orthographic hyphenation (переніс) is more flexible per Pravopys 2019 (се-стра, сес-тра, сест-ра), but learners focus on phonetic boundaries first.
  - Practice identifying open and closed syllables in high-frequency words: ву-ли-ця, ав-то-бус, де-ре-во.
- `## Правила переносу — Word Division Rules` (~400 words)
  - Word division (переніс) rules for writing: why correct division matters in Ukrainian handwriting and printing.
  - Cannot split: a single letter from the rest of the word (*У-країна), the digraphs дж/дз when they represent one sound (ґу-дзик, not *ґуд-зик).
  - Cannot separate: Ь from the preceding consonant (паль-ці, not *пал-ьці), the apostrophe group from the consonant before it (сім'я → сі-м'я, not *сім-'я).
  - Can split: between two consonants (сіль-ський — ль is inseparable), between a vowel and a consonant (мо-ло-ко).
  - Common learner errors: applying English hyphenation habits to Ukrainian words; drill with problem words like бібліотека, університет.
- `## Практика — Practice` (~200 words)
  - Syllable counting drills: given a word, count the vowels and identify each syllable boundary.
  - Word division exercises: mark correct division points in multi-syllable words (бі-блі-о-те-ка, у-ні-вер-си-тет).
  - Reading multi-syllable words aloud: building fluency by reading words syllable-by-syllable, then at full speed.
- `## Підсумок — Summary` (~100 words)
  - Recap: every vowel = one syllable, open vs closed syllables, consonant cluster split rules, word division for writing.
  - Self-check: How many syllables in Україна? What is an open syllable? Where do you split a consonant cluster?
  - Next: M6 — stress and intonation.

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Що таке склад? — What Is a Syllable? | 300+ |
| Типи складів — Syllable Types | 300+ |
| Правила переносу — Word Division Rules | 400+ |
| Практика — Practice | 200+ |
| Підсумок — Summary | 100+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Syllable structure Open and closed syllables", grade=1-2)` — find how textbooks teach this
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
**Required types:** quiz, fill-in, group-sort, match-up

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
