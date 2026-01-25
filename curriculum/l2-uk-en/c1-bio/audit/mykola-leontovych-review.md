# Audit Report: M66 — mykola-leontovych.md
**Level:** C1 | **Module:** M66 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:27:21

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
| 1 | quiz | «Геній Миколи Леонтовича» | 12 | 5 | ✅ |
| 2 | fill-in | «Музична термінологія композитора» | 12 | 6 | ✅ |
| 3 | error-correction | «Граматика в життєписі митця» | 12 | 5 | ✅ |
| 4 | match-up | «Світ музики та фольклору» | 12 | 6 | ✅ |
| 5 | select | «Лінгвістичний аналіз музичного генія» | 5 | 5 | ✅ |
| 6 | true-false | «Історична правда про композитора» | 12 | 5 | ✅ |
| 7 | reading | «Музичний аналіз «Щедрика»» | 3 | 1 | ✅ |
| 8 | reading | «Розслідування вбивства генія» | 3 | 1 | ✅ |
| 9 | essay-response | «Магія звуку та вічність пам'яті» | 1 | 1 | ✅ |
| 10 | comparative-study | «Два Миколи: Лисенко та Леонтович» | 1 | 1 | ✅ |
| 11 | critical-analysis | «Аналіз структури магічного Щедрика» | 1 | 1 | ✅ |
| 12 | unjumble | «Відновлення музичних тез» | 12 | 5 | ✅ |
| 13 | translate | «Музичний словник» | 12 | 5 | ✅ |
| 14 | mark-the-words | «Пошук хорових термінів та понять» | 10 | 5 | ✅ |

**Summary:**
- Total activities: 14 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 5/6 (comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 5/6 (essay-response, fill-in, match-up, quiz, reading) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in mykola-leontovych.yaml: Schema validation error at key '7': {'type': 'reading', 'title': '«Розслідування вбивства генія»', 'resource': {'type': 'article', 'url': 'https://www.istpravda.com.ua/articles/2011/01/21/17345/', 'title': '«Убивство Леонтовича: Справа чекіста Грищенка»'}, 'tasks': ['«Які докази причетності ДПУ до вбивства Леонтовича наводяться в статті?»', '«Як родина композитора намагалася зберегти правду про ту страшну ніч?»', '«Порівняйте радянську версію подій із даними відкритих архівів.»']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ❌ 1937/4000 (raw: 2159)
- **Activities:** ✅ 14/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 14 (target 3-9)
- **Immersion:** 🇺🇦 99.2% (target 95-100% (biography))
- **Richness:** ✅ 100% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 100% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 6 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 7 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 6 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 9 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 76 | Included in Core |
| **Вступ** | ✅ | 223 | Included in Core |
| **Життєпис** | ⚪️ | 797 | Skipped |
| **Внесок** | ⚪️ | 176 | Skipped |
| **Спадщина** | ⚪️ | 384 | Skipped |
| **Порівняльний аналіз** | ✅ | 115 | Included in Core |
| **Підсумок** | ✅ | 69 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 97 | Skipped |
| **Вправи** | ⚪️ | 0 | Skipped |
| **Словник** | ⚪️ | 0 | Skipped |