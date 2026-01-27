# Context: Refactor Resources from Markdown (Issue #354)

**Agent:** C1-d (Claude Sonnet - Continuation)
**Date:** 2026-01-02
**Priority:** P2 - Architecture improvement
**Issue:** #354 - Extract Resources from Markdown
**Continuation of:** #353 (you just completed this!)

---

## Your Mission

Remove `[!resources]` sections from 247 markdown files and inject resources during MDX/JSON generation instead. This matches the activities architecture pattern.

**Why this matters:** After #353, resources exist in TWO places (YAML + markdown). This violates DRY and creates maintenance burden. Activities already use the correct pattern (YAML only → inject during build).

---

## Context: What You Just Built (#353)

You created:
- ✅ `external_resources.yaml` (297KB, source of truth)
- ✅ 4 scripts (extract, merge, validate, generate)
- ✅ Regenerated `[!resources]` in 247 markdown files

**Current problem:** Resources are duplicated in markdown files. We want YAML as the ONLY source.

---

## Desired Architecture

### Activities Pattern (Proven, Working)

```
activities/*.yaml (source of truth)
         ↓
generate_mdx.py → inject activities into MDX
         ↓
Markdown files: NO activity content (clean)
```

### Resources Should Match This

```
external_resources.yaml (source of truth)
         ↓
generate_mdx.py → inject resources into MDX
generate_json.py → add resources to JSON
         ↓
Markdown files: NO [!resources] sections (clean)
```

---

## Implementation Phases

### Phase 1: Update Generation Scripts

**File:** `scripts/generate_mdx.py`

You need to modify the MDX generator to:
1. Load `docs/resources/external_resources.yaml` at start
2. For each module, lookup resources by `module_id`
3. Inject resources into MDX output (after module content, before footer)
4. Use same template you created in `generate_resource_sections.py`:

```python
def format_resources_for_mdx(resources):
    """Format resources for MDX output (emoji template)"""
    if not resources:
        return ""

    output = ["> [!resources] 🔗 External Resources\n>"]

    # Podcasts
    if resources.get('podcasts'):
        output.append("> **🎧 Podcasts:**")
        for podcast in sorted(resources['podcasts'], key=lambda x: x['relevance']):
            title = podcast['title']
            url = podcast['url']
            desc = podcast.get('match_reason', 'Listening practice')
            output.append(f"> - [{title}]({url}) — {desc}")
        output.append(">")

    # YouTube
    if resources.get('youtube'):
        output.append("> **📺 YouTube:**")
        for video in sorted(resources['youtube'], key=lambda x: x['relevance']):
            title = video['title']
            url = video['url']
            channel = video.get('channel', '')
            output.append(f"> - [{title}]({url}) — {channel}")
        output.append(">")

    # Articles, Books, Websites (similar pattern)
    # ... (adapt from generate_resource_sections.py)

    return "\n".join(output)
```

**Where to inject:** After main module content, before any footer/navigation.

**File:** `scripts/generate_json.py`

Add `external_resources` field to JSON output:

```python
def add_resources_to_json(module_data, resources):
    """Add external resources to JSON for Vibe app"""
    if resources:
        module_data['external_resources'] = {
            'podcasts': resources.get('podcasts', []),
            'youtube': resources.get('youtube', []),
            'articles': resources.get('articles', []),
            'books': resources.get('books', []),
            'websites': resources.get('websites', [])
        }
    return module_data
```

**Testing Phase 1:**
```bash
# Test MDX generation
npm run generate l2-uk-en a1 9  # Food and drinks (8 resources)
npm run generate l2-uk-en b2 75 # History module (books/articles)

# Verify resources appear in generated MDX
cat docusaurus/docs/a1/module-09.mdx | grep -A 20 "resources"

# Test JSON generation
npm run generate:json l2-uk-en a1 9
cat output/json/l2-uk-en/a1/module-09.json | jq '.external_resources'
```

---

### Phase 2: Remove from Markdown

**Create:** `scripts/remove_resources_from_markdown.py`

