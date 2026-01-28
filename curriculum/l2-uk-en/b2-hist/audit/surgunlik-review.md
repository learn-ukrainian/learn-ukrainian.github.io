# Audit Report: M111 — surgunlik.md
**Level:** B2 | **Module:** M111 | **Phase:** HIST.10 | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 10/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-27 23:39:00

## Configuration
**Type:** B2-history
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥2 types required
**Priority Types:** comparative-study, critical-analysis, essay-response, reading
**Required Types:** essay-response, reading
**Engagement:** ≥5 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥20 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | essay-response | Ваша думка | 1 | 1 | ✅ |
| 2 | comparative-study | Порівняння політики | 1 | 1 | ✅ |
| 3 | true-false | Виберіть правильні твердження | 8 | 8 | ✅ |
| 4 | true-false | Правда чи неправда | 8 | 8 | ✅ |
| 5 | true-false | Мовні особливості тексту | 8 | 8 | ✅ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 3 (minimum: 2) ✅
- Priority types used: 2/4 (comparative-study, essay-response) ✅
- Required types used: 1/2 (essay-response) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in surgunlik.yaml: Schema validation error at key '4': {'type': 'true-false', 'items': [{'correct': True, 'statement': 'Текст використовує публіцистичний стиль для висвітлення історичних подій'}, {'correct': True, 'statement': 'У тексті часто вживаються дієслова у формі минулого часу'}, {'correct': True, 'statement': 'Текст містить багато емоційно забарвлених прикметників для підсилення трагізму'}, {'correct': False, 'statement': 'У тексті відсутні будь-які терміни політичного чи правового характеру'}, {'correct': True, 'statement': 'Автор використовує пасивні конструкції для опису дій режиму'}, {'correct': True, 'statement': 'У тексті вжито цитати з первинних джерел для підтвердження фактів'}, {'correct': False, 'statement': 'У тексті переважають прості непоширені речення'}, {'correct': True, 'statement': 'Текст містить риторичні запитання для залучення читача'}], 'title': 'Мовні особливості тексту', 'instruction': 'Визначте, чи є твердження правильним.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2011/4000 (raw: 2152)
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 3/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 12/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 96.0% (target 90-100% (history))
- **Richness:** ✅ 97% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 10/10 (High)

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 11 | 3 | 100% | 24% | 23.8% |
| engagement | 12 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Sürgünlik: Депортація 1944** | ⚪️ | 162 | Skipped |
| **Читання** | ✅ | 252 | Included in Core |
| **Історичний наратив: Трагедія Sürgünlik** | ⚪️ | 866 | Skipped |
| **Первинні джерела** | ✅ | 266 | Included in Core |
| **Деколонізаційний погляд** | ✅ | 289 | Included in Core |
| **Підсумок** | ✅ | 66 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |