<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 35: Checkpoint: Places (A1, A1.5 [Places])

## Plan vocabulary to verify

(No vocabulary hints in plan)

## Sections to research

- **Що ми знаємо? (What Do We Know?)**: Self-check covering M28-M34: Can you apply euphony rules? (M28) Can you say where things are? (M29) Can you name city places? (M30) Can you say where you're going? (M31) Can you use transport? (M32) Can you give directions? (M33) Can you say where you're from? (M34)
- **Читання (Reading Practice)**: A short Ukrainian text using vocabulary from M28-M34. Content: a tourist navigates Kyiv — asks for directions, takes metro, finds a museum, describes where they're from and where they're going. Uses euphony, locative, accusative, genitive chunks, transport.
- **Граматика (Grammar Summary)**: Key patterns from A1.5: 1. Euphony: у/в, і/й, з/із/зі (M28) 2. Де? → в/на + locative: в школі, на роботі (M29) 3. Куди? → в/на + accusative: у школу, на роботу (M31) 4. Звідки? → з + genitive chunk: з України, з роботи (M34) 5. Transport: автобусом, на метро (M32) 6. Directions: прямо, направо, наліво (M33) 7. City places with correct prepositions (M30)
- **Діалог (Connected Dialogue)**: A tourist in Kyiv asks for help: — Вибачте, я з Канади. Де тут музей? — Музей у центрі. Ідіть на метро до станції Хрещатик. — А як дістатися від метро? — Вийдіть і йдіть направо. Музей на площі. — Дякую! А потім я хочу їхати у Львів. Де вокзал? — Вокзал далеко, їдьте на метро до станції Вокзальна. Uses all A1.5 skills in one realistic scenario.
- **Підсумок — Summary**: A1.5 achievement summary: You can now navigate Ukrainian cities. You know euphony rules for natural speech. You can say WHERE something is (locative). You can say WHERE you're GOING (accusative). You can say WHERE you're FROM (genitive chunks). You can use transport and give directions. Next: A1.6 — Food and Shopping (ordering, buying, accusative for objects).

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
