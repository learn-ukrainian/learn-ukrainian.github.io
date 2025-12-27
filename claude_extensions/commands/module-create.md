# Module Create (Full Pipeline)

> **⚠️ ALWAYS use `.venv/bin/python` - NEVER use `python3` or `python` directly!**

Create a new module OR migrate an existing module to YAML format.

## Usage

```
/module-create [LEVEL] [MODULE_NUM]
/module-create [LEVEL] [START]-[END]   # Batch mode
```

## Arguments

- `$ARGUMENTS` - Level and module number (e.g., `a1 15` or `b2 45`)
- Batch ranges supported: `b1 2-5` creates modules 2, 3, 4, 5

---

## Batch Mode (Multiple Modules)

**When arguments contain a range (e.g., `b1 2-5`):**

Use the **subagent pattern** to process each module with fresh context:

```
For each module in range:
  1. Spawn Task agent with subagent_type="general-purpose"
  2. Agent prompt: "Run /module-create {level} {module_num} - create single module"
  3. Wait for agent completion
  4. Log result (PASS/FAIL)
  5. Continue to next module (fresh context)
```

**Why subagents?**
- Each module gets full context capacity
- Failure in one doesn't pollute the next
- Prevents context exhaustion on large batches

**Example batch execution:**
```
/module-create b1 2-5

→ Task agent: /module-create b1 2 → ✅ PASS
→ Task agent: /module-create b1 3 → ✅ PASS
→ Task agent: /module-create b1 4 → ❌ FAIL (audit)
→ Task agent: /module-create b1 5 → ✅ PASS

Summary: 3/4 passed, 1 failed (b1/4)
```

---

## Single Module Mode

Parse arguments: $ARGUMENTS

### Step 0: Check if Module Exists

```bash
ls curriculum/l2-uk-en/{LEVEL}/*{MODULE_NUM}*.md 2>/dev/null
```

**If module EXISTS (migration mode):**
- Skip stages 1-2 (content already exists)
- Run stage 3: Create `.activities.yaml` from existing embedded activities
- Run stage 4: Audit + pipeline

**If module DOES NOT exist (creation mode):**
- Run all stages 1-4

---

## Migration Mode (Module Exists)

### Stage 3: Recreate Activities in YAML

**Drop old activities and recreate from scratch** (proven 50% faster than conversion):

1. **Delete embedded activities** from `.md` file (keep only content sections)
2. **Read module content** to understand topic and grammar focus
3. **Study 1-2 similar modules** for YAML patterns (see `stage-3-activities.md` reference table)
4. **Create `.activities.yaml` directly** with 12+ activities (B1)
5. **DO NOT** use md_to_yaml.py converter - write YAML directly

**Why recreate vs convert?**
- ✅ **50% faster** - M22 took 8 minutes vs 36 minutes average for MD conversion
- ✅ **Zero format errors** - Direct control over structure
- ✅ **Better quality** - Fresh activities with correct complexity

### Stage 4: Review & Fix

1. Run audit: `.venv/bin/python scripts/audit_module.py ...`
2. Fix violations until PASS
3. Run pipeline: `npm run pipeline l2-uk-en {LEVEL} {MODULE_NUM}`
4. Generate JSON: `npm run generate:json l2-uk-en {LEVEL} {MODULE_NUM}`

---

## Creation Mode (New Module)

```
Stage 1 → Stage 2 → Stage 3 → Stage 4 (review/fix loop) → OUTPUT
```

### Pipeline

**Stage 1: Skeleton**
1. Read curriculum plan
2. **Read appropriate template** (see template selection in `/module-stage-1`)
3. Extract module section (title, vocabulary, grammar scope)
4. Read `docs/MARKDOWN-FORMAT.md` for strict syntax requirements
5. Create file with frontmatter + headers + vocabulary table **following template structure**

**Stage 2: Content**
1. Load skeleton from Stage 1
2. Write rich instructional content
3. Verify word count, examples, engagement boxes

**Stage 3: Activities**
1. Load content from Stage 2
2. Generate activities using vocabulary
3. Verify counts, types, syntax

**Stage 4: Review & Fix**
1. Run audit: `.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{LEVEL}/module-{MODULE_NUM}.md`
2. Fix violations until PASS
3. Run content review: `/review-content l2-uk-en {LEVEL} {MODULE_NUM}`
4. Fix quality issues until PASS (Score: 5/5)
5. Run pipeline: `npm run pipeline l2-uk-en {LEVEL} {MODULE_NUM}`
6. Generate JSON: `npm run generate:json l2-uk-en {LEVEL} {MODULE_NUM}`

### Quick Reference (Read First)

1. **Quick-ref for level:** `claude_extensions/quick-ref/{level}.md` (~100 lines)
   - Frontmatter template, targets, activity mix, pre-flight checklist
2. **Philosophy guide:** `claude_extensions/quick-ref/philosophy.md` (~150 lines)
   - Soul standard, Truth standard, cultural specificity, linguistic purity

