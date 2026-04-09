<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 7: Checkpoint: First Contact (A1, A1.1 [Sounds, Letters, and First Contact])

## Plan vocabulary to verify

- All vocabulary from M01-M06 is recycled — no new required words
- ім'я (first name)
- прізвище (surname)

## Sections to research

- **Що ми знаємо? (What Do We Know?)**: Self-check covering M01-M06: Can you read any Ukrainian word? (M01-M02) Do you know what Ь and apostrophe do? (M03) Can you place stress correctly? (M04) Can you introduce yourself? (M05) Can you talk about your family? (M06)
- **Читання (Reading Practice)**: A short Ukrainian text (8-10 sentences) using ONLY vocabulary from M01-M06. No new words. The learner reads aloud. Content: A person introduces themselves, describes family, mentions professions, says where from.; Following Anna Ep10 'Я і моя сім'я' review pattern.
- **Граматика (Grammar Summary)**: Key patterns from A1.1: 1. Це + noun (identification) 2. Subject — Noun (no 'is'): Я — студент 3. У мене є + noun (possession) 4. Як тебе/вас звати? (asking names) 5. Мій/моя/моє + noun (possession with gender) 6. Звідки ти? — Я з... (origin as chunk)
- **Діалог (Capstone Dialogue)**: The Full Introduction — comprehensive dialogue combining EVERYTHING from A1.1. Setting: meeting someone new. Full cycle: greeting → name → origin → profession → family → showing photos → goodbye. If learner can follow and produce this dialogue, A1.1 is complete.; Connected monologue: learner's own self-introduction. Привіт! Мене звати [name]. Я [nationality]. Я — [profession]. Моя мама — [profession]. Мій тато — [profession]. У мене є [family]. This is the A1.1 graduation speech.
- **Підсумок — Summary**: Final self-check questions: How many letters/sounds in Ukrainian? Say hello formally and informally. Introduce yourself in 5 sentences. Name your family members with possessives.

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A1).

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
