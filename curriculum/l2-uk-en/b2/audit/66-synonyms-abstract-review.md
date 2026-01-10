# Audit Report: 66-synonyms-abstract.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть точне поняття' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** group-sort 'Рівні абстракції' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть інтелектуальну фразу' item 4 has 21 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY]** match-up 'Регістри та Поняття' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Думка та Наслідок' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q1 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q2 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q3 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q4 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q5 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q6 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q7 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Абстракції в культурі' Q8 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [знайдіть-точне-поняття] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [світ-ідей] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [рівні-абстракції] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [складіть-інтелектуальну-фразу] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [лабіринт-думок] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [відтінки-абстракції] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [виправте-думку] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [переклад-абстракцій] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [правда-про-ідеї] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [всі-форми-інтелекту] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [регістри-та-поняття] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [думка-та-наслідок] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [абстракції-в-культурі] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 66-synonyms-abstract.yaml: [стратегічні-поняття] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b2-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b2-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 29 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2524/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 87/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 28 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.4% (target 98-100% (vocab))
- **Richness:** ✅ 95% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 52 | 15 | 100% | 25% | 25.0% |
| engagement | 11 | 5 | 100% | 19% | 18.7% |
| variety | 0.95 | - | 95% | 12% | 11.9% |
| cultural | 3 | 4 | 75% | 12% | 9.4% |
| realworld | 8 | 3 | 100% | 12% | 12.5% |
| visual | 11 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 0.93 | - | 93% | 6% | 5.8% |
| questions | 11 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **95.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 74 | Included in Core |
| **Вступ: Лабіринти української думки** | ⚪️ | 95 | Skipped |
| **Частина 1: Світ Думки — Від «здогаду» до «переконання»** | ✅ | 171 | Included in Core |
| **Частина 2: Архітектура Теорії — Від «поняття» до «концепції»** | ✅ | 182 | Included in Core |
| **Частина 3: Логіка Аргументації — Від «підстави» до «висновку»** | ✅ | 121 | Included in Core |
| **Частина 6: Етика ідей та Інтелектуальна Відповідальність** | ✅ | 115 | Included in Core |
| **Частина 7: Абстрактні Поняття у Державотворенні** | ✅ | 143 | Included in Core |
| **Частина 8: Формування ідей у цифрову епоху** | ✅ | 97 | Included in Core |
| **Частина 9: Психологія Сприйняття та Уявлення про світ** | ✅ | 139 | Included in Core |
| **Частина 10: Логічна Стрункість Аргументації та доказовість** | ✅ | 92 | Included in Core |
| **Частина 11: Концепція Свободи в Українській Думці** | ✅ | 96 | Included in Core |
| **Частина 12: Логіка Наукового Пізнання та Відкриттів** | ✅ | 116 | Included in Core |
| **Частина 13: Формування Культури Дискусії** | ✅ | 79 | Included in Core |
| **Частина 11: Глибоке коріння української філософської думки** | ✅ | 174 | Included in Core |
| **Частина 12: Абстрактні Поняття в епоху Штучного Інтелекту** | ✅ | 126 | Included in Core |
| **Частина 13: Психологія ідей та їхній вплив на вчинки** | ✅ | 236 | Included in Core |
| **Частина 14: Інтелектуальна Стійкість у Світі Фейків** | ✅ | 161 | Included in Core |
| **Частина 15: Філософія Серця та Сучасні Цінності** | ✅ | 144 | Included in Core |
| **Підсумок** | ✅ | 53 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |