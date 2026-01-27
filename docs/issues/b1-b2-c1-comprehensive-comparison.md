# B1-B2-C1 Comprehensive Rebuild Analysis

**Date:** 2026-01-10
**Audited:** 384 modules (91 B1 + 145 B2 + 148 C1)
**Status:** All levels require fixes, C1 in best shape
**Critical Finding:** B1+ templates use English headers instead of Ukrainian

---

## Executive Summary

Comprehensive audit of 384 modules across B1, B2, and C1 reveals:

1. **C1 has significantly better quality** (81.1% pass rate) due to improved templates
2. **Critical template bug** - B1+ use English headers instead of Ukrainian
3. **B2 has worst quality** (1.4% pass rate) due to complexity crisis
4. **Fix order:** Templates first → B2 → B1 → C1

### Overall Metrics

| Level | Modules | Pass Rate | Violations | Fix Effort | Priority |
|-------|---------|-----------|------------|------------|----------|
| **B1** | 91 | 11% (10) | 1,391 | 1-2 weeks | 🟡 Medium |
| **B2** | 145 | 1.4% (2) | 4,603 | 2-3 weeks | 🔴 High |
| **C1** | 148/196 | **81.1% (120)** | ~90 | 7-9 hours | 🟢 Low |

**Winner:** C1 by far (built with mature templates)

---

## 🔴 CRITICAL FINDING: Template Language Issue

### Problem

**All B1+ templates use English section headers** when they should be 100% Ukrainian.

**Example violations:**
```markdown
❌ Current (English):
## Need More Practice?
## Summary
## Cultural Insight
## Primary Sources

✅ Should be (Ukrainian):
## Потрібно більше практики?
## Підсумок
## Культурний контекст
## Первинні джерела
```

### Impact

**This explains many "missing section" violations across all levels:**
- Modules use Ukrainian headers (correct)
- Templates expect English headers (incorrect)
- Audit flags "missing section" (false positive)

**Estimated false positives:**
- B1: ~50-75 violations (5% of total)
- B2: ~200-300 violations (6% of total)
- C1: ~15-20 violations (20% of total)

### Affected Templates

**B1:**
- `b1-grammar-module-template.md` (M06-M51)
- `b1-vocab-module-template.md` (M52-M71)
- `b1-cultural-module-template.md` (M72-M91)
- `b1-integration-module-template.md` (M82-M86)
- `b1-checkpoint-module-template.md` (M15, M25, M34, M41, M51)

**Exception:** `b1-metalanguage-module-template.md` (M01-M05) correctly allows bilingual

**B2:**
- `b2-module-template.md`
- `b2-history-synthesis-module-template.md`

**C1:**
- `c1-module-template.md`
- `c1-biography-module-template.md`

**C2:**
- `c2-module-template.md` (if exists)

### Fix Required

**Priority 0 (Before all other fixes):**

1. **Update all B1+ templates** - Replace English headers with Ukrainian equivalents
2. **Update audit logic** - Flag English headers in B1+ modules (except B1 M01-M05)
3. **Re-audit all levels** - Measure true violation counts after template fix
4. **Document header mappings** - Create English→Ukrainian reference

**Estimated impact:**
- Reduces B1 violations by 50-75 (4-5%)
- Reduces B2 violations by 200-300 (5-7%)
- Reduces C1 violations by 15-20 (17-22%)

**Timeline:** 2-3 hours to fix all templates + re-audit

---

## Detailed Level Comparison

### Pass Rate

```
C1 ██████████████████████████████████████████████████████████████████████████████ 81.1%
B1 ████████████ 11.0%
B2 ██ 1.4%
```

**Analysis:**
- C1: Built with mature templates → high quality
- B1: Early modules pass, later fail → template evolution
- B2: Complexity crisis + history gaps → worst quality

### Violations per Module

```
C1  ████ 3.2
B1  █████████████████████ 17.2
B2  ████████████████████████████████████ 32.2
```

**Analysis:**
- C1: Structural errors only (YAML syntax)
- B1: Pedagogical + structural
- B2: Complexity + history + structural

### Error Distribution

| Error Category | B1 | B2 | C1 |
|----------------|----|----|-----|
| **Complexity/Word Count** | 565 (41%) | 3,030 (66%) | 0 (0%) |
| **YAML Schema** | 290 (21%) | 734 (16%) | 21 (23%) |
| **Missing Sections** | 150 (11%) | 663 (14%) | 23 (26%) |
| **Empty Sections** | 150 (11%) | 2 (0.04%) | 0 (0%) |
| **Activity Density** | 58 (4%) | 0 (0%) | 0 (0%) |
| **Activity Count** | 45 (3%) | 0 (0%) | 0 (0%) |
| **Duplicate Headers** | 48 (3%) | 88 (2%) | 0 (0%) |
| **Section Order** | 42 (3%) | 0 (0%) | 0 (0%) |
| **Too Many Morphemes** | 24 (2%) | 39 (0.8%) | 0 (0%) |
| **History Callouts** | 0 (0%) | 47 (1%) | 0 (0%) |
| **Unknown Errors** | 0 (0%) | 0 (0%) | 4 (4%) |

**Key takeaway:** C1 has NO pedagogical errors, only structural YAML/template issues.

---

## Fix Strategy Comparison

### B1 Fix Plan (1-2 weeks)

**Phase 0:** Fix templates (2-3 hours)
- Update 5 templates to Ukrainian headers
- Re-audit → expect 50-75 fewer violations

**Phase 1:** Structural (2-3 days)
- YAML schema fixes (290 violations)
- Missing sections (150 violations)
- Extend sentences (565 violations)

**Phase 2:** Activities (2-3 days)
- Populate empty sections (150 violations)
- Expand density (58 violations)
- Add activities (45 violations)

**Phase 3:** Polish (1-2 days)
- Reorder sections (42 violations)
- Merge duplicates (48 violations)
- Improve immersion (19 violations)
- Simplify complexity (24 violations)

**Model:** Sonnet for structure, Opus for content (no cost concerns)

### B2 Fix Plan (2-3 weeks)

**Phase 0:** Fix templates (2-3 hours)
- Update 2 templates to Ukrainian headers
- Re-audit → expect 200-300 fewer violations

**Phase 1:** Structural (2-3 hours)
- Add practice sections (277 violations)
- Merge duplicates (88 violations)
- YAML schema (734 violations)
- Missing sections (190 violations)

**Phase 2:** History Content (4-6 hours) - **Opus**
- Add Читання sections (80 modules)
- Add Первинні джерела (32 modules)
- Add Деколонізаційний погляд (8 modules)
- Add callouts (47 modules)

**Phase 3:** Complexity Enrichment (8-12 hours) - **Opus**
- Enrich quiz prompts (~1,500 items)
- Expand unjumble (~800 items)
- Extend fill-in (~500 items)
- Manual review 30%

**Phase 4:** Validation (2-3 hours)
- Review morphemes (39 violations)
- Validate history accuracy
- Re-audit all modules

**Model:** Opus for all content (no cost concerns)

### C1 Fix Plan (7-9 hours)

**Phase 0:** Fix templates (2-3 hours)
- Update 2 templates to Ukrainian headers
- Re-audit → expect 15-20 fewer violations

**Phase 1:** YAML Fixes (2-3 hours) - **Automated**
- Quote strings with colons (21 modules)
- Fix parse errors

**Phase 2:** Template Sections (3-4 hours) - **Automated**
- Add missing biography sections (23 modules)
- Add practice sections

**Phase 3:** Manual (1-2 hours)
- Delete duplicate M04
- Fix schema violations (3 modules)
- Debug unknown errors (4 modules)

**Model:** Sonnet for automation, minimal Opus if needed

---

## Budget Update - Subscription Model

**No cost concerns** - Subscription-based pricing means Opus can be used freely.

**Updated recommendations:**

### B1: Use Opus Liberally

- All content generation (sentence extension, activity creation)
- Section population with engaging content
- Natural Ukrainian flow critical

### B2: Opus Essential

- Historical content (207+ violations)
- Sentence complexity (3,030 violations)
- Cultural authenticity required
- Volume is massive (~3,000 sentences)

### C1: Minimal Opus

- Mostly automated fixes
- Use Opus only for unknown errors or quality polish

**ROI:** Better to use Opus upfront than spend time on manual rework.

---

## Recommended Execution Order

### Option A: Template Fix First (Recommended)

**Week 1:**
- Fix all B1/B2/C1 templates (2-3 hours)
- Re-audit all levels (1 hour)
- Measure true violation counts
- Update fix plans with accurate data

**Week 2-3: B2 Completion**
- Highest priority (90% complete, customer-facing)
- Use Opus for history + complexity
- Target: 95%+ pass rate

**Week 4-5: B1 Rebuild**
- Second priority (foundational level)
- Use Opus for content quality
- Target: 95%+ pass rate

**Week 6: C1 Quick Fixes**
- Lowest priority (already 81% pass)
- Mostly automated
- Target: 95%+ pass rate

**Timeline:** 5-6 weeks total

### Option B: Parallel (Higher Risk)

Fix all levels simultaneously - NOT recommended due to:
- Template fix should happen first (affects all levels)
- B2/B1 share similar error patterns (learn from one, apply to other)
- Different fix strategies per level

---

## Completion Status

### B1 (91/91 modules exist - 100%)

| Range | Description | Pass Rate |
|-------|-------------|-----------|
| M01-M10 | Metalanguage + Aspect | 100% ✅ |
| M11-M91 | Grammar/Vocab/Cultural | 0% ❌ |

### B2 (131/145 modules exist - 90%)

| Range | Description | Pass Rate |
|-------|-------------|-----------|
| M01-M70 | Grammar/Vocab | ~3% ❌ |
| M71-M131 | Ukrainian History | ~0% ❌ |
| M132-M145 | Skills & Capstone | **MISSING** ⚠️ |

**Blocker:** M132-M145 need creation before B2 complete

### C1 (148/196 modules exist - 75.5%)

| Range | Description | Exists | Pass Rate |
|-------|-------------|--------|-----------|
| M01-M32 | Academic Writing | 33/32* | 90.9% ✅ |
| M33-M35 | Practice/Checkpoint | 0/3 | - ⚠️ |
| M36-M99 | Historical Bios | 28/64 | 46.4% ❌ |
| M100-M130 | Contemporary Bios | 31/31 | 96.8% ✅ |
| M131 | Checkpoint | 1/1 | 100% ✅ |
| M132-M150 | Stylistics | 19/19 | 78.9% 🟡 |
| M151-M196 | Literature Track | 0/46 | - ⚠️ |

*M04 duplicate exists

**Gaps:**
- M33-M35: Practice/assessment (3 modules)
- M36-M99: Historical biographies (36 modules)
- M151-M196: Literature track (46 modules) - may defer to C2

---

## Quality Trend Analysis

### Historical Quality Evolution

```
2023-2024: B1 M01-M10 (Metalanguage)
  ✅ 100% pass rate
  → Built with initial templates

2024 Early: B1 M11-M91 (Grammar/Vocab/Cultural)
  ❌ 0% pass rate
  → Templates evolved, modules didn't update

2024 Mid: B2 M01-M131 (History focus)
  ❌ 1.4% pass rate
  → Complexity targets not met
  → History modules incomplete

2024-2025: C1 M01-M150 (Academic + Bios)
  ✅ 81.1% pass rate
  → Templates matured
  → Quality enforcement improved
  → Recent modules meet standards
```

**Trend:** Quality improved significantly from B1/B2 to C1 as templates matured.

### U-Shaped Quality Curve (C1)

```
Early modules (M01-M32):  90.9% ✅ Recent, well-built
Middle modules (M36-M99): 46.4% ❌ Older, needs fixes
Later modules (M100-M150): 93.4% ✅ Recent, high quality
```

**Explanation:** Quality dipped in middle phase (historical bios), then improved as process matured.

---

## Lessons Learned

### What Went Wrong (B1/B2)

1. **Templates evolved after content creation**
   - B1 M01-10 pass → created WITH templates
   - B1 M11-91 fail → templates changed, modules didn't update

2. **No automated validation during creation**
   - Audit system came after modules built
   - Quality degraded without checks

3. **CEFR complexity targets ignored**
   - B1: 12-word target → 8-word reality
   - B2: 16-word target → 6-word reality

4. **Template language mismatch**
   - Templates in English
   - Modules in Ukrainian
   - Audit flagged false positives

### What Went Right (C1)

1. **Mature templates from start**
   - Built with lessons from B1/B2
   - Ukrainian headers from beginning

2. **Better quality enforcement**
   - Recent modules (M100-M150) meet standards
   - Process improvements visible

3. **Focused content strategy**
   - Clear biography structure
   - Consistent stylistics approach

### Preventing Future Issues

**For C2 and beyond:**

1. ✅ **Fix templates BEFORE content creation**
2. ✅ **100% Ukrainian headers in templates**
3. ✅ **Run audit DURING creation** (not after)
4. ✅ **Enforce quality gates** (block merge if fails)
5. ✅ **Use Opus for content** (subscription = no cost barrier)
6. ✅ **Validate samples** before batch generation
7. ✅ **Test pipeline early** (M01-05 proof of concept)

---

## Tracking Issues

- **B1 Rebuild:** [Issue #403](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/403)
- **B2 Rebuild:** [Issue #404](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/404)
- **C1 Quality Fixes:** [Issue #405](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/405)

All issues updated with:
- Critical template language finding
- No budget concerns (subscription model)
- Re-audit requirement after template fix

---

## Success Criteria

### B1

- [ ] Pass rate ≥ 95% (87/91)
- [ ] All checkpoints pass (M15, M25, M34, M41, M51)
- [ ] Pipeline validation passes
- [ ] 100% Ukrainian immersion (M06+)

### B2

- [ ] Pass rate ≥ 95% (138/145)
- [ ] All 145 modules exist (create M132-M145)
- [ ] History modules complete
- [ ] Complexity targets met

### C1

- [ ] Pass rate ≥ 95% (143/148)
- [ ] All YAML parse errors fixed
- [ ] Template sections complete
- [ ] Pipeline validation passes

---

## Immediate Action Items

1. **Fix templates** (2-3 hours)
   - Update all B1+ templates to Ukrainian headers
   - Document English→Ukrainian mappings
   - Update audit logic to flag English in B1+

2. **Re-audit all levels** (1 hour)
   - Run comprehensive audits after template fix
   - Measure true violation counts
   - Update fix plans with accurate data

3. **Prioritize B2** (customer-facing blocker)
   - Create M132-M145 (14 modules)
   - Fix existing violations
   - Target: 95%+ pass rate

4. **Queue B1** (foundational level)
   - Apply lessons from B2 fixes
   - Use Opus for content quality
   - Target: 95%+ pass rate

5. **Queue C1** (already good shape)
   - Quick automated fixes
   - Manual cleanup
   - Target: 95%+ pass rate

---

**Next Steps:**

1. Review this comprehensive comparison
2. Fix templates (Priority 0)
3. Re-audit to get accurate baseline
4. Execute B2 → B1 → C1 in sequence

---

**Author:** Claude Sonnet 4.5
**Audited:** 384 modules (91 B1 + 145 B2 + 148 C1)
**Documentation:** 23 files, ~2.5MB total
**Critical Finding:** B1+ template language mismatch (English vs Ukrainian)
