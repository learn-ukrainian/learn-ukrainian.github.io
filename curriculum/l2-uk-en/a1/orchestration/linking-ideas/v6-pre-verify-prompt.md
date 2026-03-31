<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 44: Linking Ideas (A1, A1.7 [Communication])

## Plan vocabulary to verify

- і (and)
- та (and — synonym of і)
- а (and/but — contrast)
- але (but)
- бо (because)
- тому що (because — longer form)
- чому (why)
- тому (therefore/that's why)
- також (also)
- теж (also — colloquial)
- або (or)
- чи (or — in questions)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Making plans: — Ти хочеш каву чи чай? — Каву, бо я дуже втомлений. — А я хочу чай, але без цукру. — Ходімо в кафе, і я візьму ще тістечко. — Я теж хочу, але я на дієті! Conjunctions: бо (because), а (and/but contrast), але (but), і (and).; Dialogue 2 — Talking about the day: — Що ти робив сьогодні? — Я працював, а потім ходив у магазин. — Я хотів зателефонувати, але ти не відповів. — Вибач, бо телефон був без звуку. — Нічого! — Завтра я вільний, і ми можемо зустрітися. Natural use of conjunctions in everyday talk.
- **Сполучники (Conjunctions)**: What are conjunctions? Ukrainian term: сполучник (from сполучити — to connect). They connect words, phrases, or whole sentences. Without: Я люблю каву. Я люблю чай. (choppy) With: Я люблю каву і чай. (natural) Without: Я хочу піти. Я втомлений. (disconnected) With: Я хочу піти, бо я втомлений. (connected thought); Grade 4-5 approach: сполучники сурядності (coordinating). These connect EQUAL parts: і / та — 'and' (та = synonym of і, common in writing): мама і тато, хліб та масло, Я читаю і пишу. а — 'and' with contrast or switch: Я люблю каву, а ти? Він працює, а вона відпочиває. але — 'but' (stronger contrast): Я хочу, але не можу. Він молодий, але розумний.
- **Бо і тому що (Because)**: Two ways to say 'because': бо — short, common in speech: Я не йду, бо я хворий. тому що — longer, common in writing: Я не йду, тому що я хворий. Both are correct. Both are Ukrainian. бо is NOT informal or wrong. Comma rule: always put a comma before бо and тому що. Я втомлений, бо багато працював. Ми не гуляємо, тому що йде дощ.; Building reasons: Чому? (Why?) → Бо / Тому що... — Чому ти вчиш українську? — Бо я люблю Україну. — Чому ти не їси? — Тому що я не голодний. — Чому ви тут? — Бо ми чекаємо друга. Бо answers the question Чому? — this is how Ukrainians explain things.
- **Підсумок — Summary**: Conjunction quick reference: | Conjunction | Meaning | Example | | і / та | and | Я їм хліб і п'ю воду. | | а | and (contrast) | Я читаю, а він пише. | | але | but | Я хочу, але не можу. | | бо | because | Я не йду, бо хворий. | | тому що | because | Я не йду, тому що хворий. | Comma rules: always before а, але, бо, тому що. Before і — only when connecting two full sentences. Self-check: Connect these pairs with the right conjunction: Я люблю каву. Я не люблю чай. → Я люблю каву, а/але...

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
