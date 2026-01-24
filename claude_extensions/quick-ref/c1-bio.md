# C1-BIO Quick Reference (Ukrainian Biographies Track)

## Track Overview

**Modules:** 101 (M01-101)
**Prerequisite:** B2-HIST Track (recommended) or B2 Core minimum
**Pedagogy:** CBI (Content-Based Instruction) with biographical narrative
**Immersion:** 100% Ukrainian

> This track was relocated from C1 M36-131. Biography content is now optional, separate from core academic path.

## Workflow Integration

**C1-BIO uses the 9-phase track workflow:**

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

- Start: `/module c1-bio {num}`
- Resume: `/module c1-bio {num} --from={phase}` (phase: meta, lesson, act, vocab)
- Status: `/module c1-bio {num} --check`

**Reference:** `docs/SCRIPTS.md` for full 9-phase documentation.

---

## Audit Limits (per config.py)

| Metric           | Value   | Source              |
| ---------------- | ------- | ------------------- |
| Word count       | 4000    | target_words        |
| Min activities   | 4       | min_activities      |
| Max activities   | 9       | max_activities      |
| Items/activity   | 1+      | min_items_per_activity |
| Required types   | reading, essay-response, critical-analysis | required_types |
| Essay word range | 250-400 | essay_min/max_words |

**Note:** C1-BIO uses pure seminar-style activities. Traditional drill activities are FORBIDDEN.

---

## Templates

**Before writing any C1-BIO module, read:**

- **Biography modules (AI)** → `docs/l2-uk-en/templates/ai/c1-biography-module-template.md`
- **Checkpoint** (M101) → `docs/l2-uk-en/templates/c1-checkpoint-module-template.md`

> **Full documentation:** See `docs/l2-uk-en/templates/c1-biography-module-template.md` for complete reference.

---

## Phase Structure (101 Modules)

| Phase  | Modules | Focus                      | Notable Figures          |
| ------ | ------- | -------------------------- | ------------------------ |
| BIO.1  | M01-06  | Medieval Founders          | Olha, Yaroslav           |
| BIO.2  | M07-15  | Early Modern Era           | Roksolana, Mazepa        |
| BIO.3  | M16-19  | Enlightenment & Baroque    | Skovoroda                |
| BIO.4  | M20-35  | National Awakening         | Shevchenko, Franko       |
| BIO.5  | M36-53  | Revolutionary Era          | Lesya Ukrainka, Petliura |
| BIO.6  | M54-69  | Soviet Era Tragedy         | Kurbas, Khvylovyi        |
| BIO.7  | M70-82  | Resistance & Diaspora      | Shukhevych, Bandera      |
| BIO.8  | M83-91  | Late Soviet & Independence | Stus, Chornovil          |
| BIO.9  | M92-98  | Contemporary Ukraine       | Activists, Artists       |
| BIO.10 | M99-100 | Academy Founders           | Vernadskyi, Krymskyi     |
| BIO.11 | M101    | **Checkpoint**             | Comprehensive review     |

---

## Pre-flight Checklist

Before writing, confirm:

- [ ] Read C1-BIO-CURRICULUM-PLAN.md for this module's vocabulary + biography scope
- [ ] **Read the biography template** (`c1-biography-module-template.md`)
- [ ] Research the historical figure thoroughly (use reliable Ukrainian sources)
- [ ] All metadata YAML fields ready
- [ ] Activity plan: 4-9 seminar-style activities (must include reading + essay-response + critical-analysis)
- [ ] Essay in YAML only (250-400 words) — NO essay section in markdown
- [ ] NO traditional drill activities (fill-in, match-up, unjumble, etc. are FORBIDDEN)
- [ ] Immersion target: **100%** Ukrainian

## Metadata YAML Template (`meta/{slug}.yaml`)

```yaml
module: c1-bio-XX
slug: '{slug}'
title: '{Name}: {Epithet}'
subtitle: '{English subtitle}'
version: '1.0'
phase: 'C1-BIO.X'
pedagogy: 'CBI'
duration: 90
transliteration: 'none'
tags: ['biography', 'era-tag', 'field-tag']
grammar: ['biographical-vocabulary', 'narrative-structures']
objectives:
  - 'Learner can understand biographical narrative about...'
  - 'Learner can use vocabulary of achievements and legacy...'
prerequisites:
  - c1-bio-XX # Previous module
naturalness:
  score: 0
  status: PENDING
  checked: null
```

## Content Requirements

