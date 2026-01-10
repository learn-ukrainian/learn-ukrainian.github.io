# B1 vs B2 Rebuild - Comparative Analysis

**Date:** 2026-01-10
**Status:** Both levels require comprehensive rebuild
**Priority:** B1 first, then B2 (learn from B1 process)

---

## Executive Summary

Both B1 and B2 levels have critical quality issues requiring systematic fixes. **B2 is in worse condition** with a 1.4% pass rate vs B1's 11%, and requires specialized handling for 61 Ukrainian history modules.

### Key Metrics

| Metric | B1 | B2 | Winner |
|--------|----|----|--------|
| **Pass Rate** | 11% (10/91) | 1.4% (2/145) | 🟢 B1 |
| **Total Violations** | 1,391 | 4,603 | 🟢 B1 |
| **Violations per Module** | 17.2 | 32.2 | 🟢 B1 |
| **Modules** | 91 | 145 (+59%) | - |
| **Estimated Fix Time** | 1-2 weeks | 2-3 weeks | 🟢 B1 |
| **Opus Required** | Phase 2 only | Phases 2-3 | 🟢 B1 |

**Conclusion:** B1 is easier to fix and should be completed first to validate the fix process.

---

## Error Distribution Comparison

### B1 Error Breakdown (1,391 total)

| Category | Count | % | Priority |
|----------|------:|--:|:--------:|
| YAML Schema Violations | 290 | 20.8% | 🔴 P1 |
| Word Count Issues | 565 | 40.6% | 🔴 P1 |
| Missing Required Sections | 150 | 10.8% | 🔴 P1 |
| Empty Required Sections | 150 | 10.8% | 🟡 P2 |
| Activity Density Below Min | 58 | 4.2% | 🟡 P2 |
| Activity Count Below Min | 45 | 3.2% | 🟡 P2 |
| Duplicate Headers | 48 | 3.4% | 🟢 P3 |
| Section Order Issues | 42 | 3.0% | 🟢 P3 |
| Low Immersion | 19 | 1.4% | 🟢 P3 |
| Too Many Morphemes | 24 | 1.7% | 🟢 P3 |

**Dominant issues:** Word count (40.6%), YAML schema (20.8%)

### B2 Error Breakdown (4,603 total)

| Category | Count | % | Priority |
|----------|------:|--:|:--------:|
| COMPLEXITY_WORD_COUNT | 3,030 | 65.8% | 🔴 P1 |
| YAML_SCHEMA_VIOLATION | 734 | 15.9% | 🔴 P1 |
| MISSING_REQUIRED_SECTION | 663 | 14.4% | 🔴 P1 |
| DUPLICATE_SYNONYMOUS_HEADERS | 88 | 1.9% | 🔴 P1 |
| MISSING_REQUIRED_CALLOUT | 47 | 1.0% | 🟡 P2 |
| TOO_MANY_MORPHEMES | 39 | 0.8% | 🟡 P2 |
| EMPTY_REQUIRED_SECTION | 2 | 0.04% | 🔴 P1 |

**Dominant issue:** Complexity word count (65.8% - 2x worse than B1)

---

## Critical Differences

### 1. Complexity Crisis

**B1:** 565 violations (40.6%)
- Sentences need 12-16 words
- Mostly grammar modules

**B2:** 3,030 violations (65.8%)
- Sentences need 10-25 words (higher CEFR target)
- Affects all module types
- **2.5x more sentences to enrich**

**Impact:** B2 requires significantly more LLM work for sentence enrichment.

---

### 2. History Modules

**B1:** None
- Standard grammar/vocabulary/cultural modules

**B2:** 61 history modules (M71-M131)
- **Unique issue:** Missing specialized sections
  - Читання (primary source readings): 80 modules
  - Первинні джерела (document excerpts): 32 modules
  - Деколонізаційний погляд (decolonization): 8 modules
  - Required callouts: 47 modules
