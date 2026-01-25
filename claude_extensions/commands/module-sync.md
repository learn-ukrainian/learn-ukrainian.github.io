# /module-sync

Sync meta.yaml to match existing markdown content.

**Use this when:** Markdown exists and is good, but meta.yaml is outdated or missing proper outline

**Don't use when:** Building a new module from scratch (use `/module` instead)

## Usage

```bash
/module-sync {level} {num}
```

## Examples

```bash
/module-sync b2-hist 1      # Sync meta to existing trypillian-civilization.md
/module-sync b2 45          # Sync meta for existing B2 module 45
/module-sync c1-bio 12      # Sync meta for biography module 12
```

---

## CRITICAL: Markdown is the Source of Truth

**Markdown content is PRESERVED** - it's expensive to regenerate.

**Meta.yaml gets UPDATED** - to match the actual markdown structure.

**Your job:** Extract sections from markdown, update meta.yaml, validate activities.

**Meta is NEVER locked** - it's a living document that reflects reality.

---

## What This Does

1. **Read existing markdown** (source of truth - PRESERVED)
2. **Extract actual sections** and word counts from markdown
3. **Update meta.yaml** content_outline to match reality
4. **Validate activities** against markdown content
5. **Fix/regenerate activities** if violations found
6. **Loop until ALL gates ✅**
7. **Deploy** when clean

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

**If meta doesn't exist:** Create skeleton meta from markdown structure

**If activities don't exist:** Will regenerate in Step 5

### Step 3: Extract Sections from Markdown

```bash
# Read markdown and extract actual H2 sections with word counts
# For each ## Section header:
#   - Record section name
#   - Count words until next section
#   - Build content_outline from reality
```

**Build actual structure:**
- Extract all H2 headers as section names
- Count actual words per section
- Sum for total word count
- Compare with current meta.yaml (if exists)

### Step 4: Update Meta.yaml

```bash
# Update content_outline to match extracted sections
meta_file=curriculum/l2-uk-en/${level}/meta/${slug}.yaml

# Update word_target to actual total
# Update content_outline sections with actual word counts
```

**If meta.yaml doesn't exist:** Create it from markdown structure.

**If meta.yaml exists:** Update `content_outline` and `word_target` to match reality.

### Step 5: Run Audit

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/${level}/${slug}.md
```

**After syncing meta to markdown, outline compliance should pass.**

### Step 6: Analyze Remaining Violations

**After syncing meta, remaining violations are typically:**

**Activity violations:**
- Schema errors → Fix YAML syntax
- Mirroring → Rephrase activities
- Too few items → Add more items

**Content violations (if any):**
- Grammar errors → Fix in markdown
- Missing engagement boxes → Add callouts

### Step 7: Fix Activities

**If activity violations exist:**
- Fix minor issues (≤3) directly
- Regenerate activities if major issues (>3)

### Step 8: Loop Until ALL Gates Pass (BATCH FIX PATTERN)

**CRITICAL:** Use **batch-fix-within-module** pattern (see NON-NEGOTIABLE-RULES.md #8).

**NEVER use iterative fix-audit cycles. Instead:**

```
while true:

  # ========================================
  # 8.1 DIAGNOSE (Comprehensive Read)
  # ========================================

  1. Run audit:
     .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/${level}/${slug}.md

  2. Read review file:
     curriculum/l2-uk-en/${level}/audit/${slug}-review.md

  3. If ALL gates ✅ → break loop, go to Step 9

  4. If violations exist:

     Read ALL component files:
     - curriculum/l2-uk-en/${level}/meta/${slug}.yaml
     - curriculum/l2-uk-en/${level}/${slug}.md (PRESERVED - minimal edits only)
     - curriculum/l2-uk-en/${level}/activities/${slug}.yaml
     - curriculum/l2-uk-en/${level}/vocabulary/${slug}.yaml

     Identify ALL violations across ALL components:

     Meta violations:
       - content_outline mismatch → which sections need sync?
       - word_target mismatch → actual vs target?
       - activity_hints gaps → missing types?

     Lesson violations (minimal edits only):
       - Missing engagement boxes → how many needed?
       - Grammar errors → which lines?
       - Low immersion → where is English?

     Activity violations:
       - Schema errors → which items?
       - Mirroring → which activities copy lesson?
       - Item count below minimum → how many needed?

     Vocab violations:
       - Missing IPA → how many items?
       - Count below target → how many needed?

  # ========================================
  # 8.2 EXECUTE (Fix ALL Issues Atomically)
  # ========================================

  Apply ALL fixes in ONE response:

  Order: meta → vocab → activities → markdown
  (Dependencies flow downstream)

  Meta fixes:
    - Sync content_outline to match markdown sections
    - Update word_target to match actual total
    - Fix activity_hints coverage

  Vocab fixes:
    - Add missing items if needed
    - Run enrichment: .venv/bin/python scripts/vocab_enrich_nlp.py ${vocab_file}

  Activity fixes:
    - Fix YAML schema errors
    - Rephrase mirroring activities
    - Add items to meet minimums
    - Ensure activity_hints coverage

  Lesson fixes (MINIMAL - markdown is source of truth):
    - Add missing engagement boxes
    - Fix grammar errors
    - Reduce English if immersion low
    - DO NOT restructure or rewrite large sections

  # ========================================
  # 8.3 VERIFY (Loop to Re-Audit)
  # ========================================

  Continue loop → Re-audit with all fixes applied

end while
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
- ✅ Meta.yaml reflects markdown reality
- ✅ Activities validated

**Why This Works:**
1. **Efficiency:** One comprehensive read + one atomic fix + one audit = O(3) instead of O(3N)
2. **Coherence:** Meta sync + activity fixes + minimal markdown edits applied together
3. **Consistency:** No intermediate states where components misaligned

### Step 9: Deploy

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
  ✓ Meta: Updated content_outline to match {N} sections
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

## Difference from /module and /module --refresh

| Feature | /module | /module --refresh | /module-sync |
|---------|---------|-------------------|--------------|
| Markdown | Generates new | **Preserves** | **Preserves** |
| Meta | Creates via architect | Regenerates via architect | **Updates from markdown** |
| Approach | Plan → Generate | Plan → Validate | Extract → Sync |
| Activities | Generates new | Regenerates | Validates + fixes |
| Use when | New module | Rehydrate outline properly | Sync meta to reality |

**Key difference:**
- `--refresh`: Uses **architect skill** to create proper hydrated outline (plan-driven)
- `--sync`: **Extracts from markdown** to update meta (reality-driven)

---

## Example Workflow

```bash
# User has module where meta.yaml outline doesn't match markdown reality
$ .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b2-hist/trypillian-civilization.md

❌ AUDIT FAILED
  • Outline compliance: meta has 5 sections, markdown has 7 sections
  • Activity mirroring: 3 violations

# Sync meta to match markdown reality
$ /module-sync b2-hist 1

→ Reading existing markdown...
→ Extracting 7 sections with word counts...
→ Updating meta.yaml content_outline...
→ Running audit... Outline now matches ✅
→ Still 3 activity violations...
→ Fixing activities.yaml...
→ Re-running audit... ✅ ALL GATES PASS
→ Deploying...

MODULE SYNCED: b2-hist/trypillian-civilization ✅
```
