You are about to build a module using the prompt below. Before you start, verify the prompt is ready.

**Default answer: PASS.** Only report genuine issues that would cause audit gate failures or introduce errors.

## The Prompt

<prompt>
**Curriculum context:** This is Module 7 of the A1 track (Ukrainian for English speakers). Title: "The Gender Code" — Unlocking Ukrainian Gender Patterns. Phase: A1.1 [First Contact]. Previous module: Stress And Intonation. Next module: Greetings And Politeness.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/the-gender-code-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-gender-code.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Three-gender system Declension families overview", grade=1-2)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 6
**Previous module:** Stress and Intonation

**Cumulative vocabulary (103 words):**
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
відповідь, кафе, голос

**Grammar already taught (26 topics):**
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

**Coming next (module after this):** T-V distinction, Imperative forms in politeness expressions
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- брат (brother) — старший брат (older brother); high-frequency family term
- сестра (sister) — молодша сестра (younger sister); high-frequency family term
- мама (mother) — моя мама; люба мама; high-frequency feminine
- тато (father) — мій тато (my dad); natural gender overrides -o ending; masculine trap
- дім (house) — новий дім; рідний дім; high-frequency masculine
- вікно (window) — відкрите вікно; велике вікно; чисте вікно; high-frequency neuter
- книга (book) — цікава книга; стара книга; електронна книга; high-frequency feminine
- місто (city) — моє місто; велике місто; State Standard §4.2.1.1 example

**Recommended** (use in your content to reach the vocabulary target):
- стіл (table) — дерев'яний стіл; великий стіл; новий стіл; core masculine
- море (sea) — синє море; тепле море; high-frequency neuter
- ніч (night) — добра ніч (good night); feminine exception with soft sign
- день (day) — гарний день (good day); masculine contrast with 'ніч'
- земля (earth) — рідна земля; чорна земля; feminine ending in -я
- серце (heart) — добре серце; моє серце; high-frequency neuter
- сонце (sun) — ясне сонце; cultural hook; neuter life-giver
- собака (dog) — моя собака (my dog); feminine despite some colloquial masculine usage
- ім'я (name) — моє повне ім'я; гарне ім'я; neuter exception (Family 4)
- артефакт (artifact) — S.T.A.L.K.E.R. hook; masculine consonant ending
- зона (zone) — S.T.A.L.K.E.R. hook; feminine -a ending
- укриття (shelter) — S.T.A.L.K.E.R. hook; neuter -я ending with stem change

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

