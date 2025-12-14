# Module Creation Prompt

This document provides instructions for AI agents writing Ukrainian curriculum modules.

---

## Critical Reading Requirements

<critical>
**EVERY time you write or rewrite a module:**

1. **READ `docs/MARKDOWN-FORMAT.md`** - The authoritative source for all activity syntax
2. **READ `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`** - Extract the EXACT vocabulary list and grammar scope
3. **READ `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`** - Activity counts, sentence complexity, engagement boxes

**DO NOT:**
- Write from memory
- Add vocabulary not in the curriculum plan
- Skip reading the format specification
- Use old or deprecated activity syntax

**The prompts exist because you forget. Read them every time.**
</critical>

---

## Activity Format Specification

### Authoritative Source

**`docs/MARKDOWN-FORMAT.md`** is the single source of truth for activity syntax.

All activities use **pure markdown** (NOT YAML). The audit will fail if you use incorrect syntax.

### CRITICAL Format Requirements

1. **Quiz items**: Use numbered lists `1.`, NOT bullets `-`
2. **Answers**: Use `> [!answer]` callout blocks, NOT inline `→` arrows
3. **True-false**: Use `- [x]` for true, `- [ ]` for false. NO "— TRUE/FALSE" suffix in text
4. **Unjumble**: Use `> [!answer]` for correct sentence, NOT nested `- answer`
5. **Fill-in**: Use `> [!answer]` AND `> [!options]` blocks, BOTH required
6. **Match-up**: Use markdown table with `| Left | Right |` headers
7. **Group-sort**: Use `### Category Name` headers with bullet lists

### Common Format Mistakes

#### WRONG: Quiz with bullets
```markdown
## quiz: Title

- What does "привіт" mean?
  - [x] hello
  - [ ] goodbye
```

#### CORRECT: Quiz with numbers
```markdown
## quiz: Title

1. What does "привіт" mean?
   - [x] hello
   - [ ] goodbye
```

---

#### WRONG: True-false with suffix
```markdown
## true-false: Title

- [x] Ukrainian has 7 cases. — TRUE
- [ ] All nouns are masculine. — FALSE
```

#### CORRECT: True-false clean
```markdown
## true-false: Title

- [x] Ukrainian has 7 grammatical cases.
  > Correct! Nominative, Genitive, Dative, Accusative, Instrumental, Locative, Vocative.

- [ ] All Ukrainian nouns are masculine.
  > Incorrect! Ukrainian has three genders: masculine, feminine, and neuter.
```

---

#### WRONG: Unjumble with nested list
```markdown
## unjumble: Title

- книгу / читаю / Я
  - answer: Я читаю книгу.
```

#### CORRECT: Unjumble with callout
```markdown
## unjumble: Title

1. книгу / читаю / Я
   > [!answer] Я читаю книгу.
   > (I read a book.) [3 words]
```

---

#### WRONG: Fill-in missing blocks
```markdown
## fill-in: Title

1. Я ___ книгу. (читаю)
```

#### CORRECT: Fill-in with both blocks
```markdown
## fill-in: Title

1. Я ___ книгу. (read)
   > [!answer] читаю
   > [!options] читаю | читаєш | читає | читають
```

---

### Activity Reference Files

- **`docs/MARKDOWN-FORMAT.md`** - Full specification (sections 240-610)
- **`docs/ACTIVITY-MARKDOWN-REFERENCE.md`** - Pattern examples for all 13 activity types

---

## Vocabulary Requirements

### Source of Truth

Extract vocabulary from the curriculum plan:
```bash
grep -A 50 "Module {NUM}:" docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md
```

### Rules

1. **Use ONLY** vocabulary from:
   - Current module's vocabulary section
   - Prior modules (cumulative)
   - Common function words (я, ти, він, це, і, а, але)

2. **NEVER** add vocabulary not in the curriculum plan
3. **NEVER** use words the learner hasn't seen yet

---

## Content Requirements

### Word Count Targets (Instructional Core)

| Level | Range | Target |
|-------|-------|--------|
| A1 | M01-05 | 300+ |
| A1 | M06-10 | 500+ |
| A1 | M11+ | 750+ |
| A2 | all | 1000+ |
| B1 | all | 1250+ |
| B2 | all | 1500+ |
| C1 | all | 1750+ |
| C2 | all | 2000+ |

### Required Elements

| Level | Example Sentences | Engagement Boxes | Mini-Dialogues |
|-------|------------------|------------------|----------------|
| A1 | 12+ | 3+ | 2-3+ |
| A2 | 18+ | 4+ | 2-3+ |
| B1 | 24+ | 5+ | 4+ |
| B2 | 28+ | 6+ | 4+ |
| C1 | 30+ | 7+ | 5+ |
| C2 | 32+ | 8+ | 5+ |

### Engagement Box Types

- `> [!tip]` - Did You Know
- `> [!example]` - Pop Culture Moment
- `> [!info]` - Real World Usage
- `> [!warning]` - Common Mistake

---

## Activity Requirements

See `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` for the complete activity matrix.

### Activity Counts

