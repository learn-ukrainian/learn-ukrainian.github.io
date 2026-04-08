<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 16: Контрольна робота — родовий відмінок (A2, A2.2 [Genitive Case Complete])

## Plan vocabulary to verify

- родовий відмінок (genitive case)
- прийменник (preposition)
- узгодження (agreement)
- множина (plural)
- однина (singular)
- закінчення (ending)
- перевірка (check, review)
- помилка (mistake, error)
- виправити (to correct)
- впізнати (to recognize)
- вибрати (to choose)

## Sections to research

- **Частина 1: Впізнавання форм (Part 1: Recognizing Forms)**: Preposition identification: given a sentence, identify which preposition triggers the Genitive and what meaning it carries (source, purpose, direction, time, location).; Form recognition: given noun phrases, identify whether they are correctly formed Genitives or contain errors.; Covers all prepositions from M08-M10: з/із/зі, від, після, для, без, біля, навпроти, коло, до.
- **Частина 2: Вибір правильної форми (Part 2: Choosing the Correct Form)**: Adjective and pronoun agreement: choose the correct Genitive form for adjectives (нового/нової), possessives (мого/моєї), and demonstratives (цього/цієї) in context.; Genitive plural selection: given a quantity word + noun, choose the correct Genitive plural ending (-ів, -ей, zero, or irregular).; Preposition choice: choose між з vs. від, біля vs. навпроти, до vs. після in minimal-pair sentences.
- **Частина 3: Вільне вживання (Part 3: Free Production)**: Sentence building: given a situation (at the market, at the doctor, giving directions), produce complete sentences using Genitive constructions.; Dialogue completion: fill in both sides of a short dialogue using appropriate Genitive phrases — market scenario, asking for directions, describing a daily routine.; Translation challenge: translate short English sentences into Ukrainian, requiring correct Genitive prepositions, agreement, and plural forms.

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
