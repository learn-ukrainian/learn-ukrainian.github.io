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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/research/dative-verbs-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a2/dative-verbs.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A2.md` | Level constraints, immersion band |
| `schemas/activities-a2.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("verbs + dative verbs + dative + accusative", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 2
**Previous module:** The Dative II — Nouns

**Cumulative vocabulary (35 words):**
мені, тобі, йому, їй, нам, вам, їм, подобатися, допомагати, дзвонити
здаватися, потрібно, треба, необхідно, цікаво, нудно, весело, сумно, важко, легко
приємно, боляче, холодно, жарко, гарно, називний, займенник, прикметник, давальний, іменник
давати, дякувати, поріг, знахідний, множина

**Grammar already taught (10 topics):**
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

**Coming next (module after this):** instrumental endings, preposition з/із/зі, accompaniment
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 25 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- допомагати (to help) — High frequency (Top 500); допомагати по господарству, допомагати армії/переселенцям, взаємно допомагати
- дякувати (to thank) — Very high frequency (Top 100); щиро дякувати, красно дякувати, дякувати Богу; наперед дякую
- подобатися (to please/like) — Very high frequency (Top 200); мені дуже подобається, страшенно подобатися; fix 'я подобаю це' error
- вірити (to believe) — вірити на слово; вірити людині (Dat) vs. вірити в Бога (Acc)
- довіряти (to trust) — сліпо довіряти, довіряти людям, не довіряти нікому
- заважати (to bother) — вибачте, що заважаю; не заважай мені!; нікому не заважати
- вибачати (to forgive) — вибачати (комусь) (щось); вибачте мені; вибачте за запізнення
- пробачати (to excuse) — пробачте мені; пробачте за запізнення
- заздрити (to envy) — заздрити успіху; біла заздрість (clean/noble envy)
- симпатизувати (to sympathize) — симпатизувати колезі (Dat)
- співчувати (to empathize) — щиро співчувати горю/людині
- личити (to suit) — тобі личить ця сукня; це тобі не личить (behavioral)
- підходити (to suit/fit) — цей час мені підходить; це мені не підходить
- вистачати (to be enough) — мені вистачає грошей; мені вистачає часу
- бракувати (to lack) — мені бракує терпіння; мені бракує слів

**Recommended** (use in your content to reach the vocabulary target):
- шкодити (to harm) — це шкодить здоров'ю; паління шкодить
- служити (to serve) — служити народу; служити в армії (Loc) vs. служити ідеї (Dat)
- належати (to belong) — це належить мені; книга належить студентові
- сподобатися (to come to like - pf) — мені сподобався фільм; мені сподобалася ідея
- захотітися (to feel like - pf) — мені захотілося кави; мені захотілося спати

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

Write **Dative Verbs** for the a2 track.

**Targets:** 2000–3000 words | 4+ callout boxes | **10–15 activities total** (required types + additional types to reach minimum) | 25 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ (Introduction)` (~300 words)
  - Introduction to the concept of verb government (керування) where verbs act as case-drivers, specifically focusing on the Dative case as the marker for recipient or beneficiary (State Standard §4.2.2.3).
  - Contrastive mapping of the 'invisible to' preposition: Comparing English direct objects (thank YOU) vs. Ukrainian indirect objects (give thanks TO YOU) to prevent the calque error «Дякую тебе» (Acc).
- `## Теорія та Презентація (Theory & Presentation)` (~500 words)
  - Classification of dative-hungry verbs: purely dative verbs (допомагати, дякувати, вірити) vs. double-object verbs (давати, повідомляти - Dat + Acc); use State Standard example: «Повідомити групі про зміни в розкладі».
  - Addressing the 'I Like' Trap: Deconstructing the impersonal usage of «подобатися» (to please) to correct the subject/object flip mismatch (Standard English 'I like it' vs. Ukrainian 'It pleases me').
- `## Культурний контекст та Волонтерство (Cultural Context & Volunteering)` (~500 words)
  - Volunteering (волонтерство) as a modern social pillar: Using 'допомагати' in the context of aiding the army and displaced persons; establishing 'допомога' as a civic duty rather than just politeness.
  - Historical anchor: The 'Толока' (Toloka) custom of communal labor; explaining reciprocity through the lens of ancient mutual aid traditions and the phrase «взаємно допомагати».
  - Sincerity markers and gestures: Mentioning the 'hand on heart' gesture that accompanies expressions of gratitude (дякую) or belief (вірю) to signal deep authenticity.
- `## Практика та Аналіз помилок (Practice & Error Analysis)` (~425 words)
  - Error correction drill: Systematic remediation of the 'Thank You' trap (fixing «Дякую тебе» to «Дякую тобі») and reinforcement of masculine -ові/-еві endings for persons (e.g., «допомагаю братові»).
  - Collocation building: Practicing high-frequency pairings from research frequency data: «щиро/красно дякувати», «наперед дякую», «сліпо довіряти», «допомагати по господарству».
- `## Діалоги та Підсумок (Dialogues & Summary)` (~275 words)
  - Contextual dialogues: Reciprocal aid scenario in a volunteer center using the pattern «Ти допоміг мені? Я допоможу тобі» to demonstrate the flow of dative relations.
  - Summary of gratitude registers: Moving from basic 'Дякую' to the more sophisticated and culturally resonant 'Красно дякую' and 'Щиро співчуваю' for A2 interpersonal competency.

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ (Introduction) | 300+ |
| Теорія та Презентація (Theory & Presentation) | 500+ |
| Культурний контекст та Волонтерство (Cultural Context & Volunteering) | 500+ |
| Практика та Аналіз помилок (Practice & Error Analysis) | 425+ |
| Діалоги та Підсумок (Dialogues & Summary) | 275+ |
| **Total** | **2000+ (aim for ~2400)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("verbs + dative verbs + dative + accusative", grade=3-5)` — find how textbooks teach this
2. **Write content** following the outline and lesson arc below
3. **Verify as you write**: `verify_words` on any Ukrainian word you're unsure about
4. **Create activities** from your content
5. **Verify activities**: batch `verify_words` on all activity items

### Beginner Lesson Arc

1. **WELCOME** — warm greeting, set context
2. **PREVIEW** — "By the end of this module, you'll be able to..."
3. **PRESENT** — the main content sections
4. **PRACTICE** — examples, dialogues, reading practice
5. **CELEBRATE** — in the final `## Діалоги та Підсумок (Dialogues & Summary)` section, tell learners what they can now do

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
**Required types:** fill-in, quiz, quiz, match-up, fill-in

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
- **MUST end with `## Діалоги та Підсумок (Dialogues & Summary)`** with self-check questions

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
module: a2-003
level: A2
sequence: 3
slug: dative-verbs
version: '2.0'
title: Dative Verbs
subtitle: Verbs That Demand the Dative Case
focus: grammar
pedagogy: PPP
phase: A2.1
word_target: 2000
objectives:
- Learner can use common verbs that require the dative case
- Learner can distinguish between verbs taking dative vs accusative
- Learner can construct sentences with indirect objects
- Learner can use verbs of communication and interaction correctly
sources:
- name: Ukrainian State Standard 2024 - Verb Government
  url: https://mon.gov.ua/
  type: reference
  notes: List of verbs requiring dative case per A2 level
- name: Ukrainian Verb Government Reference
  url: https://uk.wiktionary.org/
  type: reference
  notes: Case requirements for common verbs
content_outline:
- section: Вступ (Introduction)
  words: 300
  points:
  - Introduction to the concept of verb government (керування) where verbs act as case-drivers, specifically focusing on the
    Dative case as the marker for recipient or beneficiary (State Standard §4.2.2.3).
  - 'Contrastive mapping of the ''invisible to'' preposition: Comparing English direct objects (thank YOU) vs. Ukrainian indirect
    objects (give thanks TO YOU) to prevent the calque error «Дякую тебе» (Acc).'
- section: Теорія та Презентація (Theory & Presentation)
  words: 500
  points:
  - 'Classification of dative-hungry verbs: purely dative verbs (допомагати, дякувати, вірити) vs. double-object verbs (давати,
    повідомляти - Dat + Acc); use State Standard example: «Повідомити групі про зміни в розкладі».'
  - 'Addressing the ''I Like'' Trap: Deconstructing the impersonal usage of «подобатися» (to please) to correct the subject/object
    flip mismatch (Standard English ''I like it'' vs. Ukrainian ''It pleases me'').'
- section: Культурний контекст та Волонтерство (Cultural Context & Volunteering)
  words: 500
  points:
  - 'Volunteering (волонтерство) as a modern social pillar: Using ''допомагати'' in the context of aiding the army and displaced
    persons; establishing ''допомога'' as a civic duty rather than just politeness.'
  - 'Historical anchor: The ''Толока'' (Toloka) custom of communal labor; explaining reciprocity through the lens of ancient
    mutual aid traditions and the phrase «взаємно допомагати».'
  - 'Sincerity markers and gestures: Mentioning the ''hand on heart'' gesture that accompanies expressions of gratitude (дякую)
    or belief (вірю) to signal deep authenticity.'
- section: Практика та Аналіз помилок (Practice & Error Analysis)
  words: 425
  points:
  - 'Error correction drill: Systematic remediation of the ''Thank You'' trap (fixing «Дякую тебе» to «Дякую тобі») and reinforcement
    of masculine -ові/-еві endings for persons (e.g., «допомагаю братові»).'
  - 'Collocation building: Practicing high-frequency pairings from research frequency data: «щиро/красно дякувати», «наперед
    дякую», «сліпо довіряти», «допомагати по господарству».'
- section: Діалоги та Підсумок (Dialogues & Summary)
  words: 275
  points:
  - 'Contextual dialogues: Reciprocal aid scenario in a volunteer center using the pattern «Ти допоміг мені? Я допоможу тобі»
    to demonstrate the flow of dative relations.'
  - 'Summary of gratitude registers: Moving from basic ''Дякую'' to the more sophisticated and culturally resonant ''Красно
    дякую'' and ''Щиро співчуваю'' for A2 interpersonal competency.'
vocabulary_hints:
  required:
  - допомагати (to help) — High frequency (Top 500); допомагати по господарству, допомагати армії/переселенцям, взаємно допомагати
  - дякувати (to thank) — Very high frequency (Top 100); щиро дякувати, красно дякувати, дякувати Богу; наперед дякую
  - подобатися (to please/like) — Very high frequency (Top 200); мені дуже подобається, страшенно подобатися; fix 'я подобаю
    це' error
  - вірити (to believe) — вірити на слово; вірити людині (Dat) vs. вірити в Бога (Acc)
  - довіряти (to trust) — сліпо довіряти, довіряти людям, не довіряти нікому
  - заважати (to bother) — вибачте, що заважаю; не заважай мені!; нікому не заважати
  - вибачати (to forgive) — вибачати (комусь) (щось); вибачте мені; вибачте за запізнення
  - пробачати (to excuse) — пробачте мені; пробачте за запізнення
  - заздрити (to envy) — заздрити успіху; біла заздрість (clean/noble envy)
  - симпатизувати (to sympathize) — симпатизувати колезі (Dat)
  - співчувати (to empathize) — щиро співчувати горю/людині
  - личити (to suit) — тобі личить ця сукня; це тобі не личить (behavioral)
  - підходити (to suit/fit) — цей час мені підходить; це мені не підходить
  - вистачати (to be enough) — мені вистачає грошей; мені вистачає часу
  - бракувати (to lack) — мені бракує терпіння; мені бракує слів
  recommended:
  - шкодити (to harm) — це шкодить здоров'ю; паління шкодить
  - служити (to serve) — служити народу; служити в армії (Loc) vs. служити ідеї (Dat)
  - належати (to belong) — це належить мені; книга належить студентові
  - сподобатися (to come to like - pf) — мені сподобався фільм; мені сподобалася ідея
  - захотітися (to feel like - pf) — мені захотілося кави; мені захотілося спати
activity_hints:
- type: fill-in
  focus: Complete sentences with dative verbs
  items: 12+
- type: quiz
  focus: Add dative object to sentences
  items: 10+
- type: quiz
  focus: Which verbs require dative?
  items: 12+
- type: match-up
  focus: Verb + appropriate case pattern
  items: 10+
- type: fill-in
  focus: Dative vs accusative object selection
  items: 10+
connects_to:
- a2-04 (Instrumental I)
- a2-11 (All Cases Practice)
- a2-11 (Checkpoint - Cases)
prerequisites:
- a2-01 (Dative pronouns)
- a2-02 (Dative nouns)
- A1 verb conjugation
persona:
  voice: Encouraging Cultural Guide
  role: Volunteer Coordinator
grammar:
- verbs + dative
- verbs + dative + accusative
- indirect objects
- verb government
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