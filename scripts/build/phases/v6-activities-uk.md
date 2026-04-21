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
