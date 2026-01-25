# Audit Report: M107 — upa.md
**Level:** B2 | **Module:** M107 | **Phase:** B2.3c | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 20:23:10

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
| 1 | quiz | Розуміння тексту: Контекст та стратегія | 11 | 8 | ✅ |
| 2 | fill-in | Лексика в контексті: Збройний опір | 10 | 8 | ✅ |
| 3 | match-up | Історична термінологія | 12 | 8 | ✅ |
| 4 | essay-response | Ваша думка | 1 | 1 | ✅ |
| 5 | comparative-study | Порівняння підпілля | 1 | 1 | ✅ |
| 6 | true-false | Правда чи хибність: Факти про УПА | 10 | 8 | ✅ |
| 7 | error-correction | Виправте граматичні помилки | 7 | 6 | ✅ |
| 8 | group-sort | Категоризація термінів | 20 | 1 | ✅ |
| 9 | unjumble | Складіть речення | 8 | 6 | ✅ |
| 10 | cloze | Текст: Феномен криївки | 20 | 1 | ✅ |
| 11 | select | Аналіз деколонізації | 6 | 6 | ✅ |
| 12 | mark-the-words | Знайдіть дієслова минулого часу | 7 | 6 | ✅ |
| 13 | translate | Перекладіть правильно | 6 | 6 | ✅ |
| 14 | quiz | Аналітичний квіз: Постаті | 8 | 8 | ✅ |
| 15 | mark-the-words | Знайдіть географічні назви | 9 | 6 | ✅ |

**Summary:**
- Total activities: 15 (target: 3-9) ❌
- Unique types: 13 (minimum: 2) ✅
- Priority types used: 2/4 (comparative-study, essay-response) ✅
- Required types used: 1/2 (essay-response) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in upa.yaml: Schema validation error at key '12': {'type': 'translate', 'title': 'Перекладіть правильно', 'items': [{'source': 'They fought on two fronts.', 'options': [{'text': 'Вони воювали на два фронти.', 'correct': True}, {'text': 'Вони воювали на двох фронтів.', 'correct': False}, {'text': 'Вони воював на два фронти.', 'correct': False}]}, {'source': 'The leader of the organization.', 'options': [{'text': 'Провідник організації.', 'correct': True}, {'text': 'Провідника організація.', 'correct': False}, {'text': 'Провіднику організація.', 'correct': False}]}, {'source': 'Glory to Ukraine!', 'options': [{'text': 'Слава Україні!', 'correct': True}, {'text': 'Славу України!', 'correct': False}, {'text': 'Славою Україні!', 'correct': False}]}, {'source': 'Underground bunker.', 'options': [{'text': 'Підземна криївка.', 'correct': True}, {'text': 'Підземний криївка.', 'correct': False}, {'text': 'Підземне криївка.', 'correct': False}]}, {'source': 'Local population supported them.', 'options': [{'text': 'Місцеве населення підтримувало їх.', 'correct': True}, {'text': 'Місцеві населення підтримували їх.', 'correct': False}, {'text': 'Місцеве населення підтримував їх.', 'correct': False}]}, {'source': 'The army was secret.', 'options': [{'text': 'Армія була таємною.', 'correct': True}, {'text': 'Армія був таємний.', 'correct': False}, {'text': 'Армія було таємне.', 'correct': False}]}], 'instruction': 'Оберіть правильний переклад.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2009/4000 (raw: 2183)
- **Activities:** ✅ 15/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 15 (target 3-9)
- **Immersion:** 🇺🇦 96.9% (target 90-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 14 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 23 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 4 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **УПА і збройний опір** | ⚪️ | 95 | Skipped |
| **Читання** | ✅ | 262 | Included in Core |
| **УПА: Армія без держави** | ⚪️ | 1194 | Skipped |
| **Первинні джерела** | ✅ | 148 | Included in Core |
| **Деколонізаційний погляд** | ✅ | 138 | Included in Core |
| **Підсумок** | ✅ | 62 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |