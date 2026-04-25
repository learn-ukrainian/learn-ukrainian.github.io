# Session handoff: bakeoff merged, ready for cold-encode

**Date**: 2026-04-25 (afternoon/evening session)
**Context at handoff**: 328K tokens (past 300K early signal, before 400K handoff zone — proactive)
**Branch**: main (worktree `.worktrees/claude-1553-bakeoff/` removed)
**Key issue**: #1553 (wiki retrieval overhaul)
**Working PR**: #1562 (MERGED at 16:14 UTC on commit 5ab0e7e988)

---

## TL;DR for next session

1. **Step 5 of #1553 is done.** Bakeoff outcome: stay on Cell A (legacy 512). PR #1562 merged. Writeup at `docs/architecture/research/2026-04-25-chunk-policy-bakeoff-results.md`.
2. **Step 6 (cold-encode) is the next concrete action.** ~3 hours on user's M-series Mac (16 GB). Has a dry-run preflight that confirmed scope before kicking off.
3. **Don't skip the re-ingest of `ukrainian_wiki` BEFORE the cold-encode.** Codex flagged this — table is missing from the restored Apr 20 sources.db backup; if cold-encode runs first we'd need a 2nd encode pass.
4. **The wiki rebuild plan is locked in** — per-track Claude/Gemini split, total 1,665 wikis (754 rebuild + 524 NEW), but blocked on #1569 (multi-agent writer support in compile.py).

---

## What this session did

### Context entering session

