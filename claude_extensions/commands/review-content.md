# Review Content Quality

Evaluate module content for educational quality, coherence, and pedagogical soundness.

## Usage

```
/review-content [LEVEL]                    # Review all modules in level
/review-content [LEVEL] [MODULE_NUM]       # Review single module
/review-content [LEVEL] [START-END]        # Review range of modules
```

## Arguments

- `$ARGUMENTS` - One of:
  - `a1` - Review all A1 modules (1-34)
  - `a1 15` - Review module 15 only
  - `a1 10-20` - Review modules 10 through 20
  - `b2 1-10` - Review B2 modules 1 through 10

## Instructions

Parse arguments: $ARGUMENTS

**Step 1: Determine Scope**
- If only LEVEL provided: Review ALL modules in that level
- If LEVEL + NUMBER: Review single module
- If LEVEL + RANGE (e.g., "10-20"): Review that range
- Find all matching files in `curriculum/l2-uk-en/{level}/`

**Step 2: For Each Module**

### Extract Content
1. Read the module file
2. Extract lesson content (everything BEFORE `## Activities`)
   - Include: Summary, all instructional sections, examples, engagement boxes
   - Exclude: Frontmatter, Activities, Vocabulary, Self-Assessment
3. Extract metadata (title, level, module number, topic)

### Evaluate Quality

Score each criterion 1-5:

**1. Coherence**
- Logical organization and flow
- Clear transitions between sections
- Progressive difficulty (simple → complex)
- Consistent terminology

**2. Relevance**
- Content matches module title
- Examples relate to topic
- Grammar focus appropriate for level
- Vocabulary used matches topic

**3. Educational Value**
- Clear, sufficient explanations
- Varied, meaningful examples
- Inductive discovery patterns (observe-first)
- Follows stated pedagogy (PPP/TBL)
- Engagement boxes add value (not filler)

**4. Language Quality**
- Clear, professional writing
- No excessive repetition (same structure ≥5 times = flag)
- Grammatically correct Ukrainian
- Grammatically correct English explanations
- Consistent terminology
- **No Russisms/Surzhik:** Strictly standard Ukrainian (e.g., use 'так' not 'да', 'будь ласка' not 'пожалуйста', 'звичайно' not 'канешно'). Flag any non-standard usage.

**5. Pedagogical Correctness**
- **Sequence:** Does it teach A before B? (e.g., specific letters before reading words)
- **Scaffolding:** clear step-by-step instructions?
- **Cognitive Load:** Is it too much at once?
- **Accuracy:** Are grammar rules explained correctly?

**6. Natural Immersion (Mixed Language Check)**
- **Natural Flow:** Mixing must feel intentional (e.g., "In Ukrainian, we say **так** for yes"), NOT forced.
- **Syntactic Integrity:** Do NOT break English syntax just to insert a Ukrainian word (e.g., "The **хлопець** goes to the **школа**" -> BAD).
- **No "Denglish":** Sentences should generally be fully English (explanation) or fully Ukrainian (example), with specific exceptions for target vocabulary insertion in clear contexts.
- **Contextual Clarity:** Does the mix help or confuse?
- **Exception:** Checkpoint modules (assessments) are exempt from strict immersion flow checks.

**7. Word Salad Check**
Flag if ANY true:
- Same sentence pattern repeated 5+ times
- Generic filler without substance
- Contradictory explanations
- Examples unrelated to explanations
- Clear auto-generation artifacts

**8. Red Flags (Auto-fail)**
Flag if:
- **Forced Mixing:** "I want to **їсти** the **яблуко**." (Syntactic breakage)
- **Undefined Terms:** Using concepts not yet taught.
- **False Friends:** Using high-level grammar (cases) in A1 without explanation.
- **Russianisms/Surzhik:** Any detection of mixed Ukrainian-Russian forms (unless explicitly teaching *about* Surzhik).

**Step 3: Generate Summary Report**

For each module, output:

```
## Module {num}: {title}

**Scores:** Coherence {X}/5 | Relevance {X}/5 | Educational {X}/5 | Language {X}/5 | Pedagogy {X}/5 | Immersion {X}/5 | **Overall {X}/5**
**Status:** ✅ PASS / ⚠️ NEEDS WORK / ❌ REWRITE

{If not PASS, list 2-3 main issues}
```

**Step 4: Apply Safe Fixes**

For each module with action items, categorize fixes:

**Safe Fixes (Auto-apply):**
- Remove leftover editing notes/meta-commentary
- Fix typos and repetition errors
- Delete redundant paragraphs (exact duplicates)
- Remove factually incorrect statements
- Clean up formatting artifacts

**Risky Fixes (Report only):**
- Structural changes
- Rewriting sections for clarity
- Changing word count significantly
- Subjective improvements

For safe fixes:
1. Apply the fix to the module file
2. Run `python3 scripts/audit_module.py {file_path}` to verify still passes
3. If audit fails, revert the fix
4. Mark fix status in review: ✅ FIXED or ❌ SKIPPED

**Step 5: Save Review Files**

