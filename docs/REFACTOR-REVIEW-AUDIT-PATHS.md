# Refactoring Plan: Standardize Review/Audit File Paths & Slug Format

> **Status**: DRAFT — awaiting Gemini review
> **Date**: 2026-02-09
> **Scope**: 11 Python files, ~25 path construction references, ~600 files on disk

## Problem Statement

### Problem 1: Reviews and audits are mixed across directories

Reviews (`*-review.md`) appear in BOTH `audit/` and `review/` directories depending on which script created them. This causes:
- `review_validation.py` needs a dual-directory fallback search
- `batch_gemini_runner.py` deletes from one dir but the file exists in the other
- Agents (Claude/Gemini) guess which directory to use, creating more inconsistency

**Current state by track:**

| Track | `audit/` contents | `review/` contents |
|-------|-------------------|-------------------|
| a1 | 108 files: audit-report + audit + review mixed | 46 review files |
| a2 | 72 files: audit-report + review mixed | 71 review files |
| b1 | 6 files: audit-report + review mixed | 95 review files |
| b2 | 1 review file | 99 review files |
| b2-hist | 134 review files | 140 review files |
| c1 | 2 files: audit-report + review | 108 review files |
| c1-bio | 11 files: audit-report + review | (in review/) |
| c1-hist | 1 audit-report | 6 review files |
| lit | 35 review files | 21 review files |

### Problem 2: Slug format inconsistency

Numbered tracks (a1, a2, b1, b2, c1, c2) have `.md` files like `01-the-cyrillic-code-i.md`. But derived artifacts (reviews, audits, status) use inconsistent slugs:
- `audit/01-the-cyrillic-code-i-audit-report.md` (numbered)
- `audit/the-cyrillic-code-i-review.md` (bare — batch_gemini_runner strips numbers)
- `status/01-the-cyrillic-code-i.json` (numbered — audit/report.py uses stem)

Seminar tracks (c1-bio, b2-hist, etc.) have bare slugs naturally: `knyahynia-olha.md`.

## Target State

### Directory structure

```
curriculum/l2-uk-en/{track}/
├── {num}-{slug}.md              # Content (numbered for core, bare for seminar)
├── meta/{slug}.yaml             # Always bare slug
├── activities/{slug}.yaml       # Always bare slug
├── vocabulary/{slug}.yaml       # Always bare slug
├── audit/                       # ONLY machine-generated audit artifacts
│   ├── {slug}-audit.md          # Audit report (from audit_module.py)
│   ├── {slug}-grammar.yaml      # Grammar validation results
│   └── {slug}-quality.md        # Activity quality report
├── review/                      # ONLY LLM-generated reviews
│   └── {slug}-review.md         # Review (from phase 5)
├── status/                      # Cached audit results
│   └── {slug}.json              # Status cache (from audit)
└── orchestration/{slug}/        # Temp files for orchestrated builds
    ├── phase-*-prompt.md
    ├── phase-*-output.md
    └── fix-changes.md
```

### Slug rules

- **Bare slug** for ALL derived artifacts (audit, review, status, meta, activities, vocabulary)
- **Numbered slug** only for the `.md` content file in core tracks
- Bare slug = strip leading `\d+-` from the content filename stem
- A helper function `to_bare_slug(filename_or_slug)` used everywhere

### File naming

| Artifact | Directory | Filename | Example |
|----------|-----------|----------|---------|
| Content | `{track}/` | `{num}-{slug}.md` or `{slug}.md` | `01-the-cyrillic-code-i.md` |
| Meta | `{track}/meta/` | `{slug}.yaml` | `the-cyrillic-code-i.yaml` |
| Activities | `{track}/activities/` | `{slug}.yaml` | `the-cyrillic-code-i.yaml` |
| Vocabulary | `{track}/vocabulary/` | `{slug}.yaml` | `the-cyrillic-code-i.yaml` |
| Audit report | `{track}/audit/` | `{slug}-audit.md` | `the-cyrillic-code-i-audit.md` |
| Grammar check | `{track}/audit/` | `{slug}-grammar.yaml` | `the-cyrillic-code-i-grammar.yaml` |
| Quality check | `{track}/audit/` | `{slug}-quality.md` | `the-cyrillic-code-i-quality.md` |
| Review | `{track}/review/` | `{slug}-review.md` | `the-cyrillic-code-i-review.md` |
| Status cache | `{track}/status/` | `{slug}.json` | `the-cyrillic-code-i.json` |

