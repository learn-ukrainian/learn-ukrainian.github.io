# Embedder Survey for Split Retrieval Tiers

Date: 2026-04-19  
Issue: #1343  
Related: #1335, #1338, #1341

## Scope

This survey updates the embedder decision after the `#1335` tier split:

- T1-T2 modern Ukrainian: `modern`
- T3 Middle Ukrainian: `middle_ukrainian`
- T4 Old East Slavic: `old_east_slavic`

It combines:

- public evidence from official model cards, vendor docs, papers, the [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard), [MTEB Arena](https://huggingface.co/spaces/mteb/arena), and [Hugging Face feature-extraction trending](https://huggingface.co/models?other=feature-extraction&sort=trending)
- a local benchmark run in this repo via [scripts/rag/benchmark_embeddings.py](../../../scripts/rag/benchmark_embeddings.py) against SQLite-backed tier pools in [scripts/rag/benchmark_results.json](../../../scripts/rag/benchmark_results.json)

This ended as a partial bakeoff, not a clean four-model finish:

- `bge-m3` completed at the full `sample_size=1000`
- `jina-v3` completed only as a smoke run at `sample_size=20`
- `qwen3-0.6b` blocked on MPS memory during the full run
- `embeddinggemma-300m` blocked by a gated Hugging Face repo in this environment

## Executive Decision

> **Primary for T1-T2**: `BAAI/bge-m3`  
> Because it is the only model fully validated end-to-end on the repo's SQLite corpus, and it still delivers `modern` Recall@10 `1.00` with nDCG@10 `0.997`.

> **Backup if we need a second local option later**: `jinaai/jina-embeddings-v3`  
> Because it exposes native retrieval adapters and the smoke run was promising enough to justify a later full rerun, but not strong enough to displace BGE today.

> **Primary for T3-T4**: no dense embedder primary; keep metadata-first routing  
> Because the only full dense result still tops out at Recall@10 `0.50` on `middle_ukrainian` and `0.30` on `old_east_slavic`, which is not strong enough to overturn the architecture in `#1341`.

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
| Qwen3-Embedding-0.6B | blocked | 1000 target | blocked | blocked | blocked | blocked | blocked | blocked | n/a | MPS out-of-memory during full chunk encoding |
| EmbeddingGemma-300M | blocked | 1000 target | blocked | blocked | blocked | blocked | blocked | blocked | n/a | `google/embeddinggemma-300m` returned 401 gated-repo access error |
| jina-embeddings-v3 | partial smoke only | 20 | 1.000 | 0.850 | 0.600 | 1.000 | 0.661 | 0.367 | 4335 | Promising, but not comparable to the 1000-chunk runs |

### BGE Hybrid Baseline

| Model | Status | Sample size | Modern Recall@10 | Middle Recall@10 | OES Recall@10 | Delta vs BGE dense |
|---|---|---:|---:|---:|---:|---|
| BGE-M3 hybrid | complete | 1000 | 1.000 | 0.450 | 0.200 | No gain on `modern`; worse on both archaic slices |

### Readout

- `modern` is effectively solved enough for this pipeline class: BGE full-run Recall@10 is `1.00`, and the small jina smoke run also hit `1.00`.
- `middle_ukrainian` remains materially harder: the only full dense result is BGE at Recall@10 `0.50` and nDCG@10 `0.262`.
- `old_east_slavic` remains the weakest slice: the only full dense result is BGE at Recall@10 `0.30`, and the hybrid baseline drops further to `0.20`.
- The old pattern still holds: dense retrieval looks strong for modern textbooks, but archaic retrieval is still not solved by just swapping in a multilingual embedder.

## Recommendation by Tier

### T1-T2 (`modern`)

Recommendation: keep `BAAI/bge-m3` as the implementation choice for `#1338`.

Reasoning:

- It is the only model that completed the full SQLite-backed benchmark in this environment.
- Its `modern` result is already strong enough for the current retrieval task: Recall@10 `1.00`, nDCG@10 `0.997`.
- It is already integrated, MIT-licensed, local-first, and stays within the current 1024-dim / 8192-token operating envelope.

Secondary note:

- `jinaai/jina-embeddings-v3` is the most credible follow-up candidate because it supports asymmetric retrieval adapters and looks promising in the smoke run.
- It is not ready to replace BGE yet because the repo does not have a comparable full 1000-chunk result for it.

### T3-T4 (`middle_ukrainian`, `old_east_slavic`)

Recommendation: keep the `#1341` direction of metadata-first routing with no dense stage as the primary path.

Reasoning:

- The best full dense result still reaches only Recall@10 `0.50` on `middle_ukrainian` and `0.30` on `old_east_slavic`.
- The legacy BGE hybrid baseline does not rescue the archaic tiers; it is worse than dense-only on both.
- None of the alternative dense contenders produced a full, reproducible counterexample in this environment.

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
| [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) | 2024-02-05 ([paper](https://arxiv.org/abs/2402.03216)) | ~0.6B | 1024 | 8192 | Model card: "more than 100 working languages" | None found | Qwen's official multilingual table reports retrieval `54.60` | MIT | Local | Full local run succeeded at ~4.7 GB RSS | No | No query instruction required | Best validated fit for this repo right now |
| [Qwen/Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) | 2025-06-05 ([paper](https://arxiv.org/abs/2506.05176)) | 0.6B | 1024 | 32K | Model card: 100+ languages | None found | Official multilingual retrieval `64.64` | Apache-2.0 | Local | Full local run blocked by MPS memory | No | Query-side prompt recommended by the card | Strong public signal, but unvalidated locally here |
| [Qwen/Qwen3-Embedding-4B](https://huggingface.co/Qwen/Qwen3-Embedding-4B) | 2025-06-05 ([paper](https://arxiv.org/abs/2506.05176)) | 4B | 2560 | 32K | Model card: 100+ languages | None found | Official multilingual retrieval `69.60` | Apache-2.0 | Local | Likely too heavy for the current single-machine compile workflow | No | Query-side prompt recommended | Publicly strong, but operationally expensive here |
| [Qwen/Qwen3-Embedding-8B](https://huggingface.co/Qwen/Qwen3-Embedding-8B) | 2025-06-05 ([paper](https://arxiv.org/abs/2506.05176)) | 8B | 4096 | 32K | Model card: 100+ languages | None found | Official multilingual retrieval `70.88` | Apache-2.0 | Local | Very unlikely to fit the current worker budget comfortably | No | Query-side prompt recommended | Public leaderboard weapon, not a pragmatic first deployment here |
| [google/embeddinggemma-300m](https://huggingface.co/google/embeddinggemma-300m) | current HF card checked Apr 2026 | 0.3B | 768 | not confirmed in checked source | Google positions it as multilingual | None found | No checked Ukrainian retrieval number surfaced | Gemma license | Local | Could not be benchmarked here because the repo was gated | No | No special retrieval adapter documented in checked sources | Small on paper, but inaccessible in this environment |
| [jinaai/jina-embeddings-v3](https://huggingface.co/jinaai/jina-embeddings-v3) | 2024-09-16 ([paper](https://arxiv.org/abs/2409.10173)) | 570M | 1024 | 8194 | HF card explicitly includes `uk` | None found | Public MTEB signals exist; official card and docs emphasize task adapters | CC BY-NC 4.0 | Local | Smoke run succeeded at ~4.3 GB RSS | Yes | Native adapters: `retrieval.query` / `retrieval.passage` | Best follow-up candidate if we rerun a full bakeoff |
| [intfloat/multilingual-e5-large-instruct](https://huggingface.co/intfloat/multilingual-e5-large-instruct) | 2024-02-08 ([paper](https://arxiv.org/abs/2402.05672)) | ~0.6B | 1024 | 512 | Card says 100 XLM-R languages | None found | Qwen's official multilingual retrieval table reports `57.12` | MIT | Local | Not yet benchmarked here | No | Natural-language instruction required on the query side | 512-token truncation is a real downside for section-scale retrieval |
| [Alibaba-NLP/gte-multilingual-base](https://huggingface.co/Alibaba-NLP/gte-multilingual-base) | 2024-07-29 ([paper](https://arxiv.org/abs/2407.19669)) | 304M | 768 | 8192 | Card says 70+ languages and lists `uk` | No direct Ukrainian retrieval number found | Card points to multilingual retrieval validation and the MTEB leaderboard | Apache-2.0 | Local | Attractive size/context profile, but not benchmarked in this repo | No | No special adapter required | Worth a future lightweight comparison if BGE replacement pressure grows |

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

1. `BAAI/bge-m3`
2. `jinaai/jina-embeddings-v3` as the provisional follow-up candidate
3. `Qwen/Qwen3-Embedding-0.6B` as the strongest public-signal option that still needs a successful local run

Why this ordering:

- `modern` is already near-solved in the local benchmark, so the decision should weight operational fit and validated local behavior more heavily than leaderboard spread.
- BGE has the best combination of proven local result, integration maturity, licensing, and current pipeline fit.
- jina-v3 is more interesting than its current rank suggests because its task adapters and late-chunking story map well to section-scale retrieval, but the local evidence is still only a smoke run.
- Qwen3 looks stronger on public multilingual retrieval tables, but a model that does not finish locally is not the right immediate default for this repo.

### Why the archaic recommendation differs

- Every dense result that actually completed still shows a large modern-versus-archaic drop.
- That keeps the `#1335` split architecture intact: modern justifies a dense stage, while archaic still wants metadata-first routing and cleaner section/work boundaries.
- The T3-T4 dense question should be reopened only if we get a historical-Slavic-aware embedder or a materially stronger local benchmark than the numbers above.

## Sovereign-Ukraine Watch Item

The [January 2026 sovereign-LLM announcement](https://digitalstate.gov.ua/news/govtech/ukraine-moves-toward-a-sovereign-ai-model-national-llm-to-enter-beta-in-2026) matters strategically, but it does not change `#1338` today:

- the public announcement is for a generative Ukrainian-adapted Gemma-based LLM, not an embedding model
- it is still the right watch item for a future Ukrainian-first embedder
- the implementation implication is architectural, not tactical: keep the dense stage swappable so a sovereign embedding model can drop in later without redesigning the retrieval stack

## Bottom Line

- Keep `BAAI/bge-m3` for `#1338` until another model completes the same local benchmark and clearly beats it on `modern`.
- Keep `#1341` metadata-first and treat dense retrieval for `middle_ukrainian` and `old_east_slavic` as unproven.
- Reopen the bakeoff later only if `embeddinggemma-300m` access is available, `qwen3` can finish on CPU or a larger GPU/MPS box, and `jina-v3` gets a full 1000-chunk rerun.
