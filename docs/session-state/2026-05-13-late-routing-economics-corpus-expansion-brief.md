---
date: 2026-05-13
session: "Late-evening continuation. 5 PRs merged (#1966 jsx uk= attr, #1968 residual VESUM answer field, #1972 m20 plan refs correction, #1971 routing-budget observability, #1973 Pohribnyi pronunciation corpus + citation-fixture fix). m20 build-iteration arc nearly closed — only #1969 multimedia-search regression remains before build #5. Major architectural realignment: clarified programmatic-pool economics (it's REAL API rates, no multiplier), encoded post-2026-06-15 no-Claude-dispatch rule + agent-fallback substitution map, ingested first audio-derived corpus (Микола Погрібний 3LP pronunciation reference)."
status: ok
main_sha: 4e83e0dcbc
main_green: true
open_prs: []
active_dispatches: 0
agents: [claude, codex, gemini]
worktrees_open: 7  # main + 4 m20 build worktrees + 2 codex dispatch worktrees holding stale branches
ci_notes: "All 5 PRs passed blocking checks. Advisory `review / review` (Gemini Dispatch) failed on each — ignored per #M-0.5. PR #1973 had one pytest fail mid-cycle on `test_my_morning_module_passes_citations_resolve` — collateral from #1972's plan-refs change; fixed inline on the same branch by updating fixture to match corrected plan (Караман p.187 + Захарійчук p.162, Кравцова removed)."
filed_today: [1967, 1969]
merged_today: [1965, 1967, 1972, 1971, 1973]
closed_today: [1962, 1965, 1967]  # 1962 closed by gates 1-4 fixes earlier; 1965+1967 by their PRs
next_p0: |
  m20 has ONE remaining blocker: #1969 (multimedia search regression — writer
  made 0 calls to query_wikipedia/search_external/search_images in build #4
  vs 2 in build #3, regression from #1964 contract directives crowding out
  the multimedia-search obligation). Option A fix proposed in the issue:
  add a pre-emit checklist to scripts/build/phases/linear-write.md (~25 LOC
  prompt addition). After that lands, m20 build #5 should clear all gates
  that previously failed:
    - vesum_verified: fixed by #1968 (answer-field skip)
    - l2_exposure_floor / component_density: fixed by #1966 (uk= attribute)
    - textbook_grounding: fixed by #1972 (plan refs page correction)
    - resources_search_attempted: pending #1969 fix
    - citations_resolve: should pass under corrected plan refs

  After m20 GREEN: Phase 2b m01-m07 batch.
  Then queued (gemini lane): 500 verbs structured ingestion → 1000 words
  structured ingestion → ULP 1-00→6-00 prose chunks → #1663 Antonenko-
  Davydovych style guide completion.

  Strategic items: SDK adoption Decision Card (docs/decisions/pending/
  2026-05-14-agent-sdk-adoption.md) should move to RECONSIDER status — its
  efficiency premise was on programmatic pool we're now banned from using
  for dispatches post-June 15.
---

# Brief — 2026-05-13 late evening — routing economics + corpus expansion

> Predecessor: `2026-05-13-m20-build-iteration-4-contract-shipped-brief.md`. This session continued the m20 arc and closed 4 of the 5 build-#4 gate failures. Plus shipped routing-budget observability, ingested the first audio-derived corpus, and encoded major routing-policy shifts that take effect 2026-06-15.

## TL;DR

5 PRs merged (`157b346434` → `4e83e0dcbc`). m20 build-iteration arc converged from "5 gate failures" → "1 remaining (#1969 multimedia)". First audio corpus ingested (Pohribnyi 3LP pronunciation reference, 6 videos, 35 chunks, 70K chars of canonical orthoepic content). Routing-budget endpoint live; agent-fallback substitution config codified; post-2026-06-15 no-Claude-dispatch policy encoded with user direction "delegate only to codex and gemini after june 15th."

## What shipped

| PR | Closes | Commit | Effect |
|---|---|---|---|
| #1966 | #1965 | `be9b7cef49` | `_jsx_text_values` extracts `uk=` attr (V7 DialogueBox convention) in addition to `text=` legacy. Unblocks l2_exposure_floor + component_density gates. 7 new tests (4 in test_linear_pipeline + 3 in test_immersion_gates). |
| #1968 | #1967 | `bb7d3ed24e` | `_activity_vesum_text` skips fill-in `answer:` field unconditionally (was conditional on options presence; build #4 had fill-in items with no options). Unblocks vesum_verified gate. 1 new regression test using the actual 6 build-#4 suffix fragments. |
| #1972 | — | `59bee5d87a` | m20 plan refs corrected: Караман p.176 → p.187 (corpus has it on p.187 per `mcp__sources__search_text` verification), Кравцова Grade 4 p.113 removed (redundant with Захарійчук p.162 Білоус verse coverage). Unblocks textbook_grounding gate. |
| #1971 | #1970 (codex-filed) | `a161a8cf61` | New `GET /api/state/routing-budget` endpoint surfacing per-agent burn% + recommendation. New `scripts/config/agent_budgets.yaml` ($200 agentic pool, $1000 codex weekly, $500 gemini weekly, $460/$690 claude interactive pre/during promo). New `delegate.py --check-budget` opt-in pre-flight. +768/-1 LOC across 9 files. |
| #1973 | — | `4e83e0dcbc` | Pohribnyi YouTube playlist ingestion (3LP "Українська літературна вимова" 1992, 6 videos × ~30min ≈ 173min total audio). 35 chunks indexed at `external_articles.channel_id='pohribnyi_pronunciation'`, 70,077 chars of canonical Ukrainian orthoepic content. Plus fast-follow commit `41f904f0b4` fixing `test_my_morning_module_passes_citations_resolve` fixture (collateral damage from #1972). |

## Architectural / policy shifts (encoded in MEMORY)

### 1. Programmatic pool economics — corrected mental model

I had this WRONG earlier in the session. The new $200/mo agentic credit pool (launching 2026-06-15, covers `claude -p` / Agent SDK / GH Actions / 3rd-party SDK) is **metered at real API rates, NO multiplier**:

- $200 = ~3-6 Opus-xhigh dispatches OR ~20-40 Sonnet-high dispatches per month
- Earlier "subscription-equivalent value" framing was incorrect
- Pool is a real cap, not a multiplier-enhanced bonus
- User's clarification: "you don't pay extra. It's the same subscription, same price per month."

### 2. Post-2026-06-15 routing rule (HARD)

User direction: **"delegate only to codex and gemini after june 15th."**

The $200/mo programmatic pool is reserved for user's own cold-start interactive Claude review sessions (when user personally pastes design questions into claude.ai for adversarial perspective), NOT for orchestrator `delegate.py --agent claude` invocations.

**NO OVERAGE** — user: "i spend enough for you, not going to spend more."

Encoded in MEMORY routing rules and at `scripts/config/agent_fallback_substitutions.yaml` (canonical substitution map for when Claude programmatic surfaces are unavailable).

### 3. Routing matrix correction — Gemini default for "run-this-script" work

Failure encoded 2026-05-13: I defaulted to Codex for Pohribnyi ingestion. User: "why do you use codex to run a py program ? you should use gemini instead."