### Videos
- **All About Ukrainian Instrumental Case: Grammar, Usage, Practice** (Let's Learn Ukrainian)
  URL: https://www.youtube.com/watch?v=7q87c9T2QeA
  Score: 0.5 -- The video primarily explains the Ukrainian Instrumental Case and its usage, not directly the concept of noun gender, which is the module's core topic. It uses gendered nouns as examples within the context of case declension, offering a tangential connection.
  Suggested placement: After section Практичні вправи (Practice Exercises) -- as a broader exposure to noun forms and their variations in different cases, which can reinforce the idea that nouns have specific grammatical properties beyond just gender.
  Key excerpt: Today We are talking about Instrumental Case Instrumental caselates to ukrainian as орудний відмінок орудний орудний.


### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **ULP S4 Ep157: Ukrainian Lessons Podcast Season 4**
  URL: https://www.ukrainianlessons.com/episode157/
  Relevance: 0.4
  Topics: grammar, gender

### Blog Articles & Guides
- **Dobra Forma: Gender of Nouns** (dobraforma)
  URL: https://opentext.ku.edu/dobraforma/chapter/1-1/
  Relevance: 0.4
  Topics: gender, nouns, grammar

- **Dobra Forma: Gender of Nouns (Masculine and Feminine)** (dobraforma)
  URL: https://opentext.ku.edu/dobraforma/chapter/1-2/
  Relevance: 0.4
  Topics: gender, nouns, grammar

- **Dobra Forma: Gender of Nouns (Neuter)** (dobraforma)
  URL: https://opentext.ku.edu/dobraforma/chapter/1-3/
  Relevance: 0.4
  Topics: gender, nouns, grammar

- **Noun Genders in Ukrainian** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/noun-genders-in-ukrainian/
  Relevance: 0.3
  Topics: gender, nouns, grammar


### Textbook References
- **Grade 4, Сторінка 35**
  35
1. Розгляньте у групі однокласників таблицю. Дайте
відповіді  на  запитання  Читалочки.
Роди іменників
Чоловічий рід
(він, мій)
Жіночий рід
(вона, моя)
Середній рід
(воно, моє)
берег
кінь
батько
рі...

- **Grade 3, Сторінка 110**
  110
Навчаюся визначати рід іменників
34
Рід іменників:  
чоловічий, жіночий, середній
	 	
1   Визначте, істоту якого роду називає 
кожний іменник.
	 	
3   Допишіть пари слів за зразком.
2   Прочита...

- **Grade 4, Сторінка 58**
  •  Спишіть перший абзац тексту, розкриваючи дужки. Укажіть 
відмінок змінених іменників у дужках. Позначте закінчення 
іменників. Підкресліть іменники жіночого роду, які стоять у по­
чатковій формі.
1...

- **Grade 4, Сторінка 54**
  •  Випишіть речення, що відповідає схемі.
•  Випишіть речення з однорідними підметами. Підкресліть 
головні члени речення.
•  Зробіть звуко-буквений аналіз виділеного слова.
112. Напишіть текст-розпов...

- **Grade 6, Сторінка 129**
  § 25. Рід іменників. Іменники спільного роду  
129
§ 25. Рід іменників. Іменники спільного роду
Вправа 260
1. Прочитайте словосполучення.
парк міський
мода міська
свято міське
2. Чому, на вашу думку, ...






---

## 4. Outline

Write **The Gender Code** for the a1 track. Target: 1200–1800 words.

### CRITICAL: EXACT H2 HEADERS (copy-paste, do not alter)

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ (Introduction)` (~175 words)
  - Introduction to the Ukrainian three-gender system: Masculine, Feminine, and Neuter — stressing that gender is a linguistic category for all nouns, not just people.
  - Cultural Hook: The Neuter Sun (сонце) — explain its role as an impartial, gentle life-giver in Ukrainian folklore, contrasting it with the masculine sun in Romance languages (el sol/le soleil).
  - Visual Mnemonic Framework: Categorization logic using color codes — Blue for Masculine (Hard/Consonant), Red for Feminine (Open/A-ending), and Yellow for Neuter (Round/O-E-ending).
- `## Презентація правил (Presentation of Rules)` (~300 words)
  - Pattern Recognition for Endings: Masculine (consonant: стіл, хліб, дім), Feminine (-а/-я: книга, кімната, земля), and Neuter (-о/-е: вікно, місто, море).
  - State Standard §4.2.2 Integration: Introduction of possessive pronouns 'мій, моя, моє' as the primary diagnostic tool for gender agreement and identity.
  - Syntactic Agreement: How gender dictates the form of adjectives and pronouns — examples with 'великий стіл' (M), 'цікава книга' (F), and 'чисте вікно' (N).
  - Identity and Family Dialogue: High-frequency context using 'брат' (M), 'сестра' (F), 'мама' (F), and 'тато' (M) to demonstrate natural vs. grammatical gender.
- `## Практичні вправи (Practice Exercises)` (~300 words)
  - Natural Gender Override Trap: The case of 'тато' — explain that biological sex overrides the '-o' ending, making it Masculine (мій тато); contrast with 'місто' (N).
  - The Soft Sign Ambiguity (Ь): Drill with the high-frequency minimal pair 'день' (Masculine) vs. 'ніч' (Feminine); strategy for memorizing these essential 'soft' exceptions.
  - The 'Name' Trap and Family 4: Explaining why 'ім'я' (name) is Neuter despite ending in '-я' — contrast with Feminine 'земля' to avoid common learner confusion.
  - State Standard §4.2.1.1 Drill: Categorizing high-frequency nouns 'чоловік' (man), 'жінка' (woman), and 'місто' (city) into their respective gender buckets.
- `## Самостійна робота (Independent Work/Production)` (~250 words)
  - The 'It' Trap Correction: Targeted drill to stop learners from using neuter 'воно' for all objects; reinforcing 'стіл = він' and 'книга = вона'.
  - Mapping Gender to Modern Contexts: Using S.T.A.L.K.E.R. vocabulary — 'Артефакт' (M), 'Зона' (F), and 'Укриття' (N) as classification anchors.
  - Applying Agreement: Creating simple descriptive phrases for personal items and nature terms using 'мій/моя/моє' and basic adjectives (новий, цікавий, великий).
- `## Культурний код та підсумок (Cultural Code and Summary)` (~175 words)
  - Summary of gender prediction from endings: 95% predictability rule — reinforcement of the 'Soft Sign' and 'Natural Gender' exceptions.
  - Cultural Reflection: How gendered language shapes the Ukrainian worldview — personification of nature (земля-мати, сонце-життя).
  - Final Competency Check: Identification of gender for core identity vocabulary (ім'я, тато, мама, місто) as per State Standard requirements.

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ (Introduction) | 175+ |
| Презентація правил (Presentation of Rules) | 300+ |
| Практичні вправи (Practice Exercises) | 300+ |
| Самостійна робота (Independent Work/Production) | 250+ |
| Культурний код та підсумок (Cultural Code and Summary) | 175+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Rules (read ALL before writing)

### RULE 1: GRAMMAR — see Section 6

Section 6 (Hard Constraints) defines exactly what grammar structures you may use for this module. Follow those constraints — they vary by module number.

### RULE 2: VOCABULARY

Prioritize these Ukrainian words (from the plan). You may also use words from the cumulative vocabulary and common Ukrainian words, but these are your core teaching targets:

**Allowed Ukrainian words:** брат, сестра, мама, тато, дім, вікно, книга, місто, стіл, море, ніч, день, земля, серце, сонце, собака, ім'я, артефакт, зона, укриття

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
**Required types:** match-up, quiz, fill-in, match-up

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

GRAMMAR CONSTRAINTS (A1.1 — Grammar, M07-M14):
Keep grammar simple — first exposure to Ukrainian grammar.

ALLOWED:
- Це + noun: «Це кіт», «Це мама»
- Simple present tense (я читаю, я бачу)
- Basic imperatives (читай, слухай, дивись)
- Question words: «Хто це?», «Що це?», «Де?»
- Так/Ні answers
- Adj + noun: «великий дім», «нова книга»

BANNED: Past/future tense, conditionals, participles, passive, gerunds,
compound sentences (no і/а/але joining clauses)

METALANGUAGE: English first, Ukrainian in parentheses. Bilingual headings.

- **No Russianisms**: кушати→їсти, получати→отримувати, самий→найкращий
- **No Russian characters**: ы, э, ё, ъ — never
- **No colonial framing**: never define Ukrainian by comparing it to Russian. Don't say "unlike Russian..." or "not found in Russian." Present Ukrainian on its own terms
- **No IPA or Latin transliteration** — stress marks (´) only
- **Ukrainian quotes** in content: «...» | **YAML values**: plain text or single quotes (never «»)
- **Euphony** (у/в, і/й alternation): follow rules in the shared content rules section below — audit flags violations
- **YAML colon values**: quote with single quotes: `'text: with colon'`
- H2 titles must match the outline EXACTLY. You MAY add H3 sub-headings within H2 sections (e.g., for individual letters, grammar sub-topics)
- **MUST end with `## Культурний код та підсумок (Cultural Code and Summary)`** with self-check questions

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
module: a1-007
level: A1
sequence: 7
slug: the-gender-code
version: '2.0'
title: The Gender Code
subtitle: Unlocking Ukrainian Gender Patterns
focus: grammar
pedagogy: PPP
phase: A1.1 [First Contact]
word_target: 1200
objectives:
- Learner can identify noun gender by word ending
- Learner can categorize nouns into 4 declension families
- 'Learner recognizes patterns: consonant (m), -а/-я (f), -о/-е (n)'
- Learner can identify common exceptions
content_outline:
- section: Вступ (Introduction)
  words: 175
  points:
  - 'Introduction to the Ukrainian three-gender system: Masculine, Feminine, and Neuter — stressing that gender is a linguistic
    category for all nouns, not just people.'
  - 'Cultural Hook: The Neuter Sun (сонце) — explain its role as an impartial, gentle life-giver in Ukrainian folklore, contrasting
    it with the masculine sun in Romance languages (el sol/le soleil).'
  - 'Visual Mnemonic Framework: Categorization logic using color codes — Blue for Masculine (Hard/Consonant), Red for Feminine
    (Open/A-ending), and Yellow for Neuter (Round/O-E-ending).'
- section: Презентація правил (Presentation of Rules)
  words: 300
  points:
  - 'Pattern Recognition for Endings: Masculine (consonant: стіл, хліб, дім), Feminine (-а/-я: книга, кімната, земля), and
    Neuter (-о/-е: вікно, місто, море).'
  - 'State Standard §4.2.2 Integration: Introduction of possessive pronouns ''мій, моя, моє'' as the primary diagnostic tool
    for gender agreement and identity.'
  - 'Syntactic Agreement: How gender dictates the form of adjectives and pronouns — examples with ''великий стіл'' (M), ''цікава
    книга'' (F), and ''чисте вікно'' (N).'
  - 'Identity and Family Dialogue: High-frequency context using ''брат'' (M), ''сестра'' (F), ''мама'' (F), and ''тато'' (M)
    to demonstrate natural vs. grammatical gender.'
- section: Практичні вправи (Practice Exercises)
  words: 300
  points:
  - 'Natural Gender Override Trap: The case of ''тато'' — explain that biological sex overrides the ''-o'' ending, making
    it Masculine (мій тато); contrast with ''місто'' (N).'
  - 'The Soft Sign Ambiguity (Ь): Drill with the high-frequency minimal pair ''день'' (Masculine) vs. ''ніч'' (Feminine);
    strategy for memorizing these essential ''soft'' exceptions.'
  - 'The ''Name'' Trap and Family 4: Explaining why ''ім''я'' (name) is Neuter despite ending in ''-я'' — contrast with Feminine
    ''земля'' to avoid common learner confusion.'
  - 'State Standard §4.2.1.1 Drill: Categorizing high-frequency nouns ''чоловік'' (man), ''жінка'' (woman), and ''місто''
    (city) into their respective gender buckets.'
- section: Самостійна робота (Independent Work/Production)
  words: 250
  points:
  - 'The ''It'' Trap Correction: Targeted drill to stop learners from using neuter ''воно'' for all objects; reinforcing ''стіл
    = він'' and ''книга = вона''.'
  - 'Mapping Gender to Modern Contexts: Using S.T.A.L.K.E.R. vocabulary — ''Артефакт'' (M), ''Зона'' (F), and ''Укриття''
    (N) as classification anchors.'
  - 'Applying Agreement: Creating simple descriptive phrases for personal items and nature terms using ''мій/моя/моє'' and
    basic adjectives (новий, цікавий, великий).'
- section: Культурний код та підсумок (Cultural Code and Summary)
  words: 175
  points:
  - 'Summary of gender prediction from endings: 95% predictability rule — reinforcement of the ''Soft Sign'' and ''Natural
    Gender'' exceptions.'
  - 'Cultural Reflection: How gendered language shapes the Ukrainian worldview — personification of nature (земля-мати, сонце-життя).'
  - 'Final Competency Check: Identification of gender for core identity vocabulary (ім''я, тато, мама, місто) as per State
    Standard requirements.'
vocabulary_hints:
  required:
  - брат (brother) — старший брат (older brother); high-frequency family term
  - сестра (sister) — молодша сестра (younger sister); high-frequency family term
  - мама (mother) — моя мама; люба мама; high-frequency feminine
  - тато (father) — мій тато (my dad); natural gender overrides -o ending; masculine trap
  - дім (house) — новий дім; рідний дім; high-frequency masculine
  - вікно (window) — відкрите вікно; велике вікно; чисте вікно; high-frequency neuter
  - книга (book) — цікава книга; стара книга; електронна книга; high-frequency feminine
  - місто (city) — моє місто; велике місто; State Standard §4.2.1.1 example
  recommended:
  - стіл (table) — дерев'яний стіл; великий стіл; новий стіл; core masculine
  - море (sea) — синє море; тепле море; high-frequency neuter
  - ніч (night) — добра ніч (good night); feminine exception with soft sign
  - день (day) — гарний день (good day); masculine contrast with 'ніч'
  - земля (earth) — рідна земля; чорна земля; feminine ending in -я
  - серце (heart) — добре серце; моє серце; high-frequency neuter
  - сонце (sun) — ясне сонце; cultural hook; neuter life-giver
  - собака (dog) — моя собака (my dog); feminine despite some colloquial masculine usage
  - ім'я (name) — моє повне ім'я; гарне ім'я; neuter exception (Family 4)
  - артефакт (artifact) — S.T.A.L.K.E.R. hook; masculine consonant ending
  - зона (zone) — S.T.A.L.K.E.R. hook; feminine -a ending
  - укриття (shelter) — S.T.A.L.K.E.R. hook; neuter -я ending with stem change
activity_hints:
- type: match-up
  focus: Sort nouns by gender
  items: 30
- type: quiz
  focus: Identify gender by ending
  items: 20
- type: fill-in
  focus: Choose correct gender
  items: 15
- type: match-up
  focus: Noun → gender
  items: 20
connects_to:
- a1-09 (This Is, I Am)
- a1-11 (Adjectives)
prerequisites:
- a1-02 (Vowel Sounds)
persona:
  voice: Patient Supportive Tutor
  role: Linguistic Taxonomist
grammar:
- Three-gender system
- Declension families overview
- Gender prediction rules
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