# C1 YAML Parse Errors - Remaining Issues

**Date:** 2026-01-10
**Status:** 12 C1 activity files have YAML syntax errors
**Impact:** Cannot remove `id` properties from these files until parse errors fixed

---

## Summary

After removing 1,867 `id` properties from A1/A2/C1 activity files, **12 C1 files remain unfixed** due to YAML parse errors. These files need syntax fixes before the `id` removal script can process them.

**Affected files:**
- 12 C1 biography/history modules
- 151 `id` properties remaining in these files

---

## Files with Parse Errors

| File | Error Location | Error Message |
|------|---------------|---------------|
| `36-knyahynia-olha.yaml` | line 712, column 53 | mapping values are not allowed here |
| `37-kniaz-sviatoslav.yaml` | line 530, column 65 | mapping values are not allowed here |
| `38-volodymyr-velykii.yaml` | line 536, column 55 | mapping values are not allowed here |
| `39-kniaz-yaroslav-mudryi.yaml` | line 541, column 66 | mapping values are not allowed here |
| `40-knyazhna-anna-yaroslavna.yaml` | line 540, column 72 | mapping values are not allowed here |
| `41-mykhailo-chernihivskyi.yaml` | line 247, column 79 | mapping values are not allowed here |
| `42-roksolana.yaml` | line 247, column 82 | mapping values are not allowed here |
| `46-yuriy-nemyrych.yaml` | line 602, column 70 | mapping values are not allowed here |
| `83-marko-kropyvnytskyi.yaml` | line 499, column 32 | mapping values are not allowed here |
| `84-oleksandr-hrekiv.yaml` | line 477, column 42 | mapping values are not allowed here |
| `85-oleksandr-bohomazov.yaml` | line 487, column 32 | mapping values are not allowed here |
| `86-viacheslav-lypynskyi.yaml` | line 255, column 55 | mapping values are not allowed here |
| `87-dmytro-dontsov.yaml` | line 277, column 34 | mapping values are not allowed here |
| `88-petro-bolbochan.yaml` | line 277, column 34 | mapping values are not allowed here |
| `89-nataliia-polonska-vasylenko.yaml` | line 277, column 34 | mapping values are not allowed here |
| `90-valentyna-radzymovska.yaml` | line 125, column 60 | mapping values are not allowed here |

**Note:** Files 37-40 have errors in later sections. Files 83-90 have errors in earlier sections.

---

## Common Pattern

Error message: **"mapping values are not allowed here"**

This typically indicates:
- Unquoted strings containing colons (`:`)
- Incorrect indentation
- Missing quotes around strings with special characters

**Example problematic pattern:**
```yaml
# WRONG - unquoted text with colon
text: Historical note: This happened in 1054

# RIGHT - quoted text
text: "Historical note: This happened in 1054"
```

---

## Fix Strategy

### Option 1: Manual Fix (Recommended)

1. Open each file and go to the error line
2. Look for unquoted strings containing `:`
3. Add quotes around the problematic text
4. Verify with: `python -c "import yaml; yaml.safe_load(open('file.yaml'))"`
5. Once file parses, re-run: `.venv/bin/python scripts/fix_activity_ids_a1_a2_c1.py`

### Option 2: Automated Detection

```bash
# Find lines with potential issues (unquoted colons)
for file in curriculum/l2-uk-en/c1/activities/{36,37,38,39,40,41,42,46,83,84,85,86,87,88,89,90}-*.yaml; do
  echo "=== $file ==="
  grep -n ': .*:' "$file" | head -5
done
```

### Option 3: Validate All C1 Files

```bash
# Check which C1 files have YAML syntax errors
for file in curriculum/l2-uk-en/c1/activities/*.yaml; do
  python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>&1 | grep -q "error" && echo "ERROR: $file"
done
```

---

## Impact

### Current State

**A1:** ✅ 100% clean (0 violations)
**A2:** ✅ 100% clean (0 violations)
**C1:** ⚠️ 84 files clean, 12 files blocked by parse errors (151 id violations remain)

### After Fix

Once the 12 C1 files are fixed:
1. Re-run `fix_activity_ids_a1_a2_c1.py` to remove remaining 151 `id` properties
2. C1 will be 100% clean
3. All schema violations resolved

---

## Verification Commands

### Check parse errors
```bash
.venv/bin/python -c "import yaml; yaml.safe_load(open('curriculum/l2-uk-en/c1/activities/36-knyahynia-olha.yaml'))"
# Should show: mapping values are not allowed here
```

### Count remaining id properties
```bash
rg '^  id: ' curriculum/l2-uk-en/c1/activities/*.yaml | wc -l
# Current: 151
# Target: 0
```

### After fixing parse errors
```bash
# Re-run fix script
.venv/bin/python scripts/fix_activity_ids_a1_a2_c1.py

# Verify all clean
rg '^  id: ' curriculum/l2-uk-en/c1/activities/*.yaml
# Expected: no output
```

---

## Next Steps

1. **[IMMEDIATE]** Fix YAML parse errors in 12 C1 files
2. **[AFTER FIX]** Re-run `fix_activity_ids_a1_a2_c1.py` to remove remaining 151 id properties
3. **[VERIFY]** Run audit on sample C1 modules to confirm all clean

---

**Prepared by:** Claude Sonnet 4.5
**Date:** 2026-01-10
**Related:** docs/dev/YAML-SCHEMA-ROOT-CAUSE-ANALYSIS.md
