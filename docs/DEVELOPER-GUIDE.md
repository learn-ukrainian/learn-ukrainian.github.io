# Developer Guide - Learn Ukrainian

**For human developers working on the Ukrainian curriculum.**

This guide helps you understand the tools, workflows, and best practices for curriculum development.

---

## 🚀 Quick Start

### I want to...

| Goal | Command/Tool |
|------|--------------|
| **Create a new module** | `/module {level} {num}` |
| **Fix a failing module** | Paste audit log + `/interview` for complex issues |
| **Check module quality** | `scripts/audit_module.sh curriculum/l2-uk-en/{level}/{file}.md` |
| **Understand a design decision** | `/explain-decision [topic]` |
| **Quick review before commit** | `/review-content-quick {level} {num}` |
| **Final review (A1/A2/B1.0)** | `/review-content-core-a {level} {num}` |
| **Final review (B1.1+/B2+)** | `/review-content-v4 {level} {num}` |
| **Understand module status** | `/module-status {level} {num}` or `docs/{LEVEL}-STATUS.md` |

---

## 📁 Architecture Overview

### Three-Layer System

```
Plans (Immutable)          Build (Mutable)           Status (Cached)
    ↓                           ↓                         ↓
plans/{level}/{slug}.yaml → {level}/{slug}.md → status/{slug}.json
                          → meta/{slug}.yaml
                          → activities/{slug}.yaml
                          → vocabulary/{slug}.yaml
```

**Key Principle**: Plans are source of truth. Content must match plans. Status cache speeds up reporting.

**Files**:
- `plans/{level}/{slug}.yaml` - What to build (objectives, outline, vocab)
- `{level}/meta/{slug}.yaml` - How to build (pedagogy, duration)
- `{level}/{slug}.md` - The actual lesson content
- `status/{slug}.json` - Audit results cache (~15x faster than live audit)

**Docs**:
- `docs/ARCHITECTURE-PLANS.md` - Full architecture explanation
- `docs/STATUS-SYSTEM.md` - Status caching system

---

## 🛠️ Essential Tools

### 1. Module Audit (Quality Check)

**Wrapper (Recommended):**
```bash
scripts/audit_module.sh curriculum/l2-uk-en/b1/09-aspect-future.md
```
- Auto-saves log to `audit/aspect-future-audit.log`
- No need for manual `tee` commands

**Direct call:**
```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/09-aspect-future.md
```
- Use when you need raw output without log saving

**What it checks**:
- ✅ Word count (meets target?)
- ✅ Outline compliance (all sections from plan?)
- ✅ Activities (required types + counts?)
- ✅ Vocabulary (matches plan?)
- ✅ Structure (valid markdown?)
- ✅ Naturalness (8+/10 for Ukrainian quality)

**Output**: Detailed report with gates (✅/❌) + specific issues

### 2. Two-Tier Review System

**Quick Review** (3-5 min, during development):
```bash
/review-content-quick b1 9
```

**What it catches**:
- Duplicated content
- Robotic AI patterns ("Welcome to this lesson...")
- Russianisms/calques (auto-fail)
- Grammar errors (spot-check)
- Activity answer errors
- Flow issues

**When**: Before committing modules, during content generation

**Deep Review — Core A** (20-25 min, A1/A2/B1 M01-05):
```bash
/review-content-core-a a1 5
```

**What it validates (12 dimensions)**:
- L1/L2 balance (graduated immersion targets)
- Beginner safety ("Would I Continue?" test)
- IPA transcription accuracy
- State Standard grammar compliance
- Emotional beats (welcome, encouragement, progress)

**Deep Review — Core B / Seminar** (20-25 min, B1 M06+/B2+):
```bash
/review-content-v4 b1 9
```

**What it validates (14 dimensions)**:
- All Core A checks PLUS:
- Propaganda filter (B2+ cultural content)
- Semantic nuance (C1+ modal hedging)

