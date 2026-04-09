<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 22: What Time? (A1, A1.4 [Time and Nature])

## Plan vocabulary to verify

- година (hour, f)
- котра (which — feminine, for time)
- перша, друга, третя (1st, 2nd, 3rd — feminine ordinals)
- ранок (morning, m)
- вечір (evening, m)
- день (day, m)
- ніч (night, f)
- четверта, п'ята, шоста (4th, 5th, 6th)
- сьома, восьма, дев'ята (7th, 8th, 9th)
- десята, одинадцята, дванадцята (10th, 11th, 12th)
- пів (half)
- чверть (quarter)
- опівдні (at noon)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Scheduling a meeting: — Котра година? — Десята. — О котрій ти працюєш? — О дев'ятій. А ти? — Я працюю о десятій. — Добре, тоді о першій? — Так! Time expressions emerge through making plans.; Dialogue 2 — Daily schedule: — Коли ти снідаєш? — О восьмій ранку. — А обідаєш? — О першій. Вечеряю о сьомій. Combining time with verbs from A1.3.
- **Котра година? (What Time Is It?)**: Захарійчук Grade 4 p.117: Котра година? — ordinal numbers for hours. Full hours use feminine ordinal numbers (година = feminine): Перша (1:00), друга (2:00), третя (3:00), четверта (4:00), п'ята (5:00), шоста (6:00), сьома (7:00), восьма (8:00), дев'ята (9:00), десята (10:00), одинадцята (11:00), дванадцята (12:00). Learn these as vocabulary — the grammar behind ordinals comes later.; Half hours and quarters: Пів на другу (1:30 — literally 'half to the second'). Чверть на третю (2:15). За чверть третя (2:45). At A1: focus on full hours and 'пів на'. Quarters for recognition only.
- **О котрій? (At What Time?)**: 'At' + time uses о/об + locative form (taught as chunks): О першій (at 1), о другій (at 2), о третій (at 3), о четвертій (at 4), о п'ятій (at 5), о шостій (at 6), о сьомій (at 7), о восьмій (at 8), о дев'ятій (at 9), о десятій (at 10), об одинадцятій (at 11), о дванадцятій (at 12). Note: об before vowels (об одинадцятій).; Time of day words: ранку (in the morning), дня (in the afternoon), вечора (in the evening), ночі (at night). О сьомій ранку (at 7 AM). О третій дня (at 3 PM). О десятій вечора (at 10 PM). Опівдні (at noon). Опівночі (at midnight).
- **Підсумок — Summary**: Telling time: Котра година? — Десята. (What time? — Ten o'clock.) О котрій? — О десятій. (At what time? — At ten.) Пів на другу (1:30). О пів на другу (at 1:30). Self-check: What time is it now? When do you wake up? When do you eat lunch? Say 3 times in Ukrainian.

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
