<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 46: Holidays (A1, A1.7 [Communication])

## Plan vocabulary to verify

- свято (holiday, n)
- святкувати (to celebrate)
- Різдво (Christmas, n)
- Великдень (Easter, m)
- Новий рік (New Year)
- вітати (to congratulate/greet)
- кутя (kutia, f)
- колядка (carol, f)
- писанка (decorated Easter egg, f)
- паска (Easter bread, f)
- парад (parade, m)
- прапор (flag, m)
- вишиванка (embroidered shirt, f)
- незалежність (independence, f)
- салют (fireworks, m)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Before Christmas: — Коли в тебе Різдво? — Двадцять п'ятого грудня. А в тебе? — У нас — теж! Раніше святкували сьомого січня, але тепер — двадцять п'ятого. — Що ви робите на Різдво? — Ми співаємо колядки і їмо кутю. — Як гарно! З Різдвом! — З Різдвом Христовим! Різдво vocabulary: колядки (carols), кутя (kutia — ritual dish), святкувати.; Dialogue 2 — Independence Day: — Двадцять четверте серпня — День Незалежності! — Так, це головне державне свято України. — Що ви робите? — Ми дивимося парад і ходимо на концерт. — А ввечері? — Ввечері — салют і святковий вечір з друзями. — З Днем Незалежності! — Слава Україні! National holiday: парад, концерт, салют.
- **Українські свята (Ukrainian Holidays)**: Різдво (Christmas) — December 25: Ukraine moved Christmas from January 7 to December 25 in 2023. January 7 was the Russian Orthodox date; December 25 aligns with Europe. Traditions: Свята вечеря (Holy Supper) on December 24 — 12 страв (12 dishes). кутя (kutia) — wheat porridge with honey and poppy seeds — the first dish. колядки (carols) — traditional Christmas songs. Колядники go door to door.; Великдень (Easter): The biggest religious holiday. Date changes each year (spring). Traditions: писанки (decorated eggs — unique Ukrainian art), паска (Easter bread), святити кошик (blessing the Easter basket at church). Greeting: Христос воскрес! — Воістину воскрес! (Christ is risen! — Indeed risen!)
- **Державні свята (National Holidays)**: День Незалежності — August 24, 1991: Ukraine declared independence from the Soviet Union. The most important державне свято (national holiday). Celebrations: парад (parade), концерти, салют (fireworks), прапори (flags). Greeting: З Днем Незалежності! (Happy Independence Day!) Слава Україні! — Героям слава! (Glory to Ukraine! — Glory to the heroes!); Other holidays to know: Новий рік (New Year) — January 1 — biggest secular celebration. Вишиванковий день (Vyshyvanka Day) — third Thursday of May. Everyone wears вишиванка (embroidered shirt) — symbol of Ukrainian identity. День Конституції (Constitution Day) — June 28. День захисників і захисниць (Defenders' Day) — October 1.
- **Підсумок — Summary**: Holiday greetings pattern: З + instrumental case! З Різдвом! (Merry Christmas!) З Великоднем! (Happy Easter!) З Новим роком! (Happy New Year!) З Днем Незалежності! З днем народження! (Happy birthday!) Pattern: З + [holiday/occasion in instrumental] + ! You already know instrumental from з + noun (кава з молоком). Here it's the same: 'with' the holiday → instrumental. Quick calendar: грудень 25 — Різдво, січень 1 — Новий рік, весна — Великдень, серпень 24 — День Незалежності. Self-check: How do you say 'Merry Christmas' and 'Happy New Year'?

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