```python
#!/usr/bin/env python3
"""
Remove [!resources] sections from all markdown files.
Resources are now injected during generation from external_resources.yaml.
"""

import re
from pathlib import Path
import argparse
import shutil

def remove_resources_block(content: str) -> str:
    """Remove [!resources] callout block from markdown content"""
    # Pattern: > [!resources] ... until next non-quoted line or end
    pattern = r'^> \[!resources\].*?(?=\n(?!>)|$)'
    cleaned = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)

    # Clean up extra blank lines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned.strip() + '\n'

def process_module(file_path: Path, dry_run: bool = False):
    """Process a single module file"""
    content = file_path.read_text(encoding='utf-8')

    # Check if has resources block
    if '[!resources]' not in content:
        return False

    # Remove resources block
    cleaned = remove_resources_block(content)

    if dry_run:
        print(f"Would update: {file_path}")
        return True

    # Backup original
    backup_path = file_path.with_suffix('.md.bak')
    shutil.copy2(file_path, backup_path)

    # Write cleaned content
    file_path.write_text(cleaned, encoding='utf-8')
    print(f"✅ Cleaned: {file_path}")

    return True

def main():
    parser = argparse.ArgumentParser(description='Remove [!resources] sections from markdown')
    parser.add_argument('--curriculum', required=True, help='Curriculum directory')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    args = parser.parse_args()

    curriculum_path = Path(args.curriculum)
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']

    total = 0
    updated = 0

    for level in levels:
        level_path = curriculum_path / level
        if not level_path.exists():
            continue

        for md_file in level_path.glob('*.md'):
            if md_file.name.startswith('.'):
                continue

            total += 1
            if process_module(md_file, dry_run=args.dry_run):
                updated += 1

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Processed {total} files, updated {updated}")

if __name__ == '__main__':
    main()
```

**Execution:**
```bash
# DRY RUN FIRST (always!)
.venv/bin/python scripts/remove_resources_from_markdown.py \
  --curriculum curriculum/l2-uk-en/ \
  --dry-run

# Review output, then execute
.venv/bin/python scripts/remove_resources_from_markdown.py \
  --curriculum curriculum/l2-uk-en/

# Verify - should find ZERO matches
rg "\[!resources\]" curriculum/l2-uk-en/
```

**Verification:**
- Check 5 sample modules manually (open in editor, verify no `[!resources]`)
- Use `rg` to search entire curriculum (should be empty)
- Backups created: `*.md.bak` files (can restore if needed)

---

### Phase 3: Update Validation

**File:** `scripts/audit_module.py`

Remove or update resource-related checks:

```python
# OLD (remove this):
def check_resources_format(content):
    """Check [!resources] callout format"""
    # ... validation logic ...

# NEW (add this):
def check_resources_in_yaml(module_id):
    """Verify module has resources in external_resources.yaml if expected"""
    yaml_path = Path('docs/resources/external_resources.yaml')
    if not yaml_path.exists():
        return  # YAML not generated yet, skip

    # Load YAML and check if module_id exists
    # Don't fail - just warn if missing
    # (some modules legitimately have no resources)
```

**File:** `scripts/validate_mdx.py`

Add validation that resources appear in MDX:

```python
def validate_resources_injected(mdx_path, module_id):
    """Verify resources from YAML were injected into MDX"""
    # Load external_resources.yaml
    # Check if module has resources
    # If yes, verify MDX contains [!resources] section
    # Count resources in both (should match)
```

---

### Phase 4: Deprecate Old Script

**File:** `scripts/generate_resource_sections.py`

Add deprecation notice at top:

```python
#!/usr/bin/env python3
"""
DEPRECATED: This script is no longer used in the build pipeline.

Resources are now injected directly during MDX/JSON generation,
not written to markdown files.

Kept for reference/debugging only. Will be deleted in future cleanup.

See Issue #354 for migration details.
"""

# ... existing code ...
```

---

### Phase 5: Update Documentation

**File:** `docs/ARCHITECTURE.md`

Find "External Resources" section, replace with:

```markdown
### External Resources

**Source of truth:** `docs/resources/external_resources.yaml` (297KB, 247 modules)

**Architecture:** YAML-only source, injected during generation (matches activities pattern)

```
external_resources.yaml
         ↓
generate_mdx.py → inject into MDX
generate_json.py → add to JSON
         ↓
Markdown files: NO [!resources] (clean content only)
```

**Scripts:**
- `extract_external_resources.py` - Parse existing markdown (one-time migration)
- `merge_podcast_mappings.py` - Merge ULP podcast data
- `validate_external_resources.py` - Validate YAML structure
- `generate_resource_sections.py` - DEPRECATED (kept for reference)

**Management:**
- Edit `external_resources.yaml` to add/update resources
- Run generation pipeline to rebuild output
- Resources automatically injected into MDX/JSON
```

**File:** `docs/MARKDOWN-FORMAT.md`

Remove `[!resources]` documentation, add note:

```markdown
## External Resources

External learning resources (podcasts, YouTube, articles, books) are managed in:
- `docs/resources/external_resources.yaml`

They are injected into generated output (MDX/JSON) during the build pipeline.

**Do NOT add `[!resources]` sections to markdown files.**

To add resources for a module:
1. Edit `docs/resources/external_resources.yaml`
2. Add resources under the module's `module_id`
3. Run generation pipeline
```

**File:** `CLAUDE.md`

Update module creation workflow:

