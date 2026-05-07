# Kubedojo Decision Graph paradigm + persistent listener architecture — follow-up actions

> **Status update 2026-05-07 evening:**
> - PR #1781 MERGED (HARD STOP RULE)
> - Bakeoff retry v2 RUNNING (`bakeoff-2026-05-07-retry-2`, ~50min in at this update)
> - Issue #1782 FILED (persistent agent listeners umbrella)
> - Tier-2 warm-cache fix DISPATCHED (Codex `tier-2-warm-cache`, fires PR for #1782 sub-task 1)
>
> Original direction 2026-05-07 morning: "save these and do it after the bakeoff."
> Refined direction 2026-05-07 evening: "prepare th tasks and do 2 right away." → Tier-2 dispatched immediately; everything else still queued behind bakeoff completion.

## Context

The kubedojo team (sister project) compared their dashboard to ours and pitched
inverting `channels.html` from chat-primary to **Decision Graph**-primary, with
chat as a toggle. They also offered to upstream their D3 (Decision Graph) PR
to us after they implement it in their own repo.

3-way agent review converged on a **modified version**:

- ✅ Decision Graph as a **TOGGLE** that auto-engages when a thread has ≥2
  distinct `agent_family` responses with `[AGREE]`/`[OPTION]`/`[OBJECT]`/
  `[DEFER]` markers. Chat stays primary.
- ✅ D4 (decision-lineage backlink scanner) is paradigm-independent and ships
  standalone, ahead of any UI work.
- ✅ Decision Graph proposal warrants its own ADR — distinct category from
  the existing pending Multi-UI ADR (which is about identity / claims / blob
  storage, not deliberation visualization).

Codex did real evidence-gathering (file:line refs + DB statistics); Gemini
rubber-stamped without citations. Codex's pushback is what shaped the final
position.

## Codex's data (verbatim, verifiable)

**Channel marker-thread density** (from local `channel_messages` snapshot
2026-05-07):

| Channel | Marker threads | Total threads | % |
|---|---:|---:|---:|
| `architecture` | 32 | 39 | 82% |
| `pipeline` | 2 | 11 | 18% |
| `reviews` | 19 | 83 | 23% |

Confirms: the inversion would be wrong for ~75-80% of our channel traffic.
Toggle is the right paradigm.

**Round-reply body sizes** (architecture channel):
- Average: 2367 chars
- Maximum: 8349 chars

Confirms: 3-column body-first grid is unreadable. Codex's framing of
**"outline-first matrix + side drawer"** is the right shape — see action C
below.

## The 4 queued actions

### A — File issue: D4 lineage backlink scanner

**Scope**: Standalone read-only tool that walks `docs/decisions/*.md` + scans
`git log` to populate "Influenced" backlinks per decision.

**Improvement over my initial pitch** (per Codex): scan multiple alias forms,
not just literal ADR ID:

- Filename (e.g. `2026-05-06-multi-ui-channel-participation`)
- Title (from `# heading` line)
- `ADR-00N` shorthand
- Decision IDs (whatever convention the file declares)
- PR references that touch the file path

**Output**: JSON/API endpoint + console-printable summary. UI consumption
deferred. Estimated ~150-200 LOC.

**Issue title**: `Add decision-lineage backlink scanner (multi-alias) with
JSON/API output`

**Acceptance criteria**:
1. Walk `docs/decisions/**/*.md` and emit one record per file
2. For each file, scan `git log --all -p` for commits that touched the file
   path OR mention any of the alias forms above
3. Output JSON: `{decision_id, file_path, aliases[], commits[], prs[],
   first_cited_at, last_cited_at}`
4. Expose via Monitor API endpoint `/api/decisions/lineage` (read-only)
5. CLI: `.venv/bin/python scripts/audit/decision_lineage.py [--decision-id X]`
6. Add a test fixture with 2 decision files + 3 fake commits referencing
   them in different alias forms, assert the scanner finds all 3
7. Update `docs/SCRIPTS.md` with the new script

**Reference files**:
- `docs/decisions/INDEX.md` — existing decision index
- `scripts/audit/check_decisions.py` — existing decision-staleness checker
  (use the same module conventions)
- `docs/decisions/pending/README.md` — pending-decision protocol

### B — File 3 infrastructure bugs surfaced by the failed `ab discuss`

**B.1 — `ab discuss` truncates root message out of round-2+ prompts**

The fresh-Claude subagent in the failed discussion correctly diagnosed this:
> "In round 2 my prompt shows `... [15 older messages omitted] ...` — the root
> message was truncated out entirely from my view. With `needed_history = 1 +
> N*max_rounds + 10` (see `scripts/ai_agent_bridge/_channels_cli.py:1256`),
> the design is to preserve the root, so the truncation happened at the
> prompt-render boundary, not from history sizing."

**Symptom**: Round 2+ agents in any `ab discuss` operate on a brief that has
the original question stripped out, especially in busy channels (architecture
has 157 prior messages → high truncation pressure).

**Fix scope**: in `_channels_cli.py:1256` (or the prompt-render boundary
nearby), pin the root message into the prompt unconditionally — it's the
question, it must always be visible. Do the truncation against history,
not the root.

**Test**: discussion with N=4 max-rounds in a channel with 200+ prior msgs;
assert root message appears in round-4 prompt verbatim.

**B.2 — Fresh Claude subprocess in `ab discuss` is instantiated in plan
mode WITHOUT writer tools**

**Symptom**: Round-1 and round-2 Claude replies in the failed discussion
were both "I have a tooling problem" complaints — Claude correctly refused
to fake responses, but couldn't engage with the brief.

**Available tools observed**: `Glob`, `Grep`, `LSP`, `Read`, MCP `sources`,
MCP `claude_ai_Google_Drive`. Missing: `Write`, `Edit`, `Bash`, `Agent`,
`ExitPlanMode`, `AskUserQuestion`.

**Two possible fixes** (investigate which is right):
1. Don't put discuss subagents in plan mode (they're commenting, not planning)
2. If plan mode is intentional, attach `Write` + `ExitPlanMode` so the
   subagent can complete the workflow