### Module Architect Skills (Use for Focus-Area Guidance)

Select the appropriate architect skill based on module type:

| Module Type | Skill | When to Use |
|-------------|-------|-------------|
| Grammar (B1-B2) | `grammar-module-architect` | Aspect, motion verbs, participles, passive voice |
| Vocabulary (B1) | `vocab-module-architect` | Abstract concepts, collocations, synonymy |
| Cultural (B1-C1) | `cultural-module-architect` | Regions, music, cinema, folk culture |
| History/Biography (B2-C1) | `history-module-architect` | Ukrainian history, historical figures |
| Integration (B1-B2) | `integration-module-architect` | Level-end review and consolidation |
| Checkpoint (All) | `checkpoint` | Phase-end assessment modules |
| Literature (LIT) | `literature-module-architect` | Post-C1 Ukrainian literature track |

These skills provide focus-area pedagogical guidance beyond the template structure.

### Curriculum Plan (Extract Only Your Module)

**DO NOT read the entire curriculum plan file.** Use grep to extract only your module:

```bash
grep -A 50 "Module {NUM}:" docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md
```

This gives you ONLY the vocabulary and grammar scope for your specific module (~50 lines).

### Pre-flight Checklist

Before writing, confirm from quick-ref:
- [ ] All frontmatter fields ready (copy template)
- [ ] Vocabulary list from curriculum plan
- [ ] Activity count + types match level requirements
- [ ] Immersion target known
- [ ] No duplicate explanations planned
- [ ] External Resources (YouTube/Blogs) planned?
- [ ] **If checkpoint:** Read `docs/l2-uk-en/CHECKPOINT-DESIGN-GUIDE.md`

### ⚠️ CRITICAL CONSTRAINTS (Apply DURING Writing, Not After)

**Quiz Prompts:**
- Each quiz question prompt MUST be **12-20 words** (audit fails below 12)
- Count words BEFORE writing each question

**100% Ukrainian Immersion (B1+):**
- **FORBIDDEN:** English annotations in parentheses e.g. `(Before)`, `(While...)`, `(As soon as)`
- **ALLOWED:** English ONLY in vocabulary table translations
- All grammar explanations must be in Ukrainian with Ukrainian examples

**Ukrainian Grammar Validation (MANDATORY):**

Validate ALL Ukrainian text against these sources:
- ✅ **Словник.UA** (slovnyk.ua) - standard spelling
- ✅ **Словарь Грінченка** - authentic Ukrainian forms
- ✅ **Антоненко-Давидович "Як ми говоримо"** - Russianisms guide
- ❌ **NOT TRUSTED:** Google Translate, Russian-Ukrainian dictionaries

**Auto-fail Russianisms (fix immediately):**
| ❌ Wrong | ✅ Correct |
|----------|-----------|
| кушать | їсти |
| да | так |
| кто | хто |
| нету | немає |
| пока | поки |
| сейчас | зараз |
| приймати участь | брати участь |
| самий кращий | найкращий |
| слідуючий | наступний |

**Auto-fail Calques (English loan translations):**
| ❌ Wrong | ✅ Correct |
|----------|-----------|
| робити сенс | мати сенс |
| брати місце | відбуватися |
| в кінці дня | врешті-решт |

### Stage Instructions (if needed)

Only read stage docs for complex cases:
- `claude_extensions/stages/stage-1-skeleton.md`
- `claude_extensions/stages/stage-2-content.md`
- `claude_extensions/stages/stage-3-activities.md`
- `claude_extensions/stages/stage-4-review-fix.md`

### Output

On completion:
- Module file: `curriculum/l2-uk-en/{level}/{num}-{slug}.md`
- MDX: `docusaurus/docs/{level}/module-{num}.mdx`
- JSON: `output/json/l2-uk-en/{level}/module-{num}.json`

Status: APPROVED (pipeline passes) or NEEDS MANUAL REVIEW

**Pipeline validates:**
- Lint (MD format)
- Generate (MD → MDX)
- Validate MDX (no content loss)
- Validate HTML (browser rendering)

**Note:** HTML validation requires `cd docusaurus && npm start` running

## Individual Stage Commands

For manual control, use individual stage commands:

```
/module-stage-1 [LEVEL] [MODULE]   # Create skeleton
/module-stage-2 [LEVEL] [MODULE]   # Fill content
/module-stage-3 [LEVEL] [MODULE]   # Add activities
/module-stage-4 [LEVEL] [MODULE]   # Review & fix loop
```

## Examples

```
/module-create a1 15      # Create A1 module 15 (full pipeline)
/module-create b2 45      # Create B2 module 45 (full pipeline)

# Or step by step:
/module-stage-1 a1 15     # Create skeleton
/module-stage-2 a1 15     # Add content
/module-stage-3 a1 15     # Add activities
/module-stage-4 a1 15     # Review and fix until pass
```
