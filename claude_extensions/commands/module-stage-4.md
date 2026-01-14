# Module Stage 4: Review & Fix

> **⚠️ ALWAYS use `.venv/bin/python` - NEVER use `python3` or `python` directly!**

Review module, fix violations, loop until PASS.

## Usage

```
/module-stage-4 [LEVEL] [MODULE_NUM]
/module-stage-4 [LEVEL] [START]-[END]   # Batch mode
```

## Arguments

- `$ARGUMENTS` - Level and module number (e.g., `a1 15` or `b2 45`)
- Batch ranges supported: `b1 2-5` processes modules 2, 3, 4, 5

---

## Batch Mode (Multiple Modules)

**When arguments contain a range (e.g., `b1 2-5`):**

Use the **subagent pattern** to process each module with fresh context:

```
For each module in range:
  1. Spawn Task agent with subagent_type="general-purpose"
  2. Agent prompt: "Run /module-stage-4 {level} {module_num}"
  3. Wait for agent completion
  4. Log result (PASS/FAIL)
  5. Continue to next module (fresh context)
```

---

## Single Module Mode

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Stage Instructions

Read: `claude_extensions/stages/stage-4-review-fix.md`

### Step 2: Load Module

Read the module file:
`curriculum/l2-uk-en/{level}/{number}-*.md`

### Step 3: Run Initial Audit

```bash
.venv/bin/python scripts/audit_module.py {file_path}
```

Capture all violations.

### Step 4: Review Loop

**IF NO VIOLATIONS:** Go to Step 6 (PASS)

**IF VIOLATIONS:**

Count violations by category:
- Grammar violations (validate with dictionaries below)
- Vocabulary violations
- Activity syntax issues
- Richness failures
- Linguistic purity issues

**Ukrainian Grammar Validation (MANDATORY):**

Validate ALL Ukrainian text against these sources:
- ✅ **Словник.UA** (slovnyk.ua) - standard spelling
- ✅ **Словарь Грінченка** - authentic Ukrainian forms
- ✅ **Антоненко-Давидович "Як ми говоримо"** - Russianisms guide
- ❌ **NOT TRUSTED:** Google Translate, Russian-Ukrainian dictionaries

**Auto-fail Russianisms (fix before proceeding):**
| ❌ Wrong | ✅ Correct |
|----------|-----------|
| кушать | їсти |
| да | так |
| кто | хто |
| нету | немає |
| пока | поки |
| сейчас | зараз |
| приймати участь | брати участь |
| самий кращий | найкращий |
| слідуючий | наступний |
| на протязі | протягом |
| вибачаюсь | вибачте / перепрошую |

**Auto-fail Calques (English loan translations):**
| ❌ Wrong | ✅ Correct |
|----------|-----------|
| робити сенс | мати сенс |
| брати місце | відбуватися |
| дивитися вперед | чекати з нетерпінням |
| в кінці дня | врешті-решт |

**Use architect skills for fix guidance:**

| Module Type | Skill for Fixes |
|-------------|-----------------|
| Grammar (B1-B2) | `grammar-module-architect` |
| Vocabulary (B1) | `vocab-module-architect` |
| Cultural (B1-C1) | `cultural-module-architect` |
| History/Biography (B2-C1) | `history-module-architect` |
| Integration (B1-B2) | `integration-module-architect` |
| Checkpoint (All) | `checkpoint` |
| Literature (LIT) | `literature-module-architect` |

**Decision Matrix:**

| Violations | Action |
|------------|--------|
| ≤3 total | Fix individually |
| >3 in content | Rebuild content (Stage 2) |
| >3 in activities | Rebuild activities (Stage 3) |
| >10 OR structural | Rebuild from Stage 1 |

### Step 5: Apply Fixes or Rebuild

**For individual fixes:**
- Edit the specific lines
- Re-run audit
- Loop back to Step 4

**For section rebuild:**
- Call appropriate stage command
- Then return to this stage

**Maximum 3 iterations.** If still failing:
- Report persistent issues
- Ask user for guidance

### Step 5b: Vocabulary Sync Check (B2+)

**For B2+ modules (no embedded vocabulary tables):**

If content was modified, check vocabulary alignment:

1. **Identify new vocabulary** in updated content:
   - Look for Ukrainian words used in examples, dialogues, explanations
   - Compare against existing vocabulary YAML

2. **If new vocabulary found:**
   ```yaml
   # Add to existing {level}/vocabulary/{slug}.yaml
   - lemma: нове_слово
     ipa: ''          # Empty for enrichment
     translation: ''
     pos: noun
     gender: m
   ```

3. **Run enrichment** for new entries:
   ```bash
   .venv/bin/python scripts/enrich_yaml_vocab.py curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml
   ```

4. **Validate:**
   ```bash
   .venv/bin/python scripts/global_vocab_audit.py --level {level}
   ```

### Step 5c: Naturalness Check

**After all structural/grammar/vocabulary audits pass, check prose naturalness.**

**Reference:** See Section 9 in `claude_extensions/stages/stage-4-review-fix.md` for detailed criteria.

**Quick workflow:**

1. **Read activities YAML:** `curriculum/l2-uk-en/{level}/activities/{slug}.yaml`

2. **Extract prose activities:**
   - `cloze` passages with 5+ sentences
   - `fill-in` with multi-sentence context
   - `unjumble` with 5+ sentences
   - Skip: quiz, true-false, match-up, group-sort, select, error-correction, translate, mark-the-words

3. **If NO prose activities found:** Skip to Step 6 (PASS)

4. **If prose activities found:** Switch to Ukrainian language mode and analyze each:
   - Subject consistency
   - Discourse markers (а, але, потім, тому, також, спочатку, нарешті)
   - Topic coherence
   - Redundancy/repetition

5. **Score each activity 1-10:**
   - 8/10+ = Pass (content modules)
   - 7/10+ = Pass (checkpoints/review modules)
   - < target = Flag for fixes

6. **Calculate module average** from all prose activity scores

7. **If module average < target:**
   - Identify specific red flags (template repetition, excessive intensifiers, etc.)
   - Apply fixes using ONLY vocabulary from M01-M{current}
   - Re-score to verify improvement (target: 8/10+)

**Common fixes:**
- Break template repetition (vary sentence structures)
- Remove 50% of intensifiers ("дуже", "надзвичайно")
- Add discourse markers (2-3 per 10 sentences)
- Simplify robotic transitions

**If naturalness fixes applied:** Re-run audit (Step 3) to ensure no new violations introduced.

### Step 6: PASS - Run Full Pipeline

When audit passes, run the full validation pipeline:

```bash
# Full pipeline: lint → generate MDX → validate MDX → validate HTML
npm run pipeline l2-uk-en {level} {module_num}
```

**Note:** HTML validation requires dev server running:
```bash
cd docusaurus && pnpm start  # In separate terminal
```

If pipeline fails at any step, fix the issue and re-run.

### Output

**On PASS:**
```
MODULE APPROVED

Audit: PASS
Pipeline: PASS (lint ✓ generate ✓ validate_mdx ✓ validate_html ✓)
MDX: docusaurus/docs/{level}/module-{num}.mdx

Statistics:
- Word count: XXX
- Activities: XX
- Vocabulary: XX words
- Interactive elements: XX
```

**On FAIL (after 3 iterations):**
```
MODULE NEEDS MANUAL REVIEW

Persistent issues:
1. [issue]
2. [issue]

Recommendation: [rebuild from stage X / manual edit / user decision]
```