**When**: Before final publication, when level complete

**Which review to use**:
| Modules | Command |
|---------|---------|
| A1, A2, B1 M01-05 | `/review-content-core-a` |
| B1 M06+, B2, C1, C2, PRO | `/review-content-v4` |

**Strategy**: Quick review during dev, deep review before release

### 3. Interview Tool (Specification Before Building)

**When to use**:
- ✅ Complex feature (>30 min work)
- ✅ Requirements unclear
- ✅ Multiple approaches possible
- ✅ Broad request ("improve X", "add Y")

**Usage**:
```bash
/interview Create integrated checkpoint activities for B1 grammar modules
```

**Process**:
1. 40-60 questions across 4 phases
2. Generates complete specification document
3. Get approval before building
4. Build with confidence

**Benefit**: Build once instead of iterating 5 times

**Modes**:
- Comprehensive (default): 60 questions
- Focused (`--mode focused`): 20-30 questions
- Rapid (`--mode rapid`): 10-15 questions

### 4. Design Rationale Tool (Learning)

**Purpose**: Understand "why" behind curriculum decisions

**Usage**:
```bash
/explain-decision aspect-teaching-sequence     # Why aspect at B1 not A2?
/explain-decision module b1 9                  # Why is M9 structured this way?
/explain-decision compare aspect-first vs motion-first
```

**Output**:
1. Direct answer (2-3 sentences)
2. Pedagogical rationale
3. CEFR alignment
4. Trade-offs
5. Alternatives considered
6. Ukrainian-specific factors
7. Recommendations

**Use this to**: Learn curriculum design principles, not just execute tasks

---

## 📋 Common Workflows

### Creating a New Module

**Full pipeline (recommended):**
```bash
/module b1 15
```

**This runs 9 phases**:
1. Extract plan (from meta if needed)
2. Create skeleton
3. Generate content
4. Create activities
5. Enrich vocabulary
6. Review & fix loop
7. Generate MDX
8. Validate MDX
9. Update status

**Manual approach** (if you prefer control):
```bash
# 1. Check plan exists
cat curriculum/l2-uk-en/plans/b1/aspect-future.yaml

# 2. Read requirements
cat curriculum/l2-uk-en/b1/meta/aspect-future.yaml
cat claude_extensions/quick-ref/B1.md

# 3. Write content (or use /module-lesson)
# 4. Audit
scripts/audit_module.sh curriculum/l2-uk-en/b1/09-aspect-future.md

# 5. Fix issues until audit passes
# 6. Generate MDX
npm run pipeline l2-uk-en b1 9
```

### Fixing a Failing Module

**Efficient approach using Bug Fix Protocol**:

```bash
# 1. Get full audit log
scripts/audit_module.sh curriculum/l2-uk-en/b1/09-aspect-future.md

# 2. Give Claude clear instructions:
"Fix M09. Here's the full audit log:

[paste curriculum/l2-uk-en/b1/audit/aspect-future-audit.log]

Fix all issues:
1. Read plan file first to see what's missing
2. Add missing subsections from outline
3. Expand content to meet word target (3000)
4. Re-audit until pass

Use the plan as source of truth."
```

**For complex issues**:
```bash
/interview Fix module B1-09 outline compliance and word count issues
```

**Batch fixing multiple modules**:
```bash
"Batch fix outline compliance for B1 modules 15-20.

For each module:
- Read plan outline
- Compare to actual sections in .md
- Add any missing subsections
- Ensure each subsection has content
- Re-audit

Work systematically, don't skip any."
```

### Checking Module/Level Status

**Single module**:
```bash
/module-status b1 9
```

**Entire level**:
```bash
/level-status b1
# or read: docs/B1-STATUS.md
```

**Regenerate level status** (after fixing modules):
```bash
npm run status:b1
# or: .venv/bin/python scripts/generate_level_status.py b1
```

### Before Committing Changes

