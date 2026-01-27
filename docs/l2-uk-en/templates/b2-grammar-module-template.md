# B2 Grammar Module Template

**Purpose:** Reference template for B2 grammar modules (M01-40: Passive Voice, Participles, Register System, Numerals, Word Formation)

**Based on:** `b2-module-template.md` — inherits all B2 quality standards

**Related Issue:** [#305](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/305)

<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Пояснення|Граматика|Теорія
  - Трансформації
  - Підсумок
  - Потрібно більше практики?
  pedagogy: TTT
  min_word_count: 1750
  required_callouts: []
  description: B2 grammar uses TTT with register awareness and transformation activities
-->

---

## Quick Reference Checklist

Before submitting a B2 grammar module, verify all items from `b2-module-template.md` PLUS:

### Grammar-Specific Requirements

- [ ] **TTT pedagogy:** Test-Teach-Test structure (NOT narrative arc)
- [ ] **Authentic text:** 300-500+ word passage showing grammar in context (Тест section)
- [ ] **Register awareness:** Show how grammar varies across registers
- [ ] **4 passive forms:** If teaching passive, cover all 4 forms with register distribution
- [ ] **Transformation activities:** Active → Passive, register shifting
- [ ] **Decision framework:** "Як обрати?" section with clear decision rules

---

## Naturalness Quality Checklist

**Run this check during Stage 4 (Review & Fix) on prose activities.**

Before finalizing the module, verify prose activities (cloze, fill-in, unjumble with 5+ sentences) achieve:

- [ ] **Subject consistency** - Clear subjects maintained throughout passages
- [ ] **Discourse markers** - At least 2-3 connectors per 10-sentence passage (а, але, потім, тому, також, спочатку, нарешті)
- [ ] **Topic coherence** - All sentences contribute to unified narrative/theme, no random topic jumps
- [ ] **No template repetition** - Varied sentence structures across activities within the module
- [ ] **Moderate intensifiers** - Maximum 2-3 "дуже" per module, 0-1 "надзвичайно/справжній"
- [ ] **No double superlatives** - Use one precise descriptor instead of redundant pairs (e.g., "найкращий" NOT "найкращий та найвидатніший")
- [ ] **Natural transitions** - Avoid robotic "і це", "тому що... тому" patterns

**Target score:** 8/10 for content modules, 7/10 for checkpoints

**Red flags (score < target):**
- Same sentence template repeated across multiple activities
- Disconnected factoid lists without discourse markers
- Excessive intensifiers or double superlatives
- Robotic, mechanical transitions

**See:** `claude_extensions/stages/stage-4-review-fix.md` Section 9 for detailed naturalness criteria.

**For batch scanning:** Use `/scan-naturalness {level} {start} {end}` to scan completed modules.

---

## Module Structure (Grammar-Specific)

### 1. Frontmatter

```yaml
---
module: b2-XX
title: 'Ukrainian Grammar Title'
phase: 'B2.1a [Grammar & Register]' # or B2.1b [Grammar Completion]
pedagogy: 'TTT' # ALWAYS TTT for grammar modules
register: 'науковий' # Primary register for examples
tags:
  - grammar
  - [specific-topic: passive, participles, register, numerals, word-formation]
grammar:
  - 'Main grammar concept with specifics'
  - 'Register variation notes'
---
```

### 2. TTT Content Structure

#### Section 1: Тест (Test Phase) — 300-500 words

```markdown
## Тест: Прочитайте текст

[300-500 word authentic Ukrainian text (journalism/academic) containing target grammar]

**Аналіз:**

- Знайдіть усі приклади [target structure] у тексті.
- Яку функцію виконує [target structure] у кожному випадку?
- Як [target structure] взаємодіє з регістром тексту?
```

**Text source recommendations:**

- Офіційно-діловий: Ukrainian government documents, laws
- Науковий: Academic journal abstracts, Wikipedia Ukrainian
- Публіцистичний: Ukrainska Pravda, Radio Svoboda
- Художній: Contemporary Ukrainian prose (Serhiy Zhadan, Oksana Zabuzhko)

#### Section 2: Пояснення (Teach Phase) — 1000-1200 words

```markdown
## Пояснення

### [Grammar Concept in Ukrainian]

**Функція:** [Explain what this grammar does]

**Форми:**

| Форма    | Конструкція | Приклад   | Регістр                          |
| -------- | ----------- | --------- | -------------------------------- |
| [Form 1] | [Structure] | [Example] | [Style: офіційний/науковий/etc.] |
| [Form 2] | [Structure] | [Example] | [Style]                          |
| [Form 3] | [Structure] | [Example] | [Style]                          |
| [Form 4] | [Structure] | [Example] | [Style]                          |

### Регістрова варіація

[CRITICAL for B2: Show how the same meaning is expressed differently across registers]

| Регістр          | Форма            | Приклад   |
| ---------------- | ---------------- | --------- |
| Офіційно-діловий | [preferred form] | [example] |
| Науковий         | [preferred form] | [example] |
| Публіцистичний   | [preferred form] | [example] |
| Художній         | [preferred form] | [example] |
| Розмовний        | [preferred form] | [example] |

### Як обрати? (Decision Framework)

[Provide clear decision rules — B2 learners need explicit guidance]

**Питання 1:** [Question about context]

- Якщо [condition] → використовуйте [form]
- Якщо [condition] → використовуйте [form]

**Питання 2:** [Question about purpose]

- [More decision rules]

### Типові помилки

**Помилка 1: [Description]**

❌ Неправильно: [Example]
✅ Правильно: [Example]

**Чому?** [Explanation in Ukrainian]
```

#### Section 3: Практика (Test Phase 2) — 400-500 words

```markdown
## Практика

### Завдання 1: Трансформація

Перетворіть речення, використовуючи [target grammar]:

1. [Active/source sentence] → [Target form in specific register]
2. [Continue with 10+ items]

### Завдання 2: Вибір регістру

Яку форму ви оберете для кожної ситуації?

| Ситуація              | Регістр        | Ваша форма |
| --------------------- | -------------- | ---------- |
| [Professional email]  | офіційний      | [answer]   |
| [Casual conversation] | розмовний      | [answer]   |
| [News article]        | публіцистичний | [answer]   |

### Завдання 3: Написання (з Model Answer)

Напишіть текст (150+ слів) у [register] стилі, використовуючи [target grammar] мінімум 5 разів.

**Зразок відповіді:**

[Complete 150+ word model answer showing correct grammar usage in specified register]
```

---

## Grammar-Specific Activities

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/b2-01-passive.yaml`:**

```yaml
- type: essay-response
  title: Активний → Пасивний стан
  prompt: 'Трансформуйте в пасивний стан: Уряд прийняв закон.'
  model_answer: 'Закон прийнято урядом.'
- type: group-sort
  title: Регістрова класифікація
  groups:
    - name: Офіційно-діловий
      items:
        - Наказ видано.
    - name: Розмовний
      items:
        - Мені сказали.
```

---

### Transformation Activities (CRITICAL for Grammar)

**Defined in YAML as `type: essay-response` (for text) or `type: fill-in` (for sentences).**

### Register Identification Activities

**Defined in YAML as `type: group-sort`.**

### Error-Correction with Register Explanation

**Defined in YAML as `type: error-correction`.**

---

## Engagement Boxes for Grammar Modules

```markdown
> 📊 **Статистика регістру**
>
> [Data about which forms are most common in which registers — based on corpus data if available]

> ⚠️ **Поширена помилка**
>
> [Common error made by learners — often influenced by English or other L1]

> 🎯 **Регістр має значення**
>
> [Show same content in 2-3 registers — demonstrate how grammar choice affects tone]

> 📚 **У літературі**
>
> [Quote from Ukrainian literature showing target grammar in literary register]

> 📰 **У пресі**
>
> [Quote from Ukrainian journalism showing target grammar in journalistic register]
```

---

## Example Module Outline: M01 (Passive Voice Overview)

```markdown
# Пасивний стан: повна система

> 🎯 **Чому це важливо?**
> Пасивний стан — це базова граматична структура формальної української мови...

## Тест: Прочитайте текст

[300+ word news article with passive constructions]

## Пояснення

### Чотири форми пасивного стану

[Table: 4 forms with register distribution]

### Регістрова варіація

[5-register comparison table]

### Як обрати?

[Decision framework with 3-4 questions]

### Типові помилки

[3-4 common errors with corrections]

## Практика

### Завдання 1: Трансформація

### Завдання 2: Вибір регістру

### Завдання 3: Написання (Model Answer)

## Діалоги

[5-6 dialogues showing register variation]

# Підсумок

[Summary with self-assessment checklist]

---

## Content Structure Note

### Vocabulary & Activities

**CRITICAL:** Do NOT add `# Словник` or `# Активності` headers. These sections are injected automatically from:

- `vocabulary/b2-01-passive.yaml`
- `activities/b2-01-passive.yaml`
```

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/b2-module-template.md`
- **B2 Curriculum Plan:** `docs/l2-uk-en/B2-CURRICULUM-PLAN.md` (M01-40 grammar progression)
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
