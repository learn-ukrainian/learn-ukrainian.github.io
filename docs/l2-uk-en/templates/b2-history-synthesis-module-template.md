# B2 History Synthesis Module Template

**Purpose:** Reference template for B2 Ukrainian history synthesis modules (M83, M108, M119, M125, M131)

**Based on:** `history-module-template.md` — inherits decolonization standards

**Related Issues:** [#332](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/332)

> **Note:** Regular history modules (M71-82, M84-107, etc.) use `history-module-template.md` instead.

<!--
TEMPLATE_METADATA:
  required_sections:
  - Огляд періоду
  - Ключові теми
  - Аналіз
  - Підсумок
  - Потрібно більше практики?
  pedagogy: CBI
  min_word_count: 5000
  required_callouts:
  - myth-buster
  - history-bite
  description: B2 history synthesis modules connect multiple periods or themes
-->

---

## What is a Synthesis Module?

Synthesis modules **culminate** each historical era with thematic analysis rather than quiz-style testing. They connect cause/effect relationships across multiple modules and link historical events to modern Ukrainian identity.

### Key Differences from Standard Checkpoint

| Aspect | Standard Checkpoint | Synthesis Module |
|--------|---------------------|------------------|
| **Focus** | Testing grammar/vocab recall | Analyzing historical themes |
| **Format** | Quiz, gap-fill, MCQ | Essay, timeline, discussion |
| **New content** | Minimal | Extended synthesis text (500+ words) |
| **Assessment** | Right/wrong answers | Argumentative quality |
| **Flow** | Interrupts narrative | Culminates narrative arc |
| **Vocabulary** | Review only | Review in new contexts |

---

## Synthesis Modules Overview

| Module | Title | Era Covered | Modules Synthesized |
|--------|-------|-------------|---------------------|
| M83 | Синтез: Від витоків до литовської доби | Origins → Lithuania | M71-82 (12 modules) |
| M108 | Синтез: Козацька спадщина | Cossack Era | M84-107 (24 modules) |
| M119 | Синтез: Століття випробувань | 20th Century Trauma | M109-118 (10 modules) |
| M125 | Синтез: Відновлення державності | Independence Era | M120-124 (5 modules) |
| M131 | Синтез: Війна за існування | 2014-Present War | M126-130 (5 modules) |

---

## Quick Reference Checklist

Before submitting a B2 synthesis module, verify:

### Synthesis-Specific Requirements

- [ ] **CBI pedagogy:** Content-Based Instruction with Thematic Analysis
- [ ] **Era overview:** 500+ word synthesis text connecting ALL modules in era
- [ ] **Chronology activity:** Timeline reconstruction (12+ events)
- [ ] **Era vocabulary:** Review of 25+ key terms from era (NOT new vocabulary)
- [ ] **Essay task:** 250-400 word analytical prompt with model answer
- [ ] **Present connection:** Link to modern Ukraine (post-2014/2022)
- [ ] **Decolonization lens:** Ukraine-centric perspective throughout
- [ ] **Immersion:** 100% Ukrainian (English only in vocabulary translations)
- [ ] **Word count:** 5000+ words per config.py
- [ ] **Activities:** 10-12 activities (fewer than regular modules, more analytical)

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

## Module Structure (Synthesis-Specific)

### 1. Frontmatter

```yaml
---
module: b2-XX
title: "Синтез: [Era Title]"
phase: "B2.3 [Ukrainian History]"
pedagogy: "CBI"
register: "публіцистичний"
tags:
  - history
  - synthesis
  - [era-tag]
grammar:
  - "Analytical writing"
  - "Cause-effect structures"
vocabulary_focus:
  - "Era-specific terminology review"
  - "Historical argumentation"
objectives:
  - "Синтезувати знання з модулів [XX]-[YY]"
  - "Аналізувати причинно-наслідкові зв'язки в історичному контексті"
  - "Формулювати аргументовані висновки про історичні події"
vocabulary_count: 30  # Must match count in vocabulary/{slug}.yaml
---
```

### 2. Era Overview Section — 500+ words

```markdown
# Синтез: [Era Title]

> 🎯 **Чому це важливо?**
>
> [Explain significance of this era for Ukrainian identity]
> [Preview the synthesis: what themes connect the modules?]
> [Frame decolonization perspective for the entire era]

## Узагальнення епохи: [Era Name]

### Вступ

[100-150 words: Opening that frames the era as a whole]

### Основні теми епохи

**Тема 1: [Theme Name]**

[150-200 words connecting multiple modules through this theme]
[Reference specific events from M[XX], M[YY], M[ZZ]]

**Тема 2: [Theme Name]**

[150-200 words connecting multiple modules through this theme]

**Тема 3: [Theme Name]**

[150-200 words connecting multiple modules through this theme]

### Причинно-наслідкові зв'язки

[100-150 words explicitly connecting cause → effect across the era]

> 🌍 **Сучасна перспектива**
>
> [How does understanding this era help us understand today's Ukraine?]
```

### 3. Chronology Section

```markdown
---

## Хронологія: [Era Name]

Розставте події в хронологічному порядку та визначте їхній зв'язок.

### Ключові дати епохи

| Рік | Подія | Значення |
|-----|-------|----------|
| [year] | [event from M71] | [brief significance] |
| [year] | [event from M72] | [brief significance] |
| [year] | [event from M73] | [brief significance] |
[... 12+ events covering ALL modules in era]

### Хронологічне завдання

Розташуйте ці події у правильному порядку:

1. [Event A - scrambled]
2. [Event B - scrambled]
3. [Event C - scrambled]
[... 8-10 events]

> [!solution] Правильний порядок
> 1. [Correct first event] ([year])
> 2. [Correct second event] ([year])
> [...]

> 💡 **Чи знали ви?**
>
> [Interesting chronological fact — e.g., what events happened simultaneously in Europe?]
```

### 4. Era Vocabulary Review Section

```markdown
---

## Словник епохи: [Era Name]

Ці терміни з модулів [XX]-[YY] є ключовими для розуміння епохи.

### Політична лексика

| Слово | Значення | Контекст епохи |
|-------|----------|----------------|
| **[term1]** | [definition in Ukrainian] | [how it applies to this era] |
| **[term2]** | [definition in Ukrainian] | [how it applies to this era] |
[... 8-10 political terms]

### Соціально-культурна лексика

| Слово | Значення | Контекст епохи |
|-------|----------|----------------|
| **[term1]** | [definition in Ukrainian] | [how it applies to this era] |
[... 8-10 socio-cultural terms]

### Історіографічна лексика

| Слово | Значення | Контекст епохи |
|-------|----------|----------------|
| **[term1]** | [definition in Ukrainian] | [how it applies to this era] |
[... 5-8 historiographical terms]

### Застосування в контексті

Заповніть пропуски словами з таблиць вище:

1. [Sentence with blank using term1]
   > [!answer] [term1]

2. [Sentence with blank using term2]
   > [!answer] [term2]

[... 8-10 contextual exercises]
```

### 5. Analytical Essay (YAML-ONLY)

**CRITICAL: DO NOT include an `## Есе` section in the markdown file.** This section is defined exclusively in `activities/{slug}.yaml` as an `essay-response` activity.

#### Essay Requirements (for YAML `model_answer`):

1. **Word Count:** 300-400 words.
2. **Structure:** Thesis → 2 Arguments with historical evidence → Conclusion with modern connection.
3. **Perspective:** Must maintain a decolonization lens.

#### Useful Argumentation Phrases (Use in YAML `model_answer`):

| Function | Expressions |
|---------|--------|
| Thesis | На мою думку... / Я вважаю, що... / Очевидно, що... |
| Argument | По-перше... / По-друге... / Крім того... |
| Example | Наприклад... / Яскравим прикладом є... / Це підтверджує... |
| Contrast | Однак... / З іншого боку... / Незважаючи на це... |
| Conclusion | Отже... / Таким чином... / Підсумовуючи... |

### 6. Connection to Present Section

```markdown
---

## Зв'язок із сьогоденням

### Як ця епоха формує сучасну Україну?

[200-300 words connecting historical era to post-2014/2022 context]

**Політичний вимір:**
[How political patterns from this era appear today]

**Культурний вимір:**
[How cultural elements from this era persist]

**Ідентичність:**
[How this era shapes Ukrainian national identity]

### Дискусійні питання

Обговоріть у групі або поміркуйте самостійно:

1. [Discussion question linking past to present]
2. [Discussion question about modern relevance]
3. [Discussion question about decolonization]

> 🌍 **Реальне життя**
>
> [Concrete example of how this history appears in daily Ukrainian life today]
> [Reference to current events, memorials, place names, etc.]
```

### 7. Summary Section

```markdown
---

# Підсумок

## Ключові висновки епохи

| Аспект | Основний висновок |
|--------|-------------------|
| Політика | [One-sentence political conclusion] |
| Культура | [One-sentence cultural conclusion] |
| Ідентичність | [One-sentence identity conclusion] |
| Спадщина | [One-sentence legacy conclusion] |

## Модулі цієї епохи

| Модуль | Тема | Ключова подія |
|--------|------|---------------|
| M[XX] | [Title] | [Key event] |
| M[YY] | [Title] | [Key event] |
[... all modules in era]

## Що далі?

[Preview of next historical era and its connection to this one]

> ✅ **Самоперевірка**
>
> Чи можете ви:
> - [ ] Пояснити основні теми епохи [Era Name]?
> - [ ] Розташувати ключові події в хронологічному порядку?
> - [ ] Написати аргументоване есе про цю епоху?
> - [ ] Пов'язати історичні події із сучасною Україною?
>
> Якщо так — ви готові до наступної епохи!
```

### 8. Vocabulary Section

**CRITICAL:** Vocabulary must be defined in `vocabulary/{slug}.yaml`. Do NOT embed a vocabulary table in Markdown.

**Example `vocabulary/b2-83-synthesis.yaml`:**

```yaml
items:
- lemma: синтез
  ipa: /sɪnˈtɛz/
  translation: synthesis
  pos: ім.
  note: об'єднання знань
```

---

## Synthesis-Specific Activities

### Activity Mix (10-12 activities)

Unlike regular modules (14+ activities), synthesis modules have fewer but more analytical activities:

| Activity Type | Count | Purpose |
|---------------|-------|---------|
| **quiz** | 2 | Test understanding of themes and connections |
| **match-up** | 2 | Connect events, figures, consequences |
| **group-sort** | 1 | Categorize by theme, period, or significance |
| **fill-in** | 2 | Vocabulary in context |
| **unjumble** | 1 | Chronological ordering |
| **cloze** | 1 | Extended synthesis passage |
| **select** | 1 | Multiple correct answers for complex questions |
| **error-correction** | 1-2 | Historical and linguistic accuracy |

### Activity Design Principles

**1. Test SYNTHESIS, not recall:**
```markdown
## quiz: Тематичний аналіз

1. Яка спільна тема об'єднує події в модулях M71-M75?
   - [ ] Релігійні конфлікти
   - [x] Формування державності
   - [ ] Економічний розвиток
   - [ ] Культурне піднесення
   > Усі ці модулі показують різні аспекти державотворення.
```

**2. Test CONNECTIONS, not facts:**
```markdown
## match-up: Причини та наслідки

| Подія | Наслідок |
|-------|----------|
| Хрещення Русі | Культурна інтеграція з Європою |
| Монгольська навала | Перенесення центру на захід |
| Люблінська унія | Посилення полонізації |
```

**3. Test ARGUMENTATION, not memorization:**
```markdown
## select: Аргументи для есе

Які з цих тверджень можна використати як аргументи в есе про роль козацтва?

- [x] Козацтво створило традицію виборної влади
- [x] Січ була прикладом військової демократії
- [ ] Козаки підтримували абсолютну монархію
- [x] Козацький міф формує сучасну ідентичність
```

---

## Example Essay Prompts by Synthesis Module

### M83: Від витоків до литовської доби

**Prompt 1:** Порівняйте роль Київської Русі та Галицько-Волинського князівства у збереженні української державності.

**Prompt 2:** Як монгольська навала змінила вектор українського історичного розвитку?

**Prompt 3:** Чи можна вважати литовський період "золотою добою" для українських земель?

### M108: Козацька спадщина

**Prompt 1:** Порівняйте політичні проекти Богдана Хмельницького та Івана Мазепи.

**Prompt 2:** Як Переяславська угода вплинула на долю української державності?

**Prompt 3:** Чому козацький міф залишається важливим для сучасної української ідентичності?

### M119: Століття випробувань

**Prompt 1:** Порівняйте спроби створення української держави в 1918 та 1991 роках.

**Prompt 2:** Як Голодомор вплинув на українську національну свідомість?

**Prompt 3:** Чому XX століття називають "століттям випробувань" для України?

### M125: Відновлення державності

**Prompt 1:** Які уроки з подій 1991-2013 років є актуальними для сучасної України?

**Prompt 2:** Як Помаранчева революція змінила політичну культуру України?

**Prompt 3:** Чому Революція Гідності стала поворотним моментом в історії України?

### M131: Війна за існування

**Prompt 1:** Як російська агресія змінила українську національну ідентичність?

**Prompt 2:** Порівняйте українську боротьбу 2014-2022 з історичними прикладами національного спротиву.

**Prompt 3:** Яку роль відіграє деколонізація у сучасній війні за незалежність?

---

## Model Answer Format

Each synthesis module must include ONE complete model essay (300-400 words) demonstrating:

```markdown
### Зразок есе

**Тема:** [Full essay prompt]

---

**Вступ**

[Thesis statement: clear position on the question]
[Brief preview of arguments]

**Аргумент 1**

[Topic sentence]
[Historical evidence from the era]
[Analysis connecting evidence to thesis]

**Аргумент 2**

[Topic sentence]
[Historical evidence from the era]
[Analysis connecting evidence to thesis]

**Висновок**

[Restatement of thesis]
[Connection to modern Ukraine]
[Final thought on significance]

---

*Кількість слів: ~350*

**Аналіз зразка:**
- ✅ Чітка теза
- ✅ Два аргументи з доказами
- ✅ Зв'язок із сучасністю
- ✅ Деколонізаційна перспектива
```

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/history-module-template.md`
- **B2 Curriculum Plan:** `docs/l2-uk-en/B2-CURRICULUM-PLAN.md`
- **Decolonization guidelines:** Referenced in history template
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`
- **Checkpoint comparison:** `docs/l2-uk-en/templates/b1-checkpoint-module-template.md`

---

## Clean MD Architecture Note

### Activities, Vocabulary, and External Resources

**CRITICAL:** Do NOT add `## Activities`, `## Vocabulary`, or `## External Resources` headers to the Markdown file. These sections are automatically injected by the build system from the corresponding YAML sidecars:

- `activities/{slug}.yaml` → `## Activities` section
- `vocabulary/{slug}.yaml` → `## Vocabulary` section
- `docs/resources/external_resources.yaml` (filtered by `module_id`) → `## External Resources` section

The module structure follows **Clean MD architecture**: Markdown contains narrative content only, YAML sidecars contain structured data.

---

**Last Updated:** 2025-12-30
**Template Version:** 1.0

**Changelog:**
- v1.0 (2025-12-30): Initial creation per Issue #332
