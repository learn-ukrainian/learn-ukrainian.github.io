# Stage 3: Activities (YAML-First)

> **⚠️ READ FIRST: `claude_extensions/NON-NEGOTIABLE-RULES.md`**

Generate activities in YAML format, separate from prose.

> **CRITICAL:** See `docs/ACTIVITY-YAML-REFERENCE.md` for authoritative format reference.

## YAML Structure Rules

### 1. Root MUST Be Bare List
```yaml
# ✅ CORRECT
- type: quiz
  title: Quiz title

# ❌ WRONG - dictionary wrapper
activities:
  - type: quiz
```

### 2. Schema Property Names
| Activity | Correct | Wrong |
|----------|---------|-------|
| unjumble | `jumbled` | `scrambled`, `words` |
| mark-the-words | `text` + `answers` | `passage`, asterisks |
| true-false | `statement` | `sentence` |

### 3. Mark-the-Words Format
```yaml
# ✅ CORRECT
- type: mark-the-words
  text: Гарний день приніс радість.
  answers: [день, радість]

# ❌ WRONG - asterisks
text: Гарний *день*.
```

## Common Schema Errors

**CRITICAL: Check `quick-ref/{level}.md` for minimum item counts!**

### Universal Field Names
- ✅ `instruction` (singular) - REQUIRED
- ❌ `instructions` (plural) - Schema violation
- ❌ `id` - NOT allowed (except LIT)

### Fill-in Requirements
```yaml
# REQUIRED: options array with exactly 4 items
- sentence: "Text [___] here"
  answer: correct
  options: [correct, wrong1, wrong2, wrong3]
```

### Cloze Format
```yaml
# ✅ Inline format (no blanks array)
passage: "Text {correct|wrong1|wrong2|wrong3}"

# ✅ Numbered format (with blanks array)
passage: "Text {1} and {2}"
blanks:
  - id: 1
    answer: correct
    options: [correct, wrong1, wrong2, wrong3]
```

### Ukrainian Text
```yaml
# ❌ WRONG
answer: 'інтерв'ю'

# ✅ CORRECT
answer: "інтерв'ю"
```

## Direct YAML Creation (Recommended)

1. Read module content
2. Study 1-2 similar modules for patterns
3. Create `activities/{slug}.yaml`
4. Use YAML Format Reference
5. Run audit

**Why?** Faster, fewer errors, better quality than md_to_yaml.py.

## Reference Existing Modules

| Level | Module Type | Examples | Look For |
|-------|-------------|----------|----------|
| B1 | Grammar | M06-10 | Variety, sequencing |
| B1 | Vocabulary | M52-53 | Cloze structure |
| A2 | All | M01-10 | Patterns |

## Output Files

```
curriculum/l2-uk-en/{level}/
├── {slug}.md                    # Prose only
└── activities/{slug}.yaml       # All activities
```

**CRITICAL:** Activity files MUST include module number prefix for core levels (e.g., `35-at-the-cafe.yaml`).

## Activity Count Requirements

| Level | Target | WARN | FAIL | Items/Activity | Types |
|-------|--------|------|------|----------------|-------|
| A1 | 8+ | <8 | <6 | 12+ | 4+ |
| A2 | 10+ | <10 | <8 | 12+ | 5+ |
| B1 | 12+ | <12 | <8 | 14+ | 5+ |
| B2 | 14+ | <14 | <10 | 16+ | 5+ |
| C1 | 16+ | <16 | <12 | 18+ | 5+ |
| C2 | 16+ | <16 | <12 | 18+ | 5+ |

**Content-heavy** (B2-HIST, C1-BIO): 10-12 activities (comprehension-focused).

## Naturalness Requirements

**All prose activities (cloze, fill-in, unjumble) MUST score >= 8/10.**

**Common failures (< 8):**
1. **Random subject shifts:**
   ```yaml
   # ❌ BAD
   - sentence: Я читаю книгу.
   - sentence: Вона пише листа.
   - sentence: Він малює.

   # ✅ GOOD - unified context
   - sentence: Я читаю книгу.
   - sentence: Моя сестра пише листа.
   - sentence: Мій брат малює.
   ```