For each module, save detailed review to:
`curriculum/l2-uk-en/{level}/review/{module_number}-{slug}-review.md`

Example: `curriculum/l2-uk-en/a1/review/03-the-gender-code-review.md`

**Step 6: Generate Final Summary**

After reviewing all modules in scope:

```
# Content Quality Summary

**Level:** {level}
**Modules Reviewed:** {count}
**Date:** {today}

---

## Overview

| Status | Count | Modules |
|--------|-------|---------|
| ✅ PASS (≥4/5) | {count} | {list} |
| ⚠️ NEEDS WORK (3/5) | {count} | {list} |
| ❌ REWRITE (<3/5) | {count} | {list} |

---

## Module Reports

{Full report for each module}

---

## Detailed Module: {module_number} - {title}

**Overall Score:** {X}/5 {stars}

### Scores Breakdown
- Coherence: {X}/5 {reason}
- Relevance: {X}/5 {reason}
- Educational: {X}/5 {reason}
- Language: {X}/5 {reason}
- Pedagogy: {X}/5 {reason}
- Immersion: {X}/5 {reason}
- Word Salad: ❌ No / ⚠️ Yes

### Strengths
- {strength 1}
- {strength 2}
- {strength 3}

### Issues
- **[Category]** {specific issue with line/example}
- **[Category]** {specific issue with line/example}

### Examples
{Quote 1-2 specific problematic or exemplary passages}

> "{quoted text}"
- Issue: {what's wrong}
- Fix: {how to fix}

### Recommendation
{✅ PASS / ⚠️ NEEDS IMPROVEMENT / ❌ REWRITE}

### Action Items
1. {specific, actionable fix} [SAFE/RISKY]
   - ✅ FIXED / ❌ SKIPPED / ⏳ MANUAL (if risky)
2. {specific, actionable fix} [SAFE/RISKY]
   - ✅ FIXED / ❌ SKIPPED / ⏳ MANUAL (if risky)
3. {specific, actionable fix} [SAFE/RISKY]
   - ✅ FIXED / ❌ SKIPPED / ⏳ MANUAL (if risky)

---

{Repeat for each module}

---

## Priority Fixes

### Critical (Must Fix)
{List modules with score < 3 or word salad}

### Important (Should Fix)
{List modules with score = 3}

### Optional (Nice to Have)
{List modules with score = 4 but minor issues}

---

## Patterns Across Level

### Common Strengths
- {pattern seen in multiple modules}
- {pattern seen in multiple modules}

### Common Issues
- {pattern seen in multiple modules}
- {pattern seen in multiple modules}

### Recommendations
1. {level-wide improvement suggestion}
2. {level-wide improvement suggestion}
3. {level-wide improvement suggestion}
```

## Scoring Scale

| Score | Rating | Meaning |
|-------|--------|---------|
| 5 | Excellent | No issues, exemplary quality |
| 4 | Good | Minor issues, overall strong |
| 3 | Acceptable | Several issues, needs improvement |
| 2 | Poor | Major issues, requires significant rework |
| 1 | Critical | Fundamental flaws, complete rewrite |

## Example Usage

```bash
# Review all A1 modules
/review-content a1

# Review single module
/review-content a2 19

# Review range
/review-content b1 1-10

# Review checkpoint modules in A1
/review-content a1 10 20 34
```

## Performance Notes

- **Single module:** ~30 seconds
- **10 modules:** ~5 minutes
- **Full level (34 modules):** ~15 minutes
- **Full level (80 modules):** ~40 minutes

For large batches, the command will show progress:
```
Reviewing A1...
[1/34] Module 01... ✅ PASS (4.5/5)
[2/34] Module 02... ⚠️ NEEDS WORK (3/5)
...
```

## What Gets Checked

✅ **Checked:**
- Lesson content (instructional text)
- Examples and explanations
- Engagement boxes
- Topic consistency
- Language quality
- Pedagogical approach

❌ **Not Checked:**
- Activities (separate audit)
- Vocabulary tables (separate audit)
- Frontmatter metadata
- Self-assessment sections

## Important Notes

1. **Focus on teaching quality**, not just format
2. **Be specific** - quote actual problematic text
3. **Provide actionable fixes** - not vague suggestions
4. **Score honestly** - don't inflate for "effort"
5. **Check both languages** - Ukrainian examples AND English explanations
6. **Context matters** - what's good at A1 may be weak at C1
7. **Auto-fix safe issues** - apply safe fixes, run audit, verify pass
8. **Save to review/ folder** - don't append to gemini/ folder anymore

## Red Flags (Auto-fail)

These trigger automatic REWRITE recommendation:
- ❌ Word salad detected
- ❌ Overall score < 2/5
- ❌ Teaching wrong grammar for level
- ❌ Examples completely unrelated to topic
- ❌ No actual teaching content (just filler)
- ❌ Contradictory explanations
- ❌ **Unnatural Language Mixing:** (e.g., "The **чоловiк** is walking" -> BAD. "The word for man is **чоловік**" -> GOOD).
- ❌ **Pedagogical Leaps:** Testing material that wasn't taught.
