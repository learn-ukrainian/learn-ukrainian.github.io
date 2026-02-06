# LIT Quick Reference (Ukrainian Literature Track)

## Track Overview

**Modules:** 30 (M01-30)
**Prerequisite:** C1 Core (required)
**Pedagogy:** CBI (Content-Based Instruction) with literary analysis
**Immersion:** 95-100% Ukrainian

> **LIT is about deep engagement with classic Ukrainian literature** — original texts, literary analysis, stylistic devices, and cultural context.

---

## Audit Limits (per config.py)

| Metric           | Value   | Source              |
| ---------------- | ------- | ------------------- |
| Word count       | 4500    | target_words        |
| Min activities   | 3       | min_activities      |
| Max activities   | 9       | max_activities      |
| Items/activity   | 1+      | min_items_per_activity |
| Unique types     | 2+      | min_types_unique    |
| Required types   | reading, essay-response, critical-analysis | required_types |
| Priority types   | reading, essay-response, critical-analysis, comparative-study | priority_types |
| Forbidden types  | quiz, match-up, fill-in, unjumble, anagram, cloze, mark-the-words | forbidden_types |
| Immersion        | 95-100% | min/max_immersion   |
| Engagement       | 4+      | min_engagement      |

**Note:** LIT uses pure seminar-style activities. Traditional drill activities are FORBIDDEN. No essay word range configured in config.py.

---

## Valid Activity Types

| Type | Use For |
|------|---------|
| `reading` | Primary text analysis, literary excerpts |
| `critical-analysis` | Stylistic analysis, thematic interpretation, authorial intent |
| `comparative-study` | Comparing authors, periods, literary movements |
| `essay-response` | Analytical essays on literary topics |

**Forbidden:** `quiz`, `match-up`, `fill-in`, `unjumble`, `anagram`, `cloze`, `mark-the-words`

---

## Templates

**Before writing any LIT module, read:**

- **Literature template** → `docs/l2-uk-en/templates/lit-module-template.md` (if available)
- **Tier 3 guidance** → `claude_extensions/commands/review-tiers/tier-3-seminar.md`

---

## Phase Structure (30 Modules)

| Phase | Modules | Focus                      | Key Author                     |
| ----- | ------- | -------------------------- | ------------------------------ |
| LIT.1 | M01-05  | Котляревський              | Eneida, Natalka Poltavka       |
| LIT.2 | M06-10  | Квітка-Основ'яненко        | Marusya, Konotop Witch         |
| LIT.3 | M11-20  | Шевченко                   | Kobzar, Haidamaky, Zapovit     |
| LIT.4 | M21-25  | Куліш                      | Black Council, language debates |
| LIT.5 | M26-30  | Нечуй-Левицький            | Kaidash Family, realism        |

---

## Pre-flight Checklist

Before writing any LIT module:

1. Read the plan: `curriculum/l2-uk-en/plans/lit/{slug}.yaml`
2. Read the meta: `curriculum/l2-uk-en/lit/meta/{slug}.yaml`
3. Read the template (if available)
4. Research the literary work using Ukrainian sources (ukrlib.com.ua)

---

## Research-First Workflow (MANDATORY)

**LIT requires Phase 0: Deep Research before writing.**

1. **Research the literary work** using primary sources:
   - [ukrlib.com.ua](https://ukrlib.com.ua) — Ukrainian digital library
   - Ukrainian literary criticism and scholarship
   - Historical context from Ukrainian sources

2. **Take structured notes** with citations, key quotes, and literary analysis

3. **Create outline** integrating research with plan requirements

4. **Write content** using research notes (NOT from memory!)

5. **Generate activities** — 3-9 only, seminar-style

> **Source integrity:** All texts and analysis based on Ukrainian scholarship, avoiding Russian imperial interpretations.

---

## Anti-Hallucination Rules

1. **NEVER invent literary interpretations** — verify which scholars actually hold these views
2. **NEVER generate literary text from memory** — always verify from ukrlib or original editions
3. **NEVER attribute views to literary critics without verification**
4. **NEVER invent publication dates or biographical details**
5. **When in doubt, mark as [NEEDS VERIFICATION]** — flag for review

---

## Content Requirements

| Metric            | Value   |
| ----------------- | ------- |
| Core Word Count   | 4500+   |
| Immersion         | **95-100%** |
| Engagement Boxes  | 4+      |
| Primary Sources   | Required (original literary text excerpts) |

---

## Golden Rule for Literature Modules

**"Can the learner answer without reading the Ukrainian text?"**

- If YES → Rewrite (tests literary knowledge, not language)
- If NO → Keep (tests Ukrainian literary comprehension)

---

## Activity Schema

### reading

```yaml
- type: reading
  title: "Первинне джерело: ..."
  text: |
    [Literary text excerpt with context]
  tasks:
    - "Task 1"
    - "Task 2"
```

### critical-analysis

```yaml
- type: critical-analysis
  title: "Аналіз тексту: ..."
  target_text: |
    [Literary passage or excerpt]
  questions:
    - "Question 1?"
    - "Question 2?"
  model_answers:
    - "Answer 1"
    - "Answer 2"
```

### comparative-study

```yaml
- type: comparative-study
  title: "Порівняльний аналіз: ..."
  items_to_compare:
    - "Item 1"
    - "Item 2"
  criteria:
    - "Criterion 1"
    - "Criterion 2"
  prompt: "Analysis prompt"
  model_answer: |
    [Model comparative analysis]
```

### essay-response

```yaml
- type: essay-response
  title: "Есе: ..."
  prompt: |
    [Essay prompt with requirements]
  model_answer: |
    [Model essay response]
```

---

## Related Documentation

- **LIT Level Plan:** `curriculum/l2-uk-en/plans/lit.yaml`
- **LIT Module Plans:** `curriculum/l2-uk-en/plans/lit/{slug}.yaml`
- **Activity Reference:** `docs/ACTIVITY-YAML-REFERENCE.md`
- **Richness Guidelines:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
