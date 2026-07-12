# How We Work (Mandatory Workflow)

<critical>

## Cold-start sequence (do this first every session)

Use the Monitor API instead of reading files. A session with a known assigned
functional role opts into that role's bounded pointer-only cold start:

```python
from ai_agent_bridge.monitor_client import MonitorClient
boot = MonitorClient().bootstrap(role="quality")
  # boot["rules"].body     — condensed rules markdown
  # boot["session"].body   — condensed session summary
  # boot["research"].body  — role-scoped pointers only, if enabled
```

Generic or genuinely role-unknown startup stays pointer-free:

```python
boot = MonitorClient().bootstrap()
```

There is no hidden default role. `bootstrap()` remains the generic, silent
path; add `role="..."` only when the session already has that known assigned
functional role.

Shell equivalent:

```bash
curl -s http://localhost:8765/api/state/manifest         # ~1 KB index
curl -s http://localhost:8765/api/rules?format=markdown  # only if hash changed
curl -s 'http://localhost:8765/api/session/current?agent=orchestrator'  # only if hash changed
curl -s http://localhost:8765/api/orient                 # always-fresh, has meta
# Known functional role only: replace `quality` with the assigned role.
curl -s 'http://localhost:8765/api/knowledge/cold-start?role=quality'  # role-scoped pointers
# Generic or genuinely role-unknown session: skip the role-scoped request; remain pointer-free.
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'  # unread messages
```

### Project Research Registry — orchestrator dispatch duty

Cold-start awareness is not enough. Before **every** `delegate.py dispatch`, the
accountable orchestrator must classify the task from its issue/brief and record
one of these outcomes in the brief or orchestration note:

- **Scoped:** pass every known task dimension with `--research-role`,
  `--research-task-family`, `--research-track`, and repeatable
  `--research-owned-path`. These describe the task's functional context, never
  the provider or agent identity. The registry matcher is conjunctive: a missing
  dimension required by a record safely produces no match. Never invent a value
  to force a pointer; split a dispatch that spans incompatible single-value
  roles, families, or tracks.
- **Genuinely generic or unknown:** omit all `--research-*` flags and keep the
  dispatch pointer-free. This must be a deliberate classification, not the
  accidental result of forgetting the registry.

Example scoped dispatch fragment:

```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent codex --task-id quality-4952 \
  --prompt-file docs/dispatch-briefs/quality-4952.md --worktree \
  --mode danger \
  --research-role quality \
  --research-task-family difficulty-gate \
  --research-track core \
  --research-owned-path scripts/audit/text_difficulty.py
```

The injected block contains pointers only. A worker that relies on a record must
fetch it while the task is active with
`GET /api/knowledge/record/{id}?task=<task-id>`. A surfaced pointer is not proof
of consumption: do not claim research was used without attributed fetch evidence,
and do not fetch an irrelevant record merely to manufacture adoption. Before
final disposition, the orchestrator checks the task's consumption evidence and
the privacy-safe aggregate `/api/knowledge/monitor`; any relevant surfaced but
unconsumed pointer must be explained, not silently counted as adopted.

Classification is mandatory; delivery remains fail-open. A disabled or degraded
registry must not block the delegated task, and it does not justify fabricating
context or weakening the generic pointer-free contract.

**Do NOT read `CLAUDE.md`, `agents_extensions/shared/rules/*.md`, or
`docs/session-state/current.md` directly on cold start.** Those are
the source of truth the endpoints above serve. Reading them separately
costs 5+ tool calls and ignores the hash-based cache. If an endpoint
is unreachable (API server down), THEN fall back to files.

For Claude specifically, `.claude/rules/` now carries only a small API
pointer plus path-scoped rules. The canonical always-load rule set for
Claude is `/api/rules?format=markdown`; use the source files directly
only as the offline fallback above.

After a write that needs to be immediately visible (just-committed
change, just-filed issue), pass `?fresh=true` to `/api/orient`.

