# GitHub Issues Update - December 27, 2025

## Summary

Updated all YAML migration and B1-related issues to reflect current state of the project after YAML-first workflow validation.

---

## Issues Updated

### 1. Issue #323: Phase 3: B1 Migration ✅ UPDATED

**Status:** Changed from "conversion workflow" to "recreation workflow"

**Key Changes:**
- Documented M22 experiment results (8 min vs 36 min)
- Updated strategy: Drop old activities, recreate from scratch in YAML
- Added parallel execution plan (4 agents, ~1 hour total)
- Updated task breakdown by batch (M23-M25, M26-M34, M35-M41, M42-M51)
- Listed all updated documentation files

**Current Progress:**
- 24/85 modules have YAML activities (M01-M22, M52-M53)
- 29 modules pending YAML recreation (M23-M51)
- 32 modules not yet created (M54-M85)

**Link:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/323

---

### 2. Issue #276: [B1] Build modules 01-85 ✅ UPDATED

**Status:** Updated with accurate phase breakdown and current progress

**Key Changes:**
- Updated phase table with detailed status (✅/⏳/❌)
- Added "Next Steps" section with parallel execution plan
- Documented YAML-first workflow (8 minutes per module)
- Updated workflow commands with correct paths
- Listed recent progress (Dec 27)

**Current Progress:**
- M01-M22: ✅ Complete
- M52-M53: ✅ Complete
- M23-M51: ⏳ YAML pending
- M54-M85: ❌ Not started

**Link:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/276

---

### 3. Issue #312: Epic: YAML Activity Migration ✅ UPDATED

**Status:** Completely restructured to reflect validated workflow

**Key Changes:**
- Marked Phase 1 (Infrastructure) as SKIPPED with rationale
- Marked Phase 1.5 (Dry Run) as SKIPPED
- Updated Phase 2 as COMPLETE (validated via M22 experiment)
- Updated Phase 3 as IN PROGRESS (24/85 B1 modules)
- Added current status summary table (all levels)
- Updated success metrics with proven results
- Listed key documents (removed deprecated ones)

**Major Decision:**
- Skipped JSON Schema infrastructure → Use example-based learning instead
- Skipped formal B2 pilot → Validated with B1 M22 instead
- 50% time savings proven (8 min vs 36 min)

**Link:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/312

---

### 4. Issue #311: Staged Generation Architecture ✅ UPDATED

**Status:** Marked as COMPLETE - all scripts exist and are operational

**Key Changes:**
- Updated "Scripts to Build" section - all ✅ COMPLETE
- Added "Claude Skills" section listing deployed commands
- Added "Workflow Integration" showing active usage
- Listed all hard/soft gates with validation status
- Updated richness metrics table with validation status
- Changed status from "to implement" to "operational with optional enhancements"

**Scripts Deployed:**
- `generate_skeleton.py` ✅
- `check_gate.py` ✅
- `extract_for_activities.py` ✅
- `calculate_richness.py` ✅

**Link:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/311

---

### 5. Issue #300: [EPIC] B1 Complete Implementation ✅ UPDATED

**Status:** Updated with current progress (28% complete)

**Key Changes:**
- Added "Current Status" section with 24/85 progress
- Updated phase table with granular status per phase
- Added "Next Steps" with immediate actions (M23-M51)
- Updated subtasks with current status
- Added quality gates section
- Removed completed subtask (#298 - templates exist)

**Current Progress:**
- B1.0-B1.1: ✅ Complete (M01-M15)
- B1.2: ✅ Mostly complete (M16-M22)
- B1.3-B1.4: ⏳ Content exists, YAML pending
- B1.5: 🔄 Partial (M52-M53 only)
- B1.6-B1.8: ❌ Not started

**Link:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/300

---

## Issues Closed

### 6. Issue #321: Regression testing ✅ CLOSED

**Reason:** Completed via alternative approach

**Explanation:**
- Formal regression test suite not needed
- Validation achieved through M17-M22 practical testing
- Audit + pipeline workflow provides sufficient confidence
- MDX + HTML validation catches real-world issues

**Validation workflow:**
1. Audit script validates structure and content
2. Pipeline generates MDX from YAML
3. MDX validator checks for content loss
4. HTML validator checks browser rendering
5. Manual spot-checks for quality

**Link:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/321

---

### 7. Issue #322: Phase 2: B2 Pilot ✅ CLOSED

**Reason:** Phase skipped - validated workflow via different approach

**Explanation:**
- Original plan: Create 10 B2 modules to test YAML-first workflow
- What we did: Validated workflow with B1 M22 recreation experiment
- Result: Proven 50% time reduction (8 min vs 36 min)
- Decision Gate 2: PASSED

**Why B1 M22 was better validation:**
1. Tested migration workflow (more complex than creation)
2. Proven time savings with real data
3. System ready for production use
4. All prompts updated for YAML-first approach

**Next:** Proceeding directly to Phase 3 (B1 M23-M51) with validated workflow

**Link:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/322

---

## Issues Reviewed (No Changes Needed)

### 8. Issue #275: [A2] Complete Stage 4 review

**Status:** Still relevant, pending YAML migration

**Reason:** A2 has 57 .md files but 0 YAML activities. This issue will be relevant after A2 YAML migration (Issue #324) is complete.

---

### 9. Issues #324, #325: A1/A2 Migration & Cleanup

**Status:** Still relevant, pending B1 completion

**Reason:** These are future work after B1 M23-M51 migration completes.

---

### 10. Issues #301-303: B2/C1/C2 Epics

**Status:** Still relevant, pending B1 completion

**Reason:** These levels will use YAML-first workflow from the start (no migration needed).

---

### 11. Issues #277, #264, #267: B2/C1/C2 Build Tasks

**Status:** Still relevant, pending B1 completion

**Reason:** Future work - no updates needed yet.

---

### 12. Issues #278, #279, #281, #263, #266: Vocabulary Finalization

**Status:** Still relevant, pending module completion

**Reason:** These run after all modules in each level are complete.

---

### 13. Issues #304, #238-240: YouTube Content

**Status:** Still relevant, ongoing work

**Reason:** Can be done in parallel with module creation.

---

### 14. Issues #299, #242, #236: Enhancements

**Status:** Still relevant, low priority

**Reason:** Optional improvements, not blockers.

---

## Summary Statistics

**Total Issues Reviewed:** 20+

**Issues Updated:** 5
- #323 (Phase 3 B1 Migration)
- #276 (B1 Build)
- #312 (YAML Migration Epic)
- #311 (Staged Generation Architecture)
- #300 (B1 Epic)

**Issues Closed:** 2
- #321 (Regression Testing - completed via alternative approach)
- #322 (B2 Pilot - skipped, validated via M22 instead)

**Issues Unchanged:** 13+ (still relevant for future work)

---

## Key Decisions Documented

1. **YAML-First Workflow Validated:** 50% faster than MD conversion (8 min vs 36 min)
2. **Migration Strategy:** Drop old activities, recreate from scratch
3. **Parallel Execution Ready:** 4 agents can work simultaneously on different batches
4. **Infrastructure Complete:** All staged generation scripts exist and are operational
5. **Templates Deployed:** All prompts updated for YAML-first workflow

---

## Next Steps

**Immediate (Today/Tomorrow):**
1. Start parallel execution on M23-M51 (29 modules, ~1 hour)
2. Validate batch results
3. Proceed to M54-M85 creation (32 modules, ~4 hours)

**After B1 Complete:**
1. Migrate A1 modules to YAML (34 modules)
2. Migrate A2 modules to YAML (50 modules)
3. Create B2/C1/C2 modules with YAML-first workflow

---

## Blockers

**None** - System is ready for parallel execution.

All prompts, scripts, and documentation are up-to-date and aligned with the validated YAML-first workflow.
