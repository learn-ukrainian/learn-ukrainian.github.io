You are about to build a module using the prompt below. Before you start, verify the prompt is ready.

**Default answer: PASS.** Only report genuine issues that would cause audit gate failures or introduce errors.

## The Prompt

<prompt>
**Curriculum context:** This is Module 3 of the A1 track (Ukrainian for English speakers). Title: "Consonant Sounds" — Приголосні звуки — Voiced, Voiceless, Hard, and Soft. Phase: A1.1 [First Contact]. Previous module: Vowel Sounds. Next module: Completing The Alphabet.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/consonant-sounds-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/consonant-sounds.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Sonorant consonants (Л М Н Р В) Voiced/voiceless consonant pairs", grade=1-2)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 2
**Previous module:** Vowel Sounds

**Cumulative vocabulary (39 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, суп

**Grammar already taught (9 topics):**
- Full alphabet overview (33 letters)
- Sound-letter correspondence (букви vs звуки)
- Vowel vs consonant classification
- Basic syllable blending and word reading
- Base vowel pronunciation (А О У Е И І)
- Iotated vowels dual function (Я Ю Є Ї)
- И vs І distinction
- Word stress basics (наголос)
- Vowel purity rule (no reduction)

**Coming next (module after this):** Soft sign palatalization (Ь), Apostrophe function and rules, Affricates (Ц, Ч, Щ)
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- хліб (bread) — cultural staple; demonstrates Х; no-devoicing rule
- зуб (tooth) — demonstrates З; no-devoicing drill with суп
- дім (house) — high-frequency; demonstrates Д
- вовк (wolf) — tale vocabulary; demonstrates В (sonorant)
- жук (beetle) — demonstrates Ж; Bolshakova
- шапка (hat) — demonstrates Ш; everyday clothing
- гора (mountain) — demonstrates Г (throaty fricative); high-frequency
- небо (sky) — demonstrates Н; high-frequency
- рука (hand) — demonstrates Р (rolled); body vocabulary
- бабуся (grandma) — demonstrates Б; high-frequency family word

**Recommended** (use in your content to reach the vocabulary target):
- павук (spider) — demonstrates П; Bolshakova
- ґанок (porch) — demonstrates rare Ґ; classic textbook word
- сіль (salt) — demonstrates soft С and Л; everyday kitchen word
- люди (people) — demonstrates soft Л; high-frequency
- суп (soup) — voiceless pair drill with зуб; everyday food
- вода (water) — demonstrates В; high-frequency
- цибуля (onion) — hard Л; minimal pair with люк
- люк (hatch) — soft Л; minimal pair with лук

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

### Blog Articles & Guides
- **Ukrainian Cyrillic Alphabet — Letters and Sounds** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ukrainian-cyrillic-alphabet/
  Relevance: 0.4
  Topics: alphabet, cyrillic, letters, sounds


### Textbook References
- **Grade 2, Сторінка 40**
  40
ДЗВІНКІ ТА ГЛУХІ ПРИГОЛОСНІ ЗВУКИ
147. Виконай завдання на вибір.
	 Доповни речення.
У школі ми вивчаємо такі предмети: математику, …
	 Запиши кілька назв предметів, які є в класній кімнаті.
146.	 ...

- **Grade 2, Сторінка 62**
  62
ДЗвІнкІ та ГЛУХІ ПриГоЛоснІ ЗвУки
Вимов звуки, які позначають виділені букви. Які з них ти ви-
мовляєш за допомогою голосу і шуму, а які — тільки шуму? 
жабка — шапка
злива — слива
ґава — кава
дуб ...

- **Grade 2, Сторінка 3**
  ЗВУКИ І БУКВИ
к
і
<
ЗВУКИ
СКЛАД^
У розділі ти будеш вивчати:
БУКВИ
НАГОЛОС
Дізнаєшся про:
к
1
г
л
І
1
наголошені
ГОЛОСНІ ЗВУКИ
____________________
ненаголошені
дзвінкі, глухі
г
тверді, м'які
^ПРИГОЛО...

- **Grade 1, Сторінка 17**
  15
Приголосні тверді та м’які
	 Вимов звуки, які ти чуєш на початку слів — 
назв намальованих предметів.
	 Порівняй вимову перших звуків у словах — на-
звах предметів. У яких словах перші звуки ви-
мо...

- **Grade 4, Сторінка 5**
  * 
6. Розглянь таблиці. Пригадай, за допомогою чого утворю­
ються дзвінкі приголосні. Що ми чуємо, коли їх вимовля­
ємо?
Приголосні звуки, які мають пару
Дзвінкі
[б]
м
[ЦІ
[3]
[3']
[ж]
[дж]
[дз]
[ДЗ'1...


### Pronunciation Videos (from plan — MANDATORY embeds)
*Credit: Anna Ohoiko — Ukrainian Lessons*

- **Full Playlist**: [Anna Ohoiko — Ukrainian Lessons — Playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)

**Each letter below MUST get its video embedded in the corresponding H3 section:**

- **Літера М**: [Anna Ohoiko — Ukrainian Lessons — М](https://www.youtube.com/watch?v=Ez95H4ibuJo)
- **Літера Н**: [Anna Ohoiko — Ukrainian Lessons — Н](https://www.youtube.com/watch?v=vNUfiKHPYaU)
- **Літера Л**: [Anna Ohoiko — Ukrainian Lessons — Л](https://www.youtube.com/watch?v=v6-3Xg52Buk)
- **Літера Р**: [Anna Ohoiko — Ukrainian Lessons — Р](https://www.youtube.com/watch?v=fMGsQ5KPQgg)
- **Літера Й**: [Anna Ohoiko — Ukrainian Lessons — Й](https://www.youtube.com/watch?v=aq0cjB90s3w)
- **Літера В**: [Anna Ohoiko — Ukrainian Lessons — В](https://www.youtube.com/watch?v=aFcvYfvQ2X4)
- **Літера Б**: [Anna Ohoiko — Ukrainian Lessons — Б](https://www.youtube.com/watch?v=V1hxBE_JbGg)
- **Літера П**: [Anna Ohoiko — Ukrainian Lessons — П](https://www.youtube.com/watch?v=JksSjjxyW5Y)
- **Літера Д**: [Anna Ohoiko — Ukrainian Lessons — Д](https://www.youtube.com/watch?v=g4Bh-lqzd48)
- **Літера Т**: [Anna Ohoiko — Ukrainian Lessons — Т](https://www.youtube.com/watch?v=m-jcLR_gK0k)
- **Літера Г**: [Anna Ohoiko — Ukrainian Lessons — Г](https://www.youtube.com/watch?v=gVnclpSI0DU)
- **Літера К**: [Anna Ohoiko — Ukrainian Lessons — К](https://www.youtube.com/watch?v=J7sGEI4-xJo)
- **Літера Ж**: [Anna Ohoiko — Ukrainian Lessons — Ж](https://www.youtube.com/watch?v=dIrGVcqPwqM)
- **Літера Ш**: [Anna Ohoiko — Ukrainian Lessons — Ш](https://www.youtube.com/watch?v=1D-6MIw3OXY)
- **Літера З**: [Anna Ohoiko — Ukrainian Lessons — З](https://www.youtube.com/watch?v=BhASNxitC1A)
- **Літера С**: [Anna Ohoiko — Ukrainian Lessons — С](https://www.youtube.com/watch?v=7UsFBgSL91E)
- **Літера Х**: [Anna Ohoiko — Ukrainian Lessons — Х](https://www.youtube.com/watch?v=vpr58zJSJKc)



---

## 4. Outline

Write **Consonant Sounds** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ — Introduction` (~100 words)
  - Review: M1 gave you the alphabet, M2 mastered vowels. Today: the 22 consonant letters — how they're organized by sound production.
  - All 10 vowels from M2 are available. Focus is on consonant pronunciation and classification.
- `## Сонорні — Sonorant Consonants` (~200 words)
  - Sonorants are the 'musical' consonants — voice dominates over noise. 5 sonorants: Л М Н Р В. You already know Л М Н from M1.
  - Р — the rolled/trilled R! Words: риба (fish), рука (hand). Practice the tongue-tip trill. Looks like English P but sounds completely different.
  - В — a sonorant in Ukrainian — closer to English W than English V. Lips rounded, NOT teeth on lip. Words: вода (water), вовк (wolf).
- `## Дзвінкі та глухі пари — Voiced and Voiceless Pairs` (~400 words)
  - Hand-on-throat test: voiced (дзвінкий) = throat vibrates. Voiceless (глухий) = only air. Each pair is identical mouth position, different voicing.
  - Б/П — бабуся (grandma) / павук (spider). Б = voiced, П = voiceless.
  - Д/Т — дім (house) / тато (M1 review). Д = voiced, Т = voiceless.
  - З/С — зуб (tooth) / суп (soup). З = voiced, С = voiceless.
  - Ж/Ш — жук (beetle) / шапка (hat). Ж = voiced sibilant (like 'zh' in 'measure'), Ш = voiceless (like English 'sh').
  - Г/Х — гора (mountain) / хліб (bread). Г is a soft throaty sound (voiced glottal fricative), NOT a hard 'g' like English 'go'. Х like German 'ch' in 'ach'.
  - Ґ/К — ґанок (porch) / кіт (M1 review). Ґ IS the hard 'g' (like English 'go') — very rare (~400 native words). Removed from alphabet in 1933, restored 1990.
  - CRITICAL RULE: voiced consonants stay voiced at word end! зуб = зу[б], NOT зу[п]. хліб = хлі[б], NOT хлі[п]. Different from Russian and German.
- `## Тверді та м'які — Hard and Soft Consonants` (~250 words)
  - Most Ukrainian consonants come in hard/soft variants. A consonant becomes soft (palatalized) before І, Я, Ю, Є or when followed by Ь (covered in M4).
  - Examples: ліс (soft Л), день (soft Д and Н), сіль (soft С and Л).
  - Compare: лук (hard Л — bow (weapon)) vs люк (soft Л — hatch). The consonant changes, not the vowel!
  - Always-hard: Ж, Ш are always hard. Й is always soft. Details on Ь (the soft sign that forces softening) in M4.
- `## Читання — Reading Practice` (~150 words)
  - Words using the full consonant inventory. All vowels from M2 available.
  - NO full sentences with verbs — grammar is not taught yet. Use word groups, noun phrases, and labeling: Це дім. Це хліб. Ось бабуся.
  - Voiced/voiceless pair drills: зуб/суп, жук/шапка, гора/хор.
  - Minimal pair practice: лук/люк (hard/soft), дим/дім (И/І).
- `## Підсумок — Summary` (~100 words)
  - 5 sonorants (Л М Н Р В), 6 voiced/voiceless pairs, hard/soft system.
  - Self-check: What are the 5 sonorants? What is the voiceless partner of Б? Is Г a hard 'g' or a soft throaty sound? Do voiced consonants devoice at word end?
  - Next: M4 completes the alphabet — soft sign (Ь), apostrophe, affricates (Ц Ч Щ), digraphs (ДЖ ДЗ), and rare Ф.

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ — Introduction | 100+ |
| Сонорні — Sonorant Consonants | 200+ |
| Дзвінкі та глухі пари — Voiced and Voiceless Pairs | 400+ |
| Тверді та м'які — Hard and Soft Consonants | 250+ |
| Читання — Reading Practice | 150+ |
| Підсумок — Summary | 100+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Sonorant consonants (Л М Н Р В) Voiced/voiceless consonant pairs", grade=1-2)` — find how textbooks teach this
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
**Required types:** watch-and-repeat, classify, image-to-letter, match-up, quiz

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

## The Plan

<plan>
module: a1-003
level: A1
sequence: 3
slug: consonant-sounds
version: '2.0'
title: Consonant Sounds
subtitle: "Приголосні звуки — Voiced, Voiceless, Hard, and Soft"
focus: grammar
pedagogy: PPP
phase: A1.1 [First Contact]
word_target: 1200
objectives:
- Learner masters sonorant consonants (Л М Н Р В)
- "Learner understands voiced/voiceless pairs (Б/П Д/Т З/С Ж/Ш Г/Х Ґ/К)"
- Learner knows the hard vs soft consonant distinction
- Learner can read words with all consonants
- "Key rule: Ukrainian voiced consonants do NOT devoice at word end (зуб = зу[б], not зу[п])"
content_outline:
- section: Вступ — Introduction
  words: 100
  points:
  - "Review: M1 gave you the alphabet, M2 mastered vowels. Today: the 22 consonant
    letters — how they're organized by sound production."
  - "All 10 vowels from M2 are available. Focus is on consonant pronunciation
    and classification."
- section: "Сонорні — Sonorant Consonants"
  words: 200
  points:
  - "Sonorants are the 'musical' consonants — voice dominates over noise.
    5 sonorants: Л М Н Р В. You already know Л М Н from M1."
  - "Р — the rolled/trilled R! Words: риба (fish), рука (hand). Practice the
    tongue-tip trill. Looks like English P but sounds completely different."
  - "В — a sonorant in Ukrainian — closer to English W than English V. Lips rounded,
    NOT teeth on lip. Words: вода (water), вовк (wolf)."
- section: "Дзвінкі та глухі пари — Voiced and Voiceless Pairs"
  words: 400
  points:
  - "Hand-on-throat test: voiced (дзвінкий) = throat vibrates. Voiceless (глухий)
    = only air. Each pair is identical mouth position, different voicing."
  - "Б/П — бабуся (grandma) / павук (spider). Б = voiced, П = voiceless."
  - "Д/Т — дім (house) / тато (M1 review). Д = voiced, Т = voiceless."
  - "З/С — зуб (tooth) / суп (soup). З = voiced, С = voiceless."
  - "Ж/Ш — жук (beetle) / шапка (hat). Ж = voiced sibilant (like 'zh' in 'measure'),
    Ш = voiceless (like English 'sh')."
  - "Г/Х — гора (mountain) / хліб (bread). Г is a soft throaty sound (voiced glottal
    fricative), NOT a hard 'g' like English 'go'. Х like German 'ch' in 'ach'."
  - "Ґ/К — ґанок (porch) / кіт (M1 review). Ґ IS the hard 'g' (like English 'go') —
    very rare (~400 native words). Removed from alphabet in 1933, restored 1990."
  - "CRITICAL RULE: voiced consonants stay voiced at word end! зуб = зу[б], NOT
    зу[п]. хліб = хлі[б], NOT хлі[п]. Different from Russian and German."
- section: "Тверді та м'які — Hard and Soft Consonants"
  words: 250
  points:
  - "Most Ukrainian consonants come in hard/soft variants. A consonant becomes soft
    (palatalized) before І, Я, Ю, Є or when followed by Ь (covered in M4)."
  - "Examples: ліс (soft Л), день (soft Д and Н), сіль (soft С and Л)."
  - "Compare: лук (hard Л — bow (weapon)) vs люк (soft Л — hatch). The consonant changes,
    not the vowel!"
  - "Always-hard: Ж, Ш are always hard. Й is always soft. Details on Ь (the soft
    sign that forces softening) in M4."
- section: "Читання — Reading Practice"
  words: 150
  points:
  - "Words using the full consonant inventory. All vowels from M2 available."
  - "NO full sentences with verbs — grammar is not taught yet. Use word groups,
    noun phrases, and labeling: Це дім. Це хліб. Ось бабуся."
  - "Voiced/voiceless pair drills: зуб/суп, жук/шапка, гора/хор."
  - "Minimal pair practice: лук/люк (hard/soft), дим/дім (И/І)."
- section: "Підсумок — Summary"
  words: 100
  points:
  - "5 sonorants (Л М Н Р В), 6 voiced/voiceless pairs, hard/soft system."
  - "Self-check: What are the 5 sonorants? What is the voiceless partner of Б?
    Is Г a hard 'g' or a soft throaty sound? Do voiced consonants devoice at word end?"
  - "Next: M4 completes the alphabet — soft sign (Ь), apostrophe, affricates
    (Ц Ч Щ), digraphs (ДЖ ДЗ), and rare Ф."
vocabulary_hints:
  required:
  - "хліб (bread) — cultural staple; demonstrates Х; no-devoicing rule"
  - "зуб (tooth) — demonstrates З; no-devoicing drill with суп"
  - "дім (house) — high-frequency; demonstrates Д"
  - "вовк (wolf) — tale vocabulary; demonstrates В (sonorant)"
  - "жук (beetle) — demonstrates Ж; Bolshakova"
  - "шапка (hat) — demonstrates Ш; everyday clothing"
  - "гора (mountain) — demonstrates Г (throaty fricative); high-frequency"
  - "небо (sky) — demonstrates Н; high-frequency"
  - "рука (hand) — demonstrates Р (rolled); body vocabulary"
  - "бабуся (grandma) — demonstrates Б; high-frequency family word"
  recommended:
  - "павук (spider) — demonstrates П; Bolshakova"
  - "ґанок (porch) — demonstrates rare Ґ; classic textbook word"
  - "сіль (salt) — demonstrates soft С and Л; everyday kitchen word"
  - "люди (people) — demonstrates soft Л; high-frequency"
  - "суп (soup) — voiceless pair drill with зуб; everyday food"
  - "вода (water) — demonstrates В; high-frequency"
  - "цибуля (onion) — hard Л; minimal pair with люк"
  - "люк (hatch) — soft Л; minimal pair with лук"
activity_hints:
- type: watch-and-repeat
  focus: "Consonant pronunciation — hear and repeat each voiced/voiceless pair"
  items: 12
- type: classify
  focus: "Sort consonants into сонорні / дзвінкі / глухі"
  items: 15
- type: image-to-letter
  focus: "Match picture to consonant it starts with — жук→Ж, шапка→Ш, рука→Р"
  items: 8
- type: match-up
  focus: "Match voiced consonant to its voiceless partner (Б↔П, Д↔Т, З↔С, Ж↔Ш, Г↔Х)"
  items: 6
- type: quiz
  focus: "Hand-on-throat test — is this consonant voiced or voiceless?"
  items: 10
- type: classify
  focus: "Hard or soft? Identify consonant quality in context (лук vs люк)"
  items: 8
connects_to:
- a1-04 (Completing the Alphabet)
prerequisites:
- a1-02 (Vowel Sounds)
persona:
  voice: Patient Supportive Tutor
  role: Typography Artist
grammar:
- "Sonorant consonants (Л М Н Р В)"
- "Voiced/voiceless consonant pairs"
- "No final devoicing rule"
- "Hard/soft consonant distinction"
- "Г vs Ґ distinction"
register: розмовний
pronunciation_videos:
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV
  credit: "Anna Ohoiko — Ukrainian Lessons"
  letters:
    М: https://www.youtube.com/watch?v=Ez95H4ibuJo
    Н: https://www.youtube.com/watch?v=vNUfiKHPYaU
    Л: https://www.youtube.com/watch?v=v6-3Xg52Buk
    Р: https://www.youtube.com/watch?v=fMGsQ5KPQgg
    Й: https://www.youtube.com/watch?v=aq0cjB90s3w
    В: https://www.youtube.com/watch?v=aFcvYfvQ2X4
    Б: https://www.youtube.com/watch?v=V1hxBE_JbGg
    П: https://www.youtube.com/watch?v=JksSjjxyW5Y
    Д: https://www.youtube.com/watch?v=g4Bh-lqzd48
    Т: https://www.youtube.com/watch?v=m-jcLR_gK0k
    Г: https://www.youtube.com/watch?v=gVnclpSI0DU
    К: https://www.youtube.com/watch?v=J7sGEI4-xJo
    Ж: https://www.youtube.com/watch?v=dIrGVcqPwqM
    Ш: https://www.youtube.com/watch?v=1D-6MIw3OXY
    З: https://www.youtube.com/watch?v=BhASNxitC1A
    С: https://www.youtube.com/watch?v=7UsFBgSL91E
    Х: https://www.youtube.com/watch?v=vpr58zJSJKc

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