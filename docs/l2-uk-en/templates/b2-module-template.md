# B2 Module Template

**Purpose:** Reference template for creating B2 modules (M01-110: Grammar, Phraseology, Ukrainian History, Skills)

**Based on:** B1-grammar-module-template.md, scaled to B2 requirements per Ukrainian State Standard 2024

**Related Issue:** [#292](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/292)

---

## Quick Reference Checklist

Before submitting a B2 module, verify:

### Content Requirements
- [ ] **Word count:** 1800+ words (core prose: explanations, examples, engagement boxes — excludes vocabulary section, activities section, and tables)
- [ ] **Vocabulary:** 30+ items in 3-column format (Слово | Переклад | Примітки)
- [ ] **Text passages:** 300-500+ word authentic-style reading passages
- [ ] **Writing support:** ALL writing tasks include Model Answers
- [ ] **Engagement boxes:** 5-6 boxes with pedagogical value

### Activity Requirements
- [ ] **Activities:** 14+ minimum (B2 standard)
- [ ] **Activity density:**
  - Quiz: 10+ items, questions 15-25 words each
  - Fill-in: 10+ items
  - Unjumble: 8+ items, sentences 15-20 words each
  - Cloze: 16+ blanks in passage
  - Group-sort: 16+ items
  - Error-correction: 8+ items with all 4 callouts
  - Translate: 8+ items (if used)
  - Mark-the-words: 300+ word passage
  - Dialogue-reorder: 10+ dialogue lines

### Immersion & Quality
- [ ] **Immersion:** 100% Ukrainian (English ONLY in vocabulary translations)
- [ ] **No Language Link boxes** — all explanations in Ukrainian
- [ ] **Pedagogy:** CBI (Content-Based Instruction) — TTT for grammar, Narrative Arcs for vocab/history
- [ ] **Register awareness:** Module uses appropriate functional style
- [ ] **No violations:** Check for pedagogical red flags

---

## Module Structure Template

### 1. Frontmatter (YAML)

```yaml
---
module: b2-XX
title: "Ukrainian Title"
subtitle: "English subtitle"
version: "1.0"
phase: "B2.X [Phase Name]"  # B2.1a, B2.1b, B2.2, B2.3, B2.4
pedagogy: "TTT"  # Grammar modules; "CBI" for Vocab/History modules
duration: 90  # minutes
transliteration: none  # No transliteration at B2
immersion: 100  # FULL immersion (English only in vocab table)
tags:
  - [module-type]  # grammar, phraseology, history, skills
  - [topic-tag]
grammar:
  - "Main grammar concept (e.g., Passive voice - full participle form)"
  - "Secondary concept"
objectives:
  - "Learner can [specific skill at B2 level]"
  - "Learner understands [concept] in authentic Ukrainian contexts"
vocabulary_count: 30  # Must match actual count in Словник
register: "науковий"  # Options: офіційно-діловий, науковий, публіцистичний, художній, розмовний
---
```

**New B2 fields:**
- `immersion: 100`: Enforces full Ukrainian immersion
- `register`: Functional style (5 options) — determines vocabulary, syntax, tone
- `pedagogy`: "TTT" (Test-Teach-Test) or "CBI" (Content-Based Instruction)

---

### 2. Module Title and Motivation Box

```markdown
# Ukrainian Title

> 🎯 **Чому це важливо?**
>
> [2-3 sentences IN UKRAINIAN explaining why this concept matters]
> [Connect to authentic Ukrainian usage: literature, journalism, academic texts]
> [Reference State Standard 2024 B2 requirements if relevant]
```

**Example (Passive Voice module):**
```markdown
# Пасивний стан: повна система

> 🎯 **Чому це важливо?**
>
> Пасивний стан — це базова граматична структура формальної української мови. Ви побачите її у наукових статтях, офіційних документах, журналістиці. Українська має чотири форми пасивного стану, кожна з різним стилістичним забарвленням. Без розуміння пасивного стану ви не зможете повністю зрозуміти академічний або офіційний текст.
```

**Critical:** Motivation box is IN UKRAINIAN (not English) at B2. No exceptions.

---

### 3. Content Sections (1800+ words total)

**Structure depends on pedagogy:**

#### For Grammar Modules (TTT Pedagogy)

**Section 1: Тест (Test Phase) — 200-300 words**
- Present authentic text containing target grammar
- No explanation yet — students discover the pattern
- Complex, real-world passage

```markdown
## Тест: Прочитайте текст

[300+ word passage from Ukrainian journalism/academic writing showing target grammar in context]

**Аналіз:**
- Знайдіть у тексті всі приклади [target structure]
- Що їх поєднує?
- Яка функція цієї структури?
```

**Section 2: Пояснення (Teach Phase) — 1000-1200 words**
- Systematic grammar explanation IN UKRAINIAN
- Use tables for organization
- Show register variation
- Include authentic examples

```markdown
## Пояснення

### [Concept Name in Ukrainian]

**Функція:** [Explain function]

**Форми:**

| Форма | Конструкція | Приклад | Регістр |
|-------|-------------|---------|---------|
| [Form 1] | [Structure] | [Example] | [Style] |
| [Form 2] | [Structure] | [Example] | [Style] |

**Вживання:**

1. **[Context 1]:**
   - [Explanation in Ukrainian]
   - Приклад: [Authentic example]

2. **[Context 2]:**
   - [Explanation in Ukrainian]
   - Приклад: [Authentic example]

[Continue for all usage contexts]
```

**Section 3: Практика (Test Phase 2) — 400-500 words**
- Apply grammar in new contexts
- Production tasks
- Free practice

```markdown
## Практика

### Завдання 1: Трансформація

Перетворіть активні речення на пасивні, використовуючи правильну форму для кожного регістру:

[10+ transformation examples]

### Завдання 2: Написання

Напишіть короткий текст (150+ слів) у [register] стилі, використовуючи [target grammar].

**Зразок відповіді (Model Answer):**

[Provide complete model answer showing correct usage]
```

---

#### For Vocabulary/History Modules (CBI/Narrative Arc Pedagogy)

**Section 1: Narrative Hook — 300-500 words**
- Compelling story or historical account
- Vocabulary embedded in context
- No lists!

```markdown
## [Story/Historical Event Title]

[300-500 word narrative introducing vocabulary naturally through storytelling]

[Use engagement boxes to add cultural/historical context]
```

**Section 2: Deep Dive — 800-1000 words**
- Continue narrative
- Expand on context
- Show vocabulary in multiple authentic uses

**Section 3: Analysis/Reflection — 300-400 words**
- Discuss significance
- Connect to broader themes
- Encourage critical thinking

---

### 4. Vocabulary Section (Словник)

**Format:** 3-column table (B2+ standard — NO pronunciation column)

```markdown
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| пасивний стан | passive voice | grammar term |
| дієприкметник | participle | from "дія" (action) + "прикмета" (attribute) |
| офіційно-діловий | official/bureaucratic style | functional register |
| фразеологізм | idiom, set expression | phraseology term |
| [30+ items] | | |
```

**B2 Vocabulary Notes:**
- **30+ items minimum** (vs. 25+ for B1)
- **3 columns only:** Слово, Переклад, Примітки (no Вимова/IPA)
- **Register-appropriate:** Vocabulary should match module's functional style
- **Примітки column:** Etymology, usage notes, collocations, register markers

---

### 5. Activities Section (Активності)

**Minimum:** 14+ activities (vs. 12+ for B1)

**Activity Mix for B2:**

#### Core Activities (Must Have)
1. **quiz** (10+ items, 15-25 words/question)
2. **fill-in** (10+ items)
3. **unjumble** (8+ items, 15-20 words/sentence)
4. **cloze** (16+ blanks, 300+ word passage)
5. **error-correction** (8+ items with all 4 callouts)
6. **group-sort** (16+ items, complex categories)

#### B2-Specific Activities
7. **mark-the-words** (300+ word passage, mark target grammar/vocabulary)
8. **dialogue-reorder** (10+ dialogue lines)
9. **translate** (8+ items, Ukrainian ↔ English)
10. **select** (multi-checkbox, 10+ items)

#### Writing/Production Activities
11. **Essay/Report with Model Answer** (150-300 words)
12. **Transformation** (Active → Passive, Register shift, etc.)
13. **Text analysis** (Identify register, grammar structures)
14. **Collocation practice** (Phraseology, set expressions)

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

### 6. Model Answers (MANDATORY for Writing Tasks)

**ALL writing tasks at B2+ MUST include Model Answers.**

```markdown
## Активність X: Написання есе

> [!writing]
> Напишіть есе (200+ слів) на тему: [Topic]
>
> Використовуйте:
> - [Target grammar/vocabulary]
> - [Register requirement]
> - [Structural requirements]

**Зразок відповіді (Model Answer):**

[Provide complete 200+ word essay showing:
- Correct register
- Target grammar/vocabulary used correctly
- Proper structure
- B2-appropriate complexity]

**Рубрика (Rubric):**

| Критерій | Опис |
|----------|------|
| Граматика | [Grammar criteria] |
| Лексика | [Vocabulary criteria] |
| Регістр | [Register criteria] |
| Структура | [Organization criteria] |
```

---

### 7. Engagement Boxes (5-6 boxes)

**B2 Engagement Box Types:**

```markdown
> 💡 **Чи знали ви?**
>
> [Linguistic/cultural fact IN UKRAINIAN]

> 🌍 **У реальному житті**
>
> [Real-world usage example IN UKRAINIAN]

> 📚 **Літературний приклад**
>
> [Quote from Ukrainian literature showing target grammar/vocabulary]

> 📰 **У пресі**
>
> [Example from Ukrainian journalism]

> ⚠️ **Поширена помилка**
>
> [Common error and correction]

> 🎯 **Регістр має значення**
>
> [Show how register affects grammar/vocabulary choice]
```

**Critical:** ALL engagement boxes in Ukrainian (no English text).

---

## B2-Specific Pedagogical Notes

### 1. Full Immersion (100%)

**English appears ONLY in vocabulary table translations. Everything else is Ukrainian:**
- Grammar explanations
- Activity instructions
- Examples
- Engagement boxes
- Model answers

**No Language Link boxes.** Students learned all metalanguage at B1.

### 2. Content-Based Instruction (CBI)

**"Content is King" at B2:**
- Grammar modules: Teach grammar through authentic texts (300-500+ words)
- Vocabulary modules: Embed words in compelling narratives (no lists!)
- History modules: Teach vocabulary through historical accounts

**Text density:** B2 modules feature substantial reading passages that mimic Ukrainian media/literature.

### 3. Register Awareness

**Every B2 module has a `register` field:**
- **Офіційно-діловий:** Documents, laws, bureaucratic language
- **Науковий:** Academic, scientific, technical writing
- **Публіцистичний:** Journalism, opinion pieces, persuasive writing
- **Художній:** Literary, artistic, creative writing
- **Розмовний:** Colloquial, conversational language

**Module vocabulary, syntax, and examples should match the register.**

### 4. Model Answers for ALL Writing

**Self-learners need examples.** Every writing task must include:
- Complete model answer (same length as required from learner)
- Shows correct grammar/vocabulary usage
- Demonstrates register appropriately
- Provides rubric for self-assessment

### 5. Complexity Scaling (B1 → B2)

| Feature | B1 | B2 |
|---------|----|----|
| Word count | 1500+ | 1800+ |
| Vocabulary | 25+ | 30+ |
| Activities | 12+ | 14+ |
| Quiz words/question | 12-20 | 15-25 |
| Unjumble words/sentence | 12-16 | 15-20 |
| Cloze blanks | 14+ | 16+ |
| Passages | 200-300 words | 300-500+ words |
| Immersion | 90-100% | 100% |

---

## Module Type Breakdown

### B2.1a: Grammar & Register (M01-30)

**Focus:** Passive voice, participles, register system
**Pedagogy:** TTT (Test-Teach-Test)
**Activities:** 14+ (heavy on transformation, register identification)
**Word count:** 1800+
**Passages:** Academic/journalistic texts (300-500 words)

**Example modules:**
- M01-10: Passive voice (4 forms)
- M11-20: Participles (active/passive)
- M21-30: Register system (5 functional styles)

### B2.1b: Grammar Completion (M31-40)

**Focus:** Numerals, word formation, pronouns
**Pedagogy:** TTT
**Activities:** 14+
**Word count:** 1800+

**Example modules:**
- M31-35: Complex numerals, collective numerals
- M36-40: Word formation (compounding, derivation)

### B2.2: Phraseology & Synonymy (M41-70)

**Focus:** Idioms, proverbs, synonyms, antonyms, collocations
**Pedagogy:** CBI (Narrative Arcs)
**Activities:** 12+ (collocation matching, idiom usage)
**Word count:** 1800+
**Passages:** Literary excerpts, journalistic pieces

**Example modules:**
- M41-50: Phraseology (фразеологізми, прислів'я, приказки)
- M51-60: Synonyms and antonyms
- M61-70: Collocations and set expressions

### B2.3: Ukrainian History (M71-95)

**Focus:** Medieval to present history, vocabulary through narrative
**Pedagogy:** CBI (Historical narratives)
**Activities:** 10-12 (comprehension, vocabulary in context)
**Word count:** 1800+
**Passages:** 500+ word historical accounts

**Example modules:**
- M71-80: Kyivan Rus, Cossack era
- M81-90: Soviet period, Holodomor, decolonization
- M91-95: Independence, modern Ukraine

**Critical:** Decolonization content (Pereiaslav Treaty myths, Holodomor recognition)

### B2.4: Skills & Capstone (M96-110)

**Focus:** Integrated skills, final assessment
**Pedagogy:** CBI + Skills integration
**Activities:** 12+ (multi-skill integration)
**Word count:** 1800+

**Example modules:**
- M96-105: Reading comprehension, writing skills, listening
- M106-109: Grammar/vocab review
- M110: Final exam (checkpoint with full assessment)

---

## Common Pitfalls to Avoid

### ❌ DON'T:
- **Don't use English in explanations** — 100% Ukrainian immersion required
- **Don't create vocabulary lists** — Embed vocabulary in narratives
- **Don't skip Model Answers** — Writing tasks MUST have examples
- **Don't ignore register** — Module must match its functional style
- **Don't use short passages** — B2 requires 300-500+ word texts
- **Don't under-count activities** — 14+ is the minimum

### ✅ DO:
- **Use authentic-style passages** — Mimic Ukrainian journalism/literature
- **Provide Model Answers for all writing** — Support self-learners
- **Match register throughout** — Vocabulary, syntax, examples consistent
- **Use TTT for grammar** — Present complex text, then explain
- **Use Narrative Arcs for vocab** — Tell compelling stories
- **Scale complexity from B1** — Longer texts, more activities, harder sentences

---

## Pre-Submission Checklist

### Content
- [ ] 1800+ words before activities
- [ ] 30+ vocabulary items in 3-column format
- [ ] 300-500+ word reading passages
- [ ] Model Answers for ALL writing tasks
- [ ] 5-6 engagement boxes (all in Ukrainian)
- [ ] Register matches frontmatter declaration

### Activities
- [ ] 14+ activities minimum
- [ ] All activity types represented
- [ ] Activity density meets B2 standards
- [ ] Writing tasks include rubrics
- [ ] Instructions in Ukrainian

### Immersion & Quality
- [ ] 100% Ukrainian (English only in vocabulary "Переклад" column)
- [ ] No Language Link boxes
- [ ] Pedagogy appropriate (TTT for grammar, CBI for vocab/history)
- [ ] No pedagogical violations
- [ ] Register awareness throughout

### Audit
- [ ] Module passes `python3 scripts/audit_module.py`
- [ ] Immersion ≥98%
- [ ] Vocabulary count matches frontmatter
- [ ] All activities formatted correctly

---

## Related Documentation

- **B2 Curriculum Plan:** `docs/l2-uk-en/B2-CURRICULUM-PLAN.md`
- **B2 Improvement Plan:** `docs/l2-uk-en/B2-IMPROVEMENT-PLAN.md`
- **B1 Grammar Template:** `docs/l2-uk-en/templates/b1-grammar-module-template.md`
- **Module Richness Guidelines:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- **Activity Markdown Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`
- **Ukrainian State Standard 2024:** `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
**Maintainer:** Claude (The Content Developer)
