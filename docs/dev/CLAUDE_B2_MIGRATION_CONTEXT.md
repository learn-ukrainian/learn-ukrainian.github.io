# Claude B2 Migration Context

**Issue:** #349 - B2 YAML Migration & Enrichment
**Parent Epic:** #340 - Rebuild vocabulary database from actual content usage

## Current Situation

The project is migrating vocabulary from embedded Markdown tables to standalone YAML files. This enables:
- Marking mandatory vs passive vocabulary
- Easier enrichment and validation
- Building vocabulary.db from structured data

### Migration Status

| Level | Extraction | Enrichment | Pipeline |
|-------|------------|------------|----------|
| A1 | ✅ 34/34 | ✅ Complete | ✅ Pass |
| A2 | ✅ 57/57 | ⏳ 13/57 (Gemini working) | ❌ Blocked |
| B1 | ⏳ Gemini | ⏳ | ❌ |
| **B2** | **Your task** | **Your task** | ❌ |

## Your Task: B2 Migration

### Step 1: Extract Vocabulary to YAML

```bash
.venv/bin/python scripts/migrate_vocab_to_yaml.py curriculum/l2-uk-en/b2/
```

This will:
- Extract frontmatter → `meta/{slug}.yaml`
- Extract vocabulary table → `vocabulary/{slug}.yaml`
- Strip both from the MD file

### Step 2: Verify Extraction

```bash
ls curriculum/l2-uk-en/b2/vocabulary/*.yaml | wc -l
# Expected: 106
```

### Step 3: Vocabulary Enrichment (CRITICAL)

B2 vocabulary tables have **empty IPA and English fields**. You must enrich them.

**Check a sample file:**
```bash
cat curriculum/l2-uk-en/b2/vocabulary/01-passive-voice-system.yaml
```

You'll see:
```yaml
items:
  - lemma: пасивний
    ipa: ''           # NEEDS ENRICHMENT
    translation: ''   # NEEDS ENRICHMENT
    pos: adj
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

### Step 4: Validate

```bash
.venv/bin/python scripts/global_vocab_audit.py --level b2
```

All modules should pass (no missing IPA/translation).

### Step 5: Test Pipeline

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
- M01-M10: Passive voice system
- M11-M30: Syntax, registers, advanced grammar
- M31-M70: Vocabulary (idioms, synonyms, proverbs)
- M71-M106: Ukrainian history (Trypillia to 1920s)

All B2 content is **100% immersed Ukrainian** (no English in body text).

## Estimated Scope

- 106 modules
- ~2,500+ vocabulary words
- Enrichment is the main work (extraction is automated)

## Workflow Tips

1. **Batch by module range:** Do M01-M10, validate, commit. Then M11-M20, etc.
2. **Use grep to find empty fields:**
   ```bash
   grep -l "ipa: ''" curriculum/l2-uk-en/b2/vocabulary/*.yaml | wc -l
   ```
3. **Commit after each batch** to avoid losing work

## When Done

1. Run final validation:
   ```bash
   .venv/bin/python scripts/global_vocab_audit.py --level b2
   ```
2. Comment on issue #349 with results
3. Push changes to main branch

## Questions?

Check the parent docs:
- `docs/dev/VOCAB_YAML_SCHEMA.md` - YAML schema
- `docs/dev/VOCAB_SYSTEM_ARCHITECTURE.md` - Overall architecture
- `CLAUDE.md` - Project instructions
