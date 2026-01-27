# GEMINI.md - Gemini Agent Context & Memory

## Project Overview

**Learn Ukrainian** is a language content factory generating Ukrainian language learning curricula.

- **Target**: Ukrainian for English speakers (l2-uk-en).
- **Philosophy**: "Theory-First, Content-Driven".
- **Structure**: 6 Levels (A1, A2, B1, B2, C1, C2) aligned with Ukrainian State Standard 2024.

## Gemini Memory Context

### Strategic Decisions

- **Architecture v2.0 (Plan-Build-Status)**:
  - **Plans** (Immutable): `plans/{level}/{slug}.yaml`. Defines *what* to build (outline, targets).
  - **Build** (Mutable): `meta/{slug}.yaml`, `{slug}.md`, `activities/`, `vocabulary/`. The actual content.
  - **Status** (Cached): `status/{slug}.json`. Auto-generated audit results.
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

## Work Status (Migration Completed Jan 2026)

- **Architecture Migration (Epic #465)**: ✅ **COMPLETE**. All levels migrated to V2.0 structure.
- **A1 (01-34)**: ✅ Migrated to V2.0. Status: **COMPLETE**.
- **A2 (01-57)**: ✅ Migrated to V2.0. Status: **COMPLETE**.
- **B1 (01-86)**: ✅ Migrated to V2.0. Status: **CONTENT DRAFTED**.
- **B2 (01-145)**: ✅ Migrated to V2.0. Status: **PLANNED** (Content pending).
- **C1 (01-182)**: ✅ Migrated to V2.0. Status: **PLANNED** (Content pending).
- **C2 (01-100)**: ✅ Migrated to V2.0. Status: **PLANNED**.
- **Tracks (HIST, BIO, LIT)**: ✅ Migrated to V2.0. Status: **PLANNED**.

## Critical Workflow Rules (Gemini)

0. **Plan Immutability (CRITICAL)**: Plans in `plans/` are IMMUTABLE source of truth.
   - **READ** plans to understand requirements (`content_outline`, `word_target`).
   - **NEVER** modify plan files.
   - **REPORT** if build cannot meet plan; do not lower targets yourself.
1. **Meta is Build Config**: `meta/{slug}.yaml` stores mutable build data (`naturalness`, `timestamps`), NOT planning data.
2. **Audit & Status**:
   - Run `audit_module.py` to validate content and update the JSON status cache.
   - Use `/module-status` or `/level-status` for instant status checks.
3. **Use Mandatory Templates**: Every module MUST follow the structural guide in `docs/l2-uk-en/templates/`.
4. **Read Specs First**: Always read the Plan (`plans/{level}/{slug}.yaml`) before generating.
5. **Narrative Vocabulary**: Use "Passive Vocabulary" freely in narratives; restrict "Active Vocabulary" (drills) to the target list.
6. **Strict Header Hierarchy**: `# Summary`, `# Activities` (H1), `##` (H2).
7. **Regenerate HTML**: Always regenerate HTML output immediately after fixing module markdown.
8. **Decolonization & Patriotism (MANDATORY)**: Include Myth Buster, History Bite, and celebrate Ukrainian identity. Use "Prosecutor's Voice".
9. **Issue Tracking**: Use GitHub Issues. Do not use `docs/issues/`.
10. **Workflow/Command Loading**: Load from `claude_extensions/commands/`.
11. **Virtual Environment**: Always use `.venv/bin/python`.
12. **BROKEN TOOL AVOIDANCE**: Use `run_shell_command("rg ...")` instead of `search_file_content`.
13. **Typography & JSX Safety**: ALWAYS use Ukrainian angular quotes `«...»`.
14. **Seminar Pedagogy (RFC #409)**: `c1-bio`, `b2-hist`, `lit` require `reading`, `critical-analysis`, `essay-response` activities.
16. **Definition of Done (CRITICAL)**: A module is NOT done until:
    1. `audit_module.py` passes (✅).
    2. `npm run generate` has been executed to update the website.
    3. `status/{slug}.json` is updated.
    **NEVER** stop at audit pass. ALWAYS run generation.

## File Structure Reference (V2.0)

- **Plans (Immutable)**: `curriculum/l2-uk-en/plans/{level}/{slug}.yaml`
- **Content (Mutable)**: `curriculum/l2-uk-en/{level}/{slug}.md`
- **Activities**: `curriculum/l2-uk-en/{level}/activities/{slug}.yaml`
- **Vocabulary**: `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml`
- **Build Meta**: `curriculum/l2-uk-en/{level}/meta/{slug}.yaml`
- **Status Cache**: `curriculum/l2-uk-en/{level}/status/{slug}.json`
- **Key Scripts**:
  - `scripts/audit_module.py` (Validates build against plan, writes cache)
  - `scripts/generate_level_status.py` (Reads cache, generates reports)
  - `scripts/pipeline.py` (Main generation/validation workflow)

## B2+ Module Creation Workflow (V2.0)

For B2+ levels (B2, C1, C2, Tracks), follow this EXACT workflow:

### 1. Read Immutable Plan

Read `curriculum/l2-uk-en/plans/{level}/{slug}.yaml`. This contains the `content_outline`, `objectives`, and `word_target`.

### 2. Create/Update Build Metadata

Ensure `curriculum/l2-uk-en/{level}/meta/{slug}.yaml` exists (migrated from plan or created new). It tracks `naturalness` and build status.

### 3. Create Vocabulary YAML

Create `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml` (enriched with IPA).

### 4. Create Module Content

Create `curriculum/l2-uk-en/{level}/{slug}.md`:
- Follow `content_outline` from the **Plan** exactly.
- Use B2+ history callouts: `[!history-bite]`, `[!myth-buster]`.
- End with `> [!resources]`.

### 5. Create Activities YAML

Create `curriculum/l2-uk-en/{level}/activities/{slug}.yaml`.

### 6. Run Audit (Updates Cache)

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{slug}.md
```

**All gates must pass before proceeding.**
