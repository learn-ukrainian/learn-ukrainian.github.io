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

### 1. Pre-Submit Verification Checklist
Skills that generate content MUST include a self-audit checklist:
- **Fact-to-Word Density**: Aim for 8+ unique entities (dates, names, quotes) per 1000 words.
- **Semantic Nuance**: Use 5–15 hedging markers per 1000 words for C1+.
- **Agency Pass**: Ensure active decolonized framing (Ukrainian entities as Subjects).
- **Linguistic Scan**: Verify against the Russicism Blacklist.

### 2. Linguistic Integrity (The Blacklist)
Skills MUST include the inline Russicism blacklist to prevent contamination:
- під → под (pod)
- кушати → їсти
- приймати участь → брати участь
- самий кращий → найкращий
- слідуючий → наступний
- на протязі → протягом
- любий (any) → будь-який
- отвічати → відповідати
- вообще → взагалі
- получати → отримувати
- відноситися → ставитися

### 3. Structural Enforcement
- **Delimiters**: Use `===CONTENT_START===` / `===CONTENT_END===` for orchestration compatibility.
- **YAML Format**: Always enforce "Bare List at root" for activities and vocabulary.
- **Checkpoints**: Mandatory "STOP and COUNT" gates at logical intervals (e.g., 2000 words).

## Skill Creation Process

1. Understand the skill with concrete examples
2. Plan reusable skill contents (scripts, references, assets)
3. **Initialize**: `node scripts/init_skill.cjs <name>`
4. **Edit**: Implement resources and write SKILL.md (Incorporate Project-Specific Guardrails!)
5. **Package**: `node scripts/package_skill.cjs <folder>`
6. **Install**: `gemini skills install <name>.skill --scope workspace`
7. **Reload**: Ask user to run `/skills reload`

## Writing the SKILL.md

### Frontmatter
- `name`: hyphen-case (e.g., `feature-rebuild`)
- `description`: Single-line trigger context.

### Body (Hardened Pattern)
1. **Role & Pedagogy**: Define the persona (e.g., "Professor of History").
2. **Research & Mapping**: Define sniper search site filters.
3. **The Soul Layer**: Plan emotional hooks and sensory density.
4. **Workflow Phases**: Explicitly define Phase 0 to Phase N.
5. **Pre-Submit Checklist**: Paste the Project-Specific Guardrails here.
6. **Output Format**: Define delimiter tags.

---
*Note: This workspace-specific skill-creator overrides the global one to ensure project consistency.*