**Quick validation checklist**:
```bash
# 1. Quick review (catches obvious issues)
/review-content-quick b1 9

# 2. Audit passes?
scripts/audit_module.sh curriculum/l2-uk-en/b1/09-aspect-future.md

# 3. MDX generates correctly?
npm run pipeline l2-uk-en b1 9

# 4. Status updated?
npm run status:b1
```

---

## 🎯 Best Practices

### Working with Claude

**Use Enhanced Prompting Patterns** (see CLAUDE.md):

1. **Self-Review**: Ask Claude to review its own work
   ```
   "Review your work on M15:
   1. Does it match the plan outline exactly?
   2. Are there any sections that feel thin or robotic?
   3. Are all Ukrainian sentences natural (no calques)?
   4. What would make it pedagogically stronger?"
   ```

2. **Upfront Specifications**: Confirm Claude read requirements first
   ```
   "Before you write M20, confirm you've read:
   1. plans/b1/motion-approaching-departing.yaml
   2. meta/motion-approaching-departing.yaml
   3. quick-ref/B1.md

   Tell me: word target, key grammar focus, required activities"
   ```

3. **Comparative Examples**: Show what you want vs. don't want
   ```
   "M18 feels robotic. Example:

   ❌ Current: 'Тепер ми розглянемо дієслово "переходити"...'
   ✅ Better: 'Уявіть: ви стоїте на одному боці вулиці...'

   Apply this pattern throughout M18"
   ```

**Use Interview Tool** for complex tasks:
- Building new features
- Unclear requirements
- Exploring alternatives

**Use explain-decision** when you want to learn:
- Why things are designed certain ways
- Pedagogical principles
- CEFR alignment reasoning

### Quality Standards

**Non-negotiable**:
- Word count ≥ target (95% minimum)
- All plan outline sections included
- Activities meet richness guidelines
- Ukrainian language = native quality (8+/10)
- No Russianisms/calques

**Common failures** (see CLAUDE.md "Lessons Learned"):
1. Outline compliance (missing subsections)
2. Word count shortfalls
3. Activity gaps (missing types)
4. Checkpoint confusion (treating like regular modules)

### Resource Strategy

**During content generation (A1-C1)**:
- Use **quick review** (fast, catches obvious issues)
- Use `audit_module.sh` (validates structure)
- Save deep review for later

