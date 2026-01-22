# /module-sync

Fix existing module to match its specification (meta.yaml).

**Use this when:** Module already exists but has audit violations

**Don't use when:** Building a new module from scratch (use `/module` instead)

## Usage

```bash
/module-sync {level} {num}
```

## Examples

```bash
/module-sync b2-hist 1      # Fix trypillian-civilization to match meta
/module-sync b2 45          # Fix existing B2 module 45
/module-sync c1-bio 12      # Fix biography module 12
```

---

## CRITICAL: Meta.yaml is the Specification

**Meta.yaml is LOCKED** - it defines what the module should be.

**Markdown is the implementation** - it must conform to meta.yaml.

**Your job:** Fix markdown and activities to match the specification.

**FORBIDDEN:** Editing meta.yaml to match existing markdown (this is mutiny).

**Exception:** If user explicitly says "the meta.yaml is wrong", tell them to:
1. Run `/module-meta {level} {num}` to rebuild meta
2. Then run `/module-sync {level} {num}` to fix content

---

## What This Does

1. **Read meta.yaml** (the specification - LOCKED)
2. **Read existing markdown** and activities
3. **Run audit** and read detailed review file
4. **Fix violations** by editing markdown/activities to match meta
5. **Loop until ALL gates ✅** - no stopping until complete
6. **Deploy** when clean

---

## Instructions

Parse arguments: {level} {num}

**CRITICAL:** Do NOT stop and ask user what to do. Work continuously until ALL audit gates pass.

### Step 1: Resolve Module Slug

**For tracks (b2-hist, c1-bio, c1-hist, lit):**
```bash
slug=$(yq ".levels.\"${level}\".modules[$((num-1))]" curriculum/l2-uk-en/curriculum.yaml)
```

**For core levels:**
```bash
slug=$(ls curriculum/l2-uk-en/${level}/*${num}-*.md 2>/dev/null | head -1 | xargs basename -s .md)
```

### Step 2: Verify Files Exist

Check required files:
```bash
md_file=curriculum/l2-uk-en/${level}/${slug}.md
meta_file=curriculum/l2-uk-en/${level}/meta/${slug}.yaml
act_file=curriculum/l2-uk-en/${level}/activities/${slug}.yaml
```

**If markdown doesn't exist:** ERROR - use `/module` to build from scratch

**If meta doesn't exist:** ERROR - meta.yaml is required (specification), use `/module-meta` first

**If activities don't exist:** Will regenerate in Step 5

### Step 3: Read Specification (Meta.yaml)

```bash
# Load the specification - this is LOCKED, DO NOT EDIT
meta=$(cat curriculum/l2-uk-en/${level}/meta/${slug}.yaml)
```

**Extract requirements from meta.yaml:**
- `content_outline` - Required sections and word count targets
- `vocabulary_hints.required` - Must appear in content
- `grammar` - Grammar points to cover
- `word_target` - Total word count target

**These are NON-NEGOTIABLE targets you must hit.**

### Step 4: Run Audit and Read Review

```bash
# Run audit (creates review file)
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/${level}/${slug}.md

# Read the detailed review for context
cat curriculum/l2-uk-en/${level}/audit/${slug}-review.md
```

**Important:** Always read the `{slug}-review.md` file to see:
- Detailed activity breakdown
- Section-by-section analysis
- Specific violations with line numbers
- Richness scores and metrics

### Step 5: Analyze Violations

**Categorize violations:**

**Outline compliance:**
- Missing sections → Add to markdown
- Section word count under target → Expand content
- Section word count over target → Usually OK (check total)
- **Smart enforcement:** If total word count ≥ target, individual sections can be under 10%

**Activity violations:**
- Schema errors → Fix YAML syntax
- Mirroring → Rephrase activities
- Missing required vocabulary → Regenerate with correct vocab
- Too few items → Add more items

**Content violations:**
- Grammar errors → Fix in markdown
- Naturalness < 8 → Improve flow, vary structures
- Missing engagement boxes → Add callouts
- Vocabulary issues → Fix in markdown

