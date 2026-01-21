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
sources: ✓        # Required for tracks, optional for core
```

### 2. Word Target in Range

| Level | Min | Max | Notes |
|-------|-----|-----|-------|
| A1 | 300 | 750 | M01-05: 300-450, M06-10: 500-650, M11+: 750+ |
| A2 | 1000 | 1500 | Core curriculum |
| B1 | 1500 | 2000 | Core curriculum |
| B2 (core) | 1750 | 2500 | Grammar/vocab |
| B2-HIST | 3000 | 5000 | History track |
| B2-PRO | 2000 | 3000 | Professional track |
| C1 (core) | 2000 | 3000 | Advanced |
| C1-BIO | 4000 | 6000 | Biography track |
| C1-HIST | 4000 | 6000 | History track |
| LIT | 5000 | 8000 | Literature spec |
| C2 | 2000 | 4000 | Mastery level |

### 3. Objectives Quality

Each objective MUST:

**For A1-A2 (English objectives):**
- Start with "Learner can" or "Student can"
- Use measurable verb (recognize, pronounce, read, write, etc.)
- Be specific and testable
- ❌ BAD: "Learner understands the alphabet"
- ✓ GOOD: "Learner can recognize and pronounce 19 Cyrillic letters"

**For B1+ (Ukrainian objectives):**
- Start with "Учень може"
- Use measurable verb (описати, пояснити, проаналізувати, оцінити, etc.)
- Be specific and testable
- ❌ BAD: "Учень розуміє історію"
- ✓ GOOD: "Учень може порівняти політичний устрій Київської Русі з сучасною Україною"

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

**Track modules (B2-HIST, C1-BIO, C1-HIST, LIT):** Minimum 2 sources REQUIRED

**Core modules (A1-C2 core):** Sources OPTIONAL (but recommended for B2+)

When sources are present, each source MUST have:
- `name`: Descriptive title
- `url`: Valid URL
- `type`: reference, primary, or academic
- `notes`: Why this source is relevant

Trusted domains for Ukrainian content:
- uk.wikipedia.org
- resource.history.org.ua
- litopys.org.ua
- esu.com.ua
- slovnyk.ua
- mova.institute
- Academic journals (.edu, .ac.uk)

### 7. YAML Syntax

- No unquoted strings starting with quotes
- Arrays properly formatted
- No duplicate keys

### 8. Script Validation

Run mechanical validation:

```bash
.venv/bin/python scripts/audit_module.py --phase=meta curriculum/l2-uk-en/{level}/meta/{slug}.yaml
```

All checks must pass before proceeding.

**Note:** This check verifies:
- YAML syntax is parseable
- All required fields exist
- Word targets are within valid ranges
- No structural anomalies

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
✓ Script validation passed

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
