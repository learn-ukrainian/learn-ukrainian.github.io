<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 12: This and That (A1, A1.2 [My World])

## Plan vocabulary to verify

- цей, ця, це (this — m/f/n)
- той, та, те (that — m/f/n)
- чи (or — in questions)
- ось (here is, look — pointing word)
- там (there)
- тут (here)
- він, вона, воно (review from M08 — used for reference)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Shopping (extending M10 colors + M11 prices): — Скільки коштує ця сумка? — Яка? Ця червона? — Ні, та синя. — Та коштує двісті гривень. — А цей рюкзак? — Цей — сто п'ятдесят. Demonstratives emerge naturally: цей/ця = the one here, той/та = the one there.; Dialogue 2 — In a room (extending M08-M09): — Що це? — Це мій стіл. — А те? — Те — крісло. — Цей стілець новий, а той — старий. Contrast near/far with objects already known.
- **Цей, ця, це (This)**: Demonstrative pronouns follow the same gender pattern as мій/моя/моє and який/яка/яке: Цей стіл (m) — this table. Ця книга (f) — this book. Це вікно (n) — this window. Заболотний Grade 6 p.210: вказівні займенники цей, той змінюються за родами. At A1 we learn nominative only — other forms come later.; Combining with adjectives and colors: Цей великий червоний стіл. Ця нова синя сумка. Це маленьке біле вікно. Word order: demonstrative + adjective(s) + noun (same as English!).
- **Той, та, те (That)**: Той/та/те = that (farther away, or previously mentioned): Той стіл (m) — that table. Та книга (f) — that book. Те вікно (n) — that window. Contrast: Цей стілець новий, а той — старий. Warning: 'та' also means 'and' (like і/й). Context makes it clear: мама та тато (and) vs та книга (that book).; Practical usage — pointing and choosing: Який стіл? — Цей чи той? (This one or that one?) Яка сумка? — Ця червона чи та синя? Яке вікно? — Це велике чи те маленьке? Note: 'Це' as demonstrative (це вікно = this window) vs 'це' as 'this is' (Це вікно = This is a window). Context makes it clear.
- **Підсумок — Summary**: Gender agreement table — all patterns from A1.2 together: | | m | f | n | | мій | моя | моє | (M06 possessives) | який | яка | яке | (M09 questions) | цей | ця | це | (M12 this) | той | та | те | (M12 that) Same endings, same logic — Ukrainian is consistent! Self-check: Point at 3 things near you (цей/ця/це), then 3 things far away (той/та/те).

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
