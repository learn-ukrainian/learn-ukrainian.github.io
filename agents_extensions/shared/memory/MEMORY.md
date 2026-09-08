# Memory - Learn Ukrainian Project

> **BUDGET: 150 lines (hard limit 200).** Trim BEFORE adding anything.
> **WHAT BELONGS:** Hard-won behavioral lessons only. Reference content → topic files in `memory/`.

## #M-5 — NEVER PRINT SECRETS
When grepping `.bash_secrets` / `.envrc` / `.env*` / `~/.aws/credentials` / any credential file: **never print matched lines verbatim**. Always pipe through `cut -d= -f1` (key only) or `sed 's/=.*/=<REDACTED>/'`. **Inconsistent sanitization within a single diagnostic command IS the failure mode** — one branch had redaction, another didn't → leak. To check "is var X set," prefer `env -i bash -c 'source ~/.bash_secrets; [ -n "${VAR:-}" ]'` over `grep` (no value pulled into scope). Decision tree + full autopsy: `docs/bug-autopsies/secret-leakage.md`. Failure encoded: 2026-05-10 `GEMINI_API_KEY` printed during graphify-install diagnostic, forced user rotation.

## #M-4 — DETERMINISTIC OVER HALLUCINATION
**Every verifiable claim must be backed by a tool call.** The pre-trained guess feels right; it's wrong often enough to break Ukrainian curriculum, code, and orchestration. Skipping the tool = hallucinating with confidence. We have VESUM (6.7M forms), СУМ-11 (127K), Грінченко (67K), ЕСУМ, Monitor API, full code corpus, deterministic scripts — pretending otherwise is malpractice. Strict scope: word validity / stress / Russianisms / file contents / SHAs / build status / module gates / word counts / test pass-fail / module plans → run the tool. Exempt: creative output generation (narrative, dialogue, design proposals) — but every claim about an artifact inside that output is still tool-backed. Decision test: if you introduce a number, name, path, SHA, or Ukrainian word that wasn't in your very recent tool output and you didn't run a tool to confirm — STOP, run it. Full rule + anti-pattern catalog + per-agent enforcement: **`docs/best-practices/deterministic-over-hallucination.md`**. Applies to: Claude · Codex · Gemini · all dispatched sub-agents · all sessions.

## #M-3 — DON'T ASSUME COLLEAGUE TOOL CAPABILITIES OR WORK STATE — ASK
Don't design mitigations around imagined gaps in Codex/Gemini tooling (ask via `ab ask-codex` / `ab ask-agy` first — one round-trip), and don't classify uncommitted edits in a colleague's worktree as phantom or suspicious: the default reading of modifications you didn't make is WIP on their own dispatch. Codex Desktop runs `UserPromptSubmit` hooks but does not inject `additionalContext` (only Codex CLI does); its own Automations feature is the polling primitive there. ADR addendum: `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`.

## #M-2 — HTML/MD BY FLOW DIRECTION (REFINED 2026-05-09 morning)
**Format depends on the flow, not the file:**

| Flow | Format | Examples |
|---|---|---|
| **ai → human** | HTML | session handoffs, audit reports, dashboards, bakeoff comparisons, bug autopsies, PR review summaries |
| **human → ai** | MD | dispatch briefs (user writes), prompts, instructions, README, top-level project rules |
| **ai → ai** | MD | MEMORY.md, agent rules, channel context files, dispatch briefs between agents, deliberation transcripts, code-adjacent docs |

Machine-readable / agent-loaded source stays MD; HTML is a companion for human reading, never forced on new artifacts (rationale: `docs/references/external/2026-05-08-thariq-html-effectiveness.html`). Budget for 2-4× slower generation and noisy diffs. `migrate_to_html.py` refuses to overwrite hand-curated HTML (`<meta report-author>`-marked); use `--force` only with explicit user signoff.

## #M-1 — DIRECT ORDER OBEDIENCE
When user gives a direct order, especially in caps or after expressed frustration: STOP all alternative paths. Do the thing or admit I can't in ONE sentence. NO mirrors, fallbacks, curl tricks, deferring, explaining, or proposing options. If a tool is mentioned in the system prompt OR loaded by the user, USE IT FIRST. Failures encoded:
- 2026-05-09 04:00 CET: user said "do not skip" the tweet read; I kept proposing curl + mirror fallbacks. After "I SAID GET THAT TWEET" I tried curl with browser UA instead of the chrome plugin that was loaded the entire session. User had to point at it directly: "why don't you use your chrome plugin?"
- 2026-05-09 evening: user told me #1825 was theirs; I deferred memory reconciliation to them. Wrong — Claude's memory IS Claude's job. Reconcile, deploy, own.
- Lesson: for any web read, use the browser tool the session has loaded (check the tool list) before curl/WebFetch.
- Lesson: When user is frustrated, brief actions only. NO explanations, NO menus, NO "two options," NO apologetic preambles. Take the action or say "cannot, please [paste / log in / give X]."

## #M-0.5 — DON'T ADMIN-BYPASS BLOCKING CI
`gh pr merge --admin` bypasses ALL branch protection, including pytest. Only use it for explicitly-advisory failures listed in handoffs (Gemini-Dispatch, etc.). Pytest, ruff, frontend, schema-drift, gitleaks, radon, prompt-lint = ALL blocking, no exceptions, even if I think the failure is a flaky perf test. If a blocking check fails: STOP, report, ask for direction. Do NOT decide on the user's behalf. Failure encoded: 2026-05-09 PR #1813 — admin-merged while `Test (pytest):fail` showed (turned out to be flaky perf assertion `test_playground_primary_endpoints_keep_health_fast`, unrelated to MCP fix; that doesn't excuse the bypass).

## #M0 — PER-TASK MODEL ASSIGNMENT
Don't pattern-match on principles ("orchestrate when possible") — match the EXACT command. The dispatch determines the model.

| Task | Tool + model |
|---|---|
| Inline code edit ≤5 LOC, only when fixing a CI failure I just caused | Me, current model |
| Code change >5 LOC, mechanical / pattern / fixtures | Dispatch — 3:3:3 split: codex (`--agent codex --mode danger --worktree --base main`), claude-headless (architectural / cross-file), gemini (tests, schema migrations, docs-near-code). NOT gemini for: cross-file refactor, security/concurrency, GH-auth, mass mechanical |
| Wiki/content writing | `delegate.py dispatch --agent gemini` (Gemini sub, unmetered) |
| Adversarial review of design / ADR / architecture | `delegate.py dispatch --agent claude --mode read-only --model <formal CF pin from model-assignment.md> --effort xhigh` (headless, separate billing) |
| Q&A or single-shot review without need to commit | `ab ask-codex` / `ab ask-agy` (Flash default; Pro only for deep — current ids in `model-assignment.md` § Gemini) |
| Search / grep / "find me X" across files | `Agent` tool with `subagent_type: Explore`, `model: "haiku"` |
| Status check on running dispatches | Monitor API curl, never inline file scans |
| Memory / rules / Claude-owned text | Me, inline. Claude's brain = Claude's job. Never deflect to user. |

If I'm about to write code inline and it doesn't match the first row, STOP and dispatch instead. The dispatch script enforces worktree + commits — memory does not. Note: `--base main` not `--base origin/main` — runtime prepends `origin/` itself.

## #0J — LOCAL REFERENCE CORPUS IS RIGHT THERE — STOP ASKING FOR MORE (2026-05-06)
Before EVER asking the user for additional pedagogical material, check: `docs/references/private/` (ULP 1-00→4-00 + Ohoiko June preview + 1000 words + 500 verbs, gitignored), `docs/references/textbooks-txt/` (committed), `data/textbooks/` (561 MB PDFs, gitignored), MCP `mcp__sources__search_text`. Anna Ohoiko rule: align with pedagogy/methodology, never "book-based"; her materials are IP; unknown constructs may appear before explicit teaching to avoid shallow content; never copy/quote/frame materials as source text. User quote: "we have so many content, but it is never enough for you."

## #0I — DON'T STACK MICRO-DILEMMAS, DECIDE FOR THE USER (2026-05-04)
Compound decisions = ONE table + ONE recommendation, NEVER N parallel sign-off questions. Required shape: (1) state of play 1-3 sentences, (2) options table 2-3 rows max, (3) **MY RECOMMENDATION** with one explicit pick + why + reject worst by name, (4) "going to execute unless you stop me" + first action verb. A numbered "sign off on these N" list IS a menu — forbidden.

## #0H — CF REVIEW MANDATORY ON EVERY PR; THEN MERGE (2026-07-27)
**Independent cross-family (CF) formal review is ALWAYS mandatory before merge.** No exceptions for “small,” docs-only, launcher, or infra PRs. Discussion / self-review / same-family review ≠ the gate.
- Request immediately after `gh pr create` — **lightweight direct path (sealed `review-pr` RETIRED 2026-08-07):** `printf '%s\n' "Cross-family review of PR #<N> at head <SHA>: verdict + findings." | .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-<lane> - --task-id review-<N> --type review`, then post the verdict on the PR. Resolve the reviewer lane with `scripts.review.closeout_cli ... resolve-reviewer` (must be outside the author's model family; eligibility pins are retired with the sealed path). `--type review` routes to headless `delegate.py dispatch` WITH tools (`gh`/pytest), never tool-less ACP (2026-08-23, #7155) — a reviewer needs `gh` to ground a verdict.
- Closeout incomplete until CF is requested (and settled). Failure encoded: 2026-07-27 Grok shipped #5875 without CF review; operator had to ask.
- After CF pass + green blocking CI: `gh pr merge N --auto --squash` (action bias — don’t leave PRs limbo). Hold only for CF fail or blocking CI.

## #0G — NEVER REPORT ASYNC-TASK STATE FROM MEMORY (2026-05-08)
Before saying "task X is running / X just finished / X is at step Y", ALWAYS query `delegate.py status-or-fail X` or Monitor API `/api/delegate/active`. Memory of state from 2 minutes ago is wrong by default. Established 2026-05-08 after orchestrator reported bakeoff "Gemini mid-write" when it had finished.

## #0C — COLD-START VIA MONITOR API + HANDOFF CHAIN
Orient from live state per the agent definition and `workflow.md` § Cold-start sequence (Monitor API manifest → orientation → inbox); read `CLAUDE.md`, the rule files or `session-state/current.md` directly only when the Monitor API is down, and say so. Before any multi-session topic, run `ls -lt docs/session-state/*.md | head -10` and read the chain — the newest file alone is not enough; framings land 1-3 days back.

## #0B — USE THE MONITOR TOOL FOR EVENT STREAMS
`Monitor` tool: one stdout line → one notification, ~zero context cost. Use for v7_build.py JSONL events, `ab channel watch --follow`, any long-running command. NEVER poll with ScheduleWakeup loops or repeat tool calls — wait for `<task-notification>` or Monitor events.

## #0A — STATE YOUR READING OF A VAGUE INSTRUCTION, THEN PROCEED
User is senior, time-poor, budget-sensitive. On a short or vague instruction, state the interpretation you are acting on in one line ("I read X as Y with constraint Z; default is [X]"), name the ambiguity, and proceed under that reading — the user overrides if it is wrong. Stop and wait only where a wrong guess would be destructive or would make the work useless (operator contract item 10). Never present a menu ("A, B, or C?") and never act silently on a reading you did not state; a one-line challenge of a bad instruction is welcome.

## #0 — CLAUDE'S ROLE (refined 2026-05-10)
**Role:** orchestrator + adversarial reviewer + UI tester + memory/rules custodian. NOT primary coder — dispatch.
**Split: 3:3:3 Codex:Claude-headless:Gemini** across open coding (user-stated 2026-05-10, supersedes 6:4 from 2026-04-23). Routing target, not strict quota — pick by fit. Gemini = bounded tests, schema migrations, fixtures with semantic judgment, docs-near-code. NOT gemini for: ambiguous cross-file architectural rewrites, security/concurrency bugs, GH/rebase/auth-heavy work, mass mechanical pattern-application.
- **Inline that IS mine:** browser/UI testing, adversarial reviews via dispatch, hard-bug debugging through reasoning (not coding), brief writing, linguistic verification via `mcp__sources__*`, memory/rules/docs custodianship.
- **>50 LOC of non-test code inline?** STOP — dispatch instead.
- **DISPATCH WIDTH: pace/reserve-driven — fixed in-flight caps are OBSOLETE (operator 2026-07-26).** Width comes from CodexBar pace stage + reserve per lane (`codexbar usage --json --provider <lane>`), bounded above by worktree DISK (`df -h /` plus `du -sh "$repo_root/.worktrees"` where `repo_root=$(dirname "$(git rev-parse --git-common-dir)")` — disk always wins; reap finished worktrees to buy room). Doctrine: `rules/model-assignment.md` § Worker priority ladder. Check `/api/delegate/active` before firing; idle lane + quota headroom + free disk → widen.
- User signals "claude usage is hot" if Anthropic budget tight — bias to Codex+Gemini.

## #1 — QUALITY ABOVE ALL
No heuristics when proper algorithm exists. No lowering thresholds. No "for now." Lesson 2026-03-28.

## WRITER + REVIEWER POLICY (updated 2026-04-26)
- **WIKI WRITER: Gemini ALWAYS** — `scripts/wiki/compile.py` defaults `--writer gemini`; never pass `--writer=claude`. Gemini sub unmetered.
- **V7 module writer:** claude-tools, codex-tools or cursor-tools by fit — decision card `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`; routing lives in `rules/pipeline.md`.
- **Codex is primary pipeline reviewer.** Gemini self-review OFF.

## PR CI MONITOR
`Bash(command="gh pr checks N --watch --interval 10", run_in_background=True)`, then wait for notification. NEVER `for i in seq; do sleep` polling — `--watch` waits for pending.

## DISPATCH-BRIEF CHECKLIST
Codex/Claude brief MUST have these as EXPLICIT NUMBERED STEPS: (1) `git worktree add` setup, (2) file-level work, (3) test suite, (4) ruff, (5) commit conventional msg, (6) `git push -u origin`, (7) `gh pr create`, (8) NO auto-merge. Plus #M-4 preamble: brief MUST list the verifiable claims the work will produce + the deterministic tool for each + the output format that captures tool evidence (quote raw output, never "I checked X"). See `docs/best-practices/deterministic-over-hallucination.md`.

## PROMPT-ABLATION DISCIPLINE
Pipeline-prompt changes pilot on ≥3 seeded modules before bulk. Gradual: 0→1→3→10→full. Never direct-jump `--range 1 194`.

## BUILDS — ONE MODULE AT A TIME
Agent-run builds go through `scripts/build/v7_build.py <level> <slug> --worktree`, one module per run, watched with `Monitor`. Never run bulk ranges or a resume-all step: a bulk resume once destroyed 40+ files, and the pilot ladder below exists for the same reason.

## #2 — CONTEXT + SESSION DISCIPLINE
**Context lifecycle is profile-bound.** There is no universal 1M auto-compaction fallback: native Claude keeps native compaction behavior, certified gateway routes may declare a separate compaction capacity, and unknown routes force neither a denominator nor compaction. Statusline observations update the canonical per-session window; profile warning tiers drive handoff. **Monitor rot DETERMINISTICALLY** (self-report is unreliable) with `scripts/context_canary.py`: mint anchors at low context, answer FROM MEMORY at each checkpoint, `score` diffs vs frozen truth; drift below pass-ratio → hand off NOW. Log → `batch_state/canary/canary_log.csv` maps where rot starts. Late handoff fails SILENTLY (rot ≠ self-reported) — when unsure, hand off; dense-state earlier than read-once-file. Self-estimate runs 1.8× high.
- NEVER `/compact` (rewrites context, loses fidelity).
- Do not `--resume`/`--continue` the interactive orchestrator session; continue through the `thread-rollover` skill's packet.
- Diary handoff: `docs/session-state/YYYY-MM-DD-<slug>.md`.
- Overnight = orchestrator-only, ALL execution dispatched.
- Intra-session subagents are for large, genuinely independent work; dispatch volume through `delegate.py` and keep working while it runs.

## TOOL SELECTION
- `delegate.py dispatch` → EXECUTION (code+commits). Fire-and-forget, `--mode danger`.
- `ai_agent_bridge` → COMMUNICATION (discussions, reviews, Q&A). NOT execution. `ab discuss` is analysis-only — filesystem writes during discussion = HARD STOP, dispatch the work as a separate brief.
- `Monitor` → watch long-running. Never ScheduleWakeup loops.
- Monitor API `localhost:8765` → state queries. One curl > custom scripts.
- `/api/state/routing-budget` → pre-dispatch capacity check. Add `--check-budget` to delegate.py for warnings. Soft-fail when API down.
- `ugrep` → prefer over grep (faster, parallel, binary-safe).

## INVESTIGATE BEFORE ACTING
Before ANY non-trivial change: read design docs, trace flow end-to-end. "I already know" is ALWAYS wrong. 2026-04-18: assumed review was single-score before reading v6-review.md (was 9-dim weighted) — 30-min reframe.

## #0F — TRACE LOW REVIEWER DIMS TO PIPELINE CODE BEFORE PROMPT FIXES
Reviewer dim scoring low? FIRST read pipeline code producing the writer's input artifact, NOT the prompt. Twice wrong this week (#1449/EPIC #1451).

## #0E — UKRAINIAN GRADES ≠ CEFR LEVELS
School Grade 1-4 ≠ A1/A2. Orthogonal. ADR-007 killed grade→CEFR SQL filter. The 24K-chunk textbook corpus is L1 native education; A1/A2 thin-source is absence-of-L2-pedagogy, not filter problem.

## #0D — CORPUS BOOTSTRAP = A1/A2 BUILD-ORDER PLAN
NOT "pivot," NOT "L1-UK" (user corrected 4+ times). Read `memory/l1-uk-corpus-bootstrap.md` BEFORE discussing. Flow: UK wikis → UK A1/A2 → those become source → English A1/A2 immersion against enriched corpus.

## Critical Behavioral Rules (condensed)
- **PRE-COMMIT AUTO:** Done + tests pass → ruff, then request the cross-family review per #0H (`resolve-reviewer` picks the seat). User never reminds.
- **QUALITY GATE:** Every changed function needs a test. 80%+ on critical paths.
- **HYGIENE:** Work like now: act, record durable memory immediately, commit/push cleanup, keep git clean, update stale/partial issues. No chat-only promises.
- **EDUCATION NOT SOFTWARE:** Real learners use these. Build ONE module → verify pedagogy → next.
- **SEQUENCE:** One working e2e example FIRST. Never modify pipeline without tracing.
- **DIALOGUES:** From textbooks, not invented (#A2 genitive interrogation 2026-03-24).
- **WORD TARGETS:** 1.5× overshoot (4000 → 5500-6000). Easier to trim than expand.

## Fleet Comms + Delegation + CodexBar + Local API Cold-Start (2026-07-09)
**Fleet lanes:** Claude, Codex, AGY (the Gemini lane), Grok, DeepSeek, Cursor, pool, glm — current models, tiers and seats live in `rules/model-assignment.md` and `scripts/config/model_catalog.yaml`; read them live, never from this file. Width is pace/reserve-driven (CodexBar pace + disk bound), not fixed caps. Use the full fleet for parallel work.

**Communicate / ask / discuss (analysis, no FS writes):** Always `.venv/bin/python scripts/ai_agent_bridge/__main__.py` (bare `ab` = ApacheBench).
- One-shot: `ask-codex - --task-id foo <prompt.md` (also ask-claude, ask-agy [--to-model ...], ask-grok-build (native alias), ask-hermes, ask-opencode, ask-pool, ask-cursor, ask-glm...)
- Multi-agent discuss: `discuss <chan> "topic-or-stdin" --with codex,claude,agy --max-rounds 3 [--review]`
- Broker: inbox / send / post / channel / converse / process-*

**Delegate real work (edits, builds — ALWAYS --worktree):** `scripts/delegate.py dispatch --agent codex --task-id bar --brief docs/dispatch-briefs/xx.md --worktree --mode workspace-write` (or read-only). Agents: codex/claude/agy/cursor/grok (alias grok-build)/etc. Follow with `status`, `wait`, `list`.

**CodexBar.app (local Mac app on this machine):** Visual for 5h / weekly / monthly limits + consumption across agents + self. (CodexBar CLI example: `/Applications/CodexBar.app/Contents/Helpers/CodexBarCLI`)

Project-side:
- `... ai_agent_bridge/__main__.py codex-usage`
- `.venv/bin/python scripts/analytics/cost_report.py --all --markdown`
- Dashboards: `dashboards/cost.html`, `runtime.html`, `delegate.html`
- Raw: `batch_state/api_usage/*.jsonl`
- API: `/api/health` (shows resilience/slows), `/api/runtime/agents`, `/api/runtime/recent`

**Local Monitor API (cold-start + full project status) http://localhost:8765**
- Start (if down): `npm run api` (fg) or `npm run api:bg`; logs `npm run api:logs`. Also serves dashboards.
- Efficient cold-start sequence (per docs/MONITOR-API.md + #0C):
  1. `curl -s /api/state/manifest` (tiny hashes → decide fetches; supports ETag/304)
  2. Conditional: `/api/rules?format=markdown`, `/api/session/current?agent=orchestrator`
  3. `/api/orient` (git, issues, delegate, runtime, health, pipeline) or `?fresh=true`
- Key status: `/api/state/summary` (tracks: total/published_mdx/audit_passing/etc.), `/api/state/track-health/{a1,a2,...}`, `/api/state/pipeline/{track}`, `/api/orient`, `/api/delegate/active`, `/api/runtime/agents`, `/api/health`
- Full contract: `/api/contracts/routes`

**gh + MCP:** `gh` CLI installed and ready (pr list/view/diff/comment/merge). Also github MCP (search_tool first for schema, then use_tool github__*).

**Dependabot:** `.github/dependabot.yml` (weekly Mon, 7d cooldown, groups + targeted ignores for pins like pydantic-core, lxml, starlette...). Triage via `gh pr list --search dependabot`, view #N, verify (only lock changes common), merge if CI green + safe. Security-audit.yml for visibility.

See: `docs/guardrails/agent-fleet-tooling.md`, `docs/MONITOR-API.md`, `agents_extensions/shared/quick-ref/monitor-api.md`, `docs/best-practices/agent-activity-matrix.md`, `docs/best-practices/agent-cooperation.md`

## See Also (topic files in `memory/`)
- `gpt-5.5-rollout.md`, `agent-debug.md`, `data-inventory.md`, `cooperation-tooling.md`, `l1-uk-corpus-bootstrap.md`
- `textbook-research.md`, `textbook-exercises.md`, `reference_ukrainian_dictionaries_online.md`, `reference_awesome_ukrainian_nlp.md`
- `project_goals_and_frustrations.md`, `project-pitch.md`, `user_teachers_and_learning.md`, `wiki-knowledge-base-plan.md`, `fact-corrections.md`
- `feedback_*.md` — pre-V7-reboot lessons (Mar-Apr 2026), kept for reference; new feedback goes inline here
