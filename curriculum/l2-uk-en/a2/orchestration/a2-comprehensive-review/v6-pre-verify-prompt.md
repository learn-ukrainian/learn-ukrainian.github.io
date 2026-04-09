<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 67: Повна картина (A2, A2.10 [Refinement and Graduation])

## Plan vocabulary to verify

- повторення (review, revision)
- граматика (grammar)
- відмінок (grammatical case)
- дієслово (verb)
- прикметник (adjective)
- займенник (pronoun)
- речення (sentence)
- помилка (error, mistake)
- впевненість (confidence)
- складний (complex, compound)
- сполучник (conjunction)

## Sections to research

- **Відмінки: від називного до кличного (Cases: From Nominative to Vocative)**: Systematic review of all seven cases: when each is used, key prepositions, and typical verb government. Quick reference chart with the most important triggers for each case.; Genitive and instrumental deep dive — the two cases learners confuse most at A2. Contrastive pairs: без + Gen vs з + Instr, preposition overlap.; Mixed exercise: sentences requiring the learner to choose the correct case based on context — verbs, prepositions, and constructions from across A2.
- **Дієслово: вид, час, спосіб (The Verb: Aspect, Tense, Mood)**: Review of aspect pairs and their usage in context. When to use imperfective (process, repetition, general) vs. perfective (result, completion, single event).; Tense review: past, present, future — including compound future (буду + infinitive) and synthetic future (-му). When each form is preferred.; Imperative and conditional: quick review of commands and wishes (Прочитай! Якщо б я мав час, я б поїхав).
- **Прикметники, порівняння, займенники (Adjectives, Comparison, Pronouns)**: Adjective declension review: hard and soft stems across all cases. Comparative and superlative forms, including irregular (кращий, більший, гірший).; Pronoun system review: personal, possessive (including свій), demonstrative, interrogative, indefinite (хтось, щось), negative (ніхто, ніщо), reflexive (себе).; Practice: fill in the correct pronoun or adjective form in connected text.
- **Складне речення: з'єднуємо думки (Complex Sentences: Connecting Ideas)**: Review of conjunctions and their usage: що (that), тому що (because), бо (because), коли (when), якщо (if), щоб (in order to), хоча (although).; Register distinction: бо (informal) vs тому що (neutral) vs через те що (formal). When to use which in writing vs speech.; Practice: combine simple sentences into complex ones using the appropriate conjunction. Transform between register levels.
- **Самооцінка і перехід до B1 (Self-Assessment and B1 Transition)**: Self-assessment checklist: rate your confidence in each grammar area (cases, aspect, comparison, syntax, metalanguage). Identify weakest areas.; What B1 expects: preview of Ukrainian-language grammar instruction, metalanguage vocabulary readiness check (from A2 metalanguage modules M55-M60).; Personal study plan: based on self-assessment results, which A2 modules to revisit before starting B1.

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 3: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 4: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A2).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
