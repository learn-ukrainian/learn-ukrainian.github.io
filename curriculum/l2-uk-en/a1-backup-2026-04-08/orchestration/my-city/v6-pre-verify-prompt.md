<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 30: My City (A1, A1.5 [Places])

## Plan vocabulary to verify

- аптека (pharmacy, f)
- бібліотека (library, f)
- магазин (shop, m)
- ресторан (restaurant, m)
- готель (hotel, m)
- вокзал (train station, m)
- тут (here)
- там (there)
- лікарня (hospital, f)
- супермаркет (supermarket, m)
- пошта (post office, f)
- музей (museum, m)
- церква (church, f)
- далеко (far)
- близько (near)
- біля (near — + genitive chunk)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — New in the city: — Вибачте, де тут аптека? — Аптека на вулиці Шевченка. — А бібліотека? — Бібліотека в центрі, біля парку. — Дякую! — Будь ласка! City places in asking-for-directions context.; Dialogue 2 — My neighborhood: — Що є біля твого дому? — Біля дому є магазин і кафе. — А школа? — Школа далеко, у центрі міста. Review: в/на + locative for all places.
- **Місця в місті (City Places)**: Essential city vocabulary: аптека (pharmacy), бібліотека (library), лікарня (hospital), магазин (shop), супермаркет (supermarket), ресторан (restaurant), кафе (café), банк (bank), пошта (post office), вокзал (train station), готель (hotel), музей (museum), театр (theater), кінотеатр (cinema), церква (church), стадіон (stadium), університет (university).; Each place with its preposition (locative from M29): в аптеці, у бібліотеці, у лікарні, в магазині, у ресторані, у кафе, у банку, на пошті, на вокзалі, у готелі, в музеї. What you do there: Я купую ліки в аптеці. Я читаю в бібліотеці. Я працюю в офісі. Я відпочиваю в парку.
- **Де це? (Where Is It?)**: Location words: тут (here), там (there), далеко (far), близько (near/close), біля + gen (near — as chunk: біля парку, біля дому), у центрі (in the center), на розі (on the corner). Note: біля requires genitive — learn as chunks, not grammar.; Describing your city: У моєму місті є великий парк і два музеї. Бібліотека біля університету. Магазин тут, біля дому. Note: є = 'there is/are' (already used since M06).
- **Підсумок — Summary**: City vocabulary with prepositions: В/у: аптеці, бібліотеці, магазині, банку, готелі, ресторані. На: пошті, вокзалі, стадіоні, площі. Location words: тут, там, далеко, близько, біля. Self-check: Name 5 places near your home. What do you do there?

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