```markdown
## Module Writing Workflow

...

6. **WRITE the module** using the template as structural guide
7. **DO NOT add [!resources] sections** - resources managed in external_resources.yaml
8. **VERIFY** before delivering

...
```

**File:** `claude_extensions/quick-ref/*.md`

Check all level quick references, remove any mentions of `[!resources]` callouts if present.

---

### Phase 6: Testing & Verification

**Full pipeline testing:**

```bash
# A1 (34 modules)
npm run pipeline l2-uk-en a1

# A2 (57 modules)
npm run pipeline l2-uk-en a2

# B1 samples (including the 3 with validation errors)
npm run pipeline l2-uk-en b1 25
npm run pipeline l2-uk-en b1 82
npm run pipeline l2-uk-en b1 84

# B2 sample (history module with resources)
npm run pipeline l2-uk-en b2 75
```

**Validation checklist:**
- [ ] No `[!resources]` in any markdown: `rg "\[!resources\]" curriculum/` → empty
- [ ] MDX has resources: Check `docusaurus/docs/a1/module-09.mdx` has 8 resources
- [ ] JSON has resources: Check `output/json/l2-uk-en/a1/module-09.json` has `external_resources` field
- [ ] Resource counts match: YAML (602 podcasts) → MDX (same) → JSON (same)
- [ ] All pipelines pass without errors

---

## Acceptance Criteria

Before reporting completion, verify:

- [ ] `generate_mdx.py` injects resources from YAML (tested on 5+ modules)
- [ ] `generate_json.py` includes `external_resources` field
- [ ] `remove_resources_from_markdown.py` created and executed
- [ ] ZERO `[!resources]` sections in markdown: `rg "\[!resources\]" curriculum/` is empty
- [ ] `audit_module.py` updated (no markdown resource checks)
- [ ] `validate_mdx.py` validates resource injection
- [ ] `generate_resource_sections.py` marked DEPRECATED
- [ ] 4 documentation files updated (ARCHITECTURE, MARKDOWN-FORMAT, CLAUDE, quick-ref)
- [ ] Full pipeline passes for A1, A2, sample B1/B2
- [ ] MDX output identical to before (same resources, same formatting)
- [ ] JSON output includes resources

---

## Success Metrics

**Before (#353):**
- Resources in 2 places: YAML + markdown (duplicated)
- 247 markdown files with `[!resources]` sections
- Manual markdown editing required for updates

**After (#354):**
- Resources in 1 place: YAML only (single source of truth)
- 247 markdown files clean (content only)
- Update YAML → regenerate → done

**Code quality:**
- Matches activities architecture (proven pattern)
- Reduces maintenance burden
- Enables flexible formatting per output

---

## Commands Reference

```bash
# Phase 1: Test generation
npm run generate l2-uk-en a1 9
npm run generate:json l2-uk-en a1 9

# Phase 2: Remove from markdown
.venv/bin/python scripts/remove_resources_from_markdown.py \
  --curriculum curriculum/l2-uk-en/ \
  --dry-run

.venv/bin/python scripts/remove_resources_from_markdown.py \
  --curriculum curriculum/l2-uk-en/

# Verify cleanup
rg "\[!resources\]" curriculum/l2-uk-en/

# Phase 6: Full testing
npm run pipeline l2-uk-en a1
npm run pipeline l2-uk-en a2
npm run pipeline l2-uk-en b1 25
npm run pipeline l2-uk-en b2 75
```

---

## Files You'll Modify

1. `scripts/generate_mdx.py` - Add resource injection
2. `scripts/generate_json.py` - Add external_resources field
3. `scripts/remove_resources_from_markdown.py` - NEW (cleanup script)
4. `scripts/audit_module.py` - Remove markdown resource checks
5. `scripts/validate_mdx.py` - Add injection validation
6. `scripts/generate_resource_sections.py` - Add DEPRECATED notice
7. `docs/ARCHITECTURE.md` - Update external resources section
8. `docs/MARKDOWN-FORMAT.md` - Remove [!resources] docs
9. `CLAUDE.md` - Update workflow (no resources in markdown)
10. `claude_extensions/quick-ref/*.md` - Remove [!resources] mentions

---

## Your Advantage

You just completed #353, so you already know:
- ✅ YAML structure (`external_resources.yaml`)
- ✅ Resource types (podcasts, youtube, articles, books, websites)
- ✅ Formatting template (emoji icons, sorting by type/relevance)
- ✅ Module ID patterns (`a1-09-food-and-drinks`)

This is a natural continuation - you're removing the duplication you just created in #353 and moving to a cleaner architecture.

---

**Ready to start?** Begin with Phase 1 (update generation scripts), test thoroughly, then proceed to Phase 2 (cleanup markdown).
