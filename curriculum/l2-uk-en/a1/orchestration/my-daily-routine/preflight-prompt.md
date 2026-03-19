You are about to build a module using the prompt below. Before you start, verify the prompt is ready.

**Default answer: PASS.** Only report genuine issues that would cause audit gate failures or introduce errors.

## The Prompt

<prompt>
**Curriculum context:** This is Module 38 of the A1 track (Ukrainian for English speakers). Title: "My Daily Routine" — Reflexive Verbs and Daily Activities. Phase: A1.4 [Tenses & Daily Life]. Previous module: Tomorrow Future Tense. Next module: Food Vocabulary.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/my-daily-routine-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/my-daily-routine.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Reflexive verbs (-ся/-сь) in context Sequence adverbs (спочатку, потім, нарешті)", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 37
**Previous module:** Tomorrow - Future Tense

**Cumulative vocabulary (230 words):**
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
бувати, здрастуйте, справа, немає, без, гроші, проблема, квиток, ключ, телефон
газ, від, на жаль, вогонь, будь ласка, є, магазин, кухня, пошта, біля
навпроти, знаходитися, поруч, між, близько, парк, аптека, банк, зупинка, метро
новий, великий, маленький, красивий, старий, цікавий, смачний, дорогий, український, молодий
важливий, популярний, фільм, студент, ресторан, церква, де, куди, звідки, через
за, про, робота, центр, іти, їхати, до, з, лікар, Київ
повертатися, виходити, аеропорт, вокзал, вчора, бути, робити, їсти, пити, читати
дивитися, ходити, минулий, раніше, тиждень, місяць, спати, працювати, йти, писати
варити, готувати, купувати, гуляти, додому, завтра, наступний, план, хотіти, збиратися
скоро, потім, рік, сподіватися, мріяти, планувати, пізніше, післязавтра, майбутнє, відпочивати

**Grammar already taught (122 topics):**
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
- Yes/no questions with чи
- Question words
- Negation with не
- Dative construction Мені подобається
- Люблю + Accusative
- Хочу + infinitive
- Possessive pronouns
- Gender agreement
- Variable vs invariable forms
- Reflexive possessive свій (свій vs його/її)
- Demonstrative pronouns
- Proximity distinction
- Cardinals 0-100
- Number agreement (1=nom, 2-4=nom.pl, 5+=gen.pl)
- Genitive plural with numbers
- Clock time expressions (Котра година?)
- Time prepositions (о, до, після)
- Days and months in context
- Present tense conjugation (I and II)
- Question words and Чи-questions
- Preference constructions (Dative, Accusative, Infinitive)
- Vocative case (кличний відмінок)
- Nominative as base form (називний відмінок)
- Case system introduction (7 cases overview)
- Accusative case (inanimate)
- Feminine: -а → -у, -я → -ю
- Masculine/Neuter: no change
- Accusative for animate nouns
- Masculine animate: accusative = genitive
- Feminine animate: same as inanimate
- Accusative prepositions (в/у, на, за, через, про)
- Direction expressions with Accusative
- Preposition semantics and contrast
- Locative case endings
- Prepositions в/у and на
- Location expressions
- Locative case in context
- Directional expressions
- Prepositions of location
- Genitive case for absence
- Genitive endings
- Немає + genitive
- Locative prepositions (в/у, на)
- Euphonic в/у alternation
- Біля/навпроти + Genitive
- Adjective declension in Accusative
- Adjective declension in Locative
- Gender-case agreement patterns
- Accusative case (inanimate and animate)
- Locative case (location)
- Genitive case (absence)
- Prepositions with Accusative and Locative
- Adjective and pronoun declension in oblique cases
- Direction prepositions + Accusative
- До + Genitive
- З/від + Genitive
- Three-question paradigm (Де/Куди/Звідки)
- Past tense formation with L-participle
- Gender agreement in past tense
- Time expressions for past events
- Compound future (буду + infinitive)
- Буду conjugation for all persons
- Future time expressions

