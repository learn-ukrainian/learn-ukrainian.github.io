# Audit Report: M126 — kateryna-kalytko.md
**Level:** C1 | **Module:** M126 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:57:20

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
| 1 | quiz | Біографія та творчий метод | 5 | 5 | ✅ |
| 2 | match-up | Поетична та психологічна лексика | 8 | 6 | ✅ |
| 3 | group-sort | Образи поезії Калитко | 12 | 1 | ✅ |
| 4 | fill-in | Контекст збірки «Земля Загублених» | 6 | 6 | ✅ |
| 5 | quiz | Аналіз стилю | 5 | 5 | ✅ |
| 6 | match-up | Синоніми та асоціації | 8 | 6 | ✅ |
| 7 | group-sort | Лексика модуля: Катерина Калитко | 12 | 1 | ✅ |
| 8 | group-sort | Теми збірок | 12 | 1 | ✅ |
| 9 | quiz | Філософія Калитко | 5 | 5 | ✅ |
| 10 | fill-in | Творчий метод | 6 | 6 | ✅ |
| 11 | essay-response | Творча робота: Поезія як свідок | 1 | 1 | ✅ |
| 12 | comparative-study | Катерина Калитко та Сільвія Плат | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in kateryna-kalytko.yaml: Schema validation error at key '9': {'type': 'fill-in', 'title': 'Творчий метод', 'items': [{'sentence': 'Калитко не намагається [сподобатися] читачеві, вона говорить правду, яка може бути неприємною.', 'answer': 'сподобатися', 'options': ['сподобатися', 'догодити', 'продати', 'збрехати']}, {'sentence': 'Її стиль характеризується густою [образністю] та складною метафорикою.', 'answer': 'образністю', 'options': ['образністю', 'простотою', 'сухістю', 'бідністю']}, {'sentence': 'Вона пише про війну не як політик, а як людина, що відчуває [шкірою].', 'answer': 'шкірою', 'options': ['шкірою', 'розумом', 'очима', 'вухами']}, {'sentence': 'Переклади з [балканських] мов збагатили її власну палітру трагічним звучанням.', 'answer': 'балканських', 'options': ['балканських', 'азійських', 'скандинавських', 'романських']}, {'sentence': 'Поезія для неї — це спосіб не [збожеволіти] в умовах катастрофи.', 'answer': 'збожеволіти', 'options': ['збожеволіти', 'заснути', 'втекти', 'заробити']}, {'sentence': 'Вона перетворює [біль] на естетику, роблячи його високим мистецтвом.', 'answer': 'біль', 'options': ['біль', 'сміх', 'радість', 'спокій']}]} is not valid under any of the given schemas
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
- **Words:** ❌ 1917/4000 (raw: 2174)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 6/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/5
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
| primary_sources | 8 | 4 | 100% | 19% | 19.0% |
| engagement | 10 | 6 | 100% | 14% | 14.3% |
| quotes | 9 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 13 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 13 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.95 | - | 95% | 5% | 4.5% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 22 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.4%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 71 | Included in Core |
| **Вступ** | ✅ | 148 | Included in Core |
| **Життєпис** | ⚪️ | 410 | Skipped |
| **Внесок** | ⚪️ | 60 | Skipped |
| **Сучасний етап** | ⚪️ | 110 | Skipped |
| **Історичний контекст** | ✅ | 410 | Included in Core |
| **Порівняльний аналіз** | ✅ | 151 | Included in Core |
| **Есе** | ⚪️ | 299 | Skipped |
| **Підсумок** | ✅ | 34 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 152 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 72 | Skipped |