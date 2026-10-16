---
name: poteto-help
description: Choose which adapted pstack skill or playbook fits a task. Use for /poteto-help.
---

# Poteto help

Answer the task in front of you, then name the one skill or playbook that fits. Do not install a plugin, write a model-routing rule, or enable a hook or subagent.

| Need | Open |
| --- | --- |
| Any non-trivial task | `poteto-mode` |
| How code works | `how` |
| Why it was built this way | `why` |
| What a change can break | `blast-radius` |
| Shape before code | `architect` |
| A defect | `correct` or the bug-fix playbook |
| A measurement | `benchmark-checklist` and `principle-explain-the-number` |
| Adversarial read of a diff | `interrogate` |
| Plain restatement | `bro` |
| Docs and commit text | `technical-writing` and `unslop` |
| Resume or pause | `thread-rollover`, then the session-pickup or pause playbook |

Playbooks live under `poteto-mode/playbooks/`. Principles live under `principle-*`. Routing, review, and landing stay in `drive-epic`, `local-code-review`, and `workflow.md`.

If none fit, use `figure-it-out`. Do not invent a skill name that is not in `agents_extensions/shared/skills/`.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
