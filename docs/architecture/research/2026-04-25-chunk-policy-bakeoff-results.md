# Chunk-policy bakeoff results (#1553 step 5)

**Date**: 2026-04-25
**Hardware**: M-series Mac, 16 GB unified memory
**Sample size per period**: 1000 (matches #1345)
**Sub-chunk retrieval depth**: 200
**Cell A baseline tolerance (vs #1345)**: ±0.02 R@10
**Source data**: `data/sources.db` restored from GDrive backup (Apr 20 1.46 GB)
**Run log**: `/tmp/bakeoff-run.log` (cells A+B complete; cell C OOM-aborted)

## TL;DR

**Stay on Cell A (current shipped behavior). Do NOT bump `INDEX_MAX_LENGTH` past 512.**

The chunker, validator, schema-versioned manifest, and MPS cleanup ship as
**infrastructure improvements** with clear maintainability value, but the
bakeoff did not measurably distinguish chunk policies on the existing
`scripts/rag/benchmark_queries.yaml` gold set. Cell B (paragraph-aware
1500/150 + encoder 2048) produced **identical** modern Recall@10 and
nDCG@10 to Cell A and **slightly worse** archaic-literary scores. Cell C
(4000/400 + encoder 8192) was hardware-infeasible on 16 GB unified
memory (Metal aborted on a 9.96 GB buffer allocation request).

## Cell A reproduction sanity check

Cell A is defined as the *legacy* baseline (`NO_CHUNK` on every corpus,
encoder window 512). It must reproduce the #1345 numbers within ±0.02
R@10 on every tier or the bakeoff is invalid.

| Tier | Cell A R@10 | #1345 baseline | Δ |
|---|---:|---:|---:|
| Modern | 1.000 | 1.000 | +0.000 ✅ |
| Middle Ukrainian | 0.500 | 0.500 | +0.000 ✅ |
| Old East Slavic | 0.300 | 0.300 | +0.000 ✅ |

`nDCG@10 modern` = 0.997, identical to #1345. **Sanity check PASSED.**

## Per-cell metrics

| Period | Cell A R@10 | Cell B R@10 | Cell C R@10 | Cell A nDCG@10 | Cell B nDCG@10 | Cell C nDCG@10 |
|---|---:|---:|---:|---:|---:|---:|
| OES (X-XIII)        | 0.300 | 0.300 | OOM | 0.269 | 0.254 | OOM |
| Middle (XIV-XVIII)  | 0.500 | **0.450** | OOM | 0.262 | 0.251 | OOM |
| Modern (textbooks)  | 1.000 | 1.000 | OOM | 0.997 | 0.997 | OOM |

**Cell B vs Cell A summary:**
- Modern: identical (R@10 saturated at 1.000; nDCG identical at 0.997)
- Middle: **−0.050 R@10** (exactly at the spec's 5pp regression threshold), −0.011 nDCG
- OES: flat R@10 (0.300), −0.015 nDCG

## Per-cell chunking stats

Sub-chunks per parent measures chunker fragmentation. Higher = more
fragmentation per source row.

| Period | Cell | Parents | Sub-chunks | mean/parent | p90/parent | max/parent |
|---|---|---:|---:|---:|---:|---:|
| OES         | A | 1010 | 1010 | 1.00 | 1 | 1 |
| Middle      | A | 1009 | 1009 | 1.00 | 1 | 1 |
| Modern      | A | 1029 | 1029 | 1.00 | 1 | 1 |
| OES         | B | 1010 | 1010 | 1.00 | 1 | 1 |
| Middle      | B | 1009 | 1009 | 1.00 | 1 | 1 |
| Modern      | B | 1029 | 1029 | 1.00 | 1 | 1 |

**Critical observation**: Cell B produced *identical* sub-chunk counts to
Cell A. The 1500-token target was not binding for any of the 3,048 sampled
rows — every row stayed below the chunk threshold. So Cell B's only real
difference vs Cell A was the encoder window (2048 vs 512), not chunking
behavior. The literary corpora's median/p99 token counts (literary p99
~1300) sit comfortably below 1500. Modern textbooks have the long tail
(p99=14991) but the random 1000-sample subset apparently didn't surface
the long-tail rows in numbers sufficient to move the metrics.

## Cell C: hardware-infeasible on 16 GB

Cell C requested `max_length=8192`, `batch_size=4`. On the first encoding
batch (OES sub-chunks), Metal failed to allocate a private MTLBuffer:

```
MPSCore/Utility/MPSCommandBufferImageCache.mm:1420:
  failed assertion `Failed to allocate private MTLBuffer for size 9964830976'
```

**9.96 GB** — more than half the Mac's 16 GB unified memory, on top of
~3 GB already held by BGE-M3 + the Python runtime + the OS. The Metal
kernel aborted with a hard assertion (process exit 0, but no output
written). Cell C cannot run on this hardware in any configuration that
preserves the chunk-policy semantics (the only way to fit it would be
batch_size=1 with much shorter `max_length`, which defeats the cell).

Cell C results would also have been moot per the data trend: middle R@10
already regressed by 5pp going from A→B; the more aggressive 8192 window
would diffuse attention even more on short archaic rows, almost certainly
pushing middle R@10 below the spec's hard `<0.40` stop condition.

## Decision (auto-generated, human-validated)

**Stay on Cell A** (current shipped behavior). The chunker and supporting
infrastructure ship per #1553 steps 0–4 because:

1. **Centralized chunking policy** (`scripts/wiki/chunking.py`) replaces
   per-iterator ad-hoc logic — clear maintainability win.
2. **Schema-versioned manifest** (`embedding_units` v2 — model_id +
   index_max_length + chunk_policy_version + pooling_mode) prevents the
   silent-mixed-config bug Codex flagged in msg #449.
3. **Validator gate** in `cold_encode_corpus` raises on units exceeding
   `INDEX_MAX_LENGTH` after chunking — protects against future
   misconfiguration.
4. **Boundary-aware splitter** (paragraph → sentence → token-window) is
   ready for activation if/when a future bakeoff justifies a window bump.
5. **MPS cache cleanup between periods** — required to fit any future
   chunk-policy work on the user's hardware.

**Not shipped** (intentionally):
- `INDEX_MAX_LENGTH` stays at 512 (no improvement over A in this bakeoff).
- `CHUNKING_POLICIES` for `textbook_sections`, `external`, `wikipedia`
  stay at the post-step-1 paragraph-aware 450/50 values (already-shipped
  in PR #1555 — no further change).
- No new winner-config PR (the code is already where it needs to be).

**Still required after this bakeoff** (these are PR #1555 follow-throughs,
**not** new bakeoff outcomes — the bakeoff confirmed the existing config
is acceptable, but PR #1555's code/manifest changes still need to be
realized on disk):
- **Step 6: full re-encode** of `textbook_sections`, `external`,
  `wikipedia` under main's current config (paragraph-aware 450/50,
  encoder 512). The schema-v2 migration in PR #1555 stamps existing rows
  as `LEGACY_SHIPPED_CONFIG`; the next `cold_encode_corpus` run will see
  the config mismatch and mark legacy rows stale, triggering re-encode.
  Production retrieval is currently using stale legacy embeddings that
  don't match what the code says it should be using. Estimated ~6h on
  M-series Mac.
- **Step 7: 754-wiki rebuild** under the new chunked retrieval. Once the
  cold-encode lands, the wikis on disk are based on the OLD retrieval
  (un-chunked, 512-truncated vectors). Rebuilding makes them consume the
  new chunked vectors. This is the user-visible improvement: wikis
  grounded in retrieval that uses the chunker instead of silently
  truncating long sources.

The bakeoff did NOT unwind the value of PR #1555's centralized chunker
landing on main. It just answered the orthogonal question "should we go
bigger than 450/512" with "no, on this gold set."

## Limitations (the bigger story)

### 1. The gold set doesn't surface the truncation bug

Cell A modern R@10 = 1.000 and nDCG@10 = 0.997 means the 30 benchmark
queries in `scripts/rag/benchmark_queries.yaml` target chunks whose
relevant content lives in the first 512 tokens of their containing rows.
The actual #1553 bug — "rows >512 tokens lose 96% of their content to
silent truncation, hiding relevant material at e.g. token positions
4000–14000" — needs queries that target deep-in-section content to be
measurable. **The bakeoff did not test what we wanted to test, because
the gold set wasn't built for it.**

**Followup**: extend `benchmark_queries.yaml` with queries that
deliberately target post-512-token content in long textbook sections.
Re-run a Cell B-vs-A bakeoff against the extended gold set. If Cell B
wins on the new queries while staying neutral on the existing ones,
revisit the INDEX_MAX_LENGTH bump decision.

### 2. Hardware ceiling: 16 GB unified memory

8192-token encoding is infeasible on this hardware regardless of the
chunk-policy outcome. Even a 4000-token chunk policy with `batch_size=1`
(max memory thrift) would barely fit. Production retrieval — once the
gold set extension above lands and (if) justifies a window bump — would
need to either (a) target a different INDEX_MAX_LENGTH (≤2048), or
(b) document that the encode step requires a workstation with 32+ GB
unified memory. Cloud GPU is an option for one-shot encoding but not for
the live pipeline.

### 3. Modern source mismatch (per Codex review #461)

The benchmark's *modern* tier samples from the legacy `textbooks` table,
while production retrieval uses `textbook_sections`. The bakeoff measured
chunk-policy quality on legacy textbook rows and extrapolates to
`textbook_sections`. Boundary structure of Ukrainian textbook prose is
similar enough to make the extrapolation reasonable, but absolute Recall
numbers may shift if/when the gold set is rewired to the production table.

### 4. No Wikipedia / external in the gold set

Wikipedia and external articles have the most extreme p99 token counts
(15K and 4.5K respectively), which is where chunking *should* most
clearly help. Neither is in the benchmark queries, so the bakeoff
strictly measures textbook + literary signal. Followup gold-set extension
should add wiki + external coverage.

### 5. Single-shot, single-seed

Same `SAMPLE_SEED=42` as #1345 so matched-pair comparison against the
baseline is valid. Cell B's middle Recall@10 dropped exactly 5pp; the
seed-42 sample may be unfortunate for B. Multi-seed re-run would
reduce variance on the borderline call. Skipped here because the
**signal direction** (modern flat, middle slightly worse, OES flat with
nDCG cost) is consistent across both cells and unlikely to flip with
re-seed. The decision (stay on A) holds even with seed noise.

### 6. Hybrid (dense+sparse) NOT in this bakeoff

Sparse weights are computed per-emitted-chunk, so sparse is not
chunk-policy independent. The policy-pick decision is dense-only, which
is the layer the chunk policy actually controls. Hybrid behavior may
diverge from dense-only conclusions but isn't measured here.

### 7. OES / Middle-Ukrainian source heterogeneity

Per user feedback (2026-04-25), confirmed by a per-source modern-letter
audit: literary corpora are a mix of three types — (a) true side-by-side
bilingual editions (archaic + modern translation interleaved, e.g.
`wave0-slovo-o-polku` 91% mixed, `wave9-tlkovaniye-1431` 83%,
`wave1-pvl-lavrentiyivskyi` 78%); (b) standalone modern-Ukrainian
translations (e.g. `wave0-pvl-yaremenko`, `wave6-galvol-kostruba`);
(c) pure archaic transcripts (e.g.
`wave1-pvl-lavrentiyivskyi-rozshyfrovka` 0% modern). Cell A embeds each
row whole regardless of type; Cell B *would* have split bilingual rows
at paragraph boundaries that happen to be archaic-modern translation
pairs — but in the seed-42 sample, no row crossed the 1500-token
threshold so this hypothetical effect didn't materialize. Future
bakeoffs that target the long-tail-row subset would surface this.

### 8. Hungarian contamination in modern textbooks (separate issue #1567)

`5-klas-ukrmova-uhor-2022-1` (246 rows in `textbooks`, 90 in
`textbook_sections`) is a Ukrainian-for-Hungarian-speakers schoolbook
with interleaved Hungarian text. Same `textbooks` table fed every cell,
so this is a constant bias that subtracts out of cell-vs-cell comparison
— but absolute Modern Recall@10 numbers may be 1-2 pp lower than they
would be on a language-pure corpus. Tracked separately.

## Followups filed

- **#1567**: Hungarian-language contamination in textbooks corpus
- **#1569**: Multi-agent writer support for `compile.py` (Claude + GPT-5.5) — needed for the next-stage wiki rebuild
- **(this PR adds)**: Harness incremental per-cell write — see "lessons learned" below

## Lessons learned for #1553 followups

1. **Gold-set coverage is the real bottleneck.** A bakeoff can only
   measure what its gold set tests. Extending `benchmark_queries.yaml`
   to include long-section/deep-token-position queries is a higher-ROI
   investment than running more cells.
2. **Per-cell incremental write.** The harness wrote outputs only after
   all cells completed. Cell C's OOM mid-cell wiped the in-memory Cell
   A+B results — recovery required reading the log. Fixed in this PR by
   writing the markdown + JSON after each cell completes.
3. **8192-token encoding requires more RAM than the user has.** Document
   the hardware floor for any future bakeoff that wants to test
   long-context configurations.
4. **The MPS cache cleanup matters.** The pre-fix Cell B run took 82 min
   for OES; post-fix took 6 min. 14× speedup just from
   `torch.mps.empty_cache()` between periods.
