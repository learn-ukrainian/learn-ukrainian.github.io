<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 58: Слова мають друзів (A2, A2.8 [Refinement and Graduation])

## Plan vocabulary to verify

- синонім (synonym)
- антонім (antonym)
- епітет (epithet)
- метафора (metaphor)
- зменшувальний (diminutive)
- суфікс (suffix)
- еліпсис (ellipsis)
- повтор (repetition)
- образний (figurative, expressive)
- ласкавий (tender, affectionate)
- стилістика (stylistics)
- порівняння (comparison, simile)
- відтінок (shade, nuance)
- прислів'я (proverb)
- виразність (expressiveness)

## Sections to research

- **Синоніми та антоніми: збагачуємо мовлення (Synonyms and Antonyms: Enriching Speech)**: What synonyms are and why they matter: говорити — казати — розповідати, великий — чималий — величезний, гарний — красивий — вродливий. Each synonym carries a different shade of meaning.; What antonyms are: великий — малий, день — ніч, початок — кінець, радість — сум. Antonym pairs in proverbs: Не знаючи лиха, не пізнаєш і добра.; Practical exercise: replace repeated words in a paragraph with synonyms to improve style.
- **Епітети та метафори: мова, що малює (Epithets and Metaphors: Language That Paints)**: Epithets — expressive adjectives that create imagery: золота осінь, срібний дощ, палке серце, синє небо. Epithets go beyond literal description.; Metaphors — comparing without "like": море квітів (a sea of flowers), крила мрії (wings of a dream), зоря надії (star of hope). Ukrainian poetry is rich in metaphor.; Examples from Ukrainian songs and poetry: Реве та стогне Дніпр широкий (Шевченко) — personification as metaphor.
- **Зменшувальні суфікси: ласкаві слова (Diminutive Suffixes: Words of Endearment)**: The main diminutive suffixes: -ик (хлопчик, котик, столик), -ок (батько → батечко, note: -ок for masculine), -ечк- (книжечка, рученька via -еньк-), -очк- (зірочка, квіточка, ніченька via -еньк-).; Emotional function: diminutives express tenderness, affection, familiarity. Мамочка, серденько, сонечко — everyday Ukrainian is full of these.; Names get diminutives too: Оксана → Оксаночка, Тарас → Тарасик, Марія → Марійка, Іван → Іванко.
- **Синтаксична стилістика: еліпсис і повтор (Syntactic Stylistics: Ellipsis and Repetition)**: Еліпсис (ellipsis) — omitting a verb or subject that is understood from context. Ukrainian uses this naturally: Усе найкраще — дітям! (= Усе найкраще належить/дається дітям). Кожному — своє.; Еліпсис in everyday speech: Він — додому, вона — на роботу. Я — каву, а ти? These are not errors — they are natural Ukrainian style.; Повтор (repetition) — deliberate repetition for emphasis or expression: думали-думали (thought and thought), ходили-ходили (walked and walked), де-де? (where?). Reduplication as stylistic device.

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
