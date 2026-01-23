# Audit Report: M58 — ruina-i.md
**Level:** B2 | **Module:** M58 | **Phase:** B2.3b | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL

## Configuration
**Type:** B2-history
**Word Target:** 4000 words
**Activities:** 3-10 required
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
| 1 | quiz | Розуміння тексту про період Руїни | 16 | 8 | ✅ |
| 2 | match-up | Політична та історична термінологія | 16 | 8 | ✅ |
| 3 | cloze | Історична лексика в контексті | 16 | 1 | ✅ |
| 4 | true-false | Факти про період Руїни | 16 | 8 | ✅ |
| 5 | group-sort | Класифікація понять | 16 | 1 | ✅ |
| 6 | unjumble | Складіть речення про Руїну | 16 | 6 | ✅ |
| 7 | error-correction | Граматика в історичних реченнях | 16 | 6 | ✅ |
| 8 | cloze | Заповніть текст про Виговського і Руїну | 16 | 1 | ✅ |
| 9 | mark-the-words | Знайдіть політичну термінологію | 13 | 6 | ✅ |
| 10 | select | Оберіть усі правильні твердження згідно з текстом | 8 | 6 | ✅ |
| 11 | translate | Переклад політичних та історичних термінів | 16 | 6 | ✅ |
| 12 | fill-in | Вибір правильного відмінка | 16 | 8 | ✅ |
| 13 | quiz | Аналіз первинних джерел | 16 | 8 | ✅ |
| 14 | essay-response | Аналітичне есе | 1 | 1 | ✅ |
| 15 | comparative-study | Порівняння політичних лідерів | 1 | 1 | ✅ |

**Summary:**
- Total activities: 15 (target: 3-10) ❌
- Unique types: 13 (minimum: 2) ✅
- Priority types used: 2/4 (comparative-study, essay-response) ✅
- Required types used: 1/2 (essay-response) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (100% overlap): "Він розуміє, що козацька держава не виживе без союзу з великою державою.". Shares significant keywords with sentence at index 26.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (100% overlap): "Але він не хоче бути васалом Москви, бо знає, що цар поглине Україну.". Shares significant keywords with sentence at index 27.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[YAML_SCHEMA_VIOLATION]** Schema error in ruina-i.yaml: Schema validation error at key 'words': ['Україна', 'трагічно', 'розпалася', 'на', 'дві', 'ворогуючі', 'частини'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 3 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 1987/4000 (raw: 2328)
- **Activities:** ✅ 15/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 15/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ⚠️ Too many activities: 15 (target 3-10)
- **Immersion:** 🇺🇦 97.0% (target 90-100% (history))
- **Richness:** ✅ 98% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 15 | 3 | 100% | 24% | 23.8% |
| engagement | 15 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 8 | 4 | 100% | 10% | 9.5% |
| visual | 11 | 4 | 100% | 10% | 9.5% |
| variety | 0.95 | - | 95% | 5% | 4.5% |
| paragraph_var | 0.74 | - | 74% | 5% | 3.5% |
| questions | 11 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **98.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Руїна I: Виговщина і розкол** | ⚪️ | 72 | Skipped |
| **Вступ: Руїна I, Виговщина і розкол** | ✅ | 173 | Included in Core |
| **Читання: Іван Виговський: спроба зберегти державу** | ✅ | 303 | Included in Core |
| **Гадяцька угода: альтернатива Москві** | ⚪️ | 193 | Skipped |
| **Конотопська битва: тріумф і трагедія** | ⚪️ | 273 | Skipped |
| **Чорна рада і розкол** | ⚪️ | 342 | Skipped |
| **Первинні джерела** | ✅ | 181 | Included in Core |
| **Деколонізаційний погляд** | ✅ | 216 | Included in Core |
| **Підсумок** | ✅ | 124 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |