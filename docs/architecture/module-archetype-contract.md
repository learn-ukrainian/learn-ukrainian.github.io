---
title: "Module Archetype Contract"
status: DRAFT
date: 2026-05-31
owner: Codex / orchestrator
scope: Writer prompt, deterministic gates, A1-C2 and seminar lesson generation
---

# Module Archetype Contract

## Purpose

Learner state answers: what does the student already know?

The module archetype answers: what kind of lesson is this?

The writer needs both. Without an archetype contract, automation treats A1 M1,
A1 M7, B1 core grammar, and HIST seminar modules as variations of the same
four-tab page. That is why hand-written modules can be good while one-pass
automation drifts: the model is forced to infer pedagogy from scattered plan,
wiki, config, and resource context.

## Runtime Source

The resolver lives in `scripts/pipeline/module_archetypes.py`.

Prompt builders and review gates should call:

```python
from pipeline.module_archetypes import format_module_archetype, resolve_module_archetype

contract = resolve_module_archetype(track="a1", module_num=1)
prompt_block = format_module_archetype(contract)
```

## Initial Archetypes

| Archetype | Scope | Main constraint |
| --- | --- | --- |
| `a1-zero-script-onboarding` | A1 M01 | English-led zero-learner lesson; every Ukrainian item introduced before use |
| `a1-script-building` | A1 M02-M04 | English-led script/sound/stress work with point-of-use media |
| `a1-first-contact-survival` | A1 M05-M07 | Memorized phrases, short reusable dialogues, checkpoint review |
| `a1-grammar-first-contact` | A1 M08-M24 | English explanations, Ukrainian pattern boxes, tightly scoped examples |
| `a1-a2-expansion-ramp` | late A1 and A2 | Late A1 receding English; A2 easy Ukrainian with a natural complexity ramp |
| `b1-plus-core` | B1-C2 core | Ukrainian-only body; English only in Vocabulary translations |
| `seminar-source-analysis` | BIO, HIST, LIT, OES, RUTH, FOLK, ISTORIO | Source-based analytical lesson; seminar activities, not beginner drills |

## Fixed Product Surface

The product contract is:

1. Lesson
2. Workbook
3. Vocabulary
4. Resources

Current Starlight output still renders:

1. Lesson
2. Vocabulary
3. Activities
4. Resources

That is a runtime mismatch, not a pedagogy decision. The archetype contract uses
the product labels while also exposing the current Starlight labels so migration
can be incremental.

## Resource Policy

Required resources appear twice:

- at the point of use, inside Lesson or Workbook, when the learner needs them;
- canonically in Resources, so the module has a complete source/resource
  inventory.

Internal AI-facing wiki pages are not student-facing resources. Do not link
private or unpublished wiki material from lessons.

## Gate Direction

The next deterministic gates should consume this contract:

- `introduced-before-use`: activity concepts cannot appear before the lesson
  introduces them.
- `resource-coverage`: plan/resource obligations are present in the lesson or
  workbook and listed in Resources.
- `archetype-fit`: activity families, language role, and tab composition match
  the resolved archetype.
- `ULP-fidelity`: A1/A2 modules follow the accepted ULP ramp and presentation
  practices.
