# Audit Report: M47 — yevhen-chykalenko.md
**Level:** C1 | **Module:** M47 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:20

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
| 1 | quiz | Розуміння постаті Євгена Чикаленка | 8 | 5 | ✅ |
| 2 | fill-in | Термінологія меценатства та економіки | 8 | 6 | ✅ |
| 3 | error-correction | Граматичні конструкції в історичному тексті | 8 | 5 | ✅ |
| 4 | match-up | Словник мецената та аграрія | 12 | 6 | ✅ |
| 5 | select | Аналіз риторики мецената | 9 | 5 | ✅ |
| 6 | unjumble | Концепції національного меценатства | 8 | 5 | ✅ |
| 7 | cloze | Філософія дії Євгена Чикаленка | 16 | 1 | ✅ |
| 8 | true-false | Міфи та факти про Чикаленка | 8 | 5 | ✅ |
| 9 | group-sort | Галузі впливу Євгена Чикаленка | 15 | 1 | ✅ |
| 10 | comparative-study | Чикаленко та Франко - Тандем духу та ресурсу | 1 | 1 | ✅ |
| 11 | reading | Аналіз меценатської етики Чикаленка | 3 | 1 | ✅ |
| 12 | reading | Епістолярна спадщина мецената | 3 | 1 | ✅ |
| 13 | authorial-intent | Наміри Чикаленка у «Щоденнику» | 1 | 1 | ✅ |
| 14 | essay-response | «Феномен українського меценатства — Від Чикаленка до сьогодні» | 1 | 1 | ✅ |

**Summary:**
- Total activities: 14 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 5/6 (authorial-intent, comparative-study, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in yevhen-chykalenko.yaml: Schema validation error at key '11': {'type': 'reading', 'title': 'Епістолярна спадщина мецената', 'resource': {'type': 'primary_source', 'url': 'https://shron1.chtyvo.org.ua/Chykalenko_Yevhen/Lysty_do_M_Hrushevskoho.pdf', 'title': '«Листи Євгена Чикаленка до Михайла Грушевського»'}, 'tasks': ['«Проаналізуйте офіційно-ввічливий стиль звертань, який використовує Чикаленко у листуванні з видатним істориком.»', "«Які практичні питання видавничої справи обговорюються у листах? Випишіть терміни, пов'язані з друкарством та поширенням газет.»", "«Знайдіть у листах приклади емоційної напруги, пов'язаної з труднощами фінансування українських проектів.»"]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Спадщина|Вплив' found: Вплив на сучасників, Спадщина
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation
**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 1939/4000 (raw: 2170)
- **Activities:** ✅ 14/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 14 (target 3-9)
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
| primary_sources | 4 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 8 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 5 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 11 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 89 | Included in Core |
| **Вступ** | ✅ | 210 | Included in Core |
| **Життєпис** | ⚪️ | 399 | Skipped |
| **Внесок** | ⚪️ | 453 | Skipped |
| **Спадщина** | ⚪️ | 179 | Skipped |
| **Історичний контекст** | ✅ | 299 | Included in Core |
| **Порівняльний аналіз** | ✅ | 129 | Included in Core |
| **Підсумок** | ✅ | 166 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 15 | Skipped |