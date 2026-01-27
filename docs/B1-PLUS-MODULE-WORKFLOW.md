# B1+ Module Creation & Validation Workflow

**Complete end-to-end guide for creating B1, B2, C1, and C2 modules with full quality validation.**

> **👤 For human users:** See **`docs/HUMAN-WORKFLOW-B1-PLUS.md`** for a simplified guide showing exactly what commands YOU run.
>
> **🤖 This document** is the comprehensive reference that AI agents (Claude/Gemini) follow when creating modules.

---

## Table of Contents

1. [Overview](#overview)
2. [Quality Validation Systems](#quality-validation-systems)
3. [Prerequisites](#prerequisites)
4. [Complete Workflow](#complete-workflow)
5. [Stage-by-Stage Creation](#stage-by-stage-creation)
6. [Quality Validation (Optional)](#quality-validation-optional)
7. [Pipeline Generation](#pipeline-generation)
8. [Troubleshooting](#troubleshooting)

---

## Overview

B1+ modules (B1, B2, C1, C2) are **100% immersed Ukrainian content** (except B1 M01-05 bridge modules at 65%). They require:

- Advanced pedagogical structure (PPP/TTT)
- High activity quality and variety
- Natural Ukrainian language (no Russianisms, calques)
- CEFR-appropriate difficulty
- Rich content (examples, engagement, cultural context)

This workflow uses a **4-stage creation pipeline** followed by **3 optional quality validation systems**.

---

## Quality Validation Systems

Learn Ukrainian has three complementary quality validation systems:

| System | Type | Validation Focus | When to Use | API Required |
|--------|------|------------------|-------------|--------------|
| **Audit** | Automated | Structure, pedagogy, format, richness | Always (required) | No |
| **Grammar Validation** | LLM-based | Ukrainian grammar correctness (Russianisms, calques, errors) | B1+ recommended | Yes (Gemini) |
| **Content Quality Review** | LLM-based | Pedagogical quality, examples, scaffolding, cultural relevance | Optional, before release | Yes (Gemini) |
| **Activity Quality** | Hybrid (deterministic + manual) | Naturalness, difficulty, distractors, engagement, variety | Optional, for high-stakes content | Partially |

### System Details

#### 1. Audit (Required)

- **Script**: `scripts/audit_module.py`
- **Checks**:
  - Structure (sections, headers, frontmatter)
  - Pedagogy (PPP/TTT compliance, activity sequencing)
  - Format (markdown syntax, activity formats)
  - Richness (examples, engagement boxes, variety)
  - Vocabulary (plan compliance, no duplicates)
  - Immersion percentage (CEFR-appropriate)
- **Usage**: `.venv/bin/python scripts/audit_module.py {file_path}`
- **Gates**: Blocks pipeline if FAIL

#### 2. Grammar Validation (Recommended for B1+)

- **Skill**: `/grammar-validate` (Claude Code skill)
- **Checks**:
  - Russianisms (кушать → їсти)
  - Calques (робити сенс → мати сенс)
  - Surzhyk (mixed Ukrainian-Russian)
  - Unnatural word order
  - Case/gender/number agreement
  - CEFR-inappropriate complexity
- **Usage**:
  - Manual: `/grammar-validate` in Claude Code (paste module content)
  - Automated: `.venv/bin/python scripts/audit_module.py {file} --validate-grammar` (requires `GEMINI_API_KEY`)
- **Output**: JSON report with violations, severity, corrections
- **Gates**: Informational (doesn't block audit)

#### 3. Content Quality Review (Optional)

- **Skill**: `/review-content` (Claude Code skill)
- **Checks**:
  - Pedagogical coherence (objectives ↔ activities alignment)
  - Example quality (authenticity, cultural relevance)
  - Scaffolding (graduated difficulty)
  - Engagement (interesting, not boring)
  - Cultural context (Ukrainian-specific, not generic)
  - Section 8: Activity quality dimensions (naturalness, difficulty, distractors, engagement)
- **Usage**:
  - Manual: `/review-content` in Claude Code (paste module content)
  - Automated: `AUDIT_CONTENT_QUALITY=true GEMINI_API_KEY=xxx .venv/bin/python scripts/audit_module.py {file}`
- **Output**: Markdown report with scores (0-10) and recommendations
- **Documentation**: `docs/CONTENT-QUALITY-AUDIT.md`

#### 4. Activity Quality Validation (Optional)

- **Type**: Hybrid (deterministic + manual semantic validation)
- **Checks**:
  - **Naturalness** (1-5): Robotic → Highly Natural
  - **Difficulty** (3-option): too_easy | appropriate | too_hard
  - **Distractor Quality** (1-5): Nonsense → Excellent
  - **Engagement** (1-5): Boring → Highly Engaging
  - **Variety** (0-100%): Mechanical pattern detection
- **Usage**: Queue-based workflow (see [Activity Quality Validation](#activity-quality-validation))
- **CEFR Gates**:
  - B1: 3.5 naturalness, 60% variety, 4.0 distractors, ≤20% inappropriate
  - B2: 4.0 naturalness, 65% variety, 4.2 distractors, ≤15% inappropriate
  - C1: 4.5 naturalness, 70% variety, 4.5 distractors, ≤10% inappropriate
  - C2: 4.8 naturalness, 75% variety, 5.0 distractors, ≤5% inappropriate
- **Output**: Markdown report in `audit/` directory
- **Documentation**: `docs/SCRIPTS.md` - Activity Quality Validation section

### When to Use Which System

| Stage | Audit | Grammar | Content Review | Activity Quality |
|-------|-------|---------|----------------|------------------|
| **After Stage 1 (Skeleton)** | ✅ Structure only | ❌ No content yet | ❌ No content yet | ❌ No activities yet |
| **After Stage 2 (Content)** | ✅ Full audit | ✅ Yes (grammar) | ✅ Yes (optional) | ❌ No activities yet |
| **After Stage 3 (Activities)** | ✅ Full audit | ✅ Yes (full module) | ✅ Yes (full review) | ✅ Yes (optional) |
| **After Stage 4 (Review/Fix)** | ✅ Must PASS | ✅ Final check | ✅ Final review | ✅ Final validation |
| **Before Release** | ✅ Must PASS | ✅ Recommended | ✅ Recommended | ⚠️ High-stakes only |

---

## Prerequisites

### 1. Environment Setup

```bash
# Python virtual environment with dependencies
source .venv/bin/activate  # Or use .venv/bin/python directly

# Verify dependencies
.venv/bin/python -c "import yaml, re, os; print('OK')"
```

### 2. API Keys (Optional)

For optional LLM-based validation:

```bash
# Gemini API key for grammar/content validation
export GEMINI_API_KEY="your-gemini-api-key"

# Enable content quality audit (optional)
export AUDIT_CONTENT_QUALITY="true"
```

### 3. Documentation

Read these before starting:

- **Level-specific quick-ref**: `claude_extensions/quick-ref/{level}.md`
- **Curriculum plan**: `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`
- **Richness guidelines**: `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- **Template**: `docs/l2-uk-en/templates/{level}-{type}-module-template.md`

### 4. Required Scripts

```bash
# Audit (always needed)
.venv/bin/python scripts/audit_module.py

# Pipeline (generation + validation)
.venv/bin/python scripts/pipeline.py

# Activity quality (optional)
.venv/bin/python scripts/generate_activity_quality_queue.py
.venv/bin/python scripts/finalize_activity_quality.py
```

---

## Complete Workflow

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    MODULE CREATION STAGES                        │
│                                                                 │
│  Stage 1: Skeleton → Stage 2: Content → Stage 3: Activities    │
│              ↓             ↓                  ↓                  │
│           [audit]      [audit]           [audit]               │
│                        [grammar?]        [grammar?]            │
│                        [content?]        [content?]            │
│                                          [activity?]           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STAGE 4: REVIEW & FIX                         │
│                                                                 │
│  1. Run audit (must PASS)                                       │
│  2. Optional: Run grammar validation                            │
│  3. Optional: Run content quality review                        │
│  4. Optional: Run activity quality validation                   │
│  5. Fix violations (loop until PASS)                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE GENERATION                           │
│                                                                 │
│  1. Lint markdown                                               │
│  2. Generate MDX (Docusaurus)                                   │
│  3. Validate MDX (content integrity)                            │
│  4. ~~Generate JSON~~ (Vibe app on hold)                        │
│  5. Validate HTML (browser rendering - needs dev server)        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                       ✅ MODULE COMPLETE
```

### Quick Command Reference

```bash
# === MODULE CREATION ===
# Full pipeline (all 4 stages)
/module-create b1 50

# Individual stages
/module-stage-1 b1 50    # Skeleton
/module-stage-2 b1 50    # Content
/module-stage-3 b1 50    # Activities
/module-stage-4 b1 50    # Review/Fix

# === VALIDATION ===
# Audit (required)
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md

# Grammar validation (optional, requires GEMINI_API_KEY)
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md --validate-grammar

# Content quality (optional, requires GEMINI_API_KEY + AUDIT_CONTENT_QUALITY=true)
AUDIT_CONTENT_QUALITY=true .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md

# Activity quality (optional, manual workflow - see section below)
npm run quality:generate l2-uk-en b1 50
# ... manual validation in YAML ...
npm run quality:finalize l2-uk-en b1 50

# === PIPELINE GENERATION ===
# Full pipeline (lint → generate → validate)
npm run pipeline l2-uk-en b1 50

# Individual steps
npm run generate l2-uk-en b1 50        # MDX for Docusaurus
# npm run generate:json - SKIP (Vibe app on hold)
npm run validate:mdx l2-uk-en b1 50    # Content integrity
npm run validate:html l2-uk-en b1 50   # Browser rendering (needs dev server)
```

---

## Stage-by-Stage Creation

### Stage 1: Skeleton

**Purpose**: Create module structure with exact vocabulary from plan.

**Command**: `/module-stage-1 b1 50`

**What it creates**:
- YAML frontmatter (module, title, level, phase, pedagogy, objectives)
- Section headers based on pedagogy (PPP/TTT/CLIL)
- Vocabulary table (copied EXACTLY from curriculum plan)
- `[placeholder]` markers for content sections

**Verification**:
```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md
```

**Expected audit results**:
- ✅ Structure: Valid sections
- ✅ Vocabulary: Matches plan
- ❌ Content: Placeholders (expected)
- ❌ Activities: None yet (expected)

**Fix before proceeding**: Only structural issues (missing sections, incorrect headers).

---

### Stage 2: Content

**Purpose**: Fill in rich instructional content.

**Command**: `/module-stage-2 b1 50`

**What it creates**:
- Narrative introduction (engaging, not "Welcome to...")
- Presentation section (grammar explanations, examples, tables)
- Practice section (guided exercises, scaffolding)
- Engagement boxes (💡 Did You Know, 🎬 Pop Culture, 🌍 Real World)
- Mini-dialogues (2-5+ authentic Ukrainian conversations)
- Examples (12-32+ by level, using only vocab from this + prior modules)

**Content requirements by level**:

| Level | Word Count | Examples | Engagement | Dialogues | Immersion |
|-------|------------|----------|------------|-----------|-----------|
| **B1** | 800-1200 | 18-24 | 3-5 | 3-5 | 100% (M06+) |
| **B2** | 1200-1600 | 24-30 | 4-6 | 4-6 | 100% |
| **C1** | 1500-2000 | 30-36 | 5-8 | 5-8 | 100% |
| **C2** | 1800-2400 | 36+ | 6+ | 6+ | 100% |

**Verification**:
```bash
# Audit (required)
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md

# Grammar validation (optional but recommended)
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md --validate-grammar
```

**Expected audit results**:
- ✅ Structure: Complete
- ✅ Content: Rich, meets word count
- ✅ Vocabulary: Used correctly
- ✅ Immersion: 100% (B1 M06+, B2, C1, C2)
- ⚠️ Grammar: Check for Russianisms, calques
- ❌ Activities: None yet (expected)

**Fix before proceeding**:
- All structural violations
- Grammar violations (Russianisms, calques, unnatural Ukrainian)
- Immersion violations (wrong percentage)
- Vocabulary violations (words not in plan or prior modules)

---

### Stage 3: Activities

**Purpose**: Create diverse, sequenced activities.

**Command**: `/module-stage-3 b1 50`

**What it creates**:
- 12-16+ activities (by level)
- 15-20+ items per activity
- 5-7+ activity types
- Proper sequencing (warm-up → practice → production)

**Activity requirements by level**:

| Level | Min Activities | Items/Activity | Min Types | Must Include |
|-------|----------------|----------------|-----------|--------------|
| **B1** | 12 | 15 | 5 | fill-in, unjumble, cloze, error-correction, quiz |
| **B2** | 14 | 18 | 6 | All B1 + translate, select, mark-the-words |
| **C1** | 14 | 20 | 6 | All B2 + advanced cloze, complex error-correction |
| **C2** | 14 | 20 | 6 | All C1 + stylistic analysis, register variation |

**Activity types**:

| Type | Description | Levels | Priority |
|------|-------------|--------|----------|
| `quiz` | Multiple choice (single answer) | All | Core |
| `match-up` | Match pairs (UK ↔ EN) | All | Core |
| `fill-in` | Gap fill with dropdown | All | Core |
| `group-sort` | Sort items into categories | All | Core |
| `unjumble` | Reorder words into sentence | All | Core |
| `true-false` | Statement validation | A1-B2 | Core |
| `error-correction` | Find and fix errors | A2+ | Priority |
| `cloze` | Passage completion | A2+ | Priority |
| `mark-the-words` | Click words matching criteria | A2+ | Engagement |
| `select` | Multi-checkbox selection | A2+ | Optional |
| `translate` | Translation multiple choice | A2+ | Optional |

**Verification**:
```bash
# Audit (required)
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md

# Grammar validation (recommended - check activity text)
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md --validate-grammar
```

**Expected audit results**:
- ✅ Structure: Complete
- ✅ Activities: Count, types, items meet requirements
- ✅ Vocabulary: Activities use only module + prior vocab
- ⚠️ Activity quality: Check answers, distractors
- ⚠️ Grammar: Natural Ukrainian in all activity text

**Fix before proceeding**:
- Activity count violations
- Activity type violations (missing required types)
- Item count violations (too few items per activity)
- Answer correctness (wrong answers marked as correct)
- Grammar violations in activity text
- Vocabulary violations (using words not yet introduced)

---

### Stage 4: Review & Fix

**Purpose**: Audit, validate, fix until module passes all gates.

**Command**: `/module-stage-4 b1 50`

**Process**:

1. **Run audit** (required):
   ```bash
   .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md
   ```

2. **Count violations**:
   - ≤3 violations → Fix individually
   - >3 violations in one section → Rebuild section (call earlier stage)
   - >10 violations or structural → Rebuild from Stage 1

3. **Optional validations** (recommended for B1+):
   ```bash
   # Grammar validation
   .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md --validate-grammar

   # Content quality review
   AUDIT_CONTENT_QUALITY=true .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md

   # Activity quality validation (see detailed workflow below)
   npm run quality:generate l2-uk-en b1 50
   # ... manual validation ...
   npm run quality:finalize l2-uk-en b1 50
   ```

4. **Fix violations**:
   - Address all FAIL-level issues
   - Address recommended fixes from validation reports
   - Loop until audit PASS

5. **Maximum 3 iterations**:
   - If not passing after 3 fix loops → Rebuild from earlier stage
   - Common reasons: structural issues, vocabulary scope, grammar patterns

**Exit criteria**:
- ✅ Audit: PASS (all required gates green)
- ✅ Grammar: No critical violations (if validated)
- ✅ Content: Score 7+ (if reviewed)
- ✅ Activity Quality: PASS CEFR gates (if validated)

---

## Quality Validation (Optional)

### Grammar Validation

**When to use**: All B1+ modules (recommended).

**Skill**: `/grammar-validate` (Claude Code)

**Automated**:
```bash
export GEMINI_API_KEY="your-key"
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md --validate-grammar
```

**Manual (in Claude Code)**:
```
/grammar-validate

[Paste module content or specific sections]
```

**What it checks**:
1. **Russianisms**: кушать → їсти, кофе → кава, обязательно → обов'язково
2. **Calques**: робити сенс → мати сенс, мати місце → відбуватися
3. **Surzhyk**: Mixed Ukrainian-Russian forms
4. **Unnatural word order**: Influenced by English/Russian structure
5. **Case/gender/number agreement**: Morphological correctness
6. **CEFR appropriateness**: Complexity matches level

**Output format** (JSON):
```json
{
  "violations": [
    {
      "line": 45,
      "type": "russicism",
      "severity": "critical",
      "text": "Я кушаю яблуко",
      "issue": "Russicism: кушати",
      "correction": "Я їм яблуко",
      "explanation": "Use їсти instead of кушати (Russian loan)"
    }
  ],
  "summary": {
    "total": 3,
    "critical": 1,
    "major": 2,
    "minor": 0
  }
}
```

**How to fix**:
- Apply corrections directly to module markdown
- Re-run validation to verify
- For pedagogical exceptions (e.g., teaching "Я є студент" for A1), document in comments

**Trusted sources**:
- **Slovnyk.ua** (standard Ukrainian dictionary)
- **Grinchenko Dictionary** (authentic historical forms)
- **Antonenko-Davydovych "Як ми говоримо"** (Russianisms guide)

---

### Content Quality Review

**When to use**: Optional, before releasing modules.

**Skill**: `/review-content` (Claude Code)

**Automated**:
```bash
export GEMINI_API_KEY="your-key"
export AUDIT_CONTENT_QUALITY="true"
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md
```

**Manual (in Claude Code)**:
```
/review-content

[Paste module content]
```

**What it checks** (8 sections):

1. **Pedagogical Coherence** (0-10):
   - Objectives ↔ activities alignment
   - Scaffolding (simple → complex)
   - Pedagogy compliance (PPP/TTT structure)

2. **Example Quality** (0-10):
   - Authenticity (real Ukrainian usage)
   - Cultural relevance (Ukraine-specific context)
   - Appropriateness (CEFR level-appropriate)

3. **Engagement & Interest** (0-10):
   - Boring vs interesting content
   - Repetitive vs varied
   - Dry vs rich narrative

4. **Cultural Context** (0-10):
   - Ukrainian-specific vs generic
   - Historical accuracy
   - Contemporary relevance

5. **Explanation Quality** (0-10):
   - Clear grammar explanations
   - Visual aids (tables, diagrams)
   - Progressive disclosure

6. **Narrative Flow** (0-10):
   - Logical progression
   - Transitions between sections
   - Cohesion

7. **Vocabulary Usage** (0-10):
   - Appropriate frequency
   - Contextualized (not list-heavy)
   - Reinforcement throughout module

8. **Activity Quality** (0-10):
   - Naturalness (not robotic)
   - Difficulty calibration (not too easy/hard)
   - Distractor quality (plausible errors)
   - Engagement (interesting scenarios)
   - Variety (no mechanical patterns)

**Output format** (Markdown report):
```markdown
# Content Quality Review: Module 50

**Overall Score:** 8.2/10 ✅ PASS

## Section Scores
- Pedagogical Coherence: 9/10 ✅
- Example Quality: 8/10 ✅
- Engagement: 7/10 ⚠️
- Cultural Context: 9/10 ✅
- Explanation Quality: 8/10 ✅
- Narrative Flow: 8/10 ✅
- Vocabulary Usage: 8/10 ✅
- Activity Quality: 8/10 ✅

## Recommendations
- Add 1-2 more engagement boxes (Currently 3, target 4-5 for B1)
- Consider adding pop culture reference (Witcher 3, S.T.A.L.K.E.R.)
- Error-correction activity #7: Distractor "прочитати" too obvious
```

**How to fix**:
- Address all critical issues (score ≤5)
- Improve sections with warnings (score 6-7)
- Optional: Enhance excellent sections (score 8-9 → 10)

**Documentation**: `docs/CONTENT-QUALITY-AUDIT.md`

---

### Activity Quality Validation

**When to use**: Optional, for high-stakes content (C1/C2, pre-publication).

**Type**: Hybrid (deterministic checks + manual semantic validation)

**Workflow**:

#### Step 1: Generate Quality Queue

```bash
npm run quality:generate l2-uk-en b1 50
```

**Output**: `curriculum/l2-uk-en/b1/audit/50-{slug}-quality-queue.yaml`

**Queue structure**:
```yaml
module: "50"
level: "B1"
activities:
  - id: "activity-1-quiz-dative-case"
    type: "quiz"
    text: "Я дав книгу ____ другу."
    correct_answer: "моєму"
    options: ["моєму", "мій", "моїм", "мого"]

    # Deterministic checks (pre-populated)
    deterministic:
      cognitive_load: "low"
      vocabulary_difficulty: "appropriate"
      variety_contribution: 15  # percent

    # Manual validation (YOU FILL IN)
    manual_naturalness: null      # 1-5 scale
    manual_difficulty: null       # too_easy | appropriate | too_hard
    manual_engagement: null       # 1-5 scale
    manual_distractor_quality: null  # 1-5 scale (plausibility of wrong answers)
    manual_notes: ""
```

#### Step 2: Manual Validation

Open the queue YAML and fill in the `manual_*` fields for each activity:

```yaml
manual_naturalness: 4          # Natural Ukrainian, not robotic
manual_difficulty: appropriate # Level-appropriate for B1
manual_engagement: 3           # Functional but not exciting
manual_distractor_quality: 4   # Plausible errors (case confusion)
manual_notes: "Good case contrast, consider more engaging context"
```

**Validation criteria**:

| Dimension | Scale | What to Check |
|-----------|-------|---------------|
| **Naturalness** | 1-5 | Does it sound like real Ukrainian? Any calques, Russianisms, unnatural word order? |
| **Difficulty** | 3-option | Is it too easy (obvious), too hard (requires C1 knowledge), or just right for the level? |
| **Engagement** | 1-5 | Is it boring (grammar drill) or interesting (real-world scenario, cultural context)? |
| **Distractor Quality** | 1-5 | Are wrong answers plausible (common errors) or nonsense (random words)? |

**Batch validation tip**: Open all `*-quality-queue.yaml` files in your editor, fill in all at once, then finalize all modules.

#### Step 3: Finalize Quality Report

```bash
npm run quality:finalize l2-uk-en b1 50
```

**Output**: `curriculum/l2-uk-en/b1/audit/50-{slug}-quality.md`

**Report structure**:
```markdown
# Activity Quality Audit Report

**Module:** 50 | **Level:** B1

**Result:** ✅ PASS

## Quality Scores Summary

| Dimension | Score | B1 Gate | Status |
|-----------|-------|---------|--------|
| **Naturalness** | 4.2 | 3.5 | ✅ |
| **Engagement** | 3.8 | 3.0 | ✅ |
| **Distractor Quality** | 4.5 | 4.0 | ✅ |
| **Variety** | 72% | 60% | ✅ |
| **Difficulty Appropriate** | 87% | ≥80% | ✅ |

## CEFR Gate: PASS

All B1 quality thresholds met.

## Activity Details

### Activity 1: quiz - Dative Case
- **Naturalness:** 4 (Natural)
- **Difficulty:** appropriate
- **Engagement:** 3 (Functional)
- **Distractor Quality:** 4 (Plausible)
- **Notes:** Good case contrast, consider more engaging context

[... details for all activities ...]

## Recommendations

- 3 activities scored 3/5 for engagement - consider adding cultural/real-world context
- All distractors plausible - excellent pedagogical design
```

#### Step 4: View in Audit

The quality report automatically appears in audit output:

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/50-*.md
```

**Audit output**:
```
## Gates
- Activity_quality ✅ Quality gates: All passed
```

Or if failed:
```
- Activity_quality ⚠️ Quality gates: 2 failed (see report)
```

**CEFR Quality Gates**:

| Level | Min Naturalness | Min Variety | Min Distractors | Max Inappropriate |
|-------|-----------------|-------------|-----------------|-------------------|
| **B1** | 3.5 | 60% | 4.0 | ≤20% |
| **B2** | 4.0 | 65% | 4.2 | ≤15% |
| **C1** | 4.5 | 70% | 4.5 | ≤10% |
| **C2** | 4.8 | 75% | 5.0 | ≤5% |

**Note**: This is an **informational gate** (INFO) - it doesn't block audit pass/fail, but provides supplementary quality feedback.

**Documentation**: `docs/SCRIPTS.md` - Activity Quality Validation section

---

## Pipeline Generation

After module passes audit and all optional validations:

### Full Pipeline (Recommended)

```bash
npm run pipeline l2-uk-en b1 50
```

**What it does**:
1. **Lint**: Check markdown format compliance
2. **Generate MDX**: Create Docusaurus lesson files
3. **Validate MDX**: Ensure no content loss during generation
4. ~~**Generate JSON**~~: (Vibe app on hold)
5. **Validate HTML**: Browser rendering check (requires dev server)

**Output**:
- `docusaurus/docs/b1/module-50.mdx` (web lesson)
- ~~`output/json/l2-uk-en/b1/module-50.json`~~ (Vibe app on hold)

### Individual Steps

If you need to run steps separately:

```bash
# Generate MDX for Docusaurus
npm run generate l2-uk-en b1 50

# Generate JSON for Vibe (SKIP - project on hold)
# npm run generate:json l2-uk-en b1 50

# Validate MDX integrity
npm run validate:mdx l2-uk-en b1 50

# Validate HTML rendering (requires dev server running)
npm run validate:html l2-uk-en b1 50
```

### HTML Validation

HTML validation requires Docusaurus dev server:

**Terminal 1** (start dev server):
```bash
cd docusaurus
npm start
# Wait for "webpack compiled" message
```

**Terminal 2** (run validation):
```bash
npm run validate:html l2-uk-en b1 50
```

**What it checks**:
- Page loads without crash
- All activities render
- No console errors
- Interactive components functional

---

## Troubleshooting

### Audit Failures

**Problem**: Audit shows FAIL with multiple violations.

**Solution**:
1. Count violations by category
2. If >3 violations in one section → Rebuild that section (re-run earlier stage)
3. If >10 total violations → Rebuild from Stage 1
4. If ≤3 violations → Fix individually

**Common violations**:

| Violation | Cause | Fix |
|-----------|-------|-----|
| `VOCAB_PLAN_MISSING` | Vocabulary doesn't match plan | Add missing words from plan |
| `VOCAB_PLAN_EXTRA` | Vocabulary has words not in plan | Remove extra words |
| `LINT_QUOTE_STYLE` | Wrong quote style | Use «...» instead of "..." |
| `YAML_SCHEMA_VIOLATION` | Activity YAML invalid | Fix activity format (see `docs/ACTIVITY-YAML-REFERENCE.md`) |
| `COMPLEXITY_WORD_COUNT` | Sentence too short/long | Adjust fill-in/unjumble word count |
| `IMMERSION_PERCENTAGE` | Wrong UK/EN ratio | Adjust content (100% for B1+ M06+) |

---

### Grammar Validation Issues

**Problem**: Grammar validation reports Russianisms/calques.

**Solution**:
1. Check trusted sources (Slovnyk.ua, Grinchenko)
2. Apply corrections from validation report
3. If pedagogically intentional (teaching contrast), document in module
4. Re-run validation to verify

**Common false positives**:
- Pedagogical examples showing wrong forms (e.g., error-correction activities)
- Transliteration in A1 modules (expected)
- English in vocabulary table translations (expected)

**How to handle**:
- Add comment: `<!-- Pedagogical exception: teaching Russianisms -->`
- Or exclude line from validation: `<!-- grammar-validate: ignore -->`

---

### Content Quality Review Issues

**Problem**: Content quality score <7/10.

**Solution**:
1. Focus on sections with lowest scores (≤5 = critical)
2. Apply specific recommendations from report
3. Add missing elements:
   - Examples (if <18 for B1)
   - Engagement boxes (if <3 for B1)
   - Cultural context (if generic)
   - Dialogues (if <3 for B1)

**Score interpretation**:
- 9-10: Excellent (no changes needed)
- 7-8: Good (minor improvements)
- 5-6: Adequate (needs work)
- 3-4: Poor (major revision)
- 0-2: Fail (rebuild section)

---

### Activity Quality Issues

**Problem**: Activity quality gates FAIL.

**Solution**:
1. Check failed gates in report
2. Focus on lowest-scoring activities
3. Common fixes:

| Failed Gate | Typical Cause | Fix |
|-------------|---------------|-----|
| Naturalness <3.5 | Robotic, literal translations | Rewrite with natural Ukrainian phrasing |
| Variety <60% | Mechanical sentence patterns | Diversify sentence structures |
| Distractors <4.0 | Nonsense options | Create plausible wrong answers (common errors) |
| Difficulty >20% inappropriate | Too easy or too hard | Adjust complexity to match CEFR level |
| Engagement <3.0 | Boring drills | Add cultural context, real-world scenarios |

**Batch fixes**: If many activities fail, consider regenerating entire Activities section (re-run Stage 3).

---

### Pipeline Generation Errors

**Problem**: MDX generation fails.

**Causes**:
- Invalid markdown syntax
- Broken activity format
- Missing sections

**Solution**:
1. Run audit first (catches most format errors)
2. Check error message for specific line
3. Fix markdown syntax
4. Re-run pipeline

**Problem**: HTML validation fails.

**Causes**:
- Dev server not running
- Port conflict (default 3000)
- Module not generated yet

**Solution**:
```bash
# Check dev server
cd docusaurus && pnpm start

# If port conflict, use different port
PORT=3001 pnpm start

# Regenerate module first
npm run generate l2-uk-en b1 50

# Then validate
npm run validate:html l2-uk-en b1 50
```

---

## Summary Checklist

Use this checklist for every B1+ module:

### Stage 1: Skeleton

- [ ] Read level quick-ref (`claude_extensions/quick-ref/{level}.md`)
- [ ] Read curriculum plan section for this module
- [ ] Run `/module-stage-1 {level} {num}`
- [ ] Verify vocabulary matches plan EXACTLY
- [ ] Run audit (structure check only)

### Stage 2: Content

- [ ] Read module template (`docs/l2-uk-en/templates/{level}-{type}-module-template.md`)
- [ ] Run `/module-stage-2 {level} {num}`
- [ ] Verify word count meets level requirements
- [ ] Verify immersion percentage (100% for B1 M06+, B2, C1, C2)
- [ ] Run audit
- [ ] Optional: Run grammar validation
- [ ] Fix all violations before Stage 3

### Stage 3: Activities

- [ ] Read richness guidelines (`docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`)
- [ ] Run `/module-stage-3 {level} {num}`
- [ ] Verify activity count, types, items meet requirements
- [ ] Check answer correctness (wrong answers not marked correct)
- [ ] Run audit
- [ ] Optional: Run grammar validation
- [ ] Fix all violations before Stage 4

### Stage 4: Review & Fix

- [ ] Run `/module-stage-4 {level} {num}` (or manual audit)
- [ ] Audit: PASS (required)
- [ ] Optional: Grammar validation (recommended for B1+)
- [ ] Optional: Content quality review (recommended before release)
- [ ] Optional: Activity quality validation (for high-stakes content)
- [ ] Fix all critical violations
- [ ] Loop until audit PASS (max 3 iterations)

### Pipeline Generation

- [ ] Run `npm run pipeline l2-uk-en {level} {num}`
- [ ] MDX generated successfully
- [ ] JSON generated successfully
- [ ] MDX validation PASS
- [ ] HTML validation PASS (if dev server running)

### Final Verification

- [ ] Open in Docusaurus (http://localhost:3000/learn-ukrainian/{level}/module-{num})
- [ ] Test all activities (interactive, correct answers)
- [ ] Check vocabulary table (6 columns, correct data)
- [ ] Verify immersion (Ukrainian-only content for B1 M06+/B2/C1/C2)
- [ ] Check for Russianisms, calques (native speaker review if possible)

---

## Related Documentation

- **ARCHITECTURE.md** - System architecture overview
- **SCRIPTS.md** - Complete scripts reference
- **MODULE-AUDIT-GUIDE.md** - Legacy audit guide (outdated, use this instead)
- **STAGED-MODULE-CREATION.md** - Staged workflow overview
- **CONTENT-QUALITY-AUDIT.md** - Content quality review system
- **MODULE-RICHNESS-GUIDELINES-v2.md** - Quality standards and targets
- **MARKDOWN-FORMAT.md** - Markdown syntax specification
- **ACTIVITY-YAML-REFERENCE.md** - Activity format reference

---

**Last Updated**: January 8, 2026
**Applies To**: B1, B2, C1, C2 modules (100% immersed Ukrainian)
