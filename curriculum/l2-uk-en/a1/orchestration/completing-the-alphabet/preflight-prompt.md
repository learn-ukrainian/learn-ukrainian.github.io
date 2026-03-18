You are about to build a module using the prompt below. Before you start, verify the prompt is ready.

**Default answer: PASS.** Only report genuine issues that would cause audit gate failures or introduce errors.

## The Prompt

<prompt>
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

**Cumulative vocabulary (39 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, ніс, сон
сік, стіл, кіно, тут, там, так, ні, привіт, дякую, це
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, кит

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

Write **Completing the Alphabet** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **0–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

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

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Soft sign palatalization (Ь) Apostrophe function and rules", grade=1-2)` — find how textbooks teach this
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

</prompt>

## The Plan

<plan>
module: a1-004
level: A1
sequence: 4
slug: completing-the-alphabet
version: '2.0'
title: Completing the Alphabet
subtitle: "Завершуємо алфавіт — Soft Sign, Apostrophe, Affricates, and Digraphs"
focus: grammar
pedagogy: PPP
phase: A1.1 [First Contact]
word_target: 1200
objectives:
- Learner understands the soft sign (Ь) as a consonant modifier with no sound of its own
- Learner understands the apostrophe as a separator preserving the Й-sound
- "Learner can pronounce affricates Ц, Ч, Щ and digraphs ДЖ, ДЗ"
- Learner knows Ф appears mostly in borrowed words
- "Learner can read any Ukrainian word — the full 33-letter alphabet is mastered"
content_outline:
- section: Вступ — Introduction
  words: 100
  points:
  - "Review: M1 gave you the map, M2 mastered vowels, M3 mastered consonants. Today:
    the final pieces — modifiers (Ь, apostrophe), affricates (Ц Ч Щ), digraphs
    (ДЖ ДЗ), and the rare Ф. After this, you can read ANY Ukrainian word."
- section: "М'який знак — The Soft Sign"
  words: 250
  points:
  - "Ь has no sound of its own — it softens (palatalizes) the consonant before it.
    Place your tongue closer to the roof of your mouth."
  - "Words: сіль (salt), день (day), Львів (Lviv), мідь (copper), осінь (autumn)."
  - "Pattern: Ь appears after consonants at word end (сіль, день) or before another
    consonant (Львів). Never at word start, never after vowels."
  - "Minimal pair: кінь (horse) vs кін (a stake in a game) — Ь changes the preceding
    consonant's quality, creating a different word."
- section: "Апостроф — The Apostrophe"
  words: 250
  points:
  - "The apostrophe separates a consonant from a following iotated vowel (Я Ю Є Ї),
    preserving the Й-sound that would otherwise be absorbed into softening."
  - "Words: м'ясо (meat), п'ять (five), сім'я (family), м'яч (ball), об'єкт (object)."
  - "Rule: apostrophe appears after Б, П, В, М, Ф, Р before Я, Ю, Є, Ї."
  - "Compare: without apostrophe, М+Я would mean 'soft М + А'. With apostrophe,
    М'Я means 'hard М + Й + А'. The apostrophe is NOT optional."
- section: "Африкати, Щ та Ф — Affricates, Щ, and Ф"
  words: 300
  points:
  - "Ц — a true affricate: Т+С fused into one sound. Like English 'ts' in 'cats'.
    Words: цукор (sugar), цибуля (onion). Common in endings: -ець, -иця."
  - "Ч — a true affricate: like English 'ch' in 'church'. Very frequent. Words:
    час (time/hour), черепаха (turtle), чай (tea)."
  - "Щ — NOT an affricate. It represents TWO separate sounds: Ш+Ч (a consonant
    cluster written as one letter). Words: що (what), ще (still/more), щастя
    (happiness). що appears in almost every conversation."
  - "Ф — like English 'f'. Rare in native Ukrainian words — appears mostly in
    borrowings: факт (fact), фото (photo). Voiceless partner of В."
- section: "Диграфи ДЖ, ДЗ — Digraphs"
  words: 150
  points:
  - "Two letters, one sound each. These are single phonemes written with two characters."
  - "ДЖ — like English 'j' in 'jungle'. Words: джерело (spring/source),
    бджола (bee). Voiced partner of Ч."
  - "ДЗ — no English equivalent. Voiced partner of Ц. Words: дзвін (bell),
    дзеркало (mirror). Uniquely Ukrainian — absent from Russian."
