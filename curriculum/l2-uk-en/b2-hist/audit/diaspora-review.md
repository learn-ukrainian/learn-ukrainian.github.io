# Audit Report: M118 — diaspora.md
**Level:** B2 | **Module:** M118 | **Phase:** HIST.11 | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 10/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-27 15:51:36

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
| 1 | true-false | Визначте, чи є твердження правдивими. | 8 | 8 | ✅ |
| 2 | true-false | Виберіть правильні відповіді | 8 | 8 | ✅ |
| 3 | essay-response | Ваша думка | 1 | 1 | ✅ |
| 4 | comparative-study | Роль діаспори та материка | 1 | 1 | ✅ |
| 5 | true-false | Які мовні засоби використовуються в тексті для опису ролі діаспори? | 8 | 8 | ✅ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 3 (minimum: 2) ✅
- Priority types used: 2/4 (comparative-study, essay-response) ✅
- Required types used: 1/2 (essay-response) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in diaspora.yaml: Schema validation error at key '4': {'type': 'true-false', 'title': 'Які мовні засоби використовуються в тексті для опису ролі діаспори?', 'instruction': 'Визначте, чи використовується цей засіб.', 'items': [{'statement': 'Метафора «ковчег» для позначення рятівної місії.', 'correct': True}, {'statement': 'Урочиста лексика (клейноди, святиня, місія).', 'correct': True}, {'statement': 'Використання жаргонізмів та сленгу.', 'correct': False}, {'statement': 'Історичні терміни (Директорія, УНР, екзил).', 'correct': True}, {'statement': 'Емоційно забарвлені слова (плакали, надія, гідність).', 'correct': True}, {'statement': 'Науковий стиль без емоцій.', 'correct': False}, {'statement': 'Риторичні запитання для привернення уваги.', 'correct': True}, {'statement': 'Велика кількість запозичень з англійської мови.', 'correct': False}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2054/4000 (raw: 2215)
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 3/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 20/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 96.9% (target 90-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 10/10 (High)

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 15 | 3 | 100% | 24% | 23.8% |
| engagement | 20 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 19 | 4 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 0.98 | - | 98% | 5% | 4.7% |
| questions | 5 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Діаспора: Ковчег Держави** | ⚪️ | 90 | Skipped |
| **Читання** | ✅ | 178 | Included in Core |
| **Уряд УНР в екзилі** | ⚪️ | 253 | Skipped |
| **Діаспорні інституції** | ⚪️ | 833 | Skipped |
| **Передача клейнодів** | ⚪️ | 198 | Skipped |
| **Первинні джерела** | ✅ | 183 | Included in Core |
| **Деколонізаційний погляд** | ✅ | 154 | Included in Core |
| **Підсумок** | ✅ | 55 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |