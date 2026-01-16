# Stage 3: Activities (YAML-First)

Generate activities in YAML format, separate from the prose content.

> **CRITICAL:** See `docs/ACTIVITY-YAML-REFERENCE.md` for authoritative format reference.

<critical>

## ⚠️ YAML Structure Rules (MUST READ)

### 1. Root MUST Be a Bare List
```yaml
# ✅ CORRECT - bare list at root
- type: quiz
  title: Quiz title

- type: match-up
  title: Match title
```

```yaml
# ❌ WRONG - dictionary wrapper causes schema validation failure
activities:
  - type: quiz
```

### 2. Use Schema Property Names
| Activity | Correct | Wrong |
|----------|---------|-------|
| unjumble | `jumbled` | `scrambled`, `words` |
| mark-the-words | `text` + `answers` | `passage`, asterisks |
| true-false | `statement` | `sentence` |

### 3. Mark-the-Words Format
```yaml
# ✅ CORRECT
- type: mark-the-words
  text: Гарний день приніс радість у серце.
  answers:
    - день
    - радість
    - серце

# ❌ WRONG - asterisks deprecated
text: Гарний *день* приніс *радість*.
answers: []
```

</critical>

---

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
└── activities/{num}-{slug}.yaml       # All activities in YAML
```

**Example for A1 Module 35 "At the Café":**
- `curriculum/l2-uk-en/a1/35-at-the-cafe.md`
- `curriculum/l2-uk-en/a1/activities/35-at-the-cafe.yaml`

**CRITICAL:** Activity files MUST include the module number prefix (e.g., `35-at-the-cafe.yaml`, NOT `at-the-cafe.yaml`).

## Migrating Existing Embedded Activities

**If MIGRATING an old module that has embedded activities:**

| Old Format                                          | Extract                                 | Put in YAML                               |
| --------------------------------------------------- | --------------------------------------- | ----------------------------------------- |
| `## quiz:` questions                                | Keep exact questions + options          | `items[].question`, `items[].options`     |
| `## match-up:` table rows                           | Keep all pairs                          | `pairs[].left`, `pairs[].right`           |
| `## fill-in:` sentences                             | Keep sentences + answers                | `items[].sentence`, `items[].answer`      |
| `## true-false:` statements                         | Keep statements + T/F                   | `items[].statement`, `items[].correct`    |
| `## group-sort:` categories                         | Keep groups + items                     | `groups[].name`, `groups[].items`         |
| `## unjumble:` scrambled                            | Keep scrambled + answer                 | `items[].jumbled`, `items[].answer`       |
| `## cloze:` passage with `[___:1]` blanks + options | Convert `[___:N]` → `{ans\|opt1\|opt2}` | `passage` with inline `{ans\|opt1\|opt2}` |
| `## error-correction:`                              | Keep sentence + error + fix             | `items[].sentence/error/answer`           |
| `## mark-the-words:`                                | Keep text + answers                     | `text` + `answers[]` array                |
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

See `docs/ACTIVITY-YAML-REFERENCE.md` for complete format specifications.

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

## Naturalness & Discourse Quality Requirements

<critical>

**Quality Threshold:** All prose activities (cloze, fill-in, unjumble) MUST score **>= 8/10** for naturalness.

**Common Failures (Score < 8):**

1. **Random subject shifts** without context:
   ```yaml
   # ❌ BAD - disconnected subjects (я → вона → він)
   - sentence: Я читаю книгу.
     answer: читаю
   - sentence: Вона пише листа.
     answer: пише
   - sentence: Він малює картину.
     answer: малює
   ```

2. **Missing discourse markers** (connectors):
   ```yaml
   # ❌ BAD - no connectors between sentences
   Я прокинувся. Я поснідав. Я пішов.

   # ✅ GOOD - добрано connectors
   Спочатку я прокинувся. Потім я поснідав. Нарешті я пішов до школи.
   ```

3. **Incoherent topic jumps**:
   ```yaml
   # ❌ BAD - school → coffee with no transition
   - Я йду до школи щодня.
   - Кава без цукру будь ласка.

   # ✅ GOOD - unified spatial context
   - Я йду до школи щодня.
   - Школа знаходиться біля великого парку.
   ```

4. **Redundant or contradictory statements**:
   ```yaml
   # ❌ BAD - repetitive without purpose
   - Я завжди снідаю.
   - Я зазвичай снідаю.
   - Я щодня снідаю.
   ```

**Fixes (How to Reach >= 8/10):**

| Issue | Solution | Ukrainian Connectors |
|-------|----------|---------------------|
| Subject shifts | Unify context (family, day, location) | я → моя сестра, мій брат, мама |
| No flow | Add discourse markers | спочатку, потім, після того, нарешті |
| Topic jumps | Create mini-narrative | а, але, тому, і |
| Drill format | Keep focused practice, don't force complex plots | Use simple family/daily contexts |

