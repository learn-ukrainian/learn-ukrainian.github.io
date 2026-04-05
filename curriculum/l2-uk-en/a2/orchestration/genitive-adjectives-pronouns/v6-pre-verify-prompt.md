<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 13: Мого друга, цієї книги (A2, A2.2 [Genitive Case Complete])

## Plan vocabulary to verify

- прикметник (adjective)
- займенник (pronoun)
- присвійний (possessive)
- вказівний (demonstrative)
- узгодження (agreement (grammatical))
- дозвіл (permission)
- підручник (textbook)
- документ (document)
- вчителька (female teacher)
- важливий (important)
- молодий (young)
- старший (older, elder)
- дівчина (girl, young woman)
- олівець (pencil)

## Sections to research

- **Який? Якого? Прикметники в родовому (Which? Whose? Adjectives in the Genitive)**: Masculine and neuter Genitive adjective endings: -ого for hard stems (нового друга, нового міста), -ього for soft stems (синього олівця, синього моря).; Feminine Genitive adjective endings: -ої for hard stems (нової книги), -ьої for soft stems (синьої сукні).; Agreement in full phrases: без нового підручника (masc.), без нової книги (fem.), біля нового будинку (masc.), біля старої церкви (fem.).
- **Мого, твого, нашого: присвійні займенники (Мого, твого, нашого: Possessive Pronouns)**: Masculine/neuter Genitive forms: мого, твого, його (unchanged), нашого, вашого, їхнього. Examples: для мого брата, біля нашого будинку, без твого дозволу.; Feminine Genitive forms: моєї, твоєї, її (unchanged), нашої, вашої, їхньої. Examples: від моєї сестри, для нашої вчительки, біля вашої школи.; Note: його and її do not change for case when they are possessives (його книга → його книги; її сумка → її сумки). But їхній declines like a soft-group adjective: їхнього друга (gen masc), їхньої школи (gen fem), їхнього міста (gen neut).
- **Цього, того: вказівні займенники та повні фрази (Цього, того: Demonstratives and Full Phrases)**: Masculine/neuter Genitive demonstratives: цього (this), того (that). Examples: біля цього будинку, після того дня, від цього вчителя.; Feminine Genitive demonstratives: цієї (this), тієї (that). Examples: для цієї дівчини, навпроти тієї школи, без тієї книги.; Full noun phrases with multiple modifiers: біля цього нового ринку, для моєї старшої сестри, без того важливого документа. Word order: demonstrative + possessive/adjective + noun.

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A2).

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
