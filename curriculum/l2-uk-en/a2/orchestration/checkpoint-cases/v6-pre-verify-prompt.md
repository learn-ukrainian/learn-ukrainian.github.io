<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 39: Контрольна точка: Відмінки та множина (A2, A2.5 [Case Synthesis and Plurals])

## Plan vocabulary to verify

- перевірка (check, review)
- контрольна точка (checkpoint)
- завдання (task, exercise)
- помилка (error, mistake)
- виправити (to correct)
- відмінок (grammatical case)
- множина (plural)
- однина (singular)
- самоперевірка (self-check)
- впевнено (confidently)
- вихідний день (day off)

## Sections to research

- **Частина 1: Форми множини (Part 1: Plural Forms)**: Exercise 1: Form the Nominative plural from 10 singular nouns across all відміни (mixed genders, including irregulars like дитина, людина, око).; Exercise 2: Form the Genitive plural — the hardest forms. Given 10 nouns, learner produces Gen.Pl. (книга → книг, студент → студентів, місто → міст, ніч → ночей, теля → телят).; Exercise 3: Complete quantity expressions with the correct Gen.Pl. form (п'ять ___, багато ___, скільки ___?).
- **Частина 2: Який відмінок? (Part 2: Which Case?)**: Exercise 4: Multiple-choice — given a sentence with a blank, choose the correct case form. Includes all triggers: verbs (допомагати + Dat., бачити + Acc., користуватися + Instr.), prepositions (у + Loc./Acc., з + Gen./Instr., по + Loc.), special uses (у четвер, у 2014 році, хлопець у светрі).; Exercise 5: Case identification — a short text (8-10 sentences) with underlined nouns. Learner identifies the case of each underlined noun and the trigger (verb, preposition, or construction).; Exercise 6: Error correction — 6 sentences with case errors. Learner finds and corrects each error (e.g., *Я допомагаю сестру → сестрі; *багато студенти → студентів).
- **Частина 3: Вільне мовлення (Part 3: Free Production)**: Exercise 7: Guided writing — "Опишіть свій ідеальний вихідний день" (Describe your ideal day off). Must include: where you go (Acc./Loc.), who you meet (Acc./Dat.), what you do (Acc./Instr.), what you eat (Gen. for quantities, Acc. for items).; Exercise 8: Dialogue completion — a dialogue with missing noun forms. Learner fills in 8-10 blanks using the correct case, both singular and plural.; Self-assessment checklist: Can I form plurals confidently? Do I know which case each preposition takes? Can I use the case compass from M31? Ready for A2.6?

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
