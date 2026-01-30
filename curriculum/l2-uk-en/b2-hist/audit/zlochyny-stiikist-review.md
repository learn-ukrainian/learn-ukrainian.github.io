# Audit Report: M139 — zlochyny-stiikist.md
**Level:** B2 | **Module:** M139 | **Phase:** HIST.13 | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 10/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-29 23:39:35

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
| 1 | true-false | Аналіз окупації | 8 | 8 | ✅ |
| 2 | true-false | Крилаті вислови війни | 8 | 8 | ✅ |
| 3 | true-false | Визначте правдивість тверджень про звільнення територій. | 8 | 8 | ✅ |
| 4 | essay-response | Ціна і Сенс Стійкості | 1 | 1 | ✅ |
| 5 | comparative-study | Дві стратегії терору | 1 | 1 | ✅ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 3 (minimum: 2) ✅
- Priority types used: 2/4 (comparative-study, essay-response) ✅
- Required types used: 1/2 (essay-response) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in zlochyny-stiikist.yaml: Schema validation error at key '2': {'type': 'true-false', 'items': [{'explanation': 'Звільнення було результатом тривалої операції та вогневого контролю.', 'statement': 'Російські війська залишили Херсон без жодного опору з боку ЗСУ.', 'correct': False}, {'explanation': 'В лісі під Ізюмом знайшли понад 400 могил.', 'statement': 'Після деокупації Ізюма були виявлені численні масові поховання.', 'correct': True}, {'explanation': 'Це був спосіб зберегти енергосистему після атак.', 'statement': 'Світло в Україні вимикали за графіками для економії енергії.', 'correct': True}, {'explanation': 'Допомога енергообладнанням була масовою.', 'statement': 'Міжнародна спільнота не надає Україні генератори та трансформатори.', 'correct': False}, {'explanation': 'Боротьба за повернення кожної дитини триває.', 'statement': 'Українські діти, депортовані в Росію, вже всі повернулися додому.', 'correct': False}, {'explanation': 'Її підтримують десятки країн-партнерів.', 'statement': 'Спеціальний трибунал — це ідея лише української влади.', 'correct': False}, {'explanation': 'Україна стала прикладом боротьби за цінності.', 'statement': 'Стійкість українців надихнула багато народів світу.', 'correct': True}, {'explanation': 'Бойові дії та окупація значних територій тривають.', 'statement': 'Війна закінчилася одразу після звільнення Херсона.', 'correct': False}], 'title': 'Визначте правдивість тверджень про звільнення територій.', 'instruction': 'Визначте, чи твердження правильне.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2009/4000 (raw: 2175)
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 3/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 96.1% (target 90-100% (history))
- **Richness:** ✅ 97% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 10/10 (High)

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 10 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 24 | 10 | 100% | 14% | 14.3% |
| decolonization | 14 | 2 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 14 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Злочини і Стійкість: Біль та Перемога** | ⚪️ | 111 | Skipped |
| **Вступ: Обличчя окупації** | ✅ | 251 | Included in Core |
| **Читання: Тріумф визволення та випробування темрявою** | ✅ | 850 | Included in Core |
| **Первинні джерела** | ✅ | 320 | Included in Core |
| **Деколонізаційний погляд** | ✅ | 289 | Included in Core |
| **Підсумок** | ✅ | 78 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |