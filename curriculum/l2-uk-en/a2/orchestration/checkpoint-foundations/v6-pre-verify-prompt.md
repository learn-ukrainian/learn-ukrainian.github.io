<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 8: Контрольна точка: Основи А2 (A2, A2.1 [Foundation and Aspect Introduction])

## Plan vocabulary to verify

- вправа (exercise)
- перевірка (check, test)
- контрольна точка (checkpoint)
- завдання (task)
- текст (text)
- речення (sentence)
- відповідь (answer)
- правильний (correct)
- варіант (option, variant)
- обрати (to choose)
- написати (to write)

## Sections to research

- **Частина 1: Вправи на розпізнавання (Part 1: Recognition Exercises)**: Exercise 1: A short text is provided. Learner must highlight all perfective verbs in one color and all imperfective verbs in another.; Exercise 2: A list of sentences with a noun in parentheses. Learner must rewrite the sentence, putting the noun in the correct Genitive form (e.g., 'У мене немає (брат)' -> 'У мене немає брата').; Exercise 3: Match the imperfective verbs with their perfective partners.
- **Частина 2: Вправи на вибір (Part 2: Choice Exercises)**: Exercise 4: Multiple-choice sentences where the learner must choose between the perfective and imperfective form of a verb (e.g., 'Вчора я (читав / прочитав) цю книгу три години').; Exercise 5: Fill-in-the-blanks with the correct quantity word or numeral, ensuring noun agreement (e.g., 'У класі ___ (5) студентів').
- **Частина 3: Практичне застосування (Part 3: Production Exercises)**: Exercise 6: Answer open-ended questions that require the Genitive case or a specific aspect (e.g., 'Скільки у вас братів і сестер?', 'Що ви зробили вчора?', 'Коли у вас день народження?').; Exercise 7: A short writing prompt (5-7 sentences). 'Напишіть про свої плани на вихідні. Що ви будете робити? Що ви хочете зробити?' (Write about your plans for the weekend. What will you be doing? What do you want to get done?).

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
