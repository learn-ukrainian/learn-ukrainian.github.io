# B2-HIST Quick Reference (Ukrainian History Track)

## Track Overview

**Modules:** 61 (M01-61)
**Prerequisite:** B2 Core (M01-70)
**Pedagogy:** CBI (Content-Based Instruction) with narrative arcs
**Immersion:** 100% Ukrainian

> This track was relocated from B2 M71-131. History content is now optional, separate from core grammar path.

---

## Relaxed Audit Limits

| Metric         | Target | WARN  | FAIL  |
| -------------- | ------ | ----- | ----- |
| Word count     | 1800   | <1800 | <1700 |
| Activities     | 10     | <10   | <8    |
| Items/activity | 14     | <14   | <10   |

**WARN** = Passes with warning. **FAIL** = Blocks approval.

**Note:** History modules have REDUCED activity counts (10-12) vs standard B2 (14+) because content depth is the focus.

---

## Templates

**Before writing any B2-HIST module, read the appropriate template:**

- **History modules** (M01-61, excluding synthesis) → `docs/l2-uk-en/templates/b2-history-module-template.md`
- **Synthesis modules** (M13, M27, M37, M49, M55, M61) → `docs/l2-uk-en/templates/b2-history-synthesis-module-template.md`

---

## Phase Structure (61 Modules)

| Phase   | Modules | Focus                            | Synthesis      |
| ------- | ------- | -------------------------------- | -------------- |
| HIST.1  | M01-13  | Origins to Kyivan Rus            | **M13**        |
| HIST.2  | M14-27  | Cossack Era                      | (none)         |
| HIST.3  | M28-37  | Imperial Period & National Revival | **M37**      |
| HIST.4  | M38-49  | Soviet Period & Tragedies        | **M49**        |
| HIST.5  | M50-61  | Independence & Modern Ukraine    | **M55**, **M61** |

---

## Pre-flight Checklist

Before writing, confirm:

- [ ] Read B2-HIST-CURRICULUM-PLAN.md for this module's vocabulary + grammar scope
- [ ] **Read the appropriate template** (history or synthesis)
- [ ] Identify if this is a synthesis module (M13, M27, M37, M49, M55, M61)
- [ ] All metadata YAML fields ready
- [ ] Activity plan: 10-12 activities (NOT 14+), 5+ types
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
  - b2-hist-XX  # Previous module
```

## Content Requirements

| Metric            | History Modules | Synthesis Modules |
| ----------------- | --------------- | ----------------- |
| Core Word Count   | 1800+           | 1500+             |
| Immersion         | **100%**        | **100%**          |
| Vocabulary (YAML) | 20-25           | 30-40             |
| Example Sentences | 24+             | 16+               |
| Engagement Boxes  | 5+              | 3+                |

## Activity Requirements

| Requirement        | History | Synthesis |
| ------------------ | ------- | --------- |
| Total Activities   | 10-12   | 12-14     |
| Items per Activity | 14+     | 12+       |
| Unique Types       | 5+      | 5+        |

### Activity Complexity (Content-Heavy)

**History modules use REDUCED complexity targets:**

| Activity         | Min words | Max words |
| ---------------- | --------- | --------- |
| Quiz             | 6         | 20        |
| Fill-in          | 8         | 14        |
| Unjumble         | 7         | 15        |
| Error-correction | 8         | 16        |
| True-false       | 8         | 18        |

> **Rationale:** Historical narratives don't need artificial elaboration. Quiz like "Згідно з текстом, коли Шевченко отримав волю?" is pedagogically effective at 8 words.

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

| Module | Title                          | Scope                    |
| ------ | ------------------------------ | ------------------------ |
| M13    | Синтез: Витоки                 | Origins to Cossack       |
| M37    | Синтез: Козаччина до 1920      | Cossack Era to Revival   |
| M49    | Синтез: Трагедії XX століття   | Soviet tragedies         |
| M55    | Синтез: Шлях до волі           | Independence path        |
| M61    | Синтез: Війна за існування     | Revolution & War         |

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
- **History Template:** `docs/l2-uk-en/templates/b2-history-module-template.md`
- **Synthesis Template:** `docs/l2-uk-en/templates/b2-history-synthesis-module-template.md`
- **Activity Reference:** `docs/ACTIVITY-YAML-REFERENCE.md`
