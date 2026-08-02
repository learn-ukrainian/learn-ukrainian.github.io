# Contamination policy

UA Open-Weight Evaluation 0.1.0 is evaluation-only. Every frozen case has
`foundry_learning_eligible: false`; no case, accepted answer, edit, duplicate,
near-duplicate, transformation, or derived rule may enter a Foundry training,
correction, preference, quality-filter, tokenizer-training, or product-learning
view.

## Mechanical boundary

- `prepare` emits only source text, item identifiers, and hashes. It emits no
  expected action, accepted text, edit, or evidence grade.
- `score` joins gold only after a complete saved-output file exists.
- The Foundry exclusion registry loads all 4,000 cases and rejects exact and
  near-duplicate learning candidates.
- The UA Eval 0.1.1 anchor remains byte-frozen. The parked v0.2 pending-review
  packet is not part of this release.
- Context wrapping expands controlled situations; it does not add independent
  linguistic judgments.

## Model disclosures

A published run must name the suite release hash, model and tokenizer revision,
model-content hash, decoding settings, request and response hashes, and local
run receipt. Authors should disclose known or suspected benchmark exposure.
Public availability means contamination cannot be ruled out for pretrained
models.

## Reporting boundary

Report all fourteen tracks separately. Do not collapse the result into a global
Ukrainian-quality score. Read correction results together with correct-control,
protected-text overcorrection, and unresolved-case abstention behavior.
