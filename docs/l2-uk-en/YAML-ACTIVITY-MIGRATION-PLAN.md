# YAML Activity Migration Plan

**Purpose:** Replace error-prone markdown activity syntax with structured YAML for reliability and schema validation.

**Status:** Planning phase - to be tested on B2 modules first.

**Related Issues:** Activity format errors occurring despite template documentation.

---

## Problem Statement

Despite comprehensive templates with activity format quick references, modules still have activity syntax errors:
- Ambiguous markdown syntax (overloaded `[ ]`, `>`, `|` symbols)
- Context-dependent parsing (same symbols mean different things)
- No validation until audit runs
- Templates are reference material, not enforced structure

## Proposed Solution

**Separate content from activities:**
- `.md` file: Prose content (intro, explanations, readings, vocabulary)
- `.yaml` file: Structured activities with schema validation

**Benefits:**
- Schema validation catches errors before audit
- Self-documenting fields (explicit `correct:`, `wrong:`, `explanation:`)
- IDE support (YAML linting, autocomplete)
- No ambiguous symbols
- Convertible to/from current markdown format

---

## Architecture Overview

### What Stays in Markdown

```
curriculum/l2-uk-en/{level}/{num}-{slug}.md
```

Contains:
- Frontmatter (module, title, phase, pedagogy, etc.)
- `# [Title]` - Module title section
- `# Вступ` - Introduction
- `# Лексика` / `# Словник` - Vocabulary presentation
- `# Використання` - Grammar/usage explanations
- `# Читання` - Reading passages
- `# Діалоги` - Dialogues
- `# Вправи` - Activities header (placeholder pointing to YAML)
- `# Підсумок` - Summary
- `# Словник` / `# Vocabulary` - Vocabulary table

### What Goes to YAML

```
curriculum/l2-uk-en/{level}/{num}-{slug}.activities.yaml
```

Contains:
- All 13 activity types with structured data
- Explicit correct/wrong answers
- Explanations
- Options/distractors
- Metadata (item count, difficulty)

---

## File Structure

### Current Structure

```
curriculum/l2-uk-en/b1/
├── 53-abstract-concepts-processes.md     # Everything in one file
```

### New Structure

```
curriculum/l2-uk-en/b1/
├── 53-abstract-concepts-processes.md           # Prose only
├── 53-abstract-concepts-processes.activities.yaml  # Activities only
```

---

## Activity YAML Schemas

### 1. quiz (Multiple Choice - Single Answer)

```yaml
- type: quiz
  title: "Вибір правильної форми"
  items:
    - question: "Яке слово означає 'зміна на краще'?"
      options:
        - text: "погіршення"
          correct: false
        - text: "покращення"
          correct: true
        - text: "сповільнення"
          correct: false
        - text: "зупинка"
          correct: false
      explanation: "Покращення — зміна на краще, погіршення — зміна на гірше."
```

### 2. select (Multiple Choice - Multiple Answers)

```yaml
- type: select
  title: "Оберіть усі правильні відповіді"
  items:
    - question: "Які слова означають позитивні зміни?"
      options:
        - text: "покращення"
          correct: true
        - text: "погіршення"
          correct: false
        - text: "зростання"
          correct: true
        - text: "занепад"
          correct: false
        - text: "розвиток"
          correct: true
      min_correct: 3
```

### 3. true-false (Statement Validation)

```yaml
- type: true-false
  title: "Правда чи ні?"
  items:
    - statement: "Модернізація означає оновлення застарілих систем."
      correct: true
      explanation: "Модернізація — процес оновлення, осучаснення."
    - statement: "Стагнація означає швидкий розвиток."
      correct: false
      explanation: "Стагнація — застій, відсутність розвитку."
```

### 4. fill-in (Gap Fill with Dropdown)

```yaml
- type: fill-in
  title: "Виберіть правильне слово"
  items:
    - sentence: "Економіка демонструє ознаки ___."
      answer: "відновлення"
      options:
        - "відновлення"
        - "відновлювання"
        - "відновити"
        - "відновляти"
      explanation: "Віддієслівний іменник 'відновлення' (процес)."
```

### 5. cloze (Passage with Multiple Blanks)

```yaml
- type: cloze
  title: "Економічний аналіз"
  passage: |
    Експерти прогнозують {1} економіки наступного року.
    Після періоду {2} очікується стабільне {3}.
    {4} інфляції залишається пріоритетом уряду.
  blanks:
    - id: 1
      answer: "зростання"
      options: ["зростання", "падіння", "зупинку", "кризу"]
    - id: 2
      answer: "стагнації"
      options: ["стагнації", "розвитку", "зростання", "покращення"]
    - id: 3
      answer: "відновлення"
      options: ["відновлення", "погіршення", "занепад", "криза"]
    - id: 4
      answer: "Стримування"
      options: ["Стримування", "Прискорення", "Ігнорування", "Збільшення"]
```

### 6. match-up (Pair Matching)

```yaml
- type: match-up
  title: "Антоніми"
  pairs:
    - left: "зростання"
      right: "падіння"
    - left: "покращення"
      right: "погіршення"
    - left: "прискорення"
      right: "сповільнення"
    - left: "стабілізація"
      right: "дестабілізація"
```

### 7. group-sort (Categorization)

```yaml
- type: group-sort
  title: "Позитивні та негативні зміни"
  groups:
    - name: "Позитивні зміни"
      items:
        - "покращення"
        - "зростання"
        - "розвиток"
        - "модернізація"
        - "оновлення"
    - name: "Негативні зміни"
      items:
        - "погіршення"
        - "занепад"
        - "деградація"
        - "криза"
        - "стагнація"
```

### 8. unjumble (Word Reordering)

```yaml
- type: unjumble
  title: "Побудуйте речення"
  items:
    - words: ["Економіка", "демонструє", "ознаки", "відновлення", "."]
      answer: "Економіка демонструє ознаки відновлення."
    - words: ["стабільне", "Спостерігається", "зростання", "експорту", "."]
      answer: "Спостерігається стабільне зростання експорту."
```

### 9. error-correction (Find and Fix)

```yaml
- type: error-correction
  title: "Виправте помилки"
  items:
    - sentence: "Компанія переживає глибоку трансформацію цифрова."
      error: "цифрова"
      answer: "цифрову"
      options: ["цифрова", "цифрову", "цифровий", "цифрове"]
      explanation: "Знахідний відмінок жіночого роду: яку? — цифрову."
    - sentence: "Уряд планує провести модернізація інфраструктури."
      error: "модернізація"
      answer: "модернізацію"
      options: ["модернізація", "модернізацію", "модернізації", "модернізаціям"]
      explanation: "Після 'провести' потрібен знахідний відмінок: що? — модернізацію."
```

### 10. mark-the-words (Click Words Matching Criteria)

```yaml
- type: mark-the-words
  title: "Іменники процесів"
  instruction: "Позначте всі іменники, що означають процеси"
  passage: |
    Економіка демонструє ознаки відновлення після тривалої кризи.
    Спостерігається стабільне зростання експорту товарів і послуг.
    Компанія переживає глибоку цифрову трансформацію своїх бізнес-процесів.
  correct_words:
    - "відновлення"
    - "зростання"
    - "трансформацію"
```

### 11. translate (Translation Multiple Choice)

```yaml
- type: translate
  title: "Перекладіть речення"
  items:
    - source: "The economy is showing signs of recovery."
      options:
        - text: "Економіка демонструє ознаки відновлення."
          correct: true
        - text: "Економіка показує знаки відновлення."
          correct: false
        - text: "Економія демонструє ознаки відновлення."
          correct: false
      explanation: "'Signs' = ознаки (не знаки), 'economy' = економіка (не економія)."
```

### 12. anagram (Letter Unscrambling - A1 Only)

```yaml
- type: anagram
  title: "Розшифруйте слова"
  items:
    - scrambled: "ЛВСОО"
      answer: "СЛОВО"
      hint: "word"
    - scrambled: "ИМІР"
      answer: "МИР"
      hint: "peace / world"
```

---

## Vocabulary YAML Schema (Optional)

For levels with complex vocabulary, vocabulary can also be YAML:

```yaml
# {num}-{slug}.vocabulary.yaml
vocabulary:
  - word: "зростання"
    ipa: "/zrosˈtɑnʲːɑ/"
    translation: "growth"
    pos: "noun"
    gender: "n"
    note: "process noun from зростати"

  - word: "покращення"
    ipa: "/pokrɑˈʃɛnʲːɑ/"
    translation: "improvement"
    pos: "noun"
    gender: "n"
    note: "process noun from покращувати"
```

---

## JSON Schema for Validation

Create `schemas/activities.schema.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Module Activities",
  "type": "array",
  "items": {
    "oneOf": [
      { "$ref": "#/definitions/quiz" },
      { "$ref": "#/definitions/select" },
      { "$ref": "#/definitions/true-false" },
      { "$ref": "#/definitions/fill-in" },
      { "$ref": "#/definitions/cloze" },
      { "$ref": "#/definitions/match-up" },
      { "$ref": "#/definitions/group-sort" },
      { "$ref": "#/definitions/unjumble" },
      { "$ref": "#/definitions/error-correction" },
      { "$ref": "#/definitions/mark-the-words" },
      { "$ref": "#/definitions/translate" },
      { "$ref": "#/definitions/anagram" }
    ]
  },
  "definitions": {
    "quiz": {
      "type": "object",
      "required": ["type", "title", "items"],
      "properties": {
        "type": { "const": "quiz" },
        "title": { "type": "string" },
        "items": {
          "type": "array",
          "minItems": 8,
          "items": {
            "type": "object",
            "required": ["question", "options"],
            "properties": {
              "question": { "type": "string" },
              "options": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": {
                  "type": "object",
                  "required": ["text", "correct"],
                  "properties": {
                    "text": { "type": "string" },
                    "correct": { "type": "boolean" }
                  }
                }
              },
              "explanation": { "type": "string" }
            }
          }
        }
      }
    },
    "error-correction": {
      "type": "object",
      "required": ["type", "title", "items"],
      "properties": {
        "type": { "const": "error-correction" },
        "title": { "type": "string" },
        "items": {
          "type": "array",
          "minItems": 6,
          "items": {
            "type": "object",
            "required": ["sentence", "error", "answer", "options", "explanation"],
            "properties": {
              "sentence": { "type": "string" },
              "error": { "type": "string" },
              "answer": { "type": "string" },
              "options": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": { "type": "string" }
              },
              "explanation": { "type": "string" }
            }
          }
        }
      }
    }
  }
}
```

---

## Conversion Strategy

### MD → YAML Converter

Create `scripts/convert_md_to_yaml.py`:

1. Parse markdown file
2. Extract activity sections (## {type}: {title})
3. Parse each activity into structured YAML
4. Write .activities.yaml file
5. Update .md file to reference YAML

### YAML → MDX Generator

Update `scripts/generate_mdx.py`:

1. Read .md file for prose content
2. Read .activities.yaml for activities
3. Generate MDX with both combined
4. No change to output format (MDX stays same)

### Validation Pipeline

```bash
# New validation step before audit
npm run validate:yaml l2-uk-en b1 53

# Validates:
# - YAML syntax
# - Schema compliance
# - Required fields present
# - Minimum item counts
# - Answer validity (correct answer in options)
```

---

## Migration Timeline

### Phase 1: Infrastructure (Week 1-2)

- [ ] Create JSON Schema for all 13 activity types
- [ ] Create `validate_yaml.py` script
- [ ] Update `generate_mdx.py` to read YAML activities
- [ ] Add `npm run validate:yaml` command

### Phase 2: B2 Pilot (Week 3-4)

- [ ] Convert 5 B2 modules to YAML format
- [ ] Test full pipeline (validate → generate → audit)
- [ ] Iterate on schema based on issues found
- [ ] Document any edge cases

### Phase 3: B1 Migration (Week 5)

- [ ] Run batch conversion on all B1 modules
- [ ] Fix any conversion errors
- [ ] Verify all modules pass audit

### Phase 4: A1/A2 Migration (Week 6)

- [ ] Convert A1 modules (handle anagram type)
- [ ] Convert A2 modules
- [ ] Verify all modules pass audit
- [ ] Update documentation

### Phase 5: Cleanup

- [ ] Remove old markdown activity parsing code (optional)
- [ ] Update templates to show YAML format
- [ ] Update CLAUDE.md instructions

---

## Level-Specific Constraints

Activity requirements vary by level. The validation system MUST enforce these constraints.

### Activity Availability Matrix

| Activity Type | A1 | A2 | B1 | B2 | C1 | C2 |
|---------------|----|----|----|----|----|----|
| quiz | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| match-up | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| fill-in | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| group-sort | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| unjumble | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| true-false | ✓ | ✓ | ✓ | ✓ | opt | opt |
| anagram | M01-10 | ❌ | ❌ | ❌ | ❌ | ❌ |
| error-correction | ❌ | ✓ | ✓ | ✓ | ✓ | ✓ |
| cloze | ❌ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mark-the-words | ❌ | ✓ | ✓ | ✓ | ✓ | ✓ |
| select | ❌ | opt | ✓ | ✓ | ✓ | ✓ |
| translate | ❌ | opt | ✓ | ✓ | ✓ | ✓ |

### Minimum Item Counts by Level

| Activity Type | A1 | A2 | B1+ |
|---------------|----|----|-----|
| quiz | 6 | 8 | 8 |
| match-up | 6 | 8 | 8 |
| fill-in | 6 | 8 | 8 |
| group-sort | 10 | 14 | 14 |
| unjumble | 4 | 6 | 6 |
| true-false | 6 | 8 | 8 |
| anagram | 6 | — | — |
| error-correction | — | 6 | 6 |
| cloze | — | 10 | 14 |
| mark-the-words | — | 6 | 6 |
| select | — | 6 | 6 |
| translate | — | 6 | 6 |

### Schema Implementation for Level Constraints

The JSON Schema cannot encode level-specific constraints directly. Solution: **level-specific schema files**.

```
schemas/
├── activities-base.schema.json    # Shared definitions
├── activities-a1.schema.json      # A1-specific constraints
├── activities-a2.schema.json      # A2-specific constraints
├── activities-b1.schema.json      # B1+ constraints (B1, B2, C1, C2)
```

**Validator usage:**
```bash
npm run validate:yaml l2-uk-en a1 05   # Uses activities-a1.schema.json
npm run validate:yaml l2-uk-en b1 53   # Uses activities-b1.schema.json
```

---

## Backward Compatibility Strategy

During migration, the system must handle mixed formats (some modules MD, some YAML).

### Dual-Format Support

**Detection Logic:**
```python
def get_activity_source(module_path):
    yaml_path = module_path.replace('.md', '.activities.yaml')
    if os.path.exists(yaml_path):
        return 'yaml', yaml_path
    else:
        return 'md', module_path  # Parse activities from MD
```

**Implementation:**
1. Generator checks for `.activities.yaml` first
2. If exists → read activities from YAML
3. If not → fall back to MD parsing (current behavior)
4. Both paths produce identical MDX output

### Migration Tracking

Track conversion status in module frontmatter:

```yaml
---
module: b1-053
title: "..."
activities_format: yaml  # or 'md' (default if missing)
---
```

**Or** maintain a tracking file:

```yaml
# curriculum/l2-uk-en/migration-status.yaml
a1:
  converted: [1, 2, 3, 4, 5]  # Module numbers
  pending: [6, 7, 8, ...]
b1:
  converted: []
  pending: [1, 2, 3, ...]
```

### Cutover Strategy

| Phase | MD Activities | YAML Activities |
|-------|---------------|-----------------|
| Pre-migration | Active | Not supported |
| Phase 2-4 | Supported (fallback) | Preferred |
| Phase 5+ | Deprecated | Required |
| Phase 6 (future) | Removed | Only option |

---

## Conversion Edge Cases & Error Handling

### Pre-Conversion Requirements

**CRITICAL:** Module must pass audit BEFORE conversion.

```bash
# Step 1: Verify module passes audit
python3 scripts/audit_module.py curriculum/l2-uk-en/b1/53-*.md

# Step 2: Only convert if PASS
npm run convert:yaml l2-uk-en b1 53
```

**Rationale:** Converting a broken MD module produces broken YAML. Fix MD first.

### Known Edge Cases

| Edge Case | Problem | Solution |
|-----------|---------|----------|
| Malformed MD syntax | Parser fails | Manual conversion queue |
| Ukrainian quotes « » | YAML string escaping | Use `\|` block scalar |
| Pipes in tables | Conflicts with MD table | Already extracted to YAML |
| Nested blockquotes | Complex parsing | Flatten in YAML |
| Empty explanations | Optional field | Allow null/omit |
| Duplicate correct answers | Multiple `correct: true` | Schema validation |

### Special Character Handling

```yaml
# Problem: Special characters in Ukrainian text
- sentence: "Він сказав: «Добре»."  # OK - quotes inside string
- sentence: 'Він сказав: "Добре".'  # Also OK

# Use block scalar for complex text:
- passage: |
    Текст з різними символами:
    — тире (em-dash)
    « » лапки
    ... три крапки
```

### Conversion Error Handling

```python
def convert_module(module_path):
    try:
        activities = parse_md_activities(module_path)
        yaml_content = activities_to_yaml(activities)
        write_yaml(yaml_content, yaml_path)
        return {'status': 'success', 'activities': len(activities)}
    except ParseError as e:
        return {
            'status': 'failed',
            'error': str(e),
            'line': e.line_number,
            'activity': e.activity_type
        }
```

**Failed conversions go to manual review queue:**
```
curriculum/l2-uk-en/conversion-failed.log
```

---

## Rollback Strategy

### Decision Criteria: When to Rollback

| Condition | Action |
|-----------|--------|
| B2 pilot: >50% modules fail conversion | Rollback, redesign schema |
| B2 pilot: Generator output differs from MD | Fix generator, continue |
| B2 pilot: Audit failures after conversion | Fix conversion, continue |
| Any phase: Data loss detected | Immediate rollback |

### Rollback Procedure

**Level 1: Module-level rollback**
```bash
# Keep MD activities, delete YAML
rm curriculum/l2-uk-en/b1/53-*.activities.yaml
# Generator falls back to MD automatically
```

**Level 2: Level-wide rollback**
```bash
# Delete all YAML files for a level
rm curriculum/l2-uk-en/b1/*.activities.yaml
# Update migration-status.yaml
```

**Level 3: Full rollback**
```bash
# Revert to pre-migration branch
git checkout pre-yaml-migration -- curriculum/
git checkout pre-yaml-migration -- scripts/
```

### Data Safety Rules

1. **Never delete MD activities** until Phase 5 (after full validation)
2. **Git branch per phase:** `yaml-migration/phase-2-b2-pilot`
3. **Backup before batch conversion:** `cp -r curriculum/ curriculum-backup-$(date +%Y%m%d)/`

---

## Testing Strategy

### Test Categories

| Category | Purpose | Location |
|----------|---------|----------|
| Unit tests | YAML parser functions | `tests/test_yaml_parser.py` |
| Schema tests | Valid/invalid YAML examples | `tests/fixtures/yaml/` |
| Integration tests | Full pipeline | `tests/test_pipeline_yaml.py` |
| Regression tests | MD vs YAML output comparison | `tests/test_regression.py` |

### Test Fixtures

```
tests/fixtures/yaml/
├── valid/
│   ├── quiz-minimal.yaml       # Minimum valid quiz
│   ├── quiz-full.yaml          # All optional fields
│   ├── all-activities.yaml     # One of each type
│   └── edge-cases.yaml         # Special characters, long text
├── invalid/
│   ├── missing-required.yaml   # Missing 'type' field
│   ├── wrong-type.yaml         # Invalid activity type
│   ├── too-few-items.yaml      # Below minimum count
│   ├── no-correct-answer.yaml  # Options without correct
│   └── duplicate-correct.yaml  # Multiple correct (for quiz)
└── level-specific/
    ├── a1-valid.yaml           # A1-specific constraints
    ├── a1-invalid-cloze.yaml   # Cloze not allowed at A1
    └── b1-valid.yaml           # B1 constraints
```

### Regression Testing

**Compare MD-sourced vs YAML-sourced output:**

```python
def test_output_equivalence():
    # Generate MDX from MD activities
    mdx_from_md = generate_mdx(module_path, source='md')

    # Generate MDX from YAML activities
    mdx_from_yaml = generate_mdx(module_path, source='yaml')

    # Compare (ignoring whitespace)
    assert normalize(mdx_from_md) == normalize(mdx_from_yaml)
```

### CI Integration Tests

```yaml
# .github/workflows/test-yaml.yml
- name: Validate all YAML files
  run: npm run validate:yaml:all

- name: Run regression tests
  run: npm run test:regression

- name: Check output equivalence
  run: npm run test:equivalence
```

---

## Architecture & Data Flow

### Current Architecture (MD-only)

```
┌─────────────────┐
│  module.md      │ ──── parse ────▶ ┌─────────────┐
│  (prose +       │                  │  Generator  │ ──▶ MDX/JSON
│   activities)   │                  └─────────────┘
└─────────────────┘                         │
                                            ▼
                                    ┌─────────────┐
                                    │   Audit     │
                                    └─────────────┘
```

### New Architecture (YAML activities)

```
┌─────────────────┐     ┌─────────────────────┐
│  module.md      │     │  module.activities  │
│  (prose only)   │     │  .yaml              │
└────────┬────────┘     └──────────┬──────────┘
         │                         │
         │    ┌────────────────────┤
         │    │                    │
         ▼    ▼                    ▼
    ┌─────────────┐        ┌─────────────┐
    │  Generator  │        │  Validator  │ ◀── Schema
    └──────┬──────┘        └─────────────┘
           │
           ▼
    ┌─────────────┐
    │  MDX/JSON   │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │   Audit     │ (validates output, not source)
    └─────────────┘
```

### Shared YAML Parser

**CRITICAL:** Single parser used by both Generator and Validator.

```python
# scripts/yaml_activities.py

class ActivityParser:
    """Single source of truth for YAML activity parsing."""

    def parse(self, yaml_path: str) -> List[Activity]:
        """Parse YAML file into Activity objects."""
        ...

    def validate(self, activities: List[Activity], level: str) -> ValidationResult:
        """Validate activities against level-specific rules."""
        ...

    def to_mdx(self, activities: List[Activity]) -> str:
        """Convert activities to MDX format."""
        ...

    def to_json(self, activities: List[Activity]) -> dict:
        """Convert activities to JSON format (Vibe app)."""
        ...
```

**Usage:**
```python
# In generate_mdx.py
from yaml_activities import ActivityParser
parser = ActivityParser()
activities = parser.parse(yaml_path)
mdx = parser.to_mdx(activities)

# In validate_yaml.py
from yaml_activities import ActivityParser
parser = ActivityParser()
activities = parser.parse(yaml_path)
result = parser.validate(activities, level='b1')
```

### Audit Script Integration

**Decision:** Audit validates generated output, not YAML source.

**Rationale:**
- Audit checks final user experience (MDX/HTML)
- YAML validation handles source format
- Keeps audit independent of source format

**Flow:**
```
YAML ──▶ Validator ──▶ Generator ──▶ MDX ──▶ Audit
                                            ▲
                                            │
                                      (validates this)
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/validate-activities.yml
name: Validate Activities

on:
  push:
    paths:
      - 'curriculum/**/*.activities.yaml'
  pull_request:
    paths:
      - 'curriculum/**/*.activities.yaml'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Validate YAML syntax
        run: npm run validate:yaml:syntax

      - name: Validate against schema
        run: npm run validate:yaml:schema

      - name: Check activity constraints
        run: npm run validate:yaml:constraints

      - name: Generate and compare output
        run: npm run test:equivalence
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-activity-yaml
        name: Validate activity YAML
        entry: npm run validate:yaml:changed
        language: system
        files: '\.activities\.yaml$'
        pass_filenames: true
```

### PR Template Update

```markdown
<!-- .github/pull_request_template.md -->

## Activity Changes

- [ ] YAML files pass validation: `npm run validate:yaml l2-uk-en {level} {module}`
- [ ] Generated output matches expected: `npm run test:equivalence`
- [ ] Audit passes: `python3 scripts/audit_module.py {file}`
```

---

## Developer Experience

### IDE Setup: VS Code

**Recommended extensions:**
- YAML (Red Hat) - YAML language support
- YAML JSON Schema (Erik Lynd) - Schema autocomplete

**Workspace settings (`.vscode/settings.json`):**
```json
{
  "yaml.schemas": {
    "./schemas/activities-b1.schema.json": "curriculum/l2-uk-en/b1/*.activities.yaml",
    "./schemas/activities-a1.schema.json": "curriculum/l2-uk-en/a1/*.activities.yaml",
    "./schemas/activities-a2.schema.json": "curriculum/l2-uk-en/a2/*.activities.yaml"
  },
  "yaml.validate": true,
  "yaml.hover": true,
  "yaml.completion": true,
  "[yaml]": {
    "editor.defaultFormatter": "redhat.vscode-yaml",
    "editor.formatOnSave": true,
    "editor.tabSize": 2
  }
}
```

### Error Message Quality

**Bad (raw JSON Schema error):**
```
Error: oneOf failed at #/items/0
```

**Good (custom formatter):**
```
Error in quiz activity "Вибір правильної форми":
  - Item 3: Missing required field 'explanation'
  - Item 5: No correct answer (all options have correct: false)
  - Total items: 6 (minimum required: 8 for B1)
```

**Implementation:**
```python
def format_validation_error(error, yaml_content):
    """Convert JSON Schema error to human-readable message."""
    activity = find_activity_at_path(yaml_content, error.path)
    return f"""
Error in {activity['type']} activity "{activity['title']}":
  - {describe_error(error)}
  - Line: {find_line_number(yaml_content, error.path)}
"""
```

### Contributor Guide

Create `docs/CONTRIBUTING-ACTIVITIES.md`:

```markdown
# Contributing Activities (YAML Format)

## Quick Start

1. Copy template: `cp templates/activities-template.yaml curriculum/l2-uk-en/b1/XX-new-module.activities.yaml`
2. Edit in VS Code (schema autocomplete enabled)
3. Validate: `npm run validate:yaml l2-uk-en b1 XX`
4. Generate: `npm run generate l2-uk-en b1 XX`
5. Audit: `python3 scripts/audit_module.py curriculum/l2-uk-en/b1/XX-*.md`

## Common Mistakes

- Forgetting `explanation` field in error-correction
- Using cloze at A1 level (not allowed)
- Having <8 items in quiz for B1+
- Missing `correct: true` in any option set

## Getting Help

Run validator with verbose output:
`npm run validate:yaml l2-uk-en b1 53 -- --verbose`
```

---

## Activity Order & Pedagogy

### Is Activity Order Significant?

**Answer:** Yes, but loosely.

**Pedagogical pattern (recommended, not enforced):**

| Order | Activity Type | Purpose |
|-------|---------------|---------|
| 1-2 | Recognition (quiz, true-false) | Check comprehension |
| 3-4 | Matching (match-up, group-sort) | Build associations |
| 5-6 | Production (fill-in, cloze) | Active recall |
| 7-8 | Synthesis (unjumble, error-correction) | Apply rules |
| 9-10 | Integration (translate) | Real-world use |
| 11-12 | Challenge (mark-the-words, select) | Advanced practice |

**Implementation:**
- YAML preserves array order (activities render in file order)
- No schema enforcement (order is guideline, not rule)
- Document recommended order in contributor guide

### Activity Order Validation (Optional)

```python
# Future enhancement: warn if order seems pedagogically backwards
PREFERRED_ORDER = {
    'quiz': 1, 'true-false': 1,
    'match-up': 2, 'group-sort': 2,
    'fill-in': 3, 'cloze': 3,
    'unjumble': 4, 'error-correction': 4,
    'translate': 5,
    'mark-the-words': 6, 'select': 6
}

def warn_activity_order(activities):
    """Warn if recognition activities come after production activities."""
    # Implementation: optional warning, not error
```

---

## Cross-Reference Validation

### Problem: Activities Use Vocabulary Not in Module

Activities may use words that aren't in the module's vocabulary section.

### Validation Rule

```python
def validate_vocabulary_usage(yaml_activities, md_vocabulary_section):
    """Check that activity content uses module vocabulary."""
    module_vocab = extract_vocab_words(md_vocabulary_section)
    activity_vocab = extract_vocab_from_activities(yaml_activities)

    # Ukrainian words in activities should be in vocabulary
    unknown_words = activity_vocab - module_vocab - COMMON_WORDS

    if unknown_words:
        return Warning(f"Activities use words not in vocabulary: {unknown_words}")
```

### What to Validate

| Check | Severity | Implementation |
|-------|----------|----------------|
| Activity answers in vocab | Warning | Extract from fill-in, cloze answers |
| Quiz options in vocab | Info | May include distractors |
| Match-up pairs in vocab | Warning | Both left and right sides |
| Group-sort items in vocab | Warning | All items |

### Common Words Exception

Some words are so common they don't need to be in vocabulary:

```python
COMMON_WORDS = {
    # Pronouns
    'я', 'ти', 'він', 'вона', 'воно', 'ми', 'ви', 'вони',
    # Articles/particles
    'і', 'та', 'а', 'але', 'що', 'як', 'де', 'коли',
    # Common verbs
    'є', 'бути', 'мати', 'робити',
    # Numbers
    'один', 'два', 'три', ...
}
```

### Implementation Phase

Add to Phase 1.5 (Dry Run) as optional warning, not blocking error.

---

## Content Quality Validation

### Beyond Structure: Semantic Correctness

YAML schema validates structure but NOT:
- Is the "correct" answer actually correct?
- Are explanations accurate?
- Is Ukrainian grammar correct in sentences?

### What Schema CAN Validate

| Check | Schema Can Validate? |
|-------|---------------------|
| Required fields present | ✓ Yes |
| Minimum item counts | ✓ Yes |
| Exactly one correct answer (quiz) | ✓ Yes |
| Answer in options list | ✓ Yes |
| Field types (string, array, boolean) | ✓ Yes |

### What Schema CANNOT Validate

| Check | Solution |
|-------|----------|
| Answer is linguistically correct | LLM review / human review |
| Explanation matches answer | LLM review / human review |
| Ukrainian grammar is correct | Grammar check skill |
| Difficulty is appropriate for level | Human review |
| No duplicate questions | Custom validator |

### Hybrid Approach

```
YAML ──▶ Schema Validator ──▶ Custom Validator ──▶ [Optional] LLM Review
              │                      │                      │
         Structure OK          Logic OK              Content OK
```

**Custom validator checks:**
- No duplicate questions within activity
- Answer appears in options (fill-in)
- Error word appears in sentence (error-correction)
- Blank count matches blank definitions (cloze)

**LLM review (optional, expensive):**
- Grammar correctness
- Answer accuracy
- Explanation quality

### Implementation

```python
# scripts/validate_yaml.py

def validate_activity_file(yaml_path, level):
    activities = load_yaml(yaml_path)

    # Stage 1: Schema validation (fast, always run)
    schema_result = validate_schema(activities, level)
    if not schema_result.ok:
        return schema_result

    # Stage 2: Logic validation (fast, always run)
    logic_result = validate_logic(activities)
    if not logic_result.ok:
        return logic_result

    # Stage 3: Cross-reference validation (medium, always run)
    xref_result = validate_cross_references(activities, module_vocab)

    # Stage 4: LLM review (slow, optional)
    if os.environ.get('VALIDATE_WITH_LLM'):
        llm_result = validate_with_llm(activities)
        return combine_results(schema_result, logic_result, xref_result, llm_result)

    return combine_results(schema_result, logic_result, xref_result)
```

---

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Severity | Mitigation |
|------|------------|--------|----------|------------|
| Schema incomplete | Certain | Medium | **High** | Complete all 13 types before Phase 2 |
| Conversion data loss | Possible | High | **High** | Pre-conversion audit + manual review |
| Level constraints wrong | Likely | Medium | **Medium** | Test fixtures per level |
| Generator output differs | Likely | Medium | **Medium** | Regression tests |
| No rollback plan | N/A | High | **High** | Git branches + backup strategy |
| CI not integrated | Certain | Low | **Low** | Add in Phase 1 |
| Poor error messages | Likely | Low | **Low** | Custom formatter |
| IDE setup missing | Certain | Low | **Low** | VS Code settings + docs |
| Activities use unknown vocab | Likely | Low | **Low** | Cross-reference validation |
| Answers semantically wrong | Possible | Medium | **Medium** | Optional LLM review |
| Activity order suboptimal | Likely | Low | **Info** | Order validation (warning only) |

### Severity Definitions

- **High:** Blocks migration or causes data loss
- **Medium:** Causes rework or delays
- **Low:** Inconvenience, workaround exists

### Mitigation Status

| Risk | Mitigation | Status |
|------|------------|--------|
| Schema incomplete | Add to Phase 1 requirements | ✓ Planned |
| Conversion data loss | Pre-audit + manual queue | ✓ Planned |
| Level constraints wrong | Level-specific schemas | ✓ Planned |
| Generator output differs | Regression tests | ✓ Planned |
| No rollback plan | Document procedure | ✓ Documented |
| CI not integrated | GitHub Actions | ✓ Planned |
| Poor error messages | Custom formatter | ✓ Planned |
| IDE setup missing | VS Code settings | ✓ Documented |
| Activities use unknown vocab | Cross-reference validator | ✓ Planned |
| Answers semantically wrong | Optional LLM review | ✓ Planned |
| Activity order suboptimal | Order validation | ✓ Documented |

---

## Benefits Summary

| Aspect | Current MD | Proposed YAML |
|--------|------------|---------------|
| **Validation** | At audit time | Before creation |
| **Syntax** | Ambiguous | Explicit |
| **Errors** | Runtime | Compile-time |
| **IDE Support** | Minimal | Full (linting, autocomplete) |
| **Learnability** | Template reference | Schema enforcement |
| **Debugging** | Parse error messages | Field-level errors |

---

## Updated Migration Timeline

### Phase 0: Prerequisites (Before Starting)

- [ ] All B1 modules pass audit (current state)
- [ ] Git branch: `yaml-migration/main`
- [ ] Backup: `curriculum-backup-pre-yaml/`

### Phase 1: Infrastructure (Week 1-2)

- [ ] Create `schemas/activities-base.schema.json` with all 13 types
- [ ] Create level-specific schemas (a1, a2, b1)
- [ ] Create `scripts/yaml_activities.py` (shared parser)
- [ ] Create `scripts/validate_yaml.py` (validator CLI)
- [ ] Create `scripts/convert_md_to_yaml.py` (converter)
- [ ] Add `npm run validate:yaml` command
- [ ] Add `npm run convert:yaml` command
- [ ] Create test fixtures (`tests/fixtures/yaml/`)
- [ ] Write unit tests (`tests/test_yaml_parser.py`)
- [ ] Setup VS Code workspace settings
- [ ] Setup pre-commit hook
- [ ] Setup GitHub Actions workflow

### Phase 1.5: Dry Run (Week 2-3) — NEW

- [ ] Convert ALL B1 modules to YAML (keep MD activities)
- [ ] Run regression tests: compare MD vs YAML output
- [ ] Document all edge cases found
- [ ] Fix converter issues
- [ ] Verify 100% output equivalence
- [ ] **Decision gate:** Proceed only if equivalence confirmed

### Phase 2: B2 Pilot (Week 3-4)

- [ ] Create 5 NEW B2 modules with YAML activities (not converted)
- [ ] Test full pipeline (validate → generate → audit)
- [ ] Iterate on schema based on issues found
- [ ] Document learnings
- [ ] **Decision gate:** Continue or rollback

### Phase 3: B1 Migration (Week 5)

- [ ] Remove MD activities from B1 modules (YAML now source of truth)
- [ ] Verify all modules pass audit
- [ ] Run full pipeline for all B1 modules

### Phase 4: A1/A2 Migration (Week 6)

- [ ] Convert A1 modules (handle anagram type)
- [ ] Convert A2 modules
- [ ] Verify all modules pass audit

### Phase 5: Cleanup (Week 7)

- [ ] Remove MD activity parsing from generator (optional)
- [ ] Update all documentation (see checklist)
- [ ] Update all templates
- [ ] Update CLAUDE.md
- [ ] Archive old markdown reference

### Phase 6: Stabilization (Week 8+)

- [ ] Monitor for issues
- [ ] Gather contributor feedback
- [ ] Refine error messages
- [ ] Consider vocabulary YAML (optional)

---

## Decision Gates

### Gate 1: After Phase 1.5 (Dry Run)

**Question:** Does YAML produce identical output to MD?

| Result | Action |
|--------|--------|
| 100% equivalent | Proceed to Phase 2 |
| >95% equivalent | Fix issues, re-test |
| <95% equivalent | Investigate root cause, possibly redesign |

### Gate 2: After Phase 2 (B2 Pilot)

**Question:** Is YAML workflow sustainable for new module creation?

| Result | Action |
|--------|--------|
| Smooth workflow | Proceed to Phase 3 |
| Minor issues | Fix and continue |
| Major friction | Rollback, gather feedback, redesign |

---

## Example: Complete Module

### `53-abstract-concepts-processes.md`

```markdown
---
module: b1-053
title: "Абстрактні концепції: процеси та зміни"
phase: "B1.5-6"
pedagogy: "PPP"
# ... other frontmatter
---

# Абстрактні концепції: процеси та зміни

## Вступ

[Introduction content...]

## Лексика

[Vocabulary presentation...]

## Використання

[Grammar explanations...]

## Читання

[Reading passage...]

## Діалоги

[Dialogue content...]

## Вправи

<!-- Activities loaded from 53-abstract-concepts-processes.activities.yaml -->

## Підсумок

[Summary...]

# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| зростання | growth | process noun |
| ... | ... | ... |
```

### `53-abstract-concepts-processes.activities.yaml`

```yaml
# Module: B1-053 Abstract Concepts: Processes and Changes
# Activities: 12 total

- type: quiz
  title: "Вибір правильного слова"
  items:
    - question: "Яке слово означає 'зміна на краще'?"
      options:
        - text: "погіршення"
          correct: false
        - text: "покращення"
          correct: true
        - text: "сповільнення"
          correct: false
        - text: "зупинка"
          correct: false
      explanation: "Покращення — зміна на краще."
    # ... 7 more items (min 8 for quiz)

- type: match-up
  title: "Антоніми"
  pairs:
    - left: "зростання"
      right: "падіння"
    - left: "покращення"
      right: "погіршення"
    # ... more pairs (min 8 for B1)

- type: fill-in
  title: "Колокації з дієсловами"
  items:
    - sentence: "Економіка демонструє ознаки ___."
      answer: "відновлення"
      options: ["відновлення", "відновлювати", "відновити", "відновлений"]
    # ... more items (min 8 for B1)

# ... 9 more activities (12 total for B1)
```

---

## Documentation Updates Required

When YAML migration is complete, the following documents need updating:

### 1. CLAUDE.md (Project Instructions)

**Location:** `/CLAUDE.md`

**Changes:**
- Update "Activity & Content Requirements" section to reference YAML format
- Update "Activity Format Requirements (CRITICAL)" to show YAML instead of MD
- Add new command: `npm run validate:yaml`
- Update module writing workflow to include YAML activities step
- Remove/deprecate markdown activity syntax examples

**Example update:**
```markdown
## Activity Format Requirements

Activities are defined in YAML files: `{num}-{slug}.activities.yaml`

Validation: `npm run validate:yaml l2-uk-en b1 53`

See `docs/l2-uk-en/YAML-ACTIVITY-MIGRATION-PLAN.md` for schemas.
```

### 2. MODULE-RICHNESS-GUIDELINES-v2.md

**Location:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`

**Changes:**
- Activity counts stay the same (these are content requirements, not format)
- Add note that activities are now in YAML format
- Link to YAML schema for format details
- Remove markdown syntax examples (if any)

**No changes needed for:**
- Minimum item counts per activity type
- Activity type availability matrix by level
- Richness scoring formula
- Engagement box requirements

### 3. Curriculum Plans

**Location:** `docs/l2-uk-en/*-CURRICULUM-PLAN.md`

**Changes:** Minimal - these define *what* content, not *how* it's formatted
- No syntax changes needed
- Activity requirements stay the same
- Vocabulary lists stay the same

### 4. Module Templates (28 templates)

**Location:** `docs/l2-uk-en/templates/*.md`

**Changes:** Replace markdown activity examples with YAML
- Remove "Activity Format Quick Reference" tables (no longer needed)
- Add note: "Activities defined in separate .activities.yaml file"
- Optionally include YAML schema reference

**Templates to update:**
```
docs/l2-uk-en/templates/
├── a1-module-template.md
├── a2-module-template.md
├── b1-grammar-module-template.md
├── b1-vocab-module-template.md
├── b1-cultural-module-template.md
├── b1-checkpoint-module-template.md
├── b1-integration-module-template.md
├── b2-grammar-module-template.md
├── b2-history-module-template.md
├── b2-phraseology-module-template.md
├── b2-checkpoint-module-template.md
├── b2-integration-module-template.md
├── c1-literature-module-template.md
├── c1-biography-module-template.md
├── c1-folk-culture-module-template.md
├── c1-academic-module-template.md
├── c1-sociolinguistics-module-template.md
├── c1-checkpoint-module-template.md
├── c2-style-module-template.md
├── c2-literary-module-template.md
├── c2-professional-module-template.md
├── c2-meta-skills-module-template.md
├── c2-checkpoint-module-template.md
└── lit-module-template.md
```

### 5. ACTIVITY-MARKDOWN-REFERENCE.md

**Location:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

**Options:**
1. **Deprecate:** Add banner "DEPRECATED - Activities now use YAML format"
2. **Archive:** Move to `docs/archive/ACTIVITY-MARKDOWN-REFERENCE-LEGACY.md`
3. **Replace:** Rewrite as `docs/ACTIVITY-YAML-REFERENCE.md`

**Recommended:** Option 3 - create new YAML reference

### 6. Quick Reference Files

**Location:** `.claude/quick-ref/*.md`

**Changes:**
- Update activity syntax examples to YAML
- Add `npm run validate:yaml` command
- Reference YAML schema

**Files:**
```
.claude/quick-ref/
├── a1.md
├── a2.md
├── b1.md
├── b2.md
├── c1.md
└── c2.md
```

### 7. Stage Files (Module Creation Workflow)

**Location:** `.claude/stages/*.md`

**Changes:**
- Stage 3 (Activities): Update to create YAML file instead of MD activities
- Stage 4 (Review): Add YAML validation step before audit

**Files:**
```
.claude/stages/
├── stage-1-skeleton.md      # No change (prose structure)
├── stage-2-content.md       # No change (prose content)
├── stage-3-activities.md    # UPDATE: Create .activities.yaml
└── stage-4-review-fix.md    # UPDATE: Add validate:yaml step
```

### 8. Audit Script Configuration

**Location:** `scripts/audit/config.py`

**Changes:**
- Add YAML activity file detection
- Update activity parsing to read from YAML
- Keep all validation rules (counts, types, etc.)

### 9. Skills (Claude Agent Skills)

**Location:** `.claude/skills/*/SKILL.md`

**Changes:**
- `grammar-module-architect` - Update activity creation guidance
- `vocab-module-architect` - Update activity creation guidance
- `cultural-module-architect` - Update activity creation guidance
- etc.

---

## Documentation Update Checklist

Use this checklist during Phase 5 (Cleanup):

### Core Documentation

- [ ] `CLAUDE.md` - Activity format section updated
- [ ] `docs/ACTIVITY-MARKDOWN-REFERENCE.md` - Deprecated or replaced
- [ ] `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Format note added

### Templates (28 total)

- [ ] A1 template updated
- [ ] A2 template updated
- [ ] B1 templates updated (5)
- [ ] B2 templates updated (5)
- [ ] C1 templates updated (6)
- [ ] C2 templates updated (5)
- [ ] LIT template updated

### Workflow Documentation

- [ ] `.claude/quick-ref/*.md` - All 6 files updated
- [ ] `.claude/stages/stage-3-activities.md` - YAML creation
- [ ] `.claude/stages/stage-4-review-fix.md` - YAML validation

### Skills

- [ ] All architect skills updated with YAML guidance

### Scripts

- [ ] `scripts/audit/config.py` - YAML support added
- [ ] `scripts/generate_mdx.py` - YAML reading added
- [ ] `scripts/validate_yaml.py` - Created

---

## Related Documentation

- `docs/ACTIVITY-MARKDOWN-REFERENCE.md` - Current markdown syntax (to be deprecated)
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Activity counts and requirements
- `schemas/activities.schema.json` - JSON Schema for validation (to be created)

---

**Last Updated:** 2025-12-26
**Plan Version:** 2.0
**Status:** Planning - comprehensive plan ready for Epic/Issue creation
