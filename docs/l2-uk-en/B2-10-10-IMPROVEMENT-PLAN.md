# B2 Curriculum: Path to 10/10

**Created:** 2025-01-31
**Current Score:** 4.9/10
**Target Score:** 10/10

---

## Standardized Scoring (Consistent Across All Levels)

| Criterion | Weight | Score | Weighted |
|-----------|--------|-------|----------|
| Grammar/Content coverage | 15% | 8/10 | 1.20 |
| Vocabulary coverage | 10% | 3/10 | 0.30 |
| Skills balance | 15% | 6/10 | 0.90 |
| State Standard compliance | 15% | 7/10 | 1.05 |
| CEFR alignment | 10% | 6/10 | 0.60 |
| Internal consistency | 10% | 4/10 | 0.40 |
| Checkpoint structure | 10% | 8/10 | 0.80 |
| Audit pass rate | 15% | 0/10 | 0.00 |
| **Total** | 100% | — | **4.9/10** |

---

## Current State

| Metric | Value | Status |
|--------|-------|--------|
| Total Modules | 94 | ✅ Complete |
| Audit Pass Rate | 0% (0/94) | 🔴 All failing |
| Primary Blocker | Outline compliance | 🔴 |
| Vocabulary | 5-7 items vs 25+ | ⚠️ |

---

## Critical Blockers

### Blocker 1: Outline Compliance Errors (ALL 94 MODULES)

**Issue:** Content sections don't match planned outlines in YAML plans.

**Pattern:** Each module has 3-7 "Outline Compliance Errors"

**Root Cause:** Content was written with different section structure than what plans specify.

**Fix Strategy:**
1. Either update plans to match existing content structure
2. Or rewrite content to match plans

**Recommendation:** Update plans to match content (less work, content already reviewed)

### Blocker 2: Missing Required Activity Types

| Activity Type | Modules Missing | Count |
|---------------|-----------------|-------|
| `reading` | M07-94 (almost all) | ~87 |
| `essay-response` | M30, M70, M79 | 3 |
| `fill-in-the-blank` | M52-66 | 15 |
| `true-false` | M38, M40, M49, M80-81, M84 | 6 |

**Fix:** Add missing activity types to each module's activities.yaml

### Blocker 3: Forbidden Activity Types (M71-94)

**Issue:** Modules M71-82 have 8-12 "forbidden activity types"

**Cause:** Old activity schema used, now invalid

**Fix:** Run `--fix` flag or manually convert to valid types

### Blocker 4: Word Count Shortfalls

| Phase | Target | Actual Range | Gap |
|-------|--------|--------------|-----|
| M01-10 | 3800 | 1717-2481 | 35-55% short |
| M11-20 | 3800 | 1858-3120 | 18-51% short |
| M21-70 | 2000 | 1750-2930 | OK to +47% |
| M71-94 | 2000 | 1787-3032 | OK to +52% |

**Priority:** M01-20 need significant content expansion

---

## Issue #422 Status (Communication Skills M85-94)

**Current:** Plans exist, content exists, but ALL failing audits

**Specific Issues:**
- M85-86: Missing from curriculum.yaml (slug inconsistency)
- M85-94: Outline compliance errors
- M85-94: Missing reading activities

**To Complete Issue #422:**
1. Fix curriculum.yaml slugs for M85-86
2. Fix outline compliance in plans
3. Add reading activities
4. Re-run audits

---

## Phase 1: Fix Systemic Audit Blockers (Critical)

### 1.1 Fix Outline Compliance

**Approach A (Recommended):** Update plans to match existing content

```bash
# For each module, compare:
# 1. Plan content_outline sections
# 2. Actual markdown ## headers
# Update plan to match content
```

**Estimated effort:** 2-3 minutes per module × 94 = ~5 hours

### 1.2 Add Missing Activity Types

**Script approach:**
```bash
# Generate reading activity template
# Append to each activities.yaml that's missing it
```

**Estimated effort:** 1 minute per module × 87 = ~1.5 hours

### 1.3 Fix Forbidden Activity Types

```bash
.venv/bin/python scripts/audit_module.py --fix curriculum/l2-uk-en/b2/71-medytsyna-pohlybleno.md
# Repeat for M71-82
```

**Estimated effort:** 12 modules × 5 minutes = ~1 hour

### 1.4 Fix curriculum.yaml Slug Inconsistency

```yaml
# Current (WRONG):
- professional-email-basics
- professional-email-advanced

# Correct:
- 85-professional-email-basics
- 86-professional-email-advanced
```

---

## Phase 2: Expand Word Counts (High Priority)

### 2.1 Target Modules

| Module | Current | Target | Need |
|--------|---------|--------|------|
| M01 | 1943 | 3800 | +1857 words |
| M02 | 2124 | 3800 | +1676 words |
| M03 | 1925 | 3800 | +1875 words |
| M04 | 1962 | 3800 | +1838 words |
| M05 | 1904 | 3800 | +1896 words |
| M06 | 2114 | 3800 | +1686 words |
| M10 | 1717 | 3500 | +1783 words |

