# B1 MD→YAML Migration Test Plan

## Context

**Current State:**
- 52/85 B1 modules exist as .md files
- 18/85 converted to new MD+YAML format
- 34 modules need conversion (M17-M51)
- 33 modules need creation (M54-M85)

**Quality Validation (Dec 27, 2025):**
- ✅ All 3 template types validated with Ukrainian Grammar Validator
- ✅ Content quality is HIGH - worth migrating existing modules
- ⚠️ Migration has been problematic - need careful testing

---

## The md_to_yaml.py Tool

**What it does:**
- Reads .md files with inline Markdown activities
- Extracts activities using regex parsers
- Converts to YAML format
- Writes separate `.activities.yaml` files
- Optionally strips activities from .md (with `--strip` flag)

**Recent fixes (commit 5ad4eea2):**
- `parse_true_false`: Parses numbered blocks with Правда/Неправда
- `parse_cloze`: Returns inline {answer|opt1|opt2} format
- `parse_mark_the_words`: Handles [word] and **word** formats

**Successfully converted:** M01-M16 (aspect phase + metalanguage)

---

## Test Plan

### Phase 1: Single Module Test (CRITICAL)

**Test module:** M17 (motion-coming-going)

```bash
# 1. Dry-run to preview
.venv/bin/python scripts/md_to_yaml.py curriculum/l2-uk-en/b1/17-motion-coming-going.md --dry-run

# 2. If preview looks good, convert
.venv/bin/python scripts/md_to_yaml.py curriculum/l2-uk-en/b1/17-motion-coming-going.md

# 3. Audit the result
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/17-motion-coming-going.md

# 4. Validate content quality (sample)
.venv/bin/python scripts/validate_content_quality.py curriculum/l2-uk-en/b1/17-motion-coming-going.md

# 5. Run pipeline
npm run pipeline l2-uk-en b1 17
```

**Success criteria:**
- ✅ YAML file created with correct structure
- ✅ All activities extracted (12 expected for M17)
- ✅ Audit passes
- ✅ Pipeline generates valid MDX + JSON
- ✅ No content loss (compare MD before/after)

**If fails:**
- Document the error
- Fix md_to_yaml.py parser
- Re-test
- DO NOT proceed to batch until single module works

---

### Phase 2: Small Batch Test (5 modules)

**Test batch:** M17-M21 (motion verbs phase)

```bash
# Convert batch
for i in 17 18 19 20 21; do
    echo "=== Converting M$i ==="
    .venv/bin/python scripts/md_to_yaml.py curriculum/l2-uk-en/b1/$i-*.md

    if [ $? -ne 0 ]; then
        echo "ERROR: M$i failed conversion"
        break
    fi
done

# Audit batch
for i in 17 18 19 20 21; do
    echo "=== Auditing M$i ==="
    .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/$i-*.md
done

# Pipeline batch
npm run pipeline l2-uk-en b1
```

**Success criteria:**
- ✅ All 5 modules convert without errors
- ✅ All 5 pass audit
- ✅ All 5 generate valid MDX/JSON
- ✅ Activity counts match expectations

**If fails:**
- Identify which module failed
- Debug that specific module
- Fix parser if needed
- Re-test from Phase 1

---

### Phase 3: Full Migration (34 modules)

**Only proceed if Phase 1 and Phase 2 succeed.**

**Modules to convert:** M17-M51 (excluding already converted)

**Strategy:** Batch by phase to isolate failures

#### Batch 1: Motion Verbs (M17-M25)

```bash
for i in {17..25}; do
    .venv/bin/python scripts/md_to_yaml.py curriculum/l2-uk-en/b1/$i-*.md
done
```

#### Batch 2: Complex Sentences I (M26-M34)

```bash
for i in {26..34}; do
    .venv/bin/python scripts/md_to_yaml.py curriculum/l2-uk-en/b1/$i-*.md
done
```

#### Batch 3: Complex Sentences II (M35-M41)

```bash
for i in {35..41}; do
    .venv/bin/python scripts/md_to_yaml.py curriculum/l2-uk-en/b1/$i-*.md
done
```

#### Batch 4: Advanced Grammar (M42-M51)

```bash
for i in {42..51}; do
    .venv/bin/python scripts/md_to_yaml.py curriculum/l2-uk-en/b1/$i-*.md
done
```

**After each batch:**
- Run audit on all modules in batch
- Fix any errors before proceeding
- Run pipeline validation

---

## Rollback Plan

**If migration fails badly:**

1. **Git reset** - all changes are tracked
2. **Alternative approach:** Rewrite problematic modules from scratch
3. **Hybrid:** Convert what works, rewrite what doesn't

**Git safety:**
```bash
# Before starting migration
git -C /Users/krisztiankoos/projects/learn-ukrainian status
git -C /Users/krisztiankoos/projects/learn-ukrainian branch migration-test-dec27

# If need to rollback
git -C /Users/krisztiankoos/projects/learn-ukrainian checkout main
git -C /Users/krisztiankoos/projects/learn-ukrainian branch -D migration-test-dec27
```

---

## Known Issues & Workarounds

### Issue 1: YAML Structure Variations

Some modules use `activities:` wrapper, others are direct lists.

**Workaround:** Update `load_yaml_activities()` to handle both formats.

### Issue 2: Activity Type Naming

Some activities use `error-correction`, others `error_correction`.

**Workaround:** Normalize in parser (already implemented in audit).

### Issue 3: Cloze Format Variations

Inline `{answer|opt1|opt2}` vs dict format.

**Workaround:** Parser should output inline format (recent fix).

---

## Success Metrics

**Migration complete when:**
- ✅ 52/52 existing B1 modules have `.activities.yaml` files
- ✅ All 52 modules pass audit
- ✅ All 52 modules generate valid MDX + JSON
- ✅ No content loss detected
- ✅ Activity counts match original modules

**Then proceed to:** Create M54-M85 (33 new modules)

---

## Timeline Estimate

**Conservative approach:**
- Phase 1 (single module): 1 hour (including fixes if needed)
- Phase 2 (5 modules): 2 hours (including audit/validation)
- Phase 3 (34 modules): 1 day (including batch processing + fixes)

**Aggressive approach (if tools work perfectly):**
- All phases: 4 hours

**Realistic:** Plan for 1 full day of focused work with fixes.

---

## Phase 1 Results (2025-12-27)

**Status:** ✅ COMPLETED

### Issues Found

**Issue #1: M17 used non-standard cloze format (named blanks)**
- **Problem**: M17 used named blanks `[___:answer]` instead of documented numbered format `[___:1]`
- **Impact**: Parser couldn't convert, audit reported 0 items (failed density gate)
- **Root Cause**: Incomplete documentation - `stage-3-activities.md` showed output YAML format but not input MD format
- **Fix**: Converted M17 cloze to numbered format with options:
  ```markdown
  [___:1] → 1. opt1 | opt2 | opt3 | opt4
             > [!answer] correct
  ```
- **Verification**: M17 was the ONLY module using this format (17 other modules use numbered format)

**Issue #2: M18 used non-standard cloze format (numbered inline)**
- **Problem**: M18 used `[N:answer]` format instead of documented `[___:N]` format
- **Impact**: Parser couldn't convert, audit reported 0 items (failed density gate)
- **Example**: `[1:пройтися]` instead of `[___:1]` with option list
- **Fix**: Converted M18 cloze to numbered format with 16 option lists
- **Verification**: Detection script found only M18 and M21 use this format
- **Status**: M18 fixed, M21 pending fix

**Issue #3: M19 used inline options cloze format**
- **Problem**: M19 used `[opt1 | opt2 | opt3:N]` format with answer key at bottom
- **Impact**: Parser couldn't convert, audit reported 0 items (failed density gate)
- **Example**: `[поїхали | зайшли | розійшлися:1]` with answer list `1. поїхали`
- **Observation**: Correct answer is always first option in this format
- **Fix**: Converted M19 cloze to numbered format with 14 option lists
- **Verification**: Only M19 uses this inline options format
- **Status**: ✅ Fixed

**Issue #4: M19 used checkbox true-false format without Правда/Неправда**
- **Problem**: M19 used checkbox format with `[!answer]` callouts instead of "Правда/Неправда" labels
- **Impact**: Parser couldn't parse, returned empty `items: []`, audit reported 0 items
- **Example**: Used `> [!answer] true` instead of `- [x] Правда`
- **Root Cause**: Misunderstood true-false format (should use Ukrainian labels, not English)
- **Fix**: Converted to numbered list with `- [x] Правда` / `- [x] Неправда` format
- **Verification**: Checked M17 format, confirmed Правда/Неправда is the working pattern
- **Status**: ✅ Fixed

### Results

**M17 (motion-coming-going):**
- ✅ YAML created with 12 activities
- ✅ Cloze activity: 14 blanks detected (was 0, now 14)
- ✅ Audit passed (all strict gates)
- ✅ Pipeline passed (MDX + HTML validation)

**M18 (motion-passing-crossing):**
- ✅ YAML created with 12 activities
- ✅ Cloze activity: 16 blanks detected (was 0, now 16)
- ✅ Audit passed (all strict gates)
- ✅ Pipeline passed (MDX + HTML validation)

**M19 (motion-starting-returning):**
- ✅ YAML created with 12 activities
- ✅ Cloze activity: 14 blanks detected (was 0, now 14)
- ✅ True-false activity: 10 items detected (was 0, now 10)
- ✅ Audit passed (all strict gates)
- ✅ Pipeline passed (MDX + HTML validation)

**Source Fixes Applied:**
- ✅ Updated `claude_extensions/stages/stage-3-activities.md` with explicit cloze format documentation
- ✅ Added "Fix the Source" principle to `CLAUDE.md`
- ✅ Created detection script `scripts/fix_cloze_formats.py` to scan remaining modules
- ✅ Deployed changes via `npm run claude:deploy`

**M21 (motion-figurative-uses):**
- ✅ YAML created with 12 activities
- ❌ First audit failed: 11/12 activities (quiz misplaced in content section)
- 🔧 Issue #5: Quiz activity placed before "# Вправи" header (not parseable)
- 🔧 Issue #6: Cloze used `[N:answer]` format (same as M18)
- 🔧 Issue #7: Translate used callout format instead of checkboxes
- 🔧 Issue #8: Unjumble typo `[!!answer]` → `[!answer]`
- ✅ Fixed: Moved quiz to Activities section (11 → 12 activities)
- ✅ Fixed: Converted cloze to `[___:N]` format (14 blanks)
- ✅ Fixed: Converted translate to checkbox format (8 items, added 4th distractor)
- ✅ Fixed: Corrected unjumble typo (5 → 6 items)
- ❌ Second audit failed: Richness 93% (needs 95%)
- 🔧 Issue #9: Only 16 examples vs 24 needed (pre-existing content issue)
- ✅ Fixed: Added 5 bulleted examples (21 total → 97% richness)
- ✅ Audit passed (all strict gates)
- ✅ Pipeline passed (MDX + HTML validation)

### Phase 1 Complete

**Status:** ✅ PHASE 1 COMPLETED (5/5 modules tested)
**Date:** 2025-12-27

**Summary:**
- All 5 modules (M17-M21) successfully migrated to MD+YAML format
- All modules pass audit with all strict gates
- All modules generate valid MDX + JSON via pipeline
- 9 distinct format issues found and fixed:
  1. M17: Cloze named blanks `[___:answer]`
  2. M18: Cloze numbered inline `[N:answer]`
  3. M19: Cloze inline options `[opt1|opt2:N]`
  4. M19: True-false callout format (no Правда/Неправда)
  5. M20: True-false same as M19
  6. M21: Quiz misplaced (before Activities section)
  7. M21: Cloze `[N:answer]` (same as M18)
  8. M21: Translate callouts instead of checkboxes
  9. M21: Unjumble typo `[!!answer]`
- 1 content quality issue found and fixed:
  10. M21: Richness 93% (insufficient examples)

**Converter Performance:**
- Works correctly for all standard formats
- Requires manual fixes for non-standard activity formats
- All fixes applied to source .md files (Fix the Source principle)

**Next Phase:**
- Ready for Phase 2 (small batch test: M17-M21 confirmed working)
- OR proceed directly to Phase 3 (full migration M17-M51)