**Coming next (module after this):** Food noun gender, Я не їм construction, Food collocations with adjectives
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- прокидатися (to wake up) — High frequency; collocations: рано прокидатися, прокидатися о сьомій
- вмиватися (to wash oneself) — Medium frequency; learner error: distinguish from 'мити руки' (washing hands)
- одягатися (to dress oneself) — Collocations: швидко одягатися, одягатися тепло; note -ся/-сь agreement
- снідати / обідати / вечеряти (to have breakfast/lunch/dinner) — High frequency; note that 'обід' is the main meal (13:00-14:00)
- дивитися (to watch/look) — §4.2.4.1 core conjugation: дивлюся, дивишся, дивиться; focus on reflexive particle
- лягати (спати) (to lie down/go to bed) — High frequency; collocations: лягати спати, лягати пізно
- зазвичай (usually) — High frequency adverb; collocations: я зазвичай встаю, як зазвичай

**Recommended** (use in your content to reach the vocabulary target):
- спочатку (first) — sequence marker for routine
- потім (then) — sequence marker for routine
- нарешті (finally) — sequence marker for finishing the day
- щодня (every day) — frequency marker for habits
- обідня перерва (lunch break) — §3.5 concept; crucial for the working day description
- домашній одяг (home clothes) — cultural hook for the evening transition

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 20-35% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — brief and clear. Show, don't tell.
- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.
- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).
- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.
- PATTERN BOXES: Show transformations: `читати → читай → читайте`.
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes.
Ukrainian sentences max 10 words. Mix container types.

### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **FMU Ep58: How to describe your daily routine in Ukrainian**
  URL: https://www.ukrainianlessons.com/fmu58/
  Relevance: 0.4
  Topics: grammar, verbs, conjugation, phrases, listening


### Textbook References
- **Grade 2, Сторінка 55**
  55
оДнина І мноЖина
Що відбувається? Склади та запиши речення за малюнком. 
Підкресли слова — назви дій. 
ганчірка
витирає
праска
підодіяльник
прибирання
прасує
простирадло
віяло
Зразок. Дарина несе п...

- **Grade 4, Сторінка 162**
  •  Спишіть текст. Підкресліть дієслова. Укажіть у дужках час, 
особу й число дієслів за зразком у тексті.
Дієслова на -ся
370. Прочитайте вірш Галини Кирпи.
Дерево трудиться назеленітися.
Квіточка тру...

- **Grade 6, Сторінка 10**
  10
1.	Прочитайте записи в колонках і виконайте завдання. 
о сьомій годині 
кілька вправ 
контрастним душем
Я прокидаюсь о сьомій годині.
Виконую кілька фізичних вправ. 
Потім загартовуюся контрастним ...

- **Grade 5, Сторінка 84**
  84
Лексикологія.  Підсумковий тест
ПІДСУМКОВИЙ ТЕСТ
Виконайте тестові завдання.  У  завданнях 1—8 оберіть один правильний 
варіант відповіді, у  завданні 9 увідповідніть варіанти з  двох стовпчиків.
1...

- **Grade 6, Сторінка 55**
  55
55
§ 29.  Змінювання   і  творення слів
3.	 Випишіть виділені слова та визначте, від яких слів вони утворені (за 
зразком). 
Зразок. Прожити ← жити. 
1. Життя прожити — не поле перейти. 2. Кінь 
ба...






---

## 4. Outline

Write **My Daily Routine** for the a1 track. Target: 1200–1800 words.

