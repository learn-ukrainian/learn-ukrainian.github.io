<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 33: Around the City (A1, A1.5 [Places])

## Plan vocabulary to verify

- пішки (on foot)
- хвилина (minute, f)
- район (neighborhood, m)
- центр (center, m)
- вибачте (excuse me)
- дістатися (to get to)
- ідіть (go! — imperative, preview)
- їдьте (go by transport! — imperative, preview)
- поруч (nearby)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Asking for directions: — Вибачте, як дістатися до бібліотеки? — Ідіть прямо, потім направо. Бібліотека на розі. — А музей? — Музей далеко. Їдьте на метро до центру. Combines directions + transport + city places.; Dialogue 2 — Describing your route: — Як ти дістаєшся на роботу? — Спочатку йду на зупинку. Потім їду автобусом до центру. — А потім? — Потім іду пішки п'ять хвилин. Робота в офісі на площі. Daily route using sequence words + transport + places.
- **Де і куди разом (Where and Where To Together)**: Real navigation uses both cases together: Я зараз у парку (де? — locative). Я йду в магазин (куди? — accusative). Магазин на вулиці Шевченка (де? — locative). Потім їду на роботу (куди? — accusative). The constant switch between де? and куди? is natural Ukrainian.; Preposition patterns (synthesis): | Situation | Question | Form | | Static | Де ти? | в/на + locative | | Direction | Куди йдеш? | в/на + accusative | | By transport | Як? Чим? | автобусом / на метро | | Distance | Далеко? | далеко / близько / пішки |
- **Мій район (My Neighborhood)**: Describing where you live: Я живу на вулиці Франка. Біля мого дому є парк і магазин. Школа далеко — треба їхати автобусом. Аптека близько, можна піти пішки. У моєму районі є кафе, ресторан і бібліотека.; Useful phrases for city life: пішки (on foot), хвилина (minute) — П'ять хвилин пішки. далеко/близько від (far/near from — chunk). У центрі міста / на околиці (in the center / on the outskirts).
- **Підсумок — Summary**: Urban communication toolkit: Asking: Де...? Як дістатися до...? Directions: прямо, направо, наліво. Location: в/на + locative, в/на + accusative. Transport: автобусом, на метро, пішки. Self-check: Describe your route from home to work/school.

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
