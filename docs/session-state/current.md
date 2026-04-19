# Session Handoff — 2026-04-19 morning (post-#1343 recalibration, #1345 ready to dispatch)

You're resuming (or starting cold). Boot via the API, not the filesystem:

```bash
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'
```

If API down: `npm run api:bg` (per `services.sh`).

## TL;DR first action

**Dispatch #1345 to Codex `--mode danger`** — it's the "complete the embedder bakeoff + add dedicated reranker benchmark" ticket that supersedes #1343's winner-by-elimination verdict. All prerequisites are met (HF_TOKEN present in `~/.bash_secrets`, fresh shell inherits it). Command:

```bash
.venv/bin/python scripts/delegate.py dispatch --agent codex --task-id issue-1345 \
  --prompt-file /tmp/codex-1345-prompt.md --mode danger
```

No prompt file yet — write one first. Use the GH issue body (`gh issue view 1345`) as the spec; key additions for the prompt: explicit file allow-list (`scripts/rag/**`, `docs/architecture/research/**`, `tests/rag/**`), "no `git add -A`" guardrail, HF_TOKEN usage note.

## Why #1345 matters (don't skip reading this)

#1343 returned **partial data** and a **verdict-by-elimination**:

| Model | Sample | Modern R@10 | Middle R@10 | OES R@10 | Status |
|---|---:|---:|---:|---:|---|
| BGE-M3 dense | 1000 | 1.00 | 0.50 | 0.30 | ✅ only full run |
| BGE-M3 hybrid | 1000 | 1.00 | 0.45 | 0.20 | ✅ (worse on archaic) |
| **jina-v3** | **20** | 1.00 | **0.85** | **0.60** | 🟡 smoke only |
| Qwen3-0.6B | 0 | — | — | — | ❌ MPS OOM |
| EmbeddingGemma-300M | 0 | — | — | — | ❌ HF gated (401) |

**jina-v3 smoke beats BGE-M3 on archaic by 70% (Middle) and 2× (OES).** If that holds at 1000, the "T3-T4 metadata-first, no dense" recommendation **flips entirely**. Shipping #1338 with BGE-M3 right now would lock in a decision made on missing data.

Plus: **dedicated cross-encoder rerankers were never tested** (BGE-reranker-v2-m3, jina-reranker-v2). Those typically give 2-10× better precision-at-top-K than using an embedding model for re-ranking. The `#1335` architecture says "FTS5 + dense re-ranker" — we need to decide whether "dense re-ranker" means embedding cosine or a dedicated reranker model.

#1345 closes both gaps. Qwen3 deferred on AC6 (conditional reopen if jina-v3 1000-run is disappointing).

## Phase 0 smoke — DO NOT commit, DO NOT delete

These three untracked files are **known-REJECT under old retrieval**:

```
wiki/pedagogy/a1/sounds-letters-and-hello.md
wiki/pedagogy/a1/sounds-letters-and-hello.sources.yaml
wiki/.reviews/pedagogy/a1/sounds-letters-and-hello.json
```

Final verdict = REJECT. source_grounding dim stuck (REJECT score 4→5, findings 16→9 across 2 rounds). Other 3 dims converged to PASS (ukrainian_perspective 9→10, register 8→10, factual_accuracy REVISE 7→PASS 8).

**Root causes (partly fixed, not all):**
1. `STALE_CITATION` (70% of findings) — writer-registry numbering misalignment. **Fixed in `a613f9b82`** via the `_write_sources_registry` invariant docstring + `force=` plumb-through.
2. `MISATTRIBUTION` — supporting chunks trimmed by too-tight 45k A1 char cap. **Fixed in `a613f9b82`** via 45k → 60k bump.
3. `UNSUPPORTED_CLAIM` — retrieval returning wrong chunks. **NOT fixed** — this is the `#1330` retrieval bottleneck, blocked on #1345 → #1338 → #1340.

**Do not rerun Phase 0 until after #1338 lands and #1340 validates.** Fixes 1+2 are necessary but not sufficient; the dominant failure mode is retrieval itself. Rerunning now will reproduce substantively the same REJECT.

## Chain state

| # | Title | Status | Next step |
|---|---|---|---|
| #1335 | EPIC — Compile-layer retrieval rebuild | open | tracker |
| #1336 | ADR-006 multi-tier architecture | ✅ closed | — |
| #1337 | Parent-section schema + extraction | ✅ closed | 98.83% chunks assigned, well under 20% blocker |
| #1339 | A1 grade filter fix | ✅ closed | — |
| #1343 | Embedder bakeoff (partial) | ✅ closed | **superseded by #1345** |
| **#1345** | **Complete bakeoff + reranker benchmark** | **🆕 filed, ready** | **DISPATCH FIRST** |
| #1338 | T1-T2 retrieval pipeline | ⏸️ parked | gated on #1345 verdict |
| #1340 | Re-validate #1330 diagnostic | ⏸️ parked | gated on #1338 |
| #1341 | T3-T4 retrieval | ⏸️ parked | gated on #1345 (jina-v3 result may flip direction) |
| #1342 | Doc updates (closes EPIC) | open | last |
| #1344 | Replace Phase A canary wiki articles | 🆕 filed | rebuild dependency — not urgent |

## Commits this session (all on `main`)

| SHA | What | Type |
|---|---|---|
| `d110b741d` | feat(wiki): rebuild orchestrator + phased plan doc | user WIP — scripts/wiki/rebuild.py (549 LOC) + docs/wiki-rebuild-plan.md |
| `a613f9b82` | fix(wiki): dim-review taxonomy split + A1 char cap + registry invariant | evidence-based refinements from adversarial review + Phase 0 diagnosis |
| `5e0b0bd47` | chore(env): autocompact 650k → 750k | start-claude.sh tweak |
| `0ce8d5b7e` | chore(wiki): mark Phase A canary articles as deprecated (#1344) | banner on 4 articles + plan doc migration table |
| `8e5cb44e8` | feat(wiki): section-level extraction schema + pipeline (#1337) | Codex commit — 98.83% assigned rate |
| `b1563e994` | #1343 Refactor embedding benchmark to SQLite + document bakeoff | Codex commit — survey doc in `docs/architecture/research/` |
| `0ae0d0d1f` | docs(adr): ADR-006 multi-tier compile-layer retrieval (#1336) | Codex commit |

## Env / infra

- **HF_TOKEN** in `~/.bash_secrets` (line 1252 of `~/.bashrc` sources it). **Read-scope token**, not rotated (low-risk surface). **Fresh bash login shell sees it; this session's Claude process does NOT** — that's why we're restarting/resuming.
- **start-claude.sh autocompact** bumped to 750k (`5e0b0bd47`). Current running session was launched before that commit — still on 650k. Fresh launch picks up 750k.
- **Claude Code output env vars confirmed correct**: `CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000` (at model max for Opus 4.7) + `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS=32000` (conservative; consider 50000 if you routinely full-read large files).

## Git dirty state (all expected, do not touch)

```
?? wiki/.reviews/pedagogy/a1/sounds-letters-and-hello.json
?? wiki/pedagogy/a1/   (contains sounds-letters-and-hello.md + .sources.yaml)
```

These three files are the parked Phase 0 smoke artifacts. DO NOT COMMIT, DO NOT DELETE until #1345 → #1338 → #1340 → clean Phase 0 re-run.

## Monitor watcher

The Codex chain watcher from the previous handoff is dead (this session ended its only instance). Re-arm after dispatching #1345:

```python
Monitor(
  command=': > /tmp/.codex-chain-seen; while true; do for tid in 1345 1338 1340 1341 1342 1344; do rf="batch_state/tasks/issue-$tid.result"; if [ -f "$rf" ] && ! grep -q "^$tid$" /tmp/.codex-chain-seen 2>/dev/null; then echo "$tid" >> /tmp/.codex-chain-seen; status_json=$(.venv/bin/python scripts/delegate.py status issue-$tid 2>/dev/null | head -20); echo "[$(date +%T)] CODEX TASK COMPLETE: issue-$tid — $(echo "$status_json" | grep -E \'"status"|"returncode"\' | tr -d \' ,\\"\' | tr \'\\n\' \' \')"; fi; done; sleep 45; done',
  description="Codex chain watcher",
  persistent=True, timeout_ms=3600000,
)
```

Pre-seed seen-list with already-done tasks so watcher doesn't re-fire:

```bash
echo -e "1330\n1331\n1333\n1336\n1337\n1339\n1343" > /tmp/.codex-chain-seen
```

## Architecture recap (don't re-litigate)

- **ADR-006** (`docs/architecture/adr/adr-006-compile-layer-retrieval.md`) locks the multi-tier split: T1-T2 dense + section + grade routing; T3-T4 metadata-first.
- **ADR-005** has a partial-supersession note — stands for WRITE-layer + T3-T4 compile.
- **Wiki-as-consumption-unit** preserved. Search returns at COMPILE, not WRITE.
- **Hybrid retrieval rejected** — `#1101` + repeat in `b1563e994` shows zero gain on modern + active harm on archaic.
- **Project is permanently non-commercial** — CC BY-NC deps (like jina-v3) are fine.

## When Codex fails infra steps

Codex is dispatched in `--mode danger` so it can `pip install`, set env vars, accept EULAs (where possible). But:

- **HF gating (EmbeddingGemma)** — Codex cannot accept a license on your behalf. If it hits 401, user must manually accept at the model page on HF. HF_TOKEN is already set, so if Codex hits 401 it means the license isn't accepted yet, not that the token is missing.
- **MPS OOM (Qwen3)** — Codex is instructed to skip per AC6. Don't let it burn hours trying to finesse memory.

If Codex hits a hard block it can't solve, it'll comment on the GH issue with "need user to X" and halt. Pick up inline with the specific human-in-the-loop step.

## Recent session-state files (for deeper context)

- `docs/session-state/writer-ab-test-plan.md`
- `docs/session-state/2026-04-18-am-autonomous-handoff.md`
- `docs/session-state/2026-04-14-handoff.md`
