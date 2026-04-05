# Audit Report: M20 — locative-expanded.md
**Level:** A2 | **Module:** M20 | **Phase:** A2.3 | **Pedagogy:** PPP | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:05:03

## Configuration
**Type:** A2-grammar
**Word Target:** 2000 words
**Activities:** 0-4 required
**Items per Activity:** ≥8 items
**Unique Types:** ≥0 types required
**Priority Types:** cloze, error-correction, fill-in, group-sort, mark-the-words, match-up, observe, odd-one-out, order, quiz, reading, select, translate, true-false, unjumble
**Engagement:** ≥3 callouts
**Immersion:** 0-100%
**Vocab Target:** ≥1 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz |  | 8 | 8 | ✅ |
| 2 | fill-in |  | 8 | 8 | ✅ |
| 3 | match-up |  | 8 | 8 | ✅ |
| 4 | error-correction |  | 8 | 6 | ✅ |

**Summary:**
- Total activities: 4 (target: 0-4) ✅
- Unique types: 4 (minimum: 0) ✅
- Priority types used: 4/15 (error-correction, fill-in, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q4 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[METALANGUAGE]** Metalanguage terms used but not in vocabulary: іменник
  - FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
- **[STRUCTURAL_MONOTONY]** 4 of 5 section openers share >70% lexical overlap. Sections: ## Місце́вий з абстра́ктними іме́нниками; ## Часови́й місцевий відмінок (Temporal ; ## По телефону, по ра́діо: місцевий із п... Opener pattern: "«Чита́ємо украї́нською»..."
  - FIX: Diversify section openings. Each section should start with a unique approach: questions, examples, cultural hooks, direct instruction, comparisons — not the same template.
- **[YAML_SCHEMA_VIOLATION]** Schema error in locative-expanded.yaml: Schema validation error at key '3': {'id': 'error-correction-prepositions', 'type': 'error-correction', 'instruction': 'Знайдіть і виправте помилку в прийменнику', 'items': [{'sentence': 'Я зараз у роботі.', 'error': 'у', 'correction': 'на', 'error_type': 'word', 'options': ['в', 'на', 'по'], 'explanation': 'Зі словом «робота» завжди використовується прийменник «на».'}, {'sentence': 'Ми говорили у телефону.', 'error': 'у', 'correction': 'по', 'error_type': 'word', 'options': ['по', 'на', 'про'], 'explanation': "Засіб зв'язку вимагає прийменника «по» (по телефону)."}, {'sentence': 'На минулому місяці мій брат купив машину.', 'error': 'На', 'correction': 'У', 'error_type': 'word', 'options': ['У', 'В', 'По'], 'explanation': 'З назвами місяців і словом «місяць» використовується прийменник «у» або «в».'}, {'sentence': 'Вони працюють на бізнесі.', 'error': 'на', 'correction': 'у', 'error_type': 'word', 'options': ['в', 'у', 'по'], 'explanation': 'Абстрактні сфери, як-от бізнес чи політика, вимагають «у»/«в».'}, {'sentence': 'У цьому тижні я дуже зайнятий.', 'error': 'У', 'correction': 'На', 'error_type': 'word', 'options': ['На', 'В', 'По'], 'explanation': 'Зі словом «тиждень» завжди використовується прийменник «на».'}, {'sentence': 'Вона дивиться новини про телевізору.', 'error': 'про', 'correction': 'по', 'error_type': 'word', 'options': ['по', 'на', 'у'], 'explanation': "Канал зв'язку (телевізор, радіо) вимагає прийменника «по»."}, {'sentence': 'Я купив свіжий хліб у дорозі додому.', 'error': 'у', 'correction': 'по', 'error_type': 'word', 'options': ['на', 'по', 'в'], 'explanation': 'Процес або шлях подорожі передається виразом «по дорозі».'}, {'sentence': 'Що ти робиш в наступному тижні?', 'error': 'в', 'correction': 'на', 'error_type': 'word', 'options': ['у', 'на', 'по'], 'explanation': 'Зі словом «тиждень» завжди використовується прийменник «на».'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 15/100)

- 4 violations (moderate)

## Gates
- **Words:** ⚠️ 1914/2000 (raw: 2101) (86 short)
- **Activities:** ✅ 4/0
- **Density:** ✅ All > 8
- **Unique_types:** ✅ 4/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 44/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** ❌ 37.0% LOW (target 40-70% (A2.1))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 545 | Included in Core |
| **Часови́й місцевий відмінок (Temporal Locative)** | ✅ | 480 | Included in Core |
| **По телефону, по ра́діо: місцевий із прийме́нником «по» (Locative with "po")** | ✅ | 421 | Included in Core |
| **Місцевий відмінок: від мі́сця до се́нсу (From Place to Meaning)** | ✅ | 468 | Included in Core |