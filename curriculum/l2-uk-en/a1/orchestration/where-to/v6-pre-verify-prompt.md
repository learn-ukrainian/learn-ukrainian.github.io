<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 31: Where To? (A1, A1.5 [Places])

## Plan vocabulary to verify

- куди (where to)
- йти (to go on foot)
- їхати (to go by transport)
- школа → у школу (to school)
- робота → на роботу (to work)
- банк → у банк (to the bank)
- магазин → у/в магазин (to the shop)
- бібліотека → у бібліотеку (to the library)
- ресторан → у ресторан (to the restaurant)
- Одеса → в Одесу (to Odesa)
- повертатися → додому (to return home)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Where are you going? (ULP Ep18): — Куди ти йдеш? — Я йду в банк. А ти? — Я йду на роботу. — А потім? — Потім іду в магазин. — А потім ходімо в кафе! Direction vs location: іду В банк (direction) vs я В банку (location).; Dialogue 2 — Planning a trip: — Куди ти їдеш у суботу? — Я їду у Львів. — А Олена? — Вона їде в Одесу. Cities as destinations: їхати в/у + city.
- **Куди? Знахідний відмінок (Where To? Accusative)**: Grade 4 case helper: Зн. (бачу) — кого? що? For direction: в/у + accusative = WHERE TO (motion toward). Compare with locative: в/у + locative = WHERE (static position). Де ти? — Я в банку. (locative — you ARE there) Куди ти йдеш? — Я йду в банк. (accusative — you're GOING there); Accusative endings for places: Masculine inanimate: = nominative (no change!): банк → в банк, магазин → у магазин, парк → у парк. Feminine -а/-я → -у/-ю: школа → у школу, робота → на роботу, бібліотека → у бібліотеку. Neuter: = nominative (no change): кафе → у кафе, місто → у місто. Good news: masculine and neuter don't change! Only feminine shifts.
- **Де чи куди? (Where or Where To?)**: The key question pair: Де ти? (Where are you?) → в/у/на + LOCATIVE Куди ти йдеш? (Where are you going?) → в/у/на + ACCUSATIVE | Place | Де? (М.в.) | Куди? (Зн.в.) | | школа | в школі | у школу | | робота | на роботі | на роботу | | банк | у банку | у банк | | парк | у парку | у парк |; Motion verbs: йти (to go on foot): Я йду в магазин. їхати (to go by transport): Я їду на вокзал. Note: йти = on foot, їхати = by vehicle. Both + в/на + accusative.
- **Підсумок — Summary**: Two questions, two cases: Де? → locative (в школі, на роботі) = STATIC Куди? → accusative (у школу, на роботу) = DIRECTION Masculine/neuter accusative = nominative (no change). Feminine: -а→-у, -я→-ю (школа→школу, бібліотека→бібліотеку). Self-check: Where are you? (Де?) Where are you going? (Куди?)

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
