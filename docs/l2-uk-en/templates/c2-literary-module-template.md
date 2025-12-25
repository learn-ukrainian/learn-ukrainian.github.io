# C2 Literary Module Template

**Purpose:** Reference template for C2 literary mastery modules (M26-45: Literary Theory, Creative Writing, Translation, Scholar-Level Analysis)

**Based on:** `c2-module-template.md` — inherits all C2 quality standards

**Related Issue:** [#307](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/307)

---

## Quick Reference Checklist

Before submitting a C2 literary module, verify all items from `c2-module-template.md` PLUS:

### Literary-Specific Requirements
- [ ] **Scholar-level analysis:** Literary theory and criticism, not surface reading
- [ ] **Original production:** Poetry, prose, or literary essay (with Model Answer)
- [ ] **Translation component:** Literary translation theory or practice
- [ ] **Ukrainian critical terminology:** All analysis in Ukrainian
- [ ] **Canon awareness:** Connect to Ukrainian literary tradition
- [ ] **Meta-linguistic commentary:** Explain stylistic and creative choices

---

## Module Types in C2.2

### Literary Theory (M26-32)

| Modules | Focus | Content |
|---------|-------|---------|
| M26 | Literary Theory | Scholar-level frameworks |
| M27 | Narratology | Narrative analysis |
| M28 | Поетика: Verse Analysis | Poetry mastery |
| M29 | Поетика: Prose Analysis | Prose mastery |
| M30 | Intertextuality | Literary connections |
| M31 | Literary Criticism Methods | Critical approaches |
| M32 | Writing Literary Essays | Publication-ready criticism |

### Translation & Creative Writing (M33-40)

| Modules | Focus | Content |
|---------|-------|---------|
| M33 | Translation Theory | Understanding translation |
| M34 | Literary Translation I | Poetry translation |
| M35 | Literary Translation II | Prose translation |
| M36 | Creative Writing: Poetry | Original poetry |
| M37 | Creative Writing: Prose | Original prose |
| M38 | Contemporary Literature | Current literary scene |
| M39 | Digital Literature | New forms |
| M40 | Literary Prizes & Canon | Cultural context |

### Integration (M41-45)

| Modules | Focus |
|---------|-------|
| M41-42 | Literary Community |
| M43 | C2.2 Practice I — Literary Portfolio |
| M44 | C2.2 Practice II — Creative Portfolio |
| M45 | C2.2 Checkpoint |

---

## Module Structure (Literary-Specific)

### 1. Frontmatter

```yaml
---
module: c2-0XX
title: "[Literary Topic]: Ukrainian Title"
phase: "C2.2 [Literary Mastery]"
pedagogy: "Creative Production"  # or "Literary Analysis"
register: "художній"  # Primary register for literature
style_focus: "[literary technique]"  # narratology, poetics, translation, etc.
tags:
  - literary
  - [theory, creative-writing, translation, poetry, prose]
  - [author/movement if applicable]
grammar:
  - "Literary syntax and stylistics"
  - "Narrative techniques"
vocabulary_focus:
  - "Літературознавча термінологія"
  - "Критичний аналіз"
---
```

### 2. Literary Content Structure

#### Section 1: Theoretical Framework — 400-500 words

```markdown
# [Literary Topic]: Теоретичні засади

> 🎯 **Чому це важливо?**
>
> [Explain theoretical significance for C2 mastery]
> [How this connects to Ukrainian literary tradition]
> [What creative skills this enables]

## Теоретична база

### Ключові поняття

[Presentation of theoretical concepts — 200-250 words]

| Поняття | Визначення | Приклад |
|---------|------------|---------|
| [Concept 1] | [Definition] | [Literary example] |
| [Concept 2] | [Definition] | [Literary example] |
| [Concept 3] | [Definition] | [Literary example] |

### Історичний контекст

[Development of this literary concept — 100-150 words]

> 📚 **Літературознавчий контекст**
>
> [How this fits into Ukrainian and world literary theory]
```

#### Section 2: Literary Analysis — 600-800 words

```markdown
## Аналіз тексту

### Первинний текст

**Автор:** [Author]
**Твір:** [Work title]
**Жанр:** [Genre]
**Рік:** [Year]

> [500-800 word literary excerpt or complete short text]

---

### Детальний аналіз

#### Наратологічний аналіз

**Наратор:** [Type of narrator]
**Фокалізація:** [Point of view]
**Часова організація:** [Temporal structure]

[150-200 word analysis]

#### Стилістичний аналіз

| Засіб | Приклад з тексту | Функція |
|-------|------------------|---------|
| [Device 1] | "[Quote]" | [Function] |
| [Device 2] | "[Quote]" | [Function] |
| [Device 3] | "[Quote]" | [Function] |

[150-200 word analysis of stylistic effects]

#### Інтертекстуальний аналіз

**Алюзії:**
- [Allusion 1 with explanation]
- [Allusion 2 with explanation]

**Діалог з традицією:**
[100-150 word analysis of intertextual connections]

> 💡 **Експертна перспектива**
>
> [Scholar-level insight about the text]
```

#### Section 3: Creative Production — 500-700 words

```markdown
## Творче завдання

### Завдання: [Poetry/Prose/Essay]

**Тип:** [Specific form — сонет, оповідання, критичне есе]

**Завдання:**
[Detailed creative task description — 50-100 words]

**Вимоги:**
1. [Formal requirement]
2. [Thematic requirement]
3. [Stylistic requirement]
4. [Length requirement]

---

### Зразок відповіді (Model Answer)

**[Title of model work]**

> [Complete model creative work:
> - For poetry: 14+ lines
> - For prose: 400+ words
> - For essay: 500+ words
> Demonstrating:
> - Mastery of form
> - Sophisticated use of literary devices
> - Individual voice
> - Native-like linguistic control]

---

### Авторський коментар

> [150+ word self-reflective commentary explaining:
> - Creative choices made
> - How theory was applied
> - Intended effects
> - Relationship to literary tradition]

---

### Рубрика оцінювання

| Критерій | Очікування на C2 |
|----------|------------------|
| Форма | Досконале володіння обраною формою |
| Стиль | Індивідуальний голос, багата образність |
| Техніка | Свідоме використання літературних засобів |
| Оригінальність | Творчий внесок, не імітація |
| Мова | Бездоганна граматика, багата лексика |
```

#### Section 4: Translation (if applicable) — 400-500 words

```markdown
## Перекладознавчий аналіз

### Оригінал

**Мова:** [Source language]
**Автор:** [Author]

> [Original text — 100-200 words]

---

### Переклад 1: [Translator name]

> [Translation 1]

### Переклад 2: [Translator name]

> [Translation 2]

---

### Порівняльний аналіз

| Аспект | Переклад 1 | Переклад 2 |
|--------|------------|------------|
| Стратегія | [domestication/foreignization] | [domestication/foreignization] |
| Лексика | [Analysis] | [Analysis] |
| Синтаксис | [Analysis] | [Analysis] |
| Ритм | [Analysis] | [Analysis] |
| Точність | [Analysis] | [Analysis] |

**Висновок:**
[100-150 word comparative conclusion]

---

### Завдання: Власний переклад

**Оригінал:**
> [50-100 word text for translation]

**Зразок відповіді:**
> [Model translation with translator's notes]

> 🔍 **Метамовна свідомість**
>
> [Discussion of translation choices and their effects]
```

---

## Literary-Specific Activities

### Literary Analysis Quiz

```markdown
## quiz: Літературознавчий аналіз

1. Яка наративна техніка характерна для модерністської прози?
   - [ ] Хронологічна послідовність
   - [x] Потік свідомості
   - [ ] Всезнаючий наратор
   - [ ] Рамкова оповідь
   > Потік свідомості — ключова техніка модернізму (Джойс, Вулф, Підмогильний).

2. Що таке "фокалізація" у наратології?
   - [ ] Головний персонаж
   - [x] Точка зору, з якої подаються події
   - [ ] Авторська позиція
   - [ ] Кульмінація сюжету
   > Фокалізація — термін Ж. Женетта для позначення перспективи оповіді.

[12+ literary theory questions]
```

### Creative Writing Workshop

```markdown
## production: Поетична майстерня

**Завдання:**
Напишіть сонет на тему [theme], дотримуючись класичної форми.

**Вимоги:**
- 14 рядків
- Рима: ABAB CDCD EFEF GG (або італійська схема)
- Ямб
- Вольта (перелом) у 9 або 13 рядку

**Зразок відповіді:**

> [Complete 14-line sonnet demonstrating form mastery]

**Технічний аналіз:**
> [100+ word analysis of prosodic and stylistic choices]
```

### Translation Practice

```markdown
## translate: Літературний переклад

Перекладіть поетичний уривок, зберігаючи:
- Ритмічну структуру
- Образність
- Емоційний тон

**Оригінал (English):**
> [50-100 word poetic text]

**Зразок відповіді:**
> [Model translation preserving literary qualities]

**Перекладацький коментар:**
> [50-100 word explanation of translation choices]
```

### Intertextuality Analysis

```markdown
## match-up: Інтертекстуальні зв'язки

- "Заповіт" Шевченка | Біблійний псалом
- "Лісова пісня" Українки | Скандинавська міфологія
- "Тіні забутих предків" Коцюбинського | Гуцульський фольклор
- "Місто" Підмогильного | Європейський модернізм
- "Польові дослідження..." Забужко | Постмодерна деконструкція

[14+ intertextual connections]
```

---

## Engagement Boxes for Literary Modules

```markdown
> 📚 **Літературознавчий контекст**
>
> [How this fits into literary theory/tradition]

> 💡 **Експертна перспектива**
>
> [Scholar-level insight about literature]

> 🎭 **Театральні та екранні адаптації**
>
> [Notable adaptations of literary works]

> 🏛️ **Історичний контекст**
>
> [Political/social context of literary work]

> 🔍 **Метамовна свідомість**
>
> [How writers think about language]

> 📖 **Рекомендоване читання**
>
> [Further reading in Ukrainian literature]

> 🌍 **Світовий контекст**
>
> [Ukrainian literature in world context]
```

---

## Vocabulary Section for Literary Modules

```markdown
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| **наратологія** | narratology | наука про оповідь |
| **фокалізація** | focalization | точка зору оповіді |
| **інтертекстуальність** | intertextuality | зв'язки між текстами |
| **деконструкція** | deconstruction | критичний метод |
| **верлібр** | free verse | вільний вірш |
| **катрен** | quatrain | чотиривірш |
| **терцина** | terza rima | тривірш |
| **сонет** | sonnet | 14-рядковий вірш |
| **новела** | novella | коротка проза |
| **оповідач** | narrator | той, хто розповідає |
| **протагоніст** | protagonist | головний герой |
| **антагоніст** | antagonist | противник героя |
| **хронотоп** | chronotope | час-простір у творі |
| **еквівалентність** | equivalence | перекладознавчий термін |
| [40+ literary terms] | | |
```

---

## Module Breakdown: C2.2 Literary Mastery

### Theory Modules (M26-32)

| Module | Focus | Key Concepts |
|--------|-------|--------------|
| M26 | Literary Theory | Формалізм, структуралізм, постструктуралізм |
| M27 | Narratology | Наратор, фокалізація, час оповіді |
| M28 | Poetics: Verse | Метр, рима, строфа, образність |
| M29 | Poetics: Prose | Сюжет, персонаж, хронотоп |
| M30 | Intertextuality | Алюзія, цитата, пародія |
| M31 | Criticism Methods | Феміністична, постколоніальна критика |
| M32 | Literary Essays | Структура, аргументація, стиль |

### Creative Modules (M33-40)

| Module | Focus | Production Type |
|--------|-------|-----------------|
| M33 | Translation Theory | Theoretical essay |
| M34 | Poetry Translation | Translated poem |
| M35 | Prose Translation | Translated excerpt |
| M36 | Creative Poetry | Original poems |
| M37 | Creative Prose | Original story |
| M38-40 | Contemporary/Digital | Critical essays |

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/c2-module-template.md`
- **C2 Curriculum Plan:** `docs/l2-uk-en/C2-CURRICULUM-PLAN.md` (M26-45 specifications)
- **C1 Literature Template:** `docs/l2-uk-en/templates/c1-literature-module-template.md`
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
