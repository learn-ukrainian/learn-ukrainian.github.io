# B1 Vocabulary Expansion Module Template

**Purpose:** Reference template for creating B1 vocabulary expansion modules (M51-70: Abstract concepts, Opinions, Discourse markers, Synonymy, Collocations)

**Based on:** B1 Curriculum Plan specifications for Phase B1.5-B1.6 vocabulary modules

**Key Differences from Grammar Template:**

- Less grammar explanation, more lexical depth
- Thematic vocabulary presentation (25-30 words per theme)
- Contextual usage patterns (collocations, synonyms, register)
- More match-up, group-sort, select activities
- Reading-heavy with authentic examples
- Focus on USAGE and CONTEXT, not grammar rules

**Related Issue:** [#284](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/284)

---

## Quick Reference Checklist

Before submitting a B1 vocabulary module, verify:

- [ ] **Word count:** 1500+ words (core prose: explanations, examples, engagement boxes — excludes vocabulary section, activities section, and tables)
- [ ] **Vocabulary:** 25-30 items in 5-column format (Слово | Вимова | Переклад | ЧМ | Примітка)
- [ ] **Thematic organization:** Vocabulary grouped by semantic field or function
- [ ] **Key patterns:** 6-10 usage patterns with authentic examples
- [ ] **Collocations:** Common word combinations explicitly taught
- [ ] **Synonymy:** Related words differentiated by register/nuance
- [ ] **Activities:** 12+ with emphasis on:
  - Match-up (collocations, synonyms)
  - Group-sort (semantic fields, register)
  - Select (multiple correct collocations)
  - Fill-in (contextual usage)
- [ ] **Reading passages:** 2-3 authentic texts using target vocabulary
- [ ] **Engagement boxes:** 5+ boxes with real-world usage
- [ ] **Immersion:** 90-100% Ukrainian (vocabulary taught in context)
- [ ] **Pedagogy:** Level-appropriate complexity

---

## Module Structure Template

### 1. Frontmatter (YAML)

```yaml
---
module: b1-XX
title: 'Ukrainian Title'
subtitle: 'English subtitle'
version: '1.0'
phase: 'B1.5 Vocabulary Expansion I' # or "B1.6 Vocabulary Expansion II"
pedagogy: 'PPP' # Presentation-Practice-Production for vocab modules
duration: 90 # minutes
transliteration: none
tags:
  - vocabulary
  - [thematic-tag] # e.g., abstract, opinions, discourse, synonymy
grammar:
  - 'Vocabulary focus: [theme]'
objectives:
  - 'Learner can use [vocabulary group] in context'
  - 'Learner can distinguish [synonyms/register]'
  - 'Learner can form natural collocations with [key words]'
vocabulary_count: 25 # 25-30 for vocab modules
---
```

**Why these fields:**

- `phase`: "B1.5 Vocabulary Expansion I" (M51-60) or "B1.6 Vocabulary Expansion II" (M61-70)
- `pedagogy`: "PPP" for vocabulary (Present vocabulary → Practice in context → Produce in writing/speaking)
- `vocabulary_count`: 25-30 items (higher density than grammar modules)

---

### 2. Module Title and Motivation Box

```markdown
# Ukrainian Title

> 🎯 **Чому це важливо?**
>
> [2-3 sentences explaining WHY this vocabulary is essential]
> [Show WHERE learners will encounter these words]
> [Connect to real-world communication needs]
```

**Example for Abstract Concepts module:**

```markdown
# Абстрактні концепції: ідеї та думки

> 🎯 **Чому це важливо?**
>
> Щоб брати участь в інтелектуальних дискусіях українською, вам потрібна абстрактна лексика. Ці слова використовуються в академічних текстах, новинах, професійних розмовах та дебатах. Без них ви обмежені лише конкретними темами.
```

**Why this works:**

- Establishes practical value immediately
- Shows WHERE vocabulary is used
- Motivates learners with real-world relevance

---

### 3. Content Sections (1500+ words total)

**Structure for PPP pedagogy:**

#### Section 1: Вступ (Introduction Phase)

- Present target vocabulary in semantic groups
- Show authentic examples in context
- NO translation lists yet — contextual discovery first
- 200-300 words

```markdown
## Вступ

Прочитайте цей уривок з новинної статті:

> У світі виникає все більше **проблем**, пов'язаних з кліматичними змінами. Науковці пропонують різні **рішення**: від використання відновлюваних джерел енергії до зміни способу життя. Однак не всі погоджуються з цими **підходами**. Деякі експерти стверджують, що потрібна радикальна **трансформація** економіки, інші вважають, що достатньо поступових **змін**.

Помітили виділені слова? Це — **абстрактна лексика**. Вона дозволяє говорити про ідеї, процеси та концепції, а не лише про конкретні об'єкти.

У цьому модулі ви навчитеся використовувати 30 таких слів для обговорення ідей, проблем та рішень.
```

**Why this works:**

- Authentic text shows vocabulary in natural context
- Learners discover meaning from context before definitions
- Sets the semantic field clearly

#### Section 2: Лексика (Presentation Phase)

- Present vocabulary in THEMATIC GROUPS (not alphabetical)
- Each group: 6-10 words with collocations
- Tables showing word + common collocations
- 600-800 words minimum

**CRITICAL:** Organize by SEMANTIC FUNCTION, not just translation

```markdown
## Лексика

### Група 1: Ідеї та думки (Ideas and Thoughts)

**Основні слова:**

| Слово         | Типові колокації                                       | Приклад                                       |
| ------------- | ------------------------------------------------------ | --------------------------------------------- |
| **ідея**      | мати ідею, цікава ідея, головна ідея                   | У мене є **ідея**, як розв'язати цю проблему. |
| **думка**     | на мою думку, особиста думка, змінити думку            | **На мою думку**, це правильний підхід.       |
| **концепція** | нова концепція, складна концепція, розвивати концепцію | Він розробив нову **концепцію** навчання.     |
| **теорія**    | наукова теорія, перевірити теорію                      | Ця **теорія** ще не підтверджена.             |

**Важливі відмінності:**

- **ідея** → конкретна думка, пропозиція (countable idea)
- **думка** → opinion, personal view
- **концепція** → abstract framework (more formal than ідея)
- **теорія** → scientific hypothesis (formal, academic)

> 🌍 **У реальному житті**
>
> В українських новинах часто використовують **ідея** для політичних пропозицій: "Президент висловив ідею референдуму." Але для особистих поглядів використовують **думка**: "На думку експертів..."

### Група 2: Проблеми та виклики (Problems and Challenges)

[Continue with 3-4 more semantic groups]
```

**Why this structure:**

- Groups by FUNCTION (how words are used), not just meaning
- Shows COLLOCATIONS (natural word combinations)
- Differentiates SYNONYMS by register/nuance
- Provides AUTHENTIC examples for each word
- Engagement boxes show REAL-WORLD usage

**Engagement Boxes in Лексика Section:**

Minimum 5+ engagement boxes focusing on USAGE:

```markdown
> 💡 **Важливо знати** - Register differences (formal/informal)
> 🎬 **У медіа** - How media uses this vocabulary
> 🌍 **Реальний контекст** - Authentic usage scenarios
> 🎯 **Колокації** - Common word combinations
> 📖 **Синоніми** - How to choose between similar words
```

#### Section 3: Використання (Practice Phase)

- Collocation patterns
- Register differentiation (formal/informal)
- Synonymy distinctions
- 400-600 words

```markdown
## Використання

### Колокації: як поєднувати слова?

**З дієсловом "мати":**

- мати **ідею** ✅
- мати **думку** ✅
- мати **концепцію** ❌ (use "розробити концепцію")
- мати **теорію** ❌ (use "висунути теорію")

**З дієсловом "вирішити":**

- вирішити **проблему** ✅
- вирішити **питання** ✅
- вирішити **завдання** ✅
- вирішити **ідею** ❌ (ideas aren't "solved")

**Чому це важливо?** Неправильні колокації звучать дивно для носіїв мови, навіть якщо граматично правильні.

### Реєстр: формальне чи розмовне?

**Розмовна мова:**

- У мене є **ідея**!
- Це **проблема**.
- Треба щось **придумати**.

**Формальна мова / Академічна:**

- Висуваю **гіпотезу**, що...
- Існує **проблематика**...
- Необхідно **розробити концептуальний підхід**.

> 💡 **Важливо розуміти**
>
> У професійному або академічному контексті використовуйте формальні варіанти. У повсякденному спілкуванні — розмовні. Змішування реєстрів звучить незграбно.

### Синоніми: які відмінності?

**ідея / думка / концепція**

- **ідея** → concrete proposal, creative suggestion
  - "У мене є ідея для проєкту." (I have an idea for a project.)

- **думка** → opinion, personal view
  - "Яка твоя думка про це?" (What's your opinion on this?)

- **концепція** → theoretical framework, systematic approach
  - "Концепція сталого розвитку." (The concept of sustainable development.)

**When to use which:**

- Everyday conversation → **ідея, думка**
- Academic/professional → **концепція, підхід**
```

**Why this works:**

- Teaches COLLOCATIONS explicitly (not just words in isolation)
- Shows REGISTER differences (formal vs informal)
- Differentiates SYNONYMS by usage context
- Uses ❌/✅ visual markers for clarity

---

### 4. Читання (Reading / Application Phase)

2-3 authentic passages using target vocabulary in context:

```markdown
## Читання

### Текст 1: Новинна стаття

**Про що текст:** Суспільні зміни в Україні

> Протягом останніх десяти років Україна пережила значні **зміни** в багатьох сферах. **Процес** демократизації прискорився після Євромайдану. Експерти **вважають**, що ці **трансформації** є незворотними, хоча деякі **критикують** темп реформ. На **думку** соціологів, найбільш помітні **зміни** відбулися в медіа-просторі та громадянському суспільстві. Однак залишається багато **проблем**, які потребують **рішень**.

**Після читання:**

1. Знайдіть у тексті 8 слів з вашого словника цього модуля.
2. Які колокації ви помітили? (наприклад: "значні зміни", "процес демократизації")
3. Яка думка експертів?

### Текст 2: Академічна дискусія

[2nd authentic passage]

### Текст 3: Блог / Розмовний стиль

[3rd authentic passage showing informal register]
```

**Why this works:**

- Shows vocabulary in AUTHENTIC contexts
- Different text types demonstrate REGISTER variation
- Comprehension questions verify understanding
- Multiple exposures reinforce learning

---

### 5. Діалоги / Обговорення (Production Phase)

4-5 dialogues or discussion scenarios:

```markdown
## Діалоги

### Діалог 1: Обговорення проєкту (Formal - коллеги)

**Олександр:** Яка твоя **думка** про нову **концепцію** маркетингу?

**Наталія:** **На мою думку**, це цікавий **підхід**. Але я **сумніваюся**, що він підійде для нашого ринку.

**Олександр:** Чому ти так **вважаєш**?

**Наталія:** Тут інша **проблематика**. Потрібне інше **рішення**.

---

### Діалог 2: Неформальна розмова (Informal - друзі)

**Марко:** У мене є **ідея**!

**Софія:** Яка?

**Марко:** Поїхати на вихідні до Карпат.

**Софія:** Непогана **думка**! Але є одна **проблема** — у мене немає грошей.

**Марко:** Знайдемо **рішення**!
```

**Why this works:**

- Shows REGISTER contrast (formal vs informal vocabulary)
- Demonstrates natural COLLOCATION use in speech
- Provides SPEAKING models for learners

---

### 6. Підсумок (Summary)

```markdown
# Підсумок

**Що ви навчилися:**

1. **30 слів абстрактної лексики** для обговорення ідей, проблем, рішень
2. **Колокації**: які слова природно поєднуються (мати ідею, вирішити проблему, висунути теорію)
3. **Реєстр**: коли використовувати формальні vs розмовні варіанти
4. **Синоніми**: як обрати між ідея/думка/концепція залежно від контексту

**Основне правило:**

> Абстрактна лексика дозволяє говорити про концепції та процеси, а не лише про конкретні об'єкти. Використовуйте її для інтелектуальних дискусій, академічного письма та професійного спілкування.

**Далі:**

У модулі 52 ми вивчимо абстрактні слова для опису **процесів** та **змін**: розвиток, прогрес, еволюція, трансформація.

> ✅ **Самоперевірка**
>
> Чи можете ви:
>
> - [ ] Відрізнити ідею від думки та концепції?
> - [ ] Утворити правильні колокації (мати ідею, вирішити проблему)?
> - [ ] Обрати формальний чи розмовний варіант залежно від ситуації?
> - [ ] Використати ці слова в реченні природно?
>
> Якщо так — ви готові до практики!
```

---

<!-- External resources moved to docs/resources/external_resources.yaml -->

---

## Activity Section Template

### Activity Order and Emphasis

**Recommended activities for B1 Vocabulary modules (12+ total):**

**High Priority (vocab-focused):**

1. **match-up** (12+ items) — Collocations, synonyms, definitions
2. **group-sort** (16+ items) — Semantic fields, register, word formation
3. **select** (8+ items) — Multiple correct collocations
4. **fill-in** (12+ items) — Contextual usage in sentences
5. **cloze** (14+ blanks) — Reading passage with target vocabulary

**Standard Activities:** 6. **quiz** (8+ items, 12-20 words) — Vocabulary comprehension 7. **true-false** (8+ items) — Usage verification 8. **unjumble** (6+ items, 12-16 words) — Sentence construction 9. **dialogue-reorder** (4+ lines) — Conversation flow 10. **translate** (6+ items) — Translation practice

**Advanced Activities:** 11. **error-correction** (6+ items) — Wrong collocations 12. **mark-the-words** (6+ markable words) — Identify semantic field

---

### Activity Format Quick Reference

**CRITICAL:** Use these exact formats for MDX generation to work.

**quiz** (checkbox, single answer):

```markdown
## quiz: Title

1. Question text (12-20 words)?
   - [ ] Wrong answer
   - [x] Correct answer
   - [ ] Wrong answer
   - [ ] Wrong answer
```

**match-up** (table):

```markdown
## match-up: Title

| Left | Right      |
| ---- | ---------- |
| term | definition |
```

**fill-in** (callouts):

```markdown
## fill-in: Title

1. Sentence with **\_** blank.
   > [!answer] correct
   > [!options] wrong1 | correct | wrong2 | wrong3
```

**true-false** (checkbox with explanations):

```markdown
## true-false: Title

- [x] True statement.
  > Explanation.
- [ ] False statement.
  > Explanation.
```

**group-sort** (category headers):

```markdown
## group-sort: Title

### Category A

- item1

### Category B

- item2
```

**select** (multi-checkbox):

```markdown
## select: Title

1. Question (select ALL correct):
   - [x] Correct 1
   - [x] Correct 2
   - [ ] Wrong
```

**cloze** (inline blanks):

```markdown
## cloze: Title

> Text with {blank|opt1|opt2|answer} blanks.
```

**unjumble** (answer callout):

```markdown
## unjumble: Title

1. words / in / order
   > [!answer] Correct sentence.
```

**error-correction** (4 callouts):

```markdown
## error-correction: Title

1. Sentence with error.
   > [!error] wrong
   > [!answer] correct
   > [!options] wrong | correct | d1 | d2
   > [!explanation] Why wrong.
```

**translate** (multi-choice):

```markdown
## translate: Title

1. English sentence.
   - [ ] Wrong
   - [x] Correct
   - [ ] Wrong
   - [ ] Wrong
```

**mark-the-words** (asterisks):

```markdown
## mark-the-words: Title

> [!instruction] Click target words.
>
> _Target_ other _target_.
```

**dialogue-reorder** (numbered):

```markdown
## dialogue-reorder: Title

- [2] Second line.
- [1] First line.
```

---

### Match-up: Collocations (HIGH PRIORITY for vocab modules)

**Example: Noun + Verb collocations**

```markdown
## match-up: Колокації — Іменник + Дієслово

Поєднайте іменники з дієсловами, які з ними природно використовуються:

- **ідею** → **мати** (мати ідею)
- **проблему** → **вирішити** (вирішити проблему)
- **теорію** → **висунути** (висунути теорію)
- **концепцію** → **розробити** (розробити концепцію)
- **думку** → **висловити** (висловити думку)
- **рішення** → **знайти** (знайти рішення)
- **питання** → **поставити** (поставити питання)
- **відповідь** → **дати** (дати відповідь)
```

**Why this is critical:**

- Vocabulary modules MUST teach COLLOCATIONS, not just isolated words
- Match-up is the best activity type for practicing word combinations
- 12+ items ensure comprehensive coverage

---

### Group-sort: Semantic Fields or Register (HIGH PRIORITY)

**Example: Sort by semantic field**

```markdown
## group-sort: Групування за значенням

Розподіліть слова за групами:

**Групи:**

1. **Ідеї та думки** (Ideas and Thoughts)
2. **Проблеми та виклики** (Problems and Challenges)
3. **Рішення та підходи** (Solutions and Approaches)

**Слова для сортування:**

- ідея → Ідеї та думки
- проблема → Проблеми та виклики
- рішення → Рішення та підходи
- думка → Ідеї та думки
- виклик → Проблеми та виклики
- підхід → Рішення та підходи
- концепція → Ідеї та думки
- труднощі → Проблеми та виклики
- метод → Рішення та підходи
- теорія → Ідеї та думки
- завдання → Проблеми та виклики
- стратегія → Рішення та підходи
- гіпотеза → Ідеї та думки
- питання → Проблеми та виклики
- спосіб → Рішення та підходи
- припущення → Ідеї та думки
```

**Why 16+ items:**

- Sufficient coverage of semantic categories
- Reinforces thematic organization from Лексика section
- Tests conceptual understanding, not just memorization

---

### Select: Multiple Correct Collocations (HIGH PRIORITY)

**Example: Choose ALL correct collocations**

```markdown
## select: Правильні колокації

Виберіть ВСІ правильні колокації для кожного дієслова:

1. **мати** (to have):
   - [x] мати ідею
   - [x] мати думку
   - [ ] мати концепцію (use "розробити концепцію")
   - [x] мати проблему
   - [ ] мати рішення (use "знайти рішення")

2. **вирішити** (to solve):
   - [ ] вирішити ідею
   - [x] вирішити проблему
   - [x] вирішити питання
   - [x] вирішити завдання
   - [ ] вирішити думку

[6 more questions]
```

**Why this works:**

- Trains PRODUCTIVE collocation knowledge
- Multiple correct answers reflect real language flexibility
- Tests both correct and incorrect combinations

---

### Fill-in: Contextual Usage (HIGH PRIORITY)

**Example: Choose the correct word from context**

```markdown
## fill-in: Вибір слова з контексту

Виберіть правильне слово для кожного речення:

1. На мою [___], це правильний підхід.
   - [ ] ідея
   - [x] думка
   - [ ] концепція
   - [ ] теорія

2. Вчені висунули нову [___] про походження Всесвіту.
   - [ ] ідея
   - [ ] думка
   - [ ] концепція
   - [x] теорія

3. У мене є [___], як покращити проєкт.
   - [x] ідея
   - [ ] думка
   - [ ] концепція
   - [ ] теорія

[9-11 more items for total of 12+]
```

**Why 12+ items:**

- Each item tests CONTEXTUAL appropriateness
- Forces learners to distinguish synonyms by usage
- Reinforces collocation patterns ("На мою думку", "висунути теорію")

---

## Vocabulary Section Template (25-30 items, 5 columns)

**✅ CORRECT FORMAT (5 columns with IPA) — AUDIT PASSES:**

```markdown
# Словник

| Слово             | Вимова            | Переклад             | ЧМ           | Примітка                             |
| ----------------- | ----------------- | -------------------- | ------------ | ------------------------------------ |
| **ідея**          | /iˈdɛjɑ/          | idea                 | ім. (ж.р.)   | мати ідею, цікава ідея               |
| **думка**         | /ˈdumkɑ/          | opinion, thought     | ім. (ж.р.)   | на мою думку, висловити думку        |
| **концепція**     | /kɔnˈt͡sɛpt͡sijɑ/   | concept              | ім. (ж.р.)   | розробити концепцію (formal)         |
| **теорія**        | /tɛˈɔrijɑ/        | theory               | ім. (ж.р.)   | наукова теорія, висунути теорію      |
| **проблема**      | /prɔˈblɛmɑ/       | problem              | ім. (ж.р.)   | вирішити проблему, серйозна проблема |
| **рішення**       | /riˈʃɛnːɑ/        | solution, decision   | ім. (с.р.)   | знайти рішення, прийняти рішення     |
| **вважати**       | /vːɑˈʒɑtɪ/        | to believe, consider | дієсл. (НДВ) | я вважаю, що...                      |
| **погоджуватися** | /pɔɦɔˈdʒuvɑtɪsʲɑ/ | to agree             | дієсл. (НДВ) | погоджуватися з думкою               |

[... 17-22 more entries for total of 25-30]
```

**CRITICAL for Vocabulary Modules:**

- **Примітка column**: MUST include common collocations
- 25-30 items (higher than grammar modules' 25)
- Group vocabulary thematically in the table if possible

---

## Common Pitfalls to Avoid

### 1. **Teaching Words in Isolation**

- ❌ Problem: Just listing words with translations, no collocations
- ✅ Solution: ALWAYS teach collocations: "мати ідею", "вирішити проблему", "висловити думку"

### 2. **Ignoring Register Differences**

- ❌ Problem: Not distinguishing formal vs informal vocabulary
- ✅ Solution: Mark register in Примітка column and explain in content

### 3. **Not Differentiating Synonyms**

- ❌ Problem: Teaching ідея/думка/концепція as identical
- ✅ Solution: Explicitly show USAGE differences in "Використання" section

### 4. **Insufficient Collocation Practice**

- ❌ Problem: Only 1-2 match-up activities for collocations
- ✅ Solution: Use match-up, select, and fill-in to reinforce collocations from multiple angles

### 5. **No Authentic Reading**

- ❌ Problem: All examples are constructed sentences
- ✅ Solution: Include 2-3 authentic passages (news, blogs, academic) showing vocabulary in real context

### 6. **Wrong Activity Mix**

- ❌ Problem: Too many quiz/true-false, not enough match-up/group-sort/select
- ✅ Solution: Emphasize vocabulary-focused activity types:
  - Match-up: 2-3 activities (collocations, synonyms)
  - Group-sort: 2-3 activities (semantic fields, register)
  - Select: 2 activities (multiple correct collocations)
  - Fill-in: 2 activities (contextual usage)

### 7. **Alphabetical Organization**

- ❌ Problem: Vocabulary presented alphabetically (defeats semantic learning)
- ✅ Solution: Organize by SEMANTIC GROUPS in Лексика section

### 8. **Missing Resources**

- ❌ Problem: No authentic materials for learners to practice with
- ✅ Solution: Add resources to `docs/resources/external_resources.yaml`

---

## Audit Validation

Before submitting, run:

```bash
python3 scripts/audit_module.py curriculum/l2-uk-en/b1/XX-your-module.md
```

**Target output:**

```
✅ Words: 1500+/1500
✅ Activities: 12/12
✅ Density: All > minimums
✅ Vocab: 25-30/25
✅ Pedagogy: Level-appropriate
✅ Immersion: 90-100%
✅ AUDIT PASSED.
```

---

## Example: M51 Structure (When Available)

When M51 (Abstract Concepts I) is created, it will serve as the reference implementation for vocabulary modules.

**Expected M51 specs:**

- ✅ Words: 1500+
- ✅ Vocabulary: 30 items
- ✅ Thematic groups: 5 semantic fields
- ✅ Collocations: Taught explicitly in tables and activities
- ✅ Register: Formal vs informal differentiation
- ✅ Reading: 3 authentic passages
- ✅ Activities: Emphasis on match-up, group-sort, select, fill-in

---

## Related Documents

- [B1 Curriculum Plan](../B1-CURRICULUM-PLAN.md) - Module 51-65 specifications
- [Module Richness Guidelines](../MODULE-RICHNESS-GUIDELINES-v2.md) - Quality standards
- [B1 Grammar Module Template](./b1-grammar-module-template.md) - For comparison
- [Activity Markdown Reference](../ACTIVITY-MARKDOWN-REFERENCE.md) - Activity syntax

---

**Last Updated:** 2025-12-23
**Based on:** B1 Curriculum Plan (Phase B1.5-B1.6)
**Status:** ✅ Production Ready
