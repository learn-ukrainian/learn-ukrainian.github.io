# C2 Literary Module Template

**Purpose:** Reference template for C2 literary mastery modules (M26-45: Literary Theory, Creative Writing, Translation, Scholar-Level Analysis)

**Based on:** `c2-module-template.md` — inherits all C2 quality standards

**Related Issue:** [#307](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/307)

<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Літературний аналіз
  - Підсумок
  - Потрібно більше практики?
  pedagogy: Native
  min_word_count: 5000
  required_callouts: []
  description: C2 literary modules achieve native literary analysis
-->

---

## Quick Reference Checklist

Before submitting a C2 literary module, verify all items from `c2-module-template.md` PLUS:

### Literary-Specific Requirements

- [ ] **Scholar-level analysis:** Literary theory and criticism, not surface reading
- [ ] **Original production:** Poetry, prose, or literary essay — YAML only (`essay-response` activity)
- [ ] **Translation component:** Literary translation theory or practice
- [ ] **Ukrainian critical terminology:** All analysis in Ukrainian
- [ ] **Canon awareness:** Connect to Ukrainian literary tradition
- [ ] **Meta-linguistic commentary:** Explain stylistic and creative choices
- [ ] **NO CONVERSATIONAL DIALOGS:** C2 literary modules are ANALYTICAL. Do NOT include tourist dialogs or conversational scenarios. If analyzing dramatic dialogue, quote and analyze the text—don't simulate conversations.

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

#### Section 3: Creative Production (YAML Only)

**CRITICAL:** Creative production activities are defined ONLY in `activities/{slug}.yaml` as `type: essay-response`.

**DO NOT include creative task sections with model answers in markdown.** This causes:
- Content redundancy (essay prompt + model answer duplicated)
- Word count inflation (~700 words added to content)
- QA confusion (auditing both locations)

**Per config.py:** Check C2 essay_min_words and essay_max_words for word limits.

**Creative activity example in YAML:**

```yaml
- type: essay-response
  id: c2-XX-creative-01
  title: 'Творче завдання: [Poetry/Prose/Essay]'
  prompt: |
    Тип: [Specific form — сонет, оповідання, критичне есе]

    Завдання: [Detailed creative task description]

    Вимоги:
    1. [Formal requirement]
    2. [Thematic requirement]
    3. [Stylistic requirement]
  rubric:
    - criterion: Форма
      weight: 20
      description: Досконале володіння обраною формою
    - criterion: Стиль
      weight: 20
      description: Індивідуальний голос, багата образність
    - criterion: Техніка
      weight: 20
      description: Свідоме використання літературних засобів
    - criterion: Оригінальність
      weight: 20
      description: Творчий внесок, не імітація
    - criterion: Мова
      weight: 20
      description: Бездоганна граматика, багата лексика
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

### CRITICAL: Language Practice, Not Content Testing

<critical>

**Activities test LANGUAGE SKILLS, not literary theory recall.**

The lesson teaches both Ukrainian AND literary mastery. Activities practice only Ukrainian using literary content as context.

**✅ CORRECT:** "Згідно з текстом, як автор визначає поняття фокалізації?" (requires reading Ukrainian)
**❌ WRONG:** "Що таке фокалізація?" (tests definition recall, not reading comprehension)

**Key Test:** Can the learner answer without reading the Ukrainian analysis text? If yes, rewrite.

| Component | Purpose |
|-----------|---------|
| **Lesson Content** | Teaches BOTH Ukrainian language AND literary theory/criticism |
| **Activities** | Practice ONLY Ukrainian language skills using literary content as context |

**Activity Types and Their Language Focus:**
- **quiz**: Test reading comprehension of theoretical text — "Згідно з текстом модуля..."
- **fill-in**: Test literary terminology/collocations in context
- **match-up**: Test vocabulary — Ukrainian terms ↔ Ukrainian definitions
- **cloze**: Test vocabulary in literary analysis context
- **group-sort**: Test categorization using module vocabulary
- **mark-the-words**: Test grammar recognition in literary text
- **error-correction**: Test grammar, NOT theoretical errors

</critical>

---

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/c2-26-theory.yaml`:**

```yaml
- type: quiz
  title: Літературознавчий аналіз
  items:
    - question: Що таке "фокалізація" у наратології?
      options:
        - text: Точка зору оповіді
          correct: true
        - text: Головний герой
          correct: false

- type: essay-response
  title: Поетична майстерня
  instruction: Напишіть сонет на тему природи.
  model_answer: (Sample sonnet...)
```

---

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

## Advanced Seminar-Style Activities

### Source-Evaluation Activity

**Use for analyzing literary theory sources and critical schools:**

```yaml
- type: source-evaluation
  title: "Оцінка джерела: Літературознавча стаття/Критичний маніфест"
  instruction: "Застосуйте метод критичного аналізу до цього теоретичного джерела."
  source_text: |
    [Excerpt from literary theory, critical manifesto, or scholarly article — 100-200 words]
  source_metadata:
    author: "[Theorist/critic name]"
    date: "[Year of publication]"
    type: "[theory/manifesto/criticism/essay]"
    context: "[Critical school, intellectual movement, historical moment]"
  evaluation_criteria:
    - authorship
    - date_and_context
    - intended_audience
    - purpose_and_bias
    - omissions
  guiding_questions:
    - "До якої критичної школи належить автор? (формалізм, структуралізм, постколоніалізм...)"
    - "Який ідейний контекст теорії?"
    - "Які тексти/автори підтверджують або спростовують цю теорію?"
    - "Які альтернативні підходи автор ігнорує?"
  model_evaluation: |
    **1. Авторство:** [Who is the theorist, their critical school]
    **2. Теоретичний контекст:** [Intellectual movement, predecessors]
    **3. Методологія:** [How the theory approaches literature]
    **4. Упередження:** [Theoretical blind spots, ideological assumptions]
    **5. Застосування:** [What this theory illuminates and what it misses]
```

### Debate Activity

**Use for contested critical positions and theoretical disputes:**

```yaml
- type: debate
  title: "Дискусія: [Contested Theoretical Question]"
  instruction: "Проаналізуйте конкуруючі теоретичні позиції та оцініть їхню пояснювальну силу."
  debate_question: "[The contested question in literary theory]"
  historical_context: |
    [Background on the theoretical debate — 50-100 words]
  positions:
    - name: "[Position 1 — e.g., Формалістична позиція]"
      proponents: "[Theorists, schools]"
      argument: "[Core theoretical argument]"
      evidence:
        - "[Textual evidence — how texts support this reading]"
        - "[Theoretical argument]"
      weaknesses:
        - "[Theoretical limitation]"
    - name: "[Position 2 — e.g., Постколоніальна позиція]"
      proponents: "[Who holds this view]"
      argument: "[Core argument]"
      evidence:
        - "[Evidence]"
      weaknesses:
        - "[Critique]"
    - name: "[Position 3 — e.g., Феміністична критика]"
      proponents: "[Scholars]"
      argument: "[Their reading]"
      evidence:
        - "[Evidence]"
      weaknesses:
        - "[Limitation]"
  analysis_tasks:
    - "Які методологічні припущення кожної позиції?"
    - "Як кожен підхід читає конкретний текст по-різному?"
    - "Чи можливий методологічний синтез?"
    - "Яку позицію ви вважаєте найбільш продуктивною? Чому?"
  model_analysis: |
    [Balanced evaluation of theoretical positions, demonstrating how different
    methodologies produce different readings of the same text. C2-level analysis
    should show sophisticated understanding of critical theory.]
```

**Example contested questions for C2 literary:**
- "Чи смерть автора справді звільняє текст?"
- "Як деколонізувати канон: виключати чи перечитувати?"
- "Формалізм vs. культурні студії: текст чи контекст?"
- "Чи можлива феміністична критика класиків-чоловіків?"

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

---

## Content Structure Note

### Vocabulary & Activities

**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:
- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

The build system will inject these sections at build time.
**Example `vocabulary/c2-26-theory.yaml`:**

```yaml
items:
- lemma: наратологія
  ipa: /nɑrɑtɔˈlɔɦʲijɑ/
  translation: narratology
  pos: ім.
  note: наука про оповідь
- lemma: фокалізація
  ipa: /fɔkɑlʲiˈzɑt͡sʲijɑ/
  translation: focalization
  pos: ім.
  note: точка зору оповіді
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
