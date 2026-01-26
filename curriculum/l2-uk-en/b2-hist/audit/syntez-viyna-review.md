# Audit Report: M140 — syntez-viyna.md
**Level:** B2 | **Module:** M140 | **Phase:** B2.3e | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 22:23:52

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
| 1 | unjumble | Хронологія великої боротьби | 16 | 6 | ✅ |
| 2 | quiz | Аналіз сучасної суб'єктності | 12 | 8 | ✅ |
| 3 | fill-in | Синтез понять та ідей | 16 | 8 | ✅ |
| 4 | match-up | Героїчні місця та їх значення | 16 | 8 | ✅ |
| 5 | group-sort | Патерни агресії та спротиву | 23 | 1 | ✅ |
| 6 | cloze | Логіка сучасної стійкості | 16 | 1 | ✅ |
| 7 | true-false | Критерії справжньої Перемоги | 12 | 8 | ✅ |
| 8 | error-correction | Спростування дезінформації | 8 | 6 | ✅ |
| 9 | translate | Аналітичний переклад | 12 | 6 | ✅ |
| 10 | match-up | Колокації сучасної історії | 16 | 8 | ✅ |
| 11 | mark-the-words | Пасивний стан в історії | 12 | 6 | ✅ |
| 12 | true-false | Факти сучасної війни | 12 | 8 | ✅ |
| 13 | quiz | Міжнародна підтримка та солідарність | 8 | 8 | ✅ |
| 14 | true-false | Цінності українського опору | 12 | 8 | ✅ |
| 15 | essay-response | Від «Об'єкта» до «Суб'єкта» | 1 | 1 | ✅ |
| 16 | comparative-study | Еволюція війни: 2014 vs 2022 | 1 | 1 | ✅ |

**Summary:**
- Total activities: 16 (target: 3-9) ❌
- Unique types: 12 (minimum: 2) ✅
- Priority types used: 2/4 (comparative-study, essay-response) ✅
- Required types used: 1/2 (essay-response) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in syntez-viyna.yaml: Schema validation error at key 'words': ['Підписання', 'других', 'Мінських', 'домовленостей', 'про', 'припинення', 'вогню'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Європейський контекст: Еволюція війни, Вступ: Поворотний момент історії
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation
**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 1872/4000 (raw: 2338)
- **Activities:** ✅ 16/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 12/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 16 (target 3-9)
- **Immersion:** 🇺🇦 96.3% (target 90-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 4 | 3 | 100% | 24% | 23.8% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 15 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Синтез: Війна за існування** | ⚪️ | 80 | Skipped |
| **Читання: Узагальнення епохи 2014–2024** | ✅ | 891 | Included in Core |
| **Первинні джерела: Хронологія війни** | ✅ | 101 | Included in Core |
| **Деколонізаційний погляд: Україна як Щит Європи** | ✅ | 378 | Included in Core |
| **Європейський контекст: Еволюція війни** | ✅ | 115 | Included in Core |
| **Підсумок** | ✅ | 0 | Included in Core |
| **Ключові висновки епохи 2014-2024** | ✅ | 0 | Included in Core |
| **Модулі цієї епохи (M126-130)** | ⚪️ | 197 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |