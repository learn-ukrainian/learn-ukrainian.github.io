# Per-Task Model Assignment (HARD RULE)

<critical>

Match the EXACT command — not a principle. Memory does not enforce; the dispatch tool does. Established 2026-05-06 after repeated drift on cost discipline.

| Task | Tool + model |
|---|---|
| Inline code edit ≤5 LOC, fixing a CI failure I just caused | Me, current model |
| Code change >5 LOC, mechanical / pattern-applying / fixtures | `delegate.py dispatch --agent codex --mode danger --worktree --base origin/main` (no `--model`) |
| Code Review (PR diff) — cheap second opinion | `delegate.py dispatch --agent deepseek --model deepseek-v4-flash --mode read-only` (hermes; PR #2107 adapter). Empirical winner 2026-05-17 bakeoff (A+ at 15s) |
| Content Review with VESUM verification (load-bearing) | `delegate.py dispatch --agent deepseek --model deepseek-v4-pro` (hermes; MCP-backed: proactively calls `sources` `verify_words`, `query_cefr_level`, `check_russian_shadow`). Validated by PR #2112 write-mode dispatch on artifacts-MD feature |
| Wiki / content writing | `delegate.py dispatch --agent agy` (Gemini-family lane; **metered** — agy replaced gemini-cli 2026-06-08; §7/factual cleared 2026-06-13). Wiki-writer policy stays Gemini-family. |
| Adversarial review of design / ADR / architecture / code — the **Claude reviewer seat** | **Prefer IN-SESSION INLINE for cost** — the interactive orchestrator reads the artifact, verifies claims, writes the verdict + fix notes on the main quota (cheapest path; economics below). Dispatching Claude (`claude -p` / `--agent claude` / `review-deep` / an `Agent` review subagent) **is permitted when it adds value or inline isn't feasible** — the `-p` sunset was cancelled (user 2026-06-22). For routine reviews still prefer inline or a non-Claude lane; reserve dispatched Claude for catches that need it. Context heavy → DEFER to the next interactive session, or dispatch if it must clear now. |
| Q&A or single-shot review without commit | `ab ask-codex` / `ab ask-agy --to-model gemini-3.5-flash-high` for routine, `--to-model gemini-3.1-pro-high` only for deep (gemini-cli retired → agy) |
| Search / grep / "find me X" across files | `Agent` tool with `subagent_type: Explore`, `model: "haiku"` |
| Status check on running dispatches | Monitor API curl, never inline file scans |

If I'm about to write code inline and it doesn't match row 1, STOP and dispatch instead. Tooling enforces (worktree + commits) — memory does not.

## Fleet discussion panels — actively involve ≥1 other agent before committing (user order 2026-06-23)

Drive high-judgment work (design, architecture, in-the-loop review, brief authoring) YOURSELF in-context — Opus 4.8 does not brain-rot (canary-verified). But for any SUBSTANTIVE design / decision, **actively DISCUSS + cross-verify with the fleet BEFORE committing** — not solo dispatch-and-merge. Default to ≥1 other agent per substantive task; solo only for trivial work. Convene by lane:

- **Module-content panel** (writers, content review): **agy** (gemini-pro) · **gpt-5.5** (codex, `--effort xhigh`) · **cursor** (composer-2.5). Prefer a bake-off + cross-family verification. Folk content review stays **cross-family (GPT↔Claude)** per `docs/folk-epic/folk-review-rubric.md` — **NO DeepSeek for folk culture** (lacks intrinsic Ukrainian-culture knowledge).
- **Infra panel** (code, gates, pipeline, tooling, schemas, Atlas/lexicon): **agy** · **gpt-5.5** (codex) · **cursor** (auto) · **grok-build** · **deepseek-v4-pro** (code review).

Invocation (`scripts/ai_agent_bridge/__main__.py`): `ask-codex` · `ask-agy --to-model gemini-3.1-pro-high` · `ask-cursor --model auto` (or `--model composer-2.5`) · `ask-grok-build` · `discuss <channel> "<topic>" --with <a,b,c>` for a bounded multi-round. **deepseek has NO `ask-*`** — route it via `delegate.py dispatch --agent deepseek --model deepseek-v4-pro`. Bridge `ask-*` replies arrive as INBOX MESSAGES (`ab read <id>`), not stdout.

**Model names here are current-as-of-2026-06-23 EXAMPLES, not constants** — grok-build, cursor, agy, hermes change CLIs/flags/models often. Confirm current capability via this file, `docs/best-practices/agent-activity-matrix.md`, `ab check-model`, the agent's `--help`, or `docs/agent-runtime-guide.md` before relying on a specific string. Worked example: the 2026-06-23 Atlas warning-taxonomy plan — a 3-agent panel (codex, agy-pro, cursor) caught real defects no single seat saw.

## Claude reviewer-seat economics (2026-06-12)

There is ONE Claude Code quota. A dispatched / headless / subagent Claude competes with the interactive
orchestrator's own seat, AND a subagent starts a fresh context that **reloads the full project (~2–3M tokens,
~1000:1 overhead per the global `code-editing-safety` §7 rule)** to return a verdict that inline costs
~15–25k. A subagent therefore *duplicates a session boot you pay for anyway* → ~50–150× the tokens for the
identical verdict. So **prefer** fulfilling the Claude reviewer seat IN-SESSION (dispatching Claude is
permitted — the `-p` sunset was cancelled, user 2026-06-22 — but it costs the multiple above, so route by need):

1. **Default: review INLINE, early in the session** while context is light — cheapest, full faculties, and you
   reuse the read to write the fix.
2. **Context heavy + a Claude review is still needed: DEFER** to the next MANUAL interactive session's start
   (record a top-of-handoff `Claude review PENDING: <artifact>` so cold-start picks it up first). That
   artifact's merge waits one session. Prefer this over cramming it into a depleted session or spawning a
   subagent (cost) — though dispatch IS available when the review must clear now.
3. **Inline-now despite heavy context** only when latency is unacceptable (the review must clear THIS session
   to unblock something).

Non-Claude reviewers are UNAFFECTED — keep routing the bulk of reviews to them: DeepSeek (rows above) for PR
diffs + VESUM content review, Codex for novel-architecture catches. The *Claude* seat is **preferred** in-session for cost.
(The headless `--agent claude` / `claude -p` lane is AVAILABLE again — the mid-June 2026 sunset / "native binary not
installed" fiasco was cancelled, user 2026-06-22; Claude may be used for ANY task, incl. dispatched review, when needed.
The cost economics above stand regardless: dispatched Claude is far pricier than inline, so route by need, not by ban.)

The same table lives in `memory/MEMORY.md` rule #M0; this file is the deploy-rule mirror so it loads via `npm run agents:deploy` into `.claude/rules/`.

</critical>
