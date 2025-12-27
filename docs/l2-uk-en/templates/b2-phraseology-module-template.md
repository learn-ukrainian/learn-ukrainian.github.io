# B2 Phraseology Module Template

**Purpose:** Reference template for B2 phraseology modules (M41-70: Idioms, Proverbs, Sayings, Synonyms, Collocations)

**Based on:** `b2-module-template.md` — inherits all B2 quality standards

**Related Issue:** [#305](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/305)

---

## Quick Reference Checklist

Before submitting a B2 phraseology module, verify all items from `b2-module-template.md` PLUS:

### Phraseology-Specific Requirements
- [ ] **CBI pedagogy:** Content-Based Instruction with Narrative Arc (NOT TTT)
- [ ] **Idioms in context:** 15-20 phraseological units embedded in narratives
- [ ] **Semantic categories:** Organize by meaning (somatic, animal, color, etc.)
- [ ] **Usage register:** Show where each expression is appropriate
- [ ] **Cultural origin:** Explain cultural/historical background where relevant
- [ ] **Synonym nuance:** Distinguish between near-synonyms with examples

---

## Module Structure (Phraseology-Specific)

### 1. Frontmatter

```yaml
---
module: b2-XX
title: "Ukrainian Title — Phraseology Category"
phase: "B2.2 [Phraseology & Synonymy]"
pedagogy: "CBI"  # Content-Based Instruction
register: "varies"  # Phraseology spans registers
tags:
  - phraseology
  - [category: somatic, animal, color, proverbs, synonyms, collocations]
grammar:
  - "Fixed expressions"
  - "Idiom structure and variation"
vocabulary_focus:
  - "Phraseological units"
  - "Semantic nuance"
---
```

### 2. Narrative Arc Structure

#### Section 1: Hook with Idioms — 200-300 words

```markdown
# [Phraseology Category Title]

> 🎯 **Чому це важливо?**
>
> [Explain why idioms/proverbs are essential for B2 fluency]
> [Connect to cultural understanding]
> [Set expectations for 15-20 expressions]

## Вступ

[Short narrative using 3-4 target idioms naturally — reader discovers them in context]

Марія **як у воду дивилася**: її прогноз справдився. Вона завжди **тримала руку на пульсі** подій і знала, що конфлікт неминучий. Але навіть вона не очікувала, що все станеться **ні сіло ні впало** — раптово, без попередження.

> 💡 **Чи знали ви?**
>
> Українська мова має понад 30,000 фразеологізмів — більше, ніж більшість європейських мов!
```

#### Section 2: Semantic Categories — 800-1000 words

```markdown
## [Category Name]: Фразеологізми

### Категорія 1: [Semantic Group]

**[Idiom 1]** — [Literal meaning] → [Figurative meaning]

**Приклад у контексті:**
> [2-3 sentence example showing natural usage]

**Регістр:** [Register: розмовний, нейтральний, книжний, etc.]

**Синоніми:** [Related expressions with subtle differences]

---

**[Idiom 2]** — [Literal meaning] → [Figurative meaning]

[Continue pattern for 5-6 idioms in this category]

### Категорія 2: [Next Semantic Group]

[Continue with next category...]
```

**Semantic category examples:**

| Category | Ukrainian | Example Idioms |
|----------|-----------|----------------|
| Соматичні (body) | Частини тіла | рукою подати, на свої очі, мати голову на плечах |
| Зоологічні (animal) | Тварини | вовком дивитися, як риба у воді, купити кота в мішку |
| Кольорові (color) | Кольори | чорна заздрість, біла ворона, рожеві окуляри |
| Природні (nature) | Природа | як грім серед ясного неба, після дощику в четвер |
| Кількісні (quantity) | Кількість | як кіт наплакав, хоч греблю гати |

#### Section 3: Proverbs and Sayings — 300-400 words

```markdown
## Прислів'я та приказки

### Про [Theme]

**Без труда нема плода.**
- *Without labor there's no fruit.* (No pain, no gain.)
- **Вживання:** Мотивація до роботи
- **Регістр:** Нейтральний, широковживаний

**Як посієш, так і пожнеш.**
- *As you sow, so shall you reap.*
- **Вживання:** Попередження про наслідки
- **Регістр:** Нейтральний

[Continue with 8-10 proverbs organized by theme]

> 🌍 **Культурний контекст**
>
> [Explain cultural background — many Ukrainian proverbs reflect agrarian past, Cossack values, or Christian tradition]
```

#### Section 4: Usage in Context — 300-400 words

```markdown
## Вживання у контексті

### Діалог 1: Побутова розмова

**Оля:** Ну що, як справи на роботі?

**Петро:** Та **ні пуху ні пера**! Проєкт нарешті завершили.

**Оля:** Справді? Я думала, ви ще **на мілині сидите** — грошей ніяк не виділяли.

**Петро:** Було складно, але шеф нарешті **взяв бика за роги** і знайшов інвестора.

### Діалог 2: Формальніший контекст

[Show how some idioms work in more formal settings, and which don't]

### Помилки у вживанні

**Помилка:** Використання книжного фразеологізму в розмові
- ❌ "Мій друг — стовп суспільства." (занадто книжно)
- ✅ "Мій друг — надійна людина."

**Помилка:** Змішування фразеологізмів
- ❌ "Рукою подати на мілині" (два різні вирази)
- ✅ "Рукою подати" АБО "сидіти на мілині"
```

---

## Phraseology-Specific Activities

### Activity Format Quick Reference

**CRITICAL:** Use these exact formats for MDX generation to work correctly.

| Activity | Format |
|----------|--------|
| **quiz** | `- [ ] wrong` / `- [x] correct` with optional `> explanation` |
| **true-false** | `- [x] True.` with `> explanation` / `- [ ] False.` with `> explanation` |
| **fill-in** | `> [!answer] correct` + `> [!options] a \| b \| c \| d` |
| **error-correction** | ALL 4 required: `> [!error]` + `> [!answer]` + `> [!options]` + `> [!explanation]` |
| **match-up** | Table: `\| Left \| Right \|` |
| **group-sort** | `### Category` headers with `- items` underneath |
| **unjumble** | `> [!answer] Correct sentence here.` |
| **cloze** | Inline: `{blank\|opt1\|opt2\|answer}` |
| **select** | Multiple `- [x]` for all correct options |
| **translate** | Multi-choice: `- [x] Correct translation.` with `> explanation` |
| **mark-the-words** | `*marked*` words in blockquote passage |
| **dialogue-reorder** | `- [N]` numbered lines (N = correct order) |

---

### Idiom Matching

```markdown
## match-up: Фразеологізм та значення

- рукою подати | дуже близько
- як кіт наплакав | дуже мало
- ні пуху ні пера | побажання успіху
- брати бика за роги | рішуче діяти
- як у воду дивитися | правильно передбачити
- тримати руку на пульсі | бути в курсі подій
- біла ворона | не такий як усі
- після дощику в четвер | ніколи

[12+ matches]
```

### Context Completion

```markdown
## fill-in: Фразеологізми в контексті

1. Магазин зовсім поруч, [___].
   - [x] рукою подати
   - [ ] на носі
   - [ ] під боком
   > "Рукою подати" = дуже близько (можна дістати рукою).

2. Грошей у нас [___], ледве на їжу вистачає.
   - [x] як кіт наплакав
   - [ ] хоч греблю гати
   - [ ] повні кишені
   > "Як кіт наплакав" = дуже мало (коти не плачуть).

[10+ items]
```

### Synonym Nuance

```markdown
## group-sort: Відтінки значення

Розподіліть слова за ступенем інтенсивності:

- group: Слабкий ступінь
  - сердитий
  - незадоволений
  - роздратований

- group: Середній ступінь
  - злий
  - розгніваний
  - обурений

- group: Сильний ступінь
  - лютий
  - шаленій
  - скаженій

[16+ items across 3-4 intensity levels]
```

### Register Sorting

```markdown
## group-sort: Регістр фразеологізмів

- group: Розмовний
  - ні пуху ні пера
  - купити кота в мішку
  - сісти в калюжу

- group: Нейтральний
  - рукою подати
  - як у воду дивитися
  - тримати руку на пульсі

- group: Книжний/урочистий
  - стовп суспільства
  - нести хрест
  - каменем спотикання

[16+ items]
```

### Proverb Completion

```markdown
## fill-in: Закінчіть прислів'я

1. Без труда [___].
   - [x] нема плода
   - [ ] нема ліда
   - [ ] нема роду
   > Прислів'я про цінність праці.

2. Як посієш, [___].
   - [x] так і пожнеш
   - [ ] так і виросте
   - [ ] так і буде
   > Прислів'я про наслідки вчинків.

[10+ proverb completions]
```

---

## Engagement Boxes for Phraseology Modules

```markdown
> 💡 **Етимологія**
>
> [Origin story of a particularly interesting idiom]

> 🎭 **Варіанти**
>
> [Show regional or stylistic variants of the same expression]

> ⚠️ **Фальшиві друзі**
>
> [Idioms that look like English expressions but mean something different]

> 🌍 **Культурний контекст**
>
> [Cultural background explaining why this expression exists]

> 📚 **У літературі**
>
> [Quote from Ukrainian literature using the expression]

> 🔄 **Синоніми**
>
> [Compare 2-3 similar expressions with subtle differences]
```

---

## Vocabulary Section for Phraseology Modules

```markdown
# Словник

| Слово / Вираз | Переклад | Примітки |
|---------------|----------|----------|
| **рукою подати** | very close, a stone's throw | соматичний; "можна дістати рукою" |
| **як кіт наплакав** | very little | зоологічний; іронія — коти не плачуть |
| **біла ворона** | odd one out, black sheep | зоологічний + кольоровий |
| **ні пуху ні пера** | break a leg, good luck | мисливський вираз; відповідь: "До біса!" |
| **фразеологізм** | idiom, set expression | лінгвістичний термін |
| **прислів'я** | proverb | народна мудрість; завершена думка |
| **приказка** | saying | незавершена думка, порівняння |
| **крилатий вислів** | winged word | вираз із відомим джерелом |
| [30+ items] | | |
```

---

## Example Module Outline: M45 (Somatic Idioms)

```markdown
# Соматичні фразеологізми: Частини тіла

> 🎯 **Чому це важливо?**
> Фразеологізми з частинами тіла — найпоширеніша категорія в українській мові...

## Вступ
[Narrative using 3-4 somatic idioms]

## Голова
- мати голову на плечах
- втратити голову
- морочити голову

## Руки
- рукою подати
- золоті руки
- опустити руки

## Очі
- на свої очі
- закривати очі
- відкрити комусь очі

## Вживання у контексті
[Dialogues showing natural usage]

# Підсумок
# Словник [30+ expressions + terminology]
# Активності [14+ activities]
```

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/b2-module-template.md`
- **B2 Curriculum Plan:** `docs/l2-uk-en/B2-CURRICULUM-PLAN.md` (M41-70 phraseology progression)
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
