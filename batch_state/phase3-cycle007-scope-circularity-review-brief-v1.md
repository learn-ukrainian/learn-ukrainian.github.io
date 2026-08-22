# Phase 3 Cycle 007 scope and circularity review brief v1

Review only the exact bytes of
`batch_state/phase3-cycle007-source-grounded-amendment-v1.md`. Do not inspect
private packets, prompts, labels, provider outputs, account data, or raw logs.

Adversarially check that the proposed restart:

1. preserves exactly 204 packets / 10,159 rows and the frozen identity order;
2. copies no Cycle 006 labels or provider artifacts;
3. does not treat model agreement as truth or use either first-pass model as
   its own independent evaluator, including under a fresh session identity;
4. freezes the evidence, seed, audit selection, prompts, code, and source
   versions before private labeling;
5. prevents evidence cherry-picking, cross-row evidence reuse, leakage,
   post-label sample selection, and source-blind overrides;
6. defines terminal semantic and privacy stops without silent retries;
7. proves the user-visible outcome rather than only hashes, schemas, cost, or
   throughput;
8. keeps private data local while making useful use of the VPS fleet.

Return the amendment SHA-256, `APPROVE` or `REQUEST_CHANGES`, numbered findings
with severity, and concrete corrections. This is prompt/contract review, not
the later exact-head implementation or cross-family PR review.
