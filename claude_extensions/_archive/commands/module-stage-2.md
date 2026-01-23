# Module Stage 2: Content

> **⚠️ READ FIRST: `claude_extensions/NON-NEGOTIABLE-RULES.md`**

Fill the skeleton with rich instructional content.

## Usage

```
/module-stage-2 [LEVEL] [MODULE_NUM]
/module-stage-2 [LEVEL] [START]-[END]   # Batch mode
```

## Arguments

- `$ARGUMENTS` - Level and module number (e.g., `a1 15` or `b2 45`)
- Batch ranges supported: `b1 2-5` processes modules 2, 3, 4, 5

---

## Batch Mode (Multiple Modules)

**When arguments contain a range (e.g., `b1 2-5`):**

Use the **subagent pattern** to process each module with fresh context:

```
For each module in range:
  1. Spawn Task agent with subagent_type="general-purpose"
  2. Agent prompt: "Run /module-stage-2 {level} {module_num}"
  3. Wait for agent completion
  4. Log result (PASS/FAIL)
  5. Continue to next module (fresh context)
```

---

## Single Module Mode

## Instructions

### Step 0: Context Priming (MANDATORY)

1. **Read Stage Instructions:** `claude_extensions/stages/stage-2-content.md`
2. **Read Appropriate Template:** (See list in `stage-2-content.md`)
3. **Load Architect Skill:** Identify and read the required architect skill from the table in Step 4.
4. **Task Boundary Acknowledgement:** State in your task boundary: "I have read the targets for word count, immersion, and pedagogy and will apply them sequentially."

### Step 1: Read Stage Instructions

Read: `claude_extensions/stages/stage-2-content.md`

### Step 2: Load Existing Module

Read the module file created in Stage 1:

**For core levels (a1, a2, b1, b2, c1, c2):**
`curriculum/l2-uk-en/{level}/{number:02d}-*.md`

**For track levels (b2-hist, c1-bio, lit, b2-pro, c1-pro):**
Look up slug from manifest: `yq ".levels.\"{level}\".modules[{number-1}]" curriculum/l2-uk-en/curriculum.yaml`
Then: `curriculum/l2-uk-en/{level}/{slug}.md`

If file doesn't exist or has no skeleton, STOP and report: "Run Stage 1 first."

### Step 2b: Check & Hydrate Plan (Fractal Generation)

Before writing content, verify the module has a detailed `content_outline`.

1. **Run Check:**

   ```bash
   .venv/bin/python scripts/fractal/check_hydration.py --hydrate curriculum/l2-uk-en/{level}/meta/{slug}.yaml
   ```

2. **If Output says "needs hydration":**
   - **Activate Skill:** `architect`
   - **Instruction:** "Hydrate `meta/{slug}.yaml` using template `{template_path}` as identified by the script."
   - **Wait:** Confirm hydration is complete (YAML updated) before proceeding.

3. **If Output says "already hydrated":** Proceed to Step 3.

### Step 3: Load Content Outline & Determine Targets

**CRITICAL:** Read the module's meta YAML file to get section-level word targets:

1. Read `curriculum/l2-uk-en/{level}/meta/{slug}.yaml`
2. Extract the `content_outline` array
3. For EACH section in content_outline:
   - Section name (e.g., "Вступ")
   - Word target (e.g., 400)
   - Content points (guide topics to cover)

From the level, also identify:

- Overall module word count target
- Immersion percentage
- Example sentence minimum
- Engagement box minimum
- Mini-dialogue minimum

**During writing:** Generate each section to meet its word target (±10%).
Do NOT proceed to next section until current section meets its target.

### Step 4: Write Content

**Follow the template structure** from Stage 1 (Step 2b).

**Use the appropriate architect skill** for focus-area guidance:

| Module Type               | Skill                          |
| ------------------------- | ------------------------------ |
| Grammar (B1-B2)           | `grammar-module-architect`     |
| Vocabulary (B1)           | `vocab-module-architect`       |
| Cultural (B1-C1)          | `cultural-module-architect`    |
| History/Biography (B2-C1) | `history-module-architect`     |
| Integration (B1-B2)       | `integration-module-architect` |
| Checkpoint (All)          | `checkpoint`                   |
| Literature (LIT)          | `literature-module-architect`  |

Replace `[placeholder]` markers with rich content following template guidance:

1. **Warm-up/Diagnostic**: Connect to prior knowledge, leading question
2. **Presentation/Analysis**: Grammar explanation, tables, examples
3. **Cultural Insight/Deep Dive**: History, culture, engagement boxes
4. **Practice**: Pattern drills, model exercises

**CRITICAL:** Use ONLY vocabulary from:

- The module's vocabulary table
- Prior modules (cumulative)

**Template checklist:**

- [ ] All required sections from template present
- [ ] Common pitfalls from template avoided
- [ ] Structure matches template pattern

### Step 5: Verify & Manual Review (MANDATORY)

1. **Self-Check:**
   - [ ] **Section-level word counts:** Each section meets its target from content_outline (±10%)
   - [ ] **Overall word count:** Total meets module target (instructional core only)
   - [ ] Example sentences meet minimum
   - [ ] Engagement boxes meet minimum
   - [ ] Mini-dialogues present (if required)
   - [ ] Uses ONLY vocabulary from YAML + prior modules
2. **Naturalness Review:** Perform an internal linguistic review of all Ukrainian text. Follow the `Naturalness Quality Checklist` in the template.
3. **Linguistic Purity:** Verify ZERO Russian phonetic or lexical "ghost words".
4. **Generate Review File:**
   - Calculate Content Hash using project logic.
   - Manually write `curriculum/l2-uk-en/{level}/audit/{slug}-llm-review.md`.
   - Set `Status: PASS` only if you have verified the content yourself.

### Step 6: Run Audit

```bash
.venv/bin/python scripts/audit_module.py {file_path}
```

### Output

Report:

- Word count (instructional core)
- Example sentences count
- Engagement boxes count
- Immersion %
- Any violations found
- "Ready for Stage 3" or "Fix issues first"
