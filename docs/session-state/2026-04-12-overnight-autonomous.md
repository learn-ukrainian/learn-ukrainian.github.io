# Session State — 2026-04-12 Overnight Autonomous Run

**Started**: 2026-04-12, late-session continuation of a very long day.
**Context**: User is going to sleep. Autonomous work until morning. No rush, no 1-hour artificial stop.
**Mode**: `<<autonomous-loop-dynamic>>` — self-paced, foreground work + `ScheduleWakeup` for idle waits.

---

## Critical user directives (from this session, DO NOT FORGET)

1. **Claude's role**: lead developer, architect, code reviewer, + UI/browser testing (best tools: claude-in-chrome, lightpanda). **Everything else: delegate.**
2. **Codex has 10× budget through May 17, 2026** — hammer it with tasks. Codex is now the primary implementation worker.
3. **Gemini reviews code + writes content** — used for every commit review via `ab discuss reviews`.
4. **Weekly Claude budget is tight** — aggressive delegation is non-negotiable. Do NOT write >50 LOC of non-test code inline without asking "could Codex do this?"
5. **Hygiene rule**: nothing commits or merges without adversarial review from another agent. Every commit must have `Reviewed-By:` trailer with task-id.
6. **Close issues only when ALL ACs are met**, never before.
7. **Morning report required** — summary of progress at top of next session.
8. **Don't do**: force-push, reset --hard, `v6_build.py --range`, modify curriculum/ content, destructive git ops without explicit permission.

---

## PRIORITY SHIFT (logged 02:15-ish)

User flagged **B1 language immersion** as the #1 priority. Current state: "too much English", "shameful language salad". Target: B1+ should be **dominantly Ukrainian** with English reserved for complex explanations (metalinguistic grammar, difficult concepts). A2 pipeline already ramps to "full Ukrainian by end of A2" — B1 needs to match.

**Tonight's real deliverable**: figure out with Gemini + Codex how to handle B1 language ratio. Outcome should be:
1. A pedagogical spec (what % English is allowed where)
2. A pipeline-level enforcement mechanism (audit gate)
3. A writer prompt fix
4. A decision on retroactive rebuild vs. forward-only

Phase C is still the architecture track but it's secondary. B1 immersion is blocking real module building. Parallel-track both where possible.

## Plan for the night

### Phase 1 — #1192 Phase C (channel bridge true async)

Filed as `#1192` with the synthesized design from the Gemini + Codex architecture discussion (thread `24bd19e24be34002834360ab71e26d60` in the `architecture` channel).

Sub-phases:
- **C.1** — Lease semantics on `deliveries` (Codex lead)
- **C.2** — Bridge session reuse + thread-coalesced worker (Codex lead, Gemini review)
- **C.3** — OS wake files + CLI (Codex lead)
- **C.4** — Fix `ab discuss` queue routing (Claude lead, Codex review)
- **C.5** — Codex worktree status brief (Codex lead)
- **C.6** — Structured Codex report contract (Codex lead)

Each sub-phase = 1 commit with `Reviewed-By:` trailer. Delegation pattern:
1. Write AC-anchored brief
2. `ask-codex` in background with `CODEX_BRIDGE_MODE=workspace-write`
3. Wait for Codex's structured report
4. Review the diff + run ruff + run any touched tests
5. `ab discuss reviews --with gemini --max-rounds 1` for adversarial review
6. Apply fixes if any blockers
7. Commit with full trailer
8. Update #1192 with sub-phase progress

### Phase 2 — Open infra issues

After Phase C or in parallel where independent:

- **#1082** — frontend test coverage. Check if closable. 11 of 12 components covered; verify what "Select" is, or if all ACs are actually hit.
- **#1191** — Cloze indexing fix (small, delegate to Codex). Align parser and text markers to 1-based.
- **#1161** — Wiki compilation prompt fixes. Assess scope. If >2 hours, triage for another session.
- **#1151** — YouTube subtitles ingest. Assess.
- **#1189** — B1 friction fixes. Already 4/5 patterns shipped. Verify issue status is accurate, close if all ACs met.

### Phase 3 — Morning report

Write `docs/session-state/2026-04-12-overnight-report.md` with:
- Commits landed (SHA + one-line summary)
- Issues closed
- Issues still open with status
- Decisions made autonomously + rationale
- Questions that need user input
- Token burn estimate if I can measure it
- What I would work on next

---

## Current state

