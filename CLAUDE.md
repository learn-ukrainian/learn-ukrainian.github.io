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

> **Status Overview:**
> - **Queryable status**: `curriculum/l2-uk-en/status/{level}.yaml` (machine-readable)
> - **Human-readable**: `docs/{LEVEL}-STATUS.md` (e.g., `docs/B2-HIST-STATUS.md`)
> - **Update status**: `.venv/bin/python scripts/update_status.py {level|all}`
> - **Generate markdown**: `npm run status:{level}` or `npm run status:all`

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

1. **READ** `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` - Module plan (source of truth)
2. **READ** `curriculum/l2-uk-en/{level}/meta/{slug}.yaml` - Build config (pedagogy, grammar)
3. **READ** `claude_extensions/quick-ref/{LEVEL}.md` - Level requirements
4. **READ** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Activity counts, complexity
5. **WRITE** using ONLY vocabulary from the plan
6. **UPDATE** `curriculum/l2-uk-en/status/{level}.yaml` after completion

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

# Update status (after module completion)
.venv/bin/python scripts/update_status.py {level}

# Extract plans from meta (migration tool)
.venv/bin/python scripts/extract_plans.py {level}

# Full pipeline (lint → generate → validate)
npm run pipeline l2-uk-en {level} {module_num}

# Deploy skill changes
npm run claude:deploy

# Vocabulary rebuild
npm run vocab:rebuild
```

See `docs/SCRIPTS.md` for complete reference.

---

## Project Structure (Three-Layer Architecture)

```
curriculum/l2-uk-en/
├── plans/                        # LAYER 1: SOURCE OF TRUTH
│   ├── {level}.yaml              # Level plan (phases, scope)
│   └── {level}/                  # Module plans
│       └── {slug}.yaml           # What to build: objectives, outline, vocab
│
├── {level}/                      # LAYER 2: BUILD ARTIFACTS
│   ├── meta/{slug}.yaml          # How to build: pedagogy, duration, grammar
│   ├── {num}-{slug}.md           # Content prose
│   ├── activities/{slug}.yaml    # Activities (bare list at root)
│   ├── vocabulary/{slug}.yaml    # Vocabulary data
│   └── audit/                    # Review reports
│
└── status/                       # LAYER 3: TRACKING
    └── {level}.yaml              # Per-module state, timestamps
```

**Module counts**: A1 (44), A2 (70), B1 (92), B2 (94), C1 (106), C2 (100)
**Track counts**: B2-HIST (140), C1-BIO (128), LIT (30)

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
| **Module plans (source)** | `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` ⭐ |
| **Module status (queryable)** | `curriculum/l2-uk-en/status/{level}.yaml` ⭐ |
| **Level status (human)** | `docs/{LEVEL}-STATUS.md` (auto-generated) |
| **YAML activities** | `docs/ACTIVITY-YAML-REFERENCE.md` |
| **Quality standards** | `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` |
| **Subsection flexibility** | `docs/SUBSECTION-FLEXIBILITY-GUIDE.md` |
| **Markdown format** | `docs/MARKDOWN-FORMAT.md` |
| **Scripts reference** | `docs/SCRIPTS.md` |
| **Architecture** | `docs/ARCHITECTURE.md` |
| **Plans architecture** | `docs/ARCHITECTURE-PLANS.md` |
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
