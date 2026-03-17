# Module Build: Content + Activities + Vocabulary

## 1. Goal

> **You are Patient & Supportive Ukrainian Tutor, writing in the voice of Encouraging Cultural Guide.**
>
> Build a complete beginner module for English-speaking teens and adults learning Ukrainian at the a2 level. Your job: **search Ukrainian school textbooks using RAG tools**, then **adapt** the pedagogy for L2 learners.
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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/research/aspect-introduction-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a2/aspect-introduction.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A2.md` | Level constraints, immersion band |
| `schemas/activities-a2.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("imperfective aspect (process) perfective aspect (result)", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 13
**Previous module:** Checkpoint — Cases

**Cumulative vocabulary (218 words):**
мені, тобі, йому, їй, нам, вам, їм, подобатися, допомагати, дзвонити
здаватися, потрібно, треба, необхідно, цікаво, нудно, весело, сумно, важко, легко
приємно, боляче, холодно, жарко, гарно, називний, займенник, прикметник, давальний, іменник
давати, дякувати, поріг, знахідний, множина, з, із, зі, разом, разом з
поруч з, гуляти, розмовляти, зустрічатися, вітатися, спілкуватися, жити, працювати, грати, дружити
товаришувати, приятелювати, посваритися, помиритися, знайомитися, друг, подруга, приятель, знайомий, сусід
колега, партнер, орудний, одружитися, подружитися, познайомитися, автобус, поїзд, машина, метро
таксі, ручка, олівець, ніж, виделка, ложка, трамвай, тролейбус, літак, комп'ютер
телефон, ножиці, голка, молоток, пензель, око, вухо, рука, голова, користуватися
дістатися, бути, стати, ставати, лікар, лікарка, вчитель, вчителька, програміст, програмістка
айтішник, айтішниця, інженер, інженерка, журналіст, журналістка, юрист, юристка, економіст, економістка
менеджер, менеджерка, спеціаліст, спеціалістка, громадянин, громадянка, директор, директорка, тестувальник, філологиня
в, на, під, над, перед, за, між, до, напроти, біля
коло, поруч, навколо, вздовж, всередині, ззовні, посеред, збоку, поміж, стіл
кімната, шафа, диван, вікно, для, без, через, про, після, о
об, завдяки, протягом, крім, замість, від, щодо, стосовно, внаслідок, заради
всупереч, по, причина, мета, тому що, бо, щоб, здоров'я, хто, що
кого, чого, кому, чому, ким, чим, на кому, на чому, відмінок, родовий
місцевий, кличний, однина, закінчення, відмінювати, прийменник, суддя, свідок, пошта, банк
лист, посилка, бандероль, марка, конверт, адреса, індекс, відправляти, отримувати, гроші
рахунок, картка, готівка, валюта, переказ, знімати, вкладати, обмінювати, курс, замовляти
обмін, долар, євро, правильно, помилка, виправити, перевірити, оцінка

**Grammar already taught (56 topics):**
- dative pronouns
- impersonal constructions
- подобатися
- потрібно
- states
- dative noun endings
- masculine dative (-ові/-у)
- feminine dative (-і)
- neuter dative (-у/-ові)
- plural dative (-ам)
- verbs + dative
- verbs + dative + accusative
- indirect objects
- verb government
- instrumental endings
- preposition з/із/зі
- accompaniment
- social interaction
- instrumental of means
- instrumental without prepositions
- transport
- tools
- бути + instrumental
- стати + instrumental
- працювати + instrumental
- past tense of бути
- prepositions of location
- prepositions of motion
- в/на + locative vs accusative
- під/за/над + instrumental
- prepositions of cause (через)
- prepositions of purpose (для)
- prepositions of time (після, до, о)
- other logical prepositions (про, без, крім)
- noun plural paradigms across all 7 cases
- genitive plural formation (ів/їв, zero ending)
- consonant alternation in Nominative plural
- irregular plural nouns
- animate vs inanimate distinction in Accusative plural
- adjective plural declension (all 7 cases)
- hard group endings (-і, -их, -им, -ими)
- soft group endings (-і, -іх, -ім, -іми)
- noun-adjective agreement in plural
- animate vs inanimate Accusative plural
- all 7 cases review
- case selection logic
- common prepositions
- case endings
- accusative for services (відправити листа)
- numbers 100-1000
- currency and exchange rates
- polite requests (я хочу...)
- case system review
- prepositions review
- case functions
- error correction

**Coming next (module after this):** perfective past tense, formation of past tense, narrative sequencing
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 25 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- писати/написати (to write) — писати лист, написати книгу, написати тест; Top 100 verbs
- робити/зробити (to do/make) — робити вправи, зробити домашнє завдання, робити помилку; Top 50 verbs
- говорити/сказати (to say/speak) — говорити правду, сказати слово, сказати комплімент; Top 50 (Suppletive)
- купувати/купити (to buy) — купувати продукти, купити подарунок; High frequency (A2 Shopping)
- пити/випити (to drink) — пити каву, випити склянку води; High frequency (A2 Daily Life)
- ділити/поділити (to divide) — State Standard §4.3.2 example
- виходити/вийти (to go out) — State Standard §4.3.2 example
- забувати/забути (to forget) — State Standard §4.3.2 example
- читати/прочитати (to read) — читати статтю, прочитати новини
- бачити/побачити (to see) — побачити друга, бачити результат
- брати/взяти (to take) — брати участь, взяти таксі; Suppletive pair
- давати/дати (to give) — давати пораду, дати відповідь
- їсти/з'їсти (to eat) — їсти обід, з'їсти все
- вчити/вивчити (to learn) — вчити слова, вивчити правило
- продавати/продати (to sell) — продавати квитки, продати машину
- вид (aspect) — grammar term
- недоконаний (imperfective) — grammar term
- доконаний (perfective) — grammar term

**Recommended** (use in your content to reach the vocabulary target):
- процес (process) — emphasis on duration
- результат (result) — emphasis on completion
- тривалість (duration) — temporal marker
- завершення (completion) — perfective focus
- повторення (repetition) — imperfective focus
- раптом (suddenly) — perfective trigger
- щодня (every day) — imperfective trigger

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 45-65% Ukrainian.
LANGUAGE ROLES:
- THEORY: English prose for grammar explanations that would be too complex in Ukrainian at this level.
- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, cultural context.
- HEADERS: Ukrainian with English in parentheses.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix languages within a sentence. Ukrainian paragraphs and dialogues carry most content. English appears for grammar theory and in callout boxes.
A2 register ONLY. Concrete everyday vocabulary. No literary/poetic language. No abstract nouns. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles.







---

## 4. Outline

Write **Aspect Introduction** for the a2 track.

**Targets:** 2000–3000 words | 4+ callout boxes | **10–15 activities total** (required types + additional types to reach minimum) | 25 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ (Introduction)` (~325 words)
  - Concept of aspect (Process vs Result) — introduce the cultural hook 'Без труда нема плода' (Without labor there is no fruit) to illustrate that a result (fruit) is impossible without a process (labor).
  - Importance of verb pairs for A2 linguistic competence — align with State Standard §4.3.2 requirements for identifying basic aspectual relationships in daily communication.
  - Cultural Hook: The Borsch Ritual — contrast the long, symbolic process of cooking (варити - imperfective) with the finished culinary masterpiece (зварити - perfective), noting UNESCO's 2022 recognition of Ukrainian borsch culture.
- `## Презентація: Видові пари (Presentation: Aspect Pairs)` (~500 words)
  - Classification of aspect pairs by formation: prefixation (писати/написати, робити/зробити, ділити/поділити), suffix/stem change (купувати/купити, забувати/забути), and suppletion (говорити/сказати, брати/взяти).
  - The Present Tense Constraint — explain that perfective verbs DO NOT have a present tense form. Drill the common error where 'Я напишу' is mistakenly used for 'I am writing now' instead of 'I will write/finish'.
  - Identification via time markers: teach context clues for imperfective (часто, щодня, довго, зараз) vs. perfective (уже, нарешті, раптом) to help learners choose the correct form.
- `## Нюанси та типові помилки (Nuances and Common Errors)` (~475 words)
  - Learner error: English '-ing' mapping — address the tendency to assume all '-ing' forms are imperfective; explain cases where focus on completion requires the perfective aspect despite duration.
  - Negation nuances: 'Не робив' (habit/general process) vs. 'Не зробив' (failed result/unfinished task). Provide minimal pairs: 'Я не читав' (I haven't been reading) vs. 'Я не прочитав' (I haven't finished/read it all).
  - Contextual shift: how the choice of aspect changes the perceived meaning of a sentence from a simple description of activity to a statement of achievement.
- `## Практика та вправи (Practice and Exercises)` (~375 words)
  - Drill: Transformation of sentences from process to result using State Standard §4.3.2 verb pairs (e.g., 'Я писав тест' to 'Я написав тест').
  - Contextual sorting: categorizing sentences as 'Process' or 'Result' based on the presence of specific adverbs and aspectual verb forms.
  - Error correction activity: identifying and fixing 'Present Tense Perfective' errors in simple A2-level diary entries or messages.
- `## Діалоги та підсумок (Dialogues and Summary)` (~325 words)
  - Dialogue: 'The Kitchen Check-in' — a situational exchange using 'Did you finish?' (Ти вже зробив...?) vs 'Are you still doing...?' (Ти ще робиш...?) in the context of cooking or chores.
  - Summary of A2 competence: recapping how mastery of aspect pairs allows for more precise descriptions of daily routines and accomplishments.
  - Final reflection on 'The Borsch Ritual': connecting the grammar back to the cultural identity of achieving excellence through dedicated process.

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ (Introduction) | 325+ |
| Презентація: Видові пари (Presentation: Aspect Pairs) | 500+ |
| Нюанси та типові помилки (Nuances and Common Errors) | 475+ |
| Практика та вправи (Practice and Exercises) | 375+ |
| Діалоги та підсумок (Dialogues and Summary) | 325+ |
| **Total** | **2000+ (aim for ~2400)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("imperfective aspect (process) perfective aspect (result)", grade=3-5)` — find how textbooks teach this
2. **Write content** following the outline and lesson arc below
3. **Verify as you write**: `verify_words` on any Ukrainian word you're unsure about
4. **Create activities** from your content
5. **Verify activities**: batch `verify_words` on all activity items

### Beginner Lesson Arc

1. **WELCOME** — warm greeting, set context
2. **PREVIEW** — "By the end of this module, you'll be able to..."
3. **PRESENT** — the main content sections
4. **PRACTICE** — examples, dialogues, reading practice
5. **CELEBRATE** — in the final `## Діалоги та підсумок (Dialogues and Summary)` section, tell learners what they can now do

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
- Read `schemas/activities-a2.schema.json` for full field definitions.

**Allowed types:** quiz, true-false, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction, group-sort, watch-and-repeat, classify, image-to-letter
**Forbidden types:** anagram, essay-response, critical-analysis, comparative-study, authorial-intent
**Required types:** match-up, fill-in, quiz, quiz, fill-in

| Module range | Use these | Avoid these |
|-------------|-----------|-------------|
| M1-M4 (alphabet) | quiz, match-up, group-sort, anagram, true-false, fill-in, watch-and-repeat, image-to-letter, classify | unjumble, cloze, translate |
| M5-M10 | + unjumble, fill-in with sentences | cloze, translate |
| M11+ | all types including translate | cloze (needs 14+ blanks) |

### Item Minimums (HARD FAIL if under)

| Type | Minimum |
|------|--------|
| quiz | ≥8 items |
| true-false | ≥8 items |
| fill-in | ≥8 items |
| match-up | ≥8 pairs |
| unjumble | ≥6 items |
| mark-the-words | ≥6 items |
| error-correction | ≥6 items |
| group-sort | ≥8 items |

### Vocabulary YAML

Object with `items:` wrapper. Each entry: `lemma` (dictionary form), `translation`, `pos`. Optional: `gender`, `notes`, `usage`, `example`. No `ipa` field.

---

## 6. Hard Constraints



- **No Russianisms**: кушати→їсти, получати→отримувати, самий→найкращий
- **No Russian characters**: ы, э, ё, ъ — never
- **No colonial framing**: never define Ukrainian by comparing it to Russian. Don't say "unlike Russian..." or "not found in Russian." Present Ukrainian on its own terms
- **No IPA or Latin transliteration** — stress marks (´) only
- **Ukrainian quotes** in content: «...» | **YAML values**: plain text or single quotes (never «»)
- **Euphony** (у/в, і/й alternation): follow rules in the shared content rules section below — audit flags violations
- **YAML colon values**: quote with single quotes: `'text: with colon'`
- H2 titles must match the outline EXACTLY. You MAY add H3 sub-headings within H2 sections (e.g., for individual letters, grammar sub-topics)
- **MUST end with `## Діалоги та підсумок (Dialogues and Summary)`** with self-check questions

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
