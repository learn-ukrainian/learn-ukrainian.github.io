# /module-fix

Check and fix a complete module until all audit gates pass.

> **🤝 COLLABORATION RULE:** Fix issues yourself. Ask the other agent for help (research, facts, validation) when stuck. Never guess or hallucinate - collaboration is faster than guessing wrong.

## Usage

```bash
/module-fix {level} {module_num}
```

## What This Does

Orchestrates all QA checks and fixes issues in a loop until COMPLETE:

1. **Run comprehensive audit** → identifies all violations
2. **Categorize violations** → meta, lesson, activities, vocab
3. **Fix by category** → using existing QA prompts
4. **Loop until ALL gates ✅**

> **📖 IMPORTANT: Read before fixing word count issues**
>
> Section word targets are FLEXIBLE guidance, not hard limits.
> See: `docs/SUBSECTION-FLEXIBILITY-GUIDE.md`
>
> **Quick rule:** If total ≥ word_target, you can redistribute words between sections.
> Don't blindly expand every under-target section - look for over-target sections first!

---

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Resolve Module Path

**For core levels (a1, a2, b1, b2, c1, c2):**
```bash
slug=$(ls curriculum/l2-uk-en/${level}/${num}-*.md 2>/dev/null | head -1 | xargs basename -s .md)
```

**For tracks (b2-hist, c1-bio, c1-hist, lit):**
```bash
slug=$(yq ".levels.\"${level}\".modules[$((num-1))]" curriculum/l2-uk-en/curriculum.yaml)
```

**Set file paths:**
```
md_file=curriculum/l2-uk-en/${level}/${slug}.md
plan_file=curriculum/l2-uk-en/plans/${level}/${slug}.yaml   # IMMUTABLE - source of truth
meta_file=curriculum/l2-uk-en/${level}/meta/${slug}.yaml    # MUTABLE - build config
act_file=curriculum/l2-uk-en/${level}/activities/${slug}.yaml
vocab_file=curriculum/l2-uk-en/${level}/vocabulary/${slug}.yaml
status_file=curriculum/l2-uk-en/${level}/status/${slug}.json # AUTO-GENERATED - audit cache
```

> **Architecture Note (v2.0):**
> - **Plan** (`plans/`): Immutable source of truth - content_outline, word_target, objectives
> - **Meta** (`meta/`): Mutable build config - naturalness, version, build timestamps
> - **Status** (`status/`): Auto-generated audit cache - gates, violations, last_audit

### Step 2: Run Initial Audit

> **📋 QUICK REFERENCES (read BEFORE fixing activities):**
> - Activity schemas: `claude_extensions/quick-ref/ACTIVITY-SCHEMAS.md`
> - Activity YAML reference: `docs/ACTIVITY-YAML-REFERENCE.md`

**First, run fast schema validation on activities:**

```bash
.venv/bin/python scripts/validate_activities_schema.py ${act_file}
```

If schema errors exist, fix those first (see quick-ref for exact field names).

**Then run full audit:**

```bash
.venv/bin/python scripts/audit_module.py ${md_file} --fix
```

The `--fix` flag auto-fixes common YAML schema issues.

Read the audit review file:
```
curriculum/l2-uk-en/${level}/audit/${slug}-review.md
```

### Step 3: Categorize Violations

Group violations by component:

| Category | Violations | Fix With |
|----------|-----------|----------|
| **Meta** | MISSING_META_YAML, INVALID_META_YAML, INVALID_ACTIVITY_TYPE, word target mismatch | Fix meta.yaml directly |
| **Lesson** | OUTLINE_MISMATCH, word count, engagement boxes, immersion | Fix markdown directly |
| **Activities** | Schema errors, item counts, mirroring, activity_hints coverage | Fix activities.yaml or regenerate |
| **Vocab** | Missing IPA, wrong POS, duplicates | Fix vocabulary.yaml |
| **Naturalness** | Score < 8, robotic text, template repetition | Fix affected content |

### Step 4: Smart Batching Fix Loop

**CRITICAL:** Use **threshold-based smart batching** for optimal efficiency + debuggability.

```
while violations_exist:

    # ========================================
    # 4.1 DIAGNOSE (Read All Files Once)
    # ========================================

    Read all 4 components:
    - ${meta_file}     (meta.yaml)
    - ${md_file}       (markdown)
    - ${act_file}      (activities.yaml)
    - ${vocab_file}    (vocabulary.yaml)

    Read audit review file:
    - curriculum/l2-uk-en/${level}/audit/${slug}-review.md

    Count and categorize ALL violations:

    Meta violations (M):
      - INVALID_ACTIVITY_TYPE → which types are invalid?
      - Word target mismatch → actual vs target?
      - Activity_hints coverage → missing types?

    Vocab violations (V):
      - Missing IPA → how many items?
      - Wrong POS → which entries?
      - Duplicates → which words?
      - Count below target → how many needed?

    Activity violations (A):
      - Schema errors → which items malformed?
      - Item count below minimum → how many needed?
      - Mirroring issues → which activities copy lesson?
      - Missing activity_hints coverage → which types not represented?

    Lesson violations (L):
      - Word count shortfall → which sections under target?
      - Missing engagement boxes → how many needed?
      - Low immersion → where is English text?
      - OUTLINE_MISMATCH → which sections missing?

    Naturalness violations (N) - AGENT EVALUATED:
      - If meta.yaml has naturalness.status = PENDING or FAIL → YOU must evaluate
      - Score < 8 → which sections flagged?
      - Red flags → template repetition? robotic transitions?
      - NOTE: The audit script only checks if a score exists; YOU provide the evaluation

    TOTAL_VIOLATIONS = M + V + A + L + N

    # ========================================
    # 4.2 CHOOSE STRATEGY (Threshold-Based)
    # ========================================

    if TOTAL_VIOLATIONS == 0:
        break  # Done!

    if TOTAL_VIOLATIONS <= 5:
        # STRATEGY: Fix all at once (small enough to track)
        execute_batch_fix_all()
        audit_once()

    elif TOTAL_VIOLATIONS <= 15:
        # STRATEGY: Fix by component (respects dependencies)
        execute_component_rounds()
        # Round 1: Meta (if M > 0)
        # Round 2: Vocab (if V > 0)
        # Round 3: Activities (if A > 0)
        # Round 4: Lesson + Naturalness (if L > 0 or N > 0)

    else:  # TOTAL_VIOLATIONS > 15
        # STRATEGY: Fix by severity (get unblocked fast)
        execute_severity_rounds()
        # Round 1: BLOCKING (schema errors, missing sections)
        # Round 2: MAJOR (word count, required vocab, structural)
        # Round 3: MINOR (engagement boxes, examples, polish)

    # ========================================
    # 4.3 EXECUTION DETAILS
    # ========================================

end while
```

### Strategy 1: Batch Fix All (≤5 violations)

**Use when:** Total violations ≤ 5

**Process:**
```
Apply ALL fixes in ONE response:

Order: meta → vocab → activities → lesson → naturalness
(Dependencies flow downstream)

# Meta fixes
if M > 0:
    Read: claude_extensions/phases/module-meta-qa.md
    Fix meta.yaml:
      - Replace invalid activity types with valid ones
      - Update word_target if legitimately wrong (rare)
      - Ensure activity_hints covers all activity types

# Vocab fixes
if V > 0:
    Read: claude_extensions/phases/module-vocab-qa.md
    Fix vocabulary.yaml:
      - Add missing vocabulary items
      - Fix POS tags
      - Remove duplicates
    Run: .venv/bin/python scripts/vocab_enrich_nlp.py ${vocab_file}

# Activity fixes
if A > 0:
    Read: claude_extensions/quick-ref/ACTIVITY-SCHEMAS.md  # Field requirements
    Read: claude_extensions/phases/module-act-qa.md
    Validate: .venv/bin/python scripts/validate_activities_schema.py ${act_file}
    Fix activities.yaml:
      - Fix schema errors (correct→not answer, criteria→not criterion)
      - Add missing items
      - Rephrase mirroring activities

# Lesson fixes
if L > 0:
    Read: claude_extensions/phases/module-lesson-qa.md
    Fix markdown:
      - Expand under-length sections
      - Add missing engagement boxes
      - Increase immersion
      - Add missing sections

# Naturalness fixes
if N > 0:
    Fix affected prose:
      - Vary sentence structures
      - Add discourse markers
      - Remove template repetition

Audit once: .venv/bin/python scripts/audit_module.py ${md_file}
```

**Why:** Small violation count = manageable in one pass, maximum efficiency.

