# C2 Style Module Template

**Purpose:** Reference template for C2 stylistic perfection modules (M01-25: All 7 Functional Styles, Style Transformation, Individual Voice Development)

**Based on:** `c2-module-template.md` — inherits all C2 quality standards

**Related Issue:** [#307](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/307)


<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Стилістичний аналіз
  - Підсумок
  - Потрібно більше практики?
  pedagogy: Native
  min_word_count: 2500
  required_callouts: []
  description: C2 style modules achieve stylistic perfection
-->

---

## Quick Reference Checklist

Before submitting a C2 style module, verify all items from `c2-module-template.md` PLUS:

### Style-Specific Requirements
- [ ] **Creative Production pedagogy:** Focus on creating, not just analyzing
- [ ] **7 functional styles:** Module covers or references appropriate styles
- [ ] **Style transformation:** Demonstrate shifting between registers
- [ ] **Euphonic mastery:** All euphonic alternations correctly applied
- [ ] **Individual voice:** Encourage development of personal style
- [ ] **Model Answers:** ALL creative tasks include gold standard examples
- [ ] **Native-level complexity:** No simplification

---

## Module Types in C2.1

### Functional Styles (M01-09)

| Modules | Focus | Style |
|---------|-------|-------|
| M01 | C1 Bridge & Assessment | Diagnostic |
| M02 | Милозвучність Complete | Euphony |
| M03 | Науковий стиль Mastery | Academic/Scientific |
| M04 | Офіційний стиль Mastery | Official/Legal |
| M05 | Публіцистичний стиль | Journalistic |
| M06 | Художній стиль | Literary |
| M07 | Розмовний стиль | Colloquial |
| M08 | Релігійний стиль | Religious/Liturgical |
| M09 | Епістолярний стиль | Epistolary |

### Style Transformation (M10-16)

| Modules | Focus | Skills |
|---------|-------|--------|
| M10-11 | Style Transformation | Academic → Popular, Official → Journalistic |
| M12-13 | Lexical & Syntactic Stylistics | Word choice, sentence variety |
| M14-15 | Individual Voice | Personal style development |
| M16 | Text Coherence | Seamless flow |

### Advanced Stylistics (M21-25)

| Modules | Focus | Skills |
|---------|-------|--------|
| M21 | Stylistic Devices Mastery | Metaphor, metonymy, synecdoche |
| M22 | Rhythm & Prosody | Prose rhythm control |
| M23 | Intertextuality | Allusion, quotation, parody |
| M24 | Style Blending | Hybrid registers |
| M25 | C2.1 Final Checkpoint | Complete stylistic mastery |


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

**See:** `claude_extensions/stages/stage-4-review-fix.md` Section 9 for detailed naturalness criteria.

**For batch scanning:** Use `/scan-naturalness {level} {start} {end}` to scan completed modules.

---

## Module Structure (Style-Specific)

### 1. Frontmatter

```yaml
---
module: c2-0XX
title: "[Style Name]: Ukrainian Title"
phase: "C2.1 [Stylistic Perfection]"
pedagogy: "Creative Production"
register: "[target style]"  # науковий, офіційний, публіцистичний, художній, розмовний, релігійний, епістолярний
style_focus: "[nuance]"  # formal, ironic, archaic, euphonic, etc.
tags:
  - stylistic
  - [specific-style]
  - [transformation or production]
grammar:
  - "Style-specific grammatical features"
  - "Register markers and conventions"
vocabulary_focus:
  - "Стилістична термінологія"
  - "Регістрова лексика"
---
```

### 2. Style Content Structure

#### Section 1: Style Presentation — 400-500 words

```markdown
# [Style Name]: Майстерність

> 🎯 **Чому це важливо?**
>
> [Explain the style's role in Ukrainian communication]
> [Where native speakers use this style]
> [Why C2 learners must master this style]

## Характеристика стилю

### Сфера використання

[Where this style is used — 100-150 words]

### Ключові ознаки

| Аспект | Характеристика | Приклад |
|--------|----------------|---------|
| Лексика | [Features] | [Example] |
| Синтаксис | [Features] | [Example] |
| Морфологія | [Features] | [Example] |
| Тон | [Features] | [Example] |

> 💡 **Чи знали ви?**
>
> [Interesting fact about this style in Ukrainian culture]
```

#### Section 2: Exemplar Texts — 600-1000 words

```markdown
## Зразкові тексти

### Текст 1: Класичний приклад

**Контекст:**
[Context about text type, author, purpose]

> [600-1000 word exemplar text in target style]

**Стилістичний аналіз:**
- Лексика: [Analysis of vocabulary choices]
- Синтаксис: [Analysis of sentence structures]
- Тон: [Tone characteristics]
- Стилістичні засоби: [Devices used]

---

### Текст 2: Сучасний приклад

**Контекст:**
[Modern context for the style]

> [400-600 word modern example]

**Аналіз відмінностей:**
[How modern usage differs from classic — 100-150 words]

> 📚 **Еволюція стилю**
>
> [How this style has changed over time]
```

#### Section 3: Style Production — 400-600 words

```markdown
## Творче завдання

### Завдання 1: Написання у стилі

**Завдання:**
Напишіть текст (250+ слів) у [target style] на тему [topic].

**Вимоги:**
1. Використовуйте характерні лексичні маркери
2. Дотримуйтесь синтаксичних норм стилю
3. Витримайте відповідний тон
4. Використайте мінімум 5 стилістичних засобів

**Зразок відповіді (Model Answer):**

> [Complete 250+ word model answer demonstrating:
> - Perfect register control
> - Appropriate vocabulary
> - Correct syntax
> - Native-like fluency]

**Коментар автора:**
> [100+ word commentary explaining stylistic choices made]

---

### Завдання 2: Трансформація

**Вихідний текст ([source style]):**
> [150-200 word text in different style]

**Завдання:**
Трансформуйте текст у [target style], зберігаючи зміст.

**Зразок відповіді:**

> [150-200 word transformation showing style shift]

**Аналіз змін:**
| Аспект | Оригінал | Трансформація |
|--------|----------|---------------|
| Лексика | [Source] | [Target] |
| Синтаксис | [Source] | [Target] |
| Тон | [Source] | [Target] |
```

#### Section 4: Meta-linguistic Analysis — 300-400 words

```markdown
## Метамовний аналіз

### Як українська реалізує цей стиль

[Discussion of how Ukrainian creates this style — 150-200 words]

**Порівняння з іншими мовами:**
- Англійська: [Comparison]
- Інші слов'янські: [Comparison]

### Стиль у культурному контексті

[Cultural context for this style — 100-150 words]

> 🎨 **Стилістична нюансировка**
>
> [Subtle distinctions within this style]

> 🔍 **Метамовна свідомість**
>
> [How native speakers think about this style]
```

---

## Style-Specific Activities

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/c2-01-style-mastery.yaml`:**

```yaml
- type: quiz
  title: Визначення стилю
  items:
    - question: Визначте стиль: "Згідно з пунктом 5.2 Угоди..."
      options:
        - text: Офіційно-діловий
          correct: true
        - text: Науковий
          correct: false

- type: essay-response
  title: Стилістична трансформація
  prompt: "Трансформуйте речення в офіційний стиль: 'Ми домовились, що він прийде завтра.'"
  model_answer: "Сторонами досягнуто домовленості про зустріч."
```

---

### Style Recognition

```markdown
## quiz: Визначення стилю

1. "Згідно з пунктом 5.2 Угоди, Сторона зобов'язується..."
   - [ ] Науковий
   - [x] Офіційно-діловий
   - [ ] Публіцистичний
   - [ ] Розмовний
   > Фіксовані формули та посилання на документи — ознаки офіційного стилю.

2. "Отже, дослідження показало кореляцію між показниками X та Y..."
   - [x] Науковий
   - [ ] Офіційно-діловий
   - [ ] Художній
   - [ ] Розмовний
   > Термінологія, безособові конструкції — ознаки наукового стилю.

[12+ style identification questions]
```

### Style Transformation

```markdown
## transform: Стилістична трансформація

Трансформуйте речення з розмовного стилю в офіційний:

1. "Ми домовились, що він прийде завтра і все пояснить."
   > [!answer] Сторонами досягнуто домовленості про проведення зустрічі наступного дня з метою надання роз'яснень.
   > [!explanation] Зміни: "домовились" → "досягнуто домовленості", "він прийде" → "проведення зустрічі", "все пояснить" → "надання роз'яснень".

2. "Шеф сказав, що треба все переробити."
   > [!answer] Керівництвом прийнято рішення про необхідність внесення змін.
   > [!explanation] Безособова конструкція замість прямого мовлення.

[10+ transformation items]
```

### Stylistic Devices

```markdown
## mark-the-words: Стилістичні маркери

Відзначте всі стилістичні маркери [target style] у тексті:

> [400-500 word passage with markable style markers]

[!markable] [list of style markers to identify]
```

### Euphonic Correction

```markdown
## error-correction: Милозвучність

1. Вона в Україні живе уже п'ять років.
   > [!error] в Україні
   > [!answer] в Україні → в Україні (або: у вона)
   > [!options] в Україні | в Україна | в Україну | у Вкраїні
   > [!explanation] Після приголосного перед голосним уживається "в".

[12+ euphonic correction items]
```

### Voice Development

```markdown
## production: Індивідуальний голос

**Завдання:**
Напишіть есе (300+ слів) на тему "[topic]", свідомо розвиваючи свій індивідуальний авторський голос.

**Після написання:**
1. Проаналізуйте свої лексичні вподобання
2. Визначте характерні синтаксичні патерни
3. Опишіть свій авторський тон

**Зразок відповіді:**

> [Complete 300+ word model answer with distinctive voice]

**Самоаналіз автора:**
> [100+ word self-analysis of voice choices]
```

---

## Engagement Boxes for Style Modules

```markdown
> 💡 **Експертна перспектива**
>
> [Expert-level insight about style usage]

> 📚 **Літературний майстер-клас**
>
> [How Ukrainian masters use this style]

> 🎨 **Стилістична нюансировка**
>
> [Subtle distinction between style variants]

> ⚖️ **Порівняння стилів**
>
> [Same content in 3+ styles]

> 🔍 **Метамовна свідомість**
>
> [How natives think about this style]

> 🗣️ **Регіональна варіація**
>
> [Regional differences in style usage]

> 🎭 **Стилістичний ефект**
>
> [What effect this style creates]
```

---

---

## Content Structure Note

### Vocabulary & Activities
**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:
- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

The build system will inject these sections at build time.
**Example `vocabulary/c2-01-style-mastery.yaml`:**

```yaml
items:
- lemma: регістр
  ipa: /rɛˈɦʲistr/
  translation: register
  pos: ім.
  note: функціональний стиль
- lemma: тон
  ipa: /tɔn/
  translation: tone
  pos: ім.
  note: емоційне забарвлення
```

---

## Common Pitfalls to Avoid

### 1. **Style Confusion**
- ❌ Problem: Mixing style markers inappropriately
- ✅ Solution: Maintain consistent register throughout

### 2. **Missing Euphony**
- ❌ Problem: Ignoring у/в, і/й, з/зі/із alternations
- ✅ Solution: Apply all euphonic rules systematically

### 3. **No Model Answers**
- ❌ Problem: Creative tasks without examples
- ✅ Solution: ALL production tasks include gold standard Model Answer

### 4. **Shallow Analysis**
- ❌ Problem: "This is formal style" without explaining WHY
- ✅ Solution: Analyze specific linguistic features that create the style

### 5. **No Voice Development**
- ❌ Problem: Only copying styles, not developing personal voice
- ✅ Solution: Include self-analysis and voice development activities

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/c2-module-template.md`
- **C2 Curriculum Plan:** `docs/l2-uk-en/C2-CURRICULUM-PLAN.md` (M01-25 specifications)
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
