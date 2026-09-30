# Rules — loaded via API

<critical>

The full agent rule set (operator-expectations · critical · non-negotiable ·
workflow · fleet-comms-coordination · delegate-worktree · cli-help ·
model-assignment · fleet-driver-routing · fleet-shared-doctrine ·
fleet-role-scorecard) is served at:

    GET /api/rules?format=markdown    (Monitor API on localhost:8765)

For task intake, read `agents_extensions/shared/rules/task-scoped-reading.md`
and load the applicable sources before acting. The endpoint is the complete
reference for full policy audits or cross-cutting work; it supports
`If-None-Match` for warm-cache hits.

Offline: use the same task selector. When the complete reference is needed,
read this full fallback list — same paths, same order as
`scripts/api/rules_router.py` `RULE_SOURCES`:

    agents_extensions/shared/rules/operator-expectations.md
    agents_extensions/shared/rules/critical-rules.md
    agents_extensions/shared/rules/non-negotiable-rules.md
    agents_extensions/shared/rules/workflow.md
    agents_extensions/shared/rules/fleet-comms-coordination.md
    agents_extensions/shared/rules/delegate-must-use-worktree.md
    agents_extensions/shared/rules/cli-help-standard.md
    agents_extensions/shared/rules/model-assignment.md
    agents_extensions/shared/rules/fleet-driver-routing.md
    docs/best-practices/fleet-shared-doctrine.md
    docs/best-practices/fleet-role-scorecard.md

Scoped selections — `GET /api/rules?scope=<scope>&format=markdown`, each with
its own hash. Offline, `scripts/lib/rules_core.py` reads the same files in the
same order (launchers, `delegate.py` workers and ACP asks already inject the
core):

    scope=core             agents_extensions/shared/rules/core.md
    scope=content          agents_extensions/shared/rules/core.md
                           agents_extensions/shared/rules/core-curriculum.md
    scope=task:repo-change agents_extensions/shared/rules/critical-rules.md
                           agents_extensions/shared/rules/delegate-must-use-worktree.md
                           agents_extensions/shared/rules/workflow.md
    scope=task:cli         agents_extensions/shared/rules/cli-help-standard.md
    scope=task:curriculum  agents_extensions/shared/rules/non-negotiable-rules.md
    scope=task:fresh-build docs/epics/fresh-build-build-program.md
    scope=task:routing     agents_extensions/shared/rules/model-assignment.md
                           agents_extensions/shared/rules/workflow.md
    scope=task:driver      agents_extensions/shared/rules/fleet-comms-coordination.md
                           agents_extensions/shared/rules/fleet-driver-routing.md
                           docs/best-practices/fleet-shared-doctrine.md
                           docs/best-practices/fleet-role-scorecard.md
                           agents_extensions/shared/skills/drive-epic/SKILL.md
    scope=task:fleet-comms agents_extensions/shared/rules/fleet-comms-coordination.md
    scope=task:intake      agents_extensions/shared/skills/entire-context/SKILL.md
    scope=task:review      agents_extensions/shared/skills/local-code-review/SKILL.md
    scope=task:task-family agents_extensions/shared/skills/task-family-manager/SKILL.md
    scope=task:rollover    agents_extensions/shared/skills/thread-rollover/SKILL.md

These files no longer auto-load into the Claude Code system prompt
(moved out of `.claude/rules/` deploy target) — read them directly
when selected for the task or when the full offline reference is needed.

</critical>
