# Activity Quality & Expansion Plan

**Status**: 🚧 In Progress
**Last Updated**: 2026-01-04
**Tracking Issue**: [#370](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/370)

---

## Executive Summary

**Current Status** (2,903 total activities):
- ✅ **2,680 working** (92.3%)
- ❌ **223 broken** (7.7%)

**Goals**:
1. Fix all 73 broken activities (11 cloze + 62 error-correction)
2. Expand cloze from 8.0% to 10%+ of total activities
3. Ensure 100% of activities pass pedagogy gate

---

## Current Activity Distribution

| Rank | Type | Count | % | Status |
|------|------|-------|---|--------|
| 1 | Quiz | 394 | 13.6% | ✅ Working |
| 2 | Fill-in | 380 | 13.1% | ✅ Working |
| 3 | Match-up | 340 | 11.7% | ✅ Working |
| 4 | Group-sort | 273 | 9.4% | ✅ Working |
| 5 | True-false | 244 | 8.4% | ✅ Working |
| 6 | Unjumble | 239 | 8.2% | ✅ Working |
| 7 | **Cloze** | **233** | **8.0%** | **95% working** |
| 8 | Error-correction | 219 | 7.5% | ⚠️ 72% working |
| 9 | Mark-the-words | 207 | 7.1% | ✅ Working |
| 10 | Translate | 185 | 6.4% | ✅ Working |
| 11 | Select | 173 | 6.0% | ✅ Working |

---

## Broken Activities Breakdown

### Critical Issues

1. **11 cloze activities** - semantic issues (render with `?`)
   - A2: 1 module
   - B1: 5 modules
   - B2: 5 modules
   - **Issue**: [#371](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/371)

2. **62 error-correction activities** - placeholder syntax
   - A2: 10 modules
   - B1: 4 modules
   - B2: 48 modules
   - **Issue**: [#369](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/369)

### Total Impact
- **73 activities need fixing** (2.5% of all activities)

---

## Cloze Activity Deep Dive

### Current Status
- **233 total cloze** (8.0% of all activities)
- **222 working** (95%)
- **11 broken** (5%) - semantic issues

### Distribution by Level
| Level | Total Activities | Cloze Count | Cloze % | Working | Broken |
|-------|-----------------|-------------|---------|---------|--------|
| A1 | 300 | 0 | 0% | 0 | 0 |
| A2 | 560 | 65 | 11.6% | 64 | 1 |
| B1 | 926 | 78 | 8.4% | 73 | 5 |
| B2 | 1,117 | 90 | 8.1% | 85 | 5 |

### Why Expand Cloze?

**Pedagogical advantages**:
- Context-rich learning (full sentences/passages)
- Tests comprehension + grammar + vocabulary simultaneously
- More engaging than isolated exercises
- Natural reading flow with active gaps
- Perfect for aspect, cases, motion verbs, register practice

**Best use cases**:
- Aspect selection (perfective/imperfective in context)
- Case endings (correct case forms)
- Motion verbs (directional + prefixes)
- Register/style (formal vs informal)
- Collocations (natural word combinations)

---

## Implementation Roadmap

### Phase 1: Fix Broken Activities (CRITICAL)
**Timeline**: Week 1-3
**Effort**: Medium

#### Tasks
1. ✅ **Automated fixes applied** (completed in #369)
   - Deleted 221 malformed cloze (dialogue-based)
   - Fixed 5 cloze syntax errors (removed colons)

2. ⏳ **Fix 11 broken cloze** ([#371](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/371))
   - [ ] A2 M37 - action-verb-prefixes
   - [ ] B1 M09 - aspect-future
   - [ ] B1 M10 - aspect-negation
   - [ ] B1 M12 - aspect-pairs-essential-40
   - [ ] B1 M13 - work-week-aspect-in-action
   - [ ] B1 M25 - checkpoint-motion-verbs
   - [ ] B2 M103 - mykhailo-hrushevskyi
   - [ ] B2 M104 - first-world-war (2 activities)
   - [ ] B2 M105 - unr-zunr (2 activities)

3. ⏳ **Rewrite 62 error-correction** ([#369](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/369))
   - See issue for full list
   - Convert placeholder-based exercises to proper error-correction format

**Acceptance Criteria**:
- [ ] All 11 cloze render with dropdown menus (no `?`)
- [ ] All 62 error-correction use real error words in sentences
- [ ] All affected modules pass pedagogy gate
- [ ] MDX regenerated for all fixed modules

---

### Phase 2: Expand Cloze Coverage (ENHANCEMENT)
**Timeline**: Week 4+
**Effort**: High
**Priority**: Low (after Phase 1 complete)

**Target**: Add ~60 new cloze to reach 10% coverage

#### Sub-phases

**2.1: Convert Existing Activities** (Low effort, quick wins)
- [ ] Scan A2/B1/B2 for fill-in with connected context
- [ ] Convert 20-30 activities to cloze format
- **Issue**: [#372](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/372)

**2.2: Create New Cloze** (Medium effort)
- [ ] Add to grammar modules (aspect, cases, motion verbs)
- [ ] Add to cultural modules (reading comprehension)
- [ ] Add to checkpoint modules (integrated review)

**2.3: Quality Enhancement** (High effort)
- [ ] Story-based cloze (200-300 words, 10-15 blanks)
- [ ] Dialogue cloze (authentic conversations)
- [ ] Article cloze (reading comprehension)

**Target Distribution**:
| Level | Current | Target | New Activities Needed |
|-------|---------|--------|----------------------|
| A2 | 65 (11.6%) | 75 (13%) | +10 |
| B1 | 78 (8.4%) | 95 (10%) | +17 |
| B2 | 90 (8.1%) | 120 (10.7%) | +30 |
| **Total** | **233** | **290** | **+57** |

**Acceptance Criteria**:
- [ ] Total cloze count: 290+ (10% of all activities)
- [ ] All new cloze pass audit checks
- [ ] MDX generated and tested
- [ ] No regression in existing activities

---

## Work Assignments

### High Priority (Do First)

**Issue #371** - Fix 11 broken cloze
- **Assignable**: Yes ✅
- **Effort**: 2-4 hours
- **Skills**: YAML editing, Ukrainian grammar
- **Steps**:
  1. Read issue for module list
  2. For each module: inspect → fix → regenerate → test
  3. Mark checkbox when done
  4. Commit with `fix(#371): Fix cloze in {level} M{num}`

**Issue #369** - Rewrite 62 error-correction
- **Assignable**: Yes ✅ (can split into batches)
- **Effort**: 10-15 hours
- **Skills**: YAML editing, Ukrainian grammar, pedagogical design
- **Batches**:
  - Batch 1: A2 (10 modules) - 2-3 hours
  - Batch 2: B1 (4 modules) - 1 hour
  - Batch 3: B2 (48 modules) - 8-10 hours

### Medium Priority (Do After Phase 1)

**Issue #372** - Expand cloze coverage
- **Assignable**: Yes ✅ (can split by sub-phase)
- **Effort**: 20-30 hours
- **Skills**: YAML editing, Ukrainian content creation, pedagogical design
- **Batches**:
  - Batch 1: Convert existing (5-8 hours)
  - Batch 2: Create new (10-15 hours)
  - Batch 3: Quality enhancement (5-7 hours)

---

## Progress Tracking

### Automated Fixes (Completed ✅)
- ✅ Created audit checks for malformed cloze, syntax errors, error-correction
- ✅ Built batch fix script (`scripts/fix_broken_activities.py`)
- ✅ Deleted 221 malformed cloze activities
- ✅ Fixed 5 cloze syntax errors
- ✅ Flagged 62 error-correction for manual rewrite
- ✅ Committed changes (ec8d7c66)

### Manual Fixes (In Progress ⏳)
- ⏳ Fix 11 broken cloze ([#371](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/371))
- ⏳ Rewrite 62 error-correction ([#369](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/369))

### Expansion (Pending 📋)
- 📋 Add 60 new cloze activities ([#372](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/372))

---

## Success Metrics

### Phase 1 (Fix Broken)
- [ ] 100% of activities pass pedagogy gate
- [ ] 0 cloze activities render with `?`
- [ ] 0 error-correction use placeholder syntax
- [ ] All modules regenerate without errors

### Phase 2 (Expand Cloze)
- [ ] Cloze activities reach 10% of total (290+)
- [ ] Cloze distribution balanced across A2/B1/B2
- [ ] Quality: multi-paragraph cloze in each level
- [ ] User feedback: cloze is engaging and effective

---

## Related Documentation

- [Activity Markdown Reference](ACTIVITY-MARKDOWN-REFERENCE.md) - Syntax guide
- [Module Richness Guidelines v2](l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md) - Quality standards
- [Scripts Documentation](SCRIPTS.md) - Generation pipeline

---

## Questions & Support

For questions or clarifications:
- Comment on tracking issue [#370](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/370)
- Tag @krisztiankoos in specific sub-issues
- Use `#activity-quality` tag for filtering

---

**Last Updated**: 2026-01-04
**Next Review**: After Phase 1 completion
