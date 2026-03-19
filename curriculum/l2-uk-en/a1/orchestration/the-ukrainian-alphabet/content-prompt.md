**Curriculum context:** This is Module 1 of the A1 track (Ukrainian for English speakers). Title: "The Ukrainian Alphabet" — 33 Letters, One System — Your Map to Reading Ukrainian. Phase: A1.1 [First Contact]. Next module: Vowel Sounds.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/the-ukrainian-alphabet-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-ukrainian-alphabet.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Full alphabet overview (33 letters) Sound-letter correspondence (букви vs звуки)", grade=1-2)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

(This is the first module — no prior learner knowledge.)

**Coming next (module after this):** Base vowel pronunciation (А О У Е И І), Iotated vowels dual function (Я Ю Є Ї), И vs І distinction
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- мама (mom) — decodable (М+А+М+А); universal first word; Bolshakova p.14
- тато (dad) — decodable (Т+А+Т+О); high-frequency family word
- кіт (cat) — decodable (К+І+Т); high-frequency; Bolshakova
- молоко (milk) — decodable (М+О+Л+О+К+О); Bolshakova p.14
- масло (butter) — decodable (М+А+С+Л+О); Bolshakova p.15
- ліс (forest) — decodable (Л+І+С); high-frequency
- місто (city) — decodable (М+І+С+Т+О); high-frequency
- око (eye) — decodable (О+К+О); Bolshakova p.13
- так (yes) — decodable (Т+А+К); survival word
- ні (no) — decodable (Н+І); survival word

**Recommended** (use in your content to reach the vocabulary target):
- сон (dream/sleep) — decodable (С+О+Н); Bolshakova p.22
- сом (catfish) — decodable (С+О+М); Bolshakova p.22
- ніс (nose) — decodable (Н+І+С); body vocabulary
- мак (poppy) — decodable (М+А+К); Bolshakova
- сік (juice) — decodable (С+І+К); everyday food word
- стіл (table) — decodable (С+Т+І+Л); everyday object
- тут (here) — decodable (Т+У+Т); high-frequency adverb
- там (there) — decodable (Т+А+М); high-frequency adverb
- сало (lard) — decodable (С+А+Л+О); everyday food word
- кіно (cinema) — decodable (К+І+Н+О); everyday word

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



### Pronunciation Videos (from plan — MANDATORY embeds)
*Credit: Anna Ohoiko — Ukrainian Lessons*