Corrected lane mapping (MEMORY #M0):
- **Gemini** = DEFAULT for routine: running existing scripts, ingestion runs, tests/migrations/fixtures, docs-near-code (unmetered for us)
- **Codex** = work with implementation judgment: novel implementations, multi-file pattern application, hard debugging
- **Claude** = architectural (post-2026-06-15 forbidden)

### 4. Knock-on consequences pre-June-15

- V7 writer phase default is currently `claude-tools` per `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`. Post-June-15 this needs alternate path. Likely: writer phase done inline by orchestrator using `curriculum-writer` subagent + manual gate runs (the pre-multi-agent pattern that user confirmed worked historically: "all lessons were generated interactively").
- SDK Adoption Decision Card (`docs/decisions/pending/2026-05-14-agent-sdk-adoption.md`) needs RECONSIDER — its efficiency premise was on programmatic pool we're now not using for dispatches.

## Autopsies

### #M-7 pytest-locally violation on PR #1972

When I shipped #1972 (plan refs correction), I ran `tests/build/test_linear_pipeline.py` + `tests/test_immersion_gates.py` locally — matching test files to the CODE AREA I changed. But a DATA-FILE change can break ANY test that reads that file. `tests/test_citation_resolve.py` had a hardcoded fixture asserting on the old plan refs (Караман p.176, Кравцова p.113) and went red on main when #1972 merged. PR #1973 inherited the breakage; fixed inline on the same branch.

Lesson broader than current #M-7 wording: **when changing a data file (plan / config / fixture), the correct pre-push pytest scope is the full suite OR at minimum `grep -lR <filename-or-key> tests/` to find dependent tests.** Worth tightening MEMORY #M-7 next session when budget allows (currently 150/150).

### Routing miss on Pohribnyi ingestion

I defaulted to Codex for "register YouTube playlist + run existing yt-dlp script + extend `normalize_channel_url` for playlist URLs." Codex completed successfully (returncode=0, 22min, 6 videos fetched, 35 chunks inserted) — but it should have gone to Gemini. Codex's lane is implementation judgment; Gemini's lane is executing existing patterns. Pohribnyi was the latter. Encoded as lane correction in MEMORY #M0.

### Pohribnyi audit caveats (filed, NOT blocking m20)

1. **Timestamps NULL in chunks** — schema has `chunk_start_ts`/`chunk_end_ts` columns but `_parse_vtt()` discards timestamp lines during VTT parse. User pushed back ("do we need the timestamp btw?") — agreed: no current consumer needs them; YAGNI. Schema columns can stay NULL until/unless a use case appears.
2. **Auto-captions are lowercase + no punctuation** — content is correct verbatim Pohribnyi speech, but unsuitable for verbatim ≥30-word blockquoting in `textbook_grounding`. Writer should paraphrase, not verbatim-quote auto-caption sources. Small writer-prompt directive update (~5 LOC) batched with the broader ULP/Ohoiko verbatim-policy work queued for later.

## Decision Cards drafted (status: PROPOSED, needs review)

| Path | Status | Note |
|---|---|---|
| `docs/decisions/pending/2026-05-14-agent-sdk-adoption.md` | PROPOSED → **RECONSIDER** | Premise (efficiency on programmatic pool) undermined by no-Claude-dispatch policy. Worth keeping for the architectural framing but adoption sequencing needs rethinking. |

## Issues filed today

| Issue | Subject | Status |
|---|---|---|
| #1967 | Residual VESUM `answer:` field leak — 6 reflexive suffix fragments still missing post-#1963 | ✅ Closed by #1968 |
| #1969 | resources_search_attempted=0 regression — multimedia search obligation crowded out by #1964 contract | **P0 next session** |
| (Codex filed #1970 during routing-budget dispatch — closed by #1971) | | ✅ Closed by #1971 |

## Build worktrees preserved

All 4 m20 build worktrees still on disk (122043, 161726, 164953, 193448). Build #4 worktree (193448) was the diagnostic source for this session; can be archived/removed after build #5 lands and verifies the fixes. The 2 codex dispatch worktrees (1967-vesum-answer-field, m20-plan-refs, jsx-uk-attribute, routing-budget-observability, ingest-pohribnyi-pronunciation) hold deleted-on-remote branches; safe to clean up once main fast-forwarded properly.

## Dispatches this session

| Task ID | Agent | Duration | Outcome |
|---|---|---|---|
| `jsx-uk-attribute-2026-05-13` | codex/gpt-5.5/high | 299s | done; PR #1966 |
| `routing-budget-observability-2026-05-13` | codex/gpt-5.5/high | 931s | done; PR #1971 |
| `ingest-pohribnyi-pronunciation-2026-05-13` | codex/gpt-5.5/high | 1341s | done; PR #1973. **Should have gone to gemini** — routing lesson encoded. |

Codex weekly quota burn: 3 dispatches × ~9 min avg ≈ 30 min of Codex high-effort time. Within budget.

Inline-by-orchestrator (interactive bucket): #1967 fix (~15 LOC + 60 LOC test, ~10 min wall-clock), #1972 plan refs correction (~4 line edits, ~5 min), citation-fixture fix on PR #1973 (~5 LOC, ~3 min). This proved the "inline-with-context" routing pattern works: when I have the diagnosis loaded, the inline path is materially faster than dispatch (no cold-start re-derivation).

## Outstanding queue (carry-over priority order)

- **P0:** #1969 multimedia search regression — Option A pre-emit checklist (~25 LOC writer-prompt edit). Gemini lane.
- **P0:** m20 build #5 — runs after #1969 fix lands. Validates all gate fixes end-to-end.
- **P1:** 500 verbs structured ingestion (gemini lane). User: "killer content."
- **P1:** 1000 words structured ingestion (gemini lane).
- **P2:** ULP 1-00 → 6-00 prose chunks ingestion (gemini lane; large scope, needs `quote_verbatim_allowed=false` policy field for paraphrase-only sources).
- **P2:** #1663 Antonenko-Davydovych style guide completion (gemini lane; ingest remaining ~321 entries from Tier 2 escalation URL).
- **P3 strategic:** SDK Adoption Decision Card status change to RECONSIDER + revised plan.
- **P3 strategic:** Tighten MEMORY #M-7 ("data-file change → grep dependent tests") — needs MEMORY trim first.
- **P3 strategic:** Extend `/api/state/routing-budget` `recommendation` to surface `fallback_substitutions` from the YAML config (follow-up to #1971).
- **P4 backlog:** #1958 stale red tests on main (still open at session start, unverified after this session's changes).

## Next session opening action

1. Read this brief.
2. `curl -s http://localhost:8765/api/orient` — confirm main at `4e83e0dcbc` or newer.
3. Fix #1969 multimedia search regression: edit `scripts/build/phases/linear-write.md` to add pre-emit checklist (gemini dispatch OR inline if context still loaded). Brief is essentially the issue body.
4. After #1969 lands: re-run m20 build #5 with `--worktree`. Monitor via `Monitor` tool on JSONL event stream. Realistic target: m20 GREEN.
5. After m20 GREEN: Phase 2b m01-m07 batch per existing brief at `docs/dispatch-briefs/2026-05-13-phase-2b-m1-m7-warmup-batch.md`.
6. In parallel: file dispatch briefs for 500 verbs + 1000 words ingestion (gemini lane). Don't fire all four corpus ingestions simultaneously — sequence to avoid stepping on sources.db locks.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". MD-only per #M-2 ai→ai. Companion canonical configs: `scripts/config/agent_budgets.yaml`, `scripts/config/agent_fallback_substitutions.yaml`. Companion Decision Card (RECONSIDER): `docs/decisions/pending/2026-05-14-agent-sdk-adoption.md`.*
