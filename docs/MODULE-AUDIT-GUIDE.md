# Module Audit & Review Guide

This document describes the design, implementation, and usage of the module audit and review system for Curricula Opus.

---

## Overview

The audit system ensures curriculum modules meet quality standards before and after editing. It checks:

- **Structural compliance** - Required sections, activity formats
- **Level requirements** - Activity counts, vocab targets, sentence complexity
- **Content quality** - Engagement boxes, narrative richness, examples
- **Vocabulary consistency** - No duplicates across modules (cascade detection)
- **Immersion balance** - Ukrainian/English percentage per level

---

## Quick Start

### Run the audit

```bash
# Audit all modules
npx ts-node scripts/module-audit.ts l2-uk-en

# Audit specific range
npx ts-node scripts/module-audit.ts l2-uk-en 1-30

# Audit single module
npx ts-node scripts/module-audit.ts l2-uk-en 47

# Generate fix prompts (copy-paste to Claude)
npx ts-node scripts/module-audit.ts l2-uk-en 1-30 --fix
```

### After editing modules

```bash
# Regenerate output
npm run generate l2-uk-en a1 [module_number]      # MDX for Docusaurus
npm run generate:json l2-uk-en a1 [module_number] # JSON for Vibe

# Rebuild vocabulary database
npm run vocab:rebuild
```

---

## Architecture

### Components

| Component | File | Purpose |
|-----------|------|---------|
| **Audit Script** | `scripts/module-audit.ts` | Main audit logic |
| **Vocab Database** | `curriculum/l2-uk-en/vocabulary.db` | SQLite DB for word tracking |
| **Review Prompts** | `docs/l2-uk-en/claude-review-prompt.md` | AI review instructions |
| **Richness Guidelines** | `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` | Quality standards (consolidated) |

### Data Flow

```
Module Markdown → Audit Script → Issues Report
                      ↓
              Vocab DB (duplicate check)
                      ↓
              Fix Prompts (--fix mode)
```

---

## Issue Categories

### Error (Must Fix)

| Category | Description |
|----------|-------------|
| `broken-format` | Invalid markdown syntax (old order format, arrow answers) |
| `broken-activity` | Activities missing answers or tables |
| `vocab-duplicate` | Words already introduced in earlier modules |

### Warning (Should Fix)

| Category | Description |
|----------|-------------|
| `requirements` | Below level requirements (activity count, vocab) |
| `missing-content` | No Vocabulary/Summary section |
| `checkpoint` | Checkpoint module missing character/testimonies |
| `enrichment` | No engagement boxes, low word count |
| `narrative` | Dry narration (mostly tables/lists) |
| `immersion` | Wrong Ukrainian/English balance |
| `content-quality` | Missing examples, grammar tables |

### Info (Consider)

| Category | Description |
|----------|-------------|
| `activity-order` | High-load activities before low-load |
| `complexity` | Sentence complexity mismatch |

---

## Level Requirements

### Activity & Vocabulary

| Level | Modules | Activities | Items/Activity | New Words |
|-------|---------|------------|----------------|-----------|
| A1 | 1-30 | 6 | 10 | 15-20 |
| A2 | 31-60 | 8 | 10 | 20-25 |
| A2+ | 61-80 | 10 | 15 | 35-40 |
| B1 | 81-120 | 12 | 20 | 25-30 |
| B1+ | 121-160 | 12 | 20 | 25-30 |
| B2 | 161-235 | 14 | 20 | 25-30 |
| B2+ | 236-310 | 14 | 20 | 25-30 |
| C1 | 311-400 | 14 | 20 | 30-35 |

### Immersion Levels

| Level | Ukrainian % | English % | Tolerance |
|-------|-------------|-----------|-----------|
| A1 | 30% | 70% | ±10% |
| A2 | 40% | 60% | ±10% |
| A2+ | 50% | 50% | ±10% |
| B1 | 60% | 40% | ±10% |
| B1+ | 70% | 30% | ±10% |
| B2 | 85% | 15% | ±10% |
| B2+ | 90% | 10% | ±10% |
| C1 | 95% | 5% | ±10% |

### Sentence Complexity

| Level | Fill-in Words | Unjumble Words |
|-------|---------------|----------------|
| A1 | 3-5 | 4-6 |
| A2 | 6-8 | 8-10 |
| A2+ | 8-10 | 10-12 |
| B1 | 10-14 | 12-16 |
| B1+ | 10-14 | 12-16 |
| B2 | 12-16 | 14-18 |
| B2+ | 12-16 | 14-18 |
| C1 | 14-18 | 16-20 |

---

## Vocabulary Cascade Rule

### The Problem