| Level | Activities | Items per Activity | Activity Types |
|-------|-----------|-------------------|----------------|
| A1 | 8+ | 12+ | 4+ |
| A2 | 10+ | 12+ | 5+ |
| B1 | 12+ | 14+ | 5+ |
| B2 | 14+ | 16+ | 5+ |
| C1 | 16+ | 18+ | 5+ |
| C2 | 16+ | 18+ | 5+ |

### Core Activity Types (All Levels)

- `quiz` - Multiple choice (single answer)
- `match-up` - Match pairs (Ukrainian ↔ English)
- `fill-in` - Gap fill with dropdown options
- `true-false` - Statement validation
- `group-sort` - Sort items into categories
- `unjumble` - Reorder words into sentence

### A1-Only Activity

- `anagram` - Letter unscrambling (M01-10 only, phased out by M21+)

### A2+ Activities

- `error-correction` - Find and fix errors
- `cloze` - Passage completion with multiple blanks
- `mark-the-words` - Click words matching criteria
- `dialogue-reorder` - Put conversation lines in order
- `select` - Multi-checkbox (multiple correct answers)
- `translate` - Translation multiple choice

---

## Pre-Submission Checklist

Before delivering a module, verify:

### Format Compliance
- [ ] Quiz items use numbered lists `1.`, not bullets `-`
- [ ] All answers use `> [!answer]` callout blocks
- [ ] True-false items have NO "— TRUE/FALSE" suffix
- [ ] Fill-in activities include BOTH `> [!answer]` AND `> [!options]`
- [ ] Unjumble uses `> [!answer]` not nested lists
- [ ] Match-up uses markdown table format
- [ ] Group-sort uses `### Category` headers

### Vocabulary Compliance
- [ ] ALL vocabulary from curriculum plan is in vocabulary section
- [ ] NO vocabulary added that's not in the curriculum plan
- [ ] Activities use ONLY vocabulary from table or prior modules

### Content Requirements
- [ ] Word count meets level target
- [ ] Example sentences meet minimum count
- [ ] Engagement boxes meet minimum count
- [ ] Mini-dialogues present

### Activity Requirements
- [ ] Activity count meets level minimum
- [ ] Items per activity meets level minimum
- [ ] Activity type variety meets minimum
- [ ] All activity answers are correct

---

## Audit Validation

The audit (`npx ts-node scripts/module-audit.ts`) checks:

1. **Format compliance** - Markdown syntax matches MARKDOWN-FORMAT.md
2. **Activity counts** - Meets MODULE-RICHNESS-GUIDELINES-v2.md targets
3. **Vocabulary coverage** - All plan words present, no extras
4. **Answer correctness** - All activity solutions valid

**If the audit fails, you MUST fix the violations before completing.**

---

## Grammar and Pedagogy

### Grammar Constraints

See curriculum plan for module-specific grammar scope. NEVER introduce grammar not listed in the plan.

### Pedagogical Patterns

- **PPP (Presentation-Practice-Production)**: Most common for grammar modules
- **TTT (Test-Teach-Test)**: For diagnostic/discovery modules
- **Narrative Arc**: For immersive vocabulary modules (B1+)

### Observe-First Pattern (B1-B2)

Use `> [!observe]` callout for inductive pattern discovery BEFORE explaining rules:

```markdown
> [!observe]
> Я **читаю** книгу.
> Ти **читаєш** книгу.
> Він **читає** книгу.
>
> 🔎 What do you notice about the verb endings?
```

**Key points:**
- Place inline in lesson content (NOT in Activities section)
- Show 3-4 example sentences with **bold** highlighting
- End with discovery prompt (🔎 question)
- Follow immediately with explicit grammar explanation

---

## Level-Specific Notes

### A1 (Modules 1-34)

- **Transliteration**:
  - M01-10: Full transliteration `Слово (Slovo)`
  - M11-20: Vocab lists only
  - M21-34: First occurrence only
- **Anagram**: Allowed M01-10, reduce M11-20, avoid M21+
- **Vocabulary**: English header, 6 columns (Word, IPA, English, POS, Gender, Note)

### A2 (Modules 1-50)

- **No transliteration** (starts module 31+ overall)
- **New activities**: error-correction, cloze, mark-the-words, dialogue-reorder
- **Vocabulary**: Same 6-column format as A1

### B1 (Modules 1-80)

- **Vocabulary**: Ukrainian header `# Словник`, 5 columns (Слово, Вимова, Переклад, ЧМ, Примітка)
- **Observe-first**: Required for grammar modules
- **Higher sentence complexity**: 5-8 words in unjumble

### B2-C2

- **Vocabulary**: Minimal 3-column format (Слово, Переклад, Примітки)
- **High immersion**: 70-100% Ukrainian in content
- **Complex activities**: More error-correction, cloze, translate

---

## References

- **Format Spec**: `docs/MARKDOWN-FORMAT.md`
- **Activity Patterns**: `docs/ACTIVITY-MARKDOWN-REFERENCE.md`
- **Richness Guidelines**: `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- **Curriculum Plans**: `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`
- **Architecture**: `docs/ARCHITECTURE.md`
