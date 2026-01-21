# Phase 2: module-meta-qa

Validate module metadata before locking.

## Usage

```
/module-meta-qa {level} {module_num}
```

## Input

- `curriculum/l2-uk-en/{level}/meta/{slug}.yaml`

## Validation Checks

### 1. Required Fields Present

All these fields MUST exist:

```yaml
module: ✓
id: ✓
title: ✓          # Must be in Ukrainian
subtitle: ✓       # English translation
slug: ✓
version: ✓
phase: ✓
focus: ✓
pedagogy: ✓
objectives: ✓     # Array with 3-5 items
grammar: ✓        # Array with 2+ items
word_target: ✓
content_outline: ✓
vocabulary_hints: ✓
activity_hints: ✓
sources: ✓        # Array with 2+ items
```

### 2. Word Target in Range

| Level | Min | Max |
|-------|-----|-----|
| B2-HIST | 3000 | 5000 |
| C1-BIO | 4000 | 6000 |
| LIT | 5000 | 8000 |
| C2 | 4000 | 6000 |

### 3. Objectives Quality

Each objective MUST:
- Start with "Учень може"
- Use measurable verb (describe, explain, analyze, evaluate, etc.)
- Be specific and testable
- Be in Ukrainian

❌ BAD: "Учень розуміє історію"
✓ GOOD: "Учень може порівняти політичний устрій Київської Русі з сучасною Україною"

### 4. Content Outline Structure

Each section MUST have:
- `section`: Ukrainian heading
- `words`: Word count target (number)
- `points`: Array of key points (can be empty for intro/outro)

Sum of all section word counts MUST equal ±10% of `word_target`.

### 5. Activity Hints Match Pedagogy

| Pedagogy | Required Activity Types |
|----------|------------------------|
| seminar | reading, quiz, essay-response or critical-analysis |
| TTT | diagnostic, practice, error-correction |
| PPP | presentation, practice, production |
| CLIL | reading, vocabulary, discussion |

### 6. Sources Credibility

Minimum 2 sources. Each source MUST have:
- `name`: Descriptive title
- `url`: Valid URL
- `type`: reference, primary, or academic
- `notes`: Why this source is relevant

Trusted domains:
- uk.wikipedia.org
- resource.history.org.ua
- litopys.org.ua
- esu.com.ua
- Academic journals

### 7. YAML Syntax

- No unquoted strings starting with quotes
- Arrays properly formatted
- No duplicate keys

## Output

### On PASS

```
META-QA: PASS

✓ Required fields present
✓ Word target: {N} (within range)
✓ Objectives: {N} measurable items
✓ Content outline: {N} sections, {total} words
✓ Activity hints: {N} types (pedagogy match)
✓ Sources: {N} credible sources
✓ YAML syntax valid

META LOCKED. Proceed to: /module-lesson {level} {module_num}
```

### On FAIL

```
META-QA: FAIL

Violations:
1. [CHECK_NAME]: {specific issue}
2. [CHECK_NAME]: {specific issue}

Fix meta.yaml and re-run /module-meta-qa {level} {module_num}
```

## Phase Rewind

If meta cannot be fixed without changing curriculum plan:

```
PHASE UNLOCK REQUIRED: {reason}

Cannot proceed. Curriculum plan needs adjustment.
```

---

**On PASS:** Meta is LOCKED. Do not modify. Proceed to `/module-lesson`.
