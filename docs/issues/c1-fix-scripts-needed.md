# C1 Fix Scripts Implementation Plan

**Date:** January 10, 2026
**Scope:** Automated fixes for 28 failing C1 modules

## Overview

Based on the C1 audit, we need **4 automated fix scripts** and **2 manual interventions** to bring C1 from 81% to 95%+ pass rate.

## Fix Priority Matrix

| Fix | Modules | Effort | Impact | Priority |
|-----|---------|--------|--------|----------|
| **1. YAML Syntax Errors** | 21 | 2-3h | High | P0 |
| **2. Missing Template Sections** | 23 | 3-4h | High | P0 |
| **3. Remove Duplicate M04** | 1 | 5min | Low | P1 |
| **4. Fix Schema Violations** | 3 | 1h | Medium | P1 |
| **5. Investigate Unknown Errors** | 4 | 1h | Medium | P1 |

**Total Effort:** 7-9 hours (mostly automated)

---

## Fix #1: YAML Syntax Errors (P0)

### Problem

21 modules have YAML parse error: "mapping values are not allowed here"

### Root Cause

YAML interprets unquoted strings containing colons as nested mappings.

**Example Error:**
```yaml
# Incorrect - triggers "mapping values not allowed here"
key: value: description

# Correct - properly quoted
key: "value: description"
```

### Affected Modules

All in M36-M99 range (Historical Biographies):
- M36, M37, M38, M39, M40, M41, M42, M44, M46
- M83, M84, M85, M86, M87, M88, M89, M90

### Script: `scripts/fix/fix_c1_yaml_syntax.py`

```python
#!/usr/bin/env python3
"""
Fix YAML syntax errors in C1 activity files.

Fixes "mapping values are not allowed here" errors by:
1. Parsing YAML to find errors
2. Quoting values containing unescaped colons
3. Validating fixed YAML
4. Writing back to file

Usage:
    .venv/bin/python scripts/fix/fix_c1_yaml_syntax.py
"""

import yaml
import re
from pathlib import Path
from typing import List, Tuple

# Modules with known YAML parse errors
AFFECTED_MODULES = [
    36, 37, 38, 39, 40, 41, 42, 44, 46,
    83, 84, 85, 86, 87, 88, 89, 90
]

def find_yaml_files(module_nums: List[int]) -> List[Path]:
    """Find activity YAML files for affected modules."""
    base = Path("curriculum/l2-uk-en/c1/activities")
    files = []
    for num in module_nums:
        pattern = f"{num:02d}-*.yaml"
        found = list(base.glob(pattern))
        files.extend(found)
    return files

def fix_yaml_syntax(yaml_path: Path) -> Tuple[bool, str]:
    """
    Fix YAML syntax errors in a single file.

    Returns:
        (success: bool, message: str)
    """
    try:
        # Read original content
        content = yaml_path.read_text(encoding='utf-8')

        # Try to parse - if it works, no fix needed
        try:
            yaml.safe_load(content)
            return (True, "Already valid")
        except yaml.YAMLError as e:
            error_msg = str(e)

            # Check if it's the "mapping values not allowed" error
            if "mapping values are not allowed here" not in error_msg:
                return (False, f"Different YAML error: {error_msg}")

        # Fix strategy: Quote values containing unescaped colons
        # Common patterns:
        # 1. key: value: description → key: "value: description"
        # 2. - item: description → - "item: description"

        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            # Skip comments and empty lines
            if line.strip().startswith('#') or not line.strip():
                fixed_lines.append(line)
                continue

            # Pattern: key: value with multiple colons (not already quoted)
            # Match: "  key: value: more stuff"
            # Don't match: "  key: 'already quoted: stuff'"
            # Don't match: "  key: \"already quoted: stuff\""

            match = re.match(r'^(\s*-?\s*[\w\-]+):\s*([^"\'#\n]+:\s*.+)$', line)
            if match:
                indent_and_key = match.group(1)
                value_with_colon = match.group(2).strip()

                # Quote the value
                fixed_line = f'{indent_and_key}: "{value_with_colon}"'
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)

        fixed_content = '\n'.join(fixed_lines)

        # Validate fixed YAML
        try:
            yaml.safe_load(fixed_content)
        except yaml.YAMLError as e:
            return (False, f"Fix didn't work: {str(e)}")

        # Write back
        yaml_path.write_text(fixed_content, encoding='utf-8')
        return (True, "Fixed and validated")

    except Exception as e:
        return (False, f"Exception: {str(e)}")

def main():
    print("C1 YAML Syntax Fix")
    print("=" * 50)

    files = find_yaml_files(AFFECTED_MODULES)
    print(f"Found {len(files)} YAML files to check")
    print()

    fixed_count = 0
    already_valid = 0
    failed = []

    for yaml_file in files:
        success, message = fix_yaml_syntax(yaml_file)

        if success:
            if message == "Already valid":
                already_valid += 1
                print(f"✓ {yaml_file.name}: {message}")
            else:
                fixed_count += 1
                print(f"✅ {yaml_file.name}: {message}")
        else:
            failed.append((yaml_file.name, message))
            print(f"❌ {yaml_file.name}: {message}")

    print()
    print("=" * 50)
    print(f"Results:")
    print(f"  Fixed: {fixed_count}")
    print(f"  Already valid: {already_valid}")
    print(f"  Failed: {len(failed)}")

    if failed:
        print()
        print("Failed files (need manual inspection):")
        for filename, error in failed:
            print(f"  - {filename}: {error}")

if __name__ == "__main__":
    main()
```

### Testing

```bash
# Dry run first (add --dry-run flag to script)
.venv/bin/python scripts/fix/fix_c1_yaml_syntax.py --dry-run

# Apply fixes
.venv/bin/python scripts/fix/fix_c1_yaml_syntax.py

# Verify fixes
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/c1/36-*.md
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/c1/37-*.md
# ... etc
```

### Expected Outcome

- 21 modules fixed
- 21 YAML files pass validation
- 0 remaining "mapping values not allowed" errors

---

## Fix #2: Missing Template Sections (P0)

### Problem

23 modules missing required biography template sections:
- "Життєпис" (Biography)
- "Внесок" (Contribution)
- "Спадщина" (Legacy)
- "Need More Practice?"

### Root Cause

Modules created before template standardization or template not followed.

### Affected Modules

Overlaps with YAML errors (concentrated in M36-M99):
- All modules from Fix #1
- Plus: M109 (Lina Kostenko)

### Strategy

**Two-phase approach:**
1. **Automated:** Add empty sections with TODO markers
2. **Manual:** Content authors fill in TODO sections (defer)

### Script: `scripts/fix/fix_c1_biography_sections.py`

```python
#!/usr/bin/env python3
"""
Add missing template sections to C1 biography modules.

Adds required sections per c1-biography-module-template:
- Життєпис (Biography)
- Внесок (Contribution)
- Спадщина (Legacy)
- Need More Practice?

Usage:
    .venv/bin/python scripts/fix/fix_c1_biography_sections.py
"""

import re
from pathlib import Path
from typing import List, Set, Tuple

# Required sections per c1-biography-module-template
REQUIRED_SECTIONS = {
    "Життєпис": "Biography",
    "Внесок": "Contribution",
    "Спадщина": "Legacy",
    "Need More Practice?": "Practice section"
}

# Modules with missing sections (from audit)
AFFECTED_MODULES = [
    36, 37, 38, 39, 40, 41, 42, 44, 46,
    83, 84, 85, 86, 87, 88, 89, 96, 98, 109
]

def find_modules(module_nums: List[int]) -> List[Path]:
    """Find module markdown files."""
    base = Path("curriculum/l2-uk-en/c1")
    files = []
    for num in module_nums:
        pattern = f"{num:02d}-*.md"
        found = list(base.glob(pattern))
        if found:
            files.append(found[0])
    return files

def get_existing_sections(content: str) -> Set[str]:
    """Extract existing H2 section headers."""
    sections = set()
    for line in content.split('\n'):
        if line.startswith('## '):
            header = line[3:].strip()
            sections.add(header)
    return sections

def find_section_aliases(content: str, canonical: str) -> List[str]:
    """
    Find sections that might be aliases for canonical section.

    E.g., "Спадщина та сучасне сприйняття" is an alias for "Спадщина"
    """
    aliases = []
    for line in content.split('\n'):
        if line.startswith('## '):
            header = line[3:].strip()
            # Check if canonical word appears in header
            if canonical.lower() in header.lower() and header != canonical:
                aliases.append(header)
    return aliases

def add_missing_sections(module_path: Path) -> Tuple[int, List[str]]:
    """
    Add missing template sections to module.

    Returns:
        (added_count, messages)
    """
    content = module_path.read_text(encoding='utf-8')
    existing = get_existing_sections(content)

    added = []
    messages = []

    for section, description in REQUIRED_SECTIONS.items():
        # Check if section exists (exact match)
        if section in existing:
            messages.append(f"  ✓ {section} exists")
            continue

        # Check for aliases
        aliases = find_section_aliases(content, section.split()[0])  # First word
        if aliases:
            messages.append(f"  ~ {section} has alias: {aliases[0]} (keeping)")
            continue

        # Section missing - add it
        added.append(section)
        messages.append(f"  + Adding {section}")

    if not added:
        return (0, messages)

    # Add missing sections before "Need More Practice?" or at end
    # Strategy: Insert in template order

    # Find insertion point
    if "## Need More Practice?" in content:
        # Insert before practice section
        insertion_marker = "## Need More Practice?"
    else:
        # Insert before final vocabulary section or at end
        if "## Словник" in content:
            insertion_marker = "## Словник"
        else:
            insertion_marker = None

    # Build sections to add
    sections_text = "\n"
    for section in added:
        if section == "Need More Practice?":
            # Add practice section with standard content
            sections_text += f"\n## {section}\n\n"
            sections_text += "Готові попрактикувати більше? Перегляньте:\n\n"
            sections_text += "- [Exercises](https://www.ukrainianlessons.com/exercises/)\n"
            sections_text += "- [Reading practice](https://www.ukrainianlessons.com/reading/)\n\n"
        else:
            # Add empty section with TODO
            sections_text += f"\n## {section}\n\n"
            sections_text += "<!-- TODO: Add content for this section -->\n\n"

    # Insert sections
    if insertion_marker:
        content = content.replace(
            f"\n{insertion_marker}",
            sections_text + insertion_marker
        )
    else:
        # Append at end
        content += sections_text

    # Write back
    module_path.write_text(content, encoding='utf-8')

    return (len(added), messages)

def main():
    print("C1 Biography Sections Fix")
    print("=" * 50)

    modules = find_modules(AFFECTED_MODULES)
    print(f"Found {len(modules)} modules to fix")
    print()

    total_added = 0

    for module in modules:
        print(f"Processing {module.name}...")
        added_count, messages = add_missing_sections(module)

        for msg in messages:
            print(msg)

        if added_count > 0:
            print(f"  ✅ Added {added_count} sections")
            total_added += added_count
        else:
            print(f"  ✓ All sections present")

        print()

    print("=" * 50)
    print(f"Total sections added: {total_added}")
    print()
    print("Next steps:")
    print("1. Review modules with <!-- TODO --> markers")
    print("2. Fill in missing content manually")
    print("3. Re-run audit to verify compliance")

if __name__ == "__main__":
    main()
```

