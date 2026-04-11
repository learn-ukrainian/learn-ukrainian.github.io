<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 74: Контрольна робота 6 (B1, B1.6 [Participles & Gerunds])

## Plan vocabulary to verify

- контрольна робота (test/assessment)
- дієприкметник (participle)
- дієприслівник (gerund/adverbial participle)
- дієприкметниковий зворот (participle phrase)
- дієприслівниковий зворот (gerund phrase)
- короткий прикметник (short-form adjective)
- одночасність (simultaneity)
- різночасність (temporal non-simultaneity)
- самооцінка (self-assessment)
- повторення (review)
- перевірка (check/verification)
- впевнено (confidently)

## Sections to research

- **Вступ: як працювати з контрольною**: Overview: this checkpoint tests everything from M57-M64 (Phase 7): активні дієприкметники (M57), пасивні дієприкметники (M58), дієприкметниковий зворот (M59), короткі прикметники (M60), дієприслівники недоконаного виду (M61), дієприслівники доконаного виду (M62), дієприслівниковий зворот (M63), освіта (M64).; Self-assessment framework: after each block, rate confidence: впевнено / потребую повторення / не розумію.
- **Блок 1: Дієприкметники**: Formation exercise: form active and passive participles from 12 verbs. Learners must choose correct suffix and apply consonant alternations: квітнути → ?, носити → ?, прочитати → ?, зів'яти → ?, побачити → ?, мити → ?, закрутити → ?, робити → ?; Classification: given 10 participles, classify as активний теперішній, активний минулий, or пасивний. Then determine whether each active present participle is natural Ukrainian or a Russian calque.; Russian calque editing: rewrite 6 phrases replacing unnatural participles with natural Ukrainian equivalents (descriptions, adjectives, descriptive clauses).
- **Блок 2: Звороти і пунктуація**: Punctuation exercise: 10 sentences with дієприкметникові and дієприслівникові звороти — learners place all commas correctly. Include edge cases: preposed participle phrases, pronoun referents, phraseological gerund expressions.; Classification: identify whether each phrase is дієприкметниковий (означення) or дієприслівниковий (обставина) and state the rule that determines comma placement.; Transformation: convert 6 participle/gerund phrases to subordinate clauses with який/коли/після того як, and vice versa.
- **Блок 3: Дієприслівники**: Formation: form imperfective and perfective gerunds from 10 verbs. Include reflexive verbs. Learners must choose correct suffix (-учи/-ючи/-ачи/-ячи vs -вши/-ши).; Temporal logic: given 8 sentence contexts, learners choose imperfective (одночасність) or perfective (різночасність) gerund.; Logical subject check: identify and fix 4 dangling gerund errors.
- **Блок 4: Короткі прикметники**: Identification: find short-form adjectives in 5 literary/folk excerpts and give their full forms.; Modern usage: complete 6 sentences with correct short-form adjective (потрібен/певен/годен/ладен/варт/рад) in predicative position.
- **Блок 5: Освіта та академічний стиль**: Academic vocabulary: match 10 academic terms to definitions.; Register transformation: rewrite 5 informal sentences about university life in academic register using participle phrases and gerund constructions.; Reading comprehension: a short academic passage using Phase 7 grammar. Questions test language: identify all дієприкметники, звороти, стиль.
- **Блок 6: Інтегроване завдання**: Cloze passage: an academic text with 10 blanks. Learners fill in correct participle/gerund forms, choosing between active/passive, imperfective/perfective, with correct agreement and punctuation.; Production: write a short paragraph (5-7 sentences) describing a research project or study experience, using at least 2 participle phrases, 2 gerund phrases, and 1 short-form adjective.
- **Підсумок та самооцінка**: Self-assessment checklist: Дієприкметники: Чи правильно я утворюю активні й пасивні форми? Звороти: Чи правильно я ставлю розділові знаки? Дієприслівники: Чи розрізняю одночасність і різночасність? Короткі прикметники: Чи вживаю потрібен/певен/годен правильно? Освіта: Чи можу я говорити про навчання науковим стилем?; Recommendations: if any block scores below 70%, return to the corresponding module. Phase 8 (Complex Syntax) builds on this foundation to construct multi-clause sentences.

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (B1).

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
