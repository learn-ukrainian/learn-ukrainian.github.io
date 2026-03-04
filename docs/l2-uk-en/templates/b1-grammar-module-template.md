# B1 Grammar Module Template

**Purpose:** Reference template for creating B1 grammar modules (M06-50: Aspect, Motion Verbs, Complex Sentences, Advanced Grammar)

**Based on:** M06 (Aspect - Complete System) which achieved ✅ PASS on all audit gates

**Related Issue:** [#283](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/283)

<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка|Тест
  - Пояснення|Граматика|Теорія
  - Практика|Вправи
  - Підсумок
  - Потрібно більше практики?
  pedagogy: TTT
  min_word_count: 4000
  required_callouts: []
  description: B1 grammar uses TTT (Test-Teach-Test) with guided discovery
-->

---

## Quick Reference Checklist

Before submitting a B1 grammar module, verify:

- [ ] **Word count:** 4000+ words per config.py (core prose — excludes vocabulary section, activities section, and tables)
- [ ] **Vocabulary:** 25+ items in 5-column format (Слово | Вимова | Переклад | ЧМ | Примітка)
- [ ] **Activities:** 8-10 activities (quality over quantity, core types required)
- [ ] **Activity density:**
  - Quiz: 8+ items
  - Fill-in: 8+ items
  - Unjumble: 6+ items
  - Cloze: 12+ blanks in passage
  - Group-sort: 12+ items (optional activity)
  - **Sentence complexity:** Validated by audit (see `scripts/audit/config.py` for CEFR-aligned targets)
  - Error-correction: 6+ items with all 4 callouts
- [ ] **Engagement boxes:** 5+ boxes with pedagogical value
- [ ] **Immersion:** 90-100% Ukrainian (grammar explanations in Ukrainian)
- [ ] **Pedagogy:** Level-appropriate complexity, no violations
- [ ] **Structure:** TTT or Presentation-Practice-Production

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

## Module Structure Template

### 1. Frontmatter (YAML)

```yaml
---
module: b1-XX
title: 'Ukrainian Title'
subtitle: 'English subtitle'
version: '1.0'
phase: 'B1.X [Phase Name]'
pedagogy: 'TTT' # or "PPP"
duration: 90 # minutes
transliteration: none # B1 has no transliteration
tags:
  - grammar
  - [topic-specific-tag]
grammar:
  - 'Main grammar concept'
  - 'Secondary concept'
objectives:
  - 'Learner can X'
  - 'Learner understands Y'
vocabulary_count: 25 # Must match count in vocabulary/{slug}.yaml
---
```

**Why these fields:**

- `phase`: Groups modules thematically (e.g., "B1.1 Aspect", "B1.2 Motion")
- `pedagogy`: "TTT" for test-teach-test, "PPP" for presentation-practice-production
- `transliteration: none`: B1+ modules are 90-95% immersed, no transliteration
- `vocabulary_count`: Audit validates this matches actual vocabulary count

---

### 2. Module Title and Motivation Box

```markdown
# Ukrainian Title

> 🎯 **Чому це важливо?**
>
> [2-3 sentences explaining WHY this grammar concept matters]
> [Connect to real-world usage]
> [Reference previous modules if applicable]
```

**Example from M06:**

```markdown
# Вид дієслова: повна система

> 🎯 **Чому це важливо?**
>
> Вид дієслова — це найважливіша граматична категорія української мови. Кожне дієслово має вид: доконаний або недоконаний. Вибір виду змінює значення речення. Ви вже знаєте терміни з модуля 02. Тепер настав час зрозуміти всю систему.
```

**Why this works:**

- Establishes relevance immediately
- Connects to prior knowledge (M02 metalanguage)
- Sets expectations for module depth

---

### 3. Content Sections (4000+ words total)

**Structure for TTT pedagogy:**

#### Section 1: Тест (Test Phase)

- Present diagnostic contrast or puzzle
- No explanation yet, just observation
- 100-200 words

```markdown
## Тест

Прочитайте два речення:

1. **Я писав листа.**
2. **Я написав листа.**

Яка різниця? Обидва речення про минуле. Обидва про листа. Але значення різні:

- **Перше речення** (писав) = процес. Я був у процесі написання. Можливо, я не закінчив.
- **Друге речення** (написав) = результат. Я закінчив. Лист готовий.

Це — **вид дієслова**. Одне дієслово, два види, різні значення.
```

**Why this works:**

- Concrete contrast makes the concept tangible
- Avoids abstract definitions initially
- Engages critical thinking

#### Section 2: Пояснення (Teach Phase)

- Systematic grammar explanation
- Use Ukrainian metalanguage (вид, доконаний, недоконаний)
- Tables for organization
- 700-900 words minimum

**CRITICAL:** Grammar must be explained **IN UKRAINIAN** (90-95% immersion)

```markdown
## Пояснення

### Недоконаний вид (НДВ)

**Функція:** виражає **процес**, **тривалість**, **повторення**.

**Коли використовується:**

1. **Дія триває:**
   - Я **читав** книгу дві години. (процес)
   - Вона **писала** листа весь вечір. (тривалість)

2. **Дія повторюється:**
   - Я **читав** цю книгу кілька разів. (повторення)
   - Вони **зустрічалися** щотижня. (регулярність)

[Continue with 4 usage contexts + examples table]
```

**Why this structure:**

- Groups by FUNCTION, not just by form
- Provides 4+ usage contexts with concrete examples
- Uses tables to reduce cognitive load
- Introduces terminology naturally in context

**Engagement Boxes in Пояснення:**

Minimum 5+ engagement boxes with pedagogical value:

```markdown
> 💡 **Чи знали ви** - Linguistic insight
> 🎬 **Момент поп-культури** - Cultural connection
> 🌍 **Реальний світ** - Practical application
> 🎯 **Цікавий факт** - Memorable trivia
```

**Example from M06:**

```markdown
> 🌍 **У реальному житті**
>
> Коли українці розповідають про свій день, вони часто використовують НДВ: "Я працював, обідав, відпочивав..." Це показує послідовність дій як процесів, не акцентуючи на результатах.
```

**Why this works:**

- Shows USAGE, not just definition
- Connects grammar to real Ukrainian communication patterns
- Motivates learners with practical relevance

#### Section 3: Практика (Practice Phase)

- Decision-making framework
- Comparative examples
- Common mistakes section
- 400-600 words

```markdown
## Практика

### Як обрати вид?

Задайте собі питання:

1. **Що важливіше — процес чи результат?**
   - Процес → НДВ: "Я **читав** книгу." (що я робив)
   - Результат → ДВ: "Я **прочитав** книгу." (що я досяг)

[3-4 more decision questions]

### Типові помилки та як їх уникнути

**Помилка 1: [Description]**

❌ Неправильно: [Example]
✅ Правильно: [Example]

**Чому?** [Explanation]
```

**Why this works:**

- Gives learners TOOLS for aspect selection
- Addresses common errors proactively
- Uses ❌/✅ visual markers for clarity

---

### 4. Діалоги (Production Phase)

5-6 authentic dialogues showing grammar in context:

```markdown
## Діалоги

### Діалог 1: Про вихідні

**Олег:** Що ти **робив** у суботу?

**Марія:** Я **читала** книгу та **дивилася** фільм.

**Олег:** І що, **прочитала** всю книгу?

**Марія:** Ні, я тільки **починала**. Ще не **закінчила**.
```

**Why this works:**

- Shows natural code-switching between НДВ/ДВ
- Demonstrates pragmatic use in conversation
- 5-6 dialogues cover different contexts (home, work, school, etc.)

---

### 5. Підсумок (Summary)

```markdown
# Підсумок

**Що ви навчилися:**

1. [Key concept 1]
2. [Key concept 2]
3. [Key concept 3]
4. [Key concept 4]

**Основне правило:**

> [Quotable summary in Ukrainian]

**Далі:**

У наступних модулях ми розглянемо [preview of M+1, M+2, etc.]

> ✅ **Самоперевірка**
>
> Чи можете ви:
>
> - [ ] [Self-assessment criterion 1]?
> - [ ] [Self-assessment criterion 2]?
> - [ ] [Self-assessment criterion 3]?
> - [ ] [Self-assessment criterion 4]?
>
> Якщо так — ви готові до практики!
```

**Why this works:**

- Consolidates learning
- Preview creates continuity to next modules
- Self-assessment empowers learner autonomy

---

### 6. External Resources

> **⚠️ NOTE:** External resources are managed in `docs/resources/external_resources.yaml`, NOT in module markdown files. Do NOT add `[!resources]` blocks to modules.

---

## Activity Section Template

### Activity Order and Density

**Required activities for B1 (8-10 total, core types):**

**Core Activities (Required - 7 types minimum):**
1. quiz (8+ items)
2. match-up (8+ items)
3. fill-in (8+ items)
4. unjumble (6+ items)
5. error-correction (6+ items with all 4 callouts)
6. cloze (12+ blanks in passage)
7. translate (6+ translation questions)

**Sentence Complexity:** See `scripts/audit/config.py` ACTIVITY_COMPLEXITY['B1'] for CEFR-aligned word count targets

**Optional Activities (choose 1-3 to reach 8-10 total):**
8. true-false (8+ items)
9. group-sort (12+ items)
10. mark-the-words (6+ markable words)
11. select (6+ multi-select questions)

---

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/b1-06-aspect-complete-system.yaml`:**

```yaml
- type: quiz
  title: Вибір виду дієслова
  items:
    - question: Яке з наведених дієслів виражає процес?
      options:
        - text: читати
          correct: true
        - text: прочитати
          correct: false
      explanation: Недоконаний вид (читати) виражає процес.

- type: unjumble
  title: Побудова речення
  items:
    - jumbled: я / читав / книгу / дві / години
      answer: Я читав книгу дві години.
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

## Common Pitfalls to Avoid

### 1. **Insufficient Word Count**

- ❌ Problem: Module has 897 words (need 1500+)
- ✅ Solution: Expand Пояснення section with more examples, cultural context, decision frameworks, common mistakes

### 2. **Quiz Questions Too Short**

- ❌ Problem: Questions 4-8 words (need 12-20)
- ✅ Solution: Add context ("Яке з наведених нижче..."), conditions, subordinate clauses

### 3. **Unjumble Sentences Too Simple**

- ❌ Problem: Sentences 7-9 words (need 12-16)
- ✅ Solution: Add subordinate clauses (коли, що, бо), prepositional phrases, adverbs

### 4. **Cloze Passage Too Sparse**

- ❌ Problem: 10 blanks (need 14+)
- ✅ Solution: Expand passage with parallel actions, result clauses, more context

### 5. **Wrong Vocabulary Format**

- ❌ Problem: 3 columns without IPA (need 5 columns with IPA)
- ✅ Solution: Add Вимова and ЧМ columns, use proper IPA notation

### 6. **Insufficient Engagement Boxes**

- ❌ Problem: 3 boxes (need 5+)
- ✅ Solution: Add 💡 Чи знали ви, 🎬 Поп-культура, 🌍 Реальний світ, 🎯 Цікавий факт

### 7. **Low Immersion**

- ❌ Problem: Grammar explained in English (85% Ukrainian)
- ✅ Solution: Use Ukrainian metalanguage for grammar explanations (90-95% target)

### 8. **Missing Error-Correction Callouts**

- ❌ Problem: Only `[!error]` and `[!answer]` provided
- ✅ Solution: Add `[!options]` and `[!explanation]` for every error-correction item

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
✅ Vocab: 25/25
✅ Pedagogy: Level-appropriate
✅ Immersion: 90-100%
✅ AUDIT PASSED.
```

---

## Example: M06 as Reference Implementation

See `curriculum/l2-uk-en/b1/06-aspect-complete-system.md` for a complete example that passes all audit gates.

**M06 Audit Results:**

- ✅ Words: 1516/1500
- ✅ Activities: 12/12 (all types)
- ✅ Density: Quiz 14 items, Cloze 14 blanks, Unjumble 8 items
- ✅ Vocab: 25/25 in correct 5-column format
- ✅ Engagement: 10 boxes
- ✅ Immersion: 97.2%
- ✅ Pedagogy: No violations

---

## Related Documents

- [B1 Curriculum Plan](../B1-CURRICULUM-PLAN.md) - Full B1 module specifications
- [Module Richness Guidelines](../MODULE-RICHNESS-GUIDELINES-v2.md) - Quality standards
- [Quick Reference: B1](claude_extensions/quick-ref/b1.md) - B1 requirements summary
- [Activity Markdown Reference](../ACTIVITY-MARKDOWN-REFERENCE.md) - Activity syntax patterns

---

**Last Updated:** 2025-12-22
**Based on:** M06 (Aspect - Complete System)
**Status:** ✅ Production Ready
