# Audit Report: 106-vistovtsi-neoclassicists.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1400
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст 1920-х' Q1 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст 1920-х' Q2 prompt length 8 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст 1920-х' Q3 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст 1920-х' Q4 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст 1920-х' Q5 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст 1920-х' Q6 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст 1920-х' Q7 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний контекст 1920-х' Q8 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** match-up 'Постаті та ідеї' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** group-sort 'Неокласики vs Романтики' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати епохи' item 1 has 11 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати епохи' item 4 has 12 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати епохи' item 5 has 10 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY]** match-up 'Стилі та групи' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Трагедія Сандармоху' Q1 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Трагедія Сандармоху' Q2 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Трагедія Сандармоху' Q3 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Трагедія Сандармоху' Q4 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Трагедія Сандармоху' Q5 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Трагедія Сандармоху' Q6 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Трагедія Сандармоху' Q7 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Трагедія Сандармоху' Q8 prompt length 8 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** group-sort 'Символи 1920-х' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Культурні локації' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 106-vistovtsi-neoclassicists.yaml: [культурний-контекст-1920-х] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 106-vistovtsi-neoclassicists.yaml: [лексика-1920-х] fill-in: 'items.7.options' - ['азіатського', 'північного', 'старого'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 106-vistovtsi-neoclassicists.yaml: [факти-чи-вигадки] true-false: 'items.2' - 'statement' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 106-vistovtsi-neoclassicists.yaml: [ознаки-епохи] select: 'items.0.options' - [{'text': 'українізація', 'correct': True}, {'text': 'Березіль', 'correct': True}, {'text': 'психологічна Європа', 'correct': True}, {'text': "будинок 'Слово'", 'correct': True}, {'text': 'розстріляне відродження', 'correct': True}, {'text': 'азіатський ренесанс', 'correct': True}, {'text': 'сонет (неокласики)', 'correct': True}, {'text': 'експресіонізм', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 106-vistovtsi-neoclassicists.yaml: [трагедія-сандармоху] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 106-vistovtsi-neoclassicists.yaml: [постаті-в-історії] fill-in: 'items.7.options' - ['Сосюра', 'Тичина', 'Рильський'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 32 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2836/1400
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 9/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 162/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 32 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.9% (target 98-100% (history))
- **Richness:** ✅ 99% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 77 | 15 | 100% | 25% | 25.0% |
| engagement | 10 | 5 | 100% | 19% | 18.7% |
| variety | 0.97 | - | 97% | 12% | 12.1% |
| cultural | 10 | 4 | 100% | 12% | 12.5% |
| realworld | 8 | 3 | 100% | 12% | 12.5% |
| visual | 20 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 12 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **99.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ: Харків — столиця відродження** | ⚪️ | 301 | Skipped |
| **Частина 1: Українізація — Вимушений маневр чи Шанс на свободу?** | ✅ | 111 | Included in Core |
| **Частина 2: Микола Хвильовий та концепція «Геть від Москви!»** | ✅ | 178 | Included in Core |
| **Частина 3: Неокласики — Культ розуму, гармонії та форми** | ✅ | 199 | Included in Core |
| **Частина 4: Театр «Березіль» та Авангардне мистецтво** | ✅ | 175 | Included in Core |
| **Частина 5: Будинок «Слово» — Рай для творців, що став пасткою** | ✅ | 122 | Included in Core |
| **Частина 6: Великий терор та Кривавий Фінал відродження** | ✅ | 160 | Included in Core |
| **Частина 7: Деколонізація пам'яті сьогодні** | ✅ | 604 | Included in Core |
| **Частина 8: Спадщина Леся Курбаса в сучасному театрі** | ✅ | 120 | Included in Core |
| **Частина 9: Архітектурне обличчя Харкова: Держпром та конструктивізм** | ✅ | 121 | Included in Core |
| **Частина 10: Жіночі обличчя Розстріляного відродження** | ✅ | 273 | Included in Core |
| **Частина 9: Архітектурне обличчя Харкова та Конструктивізм** | ✅ | 191 | Included in Core |
| **Частина 10: Літературний калейдоскоп: ВАПЛІТЕ, МАРС та інші** | ✅ | 143 | Included in Core |
| **Підсумок** | ✅ | 51 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |