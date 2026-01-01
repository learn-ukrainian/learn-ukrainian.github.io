# Gemini 2: B1 Migration Context

**Issue:** #350 - B1 YAML Migration & Enrichment
**Parent Epic:** #340 - Rebuild vocabulary database from actual content usage

## Current Agent Assignments

| Agent | Task | Issue |
|-------|------|-------|
| Gemini 1 | A2 enrichment (finishing) | #340 |
| **Gemini 2 (you)** | **B1 migration + enrichment** | **#350** |
| Claude | B2 migration + enrichment | #349 |

## Migration Status

| Level | Extraction | Enrichment | Pipeline |
|-------|------------|------------|----------|
| A1 | ✅ 34/34 | ✅ Complete | ✅ Pass |
| A2 | ✅ 57/57 | ⏳ Gemini 1 working | ❌ |
| **B1** | **✅ 86/86** | **✅ Complete** | ⚠️ Issues |
| B2 | Claude working | Claude working | ❌ |

## Your Task: B1 Migration

### Step 1: Extract Vocabulary to YAML

```bash
.venv/bin/python scripts/migrate_vocab_to_yaml.py curriculum/l2-uk-en/b1/
```

This creates:
- `curriculum/l2-uk-en/b1/vocabulary/*.yaml` (86 files)
- `curriculum/l2-uk-en/b1/meta/*.yaml` (86 files)

### Step 2: Verify Extraction

```bash
ls curriculum/l2-uk-en/b1/vocabulary/*.yaml | wc -l
# Expected: 86
```

### Step 3: Check If Enrichment Needed

```bash
head -30 curriculum/l2-uk-en/b1/vocabulary/01-how-to-talk-about-grammar.yaml
```

If you see empty `ipa: ''` and `translation: ''`, enrichment is required.

### Step 4: Vocabulary Enrichment

For each lemma with empty fields, add:
- `ipa`: Ukrainian IPA (e.g., `/dʲijeˈslɔvɔ/`)
- `translation`: English (e.g., "verb")

**Before:**
```yaml
- lemma: дієслово
  ipa: ''
  translation: ''
  pos: noun
  gender: n
```

**After:**
```yaml
- lemma: дієслово
  ipa: /dʲijeˈslɔvɔ/
  translation: verb
  pos: noun
  gender: n
```

### Step 5: Validate

```bash
.venv/bin/python scripts/global_vocab_audit.py --level b1
```

All 86 modules should pass.

### Step 6: Test Pipeline

```bash
npm run pipeline l2-uk-en b1
```

## B1 Content Structure

| Modules | Content | Immersion |
|---------|---------|-----------|
| M01-M05 | Metalanguage bridge | Transitional |
| M06-M15 | Aspect mastery | 100% Ukrainian |
| M16-M25 | Motion verbs | 100% Ukrainian |
| M26-M41 | Complex sentences | 100% Ukrainian |
| M42-M51 | Advanced grammar | 100% Ukrainian |
| M52-M71 | Vocabulary expansion | 100% Ukrainian |
| M72-M86 | Cultural + integration | 100% Ukrainian |

## Important Rules

1. **Use venv:** `.venv/bin/python` not `python3`
2. **No API keys:** Enrich from your training corpus
3. **IPA format:** Use slashes `/.../`
4. **Preserve existing data:** Don't change pos/gender values

## Workflow Tips

1. **Batch processing:** Do M01-M20, validate, then M21-M40, etc.
2. **Find unenriched files:**
   ```bash
   grep -l "ipa: ''" curriculum/l2-uk-en/b1/vocabulary/*.yaml | wc -l
   ```
3. **Commit after each batch**

## Estimated Scope

- 86 modules
- ~2,000+ vocabulary words
- B1 M01-M05 may have simpler vocabulary (metalanguage terms)
- B1 M06+ has domain-specific vocabulary (aspect, motion, grammar terms)

## When Done

1. Final validation:
   ```bash
   .venv/bin/python scripts/global_vocab_audit.py --level b1
   ```
2. Comment on issue #350
3. Push to main

## Reference Docs

- `docs/dev/VOCAB_YAML_SCHEMA.md` - Schema spec
- `docs/dev/VOCAB_SYSTEM_ARCHITECTURE.md` - Architecture
- `GEMINI.md` - Gemini-specific instructions
