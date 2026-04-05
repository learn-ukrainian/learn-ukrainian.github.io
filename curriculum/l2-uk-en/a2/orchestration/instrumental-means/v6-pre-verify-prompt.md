<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 25: Ручкою, автобусом (A2, A2.4 [Instrumental Case])

## Plan vocabulary to verify

- ручка (pen)
- олівець (pencil)
- фарба (paint)
- лінійка (ruler)
- ніж (knife)
- ложка (spoon)
- автобус (bus)
- потяг (train)
- літак (airplane)
- трамвай (tram)
- засіб (means, tool)
- знаряддя (instrument, tool)
- транспорт (transport)
- пішки (on foot)
- корабель (ship)

## Sections to research

- **Чим? Знаряддя дії (With What? The Tool of an Action)**: The original meaning of Instrumental: the tool you use to do something. No preposition needed — the case ending alone carries the meaning.; Writing and drawing: писати ручкою, писати олівцем, малювати фарбами, креслити лінійкою, різати ножем, їсти ложкою.; Housework and daily tools: мити водою, витирати ганчіркою, чистити щіткою, підмітати віником.
- **Їхати автобусом: Засіб пересування (Travel by Bus: Means of Transport)**: Transport in Instrumental without a preposition: їхати автобусом, їхати потягом, летіти літаком, пливти кораблем, їхати таксі (indeclinable).; Question pattern: Чим ти їдеш на роботу? — Я їду автобусом / метро / трамваєм.; Dialogue: Two colleagues discussing how they get to work — one takes the bus, the other walks (іти пішки — an exception that uses no Instrumental).
- **Орудний відмінок множини (Instrumental Plural)**: Instrumental plural endings: -ами for hard stems (руками, столами, вікнами), -ями for soft stems (олівцями, дверями, конями).; The plural pattern is simpler than singular — same endings across all genders.; Practice with tools in plural: малювати фарбами, їсти паличками, працювати руками, писати олівцями.
- **Практика: Знаряддя чи супутник? (Practice: Tool or Companion?)**: Contrastive drill: Я пишу ручкою (tool) vs. Я ходжу з ручкою (companion — carrying it around). Він їде автобусом (means) vs. Він їде з другом (companion).; Fill-in exercises: choose whether to add з or use bare Instrumental based on meaning.; Dialogue: At school — students discuss what they write with, draw with, and how they get to school.

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
