# Vocabulary YAML Workflow

**Purpose:** Standard workflows for creating and maintaining vocabulary YAML files.

## Overview

Vocabulary lives in YAML files at `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml`.

- **Schema:** See `VOCAB_YAML_SCHEMA.md` for format specification
- **Validation:** `scripts/global_vocab_audit.py --level {level}`
- **Enrichment:** `scripts/enrich_yaml_vocab.py` (adds IPA, translations)

---

## Workflow 1: New Module Creation

When building a new module from scratch:

### Step 1: Create Module Content

Write the module markdown with all content sections.

### Step 2: Create Vocabulary YAML

Create `{level}/vocabulary/{slug}.yaml` with skeleton entries:

```yaml
module: 111-module-slug
level: B2
version: '2.0'
items:
  - lemma: слово
    ipa: ''          # Empty - will be enriched
    translation: ''  # Empty - will be enriched
    pos: noun
    gender: m

  - lemma: говорити
    ipa: ''
    translation: ''
    pos: verb
```

**Required fields:**
- `lemma` - Base form of the word
- `pos` - Part of speech (noun, verb, adj, adv, etc.)
- `gender` - Required for nouns (m, f, n, pl)

**Leave empty for enrichment:**
- `ipa` - Will be filled by enrichment script
- `translation` - Will be filled by enrichment script

### Step 3: Run Enrichment

```bash
.venv/bin/python scripts/enrich_yaml_vocab.py curriculum/l2-uk-en/b2/vocabulary/111-module-slug.yaml
```

### Step 4: Validate

```bash
.venv/bin/python scripts/global_vocab_audit.py --level b2
```

---

## Workflow 2: Module Content Updated

When module content is updated with new vocabulary:

### Step 1: Identify New Vocabulary

Run audit to check for vocabulary gaps:

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b2/107-*.md
```

Or manually compare:
- Read updated module content
- Check which Ukrainian words are NOT in the vocabulary YAML
- Focus on new terms introduced in the added content

### Step 2: Add New Entries to YAML

Edit the existing vocabulary YAML file:

```yaml
# Add new entries with empty enrichment fields
  - lemma: нове_слово
    ipa: ''
    translation: ''
    pos: noun
    gender: m
```

### Step 3: Re-run Enrichment

```bash
.venv/bin/python scripts/enrich_yaml_vocab.py curriculum/l2-uk-en/b2/vocabulary/107-*.yaml
```

The enrichment script will:
- Skip entries that already have IPA/translation
- Fill in empty fields for new entries

### Step 4: Validate

```bash
.venv/bin/python scripts/global_vocab_audit.py --level b2
```

---

## Workflow 3: Batch Extraction (Level Migration)

When migrating a level with embedded vocabulary tables:

### For Levels with Vocabulary Tables (A1, A2, B1)

```bash
# Extract vocabulary from markdown tables to YAML
.venv/bin/python scripts/migrate_vocab_to_yaml.py curriculum/l2-uk-en/a1/01-*.md

# Or batch process entire level
.venv/bin/python scripts/migrate_vocab_to_yaml.py --dir curriculum/l2-uk-en/a1/
```

### For Levels Without Tables (B2+)

Vocabulary must be created manually or extracted from content by an agent.

---

## Workflow 4: Quality Review

When reviewing vocabulary for quality issues:

### Step 1: Run Global Audit

```bash
.venv/bin/python scripts/global_vocab_audit.py --level b1
```

### Step 2: Check for Quality Issues

Look for:
- `???` in translations (unknown/uncertain)
- `(typo)` markers in translations
- Surzhyk forms (Russian-Ukrainian mixed)
- Missing IPA or translations

### Step 3: Fix Issues

- **Typos:** Fix lemma and re-enrich
- **Surzhyk:** Replace with standard Ukrainian form
- **Unknown:** Research correct translation or remove

### Step 4: Re-validate

```bash
.venv/bin/python scripts/global_vocab_audit.py --level b1
```

---

## Common Commands Reference

```bash
# Validate single level
.venv/bin/python scripts/global_vocab_audit.py --level b2

# Find unenriched files (empty IPA)
rg -l "ipa: ''" curriculum/l2-uk-en/b2/vocabulary/*.yaml

# Count vocabulary items in a file
yq '.items | length' curriculum/l2-uk-en/b2/vocabulary/107-*.yaml

# Enrich single file
.venv/bin/python scripts/enrich_yaml_vocab.py path/to/file.yaml

# Audit module content vs vocabulary
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b2/107-*.md
```

---

## Agent Responsibilities

When assigned vocabulary work:

1. **Read this document first** before starting
2. **Follow the appropriate workflow** based on task type
3. **Validate before reporting complete** - run global audit
4. **Report issues** if you find quality problems (typos, Surzhyk, ???)
5. **Document blockers** in issue comments if you can't proceed