- **Requires:** Historical accuracy + cultural authenticity
- **Opus essential:** Cannot mechanically generate historical content

**Impact:** B2 has unique complexity not present in B1.

---

### 3. Template Compliance

**B1:** Mixed template types
- Metalanguage (M01-05): ✅ 100% pass
- Grammar (M06-51): 0% pass
- Vocabulary (M52-71): 0% pass
- Cultural (M72-91): 0% pass

**B2:** Unified template (history-heavy)
- History synthesis (M71-131): 0% pass
- Grammar/Vocab (M01-70): ~3% pass
- Skills & Capstone (M132-145): 0% pass

**Impact:** B1 has more template diversity; B2 is more uniform but specialized.

---

### 4. YAML Schema Issues

**B1:** 290 violations (20.8%)
- Missing `correct_words` in mark-the-words
- Basic schema compliance

**B2:** 734 violations (15.9%)
- Quiz options with invalid properties
- Too few options (<4)
- Deprecated properties
- **2.5x more violations** despite lower percentage

**Impact:** B2 has more activity volume → more YAML to fix.

---

## Fix Strategy Comparison

### B1 Fix Phases (1-2 weeks)

| Phase | Focus | Scripts | Impact | Model |
|-------|-------|---------|--------|-------|
| 1 | Structure | 1-3 | 1,005 errors (72%) | Sonnet |
| 2 | Activities | 4-6 | 253 errors (18%) | Opus |
| 3 | Polish | 7-10 | 133 errors (10%) | Sonnet |

**Total:** 10 scripts, mostly automated

### B2 Fix Phases (2-3 weeks)

| Phase | Focus | Scripts | Impact | Model |
|-------|-------|---------|--------|-------|
| 1 | Structure | 1-4 | 752 errors (16%) | Sonnet |
| 2 | History | 5-8 | 207+ errors (5%) | **Opus** |
| 3 | Complexity | 9-11 | 3,030 errors (66%) | **Opus** |
| 4 | Review | 12 | 614 errors (13%) | Manual |

**Total:** 12 scripts, **heavy Opus usage**

---

## Opus Cost Analysis

### B1 Opus Usage

**Phase 2 only (Scripts 3-6):**
- Sentence extension: ~565 sentences
- Activity generation: ~100 activities
- Section population: ~150 sections

**Estimated tokens:** ~500K input + 1M output = 1.5M tokens
**Cost:** ~$22.50 (at $15/1M input, $75/1M output)

### B2 Opus Usage

**Phases 2-3 (Scripts 5-11):**
- Historical content generation:
  - Читання sections: 80 × 400 words = 32K words
  - Первинні джерела: 32 × 300 words = 9.6K words
  - Callouts: 47 × 150 words = 7K words
- Sentence extension: ~3,030 sentences
- Activity enrichment: ~200 activities

**Estimated tokens:** ~3M input + 6M output = 9M tokens
**Cost:** ~$495 (at $15/1M input, $75/1M output)

**B2 costs 22x more than B1 for Opus usage** due to:
1. 5.4x more sentences to enrich
2. Specialized historical content generation
3. Cultural authenticity requirements

---

## Risk Assessment

### B1 Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Bad sentence extensions | Medium | High | 30% manual review |
| Template misalignment | Low | Medium | Validate against templates |
| Activity quality issues | Medium | Medium | Quality gates in audit |
| Rework needed | Low | Low | Test on M11-15 first |

**Overall risk:** 🟡 Moderate (manageable with testing)

### B2 Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Historical inaccuracies | Medium | **Critical** | Expert review required |
| Cultural inauthenticity | Medium | **High** | Decolonization perspective check |
| Sentence complexity mismatch | High | High | B2 CEFR validation |
| Opus cost overrun | Medium | Medium | Budget $500-600 |
| Rework needed | Medium | High | Test on M71-75 first |

