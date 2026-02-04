# /batch-fix - Batch Module Fix (No Content Writing)

<skill>
name: batch-fix
description: Run audit on module range and fix non-content issues systematically. Does NOT fix word count issues - those require /research + /expand.
arguments: level range - e.g., "b1 15-20" or "c1-bio 25-29"
</skill>

## Purpose

Efficiently fix multiple modules for issues that don't require content writing:
- YAML schema errors
- Activity format issues
- Callout additions
- Structure fixes
- MDX regeneration

**CRITICAL: This skill does NOT fix word count shortfalls.** Word count issues require proper research and content expansion, which must be done individually.

## What This Skill Fixes

| Issue Type | Auto-Fix | Notes |
|------------|----------|-------|
| YAML schema errors | ✅ | Activity format, meta structure |
| Missing callouts | ✅ | Add [!background], [!quote], etc. |
| Activity type errors | ✅ | Replace forbidden types |
| Lint/format issues | ✅ | Heading levels, spacing |
| Structure issues | ✅ | Section ordering |
| MDX generation | ✅ | Regenerate after fixes |
| **Word count shortfall** | ❌ | **Requires /expand** |
| **Content quality** | ❌ | **Requires manual review** |

## Workflow

### Step 1: Audit All Modules in Range

```bash
for module in range:
    scripts/audit_module.sh {module_path}
```

Collect results into categories:
- Passed (no action needed)
- Fixable (schema, format, structure)
- Needs expansion (word count issues)
- Needs review (quality issues)

### Step 2: Report Status

```
📊 Batch Audit: c1-bio 25-29

✅ PASSED (1):
   - M27 ivan-mazepa

🔧 FIXABLE (2):
   - M25 ivan-sirko: Activity schema error
   - M26 yuriy-nemyrych: Transliteration detected

📝 NEEDS EXPANSION (2):
   - M28 danylo-apostol: 1465/4300 words (-2835)
   - M29 pavlo-polubotok: 1343/4300 words (-2957)

Proceed with auto-fixes for FIXABLE modules? (y/n)
Word count issues must be fixed individually with /expand.
```

### Step 3: Fix Fixable Issues

For each fixable module:
1. Read the specific error from audit log
2. Apply targeted fix
3. Re-audit to verify
4. Generate MDX if passed

**Do NOT:**
- Change word_target to match content
- Add filler content
- Skip word count validation

### Step 4: Report Remaining Work

After batch fixes complete:

```
✅ Batch Fix Complete

Fixed:
- M25 ivan-sirko: Schema fixed, MDX generated
- M26 yuriy-nemyrych: Removed Latin transliteration

Still needs work (use /expand individually):
- M28 danylo-apostol: 1465/4300 words
- M29 pavlo-polubotok: 1343/4300 words

To fix word count issues:
  /expand curriculum/l2-uk-en/c1-bio/danylo-apostol.md
  /expand curriculum/l2-uk-en/c1-bio/pavlo-polubotok.md
```

## Example Usage

```
User: /batch-fix c1-bio 25-29

Claude:
📊 Auditing c1-bio modules 25-29...

[Runs audits, categorizes results]

🔧 Auto-fixing 2 modules with schema/format issues...

M25 ivan-sirko:
  - Fixed: Activity YAML schema
  - Re-audit: ✅ PASSED
  - Generated MDX

M26 yuriy-nemyrych:
  - Fixed: Removed "(Intermarium)" transliteration
  - Re-audit: ✅ PASSED
  - Generated MDX

📝 Cannot auto-fix (word count issues):
  - M28: 1465/4300 words → use /expand
  - M29: 1343/4300 words → use /expand

Batch complete. 2 fixed, 2 need manual expansion.
```

## Why Word Count Is Excluded

Word count shortfalls indicate:
1. Insufficient research on the topic
2. Missing substantive content
3. Sections that need proper development

These require:
- Research using Ukrainian sources (/research)
- Thoughtful content expansion (/expand)
- Quality review

**Batch-fixing word count would mean adding filler, which defeats the purpose of the curriculum.**

## Integration

This skill should be called from `/module` when processing ranges:

```
/module c1-bio 25-29
→ Run batch audit first
→ Auto-fix fixable issues
→ Flag word count issues for individual /expand
→ Continue with content work only on passed modules
```