**Canary mint (orchestrator sessions, user go 2026-07-07):** after orientation,
freeze 8-10 anchors from the facts just gathered (origin/main SHA, open-PR numbers,
queue/corpus counts): `.venv/bin/python scripts/context_canary.py mint --facts
'<json {id,q,a} list>' --out .agent/canary-<stamp>.json`. Score FROM MEMORY (no
scrolling back) at ≥50% of the active model's window and before any handoff. Rot
evidence is PER-MODEL (Claude lane rotates: Opus 4.8 verified, Fable 5 improvised
10/10 @ ~500K, Sonnet 5 pending) — on a not-yet-canaried model this is mandatory.

## Merge policy — ready PRs must not sit (user directive 2026-07-07, #4703)

The repo setting `allow_auto_merge` is ENABLED (was the root cause of ready PRs sitting for
hours). Every lane: the moment a PR's review gate passes (cross-family review evidence, no
requested changes), run `gh pr merge <N> --auto --squash --delete-branch` — GitHub merges it
when CI settles, nobody babysits. Dispatched agents still do NOT self-enable auto-merge
(review gate first — unchanged). `--auto` waits for green and never bypasses blocking checks
(#M-0.5 semantics unchanged).

**Stream-scoped sweeps (user directive 2026-07-13 — parallel-stream chaos fix; supersedes the
2026-07-07 one-hour out-of-lane backstop for TRACK sessions).** Multiple streams run in parallel, so a
session's start/end sweep is **OWN-STREAM ONLY**: it may review, review-route, arm auto-merge, or merge
**only** PRs in its own stream.

**Stream membership is AUTHORITATIVE + FAIL-CLOSED.** A PR is *in-stream* iff its linked issue resolves
to the session's stream-epic in the issue→epic membership registry — `/api/issues/streams` (from
`scripts.orchestration.issue_stream_audit`). **Branch prefixes (`codex/`, `claude/`, `agy/`) are AUTHOR
lanes, NOT streams — never use them for membership.** If a PR does not resolve to exactly one
stream-epic there (no link, multiple/conflicting `Closes/Refs`, or not yet indexed), it is
**out-of-stream → hands-off** for every track session. Out-of-stream = another stream's PR → do NOT
shepherd, review-route, or arm auto-merge on it: **no time threshold, no exception.** Rationale: the old
one-hour timer could not tell an *abandoned* PR from an *owner-paused* one, so with parallel streams it
made two sessions grab the same PR, or one merge another live stream's paused PR.

**The cross-stream abandoned-PR net has exactly ONE owner — the INTEGRATION-OWNER ROLE** (default
holder: Codex-main; a ROLE, not a hardcoded session/model — the roster owns repo-wide queue +
integration + final merge judgment). Only that role sweeps out-of-stream PRs, and only ones sat green
(CI + review gate passed) idle for MORE THAN 1 HOUR. **To avoid a liveness gap** (a down role-holder
stranding a green PR forever), this net MUST run as a **scheduled integration sweep** owned by the role
— it must not depend on any interactive session being live. (Until that scheduled sweep is wired, the
role-holder runs it at session start/end — see follow-up.) Per-lane `--auto` merge already keeps
in-stream PRs from sitting, so this net is a rare safety valve, not the primary path.

## Two-tier handoffs (epic #1865 item #1, shipped 2026-05-11)

Thread rollover handoffs are separate from durable session records. When a
thread approaches context threshold, run
`.venv/bin/python scripts/orchestration/thread_handoff.py prepare --agent <name>`
and continue from `.agent/<name>-thread-bootstrap.md` plus
`.agent/<name>-thread-handoff.md`. Those files are gitignored local state.
Do **not** write `docs/session-state/current.md` or any other git-tracked
handoff file just to survive compaction.

Every new durable session handoff ships as **MD brief only** (user decision 2026-07-07 —
the HTML halves were not being read):

