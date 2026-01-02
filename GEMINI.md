# GEMINI.md - Gemini Agent Context & Memory

## Project Overview

**Learn Ukrainian** is a language content factory generating Ukrainian language learning curricula.

- **Target**: Ukrainian for English speakers (l2-uk-en).
- **Philosophy**: "Theory-First, Content-Driven".
- **Structure**: 6 Levels (A1, A2, B1, B2, C1, C2) aligned with Ukrainian State Standard 2024.

## Gemini Memory Context

### Strategic Decisions

- **Pedagogy**:
  - **A1-A2**: PPP (Present-Practice-Produce). Focus on clarity and building blocks.
  - **B1+ Grammar**: TTT (Test-Teach-Test). Guided discovery from context.
  - **B1+ Vocabulary/History**: **Narrative Arcs**. Vocabulary embedded in compelling stories (Content-Based Instruction).
- **Richness**:
  - "Content is King". Long, authentic texts are the primary driver of learning from B2+.
  - **Audio**: Mandatory for all new vocabulary and key examples.
  - **Phonetics**: IPA for all new vocabulary.
  - **Culture**: Integration of folklore, history, and decolonization lens.
  - **Phraseology**: Proverbs and idioms integrated from B1+.
- **Production Support**:
  - **Model Answers**: Mandatory for all writing/speaking production tasks (B2+) using `> [!model-answer]`.
  - **Activity Density**: 8+ activities per module, 12+ items per activity.
  - **Graduated Immersion (A1)**: M01-M10 (Tier 1) allow 1.5 ratio; M11-M24 (Tier 2) allow 0.8; M25+ (Tier 3) strict 0.4.

### Vocabulary Targets (Verified Dec 2025)

| Level  | Modules | Module Target | Cumulative Target | Note                           |
| ------ | ------- | ------------- | ----------------- | ------------------------------ |
| **A1** | 34      | ~25 words     | ~850              | Deduplicated (Introduced Once) |
| **A2** | 57      | ~25 words     | ~1,800            | Deduplicated (Cumulative)      |
| **B1** | 86      | ~30-40 words  | ~3,300            | Narrative-driven expansion     |
| **B2** | 145     | ~24 words     | ~6,780            | Specialized domains            |
| **C1** | 182     | ~24 words     | ~10,300           | Academic/Literary              |
| **C2** | 100     | ~25 words     | ~12,280           | Native mastery                 |

### User Preferences

- **User**: Krisztian (Hungarian native).
- **Grammar Preference**: "Declension Group" (structural) approach over simple ending rules.
- **Goal**: Theory-first curriculum; Vibe app is a secondary practice tool.

## Work Status

- **A1 (01-34)**:
  - Curriculum Plan: ✅ Updated & Aligned.
  - Status: **COMPLETE**.
- **A2 (01-57)**:
  - Curriculum Plan: ✅ Updated & Aligned.
  - Status: **COMPLETE**.
- **B1 (01-86)**:
  - Curriculum Plan: ✅ Updated & Aligned (TTT/Narrative strategy).
  - Status: **CONTENT DRAFTED** (Modules 01-86 exist; in validation/review phase).
- **B2 (01-145)**:
  - Curriculum Plan: ✅ Updated & Aligned (CBI strategy).
  - Status: **PLANNED** (Major expansion Dec 2025).
- **C1 (01-182)**:
  - Curriculum Plan: ✅ Updated & Aligned (Immersion & Analysis).
  - Status: **PLANNED** (Arts & Biographies expansion Dec 2025).
- **C2 (01-100)**:
  - Curriculum Plan: ✅ Updated & Aligned (Stylistic Perfection).
  - Status: **PLANNED**.

## Critical Workflow Rules (Gemini)

0. **Use Mandatory Templates (CRITICAL)**: Every module MUST follow the structural guide in `docs/l2-uk-en/templates/` corresponding to its type (e.g., `b1-grammar-module-template.md`). The template defines the mandatory sections and layout.
1. **Read Specs First**: Always read `{LEVEL}-CURRICULUM-PLAN.md` and `MODULE-RICHNESS-GUIDELINES-v2.md` before generating.
2. **Audit Immediately**: After generating content, use `wc -w` (or equivalent logic) to verify Instructional Core word counts.
3. **Narrative Vocabulary**: Use "Passive Vocabulary" freely in narratives for richness; restrict "Active Vocabulary" (drills) to the target list.
4. **Standardized Activities**: Use Markdown types (`quiz`, `match-up`, `fill-in`) mapped from pedagogical concepts (`Production`, `Dialogue`).
5. **Strict Header Hierarchy**: Use `# Summary`, `# Activities`, `# Vocabulary` (H1) for main sections. Use `##` (H2) for content within them.
6. **Regenerate HTML**: Always regenerate HTML output immediately after fixing module markdown content to ensure fixes are live.
7. **Strict Scope Enforcement**: NEVER use grammar or vocabulary that has not been explicitly introduced in the current or previous modules. (e.g., No "Model Answers" or "Topic Sentences" in A1 unless taught).
8. **Decolonization & Patriotism (MANDATORY)**: Every module MUST include:
   - **Myth Buster box**: Debunk Russian propaganda lies (e.g., "Ukrainian is a dialect", "Lenin created Ukraine").
   - **History Bite box**: Highlight Ukrainian resistance (Ems Ukaz, Valuev Circular, Executed Renaissance).
   - **Celebrate Ukrainian identity**: Unique letters (Ї, Є, Ґ, І), distinct linguistic heritage, cultural achievements.
   - **Use "Prosecutor's Voice"**: Frame facts to actively dismantle imperial narratives.
   - **Anti-Russian propaganda**: Actively counter common lies about Ukrainian language/culture/history.
