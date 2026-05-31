# Current - Codex orchestrator handoff (2026-05-31T08:15Z)

Latest-Brief: docs/session-state/current.orchestrator.md

> Handoff-only update. Treat `origin/main` and this file as authoritative.

## Role / Direction

- Codex is the orchestrator and sidekick for GitHub issue memory, agent bridge
  awareness, A1 golden learner journey, tooling, infra, and tech debt.
- BIO track is fully owned by the BIO orchestrator (Claude). Do not interfere
  with BIO PRs/content/delegates unless Claude explicitly asks Codex for help.
- When a track orchestrator is promoted, let that orchestrator run the track.
  They can call headless Codex when needed; Codex main stays organized around
  repo-wide orchestration and non-BIO work.
- Use the strong-agent mix actively for bounded work:
  - Codex: orchestration, integration, code changes, final merge judgment.
  - Claude: BIO ownership, deep PR/path review via `review-deep`, sensitive
    reasoning.
  - Cursor: implementation/content rebuild work through delegate/bridge.
  - DeepSeek: cheap code/content review and deterministic triage via delegate.
- Stop using Gemini for reviews until the user says otherwise. Gemini review
  checks are currently unreliable/noisy and should not provide merge confidence.
- Do not delete or pause old automation unless explicitly instructed.

## Git State

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Main checkout branch: `main`
- Current authoritative remote head at handoff:
  `836526d165 feat(api): surface bridge activity for orchestrators`
- Main checkout has unrelated dirty user/Claude files; do not revert:
  - `docs/bio-epic/CLAUDE-DRIVER-HANDOFF.md`
  - `scripts/deploy_prompts.sh`
  - `docs/bio-epic/phase2-word-target-defects-2026-05-31.txt`
  - `docs/session-state/2026-05-30-pr2460-bak-fix-inflight.md`

## Completed Since Prior Handoff

- #2459 merged: BIO Claude driver handoff refresh.
- #2450 merged: agent-specific thread handoff routers. `docs/session-state/current.md`
  is now a router; detailed state lives in `current.<agent>.md`.
- #2447 merged: stressed plan section heading gate.
- #2478 merged: `GET /api/comms/agent-activity` read-only bridge activity
  endpoint plus manifest discovery. Local API at `127.0.0.1:8765` was still
  serving the old process when checked, so restart it before expecting the new
  endpoint locally.

Note: #2478 deterministic CI passed and local Gemini diff review had no
findings, but the user has since corrected policy: do not use Gemini for review
confidence going forward.

## Active Delegates

Check with:

```bash
curl -sS http://127.0.0.1:8765/api/delegate/active
```

Active at handoff time:

- `review-2477-20260531080952` - Claude Opus review-deep for BIO PR #2477.
- `bio-rebuild-blockI1` - Cursor, running before this handoff.
- `bio-rebuild-blockG7` - Cursor, running before this handoff.
- `review-pr2476-plan-ci` - DeepSeek v4 flash read-only triage for BIO PR
  #2476. Dispatched before the BIO boundary correction; let Claude decide
  whether to use or ignore the result.
- `review-pr2474-plan-ci` - DeepSeek v4 flash read-only triage for BIO PR
  #2474. Dispatched before the BIO boundary correction; let Claude decide
  whether to use or ignore the result.

Do not assume the bridge `status` command is authoritative for delegates; use
`/api/delegate/active` and task logs/state.

## BIO Boundary

Open BIO PRs remain, but they are Claude/BIO-orchestrator owned. Codex should
not triage, fix, merge, or route BIO content PRs unless Claude asks. Awareness:

- #2477 deterministic checks clean; Gemini review canceled; Claude review
  running.
- #2476 has real `Curriculum Plans` failure:
  `hryhorii-khomyshyn` content outline sum 4000 under word target 5200.
- #2474 has real `Curriculum Plans` failure:
  `danylo-shcherbakivskyi` word target under config, plan 3400 vs config 5000.
- #2473 and #2471 have real `Curriculum Plans` failures and active Cursor BIO
  rebuild delegates.
- #2475, #2472, #2470, #2469, #2468 appeared deterministic-clean except
  Gemini review failure/cancellation at last check.

Let Claude/BIO orchestrator handle these.

## Agent Bridge Routes

Use these instead of Gemini:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-deep <PR-or-path> --effort high
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude "<prompt>" --task-id <id> --review
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-cursor - --task-id <id>
.venv/bin/python scripts/delegate.py dispatch --agent deepseek --model deepseek-v4-flash --mode read-only --task-id <id> --prompt '<prompt>'
```

DeepSeek is wired through Hermes:

- `deepseek-v4-flash`: cheap code/PR review and CI triage.
- `deepseek-v4-pro`: content review / VESUM-heavy lanes.

Cursor has broker/delegate support but no PR-comment auto-posting wrapper.
Claude `review-deep` is the explicit PR/path review wrapper.

## A1 Direction

Codex focus now: A1, tooling, infra, tech debt, and GitHub issues.

Do not treat m20/m21/m22 as product strategy. They are support/validation
items. Product direction:

- Start A1 from the beginning.
- Build the learner experience as the product spine.
- First slice is A1 M1-M7 safe onboarding / first contact.
- Fix pipeline/gates only when they block excellent learner content.

A1 M1-M7 sequence:

1. `sounds-letters-and-hello`
2. `reading-ukrainian`
3. `special-signs`
4. `stress-and-melody`
5. `who-am-i`
6. `my-family`
7. `checkpoint-first-contact`

## Restart Commands

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git status --short
git log --oneline -8 --decorate --no-merges
curl -sS http://127.0.0.1:8765/api/delegate/active
gh pr list --state open --json number,title,headRefName,mergeStateStatus,statusCheckRollup,url,updatedAt,isDraft,reviewDecision --limit 20
```

## Guardrails

- Use `.worktrees/dispatch/<agent>/<task>/` for implementation.
- Do not edit generated status/audit/review artifacts, linter configs, or
  `.python-version`.
- Every commit must carry an `X-Agent` trailer.
- Use `.venv/bin/python`, not `sys.executable` or system Python.
- Do not revert unrelated dirty files in the main checkout.