- section: "Весь алфавіт! — The Full Alphabet Mastered"
  words: 150
  points:
  - "The complete 33-letter Ukrainian alphabet: А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М
    Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я. Plus digraphs ДЖ, ДЗ and the apostrophe."
  - "Full-alphabet reading challenge: a short paragraph using all letter types —
    vowels, consonants, soft sign, apostrophe, affricates, digraphs."
  - "Survival phrases using the full alphabet: Добрий день! (Good day!) Як справи?
    (How are you?) Дякую! (Thank you!) Будь ласка! (Please!) До побачення! (Goodbye!)"
  - "Celebration: you can now decode any Ukrainian word. The reading skills from
    M1-M4 are the foundation for everything that follows."
- section: "Підсумок — Summary"
  words: 100
  points:
  - "Recap: Ь softens consonants, apostrophe preserves Й-sound, Ц and Ч are
    affricates, Щ is a Ш+Ч cluster, ДЖ and ДЗ are digraphs, Ф is rare."
  - "Self-check: What does Ь do? When do you use an apostrophe? What two sounds
    does Щ represent? Can you read any Ukrainian word now?"
  - "Next: M5 — syllables and word division."
vocabulary_hints:
  required:
  - "сіль (salt) — demonstrates Ь softening; everyday kitchen word"
  - "день (day) — demonstrates Ь; top 50 word; collocation: добрий день"
  - "Львів (Lviv) — demonstrates Ь before consonant; cultural significance"
  - "м'ясо (meat) — demonstrates apostrophe; everyday food"
  - "п'ять (five) — demonstrates apostrophe; number"
  - "сім'я (family) — demonstrates apostrophe; high-frequency"
  - "цукор (sugar) — demonstrates Ц; everyday kitchen word"
  - "час (time/hour) — demonstrates Ч; top 100 word"
  - "що (what) — demonstrates Щ; top 10 word"
  - "джерело (spring/source) — demonstrates ДЖ digraph"
  - "дзвін (bell) — demonstrates ДЗ digraph; cultural (church bells)"
  recommended:
  - "осінь (autumn) — demonstrates Ь; seasonal vocabulary"
  - "м'яч (ball) — demonstrates apostrophe; children's vocabulary"
  - "щастя (happiness) — demonstrates Щ; high-frequency"
  - "факт (fact) — demonstrates Ф; internationalism"
  - "бджола (bee) — demonstrates ДЖ; nature vocabulary"
  - "дзеркало (mirror) — demonstrates ДЗ; everyday object"
  - "черепаха (turtle) — demonstrates Ч; children's literature"
  - "цибуля (onion) — demonstrates Ц; everyday food"
  - "чай (tea) — demonstrates Ч; high-frequency"
  - "кінь (horse) — Ь minimal pair; Bolshakova"
activity_hints:
- type: watch-and-repeat
  focus: "Pronunciation of Ь-softened consonants, affricates Ц Ч Щ, digraphs ДЖ ДЗ"
  items: 10
- type: classify
  focus: "Identify words containing Ь — which consonant is softened?"
  items: 8
- type: image-to-letter
  focus: "Match picture to word with target letter — цукор→Ц, час→Ч, джерело→ДЖ"
  items: 8
- type: quiz
  focus: "Apostrophe rule — does this word need an apostrophe? (м_ясо, п_ять, сім_я)"
  items: 10
- type: classify
  focus: "Affricate identification — Ц, Ч, or Щ?"
  items: 8
- type: fill-in
  focus: "Full-alphabet reading challenge — decode survival phrases"
  items: 6
- type: match-up
  focus: "Match survival phrase to meaning (Добрий день = Good day, Дякую = Thank you)"
  items: 6
connects_to:
- a1-05 (Syllables and Word Division)
prerequisites:
- a1-03 (Consonant Sounds)
persona:
  voice: Patient Supportive Tutor
  role: Typography Artist
grammar:
- "Soft sign palatalization (Ь)"
- "Apostrophe function and rules"
- "Affricates (Ц, Ч, Щ)"
- "Digraphs (ДЖ, ДЗ)"
- "Ф — rare native, common in borrowings"
- "Full alphabet mastery"
register: розмовний
pronunciation_videos:
  overview: https://www.youtube.com/watch?v=ksXIXj7CXwc
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV
  credit: "Anna Ohoiko — Ukrainian Lessons"
  letters:
    Ь: https://www.youtube.com/watch?v=cJlal8XKBxo
    Ґ: https://www.youtube.com/watch?v=gNjHqjTW9WQ
    Ф: https://www.youtube.com/watch?v=haHRsFFZRQI
    Щ: https://www.youtube.com/watch?v=QmBLieIuf6Q
    Ц: https://www.youtube.com/watch?v=u44eCjR2Oz8
    Ч: https://www.youtube.com/watch?v=UsJkbdsY2RA

</plan>

## Audit Gates

## Audit Gates (your content will be checked against these)

Level: A1
Word target: 1200
Word ceiling: ~1800 (exceeding = FAIL)
Min activities: 0
Min engagement boxes: 3
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