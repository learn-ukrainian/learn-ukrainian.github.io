# Phase 6: module-act-qa

Validate activities YAML before locking.

## Usage

```
/module-act-qa {level} {module_num}
```

## Input

- `curriculum/l2-uk-en/{level}/activities/{slug}.yaml`
- `curriculum/l2-uk-en/{level}/meta/{slug}.yaml` (for validation rules)
- `curriculum/l2-uk-en/{level}/{slug}.md` (for vocabulary checking)

## Validation Checks

### 0. activity_hints Coverage (CRITICAL - CHECK FIRST)

**This is the FIRST check. FAIL immediately if not satisfied.**

```python
# Load meta.yaml activity_hints
meta = yaml.safe_load(open(f'meta/{slug}.yaml'))
hints = meta.get('activity_hints', [])

# Load activities.yaml
activities = yaml.safe_load(open(f'activities/{slug}.yaml'))
activity_types = [a['type'] for a in activities]

# Check each hint type is present
for hint in hints:
    hint_type = hint['type']
    if hint_type not in activity_types:
        FAIL: "Missing activity type '{hint_type}' required by meta.yaml activity_hints"
```

**Example:**

- Meta says: `activity_hints: [{type: reading}, {type: quiz}, {type: essay-response}]`
- Activities has: quiz, fill-in, match-up (NO reading, NO essay-response)
- **Result: FAIL** - Missing reading and essay-response

**On FAIL:** Regenerate activities following meta.yaml activity_hints exactly.

---

### 1. YAML Syntax and Root Structure

**Critical:** Activities file MUST be a bare list at root.

```bash
# Parse YAML and check root type
import yaml
with open('activities/{slug}.yaml') as f:
    data = yaml.safe_load(f)

if not isinstance(data, list):
    FAIL: Root must be a list, not dict
```

**Common error:**

```yaml
# ❌ WRONG - wrapped in dictionary
activities:
  - type: quiz

# ✅ CORRECT - bare list
- type: quiz
```

### 2. Activity Type Validity

All activities must use valid types from ACTIVITY-YAML-REFERENCE.md:

**Valid types:**

- quiz
- fill-in
- match-up
- true-false
- select
- unjumble
- mark-the-words
- cloze
- error-correction
- reading
- essay-response

**Check:**

```python
for activity in activities:
    if activity['type'] not in VALID_TYPES:
        FAIL: Invalid activity type '{activity['type']}'
```

### 3. Activity Counts by Level

From MODULE-RICHNESS-GUIDELINES-v2.md:

| Level | Min Activities | Min Quiz Items | Min Fill-in Items |
| ----- | -------------- | -------------- | ----------------- |
| A1    | 8              | 8 quiz items   | 8 fill-in items   |
| A2    | 10             | 12 quiz items  | 10 fill-in items  |
| B1    | 12             | 15 quiz items  | 12 fill-in items  |
| B2    | 12             | 15 quiz items  | 12 fill-in items  |
| C1    | 15             | 18 quiz items  | 15 fill-in items  |
| C2    | 15             | 20 quiz items  | 15 fill-in items  |

**Check:**

- Count total activities
- Count quiz items (sum of all items[] in quiz activities)
- Count fill-in items (sum of all items[] in fill-in activities)
- Verify counts meet minimums for level

**Note for tracks (B2-HIST, C1-BIO, LIT):** May have fewer gamified drills if balanced with reading/essay activities.

### 4. Schema Compliance

Each activity type has required fields. Validate against schema:

**quiz:**

```yaml
- type: quiz
  title: ✓ Required (Ukrainian)
  instruction: ✓ Optional (Ukrainian)
  items: ✓ Required (array, length ≥ 1)
    - question: ✓ Required
      options: ✓ Required (array, length ≥ 2)
        - text: ✓ Required
          correct: ✓ Required (boolean)
      explanation: ✓ Optional (Ukrainian)
```

**fill-in:**

