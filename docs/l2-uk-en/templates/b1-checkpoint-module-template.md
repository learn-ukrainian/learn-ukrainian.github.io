# B1 Checkpoint Module Template

**Purpose:** Reference template for creating B1 checkpoint modules (M10, M20, M35, M45, M55, M65, M75, M80)

**Based on:** M05 (Ready for Immersion) which achieved ✅ 5.0/5 exemplary score

**Key Checkpoint Characteristics:**
- TTT pedagogy (Test-Teach-Test structure)
- Integration of all previous modules in the phase
- Self-assessment checklist for learner autonomy
- Emotional journey from uncertainty to confidence
- Authentic Ukrainian texts (grammar examples, dialogues)
- 1200+ words acceptable (lower than regular modules' 1500+)
- 25+ activities (comprehensive testing)

**Related Issue:** [#285](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/285)

---

## Quick Reference Checklist

Before submitting a B1 checkpoint module, verify:

- [ ] **Word count:** 1200+ words (content before activities section)
- [ ] **Vocabulary:** 40-50 items (review vocabulary from all modules in phase)
- [ ] **Activities:** 25+ comprehensive testing activities
- [ ] **TTT structure:** Діагностика → Аналіз → Поглиблення → Практика → Діалоги → Підсумок
- [ ] **Integration:** Complete review of ALL modules in the phase
- [ ] **Self-assessment:** "Чи можете ви..." checklist at end
- [ ] **Authentic texts:** 2-3 real Ukrainian grammar/dialogue texts
- [ ] **Emotional arc:** Uncertainty ("Чи готові ви?") → Confidence ("Ви готові!")
- [ ] **Immersion:** 80-85% Ukrainian (checkpoint can have more English scaffolding)
- [ ] **Pedagogy:** Comprehensive, not introducing new content

---

## Module Structure Template

### 1. Frontmatter (YAML)

```yaml
---
module: b1-XX
title: "Ukrainian Title"
subtitle: "English subtitle - [Phase Name] Checkpoint"
version: "1.0"
phase: "B1.X [Phase Name]"
pedagogy: "TTT"  # Always TTT for checkpoints
duration: 75  # minutes (checkpoints can be slightly shorter)
transliteration: none
tags:
  - checkpoint
  - integration
  - [phase-specific-tag]
grammar:
  - "Integration of M[start]-M[end]"
  - "Comprehensive review and testing"
objectives:
  - "Learner can demonstrate mastery of [phase topic]"
  - "Learner can integrate knowledge from M[start]-M[end]"
  - "Learner can self-assess readiness for next phase"
vocabulary_count: 44  # Higher than regular modules (review vocabulary)
---
```

**Why these fields:**
- `pedagogy`: Always "TTT" (Test-Teach-Test) for checkpoints
- `tags`: Must include "checkpoint" and "integration"
- `grammar`: Focus on INTEGRATION, not new content
- `objectives`: Focus on MASTERY and SELF-ASSESSMENT
- `vocabulary_count`: 40-50 (all review vocabulary from phase)
- `duration`: 75 minutes acceptable (vs 90 for regular modules)

---

### 2. Module Title and Motivation Box

```markdown
# Ukrainian Title

> 🎯 **Why This Module Matters**
>
> [Explain this is a checkpoint - no new content]
> [Describe what phase is being assessed]
> [Set expectation for comprehensive review]
> [Preview what comes after mastering this checkpoint]
```

**Example from M05 (Bridge Checkpoint):**
```markdown
# Готові до занурення

> 🎯 **Why This Module Matters**
>
> This is your final checkpoint before full immersion. After this module, all grammar explanations will be in Ukrainian. You've learned parts of speech, cases, aspect, tense, sentence structure, and grammar explanation patterns. Now it's time to prove you can understand Ukrainian grammar resources independently.
```

**Example for Aspect Checkpoint (M10):**
```markdown
# Контрольна точка: Вид дієслова

> 🎯 **Why This Module Matters**
>
> You've spent five modules learning the aspectual system — the most important grammatical category in Ukrainian. This checkpoint tests whether you can: (1) distinguish perfective from imperfective in any context, (2) choose the correct aspect for any situation, (3) understand aspect in past, present, and future. If you pass this checkpoint, you're ready for motion verbs!
```

**Why this works:**
- Sets clear expectations: this is ASSESSMENT, not new learning
- Summarizes what will be tested (all modules in phase)
- Creates emotional stakes: "prove you're ready"
- Previews next phase as motivation

---

### 3. TTT Content Structure (1200+ words total)

#### Section 1: Діагностика (Diagnostic Test Phase)
- Initial comprehension test without scaffolding
- Authentic Ukrainian text using all phase concepts
- Comprehension questions in both English and Ukrainian
- 200-300 words

```markdown
## Діагностика

### Тест: Чи готові ви?

Read this Ukrainian grammar text and answer the questions that follow:

> *[Authentic Ukrainian text using ALL concepts from the phase]*
> *[3-4 sentences minimum]*
> *[No translations or glosses]*

**Comprehension Check — Перевірка розуміння:**

1. [Question 1 testing concept from M[X]]?
   - Answer: [Answer]

2. [Question 2 testing concept from M[Y]]?
   - Answer: [Answer]

3. [Question 3 testing integration of concepts]?
   - Answer: [Answer]

4. [Question 4 testing application]?
   - Answer: [Answer]

If you answered all four questions correctly, you're ready for [next phase]!
```

**Example from M05:**
```markdown
### Тест: Чи готові ви?

Read this Ukrainian grammar text and answer the questions that follow:

> *Дієслово "читати" — недоконаного виду. Воно використовується, коли дія триває або повторюється. Доконана пара — "прочитати". Доконаний вид означає завершену дію з результатом.*

**Comprehension Check:**

1. Яким видом є дієслово "читати" в українській мові?
   - Answer: Недоконаного виду.

2. Що означає доконаний вид дієслова?
   - Answer: Завершену дію з результатом.
```

**Why this works:**
- Tests comprehension WITHOUT prior review
- Authentic text creates real-world simulation
- Immediate feedback shows readiness level
- Creates emotional hook: "Am I ready or not?"

#### Section 2: Аналіз (Review / Teach Phase)
- Complete review of what was learned in ALL modules
- Organized by module, not by concept
- Lists key terminology and patterns
- 300-400 words

```markdown
## Аналіз

### What You've Learned

In the [Phase Name] (M[start]-M[end]), you learned:

**Module [X]: [Title]**
- [Key concept 1]
- [Key concept 2]
- [Key terminology list]
- [Key patterns]

**Module [Y]: [Title]**
- [Key concept 1]
- [Key concept 2]
- [Key terminology list]
- [Key patterns]

[Continue for ALL modules in phase]

**Module [This Module]: Final Integration**
- Complete review of all concepts from M[start]-M[end]
- Comprehensive testing of mastery
- Self-assessment and readiness check
- Preparation for [Next Phase]

> 💡 **Did You Know?**
>
> [Interesting fact about the phase content]
> [Connection to real-world usage]
> [Motivation for next phase]
```

**Example from M05:**
```markdown
**Module 02: Verb Terminology**
- Вид: доконаний, недоконаний
- Час: теперішній, минулий, майбутній
- Дія, процес, результат, тривалість, повторення
- Спосіб: наказовий, умовний
- Negation: заперечення, загальне заперечення, очікувана дія, попередження, заборона
- Verb forms: складна форма, синтетична форма, наказова форма, парадигма
```

**Why this works:**
- COMPLETE review before testing
- Organized by MODULE for easy reference
- Shows SCOPE of what's being tested
- Engagement box adds value and motivation

#### Section 3: Поглиблення (Deeper Testing Phase)
- Extended authentic text (longer than Діагностика)
- Tests ability to apply concepts in complex context
- Comprehension verification questions
- 200-300 words

```markdown
## Поглиблення

### Reading a Real [Topic] Text

Here's an excerpt adapted from a Ukrainian [grammar textbook / article / conversation]. Read it and test your comprehension:

> *[Extended authentic Ukrainian text]*
> *[6-8 sentences minimum]*
> *[Uses ALL phase concepts in integrated way]*
> *[No translations or glosses]*

**Test Your Understanding:**

Can you identify:
- [Question 1]: (Answer reference)
- [Question 2]: (Answer reference)
- [Question 3]: (Answer reference)
- [Question 4 - integration]: (Answer reference)
```

**Example from M05:**
```markdown
### Reading a Real Grammar Explanation

> *Дієслова в українській мові мають дві граматичні категорії: вид і час. Категорія виду поділяє дієслова на дві групи: дієслова недоконаного виду (НДВ) і дієслова доконаного виду (ДВ).*
>
> *Недоконаний вид виражає процес дії, її тривалість або повторення...*

**Test Your Understanding:**

Can you identify:
- Which terms are used for aspect? (вид, доконаний, недоконаний)
- What explanation pattern is used? (виражає, означає)
```

**Why this works:**
- AUTHENTIC text (not constructed for pedagogy)
- LONGER passage tests sustained comprehension
- Questions verify UNDERSTANDING, not just recognition
- No scaffolding tests true mastery

#### Section 4: Практика (Application Phase)
- Real-world simulation: "From this point forward..."
- Preview of next phase material
- Application of phase concepts to new context
- 200-300 words

```markdown
## Практика

### The Real Test: Can You Learn From This?

From this point forward, [description of how next phase will work]:

> *[Preview text from next phase]*
> *[Uses all current phase concepts as foundation]*
> *[Shows what's coming next]*

**Can you:**
- [Application task 1]
- [Application task 2]
- [Application task 3]
- [Application task 4]

> 🌍 **У реальному житті**
>
> [Show where learners will encounter this]
> [Connect to authentic Ukrainian resources]
> [Preview next phase challenges]
```

**Example from M05:**
```markdown
### The Real Test: Can You Learn From This?

From this point forward, grammar explanations will look like this:

> *Відмінювання іменників жіночого роду*
> *Іменники жіночого роду на -а/-я відмінюються за першою відміною...*

If you can understand this text using only your M01-05 metalanguage, you're ready for full immersion!
```

**Why this works:**
- SIMULATION of next phase
- Tests TRANSFER of knowledge to new context
- Creates CONFIDENCE for next phase
- Engagement box shows REAL-WORLD relevance

---

### 5. Діалоги (Production Phase)

5-6 dialogues showing integrated use of phase content:

```markdown
## Діалоги

### Діалог 1: [Context 1]

**[Speaker 1]:** [Line using concept from M[X]]

**[Speaker 2]:** [Line using concept from M[Y]]

**[Speaker 1]:** [Line integrating both concepts]

**[Speaker 2]:** [Line showing application]

---

### Діалог 2: [Context 2]

[Continue with 4-5 more dialogues]

> 💡 **Patterns to Notice**
>
> [Point out integration patterns in dialogues]
> [Show how concepts work together]
```

**Why this works:**
- Shows INTEGRATION in conversation
- Different contexts = different applications
- 5-6 dialogues ensure comprehensive coverage
- Callout highlights patterns to notice

---

### 6. Підсумок (Summary with Self-Assessment)

```markdown
# Підсумок

**Що ви навчилися:**

1. [Comprehensive summary point 1 - covers M[X]-M[Y]]
2. [Comprehensive summary point 2 - integration]
3. [Comprehensive summary point 3 - application]
4. [Comprehensive summary point 4 - readiness for next phase]

**Основне правило:**

> [Quotable summary in Ukrainian or bilingual]
> [Captures essence of the entire phase]

**Далі:**

[Preview of next phase with specific modules]

> ✅ **Самоперевірка**
>
> Чи можете ви:
> - [ ] [Self-assessment criterion 1 - concept from M[X]]?
> - [ ] [Self-assessment criterion 2 - concept from M[Y]]?
> - [ ] [Self-assessment criterion 3 - integration]?
> - [ ] [Self-assessment criterion 4 - application]?
> - [ ] [Self-assessment criterion 5 - readiness]?
>
> Якщо ви відповіли "так" на всі питання — ви готові до [Next Phase]!
```

**Example from M05:**
```markdown
> ✅ **Самоперевірка**
>
> Чи можете ви:
> - [ ] Розуміти українські граматичні пояснення без перекладу?
> - [ ] Визначити частини мови та відмінки в реченні?
> - [ ] Відрізнити доконаний вид від недоконаного?
> - [ ] Читати складносурядні та складнопідрядні речення?
>
> Якщо так — ви готові до повного занурення!
```

**Why this works:**
- CONSOLIDATES all phase learning
- EMPOWERS learner with self-assessment
- Creates EMOTIONAL payoff: "Ви готові!"
- Specific criteria from EACH module in phase

---

## Activity Section Template

### Activity Requirements for Checkpoints

**Comprehensive Testing (25+ activities required):**

Checkpoints must test ALL content from the phase comprehensively. Activity mix should include:

**Core Testing Activities:**
1. **quiz** (3-4 activities, 8-14 items each) - One quiz per major concept
2. **match-up** (2-3 activities, 12+ items) - Term-definition, concept-example
3. **fill-in** (2-3 activities, 12-14 items) - Contextual application
4. **true-false** (1-2 activities, 14 items) - Validation of understanding
5. **group-sort** (2 activities, 14-18 items) - Categorization by module/concept
6. **unjumble** (2 activities, 6-14 items) - Sentence construction

**Integration Activities:**
7. **error-correction** (2 activities, 8-14 items) - Common mistakes across phase
8. **cloze** (1 activity, 14+ blanks) - Extended passage integrating all concepts
9. **mark-the-words** (1 activity, 11-13 markable words) - Identification across text
10. **dialogue-reorder** (1 activity, 8 lines) - Conversation flow
11. **select** (1 activity, 14 items) - Multi-answer questions
12. **translate** (1 activity, 14 items) - Translation practice

**Total: 25+ activities ensuring comprehensive coverage**

---

### Quiz Activities: One Per Module/Concept

**✅ CHECKPOINT PATTERN - Multiple Quizzes:**

```markdown
## quiz: Комплексний тест — [Module X Topic]

[8-14 questions testing ONLY Module X concepts]

---

## quiz: Комплексний тест — [Module Y Topic]

[8-14 questions testing ONLY Module Y concepts]

---

## quiz: Комплексний тест — [Module Z Topic]

[8-14 questions testing ONLY Module Z concepts]

---

## quiz: Інтеграція всіх модулів

[14 questions testing INTEGRATION across all modules]
```

**Why multiple quizzes:**
- Each quiz focuses on ONE module's content
- Final quiz tests INTEGRATION
- Learners can identify which module needs review
- Comprehensive coverage guaranteed

---

### Fill-in: Contextual Application

**Example for Aspect Checkpoint:**

```markdown
## fill-in: Вибір виду в контексті

1. Вчора я [___] книгу дві години.
   - [ ] прочитав (ДВ - wrong, shows duration)
   - [x] читав (НДВ - correct, process)
   - [ ] читаю (present tense - wrong)

2. Нарешті я [___] всю книгу!
   - [x] прочитав (ДВ - correct, result)
   - [ ] читав (НДВ - wrong, "нарешті" signals completion)
   - [ ] буду читати (future - wrong)

[10-12 more items testing different aspect contexts]
```

---

### Error-Correction: Common Mistakes from Phase

**Example:**

```markdown
## error-correction: Типові помилки — Вид дієслова

1. Я прочитав книгу дві години.
   > [!error] прочитав
   > [!answer] читав
   > [!options] прочитав | читав | читаю | буду читати
   > [!explanation] Тривалість (дві години) вимагає НДВ, а не ДВ.

2. Я завжди читаю цю книгу перед сном.
   > [!error] читаю
   > [!answer] читав
   > [!options] читаю | читав | прочитав | прочитаю
   > [!explanation] Звичка в минулому вимагає НДВ у минулому часі: читав.

[6-12 more common mistakes from across the phase]
```

**Why this is critical:**
- Tests CORRECTION ability
- Focuses on COMMON errors from phase
- Explanation helps understanding

---

### Cloze: Extended Integration Passage

**Checkpoint cloze should:**
- Use 14+ blanks (high density)
- Test concepts from ALL modules in phase
- Use authentic-style text (not constructed pedagogy)

```markdown
## cloze: Інтеграційний текст

[Extended passage with 14+ blanks testing concepts from M[X], M[Y], M[Z], etc.]

**Correct answers reference:**
- Blank 1: [concept from M[X]]
- Blank 2: [concept from M[Y]]
- Blank 3: [integration of M[X] and M[Y]]
- [etc.]
```

---

## Vocabulary Section Template (40-50 items)

**Checkpoint vocabulary = REVIEW vocabulary from ALL modules in phase**

**✅ CORRECT FORMAT (5 columns, organized by module):**

```markdown
# Словник

## Module [X]: [Title]

| Слово | Вимова | Переклад | ЧМ | Примітка |
|-------|--------|----------|-----|----------|
| **[term1]** | /.../ | ... | ... | from M[X] |
| **[term2]** | /.../ | ... | ... | from M[X] |
[... all vocabulary from M[X]]

## Module [Y]: [Title]

| Слово | Вимова | Переклад | ЧМ | Примітка |
|-------|--------|----------|-----|----------|
| **[term1]** | /.../ | ... | ... | from M[Y] |
[... all vocabulary from M[Y]]

[Continue for ALL modules in phase]
```

**Why organize by module:**
- Easy reference when reviewing specific module
- Shows comprehensive coverage
- Helps learners identify which module needs work
- 40-50 items total across all phase modules

---

## Common Pitfalls to Avoid

### 1. **Introducing New Content**
- ❌ Problem: Teaching new grammar or vocabulary in checkpoint
- ✅ Solution: Checkpoints ONLY review and test. All content must come from prior modules.

### 2. **Insufficient Module Coverage**
- ❌ Problem: Testing only 2-3 modules out of 5-module phase
- ✅ Solution: Create dedicated quiz for EACH module + integration quiz

### 3. **No Self-Assessment Checklist**
- ❌ Problem: Learners don't know if they're ready for next phase
- ✅ Solution: Include "Чи можете ви..." checklist with criteria from EACH module

### 4. **Missing Emotional Arc**
- ❌ Problem: Flat, clinical testing without motivation
- ✅ Solution: Create journey from "Чи готові ви?" (uncertain) → "Ви готові!" (confident)

### 5. **Constructed vs Authentic Texts**
- ❌ Problem: Using simplified pedagogical texts for testing
- ✅ Solution: Use AUTHENTIC Ukrainian grammar texts, news, dialogues

### 6. **No Integration Testing**
- ❌ Problem: Testing modules in isolation, not together
- ✅ Solution: Include integration activities (cloze, final quiz, dialogues) showing how concepts work together

### 7. **Too Few Activities**
- ❌ Problem: 12-15 activities (same as regular modules)
- ✅ Solution: 25+ activities for comprehensive testing (one quiz per module + integration)

### 8. **Missing Preview of Next Phase**
- ❌ Problem: Checkpoint ends abruptly without showing what's next
- ✅ Solution: Include "Далі" section showing specific upcoming modules and topics

---

## Audit Validation

Before submitting, run:
```bash
python3 scripts/audit_module.py curriculum/l2-uk-en/b1/XX-checkpoint.md
```

**Target output:**
```
✅ Words: 1200+/1200 (lower threshold for checkpoints)
✅ Activities: 25+/12 (higher requirement for comprehensive testing)
✅ Density: All > minimums
✅ Vocab: 40-50/20 (review vocabulary from entire phase)
✅ Pedagogy: TTT structure, no new content
✅ Immersion: 80-85% (checkpoints can have more English scaffolding)
✅ AUDIT PASSED.
```

---

## Example: M05 as Reference Implementation

See `curriculum/l2-uk-en/b1/05-ready-for-immersion.md` for a complete checkpoint example.

**M05 Audit Results:**
- ✅ Words: 1255/1200
- ✅ Activities: 25/12
- ✅ Vocab: 48/20 (review vocab from M01-04 + gap analysis additions)
- ✅ TTT structure: Діагностика → Аналіз → Поглиблення → Практика → Діалоги → Підсумок
- ✅ Integration: Complete review of M01-05
- ✅ Self-assessment: "Чи можете ви..." checklist with 4 criteria
- ✅ Immersion: 82.4%
- ✅ Content Quality: 5.0/5 ⭐⭐⭐⭐⭐

**M05 Success Patterns:**
- 25 activities total: 9 quizzes (one per concept category), 16 other types
- Authentic Ukrainian grammar texts in Діагностика and Поглиблення
- Emotional arc: "Чи готові ви?" → "Ви готові до повного занурення!"
- Complete review organized by module in Аналіз section
- Self-assessment checklist with specific criteria from each module

---

## Related Documents

- [B1 Curriculum Plan](../B1-CURRICULUM-PLAN.md) - Checkpoint module specifications
- [Module Richness Guidelines](../MODULE-RICHNESS-GUIDELINES-v2.md) - Quality standards
- [B1 Grammar Module Template](./b1-grammar-module-template.md) - Regular module comparison
- [Activity Markdown Reference](../ACTIVITY-MARKDOWN-REFERENCE.md) - Activity syntax

---

**Last Updated:** 2025-12-23
**Based on:** M05 (Ready for Immersion) - 5.0/5 exemplary score
**Status:** ✅ Production Ready
