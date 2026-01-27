# Audit Report: M61 — ahatanhel-krymskyi.md

**Level:** C1 | **Module:** M61 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:27

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
| 1 | quiz | Розуміння біографії Кримського | 5 | 5 | ✅ |
| 2 | match-up | Терміни та визначення | 8 | 6 | ✅ |
| 3 | cloze | Життя та трагедія Кримського | 12 | 1 | ✅ |
| 4 | true-false | Факти про Кримського | 5 | 5 | ✅ |
| 5 | fill-in | Заповніть пропуски | 6 | 6 | ✅ |
| 6 | select | Виберіть правильні твердження | 5 | 5 | ✅ |
| 7 | error-correction | Виправте помилки | 5 | 5 | ✅ |
| 8 | unjumble | Складіть речення про Кримського | 5 | 5 | ✅ |
| 9 | group-sort | Класифікація понять | 12 | 1 | ✅ |
| 10 | comparative-study | Порівняння долі Кримського та Вернадського | 1 | 1 | ✅ |
| 11 | essay-response | Письмове завдання | 1 | 1 | ✅ |
| 12 | mark-the-words | Знайдіть терміни зі сходознавства та репресій | 8 | 5 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 12 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (100% overlap): "Його праці перевидають, його ім'я повертається в наукове життя.". Shares significant keywords with sentence at index 114.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[YAML_SCHEMA_VIOLATION]** Schema error in ahatanhel-krymskyi.yaml: Schema validation error at key 'words': ['ЮНЕСКО', 'включило', "ім'я", 'Кримського', 'до', 'списку', 'видатних', 'діячів', 'світу', 'в', '1970', 'році', 'посмертно', '.'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation

**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 2137/4000 (raw: 2364)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 12/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 12/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9); 1 cloze with year blanks
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 9 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 4 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 11 | 2 | 100% | 10% | 9.5% |
| variety | 0.92 | - | 92% | 5% | 4.4% |
| paragraph_var | 0.52 | - | 52% | 5% | 2.5% |
| questions | 6 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.3%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Вступ** | ✅ | 89 | Included in Core |
| **Життєпис** | ⚪️ | 1136 | Skipped |
| **Внесок** | ⚪️ | 414 | Skipped |
| **Порівняльний аналіз** | ✅ | 238 | Included in Core |
| **Підсумок** | ✅ | 221 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 39 | Skipped |
