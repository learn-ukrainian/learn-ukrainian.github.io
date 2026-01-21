# Audit Report: M94 — 94-b2-final-exam.md
**Level:** B2 | **Module:** M94 | **Phase:** B2.4 | **Pedagogy:** TTT | **Target:** 4000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 94-b2-final-exam.yaml: Schema validation error at key '14': {'type': 'select', 'title': 'Множинний вибір - Характеристики професійного спілкування', 'instruction': 'Оберіть усі правильні варіанти (може бути більше одного).', 'items': [{'question': "Які елементи обов'язкові в професійному листі?", 'min_correct': 3, 'options': [{'text': 'Формальне звертання', 'correct': True}, {'text': 'Чітка структура', 'correct': True}, {'text': 'Повний підпис з посадою', 'correct': True}, {'text': 'Смайлики', 'correct': False}, {'text': 'Англіцизми', 'correct': False}], 'explanation': 'Професійний лист має містити формальне звертання, структуру та повний підпис.'}, {'question': 'Які розділи входять до стандартного звіту?', 'min_correct': 4, 'options': [{'text': 'Вступ', 'correct': True}, {'text': 'Аналіз даних', 'correct': True}, {'text': 'Висновки', 'correct': True}, {'text': 'Рекомендації', 'correct': True}, {'text': 'Привітання', 'correct': False}], 'explanation': 'Стандартний звіт містить Вступ, Аналіз, Висновки та Рекомендації.'}, {'question': 'Які ознаки вказують на упередження в медіатексті?', 'min_correct': 3, 'options': [{'text': 'Емоційно забарвлена лексика', 'correct': True}, {'text': 'Відсутність альтернативних точок зору', 'correct': True}, {'text': 'Апеляція до емоцій замість фактів', 'correct': True}, {'text': 'Конкретні цифри та джерела', 'correct': False}, {'text': 'Нейтральна мова', 'correct': False}], 'explanation': 'Упередження проявляється через емоційність, однобічність та маніпуляції замість фактів.'}, {'question': 'Які елементи важливі для ефективної презентації?', 'min_correct': 3, 'options': [{'text': 'Чітка структура', 'correct': True}, {'text': 'Тези з підтвердженням даними', 'correct': True}, {'text': 'Вміння відповідати на питання', 'correct': True}, {'text': 'Багато тексту на слайдах', 'correct': False}, {'text': 'Читання з паперу', 'correct': False}], 'explanation': 'Ефективна презентація має структуру, тези з даними та інтерактивність.'}, {'question': 'Які фрази допомагають у конструктивній дискусії?', 'min_correct': 3, 'options': [{'text': 'По-перше, по-друге, по-третє', 'correct': True}, {'text': 'Однак, проте, водночас', 'correct': True}, {'text': 'Пропоную компроміс', 'correct': True}, {'text': 'Ви не маєте рації', 'correct': False}, {'text': 'Це абсурд', 'correct': False}], 'explanation': "Конструктивна дискусія використовує логічні зв'язки та пошук компромісу."}, {'question': 'Що допомагає виявити фейкові новини?', 'min_correct': 3, 'options': [{'text': 'Перевірка первинних джерел', 'correct': True}, {'text': 'Пошук підтвердження в інших медіа', 'correct': True}, {'text': 'Аналіз дати публікації', 'correct': True}, {'text': 'Кількість лайків', 'correct': False}, {'text': 'Популярність у соцмережах', 'correct': False}], 'explanation': 'Фактчекінг вимагає перевірки джерел, крос-референсів та контексту.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ' per template 'b2-module-template.md'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/b2-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення' per template 'b2-module-template.md'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b2-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 40/100)

- Revision recommended (severity 40/100)
- 5 violations (moderate)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ❌ 2387/4000
- **Activities:** ❌ 0/3
- **Density:** ❌ 0 < 1
- **Unique_types:** ❌ 0/2 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 5/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 45/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 3-10)
- **Immersion:** 🇺🇦 95.8% (target 90-100% (history))
- **Richness:** ❌ 85% < 95% min (grammar)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 85% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 53 | 24 | 100% | 20% | 20.0% |
| engagement | 5 | 5 | 100% | 15% | 15.0% |
| dialogues | 1 | 4 | 25% | 15% | 3.8% |
| variety | 0.97 | - | 97% | 10% | 9.7% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| realworld | 5 | 3 | 100% | 10% | 10.0% |
| visual | 9 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 53 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **85.2%** |

### Dryness Flags & Fixes
- ❌ **LOW_DIALOGUE**
  - FIX:
    Add more mini-dialogues (need 4+ total). Use this exact format:
    
    **Діалог: [Location in Ukraine]**
    
    > — [Speaker 1 line with **bolded** grammar examples]
    > — [Speaker 2 response with **bolded** grammar examples]
    > — [Speaker 1 continuation]
    > — [Speaker 2 conclusion]

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 88 | Included in Core |
| **B2 Підсумковий іспит** | ⚪️ | 64 | Skipped |
| **Огляд** | ⚪️ | 117 | Skipped |
| **Навичка 1: Професійна електронна пошта (M85-86)** | ⚪️ | 292 | Skipped |
| **Навичка 2: Професійні звіти (M87-88)** | ⚪️ | 321 | Skipped |
| **Навичка 3: Критичний аналіз новин (M89-90)** | ✅ | 234 | Included in Core |
| **Навичка 4: Презентаційні навички (M91-92)** | ⚪️ | 396 | Skipped |
| **Навичка 5: Дискусії та дебати (M93)** | ⚪️ | 446 | Skipped |
| **Інтеграційне завдання** | ⚪️ | 81 | Skipped |
| **Підсумок** | ✅ | 88 | Included in Core |
| **Самоперевірка: Чи готові ви до C1?** | ⚪️ | 169 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 91 | Skipped |