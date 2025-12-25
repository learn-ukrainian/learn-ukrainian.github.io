# C1 Biography Module Template

**Purpose:** Reference template for C1 biography modules (M36-100: 65 Ukrainian Historical & Cultural Figures)

**Based on:** `c1-module-template.md` — inherits all C1 quality standards

**Related Issue:** [#306](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/306)

---

## Quick Reference Checklist

Before submitting a C1 biography module, verify all items from `c1-module-template.md` PLUS:

### Biography-Specific Requirements
- [ ] **CBI pedagogy:** Content-Based Instruction (vocabulary through narrative)
- [ ] **Extended narrative:** 800-1000 word biographical account
- [ ] **Primary sources:** Include quotes, letters, or speeches from the figure
- [ ] **Historical context:** Place figure in their era's political/cultural context
- [ ] **Legacy section:** Connect to modern Ukraine
- [ ] **Gender/era balance:** Follow curriculum diversity requirements
- [ ] **Decolonization lens:** Ukrainian perspective, not Russian imperial framing

---

## Module Structure (Biography-Specific)

### 1. Frontmatter

```yaml
---
module: c1-XX
title: "[Figure Name]: [Ukrainian Title]"
phase: "C1.3 [Biographies]"
pedagogy: "CBI"  # Content-Based Instruction
register: "публіцистичний"  # Biographical narrative style
tags:
  - biography
  - [era: pre-modern, cossack, imperial, revolutionary, soviet, independence]
  - [domain: literature, politics, science, arts, military, religion]
grammar:
  - "Historical narrative tenses"
  - "Quoted speech conventions"
vocabulary_focus:
  - "Domain-specific terminology"
  - "Historical vocabulary"
---
```

### 2. Biography Content Structure

#### Section 1: Hook & Context — 300-400 words

```markdown
# [Figure Name]: [Descriptive Title]

> 🎯 **Чому це важливо?**
>
> [2-3 sentences explaining figure's significance]
> [Why modern Ukrainians remember this person]
> [What learners will understand by studying this figure]

## Вступ

[Compelling opening — a dramatic moment, famous quote, or surprising fact about the figure]

[Set the historical context: When did they live? What was Ukraine like then? What challenges did they face?]

> 💡 **Чи знали ви?**
>
> [Surprising or lesser-known fact about the figure]
```

#### Section 2: Біографія (Main Narrative) — 800-1000 words

```markdown
## Біографія

### Ранні роки

[200-250 words about birth, childhood, education, formative experiences]

**Ключові дати:**
| Рік | Подія |
|-----|-------|
| [Year] | [Event] |
| [Year] | [Event] |

### Шлях до [визнання/влади/творчості]

[300-350 words about rise to prominence, key achievements, turning points]

> 📜 **Первинне джерело**
>
> [Quote from the figure's letters, speeches, or writings — 50-100 words]
> *— Джерело: [Attribution]*

### Головні досягнення

[250-300 words about major contributions, works, or actions]

**[Figure's domain]-specific achievements:**
1. [Achievement 1]
2. [Achievement 2]
3. [Achievement 3]

### Останні роки та спадщина

[200-250 words about later life, death, and legacy]

> 🌍 **Сучасна Україна**
>
> [How this figure is remembered today — monuments, street names, cultural references]
```

#### Section 3: Історичний контекст — 300-400 words

```markdown
## Історичний контекст

### [Era Name]: Україна у [period]

[Describe the political, cultural, and social context of the figure's life]

**Ключові контекстуальні фактори:**
- **Політика:** [Political situation]
- **Культура:** [Cultural movements]
- **Мова:** [Language situation — Russification, national revival, etc.]

### Вплив на сучасників

[How the figure influenced contemporaries and was perceived in their time]

> ⚠️ **Деколонізація**
>
> [Challenge Russian/Soviet historiographical myths about this figure if applicable]
> [Provide Ukrainian perspective based on primary sources]
```

#### Section 4: Порівняльний аналіз — 300-400 words

```markdown
## Порівняльний аналіз

### [Figure] vs. [Contemporary or Contrasting Figure]

| Аспект | [Figure 1] | [Figure 2] |
|--------|------------|------------|
| Епоха | [Era] | [Era] |
| Домен | [Domain] | [Domain] |
| Підхід | [Approach] | [Approach] |
| Спадщина | [Legacy] | [Legacy] |

**Аналіз:**
[200-250 words comparing the two figures' contributions, approaches, or legacies]

### Критичне мислення

**Питання для роздуму:**
1. Чому ця постать важлива для української ідентичності?
2. Як би її життя відрізнялося в інших обставинах?
3. Які уроки можна винести з її досвіду?
```

---

## Biography-Specific Activities

### Chronology & Comprehension

```markdown
## quiz: Біографія [Figure Name]

1. У якому році народився/народилася [Figure]?
   - [ ] [Wrong year]
   - [x] [Correct year]
   - [ ] [Wrong year]
   - [ ] [Wrong year]
   > [Brief context about birthplace/circumstances]

2. Який головний внесок [Figure] у [domain]?
   - [x] [Correct contribution]
   - [ ] [Distractor]
   - [ ] [Distractor]
   - [ ] [Distractor]
   > [Explanation of contribution's significance]

[12+ comprehension questions]
```

### Primary Source Analysis

```markdown
## select: Аналіз первинного джерела

Прочитайте уривок із [letter/speech/work] [Figure]:

> "[150-200 word excerpt]"

Виберіть усі правильні твердження:

- [x] Автор підтримує [position]
- [ ] Автор критикує [position]
- [x] Текст написаний для [audience]
- [ ] Текст є об'єктивним описом подій
- [x] Лексика вказує на [register/attitude]

> Аналіз: [Explanation of correct answers]
```

### Vocabulary in Biographical Context

```markdown
## fill-in: Біографічна лексика

1. [Figure] [___] у боротьбі за незалежність.
   - [x] брав/брала участь
   - [ ] робив/робила участь
   - [ ] мав/мала участь
   > "Брати участь" — фіксований вираз для participation.

2. Його/Її [___] залишається актуальною досі.
   - [x] спадщина
   - [ ] наслідок
   - [ ] залишок
   > "Спадщина" — legacy, intellectual/cultural inheritance.

[12+ biographical vocabulary items]
```

### Era Categorization

```markdown
## group-sort: Постаті за епохами

- group: Княжа доба (до 1340)
  - Ярослав Мудрий
  - Анна Ярославна
  - Нестор-літописець

- group: Козацька доба (1500-1764)
  - Богдан Хмельницький
  - Іван Мазепа
  - Пилип Орлик

- group: Імперська доба (1764-1917)
  - Тарас Шевченко
  - Леся Українка
  - Михайло Грушевський

- group: Сучасність (1991-)
  - [Contemporary figures]

[20+ figures across 5-6 eras]
```

---

## Engagement Boxes for Biography Modules

```markdown
> 💡 **Чи знали ви?**
>
> [Surprising fact about the figure]

> 📜 **Первинне джерело**
>
> [Quote from letters, speeches, or works]

> 🏛️ **Історичний контекст**
>
> [Background information about the era]

> ⚠️ **Деколонізація**
>
> [Challenge Russian/Soviet myths]

> 🌍 **Сучасна Україна**
>
> [How figure is remembered today]

> 📚 **Рекомендоване читання**
>
> [Ukrainian-language sources for further study]
```

---

## Vocabulary Section for Biography Modules

```markdown
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| **постать** | figure, personality | історична постать — historical figure |
| **спадщина** | legacy, heritage | інтелектуальна спадщина |
| **внесок** | contribution | зробити внесок у... |
| **діяльність** | activity, work | громадська діяльність — public activity |
| **сучасник** | contemporary | pl.: сучасники |
| **послідовник** | follower, successor | ідейний послідовник |
| **світогляд** | worldview | філософський світогляд |
| **доля** | fate, destiny | трагічна доля |
| **вшанування** | commemoration | вшанування пам'яті |
| **пам'ятник** | monument | пам'ятник [кому? — Dative] |
| [35+ biographical terms] | | |
```

---

## Module Breakdown: C1.3 Biographies

### Era Distribution (65 modules)

| Era | Modules | Count | Focus |
|-----|---------|-------|-------|
| Pre-modern | M36-45 | 10 | Kyivan Rus, medieval figures |
| Cossack era | M46-55 | 10 | Hetmans, Sich leaders, diplomats |
| Imperial era | M56-70 | 15 | Writers, artists, activists under Russian rule |
| Revolutionary | M71-78 | 8 | UNR, Sich Riflemen, early Soviet |
| Soviet era | M79-88 | 10 | Dissidents, executed renaissance, WWII |
| Independence | M89-100 | 12 | Contemporary figures, Maidan, war heroes |

### Gender Balance Requirement

- **Target:** Minimum 30% women (20+ modules)
- **Domains:** Literature, arts, science, politics, military, activism
- **Era representation:** Women from each major era

---

## Decolonization Guidelines

### Required Perspective Corrections

| Figure | Colonial Myth | Ukrainian Reality |
|--------|---------------|-------------------|
| Shevchenko | "Russian poet" | Ukrainian poet persecuted by Russian Empire |
| Mazepa | "Traitor" | Defender of Ukrainian autonomy |
| Hrushevsky | "Nationalist" | Historian documenting Ukrainian statehood |
| UPA figures | "Nazis" | Independence fighters in complex WWII context |

### Language Sensitivity

- Use "Московське царство" before 1721
- Use "Російська імперія" for 1721-1917
- Avoid Soviet-era designations ("Malorossiya", "Little Russia")
- Emphasize Ukrainian agency, not victimhood

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/c1-module-template.md`
- **C1 Curriculum Plan:** `docs/l2-uk-en/C1-CURRICULUM-PLAN.md` (M36-100 specifications)
- **B2 History Template:** `docs/l2-uk-en/templates/b2-history-module-template.md`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
