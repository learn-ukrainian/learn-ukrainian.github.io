---
name: module-workflow
description: Expert knowledge for Ukrainian curriculum module development workflow. Provides commands for staging modules from skeleton to content to activities and finally review.
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# Module Workflow Skill

Expert knowledge for Ukrainian curriculum module development workflow.

## Module Creation Pipeline

### Stage 1: Skeleton

```bash
/module-stage-1 [level] [module_num]
```

- Creates module file with frontmatter and section markers
- Extracts vocabulary from curriculum plan
- No content generation yet

### Stage 2: Content

```bash
/module-stage-2 [level] [module_num]
```

- Reads curriculum plan for grammar scope
- Generates all content sections
- Uses ONLY vocabulary from plan
- Follows level-specific template

### Stage 3: Activities

```bash
/module-stage-3 [level] [module_num]
```

- Creates `.activities.yaml` file (NOT embedded in MD)
- Follows activity sequencing: recognition → discrimination → controlled → production
- Uses module vocabulary + prior modules
- Validates Ukrainian grammar against Russianisms/calques

### Stage 4: Review & Fix

```bash
/module-stage-4 [level] [module_num]
```

- Runs audit in loop until PASS
- Fixes violations (rebuilds if >3 errors)
- Runs full pipeline (lint → generate → validate)
- Maximum 3 iterations before asking for help

## Batch Processing

All stages support batch ranges:

```bash
/module-stage-3 b1 52-56    # Process modules 52, 53, 54, 55, 56
```

Uses subagent pattern for fresh context per module.

## Quality Gates

### Audit Gates (Stage 4)

- Grammar violations (Russianisms, calques, case errors)
- Vocabulary violations (words not in module table)
- Activity syntax issues
- Richness failures (activity count, sentence complexity)

### Pipeline Gates

- Lint: Markdown format compliance
- Generate: MDX creation for Docusaurus
- Validate MDX: Content integrity check
- Validate HTML: Browser rendering test (requires dev server)

## Module Types & Templates

| Module Type               | Template                            | Architect Skill                |
| ------------------------- | ----------------------------------- | ------------------------------ |
| Grammar (B1-B2)           | `b1-grammar-module-template.md`     | `grammar-module-architect`     |
| Vocabulary (B1)           | `b1-vocab-module-template.md`       | `vocab-module-architect`       |
| Cultural (B1-C1)          | `b1-cultural-module-template.md`    | `cultural-module-architect`    |
| History/Biography (B2-C1) | `history-module-template.md`        | `history-module-architect`     |
| Integration (B1-B2)       | `b1-integration-module-template.md` | `integration-module-architect` |
| Checkpoint                | `b1-checkpoint-module-template.md`  | `checkpoint`                   |

## Ukrainian Validation Sources

✅ **Trusted:**

- Словник.UA (slovnyk.ua) - standard spelling
- Словарь Грінченка - authentic Ukrainian forms
- Антоненко-Давидович "Як ми говоримо" - Russianisms guide

❌ **NOT Trusted:**

- Google Translate
- Russian-Ukrainian dictionaries

## Auto-fail Errors

### Russianisms

- кушать → їсти
- да → так
- кто → хто
- нету → немає
- приймати участь → брати участь
- самий кращий → найкращий

### Calques (English loan translations)

- робити сенс → мати сенс
- брати місце → відбуватися
- в кінці дня → врешті-решт

## Immersion Levels

- **A1**: Scaffolded (English + transliteration) → NOT for NLP validation
- **A2**: 40-50% immersed → NOT for NLP validation
- **B1 M01-M05**: Metalanguage bridge
- **B1 M06-M85**: 100% immersed → IDEAL for NLP validation
- **B2, C1, C2**: 100% immersed → IDEAL for NLP validation

## Critical Rules

### NEVER

- Write modules from memory
- Add "helpful" vocabulary not in plan
- Skip template reading
- Keep old activities when enriching
- Use vocabulary not in module table

### ALWAYS

- Read curriculum plan first
- Read template before writing
- Delete ALL activities before recreating
- Verify answers are correct
- Add vocabulary from curriculum plan
- Run audit before declaring complete
