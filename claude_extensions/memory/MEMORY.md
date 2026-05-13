# Memory - Learn Ukrainian Project

> **BUDGET: 150 lines (hard limit 200).** Trim BEFORE adding anything.
> **WHAT BELONGS:** Hard-won behavioral lessons only. Reference content → topic files in `memory/`.

## #M-5 — NEVER PRINT SECRETS (HARD RULE, 2026-05-10)
When grepping `.bash_secrets` / `.envrc` / `.env*` / `~/.aws/credentials` / any credential file: **never print matched lines verbatim**. Always pipe through `cut -d= -f1` (key only) or `sed 's/=.*/=<REDACTED>/'`. **Inconsistent sanitization within a single diagnostic command IS the failure mode** — one branch had redaction, another didn't → leak. To check "is var X set," prefer `env -i bash -c 'source ~/.bash_secrets; [ -n "${VAR:-}" ]'` over `grep` (no value pulled into scope). Decision tree + full autopsy: `docs/bug-autopsies/secret-leakage.md`. Failure encoded: 2026-05-10 `GEMINI_API_KEY` printed during graphify-install diagnostic, forced user rotation.

## #M-4 — DETERMINISTIC OVER HALLUCINATION (TOP PRIORITY, 2026-05-09)
**Every verifiable claim must be backed by a tool call.** The pre-trained guess feels right; it's wrong often enough to break Ukrainian curriculum, code, and orchestration. Skipping the tool = hallucinating with confidence. We have VESUM (6.7M forms), СУМ-11 (127K), Грінченко (67K), ЕСУМ, Monitor API, full code corpus, deterministic scripts — pretending otherwise is malpractice. Strict scope: word validity / stress / Russianisms / file contents / SHAs / build status / module gates / word counts / test pass-fail / module plans → run the tool. Exempt: creative output generation (narrative, dialogue, design proposals) — but every claim about an artifact inside that output is still tool-backed. Decision test: if you introduce a number, name, path, SHA, or Ukrainian word that wasn't in your very recent tool output and you didn't run a tool to confirm — STOP, run it. Full rule + anti-pattern catalog + per-agent enforcement: **`docs/best-practices/deterministic-over-hallucination.md`**. Applies to: Claude · Codex · Gemini · all dispatched sub-agents · all sessions.

## #M-3 — DON'T ASSUME COLLEAGUE TOOL CAPABILITIES OR WORK STATE — ASK (2026-05-09)
Don't design mitigations around imagined gaps in Codex/Gemini tooling, AND don't classify uncommitted edits in a colleague's worktree as "phantom" / suspicious / unsigned. Both errors hit 2026-05-09. (1) **Tool capabilities:** assumed "Codex headless is blind" — wrong, has `@browser` / `@browser-use`. ASK via `ab ask-codex` / `ab ask-gemini` before designing around assumed gaps. (2) **Work state:** stash-and-filed Codex's WIP review-fixes for PR #1824 as suspicious phantom-edits (#1832, closed not-planned). Default hypothesis when `git status` in a colleague worktree shows modifications you didn't make: they're WIP-ing on their own dispatch. Cost: one `ab ask-*` round-trip. (3) **Empirical finding 2026-05-09 evening:** Codex Desktop runs `UserPromptSubmit` hooks but does NOT inject `additionalContext` into model context (only Codex CLI does). See ADR addendum at `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`. Codex Desktop has its own [Automations](https://developers.openai.com/codex/app/automations) feature for autonomous polling — that's the right primitive, not external hooks/cron.

## #M-2 — HTML/MD BY FLOW DIRECTION (REFINED 2026-05-09 morning)
**Format depends on the flow, not the file:**

| Flow | Format | Examples |
|---|---|---|
| **ai → human** | HTML | session handoffs, audit reports, dashboards, bakeoff comparisons, bug autopsies, PR review summaries |
| **human → ai** | MD | dispatch briefs (user writes), prompts, instructions, README, top-level project rules |
| **ai → ai** | MD | MEMORY.md, agent rules, channel context files, dispatch briefs between agents, deliberation transcripts, code-adjacent docs |