- **`docs/session-state/<date>-<slug>-brief.md`** (~2-5KB) — machine-readable, cold-start
  entry point. YAML frontmatter + bullet-list body. Agents AND the human read THIS.
- HTML companion ONLY on explicit request or for major milestone arcs — never by default.

**Cold-start rule:** after the Monitor API bootstrap above, use the agent-specific
session endpoint when you know your role:

```bash
curl -s 'http://localhost:8765/api/session/current?agent=claude'
curl -s 'http://localhost:8765/api/session/current?agent=codex'
curl -s 'http://localhost:8765/api/session/current?agent=gemini'
curl -s 'http://localhost:8765/api/session/current?agent=orchestrator'
```

`docs/session-state/current.md` is a git-tracked compatibility router, not a
scratchpad and not the context-threshold rollover mechanism. It keeps
`Latest-Brief: docs/session-state/current.orchestrator.md` for legacy API
compatibility and an `Agent-Handoff:` mapping for `current.<agent>.md`. Read
the router only to discover paths; detailed state belongs in the agent-specific
file. Do NOT read the `.html` unless the agent-specific handoff points you
there.

### Brief frontmatter schema (required fields)

```yaml
---
date: 2026-05-10                              # YYYY-MM-DD
session: "Evening — short title"              # human-readable session label
status: ok                                    # ok | warn | fail
detail: <date>-<slug>.html                    # paired HTML filename, relative to docs/session-state/
main_sha: 99d3844e9                           # short SHA at end-of-session
main_green: true                              # CI state on main
open_prs: 0                                   # count at end-of-session
active_dispatches: 0                          # count at end-of-session
merged_today: [1861, 1863, 1864]              # PR numbers
rejected_today: [1862]                        # PR numbers (closed without merge)
filed_today: [1860, 1863, 1865]               # issue + PR numbers filed
closed_today: [1762, 1860]                    # issues closed
in_flight: []                                 # list of {pr/issue/dispatch} still active
blocked: []                                   # list of {item, reason}
next_p0: "one-line description of next priority"
agents: [claude, codex, gemini]               # agents that participated
---
```

Optional/extensible fields are allowed (e.g. `ci_notes`, `worktrees_open`, `incidents`) but the required block above MUST be present for cold-start parsing.

### Brief body shape

After the frontmatter, the body is a **bullet-list summary**, NOT narrative. Recommended sections:

1. `## TL;DR` — 2-4 lines.
2. `## What shipped` — table of PR/issue with one-line "what".
3. `## What rejected` (if any) — short reason + lesson encoded.
4. `## Carry-over queue` — priority-ordered list of items NOT done.
5. `## Decisions encoded` — short bullets.
6. `## Pending decisions` (if any) — links to `docs/decisions/pending/*`.
7. `## Cold-start orientation for next agent` — explicit instructions to the next session.

Reserve all narrative, anecdotes, KPIs, and rich rationale for the `.html` companion. The brief is a state snapshot, not a story.

### Pair authoring rule

Brief and HTML are authored together in the same orchestrator turn. Never ship one without the other for sessions going forward.

Every approved compatibility-router update to `docs/session-state/current.md`
MUST keep the top-level `Latest-Brief:` marker and the `Agent-Handoff:` mapping
parseable. Non-orchestrator agents update only
`docs/session-state/current.<agent>.md` unless a task explicitly authorizes a
router update. The SessionStart hook no longer reads this router by default;
set `SESSION_HANDOFF_ALLOW_GIT_ROUTER=1` only for legacy compatibility tests or
an explicitly approved router-oriented cold start.

### Backfill policy

Older `current.md` rows are HTML-only. Backfill is OPTIONAL — only worth it if a future thread needs to re-pickup that session. The cold-start fallback handles the missing-brief case.

## Scoped queries — call the API instead of filesystem spelunking

When you need deterministic answers about a specific module / range /
worktree, use these endpoints instead of grepping `orchestration/`,
`status/`, or `review/` directly. They are the source of truth for
agent-side reasoning.

| Question | Endpoint |
| --- | --- |
| What's module `{slug}` doing right now? | `GET /api/state/module/{track}/slug/{slug}` |
| Give me the dashboard for modules N..M on {track} | `GET /api/state/range/{track}?start=N&end=M` |
| Which files would `--force` delete for this module? | `GET /api/artifacts/{track}/{slug}/force-preview` |
| Classify every file tied to this module (source/generated/published/stale) | `GET /api/artifacts/{track}/{slug}/files` |
| Latest main + style reviews + "reviewer gaming" flag | `GET /api/artifacts/{track}/{slug}/review-snapshot` |
| Does state.json agree with audit / reviews / published MDX? | `GET /api/artifacts/{track}/{slug}/drift` |
| Can I ship this module? (every gate green) | `GET /api/artifacts/{track}/{slug}` |
| Aggregate list of ship-ready modules | `GET /api/artifacts/ship-ready[?track=...]` |
| Is the public site actually reachable? | `GET /api/site/health` |
| Recent GH Pages deployments | `GET /api/site/deployments` |
| Which worktrees exist and which branches are they on? | `GET /api/worktrees` |
| Open issues grouped by category, with supersede hints | `GET /api/issues/map` |
| Per-agent auth mode (Gemini subscription vs API) | `GET /api/runtime/auth` |

**Rule of thumb:** if you're about to run `ls`, `cat`, `grep`, or
`find` against `curriculum/` / `orchestration/` / `review/` /
`status/` / `.git/worktrees/` — check the table above first. A
single API call almost always returns the structured answer you
were trying to reconstruct.

**Full reference:** [`docs/MONITOR-API.md`](../../docs/MONITOR-API.md).

### Don't confuse `claude agents` with active-dispatch state

The Claude Code v2.1.139 `claude agents` command is a **static
configuration lister**, not a live-session view. Its output lists
loaded agent DEFINITIONS (e.g. `curriculum-orchestrator`, `Explore`,
`Plan`, `claude`) and labels them "active" — meaning "loaded into the
current process," NOT "running a session." Verified 2026-05-12 against
Claude Code 2.1.139 (`claude agents --format json` is rejected with
`unknown option`; only the plaintext lister exists).

To check ACTIVE DISPATCHES, use `/api/delegate/active` (Monitor API).
To check OPEN PRs, use `gh pr list`. To check IN-FLIGHT WORKTREES,
use `/api/worktrees`. `claude agents` does not replace any of these.

(Encoded 2026-05-12 after queue item #2 in `2026-05-12-cold-start-followups-brief.md` was filed under the wrong assumption.)

---

## Work intake — stream epics (#4708, binding for ALL orchestrators incl. Codex UI)

Every OPEN issue belongs to **exactly one stream epic**. The registry is
`scripts/config/issue_streams.yaml` (streams → epic numbers; mirrored in
`docs/WORKSTREAMS.md` § Streams). This is how orchestrators stay on track and schedule:

- **Cold start**: your queue = YOUR stream's epic checklist/sub-issues, not the global
  issue list. Check `/api/issues/streams` (or the session-setup 11b warning) for drift.
- **Creating an issue**: link it to its stream epic AT CREATION — native sub-issue
  (preferred) or a `#N` checklist line in the epic body. An unlinked issue is an ORPHAN
  and gets flagged at every agent's cold start until adopted.
- **Closing**: when a PR fixes an issue, CLOSE it with evidence (auto-close keywords are
  fine, but verify — `Fixes #N` closes the whole issue even when scope remains; split
  remainders into a new linked issue FIRST).
- **New stream?** Only with a new epic + a registry entry in the same PR — streams are
  deliberate, not emergent.
- Auditor: `.venv/bin/python -m scripts.orchestration.issue_stream_audit` (`--check` for
  gates, `--migrate` to convert body references into native sub-issues).

## Mandatory task workflow

Every task follows this workflow. No exceptions for non-trivial changes.

1. **Create GH issue** — describe the problem, draft a plan, **link it to its stream epic** (see Work intake above)
2. **Adversarial review of plan** — send to Gemini, incorporate feedback
3. **Finalize ACs** — update issue with concrete acceptance criteria
4. **Implement** — work through ACs one by one
5. **Verify all ACs** — every AC checked and documented on the issue
6. **Adversarial review of implementation** — send code to Gemini, fix findings
7. **Close** — only when all ACs pass and review is clean

**Goal-Driven Execution (step 4)**: Transform imperative tasks into verifiable goals. For multi-step work, state a plan with explicit verification at each step:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```
Strong success criteria enable independent looping. Weak criteria ("make it work") require constant clarification.

**Skip plan review** (step 2) only for trivial changes (< 50 lines, config/typo fixes).

**Adversarial review command** (steps 2 & 6). Always use `--model gemini-3.1-pro-preview`. Document findings on the GH issue.
```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Adversarial review for #NNN. Read {path}." \
  --task-id issue-NNN --model gemini-3.1-pro-preview
```

## Channel bridge (#1190, shipped 2026-04-12)

The agent bridge now supports **topic-scoped channels** — preferred
for sustained multi-turn conversations because they eliminate the
need to re-paste project context on every round.

**Five seeded channels**: `shared`, `pipeline`, `content`,
`architecture`, `reviews`. Every post auto-prepends:
1. The channel's pinned `context.md` (via the include chain, so
   `shared` is merged into everything)
2. A Monitor API snapshot of volatile project state
3. Recent channel history, character-budget truncated

**Preferred for:** code reviews (multi-round), design debates,
cross-agent discussions, anything that needs pinned context.
**Not preferred for:** one-off drive-by questions — use `ask-*` for
those.

**Quick reference**:
```bash
  # List / inspect
ab channel list
ab channel info pipeline
ab channel tail reviews -n 20
ab channel tail reviews --thread THREAD_ID

  # Post (short form — single recipient)
ab p reviews gemini "quick question about module X"

  # Post (long form — multi-recipient, threading, parent/corr ids)
ab post reviews "Review of #NNN" --to gemini,codex --parent MSG_ID

  # Multi-agent bounded discussion
ab discuss architecture "Should we extract the V6 god object?" \
    --with claude,gemini,codex --max-rounds 2
```

`ab discuss` runs rounds in parallel via ThreadPoolExecutor,
short-circuits when all agents end their response with `[AGREE]`,
and caps at 4 rounds. Default: 2 rounds, 1 agent. The transcript
lands in `channel_messages` with proper `parent_id` threading so
you can tail it later with `ab channel tail --thread`.

**Web dashboard**: `http://localhost:8765/channels.html` (localhost
only, read + post).

**Full docs**: `docs/best-practices/agent-bridge.md`.

The legacy `ask-gemini` / `ask-claude` / `ask-codex` commands are
NOT deprecated — they stay alive for one-shot delegations. Use
channels for anything that will have >1 turn.

**Why**: GH issues are persistent memory. Without them, context is lost between sessions and work gets repeated or silently broken.

**Issue discipline (coding issues)**:
- **Never leave half-done.** If you open it, finish it. If you can't finish it now, document exactly where you stopped and what remains.
- **Never close unless ALL acceptance criteria are verified.** Partial completion = still open.
- **Aim to fully resolve and close.** Open issues are debt. Minimize them aggressively.
- **The human manages content generation issues.** Claude owns coding/infrastructure issues. But proactively remind when it's time to start building a new track or batch — initiative is welcome.

**Proactive issue hygiene**: At the start of each session, check open coding issues. Prioritize, resolve, close — don't let them go stale.

</critical>
