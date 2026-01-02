# Claude B2 Migration Context

**Issue:** #349 - B2 YAML Migration & Enrichment
**Parent Epic:** #340 - Rebuild vocabulary database from actual content usage
**Model:** Sonnet (structured, repetitive enrichment work)

## Model Selection

**Task Type:** Vocabulary enrichment (structured, repetitive)
**Recommended Model:** Sonnet
**Reasoning:**
- B2 enrichment is structured data transformation (lemma → IPA + translation)
- ~2,500 vocabulary items across 145 modules
- Predictable patterns, no complex creative writing
- Sonnet provides 95% quality at 20% cost vs Opus
- Cost-effective for high-volume batch processing

**NOT recommended for:**
- Complex module content creation (use Opus)
- Cultural narrative writing (use Opus)
- Domain expertise requiring nuance (use Opus)

## Current Situation

The project is migrating vocabulary from embedded Markdown tables to standalone YAML files. This enables:
- Marking mandatory vs passive vocabulary
- Easier enrichment and validation
- Building vocabulary.db from structured data

### Migration Status

| Level | Extraction | Enrichment | Pipeline |
|-------|------------|------------|----------|
| A1 | ✅ 34/34 | ✅ Complete | ✅ Pass |
| A2 | ✅ 57/57 | ✅ Complete | ✅ Pass |
| B1 | ✅ 86/86 | ✅ Complete | ⚠️ Quality issues |
| **B2** | **✅ 132/132** | **⏳ 10/132 (your task)** | ❌ |

## Your Task: B2 Vocabulary Enrichment

**CRITICAL:** Extraction is already done (132 YAML files). Your task is enrichment only.

### Current Status (as of Jan 2, 2026)

```
✅ M01-M26:   Enriched (done by you - passive voice, syntax, registers, domain vocab)
❌ M27-M106:  NEED ENRICHMENT (80 modules)
✅ M107-M109: Enriched (Agent K)
❌ M110-M111: NEED ENRICHMENT (2 modules)
✅ M112-M131: Enriched (Agent K)
```

**Total modules:** 132
**Fully enriched:** 50 (38%)
**Need enrichment:** 82 (62%)

### Why Two Workflows?

**Old workflow (M01-M111):**
- Module created → Vocabulary extracted to YAML (lemmas only)
- Enrichment done separately (your task)

**New workflow (M112-M131):**
- Module created → Vocabulary YAML includes IPA + translation
- Already enriched at creation time

### Step 1: Verify Current State

```bash
# Total vocabulary files
ls curriculum/l2-uk-en/b2/vocabulary/*.yaml | wc -l
# Expected: 132

# Files still needing enrichment
rg -l "ipa: ''" curriculum/l2-uk-en/b2/vocabulary/*.yaml | wc -l
# Expected: 82
```

### Step 2: Vocabulary Enrichment

For modules M27-M106 and M110-M111, vocabulary YAML files have **empty IPA and translation fields**.

**Resume from M27** (law-justice-vocabulary).

**Check next unenriched module:**
```bash
cat curriculum/l2-uk-en/b2/vocabulary/27-law-justice-vocabulary.yaml
```

You'll see empty fields:
```yaml
items:
  - lemma: адвокат
    ipa: ''           # NEEDS ENRICHMENT
    translation: ''   # NEEDS ENRICHMENT
    pos: noun
    gender: m
```

**Your job:** For each lemma, add IPA and English translation from your knowledge:

```yaml
items:
  - lemma: пасивний
    ipa: /pɐˈsɪwnɪj/
    translation: passive
    pos: adj
    gender: m
```

### Step 3: Validate

```bash
.venv/bin/python scripts/global_vocab_audit.py --level b2
```

All 83 unenriched modules should now pass (no missing IPA/translation).

### Step 4: Test Pipeline

```bash
npm run pipeline l2-uk-en b2
```

Note: Pipeline may fail on pre-existing content issues (not your problem). Focus on vocabulary YAML validation passing.

## Important Rules

1. **Use venv Python:** `.venv/bin/python` not `python3`
2. **No API keys:** Enrich vocabulary manually from your corpus
3. **IPA format:** Use slashes `/.../` and Ukrainian IPA symbols
4. **Keep POS/gender:** Don't change existing pos/gender values

## B2 Content Context

B2 modules cover:
- M01-M10: Passive voice system ✅ Enriched
- M11-M26: Syntax, registers, domain vocab ✅ Enriched
- M27-M30: Domain vocabulary (law, economics) ❌ Need enrichment
- M31-M70: Vocabulary (idioms, synonyms, proverbs) ❌ Need enrichment
- M71-M106: Ukrainian history (Trypillia → 1920s) ❌ Need enrichment
- M107-M109: History (Cossacks, Rozstriliane) ✅ Enriched by Agent K
- M110-M111: History (Holodomor) ❌ Need enrichment
- M112-M131: History (WWII → War 2022) ✅ Enriched by Agent K

All B2 content is **100% immersed Ukrainian** (no English in body text).

## Actual Scope

- **132 modules total** (expanded from original 106 plan)
- **82 modules need enrichment** (M27-M106, M110-M111)
- **50 modules already enriched** (M01-M26, M107-M109, M112-M131)
- **~2,100 vocabulary words remaining** to enrich
- Extraction already complete (done by previous agents)

## Workflow Tips

1. **Skip already-enriched modules:**
   - M01-M26 ✅ Done by you
   - M107-M109, M112-M131 ✅ Done by Agent K
   - Focus on M27-M106 and M110-M111

2. **Batch by module range:**
   - M27-M30 (4 modules - domain vocabulary completion)
   - M31-M70 (40 modules - idioms, synonyms, proverbs)
   - M71-M106 (36 modules - history Trypillia→1920s)
   - M110-M111 (2 modules - Holodomor)

3. **Check progress:**
   ```bash
   # Modules still needing enrichment
   rg -l "ipa: ''" curriculum/l2-uk-en/b2/vocabulary/*.yaml | \
     sed 's/.*vocabulary\///' | sed 's/-.*//' | sort -n
   ```

4. **Commit after each batch** (every 10-20 modules)

## Progress Tracking

Update this checklist as you work:

```
✅ M01-M26:  Enriched (passive voice, syntax, registers, domain vocab)
☐ M27-M30:  Enrichment needed (4 modules - law, economics)
☐ M31-M70:  Enrichment needed (40 modules - idioms, synonyms)
☐ M71-M106: Enrichment needed (36 modules - history)
☐ M110-M111: Enrichment needed (2 modules - Holodomor)
```

**Next up: M27 (law-justice-vocabulary)**

## When Done

1. Run final validation:
   ```bash
   .venv/bin/python scripts/global_vocab_audit.py --level b2
   ```

2. Verify all enriched:
   ```bash
   rg -l "ipa: ''" curriculum/l2-uk-en/b2/vocabulary/*.yaml | wc -l
   # Expected: 0
   ```

3. Comment on issue #349 with results
4. Push changes to main branch

## Questions?

Check the parent docs:
- `docs/dev/VOCAB_YAML_SCHEMA.md` - YAML schema
- `docs/dev/VOCAB_SYSTEM_ARCHITECTURE.md` - Overall architecture
- `CLAUDE.md` - Project instructions