---

### Strategy 2: Component Rounds (6-15 violations)

**Use when:** Total violations 6-15

**Process:**
```
Round 1: FIX META (if M > 0)
  Read: claude_extensions/phases/module-meta-qa.md
  Fix meta.yaml:
    - Replace invalid activity types
    - Update activity_hints coverage
    - Adjust word_target if needed
  Audit: .venv/bin/python scripts/audit_module.py ${md_file}
  Check: Meta violations cleared? ✅

Round 2: FIX VOCAB (if V > 0)
  Read: claude_extensions/phases/module-vocab-qa.md
  Fix vocabulary.yaml:
    - Add missing vocabulary items
    - Fix POS tags
    - Remove duplicates
  Run: .venv/bin/python scripts/vocab_enrich_nlp.py ${vocab_file}
  Audit: .venv/bin/python scripts/audit_module.py ${md_file}
  Check: Vocab violations cleared? ✅

Round 3: FIX ACTIVITIES (if A > 0)
  Read: claude_extensions/phases/module-act-qa.md
  Fix activities.yaml:
    - Fix ALL schema errors
    - Add missing items to reach minimums
    - Rephrase mirroring activities
    - Ensure activity_hints coverage
  Audit: .venv/bin/python scripts/audit_module.py ${md_file}
  Check: Activity violations cleared? ✅

Round 4: FIX LESSON + NATURALNESS (if L > 0 or N > 0)
  Read: claude_extensions/phases/module-lesson-qa.md
  Fix markdown:
    - Expand sections below word count targets
    - Add missing engagement boxes
    - Increase immersion (reduce English)
    - Add missing sections from content_outline
    - Fix naturalness (vary structures, add discourse markers)
  Audit: .venv/bin/python scripts/audit_module.py ${md_file}
  Check: Lesson + naturalness violations cleared? ✅
```

**Why:**
- Respects dependency chain (meta → vocab → activities → lesson)
- Each component audited independently
- Easier to debug which fix caused new issues
- Medium violation count = needs organization but not overwhelming

**Typical rounds:** 2-4 audits (vs 6-15 if done one-by-one)

---

### Strategy 3: Severity Rounds (>15 violations)

**Use when:** Total violations > 15

**Process:**
```
Round 1: FIX BLOCKING ISSUES
  Identify BLOCKING violations:
    - Schema errors (activities can't parse)
    - Missing required sections (outline mismatch)
    - Invalid YAML syntax
    - Missing meta.yaml

  Fix ALL blocking issues across ALL components:
    - Fix schema errors in activities.yaml
    - Add missing sections to markdown
    - Fix YAML syntax in meta/vocab/activities

  Audit: .venv/bin/python scripts/audit_module.py ${md_file}
  Check: All BLOCKING cleared? ✅

Round 2: FIX MAJOR ISSUES
  Identify MAJOR violations:
    - Word count < 90% of target
    - Required vocabulary missing
    - Structural issues (wrong pedagogy)
    - Activity count below minimums
    - Naturalness score < 7

  Fix ALL major issues:
    - Expand sections to hit word targets
    - Add required vocabulary to content
    - Fix structural mismatches
    - Add activities to reach minimums
    - Improve naturalness in flagged sections

  Audit: .venv/bin/python scripts/audit_module.py ${md_file}
  Check: All MAJOR cleared? ✅

Round 3: FIX MINOR ISSUES
  Identify MINOR violations:
    - Missing engagement boxes
    - Low example count
    - Immersion < 98%
    - Naturalness score 7-7.9

  Fix ALL minor issues:
    - Add engagement boxes
    - Add example sentences
    - Translate English to Ukrainian
    - Polish naturalness

  Audit: .venv/bin/python scripts/audit_module.py ${md_file}
  Check: All MINOR cleared? ✅
```

**Why:**
- Get unblocked fast (blocking → major → minor)
- Group similar fixes together
- High violation count = likely structural issues
- Avoid fixing polish items before structure is solid

**Typical rounds:** 3 audits (vs >15 if done one-by-one)

---

### Step 5: Benefits of Smart Batching

