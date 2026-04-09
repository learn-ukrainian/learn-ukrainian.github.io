<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 27: Checkpoint: Time and Nature (A1, A1.4 [Time and Nature])

## Plan vocabulary to verify

(No vocabulary hints in plan)

## Sections to research

- **Що ми знаємо? (What Do We Know?)**: Self-check covering M22-M26: Can you tell time? (M22) Can you name days and months? (M23) Can you describe the weather? (M24) Can you describe your day? (M25) Can you talk about hobbies? (M26)
- **Читання (Reading Practice)**: A short Ukrainian text (8-10 sentences) using vocabulary from M22-M26. Content: a person describes their typical week — schedule, weather, hobbies. Example: У понеділок я працюю з дев'ятої до п'ятої. У вівторок вивчаю українську. Влітку я часто гуляю. Взимку ходжу в кіно. Мені подобається осінь.
- **Граматика (Grammar Summary)**: Key patterns from A1.4: 1. Time: Котра година? О котрій? (ordinal chunks) 2. Days: у понеділок, в суботу (accusative chunks) 3. Months: у січні, в серпні (locative chunks) 4. Seasons: взимку, навесні, влітку, восени 5. Weather: холодно, тепло, іде дощ, іде сніг 6. Sequence: спочатку, потім, нарешті 7. Frequency: завжди, часто, іноді, рідко, ніколи
- **Діалог (Connected Dialogue)**: A complete conversation combining all A1.4 skills: Planning a weekend outing. — Яка завтра погода? — Тепло і сонячно. — Чудово! Ходімо в парк! О котрій? — О десятій ранку. — Добре! Я часто гуляю в суботу. — А потім ходімо в кіно! — О п'ятій? — Так! Uses: time, day, weather, invitation, frequency.
- **Підсумок — Summary**: A1.4 achievement summary: You can now talk about time, schedules, and the world around you. You can tell time and plan meetings. You can name all days, months, and seasons. You can describe the weather. You can tell a story about your day. You can discuss hobbies and make plans. Next: A1.5 — Places (city, directions, transport).

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
