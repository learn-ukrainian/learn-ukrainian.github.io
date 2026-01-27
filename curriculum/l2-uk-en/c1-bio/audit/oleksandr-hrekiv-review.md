# Audit Report: M65 — oleksandr-hrekiv.md

**Level:** C1 | **Module:** M65 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:30

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
| 1 | quiz | «Життєвий шлях генерала Грекова» | 12 | 5 | ✅ |
| 2 | fill-in | «Військова лексика генерала» | 12 | 6 | ✅ |
| 3 | error-correction | «Граматика військової історії» | 12 | 5 | ✅ |
| 4 | match-up | «Військовий словник» | 12 | 6 | ✅ |
| 5 | select | «Аналіз військової біографії» | 5 | 5 | ✅ |
| 6 | true-false | «Факти про генерала» | 12 | 5 | ✅ |
| 7 | reading | «Спогади про Чортківську офензиву» | 3 | 1 | ✅ |
| 8 | reading | «Арешт у Відні: Документи СМЕРШ» | 3 | 1 | ✅ |
| 9 | essay-response | «Трагедія українського офіцера» | 1 | 1 | ✅ |
| 10 | comparative-study | «Стратег і Практик: Греків та Омелянович-Павленко» | 1 | 1 | ✅ |
| 11 | critical-analysis | «Аналіз спогадів генерала» | 1 | 1 | ✅ |
| 12 | unjumble | «Відновлення військових тез» | 12 | 5 | ✅ |
| 13 | translate | «Військова кар'єра Грекова» | 12 | 5 | ✅ |
| 14 | mark-the-words | «Пошук географічних назв» | 7 | 5 | ✅ |
| 15 | translate | «Військовий переклад» | 12 | 5 | ✅ |
| 16 | mark-the-words | «Пошук військових термінів» | 11 | 5 | ✅ |
| 17 | true-false | «Принципи генерала Грекова» | 12 | 5 | ✅ |
| 18 | select | «Військова стратегія і тактика» | 5 | 5 | ✅ |

**Summary:**
- Total activities: 18 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 5/6 (comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 5/6 (essay-response, fill-in, match-up, quiz, reading) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[MALFORMED_ERROR_CORRECTION]** Error-correction activity '«Граматика військової історії»' uses placeholder syntax instead of real errors
  - FIX: Convert to proper error-correction format with real error words in sentences, or change to fill-in activity. Found 12/12 items with placeholders/missing errors.
- **[YAML_SCHEMA_VIOLATION]** Schema error in oleksandr-hrekiv.yaml: Schema validation error at key '17': {'type': 'select', 'id': 'c1-84-select-2', 'title': '«Військова стратегія і тактика»', 'instruction': '«Оберіть правильні твердження про військові погляди Грекова.»', 'items': [{'question': '«Що було основою успіху Чортківської офензиви?»', 'options': [{'text': '«Масова атака піхоти без підтримки артилерії»', 'correct': False}, {'text': '«Раптовий фланговий удар та маневр»', 'correct': True}, {'text': '«Довга артилерійська підготовка»', 'correct': False}, {'text': '«Використання авіації»', 'correct': False}], 'explanation': '«Греків зробив ставку на маневр і несподіваність.»'}, {'question': '«Як Греків ставився до партизанської війни?»', 'options': [{'text': '«Він вважав її єдиним можливим методом боротьби»', 'correct': False}, {'text': '«Він віддавав перевагу регулярній армії та фронту»', 'correct': True}, {'text': '«Він забороняв будь-які партизанські дії»', 'correct': False}, {'text': '«Він сам очолював партизанський загін»', 'correct': False}], 'explanation': '«Як кадровий офіцер, він був прихильником регулярного війська.»'}, {'question': '«Яку роль він відводив штабу армії?»', 'options': [{'text': '«Це лише місце для оформлення паперів»', 'correct': False}, {'text': '«Штаб — це мозок армії, що планує операції»', 'correct': True}, {'text': '«Штаб не повинен втручатися в дії командирів»', 'correct': False}, {'text': '«Штаб потрібен лише для нагородження героїв»', 'correct': False}], 'explanation': '«Він розумів важливість чіткого планування та управління.»'}, {'question': '«Чому він наполягав на єдності командування?»', 'options': [{'text': '«Щоб мати всю владу в своїх руках»', 'correct': False}, {'text': '«Щоб уникнути хаосу та неузгодженості дій»', 'correct': True}, {'text': '«Щоб ніхто не міг його критикувати»', 'correct': False}, {'text': '«Щоб отримувати більшу зарплату»', 'correct': False}], 'explanation': '«Єдине командування — запорука ефективності армії.»'}, {'question': '«Як він оцінював роль технічного забезпечення?»', 'options': [{'text': '«Техніка не важлива, головне — дух»', 'correct': False}, {'text': '«Сучасна війна вимагає новітньої зброї та техніки»', 'correct': True}, {'text': '«Краще воювати старою зброєю, але перевіреною»', 'correct': False}, {'text': '«Техніка лише заважає солдатам рухатися»', 'correct': False}], 'explanation': '«Він намагався модернізувати українське військо.»'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation

**📝 UPDATE** (severity 5/100)

- 3 violations (minor)

## Gates

- **Words:** ❌ 2144/4000 (raw: 2380)
- **Activities:** ✅ 18/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ⚠️ Too many activities: 18 (target 3-9)
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
| engagement | 8 | 6 | 100% | 14% | 14.3% |
| quotes | 8 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 72 | Included in Core |
| **Вступ** | ✅ | 202 | Included in Core |
| **Життєпис** | ⚪️ | 841 | Skipped |
| **Внесок** | ⚪️ | 184 | Skipped |
| **Спадщина** | ⚪️ | 386 | Skipped |
| **Порівняльний аналіз** | ✅ | 124 | Included in Core |
| **Підсумок** | ✅ | 246 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 89 | Skipped |
| **Вправи** | ⚪️ | 0 | Skipped |
| **Словник** | ⚪️ | 0 | Skipped |
