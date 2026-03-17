You are about to build a module using the prompt below. Before you start, verify the prompt is ready.

**Default answer: PASS.** Only report genuine issues that would cause audit gate failures or introduce errors.

## The Prompt

<prompt>
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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/research/the-instrumental-i-accompaniment-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a2/the-instrumental-i-accompaniment.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A2.md` | Level constraints, immersion band |
| `schemas/activities-a2.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("instrumental endings preposition з/із/зі", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 3
**Previous module:** Dative Verbs

**Cumulative vocabulary (35 words):**
мені, тобі, йому, їй, нам, вам, їм, подобатися, допомагати, дзвонити
здаватися, потрібно, треба, необхідно, цікаво, нудно, весело, сумно, важко, легко
приємно, боляче, холодно, жарко, гарно, називний, займенник, прикметник, давальний, іменник
давати, дякувати, поріг, знахідний, множина

**Grammar already taught (14 topics):**
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

**Coming next (module after this):** instrumental of means, instrumental without prepositions, transport
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 25 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- з / із / зі (with) — Top 10 preposition; used for accompaniment (спільність дії); зі used before clusters like ст-, зв-
- разом (together) — high-frequency: працювати разом, жити разом
- разом з (together with) — mandatory collocation for social interactions
- зустрічатися (to meet/to date) — collocation: зустрічатися з друзями, зустрічатися біля метро
- розмовляти (to talk) — collocation: розмовляти з мамою, розмовляти з колегою
- гуляти (to walk/hang out) — high-frequency: гуляти з собакою, гуляти парком
- спілкуватися (to communicate) — State Standard §4.2.2.5.2 alignment; high frequency in A2
- познайомитися (to get acquainted) — collocation: познайомитися з новою подругою
- одружитися (to get married) — usage note: always used with 'з' for accompaniment
- подружитися (to become friends) — transition from acquaintance to friendship
- друг (friend) — cultural note: signifies a very close, trusted bond
- приятель (pal/buddy) — casual friendship, less intense than 'друг'
- знайомий (acquaintance) — formal or casual person one knows but is not close to

**Recommended** (use in your content to reach the vocabulary target):
- хліб-сіль (bread and salt) — cultural symbol of hospitality and sharing
- помиритися (to make up) — collocation: помиритися з братом
- посваритися (to quarrel) — opposite of accompaniment; used with 'з'
- товаришувати (to be friends) — professional or long-term friendship verb
- сусідити (to be neighbors) — shared space accompaniment

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

Write **The Instrumental I — Accompaniment** for the a2 track.

**Targets:** 2000–3000 words | 4+ callout boxes | **10–15 activities total** (required types + additional types to reach minimum) | 25 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ: Орудний відмінок та спільність дії (Introduction: The Instrumental Case and Joint Action)` (~325 words)
  - Introduction to the seventh case (орудний відмінок) and its alignment with Ukrainian State Standard §4.2.2.5.2, focusing specifically on 'спільність дії' (joint action/accompaniment).
  - The primary questions of the case: ким? (with whom?) and чим? (with what?) in the context of people and things.
  - Cultural Hook: 'Bread and Salt' (Хліб-сіль). Detailed explanation of welcoming guests 'з хлібом-сіллю' where bread symbolizes wealth/prosperity and salt symbolizes protection from evil, establishing a sacred bond of friendship.
- `## Презентація: Закінчення та правила евфонії (Presentation: Endings and Euphony Rules)` (~575 words)
  - Paradigm of Instrumental endings for nouns across all genders, emphasizing the transition from A1 Nominative forms to A2 Case forms.
  - Learner Error: Nominative Overuse. Drill specifically on avoiding errors like 'Я йду з друг' instead of the correct 'Я йду з другом'.
  - The Euphony Rule (з/із/зі): Detailed breakdown of choosing the variant based on vocal flow. 'Зі' is mandatory before consonant clusters like 'ст-', 'зв-', 'шк-' (e.g., зі студентами, зі мною).
  - Learner Error: Euphony default. Correcting the tendency to use 'з' everywhere (e.g., 'з студентом' vs. correct 'зі студентом').
- `## Дієслова спілкування та прийменник 'З' (Social Verbs and the Preposition 'З')` (~500 words)
  - Focus on high-frequency social verbs: розмовляти (to talk), гуляти (to walk), зустрічатися (to meet), спілкуватися (to communicate).
  - Crucial Distinction: Meaning changes with and without the preposition. 'Розмовляти телефоном' (using phone as means) vs. 'Розмовляти з колегою' (accompaniment with a person).
  - Learner Error: Missing Preposition 'з'. Drill on the semantic error 'Я розмовляю мамою' (implies using mother as a tool) vs. the correct 'Я розмовляю з мамою'.
- `## Практика: Разом та ієрархія дружби (Practice: 'Together' and Friendship Hierarchy)` (~375 words)
  - Usage of the high-frequency collocation 'разом з' (together with) in social contexts like 'жити разом', 'працювати разом з нами'.
  - Cultural Linguistic Nuance: The Friendship Hierarchy. Distinguishing between 'знайомий' (acquaintance), 'приятель' (buddy/pal - casual), and 'друг' (close, trusted friend). Explain why 'друг' is a serious title not given lightly in Ukrainian culture.
  - Sentence formation practice focusing on everyday collocations: 'зустрічатися біля метро', 'гуляти з собакою'.
- `## Займенники в орудному (Pronouns in Instrumental)` (~150 words)
  - Personal pronoun instrumental forms: мною, тобою, ним, нею, нами, вами, ними. з мною, з тобою, з ним, з нею, з нами, з вами, з ними.
  - After prepositions, 3rd person adds н-: з ним → з ним (already has н in ним). But note: без нього (Gen) vs з ним (Instr) — different base forms.
  - Required by State Standard §4.2.1.4 (A2 level).
- `## Діалоги та підсумок (Dialogues and Summary)` (~150 words)
  - Social interaction scenarios: planning a meeting, introducing a friend ('познайомитися з...'), and discussing household life ('жити разом з...').
  - Review of 'з/із/зі' top 10 preposition status and summary of the joint action (спільність дії) function.
  - Checklist for learners: (1) Did I use 'з'? (2) Is the ending correct? (3) Is the euphony variant ('зі') needed?

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ: Орудний відмінок та спільність дії (Introduction: The Instrumental Case and Joint Action) | 325+ |
| Презентація: Закінчення та правила евфонії (Presentation: Endings and Euphony Rules) | 575+ |
| Дієслова спілкування та прийменник 'З' (Social Verbs and the Preposition 'З') | 500+ |
| Практика: Разом та ієрархія дружби (Practice: 'Together' and Friendship Hierarchy) | 375+ |
| Займенники в орудному (Pronouns in Instrumental) | 150+ |
| Діалоги та підсумок (Dialogues and Summary) | 150+ |
| **Total** | **2000+ (aim for ~2400)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("instrumental endings preposition з/із/зі", grade=3-5)` — find how textbooks teach this
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
**Required types:** fill-in, match-up, fill-in, quiz, fill-in

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

</prompt>

## The Plan

<plan>
module: a2-004
level: A2
sequence: 4
slug: the-instrumental-i-accompaniment
version: '2.0'
title: The Instrumental I — Accompaniment
subtitle: With Whom? Using 'З'
focus: grammar
pedagogy: PPP
phase: A2.1
word_target: 2000
objectives:
- Learner can form instrumental case endings for nouns
- Learner can use the preposition з (with) correctly
- Learner can describe doing things together with others
- Learner can use proper euphony rules for з/із/зі
sources:
- name: Ukrainian State Standard 2024 - Instrumental Case
  url: https://mon.gov.ua/
  type: reference
  notes: Instrumental endings and з/із/зі usage rules
- name: Ukrainian Grammar Reference
  url: https://uk.wikipedia.org/wiki/Орудний_відмінок
  type: reference
  notes: Complete instrumental paradigm
content_outline:
- section: 'Вступ: Орудний відмінок та спільність дії (Introduction: The Instrumental Case and Joint Action)'
  words: 325
  points:
  - Introduction to the seventh case (орудний відмінок) and its alignment with Ukrainian State Standard §4.2.2.5.2, focusing
    specifically on 'спільність дії' (joint action/accompaniment).
  - 'The primary questions of the case: ким? (with whom?) and чим? (with what?) in the context of people and things.'
  - 'Cultural Hook: ''Bread and Salt'' (Хліб-сіль). Detailed explanation of welcoming guests ''з хлібом-сіллю'' where bread
    symbolizes wealth/prosperity and salt symbolizes protection from evil, establishing a sacred bond of friendship.'
- section: 'Презентація: Закінчення та правила евфонії (Presentation: Endings and Euphony Rules)'
  words: 575
  points:
  - Paradigm of Instrumental endings for nouns across all genders, emphasizing the transition from A1 Nominative forms to
    A2 Case forms.
  - 'Learner Error: Nominative Overuse. Drill specifically on avoiding errors like ''Я йду з друг'' instead of the correct
    ''Я йду з другом''.'
  - 'The Euphony Rule (з/із/зі): Detailed breakdown of choosing the variant based on vocal flow. ''Зі'' is mandatory before
    consonant clusters like ''ст-'', ''зв-'', ''шк-'' (e.g., зі студентами, зі мною).'
  - 'Learner Error: Euphony default. Correcting the tendency to use ''з'' everywhere (e.g., ''з студентом'' vs. correct ''зі
    студентом'').'
- section: Дієслова спілкування та прийменник 'З' (Social Verbs and the Preposition 'З')
  words: 500
  points:
  - 'Focus on high-frequency social verbs: розмовляти (to talk), гуляти (to walk), зустрічатися (to meet), спілкуватися (to
    communicate).'
  - 'Crucial Distinction: Meaning changes with and without the preposition. ''Розмовляти телефоном'' (using phone as means)
    vs. ''Розмовляти з колегою'' (accompaniment with a person).'
  - 'Learner Error: Missing Preposition ''з''. Drill on the semantic error ''Я розмовляю мамою'' (implies using mother as
    a tool) vs. the correct ''Я розмовляю з мамою''.'
- section: 'Практика: Разом та ієрархія дружби (Practice: ''Together'' and Friendship Hierarchy)'
  words: 375
  points:
  - Usage of the high-frequency collocation 'разом з' (together with) in social contexts like 'жити разом', 'працювати разом
    з нами'.
  - 'Cultural Linguistic Nuance: The Friendship Hierarchy. Distinguishing between ''знайомий'' (acquaintance), ''приятель''
    (buddy/pal - casual), and ''друг'' (close, trusted friend). Explain why ''друг'' is a serious title not given lightly
    in Ukrainian culture.'
  - 'Sentence formation practice focusing on everyday collocations: ''зустрічатися біля метро'', ''гуляти з собакою''.'
- section: "Займенники в орудному (Pronouns in Instrumental)"
  words: 150
  points:
  - "Personal pronoun instrumental forms: мною, тобою, ним, нею, нами, вами, ними.
    з мною, з тобою, з ним, з нею, з нами, з вами, з ними."
  - "After prepositions, 3rd person adds н-: з ним → з ним (already has н in ним).
    But note: без нього (Gen) vs з ним (Instr) — different base forms."
  - "Required by State Standard §4.2.1.4 (A2 level)."
- section: Діалоги та підсумок (Dialogues and Summary)
  words: 150
  points:
  - 'Social interaction scenarios: planning a meeting, introducing a friend (''познайомитися з...''), and discussing household
    life (''жити разом з...'').'
  - Review of 'з/із/зі' top 10 preposition status and summary of the joint action (спільність дії) function.
  - 'Checklist for learners: (1) Did I use ''з''? (2) Is the ending correct? (3) Is the euphony variant (''зі'') needed?'
vocabulary_hints:
  required:
  - з / із / зі (with) — Top 10 preposition; used for accompaniment (спільність дії); зі used before clusters like ст-, зв-
  - 'разом (together) — high-frequency: працювати разом, жити разом'
  - разом з (together with) — mandatory collocation for social interactions
  - 'зустрічатися (to meet/to date) — collocation: зустрічатися з друзями, зустрічатися біля метро'
  - 'розмовляти (to talk) — collocation: розмовляти з мамою, розмовляти з колегою'
  - 'гуляти (to walk/hang out) — high-frequency: гуляти з собакою, гуляти парком'
  - спілкуватися (to communicate) — State Standard §4.2.2.5.2 alignment; high frequency in A2
  - 'познайомитися (to get acquainted) — collocation: познайомитися з новою подругою'
  - 'одружитися (to get married) — usage note: always used with ''з'' for accompaniment'
  - подружитися (to become friends) — transition from acquaintance to friendship
  - 'друг (friend) — cultural note: signifies a very close, trusted bond'
  - приятель (pal/buddy) — casual friendship, less intense than 'друг'
  - знайомий (acquaintance) — formal or casual person one knows but is not close to
  recommended:
  - хліб-сіль (bread and salt) — cultural symbol of hospitality and sharing
  - 'помиритися (to make up) — collocation: помиритися з братом'
  - посваритися (to quarrel) — opposite of accompaniment; used with 'з'
  - товаришувати (to be friends) — professional or long-term friendship verb
  - сусідити (to be neighbors) — shared space accompaniment
activity_hints:
- type: fill-in
  focus: Add instrumental endings to nouns
  items: 15+
- type: match-up
  focus: Person + з + instrumental form
  items: 12+
- type: fill-in
  focus: Combine two people doing something together
  items: 10+
- type: quiz
  focus: Choose correct instrumental ending
  items: 12+
- type: fill-in
  focus: Complete social verb sentences
  items: 10+
connects_to:
- a2-05 (Instrumental II - Means & Tools)
- a2-06 (Being and Becoming)
- a2-07 (Spatial Prepositions)
prerequisites:
- a2-02 (Dative noun endings)
- A1 noun gender
- A1 prepositions basics
persona:
  voice: Encouraging Cultural Guide
  role: Wedding Starosta
grammar:
- instrumental endings
- preposition з/із/зі
- accompaniment
- social interaction
module_type: grammar
immersion: 50-60% Ukrainian
register: розмовний

</plan>

## Audit Gates

## Audit Gates (your content will be checked against these)

Level: A2
Word target: 2000
Word ceiling: ~3000 (exceeding = FAIL)
Min activities: 10
Min engagement boxes: 4
Min activity types: 4

### Immersion
Target range: defined in the prompt's Immersion Target section (varies by module).
Tables count ZERO for immersion — only blockquotes, bulleted lists, and pattern boxes count.

### Grammar constraints
Max words per Ukrainian sentence: 15
Participles allowed: False
Max clauses: 2

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