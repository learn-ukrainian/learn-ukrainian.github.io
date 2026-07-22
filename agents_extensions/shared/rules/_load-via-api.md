# Rules — loaded via API

<critical>

The full agent rule set (critical · non-negotiable · workflow ·
fleet-comms-coordination · delegate-worktree · cli-help · model-assignment)
is served at:

    GET /api/rules?format=markdown    (Monitor API on localhost:8765)

Cold-start: fetch this endpoint as step 2 of the orientation sequence
(workflow.md § "Cold-start sequence"). The endpoint supports
`If-None-Match` for warm-cache hits.

Offline fallback (API unreachable):

    agents_extensions/shared/rules/operator-expectations.md
    agents_extensions/shared/rules/critical-rules.md
    agents_extensions/shared/rules/non-negotiable-rules.md
    agents_extensions/shared/rules/workflow.md
    agents_extensions/shared/rules/fleet-comms-coordination.md
    agents_extensions/shared/rules/delegate-must-use-worktree.md
    agents_extensions/shared/rules/cli-help-standard.md
    agents_extensions/shared/rules/model-assignment.md

These files no longer auto-load into the Claude Code system prompt
(moved out of `.claude/rules/` deploy target) — read them directly
only when the API is down.

</critical>
