# Deep Review Workflow Optimization Guide

**For use with review-content-v4 when doing final quality validation.**

---

## Philosophy

**Quality is non-negotiable. This is for a nation's education.**

These optimizations improve **workflow efficiency** without compromising **quality standards**.

---

## Pre-Review Preparation

### 1. Ensure Quick Review Passed

Before starting deep review, module should have:
- ✅ Passed quick review (no obvious issues)
- ✅ Passed technical audit (scripts/audit_module.sh)
- ✅ No duplicated content or AI patterns

**Don't waste deep review time on issues quick review catches.**

### 2. Batch Context Loading

**Load all files at once** (parallel reads):

```markdown
Read these files in parallel:
- curriculum/l2-uk-en/{level}/{slug}.md
- curriculum/l2-uk-en/{level}/activities/{slug}.yaml
- curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml
- curriculum/l2-uk-en/plans/{level}/{slug}.yaml
```

**Why:** Single context load vs. multiple requests = faster.

### 3. Have Audit Log Ready

```bash
# Run audit first, save log
scripts/audit_module.sh curriculum/l2-uk-en/{level}/{slug}.md

# Deep review can reference: curriculum/l2-uk-en/{level}/audit/{slug}-audit.log
```

**Why:** I can see what technical issues exist before reviewing.

---

## Review Strategy Optimizations

### 1. Structured Reading Order

**Don't read randomly. Follow this order:**

```
1. Read plan file (know what SHOULD be there)
2. Read audit log (know what issues exist)
3. Read content .md (verify against plan)
4. Read activities (check each type systematically)
5. Read vocabulary (spot-check)
```

**Why:** Context → expectations → verification = fewer iterations.

### 2. Section-by-Section Verification

**For content.md, go section by section:**

```markdown
## For each section:
1. Check: Is this in the plan outline? ✓
2. Check: Word count appropriate? ✓
3. Verify: 2-3 Ukrainian sentences (grammar)
4. Verify: Examples support claims
5. Note issues immediately, fix at end
```

**Why:** Systematic = complete coverage, no redundant re-reading.

### 3. Activity Type Batching

**Check activities by type, not sequentially:**

```markdown
1. All quiz items together (check answer correctness)
2. All fill-in together (check grammatical fit)
3. All error-correction together (verify errors)
4. etc.
```

**Why:** Context switching is expensive. Batch similar checks.

### 4. Fix in Batches

**Don't fix issues as you find them. Batch them:**

```markdown
## Issues Found (collect during review):
- Line 45: Russicism "кушать" → "їсти"
- Line 89: Calque "це є" → "це"
- Activity 7, Item 3: Wrong case
- Activity 12, Item 1: Duplicate of Activity 5

## Then fix all at once (fewer edits, faster)
```

**Why:** Fewer Edit tool calls = faster completion.

---

## Dimension Scoring Optimization

### 1. Score During Review (Not After)

**As you verify each section, note dimension scores:**

```markdown
## Section 1 verification:
- Language: Found 1 Russicism (score: 7)
- Educational: Clear explanations (score: 9)
- Coherence: Good flow (score: 9)

## Section 2 verification:
- Language: Perfect (score: 10)
- Activities: 2 wrong answers (score: 6)
```

**Why:** Don't re-read entire module to score later.

### 2. Use Scoring Shortcuts

**Quick dimension assessment:**

- **9-10**: No issues found in this dimension
- **7-8**: 1-2 minor issues
- **5-6**: 3-4 issues
- **<5**: Many issues or critical failures

**Why:** Precise scoring vs. approximate is same outcome if both pass/fail threshold.

---

## Fix Application Strategy

### 1. Triage Fixes

**Critical (fix immediately):**
- Russianisms, calques (auto-fail)
- Wrong activity answers (auto-fail)
- Grammar errors in examples

**Important (batch at end):**
- Unnatural phrasing
- Better example suggestions
- Tone improvements

**Optional (note only):**
- Minor style preferences
- Enhancement ideas

**Why:** Focus deep review time on quality gates.

### 2. Use Replace-All for Patterns

**If same error appears multiple times:**

```markdown
Found "це є" in lines 23, 45, 67, 89
→ Use Edit with replace_all=true
```

**Why:** One fix vs. four edits = 4x faster.

### 3. Activity YAML Fixes

**For activity errors, fix entire file at once:**

```markdown
Read activities/{slug}.yaml
Fix all issues in single Write/Edit
Don't make 10 separate edits
```

**Why:** Fewer tool calls, maintain YAML structure.

---

## Quality vs. Speed Trade-offs

### What We CAN Optimize (No Quality Loss)

✅ **Workflow order** (systematic vs. random)
✅ **Batch operations** (group similar checks)
✅ **Parallel loading** (all files at once)
✅ **Fix batching** (collect issues, fix together)
✅ **Dimension scoring** (during review, not after)

### What We CANNOT Optimize (Quality Required)

❌ **Skip sections** (must verify all)
❌ **Sample activities** (must check all items)
❌ **Approximate Ukrainian** (every sentence must be correct)
❌ **Lower thresholds** (8.5+ overall, dimension thresholds fixed)
❌ **Skip linguistic claims** (must verify all grammar rules)

**Mission**: This is for Ukrainian nation's education. Quality is sacred.

---

## Estimated Time Savings

**Traditional approach:** 30-40 minutes per module
**Optimized approach:** 20-25 minutes per module

**Savings:** ~35% time reduction
**Quality impact:** Zero (same verification, better workflow)

---

## Batch Review Strategy

### For Multiple Modules

**If reviewing 5-10 modules:**

```markdown
1. Load all plan files at once (parallel)
2. Load all audit logs at once
3. Review modules sequentially (keep context)
4. Batch common fixes across modules
```

**Why:** Shared context, pattern recognition across modules.

### Warning on Batch Size

**Don't review more than 10 modules in one session:**
- Context overflow risk
- Fatigue affects quality
- Better: 5 modules, break, 5 more

---

## When to Use Deep Review

### Required (No Exceptions)

✅ Before releasing any module to users
✅ Before marking level as "complete"
✅ For modules that failed quick review badly
✅ When module impacts critical learning (aspect, cases, motion verbs)

### Can Defer (Resource Constraints)

⏳ Modules still in draft
⏳ Content not yet ready for users
⏳ Minor topic modules (can batch later)
⏳ Experimental content

**Strategy:**
1. Use quick review during A1-C1 content generation
2. Batch deep reviews by level when content complete
3. Deep review all before public release

---

## Checklist for Efficient Deep Review

**Before starting:**
- [ ] Module passed quick review
- [ ] Audit log generated and ready
- [ ] All files loaded in parallel
- [ ] Plan file read (know expectations)

**During review:**
- [ ] Follow systematic section order
- [ ] Batch activity checks by type
- [ ] Note issues (don't fix immediately)
- [ ] Score dimensions during verification

**After verification:**
- [ ] Batch fix all issues at once
- [ ] Re-run audit to verify
- [ ] Write comprehensive report

**Time target:** 20-25 minutes for standard module

---

## Remember

**Optimization Goal:** Work smarter, not lower standards

**Quality Standards:** Non-negotiable
- Ukrainian must be perfect (native quality)
- All gates must pass (✅)
- No shortcuts on verification
- This is for a nation's future

**Resource Reality:** Limited resources now
- Quick review during content generation
- Deep review batch before release
- Strategic use of expensive validation

**Long-term Mission:**
Fighting for Ukrainian language, culture, and heritage.
Content quality reflects respect for this mission.

---

**END OF OPTIMIZATION GUIDE**
