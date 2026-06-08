# Error-Correction Activity - Extended Format

**Status**: ✅ Implemented (Issue #442)
**Schema Version**: 2.0 (backward compatible)
**Applies To**: All levels (A1-C2, all tracks)

---

## Overview

The `error-correction` activity type has been extended to support **multi-word corrections** while maintaining 100% backward compatibility with existing single-word activities.

**Key Enhancement**: Optional `error_type` field enables phrase corrections, register transformations, and complex grammatical constructions.

---

## Error Types

| Type | Use Case | Example |
|------|----------|---------|
| `word` | Single-word grammatical corrections (default) | кожний → кожного |
| `phrase` | Multi-word phrase corrections | Привіт, Іване → Шановний Іване |
| `register` | Style/register transformations | Дай мені знати → Будь ласка, повідомте мене |
| `construction` | Grammatical construction corrections | Complex sentence structure fixes |

---

## Schema Definition

```yaml
- type: error-correction
  title: string (required)
  instruction: string (optional)
  items: array (required)
    - sentence: string (required)
      error: string (required) - word or phrase
      answer: string (required) - word or phrase
      error_type: enum (optional) - word | phrase | register | construction
      options: array[4] (required)
      explanation: string (required)
```

**Default Behavior**: If `error_type` is omitted, it defaults to `word` (existing behavior).

---

## Usage Examples

### Example 1: Single-Word Correction (Default)

```yaml
- type: error-correction
  title: Виправте граматичні помилки
  instruction: Оберіть правильну форму слова.
  items:
    - sentence: Я їду до Київа кожний день.
      error: кожний
      answer: кожного
      options:
        - кожний
        - кожного
        - кожному
        - кожним
      explanation: Після прийменника "до" використовується родовий відмінок.
```

**Note**: No `error_type` field needed - defaults to `word`.

---

### Example 2: Multi-Word Phrase Correction

```yaml
- type: error-correction
  title: Замініть розмовні фрази на офіційні
  instruction: Оберіть правильний офіційний варіант.
  items:
    - sentence: Привіт, Іване, як справи?
      error: Привіт, Іване
      answer: Шановний Іване
      error_type: phrase
      options:
        - Привіт, Іване
        - Шановний Іване
        - Добрий день, Іване
        - Вітаю, Іване
      explanation: В офіційному листуванні використовується «Шановний + ім'я».

    - sentence: Дякую за листа, буду чекати на відповідь.
      error: буду чекати на
      answer: очікую на
      error_type: phrase
      options:
        - буду чекати на
        - очікую на
        - чекаю на
        - сподіваюся на
      explanation: «Очікую на» — більш офіційний та стислий варіант.
```

---

### Example 3: Register Transformation

```yaml
- type: error-correction
  title: Перетворіть неформальні звертання на офіційні
  instruction: Оберіть офіційний варіант звертання.
  items:
    - sentence: Дай мені знати, коли будеш готовий.
      error: Дай мені знати
      answer: Будь ласка, повідомте мене
      error_type: register
      options:
        - Дай мені знати
        - Будь ласка, повідомте мене
        - Скажи мені
        - Дайте знати
      explanation: Офіційний регістр вимагає ввічливої форми «будь ласка, повідомте».

    - sentence: Можна б зустрітися завтра?
      error: Можна б
      answer: Чи не могли б Ви
      error_type: register
      options:
        - Можна б
        - Чи не могли б Ви
        - Давай
        - Може
      explanation: Офіційне прохання використовує форму «Чи не могли б Ви».
```

---

### Example 4: Grammatical Construction

```yaml
- type: error-correction
  title: Виправте пунктуацію у складних реченнях
  instruction: Оберіть правильний варіант пунктуації.
  items:
    - sentence: Я хотів би щоб ви надіслали документи.
      error: щоб ви надіслали
      answer: щоб, ви надіслали
      error_type: construction
      options:
        - щоб ви надіслали
        - щоб, ви надіслали
        - що ви надіслали
        - аби ви надіслали
      explanation: Підрядне речення мети потребує коми після сполучника «щоб».
```

---

## When to Use Each Type

### Use `word` (or omit error_type) when:
- Correcting case endings
- Fixing verb conjugations
- Correcting single-word grammatical errors
- Teaching declension/conjugation patterns

### Use `phrase` when:
- Replacing informal greetings with formal ones
- Correcting multi-word set expressions
- Teaching collocation patterns
- Fixing idiomatic phrases

### Use `register` when:
- Transforming informal speech to formal writing
- Teaching business communication
- Practicing official correspondence
- Demonstrating style differences

### Use `construction` when:
- Correcting sentence structure
- Teaching complex punctuation
- Fixing word order in multi-word phrases
- Demonstrating grammatical patterns

---

## Best Practices

### 1. Keep Error Location Clear
The `error` field should match the exact text in the sentence to be highlighted.

**Good:**
```yaml
sentence: Привіт, Іване, як справи?
error: Привіт, Іване
```

**Bad:**
```yaml
sentence: Привіт, Іване, як справи?
error: Привіт  # Incomplete - doesn't match sentence text exactly
```

### 2. Include Error in Options
The incorrect form (`error`) should always appear in the `options` array.

**Good:**
```yaml
error: Дай мені знати
options:
  - Дай мені знати        # Error included
  - Будь ласка, повідомте мене
  - Скажи мені
  - Дайте знати
```

### 3. Write Clear Explanations
Explanations should state WHY the error is wrong and WHY the answer is correct.

**Good:**
```yaml
explanation: Офіційний регістр вимагає ввічливої форми «будь ласка, повідомте».
```

**Bad:**
```yaml
explanation: Неправильно.  # Too vague
```

### 4. Maintain Vocabulary Scope
Use only vocabulary from the current module and prior modules.

### 5. Balance Options
Include plausible distractors that test understanding, not just random words.

---

## Pedagogical Use Cases

### B2 Communication Skills Modules (M85-94)
- Professional email register transformations
- Formal vs informal greetings
- Business correspondence phrases

### B2 History/Biography Modules
- Academic writing register
- Historical narrative style
- Formal analysis language

### C1 Cultural/Literary Modules
- Literary register variations
- Complex sentence structures
- Stylistic transformations

---

## Backward Compatibility Guarantee

**All existing error-correction activities continue working without changes.**

- Activities without `error_type` default to `word` behavior
- No schema validation errors for existing activities
- No breaking changes to activity processing
- Zero impact on 1000+ existing activities across all levels

**Migration**: Existing activities can be enhanced by adding `error_type` field if needed, but it's entirely optional.

---

## Implementation Details

**Schema Location**: `schemas/activities-base.schema.json`
**Documentation**: `docs/ACTIVITY-YAML-REFERENCE.md`
**GitHub Issue**: #442
**Related Friction**: [FRICTION-ACT-004] from Issue #441

**Validation**:
```bash
# Validate activity YAML with extended schema
npm run validate:yaml curriculum/l2-uk-en/{level}/activities/{slug}.yaml

# Full module audit (includes extended error-correction)
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{slug}.md
```

---

## Decision Rationale

**Why extend error-correction instead of creating a new activity type?**

1. **Conceptual Unity**: All variants involve finding/fixing errors in context
2. **Backward Compatibility**: No impact on existing activities
3. **Pedagogical Clarity**: Same interaction pattern for learners
4. **Maintainability**: One activity type to document/support
5. **Extensibility**: Can add more error types in future if needed

**Alternative Considered**: Create separate activity types (phrase-correction, register-correction)
**Rejected Because**: Would fragment conceptually related activities and increase maintenance burden.

---

## Memory/Context for LLMs

**When generating activities for B2+ modules:**

1. **Check module focus**: If focus is "skills" or "communication", consider using error-correction with `phrase` or `register` types
2. **Prefer error-correction over quiz**: When the pedagogical goal is identifying specific errors in context
3. **Use appropriate error_type**: Match the learning objective (grammar → word, communication → phrase/register)
4. **Include in activity mix**: Error-correction counts toward unique activity types

**When reviewing/auditing modules:**
- Accept both single-word and multi-word error-correction activities
- Validate that error_type matches the actual correction being made
- Ensure vocabulary is from allowed scope (current + prior modules)

---

**Last Updated**: 2026-01-20 (B2 M85 completion session)
