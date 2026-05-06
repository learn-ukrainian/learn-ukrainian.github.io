# Per-Task Model Assignment (HARD RULE)

<critical>

Match the EXACT command — not a principle. Memory does not enforce; the dispatch tool does. Established 2026-05-06 after repeated drift on cost discipline.

| Task | Tool + model |
|---|---|
| Inline code edit ≤5 LOC, fixing a CI failure I just caused | Me, current model |
| Code change >5 LOC, mechanical / pattern-applying / fixtures | `delegate.py dispatch --agent codex --mode danger --worktree --base origin/main` (no `--model`) |
| Wiki / content writing | `delegate.py dispatch --agent gemini` (Gemini sub, unmetered) |
| Adversarial review of design / ADR / architecture | `delegate.py dispatch --agent claude --mode read-only --model claude-opus-4-7 --effort xhigh` (headless Opus, separate billing) |
| Q&A or single-shot review without commit | `ab ask-codex` / `ab ask-gemini --model gemini-3.0-flash-preview` for routine, `--model gemini-3.1-pro-preview` only for deep |
| Search / grep / "find me X" across files | `Agent` tool with `subagent_type: Explore`, `model: "haiku"` |
| Status check on running dispatches | Monitor API curl, never inline file scans |

If I'm about to write code inline and it doesn't match row 1, STOP and dispatch instead. Tooling enforces (worktree + commits) — memory does not.

The same table lives in `memory/MEMORY.md` rule #M0; this file is the deploy-rule mirror so it loads via `npm run claude:deploy` into `.claude/rules/`.

</critical>
