# /module-fix

Check and fix a complete module until all audit gates pass.

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
meta_file=curriculum/l2-uk-en/${level}/meta/${slug}.yaml
act_file=curriculum/l2-uk-en/${level}/activities/${slug}.yaml
vocab_file=curriculum/l2-uk-en/${level}/vocabulary/${slug}.yaml
```

### Step 2: Run Initial Audit

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

### Step 4: Batch Fix Loop (OPTIMIZED)

**CRITICAL:** Use **batch-fix-within-module** pattern (see NON-NEGOTIABLE-RULES.md #8).

**NEVER use iterative fix-audit cycles. Instead:**

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

    Identify ALL violations across ALL components:

    Meta violations:
      - INVALID_ACTIVITY_TYPE → which types are invalid?
      - Word target mismatch → actual vs target?
      - Activity_hints coverage → missing types?

    Lesson violations:
      - Word count shortfall → which sections under target?
      - Missing engagement boxes → how many needed?
      - Low immersion → where is English text?
      - OUTLINE_MISMATCH → which sections missing?

    Activity violations:
      - Schema errors → which items malformed?
      - Item count below minimum → how many needed?
      - Mirroring issues → which activities copy lesson?
      - Missing activity_hints coverage → which types not represented?

    Vocab violations:
      - Missing IPA → how many items?
      - Wrong POS → which entries?
      - Duplicates → which words?
      - Count below target → how many needed?

    Naturalness violations:
      - Score < 8 → which sections flagged?
      - Red flags → template repetition? robotic transitions?

    # ========================================
    # 4.2 EXECUTE (Fix ALL Issues Atomically)
    # ========================================

    Apply ALL fixes in ONE response:

    Order: meta → vocab → activities → markdown
    (Dependencies flow downstream)

    # Meta fixes (if needed)
    if meta_violations:
        Read: claude_extensions/phases/module-meta-qa.md
        Fix meta.yaml:
          - Replace invalid activity types with valid ones
          - Update word_target if legitimately wrong (rare)
          - Ensure activity_hints covers all activity types

    # Vocab fixes (if needed)
    if vocab_violations:
        Read: claude_extensions/phases/module-vocab-qa.md
        Fix vocabulary.yaml:
          - Add missing vocabulary items
          - Fix POS tags
          - Remove duplicates

        If missing IPA/POS data:
          .venv/bin/python scripts/vocab_enrich_nlp.py ${vocab_file}

    # Activity fixes (if needed)
    if activity_violations:
        if violations <= 3:
            Fix individually in activities.yaml:
              - Fix schema errors
              - Add missing items
              - Rephrase mirroring activities
        else:
            Read: claude_extensions/phases/module-act-qa.md
            Rebuild activities section with:
              - Correct schemas
              - Sufficient item counts
              - Coverage of all activity_hints types
              - No mirroring of lesson text

    # Lesson fixes (if needed)
    if lesson_violations:
        Read: claude_extensions/phases/module-lesson-qa.md
        Fix markdown:
          - Expand under-length sections to hit targets
          - Add missing engagement boxes
          - Increase immersion (reduce English)
          - Add missing sections from content_outline
          - Fix naturalness (vary structures, add discourse markers)

    # Naturalness fixes (if needed)
    if naturalness_score < 8:
        Fix affected prose in lesson/activities:
          - Remove template repetition
          - Add discourse markers
          - Simplify robotic transitions
          - Reduce excessive intensifiers

    # ========================================
    # 4.3 VERIFY (ONE Final Audit)
    # ========================================

    .venv/bin/python scripts/audit_module.py ${md_file}

    Read audit review:
    curriculum/l2-uk-en/${level}/audit/${slug}-review.md

    # Check if all gates pass
    if all_gates_pass:
        break

    # If still violations, repeat cycle
    # (Should be rare with comprehensive batch fix)

end while
```

**Why This Works:**

1. **Efficiency:** One read + one fix + one audit = O(3) instead of O(3N)
2. **Coherence:** Fixes can reference each other (e.g., new vocab drives section expansion)
3. **Consistency:** Avoids intermediate states where vocab exists but isn't used in content
4. **Speed:** Fewer API calls, less token usage

### Step 5: Decision Matrix

| Violations | Action |
|-----------|--------|
| ≤3 total | Fix individually |
| >3 in one component | Rebuild that component |
| >10 OR structural | Consider full rebuild |

### Step 6: Validation Complete

When ALL audit gates show ✅:

```bash
# Run full pipeline
npm run pipeline l2-uk-en ${level} ${module_num}
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

### Naturalness Fixes
- Template repetition → vary sentence structures
- Robotic transitions → simplify, use natural connectors
- Excessive intensifiers → remove 50% of "дуже", etc.

---

## Output

**On COMPLETE:**

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

Pipeline: PASS
MDX: docusaurus/docs/{level}/{slug}.mdx

MODULE APPROVED
```

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
