# B2 History Module Template

**Purpose:** Reference template for B2 Ukrainian history modules (M71-95: Medieval to Present, Decolonization Focus)

**Based on:** `b2-module-template.md` — inherits all B2 quality standards

**Related Issue:** [#305](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/305)

---

## Quick Reference Checklist

Before submitting a B2 history module, verify all items from `b2-module-template.md` PLUS:

### History-Specific Requirements
- [ ] **CBI pedagogy:** Content-Based Instruction with Narrative Arc (NOT TTT)
- [ ] **Extended narrative:** 500+ word historical account (main text)
- [ ] **Decolonization lens:** Ukraine-centric perspective, not Russian imperial framing
- [ ] **Primary sources:** Include translated excerpts from historical documents
- [ ] **Vocabulary in context:** Historical terms embedded in narrative, not listed
- [ ] **Engagement boxes:** Historical context, myth-busting, modern relevance

---

## Module Structure (History-Specific)

### 1. Frontmatter

```yaml
---
module: b2-XX
title: "Ukrainian Title — Historical Period/Event"
phase: "B2.3 [Ukrainian History]"
pedagogy: "CBI"  # Content-Based Instruction
register: "публіцистичний"  # Historical narrative style
tags:
  - history
  - [era: medieval, cossack, imperial, soviet, independence]
  - [topic: specific-event-or-period]
grammar:
  - "Historical narrative tenses"
  - "Passive voice in historical writing"
vocabulary_focus:
  - "Historical terminology"
  - "Political/military vocabulary"
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
> *— Джерело: [Attribution]*

**Аналіз:**
- Яку позицію висловлює автор?
- Які слова/вирази вказують на цю позицію?
- Як цей документ відображає погляди свого часу?

### Документ 2: [Contrasting Source]

[If applicable, provide contrasting perspective for analysis]
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

## History-Specific Activities

### Comprehension with Analysis

```markdown
## quiz: Розуміння тексту

1. Яка була головна причина козацького повстання під проводом Богдана Хмельницького проти Речі Посполитої у 1648 році?
   - [ ] Релігійні переслідування
   - [x] Соціально-економічне гноблення козацтва та селянства
   - [ ] Особиста образа гетьмана
   - [ ] Підбурювання з боку Московського царства
   > Хоча всі фактори відігравали роль, основною причиною було гноблення козацтва.

[10+ comprehension questions testing understanding of narrative]
```

### Vocabulary in Historical Context

```markdown
## fill-in: Історична лексика в контексті

1. Запорозька Січ була [___] козацької демократії.
   - [ ] прикладом (example)
   - [x] осередком (center)
   - [ ] причиною (cause)
   > Осередок = центр, місце зосередження.

2. Козаки [___] спротив польському пануванню.
   - [x] чинили (offered/put up)
   - [ ] робили (did)
   - [ ] давали (gave)
   > Чинити спротив = to resist (fixed collocation).

[10+ items using historical vocabulary]
```

### Source Analysis

```markdown
## select: Аналіз первинного джерела

Прочитайте уривок і виберіть усі правильні твердження:

> "..." [Primary source excerpt]

- [x] Автор підтримує [position]
- [ ] Автор критикує [position]
- [x] Текст написаний для [audience]
- [ ] Текст є об'єктивним описом подій
- [x] Лексика вказує на [register/bias]

[Multi-select questions requiring close reading]
```

### Myth vs. Reality

```markdown
## true-false: Міфи та реальність

1. Переяславська рада 1654 року означала добровільне приєднання України до Росії.
   - [ ] Правда
   - [x] Міф
   > Це радянський міф. Насправді угода передбачала військовий союз, а не підданство.

2. Козацька Україна мала власну державність і дипломатію.
   - [x] Правда
   - [ ] Міф
   > Гетьманщина була квазідержавним утворенням із власною армією, адміністрацією та зовнішньою політикою.

[14+ items challenging misconceptions]
```

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

## Vocabulary Section for History Modules

```markdown
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| **гетьман** | hetman | козацький вождь, очільник Війська Запорозького |
| **козацтво** | Cossackdom | козацький соціальний стан та культура |
| **Січ** | Sich | козацька фортеця-столиця |
| **повстання** | uprising, rebellion | збройний спротив владі |
| **гноблення** | oppression | соціально-політичний тиск |
| **панування** | rule, dominion | контроль, влада над територією |
| **спротив** | resistance | протидія, опір |
| **здобути перемогу** | to win a victory | фіксований вираз |
| **підірвати владу** | to undermine power | ослабити, зашкодити |
| **первинне джерело** | primary source | історіографічний термін |
| [30+ items] | | |
```

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
# Активності [14+ activities]
```

---

## Decolonization Content Guidelines

### Required Myth-Busting

**For each major historical period, address:**

| Period | Common Myth | Ukrainian Reality |
|--------|-------------|-------------------|
| Medieval | Kyivan Rus = "Ancient Russia" | Rus was a multi-ethnic state; "Russia" is a later appropriation |
| Cossack | Pereyaslav = "reunification" | Military alliance, not submission; broken by Moscow |
| Imperial | "Little Russians" | Colonial term; Ukrainians had distinct identity and language |
| Soviet | "Brotherly nations" | Russification, Holodomor, cultural suppression |
| Modern | "One people" | Independent nation with separate history, language, culture |

### Decolonization Vocabulary

| Term | Usage |
|------|-------|
| Московське царство | Use instead of "Росія" for pre-1721 period |
| Російська імперія | Use for 1721-1917 period |
| Русифікація | Describe policies suppressing Ukrainian language/culture |
| Колоніальний наратив | Label Russian/Soviet historiographical distortions |
| Українська державність | Emphasize continuous tradition of statehood |

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/b2-module-template.md`
- **B2 Curriculum Plan:** `docs/l2-uk-en/B2-CURRICULUM-PLAN.md` (M71-95 history progression)
- **Decolonization guidelines:** Referenced in curriculum plan

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
