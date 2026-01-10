# B1/B2 Activity Complexity Reduction Proposal

**Date:** January 10, 2026
**Context:** Apply C1's successful activity reduction strategy to B1/B2 for workload relief while maintaining quality

---

## C1 Reduction Success Story

**What happened in C1:**
- Content-based modules (Biography, History, Literature) reduced from **16+ → 10-12 activities** (~35% reduction)
- Standard academic modules kept at 16+
- User feedback: "it helped a lot"

**Templates affected:**
- `c1-biography-module-template.md`: 10-12 activities
- `c1-literature-module-template.md`: 10-12 activities
- History modules in `MODULE-RICHNESS-GUIDELINES-v2.md`: 10-12 activities

**Philosophy:** "Focus on quality over quantity"

---

## Current B1/B2 Requirements

### Activity Count

| Level | Current  | Items/Activity | Module Types                        |
| ----- | -------- | -------------- | ----------------------------------- |
| B1    | **12+**  | **14+**        | Grammar, Vocab, Cultural, Checkpoint |
| B2    | **14+**  | **16+**        | Grammar, Vocab, History (M71-131)   |

### Mandatory Activity Mix (B1)

From `MODULE-RICHNESS-GUIDELINES-v2.md` lines 315-331:

- fill-in: 2+
- match-up: 1+
- quiz: 1+
- true-false: 1+
- group-sort: 1+
- unjumble: 2+
- error-correction: 2+
- cloze: 1+
- mark-the-words: 1+
- select: 1+
- translate: 1+

**Total mandatory types:** 12 minimum

---

## Proposed Reduction Strategy

### Option 1: Uniform Reduction (RECOMMENDED)

**Philosophy:** Same relief across all B1/B2 modules, consistent with C1 content module reduction (~33%)

| Level | Current | Proposed | Reduction | Items/Activity (Current → Proposed) |
| ----- | ------- | -------- | --------- | ----------------------------------- |
| B1    | 12+     | **8-10** | -25%      | 14+ → **12+**                       |
| B2    | 14+     | **10-12** | -25%      | 16+ → **14+**                       |

**Rationale:**
- User wants "big relief" - 25% reduction provides significant workload reduction
- Matches C1's ~33% reduction for content modules
- Maintains high quality by requiring fewer but richer activities

### Option 2: Tiered by Module Type

**Philosophy:** Different requirements for grammar-heavy vs. content/vocabulary modules

**B1:**
- Grammar modules (M01-45): **10-11 activities** (keep higher for practice)
- Vocabulary/Cultural (M46-91): **8-9 activities**
- Checkpoints (M15, M25, M34, M41, M51): **12+ activities** (assessment - keep current)

**B2:**
- Grammar modules (M01-40): **12-13 activities**
- History/Content (M71-131): **10-12 activities** (match C1 content modules)
- Vocabulary (M41-70): **10-11 activities**
- Checkpoints: **14+ activities** (keep current)

**Rationale:**
- Grammar needs more controlled practice
- Content modules can use fewer, deeper activities
- Checkpoints remain comprehensive assessments

---

## Impact Analysis

### B1 Rebuild (Issue #403)

**Current audit results:**
- 91 modules, 11% pass rate (10/91)
- 1,391 violations, many from activity count/density

**With Option 1 reduction:**
- Fix #4 (activity density): Currently 58 violations → **Likely reduced to ~20-30 violations**
- Fix #5 (activity count): Currently 45 violations → **Likely reduced to ~15-20 violations**

**Estimated impact:**
- ~73 fewer violations (~5% reduction)
- Easier to achieve 8-10 quality activities than 12+ mediocre ones
- Focus shifts to making existing activities excellent

### B2 Rebuild (Issue #404)

**Current audit results:**
- 145 modules, 1.4% pass rate (2/145)
- 4,603 violations

**B2 has NO activity count/density violations** (0 violations)
- This means current modules either have 14+ activities already OR audit isn't checking this yet

**With Option 1 reduction:**
- History modules (M71-131) would align with C1 content standard: **10-12 activities**
- Reduces pressure during M132-M145 creation (14 missing modules)

---

## Recommended Changes

### 1. Update MODULE-RICHNESS-GUIDELINES-v2.md

**Lines 306-313** - Activity Requirements by Level table:

```markdown
| Level | Activities | Items/Activity | Types | Stage Sequencing                                       |
| ----- | ---------- | -------------- | ----- | ------------------------------------------------------ |
| A1    | 8+         | 12+            | 4+    | Recognition → Production (no stages needed)            |
| A2    | 10+        | 12+            | 5+    | Recognition → Discrimination → Controlled → Production |
| B1    | 8-10       | 12+            | 5+    | Full stage sequence                                    |
| B2    | 10-12      | 14+            | 5+    | Full stage sequence, heavier on production             |
| C1    | 16+        | 18+            | 5+    | Production-heavy, subtle discrimination                |
| C2    | 16+        | 18+            | 5+    | Production-heavy, native-level complexity              |
```

