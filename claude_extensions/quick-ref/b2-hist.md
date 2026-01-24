# B2-HIST Quick Reference (Ukrainian History Track)

## Track Overview

**Modules:** 61 (M01-61)
**Prerequisite:** B2 Core (M01-70)
**Pedagogy:** CBI (Content-Based Instruction) with narrative arcs
**Immersion:** 100% Ukrainian

> This track was relocated from B2 M71-131. History content is now optional, separate from core grammar path.

---

## Audit Limits (per config.py)

| Metric           | Value   | Source              |
| ---------------- | ------- | ------------------- |
| Word count       | 4000    | target_words        |
| Min activities   | 3       | min_activities      |
| Max activities   | 10      | max_activities      |
| Items/activity   | 1+      | min_items_per_activity |
| Required types   | reading, essay-response | required_types |
| Essay word range | 150-250 | essay_min/max_words |

**Note:** B2-HIST uses seminar-style activities (reading + essay-response + critical-analysis), not traditional drill activities. Quality over quantity.

---

## Templates

**Before writing any B2-HIST module, read the appropriate template:**

- **History modules** (M01-61, excluding synthesis) → `docs/l2-uk-en/templates/ai/b2-history-module-template.md`
- **Synthesis modules** (M13, M27, M37, M49, M55, M61) → `docs/l2-uk-en/templates/b2-history-synthesis-module-template.md`

> **Full documentation:** See `docs/l2-uk-en/templates/b2-history-module-template.md` for complete reference.

---

## Workflow Integration

**B2-HIST uses the 9-phase track workflow:**

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

- Start: `/module b2-hist {num}`
- Resume: `/module b2-hist {num} --from={phase}` (phase: meta, lesson, act, vocab)
- Status: `/module b2-hist {num} --check`

**Reference:** `docs/SCRIPTS.md` for full 9-phase documentation.

---

## Phase Structure (61 Modules)

| Phase  | Modules | Focus                              | Synthesis        |
| ------ | ------- | ---------------------------------- | ---------------- |
| HIST.1 | M01-13  | Origins to Kyivan Rus              | **M13**          |
| HIST.2 | M14-27  | Cossack Era                        | (none)           |
| HIST.3 | M28-37  | Imperial Period & National Revival | **M37**          |
| HIST.4 | M38-49  | Soviet Period & Tragedies          | **M49**          |
| HIST.5 | M50-61  | Independence & Modern Ukraine      | **M55**, **M61** |

---

## Pre-flight Checklist

Before writing, confirm:

- [ ] Read B2-HIST-CURRICULUM-PLAN.md for this module's vocabulary + grammar scope
- [ ] **Read the appropriate template** (history or synthesis)
- [ ] Identify if this is a synthesis module (M13, M27, M37, M49, M55, M61)
- [ ] All metadata YAML fields ready
- [ ] Activity plan: 3-10 seminar-style activities (must include reading + essay-response)
- [ ] Essay in YAML only (150-250 words) — NO essay section in markdown
- [ ] Immersion target: **100%** Ukrainian

## Metadata YAML Template (`meta/{slug}.yaml`)

```yaml
module: b2-hist-XX
slug: '{slug}'
title: '{Title in Ukrainian}'
subtitle: '{Subtitle}'
version: '1.0'
phase: 'B2-HIST.X'
pedagogy: 'CBI'
duration: 90
transliteration: 'none'
tags: ['history', 'topic-tag']
grammar: ['historical-vocabulary', 'narrative-structures']
objectives:
  - 'Learner can understand historical narrative about...'
  - 'Learner can use period-specific vocabulary...'
prerequisites:
  - b2-hist-XX # Previous module
```

## Content Requirements

| Metric            | History Modules | Synthesis Modules |
| ----------------- | --------------- | ----------------- |
| Core Word Count   | 4000+           | 3000+             |
| Immersion         | **100%**        | **100%**          |
| Vocabulary (YAML) | 20-25           | 30-40             |
| Example Sentences | 24+             | 16+               |
| Engagement Boxes  | 5+              | 3+                |

## Activity Requirements (per config.py)

**B2-HIST uses seminar-style pedagogy:**

| Requirement        | History | Synthesis |
| ------------------ | ------- | --------- |
| Total Activities   | 3-10    | 3-10      |
| Items per Activity | 1+      | 1+        |
| Unique Types       | 2+      | 2+        |

### Required Activity Types

**Every module MUST include:**
- `reading` - External reading assignments with linguistic analysis
- `essay-response` - 150-250 word essay task (NO model answer in markdown)

**Optional activity types:**
- `critical-analysis` - Analytical questions about source material
- `comparative-study` - Cross-period or cross-figure comparisons
- `true-false` - Only for factual checks (allowed in B2-HIST)

### Essay Activities

Essays are defined ONLY in `activities/{slug}.yaml`, NOT in markdown:

```yaml
- type: essay-response
  id: b2-hist-XX-essay-01
  title: 'Есе: [Topic]'
  prompt: |
    Напишіть есе (150-250 слів)...
  rubric:
    - criterion: Мовна якість
      weight: 40
```

**Word range:** 150-250 (per config.py essay_min/max_words)

---

## Golden Rule for History Modules

**"Can the learner answer without reading the Ukrainian text?"**

- If YES → Rewrite (tests history facts, not language)
- If NO → Keep (tests Ukrainian comprehension)

### Forbidden Patterns (Tests Content)

- "У якому році..." (dates)
- "Хто був..." (names)
- "Скільки..." (numbers)

### Required Patterns (Tests Language)

- "Згідно з текстом, як автор..."
- "У тексті модуля автор характеризує..."
- "Який аргумент автор наводить..."

---

## Synthesis Modules

Synthesis modules consolidate learning across multiple modules:

| Module | Title                        | Scope                  |
| ------ | ---------------------------- | ---------------------- |
| M13    | Синтез: Витоки               | Origins to Cossack     |
| M37    | Синтез: Козаччина до 1920    | Cossack Era to Revival |
| M49    | Синтез: Трагедії XX століття | Soviet tragedies       |
| M55    | Синтез: Шлях до волі         | Independence path      |
| M61    | Синтез: Війна за існування   | Revolution & War       |

**Synthesis modules focus on:**

- Cross-era analysis and comparison
- Thematic connections across periods
- Decolonization perspective
- Critical analysis of historical narratives

---

## Decolonization Approach

History modules must present Ukrainian history from Ukrainian perspective:

- **Avoid:** Russo-centric framings ("Little Russia", "reunification")
- **Use:** Ukrainian terminology (Київська Русь, not "Kievan")
- **Include:** Module M26 "Російські міфи про Україну" explicitly addresses imperial myths
- **Balance:** Show agency of Ukrainian actors, not just victimhood

---

## Structure (CBI/Narrative)

1. `## Вступ` - Historical context and hook
2. `## Наратив` - Extended historical narrative (500+ words)
3. `## Аналіз` - Analysis of events/significance
4. `## Джерела` - Primary source excerpts (when available)
5. `## Підсумок` - Summary and legacy

---

## Related Documentation

- **B2-HIST Curriculum Plan:** `docs/l2-uk-en/B2-HIST-CURRICULUM-PLAN.md`
- **History Template (AI):** `docs/l2-uk-en/templates/ai/b2-history-module-template.md`
- **History Template (Full):** `docs/l2-uk-en/templates/b2-history-module-template.md`
- **Synthesis Template:** `docs/l2-uk-en/templates/b2-history-synthesis-module-template.md`
- **Activity Reference:** `docs/ACTIVITY-YAML-REFERENCE.md`