- **Overview**: [Anna Ohoiko — Ukrainian Lessons — Overview](https://www.youtube.com/watch?v=ksXIXj7CXwc)
- **Full Playlist**: [Anna Ohoiko — Ukrainian Lessons — Playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)

**Each letter below MUST get its video embedded in the corresponding H3 section:**

- **Літера А**: [Anna Ohoiko — Ukrainian Lessons — А](https://www.youtube.com/watch?v=hvB3VpcR3ZE)
- **Літера О**: [Anna Ohoiko — Ukrainian Lessons — О](https://www.youtube.com/watch?v=gJFxRIPRZbI)
- **Літера У**: [Anna Ohoiko — Ukrainian Lessons — У](https://www.youtube.com/watch?v=VB1O6PmtYRU)
- **Літера І**: [Anna Ohoiko — Ukrainian Lessons — І](https://www.youtube.com/watch?v=Z9TH0H4ShGo)
- **Літера М**: [Anna Ohoiko — Ukrainian Lessons — М](https://www.youtube.com/watch?v=Ez95H4ibuJo)
- **Літера Н**: [Anna Ohoiko — Ukrainian Lessons — Н](https://www.youtube.com/watch?v=vNUfiKHPYaU)
- **Літера Т**: [Anna Ohoiko — Ukrainian Lessons — Т](https://www.youtube.com/watch?v=m-jcLR_gK0k)
- **Літера К**: [Anna Ohoiko — Ukrainian Lessons — К](https://www.youtube.com/watch?v=J7sGEI4-xJo)
- **Літера С**: [Anna Ohoiko — Ukrainian Lessons — С](https://www.youtube.com/watch?v=7UsFBgSL91E)
- **Літера Л**: [Anna Ohoiko — Ukrainian Lessons — Л](https://www.youtube.com/watch?v=v6-3Xg52Buk)



---

## 4. Outline

Write **The Ukrainian Alphabet** for the a1 track. Target: 1200–1800 words.

### CRITICAL: EXACT H2 HEADERS (copy-paste, do not alter)

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ — Introduction` (~150 words)
  - Ukrainian uses Cyrillic script — descended from Greek via the First Bulgarian Empire. 33 letters, highly phonetic: each letter usually maps to one sound (unlike English where 'ough' can sound 5 different ways).
  - Show the full 33-letter alphabet chart (COPY EXACTLY): А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я Learners don't memorize it all now — master each group in M2-M4.
  - Cultural hook: Cyrillic was created by students of Saints Cyril and Methodius. It is NOT derived from Latin — it descends from the Greek alphabet.
- `## Букви і звуки — Letters and Sounds` (~200 words)
  - Letters (букви) are written symbols. Sounds (звуки) are what you hear and pronounce. They are not the same thing — Ukrainian has 38 phonemes but 33 letters.
  - Key insight: Ukrainian spelling is highly phonetic — one letter almost always represents one sound. This makes Ukrainian FAR easier to read than English. Once you learn the 33 letters, you can sound out any word.
  - Some letters do double duty: iotated vowels (Я Ю Є Ї) can represent two sounds. The soft sign (Ь) modifies the consonant before it. Details in M2 and M4.
- `## Голосні та приголосні — Vowels and Consonants` (~200 words)
  - 10 vowel letters: 6 base (А О У Е И І) + 4 iotated (Я Ю Є Ї). Vowels = voice only, no obstruction. Every Ukrainian syllable has exactly one vowel.
  - 22 consonant letters + the soft sign Ь (modifier, no sound of its own). Consonants = air is obstructed (lips, tongue, teeth).
  - Preview chart organized by category (COPY EXACTLY): Голосні (Base): А, О, У, Е, И, І Голосні (Iotated): Я, Ю, Є, Ї Приголосні: Б, В, Г, Ґ, Д, Ж, З, Й, К, Л, М, Н, П, Р, С, Т, Ф, Х, Ц, Ч, Ш, Щ Modifier: Ь M2 will master vowels, M3 consonants, M4 special signs.
- `## Перші 10 літер — First 10 Letters` (~350 words)
  - Today's practice set: А О У І (4 vowels) + М Н Т К С Л (6 consonants). These 10 high-frequency letters let you read real Ukrainian words immediately.
  - Letter-by-letter introduction with pronunciation guidance: А — open 'a' as in 'father'. М — like English M. О — rounded 'o' as in 'more'. Н — like English N (looks like H but is NOT H!). У — 'oo' as in 'moon'. Т — like English T. І — 'ee' as in 'see'. К — like English K. С — like English S. Л — like English L (tongue position differs slightly).
  - Decodable words (use ONLY these 10 letters): мама (mom), тато (dad), кіт (cat), молоко (milk), масло (butter), око (eye), ніс (nose), місто (city), ліс (forest), сон (dream), мак (poppy), сік (juice), сало (lard), стіл (table), тут (here), там (there).
  - Detailed phonetic walkthroughs: how to blend М+А→МА, then МА+МА→МАМА. How to read К+І+Т→КІТ. Build from letters → syllables → words.
- `## Перші слова — First Words in Context` (~200 words)
  - Micro-dialogues using decodable words + sight words: — Це кіт? — Так, це кіт. / — Це місто? — Ні, це ліс.
  - Sight words (contain untaught letters — recognize as wholes): привіт (hello), дякую (thank you), це (this is). так (yes) and ні (no) are fully decodable with the 10 practice letters.
  - Reading practice: short sentences mixing decodable words and sight words. Мама тут. Кіт там. Це молоко. Це масло.
- `## Підсумок — Summary` (~100 words)
  - 33 letters: 10 vowels, 22 consonants, 1 modifier (Ь). Highly phonetic system.
  - You mastered 10 letters today. You can read: мама, тато, кіт, молоко, місто, ліс.
  - Self-check: Can you find all 10 vowel letters on the chart? Can you read мама and кіт? What is the difference between букви and звуки?
  - Next: M2 deep-dives into the vowel system — all 10 vowel letters.

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ — Introduction | 150+ |
| Букви і звуки — Letters and Sounds | 200+ |
| Голосні та приголосні — Vowels and Consonants | 200+ |
| Перші 10 літер — First 10 Letters | 350+ |
| Перші слова — First Words in Context | 200+ |
| Підсумок — Summary | 100+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Rules (read ALL before writing)

### RULE 1: GRAMMAR — see Section 6

Section 6 (Hard Constraints) defines exactly what grammar structures you may use for this module. Follow those constraints — they vary by module number.

### RULE 2: VOCABULARY

Prioritize these Ukrainian words (from the plan). You may also use words from the cumulative vocabulary and common Ukrainian words, but these are your core teaching targets:

**Allowed Ukrainian words:** мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні, сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно, привіт, дякую, це

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
**Required types:** watch-and-repeat, image-to-letter, classify, match-up, fill-in

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

GRAMMAR CONSTRAINTS (A1.1 — Phonetics, M01-M06):
NO CONJUGATED VERBS. NO IMPERATIVES. This is the phonetics phase.

ALLOWED structures (Ukrainian examples only):
- Це + noun: «Це кіт», «Це мама»
- Noun + тут/там: «Мама тут», «Кіт там»
- Question words: «Хто це?», «Що це?», «Де мама?»
- Так/Ні: «Так, це кіт», «Ні, це не кіт»
- Fixed phrases (memorized, no grammar): дякую, будь ласка, привіт

BANNED: ALL verbs, past/future tense, cases, compound sentences

STRESS MARKS: Do NOT add stress marks (´). Write plain Ukrainian.
The pipeline adds stress marks deterministically after you write.

METALANGUAGE: English prose, Ukrainian examples. Bilingual headings.

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
