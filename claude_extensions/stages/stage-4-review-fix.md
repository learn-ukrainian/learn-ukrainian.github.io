# Stage 4: Review & Fix Loop

> **⚠️ READ FIRST: `claude_extensions/NON-NEGOTIABLE-RULES.md`**
>
> All audit gates MUST pass. NO exceptions. NO negotiation. Work until ✅ on ALL gates.

> **⚠️ CRITICAL: Always use `.venv/bin/python` for ALL Python scripts.**
> Never use `python3` or `python` directly - dependencies are in the venv.

Review the module, fix violations, repeat until PASS.

## SUCCESS CRITERIA

**A module is COMPLETE when:**
- ✅ ALL audit gates show green checkmarks
- ✅ Naturalness score is 8+/10
- ✅ Word count meets or exceeds target
- ✅ NO violations remain

**INCOMPLETE means:**
- ❌ ANY gate shows red X
- ⚠️ ANY gate shows warning
- Word count below target
- ANY violations remain

**If incomplete: KEEP WORKING. Loop until complete.**

## Input

- **Module file**: Complete module from Stages 1-3
- **Level**: Determines constraints and expectations

## Process

```
┌─────────────────────────────────────────────────┐
│                 REVIEW MODULE                   │
│         Run audit, check all constraints        │
└─────────────────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │    VIOLATIONS?        │
            └───────────────────────┘
                   │         │
                   │ NO      │ YES
                   ▼         ▼
        ┌─────────────┐   ┌─────────────────────────┐
        │   PASS!     │   │  COUNT VIOLATIONS       │
        │ Output MDX  │   │  ≤3 = FIX               │
        │             │   │  >3 = REBUILD SECTION   │
        └─────────────┘   └─────────────────────────┘
                                    │
                                    ▼
                          ┌─────────────────────┐
                          │   APPLY FIX or      │
                          │   REBUILD SECTION   │
                          └─────────────────────┘
                                    │
                                    ▼
                              (loop back to REVIEW)
```

## Review Checklist

### 1. Template Compliance

- [ ] **Read the appropriate template** for this module type:
  - **B1 M01-05 (Metalanguage):** `docs/l2-uk-en/templates/b1-metalanguage-module-template.md`
  - **B1 M06-51 (Grammar):** `docs/l2-uk-en/templates/b1-grammar-module-template.md`
  - **B1 Checkpoints (M15, M25, M34, M41, M51 — grammar phases only):** `docs/l2-uk-en/templates/b1-checkpoint-module-template.md`
  - **B1 M52-71 (Vocabulary):** `docs/l2-uk-en/templates/b1-vocab-module-template.md`
  - **B1 M72-81 (Cultural):** `docs/l2-uk-en/templates/b1-cultural-module-template.md`
  - **B1 M82-86 (Integration):** `docs/l2-uk-en/templates/b1-integration-module-template.md`
  - **B2:** `docs/l2-uk-en/templates/b2-module-template.md`
  - **C1:** `docs/l2-uk-en/templates/c1-module-template.md`
  - **C2:** `docs/l2-uk-en/templates/c2-module-template.md`
  - **LIT:** `docs/l2-uk-en/templates/lit-module-template.md`
- [ ] Module structure matches template sections
- [ ] Word count meets template minimum
- [ ] Activity count and types match template requirements
- [ ] Vocabulary count meets template specification

### 2. Structural Audit

- [ ] Metadata YAML sidecar exists and has required fields
- [ ] Vocabulary YAML sidecar exists (no embedded table)
- [ ] Activities YAML sidecar exists (no embedded activities)

### 3. Grammar Constraints

- [ ] Only uses grammar allowed at this level
- [ ] See `{LEVEL}-CURRICULUM-PLAN.md` Каталог В

### 4. Vocabulary Constraints

- [ ] Vocabulary YAML matches Schema (POS, Gender, IPA)
- [ ] Uses vocabulary from curriculum plan
- [ ] `validate_vocab_yaml.py` passes
- **Note:** Cross-module vocab validation deferred to pipeline

### 5. Activity Constraints

