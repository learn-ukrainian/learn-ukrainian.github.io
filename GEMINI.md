# GEMINI.md - Gemini Agent Context & Memory

## Project Overview
**Curricula Opus** (CO) is a language content factory generating Ukrainian language learning curricula.
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

### Vocabulary Targets (Updated Dec 2025)
| Level | Module Target | Cumulative Target | Note |
|-------|---------------|-------------------|------|
| **A1** | ~25 words | ~850 | Deduplicated (Introduced Once) |
| **A2** | ~17 words | ~1,800 | Deduplicated (Cumulative) |
| **B1** | ~35 words | ~4,500 | Narrative-driven expansion |
| **B2** | ~25 words | ~7,500 | Specialized domains |
| **C1** | ~25 words | ~10,500 | Academic/Literary |
| **C2** | ~25 words | ~12,500 | Native mastery |

### User Preferences
- **User**: Krisztian (Hungarian native).
- **Grammar Preference**: "Declension Group" (structural) approach over simple ending rules.
- **Goal**: Theory-first curriculum; Vibe app is a secondary practice tool.

## Work Status
- **A1 (01-30)**:
    - Curriculum Plan: ✅ Updated & Aligned.
    - Content: Modules 01-05 regenerated in `curriculum/l2-uk-en/a1/gemini/` with full richness.
- **A2 (01-50)**:
    - Curriculum Plan: ✅ Updated & Aligned.
- **B1 (01-80)**:
    - Curriculum Plan: ✅ Updated & Aligned (TTT/Narrative strategy).
- **B2 (01-125)**:
    - Curriculum Plan: ✅ Updated & Aligned (CBI strategy).
- **C1 (01-115)**:
    - Curriculum Plan: ✅ Updated & Aligned (Immersion & Analysis).
- **C2 (01-80)**:
    - Curriculum Plan: ✅ Updated & Aligned (Stylistic Perfection).

## Critical Workflow Rules (Gemini)
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
10. **Workflow Files**: ALL workflow/command files go in `claude_extensions/` (tracked). NEVER edit `.agent/workflows/` (gitignored, changes lost).

## File Structure Reference
- **Curriculum Plans**: `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`
- **Guidelines**: `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- **Module Content**: `curriculum/l2-uk-en/{level}/`
- **Skills**: `claude_extensions/skills/module-architect/SKILL.md`
