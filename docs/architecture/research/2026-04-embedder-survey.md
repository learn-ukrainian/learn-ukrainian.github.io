# Embedder Survey for Split Retrieval Tiers

Date: 2026-04-19  
Issue: #1345  
Related: #1335, #1338, #1341, #1343

## Scope

This survey updates the embedder decision after the `#1335` tier split:

- T1-T2 modern Ukrainian: `modern`
- T3 Middle Ukrainian: `middle_ukrainian`
- T4 Old East Slavic: `old_east_slavic`

It combines:

- public evidence from official model cards, vendor docs, papers, the [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard), [MTEB Arena](https://huggingface.co/spaces/mteb/arena), and [Hugging Face feature-extraction trending](https://huggingface.co/models?other=feature-extraction&sort=trending)
- a local benchmark run in this repo via [scripts/rag/benchmark_embeddings.py](../../../scripts/rag/benchmark_embeddings.py) against SQLite-backed tier pools in [scripts/rag/benchmark_results.json](../../../scripts/rag/benchmark_results.json)

This bakeoff is now complete to the practical limit of this machine:

- full `sample_size=1000` dense runs completed for `bge-m3`, `jina-v3`, `multilingual-e5-large-instruct`, `gte-multilingual-base`, and `embeddinggemma-300m`
- `qwen3-0.6b` is the only remaining blocked dense candidate because the full run still hits MPS out-of-memory on `old_east_slavic`
- the legacy `bge-m3-hybrid` row remains as the prior-project baseline
- both dedicated rerankers completed at `sample_size=1000` against FTS5 top-50 candidate sets

## Executive Decision

> **Primary for T1-T2**: `BAAI/bge-m3`  
> It ties the top `modern` Recall@10 at `1.00`, leads `modern` nDCG@10 at `0.997`, and remains the strongest completed dense model overall (`Recall@10 0.600`, `nDCG@10 0.509`).

> **Secondary dense fallback if BGE replacement pressure appears later**: `intfloat/multilingual-e5-large-instruct`  
> It is the only completed challenger that stays close on `middle_ukrainian` (`Recall@10 0.433`, `nDCG@10 0.330`), but the `512`-token input cap truncated `2020/3048` sampled passages and keeps it behind BGE for section-scale retrieval.

> **Primary for T3-T4**: keep ADR-006 metadata-first routing  
> No tested dense model or reranker overturns that call: the best dense result is still only `0.50` / `0.30` Recall@10 on `middle_ukrainian` / `old_east_slavic`, and both dedicated rerankers leave archaic FTS5 candidate recall at `0.10` / `0.10`.

## What I Checked

- [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard): multilingual retrieval, long-context retrieval, and model metadata snapshots
- [MTEB Arena](https://huggingface.co/spaces/mteb/arena): secondary signal only; useful for global pairwise preference, but not Ukrainian- or archaic-specific
- [Hugging Face feature-extraction trending](https://huggingface.co/models?other=feature-extraction&sort=trending): adoption signal only, not a substitute for local relevance evaluation
- arXiv and public sources since 2026-01: no newer public Ukrainian retrieval bakeoff surfaced that supersedes the repo-local benchmark
- [Ukraine sovereign LLM announcement](https://digitalstate.gov.ua/news/govtech/ukraine-moves-toward-a-sovereign-ai-model-national-llm-to-enter-beta-in-2026): relevant as a future watch item, not an immediate embedder choice

## Local Benchmark

Method:

- Source chunks came from `data/sources.db`, not Qdrant.
- `modern` used all textbook grades because the benchmark ground truth spans grades 3-11.
- `middle_ukrainian` and `old_east_slavic` used `literary_texts` rows filtered by `source_file` allowlists derived from the corpus' original `language_period` metadata.
- Metrics: Recall@5, Recall@10, nDCG@10.
- Recommendation decisions use the dense rows. `bge-m3-hybrid` is retained only as a legacy baseline because the project previously used BGE dense+sparse.

### Dense Comparison

| Model | Status | Sample size | Modern Recall@10 | Middle Recall@10 | OES Recall@10 | Modern nDCG@10 | Middle nDCG@10 | OES nDCG@10 | Peak RSS MB | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| BGE-M3 dense | complete | 1000 | 1.000 | 0.500 | 0.300 | 0.997 | 0.262 | 0.269 | 4737 | Full local run on SQLite source pools |
| jina-embeddings-v3 | complete | 1000 | 1.000 | 0.283 | 0.150 | 0.979 | 0.175 | 0.118 | 4269 | Full run completed; the 20-sample smoke uplift collapsed at scale |
| multilingual-e5-large-instruct | complete | 1000 | 1.000 | 0.433 | 0.100 | 0.974 | 0.330 | 0.100 | 3836 | Strong middle slice, but `512`-token cap truncated `2020/3048` passages |
| gte-multilingual-base | complete | 1000 | 1.000 | 0.267 | 0.100 | 0.923 | 0.121 | 0.057 | 2416 | Fastest / lightest credible full run, but clearly behind BGE on quality |
| EmbeddingGemma-300M | complete | 1000 | 0.033 | 0.150 | 0.050 | 0.047 | 0.161 | 0.061 | 3951 | HF gating was unblocked, but retrieval quality was not competitive |
| Qwen3-Embedding-0.6B | blocked | 1000 target | blocked | blocked | blocked | blocked | blocked | blocked | n/a | MPS out-of-memory during full chunk encoding on `old_east_slavic` |

### BGE Hybrid Baseline

| Model | Status | Sample size | Modern Recall@10 | Middle Recall@10 | OES Recall@10 | Delta vs BGE dense |
|---|---|---:|---:|---:|---:|---|
| BGE-M3 hybrid | complete | 1000 | 1.000 | 0.450 | 0.200 | No gain on `modern`; worse on both archaic slices |

### Reranker Comparison

Cells use `Recall@10 / nDCG@10`.

| Model | Status | Sample size | Modern FTS5 baseline | Modern reranked | Modern delta | Middle FTS5 baseline | Middle reranked | Middle delta | OES FTS5 baseline | OES reranked | OES delta | Notes |
|---|---|---:|---|---|---|---|---|---|---|---|---|---|
| BGE-reranker-v2-m3 | complete | 1000 | 0.200 / 0.108 | 0.533 / 0.441 | +0.333 / +0.333 | 0.100 / 0.042 | 0.100 / 0.062 | +0.000 / +0.020 | 0.100 / 0.100 | 0.100 / 0.050 | +0.000 / -0.050 | Helps `modern`, flat on `middle_ukrainian`, worse ranking on `old_east_slavic` |
| jina-reranker-v2-base-multilingual | complete | 1000 | 0.200 / 0.108 | 0.533 / 0.426 | +0.333 / +0.318 | 0.100 / 0.042 | 0.100 / 0.047 | +0.000 / +0.005 | 0.100 / 0.100 | 0.100 / 0.100 | +0.000 / +0.000 | Same recall pattern as BGE reranker, slightly cheaper and lighter |

### Readout

- `BAAI/bge-m3` is the clear dense winner: it ties the top `modern` Recall@10 at `1.00`, posts the best `modern` nDCG@10 (`0.997`), and leads every completed challenger on at least one archaic tier.
- `jina-v3` changed from a live upset candidate to a negative result: its smoke numbers collapsed from `0.85 -> 0.283` on `middle_ukrainian` and from `0.60 -> 0.15` on `old_east_slavic` once the run scaled to `1000`.
- `multilingual-e5-large-instruct` is the only challenger that stayed within range on `middle_ukrainian`, but its `512`-token truncation penalty is material for this repo's section-scale retrieval.
- Dedicated rerankers help `modern` candidate ordering, but they do not rescue archaic tiers because the FTS5 candidate set itself tops out at `0.10` Recall@10 on both `middle_ukrainian` and `old_east_slavic`.
- The architecture-level result did not flip: modern retrieval justifies a dense stage, while T3-T4 still do not show enough semantic retrieval signal to replace metadata-first routing.

## Recommendation by Tier

### T1-T2 (`modern`)

Recommendation: keep `BAAI/bge-m3` as the implementation choice for `#1338`.

Reasoning:

- It wins the completed dense matrix on the metric that matters most here: `modern` Recall@10 stays at `1.00`, while `modern` nDCG@10 is the best observed result at `0.997`.
- It also remains the best full-run dense model on the archaic slices (`middle_ukrainian Recall@10 0.50`, `old_east_slavic Recall@10 0.30`), which matters because the same embedder choice informs cross-tier maintenance pressure.
- Its operational profile is still reasonable for the compile machine: about `673s` encode time, `4737 MB` peak RSS, and an already-integrated MIT-licensed local deployment path.
- This keeps the verdict aligned with ADR-006: `#1338` should proceed with BGE as the dense model inside the T1-T2 compile pipeline.

Secondary note:

- The jina-v3 smoke-to-full collapse changes the decision from "wait for the rerun" to "decision closed": it ties BGE only on `modern` Recall@10, loses on `modern` nDCG@10, loses on both archaic tiers, and takes more than `3x` BGE's encode time.
- `multilingual-e5-large-instruct` is the only meaningful fallback worth keeping on the board, but the passage truncation rate keeps it behind BGE for the actual section sizes used here.

### T3-T4 (`middle_ukrainian`, `old_east_slavic`)

Recommendation: keep the `#1341` direction of metadata-first routing with no dense stage as the primary path.

Reasoning:

- The best dense result is still BGE at Recall@10 `0.50` on `middle_ukrainian` and `0.30` on `old_east_slavic`; that is not strong enough to justify replacing metadata-first routing.
- The jina-v3 full run removes the only apparent overturn candidate from the earlier survey: its smoke lead on archaic slices does not survive the `1000`-sample run.
- The dedicated reranker results do not create a pivot path either. Both reranker models leave `middle_ukrainian` and `old_east_slavic` stuck at Recall@10 `0.10` from the FTS5 candidate set.
- The legacy BGE hybrid baseline stays worse than dense-only on both archaic tiers, so there is still no evidence for a dense+sparse rescue architecture.

## Does jina-v3 Late Chunking Remove #1337?

Short answer: no.

Why:

- Late chunking improves long-context representations, but `#1337` is not only about representation quality. It is also about explicit section identities, parent-context delivery, and deterministic citation units.
- `#1338` needs section-level retrieval outputs with stable `section_id` and `full_text` boundaries. A late-chunked embedder does not create those schema objects by itself.
- The local benchmark here is still chunk-level. Even if jina-v3 eventually wins a tier, the pipeline still needs the section/parent layer so the wiki compiler gets clean retrieval units.

Conclusion:

- jina-v3 may reduce the semantic cost of imperfect chunk boundaries.
- jina-v3 does not remove the need for `#1337` parent-section extraction or `#1338` section-level delivery.

## Candidate Fact Cards

### Local / open-weight candidates

| Model | Release | Params | Embedding dim | Max input | Languages explicitly claimed | Ukrainian-specific published data | Public retrieval signal | License | Hosting | Local fit | Late chunking | Instruction style | Practical note |
|---|---|---:|---:|---:|---|---|---|---|---|---|---|---|---|
| [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) | 2024-02-05 ([paper](https://arxiv.org/abs/2402.03216)) | ~0.6B | 1024 | 8192 | Model card: "more than 100 working languages" | None found | Qwen's official multilingual table reports retrieval `54.60` | MIT | Local | Full local run succeeded at ~4.7 GB RSS | No | No query instruction required | Full 1000-sample winner in this repo |
| [Qwen/Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) | 2025-06-05 ([paper](https://arxiv.org/abs/2506.05176)) | 0.6B | 1024 | 32K | Model card: 100+ languages | None found | Official multilingual retrieval `64.64` | Apache-2.0 | Local | Full local run blocked by MPS memory | No | Query-side prompt recommended by the card | Still blocked locally; deferred unless a future ticket funds CPU or smaller-batch execution |
| [Qwen/Qwen3-Embedding-4B](https://huggingface.co/Qwen/Qwen3-Embedding-4B) | 2025-06-05 ([paper](https://arxiv.org/abs/2506.05176)) | 4B | 2560 | 32K | Model card: 100+ languages | None found | Official multilingual retrieval `69.60` | Apache-2.0 | Local | Likely too heavy for the current single-machine compile workflow | No | Query-side prompt recommended | Publicly strong, but operationally expensive here |
| [Qwen/Qwen3-Embedding-8B](https://huggingface.co/Qwen/Qwen3-Embedding-8B) | 2025-06-05 ([paper](https://arxiv.org/abs/2506.05176)) | 8B | 4096 | 32K | Model card: 100+ languages | None found | Official multilingual retrieval `70.88` | Apache-2.0 | Local | Very unlikely to fit the current worker budget comfortably | No | Query-side prompt recommended | Public leaderboard weapon, not a pragmatic first deployment here |
| [google/embeddinggemma-300m](https://huggingface.co/google/embeddinggemma-300m) | current HF card checked Apr 2026 | 0.3B | 768 | not confirmed in checked source | Google positions it as multilingual | None found | No checked Ukrainian retrieval number surfaced | Gemma license | Local | Full local run succeeded after HF token setup | No | No special retrieval adapter documented in checked sources | Access was fixed, but the resulting retrieval quality rules it out |
| [jinaai/jina-embeddings-v3](https://huggingface.co/jinaai/jina-embeddings-v3) | 2024-09-16 ([paper](https://arxiv.org/abs/2409.10173)) | 570M | 1024 | 8194 | HF card explicitly includes `uk` | None found | Public MTEB signals exist; official card and docs emphasize task adapters | CC BY-NC 4.0 | Local | Full run succeeded at ~4.3 GB RSS | Yes | Native adapters: `retrieval.query` / `retrieval.passage` | Full-run collapse eliminated it as a BGE replacement |
| [intfloat/multilingual-e5-large-instruct](https://huggingface.co/intfloat/multilingual-e5-large-instruct) | 2024-02-08 ([paper](https://arxiv.org/abs/2402.05672)) | ~0.6B | 1024 | 512 | Card says 100 XLM-R languages | None found | Qwen's official multilingual retrieval table reports `57.12` | MIT | Local | Full run completed | No | Natural-language instruction required on the query side | Best completed fallback, but the `512`-token cap is a real downside for section-scale retrieval |
| [Alibaba-NLP/gte-multilingual-base](https://huggingface.co/Alibaba-NLP/gte-multilingual-base) | 2024-07-29 ([paper](https://arxiv.org/abs/2407.19669)) | 304M | 768 | 8192 | Card says 70+ languages and lists `uk` | No direct Ukrainian retrieval number found | Card points to multilingual retrieval validation and the MTEB leaderboard | Apache-2.0 | Local | Full run completed | No | No special adapter required | Attractive efficiency profile, but not enough retrieval quality to displace BGE |

### API / watchlist candidates

| Model | Release | Embedding dim | Max input | Public signal | Hosting | Decision |
|---|---|---:|---:|---|---|---|
| [OpenAI text-embedding-3-large](https://platform.openai.com/docs/models/text-embedding-3-large) | 2024-01-25 ([announcement](https://openai.com/index/new-embedding-models-and-api-updates/)) | 3072 max, shorten-able | 8192 | OpenAI reports MTEB average `64.6`; Qwen's multilingual table reports `59.27` | API only | Strong external reference point, but not the primary choice for a local-first pipeline |
| [Cohere embed-multilingual-v3.0](https://docs.cohere.com/v1/docs/embeddings) | vendor docs current | vendor-configured | vendor-configured | Qwen's multilingual table reports `59.16` | API only | Reasonable API baseline, but not enough upside over local options to justify the dependency |
| [Cohere embed-v4.0](https://docs.cohere.com/v1/docs/embeddings) | 2025-04-15 ([announcement](https://docs.cohere.com/changelog/embed-multimodal-v4)) | 256 / 512 / 1024 / 1536 | 128K | Technically attractive on context length, but no local result here | API only | Watch only |
| [mixedbread-ai/deepset-mxbai-embed-de-large-v1](https://huggingface.co/mixedbread-ai/deepset-mxbai-embed-de-large-v1) | 2024 | 1024 | not confirmed in checked card | Model card explicitly scopes it to German and English | Local / API | Rule out for Ukrainian |
| [EuroLLM collection](https://huggingface.co/collections/EuroLLM) | n/a for embeddings | n/a | n/a | No embedder candidate surfaced | n/a | Watch only; not actionable for `#1338` or `#1341` yet |

## Comparative Analysis

### Best fit for modern Ukrainian textbooks

`BAAI/bge-m3` is the only dense choice that still wins once the full matrix is in:

- It ties the best `modern` Recall@10 at `1.00`, but it separates on ranking quality with the best `modern` nDCG@10 (`0.997`).
- `multilingual-e5-large-instruct` is the only challenger worth keeping in reserve, but its `512`-token ceiling is misaligned with the repo's section lengths.
- `jina-v3` no longer deserves provisional-upset status after the full run. It ties BGE only on `modern` Recall@10, loses on `modern` nDCG@10, and is materially slower.
- `gte-multilingual-base` is the efficiency option, not the quality option. `EmbeddingGemma-300M` is out of contention on retrieval quality. `Qwen3-0.6B` remains blocked locally.

### Why the archaic recommendation differs

- Every completed dense result still shows a large modern-versus-archaic drop, and no dedicated reranker closes it on top of FTS5 candidates.
- That keeps the `#1335` split architecture intact: modern justifies a dense stage, while archaic still wants metadata-first routing and cleaner section/work boundaries.
- The T3-T4 dense question should be reopened only if we get either a historical-Slavic-aware embedder or new implementation evidence that metadata-first routing is failing in practice.

## Sovereign-Ukraine Watch Item

The [January 2026 sovereign-LLM announcement](https://digitalstate.gov.ua/news/govtech/ukraine-moves-toward-a-sovereign-ai-model-national-llm-to-enter-beta-in-2026) matters strategically, but it does not change `#1338` today:

- the public announcement is for a generative Ukrainian-adapted Gemma-based LLM, not an embedding model
- it is still the right watch item for a future Ukrainian-first embedder
- the implementation implication is architectural, not tactical: keep the dense stage swappable so a sovereign embedding model can drop in later without redesigning the retrieval stack

## Bottom Line

- `BAAI/bge-m3` is the `#1338` choice. It ties the top `modern` Recall@10 at `1.00`, posts the best `modern` nDCG@10 at `0.997`, and remains the strongest completed dense model across the full matrix.
- `#1341` stays metadata-first for `middle_ukrainian` and `old_east_slavic`. The best dense result is still only `0.50` / `0.30`, and both dedicated rerankers leave archaic FTS5 candidate recall at `0.10` / `0.10`.
- Dedicated rerankers are worth considering only as T1-T2 precision layers on top of a stronger candidate generator. They are not a rescue path for archaic retrieval.
- `Qwen3-Embedding-0.6B` stays deferred unless a future follow-up ticket funds CPU or smaller-batch execution for a new decision need. The completed matrix already resolved the current embedder and architecture choices without it.