When you add a word to an earlier module, it may already exist as "new vocabulary" in a later module. This creates duplicates.

### Example

1. Module 12 introduces "книга" (book)
2. Later, you add "книга" to Module 45's vocabulary
3. **Problem**: Module 45 now incorrectly lists "книга" as new

### The Solution

The audit script detects these cascades automatically:

```bash
📋 VOCAB-DUPLICATE
----------------------------------------------------------------------

  Module 45: At the Library (A2)
    ⚠️ 3 vocab word(s) already introduced in earlier modules - remove from this module's vocab
```

### After Detection

1. Remove the duplicate words from the later module's Vocabulary section
2. Run `npm run vocab:rebuild` to rebuild the database
3. Re-run the audit to verify

---

## Checkpoint Module Requirements

Checkpoint modules (every 10th: 10, 20, 30...) must have:

1. **Named character** with format: `**Name** (age, nationality, city)`
   - Example: `**Ліам** (26, Irish, Dublin)`

2. **Opening narrative** - Journal entry or story
   - Day X, Dear Diary style

3. **Dialogue tables**
   ```markdown
   | Speaker | Ukrainian | English |
   |---------|-----------|---------|
   | Ліам | Добрий день! | Hello! |
   ```

4. **Testimonies** - 3-4 learner quotes with names

5. **Framed activities** - "Help [Character]..." format

---

## Fix Mode

Running with `--fix` generates copy-paste prompts:

```bash
npx ts-node scripts/module-audit.ts l2-uk-en 1-30 --fix
```

Output includes:

1. **Priority-ordered issues** - Errors first, then warnings
2. **Level-specific requirements** - What this level needs
3. **Actionable instructions** - Exactly what to fix
4. **Quality checklist** - Additional review items

### Example Fix Prompt

```
Review and fix module 20 (Checkpoint: First Conversations, A1).

**A1 Requirements:** Activities: 6 min, 10 items each | Vocab: 15-20 | Sentences: 3-6 words

## 🔴 FIX BROKEN FORMATS:
- Quiz question 3 has no correct answer marked [x]

## 🔴 REMOVE DUPLICATE VOCABULARY:
The following words were already introduced in earlier modules:
- привіт (introduced in module 1)
- так (introduced in module 3)

## 🟡 CHECKPOINT REQUIREMENTS:
- Add named character: "Name, age, nationality, city"
- Add 3-4 learner testimonies with names and quotes
```

---

## Workflow

### Standard Review Process

1. **Run audit** on module range
2. **Review errors** - Must fix before commit
3. **Review warnings** - Should fix for quality
4. **Generate fix prompts** if needed
5. **Edit modules** using prompts
6. **Regenerate output** (`npm run generate` for MDX, `npm run generate:json` for Vibe)
7. **Rebuild vocab DB** (`npm run vocab:rebuild`)
8. **Re-run audit** to verify fixes

### After Vocabulary Changes

When adding/removing vocabulary words:

1. Edit the module's `# Vocabulary` section
2. Run `npm run vocab:rebuild` to rebuild database
3. Run audit to check for cascading duplicates
4. Fix any duplicates in later modules
5. Regenerate affected modules

---

## Related Scripts

| Script | Purpose |
|--------|---------|
| `scripts/module-audit.ts` | Main audit script |
| `scripts/generate-mdx.ts` | Generate MDX for Docusaurus |
| `scripts/generate_json.py` | Generate JSON for Vibe app |
| `scripts/vocab-init.ts` | Initialize vocabulary.db |
| `scripts/vocab-scan.ts` | Populate vocabulary.db from modules |
| `scripts/vocab-enrich.ts` | Enrich module vocabulary sections |
| `scripts/vocab-audit.ts` | Audit vocab usage in module content |

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `docs/l2-uk-en/claude-review-prompt.md` | AI review instructions |
| `docs/MARKDOWN-FORMAT.md` | Markdown syntax specification |
| `docs/l2-uk-en/A1-REVIEW-STATUS.md` | A1 modules review status |
| `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` | Quality standards (consolidated) |

---

## Troubleshooting

### "No vocabulary.db found"

Run `npm run vocab:init` to create the database, then `npm run vocab:scan` to populate it.

### Immersion check not working

The immersion check requires at least 100 alphabetic characters in the main content (excluding tables, code blocks, frontmatter).

### Vocab duplicates not detected

Ensure:
1. `vocabulary.db` exists and is up to date (`npm run vocab:rebuild`)
2. The vocab table uses standard format with Ukrainian words in first column

### Fix prompts not showing

Fix prompts only appear when:
1. Using `--fix` flag
2. There are modules with issues (errors or warnings)
