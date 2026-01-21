# Phase 7: module-integrate

Deploy module with skeleton vocabulary. Full vocab enrichment runs separately.

## Usage

```
/module-integrate {level} {module_num}
```

## Input (LOCKED from previous phases)

- `curriculum/l2-uk-en/{level}/meta/{slug}.yaml` (Phase 2)
- `curriculum/l2-uk-en/{level}/{slug}.md` (Phase 4)
- `curriculum/l2-uk-en/{level}/activities/{slug}.yaml` (Phase 6)

## Output

- `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml` (skeleton)
- `docusaurus/docs/{level}/module-{num}.mdx` (deployment)
- `curriculum/l2-uk-en/{level}/audit/{slug}-review.md` (report)

---

## Integration Process

### Step 1: Verify Locked Files Present

Check that content files exist:

```bash
files=(
  "curriculum/l2-uk-en/{level}/meta/{slug}.yaml"
  "curriculum/l2-uk-en/{level}/{slug}.md"
  "curriculum/l2-uk-en/{level}/activities/{slug}.yaml"
)

for file in "${files[@]}"; do
  if [[ ! -f "$file" ]]; then
    FAIL: Missing locked file: $file
  fi
done
```

### Step 2: Create Skeleton Vocabulary

**Create empty vocabulary file if it doesn't exist:**

```yaml
# curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml
module: { slug }
level: { LEVEL }
version: '2.0'
items: [] # Empty - will be enriched by /module-vocab-enrich
```

**If file already exists:** Use existing (may be partially enriched).

### Step 3: Cross-File Consistency Checks

#### 3.1 Metadata Consistency

```python
# Check all files have matching module identifiers
meta = yaml.safe_load(open(f'meta/{slug}.yaml'))

# Extract frontmatter from lesson
with open(f'{slug}.md') as f:
    frontmatter = parse_frontmatter(f.read())

if meta['id'] != frontmatter['module']:
    FAIL: Module ID mismatch between meta and lesson
```

#### 3.2 Word Count Verification

```python
word_target = meta['word_target']
actual_words = count_ukrainian_words(lesson_text)
deviation = abs(actual_words - word_target) / word_target

if deviation > 0.05:
    FAIL: Word count {actual_words} deviates >5% from target {word_target}
```

#### 3.3 Activity Count Verification

```python
minimums = get_minimums(meta['level'])
activity_counts = count_activities_by_type(activities)

if activity_counts['total_activities'] < minimums['total_activities']:
    FAIL: Total activities below minimum
```

### Step 4: Generate MDX

Run the official generator script to build the MDX file. This script handles:
- Correct filename generation (slug vs module-N)
- Activity component rendering
- Callout conversion
- Vocabulary table injection

```bash
python scripts/generate_mdx.py l2-uk-en {level} {num}
```

**Verify output:**
- For Core (A1-C2): `docusaurus/docs/{level}/module-{num}.mdx`
- For Tracks (b2-hist, etc): `docusaurus/docs/{level}/{slug}.mdx`

### Step 5: Generate Audit Report

Create `audit/{slug}-review.md`:

```markdown
# Module Integration Report

**Module:** {level}-{num} ({title})
**Date:** {timestamp}
**Status:** DEPLOYED (skeleton vocab)

## Phase Status

✓ Phase 1: module-meta (LOCKED)
✓ Phase 2: module-meta-qa (PASSED)
✓ Phase 3: module-lesson (LOCKED)
✓ Phase 4: module-lesson-qa (PASSED)
✓ Phase 5: module-act (LOCKED)
✓ Phase 6: module-act-qa (PASSED)
✓ Phase 7: module-integrate (COMPLETE)

⏳ Vocabulary: Skeleton only (run /module-vocab-enrich after track complete)

## Quality Metrics

### Lesson

- Word count: {actual}/{target} ({percentage}%)
- Example sentences: {count}
- Engagement boxes: {count}

### Activities

- Total activities: {count}
- Quiz items: {count}

### Vocabulary

- Items: 0 (skeleton)
- Status: Awaiting enrichment

## Files

- meta/{slug}.yaml
- {slug}.md ({word_count} words)
- activities/{slug}.yaml ({activity_count} activities)
- vocabulary/{slug}.yaml (skeleton)
- docusaurus/docs/{level}/{mdx_filename}

## Next Steps

1. Preview: http://localhost:3000/docs/{level}/{slug_or_module_num}
2. When track complete: /module-vocab-enrich {level}
```

---

## Output

### On SUCCESS

```
INTEGRATION COMPLETE: {level}/{slug}

✓ Meta verified
✓ Lesson verified ({word_count} words)
✓ Activities verified ({activity_count} activities)
✓ Skeleton vocabulary created
✓ MDX generated: docusaurus/docs/{level}/{mdx_filename}
✓ Audit report: audit/{slug}-review.md

Preview: http://localhost:3000/docs/{level}/{slug_or_module_num}

Note: Vocabulary table is empty.
      Run /module-vocab-enrich {level} when track is complete.
```

### On FAILURE

```
INTEGRATION FAILED: {level}/{slug}

Violations:
1. [CHECK_NAME]: {specific issue}

Fix and re-run: /module-integrate {level} {module_num}
```

---

## Deployment Checklist

After integration:

- [ ] MDX file generated
- [ ] Start dev server: `cd docusaurus && pnpm start`
- [ ] Preview module at localhost:3000
- [ ] Test all interactive activities
- [ ] Vocabulary table shows "No items" (expected with skeleton)

When track complete:

- [ ] Run /module-vocab-enrich {level}
- [ ] Verify vocabulary tables populated
- [ ] Run `npm run docs:build`
- [ ] Deploy to production
