# Module Stage 3: Activities

Generate activities based on the module content.

## Usage

```
/module-stage-3 [LEVEL] [MODULE_NUM]
/module-stage-3 [LEVEL] [START]-[END]   # Batch mode
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
  2. Agent prompt: "Run /module-stage-3 {level} {module_num}"
  3. Wait for agent completion
  4. Log result (PASS/FAIL)
  5. Continue to next module (fresh context)
```

---

## Single Module Mode

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Stage Instructions

Read: `claude_extensions/stages/stage-3-activities.md`

### Step 2: Load Module

Read the module file:
`curriculum/l2-uk-en/{level}/{number}-*.md`

Verify content is present (not just `[placeholder]` markers).
If content incomplete, STOP and report: "Run Stage 2 first."

### Step 3: Extract Vocabulary

From the module's vocabulary table and prior modules, build the allowed word list.

### Step 4: Determine Requirements

From the level:
- Activity count minimum
- Items per activity minimum
- Required activity types
- Sequencing rules

**Use the appropriate architect skill** for activity priorities:

| Module Type | Skill | Activity Focus |
|-------------|-------|----------------|
| Grammar (B1-B2) | `grammar-module-architect` | fill-in, error-correction, cloze |
| Vocabulary (B1) | `vocab-module-architect` | match-up, group-sort, select |
| Cultural (B1-C1) | `cultural-module-architect` | quiz, true-false, cloze |
| History/Biography (B2-C1) | `history-module-architect` | comprehension, primary source analysis |
| Integration (B1-B2) | `integration-module-architect` | comprehensive review activities |
| Checkpoint (All) | `checkpoint` | 16+ skill-targeted activities |
| Literature (LIT) | `literature-module-architect` | essays, deep reading (no drills) |

### Step 5: Create Activities YAML File

**Create `.activities.yaml` file directly** (NOT embedded in `.md`):

1. **File location**: `curriculum/l2-uk-en/{level}/{number}-{slug}.activities.yaml`
2. **Study reference modules** first (see `stage-3-activities.md` reference table)
3. **Write activities in YAML format** with proper sequencing:
   - **Recognition stage**: match-up, group-sort, mark-the-words
   - **Discrimination stage**: quiz, true-false, select
   - **Controlled stage**: fill-in, cloze, error-correction
   - **Production stage**: unjumble, translate
4. **Use ONLY vocabulary** from module's table + prior modules
5. **Include required fields**: `type`, `id`, `title`, `instructions`, `items`/`groups`/`lines`/etc.

**DO NOT:**
- Embed activities in the `.md` file
- Create activities in MD format first and convert
- Use md_to_yaml.py converter

### Step 6: Verify YAML Structure

- [ ] File is valid YAML (use `npm run validate:yaml {file_path}`)
- [ ] All activities have `id`, `title`, `instructions` fields
- [ ] Cloze uses `passage` + `blanks` list (NOT inline format)
- [ ] All string values with quotes/colons are properly escaped
- [ ] Activity count meets level minimum
- [ ] Items per activity meet density requirements
- [ ] **Ukrainian grammar validated** (see below)

**Ukrainian Grammar Validation (MANDATORY for activity text):**

Validate ALL Ukrainian text in activities against these sources:
- ✅ **Словник.UA** (slovnyk.ua) - standard spelling
- ✅ **Словарь Грінченка** - authentic Ukrainian forms
- ✅ **Антоненко-Давидович "Як ми говоримо"** - Russianisms guide
- ❌ **NOT TRUSTED:** Google Translate, Russian-Ukrainian dictionaries

**Auto-fail Russianisms in activities:**
| ❌ Wrong | ✅ Correct |
|----------|-----------|
| кушать | їсти |
| да | так |
| кто | хто |
| нету | немає |
| приймати участь | брати участь |
| самий кращий | найкращий |

**Auto-fail Calques in activities:**
| ❌ Wrong | ✅ Correct |
|----------|-----------|
| робити сенс | мати сенс |
| брати місце | відбуватися |

### Step 7: Run Audit

```bash
.venv/bin/python scripts/audit_module.py {file_path}
```

### Step 8: Generate Output

```bash
npm run generate l2-uk-en {level} {module_num}
npm run generate:json l2-uk-en {level} {module_num}
```

### Output

Report:
- Activity count
- Activity types used
- Items per activity (min/max)
- Vocabulary violations (if any)
- Audit result
- "Module complete" or "Fix issues"
