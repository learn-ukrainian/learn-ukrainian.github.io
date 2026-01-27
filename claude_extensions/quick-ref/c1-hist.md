# C1-HIST Quick Reference (Advanced Historiography Track)

## Track Overview

**Modules:** 135 (M01-135)
**Prerequisite:** B2-HIST Track (for factual foundation)
**Pedagogy:** SEMINAR (academic analysis, not narrative)
**Immersion:** 95-100% Ukrainian
**Focus:** HOW we know history, not WHAT happened

> C1-HIST is the analytical complement to B2-HIST. It teaches historiographical methodology, source criticism, and interpretation of competing narratives.

---

## Audit Limits (per config.py)

| Metric           | Value   | Source              |
| ---------------- | ------- | ------------------- |
| Word count       | 4000    | target_words        |
| Min activities   | 3       | min_activities      |
| Max activities   | 9       | max_activities      |
| Items/activity   | 1+      | min_items_per_activity |
| Required types   | reading, essay-response, critical-analysis | required_types |
| Essay word range | 500+    | essay_min_words     |
| Vocabulary       | 25+     | min_vocab           |

**Note:** C1-HIST uses seminar-style activities. Quality over quantity. All essays require 500+ words with thesis, evidence, and analysis.

---

## Templates

**Before writing any C1-HIST module, read the template:**

- **All modules** → `docs/l2-uk-en/templates/c1-history-module-template.md`

> **Full documentation:** The template includes research strategy, anti-hallucination rules, and YAML examples.

---

## Activity Types (Schema: activities-c1-hist.schema.json)

### Required Types (Every Module)

| Type | Purpose | Key Requirements |
|------|---------|------------------|
| `reading` | Primary source input | MUST have `id` for linking |
| `essay-response` | Analytical output | 500+ words, thesis + evidence |
| `critical-analysis` | Source criticism | 2-4 questions with model answers |

### Recommended Types

| Type | Purpose | When to Use |
|------|---------|-------------|
| `comparative-study` | Compare interpretations | Ukrainian vs Russian vs Western |
| `source-evaluation` | 5-question method | Teaching methodology |
| `debate` | Contested interpretations | Complex historiographical questions |

### Source-Evaluation Activity

Structured application of the 5-question method:

```yaml
- type: source-evaluation
  title: "Оцінка джерела: [Name]"
  source_text: "[Historical source excerpt]"
  source_metadata:
    author: "[Author]"
    date: "[Date]"
    type: "[chronicle/memoir/official/propaganda/academic]"
    context: "[Historical context]"
  evaluation_criteria:
    - authorship
    - date_and_context
    - intended_audience
    - purpose_and_bias
    - omissions
  guiding_questions:
    - "Хто написав це джерело?"
    - "Яким був контекст створення?"
    - "Для кого це було написано?"
    - "Яка мета автора?"
    - "Що це джерело замовчує?"
  model_evaluation: "[Model answer]"
```

### Debate Activity

For contested historiographical interpretations:

```yaml
- type: debate
  title: "Дискусія: [Question]"
  debate_question: "[Contested historiographical question]"
  historical_context: "[Background]"
  positions:
    - name: "[Position 1]"
      proponents: "[Historians]"
      argument: "[Core argument]"
      evidence: ["[Evidence 1]", "[Evidence 2]"]
      weaknesses: ["[Critique]"]
    - name: "[Position 2]"
      proponents: "[Historians]"
      argument: "[Core argument]"
      evidence: ["[Evidence]"]
  analysis_tasks:
    - "Визначте найсильніший аргумент."
    - "Чи є спільні точки між позиціями?"
  model_analysis: "[Model answer]"
```

### Forbidden Activity Types

Per config.py, C1-HIST does NOT use drill activities:
- `match-up`, `fill-in`, `cloze`, `group-sort`, `unjumble`, `anagram`, `mark-the-words`
- `quiz` (unless testing methodology, not factual recall)

---

## Phase Structure (135 Modules)

| Phase     | Modules | Focus                              |
| --------- | ------- | ---------------------------------- |
| C1H.1     | M01-10  | Historiography & Methodology       |
| C1H.2-5   | M11-50  | Primary Sources (Medieval → Modern)|
| C1H.6-9   | M51-80  | Thematic Studies (Holodomor, etc.) |
| C1H.10-11 | M81-95  | Regional Perspectives              |
| C1H.12-16 | M96-115 | Imperial Mechanisms & Patterns     |
| C1H.17-21 | M116-135| Complex Questions & Synthesis      |

---

## Pre-flight Checklist

Before writing, confirm:

- [ ] Read module plan from `curriculum/l2-uk-en/plans/c1-hist/{slug}.yaml`
- [ ] **Read the template** `docs/l2-uk-en/templates/c1-history-module-template.md`
- [ ] **Research historiography** (WebSearch, WebFetch academic sources)
- [ ] All metadata YAML fields ready
- [ ] Activity plan: 3-9 seminar-style activities (must include reading + essay-response + critical-analysis)
- [ ] Essay in YAML only (500+ words) — NO essay section in markdown
- [ ] Immersion target: **95-100%** Ukrainian

## Metadata YAML Template (`meta/{slug}.yaml`)

```yaml
module: c1-hist-XX
level: C1-HIST
slug: '{slug}'
version: '2.0'
duration: 150
transliteration: none
tags:
  - historiography
  - [methodology/sources/decolonization/etc.]
vocabulary_count: 30
naturalness:
  score: 10
  status: PASS
build:
  last_modified: 'YYYY-MM-DD'
```

---

## Content Requirements

| Metric            | Target    |
| ----------------- | --------- |
| Core Word Count   | 4000+     |
| Immersion         | 95-100%   |
| Vocabulary (YAML) | 25+       |
| Engagement Boxes  | 6+        |
| Primary Sources   | 1+        |

---

## The 5-Question Method

C1-HIST teaches critical source analysis using 5 questions:

1. **Хто написав?** (Authorship, credentials, affiliation)
2. **Коли?** (Date and historical context)
3. **Для кого?** (Intended audience)
4. **Чому?** (Purpose, agenda, motivation)
5. **Що опущено?** (Omissions, silences, alternative perspectives)

This method should be taught in M01 and applied throughout the track.

---

## Golden Rule for C1-HIST

**"Does this teach HOW we know, not WHAT happened?"**

- If testing facts → Belongs in B2-HIST
- If testing methodology → Belongs in C1-HIST

### C1-HIST Patterns (Tests Methodology)

- "Застосуйте 5 питань критичного аналізу..."
- "Порівняйте українську та російську інтерпретації..."
- "Визначте упередження в цьому джерелі..."
- "Як цей текст використовується в сучасній пропаганді?"

### NOT C1-HIST Patterns (Tests Facts)

- "У якому році..." (dates)
- "Хто був..." (names)
- "Де відбулося..." (places)

---

## Engagement Boxes for C1-HIST

```markdown
> [!history-bite]
> [Surprising historiographical fact]

> [!quote]
> [Primary source excerpt with attribution]

> [!analysis]
> [Critical analysis point]

> [!caution]
> [Methodological warning or propaganda alert]

> [!source]
> [Source criticism note]

> [!reflection]
> [Self-check or deeper thinking prompt]
```

---

## Related Documentation

- **C1-HIST Level Plan:** `curriculum/l2-uk-en/plans/c1-hist.yaml`
- **C1-HIST Module Plans:** `curriculum/l2-uk-en/plans/c1-hist/{slug}.yaml`
- **Template:** `docs/l2-uk-en/templates/c1-history-module-template.md`
- **Activity Schema:** `schemas/activities-c1-hist.schema.json`
- **Activity Reference:** `docs/ACTIVITY-YAML-REFERENCE.md`
- **Sample Module:** `curriculum/l2-uk-en/c1-hist/01-shcho-take-istoriohrafiia.md`

---

**Last Updated:** 2026-01-27
**Version:** 1.0
