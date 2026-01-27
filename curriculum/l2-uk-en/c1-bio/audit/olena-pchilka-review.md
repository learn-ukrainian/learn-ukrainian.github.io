# Audit Report: M42 — olena-pchilka.md

**Level:** C1 | **Module:** M42 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:17

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
| 1 | quiz | Життя і переконання | 12 | 5 | ✅ |
| 2 | fill-in | Культурна лексика | 12 | 6 | ✅ |
| 3 | match-up | Поняття і визначення | 12 | 6 | ✅ |
| 4 | select | Аналіз тексту про Пчілку | 6 | 5 | ✅ |
| 5 | error-correction | Граматика в тексті про Пчілку | 12 | 5 | ✅ |
| 6 | group-sort | Пчілка vs Драгоманов | 24 | 1 | ✅ |
| 7 | essay-response | Критичний аналіз: Виховання еліти | 1 | 1 | ✅ |
| 8 | comparative-study | Мати і Донька | 1 | 1 | ✅ |
| 9 | reading | Спогади про Пчілку | 3 | 1 | ✅ |
| 10 | reading | Стаття про фемінізм | 3 | 1 | ✅ |
| 11 | essay-response | Есе: Інженер душі | 1 | 1 | ✅ |
| 12 | unjumble | Цитати та думки Пчілки | 6 | 5 | ✅ |
| 13 | cloze | Життєвий шлях Олени Пчілки | 12 | 1 | ✅ |
| 14 | translate | Переклад думок про Пчілку | 6 | 5 | ✅ |
| 15 | match-up | Родинні зв'язки Косачів-Драгоманових | 12 | 6 | ✅ |

**Summary:**
- Total activities: 15 (target: 3-9) ❌
- Unique types: 12 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in olena-pchilka.yaml: Schema validation error at key '13': {'type': 'translate', 'title': 'Переклад думок про Пчілку', 'items': [{'source': 'She was the iron lady of Ukrainian culture.', 'options': [{'text': 'Вона була залізною леді української культури.', 'correct': True}, {'text': 'Вона була доброю жінкою в культурі.', 'correct': False}, {'text': 'Вона мала залізний характер.', 'correct': False}, {'text': 'Вона любила залізо і культуру.', 'correct': False}]}, {'source': 'She refused to speak Russian even in official settings.', 'options': [{'text': 'Вона відмовлялася говорити російською навіть в офіційних установах.', 'correct': True}, {'text': 'Вона не знала російської мови.', 'correct': False}, {'text': 'Вона говорила російською лише вдома.', 'correct': False}, {'text': 'Вона любила офіційні промови.', 'correct': False}]}, {'source': 'Her pseudonym symbolized tireless work.', 'options': [{'text': 'Її псевдонім символізував невтомну працю.', 'correct': True}, {'text': 'Вона любила бджіл і мед.', 'correct': False}, {'text': "Пчілка - це ім'я її улюбленої тварини.", 'correct': False}, {'text': 'Символ праці - це мураха.', 'correct': False}]}, {'source': 'She educated her children at home to preserve their identity.', 'options': [{'text': 'Вона навчала дітей вдома, щоб зберегти їхню ідентичність.', 'correct': True}, {'text': 'Діти не ходили до школи через хворобу.', 'correct': False}, {'text': 'Вона не мала грошей на школу.', 'correct': False}, {'text': 'Вдома вчитися легше.', 'correct': False}]}, {'source': 'She was a pioneer of the feminist movement.', 'options': [{'text': 'Вона була піонеркою феміністичного руху.', 'correct': True}, {'text': 'Вона не любила чоловіків.', 'correct': False}, {'text': 'Фемінізм був їй чужий.', 'correct': False}, {'text': 'Вона заснувала жіночий клуб.', 'correct': False}]}, {'source': 'She proved that language is a weapon.', 'options': [{'text': 'Вона довела, що мова — це зброя.', 'correct': True}, {'text': 'Вона показала, що зброя — це погано.', 'correct': False}, {'text': 'Вона купила зброю для захисту.', 'correct': False}, {'text': 'Вона не любила сперечатися.', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation

**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 2037/4000 (raw: 2288)
- **Activities:** ✅ 15/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 12/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 15 (target 3-9)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
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
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 7 | 3 | 100% | 14% | 14.3% |
| cultural | 6 | 4 | 100% | 10% | 9.5% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 23 | 8 | 100% | 10% | 9.5% |
| legacy | 13 | 2 | 100% | 10% | 9.5% |
| variety | 0.95 | - | 95% | 5% | 4.5% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 78 | Included in Core |
| **Вступ** | ✅ | 145 | Included in Core |
| **Життєпис** | ⚪️ | 551 | Skipped |
| **Спадщина** | ⚪️ | 53 | Skipped |
| **Внесок** | ⚪️ | 237 | Skipped |
| **Історичний контекст** | ✅ | 494 | Included in Core |
| **Порівняльний аналіз** | ✅ | 50 | Included in Core |
| **Критичне мислення** | ⚪️ | 76 | Skipped |
| **Есе** | ⚪️ | 35 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 249 | Skipped |
| **Підсумок** | ✅ | 55 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 14 | Skipped |
