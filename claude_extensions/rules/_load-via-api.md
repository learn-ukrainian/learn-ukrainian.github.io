# Rules — loaded via API

<critical>

The full agent rule set (critical · non-negotiable · workflow ·
delegate-worktree · cli-help · model-assignment) is served at:

    GET /api/rules?format=markdown    (Monitor API on localhost:8765)

Cold-start: fetch this endpoint as step 2 of the orientation sequence
(workflow.md § "Cold-start sequence"). The endpoint supports
`If-None-Match` for warm-cache hits.

Offline fallback (API unreachable):

    claude_extensions/rules/critical-rules.md
    claude_extensions/rules/non-negotiable-rules.md
    claude_extensions/rules/workflow.md
    claude_extensions/rules/delegate-must-use-worktree.md
    claude_extensions/rules/cli-help-standard.md
    claude_extensions/rules/model-assignment.md

These files no longer auto-load into the Claude Code system prompt
(moved out of `.claude/rules/` deploy target) — read them directly
only when the API is down.

</critical>
