<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 14: Checkpoint: My World (A1, A1.2 [My World])

## Plan vocabulary to verify

(No vocabulary hints in plan)

## Sections to research

- **Що ми знаємо? (What Do We Know?)**: Self-check covering M08-M13: Can you determine noun gender? (M08) Can you describe things with adjectives? (M09) Can you name colors, including both blues? (M10) Can you count and say prices? (M11) Can you say 'this' and 'that'? (M12) Can you make things plural? (M13)
- **Читання (Reading Practice)**: A short Ukrainian text (8-10 sentences) using ONLY vocabulary from M08-M13. No new words. The learner reads aloud. Content: describing a room — objects, colors, prices, pointing at things. Example: Це моя кімната. Мій стіл великий і новий. Ця лампа біла, а та — жовта. У мене є три книги. Ці книги нові. Стіни білі.
- **Граматика (Grammar Summary)**: Key patterns from A1.2: 1. Gender: він/вона/воно test + endings (consonant/−а,−я/−о,−е) 2. Agreement: великий стіл, велика книга, велике вікно 3. Hard vs soft stem: червоний (-ий) vs синій (-ій) 4. Demonstratives: цей/ця/це, той/та/те 5. Plurals: столи, книги, вікна; adjective always -і 6. Numbers: as vocabulary (no morphology)
- **Діалог (Connected Dialogue)**: A complete conversation combining all A1.2 skills: Shopping scenario — choosing items, describing what you want, asking prices. Uses gender agreement, colors, demonstratives, numbers, and plurals. — Добрий день! У вас є сумки? — Так! Ця червона чи та синя? — Та синя. Скільки вона коштує? — Двісті гривень. — Добре. А ці зошити? Скільки коштує один зошит? — Двадцять гривень.
- **Підсумок — Summary**: A1.2 achievement summary: You can now describe your world in Ukrainian. You know 20+ objects with their genders. You can describe them (big, new, red, blue). You can count and talk about prices. You can point at things (this/that). You can talk about groups (plurals). Next: A1.3 — Actions (verbs, what you do and like).

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
