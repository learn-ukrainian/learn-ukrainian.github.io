# Audit Report: 135-euphemism-taboo.md
**Phase:** C1.4 | **Level:** C1 | **Pedagogy:** Immersion | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 135-euphemism-taboo.yaml: Schema validation error at key '10': {'type': 'true-false', 'title': 'Правда чи Міф: Табу', 'items': [{'statement': "Слово 'останній' часто замінюють на 'крайній' у чергах через професійні забобони.", 'correct': True, 'explanation': "Це поширений мовний забобон, хоча літературно правильно 'останній'."}, {'statement': 'В Україні прийнято голосно обговорювати свої хвороби за святковим столом.', 'correct': False, 'explanation': 'Це вважається поганим тоном і псує апетит присутнім.'}, {'statement': 'Евфемізми завжди роблять мову менш точною, але більш ввічливою.', 'correct': True, 'explanation': 'Так, вони розмивають зміст заради ввічливості або маніпуляції.'}, {'statement': "Вживати слово 'туалет' в офіційному суспільстві суворо заборонено законом.", 'correct': False, 'explanation': "Це нормальне слово, але 'вбиральня' звучить краще."}, {'statement': 'Усі евфемізми є брехнею, яка має на меті обдурити співрозмовника.', 'correct': False, 'explanation': "Вони пом'якшують правду, але не обов'язково її викривляють."}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка' per template 'c1-module-template.md'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/c1-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ⚠️ 1999/2000 (1 short)
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 99.4% (target 90-100%)
- **Richness:** ✅ 99% (style)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** style

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| exemplar_texts | 15 | 2 | 100% | 25% | 25.0% |
| model_answers | 71 | 3 | 100% | 20% | 20.0% |
| engagement | 7 | 5 | 100% | 15% | 15.0% |
| register_analysis | 15 | 5 | 100% | 15% | 15.0% |
| visual | 7 | 4 | 100% | 10% | 10.0% |
| variety | 0.99 | - | 99% | 5% | 5.0% |
| cultural | 1 | - | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 70 | Included in Core |
| **Warm-up** | ✅ | 70 | Included in Core |
| **Теорія: Мистецтво пом'якшення** | ⚪️ | 134 | Skipped |
| **Сфери вживання: Про що ми «не говоримо»** | ⚪️ | 287 | Skipped |
| **Історичний екскурс: Радянська новомова** | ⚪️ | 177 | Skipped |
| **Аналіз: Табу в українській культурі** | ✅ | 511 | Included in Core |
| **Дисфемізми: Коли хочеться грубості** | ⚪️ | 240 | Skipped |
| **Психолінгвістика війни: Від «бавовни» до «блекауту»** | ⚪️ | 143 | Skipped |
| **Табу в бізнесі: Гроші люблять тишу** | ⚪️ | 0 | Skipped |
| **Регістр: Як обрати правильне слово** | ⚪️ | 53 | Skipped |
| **Підсумок** | ✅ | 95 | Included in Core |
| **Кейс-стаді: "Політична коректність" в сучасній Україні** | ⚪️ | 149 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 70 | Skipped |