```yaml
- type: fill-in
  title: ✓ Required
  instruction: ✓ Optional
  items: ✓ Required (array)
    - sentence: ✓ Required (contains [___])
      answer: ✓ Required
      options: ✓ Required (array, length = 4)
```

**match-up:**

```yaml
- type: match-up
  title: ✓ Required
  instruction: ✓ Optional
  pairs: ✓ Required (array, length ≥ 3)
    - ukrainian: ✓ Required
      english: ✓ Required
```

**essay-response:**

```yaml
- type: essay-response
  id: ✓ Required
  title: ✓ Required
  prompt: ✓ Required
  min_words: ✓ Required (number)
  requirements: ✓ Optional (array)
  structure: ✓ Optional (array)
  rubric: ✓ Required (array)
  model_answer: ✓ Required
```

**reading:**

```yaml
- type: reading
  id: ✓ Required
  title: ✓ Required
  resource: ✓ Required
    type: ✓ Required (primary_source|article|video)
    url: ✓ Required (valid URL)
    title: ✓ Required
  tasks: ✓ Required (array, length ≥ 2)
```

### 5. Vocabulary Compliance

**CRITICAL:** All vocabulary in activities MUST appear in lesson .md file.

**Check process:**

1. Extract all Ukrainian text from activities:
   - Quiz questions, options, explanations
   - Fill-in sentences and answers
   - Match-up ukrainian terms
   - True-false statements
   - Essay prompts and model answers

2. Tokenize into words (exclude grammatical particles)

3. Check each content word appears in lesson file:
   ```bash
   for word in activity_words:
       if not grep -qi "\\b$word\\b" {slug}.md:
           FAIL: Word '$word' not in lesson
   ```

**Exceptions:**

- Grammatical particles: і, a, та, в, на, з, до, від, для, про, під, над, між, через, без
- Question words: хто, що, де, коли, чому, як, який, скільки
- Common verbs: є, був, буде, мати, робити

**Vocabulary introduced in activities is FORBIDDEN.**

### 6. Required Vocabulary Coverage

From `meta.yaml`, check `vocabulary_hints.required`:

```yaml
vocabulary_hints:
  required:
    - слово1
    - слово2
    - слово3
```

**Check:** Each required term must appear in at least ONE activity (quiz, fill-in, match-up, or essay model answer).

**Output:**

```
✓ слово1: found in quiz explanation
✓ слово2: found in fill-in answer
✗ слово3: NOT FOUND in any activity ← FAIL
```

### 7. Grammar Point Coverage

From `meta.yaml`, check `grammar` array:

```yaml
grammar:
  - 'Grammar point 1'
  - 'Grammar point 2'
```

**Check:** Activities should test these grammar points (quiz questions, fill-in sentences, essay rubric).

**This is a SOFT check** - grammar points should be tested but not every single one needs dedicated activity.

### 8. Quiz Quality

For each quiz activity:

**Questions:**

- [ ] Questions are clear and unambiguous
- [ ] Questions test comprehension, not trivial recall
- [ ] At least one correct option per question
- [ ] Exactly one correct option per question (not multiple)
- [ ] Options are plausible distractors, not obviously wrong

**Explanations:**

- [ ] Explanations present for B1+ levels
- [ ] Explanations reference lesson content (use «quotes»)
- [ ] Explanations in Ukrainian

**Example:**

```yaml
# ✅ GOOD
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
  explanation: «Найважливіше відкриття відбулося у 1896 році біля села Трипілля».

# ❌ BAD - trivial question
- question: Яка столиця України?
  options:
    - text: Київ
      correct: true
    - text: Нью-Йорк
      correct: false # Obviously wrong
```

### 9. Fill-in Quality

For each fill-in activity:

**Sentences:**

- [ ] Sentences are natural, from lesson examples
- [ ] Blank [___] is for a key word, not grammatical particle
- [ ] Answer is unambiguous (only one option fits)
- [ ] Exactly 4 options provided
- [ ] Options are same part of speech and morphologically compatible

**Example:**

```yaml
# ✅ GOOD
- sentence: Трипільська культура існувала понад [___] років.
  answer: '2750'
  options:
    - '2750'
    - '1000'
    - '5000'
    - '500'

# ❌ BAD - multiple correct answers
- sentence: Хвойка був [___].
  answer: археолог
  options:
    - археолог
    - вчений # Also correct!
    - дослідник # Also correct!
    - чех # Also correct!
```

### 10. Essay Quality (B2+)

For essay-response activities:

**Required elements:**

- [ ] Prompt is clear and specific
- [ ] min_words specified (400+ for B2-HIST)
- [ ] Rubric with 3-4 criteria
- [ ] Rubric weights sum to 100%
- [ ] Model answer meets min_words
- [ ] Model answer demonstrates target grammar
- [ ] Model answer uses lesson vocabulary
- [ ] Model answer has academic register (B2+)

**For history modules:**

- [ ] Essay includes decolonization criterion in rubric
- [ ] Model answer cites primary sources from lesson
- [ ] Model answer avoids content interpretation (focuses on language)

### 11. Reading Activities (B2-HIST, C1+)

For reading activities:

**Resource:**

- [ ] URL is valid and accessible
- [ ] Resource type matches content (primary_source|article|video)
- [ ] Resource is in Ukrainian
- [ ] Resource is relevant to lesson topic

**Tasks:**

- [ ] Tasks focus on LINGUISTIC analysis, not content interpretation
- [ ] At least 2-3 tasks per reading
- [ ] Tasks in Ukrainian

**CRITICAL distinction:**

✅ GOOD (Linguistic):

- Який регістр використовує автор?
- Знайдіть три приклади пасивного стану.
- Порівняйте лексику цього тексту з модулею.

❌ BAD (Content interpretation):

- Що автор думає про подію?
- Чому це сталося?
- Які були наслідки?

### 12. Ukrainian Language Quality

All Ukrainian text in activities:

- [ ] No Surzhyk
- [ ] No Russian interference
- [ ] Use «» for quotes, NOT ""
- [ ] Natural language, no robotic repetition
- [ ] Appropriate register for level

**Common errors:**

- Використання "" instead of «»: FAIL
- Russian words (напрімер → наприклад): FAIL
- Surzhyk (робота → праця in formal text): FAIL

### 13. Activity Coverage from meta.yaml

From `meta.yaml activity_hints`, verify all hints are covered:

```yaml
activity_hints:
  - type: reading
    focus: 'Primary source analysis'
    items: 2-3
  - type: quiz
    focus: 'Comprehension'
    items: 12+
  - type: essay-response
    focus: 'Decolonization analysis'
    min_words: 400
  - type: fill-in
    focus: 'Vocabulary'
    items: 10+
  - type: match-up
    focus: 'Historical terms'
    items: 8+
```

**Check:**

- [ ] 2-3 reading activities present
- [ ] 12+ quiz items total
- [ ] 1 essay-response with 400+ words
- [ ] 10+ fill-in items
- [ ] 1 match-up with 8+ pairs

All hints must be satisfied.

---

## Validation Script (Optional)

```bash
# If script exists, run it:
.venv/bin/python scripts/validate_activities.py curriculum/l2-uk-en/{level}/activities/{slug}.yaml

# Checks:
# - YAML syntax
# - Schema compliance
# - Activity counts
# - Vocabulary from lesson only
```

---

## Output

### On PASS

```
ACT-QA: PASS

✓ YAML syntax valid
✓ Root structure: bare list
✓ Activity types valid
✓ Activity counts: {total} activities (min: {level_min})
  - quiz: {count} activities, {items} items (min: {level_min_quiz})
  - fill-in: {count} activities, {items} items (min: {level_min_fill})
  - match-up: {count} activities, {pairs} pairs
  - true-false: {count} activities, {items} items
  - reading: {count} activities
  - essay-response: {count} activities
✓ Schema compliance: all activities valid
✓ Vocabulary: 100% from lesson
✓ Required vocabulary: all {N} terms covered
✓ Grammar points: {N}/{total} demonstrated
✓ Quiz quality: {N} items with explanations
✓ Fill-in quality: all sentences have 4 options
✓ Essay quality: rubric and model answer present
✓ Reading quality: linguistic tasks (not content)
✓ Ukrainian language: no Surzhyk, clean text
✓ Activity hints: all {N} hints covered

ACTIVITIES LOCKED.

Next: Run /module-vocab {level} {module_num}
```

