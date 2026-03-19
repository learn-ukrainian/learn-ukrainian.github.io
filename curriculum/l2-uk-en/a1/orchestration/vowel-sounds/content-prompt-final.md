**Curriculum context:** This is Module 2 of the A1 track (Ukrainian for English speakers). Title: "Vowel Sounds" — Голосні звуки — The Heartbeat of Every Ukrainian Word. Phase: A1.1 [First Contact]. Previous module: The Ukrainian Alphabet. Next module: Consonant Sounds.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/vowel-sounds-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/vowel-sounds.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Base vowel pronunciation (А О У Е И І) Iotated vowels dual function (Я Ю Є Ї)", grade=1-2)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 1
**Previous module:** The Ukrainian Alphabet

**Cumulative vocabulary (20 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно

**Grammar already taught (4 topics):**
- Full alphabet overview (33 letters)
- Sound-letter correspondence (букви vs звуки)
- Vowel vs consonant classification
- Basic syllable blending and word reading

**Coming next (module after this):** Sonorant consonants (Л М Н Р В), Voiced/voiceless consonant pairs, No final devoicing rule
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- яблуко (apple) — key word for Я; Bolshakova p.18
- риба (fish) — key word for И; high-frequency; Bolshakova
- село (village) — demonstrates unstressed Е staying pure; high-frequency
- Україна (Ukraine) — key word for Ї; cultural significance
- їжак (hedgehog) — key word for Ї; children's literature staple
- юнак (young man) — key word for Ю; State Standard vocabulary
- край (edge/land) — demonstrates Й at word end; high-frequency
- день (day) — demonstrates Е; top 50 word
- син (son) — demonstrates И; high-frequency family word
- моя (my-f) — demonstrates Я after vowel; possessive sight word

**Recommended** (use in your content to reach the vocabulary target):
- вухо (ear) — demonstrates У; body vocabulary
- їжа (food) — demonstrates Ї; everyday vocabulary
- моє (my-n) — demonstrates Є after vowel; possessive sight word
- яйце (egg) — demonstrates Я at word start; everyday vocabulary
- юшка (soup/broth) — demonstrates Ю; everyday vocabulary
- каша (porridge) — demonstrates А; everyday food word; Bolshakova
- небо (sky) — demonstrates Е; high-frequency
- сир (cheese) — demonstrates И; everyday food word

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

- **Full Playlist**: [Anna Ohoiko — Ukrainian Lessons — Playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)

**Each letter below MUST get its video embedded in the corresponding H3 section:**

- **Літера А**: [Anna Ohoiko — Ukrainian Lessons — А](https://www.youtube.com/watch?v=hvB3VpcR3ZE)
- **Літера О**: [Anna Ohoiko — Ukrainian Lessons — О](https://www.youtube.com/watch?v=gJFxRIPRZbI)
- **Літера У**: [Anna Ohoiko — Ukrainian Lessons — У](https://www.youtube.com/watch?v=VB1O6PmtYRU)
- **Літера Е**: [Anna Ohoiko — Ukrainian Lessons — Е](https://www.youtube.com/watch?v=KFlsroBW0dk)
- **Літера И**: [Anna Ohoiko — Ukrainian Lessons — И](https://www.youtube.com/watch?v=W-1rCu0indE)
- **Літера І**: [Anna Ohoiko — Ukrainian Lessons — І](https://www.youtube.com/watch?v=Z9TH0H4ShGo)
- **Літера Я**: [Anna Ohoiko — Ukrainian Lessons — Я](https://www.youtube.com/watch?v=yhSAf41LX8I)
- **Літера Ю**: [Anna Ohoiko — Ukrainian Lessons — Ю](https://www.youtube.com/watch?v=9JdIBYCTWGw)
- **Літера Є**: [Anna Ohoiko — Ukrainian Lessons — Є](https://www.youtube.com/watch?v=O0bwRyyBQSc)
- **Літера Ї**: [Anna Ohoiko — Ukrainian Lessons — Ї](https://www.youtube.com/watch?v=UcjdjQXhAY8)



---

## 4. Outline

Write **Vowel Sounds** for the a1 track. Target: 1200–1800 words.

### CRITICAL: EXACT H2 HEADERS (copy-paste, do not alter)

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ — Introduction` (~100 words)
  - Review: M1 gave you the alphabet map and 10 practice letters. Today: the vowel system — 10 letters that carry every Ukrainian syllable.
  - Why vowels matter: every syllable has exactly one vowel. Count the vowels and you know how many syllables a word has.
- `## Шість основних голосних — Six Base Vowels` (~300 words)
  - А — open, like 'a' in 'father'. Never reduces. Words: мама (M1 review), каша (porridge), сало (lard).
  - О — rounded, like 'o' in 'more'. Stays О even when unstressed (unlike Russian!). Words: око (M1 review), молоко (M1 review), село (village).
  - У — like 'oo' in 'moon'. Words: тут (M1 review), вухо (ear), суп (soup).
  - Е — like 'e' in 'set'. NOT like English 'ee'. Words: небо (sky), село (village). New consonants Д, В, Р appear in examples — focus is on the vowel sound.
  - И — uniquely Ukrainian. No exact English equivalent. Jaw relaxed, tongue lower than І. Words: риба (fish), сир (cheese), син (son).
  - І — like 'ee' in 'see'. Brighter and higher than И. Words: ліс (M1 review), кіт (M1 review), сік (M1 review).
  - The И vs І distinction is the hardest vowel contrast for English speakers. Drill with minimal pairs: кит (whale) vs кіт (cat). Feel the jaw position.
- `## Наголос — Word Stress` (~150 words)
  - Every Ukrainian word has one stressed syllable. The stressed vowel is louder and slightly longer, but its quality does NOT change.
  - Golden Rule: Ukrainian vowels stay pure in any position — stressed or unstressed. English speakers naturally swallow unstressed vowels into schwa (uh). Fight this!
  - Example: молоко — stress on last syllable (молокО), but all three О's sound the same. Compare English 'photograph' where vowels shift with stress.
- `## Йотовані голосні — Iotated Vowels` (~350 words)
  - Я, Ю, Є, Ї are 'double-duty' vowels. At word start or after another vowel, they represent TWO sounds: Й + base vowel.
  - Я = й+а. At start: яблуко (apple). After vowel: моя (my-f). After consonant: softens it (дядько — Д becomes soft before Я).
  - Ю = й+у. At start: юнак (young man), юшка (broth). After consonant: softens it (люди — Л becomes soft).
  - Є = й+е. At start: Європа (Europe). After vowel: моє (my-n).
  - Ї = ALWAYS two sounds й+і, never softens a consonant. Words: їжак (hedgehog), їжа (food), Україна. Cultural note: the letter Ї as a symbol of Ukrainian identity.
  - Й — the semi-vowel itself. Short consonant-like sound. Words: край (edge/land), йогурт. Never forms a syllable alone.
- `## Голосні в словах — Vowels in Words` (~200 words)
  - Reading practice — words organized by vowel focus. Use any consonants freely (consonant system is covered in M3).
  - Short sentences: Це яблуко. Це моє село. Мама каже 'так'. Де мій кіт?
  - Count-the-vowels exercise: молоко (3 vowels = 3 syllables), Україна (4 vowels = 4 syllables: У-кра-ї-на), кіт (1 vowel = 1 syllable).
- `## Підсумок — Summary` (~100 words)
  - 10 vowel letters: 6 base (А О У Е И І) + 4 iotated (Я Ю Є Ї) + semi-vowel Й.
  - Golden Rule reinforced: Ukrainian vowels stay pure — never swallow or reduce them.
  - Self-check: Can you pronounce all 6 base vowels? What two sounds does Я make at word start? What is the difference between И and І?
  - Next: M3 masters the consonant system — voiced/voiceless pairs, sonorants, hard vs soft.

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ — Introduction | 100+ |
| Шість основних голосних — Six Base Vowels | 300+ |
| Наголос — Word Stress | 150+ |
| Йотовані голосні — Iotated Vowels | 350+ |
| Голосні в словах — Vowels in Words | 200+ |
| Підсумок — Summary | 100+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Rules (read ALL before writing)

### RULE 1: GRAMMAR — see Section 6

Section 6 (Hard Constraints) defines exactly what grammar structures you may use for this module. Follow those constraints — they vary by module number.

### RULE 2: VOCABULARY

Prioritize these Ukrainian words (from the plan). You may also use words from the cumulative vocabulary and common Ukrainian words, but these are your core teaching targets:

**Allowed Ukrainian words:** яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя, вухо, їжа, моє, яйце, юшка, каша, небо, сир

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
**Required types:** watch-and-repeat, classify, image-to-letter, quiz, group-sort

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
