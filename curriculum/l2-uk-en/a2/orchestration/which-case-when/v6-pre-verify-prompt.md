<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 36: Компас відмінків (A2, A2.5 [Case Synthesis and Plurals])

## Plan vocabulary to verify

- відмінок (grammatical case)
- прийменник (preposition)
- дієслово (verb)
- напрямок (direction)
- місце (place, location)
- час (time)
- характеристика (characteristic, description)
- думати (to think)
- боятися (to be afraid)
- користуватися (to use)
- алгоритм (algorithm)
- контекст (context)
- керувати (to manage, drive)
- майбутнє (future)

## Sections to research

- **Дієслово вирішує: Який відмінок після дієслова? (The Verb Decides: Which Case After a Verb?)**: Accusative verbs (most transitive): бачити, знати, любити, читати, купити, шукати + Acc. Я читаю книгу. Ми шукаємо ключі.; Dative verbs: допомагати, телефонувати, дякувати, радити, заважати + Dat. Я допомагаю сестрі. Ми дякуємо вчителям.; Instrumental verbs: користуватися, цікавитися, займатися, керувати + Instr. Він користується комп'ютером. Вона цікавиться історією.
- **Прийменник вирішує: Один прийменник — різні відмінки (The Preposition Decides: One Preposition, Different Cases)**: на + Acc. (direction/goal): Я йду на роботу. Поклади книгу на стіл. на + Loc. (location): Я на роботі. Книга лежить на столі.; у/в + Acc. (direction): Я йду в магазин. Acc. for time: у четвер, у середу, у п'ятницю. у/в + Loc. (location): Я в магазині. Loc. for years: у 2014 році, у минулому році.; по + Loc. (path/surface): бігати по кімнаті, ходити по вулиці, подорожувати по Україні.
- **Особливі випадки: Час, характеристика, шлях (Special Uses: Time, Characteristics, Path)**: Acc. for days and time periods: у четвер, у середу, у п'ятницю. Цю неділю я відпочиваю. Наступного тижня (Gen. for next/last).; Loc. for characteristics/description: хлопець у червоному светрі, дівчина в окулярах, жінка у білому пальті. Pattern: noun + у/в + Loc. describes what someone is wearing or looks like.; Loc. for years and time contexts: у 2014 році, у двадцять першому столітті, у дитинстві.
- **Алгоритм вибору відмінка (The Case Selection Algorithm)**: Step 1: Is there a preposition? → Check which case(s) it governs. Step 2: No preposition? → Check which case the verb requires. Step 3: Still unsure? → Ask the case question (Кого? Що? Кому? Ким? etc.).; Decision tree visual: Preposition → Case. Verb → Case. Neither → Default Nom. (subject) or context-dependent.; Common pitfalls: confusing на + Acc. (direction) with на + Loc. (location); forgetting that думати takes про + Acc., not Loc.; using Gen. instead of Dat. after допомагати.

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