User's refinement (2026-05-09 mid-morning): *"html is for ai → human, human→ai ai→ai should stay md no?"* — yes. Don't force HTML for everything new. Codex's r1 in `33d8893f` already nailed this: machine-readable / agent-loaded source stays MD; HTML is a companion for human reading. Per Thariq (`docs/references/external/2026-05-08-thariq-html-effectiveness.html`). Plugins: `frontend-design` for styling, `playground` for interactive. No `/html` skill — Thariq warned against it. Tradeoffs to budget: 2-4× slower generation, noisy diffs. `migrate_to_html.py` refuses to overwrite hand-curated HTML (`<meta report-author>`-marked); use `--force` only with explicit user signoff.

## #M-1 — DIRECT ORDER OBEDIENCE (TOP PRIORITY, 2026-05-09)
When user gives a direct order, especially in caps or after expressed frustration: STOP all alternative paths. Do the thing or admit I can't in ONE sentence. NO mirrors, fallbacks, curl tricks, deferring, explaining, or proposing options. If a tool is mentioned in the system prompt OR loaded by the user, USE IT FIRST. Failures encoded:
- 2026-05-09 04:00 CET: user said "do not skip" the tweet read; I kept proposing curl + mirror fallbacks. After "I SAID GET THAT TWEET" I tried curl with browser UA instead of the chrome plugin that was loaded the entire session. User had to point at it directly: "why don't you use your chrome plugin?"
- 2026-05-09 evening: user told me #1825 was theirs; I deferred memory reconciliation to them. Wrong — Claude's memory IS Claude's job. Reconcile, deploy, own.
- Lesson: When in doubt, the answer is `mcp__claude-in-chrome__*` for any web read, not curl/WebFetch.
- Lesson: When user is frustrated, brief actions only. NO explanations, NO menus, NO "two options," NO apologetic preambles. Take the action or say "cannot, please [paste / log in / give X]."

## #M-0.5 — DON'T ADMIN-BYPASS BLOCKING CI (HARD RULE, 2026-05-09)
`gh pr merge --admin` bypasses ALL branch protection, including pytest. Only use it for explicitly-advisory failures listed in handoffs (Gemini-Dispatch, etc.). Pytest, ruff, frontend, schema-drift, gitleaks, radon, prompt-lint = ALL blocking, no exceptions, even if I think the failure is a flaky perf test. If a blocking check fails: STOP, report, ask for direction. Do NOT decide on the user's behalf. Failure encoded: 2026-05-09 PR #1813 — admin-merged while `Test (pytest):fail` showed (turned out to be flaky perf assertion `test_playground_primary_endpoints_keep_health_fast`, unrelated to MCP fix; that doesn't excuse the bypass).

## #M0 — PER-TASK MODEL ASSIGNMENT (HARD RULE, 2026-05-06)
Don't pattern-match on principles ("orchestrate when possible") — match the EXACT command. The dispatch determines the model.

| Task | Tool + model |
|---|---|
| Inline code edit ≤5 LOC, only when fixing a CI failure I just caused | Me, current model |
| Code change >5 LOC, mechanical / pattern / fixtures | Dispatch — 3:3:3 split: codex (`--agent codex --mode danger --worktree --base main`), claude-headless (architectural / cross-file), gemini (tests, schema migrations, docs-near-code). NOT gemini for: cross-file refactor, security/concurrency, GH-auth, mass mechanical |
| Wiki/content writing | `delegate.py dispatch --agent gemini` (Gemini sub, unmetered) |
| Adversarial review of design / ADR / architecture | `delegate.py dispatch --agent claude --mode read-only --model claude-opus-4-7 --effort xhigh` (headless Opus, separate billing) |
| Q&A or single-shot review without need to commit | `ab ask-codex` / `ab ask-gemini --model gemini-3.0-flash-preview` for routine, `--model gemini-3.1-pro-preview` only for deep |
| Search / grep / "find me X" across files | `Agent` tool with `subagent_type: Explore`, `model: "haiku"` |
| Status check on running dispatches | Monitor API curl, never inline file scans |
| Memory / rules / Claude-owned text | Me, inline. Claude's brain = Claude's job. Never deflect to user. |

If I'm about to write code inline and it doesn't match the first row, STOP and dispatch instead. The dispatch script enforces worktree + commits — memory does not. Note: `--base main` not `--base origin/main` — runtime prepends `origin/` itself.

## #0J — LOCAL REFERENCE CORPUS IS RIGHT THERE — STOP ASKING FOR MORE (2026-05-06)
Before EVER asking the user for additional pedagogical material, check: `docs/references/private/` (ULP 1-00→4-00 + Ohoiko June book + 1000 words + 500 verbs, gitignored), `docs/references/textbooks-txt/` (committed), `data/textbooks/` (561 MB PDFs, gitignored), MCP `mcp__sources__search_text`. NEVER quote verbatim in pipeline outputs. User quote: "we have so many content, but it is never enough for you."

