# C1 Folk Culture Module Template

**Purpose:** Reference template for C1 folk culture modules (M121-145: Traditional Ukrainian Culture, Music, Arts, Beliefs, Crafts)

**Based on:** `c1-module-template.md` — inherits all C1 quality standards

**Related Issue:** [#306](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/306)


<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Фольклор
  - Підсумок
  - Потрібно більше практики?
  pedagogy: Immersion
  min_word_count: 3000
  required_callouts: []
  description: C1 folk culture modules explore Ukrainian traditions
-->

---

## Quick Reference Checklist

Before submitting a C1 folk culture module, verify all items from `c1-module-template.md` PLUS:

### Folk Culture-Specific Requirements
- [ ] **CBI pedagogy:** Content-Based Instruction (cultural content drives language)
- [ ] **Authentic materials:** Folk songs, proverbs, ritual descriptions, craft terminology
- [ ] **Reading tasks (2-3):** External reading assignments with linguistic analysis of authentic materials
- [ ] **Essay assignment:** 400+ word cultural analysis with model answer and rubric
- [ ] **Activity count:** 10-12 language-focused activities (NOT 14+)
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

[Continue with modern context section...]
```

---

## Reading Tasks (External Assignments)

Folk culture modules should include **2-3 external reading tasks** for deeper engagement with authentic materials.

```yaml
# In activities/{slug}.yaml

- type: reading
  id: c1-1XX-reading-01
  title: "Автентичний фольклорний текст"
  resource:
    type: primary_source
    url: "https://..."
    title: "[Folk song collection / ritual description / craft manual]"
  tasks:
    - "Знайдіть у тексті три приклади архаїчних форм. Як вони змінилися в сучасній мові?"
    - "Який регістр використовується в тексті? Наведіть приклади."
    - "Порівняйте лексику тексту з лексикою модуля. Які терміни потребують пояснення?"

- type: reading
  id: c1-1XX-reading-02
  title: "Науковий культурологічний аналіз"
  resource:
    type: article
    url: "https://..."
    title: "[Ukrainian ethnographer's article]"
  tasks:
    - "Як автор використовує фольклорну термінологію?"
    - "Знайдіть приклади академічного регістру в тексті"
    - "Порівняйте інтерпретацію дослідника з аналізом у модулі"
```

**Note:** Questions focus on LINGUISTIC analysis of authentic materials, not cultural interpretation alone.

---

## Essay Assignment

Each folk culture module should include a **400+ word cultural analysis essay** with model answer and rubric.

```markdown
# Есе

## Тема

Напишіть культурознавчий аналіз (400+ слів): "[Folk Tradition]: Культурна функція та символіка"

**Вимоги:**
- Використайте лексику та граматику модуля
- Проаналізуйте культурну функцію та символічне значення традиції
- Використайте приклади з автентичних фольклорних текстів
- Порівняйте регіональні варіанти (якщо є)

**Структура:**
1. Вступ (100 слів) — культурний контекст
2. Основна частина (200 слів) — функція та символіка
3. Висновок (100 слів) — сучасне відродження та значення

## Критерії оцінювання

| Критерій | Вага | Опис |
|----------|------|------|
| **Мовна якість** | 40% | Граматична правильність, фольклорна термінологія, C1 рівень |
| **Використання матеріалу** | 30% | Цитування автентичних текстів, використання лексики модуля |
| **Культурний аналіз** | 20% | Розуміння функції та символіки традиції |
| **Структура та зв'язність** | 10% | Організація, дискурсивні маркери |

## Зразок відповіді

[400+ word model essay demonstrating:]
- C1-level grammar and syntax
- Module folk culture vocabulary (відіграти роль, символізувати, втілювати)
- Cultural analysis framework
- Citations from authentic folk texts
- Mix of художній and публіцистичний registers

**Мовні особливості зразка:**
- Фольклорна термінологія: "обрядова функція", "символічне значення"
- Складні речення з підрядними
- Академічні конструкції: "як свідчить", "на відміну від"
```

---

## Folk Culture-Specific Activities

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

**These are LANGUAGE lessons that use folk culture as context, NOT folk culture exams taught in Ukrainian.**

**The Golden Rule:** "Can the learner answer this without reading the Ukrainian text?"
- **If YES** → Rewrite (tests cultural knowledge, not language)
- **If NO** → Keep (tests Ukrainian comprehension)

### Examples: GOOD vs BAD Activities

**❌ BAD (Tests Cultural Knowledge):**
```markdown
1. Що символізує калина в українській культурі?
   - [x] Материнство і жіночність
```
Problem: Tests cultural symbolism recall. Can be answered without reading Ukrainian.

**❌ BAD (Tests Factual Recall):**
```markdown
1. Коли співають колядки?
   - [x] Під час Різдва
```
Problem: Tests folk calendar knowledge, not language.

**✅ GOOD (Tests Ukrainian Language):**
```markdown
1. Згідно з текстом, як автор описує функцію рушника в обряді?
   - [x] Автор підкреслює його символічну роль як зв'язку між світами
```
Why GOOD: Requires reading MODULE'S DESCRIPTION in Ukrainian.

**✅ GOOD (Tests Ukrainian Collocations):**
```markdown
1. Ця традиція [___] важливу роль у збереженні культурної ідентичності.
   - [x] відіграє
   > [!options] відіграє | робить | має | дає
```
Why GOOD: Tests fixed collocation (відіграти роль), requires understanding Ukrainian usage.

**Key phrases to use:**
- "Згідно з текстом..."
- "Як автор описує функцію/значення..."
- "У тексті модуля зазначено..."

**Never ask:**
- "Що символізує..." (unless "Як автор тлумачить символіку...")
- "Коли відбувається..." (tests cultural knowledge)
- "Які кольори використовують..." (tests craft facts)

</critical>

---

### Activity Mix for Folk Culture Modules

**Total: 10-12 activities** (focus on quality over quantity)

| Activity Type | Count | Purpose | Example |
|---------------|-------|---------|---------|
| **quiz** | 4-5 | Reading comprehension | "Згідно з текстом, як автор описує функцію рушника?" |
| **fill-in / cloze** | 3-4 | Folk vocabulary in context | "Традиція [___] важливу роль" → відіграє |
| **error-correction** | 2-3 | Grammar practice | Fix case/aspect errors in folk culture sentences |
| **match-up** | 1-2 | Terminology | Ukrainian folk term ↔ Ukrainian definition |
| **mark-the-words / select** | 1-2 | Analysis | Find archaic forms in folk song, identify symbolism |

**Note:** Plus 2-3 external reading tasks and 1 essay assignment (tracked in activities YAML).

---

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/c1-121-folk-songs.yaml`:**

```yaml
- type: cloze
  title: Народна пісня
  passage: Ой у [___:1] та й при [___:2]...
  blanks:
    - id: 1
      answer: лузі
      options:
        - лузі
        - полі
    - id: 2
      answer: долині
      options:
        - долині
        - горі

- type: match-up
  title: Фольклорна термінологія
  pairs:
    - left: веснянка
      right: spring song
    - left: колядка
      right: Christmas carol
```

---

### Activity Examples (Conceptual)

*Note: These activities must be implemented in YAML.*

1. **Folk Song Analysis (cloze):** Fill in the blanks in a song.
2. **Terminology Matching (match-up):** Match phrase to meaning.
3. **Regional Variation (group-sort):** Sort by region.
4. **Reading Comprehension (quiz):** Test understanding of text.

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

---

## Content Structure Note

### Vocabulary & Activities
**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:
- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

The build system will inject these sections at build time.
**Example `vocabulary/c1-121-folk-songs.yaml`:**

```yaml
items:
- lemma: веснянка
  ipa: /vɛsˈnʲɑnkɑ/
  translation: spring song
  pos: ім. (ж.р.)
  note: обрядова пісня
- lemma: колядка
  ipa: /kɔˈlʲɑdkɑ/
  translation: carol
  pos: ім. (ж.р.)
  note: пісня на Різдво
```

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/c1-module-template.md`
- **C1 Curriculum Plan:** `docs/l2-uk-en/C1-CURRICULUM-PLAN.md` (M121-145 specifications)
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