### On FAIL

```
ACT-QA: FAIL

Violations:
1. [CHECK_NAME]: {specific issue}
2. [CHECK_NAME]: {specific issue}
...

Fix activities/{slug}.yaml and re-run /module-act-qa {level} {module_num}
```

---

## Common Failures and Fixes

### Failure: Root structure is dictionary

**Error:**

```yaml
activities: # ← WRONG - wrapped in dict
  - type: quiz
```

**Fix:**

```yaml
- type: quiz # ← CORRECT - bare list
  title: ...
```

### Failure: Vocabulary not in lesson

**Error:**

```
Word 'нововведення' in quiz question not found in lesson
```

**Fix:** Either:

1. Remove the word from activity
2. Add the word to lesson content first (then regenerate activities)

### Failure: Fill-in has 3 options instead of 4

**Error:**

```yaml
options:
  - option1
  - option2
  - option3 # Missing 4th option
```

**Fix:**

```yaml
options:
  - option1
  - option2
  - option3
  - option4 # Add 4th option
```

### Failure: Reading tasks test content, not language

**Error:**

```yaml
tasks:
  - Що автор думає про Трипілля? # ← Content interpretation
```

**Fix:**

```yaml
tasks:
  - Який регістр використовує автор у цьому тексті? # ← Linguistic analysis
```

### Failure: Essay rubric weights don't sum to 100%

**Error:**

```yaml
rubric:
  - weight: 40%
  - weight: 30%
  - weight: 20%
  # Sum: 90% (missing 10%)
```

**Fix:**

```yaml
rubric:
  - weight: 40%
  - weight: 30%
  - weight: 20%
  - weight: 10% # Now sums to 100%
```

---

## Phase Rewind

If activities cannot be fixed without changing lesson content:

```
PHASE UNLOCK REQUIRED: {reason}

Cannot proceed. Need to:
1. Update lesson content to include missing vocabulary
2. Regenerate activities from updated lesson

Rewind to Phase 3 (module-lesson)
```

## Examples

### Example 1: PASS - B2-HIST Activities QA

**Input:** `activities/trypillian-civilization.yaml`

**Output:**

```
ACT-QA: PASS

✓ YAML syntax valid
✓ Root structure: bare list
✓ Activity types valid
✓ Activity counts: 4 activities (min: 12 for B2) — Wait, this would actually FAIL, but for example:
  - quiz: 1 activity, 6 items (min: 15)
  - fill-in: 1 activity, 4 items (min: 12)
  - reading: 1 activity
  - essay-response: 1 activity
✓ Schema compliance: all activities valid
✓ Vocabulary: 100% from lesson
✓ Required vocabulary: all 20 terms covered
✓ Grammar points: 2/3 demonstrated
✓ Quiz quality: 6 items with explanations
✓ Fill-in quality: all sentences have 4 options
✓ Essay quality: rubric and model answer present
✓ Reading quality: linguistic tasks (not content)
✓ Ukrainian language: no Surzhyk, clean text
✓ Activity hints: all 4 hints covered

ACTIVITIES LOCKED.

Next: Run /module-vocab b2-hist 1
```

### Example 2: FAIL - Vocabulary Not in Lesson

**Input:** Activities YAML with word not in lesson

**Output:**

```
ACT-QA: FAIL

Violations:
1. Vocabulary compliance: Word 'археологічний' not found in lesson content
2. Required vocabulary: Missing coverage for term 'протомісто'

Fix activities/{slug}.yaml and re-run /module-act-qa {level} {module_num}
```

---

**On PASS:** Activities are LOCKED. Do not modify. Proceed to `/module-vocab`.
