# Context: Extract External Resources from Markdown (Issue #353)

**Agent:** C1-d (Claude Sonnet - New Session)
**Date:** 2026-01-02
**Priority:** P1 - Blocks podcast integration (#338)
**Issue:** #353 - Phase 3a: Extract External Resources

---

## Your Mission

Implement 4 Python scripts to extract, merge, validate, and regenerate external learning resources from curriculum markdown files.

**CRITICAL:** This work BLOCKS Issue #338 (podcast integration). We need to preserve 304 existing `[!resources]` sections before merging Gemini's 173 ULP podcast mappings.

---

## Background: Why This Matters

**Current state:**
- 304 curriculum modules have `[!resources]` sections with YouTube, articles, websites
- Gemini just completed mapping 173 podcast episodes to modules (`ulp_mapping.yaml`)
- No unified schema or database for external resources

**Problem:**
- Resources are embedded in markdown (hard to update, validate, dedupe)
- Need to merge podcast mappings WITHOUT losing existing resources
- Want single source of truth for all external learning resources

**Solution:**
1. **Extract** existing resources from markdown → YAML
2. **Merge** ULP podcast mappings into unified structure
3. **Validate** URLs, deduplication, episode IDs
4. **Generate** updated `[!resources]` sections from YAML

---

## Schema Design (Already Complete)

**READ THIS FIRST:** `/Users/krisztiankoos/projects/learn-ukrainian/docs/resources/EXTERNAL_RESOURCES_SCHEMA.md`

This schema defines:
- 5 resource types: `youtube`, `podcasts`, `articles`, `books`, `websites`
- Required fields per type
- Relevance levels: `high`, `medium`, `low`
- YAML structure (module-centric)
- Markdown generation template
- Validation rules

**Target output file:** `docs/resources/external_resources.yaml`

---

## Your Deliverables

### 1. Extraction Script ✅ CREATE THIS FIRST

**File:** `scripts/extract_external_resources.py`

**Purpose:** Parse all 304 markdown files, extract `[!resources]` sections, convert to YAML

**Algorithm:**
1. Find all module markdown files in `curriculum/l2-uk-en/{a1,a2,b1,b2,c1,c2}/`
2. For each file:
   - Locate `> [!resources]` callout block
   - Parse resource items (YouTube, articles, etc.)
   - Classify resource type based on URL pattern:
     - `youtube.com/watch` or `youtu.be/` → `youtube`
     - `ukrainianlessons.com/lesson/` or `/fmu` → `podcasts`
     - Other URLs → `articles` or `websites`
   - Extract: title, URL, source/channel
   - Infer relevance (default: `high` for existing resources)
   - Structure by module_id

3. Write to `docs/resources/external_resources.yaml`

**CLI:**
```bash
.venv/bin/python scripts/extract_external_resources.py \
  --curriculum curriculum/l2-uk-en/ \
  --output docs/resources/external_resources.yaml
```

**Edge cases to handle:**
- Modules with no `[!resources]` section (skip)
- Malformed resource items (log warning, skip)
- Duplicate URLs within same module (keep first)

### 2. Merge Script

**File:** `scripts/merge_podcast_mappings.py`

**Purpose:** Merge Gemini's ULP mappings into extracted resources

**Input:**
- `docs/resources/external_resources.yaml` (from extraction)
- `docs/resources/podcasts/ulp_mapping.yaml` (Gemini's work)

**Algorithm:**
1. Load both YAML files
2. For each mapping in `ulp_mapping.yaml`:
   - Get `module_id` (e.g., `a1-09-food-and-drinks`)
   - For each `recommended_episodes`:
     - Check if episode already exists in module's `podcasts` array
     - If NOT exists: Add to module's `podcasts` array
     - If exists: Update `relevance` and `match_reason` if Gemini's is better
3. Write merged result to `docs/resources/external_resources.yaml`

**CLI:**
```bash
.venv/bin/python scripts/merge_podcast_mappings.py \
  --existing docs/resources/external_resources.yaml \
  --podcasts docs/resources/podcasts/ulp_mapping.yaml \
  --output docs/resources/external_resources.yaml
```

**Deduplication logic:**
- Same `episode_id` in same module → merge (keep highest relevance)
- Same YouTube URL → deduplicate
- Same article URL → deduplicate

### 3. Validation Script

**File:** `scripts/validate_external_resources.py`

**Purpose:** Validate YAML structure, check URLs, verify episode IDs

**Validation checks:**

**ERRORS (must fix):**
- Invalid YAML syntax
- Missing required fields (title, url, relevance)
- Invalid relevance value (not high/medium/low)
- Podcast `episode_id` doesn't exist in `podcast_db.json`
- Duplicate URLs within same module
- Module IDs don't exist in curriculum

**WARNINGS (log only):**
- Missing `description` for high-relevance resources
- More than 10 resources per type per module
- YouTube URL format doesn't match standard patterns
- HTTP 404 URLs (optional check with `--check-urls` flag)

**CLI:**
```bash
.venv/bin/python scripts/validate_external_resources.py \
  docs/resources/external_resources.yaml

# Optional URL health check (slow)
.venv/bin/python scripts/validate_external_resources.py \
  docs/resources/external_resources.yaml \
  --check-urls
```

**Output:**
- Exit 0 if valid
- Exit 1 if errors found
- Print summary: X errors, Y warnings

### 4. Generation Script

**File:** `scripts/generate_resource_sections.py`

**Purpose:** Regenerate `[!resources]` markdown sections from YAML

**Algorithm:**
1. Load `docs/resources/external_resources.yaml`
2. For each module_id:
   - Find markdown file in curriculum
   - Locate existing `> [!resources]` section (or insert location)
   - Generate new section using template:
     ```markdown
     > [!resources] 🔗 External Resources
     >
     > **🎧 Podcasts:**
     > - [ULP 1-11: Title](url) — Description
     >
     > **📺 YouTube:**
     > - [Video Title](url) — Channel Name
     >
     > **📖 Articles:**
     > - [Article Title](url) — Description
     ```
   - Sort resources: Podcasts → YouTube → Articles → Books → Websites
   - Within type: high relevance first, then medium, then low
   - Replace existing section with generated content

3. Write updated markdown file

**CLI:**
```bash
# Dry run (show changes, don't write)
.venv/bin/python scripts/generate_resource_sections.py \
  --input docs/resources/external_resources.yaml \
  --curriculum curriculum/l2-uk-en/ \
  --dry-run

# Execute (write files)
.venv/bin/python scripts/generate_resource_sections.py \
  --input docs/resources/external_resources.yaml \
  --curriculum curriculum/l2-uk-en/
```

**Template per schema:** See `EXTERNAL_RESOURCES_SCHEMA.md` section "Markdown Generation"

---

## Implementation Order

**DO THESE IN ORDER:**

1. ✅ Read schema: `docs/resources/EXTERNAL_RESOURCES_SCHEMA.md`
2. ✅ Read ULP mapping review: `docs/dev/ULP_MAPPING_REVIEW.md`
3. ⏳ Implement `extract_external_resources.py`
4. ⏳ Test extraction on 5 sample modules
5. ⏳ Run extraction on all 304 modules
6. ⏳ Implement `merge_podcast_mappings.py`
7. ⏳ Test merge on sample data
8. ⏳ Run merge on full dataset
9. ⏳ Implement `validate_external_resources.py`
10. ⏳ Run validation, fix any errors
11. ⏳ Implement `generate_resource_sections.py`
12. ⏳ Test generation with `--dry-run` on 5 modules
13. ⏳ Visual review of dry-run output
14. ⏳ Run generation on all modules
15. ✅ Verify round-trip: extract → merge → validate → generate
16. ✅ Report completion

---

## Test Modules for Development

Use these 5 modules for testing (diverse resource types):

1. **a1-07-questions-and-negation.md** - Has YouTube + articles
2. **a1-09-food-and-drinks.md** - Will gain ULP podcasts
3. **b1-06-aspect-complete-system.md** - Complex grammar, likely has resources
4. **b2-75-volodymyr-i-khreshchennia.md** - History module, likely has books/articles
5. **a2-12-aspect-introduction.md** - Gemini mapped ULP episodes here

**Test workflow:**
```bash
# Extract sample
.venv/bin/python scripts/extract_external_resources.py \
  --curriculum curriculum/l2-uk-en/ \
  --output /tmp/test_resources.yaml \
  --modules a1-07 a1-09 b1-06 b2-75 a2-12

# Merge sample
.venv/bin/python scripts/merge_podcast_mappings.py \
  --existing /tmp/test_resources.yaml \
  --podcasts docs/resources/podcasts/ulp_mapping.yaml \
  --output /tmp/test_merged.yaml

# Validate
.venv/bin/python scripts/validate_external_resources.py /tmp/test_merged.yaml

# Generate (dry run)
.venv/bin/python scripts/generate_resource_sections.py \
  --input /tmp/test_merged.yaml \
  --curriculum curriculum/l2-uk-en/ \
  --dry-run \
  --modules a1-07 a1-09 b1-06 b2-75 a2-12
```

---

## Dependencies & References

**Files to read:**
- `docs/resources/EXTERNAL_RESOURCES_SCHEMA.md` - **MANDATORY** (schema definition)
- `docs/resources/podcasts/ulp_mapping.yaml` - Gemini's podcast mappings (173 mappings)
- `docs/resources/podcasts/podcast_db.json` - Episode metadata database
- `docs/dev/ULP_MAPPING_REVIEW.md` - Quality review of podcast mappings

**Python libraries available:**
- `PyYAML` - YAML parsing
- `pathlib` - File operations
- `re` - Regex for parsing markdown

**Module ID format:**
- `{level}-{number}-{slug}` (e.g., `a1-07-questions-and-negation`)
- Derived from file path: `curriculum/l2-uk-en/a1/07-questions-and-negation.md`

---

## Success Criteria

✅ You've completed Issue #353 when:

1. All 4 scripts exist and are functional
2. Extraction runs on 304 modules without errors
3. Merge successfully integrates 173 ULP mappings
4. Validation passes (0 errors)
5. Generation produces valid markdown (tested with dry-run)
6. Round-trip verified: Original resources preserved + ULP added
7. File exists: `docs/resources/external_resources.yaml` (complete)
8. Updated `AGENT_COORDINATION.md` with completion status

---

## What NOT to Do

- ❌ Don't modify ULP mapping file (`ulp_mapping.yaml`) - it's Gemini's work
- ❌ Don't skip validation before generation
- ❌ Don't overwrite markdown files without dry-run testing
- ❌ Don't add new resources not in source data
- ❌ Don't change relevance levels without justification

---

## Questions & Support

**If unclear:**
1. Read schema document again
2. Check ULP mapping review for context
3. Ask coordinator (C1-a) for clarification

**Common issues:**
- Markdown parsing - Use regex for `> [!resources]` block extraction
- URL classification - Check schema for URL patterns per type
- Deduplication - Compare URLs, not titles (titles may vary)

---

## Deliverable Checklist

Before reporting completion, verify:

- [ ] `scripts/extract_external_resources.py` exists and works
- [ ] `scripts/merge_podcast_mappings.py` exists and works
- [ ] `scripts/validate_external_resources.py` exists and works
- [ ] `scripts/generate_resource_sections.py` exists and works
- [ ] `docs/resources/external_resources.yaml` created (all 304 modules)
- [ ] Validation passes (0 errors)
- [ ] Dry-run generation tested on 5 sample modules
- [ ] Round-trip verified (extract → merge → validate → generate → compare)
- [ ] Documentation updated (if needed)
- [ ] Completion reported to coordinator (C1-a)

---

**Ready to start?** Begin by reading the schema document, then implement extraction script first.
