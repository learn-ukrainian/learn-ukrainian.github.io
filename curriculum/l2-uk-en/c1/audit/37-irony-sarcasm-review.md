# Audit Report: 133-irony-sarcasm.md
**Phase:** C1.4 | **Level:** C1 | **Pedagogy:** Immersion | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 133-irony-sarcasm.yaml: Schema validation error at key '11': {'type': 'select', 'title': 'Іронія в культурі', 'items': [{'question': 'Який український письменник вважається майстром іронічної прози?', 'options': [{'text': 'Остап Вишня', 'correct': True}, {'text': 'Тарас Шевченко', 'correct': False}, {'text': 'Василь Стефаник', 'correct': False}, {'text': 'Іван Багряний', 'correct': False}], 'explanation': 'Остап Вишня — класик українського гумору та сатири.'}, {'question': "Що таке 'сміх крізь сльози'?", 'options': [{'text': 'Поєднання комічного і трагічного, характерне для української літератури.', 'correct': True}, {'text': 'Сміх під час нарізання цибулі.', 'correct': False}, {'text': 'Істерична реакція на стрес.', 'correct': False}, {'text': 'Медичний термін.', 'correct': False}]}, {'question': 'Який персонаж є прикладом сатиричного зображення?', 'options': [{'text': "Голохвастов ('За двома зайцями')", 'correct': True}, {'text': 'Захар Беркут', 'correct': False}, {'text': 'Мавка', 'correct': False}, {'text': 'Ярослав Мудрий', 'correct': False}]}, {'question': 'Як українці використовують іронію під час війни?', 'options': [{'text': 'Як захисний механізм та зброю проти пропаганди (меми, жарти).', 'correct': True}, {'text': 'Українці перестали жартувати.', 'correct': False}, {'text': 'Іронія заборонена законом.', 'correct': False}, {'text': 'Тільки для спілкування з ворогами.', 'correct': False}]}, {'question': "Що означає вираз 'зробити ведмежу послугу'?", 'options': [{'text': 'Допомогти так, що стало тільки гірше (ситуативна іронія).', 'correct': True}, {'text': 'Принести мед.', 'correct': False}, {'text': 'Бути дуже сильним.', 'correct': False}, {'text': 'Впасти в сплячку.', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка' per template 'c1-module-template.md'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/c1-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ⚠️ 1917/2000 (83 short)
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 99.9% (target 90-100%)
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
| model_answers | 54 | 3 | 100% | 20% | 20.0% |
| engagement | 9 | 5 | 100% | 15% | 15.0% |
| register_analysis | 11 | 5 | 100% | 15% | 15.0% |
| visual | 9 | 4 | 100% | 10% | 10.0% |
| variety | 1.00 | - | 100% | 5% | 5.0% |
| cultural | 6 | - | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 57 | Included in Core |
| **Warm-up** | ✅ | 53 | Included in Core |
| **Теорія: Коли «Так» означає «Ні»** | ⚪️ | 229 | Skipped |
| **Аналіз: Іронія в українській культурі** | ✅ | 180 | Included in Core |
| **Іронія як інструмент виживання** | ⚪️ | 133 | Skipped |
| **Сучасна політична сатира** | ⚪️ | 143 | Skipped |
| **Лінгвістичні механізми іронії** | ⚪️ | 211 | Skipped |
| **Постмодерна іронія та метамодерн** | ⚪️ | 187 | Skipped |
| **Психологія сарказму** | ⚪️ | 79 | Skipped |
| **Мовні засоби створення іронії** | ⚪️ | 86 | Skipped |
| **Регістр: Де доречна іронія?** | ⚪️ | 133 | Skipped |
| **Іронія в історії** | ⚪️ | 91 | Skipped |
| **Сміх крізь сльози: Гумор як спротив** | ⚪️ | 211 | Skipped |
| **Підсумок** | ✅ | 84 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 40 | Skipped |