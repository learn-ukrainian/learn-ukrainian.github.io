# C2 Professional Module Template

**Purpose:** Reference template for C2 professional specialization modules (M46-75: Meta-Skills, Terminology Acquisition, Professional Document Production)

**Based on:** `c2-module-template.md` — inherits all C2 quality standards

**Related Issue:** [#307](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/307)

---

## ⚠️ BEFORE WRITING: Research Meta-Skills Content First!

**CRITICAL:** C2 professional modules teach transferable meta-skills, not domain jargon. However, authentic examples still require research.

### Research Strategy

**Step 1: Find Terminology Acquisition Examples**
```
WebSearch: "юридична термінологія українською словник"
WebSearch: "медична термінологія українською"
WebSearch: "термінологічний словник [domain]"
```

**Step 2: Professional Document Standards**
```
WebSearch: "ДСТУ 4163 діловодство" (document standards)
WebSearch: "офіційно-діловий стиль приклади"
WebFetch: zakon.rada.gov.ua/laws/show/[standard]
```

### Key Resources for Meta-Skills

| Meta-Skill | Resources |
|------------|-----------|
| **Terminology Acquisition** | sum.in.ua (dictionaries) |
| **Document Production** | zakon.rada.gov.ua (ДСТУ standards) |
| **Professional Reading** | nbuv.gov.ua, domain journals |
| **Cross-Domain Communication** | Popular science sites, TED-Ed UA |

### Anti-Hallucination Rules

1. **NEVER invent Ukrainian word formation patterns** — verify with etymological dictionaries
2. **NEVER generate professional document structures from memory** — check ДСТУ standards
3. **Domain terminology examples must be real** — verify in specialized dictionaries
4. **Cross-domain simplification examples need real sources** — find actual popularizations
5. **When in doubt, mark as [NEEDS VERIFICATION]** — flag for review

> 💡 **Tip:** The goal is teaching HOW to acquire terminology, not specific jargon. Use real examples to illustrate meta-strategies.

---

<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Професійний контекст
  - Підсумок
  - Потрібно більше практики?
  pedagogy: Native
  min_word_count: 5000
  required_callouts: []
  description: C2 professional modules for workplace Ukrainian
-->

---

## Quick Reference Checklist

Before submitting a C2 professional module, verify all items from `c2-module-template.md` PLUS:

### Professional-Specific Requirements (Seminar Style)

- [ ] **Seminar pedagogy:** Production-focused, not drill-focused
- [ ] **Activities:** 3-9 production activities (reading, essay-response, critical-analysis)
- [ ] **Essay requirements:** 300-500 words per essay (with Model Answer)
- [ ] **Meta-skills focus:** Transferable professional skills, not domain jargon
- [ ] **Universal templates:** Patterns applicable to ANY professional field
- [ ] **Professional immersion:** 100% Ukrainian in professional scenarios
- [ ] **Document production:** Professional documents with Model Answers
- [ ] **Self-directed learning:** Strategies for acquiring domain vocabulary
- [ ] **Cross-domain communication:** Explaining to non-specialists

---

## Module Types in C2.3

### Meta-Skills Foundation (M46-55)

| Modules | Focus | Skills |
|---------|-------|--------|
| M46 | Professional Language Overview | Understanding specialization |
| M47-48 | Terminology Acquisition I-II | Learning new terms systematically |
| M49-50 | Reading Professional Texts | Comprehending specialized texts |
| M51-53 | Professional Document Writing | Reports, proposals, presentations |
| M54 | Professional Oral Communication | Presentations, meetings |
| M55 | C2.3 Midpoint Checkpoint | Skills assessment |

### Professional Communication (M56-60)

| Modules | Focus | Skills |
|---------|-------|--------|
| M56 | Professional Correspondence | Emails, letters, formal requests |
| M57 | Professional Discussions | Debates, negotiations |
| M58 | Cross-Domain Communication | Explaining to non-specialists |
| M59 | Professional Research Skills | Finding and evaluating sources |
| M60 | Building Domain Expertise | Self-directed specialization |

### Domain Introduction (M61-70)

| Modules | Focus | Content |
|---------|-------|---------|
| M61-65 | Legal Ukrainian I-V | Contracts, court procedures, legal writing |
| M66-70 | Medical Ukrainian I-V | Patient communication, documentation |

### Portfolio & Integration (M71-75)

| Modules | Focus |
|---------|-------|
| M71-72 | Professional Portfolio |
| M73 | Professional Identity |
| M74 | C2.3 Review |
| M75 | C2.3 Checkpoint |

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

## Module Structure (Professional-Specific)

### 1. Frontmatter

```yaml
---
module: c2-0XX
title: "[Professional Topic]: Ukrainian Title"
phase: "C2.3 [Professional Specialization]"
pedagogy: "Professional Simulation"  # or "Meta-Skills"
register: "офіційно-діловий"  # or "науковий" for technical
tags:
  - professional
  - [meta-skills, terminology, documents, communication]
  - [domain if applicable: legal, medical, etc.]
grammar:
  - "Professional document conventions"
  - "Formal register markers"
vocabulary_focus:
  - "Професійна термінологія"
  - "Ділова комунікація"
---
```

### 2. Professional Content Structure

#### Section 1: Meta-Skills Framework — 400-500 words

```markdown
# [Professional Topic]: Універсальні навички

> 🎯 **Чому це важливо?**
>
> [Explain transferable value across ALL professional domains]
> [How this skill applies regardless of specialization]
> [Why C2 learners need this for any career]

## Теоретична база

### Принцип: [Core principle]

[Explanation of transferable meta-skill — 150-200 words]

**Застосування в різних галузях:**

| Галузь | Приклад застосування |
|--------|---------------------|
| Юриспруденція | [Example] |
| Медицина | [Example] |
| IT/Технології | [Example] |
| Бізнес | [Example] |

> 💡 **Універсальність**
>
> [Why this skill works across domains]
```

#### Section 2: Terminology Acquisition (if applicable) — 400-500 words

```markdown
## Стратегії опанування термінології

### Аналіз словотвору

**Патерни українського словотвору:**

| Елемент | Значення | Приклади |
|---------|----------|----------|
| -ість | абстрактна якість | відповідальність, компетентність |
| -ання/-ення | процес | дослідження, впровадження |
| -ач/-ник | діяч | дослідник, виконавець |
| без- | відсутність | безкоштовний, безстроковий |
| пере- | повторення/зміна | перегляд, переоцінка |

### Контекстуальне виведення

[How to infer meaning from context — 100-150 words]

**Приклад:**
> "Позивач звернувся до суду з метою стягнення заборгованості."

**Аналіз:**
- "позивач" — той, хто позивається (суфікс -ач = діяч)
- "стягнення" — дія стягування (юридичний контекст = отримання боргу)

### Ресурсна стратегія

**Рекомендовані ресурси:**
1. Термінологічні словники за галузями
2. Офіційні глосарії державних установ
3. Наукові публікації з визначеннями

> 🔍 **Метамовна свідомість**
>
> [How professionals think about terminology]
```

#### Section 3: Professional Documents — 600-800 words

```markdown
## Професійні документи

### Універсальна структура: [Document type]

**Компоненти:**

1. **Заголовок/Назва**
   - Формат: [Specific format]
   - Приклад: [Example]

2. **Вступна частина**
   - Мета документа
   - Контекст

3. **Основна частина**
   - Логічна структура
   - Чіткі розділи

4. **Заключна частина**
   - Висновки/рекомендації
   - Заклик до дії (якщо потрібно)

5. **Формальності**
   - Підпис, дата
   - Реквізити

---

### Зразок документа

**Тип:** [Document type]
**Контекст:** [Professional context]

> [Complete 300-400 word model document showing:
> - Correct structure
> - Appropriate register
> - Professional conventions
> - Native-like formulations]

---

### Шаблон

```
[Blank template with placeholders showing structure]
```

---

### Завдання: Створіть документ

**Ситуація:**
[Professional scenario — 50-100 words]

**Вимоги:**
1. Дотримуйтесь структури
2. Використовуйте формальний регістр
3. 200+ слів

**Зразок відповіді:**

> [Complete model answer for the scenario]

**Коментар:**
> [100+ word explanation of document conventions used]
```

#### Section 4: Professional Communication — 400-500 words

```markdown
## Професійна комунікація

### Сценарій: [Communication type]

**Контекст:**
[Professional scenario — 50-100 words]

---

### Діалог/Презентація

> [Complete professional dialogue or presentation script:
> - Appropriate register
> - Professional conventions
> - Turn-taking/interruption norms
> - 200-300 words]

---

### Аналіз комунікативних стратегій

| Стратегія | Приклад | Функція |
|-----------|---------|---------|
| Пом'якшення | "Можливо, варто розглянути..." | Ввічливість |
| Уточнення | "Якщо я правильно розумію..." | Перевірка |
| Підсумок | "Отже, ми домовилися, що..." | Закріплення |

> 🗣️ **Культурні конвенції**
>
> [Ukrainian professional communication norms]
```

---

## Professional-Specific Activities

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/c2-46-meta-skills.yaml`:**

```yaml
- type: fill-in
  title: Термінологія за контекстом
  instruction: Визначте значення терміна з контексту.
  items:
    - sentence: Позивач вимагає [___] моральної шкоди.
      answer: відшкодування
      options:
        - відшкодування
        - нанесення
```

---

### Terminology Acquisition

```markdown
## fill-in: Термінологія за контекстом

Визначте значення терміна з контексту:

1. "Реципієнт трансплантата потребує імуносупресивної терапії."
   [___] — це людина, яка...
   - [x] отримує орган від донора
   - [ ] дарує орган
   - [ ] проводить операцію
   - [ ] призначає лікування
   > "Реципієнт" від лат. recipere = отримувати. Контекст "трансплантата" підтверджує.

2. "Позивач вимагає відшкодування моральної шкоди."
   [___] — це особа, яка...
   - [x] подає позов до суду
   - [ ] захищається в суді
   - [ ] виносить рішення
   - [ ] представляє інтереси сторони
   > Суфікс -ач = діяч; "позивати" = подавати позов.

[12+ terminology inference items]
```

### Professional Document Production

```markdown
## production: Діловий документ

**Завдання:**
Напишіть [document type] для ситуації:

[Professional scenario — 100-150 words]

**Вимоги:**
1. Структура: [specific structure]
2. Регістр: офіційно-діловий
3. Обсяг: 200+ слів
4. Формальності: [specific formalities]

**Зразок відповіді:**

> [Complete 200+ word model document]

**Рубрика:**

| Критерій | C2 очікування |
|----------|---------------|
| Структура | Чітка, логічна, повна |
| Регістр | Бездоганно офіційний |
| Формулювання | Типові ділові конструкції |
| Формальності | Усі необхідні елементи |
```

### Cross-Domain Communication

```markdown
## transform: Популяризація

Перепишіть фаховий текст для неспеціалістів:

**Оригінал (фаховий):**
> [150-200 word technical/specialized text]

**Цільова авдиторія:** Широка публіка

**Зразок відповіді:**

> [150-200 word accessible version showing:
> - Simplified terminology
> - Added explanations
> - Analogies and examples
> - Maintained accuracy]

**Аналіз стратегій:**
> [100+ word explanation of simplification strategies used]
```

### Professional Discussion

```markdown
## cloze: Ділова зустріч

Заповніть пропуски у діалозі:

> А: Доброго дня, колеги. {Сьогодні|Завтра|Вчора} ми розглянемо стратегію на наступний квартал.
> Б: Якщо {дозволите|можна|ласка}, я хотів би уточнити щодо термінів реалізації.
> А: Гарне {запитання|питання|уточнення}. Терміни такі: перший етап — до кінця місяця.
> Б: Дякую. {Підсумовуючи|Отже|Тож}, ми домовились про три ключові кроки.
> А: Саме так. Дякую за увагу. Чи є {запитання|питання|уточнення}?

> [!explanation] Логіка ділової зустрічі: вступ → обговорення → підсумок → завершення.
```

---

## Engagement Boxes for Professional Modules

```markdown
> 💡 **Універсальність**
>
> [How this skill applies across professional domains]

> 🏢 **Професійна практика**
>
> [Real-world professional application]

> 🔍 **Метамовна свідомість**
>
> [How professionals think about language]

> ⚖️ **Регістрова точність**
>
> [Formal vs. informal professional language]

> 🌍 **Культурні конвенції**
>
> [Ukrainian professional culture norms]

> 📋 **Шаблон**
>
> [Document template for reference]

> 🎓 **Самонавчання**
>
> [Strategies for self-directed professional learning]
```

---

---

## Content Structure Note

### Vocabulary & Activities

**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:
- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

The build system will inject these sections at build time.
**Example `vocabulary/c2-46-meta-skills.yaml`:**

```yaml
items:
- lemma: термін
  ipa: /tɛrmin/
  translation: term
  pos: ім.
  note: фахове слово
- lemma: галузь
  ipa: /ɦɑluzʲ/
  translation: field/domain
  pos: ім.
  note: сфера діяльності
```

---

## Key Principle: Meta-Skills, Not Jargon

### What C2.3 Teaches

✅ **Correct approach:**
- How to acquire terminology in ANY field
- Universal document structures
- Professional communication patterns
- Self-directed learning strategies

❌ **Incorrect approach:**
- Memorizing legal jargon lists
- Medical terminology drills
- IT-specific vocabulary only

### Rationale

The Ukrainian State Standard 2024 requires C2 learners to handle "any professional field." Rather than teaching specific domains (which would require dozens of tracks), C2.3 teaches **transferable meta-skills** that work in any profession.

**Example:**
Instead of teaching "судове рішення = court decision," teach:
1. How to identify word roots (суд + -ов- + рішення)
2. How to use context clues
3. How to find reliable glossaries
4. How to verify meaning

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/c2-module-template.md`
- **C2 Curriculum Plan:** `docs/l2-uk-en/C2-CURRICULUM-PLAN.md` (M46-75 specifications)
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
