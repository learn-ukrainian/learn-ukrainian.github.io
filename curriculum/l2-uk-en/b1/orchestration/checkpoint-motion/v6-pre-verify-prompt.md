<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 33: Контрольна робота 4 (B1, B1.3 [Motion Verb Universe])

## Plan vocabulary to verify

- контрольна робота (test/assessment)
- просторовий прийменник (spatial preposition)
- односпрямований (unidirectional)
- різноспрямований (multidirectional)
- префікс (prefix)
- переносне значення (figurative meaning)
- подорож (journey)
- маршрут (route)
- розклад (schedule)
- самооцінка (self-assessment)
- повторення (review/revision)
- завдання (task/exercise)
- впевнено (confidently)
- перевірка (check/verification)

## Sections to research

- **Вступ: як працювати з контрольною**: Overview: this checkpoint tests everything from M27-M36 (Phase 4: Motion Verb Universe). Ten content areas: просторові прийменники (M27), базові пари дієслів руху (M28), prefix groups при-/до- (M29), пі-/по-/від- (M30), за-/ви- (M31), пере-/про- (M32), об-/під- (M33), повітряний/водний рух (M34), переносне значення (M35), подорожні розповіді (M36).; Instructions in Ukrainian: 'Виконайте всі завдання по черзі. Для кожного блоку є підказка, який модуль повторити. Головне — розуміння системи, а не механічне запам'ятовування.'; Self-assessment framework: after each block, rate your confidence (впевнено / потребую повторення / не розумію).
- **Блок 1: Просторові прийменники**: Case agreement exercise: given 8 sentences with spatial prepositions, learners choose the correct case ending for the following noun. Tests біля/серед/навпроти + Р.в., між/над/під/за/перед + Ор.в., під/за + Зн.в. (direction).; Preposition choice: 6 sentences where learners choose between synonymous prepositions (біля/коло/поруч з, серед/посеред, навколо/довкола) based on context and register.; Preposition vs adverb: 4 sentence pairs where learners identify whether the word is a preposition or adverb (навпроти школи vs сидів навпроти).
- **Блок 2: Базові пари дієслів руху**: Verb choice: 8 sentences where learners choose between односпрямований and різноспрямований verb (іти vs ходити, їхати vs їздити, бігти vs бігати, нести vs носити). Context clues: зараз, щодня, часто, саме цієї хвилини.; Conjugation: conjugate 4 base motion verbs in present tense (full paradigm), including irregular forms (біжу, їжджу, ходжу).; Prepositions with base motion verbs: complete 4 sentences choosing correct direction preposition (до + Р.в., в/на + Зн.в., з + Р.в.).
- **Блок 3: Префікси при-/до- та пі-/по-/від-**: Prefix selection: 8 sentences where learners choose the correct prefix (при-, до-, пі-/по-, від-) based on whether the motion is arriving, reaching, departing, or moving away.; Aspect pairs: given 6 perfective prefixed verbs, learners produce the imperfective counterpart (прийти→приходити, поїхати→виїжджати, від'їхати→від'їжджати).; Journey stage ordering: arrange 6 sentences in logical journey order (відійшов → поїхав → проїхав → доїхав → приїхав).
- **Блок 4: Префікси за-/ви-, пере-/про-, об-/під-**: Prefix selection: 10 sentences testing all remaining prefix groups. Learners choose between за- (entering/dropping by) and ви- (exiting), пере- (crossing) and про- (passing), об- (around) and під- (approaching).; Opposite pairs: given 6 prefixed verbs, learners produce the spatial opposite (зайти↔вийти, перейти↔?, обійти↔підійти).; Preposition + case: complete 6 sentences with correct preposition after prefixed motion verbs (зайти в/до, вийти з, перейти через, проїхати повз, підійти до).
- **Блок 5: Повітряний і водний рух та переносне значення**: Air/water motion: 6 sentences testing prefixed forms of летіти and пливти (прилетіти, вилетіти, переплисти, відпливти). Includes aviation/maritime vocabulary (аеропорт, рейс, причал).; Literal vs figurative: 8 sentences where learners identify whether the motion verb is used literally or figuratively. Час іде (figurative). Людина іде (literal). Літак летить (literal). Час летить (figurative).; Figurative expression completion: fill in 4 expressions (дощ ___, справи ___ добре, нести ___, вести ___).
- **Блок 6: Подорожні розповіді**: Reading comprehension: a travel passage (200-250 words) about a journey across Ukraine, followed by 5-6 comprehension questions testing understanding of motion verbs, routes, and destinations.; Travel dialogue: complete a dialogue at a train station with appropriate vocabulary and motion verb forms (6 exchanges).; Production: write a short travel plan for a weekend trip in Ukraine, using at least 8 different prefixed motion verbs, 4 spatial prepositions, and 5 transport vocabulary items.
- **Підсумок та самооцінка**: Integrated exercise: a passage (200 words) with 10 blanks where learners fill in the correct motion verb (choosing base vs prefixed, correct prefix, correct aspect).; Self-assessment checklist: Прийменники: Чи правильно я вживаю відмінки після просторових прийменників? Пари: Чи розумію різницю між іти та ходити? Префікси: Чи можу я вжити всі 10 префіксів правильно? Переносне: Чи вживаю я дієслова руху в переносному значенні? Подорожі: Чи можу я розповісти про подорож українською?; Recommendations: if any block scores below 70%, return to the corresponding module. Phase 5 (Degrees of Comparison) shifts focus from motion to description — a different grammar domain.

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (B1).

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
