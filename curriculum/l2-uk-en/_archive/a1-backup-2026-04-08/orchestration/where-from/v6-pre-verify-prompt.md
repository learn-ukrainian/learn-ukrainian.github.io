<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 34: Where From? (A1, A1.5 [Places])

## Plan vocabulary to verify

- звідки (where from)
- з/із/зі (from — + genitive chunk)
- Україна (Ukraine)
- Київ (Kyiv)
- Львів (Lviv)
- Канада (Canada)
- Одеса (Odesa)
- Харків (Kharkiv)
- США (USA)
- Англія (England)
- Німеччина (Germany)
- Польща (Poland)
- додому (home — direction)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Meeting someone (extending M05, ULP Ep4): — Звідки ти? — Я з України, з Києва. А ти? — Я з Канади, із Торонто. — Давно тут? — Ні, я приїхав місяць тому. Звідки? pattern with countries and cities.; Dialogue 2 — Coming from somewhere: — Звідки ти йдеш? — Я йду з роботи. — А Олена? — Вона йде зі школи. — Куди вона йде? — Додому. Direction FROM (з + genitive chunk) vs TO (в/на + accusative).
- **Звідки? (Where From?)**: Three direction questions complete: Де ти? — В Україні. (locative — where you ARE) Куди ти їдеш? — В Україну. (accusative — where you're GOING) Звідки ти? — З України. (genitive — where you're FROM) At A1: learn з + country/city as chunks. Genitive grammar = A2.; Pattern: з/із/зі + genitive (memorized forms): з України, з Києва, зі Львова, з Одеси, з Харкова. з Канади, зі США (зі Штатів), з Англії, з Німеччини, з Польщі. з роботи, зі школи, з магазину, з банку. Note: euphony rules from M28 apply: з/із/зі.
- **Країни і міста (Countries and Cities)**: Ukrainian cities: Київ (Kyiv), Львів (Lviv), Одеса (Odesa), Харків (Kharkiv), Дніпро (Dnipro), Запоріжжя (Zaporizhzhia). Countries (common for learners): Україна, Канада, США, Англія, Німеччина, Польща, Франція, Італія, Японія.; Nationality and language links: Я з України → Я українець/українка → Я говорю українською. Review from M05: Мене звати..., Я з..., Я говорю... New: Я живу в Києві, але я зі Львова. (current location vs origin)
- **Підсумок — Summary**: Three location questions: Де? → в/на + locative (В Україні) Куди? → в/на + accusative (В Україну) Звідки? → з/із/зі + genitive chunk (З України) Self-check: Where are you from? Where do you live now? Where are you going after this lesson?

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
