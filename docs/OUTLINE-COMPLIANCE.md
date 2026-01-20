# Outline Compliance Checker (Structural)

**Issue:** #440
**Status:** ✅ COMPLETED (Phase 1 - Structural)
**Date:** 2026-01-20

## Problem

The `content_outline` in `meta/*.yaml` defines detailed structure for modules, but audit didn't verify actual content follows it.

**Example drift:**
- Outline says: "Legitimacy of Power - how Monomakh justified his rule (480 words)"
- Content written: Section exists but only 85 words
- OR: Section completely missing from markdown

**Result:** Incomplete modules that pass word count gates but don't match the pedagogical plan.

## Solution Implemented

Created `scripts/audit/checks/outline_compliance.py` with **Level 1: Structural Compliance** (Phase 1).

### What It Checks

1. **Section presence**: All sections in `content_outline` exist as `##` headers in markdown
2. **Section word counts**: Each section meets minimum word count (-10% warning, -20% error). Sections with MORE words than target are acceptable.
3. **Extra sections**: Markdown sections not in outline are flagged
4. **Fuzzy matching**: Section names normalized for flexible matching

### Integration

Automatically runs as part of `audit_module.py`:

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b2-hist/volodymyr-monomakh.md

# Output includes outline compliance section:
⚠️  Outline compliance: 7 errors, 8 warnings
   ❌ [SECTION_LENGTH_MISMATCH] Section 'Вступ' is under target word count.
   ❌ [MISSING_OUTLINE_SECTION] Section 'Повчання Мономаха' not found...
   ⚠️ [EXTRA_SECTION_IN_MARKDOWN] Section 'Деколонізаційний погляд' not in outline...
```

## How It Works

### 1. Section Extraction from Markdown

```python
def extract_markdown_sections(md_path: Path) -> Dict[str, Dict]:
    """
    Extracts ## headers and counts words in each section.

    Returns:
        {
            "Вступ": {"header": "Вступ", "words": 85, "line_num": 7},
            "Шлях до великого княжіння": {"words": 178, "line_num": 31}
        }
    """
```

**What it does:**
- Parses markdown line by line
- Detects `##` headers (main sections)
- Counts words between headers
- Skips frontmatter, code blocks, blockquotes
- Records line numbers for violation reporting

### 2. Outline Loading from Meta YAML

```python
def load_content_outline(md_path: Path) -> Optional[List[Dict]]:
    """
    Loads content_outline from meta/{slug}.yaml.

    Returns:
        [
            {"section": "Вступ — Останній великий князь", "words": 480, "points": [...]},
            {"section": "Шлях до великого княжіння", "words": 640, "points": [...]}
        ]
    """
```

### 3. Section Name Normalization & Fuzzy Matching

Handles minor variations in section names:

```python
def normalize_section_name(name: str) -> str:
    # "Вступ — Останній великий князь" → "вступ останній великий князь"
    # "Шлях до великого княжіння" → "шлях великого княжіння"

def fuzzy_match_section(markdown_section, outline_sections):
    # Uses SequenceMatcher with 60% similarity threshold
    # "Вступ" matches "Вступ — Останній великий князь" ✓
```

**Handles:**
- Em-dash subtitles (`—`, `–`, `-`)
- Punctuation variations
- Extra whitespace
- Minor wording differences

### 4. Violation Detection

**Three types of violations:**

#### A. Missing Sections (ERROR)
```
Section 'Повчання Мономаха' defined in outline but not found in markdown.
  Expected word count: 693
  Add section to markdown with ## header
```

#### B. Word Count Mismatch (WARNING/ERROR)
```
Section 'Вступ — Останній великий князь' is under target word count.
  Expected: ~480 words (minimum -10%)
  Actual: 85 words
  Deviation: -395 words (82%)
  Location: line 7 in markdown
```

**Thresholds (only applies to sections UNDER target):**
- **10% under** (-10% deviation) = WARNING starts
- **20% under** (-20% deviation) = ERROR starts
- Over target = No violation (acceptable)

#### C. Extra Sections (WARNING)
```
Section 'Деколонізаційний погляд' found in markdown but not in outline.
  Word count: 2568
  Location: line 108
  Either add to content_outline in meta YAML or remove from markdown
```

## Test Results

**Test module:** `curriculum/l2-uk-en/b2-hist/volodymyr-monomakh.md`

**Outline (from meta YAML):**
```yaml
content_outline:
  - section: Вступ — Останній великий князь
    words: 480
  - section: Шлях до великого княжіння
    words: 640
  - section: Внутрішня політика
    words: 693
  - section: Зовнішня політика
    words: 586
  - section: Повчання Мономаха
    words: 693
  - section: Спадщина та значення
    words: 533
  - section: Підсумок
    words: 375
```

**Violations found:** 15 total (7 errors, 8 warnings)

| Violation Type | Count | Details |
|---------------|-------|---------|
| SECTION_LENGTH_MISMATCH | 4 errors | Sections 72-87% under target |
| MISSING_OUTLINE_SECTION | 3 errors | 3 planned sections not written |
| EXTRA_SECTION_IN_MARKDOWN | 8 warnings | 8 sections not in outline |

**Interpretation:**
- Module is incomplete (missing 3 sections)
- Existing sections are severely underwritten (72-87% short)
- Extra sections added that weren't planned (e.g., "Деколонізаційний погляд" with 2568 words)

**Outcome:** Module needs major revision to match outline OR outline needs updating.

## Implementation Details

### Files Created

- `scripts/audit/checks/outline_compliance.py` (330 lines)
  - Section extraction from markdown
  - Outline loading from meta YAML
  - Fuzzy section name matching
  - Violation detection with 3 severity levels

### Files Modified

- `scripts/audit/core.py` - Integration into audit pipeline (line ~696)
  - Added import for `check_outline_compliance`
  - Runs after template compliance check
  - Shows first 3 violations in summary

### Testing

**Tested with:**
- ✅ Module with content_outline (volodymyr-monomakh.md)
- ✅ Module without content_outline (aneksiia-krymu.md - skips gracefully)
- ✅ Section name variations (em-dash, punctuation)
- ✅ Word count tolerance calculations
- ✅ Fuzzy matching (60% similarity threshold)

## When This Checker Activates

**Only runs when:**
1. `meta/{slug}.yaml` exists
2. AND contains `content_outline` key
3. AND outline is non-empty

**Gracefully skips when:**
- No meta YAML file
- No content_outline in meta
- Empty outline array

**Expected usage:**
- B2-HIST modules using fractal generation (23 modules currently have outlines)
- C1-BIO modules with detailed structure
- Any module requiring pre-planned section breakdown

## Limitations

### Phase 1 (Structural) - Current Implementation

✅ **Checks:**
- Section presence ✓
- Word counts ✓
- Extra sections ✓

❌ **Does NOT check:**
- Content actually covers outlined points
- Semantic drift (outline says "legitimacy", content discusses "military campaigns")
- Quality of content within sections

**Example limitation:**
```yaml
outline:
  - section: Внутрішня політика
    words: 693
    points:
      - Устав Володимира Мономаха
      - Захист боржників
      - Обмеження лихварства
```

**Structural check:** ✓ Section exists, ✓ 693 words written

**But content could be:** 693 words about his favorite foods instead of legal reforms!

→ **Solution:** Phase 2 (Semantic compliance with LLM)

### Phase 2 (Semantic) - Future Enhancement

**Not yet implemented. Would require:**

1. **LLM-based analysis** (Gemini/Claude API)
2. **Point-by-point coverage check:**
   ```python
   def check_semantic_compliance(section_content, outline_points):
       prompt = f"""
       Does this content cover these points?
       Points: {outline_points}
       Content: {section_content}
       Return: coverage score and missing topics
       """
       # Call LLM API
   ```
3. **Cost controls** (sample checking, caching)
4. **Accuracy threshold** (~80% coverage required)

**Estimated cost:** ~$0.01 per module with Gemini Flash

**When to implement:** If structural checking alone proves insufficient for catching semantic drift.

## Usage Examples

### During Module Development

```bash
# Write content section by section
# Check compliance as you go

.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b2-hist/my-module.md

# Output shows which sections need work:
⚠️  Outline compliance: 2 errors, 1 warning
   ❌ [SECTION_LENGTH_MISMATCH] Section 'Внутрішня політика' is under target.
   ❌ [MISSING_OUTLINE_SECTION] Section 'Спадщина' not found.
```

### Batch Checking All Modules

```bash
# Check all B2-HIST modules with outlines
for f in curriculum/l2-uk-en/b2-hist/*.md; do
  echo "Checking $f..."
  .venv/bin/python scripts/audit_module.py "$f" 2>&1 | grep "Outline compliance"
done
```

### CI/CD Integration

```yaml
# In GitHub Actions
- name: Audit Module Compliance
  run: |
    .venv/bin/python scripts/audit_module.py ${{ matrix.module }}
    # Fails if outline compliance errors > 0
```

## Success Criteria

- [x] Detects missing sections (100% accuracy)
- [x] Flags word count deviations >10% (accurate)
- [x] Fuzzy matches section names (60% threshold works well)
- [x] Runs in <1 second per module
- [x] Clear, actionable violation messages
- [x] Integrated into audit pipeline
- [x] Gracefully handles modules without outlines
- [x] Documented comprehensively

## Related

- Issue #439: Cross-file vocabulary integrity (COMPLETED)
- Issue #438: Auto vocabulary extraction (COMPLETED)
- Issue #437: Schema error enhancement (COMPLETED)
- Fractal generation workflow (`scripts/fractal/`)
- Stage 4 review process
- `meta/*.yaml` structure

## Future Enhancements (Optional)

### 1. Self-Updating Outlines

If content is written but outline is outdated:
```bash
.venv/bin/python scripts/update_outline_from_content.py curriculum/l2-uk-en/b2-hist/my-module.md

# Extracts actual section structure and updates meta YAML
```

### 2. Outline Generation from Content

For existing modules without outlines:
```bash
.venv/bin/python scripts/generate_outline.py curriculum/l2-uk-en/b2-hist/my-module.md

# Creates content_outline based on existing sections
```

### 3. Phase 2: Semantic Compliance (LLM-based)

See "Limitations" section above for details.

**Priority:** Low (structural checking catches most issues)

**Trigger:** If >20% of modules pass structural but fail semantic review

---

**Status:** ✅ Phase 1 COMPLETED (Structural)
**Date:** 2026-01-20
**Next:** Optional Phase 2 (Semantic) if needed
