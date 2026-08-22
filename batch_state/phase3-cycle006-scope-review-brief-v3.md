# Independent scope and circularity review brief v3

Review the adjacent exact candidate
`phase3-cycle006-restart-amendment-v3.md`, whose SHA-256 is
`524e6eb4f18d38f104413fb32f421ff73c3d80bc411d338a6d8a31fabc087474`.
Hash the candidate before review and fail closed on mismatch.

This is a read-only pre-call gate. Do not edit files, invoke providers, request
private packets, or infer from held-out contents. Adversarially verify that the
restart does not reroll or reuse labels; change the denominator, taxonomy,
chunk size, validator, or custody boundary; create circular adjudication;
weaken the residual or stop policy; or allow certification without complete
independent coverage.

The sole authorized change from v2 is correction of an underived ordered
identity value to the independently recomputed canonical five-field stream
SHA-256
`331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419`,
with the byte serialization now explicit. Verify that this is a derived-value
correction only and does not widen the approved Phase 3 scope.

Return a concise final JSON object with exactly: `review_role`,
`reviewer_task_id`, `exact_model`, `candidate_raw_sha256`, `approved`,
`scope_and_circularity_preserved`, and `findings` (an array of concrete
material findings). Set `reviewer_task_id` to
`cycle006-restart-scope-circularity-v3-6375`.
