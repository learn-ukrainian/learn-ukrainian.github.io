# /meta-fix

Check and fix invalid activity types in meta.yaml files.

## Usage

```bash
/meta-fix [level] [--apply]
```

## Arguments

- `level` (optional): Specific level to check (e.g., `b1`, `b2-hist`, `c1-bio`). If omitted, checks all levels.
- `--apply`: Apply fixes. Without this flag, runs in dry-run mode (report only).

## Examples

```bash
/meta-fix                  # Dry-run on all levels
/meta-fix b1               # Dry-run on B1 only
/meta-fix b2-hist --apply  # Fix B2-HIST modules
/meta-fix --apply          # Fix all levels
```

---

## What This Checks

Invalid activity types in `activity_hints` section of meta.yaml files.

**Valid activity types** (from `scripts/audit/config.py`):
- match-up, fill-in, quiz, true-false, group-sort, unjumble
- error-correction, anagram, select, translate, cloze
- mark-the-words, reading, essay-response
- critical-analysis, comparative-study, authorial-intent

**Common invalid types and their mappings:**

| Invalid Type | Action | Rationale |
|--------------|--------|-----------|
| transform | → fill-in | Verb transformation = fill-in |
| conjugation | → fill-in | Verb conjugation = fill-in |
| dialogue | REMOVE | Content type, not activity |
| roleplay | REMOVE | Content type, not activity |
| discussion | REMOVE | Content type, not activity |
| flashcards | → match-up | Memorization = match-up |
| rewrite | → error-correction | Rewriting = correction |
| compare | → group-sort | Comparison = sorting |
| identify | → mark-the-words | Identification = marking |
| writing | → essay-response | Writing = essay |

---

## Instructions

Parse arguments to determine:
- `level`: specific level or all (`curriculum/l2-uk-en/*/meta`)
- `apply`: whether to apply fixes or dry-run

### Step 1: Run the Fix Script

```bash
# Dry-run (default)
.venv/bin/python scripts/fix_invalid_activity_types.py [path] [--level {level}]

# Apply fixes
.venv/bin/python scripts/fix_invalid_activity_types.py [path] [--level {level}] --apply
```

### Step 2: Report Results

**Dry-run output:**
```
META CHECK: {level or "all levels"}

Invalid activity types found:
  {level}/{file}.yaml:
    🔄 {old_type} → {new_type}
    🗑️  {removed_type} (content type, not activity)

Summary: {N} fixes needed in {M} files
Run with --apply to fix
```

**Apply output:**
```
META FIX: {level or "all levels"}

Fixed:
  {level}/{file}.yaml:
    ✓ {old_type} → {new_type}
    ✓ Removed {removed_type}

Summary: {N} fixes applied in {M} files
```

### Step 3: Validate After Fix

If `--apply` was used, run validation on a sample:

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{first_fixed_module}.md 2>&1 | grep -E "INVALID_ACTIVITY|Meta"
```

Confirm no INVALID_ACTIVITY_TYPE errors appear.

---

## Adding New Mappings

If you encounter unknown types, update `scripts/fix_invalid_activity_types.py`:

```python
TYPE_MAPPINGS = {
    # ... existing mappings ...
    'new-invalid-type': 'valid-replacement',  # or None to remove
}
```

Then re-run the command.

---

## Related

- `/module-meta-qa` - Full meta.yaml validation
- `/module-sync` - Sync meta to markdown structure
- `scripts/audit/config.py` - Source of VALID_ACTIVITY_TYPES
