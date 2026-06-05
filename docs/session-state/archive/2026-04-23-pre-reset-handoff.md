# Session Handoff — 2026-04-23 /reset (late morning CET)

> User is doing `/reset` not a full restart. Conversation context clears
> but running processes, Monitors, dispatches, worktrees all survive.
> Next session inherits state via this file + Monitor API.

## Cold-start — first 3 commands

```bash
# 1. Current dispatches + PRs + issues
curl -s http://localhost:8765/api/orient
.venv/bin/python scripts/delegate.py list | jq '.[] | select(.status == "running")'
gh pr list --state open
```

Don't re-read `CLAUDE.md` / rules files directly — `/api/state/manifest`
serves a condensed, hash-cached version. See `workflow.md` rule.

## Dispatches alive RIGHT NOW (4 total, strict max-2-per-agent)

| Task ID | Agent | What | Hard timeout |
|---|---|---|---|
| `claude-1431-v2-shared-contract` | Claude opus 4.7 xhigh | Shared contract (writer+reviewer sync) + smoke a1/colors build | 14400s |
| `scale-checkpoint-first-contact-review-and-lock` | Claude opus 4.7 xhigh | A1 slug review-and-lock | 5400s |
| `codex-1434-compiler-attribution` | Codex gpt-5.4 high | **BLOCKER** — fix bare-chunk-ID leak in sources.yaml. User waiting. | 5400s |
| `scale-special-signs-review-and-lock` | Codex gpt-5.4 high | A1 slug review-and-lock | 5400s |

**STRICT RULE**: max 2 Claude, max 2 Codex parallel. User got rate-limited
earlier today because I fired 8 Codex at once. DO NOT exceed 2 per agent.

## Queue — next Codex dispatches (fire one at a time as slots free)

File: `batch_state/codex-dispatch-queue.md`. Priority order:

1. `codex-1286-review-transport` — brief `.worktree-briefs/codex-1286-review-transport.md` — 3600s
2. `codex-1403-prevent-auto-merge` — brief `.worktree-briefs/codex-1403-prevent-auto-merge.md` — 3600s
3. `codex-compile-strip-mcp-warning` — brief `.worktree-briefs/codex-compile-strip-mcp-warning.md` — 2700s
4. `codex-monitor-api-locks` — brief `.worktree-briefs/codex-monitor-api-lock-state.md` — 3600s
5. `codex-1268-gemini-rewrite-budget` — brief `.worktree-briefs/codex-1268-gemini-rewrite-budget.md` — 2700s
6. `codex-1395-git-cleanup-endpoint` — brief `.worktree-briefs/codex-1395-git-cleanup-endpoint.md` — 3600s

**Cleanup before each re-dispatch** (worktrees/branches stale from earlier):
```bash
git branch -D codex/<TASK_ID> 2>/dev/null
git worktree remove .worktrees/<TASK_ID> --force 2>/dev/null
rm -f batch_state/tasks/<TASK_ID>.json batch_state/tasks/<TASK_ID>.result
```

**Dispatch template:**
```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent codex --model gpt-5.4 --effort high \
  --task-id <TASK_ID> \
  --worktree .worktrees/<TASK_ID> \
  --mode danger \
  --prompt-file .worktree-briefs/<BRIEF>.md \
  --hard-timeout <TIMEOUT>
```

## Queue — next Claude A1-lock dispatches (when scale-who-am-i completes)

A1 slugs still unlocked (43 remaining after current 2 in flight finish):

```bash
comm -23 \
  <(ls curriculum/l2-uk-en/plans/a1/*.yaml | xargs -n1 basename | sed 's/.yaml//' | sort) \
  <(grep -l "lifecycle: locked" curriculum/l2-uk-en/plans/a1/*.yaml | xargs -n1 basename | sed 's/.yaml//' | sort)
```

Next slugs in curriculum order after special-signs + who-am-i:
`checkpoint-first-contact`, `things-have-gender`, `what-is-it-like`,
`how-many`, `this-and-that`, `many-things`, ...

**Dispatch pattern** (alternate Claude / Codex to balance load):
```bash
NEXT=<slug>
sed "s/colors/$NEXT/g" .worktree-briefs/scale-colors-review-and-lock.md > ".worktree-briefs/scale-${NEXT}-review-and-lock.md"
.venv/bin/python scripts/delegate.py dispatch \
  --agent claude --effort xhigh --model claude-opus-4-7 \
  --task-id "scale-${NEXT}-review-and-lock" \
  --worktree ".worktrees/scale-${NEXT}" \
  --mode danger \
  --prompt-file ".worktree-briefs/scale-${NEXT}-review-and-lock.md" \
  --hard-timeout 5400
```

## Monitors armed (re-arm if timed out)

| ID | Watches | On fire |
|---|---|---|
| `bg8h7qwl3` | #1434 compiler fix | Verify AC → merge → dispatch #1435 backfill + refill codex slot |
| `bovx985hn` | special-signs lock | Merge PR → dispatch next from codex queue |
| `bpup3xgm7` | #1431 v2 contract+smoke | Read result → merge or write infeasibility brief |
| `bq7bwd0rx` | checkpoint-first-contact lock | Merge PR → dispatch next A1 slug (Claude) |

Monitor timeout = 1h; re-arm with same watch command if still running.

## Binary outcome pending — #1431

**Project-life question.** `claude-1431-v2-shared-contract` running now
tests if AI-only pipeline can produce a passing A1 module (colors):

