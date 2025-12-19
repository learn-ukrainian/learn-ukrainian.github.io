# Checkpoint Design Guide

## Purpose

Checkpoints are **diagnostic and consolidation** modules, not content delivery modules. They answer:
- "Can the student DO the skills from this block?"
- "Where are the gaps?"

## Core Principle

> Replace "produce freely" with "recognize, complete, and compare."

Open-ended tasks are great for learning but terrible for self-study because:
- No feedback on correctness
- No model to compare against
- Student doesn't know if they succeeded

---

## Immersion Policy

**No immersion gate for checkpoints.** Immersion should come naturally from:
- Task instructions (simple imperatives: *Виберіть*, *Заповніть*)
- Model responses students analyze
- Activity sentences and dialogues
- Answer keys

**NOT from:**
- Grammar summary tables translated to Ukrainian
- Rule explanations in Ukrainian
- Filler content added to hit metrics

If you're adding Ukrainian just to raise a percentage, that's forced immersion.

---

## Checkpoint Structure: Model → Practice → Check

Every skill section needs three parts:

### 1. Model First (Show what good looks like)

```markdown
## Skill: Describing Your Day

**Model: Олег's Day**

> Вчора я **встав** о сьомій годині. Потім я **снідав** двадцять хвилин —
> я **їв** кашу і **пив** каву. Після сніданку я **пішов** на роботу.

**Notice:**
- встав, пішов = **perfective** (single completed actions)
- снідав, їв, пив = **imperfective** (processes, duration)
```

### 2. Scaffolded Practice (Guided, not open-ended)

```markdown
**Your Turn:** Fill in the correct verb forms:

1. Вчора я ___ (встати/вставати) о сьомій годині.
2. Я ___ (снідати/поснідати) двадцять хвилин.
3. Потім я ___ (піти/ходити) на роботу.

> [!solution] Перевірити (Check)
> 1. встав (perfective - single action)
> 2. снідав (imperfective - duration)
> 3. пішов (perfective - single action)
```

**Note:** Use `[!solution]` for body text answers (collapsible, click-to-reveal).
Use `[!answer]` only inside Activities section (parsed by activity renderer).

### 3. Self-Check (Did I succeed?)

```markdown
**Self-Check:**
- ☐ Did you use **perfective** for "got up" and "left"?
- ☐ Did you use **imperfective** for "was eating"?
- ☐ Do your time expressions match the aspect?
```

---

## Activity Types for Self-Study Checkpoints

| Instead of...             | Use this...                                      |
|---------------------------|--------------------------------------------------|
| "Write about your family" | Cloze passage with model + gaps                  |
| "Describe the picture"    | Multiple choice: "Which description is correct?" |
| "Have a conversation"     | Dialogue-reorder or fill-in dialogue             |
| "Express your preference" | Choose between two model responses               |
| "Tell a story"            | Error-correction on a given story                |

---

## Full Checkpoint Template

```markdown
# Checkpoint: [Block Name]

## Overview

This checkpoint reviews the skills from Modules X-Y:
- Skill 1: [e.g., Describing locations with Locative case]
- Skill 2: [e.g., Expressing past actions with aspect]
- Skill 3: [e.g., Comparing things]

---

## Skill 1: [Skill Name]

**Model:**
> [Annotated example showing the skill in use]

**Practice:** [Fill-in, complete, or choose activity]

**Self-Check:** [Criteria checklist or answer key]

---

## Skill 2: [Skill Name]

**Model:**
> [Annotated example]

**Practice:** [Scaffolded activity]

**Self-Check:** [Criteria]

---

## Integration Challenge

**Read this story, then answer the questions:**

> [Story using all reviewed grammar naturally]

1. [Question testing Skill 1]
2. [Question testing Skill 2]
3. [Question testing Skill 3]

> [!answer]
> 1. [Answer with grammar explanation]
> 2. [Answer with grammar explanation]
> 3. [Answer with grammar explanation]

---

## Summary

| Skill | Key Pattern | Example |
|-------|-------------|---------|
| Skill 1 | [Pattern] | [Quick example] |
| Skill 2 | [Pattern] | [Quick example] |
| Skill 3 | [Pattern] | [Quick example] |

---

## Need More Practice?

> [!resources] External Resources
>
> **Topic Review:**
> - 🎧 [Resource from {LEVEL}-MEDIA-ASSIGNMENT.md](URL) — Description
>
> **Struggling with a skill?** Go back to:
> - Skill 1 → Module X
> - Skill 2 → Module Y
```

---

## Section Summary

| Section         | Purpose               | Format                             |
|-----------------|-----------------------|------------------------------------|
| Model           | Show the target skill | Annotated example text             |
| Guided Practice | Scaffolded production | Fill-in, complete, choose          |
| Self-Check      | Verify correctness    | Answer key + criteria              |
| Integration     | Combine all skills    | Comprehension questions on a story |
| Resources       | Review & remediation  | Links from media assignment + module pointers |

---

## A2 Checkpoints

| Module | Checkpoint | Covers Modules |
|--------|------------|----------------|
| 11 | Cases | 01-10 |
| 24 | Aspect & Comparison | 12-23 |
| 34 | Complex Sentences | 25-33 |
| 43 | Word Formation | 35-42 |
| 55 | Vocabulary Expansion | 44-54 |

---

## Implementation Notes

1. **No word count gate** - Checkpoints can be shorter than regular modules
2. **No immersion gate** - Ukrainian emerges from practice, not filler
3. **Activity count** - Still need 10+ activities for practice density
4. **Focus on skills** - Organize by "what can you do" not "what did we cover"
5. **Resources required** - Every checkpoint must have a resources section

---

## Media Assignment Documents

Resources for checkpoints come from level-specific media assignments:

| Level | Document |
|-------|----------|
| A1 | `docs/l2-uk-en/A1-MEDIA-ASSIGNMENT.md` |
| A2 | `docs/l2-uk-en/A2-MEDIA-ASSIGNMENT.md` |
| B1 | `docs/l2-uk-en/B1-MEDIA-ASSIGNMENT.md` |
| B2 | `docs/l2-uk-en/B2-MEDIA-ASSIGNMENT.md` |
| C1 | `docs/l2-uk-en/C1-MEDIA-ASSIGNMENT.md` |
| C2 | `docs/l2-uk-en/C2-MEDIA-ASSIGNMENT.md` |

Each document contains:
- YouTube channel recommendations
- ukrainianlessons.com links by topic
- External resource URLs verified to work

---

*Created: 2025-12-19*
*Updated: 2025-12-19 - Added resources requirement*
