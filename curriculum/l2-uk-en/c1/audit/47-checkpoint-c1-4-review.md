# Audit Report: 143-checkpoint-c1-4.md
**Phase:** C1.4 | **Level:** C1 | **Pedagogy:** Assessment | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 143-checkpoint-c1-4.yaml: Schema validation error at key '13': {'type': 'translate', 'title': 'Фінальний переклад', 'instruction': 'Перекладіть англійські фрази українською у відповідному регістрі.', 'items': [{'source': "Hey bro, what's up? (Slang)", 'options': [{'text': 'Йо, бро, як справи?', 'correct': True}, {'text': 'Вітаю, брате, що нового?', 'correct': False}, {'text': 'Доброго дня, колего.', 'correct': False}, {'text': 'Привіт, родичу, як життя?', 'correct': False}]}, {'source': 'I hereby certify that... (Formal)', 'options': [{'text': 'Цим засвідчую, що...', 'correct': True}, {'text': 'Я тут кажу, що...', 'correct': False}, {'text': 'Я клянусь, що...', 'correct': False}, {'text': 'Зуб даю, що...', 'correct': False}]}, {'source': 'My darling, I miss you. (Intimate)', 'options': [{'text': 'Моє сонечко, я сумую.', 'correct': True}, {'text': 'Моя дорога, я не бачив тебе.', 'correct': False}, {'text': 'Шановна, мені нудно.', 'correct': False}, {'text': 'Мала, де ти є?', 'correct': False}]}, {'source': 'Could you please help me? (Polite)', 'options': [{'text': 'Чи не могли б Ви мені допомогти?', 'correct': True}, {'text': 'Поможи мені швидко.', 'correct': False}, {'text': 'Треба хелп.', 'correct': False}, {'text': 'Ви мусите допомогти.', 'correct': False}]}, {'source': "It's cringe. (Slang)", 'options': [{'text': 'Це крінж.', 'correct': True}, {'text': 'Це соромно.', 'correct': False}, {'text': 'Це незручно.', 'correct': False}, {'text': 'Це ганьба.', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Потрібно більше практики?' per template 'c1-checkpoint-module-template.md'
  - FIX: Add '## Потрібно більше практики?' section as specified in docs/l2-uk-en/templates/c1-checkpoint-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ⚠️ 1668/1750 (82 short)
- **Activities:** ✅ 14/14
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/4
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 20/15
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.4% (checkpoint - no gate)
- **Richness:** ✅ 85% (checkpoint)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 85% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 10 | 8 | 100% | 25% | 25.0% |
| review_sections | 32 | 3 | 100% | 20% | 20.0% |
| variety | 0.97 | - | 97% | 15% | 14.5% |
| engagement | 10 | 3 | 100% | 10% | 10.0% |
| cultural | 0 | - | 0% | 10% | 0.0% |
| visual | 2 | 3 | 67% | 10% | 6.7% |
| paragraph_var | 0.90 | - | 90% | 10% | 9.0% |
| **TOTAL** | | | | | **85.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 59 | Included in Core |
| **Огляд** | ⚪️ | 148 | Skipped |
| **Чому стиль важливий для кар'єри** | ⚪️ | 128 | Skipped |
| **Кейс-стаді: Дипломатичний скандал** | ⚪️ | 87 | Skipped |
| **Навички** | ⚪️ | 96 | Skipped |
| **Навичка 1: Ідентифікація регістру** | ⚪️ | 83 | Skipped |
| **Навичка 2: Трансформація тексту (Code-switching)** | ✅ | 62 | Included in Core |
| **Навичка 3: Ввічливість та Етикет** | ⚪️ | 77 | Skipped |
| **Навичка 4: Сленг та молодіжна мова** | ⚪️ | 36 | Skipped |
| **Навичка 5: Офіційно-діловий стиль** | ⚪️ | 49 | Skipped |
| **Поради для успішного складання тесту** | ⚪️ | 130 | Skipped |
| **Мій стилістичний паспорт** | ⚪️ | 110 | Skipped |
| **Поглиблений аналіз: Чотири сторони повідомлення** | ✅ | 352 | Included in Core |
| **Кейс-стаді: Літературні приклади** | ⚪️ | 125 | Skipped |
| **Need More Practice?** | ⚪️ | 66 | Skipped |
| **Підсумок** | ✅ | 60 | Included in Core |