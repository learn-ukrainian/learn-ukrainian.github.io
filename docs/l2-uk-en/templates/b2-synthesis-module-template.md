# B2 Synthesis Module Template

**Purpose:** Reference template for B2.3 History Synthesis modules (M83, M107, M119, M125, M131)

**Based on:** `b2-history-module-template.md` — inherits history-specific requirements

**Related Issue:** [#332](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/332)


<!--
TEMPLATE_METADATA:
  required_sections:
  - Огляд
  - Інтеграція
  - Summary|Підсумок
  - Need More Practice?
  pedagogy: TTT
  min_word_count: 1800
  required_callouts: []
  description: B2 synthesis modules integrate grammar, vocabulary, and skills
-->

---

## What Are Synthesis Modules?

Synthesis modules replace traditional checkpoints in the B2.3 History track. Unlike grammar checkpoints that test recall of rules, **Synthesis modules test historical analysis, argumentation, and cross-era connections**.

| Aspect | Traditional Checkpoint | Synthesis Module |
|--------|----------------------|------------------|
| Focus | Recall of facts/rules | Analysis & argumentation |
| Question type | "What happened in 1654?" | "How does Pereiaslav relate to 2014?" |
| Skills tested | Memory, recognition | Synthesis, evaluation, comparison |
| Content | Review of covered material | Cross-era thematic connections |
| Pedagogy | TTT (Test-Teach-Test) | CBI (Content-Based Instruction) |

---

## B2.3 Synthesis Module Positions

| Module | Title | Covers | Focus |
|--------|-------|--------|-------|
| **M83** | Синтез: Витоки | M71-82 | Origins → Commonwealth themes |
| **M107** | Синтез: Козаччина — Імперія | M84-106 | Cossack identity, imperial resistance |
| **M119** | Синтез: Трагедії XX ст. | M108-118 | Genocides, cultural destruction, survival |
| **M125** | Синтез: Шлях до Волі | M120-124 | Independence, Euromaidan, identity |
| **M131** | Синтез: Історія B2 | M71-130 | Full B2 history synthesis & capstone |

---

## Quick Reference Checklist

Before submitting a B2 Synthesis module, verify:

### Synthesis-Specific Requirements
- [ ] **CBI pedagogy:** Content-Based Instruction with Synthesis Arc
- [ ] **Thematic approach:** NOT chronological recap — cross-era thematic connections
- [ ] **Analysis activities:** Primary source comparison, historiographical analysis
- [ ] **Decolonization synthesis:** Consolidate myth-busting from covered modules
- [ ] **Modern connections:** Link historical themes to contemporary Ukraine
- [ ] **Argument writing:** Include structured argument production task
- [ ] **NO new content:** Only synthesize material from covered modules

### Inherited from History Template
- [ ] **Primary sources (≥3):** From different modules/eras for comparison
- [ ] **100% Ukrainian immersion:** English only in vocabulary translations
- [ ] **Word count:** 1200+ words (synthesis narrative, not teaching)
- [ ] **Activities:** 14+ with analysis focus
- [ ] **NO DIALOGS:** Synthesis modules are analysis-centric

---

## Module Structure (Synthesis-Specific)

### 1. Frontmatter

```yaml
---
module: b2-XX
title: "Синтез: [Theme/Era]"
phase: "B2.3 [Ukrainian History] Synthesis"
pedagogy: "CBI"  # Content-Based Instruction
register: "публіцистичний"
tags:
  - history
  - synthesis
  - checkpoint
  - [era-tags from covered modules]
grammar:
  - "Historical narrative synthesis"
  - "Argumentative writing structures"
objectives:
  - "Learner can synthesize historical themes across eras"
  - "Learner can construct historical arguments with evidence"
  - "Learner can identify continuities in Ukrainian history"
vocabulary_count: 25  # Must match count in vocabulary/{slug}.yaml
---
```

### 2. Synthesis Arc Structure

#### Section 1: Thematic Hook — 200-300 words

```markdown
# Синтез: [Theme]

> 🎯 **Чому це важливо?**
>
> [Frame the synthesis theme — what connects these modules?]
> [Why does this pattern matter for understanding Ukraine?]
> [Preview the cross-era connections to explore]

## Ключова тема

[Introduce the overarching theme that connects covered modules]

**Що об'єднує M[XX]-M[YY]?**

| Ера | Подія | Зв'язок з темою |
|-----|-------|-----------------|
| [Era 1] | [Event from M__] | [Connection] |
| [Era 2] | [Event from M__] | [Connection] |
| [Era 3] | [Event from M__] | [Connection] |
```

#### Section 2: Thematic Analysis — 600-800 words

```markdown
## Тематичний аналіз

### Патерн 1: [Pattern Name]

[200-250 words analyzing how this pattern appears across eras]

> 📜 **Порівняння джерел**
>
> **Джерело A (Ера X):** "[Quote from M__]"
> **Джерело B (Ера Y):** "[Quote from M__]"
>
> **Аналіз:** [Compare/contrast the sources]

### Патерн 2: [Pattern Name]

[200-250 words on second pattern]

### Сучасні паралелі

[200 words connecting historical patterns to modern Ukraine]

> 🌍 **2022 і далі**
>
> [How do these historical patterns illuminate current events?]
```

#### Section 3: Decolonization Synthesis — 200-300 words

```markdown
## Деколонізаційний синтез

**Міфи, які ми розібрали (M[XX]-M[YY]):**

| Міф | Де розібрали | Ключовий аргумент |
|-----|--------------|-------------------|
| [Myth 1] | M__ | [Counter-evidence] |
| [Myth 2] | M__ | [Counter-evidence] |
| [Myth 3] | M__ | [Counter-evidence] |

### Системна картина

[How do these myths connect? What is Russia's historiographical strategy?]

> ⚠️ **Деколонізація**
>
> [Synthesis statement on the overarching colonial narrative and why it's false]
```

#### Section 4: Historiographical Reflection — 150-200 words

```markdown
## Історіографічна рефлексія

**Як історія формує ідентичність:**

[Reflection on how understanding these periods shapes Ukrainian identity]

**Джерела для подальшого вивчення:**

- [Ukrainian historian/source 1]
- [Ukrainian historian/source 2]
- [Primary source collection]
```

---

## Synthesis-Specific Activities

### CRITICAL: Language Practice, Not Content Testing

<critical>

**Even in synthesis modules, activities test LANGUAGE SKILLS, not historical recall.**

The lesson content teaches cross-era analysis. Activities practice Ukrainian reading comprehension, vocabulary, and grammar using the synthesis content as context.

**✅ CORRECT:** "Згідно з текстом модуля, який патерн автор виділяє?" (requires reading the Ukrainian synthesis)
**❌ WRONG:** "Який патерн об'єднує ці події?" (tests recall, not language)

**Key Test:** Can the learner answer without reading the Ukrainian synthesis text? If yes, rewrite.

</critical>

### 1. Cross-Era Reading Comprehension (quiz)

**Purpose:** Test comprehension of the synthesis text, NOT recall of historical facts.

```markdown
## quiz: Розуміння синтезу

> Відповідайте на питання на основі прочитаного тексту модуля.

1. Згідно з текстом, який патерн автор виділяє між подіями 1654 та 1994 років?
   - [ ] Обидва були військовими союзами
   - [x] Обидва показують небезпеку довіри до зовнішніх гарантій
   - [ ] Обидва були підписані під примусом
   - [ ] Обидва стосувалися територіальних питань
   > Текст наголошує на повторюваності ситуацій, коли Україна довіряла гарантіям безпеки.

2. Як автор формулює основну тезу модуля?
   - [ ] Україна завжди була частиною Росії
   - [x] Безперервність української державності простежується крізь епохи
   - [ ] Козацька доба не мала впливу на сьогодення
   - [ ] Історія не має значення для сучасності
   > У вступі автор чітко формулює цю тезу.

[All questions must begin with "Згідно з текстом" or reference specific text sections]
```

### 2. Source Linguistic Analysis (select)

**Purpose:** Test close reading and linguistic analysis of primary sources.

```markdown
## select: Лінгвістичний аналіз джерел

Прочитайте два джерела з модуля і виберіть усі правильні твердження про мову текстів:

> **Джерело A (XVII ст.):** "[Quote from Cossack era]"
>
> **Джерело B (XX ст.):** "[Quote from Soviet era]"

- [x] Джерело A використовує архаїчну лексику
- [ ] Обидва тексти написані розмовним стилем
- [x] Джерело B має елементи офіційного регістру
- [ ] Лексика обох джерел однакова
- [x] В обох текстах є емоційно забарвлені слова

[Test LINGUISTIC features of sources, not historical interpretation]
```

### 3. Vocabulary in Synthesis Context (fill-in)

**Purpose:** Test analytical vocabulary from module.

```markdown
## fill-in: Аналітична лексика

1. Автор використовує метод [___] для виявлення спільних рис між епохами.
   > [!answer] порівняння
   > [!options] порівняння | опису | цитування | критики
   > Порівняння = comparison (analytical method).

2. У тексті простежується [___] української державницької традиції.
   > [!answer] безперервність
   > [!options] безперервність | переривання | зникнення | занепад
   > Безперервність = continuity.

3. Автор [___] радянський міф про "братні народи".
   > [!answer] спростовує
   > [!options] підтримує | спростовує | ігнорує | повторює
   > Спростовує = refutes.

[Test MODULE VOCABULARY, especially analytical/historiographical terms]
```

### 4. Argument Structure Analysis (cloze)

**Purpose:** Test understanding of argument structure in Ukrainian.

```markdown
## cloze: Структура аргументу

Заповніть пропуски відповідно до структури тексту модуля:

Автор будує аргумент у три етапи. {blank|По-перше|Спочатку|На початку}, він аналізує події Козацької доби. {blank|По-друге|Далі|Потім}, він порівнює їх із подіями XX століття. {blank|Нарешті|Зрештою|На завершення}, він формулює {blank|висновок|тезу|ідею} про безперервність української традиції.

[Test DISCOURSE MARKERS and argument structure, not content]
```

### 5. Grammar in Analytical Text (error-correction)

**Purpose:** Test grammar using synthesis content as context.

```markdown
## error-correction: Граматика в аналітичному тексті

1. Безперервність української державності простежується від козацької доба до сьогодення.
   > [!error] доба
   > [!answer] доби
   > [!options] доба | доби | добі | добою
   > [!explanation] Прийменник "від" вимагає родового відмінка: від чого? → від доби.

2. Історик аналізуючи джерела виявив важливу закономірність.
   > [!error] аналізуючи
   > [!answer] аналізуючи,
   > [!options] аналізуючи | аналізуючи, | аналізував | аналізує
   > [!explanation] Дієприслівниковий зворот відокремлюється комою.

[Focus on GRAMMAR errors in analytical writing style]
```

### Продукція Task with Model Answer

```markdown
## Завдання: Письмовий аргумент

**Тема:** Оберіть ОДНУ тему:

A) Порівняйте два випадки, коли Україна довіряла зовнішнім гарантіям безпеки. Які уроки?

B) Проаналізуйте, як культурний опір допомагав українцям вижити в різні епохи.

**Вимоги:**
- 150-200 слів
- Посилання на ≥2 модулі/епохи
- Використання первинних джерел
- Чіткий аргумент із доказами

---

> [!model-answer] Зразок відповіді (Тема A)
>
> Переяславська угода 1654 року та Будапештський меморандум 1994 року демонструють небезпеку довіри до зовнішніх гарантій безпеки.
>
> У 1654 році козаки під проводом Хмельницького підписали угоду з Московським царством, сподіваючись на захист від Польщі. Як писав сам гетьман: "[цитата з М89]". Однак Москва поступово ліквідувала українську автономію, завершивши це зруйнуванням Січі 1775 року.
>
> Аналогічно, у 1994 році Україна віддала ядерну зброю в обмін на гарантії територіальної цілісності від Росії, США та Великої Британії. Через 20 років Росія анексувала Крим, повністю порушивши меморандум.
>
> Урок: гарантії без механізму примусу — лише слова. Україна навчилася покладатися на власну оборону.
```

---

## Vocabulary for Synthesis Modules

**CRITICAL:** Vocabulary must be defined in `vocabulary/{slug}.yaml`. Do NOT embed a vocabulary table in Markdown.

**Example `vocabulary/b2-XX-synthesis.yaml`:**

```yaml
items:
- lemma: синтез
  ipa: /sɪnˈtɛz/
  translation: synthesis
  pos: ім.
  note: об'єднання ідей
```

---

## Activity Distribution for Synthesis Modules

| Activity Type | Count | Focus |
|--------------|-------|-------|
| **quiz** | 2 | Cross-era synthesis questions |
| **select** | 2 | Source comparison (multi-select) |
| **true-false** | 2 | Myth synthesis |
| **cloze** | 2 | Argument construction |
| **fill-in** | 2 | Historiographical vocabulary |
| **match-up** | 1 | Era ↔ Theme connections |
| **Production** | 1 | Written argument with model |
| **Total** | **14+** | |

**Priority activities for synthesis:** `quiz`, `select`, `cloze`, `true-false`

---

## Common Pitfalls to Avoid

### 1. **Chronological Recap**
- ❌ Problem: "First we studied M71, then M72..."
- ✅ Solution: Thematic synthesis across eras, not module-by-module review

### 2. **Testing Recall Instead of Analysis**
- ❌ Problem: "In what year was Pereiaslav signed?"
- ✅ Solution: "How does Pereiaslav relate to modern Russian policy?"

### 3. **Missing Cross-Era Connections**
- ❌ Problem: Analyzing each era separately
- ✅ Solution: Every question/activity should connect ≥2 eras

### 4. **New Historical Content**
- ❌ Problem: Introducing events not covered in prior modules
- ✅ Solution: Synthesize only what was already taught

### 5. **Weak Decolonization Synthesis**
- ❌ Problem: Just listing myths without showing the pattern
- ✅ Solution: Show how myths connect to systematic colonial narrative

---

## Related Documentation

- **History template:** `docs/l2-uk-en/templates/b2-history-module-template.md`
- **B2 Curriculum Plan:** `docs/l2-uk-en/B2-CURRICULUM-PLAN.md` (M71-131 history progression)
- **Checkpoint design:** `docs/l2-uk-en/templates/b1-checkpoint-module-template.md` (contrast with grammar checkpoints)
- **Decolonization guidelines:** Referenced in B2 curriculum plan

---

## Clean MD Architecture Note

### Activities, Vocabulary, and External Resources

**CRITICAL:** Do NOT add `## Activities`, `## Vocabulary`, or `## External Resources` headers to the Markdown file. These sections are automatically injected by the build system from the corresponding YAML sidecars:

- `activities/{slug}.yaml` → `## Activities` section
- `vocabulary/{slug}.yaml` → `## Vocabulary` section
- `docs/resources/external_resources.yaml` (filtered by `module_id`) → `## External Resources` section

The module structure follows **Clean MD architecture**: Markdown contains narrative content only, YAML sidecars contain structured data.

---

**Last Updated:** 2025-12-29
**Template Version:** 1.0

**Changelog:**
- v1.0 (2025-12-29): Initial creation — replaces traditional checkpoints with analysis-focused synthesis modules per GitHub issue #332