| Metric            | Biography Modules | Checkpoint |
| ----------------- | ----------------- | ---------- |
| Core Word Count   | 4000+             | 2500+      |
| Immersion         | **100%**          | **100%**   |
| Vocabulary (YAML) | 20-25             | 50-55      |
| Engagement Boxes  | 6+                | 4+         |
| Primary Sources   | 1+ quote          | Multiple   |

## Activity Requirements (per config.py)

**C1-BIO uses pure seminar-style pedagogy:**

| Requirement        | Biography | Checkpoint |
| ------------------ | --------- | ---------- |
| Total Activities   | 4-9       | 14+        |
| Items per Activity | 1+        | 14+        |
| Unique Types       | 3+        | 6+         |

### Required Activity Types

**Every module MUST include:**
- `reading` - External reading assignments with linguistic analysis
- `essay-response` - 250-400 word essay task (NO model answer in markdown)
- `critical-analysis` - Deep analytical questions about sources/legacy

**Optional activity types:**
- `comparative-study` - Cross-figure or cross-era comparisons
- `authorial-intent` - Analysis of the figure's own writings
- `quiz` - ONLY for conceptual questions (per config.py, quiz is allowed)

### FORBIDDEN Activity Types (per config.py)

**These traditional drill activities are NOT ALLOWED in C1-BIO:**
- match-up
- fill-in
- cloze
- group-sort
- unjumble
- anagram
- mark-the-words

### Essay Activities

Essays are defined ONLY in `activities/{slug}.yaml`, NOT in markdown:

```yaml
- type: essay-response
  id: c1-bio-XX-essay-01
  title: 'Есе: Порівняльний аналіз'
  prompt: |
    Напишіть порівняльне есе (250-400 слів)...
  rubric:
    - criterion: Мовна якість
      weight: 40
```

**Word range:** 250-400 (per config.py essay_min/max_words)

---

## Golden Rule for Biography Modules

**"Can the learner answer without reading the Ukrainian text?"**

- If YES → Rewrite (tests biographical facts, not language)
- If NO → Keep (tests Ukrainian comprehension)

### Forbidden Patterns (Tests Content Recall)

- "У якому році народився..." (birth dates)
- "Хто був..." (who was)
- "Що символізує..." (without text reference)

### Required Patterns (Tests Ukrainian Language)

- "Згідно з текстом, як автор аналізує..."
- "У тексті модуля автор інтерпретує..."
- "Яку стилістичну функцію виконує..."

---

## Biography Module Structure

### Required Sections

1. **Вступ** - Hook and context (why this person matters)
2. **Життєпис** - Biographical narrative (chronological)
3. **Досягнення** - Achievements and contributions
4. **Спадщина** - Legacy and modern relevance
5. **Підсумок** - Summary

### Required Elements

- **Primary source quote** - At least one quote from the person or contemporaries
- **Timeline table** - Key dates and events
- **Cultural references** - Ukrainian place names, institutions, works
- **Engagement boxes** - 💡, 🇺🇦, 🌍 types for cultural depth

---

## Richness Requirements

Biography modules must achieve **95%+ richness score**:

| Component        | Weight | Target                  |
| ---------------- | ------ | ----------------------- |
| Primary sources  | 15%    | 1+ quote                |
| Engagement boxes | 15%    | 6+ boxes                |
| Quotes           | 10%    | 2+ quotes               |
| Cultural refs    | 10%    | 4+ Ukrainian references |
| Visual elements  | 10%    | 2+ tables               |
| Mini-dialogues   | 10%    | 1+ (if appropriate)     |

---

## Naturalness Requirements

All biography modules must pass naturalness check:

- **Score:** 8/10 minimum (10/10 preferred)
- **Status:** PASS required before merge
- **Checker:** Use MCP `check_naturalness` tool

Update meta YAML after validation:

```yaml
naturalness:
  score: 10
  status: PASS
  checked: 2026-01-16
```

---

## Gender & Era Balance

The track maintains diversity:

- **Gender:** ~30% women figures across all eras
- **Era:** Coverage from 10th century to present
- **Fields:** Politics, arts, science, literature, activism, military
- **Regions:** Kyiv, Galicia, Slobozhanshchyna, diaspora

---

## Related Documentation

- **C1-BIO Curriculum Plan:** `docs/l2-uk-en/C1-BIO-CURRICULUM-PLAN.md`
- **Biography Template (AI):** `docs/l2-uk-en/templates/ai/c1-biography-module-template.md`
- **Biography Template (Full):** `docs/l2-uk-en/templates/c1-biography-module-template.md`
- **Checkpoint Template:** `docs/l2-uk-en/templates/c1-checkpoint-module-template.md`
- **Activity Reference:** `docs/ACTIVITY-YAML-REFERENCE.md`
- **Richness Guidelines:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
