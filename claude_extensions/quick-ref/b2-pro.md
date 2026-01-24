# B2-PRO Quick Reference (Professional Ukrainian Track)

## Track Overview

**Modules:** 40 (M01-40)
**Prerequisite:** B2 Core (M01-70)
**Pedagogy:** ESP (English for Specific Purposes adapted for Ukrainian)
**Immersion:** 100% Ukrainian

> This track provides career-focused Ukrainian language training separate from the core grammar path.

## Workflow Integration

**B2-PRO uses the 9-phase track workflow:**

1. **Meta** → Generate module metadata (hydrated content outline)
2. **Meta-QA** → Validate metadata and word targets
3. **Lesson** → Write lesson content following meta outline
4. **Lesson-QA** → Validate lesson against requirements
5. **Act** → Generate activities from lesson content
6. **Act-QA** → Validate activities quality and coverage
7. **Integrate** → Deploy to website (MDX generation)
8. **Vocab** → Extract vocabulary from lesson
9. **Vocab-QA** → Validate vocabulary schema and uniqueness

**Commands:**

- Start: `/module b2-pro {num}`
- Resume: `/module b2-pro {num} --from={phase}` (phase: meta, lesson, act, vocab)
- Status: `/module b2-pro {num} --check`

**Reference:** `docs/SCRIPTS.md` for full 9-phase documentation.

---

## Audit Limits

| Metric         | Target | WARN  | FAIL  |
| -------------- | ------ | ----- | ----- |
| Word count     | 3000   | <3000 | <2800 |
| Activities     | 10     | <10   | <8    |
| Items/activity | 14     | <14   | <10   |

**WARN** = Passes with warning. **FAIL** = Blocks approval.

---

## Templates

**Before writing any B2-PRO module, read:**

- **Professional modules (AI)** → `docs/l2-uk-en/templates/ai/b2-pro-module-template.md`
- **Checkpoint modules** (M13, M28, M38, M40) → Same template with checkpoint focus

> **Full documentation:** See `docs/l2-uk-en/templates/b2-pro-module-template.md` for complete reference.

---

## Phase Structure (40 Modules)

| Phase | Modules | Focus                       | Checkpoints      |
| ----- | ------- | --------------------------- | ---------------- |
| PRO.1 | M01-15  | Business Communication      | **M13**, **M15** |
| PRO.2 | M16-30  | Technical & Domain-Specific | **M28**, **M30** |
| PRO.3 | M31-40  | Media & Public Discourse    | **M38**, **M40** |

---

## Pre-flight Checklist

Before writing, confirm:

- [ ] Read B2-PRO-CURRICULUM-PLAN.md for this module's vocabulary + scope
- [ ] **Read the professional template** (`b2-pro-module-template.md`)
- [ ] Identify if this is a checkpoint module (M13, M15, M28, M30, M38, M40)
- [ ] All metadata YAML fields ready
- [ ] Activity plan: 10-12 activities, 4+ types
- [ ] Immersion target: **100%** Ukrainian

## Metadata YAML Template (`meta/{slug}.yaml`)

```yaml
module: b2-pro-XX
slug: '{slug}'
title: '{Title in Ukrainian}'
subtitle: '{English subtitle}'
version: '1.0'
phase: 'B2-PRO.X'
pedagogy: 'ESP'
duration: 90
transliteration: 'none'
tags: ['professional', 'domain-tag']
grammar: ['professional-vocabulary', 'business-structures']
objectives:
  - 'Learner can communicate professionally in...'
  - 'Learner can use domain-specific vocabulary for...'
prerequisites:
  - b2-pro-XX # Previous module
```

## Content Requirements

| Metric            | Professional Modules | Checkpoint Modules |
| ----------------- | -------------------- | ------------------ |
| Core Word Count   | 3000+                | 2000+              |
| Immersion         | **100%**             | **100%**           |
| Vocabulary (YAML) | 30+                  | 40+                |
| Example Sentences | 24+                  | 16+                |
| Engagement Boxes  | 5+                   | 3+                 |

## Activity Requirements

| Requirement        | Professional | Checkpoint |
| ------------------ | ------------ | ---------- |
| Total Activities   | 10-12        | 12-14      |
| Items per Activity | 14+          | 12+        |
| Unique Types       | 4+           | 5+         |

---

## Domain Coverage

| Phase | Domain                   | Modules                                               |
| ----- | ------------------------ | ----------------------------------------------------- |
| PRO.1 | Business Communication   | Email, reports, meetings, presentations, negotiations |
| PRO.2 | Technical Domains        | IT, finance, legal, medical, HR, scientific           |
| PRO.3 | Media & Public Discourse | News analysis, journalism, public speaking            |

---

## Golden Rule for Professional Modules

**"Is this language transferable to real professional contexts?"**

- Activities should simulate real workplace scenarios
- Vocabulary should be immediately applicable
- Avoid overly academic or theoretical content

### Required Patterns

- Real business document formats (emails, reports, contracts)
- Authentic professional scenarios
- Domain-specific terminology in context

### Focus Areas

- Formal register markers (шановний, з повагою, прошу)
- Meeting vocabulary (порядок денний, протокол, ухвала)
- Negotiation terms (пропозиція, компроміс, умови)
- Technical terminology appropriate to domain

---

## Structure (ESP/Professional)

1. `## Вступ` - Professional context and objectives
2. `## Лексика` - Domain-specific vocabulary introduction
3. `## Практика` - Authentic document/scenario analysis
4. `## Завдання` - Practical application tasks
5. `## Підсумок` - Key takeaways and next steps

---

## Related Documentation

- **B2-PRO Curriculum Plan:** `docs/l2-uk-en/B2-PRO-CURRICULUM-PLAN.md`
- **Professional Template (AI):** `docs/l2-uk-en/templates/ai/b2-pro-module-template.md`
- **Professional Template (Full):** `docs/l2-uk-en/templates/b2-pro-module-template.md`
- **Activity Reference:** `docs/ACTIVITY-YAML-REFERENCE.md`