### Testing

```bash
# Dry run on one module first
.venv/bin/python scripts/fix/fix_c1_biography_sections.py --module 36 --dry-run

# Apply to all
.venv/bin/python scripts/fix/fix_c1_biography_sections.py

# Verify
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/c1/36-*.md
```

### Expected Outcome

- 23 modules have all required sections
- Sections with TODO markers flagged for manual content
- 0 "MISSING_REQUIRED_SECTION" errors

---

## Fix #3: Remove Duplicate M04 (P1)

### Problem

Two M04 modules exist:
- `04-analysis-vocab.md` (FAILED audit)
- `04-analysis-vocabulary.md` (PASSED audit)

### Decision

**Keep:** `04-analysis-vocabulary.md` (passes audit)
**Delete:** `04-analysis-vocab.md` (fails audit)

### Manual Steps

```bash
# Verify which one passes
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/c1/04-analysis-vocab.md
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/c1/04-analysis-vocabulary.md

# Delete failed one
rm curriculum/l2-uk-en/c1/04-analysis-vocab.md
rm curriculum/l2-uk-en/c1/activities/04-analysis-vocab.yaml
rm curriculum/l2-uk-en/c1/vocabulary/04-analysis-vocab.yaml

# Verify no other references
rg "04-analysis-vocab" curriculum/ docs/
```

