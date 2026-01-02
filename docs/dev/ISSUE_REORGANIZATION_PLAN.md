# GitHub Issue Reorganization Plan

**Date:** 2026-01-02
**Goal:** Separate core content creation (blocking) from quality enhancements (non-blocking)

---

## Philosophy

1. **Core = Content Creation** - Building modules is the primary goal
2. **Quality Enhancements = Important but Non-blocking** - Grammar validation, external resources shouldn't stop content creation
3. **Some systems are outdated** - Grammar queue system is overcomplicated, needs simplification

---

## Issue Categories

### P0 - CORE BLOCKING (Content Creation)

**Active Epics:**

- #301 - [EPIC] B2 Complete Implementation ✅ Keep
- #302 - [EPIC] C1 Complete Implementation ✅ Keep
- #303 - [EPIC] C2 Complete Implementation ✅ Keep
- #347 - Epic: Phase 2 - Complete B2 Level ✅ Keep
- #348 - Epic: Phase 3 - C1/C2 Production ✅ Keep

**Active Content Work:**

- #349 - B2 YAML Migration & Enrichment ✅ Keep (C1-b working, enrichment ongoing)
- #350 - B1 YAML Migration & Enrichment ✅ Keep (19 modules need fixes)
- #351 - [B1.7] Expand with Active Lifestyle Modules ✅ **CLOSED** (completed 2026-01-01)

**Future Content Work:**

- #267 - [C1] Build modules 01-160 ✅ Keep (blocked by B2 completion)
- #264 - [C2] Build modules 01-100 ✅ Keep (blocked by C1 completion)

---

### P1 - QUALITY ENHANCEMENT (Important, Non-blocking)

**External Resources (Podcast Mapping):**

- #334 - Epic: Podcast Data Ingestion ✅ Keep (YAML migration recommended)
- #336 - Phase 1: URL Confirmation & Scrape ⚠️ Reframe as YAML workflow
- #337 - Phase 2: JSON Generation ⚠️ Reframe as YAML workflow
- #338 - Phase 3: Data Extraction & Mapping ⚠️ Reframe as YAML workflow
- #333 - Add Anna Ohoiko podcast ⚠️ Merge into #334

**Recommendation:**

- Keep #334 as parent epic
- Close #336-338 (outdated JSON workflow)
- Create NEW issues:
  - #NEW: Phase 1 - Scrape podcasts to YAML (Season 1-6 + Five Minute Ukrainian)
  - #NEW: Phase 2 - Map podcasts to modules via YAML sidecars
  - #NEW: Phase 3 - Integrate into MDX/HTML output

**Grammar Validation:**

- #311 - Implement Staged Generation with Hard Gates ⚠️ Reframe/Split

**Recommendation:**

- Grammar queue system is outdated/overcomplicated
- Split into two issues:
  - #NEW: Simplify grammar validation (remove queue system, use direct LLM validation)
  - #NEW: Activity format validation (ensure activities are correct)
- Close #311 (too broad, architecture already exists via /module-stage-\* commands)

**Vocabulary Management:**

- #299 - Vocabulary Deduplication Audit Script ✅ Keep (low priority, non-blocking)
- #263 - [C2] Finalize vocabulary ⏸️ Defer (after C2 content complete)
- #266 - [C1] Finalize vocabulary ⏸️ Defer (after C1 content complete)
- #279 - [B2] Finalize vocabulary ⏸️ Defer (after B2 content complete)

---

### P2 - FUTURE/RESEARCH (Defer or Close)

**YouTube Content Finding:**

- #238 - B2 Media: Find YouTube content ⏸️ Defer
- #239 - C1 Media: Find YouTube content ⏸️ Defer
- #240 - C2 Media: Find YouTube content ⏸️ Defer
- #304 - B1 Media: Find YouTube content ⏸️ Defer

**Recommendation:** Low priority - Focus on podcasts first (#334), YouTube later.

**Research/Planning:**

- #236 - Research: Optimal embedding model for Qdrant ⏸️ Defer (RAG not critical path)
- #242 - Plan micro-write as production activity ⏸️ Defer (B1+ feature, not blocking)

---

### CLOSE - Completed or Obsolete

**Completed Work:**

- #275 - [A2] Complete Stage 4 review ❌ CLOSE (A2 is 100% complete)
- #281 - [A2] Finalize vocabulary ❌ CLOSE (A2 vocab complete)
- #277 - [B2] Build modules 01-110 ❌ CLOSE (B2 has 131 modules, target 145, superseded by #301)
- #346 - Epic: Phase 1 - Complete YAML Migration ❌ CLOSE (A1/A2/B1 migration complete)
- #351 - [B1.7] Active Lifestyle Modules ❌ CLOSE (completed 2026-01-01)

**Check if Complete:**

- #340 - Epic: YAML Vocabulary Architecture Migration ❓ CHECK
  - **Sub-issues (must close first):**
    - #342 - Phase 1: YAML Schema & Migration Tooling
    - #343 - Phase 2: A1 Pilot Migration
    - #344 - Phase 3: Manual Vocabulary Enrichment
    - #345 - Phase 4: Full Rollout & Cleanup
  - If migration is done (A1/A2/B1/B2 all use YAML), CLOSE all sub-issues then parent epic
- #312 - Epic: YAML Activity Migration ❓ CHECK
  - Sub-issue #325 (Cleanup and documentation)
  - If all levels use YAML activities, CLOSE
- #325 - Phase 5: Cleanup and documentation ❓ CHECK (part of #312)

---

## Recommended Actions

### Immediate (Close Completed Work)

```bash
# Close A2 completed issues
gh issue close 275 -c "A2 is 100% complete (57/57 modules pass audit + pipeline)"
gh issue close 281 -c "A2 vocabulary finalized and database rebuilt"

# Close superseded B2 issue
gh issue close 277 -c "Superseded by #301 (B2 has 132 modules, not 110)"

# Close completed migration epic
gh issue close 346 -c "Phase 1 complete: A1 (34), A2 (57), B1 (86) all migrated to YAML"
```

### Check Status & Close if Complete

```bash
# Check if YAML migrations are complete
gh issue comment 340 -b "**Status check:** Is YAML vocabulary migration complete for all active levels (A1/A2/B1/B2)? If yes, close this epic."
gh issue comment 312 -b "**Status check:** Are all levels using YAML activities? If yes, close this epic."
gh issue comment 325 -b "**Status check:** Is cleanup/documentation complete? Part of #312."
```

### Reframe Issues

**Grammar Validation (#311):**

```bash
gh issue comment 311 -b "**Reframing recommendation:**

Current scope is too broad. Staged generation architecture already exists via /module-stage-* commands.

**Proposed split:**
1. New issue: Simplify grammar validation (remove queue system, direct LLM validation)
2. New issue: Activity format validation (ensure correct activity syntax)

Close this issue after creating focused replacements."
```

**Podcast Work (#336-338):**

```bash
gh issue comment 334 -b "**Workflow update:**

Original plan used JSON. Recommendation: Use YAML for consistency with vocab/activity architecture.

**Proposed:**
- Close #336, #337, #338 (JSON workflow)
- Create new YAML-based workflow:
  - Phase 1: Scrape to YAML
  - Phase 2: Map to modules via YAML sidecars
  - Phase 3: Integrate into output

Merge #333 into this epic."

gh issue close 336 -c "Replaced by YAML-based podcast workflow under #334"
gh issue close 337 -c "Replaced by YAML-based podcast workflow under #334"
gh issue close 338 -c "Replaced by YAML-based podcast workflow under #334"
gh issue close 333 -c "Merged into #334 (podcast epic)"
```

---

## Priority Order (What to Work On)

### Now (January 2026)

1. ✅ #351 - Finish B1.7 expansion (M82-84) - Agent K in progress
2. ✅ #349 - B2 enrichment (M27-M111) - C1-b in progress
3. ✅ #350 - Fix B1 quality issues (19 modules)

### Next (After B1 Complete)

4. ✅ #301 - Complete B2 (M132-M145: **14 modules remaining**, 131 exist, target 145)
5. ✅ #279 - Finalize B2 vocabulary
6. ✅ #347 - Mark B2 level complete

### Then (After B2 Complete)

7. ✅ #302/#267 - Start C1 (160 modules)
8. 🎧 #334 - Podcast mapping (parallel work, non-blocking)
9. 🎧 Create simplified grammar validation (replace #311)

### Later (After C1 Complete)

10. ✅ #303/#264 - Start C2 (100 modules)
11. 📺 YouTube content finding (#238-240, #304)
12. 🔬 Research tasks (#236, #242)

---

## Summary

**Close:** 7 issues (completed/obsolete)
**Reframe:** 5 issues (podcast YAML workflow, grammar validation split)
**Keep:** 16 issues (core content + quality enhancements)
**Defer:** 6 issues (YouTube, research)

**Total active after cleanup:** ~16 issues (down from 34)

**Clear priority:**

1. Finish current content (B1.7, B2 enrichment, B1 fixes)
2. Complete B2 → C1 → C2
3. Quality enhancements in parallel (podcasts, validation)

---

## Reviewer Notes (Gemini Agent - 2026-01-02)

### Verification Commands (Run Before Closing)

```bash
# Verify A2 is truly complete
npm run pipeline l2-uk-en a2 --audit-only

# Verify B1 vocab migration status
ls curriculum/l2-uk-en/b1/vocabulary/*.yaml | wc -l  # Should be 86+

# Verify B2 module count
ls curriculum/l2-uk-en/b2/*.md | wc -l  # Currently 131, target 145
```

### Acceptance Criteria for Epic Closures

**For #340 (YAML Vocabulary Migration):**

- [ ] All A1 modules have `vocabulary/*.yaml` files
- [ ] All A2 modules have `vocabulary/*.yaml` files
- [ ] All B1 modules have `vocabulary/*.yaml` files
- [ ] `scripts/global_vocab_audit.py` passes for all levels
- [ ] Close sub-issues #342, #343, #344, #345 BEFORE parent

**For #312 (YAML Activity Migration):**

- [ ] All B1+ modules have `activities/*.yaml` files
- [ ] No modules have activities embedded in `.md` files
- [ ] `scripts/audit_module.py` validates activity format
- [ ] Close #325 BEFORE parent

### Additional Suggestions

1. **Podcast YAML Schema** - Define location (e.g., `curriculum/l2-uk-en/podcasts/`) before creating new issues
2. **Deferred Work Timeline** - Revisit YouTube/research issues when C1 is 50%+ complete
3. **Batch Close Command** - Use `gh issue close 275 281 277 346 351` for efficiency
