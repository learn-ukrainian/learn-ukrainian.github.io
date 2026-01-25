# CLAUDE.md - Project Instructions

> **⚠️ READ FIRST: `claude_extensions/NON-NEGOTIABLE-RULES.md`**
>
> **These rules are ABSOLUTE. No negotiation. No exceptions.**
> - Word count targets: MUST meet them
> - Audit gates: ALL must pass (✅)
> - Section targets: MUST hit each one
> - Stage 4 loop: Work until COMPLETE
> - Quality standards: NO shortcuts
>
> **If you cannot commit to these rules, STOP NOW.**

> **Status**: See `docs/CURRENT-STATUS.md` for completion status and current focus.

## Critical Rules

<critical>

### 1. Work in `claude_extensions/` First
**NEVER** edit `.claude/`, `.agent/`, `.gemini/` directly.
- Edit in `claude_extensions/` (commands, skills, stages, quick-ref)
- Run `npm run claude:deploy` to sync
- Structure: `commands/` (skills), `skills/` (architect prompts), `stages/` (workflow docs)

### 2. Use Python venv
**ALWAYS** use `.venv/bin/python`, **NEVER** `python3` or `python` directly.
```bash
.venv/bin/python scripts/audit_module.py {path}  # Correct
python3 scripts/audit_module.py {path}           # WRONG - missing deps
```

### 3. Use Modern CLI Tools
Prefer fast tools: `rg` (grep), `fd` (find), `bat` (cat), `sd` (sed), `yq` (yaml), `jq` (json).

### 4. Fix Source, Not Symptoms
When issues occur: fix documentation/tools **first**, then validate with manual fix.
- Ask: What process/tool caused this? How to prevent recurrence?

### 5. Language Settings
- **English**: All technical work (git, scripts, errors, planning)
- **Ukrainian**: Curriculum content only (lessons, activities, vocabulary)

### 6. External LLM Access
**No direct API keys** - use MCP server for Gemini access.
- gemini-cli installed with Google AI Pro subscription
- MCP server: `.mcp/servers/ukrainian-validator/server.py`
- Provides `validate_ukrainian` tool for grammar checks
- Python scripts can call same MCP server via `mcp` client library
- See issue #412 for content naturalness detection extension

</critical>

---

## Module Workflow

**EVERY time you write a module:**

1. **READ** `claude_extensions/quick-ref/{LEVEL}.md` - Level requirements
2. **READ** `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md` - Vocabulary and grammar scope
3. **READ** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Activity counts, complexity
4. **READ** template from `docs/l2-uk-en/templates/`
5. **WRITE** using ONLY vocabulary from the plan
6. **VERIFY** against template checklist

**NEVER:**
- Write from memory
- Add vocabulary not in the plan
- Skip reading templates
- Create activities below item counts

---

## Quick Commands

```bash
# Audit module
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{file}.md

# Full pipeline (lint → generate → validate)
npm run pipeline l2-uk-en {level} {module_num}

# Deploy skill changes
npm run claude:deploy

# Vocabulary rebuild
npm run vocab:rebuild
```

See `docs/SCRIPTS.md` for complete reference.

---

## Project Structure

```
curriculum/l2-uk-en/{level}/
├── {num}-{slug}.md           # Module prose (no activities)
├── activities/{slug}.yaml    # Activities in YAML (root = list)
├── vocabulary/{slug}.yaml    # Vocabulary data
└── audit/                    # Review reports
```

**Levels**: A1 (34), A2 (57), B1 (91), B2 (145), C1 (202), C2 (100)

---

## Activity YAML Rules

<critical>

### Root Structure
YAML files must be a **bare list at root**, NOT wrapped in `activities:`:
```yaml
# CORRECT - bare list
- type: quiz
  title: ...

# WRONG - dictionary wrapper
activities:
  - type: quiz
```

### Mark-the-Words Format
Use `text` (no asterisks) + `answers` array:
```yaml
- type: mark-the-words
  text: Гарний день приніс радість у серце.
  answers:
    - день
    - радість
    - серце
```

See `docs/ACTIVITY-YAML-REFERENCE.md` for all activity types.

</critical>

---

## Documentation Index

| Topic | Location |
|-------|----------|
| **Current status** | `docs/CURRENT-STATUS.md` |
| **YAML activities** | `docs/ACTIVITY-YAML-REFERENCE.md` |
| **Quality standards** | `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` |
| **Subsection flexibility** | `docs/SUBSECTION-FLEXIBILITY-GUIDE.md` ⭐ |
| **Markdown format** | `docs/MARKDOWN-FORMAT.md` |
| **Scripts reference** | `docs/SCRIPTS.md` |
| **Architecture** | `docs/ARCHITECTURE.md` |
| **Grammar validation** | `scripts/audit/ukrainian_grammar_validator_prompt.md` |
| **Level quick-refs** | `claude_extensions/quick-ref/{level}.md` |
| **Stage workflows** | `claude_extensions/stages/stage-{1-4}-*.md` |

---

## Historical Context

Previous failures (Dec 2024) stemmed from ignoring documented workflows. Key lessons:
- **Read before writing** - Never generate from memory
- **Follow vocabulary exactly** - No "helpful additions"
- **Run validation** - Don't skip audit steps
- **Fix source first** - Update docs/tools before manual fixes

**Following instructions > Being "helpful"**