### Expected Outcome

- Only one M04 module remains
- No broken references
- No numbering conflicts

---

## Fix #4: Schema Violations (P1)

### Problem

3 modules have schema violations:
- **M04** (analysis-vocab): Missing 'sentence' property, min_words too low
- **M14** (literature-review): Options arrays too short

### Fixes Required

#### M04: 04-analysis-vocab.yaml

**Note:** This file will be deleted (see Fix #3), so skip this fix.

#### M14: 14-literature-review.yaml

**Error 1:** fill-in "словник-дискусії" - options array too short
```yaml
# Current (3 options - too short)
options: ['прислухатися', 'подивитися', 'прийти']

# Fix (add 4th option)
options: ['прислухатися', 'подивитися', 'прийти', 'послухати']
```

**Error 2:** error-correction "стиль-огляду:-редагування" - options array too short
```yaml
# Current (2 options - too short)
options: ['велика дірка', 'дірка в науці']

# Fix (add 3rd and 4th options)
options: ['велика дірка', 'дірка в науці', 'великий розрив', 'пропуск']
```

### Manual Fix

```bash
# Edit file directly
vim curriculum/l2-uk-en/c1/activities/14-literature-review.yaml

# Or use script
.venv/bin/python scripts/fix/fix_c1_schema_violations.py
```

### Expected Outcome

- M14 passes schema validation
- All fill-in activities have 4+ options
- All error-correction activities have 4+ options

---

## Fix #5: Investigate Unknown Errors (P1)

### Problem

4 modules produced no error output during audit:
- M134 (Hyperbole-Litotes)
- M135 (Euphemism-Taboo)
- M136 (Rhetorical Questions)
- M146 (Kolyskovi ta Dumy)

### Investigation Steps

```bash
# Check if files are empty
for module in 134 135 136 146; do
    file="curriculum/l2-uk-en/c1/${module}-*.md"
    wc -l $file
    head -20 $file
done

# Check for corrupted markdown
for module in 134 135 136 146; do
    file="curriculum/l2-uk-en/c1/${module}-*.md"
    .venv/bin/python scripts/audit_module.py $file 2>&1 | head -50
done

# Check frontmatter
for module in 134 135 136 146; do
    file="curriculum/l2-uk-en/c1/${module}-*.md"
    head -10 $file | grep -A 10 "^---"
done
```

### Possible Issues

1. **Empty files** - Need content
2. **Missing frontmatter** - Add frontmatter
3. **Corrupted markdown** - Repair structure
4. **Critical structural errors** - Rebuild from template

### Resolution

Based on investigation, create fix script or manual intervention.

### Expected Outcome

- 4 modules either pass audit or have clear error messages
- No "silent failures" (unknown errors)

---

## Testing & Validation Plan

### Phase 1: Fix Application

1. Run Fix #1 (YAML syntax)
2. Run Fix #2 (missing sections)
3. Apply Fix #3 (remove duplicate)
4. Apply Fix #4 (schema violations)
5. Complete Fix #5 (investigate unknowns)

### Phase 2: Verification

```bash
# Re-audit all C1 modules
for module in curriculum/l2-uk-en/c1/[0-9]*.md; do
    .venv/bin/python scripts/audit_module.py "$module"
done | tee c1-post-fix-audit.log

# Count pass/fail
grep "✅ AUDIT PASSED" c1-post-fix-audit.log | wc -l
grep "❌ AUDIT FAILED" c1-post-fix-audit.log | wc -l
```

**Target:** 143+/148 pass (95%+)

### Phase 3: Pipeline Validation

```bash
# Validate MDX generation
npm run pipeline l2-uk-en c1

# Check for errors
echo $?  # Should be 0
```

### Phase 4: Regression Check

```bash
# Ensure fixes didn't break passing modules
# Re-audit modules that were passing before
grep "✅" docs/issues/c1-rebuild-audit-report.md | head -20

# Spot-check 10 previously passing modules
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/c1/01-*.md
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/c1/100-*.md
# ... etc
```

---

## Implementation Schedule

### Day 1 (4 hours)

**Morning (2h):**
- [ ] Create `scripts/fix/fix_c1_yaml_syntax.py`
- [ ] Test on 3 modules (M36, M37, M38)
- [ ] Run on all 21 affected modules
- [ ] Verify YAML parsing works

**Afternoon (2h):**
- [ ] Create `scripts/fix/fix_c1_biography_sections.py`
- [ ] Test on 3 modules
- [ ] Run on all 23 affected modules
- [ ] Verify sections present (TODOs acceptable)

### Day 2 (3 hours)

**Morning (1.5h):**
- [ ] Apply Fix #3 (remove duplicate M04)
- [ ] Apply Fix #4 (schema violations in M14)
- [ ] Complete Fix #5 (investigate unknown errors)

**Afternoon (1.5h):**
- [ ] Re-audit all 148 C1 modules
- [ ] Generate post-fix audit report
- [ ] Compare before/after metrics
- [ ] Document remaining issues (if any)

### Day 3 (Optional - Content Filling)

**If needed:**
- [ ] Fill TODO sections in biography modules
- [ ] Review and improve auto-generated content
- [ ] Final audit pass
- [ ] Pipeline validation

---

## Success Criteria

### Minimum Success (Day 1-2)

- [x] YAML syntax errors: 21 → 0
- [x] Missing sections: 23 → 0 (structure only, TODOs acceptable)
- [x] Duplicate modules: 1 → 0
- [x] Schema violations: 3 → 0
- [x] Unknown errors: 4 → 0 (identified and documented)
- [x] **Pass rate: 81% → 95%+**

### Full Success (Day 3)

- [ ] All TODO sections filled with quality content
- [ ] Pass rate: 95% → 98%+
- [ ] Pipeline passes: `npm run pipeline l2-uk-en c1`
- [ ] Landing page updated: `npm run sync:landing`

### Strategic Success (Future)

- [ ] Complete M33-M35 (checkpoints) → 77% complete
- [ ] Vocabulary enrichment → Full metadata
- [ ] HTML validation → Production-ready

---

## Risk Mitigation

### Backup Before Fixes

```bash
# Create backup branch
git checkout -b backup/c1-pre-fixes
git add curriculum/l2-uk-en/c1/
git commit -m "Backup C1 modules before automated fixes"
git checkout main

# Or create tar backup
tar -czf c1-backup-$(date +%Y%m%d).tar.gz curriculum/l2-uk-en/c1/
```

### Rollback Plan

```bash
# If fixes break things
git diff backup/c1-pre-fixes..main -- curriculum/l2-uk-en/c1/

# Restore from backup
git checkout backup/c1-pre-fixes -- curriculum/l2-uk-en/c1/
```

### Incremental Approach

- Test each fix on 3 modules before applying to all
- Commit after each fix type
- Re-audit after each fix to verify improvement

---

## Monitoring & Reporting

### Progress Tracking

Update `c1-rebuild-index.md` with:
- Fix completion status
- Before/after metrics
- Remaining issues

### Metrics Dashboard

```markdown
## Fix Progress

| Fix | Status | Modules | Pass Rate |
|-----|--------|---------|-----------|
| Before fixes | ✅ Complete | 148 | 81.1% |
| #1: YAML syntax | 🚧 In progress | 21 | - |
| #2: Missing sections | ⏳ Pending | 23 | - |
| #3: Duplicate M04 | ⏳ Pending | 1 | - |
| #4: Schema violations | ⏳ Pending | 3 | - |
| #5: Unknown errors | ⏳ Pending | 4 | - |
| **After fixes** | ⏳ Pending | 148 | **Target: 95%** |
```

---

## Appendix: Affected Module List

### Fix #1: YAML Syntax (21 modules)

M36, M37, M38, M39, M40, M41, M42, M44, M46, M83, M84, M85, M86, M87, M88, M89, M90

### Fix #2: Missing Sections (23 modules)

M36, M37, M38, M39, M40, M41, M42, M44, M46, M83, M84, M85, M86, M87, M88, M89, M96, M98, M109

### Fix #3: Duplicate (1 module)

M04 (analysis-vocab vs analysis-vocabulary)

### Fix #4: Schema (2 unique modules)

M04 (will be deleted), M14

### Fix #5: Unknown (4 modules)

M134, M135, M136, M146
