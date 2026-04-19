# Session Handoff — 2026-04-19 early morning (compile-layer retrieval rebuild planned, Codex tasks in flight)

You're starting cold. Boot via the API, not the filesystem:

```bash
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'
```

If API down: `npm run api:bg` (per `services.sh`).

## CRITICAL — re-arm Monitor immediately

Two Codex tasks are running independently of any Claude session. They write `.result` files to `batch_state/tasks/` when done. The previous Monitor watcher died with the prior session. Re-arm with:

```python
Monitor(
  command=': > /tmp/.codex-chain-seen; while true; do for tid in 1339 1343 1336 1337 1338 1340 1341 1342; do rf="batch_state/tasks/issue-$tid.result"; if [ -f "$rf" ] && ! grep -q "^$tid$" /tmp/.codex-chain-seen 2>/dev/null; then echo "$tid" >> /tmp/.codex-chain-seen; status_json=$(.venv/bin/python scripts/delegate.py status issue-$tid 2>/dev/null | head -20); echo "[$(date +%T)] CODEX TASK COMPLETE: issue-$tid — $(echo "$status_json" | grep -E \'"status"|"returncode"\' | tr -d \' ,\\"\' | tr \'\\n\' \' \')"; fi; done; sleep 45; done',
  description="Codex chain — fires on each task .result appearing",
  persistent=True, timeout_ms=3600000,
)
```

Pre-seed the seen-list so the watcher doesn't re-fire on already-completed tasks:
```bash
echo -e "1330\n1331\n1333" > /tmp/.codex-chain-seen
```

(Adjust list to match `ls batch_state/tasks/issue-*.result` at your start time.)

## CRITICAL — project policy locked this session

**Project is permanently non-commercial.** Recorded in CLAUDE.md (commit `f8dc07df7`). Implication: CC BY-NC and similar non-commercial licenses are acceptable for dependencies. Don't re-litigate.

## What's actively running (as of handoff)

| Slot | Task | What it does | Timeout |
|---|---|---|---|
| Codex 1 | #1339 grade-filter bug | Independent bug fix in `sources_db.py` | 1h |
| Codex 2 | #1343 embedder benchmark | Refactors `benchmark_embeddings.py` to read sources.db (not Qdrant) + adds jina-v3 + runs 4 models × 3 tiers | 4h |

Check status: `.venv/bin/python scripts/delegate.py list --status running`.

**WARNING**: a stale `.git/index.lock` was found and removed in this session. If git operations fail again with "Unable to create '.git/index.lock'", check `command ps -p <PID>` for the lock owner; if dead, `rm .git/index.lock`. Codex tasks aggressively try to commit and can leave stale locks if killed mid-write.

## Autonomous chain plan — execute when Monitor fires

When task X completes → review briefly → dispatch next via prompts in `/tmp/codex-NNNN-prompt.md` (or write fresh tight prompt):

| Trigger | Next dispatch | Notes |
|---|---|---|
| #1339 done | #1336 (ADR-006) — **dispatch to Codex** with discussion thread + epic body as input | User said use Codex, not Claude inline |
| #1343 done | If verdict says BGE-M3: continue to #1336 → #1337. If verdict says jina-v3 + late chunking: re-evaluate whether #1337 schema is needed | Read `docs/architecture/research/2026-04-embedder-survey.md` first |
| #1336 done | #1337 (schema + extraction pipeline) — Codex | Foundation for #1338 + #1341 |
| #1337 done | #1338 (T1-T2 pipeline) — Codex | Use embedder from #1343 verdict |
| #1338 done | #1340 (re-validate diagnostic) — Codex | If passes: epic almost closed; if fails: file embedder bakeoff |
| #1340 passes | #1341 (T3-T4) — Codex, lower priority | Can hold for next sprint |
| #1341 done | #1342 (doc updates) — closes EPIC #1335 | Mostly mechanical |

User directive on this session: **push load to Codex. Claude budget is bleeding.** Don't write any of these inline unless Codex blocks. Default to small Gemini consults if responsive.

## Architecture decision this session — multi-tier compile-layer retrieval

EPIC: **#1335**. Filed today after a 2-round discussion (channel `reviews`, thread `ae74c96384514d47ba81417e6e8c0da6`) where Claude + Codex + Gemini converged with `[AGREE]`.

**Decision**: split COMPILE-layer retrieval architecture by linguistic tier. Wiki-as-consumption-unit (ADR-005) UNCHANGED. Karpathy's pattern preserved at WRITE phase; search returns at COMPILE phase per Karpathy's own qmd recommendation at scale.

| Tier | Tracks | Recommended retrieval |
|---|---|---|
| T1-T2 modern Ukrainian | A1, A2, B1, B2, C1, C2 + seminars | Section/chapter-level FTS5 + dense re-ranker, parent-context injection, grade routing |
| T3 Middle Ukrainian | RUTH | Section/work-level metadata routing, NO dense, NO hybrid |
| T4 Old East Slavic | OES | Section/work-level metadata routing, NO dense, NO hybrid |

Empirical anchor (`#1101` benchmark, BGE-M3, 2026-03-30): modern dense Recall@10 = 0.967 (excellent), Middle 0.600, OES 0.400. Hybrid actively worse on archaic. **#1343 is re-running with all 4 models × all 3 tiers** to lock the embedder choice.

## Issue map (filed today, 2026-04-18 → 2026-04-19)