**Overall risk:** 🔴 High (requires expert validation)

---

## Recommended Execution Order

### Option 1: Sequential (Recommended)

**Week 1-2: B1 Rebuild**
1. Implement all 10 B1 scripts
2. Test on M11-15
3. Apply to all B1 modules
4. Achieve 95%+ pass rate
5. **Learn lessons for B2**

**Week 3-5: B2 Rebuild**
1. Apply lessons from B1
2. Implement B2-specific scripts (history content)
3. Use Opus for complexity enrichment
4. Expert review of history modules
5. Achieve 95%+ pass rate

**Advantages:**
- Validate process on simpler B1 first
- Learn from mistakes before expensive B2 work
- Reduce risk of B2 rework
- Can cancel B2 if B1 approach fails

**Disadvantages:**
- Takes 4-5 weeks total
- B2 remains broken longer

### Option 2: Parallel

**Week 1-3: Both levels simultaneously**
- Run scripts in parallel
- Split work between two developers/agents

**Advantages:**
- Faster overall completion (3 weeks)

**Disadvantages:**
- Higher risk (no learning from B1)
- Potential B2 rework if B1 approach fails
- Higher cognitive load
- Opus costs hit all at once

**Recommendation:** **Option 1 (Sequential)** - Validate process on B1, then apply to B2.

---

## Success Criteria

### B1 Success Metrics

- [ ] Pass rate ≥ 95% (87/91 modules)
- [ ] All checkpoints pass (M15, M25, M41, M51)
- [ ] Pipeline validation passes
- [ ] YAML schema 100% compliant
- [ ] Template compliance ≥ 95%

### B2 Success Metrics

- [ ] Pass rate ≥ 95% (138/145 modules)
- [ ] All history modules complete (M71-M131)
- [ ] Complexity targets met (95%+ sentences B2-level)
- [ ] Historical accuracy validated
- [ ] Cultural authenticity confirmed
- [ ] Pipeline validation passes

---

## Lessons from Audit

### What Went Wrong

Both levels show **systematic template non-compliance**, indicating:

1. **Templates evolved after content creation**
   - B1 M01-10 (early modules) pass → created with templates
   - B1 M11-91 (later modules) fail → templates changed or ignored

2. **Inconsistent quality enforcement**
   - No automated validation during creation
   - Audit system came after modules were built
   - Quality degraded over time

3. **CEFR complexity targets not met**
   - B1 sentences too simple (12-word target → 8-word reality)
   - B2 sentences way too simple (16-word target → 6-word reality)
   - Indicates rushed content generation

4. **YAML schema violations**
   - Schema evolved (added `correct_words` requirement)
   - Old modules not updated retroactively

### Preventing Future Issues

**For future levels (C1, C2):**

1. ✅ **Create comprehensive templates FIRST**
2. ✅ **Run audit DURING creation** (not after)
3. ✅ **Enforce quality gates** (block merge if audit fails)
4. ✅ **Use Opus for content generation** from day 1
5. ✅ **Validate samples** before batch generation
6. ✅ **Test pipeline early** (M01-05 as proof of concept)

---

## Tracking Issues

- **B1 Rebuild:** [Issue #403](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/403)
- **B2 Rebuild:** [Issue #404](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/404)

Both issues include:
- Detailed error breakdowns
- Implementation checklists
- Model recommendations
- Timeline estimates
- Success criteria

---

## Next Steps

1. **Review this comparison** - Understand B1 vs B2 differences
2. **Decide execution order** - Sequential (recommended) or Parallel
3. **Start with B1** - Validate process on simpler level
4. **Budget for B2** - Allocate $500-600 for Opus usage
5. **Plan expert review** - Line up Ukrainian historian for B2 M71-M131 validation

---

**Author:** Claude Sonnet 4.5
**Audited:** 236 modules (91 B1 + 145 B2)
**Documentation:** 16 files, ~1.4MB total
