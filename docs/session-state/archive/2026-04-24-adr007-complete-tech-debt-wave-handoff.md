# Session Handoff — 2026-04-24 ~05:30 UTC: ADR-007 100% complete + 4-issue tech-debt wave shipped

> **TL;DR** ADR-007 migration closed out end-to-end this session (PR-F,
> PR-D, PR-E all merged). On top of that, 4 tech-debt issues shipped:
> content-based `_FLOAT_LITERAL_ALLOWLIST` (#1507), 7 A1 wiki citation
> drifts (#1488–#1494), Unicode й/ї corruption fix across 4 helpers
> (#1487), plan immutability pre-commit hook (#1463), and the deploy-
> script idempotency CI invariant (#1464, re-scoped after first attempt
> was architecturally flawed). **a1/colors pilot gates fully green** —
> user can fire the runbook any time.
>
> **Read the 00:55 CET handoff** (`2026-04-24-adr007-b-merged-d-f-
> inflight-handoff.md`) for the ADR-007 state at session start. This
> file is the delta: ADR-007 finished + 4 unrelated tech-debt items
> closed + colors pilot unblocked.

---

## What landed this session (merged to main, newest first)

| PR | Issue | Subject | Notes |
|---|---|---|---|
| #1516 | #1464 | `ci(rules): deploy-script idempotency invariant` | **Re-scoped.** First attempt (PR #1514) was gitignore-violating, closed with autopsy. v2 tests deploy-script produces synced output — the correct CI-enforceable question. |
| #1515 | #1463 | `feat(pre-commit): plan immutability enforcement` | CI-fix push required (`.venv/bin/python` → `sys.executable` in tests) |
| #1513 | #1487 | `fix(unicode): preserve й/ї during normalization` | 4 helpers fixed + shared `strip_ukrainian_stress` extracted to `scripts/common/text_utils.py` + round-trip tests |
| #1512 | #1488–#1494 | `fix(wiki): resolve citation drift in 7 A1 articles` | Review caught 2 whitespace artifacts (bracket-stripping left `VESUM ;`) — fixed and pushed. KNOWN_DRIFT dict now empty. |
| #1511 | #1456 | `docs(adr): ADR-007 ACCEPTED — close superseded issues` | Admin-merged (docs-only path filter, Gemini advisory non-blocking) |
| #1510 | #1507 | `test(threshold): content-based _FLOAT_LITERAL_ALLOWLIST` | Adversarial review caught duplicate allowlist entries — inline fix pushed |
| #1509 | — | `refactor: ADR-007 PR-D — delete rewrite-block infrastructure` | Rebase + test-symbol promotion + allowlist line bump (2766→2758) required. PR-F's self-documenting invariant test flipped xfail symbols into active set as designed. |
| #1508 | — | `test(adr-007): structural invariant — forbidden rewrite symbols stay gone` | Merged with all CI green; only advisory Gemini failed |

**9 PRs merged, 17 issues closed.** Session wall-clock ~4h.

---

## Issues closed this session

### ADR-007 wave (5 supersedes, auto-closed by PR-E #1511 — traceability comments posted)
- #1268 (per-call Gemini budget) — *obsolete*
- #1277 (rewrite-block prompt slimming) — *obsolete*
- #1288 (WORD_BUDGET auto-heal) — *rejected*
- #1322 (convergent pipeline) — *partially shipped, tightened*
- #1456 (ADR-007 closer)

### Citation drift (7 closed by PR #1512)
- #1488 food-and-drink, #1489 hey-friend, #1490 my-family, #1491 reading-ukrainian, #1492 stress-and-melody, #1493 things-have-gender, #1494 who-am-i
- GitHub's `Closes` keyword only honored the first — posted explicit close comments on the other 6

### Tech-debt (5 closed)
- #1486 (Unicode helpers dup of #1487)
- #1487 (Unicode й/ї corruption) — PR #1513
- #1507 (content-based allowlist) — PR #1510
- #1463 (plan immutability hook) — PR #1515
- #1464 (deploy-script idempotency) — PR #1516

---

## Open items

### Nothing in flight. All dispatches resolved.

### Open issues (10 total) — **NONE block the colors pilot**

Verified end-to-end against the pipeline runtime path:

| # | Why it doesn't block | Effect if fixed |
|---|---|---|
| #1481 | CI speed-up only | Faster CI |
| #1480 | Local dev ergonomics | Docker-pytest parity |
| #1451 | Umbrella EPIC, not a bug | — |
| #1435 | Affects `wiki/**.sources.yaml`; pilot builds `curriculum/l2-uk-en/a1/colors.md` via `sources.db` MCP tools, not wiki sidecars | Wider wiki quality |
| #1398 | Gemini-specific; pilot is Claude + Codex | — |
| #1395 | Dashboard tooling | — |
| #1377 | B1+ corpus scope; pilot is A1 | — |
| #1373 | `ukrainian_wiki` corpus not yet in `sources.db`; pipeline doesn't query it | Would enhance A1 retrieval |
| #1365 | Meta EPIC | — |

---

## a1/colors pilot — READY TO FIRE

### Runtime surface verified green

- ✅ v6_build.py convergence loop (PR-A/B/C/D killed rewrites; only `patch` + `plan_revision_request`)
- ✅ claude-tools writer @ Opus 4.7 xhigh (default since 2026-04-23)
- ✅ codex-tools reviewer (per-dim + MIN aggregation via #1455)
- ✅ Plan contract (required_terms fixed per EPIC #1451 Phase 3, WORD_BUDGET auto-heal removed)
- ✅ Citation invariant gate on published `colors.md` (KNOWN_DRIFT empty for A1)
- ✅ Unicode helpers preserve й/ї (#1513)
- ✅ `_FLOAT_LITERAL_ALLOWLIST` content-based (won't break on future line shifts)
- ✅ Plan immutability enforced at commit-msg stage (#1515)
- ✅ Rules deployment CI invariant (#1516)

### Minimal command

```bash
.venv/bin/python scripts/build/v6_build.py a1 10
```

That's all. Defaults cover writer/reviewer/model/effort. The runbook at
`.worktree-briefs/colors-pilot-post-adr007.md:121` explicitly warns not
to pass `--writer-model` or `--writer-effort` — those flags don't exist
on v6_build.py. (I made that mistake in summary messages during this
session; runbook was always correct.)

### When fire: USER-FIRED

Per the prior handoff: the pilot is explicitly user-fired, not Claude-
fired. User watches output, Claude triages failures.

**Recommended**: arm a Monitor on v6_build.py JSONL events before firing
so phase-by-phase failures surface as notifications:

```
Monitor(
  command=".venv/bin/python -u scripts/build/v6_build.py a1 10 2>&1 | grep --line-buffered '^{\"event\"'",
  persistent=True, timeout_ms=3600000
)
```

---

## Lessons logged

### "Gemini Code Assist out of quota → I do the adversarial review inline"
User flagged it at PR #1510 review time. I took over adversarial review for each subsequent Codex PR (#1513, #1515, #1516). Findings caught across 3 of 4 reviewed PRs:
- #1510: duplicate allowlist entries (inline fix pushed)
- #1512: 2 whitespace artifacts from bracket-stripping (inline fix pushed)
- #1515: `.venv/bin/python` hardcoded in tests → CI failure (inline fix pushed)
- #1514 (rejected): gitignore violation in CI invariant approach — **entire PR closed**, re-briefed and re-dispatched as #1516

Takeaway: agent-dispatched PRs benefit significantly from inline review. Budget for it.

### "Briefs must flag gitignore constraints explicitly for any sync-invariant"
My first #1464 brief told Codex to mirror `npm run claude:deploy` paths without flagging that `.claude/` is gitignored. Agent followed literally and force-committed ignored files. v2 brief explicitly called out the gitignore and re-framed the invariant as deploy-script idempotency.

### "`Closes #A, #B, #C` in PR body only honors the FIRST issue"
GitHub's keyword auto-close requires each issue to be prefixed with the
close keyword. Citation PR #1512 listed 7 issues; only #1488 auto-closed.
Posted explicit close comments on the other 6.

### "Memory #0H validated: merging is my job, not the user's"
Merged 9 PRs inline during this session. Memory call-out from 2026-04-23
("you merge you idiot") worked — I didn't once stop to ask permission.

---

## Monitor state at handoff

- `bolpouiyd` — #1464 v2 monitor, idle (#1516 merged). Will stay armed until session end; no cost as no transitions expected.
- `bm9ukcgd1` — earlier tech-debt monitor, all 3 refs resolved. Idle.
- `b52m9xsmy` — citation/ADR monitor, all 3 refs resolved. Idle.

No notifications expected until next activity. Session safe to end.

---

## Context accounting

Start: ~100K (fresh session)
Peak: ~270K during heaviest dispatch-review burst
End: ~275K estimated
Cap: 500K (user-set)
Headroom: ~45% remaining at handoff

Budget healthy. No compaction needed. Session can end cleanly or continue
autonomously per user direction.

---

*Generated 2026-04-24 ~05:30 UTC at Krisztian's request. All in-flight
work resolved; a1/colors pilot gates fully green. Next session: user
fires pilot, Claude triages output OR Claude picks next tech-debt item
from the 10 open issues (all unblocked, none time-critical).*
