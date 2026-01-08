# Audit Report: 70-b2-checkpoint.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** Assessment | **Target:** 1000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Граматичний Checkpoint' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фразеологічна перевірка' Q1 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фразеологічна перевірка' Q2 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фразеологічна перевірка' Q3 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фразеологічна перевірка' Q4 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фразеологічна перевірка' Q5 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фразеологічна перевірка' Q6 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фразеологічна перевірка' Q7 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фразеологічна перевірка' Q8 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** group-sort 'Синтаксичний лабіринт' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Синонімічний Checkpoint' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Регістри та Ситуації' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний вердикт' Q1 prompt length 3 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний вердикт' Q2 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний вердикт' Q3 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний вердикт' Q4 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний вердикт' Q5 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний вердикт' Q6 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний вердикт' Q7 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний вердикт' Q8 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний синтаксис' Q1 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний синтаксис' Q2 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний синтаксис' Q3 prompt length 3 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний синтаксис' Q4 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний синтаксис' Q5 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний синтаксис' Q6 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний синтаксис' Q7 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фінальний синтаксис' Q8 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 70-b2-checkpoint.yaml: [фразеологічна-перевірка] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 70-b2-checkpoint.yaml: [фінальний-переклад] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 70-b2-checkpoint.yaml: [арсенал-b2.2] select: 'items.0.options' - [{'text': 'відмінювати числівники', 'correct': True}, {'text': 'вживати ідіоми', 'correct': True}, {'text': 'будувати складні речення', 'correct': True}, {'text': 'розрізняти синоніми', 'correct': True}, {'text': 'використовувати абстрактну лексику', 'correct': True}, {'text': 'трансформувати тексти', 'correct': True}, {'text': 'володіти стилістичними регістрами', 'correct': True}, {'text': 'аналізувати підтекст', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 70-b2-checkpoint.yaml: [фінальний-вердикт] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 70-b2-checkpoint.yaml: [самодіагностика] select: 'items.0.options' - [{'text': 'розумію синоніми', 'correct': True}, {'text': 'відмінюю числівники', 'correct': True}, {'text': 'вживаю сполучники', 'correct': True}, {'text': 'знаю ідіоми', 'correct': True}, {'text': 'відчуваю регістри', 'correct': True}, {'text': 'можу написати есей', 'correct': True}, {'text': 'готовий до історії', 'correct': True}, {'text': 'ціную мову', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 70-b2-checkpoint.yaml: [фінальний-синтаксис] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 34 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1150/1000
- **Activities:** ✅ 15/15
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 4/4
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 26/10
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 34 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.6% (checkpoint - no gate)
- **Richness:** ✅ 89% (checkpoint)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 89% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 10 | 8 | 100% | 25% | 25.0% |
| review_sections | 30 | 3 | 100% | 20% | 20.0% |
| variety | 0.97 | - | 97% | 15% | 14.5% |
| engagement | 5 | 3 | 100% | 10% | 10.0% |
| cultural | 0 | - | 0% | 10% | 0.0% |
| visual | 4 | 3 | 100% | 10% | 10.0% |
| paragraph_var | 1.00 | - | 100% | 10% | 10.0% |
| **TOTAL** | | | | | **89.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 79 | Included in Core |
| **Навичка 1: Граматичний фундамент — Числівники та Дати** | ⚪️ | 172 | Skipped |
| **Навичка 2: Словотвір та Морфологічна компетентність** | ⚪️ | 145 | Skipped |
| **Навичка 3: Синтаксичні конструкції та Стилістичні Регістри** | ⚪️ | 106 | Skipped |
| **Навичка 4: Фразеологічний арсенал — Прислів'я та Ідіоми** | ⚪️ | 148 | Skipped |
| **Навичка 5: Архітектура думки — Складні Сполучники та Логіка** | ⚪️ | 143 | Skipped |
| **Навичка 6: Синонімічна палітра та Глибокий Аналіз у контексті** | ✅ | 115 | Included in Core |
| **Навичка 7: Творча трансформація та Фінальний Синтез знань** | ⚪️ | 97 | Skipped |
| **Підготовка: Самодіагностика перед великим Assessment** | ✅ | 101 | Included in Core |
| **Підсумок** | ✅ | 44 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |