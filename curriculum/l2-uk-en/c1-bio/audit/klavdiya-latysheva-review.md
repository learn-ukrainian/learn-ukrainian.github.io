# Audit Report: M79 — klavdiya-latysheva.md

**Level:** C1 | **Module:** M79 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:39

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
| 1 | quiz | Розуміння тексту: Життя Клавдії Латишевої | 5 | 5 | ✅ |
| 2 | fill-in | Лексика: Наука та Освіта | 6 | 6 | ✅ |
| 3 | error-correction | Граматика: Біографія вченого | 5 | 5 | ✅ |
| 4 | match-up | Науковий словник | 8 | 6 | ✅ |
| 5 | select | Аналіз ставлення до науки | 5 | 5 | ✅ |
| 6 | group-sort | Науковий шлях Латишевої | 12 | 1 | ✅ |
| 7 | true-false | Факти про жінку-математика | 5 | 5 | ✅ |
| 8 | authorial-intent | Намір автора: Чесність науки | 1 | 1 | ✅ |
| 9 | essay-response | Аналіз успіху: Жінка в науці | 1 | 1 | ✅ |
| 10 | comparative-study | Порівняння: Латишева та Ковалевська | 1 | 1 | ✅ |
| 11 | critical-analysis | Аналіз наукової школи | 1 | 1 | ✅ |
| 12 | translate | Переклад термінів: Наука та Розум | 5 | 5 | ✅ |
| 13 | reading | Жінки в українській науці | 3 | 1 | ✅ |

**Summary:**
- Total activities: 13 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 6/6 (authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in klavdiya-latysheva.yaml: Schema validation error at key '12': {'type': 'reading', 'title': 'Жінки в українській науці', 'resource': {'type': 'article', 'url': 'https://www.nas.gov.ua/', 'title': 'Видатні жінки-вчені України'}, 'tasks': ['Знайдіть у тексті інформацію про науковий внесок Латишевої.', 'Які ще імена жінок-математиків згадуються?', 'Як автор оцінює роль жінок у розвитку кібернетики?']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation

**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 2041/4000 (raw: 2322)
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
- **Immersion:** 🇺🇦 99.7% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 4 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 7 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 8 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.96 | - | 96% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 22 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.4%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 95 | Included in Core |
| **Вступ** | ✅ | 199 | Included in Core |
| **Життєпис** | ⚪️ | 474 | Skipped |
| **Внесок** | ⚪️ | 54 | Skipped |
| **Спадщина** | ⚪️ | 90 | Skipped |
| **Сучасний контекст** | ✅ | 168 | Included in Core |
| **Історичний контекст** | ✅ | 398 | Included in Core |
| **Порівняльний аналіз** | ✅ | 168 | Included in Core |
| **Підсумок** | ✅ | 101 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 171 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 123 | Skipped |
