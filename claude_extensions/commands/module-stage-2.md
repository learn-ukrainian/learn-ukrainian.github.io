# Module Stage 2: Content

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

Parse arguments: $ARGUMENTS

### Step 1: Read Stage Instructions

Read: `claude_extensions/stages/stage-2-content.md`

### Step 2: Load Existing Module

Read the module file created in Stage 1:
`curriculum/l2-uk-en/{level}/{number}-*.md`

If file doesn't exist or has no skeleton, STOP and report: "Run Stage 1 first."

### Step 3: Determine Targets

From the level, identify:
- Word count target
- Immersion percentage
- Example sentence minimum
- Engagement box minimum
- Mini-dialogue minimum

### Step 4: Write Content

**Follow the template structure** from Stage 1 (Step 2b).

**Use the appropriate architect skill** for focus-area guidance:

| Module Type | Skill |
|-------------|-------|
| Grammar (B1-B2) | `grammar-module-architect` |
| Vocabulary (B1) | `vocab-module-architect` |
| Cultural (B1-C1) | `cultural-module-architect` |
| History/Biography (B2-C1) | `history-module-architect` |
| Integration (B1-B2) | `integration-module-architect` |
| Checkpoint (All) | `checkpoint` |
| Literature (LIT) | `literature-module-architect` |

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

### Step 5: Verify

- [ ] Word count meets target
- [ ] Example sentences meet minimum
- [ ] Engagement boxes meet minimum
- [ ] Mini-dialogues present
- [ ] No vocabulary violations
- [ ] Specific Ukrainian locations used
- [ ] Immersion % appropriate
- [ ] **Ukrainian grammar validated** (see below)

**Ukrainian Grammar Validation (MANDATORY):**

Validate ALL Ukrainian text against these sources:
- ✅ **Словник.UA** (slovnyk.ua) - standard spelling
- ✅ **Словарь Грінченка** - authentic Ukrainian forms
- ✅ **Антоненко-Давидович "Як ми говоримо"** - Russianisms guide
- ❌ **NOT TRUSTED:** Google Translate, Russian-Ukrainian dictionaries

**Auto-fail Russianisms:**
| ❌ Wrong | ✅ Correct |
|----------|-----------|
| кушать | їсти |
| да | так |
| кто | хто |
| нету | немає |
| приймати участь | брати участь |
| самий кращий | найкращий |
| слідуючий | наступний |

**Auto-fail Calques:**
| ❌ Wrong | ✅ Correct |
|----------|-----------|
| робити сенс | мати сенс |
| брати місце | відбуватися |

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
