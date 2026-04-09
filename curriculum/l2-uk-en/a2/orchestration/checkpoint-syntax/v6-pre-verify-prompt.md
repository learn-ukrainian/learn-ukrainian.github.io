<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 53: Контрольна робота — складне речення (A2, A2.7 [Complex Sentences and Conditionals])

## Plan vocabulary to verify

- тому що (because)
- бо (because)
- хоча (although)
- щоб (in order to)
- який (which, that)
- якщо (if)
- сполучник (conjunction)
- складне речення (complex sentence)
- підрядний (subordinate)
- головний (main)
- кома (comma)

## Sections to research

- **Частина 1: Впізнай сполучник (Part 1: Identify the Conjunction)**: Conjunction identification: given a complex sentence, identify the conjunction and name its type — причина (тому що, бо), допуст (хоча), мета (щоб), означальне (який, де, куди, звідки), умова (якщо).; Error detection: find and correct errors in complex sentences — wrong conjunction, missing comma, wrong form of який, wrong verb form after щоб.; Mixed examples from all five types, drawn from everyday contexts covered in M42-M46.
- **Частина 2: Вибери правильну форму (Part 2: Choose the Correct Form)**: Conjunction selection: given a pair of ideas, choose the correct conjunction to combine them. Cause vs. purpose (тому що vs. щоб), coordination vs. subordination (але vs. хоча). Note: якщо (real condition) is A2; якби (unreal condition) is B1 — recognition only, no production expected.; Form agreement: choose the correct form of який (gender, number) for relative clauses. Choose the correct verb form after щоб (infinitive vs. past-tense form).; Basic reported speech: relay what someone said using що and чи (A2 scope — no sequence of tenses or complex transformations).
- **Частина 3: Побудуй складне речення (Part 3: Build Complex Sentences)**: Sentence building: given a situation (at university, at work, planning a trip), produce complex sentences using the required conjunction type.; Paragraph writing: combine multiple complex sentence types into a short connected paragraph about education goals, work experience, or weekend plans.; Self-assessment checklist: review all five types of complex sentences learned in A2.7. Can I explain причину? допуст? мету? означення? умову? Can I report what someone said?

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
