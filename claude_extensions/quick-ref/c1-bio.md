# C1-BIO Quick Reference (Ukrainian Biographies Track)

## Track Overview

**Modules:** 101 (M01-101)
**Prerequisite:** B2-HIST Track (recommended) or B2 Core minimum
**Pedagogy:** CBI (Content-Based Instruction) with biographical narrative
**Immersion:** 100% Ukrainian

> This track was relocated from C1 M36-131. Biography content is now optional, separate from core academic path.

---

## Relaxed Audit Limits

| Metric         | Target | WARN  | FAIL  |
| -------------- | ------ | ----- | ----- |
| Word count     | 2000   | <2000 | <1900 |
| Activities     | 10     | <10   | <8    |
| Items/activity | 16     | <16   | <12   |

**WARN** = Passes with warning. **FAIL** = Blocks approval.

**Note:** Biography modules have REDUCED activity counts (10-12) vs standard C1 (16+) because content depth is the focus.

---

## Templates

**Before writing any C1-BIO module, read:**

- **Biography modules** → `docs/l2-uk-en/templates/c1-biography-module-template.md`
- **Checkpoint** (M101) → `docs/l2-uk-en/templates/c1-checkpoint-module-template.md`

---

## Phase Structure (101 Modules)

| Phase    | Modules | Focus                          | Notable Figures |
| -------- | ------- | ------------------------------ | --------------- |
| BIO.1    | M01-06  | Medieval Founders              | Olha, Yaroslav  |
| BIO.2    | M07-15  | Early Modern Era               | Roksolana, Mazepa |
| BIO.3    | M16-19  | Enlightenment & Baroque        | Skovoroda       |
| BIO.4    | M20-35  | National Awakening             | Shevchenko, Franko |
| BIO.5    | M36-53  | Revolutionary Era              | Lesya Ukrainka, Petliura |
| BIO.6    | M54-69  | Soviet Era Tragedy             | Kurbas, Khvylovyi |
| BIO.7    | M70-82  | Resistance & Diaspora          | Shukhevych, Bandera |
| BIO.8    | M83-91  | Late Soviet & Independence     | Stus, Chornovil |
| BIO.9    | M92-98  | Contemporary Ukraine           | Activists, Artists |
| BIO.10   | M99-100 | Academy Founders               | Vernadskyi, Krymskyi |
| BIO.11   | M101    | **Checkpoint**                 | Comprehensive review |

---

## Pre-flight Checklist

Before writing, confirm:

- [ ] Read C1-BIO-CURRICULUM-PLAN.md for this module's vocabulary + biography scope
- [ ] **Read the biography template** (`c1-biography-module-template.md`)
- [ ] Research the historical figure thoroughly (use reliable Ukrainian sources)
- [ ] All metadata YAML fields ready
- [ ] Activity plan: 10-12 activities (NOT 16+), 5+ types
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
  - c1-bio-XX  # Previous module
naturalness:
  score: 0
  status: PENDING
  checked: null
```

## Content Requirements

| Metric            | Biography Modules | Checkpoint |
| ----------------- | ----------------- | ---------- |
| Core Word Count   | 2000+             | 1800+      |
| Immersion         | **100%**          | **100%**   |
| Vocabulary (YAML) | 20-25             | 50-55      |
| Engagement Boxes  | 6+                | 4+         |
| Primary Sources   | 1+ quote          | Multiple   |

## Activity Requirements

| Requirement        | Biography | Checkpoint |
| ------------------ | --------- | ---------- |
| Total Activities   | 10-12     | 16+        |
| Items per Activity | 16+       | 14+        |
| Unique Types       | 5+        | 6+         |

### Activity Complexity (Content-Heavy)

**Biography modules use context-specific targets:**

| Activity         | Min words | Max words |
| ---------------- | --------- | --------- |
| Quiz             | 8         | 25        |
| Fill-in          | 8         | 16        |
| Unjumble         | 10        | 18        |
| Error-correction | 8         | 18        |
| True-false       | 8         | 20        |

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

| Component        | Weight | Target |
| ---------------- | ------ | ------ |
| Primary sources  | 15%    | 1+ quote |
| Engagement boxes | 15%    | 6+ boxes |
| Quotes           | 10%    | 2+ quotes |
| Cultural refs    | 10%    | 4+ Ukrainian references |
| Visual elements  | 10%    | 2+ tables |
| Mini-dialogues   | 10%    | 1+ (if appropriate) |

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
- **Biography Template:** `docs/l2-uk-en/templates/c1-biography-module-template.md`
- **Checkpoint Template:** `docs/l2-uk-en/templates/c1-checkpoint-module-template.md`
- **Activity Reference:** `docs/ACTIVITY-YAML-REFERENCE.md`
- **Richness Guidelines:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
