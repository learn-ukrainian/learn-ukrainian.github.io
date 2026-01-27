# Audit Report: M119 — yaroslav-hrytsak.md

**Level:** C1 | **Module:** M119 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:57

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
| 1 | quiz | Біографія та основні ідеї | 5 | 5 | ✅ |
| 2 | match-up | Історичні та соціологічні поняття | 8 | 6 | ✅ |
| 3 | group-sort | Фактори розвитку України | 12 | 1 | ✅ |
| 4 | fill-in | Концепції Ярослава Грицака | 6 | 6 | ✅ |
| 5 | quiz | Аналіз історичного контексту | 5 | 5 | ✅ |
| 6 | match-up | Метафори та цитати | 8 | 6 | ✅ |
| 7 | group-sort | Цінності (за Інглхартом/Грицаком) | 12 | 1 | ✅ |
| 8 | fill-in | Майбутнє України | 6 | 6 | ✅ |
| 9 | quiz | Порівняння істориків | 5 | 5 | ✅ |
| 10 | group-sort | Лексика модуля: Ярослав Грицак | 12 | 1 | ✅ |
| 11 | essay-response | Творча робота: Історія як шанс | 1 | 1 | ✅ |
| 12 | comparative-study | Ярослав Грицак та сучасна історична наука | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in yaroslav-hrytsak.yaml: Schema validation error at key '7': {'type': 'fill-in', 'title': 'Майбутнє України', 'items': [{'sentence': 'Грицак вірить, що Україна приречена на [успіх], якщо зробить правильний ціннісний вибір.', 'answer': 'успіх', 'options': ['успіх', 'провал', 'застій', 'ізоляцію']}, {'sentence': 'У глобальному світі виграють нації, які сповідують цінності [довіри] та відповідальності.', 'answer': 'довіри', 'options': ['довіри', 'сили', 'хитрості', 'страху']}, {'sentence': 'Він вчить українців бути [дорослими] і не чекати месії.', 'answer': 'дорослими', 'options': ['дорослими', 'дітьми', 'слухняними', 'агресивними']}, {'sentence': 'Подолання минулого — це відмова від [патерналізму] та корупції.', 'answer': 'патерналізму', 'options': ['патерналізму', 'демократії', 'свободи', 'науки']}, {'sentence': 'Війна показала, що українці готові вмирати за [цінності], а не лише за інтереси.', 'answer': 'цінності', 'options': ['цінності', 'гроші', 'території', 'нафту']}, {'sentence': 'Історія — це не вирок, а [можливість] змінитися.', 'answer': 'можливість', 'options': ['можливість', 'кара', 'помилка', 'стіна']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation

**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 2063/4000 (raw: 2338)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 6/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 13 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 14 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 12 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 16 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 19 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 74 | Included in Core |
| **Вступ** | ✅ | 175 | Included in Core |
| **Життєпис** | ⚪️ | 468 | Skipped |
| **Внесок** | ⚪️ | 60 | Skipped |
| **Сучасний етап** | ⚪️ | 114 | Skipped |
| **Історичний контекст** | ✅ | 331 | Included in Core |
| **Порівняльний аналіз** | ✅ | 169 | Included in Core |
| **Есе** | ⚪️ | 340 | Skipped |
| **Підсумок** | ✅ | 53 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 175 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 104 | Skipped |
