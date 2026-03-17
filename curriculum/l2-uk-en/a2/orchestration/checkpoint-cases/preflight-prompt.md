You are about to build a module using the prompt below. Before you start, verify the prompt is ready.

**Default answer: PASS.** Only report genuine issues that would cause audit gate failures or introduce errors.

## The Prompt

<prompt>
# Beginner Checkpoint: Synthesis & Review

> **Persona reminder:** You are Patient & Supportive Ukrainian Tutor. Write in the voice of Encouraging Cultural Guide.

> **Your task: Write approximately 2000 words that REVIEW and SYNTHESIZE prior material — NOT teach new concepts.**
> Write clear, practical prose. Every H3 gets {H3_WORD_RANGE} words. Focus on examples and usage patterns. Avoid unnecessary theory or padding.

> **Output capacity: You can generate 65,000+ tokens per response.** Do NOT preemptively truncate.

## CHECKPOINT IDENTITY — READ THIS FIRST

**This is a CHECKPOINT module.** Checkpoints are fundamentally different from teaching modules:

| Teaching Module | Checkpoint Module |
|----------------|-------------------|
| Introduces new grammar/vocabulary | Reviews grammar/vocabulary from prior modules |
| Explains concepts for the first time | Creates new CONTEXTS that combine prior concepts |
| Learning objectives | Synthesis objectives |
| "Here's how it works" | "Show me you can use it" |
| Feels like a lecture | Feels like a celebration of progress |

**The golden rule: If the learner hasn't seen it in a prior module, it does NOT belong here.**

### What Checkpoints Do

1. **Reuse ALL vocabulary and grammar from the preceding block** — no new teaching
2. **Create new contexts** that force combining multiple skills learned separately
3. **Feel like a reward/celebration**, not a test — the learner should feel proud of how far they've come
4. **Synthesis over explanation** — show how pieces fit together, don't re-explain them
5. **Self-assessment** — help learners identify gaps before moving forward

### What Checkpoints Do NOT Do

- Introduce new grammar rules or patterns
- Teach new vocabulary (only reuse from prior modules)
- Explain concepts in detail (brief reminders only, not full explanations)
- Present theory-heavy sections

---

## Files to Read

| File | Purpose |
|------|---------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/research/checkpoint-cases-research.md` | Research notes |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a2/checkpoint-cases.yaml` | Content outline, section word allocations, vocabulary_hints |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A2.md` | Level constraints, immersion % |

Read ALL files before writing.

## Resource Discoveries





## Module Constraints (HARD FAIL if violated)





**Target vocabulary** (from the plan — these are REVIEW words from prior modules, not new vocabulary):

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- відмінок (case) — Nominative to Vocative (7 cases); review of the full system.
- давальний (dative) — Recipients & Experiencers; focus on age and feelings.
- орудний (instrumental) — Tools & Companions; focus on profession/status.
- прийменник (preposition) — Critical for case governance; major focus on matching.
- допомагати (to help) — High frequency (Dative); collocations: допомагати мамі/другові, допомагати з роботою.
- подобатися (to like) — High frequency (Dative); collocations: мені подобається це місто, подобатися вчителю.
- з (із/зі) (with/from) — Very High frequency (Inst/Gen); collocations: кава з молоком, розмовляти з другом, приїхати з Києва.
- для (for) — Genitive preposition; high frequency in service contexts.
- без (without) — Genitive preposition; essential for negation and exclusion.
- через (because of/through) — High frequency (Acc); collocations: через дорогу (motion), через дощ (reason), через тиждень (time).
- після (after) — Genitive preposition; frequency in scheduling and dates.
- пошта (post office) — Medium (Services); collocations: на пошті, відправити поштою, відділення пошти.
- рахунок (account) — Medium (Bank); collocations: відкрити рахунок, гроші на рахунку, номер рахунку.
- відправляти (to send) — Post context; typically takes Accusative direct object.
- обмінювати (to exchange) — Bank context; essential for currency exchange tasks.

**Recommended** (use in your content to reach the vocabulary target):
- правильно (correctly) — Self-correction and assessment context.
- помилка (mistake) — Focus on identifying and correcting learner errors.
- виправити (to correct) — Action-oriented verb for error correction tasks.
- перевірити (to check) — Self-assessment and verification context.
- оцінка (assessment) — Progress tracking and goal setting.

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

**Rules:**
- Every word listed above was taught in a prior module. Use them in NEW combinations and contexts.
- Do NOT explain these words as if seeing them for the first time — the learner already knows them.
- Create fresh example sentences that combine vocabulary from different prior modules.
- Match the syntactic complexity of the prior modules — do not escalate difficulty.



---

## Writing Instructions

Write the checkpoint content for **Checkpoint — Cases** (a2 track).

- **Target**: 2000–3000 words (below 2000 = FAIL)
- **Engagement callouts**: **4+ MANDATORY** — spread across sections, at least 3 different types
- **Structure**: Use the EXACT H2 section titles listed below. Missing or renamed sections fail validation.

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Огляд та самооцінка (Overview and Self-assessment)` (~267 words)
  - Checkpoint goals and alignment with Ukrainian State Standard §4.2.2 (Linguistic competence: morphology, Catalogue C); emphasis on systematic review of all 7 cases.
  - Comprehensive self-assessment checklist based on CEFR A2 descriptors; must include a 'Preposition + Case' matching section as identified in research as a primary friction point.
- `## Відмінки в дії: Давальний та Орудний (Cases in Action: Dative and Instrumental)` (~467 words)
  - Dative case review (Standard §4.2.2.3): Emphasize recipients (Подарувати книжку студентові), age (Дідусеві вісімдесят років), and expressions of feeling (мені холодно/цікаво).
  - Instrumental case review (Standard §4.2.2.5): Focus on profession/status (бути програмувальником) and instruments (пише ручкою).
  - Targeted drill for learner error: Nom. for Instruments (e.g., correcting 'Я пишу ручка' to 'Я пишу ручкою') to ensure mastery of case endings for tools.
- `## Граматичні тонкощі: Родовий, Знахідний та Кличний (Grammar Nuances: Genitive, Accusative, and Vocative)` (~467 words)
  - Genitive case functions (Standard §4.2.2.2): Practice with time/date (десятого березня), prepositions (з, до, для, біля), and mandatory case change under negation.
  - Correction of learner error 'Nom. after Negation': Drill minimal pairs (e.g., correcting 'У мене немає гроші' to 'У мене немає грошей').
  - Accusative vs. Locative for Motion and Location (Standard §4.2.2.4/§4.2.2.6): Mastering prepositions в/у, на and the path-oriented 'по'.
  - Vocative case mastery: Addressing learner error 'Nom. instead of Voc.' (e.g., correcting 'Сергій, привіт!' to 'Сергію, привіт!') to build natural conversational habits.
- `## Сервіси та цифрова Україна (Services and Digital Ukraine)` (~467 words)
  - Practical mixed-case dialogues in service environments: Post office and Banking (Standard Catalogue B).
  - Vocabulary integration: 'відправити поштою', 'рахунок у банку', 'допомагати з роботою' using high-frequency verbs 'допомагати' and 'відправляти'.
  - Cultural Hook — Digital Banking Leadership: Exploring Ukraine's role as a global leader via Monobank and the 'Diia' app; practicing case usage while discussing modern tech ecosystems.
- `## Історичний виклик та підсумок (Historical Challenge and Summary)` (~332 words)
  - Integration Challenge: Mixed case narrative analysis based on the cultural hook 'Stamps as Currency (1918)'; how the UNR issued stamps that circulated equally with coins.
  - Final summary of case governance and prepositional matching; preparing the learner for a2-12 (Aspect Introduction) where case endings remain constant regardless of verb aspect.

### Checkpoint Writing Style

**Tone: Celebratory and encouraging.** The learner has completed a block of lessons. This is a victory lap, not an exam.

- Open with acknowledgment of progress: "You've learned X, Y, and Z — now let's see how they work together!"
- Use warm, encouraging language throughout
- Frame challenges as "puzzles" or "adventures", not "tests"
- End with a clear signal of readiness for the next phase

**Structure each skill-review section as:**
1. **Brief reminder** (1-2 sentences max) of what the skill is — NOT a full re-explanation
2. **New context** that exercises the skill — a scenario, dialogue, or situation the learner hasn't seen
3. **Integration challenge** that combines this skill with others from the same block
4. **Reinforcement callout** (tip, culture note, or encouragement)

**Integration sections must:**
- Combine 2+ skills from different prior modules in a single task
- Use a realistic scenario (ordering food, describing a room, introducing family)
- Show how grammar and vocabulary work together in natural speech

### Immersion Target

TARGET: 45-65% Ukrainian.
LANGUAGE ROLES:
- THEORY: English prose for grammar explanations that would be too complex in Ukrainian at this level.
- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, cultural context.
- HEADERS: Ukrainian with English in parentheses.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix languages within a sentence. Ukrainian paragraphs and dialogues carry most content. English appears for grammar theory and in callout boxes.
A2 register ONLY. Concrete everyday vocabulary. No literary/poetic language. No abstract nouns. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles.

### Structural Containment (how to achieve immersion without code-switching)

**Three rules govern where each language appears:**

1. **Paragraphs = English** with Ukrainian vocabulary **bolded inline**: "Remember **книга** (book)? Now combine it with the adjective **нова** to get **нова книга**."

2. **Full Ukrainian sentences = prefer structural containers.** Ukrainian sentences (3+ words with a verb) work best in containers, but short inline Ukrainian is fine in explanatory context (e.g., "Remember how **Це нова книга** uses the adjective before the noun?"):
   - **Tables** — paradigms, vocabulary groups, gender sorting (tables count ZERO for immersion — use for structure/explanation only)
   - **Bulleted example lists** — Ukrainian line + English gloss: `- **Читай книгу!** — Read the book!`
   - **Blockquote dialogues** — mini-conversations with labeled speakers
   - **Pattern boxes** — transformations: `читати → читай → читайте`

3. **Vary containers.** Never use the same container type twice in a row.

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Огляд та самооцінка (Overview and Self-assessment) | 267+ |
| Відмінки в дії: Давальний та Орудний (Cases in Action: Dative and Instrumental) | 467+ |
| Граматичні тонкощі: Родовий, Знахідний та Кличний (Grammar Nuances: Genitive, Accusative, and Vocative) | 467+ |
| Сервіси та цифрова Україна (Services and Digital Ukraine) | 467+ |
| Історичний виклик та підсумок (Historical Challenge and Summary) | 332+ |
| **Total** | **2000+ (aim for ~2400)** |

### Callout Types to Use

- `[!tip]` — practical reminders for learners
- `[!warning]` — common mistakes to watch for (review traps)
- `[!did-you-know]` — fun facts about Ukrainian
- `[!culture]` — cultural connections that make the language come alive

### Audit Gates (your content will be checked for)

- **Word count**: minimum 2000 words
- **Russianisms**: banned (кушати, получати, etc.)
- **Russian characters**: ы, э, ё, ъ must NEVER appear
- **Euphony**: і/й, у/в alternation
- **Engagement callouts**: 4+
- **IPA/phonetic brackets**: BANNED
- **New grammar/vocabulary**: BANNED — checkpoint reviews only

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


---

## Pre-Submission Checks

1. **Plan compliance**: Does every point in the content_outline have dedicated prose?
2. **Word count**: Does the total meet 2000?
3. **Language scan**: No Russianisms, no Russian characters, no IPA, no Latin transliteration?
4. **Decodable vocabulary**: Does every Ukrainian word use only the allowed letter set?
5. **Synthesis check**: Does every section COMBINE skills rather than re-teach them individually?
6. **No new material**: Have you avoided introducing any grammar or vocabulary not from prior modules?



---

## Output Format

```
===CONTENT_START===

<!-- SCOPE
Covers: Review and synthesis of {prior modules}
Not covered:
  - New grammar or vocabulary
  - {next phase topic} → {next-slug}
-->

# {Title}

> **Чому це важливо?**
>
> {2-3 celebratory sentences acknowledging progress}

## {Section 1}
...

---

# Історичний виклик та підсумок (Historical Challenge and Summary)

{Summary + 3-4 self-check questions. Each question MUST include an English translation if the question is in Ukrainian. Format: "Який? (Which?) — answer / відповідь"}

---

===CONTENT_END===
```

```
===WORD_COUNTS===
Section "{name}": {count} words (minimum: {allocation})
...
Total: {total} words (target: 2000)
===WORD_COUNTS===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Beginner Checkpoint Content
**Step**: {what you were doing}
**Friction Type**: NONE | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT generate activities or vocabulary tables (separate phase)
- Do NOT introduce new vocabulary or grammar not from prior modules
- **VOCABULARY COVERAGE RULE:** All words from `vocabulary_hints` in the plan MUST appear at least once in the module content.
- Do NOT skip sections from the content_outline
- Do NOT write fewer than 2000 words
- Do NOT use straight quotes "..." — always «...»
- Do NOT re-explain concepts in detail — brief reminders only, then synthesize

</prompt>

## The Plan

<plan>
module: a2-013
level: A2
sequence: 13
slug: checkpoint-cases
version: '2.0'
title: Checkpoint — Cases
subtitle: Review and Mastery
focus: checkpoint
pedagogy: TTT
phase: A2.1
word_target: 2000
objectives:
- Learner can correctly identify and use all 7 cases
- Learner can choose appropriate prepositions for each case
- Learner can correct common case errors
- Learner can apply case knowledge in mixed contexts
sources:
- name: Ukrainian State Standard 2024 - A2 Assessment
  url: https://mon.gov.ua/
  type: reference
  notes: Assessment criteria for case system mastery
- name: CEFR A2 Can-Do Statements
  url: https://www.coe.int/en/web/common-european-framework-reference-languages
  type: reference
  notes: A2 grammar proficiency requirements
content_outline:
- section: Огляд та самооцінка (Overview and Self-assessment)
  words: 267
  points:
  - 'Checkpoint goals and alignment with Ukrainian State Standard §4.2.2 (Linguistic
    competence: morphology, Catalogue C); emphasis on systematic review of all 7 cases.'
  - Comprehensive self-assessment checklist based on CEFR A2 descriptors; must include
    a 'Preposition + Case' matching section as identified in research as a primary
    friction point.
- section: 'Відмінки в дії: Давальний та Орудний (Cases in Action: Dative and Instrumental)'
  words: 467
  points:
  - 'Dative case review (Standard §4.2.2.3): Emphasize recipients (Подарувати книжку
    студентові), age (Дідусеві вісімдесят років), and expressions of feeling (мені
    холодно/цікаво).'
  - 'Instrumental case review (Standard §4.2.2.5): Focus on profession/status (бути
    програмувальником) and instruments (пише ручкою).'
  - 'Targeted drill for learner error: Nom. for Instruments (e.g., correcting ''Я
    пишу ручка'' to ''Я пишу ручкою'') to ensure mastery of case endings for tools.'
- section: 'Граматичні тонкощі: Родовий, Знахідний та Кличний (Grammar Nuances: Genitive,
    Accusative, and Vocative)'
  words: 467
  points:
  - 'Genitive case functions (Standard §4.2.2.2): Practice with time/date (десятого
    березня), prepositions (з, до, для, біля), and mandatory case change under negation.'
  - 'Correction of learner error ''Nom. after Negation'': Drill minimal pairs (e.g.,
    correcting ''У мене немає гроші'' to ''У мене немає грошей'').'
  - 'Accusative vs. Locative for Motion and Location (Standard §4.2.2.4/§4.2.2.6):
    Mastering prepositions в/у, на and the path-oriented ''по''.'
  - 'Vocative case mastery: Addressing learner error ''Nom. instead of Voc.'' (e.g.,
    correcting ''Сергій, привіт!'' to ''Сергію, привіт!'') to build natural conversational
    habits.'
- section: Сервіси та цифрова Україна (Services and Digital Ukraine)
  words: 467
  points:
  - 'Practical mixed-case dialogues in service environments: Post office and Banking
    (Standard Catalogue B).'
  - 'Vocabulary integration: ''відправити поштою'', ''рахунок у банку'', ''допомагати
    з роботою'' using high-frequency verbs ''допомагати'' and ''відправляти''.'
  - 'Cultural Hook — Digital Banking Leadership: Exploring Ukraine''s role as a global
    leader via Monobank and the ''Diia'' app; practicing case usage while discussing
    modern tech ecosystems.'
- section: Історичний виклик та підсумок (Historical Challenge and Summary)
  words: 332
  points:
  - 'Integration Challenge: Mixed case narrative analysis based on the cultural hook
    ''Stamps as Currency (1918)''; how the UNR issued stamps that circulated equally
    with coins.'
  - Final summary of case governance and prepositional matching; preparing the learner
    for a2-12 (Aspect Introduction) where case endings remain constant regardless
    of verb aspect.
vocabulary_hints:
  required:
  - відмінок (case) — Nominative to Vocative (7 cases); review of the full system.
  - давальний (dative) — Recipients & Experiencers; focus on age and feelings.
  - орудний (instrumental) — Tools & Companions; focus on profession/status.
  - прийменник (preposition) — Critical for case governance; major focus on matching.
  - 'допомагати (to help) — High frequency (Dative); collocations: допомагати мамі/другові,
    допомагати з роботою.'
  - 'подобатися (to like) — High frequency (Dative); collocations: мені подобається
    це місто, подобатися вчителю.'
  - 'з (із/зі) (with/from) — Very High frequency (Inst/Gen); collocations: кава з
    молоком, розмовляти з другом, приїхати з Києва.'
  - для (for) — Genitive preposition; high frequency in service contexts.
  - без (without) — Genitive preposition; essential for negation and exclusion.
  - 'через (because of/through) — High frequency (Acc); collocations: через дорогу
    (motion), через дощ (reason), через тиждень (time).'
  - після (after) — Genitive preposition; frequency in scheduling and dates.
  - 'пошта (post office) — Medium (Services); collocations: на пошті, відправити поштою,
    відділення пошти.'
  - 'рахунок (account) — Medium (Bank); collocations: відкрити рахунок, гроші на рахунку,
    номер рахунку.'
  - відправляти (to send) — Post context; typically takes Accusative direct object.
  - обмінювати (to exchange) — Bank context; essential for currency exchange tasks.
  recommended:
  - правильно (correctly) — Self-correction and assessment context.
  - помилка (mistake) — Focus on identifying and correcting learner errors.
  - виправити (to correct) — Action-oriented verb for error correction tasks.
  - перевірити (to check) — Self-assessment and verification context.
  - оцінка (assessment) — Progress tracking and goal setting.
activity_hints:
- type: quiz
  focus: Comprehensive case quiz - all 7 cases
  items: 20+
- type: fill-in
  focus: Sentence transformation - change case
  items: 15+
- type: quiz
  focus: Error identification and correction
  items: 12+
- type: match-up
  focus: Preposition + case + meaning
  items: 15+
- type: fill-in
  focus: Service interaction dialogues
  items: 10+
connects_to:
- a2-14 (Aspect Introduction)
- 'a2-30 (Checkpoint: Aspect, Comparison & Modality)'
- a2-35 (Checkpoint - Complex Ideas)
prerequisites:
- a2-01 through a2-10 (all A2.1 modules)
persona:
  voice: Encouraging Cultural Guide
  role: Manuscript Proofreader
grammar:
- case system review
- prepositions review
- case functions
- error correction
module_type: checkpoint
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