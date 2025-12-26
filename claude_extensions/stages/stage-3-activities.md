# Stage 3: Activities (YAML-First)

Generate activities in YAML format, separate from the prose content.

## Output Files

For each module, create:
```
curriculum/l2-uk-en/{level}/
├── {num}-{slug}.md                    # Prose only (no activities)
└── {num}-{slug}.activities.yaml       # All activities in YAML
```

## Migrating Existing Embedded Activities

**If `.md` has embedded activities, migrate them to YAML:**

| Old Format | Extract | Put in YAML |
|------------|---------|-------------|
| `## quiz:` questions | Keep exact questions + options | `items[].question`, `items[].options` |
| `## match-up:` table rows | Keep all pairs | `pairs[].left`, `pairs[].right` |
| `## fill-in:` sentences | Keep sentences + answers | `items[].sentence`, `items[].answer` |
| `## true-false:` statements | Keep statements + T/F | `items[].statement`, `items[].correct` |
| `## group-sort:` categories | Keep groups + items | `groups[].name`, `groups[].items` |
| `## unjumble:` scrambled | Keep scrambled + answer | `items[].scrambled`, `items[].answer` |
| `## cloze:` passage | Keep passage, reformat blanks | `passage` with `{ans\|opt1\|opt2}` |
| `## error-correction:` | Keep sentence + error + fix | `items[].sentence/error/answer` |
| `## mark-the-words:` | Keep text + targets | `text` with `*marked*` words |
| `## dialogue-reorder:` | Keep lines + speakers | `lines[].order/speaker/text` |
| `## select:` questions | Keep questions + all options | `items[].question`, `items[].options` |
| `## translate:` sentences | Keep source + options | `items[].source`, `items[].options` |

**Then:**
1. Add missing explanations (required for quiz, error-correction)
2. Add items if below minimum count
3. Add activity types if below level variety requirement
4. Delete embedded activities from `.md` after YAML created

## Activity Count Requirements

| Level | Count | Items per Activity | Types |
|-------|-------|-------------------|-------|
| A1 | 8+ | 12+ | 4+ |
| A2 | 10+ | 12+ | 5+ |
| B1 | 12+ | 14+ | 5+ |
| B2 | 14+ | 16+ | 5+ |
| C1 | 16+ | 18+ | 5+ |
| C2 | 16+ | 18+ | 5+ |

## Activity Matrix by Level

| Activity | A1 | A2 | B1 | B2 | C1 | C2 |
|----------|----|----|----|----|----|----|
| fill-in | 2+ | 2+ | 2+ | 3+ | 2+ | 2+ |
| match-up | 2+ | 1+ | 1+ | 1+ | 1+ | 1+ |
| quiz | 1+ | 1+ | 1+ | 1+ | 1+ | 1+ |
| true-false | 1+ | 1+ | 1+ | 1+ | - | - |
| group-sort | 1+ | 1+ | 1+ | 1+ | 1+ | 1+ |
| anagram | 2+ (M01-10) | - | - | - | - | - |
| unjumble | 2+ (M11+) | 2+ | 2+ | 2+ | 2+ | 2+ |
| error-correction | - | 1+ | 2+ | 2+ | 3+ | 3+ |
| cloze | - | 1+ | 1+ | 1+ | 3+ | 3+ |
| mark-the-words | - | 1+ | 1+ | 1+ | - | - |
| dialogue-reorder | - | 1+ | 1+ | 1+ | 1+ | - |
| select | - | opt | 1+ | 1+ | 1+ | 1+ |
| translate | - | opt | 1+ | 1+ | 2+ | 2+ |

## YAML Format Reference

> [!IMPORTANT]
> See `docs/ACTIVITY-MARKDOWN-REFERENCE.md` for complete format with examples.

### Common Activity Structures

```yaml
# Quiz (8+ items for B1)
- type: quiz
  title: Quiz title
  items:
    - question: Question text?
      options:
        - text: Wrong answer
          correct: false
        - text: Correct answer
          correct: true
        - text: Wrong answer
          correct: false
        - text: Wrong answer
          correct: false
      explanation: Optional explanation.

# Match-up (12+ pairs for B1)
- type: match-up
  title: Match title
  pairs:
    - left: Ukrainian term
      right: English translation
    - left: Another term
      right: Its translation

# Fill-in (12+ items for B1)
- type: fill-in
  title: Fill-in title
  items:
    - sentence: Sentence with _____ blank.
      answer: correct
      options:
        - wrong1
        - correct
        - wrong2
        - wrong3

# True-false (12+ items for B1)
- type: true-false
  title: True/False title
  items:
    - statement: Statement text.
      correct: true
      explanation: Why true/false.

# Group-sort (16+ total items for B1)
- type: group-sort
  title: Sorting title
  groups:
    - name: Category A
      items:
        - item1
        - item2
    - name: Category B
      items:
        - item3
        - item4

# Unjumble (8+ items for B1)
- type: unjumble
  title: Unjumble title
  items:
    - scrambled: words / in / disorder
      answer: Words in correct order.

# Cloze (14+ blanks for B1)
- type: cloze
  title: Cloze title
  passage: |
    Text with {blank1|opt1|opt2|answer} and more {blank2|opt1|answer|opt3} blanks.

# Error-correction (8+ items for B1)
- type: error-correction
  title: Error correction title
  items:
    - sentence: Sentence with error.
      error: wrong_word
      answer: correct_word
      options:
        - wrong_word
        - correct_word
        - distractor1
        - distractor2
      explanation: Why it's wrong.

# Mark-the-words (6+ correct for B1)
- type: mark-the-words
  title: Mark words title
  instruction: Click all nouns.
  text: Regular word *target* regular *target* word.

# Dialogue-reorder (6+ lines for B1)
- type: dialogue-reorder
  title: Dialogue title
  lines:
    - order: 1
      speaker: Олександр
      text: First line.
    - order: 2
      speaker: Наталія
      text: Second line.

# Select (8+ items for B1)
- type: select
  title: Select title
  items:
    - question: Select ALL correct answers.
      options:
        - text: Correct 1
          correct: true
        - text: Correct 2
          correct: true
        - text: Wrong
          correct: false

# Translate (8+ items for B1)
- type: translate
  title: Translate title
  items:
    - source: English sentence.
      options:
        - text: Wrong translation
          correct: false
        - text: Correct translation
          correct: true
        - text: Wrong translation
          correct: false
        - text: Wrong translation
          correct: false
```

## YAML Quoting Rules (CRITICAL)

When a string contains special characters, quote it properly:

1. **Strings with embedded quotes** → wrap in single quotes, double internal quotes:
   ```yaml
   explanation: '"Думка" means opinion.'
   statement: '"Рішення" та "розв''язання" — різні слова.'
   ```

2. **Strings with colons** → wrap in quotes:
   ```yaml
   explanation: 'Правильно: так і ні.'
   ```

3. **Strings with apostrophes** → double the apostrophe inside single quotes:
   ```yaml
   statement: 'Слово "розв''язання" має інше значення.'
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
- [ ] Uses ONLY vocabulary from table + prior modules
- [ ] Strings with quotes/colons properly escaped

## DO NOT

- Embed activities in the markdown file
- Use vocabulary not in table or prior modules
- Write fewer than required activities
- Create activities with fewer than minimum items
- Leave quotes/colons unescaped in YAML strings
