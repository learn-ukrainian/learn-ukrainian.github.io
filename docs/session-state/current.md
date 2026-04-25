# Current — multi-agent index (2026-04-25)

> **TWO concurrent agent sessions are writing handoffs.** This file is
> a small index. Each agent maintains its OWN date-stamped handoff. Do
> NOT clobber the other agent's content here.

## Active threads

| Thread | Latest handoff | Owner |
|---|---|---|
| EPIC #1550 a1/1 verification (Unit 6 A/B) | `docs/session-state/2026-04-25-orchestration-final-with-data.md` | orchestration session |
| Wiki retrieval overhaul (#1553) | `docs/session-state/2026-04-25-wiki-retrieval-overhaul-1553.md` | wiki agent session |
| Cold encode complete → next is #1569 | `docs/session-state/2026-04-25-cold-encode-complete.md` | wiki agent session |

## Cold-start protocol

1. Read this index.
2. Open the handoff(s) relevant to your role.
3. If you create a new handoff, **add a row to the table above** —
   do NOT replace this whole file.

## Cross-thread notes

- **Wiki search-index rebuild pending** (orchestration agent flagged
  2026-04-25): when wiki agent finishes its rebuild pass, schedule a
  search-index rebuild on the same artifacts. No immediate action.
- **Cold-encode 88,192 units / 4 corpora committed 2026-04-25 evening**
  (wiki agent). All `up_to_date: true`. GDrive backup refreshed. The
  retrieval layer is now consistent with PR #1555's paragraph-aware
  chunker for the FIRST time. If lesson builds since 2026-04-23 looked
  off, that gap is now closed.
- **`~/.bash_secrets`** is where `GITHUB_TOKEN` lives. Not in any
  standard rc file. Source it manually before `gh` calls.
- **a1/1 working tree** has user's preserved manual patches. Do NOT
  clobber from any thread.
- **Main is at `24f3849a05`** as of orchestration session end.
