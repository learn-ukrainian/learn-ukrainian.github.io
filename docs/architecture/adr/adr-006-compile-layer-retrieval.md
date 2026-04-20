# ADR-006: Multi-tier compile-layer retrieval architecture

**Status**: Accepted
**Date**: 2026-04-20
**Related**: #1335 (epic), #1330 (diagnostic), #1101 (benchmark), ADR-005 (partially superseded), #1337, #1338, #1339, #1340, #1341, #1342, #1348

## Context

The COMPILE-layer retrieval pipeline is the bottleneck for wiki generation quality. `#1330` established the failure mode on `wiki/pedagogy/a1/sounds-letters-and-hello.md`: only 5/10 target concepts surfaced into the 40 returned chunks, while 4/10 concepts were present elsewhere in the corpus and were never surfaced at all.

The benchmark evidence in `#1101` shows this problem is tier-dependent rather than project-wide. Dense retrieval reached Recall@10 of 0.967 on modern Ukrainian textbooks, but only 0.600 on Middle Ukrainian and 0.400 on Old East Slavic. Hybrid retrieval was strictly worse than dense on the archaic tiers, so the data does not support dense+sparse as a universal strategy.

This ADR follows the scaling argument in Andrej Karpathy's "Software in the era of AI" discussion of search at compile/lookup time rather than at consumption time: <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>. ADR-005's wiki-as-consumption-unit decision remains correct at the WRITE layer; the correction here is limited to how sources are retrieved during wiki compilation.

## Decision

## Revision 2026-04-20 (stage d of #1348)

Stage (d) of `#1348` revises the 2026-04-19 decision in place based on the shipped stage history and the 2026-04-19 smoke-test evidence.

- **All tiers now use dense retrieval over VERBATIM text**: textbook, modern literary, archaic literary, external, and Wikipedia units are encoded as-is with MLX-fp16 BGE-M3 vectors. Routing happens via per-track priors in `scripts/wiki/track_priors.yaml`, not via tier-based source exclusion.
- **Framework decision is now locked**: use MLX fp16 with manual CLS pooling in the isolated bridge worker. The community port `mlx-community/bge-m3-mlx-fp16` ships without `1_Pooling/config.json`, so the worker applies manual CLS pooling and L2 normalization explicitly.
- **Evidence for parity and precision**: the smoke test measured cosine `1.00000` versus FlagEmbedding fp16 and top-5 overlap `100%` on the 100-text fixture. Archaic fp16 versus fp32 held minimum cosine `0.99998` with top-5 overlap `100%`, so fp16 is sufficient for both modern and archaic tracks.
- **Evidence for memory headroom**: peak RSS measured `1,760 MB` on the 100-text sample, `43%` lower than the PyTorch MPS reference, so MLX fp16 is the chosen compile-time path.
- **Storage decision is now explicit**: embeddings are stored as `.npy` shards plus a separate manifest DB at `data/embeddings/manifest.db`, not in `sources.db`, because `scripts/wiki/build_sources_db.py:382` recreates `sources.db` during rebuilds.
- **Build history for this revision**: stage (a) MLX bridge [`428be007b`](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/428be007b), stage (b) manifest [`59a419228`](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/59a419228), stage (c) retrieval rewire [`9e86a33a0`](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/9e86a33a0).

- **COMPILE-layer retrieval is project-wide dense retrieval**: all tracks use dense retrieval with per-track corpus priors, neighbor-context expansion where applicable, and verbatim source text.
- **Hybrid retrieval is rejected everywhere**: dense+sparse combinations are not part of the architecture for any tier.
- **The embedder/framework decision is no longer deferred**: the project standard is MLX fp16 BGE-M3 with manual CLS pooling through the isolated subprocess bridge.
- **Embedding storage is separate from `sources.db`**: retrieval vectors live in manifest-backed shard files under `data/embeddings/`.

## Alternatives considered

- **Pure SQLite FTS5 keyword bakeoff (Meilisearch / pg_trgm / OpenSearch-Snowball)**: rejected because it addresses morphological variance, not the actual lexical-disjoint miss profile observed in `#1330`.
- **Why the `#1101` archaic recall objection no longer blocks pure dense retrieval**: those results predated verbatim full-text encoding across all corpora and predated per-track priors. The `#1348` pipeline keeps archaic text verbatim, indexes the full text rather than metadata-only surrogates, and weights merged results by track priors instead of excluding sources by tier, which makes the dense path acceptable for the archaic tracks.
- **Live RAG at WRITE phase**: rejected because ADR-005 stands; wiki articles remain the consumption unit.
- **Hybrid (dense + sparse) retrieval**: rejected because `#1101` shows zero benefit on modern tiers and active harm on archaic tiers.
- **Deferring any change until a full embedder bakeoff**: rejected because the unit-size and routing fix is primary and independent of the eventual embedder winner.

## Consequences

**Positive**:
- Closes the retrieval failure mode exposed by `#1330`.
- Preserves ADR-005's wiki-as-consumption-unit architecture at the WRITE layer.
- Makes grade routing an enforceable part of the T1-T2 compile pipeline; `#1339` is the supporting bug fix.

**Negative / risks**:
- Introduces parent-section schema work tracked in `#1337`.
- Requires dense-embedder inference during compile time for T1-T2.
- Adds a permanent tier classification requirement for each source.

## Implementation tickets

- `#1337` — schema: parent section table + extraction pipeline
- `#1338` — superseded by `#1348`
- `#1339` — grade-filter bug fix (closed)
- `#1340` — re-validation against the `#1330` diagnostic
- `#1341` — folded into `#1348` (archaic uses the same dense pipeline, weighted via priors)
- `#1342` — documentation updates and epic closeout
- `#1348` — full-corpus dense retrieval, MLX bridge, manifest storage, and ADR revision

## Discussion record

- `reviews` channel, thread `ae74c96384514d47ba81417e6e8c0da6` — converged architecture, round 2
- `reviews` channel, thread `0d9b884ecfe94db8bd9bd681a9c5fe49` — round 1, bakeoff vs query construction

These threads record the Claude + Codex + Gemini discussion rounds and end with all participants at `[AGREE]`.

Tail command for future readers: `.venv/bin/python scripts/ai_agent_bridge/__main__.py channel tail reviews --thread <ID>`
