# B1 Integration Module Template

**For:** B1 Phase 8 - Skills & Integration (Modules 81-85)
**Examples:** M81 (Новини - як читати), M82 (Інтерв'ю та подкасти), M83 (Grammar Integration), M84 (Vocabulary Integration), M85 (B1 Capstone)

---

## Quick Reference Checklist

Before submitting your integration module, verify:

- [ ] **Word count:** 1500+ words (M81-84), 1200+ (M85 Capstone)
- [ ] **Vocabulary:** 15-20 items in 5-column format with IPA (lower than regular modules - these are review/meta modules)
- [ ] **Activities:** 8-10 activities for M81-84 (quality over quantity), 5-8 activities + 5 tasks for M85 Capstone
- [ ] **Authentic materials:** 5+ authentic Ukrainian texts/resources (news, podcasts, interviews)
- [ ] **Sentence complexity:** Validated by audit (see `scripts/audit/config.py` for CEFR-aligned targets)
- [ ] **Cloze passages:** 14+ blanks
- [ ] **Engagement boxes:** 5+ (focus on learning strategies)
- [ ] **Immersion:** 90-100% Ukrainian
- [ ] **External resources:** Added to `docs/resources/external_resources.yaml` (NOT embedded in module)
- [ ] **Meta-level guidance:** Explicit instruction on HOW to read/listen/integrate
- [ ] **B2 readiness check:** Explicitly prepares for next level

<!--
TEMPLATE_METADATA:
  required_sections:
  - Огляд
  - Інтеграція
  - Підсумок
  - Потрібно більше практики?
  pedagogy: TTT
  min_word_count: 1500
  required_callouts: []
  description: B1 integration combines multiple grammar points
-->

---

## Key Integration Module Characteristics

**Different from all previous B1 modules:**

1. **Meta-Skills Focus**
   - Not teaching new grammar or vocabulary
   - Teaching HOW to use Ukrainian (reading strategies, listening strategies, integration)
   - Preparing for autonomous learning at B2

2. **Authentic Material Heavy**
   - Real Ukrainian news articles (М81)
   - Real podcasts and interviews (М82)
   - Real-world application of grammar (М83)
   - Real-world use of vocabulary (М84)

3. **Lower New Vocabulary**
   - 15-20 words (vs 25+ for regular modules)
   - Mostly meta-language (e.g., заголовок, лід, підзаголовок for M81)
   - Review of previous vocabulary dominates

4. **Integration Emphasis**
   - М81-82: Skills integration (reading + listening)
   - М83: Grammar integration (all B1 grammar)
   - М84: Vocabulary integration (all B1 vocabulary)
   - М85: Comprehensive integration (all skills)

5. **B2 Bridge**
   - Explicitly prepares for B2 level
   - Shows what B2 will expect
   - Self-assessment of B1 mastery

---

## Module Types in B1.8

### Type 1: Skills Modules (M81-82)

**M81: Новини - як читати (News Reading)**

- Focus: Reading strategies for news
- Meta-vocabulary: заголовок, лід, підзаголовок, факт vs думка
- Activities: Analyzing headlines, identifying main points, fact vs opinion

**M82: Інтерв'ю та подкасти (Interviews and Podcasts)**

- Focus: Listening strategies
- Meta-vocabulary: інтерв'ю, подкаст, ведучий, нотатки
- Activities: Note-taking, summarizing, comprehension

**Structure:** PPP with explicit strategy instruction

---

### Type 2: Integration Modules (M83-84)

**M83: B1 Grammar Integration**

- Focus: All B1 grammar reviewed
- Areas: Aspect, motion verbs, complex sentences, participles
- Activities: Mixed grammar tasks, error correction, production

**M84: B1 Vocabulary Integration**

- Focus: All B1 vocabulary reviewed
- Domains: Abstract concepts, opinions, culture, professional
- Activities: Collocations, register, cross-domain usage

**Structure:** TTT (test existing knowledge → review gaps → test again)

---

### Type 3: Capstone Module (M85)

**M85: B1 Capstone**

- Focus: Comprehensive B1 assessment
- All skills: Reading, writing, listening, grammar, vocabulary
- Can-do assessment checklist
- B2 readiness evaluation

**Structure:** Comprehensive testing (no new teaching)

---

## Template Structure by Module Type

### Type 1: Skills Module (M81-82)

#### Frontmatter

```yaml
---
module: [81 or 82]
title: [Ukrainian title]
subtitle: [English subtitle]
level: B1
phase: B1.8
pedagogy: PPP
objectives:
  - Learner can apply [skill] strategies to authentic Ukrainian texts
  - Learner can identify [specific elements] in authentic materials
  - Learner can produce [output] based on authentic input
  - Learner is prepared for autonomous [skill] practice at B2
word_target: 1500
vocab_target: 15-20 # Must match count in vocabulary/{slug}.yaml
immersion_target: 90-95%
---
```

**WHY these objectives:** Skills modules develop meta-cognitive strategies, not grammar/vocabulary.

---

#### Section 1: Вступ (Introduction) - 200-300 words

**Purpose:** Introduce the meta-skill and why it matters

**Structure:**

##### Opening Hook (50-100 words)

- Why this skill is important for B2 readiness
- Example: "Читання новин українською — це ключовий навик для B2 рівня..."

##### Strategy Overview (100-150 words)

- What strategies will be taught
- Example (M81): "Ви навчитеся розуміти заголовки, знаходити головну думку, відрізняти факти від думок..."

##### Meta-Vocabulary Preview (50-100 words)

- Introduce 5-8 key meta-terms
- Example (M81): "**заголовок** (headline), **лід** (lead), **підзаголовок** (subheading)..."

**Engagement Box (1):**

> 💡 **Чи знали ви:** [Strategy tip or learning hack]

---

#### Section 2: Презентація (Presentation) - 600-800 words

**Purpose:** Teach the meta-skill through explicit strategy instruction + examples

**Structure:**

##### Strategy 1: [Name] (150-200 words)

- What it is
- Why it's useful
- How to apply it
- Example using authentic Ukrainian text

**Example (M81 - Understanding Headlines):**

```markdown
#### Стратегія 1: Розуміння заголовків

**Що це?**
Заголовок — це перше, що ви читаєте в новині. Він часто містить головну думку всієї статті.

**Навіщо це потрібно?**
Якщо ви розумієте заголовок, ви можете швидко вирішити, чи варто читати всю статтю.

**Як це робити?**

1. Читайте заголовок повільно
2. Визначте ключові слова (хто, що, де)
3. Спробуйте передбачити, про що стаття

**Приклад:**

> **Заголовок:** "Україна виграла «Євробачення» вдруге за десять років"
>
> - **Хто?** Україна
> - **Що зробила?** Виграла Євробачення
> - **Коли?** Вдруге за десять років
> - **Прогноз:** Стаття про перемогу на Євробаченні, можливо про виконавця та пісню
```

##### Strategy 2: [Name] (150-200 words)

- Same structure as Strategy 1

##### Strategy 3: [Name] (150-200 words)

- Same structure

##### Authentic Text with Strategy Application (200-300 words)

- Full authentic Ukrainian text (news article for M81, interview excerpt for M82)
- Annotations showing strategies in action
- Comprehension questions

**WHY 3 strategies:** Focused skill development, manageable cognitive load.

**Engagement Boxes (2-3):**

> 🌍 **Реальний світ:** [Where/how to practice this skill]
> 🎯 **Цікавий факт:** [Interesting fact about Ukrainian news/podcasts]

---

#### Section 3: Практика (Practice) - 400-600 words

**Purpose:** Apply strategies to multiple authentic texts

**Structure:**

##### Практика Text 1 (150-200 words)

- Authentic Ukrainian text
- Strategy application tasks
- Comprehension questions

##### Практика Text 2 (150-200 words)

- Different authentic text
- More complex strategy application
- Comprehension questions

##### Практика Text 3 (100-150 words)

- Most challenging text
- Independent strategy application
- Comprehension questions

**WHY 3 texts:** Progressive difficulty, builds confidence, prepares for autonomous practice.

---

#### Section 4: Продукція (Production) - 200-300 words

**Purpose:** Demonstrate strategy mastery through production

**Structure:**

##### Продукція Task (100-150 words)

- Example (M81): "Write a news headline and lead for this event..."
- Example (M82): "Record a 1-minute summary of the podcast..."

##### Self-Assessment (50-100 words)

- Checklist: "Can I...?"
- Example: "Чи можу я розуміти заголовки українських новин?"

##### B2 Preview (50-100 words)

- What's next at B2
- Example: "На рівні B2 ви будете читати довгі статті про складні теми..."

**Engagement Box (1):**

> 🎯 **Next Steps:** [How to continue practicing at B2]

---

#### Section 5: Підсумок (Summary) - 100-200 words

**Purpose:** Recap strategies and encourage autonomous practice

**Structure:**

##### Strategies Learned (50-100 words)

- List 3 key strategies
- Quick reminder of each

##### How to Practice (50-100 words)

- Where to find authentic materials
- How often to practice
- What to focus on

---

#### Section 6: Вправи (Activities)

**8-10 activities** (reduced from 12+, Jan 2026) focused on strategy application

**Activity Mix for Skills Modules:**

| Activity Type    | Count       | Priority | Purpose                                                  |
| ---------------- | ----------- | -------- | -------------------------------------------------------- |
| quiz             | 10-12 items | HIGH     | Reading/listening comprehension, strategy identification |
| true-false       | 10-12 items | HIGH     | Fact verification, headline analysis                     |
| match-up         | 12+ items   | HIGH     | Match headlines to articles, speakers to quotes          |
| fill-in          | 12+ items   | MEDIUM   | Complete summaries, fill in key information              |
| cloze            | 14+ blanks  | MEDIUM   | Passage completion from authentic text                   |
| group-sort       | 16+ items   | MEDIUM   | Categorize (fact vs opinion, main vs detail)             |
| select           | 8+ items    | MEDIUM   | Identify all correct answers                             |
| unjumble         | 8+ items    | LOW      | Reconstruct sentences from authentic texts               |
| error-correction | 8+ items    | LOW      | Common reading/listening errors                          |
| mark-the-words   | 8+ words    | LOW      | Identify key words in passage                            |

**WHY this mix:** Skills modules prioritize comprehension and strategy application over production.

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/b1-81-news-reading.yaml`:**

```yaml
- type: quiz
  title: Розуміння заголовків
  instruction: Прочитайте заголовок і виберіть правильну інтерпретацію.
  items:
    - question: Що означає заголовок "Україна здобула перемогу"?
      options:
        - text: Україна виграла
          correct: true
        - text: Україна програла
          correct: false
```

---

#### Section 7: Словник (Vocabulary)

**CRITICAL:** Vocabulary must be defined in `vocabulary/{slug}.yaml`. Do NOT embed a vocabulary table in Markdown.

**Example `vocabulary/b1-81-news-reading.yaml`:**

```yaml
items:
  - lemma: заголовок
    ipa: /zɑhoˈlɔvɔk/
    translation: headline
    pos: ім. (ч.р.)
    gender: m
    note: перший рядок новини
  - lemma: лід
    ipa: /lid/
    translation: lead (journalism)
    pos: ім. (ч.р.)
    gender: m
    note: перший абзац, головна інформація
```

---

#### Section 8: External Resources

> **⚠️ NOTE:** External resources are managed in `docs/resources/external_resources.yaml`, NOT in module markdown files. Do NOT add `[!resources]` blocks to modules.

**To add resources for skills modules:**

1. Open `docs/resources/external_resources.yaml`
2. Add entries with the module ID:

```yaml
# For M81 (News Reading)
- module_id: b1-81
  url: 'https://www.pravda.com.ua/'
  title: 'Українська правда'
  type: website
  relevance: 5

- module_id: b1-81
  url: 'https://hromadske.ua/'
  title: 'Громадське'
  type: website
  relevance: 5

# For M82 (Podcasts)
- module_id: b1-82
  url: 'https://bookforum.ua/podcast/'
  title: 'Книжковий Арсенал'
  type: podcast
  relevance: 5
```

**Resource types:** `website`, `article`, `video`, `podcast`, `book`, `music`

**WHY extensive resources:** Skills modules prepare learners for autonomous practice.

---

### Type 2: Integration Module (M83-84)

Integration modules use **TTT structure** (Test-Teach-Test), similar to checkpoint modules.

#### Frontmatter

```yaml
---
module: [83 or 84]
title: [Ukrainian title - e.g., 'B1 Grammar Integration']
subtitle: [English subtitle]
level: B1
phase: B1.8
pedagogy: TTT
objectives:
  - Learner can demonstrate mastery of all B1 [grammar/vocabulary]
  - Learner can apply [grammar/vocabulary] in integrated contexts
  - Learner can identify and correct [grammar/vocabulary] errors
  - Learner is prepared for B2 [grammar/vocabulary] challenges
word_target: 1500
vocab_target: 15
immersion_target: 90-95%
---
```

---

#### Section 1: Діагностика (Diagnostic Test) - 200-300 words

**Purpose:** Test current knowledge without scaffolding

**Structure:**

##### Diagnostic Activity (150-250 words)

- Comprehensive quiz covering all B1 areas
- No hints, no scaffolding
- Reveals gaps

**Example (M83 - Grammar Integration):**

```markdown
#### Діагностичний тест: Вся граматика B1

**Instructions:** Complete these sentences using correct grammar. No hints provided.

1. Я **\_\_\_** (читати/прочитати) цю книгу вчора. (aspect choice)
2. Ми **\_\_\_** (йти/піти) до університету щодня. (motion verbs)
3. Якщо **\_\_\_** (мати) час, я **\_\_\_** (допомогти) тобі. (conditionals)
4. Текст, **\_\_\_** (писати/написаний) студентом, був дуже цікавий. (participles)
   ... [20-30 diagnostic items]
```

**WHY diagnostic:** Reveals what learners remember vs what needs review.

---

#### Section 2: Аналіз (Review / Teach) - 600-800 words

**Purpose:** Comprehensive review of all B1 content

**Structure (M83 - Grammar Integration):**

##### Grammar Area 1: Aspect (150-200 words)

- Quick review of aspect rules
- Common errors reminder
- Context: Past, future, negation, imperatives

##### Grammar Area 2: Motion Verbs (150-200 words)

- Prefix system review
- Common motion verbs
- Figurative uses

##### Grammar Area 3: Complex Sentences (150-200 words)

- All clause types (relative, purpose, conditional, concessive, causal)
- Conjunction review

##### Grammar Area 4: Participles (150-200 words)

- Adverbial participles (-ючи, -вши)
- Passive constructions (-ний, -но, -то)
- Short vs long forms

**Structure (M84 - Vocabulary Integration):**

##### Vocabulary Domain 1: Abstract Concepts (150-200 words)

- Review M51-55 vocabulary
- Collocations and usage

##### Vocabulary Domain 2: Discourse and Opinions (150-200 words)

- Review M56-60 vocabulary
- Register and formality

##### Vocabulary Domain 3: Culture and Regions (150-200 words)

- Review M66-75 vocabulary
- Cultural context

##### Vocabulary Domain 4: Professional and Emotional (150-200 words)

- Cross-domain review
- Synonymy and register

**Engagement Boxes (3-4):**

> 💡 **Common Error:** [Frequent B1 mistake with this grammar/vocabulary]
> 🎯 **Quick Tip:** [Memory aid or learning hack]

---

#### Section 3: Поглиблення (Deeper Testing) - 300-400 words

**Purpose:** Test mastery after review

**Structure:**

##### Integrated Text 1 (150-200 words)

- Authentic Ukrainian text using ALL B1 grammar/vocabulary
- Comprehension + analysis questions
- Error identification tasks

##### Integrated Text 2 (150-200 words)

- More complex authentic text
- Production tasks (rewrite, transform, extend)

**WHY 2 texts:** Progressive difficulty, tests transfer of knowledge.

---

#### Section 4: Практика (Application) - 200-300 words

**Purpose:** Apply integrated knowledge in production

**Structure:**

##### Продукція Task (100-150 words)

- Example (M83): "Write a 200-word text using aspect, motion verbs, complex sentences, and participles."
- Example (M84): "Write a 200-word text using vocabulary from all B1 domains."

##### Self-Assessment (50-100 words)

- B1 grammar/vocabulary checklist
- Gap identification

##### B2 Preview (50-100 words)

- What's next at B2
- How B1 foundations prepare for B2

---

#### Section 5: Підсумок (Summary) - 100-200 words

**Purpose:** Celebrate mastery, encourage continued practice

**Structure:**

##### What You've Mastered (100-150 words)

- List all B1 grammar/vocabulary areas covered
- Acknowledge progress from A2 to B1

##### B1 → B2 Transition (50-100 words)

- How to maintain B1 skills
- What to expect at B2

---

#### Section 6: Вправи (Activities)

**8-10 activities for M83-84** (reduced from 12+, Jan 2026 - quality over quantity)
**5-8 activities + 5 comprehensive tasks for M85** (tasks ARE the main assessment)

**Activity Mix for Integration Modules (M83-84):**

| Activity Type    | Count      | Priority | Purpose                                      |
| ---------------- | ---------- | -------- | -------------------------------------------- |
| quiz             | 8+ items   | HIGH     | All grammar/vocabulary areas                 |
| error-correction | 6+ items   | HIGH     | Common B1 errors                             |
| fill-in          | 8+ items   | HIGH     | Context application                          |
| cloze            | 12+ blanks | HIGH     | Integrated passage                           |
| match-up         | 8+ items   | MEDIUM   | Term to definition, rule to example          |
| unjumble         | 6+ items   | MEDIUM   | Complex sentences (see config.py)              |
| translate        | 6+ items   | MEDIUM   | All grammar/vocabulary contexts              |

**Activity Mix for Capstone (M85):**

**Traditional Activities (5-8 total):**

| Activity Type    | Count      | Purpose                            |
| ---------------- | ---------- | ---------------------------------- |
| quiz             | 8+ items   | Quick comprehension check          |
| error-correction | 6+ items   | Common B1 errors                   |
| cloze            | 12+ blanks | Integrated passage                 |
| fill-in          | 8+ items   | Context application                |

**Comprehensive Tasks (5 required):** See Task-Based Learning section

---

#### Section 7: Словник (Vocabulary)

**15 items** - mostly review, some new meta-language

**Example (M83 - Grammar Integration):**

- граматична категорія, граматична форма, граматична структура (grammar meta-language)
- Review of aspect, motion, participle terminology

**Example (M84 - Vocabulary Integration):**

- синонім, антонім, колокація, регістр (vocabulary meta-language)
- Review of domain-specific terms

---

### Type 3: Capstone Module (M85)

#### Frontmatter

```yaml
---
module: 85
title: B1 Capstone
subtitle: Comprehensive B1 Assessment
level: B1
phase: B1.8
pedagogy: TBL (Task-Based Learning)
objectives:
  - Learner can demonstrate comprehensive B1 mastery across all skills
  - Learner can produce extended written and spoken discourse
  - Learner can comprehend authentic Ukrainian texts and audio
  - Learner is ready to begin B2 level
word_target: 1200
vocab_target: 10
immersion_target: 95-100%
---
```

**WHY TBL:** Capstone is task-based, not teaching.

---

#### Section 1: Вступ (Introduction) - 100-150 words

**Purpose:** Frame the capstone assessment

**Structure:**

##### Capstone Purpose (50-100 words)

- What the capstone assesses
- Why it matters for B2 readiness

##### Assessment Overview (50-100 words)

- 5 comprehensive tasks (reading, writing, listening, grammar, vocabulary)
- How to approach each task

---

#### Section 2: Завдання (Tasks) - 1000-1200 words

**Purpose:** Comprehensive B1 assessment across all skills

**Structure:**

##### Task 1: Reading Comprehension (200-250 words)

- Authentic Ukrainian text (400-500 words)
- 10+ comprehension questions
- Requires aspect, motion verbs, complex sentences, participles

##### Task 2: Extended Writing (200-250 words)

- Prompt: "Write 250 words about [topic requiring all B1 grammar and vocabulary]"
- Example: "Опишіть ваш досвід вивчення української мови: що було складно, що вам подобається, куди ви хочете поїхати в Україні..."
- Rubric provided

##### Task 3: Listening Comprehension (200-250 words)

- Link to authentic Ukrainian podcast/interview (5-10 minutes)
- 10+ comprehension questions
- Note-taking task

##### Task 4: Grammar Comprehensive Test (200-250 words)

- 30+ items covering all B1 grammar
- Aspect, motion, complex sentences, participles
- Mixed formats (quiz, fill-in, error-correction)

##### Task 5: Vocabulary Comprehensive Test (200-250 words)

- 30+ items covering all B1 vocabulary domains
- Abstract, discourse, culture, professional
- Mixed formats (match-up, group-sort, fill-in)

**WHY 5 tasks:** Comprehensive assessment of all B1 competencies.

---

#### Section 3: Самооцінка (Self-Assessment) - 200-300 words

**Purpose:** Learner evaluates own B1 mastery

**Structure:**

##### B1 Can-Do Checklist (100-150 words)

```markdown
#### Чи можу я...?

**Reading:**

- [ ] Розуміти головні думки в стандартних текстах?
- [ ] Читати українські новини і розуміти основний зміст?

**Writing:**

- [ ] Писати зв'язні тексти на знайомі теми (200+ слів)?
- [ ] Описувати досвід, події, мрії?

**Listening:**

- [ ] Розуміти головні думки чіткої стандартної української мови?
- [ ] Слухати українські подкасти і розуміти основний зміст?

**Grammar:**

- [ ] Правильно використовувати вид дієслова у всіх контекстах?
- [ ] Використовувати дієслова руху з префіксами?
- [ ] Будувати складні речення всіх типів?

**Vocabulary:**

- [ ] Використовувати ~3,500 українських слів?
- [ ] Обговорювати абстрактні теми?
- [ ] Висловлювати думки та аргументи?
```

##### Scoring Guide (50-100 words)

- How to interpret self-assessment
- What to review if gaps identified

##### B2 Readiness (50-100 words)

- What B2 will expect
- How to prepare for transition

---

#### Section 4: Підсумок (Summary) - 100-150 words

**Purpose:** Celebrate B1 completion, preview B2

**Structure:**

##### B1 Journey Recap (50-100 words)

- From А1 (Cyrillic) → A2 (Cases) → B1 (Aspect, Motion, Complexity)
- Total progress: ~3,500 words, all major grammar structures

##### Next Steps: B2 Preview (50-100 words)

- B2 Focus: Literature, academic language, professional contexts
- B2 Vocabulary: +2,900 words
- B2 Grammar: Refinement and stylistic mastery

##### Encouragement (20-50 words)

- Congratulate learner
- Encourage continued practice

---

#### Section 5: Вправи (Activities)

**NOTE:** Capstone modules have FEWER traditional activities (5-8) because the 5 comprehensive tasks ARE the activities.

**Activity Mix for Capstone:**

| Activity Type    | Count      | Purpose                       |
| ---------------- | ---------- | ----------------------------- |
| quiz             | 20+ items  | Final grammar/vocabulary test |
| cloze            | 14+ blanks | Final reading comprehension   |
| error-correction | 12+ items  | Final grammar application     |
| fill-in          | 12+ items  | Final context usage           |
| translate        | 10+ items  | Final production              |

**WHY fewer activities:** The 5 comprehensive tasks are the primary assessment.

---

#### Section 6: Словник (Vocabulary)

**10 items** - B2 preview vocabulary

**Example:**

- академічний, професійний, літературний (B2 domains)
- поглиблений, вдосконалений, складний (B2 level descriptors)

**WHY preview vocabulary:** Bridges to B2 level.

---

#### Section 7: External Resources

> **⚠️ NOTE:** External resources are managed in `docs/resources/external_resources.yaml`.

Add B2 preparation resources to `external_resources.yaml` with `module_id: b1-85`:

- Ukrainian State Standard B2 (website)
- CEFR B2 Descriptors (article)
- Ukrainian literature short stories (website)
- Academic texts from universities (article)

---

## Common Pitfalls to Avoid

### 1. **Teaching New Content in Integration Modules**

**Problem:** Integration modules (M83-85) introduce new grammar/vocabulary.
**Fix:** Integration modules REVIEW only. All new content must be taught in M01-82.

**Example:**

- ❌ Bad (M83): "У цьому модулі ми вивчимо нову граматичну структуру..."
- ✅ Good (M83): "У цьому модулі ми повторимо всю граматику B1..."

---

### 2. **Insufficient Authentic Materials**

**Problem:** Skills modules (M81-82) use only constructed examples.
**Fix:** Use REAL Ukrainian news, podcasts, interviews. Adapt if needed, but cite sources.

**Example (M81):**

- ❌ Bad: Made-up news article
- ✅ Good: Adapted article from Українська правда with source citation

---

### 3. **Missing Resources Section**

**Problem:** No links to authentic Ukrainian materials for practice.
**Fix:** Extensive Resources section is MANDATORY for all integration modules.

---

### 4. **Too Many Activities in Capstone (M85)**

**Problem:** 25+ traditional activities in M85.
**Fix:** M85 has 5-8 traditional activities + 5 comprehensive tasks. The tasks ARE the assessment.

---

### 5. **No B2 Preview**

**Problem:** Integration modules don't prepare for B2.
**Fix:** Every integration module MUST include "Next Steps: B2" section.

**Example:**

```markdown
#### Наступний крок: Рівень B2

На рівні B2 ви будете читати складніші тексти: літературу, академічні статті, професійні документи. Ви вивчите ще ~2,900 слів і вдосконалите граматичні навички.
```

---

### 6. **Grammar/Vocabulary Integration Modules Missing Diagnostic Test**

**Problem:** M83-84 jump straight to review without testing current knowledge.
**Fix:** Use TTT structure: Diagnostic → Review → Retest.

---

### 7. **Skills Modules (M81-82) Too Grammar-Heavy**

**Problem:** M81-82 teach grammar instead of reading/listening strategies.
**Fix:** Focus on HOW to read/listen, not grammar rules.

**Example (M81):**

- ❌ Bad: "У заголовках часто використовується доконаний вид..." (grammar focus)
- ✅ Good: "Заголовок містить головну думку. Читайте його спочатку." (strategy focus)

---

### 8. **Capstone Module (M85) Too Easy**

**Problem:** M85 tasks don't comprehensively test B1.
**Fix:** Each task must require ALL B1 grammar and vocabulary.

**Example (M85 Writing Task):**

- ❌ Bad: "Напишіть 100 слів про вашу сім'ю." (A2 level)
- ✅ Good: "Напишіть 250 слів про ваш досвід вивчення української мови. Використайте: дієслова виду (aspect), дієслова руху (motion), складні речення (complex sentences), та пасивні конструкції (passives)." (B1 comprehensive)

---

## Audit Validation Checklist

Before running the audit script, manually verify:

### Content Gates (All Integration Modules):

- [ ] **Authentic materials** - 5+ real Ukrainian texts/resources
- [ ] **Resources section** - Extensive links to Ukrainian materials
- [ ] **B2 preview** - Explicit "Next Steps" section
- [ ] **Word count:** 1500+ words (M81-84), 1200+ (M85)
- [ ] **Vocabulary:** 15-20 items (M81-84), 10 items (M85)

### Skills Modules (M81-82) Specific:

- [ ] **3 strategies** explicitly taught with examples
- [ ] **3 practice texts** (progressive difficulty)
- [ ] **Strategy application** demonstrated in all texts
- [ ] **Production task** requiring strategy use

### Integration Modules (M83-84) Specific:

- [ ] **TTT structure** - Diagnostic → Review → Retest
- [ ] **All B1 content reviewed** - complete coverage
- [ ] **25+ activities** - comprehensive testing
- [ ] **Diagnostic test** without hints

### Capstone Module (M85) Specific:

- [ ] **5 comprehensive tasks** covering all skills
- [ ] **Extended writing task** (250+ words)
- [ ] **Authentic listening** (5-10 min podcast/interview)
- [ ] **Self-assessment checklist** with B1 can-do statements
- [ ] **B2 preview** with specific expectations

### Technical Gates (All):

- [ ] **Sentence complexity:** Validated by audit (see `scripts/audit/config.py` for CEFR-aligned targets)
- [ ] **Cloze passages:** 14+ blanks
- [ ] **Engagement boxes:** 5+ boxes
- [ ] **Immersion:** 90-100% Ukrainian (95-100% for M85)

---

## Creator's Pre-Submission Checklist

### Phase 1: Research (Skills Modules M81-82)

- [ ] Find 5+ authentic Ukrainian texts (news articles, interviews, podcasts)
- [ ] Identify 3 key strategies for the skill
- [ ] Test strategies on authentic materials
- [ ] Extract 15-20 meta-vocabulary items

### Phase 1: Research (Integration Modules M83-84)

- [ ] Review ALL previous B1 modules (M01-80)
- [ ] List all grammar areas (M83) or vocabulary domains (M84)
- [ ] Identify common errors from previous modules
- [ ] Plan comprehensive review structure

### Phase 1: Research (Capstone M85)

- [ ] Design 5 comprehensive tasks covering all B1 skills
- [ ] Find authentic text (400-500 words) and podcast (5-10 min)
- [ ] Create B1 can-do checklist
- [ ] Plan B2 preview

### Phase 2: Content Creation (All)

- [ ] Write Вступ with meta-skill/assessment overview
- [ ] Write main content (Презентація for skills, Аналіз for integration, Завдання for capstone)
- [ ] Write Практика/Продукція with production tasks
- [ ] Write Підсумок with B2 preview
- [ ] Create Resources section with 10+ authentic links

### Phase 3: Activities (All)

- [ ] Create 12+ activities (skills), 25+ (integration), 5-8 (capstone)
- [ ] Sentence complexity validated by audit (see config.py)
- [ ] Sentence complexity validated by audit (see config.py)
- [ ] Verify cloze passage has 14+ blanks
- [ ] Verify all error-correction activities have all 4 callouts

### Phase 4: Vocabulary (All)

- [ ] Create 5-column vocabulary table
- [ ] Add IPA pronunciation for all words
- [ ] 15-20 items (M81-84), 10 items (M85)
- [ ] Include meta-language and review vocabulary

### Phase 5: Engagement (All)

- [ ] Add 5+ engagement boxes (focus on strategies, tips, B2 preview)
- [ ] Verify boxes add value (not filler)

### Phase 6: Audit (All)

- [ ] Run `python3 scripts/audit_module.py curriculum/l2-uk-en/b1/[module-file].md`
- [ ] Fix gate failures
- [ ] Manually verify all checklist items above
- [ ] Verify Resources section has working links

---

## Example Module Outline: M81 - Новини - як читати

**Specification (from B1-CURRICULUM-PLAN.md):**

- **Topic:** News literacy and reading skills
- **Vocabulary:** 20 words (заголовок, лід, підзаголовок, факт, думка, etc.)
- **Skills:** Headlines, main points, fact vs opinion, source evaluation

**Implementation:**

### Frontmatter

```yaml
---
module: 81
title: Новини - як читати
subtitle: News Reading Strategies
level: B1
phase: B1.8
pedagogy: PPP
objectives:
  - Learner can apply news reading strategies to authentic Ukrainian texts
  - Learner can identify headlines, leads, and main points
  - Learner can distinguish fact from opinion in news articles
  - Learner is prepared for autonomous news reading at B2
word_target: 1500
vocab_target: 20
immersion_target: 90-95%
---
```

### Section 1: Вступ (250 words)

"Читання новин українською — це ключовий навик для B2 рівня. Ви навчитеся розуміти заголовки, знаходити головну думку, відрізняти факти від думок..."

> 💡 **Чи знали ви:** Ukrainian news headlines often omit verbs for brevity.

### Section 2: Презентація (700 words)

**Strategy 1: Розуміння заголовків (200 words)**

- What headlines are
- How to read them (identify who, what, where)
- Example from Українська правда

**Strategy 2: Знаходження головної думки (200 words)**

- What a lead (лід) is
- How to identify main points
- Example from BBC News Україна

**Strategy 3: Факти проти думок (200 words)**

- Difference between fact and opinion
- Signal words (на мою думку, експерти вважають)
- Example from Hromadske

**Authentic Article with Annotations (100 words)**

- Full news article with strategy markers

> 🌍 **Реальний світ:** Practice on Українська правда daily
> 🎯 **Цікавий факт:** Ukrainian journalism won European Press Prize in 2022

### Section 3: Практика (400 words)

**Practice Text 1:** Simple news (200 words)

- Article from Суспільне
- Strategy application tasks

**Practice Text 2:** Complex news (200 words)

- Article from BBC News Україна
- Independent strategy application

### Section 4: Продукція (200 words)

**Production Task:** "Write a headline and lead for this event..."

**Self-Assessment:** "Чи можу я розуміти українські новини?"

**B2 Preview:** "На B2 ви будете читати аналітичні статті та есеї..."

> 🎯 **Next Steps:** Read one Ukrainian news article daily

### Section 5: Підсумок (100 words)

"Ви навчилися читати українські новини: розуміти заголовки, знаходити головну думку, відрізняти факти від думок."

### Section 6: Вправи (12 activities)

1. quiz: Новини та заголовки (12 items)
2. true-false: Факти чи думки? (12 items)
3. match-up: Заголовки та статті (12 items)
4. fill-in: Заповніть ліди (12 items)
5. cloze: Новинна стаття (14 blanks)
6. group-sort: Факти, думки, джерела (18 items)
7. select: Головні думки (8 items)
8. unjumble: Новинні речення (8 items)
9. error-correction: Помилки в новинах (8 items)
10. mark-the-words: Ключові слова (10 words)
11. translate: Новинні фрази (8 items)

### Section 7: Словник (20 words)

заголовок, лід, підзаголовок, абзац, цитата, джерело, факт, думка, аналіз, коментар, редакція, колонка, репортаж, хроніка, зведення, огляд, дайджест, головна новина, термінове повідомлення, ексклюзив

### Section 8: External Resources

*Added to `docs/resources/external_resources.yaml` with `module_id: b1-81`:*

- Українська правда (website)
- BBC News Україна (website)
- Hromadske (website)
- Detector Media (website)

---

## Notes for AI Agents

**When creating integration modules:**

1. **Skills modules (M81-82):** Focus on HOW to read/listen, not WHAT to learn. Use authentic materials.

2. **Integration modules (M83-84):** Use TTT structure. Diagnostic → Review → Retest. Cover ALL B1 content.

3. **Capstone (M85):** 5 comprehensive tasks, not 25+ activities. Tasks ARE the assessment.

4. **All integration modules:** MANDATORY external resources in `docs/resources/external_resources.yaml`.

5. **All integration modules:** MANDATORY B2 preview section.

6. **No new content:** Integration modules review only. All teaching happens in M01-82.

**Activity creation for integration modules:**

- Skills modules: Prioritize comprehension and strategy application
- Integration modules: 25+ activities (like checkpoints)
- Capstone: 5-8 activities + 5 comprehensive tasks

**Common mistakes to avoid:**

- ❌ Teaching new grammar/vocabulary in integration modules (review only!)
- ❌ Using constructed texts instead of authentic materials
- ❌ Missing external resources (add to `docs/resources/external_resources.yaml`)
- ❌ No B2 preview
- ❌ Too many traditional activities in capstone (tasks are the assessment)
- ❌ Grammar-heavy skills modules (focus on strategies, not grammar)

---

## Clean MD Architecture Note

### Activities, Vocabulary, and External Resources

**CRITICAL:** Do NOT add `## Activities`, `## Vocabulary`, or `## External Resources` headers to the Markdown file. These sections are automatically injected by the build system from the corresponding YAML sidecars:

- `activities/{slug}.yaml` → `## Activities` section
- `vocabulary/{slug}.yaml` → `## Vocabulary` section
- `docs/resources/external_resources.yaml` (filtered by `module_id`) → `## External Resources` section

The module structure follows **Clean MD architecture**: Markdown contains narrative content only, YAML sidecars contain structured data.

---

**End of B1 Integration Module Template**

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
