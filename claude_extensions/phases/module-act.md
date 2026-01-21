# Phase 5: module-act

Generate activities YAML from locked meta.yaml and lesson content.

## Usage

```
/module-act {level} {module_num}
```

## Input

- `curriculum/l2-uk-en/{level}/meta/{slug}.yaml` (LOCKED from Phase 2)
- `curriculum/l2-uk-en/{level}/{slug}.md` (LOCKED from Phase 4)

## Output

- `curriculum/l2-uk-en/{level}/activities/{slug}.yaml`

## Critical Rules

> [!IMPORTANT]
> ### Activity-Only Scope
>
> Generate ONLY activities YAML. DO NOT:
> - ❌ Add vocabulary tables → Phase 7
> - ❌ Add reading passages → already in lesson .md
> - ❌ Add essays with model answers → use essay-response activity type
> - ✓ Create quiz, fill-in, match-up, true-false, etc.
> - ✓ Use ONLY vocabulary from lesson content
> - ✓ Test grammar points from meta.grammar
>
> ### YAML Root Structure
>
> **CRITICAL:** Activities file MUST be a bare list at root:
>
> ```yaml
> # ✅ CORRECT - bare list
> - type: quiz
>   title: Quiz title
>   items: [...]
>
> - type: match-up
>   title: Match title
>   pairs: [...]
> ```
>
> ```yaml
> # ❌ WRONG - dictionary wrapper
> activities:
>   - type: quiz
> ```
>
> **Why:** JSON schema validates against root array. Dictionary wrapper fails validation.
>
> ### Content-Based Activities
>
> All activities MUST test content from the lesson .md file:
> - Use examples, facts, and vocabulary from lesson
> - Test comprehension of main narrative
> - Reinforce grammar points demonstrated in lesson
> - DO NOT introduce new vocabulary or concepts

---

## Activity Generation Process

### Step 1: Load Inputs

1. Read meta.yaml:
   ```bash
   curriculum/l2-uk-en/{level}/meta/{slug}.yaml
   ```

2. Read lesson content:
   ```bash
   curriculum/l2-uk-en/{level}/{slug}.md
   ```

3. Read activity reference:
   ```bash
   docs/ACTIVITY-YAML-REFERENCE.md
   ```

4. Read richness guidelines (for activity counts):
   ```bash
   docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md
   ```

### Step 2: Extract Activity Requirements

From `meta.yaml`, read `activity_hints` array:

```yaml
activity_hints:
  - type: reading
    focus: "What to test"
    items: 2-3
  - type: quiz
    focus: "What to test"
    items: 12+
  - type: essay-response
    focus: "Essay topic"
    min_words: 200
```

Each hint specifies:
- `type`: Activity type (quiz, fill-in, etc.)
- `focus`: What to test (comprehension, vocabulary, grammar)
- `items`: Number of items or minimum word count
- Optional: `source`, `tasks`, other type-specific fields

### Step 3: Generate Activities by Type

For each `activity_hints` entry, generate corresponding YAML activity following schemas.

#### Activity Type Mapping

| meta.yaml type | YAML type | Schema fields |
|----------------|-----------|---------------|
| reading | reading | resource, tasks |
| quiz | quiz | items[].question, options, explanation |
| essay-response | essay-response | prompt, min_words, rubric, model_answer |
| critical-analysis | essay-response | (same, with analytical prompt) |
| fill-in | fill-in | items[].sentence, answer, options |
| match-up | match-up | pairs[].ukrainian, english |
| true-false | true-false | items[].statement, correct, explanation |
| vocabulary | fill-in or match-up | (test vocabulary from lesson) |
| timeline | select or quiz | (chronological events) |
| map-activity | select or quiz | (geographical locations) |
| image-analysis | essay-response | (describe/interpret images) |

#### Common Activity Types by Pedagogy

**Seminar (B2-HIST, C1-BIO, C1-HIST, LIT):**
- reading (2-3): External texts with linguistic analysis
- quiz (12+): Comprehension questions
- essay-response (1-2): 400+ word analytical essays
- fill-in (8-12): Vocabulary and collocations
- match-up (1-2): Historical terms and definitions
- true-false (8-10): Fact checking

**TTT (A2-B1 grammar):**
- diagnostic (1): Reveals learning gap
- quiz (10-15): Grammar knowledge
- fill-in (10-15): Grammar in context
- error-correction (5-8): Common mistakes
- unjumble (8-12): Sentence structure

**PPP (A1-A2 basic):**
- quiz (8-12): Vocabulary and basic grammar
- fill-in (8-12): Pattern practice
- match-up (2-3): Vocabulary pairs
- mark-the-words (3-5): Recognition

### Step 4: Content Extraction

For each activity, extract content from lesson .md:

**Quiz questions:**
- Use facts from main narrative sections
- Test key historical events, figures, concepts
- Include explanations referencing lesson text

