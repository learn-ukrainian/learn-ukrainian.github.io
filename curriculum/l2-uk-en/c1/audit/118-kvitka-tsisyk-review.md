# Audit Report: 118-kvitka-tsisyk.md
**Phase:** C1.3 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Життєвий шлях Квітки Цісик' Q1 prompt length 9 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Життєвий шлях Квітки Цісик' Q4 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Життєвий шлях Квітки Цісик' Q5 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Мистецький аналіз вокалу' Q1 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Мистецький аналіз вокалу' Q2 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Мистецький аналіз вокалу' Q3 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Мистецький аналіз вокалу' Q4 prompt length 9 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Мистецький аналіз вокалу' Q5 prompt length 8 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Роль діаспори у збереженні ідентичності' Q1 prompt length 8 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Роль діаспори у збереженні ідентичності' Q2 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Роль діаспори у збереженні ідентичності' Q3 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Роль діаспори у збереженні ідентичності' Q4 prompt length 10 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Роль діаспори у збереженні ідентичності' Q5 prompt length 9 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 118-kvitka-tsisyk.yaml: Schema validation error at key '8': {'type': 'quiz', 'title': 'Роль діаспори у збереженні ідентичності', 'items': [{'question': 'Яку хвилю української еміграції представляла родина Квітки Цісик?', 'options': [{'text': 'Першу (трудову)', 'correct': False}, {'text': 'Третю (політичну після Другої світової)', 'correct': True}, {'text': 'Четверту (сучасну економічну)', 'correct': False}, {'text': 'Другу (міжвоєнну)', 'correct': False}]}, {'question': 'Чому для діаспори було важливо зберігати українську мову та культуру?', 'options': [{'text': 'Бо вони не хотіли вчити англійську', 'correct': False}, {'text': 'Для протидії радянській русифікації та збереження нації в екзилі', 'correct': True}, {'text': 'Через вимоги американського уряду', 'correct': False}, {'text': 'Це було просто хобі для вільних людей', 'correct': False}]}, {'question': 'Яку мету переслідувала Квітка, вкладаючи власні кошти в українські пісні?', 'options': [{'text': 'Стати популярною в СРСР', 'correct': False}, {'text': 'Віддати шану своєму народові та зберегти спадщину', 'correct': True}, {'text': 'Уникнути сплати податків у США', 'correct': False}, {'text': 'Вона просто не мала куди витрачати гроші', 'correct': False}]}, {'question': 'Як радянська влада ставилася до популярності Квітки Цісик в Україні?', 'options': [{'text': 'Офіційно запрошувала її на гастролі', 'correct': False}, {'text': 'Замовчувала її існування та переслідувала за розповсюдження касет', 'correct': True}, {'text': 'Вручила їй державну премію', 'correct': False}, {'text': 'Дозволяла крутити її пісні на радіо', 'correct': False}]}, {'question': 'Яке значення має приклад Квітки для сучасного патріотичного виховання?', 'options': [{'text': 'Він вчить, що треба виїжджати з України', 'correct': False}, {'text': 'Він показує, як можна любити і прославляти Батьківщину ділом', 'correct': True}, {'text': 'Він демонструє, що реклама — це найголовніше мистецтво', 'correct': False}, {'text': 'Він не має жодного значення сьогодні', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Спадщина' per template 'c1-biography-module-template.md'
  - FIX: Add '## Спадщина' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 17 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2182/2000
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 6/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 27/24
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 14 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 99.4% (target 90-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 7 | 4 | 100% | 19% | 19.0% |
| engagement | 10 | 6 | 100% | 14% | 14.3% |
| quotes | 12 | 3 | 100% | 14% | 14.3% |
| cultural | 6 | 4 | 100% | 10% | 9.5% |
| visual | 14 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 24 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.96 | - | 96% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 15 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 74 | Included in Core |
| **Вступ** | ⚪️ | 199 | Skipped |
| **Біографія** | ⚪️ | 788 | Skipped |
| **Історичний контекст** | ✅ | 237 | Included in Core |
| **Порівняльний аналіз** | ✅ | 159 | Included in Core |
| **Есе** | ⚪️ | 360 | Skipped |
| **Підсумок** | ✅ | 53 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 189 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 123 | Skipped |