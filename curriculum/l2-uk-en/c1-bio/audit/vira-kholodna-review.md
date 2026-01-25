# Audit Report: M85 — vira-kholodna.md
**Level:** C1 | **Module:** M85 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:27:31

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
| 1 | quiz | Розуміння тексту: Життя Віри Холодної | 5 | 5 | ✅ |
| 2 | fill-in | Лексика: Кіно, Емоції та Слава | 6 | 6 | ✅ |
| 3 | error-correction | Граматика: Біографічні події | 5 | 5 | ✅ |
| 4 | match-up | Кінематографічний словник | 8 | 6 | ✅ |
| 5 | select | Аналіз емоційного стану | 5 | 5 | ✅ |
| 6 | group-sort | Життєвий шлях Віри Холодної | 12 | 1 | ✅ |
| 7 | true-false | Міфи та правда про зірку | 5 | 5 | ✅ |
| 8 | authorial-intent | Намір автора: Сповідь актриси | 1 | 1 | ✅ |
| 9 | essay-response | Аналіз феномену: Королева екрану | 1 | 1 | ✅ |
| 10 | comparative-study | Порівняння: Холодна та Пікфорд | 1 | 1 | ✅ |
| 11 | critical-analysis | Аналіз міфів про смерть | 1 | 1 | ✅ |
| 12 | translate | Переклад термінів: Кіно та Мистецтво | 5 | 5 | ✅ |
| 13 | reading | Спогади про Віру Холодну | 3 | 1 | ✅ |

**Summary:**
- Total activities: 13 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 6/6 (authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in vira-kholodna.yaml: Schema validation error at key '12': {'type': 'reading', 'title': 'Спогади про Віру Холодну', 'resource': {'type': 'primary_source', 'url': 'https://elib.nlu.org.ua/', 'title': 'Олександр Вертинський: Моя маленька креолка'}, 'tasks': ['Як Вертинський описує першу зустріч з Вірою?', 'Які епітети він використовує для характеристики її зовнішності?', 'Знайдіть у тексті згадку про присвяту пісні.']} is not valid under any of the given schemas
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

- 4 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2246/4000 (raw: 2507)
- **Activities:** ✅ 13/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 13 (target 3-9)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ✅ 95% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 6 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 14 | 3 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 20 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 117 | Included in Core |
| **Вступ** | ✅ | 267 | Included in Core |
| **Біографія** | ⚪️ | 739 | Skipped |
| **Сучасний контекст** | ✅ | 191 | Included in Core |
| **Історичний контекст** | ✅ | 271 | Included in Core |
| **Порівняльний аналіз** | ✅ | 185 | Included in Core |
| **Підсумок** | ✅ | 133 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 213 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 130 | Skipped |