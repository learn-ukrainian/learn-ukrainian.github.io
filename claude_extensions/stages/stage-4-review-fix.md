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

## Process

1. Run audit → 2. Violations? → YES: Fix (≤3) or Rebuild (>3) → Loop back to 1
                              → NO: PASS, run pipeline

## Review Checklist

### 1. Template Compliance

- [ ] **Read the appropriate template** for this module type:
  - **B1 M01-05 (Metalanguage):** `docs/l2-uk-en/templates/b1-metalanguage-module-template.md`
  - **B1 M06-51 (Grammar):** `docs/l2-uk-en/templates/b1-grammar-module-template.md`
  - **B1 Checkpoints:** `docs/l2-uk-en/templates/b1-checkpoint-module-template.md`
  - **B1 M52-71 (Vocabulary):** `docs/l2-uk-en/templates/b1-vocab-module-template.md`
  - **B1 M72-81 (Cultural):** `docs/l2-uk-en/templates/b1-cultural-module-template.md`
  - **B1 M82-86 (Integration):** `docs/l2-uk-en/templates/b1-integration-module-template.md`
  - **B2/C1/C2/LIT:** Respective templates
- [ ] Module structure matches template sections
- [ ] Word count meets template minimum
- [ ] Activity count and types match template requirements
- [ ] Vocabulary count meets template specification

### 2. Structural Audit

- [ ] Metadata YAML sidecar exists and has required fields
- [ ] Vocabulary YAML sidecar exists (no embedded table)
- [ ] Activities YAML sidecar exists (no embedded activities)

### 3. Grammar & Vocabulary

- [ ] Grammar allowed at level (check `{LEVEL}-CURRICULUM-PLAN.md`)
- [ ] Vocabulary YAML matches schema (POS, Gender, IPA)
- [ ] Uses vocabulary from curriculum plan

### 4. Activity Constraints

- [ ] Count meets minimum (8-16+ by level - check `quick-ref/{level}.md`)
- [ ] Items per activity meets minimum (12-18+ by level)
- [ ] Type variety (4-5+ different activity types)
- [ ] Correct syntax (fill-in `[___]`, unjumble `/`, cloze `{|}`)
- [ ] All answers correct

### 5. Richness Constraints (Counts)

**CRITICAL: Read `docs/RICHNESS-SCORING-GUIDE.md` for scoring details and fix templates.**

- [ ] Word count meets target
- [ ] Example sentences meet minimum
- [ ] Engagement boxes meet minimum (💡, ⚠️, 🎯)
- [ ] Mini-dialogues present

When richness fails, check the audit report for **Dryness Flags** and use the exact fix templates from the guide.

### 6. Content Richness Quality (B1+ Critical)

**This is not about counts. This is about whether the content is ALIVE or DEAD.**

Check each section for these quality indicators:

#### 6a. Engagement Quality

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

#### 6b. Variety Check

**DRY:** >50% sentences start the same way

```markdown
Доконаний вид означає...
Доконаний вид використовується...
Доконаний вид показує...
```

**RICH:** Varied sentence starters, rhythm

```markdown
Коли дія завершена — це доконаний вид.
Українці кажуть «я прочитав книгу», бо книга закінчена.
Порівняйте: «він писав лист» vs «він написав лист».
```

#### 6c. Emotional Hooks

**Each major section needs at least one of:**

- Metaphor or analogy (як фальшива нота, як різниця між X і Y)
- Real-world scenario (уявіть: ви на співбесіді...)
- Cultural connection (українці кажуть так, бо...)
- Surprise or contrast (але тут є сюрприз!)
- Question to reader (а що якщо...? чому так?)

❌ No hooks = textbook voice = learner falls asleep
✅ Has hooks = conversation voice = learner stays engaged

#### 6d. Cultural Depth (B1+)

**Each module should include:**

- [ ] 1+ named Ukrainian place (Львів, Карпати, Дніпро)
- [ ] 1+ cultural reference
- [ ] Real-world context showing WHY this matters

❌ Generic: "Людина купує хліб у магазині."
✅ Specific: "Оксана купує паляницю на Бесарабському ринку в Києві."

#### 6e. Proverbs & Idioms (B1+)

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

#### 6f. Quick Dryness Flags

Flag content as DRY if ANY of these are true:

**If 2+ flags: Section needs REWRITE, not just fix.**

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

### 8. Naturalness Check

After grammar and vocabulary validation, check ALL Ukrainian text for naturalness.

**Purpose:** Prevent disconnected drills, template repetition, and robotic flow that grammar/vocabulary checks miss.

**CRITICAL:** Naturalness is NEVER "N/A" - every module with Ukrainian text requires evaluation.

**Extract ALL Ukrainian:**
- Activity instructions (e.g., "З'єднайте відповідні елементи")
- Cloze passages
- Fill-in sentences/paragraphs
- Unjumble sentences
- Quiz explanations in Ukrainian
- Mark-the-words text passages

**Analyze naturalness based on:**
1. Subject consistency - Are subjects maintained throughout passages?
2. Discourse markers - Presence of connectors (а, але, потім, тому, також)
3. Topic coherence - Do passages maintain unified topics or jump randomly?
4. Redundancy - Are there repetitive patterns or disconnected sentences?

**Red flags (< 8/10):**

| Issue | Example |
|-------|---------|
| Template repetition | Same structure across activities |
| Excessive intensifiers | "дуже" 5+ times |
| Double superlatives | "найвидатніший та найвідоміший" |
| Missing discourse markers | No а, але, потім, тому |
| Robotic transitions | "і це допомагає...", "тому що... тому" |

**Standards:**
- Content modules: 8/10
- Checkpoints: 7/10

**If < target:**
1. Identify specific patterns causing issues (which red flags apply?)
2. Propose fixes using ONLY:
   - Vocabulary from M01-M{current} (check cumulative vocab)
   - Grammar from curriculum plan (check allowed constructs)
3. Apply fixes to activities YAML file
4. Re-score to verify improvement

**Common fix strategies:**

| Issue | Fix |
|-------|-----|
| Template repetition | Vary sentence structures across activities |
| Excessive intensifiers | Remove 50% of "дуже", eliminate "надзвичайно" unless essential |
| Double superlatives | Replace with single precise descriptor |
| Missing discourse markers | Add 2-3 connectors per 10-sentence passage (також, проте, тому) |
| Robotic transitions | Simplify mechanical constructions, use natural flow |

**Update meta YAML:**

```yaml
naturalness:
  score: 9
  status: PASS  # PASS if ≥8 (≥7 for checkpoints)
```

### 9. Seminar Track Pairing (LIT, B2-HIST, C1-BIO)

**Applies to:** LIT, B2-HIST, C1-HIST, C1-BIO tracks only.

Every analytical activity MUST link to reading source.

**Critical violations:**
- `MISSING_SOURCE_READING` - Add `source_reading: reading-XX`
- `READING_MISSING_ID` - Add `id: reading-XX`
- `INVALID_SOURCE_READING` - Fix broken reference

**Fix: Add Missing Reading Activity**

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

**Fix: Add source_reading to Existing Activities**

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

**Fix: Reading Missing ID**

```yaml
# BEFORE (fails audit)
- type: reading
  title: 'Джерело: Заповіт'
  text: |
    Як умру, то поховайте...

# AFTER (passes audit)
- type: reading
  id: reading-testament              # ← ADDED
  title: 'Джерело: Заповіт'
  text: |
    Як умру, то поховайте...
```

### 10. LLM Self-Validation - Seminar Tracks (MANDATORY)

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
