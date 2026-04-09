<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 39: Shopping (A1, A1.6 [Food and Shopping])

## Plan vocabulary to verify

- коштувати (to cost)
- скільки (how much/many)
- гривня (hryvnia, f)
- ціна (price, f)
- магазин (shop, m)
- ринок (market, m)
- купувати (to buy)
- дорого (expensive — adverb)
- дешево (cheap — adverb)
- копійка (kopeck, f)
- кілограм (kilogram, m)
- літр (liter, m)
- пляшка (bottle, f)
- пачка (pack, f)
- знижка (discount, f)
- супермаркет (supermarket, m)
- гроші (money, pl.)
- готівка (cash, f)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — At the market: — Скільки коштує кілограм яблук? — Сорок гривень. — А помідори? — Тридцять п'ять гривень за кілограм. — Дайте, будь ласка, два кілограми помідорів і кілограм яблук. — Сімдесят п'ять гривень. — Ось, будь ласка. Prices, quantities, polite buying at the market.; Dialogue 2 — At the supermarket: — Вибачте, де тут хліб? — Хліб у третьому ряді. — А молоко? — Молоко в холодильнику, там. — Скільки коштує цей сир? — Сто двадцять гривень. — Дорого! А є дешевший? — Так, ось цей — вісімдесят. Navigation, asking prices, comparing (дорого/дешево).
- **Скільки коштує? (How Much?)**: Price patterns: Скільки коштує [item]? — [number] гривень/гривні/гривня. Скільки коштують [plural item]? — verb agrees with plural. Currency: гривня (1), гривні (2-4), гривень (5+). Копійка: one hundredth of a гривня (often rounded).; Numbers with prices (review from M12): 21 гривня, 32 гривні, 45 гривень, 100 гривень. Дорого! (Expensive!) Дешево! (Cheap!) Нормальна ціна. (Fair price.) Є знижка? (Is there a discount?) За все — [total]. (Total.)
- **Де купити? (Where to Buy)**: Shopping locations: магазин (shop), супермаркет (supermarket), ринок (market), аптека (pharmacy), крамниця (store — Ukrainian synonym for магазин). Specific: м'ясний відділ (meat section), молочний (dairy section).; Quantity words: кілограм (kilogram): кілограм яблук, два кілограми помідорів. літр (liter): літр молока, два літри соку. пачка (pack): пачка масла, пачка чаю. пляшка (bottle): пляшка води, пляшка соку. буханка (loaf): буханка хліба. All use genitive after quantity — taught as chunks at A1.
- **Підсумок — Summary**: Shopping toolkit: Ask: Скільки коштує? Де тут [item]? Buy: Дайте, будь ласка, [quantity] [item]. React: Дорого! / Дешево! / Добре, беру. Pay: Скільки за все? Можна карткою? Self-check: Buy 3 items at a market. Ask the price, choose a quantity, pay.

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
