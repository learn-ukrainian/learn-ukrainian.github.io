# Task-scoped instruction reading

The root `AGENTS.md` digest and operator contract remain binding. Read
`agents_extensions/shared/rules/operator-expectations.md` before consequential
work. Then load only the canonical sources applicable to the task and current
phase. This changes loading scope, not authorization or any safety/review gate.
If a relevant rule is unclear, read its full source before acting.

Paths below are relative to the repository root. Read each selected file once;
retain relevant context across phases and reload when its contents change.

| Task or phase | Read before acting |
| --- | --- |
| Any repository change, including documentation | `agents_extensions/shared/rules/critical-rules.md`; `agents_extensions/shared/rules/delegate-must-use-worktree.md`; `agents_extensions/shared/rules/workflow.md` sections on task workflow and merge policy |
| CLI implementation or interface change | `agents_extensions/shared/rules/cli-help-standard.md` |
| Curriculum planning, build, repair, or semantic review | `agents_extensions/shared/rules/non-negotiable-rules.md`; select the relevant curriculum skill below |
| Assigning workers or choosing model/provider routes | `agents_extensions/shared/rules/model-assignment.md`; `agents_extensions/shared/rules/workflow.md` research-registry and pre-dispatch sections; use live catalog and quota evidence |
| Explicitly assigned epic/track driver | `agents_extensions/shared/rules/fleet-comms-coordination.md`; `agents_extensions/shared/rules/fleet-driver-routing.md`; `docs/best-practices/fleet-shared-doctrine.md`; `docs/best-practices/fleet-role-scorecard.md`; `drive-epic` skill |
| Fleet Comms action outside an assigned driver role | `agents_extensions/shared/rules/fleet-comms-coordination.md`; preserve existing ownership and use only the requested action |
| Non-trivial intake or continuity gap | `entire-context` skill; the accountable root owns bounded intake and shares only relevant body-free locators |
| Code/infra review and closeout | `local-code-review` skill; exact-head cross-family review and required CI remain merge gates |
| Task archive, rename, or resource cleanup | `task-family-manager` skill; load only the requested operation reference |
| Rollover preparation or resumption | `thread-rollover` skill; load the current rollover phase |

Skill sources live under `agents_extensions/shared/skills/<name>/SKILL.md`.
For standalone module completion use `track-completion`; for manifest-order
track coordination use `curriculum-lifecycle`; for prerequisite-only work use
`curriculum-preparation`. A diagnostic review does not certify completion.
Ordinary code or documentation edits do not require curriculum workflow loading.

The complete Monitor `/api/rules?format=markdown` response is available for full
policy audits, ambiguous cross-cutting tasks, and clients needing the complete
ruleset. Its hash cache and source order are unchanged. Offline, select these
same Git sources; `_load-via-api.md` retains the ordered full-reference list.
A missing service never waives a gate. Do not infer health, permission, or
completion from unavailable telemetry.
