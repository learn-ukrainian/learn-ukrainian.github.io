# B1 Rebuild - Audit & Fix Documentation Index

**Date:** 2026-01-10
**Status:** Audit complete, batch fixes needed

---

## Quick Summary

**Current Status:**
- 10/91 modules pass audit (11% pass rate)
- 1,391 violations across 81 failing modules
- Only modules M01-10 are clean (metalanguage + early aspect)

**Target After Fixes:**
- 95%+ pass rate (86+/91 modules)
- All modules compliant with B1 templates and richness guidelines

---

## Documentation Files

### 1. Quick Summary (Start Here)

**File:** `b1-audit-quick-summary.md`

**Contents:**
- Error summary table (10 error categories)
- Status visualization by module range
- Top 5 issues with fix strategies
- Impact analysis (priority ranking)
- Example errors from modules 11 & 52
- Timeline estimate (1-2 weeks)

**Best for:** High-level overview, decision making

---

### 2. Comprehensive Analysis

**File:** `b1-rebuild-audit-summary.md`

**Contents:**
- Executive summary
- Detailed error category analysis (all 10 categories)
- Error patterns and examples
- Modules that pass (detailed list)
- Action plan with batch fix strategy
- Template alignment recommendations
- Scripts to implement (overview)
- Questions for review
- Appendix with module status breakdown

**Best for:** Deep analysis, planning fix strategy

---

### 3. Implementation Checklist

**File:** `b1-fix-scripts-needed.md`

**Contents:**
- 10 scripts to implement (detailed specs)
- Priority ranking (P1: Critical, P2: High, P3: Quality)
- Implementation pseudocode for each script
- Test cases for validation
- Week-by-week implementation order
- Success criteria
- Testing strategy (unit, integration, regression)

**Best for:** Implementation planning, developer handoff

---

### 4. Full Audit Report (Raw Data)

**File:** `b1-rebuild-audit-report.md` (473KB)

**Contents:**
- Complete audit output for all 91 modules
- Detailed violation logs for each failing module
- Gate status (words, activities, density, etc.)
- Pedagogical violations with line-by-line fixes

**Best for:** Debugging specific modules, detailed investigation

**Note:** This file is too large to read in one pass. Use grep/search to find specific modules or error types.

---

## Key Findings

### Error Distribution

| Error Category | Count | Modules | Priority |
|---|---:|---:|:---:|
| YAML Schema Violations | 290 | 81 | 🔴 P1 |
| Word Count Issues | 565 | 51 | 🔴 P1 |
| Missing Required Sections | 150 | 42 | 🔴 P1 |
| Empty Required Sections | 150 | 81 | 🟡 P2 |
| Activity Density Below Min | 58 | 58 | 🟡 P2 |
| Activity Count Below Min | 45 | 45 | 🟡 P2 |

**Total:** 1,391 violations across 81 modules

### Module Status by Range

```
M01-10 (Metalanguage + Aspect)      [10/10] ✅✅✅✅✅ 100%
M11-15 (Aspect cont.)               [ 0/ 5] ❌❌❌❌❌ 0%
M16-25 (Motion Verbs)               [ 0/10] ❌❌❌❌❌ 0%
M26-34 (Complex Sentences I)        [ 0/ 9] ❌❌❌❌❌ 0%
M35-41 (Complex Sentences II)       [ 0/ 7] ❌❌❌❌❌ 0%
M42-51 (Advanced Grammar)           [ 0/10] ❌❌❌❌❌ 0%
M52-71 (Vocabulary)                 [ 0/20] ❌❌❌❌❌ 0%
M72-91 (Cultural/Integration)       [ 0/20] ❌❌❌❌❌ 0%
```

---

## Recommended Reading Order

### For Decision Makers

1. **Quick Summary** (`b1-audit-quick-summary.md`)
2. **Implementation Checklist** (timeline section only)
3. **Comprehensive Analysis** (executive summary + recommendations)

### For Implementers

1. **Implementation Checklist** (`b1-fix-scripts-needed.md`) - Full read
2. **Comprehensive Analysis** (`b1-rebuild-audit-summary.md`) - Error patterns section
3. **Full Audit Report** (`b1-rebuild-audit-report.md`) - As needed for debugging

### For Reviewers/QA

1. **Quick Summary** (error categories + examples)
2. **Full Audit Report** (specific modules being tested)

---

## Next Steps

### Immediate (This Week)

1. **Review documentation** → Confirm fix strategy
2. **Prioritize scripts** → Decide implementation order
3. **Set up testing** → Sample modules for validation

### Short-term (Week 1-2)

4. **Implement P1 scripts** → YAML schema, missing sections, word count
5. **Test on M11-15** → Validate fixes work correctly
6. **Batch apply to B1** → Run fixes on all 81 modules

### Long-term (Week 3)

7. **Implement P2-P3 scripts** → Activity quality, cleanup
8. **Re-audit all B1** → Validate 95%+ pass rate
9. **Run pipeline** → Generate MDX and validate HTML
10. **Update templates** → Prevent future violations

---

## Success Metrics

**Current State:**
- Pass rate: 11% (10/91)
- Violations: 1,391
- Clean modules: M01-10 only

**Target State:**
- Pass rate: 95%+ (86+/91)
- Violations: <70 (edge cases)
- Clean modules: M01-91

**Validation:**
```bash
# Audit entire level
.venv/bin/python scripts/audit_level.py l2-uk-en b1

# Generate output
npm run pipeline l2-uk-en b1

# Validate HTML
npm run validate:html l2-uk-en b1
```

---

## Questions or Issues?

**Template Compliance:**
- Should "Потрібно більше практики?" be required or optional?
- Should checkpoint modules auto-generate grammar reference sections?

**Immersion Targets:**
- Should motion modules (M17-24) have lower immersion targets due to complexity?

**Morpheme Complexity:**
- Should fill-in allow prefixed motion verbs (при-йти, ви-йти)?

**Review these questions in:** `b1-rebuild-audit-summary.md` (Questions for Review section)

---

## File Locations

All files in: `/Users/krisztiankoos/projects/learn-ukrainian/docs/issues/`

- `b1-audit-quick-summary.md` (5KB) - Quick overview
- `b1-rebuild-audit-summary.md` (13KB) - Comprehensive analysis
- `b1-fix-scripts-needed.md` (10KB) - Implementation checklist
- `b1-rebuild-audit-report.md` (473KB) - Full raw data
- `b1-rebuild-index.md` (this file) - Navigation guide

---

**Generated:** 2026-01-10 by comprehensive B1 audit
**Next Update:** After Phase 1 fixes (YAML schema, missing sections, word count)
