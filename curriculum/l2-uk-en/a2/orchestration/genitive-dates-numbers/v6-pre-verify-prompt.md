<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 6: Скільки? Котра година? Яке число? (A2, A2.1 [Foundation and Aspect Introduction])

## Plan vocabulary to verify

- число (дата) (date)
- місяць (month)
- січень (січня) (January)
- лютий (лютого) (February)
- березень (березня) (March)
- квітень (квітня) (April)
- травень (травня) (May)
- червень (червня) (June)
- липень (липня) (July)
- серпень (серпня) (August)
- вересень (вересня) (September)
- жовтень (жовтня) (October)
- листопад (листопада) (November)
- грудень (грудня) (December)
- заперечення (negation)
- числівник (numeral)
- додаток (object (grammatical))
- правило (rule)

## Sections to research

- **Яке сьогодні число? Родовий з датами (What's the Date? Genitive with Dates)**: How to ask the date: 'Яке сьогодні число?'; How to answer: The day is an ordinal numeral (перше, друге), and the month is a noun in the Genitive singular.; Examples: перше січня, друге лютого, двадцять п'яте грудня. All month names are masculine and take the standard genitive endings: -я (січня, лютого, березня...) or -а (листопада).
- **Рахуємо предмети: правило '1, 2-4, 5+' (Counting Items: The '1, 2-4, 5+' Rule)**: The fundamental rule for counting in Ukrainian:; 1 (+21, 31..): Nominative Singular (один стіл).; 2, 3, 4 (+22-24..): Nominative Plural (два столи, три столи, чотири столи).
- **Заперечення з прямим додатком (Negation with a Direct Object)**: When you negate a verb that takes a direct object in the Accusative, the object often (but not always) shifts to the Genitive.; This adds emphasis to the negation. It's the difference between 'I didn't read *the book*' and 'I didn't read *any book*'.; Clear examples: 'Я читаю книгу' (Acc) -> 'Я не читаю книги' (Gen). 'Він купив машину' (Acc) -> 'Він не купив машини' (Gen).

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
