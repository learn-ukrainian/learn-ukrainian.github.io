<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 19: Questions (A1, A1.3 [Actions])

## Plan vocabulary to verify

- хто (who)
- що (what)
- де (where)
- куди (where to)
- коли (when)
- чому (why)
- як (how)
- не (not)
- ні (no)
- ніхто (nobody)
- нічого (nothing)
- ніколи (never)
- жити (to live)
- розуміти (to understand)
- тому що (because)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Getting to know someone (extending M05): — Хто ти? — Я студент. — Що ти вивчаєш? — Я вивчаю українську. — Де ти живеш? — Я живу в Києві. — Коли ти працюєш? — Вранці. Question words demonstrated in real conversation.; Dialogue 2 — At home: — Де моя книга? — Я не знаю. — А хто знає? — Мама знає. — Чому мама? — Тому що вона все знає! Questions + negation in practical context.
- **Питальні слова (Question Words)**: Seven essential question words: Хто? (Who?) — Хто це? Хто говорить? Що? (What?) — Що це? Що ти робиш? Де? (Where?) — Де ти живеш? Де книга? Куди? (Where to?) — Куди ти ходиш? Коли? (When?) — Коли ти працюєш? Чому? (Why?) — Чому ти не працюєш? Як? (How?) — Як справи? Як тебе звати?; Word order: question word + verb + subject (flexible): Де ти живеш? = Ти де живеш? (both acceptable). Yes/no questions: just raise intonation at the end: Ти говориш українською? ↑ (no special word needed). Чи ти говориш? — formal/written (optional for A1).
- **Заперечення (Negation)**: Не = not (before verb): Я не знаю. Він не працює. Ми не розуміємо. Не goes directly before the verb — never separated. Review: Я не хочу. Мені не подобається. (from M15, M18); Ні = no (standalone) / nothing, nobody (with pronouns): Ні, я не знаю. (No, I don't know.) Нічого (nothing), ніхто (nobody), ніколи (never), ніде (nowhere). Double negation is REQUIRED in Ukrainian: Я нічого не знаю. (literally: I nothing don't know = I don't know anything.) Ніхто не говорить. (Nobody speaks.) — unlike English, both не and ні- are needed.
- **Підсумок — Summary**: Questions: Хто? Що? Де? Куди? Коли? Чому? Як? Yes/no: intonation only (Ти знаєш? ↑) Negation: не before verb (Я не знаю). Double negation: Ніхто не знає. Я нічого не бачу. Self-check: Ask 3 questions about a friend (Де...? Що...? Коли...?). Make 2 negative sentences (Я не... / Ніхто не...).

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