**Vocabulary Constraints:**

- **ONLY use vocabulary from** `docs/l2-uk-en/{A1\|A2\|B1}-CURRICULUM-PLAN.md`
- **Check module number:** Don't use vocabulary from later modules
  - Example: Module 07 (Spatial Prepositions) must NOT use Module 08 prepositions (без, для, через, про)

**Pedagogical Correctness:**

- **Preserve grammar point** being taught
- **Don't sacrifice drill focus** for narrative complexity
- **Maintain CEFR level** (A1 = simple, A2 = connected, B1 = coherent)

**Testing Naturalness:**

Use MCP tool to validate fixes:
```bash
# Via MCP server
mcp__ukrainian-validator__check_naturalness(
  content="Учора я читав книгу. Потім моя сестра написала листа.",
  level="A2",
  context="fill-in activity about aspect"
)
```

**Target:** Score >= 8/10 (natural Ukrainian discourse)

</critical>

---

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
| select           | -           | opt | 1+  | 1+  | 1+  | 1+  |
| translate        | -           | opt | 1+  | 1+  | 2+  | 2+  |

## YAML Format Reference

> [!IMPORTANT]
> See `docs/ACTIVITY-YAML-REFERENCE.md` for complete format with examples.

### Common Activity Structures

```yaml
# Quiz (8+ items for B1)
- type: quiz
  title: Quiz title
  instruction: Select the correct answer.
  items:
    - question: Яке слово є синонімом до "великий"?
      options:
        - text: малий
          correct: false
        - text: величезний
          correct: true
        - text: швидкий
          correct: false
        - text: повільний
          correct: false
      explanation: "Величезний" означає дуже великий.

# Match-up (12+ pairs for B1)
- type: match-up
  title: Match title
  instruction: Match the pairs.
  pairs:
    - left: іти
      right: to go (on foot)
    - left: їхати
      right: to go (by vehicle)

# Fill-in (12+ items for B1)
- type: fill-in
  title: Fill-in title
  instruction: Choose the correct word.
  items:
    - sentence: Вона [___] до магазину, щоб купити хліб.
      answer: пішла
      options:
        - пішла
        - їхала
        - летіла
        - бігла

# True-false (12+ items for B1)
- type: true-false
  title: True/False title
  instruction: Determine if the statement is true or false.
  items:
    - statement: Дієслово "іти" означає рух пішки.
      correct: true
      explanation: Так, "іти" — це рух пішки, на відміну від "їхати" (транспортом).

# Group-sort (16+ total items, 3-5 categories for B1)
- type: group-sort
  title: Sorting title
  instruction: Sort items into categories.
  groups:
    - name: Дієслова руху пішки
      items:
        - іти
        - бігти
    - name: Дієслова руху транспортом
      items:
        - їхати
        - летіти
    - name: Не дієслова руху
      items:
        - читати
        - писати

# Unjumble (6+ items for B1, 12-16 words per sentence)
- type: unjumble
  title: Unjumble title
  instruction: Put the words in the correct order.
  items:
    - jumbled: Вона / до / пішла / магазину
      answer: Вона пішла до магазину.

# Cloze (14+ blanks for B1)
- type: cloze
  title: Cloze title
  instruction: Fill in the blanks.
  passage: 'Марія {пішла|поїхала|полетіла} до школи, а потім {зайшла|виїхала|прибігла} до бібліотеки.'

# Error-correction (6+ items for B1)
- type: error-correction
  title: Error correction title
  instruction: Find and fix the ONE error in each sentence.
  items:
    - sentence: Вона пішла до магазин, щоб купити хліб.
      error: магазин
      answer: магазину
      options:
        - магазин
        - магазину
        - магазином
        - магазині
      explanation: Після прийменника "до" потрібен родовий відмінок — "магазину".

# Mark-the-words (6+ correct words for B1)
- type: mark-the-words
  title: Mark words title
  instruction: Знайдіть усі іменники.
  text: Гарний день приніс радість у серце.
  answers:
    - день
    - радість
    - серце

# Select (6+ items for B1)
- type: select
  title: Select title
  instruction: Select ALL correct answers for each question.
  items:
    - question: Які з цих слів є дієсловами руху?
      options:
        - text: іти
          correct: true
        - text: бігти
          correct: true
        - text: стіл
          correct: false
        - text: великий
          correct: false
      explanation: Іти та бігти означають рух, стіл — іменник, великий — прикметник.

# Translate (6+ items for B1)
- type: translate
  title: Translate title
  instruction: Choose the correct Ukrainian translation.
  items:
    - source: She went to the store.
      options:
        - text: Вона пішла до магазину.
          correct: true
        - text: Вона їхала до магазину.
          correct: false
        - text: Вона біжить до магазину.
          correct: false
        - text: Вона йде до магазину.
          correct: false
      explanation: "Went" — минулий час, тому "пішла".
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
[production] unjumble → translate
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
