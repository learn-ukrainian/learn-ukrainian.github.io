# Audit Report: M06 — volodymyr-monomakh.md
**Level:** C1-BIO | **Module:** M06 | **Phase:** C1 | **Pedagogy:** seminar | **Target:** 4300
**Naturalness:** 0/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-07 10:55:09

## Configuration
**Type:** C1-biography
**Word Target:** 4300 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** comparative-study, critical-analysis, decolonization-debate, essay-response, linguistic-analysis, reading-comprehension, source-analysis
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | reading | Уривки з «Повчання дітям» Володимира Мономаха | 4 | 1 | ✅ |
| 2 | critical-analysis | Аналіз етичного кодексу | 1 | 1 | ✅ |
| 3 | essay-response | Есе: Образ філософа на престолі | 1 | 1 | ✅ |
| 4 | comparative-study | Порівняльне дослідження: Мономах та Марк Аврелій | 1 | 1 | ✅ |
| 5 | critical-analysis | Юридичний аналіз Статуту | 1 | 1 | ✅ |
| 6 | select | Вибір контексту: Русь XI-XII ст. | 3 | 5 | ❌ |
| 7 | true-false | Деколонізація: Факти vs Міфи | 10 | 5 | ✅ |
| 8 | reading | Постанова Любецького з'їзду | 3 | 1 | ✅ |

**Summary:**
- Total activities: 8 (target: 3-9) ✅
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 3/7 (comparative-study, critical-analysis, essay-response) ❌
- Low density activities: 1

## PEDAGOGICAL VIOLATIONS
- **[HISTORICAL_CHARS_IN_MODERN]** Found historical Cyrillic characters outside quote context: ѣ (lines: [57])
  - FIX: Remove historical characters from modern Ukrainian prose, or use [!quote] callout for authentic historical quotes.
- **[COMPLEXITY]** select 'Вибір контексту: Русь XI-XII ст.' has 3 items (minimum: 5)
  - FIX: Add more items. C1 select requires at least 5 items.
- **[INVALID_META_YAML]** Meta YAML Schema Violation at 'vocabulary_hints': ['міжусобиці', 'коаліція', 'повчання', 'отчина', 'лихварство', 'закуп', 'смерд', 'статут', 'каяття', 'християнська етика'] is not of type 'object'
  - FIX: Correct the YAML structure to match schemas/meta-module.schema.json
- **[INVALID_ACTIVITY_TYPE]** Invalid activity types in activity_hints: ['reading-comprehension', 'linguistic-analysis', 'decolonization-debate', 'source-analysis']. Valid types: ['match-up', 'fill-in', 'quiz', 'true-false', 'group-sort', 'unjumble', 'error-correction', 'anagram', 'select', 'translate', 'cloze', 'mark-the-words', 'reading', 'essay-response', 'critical-analysis', 'comparative-study', 'authorial-intent', 'creative-writing', 'etymology-trace', 'transcription', 'grammar-identify', 'paleography-analysis', 'dialect-comparison', 'translation-critique', 'phonology-lab', 'grammar-lab', 'parallel-text', 'historical-writing', 'register-identify', 'loanword-trace', 'comparative-style']
  - FIX: Replace invalid types with valid ones from: match-up, fill-in, quiz, true-false, group-sort, unjumble, error-correction, anagram, select, translate, cloze, mark-the-words, reading, essay-response, critical-analysis, comparative-study, authorial-intent, creative-writing, etymology-trace, transcription, grammar-identify, paleography-analysis, dialect-comparison, translation-critique, phonology-lab, grammar-lab, parallel-text, historical-writing, register-identify, loanword-trace, comparative-style
- **[HISTORICAL_CHARS_IN_MODERN]** Found historical Cyrillic characters outside quote context: ѣ (lines: [57])
  - FIX: Move historical text into a blockquote (> ) to mark it as a primary source quote.
- **[YAML_SCHEMA_VIOLATION]** Schema error in volodymyr-monomakh.yaml: Schema validation error at key 'id': 'matching-quotes' does not match '^reading-[a-z0-9-]+$'
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 6 violations (moderate)
- Activity density below minimum

## Gates
- **Words:** ❌ 4187/4300 (raw: 4308)
- **Activities:** ✅ 8/3
- **Density:** ❌ 1 < 1
- **Unique_types:** ✅ 6/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 3/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 22 < 24 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 6 violations
- **Content_heavy:** ✅ Content-heavy OK (8 activities)
- **Immersion:** 🇺🇦 99.7% (target 95-100% (biography))
- **Richness:** ❌ 87% < 95% min (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ Not scored

## Richness Details
**Score:** 87% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 15 | 4 | 100% | 19% | 19.0% |
| engagement | 2 | 6 | 33% | 14% | 4.7% |
| quotes | 15 | 3 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 3 | 4 | 75% | 10% | 7.1% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 3 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **87.9%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Вибір контексту: Русь XI-XII ст. | select | 3 | 5 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 76 | Included in Core |
| **Вступ: Моральна криза та Любецький з’їзд** | ✅ | 534 | Included in Core |
| **Життєпис: Шлях від Переяслава до Києва** | ⚪️ | 634 | Skipped |
| **Битва на Сальниці: Тріумф коаліційної стратегії** | ⚪️ | 530 | Skipped |
| **«Повчання дітям»: Перший політичний маніфест Русі** | ⚪️ | 824 | Skipped |
| **Деколонізація: Київський центр vs московські міфи** | ⚪️ | 599 | Skipped |
| **Мономах та інтелектуальне середовище: Лавра, Сильвестр та Нестор** | ⚪️ | 328 | Skipped |
| **Спадщина та уроки для сучасності** | ⚪️ | 284 | Skipped |
| **Підсумок** | ✅ | 207 | Included in Core |
| **Додаток: Ключові терміни та поняття епохи Мономаха (для C1 аналізу)** | ✅ | 171 | Included in Core |