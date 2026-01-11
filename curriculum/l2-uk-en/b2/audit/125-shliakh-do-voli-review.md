# Audit Report: 125-shliakh-do-voli.md
**Phase:** B2.3d | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Події та їхнє значення для волі' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Термінологічний синтез' has 10 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** group-sort 'Процеси державотворення' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Синтез історичної думки' item 1 has 19 words (target: 8-15)
  - FIX: Adjust sentence length to 8-15 words to match B2 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 125-shliakh-do-voli.yaml: Array validation: {'type': 'select', 'title': 'Аналіз первинних джерел', 'instruction': 'Прочитайте уривки з Акту незалежності та вимог студентів і виберіть правильні твердження.', 'items': [{'correct': True, 'question': 'Обидва тексти апелюють до права нації на самовизначення та волю'}, {'correct': False, 'question': 'Студентське звернення 1990 року є менш радикальним за Акт 1991 року'}, {'correct': True, 'question': 'В Акті незалежності підкреслюється тисячолітня традиція нашого державотворення'}, {'correct': True, 'question': 'Джерела демонструють єдину мету: вихід України з-під контролю Москви'}, {'correct': False, 'question': 'Лексика обох джерел є виключно розмовною та неформальною'}, {'correct': True, 'question': 'Тексти доводять, що незалежність була вимогою активної частини суспільства'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 125-shliakh-do-voli.yaml: [index-4] select: 'items.6' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 125-shliakh-do-voli.yaml: [index-11] select: 'items.6' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 125-shliakh-do-voli.yaml: [index-12] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Первинні джерела' per template 'b2-history-module-template'
  - FIX: Add '## Первинні джерела' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Деколонізаційний погляд' per template 'b2-history-module-template'
  - FIX: Add '## Деколонізаційний погляд' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'b2-history-module-template'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!myth-buster]' per template 'b2-history-module-template'
  - FIX: Add a `> [!myth-buster]` box as specified in the template. This enhances module quality.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 15 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2004/2000
- **Activities:** ✅ 13/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 10 violations
- **Content_heavy:** ✅ Content-heavy OK (13 activities)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (history))
- **Richness:** ✅ 100% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 100% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 3 | 3 | 100% | 24% | 23.8% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 7 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 107 | Included in Core |
| **Ключова тема: Відновлення та захист суб'єктності** | ⚪️ | 61 | Skipped |
| **Тематичний аналіз** | ✅ | 1051 | Included in Core |
| **Міжнародний контекст: Україна як фактор європейської безпеки** | ✅ | 174 | Included in Core |
| **Деколонізаційний синтез** | ⚪️ | 226 | Skipped |
| **Історіографічна рефлексія** | ⚪️ | 190 | Skipped |
| **Summary** | ✅ | 85 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |