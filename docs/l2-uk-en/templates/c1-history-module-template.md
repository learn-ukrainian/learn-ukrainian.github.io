# C1 History Module Template

**Purpose:** Reference template for ISTORIO advanced historical analysis modules (M01-135: Historiography, Primary Sources, Imperial Mechanisms)

**Based on:** `c1-module-template.md` — inherits all C1 quality standards

**Related Plan:** `docs/l2-uk-en/ISTORIO-CURRICULUM-PLAN.md`

**Prerequisite:** HIST Track (for factual foundation)

---

## ⚠️ BEFORE WRITING: Research Historiographical Content First!

**CRITICAL:** ISTORIO is NOT about historical facts (that's HIST). It's about **how we know history** — sources, methods, interpretations, contested narratives. This requires academic-level research.

### Research Strategy

**Step 1: Find Academic Sources**
```
WebSearch: "[topic] historiography Ukrainian"
WebSearch: "[historian name] праці"
WebSearch: "[primary source name] аналіз джерела"
```

**Step 2: Verify with WebFetch**
```
WebFetch: http://resource.history.org.ua/... (Institute of History)
WebFetch: http://nbuv.gov.ua/... (National Library)
```

**Step 3: Primary Source Verification**
For any primary source excerpts:
```
WebSearch: "[source title] повний текст"
WebSearch: "[source title] site:litopys.org.ua"
```

### Key Academic Resources (PRIORITIZE THESE)

| Resource | URL | Use For |
|----------|-----|---------|
| **Litopys.org.ua** | [litopys.org.ua](https://litopys.org.ua) | Primary sources: chronicles, universals, legal documents |
| **Institute of History NANU** | [history.org.ua](https://history.org.ua) | Scholarly articles, historiographical reviews |
| **National Library** | [nbuv.gov.ua](https://nbuv.gov.ua) | Academic journals, dissertations |
| **Hrushevsky Digital** | [hrushevsky.nbuv.gov.ua](https://hrushevsky.nbuv.gov.ua) | Hrushevsky's complete works |
| **ЕСУ** | [esu.com.ua](https://esu.com.ua) | Biographical and conceptual articles |
| **UINP** | [memory.gov.ua](https://memory.gov.ua) | 20th century, decolonization |

> ⚠️ **Wikipedia Warning:** Ukrainian Wikipedia (uk.wikipedia.org) is contested territory subject to Russian information warfare. **For historiography, NEVER rely on Wikipedia.** Use .gov.ua and academic sources only.

### Reference Works (Use, Don't Copy!)

| Source | Use For |
|--------|---------|
| Грушевський М. "Історія України-Руси" | Foundational historiography, methodology |
| Яковенко Н. "Нарис історії середньовічної та ранньомодерної України" | Modern Ukrainian historiography model |
| Plokhy S. "The Gates of Europe" | Accessible academic synthesis |
| Subtelny O. "Ukraine: A History" | Diaspora historiographical perspective |

**⚠️ ANTI-PLAGIARISM RULES:**
1. **SYNTHESIZE historiographical debates** — don't copy conclusions
2. **Quote primary sources properly** — use `> [!quote]` with full attribution
3. **Distinguish perspectives** — Ukrainian vs. Russian vs. Western historiography
4. **Add analytical value** — explain WHY interpretations differ, not just WHAT they say

### Anti-Hallucination Rules

1. **NEVER invent historiographical debates** — verify which historians actually disagree
2. **NEVER generate primary source text from memory** — always verify from litopys.org.ua or similar
3. **NEVER attribute views to historians without verification** — check their actual arguments
4. **NEVER invent dating or authorship debates** — these are well-documented
5. **When in doubt, mark as [NEEDS VERIFICATION]** — flag for review

> 💡 **Tip:** ISTORIO teaches how to analyze history, not history itself. Focus on methodology, source criticism, and competing narratives.

---

<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст
  - Аналіз джерела|Історіографічний огляд
  - Критика|Методологія
  - Підсумок
  - Потрібно більше практики?
  pedagogy: CLIL
  min_word_count: 5000
  required_callouts: []
  description: ISTORIO modules focus on historiographical analysis and primary sources
-->

---

## Quick Reference Checklist

Before submitting a ISTORIO module, verify all items from `c1-module-template.md` PLUS:

### History Analysis-Specific Requirements

- [ ] **CLIL pedagogy:** Content and Language Integrated Learning at academic level
- [ ] **Primary sources (≥1):** Include excerpt with glosses for archaic forms using `[!quote]` callouts
- [ ] **Source criticism:** Every primary source includes authorship, bias, purpose analysis
- [ ] **Historiographical context:** Compare Ukrainian, Russian, Western interpretations
- [ ] **Activity count:** 3-9 seminar-style activities (reading + essay-response + critical-analysis)
- [ ] **Academic vocabulary:** 30+ historiographical terms per module
- [ ] **Essay activity:** 250-500 word analytical essay in YAML — NO essay section in markdown
- [ ] **NO factual drills:** This is NOT HIST — no quiz on dates/events

---

## Naturalness Quality Checklist

**Run this check during Stage 4 (Review & Fix) on prose activities.**

Before finalizing the module, verify prose activities achieve:

- [ ] **Subject consistency** - Clear subjects maintained throughout passages
- [ ] **Discourse markers** - At least 2-3 connectors per 10-sentence passage
- [ ] **Topic coherence** - All sentences contribute to unified analytical argument
- [ ] **No template repetition** - Varied sentence structures across activities
- [ ] **Academic register** - Appropriate historiographical vocabulary
- [ ] **Natural transitions** - Avoid robotic patterns

**Target score:** 8/10 for content modules, 7/10 for checkpoints

---

## Module Structure (Historiography-Specific)

### 1. Frontmatter

```yaml
---
module: istorio-XX
title: "[Historiographical Topic]: Ukrainian Title"
phase: "C1H.X [Phase Name]"
pedagogy: "CLIL"
register: "науковий"  # Academic register
tags:
  - historiography
  - [primary-sources, methodology, interethnic, imperial-mechanisms]
  - [era if applicable]
grammar:
  - "Academic discourse markers"
  - "Source citation conventions"
vocabulary_focus:
  - "Historiographical terminology"
  - "Source criticism vocabulary"
---
```

### 2. Content Structure

#### Section 1: Methodological Introduction — 400-500 words

```markdown
# [Historiographical Topic]

> 🎯 **Чому це важливо?**
>
> [Explain why this method/debate/source matters for understanding Ukrainian history]
> [How this develops analytical skills beyond HIST]

## Методологічний вступ

[300-400 words introducing the historiographical concept, method, or debate]

**Ключові питання:**
1. [Question about sources/methods]
2. [Question about interpretation]
3. [Question about competing narratives]

> 📚 **Історіографічний контекст**
>
> [Brief overview of how this topic has been treated by different historiographical traditions]
```

#### Section 2: Source Analysis / Historiographical Review — 800-1000 words

```markdown
## Аналіз джерела / Історіографічний огляд

### Джерело: [Source Title]

**Контекст створення:**
[When, where, why was this source created — 100-150 words]

**Оригінал (з глосами):**

> [Primary source excerpt in original Ukrainian/Church Slavonic — 200-300 words]
>
> *— Джерело: [Full attribution]*

**Глоси:**
| Архаїзм | Сучасне значення |
|---------|------------------|
| [archaic word] | [modern equivalent] |

### Критика джерела

**Авторство:** [Who wrote it, what can we verify]
**Мета:** [Why was it written, for whom]
**Упередження:** [What biases can we detect]
**Достовірність:** [How reliable for historical reconstruction]

> ⚠️ **Методологічна примітка**
>
> [Key methodological point about using this type of source]
```

#### Section 3: Comparative Historiography — 400-500 words

```markdown
## Порівняльна історіографія

### Українська інтерпретація

[How Ukrainian historians (Hrushevsky, modern scholars) interpret this topic — 150-200 words]

### Російська/імперська інтерпретація

[How Russian/imperial historiography frames this — 150-200 words]

> ⚠️ **Деколонізація**
>
> [Why the imperial narrative is problematic, based on source evidence]

### Західна історіографія

[How Western scholars approach this — 100-150 words]

### Синтез

[What can we conclude from comparing these perspectives — 100-150 words]
```

#### Section 4: Application — 300-400 words

```markdown
## Застосування методу

### Практика критики джерел

[Exercise applying source criticism method to a new excerpt]

### Питання для аналізу

1. [Critical question about the source]
2. [Question comparing interpretations]
3. [Question about applicability to other sources]

> 💡 **Методологічний інсайт**
>
> [Transferable analytical skill from this module]
```

---

## Activity Format (Seminar-Style Only)

**CRITICAL:** ISTORIO uses ONLY seminar-style activities per config.py.

### Required Activity Types

```yaml
# In activities/{slug}.yaml

- type: reading
  id: istorio-XX-reading-01
  title: "Аналіз первинного джерела"
  resource:
    type: primary_source
    url: "https://litopys.org.ua/..."
    title: "[Source Title]"
  tasks:
    - "Визначте регістр та стиль джерела. Наведіть приклади."
    - "Знайдіть три приклади архаїчної лексики. Яке їх сучасне значення?"
    - "Які упередження автора можна виявити з тексту?"

- type: essay-response
  id: istorio-XX-essay-01
  title: "Історіографічний аналіз"
  prompt: |
    Напишіть порівняльний аналіз (250-500 слів):
    "[Topic]: Українська та російська інтерпретації"

    Вимоги:
    - Використайте академічну лексику модуля
    - Цитуйте первинне джерело
    - Обґрунтуйте, чому одна інтерпретація переконливіша
  rubric:
    - criterion: Академічна мова
      weight: 40
      description: Використання історіографічної термінології
    - criterion: Критика джерел
      weight: 30
      description: Аналіз достовірності та упереджень
    - criterion: Порівняльний аналіз
      weight: 20
      description: Логічне порівняння інтерпретацій
    - criterion: Аргументація
      weight: 10
      description: Обґрунтованість висновків

- type: critical-analysis
  id: istorio-XX-analysis-01
  title: "Методологічна рефлексія"
  questions:
    - "Як застосувати цей метод критики джерел до інших періодів?"
    - "Які обмеження має цей тип джерела?"
    - "Як сучасна деколонізація змінює інтерпретацію цього періоду?"

- type: source-evaluation
  title: "Оцінка джерела: [Source Name]"
  source_text: |
    [Historical source excerpt to evaluate]
  source_metadata:
    author: "[Author name or 'Anonymous']"
    date: "[Date or period]"
    type: "[chronicle/memoir/official document/propaganda/academic]"
    context: "[Historical context of creation]"
  evaluation_criteria:
    - authorship
    - date_and_context
    - intended_audience
    - purpose_and_bias
    - omissions
  guiding_questions:
    - "Яким був політичний контекст створення цього джерела?"
    - "Які упередження автора можна виявити?"
    - "Що це джерело замовчує?"
  model_evaluation: |
    [Model answer demonstrating proper source criticism methodology]

- type: debate
  title: "Дискусія: [Contested Question]"
  debate_question: "[The contested historiographical question]"
  historical_context: "[Background needed to understand the debate]"
  positions:
    - name: "[Position 1 name]"
      proponents: "[Historians/schools]"
      argument: "[Core argument]"
      evidence:
        - "[Key evidence 1]"
        - "[Key evidence 2]"
      weaknesses:
        - "[Critique of this position]"
    - name: "[Position 2 name]"
      proponents: "[Historians/schools]"
      argument: "[Core argument]"
      evidence:
        - "[Key evidence 1]"
      weaknesses:
        - "[Critique of this position]"
  analysis_tasks:
    - "Визначте найсильніший аргумент кожної позиції."
    - "Чи є спільні точки між позиціями?"
    - "Яку позицію ви вважаєте переконливішою? Чому?"
  model_analysis: |
    [Model answer showing balanced evaluation of positions]
```

### Additional ISTORIO Activity Types

In addition to the required types above, ISTORIO supports:

- **`source-evaluation`**: Structured 5-question method (Хто? Коли? Для кого? Чому? Що опущено?) applied to primary/secondary sources. Use for historiographical methodology training.

- **`debate`**: Presents 2-4 competing historiographical positions on a contested question. Learners analyze arguments, evidence, and weaknesses. Use for complex interpretive questions (e.g., "Was Pereiaslav a reunification or a military alliance?").

- **`comparative-study`**: Compare historians, schools, or interpretations across criteria. Already supported in base schema.

### Forbidden Activity Types

Per config.py, ISTORIO does NOT use:
- match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words
- quiz (unless testing methodology concepts, not factual recall)

---

## Engagement Boxes for Historiography Modules

```markdown
> 📚 **Історіографічний контекст**
>
> [Overview of how topic has been treated by different traditions]

> 📜 **Первинне джерело**
>
> [Key excerpt with attribution]

> ⚠️ **Методологічна примітка**
>
> [Important point about source criticism or interpretation]

> 🔍 **Критика джерела**
>
> [Analysis of bias, purpose, reliability]

> ⚠️ **Деколонізація**
>
> [Challenge imperial historiographical narratives]

> 💡 **Методологічний інсайт**
>
> [Transferable analytical skill]
```

---

## Content Structure Note

### Vocabulary & Activities

**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:
- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/c1-module-template.md`
- **ISTORIO Curriculum Plan:** `docs/l2-uk-en/ISTORIO-CURRICULUM-PLAN.md`
- **B2 History Template:** `docs/l2-uk-en/templates/history-module-template.md` (for narrative approach comparison)
- **Primary Sources:** litopys.org.ua

---

**Last Updated:** 2026-01-24
**Template Version:** 1.0
