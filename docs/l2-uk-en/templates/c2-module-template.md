# C2 Module Template

**Purpose:** Reference template for creating C2 modules (M01-100: Stylistic Perfection, Literary Mastery, Professional Specialization, Meta-Skills & Capstone)

**Based on:** C1-module-template.md, scaled to C2 requirements per Ukrainian State Standard 2024

**Related Issue:** [#294](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/294)

---

## Quick Reference Checklist

Before submitting a C2 module, verify:

### Content Requirements
- [ ] **Word count:** 2200+ words (core prose: explanations, examples, engagement boxes — excludes vocabulary section, activities section, and tables)
- [ ] **Vocabulary:** 40+ items in 3-column format (Слово | Переклад | Примітки)
- [ ] **Text passages:** 600-1000+ word native-level texts
- [ ] **Creative/productive tasks:** Original writing, translation, or transformation
- [ ] **Writing support:** ALL creative tasks include Model Answers (gold standard)
- [ ] **Engagement boxes:** 7-8 boxes with expert-level depth

### Activity Requirements
- [ ] **Activities:** 14-16 minimum (C2 standard — quality over quantity)
- [ ] **Activity density:**
  - Quiz: 10-12 items, questions 20-35 words each (complex)
  - Fill-in: 12+ items (nuanced, stylistic choices)
  - Unjumble: 10+ items, sentences 20-30 words each
  - Cloze: 20+ blanks in passage
  - Transformation: 8+ items (register shift, style transformation)
  - Creative production: Poetry, prose, translation (with Model Answer)
  - Translation analysis: Compare translations, discuss choices

### Immersion & Quality
- [ ] **Immersion:** 100% Ukrainian (English ONLY in vocabulary translations)
- [ ] **Native-level texts:** No simplification
- [ ] **Creative production:** Original writing required
- [ ] **Stylistic precision:** Nuanced register/style control
- [ ] **No violations:** Check for pedagogical red flags

---

## Module Structure Template

### 1. Frontmatter (YAML)

```yaml
---
module: c2-XXX  # M001-100 (3-digit numbering)
title: "Ukrainian Title"
subtitle: "English subtitle"
version: "1.0"
phase: "C2.X [Phase Name]"  # C2.1, C2.2, C2.3, C2.4
pedagogy: "Creative Production"  # Or "Stylistic Mastery", "Professional", "Meta-Linguistic"
duration: 120  # minutes (complex creative tasks require time)
transliteration: none
immersion: 100
tags:
  - [module-type]  # stylistic, literary, professional, meta-skills, capstone
  - [topic-tag]
grammar:
  - "Complete morphological/syntactic mastery concept"
  - "Stylistic device or rare form"
objectives:
  - "Learner can produce [creative/professional work] at native-like level"
  - "Learner can transform [text] across styles/registers with precision"
  - "Learner can analyze [linguistic phenomenon] at expert level"
vocabulary_count: 40  # Must match count in vocabulary/{slug}.yaml
---
```

**New C2 fields:**
- `pedagogy: "Creative Production"`: Reflects C2 emphasis on original creation
- `style_focus`: Specific stylistic nuance (irony, archaism, euphony, etc.)

---

## What Makes C2 Different from C1

| Aspect | C1 | C2 |
|--------|----|----|
| **Philosophy** | "Studying IN Ukrainian" | "Creating WITH Ukrainian" |
| **Word count** | 2000+ | 2200+ |
| **Vocabulary** | 35+ | 40+ |
| **Activities** | 16+ | 14-16 (quality over quantity) |
| **Passages** | 500-800 words | 600-1000+ words |
| **Complexity** | University-level | Native-level, literary |
| **Analysis** | Comparative, critical | Expert, meta-linguistic |
| **Production** | Academic papers, critiques | Poetry, prose, translation, professional docs |
| **Register** | Mastery + shifting | All 7 styles + nuanced control |
| **Focus** | Understanding | Creating, perfecting |

**Key shift:** At C2, learners are **creators** — poets, translators, professional writers. They don't just use Ukrainian; they **craft** it.

---

### 2. Module Title and Motivation Box

```markdown
# Ukrainian Title

> 🎯 **Чому це важливо?**
>
> [3-4 sentences IN UKRAINIAN explaining native-level significance]
> [Connect to literary creation, professional excellence, or linguistic mastery]
> [Reference State Standard 2024 C2 requirements if relevant]
> [Emphasize creative/productive aspect]
```

**Example (Stylistic Transformation module):**
```markdown
# Стилістична трансформація: від формального до іронічного

> 🎯 **Чому це важливо?**
>
> На рівні C2 ви маєте вміти не тільки розпізнавати регістри, але й майстерно трансформувати тексти між ними. Іронія — це тонкий стилістичний прийом, що вимагає глибокого розуміння мови та культури. Перетворення формального тексту на іронічний — це не просто підміна слів, а створення нового смислового шару. Цей модуль навчить вас створювати іронію мовними засобами, як це роблять майстри української літератури.
```

**Critical:** Motivation box must emphasize **creative production** and **native-like mastery**.

---

### 3. Content Sections (2200+ words total)

**Structure for Creative Production:**

#### Section 1: Presentation of Exemplar Texts — 600-1000 words

- Present multiple exemplar texts showing target style/register
- Native-level literary/professional texts
- Detailed stylistic analysis

```markdown
## Зразкові тексти

### Текст 1: Формальний регістр

**Контекст:**
[Context about text type, author, purpose]

[600-1000 word formal text — academic, official, or journalistic]

**Стилістичний аналіз:**
- Лексика: [Formal vocabulary characteristics]
- Синтаксис: [Complex sentence structures]
- Тон: [Neutral, impersonal]
- Стилістичні засоби: [Devices used]

### Текст 2: Іронічний регістр

**Контекст:**
[Context for ironic text]

[600-1000 word ironic text showing transformation]

**Стилістичний аналіз:**
- Лексика: [How vocabulary creates irony]
- Синтаксис: [How structure supports irony]
- Тон: [Ironic, subversive]
- Стилістичні засоби: [Irony, hyperbole, litotes, etc.]

### Порівняльний аналіз

| Аспект | Формальний | Іронічний |
|--------|-----------|-----------|
| Лексика | [Analysis] | [Analysis] |
| Синтаксис | [Analysis] | [Analysis] |
| Тон | [Analysis] | [Analysis] |
| Ефект | [Analysis] | [Analysis] |
```

#### Section 2: Creative Production Task — 800-1000 words

- Original writing, translation, or transformation task
- Detailed guidance and rubric
- **Model Answer (gold standard)**

```markdown
## Творче завдання: Стилістична трансформація

**Завдання:**
Візьміть формальний текст (150+ слів) на тему [topic] і трансформуйте його в іронічний регістр.

**Вимоги:**
1. Зберегти фактичну інформацію
2. Змінити тон на іронічний
3. Використати мінімум 5 стилістичних прийомів (гіпербола, літота, евфемізм, тощо)
4. Написати короткий коментар (100+ слів), пояснюючи ваші стилістичні вибори

**Зразок відповіді (Model Answer):**

**Оригінальний формальний текст:**
[150+ word formal text]

**Іронічна трансформація:**
[150+ word ironic transformation showing:
- Ironic tone
- Stylistic devices (hyperbole, litotes, euphemism, etc.)
- Subtle subversion of formal register
- Native-like linguistic control]

**Коментар автора:**
[100+ word commentary explaining:
- Which stylistic devices were used and why
- How irony was created linguistically
- What effect was intended
- Meta-linguistic awareness of choices]

**Рубрика:**

| Критерій | Опис | Очікування на C2 |
|----------|------|------------------|
| Іронічний тон | Створення іронії | Тонка, контрольована іронія без грубості |
| Стилістичні прийоми | Використання засобів | Мінімум 5 засобів, вжиті природно |
| Лінгвістична точність | Граматика, лексика | Безпомилкове використання |
| Метамовна свідомість | Коментар | Глибоке розуміння власних стилістичних виборів |
```

#### Section 3: Expert Analysis — 400-600 words

- Meta-linguistic discussion
- Discuss how Ukrainian creates stylistic effects
- Reference literary examples
- Connect to broader linguistic concepts

```markdown
## Метамовний аналіз

### Як українська створює іронію

[Discussion of linguistic mechanisms for irony in Ukrainian:
- Lexical choices (euphemisms, hyperbole)
- Syntactic structures (inversion, ellipsis)
- Tone markers (particles, discourse markers)
- Cultural references and allusions]

### Іронія в українській літературі

[Examples from Ukrainian literature:
- Quotes from Shevchenko, Franko, Kulish showing irony
- Analysis of how masters create ironic effects
- Discussion of cultural context]

### Культурний контекст

[Why irony matters in Ukrainian culture:
- Historical context (Soviet censorship, coded critique)
- Contemporary usage (journalism, social media)
- Register awareness in native speakers]
```

---

### 4. Vocabulary Section (Словник)

**CRITICAL:** Vocabulary must be defined in `vocabulary/{slug}.yaml`. Do NOT embed a vocabulary table in Markdown.

**Example `vocabulary/c2-XX-style.yaml`:**

```yaml
items:
- lemma: евфемізм
  ipa: /ɛu̯fɛˈmʲizm/
  translation: euphemism
  pos: ім. (ч.р.)
  note: stylistic device: mild expression
- lemma: іронія
  ipa: /iˈrɔnʲijɑ/
  translation: irony
  pos: ім. (ж.р.)
  note: stylistic tone
```

**C2 Vocabulary Notes:**
- **40+ items minimum** (vs. 35+ for C1)
- **Highly specialized:** Literary, stylistic, professional, meta-linguistic terminology
- **Note field:** Etymology, usage examples, collocations, stylistic effects, cultural notes
- **Native-level nuance:** Synonyms with subtle differences, register-specific variants

---

### 5. Activities Section (Активності)

**Minimum:** 14-16 activities (C2 emphasizes **quality over quantity**)

**Activity Mix for C2:**

#### Core Activities (Refined for C2)
1. **quiz** (10-12 items, 20-35 words/question — complex, nuanced)
2. **fill-in** (12+ items, stylistic/register choices)
3. **unjumble** (10+ items, 20-30 words/sentence)
4. **cloze** (20+ blanks, 600+ word passage)
5. **transformation** (8+ items: register shift, style change)

#### C2-Specific Creative Activities (Use new Schema types)
6. **[essay-response]** (Publication-ready writing)
    *   *Requires `rubric` and `model_answer` in YAML.*
7. **[comparative-study]** (Synthesis of multiple sources)
    *   *Complex comparison of 3+ texts or translations.*
8. **[critical-analysis]** (Scholar-level critique)
    *   *Analyze style, tone, and intertextuality.*
9. **[authorial-intent]** (Reconstruction of creative choices)
    *   *Reverse-engineer the author's stylistic decisions.*
10. **Style transformation** (Formal → Ironic, Neutral → Literary, etc.)
    *   *Use `essay-response` type with specific prompt.*

#### Meta-Linguistic Activities
11. **Stylistic analysis** (Identify all devices in passage, explain function)
12. **Translation comparison** (Compare 2+ translations, discuss choices)
13. **Error detection** (Subtle stylistic/register errors)
14. **Literary criticism** (Analyze author's style, technique)

#### Professional Activities (C2.3 modules)
15. **Professional document production** (Contract, report, memo — with Model Answer)
16. **Professional correspondence** (Formal letters, emails — with rubric)

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/c2-XX-style.yaml`:**

```yaml
- type: essay-response
  title: Стилістична трансформація
  instruction: Трансформуйте текст в іронічний регістр.
  prompt: Візьміть формальний текст і змініть тон на іронічний.
  model_answer: (Sample ironic text...)
  rubric: (Evaluation criteria...)

- type: comparative-study
  title: Порівняння перекладів
  content: (Two translations of Hamlet)
  task: Порівняйте вибір лексики у двох перекладах.
  model_answer: (Detailed analysis...)
```

---

### 6. Engagement Boxes (7-8 boxes)

**C2 Engagement Box Types:**

```markdown
> 💡 **Експертна перспектива**
>
> [Deep expert-level linguistic insight IN UKRAINIAN about language, style, or usage]

> 📚 **Літературний майстер-клас**
>
> [How Ukrainian literary masters (Shevchenko, Franko, Lesya Ukrainka) use this technique]

> 🎨 **Стилістична нюансировка**
>
> [Subtle distinction between near-synonyms, stylistic variants, register choices]

> 🌍 **Культурно-історичний контекст**
>
> [Why this linguistic feature exists in Ukrainian culture/history]

> 🔍 **Метамовна свідомість**
>
> [Meta-linguistic awareness: how natives think about this feature]

> ⚖️ **Порівняння стилів**
>
> [Same content in 3+ styles — show full range]

> 🗣️ **Регіональна варіація**
>
> [How this appears in different Ukrainian dialects or regional variants]

> 🎭 **Стилістичний ефект**
>
> [What effect this creates: irony, formality, intimacy, etc.]
```

**Critical:** ALL engagement boxes in Ukrainian, reflect **native-level expertise**.

---

## C2-Specific Pedagogical Notes

### 1. Creative Production (Mandatory)

**C2 modules MUST include creative/productive tasks:**
- Original poetry (20+ lines)
- Original prose (500+ words)
- Literary translation (300+ words source text)
- Professional documents (contracts, reports, memos)

**Model Answers are MANDATORY:**
- Provide "gold standard" example
- Show native-like linguistic control
- Demonstrate stylistic precision
- Include author commentary (meta-linguistic awareness)

### 2. Stylistic Precision

**C2 learners must control:**
- **All 7 functional styles:** Розмовний, Офіційний, Науковий, Публіцистичний, Художній, Релігійний, Епістолярний
- **Stylistic nuances:** Irony, euphony, archaism, colloquialism, formality levels
- **Register shifting:** Same content, multiple styles
- **Synonym nuance:** Choose between near-synonyms based on context

**Example:**
- "говорити" vs. "казати" vs. "мовити" vs. "промовляти" (all = "to speak", different registers)

### 3. All 7 Functional Styles (C2 Expansion)

**C2 adds 2 new styles beyond B2/C1:**

| Style | Description | C2 Production |
|-------|-------------|---------------|
| Розмовний | Colloquial | Natural, native-like informal speech |
| Офіційний | Official/bureaucratic | Legal documents, contracts |
| Науковий | Scientific/academic | Research papers, abstracts |
| Публіцистичний | Journalistic | Opinion pieces, editorials |
| Художній | Literary/artistic | Poetry, prose, literary analysis |
| **Релігійний** | **Religious** | Church texts, sermons (NEW at C2) |
| **Епістолярний** | **Epistolary** | Letters, correspondence (NEW at C2) |

**Modules must address all 7 styles by end of C2.**

### 4. Professional Specialization (C2.3 — Meta-Skills)

**C2.3 teaches UNIVERSAL professional skills, not domain jargon:**
- Terminology acquisition strategies
- Professional text comprehension patterns
- Professional document templates (applicable to ANY field)
- Professional discourse navigation
- Self-directed learning frameworks

**Example:** Instead of teaching "legal Ukrainian", teach:
- How to acquire legal terminology independently
- Structure of legal documents (universal templates)
- How to recognize register in professional texts
- How to produce professional documents in any domain

**Future:** Optional extension tracks (Legal, Medical, IT) can build on C2.3 meta-skills.

### 5. Capstone Projects (C2.4)

**C2.4 includes 4 capstone options:**

1. **Research Paper** (10,000-12,000 words, 15+ sources, academic register)
2. **Literary Work** (Poetry collection 20+ poems OR prose 15,000+ words)
3. **Translation Project** (50+ pages source text, translator's preface, glossary)
4. **Professional Portfolio** (10+ documents across 3+ styles)

**Model capstone projects must be provided** to show expectations.

### 6. Meta-Linguistic Awareness

**C2 learners must demonstrate:**
- Understanding of own linguistic choices
- Ability to explain stylistic decisions
- Awareness of register/style effects
- Knowledge of Ukrainian linguistic history
- Sociolinguistic understanding (dialects, Surzhyk, register variation)

**Every creative task should include commentary:**
- "Why did you choose this word over that synonym?"
- "What effect were you trying to create?"
- "How does your register choice support your purpose?"

### 7. Complexity Scaling (C1 → C2)

| Feature | C1 | C2 |
|---------|----|----|
| Word count | 2000+ | 2200+ |
| Vocabulary | 35+ | 40+ |
| Activities | 16+ | 14-16 (quality over quantity) |
| Quiz words/question | 18-30 | 20-35 |
| Unjumble words/sentence | 18-25 | 20-30 |
| Cloze blanks | 20+ | 20+ |
| Passages | 500-800 words | 600-1000+ words |
| Complexity | University-level | Native-level, literary |
| Production | Academic papers | Poetry, prose, translation |
| Focus | Analysis | Creation |

---

## Module Type Breakdown

### C2.1: Stylistic Perfection (M01-25)

**Focus:** All 7 functional styles, style transformation, euphonic mastery
**Pedagogy:** Creative Production
**Activities:** 14-16 (heavy on transformation, production)
**Word count:** 2200+
**Creative tasks:** Style transformation, register shifting, original writing

**Example modules:**
- M01-07: 7 functional styles (including религійний, епістолярний)
- M08-15: Style transformation exercises
- M16-20: Euphonic mastery (sound patterns, rhythm)
- M21-25: Individual voice development

### C2.2: Literary Mastery (M26-45)

**Focus:** Literary theory, narratology, poetics, translation, creative writing
**Pedagogy:** Creative Production
**Activities:** 12-14 (creative writing, translation, analysis)
**Word count:** 2200+
**Creative tasks:** Poetry, prose, translation (with Model Answers)

**Example modules:**
- M26-30: Literary theory and analysis
- M31-35: Narratology and poetics
- M36-40: Translation theory and practice
- M41-45: Creative writing (poetry and prose)

### C2.3: Professional Specialization (M46-75)

**Focus:** Meta-skills for professional domains (universal templates, not jargon)
**Pedagogy:** Professional simulation
**Activities:** 12-14 (professional writing, document templates)
**Word count:** 2200+
**Professional tasks:** Documents, reports, correspondence (with Model Answers)

**Example modules:**
- M46-55: Terminology acquisition strategies
- M56-65: Professional text comprehension
- M66-75: Professional document production (universal templates)

**Critical:** NOT domain-specific jargon, but transferable meta-skills.

### C2.4: Meta-Skills & Capstone (M76-100)

**Focus:** Complete grammar review, rare/archaic forms, regional varieties, sociolinguistics, teaching Ukrainian, translation, capstone projects
**Pedagogy:** Meta-Linguistic + Capstone
**Activities:** 10-16 (meta-analysis, capstone work)
**Word count:** 2200+

**Example modules:**
- M76-80: Complete grammar review
- M81-85: Rare and archaic forms
- M86-90: Regional varieties and dialects
- M91-95: Sociolinguistic mastery
- M96: Teaching Ukrainian (meta-awareness)
- M97-98: Translation theory and practice
- M99: Final review
- M100: Final certification

**Capstone options:**
- Research paper (10,000-12,000 words)
- Literary work (poetry 20+ poems OR prose 15,000+ words)
- Translation project (50+ pages)
- Professional portfolio (10+ documents, 3+ styles)

---

## Common Pitfalls to Avoid

### ❌ DON'T:
- **Don't skip Model Answers** — Creative tasks MUST have gold standard examples
- **Don't simplify texts** — C2 requires native-level complexity
- **Don't ignore stylistic nuance** — Synonym choice matters at C2
- **Don't skip meta-linguistic commentary** — C2 requires awareness of choices
- **Don't teach domain jargon in C2.3** — Teach universal professional meta-skills
- **Don't under-count creative tasks** — C2 is about production

### ✅ DO:
- **Provide Model Answers for ALL creative tasks** — Poetry, prose, translation
- **Use native-level literary/professional texts** — No simplification
- **Focus on stylistic precision** — Nuanced register/style control
- **Require meta-linguistic commentary** — "Why did you choose this word?"
- **Teach transferable professional skills** — Universal templates, strategies
- **Scale complexity from C1** — Longer texts, deeper analysis, original creation

---

## Pre-Submission Checklist

### Content
- [ ] 2200+ words before activities
- [ ] 40+ vocabulary items in 3-column format
- [ ] 600-1000+ word reading passages
- [ ] Creative/productive tasks (original writing, translation, transformation)
- [ ] Model Answers for ALL creative tasks (gold standard)
- [ ] 7-8 engagement boxes (all in Ukrainian)
- [ ] Native-level complexity throughout

### Activities
- [ ] 14-16 activities minimum (quality over quantity)
- [ ] All activity types represented
- [ ] Creative production activities included
- [ ] Writing tasks include rubrics AND Model Answers
- [ ] Meta-linguistic activities included
- [ ] Instructions in Ukrainian

### Immersion & Quality
- [ ] 98-100% Ukrainian (English only in vocabulary "Переклад" column)
- [ ] Native-level texts (no simplification)
- [ ] Creative production demonstrated
- [ ] Stylistic precision shown
- [ ] Meta-linguistic awareness required
- [ ] No pedagogical violations

### Audit
- [ ] Module passes `python3 scripts/audit_module.py`
- [ ] Immersion ≥98%
- [ ] Vocabulary count matches frontmatter
- [ ] All activities formatted correctly

---

## Related Documentation

- **C2 Curriculum Plan:** `docs/l2-uk-en/C2-CURRICULUM-PLAN.md`
- **C2 Improvement Plan:** `docs/l2-uk-en/C2-IMPROVEMENT-PLAN.md`
- **C1 Module Template:** `docs/l2-uk-en/templates/c1-module-template.md`
- **Module Richness Guidelines:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- **Activity Markdown Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`
- **Ukrainian State Standard 2024:** `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt`

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
**Maintainer:** Claude (The Content Developer)
