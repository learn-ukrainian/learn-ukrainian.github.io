# B2 History Module Template

**Purpose:** Reference template for B2 Ukrainian history modules (M71-131: Origins to Present, Decolonization Focus)

**Based on:** `b2-module-template.md` — inherits all B2 quality standards

**Related Issues:** [#305](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/305), [#332](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/332)

> **Note:** Synthesis modules (M83, M107, M119, M125, M131) use `b2-synthesis-module-template.md` instead.

<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Читання
  - Первинні джерела
  - Деколонізаційний погляд
  - Підсумок
  - Потрібно більше практики?
  optional_sections:
  - Діалоги
  forbidden_headers:
  - Activities
  - Vocabulary
  - External Resources
  - Вправи
  - Словник
  - Зовнішні ресурси
  pedagogy: CBI
  min_word_count: 1800
  required_callouts:
  - myth-buster
  - history-bite
  - quote
  description: History modules use Content-Based Instruction with mandatory decolonization
    content
-->

---

## Quick Reference Checklist

Before submitting a B2 history module, verify all items from `b2-module-template.md` PLUS:

### History-Specific Requirements

- [ ] **CBI pedagogy:** Content-Based Instruction with Narrative Arc (NOT TTT)
- [ ] **Extended narrative:** 500+ word historical account (main text)
- [ ] **Decolonization lens:** Ukraine-centric perspective, not Russian imperial framing
- [ ] **Primary sources (≥2):** MANDATORY — include at least 2 excerpts from historical documents using `[!quote]` callout format
- [ ] **Reading tasks (2-3):** External reading assignments with linguistic analysis questions
- [ ] **Essay assignment:** 400+ word essay with model answer and rubric
- [ ] **Activity count:** 10-12 language-focused activities (reduced from 14+)
- [ ] **Vocabulary in context:** Historical terms embedded in narrative, not listed
- [ ] **Engagement boxes:** Historical context, myth-busting, modern relevance
- [ ] **NO DIALOGS:** History modules are READING-CENTRIC. Do NOT include conversational dialogs — they waste space and distract from historical content. Use primary source excerpts instead.

---

## Module Structure (History-Specific)

### 1. Frontmatter

```yaml
---
module: b2-XX
title: 'Ukrainian Title — Historical Period/Event'
phase: 'B2.3 [Ukrainian History]'
pedagogy: 'CBI' # Content-Based Instruction
register: 'публіцистичний' # Historical narrative style
tags:
  - history
  - [era: medieval, cossack, imperial, soviet, independence]
  - [topic: specific-event-or-period]
grammar:
  - 'Historical narrative tenses'
  - 'Passive voice in historical writing'
vocabulary_focus:
  - 'Historical terminology'
  - 'Political/military vocabulary'
---
```

### 2. Narrative Arc Structure

#### Section 1: Hook — 200-300 words

```markdown
# [Historical Topic Title]

> 🎯 **Чому це важливо?**
>
> [Connect historical event to modern Ukrainian identity]
> [Explain relevance to language learner]
> [Frame the decolonization perspective]

## Вступ

[Compelling opening that draws reader in — a dramatic moment, a key figure's words, or a surprising fact]

[Set the historical context: When? Where? Who? What was at stake?]

> 💡 **Чи знали ви?**
>
> [Surprising fact that challenges common misconceptions]
```

#### Section 2: Historical Narrative — 800-1000 words

```markdown
## [Historical Event/Period Name]

### Контекст

[200-300 words of background: political situation, key players, tensions]

### Основні події

[400-500 words of main narrative with embedded vocabulary]

**Key vocabulary should appear naturally in the narrative:**

> Гетьман Богдан Хмельницький **очолив** козацьке повстання проти польського панування. Запорозька Січ стала центром **спротиву**. Козаки **здобули** низку перемог, що **підірвали** владу Речі Посполитої.

### Наслідки

[200-300 words on consequences and legacy]

> 🌍 **Сучасна перспектива**
>
> [How this historical event is viewed today in Ukraine]
> [Contrast with Russian/Soviet historiography if relevant]
```

#### Section 3: Primary Sources — 200-300 words

```markdown
## Первинні джерела

### Документ 1: [Source Title]

**Контекст:** [Brief context about the document]

> [Excerpt from primary source in Ukrainian — 100-200 words]
> _— Джерело: [Attribution]_

**Лінгвістичний аналіз:**

<critical>
**FOCUS ON LANGUAGE, NOT CONTENT INTERPRETATION**

Questions must analyze LINGUISTIC features, not historical meaning.
</critical>

**✅ GOOD (Linguistic Analysis):**

- Який регістр використовує автор? Наведіть приклади.
- Знайдіть три приклади пасивного стану. Чому автор їх використовує?
- Порівняйте лексику цього тексту з лексикою модуля. Які слова застаріли?
- Які синтаксичні конструкції характерні для офіційного стилю?

**❌ BAD (Content Interpretation):**

- Що автор думає про Московське царство? ← Tests interpretation
- Чому Хмельницький прийняв це рішення? ← Tests historical knowledge

### Документ 2: [Contrasting Source]

[If applicable, provide contrasting perspective for LINGUISTIC comparison]
```

#### Section 4: Decolonization Focus — 200-300 words

```markdown
## Деколонізаційний погляд

### Міфи та реальність

**Міф:** [Common misconception from Russian/Soviet historiography]

**Реальність:** [Ukrainian perspective based on primary sources and modern scholarship]

> ⚠️ **Деколонізація**
>
> [Explain why the Russian/Soviet narrative is problematic]
> [Cite Ukrainian historians or primary sources]

### Сучасна Україна

[Connect historical event to modern Ukrainian identity and independence movement]
```

---

## Reading Tasks (External Assignments)

History modules should include **2-3 external reading tasks** for deeper engagement with authentic Ukrainian historical texts.

```yaml
# In activities/{slug}.yaml

- type: reading
  id: b2-75-reading-01
  title: 'Аналіз первинного джерела'
  resource:
    type: primary_source
    url: 'https://...'
    title: 'Універсал Богдана Хмельницького'
  tasks:
    - 'Знайдіть у тексті три приклади офіційного регістру'
    - 'Які дієслова використовує автор для опису своїх дій?'
    - 'Порівняйте синтаксис цього документа із сучасною публіцистикою'

- type: reading
  id: b2-75-reading-02
  title: 'Сучасний історичний аналіз'
  resource:
    type: article
    url: 'https://...'
    title: "[Ukrainian historian's article]"
  tasks:
    - 'Як автор описує деколонізаційний підхід до цього періоду?'
    - 'Знайдіть приклади академічного регістру в тексті'
    - 'Порівняйте мову історика з мовою первинного джерела'
```

**Note:** Questions focus on LINGUISTIC analysis, not historical interpretation.

---

## Essay Assignment

Each history module should include a **400+ word essay** with model answer and rubric.

```markdown
# Есе

## Тема

Напишіть есе (400+ слів) на тему: "[Деколонізаційний аналіз історичної події]"

**Вимоги:**

- Використайте лексику та граматику модуля
- Застосуйте деколонізаційний підхід до аналізу
- Порівняйте українську та російську/радянську історіографію
- Використайте цитати з первинних джерел

**Структура:**

1. Вступ (100 слів) — тема та теза
2. Основна частина (200 слів) — аргументи з первинних джерел
3. Висновок (100 слів) — деколонізаційна перспектива

## Критерії оцінювання

| Критерій                    | Вага | Опис                                                                      |
| --------------------------- | ---- | ------------------------------------------------------------------------- |
| **Мовна якість**            | 40%  | Граматична правильність, багатство лексики, складність речень (B2 рівень) |
| **Використання матеріалу**  | 30%  | Цитування первинних джерел, використання лексики модуля                   |
| **Структура та зв'язність** | 20%  | Логічна організація, дискурсивні маркери                                  |
| **Деколонізаційний підхід** | 10%  | Критичний аналіз імперських наративів                                     |

## Зразок відповіді

[400+ word model essay demonstrating:]

- B2-level grammar and syntax
- Module vocabulary in context
- Decolonization framework
- Citations from primary sources
- Academic register

**Мовні особливості зразка:**

- Пасивні конструкції: "було засновано", "був обраний"
- Складні речення з підрядними
- Історична лексика модуля
- Академічний регістр
```

---

## History-Specific Activities

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

### Activity Examples (Conceptual)

_Note: These activities must be implemented in YAML._

1. **Reading Comprehension (quiz):** Test understanding of Ukrainian text, NOT recall of historical facts.
2. **Vocabulary in Context (fill-in):** Test vocabulary and collocations from module.
3. **Grammar in Historical Sentences (error-correction):** Test grammar using historical content as context.
4. **Source Analysis (select):** Test close reading of primary source in Ukrainian.
5. **Vocabulary Matching (match-up):** Test recognition of historical vocabulary.
6. **Mark the Words (mark-the-words):** Test grammar recognition in authentic historical text.

---

## Engagement Boxes for History Modules

```markdown
> 🏛️ **Історичний контекст**
>
> [Background information that helps understand the period]

> ⚠️ **Деколонізація**
>
> [Challenge Russian/Soviet historiographical myths]

> 📜 **Первинне джерело**
>
> [Quote from historical document with translation notes]

> 🌍 **Сучасна Україна**
>
> [Connect to post-2014 or post-2022 context]

> 💡 **Чи знали ви?**
>
> [Surprising historical fact]

> 🗺️ **Географічний контекст**
>
> [Explain historical geography — borders, regions, place names]
```

---

---

## Content Structure Note

### Vocabulary & Activities

**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:

- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

The build system will inject these sections at build time.

**History vocabulary notes:**

- Include political/military terminology
- Include historiographical terms (джерело, свідчення, інтерпретація)
- Include fixed collocations common in historical writing
- Note decolonization-relevant terms (гноблення, колонізація, русифікація)

---

## Example Module Outline: M75 (Cossack Era)

```markdown
# Козацька ера: Хмельниччина

> 🎯 **Чому це важливо?**
> Козацька революція 1648-1657 років — це початок модерної української державності...

## Вступ

[Hook with dramatic opening — perhaps Хмельницький's words]

## Хмельниччина: Повстання та війна

### Контекст [Polish-Lithuanian oppression]

### Основні події [Uprising, battles, negotiations]

### Наслідки [Hetmanate, Pereyaslav]

## Первинні джерела

### Універсал Богдана Хмельницького

### Свідчення іноземних дипломатів

## Деколонізаційний погляд

### Міфи про "возз'єднання"

### Сучасна українська історіографія

# Підсумок

# Словник [30+ historical terms]

# Активності [10-12 language-focused activities]

# Есе [400+ word decolonization analysis with rubric]
```

---

## Decolonization Content Guidelines

### Required Myth-Busting

**For each major historical period, address:**

| Period   | Common Myth                   | Ukrainian Reality                                               |
| -------- | ----------------------------- | --------------------------------------------------------------- |
| Medieval | Kyivan Rus = "Ancient Russia" | Rus was a multi-ethnic state; "Russia" is a later appropriation |
| Cossack  | Pereyaslav = "reunification"  | Military alliance, not submission; broken by Moscow             |
| Imperial | "Little Russians"             | Colonial term; Ukrainians had distinct identity and language    |
| Soviet   | "Brotherly nations"           | Russification, Holodomor, cultural suppression                  |
| Modern   | "One people"                  | Independent nation with separate history, language, culture     |

### Decolonization Vocabulary

| Term                   | Usage                                                    |
| ---------------------- | -------------------------------------------------------- |
| Московське царство     | Use instead of "Росія" for pre-1721 period               |
| Російська імперія      | Use for 1721-1917 period                                 |
| Русифікація            | Describe policies suppressing Ukrainian language/culture |
| Колоніальний наратив   | Label Russian/Soviet historiographical distortions       |
| Українська державність | Emphasize continuous tradition of statehood              |

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/b2-module-template.md`
- **Synthesis template:** `docs/l2-uk-en/templates/b2-synthesis-module-template.md` (for M83, M107, M119, M125, M131)
- **B2 Curriculum Plan:** `docs/l2-uk-en/B2-CURRICULUM-PLAN.md` (M71-131 history progression)
- **Restructure proposal:** `docs/l2-uk-en/B2-HISTORY-RESTRUCTURE-PROPOSAL.md`
- **Gemini expansion:** `docs/l2-uk-en/B2-GEMINI-EXPANSION-PROPOSAL.md` (detailed module specs)
- **Decolonization guidelines:** Referenced in curriculum plan

---

**Last Updated:** 2025-12-29
**Template Version:** 1.2

**Changelog:**

- v1.2 (2025-12-29): Updated module range M71-131, added reference to synthesis template
- v1.1 (2025-12-29): Added NO DIALOGS rule, made primary sources mandatory (≥2)