### CRITICAL: EXACT H2 HEADERS (copy-paste, do not alter)

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ (Introduction)` (~250 words)
  - State Standard §3.4/§3.5 Alignment: Introducing typical daily activities (типові щоденні заняття) and the conceptual split between a working day (робочий день) and a day off (вихідний день).
  - Setting the scene: Discussing the start and end of activities (початок і кінець дня) using chronological markers to establish a logical flow for the routine narrative.
- `## Презентація (Presentation)` (~350 words)
  - Reflexive verbs and daily hygiene: Presentation of прокидатися and вмиватися. Explicitly address learner error: confusing reflexive 'вмиватися' (washing one's face/body) with transitive 'мити руки' (washing hands).
  - Morphological focus per §4.2.4.1: Conjugation of Class II reflexive verbs, specifically 'дивитися' (дивлюся, дивишся...). Drill the -ся/-сь rule: using -сь after vowels (я дивлюсь) vs -ся after consonants (ти дивишся).
  - Cultural Hook: The Ukrainian 'Обід' (lunch, 13:00–14:00) as the main, substantial meal of the day (first and second courses), contrasting it with lighter Western lunch habits; use of 'обідня перерва'.
- `## Практика (Practice)` (~325 words)
  - Daily commute and motion: Distinguishing between 'їхати на роботу' (by transport) and 'йти на роботу' (on foot) as part of the daily sequence.
  - Time and Case correction: Addressing the common error of using 'в' + Accusative for time; drilling the correct Locative pattern 'о сьомій годині' for scheduling routine tasks.
  - Frequency and Sequence adverbs: Integrating 'зазвичай' (usually) with markers like 'спочатку' (first), 'потім' (then), and 'після цього' (after that) to build complex descriptions of a day.
- `## Продукування та Підсумок (Production and Summary)` (~275 words)
  - Evening transitions and the 'домашній одяг' (home clothes) cultural hook: Explaining the significance of changing clothes immediately upon returning home to separate public and private spheres.
  - Synthesis Task: Learners describe their own daily routine, contrasting a busy working day with a day off, focusing on reflexive verb agreement and temporal markers.

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ (Introduction) | 250+ |
| Презентація (Presentation) | 350+ |
| Практика (Practice) | 325+ |
| Продукування та Підсумок (Production and Summary) | 275+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Rules (read ALL before writing)

### RULE 1: GRAMMAR — see Section 6

Section 6 (Hard Constraints) defines exactly what grammar structures you may use for this module. Follow those constraints — they vary by module number.

### RULE 2: VOCABULARY

Prioritize these Ukrainian words (from the plan). You may also use words from the cumulative vocabulary and common Ukrainian words, but these are your core teaching targets:

**Allowed Ukrainian words:** прокидатися, вмиватися, одягатися, снідати, дивитися, лягати, зазвичай, спочатку, потім, нарешті, щодня, обідня, домашній

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
**Required types:** quiz, fill-in, match-up, fill-in

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

GRAMMAR CONSTRAINTS (A1.4 — Tenses & Daily Life):
Past tense and future tense introduced. All present tense available.
Imperatives available.

BANNED: participles, passive voice, complex subordination

- **No Russianisms**: кушати→їсти, получати→отримувати, самий→найкращий
- **No Russian characters**: ы, э, ё, ъ — never
- **No colonial framing**: never define Ukrainian by comparing it to Russian. Don't say "unlike Russian..." or "not found in Russian." Present Ukrainian on its own terms
- **No IPA or Latin transliteration** — stress marks (´) only
- **Ukrainian quotes** in content: «...» | **YAML values**: plain text or single quotes (never «»)
- **Euphony** (у/в, і/й alternation): follow rules in the shared content rules section below — audit flags violations
- **YAML colon values**: quote with single quotes: `'text: with colon'`
- H2 titles must match the outline EXACTLY. You MAY add H3 sub-headings within H2 sections (e.g., for individual letters, grammar sub-topics)
- **MUST end with `## Продукування та Підсумок (Production and Summary)`** with self-check questions

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
module: a1-038
level: A1
sequence: 38
slug: my-daily-routine
version: '2.0'
title: My Daily Routine
subtitle: Reflexive Verbs and Daily Activities
focus: practical
pedagogy: PPP
phase: A1.4 [Tenses & Daily Life]
word_target: 1200
objectives:
- Learner can conjugate common reflexive verbs
- Learner can describe daily routine activities
- Learner can use sequence words to order events
- Learner can talk about habits and regular activities
content_outline:
- section: Вступ (Introduction)
  words: 250
  points:
  - 'State Standard §3.4/§3.5 Alignment: Introducing typical daily activities (типові щоденні заняття) and the conceptual
    split between a working day (робочий день) and a day off (вихідний день).'
  - 'Setting the scene: Discussing the start and end of activities (початок і кінець дня) using chronological markers to establish
    a logical flow for the routine narrative.'
- section: Презентація (Presentation)
  words: 350
  points:
  - 'Reflexive verbs and daily hygiene: Presentation of прокидатися and вмиватися. Explicitly address learner error: confusing
    reflexive ''вмиватися'' (washing one''s face/body) with transitive ''мити руки'' (washing hands).'
  - 'Morphological focus per §4.2.4.1: Conjugation of Class II reflexive verbs, specifically ''дивитися'' (дивлюся, дивишся...).
    Drill the -ся/-сь rule: using -сь after vowels (я дивлюсь) vs -ся after consonants (ти дивишся).'
  - 'Cultural Hook: The Ukrainian ''Обід'' (lunch, 13:00–14:00) as the main, substantial meal of the day (first and second
    courses), contrasting it with lighter Western lunch habits; use of ''обідня перерва''.'