Example:
```yaml
- question: Коли Вікентій Хвойка розпочав розкопки біля села Трипілля?
  options:
    - text: 1893 році
      correct: false
    - text: 1896 році
      correct: true
    - text: 1899 році
      correct: false
    - text: 1900 році
      correct: false
  explanation: «Найважливіше відкриття відбулося у 1896 році біля села Трипілля на Київщині».
```

**Fill-in sentences:**
- Use example sentences from lesson (marked with _Приклад:_)
- Test vocabulary from vocabulary_hints (required terms)
- Test collocations and grammar patterns

Example:
```yaml
- sentence: Трипільська культура існувала понад [___] років.
  answer: "2750"
  options:
    - "2750"
    - "1000"
    - "5000"
    - "500"
```

**Match-up pairs:**
- Use vocabulary definitions from lesson
- Match Ukrainian terms to explanations
- Historical figures to their roles

Example:
```yaml
pairs:
  - ukrainian: енеоліт
    english: період між кам'яним та бронзовим віками
  - ukrainian: протомісто
    english: велике поселення, що передувало справжнім містам
```

**True-false statements:**
- Use key facts from lesson
- Include common misconceptions
- Reference decolonization content

Example:
```yaml
- statement: Трипільські поселення були знищені ворожими нападами.
  correct: false
  explanation: «Більшість дослідників вважає, що спалення було ритуальним — частиною циклу "життя-смерть-відродження"».
```

### Step 5: Reading Activities (External Resources)

For `reading` type activities, follow this structure:

```yaml
- type: reading
  id: {level}-{module_num}-reading-01
  title: 'Аналіз первинного джерела'
  resource:
    type: primary_source|article|video
    url: 'https://...'
    title: 'Resource title'
  tasks:
    - 'Linguistic analysis task 1'
    - 'Linguistic analysis task 2'
    - 'Linguistic analysis task 3'
```

**CRITICAL for history modules:** Tasks must analyze LANGUAGE, not content interpretation:

✅ GOOD (Linguistic):
- Який регістр використовує автор? Наведіть приклади.
- Знайдіть три приклади пасивного стану.
- Порівняйте лексику цього тексту з лексикою модуля.

❌ BAD (Content interpretation):
- Що автор думає про подію? ← Tests interpretation
- Чому це сталося? ← Tests historical knowledge

### Step 6: Essay Activities

For `essay-response` or `critical-analysis` types:

```yaml
- type: essay-response
  id: {level}-{num}-essay-01
  title: 'Есе'
  prompt: 'Напишіть есе (400+ слів) на тему: [тема]'
  min_words: 400
  requirements:
    - Використайте лексику та граматику модуля
    - [Additional requirement 1]
    - [Additional requirement 2]
  structure:
    - step: Вступ (100 слів)
      description: тема та теза
    - step: Основна частина (200 слів)
      description: аргументи з первинних джерел
    - step: Висновок (100 слів)
      description: деколонізаційна перспектива
  rubric:
    - criterion: Мовна якість
      weight: 40%
      description: Граматична правильність, багатство лексики, складність речень (B2 рівень)
    - criterion: Використання матеріалу
      weight: 30%
      description: Цитування первинних джерел, використання лексики модуля
    - criterion: Структура та зв'язність
      weight: 20%
      description: Логічна організація, дискурсивні маркери
    - criterion: [Level-specific criterion]
      weight: 10%
      description: [Description]
  model_answer: |
    [400+ word model essay demonstrating:]
    - B2+ level grammar and syntax
    - Module vocabulary in context
    - Appropriate register
    - Clear structure with discourse markers
    - Citation of lesson content

    [Essay content here...]

    **Мовні особливості:**
    - [Grammar feature 1]
    - [Grammar feature 2]
    - [Vocabulary usage notes]
```

---

## Quality Standards

### Vocabulary

- **100% from lesson:** Every word in activities must appear in the lesson .md file
- **Required vocabulary:** Ensure all terms from vocabulary_hints.required are tested
- **No new vocabulary:** DO NOT introduce words not in the lesson

### Grammar

- **Test grammar points:** Create items that test grammar from meta.grammar
- **Natural examples:** Use real sentences from lesson, not artificial constructions
- **Explanations:** Reference lesson sections in explanations

### Ukrainian Language

- **No Surzhyk:** Zero tolerance
- **Use guillemets:** Use «» for quoted text, NOT ""
- **Natural language:** No robotic or template-like Ukrainian
- **Academic register:** Match lesson register (especially for B2-HIST)

### Activity Counts

Minimum activity counts by level (from MODULE-RICHNESS-GUIDELINES-v2.md):