- [ ] Count meets minimum (8-16+ by level)
- [ ] Items per activity meets minimum (12-18+ by level)
- [ ] Type variety (4-5+ types)
- [ ] Correct syntax (fill-in `___`, unjumble `/`, etc.)
- [ ] All answers correct

### 6. Richness Constraints (Counts)

**CRITICAL: Read `docs/RICHNESS-SCORING-GUIDE.md` for scoring details and fix templates.**

- [ ] Word count meets target
- [ ] Example sentences meet minimum
- [ ] Engagement boxes meet minimum
- [ ] Mini-dialogues present

When richness fails, check the audit report for **Dryness Flags** and use the exact fix templates from the guide.

### 7. Content Richness Quality (B1+ Critical)

**This is not about counts. This is about whether the content is ALIVE or DEAD.**

Check each section for these quality indicators:

#### 7a. Engagement Quality

**DRY (robot wrote this):**

```markdown
Доконаний вид показує завершену дію.
Недоконаний вид показує незавершену дію.
Дивіться таблицю нижче.
```

**RICH (learner will remember this):**

```markdown
Уявіть: ви читаєте книгу весь вечір — це процес, недоконаний вид.
Але ось ви закрили книгу — готово! Результат. Доконаний вид.

Це як різниця між «я йшов додому» (може, ще йду) і «я прийшов» (точка, фініш).

💡 **Чому це важливо?**
Українці чують цю різницю одразу. Неправильний вид —
і речення звучить... дивно. Як фальшива нота в пісні.
```

#### 7b. Variety Check

**Count unique sentence starters in each section.** If >50% of sentences start the same way, flag as DRY.

❌ DRY pattern:

```markdown
Доконаний вид означає...
Доконаний вид використовується...
Доконаний вид показує...
Доконаний вид має...
```

✅ RICH pattern:

```markdown
Коли дія завершена — це доконаний вид.
Українці кажуть «я прочитав книгу», бо книга закінчена.
А якщо ще читаю? Тоді «читаю» — без результату.
Порівняйте: «він писав лист» vs «він написав лист».
```

#### 7c. Emotional Hooks

**Each major section needs at least one of:**

- Metaphor or analogy (як фальшива нота, як різниця між X і Y)
- Real-world scenario (уявіть: ви на співбесіді...)
- Cultural connection (українці кажуть так, бо...)
- Surprise or contrast (але тут є сюрприз!)
- Question to reader (а що якщо...? чому так?)

❌ No hooks = textbook voice = learner falls asleep

✅ Has hooks = conversation voice = learner stays engaged

#### 7d. Cultural Depth (B1+)

**Each module should include:**

- [ ] At least 1 named Ukrainian place (Львів, Карпати, Дніпро)
- [ ] At least 1 cultural reference (traditional, historical, or contemporary)
- [ ] Real-world context showing WHY this grammar/vocab matters

❌ Generic: "Людина купує хліб у магазині."
✅ Specific: "Оксана купує паляницю на Бесарабському ринку в Києві."

#### 7e. Proverbs & Idioms (B1+)

**Each grammar module should include 1-2 proverbs or idioms that:**

- Naturally demonstrate the grammar point
- Are woven into content, not just listed
- Have cultural context explained

Example for aspect:

```markdown
Українці кажуть: «Не кажи гоп, поки не перескочиш».
Зверніть увагу: **перескочиш** — доконаний вид.
Чому? Бо йдеться про результат: перестрибнув чи ні.
```

#### 7f. Richness Score Calculation

For each section, mentally score:

| Criterion       | 0                   | 1                | 2                         |
| --------------- | ------------------- | ---------------- | ------------------------- |
| Engagement      | Textbook voice      | Some personality | Conversational, memorable |
| Variety         | Repetitive starters | Mixed            | Varied, rhythmic          |
| Hooks           | None                | 1-2              | 3+ per section            |
| Cultural depth  | Generic examples    | Some specifics   | Rich, placed content      |
| Proverbs/idioms | None                | 1 (forced)       | 1-2 (natural)             |

**Total 0-4:** ❌ REWRITE section
**Total 5-7:** ⚠️ ENRICH section
**Total 8-10:** ✅ PASS

#### 7g. Quick Dryness Flags

Flag content as DRY if ANY of these are true:

| Flag                  | Pattern                                                   |
| --------------------- | --------------------------------------------------------- |
| TEXTBOOK_VOICE        | No questions, metaphors, or emotional hooks in 300+ words |
| REPETITIVE            | Same sentence structure >5 times in section               |
| GENERIC_EXAMPLES      | No named people, places, or specific scenarios            |
| LIST_DUMP             | Explanation is just a list without narrative flow         |
| NO_CULTURAL_ANCHOR    | Grammar taught without Ukrainian cultural context         |
| ENGAGEMENT_BOX_FILLER | 💡 boxes just restate what was already said               |

**If 2+ flags: Section needs REWRITE, not just fix.**

### 8. Linguistic Purity

- [ ] No Surzhyk or "Ghost Words" (Verify spelling is Ukrainian, not Russian). See LINGUISTIC-PURITY-GUIDE.md
- [ ] No AI contamination ("wait", "actually", "let me")
- [ ] Correct Ukrainian spelling and grammar
- [ ] **NO Russian Characters**: Search for `ё`, `ъ`, `ы`, `э` (Forbidden).
- [ ] **NO Russian Phonetics**: No comparisons like "Ukrainian И is like Russian Ы".

### 9. Naturalness Check

After grammar and vocabulary validation, check ALL Ukrainian text for naturalness.

**Purpose:** Prevent disconnected drills, template repetition, and robotic flow that grammar/vocabulary checks miss.

**How it works:** You evaluate naturalness directly using your Ukrainian language knowledge. No external tools or MCP servers required. As an LLM trained on extensive Ukrainian text, you can assess flow, register, and authenticity.

**CRITICAL:** Naturalness is NEVER "N/A" - every module with Ukrainian text requires evaluation, including alphabet modules with simple instructions.

#### 9.1 Extract ALL Ukrainian Text

Evaluate ALL Ukrainian content in the module:

**Always evaluate:**
- **Activity instructions** (e.g., "З'єднайте відповідні елементи", "Оберіть правильну відповідь")
- **Cloze passages** (any length)
- **Fill-in sentences/paragraphs**
- **Unjumble sentences**
- **Quiz explanations** in Ukrainian
- **Mark-the-words text passages**

**Minimal evaluation (just check instructions):**
- `match-up`, `group-sort` - typically just have instruction text
- `quiz`, `true-false`, `select` - check instruction + any Ukrainian explanations

#### 9.2 Analyze Naturalness (Switch to Ukrainian Language Mode)

Score each prose activity 1-10 based on:

1. **Subject consistency** - Are subjects maintained throughout passages?
2. **Discourse markers** - Presence of connectors (а, але, потім, тому, також, спочатку, нарешті)
3. **Topic coherence** - Do passages maintain unified topics or jump randomly?
4. **Redundancy** - Are there repetitive patterns or disconnected sentences?

**Red flags (score < 8/10):**

| Issue | Example |
|-------|---------|
| **Template repetition** | Same sentence structure repeated across multiple activities in module |
| **Excessive intensifiers** | "дуже" used 5+ times, or "надзвичайно/справжній" overused |
| **Double superlatives** | "найвидатніший та найвідоміший" (semantically redundant) |
| **Missing discourse markers** | List of disconnected factoids with no connectors |
| **Robotic transitions** | "і це допомагає...", "тому що... тому" (mechanical constructions) |

#### 9.3 Scoring Standards

| Module Type | Target Score | Flag If |
|-------------|--------------|---------|
| **Content modules** | 8/10 | < 8/10 |
| **Checkpoints/Review** | 7/10 | < 7/10 |
| **Minimal prose modules** | 8/10 | < 8/10 (still evaluate instructions) |

**Score all Ukrainian text** in the module. If average is below target, flag for fixes.

#### 9.3.1 Update Meta File After Scoring

After evaluating naturalness, **always update the module's meta file**:

