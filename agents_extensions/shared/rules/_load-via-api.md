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

These files no longer auto-load into the Claude Code system prompt
(moved out of `.claude/rules/` deploy target) — read them directly
when selected for the task or when the full offline reference is needed.

</critical>