## Files to Modify

### Phase 1: Add `to_bare_slug()` utility

**New file: `scripts/audit/slug_utils.py`**

```python
import re

def to_bare_slug(name: str) -> str:
    """Strip leading number prefix from slug or filename stem.

    '01-the-cyrillic-code-i' -> 'the-cyrillic-code-i'
    'knyahynia-olha' -> 'knyahynia-olha' (no change)
    '01-the-cyrillic-code-i.md' -> 'the-cyrillic-code-i'
    """
    stem = re.sub(r'\.\w+$', '', name)  # strip extension
    return re.sub(r'^\d+-', '', stem)

def review_path(track_dir, slug):
    """Canonical review file path."""
    return track_dir / "review" / f"{to_bare_slug(slug)}-review.md"

def audit_path(track_dir, slug):
    """Canonical audit report path."""
    return track_dir / "audit" / f"{to_bare_slug(slug)}-audit.md"

def status_path(track_dir, slug):
    """Canonical status JSON path."""
    return track_dir / "status" / f"{to_bare_slug(slug)}.json"
```

### Phase 2: Update all 11 Python files

Each file listed below with the specific changes needed:

#### 1. `scripts/audit/checks/review_validation.py` (3 references)

**Current**: Dual-directory search (`audit/` then `review/`), tries both bare and numbered slug
**Target**: Single lookup via `review_path()`, bare slug only

- Line 251-273: Replace dual-directory search with `slug_utils.review_path()`
- Remove `slugs_to_try` logic entirely
- Remove fallback to `audit/` directory

#### 2. `scripts/batch_gemini_runner.py` (7 references)

**Current**: Hardcoded `audit/` paths for reviews, manual `re.sub(r"^\d+-", "", slug)`
**Target**: Use `slug_utils.review_path()` and `slug_utils.audit_path()`

- Line 201: `review_file = paths["md"].parent / "audit" / ...` → `slug_utils.review_path()`
- Line 271: `output_path = ... / "audit" / ...` → `slug_utils.review_path()`
- Line 397: `_delete_review_files()` — simplify to single path delete
- Line 593: review path in `_apply_output()` → `slug_utils.review_path()`
- Line 720: review path in fix loop → `slug_utils.review_path()`
- Line 875: review path in build mode → `slug_utils.review_path()`
- Remove all inline `re.sub(r"^\d+-", "", slug)` calls, use `to_bare_slug()`

#### 3. `scripts/audit/report.py` (3 references)

**Current**: Saves audit report as `{stem}-audit-report.md` (with number prefix), saves review-related output to `audit/`
**Target**: Save audit report as `{bare_slug}-audit.md` to `audit/`, never write reviews

- Line 651-657: `save_report()` → use `slug_utils.audit_path()`, rename `-audit-report.md` to `-audit.md`
- Line 860: `append_mdx_errors_to_report()` → write to `audit/` (correct, just fix slug)
- Line 954: `append_html_errors_to_report()` → same fix

#### 4. `scripts/audit/core.py` (2 references)

**Current**: Reads grammar and quality files from `audit/` using `base_name` (may include number prefix)
**Target**: Use `to_bare_slug()` for grammar and quality file lookups

- Line 1884-1885: grammar file path → use `to_bare_slug(base_name)`
- Line 1922: quality file path → use `to_bare_slug(base_name)`

#### 5. `scripts/audit/naturalness_check.py` (1 reference)

