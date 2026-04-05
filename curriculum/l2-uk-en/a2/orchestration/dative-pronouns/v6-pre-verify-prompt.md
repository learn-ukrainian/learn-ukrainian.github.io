<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 17: Мені, тобі, йому... (A2, A2.3 [Dative Case])

## Plan vocabulary to verify

- давальний відмінок (dative case)
- мені (to me)
- тобі (to you (informal))
- йому (to him, to it)
- їй (to her)
- нам (to us)
- вам (to you (formal/plural))
- їм (to them)
- холодно (cold (impersonal state))
- потрібно (necessary, needed)
- приємно (pleasant)
- цікаво (interesting)
- сумно (sad (impersonal state))
- важко (difficult, hard)

## Sections to research

- **Давальний відмінок: Кому? (The Dative Case: To Whom?)**: Introducing the Dative case (Давальний відмінок) as the case that answers Кому? Чому?; Core meaning: the recipient — the person who receives something, is told something, or for whom something is done.; Compare with Genitive (Кого? Чого?) and Accusative (Кого? Що?) — each case has its own question and function.
- **Особові займенники у давальному відмінку (Personal Pronouns in the Dative)**: Full paradigm: я→мені, ти→тобі, він→йому, вона→їй, воно→йому, ми→нам, ви→вам, вони→їм.; Key pattern: 1st/2nd person forms (мені, тобі, нам, вам) are unique — must be memorized as a set.; 3rd person: йому (masc/neut), їй (fem), їм (plural). After prepositions these gain initial н-: до нього, але йому.
- **Мені холодно: Безособові конструкції (Impersonal Constructions with Dative)**: Pattern: Dative pronoun + adverb/predicate to express states and feelings without a subject — мені холодно, тобі сумно, їй весело.; Common predicates: холодно, тепло, важко, легко, весело, сумно, приємно, цікаво, нудно, потрібно, можна.; Compare with nominative subject sentences: Я втомлена vs. Мені важко — different structure, different nuance.
- **Давальний чи знахідний? (Dative or Accusative?)**: Minimal pairs: Я бачу тебе (Acc.) vs. Я кажу тобі (Dat.). Він знає її (Acc.) vs. Він дзвонить їй (Dat.).; Decision strategy: Who receives the action? → Dative. Who is directly affected? → Accusative.; Practice distinguishing case usage with two-object verbs (давати щось комусь).

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Search textbooks for each section topic

For each section title above, call `search_text` with the Ukrainian keywords.

Report the most relevant textbook excerpt for each section (author, grade, key quote).

### Task 3: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 4: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 5: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A2).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Textbook Excerpts
### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
