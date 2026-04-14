<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 9: What Is It Like? (A1, A1.2 [My World])

## Plan vocabulary to verify

- який, яка, яке (what kind? — m/f/n)
- великий (big)
- маленький (small)
- новий (new)
- старий (old)
- гарний (nice, beautiful)
- чистий (clean)
- дорогий (expensive)
- дешевий (cheap)
- поганий (bad)
- брудний (dirty)
- світлий (light, bright)
- темний (dark)
- а (and/but — contrast)
- але (but)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Describing a room (Вашуленко Grade 3 p.131 'Моя кімната'): — Яка твоя кімната? — Моя кімната велика і світла. — А стіл? — Стіл новий. А ліжко — старе. Adjective agreement emerges from real description.; Dialogue 2 — Shopping (window shopping): — Яка гарна сумка! — Так, але вона дорога. — А телефон? Який він? — Він великий і дешевий.
- **Який? Яка? Яке? (What kind?)**: The question 'What kind?' changes by gender — same pattern as мій/моя/моє: Який стіл? (m) → Великий стіл. Яка книга? (f) → Нова книга. Яке вікно? (n) → Чисте вікно.; Пономарова Grade 3 p.98: Adjective has the same gender as the noun. Masculine: -ий (великий, новий, чистий) Feminine: -а (велика, нова, чиста) Neuter: -е (велике, нове, чисте) Soft-stem adjectives (-ій/-я/-є like синій) come in M10 Colors. This pattern will reappear in every case — learn it well now.
- **Прикметники (Common Adjectives)**: Taught in pairs (opposites — easier to remember): великий ↔ маленький (big ↔ small) новий ↔ старий (new ↔ old) гарний ↔ поганий (nice/beautiful ↔ bad) чистий ↔ брудний (clean ↔ dirty) дорогий ↔ дешевий (expensive ↔ cheap) світлий ↔ темний (light ↔ dark); Building descriptions with M08 objects: У мене є великий стіл. Моя кімната маленька, але гарна. Вікно велике і чисте. Стілець старий, а ліжко — нове. Note: 'а' = and/but (contrast), 'і' = and (parallel).
- **Підсумок — Summary**: Self-check: What ending does a masculine adjective have? (-ий/-ій) Feminine? (-а/-я) Neuter? (-е/-є) Describe your room in 3 sentences using adjectives.

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
