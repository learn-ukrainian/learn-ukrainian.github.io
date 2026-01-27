# Audit Report: M124 — oleg-sentsov.md

**Level:** C1 | **Module:** M124 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:57:19

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
| 1 | quiz | Біографія Олега Сенцова | 5 | 5 | ✅ |
| 2 | match-up | Лексика опору та кіно | 8 | 6 | ✅ |
| 3 | group-sort | Етапи життя Олега Сенцова | 12 | 1 | ✅ |
| 4 | fill-in | Контекст ув'язнення та звільнення | 6 | 6 | ✅ |
| 5 | quiz | Аналіз творчості | 5 | 5 | ✅ |
| 6 | match-up | Синоніми та антоніми | 8 | 6 | ✅ |
| 7 | group-sort | Лексика модуля: Олег Сенцов | 12 | 1 | ✅ |
| 8 | group-sort | Характер Сенцова | 12 | 1 | ✅ |
| 9 | quiz | Політичні погляди | 5 | 5 | ✅ |
| 10 | fill-in | Значення для світу | 6 | 6 | ✅ |
| 11 | essay-response | Творча робота: Ціна свободи | 1 | 1 | ✅ |
| 12 | comparative-study | Олег Сенцов та Василь Стус | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in oleg-sentsov.yaml: Schema validation error at key '9': {'type': 'fill-in', 'title': 'Значення для світу', 'items': [{'sentence': 'Сенцов став глобальним [символом] опору російській агресії.', 'answer': 'символом', 'options': ['символом', 'ворогом', 'другом', 'гостем']}, {'sentence': 'Його історія показала, що один [воїн] у полі — теж воїн.', 'answer': 'воїн', 'options': ['воїн', 'фермер', 'лікар', 'учень']}, {'sentence': 'Світ побачив справжнє обличчя [кремлівського] режиму через його справу.', 'answer': 'кремлівського', 'options': ['кремлівського', 'київського', 'львівського', 'одеського']}, {'sentence': 'Він надихнув мільйони людей не боятися говорити [правду].', 'answer': 'правду', 'options': ['правду', 'брехню', 'казку', 'вірш']}, {'sentence': 'Його фільми представляють Україну на найкращих [фестивалях] світу.', 'answer': 'фестивалях', 'options': ['фестивалях', 'базарах', 'вокзалах', 'стадіонах']}, {'sentence': 'Сенцов довів, що свобода — це найвища [цінність].', 'answer': 'цінність', 'options': ['цінність', 'ціна', 'плата', 'схема']}]} is not valid under any of the given schemas
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

- **Words:** ❌ 1973/4000 (raw: 2254)
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
- **Immersion:** 🇺🇦 99.8% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 6 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 7 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 12 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 10 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 15 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 74 | Included in Core |
| **Вступ** | ✅ | 158 | Included in Core |
| **Життєпис** | ⚪️ | 478 | Skipped |
| **Внесок** | ⚪️ | 54 | Skipped |
| **Сучасний етап** | ⚪️ | 100 | Skipped |
| **Історичний контекст** | ✅ | 332 | Included in Core |
| **Порівняльний аналіз** | ✅ | 186 | Included in Core |
| **Есе** | ⚪️ | 313 | Skipped |
| **Підсумок** | ✅ | 40 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 148 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 90 | Skipped |
