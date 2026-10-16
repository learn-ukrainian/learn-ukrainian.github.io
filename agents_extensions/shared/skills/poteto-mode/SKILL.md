---
name: poteto-mode
description: Match a non-trivial task to one adapted playbook and follow it inside
  repository ownership rules. Use for /poteto-mode.
---

# Poteto mode

Match the task to one playbook and follow that file. Do not copy a second orchestrator into the session. Do not install pstack, enable a hook, enable a subagent, write a model-routing rule, or run an upstream script.

## Boundaries

The accountable driver owns scope, routing, landing, and closeout (`drive-epic`). A worker completes one brief inside owned paths and does not merge, enqueue, deploy, or sub-delegate. Independent exact-head cross-family review and current-head CI are `local-code-review` and `agents_extensions/shared/rules/workflow.md`. This skill does not approve work.

New architecture, layout, process, or policy needs designated approval before it is built. Confirm irreversible or shared-system actions. Do not print secrets or private transcripts. An N-implementation arena and the Benny automation are out of policy. Do not vendor or run them.

Proceed on ordered reversible work inside the brief (`principle-never-block-on-the-human`). Stop when the brief is ambiguous and a wrong guess would be destructive.

## Principles

Read the leaf skill before you rely on it. The leaves are `principle-laziness-protocol`, `principle-foundational-thinking`, `principle-redesign-from-first-principles`, `principle-attack-the-premise`, `principle-subtract-before-you-add`, `principle-minimize-reader-load`, `principle-outcome-oriented-execution`, `principle-experience-first`, `principle-exhaust-the-design-space`, `principle-build-the-lever`, `principle-model-the-domain`, `principle-boundary-discipline`, `principle-type-system-discipline`, `principle-make-operations-idempotent`, `principle-migrate-callers-then-delete-legacy-apis`, `principle-separate-before-serializing-shared-state`, `principle-prove-it-works`, `principle-fix-root-causes`, `principle-sequence-verifiable-units`, `principle-test-behavior-not-implementation`, `principle-explain-the-number`, `principle-guard-the-context-window`, `principle-never-block-on-the-human`, and `principle-encode-lessons-in-structure`.

## Playbooks

| Playbook | Use |
| --- | --- |
| [investigation](playbooks/investigation.md) | A read-only question. |
| [bug-fix](playbooks/bug-fix.md) | Reproduce a defect, fix the cause, and prove the reproduction is gone. |
| [perf-issue](playbooks/perf-issue.md) | Trace a measured slowness against a vetted baseline. |
| [hillclimb](playbooks/hillclimb.md) | Improve one metric with a frozen harness and a decision log. |
| [runtime-forensics](playbooks/runtime-forensics.md) | Diagnose a live symptom. Do not fix unless asked. |
| [trace-forensics](playbooks/trace-forensics.md) | Diagnose a captured profile or heap snapshot. |
| [feature](playbooks/feature.md) | New or changed behavior from a named data shape. |
| [refactoring](playbooks/refactoring.md) | Change structure and keep behavior. |
| [prototype](playbooks/prototype.md) | A throwaway sketch that decides one question. |
| [visual-parity](playbooks/visual-parity.md) | Pixel match against a frozen baseline. |
| [authoring-a-skill](playbooks/authoring-a-skill.md) | Write or edit a skill under agents_extensions. |
| [eval](playbooks/eval.md) | A blinded check of a prompt or skill change the brief ordered. |
| [babysit](playbooks/babysit.md) | Drive a pull request to merge-ready without merging it. |
| [shipping](playbooks/shipping.md) | Driver-only landing after exact-head approval and green CI. |
| [autonomous-run](playbooks/autonomous-run.md) | Drive one task to a checkable predicate. |
| [orchestrate](playbooks/orchestrate.md) | A multi-day stream, using drive-epic. |
| [autopilot-full](playbooks/autopilot-full.md) | A queue of independent pull requests, driver-landed. |
| [autopilot-stack](playbooks/autopilot-stack.md) | One linear stack for the driver to land. |
| [session-pickup](playbooks/session-pickup.md) | Resume from the handoff and git, not a private transcript. |
| [pause-safely](playbooks/pause-safely.md) | Stop at a safe boundary and write the handoff. |
| [multi-phase-plan](playbooks/multi-phase-plan.md) | Phases that each end in a check. |
| [worktree-cleanup](playbooks/worktree-cleanup.md) | Reap through the common reaper only. |
| [opening-a-pr](playbooks/opening-a-pr.md) | Prepare a pull request when the brief allows one. |

When no row fits, use `figure-it-out`. A standing stream uses `drive-epic`, not a new coordinator.

## Reply

Lead with the outcome. Name the principle that changed a decision only if you read that leaf. Cite a path or a command for every verifiable claim. Use `unslop` on prose you will commit. Use `technical-writing` for a document, a pull-request body, or a commit message.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
