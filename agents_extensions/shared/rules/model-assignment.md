# Per-Task Model Assignment (HARD RULE)

<critical>

Match the EXACT command — not a principle. Memory does not enforce; the dispatch tool does. Established 2026-05-06 after repeated drift on cost discipline.

| Task | Tool + model |
|---|---|
| Inline code edit ≤5 LOC, fixing a CI failure I just caused | Me, current model |
| Code change >5 LOC, mechanical / pattern-applying / fixtures | `delegate.py dispatch --agent codex --mode danger --worktree --base origin/main` (no `--model`) |
| Code Review (PR diff) — cheap second opinion | `delegate.py dispatch --agent deepseek --model deepseek-v4-flash --mode read-only` (hermes; PR #2107 adapter). Empirical winner 2026-05-17 bakeoff (A+ at 15s) |
| Content Review with VESUM verification (load-bearing) | `delegate.py dispatch --agent deepseek --model deepseek-v4-pro` (hermes; MCP-backed: proactively calls `sources` `verify_words`, `query_cefr_level`, `check_russian_shadow`). Validated by PR #2112 write-mode dispatch on artifacts-MD feature |
| Wiki / content writing | `delegate.py dispatch --agent gemini` (Gemini sub, unmetered) |
| Adversarial review of design / ADR / architecture / code — the **Claude reviewer seat** | **IN-SESSION INLINE** — the interactive orchestrator reads the artifact, verifies claims, writes the verdict + fix notes, on the main subscription quota. **NEVER** `claude -p` / `--agent claude` / Agent-SDK / GH-Actions-Claude, and **NEVER an `Agent`-tool review subagent**. Context heavy → **DEFER** to the next interactive session's start (top-of-handoff `Claude review PENDING: <artifact>`). See the reviewer-seat economics below. |
| Q&A or single-shot review without commit | `ab ask-codex` / `ab ask-gemini --model gemini-3.0-flash-preview` for routine, `--model gemini-3.1-pro-preview` only for deep |
| Search / grep / "find me X" across files | `Agent` tool with `subagent_type: Explore`, `model: "haiku"` |
| Status check on running dispatches | Monitor API curl, never inline file scans |

If I'm about to write code inline and it doesn't match row 1, STOP and dispatch instead. Tooling enforces (worktree + commits) — memory does not.

## Claude reviewer-seat economics (2026-06-12)

There is ONE Claude Code quota. A dispatched / headless / subagent Claude competes with the interactive
orchestrator's own seat, AND a subagent starts a fresh context that **reloads the full project (~2–3M tokens,
~1000:1 overhead per the global `code-editing-safety` §7 rule)** to return a verdict that inline costs
~15–25k. A subagent therefore *duplicates a session boot you pay for anyway* → ~50–150× the tokens for the
identical verdict. So the Claude reviewer seat is fulfilled IN-SESSION:

1. **Default: review INLINE, early in the session** while context is light — cheapest, full faculties, and you
   reuse the read to write the fix.
2. **Context heavy + a Claude review is still needed: DEFER** to the next MANUAL interactive session's start
   (record a top-of-handoff `Claude review PENDING: <artifact>` so cold-start picks it up first). That
   artifact's merge waits one session. Do NOT cram it into the depleted session and do NOT spawn a subagent.
   "Next session" = the next manual interactive session, NOT a cron / scheduled cloud agent / `claude -p`
   (those are the capped pool).
3. **Inline-now despite heavy context** only when latency is unacceptable (the review must clear THIS session
   to unblock something).

Non-Claude reviewers are UNAFFECTED — keep routing the bulk of reviews to them: DeepSeek (rows above) for PR
diffs + VESUM content review, Codex for novel-architecture catches. Only the *Claude* seat is in-session.
(As of mid-June 2026 the headless `--agent claude` lane is also independently off — `@anthropic-ai/claude-code`
recent versions fail with "native binary not installed" — but the economics above stand regardless of lane health.)

The same table lives in `memory/MEMORY.md` rule #M0; this file is the deploy-rule mirror so it loads via `npm run agents:deploy` into `.claude/rules/`.

</critical>
