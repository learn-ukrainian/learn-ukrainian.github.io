# C1-HIST Quick Reference (Ukrainian Historiography Track)

## Track Overview

**Modules:** 135 (M01-135)
**Prerequisite:** B2-HIST Track (required for factual foundation)
**Pedagogy:** CBI (Content-Based Instruction) with historiographical analysis
**Immersion:** 95-100% Ukrainian

> **C1-HIST is NOT about historical facts (that's B2-HIST). It's about HOW we know history** — sources, methods, interpretations, contested narratives.

---

## Audit Limits (per config.py)

| Metric           | Value   | Source              |
| ---------------- | ------- | ------------------- |
| Word count       | 4000    | target_words        |
| Min activities   | 3       | min_activities      |
| Max activities   | 9       | max_activities      |
| Items/activity   | 1+      | min_items_per_activity |
| Required types   | reading, essay-response, critical-analysis | required_types |
| Priority types   | reading, essay-response, critical-analysis, comparative-study | priority_types |
| Forbidden types  | match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words | forbidden_types |
| Essay word range | 300-500 | essay_min/max_words |
| Immersion        | 95-100% | min/max_immersion   |
| Engagement       | 6+      | min_engagement      |
| Unique types     | 3+      | min_types_unique    |
| Vocab            | 25+     | min_vocab           |

**Note:** C1-HIST uses pure seminar-style activities. Traditional drill activities are FORBIDDEN.

---

## Valid Activity Types

| Type | Use For |
|------|---------|
| `reading` | Primary source analysis, historiographical excerpts |
| `critical-analysis` | Source evaluation, bias detection, methodology critique |
| `comparative-study` | Comparing historiographical schools, interpretations |
| `essay-response` | Analytical essays (300-500 words) |

**Forbidden:** `match-up`, `fill-in`, `cloze`, `group-sort`, `unjumble`, `anagram`, `mark-the-words`

---

## Templates

**Before writing any C1-HIST module, read:**

- **History modules** → `docs/l2-uk-en/templates/c1-history-module-template.md`
- **Tier 3 guidance** → `claude_extensions/commands/review-tiers/tier-3-seminar.md`

---

## Phase Structure (135 Modules)

| Phase   | Modules  | Focus                          |
| ------- | -------- | ------------------------------ |
| HIST.1  | M01-10   | Historiography fundamentals    |
| HIST.2  | M11-18   | Medieval sources (PVL, Pateryk)|
| HIST.3  | M19-28   | Cossack chronicles & documents |
| HIST.4  | M29-42   | Imperial mechanisms            |
| HIST.5  | M43-58   | Holodomor studies              |
| HIST.6  | M59-72   | Soviet historiography          |
| HIST.7  | M73-88   | Dissident & diaspora sources   |
| HIST.8  | M89-104  | Independence era               |
| HIST.9  | M105-120 | Contemporary & information war |
| HIST.10 | M121-135 | Synthesis & methodology        |

---

## Pre-flight Checklist

Before writing any C1-HIST module:

1. ✅ Read the plan: `curriculum/l2-uk-en/plans/c1-hist/{slug}.yaml`
2. ✅ Read the meta: `curriculum/l2-uk-en/c1-hist/meta/{slug}.yaml`
3. ✅ Read the template: `docs/l2-uk-en/templates/c1-history-module-template.md`
4. ✅ Check curriculum.yaml for correct sequence number

---

## Research-First Workflow (MANDATORY)

**C1-HIST requires Phase 0: Deep Research before writing.**

1. **Research the topic** using academic sources:
   - [litopys.org.ua](https://litopys.org.ua) — Primary sources
   - [history.org.ua](https://history.org.ua) — Institute of History NANU
   - [nbuv.gov.ua](https://nbuv.gov.ua) — National Library
   - [hrushevsky.nbuv.gov.ua](https://hrushevsky.nbuv.gov.ua) — Hrushevsky's works

2. **Take structured notes** with citations and key facts

3. **Create outline** integrating research with plan requirements

4. **Write content** using research notes (NOT from memory!)

5. **Generate activities** — 3-9 only, seminar-style

> ⚠️ **Wikipedia Warning:** Ukrainian Wikipedia is contested territory subject to Russian information warfare. For historiography, NEVER rely on Wikipedia. Use .gov.ua and academic sources only.

---

## Anti-Hallucination Rules

1. **NEVER invent historiographical debates** — verify which historians actually disagree
2. **NEVER generate primary source text from memory** — always verify from litopys.org.ua
3. **NEVER attribute views to historians without verification** — check their actual arguments
4. **NEVER invent dating or authorship debates** — these are well-documented
5. **When in doubt, mark as [NEEDS VERIFICATION]** — flag for review

---

## Activity Schema

### critical-analysis

```yaml
- type: critical-analysis
  title: "Оцінка джерела: ..."
  target_text: |
    [Primary source text or historiographical excerpt]
  questions:
    - "Question 1?"
    - "Question 2?"
  model_answers:
    - "Answer 1"
    - "Answer 2"
```

### reading

```yaml
- type: reading
  title: "Первинне джерело: ..."
  text: |
    [Source text with context]
  tasks:
    - "Task 1"
    - "Task 2"
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
  min_words: 300
  model_answer: |
    [Model essay response]
```

---

## Seminar Quality Standards

**C1-HIST modules must achieve A+ seminar quality:**

| Criterion | A+ Standard |
|-----------|-------------|
| Opening | Vivid scene, provocative question |
| Primary Sources | Woven into narrative, analyzed |
| Narrative Thread | Clear progression, conflict, resolution |
| Decolonization | Integrated perspective, not preachy |
| Emotional Peak | Moment of genuine impact |
| Modern Relevance | Organic connection to today |
| Closing | Memorable, quotable, actionable |

**Lecture Quality minimum: 9/10**

---

## Commands

```bash
# Build module
/module c1-hist {num}

# Resume from phase
/module c1-hist {num} --from={phase}

# Check status
/module c1-hist {num} --check

# Batch build
/module c1-hist {start}-{end}
```

---

## Key Differences from B2-HIST

| Aspect | B2-HIST | C1-HIST |
|--------|---------|---------|
| Focus | What happened | How we know |
| Content | Historical events | Historiographical debates |
| Sources | Secondary narratives | Primary source analysis |
| Activities | Reading + analysis | Source criticism + essays |
| Complexity | B2 vocabulary | C1 academic vocabulary |
| Length | 4000 words | 4000 words |
