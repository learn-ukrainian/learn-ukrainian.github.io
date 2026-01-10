# C1 Module Template

**Purpose:** Reference template for creating C1 modules (M01-160: Academic Foundation, Professional, Biographies, Stylistics, Folk Culture, Literature)

**Based on:** B2-module-template.md, scaled to C1 requirements per Ukrainian State Standard 2024

**Related Issue:** [#293](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/293)


<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст|Розминка
  - Аналіз
  - Підсумок
  - Потрібно більше практики?
  pedagogy: Immersion
  min_word_count: 2000
  required_callouts: []
  description: C1 base template with academic immersion and analysis
-->

---

## Quick Reference Checklist

Before submitting a C1 module, verify:

### Content Requirements
- [ ] **Word count:** 2000+ words (core prose: explanations, examples, engagement boxes — excludes vocabulary section, activities section, and tables)
- [ ] **Vocabulary:** 35+ items in 3-column format (Слово | Переклад | Примітки)
- [ ] **Text passages:** 500-800+ word university-level texts
- [ ] **Comparative analysis:** Module compares 2+ texts/perspectives
- [ ] **Writing support:** ALL writing tasks include Model Answers
- [ ] **Engagement boxes:** 6-7 boxes with academic/cultural depth

### Activity Requirements
- [ ] **Activities:** 16+ minimum (C1 standard)
- [ ] **Activity density:**
  - Quiz: 12+ items
  - Fill-in: 12+ items
  - Unjumble: 10+ items
  - Cloze: 20+ blanks in passage
  - Group-sort: 18+ items
  - Error-correction: 10+ items with all 4 callouts
  - Translate: 10+ items (literary/academic translation)
  - Mark-the-words: 500+ word passage
  - Text-comparison: 2+ texts analyzed

### Immersion & Quality
- [ ] **Immersion:** 100% Ukrainian (English ONLY in vocabulary translations)
- [ ] **Academic rigor:** University-level complexity
- [ ] **Comparative analysis:** Multiple texts/perspectives compared
- [ ] **Register mastery:** Sophisticated register use and awareness
- [ ] **No violations:** Check for pedagogical red flags

---

## Module Structure Template

### 1. Frontmatter (YAML)

```yaml
---
module: c1-XXX  # M001-160 (3-digit numbering)
title: "Ukrainian Title"
subtitle: "English subtitle"
version: "1.0"
phase: "C1.X [Phase Name]"  # C1.1, C1.2, C1.3, C1.4, C1.5, C1.6
pedagogy: "Academic"  # Or "Comparative Analysis", "Critical Reading"
duration: 120  # minutes (longer than B2)
transliteration: none
immersion: 100
tags:
  - [module-type]  # academic, professional, biography, stylistics, folk-culture, literature
  - [topic-tag]
grammar:
  - "Advanced grammar concept (e.g., Archaic forms in literature)"
  - "Stylistic device"
objectives:
  - "Learner can analyze [concept] in authentic Ukrainian academic/literary texts"
  - "Learner can compare [multiple perspectives/texts]"
  - "Learner can produce [academic writing type] at C1 level"
vocabulary_count: 35  # Must match count in vocabulary/{slug}.yaml
---
```

**New C1 fields:**
- `duration: 120`: C1 modules require more time (vs. 90 for B2)
- `pedagogy: "Academic"`: Reflects university-level approach
- `text_type`: Type of text featured (academic papers, literature, journalism, professional)

---

## What Makes C1 Different from B2

| Aspect | B2 | C1 |
|--------|----|----|
| **Philosophy** | "Reading to learn" | "Studying IN Ukrainian" |
| **Word count** | 1800+ | 2000+ |
| **Vocabulary** | 30+ | 35+ |
| **Activities** | 14+ | 16+ |
| **Passages** | 300-500 words | 500-800+ words |
| **Complexity** | Authentic-style | University-level authentic |
| **Analysis** | Comprehension | Comparative, critical analysis |
| **Writing** | Essays, reports | Academic papers, critiques, research |
| **Register** | Awareness | Mastery + shifting |

**Key shift:** At C1, learners don't just understand Ukrainian — they analyze it critically, compare perspectives, and produce sophisticated academic/professional writing.

---

### 2. Module Title and Motivation Box

```markdown
# Ukrainian Title

> 🎯 **Чому це важливо?**
>
> [3-4 sentences IN UKRAINIAN explaining academic/cultural significance]
> [Connect to university-level scholarship, literary analysis, or professional contexts]
> [Reference State Standard 2024 C1 requirements if relevant]
```

**Example (Literary Analysis module):**
```markdown
# Стилістика Лесі Українки

> 🎯 **Чому це важливо?**
>
> Леся Українка — одна з найбільших поетес української літератури. Її стилістичні прийоми — це майстер-клас використання мови. На рівні C1 ви маєте вміти не тільки читати літературу, але й аналізувати, як письменники створюють смисл через стиль. Цей модуль навчить вас розпізнавати метафори, іронію, алюзії — інструменти, якими Українка будує свої тексти.
```

**Critical:** Motivation box must reflect **academic depth** and **critical thinking**.

---

### 3. Content Sections (2000+ words total)

**Structure for Academic/Comparative Analysis:**

#### Section 1: Presentation of Primary Texts — 500-800 words

- Present 2-3 authentic texts (poems, excerpts, academic passages, journalistic pieces)
- No simplification — university-level complexity
- Provide context (author, historical period, cultural significance)

```markdown
## Текст 1: [Title]

**Контекст:**
[Brief context about author, period, genre]

[500-800 word primary text — poem, essay excerpt, academic passage, etc.]

## Текст 2: [Title]

**Контекст:**
[Context for second text]

[500-800 word text providing contrasting perspective or complementary analysis]
```

#### Section 2: Comparative Analysis — 800-1000 words

- Guide learners through systematic comparison
- Analyze style, register, rhetorical devices
- Discuss cultural/historical context
- Encourage critical thinking

```markdown
## Порівняльний аналіз

### Стилістичні засоби

**Текст 1:**
- [Analysis of stylistic devices: metaphor, irony, hyperbole, etc.]
- Приклад: [Quote + analysis]

**Текст 2:**
- [Analysis of stylistic devices in second text]
- Приклад: [Quote + analysis]

### Регістр і тон

| Аспект | Текст 1 | Текст 2 |
|--------|---------|---------|
| Регістр | [Identify register] | [Identify register] |
| Тон | [Analyze tone] | [Analyze tone] |
| Лексика | [Vocabulary characteristics] | [Vocabulary characteristics] |

### Культурний контекст

[Discuss how cultural/historical context shapes each text]

### Критичне мислення

[Questions for deeper reflection]
- Яка позиція автора?
- Як стиль підтримує аргумент?
- Які припущення лежать в основі тексту?
```

#### Section 3: Academic Writing/Production — 400-600 words

- Writing task requiring C1-level production
- Model Answer provided
- Rubric for self-assessment

```markdown
## Письмо: Критичне есе

**Завдання:**
Напишіть критичне есе (400+ слів), порівнюючи два тексти.

**Структура:**
1. Вступ (теза)
2. Аналіз тексту 1 (стиль, регістр, прийоми)
3. Аналіз тексту 2
4. Порівняння
5. Висновок

**Зразок відповіді (Model Answer):**

[Provide complete 400+ word essay showing:
- C1-level academic register
- Comparative analysis
- Sophisticated argumentation
- Stylistic awareness
- Proper citation/referencing]

**Рубрика:**

| Критерій | Опис | Очікування на C1 |
|----------|------|------------------|
| Аналіз | Глибина інтерпретації | Розпізнає стилістичні прийоми, пояснює їх функцію |
| Порівняння | Систематичне зіставлення | Чітка структура порівняння |
| Аргументація | Логіка, докази | Теза підтримана цитатами й аналізом |
| Регістр | Академічний стиль | Науковий регістр, відповідна лексика |
| Граматика | Складні конструкції | Безпомилкове використання |
```

---

### 4. Vocabulary Section (Словник)

**CRITICAL:** Vocabulary must be defined in `vocabulary/{slug}.yaml`. Do NOT embed a vocabulary table in Markdown.

**Example `vocabulary/c1-XX-academic.yaml`:**

```yaml
items:
- lemma: метафора
  ipa: /mɛˈtɑfɔrɑ/
  translation: metaphor
  pos: ім. (ж.р.)
  note: stylistic device
- lemma: іронія
  ipa: /iˈrɔnʲijɑ/
  translation: irony
  pos: ім. (ж.р.)
  note: stylistic device
```

**C1 Vocabulary Notes:**
- **35+ items minimum** (vs. 30+ for B2)
- **Specialized terminology:** Literary, academic, professional domains
- **Note field:** Etymology, collocations, register notes, usage examples
- **Context-rich:** Vocabulary should reflect module's academic/professional focus

---

### 5. Activities Section (Активності)

**Minimum:** 16+ activities (vs. 14+ for B2)

### CRITICAL: Language Practice, Not Content Testing

<critical>

**Activities test LANGUAGE SKILLS, not content recall.**

C1 modules teach both Ukrainian AND subject matter (academic, literary, cultural, etc.). Activities practice only Ukrainian language using content as context.

**✅ CORRECT:** "Згідно з текстом, як автор аналізує..." (requires reading Ukrainian)
**❌ WRONG:** "У якому році це відбулося?" (tests content recall, not language)

**Key Test:** Can the learner answer without reading the Ukrainian text? If yes, rewrite.

| Component | Purpose |
|-----------|---------|
| **Lesson Content** | Teaches BOTH Ukrainian language AND subject knowledge |
| **Activities** | Practice ONLY Ukrainian language skills using content as context |

**Activity Types and Their Language Focus:**
- **quiz**: Test reading comprehension — "Згідно з текстом модуля..."
- **fill-in**: Test vocabulary/collocations from module
- **match-up**: Test vocabulary — Ukrainian terms ↔ Ukrainian definitions
- **cloze**: Test vocabulary in context
- **group-sort**: Test categorization using module vocabulary
- **mark-the-words**: Test grammar/stylistic recognition in text
- **error-correction**: Test grammar, NOT content facts

</critical>

---

**Activity Mix for C1:**

#### Core Activities (Must Have)
1. **quiz** (12+ items)
2. **fill-in** (12+ items, academic/literary context)
3. **unjumble** (10+ items)
4. **cloze** (20+ blanks, 500+ word passage)
5. **error-correction** (10+ items with all 4 callouts)
6. **group-sort** (18+ items, sophisticated categories)

**Sentence Complexity:** See `scripts/audit/config.py` ACTIVITY_COMPLEXITY['C1'] for CEFR-aligned word count targets

#### C1-Specific Activities
7. **text-comparison** (Analyze 2+ texts side-by-side)
8. **register-identification** (Identify register, justify with evidence)
9. **stylistic-analysis** (Identify metaphors, irony, hyperbole, etc.)
10. **dialect-recognition** (Identify dialectal markers)
11. **archaic-forms** (Recognize старі forms in literature)
12. **translation-comparison** (Compare translations, discuss choices)

#### Advanced Writing/Production (Use new Schema types)
13. **[essay-response]** (400+ words, Argumentative/Academic)
    *   *Must include `rubric` and `model_answer` in YAML.*
14. **[comparative-study]** (Compare 2+ texts/perspectives)
    *   *Define `items_to_compare` and `criteria`.*
15. **[critical-analysis]** (Deconstruct bias/tone)
    *   *Use `focus_points` to guide analysis.*
16. **[authorial-intent]** (Evaluate purpose)
    *   *Identify specific techniques used by the author.*

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/c1-XX-academic.yaml`:**

```yaml
- type: quiz
  title: Розуміння тексту
  items:
    - question: Згідно з текстом, як автор аналізує метафору?
      options:
        - text: Як засіб образності
          correct: true
        - text: Як помилку
          correct: false

- type: essay-response
  title: Критичне есе
  instruction: Напишіть есе (400+ слів), порівнюючи два тексти.
  prompt: Порівняйте використання іронії в текстах А і Б.
  model_answer: (Sample essay...)
  rubric: (Evaluation criteria...)
```

---

### 6. Engagement Boxes (6-7 boxes)

**C1 Engagement Box Types:**

```markdown
> 💡 **Лінгвістичне спостереження**
>
> [Deep linguistic insight IN UKRAINIAN about language patterns, etymology, or usage]

> 📚 **Літературний контекст**
>
> [Discussion of how this concept appears in Ukrainian literature]

> 🎓 **Академічна перспектива**
>
> [How scholars analyze this concept; reference research if relevant]

> 🌍 **Культурна значущість**
>
> [Why this matters in Ukrainian culture/history]

> ⚠️ **Складність для іноземців**
>
> [What makes this challenging for non-native speakers; L1 interference]

> 🔍 **Порівняння регістрів**
>
> [Same concept in different registers — show variation]

> 🗣️ **Діалектні варіанти**
>
> [How this appears in different Ukrainian dialects]
```

**Critical:** ALL engagement boxes in Ukrainian, reflect **academic depth**.

---

## C1-Specific Pedagogical Notes

### 1. Academic Rigor

**C1 texts are university-level:**
- Literary excerpts (poetry, prose)
- Academic journal articles
- Professional reports
- Journalistic analysis (opinion pieces, critiques)

**No simplification.** If a text is complex, provide context, but don't water it down.

### 2. Comparative Analysis (Mandatory)

**Every C1 module should include comparison:**
- Two poems by different authors
- Academic article vs. journalistic treatment
- Historical sources with opposing views
- Translation vs. original text

**Comparison develops critical thinking:**
- How do style/register differ?
- What assumptions underlie each text?
- How does context shape meaning?

### 3. Register Mastery

**C1 learners must MASTER all 5 registers:**
- Офіційно-діловий: Produce contracts, official letters
- Науковий: Write research abstracts, academic papers
- Публіцистичний: Write opinion pieces, critiques
- Художній: Analyze literary style, recognize devices
- Розмовний: Understand jokes, wordplay, idioms

**Register shifting:** Learners should transform texts from one register to another.

### 4. Archaic & Dialectal Forms

**C1 introduces forms not in modern standard:**
- **Archaic:** старі verb forms, Church Slavonic influences
- **Dialectal:** Polissian, Galician, Slobozhan markers
- **Surzhyk:** Recognition and analysis of Russian-Ukrainian mixing

**Purpose:** Full understanding of Ukrainian in all its forms (literary, historical, regional).

### 5. Rhetorical Devices (Стилістичні засоби)

**C1 learners must recognize and analyze:**
- Метафора (metaphor)
- Іронія (irony)
- Гіпербола (hyperbole)
- Літота (litotes)
- Евфемізм (euphemism)
- Алюзія (allusion)

**Analysis includes:** Identifying device, explaining function, discussing effect.

### 6. Model Answers for ALL Writing

**C1 writing tasks are sophisticated:**
- Academic essays (400+ words)
- Critical reviews (comparing multiple sources)
- Research abstracts (structured, formal)
- Literary analysis (close reading)

**Model Answers must demonstrate:**
- C1-level academic register
- Sophisticated argumentation
- Proper structure
- Stylistic awareness
- Citation/referencing (if applicable)

### 7. Complexity Scaling (B2 → C1)

| Feature | B2 | C1 |
|---------|----|----|
| Word count | 1800+ | 2000+ |
| Vocabulary | 30+ | 35+ |
| Activities | 14+ | 16+ |
| Quiz words/question | 15-25 | 18-30 |
| Unjumble words/sentence | 15-20 | 18-25 |
| Cloze blanks | 16+ | 20+ |
| Passages | 300-500 words | 500-800+ words |
| Complexity | Authentic-style | University-level authentic |
| Analysis | Comprehension | Comparative, critical |

---

## Module Type Breakdown

### C1.1: Academic Foundation (M01-20)

**Focus:** Academic register, research writing, formal argumentation
**Pedagogy:** Academic analysis
**Activities:** 16+ (heavy on academic writing, text analysis)
**Word count:** 2000+
**Passages:** Academic journal articles, textbook excerpts (500-800 words)

**Example modules:**
- M01-05: Academic writing conventions
- M06-10: Research abstracts and summaries
- M11-15: Formal argumentation
- M16-20: Academic Checkpoint

### C1.2: Professional & Social (M21-35)

**Focus:** Professional registers, workplace communication, social contexts
**Pedagogy:** Professional simulation
**Activities:** 14-16 (professional writing, register transformation)
**Word count:** 2000+

**Example modules:**
- M21-25: Official/bureaucratic register
- M26-30: Professional correspondence
- M31-35: Professional Checkpoint

### C1.3: Biographies (M36-100)

**Focus:** 65 Ukrainian historical/cultural figures
**Pedagogy:** Biographical narrative + analysis
**Activities:** 12-14 (comprehension, vocabulary in context)
**Word count:** 2000+
**Passages:** 600+ word biographical accounts

**Example modules:**
- M36-50: Pre-modern figures (Kyivan Rus, Cossack era)
- M51-75: 19th-20th century figures (writers, artists, activists)
- M76-100: Contemporary figures (post-independence)

**Critical:** Gender/era balance, cultural diversity

### C1.4: Advanced Stylistics & Rhetoric (M101-120)

**Focus:** Rhetorical devices, stylistic analysis, register shifting
**Pedagogy:** Comparative stylistic analysis
**Activities:** 16+ (stylistic identification, register transformation)
**Word count:** 2000+

**Example modules:**
- M101-110: Rhetorical devices (metaphor, irony, hyperbole, etc.)
- M111-115: Register transformation
- M116-120: Stylistics Checkpoint

### C1.5: Folk Culture & Arts (M121-145)

**Focus:** Traditional Ukrainian culture (music, art, beliefs, crafts)
**Pedagogy:** Cultural analysis
**Activities:** 12-14 (cultural comprehension, vocabulary)
**Word count:** 2000+

**Example modules:**
- M121-130: Traditional music and folk songs
- M131-140: Traditional arts and crafts
- M141-145: Folk Culture Checkpoint

### C1.6: Literature - Complete (M146-160)

**Focus:** Ukrainian literary canon (classics + contemporary)
**Pedagogy:** Literary analysis, close reading
**Activities:** 12-14 (text analysis, stylistic devices)
**Word count:** 2000+
**Passages:** Poetry, prose excerpts (500-800 words)

**Example modules:**
- M146-152: Classics (Shevchenko, Franko, Lesya Ukrainka)
- M153-158: Contemporary literature (post-independence)
- M159: Literature Review
- M160: C1 Final Exam (Checkpoint)

---

## Common Pitfalls to Avoid

### ❌ DON'T:
- **Don't simplify texts** — C1 requires university-level complexity
- **Don't skip comparative analysis** — C1 is about critical thinking
- **Don't use only one text** — Always compare perspectives
- **Don't ignore register mastery** — C1 must demonstrate full register control
- **Don't skip archaic/dialectal forms** — C1 includes full language awareness
- **Don't under-count activities** — 16+ is the minimum

### ✅ DO:
- **Use authentic university-level texts** — Academic papers, literary excerpts
- **Compare multiple texts/perspectives** — Develop critical analysis
- **Provide Model Answers for all writing** — Support sophisticated production
- **Teach archaic and dialectal forms** — Full language mastery
- **Analyze rhetorical devices systematically** — Name, identify, explain function
- **Scale complexity from B2** — Longer texts, more activities, deeper analysis

---

## Pre-Submission Checklist

### Content
- [ ] 2000+ words before activities
- [ ] 35+ vocabulary items in 3-column format
- [ ] 500-800+ word reading passages
- [ ] Comparative analysis of 2+ texts
- [ ] Model Answers for ALL writing tasks
- [ ] 6-7 engagement boxes (all in Ukrainian)
- [ ] Academic rigor throughout

### Activities
- [ ] 16+ activities minimum
- [ ] All activity types represented
- [ ] Activity density meets C1 standards
- [ ] Writing tasks include rubrics
- [ ] Comparative/analytical activities included
- [ ] Instructions in Ukrainian

### Immersion & Quality
- [ ] 100% Ukrainian (English only in vocabulary "Переклад" column)
- [ ] University-level texts (no simplification)
- [ ] Critical analysis demonstrated
- [ ] Register mastery shown
- [ ] No pedagogical violations

### Audit
- [ ] Module passes `python3 scripts/audit_module.py`
- [ ] Immersion ≥98%
- [ ] Vocabulary count matches frontmatter
- [ ] All activities formatted correctly

---

## Related Documentation

- **C1 Curriculum Plan:** `docs/l2-uk-en/C1-CURRICULUM-PLAN.md`
- **C1 Improvement Plan:** `docs/l2-uk-en/C1-IMPROVEMENT-PLAN.md`
- **B2 Module Template:** `docs/l2-uk-en/templates/b2-module-template.md`
- **Module Richness Guidelines:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- **Activity Markdown Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`
- **Ukrainian State Standard 2024:** `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt`

---

## Clean MD Architecture Note

### Activities, Vocabulary, and External Resources

**CRITICAL:** Do NOT add `## Activities`, `## Vocabulary`, or `## External Resources` headers to the Markdown file. These sections are automatically injected by the build system from the corresponding YAML sidecars:

- `activities/{slug}.yaml` → `## Activities` section
- `vocabulary/{slug}.yaml` → `## Vocabulary` section
- `docs/resources/external_resources.yaml` (filtered by `module_id`) → `## External Resources` section

The module structure follows **Clean MD architecture**: Markdown contains narrative content only, YAML sidecars contain structured data.

---

**Last Updated:** 2025-12-24
**Template Version:** 1.0
**Maintainer:** Claude (The Content Developer)
