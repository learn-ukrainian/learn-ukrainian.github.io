# Stage 3: Activities (YAML-First)

Generate activities in YAML format, separate from the prose content.

## ⚡ Direct YAML Creation (Recommended)

**For new modules or recreation, write activities directly in YAML:**

1. **Read the module content** (explanation sections) to understand the topic
2. **Study 1-2 similar modules** (see Reference table below) for YAML patterns
3. **Create `.activities.yaml` file** with 12+ activities (B1)
4. **Use the YAML Format Reference** below for correct structure
5. **Run audit** to verify compliance
6. **DO NOT** use md_to_yaml.py converter - write YAML directly!

**Why direct YAML?**

- ✅ **Faster** - No MD→YAML conversion step
- ✅ **No format errors** - Direct control over structure
- ✅ **Better quality** - Explicit syntax, no parsing ambiguity
- ✅ **Proven** - M22 took 8 minutes vs 36 minutes for MD approach

## Reference Existing Modules First

**Before writing activities, study 1-2 similar existing modules:**

| Level | Module Type | Reference Examples | Look For                                   |
| ----- | ----------- | ------------------ | ------------------------------------------ |
| B1    | Grammar     | M06-10 (Aspect)    | Activity variety, sequencing, quiz prompts |
| B1    | Vocabulary  | M52-53             | YAML format, cloze passage structure       |
| A2    | All types   | M01-10             | Activity patterns, engagement integration  |

**Pattern extraction steps:**

1. Read the `.md` file for activity section structure
2. Read the `.activities.yaml` file (if exists) for YAML patterns
3. Note: quiz question length, fill-in sentence structure, error types
4. Adapt patterns to new content (don't copy actual items)

---

## Output Files

For each module, create:

```
curriculum/l2-uk-en/{level}/
├── {num}-{slug}.md                    # Prose only (no activities)
└── {num}-{slug}.activities.yaml       # All activities in YAML
```

## Migrating Existing Embedded Activities

**If MIGRATING an old module that has embedded activities:**

| Old Format                                          | Extract                                 | Put in YAML                               |
| --------------------------------------------------- | --------------------------------------- | ----------------------------------------- |
| `## quiz:` questions                                | Keep exact questions + options          | `items[].question`, `items[].options`     |
| `## match-up:` table rows                           | Keep all pairs                          | `pairs[].left`, `pairs[].right`           |
| `## fill-in:` sentences                             | Keep sentences + answers                | `items[].sentence`, `items[].answer`      |
| `## true-false:` statements                         | Keep statements + T/F                   | `items[].statement`, `items[].correct`    |
| `## group-sort:` categories                         | Keep groups + items                     | `groups[].name`, `groups[].items`         |
| `## unjumble:` scrambled                            | Keep scrambled + answer                 | `items[].scrambled`, `items[].answer`     |
| `## cloze:` passage with `[___:1]` blanks + options | Convert `[___:N]` → `{ans\|opt1\|opt2}` | `passage` with inline `{ans\|opt1\|opt2}` |
| `## error-correction:`                              | Keep sentence + error + fix             | `items[].sentence/error/answer`           |
| `## mark-the-words:`                                | Keep text + targets                     | `text` with `*marked*` words              |
| `## dialogue-reorder:`                              | Keep lines + speakers                   | `lines[].order/speaker/text`              |
| `## select:` questions                              | Keep questions + all options            | `items[].question`, `items[].options`     |
| `## translate:` sentences                           | Keep source + options                   | `items[].source`, `items[].options`       |

**CRITICAL - Cloze Format:**

The MD format for cloze activities MUST use **numbered blanks** with option lists:

```markdown
## cloze: Title

> Instructions

Passage with [___:1] blank and [___:2] another blank.

1. opt1 | opt2 | opt3 | opt4

   > [!answer] correct_answer

2. opt1 | opt2 | opt3 | opt4
   > [!answer] correct_answer
```

**DO NOT use named blanks** like `[___:answer]` - the parser does not support this format.

See `docs/ACTIVITY-MARKDOWN-REFERENCE.md` for complete cloze syntax.

---

**Then:**

1. Add missing explanations (required for quiz, error-correction)
2. Add items if below minimum count
3. Add activity types if below level variety requirement
4. Delete embedded activities from `.md` after YAML created

## Activity Count Requirements (Relaxed)

| Level | Target | WARN | FAIL | Items/Activity | Types |
| ----- | ------ | ---- | ---- | -------------- | ----- |
| A1    | 8+     | <8   | <6   | 12+            | 4+    |
| A2    | 10+    | <10  | <8   | 12+            | 5+    |
| B1    | 12+    | <12  | <8   | 14+            | 5+    |
| B2    | 14+    | <14  | <10  | 16+            | 5+    |
| C1    | 16+    | <16  | <12  | 18+            | 5+    |
| C2    | 16+    | <16  | <12  | 18+            | 5+    |

**WARN** = Passes with warning. **FAIL** = Blocks approval.

## Special Requirements: Content-Heavy Modules

**Content-heavy modules** (B2 History, C1 Literature/Biography/Folk/Arts) have **different requirements**:

| Aspect         | Standard Module | Content-Heavy Module        |
| -------------- | --------------- | --------------------------- |
| Activity Count | 14+ (B2/C1)     | **10-12** (reduced)         |
| Activity Mix   | All types       | **Comprehension-focused**   |
| Quiz Questions | General         | **MUST reference text**     |
| Purpose        | Drill practice  | **Language comprehension**  |

### The Golden Rule for Content-Heavy Modules

<critical>

**"Can the learner answer this without reading the Ukrainian text?"**

- **If YES** → Rewrite (tests content knowledge, not language)
- **If NO** → Keep (tests Ukrainian comprehension)

</critical>

### Activity Mix for Content-Heavy Modules (10-12 total)

| Activity Type        | Count | Key Requirement                                                  |
| -------------------- | ----- | ---------------------------------------------------------------- |
| quiz                 | 4-5   | MUST start with "Згідно з текстом..."                            |
| fill-in / cloze      | 3-4   | Test collocations (чинити спротив, відіграти роль, брати участь) |
| error-correction     | 2-3   | Fix GRAMMAR errors, NOT factual inaccuracies                     |
| match-up             | 1-2   | Ukrainian term ↔ Ukrainian definition                            |
| select / mark-words  | 1-2   | Find grammatical features in text                                |

### Forbidden vs Required Patterns (Quiz Questions)

❌ **FORBIDDEN** (Tests Content Recall):
- "У якому році..." (dates)
- "Хто був..." (names)
- "Скільки..." (numbers)
- "Що символізує..." (interpretation without text reference)

✅ **REQUIRED** (Tests Ukrainian Language):
- "Згідно з текстом, як автор..."
- "У тексті модуля автор характеризує..."
- "Яку функцію автор підкреслює..."
- "Який аргумент автор наводить..."

### Self-Check Before Delivering

For EVERY quiz question in content-heavy modules:

1. Can learner answer without reading Ukrainian module text?
2. If YES → You're testing history/literature. STOP and rewrite.
3. If NO → You're testing Ukrainian. Proceed.

### Applies To

| Level  | Module Range | Focus                     |
| ------ | ------------ | ------------------------- |
| **B2** | M71-131      | History (61 modules)      |
| **C1** | M146-160     | Literature (15 modules)   |
| **C1** | M36-100      | Biography (65 modules)    |
| **C1** | M121-145     | Folk Culture (25 modules) |
| **C1** | Various      | Fine Arts expansion       |

---

## Activity Matrix by Level

| Activity         | A1          | A2  | B1  | B2  | C1  | C2  |
| ---------------- | ----------- | --- | --- | --- | --- | --- |
| fill-in          | 2+          | 2+  | 2+  | 3+  | 2+  | 2+  |
| match-up         | 2+          | 1+  | 1+  | 1+  | 1+  | 1+  |
| quiz             | 1+          | 1+  | 1+  | 1+  | 1+  | 1+  |
| true-false       | 1+          | 1+  | 1+  | 1+  | -   | -   |
| group-sort       | 1+          | 1+  | 1+  | 1+  | 1+  | 1+  |
| anagram          | 2+ (M01-10) | -   | -   | -   | -   | -   |
| unjumble         | 2+ (M11+)   | 2+  | 2+  | 2+  | 2+  | 2+  |
| error-correction | -           | 1+  | 2+  | 2+  | 3+  | 3+  |
| cloze            | -           | 1+  | 1+  | 1+  | 3+  | 3+  |
| mark-the-words   | -           | 1+  | 1+  | 1+  | -   | -   |
| dialogue-reorder | -           | 1+  | 1+  | 1+  | 1+  | -   |
| select           | -           | opt | 1+  | 1+  | 1+  | 1+  |
| translate        | -           | opt | 1+  | 1+  | 2+  | 2+  |

## YAML Format Reference

> [!IMPORTANT]
> See `docs/ACTIVITY-MARKDOWN-REFERENCE.md` for complete format with examples.

### Common Activity Structures

```yaml
# Quiz (8+ items for B1)
- type: quiz
  id: quiz-id
  title: Quiz title
  instructions: Select the correct answer.
  items:
    - prompt: Question text (12-20 words for B1)?
      options:
        - text: Wrong answer
          correct: false
        - text: Correct answer
          correct: true
        - text: Wrong answer
          correct: false
        - text: Wrong answer
          correct: false
      explanation: Why correct/wrong.

# Match-up (12+ pairs for B1)
- type: match-up
  id: match-id
  title: Match title
  instructions: Match the pairs.
  items:
    - left: Ukrainian term
      right: English translation
    - left: Another term
      right: Its translation

# Fill-in (12+ items for B1)
- type: fill-in
  id: fill-id
  title: Fill-in title
  instructions: Choose the correct word.
  items:
    - prompt: Sentence with _____ blank (12-20 words for B1).
      answer: correct
      options:
        - correct
        - wrong1
        - wrong2
        - wrong3

# True-false (12+ items for B1)
- type: true-false
  id: true-false-id
  title: True/False title
  instructions: Determine if the statement is true or false.
  items:
    - statement: Statement text.
      correct: true
      explanation: Why true/false.

# Group-sort (16+ total items, 3-5 categories for B1)
- type: group-sort
  id: group-sort-id
  title: Sorting title
  instructions: Sort items into categories.
  groups:
    - name: Category A
      items:
        - item1
        - item2
    - name: Category B
      items:
        - item3
        - item4
    - name: Category C
      items:
        - item5
        - item6

# Unjumble (6+ items for B1, 12-16 words per sentence)
- type: unjumble
  id: unjumble-id
  title: Unjumble title
  instructions: Put the words in the correct order.
  items:
    - words: слова / у / неправильному / порядку / для / створення / речення / довжиною / дванадцять / або / більше / слів
      answer: Слова у неправильному порядку для створення речення довжиною дванадцять або більше слів.

# Cloze (14+ blanks for B1)
- type: cloze
  id: cloze-id
  title: Cloze title
  instructions: Instructions for cloze.
  passage: 'Text with {answer1} blanks and {answer2} more blanks.'
  blanks:
    - id: 1
      answer: answer1
      options:
        - answer1
        - option1
        - option2
        - option3
    - id: 2
      answer: answer2
      options:
        - answer2
        - option1
        - option2
        - option3

# Error-correction (6+ items for B1)
- type: error-correction
  id: error-id
  title: Error correction title
  instructions: Find and fix the ONE error in each sentence.
  items:
    - sentence: Sentence with error (12-20 words for B1).
      error: wrong_word
      answer: correct_word
      options:
        - wrong_word
        - correct_word
        - distractor1
        - distractor2
      explanation: Why it's wrong.

# Mark-the-words (6+ marked words for B1)
- type: mark-the-words
  id: mark-id
  title: Mark words title
  instructions: Click all target words in the text.
  text: 'Regular word [target] regular [target] word [target] more text.'
  hint: Optional hint about what to mark.

# Dialogue-reorder (4+ lines minimum for B1)
- type: dialogue-reorder
  id: dialogue-id
  title: Dialogue title
  instructions: Put the dialogue lines in the correct order.
  lines:
    - speaker: Олександр
      text: First line.
    - speaker: Наталія
      text: Second line.
    - speaker: Олександр
      text: Third line.
    - speaker: Наталія
      text: Fourth line.

# Select (6+ items for B1)
- type: select
  id: select-id
  title: Select title
  instructions: Select ALL correct answers for each question.
  items:
    - prompt: Question text?
      options:
        - text: Correct 1
          correct: true
        - text: Correct 2
          correct: true
        - text: Wrong
          correct: false
        - text: Wrong 2
          correct: false
      explanation: Why these are correct.

# Translate (6+ items for B1)
- type: translate
  id: translate-id
  title: Translate title
  instructions: Choose the correct Ukrainian translation.
  items:
    - prompt: English sentence.
      options:
        - text: Correct translation
          correct: true
        - text: Wrong translation
          correct: false
        - text: Wrong translation
          correct: false
        - text: Wrong translation
          correct: false
      explanation: Why this translation is correct.
```

## YAML Quoting Rules (CRITICAL)

When a string contains special characters, quote it properly:

1. **Quoted speech in cloze/mark-the-words** → use Ukrainian guillemets `«»`, NOT escaped quotes:

   ```yaml
   # ✅ CORRECT - guillemets work in MDX/JSX
   passage: "Викладач сказав: «{Не забувай} читати щодня!»"
   text: "Він відповів: «Я *не* розумію.»"

   # ❌ WRONG - escaped quotes break MDX compilation
   passage: "Викладач сказав: \"{Не забувай} читати щодня!\""
   ```

   **Why:** Cloze `passage` and mark-the-words `text` become JSX attributes. Escaped `\"` causes "Unexpected character" errors during MDX build.

2. **Strings with embedded quotes (other fields)** → wrap in single quotes, double internal quotes:

   ```yaml
   explanation: '"Думка" means opinion.'
   statement: '"Рішення" та "розв''язання" — різні слова.'
   ```

3. **Strings with colons** → wrap in quotes:

   ```yaml
   explanation: 'Правильно: так і ні.'
   ```

4. **Strings with apostrophes** → double the apostrophe inside single quotes:

   ```yaml
   statement: 'Слово "розв''язання" має інше значення.'
   ```

5. **Numeric option values** → quote as strings:

   ```yaml
   # ✅ CORRECT
   - text: '5'
     correct: false

   # ❌ WRONG - causes 'int' object has no attribute 'replace'
   - text: 5
     correct: false
   ```

## Activity Sequencing

Flow: Easy → Medium → Hard

### A1

```
match-up → group-sort → quiz → true-false → fill-in → anagram/unjumble
```

### A2-B1

```
[recognition] mark-the-words → match-up → group-sort
[discrimination] quiz → true-false → select
[controlled] fill-in → cloze → error-correction
[production] unjumble → dialogue-reorder → translate
```

### B2-C2

```
[discrimination] select (nuanced)
[controlled] fill-in → cloze → error-correction ×2-3
[production] translate → unjumble ×2-3
```

## Vocabulary Constraint (CRITICAL)

Activities MUST use ONLY:

1. Words from the current module's vocabulary table
2. Words from prior modules (cumulative vocabulary)
3. Common function words (я, ти, він, це, і, а, але, etc.)

NEVER use words not taught yet.

## Validation

After writing the YAML file:

```bash
# Validate YAML structure
npm run validate:yaml curriculum/l2-uk-en/{level}/{file}.activities.yaml

# Run module audit
python3 scripts/audit_module.py curriculum/l2-uk-en/{level}/{file}.md
```

## Checklist

- [ ] Created `.activities.yaml` file (NOT embedded in `.md`)
- [ ] Activity count meets level requirement
- [ ] Items per activity meets minimum
- [ ] Activity variety (4-5+ types)
- [ ] Proper sequencing (easy → hard)
- [ ] Valid YAML syntax (run validator)
- [ ] All answers are correct
- [ ] Uses ONLY vocabulary from YAML + prior modules
- [ ] Strings with quotes/colons properly escaped

## DO NOT

- Embed activities in the `.md` file
- Use vocabulary not in YAML or prior modules
- Write fewer than required activities
- Create activities with fewer than minimum items
- Leave quotes/colons unescaped in YAML strings