- **PASS** (all 9 dims MIN ≥ 8) → pipeline viable, scale overnight
- **FAIL** (proper attempt) → write `docs/decisions/2026-04-23-ai-only-build-infeasible.md`, user decides

Agent scope:
1. Shared contract `scripts/build/contracts/module-contract.md` — single source of truth; both writer + reviewer cite it
2. Reviewer persona moderation — A1 immersion calibration + phrase allow-list
3. Writer retrieval for dialogues via `search_sources`
4. Writer plan adherence
5. **Exemplar requirement** (user architectural addition, GH #1431 comment) — any dim < 8 must emit `<exemplar>` block demonstrating target

## User's canonical AC for #1434

PR is done only when this command produces a sources.yaml with ZERO `type: unknown` entries:

```bash
.venv/bin/python scripts/wiki/compile.py --track b2 --slug academic-writing --force
```

Every `[S*]` entry must have real attribution:
- `file:` NOT a bare chunk ID (no `file: S2318`)
- `type:` one of textbook / literary / external / ukrainian_wiki / wikipedia / dictionary
- YouTube chunks include URL with `?t=<ts_start>s`

When #1434 merges → dispatch #1435 (backfill for ~227 existing wikis).

## PRs merged this session (12)

1421 (per-dim reviewer), 1422 (my-day lock), 1423 (hey-friend lock),
1424 (shopping lock), 1425 (holidays lock), 1426 (auth test fix 1),
1427 (ukrainian_wiki embeddings), 1428 (auth test fix 2),
1430 (convergence budget fix), 1432 (reading-ukrainian lock),
1433 (stress-and-melody lock), 1436 (who-am-i lock).

## Open issues that matter

| # | Title | Status |
|---|---|---|
| #1431 | BLOCKER: Prove AI-only v6 pipeline can pass a1/colors | In-flight |
| #1434 | BLOCKER: compiler.py source attribution | In-flight |
| #1435 | Backfill attribution across 227 existing wikis | Queued (depends on #1434) |
| #1286 | Stabilize codex-tools review transport | Queued |
| #1403 | Prevent danger-mode auto-merge | Queued |
| #1395 | /api/git/cleanup endpoint | Queued |
| #1268 | Cap Gemini rewrite-block timeout | Queued |

## A1 lock state

**12/55 locked.** 2 in flight will bring it to 14.

Locked: at-the-cafe, food-and-drink, my-family, sounds-letters-and-hello,
colors, my-day, hey-friend, shopping, holidays, reading-ukrainian,
stress-and-melody, who-am-i.

In flight: special-signs (Codex), checkpoint-first-contact (Claude).
Next in order after those: things-have-gender, what-is-it-like, how-many.

Count live: `grep -l "lifecycle: locked" curriculum/l2-uk-en/plans/a1/*.yaml | wc -l`

## Wiki compile state

- MCP sources server running (port 8766), api running (8765), starlight running (4321)
- User's shell: `GEMINI_AUTH_MODE=subscription` set, `GEMINI_API_KEY` unset
- 1 B2 article compiled (`academic-writing.md`) — has the #1434 attribution bug in its sources.yaml
- **User paused B2 batch compile until #1434 ships** — do NOT resume until user OKs

## Operational protocols user stated today (HOLD STRICTLY)

1. **Max 2 Claude + max 2 Codex parallel.** Not 8. Not 4. Two per agent.
2. **Smoke-test any unfamiliar CLI flag before firing N dispatches.** Today I burned 7 dispatches with wrong model name.
3. **No auto-merge ever.** User merges. INCIDENT #1403 (and this session) prove agents can't be trusted with the keys.
4. **Never lower MIN-score gate** on reviewers.
5. **Never publish a failing module's .mdx.**
6. **Read content, don't pattern-match.** If judging a wiki/article: cite specific lines, verify vocab against VESUM, verify citations against sources.yaml. No stamp-approval.
7. **No A/B/C option menus.** Pick one, act, report. User pushes back if wrong.
8. **Tight responses.** Long structured output = performance of thoroughness, not thoroughness itself.
9. **Active management, not silence.** When monitor fires, immediately refill that agent's slot from the queue. Don't wait for user prompt.
10. **Russian-pattern operational failure is a real risk** — bureaucratic stamping, menu-offering, volume substitution, unverified-assumption-then-scale. This project exists to oppose that. Stay substantive.

## What next session does first (action list, not options)

1. Cold-start: `curl orient`, `delegate list`, `gh pr list`
2. Re-arm any timed-out monitors for the 4 running dispatches
3. When `#1434` merges → run `compile.py --track b2 --slug academic-writing --force` locally to verify user's canonical AC, then dispatch `#1435` backfill
4. When any Codex slot frees → dispatch next from `batch_state/codex-dispatch-queue.md`
5. When any Claude A1-lock slot frees → dispatch next unlocked A1 slug
6. When `#1431 v2` completes → read PR carefully (no stamp-approval), verify against ACs, report honestly to user with per-dim scores

## Environment sticky state

User's terminal has:
- `GEMINI_AUTH_MODE=subscription`
- `GEMINI_API_KEY`, `GOOGLE_API_KEY` both unset

If a /reset kills the terminal these are lost — user needs to re-export.

## Services

All 3 running and must stay running:
- `sources` MCP (port 8766) — wiki compile + module writer depend on this
- `api` (port 8765) — monitor API
- `starlight` (port 4321) — user views built modules here

Restart if down: `./services.sh restart <service>`.
