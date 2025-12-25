# C1 Literature Module Template

**Purpose:** Reference template for C1 literature modules (M146-160: Ukrainian Literary Canon — Classics through Contemporary)

**Based on:** `c1-module-template.md` — inherits all C1 quality standards

**Related Issue:** [#306](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/306)

---

## Quick Reference Checklist

Before submitting a C1 literature module, verify all items from `c1-module-template.md` PLUS:

### Literature-Specific Requirements
- [ ] **Literary analysis:** Close reading, stylistic analysis, thematic interpretation
- [ ] **Primary texts:** Full poems or 500-800 word prose excerpts
- [ ] **Comparative analysis:** 2+ texts compared (same author different works, or different authors)
- [ ] **Historical context:** Author's era, literary movement, political context
- [ ] **Rhetorical devices:** Identify and analyze метафора, іронія, символ, etc.
- [ ] **Critical essay:** Writing task with model answer

---

## Module Types in C1.6

### Classic Authors (M146-152)

| Modules | Author | Focus Works |
|---------|--------|-------------|
| M146-147 | Тарас Шевченко | Кобзар, Заповіт, Катерина |
| M148-149 | Іван Франко | Каменярі, Мойсей, prose |
| M150-151 | Леся Українка | Лісова пісня, драми, лірика |
| M152 | Classics Checkpoint | Integration |

### 20th Century (M153-155)

| Modules | Authors | Focus |
|---------|---------|-------|
| M153 | Розстріляне відродження | Хвильовий, Семенко, Підмогильний |
| M154 | Шістдесятники | Стус, Симоненко, Костенко |
| M155 | Діаспора | Маланюк, Антонич |

### Contemporary (M156-159)

| Modules | Authors | Focus |
|---------|---------|-------|
| M156 | Сучасна поезія | Жадан, Андрухович, Забужко |
| M157 | Сучасна проза | Романи, оповідання |
| M158 | Воєнна література | 2014-present |
| M159 | Literature Review | Integration |

### Final Exam (M160)

---

## Module Structure (Literature-Specific)

### 1. Frontmatter

```yaml
---
module: c1-1XX
title: "[Author/Work]: Literary Analysis"
phase: "C1.6 [Literature]"
pedagogy: "Literary Analysis"
register: "художній"  # Literary register
tags:
  - literature
  - [era: classic, 20th-century, contemporary]
  - [author-name]
  - [genre: poetry, prose, drama]
grammar:
  - "Literary syntax (inversions, archaic forms)"
  - "Stylistic devices"
vocabulary_focus:
  - "Літературознавча термінологія"
  - "Авторський стиль"
---
```

### 2. Literature Content Structure

#### Section 1: Author & Context — 300-400 words

```markdown
# [Author Name]: [Work/Theme Title]

> 🎯 **Чому це важливо?**
>
> [Author's significance in Ukrainian literature]
> [Why C1 learners must know this author/work]
> [Cultural/historical importance]

## Біографічний контекст

[Brief biography focusing on what shaped the writer — 150-200 words]

**Ключові дати:**

| Рік | Подія |
|-----|-------|
| [Year] | Народження [circumstances] |
| [Year] | [Key event in life] |
| [Year] | [Publication of major work] |
| [Year] | Смерть [circumstances] |

### Літературний рух

[Literary movement/school the author belongs to — 100-150 words]

> 📚 **Літературний контекст**
>
> [How this author fits into Ukrainian and European literary traditions]
```

#### Section 2: Primary Text — 500-800 words

```markdown
## Текст: [Title]

**Жанр:** [Genre]
**Рік публікації:** [Year]
**Контекст написання:** [Brief context]

---

> [Full poem OR 500-800 word prose excerpt]
>
> [If poem, include line numbers for analysis reference]

---

### Первинний аналіз

**Питання для першого читання:**

1. Про що цей текст? (фабула/сюжет)
2. Хто говорить? (наратор/ліричний герой)
3. До кого звернено? (адресат)
4. Який настрій/тон?
5. Які образи найбільш вражають?

> 💡 **Для розуміння**
>
> [Vocabulary or cultural notes needed to understand the text]
```

#### Section 3: Literary Analysis — 600-800 words

```markdown
## Літературознавчий аналіз

### Тематика

**Головна тема:** [Main theme]

**Додаткові теми:**
- [Theme 2]
- [Theme 3]
- [Theme 4]

[Analysis of themes — 150-200 words]

---

### Стилістичні засоби

| Засіб | Приклад із тексту | Функція |
|-------|-------------------|---------|
| Метафора | "[Quote]" (рядок X) | [Function] |
| Порівняння | "[Quote]" | [Function] |
| Іронія | "[Quote]" | [Function] |
| Символ | "[Image]" | [Symbolic meaning] |
| [Device] | "[Quote]" | [Function] |

[Analysis of how devices contribute to meaning — 150-200 words]

---

### Композиція

**Структура:**
- [Beginning — what it establishes]
- [Middle — development]
- [Climax — turning point]
- [End — resolution or open ending]

[Analysis of structure — 100-150 words]

---

### Мова автора

**Особливості авторського стилю:**
- Лексика: [archaic, dialectal, neologisms]
- Синтаксис: [inversions, parallelism, length of sentences]
- Звукопис: [alliteration, assonance, rhythm]

> 🔍 **Авторський стиль**
>
> [What makes this author's language distinctive]
```

#### Section 4: Comparative Analysis — 300-400 words

```markdown
## Порівняльний аналіз

### [Text 1] vs. [Text 2]

[Compare two texts — same author different periods, or different authors same theme]

| Аспект | [Text 1] | [Text 2] |
|--------|----------|----------|
| Тема | [Theme] | [Theme] |
| Настрій | [Mood] | [Mood] |
| Стиль | [Style] | [Style] |
| Символіка | [Symbols] | [Symbols] |

### Критичне мислення

**Питання для роздуму:**
1. Як історичний контекст впливає на текст?
2. Яка позиція автора? Як вона виражена?
3. Як цей текст перегукується із сучасністю?
4. Що робить цей текст класикою?
```

#### Section 5: Critical Essay — 300-400 words

```markdown
## Критичне есе

### Завдання

Напишіть критичне есе (400+ слів) на одну з тем:

1. [Essay topic 1 — thematic analysis]
2. [Essay topic 2 — stylistic analysis]
3. [Essay topic 3 — comparative analysis]

**Структура:**
1. Вступ (теза про текст)
2. Аналіз із цитатами (3-4 абзаци)
3. Висновок

**Вимоги:**
- Цитати з тексту з аналізом
- Літературознавча термінологія
- Власна інтерпретація

---

### Зразок відповіді

> [Complete 400+ word model essay demonstrating:
> - Literary analysis techniques
> - Proper citation of primary text
> - Use of literary terminology
> - Original interpretation
> - Academic register]

**Рубрика:**

| Критерій | C1 очікування |
|----------|---------------|
| Теза | Чітка, оригінальна інтерпретація |
| Аналіз | Детальний, із цитатами |
| Термінологія | Правильне використання |
| Аргументація | Логічна, переконлива |
| Стиль | Академічний регістр |
```

---

## Literature-Specific Activities

### Close Reading

```markdown
## quiz: Літературознавчий аналіз

1. Який стилістичний засіб використано у рядку: "Реве та стогне Дніпр широкий"?
   - [ ] Метафора
   - [x] Персоніфікація
   - [ ] Гіпербола
   - [ ] Літота
   > Дніпр "реве" і "стогне" — це персоніфікація (надання людських якостей неживому).

2. Що символізує образ "каменярів" у Франка?
   - [ ] Будівельників
   - [ ] Ремісників
   - [x] Борців за прогрес і свободу
   - [ ] Засуджених
   > "Каменярі" — це символ тих, хто будує майбутнє своєю працею.

[12+ literary analysis questions]
```

### Device Identification

```markdown
## mark-the-words: Стилістичні засоби

Відзначте всі метафори у вірші:

> [Full poem with markable metaphors]

[!markable] [list of metaphors to mark]
```

### Quote Analysis

```markdown
## fill-in: Аналіз цитати

1. "Реве та стогне Дніпр широкий" — це приклад [___].
   - [x] персоніфікації
   - [ ] метафори
   - [ ] порівняння
   > Дніпр наділяється людськими якостями (реве, стогне).

2. У вірші Шевченка "Заповіт" [___] є центральним мотивом.
   - [ ] кохання
   - [x] патріотизму і національного визволення
   - [ ] природи
   > "Заповіт" — це поетичний заповіт про боротьбу за свободу України.

[12+ quote analysis items]
```

### Author Comparison

```markdown
## group-sort: Автори та характеристики

- group: Тарас Шевченко
  - Романтизм
  - Народна мова
  - Кобзар

- group: Іван Франко
  - Реалізм + модернізм
  - Філософічність
  - Каменярі

- group: Леся Українка
  - Неоромантизм
  - Драматичні поеми
  - Європейські сюжети

- group: Василь Стус
  - Шістдесятництво
  - Екзистенціалізм
  - Табірна лірика

[20+ characteristics across 4-5 authors]
```

---

## Engagement Boxes for Literature Modules

```markdown
> 📚 **Літературний контекст**
>
> [How this work fits into literary tradition]

> 🎭 **Театральні постановки**
>
> [Notable stage/film adaptations]

> 🔍 **Авторський стиль**
>
> [What makes this author's language distinctive]

> 🏛️ **Історичний контекст**
>
> [Political/social context of the work]

> 💡 **Інтерпретації**
>
> [Different scholarly interpretations of the work]

> 📖 **Рекомендоване читання**
>
> [Other works by this author to read]
```

---

## Vocabulary Section for Literature Modules

```markdown
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| **ліричний герой** | lyrical persona | не автор, а голос у вірші |
| **наратор** | narrator | той, хто розповідає |
| **фабула** | plot, fabula | що відбувається |
| **сюжет** | narrative, sujet | як розповідається |
| **метафора** | metaphor | неявне порівняння |
| **символ** | symbol | образ із глибшим значенням |
| **алегорія** | allegory | розгорнута метафора |
| **іронія** | irony | протилежне значення |
| **класицизм** | classicism | літературний напрям |
| **романтизм** | romanticism | літературний напрям |
| **модернізм** | modernism | літературний напрям |
| **розстріляне відродження** | Executed Renaissance | покоління 1920-х |
| [35+ literary terms] | | |
```

---

## Module Breakdown: C1.6 Literature

### Classics (M146-152)

| Author | Modules | Focus Works |
|--------|---------|-------------|
| Шевченко | M146-147 | Кобзар: Заповіт, Катерина, Сон |
| Франко | M148-149 | Каменярі, Мойсей, проза |
| Леся Українка | M150-151 | Лісова пісня, драми |
| Checkpoint | M152 | Integration |

### 20th Century (M153-155)

| Era | Modules | Authors |
|-----|---------|---------|
| Розстріляне відродження | M153 | Хвильовий, Семенко, Підмогильний |
| Шістдесятники | M154 | Стус, Симоненко, Костенко |
| Діаспора | M155 | Маланюк, Антонич |

### Contemporary (M156-159)

| Focus | Modules | Authors |
|-------|---------|---------|
| Сучасна поезія | M156 | Жадан, Андрухович |
| Сучасна проза | M157 | Забужко, Прохасько |
| Воєнна література | M158 | 2014-2024 |
| Literature Review | M159 | Integration |

### Final Exam (M160)

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/c1-module-template.md`
- **C1 Curriculum Plan:** `docs/l2-uk-en/C1-CURRICULUM-PLAN.md` (M146-160 specifications)
- **LIT Track Template:** `docs/l2-uk-en/templates/lit-module-template.md`
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