2. **Missing discourse markers:**
   ```yaml
   # ❌ BAD
   Я прокинувся. Я поснідав. Я пішов.

   # ✅ GOOD
   Спочатку я прокинувся. Потім я поснідав. Нарешті я пішов.
   ```

3. **Incoherent topic jumps:**
   ```yaml
   # ❌ BAD
   - Я йду до школи.
   - Кава без цукру.

   # ✅ GOOD
   - Я йду до школи щодня.
   - Школа знаходиться біля парку.
   ```

**Fixes:**
| Issue | Solution | Connectors |
|-------|----------|------------|
| Subject shifts | Unify context (family, day) | я → моя сестра, мама |
| No flow | Add discourse markers | спочатку, потім, нарешті |
| Topic jumps | Create mini-narrative | а, але, тому |

**Vocabulary constraints:**
- ONLY use from `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`
- Don't use words from later modules

**Test with MCP:**
```bash
mcp__ukrainian-validator__check_naturalness(
  content="...",
  level="A2",
  context="fill-in activity"
)
```

## Content-Heavy Modules (B2-HIST, C1-BIO)

**Golden Rule:** "Can learner answer without reading Ukrainian text?"
- YES → Rewrite (tests content, not language)
- NO → Keep (tests comprehension)

**Activity mix (10-12 total):**
| Type | Count | Requirement |
|------|-------|-------------|
| quiz | 4-5 | MUST start "Згідно з текстом..." |
| fill-in/cloze | 3-4 | Test collocations |
| error-correction | 2-3 | Fix GRAMMAR, not facts |
| match-up | 1-2 | Ukrainian term ↔ definition |

**Forbidden:** "У якому році...", "Хто був...", "Скільки..."
**Required:** "Згідно з текстом, як автор...", "Яку функцію..."

## Seminar Tracks (LIT, B2-HIST, C1-HIST, C1-BIO)

**Reading-Analysis Pairs:** Every analytical activity MUST link to reading.

### Core Structure
```yaml
# INPUT
- type: reading
  id: reading-01  # REQUIRED
  title: 'Джерело: ...'
  text: |
    [200-500 words]

# OUTPUT
- type: essay-response
  source_reading: reading-01  # REQUIRED link
  title: 'Есе: ...'
  model_answer: |
    [300-500 for C1, 150-250 for B2]
```

### Activity Counts

| Track | Level | Count | Essay Length |
|-------|-------|-------|--------------|
| LIT | post-C1 | 3-6 | 300-500 |
| C1-HIST/BIO | C1 | 3-5 | 250-400 |
| B2-HIST | B2 | 3-6 | 150-250 |

### Required Types

**Use ONLY:**
- `reading` (1-2, always with `id`)
- `essay-response` (1-2, always with `source_reading`)
- `critical-analysis` (1-2, always with `source_reading`)
- `comparative-study` (0-1, always with `source_reading`)

**Analytical activities MUST have:**
```yaml
source_reading: reading-01
target_text: "Quote from source"
questions: [...]
model_answer: |
  [Substantive analysis]
```

### Common Violations

| Violation | Fix |
|-----------|-----|
| `MISSING_SOURCE_READING` | Add `source_reading: reading-XX` |
| `READING_MISSING_ID` | Add `id: reading-XX` |
| `INVALID_SOURCE_READING` | Fix broken reference |

### Self-Validation (MANDATORY)

**Before outputting, verify:**
1. **URLs** - Do you know this URL? Does it match the author?
2. **Coherence** - Does `target_text` appear in source?
3. **Model Answers** - Do they address prompts?
4. **Facts** - Are dates/names correct?

**If uncertain:** STOP and ask user.

## Activity Types Reference

**Standard (A1-C2):**
`quiz`, `fill-in`, `cloze`, `match-up`, `true-false`, `group-sort`, `unjumble`, `error-correction`, `mark-the-words`, `select`, `translate`

**Seminar (LIT, HIST, BIO):**
`reading`, `essay-response`, `critical-analysis`, `comparative-study`, `authorial-intent`

**See `docs/ACTIVITY-YAML-REFERENCE.md` for complete syntax.**

## YAML Format Examples

### Quiz
```yaml
- type: quiz
  title: 'Квіз: Title'
  instruction: 'Choose correct answer'
  items:
    - question: 'Text?'
      correct: 'answer'
      options: [answer, opt1, opt2, opt3]
      explanation: 'Why...'
```

### Match-up
```yaml
- type: match-up
  title: 'Title'
  instruction: 'Match pairs'
  pairs:
    - left: term
      right: definition
```

### Fill-in
```yaml
- type: fill-in
  title: 'Title'
  instruction: 'Choose correct word'
  items:
    - sentence: "Text [___] here"
      answer: correct
      options: [correct, opt1, opt2, opt3]
```

### Cloze
```yaml
- type: cloze
  title: 'Title'
  instruction: 'Fill blanks'
  passage: 'Text {ans1|opt1|opt2} more {ans2|opt3|opt4}.'
```

### Error-correction
```yaml
- type: error-correction
  title: 'Title'
  instruction: 'Find and fix ONE error'
  items:
    - sentence: "Text з помилкою."
      error: "помилкою"
      answer: "помилкою"
      options: [помилкою, помилка, помилку, помилці]
      explanation: "After 'з' use instrumental..."
```

### Unjumble
```yaml
- type: unjumble
  title: 'Title'
  instruction: 'Put in correct order'
  items:
    - jumbled: "word / order / wrong / in"
      answer: "in wrong word order"
```

### Mark-the-Words
```yaml
- type: mark-the-words
  title: 'Title'
  instruction: 'Знайдіть усі іменники'
  text: "Гарний день приніс радість."
  answers: [день, радість]
```

### Seminar Reading-Analysis Pair
```yaml
- type: reading
  id: reading-testament
  title: 'Джерело: Заповіт'
  source: 'Тарас Шевченко (1845)'
  text: |
    Як умру, то поховайте...

- type: critical-analysis
  source_reading: reading-testament
  title: 'Аналіз символіки'
  target_text: 'Поховайте та вставайте...'
  questions:
    - 'Яку функцію виконує імператив?'
  model_answer: |
    Імператив у Шевченка...
```

## YAML Quoting Rules

1. **Cloze/mark-the-words quoted speech** - use Ukrainian guillemets `«»`:
   ```yaml
   # ✅ CORRECT
   passage: "Він сказав: «{Привіт}!»"

   # ❌ WRONG - breaks MDX
   passage: "Він сказав: \"{Привіт}!\""
   ```

2. **Embedded quotes (other fields)** - wrap in single, double internal:
   ```yaml
   explanation: '"Думка" means opinion.'
   ```

3. **Colons** - quote strings:
   ```yaml
   explanation: 'Правильно: так і ні.'
   ```

4. **Numeric options** - quote as strings:
   ```yaml
   # ✅ CORRECT
   - text: '5'

   # ❌ WRONG
   - text: 5
   ```

## Activity Sequencing

**A1:**
```
match-up → group-sort → quiz → true-false → fill-in → anagram/unjumble
```

**A2-B1:**
```
[recognition] mark-the-words → match-up → group-sort
[discrimination] quiz → true-false → select
[controlled] fill-in → cloze → error-correction
[production] unjumble → translate
```

**B2-C2:**
```
[discrimination] select
[controlled] fill-in → cloze → error-correction ×2-3
[production] translate → unjumble ×2-3
```

## Validation

```bash
# Validate YAML
npm run validate:yaml curriculum/l2-uk-en/{level}/{file}.activities.yaml

# Run audit
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{file}.md
```

## Checklist

- [ ] Created `.activities.yaml` (NOT embedded in `.md`)
- [ ] Activity count meets level requirement
- [ ] Items per activity meets minimum
- [ ] Activity variety (4-5+ types)
- [ ] Proper sequencing (easy → hard)
- [ ] Valid YAML syntax
- [ ] All answers correct
- [ ] Uses ONLY vocabulary from YAML + prior modules
- [ ] Strings with quotes/colons properly escaped
- [ ] Naturalness >= 8/10 for prose activities

## DO NOT

- Embed activities in `.md` file
- Use vocabulary not in YAML or prior modules
- Write fewer than required activities
- Create activities with fewer than minimum items
- Leave quotes/colons unescaped