## #0I — DON'T STACK MICRO-DILEMMAS, DECIDE FOR THE USER (2026-05-04)
Compound decisions = ONE table + ONE recommendation, NEVER N parallel sign-off questions. Required shape: (1) state of play 1-3 sentences, (2) options table 2-3 rows max, (3) **MY RECOMMENDATION** with one explicit pick + why + reject worst by name, (4) "going to execute unless you stop me" + first action verb. A numbered "sign off on these N" list IS a menu — forbidden.

## #0H — MERGING PRs IS MY JOB (action bias)
Review each PR (body + diff + CI), merge if clean: `gh pr merge N --squash --delete-branch`. Don't ask, do it. Hold only for BLOCKING CI fails (advisory Gemini-Dispatch fails ≠ blocking). LEAD AND GUIDE: state next action + execute + report, don't present status + wait. Same applies to memory/rules/docs cleanup — don't deflect to user.

## #0G — NEVER REPORT ASYNC-TASK STATE FROM MEMORY (2026-05-08)
Before saying "task X is running / X just finished / X is at step Y", ALWAYS query `delegate.py status-or-fail X` or Monitor API `/api/delegate/active`. Memory of state from 2 minutes ago is wrong by default. Established 2026-05-08 after orchestrator reported bakeoff "Gemini mid-write" when it had finished.

## #0C — COLD-START VIA MONITOR API + HANDOFF CHAIN
`/api/state/manifest` → cached rules/session → `/api/orient` → inbox. NEVER read CLAUDE.md / rules / `session-state/current.md` directly. Cold-start: 75 KB → 778 bytes warm-cache. Before any multi-session topic, run `ls -lt docs/session-state/*.md | head -10` and read the chain — newest file alone is NOT enough; framings land 1-3 days back.

## #0B — USE THE MONITOR TOOL FOR EVENT STREAMS
`Monitor` tool: one stdout line → one notification, ~zero context cost. Use for v7_build.py JSONL events, `ab channel watch --follow`, any long-running command. NEVER poll with ScheduleWakeup loops or repeat tool calls — wait for `<task-notification>` or Monitor events.

## #0A — PUSH BACK ON UNCLEAR INSTRUCTIONS (TOP PRIORITY)
User is senior, time-poor, budget-sensitive. If instruction is short/vague, NEVER guess, NEVER default-act silently, NEVER present a menu. Required order: (1) State interpretation: "I read X as Y with constraint Z"; (2) Flag ambiguity dimension(s); (3) Propose concrete default: "Default would be [X]"; (4) Ask override on THAT ONE interpretation; (5) Execute if no override. WRONG: "Want me to A, B, or C?" / "What should I do next?" Push-back WELCOME. Silent compliance on a bad read is WORSE than a 2-line challenge.

## #0 — CLAUDE'S ROLE (refined 2026-05-10)
**Role:** orchestrator + adversarial reviewer + UI tester + memory/rules custodian. NOT primary coder — dispatch.
**Split: 3:3:3 Codex:Claude-headless:Gemini** across open coding (user-stated 2026-05-10, supersedes 6:4 from 2026-04-23). Routing target, not strict quota — pick by fit. Gemini = bounded tests, schema migrations, fixtures with semantic judgment, docs-near-code. NOT gemini for: ambiguous cross-file architectural rewrites, security/concurrency bugs, GH/rebase/auth-heavy work, mass mechanical pattern-application.
- **Inline that IS mine:** browser/UI testing, adversarial reviews via dispatch, hard-bug debugging through reasoning (not coding), brief writing, linguistic verification via `mcp__sources__*`, memory/rules/docs custodianship.
- **>50 LOC of non-test code inline?** STOP — dispatch instead.
- **DISPATCH CAP: 2 Claude + 2 Codex + 2 Gemini in flight.** Check `/api/delegate/active` before firing; queue brief if cap hit.
- User signals "claude usage is hot" if Anthropic budget tight — bias to Codex+Gemini.

## #1 — QUALITY ABOVE ALL
No heuristics when proper algorithm exists. No lowering thresholds. No "for now." Lesson 2026-03-28.

## WRITER + REVIEWER POLICY (updated 2026-04-26)
- **WIKI WRITER: Gemini ALWAYS** — `scripts/wiki/compile.py` defaults `--writer gemini`; never pass `--writer=claude`. Gemini sub unmetered.
- **Module writer in V7 reboot: PENDING** — Decision card `docs/decisions/pending/2026-05-06-writer-selection-codex-gpt55.md` proposes Codex/GPT-5.5; awaiting user `go`.
- **Codex is primary pipeline reviewer.** Gemini self-review OFF.
- **CLI gate:** Claude CLI ≥ 2.1.116 required (#1472).

## PR CI MONITOR
`Bash(command="gh pr checks N --watch --interval 10", run_in_background=True)`, then wait for notification. NEVER `for i in seq; do sleep` polling — `--watch` waits for pending.

## CODEX BRANCH-BASE VERIFICATION (until #1476 ships)
After Codex dispatch returns, verify branch isn't stale: `git -C .worktrees/<x> log --oneline HEAD..origin/main` (must be empty). If non-empty: rebase + force-with-lease. Common cause: orchestrator pushed to main between dispatch start and end.

## DISPATCH-BRIEF CHECKLIST
Codex/Claude brief MUST have these as EXPLICIT NUMBERED STEPS: (1) `git worktree add` setup, (2) file-level work, (3) test suite, (4) ruff, (5) commit conventional msg, (6) `git push -u origin`, (7) `gh pr create`, (8) NO auto-merge. Plus #M-4 preamble: brief MUST list the verifiable claims the work will produce + the deterministic tool for each + the output format that captures tool evidence (quote raw output, never "I checked X"). See `docs/best-practices/deterministic-over-hallucination.md`.

## PROMPT-ABLATION DISCIPLINE
Pipeline-prompt changes pilot on ≥3 seeded modules before bulk. Gradual: 0→1→3→10→full. Never direct-jump `--range 1 194`.

## BATCH COMMANDS — NEVER RUN, ONLY SUGGEST
DO NOT run `v6_build.py --range` or `--step all`. Only user runs builds. Heal: `--step publish --resume`. Review: `--step review --resume`. Lesson 2026-04-10: `--step all --resume` destroyed 40+ files.

## #2 — CONTEXT + SESSION DISCIPLINE
**Context cap:** 750K (`CLAUDE_CODE_AUTO_COMPACT_WINDOW`). **Handoff trigger:** 300K early signal | 400K handoff zone | 450K past target. Self-estimate runs 1.8× high — use the Bash one-liner to check actual.
- NEVER `/compact` (rewrites context, loses fidelity).
- NEVER `--resume`/`--continue` (1.117 auto-summarizes, cache miss).
- Diary handoff: `docs/session-state/YYYY-MM-DD-<slug>.md`.
- 14:00–20:00 CET PEAK = MINIMAL inline. Overnight = orchestrator-only, ALL execution dispatched.
- Subagents = 74% of token volume. Prefer inline. Batch into FEWER subagents.

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
- **PLUGINS:** `frontend-design`, `code-review`, `playground`, `pyright-lsp`. Use them.
- **PRE-COMMIT AUTO:** Done + tests pass → IMMEDIATELY (1) ruff (2) `/simplify` (3) Gemini review. User never reminds.
- **QUALITY GATE:** Every changed function needs a test. 80%+ on critical paths.
- **GH ISSUE HYGIENE:** After work, close if all ACs met, comment if partial.
- **EDUCATION NOT SOFTWARE:** Real learners use these. Build ONE module → verify pedagogy → next.
- **SEQUENCE:** One working e2e example FIRST. Never modify pipeline without tracing.
- **DIALOGUES:** From textbooks, not invented (#A2 genitive interrogation 2026-03-24).
- **WORD TARGETS:** 1.5× overshoot (4000 → 5500-6000). Easier to trim than expand.

## See Also (topic files in `memory/`)
- `gpt-5.5-rollout.md`, `agent-debug.md`, `data-inventory.md`, `cooperation-tooling.md`, `l1-uk-corpus-bootstrap.md`
- `textbook-research.md`, `textbook-exercises.md`, `reference_ukrainian_dictionaries_online.md`, `reference_awesome_ukrainian_nlp.md`
- `project_goals_and_frustrations.md`, `project-pitch.md`, `user_teachers_and_learning.md`, `wiki-knowledge-base-plan.md`, `fact-corrections.md`
- `feedback_*.md` — pre-V7-reboot lessons (Mar-Apr 2026), kept for reference; new feedback goes inline here
