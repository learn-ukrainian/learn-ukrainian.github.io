# C1 Biography Module Template

**Purpose:** Reference template for C1 biography modules (M36-100: 65 Ukrainian Historical & Cultural Figures)

**Based on:** `c1-module-template.md` — inherits all C1 quality standards

**Related Issue:** [#306](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/306)


<!--
TEMPLATE_METADATA:
  required_sections:
  - Життєпис
  - Внесок
  - Спадщина
  - Підсумок
  - Потрібно більше практики?
  pedagogy: Immersion
  min_word_count: 2000
  required_callouts: []
  description: C1 biography modules focus on cultural figures
-->

---

## Quick Reference Checklist

Before submitting a C1 biography module, verify all items from `c1-module-template.md` PLUS:

### Biography-Specific Requirements
- [ ] **CBI pedagogy:** Content-Based Instruction (vocabulary through narrative)
- [ ] **Extended narrative:** 800-1000 word biographical account
- [ ] **Primary sources (≥2):** Include quotes, letters, or speeches from the figure using `[!quote]` callouts
- [ ] **Reading tasks (2-3):** External reading assignments with linguistic analysis questions
- [ ] **Essay assignment:** 400+ word comparative essay with model answer and rubric
- [ ] **Activity count:** 10-12 language-focused activities (NOT 14+)
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

## Reading Tasks (External Assignments)

Biography modules should include **2-3 external reading tasks** for deeper engagement with primary sources and scholarly biographies.

```yaml
# In activities/{slug}.yaml

- type: reading
  id: c1-XX-reading-01
  title: "Первинні джерела: Листи/Промови/Твори"
  resource:
    type: primary_source
    url: "https://..."
    title: "[Figure Name]: [Document Title]"
  tasks:
    - "Який регістр використовує автор у цьому документі? Наведіть приклади."
    - "Знайдіть три приклади емоційно забарвленої лексики"
    - "Порівняйте мову автора з сучасною українською. Які слова застаріли?"

- type: reading
  id: c1-XX-reading-02
  title: "Науковий біографічний нарис"
  resource:
    type: article
    url: "https://..."
    title: "[Ukrainian historian's biography]"
  tasks:
    - "Як автор використовує біографічну лексику (відіграти роль, творча спадщина)?"
    - "Знайдіть приклади академічного регістру в тексті"
    - "Порівняйте інтерпретацію історика з аналізом у модулі"
```

**Note:** Questions focus on LINGUISTIC analysis, not biographical interpretation.

---

## Essay Assignment

Each biography module should include a **400+ word comparative essay** with model answer and rubric.

```markdown
# Есе

## Тема

Напишіть порівняльне есе (400+ слів): "[Figure 1] та [Figure 2]: Порівняльний аналіз внеску в українську культуру"

**Вимоги:**
- Використайте лексику та граматику модуля
- Порівняйте підходи, досягнення, спадщину двох постатей
- Використайте цитати з первинних джерел
- Застосуйте біографічну та історичну лексику

**Структура:**
1. Вступ (100 слів) — контекст та теза
2. Основна частина (200 слів) — порівняльний аналіз
3. Висновок (100 слів) — значення для сучасної України

## Критерії оцінювання

| Критерій | Вага | Опис |
|----------|------|------|
| **Мовна якість** | 40% | Граматична правильність, біографічна лексика, складність речень (C1 рівень) |
| **Використання матеріалу** | 30% | Цитування первинних джерел, використання лексики модуля |
| **Порівняльний аналіз** | 20% | Логічне порівняння двох постатей |
| **Структура та зв'язність** | 10% | Організація, дискурсивні маркери |

## Зразок відповіді

[400+ word model essay demonstrating:]
- C1-level grammar and syntax
- Module biographical vocabulary (відіграти роль, творча спадщина, брати участь)
- Comparative analysis structure
- Citations from primary sources
- Публіцистичний register

**Мовні особливості зразка:**
- Біографічні колокації: "відіграв визначну роль", "творча спадщина"
- Порівняльні конструкції: "на відміну від", "подібно до"
- Складні речення з підрядними
- Публіцистичний регістр
```

---

## Biography-Specific Activities

### CRITICAL: Language Practice, Not Biographical Recall

<critical>

**These are LANGUAGE lessons that use biography as context, NOT biography tests taught in Ukrainian.**

**The Golden Rule:** "Can the learner answer this without reading the Ukrainian text?"
- **If YES** → Rewrite (tests biographical recall, not language)
- **If NO** → Keep (tests Ukrainian comprehension)

### Examples: GOOD vs BAD Activities

**❌ BAD (Tests Biographical Facts):**
```markdown
1. Шевченко народився в [___] році.
   > [!answer] 1814
```
Problem: Tests dates. No language learning.

**❌ BAD (Tests Factual Recall):**
```markdown
1. Хто викупив Шевченка з кріпацтва?
   - [x] Група митців та меценатів
```
Problem: Tests biographical knowledge from memory.

**✅ GOOD (Tests Ukrainian Collocations):**
```markdown
1. Згідно з текстом, Шевченко [___] визначну роль у розвитку української літератури.
   > [!answer] відіграв
   > [!options] відіграв | зробив | мав | дав
```
Why GOOD: Tests fixed collocation (відіграти роль), requires reading Ukrainian text.

**✅ GOOD (Tests Reading Comprehension):**
```markdown
1. Як автор характеризує вплив цієї постаті на українську культуру?
   - [x] Автор підкреслює революційний характер її творчості
```
Why GOOD: Requires understanding how the MODULE describes the figure's influence.

**Key phrases to use:**
- "Згідно з текстом..."
- "Як автор характеризує..."
- "Який внесок автор виділяє..."

**Never ask:**
- "У якому році народився/померла..." (tests dates)
- "Де навчався/жила..." (tests facts)
- "Хто був..." (tests biographical knowledge)

</critical>

---

### Activity Mix for Biography Modules

**Total: 10-12 activities** (focus on quality over quantity)

| Activity Type | Count | Purpose | Example |
|---------------|-------|---------|---------|
| **quiz** | 4-5 | Reading comprehension | "Згідно з текстом, який внесок автор виділяє?" |
| **fill-in / cloze** | 3-4 | Biographical vocabulary | "Постать [___] визначну роль" → відіграла |
| **error-correction** | 2-3 | Grammar practice | Fix case/collocation errors in biographical sentences |
| **match-up** | 1-2 | Terminology | Ukrainian term ↔ Ukrainian definition |
| **select** | 1-2 | Source analysis | Linguistic features of primary source quotes |

**Note:** Plus 2-3 external reading tasks and 1 essay assignment (tracked in activities YAML).

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/c1-XX-biography.yaml`:**

```yaml
- type: quiz
  title: Розуміння біографії
  items:
    - question: Згідно з текстом, який головний внесок цієї постаті?
      options:
        - text: Розвиток літератури
          correct: true
        - text: Військові перемоги
          correct: false
      explanation: Текст наголошує на літературній спадщині.

- type: fill-in
  title: Біографічна лексика
  items:
    - sentence: Ця постать _____ визначну роль в історії.
      answer: відіграла
      options:
        - відіграла
        - зробила
        - мала
```

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

---

## Content Structure Note

### Vocabulary & Activities
**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:
- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

The build system will inject these sections at build time.
**Example `vocabulary/c1-XX-biography.yaml`:**

```yaml
items:
- lemma: постать
  ipa: /pɔˈstɑtʲ/
  translation: figure/personality
  pos: noun
  gender: f
  note: історична постать
- lemma: спадщина
  ipa: /spɑˈdʃt͡ʃɪnɑ/
  translation: legacy/heritage
  pos: noun
  gender: f
  note: інтелектуальна спадщина
```

**Why YAML sidecar:**
- Validates schema automatically
- Ensures consistent formatting
- Enables programmatic processing
- Audit validates this exact format for C1+

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
