**Curriculum context:** This is Module 4 of the A1 track (Ukrainian for English speakers). Title: "Completing the Alphabet" — Завершуємо алфавіт — Soft Sign, Apostrophe, Affricates, and Digraphs. Phase: A1.1 [First Contact]. Previous module: Consonant Sounds. Next module: Syllables And Word Division.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/completing-the-alphabet-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/completing-the-alphabet.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Soft sign palatalization (Ь) Apostrophe function and rules", grade=1-2)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 3
**Previous module:** Consonant Sounds

**Cumulative vocabulary (55 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно
яблуко, риба, село, Україна, їжак, юнак, край, день, син, мій
вухо, їжа, яйце, юшка, каша, небо, сир, Європа, хліб, зуб
дім, вовк, жук, шапка, гора, рука, бабуся, павук, ґанок, кінь
люди, суп, вода, дим, люк

**Grammar already taught (14 topics):**
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

**Coming next (module after this):** Syllable structure, Open and closed syllables, Word division rules
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- сіль (salt) — demonstrates Ь softening; everyday kitchen word
- день (day) — demonstrates Ь; top 50 word; collocation: добрий день
- Львів (Lviv) — demonstrates Ь before consonant; cultural significance
- м'ясо (meat) — demonstrates apostrophe; everyday food
- п'ять (five) — demonstrates apostrophe; number
- сім'я (family) — demonstrates apostrophe; high-frequency
- цукор (sugar) — demonstrates Ц; everyday kitchen word
- час (time/hour) — demonstrates Ч; top 100 word
- що (what) — demonstrates Щ; top 10 word
- джерело (spring/source) — demonstrates ДЖ digraph
- дзвін (bell) — demonstrates ДЗ digraph; cultural (church bells)

**Recommended** (use in your content to reach the vocabulary target):
- осінь (autumn) — demonstrates Ь; seasonal vocabulary
- м'яч (ball) — demonstrates apostrophe; children's vocabulary
- щастя (happiness) — demonstrates Щ; high-frequency
- факт (fact) — demonstrates Ф; internationalism
- бджола (bee) — demonstrates ДЖ; nature vocabulary
- дзеркало (mirror) — demonstrates ДЗ; everyday object
- черепаха (turtle) — demonstrates Ч; children's literature
- цибуля (onion) — demonstrates Ц; everyday food
- чай (tea) — demonstrates Ч; high-frequency
- кінь (horse) — Ь minimal pair; Bolshakova

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

- **Ukrainian Phrasebook: Alphabet** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ph-alphabet/
  Relevance: 0.4
  Topics: alphabet, pronunciation, basics

- **Talk Ukrainian: Ukrainian alphabet with pronunciation** (talkukrainian)
  URL: https://talkukrainian.com/ukrainian-alphabet/
  Relevance: 0.4
  Topics: alphabet, letters, pronunciation, cyrillic

- **Ukrainian Alphabet: Full Guide with Examples and Pronunciation** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ukrainian-alphabet/
  Relevance: 0.3
  Topics: alphabet, cyrillic, pronunciation, letters

- **Transliteration of Ukrainian — How to Write Ukrainian in Latin Letters** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/transliteration/
  Relevance: 0.3
  Topics: transliteration, writing, alphabet


### Textbook References
- **Grade 2, Сторінка 26**
  АЛФАВІТ
НАВЧАЮСЯ РОЗТАШОВУВАТИ СЛОВА ЗА АЛФАВІТОМ
Переставте рядки так, щоб прочитати вірш.
Усі тут літери живуть 
їх 33 — від А до Я.
Це місто алфавітом звуть. 
щасливо й дружно, як сім'я.
<г
алфавіт...

- **Grade 1, Сторінка 4**
  4
АБЕТКА
Абетку ти береш до рук.
Абетка — ключ до всіх наук,
До всіх історій чарівних,
І таємничих, і смішних.
Рушаймо! Ось вона, твоя
Стежиночка від А до Я.
	
Григорій Фалькович
АБЕТКА
Ти можеш запис...

- **Grade 3, Сторінка 22**
  22
Дивовижний вèнахід
А далі сталася подія величезної вагè: люди 
вèнайшли письмо. Наше слов’янське письмо — зна-
йомі й звичні літери абетки — пройшло довжелåзний 
шлях, поки дійшло до нас. Поклав по...

- **Grade 1, Сторінка 11**
  11
БУКВИ 
Ти можеш записати те, що говориш, буквами. 
Букви — це умовні знаки, які позначають звуки мови.
Букви ти можеш побачити 
 і написати 
.
Якщо ти запишеш букви української мови в певному 
поря...

- **Grade 10, Сторінка 160**
  Українська морфологія
160
Буду я  навчатись мови золотої
У сучасній українській мові вживаються переважно повні фор-
ми прикметників. Коротку форму, крім кількох якісних, мають при-
свійні прикметники...


### Pronunciation Videos (from plan — MANDATORY embeds)
*Credit: Anna Ohoiko — Ukrainian Lessons*

- **Overview**: [Anna Ohoiko — Ukrainian Lessons — Overview](https://www.youtube.com/watch?v=ksXIXj7CXwc)
- **Full Playlist**: [Anna Ohoiko — Ukrainian Lessons — Playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)

**Each letter below MUST get its video embedded in the corresponding H3 section:**

- **Літера Ь**: [Anna Ohoiko — Ukrainian Lessons — Ь](https://www.youtube.com/watch?v=cJlal8XKBxo)
- **Літера Ґ**: [Anna Ohoiko — Ukrainian Lessons — Ґ](https://www.youtube.com/watch?v=gNjHqjTW9WQ)
- **Літера Ф**: [Anna Ohoiko — Ukrainian Lessons — Ф](https://www.youtube.com/watch?v=haHRsFFZRQI)
- **Літера Щ**: [Anna Ohoiko — Ukrainian Lessons — Щ](https://www.youtube.com/watch?v=QmBLieIuf6Q)
- **Літера Ц**: [Anna Ohoiko — Ukrainian Lessons — Ц](https://www.youtube.com/watch?v=u44eCjR2Oz8)
- **Літера Ч**: [Anna Ohoiko — Ukrainian Lessons — Ч](https://www.youtube.com/watch?v=UsJkbdsY2RA)



---

## 4. Outline

Write **Completing the Alphabet** for the a1 track. Target: 1200–1800 words.

### CRITICAL: EXACT H2 HEADERS (copy-paste, do not alter)

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ — Introduction` (~100 words)
  - Review: M1 gave you the map, M2 mastered vowels, M3 mastered consonants. Today: the final pieces — modifiers (Ь, apostrophe), affricates (Ц Ч Щ), digraphs (ДЖ ДЗ), and the rare Ф. After this, you can read ANY Ukrainian word.
- `## М'який знак — The Soft Sign` (~250 words)
  - Ь has no sound of its own — it softens (palatalizes) the consonant before it. Place your tongue closer to the roof of your mouth.
  - Words: сіль (salt), день (day), Львів (Lviv), мідь (copper), осінь (autumn).
  - Pattern: Ь appears after consonants at word end (сіль, день) or before another consonant (Львів). Never at word start, never after vowels.
  - Minimal pair: кінь (horse) vs кін (a stake in a game) — Ь changes the preceding consonant's quality, creating a different word.
- `## Апостроф — The Apostrophe` (~250 words)
  - The apostrophe separates a consonant from a following iotated vowel (Я Ю Є Ї), preserving the Й-sound that would otherwise be absorbed into softening.
  - Words: м'ясо (meat), п'ять (five), сім'я (family), м'яч (ball), об'єкт (object).
  - Rule: apostrophe appears after Б, П, В, М, Ф, Р before Я, Ю, Є, Ї.
  - Compare: without apostrophe, М+Я would mean 'soft М + А'. With apostrophe, М'Я means 'hard М + Й + А'. The apostrophe is NOT optional.
- `## Африкати, Щ та Ф — Affricates, Щ, and Ф` (~300 words)
  - Ц — a true affricate: Т+С fused into one sound. Like English 'ts' in 'cats'. Words: цукор (sugar), цибуля (onion). Common in endings: -ець, -иця.
  - Ч — a true affricate: like English 'ch' in 'church'. Very frequent. Words: час (time/hour), черепаха (turtle), чай (tea).
  - Щ — NOT an affricate. It represents TWO separate sounds: Ш+Ч (a consonant cluster written as one letter). Words: що (what), ще (still/more), щастя (happiness). що appears in almost every conversation.
  - Ф — like English 'f'. Rare in native Ukrainian words — appears mostly in borrowings: факт (fact), фото (photo). Voiceless partner of В.
- `## Диграфи ДЖ, ДЗ — Digraphs` (~150 words)
  - Two letters, one sound each. These are single phonemes written with two characters.
  - ДЖ — like English 'j' in 'jungle'. Words: джерело (spring/source), бджола (bee). Voiced partner of Ч.
  - ДЗ — no English equivalent. Voiced partner of Ц. Words: дзвін (bell), дзеркало (mirror). Uniquely Ukrainian — absent from Russian.
- `## Весь алфавіт! — The Full Alphabet Mastered` (~150 words)
  - The complete 33-letter Ukrainian alphabet: А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я. Plus digraphs ДЖ, ДЗ and the apostrophe.
  - Full-alphabet reading challenge: a short paragraph using all letter types — vowels, consonants, soft sign, apostrophe, affricates, digraphs.
  - Survival phrases using the full alphabet: Добрий день! (Good day!) Як справи? (How are you?) Дякую! (Thank you!) Будь ласка! (Please!) До побачення! (Goodbye!)
  - Celebration: you can now decode any Ukrainian word. The reading skills from M1-M4 are the foundation for everything that follows.
- `## Підсумок — Summary` (~100 words)
  - Recap: Ь softens consonants, apostrophe preserves Й-sound, Ц and Ч are affricates, Щ is a Ш+Ч cluster, ДЖ and ДЗ are digraphs, Ф is rare.
  - Self-check: What does Ь do? When do you use an apostrophe? What two sounds does Щ represent? Can you read any Ukrainian word now?
  - Next: M5 — syllables and word division.

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ — Introduction | 100+ |
| М'який знак — The Soft Sign | 250+ |
| Апостроф — The Apostrophe | 250+ |
| Африкати, Щ та Ф — Affricates, Щ, and Ф | 300+ |
| Диграфи ДЖ, ДЗ — Digraphs | 150+ |
| Весь алфавіт! — The Full Alphabet Mastered | 150+ |
| Підсумок — Summary | 100+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Rules (read ALL before writing)

### RULE 1: GRAMMAR — see Section 6

Section 6 (Hard Constraints) defines exactly what grammar structures you may use for this module. Follow those constraints — they vary by module number.

### RULE 2: VOCABULARY

Prioritize these Ukrainian words (from the plan). You may also use words from the cumulative vocabulary and common Ukrainian words, but these are your core teaching targets:

**Allowed Ukrainian words:** сіль, день, Львів, м'ясо, п'ять, сім'я, цукор, час, що, джерело, дзвін, осінь, м'яч, щастя, факт, бджола, дзеркало, черепаха, цибуля, чай, кінь

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
**Required types:** watch-and-repeat, classify, image-to-letter, quiz, classify

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
