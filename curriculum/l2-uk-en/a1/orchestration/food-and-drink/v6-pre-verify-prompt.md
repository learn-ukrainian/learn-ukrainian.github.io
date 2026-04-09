<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 36: Food and Drink (A1, A1.6 [Food and Shopping])

## Plan vocabulary to verify

- їжа (food, f)
- напій (drink, m)
- хліб (bread, m)
- кава (coffee, f)
- чай (tea, m)
- вода (water, f)
- молоко (milk, n)
- сік (juice, m)
- м'ясо (meat, n)
- риба (fish, f)
- суп (soup, m)
- сніданок (breakfast, m)
- обід (lunch, m)
- вечеря (dinner, f)
- борщ (beet soup, m)
- вареник (dumpling, m)
- каша (porridge, f)
- сир (cheese, m)
- масло (butter, n)
- яйце (egg, n)
- картопля (potato, f)
- цукор (sugar, m)
- сіль (salt, f)
- сметана (sour cream, f)
- компот (compote, m)
- курка (chicken, f)
- салат (salad, m)
- піца (pizza, f)
- помідор (tomato, m)
- огірок (cucumber, m)
- яблуко (apple, n)
- банан (banana, m)
- лимон (lemon, m)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — At home in the morning: — Що ти хочеш на сніданок? — Каву з молоком і хліб з маслом. — А я хочу чай з цукром і кашу. Food + drink combinations as chunks (з + noun = memorized phrase).; Dialogue 2 — Talking about food preferences: — Що ти зазвичай їш на обід? — Суп і салат. — А на вечерю? — М'ясо з картоплею або рибу з рисом. Three meals: сніданок, обід, вечеря.
- **Їжа (Food)**: Core food vocabulary by category: Хліб і каша: хліб, каша, рис, макарони. М'ясо і риба: м'ясо, курка, риба. Овочі: картопля, морква, цибуля, помідор, огірок. Фрукти: яблуко, банан, апельсин. Молочне: молоко, сир, масло, сметана, йогурт. Інше: яйце, цукор, сіль, олія.; Ukrainian iconic foods (cultural note): борщ (beet soup — national dish), вареники (filled dumplings), сало (cured pork fat), галушки (dumplings), деруни (potato pancakes). These words are cultural identity, not just vocabulary.
- **Напої (Drinks)**: Core drink vocabulary: Гарячі: кава, чай. Холодні: вода, сік, компот, лимонад. Молочні: молоко, кефір. Алкогольні: пиво, вино (for recognition). Key chunk pattern: [drink] з [addition] — memorized, NOT grammar: кава з молоком, чай з цукром, чай з лимоном, вода з газом.; Why 'з + noun' is a chunk, not grammar: At A1, learn кава з молоком as a fixed phrase, like 'coffee with milk.' The instrumental case ending (-ом, -ою) is grammar for A2. For now: memorize the whole phrase. Say it as one unit.
- **Підсумок — Summary**: Food and drink toolkit: Що ти хочеш? — Каву з молоком. / Хліб з маслом. Що ти їш на сніданок / обід / вечерю? Three meals: сніданок (breakfast), обід (lunch), вечеря (dinner). Self-check: Name 5 foods and 3 drinks you like. Name one Ukrainian dish and why it matters.

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
