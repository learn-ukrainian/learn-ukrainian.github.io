# Prompt Engineering Summary: a1 M15, M19, M39, M41

**Date:** 2026-03-06
**Ref:** #731

## Module Results

| # | Slug | Health | Validate Attempts | Friction | Top Fix |
|---|------|--------|-------------------|----------|---------|
| 15 | the-living-verb-i | NEEDS_WORK | 6 | 2 | Explicit Summary H1 heading rule |
| 19 | likes-and-preferences | NEEDS_WORK | 6 | 2 | Explicit Summary H1 heading rule |
| 39 | food-vocabulary | NEEDS_WORK | 7 | 2 | Add imperative examples to constraint |
| 41 | at-the-cafe | NEEDS_WORK | 7 | 2 | Auto-fix heading levels in pipeline |

**All 4 modules: NEEDS_WORK.** Total of 26 validate attempts across 4 modules (6.5 avg). All modules exhausted fix budget.

## Pattern Frequency

| Pattern | Occurrences | Modules Affected | Priority |
|---------|-------------|------------------|----------|
| Heading level `## Summary` vs `# Summary` | 4/4 | M15, M19, M39, M41 | **CRITICAL** |
| Imperative ban lacks explicit examples | 3/4 | M15, M39, M41 | **HIGH** |
| Meta outline `title:` vs `section:` key mismatch | 2/4 | M39, M41 | **HIGH** |
| Empty/duplicate fix prompts wasting passes | 1/4 | M19 | MEDIUM |
| Expand triggered on over-target content | 1/4 | M39 | MEDIUM |
| Dative exception not stated in constraints | 1/4 | M19 | MEDIUM |
| Low Ukrainian immersion (8% vs 15% target) | 1/4 | M15 | LOW |

## Top Template Fixes (by leverage)

### Fix 1: Heading Level — deterministic pipeline fix (Priority: CRITICAL)

**Affects:** 4/4 modules (likely ALL A1 builds)
**Problem:** Content prompt output format uses `##` for section headers, which makes Gemini output `## Підсумок` instead of `# Підсумок`. The `SECTION_FIX` format also uses `## {title}` as delimiter, structurally preventing Gemini from outputting `# Summary` even when told to fix it. This consumed **all 24 fix attempts** across 4 modules on a trivially fixable formatting issue.
**Root cause type:** template_gap + schema_mismatch
**Fix:** Add a deterministic regex post-processing step in the pipeline that promotes Summary/Підсумок headings to H1. This should NOT be an LLM task.

**Target file:** `scripts/pipeline_lib.py` or `scripts/pipeline_v5.py` (post-processing step)
```python
# After receiving content from Gemini, before validation:
import re
content = re.sub(r'^##\s+(Підсумок|Summary)\b', r'# \1', content, flags=re.MULTILINE)
```

### Fix 2: Imperative ban — add explicit banned forms list (Priority: HIGH)

**Affects:** 3/4 modules (all pre-verb A1 modules, likely M1-M14 too)
**Problem:** Constraint says "imperatives are banned" but doesn't list which Ukrainian words are imperatives. Gemini repeatedly generates `Запам'ятайте`, `Уявіть`, `Порівняйте`, `Зверніть увагу`, `Спробуйте` without recognizing them as imperative forms.
**Root cause type:** template_gap
**Fix:** Add explicit banned imperative forms to `PEDAGOGICAL_CONSTRAINTS` entries.

**Target file:** `scripts/pipeline_lib.py` (PEDAGOGICAL_CONSTRAINTS)
```python
# Add to relevant constraint entries:
"Banned imperative forms (non-exhaustive): Запам'ятайте, Уявіть, Порівняйте, "
"Зверніть увагу, Спробуйте, Подивіться, Послухайте, Прочитайте, Повторіть, "
"Напишіть, Скажіть, Дайте. Use English instructions instead: 'Try to...', "
"'Notice that...', 'Compare...'."
```

### Fix 3: Meta outline `title:` vs `section:` key — schema alignment (Priority: HIGH)

**Affects:** 2/4 modules (likely all modules using research → content pipeline)
**Problem:** Research prompt template outputs `title:` key in outline YAML, but `outline_compliance.py:298` expects `section:` key. Caused `KeyError` crash in M39 that burned the entire escalation pass.
**Root cause type:** schema_mismatch
**Fix:** Either update the research template to output `section:` or update `outline_compliance.py` to accept both keys.

**Target file:** `scripts/audit/outline_compliance.py` or research phase template
```python
# In outline_compliance.py, accept both keys:
section_name = item.get('section') or item.get('title', '')
```

### Fix 4: Empty fix prompt deduplication (Priority: MEDIUM)

**Affects:** 1/4 modules (M19), but likely a systemic issue
**Problem:** When `_extract_pedagogy_violations()` returns no violations, the pipeline still sends an empty/near-empty fix prompt, wasting API budget. Already partially addressed by SHA-256 deduplication added earlier.
**Fix:** Skip fix attempt entirely when extracted violations are empty.

### Fix 5: Expand logic direction check (Priority: MEDIUM)

**Affects:** 1/4 modules (M39 — 3526 words vs 1200 target)
**Problem:** Pipeline triggered expand phase with negative delta (-2326 words). Content was already 3x over target but expand was still triggered.
**Fix:** Guard expand phase: skip if current word count >= target.

### Fix 6: Dative exception for M19 (Priority: MEDIUM)

**Affects:** 1/4 modules (M19)
**Problem:** `likes-and-preferences` module requires dative forms (`мені`, `тобі`) but the A1-level constraint bans dative entirely. The plan update (v2.1) added a `scope_note` but the pipeline constraint was also updated separately.
**Status:** Already fixed in earlier session — `LEVEL_CONSTRAINTS["a1"]` now has M19 dative exception.

## Template Health Score

- Content prompt: **4/10** — heading level contradiction wastes all fix budget
- Activities prompt: **6/10** — schema examples present but Russicism list incomplete
- Validation prompt: **5/10** — fix prompts sometimes empty or duplicate
- Fix prompts: **3/10** — SECTION_FIX format structurally prevents heading fixes; imperative whack-a-mole burns passes

## Recommendations

1. **Fix 1 (heading levels)** is the highest-leverage change — it would have saved ~24 API calls across just these 4 modules. Implement as deterministic post-processing, not LLM instruction.
2. **Fix 2 (imperative list)** is the second-highest — would prevent 3-pass fix loops in pre-verb modules.
3. **Fix 3 (title/section key)** prevents hard crashes that waste the entire escalation budget.
4. Fixes 4-6 are important but lower priority.

## Modules Needing Rebuild

All 4 modules need rebuilding after template fixes are applied — none passed validation cleanly.

| # | Slug | Reason |
|---|------|--------|
| 15 | the-living-verb-i | Exhausted fix budget (heading + imperatives) |
| 19 | likes-and-preferences | Exhausted fix budget (heading + empty fixes) |
| 39 | food-vocabulary | Exhausted fix budget + escalation crash |
| 41 | at-the-cafe | Exhausted fix budget (heading + imperatives) |
