<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 21: Checkpoint: Actions (A1, A1.3 [Actions])

## Plan vocabulary to verify

(No vocabulary hints in plan)

## Sections to research

- **Що ми знаємо? (What Do We Know?)**: Self-check covering M15-M20: Can you say what you like? (M15) Can you conjugate Group I verbs? (M16) Can you conjugate Group II verbs? (M17) Can you say what you want, can, and must? (M18) Can you ask questions? (M19) Can you describe your morning? (M20)
- **Читання (Reading Practice)**: A short Ukrainian text (8-10 sentences) using ONLY vocabulary from M15-M20. No new words. The learner reads aloud. Content: a person describes their day — morning routine, work, hobbies. Example: Я прокидаюся о сьомій. Потім вмиваюся і снідаю. Я працюю в офісі. Я люблю читати. Увечері я дивлюся фільм.
- **Граматика (Grammar Summary)**: Key patterns from A1.3: 1. Infinitive: -ти (читати, говорити, хотіти) 2. Group I: -ю, -єш, -є, -ємо, -єте, -ють 3. Group II: -ю/-у, -иш, -ить, -имо, -ите, -ять 4. Modals: хочу/можу/мушу + infinitive 5. Questions: хто, що, де, куди, коли, чому, як 6. Negation: не + verb; double negation (ніхто не) 7. Reflexive: verb + ся (прокидаюся, вмиваюся)
- **Діалог (Connected Dialogue)**: A complete conversation combining all A1.3 skills: Meeting + plans scenario. — Привіт! Що ти робиш? — Я читаю книгу. А ти? — Я хочу гуляти. Ти можеш? — Не можу, мушу працювати. — Шкода! Коли ти працюєш? — До шостої. — Добре, тоді гуляємо ввечері! Uses: both verb groups, modals, questions, negation.
- **Підсумок — Summary**: A1.3 achievement summary: You can now talk about actions in Ukrainian. You can conjugate verbs in two groups. You can express wants, abilities, and obligations. You can ask questions and negate statements. You can describe your daily routine. Next: A1.4 — Time and Nature (time, days, weather).

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A1).

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