**Current**: Appends naturalness results to `audit/{stem}-review.md`
**Target**: Append to `review/{bare_slug}-review.md` (it's review content, not audit)

- Line 319: `audit_path = md_path.parent / 'audit' / ...` → `slug_utils.review_path()`

#### 6. `scripts/batch_fix_review.py` (1 reference)

**Current**: Points to `review/{full_stem}-review.md` (includes number prefix)
**Target**: Use `slug_utils.review_path()`

- Line 68: `"review": level_dir / f"review/{full_stem}-review.md"` → use bare slug

#### 7. `scripts/rehash_module.py` (2 references)

**Current**: Looks for `-llm-review.md` and `-review.md` in `audit/`
**Target**: Look only in `review/` for `-review.md`

- Line 37-42: Replace both lookups with `slug_utils.review_path()`

#### 8. `scripts/batch_audit_and_review.py` (1 reference)

**Current**: Saves to `audit/{slug}-llm-review.md`
**Target**: Save to `review/{bare_slug}-review.md`

- Line 56-60: Replace audit dir + llm-review path with `slug_utils.review_path()`

#### 9. `scripts/batch_review.py` (1 reference)

**Current**: Stores Gemini response in `orchestration/` (this is fine)
**Target**: No change needed for orchestration files, but ensure final review goes to `review/`

#### 10. `scripts/audit/finalize_activity_quality.py` (1 reference)

**Current**: Saves to `audit/{module_slug}-quality.md`
**Target**: Ensure bare slug: `audit/{bare_slug}-quality.md`

- Line 390-392: Use `to_bare_slug()` on `module_slug`

#### 11. `scripts/status/create_reviews.py` (1 reference)

**Current**: Creates `audit/{slug}-llm-review.md`
**Target**: Create `review/{bare_slug}-review.md`

- Line 43-48: Change dir from `audit` to `review`, drop `-llm-` prefix, use bare slug

### Phase 3: Migrate existing files on disk

**Script: `scripts/migrate_audit_review_files.py`**

```
For each track:
  1. Move all *-review.md from audit/ to review/ (bare slug)
  2. Rename *-audit-report.md to *-audit.md (bare slug)
  3. Rename *-llm-review.md to *-review.md, move to review/ (bare slug)
  4. Rename numbered artifacts to bare slug
  5. Delete duplicates (keep newest)
  6. Delete empty audit/ dirs that have no audit files left

Dry-run mode: --dry-run shows what would happen
```

**Expected file movements:**
- ~370 review files moved from `audit/` → `review/`
- ~200 files renamed from numbered to bare slug
- ~100 `-audit-report.md` → `-audit.md` renames
- ~50 `-llm-review.md` → `-review.md` renames + moves
- Duplicates resolved (keep newest mtime)

### Phase 4: Update status JSON paths

The `status/{slug}.json` files currently use numbered slugs in some tracks. The migration script should also:
- Rename `status/01-the-cyrillic-code-i.json` → `status/the-cyrillic-code-i.json`
- Update any internal references to file paths within the JSON

### Phase 5: Update documentation and templates

- `CLAUDE.md` — Update project structure section
- `docs/ARCHITECTURE.md` — Update file layout
- `claude_extensions/phases/gemini/` — Ensure templates reference correct paths
- `.gitignore` — Ensure audit/ and review/ patterns are correct

## Verification

```bash
# 1. Run migration in dry-run
.venv/bin/python scripts/migrate_audit_review_files.py --dry-run

# 2. Run migration
.venv/bin/python scripts/migrate_audit_review_files.py

# 3. Verify no reviews in audit/
fd -e md 'review' curriculum/l2-uk-en/*/audit/
# Expected: 0 results

# 4. Verify no audit-reports in review/
fd -e md 'audit' curriculum/l2-uk-en/*/review/
# Expected: 0 results

# 5. Verify no numbered slugs in status/
fd -e json '^\d+-' curriculum/l2-uk-en/*/status/
# Expected: 0 results

# 6. Run audit on a module from each tier
scripts/audit_module.sh curriculum/l2-uk-en/a1/01-the-cyrillic-code-i.md
scripts/audit_module.sh curriculum/l2-uk-en/c1-bio/knyahynia-olha.md

# 7. Run fix mode on a module from each tier
.venv/bin/python scripts/batch_gemini_runner.py a1 --range 1 --mode fix
.venv/bin/python scripts/batch_gemini_runner.py c1-bio --range 1 --mode fix

# 8. Run unit tests
.venv/bin/python -m pytest tests/test_batch_fix_mode.py -v
```

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Migration breaks git history | Migration is rename/move — git tracks this |
| Missed a path reference | Grep verification: `rg -n 'audit.*review\|review.*audit' scripts/` |
| Status JSONs have internal path refs | Migration script checks and updates |
| Existing fix-mode checkpoints invalid | Clear batch_state/ after migration |
| Other agents write to old paths | Update CLAUDE.md + AGENTS.md with new standard |

## Implementation Order

1. Create `slug_utils.py` + tests
2. Update all 11 Python files to use `slug_utils`
3. Run full test suite
4. Create + run migration script (dry-run first)
5. Run migration for real
6. Verify with audit + fix mode tests
7. Update documentation
8. Commit as single atomic change
