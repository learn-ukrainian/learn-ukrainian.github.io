---
description: Create, review, fix, and generate A1 curriculum modules
---

# Module Creation Workflow

Use this workflow to create new curriculum modules with full quality assurance.

## Usage

Replace `{LEVEL}` and `{MODULE_NUM}` with your target values:
- **LEVEL**: `a1`, `a2`, `b1`, `b2`, `c1`, `c2`
- **MODULE_NUM**: `01`, `02`, ... `34` (padded with zero)

---

## Steps

### 1. Load the Context & Skills
Read these critical context files to prevent regression:
```
GEMINI.md
docs/MARKDOWN-FORMAT.md
docs/l2-uk-en/MODULE-SKELETON.md
docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md
claude_extensions/skills/module-architect/SKILL.md
```
*Crucial: Check GEMINI.md for the latest policies (Immersion Tiers, H1 Headers).*

### 2. Create the Module
Create the module file following the skill's workflow:
```
curriculum/l2-uk-en/{LEVEL}/module-{MODULE_NUM}.md
```

### 3. Audit the Module
Run the audit script to check for issues:
```bash
python3 scripts/audit_module.py curriculum/l2-uk-en/{LEVEL}/module-{MODULE_NUM}.md
```

### 4. Save Review Report
Save the review output to the gemini subfolder:
```
curriculum/l2-uk-en/{LEVEL}/gemini/module-{MODULE_NUM}-review.md
```

### 5. Fix Failures
If audit shows ❌ FAIL:
- Fix the issues identified in the audit
- Re-run step 3
- Repeat until audit shows ✅ PASS

### 6. Generate Output
Only after audit passes, generate HTML and JSON:
```bash
npm run generate l2-uk-en {LEVEL} {MODULE_NUM}
```

---

## Example Commands

For A1 Module 05:
```bash
# Audit
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/module-05.md

# Generate (only after PASS)
npm run generate l2-uk-en a1 5
```

## Key Reminders
- Vocabulary table must be Markdown at END of file (not YAML)
- Section headers must be lowercase: `## warm-up`
- A2+ modules must have `transliteration: none`
- 8+ activities with 12+ items each
