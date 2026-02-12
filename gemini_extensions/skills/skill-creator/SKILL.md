---
name: skill-creator
description: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Gemini CLI's capabilities with specialized knowledge, workflows, or tool integrations. Hardened for learn-ukrainian project quality standards.
---

# Skill Creator (Hardened for learn-ukrainian)

This skill provides guidance for creating effective, failure-hardened skills for the learn-ukrainian project.

## About Skills

Skills are modular, self-contained packages that extend Gemini CLI's capabilities. In this project, they MUST enforce high linguistic and pedagogical standards.

## Project-Specific Guardrails (MANDATORY)

Every new skill created for this project MUST incorporate the following "Quality Layer" instructions in its body:

### 1. Workflow Phases (Full Fidelity)
Skills MUST define a complete workflow from Phase 0 to Phase 5:
- **Phase 0: Research**: Mandatory academic source verification.
- **Phase 1: Meta**: alignment of content_outline with word targets.
- **Phase 2: Content**: Prose writing with overshoot and agency rules.
- **Phase 3: YAML**: Generation of sidecar files with strict schema rules.
- **Phase 4: Audit**: Machine validation step.
- **Phase 5: Self-Review**: Naturalness and semantic coherence check.

### 2. Output Formatting (Delimiters)
Skills MUST specify delimiter tags for pipeline compatibility:
- `===RESEARCH_START===` / `===RESEARCH_END===`
- `===CONTENT_START===` / `===CONTENT_END===`
- `===ACTIVITIES_START===` / `===ACTIVITIES_END===`
- `===VOCABULARY_START===` / `===VOCABULARY_END===`
- `===WORD_COUNTS===` (For Phase 2)

### 3. YAML Property Reference
Skills that generate YAML MUST include a property table per activity type to prevent schema violations (e.g., `tasks` array for `reading`, `rubric` fields for `essay-response`).

### 4. Linguistic Integrity
Skills MUST include the inline Russicism blacklist and "Agency Pass" rules.

### 5. Seminar Activity Rules (For Tier 3 Tracks)
For seminar-style tracks (C1+, B2-HIST, LIT), skills MUST enforce:
- **CRITICAL FORBIDDEN TYPES**: quiz, fill-in, cloze, match-up, group-sort, unjumble, error-correction, select, translate, anagram
- **ALLOWED TYPES**: Only reading, essay-response, critical-analysis, comparative-study, authorial-intent, true-false
- **Boundary**: Do NOT follow activity_hints in the plan if they contain forbidden types.

## Writing the SKILL.md Template

### Frontmatter
- `name`: hyphen-case.
- `description`: Single-line trigger context. No hardcoded word counts here.

### Body Pattern
1. **Input & File Paths**: Define absolute paths for plan/meta/research.
2. **Phase Definitions**: Detailed Phase 0-5.
3. **Property Reference**: Table of YAML fields.
4. **Verification Checklist**: Pre-submit self-audit.
5. **Escape Hatch**: `NEEDS_HELP` signal.

---
*Note: This workspace-specific skill-creator ensures consistency across all rebuild tracks.*