| Aspect | Pure Batch (old) | Smart Batching (new) | One-by-One |
|--------|------------------|----------------------|------------|
| **Speed** | 1 audit | 2-4 audits | N audits |
| **Debuggability** | Hard | Easy | Easy |
| **Context load** | High | Medium | Low |
| **Risk of regression** | High | Low | Very low |
| **Dependency handling** | Manual | Automatic | Manual |
| **Best for violations** | ≤5 | 6-15 | N/A |

### Step 6: Validation Complete + MDX Generation

When ALL audit gates show ✅:

**MANDATORY: Generate MDX file for the website:**

```bash
# Generate MDX (REQUIRED - must run after audit passes)
.venv/bin/python scripts/generate_mdx.py l2-uk-en ${level} ${module_num}
```

This generates: `docusaurus/docs/${level}/${slug}.mdx`

**Verify the MDX was created:**
```bash
ls -la docusaurus/docs/${level}/${slug}.mdx
```

---

## Quick Reference: Common Fixes

### Meta Fixes
```yaml
# Invalid activity type → replace with valid
activity_hints:
  - type: fill-in  # NOT transform, conjugation, etc.

# Word target mismatch → update to match content
word_target: 3500  # Must match actual section sums ±10%
```

**IMPORTANT: Section word counts are flexible guidance**
- Total word count MUST be ≥ word_target
- Individual sections: ±10% tolerance
- You can redistribute words between sections
- Example: Section over by 600? Move content to sections under target

### Lesson Fixes
```markdown
# CRITICAL: No frontmatter in .md files (metadata lives in meta.yaml)
# File should START with <!-- SCOPE or # Title

# Missing SCOPE comment → add at start
<!-- SCOPE
Covers: ...
Not covered: ...
Related: ...
-->

# Missing engagement box → add callout
> 💡 **Чому це важливо?**
> Explanation here...

# Low word count → expand sections OR redistribute from over-sections
# Low immersion → reduce English, increase Ukrainian
```

**For section word count issues, see:** `docs/SUBSECTION-FLEXIBILITY-GUIDE.md`

### Activity Fixes
```yaml
# Schema error: missing options
- sentence: Text with [___] blank.
  answer: correct
  options: [correct, wrong1, wrong2, wrong3]  # Must be 4

# Too few items → add more
# Mirroring → rephrase to differ from lesson text
```

### Naturalness Fixes (Agent Evaluated)

> **🤖 Your responsibility:** Evaluate naturalness yourself, then update meta.yaml:
> ```yaml
> naturalness:
>   score: 9
>   status: PASS
> ```

- Template repetition → vary sentence structures
- Robotic transitions → simplify, use natural connectors
- Excessive intensifiers → remove 50% of "дуже", etc.
- Missing discourse markers → add потім, тому, але, тоді, також
- Disconnected sentences → improve thematic coherence

**Evaluation reference:** See `scripts/audit/ukrainian_naturalness_checker_prompt.md` for scoring criteria.

---

## Output

**On COMPLETE (after MDX generation):**

```
MODULE FIX: COMPLETE ✅

Level: {level}
Module: {module_num} ({slug})
Iterations: {N} audit cycles

Fixes applied:
  ✓ Meta: {description of fixes}
  ✓ Lesson: {description of fixes}
  ✓ Activities: {description of fixes}
  ✓ Vocab: {description of fixes}
  ✓ Naturalness: {score}/10

Final metrics:
  - Word count: {actual}/{target} ({percentage}%)
  - Activities: {count} ({types} types)
  - Immersion: {percentage}%

MDX Generated: ✅ docusaurus/docs/{level}/{slug}.mdx

MODULE APPROVED
```

**CRITICAL:** The MDX generation step is MANDATORY. Do not output "MODULE APPROVED" until you have:
1. Run the MDX generation command
2. Verified the MDX file exists

**THERE IS NO FAILURE OUTPUT.**

Keep iterating until complete. If truly stuck after 5+ attempts on same issue:
- Try different approach
- Check if issue is in documentation/tooling
- Only then ask user for guidance

---

## Related Commands

| Command | Purpose |
|---------|---------|
| `/module-meta-qa` | Validate meta.yaml only |
| `/module-lesson-qa` | Validate lesson only |
| `/module-act-qa` | Validate activities only |
| `/module-vocab-qa` | Validate vocabulary only |
| `/meta-fix` | Fix invalid activity types in meta |
| `/module-sync` | Sync meta to existing markdown |
| `/module-stage-4` | Full Stage 4 review (same as this) |
