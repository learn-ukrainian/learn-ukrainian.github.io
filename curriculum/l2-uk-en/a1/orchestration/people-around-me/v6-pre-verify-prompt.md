<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 40: People Around Me (A1, A1.6 [Food and Shopping])

## Plan vocabulary to verify

- бачити (to see)
- знати (to know)
- любити (to love)
- чекати (to wait for)
- шукати (to look for)
- друг (friend, m)
- подруга (friend, f)
- сусід (neighbor, m)
- колега (colleague, m/f)
- викладач (lecturer, m)
- вчитель (teacher, m)
- лікар (doctor, m)
- продавець (seller, m)
- покупець (buyer, m)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Who do you see? — Кого ти бачиш? — Я бачу маму і тата. — А хто це? — Це мій брат. Ти знаєш мого брата? — Ні, я не знаю твого брата. — Ходімо, я тебе познайомлю! Accusative animate: маму (f), тата (m), брата (m).; Dialogue 2 — At work: — Ти знаєш нашу вчительку? — Так, я знаю Олену Петрівну. — А нового лікаря? — Ні, я ще не знаю лікаря. — Він дуже добрий. Я чекаю його зараз. Animate accusative with people around you.
- **Кого? (Whom?)**: Accusative animate vs inanimate: Inanimate (M37): Я їм (що?) хліб. → no change for masculine. Animate (M40): Я бачу (кого?) брата. → masculine changes! The question word is the key: що? = inanimate (things) → masculine stays same. кого? = animate (people, animals) → masculine changes.; Ukrainian school approach (Grade 4): 'Бачу кого? що?' — two questions, two patterns. Кого? triggers the animate rule: masculine animate accusative = genitive form. брат → брата, друг → друга, тато → тата, лікар → лікаря. This is why animate accusative matters — it changes masculine nouns.
- **Знахідний відмінок — живе (Accusative Animate)**: Feminine animate: same as inanimate (-а → -у, -я → -ю): мама → маму (Я бачу маму), сестра → сестру (Я знаю сестру), Олена → Олену (Я чекаю Олену), подруга → подругу (Я люблю подругу). No surprise — same ending as M37 (кава → каву).; Masculine animate: accusative = genitive (THE new rule): брат → брата (Я бачу брата), друг → друга (Я знаю друга), тато → тата (Я люблю тата), лікар → лікаря (Я чекаю лікаря), вчитель → вчителя (Я знаю вчителя), сусід → сусіда (Я бачу сусіда). Pattern: masculine animate in accusative takes the genitive ending. Compare: Я бачу хліб (inanimate — no change) vs Я бачу брата (animate — changes).
- **Підсумок — Summary**: Accusative summary — the full picture: | | Inanimate (що?) | Animate (кого?) | | Masculine | = nominative (хліб) | = genitive (брата) | | Feminine | -а → -у (каву) | -а → -у (маму) | | Neuter | = nominative (молоко) | (rare at A1) | Key verbs with animate accusative: бачити (to see), знати (to know), любити (to love), чекати (to wait for), шукати (to look for). Self-check: Я бачу ___ (мама → маму, брат → брата).

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
