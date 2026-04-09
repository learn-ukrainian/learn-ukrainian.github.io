<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 41: Checkpoint: Food and Shopping (A1, A1.6 [Food and Shopping])

## Plan vocabulary to verify

(No vocabulary hints in plan)

## Sections to research

- **Що ми знаємо? (What Do We Know?)**: Self-check covering M36-M40: Can you name 10 foods and 5 drinks? (M36) Can you say what you eat/drink using accusative? (M37) Can you order at a cafe? (M38) Can you ask prices and buy things? (M39) Can you use accusative for people? (M40)
- **Читання (Reading Practice)**: A short Ukrainian text using vocabulary from M36-M40. Content: Anna goes to the market, buys food, then goes to a cafe. She orders борщ and каву з молоком, asks for the bill, then meets a friend and introduces her brother. Uses food vocabulary, accusative inanimate and animate, cafe phrases.
- **Граматика (Grammar Summary)**: Key patterns from A1.6: 1. Food/drink vocabulary: їжа, напої, meals (M36) 2. Accusative inanimate: masc = nom, fem -а→-у (M37) 3. Ordering: Мені каву, будь ласка (M38) 4. Prices: Скільки коштує? Гривня/гривні/гривень (M39) 5. Accusative animate: fem -а→-у, masc = genitive (M40) 6. Chunks: кава з молоком, кілограм яблук (M36, M39)
- **Діалог (Connected Dialogue)**: A day of food and shopping: — Що ти їш на сніданок? — Я їм кашу і п'ю каву з молоком. — Потім іду на ринок. Скільки коштують помідори? — Тридцять гривень. — Дайте кілограм, будь ласка. — Потім у кафе: Мені борщ і воду, будь ласка. — О, я бачу Олену! Олено, привіт! Ти знаєш мого брата? Combines all A1.6 skills in one realistic day.
- **Підсумок — Summary**: A1.6 achievement summary: You can talk about food and drinks. You can use accusative for things AND people. You can order at a cafe and pay. You can shop at a market and ask prices. Next: A1.7 — Communication (phone, email, making plans).

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
