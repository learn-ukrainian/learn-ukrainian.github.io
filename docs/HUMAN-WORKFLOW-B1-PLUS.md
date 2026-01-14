# B1+ Module Workflow - Human User Guide

**This guide is for YOU (the human user). It shows exactly what commands YOU run.**

The AI agent follows `docs/B1-PLUS-MODULE-WORKFLOW.md`. This guide is your companion - what to execute at each step.

---

## Quick Overview

```
YOU tell agent → Agent creates content → Agent validates → YOU review results → YOU generate output
```

---

## Complete Workflow (What YOU Do)

### Phase 1: Setup (One-Time)

```bash
# Ensure virtual environment is activated (or use .venv/bin/python)
source .venv/bin/activate
```

**Note:** Grammar and content validation require LLM API access. Run validation commands inside agents (Claude Code, Gemini CLI, Antigravity) where API keys are already configured.

---

### Phase 2: Module Creation (AI Does This)

**YOU tell Claude:** "Create module 50 for B1"

**Claude executes these commands** (you don't run them):
- `/module-stage-1 b1 50` - Skeleton
- `/module-stage-2 b1 50` - Content
- `/module-stage-3 b1 50` - Activities
- `/module-stage-4 b1 50` - Review/fix

**OR you can run them manually one by one** if you want to review each stage.

---

### Phase 3: Validation (Tell Agent to Run)

After AI creates the module, tell agent to validate it:

#### Required: Audit (MUST PASS)

```bash
# Tell agent to run:
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md
```

**Look for:**
- ✅ `Overall Status: PASS` - Good! Continue to next step
- ❌ `Overall Status: FAIL` - Tell agent to fix violations, then run audit again

#### Optional: Grammar Validation (Recommended for B1+)

```bash
# Tell agent to run:
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md --validate-grammar
```

**Look for:**
- Violations in terminal output
- If violations found: Tell agent "Fix grammar violations: [paste violations]"

#### Optional: Content Quality Review (Before Release)

```bash
# Tell agent to run:
AUDIT_CONTENT_QUALITY=true .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md
```

**Look for:**
- Score in terminal (0-10)
- If score <7: Tell Claude to improve low-scoring sections

#### Optional: Activity Quality (High-Stakes Content)

```bash
# Step 1: Generate quality queue
npm run quality:generate l2-uk-en b1 50

# Step 2: YOU manually fill in the YAML file
# Open: curriculum/l2-uk-en/b1/audit/50-{slug}-quality-queue.yaml
# Fill in: manual_naturalness, manual_difficulty, manual_engagement, manual_distractor_quality

# Step 3: Finalize quality report
npm run quality:finalize l2-uk-en b1 50
```

**Look for:**
- `Result: PASS` in report
- If `Result: FAIL`: Tell Claude to improve low-scoring activities

---

### Phase 4: Fix Loop (If Needed)

**If audit FAIL:**

1. Copy violations from terminal
2. Tell Claude: "Fix these audit violations: [paste violations]"
3. Wait for Claude to fix
4. Run audit again: `.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md`
5. Repeat until PASS

---

### Phase 5: Generate Output (YOU Run These)

Once audit PASS, generate final output:

```bash
# Full pipeline: lint → generate MDX → validate MDX → validate HTML
npm run pipeline l2-uk-en b1 50
```

**Note:** JSON generation (`npm run generate:json`) is disabled - Vibe app project on hold pending redesign.

**HTML validation requires dev server** (run in separate terminal):
```bash
cd docusaurus
npm start
# Wait for "webpack compiled"
```

---

## Summary: Your Command Checklist

### Creating a Module

```bash
# Tell Claude (in natural language)
"Create module 50 for B1 level"

# Claude runs: /module-stage-1, /module-stage-2, /module-stage-3, /module-stage-4
```

### After Creation: Validate

**Tell agent to run validation:**
```bash
# Required - Audit (must pass) - agent runs:
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md

# Optional - Grammar (recommended) - agent runs:
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md --validate-grammar

# Optional - Content quality (before release) - agent runs:
AUDIT_CONTENT_QUALITY=true .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md
```

**YOU run activity quality validation manually:**
```bash
# Optional - Activity quality (high-stakes only)
npm run quality:generate l2-uk-en b1 50
# ... YOU fill in YAML manually ...
npm run quality:finalize l2-uk-en b1 50
```

### After Validation: Generate

**YOU run these manually:**
```bash
# Generate output
npm run pipeline l2-uk-en b1 50
# Note: JSON generation skipped (Vibe app on hold)
```

---

## What Each Command Does

| Command | What It Does | When to Run |
|---------|--------------|-------------|
| `.venv/bin/python scripts/audit_module.py {file}` | Check structure, pedagogy, format, richness | Always (required) |
| `.venv/bin/python scripts/audit_module.py {file} --validate-grammar` | Check Ukrainian grammar (Russianisms, calques) | B1+ recommended |
| `AUDIT_CONTENT_QUALITY=true .venv/bin/python scripts/audit_module.py {file}` | Review pedagogical quality (0-10 score) | Before release (optional) |
| `npm run quality:generate l2-uk-en b1 50` | Generate activity quality queue | High-stakes content only |
| `npm run quality:finalize l2-uk-en b1 50` | Finalize activity quality report | After manual validation |
| `npm run pipeline l2-uk-en b1 50` | Generate MDX + validate | After audit PASS |
| ~~`npm run generate:json`~~ | ~~Generate JSON for Vibe app~~ | **Disabled** (project on hold) |

---

## Typical Session (Copy-Paste Ready)

### Session Start

```bash
# Activate virtual environment
source .venv/bin/activate
```

### Create Module (Tell Claude)

```
Create module 50 for B1 level
```

### Validate (Tell Agent)

```bash
# Tell agent to run:
# Audit (required)
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md

# Grammar (optional, recommended)
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md --validate-grammar
```

### Fix if Needed (Tell Agent)

```
Fix these audit violations:
[paste violations from terminal]
```

### Generate (You Run)

```bash
# Start dev server (separate terminal)
cd docusaurus && pnpm start

# Generate output (main terminal)
npm run pipeline l2-uk-en b1 50
```

### Verify (You Check)

```
Open in browser: http://localhost:3000/learn-ukrainian/b1/module-50
Test all activities, check content
```

---

## What Claude Does Automatically

When you tell Claude "Create module 50 for B1", Claude:

1. Reads these documents:
   - `claude_extensions/quick-ref/b1.md`
   - `docs/l2-uk-en/B1-CURRICULUM-PLAN.md`
   - `docs/l2-uk-en/templates/b1-{type}-module-template.md`

2. Executes these commands (internally):
   - `/module-stage-1 b1 50` - Create skeleton with vocabulary
   - `/module-stage-2 b1 50` - Write content (examples, dialogues, engagement)
   - `/module-stage-3 b1 50` - Create activities (12-16 activities)
   - `/module-stage-4 b1 50` - Review and fix until audit pass

3. Reports back to you:
   - "Module created, audit status: PASS/FAIL"
   - If FAIL: Lists violations

**You don't run `/module-stage-*` commands** - Claude does that. You just tell Claude what module to create.

---

## Quick Decision Tree

```
START: You want to create B1 module 50
  │
  ├─→ Tell Claude: "Create module 50 for B1"
  │   (Claude runs all /module-stage-* commands)
  │
  ├─→ Claude reports: "Module created, audit: PASS/FAIL"
  │
  ├─→ If PASS:
  │   └─→ You run: npm run pipeline l2-uk-en b1 50
  │       └─→ DONE ✅
  │
  └─→ If FAIL:
      └─→ Tell Claude: "Fix violations: [paste]"
          └─→ Back to start (loop until PASS)
```

---

## Common Questions

### Q: Do I run `/module-stage-1 b1 50`?
**A:** Usually no. Just tell Claude "Create module 50 for B1" and Claude runs all stages. Only run manually if you want to review each stage individually.

### Q: What commands do I ALWAYS run?
**A:** After agent creates module and audit passes:
```bash
# YOU run this manually:
npm run pipeline l2-uk-en b1 50
```

**A:** Tell agent to run validation:
```bash
# Agent runs:
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md
```

### Q: What's optional?
**A:** Tell agent to run these validations:
```bash
# Grammar validation (recommended for B1+) - agent runs:
.venv/bin/python scripts/audit_module.py {file} --validate-grammar

# Content quality (before release) - agent runs:
AUDIT_CONTENT_QUALITY=true .venv/bin/python scripts/audit_module.py {file}
```

**A:** You run activity quality validation manually:
```bash
# High-stakes content only:
npm run quality:generate + manual validation + npm run quality:finalize
```

### Q: When do I use `/grammar-validate` or `/review-content`?
**A:** Never directly. These are Claude Code skills that Claude uses internally. You run the Python scripts shown above.

### Q: Where do I see the validation results?
**A:** In your terminal where you ran the command. Look for:
- Audit: `Overall Status: PASS` or `FAIL`
- Grammar: Violations listed in terminal
- Content: Score (0-10) and section breakdown
- Activity Quality: Report file in `curriculum/l2-uk-en/b1/audit/`

---

---

## Validating Existing Modules

**Should you re-run quality validation on already-created modules?**

### Current Status (January 2026)

| Level | Modules | Status | Audit Status |
|-------|---------|--------|--------------|
| A1 | 34/34 | ✅ Complete | ✅ All pass |
| A2 | 57/57 | ✅ Complete | ✅ Most pass (some quote style issues) |
| B1 | 91/91 | ✅ Complete | ✅ 90/91 pass (1 FAIL: minor issues) |
| B2 | 145/145 | ✅ Complete | ⚠️ 0/145 pass (lint/complexity issues) |
| C1 | 0/196 | 📋 Planned | ❌ Not started |
| C2 | 0/100 | 📋 Planned | ❌ Not started |

**Why B2 modules fail audit:**
- **Lint errors:** Ukrainian angular quotes («...») needed instead of ASCII quotes (")
- **Pedagogical:** Quiz prompts too short (<15 words), unjumble sentences too short (<14 words)
- **Schema:** Some modules have YAML schema violations (missing required fields)

**These are NOT critical content issues** - they're formatting and complexity violations that are easily fixable.

### Recommendation: Selective Re-Validation

**✅ DO Re-Validate (High Priority):**
- **Checkpoint modules:** B1 (M15, M25, M34, M41, M51, M61, M71, M81), B2 (M145)
- **Cultural/History:** B1 M72-81, B2 M71-131 (Ukrainian history)
- **Complex Grammar:** B1 M06-30, B2 M01-70

**⚠️ MAYBE Re-Validate (Medium Priority):**
- Vocabulary modules (B1 M52-71, B2 M136-140)
- Integration modules (B1 M82-86, B2 M132-138)

**❌ DON'T Re-Validate (Low Priority):**
- A1/A2 modules (scaffolded, already thoroughly reviewed)
- Working modules with no reported issues

### Batch Validation Scripts

**Run these inside an agent (Claude Code, Gemini CLI, Antigravity) where API keys are configured:**

**Grammar validation (checkpoints only - recommended):**
```bash
# B1 checkpoints (8 modules, ~4 minutes with gemini-3-flash)
for m in 15 25 34 41 51 61 71 81; do
  echo "=== B1 M$m ==="
  .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/$m-*.md --validate-grammar
done

# B2 history modules sample (7 modules, ~3.5 minutes)
for m in 71 80 90 100 110 120 131; do
  echo "=== B2 M$m ==="
  .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b2/$m-*.md --validate-grammar
done
```

**Content quality review (spot check):**
```bash
# B1 checkpoints (8 modules, ~12 minutes with gemini-3-flash)
for m in 15 25 34 41 51 61 71 81; do
  echo "=== B1 M$m ==="
  AUDIT_CONTENT_QUALITY=true .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/$m-*.md
done
```

### Model Selection

**For grammar validation and content review:**
- **gemini-3-flash** (recommended): Fast (~30 sec/module), cheap, excellent quality
- **gemini-3-pro**: Best quality, slower, more expensive (use for edge cases)

**Expected time:**
- Grammar validation: ~30 seconds per module (gemini-3-flash)
- Content quality review: ~60-90 seconds per module (gemini-3-flash)

**Expected cost (with gemini-3-flash):**
- B1 checkpoints (8 modules): ~$0.50
- B2 history sample (7 modules): ~$0.50
- Total selective validation: ~$2-3

### What to Do with Results

**Grammar violations:**
- 0-2 minor violations → Ignore (acceptable)
- 3-5 violations → Fix the specific violations
- 6+ violations → Module may need content review

**Content quality scores:**
- 8-10 → Excellent, no changes needed
- 7 → Good, minor improvements optional
- 5-6 → Needs improvement (add examples, engagement boxes)
- 0-4 → Rewrite module

**Activity quality:**
- **Skip for existing modules** (too time-consuming: 75 min per module)
- Only run on checkpoint modules if needed (8 modules × 75 min = 10 hours)

---

## Related Documentation

- **`docs/B1-PLUS-MODULE-WORKFLOW.md`** - Comprehensive guide (for Claude to follow)
- **`docs/ARCHITECTURE.md`** - System architecture overview
- **`docs/SCRIPTS.md`** - Detailed script reference

---

**TL;DR:**
1. Tell agent: "Create module X for level Y"
2. Tell agent: "Run audit on the module"
3. If FAIL: Tell agent to fix, repeat step 2
4. If PASS: You run: `npm run pipeline`
5. Done! ✅
