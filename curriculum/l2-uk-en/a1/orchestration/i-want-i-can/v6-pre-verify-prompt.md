<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 18: I Want, I Can (A1, A1.3 [Actions])

## Plan vocabulary to verify

- хотіти (to want — irregular!)
- могти (to be able/can — irregular!)
- мусити (to must/have to)
- кава (coffee, f)
- їсти (to eat)
- шкода (pity, unfortunately)
- допомогти (to help)
- борщ (borscht, m)
- порекомендувати (to recommend)
- треба (need to — impersonal, preview)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Making plans: — Що ти хочеш робити? — Я хочу гуляти. А ти? — Я не можу, я мушу працювати. — Шкода! All three modals in one natural exchange.; Dialogue 2 — At a café (preview for A1.6): — Я хочу каву. — Велику чи маленьку? — Велику. І ще я хочу їсти. Що ви можете порекомендувати? — Можу порекомендувати борщ! Хотіти + noun (no infinitive needed).
- **Хотіти (To Want)**: Хотіти is irregular — it belongs to Group I despite -іти ending: я хочу, ти хочеш, він/вона хоче, ми хочемо, ви хочете, вони хочуть. Note: хот- → хоч- (т→ч change in all forms). Two uses: хочу + infinitive (Я хочу читати) or хочу + noun (Я хочу каву).; Negative: Я не хочу. Ти не хочеш? Вона не хоче. Polite requests use хотів/хотіла би (conditional) — but that's later. For now: Я хочу... is the direct way to express a want.
- **Могти і мусити (Can and Must)**: Могти (can/able to) — also irregular: я можу, ти можеш, він/вона може, ми можемо, ви можете, вони можуть. Note: мог- → мож- (г→ж change). Я можу говорити українською. Ти можеш допомогти?; Мусити (must/have to) — regular Group II: я мушу, ти мусиш, він/вона мусить, ми мусимо, ви мусите, вони мусять. Note: с→ш only in я-form (мушу), rest is regular. Я мушу працювати. Ти мусиш вчити слова. Мусити = obligation, not choice. Stronger than 'треба' (impersonal, later).
- **Підсумок — Summary**: Three modals + infinitive: Хочу + inf. = I want to (desire) Можу + inf. = I can (ability) Мушу + inf. = I must (obligation) All three: Я хочу гуляти, але не можу — мушу працювати. Self-check: Say what you want to do today. Say what you can do in Ukrainian. Say what you must do tomorrow.

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
