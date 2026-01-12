# A2 Checkpoint Module Template

**Purpose:** Diagnostic and consolidation for A2 phases (Cases, Aspect, Word Formation, etc.)
**Pedagogy:** TTT (Test-Teach-Test) / Skill-Based
**Immersion:** Graduated (follows A2 phase norms)

<!--
TEMPLATE_METADATA:
  required_sections:
  - Overview|Огляд
  - Integration Challenge|Інтеграційне завдання
  - Summary|Підсумок
  - Need More Practice?
  optional_sections:
  - Cultural Note
  - Myth Buster
  forbidden_headers:
  - Activities
  - Vocabulary
  - External Resources
  pedagogy: TTT
  min_word_count: 800
  required_callouts: []
  description: A2 checkpoint focuses on Skill-based review (Model-Practice-Check)
-->

---

## Checkpoint Structure (Skill-Based)

Every skill from the block gets its own section.

### # [Checkpoint Title]

### ## Overview

(or `## Огляд`)

List of skills reviewed from previous modules.

### ---

### ## Skill 1: [Skill Name]

Each skill section MUST have three parts:

#### ### Model: [Skill Context]

(or `### Модель:`)

> [Annotated example text showing the skill in use]

**Notice:**

- [Grammar point 1]
- [Linguistic pattern 2]

#### ### Practice: [Small Drill]

(or `### Практика:`)

[5-8 practice items like fill-in or choice]

1. [Item]
2. [Item]

> [!solution] Перевірити
>
> 1. [Answer]
> 2. [Answer]

#### ### Self-Check:

(or `### Самоперевірка`)

- ☐ [Criterion 1]
- ☐ [Criterion 2]

---

### [Repeat for all Skills]

---

### ## Integration Challenge

(or `## Інтеграційне завдання`)

A combined task (story, dialogue, or analysis) that requires using multiple skills from the phase together.

---

### # Summary

(or `# Підсумок`)

Standard A2 summary table:

| Skill   | Pattern   | Example   |
| ------- | --------- | --------- |
| Skill 1 | [Pattern] | [Example] |

---

### ## Need More Practice?

Mandatory section for external links.

---

## Content Structure Note

### Activities & Vocabulary & Resources

**CRITICAL:** Do NOT add `## Activities`, `## Vocabulary`, or `## External Resources` headers. These sections are injected automatically from YAML sidecars.


---

## Naturalness Quality Checklist

**Run this check during Stage 4 (Review & Fix) on prose activities.**

Before finalizing the module, verify prose activities (cloze, fill-in, unjumble with 5+ sentences) achieve:

- [ ] **Subject consistency** - Clear subjects maintained throughout passages
- [ ] **Discourse markers** - At least 2-3 connectors per 10-sentence passage (а, але, потім, тому, також, спочатку, нарешті)
- [ ] **Topic coherence** - All sentences contribute to unified narrative/theme, no random topic jumps
- [ ] **No template repetition** - Varied sentence structures across activities within the module
- [ ] **Moderate intensifiers** - Maximum 2-3 "дуже" per module, 0-1 "надзвичайно/справжній"
- [ ] **No double superlatives** - Use one precise descriptor instead of redundant pairs (e.g., "найкращий" NOT "найкращий та найвидатніший")
- [ ] **Natural transitions** - Avoid robotic "і це", "тому що... тому" patterns

**Target score:** 8/10 for content modules, 7/10 for checkpoints

**Red flags (score < target):**
- Same sentence template repeated across multiple activities
- Disconnected factoid lists without discourse markers
- Excessive intensifiers or double superlatives
- Robotic, mechanical transitions

**See:** `claude_extensions/stages/stage-4-review-fix.md` Section 9 for detailed naturalness criteria.

**For batch scanning:** Use `/scan-naturalness {level} {start} {end}` to scan completed modules.