**Approach:** Add deeper explanations, more examples, practice sections

**Estimated effort:** 30 min per module × 10 = ~5 hours

---

## Phase 3: Vocabulary Expansion (Medium Priority)

### 3.1 Current State

- Target: 25+ items per module
- Actual: 5-7 items per module
- Gap: ~18 items per module × 94 modules = ~1700 missing items

### 3.2 Strategy

Focus on high-impact modules first:
1. Register modules (M15-25): 10 modules × 20 items = 200 items
2. Idiom modules (M45-54): 10 modules × 20 items = 200 items
3. Domain vocab (M26-28, M71-76): 10 modules × 20 items = 200 items

**Estimated effort:** 5 minutes per item × 600 = ~50 hours (can be batched)

---

## Phase 4: State Standard Verification

### 4.1 B2 State Standard Requirements

Per STATE-STANDARD-COMPLIANCE-ANALYSIS.md:

1. ✅ Passive voice forms (all types) - M01-10
2. ✅ Aspect nuances - M41-42
3. ✅ Participles - M07-09
4. ✅ Complex syntax - M11-14, M43-44
5. ✅ Register awareness - M15-25
6. ⚠️ Needs verification after content fixes

### 4.2 Action

After Phase 1-3, run State Standard audit:
```bash
.venv/bin/python scripts/validate_state_standard.py b2
```

---

## Phase 5: Skills Production (Medium Priority)

### 5.1 Current Skills Modules

| Phase | Modules | Skills |
|-------|---------|--------|
| B2.3 | M71-84 | Integration, reading, academic writing |
| B2.4 | M85-94 | Professional email, reports, presentations, debates |

### 5.2 Missing Elements

- Speaking rubrics for M91-93
- Free writing tasks (essay-response) in M85-88
- Listening comprehension (audio requirements not specified)

---

## Implementation Checklist

### Phase 1: Systemic Fixes (Week 1) — 8 hours
- [ ] Fix outline compliance for all 94 modules
- [ ] Add reading activities to 87 modules
- [ ] Run --fix for forbidden activities in M71-82
- [ ] Fix curriculum.yaml slugs for M85-86
- [ ] Re-run full audit: `audit-level b2`

### Phase 2: Word Count Expansion (Week 2) — 5 hours
- [ ] Expand M01-M10 content (+1700 words each)
- [ ] Re-run audits for expanded modules

### Phase 3: Vocabulary (Week 3-4) — 50 hours (can parallelize)
- [ ] Expand vocabulary for M15-25 (register modules)
- [ ] Expand vocabulary for M45-54 (idiom modules)
- [ ] Expand vocabulary for domain modules

### Phase 4: State Standard (Week 5) — 4 hours
- [ ] Run State Standard validation
- [ ] Fix any gaps identified
- [ ] Update compliance documentation

### Phase 5: Skills Enhancement (Week 6) — 8 hours
- [ ] Add speaking rubrics to M91-93
- [ ] Add free writing tasks to M85-88
- [ ] Specify audio requirements

### Phase 6: Final Validation (Week 7) — 4 hours
- [ ] Full audit pass for all 94 modules
- [ ] Naturalness validation (Ukrainian grammar)
- [ ] Documentation update

---

## Success Criteria (10/10)

| Criterion | Requirement |
|-----------|-------------|
| Audit pass rate | 94/94 modules passing (100%) |
| Word counts | All modules meet targets |
| Activities | All required types present |
| Vocabulary | 25+ items per module |
| State Standard | All Каталог В requirements verified |
| CEFR B2 | All can-do statements covered |
| Documentation | All refs updated and consistent |

---

## Estimated Total Effort

| Phase | Hours | Priority |
|-------|-------|----------|
| Phase 1: Systemic Fixes | 8 | Critical |
| Phase 2: Word Count | 5 | High |
| Phase 3: Vocabulary | 50 | Medium |
| Phase 4: State Standard | 4 | Medium |
| Phase 5: Skills | 8 | Medium |
| Phase 6: Validation | 4 | Low |
| **Total** | **79 hours** | — |

**Note:** Phase 3 (vocabulary) can be parallelized or batched over time.

---

## B2 Scorecard Summary

| Criterion | Score | Notes |
|-----------|-------|-------|
| Grammar coverage | 8/10 | Plans comprehensive |
| Vocabulary coverage | 3/10 | 5-7 items vs 25+ target |
| Skills coverage | 6/10 | Plans exist, execution pending |
| State Standard compliance | 7/10 | Needs verification |
| CEFR B2 alignment | 6/10 | Plans aligned |
| Internal consistency | 4/10 | Outline mismatches |
| Audit pass rate | 0/10 | 0% passing |
| **Overall** | **2.1/10** | Blocked by audit failures |

---

## References

- Issue #422: B2 Communication Skills Expansion (M85-94)
- `docs/B2-STATUS.md` - Current audit status
- `claude_extensions/quick-ref/b2.md` - B2 workflow
- `docs/l2-uk-en/STATE-STANDARD-COMPLIANCE-ANALYSIS.md`