- section: Практика (Practice)
  words: 325
  points:
  - 'Daily commute and motion: Distinguishing between ''їхати на роботу'' (by transport) and ''йти на роботу'' (on foot) as
    part of the daily sequence.'
  - 'Time and Case correction: Addressing the common error of using ''в'' + Accusative for time; drilling the correct Locative
    pattern ''о сьомій годині'' for scheduling routine tasks.'
  - 'Frequency and Sequence adverbs: Integrating ''зазвичай'' (usually) with markers like ''спочатку'' (first), ''потім''
    (then), and ''після цього'' (after that) to build complex descriptions of a day.'
- section: Продукування та Підсумок (Production and Summary)
  words: 275
  points:
  - 'Evening transitions and the ''домашній одяг'' (home clothes) cultural hook: Explaining the significance of changing clothes
    immediately upon returning home to separate public and private spheres.'
  - 'Synthesis Task: Learners describe their own daily routine, contrasting a busy working day with a day off, focusing on
    reflexive verb agreement and temporal markers.'
vocabulary_hints:
  required:
  - 'прокидатися (to wake up) — High frequency; collocations: рано прокидатися, прокидатися о сьомій'
  - 'вмиватися (to wash oneself) — Medium frequency; learner error: distinguish from ''мити руки'' (washing hands)'
  - 'одягатися (to dress oneself) — Collocations: швидко одягатися, одягатися тепло; note -ся/-сь agreement'
  - снідати / обідати / вечеряти (to have breakfast/lunch/dinner) — High frequency; note that 'обід' is the main meal (13:00-14:00)
  - 'дивитися (to watch/look) — §4.2.4.1 core conjugation: дивлюся, дивишся, дивиться; focus on reflexive particle'
  - 'лягати (спати) (to lie down/go to bed) — High frequency; collocations: лягати спати, лягати пізно'
  - 'зазвичай (usually) — High frequency adverb; collocations: я зазвичай встаю, як зазвичай'
  recommended:
  - спочатку (first) — sequence marker for routine
  - потім (then) — sequence marker for routine
  - нарешті (finally) — sequence marker for finishing the day
  - щодня (every day) — frequency marker for habits
  - обідня перерва (lunch break) — §3.5 concept; crucial for the working day description
  - домашній одяг (home clothes) — cultural hook for the evening transition
activity_hints:
- type: quiz
  focus: Order daily activities
  items: 20
- type: fill-in
  focus: Complete routine descriptions
  items: 20
- type: match-up
  focus: Match activities to times
  items: 15
- type: fill-in
  focus: Describe your typical day
  items: 6
connects_to:
- a1-11 (Describing Things - Adjectives)
- 'a1-54 (Checkpoint: Communication)'
prerequisites:
- a1-17 (Reflexive Verbs)
- a1-23 (What Time Is It)
persona:
  voice: Patient Supportive Tutor
  role: Time Management Coach
grammar:
- Reflexive verbs (-ся/-сь) in context
- Sequence adverbs (спочатку, потім, нарешті)
- Daily routine expressions
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