```yaml
# curriculum/l2-uk-en/{level}/meta/{num}-{slug}.yaml
naturalness:
  score: 9      # Your evaluated score (1-10)
  status: PASS  # PASS if score >= 8 (or >= 7 for checkpoints), else PENDING/FAIL
```

**Status values:**
- `PASS` - Score meets threshold, audit will pass
- `PENDING` - Not yet evaluated (causes audit FAIL)
- `FAIL` - Evaluated but below threshold

The audit reads this meta file and will FAIL if status is not PASS or score < 8.

#### 9.4 Fix Flagged Issues

If module average score < target:

1. **Identify specific patterns** causing issues (which red flags apply?)
2. **Propose fixes** using ONLY:
   - Vocabulary from M01-M{current} (check cumulative vocab)
   - Grammar from curriculum plan (check allowed constructs)
3. **Apply fixes** to activities YAML file
4. **Re-score** to verify improvement

**Common fix strategies:**

| Issue | Fix |
|-------|-----|
| Template repetition | Vary sentence structures across activities |
| Excessive intensifiers | Remove 50% of "дуже", eliminate "надзвичайно/справжній" unless essential |
| Double superlatives | Replace with single precise descriptor |
| Missing discourse markers | Add 2-3 connectors per 10-sentence passage (також, проте, тому, спочатку) |
| Robotic transitions | Simplify mechanical constructions, use natural flow |

**See also:** For batch naturalness scanning of completed modules, use `/scan-naturalness {level} {start} {end}`

### 10. Seminar Track Pairing (LIT, B2-HIST, C1-HIST, C1-BIO)

**Applies to:** LIT, B2-HIST, C1-HIST, C1-BIO tracks only.

Seminar tracks use **Reading-Analysis Pairs** architecture:
- Every analytical activity MUST link to a reading source
- `reading` activities provide INPUT (source text)
- `essay-response`, `critical-analysis`, `comparative-study` provide OUTPUT (analysis)

#### 10.1 Audit Violations

| Violation | Severity | Meaning |
|-----------|----------|---------|
| `READING_MISSING_ID` | CRITICAL | Reading activity lacks `id` field |
| `MISSING_SOURCE_READING` | CRITICAL | Analytical activity lacks `source_reading` link |
| `INVALID_SOURCE_READING` | CRITICAL | `source_reading` points to non-existent reading id |
| `ORPHAN_READING` | WARNING | Reading defined but never referenced |

#### 10.2 Fix: Add Missing Reading Activity

If module has analytical activities but no `reading` activity:

**Step 1:** Identify source material from the module content (prose section)

**Step 2:** Create reading activity at the TOP of the YAML:

```yaml
- type: reading
  id: reading-01                    # REQUIRED: unique ID
  title: 'Джерело: [Topic]'
  source: '[Author] ([Year])'       # Attribution
  text: |
    [Extract 200-500 words of primary source text
    that the analytical activities will analyze]
```

**Step 3:** Link existing analytical activities:

```yaml
- type: essay-response
  source_reading: reading-01        # ADD THIS LINE
  title: 'Есе: ...'
  prompt: '...'
```

#### 10.3 Fix: Add source_reading to Existing Activities

For each `essay-response`, `critical-analysis`, `comparative-study`, or `authorial-intent`:

1. Identify which reading it analyzes
2. Add `source_reading: reading-XX` field
3. Ensure the referenced reading exists

**Example fix:**

```yaml
# BEFORE (fails audit)
- type: critical-analysis
  title: 'Аналіз символіки'
  target_text: 'Поховайте та вставайте...'
  questions:
    - 'Яку функцію виконує імператив?'

# AFTER (passes audit)
- type: critical-analysis
  source_reading: reading-01        # ← ADDED
  title: 'Аналіз символіки'
  target_text: 'Поховайте та вставайте...'
  questions:
    - 'Яку функцію виконує імператив?'
```

#### 10.4 Fix: Reading Missing ID

