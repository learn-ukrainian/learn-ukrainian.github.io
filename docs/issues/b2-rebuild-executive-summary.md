# B2 Rebuild - Executive Summary

**Date:** 2026-01-10
**Audit Status:** 🚨 CRITICAL
**Pass Rate:** 1.4% (2/145 modules)
**Total Violations:** 4,603

---

## TL;DR

B2 level has **severe template non-compliance** with only 2 passing modules out of 145. The main issues are:

1. **65.8% of errors:** Sentences too short for B2 complexity (3,030 violations)
2. **15.9% of errors:** Invalid YAML activity schemas (734 violations)
3. **14.4% of errors:** Missing required template sections (663 violations)
4. **History modules (M71-M131):** Missing specialized sections (Читання, Первинні джерела, Деколонізаційний погляд)

**Fix Timeline:** 16-24 hours over 2 weeks (similar to B1 but +33% effort due to history content)

---

## Key Metrics

| Metric | Value | Context |
|--------|-------|---------|
| **Pass Rate** | 1.4% (2/145) | Worse than B1 (8.8%) |
| **Total Violations** | 4,603 | +64% more than B1 (~2,800) |
| **Complexity Issues** | 3,030 (65.8%) | +153% vs B1 (~1,200) |
| **YAML Schema Errors** | 734 (15.9%) | +22% vs B1 (~600) |
| **Missing Sections** | 663 (14.4%) | -22% vs B1 (~850) |
| **Duplicate Headers** | 88 (1.9%) | History modules primarily |

---

## Passing Modules (Use as Reference)

✅ **M102: Franko, Lesia Ukrainka, Hrinchenko**
- Biography module with full template compliance
- All history-specific sections present
- Clean YAML, B2 complexity met

✅ **M105: UNR and ZUNR**
- History module with decolonization perspective
- Primary sources integrated
- Required callouts (`[!myth-buster]`, `[!history-bite]`)

**Observation:** Both passing modules are in the M91-M110 range, suggesting this batch was created/updated more recently with current templates.

---

## Top 5 Error Categories

### 1. COMPLEXITY_WORD_COUNT (3,030 violations, 65.8%)

**Problem:** Sentences in activities are too short for B2 level.

**B2 Targets:**
- Quiz prompts: 10-25 words (actual: 3-9 words)
- Unjumble: 10-18 words (actual: 3-7 words)
- Fill-in: 12-20 words (actual: 5-10 words)

**Root Cause:** Activities reused from A2/B1 without enrichment.

**Fix:** LLM-assisted sentence expansion (Phase 3, 8-12 hours)

---

### 2. YAML_SCHEMA_VIOLATION (734 violations, 15.9%)

**Problem:** Activity YAML files don't validate against current schema.

**Common errors:**
- Quiz options with `explanation` property (should be in markdown `[!explanation]`)
- Quiz/select activities with <4 options (need ≥4)
- Fill-in with deprecated `blank_index` property
- True-false with invalid `context` property

**Root Cause:** Schema evolution not applied to existing YAML.

**Fix:** Automated migration script (Phase 1, <1 hour)

---

### 3. MISSING_REQUIRED_SECTION (663 violations, 14.4%)

**Problem:** Modules missing template-required sections.

**Most common:**
- `Need More Practice?` - 277 modules (ALL levels)
- `Grammar/Presentation` - 190 modules (M01-M51)
- `Читання` - 80 modules (M71-M131 history)
- `Первинні джерела` - 32 modules (M71-M131 history)

**Root Cause:** Modules created before template standardization.

**Fix:**
- Automated section insertion (Phase 1, 2 hours)
- Manual content for history sections (Phase 2, 4-6 hours)

---

### 4. DUPLICATE_SYNONYMOUS_HEADERS (88 violations, 1.9%)

**Problem:** Multiple headers alias to same canonical section.

**Examples:**
- `Вступ` + `Контекст: [Event]` (both = "Introduction")
- `Граматика` + `Презентація` (both = "Grammar")

**Root Cause:** Inconsistent header naming in history modules.

**Fix:** Automated header normalization (Phase 1, <1 hour)

---

### 5. MISSING_REQUIRED_CALLOUT (47 violations, 1.0%)

**Problem:** History modules missing required callouts.

**Missing:**
- `[!myth-buster]` - 24 modules (debunking imperial myths)
- `[!history-bite]` - 23 modules (historical trivia)

**Root Cause:** History template requirements not applied.

**Fix:** Add callout templates with TODO markers (Phase 2, 2 hours)

---

## Module Health Distribution

| Severity | Count | % | Violation Range | Module Examples |
|----------|-------|---|-----------------|-----------------|
| **Critical (30+ violations)** | 31 | 21% | 30-75 | M30, M40, M132-135, M141-145 |
| **High (20-29 violations)** | 59 | 41% | 20-29 | Most M01-M70 grammar/register |
| **Medium (10-19 violations)** | 43 | 30% | 10-19 | Most M71-M131 history |
| **Low (<10 violations)** | 10 | 7% | 1-9 | M101, M103, M107, M110, M83 |
| **Passing (0 violations)** | 2 | 1% | 0 | M102, M105 |

**Worst offenders:** M30 (75), M40 (63), M145 (59), M05 (58)

**Nearly passing:** M83 (6), M103 (6), M107 (7), M27 (9)

---

## Fix Strategy (4 Phases)

### Phase 1: Automated Structural (2-3 hours) ⚡ Quick Wins

**Impact:** Fixes 752 violations (16.3%)

1. Add "Need More Practice?" to all modules
2. Normalize duplicate headers
3. Fix YAML schema violations
4. Add missing grammar sections

**Effort:** Low (scripted)
**Priority:** 🔴 Critical

---

### Phase 2: History Content (4-6 hours) 📚 Manual Work

**Impact:** Fixes 207+ violations, improves 61 modules

1. Add Читання sections (80 modules)
2. Add Первинні джерела (32 modules)
3. Add Деколонізаційний погляд (8 modules)
4. Add required callouts (47 modules)

**Effort:** Medium (template-driven)
**Priority:** 🔴 Critical

---

### Phase 3: Complexity Enrichment (8-12 hours) 🤖 LLM-Assisted

**Impact:** Fixes 3,030 violations (65.8%)

1. Enrich quiz prompts (~1,500 items)
2. Expand unjumble sentences (~800 items)
3. Extend fill-in contexts (~500 items)
4. Manual review 30% sample

**Effort:** High (semi-automated)
**Priority:** ⚠️ High

---

### Phase 4: Validation (2-3 hours) ✅ Quality Check

**Impact:** Quality assurance

1. Review TOO_MANY_MORPHEMES (39 violations)
2. Validate history callout accuracy
3. Re-run comprehensive audit
4. Fix remaining edge cases

**Effort:** Low (validation)
**Priority:** ⚠️ Moderate

---

## Timeline

**Realistic estimate:** 2-3 working days with focused effort

| Week | Days | Phases | Hours | Milestones |
|------|------|--------|-------|------------|
| **Week 1** | Mon-Fri | 1-3 | 14-21h | Automated fixes, history content, enrichment |
| **Week 2** | Mon-Tue | 4 | 2-3h | Validation, edge cases, docs |

**Parallelization:** Phases 2 and 3 can run in parallel after Phase 1.

**Expected final pass rate:** 95%+ (138/145 modules)

---

## B1 vs B2 Comparison

| Aspect | B1 | B2 | Difference |
|--------|----|----|------------|
| Total modules | 91 | 145 | +59% |
| Pass rate | 8.8% | 1.4% | -7.4pp (worse) |
| Total violations | ~2,800 | 4,603 | +64% |
| Complexity issues | ~1,200 | 3,030 | +153% |
| Fix time | 12-18h | 16-24h | +33% |
| History modules | 0 | 61 | Unique to B2 |

**Key insight:** B2 is in worse condition than B1 due to:
1. Higher complexity targets not met (10-25 vs 8-20 words)
2. 61 history modules with specialized requirements
3. More YAML schema violations (+22%)

---

## Critical Success Factors

### Must-Haves for 95%+ Pass Rate

1. ✅ All "Need More Practice?" sections added (277 modules)
2. ✅ All YAML schema violations fixed (734 violations)
3. ✅ All history modules have Читання sections (80 modules)
4. ✅ All quiz prompts enriched to 10-25 words (~1,500 items)
5. ✅ All unjumble sentences expanded to 10-18 words (~800 items)

### Nice-to-Haves for 98%+ Pass Rate

6. ⭐ All fill-in contexts extended (500 items)
7. ⭐ All history callouts factually accurate (47 modules)
8. ⭐ All duplicate headers normalized (88 violations)
9. ⭐ All TOO_MANY_MORPHEMES reviewed and justified (39 violations)

---

## Next Steps

1. **Read full documentation:**
   - [Quick Summary](./b2-audit-quick-summary.md) - 1-page overview
   - [Detailed Analysis](./b2-rebuild-audit-summary.md) - Complete breakdown
   - [Fix Scripts Guide](./b2-fix-scripts-needed.md) - Implementation
   - [Navigation Index](./b2-rebuild-index.md) - Progress tracker

2. **Start Phase 1 (Quick Wins):**
   - Run `fix_b2_missing_need_more.py`
   - Run `fix_b2_duplicate_headers.py`
   - Run `fix_b2_yaml_schema.py`
   - Run `fix_b2_missing_grammar_sections.py`

3. **Re-audit after Phase 1:**
   - Expected: ~750 violations resolved
   - Expected pass rate: ~20-30%

4. **Continue with Phases 2-4**

---

## Documentation Files

| File | Size | Purpose |
|------|------|---------|
| `b2-rebuild-audit-report.md` | 643KB | Full audit logs (145 modules) |
| `b2-audit-quick-summary.md` | 5KB | 1-page quick reference |
| `b2-rebuild-audit-summary.md` | 30KB | Detailed error analysis |
| `b2-fix-scripts-needed.md` | 25KB | Implementation guide + code |
| `b2-rebuild-index.md` | 15KB | Navigation & progress tracker |
| `b2-module-status-table.md` | 8KB | Module-by-module breakdown |
| `b2-rebuild-executive-summary.md` | 5KB | This document |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM enrichment introduces errors | Medium | High | Manual review 30% sample |
| History content requires deep research | Medium | High | Use M102/M105 as templates |
| YAML changes break activities | Low | Critical | Validate after each fix |
| Timeline slips | Medium | Medium | Parallelize Phases 2-3 |
| New violations introduced | Low | High | Re-audit after each phase |

---

## Questions for User

1. **Priority:** Start immediately or after B2 modules 132-145 completion?
2. **Scope:** Fix all 145 modules or prioritize critical range (M71-M131)?
3. **LLM enrichment:** Use Claude/Gemini API for batch enrichment or manual?
4. **History content:** Create full Читання sections or placeholder TODOs?

---

**Status:** Ready to begin Phase 1
**Recommended action:** Run Phase 1 scripts, re-audit, then proceed to Phase 2
**Estimated ROI:** 16-24 hours → 95%+ pass rate (from 1.4%)

---

**Last Updated:** 2026-01-10 by Claude Code
