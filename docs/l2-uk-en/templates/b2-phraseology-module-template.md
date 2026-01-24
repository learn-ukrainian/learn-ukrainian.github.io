# B2 Phraseology Module Template

**Purpose:** Reference template for B2 phraseology modules (M41-70: Idioms, Proverbs, Sayings, Synonyms, Collocations)

**Based on:** `b2-module-template.md` — inherits all B2 quality standards

**Related Issue:** [#305](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/305)


<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Фразеологізми
  - Вживання у контексті
  - Підсумок
  - Потрібно більше практики?
  pedagogy: CBI
  min_word_count: 1750
  required_callouts: []
  description: B2 phraseology uses CBI with semantic categories and cultural context
-->

---

## Quick Reference Checklist

Before submitting a B2 phraseology module, verify all items from `b2-module-template.md` PLUS:

### Phraseology-Specific Requirements

- [ ] **CBI pedagogy:** Content-Based Instruction with Narrative Arc (NOT TTT)
- [ ] **Idioms in context:** 15-20 phraseological units embedded in narratives
- [ ] **Semantic categories:** Organize by meaning (somatic, animal, color, etc.)
- [ ] **Usage register:** Show where each expression is appropriate
- [ ] **Cultural origin:** Explain cultural/historical background where relevant
- [ ] **Synonym nuance:** Distinguish between near-synonyms with examples


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

## Module Structure (Phraseology-Specific)

### 1. Frontmatter

```yaml
---
module: b2-XX
title: 'Ukrainian Title — Phraseology Category'
phase: 'B2.2 [Phraseology & Synonymy]'
pedagogy: 'CBI' # Content-Based Instruction
register: 'varies' # Phraseology spans registers
tags:
  - phraseology
  - [category: somatic, animal, color, proverbs, synonyms, collocations]
grammar:
  - 'Fixed expressions'
  - 'Idiom structure and variation'
vocabulary_focus:
  - 'Phraseological units'
  - 'Semantic nuance'
---
```

### 2. Narrative Arc Structure

#### Section 1: Hook with Idioms — 200-300 words

```markdown
# [Phraseology Category Title]

> 🎯 **Чому це важливо?**
>
> [Explain why idioms/proverbs are essential for B2 fluency]
> [Connect to cultural understanding]
> [Set expectations for 15-20 expressions]

## Вступ

[Short narrative using 3-4 target idioms naturally — reader discovers them in context]

Марія **як у воду дивилася**: її прогноз справдився. Вона завжди **тримала руку на пульсі** подій і знала, що конфлікт неминучий. Але навіть вона не очікувала, що все станеться **ні сіло ні впало** — раптово, без попередження.

> 💡 **Чи знали ви?**
>
> Українська мова має понад 30,000 фразеологізмів — більше, ніж більшість європейських мов!
```

#### Section 2: Semantic Categories — 800-1000 words

```markdown
## [Category Name]: Фразеологізми

### Категорія 1: [Semantic Group]

**[Idiom 1]** — [Literal meaning] → [Figurative meaning]

**Приклад у контексті:**

> [2-3 sentence example showing natural usage]

**Регістр:** [Register: розмовний, нейтральний, книжний, etc.]

**Синоніми:** [Related expressions with subtle differences]

---

**[Idiom 2]** — [Literal meaning] → [Figurative meaning]

[Continue pattern for 5-6 idioms in this category]

### Категорія 2: [Next Semantic Group]

[Continue with next category...]
```

**Semantic category examples:**

| Category             | Ukrainian    | Example Idioms                                       |
| -------------------- | ------------ | ---------------------------------------------------- |
| Соматичні (body)     | Частини тіла | рукою подати, на свої очі, мати голову на плечах     |
| Зоологічні (animal)  | Тварини      | вовком дивитися, як риба у воді, купити кота в мішку |
| Кольорові (color)    | Кольори      | чорна заздрість, біла ворона, рожеві окуляри         |
| Природні (nature)    | Природа      | як грім серед ясного неба, після дощику в четвер     |
| Кількісні (quantity) | Кількість    | як кіт наплакав, хоч греблю гати                     |

#### Section 3: Proverbs and Sayings — 300-400 words

```markdown
## Прислів'я та приказки

### Про [Theme]

**Без труда нема плода.**

- _Without labor there's no fruit._ (No pain, no gain.)
- **Вживання:** Мотивація до роботи
- **Регістр:** Нейтральний, широковживаний

**Як посієш, так і пожнеш.**

- _As you sow, so shall you reap._
- **Вживання:** Попередження про наслідки
- **Регістр:** Нейтральний

[Continue with 8-10 proverbs organized by theme]

> 🌍 **Культурний контекст**
>
> [Explain cultural background — many Ukrainian proverbs reflect agrarian past, Cossack values, or Christian tradition]
```

#### Section 4: Usage in Context — 300-400 words

```markdown
## Вживання у контексті

### Діалог 1: Побутова розмова

**Оля:** Ну що, як справи на роботі?

**Петро:** Та **ні пуху ні пера**! Проєкт нарешті завершили.

**Оля:** Справді? Я думала, ви ще **на мілині сидите** — грошей ніяк не виділяли.

**Петро:** Було складно, але шеф нарешті **взяв бика за роги** і знайшов інвестора.

### Діалог 2: Формальніший контекст

[Show how some idioms work in more formal settings, and which don't]

### Помилки у вживанні

**Помилка:** Використання книжного фразеологізму в розмові

- ❌ "Мій друг — стовп суспільства." (занадто книжно)
- ✅ "Мій друг — надійна людина."

**Помилка:** Змішування фразеологізмів

- ❌ "Рукою подати на мілині" (два різні вирази)
- ✅ "Рукою подати" АБО "сидіти на мілині"
```

---

## Phraseology-Specific Activities

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/b2-41-idioms.yaml`:**

```yaml
- type: match-up
  title: Фразеологізм та значення
  pairs:
    - left: рукою подати
      right: дуже близько
    - left: як кіт наплакав
      right: дуже мало

- type: fill-in
  title: Фразеологізми в контексті
  items:
    - sentence: Магазин зовсім поруч, [___].
      answer: рукою подати
      options:
        - рукою подати
        - на носі
```

---

### Activity Examples (Conceptual)

_Note: These activities must be implemented in YAML._

1. **Idiom Matching (match-up):** Match phrase to meaning.
2. **Context Completion (fill-in):** Choose phrase for context.
3. **Synonym Nuance (group-sort):** Sort by intensity.
4. **Register Sorting (group-sort):** Sort by register.
5. **Proverb Completion (fill-in):** Finish the proverb.

---

## Engagement Boxes for Phraseology Modules

```markdown
> 💡 **Етимологія**
>
> [Origin story of a particularly interesting idiom]

> 🎭 **Варіанти**
>
> [Show regional or stylistic variants of the same expression]

> ⚠️ **Фальшиві друзі**
>
> [Idioms that look like English expressions but mean something different]

> 🌍 **Культурний контекст**
>
> [Cultural background explaining why this expression exists]

> 📚 **У літературі**
>
> [Quote from Ukrainian literature using the expression]

> 🔄 **Синоніми**
>
> [Compare 2-3 similar expressions with subtle differences]
```

---

---

## Content Structure Note

### Vocabulary & Activities

**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:

- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

The build system will inject these sections at build time.

---

## Example Module Outline: M45 (Somatic Idioms)

```markdown
# Соматичні фразеологізми: Частини тіла

> 🎯 **Чому це важливо?**
> Фразеологізми з частинами тіла — найпоширеніша категорія в українській мові...

## Вступ

[Narrative using 3-4 somatic idioms]

## Голова

- мати голову на плечах
- втратити голову
- морочити голову

## Руки

- рукою подати
- золоті руки
- опустити руки

## Очі

- на свої очі
- закривати очі
- відкрити комусь очі

## Вживання у контексті

[Dialogues showing natural usage]

# Підсумок

# Словник [30+ expressions + terminology]

# Активності [10+ activities]
```

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/b2-module-template.md`
- **B2 Curriculum Plan:** `docs/l2-uk-en/B2-CURRICULUM-PLAN.md` (M41-70 phraseology progression)
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
