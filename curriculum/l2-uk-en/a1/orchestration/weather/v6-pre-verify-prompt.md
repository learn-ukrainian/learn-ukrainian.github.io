<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 24: Weather (A1, A1.4 [Time and Nature])

## Plan vocabulary to verify

- погода (weather, f)
- холодно (cold — adverb)
- тепло (warm — adverb)
- дощ (rain, m)
- сніг (snow, m)
- сонце (sun, n)
- сьогодні (today)
- завтра (tomorrow)
- спекотно (hot)
- прохолодно (cool)
- вітер (wind, m)
- хмарно (cloudy)
- ясно (clear)
- сонячно (sunny)
- градус (degree, m)
- вчора (yesterday)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Looking out the window (ULP Ep16 pattern): — Яка сьогодні погода? — Сьогодні холодно і йде дощ. — А завтра? — Завтра буде тепло і сонячно. — Добре! Тоді завтра гуляємо! Weather + future plans (буде as chunk).; Dialogue 2 — Seasons conversation: — Яка пора року тобі подобається? — Мені подобається літо. — Чому? — Тому що влітку тепло і сонячно. А тобі? — Мені подобається осінь. Восени красиво. Weather + seasons + opinion verbs from M15.
- **Яка погода? (What's the Weather?)**: Impersonal weather expressions (no subject — the weather just IS): Сьогодні холодно. (It's cold today.) Сьогодні тепло. (It's warm.) Сьогодні спекотно. (It's hot.) Сьогодні прохолодно. (It's cool.) Заболотний Grade 8 p.126: безособові речення передають явища природи. These are adverbs — no subject needed, just the state.; Precipitation patterns: Іде дощ. (It's raining — literally 'rain goes'.) Іде сніг. (It's snowing — 'snow goes'.) Дме вітер. (The wind is blowing.) Світить сонце. (The sun is shining.) Хмарно / ясно. (Cloudy / clear.) Note: іде дощ (not 'дощить') is the natural conversational form.
- **Погода і пори року (Weather and Seasons)**: Connecting weather to seasons (M23): Взимку холодно. Іде сніг. (In winter it's cold. It snows.) Навесні тепло. Все зелене. (In spring it's warm. Everything's green.) Влітку спекотно. Світить сонце. (In summer it's hot. The sun shines.) Восени прохолодно. Іде дощ. (In autumn it's cool. It rains.); Temperature vocabulary: градуси (degrees) — Сьогодні двадцять градусів. (20 degrees.) плюс / мінус — Мінус десять. (Minus 10.) тепло / холодно as nouns: На вулиці тепло. (It's warm outside.) Time words: сьогодні (today), завтра (tomorrow), вчора (yesterday).
- **Підсумок — Summary**: Weather toolkit: Question: Яка сьогодні погода? Temperature: холодно, тепло, спекотно, прохолодно. Precipitation: іде дощ, іде сніг, дме вітер, світить сонце. Sky: хмарно, ясно, сонячно. Seasons: взимку холодно, влітку спекотно. Self-check: Describe today's weather. What's winter like where you live?

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
