# RFC #410: Manifest-Driven Architecture

> **Status**: Approved (decisions finalized 2026-01-17)
> **Author**: Claude (AI Assistant)
> **Created**: 2026-01-14
> **GitHub Issue**: [#410](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/410)

## Executive Summary

This RFC proposes replacing the current numbered-filename system with a **manifest-driven architecture** where:

1. **`curriculum.yaml`** defines module order (single source of truth)
2. **Slug-based filenames** replace numbered prefixes (`the-cyrillic-code-i.md` not `01-the-cyrillic-code-i.md`)
3. **Build-time resolution** handles links between modules via `slug:` prefix

This eliminates "renumbering hell" when inserting, moving, or reordering modules.

---

## Problem Statement

### Current Pain Points

| Scenario | Current Impact | Files Affected |
|----------|---------------|----------------|
| Insert module at A1 position 5 | Rename 29 files + all sidecars | 120+ files |
| Move B2 history modules to track | Rename 61 modules | 244+ files |
| Reorder 3 modules in sequence | Rename all subsequent modules | Variable |
| Fix broken links after rename | Manual search/replace | All MD files |

### Why This Matters Now

RFC #409 (Curriculum Reorganization) requires:
- Adding 10+ practical modules to A1
- Adding 12+ practical modules to A2
- Moving 61 B2 history modules to a separate track
- Moving 96 C1 biography modules to a separate track

Without manifest-driven architecture, this would require renaming **300+ files** and fixing countless internal links.

---

## Proposed Solution

### 1. Manifest File: `curriculum.yaml`

Single file per language pair defining all course structure:

```yaml
# curriculum/l2-uk-en/curriculum.yaml
version: "2.0"
language_pair: uk-en
name: "Ukrainian for English Speakers"

# Global settings
settings:
  default_transliteration: true  # A1-A2

# =============================================================================
# CORE PATH - Required for all learners
# =============================================================================
core:
  a1:
    name: "A1 - Beginner"
    modules:
      # Phase A1.1 - First Contact
      - slug: the-cyrillic-code-i
        title: "The Cyrillic Code I"
        phase: A1.1
        focus: grammar

      - slug: the-cyrillic-code-ii
        title: "The Cyrillic Code II"
        phase: A1.1
        focus: grammar

      - slug: the-gender-code
        title: "The Gender Code"
        phase: A1.1
        focus: grammar

      # ... more modules

      - slug: checkpoint-first-contact
        title: "Checkpoint - First Contact"
        phase: A1.1
        focus: checkpoint

      # Phase A1.2 - Navigation
      - slug: the-accusative-i-things
        title: "The Accusative I - Things"
        phase: A1.2
        focus: grammar

      # Practical modules (NEW - from #409)
      - slug: at-the-cafe
        title: "At the Café"
        phase: A1.2
        focus: practical

      # ... etc

  a2:
    name: "A2 - Elementary"
    modules:
      - slug: the-dative-i-pronouns
        # ...

  b1:
    name: "B1 - Intermediate"
    modules:
      # ...

  b2:
    name: "B2 - Upper Intermediate"
    modules:
      # Core B2 only - history moved to track
      - slug: passive-voice-system
        # ...

  c1:
    name: "C1 - Advanced"
    modules:
      # Core C1 only - biographies moved to track
      # ...

  c2:
    name: "C2 - Mastery"
    modules:
      # ...

# =============================================================================
# SPECIALIZED TRACKS - Optional paths
# =============================================================================
tracks:
  b2-hist:
    name: "B2 History Track"
    description: "Ukrainian History from Kyivan Rus' to Independence"
    prerequisite: b2  # Must complete B2 core first
    modules:
      - slug: kyivan-rus-origins
        # ...

  c1-bio:
    name: "C1 Biography Track"
    description: "Famous Ukrainians Throughout History"
    prerequisite: c1
    modules:
      - slug: taras-shevchenko
        # ...

  b2-pro:
    name: "B2 Professional Track"
    description: "Business and Professional Ukrainian"
    prerequisite: b2
    modules:
      - slug: business-email-formal
        # ...

  lit:
    name: "Literature Track"
    description: "Classical Ukrainian Literature"
    prerequisite: c1
    modules:
      # ...
```

### 2. File Structure Changes

**Before (numbered):**
```
curriculum/l2-uk-en/a1/
├── 01-the-cyrillic-code-i.md
├── 02-the-cyrillic-code-ii.md
├── 03-the-gender-code.md
├── activities/
│   ├── 01-the-cyrillic-code-i.yaml
│   ├── 02-the-cyrillic-code-ii.yaml
├── meta/
│   ├── 01-the-cyrillic-code-i.yaml
├── vocabulary/
│   ├── 01-the-cyrillic-code-i.yaml
```

**After (slug-based):**
```
curriculum/l2-uk-en/a1/
├── the-cyrillic-code-i.md
├── the-cyrillic-code-ii.md
├── the-gender-code.md
├── activities/
│   ├── the-cyrillic-code-i.yaml
│   ├── the-cyrillic-code-ii.yaml
├── meta/
│   ├── the-cyrillic-code-i.yaml
├── vocabulary/
│   ├── the-cyrillic-code-i.yaml
```

### 3. Module Ordering

Order is **defined in `curriculum.yaml`**, not by filesystem sorting.

```python
# Before: Order by filename
module_files = sorted(level_path.glob('*.md'))  # 01, 02, 03...

# After: Order by manifest
def get_modules(level: str) -> list[Module]:
    manifest = load_manifest()
    return manifest['core'][level]['modules']
```

### 4. Link Resolution

**Current approach (fragile):**
```markdown
See [Module 5](/a1/module-05) for details.
```

**New approach (stable):**
```markdown
See [slug:my-world-objects] for details.
```

Build-time transformer resolves `slug:` links:
```python
def resolve_slug_links(content: str, manifest: dict) -> str:
    """Replace slug:xxx with actual path/title."""
    def replace_slug(match):
        slug = match.group(1)
        module = find_module_by_slug(manifest, slug)
        if module:
            return f"[{module['title']}]({module['path']})"
        else:
            raise ValueError(f"Unknown slug: {slug}")

    return re.sub(r'\[slug:([a-z0-9-]+)\]', replace_slug, content)
```

### 5. Module Number Assignment

Numbers are computed at build time based on position in manifest:

```python
def assign_numbers(manifest: dict) -> dict:
    """Add localNum and globalNum to each module."""
    global_num = 0

    for level in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']:
        local_num = 0
        for module in manifest['core'][level]['modules']:
            global_num += 1
            local_num += 1
            module['globalNum'] = global_num
            module['localNum'] = local_num
            module['path'] = f"/{level}/module-{local_num:02d}"

    return manifest
```

---

## Migration Strategy

### Phase 1: Preparation (Non-Breaking)

1. **Create `curriculum.yaml`** with current structure
2. **Update scripts** to read from manifest (fallback to filesystem)
3. **Add `slug:` link support** (alongside existing links)
4. **Validate** manifest matches filesystem state

### Phase 2: File Rename (Breaking)

1. **Snapshot current state** (git tag: `pre-manifest-migration`)
2. **Rename all files** to remove number prefixes:
   ```bash
   # Script: scripts/migrate_to_slugs.py
   for file in curriculum/l2-uk-en/*/[0-9][0-9]-*.md:
       new_name=$(echo $file | sed 's|/[0-9][0-9]-|/|')
       git mv "$file" "$new_name"
   done
   ```
3. **Rename sidecars** (activities, meta, vocabulary)
4. **Update all internal links** to use `slug:` format
5. **Run full validation** pipeline

### Phase 3: Script Updates

Update all scripts to use manifest:

| Script | Change |
|--------|--------|
| `generate_mdx.py` | Read module order from manifest |
| `audit_module.py` | Resolve paths via manifest |
| `pipeline.py` | Use manifest for discovery |
| `validate_mdx.py` | Validate slug links |

### Phase 4: Documentation

1. Update `CLAUDE.md` with new conventions
2. Update all workflow docs
3. Update templates to use `slug:` links

---

## Schema Details

### Module Entry Schema

```yaml
# Required fields
- slug: string          # URL-safe identifier (a-z, 0-9, hyphens)
  title: string         # Display title

# Optional fields
  phase: string         # e.g., "A1.1", "B2.3"
  focus: enum           # grammar | vocabulary | cultural | checkpoint | practical | integration
  prerequisites: list   # [slug, slug, ...]
  tags: list            # [tag, tag, ...]

# Computed at build time (not in YAML)
  localNum: int         # Position within level
  globalNum: int        # Position in entire course
  path: string          # URL path
```

### Validation Rules

```python
VALIDATION_RULES = {
    'slug': {
        'pattern': r'^[a-z0-9]+(-[a-z0-9]+)*$',
        'unique': True,  # Across entire curriculum
        'max_length': 50
    },
    'title': {
        'required': True,
        'max_length': 100
    },
    'focus': {
        'allowed': ['grammar', 'vocabulary', 'cultural', 'checkpoint',
                    'practical', 'integration', 'history', 'biography']
    }
}
```

---

## Impact Analysis

### Files to Modify

| Category | Count | Notes |
|----------|-------|-------|
| Module MD files | ~570 | Rename only |
| Activity YAML files | ~570 | Rename only |
| Meta YAML files | ~570 | Rename only |
| Vocabulary YAML files | ~400 | Rename only |
| Python scripts | ~15 | Update path resolution |
| Workflow docs | ~10 | Update examples |
| Templates | ~8 | Update link format |

### Breaking Changes

1. **All file paths change** - but commit atomic
2. **Link format changes** - but `slug:` is additive first
3. **Script APIs change** - module number param → slug param

### Rollback Plan

```bash
# If migration fails, rollback to snapshot
git checkout pre-manifest-migration
git checkout -b post-manifest-rollback
```

---

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| Files renamed to insert 1 module | N-1 files | 0 files |
| Time to reorder 10 modules | ~2 hours | ~5 minutes |
| Risk of broken links | High | Near zero |
| Single source of truth | No (filesystem) | Yes (manifest) |

---

## Implementation Checklist

### Prerequisites

- [ ] All levels A1-C2 in stable state
- [ ] No pending major content changes

### Phase 1: Preparation

- [ ] Create `curriculum.yaml` from current state
- [ ] Write `scripts/manifest_utils.py` with loader/validator
- [ ] Add `slug:` link resolver to `generate_mdx.py`
- [ ] Test with subset of modules

### Phase 2: Migration

- [ ] Create git tag `pre-manifest-migration`
- [ ] Write `scripts/migrate_to_slugs.py`
- [ ] Run migration on all levels
- [ ] Verify no broken links

### Phase 3: Script Updates

- [ ] Update `generate_mdx.py`
- [ ] Update `audit_module.py`
- [ ] Update `pipeline.py`
- [ ] Update all path-dependent scripts

### Phase 4: Documentation

- [ ] Update `CLAUDE.md`
- [ ] Update workflow docs
- [ ] Update templates
- [ ] Create migration guide for contributors

---

## Decisions (Finalized 2026-01-17)

### 1. Single vs per-level manifests?

**Decision: Single `curriculum.yaml`**

Rationale: With ~600 modules it's ~2000 lines - manageable. Merge conflicts are rare since module ordering rarely changes. One source of truth is cleaner.

### 2. Track module numbering?

**Decision: Slug-only for tracks (no numbers)**

Tracks (b2-hist, c1-bio, b2-pro, c1-pro, lit) use:
- `slug:` field only in meta YAML
- No `module:` field with numbers
- Order determined by manifest, not by numbering

Core levels (a1, a2, b1, b2, c1, c2) retain numbered format until full migration.

**Cleanup required:**

| Track | Files with `module:` to remove |
|-------|-------------------------------|
| B2-HIST | 63 |
| C1-BIO | 101 |
| LIT | 23 |
| **Total** | **187** |

### 3. Backward compatibility period?

**Decision: Hard cutover**

Single atomic migration commit with git tag `pre-manifest-migration` for rollback. No dual-format support needed since this is a single-developer project.

---

## Appendix A: Current File Counts

```
Level   Modules   Activities   Meta    Vocab    Total Files
A1      34        34          34      34       136
A2      57        57          57      57       228
B1      91        91          91      91       364
B2      145       145         145     120      555
C1      202       202         202     150      756
C2      100       100         100     80       380
---------------------------------------------------
Total   629       629         629     532      2419
```

---

## Appendix B: Example Migration Script

```python
#!/usr/bin/env python3
"""
Migrate from numbered filenames to slug-based filenames.

Usage:
    python scripts/migrate_to_slugs.py --dry-run  # Preview changes
    python scripts/migrate_to_slugs.py            # Execute migration
"""

import re
import subprocess
from pathlib import Path

CURRICULUM_DIR = Path("curriculum/l2-uk-en")
LEVELS = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']
SIDECAR_DIRS = ['activities', 'meta', 'vocabulary', 'audit', 'review']

def extract_slug(filename: str) -> str:
    """Extract slug from numbered filename."""
    # 01-the-cyrillic-code-i.md -> the-cyrillic-code-i
    match = re.match(r'^\d{2,3}-(.+)\.(md|yaml)$', filename)
    if match:
        return match.group(1)
    return None

def migrate_level(level: str, dry_run: bool = True):
    """Migrate all files in a level."""
    level_dir = CURRICULUM_DIR / level

    # Migrate main .md files
    for md_file in level_dir.glob('[0-9][0-9]*.md'):
        slug = extract_slug(md_file.name)
        if slug:
            new_path = level_dir / f"{slug}.md"
            if dry_run:
                print(f"  {md_file.name} -> {new_path.name}")
            else:
                subprocess.run(['git', 'mv', str(md_file), str(new_path)])

    # Migrate sidecars
    for sidecar_dir in SIDECAR_DIRS:
        sidecar_path = level_dir / sidecar_dir
        if sidecar_path.exists():
            for yaml_file in sidecar_path.glob('[0-9][0-9]*.yaml'):
                slug = extract_slug(yaml_file.name)
                if slug:
                    new_path = sidecar_path / f"{slug}.yaml"
                    if dry_run:
                        print(f"  {sidecar_dir}/{yaml_file.name} -> {new_path.name}")
                    else:
                        subprocess.run(['git', 'mv', str(yaml_file), str(new_path)])

def main():
    import sys
    dry_run = '--dry-run' in sys.argv

    print(f"Migration mode: {'DRY RUN' if dry_run else 'EXECUTE'}\n")

    for level in LEVELS:
        print(f"\n=== {level.upper()} ===")
        migrate_level(level, dry_run)

    if not dry_run:
        print("\nMigration complete. Run validation pipeline.")

if __name__ == '__main__':
    main()
```

---

## Appendix C: Manifest Loader

```python
# scripts/manifest_utils.py
"""Utilities for working with curriculum manifest."""

import yaml
from pathlib import Path
from functools import lru_cache

MANIFEST_PATH = Path("curriculum/l2-uk-en/curriculum.yaml")

@lru_cache
def load_manifest() -> dict:
    """Load and cache curriculum manifest."""
    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)

def get_module_by_slug(slug: str) -> dict | None:
    """Find module by slug across all levels and tracks."""
    manifest = load_manifest()

    # Search core levels
    for level, data in manifest.get('core', {}).items():
        for module in data.get('modules', []):
            if module.get('slug') == slug:
                module['level'] = level
                module['track'] = 'core'
                return module

    # Search tracks
    for track, data in manifest.get('tracks', {}).items():
        for module in data.get('modules', []):
            if module.get('slug') == slug:
                module['level'] = track
                module['track'] = track
                return module

    return None

def get_modules_for_level(level: str) -> list[dict]:
    """Get ordered list of modules for a level."""
    manifest = load_manifest()
    return manifest.get('core', {}).get(level, {}).get('modules', [])

def validate_manifest() -> list[str]:
    """Validate manifest integrity. Returns list of errors."""
    errors = []
    manifest = load_manifest()
    seen_slugs = set()

    def check_modules(modules: list, context: str):
        for i, module in enumerate(modules):
            slug = module.get('slug')

            # Required fields
            if not slug:
                errors.append(f"{context}[{i}]: missing slug")
            elif not module.get('title'):
                errors.append(f"{context}[{i}] ({slug}): missing title")

            # Unique slugs
            if slug in seen_slugs:
                errors.append(f"{context}: duplicate slug '{slug}'")
            seen_slugs.add(slug)

            # Slug format
            if slug and not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', slug):
                errors.append(f"{context}: invalid slug format '{slug}'")

    # Check core
    for level, data in manifest.get('core', {}).items():
        check_modules(data.get('modules', []), f"core.{level}")

    # Check tracks
    for track, data in manifest.get('tracks', {}).items():
        check_modules(data.get('modules', []), f"tracks.{track}")

    return errors
```