| # | Title | Status |
|---|---|---|
| #1330 | Retrieval bottleneck investigation | ✅ closed — verdict `retrieval_bottleneck` |
| #1331 | Universal anti-hallucination review protocol + verifier | ✅ closed — `docs/review-protocol.md` shipped |
| #1333 | Corpus gap audit | ✅ closed — 12 draft ingestion tickets at `data/corpus_audit/draft_tickets/` |
| #1334 | [PARKED] Reviewer incentive inversion | parked, do NOT implement until retrieval thread closes |
| **#1335** | **EPIC — Compile-layer retrieval rebuild** | open, tracker |
| #1336 | ADR-006: Multi-tier retrieval architecture (DOC) | open, queued — dispatch to Codex |
| #1337 | Schema: parent section table + extraction | depends on #1336 |
| #1338 | T1-T2 retrieval pipeline | depends on #1337 + #1343 verdict |
| #1339 | Bug: A1 grade filter not enforcing | 🔄 Codex running |
| #1340 | Re-validate #1330 diagnostic | depends on #1338 + #1339 |
| #1341 | T3-T4 retrieval pipeline | depends on #1337 (lower priority) |
| #1342 | Doc updates (closes EPIC) | depends on #1336 + #1338 + #1341 |
| #1343 | Embedder research + benchmark (BGE-M3 vs Qwen3 vs Gemma vs jina-v3 × 3 tiers) | 🔄 Codex running |

## Key decisions made this session (do NOT re-litigate)

1. **Project is permanently non-commercial.** CLAUDE.md + GEMINI.md updated.
2. **SQLite FTS5 alone is rejected** for the modern-tier compile retrieval. Architecture moved to dense + section-level (per #1101 evidence + discussion outcome).
3. **Hybrid (dense + sparse) rejected** — adds zero on modern, hurts archaic. #1101 data definitive.
4. **Embedder bakeoff is happening NOW** via #1343. Do NOT pre-decide the winner — wait for data.
5. **Qdrant stays retired.** #1343 refactors benchmark to read from `sources.db`, not Qdrant collections.
6. **jina-embeddings-v3 (CC BY-NC 4.0) is acceptable** because project is non-commercial. Bonus: only competitive European multilingual embedding (Berlin, Jina AI), with native late chunking that may reduce schema work in #1337.
7. **Ukrainian sovereign LLM** — beta spring 2026, built on Gemma. Watch item; likely ships embedding component eventually.
8. **Codex caught real bug**: A1 grade filter leaks Grade 5+ chunks despite `track="a1"`. #1339 fixes it. The #1330 diagnostic numbers may have been artificially boosted by leaked chunks; #1340 re-validates after fix.

## Discussion threads worth re-reading

- `reviews` channel, thread `0d9b884ecfe94db8bd9bd681a9c5fe49` — round 1 (bakeoff vs query construction)
- `reviews` channel, thread `ae74c96384514d47ba81417e6e8c0da6` — round 2 (4-tier retrieval architecture, converged [AGREE])
- `reviews` channel, thread `b338b59c64d54aeea8a0e02f4527331e` — BGE-M3 contender intel (Qwen3 vs jina-v3 vs late-chunking)

Tail: `.venv/bin/python scripts/ai_agent_bridge/__main__.py channel tail reviews --thread <ID>`.

## Files Claude committed this session

| Commit | What |
|---|---|
| `88772389c` | feat(api): timestamped logs + signal-source provenance |
| `7c9f22568` | docs(playbooks): portable anti-hallucination review protocol |
| `7645a854c` | fix(diagnostics): filename typo + dynamic chunk count (#1330) |
| `f8dc07df7` | docs: lock in non-commercial project policy |

## Files Codex committed this session

| Commit | What | Issue |
|---|---|---|
| `40a86a44b` + `f4f0e2833` | Retrieval playback diagnostic + artifacts | #1330 |
| `8bbba949b` + `4c62f894b` | Universal review protocol verifier | #1331 |
| `4cbc88199` + `e35c71af6` + `29b287200` | Corpus gap audit (A1 smoke) | #1333 |

## Pending Codex work (dirty files — Codex working on these, DO NOT touch)

`scripts/rag/benchmark_embeddings.py` — that's #1343's refactor in progress.

Other dirty files in `scripts/wiki/*` and `wiki/figures/`, `wiki/linguistics/oes/`, `wiki/literature/works/`, `wiki/periods/` — pre-existing from sessions before, not mine, not from active Codex tasks. Don't touch unless you investigate provenance.

## Small TODOs to revisit when bandwidth allows

- **Statusline context %**: `~/.claude/settings.json::statusLine` already TRIES to show `[ctx: N%]` via `context_window.used_percentage`, but the field isn't populated by current Claude Code build (the conditional skips). Need to debug what field IS available — temporarily add `tee /tmp/.statusline-input.json` to capture the input JSON, inspect, then update the jq path. User asked for this.
- **12 draft ingestion tickets** at `data/corpus_audit/draft_tickets/` from #1333 — review and selectively file as real GH issues.
- **Reviewer-incentives design (#1334)** — open after retrieval epic closes.

## What user wants from next session

- Push load to Codex. Claude budget is constrained.
- Use Gemini if responsive for second opinions / reviews.
- Manage the chain autonomously — don't ask for direction on each step.
- Surface only on completions, blocks, or things needing user judgment.

## Quick orient cheat sheet

```bash
# What's running:
.venv/bin/python scripts/delegate.py list --status running

# What just finished:
.venv/bin/python scripts/delegate.py list --status done | head -20

# Read a Codex result:
cat batch_state/tasks/issue-NNNN.result

# Tail a Codex log:
tail -50 batch_state/tasks/logs/issue-NNNN.stdout.log

# Dispatch next from a prompt file:
.venv/bin/python scripts/delegate.py dispatch --agent codex --task-id issue-NNNN \
  --prompt-file /tmp/codex-NNNN-prompt.md --mode danger
```

## Archive note

Previous handoff (2026-04-18 evening) is captured in `docs/session-state/2026-04-18-am-autonomous-handoff.md` and prior dated files. Today's content supersedes.