**Reference**: claude subagent's round-2 reply has full diagnosis with file
refs (preserved in `architecture` thread `1c1b5d54966742ffacd1bf60e0893c1c`).

**B.3 — `ask-codex` / `ask-gemini` defaults `--from` to "gemini"**

**Symptom**: When Claude (this orchestrator) calls `ask-codex` without
`--from claude`, the broker logs `From: gemini → To: codex`. Cosmetic but
misleading for telemetry / channel attribution / future audit reports.

**Fix**: detect caller identity from environment (or require explicit `--from`)
instead of defaulting to "gemini".

**Issue title**: `ab discuss + ask-* infrastructure bugs (root truncation,
plan-mode tool subset, --from default)`

### C — Decision Graph ADR

**Decision required FIRST**: separate ADR vs fold into existing pending
Multi-UI ADR's Strand 6?

**Codex's threshold rule**: ADR is needed if the work changes "the dashboard's
primary information architecture, marker semantics, or API contract"
([docs/decisions/pending/README.md:203](../decisions/pending/README.md)).

**Application**: Decision Graph view changes (a) primary IA — adds a new
view alongside chat, (b) marker semantics — auto-detects convergence from
`[AGREE]`/`[OPTION]`/`[DEFER]` patterns. Both criteria met → **separate
ADR right**, not Strand 6 fold.

**The existing Multi-UI ADR Strand 6** is "claim status, visible expiry,
attachment rendering, capability badges, fallback identity visibility" —
that's about multi-UI identity, not deliberation visualization. Different
category.

**Recommended ADR scope**:
- File: `docs/decisions/pending/2026-05-XX-decision-graph-view.md`
- Status: PROPOSED
- Q1: When does Decision Graph view auto-engage? (Marker-density threshold,
  participant-count threshold, manual toggle override)
- Q2: Layout — outline-first matrix per Codex (rows=rounds, cols=agent_family,
  cell=marker + first-line summary, click→side drawer with full body)
- Q3: Marker parsing semantics — what counts as `[AGREE]`/`[OPTION]`/
  `[OBJECT]`/`[DEFER]`? Case-sensitive? Embedded in body or required at end?
- Q4: Convergence detection — when is a thread "decided"? (All agents
  `[AGREE]` in same round?)
- Q5: Side drawer UX — single-message vs full-thread transcript? Modal vs
  pinnable rail?
- Q6: Decision provenance — does Decision Graph link out to ADR file when
  one exists? (Hooks into D4 from action A)

**3-agent review** before user signoff (per workflow rule). Use `ab discuss
architecture` ONLY AFTER B.1 (root truncation) is fixed — otherwise round-2
loses the brief again.

**Issue title (for tracker)**: `EPIC: Decision Graph view ADR + implementation`

### D — Reply to kubedojo team

**When**: After A is filed AND C ADR has user direction.

**Content shape**:
- Acknowledge their analysis (chat shell parity, paradigm pitch)
- Accept their offer to upstream D3, with constraints:
  - We want toggle, not primary inversion (data: 18-23% marker density on
    non-architecture channels)
  - We want outline-first matrix layout (data: 2367-char avg / 8349-char
    max round bodies make body-first grid unreadable)
  - We will implement D4 ourselves (multi-alias scanning, JSON/API output)
- Confirm they take from us: per-domain `scripts/api/*_router.py` split,
  delta-rendering, monotonic fetch counter, post-form-as-`agent:"human"`
- Pointer to our pending Decision Graph ADR (link once C is filed)

**Channel**: their preferred (probably their issue tracker or a shared
channel — TBD).

### E — Tier-2 warm-cache fix for `ab discuss` (DISPATCHED 2026-05-07 evening)

**Status:** in flight as Codex dispatch `tier-2-warm-cache` (PID 34738 at dispatch
time). Closes sub-task 1 of #1782.

**Origin:** User flagged that AI↔AI is fake (cold subprocess per round). 3-agent
review (Codex + Gemini) confirmed:
- `ab discuss` calls `runtime_invoke` with `entrypoint="delegate"` and no
  `session_id` (`scripts/ai_agent_bridge/_channels_cli.py:1144-1155`)
- Resume policy at `scripts/agent_runtime/runner.py:288-324` forbids resume on
  delegate entrypoint AND forbids Codex resume entirely
- Tier-2 fix: switch entrypoint to `"bridge"`, gate session_id by registry
  policy (Claude/Gemini opt-in, Codex stays fresh)

**Brief:** `docs/dispatch-briefs/2026-05-07-tier-2-warm-cache.md`. Numbered steps
include test, ruff, commit, push, PR — no auto-merge.

**Expected outcome:** PR opens against main with ~50-100 LOC change. Test asserts
session_id behavior per agent. Round-2 root truncation likely fixed as side
effect.

### F — Tier-3 persistent agent listener POC (DEFERRED)

**Status:** queued behind tier-2 + pending Multi-UI ADR ACCEPTED. Sub-task 2 of
#1782.

**Why deferred:** Tier 3 is weeks of architecture, requires the pending Multi-UI
ADR's identity/claim/lease/keepalive contracts to be ACCEPTED first. Tier 2
delivers most of the cache-warmth win without architectural dependency.

**Architecture (when it ships):**
- Build minimal Python daemon `scripts/listener/codex_listener.py`
- 4-column identity per ADR Q1 (`agent_family/ui_surface/client_id/instance_id`)
- Subscribe to bridge inbox via SSE per ADR Q2
- Hold OpenAI Responses API conversation with persistent message history
- Heartbeat 30s per Q6, release lease on SIGTERM
- Why Codex first: cold-process spawn + cold API call is its biggest pain (CLI
  startup is slow); also bypasses the registry's `resume_policy="never"` for
  Codex by routing through API daemon instead of CLI subprocess

**Real ceiling Codex surfaced:** Codex (the AI agent) is structurally barred
from prompt-cache reuse by project policy. Daemon listeners can keep the
process warm (avoid spawn cost) but each call still pays full prompt-cache
creation. Worth knowing for capacity planning.

### Sub-task 3 of #1782 — Discuss orchestrator routes to listener with fallback

**Status:** queued behind F. Per pending Multi-UI ADR Q11, route `ab discuss`
round to live listener if claim succeeds; if listener unreachable (2 missed
keepalives, lease expired, capability missing), fall back to subprocess and
record `fallback_reason` in the channel transcript.

## Execution checklist (for whoever picks this up)

```text
[x] PR #1781 merged (HARD STOP RULE)
[ ] Bakeoff retry-2 fired and REPORT.md landed
[ ] Writer-selection proposal posted on EPIC #1577
[ ] User signoff received → A1 unblocked
[x] Issue #1782 filed (persistent listeners umbrella)
[ ] Action E — Tier-2 PR lands (in flight, dispatch tier-2-warm-cache)
[ ] Action A — File D4 issue (use AC list above)
[ ] Action B — File infrastructure-bugs issue (3 sub-bugs)
[ ] Action C — Get user direction on separate-ADR vs Strand-6 fold,
    then file ADR or Strand 6 amendment
[ ] Action C — Run 3-agent review on the ADR (after B.1 is fixed)
[ ] Action D — Reply to kubedojo team
[ ] Action F — Tier-3 listener POC (deferred until ADR ACCEPTED + tier 2 ships)
[ ] Sub-task 3 of #1782 — discuss orchestrator routes to listener with fallback
```

## Don't lose this evidence

The full `architecture` thread `1c1b5d54966742ffacd1bf60e0893c1c` (root
2026-05-07T18:08:26) preserves the failed discussion + Codex's diagnosis
of B.1. Pull via:

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from ai_agent_bridge._config import DB_PATH
import sqlite3
db = sqlite3.connect(str(DB_PATH))
db.row_factory = sqlite3.Row
for r in db.execute(\"\"\"SELECT from_agent, round_index, body, created_at
    FROM channel_messages
    WHERE thread_id = '1c1b5d54966742ffacd1bf60e0893c1c'
    ORDER BY created_at ASC, message_id ASC\"\"\").fetchall():
    print('='*80); print(f\"[{r['created_at']}] {r['from_agent']} (r{r['round_index']})\"); print(r['body']); print()
"
```

Codex's clean single-shot reply (the actually-useful one) is in the
`messages` table, ID 558, also pulled via the same DB:

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from ai_agent_bridge._config import DB_PATH
import sqlite3
db = sqlite3.connect(str(DB_PATH))
print(db.execute('SELECT content FROM messages WHERE id=558').fetchone()[0])
"
```

Original brief at `/tmp/kubedojo-paradigm-brief-v2.md` (may be cleared by
OS — copy preserved here in this file's "Codex's data" + "The 4 queued
actions" sections).