| Level | Total Activities | Quiz Items | Fill-in Items | Other |
|-------|-----------------|------------|---------------|-------|
| A1 | 8-12 | 8+ quiz items | 8+ fill-in | 2-4 other |
| A2 | 10-15 | 12+ quiz items | 10+ fill-in | 3-5 other |
| B1 | 12-18 | 15+ quiz items | 12+ fill-in | 4-6 other |
| B2 | 12-20 | 15+ quiz items | 12+ fill-in | 5-8 other |
| C1 | 15-22 | 18+ quiz items | 15+ fill-in | 6-10 other |
| C2 | 15-25 | 20+ quiz items | 15+ fill-in | 6-12 other |

**For history/biography/literature tracks:** Focus on reading, essay-response, and comprehension over drills.

---

## Level-Specific Guidelines

### A1-A2 Modules

**Activity focus:**
- Vocabulary recognition and recall
- Basic grammar patterns
- Simple comprehension
- Match-up for vocabulary pairs
- Fill-in for sentence completion

**Immersion in activities:**
- A1: Instructions can be in English
- A2: Gradually shift to Ukrainian instructions

### B1+ Modules

**Activity focus:**
- Grammar in context
- Synonyms and nuances
- Complex sentence structures
- Extended reading comprehension
- Analytical writing

**Immersion:** 100% Ukrainian (all instructions, explanations)

### B2-HIST / C1-BIO / C1-HIST / LIT Tracks

**Activity focus:**
- Deep comprehension of historical/biographical narrative
- Linguistic analysis of primary sources
- Vocabulary in academic register
- Essay writing with decolonization perspective
- Less gamified drills, more seminar-style tasks

**Required:**
- 2-3 reading activities with linguistic analysis
- 1-2 essay-response activities (400+ words)
- Quiz focused on comprehension, not fact recall
- Fill-in for historical terminology and collocations

---

## Output Format

```yaml
# activities/{slug}.yaml

- type: quiz
  title: [Ukrainian title]
  instruction: [Ukrainian instruction]
  items:
    - question: [Ukrainian question]
      options:
        - text: [Option 1]
          correct: false
        - text: [Option 2]
          correct: true
      explanation: «[Explanation quoting lesson]».

- type: fill-in
  title: [Ukrainian title]
  instruction: [Ukrainian instruction]
  items:
    - sentence: [Sentence with [___] blank]
      answer: [Correct answer]
      options:
        - [Option 1]
        - [Option 2]
        - [Option 3]
        - [Option 4]

- type: match-up
  title: [Ukrainian title]
  instruction: [Ukrainian instruction]
  pairs:
    - ukrainian: [Term]
      english: [Definition or English translation]

- type: true-false
  title: [Ukrainian title]
  instruction: [Ukrainian instruction]
  items:
    - statement: [Ukrainian statement]
      correct: true|false
      explanation: [Ukrainian explanation]

- type: reading
  id: {level}-{num}-reading-01
  title: [Ukrainian title]
  resource:
    type: [primary_source|article|video]
    url: [Valid URL]
    title: [Resource title]
  tasks:
    - [Linguistic analysis task 1]
    - [Linguistic analysis task 2]

- type: essay-response
  id: {level}-{num}-essay-01
  title: 'Есе'
  prompt: [Essay prompt]
  min_words: [Number]
  requirements: [...]
  structure: [...]
  rubric: [...]
  model_answer: |
    [Model essay text]
```

---

## Validation Checklist

Before outputting, verify:

- [ ] Root structure is bare list (NOT wrapped in `activities:`)
- [ ] All activity types valid (from ACTIVITY-YAML-REFERENCE.md)
- [ ] Activity counts meet level minimums
- [ ] All vocabulary from lesson content only
- [ ] Required vocabulary from meta tested
- [ ] Grammar points from meta demonstrated
- [ ] Quiz items have explanations
- [ ] Fill-in items have 4 options
- [ ] Match-up pairs balanced (same count ukrainian/english)
- [ ] Essay activities have rubric and model answer
- [ ] Reading activities have linguistic (not content) tasks
- [ ] All text in Ukrainian (except URLs, IDs)
- [ ] No Surzhyk, clean Ukrainian
- [ ] Use «» not "" for quotes
- [ ] All activity_hints from meta covered

---

## Next Phase

On completion, output:

```
ACTIVITIES GENERATED: curriculum/l2-uk-en/{level}/activities/{slug}.yaml

Activity breakdown:
- quiz: {count} activities ({total} items)
- fill-in: {count} activities ({total} items)
- match-up: {count} activities ({total} pairs)
- true-false: {count} activities ({total} items)
- reading: {count} activities
- essay-response: {count} activities

✓ Total activities: {count} (min: {level_min})
✓ All vocabulary from lesson
✓ All required vocabulary tested
✓ Grammar points demonstrated
✓ Root structure: bare list

Next: Run /module-act-qa {level} {module_num}
```

---

**Phase output is UNLOCKED until Phase 6 QA passes.**
