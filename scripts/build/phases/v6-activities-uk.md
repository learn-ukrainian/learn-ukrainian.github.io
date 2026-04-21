<!-- version: 0.1.0 | created: 2026-04-21 | Ukrainian-canonical activities -->
# V6 Activity Generation — Ukrainian-Canonical YAML

Ви генеруєте `activities/{MODULE_SLUG}.yaml` для українського модуля.

## Контекст треку

Це **українсько-канонічний** трек. Учень працює українською мовою без англомовного мосту.

## Жорсткі правила

1. **Усі інструкції й task stems — українською.**
2. **Жодних translate-from-English шаблонів**, якщо план прямо цього не вимагає.
3. Вправи мають перевіряти **мовну механіку української**:
   - наголос
   - звук/буква
   - складоподіл
   - рід іменника
   - відмінок
   - вид дієслова
   - узгодження
   - природний вибір форми або конструкції
4. **Не тестуйте знання теми замість мови.**
5. **Усі українські слова мають бути заземлені** в прозі модуля або в `vocabulary_hints`.

## Числовий контракт

| Bucket | Min | Max |
|---|---|---|
| Total activities | {TOTAL_TARGET} | {TOTAL_TARGET}+ |
| Inline | {INLINE_MIN} | {INLINE_MAX} |
| Workbook | {WORKBOOK_MIN} | {WORKBOOK_MAX} |
| Items per activity | {ITEMS_MIN} | — |

**Не можна** падати нижче мінімумів.

## Дозволені типи

- Inline: {INLINE_ALLOWED_TYPES}
- Inline priority: {INLINE_PRIORITY_TYPES}
- Workbook: {WORKBOOK_ALLOWED_TYPES}
- Workbook priority: {WORKBOOK_PRIORITY_TYPES}
- Forbidden: {FORBIDDEN_ACTIVITY_TYPES}

## Маркери ін'єкції

{INJECTION_MARKERS}

Кожна inline-вправа мусить мати `id`, який **точно** збігається з маркером у прозі.

## Підказки з плану

{PLAN_ACTIVITY_HINTS}

## Планова лексика

{PLAN_VOCABULARY}

## Проза модуля

<module_content>
{MODULE_CONTENT}
</module_content>

## Формат виводу

Виведіть **лише сирий YAML**. Перший рядок: `version: "1.0"`.

```yaml
version: "1.0"
module: {MODULE_SLUG}
level: {LEVEL}
inline:
  - id: marker-id
    type: quiz
    instruction: "Оберіть правильний варіант"
    items:
      - question: "_____ стіл"
        options: ["цей", "ця", "це"]
        correct: 0
workbook:
  - id: case-practice
    type: fill-in
    instruction: "Вставте правильну форму"
    items:
      - sentence: "Я бачу ____."
        answer: "сестру"
```

## Схема полів за типами — ДОТРИМУЙТЕСЬ ТОЧНО

**КРИТИЧНО:** назви полів у YAML мають збігатися з цією схемою дослівно.
Перекладати назви полів НЕ МОЖНА — `pairs[{left, right}]` залишається
саме `left`/`right`, не `prompt`/`answer` і не «запитання/відповідь».
Текст значень — українською, а структура — як тут. Валідатор схеми
відхиляє альтернативні назви полів.

### Ядрові типи (A1-C2)

- **quiz**: `id`, `instruction`, `items: [{question, options[], correct}]`
- **fill-in**: `id`, `instruction`, `items: [{sentence, answer}]`.
  Порожнє місце позначайте `____` (чотири підкреслення), НЕ `{word}`.
- **match-up**: `id`, `instruction`, `pairs: [{left, right}]`. Мін. 3 пари.
  (Не `prompt`/`answer`, не `word`/`translation` — саме `left` і `right`.)
- **group-sort**: `id`, `instruction`, `groups: [{label, items[]}]`. Мін. 2 групи.
  (Не `title`/`items`, не `category`/`words` — саме `label` і `items`.)
- **classify**: `id`, `instruction`, `categories: [{label, items[]}]`.
  (Структура як `group-sort`, але ключ верхнього рівня `categories`.)
- **true-false**: `id`, `instruction`, `items: [{statement, correct}]`.
  `correct` — boolean `true`/`false`. (Не `answer`.)
- **error-correction**: `id`, `instruction`, `items: [{sentence, error, correction}]`.
  Опційно: `error_type` (одне з `"word"`, `"phrase"`, `"register"`, `"construction"`),
  `options[]`, `explanation`.
- **anagram**: `id`, `instruction`, `items: [{letters[], answer}]`.
  `letters` — масив літер, не рядок. (Не `scrambled`.)
- **translate**: `id`, `instruction`, `items: [{source}]`. Для варіантів — `options[]`.
- **unjumble**: `id`, `instruction`, `items: [{words[], correct_order[]}]`.
  `correct_order` — масив **РЯДКІВ** (слова в правильному порядку), не індексів.
- **order**: `id`, `instruction`, `items: []` (масив рядків), `correct_order[]` —
  ВЕРХНЬОРІВНЕВИЙ масив **цілих** (0-base індекси). Не всередині кожного item.
- **observe**: `id`, `examples[]`, `prompt`.

### Українська педагогіка (A1 фонетика / склади)

- **divide-words**: `id`, `instruction`, `items: [{word, answer}]`.
  Приклад: `word: "молоко"`, `answer: "мо-ло-ко"`. НЕ додавайте `hint:`.
- **count-syllables**: `id`, `items: [{word, correct}]`. Опційно: `instruction`, `maxCount`.
- **pick-syllables**: `id`, `syllables[]`, `correctIndices[]`, `category`.
- **odd-one-out**: `id`, `items: [{words[], correct, explanation}]`. `correct` — 0-base індекс.
- **image-to-letter**: `id`, `instruction`, `items: [{image, letter}]`. Опційно `options[]`.
- **letter-grid**: `id`, `letters: [{upper, lower}]`. Опційно `name`, `emoji`, `key_word`.
- **phrase-table**: `id`, `groups: [{label, phrases[]}]`.

### Типові помилки, на яких падає валідатор

- `{item, group}` замість `{label, items[]}` → ❌ валідатор відхиляє
- `{prompt, answer}` замість `{left, right}` → ❌ валідатор відхиляє
- `{scrambled, answer}` замість `{letters[], answer}` → ❌ валідатор відхиляє
- рядок замість масиву для `letters` / `items` / `options` → ❌ валідатор відхиляє

Поля значень — українською. **Ключі полів — як у схемі вище, не перекладати.**

## Які патерни заборонені

- англійські інструкції
- фрази типу “Translate into Ukrainian”
- exercises that ask about dates/names/facts instead of Ukrainian forms
- wall of quiz/true-false when richer types are allowed

## Рівневий контекст

{LEVEL_CONTEXT}

## Педагогічні патерни

{PEDAGOGY_PATTERNS}

## Мінімальні item-count правила

{ITEM_MINIMUMS_TABLE}
