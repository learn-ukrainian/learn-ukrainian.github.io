<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 68: Пробний іспит (A2, A2.10 [Refinement and Graduation])

## Plan vocabulary to verify

- іспит (exam)
- завдання (task, exercise)
- відповідь (answer)
- питання (question)
- читання (reading)
- письмо (writing)
- граматика (grammar)
- результат (result)
- самооцінка (self-assessment)
- оцінка (grade, assessment)
- правильний (correct)

## Sections to research

- **Частина 1: Читання (Part 1: Reading)**: Text A: a short informational text (advertisement, schedule, or announcement — 80-100 words) with 3-4 comprehension questions. Tests scanning for specific information.; Text B: a personal message or email (100-120 words) where a Ukrainian friend describes their plans, asks questions, shares news. 4-5 comprehension questions requiring understanding of detail and inference.; Text C: a short narrative or blog post (120-150 words) about a Ukrainian tradition or travel experience. 4-5 questions testing main idea, vocabulary in context, and drawing conclusions.
- **Частина 2: Граматика (Part 2: Grammar)**: Section A: Case selection (6 items) — choose the correct case form in sentences with various triggers (verbs, prepositions, quantity words).; Section B: Verb form (6 items) — select the correct tense, aspect, or mood for the context.; Section C: Mixed grammar (6 items) — comparatives, pronouns (свій, себе, indefinite/negative), conjunctions, numeral agreement.
- **Частина 3: Спілкування та письмо (Part 3: Communication and Writing)**: Task A: Dialogue completion — fill in 6 blanks in a natural conversation (at a cafe, on the phone, planning a trip).; Task B: Guided writing — write a short text (80-100 words) on one of three topics: (1) Describe your favorite season and why, (2) Write to a Ukrainian friend about your weekend plans, (3) Describe a holiday tradition you like.; Scoring rubric: grammar accuracy (cases, aspect, agreement), vocabulary range, coherence, task completion.
- **Результати та самооцінка (Results and Self-Assessment)**: Answer key with explanations for each grammar and reading question. Why each answer is correct — teaching through the test itself.; Self-assessment grid: Strong / Developing / Needs Work for each A2 skill area (cases, aspect, comparison, complex sentences, vocabulary, reading, writing).; Recommendations: which modules to revisit before starting B1. Encouragement: passing 70% means ready for B1.

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
