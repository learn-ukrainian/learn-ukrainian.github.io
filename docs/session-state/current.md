# Current — multi-agent index (2026-04-26)

> **MULTIPLE concurrent agent sessions are writing handoffs.** This
> file is a small index. Each agent maintains its OWN date-stamped
> handoff. Do NOT clobber the other agent's content here.

## Active threads

| Thread | Latest handoff | Owner |
|---|---|---|
| **EPIC #1577 reboot — Round 3.5 prompt-tighten shipped (#1603); decision pending on user re-run** | **`docs/session-state/2026-04-26-round-3.5-shipped.md`** | **Claude late-evening (this session)** |
| Predecessor: Round 3 QG bugfixes shipped, decision pending (3.5 vs 4) | `docs/session-state/2026-04-26-qg-bugfix-shipped.md` | Claude late-evening |
| Predecessor: Phase 4 round 3 dispatched (strict-JSON exemplar) | `docs/session-state/2026-04-26-evening-handoff.md` | Claude evening |
| Predecessor: autonomous orchestration during user-away window | `docs/session-state/2026-04-26-autonomous-orchestration.md` | Claude midday |
| Predecessor: overnight wiki rebuild + Phase 4 dispatch | `docs/session-state/2026-04-26-overnight-claude.md` | Claude overnight |
| EPIC #1577 reboot — Phase 0–3 done, Phase 4 staged | `docs/session-state/2026-04-26-overnight-1586-phase4.md` | predecessor session |
| Wiki rebuild bio/hist/lit/b2 (user-launched, slow Gemini) | covered by evening handoff | user (in flight) |
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
- **Main is at `9294dedbbe`** as of late-evening handoff (2026-04-26).
  Three Phase 4 PRs merged this round of sessions: `3603f11774` (#1598
  strict-JSON), `a6b9e7f417` (#1599 QG false-positive fixes), and
  `9294dedbbe` (#1603 round 3.5 prompt-tighten).
- **Phase 4 round 3.5 SHIPPED:** writer prompt now includes anti-meta-
  narration directives (12+ forbidden phrases), `{COMPONENT_PROPS_SCHEMA}`
  rendered from `lesson-schema.yaml` per allowed activity type, and 3
  whitelist additions + 13 declined-form variants. **Next decision:**
  user runs A1/20 build → if Gemini complies, round 3.5 is canonical
  config and Phase 5 fan-out begins; if it still produces meta-narration,
  empirical bakeoff trigger for round 4 (claude-tools vs gemini-tools).
  See `2026-04-26-round-3.5-shipped.md` for the decision table.
- **#1604 (NEW)** filed as follow-up: `PhraseTable` (and other
  vocabulary-tab activities) get `activity_type: null` in
  `lesson-schema.yaml`. Renderer warns; root cause needs schema-generator
  fix. Not Phase-4-blocking.
- **Round-3 failed Gemini exemplar artifacts** preserved in repo
  stash@{0} and stash@{1} (duplicates). `git stash show -p stash@{0}`
  to inspect — needed for round 3.5 prompt-tightening evidence.
- **Adversarial review discipline (added 2026-04-26 late):** all 3
  agents (bot + Gemini + Codex) must review before merge. Drive-by
  bot is not a substitute. Reviews are cheap and parallel; silent
  merge then bug-then-fix is expensive. See handoff for the corrected
  workflow that shipped today.
- **bio/hist/lit/b2 wiki rebuilds** (PIDs 6803, 13598, 13629, 56100)
  are user-launched Gemini runs in background. Slow (~10-15% in 1.5h).
  Will commit when done; no orchestrator action needed.
