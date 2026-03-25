# Landing Page Sync Script - Implementation Plan

## Problem

The website landing pages (`intro.mdx`, `{level}/index.mdx`) show module counts and status that drift out of sync with actual curriculum state. Manual updates are error-prone.

## Solution

Create `scripts/sync_landing_pages.py` that:
1. Scans curriculum to get real module counts
2. Determines readiness status per level
3. Updates MDX landing pages with accurate data

---

## Data Sources (Truth)

| Data | Source |
|------|--------|
| Total modules per level | Count `curriculum/l2-uk-en/{level}/*.md` files |
| Ready modules | Count `docusaurus/docs/{level}/module-*.mdx` files |
| Planned modules | From `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md` (grep total) |
| Vocabulary per level | From curriculum plans or `vocabulary.db` |

## Status Logic

```python
def get_level_status(level, completion_pct):
    """
    Status based on module completion percentage.

    Note: "Complete" is never automatic - even 100% means "In QA".
    Complete status requires manual flag (e.g., in config or frontmatter).
    """
    if completion_pct == 100:
        return "🔍 In QA"        # All modules exist, needs final review
    elif completion_pct >= 10:
        return "🚧 In Progress"  # Actively being built
    else:
        return "📋 Planned"      # <10% or curriculum plan only
```

### Manual "Complete" Override

To mark a level as truly complete (passed QA), add to a config file:

```yaml
# docs/l2-uk-en/level-status.yaml
a1: complete   # Manually verified
a2: complete   # Manually verified
b1: auto       # Use calculated status
b2: auto
```

---

## Files to Update

### 1. `docusaurus/docs/intro.mdx`

**Curriculum Overview table:**
```markdown
| Level | Description | Lessons | Status |
|-------|-------------|---------|--------|
| **A1** | Beginner — ... | {actual_count} | {status} |
...
```

**Total count:**
```markdown
**Total:** {sum} lessons covering ~{vocab} vocabulary words
```

### 2. `docusaurus/docs/{level}/index.mdx`

**Header line:**
```markdown
**{status_emoji} — {ready}/{planned} модулів** | **~{vocab} нових слів**
```

---

## Implementation Steps

### Step 1: Data Collection

```python
def collect_curriculum_stats():
    stats = {}
    for level in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']:
        stats[level] = {
            'planned': count_in_curriculum_plan(level),
            'ready': count_mdx_files(level),
            'curriculum_files': count_md_files(level),
            'vocab_new': get_vocab_count(level),
        }
    return stats
```

### Step 2: Status Calculation

```python
STATUS_THRESHOLDS = {
    'qa': 1.0,          # 100% = In QA (needs final review)
    'progress': 0.10,   # 10-99% = In Progress
    'planned': 0.0,     # <10% = Planned
}

# "Complete" requires manual override in level-status.yaml
```

### Step 3: MDX Updates

Use regex replacement to update specific sections:
- Curriculum table in `intro.mdx`
- Header in each `{level}/index.mdx`
- Total counts

### Step 4: Validation

- Ensure no MDX syntax errors introduced
- Keep existing content structure intact
- Only update data placeholders

---

## Usage

```bash
# Preview changes (dry-run)
npm run sync:landing -- --dry-run

# Apply changes
npm run sync:landing

# Part of deploy pipeline
npm run deploy  # includes sync:landing
```

---

## Edge Cases

1. **LIT track** - Special handling (not CEFR level)
2. **Missing curriculum plan** - Use actual file count as planned
3. **Empty levels** - Show "📋 Planned" with 0/N

---

## Example Output

```
📊 Landing Page Sync

Level  Planned  Ready  Status
─────  ───────  ─────  ──────
A1     34       34     ✅ Complete
A2     57       57     ✅ Complete
B1     86       18     🚧 In Progress (21%)
B2     145      106    🔍 In QA (73%)
C1     182      0      📋 Planned
C2     100      0      📋 Planned
LIT    50       14     🚧 In Progress (28%)

Total: 654 modules (229 ready)

Updated:
  ✓ docusaurus/docs/intro.mdx
  ✓ docusaurus/docs/b1/index.mdx
  ✓ docusaurus/docs/b2/index.mdx
```

---

## Integration Points

1. **CI/CD** - Run on every push to main
2. **Pre-commit hook** - Optional, may slow commits
3. **GitHub Action** - Update pages after curriculum changes

---

## Future Enhancements

- [ ] Add vocabulary count from `vocabulary.db`
- [ ] Show activity counts per level
- [ ] Generate progress badges for README
- [ ] RSS feed for new modules