```yaml
# BEFORE (fails audit)
- type: reading
  title: 'Джерело: Заповіт'
  text: |
    Як умру, то поховайте...

# AFTER (passes audit)
- type: reading
  id: reading-testament              # ← ADDED (pattern: reading-[slug])
  title: 'Джерело: Заповіт'
  text: |
    Як умру, то поховайте...
```

#### 10.5 Multiple Readings Strategy

For modules with multiple source texts:

```yaml
# First reading for first set of analyses
- type: reading
  id: reading-01
  title: 'Джерело 1: ...'
  text: '...'

# Second reading for comparison
- type: reading
  id: reading-02
  title: 'Джерело 2: ...'
  text: '...'

# Analytical activity referencing first reading
- type: essay-response
  source_reading: reading-01
  title: 'Есе про джерело 1'

# Comparative study using both
- type: comparative-study
  source_reading: reading-01        # Primary reference
  title: 'Порівняння двох джерел'
  items_to_compare:
    - 'Джерело 1'
    - 'Джерело 2'
```

#### 10.6 Quick Fix Checklist for Seminar Tracks

- [ ] At least ONE `reading` activity exists
- [ ] ALL `reading` activities have `id` field
- [ ] ALL `essay-response` have `source_reading`
- [ ] ALL `critical-analysis` have `source_reading`
- [ ] ALL `comparative-study` have `source_reading`
- [ ] ALL `authorial-intent` have `source_reading`
- [ ] ALL `source_reading` values point to valid reading IDs

#### 10.7 LLM Self-Validation (MANDATORY for Audit)

<critical>

**SKEPTICAL VALIDATION - NOT A RUBBER STAMP**

You are the last line of defense. The audit script catches syntax and structure, but YOU must catch:
- Wrong URLs pointing to wrong authors
- Factual errors in historical content
- Unnatural or robotic Ukrainian
- Model answers that don't match prompts

**Approach:**
- **Assume errors exist** until you verify otherwise
- **Actively look for problems**, don't just confirm correctness
- **Check specific details** (dates, names, URLs) against your knowledge
- **If uncertain, FLAG IT** - false positives are better than missed errors

**DO NOT:**
- ❌ Skim and approve
- ❌ Copy-paste "all checks passed" without verification
- ❌ Assume previous creator got it right

**DO:**
- ✅ Read every Ukrainian sentence critically
- ✅ Verify each URL against known mappings
- ✅ Check that model answers actually address prompts
- ✅ Document specific evidence for each check

---

**The audit script cannot verify content accuracy. YOU (the LLM doing the audit) MUST verify these against your knowledge:**

**1. External URL Verification**

For every `reading` activity with a `resource.url`:

- Do you recognize this URL from your training data?
- Does the URL content match the expected author/topic?
- Known URL mappings (verify or flag):

| Author | UkrLib URL |
|--------|------------|
| Нечуй-Левицький | `tid=1646` |
| Шевченко | `tid=57` |
| Куліш | `tid=1621` |
| Котляревський | `tid=1553` |
| Франко | `tid=71` |
| Леся Українка | `tid=83` |
| Кобилянська | `tid=1582` |
| Квітка-Основ'яненко | `tid=1568` |

**If URL doesn't match your knowledge: FLAG as `INVALID_EXTERNAL_URL` with suggested correction.**

**2. Reading-Analysis Coherence**

For every `critical-analysis` and `authorial-intent`:

- Does `target_text` actually appear in or derive from the source reading?
- Do the `questions` relate directly to the reading content?
- Are `focus_points` appropriate for the target text?

**If mismatched: FLAG as `INCOHERENT_ANALYSIS` with explanation.**

**3. Model Answer Quality**

For every `essay-response`, `critical-analysis`, and `comparative-study`:

- Does `model_answer` actually address the prompt/questions?
- Is the analysis substantive and correct?
- Does it demonstrate the expected analytical approach?

**If model answer is off-topic or incorrect: FLAG as `INVALID_MODEL_ANSWER`.**

**4. Factual Accuracy**

For all historical/biographical content:

- Are dates correct?
- Are names spelled correctly?
- Are historical facts accurate?
- Are literary attributions correct?

