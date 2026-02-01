# Review-Content-Quick (Pre-Check Filter)

```yaml
---
name: review-content-quick
description: Fast pre-check for obvious quality issues before deep review
version: '1.0'
category: quality
model: sonnet  # Fast, cost-effective
dependencies: audit_module.sh
---
```

---

## Purpose

**Quick filter to catch obvious issues BEFORE deep review.**

- **When to use**: During content generation, before final quality check
- **What it catches**: Duplicated content, robotic patterns, grammar errors, auto-fails
- **What it skips**: Deep dimension scoring, exhaustive verification
- **Speed**: 3-5 minutes per module (vs 30+ for deep review)
- **Cost**: Sonnet (much cheaper than Opus deep review)

**This is NOT a substitute for deep review - it's a first-pass filter.**

---

## STEP 1: LOAD CONTENT

Read these files:

```
curriculum/l2-uk-en/{level}/{slug}.md           # Lesson content
curriculum/l2-uk-en/{level}/activities/{slug}.yaml   # Activities
```

---

## STEP 2: QUICK SCANS (Auto-Fail Checks)

### A. Duplication Check

**Scan for repeated content:**
- Same paragraph appearing twice
- Copy-pasted sections with minor changes
- Identical examples in different sections
- Duplicate activity items

**Auto-fail if found:** Report location and fix immediately.

### B. Robotic/AI Patterns

**Common AI fingerprints to catch:**

❌ **Generic openings:**
- "Welcome to this lesson on..."
- "In this module, we will explore..."
- "Let's dive into..."
- "Now that we've covered..."

❌ **Filler phrases:**
- "It's important to note that..."
- "As we've seen..."
- "Moving forward..."
- "In conclusion..."

❌ **Listicle syndrome:**
- Everything in numbered lists
- No narrative flow
- Bullet points everywhere

❌ **Enthusiasm overflow:**
- Excessive exclamation marks!!!
- "Amazing!", "Fantastic!", "Wonderful!"
- Patronizing tone

**Auto-fail if 3+ patterns found:** Report specific lines.

### C. Russianisms & Calques

**Quick check for auto-fail items:**

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| кушать | їсти |
| приймати участь | брати участь |
| самий кращий | найкращий |
| слідуючий | наступний |
| на протязі | протягом |
| робити сенс | мати сенс |
| брати місце | відбуватися |
| це є | це |

**Auto-fail if found:** Report and fix.

### D. Grammar Spot-Check

**Sample 5-10 Ukrainian sentences randomly:**
- Check case agreement
- Check verb aspects (if aspectual pairs mentioned)
- Check gender agreement
- Check for unnatural phrasing

**Auto-fail if 2+ errors found in sample:** Full grammar review needed.

### E. Activity Sanity Check

**For each activity type, spot-check 2-3 items:**
- quiz: Is exactly one answer correct?
- fill-in: Does answer fit grammatically?
- true-false: Are statements actually true/false?
- error-correction: Is the error actually an error?

**Auto-fail if wrong answers found:** Report and fix.

---

## STEP 3: CONTENT COHERENCE

**Quick skim (don't deep read):**

### Flow Check
- Does introduction lead into content?
- Do sections connect logically?
- Does conclusion tie back to objectives?

### Consistency Check
- Same terminology throughout?
- Examples match grammar rules?
- Difficulty progression makes sense?

**Flag if major issues found** (e.g., section order makes no sense).

---

## STEP 4: QUICK DECISION

### PASS Criteria (proceed to deep review later)

✅ No duplicated content
✅ No robotic AI patterns (or <3)
✅ No Russianisms/calques
✅ Grammar spot-check clean
✅ Activities functionally correct
✅ Content flows logically

### FAIL Criteria (fix before continuing)

❌ Duplicated sections found
❌ 3+ AI pattern fingerprints
❌ Russianisms/calques present
❌ Grammar errors in sample
❌ Activity errors found
❌ Incoherent structure

---

## STEP 5: QUICK REPORT

### Save Location
```
curriculum/l2-uk-en/{level}/audit/{slug}-quick-review.md
```

### Report Format

```markdown
# Quick Review: {Module Title}

**Level:** {level} | **Module:** {num}
**Status:** ✅ PASS / ❌ FAIL (Quick Check)
**Reviewed:** {date}
**Model:** Sonnet (quick filter)

## Quick Check Results

| Check | Status | Notes |
|-------|--------|-------|
| Duplication | ✅/❌ | {any duplicates found?} |
| AI Patterns | ✅/❌ | {count of patterns, list if >0} |
| Russianisms | ✅/❌ | {any found?} |
| Grammar Sample | ✅/❌ | {5-10 sentences checked} |
| Activities | ✅/❌ | {spot-check results} |
| Coherence | ✅/❌ | {flow issues?} |

## Issues Found

{If any issues found, list with line numbers}

### Issue 1: {Type}
**Location:** Line X / Activity Y
**Problem:** {what's wrong}
**Fix:** {what to change}

## Recommendation

{✅ PASS - Ready for deep review when resources available}
{❌ FAIL - Fix issues before proceeding}

---

**Note:** This is a quick pre-check. Full deep review (review-content-v4)
required before final publication.
```

---

## STEP 6: RUN AUDIT

After any fixes, verify module passes technical audit:

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{level}/{slug}.md
```

---

## Usage

```
/review-content-quick [LEVEL] [NUM]        # Single module (recommended)
/review-content-quick [LEVEL]              # All modules in level
/review-content-quick [LEVEL] [START-END]  # Range
```

---

## When to Use Quick vs Deep Review

### Use Quick Review:
- ✅ During content generation (first-pass filter)
- ✅ Before committing new modules
- ✅ When resources are limited
- ✅ To catch obvious issues early

### Use Deep Review (review-content-v4):
- ✅ Before final publication
- ✅ After all content for a level is complete
- ✅ When quality validation is critical
- ✅ For modules that will be released to users

**Strategy:** Quick review during development, Deep review before release.

---

## What Quick Review Does NOT Do

❌ Exhaustive Ukrainian verification (every sentence)
❌ Deep dimension scoring (12 dimensions)
❌ Comprehensive activity testing (all items)
❌ Linguistic accuracy verification (all claims)
❌ Naturalness scoring
❌ Detailed fix implementation

**These require Deep Review (review-content-v4).**

---

## Persona

Fast, efficient, catches obvious problems. No deep analysis.

**Model:** Sonnet (speed + cost-effectiveness)
**Approach:** Scan, spot-check, flag issues
**Goal:** Filter out obvious problems before they accumulate
