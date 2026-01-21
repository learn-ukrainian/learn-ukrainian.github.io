# /module-vocab-enrich

Enrich vocabulary for an entire track/course after all modules are content-complete.

> **Run this after all modules in the level have been deployed with skeleton vocab.**

## Usage

```
/module-vocab-enrich {level}
```

## Examples

```bash
/module-vocab-enrich b2-hist    # Enrich all B2-HIST modules
/module-vocab-enrich c1-bio     # Enrich all C1-BIO modules
/module-vocab-enrich lit        # Enrich all LIT modules
```

---

## Why Separate Vocab Enrichment?

Vocabulary extraction requires:

1. **Sequential processing** — Module 5 needs to know what was introduced in M1-4
2. **Cumulative deduplication** — Only NEW words go in each module's vocab
3. **Complete course context** — Can't deduplicate against modules that don't exist yet

Running vocab enrichment separately ensures:

- ✅ Correct deduplication across the entire track
- ✅ Parallel content creation (multiple agents building different modules)
- ✅ Single consistent vocabulary pass at the end

---

## Process

### Step 1: Get Module List

```bash
# Get all modules in order from curriculum.yaml
modules=$(yq ".levels.\"${level}\".modules[]" curriculum/l2-uk-en/curriculum.yaml)
```

### Step 2: Process Each Module (In Order)

**CRITICAL:** Modules MUST be processed in order (M1 → M2 → M3 → ... → MN).

For each module:

```
1. Read lesson content: {slug}.md
2. Read activities: activities/{slug}.yaml
3. Load cumulative vocabulary from previous modules
4. Extract NEW vocabulary (not in cumulative set)
5. Generate IPA and translations
6. Write to: vocabulary/{slug}.yaml
7. Update cumulative vocabulary set
8. Regenerate MDX with populated vocabulary table
```

### Step 3: Validate Each Module's Vocabulary

Run vocab-qa checks:

```bash
For each module:
  1. Schema validation (module, level, version, items)
  2. IPA format check (/slashes/, stress markers)
  3. Alphabetical sorting (Ukrainian alphabet)
  4. No duplicates within module
  5. All items appear in lesson or activities
```

### Step 4: Regenerate MDX Files

After vocab enrichment, regenerate all MDX:

```bash
npm run generate l2-uk-en {level}
```

### Step 5: Update Vocabulary Database

```bash
.venv/bin/python scripts/populate_vocab_db.py --level {level}
```

---

## Output

```
VOCAB ENRICHMENT COMPLETE: {level}

Modules processed: {count}
Total vocabulary items: {total}

Per-module breakdown:
  - Module 1: {count} items
  - Module 2: {count} items
  - ...
  - Module N: {count} items

✓ All vocabulary YAMLs enriched
✓ MDX files regenerated
✓ vocabulary.db updated

Next: npm run docs:build && npm run docs:deploy
```

---

## Vocabulary Extraction Rules

### What to Extract

For each module, extract content words that:

- Appear in lesson .md
- Are used in activities
- Are NOT in any previous module's vocabulary

### Word Categories

| Category        | Include                    |
| --------------- | -------------------------- |
| Nouns           | All, with gender           |
| Verbs           | All aspects and forms      |
| Adjectives      | Including comparatives     |
| Adverbs         | Yes                        |
| Proper nouns    | People, places, events     |
| Technical terms | Domain-specific vocabulary |

### Exclusions

| Category           | Exclude                                 |
| ------------------ | --------------------------------------- |
| Particles          | і, a, та, але, чи, не                   |
| Prepositions       | в, на, з, до, від, для, про             |
| Common verbs       | є, був, буде (unless lesson focus)      |
| Question words     | хто, що, де, коли (unless lesson focus) |
| Already introduced | Words from previous modules             |

### Inflected Forms

Include ALL inflected forms that appear in content:

```yaml
# If lesson uses: Шевченко, Шевченка, Шевченком
items:
  - lemma: шевченко
    translation: Shevchenko
  - lemma: шевченка
    translation: Shevchenko (genitive)
  - lemma: шевченком
    translation: Shevchenko (instrumental)
```

---

## Error Handling

### If extraction fails for a module:

```
VOCAB ENRICHMENT PARTIAL: {level}

Completed: M1-M4
Failed: M5 - {reason}
Skipped: M6-MN

Fix M5 and re-run: /module-vocab-enrich {level}
```

### If deduplication detects issues:

```
WARN: Word 'козак' appears in both M3 and M7.
      Keeping in M3 (first occurrence), removing from M7.
```

---

## Quick Reference

```bash
# After all modules content-complete:
/module-vocab-enrich b2-hist

# Verify vocab was enriched:
wc -l curriculum/l2-uk-en/b2-hist/vocabulary/*.yaml

# Regenerate MDX manually if needed:
npm run generate l2-uk-en b2-hist

# Full rebuild:
npm run pipeline l2-uk-en b2-hist
```