### Step 6: Fix Strategy

**Based on violation count:**

**Minor (≤3 violations):**
- Apply targeted fixes directly to files
- Example: Add missing engagement box, fix typo, rephrase activity

**Major (4-10 violations):**
- Fix activities: Regenerate activities.yaml using `/module-act` instructions
- Fix markdown: Edit specific sections to add content, fix grammar

**Catastrophic (>10 violations OR missing sections):**
- Regenerate markdown sections using meta.yaml content_outline as guide
- Regenerate activities.yaml completely
- **Last resort only:** Tell user meta.yaml needs rebuilding

**CRITICAL: Fix markdown to match meta, NOT the reverse.**

### Step 7: Loop Until ALL Gates Pass

```
while true:
  1. Apply fixes (edit markdown, regenerate activities)
  2. Run audit again
  3. Read review file
  4. Check gates
  5. If ALL ✅ → break
  6. Else → analyze new violations, continue loop
```

**NO STOPPING UNTIL COMPLETE:**
- ❌ Do NOT stop at 80% and report
- ❌ Do NOT ask "should I continue?"
- ❌ Do NOT say "markdown needs manual fixes"
- ✅ Keep iterating until ALL gates ✅
- ✅ If stuck on same issue 3+ times, try different approach
- ✅ Only ask user if truly impossible (external dependency)

**Success criteria:**
- ✅ All audit gates green
- ✅ No violations remain
- ✅ Markdown matches meta.yaml specification
- ✅ Activities validated

### Step 8: Deploy

When audit passes, run integration:

```bash
# Generate skeleton vocab if missing
# Generate/update MDX
# Deploy module
```

---

## Output

**On success (ALL gates ✅):**

```
MODULE SYNCED: {level}/{slug}

Iterations: {N} audit cycles
Fixes applied:
  ✓ Markdown: {description of changes}
  ✓ Activities: {regenerated/fixed}
  ✓ All audit gates ✅

Final metrics:
  - Word count: {actual}/{target} ({percentage}%)
  - Activities: {count} ({types} types)
  - Naturalness: {score}/10
  - Immersion: {percentage}%

Deployed: docusaurus/docs/{level}/module-{num}.mdx
Audit report: curriculum/l2-uk-en/{level}/audit/{slug}-review.md
```

**Note:** There is NO "failure" output - you work until success.

---

## Difference from /module

| Feature | /module | /module-sync |
|---------|---------|--------------|
| Markdown | Generates from meta.yaml | Fixes existing to match meta.yaml |
| Meta | Creates from curriculum plan | Used as specification (NOT edited) |
| Activities | Generates new | Validates + fixes/regenerates |
| Cost | High (full generation) | Medium (editing + regeneration) |
| Use when | New module or total rebuild | Fixing existing module with violations |

---

## Example Workflow

```bash
# User has module with violations
$ .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b2-hist/trypillian-civilization.md

❌ AUDIT FAILED
  • Outline compliance: Section "Розвиток культури" 580 words (target: 680)
  • Activity mirroring: 3 violations

# Fix it with sync (edits content to match meta.yaml specification)
$ /module-sync b2-hist 1

→ Reading meta.yaml specification...
→ Target: 6800 words across 8 sections
→ Running audit, reading review...
→ Found: Section "Розвиток культури" under target by 100 words
→ Expanding section with additional content...
→ Re-running audit... Still 3 activity violations
→ Regenerating activities.yaml...
→ Re-running audit... ✅ ALL GATES PASS
→ Deploying...

MODULE SYNCED: b2-hist/trypillian-civilization ✅
```

---

## If Meta.yaml is Actually Wrong

If user says "the meta.yaml is wrong, not the content":

```
The specification (meta.yaml) appears incorrect for this module.

To fix:
1. Run: /module-meta {level} {num}
   This rebuilds meta.yaml from curriculum plan

2. Then run: /module-sync {level} {num}
   This fixes content to match new specification

I cannot edit meta.yaml during sync - it's the locked specification.
```
