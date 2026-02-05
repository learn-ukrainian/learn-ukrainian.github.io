# Current Project Status

**Last Updated**: February 1, 2026
**Session**: Productivity Improvements & B1 Module Quality

---

## 🚧 Current Work (February 1, 2026)

### Productivity Enhancement Initiative

**Status**: Phase 2 Complete, Phase 3-4 In Progress
- ✅ Implementing Claude Code workflow optimizations (Boris Cherny methodology)
- ✅ Two-tier review system created (quick + deep)
- ✅ Learning enhancement tools added
- ✅ Terminal environment documented (Ghostty)
- 🚧 Interview system protocol (next)

**Recent Improvements**:
- `scripts/audit_module.sh` - Wrapper that auto-saves audit logs
- `review-content-quick.md` - Fast pre-check filter (3-5 min, catches obvious issues)
- `review-content-deep-optimized.md` - Workflow optimization guide (35% time savings)
- `explain-decision.md` - Learning tool for curriculum design rationale
- `interview.md` - Systematic specification through 40-60 questions
- `docs/DEVELOPER-GUIDE.md` - **NEW**: Human developer guide (tools, workflows, best practices)
- Enhanced prompting patterns in CLAUDE.md (8 patterns)
- Bug fix protocol in CLAUDE.md (efficient issue reporting)
- Ghostty terminal setup documentation

**Task Tracking**: Using Claude Code task system for systematic implementation
- Phase 1 (Documentation): ✅ Complete (3/3 tasks)
- Phase 2 (Learning & Enhancement): ✅ Complete (2/2 tasks)
- Phase 3 (Interview System): 🚧 Next (2 tasks)
- Phase 4 (Status Update): 🚧 In Progress (1 task)

---

## 🚧 B1 Level: Module Quality Improvement

### B1 Level: Module Quality Improvement

**Current Status**: 23/92 modules passing (25%)
- ✅ Modules 89-92 completed (Communication Channels, Presentations, Feedback/Negotiation, Final Exam)
- ✅ Recent content updates: M90, M61, M71, M86
- 🚧 69 modules failing (primarily outline compliance + word count issues)

**Recent Achievements**:
- B1 reduced from 99 → 92 modules (removed padding)
- M90 "Presentations & Visuals" created with CEFR mapping
- M89-92 created and passing audits
- Score improvement: 8.45/10

**Next Priority**: Fix failing B1 modules
- Primary issues: Outline compliance errors (missing subsections)
- Word count shortfalls (most modules < 3000 words target)
- Activities missing for many modules

---

## 🔧 Python Environment Update

**Major Change**: Migrated from Homebrew Python to pyenv

**Current Setup**:
- Python 3.12.8 via pyenv
- Compiled with `--enable-loadable-sqlite-extensions`
- venv created from pyenv Python
- `.python-version` file pins project to 3.12.8

**Why**: Required for SQLite extension support (future use)

**Critical Rule**: Always use `.venv/bin/python`, never system `python3`

---

## 🛠️ Workflow Improvements (February 2026)

### Quality Review System

**Two-Tier Approach**: Strategic use of review depth based on resources

**Quick Review** (`review-content-quick.md`):
- **Model**: Sonnet (cost-effective)
- **Time**: 3-5 minutes per module
- **Purpose**: Pre-check filter for obvious issues
- **Catches**: Duplication, AI patterns, Russianisms, grammar errors, activity errors
- **When**: During content generation, before committing
- **Output**: `curriculum/l2-uk-en/{level}/audit/{slug}-quick-review.md`

**Deep Review** (`review-content-v4.md` + optimization guide):
- **Model**: Opus (comprehensive quality validation)
- **Time**: 20-25 minutes (optimized from 30-40 minutes)
- **Purpose**: Final quality validation before release
- **Validates**: All 12 dimensions, exhaustive Ukrainian verification
- **When**: Before publication, when level complete
- **Optimizations**: Batch operations, parallel loading, systematic workflow

**Strategy**: Quick review now (finish A1-C1 content), deep review before release

### Audit Automation

**audit_module.sh** (NEW):
```bash
# Auto-saves logs to curriculum/l2-uk-en/{level}/audit/{slug}-audit.log
scripts/audit_module.sh curriculum/l2-uk-en/b1/09-aspect-future.md
```

**Benefits**:
- No manual `tee` commands needed
- Preserves full audit output for debugging
- Claude can reference audit logs for fixes
- Consistent log naming convention

### Learning Tools

**explain-decision.md** (`/explain-decision` skill):
- Explains curriculum design rationale
- Pedagogical reasoning for decisions
- CEFR alignment justification
- Trade-offs and alternatives considered
- **Purpose**: Learn curriculum design, not just execute tasks

**Examples**:
- `/explain-decision aspect-teaching-sequence`
- `/explain-decision module b1 9`
- `/explain-decision compare aspect-first vs motion-first`

### Terminal Environment

