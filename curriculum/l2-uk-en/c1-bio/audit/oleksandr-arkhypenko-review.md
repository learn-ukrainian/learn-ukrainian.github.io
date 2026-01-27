# Audit Report: M76 — oleksandr-arkhypenko.md

**Level:** C1 | **Module:** M76 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:37

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
| 1 | quiz | Розуміння тексту: Спадщина Архипенка | 5 | 5 | ✅ |
| 2 | fill-in | Мистецька термінологія та колокації | 6 | 6 | ✅ |
| 3 | error-correction | Граматика: Опис творчого шляху | 5 | 5 | ✅ |
| 4 | match-up | Словник авангардиста | 8 | 6 | ✅ |
| 5 | select | Лінгвістичний аналіз джерел | 5 | 5 | ✅ |
| 6 | group-sort | Класифікація мистецьких реалій | 12 | 1 | ✅ |
| 7 | true-false | Факти про Олександра Архипенка | 5 | 5 | ✅ |
| 8 | translate | Переклад термінів | 5 | 5 | ✅ |
| 9 | authorial-intent | Намір автора: Маніфест Архипенка | 1 | 1 | ✅ |
| 10 | essay-response | Аналіз інновацій: Архипенко та Простір | 1 | 1 | ✅ |
| 11 | comparative-study | Порівняння: Архипенко vs Роден | 1 | 1 | ✅ |
| 12 | critical-analysis | Аналіз «Архипентури» | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 12 (minimum: 3) ✅
- Priority types used: 5/6 (authorial-intent, comparative-study, critical-analysis, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in oleksandr-arkhypenko.yaml: Schema validation error at key '7': {'type': 'translate', 'title': 'Переклад термінів', 'instruction': 'Оберіть правильний переклад українського терміну.', 'items': [{'source': 'негативний простір', 'options': [{'text': 'negative space', 'correct': True}, {'text': 'bad place', 'correct': False}, {'text': 'empty box', 'correct': False}, {'text': 'dark room', 'correct': False}]}, {'source': 'спадщина', 'options': [{'text': 'legacy', 'correct': True}, {'text': 'future', 'correct': False}, {'text': 'mistake', 'correct': False}, {'text': 'building', 'correct': False}]}, {'source': 'відвага', 'options': [{'text': 'courage', 'correct': True}, {'text': 'fear', 'correct': False}, {'text': 'speed', 'correct': False}, {'text': 'laziness', 'correct': False}]}, {'source': 'винахід', 'options': [{'text': 'invention', 'correct': True}, {'text': 'finding', 'correct': False}, {'text': 'loss', 'correct': False}, {'text': 'problem', 'correct': False}]}, {'source': 'порожнеча', 'options': [{'text': 'emptiness', 'correct': True}, {'text': 'fullness', 'correct': False}, {'text': 'noise', 'correct': False}, {'text': 'light', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Спадщина|Вплив' found: Вплив на сучасників та наступні покоління, Спадщина у світовій архітектурі та дизайні
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation

**📝 UPDATE** (severity 35/100)

- 5 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 2124/4000 (raw: 2412)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 12/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9)
- **Immersion:** 🇺🇦 99.8% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| quotes | 15 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 18 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 106 | Included in Core |
| **Вступ** | ✅ | 256 | Included in Core |
| **Біографія** | ⚪️ | 1076 | Skipped |
| **Історичний контекст** | ✅ | 243 | Included in Core |
| **Порівняльний аналіз** | ✅ | 200 | Included in Core |
| **Підсумок** | ✅ | 136 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 107 | Skipped |
