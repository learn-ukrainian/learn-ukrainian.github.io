# C2 Meta-Skills & Capstone Module Template

**Purpose:** Reference template for C2 meta-skills and capstone modules (M76-100: Grammar Review, Rare Forms, Regional Varieties, Teaching Ukrainian, Translation, Capstone Projects)

**Based on:** `c2-module-template.md` — inherits all C2 quality standards

**Related Issue:** [#307](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/307)

---

## Quick Reference Checklist

Before submitting a C2 meta-skills/capstone module, verify all items from `c2-module-template.md` PLUS:

### Meta-Skills-Specific Requirements
- [ ] **Complete mastery demonstration:** Full grammar, vocabulary, and skills review
- [ ] **Rare/archaic forms:** Understanding historical and literary Ukrainian
- [ ] **Regional varieties:** Dialectal awareness without prescriptivism
- [ ] **Teaching component:** Meta-awareness for teaching Ukrainian
- [ ] **Capstone guidance:** Clear project requirements and milestones
- [ ] **Certification preparation:** Exam-ready skills assessment

---

## Module Types in C2.4

### Grammar & Form Mastery (M76-81)

| Modules | Focus | Content |
|---------|-------|---------|
| M76 | Complete Grammar Review | Full morphology/syntax verification |
| M77 | Rare/Archaic Forms | Historical text access |
| M78 | Regional Varieties | Full dialectal awareness |
| M79 | Sociolinguistic Mastery | Complete social navigation |
| M80 | Error Analysis | Self-correction skills |
| M81 | Native-Like Fluency | Natural production |

### Teaching & Translation (M82-88)

| Modules | Focus | Content |
|---------|-------|---------|
| M82-84 | Teaching Ukrainian I-III | Pedagogical awareness, lesson planning, materials |
| M85 | Translation Theory | Understanding translation |
| M86-87 | Translation Practice I-II | Literary and technical translation |
| M88 | Interpretation Basics | Oral translation |

### Capstone (M89-94)

| Modules | Focus | Deliverable |
|---------|-------|-------------|
| M89 | Topic Selection | Approved proposal |
| M90 | Research | Research notes, bibliography |
| M91 | Drafting | First draft |
| M92 | Revision | Revised draft |
| M93 | Polish | Final version |
| M94 | Defense | Oral presentation |

### Final Review & Certification (M95-100)

| Modules | Focus |
|---------|-------|
| M95-97 | Final Review I-III (Grammar, Vocabulary, Skills) |
| M98 | Final Exam: Integrated Skills |
| M99 | C2 Certification Preparation |
| M100 | C2 РІВЕНЬ ЗАВЕРШЕНО |

---

## Module Structure (Meta-Skills-Specific)

### 1. Frontmatter

```yaml
---
module: c2-0XX
title: "[Topic]: Ukrainian Title"
phase: "C2.4 [Meta-Skills & Capstone]"
pedagogy: "Meta-Linguistic"  # or "Capstone"
register: "varies"  # All registers mastered at this level
tags:
  - meta-skills
  - [grammar-review, archaic, dialectal, teaching, translation, capstone]
grammar:
  - "Complete morphological/syntactic mastery"
  - "Rare and archaic forms"
vocabulary_focus:
  - "Метамовна термінологія"
  - "Діалектна лексика"
---
```

### 2. Meta-Skills Content Structure

#### Section 1: Mastery Verification — 400-500 words

```markdown
# [Topic]: Верифікація майстерності

> 🎯 **Чому це важливо?**
>
> [Explain what complete mastery means at C2]
> [How this module verifies native-like competence]
> [Preparation for certification and real-world use]

## Діагностика

### Самооцінка

Чи можете ви:

- [ ] [Skill 1 — specific, measurable]
- [ ] [Skill 2 — specific, measurable]
- [ ] [Skill 3 — specific, measurable]
- [ ] [Skill 4 — specific, measurable]
- [ ] [Skill 5 — specific, measurable]

### Діагностичний тест

[10-15 diagnostic questions covering the module's focus area]

> 💡 **Інтерпретація результатів**
>
> [How to interpret diagnostic results and identify gaps]
```

#### Section 2: Advanced Content — 600-800 words

##### For Grammar Review Modules:

```markdown
## Повний граматичний огляд

### Морфологія: Складні випадки

| Категорія | Складний випадок | Правильна форма | Пояснення |
|-----------|------------------|-----------------|-----------|
| Відміни | [Rare declension] | [Correct form] | [Explanation] |
| Дієслова | [Complex conjugation] | [Correct form] | [Explanation] |
| Числівники | [Compound numeral] | [Correct form] | [Explanation] |

### Синтаксис: Рідкісні конструкції

[Analysis of rare but authentic syntactic patterns — 200-250 words]

**Приклади з літератури:**

> [Quote 1 from Ukrainian literature showing rare construction]
> *— Автор, твір*

> [Quote 2]
> *— Автор, твір*
```

##### For Archaic Forms Modules:

```markdown
## Архаїчні та діалектні форми

### Церковнослов'янський вплив

| Сучасна форма | Архаїчна форма | Контекст використання |
|---------------|----------------|----------------------|
| благо | благо | релігійні тексти |
| глас | голос | поетична мова |
| врата | ворота | високий стиль |

### Читання історичних текстів

**Текст:** [Historical Ukrainian text — 200-300 words]

**Аналіз архаїзмів:**
[Detailed analysis of archaic forms in the text]

> 🏛️ **Історичний контекст**
>
> [Why these forms existed and how they evolved]
```

##### For Regional Varieties Modules:

```markdown
## Діалектна варіативність

### Три діалектні групи

| Група | Регіони | Ключові маркери |
|-------|---------|-----------------|
| Північна | Полісся | укання, тверде р |
| Південно-західна | Галичина, Закарпаття | ікання, гуцульські форми |
| Південно-східна | Слобожанщина | близькість до літературної |

### Діалектний аналіз

**Зразок:** [Dialectal text — 100-150 words]

**Ідентифікація маркерів:**
- Фонетичні: [List]
- Морфологічні: [List]
- Лексичні: [List]

> ⚠️ **Соціолінгвістичний контекст**
>
> [Attitudes toward dialects, sociolinguistic awareness]
```

##### For Teaching Ukrainian Modules:

```markdown
## Педагогічна свідомість

### Метамовні знання для викладання

**Типові труднощі для англомовних:**

| Труднощі | Причина | Педагогічна стратегія |
|----------|---------|----------------------|
| Відмінки | Аналітична структура англійської | [Strategy] |
| Вид дієслова | Відсутність в англійській | [Strategy] |
| Дієслова руху | Складна система | [Strategy] |

### Розробка навчальних матеріалів

**Завдання:**
Створіть пояснення [grammar point] для рівня A2.

**Вимоги:**
- Спрощена мова
- Чіткі приклади
- Вправа для закріплення

**Зразок:**
> [Model teaching material]
```

#### Section 3: Capstone Project (for M89-94) — 500-700 words

```markdown
## Капстоунний проєкт

### Вибір теми (M89)

**Типи проєктів:**

| Тип | Вимоги | Приклад теми |
|-----|--------|--------------|
| Дослідницька робота | 10,000+ слів, 15+ джерел | Аналіз мови Шевченка |
| Літературний твір | Поезія 20+ віршів АБО проза 15,000+ слів | Збірка віршів про сучасну Україну |
| Перекладацький проєкт | 50+ сторінок, передмова, глосарій | Переклад сучасної української поезії |
| Професійне портфоліо | 10+ документів, 3+ стилі | Журналістські матеріали |

### Процес

**Етапи:**

1. **Вибір теми (M89):**
   - Обґрунтування актуальності
   - Попередній план
   - Схвалення керівника

2. **Дослідження (M90):**
   - Збір матеріалів
   - Бібліографія
   - Дослідницькі нотатки

3. **Написання чернетки (M91):**
   - Перший повний варіант
   - Структура, зміст

4. **Редагування (M92):**
   - Змістове редагування
   - Структурні зміни
   - Зворотний зв'язок

5. **Полірування (M93):**
   - Стилістичне шліфування
   - Коректура
   - Фінальний варіант

6. **Захист (M94):**
   - Усна презентація (15-20 хв)
   - Відповіді на запитання
   - Оцінювання

### Рубрика оцінювання

| Критерій | Відмінно | Добре | Задовільно |
|----------|----------|-------|------------|
| Зміст | Глибокий, оригінальний | Достатній | Поверхневий |
| Мова | Бездоганна, багата | Коректна | Є помилки |
| Структура | Чітка, логічна | Зрозуміла | Хаотична |
| Захист | Впевнений, чіткий | Адекватний | Слабкий |
```

---

## Meta-Skills-Specific Activities

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/c2-76-grammar-mastery.yaml`:**

```yaml
- type: quiz
  title: Граматична верифікація
  items:
    - question: Яка правильна форма родового множини від "стаття"?
      options:
        - text: статей
          correct: true
        - text: статтів
          correct: false

- type: match-up
  title: Архаїзми та сучасні відповідники
  pairs:
    - left: глас
      right: голос
    - left: врата
      right: ворота
```

---

### Grammar Verification

```markdown
## quiz: Граматична верифікація

1. Яка правильна форма родового множини від "стаття"?
   - [ ] статей
   - [x] статей
   - [ ] статтів
   - [ ] статтей
   > "Стаття" — ж.р., м'яка група. Р.мн. = статей (чергування -тт- → -т-).

2. Як правильно: "Їй шістнадцять років" чи "Їй шістнадцяти років"?
   - [x] Їй шістнадцять років
   - [ ] Їй шістнадцяти років
   - [ ] Обидва правильні
   - [ ] Обидва неправильні
   > Вік у Н.в.: "скільки років?" — "шістнадцять років".

[20+ comprehensive grammar questions]
```

### Archaic Form Recognition

```markdown
## match-up: Архаїзми та сучасні відповідники

- глас | голос
- врата | ворота
- глава | голова
- чоло | лоб
- вія | повіка
- рамено | плече
- уста | губи
- длань | долоня
- чадо | дитина
- глаголати | говорити

[14+ archaic-modern pairs]
```

### Dialectal Recognition

```markdown
## group-sort: Діалектні маркери

- group: Північна (Полісся)
  - укання (високий → висукий)
  - тверде р
  - м'яке ц

- group: Південно-західна
  - ікання
  - файний замість гарний
  - бараболя замість картопля

- group: Південно-східна
  - близькість до літературної
  - вплив російської
  - степові мотиви в лексиці

[20+ dialectal features across groups]
```

### Teaching Practice

```markdown
## production: Педагогічний матеріал

**Завдання:**
Створіть пояснення знахідного відмінка для рівня A1.

**Вимоги:**
- Проста мова
- 3+ прикладів
- 1 вправа на закріплення
- 150+ слів

**Зразок відповіді:**

> [Complete teaching material for A1 learners showing:
> - Clear, simple explanation
> - Relatable examples
> - Practice exercise
> - Appropriate scaffolding]
```

### Capstone Proposal

```markdown
## production: Пропозиція капстоунного проєкту

**Завдання:**
Напишіть пропозицію капстоунного проєкту (300+ слів).

**Структура:**
1. Тема та обґрунтування
2. Попередній план
3. Список джерел (мінімум 5)
4. Очікуваний результат

**Зразок відповіді:**

> [Complete 300+ word project proposal]
```

---

## Engagement Boxes for Meta-Skills Modules

```markdown
> 💡 **Експертна перспектива**
>
> [Native-like linguistic awareness]

> 🏛️ **Історичний контекст**
>
> [Evolution of Ukrainian language features]

> 🗺️ **Регіональна варіація**
>
> [Dialectal information without prescriptivism]

> 🎓 **Педагогічна свідомість**
>
> [Teaching-oriented meta-awareness]

> 📚 **Капстоун**
>
> [Capstone project guidance]

> ✅ **Самооцінка**
>
> [Self-assessment checklist]

> 🏆 **Сертифікація**
>
> [Certification preparation tips]
```

---

## Vocabulary Section for Meta-Skills Modules

**CRITICAL:** Vocabulary must be defined in `vocabulary/{slug}.yaml`. Do NOT embed a vocabulary table in Markdown.

**Example `vocabulary/c2-76-grammar-mastery.yaml`:**

```yaml
items:
- lemma: архаїзм
  ipa: /ɑrxɑˈjizm/
  translation: archaism
  pos: ім.
  note: застаріле слово
- lemma: діалект
  ipa: /dʲiɑˈlɛkt/
  translation: dialect
  pos: ім.
  note: територіальний варіант
```

---

## Capstone Project Types

### 1. Research Paper
- **Length:** 10,000-12,000 words
- **Sources:** 15+ academic sources
- **Structure:** IMRAD or humanities format
- **Defense:** 15-20 minute presentation

### 2. Literary Work
- **Poetry:** 20+ poems with thematic coherence
- **Prose:** 15,000+ words (novel excerpt, story collection)
- **Includes:** Author's preface explaining artistic choices
- **Defense:** Reading + discussion

### 3. Translation Project
- **Length:** 50+ pages source text
- **Includes:** Translator's preface, glossary, annotations
- **Types:** Literary, technical, or mixed
- **Defense:** Analysis of translation choices

### 4. Professional Portfolio
- **Documents:** 10+ professional pieces
- **Styles:** 3+ different registers
- **Includes:** Cover letter, introduction
- **Defense:** Presentation of professional identity

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/c2-module-template.md`
- **C2 Curriculum Plan:** `docs/l2-uk-en/C2-CURRICULUM-PLAN.md` (M76-100 specifications)
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