**Ghostty Terminal** (installed):
- GPU-accelerated rendering (smooth for long audit outputs)
- Native macOS UI with system integration
- Zero-config setup with sensible defaults
- Split windows (⌘+D) for audit + editing simultaneously
- Tab auto-naming based on commands
- Nerd fonts built-in (Starship prompts work)
- Config: `~/.config/ghostty/config` (optional)

### Documentation Enhancements

**CLAUDE.md Updates**:
- ✅ Enhanced Prompting Patterns (8 patterns for better output)
- ✅ Bug Fix Protocol (efficient issue reporting format)
- ✅ Ghostty terminal documentation
- ✅ Python environment details
- ✅ Lessons Learned section (recurring issues)

**SCRIPTS.md Updates**:
- ✅ audit_module.sh documented (recommended wrapper)
- ✅ Usage examples updated

---

## 📊 Level Status Summary

| Level | Modules | Passing | Status | Notes |
|-------|---------|---------|--------|-------|
| A1 | 44/44 | 44 | ✅ Complete | Production ready |
| A2 | 70/70 | 70 | ✅ Complete | Production ready |
| B1 | 92/92 | 23 | 🚧 25% | Quality fixes needed |
| B2 | 94/94 | TBD | 🚧 In progress | - |
| B2-HIST | 140/140 | TBD | 🚧 Content phase | - |
| C1 | 106/106 | TBD | 🚧 In progress | - |
| C1-BIO | 128/128 | TBD | 📋 Planned | - |
| C1-HIST | 135/135 | TBD | 📋 Planned | - |
| C2 | 100/100 | 0 | 📋 Planned | - |
| LIT | 30/30 | TBD | 📋 Planned | - |

**Total**: 1,009 modules planned across 10 tracks

---

## 🎯 Recent Completions

### B1 Module Restructuring ✅

**Issue #474**: B1 from 99 → 92 modules
- Removed duplicate/padding modules (M93-99)
- Redefined M94, M97 to eliminate duplication
- Updated quick-ref and level plan
- **Commits**: 79bfeb8c, c9adb0fd, b436a8ac, e9fdf890

### B1 Modules 89-92 Created ✅

**New Professional Communication Modules**:
1. M89: Communication Channels
2. M90: Presentations & Visuals
3. M91: Feedback, Negotiation & Complaints
4. M92: B1 Final Exam

**Features**:
- All passing audits
- CEFR B1.2 mapping
- Comprehensive activity sets
- **Commits**: 76822820, f2a402e5, 985aa795

### Content Updates ✅

**Updated modules**:
- M61: Professional Communication (added education vocabulary)
- M71: Emotional Intelligence (mini-checkpoint section)
- M86: Ukrainian Holidays & Festivals (mini-checkpoint section)
- M90: Added summarizing skills, CEFR mapping

**Commits**: b9b1eed2, f2a402e5, 985aa795

---

## 🐛 Issues to Address

### B1 Quality Gaps

**69 modules failing** with common patterns:

1. **Outline Compliance** (most modules):
   - Missing subsections from plan outline
   - Incomplete section development
   - Need to expand content to match plan

2. **Word Count** (most modules):
   - Target: 3000 words for core modules
   - Actual: 1500-2500 words average
   - Need substantial content expansion

3. **Activities** (some modules):
   - Missing required activity types
   - Below minimum item counts
   - Need activity generation/enrichment

4. **Checkpoints** (special cases):
   - M25, M34, M41, M51: Missing checkpoint-specific activities
   - M71, M86: Missing checkpoint-vocab/culture activities

---

## 🔄 Architecture & Workflow

### Three-Layer System

**Layer 1: Plans** (source of truth)
- `curriculum/l2-uk-en/plans/{level}/{slug}.yaml`
- Immutable module specifications
- Content outline, vocabulary, objectives

**Layer 2: Build Artifacts**
- `curriculum/l2-uk-en/{level}/{num}-{slug}.md` (content)
- `curriculum/l2-uk-en/{level}/meta/{slug}.yaml` (config)
- `curriculum/l2-uk-en/{level}/activities/{slug}.yaml`
- `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml`

**Layer 3: Status Cache**
- `curriculum/l2-uk-en/{level}/status/{slug}.json`
- Generated by `audit_module.py`
- Consumed by `generate_level_status.py`
- ~15x faster than live audits

### Status Generation

```bash
# Update single module cache
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/90-presentations-visuals.md

# Regenerate level status from cache
npm run status:b1
# or: .venv/bin/python scripts/generate_level_status.py b1

# Regenerate all level statuses
npm run status:all
```

---

## 🚀 Active Workflows

### Module Development Pipeline

**Stage 1**: Skeleton creation (from plan)
**Stage 2**: Content generation (prose)
**Stage 3**: Activities generation
**Stage 4**: Review & fix loop (until audit passes)

### Quality Gates

