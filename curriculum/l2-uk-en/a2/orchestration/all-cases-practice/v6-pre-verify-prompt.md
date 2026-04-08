<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 37: Все разом (A2, A2.5 [Case Synthesis and Plurals])

## Plan vocabulary to verify

- вечірка (party)
- подарунок (gift, present)
- лікар (doctor)
- пацієнт (patient)
- здоров'я (health)
- ліки (medicine)
- подорож (trip, journey)
- потяг (train)
- визначне місце (landmark, sight)
- запрошувати (to invite)
- рецепт (prescription, recipe)
- температура (temperature)
- Карпати (Carpathians)
- милуватися (to admire)
- частувати (to treat (with food))

## Sections to research

- **Діалог 1: Організовуємо день народження (Dialogue 1: Organizing a Birthday Party)**: Extended dialogue (12-15 exchanges) between two friends planning a birthday party. Naturally includes: Nom. (subjects — хто прийде?), Gen. (немає торта, багато гостей), Dat. (подарунок Олені, написати друзям), Acc. (купити торт, запросити друзів), Instr. (з друзями, прикрасити кулями), Loc. (у кафе, на вечірці), Voc. (Оксано! Андрію!).; After each dialogue section: case identification exercise — learner marks which case each highlighted noun is in and explains the trigger.; Cultural note: Ukrainian birthday traditions — the birthday person treats guests (не гості дарують вечірку, а іменинник частує).
- **Діалог 2: У лікарні (Dialogue 2: At the Hospital)**: Extended dialogue between a patient and a doctor. Cases used: Nom. (Що вас турбує?), Gen. (немає температури, біля лікарні), Dat. (лікарю, пацієнтові), Acc. (приймати ліки, на огляд), Instr. (з кашлем, за рецептом), Loc. (у лікарні, на прийомі), Voc. (Лікарю! Пане докторе!).; Vocabulary for body and health integrated naturally: голова, горло, температура, ліки, рецепт, здоров'я.; After dialogue: learner rewrites selected sentences changing singular to plural (один пацієнт → багато пацієнтів, одні ліки → different quantity expressions).
- **Діалог 3: Подорож Україною (Dialogue 3: Traveling Across Ukraine)**: Extended dialogue between travelers discussing a road trip. Cases: Nom. (Київ — гарне місто), Gen. (з Києва, до Львова, багато визначних місць), Dat. (друзям у Львові, нам треба), Acc. (відвідати Одесу, у четвер, через Умань), Instr. (поїхати потягом, з подругою, милуватися Карпатами), Loc. (у Львові, по Хрещатику, у 2024 році), Voc. (Тарасе! Друже!).; Geography vocabulary: міста, гори, річки, вулиці — all declined in multiple cases throughout the dialogue.; Planning expressions: Давай поїдемо... Може, спочатку... А потім можна...
- **Самоперевірка: Знайди помилку (Self-Check: Find the Error)**: Short texts (3-4 sentences each) containing deliberate case errors. Learner identifies and corrects each error.; Error types include: wrong case after preposition, animate/inanimate confusion in Acc.Pl., wrong Gen.Pl. ending, Dat./Loc. confusion.; Summary: quick reference of all 7 cases with their key question words, most common prepositions, and typical verb triggers — a "case cheat sheet" the learner can return to.

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A2).

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
