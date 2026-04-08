<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 31: Контрольна точка: Орудний відмінок (A2, A2.4 [Instrumental Case])

## Plan vocabulary to verify

- орудний відмінок (instrumental case)
- вправа (exercise)
- контрольна точка (checkpoint)
- завдання (task)
- речення (sentence)
- відповідь (answer)
- текст (text)
- перевірка (check, test)
- правильний (correct)
- словосполучення (phrase, word combination)
- описати (to describe)
- визначити (to identify, to determine)

## Sections to research

- **Частина 1: Розпізнавання та форми (Part 1: Recognition and Forms)**: Exercise 1: A short text about someone's day is provided. Learner must identify all nouns in the Instrumental case and label each function (tool, companion, profession, spatial, temporal).; Exercise 2: Put nouns in parentheses into the correct Instrumental form — covers all three genders, hard and soft stems: (брат) → братом, (подруга) → подругою, (море) → морем.; Exercise 3: Form Instrumental plural from given Nominative plurals: (руки) → руками, (олівці) → олівцями, (діти) → дітьми.
- **Частина 2: Вибір та застосування (Part 2: Choice and Application)**: Exercise 4: Choose the correct preposition (з, над, під, перед, за, між) to complete spatial and temporal sentences.; Exercise 5: Decide whether to use bare Instrumental or з + Instrumental — tool vs. accompaniment discrimination (писати ручкою vs. ходити з другом).; Exercise 6: Multiple-choice — select the correct Instrumental form of adjective + noun phrases (з [гарний/гарним/гарною] [друг/другом/другові]).
- **Частина 3: Вільне вживання (Part 3: Free Production)**: Exercise 8: Answer open-ended questions requiring various Instrumental functions: Ким ти працюєш? Чим ти захоплюєшся? З ким ти живеш? Що знаходиться перед твоїм будинком?; Exercise 9: Describe a picture of a kitchen scene — who is cooking, what tools they use, what ingredients are on the table, where objects are located.; Exercise 10: Writing prompt (8-10 sentences): "Опишіть свій типовий день. Розкажіть про свою професію, як ви добираєтесь на роботу, з ким ви обідаєте, і що ви готуєте на вечерю." Learner must use at least 6 different Instrumental constructions.

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
