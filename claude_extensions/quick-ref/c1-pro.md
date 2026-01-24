# C1-PRO Quick Reference (Professional Mastery Track)

## Track Overview

**Modules:** 50 (M01-50)
**Prerequisite:** B2-PRO Track or B2 Core + demonstrated professional need
**Pedagogy:** ESP + CLIL (Content and Language Integrated Learning)
**Immersion:** 100% Ukrainian

> This track provides advanced professional and academic Ukrainian for executives, academics, and specialists.

## Workflow Integration

**C1-PRO uses the 9-phase track workflow:**

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

- Start: `/module c1-pro {num}`
- Resume: `/module c1-pro {num} --from={phase}` (phase: meta, lesson, act, vocab)
- Status: `/module c1-pro {num} --check`

**Reference:** `docs/SCRIPTS.md` for full 9-phase documentation.

---

## Audit Limits

| Metric         | Target | WARN  | FAIL  |
| -------------- | ------ | ----- | ----- |
| Word count     | 3000   | <3000 | <2800 |
| Activities     | 12     | <12   | <10   |
| Items/activity | 14     | <14   | <10   |

**WARN** = Passes with warning. **FAIL** = Blocks approval.

---

## Templates

**Before writing any C1-PRO module, read:**

- **Professional mastery modules (AI)** → `docs/l2-uk-en/templates/ai/c1-pro-module-template.md`
- **Checkpoint modules** (M13, M28, M44, M50) → Same template with checkpoint focus

> **Full documentation:** See `docs/l2-uk-en/templates/c1-pro-module-template.md` for complete reference.

---

## Phase Structure (50 Modules)

| Phase | Modules | Focus                   | Checkpoints      |
| ----- | ------- | ----------------------- | ---------------- |
| PRO.1 | M01-15  | Executive Communication | **M13**, **M15** |
| PRO.2 | M16-30  | Academic Publishing     | **M28**, **M30** |
| PRO.3 | M31-45  | Industry Specialization | **M44**, **M45** |
| PRO.4 | M46-50  | Mastery & Capstone      | **M50**          |

---

## Pre-flight Checklist

Before writing, confirm:

- [ ] Read C1-PRO-CURRICULUM-PLAN.md for this module's vocabulary + scope
- [ ] **Read the professional mastery template** (`c1-pro-module-template.md`)
- [ ] Identify if this is a checkpoint module (M13, M15, M28, M30, M44, M45, M50)
- [ ] All metadata YAML fields ready
- [ ] Activity plan: 12-15 activities, 4+ types
- [ ] Immersion target: **100%** Ukrainian

## Metadata YAML Template (`meta/{slug}.yaml`)

```yaml
module: c1-pro-XX
slug: '{slug}'
title: '{Title in Ukrainian}'
subtitle: '{English subtitle}'
version: '1.0'
phase: 'C1-PRO.X'
pedagogy: 'ESP+CLIL'
duration: 90
transliteration: 'none'
tags: ['professional-mastery', 'domain-tag']
grammar: ['advanced-professional-vocabulary', 'executive-structures']
objectives:
  - 'Learner can communicate at executive level in...'
  - 'Learner can produce professional documents for...'
prerequisites:
  - c1-pro-XX # Previous module
naturalness:
  score: 0
  status: PENDING
  checked: null
```

## Content Requirements

| Metric            | Professional Mastery | Checkpoint Modules |
| ----------------- | -------------------- | ------------------ |
| Core Word Count   | 3000+                | 2000+              |
| Immersion         | **100%**             | **100%**           |
| Vocabulary (YAML) | 35+                  | 50+                |
| Example Sentences | 28+                  | 20+                |
| Engagement Boxes  | 6+                   | 4+                 |

## Activity Requirements

| Requirement        | Professional Mastery | Checkpoint |
| ------------------ | -------------------- | ---------- |
| Total Activities   | 12-15                | 14-16      |
| Items per Activity | 14+                  | 12+        |
| Unique Types       | 4+                   | 5+         |

---

## Domain Coverage

| Phase | Domain                  | Focus                                        |
| ----- | ----------------------- | -------------------------------------------- |
| PRO.1 | Executive Communication | Leadership, strategy, stakeholder management |
| PRO.2 | Academic Publishing     | Research writing, peer review, conferences   |
| PRO.3 | Industry Specialization | IT, finance, legal, healthcare, translation  |
| PRO.4 | Mastery & Capstone      | Portfolio, career development, integration   |

---

## Golden Rule for Professional Mastery Modules

**"Is this language at C-suite/expert level?"**

- Content should reflect executive or specialist communication
- Vocabulary should be advanced and domain-specific
- Focus on nuance, precision, and professional sophistication

### Required Patterns

- Executive-level document formats
- Academic publication structures
- Cross-cultural communication awareness
- High-stakes scenarios (crisis, negotiation, presentation)

### Focus Areas

- Leadership vocabulary (візія, місія, стратегія, виконання)
- Academic discourse (гіпотеза, парадигма, концепція, теорія)
- Industry-specific terminology (IT, finance, legal, medical)
- Translation/interpretation basics

---

## Structure (ESP+CLIL/Mastery)

1. `## Вступ` - Executive context and high-level objectives
2. `## Концепція` - Theoretical framework or key concepts
3. `## Аналіз` - Case study or document analysis
4. `## Практика` - Advanced application exercises
5. `## Підсумок` - Strategic takeaways and mastery indicators

---

## Naturalness Requirements

All professional mastery modules must pass naturalness check:

- **Score:** 8/10 minimum (10/10 preferred)
- **Status:** PASS required before merge
- **Checker:** Use MCP `check_naturalness` tool

Update meta YAML after validation:

```yaml
naturalness:
  score: 10
  status: PASS
  checked: 2026-01-17
```

---

## Related Documentation

- **C1-PRO Curriculum Plan:** `docs/l2-uk-en/C1-PRO-CURRICULUM-PLAN.md`
- **Professional Mastery Template (AI):** `docs/l2-uk-en/templates/ai/c1-pro-module-template.md`
- **Professional Mastery Template (Full):** `docs/l2-uk-en/templates/c1-pro-module-template.md`
- **Activity Reference:** `docs/ACTIVITY-YAML-REFERENCE.md`
- **Richness Guidelines:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
