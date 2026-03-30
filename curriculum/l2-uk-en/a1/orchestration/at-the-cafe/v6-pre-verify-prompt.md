<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 38: At the Cafe (A1, A1.6 [Food and Shopping])

## Plan vocabulary to verify

- кафе (cafe, n, indecl.)
- меню (menu, n, indecl.)
- рахунок (bill, m)
- замовляти (to order)
- офіціант (waiter, m)
- смачно (delicious — adverb)
- будь ласка (please)
- ресторан (restaurant, m)
- рекомендувати (to recommend)
- чайові (tip/gratuity, pl.)
- готівка (cash, f)
- картка (card, f)
- гостре (spicy — neuter adj.)
- вегетаріанський (vegetarian — adj.)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Ordering at a cafe: — Добрий день! Ось меню. — Дякую. Що ви рекомендуєте? — Борщ дуже смачний. — Добре, мені борщ і хліб, будь ласка. — А що будете пити? — Каву з молоком. — Добре, одну хвилинку. Polite ordering with будь ласка, мені + accusative.; Dialogue 2 — Paying the bill: — Рахунок, будь ласка. — Ось, будь ласка. Сто двадцять гривень. — Можна карткою? — Так, звичайно. — Дякую, дуже смачно було! — Дякуємо, приходьте ще! Paying, complimenting food, tipping.
- **Як замовити (How to Order)**: Ordering patterns: Мені [accusative], будь ласка. (Мені каву, будь ласка.) Можна [accusative]? (Можна воду?) Дайте, будь ласка, [accusative]. (Дайте, будь ласка, борщ.) Я хочу / Я буду [accusative]. (Я буду салат.) All use accusative from M37 — real application.; Asking about the menu: Що ви рекомендуєте? (What do you recommend?) Це гостре? (Is it spicy?) Це з м'ясом? (Is it with meat?) А що це? (What is this?) Скільки коштує? (How much?) Є вегетаріанське меню? (Is there a vegetarian menu?)
- **Культура кафе (Cafe Culture)**: Ukrainian cafe culture: Кафе vs ресторан: кафе is casual, ресторан is formal. Меню: the waiter brings it, or it's on the wall/board. Рахунок: ask for the bill — it doesn't come automatically. Чайові (tips): 10% is standard, not obligatory. Карткою чи готівкою? (Card or cash?) — most places take cards.; Useful cafe phrases: Вільно? / Тут вільно? (Is this seat free?) Можна меню? (Can I have the menu?) Ще одну каву, будь ласка. (One more coffee, please.) Без цукру. (Without sugar.) З лимоном. (With lemon.) Все було дуже смачно! (Everything was delicious!)
- **Підсумок — Summary**: Cafe communication toolkit: Order: Мені [accusative], будь ласка. Ask: Скільки коштує? Що рекомендуєте? Pay: Рахунок, будь ласка. Можна карткою? Compliment: Дуже смачно! Self-check: Order a full meal (starter, main, drink) at a cafe. Ask for the bill and pay.

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