**If factual error found: FLAG as `FACTUAL_ERROR` with correction.**

**Audit Report Format for Self-Validation Issues:**

```
=== LLM SELF-VALIDATION ===

INVALID_EXTERNAL_URL (CRITICAL)
  Activity: Біографія Нечуя-Левицького
  Current URL: https://www.ukrlib.com.ua/bio/printit.php?tid=1815
  Expected: tid=1646 (Нечуй-Левицький)
  Reason: URL points to wrong author

FACTUAL_ERROR (WARNING)
  Activity: Есе про творчість
  Issue: "народився 1845" should be "народився 1838"
```

**Logging Results (MANDATORY):**

Write self-validation results to a **separate file** (audit.py overwrites the main review file):

**File:** `curriculum/l2-uk-en/{level}/audit/{slug}-llm-review.md`

```markdown
# LLM Self-Validation: {slug}
**Validated by:** Claude/Gemini | **Date:** YYYY-MM-DD
**Content Hash:** {first 8 chars of md5 hash of module .md file}

## Verification Evidence

### External URLs
**Status:** ✅/❌
- URL: `{actual URL from module}`
- Expected author: {author name}
- Verified against: {tid mapping or knowledge source}
- Evidence: "{quote from page title or content proving correct author}"

### Reading-Analysis Coherence
**Status:** ✅/❌
- Reading ID: `{reading-id}`
- Linked activities: {list of activity types referencing it}
- Target text verification: "{first 10 words of target_text}" appears in source: YES/NO

### Model Answers
**Status:** ✅/❌
- Checked {N} model answers
- Each addresses its prompt: YES/NO
- Quality issues: {specific issues or "None found"}

### Factual Accuracy
**Status:** ✅/❌
- Key facts verified:
  - Birth/death dates: {dates} ✓
  - Locations: {places} ✓
  - Historical events: {events} ✓
- Corrections needed: {list or "None"}

### Naturalness
**Status:** ✅/❌ | **Score:** X/10
- Checked {N} prose passages
- Red flags: {template repetition, robotic transitions, etc. or "None"}

## Issues Found
[MUST list specific issues with line numbers/activity names, or explicitly state "None found after checking X items"]

## Fixes Applied
[List specific fixes with before/after, or "None needed"]
```

**EVIDENCE REQUIRED:** Generic statements like "all checks passed" are NOT acceptable. Each section must show WHAT was checked and HOW it was verified.

**Content Hash:** Run `md5 -q {module}.md | cut -c1-8` to get the hash. If module changes after review, audit will FAIL as stale.

**Two-file structure:**
- `{slug}-review.md` - Auto-generated by `audit.py` (script output)
- `{slug}-llm-review.md` - Written by LLM (self-validation, never overwritten by script)

</critical>

### 11. Core Module LLM Self-Validation (A1-C2)

**Applies to:** A1, A2, B1, B2, C1, C2 core levels.

<critical>

**SKEPTICAL VALIDATION - NOT A RUBBER STAMP**

You are the last line of defense for core modules. Be aggressive in finding errors:
- Russianisms slip through constantly (приймати участь, на протязі)
- English calques from translation (робити сенс, брати місце)
- Wrong case endings in activities
- Vocabulary too advanced for the level

**Approach:**
- **Read every Ukrainian sentence** - don't skim
- **Check vocabulary against curriculum plan** - is this word allowed at this level?
- **Verify activity answers** - are the "correct" answers actually correct?
- **Flag uncertainty** - if you're not sure, mark it for review

---

**The audit script checks structure and counts but cannot verify content accuracy. YOU (the LLM doing the audit) MUST verify:**

**1. Ukrainian Grammar Correctness**

- Are all Ukrainian sentences grammatically correct?
- Are case endings correct for the context?
- Is word order natural (not calqued from English)?
- Are verb aspects used correctly?

**Common errors to check:**
| ❌ Wrong | ✅ Correct | Issue |
|----------|-----------|-------|
| приймати участь | брати участь | Russicism |
| самий кращий | найкращий | Superlative calque |
| на протязі | протягом | Russicism |
| робити сенс | мати сенс | English calque |

