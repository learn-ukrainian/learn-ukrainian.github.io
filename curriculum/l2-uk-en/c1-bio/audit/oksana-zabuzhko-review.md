# Audit Report: M118 — oksana-zabuzhko.md

**Level:** C1 | **Module:** M118 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:56

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
| 1 | quiz | Життєвий та творчий шлях | 5 | 5 | ✅ |
| 2 | match-up | Філософська та літературознавча лексика | 8 | 6 | ✅ |
| 3 | group-sort | Тематика творів Оксани Забужко | 12 | 1 | ✅ |
| 4 | fill-in | Контекст роману «Музей покинутих секретів» | 6 | 6 | ✅ |
| 5 | quiz | Інтелектуальний стиль та ідеї | 5 | 5 | ✅ |
| 6 | match-up | Синоніми та антоніми модуля | 8 | 6 | ✅ |
| 7 | group-sort | Погляди та переконання | 12 | 1 | ✅ |
| 8 | fill-in | Роль Оксани Забужко | 6 | 6 | ✅ |
| 9 | quiz | Світоглядні позиції | 5 | 5 | ✅ |
| 10 | group-sort | Лексика модуля: Оксана Забужко | 12 | 1 | ✅ |
| 11 | essay-response | Творча робота: Інтелектуал і Нація | 1 | 1 | ✅ |
| 12 | comparative-study | Оксана Забужко та європейський інтелектуальний роман | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in oksana-zabuzhko.yaml: Schema validation error at key '7': {'type': 'fill-in', 'title': 'Роль Оксани Забужко', 'items': [{'sentence': 'Забужко виконує роль публічного [інтелектуала], формуючи смисли для суспільства.', 'answer': 'інтелектуала', 'options': ['інтелектуала', 'менеджера', 'артиста', 'банкіра']}, {'sentence': 'Вона стала піонером [феміністичної] критики в українській літературі 1990-х років.', 'answer': 'феміністичної', 'options': ['феміністичної', 'музичної', 'спортивної', 'кулінарної']}, {'sentence': 'Її есеїстика допомагає українцям позбутися комплексу [меншовартості].', 'answer': 'меншовартості', 'options': ['меншовартості', 'переваги', 'провини', 'радості']}, {'sentence': 'Письменниця переконана, що культура — це не розвага, а система [безпеки] нації.', 'answer': 'безпеки', 'options': ['безпеки', 'торгівлі', 'освіти', 'транспорту']}, {'sentence': 'Вона активно виступає на Заході, пояснюючи суть російського [імперіалізму].', 'answer': 'імперіалізму', 'options': ['імперіалізму', 'туризму', 'балету', 'клімату']}, {'sentence': 'Забужко називає письменника [психоаналітиком] нації, який лікує її травми.', 'answer': 'психоаналітиком', 'options': ['психоаналітиком', 'водієм', 'будівельником', 'кухарем']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[FORBIDDEN_HEADER_TONE]** Header '## Сучасний етап' is inappropriate for a deceased person. Use '## Останні роки' instead.
  - FIX: Rename '## Сучасний етап' to '## Останні роки' to maintain correct biographical tone.
- ❌ **[FORBIDDEN_HEADER_TONE]** Header '## Вплив' is inappropriate for a deceased person. Use '## Спадщина' instead.
  - FIX: Rename '## Вплив' to '## Спадщина' to maintain correct biographical tone.

## Recommendation

**📝 UPDATE** (severity 25/100)

- 3 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 2041/4000 (raw: 2251)
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
- **Immersion:** 🇺🇦 99.5% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 10 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 15 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 11 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 11 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 20 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 74 | Included in Core |
| **Вступ** | ✅ | 158 | Included in Core |
| **Життєпис** | ⚪️ | 527 | Skipped |
| **Внесок** | ⚪️ | 50 | Skipped |
| **Сучасний етап** | ⚪️ | 91 | Skipped |
| **Історичний контекст** | ✅ | 305 | Included in Core |
| **Порівняльний аналіз** | ✅ | 176 | Included in Core |
| **Есе** | ⚪️ | 329 | Skipped |
| **Підсумок** | ✅ | 35 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 186 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |
