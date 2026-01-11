# Audit Report: 111-holodomor-ii-pamiat.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 111-holodomor-ii-pamiat.yaml: Array validation: {'type': 'translate', 'title': 'Англомовні поняття', 'instruction': 'Оберіть правильний переклад.', 'items': [{'sentence': 'Голодомор is a crime against humanity.', 'options': [{'text': 'Голодомор — це злочин проти людства.', 'correct': True}, {'text': 'Голодомор — це помилка природи.', 'correct': False}, {'text': 'Голодомор — це трагедія села.', 'correct': False}, {'text': 'Голодомор — це військова операція.', 'correct': False}]}, {'sentence': 'Denial is the final stage of genocide.', 'options': [{'text': 'Заперечення — це остання стадія геноциду.', 'correct': True}, {'text': 'Визнання — це початок геноциду.', 'correct': False}, {'text': 'Забуття — це мета геноциду.', 'correct': False}, {'text': 'Покарання — це наслідок геноциду.', 'correct': False}]}, {'sentence': 'Freedom of speech matters.', 'options': [{'text': 'Свобода слова має значення.', 'correct': True}, {'text': 'Свобода слова небезпечна.', 'correct': False}, {'text': 'Свобода слова скасована.', 'correct': False}, {'text': 'Свобода слова дорога.', 'correct': False}]}, {'sentence': 'Never again.', 'options': [{'text': 'Ніколи знову.', 'correct': True}, {'text': 'Завжди поруч.', 'correct': False}, {'text': 'Знову і знову.', 'correct': False}, {'text': 'Можливо колись.', 'correct': False}]}, {'sentence': 'Memory is a weapon.', 'options': [{'text': "Пам'ять — це зброя.", 'correct': True}, {'text': "Пам'ять — це біль.", 'correct': False}, {'text': "Пам'ять — це історія.", 'correct': False}, {'text': "Пам'ять — це життя.", 'correct': False}]}, {'sentence': 'The truth will prevail.', 'options': [{'text': 'Правда переможе.', 'correct': True}, {'text': 'Правда загине.', 'correct': False}, {'text': 'Правда не важлива.', 'correct': False}, {'text': 'Правда — це брехня.', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 111-holodomor-ii-pamiat.yaml: [index-0] quiz: 'items.7' - 'question' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 111-holodomor-ii-pamiat.yaml: [index-5] select: 'items.5' - 'question' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 111-holodomor-ii-pamiat.yaml: [index-7] quiz: 'items.7' - 'question' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 111-holodomor-ii-pamiat.yaml: [index-10] translate: 'items.5' - 'source' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Контекст і причини, Вступ
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Деколонізаційний погляд' per template 'b2-history-module-template'
  - FIX: Add '## Деколонізаційний погляд' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md

## Recommendation
**📝 UPDATE** (severity 55/100)

- Revision recommended (severity 55/100)
- 10 violations (significant)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ❌ 1858/2000
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 16 < 20 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 7 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 10-14)
- **Immersion:** 🇺🇦 98.2% (target 90-100% (history))
- **Richness:** ✅ 97% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 14 | 3 | 100% | 24% | 23.8% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 6 | 2 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 6 | 4 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 6 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 95 | Included in Core |
| **Вступ** | ⚪️ | 170 | Skipped |
| **Частина 1: Механізм Заперечення** | ✅ | 548 | Included in Core |
| **Частина 2: Первинні джерела та свідчення** | ✅ | 308 | Included in Core |
| **Частина 3: Деколонізація пам'яті та сучасність** | ✅ | 550 | Included in Core |
| **Підсумок** | ✅ | 77 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |