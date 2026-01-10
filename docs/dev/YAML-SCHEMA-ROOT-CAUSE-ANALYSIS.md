# YAML Schema Violations - Root Cause Analysis (CORRECTED)

**Date:** 2026-01-10 (Updated)
**Status:** CRITICAL - Affects A1, A2, C1 (1,688 activities)
**Impact:** Schema validation failures, audit errors

---

## Executive Summary

**Root Cause:** The `id` property was added to the schema and 303 A1/A2 activity YAML files on Jan 7, 2026 (commit 331e2847), then removed from the schema on Jan 10, 2026 (commit d1056994) as "forbidden", but the A1/A2/C1 YAML files were never cleaned up.

**Actual Scope (CORRECTED):**
- ❌ **A1: 300 `id` violations** (~8-9 per module × 34 modules)
- ❌ **A2: 585 `id` violations** (~10 per module × 57 modules)
- ✅ **B1: 0 `id` violations** (cleaned up on Jan 10)
- ✅ **B2: 0 `id` violations** (cleaned up on Jan 10)
- ❌ **C1: 803 `id` violations** (never cleaned up)
- ✅ **C2: 0 `id` violations** (no activities yet)

**Total violations: 1,688 `id` properties across 3 levels**

---

## What Actually Happened (Timeline)

### Jan 7, 2026 (Commit 331e2847)

**Commit message:** "feat: standardize activity YAMLs and fix Reading Activity resource handling"

**What was done:**
1. Added `id` property to schema for ALL activity types (quiz, select, fill-in, true-false, cloze, etc.)
2. Added `id` property to 303 A1/A2 activity YAML files
3. Commit message claimed: "Standardized 303 activity YAML files to match schema"
4. Also added `instruction` property to schema (this one was correct)

**Schema change example:**
```diff
 "quiz": {
   "additionalProperties": false,
   "properties": {
     "type": { "const": "quiz" },
+    "id": {
+      "type": "string",
+      "description": "Unique identifier for the activity"
+    },
+    "instruction": {
+      "type": "string",
+      "description": "Additional instructions for the learner"
+    },
     "title": { "type": "string", "minLength": 1 },
```

**YAML change example (A1 M01):**
```diff
 - type: match-up
   title: True Friends
   pairs:
     - left: А
       right: A
+  id: true-friends
```

### Jan 10, 2026 (Commit d1056994)

**Commit message:** "fix(b2): remediate modules 03-10 and sync schemas"

**What was done:**
1. Removed `id` property from schema (marked as "forbidden")
2. Removed `id` from 78 B2 activity files
3. Commit message: "Synced activities-*.schema.json files with base schema"

**Schema change:**
```diff
 "quiz": {
   "additionalProperties": false,
   "properties": {
     "type": { "const": "quiz" },
-    "id": {
-      "type": "string",
-      "description": "Unique identifier for the activity"
-    },
     "instruction": { "type": "string" },
```

### Jan 10, 2026 (Commit d4303f5f)

**Commit message:** "fix(b1): Remove 886 invalid id properties from 75 activity files"

**What was done:**
1. Removed 886 `id` properties from B1 activities (75 files)
2. Used `fix_activity_ids.py` script to automate removal

**BUT:** A1, A2, and C1 were never cleaned up!

---

## Current State

### Schema (Current)

The schema does **NOT** allow `id` property for basic activity types:

```json
{
  "quiz": {
    "additionalProperties": false,  // ← Prohibits 'id'
    "properties": {
      "type": { "const": "quiz" },
      "instruction": { "type": "string" },  // ✅ Allowed
      "title": { "type": "string" }
      // NO 'id' property
    }
  }
}
```

**Only these activity types allow `id`:**
- `cloze` items (not the activity itself)
- `comparative-study`
- `authorial-intent`
- `reading`

### YAML Files (Current)

**A1 Example (01-the-cyrillic-code-i.yaml):**
```yaml
- type: match-up
  title: True Friends
  pairs:
    - left: А
      right: A
  id: true-friends  # ❌ VIOLATION - not in schema
```

**Every A1/A2/C1 activity has this violation.**

### Violation Counts

```bash
# Actual counts (verified with rg):
a1: 300 activities with 'id' property
a2: 585 activities with 'id' property
b1: 0 activities with 'id' property
b2: 0 activities with 'id' property
c1: 803 activities with 'id' property
c2: 0 activities with 'id' property
```

**Total: 1,688 violations**

### Audit Output Example

```
YAML_SCHEMA_VIOLATION [match-up]: 'id' was unexpected
YAML_SCHEMA_VIOLATION [quiz]: 'id' was unexpected
YAML_SCHEMA_VIOLATION [fill-in]: 'id' was unexpected
```

---

## Why This Happened

### Root Cause Analysis

1. **Jan 7:** Someone (likely using Gemini) thought adding `id` would be useful for frontend rendering
2. **Jan 7:** Added `id` to schema and retroactively added to all A1/A2 YAMLs
3. **Jan 10:** Discovered this broke validation (because `additionalProperties: false`)
4. **Jan 10:** Removed `id` from schema
5. **Jan 10:** Removed `id` from B1 (886 instances) and B2 (78 instances)
6. **Jan 10:** **FORGOT to remove from A1/A2/C1**

### Evidence in Code

**scripts/fix_b2_yaml.py (lines 8-10):**
```python
# Remove top-level 'id' if present
if 'id' in activity:
    del activity['id']
```

This script was written to fix the violation but only applied to B2.

**scripts/fix_activity_ids.py:**
Used to remove 886 `id` properties from B1, but never run on A1/A2/C1.

---

## The Fix

### Solution: Remove `id` from A1/A2/C1 Activity YAMLs

**Same fix that was already applied to B1/B2.**

### Implementation

**Option 1: Modify existing script**

Update `scripts/fix_activity_ids.py` to handle A1/A2/C1:

```python
#!/usr/bin/env python3
import yaml
import sys
from pathlib import Path

def remove_activity_ids(yaml_file):
    """Remove 'id' property from all activities in YAML file."""
    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not data or 'activities' not in data:
        return 0

    count = 0
    for activity in data['activities']:
        if 'id' in activity:
            del activity['id']
            count += 1

    if count > 0:
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return count

# Process all A1/A2/C1 files
levels = ['a1', 'a2', 'c1']
total = 0

for level in levels:
    activity_dir = Path(f'curriculum/l2-uk-en/{level}/activities')
    for yaml_file in activity_dir.glob('*.yaml'):
        count = remove_activity_ids(yaml_file)
        if count > 0:
            print(f"Removed {count} id properties from {yaml_file.name}")
            total += count

print(f"\nTotal: Removed {total} id properties")
```

**Option 2: Simple sed command**

```bash
# Remove 'id: something' lines from all A1/A2/C1 activity files
for level in a1 a2 c1; do
  find curriculum/l2-uk-en/$level/activities -name "*.yaml" -type f -exec \
    sed -i '' '/^  id: /d' {} \;
done
```

---

## Verification Plan

### Before Fix

```bash
# Verify violations exist
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/01-the-cyrillic-code-i.md 2>&1 | grep "id.*was unexpected"
# Expected: 8-9 violations

# Count total violations
for level in a1 a2 c1; do
  echo "$level: $(rg "^  id: " curriculum/l2-uk-en/$level/activities/*.yaml 2>/dev/null | wc -l | tr -d ' ')"
done
# Expected: a1: 300, a2: 585, c1: 803
```

### After Fix

```bash
# Run fix script
.venv/bin/python scripts/fix_activity_ids_a1_a2_c1.py

# Verify no violations
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/01-the-cyrillic-code-i.md 2>&1 | grep "YAML_SCHEMA_VIOLATION"
# Expected: No output

# Count remaining id properties
for level in a1 a2 c1; do
  echo "$level: $(rg "^  id: " curriculum/l2-uk-en/$level/activities/*.yaml 2>/dev/null | wc -l | tr -d ' ')"
done
# Expected: a1: 0, a2: 0, c1: 0
```

### Full Level Validation

```bash
# Validate all A1 modules
for file in curriculum/l2-uk-en/a1/*.md; do
  .venv/bin/python scripts/audit_module.py "$file" 2>&1 | grep "YAML_SCHEMA_VIOLATION"
done
# Expected: No output (all clean)

# Same for A2 and C1
```

---

## Additional Issues (B1/B2)

**Note:** B1 and B2 have DIFFERENT violations unrelated to `id`:

### B1 Violations (Separate Issue)

From audit reports, B1 has violations related to:
- `scrambled` property in unjumble (should be `words`)
- `correct_words` missing in mark-the-words
- `source` missing in translate

**These are DIFFERENT from the `id` issue and require separate fixes.**

### B2 Violations (Separate Issue)

B2 also has some schema violations but not related to `id`.

**Action:** Create separate root cause analysis for B1/B2 violations after fixing A1/A2/C1 `id` issue.

---

## Impact Assessment

### Current Impact

**Schema validation fails for:**
- 34 A1 modules (~8-9 violations each)
- 57 A2 modules (~10 violations each)
- C1 modules with activities (~803 total violations)

**Pipeline impact:**
- ✅ Markdown linting: PASSES (doesn't check YAML schema)
- ❌ Audit validation: FAILS (schema violations)
- ⚠️ MDX generation: May work but technically invalid
- ⚠️ HTML rendering: Works but violates schema contract

### Post-Fix Impact

After removing `id` properties:
- ✅ Schema validation: PASS
- ✅ Audit: PASS (no YAML violations)
- ✅ Pipeline: Fully compliant

---

## Recommended Actions

### Immediate (Priority: CRITICAL)

1. ✅ **Create fix script** for A1/A2/C1 `id` removal
2. ✅ **Run fix script** on all affected files
3. ✅ **Verify** with audit on sample modules
4. ✅ **Commit** with message: "fix(a1/a2/c1): Remove 1,688 invalid id properties"

### Follow-up (Priority: HIGH)

1. 🔧 **Investigate B1 violations** (scrambled, correct_words, source)
2. 🔧 **Create separate fix strategy** for B1/B2 issues
3. 🔧 **Add pre-commit hook** to prevent future schema violations

### Prevention (Priority: MEDIUM)

1. ✅ **Add CI validation** that runs schema check on all YAML files
2. ✅ **Document schema** more clearly in ACTIVITY-YAML-REFERENCE.md
3. ✅ **Add VSCode schema hints** for autocomplete

---

## Files Changed

**Git commits involved:**
- `331e2847` - Added `id` to schema + A1/A2 YAMLs (Jan 7)
- `d1056994` - Removed `id` from schema + B2 YAMLs (Jan 10)
- `d4303f5f` - Removed `id` from B1 YAMLs (Jan 10)

**Files to fix:**
- `curriculum/l2-uk-en/a1/activities/*.yaml` (34 files, 300 violations)
- `curriculum/l2-uk-en/a2/activities/*.yaml` (57 files, 585 violations)
- `curriculum/l2-uk-en/c1/activities/*.yaml` (C1 files, 803 violations)

**Schema file (already correct):**
- `schemas/activities-base.schema.json` ✅ Does NOT allow `id` for basic activity types

---

## Conclusion

This was a 3-day mistake:
1. **Jan 7:** Added `id` thinking it was needed
2. **Jan 10:** Realized it violated `additionalProperties: false`
3. **Jan 10:** Removed from schema and B1/B2, but forgot A1/A2/C1

**Fix is simple:** Delete 1,688 lines containing `id: something` from A1/A2/C1 YAML files.

**Estimated time:** 5 minutes to write script, 1 minute to run, 10 minutes to verify.

---

**Prepared by:** Claude Sonnet 4.5
**Date:** 2026-01-10 (Corrected)
**Status:** READY FOR IMPLEMENTATION
