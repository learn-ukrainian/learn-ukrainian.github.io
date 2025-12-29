# C1 Folk Culture Module Template

**Purpose:** Reference template for C1 folk culture modules (M121-145: Traditional Ukrainian Culture, Music, Arts, Beliefs, Crafts)

**Based on:** `c1-module-template.md` — inherits all C1 quality standards

**Related Issue:** [#306](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/306)

---

## Quick Reference Checklist

Before submitting a C1 folk culture module, verify all items from `c1-module-template.md` PLUS:

### Folk Culture-Specific Requirements
- [ ] **CBI pedagogy:** Content-Based Instruction (cultural content drives language)
- [ ] **Authentic materials:** Folk songs, proverbs, ritual descriptions, craft terminology
- [ ] **Regional variation:** Note differences across Ukrainian regions
- [ ] **Historical context:** Pre-Christian origins, Christian syncretism, Soviet era changes
- [ ] **Modern relevance:** How traditions continue or are revived today
- [ ] **Vocabulary immersion:** Traditional terminology embedded in cultural narrative
- [ ] **NO TOURIST DIALOGS:** Folk culture modules present AUTHENTIC MATERIALS. Do NOT add fictional tourist scenarios. If a folk song has dialogue form, quote the song—don't simulate conversations about it.

---

## Module Types in C1.5

### Traditional Music & Song (M121-130)

| Modules | Focus | Content |
|---------|-------|---------|
| M121-122 | Folk Song Genres | колискові, веснянки, колядки, щедрівки |
| M123-124 | Wedding Songs | весільні пісні, обрядові тексти |
| M125-126 | Historical Songs | думи, історичні пісні |
| M127-128 | Kobzar Tradition | кобзарство, бандура, ліра |
| M129-130 | Modern Revival | фольклорний рух, сучасні обробки |

### Traditional Arts & Crafts (M131-140)

| Modules | Focus | Content |
|---------|-------|---------|
| M131-132 | Textile Arts | вишивка, ткацтво, килими |
| M133-134 | Decorative Arts | писанкарство, петриківка, різьблення |
| M135-136 | Pottery & Ceramics | керамка, гончарство, опішнянська кераміка |
| M137-138 | Folk Architecture | хата, дах, піч, інтер'єр |
| M139-140 | Folk Beliefs & Calendar | народний календар, обряди, звичаї |

### Integration (M141-145)

| Modules | Focus |
|---------|-------|
| M141-142 | Regional Variation | Полісся, Галичина, Слобожанщина, Поділля |
| M143-144 | Revival Movements | Сучасне відродження традицій |
| M145 | Folk Culture Checkpoint |

---

## Module Structure (Folk Culture-Specific)

### 1. Frontmatter

```yaml
---
module: c1-1XX
title: "[Folk Culture Topic]: Ukrainian Title"
phase: "C1.5 [Folk Culture & Arts]"
pedagogy: "CBI"  # Content-Based Instruction
register: "varies"  # Mix of художній and розмовний
tags:
  - folk-culture
  - [domain: music, textile, ceramics, beliefs, calendar]
  - [region: if applicable]
grammar:
  - "Folk song syntax (inversions, archaisms)"
  - "Craft terminology"
vocabulary_focus:
  - "Народна термінологія"
  - "Обрядова лексика"
---
```

### 2. Folk Culture Content Structure

#### Section 1: Cultural Introduction — 400-500 words

```markdown
# [Folk Culture Topic]

> 🎯 **Чому це важливо?**
>
> [Explain cultural significance]
> [Connection to Ukrainian identity]
> [Why C1 learners should know this]

## Вступ

[Engaging introduction to the cultural tradition — 200-250 words]

[Historical origins — when, where, how this tradition developed]

> 💡 **Чи знали ви?**
>
> [Surprising fact about this tradition]

### Ключова термінологія

| Термін | Значення | Примітка |
|--------|----------|----------|
| [Term 1] | [Meaning] | [Context] |
| [Term 2] | [Meaning] | [Context] |
| [Term 3] | [Meaning] | [Context] |
```

#### Section 2: Deep Cultural Content — 800-1000 words

```markdown
## [Main Cultural Content]

### [Aspect 1]: [Title]

[Detailed exploration — 250-300 words]

**Автентичний приклад:**

> [Folk song lyrics, proverb, ritual text, or craft description — 100-200 words]
>
> **Переклад ключових термінів:**
> - [Term]: [translation/explanation]
> - [Term]: [translation/explanation]

> 🎵 **Фольклорний контекст** (for music modules)
>
> [Context about when/how this was performed]

---

### [Aspect 2]: [Title]

[Continue pattern — 250-300 words]

**Регіональні варіанти:**

| Регіон | Варіант | Особливості |
|--------|---------|-------------|
| Полісся | [Variant] | [Features] |
| Галичина | [Variant] | [Features] |
| Поділля | [Variant] | [Features] |
| Слобожанщина | [Variant] | [Features] |

---

### [Aspect 3]: [Title]

[Continue pattern — 250-300 words]

> 🏛️ **Історичний контекст**
>
> [Pre-Christian origins, Soviet era changes, modern revival]
```

#### Section 3: Comparative Analysis — 300-400 words

```markdown
## Порівняльний аналіз

### [Tradition 1] vs. [Tradition 2]

[Compare two related traditions, regional variants, or historical periods]

| Аспект | [Tradition 1] | [Tradition 2] |
|--------|---------------|---------------|
| Регіон | [Region] | [Region] |
| Функція | [Function] | [Function] |
| Символіка | [Symbolism] | [Symbolism] |
| Сучасний стан | [Current status] | [Current status] |

### Критичне мислення

**Питання для роздуму:**
1. Як ця традиція відображає українську ідентичність?
2. Як вона змінилася за радянських часів?
3. Як вона відроджується сьогодні?
4. Які регіональні відмінності найбільш виразні?
```

#### Section 4: Modern Context — 200-300 words

```markdown
## Сучасна Україна

### Відродження традицій

[How this tradition is being revived today — 100-150 words]

**Сучасні носії:**
- [Contemporary practitioner/group 1]
- [Contemporary practitioner/group 2]
- [Contemporary practitioner/group 3]

### Де побачити/почути/спробувати

| Місце | Тип | Особливості |
|-------|-----|-------------|
| [Location 1] | [Type] | [Features] |
| [Location 2] | [Type] | [Features] |
| [Festival/event] | [Type] | [Features] |

> 🌍 **Де знайти**
>
> [Museums, festivals, YouTube channels, Spotify playlists, online resources]
```

---

## Folk Culture-Specific Activities

### CRITICAL: Language Practice, Not Content Testing

<critical>

**Activities test LANGUAGE SKILLS, not folk culture recall.**

The lesson teaches both Ukrainian AND folk culture. Activities practice only Ukrainian using cultural content as context.

**✅ CORRECT:** "Згідно з текстом, як автор описує функцію рушника?" (requires reading Ukrainian)
**❌ WRONG:** "Що символізує калина в українській культурі?" (tests cultural recall, not language)

**Key Test:** Can the learner answer without reading the Ukrainian text? If yes, rewrite.

| Component | Purpose |
|-----------|---------|
| **Lesson Content** | Teaches BOTH Ukrainian language AND folk culture knowledge |
| **Activities** | Practice ONLY Ukrainian language skills using cultural content as context |

**Activity Types and Their Language Focus:**
- **quiz**: Test reading comprehension — "Згідно з текстом модуля..."
- **cloze**: Test vocabulary in folk song/text context
- **match-up**: Test vocabulary — Ukrainian terms ↔ Ukrainian definitions
- **fill-in**: Test vocabulary/collocations from module
- **group-sort**: Test categorization using module vocabulary
- **mark-the-words**: Test grammar recognition in authentic folk text
- **error-correction**: Test grammar, NOT cultural facts

</critical>

---

### Activity Format Quick Reference

**CRITICAL:** Use these exact formats for MDX generation to work correctly.

| Activity | Format |
|----------|--------|
| **quiz** | `- [ ] wrong` / `- [x] correct` with optional `> explanation` |
| **true-false** | `- [x] True.` with `> explanation` / `- [ ] False.` with `> explanation` |
| **fill-in** | `> [!answer] correct` + `> [!options] a \| b \| c \| d` |
| **error-correction** | ALL 4 required: `> [!error]` + `> [!answer]` + `> [!options]` + `> [!explanation]` |
| **match-up** | Table: `\| Left \| Right \|` |
| **group-sort** | `### Category` headers with `- items` underneath |
| **unjumble** | `> [!answer] Correct sentence here.` |
| **cloze** | Inline: `{blank\|opt1\|opt2\|answer}` |
| **select** | Multiple `- [x]` for all correct options |
| **translate** | Multi-choice: `- [x] Correct translation.` with `> explanation` |
| **mark-the-words** | `*marked*` words in blockquote passage |
| **dialogue-reorder** | `- [N]` numbered lines (N = correct order) |

---

### Folk Song Analysis

```markdown
## cloze: Народна пісня

Заповніть пропуски у народній пісні:

> Ой у [___] та й при [___]
> Там [___] [___] сіно косить,
> А [___] [___] граблі носить,
> А [___] [___] обід носить...

[!blanks] лузі, долині, козак, молодий, дівчина, чорноброва, матінка, старенька

> Пояснення: Ця веснянка описує традиційний розподіл праці у сільській родині.

[20+ blanks in authentic folk text]
```

### Terminology Matching

```markdown
## match-up: Фольклорна термінологія

- колисанка | lullaby
- веснянка | spring song
- колядка | Christmas carol
- щедрівка | New Year carol
- гаївка | Easter song
- весільна пісня | wedding song
- думка | epic song (kobzar)
- коломийка | Hutsul dance song
- вишиванка | embroidered shirt
- писанка | decorated Easter egg
- рушник | ritual towel
- піч | traditional stove

[14+ folk terminology matches]
```

### Regional Variation

```markdown
## group-sort: Регіональні традиції

Розподіліть елементи за регіонами:

- group: Полісся
  - пісні з укання
  - архаїчні веснянки
  - чорна кераміка

- group: Галичина
  - коломийки
  - гуцульські мотиви
  - різьблення

- group: Поділля
  - петриківський розпис
  - подільська вишивка
  - білі орнаменти

- group: Слобожанщина
  - опішнянська кераміка
  - близькість до літературної мови
  - степові мотиви

[20+ regional elements across 4-5 regions]
```

### Reading Comprehension (Language-Focused)

```markdown
## quiz: Розуміння тексту

> **Instruction:** Відповідайте на питання на основі прочитаного тексту модуля.

1. Згідно з текстом, як автор характеризує роль калини в українській культурі?
   - [ ] Автор зазначає, що калина має лише декоративне значення
   - [x] Автор виділяє калину як один із найголовніших національних символів
   - [ ] Автор пише, що символіка калини прийшла з інших культур
   - [ ] Автор не згадує калину в тексті
   > Текст чітко формулює значення калини в розділі про символіку.

2. Як у тексті модуля описано функцію рушника у весільному обряді?
   - [ ] Текст зосереджується лише на практичній функції
   - [ ] Автор називає рушник сучасним винаходом
   - [x] Автор підкреслює символічну функцію — поєднання молодих та оберіг
   - [ ] У тексті не згадується рушник
   > У розділі про весільні обряди автор детально пояснює символіку рушника.

[All questions must begin with "Згідно з текстом" — tests READING COMPREHENSION, not cultural recall]
```

---

## Engagement Boxes for Folk Culture Modules

```markdown
> 💡 **Чи знали ви?**
>
> [Surprising fact about the tradition]

> 🎵 **Фольклорний контекст**
>
> [When/where/how this was traditionally performed]

> 🏛️ **Історичний контекст**
>
> [Pre-Christian origins, historical evolution]

> 🗺️ **Регіональні варіанти**
>
> [How this tradition differs across regions]

> 🌍 **Сучасне відродження**
>
> [How the tradition is being revived today]

> 📺 **Де подивитися/послухати**
>
> [YouTube, Spotify, museums, festivals]
```

---

## Vocabulary Section for Folk Culture Modules

```markdown
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| **веснянка** | spring song | обрядова пісня весняного циклу |
| **колядка** | Christmas carol | пісня, яку співають на Різдво |
| **щедрівка** | New Year carol | пісня на Старий Новий рік |
| **вишиванка** | embroidered shirt | традиційний одяг з вишивкою |
| **писанка** | decorated Easter egg | яйце, розписане воском |
| **рушник** | ritual towel | вишитий рушник для обрядів |
| **піч** | traditional stove | центр української хати |
| **оберіг** | talisman, protective charm | захисний символ |
| **кобзар** | kobzar, blind minstrel | мандрівний співець із кобзою |
| **бандура** | bandura | український струнний інструмент |
| [35+ folk culture terms] | | |
```

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/c1-module-template.md`
- **C1 Curriculum Plan:** `docs/l2-uk-en/C1-CURRICULUM-PLAN.md` (M121-145 specifications)
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
