<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 2: Зроблено чи в процесі? Вступ до виду дієслів (A2, A2.1 [Foundation and Aspect Introduction])

## Plan vocabulary to verify

- вид дієслова (verb aspect)
- недоконаний вид (imperfective aspect)
- доконаний вид (perfective aspect)
- процес (process)
- результат (result)
- дія (action)
- повторення (repetition)
- робити / зробити (to do)
- завершений (completed, finished)
- тривалий (ongoing, lasting)
- одноразовий (single, one-time)
- концепція (concept)

## Sections to research

- **Що таке вид дієслова? (What is Verb Aspect?)**: Introduction to the concept: Ukrainian verbs have a hidden dimension called 'aspect'. It's not about *when* (tense), but *how* the action unfolds.; Meet the two types: Недоконаний вид (НВ, imperfective) for ongoing processes, repeated actions, or facts. Доконаний вид (ДВ, perfective) for a single, completed action with a clear result.; Analogy: Imperfective is like watching a movie; perfective is like seeing the 'The End' screen.
- **Недоконаний вид: Процес і повторення (Imperfective: Process & Repetition)**: Focus on the uses of imperfective: describing an action in progress ('Я читав, коли ти подзвонив'), a repeated action ('Я читав цю книгу три рази'), or a general fact ('Діти читають книги').; Simple examples in present and past tense: 'Я читаю' (I am reading), 'Я читав' (I was reading / I used to read).; Key signal words: завжди (always), часто (often), зазвичай (usually), довго (for a long time), щодня (every day).
- **Доконаний вид: Результат! (Perfective: The Result!)**: Focus on the use of perfective: describing a single, successfully completed action. The result is what matters.; Example: 'Я прочитав книгу' (I have read the book, it is finished). Contrast with 'Я читав книгу' (I was reading the book, maybe I finished, maybe not).; Perfective verbs have no true present tense. Their 'present' form has a future meaning (e.g., 'зроблю' means 'I will do'). We will focus on the past tense for now: 'зробив', 'написала'.
- **Порівняння пар: Бачимо різницю (Comparing Pairs: Seeing the Difference)**: Side-by-side comparison of simple pairs: 'Він писав лист' (He was writing a letter) vs. 'Він написав лист' (He wrote a letter).; Visual aids: timelines showing the duration of an imperfective action vs. the single point of completion for a perfective action.

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
