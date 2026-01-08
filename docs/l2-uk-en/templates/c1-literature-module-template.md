# C1 Literature Module Template

**Purpose:** Reference template for C1 literature modules (M146-160: Ukrainian Literary Canon — Classics through Contemporary)

**Based on:** `c1-module-template.md` — inherits all C1 quality standards

**Related Issue:** [#306](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/306)


<!--
TEMPLATE_METADATA:
  required_sections:
  - Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка
  - Текст
  - Літературний аналіз
  - Summary|Підсумок
  - Need More Practice?
  pedagogy: Immersion
  min_word_count: 2500
  required_callouts: []
  description: C1 literature modules analyze Ukrainian literary works
-->

---

## Quick Reference Checklist

Before submitting a C1 literature module, verify all items from `c1-module-template.md` PLUS:

### Literature-Specific Requirements
- [ ] **Literary analysis:** Close reading, stylistic analysis, thematic interpretation
- [ ] **Primary texts:** Full poems or 500-800 word prose excerpts using `[!quote]` callouts
- [ ] **Comparative analysis:** 2+ texts compared (same author different works, or different authors)
- [ ] **Historical context:** Author's era, literary movement, political context
- [ ] **Rhetorical devices:** Identify and analyze метафора, іронія, символ, etc.
- [ ] **Reading tasks (2-3):** External reading assignments with stylistic analysis questions
- [ ] **Critical essay:** 400+ word essay with model answer and rubric
- [ ] **Activity count:** 10-12 language-focused activities (NOT 14+)
- [ ] **NO CONVERSATIONAL DIALOGS:** Literature modules focus on TEXTUAL ANALYSIS. Do NOT add conversational dialogs between learners or fictional scenarios. If a literary work contains dialogue (e.g., drama, prose), analyze it—don't simulate it.

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

## Reading Tasks (External Assignments)

Literature modules should include **2-3 external reading tasks** for deeper engagement with primary texts and literary criticism.

```yaml
# In activities/{slug}.yaml

- type: reading
  id: c1-146-reading-01
  title: "Повний текст твору"
  resource:
    type: primary_source
    url: "https://www.ukrlib.com.ua/..."
    title: "Тарас Шевченко. Заповіт (повний текст)"
  tasks:
    - "Знайдіть у тексті три приклади майбутнього часу. Чому автор їх використовує?"
    - "Які дієслова наказового способу є в тексті? Який ефект вони створюють?"
    - "Порівняйте мову поета з сучасною українською. Які слова змінили значення?"

- type: reading
  id: c1-146-reading-02
  title: "Літературознавчий аналіз"
  resource:
    type: article
    url: "https://..."
    title: "[Ukrainian literary critic's analysis]"
  tasks:
    - "Як автор статті використовує літературознавчу термінологію?"
    - "Знайдіть приклади академічного регістру в тексті"
    - "Порівняйте інтерпретацію критика з аналізом у модулі"

- type: reading
  id: c1-146-reading-03
  title: "Порівняльний аналіз"
  resource:
    type: article
    url: "https://..."
    title: "[Another poem by same author]"
  tasks:
    - "Порівняйте стилістичні засоби двох творів"
    - "Як змінюється мова автора між ранніми та пізніми творами?"
    - "Які теми повторюються?"
```

**Note:** Questions focus on LINGUISTIC and STYLISTIC analysis, not literary interpretation alone.

---

## Literature-Specific Activities

### CRITICAL: Language Practice, Not Content Testing

<critical>

**These are LANGUAGE lessons that use literature as context, NOT literature exams taught in Ukrainian.**

**The Golden Rule:** "Can the learner answer this without reading the Ukrainian text?"
- **If YES** → Rewrite (tests content recall, not language)
- **If NO** → Keep (tests Ukrainian comprehension)

### Examples: GOOD vs BAD Activities

**❌ BAD (Tests Literary Facts):**
```markdown
1. У якому році написаний "Заповіт"?
   - [x] 1845
```
Problem: Tests dates. Can be answered from prior knowledge.

**❌ BAD (Tests Interpretation from Memory):**
```markdown
1. Що символізує образ Дніпра в поезії Шевченка?
   - [x] Волю України
```
Problem: Tests literary knowledge. Students can answer without reading Ukrainian module text.

**✅ GOOD (Tests Ukrainian Language):**
```markdown
1. Згідно з аналізом у модулі, який стилістичний засіб автор виділяє в рядку "Реве та стогне Дніпр широкий"?
   - [x] Автор визначає це як персоніфікацію
```
Why GOOD: Requires reading the MODULE'S ANALYSIS in Ukrainian, tests comprehension of Ukrainian literary terminology.

**✅ GOOD (Tests Ukrainian Collocations):**
```markdown
1. Шевченко [___] визначну роль у розвитку української літератури.
   - [x] відіграв
```
Why GOOD: Tests fixed collocation (відіграти роль), requires understanding Ukrainian usage.

**Key phrases to use:**
- "Згідно з текстом модуля..."
- "У тексті аналізу автор..."
- "Як автор інтерпретує/тлумачить/характеризує..."

**Never ask:**
- "У якому році написаний..." (unless "Згідно з текстом, у якому році автор каже що...")
- "Що символізує..." (unless "Як автор модуля інтерпретує символіку...")
- "Хто написав..." (tests literary knowledge, not Ukrainian)

</critical>

---

### Activity Mix for Literature Modules

**Total: 10-12 activities** (focus on quality over quantity)

| Activity Type | Count | Purpose | Example |
|---------------|-------|---------|---------|
| **quiz** | 4-5 | Reading comprehension of analysis | "Згідно з текстом, як автор інтерпретує образ каменярів?" |
| **fill-in / cloze** | 3-4 | Literary vocabulary in context | "Франко [___] важливу роль у модернізмі" → відіграв |
| **error-correction** | 2-3 | Grammar practice | Fix case/aspect errors in literary sentences |
| **match-up** | 1-2 | Terminology | Ukrainian literary term ↔ Ukrainian definition |
| **mark-the-words / select** | 1-2 | Device identification | Find metaphors, passive voice in poem excerpt |

**Note:** Plus 2-3 external reading tasks and 1 essay assignment (tracked in activities YAML).

---

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/c1-146-shevchenko.yaml`:**

```yaml
- type: quiz
  title: Розуміння літературознавчого тексту
  items:
    - question: Згідно з текстом модуля, який стилістичний засіб автор виділяє?
      options:
        - text: персоніфікацію
          correct: true
        - text: метафору
          correct: false

- type: fill-in
  title: Аналіз цитати
  items:
    - sentence: '"Реве та стогне Дніпр широкий" — це приклад [___].'
      answer: персоніфікації
      options:
        - персоніфікації
        - метафори
```

---

### Close Reading (Language-Focused)

```markdown
## quiz: Розуміння літературознавчого тексту

> **Instruction:** Відповідайте на питання на основі прочитаного аналізу в модулі.

1. Згідно з текстом модуля, який стилістичний засіб автор аналізу виділяє в рядку "Реве та стогне Дніпр широкий"?
   - [ ] Автор класифікує це як метафору
   - [x] Автор визначає це як персоніфікацію
   - [ ] Автор називає це гіперболою
   - [ ] Автор не аналізує цей рядок
   > У тексті аналізу чітко зазначено, що Дніпр "реве" і "стогне" — персоніфікація.

2. Як у тексті модуля автор інтерпретує образ "каменярів" у Франка?
   - [ ] Текст описує каменярів як буквальних будівельників
   - [ ] Автор не згадує цей образ
   - [x] Автор тлумачить каменярів як символ борців за прогрес
   - [ ] Текст подає суперечливі інтерпретації
   > У розділі аналізу автор чітко формулює символічне значення образу.

[All questions must reference "згідно з текстом" or "у тексті модуля" — tests READING COMPREHENSION of the analysis, not literary recall]
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

---

## Content Structure Note

### Vocabulary & Activities
**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:
- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

The build system will inject these sections at build time.
**Example `vocabulary/c1-146-shevchenko.yaml`:**

```yaml
items:
- lemma: метафора
  ipa: /mɛˈtɑfɔrɑ/
  translation: metaphor
  pos: noun
  note: неявне порівняння
- lemma: ліричний герой
  ipa: /lʲiˈrɪt͡ʃnɪj ɦɛˈrɔj/
  translation: lyrical persona
  pos: phrase
  note: голос у вірші
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