**Note:** C1 content modules (biography, literature, history) use 10-12 activities per their templates

### 2. Update Mandatory Activity Mix

Reduce mandatory activity types for B1/B2 to allow flexibility:

**B1 (Current: 12 mandatory types → Proposed: 8 core types)**

| Activity Type        | Current | Proposed | Rationale                              |
| -------------------- | ------- | -------- | -------------------------------------- |
| fill-in              | 2+      | **1-2**  | Core activity, keep                    |
| match-up             | 1+      | **1**    | Recognition essential                  |
| quiz                 | 1+      | **1**    | Quick check essential                  |
| true-false           | 1+      | opt      | Often redundant with quiz              |
| group-sort           | 1+      | opt      | Can be cognitively overloading         |
| unjumble             | 2+      | **1-2**  | Sentence construction practice         |
| error-correction     | 2+      | **1-2**  | Critical for grammar awareness         |
| cloze                | 1+      | **1**    | Contextual practice                    |
| mark-the-words       | 1+      | opt      | Can be replaced by select              |
| select               | 1+      | opt      | Keep for multi-answer scenarios        |
| translate            | 1+      | **1**    | Production essential                   |

**Mandatory core:** 8 types (fill-in, match-up, quiz, unjumble, error-correction, cloze, translate + 1 flexible)

**B2 (Current: 11 mandatory types → Proposed: 9 core types)**

Similar reduction pattern with emphasis on production activities.

### 3. Update Templates

**Files to update:**

**B1:**
- `docs/l2-uk-en/templates/b1-grammar-module-template.md`
- `docs/l2-uk-en/templates/b1-vocab-module-template.md`
- `docs/l2-uk-en/templates/b1-cultural-module-template.md`
- `docs/l2-uk-en/templates/b1-integration-module-template.md`
- (Keep `b1-checkpoint-module-template.md` at 12+ for comprehensive assessment)

**B2:**
- `docs/l2-uk-en/templates/b2-module-template.md`
- `docs/l2-uk-en/templates/b2-history-synthesis-module-template.md`

**Changes:**
- Activity count: Update checklist from "12+/14+" to "8-10/10-12"
- Items per activity: Update from "14+/16+" to "12+/14+"
- Activity mix table: Update mandatory counts

### 4. Update Audit Logic

**File:** `scripts/audit/checks/activity_density.py`

Update thresholds:

```python
MINIMUM_ACTIVITIES = {
    'a1': 8,
    'a2': 10,
    'b1': 8,   # Changed from 12
    'b2': 10,  # Changed from 14
    'c1': 16,
    'c2': 16
}

MINIMUM_ITEMS_PER_ACTIVITY = {
    'a1': 12,
    'a2': 12,
    'b1': 12,  # Changed from 14
    'b2': 14,  # Changed from 16
    'c1': 18,
    'c2': 18
}
```

---

## Timeline

1. **User approval** of Option 1 or Option 2 (5 min)
2. **Update MODULE-RICHNESS-GUIDELINES-v2.md** (10 min)
3. **Update 6 templates** (30 min)
4. **Update audit thresholds** (5 min)
5. **Re-audit B1** (5 min) → See updated violation counts
6. **Re-audit B2** (5 min) → See updated violation counts
7. **Update GitHub Issues** #403, #404 with new violation counts (10 min)

**Total:** ~70 minutes

---

## Expected Outcomes

### Workload Relief
- **25% fewer activities** to create per module
- **Focus on quality:** 8-10 excellent activities > 12+ mediocre ones
- **Faster module creation:** Less time per module during rebuild

### Quality Improvement
- More time per activity → better distractors, richer contexts
- Clearer activity purpose (each one serves distinct pedagogical goal)
- Less "filler" activities added just to meet count

### Audit Impact
- **B1:** ~73 fewer violations expected (activity count + density)
- **B2:** Minimal immediate impact (no activity violations currently)
- **Easier pass rate:** Modules pass with 8-10 quality activities vs. struggling to reach 12-14

---

## Recommendation

**Approve Option 1: Uniform Reduction**

**Why:**
- Simplest to implement (one threshold per level)
- Consistent with user request for "big relief"
- Matches C1's proven success (~33% reduction)
- Easier to communicate in templates/docs

**Next step:** Await user approval, then implement all changes and re-audit.

---

**Author:** Claude Sonnet 4.5
**Related Issues:** #403 (B1), #404 (B2)
**User Request:** "during c1 we decided to ease on activity complexity, it helped a lot, can you help me to sort this out for b1 and b2 as well? it would give us big relief. but i want to maintain high quality activities but with less quantity"
