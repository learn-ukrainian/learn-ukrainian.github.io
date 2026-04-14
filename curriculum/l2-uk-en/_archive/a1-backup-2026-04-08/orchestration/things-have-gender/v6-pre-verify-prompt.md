<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 8: Things Have Gender (A1, A1.2 [My World])

## Plan vocabulary to verify

- стіл (table, m)
- книга (book, f)
- вікно (window, n)
- кімната (room, f)
- ліжко (bed, n)
- стілець (chair, m)
- лампа (lamp, f)
- телефон (phone, m)
- комп'ютер (computer, m)
- він, вона, воно (he, she, it — gender test words)
- зошит (notebook, m)
- ручка (pen, f)
- сумка (bag, f)
- крісло (armchair, n)
- дзеркало (mirror, n)
- ключ (key, m)
- фото (photo, n)
- стіна (wall, f)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Video call showing your room: — Привіт! Дивись, це моя кімната. — Класно! У тебе є стіл? — Так, у мене є стіл і ліжко. Gender emerges naturally through мій стіл (m), моя кімната (f), моє ліжко (n).; Dialogue 2 — What's in your bag? — Що у тебе є? — У мене є книга, телефон і фото. — А у мене є ручка і зошит.
- **Він, вона, воно (The Gender Test)**: Пономарова Grade 3 p.86: Ukrainian nouns have gender. Test: can you replace the noun with він, вона, or воно? Чоловічий рід (masculine): стіл — він. Можна додати: мій стіл. Жіночий рід (feminine): книга — вона. Можна додати: моя книга. Середній рід (neuter): вікно — воно. Можна додати: моє вікно.; Вашуленко Grade 3 p.112 — endings by gender: Masculine: usually ends in consonant — стіл, телефон, зошит. Feminine: usually ends in -а or -я — книга, лампа, кімната, ручка. Neuter: usually ends in -о or -е — вікно, ліжко, крісло, місто. This covers ~90% of nouns. Exceptions (like -ь words) come later.
- **Предмети навколо (Objects Around Us)**: Room vocabulary organized by gender: Masculine: стіл (table), стілець (chair), телефон (phone), комп'ютер (computer), зошит (notebook), ключ (key). Feminine: книга (book), лампа (lamp), сумка (bag), ручка (pen), кімната (room), стіна (wall). Neuter: вікно (window), ліжко (bed), крісло (armchair), дзеркало (mirror), фото (photo).; Extending У мене є from M06 (family) to objects: У мене є стіл. У мене є книга. У мене є вікно. Same pattern, new vocabulary.
- **Підсумок — Summary**: Gender determination in 3 steps: 1. Say він/вона/воно with the noun — which fits? 2. Check the ending — consonant? -а/-я? -о/-е? 3. Use the right possessive — мій/моя/моє. Self-check: What gender is 'стіл'? What gender is 'книга'? What about 'вікно'? Say 'I have a chair' in Ukrainian.

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
