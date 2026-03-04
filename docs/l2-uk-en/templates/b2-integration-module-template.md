# B2 Integration Module Template

**Purpose:** Reference template for B2 integration modules (M96-109: Skills & Capstone Phase)

**Based on:** `b2-module-template.md` — inherits all B2 quality standards

**Related Issue:** [#305](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/305)

<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Стратегії
  - Практика|Вправи
  - Підсумок
  - Потрібно більше практики?
  pedagogy: CBI
  min_word_count: 4000
  required_callouts: []
  description: B2 integration modules teach skills and strategies with authentic materials
-->

---

## Quick Reference Checklist

Before submitting a B2 integration module, verify all items from `b2-module-template.md` PLUS:

### Integration-Specific Requirements

- [ ] **No new grammar/vocabulary:** Integration modules REVIEW only
- [ ] **Authentic materials:** 5+ authentic Ukrainian texts (news, academic, official)
- [ ] **External resources:** Added to `docs/resources/external_resources.yaml` (NOT embedded in module)
- [ ] **C1 preview:** Explicit preparation for next level
- [ ] **Self-assessment:** B2 mastery checklist
- [ ] **Skills focus:** Reading, writing, listening, speaking strategies

---

## Module Types in B2.4

### Type 1: Skills Modules (M96-100)

**M96: Читання академічних текстів (Academic Reading)**

- Focus: Reading strategies for academic texts
- Meta-vocabulary: анотація, висновки, методологія, посилання
- Activities: Analyzing structure, identifying arguments, summarizing

**M97: Написання формальних документів (Formal Writing)**

- Focus: Official and academic writing skills
- Meta-vocabulary: звернення, обґрунтування, резюме, висновок
- Activities: Document structure, register control, argumentation

**M98: Слухання лекцій та доповідей (Lectures & Presentations)**

- Focus: Listening strategies for academic contexts
- Meta-vocabulary: теза, аргумент, контраргумент, ключові тези
- Activities: Note-taking, main points, speaker position

**M99: Усна комунікація: дебати та дискусії**

- Focus: Speaking strategies for debates
- Meta-vocabulary: позиція, заперечення, уточнення, підсумок
- Activities: Argument structure, counterarguments, persuasion

**M100: Інтегровані навички (Integrated Skills)**

- Focus: Combined reading, writing, listening, speaking
- Activities: Multi-skill tasks simulating real-world contexts

**Structure:** CBI with explicit strategy instruction

---

### Type 2: Review Modules (M101-105)

**M101-102: Grammar Review (Passive, Participles, Register)**

- Focus: All B2 grammar reviewed
- TTT structure: Diagnostic → Review → Retest

**M103-104: Vocabulary Review (Phraseology, History)**

- Focus: All B2 vocabulary reviewed
- TTT structure: Diagnostic → Review → Retest

**M105: Integrated Grammar & Vocabulary**

- Focus: Grammar and vocabulary working together
- TTT structure with production tasks

**Structure:** TTT (Test-Teach-Test)

---

### Type 3: Skills Assessment Modules (M106-109)

**M106: Reading Comprehension Assessment**
**M107: Writing Assessment**
**M108: Listening Assessment**
**M109: Speaking Assessment (Self-Guided)**

**Structure:** Task-Based Learning (TBL)

---

## Template Structure: Skills Module (M96-100)

### Frontmatter

```yaml
---
module: b2-XX
title: 'Ukrainian Title — Skills Focus'
phase: 'B2.4 [Skills & Capstone]'
pedagogy: 'CBI' # Content-Based Instruction
register: 'varies' # Skills modules span registers
tags:
  - skills
  - integration
  - [specific-skill]
grammar:
  - 'All B2 grammar (integration)'
objectives:
  - 'Learner can apply [skill] strategies to authentic Ukrainian texts'
  - 'Learner can produce [output] at B2 complexity'
  - 'Learner is prepared for C1 level [skill] challenges'
vocabulary_count: 20 # Lower (meta-language + review)
---
```

### Section 1: Вступ (Introduction) — 300-400 words

```markdown
# [Skills Title in Ukrainian]

> 🎯 **Чому це важливо?**
>
> [Explain why this skill is essential for B2/C1 in Ukrainian]
> [Connect to academic, professional, cultural contexts]
> [Preview strategies to be taught]

## Вступ

[Opening hook explaining skill importance — 100-150 words]

### Стратегії, які ви вивчите

У цьому модулі ви навчитеся:

1. **[Strategy 1]:** [Brief description]
2. **[Strategy 2]:** [Brief description]
3. **[Strategy 3]:** [Brief description]

### Мета-лексика

Ключові терміни для цього навику:

- **[term 1]** — [definition in Ukrainian]
- **[term 2]** — [definition in Ukrainian]
- **[term 3]** — [definition in Ukrainian]

> 💡 **Чи знали ви?**
>
> [Interesting fact about this skill in Ukrainian context]
```

### Section 2: Презентація (Strategy Teaching) — 800-1000 words

```markdown
## Стратегії

### Стратегія 1: [Strategy Name]

**Що це?**
[Explanation in Ukrainian — 50-100 words]

**Навіщо це потрібно?**
[Purpose and benefits — 50-100 words]

**Як це робити?**

1. [Step 1]
2. [Step 2]
3. [Step 3]

**Приклад:**

> [300+ word authentic Ukrainian text demonstrating strategy]
>
> **Аналіз:**
>
> - [Point out strategy application]
> - [Show how strategy reveals meaning]

---

### Стратегія 2: [Strategy Name]

[Same structure as Strategy 1 — 200-300 words]

---

### Стратегія 3: [Strategy Name]

[Same structure — 200-300 words]

> 🌍 **У реальному житті**
>
> [Where to practice this strategy with real Ukrainian materials]
```

### Section 3: Практика (Strategy Application) — 400-500 words

```markdown
## Практика

### Текст 1: [Context]

> [400+ word authentic Ukrainian text]

**Завдання:**

1. Застосуйте [Strategy 1] до цього тексту.
2. Визначте [specific elements].
3. Підсумуйте головну думку в 2-3 реченнях.

### Текст 2: [Different Context]

> [400+ word authentic Ukrainian text — different register]

**Завдання:**

1. Порівняйте регістр цього тексту з попереднім.
2. Застосуйте [Strategy 2].
3. Напишіть критичний коментар (100+ слів).

> ⚠️ **Поширена помилка**
>
> [Common error when applying this strategy and how to avoid it]
```

### Section 4: Продукція (Production) — 300-400 words

```markdown
## Продукція

### Завдання: [Production Task]

[Production prompt requiring skill application — 50-100 words]

**Вимоги:**

- Довжина: 250+ слів
- Регістр: [specified register]
- Використайте: [target strategies]

**Зразок відповіді:**

[Complete 250+ word model answer demonstrating:

- Correct skill application
- Register awareness
- B2-level complexity
- Strategy usage]

### Самооцінка

Чи можу я:

- [ ] Застосовувати [Strategy 1]?
- [ ] Застосовувати [Strategy 2]?
- [ ] Застосовувати [Strategy 3]?
- [ ] Працювати з автентичними українськими текстами?

> 🎯 **Наступний крок: Рівень C1**
>
> [Preview of what C1 will expect for this skill]
```

---

## Template Structure: Review Module (M101-105)

### Frontmatter

```yaml
---
module: b2-XX
title: 'Повторення: [Grammar/Vocabulary Area]'
phase: 'B2.4 [Skills & Capstone]'
pedagogy: 'TTT' # Test-Teach-Test
register: 'varies'
tags:
  - integration
  - review
  - [specific-area]
grammar:
  - 'Integration of all B2 [area]'
objectives:
  - 'Learner can demonstrate mastery of all B2 [area]'
  - 'Learner can apply [area] in integrated contexts'
  - 'Learner is prepared for C1 [area] challenges'
vocabulary_count: 15 # Lower (review only)
---
```

### TTT Structure

```markdown
# Повторення: [Area]

> 🎯 **Чому це важливо?**
>
> [Explain this is comprehensive review — no new content]

## Діагностика

### Тест без підказок

[Diagnostic test covering ALL B2 content in this area — 20-30 items]

**Підрахуйте правильні відповіді:**

- 25-30: Відмінно! Ви готові до C1.
- 18-24: Добре. Повторіть розділи нижче.
- <18: Потрібно більше практики. Прочитайте весь модуль уважно.

---

## Аналіз

### [Area 1]: [Title]

**Ключові правила:**

- [Rule 1]
- [Rule 2]
- [Rule 3]

**Приклади:**

- [Example 1]
- [Example 2]

### [Area 2]: [Title]

[Continue for all B2 areas]

---

## Поглиблення

### Інтегрований текст

> [500+ word passage integrating ALL B2 content in this area]

**Завдання:**

1. Знайдіть усі приклади [structure 1].
2. Визначте [feature] у кожному випадку.
3. Перетворіть [transformation task].

---

## Практика

### Завдання: Написання

Напишіть текст (200+ слів), використовуючи все, що ви вивчили.

**Зразок відповіді:**
[Complete model answer]
```

---

## Template Structure: Assessment Module (M106-109)

### Frontmatter

```yaml
---
module: b2-XX
title: 'Оцінювання: [Skill]'
phase: 'B2.4 [Skills & Capstone]'
pedagogy: 'TBL' # Task-Based Learning
register: 'varies'
tags:
  - assessment
  - [skill]
objectives:
  - 'Learner can demonstrate B2 [skill] proficiency'
  - 'Learner can complete authentic [skill] tasks'
---
```

### Assessment Structure

```markdown
# Оцінювання: [Skill]

> 🎯 **Інструкції**
>
> Це формальне оцінювання ваших навичок [skill] на рівні B2.
> Час: 60 хвилин. Усі завдання обов'язкові.

---

## Завдання 1: [Task Type] — 20 балів

[Task description and materials]

**Критерії оцінювання:**
| Критерій | Опис | Бали |
|----------|------|------|
| [Criterion 1] | [Description] | 5 |
| [Criterion 2] | [Description] | 5 |
| [Criterion 3] | [Description] | 5 |
| [Criterion 4] | [Description] | 5 |

---

## Завдання 2: [Task Type] — 20 балів

[Task description and materials]

---

## Завдання 3: [Task Type] — 20 балів

[Task description and materials]

---

## Результати

**Підрахунок балів:**

- 50-60: Відмінно (B2.2)
- 40-49: Добре (B2.1)
- 30-39: Задовільно (B2 мінімум)
- <30: Потрібно більше практики

**Рекомендації:**

- [Recommendation based on score]
```

---

---

## Content Structure Note

### Vocabulary, Activities & External Resources

**CRITICAL:** Do NOT add `## Vocabulary`, `## Activities`, or `## External Resources` headers. These sections are injected automatically from:

- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`
- `docs/resources/external_resources.yaml`

The build system will inject these sections at build time.

**To add resources for integration modules:**

1. Open `docs/resources/external_resources.yaml`
2. Add entries with the module ID and appropriate metadata

**Recommended resources:**

- Українська правда, Дзеркало тижня, Критика, Тиждень (reading)
- Громадське радіо, Українське радіо, подкасти (listening)
- Мова - ДНК нації, Словники України (writing)
- C1 preparation materials (next level preview)

---

## Activity Requirements

### Activity Format Quick Reference

**CRITICAL:** Use these exact formats for MDX generation to work correctly.

| Activity             | Format                                                                             |
| -------------------- | ---------------------------------------------------------------------------------- |
| **quiz**             | `- [ ] wrong` / `- [x] correct` with optional `> explanation`                      |
| **true-false**       | `- [x] True.` with `> explanation` / `- [ ] False.` with `> explanation`           |
| **fill-in**          | `> [!answer] correct` + `> [!options] a \| b \| c \| d`                            |
| **error-correction** | ALL 4 required: `> [!error]` + `> [!answer]` + `> [!options]` + `> [!explanation]` |
| **match-up**         | Table: `\| Left \| Right \|`                                                       |
| **group-sort**       | `### Category` headers with `- items` underneath                                   |
| **unjumble**         | `> [!answer] Correct sentence here.`                                               |
| **cloze**            | Inline: `{blank\|opt1\|opt2\|answer}`                                              |
| **select**           | Multiple `- [x]` for all correct options                                           |
| **translate**        | Multi-choice: `- [x] Correct translation.` with `> explanation`                    |
| **mark-the-words**   | `*marked*` words in blockquote passage                                             |

---

### Skills Modules (M96-100)

- **12+ activities** focused on strategy application
- Priority: quiz, fill-in, cloze, group-sort
- Include analysis tasks and production

### Review Modules (M101-105)

- **20+ activities** (comprehensive, like checkpoints)
- Cover ALL B2 content in the area
- TTT structure with diagnostic and final test

### Assessment Modules (M106-109)

- **5-8 formal assessment tasks**
- Rubrics for all tasks
- Scoring guide

---

## Common Pitfalls to Avoid

### 1. **Teaching New Content**

- ❌ Problem: Integration modules introduce new grammar/vocabulary
- ✅ Solution: Integration modules REVIEW only. All teaching happens in M01-95.

### 2. **Missing External Resources**

- ❌ Problem: No resources in `docs/resources/external_resources.yaml`
- ✅ Solution: Add 15+ resources to `external_resources.yaml` with module ID

### 3. **No C1 Preview**

- ❌ Problem: Modules end abruptly without C1 preparation
- ✅ Solution: Every integration module includes "Наступний крок: C1" section

### 4. **Skills Modules Too Grammar-Heavy**

- ❌ Problem: Teaching grammar instead of reading/writing/listening strategies
- ✅ Solution: Focus on HOW to read/write/listen, not grammar rules

### 5. **Missing Model Answers**

- ❌ Problem: Production tasks without examples
- ✅ Solution: ALL writing tasks include complete model answers

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/b2-module-template.md`
- **B2 Curriculum Plan:** `docs/l2-uk-en/B2-CURRICULUM-PLAN.md` (M132-145 Skills & Capstone)
- **B1 Integration Template:** `docs/l2-uk-en/templates/b1-integration-module-template.md`
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-29
**Template Version:** 1.1

**Changelog:**

- v1.1 (2025-12-29): Updated module range M132-145 (was M96-110)

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