**2. Vocabulary Appropriateness**

- Is vocabulary within the level scope? (Check curriculum plan)
- Are words used in correct contexts?
- Are collocations natural?

**3. Activity Instructions Clarity**

- Are instructions unambiguous?
- Can learners understand what to do?
- Are example answers correct?

**4. Cultural/Factual Accuracy**

- Are cultural references accurate?
- Are any facts stated that could be wrong?

**Logging Results (MANDATORY):**

**File:** `curriculum/l2-uk-en/{level}/audit/{slug}-llm-review.md`

```markdown
# LLM Self-Validation: {slug}
**Validated by:** Claude/Gemini | **Date:** YYYY-MM-DD
**Content Hash:** {first 8 chars of md5 hash of module .md file}

## Verification Evidence

### Grammar
**Status:** ✅/❌
- Sentences checked: {N}
- Russianisms found: {list or "None"}
- English calques found: {list or "None"}
- Case/aspect errors: {list or "None"}
- Sample verified: "{quote a sentence you checked}"

### Vocabulary
**Status:** ✅/❌
- Level: {A1/A2/B1/B2/C1/C2}
- Words checked against curriculum plan: {N}
- Out-of-scope words found: {list or "None"}
- Collocation issues: {list or "None"}

### Activity Instructions
**Status:** ✅/❌
- Activities reviewed: {N}
- Ambiguous instructions: {list with activity names or "None"}
- Incorrect example answers: {list or "None"}

### Factual Accuracy
**Status:** ✅/❌
- Cultural references verified: {list what you checked}
- Corrections needed: {list or "None"}

### Naturalness
**Status:** ✅/❌ | **Score:** X/10
- Prose passages checked: {N}
- Red flags: {specific issues or "None"}

## Issues Found
[MUST list specific issues with line numbers/activity names, or explicitly state "None found after checking X items"]

## Fixes Applied
[List specific fixes with before/after, or "None needed"]
```

**EVIDENCE REQUIRED:** Generic statements like "all checks passed" are NOT acceptable. Each section must show WHAT was checked and HOW it was verified.

**Content Hash:** Run `md5 -q {module}.md | cut -c1-8` to get the hash. If module changes after review, audit will FAIL as stale.

</critical>

---

## ⚡ Specialized Fix Protocols

### Common YAML Schema Violations - Quick Reference

**Use this table to diagnose and fix schema errors immediately:**

**For minimum item counts:** Check `claude_extensions/quick-ref/{level}.md` (each level has different minimums)

| Error Pattern | Root Cause | Fix |
|--------------|------------|-----|
| Quiz/fill-in/true-false has too few items | Below level-specific minimum | Check quick-ref for your level's minimum, add items |
| Cloze has too few blanks | Below level-specific minimum | Check quick-ref for your level's minimum, add blanks |
| Fill-in: "missing required 'options'" | `options` field required for each item | Add `options: [opt1, opt2, opt3, opt4]` |
| Cloze: "not valid under any schema" | Has both `blanks:` array AND inline `{a\|b}` | Remove `blanks:` array OR switch to numbered format |
| "Field 'instructions' not recognized" | Schema requires singular | Change to `instruction:` (no 's') |
| "Field 'id' not allowed" | `additionalProperties: false` | Remove `id:` field (only for LIT activities) |
| "Unexpected character near apostrophe" | Ukrainian apostrophe in single quotes | Change to double quotes: `"інтерв'ю"` |
| "Activity type 'writing' invalid" | Wrong type name | Use `essay-response` instead |
| Unjumble: "array too short" | Less than 6 words | Add words to reach 6+ per sentence |

### Fix Protocol: YAML Parse Errors

**If audit shows "Error parsing YAML":**

1. **Check for apostrophe conflicts:**
   ```bash
   grep -n "answer: '" activities/file.yaml
   ```
   Fix: Change all single-quoted strings with apostrophes to double quotes

2. **Check for unquoted colons:**
   ```bash
   grep -n ": " activities/file.yaml | grep -v "^  *-"
   ```
   Fix: Quote any string values containing colons

