# Audit Report: 131-c1-3-checkpoint.md
**Phase:** C1.3 | **Level:** C1 | **Pedagogy:** TTT | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 131-c1-3-checkpoint.yaml: Schema validation error at key '12': {'type': 'true-false', 'title': 'Перевірка знань про сучасних діячів (M115-130)', 'items': [{'statement': 'Леонід Каденюк був першим космонавтом незалежної України.', 'correct': True, 'explanation': 'Це сталося у 1997 році на борту шатла Columbia.'}, {'statement': 'Сергій Жадан є автором роману «Танґо смерті».', 'correct': False, 'explanation': 'Автором «Танґо смерті» є Юрій Винничук.'}, {'statement': 'Олександра Матвійчук очолює Центр громадянських свобод.', 'correct': True, 'explanation': 'Саме ця організація отримала Нобелівську премію миру.'}, {'statement': 'Ярослав Грицак відомий передусім як балетмейстер.', 'correct': False, 'explanation': 'Грицак — відомий історик та публічний інтелектуал.'}, {'statement': 'Василь Шкляр написав роман «Залишенець» про боротьбу холодноярців.', 'correct': True, 'explanation': 'Цей твір став знаковим для сучасної історичної прози.'}, {'statement': 'Оксана Забужко є авторкою есеїстичного твору «Музей покинутих секретів».', 'correct': True, 'explanation': 'Це один із найважливіших романів сучасної української літератури.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Навички' per template 'c1-checkpoint-module-template.md'
  - FIX: Add '## Навички' section as specified in docs/l2-uk-en/templates/c1-checkpoint-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Потрібно більше практики?' per template 'c1-checkpoint-module-template.md'
  - FIX: Add '## Потрібно більше практики?' section as specified in docs/l2-uk-en/templates/c1-checkpoint-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 5/100)

- 3 violations (minor)

## Gates
- **Words:** ✅ 1797/1750
- **Activities:** ✅ 15/14
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 4/4
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 55/15
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (15 activities)
- **Immersion:** 🇺🇦 99.5% (checkpoint - no gate)
- **Richness:** ✅ 99% (checkpoint)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 11 | 8 | 100% | 25% | 25.0% |
| review_sections | 13 | 3 | 100% | 20% | 20.0% |
| variety | 0.99 | - | 99% | 15% | 14.8% |
| engagement | 4 | 3 | 100% | 10% | 10.0% |
| cultural | 5 | - | 100% | 10% | 10.0% |
| visual | 8 | 3 | 100% | 10% | 10.0% |
| paragraph_var | 1.00 | - | 100% | 10% | 10.0% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 72 | Included in Core |
| **Огляд** | ⚪️ | 146 | Skipped |
| **Навичка 1: Біографічний наратив та академічний регістр** | ⚪️ | 305 | Skipped |
| **Навичка 2: Історичний контекст та тяглість** | ✅ | 246 | Included in Core |
| **Інтеграційне завдання** | ⚪️ | 815 | Skipped |
| **Підсумок** | ✅ | 213 | Included in Core |