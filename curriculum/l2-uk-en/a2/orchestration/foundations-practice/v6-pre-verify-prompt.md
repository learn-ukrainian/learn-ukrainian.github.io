<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 7: Перші кроки в А2 (A2, A2.1 [Foundation and Aspect Introduction])

## Plan vocabulary to verify

- планувати / запланувати (to plan)
- купувати / купити (to buy)
- готувати / приготувати (to cook, prepare)
- ринок (market)
- коштувати (to cost)
- кілограм (kilogram)
- вечірка (party)
- день (day)
- сценарій (scenario)
- діалог (dialogue)
- обговорювати (to discuss)
- замовляти / замовити (to order)

## Sections to research

- **Сценарій 1: Плануємо вечірку (Scenario 1: Planning a Party)**: A dialogue between friends planning a party. Focus on future tense.; Imperfective for discussing what needs to be done: 'Ми будемо купувати напої', 'Я буду готувати салат'.; Use of Genitive with 'немає': 'У нас немає музики!' and with quantity words: 'Треба купити багато фруктів'.
- **Сценарій 2: На ринку (Scenario 2: At the Market)**: A dialogue between a shopper and a vendor.; Shopper asks 'Скільки коштує...?'; Shopper uses the 1, 2-4, 5+ rule to ask for items: 'Дайте мені, будь ласка, один кілограм яблук, дві дині і п'ять лимонів'.
- **Сценарій 3: Як пройшов твій день? (Scenario 3: How Was Your Day?)**: A conversation about past events.; Imperfective for setting the scene or describing an ongoing past action: 'Я вчора довго читав цікаву книгу'.; Perfective for sequential, completed actions: 'Спочатку я поснідав, потім пішов на роботу, а ввечері подивився фільм'.

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
