<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 32: Transport (A1, A1.5 [Places])

## Plan vocabulary to verify

- автобус (bus, m)
- метро (metro, n)
- таксі (taxi, n)
- потяг (train, m)
- квиток (ticket, m)
- зупинка (stop, f)
- трамвай (tram, m)
- маршрутка (minibus, f)
- літак (plane, m)
- направо (right)
- наліво (left)
- прямо (straight)
- дістатися (to get to)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Getting to the train station: — Як дістатися до вокзалу? — Їдьте автобусом або на метро. — Який автобус? — Номер сім. Зупинка ось там. — Дякую! — На здоров'я! Transport vocabulary in practical context.; Dialogue 2 — Buying a ticket: — Один квиток до Львова, будь ласка. — В один бік чи туди й назад? — Туди й назад. Скільки коштує? — П'ятсот гривень. — О котрій відправлення? — О дев'ятій ранку. Combines transport + numbers (M11) + time (M22).
- **Транспорт (Transport Types)**: City transport: автобус (bus, m), тролейбус (trolleybus, m), трамвай (tram, m), метро (metro, n — indeclinable), маршрутка (minibus, f), таксі (taxi, n — indeclinable). Intercity: потяг (train, m), автобус (bus), літак (plane, m).; How to say 'by transport': їхати автобусом / тролейбусом / трамваєм (instrumental chunk — not grammar). їхати на метро / на таксі / на машині (на + locative chunk). Note: both patterns mean 'by' — learn each transport with its pattern.
- **Корисні фрази (Useful Phrases)**: At the station/stop: Зупинка (stop/station), Де зупинка автобуса? (Where's the bus stop?) квиток (ticket), Один квиток, будь ласка. (One ticket, please.) Скільки коштує квиток? (How much is a ticket?) Коли наступний потяг? (When is the next train?); On the way: Яка це зупинка? (What stop is this?) Мені виходити тут? (Do I get off here?) Вибачте, як дістатися до...? (Excuse me, how do I get to...?) прямо (straight), направо (right), наліво (left).
- **Підсумок — Summary**: Transport communication: Types: автобус, метро, таксі, потяг, трамвай. By: автобусом / на метро (two patterns). Buying: Один квиток до... Скільки коштує? Asking: Де зупинка? Як дістатися до...? Self-check: How do you get to work? Buy a train ticket to Lviv.

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
