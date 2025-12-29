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
- [ ] **Primary sources (≥2):** Include quotes, letters, or speeches from the figure using `[!quote]` callouts
- [ ] **Historical context:** Place figure in their era's political/cultural context
- [ ] **Legacy section:** Connect to modern Ukraine
- [ ] **Gender/era balance:** Follow curriculum diversity requirements
- [ ] **Decolonization lens:** Ukrainian perspective, not Russian imperial framing
- [ ] **NO DIALOGS:** Biography modules are READING-CENTRIC. Do NOT include conversational dialogs—focus on narrative, primary sources, and analysis. Fictional dialogs with historical figures are inappropriate.

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

### CRITICAL: Language Practice, Not Biographical Recall

<critical>

**Activities test LANGUAGE SKILLS, not biographical facts.**

The lesson teaches both Ukrainian AND the figure's life/achievements. Activities practice only Ukrainian using the biography as context.

**✅ CORRECT:** "Згідно з текстом, який головний внесок автор виділяє?" (requires reading Ukrainian)
**❌ WRONG:** "У якому році народився Шевченко?" (tests recall, not language)

**Key Test:** Can the learner answer without reading the Ukrainian text? If yes, rewrite.

</critical>

### Activity Format Quick Reference

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

### 1. Reading Comprehension (quiz)

**Purpose:** Test understanding of Ukrainian biography text, NOT recall of facts.

```markdown
## quiz: Розуміння біографії

> **Instruction:** Відповідайте на питання на основі прочитаного тексту.

1. Згідно з текстом, що автор виділяє як головний внесок цієї постаті?
   - [x] [Answer from text]
   - [ ] [Distractor]
   - [ ] [Distractor]
   - [ ] [Distractor]
   > Текст чітко формулює цей внесок у розділі "Головні досягнення".

2. Як автор характеризує вплив цієї постаті на українську культуру?
   - [ ] [Distractor]
   - [x] [Answer from text]
   - [ ] [Distractor]
   - [ ] [Distractor]
   > У тексті зазначено: "[quote from text]".

[All questions must reference "згідно з текстом" or "у тексті"]
```

### 2. Primary Source Linguistic Analysis (select)

**Purpose:** Test close reading and linguistic features of primary sources.

```markdown
## select: Лінгвістичний аналіз джерела

Прочитайте уривок із листа/промови/твору:

> "[150-200 word excerpt]"

Виберіть усі правильні твердження про мову тексту:

- [x] Автор використовує емоційно забарвлену лексику
- [ ] Текст написаний офіційним регістром
- [x] У тексті є елементи публіцистичного стилю
- [ ] Лексика тексту нейтральна
- [x] Автор звертається до читача безпосередньо

[Test LINGUISTIC analysis, not interpretation of content]
```

### 3. Vocabulary in Biographical Context (fill-in)

**Purpose:** Test vocabulary and collocations from module.

```markdown
## fill-in: Біографічна лексика

1. Ця постать [___] визначну роль у розвитку української культури.
   > [!answer] відіграла
   > [!options] відіграла | зробила | мала | дала
   > Відіграти роль = to play a role (fixed collocation).

2. Його/Її творча [___] охоплює понад 50 років.
   > [!answer] спадщина
   > [!options] спадщина | наслідок | залишок | результат
   > Спадщина = legacy, intellectual/cultural inheritance.

3. Він/Вона [___] участь у національно-визвольному русі.
   > [!answer] брав/брала
   > [!options] брав/брала | робив/робила | мав/мала | давав/давала
   > Брати участь = to participate (fixed expression).

[12+ items testing MODULE VOCABULARY, not biographical facts]
```

### 4. Grammar in Biographical Text (error-correction)

**Purpose:** Test grammar using biography content as context.

```markdown
## error-correction: Граматика в біографічному тексті

1. Тарас Шевченко народився в родина кріпаків.
   > [!error] родина
   > [!answer] родині
   > [!options] родина | родині | родиною | родину
   > [!explanation] Прийменник "в" + місцевий відмінок: в чому? → в родині.

2. Вона присвячувала все своє життя боротьба за права жінок.
   > [!error] боротьба
   > [!answer] боротьбі
   > [!options] боротьба | боротьбі | боротьбою | боротьбу
   > [!explanation] "Присвятити + давальний відмінок": чому? → боротьбі.

[Focus on GRAMMAR errors, not biographical inaccuracies]
```

### 5. Vocabulary Matching (match-up)

**Purpose:** Test recognition of biographical vocabulary.

```markdown
## match-up: Біографічна лексика

| Слово | Значення |
|-------|----------|
| спадщина | те, що залишилося після когось |
| внесок | те, що хтось дав суспільству |
| постать | видатна особа |
| сучасник | людина тієї ж епохи |
| наставник | той, хто навчає |

[Match Ukrainian words to Ukrainian definitions — tests vocabulary, not translation]
```

### 6. Register Identification (group-sort)

**Purpose:** Test register awareness using quotes from module.

```markdown
## group-sort: Визначте регістр цитат

### Офіційний регістр
- "Цим засвідчуємо, що..."
- "На підставі вищезазначеного..."

### Публіцистичний регістр
- "Чому ми маємо пам'ятати..."
- "Її внесок неможливо переоцінити..."

### Розмовний регістр
- "Та він же геній!"
- "Оце так талант!"

[Test REGISTER identification using module content]
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
