# C1 Fine Arts Module Template

**Purpose:** Reference template for C1 fine arts modules covering Classical Music, Opera, Visual Arts, Ballet, Theater, and Architecture

**Based on:** `c1-module-template.md` — inherits all C1 quality standards

**Related Issue:** [#306](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/306)

**Proposed Modules:** See `C1-REVIEW-PROPOSAL.md` for the comprehensive arts expansion plan

<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Аналіз мистецтва
  - Підсумок
  - Потрібно більше практики?
  pedagogy: Immersion
  min_word_count: 3000
  required_callouts: []
  description: C1 fine arts modules analyze Ukrainian visual arts
-->

---

## Quick Reference Checklist

Before submitting a C1 fine arts module, verify all items from `c1-module-template.md` PLUS:

### Fine Arts-Specific Requirements

- [ ] **CBI pedagogy:** Content-Based Instruction (arts content drives language learning)
- [ ] **Authentic materials:** Excerpts from reviews, librettos, exhibition catalogs, program notes
- [ ] **Art-specific terminology:** музичний термін, сценічна мова, мистецтвознавство
- [ ] **Historical context:** European context AND Ukrainian national significance
- [ ] **Ukrainian contribution:** Emphasize Ukrainian artists' role in world culture
- [ ] **Register:** Mix of науковий (academic) and публіцистичний (arts journalism)
- [ ] **Modern relevance:** Contemporary Ukrainian artists continuing traditions
- [ ] **Reading tasks (2-3):** External reading assignments with linguistic analysis questions
- [ ] **Essay activity:** `essay-response` activity in YAML — NO essay section in markdown
- [ ] **Activity count:** 10-12 language-focused activities (reduced from 14+)

---

## Module Types

### Classical Music (3 modules)

| Module | Focus | Key Figures & Works |
|--------|-------|---------------------|
| M141 | Baroque & Early Classical | Бортнянський, Березовський, Ведель |
| M142 | National School (19th-early 20th c.) | Лисенко, Леонтович, Стеценко, Левіцький |
| M143 | Modern Ukrainian Classical | Лятошинський, Сильвестров, Скорик, Станкович |

### Opera & Vocal Arts (2 modules)

| Module | Focus | Key Works |
|--------|-------|-----------|
| M144 | Ukrainian Opera Tradition | Запорожець за Дунаєм, Наталка Полтавка, Тарас Бульба |
| M145 | Art Song & Choral Music | Українська пісня, хорова традиція, Щедрик |

### Visual Arts (2 modules)

| Module | Focus | Key Figures |
|--------|-------|-------------|
| M146 | Icons to Avant-Garde | Боровиковський, Федотов, Бойчук, Казимир Малевич |
| M147 | Modern Ukrainian Visual Arts | Шишко, Ройтбурд, сучасне мистецтво |

### Ballet & Dance (1 module)

| Module | Focus | Key Figures |
|--------|-------|-------------|
| M148 | Ukrainian Ballet | Серж Лифар, Надія Павлова, Національний балет |

### Theater (2 modules)

| Module | Focus | Key Figures |
|--------|-------|-------------|
| M149 | Historical Ukrainian Theater | Лесь Курбас, Березіль, Гнат Юра |
| M150 | Contemporary Ukrainian Theater | Сучасні театри, режисери, драматурги |

### Architecture (1 module)

| Module | Focus | Key Sites |
|--------|-------|-----------|
| M151 | Ukrainian Architecture | Бароко, модерн, конструктивізм, сучасна архітектура |

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

**See:** `claude_extensions/phases/stage-4-review-fix.md` Section 9 for detailed naturalness criteria.

**For batch scanning:** Use `/scan-naturalness {level} {start} {end}` to scan completed modules.

---

## Module Structure (Fine Arts-Specific)

### 1. Frontmatter

```yaml
---
module: c1-1XX
title: "[Fine Arts Topic]: Ukrainian Title"
phase: "C1.5 [Fine Arts & High Culture]"
pedagogy: "CBI"  # Content-Based Instruction
register: "науковий/публіцистичний"
tags:
  - fine-arts
  - [domain: classical-music, opera, visual-arts, ballet, theater, architecture]
  - [era: baroque, romantic, modern, contemporary]
grammar:
  - "Art criticism vocabulary"
  - "Aesthetic terminology"
vocabulary_focus:
  - "Мистецька термінологія"
  - "Критика та аналіз"
---
```

### 2. Fine Arts Content Structure

#### Section 1: Artistic Introduction — 400-500 words

```markdown
# [Fine Arts Topic]

> **Чому це важливо?**
>
> [Explain artistic/cultural significance]
> [Connection to world culture AND Ukrainian identity]
> [Why C1 learners should know this]

## Вступ

[Engaging introduction to the art form — 200-250 words]

[Historical context — origins, development, Ukrainian contribution]

> **Світовий контекст**
>
> [How this art form developed in Europe and Ukraine's role]

### Ключова термінологія

| Термін | Значення | Приклад |
|--------|----------|---------|
| [Term 1] | [Meaning] | [Example usage] |
| [Term 2] | [Meaning] | [Example usage] |
| [Term 3] | [Meaning] | [Example usage] |
```

#### Section 2: Deep Artistic Content — 800-1000 words

```markdown
## [Main Artistic Content]

### [Era/Movement/Figure 1]: [Title]

[Detailed exploration — 300-400 words]

**Ключова постать: [Name]** (роки життя)

> [Biographical sketch — 100-150 words]
>
> **Головні твори:**
> - [Work 1] (рік) — [significance]
> - [Work 2] (рік) — [significance]
> - [Work 3] (рік) — [significance]

**Автентичний текст:**

> [Excerpt from review, libretto, exhibition catalog, or program notes — 100-200 words]
>
> **Ключові терміни:**
> - [Term]: [explanation]
> - [Term]: [explanation]

> **Мистецький аналіз**
>
> [Critical analysis of style, technique, significance]

---

### [Era/Movement/Figure 2]: [Title]

[Continue pattern — 300-400 words]

**Порівняння з європейським контекстом:**

| Аспект | Українська школа | Європейська традиція |
|--------|------------------|----------------------|
| Стиль | [Ukrainian style] | [European equivalent] |
| Вплив | [Ukrainian influence] | [European influence] |
| Особливість | [Ukrainian distinction] | [European norm] |

---

### [Era/Movement/Figure 3]: [Title]

[Continue pattern — 300-400 words]

> **Культурне значення**
>
> [Why this matters for Ukrainian cultural identity]
```

#### Section 3: Technical Analysis — 300-400 words

```markdown
## Технічний аналіз

### [Technique/Style/Form]

[Detailed explanation of artistic technique — 150-200 words]

**Приклад аналізу:**

[Analyze a specific work in detail — 100-150 words]

| Елемент | Характеристика | Значення |
|---------|----------------|----------|
| [Element 1] | [Characteristic] | [Significance] |
| [Element 2] | [Characteristic] | [Significance] |
| [Element 3] | [Characteristic] | [Significance] |

### Критичне мислення

**Питання для роздуму:**
1. Як українські митці поєднували національне та європейське?
2. Яку роль відіграло мистецтво у формуванні національної ідентичності?
3. Як радянський період вплинув на розвиток цього мистецтва?
4. Які сучасні митці продовжують традицію?
```

#### Section 4: Modern Context — 200-300 words

```markdown
## Сучасна Україна

### Сучасні майстри

[Contemporary artists continuing the tradition — 100-150 words]

**Провідні митці:**
- [Contemporary figure 1] — [contribution]
- [Contemporary figure 2] — [contribution]
- [Contemporary figure 3] — [contribution]

### Де побачити/почути

| Місце | Тип | Репертуар/Колекція |
|-------|-----|-------------------|
| [Venue 1] | [Type] | [Specialty] |
| [Venue 2] | [Type] | [Specialty] |
| [Festival/event] | [Type] | [Specialty] |

> **Де знайти**
>
> [Recordings, streaming, museums, concert halls, YouTube channels]
```

---

## Reading Tasks (External Assignments)

### Purpose

Reading tasks provide authentic Ukrainian practice beyond the module. They focus on **linguistic analysis**, not arts interpretation.

### Format (2-3 reading tasks per module)

```yaml
activities:
  - type: reading
    id: c1-1XX-reading-01
    title: "Аналіз мистецької рецензії"
    resource:
      type: authentic_text
      url: "https://...Ukrainian arts magazine/website..."
      title: "Рецензія на виставу/концерт/виставку"
    tasks:
      - "Який регістр використовує рецензент? Наведіть три приклади науково-публіцистичної лексики."
      - "Знайдіть у тексті п'ять мистецьких термінів з модуля. Як автор їх використовує?"
      - "Порівняйте синтаксис рецензії з побутовою мовою. Які складні конструкції ви помітили?"

  - type: reading
    id: c1-1XX-reading-02
    title: "Первинне джерело: Програмна примітка / Лібрето"
    resource:
      type: primary_source
      url: "https://...historical text..."
      title: "[Composer/Artist Name]: [Work Title] — програмна примітка (рік)"
    tasks:
      - "Який регістр використовує автор? Знайдіть три приклади науково-популярної мови."
      - "Які тропи та фігури мови є в тексті? Яка їхня функція?"
      - "Порівняйте лексику тексту з сучасною українською. Які слова застаріли або змінили значення?"

  - type: reading
    id: c1-1XX-reading-03
    title: "Інтерв'ю з сучасним митцем"
    resource:
      type: contemporary_media
      url: "https://...interview link..."
      title: "Інтерв'ю з [Contemporary Artist]"
    tasks:
      - "Як митець описує свій творчий процес? Яку лексику він використовує?"
      - "Знайдіть три приклади метафоричного використання мистецьких термінів."
      - "Порівняйте регістр інтерв'ю з академічним текстом модуля. Які відмінності?"
```

### Reading Task Guidelines

**✅ GOOD Questions (Linguistic Analysis):**
- "Який регістр використовує автор рецензії?"
- "Знайдіть п'ять пасивних конструкцій у тексті. Чому автор їх використовує?"
- "Порівняйте лексику програмної примітки з лексикою модуля."
- "Які дієслова руху використовує автор для опису балету?"

**❌ BAD Questions (Content Interpretation):**
- "Яку оцінку дає рецензент виставі?" ← Tests interpretation
- "Чи погоджуєтеся ви з думкою автора?" ← Tests opinion, not language
- "Що символізує цей образ у творі?" ← Tests arts analysis

---

## Essay Activities (In YAML Only)

**CRITICAL:** Essay activities are defined ONLY in `activities/{slug}.yaml` as `type: essay-response`.

**DO NOT include `## Есе` sections with model answers in markdown.** This causes:
- Content redundancy (essay prompt + model answer duplicated)
- Word count inflation (~700 words added)
- QA confusion

**Example essay-response activity in YAML:**

```yaml
- type: essay-response
  id: c1-XX-essay-01
  title: 'Мистецтвознавче есе'
  prompt: |
    Напишіть мистецтвознавчий есе: "[Topic]: Аналіз українського внеску у світове мистецтво"

    Структура:
    - Вступ (100 слів): Контекст і теза
    - Основна частина (250 слів): Аналіз з прикладами
    - Висновок (50 слів): Підсумок та значення

    Мовні вимоги:
    - Науково-публіцистичний регістр
    - Мінімум 10 мистецьких термінів з модуля
  rubric:
    - criterion: Мовна якість
      weight: 40
      description: Граматика, мистецька термінологія, складність речень
    - criterion: Використання матеріалу
      weight: 30
      description: Цитування джерел, лексика модуля
    - criterion: Аналітична глибина
      weight: 20
      description: Порівняння з контекстом
    - criterion: Структура
      weight: 10
      description: Організація, дискурсивні маркери
```

---

## Fine Arts-Specific Activities

### CRITICAL: Language Practice, Not Content Testing

<critical>

**These are LANGUAGE lessons that use fine arts as context, NOT arts history lessons taught in Ukrainian.**

### The Golden Rule

**"Can the learner answer this without reading the Ukrainian text?"**

- **If YES** → Rewrite (it's testing arts knowledge, not language)
- **If NO** → Keep (it's testing Ukrainian comprehension)

| Component | Purpose |
|-----------|---------|
| **Lesson Content** | Teaches BOTH Ukrainian language AND fine arts knowledge |
| **Activities** | Practice ONLY Ukrainian language skills using arts content as context |

### Examples: GOOD vs BAD Activities

#### ❌ BAD (Tests Arts Knowledge)

```markdown
## quiz: Історія опери

1. У якому році була написана опера "Запорожець за Дунаєм"?
   - [ ] 1860
   - [x] 1863
   - [ ] 1865
   - [ ] 1870

2. Хто написав "Щедрик"?
   - [ ] Лисенко
   - [x] Леонтович
   - [ ] Стеценко
   - [ ] Лятошинський
```

**Problem:** Tests dates and names. Can be answered from prior knowledge without reading Ukrainian text.

#### ✅ GOOD (Tests Ukrainian Language)

```markdown
## quiz: Розуміння тексту модуля

> **Інструкція:** Відповідайте на питання на основі прочитаного тексту модуля.

1. Згідно з текстом, як автор характеризує внесок Миколи Лисенка в українську музику?
   - [ ] Автор зазначає, що Лисенко лише обробляв народні пісні
   - [x] Автор виділяє Лисенка як засновника української національної музичної школи
   - [ ] Автор пише, що творчість Лисенка не мала впливу на наступні покоління
   - [ ] Автор не згадує Лисенка в тексті
   > У тексті модуля чітко формулюється роль Лисенка в розділі про національну школу.

2. Як у тексті модуля інтерпретується значення опери "Запорожець за Дунаєм"?
   - [ ] Текст зосереджується лише на музичних аспектах
   - [ ] Автор називає оперу невдалою спробою
   - [x] Автор підкреслює, що це перша українська опера, яка утвердила жанр
   - [ ] У тексті не згадується ця опера
   > У розділі про українську оперу автор детально пояснює історичне значення твору.
```

**Why GOOD:**
- Requires reading the MODULE'S ANALYSIS in Ukrainian
- Tests comprehension of HOW author describes, not WHAT happened
- Answer depends on understanding Ukrainian explanations

#### ❌ BAD (Tests Arts Facts)

```markdown
## fill-in: Композитори

1. Леонтович народився в [___] році.
   > [!answer] 1877
   > [!options] 1875 | 1877 | 1879 | 1881

2. Він написав [___] хорових творів.
   > [!answer] понад 100
   > [!options] близько 50 | понад 100 | більше 200
```

**Problem:** Tests biographical facts and numbers. No language learning.

#### ✅ GOOD (Tests Ukrainian Collocations)

```markdown
## fill-in: Мистецька лексика в контексті

1. Згідно з текстом, Леонтович [___] значний вплив на розвиток української хорової музики.
   > [!answer] справив
   > [!options] справив | зробив | мав | дав
   > Fixed collocation: справити вплив = to exert influence.

2. Його хорові твори [___] невід'ємною частиною репертуару українських хорів.
   > [!answer] стали
   > [!options] стали | були | є | роблять
   > Collocation: стати частиною = to become part of.

3. Композитор [___] унікальний стиль, що поєднував фольклор і професійну техніку.
   > [!answer] виробив
   > [!options] виробив | зробив | створив | написав
   > Fixed expression: виробити стиль = to develop a style.
```

**Why GOOD:**
- Tests Ukrainian collocations (справити вплив, стати частиною, виробити стиль)
- Requires understanding how these expressions work in Ukrainian
- Language-focused, not fact-focused

### Key Phrases to Use

**Always start quiz questions with:**
- "Згідно з текстом..."
- "У тексті модуля автор..."
- "Як автор описує/характеризує/інтерпретує..."
- "Який аргумент автор наводить..."

**Never ask:**
- "У якому році..." (tests dates)
- "Хто написав..." (tests names)
- "Скільки творів..." (tests numbers)
- "Що символізує..." (unless: "як автор тлумачить символіку")

</critical>

---

### Activity Mix (10-12 Activities)

| Activity Type | Count | Purpose | Example (Fine Arts) |
|---------------|-------|---------|---------------------|
| **quiz** | 4-5 | Reading comprehension | "Згідно з текстом, як автор характеризує стиль Лисенка?" |
| **fill-in / cloze** | 3-4 | Vocabulary in context | "Композитор [___] унікальний стиль" → виробив |
| **error-correction** | 2-3 | Grammar practice | Fix case errors in arts review sentences |
| **match-up** | 1-2 | Terminology | Ukrainian arts term ↔ Ukrainian definition |
| **select / mark-the-words** | 1-2 | Analytical | Find passive voice in arts review |
| **group-sort** | 1 | Categorization | Sort composers by era using module vocabulary |

**Total:** 10-12 activities (down from 14+)

**Focus:** All activities test Ukrainian language skills using fine arts content as authentic context.

---

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/c1-144-opera.yaml`:**

```yaml
- type: reading
  title: Аналіз мистецької рецензії
  resource:
    type: authentic_text
    url: https://example.com/review
    title: Рецензія на оперу
  tasks:
    - Знайдіть приклади оцінної лексики.
    - Як автор характеризує постановку?

- type: quiz
  title: Розуміння тексту модуля
  items:
    - question: Згідно з текстом, яке значення опери "Запорожець за Дунаєм"?
      options:
        - text: Перша національна опера
          correct: true
        - text: Невдалий експеримент
          correct: false
```

---

### Activity Examples (Conceptual)

*Note: These activities must be implemented in YAML.*

1. **Arts Terminology Matching (match-up):** Match phrase to meaning.
2. **Era/Style Classification (group-sort):** Sort by era/style.
3. **Reading Comprehension (quiz):** Test understanding of text.
4. **Arts Review Cloze (cloze):** Fill in the blanks.

---

## Advanced Seminar-Style Activities

### Source-Evaluation Activity

**Use for analyzing art criticism, exhibition catalogs, reviews, and program notes:**

```yaml
- type: source-evaluation
  title: "Оцінка джерела: Рецензія/Каталог/Програмна примітка"
  instruction: "Застосуйте метод критичного аналізу до цього мистецтвознавчого тексту."
  source_text: |
    [Excerpt from art review, exhibition catalog, concert program note — 100-200 words]
  source_metadata:
    author: "[Critic/curator name]"
    date: "[Year of publication]"
    type: "[review/catalog/program_note/manifesto]"
    context: "[Publication venue, artistic context, ideological background]"
  evaluation_criteria:
    - authorship
    - date_and_context
    - intended_audience
    - purpose_and_bias
    - omissions
  guiding_questions:
    - "Яку естетичну позицію представляє автор?"
    - "Який культурний/ідеологічний контекст публікації?"
    - "Як автор оцінює український внесок у світове мистецтво?"
    - "Що автор ігнорує або применшує?"
  model_evaluation: |
    **1. Авторство:** [Who wrote it, their aesthetic school]
    **2. Контекст:** [When/where published, cultural moment]
    **3. Естетична позиція:** [What aesthetic values the author promotes]
    **4. Упередження:** [Nationalist, formalist, socialist realist, etc.]
    **5. Опущення:** [What perspectives or artists are ignored]
```

### Debate Activity

**Use for contested aesthetic questions and artistic interpretations:**

```yaml
- type: debate
  title: "Дискусія: [Contested Aesthetic Question]"
  instruction: "Проаналізуйте конкуруючі мистецтвознавчі позиції та сформулюйте власну оцінку."
  debate_question: "[The contested question about art, style, or cultural significance]"
  historical_context: |
    [Background on the artistic controversy — 50-100 words]
  positions:
    - name: "[Position 1 — e.g., Національна школа]"
      proponents: "[Critics, institutions who hold this view]"
      argument: "[Core aesthetic argument]"
      evidence:
        - "[Artistic evidence — specific works, techniques]"
        - "[Critical support]"
      weaknesses:
        - "[Limitation of this perspective]"
    - name: "[Position 2 — e.g., Європейський контекст]"
      proponents: "[Who holds this view]"
      argument: "[Core argument]"
      evidence:
        - "[Evidence]"
      weaknesses:
        - "[Critique]"
    - name: "[Position 3 — e.g., Радянська/офіційна позиція]"
      proponents: "[Soviet/official criticism]"
      argument: "[Their position]"
      evidence:
        - "[Their claimed evidence]"
      weaknesses:
        - "[Why problematic — ideological, limiting, etc.]"
  analysis_tasks:
    - "Які естетичні критерії використовує кожна позиція?"
    - "Як ідеологія впливає на оцінку мистецтва?"
    - "Чи можна поєднати національну та європейську перспективи?"
    - "Яку позицію ви вважаєте найбільш переконливою? Чому?"
  model_analysis: |
    [Balanced evaluation showing how aesthetic debates reflect cultural politics.
    Should demonstrate critical thinking about art criticism.]
```

**Example contested questions for fine arts:**
- "Чи Малевич — український чи російський художник?"
- "Як оцінювати соцреалістичне мистецтво: ідеологія чи естетика?"
- "Чи українське бароко — регіональний варіант чи окремий стиль?"
- "Лисенко: національний композитор чи європейський романтик?"

---

## Engagement Boxes for Fine Arts Modules

```markdown
> **Світовий контекст**
>
> [How Ukrainian art fits into world culture]

> **Чи знали ви?**
>
> [Surprising fact about the artist or work]

> **Мистецький аналіз**
>
> [Technical or aesthetic insight]

> **Культурне значення**
>
> [Why this matters for Ukrainian identity]

> **Де послухати/подивитися**
>
> [Recordings, performances, exhibitions, YouTube, streaming]

> **Сучасна спадщина**
>
> [How contemporary artists continue the tradition]
```

---

---

## Content Structure Note

### Vocabulary & Activities

**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:
- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

The build system will inject these sections at build time.
**Example `vocabulary/c1-144-opera.yaml`:**

```yaml
items:
- lemma: опера
  ipa: /ɔpɛrɑ/
  translation: opera
  pos: ім. (ж.р.)
  note: музично-драматичний жанр
- lemma: лібрето
  ipa: /lʲibrɛtɔ/
  translation: libretto
  pos: ім. (с.р.)
  note: текст опери
```

---

## Domain-Specific Vocabulary by Module Type

### Classical Music Vocabulary

| Термін | Переклад | Примітки |
|--------|----------|----------|
| камерна музика | chamber music | для невеликого ансамблю |
| хоровий концерт | choral concerto | жанр бароко (Бортнянський) |
| симфонічна поема | symphonic poem | програмний оркестровий твір |
| етюд | etude | навчальна п'єса |
| ноктюрн | nocturne | "нічна" п'єса |
| прелюдія | prelude | вступна п'єса |

### Opera Vocabulary

| Термін | Переклад | Примітки |
|--------|----------|----------|
| тенор | tenor | високий чоловічий голос |
| сопрано | soprano | високий жіночий голос |
| бас | bass | низький чоловічий голос |
| речитатив | recitative | мелодекламація в опері |
| дует | duet | номер для двох співаків |
| фінал | finale | заключна частина акту |

### Visual Arts Vocabulary

| Термін | Переклад | Примітки |
|--------|----------|----------|
| полотно | canvas | основа для живопису |
| олія | oil (paint) | олійні фарби |
| акварель | watercolor | водяні фарби |
| графіка | graphic art | мистецтво малюнка |
| скульптура | sculpture | просторове мистецтво |
| авангард | avant-garde | експериментальне мистецтво |
| іконопис | icon painting | церковний живопис |

### Theater Vocabulary

| Термін | Переклад | Примітки |
|--------|----------|----------|
| режисер | director | постановник вистави |
| актор | actor | виконавець ролі |
| сцена | stage | місце дії |
| декорації | set design | оформлення сцени |
| драматург | playwright | автор п'єси |
| вистава | performance | театральне дійство |
| антракт | intermission | перерва між актами |

### Ballet Vocabulary

| Термін | Переклад | Примітки |
|--------|----------|----------|
| балерина | ballerina | танцівниця балету |
| хореограф | choreographer | автор танців |
| пуанти | pointe shoes | балетне взуття |
| па-де-де | pas de deux | танець удвох |
| кордебалет | corps de ballet | ансамбль танцівників |
| прима | prima ballerina | провідна балерина |

### Architecture Vocabulary

| Термін | Переклад | Примітки |
|--------|----------|----------|
| фасад | facade | зовнішня стіна будівлі |
| купол | dome | склепінне перекриття |
| дзвіниця | bell tower | вежа з дзвонами |
| бароко | baroque | архітектурний стиль XVII-XVIII ст. |
| модерн | art nouveau | стиль кінця XIX — поч. XX ст. |
| конструктивізм | constructivism | авангардний стиль 1920-х |

---

## Key Ukrainian Figures by Domain

### Classical Music

| Постать | Роки | Внесок |
|---------|------|--------|
| Дмитро Бортнянський | 1751-1825 | Хорові концерти, директор Придворної капели |
| Максим Березовський | 1745-1777 | Перший український оперний композитор |
| Артемій Ведель | 1767-1808 | Духовна хорова музика |
| Микола Лисенко | 1842-1912 | "Батько української музики", опери, романси |
| Микола Леонтович | 1877-1921 | "Щедрик" (Carol of the Bells) |
| Борис Лятошинський | 1895-1968 | Українська симфонічна школа |
| Валентин Сильвестров | 1937- | Постмодерна класична музика |

### Opera & Vocal

| Постать | Роки | Внесок |
|---------|------|--------|
| Семен Гулак-Артемовський | 1813-1873 | "Запорожець за Дунаєм" |
| Соломія Крушельницька | 1872-1952 | Світова оперна зірка |
| Іван Козловський | 1900-1993 | Тенор світового рівня |
| Анатолій Солов'яненко | 1932-1999 | Тенор, народний артист СРСР |

### Visual Arts

| Постать | Роки | Внесок |
|---------|------|--------|
| Володимир Боровиковський | 1757-1825 | Портретист, класицизм |
| Тарас Шевченко | 1814-1861 | Художник і поет |
| Михайло Бойчук | 1882-1937 | Монументалізм, бойчукісти |
| Казимір Малевич | 1879-1935 | Супрематизм |
| Олександр Архипенко | 1887-1964 | Скульптура модернізму |

### Ballet

| Постать | Роки | Внесок |
|---------|------|--------|
| Серж Лифар | 1905-1986 | Балетмейстер Паризької опери |
| Надія Павлова | 1956- | Прима-балерина Великого театру |

### Theater

| Постать | Роки | Внесок |
|---------|------|--------|
| Лесь Курбас | 1887-1937 | Режисер-реформатор, театр "Березіль" |
| Гнат Юра | 1888-1966 | Актор, засновник театру ім. Франка |
| Марія Заньковецька | 1854-1934 | Легендарна актриса |

### Architecture

| Постать | Роки | Внесок |
|---------|------|--------|
| Іван Григорович-Барський | 1713-1791 | Українське бароко |
| Владислав Городецький | 1863-1930 | Київський модерн |
| Віктор Кричевський | 1872-1952 | Український модерн |

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/c1-module-template.md`
- **Folk culture template:** `docs/l2-uk-en/templates/c1-folk-culture-module-template.md`
- **C1 Curriculum Plan:** `docs/l2-uk-en/C1-CURRICULUM-PLAN.md`
- **Arts Expansion Proposal:** `docs/l2-uk-en/C1-REVIEW-PROPOSAL.md`
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-29
**Template Version:** 1.0