3. **Validate YAML syntax:**
   ```bash
   .venv/bin/python -c "import yaml; yaml.safe_load(open('activities/file.yaml'))"
   ```

### Fix Protocol: Schema Validation Errors

**Step-by-step diagnostic:**

1. **Identify activity index** from error: `Schema validation error at key '9'`
2. **Count activities** in YAML (0-indexed, so key '9' = 10th activity)
3. **Check activity type** and **compare to schema requirements:**
   - Read `schemas/activities-{level}.schema.json` for your level (e.g., `activities-b2.schema.json`)
   - Check `minItems`, `required` fields, `additionalProperties`
   - Cross-reference with `claude_extensions/quick-ref/{level}.md` for minimums

4. **Common fixes:**
   - **Missing fields:** Add required fields (`title`, `instruction`, `items`)
   - **Extra fields:** Remove fields not in schema (`id`, `instructions` with 's')
   - **Wrong minimum:** Add items to meet level minimums (see quick-ref)
   - **Wrong structure:** Fix nested object format (e.g., `options` array must have exactly 4 items)

### Fix Protocol: Stale LLM Review

```bash
# Calculate new content hash
.venv/bin/python << 'EOF'
import sys, hashlib
sys.path.append('scripts')
from audit.core import extract_core_content, clean_for_stats

content = open('curriculum/l2-uk-en/{level}/{file}.md').read()
core = extract_core_content(content)
prose = clean_for_stats(core)
new_hash = hashlib.md5(prose.encode('utf-8')).hexdigest()[:8]
print(f"New hash: {new_hash}")
EOF

# Update hash in LLM review file
# Then run audit again to verify PASS
```

**CRITICAL:** After updating hash, run audit immediately to ensure review is now valid.

---

## Fix Strategy

### Minor Violations (≤3 issues)

Apply targeted fixes:

- Missing vocabulary → Add to table
- Wrong syntax → Correct the specific line
- Missing engagement box → Add one
- Spelling error → Fix it

### Major Violations (>3 issues in same section)

Rebuild the section:

- Content section failing → Rewrite entire section
- Multiple activity failures → Delete all activities, recreate
- Grammar violations throughout → Rewrite affected paragraphs

### Catastrophic (>10 violations OR structural issues)

Rebuild from Stage 1:

- Frontmatter wrong → Start over
- Wrong pedagogy structure → Start over
- Vocabulary fundamentally wrong → Start over

## Running the Audit

```bash
# Auto-fix YAML schema violations, then run audit
.venv/bin/python scripts/audit_module.py {file_path} --fix
```

**The `--fix` flag automatically fixes common YAML schema violations:**

- Removes invalid `id` properties
- Extracts `correct_words` from mark-the-words passage
- Converts `scrambled` to `words` array in unjumble
- Adds missing `source` in translate
- Renames `prompt`/`text` to `question` in quiz/select

**Workflow:**

1. Auto-fix runs FIRST (if violations found)
2. Audit runs AFTER fixes applied
3. If audit still fails, manual fixes needed

Audit output categories:

- **FAIL**: Must fix (grammar, vocabulary, syntax)
- **WARN**: Should fix (richness, variety)
- **INFO**: Optional improvement

## Iteration Limit

Maximum 3 fix iterations per stage. If still failing after 3:

1. Report the persistent issues
2. Ask user for guidance
3. Consider rebuilding from earlier stage

## Output on PASS

When audit passes, run the full pipeline:

```bash
# Full pipeline: lint → generate MDX → validate MDX → validate HTML
npm run pipeline l2-uk-en {level} {module_num}
```

The pipeline validates:

1. **Lint**: MD format compliance
2. **Generate**: Creates MDX for Docusaurus
3. **Validate MDX**: Ensures no content loss during conversion
4. **Validate HTML**: Headless browser check for rendering errors

**Note:** HTML validation requires dev server running (`cd docusaurus && pnpm start`)

Report:

- Final audit score
- Pipeline status (PASS/FAIL)
- MDX file location
- "MODULE APPROVED"