### Recent commits (this session, before the overnight run)

```
aa3a964b4 test(frontend): FlashcardDeck tests (Codex-written) + agent memory update (#1082, #1190)
59fe26891 test(frontend): WatchAndRepeat unit tests + data-activity (#1082)
2e2d58a17 test(frontend): unit tests for Translate, Cloze, LetterGrid (#1082)
7993790cb test(frontend): unit tests for MatchUp, GroupSort, ErrorCorrection + a11y fix (#1082)
c028db0c4 test(frontend): unit tests for Quiz, TrueFalse, FillIn + fixes (#1082)
a4812e534 feat(bridge): B.5 dogfood + measured numbers + legacy deprecation (#1190)
4f6247ce0 feat(bridge): B.4 ab discuss multi-agent fan-out (#1190)
e47f04ce0 feat(bridge): B.3 channel CLI + API + web dashboard (#1190)
e62597f46 fix(bridge): B.1 blockers + feat(bridge): B.2 context injection (#1190)
339c78961 feat(bridge): B.1 channel storage layer — schema + module + tests (#1190)
```

### Repository status

- **Branch**: `main`, ahead of origin by ~9 commits
- **Clean**: no uncommitted changes (verify via `git status` at run start)
- **Node**: `starlight/` runs vitest via happy-dom; full unit suite = 312 tests passing
- **Python**: `.venv/bin/python`, Python 3.12.8. Ruff clean on touched files.

### Open GH issues (coding/infra scope)

- **#1192** — Phase C Epic (JUST FILED — work on this tonight)
- **#1191** — Cloze indexing asymmetry (filed earlier tonight)
- **#1189** — B1 friction fixes (4/5 patterns shipped; status may be closable)
- **#1188** — Diasporiana PDF (DEFERRED per user)
- **#1161** — Wiki compilation prompts (open)
- **#1151** — YouTube subtitles ingest (open)
- **#1149** — Site design audit (open)
- **#1142** — V6 refactor (BLOCKED per memory)
- **#1122** — A2 build pipeline fixes (priority:high)
- **#1114** — BuildContext refactor (BLOCKED — "before A2" blocker)
- **#1087** — CI/CD auto-deploy (open)
- **#1086** — learner feedback / analytics (open)
- **#1082** — frontend test coverage (partially done, 11/12 components covered)
- **#1067** — Frontend redesign EPIC (open)
- **#1051** — Pedagogy Pattern Library (content, human owns)

### Key file paths for Phase C work

| Purpose | Path |
|---|---|
| Channel storage primitives | `scripts/ai_agent_bridge/_channels.py` |
| Channel CLI handlers | `scripts/ai_agent_bridge/_channels_cli.py` |
| DB schema + migrations | `scripts/ai_agent_bridge/_db.py` (channel schema at lines ~105-145) |
| Runtime invoke (unified agent dispatch) | `scripts/agent_runtime/runner.py` |
| Claude adapter (supports resume) | `scripts/agent_runtime/adapters/claude.py` |
| Gemini adapter (NO resume) | `scripts/agent_runtime/adapters/gemini.py` |
| Codex adapter (fresh only) | `scripts/agent_runtime/adapters/codex.py` |
| Codex bridge | `scripts/ai_agent_bridge/_codex.py` |
| API endpoints | `scripts/api/comms_router.py` |
| Web dashboard | `playgrounds/channels.html` |
| Best-practices doc | `docs/best-practices/agent-bridge.md` |

### Key pre-read for every Codex brief

- `_channels.py:881-900` — `pending_deliveries_for()` (needs to become `claim_next_delivery()`)
- `_channels.py:574-706` — `post()` (add wake-file touch after commit)
- `_channels.py:808-919` — `mark_delivery()` (refactor into `_delivered`/`_failed`)
- `_db.py:105-145` — channel schema (migrate to add lease columns)
- `_db.py:214-269` — sessions table (reuse for bridge session key)
- `_channels_cli.py:455-477, 640-691` — `ab discuss` with bypass bug to fix in C.4
- `_codex.py:74` — "Codex runtime always fresh" (keep intentional)
- `_codex.py:240` — legacy batch path, template for per-delivery loop
- `adapters/claude.py:110-139` — Claude `--resume` / `--session-id` support
- `adapters/gemini.py:16-20, 93-96, 126-130` — Gemini session_id ignored
- `adapters/codex.py:10` — `resume_policy="never"`
- `runtime_invoke` at `runner.py:223` — entry point signature

### Dogfood: use the new channel bridge for delegations tonight

- `ab discuss reviews --with gemini --max-rounds 1` for commit reviews (proven in earlier batches)
- `ask-codex` for implementation tasks (channel-based dispatch waits on Phase C itself)
- Every review task-id prefixed with `phase-c-c1-review`, `phase-c-c2-review`, etc.

### Codex invocation template

```bash
CODEX_BRIDGE_MODE=workspace-write .venv/bin/python \
  scripts/ai_agent_bridge/__main__.py ask-codex \
  "$(cat brief)" \
  --task-id phase-c-cN-implement \
  --new-session
```

Default directory for ask-codex tasks is the repo root — Codex works in the main workspace unless I explicitly use a worktree (not needed for Phase C since no changes contend with user activity while sleeping).

---

## Cross-agent coordination notes

### Who writes what (the division learned from earlier in this session)

| Task type | Primary | Reviewer |
|---|---|---|
| Python infra implementation | Codex | Gemini |
| SQLite schema + migrations | Codex | Gemini |
| CLI handlers / argparse | Codex | Gemini |
| OS integration (launchd/systemd) | Codex | Gemini |
| Test writing (≤3 files) | Codex | Gemini |
| React/TSX components (test writing) | Codex | Gemini |
| React/TSX components (source edits) | Claude | Gemini |
| Architectural design | Claude | Gemini + Codex |
| Cross-agent briefs / review coordination | Claude | — |
| Linguistic verification (Ukrainian) | Claude via mcp sources | — |
| UI/browser testing | Claude (chrome, lightpanda) | — |
| Content writing (prose, modules) | Gemini | Claude |
| Content linguistic review | Claude | — |
| Prompt engineering | Gemini proposes, Claude decides | — |

### Codex + worktree quality protocol (to apply tonight)

1. Every brief includes EXACT file paths, import styles, test commands, success criteria
2. Write briefs from reviewer perspective: "Before you mark this done, verify: (a)..., (b)..., (c)..."
3. Always include 3 existing files as templates
4. Codex's verification ("passing") is proof-of-concept; my post-commit check is the real gate
5. Smaller deliveries: 1–2 files per task if possible, never >5
6. Every Codex task ends with the structured report block (C.6 will formalize this; until then I ask for it explicitly in each brief)

### Known Codex gotchas

- `--allow-write` is NOT a valid flag; use `CODEX_BRIDGE_MODE=workspace-write` env var instead
- `ask-codex` defaults to `--from gemini` unless you pass `--from claude` — doesn't matter for functionality
- Codex uses `--new-session` always (resume_policy="never"); session reuse is only for Claude
- Codex adapter prefix is `scripts/agent_runtime/adapters/codex.py`
- Bridge runs Codex via `runtime_invoke("codex", ...)` through the unified runner

---

## Interruption recovery

If this session compacts or crashes mid-run:

1. **Read this file first**, then `memory/MEMORY.md`, then the most recent commit messages
2. **Check git status** for in-flight changes — if any, diff them against the most recent commit to understand what's uncommitted
3. **Check background tasks** via the task system — any running Codex or Gemini jobs may still have output pending
4. **Check `.mcp/servers/message-broker/messages.db`** for pending `deliveries` to `codex` or `gemini` — any queued bridge traffic that didn't complete
5. **Check #1192 comments** for the latest state update — I'll post one after every sub-phase commit
6. **Resume from the next uncompleted sub-phase** — don't re-do work that's already landed
7. **If anything looks destructive or wrong**, STOP and leave a note in this file rather than making it worse

## Questions that could need user input (none yet, but log them here as they come up)

_Empty for now. If I hit a decision point I can't make autonomously, I'll add it here and leave Phase C paused rather than guess._

---

## Final note to morning-self (or next session's Claude)

The user explicitly said "don't rush, I don't want you to stop after 1 hour." This is a LONG run. Pace yourself. Use `ScheduleWakeup` for idle waits. Write clean, reviewable code. Every commit should stand on its own. Don't accumulate uncommitted changes — commit often, get reviews, move on.

Quality > quantity. If Phase C takes all 6 hours, that's fine. If it takes 3 hours and there's time for two bonus issues, also fine. Do NOT finish Phase C in a rush and then cram 5 more issues — that's how bugs ship.

The morning report is the deliverable the user will read first. Make it honest: what landed, what didn't, what you chose not to do and why.
