# C1 Academic Module Template

**Purpose:** Reference template for C1 academic modules (M01-35: Academic Foundation & Professional Communication)

**Based on:** `c1-module-template.md` — inherits all C1 quality standards

**Related Issue:** [#306](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/306)

<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Академічний текст
  - Аналіз
  - Підсумок
  - Потрібно більше практики?
  pedagogy: Immersion
  min_word_count: 4000
  required_callouts: []
  description: C1 academic modules with research-level Ukrainian
-->

---

## Quick Reference Checklist

Before submitting a C1 academic module, verify all items from `c1-module-template.md` PLUS:

### Academic-Specific Requirements

- [ ] **Academic rigor:** University-level texts (500-800+ words)
- [ ] **Research writing:** Teaches academic writing conventions
- [ ] **Citation practices:** Proper referencing in Ukrainian academic tradition
- [ ] **Argumentation structure:** Thesis, evidence, counterargument, conclusion
- [ ] **Register:** Науковий (scientific/academic) primary register
- [ ] **Comparative analysis:** Analyze 2+ academic sources

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

## Module Structure (Academic-Specific)

### 1. Frontmatter

```yaml
---
module: c1-XX
title: "Ukrainian Academic Title"
phase: "C1.1 [Academic Foundation]"  # or C1.2 [Professional]
pedagogy: "Academic"
register: "науковий"  # or "офіційно-діловий" for professional modules
tags:
  - academic
  - [specific-topic: research-writing, argumentation, citation, abstract]
grammar:
  - "Academic register syntax"
  - "Impersonal constructions in academic writing"
vocabulary_focus:
  - "Academic terminology"
  - "Discipline-specific vocabulary"
---
```

### 2. Academic Content Structure

#### Section 1: Презентація (Academic Text Presentation) — 600-800 words

```markdown
# [Academic Topic Title]

> 🎯 **Чому це важливо?**
>
> [Explain academic/professional significance in Ukrainian]
> [Connect to university/professional contexts]
> [Preview skills to be developed]

## Академічний текст

**Джерело:** [Author, Publication, Year — or adapted from]

> [600-800 word authentic academic text or adapted excerpt]
>
> [Text should demonstrate:
> - Academic register conventions
> - Impersonal constructions
> - Citation practices
> - Complex sentence structures
> - Discipline-specific terminology]

### Аналіз тексту

**Регістрові маркери:**
- [Point out academic register features]
- [Identify impersonal constructions: було досліджено, вважається, що...]
- [Note vocabulary choices typical of науковий стиль]

**Структурні елементи:**
- Вступ: [Identify thesis/introduction]
- Аргументи: [Identify supporting points]
- Висновок: [Identify conclusion]

> 💡 **Академічне спостереження**
>
> [Insight about academic Ukrainian writing conventions]
```

#### Section 2: Академічне письмо (Academic Writing Instruction) — 800-1000 words

```markdown
## Академічне письмо

### Структура наукового тексту

**1. Анотація (Abstract):**
- Мета дослідження
- Методологія
- Основні результати
- Висновки

**Приклад анотації:**
> [100-150 word sample abstract in academic Ukrainian]

---

**2. Вступ (Introduction):**
- Актуальність теми
- Мета дослідження
- Завдання
- Методи

**Ключові фрази:**
| Функція | Фрази |
|---------|-------|
| Актуальність | На сучасному етапі..., Останнім часом... |
| Мета | Мета цієї статті полягає в тому, щоб... |
| Завдання | Для досягнення мети було поставлено такі завдання... |

---

**3. Основна частина (Body):**
- Аргументи з доказами
- Контраргументи та їх спростування
- Цитування джерел

**Цитування в українській традиції:**
| Тип | Приклад |
|-----|---------|
| Пряме цитування | Як зазначає Іваненко, «...» [5, с. 34] |
| Парафраз | На думку дослідника [3], ... |
| Посилання | Це підтверджується даними [7, 8, 12] |

---

**4. Висновки (Conclusion):**
- Підсумок результатів
- Практичне значення
- Перспективи подальших досліджень

> 🎓 **Академічна перспектива**
>
> [How this writing convention differs from English academic traditions]
```

#### Section 4: Comparative Analysis (YAML-ONLY)

**CRITICAL: DO NOT include an `## Аналіз` or `## Порівняльний аналіз` section in the markdown file.** This analysis is defined exclusively in `activities/{slug}.yaml` as an `essay-response` activity.

---

#### Section 5: Essay Activities (In YAML Only)

```markdown
## Практика

### Завдання 1: Написання анотації

Напишіть анотацію (150-200 слів) до [topic].

**Вимоги:**
- Структура: мета, методи, результати, висновки
- Регістр: науковий
- Безособові конструкції

**Зразок відповіді:**

> [Complete 150-200 word model abstract]

---

### Завдання 2: Академічне есе

**CRITICAL:** Essay activities are defined ONLY in `activities/{slug}.yaml` as `type: essay-response`.

**DO NOT include `## Есе` sections with model answers in markdown.** This causes:
- Content redundancy (essay prompt + model answer duplicated)
- Word count inflation (~700 words added to content)
- QA confusion (auditing both locations)

**Essay activity example in YAML:**

```yaml
- type: essay-response
  id: c1-XX-essay-01
  title: 'Академічне есе'
  prompt: |
    Напишіть академічне есе (300-400 слів) на тему: "[Topic]"

    Структура:
    1. Вступ (теза, актуальність)
    2. Аргументи з доказами (2-3 абзаци)
    3. Контраргумент та спростування
    4. Висновок
  rubric:
    - criterion: Структура
      weight: 25
      description: Чітка, логічна, академічна
    - criterion: Аргументація
      weight: 25
      description: Теза + докази + спростування контраргументів
    - criterion: Регістр
      weight: 25
      description: Науковий, безособові конструкції
    - criterion: Граматика
      weight: 25
      description: Складні конструкції, безпомилково
```
```

---

## Academic-Specific Activities

### CRITICAL: Language Practice, Not Content Testing

<critical>

**Activities test LANGUAGE SKILLS, not academic content recall.**

The lesson teaches both Ukrainian AND academic concepts. Activities practice only Ukrainian using academic content as context.

**✅ CORRECT:** "Згідно з текстом, як автор формулює свою тезу?" (requires reading Ukrainian)
**❌ WRONG:** "Яка структура наукової статті?" (tests academic knowledge recall, not language)

**Key Test:** Can the learner answer without reading the Ukrainian text? If yes, rewrite.

| Component | Purpose |
|-----------|---------|
| **Lesson Content** | Teaches BOTH Ukrainian language AND academic writing skills |
| **Activities** | Practice ONLY Ukrainian language skills using academic content as context |

**Activity Types and Their Language Focus:**
- **quiz**: Test reading comprehension of academic text — "Згідно з текстом модуля..."
- **fill-in**: Test academic vocabulary/collocations from module
- **match-up**: Test vocabulary — Ukrainian academic terms ↔ Ukrainian definitions
- **cloze**: Test vocabulary in academic context
- **group-sort**: Test register categorization using module vocabulary
- **error-correction**: Test grammar in academic sentences, NOT factual accuracy

</critical>

---

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/c1-01-academic.yaml`:**

```yaml
- type: quiz
  title: Розуміння тексту
  items:
    - question: Згідно з текстом, яка мета статті?
      options:
        - text: Аналіз проблеми
          correct: true
        - text: Опис експерименту
          correct: false

- type: fill-in
  title: Цитування джерел
  items:
    - sentence: На [___] дослідника, це важливо.
      answer: думку
      options:
        - думку
        - слова
```

---

### Citation Practice

```markdown
## fill-in: Цитування джерел

1. [___] дослідника Петренка, мова є основою національної ідентичності.
   - [x] На думку
   - [ ] За словами
   - [ ] Як вважає
   - [ ] Відповідно до
   > "На думку" + родовий відмінок — стандартна форма посилання.

2. Це підтверджується даними [___] дослідження.
   - [x] попереднього
   - [ ] цього
   - [ ] наступного
   > Посилання на попередні дослідження — академічний стандарт.

[12+ citation practice items]
```

### Impersonal Constructions

```markdown
## transform: Безособові конструкції

Перетворіть особові речення на безособові (академічний стиль):

1. Ми дослідили вплив мови на ідентичність.
   > [!answer] Було досліджено вплив мови на ідентичність.

2. Автори аналізують результати експерименту.
   > [!answer] Результати експерименту аналізуються.

3. Вчені виявили кореляцію між факторами.
   > [!answer] Виявлено кореляцію між факторами.

[10+ transformation items]
```

### Register Identification

```markdown
## group-sort: Регістр наукового тексту

Розподіліть фрази за ступенем формальності:

- group: Суто науковий
  - Мета цього дослідження полягає в тому, щоб...
  - Було виявлено статистично значущу кореляцію...
  - Отримані результати свідчать про...

- group: Академічний нейтральний
  - У статті розглядається питання...
  - Автор доходить висновку, що...
  - Проаналізовано дані...

- group: Популярно-науковий
  - Вчені з'ясували, що...
  - Дослідження показало...
  - Виявилося, що...

[18+ items across 3-4 formality levels]
```

---

## Engagement Boxes for Academic Modules

```markdown
> 🎓 **Академічна традиція**
>
> [Explain Ukrainian academic writing conventions]

> 📚 **Джерело**
>
> [Reference to Ukrainian academic journals, databases]

> 💡 **Лінгвістичне спостереження**
>
> [Language pattern observation in academic writing]

> ⚠️ **Типова помилка**
>
> [Common error in academic Ukrainian by non-natives]

> 🔍 **Критичне читання**
>
> [Critical reading strategy or question]
```

---

## Advanced Seminar-Style Activities

### Source-Evaluation Activity

**Use for analyzing academic sources, research papers, and scholarly debates:**

```yaml
- type: source-evaluation
  title: "Оцінка джерела: Наукова стаття/Дисертація"
  instruction: "Застосуйте метод критичного аналізу до цього академічного джерела."
  source_text: |
    [Excerpt from academic paper, dissertation abstract, or scholarly debate — 100-200 words]
  source_metadata:
    author: "[Researcher name, institution]"
    date: "[Year of publication]"
    type: "[journal_article/dissertation/conference_paper/monograph]"
    context: "[Academic field, school of thought, funding context]"
  evaluation_criteria:
    - authorship
    - date_and_context
    - intended_audience
    - purpose_and_bias
    - omissions
  guiding_questions:
    - "До якої наукової школи належить автор?"
    - "Який методологічний підхід використовується?"
    - "Яка цільова аудиторія публікації?"
    - "Які альтернативні підходи автор не розглядає?"
  model_evaluation: |
    **1. Авторство:** [Who wrote it, their academic affiliation and school]
    **2. Методологія:** [Research approach, theoretical framework]
    **3. Контекст публікації:** [Journal, institution, funding]
    **4. Упередження:** [Disciplinary, theoretical, or ideological biases]
    **5. Обмеження:** [What the research doesn't address]
```

### Debate Activity

**Use for contested scholarly debates and methodological disputes:**

```yaml
- type: debate
  title: "Дискусія: [Contested Academic Question]"
  instruction: "Проаналізуйте конкуруючі наукові позиції та оцініть їхні методологічні підходи."
  debate_question: "[The contested scholarly question]"
  historical_context: |
    [Background on the academic debate — 50-100 words]
  positions:
    - name: "[Position 1 — e.g., Традиційний підхід]"
      proponents: "[Scholars, institutions]"
      argument: "[Core academic argument]"
      evidence:
        - "[Research evidence]"
        - "[Methodological basis]"
      weaknesses:
        - "[Methodological limitation]"
    - name: "[Position 2 — e.g., Новий підхід]"
      proponents: "[Who holds this view]"
      argument: "[Core argument]"
      evidence:
        - "[Evidence]"
      weaknesses:
        - "[Critique]"
  analysis_tasks:
    - "Які методологічні відмінності між позиціями?"
    - "Як емпіричні дані підтримують кожну позицію?"
    - "Чи можливий методологічний синтез?"
    - "Яку позицію ви вважаєте більш обґрунтованою? Чому?"
  model_analysis: |
    [Balanced evaluation of scholarly positions, focusing on methodological rigor
    and evidence quality rather than ideological preference.]
```

**Example contested questions for academic modules:**
- "Кількісні чи якісні методи: що краще для соціолінгвістики?"
- "Як визначати межі української літературної мови?"
- "Чи існує об'єктивна наукова істина?"

---

## Content Structure Note

### Vocabulary & Activities

**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:
- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

The build system will inject these sections at build time.
**Example `vocabulary/c1-01-academic.yaml`:**

```yaml
items:
- lemma: анотація
  ipa: /ɑnɔˈtɑt͡sʲijɑ/
  translation: abstract
  pos: ім.
  note: науковий термін
- lemma: гіпотеза
  ipa: /ɦipɔˈtɛzɑ/
  translation: hypothesis
  pos: ім.
  note: наукове припущення
```

---

## Module Breakdown: C1.1 & C1.2

### C1.1: Academic Foundation (M01-20)

| Modules | Topic | Focus |
|---------|-------|-------|
| M01-05 | Academic Writing Conventions | Structure, register, impersonal forms |
| M06-10 | Research Abstracts & Summaries | анотація, реферат, огляд |
| M11-15 | Formal Argumentation | теза, аргументи, контраргументи |
| M16-19 | Citation & Referencing | Ukrainian citation traditions |
| M20 | Academic Checkpoint | Comprehensive assessment |

### C1.2: Professional & Social (M21-35)

| Modules | Topic | Focus |
|---------|-------|-------|
| M21-25 | Official Register | офіційно-діловий стиль |
| M26-30 | Professional Correspondence | листування, звіти, протоколи |
| M31-34 | Workplace Communication | наради, переговори, презентації |
| M35 | Professional Checkpoint | Comprehensive assessment |

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/c1-module-template.md`
- **C1 Curriculum Plan:** `docs/l2-uk-en/C1-CURRICULUM-PLAN.md` (M01-35 specifications)
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