**Before publication**:
- Run **deep review** (comprehensive validation)
- Batch deep reviews by level when complete
- Quality is non-negotiable (this is for a nation's education)

---

## 📚 Key Documentation

### Essential Reading (Start Here)

| Doc | Purpose |
|-----|---------|
| **CLAUDE.md** | AI agent instructions, critical rules, prompting patterns |
| **CURRENT-STATUS.md** | Current project state, recent work, next priorities |
| **SCRIPTS.md** | All scripts and skills reference |
| **ARCHITECTURE-PLANS.md** | Three-layer architecture explanation |
| **CLAUDE-GEMINI-COOPERATION.md** | Multi-LLM collaboration system ⭐ NEW |

### Workflow Guides

| Doc | Purpose |
|-----|---------|
| **CORE-A-WORKFLOW.md** | Mixed-language rebuild workflow (A1/A2/B1.0 — 119 modules) |
| **CORE-B-WORKFLOW.md** | Full-immersion rebuild workflow (B1.1+/B2/C1/C2/PRO — 477 modules) |
| **RESEARCH-FIRST-WORKFLOW.md** | Deep research workflow (seminar tracks — B2-HIST, C1-BIO, LIT) |
| **MODULE-RICHNESS-GUIDELINES-v2.md** | Activity counts, complexity requirements |
| **PLANNING-GUIDE.md** | How to create module plans |
| **STATUS-SYSTEM.md** | Status caching system |
| **SUBSECTION-FLEXIBILITY-GUIDE.md** | When to deviate from plan structure |

### Quick References (By Level)

| Level | Quick Ref |
|-------|-----------|
| B1 | `claude_extensions/quick-ref/B1.md` |
| B2 | `claude_extensions/quick-ref/B2.md` |
| C1 | `claude_extensions/quick-ref/C1.md` |

### Skills Documentation

| Skill | File |
|-------|------|
| Interview | `claude_extensions/commands/interview.md` |
| Explain Decision | `claude_extensions/commands/explain-decision.md` |
| Quick Review | `claude_extensions/commands/review-content-quick.md` |
| Core A Review (A1/A2/B1.0) | `claude_extensions/commands/review-content-core-a.md` |
| Deep Review (B1.1+/B2+) | `claude_extensions/commands/review-content-v4.md` |
| Deep Review Optimization | `claude_extensions/commands/review-content-deep-optimized.md` |

---

## 🔧 Terminal Setup

### Ghostty Terminal (Recommended)

**Why**: GPU acceleration, native UI, zero-config, split windows

**Key shortcuts**:
- `⌘+D` - Split horizontal (audit in one pane, edit in another)
- `⌘+Shift+D` - Split vertical
- Tab overview - Manage multiple modules
- Auto-naming - Tabs name themselves based on commands

**Config** (optional): `~/.config/ghostty/config`

**Resources**:
- [Ghostty Docs](https://ghostty.org/docs)
- [Feature Guide](https://itsfoss.com/ghostty-terminal-features/)

### Modern CLI Tools

**Installed and preferred**:
- `rg` (grep) - Fast code search
- `fd` (find) - Fast file finding
- `bat` (cat) - Syntax highlighting
- `sd` (sed) - Modern text replacement
- `yq` (YAML) - YAML manipulation
- `jq` (JSON) - JSON manipulation

---

## 🐛 Debugging & Troubleshooting

### Module Audit Fails

**1. Outline Compliance Error**
```
Problem: Missing subsections from plan
Fix: Read plan outline, add ALL subsections listed
```

**2. Word Count Under Target**
```
Problem: 2500 words vs 3000 target
Fix: Expand explanations, add examples, develop practice sections
Verify: Run word count during generation, not just at end
```

**3. Activity Errors**
```
Problem: Missing required activity types
Fix: Check MODULE-RICHNESS-GUIDELINES-v2.md for minimum counts
      Generate activities for EACH major concept taught
```

**4. Naturalness Score < 8**
```
Problem: Ukrainian text sounds translated or robotic
Fix: Rewrite problematic sections
     Check for Russianisms/calques
     Verify case agreement, verb aspects, gender
```

### Python Environment Issues

**Wrong Python version**:
```bash
# Always use .venv/bin/python
.venv/bin/python --version  # Should show 3.12.8

# If wrong, recreate venv
rm -rf .venv
~/.pyenv/versions/3.12.8/bin/python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

**SQLite extension error**:
```bash
# Python must be compiled with --enable-loadable-sqlite-extensions
# Already handled via pyenv installation (see .python-version)
```

### Skill Not Found

**Deploy skills**:
```bash
npm run claude:deploy
```

**Check deployment**:
```bash
ls -la .claude/commands/interview.md
ls -la .agent/workflows/interview.md
```

---

## 🎓 Learning Path

**For new developers** (you):

1. **Understand architecture** (30 min)
   - Read `ARCHITECTURE-PLANS.md`
   - Understand Plans → Build → Status flow

2. **Learn quality standards** (20 min)
   - Read `MODULE-RICHNESS-GUIDELINES-v2.md`
   - Check `claude_extensions/quick-ref/B1.md` (or your target level)

3. **Try creating a module** (1-2 hours)
   - Use `/module b1 [pick a number]`
   - Watch the 9-phase workflow
   - Review audit output

4. **Fix a failing module** (30 min)
   - Pick one from `docs/B1-STATUS.md`
   - Use Bug Fix Protocol
   - Iterate until audit passes

5. **Use learning tools** (ongoing)
   - `/explain-decision` when confused about design
   - `/interview` before complex features
   - Prompting patterns for better Claude output

**For understanding pedagogy**:

```bash
/explain-decision why-aspect-at-b1-not-a2
/explain-decision checkpoint-placement
/explain-decision vocabulary-selection-criteria
```

---

## 📊 Current Project Status

**As of February 2026**:

| Level | Modules | Passing | Status |
|-------|---------|---------|--------|
| A1 | 44 | 44 | ✅ Complete |
| A2 | 70 | 70 | ✅ Complete |
| B1 | 92 | 23 | 🚧 25% (fixing) |
| B2 | 94 | TBD | 🚧 In progress |
| B2-HIST | 140 | TBD | 🚧 Content phase |
| C1 | 106 | TBD | 🚧 In progress |

**Current priority**: Fix B1 failing modules (23/92 → 80%+)

**See**: `docs/CURRENT-STATUS.md` for detailed status

---

## 🚀 Next Steps

**Immediate**:
1. Fix B1 failing modules using new workflow tools
2. Complete B2-HIST content generation
3. Batch deep review before publication

**Future**:
4. Improve Claude-Gemini cooperation (Task #18)
5. Complete C1, C2, LIT tracks

---

## 💡 Tips & Tricks

### Time Savers

1. **Use parallel reads** in Claude prompts:
   ```
   "Read these files in parallel:
   - plans/b1/aspect-future.yaml
   - meta/aspect-future.yaml
   - quick-ref/B1.md"
   ```

2. **Batch operations** when possible:
   ```bash
   # Fix multiple modules
   for i in {9..15}; do
     scripts/audit_module.sh curriculum/l2-uk-en/b1/$i-*.md
   done
   ```

3. **Use interview mode** for specs:
   - Comprehensive: When totally unclear
   - Focused: When mostly clear but gaps
   - Rapid: When just need quick clarification

### Quality Boosters

1. **Self-review before asking Claude**:
   - Does this match the plan?
   - Is Ukrainian natural?
   - Are there obvious issues?

2. **Reference previous success**:
   ```
   "M87 and M88 passed with high scores.
   Use those as templates for M89."
   ```

3. **Specify constraints upfront**:
   ```
   "Generate M25 with these constraints:
   MUST: Test modules 16-24, 3000 words, TTT approach
   MUST NOT: Introduce new grammar, use vocab outside range"
   ```

---

## 🔗 External Resources

- [CEFR Official Descriptors](https://www.coe.int/en/web/common-european-framework-reference-languages)
- [Ukrainian State Standard 2024](https://mon.gov.ua/)
- [Ghostty Terminal](https://ghostty.org/)
- [Claude Code CLI](https://claude.ai/code)

---

## 📝 Quick Command Reference

```bash
# MODULE OPERATIONS
/module {level} {num}                          # Create full module
/module-status {level} {num}                   # Check module status
/level-status {level}                          # Check level status

# QUALITY CHECKS
scripts/audit_module.sh {path}                 # Audit with log save
/review-content-quick {level} {num}            # Fast pre-check (3-5 min)
/review-content-core-a {level} {num}           # Deep review: A1/A2/B1.0
/review-content-v4 {level} {num}               # Deep review: B1.1+/B2+

# LEARNING & PLANNING
/explain-decision [topic]                      # Understand design rationale
/interview [task]                              # Spec through questions

# STATUS & GENERATION
npm run status:{level}                         # Regenerate level status
npm run pipeline l2-uk-en {level} {num}        # Generate MDX + validate
npm run claude:deploy                          # Deploy skill changes

# PYTHON ENVIRONMENT
.venv/bin/python scripts/audit_module.py      # Always use venv Python
.venv/bin/python --version                     # Check version (3.12.8)
```

---

**Remember**: Quality over speed. This is for Ukrainian language and culture preservation.

**Мова – душа народу 🇺🇦**