9. **Issue Tracking**: Use GitHub Issues for all task tracking. DO NOT use `docs/issues/` (folder has been deprecated and removed). Use `gh issue create` and `gh issue list`.
10. **Workflow/Command Loading**: When user types `/slash-command`, load from `claude_extensions/commands/slash-command.md` (tracked in Git). NEVER load from `.agent/workflows/` (gitignored, not source of truth).
11. **Virtual Environment**: Always run Python scripts in the virtual environment. Use `.venv/bin/python3` or `source .venv/bin/activate`. Never use system Python.
12. **BROKEN TOOL AVOIDANCE**: The `search_file_content` tool is BROKEN (internal configuration error). DO NOT USE IT. Always use `run_shell_command("rg ...")` for searching the codebase. Use flags like `-i` (ignore case) or `-F` (fixed string) as needed.

## File Structure Reference

- **Curriculum Plans**: `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`
- **Guidelines**: `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- **Module Templates**: `docs/l2-uk-en/templates/`
- **Module Content**: `curriculum/l2-uk-en/{level}/`
- **Key Scripts**:
  - `scripts/pipeline.py` (Main generation/validation workflow)
  - `scripts/audit_module.py` (Content quality & structure check)
  - `scripts/generate_mdx.py` (Converts MD to Docusaurus MDX)
- **CLI Setup**: `docs/GEMINI-CLI-SETUP.md`
- **CLI Config**: `.gemini/config.yaml`

## B2+ Module Creation Workflow (CRITICAL)

For B2+ levels (B2, C1, C2), follow this EXACT workflow:

### 1. Create Metadata Sidecar FIRST

Create `curriculum/l2-uk-en/{level}/meta/{slug}.yaml`:

```yaml
module: b2-112
title: "Друга світова: окупації"
subtitle: "WWII: Occupations"
version: "2.0"
phase: "B2.3c Trauma & Resistance"
focus: history        # CRITICAL: Must be set for history modules!
pedagogy: "CBI"
duration: 120
transliteration: none
tags:
  - history
  - wwii
grammar:
  - "Historical narrative register"
objectives:
  - "Learner understands..."
vocabulary_count: 25
slug: 112-druha-svitova-okupatsii
```

**CRITICAL**: The `focus` field MUST be set to one of:
- `history` - for history modules (M71-145 in B2)
- `biography` - for biography modules
- `grammar` - for grammar-focused modules
- `vocabulary` - for vocabulary expansion modules
- `style` - for register/style modules
- `checkpoint` - for checkpoint modules

### 2. Create Vocabulary YAML (NOT Embedded Table)

For B2+ modules, vocabulary goes in a SEPARATE YAML file:

Create `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml`:

```yaml
module: 112-druha-svitova-okupatsii
level: B2
version: '2.0'
items:
- lemma: окупація
  ipa: /okʊˈpat͡sʲija/     # Include IPA!
  translation: occupation
  pos: noun
  gender: f
```

**DO NOT add embedded `# Словник` table to the markdown for B2+ modules.**

### 3. Create Module Content

Create `curriculum/l2-uk-en/{level}/{slug}.md`:
- Start directly with `# Title` (no frontmatter needed - use sidecar)
- Use B2+ history callouts: `[!history-bite]`, `[!myth-buster]`, `[!quote]`, `[!context]`
- End with `> [!resources]` section

### 4. Create Activities YAML

Create `curriculum/l2-uk-en/{level}/activities/{slug}.yaml`

### 5. Run Audit

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{slug}.md
```

**All gates must pass before proceeding.**

## B2+ History Callout Types

Use these engagement box types for history modules:

| Callout | Purpose |
|---------|---------|
| `[!history-bite]` | Interesting historical fact |
| `[!myth-buster]` | Debunk Russian/Soviet propaganda |
| `[!quote]` | Primary source quote |
| `[!context]` | Historical context |
| `[!analysis]` | Source analysis guidance |
| `[!source]` | Primary source introduction |
| `[!legacy]` | Modern legacy/impact |
| `[!reflection]` | Reflective moment |

These are recognized by the audit system alongside standard callouts (`[!tip]`, `[!important]`, etc.).