**Every module must pass**:
1. ✅ Outline compliance (all sections from plan)
2. ✅ Word count (≥95% of target)
3. ✅ Activities (required types + minimum counts)
4. ✅ Vocabulary (matches plan)
5. ✅ Structure (proper markdown format)

**Audit command**:
```bash
.venv/bin/python scripts/audit_module.py {path}
```

---

## 🔧 Configuration Changes

### Removed MCP Servers

**Previous**: Had MCP servers for memory-service and ukrainian-validator
**Current**: `.mcp.json` has empty `mcpServers: {}`
**Reason**: Not working with Claude Code CLI
**Alternative**: Call gemini-cli directly via Bash when needed

### Python Environment

**File**: `.python-version` → `3.12.8`
**Setup**:
```bash
# Python installed via pyenv with SQLite extensions
PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions" \
LDFLAGS="-L/opt/homebrew/opt/sqlite/lib" \
CPPFLAGS="-I/opt/homebrew/opt/sqlite/include" \
pyenv install 3.12.8

# Venv created from pyenv Python
~/.pyenv/versions/3.12.8/bin/python -m venv .venv
```

---

## 📚 Key Documentation

**Updated files**:
- `CLAUDE.md` - Removed MCP references, added Python env notes
- `docs/B1-STATUS.md` - Auto-generated, shows 23/92 passing
- `docs/B2-HIST-STATUS.md` - Auto-generated
- `docs/CURRENT-STATUS.md` - This file

**Quick reference docs**:
- `claude_extensions/quick-ref/B1.md` - B1 level requirements
- `docs/ARCHITECTURE-PLANS.md` - Three-layer architecture
- `docs/STATUS-SYSTEM.md` - Status caching system
- `docs/MODULE-RICHNESS-GUIDELINES-v2.md` - Activity requirements

---

## 🎯 Next Tasks

### Immediate: Complete Productivity Improvements

**Phase 3 - Interview System** (Next):
- Task #12: Create generic Interview skill
- Task #13: Document Interview Protocol in CLAUDE.md
- **Purpose**: Systematic 40+ question interviews before building
- **Benefit**: Reduce rework through upfront specification

**In Progress: Claude-Gemini Cooperation** (Task #18):
- **Plan**: `docs/CLAUDE-GEMINI-COOPERATION.md` ⭐
- **Vision**: LLM Committee System - mutual review, bidirectional communication
- **Infrastructure Created**:
  - MCP Message Broker (`.mcp/servers/message-broker/server.py`)
  - Gemini Bridge CLI (`scripts/ai_agent_bridge.py`)
- **Next**: Test message exchange, run Ukrainian test experiment (1000 sentences)
- **Phases**: Communication ✅ → Ukrainian Test → Context Packaging → Skills → Automation

### High Priority: Fix B1 Failing Modules

**Current**: 23/92 passing (25%)
**Target**: 80%+ passing

**Approach**:
1. Start with highest-value modules (aspect, motion verbs)
2. Use new Bug Fix Protocol (paste audit log + clear steps)
3. For each failing module:
   - Read plan: `curriculum/l2-uk-en/plans/b1/{slug}.yaml`
   - Identify missing sections (outline compliance)
   - Expand content to meet word targets
   - Add missing activities
   - Re-audit until passing

**Tools Available**:
- `scripts/audit_module.sh` (auto-saves logs)
- `/explain-decision` (understand design rationale)
- Bug fix protocol (efficient communication)

### Medium Priority: Complete B2-HIST

- 140 history modules in content phase
- Many need final review and activities
- Will use quick review during development
- Deep review before publication

### Lower Priority

- C1 core modules
- C1-BIO track (128 modules)
- C1-HIST track (135 modules)
- C2 core (100 modules)
- LIT track (30 modules)

---

## 💾 Recent Commits (Last 10)

```
76822820f feat(b1): create M90 Presentations & Visuals content
b9b1eed24 feat(b1): update M61, M71, M86 content to match plans
f2a402e53 feat(b1): add summarizing skills to M90, CEFR mapping doc (#474)
985aa7950 feat(b1): add education vocabulary to M61, update compliance docs (#474)
5b1c4fcfe docs(b1): update improvement plan - score now 8.45/10
e9fdf890f feat(b1): add mini-checkpoint sections to M71 and M86
1d617f1ba docs(b1): update quick-ref and level plan to 92 modules
79bfeb8c7 refactor(b1): cut from 99 to 92 modules, remove padding (#474)
c9adb0fd6 fix(b1): redefine M94 and M97 to eliminate content duplication (#474)
b436a8ac7 docs(b1): update improvement plan with Phase 1 and Phase 6 completion
```

---

## 🔗 Related Issues

- **#474** - B1 Module Restructuring (99 → 92 modules) ✅ Complete
- **#412** - Content naturalness detection (planned)
- **#402** - Full Ukrainian Immersion ✅ Complete
- **#399** - Claude Code 2.1 Integration ✅ Complete

---

**End of Status Document**

*This document serves as memory context for AI sessions. Update after major completions.*
