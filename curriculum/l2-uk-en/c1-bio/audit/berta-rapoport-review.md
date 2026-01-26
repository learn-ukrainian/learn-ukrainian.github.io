# Audit Report: M88 — berta-rapoport.md
**Level:** C1 | **Module:** M88 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:43

## Configuration
**Type:** C1-biography
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** essay-response, fill-in, group-sort, match-up, quiz, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Розуміння тексту: Капітанка Рапопорт | 5 | 5 | ✅ |
| 2 | fill-in | Лексика: Море, Професія та Рівність | 6 | 6 | ✅ |
| 3 | error-correction | Граматика: Опис морських подорожей | 5 | 5 | ✅ |
| 4 | match-up | Морська термінологія | 8 | 6 | ✅ |
| 5 | select | Лінгвістичний аналіз морської цитати | 5 | 5 | ✅ |
| 6 | group-sort | Класифікація професійного шляху | 12 | 1 | ✅ |
| 7 | true-false | Факти про Берту Рапопорт | 5 | 5 | ✅ |
| 8 | authorial-intent | Намір автора: Маніфест капітанки | 1 | 1 | ✅ |
| 9 | essay-response | Аналіз бар’єрів: Берта Рапопорт | 1 | 1 | ✅ |
| 10 | comparative-study | Порівняння: Рапопорт та Щетиніна | 1 | 1 | ✅ |
| 11 | critical-analysis | Аналіз «Морського забобону» | 1 | 1 | ✅ |
| 12 | translate | Переклад термінів: Море та Кар’єра | 5 | 5 | ✅ |
| 13 | reading | Морський статут та етика | 3 | 1 | ✅ |

**Summary:**
- Total activities: 13 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 6/6 (authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (100% overlap): "Вона назавжди залишиться нашою першою Капітанкою, яка веде Україну крізь тумани історії до берегів с...". Shares significant keywords with sentence at index 57.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[YAML_SCHEMA_VIOLATION]** Schema error in berta-rapoport.yaml: Schema validation error at key '12': {'type': 'reading', 'title': 'Морський статут та етика', 'resource': {'type': 'primary_source', 'url': 'https://zakon.rada.gov.ua/', 'title': 'Кодекс торговельного мореплавства України'}, 'tasks': ['Знайдіть у тексті обов’язки капітана судна.', 'Які терміни використовуються для опису аварійних ситуацій?', 'Поясніть значення слова «фрахтування».']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 35/100)

- 5 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2060/4000 (raw: 2296)
- **Activities:** ✅ 13/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ⚠️ Too many activities: 13 (target 3-9)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 7 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 7 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.96 | - | 96% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 14 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.4%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 114 | Included in Core |
| **Вступ** | ✅ | 235 | Included in Core |
| **Біографія** | ⚪️ | 938 | Skipped |
| **Історичний контекст** | ✅ | 365 | Included in Core |
| **Порівняльний аналіз** | ✅ | 173 | Included in Core |
| **Підсумок** | ✅ | 120 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 115 | Skipped |