- Bakeoff harness draft + spec already written (PR #1555 merged steps 0-4 of #1553)
- Worktree `.worktrees/claude-1553-bakeoff/` existed
- `data/sources.db` was found 0 BYTES at session start (mtime 14:34 today) — restored from GDrive backup (Apr 20 1.46 GB)

### Work shipped

- **PR #1562 MERGED** (squash-merged with admin override since worktree blocked the auto-merge of `--delete-branch`)
  - Commit `6bc79afbcc`: bakeoff harness `scripts/wiki/run_chunk_policy_bakeoff.py` (1091 LOC). Per-cell config (CHUNKING_POLICIES override + INDEX_MAX_LENGTH override), monkey-patched in a context manager. New BgeEncoder wrapper with per-call max_length. First-occurrence-per-parent rollup. Sanity gate vs #1345 baseline.
  - Commit `641eec655b`: MPS empty_cache between periods (was the OOM cause on the user's 16 GB Mac — pre-fix Cell B OES took 82 min, post-fix 6 min). Plus extra OES bilingual + Hungarian limitations in the writeup.
  - Commit `5ab0e7e988`: Bakeoff results writeup + per-cell incremental write fix (was: only at script-end; now `_write_outputs` runs after each cell with `partial=True`).

### Issues filed

- **#1563** — Restore + harden data/sources.db after Apr 25 wipe (root cause unknown; backup restore unblocked the work; needs ukrainian_wiki re-ingest + GDrive backup refresh)
- **#1567** — Hungarian-language contamination in textbooks corpus (`5-klas-ukrmova-uhor-2022-1` 246 chunks + `6-klas-ukrmova-betsa-2023` Hungarian glosses). Affects production retrieval but not this bakeoff's math.
- **#1569** — Multi-agent writer support for compile.py (Claude + GPT-5.5). Blocks the wiki rebuild from using the per-track Claude/Gemini split.

### Issue #1553 updated

Comment posted at `https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1553#issuecomment-4320034722` with full step-5 outcome.

---

## Bakeoff outcome (the key decision)

| Cell | Modern R@10 | Middle R@10 | OES R@10 | Modern nDCG | Middle nDCG | OES nDCG |
|---|---:|---:|---:|---:|---:|---:|
| A (legacy 512) | 1.000 | **0.500** | 0.300 | 0.997 | 0.262 | 0.269 |
| B (1500/2048)  | 1.000 | **0.450** | 0.300 | 0.997 | 0.251 | 0.254 |
| C (4000/8192)  | OOM at 9.96 GB MTLBuffer alloc — hardware-infeasible on 16 GB Mac |

**Verdict**: Stay on Cell A. NO winner-config PR needed. `INDEX_MAX_LENGTH` stays at 512.

**Codex's preferred framing** (msg #467): "no evidence to change config" rather than "legacy is objectively best." Cell B's middle −0.05 R@10 = exactly 5pp = at the spec's hard regression threshold. Cell C excluded for hardware infeasibility, not "untested."

**Bigger story (already in writeup)**: The gold set in `scripts/rag/benchmark_queries.yaml` does NOT surface the 512-truncation bug we were trying to validate. Cell A modern R@10 = 1.000 means relevant content always lives in the first 512 tokens. The actual long-tail truncation bug (textbook p99=14991 tokens losing 96% of content) needs a gold set with deep-in-section queries to be measurable. Higher-ROI followup than running more cells.

**Critical caveat for the user-visible improvement narrative**: Even though the bakeoff said "no measurable improvement," **PR #1555's chunker is still real and still hasn't been applied to disk yet**. The schema-v2 migration stamped existing rows as `LEGACY_SHIPPED_CONFIG`; the next `cold_encode_corpus` run will see config mismatch and re-encode under the post-step-1 paragraph-aware 450/50 policy. So step 6 (cold-encode) and step 7 (wiki rebuild) are STILL REQUIRED — they're PR #1555 follow-throughs, not new bakeoff outcomes.

---

## Next concrete actions (in order)

### 0. Snapshot DB before cold-encode (safety)

```bash
cp data/sources.db "data/sources.db.bak-$(date +%Y%m%d-%H%M%S)"
ls -lah data/sources.db data/sources.db.bak-*
```

Cheap insurance — guards against another 0-byte wipe mid-encode.

### 1. Re-ingest `ukrainian_wiki` AND encode in one step (~10 min)

The table is missing from the Apr 20 backup. Was added by commit `df6ce42eb0` (Apr 23). The `--encode` flag does ingest + dense encode in one pass so we don't need ukrainian_wiki in the step-4 cold-encode list at all.

```bash
.venv/bin/python scripts/wiki/ingest_ukrainian_wiki.py wiki/ --encode
```

After: `SELECT COUNT(*) FROM ukrainian_wiki` should return ~1424 (per #1345 reference). Manifest should show ukrainian_wiki rows with current encoder config.

### 2. Re-run dry-run preflight

Confirms ukrainian_wiki is now encoded (up_to_date) and shows the scope of remaining work for textbook/external/wikipedia:

```bash
.venv/bin/python scripts/wiki/cold_encode.py --corpora textbook_sections,external,wikipedia,ukrainian_wiki --dry-run
```

Expected (after step 1's ingest --encode):
```
{"corpus": "textbook_sections", "total_units": 37630, "new_units": 36921, "stale_units": 709, "up_to_date": false}
{"corpus": "external", "total_units": 7957, "new_units": 7755, "stale_units": 202, "up_to_date": false}
{"corpus": "wikipedia", "total_units": 20220, "new_units": 4111, "stale_units": 16109, "up_to_date": false}
{"corpus": "ukrainian_wiki", "total_units": ~1424, "new_units": 0, "stale_units": 0, "up_to_date": true}
```

ukrainian_wiki should be `up_to_date: true` because step 1 already encoded it via `--encode`.

### 3. Smoke check from step 1 already validates the encoder

The `--encode` pass in step 1 already smoke-tests BGE-M3 load + MPS workspace + manifest writes on ~1424 rows. If step 1 succeeded, the long cold-encode in step 4 is safe to start.

### 4. Full cold-encode for textbook + external + wikipedia (~3h)

ukrainian_wiki is already encoded by step 1, so we can skip it here.

```bash
.venv/bin/python -u scripts/wiki/cold_encode.py \
    --corpora textbook_sections,external,wikipedia \
    --resume \
    2>&1 | tee /tmp/cold-encode-full.log
```

**MUST use `--resume`** — idempotent recovery if anything dies mid-run. Use Monitor tool to watch JSONL events. Expect:
- BGE-M3 load: ~30s
- textbook_sections: ~37,630 units / ~32 batch = ~1,176 batches × ~5.5s = ~108 min
- external: ~7,957 / 32 = ~249 batches × ~5.5s = ~23 min
- wikipedia: ~20,220 / 32 = ~632 batches × ~5.5s = ~58 min
- TOTAL: ~3h10m

If memory pressure surfaces (the user has only 16 GB), drop batch via env override or interrupt + resume with smaller batch.

### 5. GDrive backup refresh

```bash
./scripts/backup-data.sh
```

After cold-encode lands, refresh the backup so we don't lose the work. Backs up `data/sources.db` + `data/embeddings/manifest.db` + dense shards.

### 6. Cross-corpus dry-run for verification

```bash
.venv/bin/python scripts/wiki/cold_encode.py --corpora textbook_sections,external,wikipedia,ukrainian_wiki --dry-run
```

Should show all `up_to_date: true`. If anything is still stale → investigation.

### 7. Move to wiki rebuild planning

After cold-encode, the next blocker is **#1569 (multi-agent writer support)**. Without it, `compile.py` is Gemini-only and we can't run the per-track Claude/Gemini split the user wants for the 1665-wiki rebuild. Realistic ~3h focused implementation session (new modules `ai_llm/claude_call.py` + `ai_llm/codex_call.py` mirroring `call_gemini_with_fallback`, plus `--writer` CLI flag and dispatch in `compiler.py`).

After #1569: writer pilot (5 wikis × 3 models, 60 min), then bulk rebuild.

---

## Wiki rebuild plan (locked in this session)

Total scope: **1,665 wikis** = 754 (need rebuild for chunk-policy fix) + 524 (NEW — never compiled). Per-track writer split per user decision:

**Claude (715 wikis, ~47h serial @ 4 min/wiki)**:
- literature: 232
- figures (bios): 180
- periods: 140
- historiography: 136
- folk: 27

**Gemini (426 wikis, ~28h serial @ 4 min/wiki)**:
- grammar: 258 (a2/b1/b2)
- academic: 111 (c1)
- pedagogy: 55 (a1)
- linguistics: 2

**NEW wikis to compile (524 total)**:
- c2: 106 (none compiled yet)
- lit + sub-tracks: 203 (lit/lit-essay/lit-war/lit-hist-fic/lit-youth/lit-fantastika/lit-humor/lit-drama all write to literature/works; total 435 modules vs 232 compiled)
- oes: 101
- ruth: 114

User has weekend Claude budget. Run Claude shell + Gemini shell in parallel; finish in ~3 days.

User architecture clarification (important context): "the wiki is for the AI [lesson-builder]. instead of rag we organize the knowledge into ordered wikis and the ai is reading the wiki when building a lesson and not the rag." So the wiki rebuild is two layers upstream from user-visible lessons. A bad WIKI systematically misleads every lesson built from it (compounding mistake), which is why getting the rebuild right matters more than just per-wiki quality.

---

## Footguns / things to watch

### sources.db is fragile

The Apr 25 14:34 wipe (root cause unknown) lost the file to 0 bytes. Restored from GDrive Apr 20 backup (1.46 GB). #1563 tracks the hardening work. Until then:
- Snapshot before any DB-mutating script run
- Don't run multiple `build_sources_db.py` instances concurrently
- The `--force` guard in `build_sources_db.py` should fire on populated DB but verify

### MPS memory ceiling

16 GB unified memory is tight. Symptoms:
- BGE-M3 fp16 takes ~2.3 GB
- batch=32 max_length=512 fits ~3-4 GB workspace → OK
- batch=16 max_length=2048 fits ~4-5 GB → OK with empty_cache between periods
- batch=4 max_length=8192 needs 9.96 GB MTLBuffer → **cannot fit**

If the cold-encode OOMs:
1. Set `BENCHMARK_BATCH_SIZE=16` env if the script supports it (check) — otherwise kill + restart with whatever knob exists
2. The `--resume` flag means we don't lose partial work
3. `torch.mps.empty_cache()` between batches helps; the chunker harness has the pattern in `_write_outputs`-adjacent code

### Worktree was removed but git history is intact

`.worktrees/claude-1553-bakeoff/` removed via `git worktree remove`. Branch `claude-1553-bakeoff` deleted. Commits live on main as squashed `<merged-commit-sha>`. PR #1562 history complete on GitHub.

### Stale lock files

`/tmp/chunk-policy-bakeoff.lock` (and similar) survives crashes when subprocess `tee` keeps the FD alive. If a future run says "another bakeoff is running" but `ps` shows no process, just `rm /tmp/chunk-policy-bakeoff.lock`.

### Stale pyenv shim

If bash starts hanging 60s on every command with "pyenv: cannot rehash: couldn't acquire lock":
```bash
rm -f /Users/krisztiankoos/.pyenv/shims/.pyenv-shim
```

### Don't propose options. Do the work.

User got frustrated this session when I (a) proposed cloud GPU instead of designing for the 16 GB Mac, and (b) waffled on counts before reading the actual code. State a default, ask only the override-relevant question, execute. The user said "stop asking, just do it" multiple times.

---

## Files / artifacts created or modified this session

### Code (on main, via PR #1562)
- `scripts/wiki/run_chunk_policy_bakeoff.py` (NEW, 1194 LOC after final commit)
- `docs/architecture/research/2026-04-25-chunk-policy-bakeoff-results.md` (NEW, 254 LOC)

### Outside the PR (still in /tmp, may be wiped on reboot)
- `/tmp/bakeoff-run.log` — full bakeoff run log including Cell A+B per-period scores and the Cell C OOM trace
- `/tmp/codex-brief-step5-bakeoff-design.md` — initial design brief sent to Codex
- `/tmp/codex-brief-step5-impl-update.md` — implementation diff brief
- `/tmp/issue-hungarian-contamination.md` — body draft for issue #1567

### GitHub
- PR #1562 merged
- Issue #1553 commented (step 5 outcome)
- Issue #1563 filed (sources.db restore + harden)
- Issue #1567 filed (Hungarian contamination)
- Issue #1569 filed (multi-agent writer support)

### Codex bridge thread
- Task ID `wiki-embedder-review` — full conversation history via `.venv/bin/python scripts/ai_agent_bridge/__main__.py conversation wiki-embedder-review`. Latest message #467 covers Codex's pre-flight recommendations for cold-encode.

---

## Recovery if next session loses context

1. `gh issue view 1553` for the canonical plan
2. Read this handoff doc end-to-end
3. `cat docs/architecture/research/2026-04-25-chunk-policy-bakeoff-results.md` for the bakeoff details
4. `.venv/bin/python scripts/ai_agent_bridge/__main__.py conversation wiki-embedder-review | tail -200` for Codex's last positions
5. `git log --oneline -10` to confirm latest main state (should include the squashed PR #1562 merge)
6. Resume from "Next concrete actions" section above
