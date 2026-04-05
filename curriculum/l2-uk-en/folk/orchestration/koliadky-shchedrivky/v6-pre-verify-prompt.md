<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 1: Колядки та щедрівки: Міф про створення світу (FOLK, FOLK.1)

## Plan vocabulary to verify

- колядка
- щедрівка
- космогонія
- світове дерево
- засівання
- паралелізм
- обрядовий
- автохтонний
- стилізація
- солярний

## Sections to research

- **Розминка**: Провокаційне питання: Чи є колядки християнськими піснями — чи язичницькими обрядами в християнській оболонці?; Цитата з архаїчної колядки — «Коли не було знащада світа...» — без пояснень, лише текст; Студент має сформулювати першу гіпотезу до кінця модуля
- **Конфліктна карта: Хто «винайшов» колядку?**: Дебат 1: Латинське походження (calendae) vs автохтонне слов'янське — Костомаров vs сучасні етнолінгвісти; Дебат 2: Дохристиянський обряд vs пізня стилізація — чи архаїчні мотиви справді давні, чи реконструйовані романтиками?; [!epistemic-humility] «За версією Костомарова... Попович натомість вказує...» — подавати як дискусію, не як факт
- **Читання: Космогонічний міф у тексті колядки**: Повний текст архаїчної колядки з Карпат (мотив пірнання птахів у первісне море); Світове дерево (явір) як axis mundi — зв'язок із індоєвропейською міфологією; Тріада у колядках: господар = місяць, господиня = сонце, діти = зорі (Попович)
- **Аналіз: Поетика та ритуальна функція**: Формульні зачини, паралелізм, рефрени («Даж Бог!», «Ой рано-рано!»); Не просто «красиво» — кожен прийом має магічну функцію: повтор = закріплення заклинання; Щедрівки та Маланка — новорічний цикл, засівання, ґендерні ролі у виконанні
- **Дискусія: Що вижило і чому?**: Колядки пережили християнізацію, татарські навали, радянський атеїзм — чому?; Гіпотези: ритуальна необхідність (календарний цикл не зупиниш) vs прихована резистентність vs простий консерватизм побуту; [!anti-hagiography] Не романтизувати — колядки також містили антисемітські та ксенофобські мотиви. Як з цим працювати?
- **Підсумок**: Повернення до початкового питання — студент формулює відповідь; Ключова теза модуля: колядки — не музейний експонат, а живий інструмент культурної ідентичності

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Search textbooks for each section topic

For each section title above, call `search_text` with the Ukrainian keywords.

Report the most relevant textbook excerpt for each section (author, grade, key quote).

### Task 3: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 4: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 5: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (FOLK).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Textbook Excerpts
### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
