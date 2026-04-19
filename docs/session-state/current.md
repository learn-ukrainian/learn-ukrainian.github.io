# Session Handoff — 2026-04-19 afternoon (post-#1345 verdict, #1338 ready to dispatch)

You're resuming (or starting cold). Boot via the API, not the filesystem:

```bash
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'
```

## TL;DR — #1345 closed, verdict locked in

**Embedder decision is final.** Complete bakeoff ran while you were biking (8 sub-tasks, memory-verified between each, zero OOM after the initial parallel-dispatch correction).

| Model | modern R@10 | middle R@10 | OES R@10 | Verdict |
|---|---:|---:|---:|---|
| **BAAI/bge-m3** | 1.00 | **0.50** | **0.30** | **WINNER** (locked for #1338) |
| intfloat/multilingual-e5-large-instruct | 1.00 | 0.43 | 0.10 | 512-tok cap, 2020/3048 passages truncated |
| jinaai/jina-embeddings-v3 | 1.00 | 0.28 | 0.15 | Smoke collapsed at scale |
| Alibaba-NLP/gte-multilingual-base | 1.00 | 0.27 | 0.10 | Fastest (246s) but weakest on archaic |
| google/embeddinggemma-300m | **0.03** | 0.15 | 0.05 | Not competitive on Ukrainian |
| Qwen/Qwen3-Embedding-0.6B | blocked | blocked | blocked | MPS OOM; parked in #1346 |

**Rerankers** (BGE-reranker-v2-m3, jina-reranker-v2-base-multilingual):
- Lift modern FTS5 **+0.33 R@10** (0.20 → 0.53) — useful but still below BGE-M3 dense @ 1.00
- **Zero effect on archaic tiers** — can't rescue Middle or OES
- Both rerankers essentially tied

## Architecture decision (LOCKED)

- **#1338 T1-T2**: `BAAI/bge-m3` dense re-ranker over section-level FTS5
- **#1341 T3-T4**: metadata-first retrieval, NO dense, NO reranker — no combo rescued archaic
- **Qwen3** parked in #1346 (conditional reopen only if future dense pressure returns)

## Next action — dispatch #1338

**Prompt ready** at `/tmp/codex-1338-prompt-DRAFT.md` — updated earlier with Gemini's adversarial-review findings:
- No new vector DB deps (no FAISS/Chroma — NumPy + SQL JOIN only)
- AC2 apostrophe preservation via existing `normalize_text`
- AC3 scoring weights `(bucket_A × 3) + (bucket_B × 1)` — hardcoded, no tuning
- AC5 enforces existing `LEVEL_CHAR_BUDGETS`
- AC6 concept assertions with ≥8/10 threshold from #1330
- Memory: blocking-wait lockfile (filelock, 60 min timeout) — NOT the non-blocking benchmark pattern
- Forbid parallel processing explicitly

**Dispatch command when ready:**

```bash
.venv/bin/python scripts/delegate.py dispatch --agent codex --task-id issue-1338 \
  --prompt-file /tmp/codex-1338-prompt-DRAFT.md --mode danger
```

**Don't auto-dispatch on cold-start** — #1338 is a larger, multi-file change (new pipeline + schema wire-up + caching). Worth a quick re-read of the draft prompt and the #1338 GH issue body first.

## Codex chain completed today (8 sub-tasks, all clean)

| SHA | Task | What |
|---|---|---|
| `c7d429d07` | A | Sequential lockfile + reranker harness skeleton + HF_TOKEN wiring |
| `8f5d753c8` | B | jina-v3 full 1000-sample |
| `87d7a454f` | F | BGE-reranker-v2-m3 full 1000-sample |
| `0101ce36e` | G | jina-reranker-v2-base-multilingual full 1000-sample |
| `b32033f46` | C | e5-large-instruct full 1000-sample |
| `3f57300dc` | D | gte-multilingual-base full 1000-sample |
| `2e7bda11e` | E | EmbeddingGemma-300M full 1000-sample |
| `089e6e459` | H | Survey doc refresh + verdict + #1345 closed |

## Plus my own commits today

| SHA | What |
|---|---|
| `d110b741d` | feat(wiki): rebuild orchestrator + plan doc (549 LOC) |
| `a613f9b82` | fix(wiki): dim-review taxonomy + A1 char cap + registry invariant |
| `5e0b0bd47` | chore(env): auto-compact 650k → 750k |
| `0ce8d5b7e` | chore(wiki): mark Phase A canary deprecated (#1344) |
| `74ab96e3b` | docs(session-state): morning handoff (superseded by this) |
| `c9707dc00` | feat(statusline): show context %, cost, rate-limit (later dropped cost) |
| `249ab34fe` | refactor(statusline): subscription-oriented (dropped $cost, added 7d) |
| `549cefacb` | docs(wiki-rebuild): encode Gemini adversarial review findings |

**Today's total on main: 34 commits.**

## Issues updated / closed today

| # | Action | Why |
|---|---|---|
| #1336 | ✅ closed (earlier) | ADR-006 shipped |
| #1337 | ✅ closed (earlier) | Parent-section schema shipped, 98.83% assigned |
| #1339 | ✅ closed (earlier) | Grade filter fix shipped |
| #1343 | ✅ closed | Claimed-closed by Codex earlier, now actually closed |
| #1332 | ✅ closed | Superseded by ADR-006 (FTS5-keyword-bakeoff rejected) |
| **#1345** | ✅ closed | **Bakeoff verdict — BGE-M3 for #1338, metadata-first for #1341** |
| #1344 | open, curriculum-plan audit posted as comment | AC2 pre-staged for when replacements land |
| **#1346** | newly opened | Qwen3 CPU/smaller-batch parked follow-up |

## Chain status

| # | Title | State | Next step |
|---|---|---|---|
| **#1338** | T1-T2 retrieval pipeline | ⏸️ waiting | **Dispatch next — prompt in `/tmp/codex-1338-prompt-DRAFT.md`** |
| #1340 | Re-validate #1330 diagnostic | ⏸️ parked on #1338 | Dispatch after #1338 validates |
| #1341 | T3-T4 archaic retrieval | ⏸️ parked on #1338 | Metadata-first, no dense (locked) |
| #1342 | Doc updates (closes EPIC) | ⏸️ last | After #1340 + #1341 |
| #1344 | Replace Phase A canary | ⏸️ parked on #1338 | Rebuild replacement + plan migration |
| #1335 | EPIC tracker | open | Closes when #1338/#1340/#1341/#1342 all done |

## Git dirty state (unchanged from this morning — do not touch)

```
?? wiki/.reviews/pedagogy/a1/sounds-letters-and-hello.json
?? wiki/pedagogy/a1/   (contains sounds-letters-and-hello.md + .sources.yaml)
```

These are Phase 0 smoke output — known-REJECT under old retrieval. DO NOT COMMIT, DO NOT DELETE. They're waiting for #1338 → #1340 → clean Phase 0 re-run.

## Monitor watcher

Chain-watching Monitor was stopped after Task H completed (task `bxnppe04y`). Re-arm when you dispatch #1338:

```python
Monitor(
  command='touch /tmp/.codex-chain-seen; while true; do for rf in batch_state/tasks/issue-1338*.result batch_state/tasks/issue-1340*.result batch_state/tasks/issue-1341*.result batch_state/tasks/issue-1342*.result batch_state/tasks/issue-1344*.result; do [ ! -f "$rf" ] && continue; tid=$(basename "$rf" .result); if ! grep -qxF "$tid" /tmp/.codex-chain-seen 2>/dev/null; then echo "$tid" >> /tmp/.codex-chain-seen; echo "[$(date +%T)] TASK COMPLETE: $tid"; fi; done; sleep 45; done',
  description="Codex chain watcher",
  persistent=True, timeout_ms=3600000,
)
```

Pre-seed seen-list with already-done IDs:

```bash
echo -e "issue-1345-A\nissue-1345-B\nissue-1345-C\nissue-1345-D\nissue-1345-E\nissue-1345-F\nissue-1345-G\nissue-1345-H" > /tmp/.codex-chain-seen
```

## Gemini reviews sent today (adversarial)

1. **Wiki rebuild plan** (msg #391) — found 3 issues, all encoded in `549cefacb`:
   - Hard retrieval dependency (phase 1 blocked until #1338 ships)
   - Halt criteria strengthened (added `>25% REJECT` trigger)
   - Runtime caveat "estimates are happy-path only"
2. **#1338 draft prompt** (msg #393) — found 4 issues, all encoded in draft:
   - No vector DB deps, SQL JOIN only for aggregation
   - Reinforce AC2/3/5/6 specific constraints explicitly
   - Blocking-wait lockfile (not non-blocking) for compile workflows
   - Forbid parallel processing patterns

## What user (you) wants on resume

- Review the #1345 verdict comment (1345 is CLOSED, check the closing comment)
- Review `/tmp/codex-1338-prompt-DRAFT.md`, dispatch when you're happy
- Maybe glance at #1346 (Qwen3 parked follow-up)
- If confident: dispatch #1338 → then #1340 → then #1341 (or parallel #1341 since it shares no files with #1338)
