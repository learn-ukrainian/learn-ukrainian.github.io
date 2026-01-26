# Audit Report: M117 — chornobyl.md
**Level:** B2 | **Module:** M117 | **Phase:** HIST.11 | **Pedagogy:** Not Specified | **Target:** 4000
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:55:24

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
| 1 | quiz | Читання: Перевірка розуміння | 8 | 8 | ✅ |
| 2 | fill-in | Заповніть пропуски відповідними словами з лексичного мінімуму. | 8 | 8 | ✅ |
| 3 | true-false | Визначте, чи є твердження правдивими. | 8 | 8 | ✅ |
| 4 | error-correction | Виправте помилки у реченнях (вживання пасивного стану та лексики). | 6 | 6 | ✅ |
| 5 | match-up | Поєднайте терміни з їхніми визначеннями. | 14 | 8 | ✅ |
| 6 | match-up | Доберіть синоніми до слів. | 14 | 8 | ✅ |
| 7 | true-false | Проаналізуйте повідомлення ТАРС і виберіть правильні твердження. | 8 | 8 | ✅ |
| 8 | mark-the-words | Знайдіть пасивні дієприкметники | 6 | 6 | ✅ |
| 9 | essay-response | Ваша думка | 1 | 1 | ✅ |
| 10 | comparative-study | Порівняння реакцій | 1 | 1 | ✅ |
| 11 | unjumble | Складіть речення про події в Чорнобилі. | 6 | 6 | ✅ |
| 12 | group-sort | Розподіліть поняття за категоріями. | 18 | 1 | ✅ |
| 13 | cloze | Заповніть пропуски в тексті (16 слів). | 16 | 1 | ✅ |
| 14 | translate | Перекладіть слова англійською мовою. | 8 | 6 | ✅ |
| 15 | true-false | Які мовні засоби використовуються в тексті для опису трагедії? | 8 | 8 | ✅ |
| 16 | quiz | Перевірте свої загальні знання про Чорнобиль. | 8 | 8 | ✅ |

**Summary:**
- Total activities: 16 (target: 3-9) ❌
- Unique types: 12 (minimum: 2) ✅
- Priority types used: 2/4 (comparative-study, essay-response) ✅
- Required types used: 1/2 (essay-response) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (73% overlap): "Вона оголила банкрутство радянської системи — її технологічну недбалість, бюрократичну брехню та зне...". Shares significant keywords with sentence at index 1.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[YAML_SCHEMA_VIOLATION]** Schema error in chornobyl.yaml: Schema validation error at key '14': {'type': 'true-false', 'items': [{'correct': True, 'statement': 'Емоційно забарвлена лексика (жахливий, смертельний, зловісний)'}, {'correct': True, 'statement': 'Велика кількість наукових термінів (ізотопи, рентгени, реакція)'}, {'correct': False, 'statement': 'Використання гумору та іронії'}, {'correct': True, 'statement': 'Риторичні запитання для залучення читача'}, {'correct': False, 'statement': 'Діалектна лексика'}, {'correct': True, 'statement': 'Метафори (сніг страху, ядерна засмага)'}, {'correct': False, 'statement': 'Велика кількість сленгу та жаргонізмів'}, {'correct': True, 'statement': 'Публіцистичний стиль викладу фактів'}], 'title': 'Які мовні засоби використовуються в тексті для опису трагедії?', 'instruction': 'Визначте, чи використовується цей засіб у тексті.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2228/4000 (raw: 2387)
- **Activities:** ✅ 16/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 12/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 22/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ⚠️ Too many activities: 16 (target 3-9)
- **Immersion:** 🇺🇦 96.9% (target 90-100% (history))
- **Richness:** ✅ 95% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 15 | 3 | 100% | 24% | 23.8% |
| engagement | 22 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 21 | 4 | 100% | 10% | 9.5% |
| variety | 0.96 | - | 96% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 10 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Чорнобиль: Ціна брехні** | ⚪️ | 82 | Skipped |
| **Читання** | ✅ | 1640 | Included in Core |
| **Первинні джерела** | ✅ | 242 | Included in Core |
| **Деколонізаційний погляд** | ✅ | 92 | Included in Core |
| **Підсумок** | ✅ | 62 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |